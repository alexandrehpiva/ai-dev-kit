"""Testes do lint_doc.py (Dado/Quando/Então). Rodar: python3 -m unittest discover -s scripts/tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LINT = Path(__file__).resolve().parent.parent / "lint_doc.py"
LOREM = "Texto de apoio para passar do mínimo de caracteres do documento. " * 6

GOOD = """<html><body><p>%s</p>
<ul class="toc"><li><a href="#s1"><span class="n">1</span><span class="t">Sobre</span><span class="p">3</span></a></li></ul>
<section id="s1"><h1>Sobre</h1>
<table><thead><tr><th>Controle</th><th>Origem</th></tr></thead>
<tbody><tr><td>WAF</td><td><span class="chip si">Reunião</span></td></tr></tbody></table></section></body></html>""" % LOREM


def run(html, *extra):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "doc.html"
        p.write_text(html, encoding="utf-8")
        r = subprocess.run([sys.executable, str(LINT), str(p), "--json", *extra], capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)


class LintTests(unittest.TestCase):
    def test_documento_valido_passa(self):
        code, out = run(GOOD)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["errors"], [])

    def test_celula_de_origem_vazia_reprova(self):
        code, out = run(GOOD.replace('<span class="chip si">Reunião</span>', ""))
        self.assertEqual(code, 1)
        self.assertTrue(any("Origem" in e for e in out["errors"]), out)

    def test_link_interno_quebrado_reprova(self):
        code, out = run(GOOD.replace('href="#s1"', 'href="#nao-existe"'))
        self.assertEqual(code, 1)
        self.assertTrue(any("nao-existe" in e for e in out["errors"]), out)

    def test_marcador_esquecido_reprova(self):
        code, out = run(GOOD.replace("Texto de apoio", "TODO revisar", 1))
        self.assertEqual(code, 1)
        self.assertTrue(any("todo" in e.lower() for e in out["errors"]), out)

    def test_placeholder_de_template_reprova(self):
        code, out = run(GOOD.replace("Texto de apoio", "veja {xref('s1', 'x')}", 1))
        self.assertEqual(code, 1, out)

    def test_termo_proibido_reprova(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "proibidos.txt"
            f.write_text("# nomes\nFulano de Tal\n", encoding="utf-8")
            code, out = run(GOOD.replace("Texto de apoio", "Elaborado por fulano de tal.", 1), "--forbid", str(f))
        self.assertEqual(code, 1)
        self.assertTrue(any("proibido" in e for e in out["errors"]), out)

    def test_nome_ambiguo_vira_aviso_nao_falha(self):
        code, out = run(GOOD.replace("Texto de apoio", "O Acme Pay recebe o pedido.", 1), "--ambiguous", "Acme Pay=Portal")
        self.assertEqual(code, 0, out)
        self.assertTrue(any("ambíguo" in w for w in out["warnings"]), out)

    def test_toc_sem_pagina_avisa_sem_pdf(self):
        code, out = run(GOOD.replace('<span class="p">3</span>', '<span class="p"></span>'))
        self.assertEqual(code, 0, out)
        self.assertTrue(any("sumário" in w for w in out["warnings"]), out)


if __name__ == "__main__":
    unittest.main()
