# -*- coding: utf-8 -*-
"""Testes do clone_profile.py. Só perfis SINTÉTICOS em pastas temporárias (nunca perfil real)."""

import json
import os
import shutil
import sqlite3
import stat
import tempfile
import unittest

from helpers import (COOKIE_SENTINEL, make_cookies_db, make_profile_tree, read_json, read_text_file, run_main,
                     sha256_file, tree_snapshot)
import clone_profile as cp
import detect_browser as db


class CloneBase(unittest.TestCase):

    os_name = "macos"

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pwmcp-w3-clone-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.src = os.path.join(self.tmp, "src-udd")
        exe_dir = os.path.join(self.tmp, "Apps", "Brave Browser.app", "Contents", "MacOS")
        os.makedirs(exe_dir)
        self.exe = os.path.join(exe_dir, "Brave Browser")
        open(self.exe, "w").close()
        self.dest = os.path.join(self.tmp, "dest")

    def tearDown(self):
        for r, dirs, files in os.walk(self.tmp):  # devolve permissão de escrita (teste de origem somente leitura)
            for n in dirs + files:
                try:
                    os.chmod(os.path.join(r, n), 0o700)
                except OSError:
                    pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def env(self, os_name=None):
        return db.SystemEnv(os_name=os_name or self.os_name, environ={"HOME": self.home, "USERPROFILE": self.home,
                                                                      "LOCALAPPDATA": os.path.join(self.home, "AppData", "Local"),
                                                                      "PATH": os.environ.get("PATH", "")})

    def clone(self, *extra, **kw):
        argv = ["--browser", self.exe, "--source-dir", self.src, "--dest", kw.get("dest", self.dest)] + list(extra)
        code, out, raw = run_main(cp.main, argv, kw.get("env") or self.env())
        self.assertNotIn(COOKIE_SENTINEL, raw)
        self.assertNotIn("pessoa@exemplo.test", raw)
        self.assertNotIn("NOME-DO-PERFIL-FALSO", raw)
        return code, out

    def rel(self, base):
        out = set()
        for r, dirs, files in os.walk(base):
            for n in dirs + files:
                out.add(os.path.relpath(os.path.join(r, n), base))
        return out


class DryRunTests(CloneBase):

    def test_dry_run_nao_cria_nada_e_mostra_plano(self):
        # Given um perfil sintético; When --dry-run; Then status planned, dest inexistente, plano com excluídos
        make_profile_tree(self.src)
        code, out = self.clone("--level", "light", "--dry-run")
        self.assertEqual((code, out["status"]), (0, "planned"))
        self.assertFalse(os.path.exists(self.dest))
        names = {e["name"] for e in out["data"]["excluded"]}
        self.assertTrue({"Cache", "Code Cache", "GPUCache", "Service Worker", "Extensions", "History",
                         "Login Data", "lockfile"} <= names)
        self.assertIn("Local Storage", {i["name"] for i in out["data"]["included"]})
        self.assertGreater(out["data"]["bytes"], 0)


class LevelTests(CloneBase):

    def setUp(self):
        super(LevelTests, self).setUp()
        make_profile_tree(self.src)

    def test_minimal_copia_so_local_state_e_cookies(self):
        code, out = self.clone("--level", "minimal")
        self.assertEqual((code, out["status"]), (0, "cloned"))
        files = {f for f in self.rel(self.dest) if os.path.isfile(os.path.join(self.dest, f))}
        self.assertEqual(files, {"Local State", os.path.join("Default", "Cookies"), cp.MARKER, cp.CONFIG_NAME})
        self.assertEqual(out["data"]["cookie_rows"], 3)

    def test_light_exclui_caches_historico_senhas_e_travas(self):
        code, out = self.clone("--level", "light")
        self.assertEqual(code, 0)
        got = self.rel(self.dest)
        for kept in ("Local State", "Default/Local Storage/dados.bin", "Default/IndexedDB/dados.bin",
                     "Default/Session Storage/dados.bin", "Default/Preferences", "Default/Cookies"):
            self.assertIn(os.path.normpath(kept), got)
        for gone in ("Default/Cache", "Default/Code Cache", "Default/GPUCache", "Default/Service Worker",
                     "Default/Extensions", "Default/Sessions", "Default/History", "Default/History-journal",
                     "Default/Favicons", "Default/Login Data", "SingletonLock", "SingletonSocket",
                     "SingletonCookie", "Default/lockfile"):
            self.assertNotIn(os.path.normpath(gone), got, gone)

    def test_full_copia_quase_tudo_mas_sem_travas_e_sessions(self):
        code, out = self.clone("--level", "full")
        self.assertEqual(code, 0)
        got = self.rel(self.dest)
        for kept in ("Default/Cache/dados.bin", "Default/Login Data", "Default/History", "Default/Extensions/dados.bin"):
            self.assertIn(os.path.normpath(kept), got)
        for gone in ("Default/Sessions", "SingletonLock", "Default/lockfile"):
            self.assertNotIn(os.path.normpath(gone), got)


