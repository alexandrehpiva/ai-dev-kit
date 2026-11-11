# -*- coding: utf-8 -*-
"""Apoio dos testes: ambiente falso (arquivos, PATH, comandos e registro simulados).

As fixtures em fixtures/ são sintéticas: seguem os formatos descritos no relatório R6
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

    def run(self, cmd, timeout=5):
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
