#!/usr/bin/env python3
"""Identifica automaticamente quem está trabalhando no protótipo e cruza com o roster do modo grupo.

Só stdlib. Imprime o envelope JSON de protolib; exit 0 (identificado/sem config), 1 (precisa de
decisão: UNKNOWN, NO_IDENTITY, REJECTED, REVOKED, MISMATCH) ou 2 (uso incorreto).

  python3 identity-check.py --repo <pasta> [--name N --email E] [--register]
                            [--set-local-git-identity] [--no-host]

Camadas de detecção (nenhuma pergunta ao usuário quando a identidade já existe):
  1. `git config user.name/user.email` (local, depois global). `--name/--email` preenchem o que faltar;
     `--set-local-git-identity` grava com `git config --local` (nunca global).
  2. Oportunista (pulada com --no-host): login do host via `gh api user`, `glab api user` ou usuário
     embutido na URL https do remoto. Nunca lê credenciais; senhas/tokens da URL são descartados.
     Sinal presente => evidence 'host-verified'; ausente => 'git-only'.
  5. policy.requireSignedCommits sem commit.gpgsign=true => aviso UNSIGNED_COMMITS_REQUIRED.

Status: IDENTIFIED_APPROVED | IDENTIFIED_PENDING | REJECTED | REVOKED | UNKNOWN | NO_IDENTITY |
MISMATCH | NO_CONFIG | SOLO. `SOLO`: config sem `groupMode: true` — a pessoa é só identificada pelo git (nome e
e-mail), sem roster, sem registro e sem aprovação; `mode` edit. `mode`: edit (aprovado), edit-limited (pendente: rascunho/beta/previews, sem
promover), consult (os demais). `--register` só age em UNKNOWN: acrescenta o membro como `pending`
(roles ['contributor'], profile 'product'); e-mail já existente nunca é duplicado.

Papel de promotor: vem de `roles` (protolib.is_promoter); `policy.promoters` não amplia o papel.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protolib as pl  # noqa: E402

HOST_TIMEOUT = 8
LOGIN_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$')
# Nomes de usuário que são marcadores de autenticação, não pessoas.
PLACEHOLDER_USERS = {'x-access-token', 'oauth2', 'git', 'token', 'x-token-auth', 'private-token'}
TOKEN_LIKE_RE = re.compile(r'^(gh[pousr]_|github_pat_|glpat-|glptt-|xox)|^[A-Fa-f0-9]{32,}$')

MODES = {
    'IDENTIFIED_APPROVED': 'edit',
    'IDENTIFIED_PENDING': 'edit-limited',
    'NO_CONFIG': 'edit',
    'SOLO': 'edit',
}


def parse_remote(url):
    """Devolve {'scheme','host','user'} de uma URL de remoto; caminhos locais => host None."""
    url = (url or '').strip()
    if not url:
        return {'scheme': None, 'host': None, 'user': None}
    if '://' not in url:
        m = re.match(r'^(?:[\w.-]+@)?([\w.-]+):(?!//)(.+)$', url)
        if m and not url.startswith(('/', '.')):
            return {'scheme': 'ssh', 'host': m.group(1).lower(), 'user': None}
        return {'scheme': None, 'host': None, 'user': None}
    p = urlparse(url)
    user = unquote(p.username) if p.username else None
    return {'scheme': p.scheme, 'host': (p.hostname or '').lower() or None, 'user': user}


def run_tool(cmd):
    """Executa uma CLI de host com timeout curto; falha de qualquer tipo => None. Stderr nunca é exposto."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=HOST_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


def valid_login(text):
    text = (text or '').strip()
    return text if LOGIN_RE.match(text) else None


def login_from_gh(host):
    if not shutil.which('gh'):
        return None
    if run_tool(['gh', 'auth', 'status', '--hostname', host]) is None:
        return None
    return valid_login(run_tool(['gh', 'api', 'user', '--hostname', host, '--jq', '.login']))


def login_from_glab(host):
    if not shutil.which('glab'):
        return None
    out = run_tool(['glab', 'api', 'user', '--hostname', host])
    if out is None:
        return None
    try:
        return valid_login(json.loads(out).get('username'))
    except (ValueError, AttributeError):
        return None


