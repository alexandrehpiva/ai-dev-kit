"""Testes de build_tickets_html.py e lint_tickets.py (Dado/Quando/Então).
Rodar: python3 -m unittest discover -s scripts/tests -v
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
EXAMPLE = SCRIPTS.parent / "templates" / "tickets.example.json"
TEMPLATE = SCRIPTS.parent / "templates" / "tickets.template.html"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / ("%s.py" % name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load("build_tickets_html")
lint = load("lint_tickets")


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def ticket(spec, code):
    return next(t for t in spec["tickets"] if t["code"] == code)


def run_lint(spec):
    raw = json.dumps(spec, ensure_ascii=False)
    report, _ = lint.lint(spec, raw)
    return report


class ExampleTests(unittest.TestCase):
    def test_example_passes_lint_clean(self):
        """Dado o exemplo da skill, quando passa no lint, então não há erro nem aviso."""
        report = run_lint(example())
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])

    def test_example_builds_html(self):
        """Dado o exemplo, quando gera o HTML, então cada chamado vira uma seção em página nova."""
        html_text = build.build(example(), TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(html_text.count('<section class="ticket'), 4)
        self.assertIn("Texto para colar", html_text)
        self.assertNotIn("{{", html_text)


class BuildTests(unittest.TestCase):
    def test_placeholder_is_escaped(self):
        """Dado um placeholder <ARN>, quando renderiza, então aparece escapado (visível no PDF)."""
        self.assertIn("&lt;ARN_KMS&gt;", build.inline("troquem <ARN_KMS> pelo ARN"))

    def test_pending_is_highlighted(self):
        """Dado [A CONFIRMAR: x], quando renderiza, então ganha a classe pend."""
        self.assertIn('<span class="pend">[A CONFIRMAR: centro de custo]</span>',
                      build.inline("CostCenter=[A CONFIRMAR: centro de custo]"))

    def test_code_and_bold(self):
        """Dado `código` e **negrito**, quando renderiza, então vira <code> e <b>."""
        out = build.inline("Use `acme` e **só** isso")
        self.assertIn("<code>acme</code>", out)
        self.assertIn("<b>só</b>", out)

    def test_code_block_is_escaped(self):
        """Dado um bloco JSON com placeholder, quando renderiza, então o bloco é <pre> escapado."""
        out = build.render_items([{"code": "{\"Resource\": \"<ARN>\"}"}])
        self.assertTrue(out.startswith("<pre>"))
        self.assertIn("&lt;ARN&gt;", out)

    def test_invalid_kind_fails(self):
        """Dado kind desconhecido, quando renderiza, então falha com mensagem."""
        spec = example()
        spec["tickets"][0]["kind"] = "outro"
        with self.assertRaises(ValueError):
            build.build(spec, TEMPLATE.read_text(encoding="utf-8"))

    def test_signature_can_be_disabled(self):
        """Dado signature false, quando renderiza, então o rodapé do solicitante não aparece no chamado."""
        spec = example()
        t = ticket(spec, "INF-01")
        t["paste"]["signature"] = False
        out = build.render_ticket(t, spec["requester"])
        self.assertNotIn("Usuário de rede", out)

    def test_cli_writes_file(self):
        """Dado o exemplo, quando roda o CLI, então grava o HTML e sai com 0."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.html"
            proc = subprocess.run([sys.executable, str(SCRIPTS / "build_tickets_html.py"), str(EXAMPLE), str(out)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype html>"))


class LintErrorTests(unittest.TestCase):
    def test_angle_quotes(self):
        """Dado aspas angulares no texto, quando passa no lint, então é erro."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["lead"] = "Solicito o «banco»."
        self.assertTrue(any("aspas angulares" in e for e in run_lint(spec).errors))

    def test_duplicate_code(self):
        """Dado dois chamados com o mesmo código, quando passa no lint, então é erro."""
        spec = example()
        spec["tickets"].append(copy.deepcopy(ticket(spec, "INF-01")))
        self.assertTrue(any("repetido" in e for e in run_lint(spec).errors))

    def test_ticket_without_paste(self):
        """Dado chamado sem texto para colar, quando passa no lint, então é erro."""
        spec = example()
        del ticket(spec, "INF-01")["paste"]
        self.assertTrue(any("Texto para colar" in e for e in run_lint(spec).errors))

    def test_deploy_without_build_section(self):
        """Dado chamado de deploy sem "Build e deploy", quando passa no lint, então é erro."""
        spec = example()
        t = ticket(spec, "INF-08")
        t["paste"]["sections"] = [s for s in t["paste"]["sections"] if s["title"] != "Build e deploy"]
        self.assertTrue(any("Build e deploy" in e for e in run_lint(spec).errors))

    def test_deploy_build_section_incomplete(self):
        """Dado "Build e deploy" sem branch nem entrypoint, quando passa no lint, então é erro listando o que falta."""
        spec = example()
        section = next(s for s in ticket(spec, "INF-08")["paste"]["sections"] if s["title"] == "Build e deploy")
        section["items"] = ["Repositório: um só. Dockerfile na raiz. Uma imagem. Variáveis iguais."]
        errors = run_lint(spec).errors
        self.assertTrue(any("incompleta" in e and "branch" in e and "entrypoint" in e for e in errors))

    def test_container_pipeline_requires_build_section(self):
        """Dado esteira de contêiner (Helm) sem "Build e deploy", quando passa no lint, então é erro."""
        spec = example()
        spec["tickets"].append({
            "code": "INF-07", "title": "Esteira da API", "case": "ci-cd-pipeline",
            "paste": {"lead": "Solicito a esteira da API com deploy por Helm.",
                      "sections": [{"title": "Esteira", "items": ["Build, scan e publicação."]}]},
        })
        self.assertTrue(any("INF-07" in e and "Build e deploy" in e for e in run_lint(spec).errors))

    def test_static_front_pipeline_does_not_require_build_section(self):
        """Dado esteira de front estático, quando passa no lint, então não exige "Build e deploy"."""
        spec = example()
        spec["tickets"].append({
            "code": "INF-10", "title": "Esteira do front", "case": "ci-cd-pipeline",
            "paste": {"lead": "Solicito a esteira do front estático.",
                      "sections": [{"title": "Esteira", "items": ["pnpm build e sync para o bucket."]}]},
        })
        self.assertFalse(any("INF-10" in e for e in run_lint(spec).errors))

    def test_invalid_json_block(self):
        """Dado bloco JSON inválido, quando passa no lint, então é erro."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append({"code": "{\"Rules\": [}"})
        self.assertTrue(any("JSON inválido" in e for e in run_lint(spec).errors))

    def test_wildcard_action(self):
        """Dado política com Action "*", quando passa no lint, então é erro."""
        spec = example()
        policy = {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append({"code": json.dumps(policy)})
        self.assertTrue(any("curinga" in e for e in run_lint(spec).errors))

    def test_secret_value(self):
        """Dado uma senha em texto, quando passa no lint, então é erro."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["sections"][1]["items"].append("senha: Sup3rSecreta!")
        self.assertTrue(any("segredo" in e for e in run_lint(spec).errors))


class LintWarningTests(unittest.TestCase):
    def test_backstage_phrase(self):
        """Dado frase de bastidor, quando passa no lint, então é aviso."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append("Os valores nunca por chamado ou chat.")
        self.assertTrue(any("bastidor" in w for w in run_lint(spec).warnings))

    def test_long_item(self):
        """Dado tópico com mais de 300 caracteres, quando passa no lint, então é aviso."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append("x" * 320)
        self.assertTrue(any("tópico longo" in w for w in run_lint(spec).warnings))

    def test_env_leak(self):
        """Dado nome de produção num documento de homologação, quando passa no lint, então é aviso."""
        spec = example()
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append("Instância: acme-orders-db-prd.")
        self.assertTrue(any("outro ambiente" in w for w in run_lint(spec).warnings))

    def test_missing_return_section(self):
        """Dado banco sem "Preciso de volta", quando passa no lint, então é aviso."""
        spec = example()
        t = ticket(spec, "INF-01")
        t["paste"]["sections"] = [s for s in t["paste"]["sections"] if s["title"] != "Preciso de volta"]
        self.assertTrue(any("Preciso de volta" in w for w in run_lint(spec).warnings))

    def test_wildcard_resource_with_write(self):
        """Dado Resource "*" com ação de escrita, quando passa no lint, então é aviso."""
        spec = example()
        policy = {"Statement": [{"Effect": "Allow", "Action": ["s3:PutObject"], "Resource": "*"}]}
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append({"code": json.dumps(policy)})
        self.assertTrue(any("Resource" in w for w in run_lint(spec).warnings))

    def test_wildcard_resource_read_only_is_fine(self):
        """Dado Resource "*" só com leitura (List/Describe/Get), quando passa no lint, então não avisa."""
        spec = example()
        policy = {"Statement": [{"Effect": "Allow", "Action": ["cloudwatch:GetMetricData"], "Resource": "*"}]}
        ticket(spec, "INF-01")["paste"]["sections"][0]["items"].append({"code": json.dumps(policy)})
        self.assertFalse(any("Resource" in w for w in run_lint(spec).warnings))

    def test_cli_exit_codes(self):
        """Dado o exemplo, quando roda o CLI, então sai com 0; com erro, sai com 1."""
        ok = subprocess.run([sys.executable, str(SCRIPTS / "lint_tickets.py"), str(EXAMPLE)], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        spec = example()
        del ticket(spec, "INF-01")["paste"]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps(spec), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPTS / "lint_tickets.py"), str(bad)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
