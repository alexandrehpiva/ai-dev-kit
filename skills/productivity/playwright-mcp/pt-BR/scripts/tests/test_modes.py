# -*- coding: utf-8 -*-
"""Testes dos recursos da skill playwright-mcp: perfis (detect_browser), modos headless
(configure_mcp), checagens por modo (check_setup). Perfis e estados 100% sintéticos."""

import json
import os
import shutil
import stat
import tempfile
import time
import unittest

from helpers import FakeEnv, make_profile_tree, read_json, run_main
import check_setup as cs
import clone_profile as cp
import configure_mcp as cm
import detect_browser as db

STATE_SECRET = "COOKIE-DO-STATE-NAO-PODE-APARECER"  # gitleaks:allow (valor falso de teste)


# ---------------------------------------------------------------------------
# detect_browser: perfis e seleção
# ---------------------------------------------------------------------------

UDD = "/Users/teste/Library/Application Support/BraveSoftware/Brave-Browser"


def local_state(profiles, last_used=None, last_active=None):
    return json.dumps({"profile": {"info_cache": {p: {"name": "NOME-FALSO", "user_name": "x@exemplo.test"}
                                                  for p in profiles},
                                   "last_used": last_used, "last_active_profiles": last_active or []}})


class ProfileListingTests(unittest.TestCase):

    def test_lista_sem_nomes_nem_emails_e_acha_cookies_nos_dois_layouts(self):
        env = FakeEnv("macos", environ={"HOME": "/Users/teste"}, files={
            UDD + "/Local State": local_state(["Default", "Profile 3"], "Profile 3", ["Profile 3"]),
            UDD + "/Default/Cookies": b"", UDD + "/Profile 3/Network/Cookies": b""})
        info = db.list_profiles(UDD, env)
        self.assertEqual([p["dir"] for p in info["profiles"]], ["Default", "Profile 3"])
        self.assertEqual(info["suggested"], "Profile 3")
        by = {p["dir"]: p for p in info["profiles"]}
        self.assertEqual(by["Default"]["cookies"], ["Default/Cookies"])
        self.assertEqual(by["Profile 3"]["cookies"], ["Profile 3/Network/Cookies"])
        self.assertTrue(by["Profile 3"]["last_active"])
        dumped = json.dumps(info)
        self.assertNotIn("NOME-FALSO", dumped)
        self.assertNotIn("exemplo.test", dumped)

    def test_sem_last_used_sugere_default_e_local_state_invalido_nao_quebra(self):
        env = FakeEnv("macos", environ={"HOME": "/Users/teste"}, files={
            UDD + "/Local State": "{quebrado", UDD + "/Default/Cookies": b""})
        info = db.list_profiles(UDD, env)
        self.assertEqual(info["suggested"], "Default")

    def test_pasta_inexistente(self):
        env = FakeEnv("macos", environ={"HOME": "/Users/teste"})
        self.assertFalse(db.list_profiles(UDD, env)["exists"])

    def test_flag_list_profiles_no_detect(self):
        from test_detect_browser import mac_env, LS_PLIST
        from helpers import fixture
        env = mac_env({LS_PLIST: fixture("macos_launchservices_brave.plist"),
                       UDD.replace("/Users/teste", "/Users/teste") + "/Local State": local_state(["Default"]),
                       UDD + "/Default/Cookies": b""})
        code, out, _ = run_main(db.main, ["--list-profiles"], env)
        self.assertEqual(code, 0)
        self.assertEqual(out["data"]["profiles"]["profiles"][0]["dir"], "Default")
        code, out, _ = run_main(db.main, [], env)
        self.assertNotIn("profiles", out["data"])


