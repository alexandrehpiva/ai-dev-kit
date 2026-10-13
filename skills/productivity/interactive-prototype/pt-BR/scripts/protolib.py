"""Biblioteca compartilhada dos scripts do modo grupo (só stdlib).

Contrato comum: todo script novo imprime UM objeto JSON no stdout (envelope abaixo) e sai com
0 (ok), 1 (problemas encontrados / precisa de decisão) ou 2 (uso incorreto).

  {"ok": bool, "status": "CODIGO", "data": {...}, "problems": [{"code","message"}], "questions": [...]}
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIG_NAME = 'prototype.config.json'
SKILL_NAME = 'interactive-prototype'
LEGACY_SKILL_VERSION = '1.0.0'

MEMBER_STATUSES = ('pending', 'approved', 'rejected', 'revoked')
ROLES = ('promoter', 'contributor')
PROFILES = ('product', 'technical')
EVIDENCE = ('host-verified', 'git-only', 'unverified')
ARTIFACT_KINDS = ('official', 'beta', 'preview')
ARTIFACT_STATUSES = ('current', 'stale', 'revoked', 'missing')
DELIVERIES = ('claude-artifact', 'file')

CHANGELOG_PENDING = 'Pendente (não commitado)'

# Trailers de commit (chave exata, como aparece na mensagem).
T_ACTOR = 'Prototype-Actor'                      # e-mail de quem executou
T_MEMBER_STATUS = 'Prototype-Member-Status'      # pending|approved|... no momento do commit
T_IDENTITY = 'Prototype-Identity'                # host-verified|git-only|unverified
T_CONFLICT = 'Prototype-Conflict-Decision'       # "kept=<ref>; dropped=<ref>; by=<email>; what=<texto curto>"
T_ROLLBACK_OF = 'Prototype-Rollback-Of'          # shas separados por vírgula
T_ROLLBACK_REASON = 'Prototype-Rollback-Reason'
T_PROMOTION = 'Prototype-Promotion'              # vX.Y.Z

DEFAULT_CONFIG = {
    'skill': {'name': SKILL_NAME, 'version': None},  # preenchido pelo chamador com skill_version()
    'groupMode': False,
    'remote': 'origin',
    'branches': {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'},
    'policy': {'promoters': 'all-members', 'requireSignedCommits': False, 'pendingExpiryDays': 7},
    'docs': {'autoMaintain': False},
    'members': [],
    'artifacts': [],
}


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def skill_root():
    return Path(__file__).resolve().parent.parent


def skill_version():
    """Lê `version:` do frontmatter do SKILL.md da skill (None se ausente)."""
    text = (skill_root() / 'SKILL.md').read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---', text, re.S)
    if not m:
        return None
    v = re.search(r'^version:\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?\s*$', m.group(1), re.M)
    return v.group(1) if v else None


def git(repo, *args, check=False, timeout=60, input=None):
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
                       timeout=timeout, input=input)
    if check and r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} falhou: {r.stderr.strip()}')
    return r


def config_path(repo):
    return Path(repo) / CONFIG_NAME


def load_config(repo):
    """Retorna (cfg|None, erro|None). Config ausente → (None, None)."""
    p = config_path(repo)
    if not p.exists():
        return None, None
    try:
        return json.loads(p.read_text(encoding='utf-8')), None
    except json.JSONDecodeError as e:
        return None, f'{CONFIG_NAME} inválido: {e}'


def save_config(repo, cfg):
    config_path(repo).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def emit(ok, status, data=None, problems=None, questions=None, stream=None):
    """Imprime o envelope JSON e devolve o exit code (0 se ok, senão 1)."""
    out = {'ok': bool(ok), 'status': status, 'data': data or {}, 'problems': problems or [],
           'questions': questions or []}
    print(json.dumps(out, ensure_ascii=False, indent=2), file=stream or sys.stdout)
    return 0 if ok else 1


def problem(code, message):
    return {'code': code, 'message': message}


def norm_email(email):
    return (email or '').strip().lower()


def find_member(cfg, email):
    e = norm_email(email)
    for m in (cfg or {}).get('members', []):
        if norm_email(m.get('email')) == e:
            return m
    return None


def is_promoter(member):
    return bool(member) and member.get('status') == 'approved' and 'promoter' in member.get('roles', [])


def slug_member(name_or_email):
    base = (name_or_email or '').split('@')[0]
    s = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
    return s or 'membro'


def draft_branch(cfg, member_email):
    pattern = cfg.get('branches', {}).get('draftPattern', 'draft/{member}')
    return pattern.replace('{member}', slug_member(member_email))


VERSION_RE = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?$')


def parse_version(text):
    """'v1.2.3' → (1,2,3,None); 'v1.2.3-beta.4' → (1,2,3,4); inválido → None."""
    m = VERSION_RE.match((text or '').strip())
    if not m:
        return None
    major, minor, patch, beta = m.groups()
    return int(major), int(minor), int(patch), (int(beta) if beta is not None else None)


def format_version(major, minor, patch, beta=None):
    return f'v{major}.{minor}.{patch}' + (f'-beta.{beta}' if beta is not None else '')


def bump(version_tuple, level):
    major, minor, patch = version_tuple[:3]
    if level == 'major':
        return major + 1, 0, 0
    if level == 'minor':
        return major, minor + 1, 0
    return major, minor, patch + 1


def parse_trailers(message):
    """Extrai `Chave: valor` do último parágrafo da mensagem (formato de trailer do git)."""
    paragraphs = [p for p in message.strip().split('\n\n') if p.strip()]
    out = {}
    if not paragraphs:
        return out
    for line in paragraphs[-1].splitlines():
        m = re.match(r'^([A-Za-z][A-Za-z0-9-]*):\s*(.*)$', line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def format_trailers(trailers):
    return '\n'.join(f'{k}: {v}' for k, v in trailers.items() if v not in (None, ''))


def commit_with_trailers(repo, subject, trailers, extra_args=()):
    msg = subject.strip() + '\n\n' + format_trailers(trailers) + '\n'
    return git(repo, 'commit', '-q', *extra_args, '-m', msg)
