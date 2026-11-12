# -*- coding: utf-8 -*-
"""Testes do check_setup.py (adaptador sobre o check_setup.py da skill playwright-mcp).

Tudo roda contra uma skill playwright-mcp FALSA em diretório temporário. Nenhum perfil, configuração
de harness ou token reais são lidos; o único teste com a skill real roda com HOME e projeto vazios.
"""

import json
import os
import unittest

from helpers import Sandbox, called, clean_environ, make_fake_pm, pm_payload, run_main, set_response
import check_setup as cs

SECRET = "token-falso-que-nao-pode-vazar-123"  # gitleaks:allow (fixture falsa de teste)
FORMS_URL = "https://docs.google.com/forms/u/0/"


class AdapterCase(unittest.TestCase):
    """Monta, em pasta temporária, o layout instalado: skills/google-forms e skills/playwright-mcp."""

    def setUp(self):
        self.sb = Sandbox()
        self.addCleanup(self.sb.cleanup)
        self.skills = self.sb.path("skills")
        self.gf = os.path.join(self.skills, "google-forms")
        os.makedirs(self.gf)
        self.project = self.sb.path("projeto")
        os.makedirs(self.project)

    def pm(self, payload=None, exit_code=0, raw_stdout=None):
        return make_fake_pm(self.skills, payload, exit_code, raw_stdout)

    def run_check(self, argv=(), environ=None, skill_dir=None, project=True):
        args = (["--project-dir", self.project] if project else []) + list(argv)
        ctx = cs.Context(environ=environ if environ is not None else clean_environ(),
                         skill_dir=skill_dir or self.gf)
        return run_main(cs.main, args, ctx)


class DelegationTests(AdapterCase):

    def test_roda_o_check_da_playwright_mcp_isolado_em_modo_extension_e_repassa_os_argumentos(self):
        """Dado a skill irmã, quando checa, então o subprocesso usa -I -B, --mode extension e os argumentos."""
        pm = self.pm()
        code, out, _ = self.run_check(["--harness", "cursor", "--server-name", "meu-servidor"])
        c = called(pm)
        self.assertEqual((code, out["status"]), (0, "ready"))
        self.assertEqual(c["argv"], ["--mode", "extension", "--harness", "cursor", "--server-name", "meu-servidor",
                                     "--project-dir", self.project])
        self.assertEqual(c["isolated"], 1)
        self.assertTrue(c["dont_write_bytecode"])

    def test_sem_server_name_deixa_o_padrao_da_playwright_mcp(self):
        """Dado nenhum --server-name, então ele não é repassado (a playwright-mcp escolhe o do modo extension)."""
        pm = self.pm()
        self.run_check()
        self.assertNotIn("--server-name", called(pm)["argv"])
        self.assertIn("auto", called(pm)["argv"])

    def test_herda_o_diretorio_atual_e_o_ambiente_sem_ler_o_token(self):
        """Dado token no ambiente, então o filho o enxerga e o adaptador não o imprime."""
        pm = self.pm()
        env = clean_environ(PLAYWRIGHT_MCP_EXTENSION_TOKEN=SECRET)
        code, out, raw = self.run_check(environ=env, project=False)
        self.assertEqual(code, 0)
        self.assertTrue(called(pm)["token_visible"])
        self.assertNotIn(SECRET, raw)
        self.assertEqual(os.path.realpath(called(pm)["cwd"]), os.path.realpath(os.getcwd()))

    def test_ambiente_sem_pythonpath_funciona(self):
        """Dado ambiente sem PYTHONPATH, então a delegação funciona (nada depende de caminho mágico)."""
        self.pm()
        env = clean_environ()
        self.assertNotIn("PYTHONPATH", env)
        code, out, _ = self.run_check(environ=env)
        self.assertEqual(out["status"], "ready")