class PickBrowserTests(unittest.TestCase):

    def test_id_instalado_alias_e_ausente(self):
        from test_detect_browser import mac_env, LS_PLIST, CHROME_EXE
        from helpers import fixture
        env = mac_env({LS_PLIST: fixture("macos_launchservices_brave.plist"), CHROME_EXE: b""})
        e, _ = db.pick_browser("chrome", env)
        self.assertEqual(e["id"], "chrome")
        e, _ = db.pick_browser("brave", env)
        self.assertEqual(e["id"], "brave")
        e, probs = db.pick_browser("edge", env)
        self.assertIsNone(e)
        self.assertTrue(probs)
        e, _ = db.pick_browser("auto", env)
        self.assertEqual(e["id"], "brave")

    def test_caminho_inexistente(self):
        env = FakeEnv("linux", environ={"HOME": "/home/t"})
        e, probs = db.pick_browser("/nao/existe/brave", env)
        self.assertIsNone(e)
        self.assertTrue(any("--browser" in p for p in probs))


# ---------------------------------------------------------------------------
# configure_mcp: modos headless
# ---------------------------------------------------------------------------

class ModeBase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwmcp-w3-modes-")
        self.home = os.path.join(self.tmp, "home")
        self.proj = os.path.join(self.tmp, "proj")
        os.makedirs(self.home)
        os.makedirs(self.proj)
        exe_dir = os.path.join(self.tmp, "Apps", "Brave Browser.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        self.brave = os.path.join(exe_dir, "Brave Browser")
        open(self.brave, "w").close()
        self.environ = {"HOME": self.home, "USERPROFILE": self.home, "PATH": os.environ.get("PATH", "")}
        self.host = db.host_os() if db.host_os() != "windows" else "linux"
        self.env = db.SystemEnv(os_name=self.host, environ=self.environ)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def clone(self, dest=None):
        src = make_profile_tree(os.path.join(self.tmp, "src"))
        dest = dest or os.path.join(self.tmp, "copia")
        code, out, _ = run_main(cp.main, ["--browser", self.brave, "--source-dir", src, "--dest", dest,
                                          "--level", "minimal"], self.env)
        self.assertEqual(code, 0, out["problems"])
        return dest

    def state_file(self, mode=0o600, doc=None, name="state.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc if doc is not None else {"cookies": [{"name": "a", "value": STATE_SECRET}],
                                                   "origins": [{"origin": "https://x.test", "localStorage": []}]}, fh)
        os.chmod(path, mode)
        return path

    def cfg(self, *extra):
        argv = ["--browser", self.brave, "--project-dir", self.proj] + list(extra)
        code, out, raw = run_main(cm.main, argv, self.env)
        self.assertNotIn(STATE_SECRET, raw)
        return code, out


