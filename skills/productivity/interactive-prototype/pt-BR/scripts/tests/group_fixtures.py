"""Protótipo em modo grupo v2 para testes: repo inicial (v1.0.0 em main e beta) + clones por membro."""

import json
import shutil
from pathlib import Path

from helpers import SCRIPTS, clone, make_repo, run, write

import changelog_tools as ct
import protolib

TEMPLATES = SCRIPTS.parent / 'templates'

ANA = ('Ana Teste', 'ana@example.test')      # promoter aprovada, host-verified
BIA = ('Bia Teste', 'bia@example.test')      # contributor aprovada, git-only
CAIO = ('Caio Teste', 'caio@example.test')   # contributor pendente
DANI = ('Dani Teste', 'dani@example.test')   # rejeitada
EDU = ('Edu Teste', 'edu@example.test')      # promoter aprovado, git-only

CHANGELOG_PREFIX = "/* changelog do protótipo (teste) */\n\nconst CHANGELOG = "
CHANGELOG_SUFFIX = ";\n\nfunction renderChangelog(){ return CHANGELOG.length; }\n"

INDEX = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Teste</title></head>
<body>
<main id="screenRoot"></main>
<button class="prototype-version-badge" id="prototype-version-badge" onclick="openChangelog()">v1.0.0 · protótipo</button>
<script src="js/components/changelog-modal.js"></script>
<script src="js/screens/a.js"></script>
</body>
</html>
"""

SCREEN_A = "// tela A\nfunction telaA(){\n  return 'titulo original';\n}\n"


def member(user, status, roles, evidence):
    return {'name': user[0], 'email': user[1], 'roles': roles, 'profile': 'product', 'status': status,
            'registeredAt': '2026-01-01T00:00:00Z', 'statusChangedAt': '2026-01-01T00:00:00Z',
            'statusChangedAtCommit': None,
            'statusHistory': [{'status': status, 'at': '2026-01-01T00:00:00Z', 'commit': None, 'by': 'setup'}],
            'identityEvidence': evidence}


def config():
    return {
        'skill': {'name': 'interactive-prototype', 'version': '2.0.0'},
        'groupMode': True, 'remote': 'origin',
        'branches': {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'},
        'policy': {'promoters': 'listed', 'requireSignedCommits': False, 'pendingExpiryDays': 7},
        'docs': {'autoMaintain': False},
        'members': [member(ANA, 'approved', ['promoter'], 'host-verified'),
                    member(BIA, 'approved', ['contributor'], 'git-only'),
                    member(CAIO, 'pending', ['contributor'], 'unverified'),
                    member(DANI, 'rejected', ['contributor'], 'unverified'),
                    member(EDU, 'approved', ['promoter'], 'git-only')],
        'artifacts': [
            {'id': 'official', 'kind': 'official', 'branch': 'main', 'delivery': 'file', 'path': 'dist/index.html',
             'owner': ANA[1], 'version': 'v1.0.0', 'status': 'current', 'pendingVersion': None,
             'publishedAt': '2026-01-01T00:00:00Z', 'publishedBy': ANA[1]},
            {'id': 'beta', 'kind': 'beta', 'branch': 'beta', 'delivery': 'file', 'path': 'dist/index.html',
             'owner': ANA[1], 'version': 'v1.0.0', 'status': 'current', 'pendingVersion': None,
             'publishedAt': '2026-01-01T00:00:00Z', 'publishedBy': ANA[1]},
        ],
    }


def changelog_text(entries):
    return ct.render_text(CHANGELOG_PREFIX, entries, CHANGELOG_SUFFIX)


def git_out(repo, *args):
    return run(['git', '-C', str(repo), *args]).stdout.strip()


def make_group_repo(tmp):
    """Repo da Ana com main e beta em v1.0.0 (commit com Prototype-Promotion) publicados no remoto bare."""
    repo, remote = make_repo(tmp, name='proto', user=ANA)
    write(repo / '.gitignore', 'dist/\n')
    write(repo / 'index.html', INDEX)
    write(repo / 'js/screens/a.js', SCREEN_A)
    write(repo / ct.CHANGELOG_REL, changelog_text(
        [{'version': 'v1.0.0', 'date': '2026-01-01', 'changes': ['Primeira versão oficial.']}]))
    write(repo / protolib.CONFIG_NAME, json.dumps(config(), ensure_ascii=False, indent=2) + '\n')
    shutil.copy(TEMPLATES / 'build.py', repo / 'build.py')
    run(['git', '-C', str(repo), 'add', '-A'])
    r = protolib.commit_with_trailers(repo, 'feat(prototype): versão inicial',
                                      {protolib.T_ACTOR: ANA[1], protolib.T_PROMOTION: 'v1.0.0'})
    assert r.returncode == 0, r.stderr
    run(['git', '-C', str(repo), 'push', '-q', 'origin', 'main'])
    run(['git', '-C', str(repo), 'push', '-q', 'origin', 'main:refs/heads/beta'])
    run(['git', '-C', str(repo), 'fetch', '-q', 'origin'])
    return repo, remote


def member_clone(remote, tmp, user):
    return clone(remote, Path(tmp) / f'clone-{user[1].split("@")[0]}', user)


def add_pending(repo, *lines):
    """Simula o agente registrando o trabalho em andamento na entrada Pendente."""
    path = Path(repo) / ct.CHANGELOG_REL
    prefix, entries, suffix = ct.parse_text(path.read_text(encoding='utf-8'))
    pend = next((e for e in entries if ct.is_pending(e)), None)
    if pend is None:
        pend = {'version': protolib.CHANGELOG_PENDING, 'date': '2026-02-01', 'changes': []}
        entries.insert(0, pend)
    pend['changes'] += list(lines)
    path.write_text(ct.render_text(prefix, entries, suffix), encoding='utf-8')


def remote_file(remote, ref, rel):
    return run(['git', '--git-dir', str(remote), 'show', f'{ref}:{rel}']).stdout


def remote_sha(remote, ref):
    r = run(['git', '--git-dir', str(remote), 'rev-parse', '--verify', '-q', ref], check=False)
    return r.stdout.strip() or None


def remote_entries(remote, ref):
    return ct.parse_text(remote_file(remote, ref, ct.CHANGELOG_REL))[1]


def commit_body(remote, ref):
    return run(['git', '--git-dir', str(remote), 'log', '-1', '--format=%B', ref]).stdout
