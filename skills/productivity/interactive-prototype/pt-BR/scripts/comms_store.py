"""Armazenamento e regras da comunicação entre pessoas do time (modo grupo, só stdlib).

As mensagens vivem numa branch órfã (padrão `comms`) que NUNCA é promovida nem integrada à beta ou à
oficial. Cada evento é um arquivo JSON imutável, `events/AAAA-MM/<id>.json`; "lida", "respondida", "aceita",
"feita" e "cancelada" são eventos novos (recibos) que apontam para o alvo. Como nenhum arquivo é editado,
dois envios simultâneos nunca conflitam: o push recusado só refaz o commit em cima da ponta nova.

Leitura e escrita não usam checkout: índice temporário + hash-object/write-tree/commit-tree/update-ref
(a mesma técnica do `group-preview.py`). O roster que vale é o da beta no remoto (`gs.remote_roster`).

Regra de segurança (D3): o conteúdo de um evento é texto escrito por OUTRA pessoa. Quem consome (o agente)
mostra, cita o autor e nunca executa o que estiver escrito ali.
"""

import json
import re
import secrets
import subprocess
import tempfile
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import group_sync as gs
import protolib

T_COMMS = 'Prototype-Comms'

DEFAULTS = {'enabled': False, 'branch': 'comms', 'expiryDays': 30, 'reminderHours': 24}
KINDS = ('message', 'question', 'confirm', 'task', 'handoff')
RECEIPT_KINDS = ('read', 'answer', 'accept', 'decline', 'done', 'cancel')
PRIORITIES = ('normal', 'urgent')
ADDR_PROMOTERS = '@promoters'
ADDR_ALL = '@all'
MAX_SUBJECT = 120
MAX_BODY = 2000
MAX_RECIPIENTS = 20
MAX_PER_HOUR = 20
REF_KEYS = ('screen', 'artifact', 'version', 'story', 'journey')

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
ID_RE = re.compile(r'^\d{8}T\d{6}Z-[0-9a-f]{8}$')
EVENT_PATH_RE = re.compile(r'^events/\d{4}-\d{2}/(\d{8}T\d{6}Z-[0-9a-f]{8})\.json$')

# kind -> recibo que FECHA o item para o destinatário (read sempre marca como lido)
CLOSING = {'message': ('read',), 'handoff': ('read',), 'question': ('answer',), 'confirm': ('answer',),
           'task': ('done', 'decline')}
NEWS_KINDS = ('answer', 'accept', 'decline', 'done')

