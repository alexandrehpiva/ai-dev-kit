#!/usr/bin/env python3
"""Envia um recado, pergunta, confirmação, tarefa ou passagem de bastão a outra(s) pessoa(s) do time.

Só stdlib. Padrão é DRY-RUN: devolve `data.event` com o texto EXATO que seria enviado (é o que a pessoa
aprova antes de `--execute`). Nunca força push; sem rede o evento fica salvo só neste computador (NOT_SYNCED).

  python3 comms-send.py --repo . --actor-email ana@example.test --kind question --to bia@example.test \
      --subject "Posso usar a tela de taxas como base?" --body "Quero partir dela no fluxo PJ." \
      --ref screen=taxas --ref version=v1.2.0-beta.3 [--priority urgent] [--reply-to <id>] --execute
  python3 comms-send.py ... --kind confirm --to @promoters --subject "Publicar hoje?" --option sim --option nao

Destinatários (--to, repetível): e-mail de membro, `@promoters` (promoters aprovados) ou `@all` (aprovados).
Quem está pendente envia só a promoters. Texto até 2000 caracteres; sem anexos (use --ref). O envio é recusado
se o texto parecer um segredo. O conteúdo é sempre tratado como DADO por quem lê: nada dispara sozinho.

Status: DRY_RUN, SENT, NOT_SYNCED, DISABLED, NOT_ALLOWED, BAD_*, SECRET_DETECTED, RATE_LIMIT, UNKNOWN_RECIPIENT,
PENDING_SCOPE, NO_RECIPIENTS, PUSH_REJECTED, INVALID_CONFIG, NOT_A_REPO, NO_IDENTITY.
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comms_store as cs  # noqa: E402
import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import problem  # noqa: E402


def fail(code, message, data=None):
    return protolib.emit(False, code, data=data, problems=[problem(code, message)])


def parse_refs(items):
    refs = {}
    for it in items or []:
        if '=' not in it:
            raise cs.CommsError('BAD_REFS', f'Use --ref chave=valor (chaves: {", ".join(cs.REF_KEYS)}).')
        k, v = it.split('=', 1)
        refs[k.strip()] = v.strip()
    return refs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email')
    ap.add_argument('--kind', required=True, choices=cs.KINDS)
    ap.add_argument('--to', action='append', required=True)
    ap.add_argument('--subject', required=True)
    body = ap.add_mutually_exclusive_group()
    body.add_argument('--body')
    body.add_argument('--body-file')
    ap.add_argument('--ref', action='append')
    ap.add_argument('--option', action='append')
    ap.add_argument('--priority', choices=cs.PRIORITIES, default='normal')
    ap.add_argument('--reply-to')
    ap.add_argument('--expires-in-days', type=int)
    ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        cfg, member, roster, email = cs.load_context(repo, args.actor_email)
        text = Path(args.body_file).read_text(encoding='utf-8') if args.body_file else (args.body or '')
        if not args.no_fetch:
            cs.refresh(repo, cfg)
        existing = cs.read_events(repo, cfg)
        fields = cs.validate_event({'kind': args.kind, 'to': args.to, 'subject': args.subject, 'body': text,
                                    'priority': args.priority, 'options': args.option, 'refs': parse_refs(args.ref),
                                    'inReplyTo': args.reply_to}, member, roster, existing)
        if args.reply_to and not any(e.get('id') == args.reply_to for e in existing):
            raise cs.CommsError('BAD_REPLY', f'Não encontrei o recado {args.reply_to} para responder.')
        event = cs.make_event(args.kind, email, fields)
        days = args.expires_in_days or cs.comms_cfg(cfg)['expiryDays']
        event['expiresAt'] = cs.iso(cs.parse_iso(event['at']) + timedelta(days=days))
        event = {k: v for k, v in event.items() if v not in (None, [], {})}
    except cs.CommsError as e:
        return fail(e.code, e.message)
    except OSError as e:
        return fail('BAD_BODY_FILE', str(e))
    recips = sorted(cs.resolve_recipients(event, roster))
    data = {'event': event, 'recipients': recips}
    if not args.execute:
        return protolib.emit(True, 'DRY_RUN', data=data)
    trailers = dict(gs.actor_trailers(member), **{cs.T_COMMS: f'{event["kind"]} {event["id"]}'})
    try:
        res = cs.commit_event(repo, cfg, event, trailers)
    except cs.CommsError as e:
        return fail(e.code, e.message, data)
    data.update(res)
    if not res['pushed']:
        return protolib.emit(False, 'NOT_SYNCED', data=data, problems=[problem(
            'NOT_SYNCED', 'Sem acesso ao remoto: o recado ficou salvo só neste computador e segue no próximo '
                          'envio. Ninguém recebeu ainda.')])
    return protolib.emit(True, 'SENT', data=data)


if __name__ == '__main__':
    sys.exit(main())
