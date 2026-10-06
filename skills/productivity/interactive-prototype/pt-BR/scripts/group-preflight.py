#!/usr/bin/env python3
"""Confere se o repositório está pronto para o modo trabalho em grupo (repo + acesso de push).

Só stdlib. Não altera o remoto: usa `git ls-remote` e `git push --dry-run`.
Saída: uma linha por checagem (OK / FALHA / INCONCLUSIVO) e exit 0 só se tudo passar.

  python3 group-preflight.py [--repo .] [--enable] [--force-check]
  --enable       grava "groupMode": true em prototype.config.json se tudo passar
  --force-check  roda as checagens mesmo com groupMode=false/ausente (para testar antes de ativar)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def git(repo, *a, timeout=30):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, timeout=timeout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--enable', action='store_true')
    ap.add_argument('--force-check', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    cfg_path = repo / 'prototype.config.json'
    results, ok_all = [], True

    def report(status, msg):
        nonlocal ok_all
        results.append(f'{status:<13} {msg}')
        if status != 'OK':
            ok_all = False

    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        report('FALHA', 'não é um repositório git')
        print('\n'.join(results)); sys.exit(1)
    report('OK', 'repositório git')

    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            report('FALHA', f'prototype.config.json inválido: {e}')
    elif not args.force_check:
        report('FALHA', 'prototype.config.json ausente (use --force-check para testar mesmo assim)')
    if not cfg.get('groupMode') and not args.force_check and not args.enable:
        print('Modo grupo desligado (groupMode != true) — nada a conferir. Use --enable para ativar.')
        sys.exit(0)

    remote = cfg.get('remote', 'origin')
    branch = cfg.get('sharedBranch', 'main')

    url = git(repo, 'remote', 'get-url', remote)
    if url.returncode != 0:
        report('FALHA', f'remoto "{remote}" não configurado (git remote add {remote} <url>)')
    else:
        report('OK', f'remoto "{remote}" configurado')
        try:
            ls = git(repo, 'ls-remote', '--heads', remote, branch, timeout=45)
        except subprocess.TimeoutExpired:
            ls = None
        if ls is None or ls.returncode != 0:
            report('FALHA', 'remoto inalcançável (sem rede ou sem permissão de leitura/autenticação)')
        else:
            report('OK', 'remoto alcançável')
            if not ls.stdout.strip():
                report('FALHA', f'branch compartilhada "{branch}" não existe no remoto (primeiro envio ainda não feito)')
            else:
                report('OK', f'branch compartilhada "{branch}" existe no remoto')
                head = git(repo, 'rev-parse', '--verify', '-q', 'HEAD')
                if head.returncode != 0:
                    report('INCONCLUSIVO', 'sem commits locais — não dá para testar o envio (push --dry-run)')
                else:
                    try:
                        push = git(repo, 'push', '--dry-run', remote, f'HEAD:refs/heads/{branch}', timeout=60)
                    except subprocess.TimeoutExpired:
                        push = None
                    if push is None:
                        report('INCONCLUSIVO', 'push --dry-run expirou — acesso de escrita não confirmado')
                    elif push.returncode == 0:
                        report('OK', 'acesso de push conferido (push --dry-run aceito)')
                    elif 'non-fast-forward' in push.stderr or 'rejected' in push.stderr:
                        report('OK', 'acesso de push conferido (rejeição só por histórico divergente — integre antes de enviar)')
                    else:
                        report('FALHA', 'sem acesso de push: ' + (push.stderr.strip().splitlines() or ['erro desconhecido'])[-1])

    print('\n'.join(results))
    if ok_all and args.enable:
        cfg.update({'groupMode': True, 'sharedBranch': branch, 'remote': remote})
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('\n✓ groupMode ativado em prototype.config.json')
    elif args.enable:
        print('\n✗ groupMode NÃO ativado: resolva as pendências acima e rode de novo.')
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