class HeadlessProfileConfigTests(ModeBase):

    def test_plano_com_copia_gera_headless_user_data_dir_e_config(self):
        copy = self.clone()
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile",
                             "--copy-dir", copy)
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        args = out["data"]["server"]["args"]
        self.assertEqual(args[:2], ["-y", "@playwright/mcp@0.0.85"])
        self.assertIn("--headless", args)
        self.assertEqual(args[args.index("--executable-path") + 1], self.brave)
        self.assertEqual(args[args.index("--user-data-dir") + 1], copy)
        self.assertEqual(args[args.index("--config") + 1], os.path.join(copy, "pwmcp-config.json"))
        for absent in ("--extension", "--isolated", "--storage-state"):
            self.assertNotIn(absent, args)
        self.assertNotIn("env", out["data"]["server"])  # sem token neste modo
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude.json")))  # plano não grava

    def test_nome_padrao_do_servidor_por_modo(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["data"]["server_name"], "playwright-headless")
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy,
                          "--server-name", "outro")
        self.assertEqual(out["data"]["server_name"], "outro")

    def test_apply_grava_e_e_idempotente(self):
        copy = self.clone()
        argv = ("--harness", "cursor", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy)
        code, out = self.cfg(*argv, "--apply")
        self.assertEqual((code, out["status"]), (0, "applied"))
        doc = read_json(os.path.join(self.home, ".cursor", "mcp.json"))
        self.assertIn("--user-data-dir", doc["mcpServers"]["playwright-headless"]["args"])
        code, out = self.cfg(*argv, "--apply")
        self.assertEqual(out["status"], "already_configured")

    def test_flags_extras_user_agent_e_no_sandbox(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy,
                          "--user-agent", "Mozilla/5.0 (X11; Linux) Chrome/157.0.0.0", "--no-sandbox")
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--user-agent") + 1], "Mozilla/5.0 (X11; Linux) Chrome/157.0.0.0")
        self.assertIn("--no-sandbox", args)

    def test_copia_inexistente_ou_sem_config(self):
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile",
                             "--copy-dir", os.path.join(self.tmp, "nao-existe"))
        self.assertEqual((code, out["status"]), (1, "copy_missing"))
        vazio = os.path.join(self.tmp, "vazio")
        os.makedirs(vazio)
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", vazio)
        self.assertEqual((code, out["status"]), (1, "copy_missing"))

    def test_pasta_sem_marcador_avisa(self):
        copy = self.clone()
        os.unlink(os.path.join(copy, cp.MARKER))
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy)
        self.assertTrue(any("marcador" in p for p in out["problems"]))

    def test_exige_copy_dir_e_recusa_flags_de_outro_modo(self):
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile")
        self.assertEqual((code, out["status"]), (2, "usage_error"))
        for extra in (("--mode", "extension", "--copy-dir", "x"), ("--mode", "profile", "--state-file", "x"),
                      ("--mode", "headless-state", "--state-file", "x", "--copy-dir", "y"),
                      ("--mode", "headless-profile", "--copy-dir", "x", "--user-data-dir", "y"),
                      ("--mode", "headless-profile", "--copy-dir", "x", "--profile-dir-name", "Profile 1")):
            code, out = self.cfg("--harness", "claude", "--scope", "user", *extra)
            self.assertEqual((code, out["status"]), (2, "usage_error"), extra)

    def test_recusa_a_pasta_real_do_navegador_como_copia(self):
        real = os.path.join(self.home, "Library", "Application Support", "BraveSoftware", "Brave-Browser")
        if self.host == "linux":
            real = os.path.join(self.home, ".config", "BraveSoftware", "Brave-Browser")
        os.makedirs(real)
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", real)
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_scope_project_avisa_caminho_absoluto(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "claude", "--scope", "project", "--mode", "headless-profile", "--copy-dir", copy)
        self.assertTrue(any("versionável" in p for p in out["problems"]))

    def test_vscode_user_tem_cli_command(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "vscode", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy)
        self.assertTrue(out["data"]["cli_command"].startswith("code --add-mcp "))


class HeadlessStateConfigTests(ModeBase):

    def test_plano_gera_isolated_storage_state(self):
        sf = self.state_file()
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state", "--state-file", sf)
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        args = out["data"]["server"]["args"]
        self.assertIn("--headless", args)
        self.assertIn("--isolated", args)
        self.assertEqual(args[args.index("--storage-state") + 1], sf)
        self.assertNotIn("--user-data-dir", args)
        self.assertNotIn("--config", args)
        self.assertNotIn("--init-script", args)

    def test_com_init_script(self):
        sf = self.state_file()
        js = os.path.join(self.tmp, "init.js")
        open(js, "w").close()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state", "--state-file", sf,
                          "--init-script", js)
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--init-script") + 1], js)

    def test_state_ausente_e_permissao_aberta(self):
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state",
                             "--state-file", os.path.join(self.tmp, "nao.json"))
        self.assertEqual((code, out["status"]), (1, "copy_missing"))
        if os.name == "posix":
            sf = self.state_file(mode=0o644)
            _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state", "--state-file", sf)
            self.assertTrue(any("chmod 600" in p for p in out["problems"]))

    def test_init_script_inexistente_avisa(self):
        sf = self.state_file()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state", "--state-file", sf,
                          "--init-script", os.path.join(self.tmp, "nada.js"))
        self.assertTrue(any("--init-script" in p for p in out["problems"]))


