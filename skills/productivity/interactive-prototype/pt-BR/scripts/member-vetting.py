#!/usr/bin/env python3
"""Vetting de membros do modo grupo: listar pendentes, relatório, aprovar, reprovar (rollback), reintegrar.

Só stdlib. Imprime o envelope JSON de protolib no stdout; exit 0 (ok), 1 (problema/decisão), 2 (uso).
Somente promoter aprovado decide (approve/reject/reinstate/finalize/abort). Sem --execute tudo é
DRY-RUN: nada é escrito (reject/reinstate simulam o rollback numa worktree temporária e descartável).

  python3 member-vetting.py --repo . --actor-email promoter@example.test list
  python3 member-vetting.py --repo . --actor-email promoter@example.test report --email pessoa@example.test
  python3 member-vetting.py --repo . --actor-email P approve --email X --roles contributor [--profile product] --execute
  python3 member-vetting.py --repo . --actor-email P reject --email X --reason "..." [--rollback-main-items]
                                                     [--leave-conflicts] [--ack-dependents] [--since <commit|data>] --execute
  python3 member-vetting.py --repo . --actor-email P finalize --email X --execute
  python3 member-vetting.py --repo . --actor-email P reinstate --email X [--roles ...] --execute
  python3 member-vetting.py --repo . --actor-email P abort --email X --execute

Escrita (--execute): exige a branch beta em uso, worktree limpo e beta == <remote>/beta após `git fetch`;
cada decisão vira UM commit na beta (roster + eventual rollback) enviado com `git push` sem force.
Janela de commits da pessoa: alcançáveis da beta e não de `statusChangedAtCommit` (ou de --since),
com trailer Prototype-Actor dela (sem trailer: e-mail do autor); merges ignorados. O arquivo de config
nunca entra no rollback: o roster é reescrito por este script e membro nenhum é apagado.
reject para com DEPENDENTS_FOUND (nada alterado) se commits posteriores de outras pessoas tocam os mesmos
arquivos do que seria revertido; --ack-dependents só depois de o promoter decidir. O commit de rollback
acrescenta ao changelog a linha "Revertido: trabalho de membro não aprovado" (sem identificar a pessoa);
conflito de revert no changelog é resolvido por merge de 3 vias (changelog_tools).

Trailers locais além dos de protolib:
  Prototype-Rollback-Member: <email>   marca o commit de rollback (reinstate o localiza por ele)
  Prototype-Reinstate-Of: <sha>        marca o commit que desfez aquele rollback
  Prototype-Member-Decision: <status> <email>
Estado de conflito deixado no worktree (--leave-conflicts) fica em <git-dir>/prototype-member-vetting.json
até `finalize` ou `abort`.
Override de teste: MEMBER_VETTING_COMPONENT_SCAN=<caminho> (vazio desliga) substitui
scripts/component-scan.py.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changelog_tools as ct  # noqa: E402
import protolib as pl  # noqa: E402

T_ROLLBACK_MEMBER = 'Prototype-Rollback-Member'
T_REINSTATE_OF = 'Prototype-Reinstate-Of'
T_DECISION = 'Prototype-Member-Decision'
STATE_NAME = 'prototype-member-vetting.json'
CFG = pl.CONFIG_NAME
CONFLICT_MARKERS = ('<<<<<<< ', '>>>>>>> ')
CHANGELOG = ct.CHANGELOG_REL
# Arquivos de registro que todo mundo toca: não fazem de ninguém "dependente".
SHARED_LEDGERS = {CFG, CHANGELOG}
ROLLBACK_LINE = 'Revertido: trabalho de membro não aprovado'


class Stop(Exception):
    def __init__(self, status, problems, data=None, exit_code=1):
        super().__init__(status)
        self.status, self.problems, self.data, self.exit_code = status, problems, data or {}, exit_code


def out(repo, *args):
    r = pl.git(repo, *args)
    return r.stdout.strip() if r.returncode == 0 else None


def sha_of(repo, ref):
    return out(repo, 'rev-parse', '--verify', '-q', f'{ref}^{{commit}}')


def days_since(iso):
    try:
        then = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return 0
    return max(0, (datetime.now(timezone.utc) - then).days)


def one_line(text):
    return ' '.join((text or '').split())


# ---------------------------------------------------------------- contexto e refs

class Ctx:
    def __init__(self, repo, actor):
        self.repo, self.actor = repo, pl.norm_email(actor)
        local_cfg, err = pl.load_config(repo)
        if err:
            raise Stop('INVALID_CONFIG', [pl.problem('INVALID_CONFIG', err)])
        base = local_cfg or {}
        branches = base.get('branches') or {}
        self.remote = base.get('remote') or 'origin'
        self.beta = branches.get('beta') or 'beta'
        self.official = branches.get('official') or 'main'
        self.warnings = []
        self.fetch_ok = True

    def fetch(self):
        r = pl.git(self.repo, 'fetch', '-q', self.remote, timeout=120)
        if r.returncode != 0:
            self.fetch_ok = False
            self.warnings.append(pl.problem('FETCH_FAILED', f'git fetch {self.remote} falhou: '
                                            + (r.stderr.strip().splitlines() or ['erro desconhecido'])[-1]))

    @property
    def remote_beta(self):
        return f'refs/remotes/{self.remote}/{self.beta}'

    def beta_ref(self):
        for ref in (self.remote_beta, f'refs/heads/{self.beta}'):
            if sha_of(self.repo, ref):
                return ref
        raise Stop('BETA_MISSING', [pl.problem('BETA_MISSING', f'A branch beta "{self.beta}" não existe '
                                               'nem localmente nem no remoto.')])

    def official_ref(self):
        for ref in (f'refs/remotes/{self.remote}/{self.official}', f'refs/heads/{self.official}'):
            if sha_of(self.repo, ref):
                return ref
        return None

    def cfg_at(self, ref):
        r = pl.git(self.repo, 'show', f'{ref}:{CFG}')
        if r.returncode != 0:
            raise Stop('NO_CONFIG', [pl.problem('NO_CONFIG', f'{CFG} não existe na branch beta.')])
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError as e:
            raise Stop('INVALID_CONFIG', [pl.problem('INVALID_CONFIG', f'{CFG} inválido na beta: {e}')])

    def state_path(self):
        p = Path(out(self.repo, 'rev-parse', '--git-path', STATE_NAME))
        return p if p.is_absolute() else self.repo / p

    def load_state(self):
        p = self.state_path()
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None

    def save_state(self, st):
        self.state_path().write_text(json.dumps(st, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def clear_state(self):
        p = self.state_path()
        if p.exists():
            p.unlink()


def require_promoter(ctx, cfg):
    actor = pl.find_member(cfg, ctx.actor)
    if not pl.is_promoter(actor):
        raise Stop('NOT_PROMOTER', [pl.problem('NOT_PROMOTER', f'{ctx.actor} não é promoter aprovado: só um '
                                               'promoter aprovado decide sobre pessoas.')])
    return actor


def require_member(cfg, email):
    m = pl.find_member(cfg, email)
    if m is None:
        raise Stop('MEMBER_NOT_FOUND', [pl.problem('MEMBER_NOT_FOUND', f'{email} não está no roster.')])
    return m


def write_blockers(ctx, allow_state=False):
    """Pré-condições de escrita; devolve a lista de problemas (vazia = pode escrever)."""
    probs = []
    if not ctx.fetch_ok:
        probs.extend(ctx.warnings)
    branch = out(ctx.repo, 'symbolic-ref', '--short', '-q', 'HEAD')
    if branch != ctx.beta:
        probs.append(pl.problem('NOT_ON_BETA', f'A branch em uso é "{branch}"; troque para "{ctx.beta}" '
                                f'(git switch {ctx.beta}) antes de decidir.'))
    if out(ctx.repo, 'status', '--porcelain'):
        probs.append(pl.problem('DIRTY_WORKTREE', 'Há alterações não commitadas; commite ou guarde-as antes.'))
    local, remote = sha_of(ctx.repo, f'refs/heads/{ctx.beta}'), sha_of(ctx.repo, ctx.remote_beta)
    if not remote:
        probs.append(pl.problem('BETA_NOT_ON_REMOTE', f'{ctx.remote}/{ctx.beta} não existe no remoto.'))
    elif local != remote:
        counts = out(ctx.repo, 'rev-list', '--left-right', '--count', f'{ctx.beta}...{ctx.remote_beta}') or '? ?'
        ahead, behind = counts.split()
        probs.append(pl.problem('BETA_OUT_OF_SYNC', f'A beta local difere de {ctx.remote}/{ctx.beta} '
                                f'({ahead} à frente, {behind} atrás); sincronize (git pull --ff-only) antes.'))
    if not allow_state and ctx.load_state():
        probs.append(pl.problem('OPERATION_IN_PROGRESS', 'Há um rollback com conflitos em andamento; conclua com '
                                '`finalize` ou desista com `abort`.'))
    return probs


# ---------------------------------------------------------------- janela e relatório

def window_commits(repo, beta_ref, anchor):
    args = ['log', '--no-merges', '--topo-order', '--reverse',
            '--format=%H%x1f%ae%x1f%an%x1f%aI%x1f%s%x1f%B%x1e', beta_ref]
    if anchor:
        args.append(f'^{anchor}')
    raw = out(repo, *args) or ''
    commits = []
    for rec in raw.split('\x1e'):
        rec = rec.strip('\n')
        if not rec:
            continue
        sha, ae, an, date, subject, body = rec.split('\x1f', 5)
        trailers = pl.parse_trailers(body)
        files = (out(repo, 'diff-tree', '--root', '--no-commit-id', '--name-only', '-r', '-z', sha) or '')
        commits.append({'sha': sha, 'authorEmail': ae, 'authorName': an, 'date': date, 'subject': subject,
                        'actor': pl.norm_email(trailers.get(pl.T_ACTOR) or ae),
                        'files': [f for f in files.split('\0') if f]})
    return commits


def resolve_since(ctx, beta_ref, since):
    sha = sha_of(ctx.repo, since)
    if sha:
        return sha
    before = out(ctx.repo, 'rev-list', '-1', f'--before={since}', beta_ref)
    if before is None:
        raise Stop('INVALID_SINCE', [pl.problem('INVALID_SINCE', f'--since "{since}" não é commit nem data.')],
                   exit_code=2)
    return before or None


def member_view(member, cfg):
    expiry = (cfg.get('policy') or {}).get('pendingExpiryDays', 7)
    days = days_since(member.get('registeredAt'))
    keys = ('name', 'email', 'hostLogin', 'roles', 'profile', 'status', 'identityEvidence', 'registeredAt',
            'statusChangedAt', 'statusChangedAtCommit', 'decidedBy', 'decidedAt', 'reason', 'statusHistory')
    view = {k: member.get(k) for k in keys if k in member}
    if member.get('status') == 'pending':
        view.update({'daysPending': days, 'expired': days > expiry, 'pendingExpiryDays': expiry})
    return view


def build_report(ctx, cfg, member, beta_ref, since=None):
    email = pl.norm_email(member.get('email'))
    anchor = resolve_since(ctx, beta_ref, since) if since else member.get('statusChangedAtCommit')
    warnings = []
    if anchor and not sha_of(ctx.repo, anchor):
        warnings.append(pl.problem('ANCHOR_MISSING', f'A âncora {anchor} não existe neste clone; a janela '
                                   'cobre todo o histórico da beta.'))
        anchor = None
    commits = window_commits(ctx.repo, beta_ref, anchor)
    official_ref = ctx.official_ref()
    in_official = set()
    if official_ref:
        args = ['rev-list', official_ref] + ([f'^{anchor}'] if anchor else [])
        in_official = set((out(ctx.repo, *args) or '').split())

    def item(c, files=None):
        flag = c['sha'] in in_official
        return {'sha': c['sha'], 'shortSha': c['sha'][:8], 'subject': c['subject'], 'date': c['date'],
                'authorName': c['authorName'], 'authorEmail': c['authorEmail'], 'actor': c['actor'],
                'files': files or c['files'], 'inOfficial': flag, 'betaOnly': not flag, 'index': idx_of[c['sha']]}

    idx_of = {c['sha']: i for i, c in enumerate(commits)}
    beta_only, official, roster_only, dependents = [], [], [], []
    touched = set()
    for c in commits:
        work_files = [f for f in c['files'] if f != CFG]
        if c['actor'] == email:
            if not work_files:
                roster_only.append(item(c))
                continue
            it = item(c)
            (official if it['inOfficial'] else beta_only).append(it)
            touched.update(f for f in work_files if f not in SHARED_LEDGERS)
        else:
            overlap = sorted(touched.intersection(work_files))
            if overlap:
                dependents.append(item(c, overlap))
    return {
        'member': member_view(member, cfg),
        'window': {'anchor': anchor, 'anchorSource': 'since' if since else 'statusChangedAtCommit',
                   'betaRef': beta_ref, 'betaHead': sha_of(ctx.repo, beta_ref), 'officialRef': official_ref,
                   'commitsInWindow': len(commits)},
        'betaOnly': beta_only, 'inOfficial': official, 'rosterOnly': roster_only, 'dependents': dependents,
        'summary': {'betaOnly': len(beta_only), 'inOfficial': len(official), 'rosterOnly': len(roster_only),
                    'dependents': len(dependents),
                    'filesTouched': sorted(touched)},
    }, warnings


# ---------------------------------------------------------------- aplicação de passos (revert/cherry-pick)

def unmerged(wt):
    return [f for f in (out(wt, 'diff', '--name-only', '--diff-filter=U') or '').splitlines() if f]


def apply_steps(wt, base, steps):
    """steps = [(kind, sha)]; devolve {'done': [...], 'conflict': None|{...}}. O config nunca é tocado."""
    done = []
    for i, (kind, sha) in enumerate(steps):
        r = pl.git(wt, kind, '--no-commit', sha)
        if r.returncode != 0:
            files = unmerged(wt)
            if not files:
                raise Stop('GIT_ERROR', [pl.problem('GIT_ERROR', f'git {kind} {sha[:8]} falhou: '
                                                    + (r.stderr.strip().splitlines() or ['?'])[-1])])
            if CFG in files:
                pl.git(wt, 'checkout', base, '--', CFG, check=True)
                files = [f for f in files if f != CFG]
            if CHANGELOG in files and resolve_changelog(wt):
                files = [f for f in files if f != CHANGELOG]
            if files:
                return {'done': done, 'conflict': {'kind': kind, 'sha': sha, 'files': files,
                                                   'remaining': [list(s) for s in steps[i + 1:]]}}
        done.append(sha)
    return {'done': done, 'conflict': None}


def resolve_changelog(wt):
    """Conflito no changelog: merge de 3 vias por versão/linha (changelog_tools); False se não der."""
    stages = {}
    for n in (1, 2, 3):
        r = pl.git(wt, 'show', f':{n}:{CHANGELOG}')
        stages[n] = r.stdout if r.returncode == 0 else None
    if stages[2] is None or stages[3] is None:
        return False
    try:
        text = ct.resolve_changelog_text(stages[1], stages[2], stages[3])
    except (ct.ConflictError, ct.ChangelogError):
        return False
    (Path(wt) / CHANGELOG).write_text(text, encoding='utf-8')
    pl.git(wt, 'add', '--', CHANGELOG, check=True)
    return True


def add_rollback_changelog_line(wt):
    """Uma linha sem identificar a pessoa: no Pendente, senão na beta mais recente, senão num Pendente novo."""
    if not (Path(wt) / CHANGELOG).exists():
        return False
    entries = ct.read_entries(wt)
    top = entries[0] if entries else None
    if not top or not (ct.is_pending(top) or ct.is_beta(top)):
        top = {'version': ct.PENDING, 'date': datetime.now().strftime('%Y-%m-%d'), 'changes': []}
        entries.insert(0, top)
    if ROLLBACK_LINE not in top['changes']:
        top['changes'].append(ROLLBACK_LINE)
    ct.write_entries(wt, entries)
    pl.git(wt, 'add', '--', CHANGELOG, check=True)
    return True


def untracked(wt):
    return set((out(wt, 'ls-files', '--others', '--exclude-standard') or '').splitlines())


def restore(wt, base, untracked_before):
    """Desfaz só o que este comando introduziu (o worktree estava limpo em `base` ao começar)."""
    for kind in ('revert', 'cherry-pick'):
        pl.git(wt, kind, '--quit')
    pl.git(wt, 'reset', '-q', '--hard', base, check=True)
    for f in untracked(wt) - untracked_before:
        p = Path(wt) / f
        if p.is_file() or p.is_symlink():
            p.unlink()


def has_markers(path, strict):
    """strict: também o separador `=======` (só nos arquivos que de fato conflitaram)."""
    try:
        lines = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return False
    return any(ln.startswith(CONFLICT_MARKERS) or (strict and ln == '=======') for ln in lines)


def component_scan_path():
    env = os.environ.get('MEMBER_VETTING_COMPONENT_SCAN')
    if env is not None:
        return Path(env) if env else None
    return Path(__file__).resolve().parent / 'component-scan.py'


def component_scan(wt):
    """Roda component-scan --lint --rules; devolve None (indisponível) ou (ok, [mensagens])."""
    scan = component_scan_path()
    if not (scan and scan.exists()):
        return None
    r = subprocess.run([sys.executable, str(scan), '--repo', str(wt), '--lint', '--rules'],
                       capture_output=True, text=True, timeout=300)
    try:
        msgs = [p.get('message', '') for p in json.loads(r.stdout).get('problems', [])]
    except (json.JSONDecodeError, AttributeError):
        msgs = [(r.stderr.strip() or r.stdout.strip())[-400:]] if r.returncode != 0 else []
    return r.returncode == 0, msgs


def scan_baseline(wt):
    """Problemas que a beta já tinha antes do rollback não o bloqueiam: só os novos contam."""
    res = component_scan(wt)
    return res[1] if res else []


def run_checks(wt, base, baseline=()):
    """build.py, node --check nos .js alterados e component-scan --lint --rules. Devolve (problemas, avisos)."""
    probs, notes = [], []
    wt = Path(wt)
    if (wt / 'build.py').exists():
        r = subprocess.run([sys.executable, 'build.py'], cwd=wt, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            probs.append(pl.problem('BUILD_FAILED', 'python3 build.py falhou: '
                                    + (r.stderr.strip() or r.stdout.strip())[-400:]))
    changed = (out(wt, 'diff', '--name-only', base) or '').splitlines()
    js = [f for f in changed if f.endswith('.js') and (wt / f).exists()]
    if js:
        node = shutil.which('node')
        if not node:
            notes.append(pl.problem('NODE_MISSING', 'node não encontrado: `node --check` dos .js foi pulado.'))
        for f in js if node else []:
            r = subprocess.run([node, '--check', f], cwd=wt, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                probs.append(pl.problem('JS_SYNTAX', f'node --check {f} falhou: ' + r.stderr.strip()[-400:]))
    res = component_scan(wt)
    if res and not res[0]:
        new = [m for m in res[1] if m not in set(baseline)]
        if new or not res[1]:
            probs.append(pl.problem('COMPONENT_SCAN_FAILED', 'component-scan --lint --rules falhou: '
                                    + '; '.join(new)[-600:]))
        else:
            notes.append(pl.problem('COMPONENT_SCAN_PREEXISTING', 'component-scan só acusou problemas que a beta '
                                    'já tinha antes; não bloqueiam o rollback.'))
    return probs, notes


# ---------------------------------------------------------------- registro da decisão

def record_decision(member, status, actor, anchor, reason=None, roles=None, profile=None):
    at = pl.now_iso()
    member.update({'status': status, 'statusChangedAt': at, 'statusChangedAtCommit': anchor,
                   'decidedBy': actor, 'decidedAt': at})
    if roles:
        member['roles'] = roles
    if profile:
        member['profile'] = profile
    if reason:
        member['reason'] = reason
    else:
        member.pop('reason', None)
    entry = {'status': status, 'at': at, 'commit': anchor, 'by': actor}
    if reason:
        entry['reason'] = reason
    member.setdefault('statusHistory', []).append(entry)
    return member


def write_roster(wt, base, email, status, actor, reason=None, roles=None, profile=None):
    pl.git(wt, 'checkout', base, '--', CFG, check=True)
    cfg, err = pl.load_config(wt)
    if err or cfg is None:
        raise Stop('INVALID_CONFIG', [pl.problem('INVALID_CONFIG', err or f'{CFG} ausente.')])
    member = record_decision(require_member(cfg, email), status, actor, base, reason, roles, profile)
    pl.save_config(wt, cfg)
    pl.git(wt, 'add', '--', CFG, check=True)
    return member


def push(ctx):
    r = pl.git(ctx.repo, 'push', ctx.remote, f'refs/heads/{ctx.beta}:refs/heads/{ctx.beta}', timeout=120)
    if r.returncode != 0:
        raise Stop('PUSH_REJECTED', [pl.problem('PUSH_REJECTED', 'O commit foi feito localmente, mas o push da '
                                                'beta foi recusado (alguém enviou antes?). Rode `git pull '
                                                '--rebase` e `git push` — nunca force. Detalhe: '
                                                + (r.stderr.strip().splitlines() or ['?'])[-1])],
                   {'commit': sha_of(ctx.repo, 'HEAD')})


def subject_for(status, email):
    verbs = {'approved': 'aprova', 'rejected': 'reprova', 'revoked': 'revoga'}
    return f'chore(roster): {verbs.get(status, status)} {email}'


# ---------------------------------------------------------------- subcomandos

def cmd_list(ctx, args):
    ctx.fetch()
    cfg = ctx.cfg_at(ctx.beta_ref())
    pend = [member_view(m, cfg) for m in cfg.get('members', []) if m.get('status') == 'pending']
    items = [{k: v.get(k) for k in ('name', 'email', 'registeredAt', 'daysPending', 'expired',
                                    'identityEvidence', 'statusChangedAtCommit')} for v in pend]
    return 'OK', {'pending': items, 'expiredCount': sum(1 for i in items if i['expired']),
                  'pendingExpiryDays': (cfg.get('policy') or {}).get('pendingExpiryDays', 7)}, []


def cmd_report(ctx, args):
    ctx.fetch()
    beta_ref = ctx.beta_ref()
    cfg = ctx.cfg_at(beta_ref)
    rep, warns = build_report(ctx, cfg, require_member(cfg, args.email), beta_ref, args.since)
    return 'OK', strip_index(rep), warns


def parse_roles(raw):
    roles = [r.strip() for r in (raw or '').split(',') if r.strip()]
    bad = [r for r in roles if r not in pl.ROLES]
    if bad or (raw is not None and not roles):
        raise Stop('INVALID_ARGS', [pl.problem('INVALID_ARGS', f'--roles inválido: use {"|".join(pl.ROLES)} '
                                               '(lista separada por vírgula).')], exit_code=2)
    return roles or None


def decision_setup(ctx, args):
    ctx.fetch()
    beta_ref = ctx.beta_ref()
    cfg = ctx.cfg_at(beta_ref)
    require_promoter(ctx, cfg)
    member = require_member(cfg, args.email)
    if pl.norm_email(args.email) == ctx.actor:
        raise Stop('SELF_DECISION', [pl.problem('SELF_DECISION', 'Um promoter não decide sobre si mesmo; peça '
                                                'a outro promoter.')])
    return beta_ref, cfg, member


def cmd_approve(ctx, args):
    beta_ref, cfg, member = decision_setup(ctx, args)
    roles = parse_roles(args.roles)
    status = member.get('status')
    if status in ('rejected', 'revoked'):
        raise Stop('USE_REINSTATE', [pl.problem('USE_REINSTATE', f'{args.email} está "{status}"; use `reinstate` '
                                                'para desfazer a decisão e o rollback.')])
    if status == 'approved' and member.get('roles') == roles and (not args.profile
                                                                  or member.get('profile') == args.profile):
        return 'NOTHING_TO_DO', {'member': member_view(member, cfg)}, []
    after = dict(member, roles=roles, status='approved', **({'profile': args.profile} if args.profile else {}))
    plan = {'member': args.email, 'from': {'status': status, 'roles': member.get('roles'),
                                           'profile': member.get('profile')},
            'to': {'status': 'approved', 'roles': roles, 'profile': after.get('profile')}}
    if not args.execute:
        return dry_run_result(ctx, plan, [])
    blockers = write_blockers(ctx)
    if blockers:
        raise Stop(blockers[0]['code'], blockers)
    base = sha_of(ctx.repo, 'HEAD')
    m = write_roster(ctx.repo, base, args.email, 'approved', ctx.actor, args.reason, roles, args.profile)
    pl.commit_with_trailers(ctx.repo, subject_for('approved', args.email),
                            {pl.T_ACTOR: ctx.actor, pl.T_MEMBER_STATUS: 'approved',
                             T_DECISION: f'approved {pl.norm_email(args.email)}'})
    push(ctx)
    return 'APPROVED', {'commit': sha_of(ctx.repo, 'HEAD'), 'anchor': base, 'member': member_view(m, cfg)}, []


def dry_run_result(ctx, plan, warns, extra=None):
    blockers = write_blockers(ctx)
    data = {'dryRun': True, 'plan': plan,
            'next': 'Repita com --execute para gravar.' if not blockers else
            'Resolva os bloqueios em `problems` antes de --execute.'}
    data.update(extra or {})
    if blockers:
        raise Stop('DRY_RUN', blockers, data)
    return 'DRY_RUN', data, warns


def simulate(ctx, beta_ref, steps_list):
    """Roda as tentativas numa worktree temporária destacada e devolve a previsão."""
    tmp = Path(tempfile.mkdtemp(prefix='member-vetting-'))
    wt = tmp / 'wt'
    head = sha_of(ctx.repo, beta_ref)
    pl.git(ctx.repo, 'worktree', 'add', '-q', '--detach', str(wt), head, check=True)
    try:
        res, baseline = None, scan_baseline(wt)
        for steps in steps_list:
            res = apply_steps(wt, head, steps)
            if not res['conflict']:
                break
            restore(wt, head, set())
        if res['conflict']:
            return {'prediction': 'CONFLICT', 'conflict': res['conflict']}
        probs, notes = run_checks(wt, head, baseline)
        return {'prediction': 'DEPENDENTS_BROKEN' if probs else 'OK', 'checks': probs, 'notes': notes}
    finally:
        pl.git(ctx.repo, 'worktree', 'remove', '--force', str(wt))
        pl.git(ctx.repo, 'worktree', 'prune')
        shutil.rmtree(tmp, ignore_errors=True)


def involved(report, files):
    files = set(files)
    pool = report['betaOnly'] + report['inOfficial'] + report['dependents']
    return [{'sha': c['sha'], 'subject': c['subject'], 'actor': c['actor'], 'files': sorted(files & set(c['files']))}
            for c in pool if files & set(c['files'])]


def strip_index(report):
    for c in report['betaOnly'] + report['inOfficial'] + report['rosterOnly'] + report['dependents']:
        c.pop('index', None)
    return report


def conflict_data(st, report=None):
    data = {'conflictFiles': st['conflictFiles'], 'conflictCommit': st['conflictCommit'],
            'conflictKind': st['conflictKind'], 'remainingSteps': st.get('remaining', [])}
    if report:
        data.update({'involvedCommits': involved(report, st['conflictFiles']), 'dependents': report['dependents']})
    return data


def cmd_reject(ctx, args):
    beta_ref, cfg, member = decision_setup(ctx, args)
    status = member.get('status')
    if status not in ('pending', 'approved'):
        raise Stop('ALREADY_DECIDED', [pl.problem('ALREADY_DECIDED', f'{args.email} já está "{status}".')])
    new_status = 'rejected' if status == 'pending' else 'revoked'
    if new_status == 'revoked':
        if not args.since:
            raise Stop('NEEDS_CUTOFF', [pl.problem('NEEDS_CUTOFF', 'Membro aprovado: a janela do rollback não é '
                                                   'automática. Pergunte ao promoter a data/commit de corte e '
                                                   'passe --since.')])
        others = [m for m in cfg.get('members', []) if pl.is_promoter(m)
                  and pl.norm_email(m.get('email')) != pl.norm_email(args.email)]
        if pl.is_promoter(member) and not others:
            raise Stop('LAST_PROMOTER', [pl.problem('LAST_PROMOTER', 'É o último promoter aprovado; aprove outro '
                                                    'promoter antes.')])
    report, warns = build_report(ctx, cfg, member, beta_ref, args.since)
    targets = report['betaOnly'] + (report['inOfficial'] if args.rollback_main_items else [])
    targets.sort(key=lambda c: c['index'], reverse=True)
    steps = [('revert', c['sha']) for c in targets]
    blocking = blocking_dependents(report, targets)
    requires_promotion = bool(args.rollback_main_items and report['inOfficial'])
    plan = {'member': args.email, 'from': status, 'to': new_status, 'reason': args.reason,
            'revert': [c['sha'] for c in targets], 'keptInOfficial': [] if args.rollback_main_items else
            [c['sha'] for c in report['inOfficial']], 'requiresPromotion': requires_promotion,
            'changelogLine': ROLLBACK_LINE}
    strip_index(report)
    alerts = ['Remova o acesso da pessoa no host de código (a skill não revoga acesso).',
              'Marque como revoked os artefatos de beta e preview que ela publicou (artifacts.py) e avise quem '
              'já os viu; o artefato oficial só muda por promoção.']
    if requires_promotion:
        alerts.append('Itens já na oficial foram revertidos só na beta: a oficial muda apenas com uma promoção.')
    if not args.execute:
        sim = simulate(ctx, beta_ref, [steps]) if steps else {'prediction': 'OK'}
        return dry_run_result(ctx, dict(plan, simulation=sim), warns,
                              {'report': report, 'requiresPromotion': requires_promotion, 'alerts': alerts,
                               'requiresAck': bool(blocking) and not args.ack_dependents,
                               'blockingDependents': blocking})
    if blocking and not args.ack_dependents:
        raise Stop('DEPENDENTS_FOUND', [pl.problem('DEPENDENTS_FOUND', f'{len(blocking)} commit(s) de outras '
                                                   'pessoas mexem depois nos mesmos arquivos do que seria '
                                                   'revertido; nada foi alterado. Mostre ao promoter e, se ele '
                                                   'decidir seguir, repita com --ack-dependents.')],
                   {'dependents': blocking, 'revert': plan['revert']})
    blockers = write_blockers(ctx)
    if blockers:
        raise Stop(blockers[0]['code'], blockers)
    base = sha_of(ctx.repo, 'HEAD')
    st = {'op': 'reject', 'email': pl.norm_email(args.email), 'actor': ctx.actor, 'base': base,
          'newStatus': new_status, 'reason': args.reason, 'rollbackOf': plan['revert'],
          'requiresPromotion': requires_promotion, 'alerts': alerts}
    return run_and_finish(ctx, st, [steps], args.leave_conflicts, report)


def blocking_dependents(report, targets):
    """Dependentes posteriores a algum commit a reverter, com os arquivos em comum com ele."""
    out_ = []
    for d in report['dependents']:
        common = set()
        for t in targets:
            if t['index'] < d['index']:
                common |= set(t['files']) & set(d['files'])
        if common:
            out_.append({'sha': d['sha'], 'subject': d['subject'], 'date': d['date'], 'actor': d['actor'],
                         'authorName': d['authorName'], 'authorEmail': d['authorEmail'],
                         'commonFiles': sorted(common), 'inOfficial': d['inOfficial']})
    return out_


def find_rollback(ctx, beta_ref, email):
    raw = out(ctx.repo, 'log', '--format=%H%x1f%B%x1e', beta_ref) or ''
    commits = []
    for rec in raw.split('\x1e'):
        rec = rec.strip('\n')
        if rec:
            sha, body = rec.split('\x1f', 1)
            commits.append((sha, pl.parse_trailers(body)))
    undone = {t.get(T_REINSTATE_OF) for _, t in commits if t.get(T_REINSTATE_OF)}
    for sha, t in commits:
        if pl.norm_email(t.get(T_ROLLBACK_MEMBER)) == email and sha not in undone:
            originals = [s for s in (t.get(pl.T_ROLLBACK_OF) or '').split(',') if s.strip()]
            return sha, [s.strip() for s in originals]
    return None, []


def cmd_reinstate(ctx, args):
    beta_ref, cfg, member = decision_setup(ctx, args)
    status = member.get('status')
    if status not in ('rejected', 'revoked'):
        raise Stop('NOT_REJECTED', [pl.problem('NOT_REJECTED', f'{args.email} está "{status}": nada a reintegrar.')])
    roles = parse_roles(args.roles) or member.get('roles') or ['contributor']
    email = pl.norm_email(args.email)
    rollback, originals = find_rollback(ctx, beta_ref, email)
    attempts = []
    if rollback:
        attempts = [[('revert', rollback)], [('cherry-pick', s) for s in reversed(originals)]]
    plan = {'member': args.email, 'from': status, 'to': 'approved', 'roles': roles, 'rollbackCommit': rollback,
            'reapply': originals[::-1]}
    if not args.execute:
        sim = simulate(ctx, beta_ref, attempts) if attempts else {'prediction': 'OK'}
        return dry_run_result(ctx, dict(plan, simulation=sim), [])
    blockers = write_blockers(ctx)
    if blockers:
        raise Stop(blockers[0]['code'], blockers)
    base = sha_of(ctx.repo, 'HEAD')
    st = {'op': 'reinstate', 'email': email, 'actor': ctx.actor, 'base': base, 'newStatus': 'approved',
          'reason': args.reason, 'roles': roles, 'profile': args.profile, 'reinstateOf': rollback}
    return run_and_finish(ctx, st, attempts, args.leave_conflicts, None)


def run_and_finish(ctx, st, attempts, leave, report):
    base, before = st['base'], untracked(ctx.repo)
    st['scanBaseline'] = scan_baseline(ctx.repo)
    res = {'conflict': None}
    for i, steps in enumerate(attempts):
        res = apply_steps(ctx.repo, base, steps)
        if not res['conflict']:
            break
        if i < len(attempts) - 1:
            restore(ctx.repo, base, before)
    if res['conflict']:
        c = res['conflict']
        st.update({'conflictFiles': c['files'], 'conflictCommit': c['sha'], 'conflictKind': c['kind'],
                   'remaining': c['remaining']})
        if not leave:
            restore(ctx.repo, base, before)
            raise Stop('CONFLICT', [pl.problem('CONFLICT', 'O rollback conflita com trabalho posterior; nada foi '
                                               'alterado. Decida com o promoter ou repita com --leave-conflicts.')],
                       conflict_data(st, report))
        if report:
            st['report'] = {'dependents': report['dependents'],
                            'involvedCommits': involved(report, c['files'])}
        st['untrackedBefore'] = sorted(before)
        ctx.save_state(st)
        raise Stop('CONFLICT_LEFT', [pl.problem('CONFLICT_LEFT', 'Conflitos deixados no worktree: resolva com o '
                                                'promoter e conclua com `finalize --email ... --execute`.')],
                   dict(conflict_data(st, report)))
    return finish(ctx, st, before, keep_on_failure=False)


def finish(ctx, st, before, keep_on_failure):
    base, email = st['base'], st['email']
    m = write_roster(ctx.repo, base, email, st['newStatus'], st['actor'], st.get('reason'),
                     st.get('roles'), st.get('profile'))
    changelog, pre = False, []
    try:
        changelog = add_rollback_changelog_line(ctx.repo) if st['op'] == 'reject' else False
    except ct.ChangelogError as e:
        pre.append(pl.problem('CHANGELOG_INVALID', f'Não deu para registrar o rollback no changelog: {e}'))
    probs, notes = run_checks(ctx.repo, base, st.get('scanBaseline', []))
    probs = pre + probs
    if probs:
        if keep_on_failure:
            raise Stop('DEPENDENTS_BROKEN', probs, {'kept': 'Worktree mantido com a resolução; corrija e rode '
                                                    '`finalize` de novo, ou `abort`.'})
        restore(ctx.repo, base, before)
        ctx.clear_state()
        raise Stop('DEPENDENTS_BROKEN', probs, {'restoredTo': base, 'nothingCommitted': True})
    trailers = {pl.T_ACTOR: st['actor'], pl.T_MEMBER_STATUS: 'approved'}
    if st['op'] == 'reject':
        trailers.update({pl.T_ROLLBACK_OF: ','.join(st['rollbackOf']),
                         pl.T_ROLLBACK_REASON: one_line(st.get('reason')),
                         T_ROLLBACK_MEMBER: email if st['rollbackOf'] else None})
    else:
        trailers[T_REINSTATE_OF] = st.get('reinstateOf')
    trailers[T_DECISION] = f"{st['newStatus']} {email}"
    subject = subject_for(st['newStatus'], email) if st['op'] == 'reject' else f'chore(roster): reintegra {email}'
    if st['op'] == 'reject' and st['rollbackOf']:
        subject += f" e reverte {len(st['rollbackOf'])} commit(s)"
    r = pl.commit_with_trailers(ctx.repo, subject, trailers)
    if r.returncode != 0:
        raise Stop('GIT_ERROR', [pl.problem('GIT_ERROR', 'git commit falhou: ' + r.stderr.strip())])
    ctx.clear_state()
    push(ctx)
    data = {'commit': sha_of(ctx.repo, 'HEAD'), 'anchor': base, 'member': member_view(m, {}),
            'checks': 'ok', 'notes': notes}
    if st['op'] == 'reject':
        data.update({'rolledBack': st['rollbackOf'], 'requiresPromotion': st.get('requiresPromotion', False),
                     'changelogUpdated': changelog,
                     'alerts': st.get('alerts', [])})
    else:
        data['reinstateOf'] = st.get('reinstateOf')
    status = {'rejected': 'REJECTED', 'revoked': 'REVOKED'}.get(st['newStatus'], 'REINSTATED')
    return status, data, []


def load_matching_state(ctx, args):
    cfg = ctx.cfg_at(f'refs/heads/{ctx.beta}' if sha_of(ctx.repo, f'refs/heads/{ctx.beta}') else ctx.beta_ref())
    require_promoter(ctx, cfg)
    st = ctx.load_state()
    if not st:
        raise Stop('NO_OPERATION', [pl.problem('NO_OPERATION', 'Não há rollback com conflitos em andamento.')])
    if st['email'] != pl.norm_email(args.email):
        raise Stop('STATE_MISMATCH', [pl.problem('STATE_MISMATCH', f'A operação em andamento é sobre {st["email"]}.')])
    if sha_of(ctx.repo, 'HEAD') != st['base'] or out(ctx.repo, 'symbolic-ref', '--short', '-q', 'HEAD') != ctx.beta:
        raise Stop('HEAD_MOVED', [pl.problem('HEAD_MOVED', 'HEAD não está mais na beta do início da operação; '
                                             'use `abort` e recomece.')])
    return st


def cmd_finalize(ctx, args):
    st = load_matching_state(ctx, args)
    changed = set((out(ctx.repo, 'diff', '--name-only', st['base']) or '').splitlines()) | set(unmerged(ctx.repo))
    strict = set(st['conflictFiles'])
    marked = sorted(f for f in changed | strict if has_markers(ctx.repo / f, f in strict))
    if marked:
        raise Stop('UNRESOLVED_CONFLICTS', [pl.problem('UNRESOLVED_CONFLICTS', 'Ainda há marcadores de conflito: '
                                                       + ', '.join(marked))], {'files': marked})
    if not args.execute:
        return 'DRY_RUN', {'dryRun': True, 'plan': {'op': st['op'], 'member': st['email'],
                                                    'remainingSteps': st.get('remaining', [])}}, []
    pl.git(ctx.repo, 'add', '-A', '--', *st['conflictFiles'], check=True)
    for kind in ('revert', 'cherry-pick'):
        pl.git(ctx.repo, kind, '--quit')
    res = apply_steps(ctx.repo, st['base'], [tuple(s) for s in st.get('remaining', [])])
    if res['conflict']:
        c = res['conflict']
        st.update({'conflictFiles': c['files'], 'conflictCommit': c['sha'], 'conflictKind': c['kind'],
                   'remaining': c['remaining']})
        ctx.save_state(st)
        raise Stop('CONFLICT_LEFT', [pl.problem('CONFLICT_LEFT', 'Novo conflito ao continuar: resolva e rode '
                                                '`finalize` de novo.')], conflict_data(st))
    st['remaining'] = []
    ctx.save_state(st)
    return finish(ctx, st, set(st.get('untrackedBefore', [])), keep_on_failure=True)


def cmd_abort(ctx, args):
    st = load_matching_state(ctx, args)
    if not args.execute:
        return 'DRY_RUN', {'dryRun': True, 'plan': {'resetTo': st['base'], 'member': st['email']}}, []
    restore(ctx.repo, st['base'], set(st.get('untrackedBefore', [])))
    ctx.clear_state()
    return 'ABORTED', {'restoredTo': st['base']}, []


# ---------------------------------------------------------------- CLI

def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--execute', action='store_true', default=argparse.SUPPRESS,
                        help='grava de fato (sem ele: DRY-RUN)')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 parents=[common])
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email', required=True)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list', parents=[common])
    p = sub.add_parser('report', parents=[common])
    p.add_argument('--email', required=True)
    p.add_argument('--since', help='commit ou data de corte (substitui statusChangedAtCommit)')
    p = sub.add_parser('approve', parents=[common])
    p.add_argument('--email', required=True)
    p.add_argument('--roles', required=True)
    p.add_argument('--profile', choices=pl.PROFILES)
    p.add_argument('--reason')
    p = sub.add_parser('reject', parents=[common])
    p.add_argument('--email', required=True)
    p.add_argument('--reason', required=True)
    p.add_argument('--rollback-main-items', action='store_true')
    p.add_argument('--leave-conflicts', action='store_true')
    p.add_argument('--ack-dependents', action='store_true',
                   help='segue mesmo com dependentes (só depois de o promoter decidir)')
    p.add_argument('--since', help='corte obrigatório para membro já aprovado (vira revoked)')
    p = sub.add_parser('reinstate', parents=[common])
    p.add_argument('--email', required=True)
    p.add_argument('--roles')
    p.add_argument('--profile', choices=pl.PROFILES)
    p.add_argument('--reason')
    p.add_argument('--leave-conflicts', action='store_true')
    for name in ('finalize', 'abort'):
        p = sub.add_parser(name, parents=[common])
        p.add_argument('--email', required=True)
    args = ap.parse_args()
    args.execute = getattr(args, 'execute', False)

    repo = Path(args.repo).resolve()
    if pl.git(repo, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        sys.exit(pl.emit(False, 'NOT_A_REPO', problems=[pl.problem('NOT_A_REPO', f'"{args.repo}" não é um '
                                                                   'repositório git.')]))
    handlers = {'list': cmd_list, 'report': cmd_report, 'approve': cmd_approve, 'reject': cmd_reject,
                'reinstate': cmd_reinstate, 'finalize': cmd_finalize, 'abort': cmd_abort}
    try:
        ctx = Ctx(repo, args.actor_email)
        status, data, warns = handlers[args.cmd](ctx, args)
        if ctx.warnings or warns:
            data.setdefault('warnings', ctx.warnings + warns)
        sys.exit(pl.emit(True, status, data))
    except Stop as s:
        code = pl.emit(False, s.status, s.data, s.problems)
        sys.exit(s.exit_code if s.exit_code != 1 else code)


if __name__ == '__main__':
    main()
