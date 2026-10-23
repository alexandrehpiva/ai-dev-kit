#!/usr/bin/env python3
"""Liga a comunicação do time e instala/remove os hooks do Claude Code desta máquina (modo grupo v2).

Só stdlib. Padrão é DRY-RUN; `--execute` realiza.

  python3 comms-setup.py --repo . --actor-email promoter@example.test --enable --execute
  python3 comms-setup.py --repo . --install-hooks --execute        # só nesta máquina (settings.local.json)
  python3 comms-setup.py --repo . --uninstall-hooks --execute

--enable (só promoter aprovado): cria a branch órfã de comunicação (README) no remoto e grava `comms.enabled`
no prototype.config.json. O config alterado precisa ser compartilhado com o time pelo fluxo normal
(group-share.py); sem isso, os outros não veem a funcionalidade ligada.

--install-hooks: acrescenta SessionStart e UserPromptSubmit em `.claude/settings.local.json` (arquivo pessoal,
fora do git), apontando para o comms-hook.py DESTA instalação da skill. Nunca grava em
`.claude/settings.json` (versionado). Não mexe em hooks de outras origens; --uninstall-hooks remove só os nossos.
Cursor e outros harnesses: sem instalação automática (ver group-comms.md).

Status: DRY_RUN, ENABLED, ALREADY_ENABLED, HOOKS_INSTALLED, HOOKS_ALREADY_INSTALLED, HOOKS_REMOVED,
NOT_ALLOWED, INVALID_CONFIG, NOT_A_REPO, NOT_SYNCED.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comms_store as cs  # noqa: E402
import group_sync as gs  # noqa: E402
import protolib  # noqa: E402
from protolib import problem  # noqa: E402

HOOK_MARK = 'comms-hook.py'
EVENTS = ('SessionStart', 'UserPromptSubmit')


def fail(status, probs, data=None):
    return protolib.emit(False, status, data=data, problems=probs)


def hook_command(repo):
    script = Path(__file__).resolve().parent / 'comms-hook.py'
    return f'python3 "{script}" --repo "{Path(repo).resolve()}"'


def settings_path(repo):
    return Path(repo) / '.claude' / 'settings.local.json'


def load_settings(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8') or '{}')


def has_our_hook(entries):
    return any(HOOK_MARK in h.get('command', '') for e in entries for h in e.get('hooks', []))


def install_hooks(repo, execute):
    path = settings_path(repo)
    try:
        settings = load_settings(path)
    except json.JSONDecodeError as e:
        return fail('INVALID_SETTINGS', [problem('INVALID_SETTINGS', f'{path} não é JSON válido: {e}')])
    hooks = settings.setdefault('hooks', {})
    cmd = hook_command(repo)
    changed = []
    for ev in EVENTS:
        entries = hooks.setdefault(ev, [])
        if not has_our_hook(entries):
            entries.append({'hooks': [{'type': 'command', 'command': cmd, 'timeout': 15}]})
            changed.append(ev)
    data = {'settingsFile': str(path), 'events': list(EVENTS), 'command': cmd, 'willChange': changed}
    if not changed:
        return protolib.emit(True, 'HOOKS_ALREADY_INSTALLED', data=data)
    if not execute:
        return protolib.emit(True, 'DRY_RUN', data=data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ignore_note = ensure_ignored(repo)
    if ignore_note:
        data['gitignore'] = ignore_note
    return protolib.emit(True, 'HOOKS_INSTALLED', data=data)


def ensure_ignored(repo):
    """Garante `.claude/settings.local.json` no .gitignore do protótipo (arquivo pessoal)."""
    gi = Path(repo) / '.gitignore'
    line = '.claude/settings.local.json'
    text = gi.read_text(encoding='utf-8') if gi.exists() else ''
    if line in text.split():
        return None
    gi.write_text(text + ('' if text.endswith('\n') or not text else '\n') + line + '\n', encoding='utf-8')
    return f'{line} adicionado ao .gitignore'


def uninstall_hooks(repo, execute):
    path = settings_path(repo)
    try:
        settings = load_settings(path)
    except json.JSONDecodeError as e:
        return fail('INVALID_SETTINGS', [problem('INVALID_SETTINGS', f'{path} não é JSON válido: {e}')])
    removed = []
    for ev in EVENTS:
        entries = settings.get('hooks', {}).get(ev, [])
        kept = []
        for e in entries:
            hs = [h for h in e.get('hooks', []) if HOOK_MARK not in h.get('command', '')]
            if len(hs) != len(e.get('hooks', [])):
                removed.append(ev)
            if hs:
                kept.append(dict(e, hooks=hs))
        if entries:
            if kept:
                settings['hooks'][ev] = kept
            else:
                settings['hooks'].pop(ev, None)
    if 'hooks' in settings and not settings['hooks']:
        settings.pop('hooks')
    data = {'settingsFile': str(path), 'removedFrom': removed}
    if not removed:
        return protolib.emit(True, 'HOOKS_REMOVED', data=data)
    if not execute:
        return protolib.emit(True, 'DRY_RUN', data=data)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return protolib.emit(True, 'HOOKS_REMOVED', data=data)


def enable(repo, actor_email, execute):
    try:
        cfg, member, roster, email = cs.load_context(repo, actor_email, require_enabled=False)
    except cs.CommsError as e:
        return fail(e.code, [problem(e.code, e.message)])
    if not protolib.is_promoter(member):
        return fail('NOT_ALLOWED', [problem('NOT_ALLOWED', 'Só um promoter aprovado liga a comunicação do time.')])
    cur = cs.comms_cfg(cfg)
    data = {'branch': cur['branch'], 'alreadyEnabled': cur['enabled']}
    if not execute:
        data['plan'] = [f'criar a branch órfã "{cur["branch"]}" no remoto (README), se não existir',
                        'gravar comms.enabled = true no prototype.config.json',
                        'compartilhar o config com o time pelo fluxo normal (group-share.py)']
        return protolib.emit(True, 'DRY_RUN', data=data)
    try:
        info = cs.ensure_branch(repo, cfg, gs.actor_trailers(member))
    except cs.CommsError as e:
        return fail(e.code, [problem(e.code, e.message)], data)
    data.update(info)
    if not info.get('pushed'):
        return fail('NOT_SYNCED', [problem('NOT_SYNCED', 'A branch de comunicação foi criada só neste computador '
                                           '(sem acesso ao remoto). Rode de novo quando houver rede.')], data)
    if cur['enabled']:
        return protolib.emit(True, 'ALREADY_ENABLED', data=data)
    block = dict(cs.DEFAULTS, **(cfg.get('comms') or {}), enabled=True)
    cfg['comms'] = block
    protolib.save_config(repo, cfg)
    data['configChanged'] = True
    return protolib.emit(True, 'ENABLED', data=data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--actor-email')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--enable', action='store_true')
    g.add_argument('--install-hooks', action='store_true')
    g.add_argument('--uninstall-hooks', action='store_true')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.install_hooks:
        return install_hooks(repo, args.execute)
    if args.uninstall_hooks:
        return uninstall_hooks(repo, args.execute)
    return enable(repo, args.actor_email, args.execute)


if __name__ == '__main__':
    sys.exit(main())
