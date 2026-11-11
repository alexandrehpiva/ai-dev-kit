# -*- coding: utf-8 -*-
"""Testes do spec_to_gs.py (sem rede). Usa node (se existir) para provar que o JS gerado é válido e
equivale ao spec; testes de YAML pulam sem PyYAML."""

import copy
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
SKILL = os.path.dirname(SCRIPTS)
FIXTURES = os.path.join(HERE, "fixtures")
TEMPLATE = os.path.join(SKILL, "templates", "build-form.gs")
SPEC_TEMPLATES = sorted(glob.glob(os.path.join(SKILL, "templates", "specs", "*.yaml")))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_to_gs as sg  # noqa: E402
import validate_spec as vs  # noqa: E402

NODE = shutil.which("node")
try:
    import yaml as _yaml  # noqa: F401
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="spec_to_gs_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.n = 0

    def write_spec(self, spec):
        self.n += 1
        path = os.path.join(self.tmp, "spec%d.json" % self.n)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, ensure_ascii=False)
        return path

    def cli(self, argv, yaml_module=False):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = sg.main(argv, yaml_module=yaml_module)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def node_json(self, js_text):
        """Executa o JS no node e devolve o JSON impresso."""
        path = os.path.join(self.tmp, "run%d.js" % self.n)
        self.n += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(js_text)
        proc = subprocess.run([NODE, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        return json.loads(proc.stdout.decode("utf-8"))

    def node_check(self, js_text):
        path = os.path.join(self.tmp, "check%d.js" % self.n)
        self.n += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(js_text)
        proc = subprocess.run([NODE, "--check", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))


class TestEscape(Base):

    def test_given_special_chars_when_js_string_then_escapes_each(self):
        # Given: aspas, barra, quebras, U+2028/2029, </script>, <!--, controle e substituto solto
        text = "a'b\"c\\d\ne\rf\tg\u2028h\u2029i</script>j<!--k\x01l\ud800m"
        # When
        lit = sg.js_string(text)
        # Then: nenhum caractere perigoso cru na saída
        for bad in ("\n", "\r", "\u2028", "\u2029", "</", "<!--", "\x01", "\ud800"):
            self.assertNotIn(bad, lit)
        self.assertTrue(lit.startswith("'") and lit.endswith("'"))
        self.assertIn("\\x3C/script>", lit)
        self.assertIn("\\u2028", lit)

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_special_chars_when_evaluated_in_node_then_roundtrip(self):
        text = "a'b\"c\\d\ne\rf\tg\u2028h\u2029i</script>j<!--k\x01l\x7fm\ufeffn ção 😀 \\x41"
        js = "var S = %s;\nconsole.log(JSON.stringify(S));" % sg.js_string(text)
        self.assertEqual(self.node_json(js), text)

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_odd_keys_when_converted_then_roundtrip_and_proto_is_own_key(self):
        spec = {"ok": 1, "com-hifen": {"a b": [1, 2.5, None, True, False]}, "ç": "x", "__proto__": {"p": 1}}
        js = "var S = %s;\nconsole.log(JSON.stringify({o: S, own: Object.keys(S)}));" % sg.to_js(spec)
        data = self.node_json(js)
        self.assertEqual(data["o"]["com-hifen"], spec["com-hifen"])
        self.assertIn("__proto__", data["own"])

    def test_given_nan_when_literal_then_error(self):
        with self.assertRaises(sg.LiteralError):
            sg.to_js({"a": float("nan")})


class TestExample(Base):

    def test_given_fixture_q6_when_inspected_then_has_exit_column(self):
        spec = load("spec_example.json")
        q6 = [it for s in spec["sections"] for it in s["items"] if it["id"] == "q6"][0]
        self.assertEqual(q6["grid"]["columns"], ["Manhã", "Tarde", "Não posso"])
        self.assertIn("Não posso", q6["description"])

    def test_given_example_when_validate_for_build_then_still_ok(self):
        code, payload = vs.build_payload("x", load("spec_example.json"), [], True)
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_given_example_when_literal_then_stdout_only_literal_and_json_on_stderr(self):
        # Given / When
        code, out, err = self.cli([os.path.join(FIXTURES, "spec_example.json"), "--literal"])
        # Then
        self.assertEqual(code, 0)
        self.assertTrue(out.rstrip().endswith("};"))
        self.assertIn("var SPEC = {", out)
        self.assertNotIn('"ok"', out)
        payload = json.loads(err)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "literal")
        self.assertEqual(sorted(payload), ["data", "next_steps", "ok", "problems", "status"])

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_example_when_literal_then_node_value_equals_spec(self):
        code, out, _ = self.cli([os.path.join(FIXTURES, "spec_example.json"), "--literal"])
        data = self.node_json(out + "\nconsole.log(JSON.stringify(SPEC));")
        self.assertEqual(data, sg.normalize(load("spec_example.json")))

    def test_given_example_when_out_then_only_spec_block_is_replaced(self):
        # Given
        out_path = os.path.join(self.tmp, "gerado.gs")
        # When
        code, out, err = self.cli([os.path.join(FIXTURES, "spec_example.json"), "--out", out_path])
        # Then
        self.assertEqual(code, 0, out)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "generated")
        with open(out_path, encoding="utf-8") as fh:
            gen = fh.read()
        with open(TEMPLATE, encoding="utf-8") as fh:
            tpl = fh.read()
        self.assertEqual(gen.count(sg.BEGIN), 1)
        self.assertEqual(gen.count(sg.END), 1)
        head_g, rest_g = gen.split(sg.END, 1)
        head_t, rest_t = tpl.split(sg.END, 1)
        self.assertEqual(rest_g, rest_t)  # nada depois do bloco mudou
        self.assertEqual(head_g.split(sg.BEGIN, 1)[0], head_t.split(sg.BEGIN, 1)[0])  # nem antes
        self.assertIn("Não posso", gen)
        self.assertIn("function criarFormulario", gen)
        self.assertEqual(payload["data"]["bytes"], len(gen.encode("utf-8")))

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_generated_gs_when_node_then_syntax_ok_and_checkSpec_accepts(self):
        out_path = os.path.join(self.tmp, "gerado.gs")
        self.cli([os.path.join(FIXTURES, "spec_example.json"), "--out", out_path])
        with open(out_path, encoding="utf-8") as fh:
            gen = fh.read()
        self.node_check(gen)
        # checkSpec_ do próprio build-form.gs (sem FormApp) aceita o SPEC convertido
        js = ("const vm = require('vm');\n"
              "const code = %s;\n"
              "const r = vm.runInNewContext(code + '\\n;checkSpec_(SPEC, OPTS); JSON.stringify({s: SPEC.status, w: OPTS.warnings});');\n"
              "console.log(r);\n" % json.dumps(gen))
        proc_path = os.path.join(self.tmp, "vm.js")
        with open(proc_path, "w", encoding="utf-8") as fh:
            fh.write(js)
        proc = subprocess.run([NODE, proc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(proc.stdout.decode("utf-8"))["s"], "approved")

    def test_given_example_when_converted_then_pending_ui_matches_live_run(self):
        code, out, err = self.cli([os.path.join(FIXTURES, "spec_example.json"), "--literal"])
        pend = json.loads(err)["data"]["pending_ui"]
        campos = [p["campo"] for p in pend]
        # as 4 pendências vistas ao vivo + a publicação (condicional)
        self.assertEqual(campos, ["meta.document_title", "settings.close.response_limit", "theme.color",
                                  "responses.sheet_access", "publish.audience"])
        self.assertIn("condicao", pend[-1])
        self.assertNotIn("condicao", pend[0])


class TestRefusals(Base):

    def test_given_draft_when_convert_then_refused_without_output(self):
        for flag in (["--literal"], ["--out", None]):
            argv = [os.path.join(FIXTURES, "spec_draft.json")]
            out_path = os.path.join(self.tmp, "nao.gs")
            argv += [out_path if a is None else a for a in flag]
            code, out, err = self.cli(argv)
            payload = json.loads(out if "--out" in flag else err)
            self.assertEqual(code, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["status"], "invalid")
            self.assertTrue(any("SPEC-APR-04" in p for p in payload["problems"]))
            if "--literal" in flag:
                self.assertEqual(out, "")
            self.assertFalse(os.path.exists(out_path))

    def test_given_pending_owner_when_convert_then_status_pending_owner(self):
        code, out, err = self.cli([os.path.join(FIXTURES, "spec_pending_owner.json"), "--literal"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(json.loads(err)["status"], "pending_owner")

    def test_given_spec_with_error_when_convert_then_invalid(self):
        spec = load("spec_example.json")
        spec["sections"][0]["items"][0]["title"] = ""
        code, out, err = self.cli([self.write_spec(spec), "--literal"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(err)["status"], "invalid")

    def test_given_missing_file_when_convert_then_usage_error(self):
        code, out, _ = self.cli([os.path.join(self.tmp, "nao-existe.json"), "--literal"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["status"], "usage_error")

    def test_given_no_output_or_both_when_convert_then_usage_error(self):
        path = os.path.join(FIXTURES, "spec_example.json")
        code, out, _ = self.cli([path])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["status"], "usage_error")
        code, out, _ = self.cli([path, "--literal", "--out", os.path.join(self.tmp, "a.gs")])
        self.assertEqual(code, 2)

    def test_given_yaml_without_pyyaml_when_convert_then_usage_error(self):
        path = os.path.join(self.tmp, "s.yaml")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("a: 1\n")
        code, out, _ = self.cli([path, "--literal"], yaml_module=None)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["status"], "usage_error")

    def test_given_existing_out_when_no_force_then_refuses_and_force_overwrites(self):
        out_path = os.path.join(self.tmp, "g.gs")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("antigo")
        argv = [os.path.join(FIXTURES, "spec_example.json"), "--out", out_path]
        code, out, _ = self.cli(argv)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["status"], "exists")
        with open(out_path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "antigo")
        code, out, _ = self.cli(argv + ["--force"])
        self.assertEqual(code, 0)
        with open(out_path, encoding="utf-8") as fh:
            self.assertIn("var SPEC", fh.read())

    def test_given_template_without_markers_when_out_then_template_issue(self):
        tpl = os.path.join(self.tmp, "t.gs")
        with open(tpl, "w", encoding="utf-8") as fh:
            fh.write("var SPEC = {};\n")
        out_path = os.path.join(self.tmp, "g.gs")
        code, out, _ = self.cli([os.path.join(FIXTURES, "spec_example.json"), "--out", out_path, "--template", tpl])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["status"], "template_issue")
        self.assertFalse(os.path.exists(out_path))

    def test_given_markers_in_wrong_order_when_render_then_message(self):
        text, why = sg.render_gs(sg.END + "\nx\n" + sg.BEGIN + "\n", "b")
        self.assertIsNone(text)
        self.assertIn("antes", why)


class TestPendingUi(unittest.TestCase):

    def test_given_features_apps_script_lacks_when_pending_ui_then_each_listed(self):
        # Given
        spec = {
            "meta": {"title": "T", "document_title": "Arq"},
            "settings": {"send_copy": "always", "disable_autosave": True,
                         "close": {"at": "2027-01-01T00:00:00-03:00", "response_limit": None}},
            "theme": {"font": "Roboto"},
            "quiz": {"enabled": True, "release": "after_manual_review"},
            "responses": {"sheet": "existing", "sheet_ref": "Planilha X", "sheet_access": "equipe"},
            "publish": {"published": True, "audience": "specific", "responders": ["a@b.c"], "notify_responders": True},
            "sections": [
                {"id": "s1", "items": [
                    {"id": "q1", "type": "rating", "title": "R", "rating": {"max": 5}},
                    {"id": "q2", "type": "file_upload", "title": "F"},
                    {"id": "q3", "type": "linear_scale", "title": "E", "scale": {"low": 1, "high": 2}},
                    {"id": "q4", "type": "mc_grid", "title": "G", "grid": {"rows": ["a"], "columns": ["b"], "shuffle_rows": True}},
                    {"id": "q5", "type": "image", "title": "I", "image": {"source": "foto.png"}},
                    {"id": "q6", "type": "video", "title": "V", "video": {"youtube_url": "u", "caption": "leg"}},
                    {"id": "q7", "type": "multiple_choice", "title": "M", "answer_key": ["x"],
                     "options": [{"value": "x", "go_to": "s2"}, {"value": "y", "go_to": "s2"}],
                     "feedback": {"right": "ok", "general": "g"}},
                    {"id": "q8", "type": "short_text", "title": "S", "answer_key": ["z"], "feedback": {"wrong": "no"}},
                ]},
                {"id": "s2", "title": "B", "after_section": "s1", "items": []},
            ],
        }
        # When
        campos = [p["campo"] for p in sg.pending_ui(spec)]
        # Then
        for esperado in ("meta.document_title", "settings.send_copy", "settings.disable_autosave", "settings.close.at",
                         "theme.font", "quiz.release", "quiz.respondent_sees", "q1 (rating)", "q2 (file_upload)",
                         "q3.scale", "q4.grid.shuffle_rows", "q5.image.source", "q6.video.caption", "q7.answer_key",
                         "q7.feedback.general", "q8.answer_key", "q8.feedback.wrong", "s2.after_section",
                         "responses.sheet", "responses.sheet_access", "publish.notify_responders"):
            self.assertIn(esperado, campos)
        self.assertNotIn("settings.close.response_limit", campos)
        self.assertNotIn("publish.audience", campos)  # specific com responders é aplicado pelo script
        self.assertNotIn("q7.feedback.right", campos)  # q7 tem gabarito: right é aplicável

    def test_given_plain_spec_when_pending_ui_then_empty(self):
        spec = {"meta": {"title": "T"}, "sections": [{"id": "s1", "items": [
            {"id": "q1", "type": "short_text", "title": "N"}]}]}
        self.assertEqual(sg.pending_ui(spec), [])


@unittest.skipUnless(HAS_YAML, "PyYAML não instalado")
class TestYamlTemplates(Base):

    def test_given_seven_templates_when_found_then_all_present(self):
        self.assertEqual(len(SPEC_TEMPLATES), 7)

    def test_given_draft_templates_when_convert_then_gate_refuses(self):
        for path in SPEC_TEMPLATES:
            with self.subTest(template=os.path.basename(path)):
                code, out, err = self.cli([path, "--literal"])
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertIn(json.loads(err)["status"], ("invalid", "pending_owner"))

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_templates_when_literal_built_then_node_value_equals_spec(self):
        import yaml
        for path in SPEC_TEMPLATES:
            with self.subTest(template=os.path.basename(path)):
                err, data, _ = vs.load_spec(path, yaml)
                self.assertIsNone(err)
                literal = sg.spec_literal(data)
                got = self.node_json(literal + "\nconsole.log(JSON.stringify(SPEC));")
                self.assertEqual(got, sg.normalize(data))

    @unittest.skipUnless(NODE, "node não encontrado")
    def test_given_templates_approved_when_out_then_generated_gs_is_valid_js(self):
        """Aprova o modelo (sem pending_owner) à força, só para provar o caminho completo."""
        import yaml
        convertidos = 0
        for path in SPEC_TEMPLATES:
            with self.subTest(template=os.path.basename(path)):
                err, data, _ = vs.load_spec(path, yaml)
                data = copy.deepcopy(data)
                data["status"] = "approved"
                data["approved_at"] = "2026-11-11"
                spec_path = self.write_spec(data)
                code, _, _ = self.cli([spec_path, "--literal"])
                if code != 0:  # ainda tem pending_owner ou erro do modelo: o gate recusou, correto
                    continue
                out_path = os.path.join(self.tmp, "t%d.gs" % self.n)
                code, out, _ = self.cli([spec_path, "--out", out_path])
                self.assertEqual(code, 0, out)
                with open(out_path, encoding="utf-8") as fh:
                    self.node_check(fh.read())
                convertidos += 1
        self.assertGreaterEqual(convertidos, 1)


if __name__ == "__main__":
    unittest.main()
