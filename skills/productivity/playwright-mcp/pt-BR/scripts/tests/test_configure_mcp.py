# -*- coding: utf-8 -*-
"""Testes do configure_mcp.py. Gravações só em pastas temporárias (HOME falso)."""

import glob
import json
import os
import shutil
import tempfile
import unittest

from helpers import FakeEnv, run_main
import configure_mcp as cm
import detect_browser as db

SECRET = "valor-secreto-do-token-NAO-PODE-APARECER"  # gitleaks:allow (fixture falsa de teste)
NEIGHBOR = "FAKE-NEIGHBOR-SECRET-123456"  # gitleaks:allow (fixture falsa de teste)
LITERAL_TOKEN = "FAKE-LITERAL-TOKEN-XYZ-7890"  # gitleaks:allow (fixture falsa de teste)
HEADER_TOKEN = "FAKE-HEADER-BEARER-abcdef"  # gitleaks:allow (fixture falsa de teste)


class TmpHome(unittest.TestCase):
    """Cada teste ganha um HOME falso e um 'Brave' falso dentro dele."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwmcp-w3-")
        self.home = os.path.join(self.tmp, "home")
        self.proj = os.path.join(self.tmp, "proj")
        os.makedirs(self.home)
        os.makedirs(self.proj)
        exe_dir = os.path.join(self.tmp, "Apps", "Brave Browser.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        self.brave = os.path.join(exe_dir, "Brave Browser")
        open(self.brave, "w").close()
        self.environ = {"HOME": self.home, "USERPROFILE": self.home, "PATH": os.environ.get("PATH", ""),
                        cm.TOKEN_ENV: SECRET}
        self.env = db.SystemEnv(os_name=db.host_os() if db.host_os() != "windows" else "linux",
                                environ=self.environ)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cfg(self, *extra, **kw):
        argv = ["--browser", self.brave, "--project-dir", self.proj] + list(extra)
        code, out, raw = run_main(cm.main, argv, kw.get("env", self.env))
        for sec in (SECRET, NEIGHBOR, LITERAL_TOKEN, HEADER_TOKEN):
            self.assertNotIn(sec, raw, "um valor secreto vazou na saída")
        self.last_raw = raw
        return code, out

    def write(self, path, text):
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()


class PlanApplyTests(TmpHome):

    def test_plano_nao_grava_nada(self):
        code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension")
        self.assertEqual((code, out["status"]), (0, "planned"))
        self.assertFalse(os.path.exists(os.path.join(self.proj, ".mcp.json")))
        self.assertIn("playwright-browser", out["data"]["diff"])
        self.assertEqual(out["data"]["file"], os.path.join(self.proj, ".mcp.json"))

    def test_apply_cria_e_segunda_vez_e_idempotente(self):
        args = ("--harness", "claude", "--scope", "project", "--mode", "extension")
        code, out = self.run_cfg(*(args + ("--apply",)))
        self.assertEqual((code, out["status"]), (0, "applied"))
        self.assertIsNone(out["data"]["backup"])  # arquivo novo: nada para copiar
        path = os.path.join(self.proj, ".mcp.json")
        doc = json.loads(self.read(path))
        srv = doc["mcpServers"]["playwright-browser"]
        self.assertEqual(srv["args"][:3], ["-y", "@playwright/mcp@0.0.85", "--extension"])
        self.assertEqual(srv["args"][3:], ["--executable-path", self.brave])
        self.assertEqual(srv["env"], {cm.TOKEN_ENV: "${%s}" % cm.TOKEN_ENV})
        self.assertNotIn(SECRET, self.read(path))
        code, out = self.run_cfg(*(args + ("--apply",)))
        self.assertEqual((code, out["status"]), (0, "already_configured"))
        self.assertEqual(glob.glob(path + ".bak-*"), [])

    def test_merge_preserva_outros_servidores_e_faz_backup(self):
        path = os.path.join(self.home, ".cursor", "mcp.json")
        os.makedirs(os.path.dirname(path))
        original = {"mcpServers": {"outro": {"command": "node", "args": ["x.js"]}}, "extra": 1}
        with open(path, "w") as fh:
            json.dump(original, fh, indent=4)
        code, out = self.run_cfg("--harness", "cursor", "--scope", "user", "--mode", "extension", "--apply")
        self.assertEqual(out["status"], "applied")
        doc = json.loads(self.read(path))
        self.assertEqual(doc["mcpServers"]["outro"], original["mcpServers"]["outro"])
        self.assertEqual(doc["extra"], 1)
        self.assertEqual(doc["mcpServers"]["playwright-browser"]["env"][cm.TOKEN_ENV],
                         "${env:%s}" % cm.TOKEN_ENV)
        self.assertTrue(os.path.exists(out["data"]["backup"]))
        self.assertEqual(json.loads(self.read(out["data"]["backup"])), original)
        self.assertIn('    "mcpServers"', self.read(path))  # indentação de 4 preservada

    def test_conflito_nao_sobrescreve_sem_force(self):
        path = os.path.join(self.proj, ".mcp.json")
        before = json.dumps({"mcpServers": {"playwright-browser": {"command": "npx", "args": ["outro"]}}})
        with open(path, "w") as fh:
            fh.write(before)
        code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension", "--apply")
        self.assertEqual((code, out["status"]), (1, "conflict"))
        self.assertEqual(self.read(path), before)
        self.assertEqual(out["data"]["existing_server"]["args"], ["outro"])
        code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension",
                                 "--apply", "--force")
        self.assertEqual((code, out["status"]), (0, "applied"))
        self.assertEqual(self.read(out["data"]["backup"]), before)

    def test_jsonc_exige_force(self):
        path = os.path.join(self.proj, ".vscode", "mcp.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as fh:
            fh.write('{\n  // comentário\n  "servers": {},\n}\n')
        code, out = self.run_cfg("--harness", "vscode", "--scope", "project", "--mode", "extension", "--apply")
        self.assertEqual((code, out["status"]), (1, "conflict"))
        self.assertIn("comentário", self.read(path))
        code, out = self.run_cfg("--harness", "vscode", "--scope", "project", "--mode", "extension", "--apply",
                                 "--force")
        self.assertEqual(out["status"], "applied")

    def test_json_invalido(self):
        path = os.path.join(self.home, ".gemini", "settings.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as fh:
            fh.write("{ isto não é json")
        code, out = self.run_cfg("--harness", "gemini", "--scope", "user", "--mode", "extension")
        self.assertEqual(code, 1)
        self.assertTrue(any("JSON" in p for p in out["problems"]))


class RedactionTests(TmpHome):
    """B-1: nenhum valor secreto de nenhum servidor aparece no stdout; o arquivo mantém os reais."""

    def neighbor_doc(self):
        return {"mcpServers": {"vizinho": {
            "command": "node", "args": ["srv.js", "--api-key", NEIGHBOR, "--auth=" + NEIGHBOR],
            "env": {"API_KEY": NEIGHBOR, "OUTRA_REF": "${env:OUTRA}"},
            "headers": {"Authorization": "Bearer " + HEADER_TOKEN}}}}

    def test_vizinho_com_env_literal_planned(self):
        # Given um mcp.json do Cursor com um servidor vizinho com env/headers/args literais
        path = os.path.join(self.home, ".cursor", "mcp.json")
        self.write(path, json.dumps(self.neighbor_doc(), indent=2))
        # When o plano é gerado
        code, out = self.run_cfg("--harness", "cursor", "--scope", "user", "--mode", "extension")
        # Then nenhum valor aparece no stdout (run_cfg confere), o diff mostra marcadores e preserva refs
        self.assertEqual((code, out["status"]), (0, "planned"))
        self.assertIn('"Authorization": "<redacted:%d chars>"' % len("Bearer " + HEADER_TOKEN),
                      out["data"]["diff"])
        # e o texto inteiro, redigido para exibição, troca env literal e mantém referência
        red = cm.Redactor()
        red.learn_text(self.read(path), "json")
        shown = red.scrub(self.read(path))
        self.assertIn('"API_KEY": "<redacted:%d chars>"' % len(NEIGHBOR), shown)
        self.assertNotIn(NEIGHBOR, shown)
        self.assertIn('"OUTRA_REF": "${env:OUTRA}"', shown)
        self.assertIn('"${env:%s}"' % cm.TOKEN_ENV, out["data"]["diff"])
        self.assertIn(NEIGHBOR, self.read(path))  # nada gravado

    def test_vizinho_com_env_literal_applied_mantem_valor_real_no_arquivo(self):
        # Given o mesmo vizinho
        path = os.path.join(self.home, ".cursor", "mcp.json")
        self.write(path, json.dumps(self.neighbor_doc(), indent=2))
        # When aplica
        code, out = self.run_cfg("--harness", "cursor", "--scope", "user", "--mode", "extension", "--apply")
        # Then o stdout segue sem segredo e o arquivo gravado tem os valores reais
        self.assertEqual((code, out["status"]), (0, "applied"))
        doc = json.loads(self.read(path))
        self.assertEqual(doc["mcpServers"]["vizinho"], self.neighbor_doc()["mcpServers"]["vizinho"])
        self.assertIn(NEIGHBOR, self.read(out["data"]["backup"]))

    def test_mesmo_servidor_com_token_literal_conflict(self):
        # Given o próprio servidor já registrado com o token literal
        path = os.path.join(self.proj, ".mcp.json")
        before = json.dumps({"mcpServers": {"playwright-browser": {
            "command": "npx", "args": ["-y", "@playwright/mcp@0.0.80", "--extension"],
            "env": {cm.TOKEN_ENV: LITERAL_TOKEN}}}}, indent=2)
        self.write(path, before)
        # When roda sem --force
        code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension", "--apply")
        # Then conflict, sem o token no stdout e com marcador em existing_server
        self.assertEqual((code, out["status"]), (1, "conflict"))
        self.assertEqual(out["data"]["existing_server"]["env"][cm.TOKEN_ENV],
                         "<redacted:%d chars>" % len(LITERAL_TOKEN))
        self.assertEqual(self.read(path), before)
        # When força a substituição
        code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension",
                                 "--apply", "--force")
        # Then o diff mostra só o marcador e o backup guarda o valor real
        self.assertEqual((code, out["status"]), (0, "applied"))
        self.assertIn("<redacted:%d chars>" % len(LITERAL_TOKEN), out["data"]["diff"])
        self.assertIn(LITERAL_TOKEN, self.read(out["data"]["backup"]))

    def test_codex_toml_vizinho_com_env_literal(self):
        path = os.path.join(self.home, ".codex", "config.toml")
        self.write(path, '[mcp_servers.vizinho]\ncommand = "node"\n\n[mcp_servers.vizinho.env]\n'
                         'API_KEY = "%s"\n' % NEIGHBOR)
        code, out = self.run_cfg("--harness", "codex", "--scope", "user", "--mode", "extension", "--apply")
        self.assertEqual(out["status"], "applied")
        self.assertIn('API_KEY = "%s"' % NEIGHBOR, self.read(path))

    def test_jsonc_conflict_tambem_redige(self):
        path = os.path.join(self.proj, ".cursor", "mcp.json")
        self.write(path, '{\n  // c\n  "mcpServers": {"v": {"command": "x", "env": {"K": "%s"}}},\n}\n' % NEIGHBOR)
        code, out = self.run_cfg("--harness", "cursor", "--scope", "project", "--mode", "extension")
        self.assertEqual(out["status"], "conflict")


class RedactorUnitTests(unittest.TestCase):

    def test_referencias_nao_sao_redigidas(self):
        for ref in ("${VAR}", "${env:VAR}", "${input:x-y}", "%VAR%", "$VAR", "Bearer ${env:T}"):
            self.assertTrue(cm.is_reference(ref), ref)
            self.assertEqual(cm.Redactor().mask(ref), ref)
        for lit in ("abc", "${VAR}-sufixo", "Bearer abc"):
            self.assertFalse(cm.is_reference(lit), lit)

    def test_rede_de_seguranca_nao_corrompe_palavras_comuns(self):
        # Given um valor de env comum e um com cara de token aprendidos
        r = cm.Redactor()
        r.tree({"env": {"A": "Fulano", "B": "tok-123456789"}})
        # When um texto livre cita os dois sem aspas
        out = r.scrub("/Users/Fulano/x tok-123456789")
        # Then só o token é trocado; o literal entre aspas de ambos é trocado
        self.assertEqual(out, "/Users/Fulano/x <redacted:13 chars>")
        self.assertEqual(r.scrub('"Fulano"'), '"<redacted:6 chars>"')

    def test_author_nao_e_credencial_mas_authorization_e(self):
        r = cm.Redactor()
        self.assertEqual(r.tree({"author": "Fulano", "Authorization": "x"}),
                         {"author": "Fulano", "Authorization": "<redacted:1 chars>"})

    def test_args_com_cara_de_credencial(self):
        r = cm.Redactor()
        out = r.args(["--token", "abcdef1", "--api-key=xyz", "Authorization: Bearer qqq", "--extension",
                      "https://h/x?access_token=zz9", "ghp_0123456789", "/Apps/Brave Browser.app"])
        self.assertEqual(out, ["--token", "<redacted:7 chars>", "--api-key=<redacted:3 chars>",
                               "Authorization: <redacted:10 chars>", "--extension",
                               "https://h/x?access_token=<redacted:3 chars>", "<redacted:14 chars>",
                               "/Apps/Brave Browser.app"])


class SkillDirTests(TmpHome):
    """A-5: --scope project nunca grava dentro da pasta da skill."""

    def test_project_na_pasta_da_skill_e_usage_error(self):
        for d in (cm.SKILL_DIR, os.path.join(cm.SKILL_DIR, "scripts")):
            code, out = self.run_cfg("--harness", "claude", "--scope", "project", "--mode", "extension",
                                     "--project-dir", d, "--apply")
            self.assertEqual((code, out["status"]), (2, "usage_error"), d)
            self.assertIn("raiz do projeto", out["problems"][0])
            self.assertIn("--project-dir", out["problems"][0])
        self.assertFalse(os.path.exists(os.path.join(cm.SKILL_DIR, ".mcp.json")))
        self.assertFalse(os.path.exists(os.path.join(cm.SKILL_DIR, "scripts", ".mcp.json")))

    def test_config_file_dentro_da_skill_e_usage_error(self):
        code, out = self.run_cfg("--harness", "cursor", "--scope", "user", "--mode", "extension",
                                 "--config-file", os.path.join(cm.SKILL_DIR, "mcp.json"))
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_escopo_user_com_cwd_na_skill_continua_permitido(self):
        code, out = self.run_cfg("--harness", "cursor", "--scope", "user", "--mode", "extension",
                                 "--project-dir", cm.SKILL_DIR)
        self.assertEqual((code, out["status"]), (0, "planned"))


class HarnessBlockTests(TmpHome):

    def plan(self, harness, scope="user", mode="extension", *extra):
        code, out = self.run_cfg("--harness", harness, "--scope", scope, "--mode", mode, *extra)
        self.assertEqual(code, 0, out)
        return out

    def test_vscode_usa_servers_e_input(self):
        out = self.plan("vscode", "project")
        self.assertTrue(out["data"]["file"].endswith(os.path.join(".vscode", "mcp.json")))
        self.assertEqual(out["data"]["server"]["env"][cm.TOKEN_ENV], "${input:%s}" % cm.VSCODE_INPUT_ID)
        self.assertIn('"servers"', out["data"]["diff"])
        self.assertIn('"password": true', out["data"]["diff"])

    def test_gemini_e_windsurf(self):
        g = self.plan("gemini")
        self.assertEqual(g["data"]["server"]["env"][cm.TOKEN_ENV], "${%s}" % cm.TOKEN_ENV)
        self.assertNotIn("type", g["data"]["server"])
        w = self.plan("windsurf")
        self.assertNotIn("env", w["data"]["server"])
        self.assertTrue(any("[não verificado]" in n for n in w["data"]["notes"]))

    def test_windsurf_projeto_e_erro_de_uso(self):
        code, out = self.run_cfg("--harness", "windsurf", "--scope", "project", "--mode", "extension")
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_codex_toml(self):
        out = self.plan("codex", "user", "extension", "--apply")
        path = os.path.join(self.home, ".codex", "config.toml")
        text = self.read(path)
        self.assertIn("[mcp_servers.playwright-browser]", text)
        self.assertIn('env_vars = ["%s"]' % cm.TOKEN_ENV, text)
        self.assertEqual(cm.toml_loads_mini(text)["mcp_servers"]["playwright-browser"], out["data"]["server"])
        out2 = self.plan("codex", "user", "extension", "--apply")
        self.assertEqual(out2["status"], "already_configured")

    def test_profile_pasta_dedicada_padrao(self):
        out = self.plan("claude", "user", "profile")
        args = out["data"]["server"]["args"]
        self.assertNotIn("--extension", args)
        self.assertEqual(args[args.index("--user-data-dir") + 1],
                         os.path.join(self.home, ".local", "share", "playwright-mcp-skill", "browser-profile"))
        self.assertNotIn("env", out["data"]["server"])

    def test_profile_recusa_pasta_real_do_navegador(self):
        real = os.path.join(self.home, "Library", "Application Support", "BraveSoftware", "Brave-Browser")
        if self.env.os_name == "linux":
            real = os.path.join(self.home, ".config", "BraveSoftware", "Brave-Browser")
        code, out = self.run_cfg("--harness", "claude", "--scope", "user", "--mode", "profile",
                                 "--user-data-dir", real)
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_cli_command_claude(self):
        out = self.plan("claude", "user")
        self.assertTrue(out["data"]["cli_command"].startswith("claude mcp add-json -s user playwright-browser '"))

    def test_versao_por_flag_e_por_variavel(self):
        out = self.plan("cursor", "user", "extension", "--version", "0.0.90")
        self.assertIn("@playwright/mcp@0.0.90", out["data"]["server"]["args"])
        self.env.environ[cm.VERSION_ENV] = "0.0.91"
        out = self.plan("cursor")
        self.assertIn("@playwright/mcp@0.0.91", out["data"]["server"]["args"])


class BuildServerTests(unittest.TestCase):
    """Montagem dos args por navegador e SO (sem disco)."""

    def entry(self, key, exe, needs):
        info = db.BROWSERS[key]
        return {"id": key, "name": info["name"], "executable": exe, "chromium": True,
                "playwright_channel": info.get("channel"), "needs_executable_path": needs, "packaging": "native"}

    def test_chrome_extensao_sem_executable_path(self):
        env = FakeEnv("macos", environ={"HOME": "/h"})
        srv, _ = cm.build_server("claude", "extension", self.entry("chrome", "/x", False), "0.0.85", env,
                                 "cmd", None, None)
        self.assertEqual(srv["args"], ["-y", "@playwright/mcp@0.0.85", "--extension"])

    def test_edge_extensao_usa_browser_msedge(self):
        env = FakeEnv("macos", environ={"HOME": "/h"})
        srv, _ = cm.build_server("cursor", "extension", self.entry("msedge", "/x", False), "0.0.85", env,
                                 "cmd", None, "Profile 2")
        self.assertEqual(srv["args"][2:], ["--extension", "--browser", "msedge", "--profile-dir-name", "Profile 2"])

    def test_windows_cmd_c_e_flag_npx(self):
        env = FakeEnv("windows", environ={"USERPROFILE": r"C:\Users\t"})
        e = self.entry("brave", r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", True)
        srv, _ = cm.build_server("claude", "extension", e, "0.0.85", env, "cmd", None, None)
        self.assertEqual(srv["command"], "cmd")
        self.assertEqual(srv["args"][:3], ["/c", "npx", "-y"])
        srv, _ = cm.build_server("claude", "extension", e, "0.0.85", env, "npx", None, None)
        self.assertEqual(srv["command"], "npx")

    def test_windows_plano_completo_com_fs_simulado(self):
        exe = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        env = FakeEnv("windows", environ={"USERPROFILE": r"C:\Users\t", "LOCALAPPDATA": r"C:\Users\t\AppData\Local"},
                      files={exe: b""})
        code, out, raw = run_main(cm.main, ["--harness", "codex", "--scope", "user", "--mode", "profile",
                                            "--browser", exe], env)
        self.assertEqual(out["status"], "planned")
        self.assertEqual(out["data"]["file"], r"C:\Users\t\.codex\config.toml")
        args = out["data"]["server"]["args"]
        self.assertEqual(out["data"]["server"]["command"], "cmd")
        self.assertEqual(args[args.index("--user-data-dir") + 1],
                         r"C:\Users\t\AppData\Local\playwright-mcp-skill\browser-profile")
        self.assertIn(r'"C:\\Program Files\\BraveSoftware', out["data"]["diff"])  # escape TOML correto


class TomlTests(unittest.TestCase):

    BASE = ('# config do usuário\nmodel = "o3"\n\n[mcp_servers.outro]\ncommand = "node"\n'
            'args = [\n  "a.js", # comentário\n  "b",\n]\n\n[mcp_servers.playwright-browser]\n'
            'command = "npx"\nargs = ["velho"]\n\n[mcp_servers.playwright-browser.env]\nX = "1"\n\n'
            '[profiles.dev]\nmodel = "o4"\n')

    def test_leitor_minimo(self):
        doc = cm.toml_loads_mini(self.BASE)
        self.assertEqual(doc["mcp_servers"]["outro"]["args"], ["a.js", "b"])
        self.assertEqual(doc["mcp_servers"]["playwright-browser"]["env"], {"X": "1"})
        self.assertEqual(doc["profiles"]["dev"]["model"], "o4")
        self.assertEqual(cm.toml_loads_mini("a = { b = 1, c = 'x' }\nd = true\n"),
                         {"a": {"b": 1, "c": "x"}, "d": True})

    def test_conflito_e_force_substitui_so_a_secao(self):
        srv = {"command": "npx", "args": ["novo"]}
        _, state, _ = cm.toml_merge(self.BASE, "playwright-browser", srv, False)
        self.assertEqual(state, "conflict")
        new, state, _ = cm.toml_merge(self.BASE, "playwright-browser", srv, True)
        self.assertEqual(state, "replace")
        doc = cm.toml_loads_mini(new)
        self.assertEqual(doc["mcp_servers"]["playwright-browser"], srv)  # subtabela .env removida
        self.assertEqual(doc["mcp_servers"]["outro"]["args"], ["a.js", "b"])
        self.assertIn("# config do usuário", new)
        self.assertIn("[profiles.dev]", new)

    def test_adiciona_no_fim(self):
        new, state, _ = cm.toml_merge('model = "o3"\n', "x", {"command": "npx"}, False)
        self.assertEqual(state, "add")
        self.assertEqual(new, 'model = "o3"\n\n[mcp_servers.x]\ncommand = "npx"\n')


if __name__ == "__main__":
    unittest.main()
