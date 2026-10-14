#!/usr/bin/env python3
"""Guarda o trabalho de um preview (ou um stash) numa branch no remoto, sem mexer no que a pessoa está fazendo.

Só stdlib. Padrão é DRY-RUN (devolve `data.plan` e não escreve nada); `--execute` realiza.

  python3 group-preview.py --repo . --actor-email ana@example.test --id opcao-a             # plano
  python3 group-preview.py --repo . --actor-email ana@example.test --id opcao-a --execute   # guarda e envia
  python3 group-preview.py --repo . --actor-email ana@example.test --id opcao-b --source 'stash@{0}' --execute
  python3 group-preview.py --repo . --actor-email ana@example.test --mode audit             # só leitura: o que está sem cópia

Problema que resolve: um preview é um artefato avulso, sem commit e sem versão, então o código por trás
dele ficava só no computador da pessoa (alteração pendente ou stash). Aqui cada preview ganha uma branch
`preview/<membro>/<id>` no remoto, e o link publicado passa a ter origem rastreável.

Como funciona o `snapshot` (modo padrão):
- `--source working` (padrão): tira uma foto do diretório de trabalho (alterações e arquivos novos; respeita
  .gitignore e nunca leva `dist/`). `--source stash@{N}`: foto do stash (inclui os arquivos novos dele).
- Monta o commit só com comandos de baixo nível do git (índice temporário + commit-tree + update-ref): a
  branch atual, o índice e os arquivos da pessoa **não são tocados**; nada é feito de checkout, stash ou reset.
- Repetir o mesmo `--id` acrescenta um commit em cima da branch (nunca reescreve). Foto idêntica à anterior
  não cria commit novo (SNAPSHOT_UNCHANGED).
- Envia sem force. Sem rede: o commit local fica feito e o status é NOT_SYNCED (nada se perde; repetir depois).
- Devolve `data.sourceRef` (`<branch>@<sha7>`) para gravar no registro do artefato com
  `artifacts.py update-source`.

`--mode audit` (somente leitura) lista o que existe só neste computador: alterações não commitadas, stashes,
branches locais com commits que o remoto não tem e previews registrados sem branch ou com a branch
desatualizada. Status SAFE ou AT_RISK; os avisos vêm em `problems`.

Status: DRY_RUN, SNAPSHOT, SNAPSHOT_UNCHANGED, NOTHING_TO_SNAPSHOT, NOT_SYNCED, PUSH_REJECTED, NOT_ALLOWED,
INVALID_CONFIG, BAD_ID, BAD_SOURCE, NOT_A_REPO, OPERATION_IN_PROGRESS, SAFE, AT_RISK.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import git, problem  # noqa: E402

ALLOWED_STATUSES = ('approved', 'pending')
ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,47}$')
STASH_RE = re.compile(r'^stash@\{\d+\}$')
T_PREVIEW = 'Prototype-Preview'
T_PREVIEW_SOURCE = 'Prototype-Preview-Source'
T_PREVIEW_BASE = 'Prototype-Preview-Base'


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email', required=True)
    ap.add_argument('--mode', choices=('snapshot', 'audit'), default='snapshot')
    ap.add_argument('--id', help='identificador do preview (a-z, 0-9 e hífen), ex.: opcao-a')
    ap.add_argument('--source', default='working', help='working (padrão) ou stash@{N}')
    ap.add_argument('--message', help='assunto do commit (padrão: preview <id>)')
    ap.add_argument('--execute', action='store_true')
    return ap.parse_args(argv)


def fail(status, probs, data=None):
    return protolib.emit(False, status, data=data, problems=probs)


def preview_branch(cfg, actor, preview_id):
    return f'preview/{protolib.slug_member(actor)}/{preview_id}'


def _plumb(repo, env_extra, *args, input=None):
    env = dict(os.environ, **env_extra)
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, env=env,
                          input=input, timeout=60)


def snapshot_tree(repo, source):
    """(tree_sha, base_sha|None, erro|None). Usa índice temporário: o índice real não é tocado."""
    with tempfile.TemporaryDirectory() as td:
        env = {'GIT_INDEX_FILE': os.path.join(td, 'index')}
        head = gs.rev(repo, 'HEAD')
        if source == 'working':
            base = head
            if head and _plumb(repo, env, 'read-tree', head).returncode != 0:
                return None, None, 'não consegui ler o HEAD'
            r = _plumb(repo, env, 'add', '-A', '--', '.')
            if r.returncode != 0:
                return None, None, f'git add falhou: {r.stderr.strip()}'
        else:
            commit = gs.rev(repo, source)
            if not commit:
                return None, None, f'{source} não existe'
            base = gs.rev(repo, f'{source}^1')
            if _plumb(repo, env, 'read-tree', commit).returncode != 0:
                return None, None, f'não consegui ler {source}'
            untracked = gs.rev(repo, f'{source}^3')
            if untracked:
                listing = git(repo, 'ls-tree', '-r', '-z', untracked).stdout
                lines = []
                for item in listing.split('\0'):
                    if item:
                        meta, path = item.split('\t', 1)
                        mode, _, sha = meta.split(' ')
                        lines.append(f'{mode} {sha}\t{path}')
                if lines:
                    r = _plumb(repo, env, 'update-index', '--add', '--index-info', input='\n'.join(lines) + '\n')
                    if r.returncode != 0:
                        return None, None, f'não consegui juntar os arquivos novos do stash: {r.stderr.strip()}'
        _plumb(repo, env, 'rm', '--cached', '-r', '-q', '--ignore-unmatch', '--', 'dist')
        w = _plumb(repo, env, 'write-tree')
        if w.returncode != 0:
            return None, None, f'git write-tree falhou: {w.stderr.strip()}'
        return w.stdout.strip(), base, None


def tree_of(repo, ref):
    return gs.out(repo, 'rev-parse', '--verify', '-q', f'{ref}^{{tree}}')


def branch_tip(repo, remote, branch):
    """Ponta da branch: a mais avançada entre a local e a do remoto. (sha|None, divergiu: bool)."""
    local = gs.rev(repo, f'refs/heads/{branch}')
    remote_sha = gs.rev(repo, f'refs/remotes/{remote}/{branch}')
    if local and remote_sha and local != remote_sha:
        if gs.is_ancestor(repo, local, remote_sha):
            return remote_sha, False
        if gs.is_ancestor(repo, remote_sha, local):
            return local, False
        return local, True
    return local or remote_sha, False


def changed_files(repo, parent, tree):
    parent_tree = tree_of(repo, parent) if parent else None
    if parent_tree is None:
        r = git(repo, 'ls-tree', '-r', '--name-only', tree)
    else:
        r = git(repo, 'diff-tree', '-r', '--name-only', parent_tree, tree)
    return sorted(p for p in r.stdout.splitlines() if p)


def run_snapshot(repo, args, cfg, member):
    if not args.id or not ID_RE.match(args.id):
        return fail('BAD_ID', [problem('BAD_ID', 'Informe --id com letras minúsculas, números e hífen '
                                       '(até 48 caracteres), ex.: opcao-a.')])
    if args.source != 'working' and not STASH_RE.match(args.source):
        return fail('BAD_SOURCE', [problem('BAD_SOURCE', '--source aceita "working" ou "stash@{N}". Para uma '
                                           'branch ou commit existente, basta enviá-lo normalmente.')])
    op = gs.operation_in_progress(repo)
    if op:
        return fail('OPERATION_IN_PROGRESS', [problem('OPERATION_IN_PROGRESS', f'Há uma operação do git em '
                                                      f'andamento ({op}); conclua ou cancele antes.')])
    remote = cfg.get('remote', 'origin')
    branch = preview_branch(cfg, args.actor_email, args.id)
    synced, _ = gs.fetch(repo, remote)
    tree, base, err = snapshot_tree(repo, args.source)
    if err:
        return fail('BAD_SOURCE', [problem('BAD_SOURCE', err)])
    tip, diverged = branch_tip(repo, remote, branch)
    if diverged:
        return fail('PUSH_REJECTED', [problem('PUSH_REJECTED', f'A branch {branch} tem versões diferentes aqui e '
                                              'no remoto. Use outro --id ou peça a quem mantém o protótipo.')])
    parent = tip or base
    data = {'branch': branch, 'source': args.source, 'previewId': args.id, 'base': base,
            'files': changed_files(repo, parent, tree), 'previousTip': tip}
    if tip and tree == tree_of(repo, tip):
        data.update({'sha': tip, 'sourceRef': f'{branch}@{tip[:7]}', 'pushed': _is_pushed(repo, remote, branch, tip)})
        if not data['pushed'] and args.execute:
            return _push(repo, remote, branch, data)
        return protolib.emit(True, 'SNAPSHOT_UNCHANGED', data=data)
    if not tip and base and tree == tree_of(repo, base):
        return protolib.emit(True, 'NOTHING_TO_SNAPSHOT', data=data, problems=[problem(
            'NOTHING_TO_SNAPSHOT', 'O trabalho é idêntico ao último commit: não há nada a guardar.')])
    if not args.execute:
        data['plan'] = [f'Criar o commit do preview "{args.id}" na branch {branch} (a partir de '
                        f'{"a ponta anterior da branch" if tip else "o commit atual"}), sem tocar no seu trabalho.',
                        f'Enviar {branch} ao remoto "{remote}" (sem force).']
        return protolib.emit(True, 'DRY_RUN', data=data)
    trailers = dict(gs.actor_trailers(member))
    trailers.update({T_PREVIEW: args.id, T_PREVIEW_SOURCE: args.source, T_PREVIEW_BASE: base or ''})
    subject = (args.message or f'chore(prototype): preview {args.id}').strip()
    msg = subject + '\n\n' + protolib.format_trailers(trailers) + '\n'
    cmd = ['commit-tree', tree, '-m', msg] + (['-p', parent] if parent else [])
    c = git(repo, *cmd)
    if c.returncode != 0:
        return fail('NOT_SYNCED', [problem('COMMIT_FAILED', f'Não consegui criar o commit: {c.stderr.strip()}')], data)
    sha = c.stdout.strip()
    ref = f'refs/heads/{branch}'
    u = git(repo, 'update-ref', ref, sha, *([tip] if gs.rev(repo, ref) else ['']))
    if u.returncode != 0:
        return fail('NOT_SYNCED', [problem('REF_FAILED', f'Não consegui atualizar {branch}: {u.stderr.strip()}')], data)
    data.update({'sha': sha, 'sourceRef': f'{branch}@{sha[:7]}'})
    return _push(repo, remote, branch, data)


def _is_pushed(repo, remote, branch, sha):
    return gs.rev(repo, f'refs/remotes/{remote}/{branch}') == sha


def _push(repo, remote, branch, data):
    state, detail = gs.push(repo, remote, f'refs/heads/{branch}:refs/heads/{branch}')
    data['pushed'] = state == 'ok'
    if state == 'ok':
        return protolib.emit(True, 'SNAPSHOT', data=data)
    if state == 'rejected':
        return protolib.emit(False, 'PUSH_REJECTED', data=data, problems=[problem(
            'PUSH_REJECTED', f'O remoto recusou o envio de {branch} (alguém atualizou no meio tempo). O commit '
                             f'local está guardado; rode de novo para integrar. {detail}')])
    return protolib.emit(False, 'NOT_SYNCED', data=data, problems=[problem(
        'NOT_SYNCED', 'Sem acesso ao remoto: o preview ficou guardado só neste computador (commit local). '
                      f'Rode de novo quando houver rede. {detail}')])


def run_audit(repo, cfg):
    remote = cfg.get('remote', 'origin')
    gs.fetch(repo, remote)
    probs, data = [], {}
    dirty = [p for _, p in gs.status_paths(repo) if not gs.is_dist(p)]
    data['uncommitted'] = dirty
    if dirty:
        probs.append(problem('UNSAVED_WORK', f'{len(dirty)} arquivo(s) com alteração só neste computador '
                             '(não commitada). Guarde com group-share.py --mode save-only ou group-preview.py.'))
    stashes = [line for line in git(repo, 'stash', 'list').stdout.splitlines() if line]
    data['stashes'] = stashes
    if stashes:
        probs.append(problem('STASHED_WORK', f'{len(stashes)} stash(es) só neste computador: guarde cada um '
                             'com group-preview.py --source stash@{N}.'))
    unpushed = []
    for line in git(repo, 'for-each-ref', '--format=%(refname:short)\t%(upstream:short)', 'refs/heads').stdout.splitlines():
        name, _, upstream = line.partition('\t')
        remote_ref = upstream or f'{remote}/{name}'
        if not gs.rev(repo, f'refs/remotes/{remote_ref}'):
            if gs.rev(repo, f'refs/heads/{name}') != gs.rev(repo, f'refs/remotes/{remote}/{cfg["branches"]["official"]}'):
                unpushed.append(name)
        elif git(repo, 'rev-list', '--count', f'refs/remotes/{remote_ref}..refs/heads/{name}').stdout.strip() not in ('', '0'):
            unpushed.append(name)
    data['unpushedBranches'] = unpushed
    if unpushed:
        probs.append(problem('UNPUSHED_BRANCH', 'Branch(es) com commits que o remoto não tem: ' + ', '.join(unpushed) + '.'))
    previews = []
    for a in cfg.get('artifacts', []):
        if not isinstance(a, dict) or a.get('kind') != 'preview' or a.get('status') == 'revoked':
            continue
        branch = a.get('branch')
        item = {'id': a.get('id'), 'branch': branch, 'sourceRef': a.get('sourceRef')}
        if not branch:
            probs.append(problem('PREVIEW_WITHOUT_BRANCH', f'O preview "{a.get("id")}" não tem branch: o código por '
                                 'trás do link só existe neste computador. Rode group-preview.py --id <id> --execute.'))
        elif not gs.rev(repo, f'refs/remotes/{remote}/{branch}'):
            probs.append(problem('PREVIEW_BRANCH_NOT_PUSHED', f'A branch {branch} do preview "{a.get("id")}" não '
                                 'está no remoto.'))
        previews.append(item)
    data['previews'] = previews
    return protolib.emit(True, 'AT_RISK' if probs else 'SAFE', data=data, problems=probs)


def main(argv=None):
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        return fail('NOT_A_REPO', [problem('NOT_A_REPO', f'{repo} não é um repositório git.')])
    cfg, err = protolib.load_config(repo)
    probs = gs.check_group_config(cfg, err)
    if probs:
        return fail('INVALID_CONFIG', probs)
    if args.mode == 'audit':
        return run_audit(repo, cfg)
    gs.fetch(repo, cfg.get('remote', 'origin'))
    roster_cfg = gs.remote_roster(repo, cfg)
    member = protolib.find_member(roster_cfg, args.actor_email) or protolib.find_member(cfg, args.actor_email)
    status = (member or {}).get('status', 'unknown')
    if status not in ALLOWED_STATUSES:
        return fail('NOT_ALLOWED', [problem('NOT_ALLOWED', f'{args.actor_email} está com status "{status}" no '
                                            'roster e não pode gerar previews. Quem não está no roster precisa se '
                                            'registrar (identity-check.py --register).')], {'memberStatus': status})
    return run_snapshot(repo, args, cfg, member)


if __name__ == '__main__':
    sys.exit(main())