class SourceSafetyTests(CloneBase):

    def test_origem_nao_muda_nada(self):
        make_profile_tree(self.src)
        before = tree_snapshot(self.src)
        code, _ = self.clone("--level", "full")
        self.assertEqual(code, 0)
        self.assertEqual(tree_snapshot(self.src), before)

    @unittest.skipIf(os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0), "precisa de POSIX não-root")
    def test_origem_somente_leitura_ainda_copia(self):
        # Se a cópia tentasse escrever na origem (journal, lock), falharia aqui.
        make_profile_tree(self.src, locks=False)
        for r, dirs, files in os.walk(self.src):
            for n in files:
                os.chmod(os.path.join(r, n), 0o444)
            os.chmod(r, 0o555)
        code, out = self.clone("--level", "light")
        self.assertEqual((code, out["status"]), (0, "cloned"), out["problems"])
        self.assertEqual(out["data"]["cookie_rows"], 3)

    def test_backup_pega_linhas_que_so_existem_no_wal(self):
        # Given um Cookies em modo WAL com o navegador (conexão) aberto e dados ainda só no -wal
        make_profile_tree(self.src, locks=False)
        os.unlink(os.path.join(self.src, "Default", "Cookies"))
        con = make_cookies_db(os.path.join(self.src, "Default", "Cookies"), rows=5, wal=True)
        self.addCleanup(con.close)
        self.assertTrue(os.path.getsize(os.path.join(self.src, "Default", "Cookies-wal")) > 0)
        # When clona; Then as 5 linhas vêm na cópia (um cp do arquivo principal as perderia)
        code, out = self.clone("--level", "minimal")
        self.assertEqual(code, 0)
        self.assertEqual(out["data"]["cookie_rows"], 5)
        chk = sqlite3.connect(os.path.join(self.dest, "Default", "Cookies"))
        self.addCleanup(chk.close)
        self.assertEqual(chk.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(chk.execute("SELECT count(*) FROM cookies").fetchone()[0], 5)

    def test_cookies_corrompido_falha_sem_tocar_a_origem(self):
        make_profile_tree(self.src)
        cookie = os.path.join(self.src, "Default", "Cookies")
        with open(cookie, "wb") as fh:
            fh.write(b"isto nao e um sqlite" * 50)
        digest = sha256_file(cookie)
        code, out = self.clone("--level", "light")
        self.assertEqual((code, out["status"]), (1, "copy_failed"))
        self.assertEqual(sha256_file(cookie), digest)

    def test_layout_windows_network_cookies(self):
        make_profile_tree(self.src, cookies_rel=("Network", "Cookies"), locks=False)
        code, out = self.clone("--level", "minimal")
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.dest, "Default", "Network", "Cookies")))
        self.assertEqual(out["data"]["cookie_databases"], ["Network/Cookies"])

    def test_cookies_recente_avisa_para_esperar(self):
        make_profile_tree(self.src)
        _, out = self.clone("--level", "minimal")
        self.assertTrue(any("espere ~30 s" in p for p in out["problems"]))
        old = os.path.join(self.src, "Default", "Cookies")
        os.utime(old, (1, 1))
        _, out = self.clone("--level", "minimal", "--replace")
        self.assertFalse(any("espere ~30 s" in p for p in out["problems"]))


