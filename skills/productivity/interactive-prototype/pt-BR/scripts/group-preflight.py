#!/usr/bin/env python3
"""Confere se o repositório está pronto para o modo trabalho em grupo (repo, branches e acesso de push).

Só stdlib. Não altera o remoto, exceto com `--create-beta` (cria a branch beta a partir da oficial,
sem force). Usa `git ls-remote`, `git fetch` das branches oficial/beta e `git push --dry-run`.
Saída: uma linha por checagem (OK / FALHA / INCONCLUSIVO / ANOMALIA) e exit 0 só se tudo passar.

  python3 group-preflight.py [--repo .] [--enable] [--force-check] [--json] [--create-beta]
  --enable       grava "groupMode": true em prototype.config.json se tudo passar (preserva as outras chaves)
  --force-check  roda as checagens mesmo com groupMode=false/ausente (para testar antes de ativar)
  --json         envelope JSON de protolib no stdout (em vez das linhas humanas)
  --create-beta  se a beta não existir no remoto, cria a partir da oficial e envia (só com a flag)

Config v1 (`sharedBranch`): uma só branch compartilhada. Config v2 (`branches.official/beta`): checa
também a beta, a proteção de branch no servidor (via `gh api`, melhor esforço; sem gh/permissão =>
INCONCLUSIVO, sem bloquear) e a ANOMALIA na oficial (commits posteriores ao último com o trailer
Prototype-Promotion; sem nenhum trailer, nada a reportar).
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protolib as pl  # noqa: E402

MAX_ANOMALIES_LISTED = 20


def git(repo, *a, timeout=30):
    return pl.git(repo, *a, timeout=timeout)


def remote_host_path(url):
    """(host, owner, repo) de uma URL https/ssh/scp-like; caminho local => (None, None, None)."""
    url = (url or '').strip()
    host = path = None
    if '://' in url:
        p = urlparse(url)
        host, path = (p.hostname or '').lower() or None, p.path
    else:
        m = re.match(r'^(?:[\w.-]+@)?([\w.-]+):(?!//)(.+)$', url)
        if m and not url.startswith(('/', '.')):
            host, path = m.group(1).lower(), m.group(2)
    if not host or not path:
        return None, None, None
    parts = [x for x in path.strip('/').removesuffix('.git').split('/') if x]
    if len(parts) < 2:
        return host, None, None
    return host, parts[0], '/'.join(parts[1:])


class Checks:
    def __init__(self):
        self.items = []

    def add(self, status, code, message, blocking=True):
        self.items.append({'status': status, 'code': code, 'message': message, 'blocking': blocking})

    @property
    def ok(self):
        return all(i['status'] == 'OK' or not i['blocking'] for i in self.items)

    def human(self):
        return '\n'.join(f"{i['status']:<13} {i['message']}" for i in self.items)

    def problems(self):
        return [pl.problem(i['code'], i['message']) for i in self.items if i['status'] != 'OK']


def check_protection(repo, remote, branch, checks):
    url = git(repo, 'config', '--get', f'remote.{remote}.url').stdout.strip()
    advice = f'peça ao responsável pelo repositório para proteger a branch "{branch}" (sem force-push nem exclusão)'
    host, owner, name = remote_host_path(url)
    if not host or 'github' not in host or not owner:
        checks.add('INCONCLUSIVO', 'PROTECTION_UNKNOWN',
                   f'proteção de "{branch}" no servidor não verificável por este remoto — {advice}', blocking=False)
        return
    if not shutil.which('gh'):
        checks.add('INCONCLUSIVO', 'PROTECTION_UNKNOWN',
                   f'proteção de "{branch}" não verificada (gh não instalado) — {advice}', blocking=False)
        return
    try:
        r = subprocess.run(['gh', 'api', f'repos/{owner}/{name}/branches/{branch}/protection',
                            '--hostname', host], capture_output=True, text=True, timeout=20)
    except (subprocess.TimeoutExpired, OSError):
        checks.add('INCONCLUSIVO', 'PROTECTION_UNKNOWN',
                   f'proteção de "{branch}" não verificada (gh expirou) — {advice}', blocking=False)
        return
    if r.returncode == 0:
        checks.add('OK', 'PROTECTION_OK', f'branch "{branch}" protegida no servidor')
    elif 'not protected' in (r.stderr + r.stdout).lower():
        # Aviso, não bloqueio: proteção é recomendação (pode nem existir no plano gratuito de repositório privado).
        checks.add('AVISO', 'BRANCH_UNPROTECTED', f'branch "{branch}" sem proteção no servidor — {advice}', blocking=False)
    else:
        checks.add('INCONCLUSIVO', 'PROTECTION_UNKNOWN',
                   f'proteção de "{branch}" não verificada (sem permissão ou recurso indisponível) — {advice}',
                   blocking=False)


def find_anomalies(repo, remote, official):
    """Commits em <remote>/<official> posteriores ao último com Prototype-Promotion; None se nenhum trailer."""
    ref = f'refs/remotes/{remote}/{official}'
    if git(repo, 'rev-parse', '--verify', '-q', ref).returncode != 0:
        return None
    log = git(repo, 'log', ref, f'--grep=^{pl.T_PROMOTION}:', '--format=%H%x1f%B%x1e')
    last = None
    for rec in log.stdout.split('\x1e'):
        sha, _, body = rec.strip().partition('\x1f')
        if sha and pl.T_PROMOTION in pl.parse_trailers(body):
            last = sha
            break
    if not last:
        return None
    after = git(repo, 'log', f'{last}..{ref}', '--format=%h%x1f%an%x1f%s')
    out = []
    for line in after.stdout.splitlines():
        short, author, subject = (line.split('\x1f') + ['', ''])[:3]
        out.append({'sha': short, 'author': author, 'subject': subject})
    return out


def dry_run_push(repo, remote, branch, checks):
    head = git(repo, 'rev-parse', '--verify', '-q', 'HEAD')
    if head.returncode != 0:
        checks.add('INCONCLUSIVO', 'NO_LOCAL_COMMITS',
                   'sem commits locais — não dá para testar o envio (push --dry-run)')
        return
    try:
        push = git(repo, 'push', '--dry-run', remote, f'HEAD:refs/heads/{branch}', timeout=60)
    except subprocess.TimeoutExpired:
        checks.add('INCONCLUSIVO', 'PUSH_TIMEOUT', 'push --dry-run expirou — acesso de escrita não confirmado')
        return
    if push.returncode == 0:
        checks.add('OK', 'PUSH_OK', f'acesso de push conferido em "{branch}" (push --dry-run aceito)')
    elif 'non-fast-forward' in push.stderr or 'rejected' in push.stderr:
        checks.add('OK', 'PUSH_OK',
                   f'acesso de push conferido em "{branch}" (rejeição só por histórico divergente — integre antes de enviar)')
    else:
        reason = (push.stderr.strip().splitlines() or ['erro desconhecido'])[-1]
        checks.add('FALHA', 'PUSH_DENIED', f'sem acesso de push em "{branch}": {reason}')


def create_beta(repo, remote, official, beta, checks):
    f = git(repo, 'fetch', '-q', remote, f'+refs/heads/{official}:refs/remotes/{remote}/{official}', timeout=60)
    if f.returncode != 0:
        checks.add('FALHA', 'BETA_CREATE_FAILED', f'não foi possível obter "{official}" do remoto para criar a beta')
        return
    push = git(repo, 'push', remote, f'refs/remotes/{remote}/{official}:refs/heads/{beta}', timeout=60)
    if push.returncode != 0:
        reason = (push.stderr.strip().splitlines() or ['erro desconhecido'])[-1]
        checks.add('FALHA', 'BETA_CREATE_FAILED', f'falha ao criar a branch "{beta}" no remoto: {reason}')
        return
    git(repo, 'fetch', '-q', remote, f'+refs/heads/{beta}:refs/remotes/{remote}/{beta}', timeout=60)
    if git(repo, 'rev-parse', '--verify', '-q', f'refs/heads/{beta}').returncode != 0:
        git(repo, 'branch', '--track', beta, f'{remote}/{beta}')
    checks.add('OK', 'BETA_CREATED', f'branch "{beta}" criada a partir de "{official}" e enviada ao remoto')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--enable', action='store_true')
    ap.add_argument('--force-check', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--create-beta', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    checks = Checks()
    anomalies, data = [], {'enabled': False}

    def finish():
        ok = checks.ok
        if args.json:
            status = 'READY' if ok else 'NOT_READY'
            data['checks'] = [{k: i[k] for k in ('status', 'code', 'message')} for i in checks.items]
            data['anomalies'] = anomalies
            return pl.emit(ok, status, data, checks.problems())
        print(checks.human())
        if data['enabled']:
            print('\n✓ groupMode ativado em prototype.config.json')
        elif args.enable:
            print('\n✗ groupMode NÃO ativado: resolva as pendências acima e rode de novo.')
        return 0 if ok else 1

    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        checks.add('FALHA', 'NOT_A_REPO', 'não é um repositório git')
        return finish()
    checks.add('OK', 'REPO_OK', 'repositório git')

    cfg, cfg_err = pl.load_config(repo)
    cfg = cfg or {}
    if cfg_err:
        checks.add('FALHA', 'CONFIG_INVALID', cfg_err)
        return finish()
    if not pl.config_path(repo).exists() and not args.force_check:
        checks.add('FALHA', 'CONFIG_MISSING', 'prototype.config.json ausente (use --force-check para testar mesmo assim)')
    if not cfg.get('groupMode') and not (args.force_check or args.enable or args.create_beta):
        msg = 'Modo grupo desligado (groupMode != true) — nada a conferir. Use --enable para ativar.'
        if args.json:
            return pl.emit(True, 'DISABLED', {'enabled': False, 'message': msg, 'checks': [], 'anomalies': []})
        print(msg)
        return 0

    is_v2 = isinstance(cfg.get('branches'), dict)
    remote = cfg.get('remote', 'origin')
    official = cfg['branches'].get('official', 'main') if is_v2 else cfg.get('sharedBranch', 'main')
    beta = cfg['branches'].get('beta', 'beta') if is_v2 else None
    data.update({'configVersion': 2 if is_v2 else 1, 'remote': remote, 'official': official, 'beta': beta})
    shared_label = 'oficial' if is_v2 else 'compartilhada'

    url = git(repo, 'remote', 'get-url', remote)
    if url.returncode != 0:
        checks.add('FALHA', 'REMOTE_NOT_CONFIGURED', f'remoto "{remote}" não configurado (git remote add {remote} <url>)')
        return finish()
    checks.add('OK', 'REMOTE_CONFIGURED', f'remoto "{remote}" configurado')

    heads = [official] + ([beta] if beta else [])
    try:
        ls = git(repo, 'ls-remote', '--heads', remote, *heads, timeout=45)
    except subprocess.TimeoutExpired:
        ls = None
    if ls is None or ls.returncode != 0:
        checks.add('FALHA', 'REMOTE_UNREACHABLE',
                   'remoto inalcançável (sem rede ou sem permissão de leitura/autenticação)')
        return finish()
    checks.add('OK', 'REMOTE_REACHABLE', 'remoto alcançável')
    remote_heads = {line.split('\t')[1][len('refs/heads/'):] for line in ls.stdout.splitlines() if '\t' in line}

    if official not in remote_heads:
        checks.add('FALHA', 'OFFICIAL_BRANCH_MISSING',
                   f'branch {shared_label} "{official}" não existe no remoto (primeiro envio ainda não feito)')
        return finish()
    checks.add('OK', 'OFFICIAL_BRANCH_OK', f'branch {shared_label} "{official}" existe no remoto')

    if is_v2:
        if beta not in remote_heads:
            if args.create_beta:
                create_beta(repo, remote, official, beta, checks)
                if checks.items[-1]['status'] == 'OK':
                    remote_heads.add(beta)
            else:
                checks.add('FALHA', 'BETA_BRANCH_MISSING',
                           f'branch beta "{beta}" não existe no remoto — rode de novo com --create-beta '
                           f'para criá-la a partir de "{official}"')
        else:
            checks.add('OK', 'BETA_BRANCH_OK', f'branch beta "{beta}" existe no remoto')

    if is_v2 and beta in remote_heads:
        dry_run_push(repo, remote, beta, checks)
    elif not is_v2:
        dry_run_push(repo, remote, official, checks)

    if is_v2:
        for b in (official, beta):
            if b in remote_heads:
                check_protection(repo, remote, b, checks)
        fetch = git(repo, 'fetch', '-q', remote, f'+refs/heads/{official}:refs/remotes/{remote}/{official}', timeout=60)
        if fetch.returncode == 0:
            found = find_anomalies(repo, remote, official)
            if found:
                anomalies.extend(found)
                listed = '; '.join(f"{a['sha']} ({a['author']}): {a['subject']}"
                                   for a in found[:MAX_ANOMALIES_LISTED])
                more = f' (+{len(found) - MAX_ANOMALIES_LISTED} omitidos)' if len(found) > MAX_ANOMALIES_LISTED else ''
                checks.add('ANOMALIA', 'OFFICIAL_ANOMALY',
                           f'{len(found)} commit(s) em "{official}" posteriores à última promoção — a oficial só '
                           f'deve avançar por promoção: {listed}{more}')
            else:
                checks.add('OK', 'OFFICIAL_CLEAN', f'oficial "{official}" sem commits fora de promoção')
        else:
            checks.add('INCONCLUSIVO', 'ANOMALY_CHECK_SKIPPED',
                       f'não foi possível obter "{official}" para procurar anomalias', blocking=False)

    if checks.ok and args.enable:
        cfg.update({'groupMode': True, 'remote': remote})
        if not is_v2:
            cfg['sharedBranch'] = official
        pl.save_config(repo, cfg)
        data['enabled'] = True
    return finish()


if __name__ == '__main__':
    sys.exit(main())
