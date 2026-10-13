"""Operações git compartilhadas por group-share.py e group-promote.py (módulo, sem CLI; só stdlib).

Regras: nunca force-push; `reset` só para desfazer o que o próprio script acabou de fazer, e sempre com
`--keep` (recusa se isso apagaria mudança não commitada do usuário).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import changelog_tools as ct
import protolib
from protolib import git

BUMP_SUBJECT_RE = re.compile(r'^chore\(prototype\): (bump version to|promote|release) ')
PUSH_REJECT_MARKERS = ('rejected', 'non-fast-forward', 'fetch first', 'failed to update ref',
                       'cannot lock ref', 'stale info', 'failed to lock')


def today():
    return date.today().isoformat()


def out(repo, *args):
    r = git(repo, *args)
    return r.stdout.strip() if r.returncode == 0 else None


def rev(repo, ref):
    return out(repo, 'rev-parse', '--verify', '-q', f'{ref}^{{commit}}')


def is_ancestor(repo, a, b):
    return git(repo, 'merge-base', '--is-ancestor', a, b).returncode == 0


def current_branch(repo):
    return out(repo, 'symbolic-ref', '--short', '-q', 'HEAD')


def git_dir(repo):
    d = out(repo, 'rev-parse', '--git-dir')
    return (Path(repo) / d) if d and not os.path.isabs(d) else Path(d or '')


def operation_in_progress(repo):
    gd = git_dir(repo)
    for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        if (gd / name).exists():
            return name
    return None


def fetch(repo, remote):
    try:
        r = git(repo, 'fetch', '--prune', '-q', remote, timeout=90)
    except subprocess.TimeoutExpired:
        return False, 'tempo esgotado'
    return r.returncode == 0, r.stderr.strip()


def ls_remote_head(repo, remote, branch):
    """sha do branch no remoto sem gravar nada localmente; None se inalcançável, '' se não existe."""
    try:
        r = git(repo, 'ls-remote', '--heads', remote, branch, timeout=20)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        sha, ref = line.split('\t', 1)
        if ref == f'refs/heads/{branch}':
            return sha
    return ''


def push(repo, remote, refspec, upstream=False):
    """Devolve ('ok'|'rejected'|'offline', stderr). Sem --force em hipótese alguma."""
    args = ['push', '--porcelain', remote, refspec]
    if upstream:
        args.insert(1, '-u')
    try:
        r = git(repo, *args, timeout=120)
    except subprocess.TimeoutExpired:
        return 'offline', 'tempo esgotado'
    if r.returncode == 0:
        return 'ok', r.stderr.strip()
    text = (r.stdout + '\n' + r.stderr).lower()
    if any(m in text for m in PUSH_REJECT_MARKERS):
        return 'rejected', r.stderr.strip()
    return 'offline', r.stderr.strip()


def rollback_to(repo, sha):
    """Desfaz commits/merge que o próprio script criou; --keep preserva mudanças locais do usuário."""
    if rev(repo, 'HEAD') != sha:
        git(repo, 'reset', '-q', '--keep', sha, check=True)


def status_paths(repo, pathspecs=('.',), untracked=True):
    args = ['status', '--porcelain=v1', '-z', f'--untracked-files={"all" if untracked else "no"}', '--',
            *pathspecs]
    raw = git(repo, *args).stdout
    items, parts, i = [], raw.split('\0'), 0
    while i < len(parts):
        p = parts[i]
        if len(p) > 3:
            code, path = p[:2], p[3:]
            items.append((code, path))
            if code[0] in 'RC':
                i += 1
        i += 1
    return items


def is_dist(path):
    return path == 'dist' or path.startswith('dist/')


def show(repo, spec):
    r = git(repo, 'show', spec)
    return r.stdout if r.returncode == 0 else None


def read_text(repo, rel):
    p = Path(repo) / rel
    if not p.exists():
        return None
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_text(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def entries_at(repo, ref):
    text = show(repo, f'{ref}:{ct.CHANGELOG_REL}')
    if text is None:
        return []
    try:
        return ct.parse_text(text)[1]
    except ct.ChangelogError:
        return []


# ---------------------------------------------------------------- config / ator

def check_group_config(cfg, err):
    if err:
        return [protolib.problem('CONFIG_INVALID', err)]
    if cfg is None:
        return [protolib.problem('CONFIG_MISSING', f'{protolib.CONFIG_NAME} não encontrado: este protótipo não '
                                 'está em modo grupo.')]
    probs = []
    skill = cfg.get('skill')
    ver = skill.get('version') if isinstance(skill, dict) else None
    if not ver:
        probs.append(protolib.problem('CONFIG_LEGACY', 'Config no formato antigo (v1): rode a migração '
                                      '(migrate.py) antes de compartilhar ou promover.'))
    elif not str(ver).startswith('2.'):
        probs.append(protolib.problem('CONFIG_VERSION_UNSUPPORTED',
                                      f'Config da skill na versão {ver}; estes scripts entendem só a 2.x.'))
    br = cfg.get('branches')
    if not isinstance(br, dict) or not all(isinstance(br.get(k), str) and br.get(k)
                                           for k in ('official', 'beta', 'draftPattern')):
        probs.append(protolib.problem('CONFIG_INVALID', '"branches" precisa de official, beta e draftPattern.'))
    if not isinstance(cfg.get('members'), list):
        probs.append(protolib.problem('CONFIG_INVALID', '"members" precisa ser uma lista.'))
    else:
        for m in cfg['members']:
            if not isinstance(m, dict) or not m.get('email') or m.get('status') not in protolib.MEMBER_STATUSES:
                probs.append(protolib.problem('CONFIG_INVALID', 'Há membro sem e-mail ou com status inválido.'))
                break
    if not isinstance(cfg.get('artifacts', []), list):
        probs.append(protolib.problem('CONFIG_INVALID', '"artifacts" precisa ser uma lista.'))
    if not probs and cfg.get('groupMode') is not True:
        probs.append(protolib.problem('GROUP_MODE_OFF', 'O modo grupo está desligado (groupMode != true).'))
    return probs


def evidence(member):
    return (member or {}).get('identityEvidence') or 'unverified'


def actor_trailers(member):
    return {protolib.T_ACTOR: protolib.norm_email(member.get('email')),
            protolib.T_MEMBER_STATUS: member.get('status'),
            protolib.T_IDENTITY: evidence(member)}


def artifacts_of(cfg, kinds):
    return [a for a in (cfg or {}).get('artifacts', []) if isinstance(a, dict) and a.get('kind') in kinds]


# ---------------------------------------------------------------- log / autoria

def commit_log(repo, rng, *paths, no_merges=True, limit=None):
    args = ['log', '--format=%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%B%x1e']
    if no_merges:
        args.append('--no-merges')
    if limit:
        args.append(f'-{limit}')
    args.append(rng)
    if paths:
        args += ['--', *paths]
    r = git(repo, *args)
    items = []
    if r.returncode != 0:
        return items
    for rec in r.stdout.split('\x1e'):
        rec = rec.strip('\n')
        if not rec:
            continue
        sha, an, ae, ad, subj, body = rec.split('\x1f', 5)
        tr = protolib.parse_trailers(body)
        items.append({'sha': sha, 'author': an, 'email': protolib.norm_email(ae), 'date': ad, 'subject': subj,
                      'actor': protolib.norm_email(tr.get(protolib.T_ACTOR)) or protolib.norm_email(ae),
                      'trailers': tr})
    return items


def side_info(repo, rng, path):
    log = commit_log(repo, rng, path, no_merges=False, limit=1)
    if not log:
        return None
    c = log[0]
    return {'commit': c['sha'], 'author': c['author'], 'email': c['email'], 'actor': c['actor'],
            'subject': c['subject']}


# ---------------------------------------------------------------- conflitos

def classify(path):
    if is_dist(path):
        return 'mechanical:dist'
    if path == ct.CHANGELOG_REL:
        return 'mechanical:changelog'
    if path == protolib.CONFIG_NAME:
        return 'mechanical:config'
    if path == ct.INDEX_REL:
        return 'mechanical:badge-only'
    return 'perceptible'


def _merge_file(base, ours, theirs):
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for name, text in (('ours', ours), ('base', base), ('theirs', theirs)):
            p = Path(td) / name
            p.write_text(text, encoding='utf-8')
            paths.append(str(p))
        r = subprocess.run(['git', 'merge-file', '-p', '-q', *paths], capture_output=True, text=True)
        return r.returncode == 0, r.stdout


def _resolve_badge_only(base, ours, theirs):
    ph = '@@PROTOTYPE_BADGE@@'
    clean, merged = _merge_file(ct.normalize_badge(base or '', ph), ct.normalize_badge(ours, ph),
                                ct.normalize_badge(theirs, ph))
    if not clean or merged.count(ph) != 1:
        raise ct.ConflictError([ct.INDEX_REL], 'index.html tem conflito além do texto do badge.')
    return merged.replace(ph, ct.badge_text(ours) or '')


def resolve_unmerged(repo):
    """Resolve conflitos mecânicos do índice atual. Devolve (resolvidos, perceptíveis[(path, detalhe)], dist)."""
    unmerged = (out(repo, 'diff', '--name-only', '--diff-filter=U') or '').splitlines()
    resolved, perceptible, regen = [], [], False
    for path in unmerged:
        kind = classify(path)
        base, ours, theirs = (show(repo, f':{n}:{path}') for n in (1, 2, 3))
        try:
            if kind == 'perceptible':
                raise ct.ConflictError([path], 'alteração perceptível nos dois lados')
            if kind == 'mechanical:dist':
                if ours is not None:
                    git(repo, 'checkout', '--ours', '--', path, check=True)
                    git(repo, 'add', '--', path, check=True)
                else:
                    git(repo, 'rm', '-q', '--', path, check=True)
                regen = True
                resolved.append({'path': path, 'how': 'dist ignorado (será regenerado)'})
                continue
            if ours is None or theirs is None:
                raise ct.ConflictError([path], 'arquivo apagado de um lado e alterado do outro')
            if kind == 'mechanical:changelog':
                merged, how = ct.resolve_changelog_text(base, ours, theirs), 'união das entradas do changelog'
            elif kind == 'mechanical:config':
                merged, how = ct.resolve_config_text(base, ours, theirs), 'merge do prototype.config.json'
            else:
                merged, how = _resolve_badge_only(base, ours, theirs), 'conflito só no texto do badge'
            write_text(repo, path, merged)
            git(repo, 'add', '--', path, check=True)
            resolved.append({'path': path, 'how': how})
        except ct.ConflictError as e:
            perceptible.append((path, str(e)))
    return resolved, perceptible, regen


def normalize_changelog_worktree(repo):
    """Depois de um merge limpo, garante changelog parseável e sem versão repetida. Erro → texto do problema."""
    text = read_text(repo, ct.CHANGELOG_REL)
    if text is None:
        return None
    try:
        prefix, entries, suffix = ct.parse_text(text)
    except ct.ChangelogError as e:
        return str(e)
    normalized = ct.normalize_entries(entries)
    if normalized != entries:
        write_text(repo, ct.CHANGELOG_REL, ct.render_text(prefix, normalized, suffix))
        git(repo, 'add', '--', ct.CHANGELOG_REL)
    return None


def conflict_report(repo, perceptible, ours_rng, theirs_rng):
    return [{'path': p, 'kind': 'perceptible', 'detail': d,
             'ours': side_info(repo, ours_rng, p), 'theirs': side_info(repo, theirs_rng, p)}
            for p, d in perceptible]


def clean_decision_text(text):
    """Texto livre de uma decisão sem os separadores do trailer (`;`, `|`, quebras de linha)."""
    return ' '.join(str(text or '').replace(';', ',').replace('|', '/').split())[:120]


def dropped_actors(repo, rng, path):
    """Todos os autores (actor) que mexeram em `path` no intervalo, do mais recente ao mais antigo."""
    seen = []
    for c in commit_log(repo, rng, path, no_merges=True):
        if c['actor'] and c['actor'] not in seen:
            seen.append(c['actor'])
    return seen


def _favor_side(base, ours, theirs, keep):
    """Merge de 3 vias que, nos trechos em conflito, fica com o lado escolhido (mine|theirs); as mudanças
    que não conflitam, de qualquer lado, são mantidas."""
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for name, text in (('ours', ours), ('base', base or ''), ('theirs', theirs)):
            p = Path(td) / name
            p.write_text(text, encoding='utf-8')
            paths.append(str(p))
        r = subprocess.run(['git', 'merge-file', '-p', '-q', '--ours' if keep == 'mine' else '--theirs', *paths],
                           capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None


def _combined_config(content, base, ours, theirs, by):
    """Conteúdo final do config num `combined`, ou None se recusado.

    Só promoter aprovado (no roster da beta) decide o config. `members` e `artifacts` do arquivo são
    ignorados: valem as fusões mecânicas dos dois lados (decisão de pessoa nunca se desfaz, ninguém some).
    """
    try:
        final, o, t = json.loads(content), json.loads(ours), json.loads(theirs)
        b = json.loads(base) if base else {}
    except ValueError:
        return None
    if not isinstance(final, dict) or not isinstance(o, dict) or not isinstance(t, dict):
        return None
    member = protolib.find_member(t, by) if by else None
    if not (member and member.get('status') == 'approved' and protolib.is_promoter(member)):
        return None
    lists = ('members', 'artifacts')
    merged = ct.merge_config({k: v for k, v in b.items() if k in lists} if isinstance(b, dict) else {},
                             {k: v for k, v in o.items() if k in lists},
                             {k: v for k, v in t.items() if k in lists})
    for k in lists:
        if k in merged:
            final[k] = merged[k]
        else:
            final.pop(k, None)
    return json.dumps(final, ensure_ascii=False, indent=2) + '\n'


def apply_decisions(repo, perceptible, decisions, ours_rng, theirs_rng, by=None):
    """Aplica decisões do usuário (`path` → keep mine|theirs|combined, what[, content]) aos conflitos perceptíveis.

    mine/theirs: a escolha vale só para os trechos em conflito; o resto do arquivo mantém as mudanças dos
    dois lados. Arquivo apagado de um lado segue a escolha inteira. combined: grava o conteúdo final
    fornecido (a combinação feita pelo agente com o usuário). No config só vale `combined`, só para promoter
    aprovado, e `members`/`artifacts` vêm sempre da fusão mecânica dos dois lados (nunca descarta roster).
    Devolve (restantes, decididos). `mine` = lado do rascunho (HEAD); `theirs` = lado da beta (MERGE_HEAD).
    O merge segue aberto; quem chama conclui ou aborta.
    """
    remaining, decided = [], []
    for path, detail in perceptible:
        dec = decisions.get(path)
        is_config = path == protolib.CONFIG_NAME
        if not dec or (is_config and dec['keep'] != 'combined'):
            remaining.append((path, detail))
            continue
        base, ours, theirs = (show(repo, f':{n}:{path}') for n in (1, 2, 3))
        if dec['keep'] == 'combined':
            content = dec.get('content')
            if content is None:
                remaining.append((path, detail))
                continue
            if is_config:
                content = _combined_config(content, base, ours or '{}', theirs or '{}', by)
                if content is None:
                    remaining.append((path, detail))
                    continue
            write_text(repo, path, content)
            git(repo, 'add', '--', path, check=True)
        elif ours is None or theirs is None:
            keep_side = ours if dec['keep'] == 'mine' else theirs
            if keep_side is None:
                git(repo, 'rm', '-q', '--', path, check=True)
            else:
                git(repo, 'checkout', '--ours' if dec['keep'] == 'mine' else '--theirs', '--', path, check=True)
                git(repo, 'add', '--', path, check=True)
        else:
            merged = _favor_side(base, ours, theirs, dec['keep'])
            if merged is None:
                remaining.append((path, detail))
                continue
            write_text(repo, path, merged)
            git(repo, 'add', '--', path, check=True)
        mine_a, theirs_a = dropped_actors(repo, ours_rng, path), dropped_actors(repo, theirs_rng, path)
        if dec['keep'] == 'combined':
            kept = list(dict.fromkeys(mine_a + theirs_a))
            dropped = [a for a in kept if a != by]
        else:
            kept = mine_a if dec['keep'] == 'mine' else theirs_a
            dropped = theirs_a if dec['keep'] == 'mine' else mine_a
        decided.append({'path': path, 'keep': dec['keep'], 'what': dec['what'],
                        'kept': ','.join(kept) or None, 'dropped': ','.join(dropped) or None})
    return remaining, decided


def decision_trailer(decided, by):
    """Valor do trailer Prototype-Conflict-Decision: um item por decisão, separados por ` | `."""
    return ' | '.join(f"kept={d['kept'] or '?'}; dropped={d['dropped'] or '?'}; by={by}; what={d['what']}"
                      for d in decided)


def parse_decision_trailer(value):
    """Inverso de decision_trailer: lista de dicts kept/dropped/by/what."""
    items = []
    for chunk in (value or '').split(' | '):
        item = {}
        for part in chunk.split('; '):
            if '=' in part:
                k, v = part.split('=', 1)
                item[k.strip()] = v.strip()
        if item:
            items.append(item)
    return items


def integrate(repo, ref, subject, trailers, decisions=None):
    """Merge (sem rebase) de `ref` no HEAD com resolução mecânica.

    `decisions` (opcional): {path: {'keep': 'mine'|'theirs', 'what': texto}} — decisões do usuário sobre
    conflitos perceptíveis; as decididas entram no merge e no trailer Prototype-Conflict-Decision.
    Devolve dict: status up-to-date|fast-forward|merged|conflicts|error, resolved, conflicts, decided,
    regenerateDist. Em `conflicts`/`error` o merge é abortado e o HEAD fica como estava.
    """
    res = {'status': None, 'resolved': [], 'conflicts': [], 'decided': [], 'regenerateDist': False,
           'error': None}
    target = rev(repo, ref)
    head = rev(repo, 'HEAD')
    if target is None or (head and is_ancestor(repo, target, head)):
        res['status'] = 'up-to-date'
        return res
    if head is None or is_ancestor(repo, head, target):
        r = git(repo, 'merge', '-q', '--ff-only', target)
        res['status'] = 'fast-forward' if r.returncode == 0 else 'error'
        res['error'] = r.stderr.strip() or None
        return res
    r = git(repo, 'merge', '-q', '--no-ff', '--no-commit', target)
    in_merge = (git_dir(repo) / 'MERGE_HEAD').exists()
    if r.returncode != 0 and not in_merge:
        res['status'], res['error'] = 'error', (r.stderr.strip() or r.stdout.strip())
        return res
    resolved, perceptible, regen = resolve_unmerged(repo)
    mb = out(repo, 'merge-base', 'HEAD', 'MERGE_HEAD')
    decided = []
    if perceptible and decisions:
        perceptible, decided = apply_decisions(repo, perceptible, decisions, f'{mb}..HEAD', f'{mb}..MERGE_HEAD',
                                               trailers.get(protolib.T_ACTOR))
    if not perceptible:
        err = normalize_changelog_worktree(repo)
        if err:
            perceptible.append((ct.CHANGELOG_REL, err))
    if perceptible:
        res['conflicts'] = conflict_report(repo, perceptible, f'{mb}..HEAD', f'{mb}..MERGE_HEAD')
        git(repo, 'merge', '--abort')
        res['status'] = 'conflicts'
        return res
    if decided:
        trailers = dict(trailers, **{protolib.T_CONFLICT: decision_trailer(decided, trailers.get(protolib.T_ACTOR))})
        res['decided'] = decided
    c = protolib.commit_with_trailers(repo, subject, trailers)
    if c.returncode != 0:
        git(repo, 'merge', '--abort')
        res['status'], res['error'] = 'error', c.stderr.strip() or c.stdout.strip()
        return res
    res.update(status='merged', resolved=resolved, regenerateDist=regen)
    return res


# ---------------------------------------------------------------- build / checagens

def run_build(repo):
    if not (Path(repo) / 'build.py').exists():
        return True, 'build.py ausente (nada a regenerar)'
    try:
        r = subprocess.run([sys.executable, 'build.py'], cwd=str(repo), capture_output=True, text=True,
                           timeout=180)
    except subprocess.TimeoutExpired:
        return False, 'build.py excedeu o tempo'
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def node_check(repo, rel_paths):
    node = shutil.which('node')
    if not node:
        return [], False
    fails = []
    for rel in rel_paths:
        p = Path(repo) / rel
        if rel.endswith('.js') and p.exists():
            r = subprocess.run([node, '--check', str(p)], capture_output=True, text=True)
            if r.returncode != 0:
                fails.append({'path': rel, 'error': (r.stderr.strip().splitlines() or [''])[-1]})
    return fails, True


def restore_files(repo, rels):
    existing = [r for r in rels if git(repo, 'cat-file', '-e', f'HEAD:{r}').returncode == 0]
    if existing:
        git(repo, 'checkout', 'HEAD', '--', *existing)


def apply_version(repo, version, entries):
    """Grava changelog + badge, regenera e checa JS. Devolve (problema|None, avisos)."""
    warnings = []
    ct.write_entries(repo, entries)
    try:
        ct.set_badge(repo, version)
    except ct.BadgeNotFound as e:
        warnings.append(protolib.problem('BADGE_NOT_FOUND', f'{e}; versão só no changelog.'))
    except FileNotFoundError:
        warnings.append(protolib.problem('BADGE_NOT_FOUND', 'index.html ausente; versão só no changelog.'))
    ok, log = run_build(repo)
    if not ok:
        restore_files(repo, [ct.CHANGELOG_REL, ct.INDEX_REL])
        return protolib.problem('BUILD_FAILED', 'python3 build.py falhou; nada foi commitado. Saída: '
                                + log[-500:]), warnings
    return None, warnings


def check_js(repo, since_ref):
    names = (out(repo, 'diff', '--name-only', since_ref, '--') or '').splitlines() if since_ref else []
    files = sorted(set([n for n in names if n.endswith('.js') and not is_dist(n)] + [ct.CHANGELOG_REL]))
    fails, ran = node_check(repo, files)
    if fails:
        restore_files(repo, [ct.CHANGELOG_REL, ct.INDEX_REL])
        return protolib.problem('JS_CHECK_FAILED', 'node --check falhou em: '
                                + ', '.join(f"{f['path']} ({f['error']})" for f in fails)), fails
    return None, ran


def commit_paths(repo, paths, subject, trailers):
    git(repo, 'add', '--', *[p for p in paths if (Path(repo) / p).exists()
                            or git(repo, 'ls-files', '--error-unmatch', p).returncode == 0])
    if git(repo, 'diff', '--cached', '--quiet').returncode == 0:
        return None
    r = protolib.commit_with_trailers(repo, subject, trailers)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return rev(repo, 'HEAD')


def checkout_synced(repo, branch, remote_ref):
    """Deixa `branch` local igual a `remote_ref` (cria ou avança só por fast-forward). (ok, motivo)."""
    target = rev(repo, remote_ref)
    if target is None:
        return False, f'{remote_ref} não existe'
    local = rev(repo, branch)
    if local is None:
        r = git(repo, 'checkout', '-q', '-b', branch, '--track', remote_ref)
        return r.returncode == 0, r.stderr.strip()
    if local != target and not is_ancestor(repo, local, target):
        return False, f'{branch} local tem commits que não estão em {remote_ref}'
    if current_branch(repo) != branch:
        r = git(repo, 'checkout', '-q', branch)
        if r.returncode != 0:
            return False, r.stderr.strip()
    if local != target:
        r = git(repo, 'merge', '-q', '--ff-only', target)
        if r.returncode != 0:
            return False, r.stderr.strip()
    return True, ''


def switch_back(repo, branch_or_sha):
    if branch_or_sha and current_branch(repo) != branch_or_sha and rev(repo, 'HEAD') != branch_or_sha:
        git(repo, 'checkout', '-q', branch_or_sha)
