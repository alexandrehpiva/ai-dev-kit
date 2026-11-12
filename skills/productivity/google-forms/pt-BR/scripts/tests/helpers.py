# -*- coding: utf-8 -*-
"""Apoio dos testes: caminhos, captura do JSON dos scripts e uma skill playwright-mcp falsa.

Os testes do check_setup.py nunca leem perfil, configuração de harness nem token reais: usam uma
skill playwright-mcp FALSA em diretório temporário (um check_setup.py que devolve o JSON combinado)
e um ambiente mínimo montado aqui.
"""

import io
import json
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# check_setup.py de mentira: grava como foi chamado e devolve o que o teste combinou em response.json.
FAKE_CHECK_SETUP = '''# -*- coding: utf-8 -*-
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, "response.json")))
with open(os.path.join(here, "called.json"), "w") as fh:
    json.dump({"argv": sys.argv[1:], "isolated": sys.flags.isolated, "dont_write_bytecode": sys.dont_write_bytecode,
               "cwd": os.getcwd(), "token_visible": "PLAYWRIGHT_MCP_EXTENSION_TOKEN" in os.environ}, fh)
if "raw_stdout" in spec:
    sys.stdout.write(spec["raw_stdout"])
else:
    sys.stdout.write(json.dumps(spec["payload"], ensure_ascii=False))
sys.exit(spec.get("exit", 0))
'''


def pm_payload(status, problems=None, next_steps=None, data=None):
    """JSON no contrato do check_setup.py da skill playwright-mcp."""
    return {"ok": status == "ready", "status": status, "data": data or {"mode": "extension"},
            "problems": problems or [], "next_steps": next_steps or []}


def make_fake_pm(root, payload=None, exit_code=0, raw_stdout=None, rel=("playwright-mcp",)):
    """Cria <root>/<rel...>/scripts/check_setup.py falso e devolve a pasta da skill falsa."""
    pm = os.path.join(root, *rel)
    os.makedirs(os.path.join(pm, "scripts"))
    with open(os.path.join(pm, "scripts", "check_setup.py"), "w") as fh:
        fh.write(FAKE_CHECK_SETUP)
    set_response(pm, payload, exit_code, raw_stdout)
    return pm


def set_response(pm, payload=None, exit_code=0, raw_stdout=None):
    spec = {"exit": exit_code}
    if raw_stdout is not None:
        spec["raw_stdout"] = raw_stdout
    else:
        spec["payload"] = payload if payload is not None else pm_payload("ready")
    with open(os.path.join(pm, "scripts", "response.json"), "w") as fh:
        json.dump(spec, fh)


def called(pm):
    with open(os.path.join(pm, "scripts", "called.json")) as fh:
        return json.load(fh)


def clean_environ(**extra):
    """Ambiente mínimo: só o necessário para o Python rodar; sem PYTHONPATH, sem token, sem HOME real."""
    env = {}
    for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    env.update(extra)
    return env


class Sandbox(object):
    """Pasta temporária com limpeza explícita."""

    def __init__(self, prefix="gforms-cs-"):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix=prefix))

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


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