def login_from_url(info):
    if info['scheme'] not in ('http', 'https'):
        return None
    user = info['user']
    if not user or user.lower() in PLACEHOLDER_USERS or TOKEN_LIKE_RE.match(user):
        return None
    return valid_login(user)


def detect_host_login(repo, remote):
    raw = pl.git(repo, 'config', '--get', f'remote.{remote}.url')
    if raw.returncode != 0:
        return None
    info = parse_remote(raw.stdout.strip())
    host = info['host']
    if not host:
        return None
    login = None
    if 'gitlab' not in host:
        login = login_from_gh(host)
    if not login and 'github' not in host:
        login = login_from_glab(host)
    return login or login_from_url(info)


def git_config(repo, key):
    r = pl.git(repo, 'config', '--get', key)
    return r.stdout.strip() if r.returncode == 0 else ''


def days_since(iso):
    try:
        then = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return 0
    return max(0, (datetime.now(timezone.utc) - then).days)


def pending_list(cfg):
    expiry = cfg.get('policy', {}).get('pendingExpiryDays', 7)
    out = []
    for m in cfg.get('members', []):
        if m.get('status') != 'pending':
            continue
        days = days_since(m.get('registeredAt'))
        out.append({'name': m.get('name'), 'email': m.get('email'), 'registeredAt': m.get('registeredAt'),
                    'daysPending': days, 'expired': days > expiry,
                    'identityEvidence': m.get('identityEvidence')})
    return out


def classify(member, detected_login):
    if member is None:
        return 'UNKNOWN'
    status = member.get('status')
    if status == 'rejected':
        return 'REJECTED'
    if status == 'revoked':
        return 'REVOKED'
    expected = member.get('hostLogin')
    if expected and detected_login and expected.lower() != detected_login.lower():
        return 'MISMATCH'
    return 'IDENTIFIED_APPROVED' if status == 'approved' else 'IDENTIFIED_PENDING'


def roster_source(repo, cfg):
    """Roster mais fresco: o config da beta no remoto (quem acabou de clonar pode estar numa cópia velha)."""
    remote = cfg.get('remote', 'origin')
    beta = cfg.get('branches', {}).get('beta')
    if not beta:
        return cfg, 'local'
    r = pl.git(repo, 'show', f'refs/remotes/{remote}/{beta}:{pl.CONFIG_NAME}')
    if r.returncode != 0:
        return cfg, 'local'
    try:
        return json.loads(r.stdout), f'{remote}/{beta}'
    except json.JSONDecodeError:
        return cfg, 'local'


def find_in_rosters(email, *cfgs):
    for c in cfgs:
        m = pl.find_member(c, email)
        if m:
            return m
    return None


