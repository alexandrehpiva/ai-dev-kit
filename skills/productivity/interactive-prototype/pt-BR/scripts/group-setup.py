#!/usr/bin/env python3
"""Configuração inicial do modo grupo em protótipo já no formato v2 (primeiro promoter e política).

Só stdlib. Não faz git e não liga `groupMode` (isso é do group-preflight.py --enable).
Idempotente: se o e-mail já está no roster, nada é duplicado.

  python3 group-setup.py --repo <pasta> --actor-name N --actor-email E \
      [--promoters-policy all-members|listed] [--docs-auto-maintain true|false] \
      [--actor-profile product|technical] [--actor-evidence host-verified|git-only|unverified]

Quem roda o setup entra como membro `approved` com papéis promoter+contributor
(statusHistory by='setup'). As respostas de política vêm da pergunta obrigatória do setup.
Para protótipos em formato antigo use migrate.py (que também registra o ator).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protolib as pl  # noqa: E402


def head_sha(repo):
    r = pl.git(repo, 'rev-parse', '--verify', '-q', 'HEAD')
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-name', required=True)
    ap.add_argument('--actor-email', required=True)
    ap.add_argument('--actor-profile', choices=pl.PROFILES, default='product')
    ap.add_argument('--actor-evidence', choices=pl.EVIDENCE, default='unverified')
    ap.add_argument('--promoters-policy', choices=('all-members', 'listed'), default=None)
    ap.add_argument('--docs-auto-maintain', choices=('true', 'false'), default=None)
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    cfg, err = pl.load_config(repo)
    if err:
        sys.exit(pl.emit(False, 'INVALID_CONFIG', problems=[pl.problem('INVALID_CONFIG', err)]))
    if cfg is None or 'skill' not in cfg:
        sys.exit(pl.emit(False, 'NEEDS_MIGRATION', problems=[pl.problem(
            'NEEDS_MIGRATION', 'O protótipo ainda não está no formato atual: rode migrate.py antes.')]))

    changed = []
    if args.promoters_policy is not None:
        cfg.setdefault('policy', {})['promoters'] = args.promoters_policy
        changed.append('policy.promoters')
    if args.docs_auto_maintain is not None:
        cfg.setdefault('docs', {})['autoMaintain'] = args.docs_auto_maintain == 'true'
        changed.append('docs.autoMaintain')

    email = pl.norm_email(args.actor_email)
    if pl.find_member(cfg, email) is None:
        now = pl.now_iso()
        cfg.setdefault('members', []).append({
            'name': args.actor_name.strip(), 'email': email, 'roles': ['promoter', 'contributor'],
            'profile': args.actor_profile, 'status': 'approved', 'registeredAt': now,
            'statusChangedAt': now, 'statusChangedAtCommit': head_sha(repo),
            'statusHistory': [{'status': 'approved', 'at': now, 'commit': head_sha(repo), 'by': 'setup'}],
            'identityEvidence': args.actor_evidence, 'decidedBy': email, 'decidedAt': now,
        })
        changed.append('members')

    validator = Path(__file__).resolve().parent / 'config-validate.py'
    original = pl.config_path(repo).read_text(encoding='utf-8')
    pl.save_config(repo, cfg)
    r = subprocess.run([sys.executable, str(validator), '--repo', str(repo)], capture_output=True, text=True)
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        env = {'ok': False, 'problems': [pl.problem('VALIDATION_FAILED', r.stderr.strip())]}
    if not env.get('ok'):
        pl.config_path(repo).write_text(original, encoding='utf-8')  # nunca deixar config inválido no disco
        sys.exit(pl.emit(False, 'INVALID_CONFIG', problems=env.get('problems', [])))
    sys.exit(pl.emit(True, 'SETUP_DONE' if changed else 'NOTHING_TO_DO', data={'changed': changed}))


if __name__ == '__main__':
    main()
