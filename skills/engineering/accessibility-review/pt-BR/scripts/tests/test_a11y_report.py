#!/usr/bin/env python3
"""Testes do a11y_report.py, do contrast.py e da consistência de CRITERIA.md (biblioteca padrão).

Rodar: python3 -m unittest discover -s tests   (dentro de scripts/)
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
SKILL = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import a11y_report as rep  # noqa: E402
import contrast as ct  # noqa: E402


def rule(rid, wcag, impact="serious", nodes=1):
    return {"id": rid, "impact": impact, "wcag": wcag, "tags": [], "help": rid, "helpUrl": f"https://x/{rid}",
            "nodeCount": nodes, "nodes": [{"target": ["#a"], "html": "<a>", "summary": ""}] * nodes}


def scan_doc(violations=(), incomplete=(), passed=()):
    run = {"scan": "home", "url": "file:///x.html", "viewport": {"name": "desktop", "width": 1280, "height": 800}, "title": "t",
           "axe": {"violations": list(violations), "incomplete": list(incomplete), "passed": len(passed), "inapplicable": 0,
                   "passedRules": list(passed)}}
    return {"ok": True, "status": "ok", "data": {"tool": {"axe": "4.14.0"}, "tags": ["wcag2a"], "runs": [run]}, "problems": [], "questions": []}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.rows, problems = rep.parse_criteria(SKILL / "CRITERIA.md")
        self.assertEqual(problems, [])

    def tearDown(self):
        self.tmp.cleanup()

    def classify(self, code, scan=None, evidence=None):
        runs = []
        if scan is not None:
            path = self.dir / "scan.json"
            path.write_text(json.dumps(scan), encoding="utf-8")
            runs, problems, _ = rep.load_scans([path])
            self.assertEqual(problems, [])
        findings, passed = rep.collect_findings(runs)
        row = next(r for r in self.rows if r["code"] == code)
        problems = []
        return rep.classify(row, findings, passed, evidence or {}, problems), problems


class CriteriaTable(Base):
    def test_has_the_55_criteria_of_wcag_22_a_and_aa(self):
        self.assertEqual(len(self.rows), 55)
        self.assertEqual(sum(r["level"] == "A" for r in self.rows), 31)
        self.assertEqual(sum(r["level"] == "AA" for r in self.rows), 24)

    def test_4_1_1_is_not_listed_because_it_was_removed_in_wcag_22(self):
        self.assertNotIn("4.1.1", {r["code"] for r in self.rows})

    def test_manual_rows_have_no_axe_rules_and_partial_rows_have(self):
        for r in self.rows:
            if r["verification"] == "manual":
                self.assertEqual(r["axe_rules"], [], r["code"])
            else:
                self.assertTrue(r["axe_rules"], r["code"])

    def test_every_roteiro_exists_as_a_section_of_manual_checks(self):
        text = (SKILL / "manual-checks.md").read_text(encoding="utf-8")
        headings = set(re.findall(r"^## (M\d+) —", text, re.M))
        used = {r["roteiro"] for r in self.rows}
        self.assertTrue(used <= headings, f"roteiros sem seção: {sorted(used - headings)}")

    def test_malformed_row_is_reported(self):
        bad = self.dir / "bad.md"
        bad.write_text("<criterios>\n| 1.1.1 | A | x | parcial |\n| 1.1.2 | Z | x | manual | — | M1 | sempre |\n</criterios>", encoding="utf-8")
        rows, problems = rep.parse_criteria(bad)
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 2)


class Classification(Base):
    def test_no_scan_no_evidence_is_not_verified_never_passed(self):
        for r in self.rows:
            res, _ = self.classify(r["code"])
            self.assertEqual(res["state"], "Não verificado", r["code"])

    def test_clean_scan_alone_does_not_pass_a_criterion(self):
        res, _ = self.classify("1.1.1", scan_doc(passed=["image-alt"]))
        self.assertEqual(res["state"], "Não verificado")
        self.assertIn("image-alt", res["note"])

    def test_automatic_violation_fails_with_severity_from_impact(self):
        res, _ = self.classify("1.4.3", scan_doc(violations=[rule("color-contrast", ["1.4.3"], "serious")]))
        self.assertEqual((res["state"], res["severity"], res["origin"]), ("Falhou", "Alta", "automático"))

    def test_incomplete_asks_for_manual_review(self):
        res, _ = self.classify("1.4.3", scan_doc(incomplete=[rule("color-contrast", ["1.4.3"])]))
        self.assertEqual(res["state"], "Revisar")

    def test_evidence_passed_requires_real_text(self):
        res, problems = self.classify("1.4.1", evidence={"1.4.1": {"status": "passou", "evidencia": "ok"}})
        self.assertEqual(res["state"], "Não verificado")
        self.assertTrue(any("evidência vazia" in p for p in problems))

    def test_evidence_with_text_passes(self):
        res, problems = self.classify("1.4.1", evidence={"1.4.1": {"status": "passou", "evidencia": "Erro tem ícone e texto além da cor", "telas": ["Home"]}})
        self.assertEqual((res["state"], res["origin"], res["screens"]), ("Passou", "manual", ["Home"]))
        self.assertEqual(problems, [])

    def test_evidence_passed_against_automatic_failure_is_a_conflict(self):
        res, _ = self.classify("1.4.3", scan_doc(violations=[rule("color-contrast", ["1.4.3"])]),
                               {"1.4.3": {"status": "passou", "evidencia": "Medi 7:1 no contrast.py"}})
        self.assertEqual(res["state"], "Conflito")

    def test_manual_failure_needs_severity(self):
        res, problems = self.classify("2.4.7", evidence={"2.4.7": {"status": "falhou", "evidencia": "Foco some no botão Continuar"}})
        self.assertEqual(res["state"], "Falhou")
        self.assertTrue(any("severidade" in p for p in problems))

    def test_not_applicable_needs_justification(self):
        res, problems = self.classify("1.2.2", evidence={"1.2.2": {"status": "nao-aplica", "evidencia": ""}})
        self.assertEqual(res["state"], "Não verificado")
        self.assertTrue(problems)
        res, problems = self.classify("1.2.2", evidence={"1.2.2": {"status": "nao-aplica", "evidencia": "O protótipo não tem vídeo"}})
        self.assertEqual(res["state"], "Não se aplica")

    def test_invalid_status_is_rejected(self):
        res, problems = self.classify("1.4.1", evidence={"1.4.1": {"status": "conforme", "evidencia": "texto longo o bastante"}})
        self.assertEqual(res["state"], "Não verificado")
        self.assertTrue(any("status de evidência inválido" in p for p in problems))


class Cli(Base):
    def test_markdown_and_json_outputs(self):
        scan = self.dir / "scan.json"
        scan.write_text(json.dumps(scan_doc(violations=[rule("image-alt", ["1.1.1"], "critical")])), encoding="utf-8")
        ev = self.dir / "ev.json"
        ev.write_text(json.dumps({"1.4.1": {"status": "passou", "evidencia": "Cor nunca é o único sinal"}, "9.9.9": {"status": "passou", "evidencia": "não existe"}}), encoding="utf-8")
        out = self.dir / "r.md"
        code = rep.main(["--scan", str(scan), "--evidence", str(ev), "--out", str(out), "--title", "T", "--date", "2026-10-28"])
        self.assertEqual(code, 0)
        md = out.read_text(encoding="utf-8")
        self.assertIn("# Avaliação de acessibilidade — T", md)
        self.assertIn("55 critérios", md)
        self.assertIn("evidência para critério desconhecido: 9.9.9", md)
        self.assertIn("\"Não verificado\" não é \"Passou\"", md)
        out_json = self.dir / "r.json"
        rep.main(["--scan", str(scan), "--format", "json", "--out", str(out_json)])
        data = json.loads(out_json.read_text(encoding="utf-8"))["data"]
        self.assertEqual(data["summary"]["Falhou"], 1)
        self.assertEqual(sum(data["summary"].values()), 55)

    def test_unusable_scan_is_reported_not_swallowed(self):
        scan = self.dir / "scan.json"
        scan.write_text(json.dumps({"ok": False, "status": "missing-tools", "data": {}}), encoding="utf-8")
        out = self.dir / "r.json"
        rep.main(["--scan", str(scan), "--format", "json", "--out", str(out)])
        doc = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(doc["status"], "with-warnings")
        self.assertTrue(any("missing-tools" in p for p in doc["problems"]))


class Contrast(unittest.TestCase):
    def test_reference_ratios(self):
        self.assertEqual(ct.evaluate("#000", "#fff")["ratio"], 21.0)
        self.assertEqual(ct.evaluate("#767676", "#ffffff")["ratio"], 4.54)
        self.assertTrue(ct.evaluate("#767676", "#fff")["texto_normal_1_4_3"])

    def test_just_below_threshold_does_not_round_up(self):
        res = ct.evaluate("#777777", "#ffffff")
        self.assertFalse(res["texto_normal_1_4_3"])
        self.assertTrue(res["texto_grande_1_4_3"])

    def test_formats_and_errors(self):
        self.assertEqual(ct.parse_color("#abc"), (170, 187, 204))
        self.assertEqual(ct.parse_color("rgb(1, 2, 3)"), (1, 2, 3))
        for bad in ("rgba(0,0,0,.5)", "red", "#12", "rgb(300,0,0)"):
            with self.assertRaises(ValueError):
                ct.parse_color(bad)

    def test_order_of_colors_does_not_matter(self):
        self.assertEqual(ct.ratio("#123456", "#ffffff"), ct.ratio("#ffffff", "#123456"))


if __name__ == "__main__":
    unittest.main()
