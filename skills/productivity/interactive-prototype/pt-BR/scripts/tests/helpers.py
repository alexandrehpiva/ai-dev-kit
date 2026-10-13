"""Auxiliares de teste: repositórios git temporários com remoto bare local (sem rede)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import protolib  # noqa: E402,F401


def run(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(f'{cmd} falhou: {r.stderr}')
    return r


def make_repo(tmp, name='proto', branch='main', user=('Ana Teste', 'ana@example.test')):
    """Cria <tmp>/<name> (git init) + <tmp>/<name>-remote.git (bare) com remoto `origin`."""
    tmp = Path(tmp)
    repo, remote = tmp / name, tmp / f'{name}-remote.git'
    repo.mkdir()
    run(['git', 'init', '-q', '-b', branch, str(repo)])
    run(['git', 'init', '-q', '--bare', '-b', branch, str(remote)])
    run(['git', '-C', str(repo), 'config', 'user.name', user[0]])
    run(['git', '-C', str(repo), 'config', 'user.email', user[1]])
    run(['git', '-C', str(repo), 'config', 'commit.gpgsign', 'false'])
    run(['git', '-C', str(repo), 'remote', 'add', 'origin', str(remote)])
    return repo, remote


def clone(remote, dest, user):
    run(['git', 'clone', '-q', str(remote), str(dest)])
    run(['git', '-C', str(dest), 'config', 'user.name', user[0]])
    run(['git', '-C', str(dest), 'config', 'user.email', user[1]])
    run(['git', '-C', str(dest), 'config', 'commit.gpgsign', 'false'])
    return Path(dest)


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def commit_all(repo, message):
    run(['git', '-C', str(repo), 'add', '-A'])
    run(['git', '-C', str(repo), 'commit', '-q', '-m', message])
    return run(['git', '-C', str(repo), 'rev-parse', 'HEAD']).stdout.strip()


def run_script(script, *args, cwd=None):
    """Executa um script da skill e devolve (exit_code, envelope_json|None, stdout, stderr)."""
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], cwd=cwd,
                       capture_output=True, text=True)
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        env = None
    return r.returncode, env, r.stdout, r.stderr


class TmpDirMixin:
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()
