# -*- coding: utf-8 -*-
"""Testes do make_init_script.py (entradas sintéticas; saída em pasta temporária)."""

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

from helpers import HERE, read_text_file, run_main
import make_init_script as mk

SECRET = "VALOR-DE-SESSAO-NAO-PODE-APARECER-123"  # gitleaks:allow (valor falso de teste)
TEMPLATE_JS = os.path.join(os.path.dirname(HERE), "..", "templates", "init-script-session-storage.js")


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwmcp-w3-init-")
        self.inp = os.path.join(self.tmp, "ss.json")
        self.doc = {"https://app.exemplo.test": {"token": SECRET, "k2": "v2"}, "http://localhost:3000": {"a": "b"}}
        self.write_in(self.doc)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_in(self, doc):
        with open(self.inp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)

    def run_mk(self, *extra):
        code, out, raw = run_main(mk.main, ["--input", self.inp] + list(extra), None)
        self.assertNotIn(SECRET, raw, "valor de sessão vazou na saída")
        return code, out


class PlanAndWriteTests(Base):

    def test_sem_output_so_resumo_sem_valores(self):
        code, out = self.run_mk()
        self.assertEqual((code, out["status"]), (0, "planned"))
        self.assertEqual(out["data"]["total_keys"], 3)
        self.assertEqual({o["origin"] for o in out["data"]["origins"]}, set(self.doc))
        self.assertIsNone(out["data"]["output"])

    def test_output_grava_600_e_contem_os_dados(self):
        dest = os.path.join(self.tmp, "sub", "init.js")
        code, out = self.run_mk("--output", dest)
        self.assertEqual((code, out["status"]), (0, "written"))
        text = read_text_file(dest)
        self.assertIn(SECRET, text)
        self.assertIn("const OVERWRITE = false;", text)
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(os.stat(dest).st_mode), 0o600)

    def test_recusa_sobrescrever_sem_force(self):
        dest = os.path.join(self.tmp, "init.js")
        self.assertEqual(self.run_mk("--output", dest)[0], 0)
        code, out = self.run_mk("--output", dest)
        self.assertEqual(code, 1)
        self.assertEqual(self.run_mk("--output", dest, "--force", "--overwrite")[0], 0)
        self.assertIn("const OVERWRITE = true;", read_text_file(dest))


class ValidationTests(Base):

    def test_entradas_invalidas_saem_com_2(self):
        for bad in ([], {}, {"sem-esquema": {"a": "b"}}, {"https://x.test/": {"a": "b"}},
                    {"https://x.test": ["a"]}, {"https://x.test": {"a": 1}}):
            self.write_in(bad)
            code, out = self.run_mk()
            self.assertEqual((code, out["status"]), (2, "usage_error"), bad)

    def test_json_quebrado_e_arquivo_ausente(self):
        with open(self.inp, "w") as fh:
            fh.write("{nao e json")
        self.assertEqual(self.run_mk()[0], 2)
        os.unlink(self.inp)
        self.assertEqual(self.run_mk()[0], 2)


class EscapingTests(unittest.TestCase):

    def test_escapa_script_tag_e_separadores_de_linha(self):
        js = mk.render({"https://x.test": {"k": "</script><script>alert(1)</script>  \"'\\"}})
        self.assertNotIn("</script>", js)
        self.assertNotIn(" ", js)
        self.assertNotIn(" ", js)

    def test_modelo_da_pasta_templates_usa_o_mesmo_codigo(self):
        template = read_text_file(TEMPLATE_JS)
        body = mk.TEMPLATE.split("\n", 1)[1]  # sem a 1ª linha "(() => {" para comparar o miolo
        miolo = [ln for ln in body.splitlines() if "__DATA__" not in ln and "__OVERWRITE__" not in ln]
        for ln in miolo:
            self.assertIn(ln, template)


@unittest.skipUnless(shutil.which("node"), "node ausente")
class RuntimeTests(Base):
    """Executa o JS gerado com o Node, com location/sessionStorage simulados."""

    def exec_js(self, origin, pre=None, overwrite=False):
        js = mk.render(self.doc, overwrite)
        harness = ("const store = new Map(%s);\n"
                   "globalThis.location = { origin: %s };\n"
                   "globalThis.sessionStorage = { getItem: k => store.has(k) ? store.get(k) : null, setItem: (k, v) => store.set(k, v) };\n"
                   "%s\nprocess.stdout.write(JSON.stringify([...store.entries()]));\n"
                   % (json.dumps(list((pre or {}).items())), json.dumps(origin), js))
        res = subprocess.run(["node", "-e", harness], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        self.assertEqual(res.returncode, 0, res.stderr.decode())
        return dict(json.loads(res.stdout.decode()))

    def test_grava_so_da_origem_corrente(self):
        self.assertEqual(self.exec_js("https://app.exemplo.test"), {"token": SECRET, "k2": "v2"})
        self.assertEqual(self.exec_js("https://outro.test"), {})

    def test_nao_sobrescreve_por_padrao_mas_sobrescreve_com_flag(self):
        self.assertEqual(self.exec_js("http://localhost:3000", pre={"a": "do-site"})["a"], "do-site")
        self.assertEqual(self.exec_js("http://localhost:3000", pre={"a": "do-site"}, overwrite=True)["a"], "b")


if __name__ == "__main__":
    unittest.main()