def register_member(repo, cfg, name, email, evidence, login):
    head = pl.git(repo, 'rev-parse', '--verify', '-q', 'HEAD')
    sha = head.stdout.strip() if head.returncode == 0 else None
    now = pl.now_iso()
    member = {'name': name, 'email': email, 'roles': ['contributor'], 'profile': 'product',
              'status': 'pending', 'registeredAt': now, 'statusChangedAt': now,
              'statusChangedAtCommit': sha,
              'statusHistory': [{'status': 'pending', 'at': now, 'commit': sha, 'by': 'self'}],
              'identityEvidence': evidence}
    if login:
        member['hostLogin'] = login
    cfg.setdefault('members', []).append(member)
    pl.save_config(repo, cfg)
    return member


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--name')
    ap.add_argument('--email')
    ap.add_argument('--register', action='store_true')
    ap.add_argument('--set-local-git-identity', action='store_true')
    ap.add_argument('--no-host', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if pl.git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        pl.emit(False, 'NOT_A_REPO', problems=[pl.problem('NOT_A_REPO', f'"{args.repo}" não é um repositório git.')])
        return 2

    cfg, cfg_err = pl.load_config(repo)
    data = {'name': None, 'email': None, 'evidence': 'unverified', 'detectedHostLogin': None, 'roles': [],
            'profile': None, 'mode': 'consult', 'canPromote': False, 'canDecideMembers': False}
    problems = []
    if cfg_err:
        problems.append(pl.problem('CONFIG_INVALID', cfg_err))
        return pl.emit(False, 'NO_CONFIG', data, problems)

    name = (args.name or git_config(repo, 'user.name')).strip()
    email = pl.norm_email(args.email or git_config(repo, 'user.email'))
    data['name'], data['email'] = name or None, email or None

    if name and email and args.set_local_git_identity:
        pl.git(repo, 'config', '--local', 'user.name', name, check=True)
        pl.git(repo, 'config', '--local', 'user.email', email, check=True)
        data['localIdentitySet'] = True

    if cfg is None:
        data['mode'] = MODES['NO_CONFIG']
        return pl.emit(True, 'NO_CONFIG', data)

    if not (name and email):
        missing = [k for k, v in (('nome', name), ('e-mail', email)) if not v]
        problems.append(pl.problem('NO_IDENTITY', 'Identidade git ausente: ' + ' e '.join(missing) + '.'))
        questions = ['Qual é o seu nome e o seu e-mail para registrar a autoria (git user.name / user.email)?']
        return pl.emit(False, 'NO_IDENTITY', data, problems, questions)

    if cfg.get('groupMode') is not True:
        data['mode'] = MODES['SOLO']
        return pl.emit(True, 'SOLO', data)

    login = None if args.no_host else detect_host_login(repo, cfg.get('remote', 'origin'))
    data['detectedHostLogin'] = login
    data['evidence'] = 'host-verified' if login else 'git-only'

    roster_cfg, data['rosterSource'] = roster_source(repo, cfg)
    member = find_in_rosters(email, roster_cfg, cfg)
    status = classify(member, login)

    registered = False
    if args.register and status == 'UNKNOWN':
        member = register_member(repo, cfg, name, email, data['evidence'], login)
        status, registered = 'IDENTIFIED_PENDING', True
    data['registered'] = registered

    data['mode'] = MODES.get(status, 'consult')
    if member:
        data['memberStatus'] = member.get('status')
        data['roles'] = list(member.get('roles', []))
        data['profile'] = member.get('profile')
        promoter = pl.is_promoter(member) and status == 'IDENTIFIED_APPROVED'
        data['canPromote'] = data['canDecideMembers'] = promoter
        if promoter:
            data['pendingMembers'] = pending_list(roster_cfg)

    questions = []
    if status == 'UNKNOWN':
        problems.append(pl.problem('UNKNOWN_MEMBER', f'{email} não consta no roster do protótipo.'))
        questions.append('Registrar este e-mail como membro pendente (--register)? Um promotor precisa aprovar depois.')
    elif status == 'REJECTED':
        problems.append(pl.problem('MEMBER_REJECTED', 'Seu cadastro foi rejeitado: apenas consulta é permitida.'))
    elif status == 'REVOKED':
        problems.append(pl.problem('MEMBER_REVOKED', 'Seu acesso foi revogado: apenas consulta é permitida.'))
    elif status == 'MISMATCH':
        problems.append(pl.problem(
            'HOST_LOGIN_MISMATCH',
            f'O login detectado no host ({login}) difere do registrado para este e-mail; '
            'apenas consulta até um promotor confirmar a identidade.'))
    elif status == 'IDENTIFIED_PENDING':
        expiry = cfg.get('policy', {}).get('pendingExpiryDays', 7)
        if days_since(member.get('registeredAt')) > expiry:
            problems.append(pl.problem(
                'PENDING_EXPIRED', f'Cadastro pendente há mais de {expiry} dias: peça a um promotor para decidir.'))

    if cfg.get('policy', {}).get('requireSignedCommits') and git_config(repo, 'commit.gpgsign').lower() != 'true':
        problems.append(pl.problem(
            'UNSIGNED_COMMITS_REQUIRED',
            'A política exige commits assinados, mas commit.gpgsign não está ativo neste repositório.'))

    ok = status in ('IDENTIFIED_APPROVED', 'IDENTIFIED_PENDING')
    return pl.emit(ok, status, data, problems, questions)


if __name__ == '__main__':
    sys.exit(main())
