# -*- coding: utf-8 -*-
"""Testes do check_setup.py (tudo simulado; nada é lido do sistema real)."""

import json
import os
import plistlib
import unittest

from helpers import FakeEnv, fixture, run_main
import check_setup as cs
import configure_mcp as cm

HOME = "/Users/teste"
PROJ = "/work/proj"
LS = HOME + "/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
BRAVE_APP = "/Applications/Brave Browser.app"
BRAVE_EXE = BRAVE_APP + "/Contents/MacOS/Brave Browser"
BRAVE_UDD = HOME + "/Library/Application Support/BraveSoftware/Brave-Browser"
SECRET = "segredo-que-nao-pode-vazar-123"  # gitleaks:allow (fixture falsa de teste)
NEIGHBOR_SECRET = "vizinho-literal-NAO-PODE-VAZAR-456"  # gitleaks:allow (fixture falsa de teste)


def server(mode="extension", token="${PLAYWRIGHT_MCP_EXTENSION_TOKEN}", exe=BRAVE_EXE, pkg="0.0.85"):
    args = ["-y", "@playwright/mcp@" + pkg]
    if mode == "extension":
        args += ["--extension", "--executable-path", exe]
    else:
        args += ["--executable-path", exe, "--user-data-dir", "/tmp/perfil"]
    srv = {"type": "stdio", "command": "npx", "args": args}
    if token is not None and mode == "extension":
        srv["env"] = {cm.TOKEN_ENV: token}
    return srv


def make_env(node="v22.11.0", files=None, environ=None, npx=True):
    f = {LS: plistlib.dumps({"LSHandlers": [{"LSHandlerURLScheme": "https",
                                             "LSHandlerRoleAll": "com.brave.browser"}]}),
         BRAVE_APP + "/Contents/Info.plist": fixture("macos_brave_info.plist"), BRAVE_EXE: b""}
    f.update(files or {})
    which, run = {}, {}
    if node:
        which["node"] = "/usr/local/bin/node"
        run[("/usr/local/bin/node", "-v")] = (0, node + "\n")
        if npx:
            which["npx"] = "/usr/local/bin/npx"
    e = {"HOME": HOME}
    e.update(environ or {})
    return FakeEnv("macos", environ=e, files=f, which=which, run=run)


def check(env, *argv):
    code, out, raw = run_main(cs.main, ["--project-dir", PROJ] + list(argv), env)
    return code, out, raw


class NodeTests(unittest.TestCase):

    def test_node_ausente(self):
        code, out, _ = check(make_env(node=None))
        self.assertEqual((code, out["status"]), (1, "node_missing"))

    def test_npx_ausente(self):
        code, out, _ = check(make_env(npx=False))
        self.assertEqual(out["status"], "node_missing")

    def test_node_antigo(self):
        code, out, _ = check(make_env(node="v18.20.8"))
        self.assertEqual((code, out["status"]), (1, "node_too_old"))

    def test_node_impar_so_avisa(self):
        _, out, _ = check(make_env(node="v25.9.0"))
        self.assertEqual(out["status"], "mcp_not_registered")
        self.assertTrue(any("ímpar" in p for p in out["problems"]))