class WindowsLauncherTests(ModeBase):

    def test_windows_usa_cmd_c_npx_nos_modos_headless(self):
        copy = self.clone()
        env = db.SystemEnv(os_name="windows", environ=dict(self.environ, LOCALAPPDATA=os.path.join(self.home, "L")))
        argv = ["--browser", self.brave, "--project-dir", self.proj, "--harness", "claude", "--scope", "user",
                "--mode", "headless-profile", "--copy-dir", copy, "--config-file", os.path.join(self.tmp, "c.json")]
        code, out, _ = run_main(cm.main, argv, env)
        self.assertEqual(out["data"]["server"]["command"], "cmd")
        self.assertEqual(out["data"]["server"]["args"][:3], ["/c", "npx", "-y"])


class MarcadorEOutputDirTests(ModeBase):
    """Decisão 2: o navegador da cópia manda. Decisão 10: --output-dir fora do projeto."""

    def setUp(self):
        super(MarcadorEOutputDirTests, self).setUp()
        exe_dir = os.path.join(self.tmp, "Apps", "Google Chrome.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        self.chrome = os.path.join(exe_dir, "Google Chrome")
        open(self.chrome, "w").close()

    def copia_de(self, navegador, exe):
        copy = self.clone()
        marker_path = os.path.join(copy, cm.CLONE_MARKER)
        doc = read_json(marker_path)
        doc.update({"browser": navegador, "executable": exe})
        with open(marker_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return copy

    def cfg_sem_browser(self, *extra):
        argv = ["--project-dir", self.proj] + list(extra)
        code, out, raw = run_main(cm.main, argv, self.env)
        return code, out

    def test_sem_browser_usa_o_executavel_do_marcador_mesmo_que_o_padrao_seja_outro(self):
        copy = self.copia_de("chrome", self.chrome)
        code, out = self.cfg_sem_browser("--harness", "claude", "--scope", "user", "--mode", "headless-profile",
                                         "--copy-dir", copy)
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--executable-path") + 1], self.chrome)

    def test_browser_diferente_do_marcador_e_recusado_e_nao_registra(self):
        copy = self.copia_de("chrome", self.chrome)
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile",
                             "--copy-dir", copy, "--apply")  # self.brave != chrome
        self.assertEqual((code, out["status"]), (1, "browser_issue"))
        self.assertTrue(any("por navegador" in p for p in out["problems"]))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude.json")))

    def test_browser_igual_ao_marcador_passa(self):
        copy = self.copia_de("brave", self.brave)
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile",
                             "--copy-dir", copy)
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])

    def test_output_dir_padrao_ao_lado_da_copia_e_override(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy)
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--output-dir") + 1], copy + "-output")
        outro = os.path.join(self.tmp, "saida")
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy,
                          "--output-dir", outro)
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--output-dir") + 1], outro)

    def test_output_dir_dentro_do_projeto_avisa_e_headless_state_tambem_tem(self):
        copy = self.clone()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-profile", "--copy-dir", copy,
                          "--output-dir", os.path.join(self.proj, "saida"))
        self.assertTrue(any(".gitignore" in p for p in out["problems"]))
        sf = self.state_file()
        _, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "headless-state", "--state-file", sf)
        args = out["data"]["server"]["args"]
        self.assertEqual(args[args.index("--output-dir") + 1], os.path.splitext(sf)[0] + "-output")

    def test_output_dir_so_vale_nos_modos_headless(self):
        code, out = self.cfg("--harness", "claude", "--scope", "user", "--mode", "extension", "--output-dir", "x")
        self.assertEqual((code, out["status"]), (2, "usage_error"))


