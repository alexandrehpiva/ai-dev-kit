#!/usr/bin/env python3
"""Valida prototype.config.json: schema (v2) + integridade referencial. Só stdlib.

  python3 config-validate.py --repo <pasta> [--require-promoter]

Status do envelope:
  VALID      config v2 íntegro (ok)
  INVALID    JSON quebrado, violação do schema ou de integridade (problemas listam o caminho do campo)
  LEGACY     config v1 (sem bloco `skill`): não é erro, `data.legacy=true`; migre com migrate.py (ok)
  NO_CONFIG  sem prototype.config.json: protótipo solo sem config (ok)
Com --require-promoter, exige ≥1 membro approved+promoter mesmo com groupMode=false; LEGACY/NO_CONFIG
passam a falhar (não há membros). Exit: 0 ok, 1 problemas, 2 uso incorreto.

Integridade: e-mails de membros únicos (sem distinguir caixa), ids de artefatos únicos, ≤1 artefato
`official` e ≤1 `beta` (artefatos `revoked` não contam: liberam o lugar), `owner` existente em members,
branches.official != branches.beta, groupMode=true ⇒ ≥1 approved+promoter, member.status == último
statusHistory[].status.

O validador de schema é próprio (sem libs): suporta o subconjunto de JSON Schema usado em
templates/prototype.config.schema.json ($ref local, type, enum, const, required, properties,
additionalProperties=false, items, minItems, uniqueItems, minLength, minimum, pattern, anyOf, format
email/date-time). Outros ficam ignorados.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import protolib  # noqa: E402
import configtools  # noqa: E402

SCHEMA_NAME = 'prototype.config.schema.json'
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$')
LEGACY_KEYS = {'groupMode': bool, 'sharedBranch': str, 'remote': str}

_TYPE_NAMES = {'string': 'texto', 'boolean': 'booleano', 'integer': 'inteiro', 'number': 'número',
               'object': 'objeto', 'array': 'lista', 'null': 'nulo'}


def schema_path():
    return protolib.skill_root() / 'templates' / SCHEMA_NAME


def load_schema():
    return json.loads(schema_path().read_text(encoding='utf-8'))


def _type_ok(value, name):
    if name == 'null':
        return value is None
    if name == 'boolean':
        return isinstance(value, bool)
    if name == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if name == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == 'string':
        return isinstance(value, str)
    if name == 'object':
        return isinstance(value, dict)
    if name == 'array':
        return isinstance(value, list)
    return True


def _type_of(value):
    for n in ('null', 'boolean', 'integer', 'number', 'string', 'object', 'array'):
        if _type_ok(value, n):
            return _TYPE_NAMES[n]
    return type(value).__name__


def _format_ok(fmt, value):
    if not isinstance(value, str):
        return True
    if fmt == 'email':
        return bool(EMAIL_RE.match(value))
    if fmt == 'date-time':
        if not ISO_RE.match(value):
            return False
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return False
        return True
    return True


def _join(path, key):
    if isinstance(key, int):
        return f'{path}[{key}]'
    return f'{path}.{key}' if path else key


def _resolve(ref, root):
    if not ref.startswith('#/'):
        raise ValueError(f'$ref não suportado: {ref}')
    node = root
    for part in ref[2:].split('/'):
        node = node[part]
    return node


def check_schema(value, schema, root, path=''):
    """Lista de (caminho, mensagem) para as violações de `value` contra `schema`."""
    if '$ref' in schema:
        return check_schema(value, _resolve(schema['$ref'], root), root, path)
    errs = []
    where = path or '(raiz)'

    types = schema.get('type')
    if types is not None:
        names = types if isinstance(types, list) else [types]
        if not any(_type_ok(value, n) for n in names):
            esperado = ' ou '.join(_TYPE_NAMES.get(n, n) for n in names)
            return [(where, f'tipo inválido: esperado {esperado}, recebido {_type_of(value)}')]

    if 'const' in schema and value != schema['const']:
        errs.append((where, f'valor inválido {value!r}; esperado {schema["const"]!r}'))
    if 'enum' in schema and value not in schema['enum']:
        errs.append((where, f'valor inválido {value!r}; permitidos: {", ".join(map(str, schema["enum"]))}'))

    if isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            errs.append((where, 'não pode ser vazio' if schema['minLength'] == 1
                         else f'tamanho mínimo {schema["minLength"]}'))
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            errs.append((where, f'formato inválido ({value!r})'))
        if 'format' in schema and not _format_ok(schema['format'], value):
            errs.append((where, f'formato de {"e-mail" if schema["format"] == "email" else "data/hora ISO-8601"} inválido ({value!r})'))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in schema and value < schema['minimum']:
            errs.append((where, f'valor mínimo {schema["minimum"]}, recebido {value}'))

    if isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            errs.append((where, f'precisa de ao menos {schema["minItems"]} item(ns)'))
        if schema.get('uniqueItems'):
            seen = []
            for i, item in enumerate(value):
                if item in seen:
                    errs.append((_join(path, i), f'item duplicado ({item!r})'))
                seen.append(item)
        if 'items' in schema:
            for i, item in enumerate(value):
                errs.extend(check_schema(item, schema['items'], root, _join(path, i)))

    if isinstance(value, dict):
        props = schema.get('properties', {})
        for name in schema.get('required', []):
            if name not in value:
                errs.append((_join(path, name), 'campo obrigatório ausente'))
        for name, sub in props.items():
            if name in value:
                errs.extend(check_schema(value[name], sub, root, _join(path, name)))
        if schema.get('additionalProperties') is False:
            for name in value:
                if name not in props:
                    errs.append((_join(path, name), 'campo desconhecido'))

    if 'anyOf' in schema:
        if not any(not check_schema(value, alt, root, path) for alt in schema['anyOf']):
            errs.append((where, f'valor inválido ({value!r}): não atende a nenhuma das alternativas permitidas'))

    return errs


def check_integrity(cfg, require_promoter=False):
    """Regras que o schema não expressa. Tolera estruturas malformadas (o schema já as reporta)."""
    errs = []
    members = [m for m in cfg.get('members', []) if isinstance(m, dict)] if isinstance(cfg.get('members'), list) else []
    seen = {}
    for i, m in enumerate(cfg.get('members') if isinstance(cfg.get('members'), list) else []):
        if not isinstance(m, dict):
            continue
        email = protolib.norm_email(m.get('email')) if isinstance(m.get('email'), str) else ''
        if email:
            if email in seen:
                errs.append((f'members[{i}].email',
                             f'e-mail duplicado (já usado em members[{seen[email]}]): {m.get("email")}'))
            else:
                seen[email] = i
        hist = m.get('statusHistory')
        if isinstance(hist, list) and hist and isinstance(hist[-1], dict) and 'status' in m:
            last = hist[-1].get('status')
            if last != m.get('status'):
                errs.append((f'members[{i}].status',
                             f'status "{m.get("status")}" diverge do último statusHistory ("{last}")'))

    arts = cfg.get('artifacts') if isinstance(cfg.get('artifacts'), list) else []
    ids, kind_first = {}, {}
    for i, a in enumerate(arts):
        if not isinstance(a, dict):
            continue
        aid = a.get('id')
        if isinstance(aid, str):
            if aid in ids:
                errs.append((f'artifacts[{i}].id', f'id de artefato duplicado (já usado em artifacts[{ids[aid]}]): {aid}'))
            else:
                ids[aid] = i
        kind = a.get('kind')
        if kind in ('official', 'beta') and a.get('status') != 'revoked':
            if kind in kind_first:
                errs.append((f'artifacts[{i}].kind',
                             f'só pode haver um artefato "{kind}" ativo (já existe artifacts[{kind_first[kind]}]); revogue o anterior antes'))
            else:
                kind_first[kind] = i
        owner = a.get('owner')
        if isinstance(owner, str) and protolib.norm_email(owner) not in seen:
            errs.append((f'artifacts[{i}].owner', f'owner "{owner}" não é um membro cadastrado em members'))

    br = cfg.get('branches')
    if isinstance(br, dict) and br.get('official') is not None and br.get('official') == br.get('beta'):
        errs.append(('branches.beta', f'branches.official e branches.beta não podem ser iguais ("{br.get("beta")}")'))

    need = cfg.get('groupMode') is True or require_promoter
    if need and not any(protolib.is_promoter(m) for m in members):
        why = 'groupMode=true' if cfg.get('groupMode') is True else '--require-promoter'
        errs.append(('members', f'{why} exige ao menos um membro approved com papel promoter'))
    return errs


def check_legacy(cfg):
    errs = []
    for key, typ in LEGACY_KEYS.items():
        if key in cfg and not isinstance(cfg[key], typ):
            errs.append((key, f'tipo inválido: esperado {_TYPE_NAMES["boolean" if typ is bool else "string"]}, recebido {_type_of(cfg[key])}'))
    return errs


def validate_config(cfg, require_promoter=False, schema=None):
    """Valida um dict já carregado. Retorna (status, data, problems)."""
    if not isinstance(cfg, dict):
        return 'INVALID', {'legacy': False}, [_prob('SCHEMA', '(raiz)', 'o config precisa ser um objeto JSON')]
    if 'skill' not in cfg:
        errs = check_legacy(cfg)
        probs = [_prob('LEGACY_FIELD', p, m) for p, m in errs]
        if require_promoter:
            probs.append(_prob('NO_PROMOTER', 'members', 'config legado não tem membros: migre (migrate.py) e registre um promoter'))
        if errs:
            return 'INVALID', {'legacy': True}, probs
        return 'LEGACY', {'legacy': True, 'groupMode': bool(cfg.get('groupMode', False))}, probs

    schema = schema or load_schema()
    probs = [_prob('SCHEMA', p, m) for p, m in check_schema(cfg, schema, schema)]
    probs += [_prob('INTEGRITY', p, m) for p, m in check_integrity(cfg, require_promoter)]
    data = {'legacy': False}
    if isinstance(cfg.get('members'), list):
        data['members'] = len(cfg['members'])
        data['promoters'] = sum(1 for m in cfg['members'] if isinstance(m, dict) and protolib.is_promoter(m))
    if isinstance(cfg.get('artifacts'), list):
        data['artifacts'] = len(cfg['artifacts'])
    data['groupMode'] = cfg.get('groupMode')
    return ('INVALID' if probs else 'VALID'), data, probs


def _prob(code, path, message):
    p = protolib.problem(code, message if path == '(raiz)' else f'{path}: {message}')
    p['path'] = path
    return p


def main(argv=None):
    ap = configtools.JsonArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--require-promoter', action='store_true')
    args = ap.parse_args(argv)

    repo = configtools.resolve_repo(args.repo)
    if repo is None:
        return configtools.usage_error(f'pasta não encontrada: {args.repo}')
    try:
        cfg, err = protolib.load_config(repo)
    except OSError as e:
        return configtools.usage_error(f'não foi possível ler {protolib.CONFIG_NAME}: {e}')
    if err:
        return protolib.emit(False, 'INVALID', {'legacy': False}, [_prob('JSON', '(raiz)', err)])
    if cfg is None:
        if args.require_promoter:
            return protolib.emit(False, 'NO_CONFIG', {}, [protolib.problem('NO_PROMOTER',
                                 'sem config: não há promoter registrado (rode migrate.py)')])
        return protolib.emit(True, 'NO_CONFIG', {'legacy': False})

    try:
        status, data, problems = validate_config(cfg, args.require_promoter)
    except (OSError, json.JSONDecodeError) as e:
        return configtools.usage_error(f'schema da skill ilegível ({schema_path()}): {e}')
    ok = status in ('VALID', 'LEGACY') and not problems
    return protolib.emit(ok, status, data, problems)


if __name__ == '__main__':
    sys.exit(main())
