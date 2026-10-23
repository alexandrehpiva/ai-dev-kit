#!/usr/bin/env python3
"""Responde a um recado: marcar como lido, responder, aceitar, recusar, concluir ou cancelar.

Só stdlib. Padrão é DRY-RUN (mostra o recibo exato; é o que a pessoa aprova antes de `--execute`).

  python3 comms-ack.py --repo . --actor-email bia@example.test --target <id> --action read --execute
  python3 comms-ack.py ... --action answer --body "Pode usar, sim." --execute
  python3 comms-ack.py ... --action answer --choice sim --execute        # confirmação: uma das opções
  python3 comms-ack.py ... --action accept|decline|done                  # tarefas
  python3 comms-ack.py ... --action cancel                               # só quem enviou
  python3 comms-ack.py ... --target <id-da-resposta> --action read       # o autor marca a resposta como vista

Ações por tipo: message/handoff → read; question → read, answer; confirm → read, answer (com --choice);
task → read, accept, decline, done. "Lida" significa: o agente mostrou o recado à pessoa, e não que baixou o arquivo.

Status: DRY_RUN, ACKED, NOT_SYNCED, NOT_FOUND, NOT_VISIBLE, NOT_OWNER, BAD_ACTION, EMPTY_ANSWER, BAD_CHOICE,
SECRET_DETECTED, BODY_TOO_LONG, DISABLED, NOT_ALLOWED, PUSH_REJECTED, INVALID_CONFIG, NOT_A_REPO, NO_IDENTITY.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comms_store as cs  # noqa: E402
import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import problem  # noqa: E402


def fail(code, message, data=None):
    return protolib.emit(False, code, data=data, problems=[problem(code, message)])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email')
    ap.add_argument('--target', required=True)
    ap.add_argument('--action', required=True, choices=cs.RECEIPT_KINDS)
    ap.add_argument('--body')
    ap.add_argument('--choice')
    ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        cfg, member, roster, email = cs.load_context(repo, args.actor_email)
        if not args.no_fetch:
            cs.refresh(repo, cfg)
        events = cs.read_events(repo, cfg)
        by_id = {e['id']: e for e in events}
        target = by_id.get(args.target)
        if not target:
            raise cs.CommsError('NOT_FOUND', f'Não encontrei o recado {args.target}.')
        originals, _, _ = cs.index_events(events)
        fields = {k: v for k, v in (('body', (args.body or '').strip()), ('choice', args.choice)) if v}
        receipt = cs.validate_receipt(dict(fields, kind=args.action), member, target, roster, originals)
        receipt = cs.make_event(args.action, email, dict(fields, target=args.target))
    except cs.CommsError as e:
        return fail(e.code, e.message)
    data = {'receipt': receipt}
    if not args.execute:
        return protolib.emit(True, 'DRY_RUN', data=data)
    trailers = dict(gs.actor_trailers(member), **{cs.T_COMMS: f'{args.action} {receipt["id"]}'})
    try:
        res = cs.commit_event(repo, cfg, receipt, trailers)
    except cs.CommsError as e:
        return fail(e.code, e.message, data)
    data.update(res)
    if not res['pushed']:
        return protolib.emit(False, 'NOT_SYNCED', data=data, problems=[problem(
            'NOT_SYNCED', 'Sem acesso ao remoto: a resposta ficou salva só neste computador e segue no próximo envio.')])
    return protolib.emit(True, 'ACKED', data=data)


if __name__ == '__main__':
    sys.exit(main())
