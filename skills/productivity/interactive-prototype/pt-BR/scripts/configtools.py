"""Helpers de config compartilhados por config-validate, skill-status, migrate e artifacts (só stdlib)."""

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import protolib

SCRIPTS_DIR = Path(__file__).resolve().parent
SEMVER_RE = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')


def load_script(filename):
    """Carrega um script de nome com hífen (ex.: config-validate.py) como módulo, sem executá-lo como __main__."""
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_semver(text):
    m = SEMVER_RE.match((text or '').strip()) if isinstance(text, str) else None
    return tuple(int(g) for g in m.groups()) if m else None


def atomic_save_config(repo, cfg):
    """Grava o config via arquivo temporário na mesma pasta + rename (nunca deixa JSON truncado)."""
    target = protolib.config_path(repo)
    fd, tmp = tempfile.mkstemp(prefix='.prototype.config.', suffix='.tmp', dir=str(target.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
        if target.exists():
            os.chmod(tmp, target.stat().st_mode & 0o777)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def resolve_repo(raw):
    """Path resolvido ou None se não for uma pasta existente."""
    p = Path(raw).expanduser().resolve()
    return p if p.is_dir() else None


def usage_error(message, stream=None):
    """Envelope de uso incorreto (exit 2)."""
    protolib.emit(False, 'BAD_USAGE', problems=[protolib.problem('BAD_USAGE', message)], stream=stream)
    return 2


def is_v2(cfg):
    return isinstance(cfg, dict) and 'skill' in cfg


class JsonArgumentParser(argparse.ArgumentParser):
    """argparse que reporta erro de uso no envelope JSON (stdout) e sai com 2."""

    def error(self, message):
        usage_error(message)
        sys.exit(2)
