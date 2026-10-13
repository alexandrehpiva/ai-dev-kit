#!/usr/bin/env python3
"""Compartilha o trabalho do membro na beta (modo grupo v2) ou só salva o rascunho pessoal.

Só stdlib. Padrão é DRY-RUN (devolve `data.plan` e não escreve nada); `--execute` realiza.

  python3 group-share.py --repo . --actor-email ana@example.test                 # plano
  python3 group-share.py --repo . --actor-email ana@example.test --execute       # compartilha na beta
  python3 group-share.py --repo . --actor-email ana@example.test --mode save-only --execute

Sequência `share`: rascunho `draft/<membro>` (criado de origin/beta) → commit do lote com trailers →
fetch → merge de origin/beta (sem rebase; conflitos mecânicos resolvidos sozinhos, perceptíveis abortam o
merge e voltam como CONFLICTS; com `--decisions <json>` as decisões do usuário entram no merge e no trailer
Prototype-Conflict-Decision) → versão `vX.Y.Z-beta.N` (Pendente renomeada só aqui) + badge + build →
commit do bump → push da beta e do rascunho (sem force; não fast-forward ⇒ refaz desde o fetch).
Sem rede: o commit local fica feito e o status é NOT_SYNCED, sem número de versão.

Status: DRY_RUN, SHARED, SAVED, NOT_SYNCED, CONFLICTS, PUSH_REJECTED, BUILD_FAILED, JS_CHECK_FAILED,
NOT_ALLOWED, VETTING_REQUIRED, NOTHING_TO_SHARE, INVALID_CONFIG, ...
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import changelog_tools as ct  # noqa: E402
import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import git, problem  # noqa: E402

ALLOWED_STATUSES = ('approved', 'pending')


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email', required=True)
    ap.add_argument('--mode', choices=('share', 'save-only'), default='share')
    ap.add_argument('--paths', nargs='+')
    ap.add_argument('--message')
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--max-retries', type=int, default=3)
    ap.add_argument('--decisions', help='JSON com as decisões do usuário sobre conflitos perceptíveis: '
                    '{"decisions":[{"path","keep":"mine|theirs|combined","what","file"}]} (mine = seu rascunho; theirs = a '
                    'beta; combined = grava o conteúdo final do arquivo `file` (relativo ao JSON); no config só promoter, e membros/artefatos vêm da fusão dos dois lados)')
    ap.add_argument('--vetting-done', action='store_true',
                    help='só libera o bloqueio VETTING_REQUIRED (promoter com membros pendentes); não grava nada. '
                    'Não vale para --mode save-only, que nunca é bloqueado')
    return ap.parse_args(argv)


def pending_lines(repo):
    try:
        for e in ct.read_entries(repo):
            if ct.is_pending(e):
                return e.get('changes', [])
    except (ct.ChangelogError, FileNotFoundError):
        pass
    return []


def default_subject(repo, actor):
    lines = pending_lines(repo)
    if lines:
        first = lines[0].strip().rstrip('.')
        return 'feat(prototype): ' + (first[:68] + '…' if len(first) > 69 else first)
    return f'feat(prototype): alterações de {protolib.slug_member(actor)}'


def files_to_commit(repo, paths):
    items = gs.status_paths(repo, tuple(paths) if paths else ('.',))
    files = sorted({p for _, p in items if not gs.is_dist(p)})
    excluded = sorted({p for _, p in items if gs.is_dist(p)})
    if paths:
        changelog_dirty = any(p == ct.CHANGELOG_REL for _, p in gs.status_paths(repo, (ct.CHANGELOG_REL,)))
        if changelog_dirty and ct.CHANGELOG_REL not in files:
            files.append(ct.CHANGELOG_REL)
    return files, excluded


def preview_version(repo, remote, beta):
    try:
        ours = ct.read_entries(repo)
    except (ct.ChangelogError, FileNotFoundError):
        ours = []
    entries = ct.union_entries(ours, gs.entries_at(repo, f'{remote}/{beta}'))
    base = ct.last_official(entries) or 'v0.0.0'
    n = ct.next_beta_number(entries, base)
    return f'{base}-beta.{n}'


def build_plan(repo, args, cfg, member, draft):
    remote, beta = cfg.get('remote', 'origin'), cfg['branches']['beta']
    files, excluded = files_to_commit(repo, args.paths)
    local_draft = gs.rev(repo, draft)
    remote_draft = gs.rev(repo, f'{remote}/{draft}')
    head_ref = draft if local_draft else ('HEAD' if gs.current_branch(repo) == draft else None)
    tracking = gs.rev(repo, f'{remote}/{beta}')
    from_beta = []
    if tracking:
        base_ref = head_ref or 'HEAD'
        from_beta = [{'sha': c['sha'][:10], 'subject': c['subject'], 'actor': c['actor']}
                     for c in gs.commit_log(repo, f'{base_ref}..{tracking}')]
    live = gs.ls_remote_head(repo, remote, beta)
    share = args.mode == 'share'
    steps = [
        f'garantir o rascunho {draft} ' + ('(já existe)' if local_draft or remote_draft
                                           else f'(criado a partir de {remote}/{beta})'),
        f'commit do lote ({len(files)} arquivo(s); dist/ fica de fora) com trailers de autoria',
    ]
    if share:
        steps += [f'git fetch {remote}', f'merge de {remote}/{beta} no rascunho (sem rebase, sem force)',
                  'renomear a entrada Pendente para a versão beta, atualizar o badge e regerar (build.py)',
                  'commit do bump de versão',
                  f'push para {remote}/{beta} e para {remote}/{draft} (não fast-forward ⇒ repete desde o fetch)']
    else:
        steps += [f'push só do rascunho para {remote}/{draft} (sem número de versão, beta intocada)']
    return {
        'mode': args.mode,
        'draftBranch': draft,
        'draftExists': {'local': bool(local_draft), 'remote': bool(remote_draft)},
        'currentBranch': gs.current_branch(repo),
        'filesToCommit': files,
        'excludedFromCommit': excluded,
        'pendingChanges': pending_lines(repo),
        'commitsFromBeta': from_beta,
        'betaVersion': preview_version(repo, remote, beta) if share else None,
        'versionIsProvisional': share,
        'remoteTrackingFresh': None if live is None else (live == (tracking or '')),
        'commitSubject': args.message or default_subject(repo, args.actor_email),
        'steps': steps,
    }


def ensure_draft(repo, remote, beta, official, draft):
    if gs.current_branch(repo) == draft:
        return True, ''
    if gs.rev(repo, draft):
        r = git(repo, 'checkout', '-q', draft)
    elif gs.rev(repo, f'{remote}/{draft}'):
        r = git(repo, 'checkout', '-q', '-b', draft, '--track', f'{remote}/{draft}')
    else:
        start = next((ref for ref in (f'{remote}/{beta}', f'{remote}/{official}') if gs.rev(repo, ref)), 'HEAD')
        r = git(repo, 'checkout', '-q', '-b', draft, start)
        if r.returncode != 0 and start != 'HEAD':
            # Mudanças feitas sobre um checkout desatualizado não "pulam" para a beta nova; o rascunho nasce no
            # HEAD atual (contido na beta) e o passo de integração traz a beta com a classificação de conflitos.
            r = git(repo, 'checkout', '-q', '-b', draft)
    return r.returncode == 0, r.stderr.strip()


def stage_batch(repo, paths):
    specs = [p for p in paths if not gs.is_dist(p.lstrip('./'))] if paths else ['.']
    if paths and ct.CHANGELOG_REL not in specs and gs.status_paths(repo, (ct.CHANGELOG_REL,)):
        specs.append(ct.CHANGELOG_REL)
    if not specs:
        return False
    # Sem pathspec de exclusão: o git recusa `:(exclude)dist` quando dist/ existe e está no .gitignore.
    git(repo, 'add', '-A', '--', *specs, check=True)
    if gs.out(repo, 'diff', '--cached', '--name-only', '--', 'dist'):
        git(repo, 'reset', '-q', '--', 'dist')
    return git(repo, 'diff', '--cached', '--quiet').returncode != 0


def fail(status, probs, data=None, questions=None):
    return protolib.emit(False, status, data=data, problems=probs, questions=questions)


def load_decisions(path):
    """Lê o arquivo de decisões. Devolve ({path: {keep, what}}, mensagem de erro|None)."""
    if not path:
        return None, None
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        items = raw['decisions']
        out = {}
        for it in items:
            keep, what, rel = it['keep'], gs.clean_decision_text(it['what']), str(it['path']).removeprefix('./')
            if keep not in ('mine', 'theirs', 'combined') or not what:
                raise ValueError(f'decisão inválida para {rel}: keep deve ser mine|theirs|combined e what não '
                                 'pode ser vazio')
            out[rel] = {'keep': keep, 'what': what}
            if keep == 'combined':
                fpath = Path(it['file'])
                if not fpath.is_absolute():
                    fpath = Path(path).resolve().parent / fpath
                out[rel]['content'] = fpath.read_text(encoding='utf-8')
        return out, None
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, f'arquivo de decisões inválido ({e})'


def execute(repo, args, cfg, member, draft):
    decisions, derr = load_decisions(args.decisions)
    if derr:
        return fail('INVALID_DECISIONS', [problem('INVALID_DECISIONS', derr)])
    remote = cfg.get('remote', 'origin')
    beta, official = cfg['branches']['beta'], cfg['branches']['official']
    trailers = gs.actor_trailers(member)
    data = {'mode': args.mode, 'draftBranch': draft, 'identityEvidence': gs.evidence(member),
            'actor': protolib.norm_email(args.actor_email)}
    warnings = []

    op = gs.operation_in_progress(repo)
    if op:
        return fail('OPERATION_IN_PROGRESS', [problem('OPERATION_IN_PROGRESS',
                    f'Há uma operação git em andamento ({op}); conclua ou aborte antes de compartilhar.')], data)
    if gs.rev(repo, 'HEAD') is None:
        return fail('NO_COMMITS', [problem('NO_COMMITS', 'O repositório ainda não tem commits.')], data)
    if args.paths and ct.INDEX_REL not in args.paths and gs.status_paths(repo, (ct.INDEX_REL,), untracked=False) \
            and args.mode == 'share':
        return fail('VERSION_FILES_DIRTY', [problem('VERSION_FILES_DIRTY',
                    'index.html tem mudanças fora do lote (--paths); o bump de versão também altera esse arquivo. '
                    'Inclua index.html no lote ou guarde essas mudanças antes.')], data)

    fetched, _ = gs.fetch(repo, remote)
    ok, err = ensure_draft(repo, remote, beta, official, draft)
    if not ok:
        return fail('DRAFT_SWITCH_BLOCKED', [problem('DRAFT_SWITCH_BLOCKED',
                    f'Não foi possível ir para o rascunho {draft} levando as mudanças: {err}')], data)

    try:
        staged = stage_batch(repo, args.paths)
    except RuntimeError as e:
        return fail('COMMIT_FAILED', [problem('COMMIT_FAILED', f'Não foi possível montar o lote: {e}')], data)
    if staged:
        subject = args.message or default_subject(repo, args.actor_email)
        r = protolib.commit_with_trailers(repo, subject, trailers)
        if r.returncode != 0:
            return fail('COMMIT_FAILED', [problem('COMMIT_FAILED', f'Commit do lote falhou: {r.stderr.strip()}')],
                        data)
        data['commitSha'] = gs.rev(repo, 'HEAD')
    batch_sha = gs.rev(repo, 'HEAD')
    data['draftSha'] = batch_sha

    if args.mode == 'save-only':
        return save_only(repo, remote, draft, fetched, trailers, data, warnings)

    beta_ref = f'{remote}/{beta}'
    if 'commitSha' not in data and gs.rev(repo, beta_ref) and gs.is_ancestor(repo, batch_sha, beta_ref):
        return fail('NOTHING_TO_SHARE', [problem('NOTHING_TO_SHARE',
                    'Nada novo para compartilhar: o rascunho já está todo na beta.')], data)

    attempts = 0
    while True:
        attempts += 1
        data['attempts'] = attempts
        ok, err = gs.fetch(repo, remote)
        if not ok:
            gs.rollback_to(repo, batch_sha)
            return fail('NOT_SYNCED', [problem('NOT_SYNCED', 'Sem conexão com o remoto: o commit ficou salvo só '
                        'nesta máquina e NÃO recebeu número de versão. Rode de novo quando houver rede.')], data)
        res = gs.integrate(repo, beta_ref, f'merge(prototype): integra {beta_ref} em {draft}', trailers,
                           decisions)
        if res['status'] == 'conflicts':
            data['conflicts'] = res['conflicts']
            questions = [f"{c['path']}: manter a versão de {(c['ours'] or {}).get('actor', 'você')} ou a de "
                         f"{(c['theirs'] or {}).get('actor', 'quem compartilhou antes')}?"
                         if c['path'] != protolib.CONFIG_NAME else
                         f"{c['path']}: a mesma chave foi alterada dos dois lados; o promoter decide o valor e a "
                         'decisão entra como combined (conteúdo final com todos os membros; group-conflicts.md).'
                         for c in res['conflicts']]
            return fail('CONFLICTS', [problem('CONFLICTS', 'Há conflitos perceptíveis com a beta; o merge foi '
                        'desfeito e nada mudou na beta. Pergunte ao usuário o que manter em cada arquivo.')],
                        data, questions)
        if res['status'] == 'error':
            return fail('MERGE_FAILED', [problem('MERGE_FAILED', f'Merge com a beta falhou: {res["error"]}')], data)
        data['autoResolved'] = res['resolved']
        if res.get('decided'):
            data['decidedConflicts'] = res['decided']

        entries = ct.read_entries(repo)
        base = ct.last_official(entries) or 'v0.0.0'
        version = f'{base}-beta.{ct.next_beta_number(entries, base)}'
        subject = args.message or default_subject(repo, args.actor_email)
        entries = ct.rename_pending(entries, version, gs.today(), fallback_changes=[subject.split(': ', 1)[-1]])
        prob, w = gs.apply_version(repo, version, entries)
        warnings += [x for x in w if x not in warnings]
        if not prob:
            prob, _ = gs.check_js(repo, beta_ref if gs.rev(repo, beta_ref) else None)
        if prob:
            gs.rollback_to(repo, batch_sha)
            return fail(prob['code'], [prob] + warnings, data)
        gs.commit_paths(repo, [ct.CHANGELOG_REL, ct.INDEX_REL], f'chore(prototype): bump version to {version}',
                        trailers)
        st, err = gs.push(repo, remote, f'HEAD:refs/heads/{beta}')
        if st == 'ok':
            break
        gs.rollback_to(repo, batch_sha)
        if st == 'offline':
            return fail('NOT_SYNCED', [problem('NOT_SYNCED', 'O envio para a beta falhou por conexão; o commit '
                        'ficou só nesta máquina, sem número de versão. Rode de novo quando houver rede.')], data)
        if attempts > args.max_retries:
            return fail('PUSH_REJECTED', [problem('PUSH_REJECTED', f'A beta mudou durante o envio {attempts} vezes '
                        'seguidas; nada foi forçado. Tente de novo em instantes.')], data)

    data.update(version=version, betaSha=gs.rev(repo, 'HEAD'),
                artifactsToUpdate=gs.artifacts_of(protolib.load_config(repo)[0], ('beta',)))
    st, err = gs.push(repo, remote, f'{draft}:refs/heads/{draft}', upstream=True)
    if st != 'ok':
        warnings.append(problem('DRAFT_PUSH_FAILED', f'A beta foi atualizada, mas o rascunho {draft} não subiu: '
                                f'{err or st}'))
    return protolib.emit(True, 'SHARED', data=data, problems=warnings)


def save_only(repo, remote, draft, fetched, trailers, data, warnings):
    if not fetched:
        return fail('NOT_SYNCED', [problem('NOT_SYNCED', 'Sem conexão com o remoto: o rascunho foi salvo só nesta '
                    'máquina.')], data)
    for _ in range(2):
        st, err = gs.push(repo, remote, f'{draft}:refs/heads/{draft}', upstream=True)
        if st == 'ok':
            data['draftSha'] = gs.rev(repo, 'HEAD')
            return protolib.emit(True, 'SAVED', data=data, problems=warnings)
        if st == 'offline':
            return fail('NOT_SYNCED', [problem('NOT_SYNCED', 'O envio do rascunho falhou por conexão; ficou salvo '
                        'só nesta máquina.')], data)
        gs.fetch(repo, remote)
        res = gs.integrate(repo, f'{remote}/{draft}', f'merge(prototype): integra {remote}/{draft}', trailers)
        if res['status'] == 'conflicts':
            data['conflicts'] = res['conflicts']
            return fail('CONFLICTS', [problem('CONFLICTS', 'O rascunho remoto (outra máquina sua) diverge deste '
                        'com conflito perceptível; o merge foi desfeito.')], data)
        if res['status'] == 'error':
            return fail('MERGE_FAILED', [problem('MERGE_FAILED', res['error'] or 'merge falhou')], data)
    return fail('PUSH_REJECTED', [problem('PUSH_REJECTED', f'O push de {draft} foi recusado; nada foi forçado.')],
                data)


def remote_roster(repo, cfg):
    """Config da beta no remoto (fonte da verdade do roster); a local se não houver."""
    remote = cfg.get('remote', 'origin')
    beta = cfg.get('branches', {}).get('beta', 'beta')
    r = git(repo, 'show', f'refs/remotes/{remote}/{beta}:{protolib.CONFIG_NAME}')
    if r.returncode == 0:
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            pass
    return cfg


def main(argv=None):
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        return fail('NOT_A_REPO', [problem('NOT_A_REPO', f'{repo} não é um repositório git.')])
    cfg, err = protolib.load_config(repo)
    probs = gs.check_group_config(cfg, err)
    if probs:
        return fail('INVALID_CONFIG', probs)
    # O roster que vale é o da beta no remoto: a cópia local pode ser velha e ainda dizer "pendente" para quem
    # já foi reprovado. Só leitura (fetch atualiza referências remotas, não mexe no trabalho).
    gs.fetch(repo, cfg.get('remote', 'origin'))
    roster_cfg = remote_roster(repo, cfg)
    member = protolib.find_member(roster_cfg, args.actor_email) or protolib.find_member(cfg, args.actor_email)
    status = (member or {}).get('status', 'unknown')
    if status not in ALLOWED_STATUSES:
        return fail('NOT_ALLOWED', [problem('NOT_ALLOWED', f'{args.actor_email} está com status "{status}" no '
                    'roster e não pode compartilhar. Quem não está no roster precisa se registrar '
                    '(identity-check.py --register).')], {'memberStatus': status})
    if args.mode == 'share' and protolib.is_promoter(member) and not args.vetting_done:
        pend = [m.get('email') for m in roster_cfg.get('members', [])
                if m.get('status') == 'pending' and protolib.norm_email(m.get('email')) != protolib.norm_email(
                    args.actor_email)]
        if pend:
            return fail('VETTING_REQUIRED', [problem('VETTING_REQUIRED', 'Há membros pendentes de aprovação: '
                        + ', '.join(pend) + '. Revise-os (member-vetting) e rode de novo com --vetting-done.')],
                        {'pendingMembers': pend})
    draft = protolib.draft_branch(cfg, args.actor_email)
    if not args.execute:
        return protolib.emit(True, 'DRY_RUN', data={'plan': build_plan(repo, args, cfg, member, draft),
                                                    'identityEvidence': gs.evidence(member),
                                                    'memberStatus': status})
    return execute(repo, args, cfg, member, draft)


if __name__ == '__main__':
    sys.exit(main())