class DestTests(CloneBase):

    def setUp(self):
        super(DestTests, self).setUp()
        make_profile_tree(self.src)

    def test_recusa_pasta_alheia_mesmo_com_replace(self):
        os.makedirs(self.dest)
        precious = os.path.join(self.dest, "importante.txt")
        with open(precious, "w") as fh:
            fh.write("nao apague")
        for extra in ((), ("--replace",)):
            code, out = self.clone("--level", "minimal", *extra)
            self.assertEqual((code, out["status"]), (1, "dest_conflict"))
            self.assertEqual(read_text_file(precious), "nao apague")
        self.assertFalse(os.path.exists(os.path.join(self.dest, cp.MARKER)))

    def test_pasta_vazia_e_aceita(self):
        os.makedirs(self.dest)
        code, out = self.clone("--level", "minimal")
        self.assertEqual((code, out["status"]), (0, "cloned"))

    def test_pasta_com_marcador_exige_replace_e_refaz(self):
        self.assertEqual(self.clone("--level", "minimal")[0], 0)
        stale = os.path.join(self.dest, "resto-antigo.txt")
        open(stale, "w").close()
        code, out = self.clone("--level", "minimal")
        self.assertEqual((code, out["status"]), (1, "dest_conflict"))
        self.assertTrue(os.path.exists(stale))
        code, out = self.clone("--level", "minimal", "--replace")
        self.assertEqual((code, out["status"]), (0, "cloned"))
        self.assertFalse(os.path.exists(stale))
        self.assertIsNotNone(cp.read_marker(self.dest))

    def test_dest_dentro_da_origem_ou_contendo_a_origem(self):
        for bad in (os.path.join(self.src, "copia"), self.tmp):
            code, out = self.clone("--level", "minimal", dest=bad)
            self.assertEqual((code, out["status"]), (1, "dest_conflict"), bad)
        self.assertEqual(os.listdir(self.src).count("copia"), 0)

    def test_dest_home_ou_raiz_recusado(self):
        for bad in (self.home, os.path.abspath(os.sep)):
            code, out = self.clone("--level", "minimal", "--dry-run", dest=bad)
            self.assertEqual((code, out["status"]), (1, "dest_conflict"), bad)

    def test_dest_e_um_arquivo(self):
        open(self.dest, "w").close()
        code, out = self.clone("--level", "minimal")
        self.assertEqual((code, out["status"]), (1, "dest_conflict"))

    @unittest.skipIf(os.name != "posix", "permissões POSIX")
    def test_pasta_destino_700_e_arquivos_sensiveis_600(self):
        self.assertEqual(self.clone("--level", "minimal")[0], 0)
        self.assertEqual(stat.S_IMODE(os.stat(self.dest).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(self.dest, cp.CONFIG_NAME)).st_mode), 0o600)


class ProfileTests(CloneBase):

    def test_perfil_nao_default_mantem_o_nome_e_gera_profile_directory(self):
        make_profile_tree(self.src, profiles=("Default", "Profile 2"), last_active=("Profile 2",))
        code, out = self.clone("--level", "minimal")  # auto = último ativo
        self.assertEqual((code, out["data"]["profile"]), (0, "Profile 2"))
        self.assertTrue(os.path.isfile(os.path.join(self.dest, "Profile 2", "Cookies")))
        self.assertFalse(os.path.exists(os.path.join(self.dest, "Default")))
        cfg = read_json(os.path.join(self.dest, cp.CONFIG_NAME))
        self.assertEqual(cfg["browser"]["launchOptions"]["args"], ["--profile-directory=Profile 2"])

    def test_default_nao_leva_profile_directory(self):
        make_profile_tree(self.src)
        self.assertEqual(self.clone("--level", "minimal")[0], 0)
        cfg = read_json(os.path.join(self.dest, cp.CONFIG_NAME))
        self.assertNotIn("args", cfg["browser"]["launchOptions"])

    def test_profile_explicito(self):
        make_profile_tree(self.src, profiles=("Default", "Profile 2"))
        code, out = self.clone("--level", "minimal", "--profile", "Default")
        self.assertEqual((code, out["data"]["profile"]), (0, "Default"))

    def test_perfil_inexistente_ou_invalido(self):
        make_profile_tree(self.src)
        for bad in ("Profile 9", "../fora", "a/b"):
            code, out = self.clone("--level", "minimal", "--profile", bad)
            self.assertEqual((code, out["status"]), (1, "profile_issue"), bad)

    def test_origem_inexistente(self):
        code, out = self.clone("--level", "minimal", "--source-dir", os.path.join(self.tmp, "nao-existe"))
        self.assertEqual((code, out["status"]), (1, "profile_issue"))

    def test_navegador_inexistente(self):
        code, out, _ = run_main(cp.main, ["--browser", os.path.join(self.tmp, "nada"), "--dest", self.dest], self.env())
        self.assertEqual((code, out["status"]), (1, "browser_issue"))


