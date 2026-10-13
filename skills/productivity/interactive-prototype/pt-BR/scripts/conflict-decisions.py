#!/usr/bin/env python3
"""Lista, na beta, as decisões de conflito que descartaram o trabalho de uma pessoa (modo grupo v2).

Só leitura, só stdlib. Procura o trailer `Prototype-Conflict-Decision` nos commits da beta (ref remota quando
existir) e devolve as decisões em que a pessoa informada está entre os `dropped`: em `mine`/`theirs`, todos os
autores do lado descartado que tocaram o arquivo (inclusive quem teve só mudanças mantidas); em `combined`, todos
os autores menos quem decidiu.

  python3 conflict-decisions.py --repo . --actor-email bia@example.test [--since <commit-ou-data>]

Status: DECISIONS (há decisões que afetam a pessoa), NONE, INVALID_CONFIG, NOT_A_REPO.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import git, problem  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email', required=True)
    ap.add_argument('--since', help='commit (exclusivo) ou data (YYYY-MM-DD) a partir de onde olhar')
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        return protolib.emit(False, 'NOT_A_REPO', problems=[problem('NOT_A_REPO', f'{repo} não é um repositório git.')])
    cfg, err = protolib.load_config(repo)
    if err or not cfg:
        return protolib.emit(False, 'INVALID_CONFIG', problems=[problem('INVALID_CONFIG', err or 'sem config')])
    remote, beta = cfg.get('remote', 'origin'), cfg.get('branches', {}).get('beta', 'beta')
    ref = f'{remote}/{beta}' if gs.rev(repo, f'{remote}/{beta}') else beta
    rng = ref
    if args.since:
        rng = f'{args.since}..{ref}' if gs.rev(repo, args.since) else ref
    me = protolib.norm_email(args.actor_email)
    found = []
    for c in gs.commit_log(repo, rng, no_merges=False):
        raw = c['trailers'].get(protolib.T_CONFLICT)
        if not raw:
            continue
        for item in gs.parse_decision_trailer(raw):
            if me in [protolib.norm_email(x) for x in (item.get('dropped') or '').split(',')]:
                found.append({'commit': c['sha'], 'date': c['date'], 'keptBy': item.get('kept'),
                              'decidedBy': item.get('by'), 'what': item.get('what')})
    if args.since and not gs.rev(repo, args.since):
        found = [f for f in found if f['date'][:10] >= args.since]
    return protolib.emit(True, 'DECISIONS' if found else 'NONE', data={'decisions': found})


if __name__ == '__main__':
    sys.exit(main())
