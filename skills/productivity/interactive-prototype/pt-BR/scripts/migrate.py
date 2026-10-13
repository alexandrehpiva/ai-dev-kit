#!/usr/bin/env python3
"""Migra um protótipo para a versão atual da skill, em saltos encadeados. Só stdlib. Nunca faz git.

  python3 migrate.py --repo <pasta> [--plan | --execute]
        [--answers-json '{...}' | --answers arquivo.json]
        [--actor-name N --actor-email E [--actor-profile product|technical] [--actor-evidence X]]
        [--templates-dir <pasta>]

--plan (padrão) não escreve nada: devolve `data.steps` (o que será criado/alterado, em frases) e `questions`
({id,text,options,default}) para o agente perguntar. --execute exige todas as respostas e, quando
groupMode=true ou não há membros, o ator (vira membro approved+promoter, statusHistory by='setup').

Respostas (JSON): promoters_policy = all-members|listed; docs_auto_maintain = true|false; com groupMode=true
também artifact_official e artifact_beta, cada um {"url": "https://..."} | {"path": "..."} | {"create": true}.
Link/arquivo informado ⇒ artefato `stale` (registrado, sem publicar); `create` ⇒ `missing` (criar depois).

Registro de migrações (MIGRATIONS): versão de origem → {to, questions, plan, transform, files}.
  transform(ctx) devolve o novo config em memória (sem I/O); files(ctx) faz os efeitos em disco.
  Ordem: todos os transform → valida o config resultante (config-validate.py) → files → grava o config
  (atômico) por último. Falha de validação ⇒ nada é escrito. Para um salto novo (ex.: 2.0.0→2.1.0) basta
  registrar mais uma entrada; se a skill estiver à frente da última migração registrada, o salto final só
  atualiza skill.version.

Idempotente: config já na versão da skill ⇒ UP_TO_DATE sem escrever; arquivos de usuário existentes nunca
são sobrescritos. Protótipo mais novo que a skill ⇒ SKILL_OUTDATED (somente consulta).
Exit: 0 ok, 1 recusado/incompleto, 2 uso incorreto.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import protolib  # noqa: E402
import configtools  # noqa: E402
import artifacts  # noqa: E402

TEMPLATE_FILES = ('AGENTS.md', 'CLAUDE.md', 'docs/business-rules.md', 'docs/components.md')
GITIGNORE_DIST = {'dist', 'dist/', '/dist', '/dist/'}
POLICIES = ('all-members', 'listed')


class Ctx:
    def __init__(self, repo, cfg, answers, actor, templates_dir, skill_version):
        self.repo = Path(repo)
        self.name = self.repo.resolve().name
        self.cfg = cfg
        self.answers = answers
        self.actor = actor
        self.templates_dir = Path(templates_dir)
        self.skill_version = skill_version
        self.warnings = []
        self.created = []
        self.updated = []
        self.skipped = []

    @property
    def group_mode(self):
        return bool(self.cfg.get('groupMode', False))


def effective_version(cfg):
    if isinstance(cfg, dict) and isinstance(cfg.get('skill'), dict) and cfg['skill'].get('version'):
        return cfg['skill']['version']
    return protolib.LEGACY_SKILL_VERSION


def pending_steps(from_version, to_version):
    """Saltos em ordem: [{from,to,type:'migration'|'version-bump'}]. Vazio se já está na versão."""
    cur, target = configtools.parse_semver(from_version), configtools.parse_semver(to_version)
    steps = []
    if cur is None or target is None:
        return steps
    cur_s = from_version
    while cur < target and cur_s in MIGRATIONS:
        nxt_s = MIGRATIONS[cur_s]['to']
        nxt = configtools.parse_semver(nxt_s)
        if nxt <= cur or nxt > target:
            break
        steps.append({'from': cur_s, 'to': nxt_s, 'type': 'migration'})
        cur_s, cur = nxt_s, nxt
    if cur < target:
        steps.append({'from': cur_s, 'to': to_version, 'type': 'version-bump'})
    return steps


# ---------- 1.0.0 → 2.0.0 ----------

def _question_defs(ctx):
    qs = [
        {'id': 'promoters_policy',
         'text': 'Qual papel sugerir ao aprovar uma pessoa? "all-members": promoter (pode publicar para o '
                 'cliente); "listed": colaborador. O papel de cada pessoa é decidido na aprovação e fica em '
                 '`roles`; só quem tem o papel promoter promove.',
         'options': list(POLICIES), 'default': 'all-members'},
        {'id': 'docs_auto_maintain',
         'text': 'O agente deve manter a documentação padrão do protótipo (design system, catálogo de componentes, '
                 'regras de negócio e jornadas já existentes) atualizada automaticamente a cada mudança?',
         'options': ['true', 'false'], 'default': 'false'},
    ]
    if ctx.group_mode:
        for kind, label in (('official', 'oficial'), ('beta', 'beta')):
            qs.append({'id': f'artifact_{kind}',
                       'text': f'Já existe um link ou arquivo do protótipo {label}? Informe {{"url": ...}} ou '
                               f'{{"path": ...}} para reaproveitar, ou {{"create": true}} para criar depois.',
                       'options': ['url', 'path', 'create'], 'default': 'create'})
    return qs


def _file_actions(ctx):
    """O que fazer com cada arquivo de template e o .gitignore (usado por plan e execute)."""
    acts = []
    for rel in TEMPLATE_FILES:
        dest, src = ctx.repo / rel, ctx.templates_dir / rel
        if dest.exists():
            acts.append({'action': 'skip', 'path': rel, 'text': f'Manter {rel} (já existe; não é sobrescrito)'})
        elif not src.is_file():
            acts.append({'action': 'warn', 'path': rel,
                         'text': f'Aviso: template de {rel} ausente; o arquivo não será criado'})
        else:
            acts.append({'action': 'create', 'path': rel, 'text': f'Criar {rel} a partir do template da skill'})
    gi = ctx.repo / '.gitignore'
    if not gi.exists():
        acts.append({'action': 'gitignore-create', 'path': '.gitignore', 'text': 'Criar .gitignore com dist/'})
    elif not _gitignore_has_dist(gi):
        acts.append({'action': 'gitignore-append', 'path': '.gitignore', 'text': 'Acrescentar dist/ ao .gitignore'})
    else:
        acts.append({'action': 'skip', 'path': '.gitignore', 'text': 'Manter .gitignore (já ignora dist/)'})
    return acts


def _gitignore_has_dist(path):
    return any(line.strip() in GITIGNORE_DIST for line in path.read_text(encoding='utf-8').splitlines())


def _needs_actor(ctx):
    return ctx.group_mode or not ctx.cfg.get('members')


def _plan_1_0_0(ctx, existed):
    a = ctx.answers
    steps = []
    if existed:
        shared = ctx.cfg.get('sharedBranch')
        steps.append(f'Converter {protolib.CONFIG_NAME} para o formato v2 (mantém groupMode={str(ctx.group_mode).lower()} '
                     f'e remote={ctx.cfg.get("remote", "origin")}'
                     + (f'; sharedBranch "{shared}" passa a ser branches.official' if shared else '') + ')')
    else:
        steps.append(f'Criar {protolib.CONFIG_NAME} v2 mínimo (groupMode=false)')
    steps.append('Definir branches (oficial=main, beta=beta, rascunho=draft/{member}) e bloco skill com a versão atual')
    policy = a.get('promoters_policy')
    steps.append(f'Registrar policy.promoters={policy}' if policy else 'Registrar policy.promoters conforme sua resposta')
    docs = a.get('docs_auto_maintain')
    steps.append(f'Registrar docs.autoMaintain={str(docs).lower()}' if docs is not None
                 else 'Registrar docs.autoMaintain conforme sua resposta')
    if _needs_actor(ctx):
        who = ctx.actor['email'] if ctx.actor else 'quem executa a migração'
        steps.append(f'Registrar {who} como membro approved + promoter (statusHistory by=setup)')
    if ctx.group_mode:
        for kind in ('official', 'beta'):
            ans = a.get(f'artifact_{kind}')
            if ans is None:
                steps.append(f'Registrar o artefato {kind} conforme sua resposta (link existente ou criar depois)')
            elif ans.get('create'):
                steps.append(f'Registrar o artefato {kind} como pendente de criação (status missing)')
            else:
                steps.append(f'Registrar o artefato {kind} reaproveitando {"o link" if "url" in ans else "o arquivo"} informado (status stale, sem publicar)')
    steps.extend(act['text'] for act in _file_actions(ctx))
    return steps


def _transform_1_0_0(ctx):
    old = copy.deepcopy(ctx.cfg)
    shared = old.pop('sharedBranch', None)
    base = copy.deepcopy(protolib.DEFAULT_CONFIG)
    base['skill']['version'] = MIGRATIONS['1.0.0']['to']
    for key, val in old.items():
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            base[key].update(val)
        else:
            base[key] = val
    if shared and not (isinstance(old.get('branches'), dict) and 'official' in old['branches']):
        base['branches']['official'] = shared
    base['policy']['promoters'] = ctx.answers['promoters_policy']
    base['docs']['autoMaintain'] = ctx.answers['docs_auto_maintain']

    if _needs_actor(ctx):
        _ensure_actor_member(base, ctx.actor)
    if base['groupMode']:
        owner = ctx.actor['email'] if ctx.actor else None
        for kind in ('official', 'beta'):
            if any(a.get('kind') == kind and a.get('status') != 'revoked' for a in base['artifacts']):
                continue
            ans = ctx.answers[f'artifact_{kind}']
            delivery = 'file' if 'path' in ans else ans.get('delivery', 'claude-artifact')
            base['artifacts'].append(artifacts.new_artifact(
                kind, kind, base['branches'][kind], delivery, owner,
                'missing' if ans.get('create') else 'stale', ans.get('url'), ans.get('path'),
                'Protótipo oficial' if kind == 'official' else 'Protótipo beta',
                'Versão aprovada para o grupo' if kind == 'official' else 'Versão compartilhada para validação'))
    return base


def _ensure_actor_member(cfg, actor):
    if protolib.find_member(cfg, actor['email']):
        return
    now = protolib.now_iso()
    cfg['members'].append({
        'name': actor['name'], 'email': actor['email'], 'roles': ['promoter', 'contributor'],
        'profile': actor['profile'], 'status': 'approved', 'registeredAt': now, 'statusChangedAt': now,
        'statusChangedAtCommit': None,
        'statusHistory': [{'status': 'approved', 'at': now, 'commit': None, 'by': 'setup'}],
        'identityEvidence': actor['evidence']})


def _files_1_0_0(ctx):
    values = {'SKILL_VERSION': ctx.skill_version, 'NAME': ctx.name}
    for act in _file_actions(ctx):
        rel, dest = act['path'], ctx.repo / act['path']
        kind = act['action']
        if kind == 'warn':
            ctx.warnings.append(act['text'])
        elif kind == 'skip':
            ctx.skipped.append(rel)
        elif kind == 'create':
            text = (ctx.templates_dir / rel).read_text(encoding='utf-8')
            for key, val in values.items():
                text = text.replace(f'@@{key}@@', val)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(dest, 'x', encoding='utf-8') as fh:
                    fh.write(text)
            except FileExistsError:
                ctx.skipped.append(rel)
            else:
                ctx.created.append(rel)
        elif kind == 'gitignore-create':
            dest.write_text('# Artefato gerado pelo build.py — nunca versionado\ndist/\n', encoding='utf-8')
            ctx.created.append(rel)
        elif kind == 'gitignore-append':
            current = dest.read_text(encoding='utf-8')
            sep = '' if current.endswith('\n') or not current else '\n'
            dest.write_text(current + sep + 'dist/\n', encoding='utf-8')
            ctx.updated.append(rel)


MIGRATIONS = {
    '1.0.0': {'to': '2.0.0', 'questions': _question_defs, 'plan': _plan_1_0_0,
              'transform': _transform_1_0_0, 'files': _files_1_0_0},
}


# ---------- orquestração ----------

def parse_answers(args):
    """Retorna (respostas, erro)."""
    raw = {}
    try:
        if args.answers:
            raw.update(json.loads(Path(args.answers).read_text(encoding='utf-8')))
        if args.answers_json:
            raw.update(json.loads(args.answers_json))
    except (OSError, json.JSONDecodeError) as e:
        return None, f'respostas ilegíveis: {e}'
    if not isinstance(raw, dict):
        return None, 'as respostas precisam ser um objeto JSON'
    return raw, None


def normalize_answers(raw):
    """Valida/normaliza respostas. Retorna (respostas, problemas)."""
    out, probs = {}, []
    if 'promoters_policy' in raw:
        if raw['promoters_policy'] in POLICIES:
            out['promoters_policy'] = raw['promoters_policy']
        else:
            probs.append(protolib.problem('BAD_ANSWER', f'promoters_policy deve ser {" ou ".join(POLICIES)}'))
    if 'docs_auto_maintain' in raw:
        v = raw['docs_auto_maintain']
        v = {'true': True, 'false': False}.get(v.strip().lower()) if isinstance(v, str) else v
        if isinstance(v, bool):
            out['docs_auto_maintain'] = v
        else:
            probs.append(protolib.problem('BAD_ANSWER', 'docs_auto_maintain deve ser true ou false'))
    for kind in ('official', 'beta'):
        key = f'artifact_{kind}'
        if key not in raw:
            continue
        v = raw[key]
        given = [k for k in ('url', 'path', 'create') if isinstance(v, dict) and v.get(k)]
        if not isinstance(v, dict) or len(given) != 1:
            probs.append(protolib.problem('BAD_ANSWER', f'{key} deve ter exatamente uma chave entre url, path ou create'))
        elif given[0] == 'url' and not (isinstance(v['url'], str) and v['url'].startswith(('http://', 'https://'))):
            probs.append(protolib.problem('BAD_ANSWER', f'{key}.url precisa começar com http:// ou https://'))
        elif given[0] == 'path' and not isinstance(v['path'], str):
            probs.append(protolib.problem('BAD_ANSWER', f'{key}.path precisa ser texto'))
        else:
            out[key] = {k: v[k] for k in given}
            if v.get('delivery') in protolib.DELIVERIES and given[0] == 'create':
                out[key]['delivery'] = v['delivery']
    return out, probs


def required_questions(ctx, steps):
    qs = []
    for st in steps:
        mig = MIGRATIONS.get(st['from']) if st['type'] == 'migration' else None
        if mig:
            qs.extend(q for q in mig['questions'](ctx))
    return qs


def build_actor(args):
    if not (args.actor_name and args.actor_email):
        return None
    return {'name': args.actor_name.strip(), 'email': args.actor_email.strip(),
            'profile': args.actor_profile, 'evidence': args.actor_evidence}


def main(argv=None):
    ap = configtools.JsonArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--execute', action='store_true')
    ap.add_argument('--answers-json')
    ap.add_argument('--answers')
    ap.add_argument('--actor-name')
    ap.add_argument('--actor-email')
    ap.add_argument('--actor-profile', choices=protolib.PROFILES, default='product')
    ap.add_argument('--actor-evidence', choices=protolib.EVIDENCE, default='unverified')
    ap.add_argument('--templates-dir')
    args = ap.parse_args(argv)

    repo = configtools.resolve_repo(args.repo)
    if repo is None:
        return configtools.usage_error(f'pasta não encontrada: {args.repo}')
    if bool(args.actor_name) != bool(args.actor_email):
        return configtools.usage_error('--actor-name e --actor-email devem ser informados juntos')
    raw, err = parse_answers(args)
    if err:
        return configtools.usage_error(err)
    templates_dir = Path(args.templates_dir).expanduser() if args.templates_dir else protolib.skill_root() / 'templates'

    skill_v = protolib.skill_version()
    if skill_v is None:
        return protolib.emit(False, 'SKILL_VERSION_MISSING', problems=[protolib.problem(
            'SKILL_VERSION_MISSING', 'não foi possível ler `version:` no frontmatter do SKILL.md da skill')])

    cfg, err = protolib.load_config(repo)
    if err:
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem('JSON', err)])
    existed = cfg is not None
    if not existed:
        if not (repo / 'index.html').is_file():
            return protolib.emit(False, 'NOT_A_PROTOTYPE', problems=[protolib.problem(
                'NOT_A_PROTOTYPE', 'não há index.html nem prototype.config.json nesta pasta; nada a migrar')])
        cfg = {'groupMode': False, 'remote': 'origin'}
    if not isinstance(cfg, dict):
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem('JSON', 'o config precisa ser um objeto JSON')])

    current = effective_version(cfg)
    cur_t, skill_t = configtools.parse_semver(current), configtools.parse_semver(skill_v)
    if cur_t is None:
        return protolib.emit(False, 'INVALID_CONFIG', problems=[protolib.problem(
            'SCHEMA', f'skill.version inválido ("{current}"): esperado X.Y.Z')])
    base_data = {'skillVersion': skill_v, 'prototypeVersion': current}
    if cur_t > skill_t:
        return protolib.emit(False, 'SKILL_OUTDATED', {**base_data, 'mode': 'consult'}, [protolib.problem(
            'SKILL_OUTDATED', f'o protótipo é da versão {current}, mais nova que a skill instalada ({skill_v}); '
                              'atualize a skill — nada foi alterado')])
    if cur_t == skill_t and existed:
        return protolib.emit(True, 'UP_TO_DATE', {**base_data, 'steps': []})

    answers, probs = normalize_answers(raw)
    if probs:
        return protolib.emit(False, 'BAD_ANSWERS', base_data, probs)
    actor = build_actor(args)
    ctx = Ctx(repo, cfg, answers, actor, templates_dir, skill_v)
    steps = pending_steps(current, skill_v)
    descriptions = []
    for st in steps:
        if st['type'] == 'migration':
            descriptions.extend(MIGRATIONS[st['from']]['plan'](ctx, existed))
        else:
            descriptions.append(f'Atualizar skill.version de {st["from"]} para {st["to"]}')
    unanswered = [q for q in required_questions(ctx, steps) if q['id'] not in answers]
    data = {**base_data, 'migrationsPending': steps, 'steps': descriptions,
            'requiresActor': _needs_actor(ctx) if steps else False,
            'groupMode': ctx.group_mode}

    if not args.execute:
        return protolib.emit(True, 'PLAN', data, questions=unanswered)

    if unanswered:
        return protolib.emit(False, 'NEEDS_ANSWERS', data, [protolib.problem(
            'NEEDS_ANSWERS', 'faltam respostas: ' + ', '.join(q['id'] for q in unanswered))], unanswered)
    if _needs_actor(ctx) and actor is None:
        return protolib.emit(False, 'NEEDS_ACTOR', data, [protolib.problem(
            'NEEDS_ACTOR', 'informe --actor-name e --actor-email: quem migra entra como membro approved + promoter')])
    if actor is not None and cfg.get('members'):
        member = protolib.find_member(cfg, actor['email'])
        if not protolib.is_promoter(member):
            return protolib.emit(False, 'NOT_PROMOTER', data, [protolib.problem(
                'NOT_PROMOTER', f'"{actor["email"]}" não é promoter aprovado; só um promoter migra o protótipo')])

    working = ctx.cfg
    for st in steps:
        if st['type'] == 'migration':
            ctx.cfg = working = MIGRATIONS[st['from']]['transform'](ctx)
        working.setdefault('skill', {'name': protolib.SKILL_NAME})
        working['skill']['version'] = st['to']

    validator = configtools.load_script('config-validate.py')
    status, _, problems = validator.validate_config(working)
    if status != 'VALID':
        return protolib.emit(False, 'INVALID', {**data, 'written': False}, problems)

    for st in steps:
        if st['type'] == 'migration':
            MIGRATIONS[st['from']]['files'](ctx)
    configtools.atomic_save_config(repo, working)
    data.update({'created': ctx.created + ([] if existed else [protolib.CONFIG_NAME]),
                 'updated': ctx.updated + ([protolib.CONFIG_NAME] if existed else []),
                 'skipped': ctx.skipped, 'warnings': ctx.warnings, 'from': current, 'to': skill_v})
    return protolib.emit(True, 'MIGRATED', data)


if __name__ == '__main__':
    sys.exit(main())