class DestinoSeguroTests(CloneBase):
    """Decisão I4: o destino nunca fica em git, cofre Obsidian, pasta sincronizada ou link simbólico."""

    def setUp(self):
        super(DestinoSeguroTests, self).setUp()
        make_profile_tree(self.src)

    def _recusa(self, dest, trecho):
        code, out = self.clone("--level", "minimal", dest=dest)
        self.assertEqual((code, out["status"]), (1, "dest_conflict"), out["problems"])
        self.assertTrue(any(trecho in p for p in out["problems"]), out["problems"])
        self.assertIn("playwright-mcp-copies", " ".join(out["next_steps"]))
        self.assertFalse(os.path.exists(dest))

    def test_dentro_de_repositorio_git(self):
        repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        self._recusa(os.path.join(repo, "sub", "copia"), "git")

    def test_dentro_de_cofre_obsidian(self):
        vault = os.path.join(self.tmp, "cofre")
        os.makedirs(os.path.join(vault, ".obsidian"))
        self._recusa(os.path.join(vault, "copia"), "Obsidian")

    def test_pastas_sincronizadas_conhecidas(self):
        for nome in ("Mobile Documents", "iCloud Drive", "Google Drive", "GoogleDrive-conta", "Dropbox",
                     "OneDrive - Empresa"):
            self._recusa(os.path.join(self.tmp, nome, "x", "copia"), "sincronizada")

    def test_link_simbolico_e_recusado_sem_traceback(self):
        alvo = os.path.join(self.tmp, "alvo")
        self.clone("--level", "minimal", dest=alvo)  # cria uma pasta marcada
        link = os.path.join(self.tmp, "link")
        os.symlink(alvo, link)
        code, out = self.clone("--level", "minimal", "--replace", dest=link)
        self.assertEqual((code, out["status"]), (1, "dest_conflict"))
        self.assertTrue(any("simbólico" in p for p in out["problems"]))
        self.assertTrue(os.path.isdir(alvo))  # nada foi apagado

    def test_home_versionado_nao_bloqueia_o_destino_padrao(self):
        os.makedirs(os.path.join(self.home, ".git"))  # HOME como repositório de dotfiles
        code, out, _ = run_main(cp.main, ["--browser", self.exe, "--source-dir", self.src, "--level", "minimal",
                                          "--dry-run"], self.env())
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])


class DestinoPadraoTests(CloneBase):

    def padrao(self, os_name):
        make_profile_tree(self.src, profiles=("Default", "Profile 2"), last_active=["Profile 2"])
        code, out, _ = run_main(cp.main, ["--browser", self.exe, "--source-dir", self.src, "--level", "minimal",
                                          "--dry-run"], self.env(os_name))
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        return out["data"]

    def test_macos(self):
        d = self.padrao("macos")
        self.assertEqual(d["dest"], os.path.join(self.home, "Library", "Application Support",
                                                 "playwright-mcp-copies", "brave-Profile-2"))
        self.assertEqual(d["output_dir"], d["dest"] + "-output")
        self.assertFalse(os.path.exists(d["dest"]))

    def test_linux(self):
        d = self.padrao("linux")
        self.assertEqual(d["dest"], os.path.join(self.home, ".local", "share", "playwright-mcp-copies",
                                                 "brave-Profile-2"))

    def test_windows(self):
        d = self.padrao("windows")
        self.assertIn(os.path.join("AppData", "Local", "playwright-mcp-copies"), d["dest"])

    def test_copia_real_no_padrao_cria_marcador_com_executavel_e_pasta_de_saida(self):
        make_profile_tree(self.src)
        code, out, _ = run_main(cp.main, ["--browser", self.exe, "--source-dir", self.src, "--level", "minimal"],
                                self.env())
        self.assertEqual((code, out["status"]), (0, "cloned"), out["problems"])
        dest = out["data"]["dest"]
        marker = read_json(os.path.join(dest, cp.MARKER))
        self.assertEqual((marker["browser"], marker["executable"]), ("brave", self.exe))
        outd = out["data"]["output_dir"]
        self.assertTrue(os.path.isdir(outd))
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(os.stat(outd).st_mode), 0o700)
        argv = out["data"]["mcp_argv"]
        self.assertEqual(argv[argv.index("--output-dir") + 1], outd)
        self.assertIn("--output-dir", out["data"]["mcp_command"])


