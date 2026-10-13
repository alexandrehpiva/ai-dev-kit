#!/usr/bin/env python3
"""Registro de artefatos (links/arquivos publicados) em prototype.config.json. Só stdlib.

  python3 artifacts.py --repo <pasta> list
  python3 artifacts.py --repo <pasta> register --id ID --kind official|beta|preview --delivery claude-artifact|file
        --owner EMAIL [--branch B] [--url URL | --path P] [--label T] [--purpose T] [--source-ref T]
  python3 artifacts.py --repo <pasta> published --id ID --version vX.Y.Z[-beta.N] --actor EMAIL
  python3 artifacts.py --repo <pasta> mark-stale --id ID --pending-version vX.Y.Z[-beta.N]
  python3 artifacts.py --repo <pasta> revoke --id ID --reason TEXTO
  python3 artifacts.py --repo <pasta> set-status --id ID --status current|stale|revoked|missing

Regras: exige config v2; escrita atômica (temporário + rename); após cada mudança o config inteiro é
revalidado e a escrita é recusada se surgir problema NOVO. Versão: official = vX.Y.Z, beta =
vX.Y.Z-beta.N, preview = sem numeração (version pode ser omitida e fica null). Publicar o oficial exige
actor promoter aprovado; beta/preview aceitam actor membro pending/approved. Artefato `revoked` só volta
a ser usado via set-status. Exit: 0 ok, 1 recusado, 2 uso incorreto.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import protolib  # noqa: E402
import configtools  # noqa: E402


def new_artifact(art_id, kind, branch, delivery, owner, status, url=None, path=None,
                 label=None, purpose=None, source_ref=None):
    """Artefato no formato do config v2 (version/pendingVersion/publishedAt/publishedBy nulos)."""
    art = {'id': art_id, 'kind': kind, 'branch': branch, 'delivery': delivery}
    if url:
        art['url'] = url
    if path:
        art['path'] = path
    art.update({'owner': owner, 'version': None, 'status': status, 'pendingVersion': None,
                'publishedAt': None, 'publishedBy': None})
    for key, val in (('label', label), ('purpose', purpose), ('sourceRef', source_ref)):
        if val:
            art[key] = val
    return art


def normalize_version(text):
    """'1.2.3' → 'v1.2.3'; None se inválida."""
    parsed = protolib.parse_version(text)
    return protolib.format_version(*parsed) if parsed else None


def version_matches_kind(kind, version):
    parsed = protolib.parse_version(version)
    if parsed is None:
        return 'versão inválida (esperado vX.Y.Z ou vX.Y.Z-beta.N)'
    if kind == 'official' and parsed[3] is not None:
        return 'artefato oficial usa vX.Y.Z (sem sufixo -beta.N)'
    if kind == 'beta' and parsed[3] is None:
        return 'artefato beta usa vX.Y.Z-beta.N'
    return None


def find_artifact(cfg, art_id):
    for a in cfg.get('artifacts', []):
        if a.get('id') == art_id:
            return a
    return None


def _fail(status, code, message):
    return protolib.emit(False, status, problems=[protolib.problem(code, message)])


def _commit(repo, before, cfg, validator, status, data):
    """Revalida o config; só grava se não surgirem problemas novos."""
    _, _, after = validator.validate_config(cfg)
    known = {p['message'] for p in before}
    fresh = [p for p in after if p['message'] not in known]
    if fresh:
        return protolib.emit(False, 'INVALID', problems=fresh)
    configtools.atomic_save_config(repo, cfg)
    return protolib.emit(True, status, data)


def cmd_list(cfg, args):
    arts = cfg.get('artifacts', [])
    return protolib.emit(True, 'OK', {'artifacts': arts, 'count': len(arts)})


def _active_exists(cfg, kind, exclude_id=None):
    return any(a.get('kind') == kind and a.get('status') != 'revoked' and a.get('id') != exclude_id
               for a in cfg.get('artifacts', []))


def _check_member_status(cfg, email, require_promoter):
    m = protolib.find_member(cfg, email)
    if m is None:
        return None, f'"{email}" não é membro cadastrado'
    if m.get('status') not in ('pending', 'approved'):
        return None, f'"{email}" está com status "{m.get("status")}" e não pode publicar'
    if require_promoter and not protolib.is_promoter(m):
        return None, f'publicar o artefato oficial exige promoter aprovado; "{email}" não é'
    return m, None


def prepare(args, cfg, validator):
    """Aplica o subcomando sobre `cfg` (in-memory). Retorna (status, data) ou levanta Refuse."""
    art_id = getattr(args, 'id', None)
    arts = cfg.setdefault('artifacts', [])

    if args.cmd == 'register':
        if find_artifact(cfg, art_id):
            raise Refuse('DUPLICATE_ID', f'já existe artefato com id "{art_id}"')
        if args.url and args.path:
            raise Refuse('BAD_LOCATION', 'informe só um entre --url e --path')
        if args.url and not args.url.startswith(('http://', 'https://')):
            raise Refuse('BAD_URL', '--url precisa começar com http:// ou https://')
        if args.url and args.delivery != 'claude-artifact':
            raise Refuse('BAD_LOCATION', '--url só vale para delivery claude-artifact')
        if args.path and args.delivery != 'file':
            raise Refuse('BAD_LOCATION', '--path só vale para delivery file')
        if args.kind in ('official', 'beta') and _active_exists(cfg, args.kind):
            raise Refuse('DUPLICATE_KIND', f'já existe um artefato "{args.kind}" ativo; revogue-o antes de registrar outro')
        owner = protolib.find_member(cfg, args.owner)
        if owner is None:
            raise Refuse('UNKNOWN_OWNER', f'owner "{args.owner}" não é membro cadastrado')
        branch = args.branch
        if branch is None and args.kind in ('official', 'beta'):
            branch = cfg.get('branches', {}).get(args.kind)
        art = new_artifact(art_id, args.kind, branch, args.delivery, owner['email'],
                           'stale' if (args.url or args.path) else 'missing', args.url, args.path,
                           args.label, args.purpose, args.source_ref)
        arts.append(art)
        return 'REGISTERED', {'artifact': art}

    art = find_artifact(cfg, art_id)
    if art is None:
        raise Refuse('NOT_FOUND', f'artefato "{art_id}" não encontrado')

    if args.cmd == 'published':
        if art['status'] == 'revoked':
            raise Refuse('REVOKED', f'artefato "{art_id}" está revogado; use set-status antes de publicar de novo')
        version = None
        if args.version:
            version = normalize_version(args.version)
            err = version_matches_kind(art['kind'], args.version)
            if err:
                raise Refuse('BAD_VERSION', err)
        elif art['kind'] != 'preview':
            raise Refuse('BAD_VERSION', '--version é obrigatório para artefato official/beta')
        _, err = _check_member_status(cfg, args.actor, art['kind'] == 'official')
        if err:
            raise Refuse('BAD_ACTOR', err)
        art.update({'version': version, 'status': 'current', 'pendingVersion': None,
                    'publishedAt': protolib.now_iso(), 'publishedBy': protolib.find_member(cfg, args.actor)['email']})
        return 'PUBLISHED', {'artifact': art}

    if args.cmd == 'mark-stale':
        if art['status'] == 'revoked':
            raise Refuse('REVOKED', f'artefato "{art_id}" está revogado')
        err = version_matches_kind(art['kind'], args.pending_version) if art['kind'] != 'preview' \
            else (None if protolib.parse_version(args.pending_version) else 'versão inválida (esperado vX.Y.Z ou vX.Y.Z-beta.N)')
        if err:
            raise Refuse('BAD_VERSION', err)
        art.update({'status': 'stale', 'pendingVersion': normalize_version(args.pending_version)})
        return 'STALE', {'artifact': art}

    if args.cmd == 'revoke':
        if not args.reason.strip():
            raise Refuse('BAD_REASON', '--reason não pode ser vazio')
        art.update({'status': 'revoked', 'revokedAt': protolib.now_iso(), 'revokedReason': args.reason.strip()})
        return 'REVOKED', {'artifact': art}

    if args.cmd == 'set-status':
        if args.status == 'current' and art['kind'] != 'preview' and not art.get('version'):
            raise Refuse('BAD_STATUS', 'artefato sem version publicada não pode ficar "current"; use "published"')
        if args.status != 'revoked':
            for key in ('revokedAt', 'revokedReason'):
                art.pop(key, None)
        if args.status == 'current':
            art['pendingVersion'] = None
        art['status'] = args.status
        return 'STATUS_SET', {'artifact': art}

    raise Refuse('BAD_USAGE', f'subcomando desconhecido: {args.cmd}')


class Refuse(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


def build_parser():
    ap = configtools.JsonArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list')
    r = sub.add_parser('register')
    r.add_argument('--id', required=True)
    r.add_argument('--kind', required=True, choices=protolib.ARTIFACT_KINDS)
    r.add_argument('--delivery', required=True, choices=protolib.DELIVERIES)
    r.add_argument('--branch')
    r.add_argument('--url')
    r.add_argument('--path')
    r.add_argument('--owner', required=True)
    r.add_argument('--label')
    r.add_argument('--purpose')
    r.add_argument('--source-ref', dest='source_ref')
    p = sub.add_parser('published')
    p.add_argument('--id', required=True)
    p.add_argument('--version')
    p.add_argument('--actor', required=True)
    s = sub.add_parser('mark-stale')
    s.add_argument('--id', required=True)
    s.add_argument('--pending-version', dest='pending_version', required=True)
    v = sub.add_parser('revoke')
    v.add_argument('--id', required=True)
    v.add_argument('--reason', required=True)
    t = sub.add_parser('set-status')
    t.add_argument('--id', required=True)
    t.add_argument('--status', required=True, choices=protolib.ARTIFACT_STATUSES)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo = configtools.resolve_repo(args.repo)
    if repo is None:
        return configtools.usage_error(f'pasta não encontrada: {args.repo}')
    cfg, err = protolib.load_config(repo)
    if err:
        return _fail('INVALID', 'JSON', err)
    if cfg is None:
        return _fail('NO_CONFIG', 'NO_CONFIG', f'{protolib.CONFIG_NAME} não existe; rode migrate.py --execute primeiro')
    if not configtools.is_v2(cfg):
        return _fail('LEGACY', 'LEGACY', 'config legado (v1): rode migrate.py antes de registrar artefatos')

    if args.cmd == 'list':
        return cmd_list(cfg, args)

    validator = configtools.load_script('config-validate.py')
    _, _, before = validator.validate_config(cfg)
    try:
        status, data = prepare(args, cfg, validator)
    except Refuse as e:
        return _fail('REFUSED', e.code, e.message)
    return _commit(repo, before, cfg, validator, status, data)


if __name__ == '__main__':
    sys.exit(main())