class StatusTests(AdapterCase):

    def test_ready_troca_o_proximo_passo_generico_pelo_do_forms(self):
        """Dado ready, então o próximo passo manda abrir a lista do Forms e o genérico some."""
        self.pm(pm_payload("ready", next_steps=["Faça a verificação final: browser_navigate em uma página qualquer."]))
        code, out, _ = self.run_check()
        self.assertEqual((code, out["ok"]), (0, True))
        self.assertTrue(out["next_steps"][0].startswith("Faça a verificação final: browser_navigate em " + FORMS_URL))
        self.assertEqual(len([s for s in out["next_steps"] if s.startswith("Faça a verificação final")]), 1)

    def test_status_acionaveis_passam_sem_alteracao_com_exit_1(self):
        """Dado cada status acionável da playwright-mcp, então o status e o exit 1 são os mesmos."""
        for status in ("node_missing", "node_too_old", "browser_issue", "mcp_not_registered", "token_missing"):
            with self.subTest(status=status):
                pm = os.path.join(self.skills, "playwright-mcp")
                if not os.path.isdir(pm):
                    pm = self.pm()
                set_response(pm, pm_payload(status, problems=["problema de " + status], next_steps=["passo"]),
                             exit_code=1)
                code, out, _ = self.run_check()
                self.assertEqual((code, out["ok"], out["status"]), (1, False, status))
                self.assertIn("problema de " + status, out["problems"])

    def test_dados_da_playwright_mcp_sao_preservados(self):
        """Dado data da playwright-mcp, então continua lá, mais optional e playwright_mcp.dir."""
        pm = self.pm(pm_payload("ready", data={"mode": "extension", "token": {"required": True, "env_length": 9}}))
        _, out, _ = self.run_check()
        self.assertEqual(out["data"]["token"], {"required": True, "env_length": 9})
        self.assertEqual(out["data"]["playwright_mcp"]["dir"], pm)
        self.assertIn("pyyaml", out["data"]["optional"])

    def test_erro_de_uso_da_playwright_mcp_vira_exit_2(self):
        """Dado usage_error (exit 2) no filho, então o adaptador também sai com 2 e não acrescenta nota."""
        self.pm(pm_payload("usage_error", problems=["Uso inválido: x"]), exit_code=2)
        code, out, _ = self.run_check()
        self.assertEqual((code, out["status"]), (2, "usage_error"))
        self.assertFalse(any("Os passos acima" in s for s in out["next_steps"]))

    def test_comando_citado_ganha_o_caminho_real_da_playwright_mcp(self):
        """Dado passo que cita configure_mcp.py, então sai com o caminho da skill playwright-mcp."""
        pm = self.pm(pm_payload("mcp_not_registered",
                                problems=["detect_browser: sem Chromium"],
                                next_steps=["Registre o servidor com configure_mcp.py (plano, --apply)."]), exit_code=1)
        _, out, _ = self.run_check()
        expected = os.path.join(pm, "scripts", "configure_mcp.py")
        self.assertIn('"%s"' % expected, out["next_steps"][0])
        self.assertEqual(out["problems"][0], "detect_browser: sem Chromium")  # prefixo sem .py fica como está

    def test_nao_ready_aponta_os_assets_da_playwright_mcp(self):
        """Dado status não ready, então há um passo final nomeando os assets da playwright-mcp."""
        self.pm(pm_payload("token_missing"), exit_code=1)
        _, out, _ = self.run_check()
        self.assertTrue(any("extension-mode.md" in s and "playwright-mcp" in s for s in out["next_steps"]))


class PyyamlTests(AdapterCase):

    def _with_pyyaml(self, present):
        original = cs.pyyaml_available
        cs.pyyaml_available = lambda: present
        self.addCleanup(lambda: setattr(cs, "pyyaml_available", original))

    def test_pyyaml_ausente_avisa_sem_mudar_status(self):
        """Dado ambiente pronto sem PyYAML, então ready, optional.pyyaml=false e próximo passo de instalação."""
        self.pm()
        self._with_pyyaml(False)
        code, out, _ = self.run_check()
        self.assertEqual((code, out["status"]), (0, "ready"))
        self.assertIs(out["data"]["optional"]["pyyaml"], False)
        self.assertTrue(any("pip install --user pyyaml" in s and "JSON" in s for s in out["next_steps"]))
        self.assertTrue(any("PyYAML ausente" in p for p in out["problems"]))

    def test_pyyaml_presente_nao_avisa(self):
        """Dado PyYAML disponível, então optional.pyyaml=true e nenhum próximo passo sobre ele."""
        self.pm()
        self._with_pyyaml(True)
        _, out, _ = self.run_check()
        self.assertIs(out["data"]["optional"]["pyyaml"], True)
        self.assertFalse(any("pyyaml" in s.lower() for s in out["next_steps"]))

    def test_pyyaml_tambem_e_avisado_quando_o_status_nao_e_ready(self):
        """Dado token_missing e sem PyYAML, então o status continua token_missing e o aviso aparece."""
        self.pm(pm_payload("token_missing"), exit_code=1)
        self._with_pyyaml(False)
        code, out, _ = self.run_check()
        self.assertEqual((code, out["status"]), (1, "token_missing"))
        self.assertIs(out["data"]["optional"]["pyyaml"], False)


