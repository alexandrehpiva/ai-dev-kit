# -*- coding: utf-8 -*-
"""Testes do detect_browser.py (sem rede; SO simulado)."""

import plistlib
import unittest

from helpers import FakeEnv, fixture, run_main
import detect_browser as db

HOME = "/Users/teste"
LS_PLIST = HOME + "/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
BRAVE_APP = "/Applications/Brave Browser.app"
BRAVE_EXE = BRAVE_APP + "/Contents/MacOS/Brave Browser"
CHROME_EXE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def ls_plist(entries, binary=False):
    fmt = plistlib.FMT_BINARY if binary else plistlib.FMT_XML
    return plistlib.dumps({"LSHandlers": entries}, fmt=fmt)


def mac_env(files=None, run=None, environ=None):
    base = {BRAVE_APP + "/Contents/Info.plist": fixture("macos_brave_info.plist"), BRAVE_EXE: b""}
    base.update(files or {})
    env = {"HOME": HOME}
    env.update(environ or {})
    return FakeEnv("macos", environ=env, files=base, run=run)


class MacOSTests(unittest.TestCase):

    def test_bundle_id_minusculo_do_plist_mapeia_para_brave(self):
        """Dado o plist com com.brave.browser (minúsculo), quando detecta, então o padrão é o Brave."""
        env = mac_env({LS_PLIST: fixture("macos_launchservices_brave.plist")})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "chromium_default")
        d = out["data"]["default"]
        self.assertEqual(d["id"], "brave")
        self.assertEqual(d["raw_id"], "com.brave.browser")
        self.assertEqual(d["executable"], BRAVE_EXE)
        self.assertTrue(d["needs_executable_path"])
        self.assertIsNone(d["playwright_channel"])
        self.assertEqual(d["user_data_dir"], HOME + "/Library/Application Support/BraveSoftware/Brave-Browser")
        self.assertEqual(out["data"]["source"], "launchservices_plist")
        self.assertEqual(set(out.keys()), {"ok", "status", "data", "problems", "next_steps"})

    def test_plist_binario_e_entrada_traco_ignorada(self):
        """Dado plist binário com uma entrada https '-' antes da real, então usa a real."""
        plist = ls_plist([{"LSHandlerURLScheme": "https", "LSHandlerRoleAll": "-"},
                          {"LSHandlerURLScheme": "https", "LSHandlerRoleAll": "COM.BRAVE.BROWSER"}], binary=True)
        code, out, _ = run_main(db.main, [], mac_env({LS_PLIST: plist}))
        self.assertEqual(out["data"]["default"]["id"], "brave")

    def test_safari_padrao_recomenda_chrome_instalado(self):
        """Dado Safari como padrão e Chrome no caminho do Playwright, então recomenda Chrome sem executable-path."""
        files = {LS_PLIST: ls_plist([{"LSHandlerURLScheme": "https", "LSHandlerRoleAll": "com.apple.safari"}]),
                 CHROME_EXE: b""}
        code, out, _ = run_main(db.main, [], mac_env(files))
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "non_chromium_default")
        self.assertFalse(out["data"]["default"]["chromium"])
        rec = out["data"]["recommended"]
        self.assertEqual(rec["id"], "chrome")  # Chrome preferido ao Brave
        self.assertFalse(rec["needs_executable_path"])
        self.assertEqual(rec["playwright_channel"], "chrome")

    def test_sem_handler_usa_nsworkspace(self):
        """Dado plist sem http/https, quando o osascript responde, então a fonte é nsworkspace."""
        run = {("osascript", "-l", "JavaScript", "-e", db.MAC_JXA): (0, BRAVE_APP + "\n")}
        code, out, _ = run_main(db.main, [], mac_env({LS_PLIST: ls_plist([])}, run=run))
        self.assertEqual(out["data"]["source"], "nsworkspace")
        self.assertEqual(out["data"]["default"]["id"], "brave")

    def test_sem_handler_e_sem_chromium_vira_no_chromium(self):
        """Dado nada registrado e nenhum Chromium instalado, então no_chromium com exit 1."""
        env = FakeEnv("macos", environ={"HOME": HOME}, files={})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "no_chromium")
        self.assertFalse(out["ok"])
        self.assertTrue(any("Safari" in p for p in out["problems"]))

    def test_pasta_de_perfil_orfa_nao_conta_como_instalado(self):
        """Dada só a pasta de dados do Vivaldi (sem o app), então o Vivaldi não aparece em installed."""
        env = mac_env({LS_PLIST: fixture("macos_launchservices_brave.plist")})
        env.dirs.add(HOME + "/Library/Application Support/Vivaldi")
        _, out, _ = run_main(db.main, [], env)
        self.assertNotIn("vivaldi", [e["id"] for e in out["data"]["installed"]])

    def test_override_inexistente_falha_com_mensagem(self):
        env = mac_env({LS_PLIST: fixture("macos_launchservices_brave.plist")},
                      environ={db.OVERRIDE_ENV: "/nao/existe/brave"})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "invalid_override")
        self.assertIn("/nao/existe/brave", out["problems"][0])

    def test_override_para_app_resolve_executavel(self):
        env = mac_env({LS_PLIST: ls_plist([])}, environ={db.OVERRIDE_ENV: BRAVE_APP})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 0)
        self.assertEqual(out["data"]["default"]["executable"], BRAVE_EXE)
        self.assertEqual(out["data"]["source"], "env:" + db.OVERRIDE_ENV)