class EscopoLocalTests(ModeBase):

    def test_so_claude_aceita_local(self):
        code, out = self.cfg("--harness", "cursor", "--scope", "local", "--mode", "extension")
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_plano_local_nao_grava_e_traz_cli_command(self):
        code, out = self.cfg("--harness", "claude", "--scope", "local", "--mode", "profile")
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        self.assertIn("-s local", out["data"]["cli_command"])
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude.json")))

    def apply_env(self, with_claude=True, ok=True):
        home, proj = self.home, self.proj
        tmp_exe = self.brave

        class Env(FakeEnv):
            def run(self, cmd, timeout=5, cwd=None):
                self.calls.append((list(cmd), cwd))
                if cmd[1:5] == ["mcp", "add-json", "-s", "local"] and ok:
                    path = home + "/.claude.json"
                    doc = json.loads(self.files[path].decode()) if path in self.files else {}
                    doc.setdefault("projects", {}).setdefault(cwd, {}).setdefault("mcpServers", {})[cmd[5]] = \
                        dict(json.loads(cmd[6]), env={})  # o Claude Code grava env vazio
                    self.files[path] = json.dumps(doc).encode()
                return 0, ""

        env = Env("linux", environ={"HOME": home}, which={"claude": "/bin/claude"} if with_claude else {},
                  files={tmp_exe: b""})
        return env

    def run_local(self, env, *extra):
        argv = ["--browser", self.brave, "--project-dir", self.proj, "--harness", "claude", "--scope", "local",
                "--mode", "profile"] + list(extra)
        return run_main(cm.main, argv, env)[:2]

    def test_apply_chama_o_cli_na_pasta_do_projeto_e_e_idempotente(self):
        env = self.apply_env()
        code, out = self.run_local(env, "--apply")
        self.assertEqual((code, out["status"]), (0, "applied"), out["problems"])
        cmd, cwd = env.calls[-1]
        self.assertEqual(cmd[:6], ["/bin/claude", "mcp", "add-json", "-s", "local", "playwright-headless"])
        self.assertEqual(cwd, os.path.abspath(self.proj))
        code, out = self.run_local(env, "--apply")
        self.assertEqual((code, out["status"]), (0, "already_configured"))

    def test_sem_claude_no_path(self):
        code, out = self.run_local(self.apply_env(with_claude=False), "--apply")
        self.assertEqual((code, out["status"]), (1, "cli_missing"))

    def test_cli_que_nao_registra_vira_apply_failed(self):
        code, out = self.run_local(self.apply_env(ok=False), "--apply")
        self.assertEqual((code, out["status"]), (1, "apply_failed"))


class WindowsNodeLauncherTests(ModeBase):

    EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    def win(self, run=None):
        return FakeEnv("windows", environ={"USERPROFILE": r"C:\Users\t", "LOCALAPPDATA": r"C:\Users\t\AppData\Local"},
                       files={self.EXE: b""}, run=run)

    def argv(self, *extra):
        return ["--harness", "claude", "--scope", "user", "--mode", "profile", "--browser", self.EXE,
                "--windows-launcher", "node"] + list(extra)

    def test_node_resolve_npm_root_g(self):
        env = self.win(run={("npm.cmd", "root", "-g"): (0, "C:\\Users\\t\\AppData\\Roaming\\npm\\node_modules\n")})
        code, out, _ = run_main(cm.main, self.argv(), env)
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        srv = out["data"]["server"]
        self.assertEqual(srv["command"], "node")
        self.assertTrue(srv["args"][0].endswith(r"@playwright\mcp\cli.js"))
        self.assertNotIn("npx", srv["args"])

    def test_node_cli_explicito_e_erro_quando_nao_acha(self):
        code, out, _ = run_main(cm.main, self.argv("--node-cli", r"D:\x\cli.js"), self.win())
        self.assertEqual(out["data"]["server"]["args"][0], r"D:\x\cli.js")
        code, out, _ = run_main(cm.main, self.argv(), self.win())
        self.assertEqual((code, out["status"]), (2, "usage_error"))

    def test_padrao_continua_cmd_c_npx_e_avisa_do_powershell(self):
        code, out, _ = run_main(cm.main, ["--harness", "claude", "--scope", "user", "--mode", "profile",
                                          "--browser", self.EXE], self.win())
        self.assertEqual(out["data"]["server"]["command"], "cmd")
        self.assertTrue(any("PowerShell 5.1" in n for n in out["data"]["notes"]))