class LocatorTests(AdapterCase):

    def test_variavel_de_ambiente_tem_prioridade_sobre_a_pasta_irma(self):
        """Dado GFORMS_PLAYWRIGHT_MCP_DIR e uma irmã, então vale a variável."""
        self.pm(pm_payload("token_missing"), exit_code=1)  # irmã
        other = make_fake_pm(self.sb.path("outro"), pm_payload("ready"), rel=("pm-em-outro-lugar",))
        env = clean_environ(GFORMS_PLAYWRIGHT_MCP_DIR=other)
        code, out, _ = self.run_check(environ=env)
        self.assertEqual((code, out["status"], out["data"]["playwright_mcp"]["dir"]), (0, "ready", other))

    def test_acha_a_pasta_irma_no_layout_instalado(self):
        """Dado skills/google-forms e skills/playwright-mcp, então acha a irmã."""
        pm = self.pm()
        _, out, _ = self.run_check()
        self.assertEqual(out["data"]["playwright_mcp"]["dir"], pm)

    def test_acha_pelo_layout_do_repositorio(self):
        """Dado productivity/google-forms/pt-BR e productivity/playwright-mcp/pt-BR, então acha a segunda."""
        repo = self.sb.path("repo", "productivity")
        gf = os.path.join(repo, "google-forms", "pt-BR")
        os.makedirs(gf)
        pm = make_fake_pm(repo, pm_payload("ready"), rel=("playwright-mcp", "pt-BR"))
        code, out, _ = self.run_check(skill_dir=gf)
        self.assertEqual((code, out["data"]["playwright_mcp"]["dir"]), (0, pm))

    def test_instalacao_por_symlink_acha_a_irma_do_link_e_nao_so_a_do_destino(self):
        """Dado google-forms instalada por symlink para pt-BR e a irmã ao lado do link, então acha a irmã."""
        repo_gf = self.sb.path("repo", "productivity", "google-forms", "pt-BR")
        os.makedirs(repo_gf)
        link = os.path.join(self.skills, "google-forms-link")
        try:
            os.symlink(repo_gf, link)
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("sem permissão para criar symlink")
        pm = self.pm()
        _, out, _ = self.run_check(skill_dir=link)
        self.assertEqual(out["data"]["playwright_mcp"]["dir"], pm)

    def test_ausente_vira_playwright_mcp_missing_com_passo_de_instalacao(self):
        """Dado nenhuma playwright-mcp, então status novo, exit 1 e o passo de instalar a skill."""
        code, out, _ = self.run_check()
        self.assertEqual((code, out["ok"], out["status"]), (1, False, "playwright_mcp_missing"))
        self.assertIsNone(out["data"]["playwright_mcp"]["dir"])
        self.assertTrue(out["data"]["playwright_mcp"]["tried"])
        self.assertTrue(any("ai-dev-kit skills install --skills productivity/playwright-mcp" in s
                            and "GFORMS_PLAYWRIGHT_MCP_DIR" in s for s in out["next_steps"]))

    def test_variavel_apontando_para_diretorio_vazio_e_missing_e_nao_cai_na_irma(self):
        """Dado variável para pasta sem check_setup.py, então missing, citando a variável, mesmo com irmã boa."""
        self.pm()
        empty = self.sb.path("vazio")
        os.makedirs(empty)
        code, out, _ = self.run_check(environ=clean_environ(GFORMS_PLAYWRIGHT_MCP_DIR=empty))
        self.assertEqual((code, out["status"]), (1, "playwright_mcp_missing"))
        self.assertTrue(any("GFORMS_PLAYWRIGHT_MCP_DIR" in p and empty in p for p in out["problems"]))

    def test_missing_tambem_traz_o_aviso_de_pyyaml(self):
        """Dado missing e sem PyYAML, então data.optional.pyyaml existe e é false."""
        original = cs.pyyaml_available
        cs.pyyaml_available = lambda: False
        self.addCleanup(lambda: setattr(cs, "pyyaml_available", original))
        _, out, _ = self.run_check()
        self.assertIs(out["data"]["optional"]["pyyaml"], False)