class RegistrationTests(unittest.TestCase):

    def test_sem_registro(self):
        code, out, _ = check(make_env())
        self.assertEqual((code, out["status"]), (1, "mcp_not_registered"))

    def test_cursor_extensao_sem_token(self):
        files = {HOME + "/.cursor/mcp.json": json.dumps({"mcpServers": {"playwright-browser": server(
            token="${env:PLAYWRIGHT_MCP_EXTENSION_TOKEN}")}})}
        code, out, _ = check(make_env(files=files))
        self.assertEqual((code, out["status"]), (1, "token_missing"))
        self.assertEqual(out["data"]["selected"]["token_config"], "env_reference")

    def test_cursor_extensao_com_token_fica_ready_sem_vazar(self):
        files = {HOME + "/.cursor/mcp.json": json.dumps({"mcpServers": {"playwright-browser": server(
            token="${env:PLAYWRIGHT_MCP_EXTENSION_TOKEN}")}})}
        code, out, raw = check(make_env(files=files, environ={cm.TOKEN_ENV: SECRET}))
        self.assertEqual((code, out["status"]), (0, "ready"))
        self.assertEqual(out["data"]["token"]["env_length"], len(SECRET))
        self.assertNotIn(SECRET, raw)

    def test_claude_escopo_local_em_claude_json(self):
        doc = {"projects": {PROJ: {"mcpServers": {"playwright-browser": server(mode="profile")}}}}
        code, out, _ = check(make_env(files={HOME + "/.claude.json": json.dumps(doc)}), "--harness", "claude")
        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["data"]["selected"]["scope"], "local")
        self.assertFalse(out["data"]["token"]["required"])

    def test_codex_env_vars(self):
        toml = ('[mcp_servers.playwright-browser]\ncommand = "npx"\nargs = ["-y", "@playwright/mcp@0.0.85", '
                '"--extension", "--executable-path", "%s"]\nenv_vars = ["%s"]\n' % (BRAVE_EXE, cm.TOKEN_ENV))
        env = make_env(files={HOME + "/.codex/config.toml": toml}, environ={cm.TOKEN_ENV: SECRET})
        code, out, _ = check(env, "--harness", "codex")
        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["data"]["selected"]["token_config"], "env_forward")

    def test_token_literal_em_projeto_e_denunciado_sem_imprimir(self):
        files = {PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright-browser": server(token=SECRET)}})}
        code, out, raw = check(make_env(files=files))
        self.assertNotIn(SECRET, raw)
        self.assertEqual(out["data"]["selected"]["token_config"], "literal")
        self.assertTrue(any("texto puro" in p for p in out["problems"]))

    def test_vscode_input(self):
        files = {PROJ + "/.vscode/mcp.json": json.dumps({"servers": {"playwright-browser": server(
            token="${input:playwright-extension-token}")}})}
        code, out, _ = check(make_env(files=files), "--harness", "vscode")
        self.assertEqual(out["status"], "ready")

    def test_outro_nome_avisa(self):
        files = {PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright": server(mode="profile")}})}
        code, out, _ = check(make_env(files=files))
        self.assertEqual(out["status"], "mcp_not_registered")
        self.assertTrue(any("outro nome" in p for p in out["problems"]))

    def test_executavel_inexistente_e_browser_issue(self):
        files = {PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright-browser": server(
            mode="profile", exe="/Applications/Sumiu.app/Contents/MacOS/Sumiu")}})}
        code, out, _ = check(make_env(files=files))
        self.assertEqual((code, out["status"]), (1, "browser_issue"))


