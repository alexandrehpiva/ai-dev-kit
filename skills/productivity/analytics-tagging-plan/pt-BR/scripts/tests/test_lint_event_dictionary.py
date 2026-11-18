"""Testes do lint_event_dictionary.py (Dado/Quando/Então). Rodar: python3 -m unittest discover -s scripts/tests -v"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINT = ROOT / "lint_event_dictionary.py"
SKILL = ROOT.parent
COLS = ["id", "event_name", "event_type", "description", "when_fires", "gtm_trigger", "parameters", "key_event",
        "kpi", "owner", "implementer", "consent_required", "pii_reviewed", "acceptance_criteria", "status", "plan_version"]


def row(**over):
    base = {"id": "EVT-001", "event_name": "view_flow_step", "event_type": "custom", "description": "d",
            "when_fires": "tela monta", "gtm_trigger": "CE - view_flow_step", "parameters": "flow_id:string;step_name:enum",
            "key_event": "no", "kpi": "KPI-01", "owner": "Produto", "implementer": "Front", "consent_required": "yes",
            "pii_reviewed": "2026-01-01 · A", "acceptance_criteria": "1 por entrada", "status": "proposed", "plan_version": "1.0.0"}
    base.update(over)
    return base


def run(rows, *extra, cols=COLS):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "dict.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return run_path(p, *extra)


def run_path(p, *extra):
    r = subprocess.run([sys.executable, str(LINT), str(p), *extra], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def codes(out, key="problems"):
    return {x["code"] for x in out[key]}


class LintTests(unittest.TestCase):
    def test_dicionario_valido_passa(self):
        code, out = run([row()])
        self.assertEqual(code, 0, out)
        self.assertTrue(out["ok"])
        self.assertEqual(out["problems"], [])

    def test_nome_acima_de_40_caracteres_falha(self):
        code, out = run([row(event_name="a" * 41)])
        self.assertEqual(code, 1)
        self.assertIn("event_name_too_long", codes(out))

    def test_nome_com_40_caracteres_passa(self):
        code, out = run([row(event_name="a" * 40)])
        self.assertEqual(code, 0, out)

    def test_nome_fora_de_snake_case_falha(self):
        for bad in ("ViewStep", "view-step", "view step", "1_view"):
            code, out = run([row(event_name=bad)])
            self.assertEqual(code, 1, bad)
            self.assertIn("not_snake_case", codes(out), bad)

    def test_nome_reservado_falha_exceto_se_automatico(self):
        code, out = run([row(event_name="session_start")])
        self.assertIn("reserved_event", codes(out))
        code, out = run([row(event_name="session_start", event_type="automatic")])
        self.assertEqual(code, 0, out)

    def test_prefixo_proibido_falha(self):
        code, out = run([row(event_name="ga_click")])
        self.assertIn("forbidden_prefix", codes(out))
        code, out = run([row(event_name="firebase_x")])
        self.assertIn("forbidden_prefix", codes(out))

    def test_mais_de_25_parametros_falha(self):
        params = ";".join("p%d" % i for i in range(26))
        code, out = run([row(parameters=params)])
        self.assertIn("too_many_params", codes(out))

    def test_25_parametros_passa_com_aviso_de_proximidade(self):
        params = ";".join("p%d" % i for i in range(25))
        code, out = run([row(parameters=params)])
        self.assertEqual(code, 0, out)
        self.assertIn("many_params", codes(out, "warnings"))

    def test_parametro_invalido_longo_ou_com_prefixo_falha(self):
        code, out = run([row(parameters="9abc;" + "x" * 41 + ";google_x;firebase_conversion")])
        self.assertEqual(code, 1)
        self.assertTrue({"bad_param_name", "param_name_too_long", "forbidden_param_prefix", "reserved_param"} <= codes(out))

    def test_parametro_duplicado_no_evento_falha(self):
        code, out = run([row(parameters="flow_id;flow_id")])
        self.assertIn("duplicate_param", codes(out))

    def test_campos_obrigatorios_vazios_falham(self):
        for col in ("owner", "gtm_trigger", "acceptance_criteria"):
            code, out = run([row(**{col: ""})])
            self.assertEqual(code, 1, col)
            self.assertIn("missing_field", codes(out), col)

    def test_parametro_pii_falha(self):
        for bad in ("cpf", "email_usuario", "customer_phone", "telefone", "document_number", "rg", "endereco",
                    "first_name", "nome", "name", "cep", "birth_date"):
            code, out = run([row(parameters="flow_id;" + bad)])
            self.assertEqual(code, 1, bad)
            self.assertIn("pii_param", codes(out), bad)

    def test_parametros_legitimos_nao_sao_pii(self):
        code, out = run([row(parameters="step_name;flow_name;document_type;error_code;partner_count")])
        self.assertEqual(code, 0, out)

    def test_allow_libera_parametro(self):
        code, out = run([row(parameters="document_number")], "--allow", "document_number")
        self.assertEqual(code, 0, out)

    def test_termos_extras_de_pii(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.txt"
            t.write_text("# comentario\nprotocolo\n", encoding="utf-8")
            code, out = run([row(parameters="protocolo")], "--pii-terms", str(t))
            self.assertIn("pii_param", codes(out))

    def test_duplicatas_de_evento_e_id_falham(self):
        code, out = run([row(), row()])
        self.assertTrue({"duplicate_id", "duplicate_event"} <= codes(out))

    def test_tipo_e_key_event_invalidos_falham(self):
        code, out = run([row(event_type="magico", key_event="talvez")])
        self.assertTrue({"bad_event_type", "bad_key_event"} <= codes(out))

    def test_avisos_nao_derrubam(self):
        code, out = run([row(pii_reviewed="", kpi="", implementer="", event_type="recommended", event_name="x_unknown")])
        self.assertEqual(code, 0, out)
        self.assertTrue({"pii_not_reviewed", "orphan_event", "no_implementer", "recommended_unknown"} <= codes(out, "warnings"))

    def test_muitos_key_events_avisa(self):
        rows = [row(id="E%d" % i, event_name="ev_%d" % i, key_event="yes") for i in range(6)]
        code, out = run(rows)
        self.assertEqual(code, 0, out)
        self.assertIn("many_key_events", codes(out, "warnings"))

    def test_coluna_ausente_falha(self):
        code, out = run([row()], cols=[c for c in COLS if c != "owner"])
        self.assertEqual(code, 1)
        self.assertIn("missing_columns", codes(out))

    def test_csv_vazio_falha(self):
        code, out = run([])
        self.assertIn("empty", codes(out))

    def test_arquivo_inexistente_sai_com_2(self):
        code, out = run_path(Path("/nonexistent/dict.csv"))
        self.assertEqual(code, 2)
        self.assertFalse(out["ok"])

    def test_template_e_exemplo_da_skill_passam(self):
        for rel in ("templates/event-dictionary.template.csv", "examples/event-dictionary.example.csv"):
            code, out = run_path(SKILL / rel)
            self.assertEqual(code, 0, (rel, out))


if __name__ == "__main__":
    unittest.main()