class FailureTests(AdapterCase):

    def test_filho_sem_json_vira_playwright_mcp_error(self):
        """Dado filho que imprime texto, então playwright_mcp_error com exit 1."""
        self.pm(raw_stdout="Traceback (most recent call last): boom", exit_code=1)
        code, out, _ = self.run_check()
        self.assertEqual((code, out["status"]), (1, "playwright_mcp_error"))
        self.assertTrue(any("não devolveu JSON" in p for p in out["problems"]))

    def test_filho_com_json_fora_do_contrato_vira_playwright_mcp_error(self):
        """Dado JSON sem 'status', então playwright_mcp_error."""
        self.pm(raw_stdout=json.dumps({"ok": True}))
        _, out, _ = self.run_check()
        self.assertEqual(out["status"], "playwright_mcp_error")

    def test_timeout_vira_playwright_mcp_error(self):
        """Dado filho que passa do limite, então playwright_mcp_error citando o tempo."""
        pm = self.pm()
        with open(os.path.join(pm, "scripts", "check_setup.py"), "w") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        rc, payload, err = cs.run_playwright_mcp(pm, [], clean_environ(), timeout=1)
        self.assertIsNone(payload)
        self.assertIn("passou de 1 s", err)

    def test_argumento_invalido_do_adaptador_e_usage_error_em_json(self):
        """Dado --harness inexistente, então JSON usage_error e exit 2."""
        self.pm()
        code, out, _ = self.run_check(["--harness", "navegador-x"])
        self.assertEqual((code, out["status"]), (2, "usage_error"))


class SkillDirTests(AdapterCase):

    def test_project_dir_na_pasta_da_skill_avisa(self):
        """Dado a raiz do projeto apontando para a pasta da skill, então há aviso pedindo a raiz do projeto."""
        self.pm()
        code, out, _ = run_main(cs.main, ["--project-dir", self.gf],
                                cs.Context(environ=clean_environ(), skill_dir=self.gf))
        self.assertTrue(any("pasta da skill" in p and "--project-dir" in p for p in out["problems"]))

    def test_subpasta_da_skill_tambem_avisa(self):
        """Dado uma subpasta da skill como raiz, então avisa."""
        self.pm()
        sub = os.path.join(self.gf, "scripts")
        os.makedirs(sub)
        _, out, _ = run_main(cs.main, ["--project-dir", sub], cs.Context(environ=clean_environ(), skill_dir=self.gf))
        self.assertTrue(any("pasta da skill" in p for p in out["problems"]))

    def test_projeto_normal_nao_avisa(self):
        """Dado um projeto fora da skill, então não avisa."""
        self.pm()
        _, out, _ = self.run_check()
        self.assertFalse(any("pasta da skill" in p for p in out["problems"]))


REAL_PM = os.path.normpath(os.path.join(cs.SKILL_DIR, "..", "..", "playwright-mcp", "pt-BR"))


@unittest.skipUnless(os.path.isfile(os.path.join(REAL_PM, "scripts", "check_setup.py")),
                     "skill playwright-mcp real ausente (layout do repositório)")
class RealPlaywrightMcpContractTests(unittest.TestCase):

    def test_contrato_com_a_skill_real_com_home_e_projeto_vazios(self):
        """Dado a playwright-mcp do repositório e HOME vazio, então o JSON volta no contrato e nada é lido do usuário."""
        sb = Sandbox()
        self.addCleanup(sb.cleanup)
        home = sb.path("home")
        project = sb.path("proj")
        os.makedirs(home)
        os.makedirs(project)
        env = clean_environ(HOME=home, USERPROFILE=home, GFORMS_PLAYWRIGHT_MCP_DIR=REAL_PM)
        code, out, _ = run_main(cs.main, ["--project-dir", project], cs.Context(environ=env))
        self.assertIn(code, (0, 1))
        self.assertEqual(set(out), {"ok", "status", "data", "problems", "next_steps"})
        self.assertNotEqual(out["status"], "usage_error")
        self.assertNotEqual(out["status"], "ready")  # sem servidor registrado no HOME vazio
        self.assertEqual(out["data"]["mode"], "extension")
        self.assertIn("pyyaml", out["data"]["optional"])


if __name__ == "__main__":
    unittest.main()