# ---------------------------------------------------------------------------
# check_setup por modo
# ---------------------------------------------------------------------------

class HybridEnv(db.SystemEnv):
    """Disco real (pastas temporárias), mas Node falso e nenhum comando externo executado."""

    def which(self, name):
        return {"node": "/usr/local/bin/node", "npx": "/usr/local/bin/npx"}.get(name)

    def run(self, cmd, timeout=5):
        if list(cmd) == ["/usr/local/bin/node", "-v"]:
            return 0, "v22.11.0\n"
        return None, ""


class CheckModeBase(ModeBase):

    def setUp(self):
        super(CheckModeBase, self).setUp()
        # override de navegador aponta para o executável falso (Chromium válido para o detect)
        self.fenv = HybridEnv(os_name=self.host, environ=dict(self.environ, **{db.OVERRIDE_ENV: self.brave}))

    def check(self, *extra):
        code, out, raw = run_main(cs.main, ["--project-dir", self.proj] + list(extra), self.fenv)
        self.assertNotIn(STATE_SECRET, raw)
        return code, out


class CheckCopyTests(CheckModeBase):

    def test_copia_boa_sem_servidor_registrado_nao_e_ready_mas_copia_ok(self):
        copy = self.clone()
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["status"], "mcp_not_registered")
        self.assertTrue(out["data"]["copy"]["marker"])
        self.assertEqual(out["data"]["copy"]["locks"], [])
        self.assertTrue(out["data"]["copy"]["config"]["ok"])

    def test_copia_inexistente(self):
        code, out = self.check("--mode", "headless-profile", "--copy-dir", os.path.join(self.tmp, "nada"))
        self.assertEqual((code, out["status"]), (1, "copy_issue"))

    def test_travas_na_copia(self):
        copy = self.clone()
        open(os.path.join(copy, "SingletonLock"), "w").close()
        open(os.path.join(copy, "Default", "lockfile"), "w").close()
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["status"], "copy_issue")
        self.assertEqual(len(out["data"]["copy"]["locks"]), 2)

    def test_config_sem_ignore_default_args_do_so(self):
        copy = self.clone()
        cfg_path = os.path.join(copy, cp.CONFIG_NAME)
        cfg = read_json(cfg_path)
        cfg["browser"]["launchOptions"].pop("ignoreDefaultArgs", None)
        with open(cfg_path, "w") as fh:
            json.dump(cfg, fh)
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        if self.host in ("macos", "linux"):
            self.assertEqual(out["status"], "copy_issue")
            self.assertTrue(any("ignoreDefaultArgs" in p for p in out["problems"]))

    def test_perfil_nao_default_sem_profile_directory(self):
        src = make_profile_tree(os.path.join(self.tmp, "src2"), profiles=("Profile 4",), last_active=("Profile 4",))
        copy = os.path.join(self.tmp, "copia4")
        code, out, _ = run_main(cp.main, ["--browser", self.brave, "--source-dir", src, "--dest", copy,
                                          "--level", "minimal"], self.env)
        self.assertEqual(code, 0)
        cfg_path = os.path.join(copy, cp.CONFIG_NAME)
        cfg = read_json(cfg_path)
        cfg["browser"]["launchOptions"].pop("args")
        with open(cfg_path, "w") as fh:
            json.dump(cfg, fh)
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["status"], "copy_issue")
        self.assertTrue(any("--profile-directory" in p for p in out["problems"]))

    def test_copia_velha(self):
        copy = self.clone()
        old = time.time() - 40 * 3600
        marker = os.path.join(copy, cp.MARKER)
        doc = read_json(marker)
        doc["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(old))
        with open(marker, "w") as fh:
            json.dump(doc, fh)
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["status"], "copy_issue")
        self.assertTrue(any("Refaça" in p for p in out["problems"]))
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy, "--max-age-hours", "100")
        self.assertEqual(out["status"], "mcp_not_registered")

    def test_pasta_sem_marcador(self):
        copy = self.clone()
        os.unlink(os.path.join(copy, cp.MARKER))
        code, out = self.check("--mode", "headless-profile", "--copy-dir", copy)
        self.assertEqual(out["status"], "copy_issue")

    def test_ready_com_servidor_registrado_e_copia_boa(self):
        copy = self.clone()
        c, o = self.cfg("--harness", "claude", "--scope", "project", "--mode", "headless-profile", "--copy-dir", copy,
                        "--apply")
        self.assertEqual(c, 0, o)
        code, out = self.check("--harness", "claude")
        self.assertEqual((code, out["status"]), (0, "ready"), out["problems"])
        self.assertEqual(out["data"]["mode"], "headless-profile")
        self.assertEqual(out["data"]["selected"]["mode"], "headless-profile")
        self.assertFalse(out["data"]["token"]["required"])