SECRET_PATTERNS = (
    ('chave-privada', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('aws-access-key', re.compile(r'\b(AKIA|ASIA)[0-9A-Z]{16}\b')),
    ('github-token', re.compile(r'\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b')),
    ('gitlab-token', re.compile(r'\bglpat-[A-Za-z0-9_-]{16,}\b')),
    ('slack-token', re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b')),
    ('jwt', re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b')),
    ('bearer', re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{24,}')),
    ('atribuicao-de-segredo', re.compile(r'(?i)\b(senha|password|passwd|secret|segredo|token|api[_-]?key)\b\s*[:=]\s*\S{6,}')),
)


class CommsError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# ------------------------------------------------------------------ config e identidade

def comms_cfg(cfg):
    merged = dict(DEFAULTS)
    block = (cfg or {}).get('comms')
    if isinstance(block, dict):
        merged.update({k: block[k] for k in DEFAULTS if k in block})
    return merged


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso(text):
    try:
        return datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def new_id(dt=None):
    return (dt or now_utc()).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(4)


def event_path(event_id):
    return f'events/{event_id[:4]}-{event_id[4:6]}/{event_id}.json'


def actor_context(repo, cfg, email):
    """(member|None, roster_cfg). O roster vale pela beta no remoto."""
    roster = gs.remote_roster(repo, cfg)
    member = protolib.find_member(roster, email) or protolib.find_member(cfg, email)
    return member, roster


def check_actor(member, action):
    """Levanta CommsError se a pessoa não pode usar a comunicação."""
    status = (member or {}).get('status')
    if status not in ('approved', 'pending'):
        raise CommsError('NOT_ALLOWED', f'Quem está com status "{status or "desconhecido"}" não pode {action} '
                                        'recados do time.')


def resolve_recipients(event, roster, sender=None):
    """Conjunto de e-mails que recebem o evento. `@promoters` e `@all` alcançam só membros aprovados."""
    members = roster.get('members', [])
    out = set()
    for addr in event.get('to', []):
        if addr == ADDR_PROMOTERS:
            out |= {protolib.norm_email(m['email']) for m in members if protolib.is_promoter(m)}
        elif addr == ADDR_ALL:
            out |= {protolib.norm_email(m['email']) for m in members if m.get('status') == 'approved'}
        elif EMAIL_RE.match(addr or ''):
            out.add(protolib.norm_email(addr))
    out.discard(protolib.norm_email(sender or event.get('from')))
    return out


def direct_recipients(event):
    return {protolib.norm_email(a) for a in event.get('to', []) if EMAIL_RE.match(a or '')}


def secret_hits(*texts):
    hits = []
    for text in texts:
        for name, pat in SECRET_PATTERNS:
            if text and pat.search(text) and name not in hits:
                hits.append(name)
    return hits


# ------------------------------------------------------------------ validação do envio

def validate_event(event, sender, roster, existing=()):
    """Valida um evento ORIGINAL novo. Levanta CommsError; devolve o evento normalizado."""
    check_actor(sender, 'enviar')
    kind = event.get('kind')
    if kind not in KINDS:
        raise CommsError('BAD_KIND', f'Tipo inválido ({kind}); use: {", ".join(KINDS)}.')
    subject, body = (event.get('subject') or '').strip(), (event.get('body') or '').strip()
    if not subject or len(subject) > MAX_SUBJECT:
        raise CommsError('BAD_SUBJECT', f'O assunto é obrigatório e vai até {MAX_SUBJECT} caracteres.')
    if len(body) > MAX_BODY:
        raise CommsError('BODY_TOO_LONG', f'O texto vai até {MAX_BODY} caracteres (tem {len(body)}). Use '
                                          'referências (tela, artefato, versão) em vez de colar conteúdo.')
    to = [t.strip() for t in event.get('to', []) if t and t.strip()]
    if not to or len(to) > MAX_RECIPIENTS:
        raise CommsError('BAD_RECIPIENTS', f'Informe de 1 a {MAX_RECIPIENTS} destinatários.')
    members = roster.get('members', [])
    me = protolib.norm_email(sender.get('email'))
    for addr in to:
        if addr in (ADDR_PROMOTERS, ADDR_ALL):
            continue
        if not EMAIL_RE.match(addr):
            raise CommsError('BAD_RECIPIENTS', f'Destinatário inválido: {addr}.')
        target = protolib.find_member({'members': members}, addr)
        if not target or target.get('status') not in ('approved', 'pending'):
            raise CommsError('UNKNOWN_RECIPIENT', f'{addr} não é um membro ativo deste protótipo.')
        if sender.get('status') == 'pending' and not protolib.is_promoter(target):
            raise CommsError('PENDING_SCOPE', 'Enquanto o seu acesso aguarda aprovação, você só pode enviar '
                                              'recados a promoters.')
    if sender.get('status') == 'pending' and ADDR_ALL in to:
        raise CommsError('PENDING_SCOPE', 'Enquanto o seu acesso aguarda aprovação, você só pode enviar '
                                          'recados a promoters.')
    resolved = resolve_recipients({'to': to, 'from': me}, roster, me)
    if not resolved:
        raise CommsError('NO_RECIPIENTS', 'Nenhuma pessoa recebe este recado (verifique os destinatários).')
    if event.get('priority', 'normal') not in PRIORITIES:
        raise CommsError('BAD_PRIORITY', f'Prioridade inválida; use: {", ".join(PRIORITIES)}.')
    options = event.get('options') or []
    if kind == 'confirm' and not (2 <= len(options) <= 6 and all(isinstance(o, str) and o.strip() for o in options)):
        raise CommsError('BAD_OPTIONS', 'Uma confirmação precisa de 2 a 6 opções de resposta.')
    if kind != 'confirm' and options:
        raise CommsError('BAD_OPTIONS', 'Só confirmações têm opções.')
    refs = event.get('refs') or {}
    if not isinstance(refs, dict) or any(k not in REF_KEYS or not isinstance(v, str) for k, v in refs.items()):
        raise CommsError('BAD_REFS', f'Referências aceitas: {", ".join(REF_KEYS)} (texto).')
    hits = secret_hits(subject, body, *options, *refs.values())
    if hits:
        raise CommsError('SECRET_DETECTED', 'O texto parece conter um segredo (' + ', '.join(hits) + '). '
                         'Não envie credenciais por aqui; combine outro canal seguro.')
    cutoff = now_utc() - timedelta(hours=1)
    recent = [e for e in existing if protolib.norm_email(e.get('from')) == me
              and (parse_iso(e.get('at')) or cutoff) > cutoff]
    if len(recent) >= MAX_PER_HOUR:
        raise CommsError('RATE_LIMIT', f'Limite de {MAX_PER_HOUR} envios por hora atingido; tente mais tarde.')
    return {'kind': kind, 'to': to, 'subject': subject, 'body': body, 'priority': event.get('priority', 'normal'),
            'options': [o.strip() for o in options], 'refs': refs, 'inReplyTo': event.get('inReplyTo')}


def validate_receipt(receipt, actor, target, roster, originals):
    """Valida um recibo (ack) sobre `target` (um evento original ou outro recibo). Levanta CommsError."""
    check_actor(actor, 'responder a')
    kind = receipt.get('kind')
    if kind not in RECEIPT_KINDS:
        raise CommsError('BAD_ACTION', f'Ação inválida; use: {", ".join(RECEIPT_KINDS)}.')
    me = protolib.norm_email(actor.get('email'))
    if target.get('kind') in RECEIPT_KINDS:
        # o autor do recado original confirma que viu a resposta (recibo "lida" sobre o recibo)
        original = originals.get(target.get('target'))
        if kind != 'read' or not original or protolib.norm_email(original.get('from')) != me:
            raise CommsError('NOT_OWNER', 'Só o autor do recado original marca a resposta dele como lida.')
        return receipt
    sender = protolib.norm_email(target.get('from'))
    if kind == 'cancel':
        if sender != me:
            raise CommsError('NOT_OWNER', 'Só quem enviou o recado pode cancelá-lo.')
        return receipt
    if not can_see(target, actor, roster):
        raise CommsError('NOT_VISIBLE', 'Este recado não foi endereçado a você.')
    if sender == me:
        raise CommsError('BAD_ACTION', 'Você não responde ao próprio recado; envie um recado novo (inReplyTo).')
    original_kind = target.get('kind')
    allowed = {'message': ('read',), 'handoff': ('read', 'answer'), 'question': ('read', 'answer'),
               'confirm': ('read', 'answer'), 'task': ('read', 'accept', 'decline', 'done')}[original_kind]
    if kind not in allowed:
        raise CommsError('BAD_ACTION', f'Para um recado do tipo "{original_kind}" use: {", ".join(allowed)}.')
    if kind == 'answer':
        body = (receipt.get('body') or '').strip()
        if not body and not receipt.get('choice'):
            raise CommsError('EMPTY_ANSWER', 'Informe o texto da resposta (ou a opção escolhida).')
        if original_kind == 'confirm' and receipt.get('choice') not in target.get('options', []):
            raise CommsError('BAD_CHOICE', 'A resposta precisa ser uma das opções: ' + ', '.join(target.get('options', [])))
        if len(body) > MAX_BODY:
            raise CommsError('BODY_TOO_LONG', f'A resposta vai até {MAX_BODY} caracteres.')
        hits = secret_hits(body)
        if hits:
            raise CommsError('SECRET_DETECTED', 'A resposta parece conter um segredo (' + ', '.join(hits) + ').')
    return receipt


def can_see(event, member, roster):
    """D5: pendente só vê o que foi endereçado diretamente a ele (ou que ele mesmo enviou)."""
    me = protolib.norm_email(member.get('email'))
    if protolib.norm_email(event.get('from')) == me:
        return True
    if member.get('status') == 'pending':
        return me in direct_recipients(event)
    if member.get('status') != 'approved':
        return False
    return me in resolve_recipients(event, roster)


# ------------------------------------------------------------------ git: leitura

def _ref_remote(repo, cfg, branch):
    return f'refs/remotes/{cfg.get("remote", "origin")}/{branch}'


def tips(repo, cfg):
    """Pontas conhecidas da branch (remota e local), sem repetição."""
    branch = comms_cfg(cfg)['branch']
    out = []
    for ref in (_ref_remote(repo, cfg, branch), f'refs/heads/{branch}'):
        sha = gs.rev(repo, ref)
        if sha and sha not in out:
            out.append(sha)
    return out


def _tree_files(repo, tip):
    r = protolib.git(repo, 'ls-tree', '-r', tip)
    files = {}
    for line in r.stdout.splitlines():
        meta, path = line.split('\t', 1)
        mode, kind, sha = meta.split(' ')
        if kind == 'blob':
            files[path] = (mode, sha)
    return files


def read_events(repo, cfg):
    """Todos os eventos legíveis (originais e recibos), unidos entre as pontas, ordenados por data."""
    seen, events = set(), []
    for tip in tips(repo, cfg):
        for path, (_, sha) in sorted(_tree_files(repo, tip).items()):
            m = EVENT_PATH_RE.match(path)
            if not m or m.group(1) in seen:
                continue
            blob = protolib.git(repo, 'cat-file', 'blob', sha)
            try:
                ev = json.loads(blob.stdout)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict) or ev.get('id') != m.group(1):
                continue
            seen.add(m.group(1))
            events.append(ev)
    events.sort(key=lambda e: (e.get('at') or '', e.get('id')))
    return events


def refresh(repo, cfg):
    """Atualiza só a branch de comunicação (sem tocar em nada mais). Devolve (ok, erro)."""
    remote, branch = cfg.get('remote', 'origin'), comms_cfg(cfg)['branch']
    try:
        r = protolib.git(repo, 'fetch', '-q', remote, f'+refs/heads/{branch}:{_ref_remote(repo, cfg, branch)}',
                         timeout=60)
    except subprocess.TimeoutExpired:
        return False, 'tempo esgotado'
    if r.returncode != 0 and 'couldn\'t find remote ref' in r.stderr:
        return True, ''  # a branch ainda não existe no remoto
    return r.returncode == 0, r.stderr.strip()


# ------------------------------------------------------------------ estado derivado

def index_events(events):
    originals = {e['id']: e for e in events if e.get('kind') in KINDS}
    receipts = [e for e in events if e.get('kind') in RECEIPT_KINDS and e.get('target')]
    by_target = {}
    for r in receipts:
        by_target.setdefault(r['target'], []).append(r)
    return originals, receipts, by_target


def is_cancelled(original, by_target):
    return any(r['kind'] == 'cancel' and protolib.norm_email(r.get('from')) == protolib.norm_email(original['from'])
               for r in by_target.get(original['id'], []))


def expires_at(original, cfg):
    explicit = parse_iso(original.get('expiresAt'))
    if explicit:
        return explicit
    base = parse_iso(original.get('at')) or now_utc()
    return base + timedelta(days=int(comms_cfg(cfg)['expiryDays']))


def recipient_state(original, email, by_target):
    """{'read': bool, 'closed': bool, 'receipts': [...]} para um destinatário."""
    me = protolib.norm_email(email)
    mine = [r for r in by_target.get(original['id'], []) if protolib.norm_email(r.get('from')) == me]
    kinds = {r['kind'] for r in mine}
    closed = bool(kinds & set(CLOSING[original['kind']]))
    return {'read': bool(kinds & {'read', 'answer', 'accept', 'decline', 'done'}), 'closed': closed,
            'receipts': mine}


def inbox_for(events, member, roster, cfg, now=None):
    """Itens abertos para a pessoa (como destinatária) e novidades dos recados que ela enviou."""
    now = now or now_utc()
    me = protolib.norm_email(member.get('email'))
    originals, receipts, by_target = index_events(events)
    comms = comms_cfg(cfg)
    incoming, sent, news, reminders = [], [], [], []
    for orig in originals.values():
        if is_cancelled(orig, by_target) or expires_at(orig, cfg) < now:
            continue
        if protolib.norm_email(orig['from']) != me and can_see(orig, member, roster):
            st = recipient_state(orig, me, by_target)
            if not st['closed']:
                incoming.append({'event': orig, 'unread': not st['read'],
                                 'accepted': any(r['kind'] == 'accept' for r in st['receipts'])})
        if protolib.norm_email(orig['from']) == me:
            recips = sorted(resolve_recipients(orig, roster))
            per = {r_email: recipient_state(orig, r_email, by_target) for r_email in recips}
            sent.append({'event': orig, 'recipients': {e: {'read': s['read'], 'closed': s['closed']}
                                                       for e, s in per.items()}})
            at = parse_iso(orig.get('at'))
            if orig.get('priority') == 'urgent' and at and now - at > timedelta(hours=int(comms['reminderHours'])):
                waiting = [e for e, s in per.items() if not s['read']]
                if waiting:
                    reminders.append({'id': orig['id'], 'subject': orig['subject'], 'waiting': waiting})
    seen_by_me = {r['target'] for r in receipts if r['kind'] == 'read' and protolib.norm_email(r['from']) == me}
    for r in receipts:
        orig = originals.get(r['target'])
        if (orig and protolib.norm_email(orig['from']) == me and protolib.norm_email(r['from']) != me
                and r['kind'] in NEWS_KINDS and r['id'] not in seen_by_me):
            news.append({'receipt': r, 'about': {'id': orig['id'], 'subject': orig['subject'], 'kind': orig['kind']}})
    incoming.sort(key=lambda i: (i['event'].get('priority') != 'urgent', i['event'].get('at') or ''))
    return {'incoming': incoming, 'news': news, 'sent': sent, 'reminders': reminders}


def pending_count(inbox):
    return sum(1 for i in inbox['incoming'] if i['unread']) + len(inbox['news'])


# ------------------------------------------------------------------ git: escrita

README_TEXT = ('# Comunicação do time\n\nBranch de recados do protótipo (gerada pela skill interactive-prototype). '
               'Não é código do protótipo: nunca é promovida nem integrada à beta ou à oficial.\n'
               'Cada arquivo em `events/` é um evento imutável; não edite à mão.\n')


def _plumb(repo, env_extra, *args, input=None):
    env = dict(os.environ, **env_extra)
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, env=env,
                          input=input, timeout=60)


def _build_tree(repo, base, add_blobs):
    """Árvore = árvore de `base` (ou vazia) + {path: (mode, blob_sha)}. Índice temporário."""
    with tempfile.TemporaryDirectory() as td:
        env = {'GIT_INDEX_FILE': os.path.join(td, 'index')}
        if base and _plumb(repo, env, 'read-tree', base).returncode != 0:
            raise CommsError('GIT_FAILED', 'não consegui ler a branch de comunicação')
        lines = [f'{mode} {sha}\t{path}' for path, (mode, sha) in sorted(add_blobs.items())]
        if lines:
            r = _plumb(repo, env, 'update-index', '--add', '--index-info', input='\n'.join(lines) + '\n')
            if r.returncode != 0:
                raise CommsError('GIT_FAILED', f'update-index falhou: {r.stderr.strip()}')
        w = _plumb(repo, env, 'write-tree')
        if w.returncode != 0:
            raise CommsError('GIT_FAILED', f'write-tree falhou: {w.stderr.strip()}')
        return w.stdout.strip()


def _blob(repo, text):
    r = subprocess.run(['git', '-C', str(repo), 'hash-object', '-w', '--stdin'], capture_output=True, text=True,
                       input=text, timeout=30)
    if r.returncode != 0:
        raise CommsError('GIT_FAILED', f'hash-object falhou: {r.stderr.strip()}')
    return r.stdout.strip()


def commit_event(repo, cfg, event, trailers, max_retries=3):
    """Grava um evento na branch de comunicação e envia (sem force, sem checkout).

    Devolve {'sha','pushed','path'}. Sem rede: o commit local fica e `pushed` é False (NOT_SYNCED ao chamador).
    Push recusado (alguém enviou no meio tempo) ⇒ refaz em cima da ponta nova, trazendo junto os eventos locais
    ainda não enviados; como cada evento é um arquivo novo, não há conflito.
    """
    remote, branch = cfg.get('remote', 'origin'), comms_cfg(cfg)['branch']
    local_ref, path = f'refs/heads/{branch}', event_path(event['id'])
    blob = _blob(repo, json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    for attempt in range(max_retries + 1):
        remote_tip, local_tip = gs.rev(repo, _ref_remote(repo, cfg, branch)), gs.rev(repo, local_ref)
        base = remote_tip or local_tip
        carry = {}
        if local_tip and base and local_tip != base and not gs.is_ancestor(repo, local_tip, base):
            base_files = _tree_files(repo, base)
            carry = {p: v for p, v in _tree_files(repo, local_tip).items() if p not in base_files}
        add = dict(carry)
        add[path] = ('100644', blob)
        if not base:
            add['README.md'] = ('100644', _blob(repo, README_TEXT))
        tree = _build_tree(repo, base, add)
        msg = f'chore(comms): {event["kind"]} {event["id"]}\n\n{protolib.format_trailers(trailers)}\n'
        c = protolib.git(repo, 'commit-tree', tree, '-m', msg, *(['-p', base] if base else []))
        if c.returncode != 0:
            raise CommsError('GIT_FAILED', f'commit-tree falhou: {c.stderr.strip()}')
        sha = c.stdout.strip()
        u = protolib.git(repo, 'update-ref', local_ref, sha)
        if u.returncode != 0:
            raise CommsError('GIT_FAILED', f'update-ref falhou: {u.stderr.strip()}')
        state, detail = gs.push(repo, remote, f'{local_ref}:refs/heads/{branch}')
        if state == 'ok':
            return {'sha': sha, 'pushed': True, 'path': path}
        if state == 'offline':
            return {'sha': sha, 'pushed': False, 'path': path, 'detail': detail}
        ok, _ = refresh(repo, cfg)
        if not ok:
            return {'sha': sha, 'pushed': False, 'path': path, 'detail': 'sem acesso ao remoto após recusa'}
    raise CommsError('PUSH_REJECTED', 'O remoto recusou o envio várias vezes seguidas; nada foi forçado. '
                                      'O recado ficou guardado neste computador; tente de novo em instantes.')


def ensure_branch(repo, cfg, trailers):
    """Cria a branch órfã (README) se ainda não existir. Devolve {'created': bool, 'pushed': bool, 'sha'}."""
    remote, branch = cfg.get('remote', 'origin'), comms_cfg(cfg)['branch']
    refresh(repo, cfg)
    if tips(repo, cfg):
        return {'created': False, 'pushed': True, 'sha': tips(repo, cfg)[0]}
    tree = _build_tree(repo, None, {'README.md': ('100644', _blob(repo, README_TEXT))})
    msg = f'chore(comms): cria a branch de comunicação\n\n{protolib.format_trailers(trailers)}\n'
    c = protolib.git(repo, 'commit-tree', tree, '-m', msg)
    if c.returncode != 0:
        raise CommsError('GIT_FAILED', f'commit-tree falhou: {c.stderr.strip()}')
    sha = c.stdout.strip()
    protolib.git(repo, 'update-ref', f'refs/heads/{branch}', sha, check=True)
    state, detail = gs.push(repo, remote, f'refs/heads/{branch}:refs/heads/{branch}')
    return {'created': True, 'pushed': state == 'ok', 'sha': sha, 'detail': detail}


def make_event(kind, sender_email, fields, now=None):
    now = now or now_utc()
    ev = {'schema': 1, 'id': new_id(now), 'at': iso(now), 'kind': kind, 'from': protolib.norm_email(sender_email)}
    ev.update(fields)
    return ev


# ------------------------------------------------------------------ contexto comum dos scripts

def enabled_anywhere(cfg, roster):
    """Ligada no config local OU no config da beta no remoto (quem acabou de clonar pode ter cópia velha)."""
    return comms_cfg(cfg)['enabled'] or comms_cfg(roster)['enabled']


def git_email(repo):
    r = protolib.git(repo, 'config', 'user.email')
    return protolib.norm_email(r.stdout) if r.returncode == 0 else ''


def load_context(repo, actor_email, require_enabled=True):
    """(cfg, member, roster, actor_email). Levanta CommsError com o código certo para cada falha."""
    if protolib.git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        raise CommsError('NOT_A_REPO', f'{repo} não é um repositório git.')
    cfg, err = protolib.load_config(repo)
    probs = gs.check_group_config(cfg, err)
    if probs:
        raise CommsError('INVALID_CONFIG', probs[0]['message'])
    email = protolib.norm_email(actor_email) or git_email(repo)
    if not email:
        raise CommsError('NO_IDENTITY', 'Informe --actor-email (o git desta máquina não tem e-mail).')
    member, roster = actor_context(repo, cfg, email)
    if require_enabled and not enabled_anywhere(cfg, roster):
        raise CommsError('DISABLED', 'A comunicação do time não está ligada neste protótipo '
                                     '(comms-setup.py --enable, por um promoter).')
    return cfg, member, roster, email
