# -*- coding: utf-8 -*-
"""Apoio dos testes: ambiente falso (arquivos, PATH, comandos e registro simulados).

As fixtures em fixtures/ são sintéticas: seguem formatos conhecidos
(plist do LaunchServices conferido no macOS; saída de `reg query` e arquivos .desktop no
formato documentado pela comunidade/freedesktop — [não verificado] em Windows/Linux reais).
"""

import io
import json
import os
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import detect_browser as db  # noqa: E402


def fixture(name, binary=True):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        data = fh.read()
    return data if binary else data.decode("utf-8")


class FakeEnv(db.SystemEnv):
    """Sistema simulado. Nada toca o disco real nem roda processos."""

    def __init__(self, os_name="macos", environ=None, files=None, dirs=None, which=None, run=None,
                 reg=None):
        super(FakeEnv, self).__init__(os_name=os_name, environ=environ or {})
        self.files = {}
        for k, v in (files or {}).items():
            self.files[k] = v.encode("utf-8") if isinstance(v, str) else v
        self.dirs = set(dirs or [])
        for f in list(self.files) + list(self.dirs):
            d = self.path.dirname(f)
            while d and d not in self.dirs and d != self.path.dirname(d):
                self.dirs.add(d)
                d = self.path.dirname(d)
        self.which_map = which or {}
        self.run_map = run or {}
        self.reg_map = reg
        self.calls = []
        self.reads = []  # caminhos lidos (permite provar que um arquivo NÃO foi lido)

    def exists(self, p):
        return p in self.files or p in self.dirs

    def isfile(self, p):
        return p in self.files

    def isdir(self, p):
        return p in self.dirs

    def listdir(self, p):
        out = set()
        for item in list(self.files) + list(self.dirs):
            if self.path.dirname(item) == p:
                out.add(self.path.basename(item))
        return sorted(out)

    def read_bytes(self, p):
        self.reads.append(p)
        return self.files.get(p)

    def which(self, name):
        return self.which_map.get(name)

    def run(self, cmd, timeout=5, cwd=None):
        self.calls.append(list(cmd))
        r = self.run_map.get(tuple(cmd))
        if r is None:
            return None, ""
        return r

    def reg_get(self, hive, subkey, value_name):
        if self.reg_map is None:
            return super(FakeEnv, self).reg_get(hive, subkey, value_name)
        return self.reg_map.get((hive, subkey, value_name))


def run_main(main, argv, env):
    """Executa main() capturando o JSON. Devolve (exit, payload, stdout cru)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            code = main(argv, env=env)
        except SystemExit as exc:  # erro de uso do argparse
            code = exc.code
    raw = buf.getvalue()
    return code, json.loads(raw), raw


# ---------------------------------------------------------------------------
# Perfil Chromium SINTÉTICO (nunca use perfil real nos testes)
# ---------------------------------------------------------------------------

import sqlite3  # noqa: E402

COOKIE_SENTINEL = "SENTINELA-COOKIE-NAO-PODE-APARECER"  # gitleaks:allow (valor falso de teste)


def make_cookies_db(path, rows=3, wal=False):
    """Cria um banco de Cookies sintético. Com wal=True devolve a conexão aberta (dados só no WAL)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    if wal:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("CREATE TABLE IF NOT EXISTS cookies (host_key TEXT, name TEXT, value TEXT, encrypted_value BLOB)")
    for i in range(rows):
        con.execute("INSERT INTO cookies VALUES (?,?,?,?)",
                    (".exemplo.test", "c%d" % i, COOKIE_SENTINEL, b"v10" + bytes([i]) * 8))
    con.commit()
    if wal:
        return con
    con.close()
    return None


def make_profile_tree(root, profiles=("Default",), cookies_rel=("Cookies",), last_active=None, locks=True,
                      rows=3):
    """Monta <root> como uma pasta de dados Chromium falsa e devolve o caminho."""
    os.makedirs(root, exist_ok=True)
    info_cache = {p: {"name": "NOME-DO-PERFIL-FALSO", "user_name": "pessoa@exemplo.test"} for p in profiles}
    state = {"profile": {"info_cache": info_cache, "last_active_profiles": list(last_active or profiles[:1]),
                         "last_used": (last_active or profiles[:1])[0]},
             "os_crypt": {"encrypted_key": "CHAVE-FALSA"}}
    with open(os.path.join(root, "Local State"), "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    for prof in profiles:
        base = os.path.join(root, prof)
        make_cookies_db(os.path.join(base, *cookies_rel), rows=rows)
        for d in ("Cache", "Code Cache", "GPUCache", "Service Worker", "Extensions", "Sessions",
                  "Local Storage", "IndexedDB", "Session Storage"):
            os.makedirs(os.path.join(base, d), exist_ok=True)
            with open(os.path.join(base, d, "dados.bin"), "wb") as fh:
                fh.write(b"x" * 100)
        for f in ("History", "History-journal", "Favicons", "Login Data", "Preferences", "Bookmarks"):
            with open(os.path.join(base, f), "wb") as fh:
                fh.write(b"y" * 50)
        if locks:
            for f in ("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile"):
                with open(os.path.join(root if f != "lockfile" else base, f), "w") as fh:
                    fh.write("trava")
    return root


def tree_snapshot(root):
    """{caminho relativo: (tamanho, mtime_ns)} para provar que nada na origem mudou."""
    out = {}
    for r, dirs, files in os.walk(root):
        for n in dirs + files:
            p = os.path.join(r, n)
            st = os.lstat(p)
            out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns)
    return out


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text_file(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def sha256_file(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()