class CheckExecutavelDoMarcadorTests(CheckModeBase):

    def test_servidor_registrado_com_outro_navegador_que_o_da_copia_e_copy_issue(self):
        copy = self.clone()
        marker_path = os.path.join(copy, cm.CLONE_MARKER)
        doc = read_json(marker_path)
        doc.update({"browser": "brave", "executable": self.brave})
        with open(marker_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        c, o = self.cfg("--harness", "claude", "--scope", "project", "--mode", "headless-profile", "--copy-dir", copy,
                        "--apply")
        self.assertEqual(c, 0, o)
        code, out = self.check("--harness", "claude")
        self.assertEqual(out["status"], "ready", out["problems"])
        # agora o marcador passa a dizer que a cópia é de Chrome: o registro (Brave) diverge
        doc.update({"browser": "chrome", "executable": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"})
        with open(marker_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        code, out = self.check("--harness", "claude")
        self.assertEqual((code, out["status"]), (1, "copy_issue"))
        self.assertTrue(any("por navegador" in p for p in out["problems"]))

    def test_registro_sem_executable_path_e_copy_issue_e_sem_output_dir_avisa(self):
        copy = self.clone()
        with open(os.path.join(self.proj, ".mcp.json"), "w", encoding="utf-8") as fh:
            json.dump({"mcpServers": {"playwright-headless": {"command": "npx", "args": [
                "-y", "@playwright/mcp@0.0.85", "--headless", "--user-data-dir", copy, "--config",
                os.path.join(copy, "pwmcp-config.json")]}}}, fh)
        code, out = self.check("--harness", "claude")
        self.assertEqual((code, out["status"]), (1, "copy_issue"))
        text = " ".join(out["problems"])
        self.assertIn("--executable-path", text)
        self.assertIn("--output-dir", text)


class CheckStateTests(CheckModeBase):

    def test_state_bom(self):
        sf = self.state_file()
        code, out = self.check("--mode", "headless-state", "--state-file", sf)
        self.assertEqual(out["status"], "mcp_not_registered")
        st = out["data"]["state"]
        self.assertEqual((st["cookies"], st["origins"]), (1, 1))

    @unittest.skipIf(os.name != "posix", "permissões POSIX")
    def test_permissao_aberta(self):
        sf = self.state_file(mode=0o644)
        code, out = self.check("--mode", "headless-state", "--state-file", sf)
        self.assertEqual((code, out["status"]), (1, "state_issue"))
        self.assertEqual(out["data"]["state"]["mode"], "0o644")

    def test_ausente_vazio_e_invalido(self):
        self.assertEqual(self.check("--mode", "headless-state", "--state-file", os.path.join(self.tmp, "n.json"))[1]["status"],
                         "state_issue")
        sf = self.state_file(doc={"cookies": [], "origins": []})
        self.assertEqual(self.check("--mode", "headless-state", "--state-file", sf)[1]["status"], "state_issue")
        bad = os.path.join(self.tmp, "ruim.json")
        with open(bad, "w") as fh:
            fh.write("{nao json")
        os.chmod(bad, 0o600)
        self.assertEqual(self.check("--mode", "headless-state", "--state-file", bad)[1]["status"], "state_issue")

    def test_state_velho(self):
        sf = self.state_file()
        old = time.time() - 30 * 3600
        os.utime(sf, (old, old))
        code, out = self.check("--mode", "headless-state", "--state-file", sf)
        self.assertEqual(out["status"], "state_issue")

    def test_ready_com_servidor_headless_state(self):
        sf = self.state_file()
        c, o = self.cfg("--harness", "claude", "--scope", "project", "--mode", "headless-state", "--state-file", sf,
                        "--apply")
        self.assertEqual(c, 0, o)
        code, out = self.check("--harness", "claude")
        self.assertEqual((code, out["status"]), (0, "ready"), out["problems"])
        self.assertTrue(out["data"]["selected"]["isolated"])


# ---------------------------------------------------------------------------
# templates e textos
# ---------------------------------------------------------------------------

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "templates")
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def forbidden_terms():
    """Termos que não podem aparecer em scripts/templates. Termos pessoais ou de cliente NUNCA ficam no
    repositório: informe-os em PWMCP_TEST_FORBIDDEN_TERMS (separados por vírgula) ao rodar a suíte."""
    generic = ["gforms", "google-forms", "meu-usuario-sintetico", "empresa-exemplo-sintetica"]
    extra = [t.strip().lower() for t in os.environ.get("PWMCP_TEST_FORBIDDEN_TERMS", "").split(",") if t.strip()]
    return generic + extra


class TemplateTests(unittest.TestCase):

    def test_configs_json_batem_com_build_config(self):
        for os_name in ("macos", "linux", "windows"):
            doc = read_json(os.path.join(TEMPLATES, "config-headless-%s.json" % os_name))
            self.assertEqual(doc, cp.build_config(os_name, "Default"), os_name)

    def test_wrappers_nao_guardam_token_e_tem_cabecalho(self):
        for name in ("token-wrapper-macos.sh", "token-wrapper-linux.sh", "token-wrapper-windows.ps1"):
            with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotRegex(text, r"PLAYWRIGHT_MCP_EXTENSION_TOKEN\s*=\s*[\"']?[A-Za-z0-9_\-]{20,}", name)
            self.assertIn("@playwright/mcp@0.0.85", text)
            self.assertIn("playwright-mcp-extension-token", text)
        self.assertTrue(os.access(os.path.join(TEMPLATES, "token-wrapper-macos.sh"), os.X_OK))
        for name in ("token-wrapper-linux.sh", "token-wrapper-windows.ps1"):
            with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
                self.assertIn("[não verificado]", fh.read())

    def test_caminho_do_brave_no_windows_e_um_so_entre_wrapper_e_scripts(self):
        with open(os.path.join(TEMPLATES, "token-wrapper-windows.ps1"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('$Browser = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"', text)
        self.assertIn("cmd /c npx", text)

    def test_export_md_traz_o_codigo_exato(self):
        with open(os.path.join(TEMPLATES, "export-storage-state.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("storageState({ path: 'state.json', indexedDB: true })", text)
        self.assertIn("evitar", text.lower())
        self.assertIn("browser_run_code_unsafe", text)
        self.assertIn("Object.fromEntries(Object.entries(sessionStorage))", text)
        self.assertIn("--isolated", text)

    def test_nenhum_script_ou_template_cita_google_forms_ou_dados_pessoais(self):
        for base in (SCRIPTS, TEMPLATES):
            for root, _d, files in os.walk(base):
                if "__pycache__" in root:
                    continue
                for name in files:
                    path = os.path.join(root, name)
                    if os.path.abspath(path) == os.path.abspath(__file__) or name.endswith((".plist", ".pyc")):
                        continue
                    try:
                        with open(path, encoding="utf-8") as fh:
                            text = fh.read().lower()
                    except UnicodeDecodeError:
                        continue
                    for bad in forbidden_terms():
                        self.assertNotIn(bad, text, "%s cita um termo proibido (%s)" % (name, bad))


if __name__ == "__main__":
    unittest.main()