WIN_ENV = {"USERPROFILE": r"C:\Users\teste", "LOCALAPPDATA": r"C:\Users\teste\AppData\Local",
           "ProgramFiles": r"C:\Program Files", "ProgramFiles(x86)": r"C:\Program Files (x86)"}
UC = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
UCL = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoiceLatest"
WIN_BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
WIN_EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class WindowsTests(unittest.TestCase):

    def test_winreg_mockado_brave(self):
        """Dado UserChoice=BraveHTML (winreg simulado), então Brave com executable-path e perfil em LOCALAPPDATA."""
        reg = {("HKCU", UC, "ProgId"): "BraveHTML",
               ("HKCR", r"BraveHTML\shell\open\command", ""): '"%s" --single-argument %%1' % WIN_BRAVE}
        env = FakeEnv("windows", environ=WIN_ENV, files={WIN_BRAVE: b""}, reg=reg)
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 0)
        d = out["data"]["default"]
        self.assertEqual((d["id"], d["executable"], d["needs_executable_path"]), ("brave", WIN_BRAVE, True))
        self.assertEqual(d["user_data_dir"], r"C:\Users\teste\AppData\Local\BraveSoftware\Brave-Browser\User Data")

    def test_reg_query_simulado_via_reg_exe(self):
        """Sem winreg (como neste host), o fallback roda `reg query` e interpreta a saída (inclusive '(Padrão)')."""
        run = {("reg", "query", "HKCU\\" + UC, "/v", "ProgId"): (0, fixture("windows_reg_userchoice.txt", False)),
               ("reg", "query", r"HKCR\BraveHTML\shell\open\command", "/ve"):
                   (0, fixture("windows_reg_command_ptbr.txt", False))}
        env = FakeEnv("windows", environ=WIN_ENV, files={WIN_BRAVE: b""}, run=run, reg=None)
        try:
            import winreg  # noqa: F401
            self.skipTest("host Windows: winreg real tem precedência sobre o reg.exe")
        except ImportError:
            pass
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(out["data"]["default"]["executable"], WIN_BRAVE)
        self.assertEqual(out["data"]["default"]["raw_id"], "BraveHTML")

    def test_parse_reg_query(self):
        self.assertEqual(db.parse_reg_query(fixture("windows_reg_userchoice.txt", False), "ProgId"), "BraveHTML")
        cmd = db.parse_reg_query(fixture("windows_reg_command_en.txt", False), "")
        self.assertEqual(db.parse_command_exe(cmd), r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        self.assertIsNone(db.parse_reg_query("ERRO: o sistema não encontrou a chave", "ProgId"))

    def test_progid_com_sufixo(self):
        self.assertEqual(db.key_for_progid("VivaldiHTM.ABCDEF123"), "vivaldi")
        self.assertEqual(db.key_for_progid("FirefoxURL-308046B0AF4A39CB"), "firefox")
        self.assertEqual(db.key_for_progid("MSEdgeHTM"), "msedge")
        self.assertIsNone(db.key_for_progid("ProgramaDesconhecido"))

    def test_firefox_padrao_recomenda_edge_no_caminho_do_playwright(self):
        reg = {("HKCU", UC, "ProgId"): "FirefoxURL-308046B0AF4A39CB"}
        env = FakeEnv("windows", environ=WIN_ENV, files={WIN_EDGE: b""}, reg=reg)
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(out["status"], "non_chromium_default")
        rec = out["data"]["recommended"]
        self.assertEqual((rec["id"], rec["needs_executable_path"]), ("msedge", False))

    def test_userchoicelatest_divergente_vira_problema(self):
        reg = {("HKCU", UC, "ProgId"): "ChromeHTML", ("HKCU", UCL, "ProgId"): "MSEdgeHTM"}
        env = FakeEnv("windows", environ=WIN_ENV, files={WIN_EDGE: b""}, reg=reg)
        _, out, _ = run_main(db.main, [], env)
        self.assertTrue(any("UserChoiceLatest" in p for p in out["problems"]))

    def test_sem_userchoice(self):
        env = FakeEnv("windows", environ=WIN_ENV, files={}, reg={})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual((code, out["status"]), (1, "no_chromium"))


LHOME = "/home/teste"
LINUX_ENV = {"HOME": LHOME, "DISPLAY": ":0"}


def linux_env(desktop_name, desktop_fixture, desktop_dir="/usr/share/applications", files=None, which=None,
              xdg_settings=None, environ=None):
    run = {("xdg-mime", "query", "default", "x-scheme-handler/https"): (0, desktop_name + "\n")}
    if xdg_settings:
        run[("xdg-settings", "get", "default-web-browser")] = (0, xdg_settings + "\n")
    f = {desktop_dir + "/" + desktop_name: fixture(desktop_fixture)}
    f.update(files or {})
    e = dict(LINUX_ENV)
    e.update(environ or {})
    return FakeEnv("linux", environ=e, files=f, which=which or {}, run=run)


class LinuxTests(unittest.TestCase):

    def test_brave_nativo_via_xdg_mime(self):
        env = linux_env("brave-browser.desktop", "linux_brave-browser.desktop",
                        files={"/usr/bin/brave-browser-stable": b""},
                        which={"brave-browser-stable": "/usr/bin/brave-browser-stable"})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual(code, 0)
        d = out["data"]["default"]
        self.assertEqual((d["id"], d["packaging"], d["executable"]), ("brave", "native", "/usr/bin/brave-browser-stable"))
        self.assertEqual(d["user_data_dir"], LHOME + "/.config/BraveSoftware/Brave-Browser")
        self.assertEqual(out["problems"], [])

    def test_brave_flatpak(self):
        exported = "/var/lib/flatpak/exports/bin/com.brave.Browser"
        env = linux_env("com.brave.Browser.desktop", "linux_com.brave.Browser.desktop",
                        desktop_dir="/var/lib/flatpak/exports/share/applications", files={exported: b""})
        _, out, _ = run_main(db.main, [], env)
        d = out["data"]["default"]
        self.assertEqual((d["id"], d["packaging"], d["executable"]), ("brave", "flatpak", exported))
        self.assertEqual(d["user_data_dir"], LHOME + "/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser")
        self.assertTrue(any("flatpak" in p for p in out["problems"]))

    def test_chromium_snap(self):
        env = linux_env("chromium_chromium.desktop", "linux_chromium_chromium.desktop",
                        desktop_dir="/var/lib/snapd/desktop/applications", files={"/snap/bin/chromium": b""})
        _, out, _ = run_main(db.main, [], env)
        d = out["data"]["default"]
        self.assertEqual((d["id"], d["packaging"], d["executable"]), ("chromium", "snap", "/snap/bin/chromium"))
        self.assertTrue(d["needs_executable_path"])

    def test_divergencia_xdg(self):
        env = linux_env("brave-browser.desktop", "linux_brave-browser.desktop",
                        files={"/usr/bin/brave-browser-stable": b""}, xdg_settings="google-chrome.desktop")
        _, out, _ = run_main(db.main, [], env)
        self.assertTrue(any("divergem" in p for p in out["problems"]))

    def test_firefox_padrao_e_chrome_em_opt(self):
        env = linux_env("firefox.desktop", "linux_firefox.desktop",
                        files={"/opt/google/chrome/chrome": b""}, which={"firefox": "/usr/bin/firefox"})
        _, out, _ = run_main(db.main, [], env)
        self.assertEqual(out["status"], "non_chromium_default")
        rec = out["data"]["recommended"]
        self.assertEqual((rec["id"], rec["needs_executable_path"]), ("chrome", False))

    def test_sem_display_avisa(self):
        env = linux_env("brave-browser.desktop", "linux_brave-browser.desktop",
                        files={"/usr/bin/brave-browser-stable": b""})
        env.environ.pop("DISPLAY")
        _, out, _ = run_main(db.main, [], env)
        self.assertTrue(any("DISPLAY" in p for p in out["problems"]))

    def test_parse_desktop_exec_remove_codigos(self):
        self.assertEqual(db.parse_desktop_exec(fixture("linux_brave-browser.desktop", False)),
                         ["/usr/bin/brave-browser-stable"])


class GeneralTests(unittest.TestCase):

    def test_so_nao_suportado(self):
        env = FakeEnv("freebsd", environ={"HOME": "/home/x"})
        code, out, _ = run_main(db.main, [], env)
        self.assertEqual((code, out["status"]), (1, "unsupported_os"))

    def test_erro_de_uso_sai_com_2_em_json(self):
        code, out, _ = run_main(db.main, ["--os", "beos"], FakeEnv("macos", environ={"HOME": HOME}))
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "usage_error")


class HelpPtBrTests(unittest.TestCase):
    def test_help_em_portugues(self):
        """Dado -h, quando o argparse imprime a ajuda, então os rótulos nativos saem em pt-BR."""
        text = db._Parser(description="x").format_help()
        self.assertIn("uso:", text)
        self.assertIn("mostra esta ajuda e sai", text)
        self.assertNotIn("show this help", text)


if __name__ == "__main__":
    unittest.main()