class PlanoMinimalETPerfilTests(CloneBase):

    def setUp(self):
        super(PlanoMinimalETPerfilTests, self).setUp()
        make_profile_tree(self.src)

    def test_dry_run_minimal_lista_local_state_e_cookies_em_included(self):
        code, out = self.clone("--level", "minimal", "--dry-run")
        self.assertEqual(code, 0)
        inc = {i["name"] for i in out["data"]["included"]}
        self.assertEqual(inc, {"Local State", "Cookies (instantâneo)"})
        self.assertNotIn("Cookies", {e["name"] for e in out["data"]["excluded"]})
        self.assertGreater(out["data"]["bytes"], 0)

    def test_perfil_ponto_pontoponto_e_absoluto_sao_recusados(self):
        for bad in (".", "..", self.src, "../x", "a/b"):
            code, out = self.clone("--level", "minimal", "--profile", bad, "--dry-run")
            self.assertEqual((code, out["status"]), (1, "profile_issue"), bad)

    def test_nome_atipico_existente_e_aceito_com_aviso(self):
        os.makedirs(os.path.join(self.src, "Perfil Estranho"))
        code, out = self.clone("--level", "minimal", "--profile", "Perfil Estranho", "--dry-run")
        self.assertEqual((code, out["status"]), (0, "planned"), out["problems"])
        self.assertTrue(any("padrão do Chromium" in p for p in out["problems"]))


class ConfigPerOsTests(CloneBase):

    def setUp(self):
        super(ConfigPerOsTests, self).setUp()
        make_profile_tree(self.src)

    def test_ignore_default_args_por_so(self):
        self.assertEqual(cp.ignore_default_args("macos"), ["--use-mock-keychain"])
        self.assertEqual(cp.ignore_default_args("linux"), ["--password-store=basic"])
        self.assertEqual(cp.ignore_default_args("windows"), [])

    def test_config_gerado_em_cada_so(self):
        expected = {"macos": ["--use-mock-keychain"], "linux": ["--password-store=basic"], "windows": None}
        for os_name, ign in expected.items():
            dest = os.path.join(self.tmp, "d-" + os_name)
            code, out = self.clone("--level", "minimal", dest=dest, env=self.env(os_name))
            self.assertEqual(code, 0, (os_name, out["problems"]))
            launch = read_json(os.path.join(dest, cp.CONFIG_NAME))["browser"]["launchOptions"]
            self.assertIs(launch["headless"], True)
            self.assertEqual(launch.get("ignoreDefaultArgs"), ign, os_name)

    def test_comando_mcp(self):
        code, out = self.clone("--level", "minimal", "--dry-run")
        argv = out["data"]["mcp_argv"]
        self.assertEqual(argv[:4], ["npx", "-y", "@playwright/mcp@0.0.85", "--headless"])
        self.assertEqual(argv[argv.index("--executable-path") + 1], self.exe)
        self.assertEqual(argv[argv.index("--user-data-dir") + 1], self.dest)
        self.assertEqual(argv[argv.index("--config") + 1], os.path.join(self.dest, cp.CONFIG_NAME))
        self.assertNotIn("--isolated", argv)
        # No Windows o comando usa cmd /c
        _, outw = self.clone("--level", "minimal", "--dry-run", env=self.env("windows"))
        self.assertEqual(outw["data"]["mcp_argv"][:3], ["cmd", "/c", "npx"])
        self.assertTrue(outw["data"]["mcp_command"].startswith("cmd /c npx"))

    def test_windows_avisa_app_bound(self):
        _, out = self.clone("--level", "minimal", "--dry-run", env=self.env("windows"))
        self.assertTrue(any("v20" in p and "[não verificado]" in p for p in out["problems"]))

    def test_versao_vem_do_ambiente(self):
        os.environ[cp.cm.VERSION_ENV] = "0.0.99"
        self.addCleanup(lambda: os.environ.pop(cp.cm.VERSION_ENV, None))
        _, out = self.clone("--level", "minimal", "--dry-run")
        self.assertIn("@playwright/mcp@0.0.99", out["data"]["mcp_argv"])


class UnitTests(unittest.TestCase):

    def test_padroes_de_exclusao(self):
        self.assertTrue(cp._matches("History-journal", cp.LIGHT_EXCLUDE))
        self.assertTrue(cp._matches("Extension Rules", cp.LIGHT_EXCLUDE))
        self.assertTrue(cp._matches("Login Data For Account", cp.LIGHT_EXCLUDE))
        self.assertFalse(cp._matches("Local Storage", cp.LIGHT_EXCLUDE))
        self.assertFalse(cp._matches("IndexedDB", cp.LIGHT_EXCLUDE))
        self.assertFalse(cp._matches("Cookies", cp.LIGHT_EXCLUDE))
        self.assertTrue(cp._matches("SingletonSocket", cp.LOCK_PATTERNS))
        self.assertTrue(cp._matches("lockfile", cp.LOCK_PATTERNS))


if __name__ == "__main__":
    unittest.main()
