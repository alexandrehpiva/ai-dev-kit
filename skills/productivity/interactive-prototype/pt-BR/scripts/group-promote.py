#!/usr/bin/env python3
"""Promove a beta para a versão oficial (o que o cliente vê), no modo grupo v2.

Só stdlib. Padrão é DRY-RUN: devolve `data.willReachClient` (o que irá ao cliente, por autor) e a versão
calculada, sem escrever nada. `--execute` realiza. Só promoter aprovado.

  python3 group-promote.py --repo . --actor-email ana@example.test [--bump auto|patch|minor|major]
  python3 group-promote.py ... --urgent [--commit SHA ...]     # correção pequena direto na oficial
  python3 group-promote.py ... --restore-version v1.2.0        # volta o conteúdo de uma versão anterior
  python3 group-promote.py ... --sync-beta                     # integra a oficial na beta (beta ⊇ oficial)

Promoção normal: commit na beta (betas do changelog consolidadas em UMA entrada oficial, badge vX.Y.Z,
build, trailer Prototype-Promotion) → push da beta → fast-forward da oficial (`push <beta>:<official>`).
Nunca force: recusa ⇒ PUSH_REJECTED. Se a beta já tem o commit de promoção e só a oficial ficou para trás,
a execução apenas conclui o fast-forward (status RESUMED).

Bump auto: minor se a beta adiciona arquivo em js/screens/ ou js/components/; senão patch. Major só
com --bump major.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import changelog_tools as ct  # noqa: E402
import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import git, problem  # noqa: E402

URGENT_MAX_FILES = 5
NEW_UI_DIRS = ('js/screens/', 'js/components/')
RESTORE_KEEP = (protolib.CONFIG_NAME, ct.CHANGELOG_REL)


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email', required=True)
    ap.add_argument('--bump', choices=('auto', 'patch', 'minor', 'major'), default='auto')
    ap.add_argument('--execute', action='store_true')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--urgent', action='store_true')
    mode.add_argument('--restore-version')
    mode.add_argument('--sync-beta', action='store_true')
    ap.add_argument('--commit', action='append', default=[],
                    help='(--urgent) commit(s) a levar à oficial; padrão: os do rascunho do ator')
    ap.add_argument('--reason', help='(--restore-version) motivo, vai no trailer Prototype-Rollback-Reason')
    ap.add_argument('--max-retries', type=int, default=3)
    return ap.parse_args(argv)


def fail(status, probs, data=None):
    return protolib.emit(False, status, data=data, problems=probs)


class Ctx:
    def __init__(self, repo, args, cfg, member):
        self.repo, self.args, self.cfg, self.member = repo, args, cfg, member
        self.remote = cfg.get('remote', 'origin')
        self.beta, self.official = cfg['branches']['beta'], cfg['branches']['official']
        self.beta_ref, self.official_ref = f'{self.remote}/{self.beta}', f'{self.remote}/{self.official}'
        self.trailers = gs.actor_trailers(member)
        self.data = {'actor': protolib.norm_email(args.actor_email), 'identityEvidence': gs.evidence(member)}
        if gs.evidence(member) == 'git-only':
            self.data['extraConfirmation'] = True


# ---------------------------------------------------------------- plano

def group_by_actor(cfg, commits):
    groups = {}
    for c in commits:
        if gs.BUMP_SUBJECT_RE.match(c['subject']) or c['subject'].startswith('merge(prototype):'):
            continue
        groups.setdefault(c['actor'], []).append(c)
    by_actor, pending = [], []
    for actor, items in groups.items():
        m = protolib.find_member(cfg, actor) or {}
        status = m.get('status', 'unknown')
        if status != 'approved':
            pending.append({'email': actor, 'status': status})
        by_actor.append({'actor': actor, 'name': m.get('name'), 'memberStatus': status,
                         'identityEvidence': gs.evidence(m) if m else 'unverified',
                         'commits': [{'sha': c['sha'][:10], 'subject': c['subject'], 'date': c['date']}
                                     for c in items]})
    return by_actor, pending


def auto_level(repo, old, new):
    names = gs.out(repo, 'diff', '--name-status', '--no-renames', old, new) if old else ''
    added = [line.split('\t', 1)[1] for line in (names or '').splitlines() if line.startswith('A\t')]
    return 'minor' if any(p.startswith(NEW_UI_DIRS) for p in added) else 'patch'


def next_official(entries, level):
    base = ct.last_official(entries) or 'v0.0.0'
    return protolib.format_version(*protolib.bump(protolib.parse_version(base), level))


def is_promotion_commit(repo, sha):
    body = gs.out(repo, 'log', '-1', '--format=%B', sha) or ''
    return protolib.parse_trailers(body).get(protolib.T_PROMOTION)


def normal_plan(c):
    repo, ob, om = c.repo, gs.rev(c.repo, c.beta_ref), gs.rev(c.repo, c.official_ref)
    if ob is None:
        return None, [problem('BETA_MISSING', f'{c.beta_ref} não existe: ninguém compartilhou na beta ainda.')]
    if om and not gs.is_ancestor(repo, om, ob):
        return None, [problem('INVARIANT_BROKEN', f'A oficial tem commits que a beta não tem; rode antes '
                              f'--sync-beta para integrar {c.official_ref} na beta.')]
    resume = is_promotion_commit(repo, ob) if om != ob else None
    commits = gs.commit_log(repo, f'{om}..{ob}' if om else ob)
    by_actor, pending = group_by_actor(c.cfg, commits)
    entries = gs.entries_at(repo, ob)
    if resume:
        version, level = resume, None
    else:
        level = c.args.bump if c.args.bump != 'auto' else auto_level(repo, om, ob)
        version = next_official(entries, level)
    preview = ct.consolidate_betas(entries, version, gs.today())
    plan = {'kind': 'resume' if resume else 'promote', 'version': version, 'bumpLevel': level,
            'betaSha': ob, 'officialSha': om,
            'willReachClient': {'commitCount': sum(len(a['commits']) for a in by_actor), 'byActor': by_actor,
                                'pendingMembers': pending,
                                'files': (gs.out(repo, 'diff', '--name-only', om, ob) or '').splitlines()
                                if om else [],
                                'changelog': next((e['changes'] for e in preview if e['version'] == version), [])}}
    if om == ob:
        return plan, [problem('NOTHING_TO_PROMOTE', 'A beta é igual à oficial: nada novo para o cliente.')]
    return plan, []


def find_promotion(repo, version, refs):
    for ref in refs:
        if not gs.rev(repo, ref):
            continue
        for item in gs.commit_log(repo, ref, no_merges=False):
            if item['trailers'].get(protolib.T_PROMOTION) == version:
                return item['sha']
    tag = gs.rev(repo, f'refs/tags/{version}')
    return tag


def restore_plan(c):
    repo, ob, om = c.repo, gs.rev(c.repo, c.beta_ref), gs.rev(c.repo, c.official_ref)
    target_v = c.args.restore_version
    if not protolib.parse_version(target_v) or protolib.parse_version(target_v)[3] is not None:
        return None, [problem('BAD_VERSION', f'"{target_v}" não é uma versão oficial vX.Y.Z.')]
    if ob is None:
        return None, [problem('BETA_MISSING', f'{c.beta_ref} não existe.')]
    if om and not gs.is_ancestor(repo, om, ob):
        return None, [problem('INVARIANT_BROKEN', 'A oficial tem commits que a beta não tem; rode --sync-beta antes.')]
    target = find_promotion(repo, target_v, (c.official_ref, c.beta_ref))
    if not target:
        return None, [problem('VERSION_NOT_FOUND', f'Nenhum commit com {protolib.T_PROMOTION}: {target_v}.')]
    level = c.args.bump if c.args.bump != 'auto' else 'patch'
    version = next_official(gs.entries_at(repo, ob), level)
    undone = gs.commit_log(repo, f'{target}..{ob}')
    by_actor, pending = group_by_actor(c.cfg, undone)
    return {'kind': 'restore', 'version': version, 'bumpLevel': level, 'restoreFrom': target_v,
            'restoreCommit': target, 'betaSha': ob, 'officialSha': om,
            'willReachClient': {'summary': f'conteúdo de {target_v} publicado como {version}',
                                'undoes': by_actor, 'pendingMembers': pending,
                                'files': (gs.out(repo, 'diff', '--name-only', target, ob, '--', '.',
                                                 *[f':(exclude){p}' for p in RESTORE_KEEP + ('dist',)]) or '')
                                .splitlines()}}, []


def urgent_commits(c):
    if c.args.commit:
        shas = [gs.rev(c.repo, s) for s in c.args.commit]
        if None in shas:
            return None, [problem('BAD_COMMIT', 'Algum --commit não existe neste repositório.')]
        return [x for s in shas for x in gs.commit_log(c.repo, s, no_merges=True, limit=1)], []
    draft = protolib.draft_branch(c.cfg, c.args.actor_email)
    ref = next((r for r in (draft, f'{c.remote}/{draft}') if gs.rev(c.repo, r)), None)
    if not ref:
        return None, [problem('NO_URGENT_COMMIT', f'Rascunho {draft} não encontrado; informe --commit.')]
    actor = protolib.norm_email(c.args.actor_email)
    items = [x for x in gs.commit_log(c.repo, f'{c.official_ref}..{ref}')
             if x['actor'] == actor and not gs.BUMP_SUBJECT_RE.match(x['subject'])]
    items.reverse()
    if not items:
        return None, [problem('NO_URGENT_COMMIT', f'Nenhum commit seu em {ref} fora da oficial; informe --commit.')]
    return items, []


def urgent_plan(c):
    repo = c.repo
    om = gs.rev(repo, c.official_ref)
    if om is None:
        return None, [problem('OFFICIAL_MISSING', f'{c.official_ref} não existe.')]
    if c.args.bump in ('minor', 'major'):
        return None, [problem('URGENT_PATCH_ONLY', 'Correção urgente é sempre patch; use a promoção normal.')]
    commits, probs = urgent_commits(c)
    if probs:
        return None, probs
    files, added_screens = set(), []
    for x in commits:
        for line in (gs.out(repo, 'show', '--name-status', '--no-renames', '--format=', x['sha']) or '').splitlines():
            st, path = line.split('\t', 1)
            if gs.is_dist(path) or path == ct.CHANGELOG_REL:
                continue
            files.add(path)
            if st == 'A' and path.startswith('js/screens/'):
                added_screens.append(path)
    version = next_official(gs.entries_at(repo, om), 'patch')
    by_actor, pending = group_by_actor(c.cfg, commits)
    plan = {'kind': 'urgent', 'version': version, 'bumpLevel': 'patch', 'officialSha': om,
            'hotfixBranch': f'hotfix/{protolib.slug_member(c.args.actor_email)}',
            'commits': [x['sha'] for x in commits],
            'willReachClient': {'commitCount': len(commits), 'byActor': by_actor, 'pendingMembers': pending,
                                'files': sorted(files)}}
    if len(files) > URGENT_MAX_FILES or added_screens:
        why = (f'toca {len(files)} arquivos (máximo {URGENT_MAX_FILES})' if len(files) > URGENT_MAX_FILES
               else 'adiciona tela nova: ' + ', '.join(added_screens))
        return plan, [problem('NOT_URGENT_SIZED', f'Não cabe como correção urgente: {why}. Use a promoção normal.')]
    return plan, []


# ---------------------------------------------------------------- execução

def require_clean(c):
    if gs.operation_in_progress(c.repo):
        return problem('OPERATION_IN_PROGRESS', 'Há uma operação git em andamento; conclua ou aborte antes.')
    if gs.status_paths(c.repo, untracked=False):
        return problem('WORKTREE_DIRTY', 'Há mudanças não commitadas; compartilhe ou guarde antes de promover.')
    return None


def promotion_commit(c, version, entries, subject_extra=''):
    prob, warnings = gs.apply_version(c.repo, version, entries)
    if prob:
        return None, prob, warnings
    trailers = dict(c.trailers)
    trailers[protolib.T_PROMOTION] = version
    sha = gs.commit_paths(c.repo, [ct.CHANGELOG_REL, ct.INDEX_REL], f'chore(prototype): promote {version}'
                          + subject_extra, trailers)
    return sha, None, warnings


def push_official(c, sha):
    st, err = gs.push(c.repo, c.remote, f'{sha}:refs/heads/{c.official}')
    return st, err


def execute_promote(c, plan):
    repo, data = c.repo, c.data
    data.update(version=plan['version'])
    orig = gs.current_branch(repo) or gs.rev(repo, 'HEAD')
    if plan['kind'] == 'resume':
        st, err = push_official(c, plan['betaSha'])
        if st != 'ok':
            return fail('PUSH_REJECTED' if st == 'rejected' else 'NOT_SYNCED',
                        [problem('PUSH_REJECTED', f'Fast-forward da oficial recusado: {err}')], data)
        data.update(betaSha=plan['betaSha'], officialSha=plan['betaSha'],
                    artifactsToUpdate=gs.artifacts_of(c.cfg, ('official', 'beta')))
        return protolib.emit(True, 'RESUMED', data=data)
    ok, why = gs.checkout_synced(repo, c.beta, c.beta_ref)
    if not ok:
        gs.switch_back(repo, orig)
        return fail('BETA_DIVERGED', [problem('BETA_DIVERGED', f'A beta local precisa ser igual a {c.beta_ref}: {why}')],
                    data)
    start = gs.rev(repo, 'HEAD')
    warnings = []
    if plan['kind'] == 'restore':
        r = git(repo, 'restore', f'--source={plan["restoreCommit"]}', '--staged', '--worktree', '--', '.',
                *[f':(exclude){p}' for p in RESTORE_KEEP], ':(exclude)dist')
        if r.returncode != 0 or git(repo, 'diff', '--cached', '--quiet').returncode == 0:
            git(repo, 'checkout', '-q', 'HEAD', '--', '.')
            gs.switch_back(repo, orig)
            return fail('NOTHING_TO_RESTORE', [problem('NOTHING_TO_RESTORE', r.stderr.strip() or
                        f'O conteúdo atual já é igual ao de {plan["restoreFrom"]}.')], data)
        undone = [x['sha'][:10] for x in gs.commit_log(repo, f'{plan["restoreCommit"]}..HEAD')]
        tr = dict(c.trailers)
        tr[protolib.T_ROLLBACK_OF] = ','.join(undone)
        tr[protolib.T_ROLLBACK_REASON] = c.args.reason or f'restaurar {plan["restoreFrom"]}'
        r = protolib.commit_with_trailers(repo, f'revert(prototype): restaura o conteúdo de {plan["restoreFrom"]}', tr)
        if r.returncode != 0:
            gs.rollback_to(repo, start)
            gs.switch_back(repo, orig)
            return fail('COMMIT_FAILED', [problem('COMMIT_FAILED', r.stderr.strip())], data)
        data['restoreSha'] = gs.rev(repo, 'HEAD')
        entries = ct.read_entries(repo)
        undone_betas = [e['version'] for e in entries if ct.is_beta(e)]
        lines = [f'Restaura o conteúdo da versão {plan["restoreFrom"]}.']
        if undone_betas:
            lines.append('Desfaz as betas: ' + ', '.join(undone_betas) + '.')
        entries = ct.consolidate_betas(entries, plan['version'], gs.today(), changes=lines)
    else:
        entries = ct.consolidate_betas(ct.read_entries(repo), plan['version'], gs.today())
    sha, prob, warnings = promotion_commit(c, plan['version'], entries)
    if prob or not sha:
        gs.rollback_to(repo, start)
        gs.switch_back(repo, orig)
        prob = prob or problem('COMMIT_FAILED', 'Commit de promoção vazio.')
        return fail(prob['code'], [prob] + warnings, data)
    st, err = gs.push(repo, c.remote, f'HEAD:refs/heads/{c.beta}')
    if st != 'ok':
        gs.rollback_to(repo, start)
        gs.switch_back(repo, orig)
        return fail('PUSH_REJECTED' if st == 'rejected' else 'NOT_SYNCED',
                    [problem('PUSH_REJECTED' if st == 'rejected' else 'NOT_SYNCED',
                             f'Envio da beta recusado ({err or st}); nada foi forçado e a promoção foi desfeita '
                             'localmente. Rode de novo.')], data)
    data['betaSha'] = sha
    st, err = push_official(c, sha)
    gs.switch_back(repo, orig)
    if st != 'ok':
        return fail('PUSH_REJECTED', [problem('PUSH_REJECTED', f'A beta já tem a promoção, mas o fast-forward da '
                    f'oficial foi recusado ({err or st}). Rode de novo para concluir (status RESUMED).')], data)
    data.update(officialSha=sha, artifactsToUpdate=gs.artifacts_of(c.cfg, ('official', 'beta')))
    return protolib.emit(True, 'RESTORED' if plan['kind'] == 'restore' else 'PROMOTED', data=data, problems=warnings)


def sync_beta(c):
    """Integra a oficial na beta (merge + nova beta.N), com nova tentativa se a beta andar no meio."""
    repo = c.repo
    for attempt in range(1, c.args.max_retries + 2):
        ok, err = gs.fetch(repo, c.remote)
        if not ok:
            return 'offline', {'error': err}
        ok, why = gs.checkout_synced(repo, c.beta, c.beta_ref)
        if not ok:
            return 'diverged', {'error': why}
        start = gs.rev(repo, 'HEAD')
        res = gs.integrate(repo, c.official_ref, f'merge(prototype): integra {c.official_ref} na beta', c.trailers)
        if res['status'] in ('conflicts', 'error'):
            return res['status'], res
        if res['status'] == 'up-to-date':
            return 'up-to-date', {'betaSha': start}
        entries = ct.read_entries(repo)
        base = ct.last_official(entries) or 'v0.0.0'
        version = f'{base}-beta.{ct.next_beta_number(entries, base)}'
        entries = ct.sort_entries(entries + [{'version': version, 'date': gs.today(),
                                              'changes': [f'Integra a versão oficial {base} na beta.']}])
        prob, _ = gs.apply_version(repo, version, entries)
        if prob:
            gs.rollback_to(repo, start)
            return 'build-failed', {'problem': prob}
        gs.commit_paths(repo, [ct.CHANGELOG_REL, ct.INDEX_REL], f'chore(prototype): bump version to {version}',
                        c.trailers)
        st, err = gs.push(repo, c.remote, f'HEAD:refs/heads/{c.beta}')
        if st == 'ok':
            return 'ok', {'betaVersion': version, 'betaSha': gs.rev(repo, 'HEAD'), 'attempts': attempt}
        gs.rollback_to(repo, start)
        if st == 'offline':
            return 'offline', {'error': err}
    return 'rejected', {}


def report_sync(c, status, info, orig, base_status='SYNCED'):
    gs.switch_back(c.repo, orig)
    data = c.data
    if status in ('ok', 'up-to-date'):
        data.update({k: v for k, v in info.items() if k in ('betaVersion', 'betaSha')})
        data['artifactsToUpdate'] = gs.artifacts_of(c.cfg, ('official', 'beta'))
        return protolib.emit(True, base_status, data=data)
    if status == 'conflicts':
        data['conflicts'] = info['conflicts']
        return fail('CONFLICTS', [problem('CONFLICTS', 'Conflito perceptível ao integrar a oficial na beta; merge '
                    'desfeito. Resolva com o usuário e rode --sync-beta.')], data)
    msg = {'offline': 'Sem conexão com o remoto.', 'diverged': f'Beta local divergente: {info.get("error")}',
           'rejected': 'A beta mudou durante o envio repetidas vezes; nada foi forçado.',
           'build-failed': (info.get('problem') or {}).get('message', 'build falhou'),
           'error': f'Merge falhou: {info.get("error")}'}[status]
    code = {'offline': 'NOT_SYNCED', 'diverged': 'BETA_DIVERGED', 'rejected': 'PUSH_REJECTED',
            'build-failed': 'BUILD_FAILED', 'error': 'MERGE_FAILED'}[status]
    return fail(code, [problem(code, msg)], data)


def execute_urgent(c, plan):
    repo, data = c.repo, c.data
    data['version'] = plan['version']
    orig = gs.current_branch(repo) or gs.rev(repo, 'HEAD')
    hotfix = plan['hotfixBranch']
    if gs.rev(repo, hotfix):
        return fail('HOTFIX_BRANCH_EXISTS', [problem('HOTFIX_BRANCH_EXISTS', f'{hotfix} já existe localmente; '
                    'conclua ou remova esse branch antes.')], data)
    r = git(repo, 'checkout', '-q', '-b', hotfix, plan['officialSha'])
    if r.returncode != 0:
        return fail('CHECKOUT_FAILED', [problem('CHECKOUT_FAILED', r.stderr.strip())], data)

    def abandon():
        gs.switch_back(repo, orig)
        git(repo, 'branch', '-q', '-D', hotfix)

    for sha in plan['commits']:
        r = git(repo, 'cherry-pick', '-x', sha)
        if r.returncode == 0:
            continue
        if not (gs.git_dir(repo) / 'CHERRY_PICK_HEAD').exists():
            abandon()
            return fail('CHERRY_PICK_FAILED', [problem('CHERRY_PICK_FAILED', r.stderr.strip())], data)
        _, perceptible, _ = gs.resolve_unmerged(repo)
        if perceptible:
            data['conflicts'] = gs.conflict_report(repo, perceptible, 'HEAD', sha)
            git(repo, 'cherry-pick', '--abort')
            abandon()
            return fail('CONFLICTS', [problem('CONFLICTS', 'O commit não aplica limpo na oficial; correção urgente '
                        'cancelada sem mudar nada. Use a promoção normal ou ajuste o commit.')], data)
        if git(repo, 'diff', '--cached', '--quiet').returncode == 0:
            git(repo, 'cherry-pick', '--skip')
        else:
            r = git(repo, '-c', 'core.editor=true', 'cherry-pick', '--continue')
            if r.returncode != 0:
                git(repo, 'cherry-pick', '--abort')
                abandon()
                return fail('CHERRY_PICK_FAILED', [problem('CHERRY_PICK_FAILED', r.stderr.strip())], data)
    err = gs.normalize_changelog_worktree(repo)
    if err:
        abandon()
        return fail('CHANGELOG_INVALID', [problem('CHANGELOG_INVALID', err)], data)
    if gs.status_paths(repo, (ct.CHANGELOG_REL,), untracked=False):
        gs.commit_paths(repo, [ct.CHANGELOG_REL], 'chore(prototype): normaliza changelog', c.trailers)
    subjects = [x['subject'] for x in gs.commit_log(repo, f'{plan["officialSha"]}..HEAD')]
    entries = ct.rename_pending(ct.read_entries(repo), plan['version'], gs.today(), fallback_changes=subjects)
    entries = [e for e in entries if not ct.is_beta(e)]
    sha, prob, warnings = promotion_commit(c, plan['version'], entries, ' (urgente)')
    if prob or not sha:
        abandon()
        prob = prob or problem('COMMIT_FAILED', 'Commit de promoção vazio.')
        return fail(prob['code'], [prob] + warnings, data)
    st, err = push_official(c, sha)
    if st != 'ok':
        abandon()
        return fail('PUSH_REJECTED' if st == 'rejected' else 'NOT_SYNCED',
                    [problem('PUSH_REJECTED' if st == 'rejected' else 'NOT_SYNCED',
                             f'Envio da oficial recusado ({err or st}); nada foi forçado.')], data)
    data['officialSha'] = sha
    git(repo, 'checkout', '-q', '--detach')
    git(repo, 'branch', '-q', '-D', hotfix)
    status, info = sync_beta(c)
    data['betaIntegration'] = status
    if status in ('ok', 'up-to-date'):
        return report_sync(c, status, info, orig, base_status='PROMOTED_URGENT')
    # A oficial já foi publicada; a falha aqui é só na integração dela na beta (rodar --sync-beta).
    return report_sync(c, status, info, orig)


def main(argv=None):
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        return fail('NOT_A_REPO', [problem('NOT_A_REPO', f'{repo} não é um repositório git.')])
    cfg, err = protolib.load_config(repo)
    probs = gs.check_group_config(cfg, err)
    if probs:
        return fail('INVALID_CONFIG', probs)
    member = protolib.find_member(cfg, args.actor_email)
    if not protolib.is_promoter(member):
        return fail('NOT_PROMOTER', [problem('NOT_PROMOTER', f'{args.actor_email} não é promoter aprovado; só '
                    'promoter aprovado publica para o cliente.')], {'memberStatus': (member or {}).get('status')})
    c = Ctx(repo, args, cfg, member)

    if args.execute:
        p = require_clean(c)
        if p:
            return fail(p['code'], [p], c.data)
        ok, e = gs.fetch(repo, c.remote)
        if not ok:
            return fail('NOT_SYNCED', [problem('NOT_SYNCED', f'Sem conexão com o remoto; nada foi feito. {e}')],
                        c.data)

    if args.sync_beta:
        if not args.execute:
            c.data['plan'] = {'kind': 'sync-beta', 'steps': [f'merge de {c.official_ref} na beta', 'nova beta.N',
                                                              f'push de {c.beta_ref}']}
            return protolib.emit(True, 'DRY_RUN', data=c.data)
        orig = gs.current_branch(repo) or gs.rev(repo, 'HEAD')
        status, info = sync_beta(c)
        return report_sync(c, status, info, orig)

    planner = urgent_plan if args.urgent else (restore_plan if args.restore_version else normal_plan)
    plan, probs = planner(c)
    if plan:
        c.data['plan'] = plan
        c.data['version'] = plan['version']
        c.data['willReachClient'] = plan['willReachClient']
    if not args.execute:
        live_b = gs.ls_remote_head(repo, c.remote, c.beta)
        c.data['remoteTrackingFresh'] = None if live_b is None else live_b == (gs.rev(repo, c.beta_ref) or '')
        if probs:
            return fail(probs[0]['code'], probs, c.data)
        return protolib.emit(True, 'DRY_RUN', data=c.data)
    if probs:
        return fail(probs[0]['code'], probs, c.data)
    return execute_urgent(c, plan) if args.urgent else execute_promote(c, plan)


if __name__ == '__main__':
    sys.exit(main())
