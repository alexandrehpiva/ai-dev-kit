"""Skill sintética para testes: copia os scripts reais e fixa SKILL.md/templates, sem depender do estado do SKILL.md real."""

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from helpers import SCRIPTS

SKILL_REAL = SCRIPTS.parent

FAKE_TEMPLATES = {
    'AGENTS.md': '# Agentes de @@NAME@@\nskill @@SKILL_VERSION@@\n',
    'CLAUDE.md': '# Claude em @@NAME@@\n',
    'docs/business-rules.md': '# Regras de @@NAME@@\n',
    'docs/components.md': '# Componentes (skill @@SKILL_VERSION@@)\n',
}


def make_skill(dest, version='2.0.0', templates=True):
    """Cria <dest>/skill com scripts reais, schema real, SKILL.md `version:` e templates falsos."""
    root = Path(dest) / 'skill'
    shutil.copytree(SCRIPTS, root / 'scripts', ignore=shutil.ignore_patterns('tests', '__pycache__'))
    (root / 'templates').mkdir()
    shutil.copy(SKILL_REAL / 'templates' / 'prototype.config.schema.json', root / 'templates')
    fm = f'---\nname: interactive-prototype\n' + (f'version: {version}\n' if version else '') + '---\n\n# Skill\n'
    (root / 'SKILL.md').write_text(fm, encoding='utf-8')
    if templates:
        for rel, text in FAKE_TEMPLATES.items():
            p = root / 'templates' / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
    return root


def run(root, script, *args):
    """(exit, envelope|None, stderr) executando <root>/scripts/<script>."""
    r = subprocess.run([sys.executable, str(Path(root) / 'scripts' / script), *map(str, args)],
                       capture_output=True, text=True)
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        env = None
    return r.returncode, env, r.stderr


NOW = '2026-01-02T03:04:05Z'


def member(email='ana@example.test', status='approved', roles=('promoter', 'contributor'), **kw):
    m = {'name': 'Ana Teste', 'email': email, 'roles': list(roles), 'profile': 'technical', 'status': status,
         'registeredAt': NOW, 'statusChangedAt': NOW, 'statusChangedAtCommit': None,
         'statusHistory': [{'status': status, 'at': NOW, 'commit': None, 'by': 'setup'}],
         'identityEvidence': 'unverified'}
    m.update(kw)
    return m


def artifact(art_id='beta', kind='beta', owner='ana@example.test', **kw):
    a = {'id': art_id, 'kind': kind, 'branch': 'beta' if kind == 'beta' else ('main' if kind == 'official' else None),
         'delivery': 'claude-artifact', 'url': f'https://example.test/{art_id}', 'owner': owner, 'version': None,
         'status': 'stale', 'pendingVersion': None, 'publishedAt': None, 'publishedBy': None}
    a.update(kw)
    return a


def valid_cfg(group=True, **over):
    cfg = {'skill': {'name': 'interactive-prototype', 'version': '2.0.0'}, 'groupMode': group, 'remote': 'origin',
           'branches': {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'},
           'policy': {'promoters': 'all-members', 'requireSignedCommits': False, 'pendingExpiryDays': 7},
           'docs': {'autoMaintain': False}, 'members': [member()], 'artifacts': []}
    cfg.update(copy.deepcopy(over))
    return cfg


def write_cfg(repo, cfg):
    (Path(repo) / 'prototype.config.json').write_text(json.dumps(cfg, indent=2), encoding='utf-8')


def read_cfg(repo):
    return json.loads((Path(repo) / 'prototype.config.json').read_text(encoding='utf-8'))