class ExtensionProfileTests(unittest.TestCase):

    def test_extensao_instalada_no_perfil(self):
        ext = BRAVE_UDD + "/Default/Extensions/" + cs.db.EXTENSION_ID + "/0.5.0_0/manifest.json"
        files = {ext: b"{}", PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright-browser": server()}})}
        _, out, _ = check(make_env(files=files, environ={cm.TOKEN_ENV: "x"}))
        self.assertEqual(out["data"]["extension"]["installed"], True)
        self.assertEqual(out["data"]["extension"]["profiles"], ["Default"])

    def test_extensao_ausente_vira_proximo_passo(self):
        files = {BRAVE_UDD + "/Default/Extensions/outra-extensao/1.0_0/manifest.json": b"{}",
                 BRAVE_UDD + "/Profile 1/Extensions/outra-extensao/1.0_0/manifest.json": b"{}",
                 PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright-browser": server()}})}
        _, out, _ = check(make_env(files=files, environ={cm.TOKEN_ENV: "x"}))
        self.assertIs(out["data"]["extension"]["installed"], False)
        self.assertTrue(any("chromewebstore" in s for s in out["next_steps"]))

    def test_nao_le_preferences_do_perfil(self):
        # Given um perfil cujo Preferences cita o ID da extensão, mas sem a pasta Extensions/<id>/
        prefs = BRAVE_UDD + "/Default/Preferences"
        secure = BRAVE_UDD + "/Default/Secure Preferences"
        files = {prefs: json.dumps({"extensions": {"settings": {cs.db.EXTENSION_ID: {}}}}),
                 secure: json.dumps({"x": cs.db.EXTENSION_ID}),
                 PROJ + "/.mcp.json": json.dumps({"mcpServers": {"playwright-browser": server()}})}
        env = make_env(files=files, environ={cm.TOKEN_ENV: "x"})
        # When o check_setup roda
        _, out, _ = check(env)
        # Then nenhum arquivo do perfil é lido e a extensão conta como ausente
        self.assertNotIn(prefs, env.reads)
        self.assertNotIn(secure, env.reads)
        self.assertFalse(any(p.startswith(BRAVE_UDD) for p in env.reads), env.reads)
        self.assertIs(out["data"]["extension"]["installed"], False)


class RedactionTests(unittest.TestCase):

    def test_nao_imprime_env_nem_args_secretos_de_servidores(self):
        # Given um registro com token literal em env e um arg de credencial, num arquivo de usuário
        srv = server(token=SECRET)
        srv["args"] = srv["args"] + ["--api-key=" + NEIGHBOR_SECRET]
        srv["headers"] = {"Authorization": "Bearer " + NEIGHBOR_SECRET}
        files = {HOME + "/.cursor/mcp.json": json.dumps({"mcpServers": {
            "playwright-browser": srv,
            "vizinho": {"command": "node", "args": ["@playwright/mcp", "--token", NEIGHBOR_SECRET],
                        "env": {"API_KEY": NEIGHBOR_SECRET}}}})}
        # When o check_setup roda
        code, out, raw = check(make_env(files=files))
        # Then nenhum valor secreto aparece no stdout, só nomes de chaves e marcadores
        self.assertNotIn(SECRET, raw)
        self.assertNotIn(NEIGHBOR_SECRET, raw)
        self.assertEqual(out["data"]["selected"]["token_config"], "literal")
        self.assertEqual(out["data"]["selected"]["env_keys"], [cm.TOKEN_ENV])
        self.assertIn("--api-key=<redacted:%d chars>" % len(NEIGHBOR_SECRET), out["data"]["selected"]["args"])


class OptionalPyyamlTests(unittest.TestCase):

    def _ready_env(self):
        files = {HOME + "/.cursor/mcp.json": json.dumps({"mcpServers": {"playwright-browser": server(
            token="${env:PLAYWRIGHT_MCP_EXTENSION_TOKEN}")}})}
        return make_env(files=files, environ={cm.TOKEN_ENV: SECRET})

    def _with_pyyaml(self, present):
        original = cs.pyyaml_available
        cs.pyyaml_available = lambda: present
        self.addCleanup(lambda: setattr(cs, "pyyaml_available", original))

    def test_pyyaml_ausente_avisa_sem_mudar_status(self):
        """Dado ambiente pronto sem PyYAML, quando checa, então ready, optional.pyyaml=false e próximo passo."""
        self._with_pyyaml(False)
        code, out, _ = check(self._ready_env())
        self.assertEqual((code, out["status"]), (0, "ready"))
        self.assertIs(out["data"]["optional"]["pyyaml"], False)
        self.assertTrue(any("pip install --user pyyaml" in s and "JSON" in s for s in out["next_steps"]))

    def test_pyyaml_presente_nao_avisa(self):
        """Dado PyYAML disponível, então optional.pyyaml=true e nenhum próximo passo sobre ele."""
        self._with_pyyaml(True)
        _, out, _ = check(self._ready_env())
        self.assertIs(out["data"]["optional"]["pyyaml"], True)
        self.assertFalse(any("pyyaml" in s.lower() for s in out["next_steps"]))


class SkillDirTests(unittest.TestCase):

    def test_project_dir_na_pasta_da_skill_avisa(self):
        # Given a raiz do projeto apontando para a própria pasta da skill
        # When o check_setup roda
        _, out, _ = run_main(cs.main, ["--project-dir", cm.SKILL_DIR], make_env())
        # Then há um aviso em problems pedindo a raiz do projeto
        self.assertTrue(any("pasta da skill" in p and "--project-dir" in p for p in out["problems"]))

    def test_subpasta_da_skill_tambem_avisa(self):
        _, out, _ = run_main(cs.main, ["--project-dir", os.path.join(cm.SKILL_DIR, "scripts")], make_env())
        self.assertTrue(any("pasta da skill" in p for p in out["problems"]))

    def test_projeto_normal_nao_avisa(self):
        _, out, _ = check(make_env())
        self.assertFalse(any("pasta da skill" in p for p in out["problems"]))


if __name__ == "__main__":
    unittest.main()
