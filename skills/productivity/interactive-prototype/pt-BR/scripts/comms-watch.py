#!/usr/bin/env python3
"""Vigia local dos recados do time (camada L4): avisa pelo sistema, fora do agente. Só stdlib, Python 3.9+.

O agente só mostra recados quando a pessoa o aciona. Este vigia roda agendado pelo sistema operacional (um
único agendamento por máquina, que varre todos os protótipos registrados) e dispara uma notificação do sistema
("Você tem N recado(s) em <pasta>") quando chegam recados novos. Funciona em macOS (LaunchAgent), Linux
(systemd de usuário; cron como alternativa) e Windows (Agendador de Tarefas).

É autossuficiente de propósito: a cópia instalada vive fora da skill, então nada é importado de comms_store,
protolib ou group_sync. A contagem espelha `comms_store.inbox_for` + `pending_count` (recados abertos e não lidos
para a pessoa + novidades de respostas aos recados que ela enviou e ainda não marcou como lidas; `reminders` não
entram). Somente leitura em relação ao repositório: `git ls-remote` e `git fetch` da branch de comunicação,
nada mais, sem checkout e sem force.

Privacidade: a notificação mostra a contagem e o nome da pasta (com `--detail sender`, também quem enviou).
NUNCA mostra assunto nem texto do recado.

  python3 comms-watch.py install --repo . [--interval 5] [--detail count|sender] [--execute]
  python3 comms-watch.py uninstall (--repo . | --all) [--execute]
  python3 comms-watch.py status
  python3 comms-watch.py run-once [--notify | --no-notify] [--repo .]
  python3 comms-watch.py doctor [--repo .]

`install` e `uninstall` simulam (DRY_RUN) até receber `--execute`. Envelope JSON de saída:
{"ok", "status", "data", "problems", "questions"}; exit 0 ok, 1 problema, 2 uso.

Variáveis de ambiente (usadas nos testes): INTERACTIVE_PROTOTYPE_COMMS_HOME (diretório de dados),
INTERACTIVE_PROTOTYPE_COMMS_OS (macos|linux|windows), INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR (diretório prefixado
no PATH dos comandos externos), INTERACTIVE_PROTOTYPE_COMMS_LABEL (rótulo do LaunchAgent).
"""

import argparse
import collections
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

WATCH_VERSION = "1.0.0"

ENV_HOME = 'INTERACTIVE_PROTOTYPE_COMMS_HOME'
ENV_OS = 'INTERACTIVE_PROTOTYPE_COMMS_OS'
ENV_STUB = 'INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR'
ENV_LABEL = 'INTERACTIVE_PROTOTYPE_COMMS_LABEL'

DATA_DIRNAME = 'interactive-prototype-comms'
DEFAULT_LABEL = 'dev.interactive-prototype.comms-watch'
UNIT_NAME = 'interactive-prototype-comms-watch'
WIN_TASK = 'InteractivePrototypeCommsWatch'
CRON_MARK = '# interactive-prototype-comms-watch'
PS_APP_ID = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'
CONFIG_NAME = 'prototype.config.json'
NOTIFY_TITLE = 'Recados do time'
DEFAULT_INTERVAL = 5
MIN_INTERVAL = 2
MAX_INTERVAL = 1439
LOG_MAX_BYTES = 200 * 1024
LOCK_STALE_SECONDS = 600
AUTH_MESSAGE = 'git não consegue autenticar sem pedir senha: configure chave SSH ou credential helper'

# ---- espelho de comms_store.py (mesmas constantes e regras)
DEFAULTS = {'enabled': False, 'branch': 'comms', 'expiryDays': 30, 'reminderHours': 24}
KINDS = ('message', 'question', 'confirm', 'task', 'handoff')
RECEIPT_KINDS = ('read', 'answer', 'accept', 'decline', 'done', 'cancel')
ADDR_PROMOTERS = '@promoters'
ADDR_ALL = '@all'
CLOSING = {'message': ('read',), 'handoff': ('read',), 'question': ('answer',), 'confirm': ('answer',),
           'task': ('done', 'decline')}
NEWS_KINDS = ('answer', 'accept', 'decline', 'done')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
EVENT_PATH_RE = re.compile(r'^events/\d{4}-\d{2}/(\d{8}T\d{6}Z-[0-9a-f]{8})\.json$')

Res = collections.namedtuple('Res', 'rc out err')


# ------------------------------------------------------------------ envelope e utilidades

def problem(code, message):
    return {'code': code, 'message': message}


def emit(ok, status, data=None, problems=None, questions=None, compact=False):
    out = {'ok': bool(ok), 'status': status, 'data': data or {}, 'problems': problems or [],
           'questions': questions or []}
    print(json.dumps(out, ensure_ascii=False, **({} if compact else {'indent': 2})))
    return 0 if ok else 1


def norm_email(email):
    return (email or '').strip().lower()


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso(text):
    try:
        return datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def detect_os():
    forced = os.environ.get(ENV_OS)
    if forced in ('macos', 'linux', 'windows'):
        return forced
    return {'Darwin': 'macos', 'Windows': 'windows'}.get(platform.system(), 'linux')


def home_dir():
    return os.path.expanduser('~')


def data_dir():
    forced = os.environ.get(ENV_HOME)
    if forced:
        return Path(forced)
    name = detect_os()
    if name == 'macos':
        return Path(home_dir()) / 'Library' / 'Application Support' / DATA_DIRNAME
    if name == 'windows':
        base = os.environ.get('APPDATA') or str(Path(home_dir()) / 'AppData' / 'Roaming')
        return Path(base) / DATA_DIRNAME
    base = os.environ.get('XDG_DATA_HOME') or str(Path(home_dir()) / '.local' / 'share')
    return Path(base) / DATA_DIRNAME


def registry_path():
    return data_dir() / 'watch.json'


def installed_script():
    return data_dir() / 'comms-watch.py'


def log_path():
    return data_dir() / 'watch.log'


def label():
    return os.environ.get(ENV_LABEL) or DEFAULT_LABEL


def uid():
    return os.getuid() if hasattr(os, 'getuid') else 0


# ------------------------------------------------------------------ comandos externos (ponto único)

def _env(extra=None):
    env = dict(os.environ)
    stub = os.environ.get(ENV_STUB)
    if stub:
        env['PATH'] = stub + os.pathsep + env.get('PATH', '')
    if extra:
        env.update(extra)
    return env


def which(name):
    return shutil.which(name, path=_env().get('PATH'))


def run_external(cmd, timeout=30, input=None, extra_env=None):
    """ÚNICA função que executa comandos externos (git, launchctl, osascript, systemctl, crontab, notify-send,
    schtasks, powershell). Com INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR, o diretório entra à frente do PATH."""
    kwargs = {}
    if sys.platform == 'win32':
        kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout,
                           input=input, env=_env(extra_env), stdin=None if input is not None else subprocess.DEVNULL,
                           **kwargs)
    except subprocess.TimeoutExpired:
        return Res(124, '', 'tempo esgotado')
    except FileNotFoundError:
        return Res(127, '', f'{cmd[0]}: comando não encontrado')
    except OSError as e:
        return Res(126, '', str(e))
    return Res(r.returncode, r.stdout, r.stderr)


GIT_ENV = {'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never', 'LC_ALL': 'C'}


def git(repo, *args, timeout=30):
    return run_external(['git', '-C', str(repo), *args], timeout=timeout, extra_env=GIT_ENV)


def git_bytes(repo, args, data, timeout=60):
    """git com entrada/saída binária (cat-file --batch). Mesmo ambiente não interativo e mesmo PATH de stubs."""
    try:
        r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, input=data, timeout=timeout,
                           env=_env(GIT_ENV))
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


# ------------------------------------------------------------------ log, registro e trava

def log(message):
    try:
        d = data_dir()
        d.mkdir(parents=True, exist_ok=True)
        path = log_path()
        if path.exists() and path.stat().st_size > LOG_MAX_BYTES:
            os.replace(str(path), str(path) + '.1')
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(f'{iso(now_utc())} {message}\n')
    except OSError:
        pass


def rotate_log():
    try:
        path = log_path()
        if path.exists() and path.stat().st_size > LOG_MAX_BYTES:
            os.replace(str(path), str(path) + '.1')
    except OSError:
        pass


def load_registry():
    try:
        reg = json.loads(registry_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return reg if isinstance(reg, dict) and isinstance(reg.get('repos'), list) else None


def new_registry():
    return {'version': WATCH_VERSION, 'intervalMinutes': DEFAULT_INTERVAL, 'detail': 'count', 'repos': []}


def save_registry(reg):
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.tmp{os.getpid()}')
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(reg, ensure_ascii=False, indent=2) + '\n')
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(str(tmp), str(path))


def acquire_lock():
    """Evita duas varreduras ao mesmo tempo (ex.: RunAtLoad + intervalo). Devolve o caminho ou None."""
    path = data_dir() / 'run.lock'
    try:
        data_dir().mkdir(parents=True, exist_ok=True)
        if path.exists() and time.time() - path.stat().st_mtime > LOCK_STALE_SECONDS:
            path.unlink()
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return path
    except FileExistsError:
        return None
    except OSError:
        return path  # sem trava possível: segue sem ela


def release_lock(path):
    try:
        if path and path.exists():
            path.unlink()
    except OSError:
        pass


# ------------------------------------------------------------------ leitura dos eventos (somente git)

def load_json_file(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def comms_cfg(cfg):
    merged = dict(DEFAULTS)
    block = (cfg or {}).get('comms')
    if isinstance(block, dict):
        merged.update({k: block[k] for k in DEFAULTS if k in block})
    return merged


def remote_roster(repo, cfg):
    """Config da beta no remoto (fonte do roster); a local se não houver (igual ao comms_store)."""
    remote = cfg.get('remote', 'origin')
    beta = (cfg.get('branches') or {}).get('beta', 'beta')
    r = git(repo, 'show', f'refs/remotes/{remote}/{beta}:{CONFIG_NAME}')
    if r.rc == 0:
        try:
            data = json.loads(r.out)
            if isinstance(data, dict):
                return data
        except ValueError:
            pass
    return cfg


def read_events(repo, remote, branch):
    """Eventos legíveis das duas pontas (remota e local da branch de comunicação), sem checkout."""
    tips = []
    for ref in (f'refs/remotes/{remote}/{branch}', f'refs/heads/{branch}'):
        r = git(repo, 'rev-parse', '--verify', '-q', f'{ref}^{{commit}}')
        sha = r.out.strip() if r.rc == 0 else ''
        if sha and sha not in tips:
            tips.append(sha)
    seen, events = set(), []
    for tip in tips:
        r = git(repo, 'ls-tree', '-r', tip)
        if r.rc != 0:
            continue
        wanted = []
        for line in r.out.splitlines():
            if '\t' not in line:
                continue
            meta, path = line.split('\t', 1)
            parts = meta.split(' ')
            m = EVENT_PATH_RE.match(path)
            if len(parts) == 3 and parts[1] == 'blob' and m and m.group(1) not in seen:
                wanted.append((m.group(1), parts[2]))
        if not wanted:
            continue
        raw = git_bytes(repo, ['cat-file', '--batch'], ''.join(f'{sha}\n' for _, sha in wanted).encode())
        if raw is None:
            continue
        pos = 0
        for event_id, sha in wanted:
            end = raw.find(b'\n', pos)
            if end < 0:
                break
            header = raw[pos:end].split(b' ')
            if len(header) != 3 or header[1] != b'blob':
                pos = end + 1
                continue
            size = int(header[2])
            blob = raw[end + 1:end + 1 + size]
            pos = end + 1 + size + 1
            try:
                ev = json.loads(blob.decode('utf-8'))
            except ValueError:
                continue
            if not isinstance(ev, dict) or ev.get('id') != event_id or event_id in seen:
                continue
            seen.add(event_id)
            events.append(ev)
    return events


# ------------------------------------------------------------------ regra de contagem (espelho do comms_store)

def is_promoter(member):
    return bool(member) and member.get('status') == 'approved' and 'promoter' in (member.get('roles') or [])


def find_member(cfg, email):
    e = norm_email(email)
    for m in (cfg or {}).get('members', []) or []:
        if isinstance(m, dict) and norm_email(m.get('email')) == e:
            return m
    return None


def resolve_recipients(event, roster, sender=None):
    members = [m for m in (roster or {}).get('members', []) or [] if isinstance(m, dict)]
    out = set()
    for addr in event.get('to', []) or []:
        if addr == ADDR_PROMOTERS:
            out |= {norm_email(m.get('email')) for m in members if is_promoter(m)}
        elif addr == ADDR_ALL:
            out |= {norm_email(m.get('email')) for m in members if m.get('status') == 'approved'}
        elif EMAIL_RE.match(addr or ''):
            out.add(norm_email(addr))
    out.discard(norm_email(sender or event.get('from')))
    return out


def direct_recipients(event):
    return {norm_email(a) for a in event.get('to', []) or [] if EMAIL_RE.match(a or '')}


def can_see(event, member, roster):
    me = norm_email(member.get('email'))
    if norm_email(event.get('from')) == me:
        return True
    if member.get('status') == 'pending':
        return me in direct_recipients(event)
    if member.get('status') != 'approved':
        return False
    return me in resolve_recipients(event, roster)


def expires_at(original, cfg, now):
    explicit = parse_iso(original.get('expiresAt'))
    if explicit:
        return explicit
    base = parse_iso(original.get('at')) or now
    try:
        days = int(comms_cfg(cfg)['expiryDays'])
    except (TypeError, ValueError):
        days = DEFAULTS['expiryDays']
    return base + timedelta(days=days)


def compute_pending(events, email, roster, cfg, now=None):
    """Ids pendentes para `email`: recados abertos e não lidos + novidades ainda não lidas.

    Devolve {'ids': [...], 'senders': [...], 'incoming': n, 'news': n, 'allowed': bool}. Mesma regra de
    `comms_store.inbox_for` + `pending_count` (sem `reminders`). Se a pessoa não consta em nenhum roster, vale só
    o endereçamento direto (tratada como pendente)."""
    now = now or now_utc()
    me = norm_email(email)
    member = find_member(roster, me) or find_member(cfg, me) or {'email': me, 'status': 'pending'}
    if member.get('status') not in ('approved', 'pending'):
        return {'ids': [], 'senders': [], 'incoming': 0, 'news': 0, 'allowed': False}
    originals = {e['id']: e for e in events if e.get('kind') in KINDS and e.get('id')}
    receipts = [e for e in events if e.get('kind') in RECEIPT_KINDS and e.get('target') and e.get('id')]
    by_target = {}
    for r in receipts:
        by_target.setdefault(r['target'], []).append(r)
    ids, senders = [], set()
    incoming = news = 0
    for orig in originals.values():
        sender = norm_email(orig.get('from'))
        cancelled = any(r['kind'] == 'cancel' and norm_email(r.get('from')) == sender
                        for r in by_target.get(orig['id'], []))
        if cancelled or expires_at(orig, cfg, now) < now:
            continue
        if sender != me and can_see(orig, member, roster):
            mine = [r for r in by_target.get(orig['id'], []) if norm_email(r.get('from')) == me]
            kinds = {r['kind'] for r in mine}
            closed = bool(kinds & set(CLOSING[orig['kind']]))
            read = bool(kinds & {'read', 'answer', 'accept', 'decline', 'done'})
            if not closed and not read:
                ids.append(orig['id'])
                senders.add(sender)
                incoming += 1
    seen_by_me = {r['target'] for r in receipts if r['kind'] == 'read' and norm_email(r.get('from')) == me}
    for r in receipts:
        orig = originals.get(r['target'])
        if (orig and norm_email(orig.get('from')) == me and norm_email(r.get('from')) != me
                and r['kind'] in NEWS_KINDS and r['id'] not in seen_by_me):
            ids.append(r['id'])
            senders.add(norm_email(r.get('from')))
            news += 1
    return {'ids': sorted(ids), 'senders': sorted(senders), 'incoming': incoming, 'news': news, 'allowed': True}


def display_names(emails, roster, cfg):
    names = []
    for e in emails:
        m = find_member(roster, e) or find_member(cfg, e)
        names.append((m or {}).get('name') or e)
    return names


# ------------------------------------------------------------------ geradores puros (escape por destino)

def systemd_quote(arg):
    """Argumento de ExecStart/Environment entre aspas duplas; `%` e `$` são especiais no systemd."""
    s = str(arg).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$')
    return f'"{s}"'


def cron_escape(text):
    return text.replace('%', '\\%')


def gen_launchd_plist(lbl, python, script, minutes, log_file, env=None):
    def s(value):
        return f'    <string>{xml_escape(str(value))}</string>'
    env_block = ''
    if env:
        items = ''.join(f'    <key>{xml_escape(k)}</key>\n    <string>{xml_escape(v)}</string>\n'
                        for k, v in sorted(env.items()))
        env_block = f'  <key>EnvironmentVariables</key>\n  <dict>\n{items}  </dict>\n'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n'
        f'  <key>Label</key>\n  <string>{xml_escape(lbl)}</string>\n'
        '  <key>ProgramArguments</key>\n  <array>\n'
        + '\n'.join(s(a) for a in (python, script, 'run-once', '--notify')) + '\n  </array>\n'
        f'  <key>StartInterval</key>\n  <integer>{int(minutes) * 60}</integer>\n'
        '  <key>RunAtLoad</key>\n  <true/>\n'
        f'  <key>StandardOutPath</key>\n  <string>{xml_escape(str(log_file))}</string>\n'
        f'  <key>StandardErrorPath</key>\n  <string>{xml_escape(str(log_file))}</string>\n'
        '  <key>ProcessType</key>\n  <string>Background</string>\n'
        + env_block + '</dict>\n</plist>\n')


def gen_systemd_units(python, script, minutes, env=None):
    env_lines = ''.join(f'Environment={systemd_quote(f"{k}={v}")}\n' for k, v in sorted((env or {}).items()))
    service = ('[Unit]\nDescription=interactive-prototype: vigia de recados do time\n\n'
               '[Service]\nType=oneshot\n'
               f'ExecStart={systemd_quote(python)} {systemd_quote(script)} run-once --notify\n' + env_lines)
    timer = ('[Unit]\nDescription=interactive-prototype: agenda o vigia de recados do time\n\n'
             '[Timer]\nOnBootSec=1min\n'
             f'OnUnitActiveSec={int(minutes)}min\nPersistent=true\n'
             f'Unit={UNIT_NAME}.service\n\n[Install]\nWantedBy=timers.target\n')
    return service, timer


def gen_cron_entry(python, script, minutes, user_id, log_file, env=None):
    minutes = int(minutes)
    spec = f'*/{minutes} * * * *' if minutes < 60 else f'0 */{max(1, minutes // 60)} * * *'
    prefix = f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user_id}/bus '
    prefix += ''.join(f'{k}={shlex.quote(v)} ' for k, v in sorted((env or {}).items()))
    cmd = (f'{shlex.quote(python)} {shlex.quote(script)} run-once --notify >> {shlex.quote(str(log_file))} 2>&1')
    return f'{CRON_MARK}\n{spec} {cron_escape(prefix + cmd)}\n'


def strip_cron_block(text):
    out, skip = [], False
    for line in text.splitlines():
        if skip:
            skip = False
            continue
        if line.strip() == CRON_MARK:
            skip = True
            continue
        out.append(line)
    return '\n'.join(out) + ('\n' if out else '')


def gen_schtasks_create(python, script, minutes):
    tr = f'"{python}" "{script}" run-once --notify'
    return ['schtasks', '/Create', '/SC', 'MINUTE', '/MO', str(int(minutes)), '/TN', WIN_TASK, '/TR', tr, '/F']


def applescript_escape(text):
    return re.sub(r'[\r\n\t]+', ' ', str(text)).replace('\\', '\\\\').replace('"', '\\"')


def gen_osascript(title, text):
    return f'display notification "{applescript_escape(text)}" with title "{applescript_escape(title)}"'


def gen_toast_script(title, text):
    clean = lambda v: xml_escape(re.sub(r'[\r\n\t]+', ' ', str(v)))  # noqa: E731
    xml = (f'<toast><visual><binding template="ToastText02"><text id="1">{clean(title)}</text>'
           f'<text id="2">{clean(text)}</text></binding></visual></toast>').replace("'", "''")
    return ('[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
            'ContentType = WindowsRuntime] | Out-Null; '
            '[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] '
            '| Out-Null; '
            f"$x = New-Object Windows.Data.Xml.Dom.XmlDocument; $x.LoadXml('{xml}'); "
            '$t = [Windows.UI.Notifications.ToastNotification]::new($x); '
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{PS_APP_ID}').Show($t)")


def gen_powershell_cmd(title, text):
    return ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command',
            gen_toast_script(title, text)]


def windows_python():
    exe = Path(sys.executable)
    pw = exe.with_name('pythonw.exe')
    return str(pw) if pw.exists() else sys.executable


def runtime_env():
    """Sobrescritas de ambiente presentes na instalação e que o agendamento precisa repetir."""
    return {k: os.environ[k] for k in (ENV_HOME,) if os.environ.get(k)}


class Plan:
    """Tudo o que o agendador do SO vai usar, derivado de forma pura."""

    def __init__(self, os_name, minutes):
        self.os = os_name
        self.minutes = int(minutes)
        self.script = str(installed_script())
        self.python = windows_python() if os_name == 'windows' else sys.executable
        self.log = str(log_path())
        self.label = label()
        self.env = runtime_env()
        home = home_dir()
        if os_name == 'macos':
            self.plist_path = Path(home) / 'Library' / 'LaunchAgents' / f'{self.label}.plist'
        if os_name == 'linux':
            base = os.environ.get('XDG_CONFIG_HOME') or str(Path(home) / '.config')
            self.unit_dir = Path(base) / 'systemd' / 'user'

    def generated(self):
        if self.os == 'macos':
            return {'path': str(self.plist_path),
                    'plist': gen_launchd_plist(self.label, self.python, self.script, self.minutes, self.log, self.env)}
        if self.os == 'linux':
            service, timer = gen_systemd_units(self.python, self.script, self.minutes, self.env)
            return {'systemd': {'servicePath': str(self.unit_dir / f'{UNIT_NAME}.service'), 'service': service,
                                'timerPath': str(self.unit_dir / f'{UNIT_NAME}.timer'), 'timer': timer},
                    'cron': gen_cron_entry(self.python, self.script, self.minutes, uid(), self.log, self.env)}
        cmd = gen_schtasks_create(self.python, self.script, self.minutes)
        return {'args': cmd, 'command': subprocess.list2cmdline(cmd)}

    def fingerprint(self, kind=None):
        g = self.generated()
        if kind == 'cron':
            g = {'cron': g['cron']}
        elif kind == 'systemd':
            g = {'systemd': g['systemd']}
        return hashlib.sha256(json.dumps(g, sort_keys=True).encode('utf-8')).hexdigest()


# ------------------------------------------------------------------ agendadores (efeitos)

def launchctl_target():
    return f'gui/{uid()}/{label()}'


def systemd_responds():
    return run_external(['systemctl', '--user', 'show-environment']).rc == 0


def crontab_text():
    r = run_external(['crontab', '-l'])
    return r.out if r.rc == 0 else ''


def scheduler_state(plan):
    """(registrado?, tipo). Somente leitura."""
    if plan.os == 'macos':
        ok = plan.plist_path.exists() and run_external(['launchctl', 'print', launchctl_target()]).rc == 0
        return ok, 'launchd'
    if plan.os == 'windows':
        return run_external(['schtasks', '/Query', '/TN', WIN_TASK]).rc == 0, 'schtasks'
    timer = plan.unit_dir / f'{UNIT_NAME}.timer'
    if timer.exists() and (plan.unit_dir / f'{UNIT_NAME}.service').exists():
        enabled = run_external(['systemctl', '--user', 'is-enabled', f'{UNIT_NAME}.timer']).rc == 0
        if enabled:
            return True, 'systemd'
    if CRON_MARK in crontab_text():
        return True, 'cron'
    return False, 'systemd' if timer.exists() else 'cron'


def scheduler_apply(plan, reg):
    """Cria/atualiza o agendamento. Devolve (ação, problemas, tipo). Mesmo conteúdo ⇒ não mexe."""
    registered, kind = scheduler_state(plan)
    saved = reg.get('scheduler') or {}
    if plan.os == 'linux':
        kind = 'systemd' if systemd_responds() else 'cron'
    fp = plan.fingerprint(kind if plan.os == 'linux' else None)
    if registered and saved.get('fingerprint') == fp and saved.get('kind') == kind:
        return 'unchanged', [], kind, fp
    action = 'updated' if registered else 'created'
    if plan.os == 'macos':
        plan.plist_path.parent.mkdir(parents=True, exist_ok=True)
        plan.plist_path.write_text(plan.generated()['plist'], encoding='utf-8')
        run_external(['launchctl', 'bootout', launchctl_target()])
        r = None
        for attempt in range(3):
            r = run_external(['launchctl', 'bootstrap', f'gui/{uid()}', str(plan.plist_path)])
            if r.rc == 0:
                break
            time.sleep(1)
        if r.rc != 0:
            return 'failed', [problem('LAUNCHCTL_FAILED', f'launchctl bootstrap falhou: {r.err.strip()}')], kind, fp
    elif plan.os == 'windows':
        r = run_external(gen_schtasks_create(plan.python, plan.script, plan.minutes))
        if r.rc != 0:
            return 'failed', [problem('SCHTASKS_FAILED', f'schtasks /Create falhou: {r.err.strip() or r.out.strip()}')], \
                kind, fp
    elif kind == 'systemd':
        g = plan.generated()['systemd']
        plan.unit_dir.mkdir(parents=True, exist_ok=True)
        Path(g['servicePath']).write_text(g['service'], encoding='utf-8')
        Path(g['timerPath']).write_text(g['timer'], encoding='utf-8')
        run_external(['systemctl', '--user', 'daemon-reload'])
        r = run_external(['systemctl', '--user', 'enable', '--now', f'{UNIT_NAME}.timer'])
        if r.rc != 0:
            return 'failed', [problem('SYSTEMCTL_FAILED', f'systemctl enable falhou: {r.err.strip()}')], kind, fp
        if registered:
            run_external(['systemctl', '--user', 'restart', f'{UNIT_NAME}.timer'])
        remove_cron()  # migração: não deixa os dois agendadores ativos
    else:
        current = strip_cron_block(crontab_text())
        r = run_external(['crontab', '-'], input=current + plan.generated()['cron'])
        if r.rc != 0:
            return 'failed', [problem('CRONTAB_FAILED', f'crontab falhou: {r.err.strip()}')], kind, fp
    return action, [], kind, fp


def remove_cron():
    text = crontab_text()
    if CRON_MARK not in text:
        return False
    rest = strip_cron_block(text)
    if rest.strip():
        run_external(['crontab', '-'], input=rest)
    else:
        run_external(['crontab', '-r'])
    return True


def scheduler_remove(plan):
    """Remove o agendamento do SO. Idempotente. Devolve a lista do que foi feito."""
    done = []
    if plan.os == 'macos':
        if run_external(['launchctl', 'print', launchctl_target()]).rc == 0:
            run_external(['launchctl', 'bootout', launchctl_target()])
            done.append('launchctl bootout')
        if plan.plist_path.exists():
            plan.plist_path.unlink()
            done.append(f'removido {plan.plist_path}')
    elif plan.os == 'windows':
        if run_external(['schtasks', '/Query', '/TN', WIN_TASK]).rc == 0:
            run_external(['schtasks', '/Delete', '/TN', WIN_TASK, '/F'])
            done.append('schtasks /Delete')
    else:
        service, timer = (plan.unit_dir / f'{UNIT_NAME}.service', plan.unit_dir / f'{UNIT_NAME}.timer')
        if service.exists() or timer.exists():
            run_external(['systemctl', '--user', 'disable', '--now', f'{UNIT_NAME}.timer'])
            for p in (service, timer):
                if p.exists():
                    p.unlink()
                    done.append(f'removido {p}')
            run_external(['systemctl', '--user', 'daemon-reload'])
        if remove_cron():
            done.append('removida a entrada do crontab')
    return done


# ------------------------------------------------------------------ notificação

def send_notification(title, text):
    """Dispara a notificação do SO. Devolve {'sent','channel','rc'}. Sem notificador: só log."""
    name = detect_os()
    if name == 'macos':
        cmd, channel = ['osascript', '-e', gen_osascript(title, text)], 'osascript'
    elif name == 'windows':
        cmd, channel = gen_powershell_cmd(title, text), 'powershell'
    else:
        if not which('notify-send'):
            log(f'notificação sem notify-send (só log): {text}')
            return {'sent': False, 'channel': 'log', 'rc': None}
        cmd, channel = ['notify-send', '--app-name=interactive-prototype', title, text], 'notify-send'
    r = run_external(cmd, timeout=20)
    log(f'notificação via {channel} rc={r.rc}: {text}')
    return {'sent': r.rc == 0, 'channel': channel, 'rc': r.rc}


# ------------------------------------------------------------------ validação do repositório

def inspect_repo(path):
    """(info|None, status|None, mensagem). `info` = path, remote, branch, actorEmail."""
    repo = Path(path).expanduser()
    if not repo.is_dir() or git(repo, 'rev-parse', '--is-inside-work-tree').rc != 0:
        return None, 'NOT_A_REPO', f'{path} não é um repositório git.'
    top = git(repo, 'rev-parse', '--show-toplevel').out.strip()
    repo = Path(top).resolve() if top else repo.resolve()
    cfg = load_json_file(repo / CONFIG_NAME)
    block = (cfg or {}).get('comms')
    if (not cfg or cfg.get('groupMode') is not True or not isinstance(block, dict)
            or block.get('enabled') is not True):
        return None, 'NOT_ENABLED', ('Este protótipo não está em modo grupo com a comunicação do time ligada '
                                     '(groupMode e comms.enabled em prototype.config.json).')
    r = git(repo, 'config', 'user.email')
    email = norm_email(r.out) if r.rc == 0 else ''
    if not email:
        return None, 'NO_IDENTITY', 'O git deste repositório não tem user.email: configure antes de instalar.'
    return {'path': str(repo), 'remote': cfg.get('remote', 'origin'), 'branch': comms_cfg(cfg)['branch'],
            'actorEmail': email}, None, ''


def same_path(a, b):
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return str(a) == str(b)


# ------------------------------------------------------------------ install / uninstall

def cmd_install(args):
    minutes = args.interval
    reg = load_registry()
    if minutes is not None and not (MIN_INTERVAL <= minutes <= MAX_INTERVAL):
        return emit(False, 'BAD_INTERVAL', problems=[problem(
            'BAD_INTERVAL', f'O intervalo vai de {MIN_INTERVAL} a {MAX_INTERVAL} minutos.')]), 2
    info, status, msg = inspect_repo(args.repo)
    if status:
        return emit(False, status, problems=[problem(status, msg)]), 1
    minutes = minutes or (reg or {}).get('intervalMinutes') or DEFAULT_INTERVAL
    detail = args.detail or (reg or {}).get('detail') or 'count'
    os_name = detect_os()
    plan = Plan(os_name, minutes)
    registered, kind = scheduler_state(plan)
    reg_new = json.loads(json.dumps(reg)) if reg else new_registry()
    reg_new.update({'version': WATCH_VERSION, 'intervalMinutes': minutes, 'detail': detail})
    entry = next((r for r in reg_new['repos'] if same_path(r.get('path', ''), info['path'])), None)
    already = entry is not None
    if entry is None:
        entry = {'lastSeenSha': None, 'notifiedIds': [], 'lastCheckedAt': None}
        reg_new['repos'].append(entry)
    elif any(entry.get(k) != info[k] for k in ('remote', 'branch', 'actorEmail')):
        entry.update({'lastSeenSha': None, 'notifiedIds': [], 'lastCheckedAt': None})
    entry.update(info)
    files = [str(registry_path()), str(installed_script()), str(log_path())]
    if os_name == 'macos':
        files.append(str(plan.plist_path))
    elif os_name == 'linux':
        files += [str(plan.unit_dir / f'{UNIT_NAME}.service'), str(plan.unit_dir / f'{UNIT_NAME}.timer'),
                  '(ou, sem systemd de usuário, uma entrada no crontab)']
    sched_cmd = {'macos': f'launchctl bootstrap gui/{uid()} {plan.generated().get("path", "")}',
                 'linux': f'systemctl --user enable --now {UNIT_NAME}.timer',
                 'windows': plan.generated().get('command', '')}[os_name]
    fp_same = (reg or {}).get('scheduler', {}).get('fingerprint') == plan.fingerprint(
        ('systemd' if systemd_responds() else 'cron') if os_name == 'linux' else None)
    data = {'os': os_name, 'repo': info['path'], 'intervalMinutes': minutes, 'detail': detail,
            'alreadyRegistered': already, 'schedulerUnchanged': bool(registered and fp_same),
            'plan': {'files': files, 'schedulerCommand': sched_cmd, 'scheduler': 'único para todos os repositórios'},
            'generated': plan.generated()}
    if not args.execute:
        return emit(True, 'DRY_RUN', data=data), 0
    try:
        data_dir().mkdir(parents=True, exist_ok=True)
        src, dst = Path(__file__).resolve(), installed_script()
        if not (dst.exists() and same_path(src, dst)):
            shutil.copyfile(str(src), str(dst))
            try:
                os.chmod(str(dst), 0o755)
            except OSError:
                pass
        action, probs, sched_kind, fp = scheduler_apply(plan, reg_new)
        if probs:
            return emit(False, 'SCHEDULER_FAILED', data=data, problems=probs), 1
        reg_new['scheduler'] = {'kind': sched_kind, 'fingerprint': fp, 'os': os_name}
        save_registry(reg_new)
    except OSError as e:
        return emit(False, 'INSTALL_FAILED', data=data, problems=[problem('INSTALL_FAILED', str(e))]), 1
    data['schedulerAction'] = action
    data['schedulerKind'] = sched_kind
    log(f'install: {info["path"]} (intervalo {minutes} min, agendador {sched_kind}: {action})')
    return emit(True, 'ALREADY_INSTALLED' if (already and action == 'unchanged') else 'INSTALLED', data=data), 0


def cmd_uninstall(args):
    reg = load_registry()
    os_name = detect_os()
    plan = Plan(os_name, (reg or {}).get('intervalMinutes') or DEFAULT_INTERVAL)
    registered, _ = scheduler_state(plan)
    leftovers = [p for p in (installed_script(), registry_path(), log_path()) if p.exists()]
    remaining = list((reg or {}).get('repos', []))
    removed_repo = None
    if args.repo:
        target = Path(args.repo).expanduser()
        kept = [r for r in remaining if not same_path(r.get('path', ''), target)]
        removed_repo = len(kept) != len(remaining)
        remaining = kept
    full = bool(args.all) or not remaining
    if reg is None and not registered and not leftovers:
        return emit(True, 'NOT_INSTALLED', data={'os': os_name}), 0
    data = {'os': os_name, 'removeRepo': removed_repo, 'removeEverything': full,
            'repoCount': len(remaining) if not full else 0,
            'plan': ['remover o agendamento do SO', 'apagar a cópia instalada, o registro e o log'] if full
            else ['tirar o repositório do registro (o agendamento continua para os demais)']}
    if not args.execute:
        return emit(True, 'DRY_RUN', data=data), 0
    actions = []
    if full:
        actions += scheduler_remove(plan)
        for p in (installed_script(), registry_path(), log_path(), Path(str(log_path()) + '.1'),
                  data_dir() / 'run.lock'):
            try:
                if p.exists():
                    p.unlink()
                    actions.append(f'removido {p}')
            except OSError:
                pass
        try:
            data_dir().rmdir()
        except OSError:
            pass
    elif reg is not None:
        reg['repos'] = remaining
        save_registry(reg)
        actions.append('repositório removido do registro')
    data['actions'] = actions
    return emit(True, 'UNINSTALLED', data=data), 0


# ------------------------------------------------------------------ status

def installed_version():
    try:
        text = installed_script().read_text(encoding='utf-8')
    except OSError:
        return None
    m = re.search(r'^WATCH_VERSION = "([^"]+)"', text, re.M)
    return m.group(1) if m else None


def cmd_status(args):
    reg = load_registry()
    os_name = detect_os()
    plan = Plan(os_name, (reg or {}).get('intervalMinutes') or DEFAULT_INTERVAL)
    registered, kind = scheduler_state(plan)
    copy_version = installed_version()
    checked = sorted(r.get('lastCheckedAt') for r in (reg or {}).get('repos', []) if r.get('lastCheckedAt'))
    data = {'os': os_name, 'dataDir': str(data_dir()), 'installed': bool(reg and installed_script().exists()),
            'scheduler': {'registered': registered, 'kind': kind},
            'registryVersion': (reg or {}).get('version'), 'copyVersion': copy_version,
            'watchVersion': WATCH_VERSION,
            'outdated': bool(reg and ((reg.get('version') != WATCH_VERSION) or (copy_version != WATCH_VERSION))),
            'intervalMinutes': (reg or {}).get('intervalMinutes'), 'detail': (reg or {}).get('detail'),
            'repos': [{k: r.get(k) for k in ('path', 'remote', 'branch', 'actorEmail', 'lastCheckedAt')}
                      for r in (reg or {}).get('repos', [])],
            'lastCheckedAt': checked[-1] if checked else None}
    return emit(True, 'INSTALLED' if data['installed'] else 'NOT_INSTALLED', data=data), 0


# ------------------------------------------------------------------ run-once

def fetch_comms(repo, remote, branch):
    """Atualiza só a branch de comunicação. Devolve (ok, erro). Branch inexistente no remoto = ok."""
    r = git(repo, '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'fetch', '-q', '--no-tags',
            '--no-recurse-submodules', remote, f'+refs/heads/{branch}:refs/remotes/{remote}/{branch}', timeout=60)
    if r.rc != 0 and "couldn't find remote ref" in r.err:
        return True, ''
    return r.rc == 0, r.err.strip()


def ls_remote_head(repo, remote, branch):
    """(sha | '' se a branch não existe | None se falhou, erro)."""
    r = git(repo, 'ls-remote', '--heads', remote, branch, timeout=20)
    if r.rc != 0:
        return None, r.err.strip()
    for line in r.out.splitlines():
        if '\t' in line:
            sha, ref = line.split('\t', 1)
            if ref.strip() == f'refs/heads/{branch}':
                return sha, ''
    return '', ''


def check_repo(entry, notify, detail):
    """Varre um repositório. Atualiza `entry` (estado) e devolve o que fez."""
    repo = Path(entry.get('path', ''))
    res = {'path': str(repo), 'count': None, 'new': 0, 'notified': False, 'notification': None, 'errors': [],
           'skipped': None}
    if not repo.is_dir() or git(repo, 'rev-parse', '--is-inside-work-tree').rc != 0:
        res['errors'].append('repositório não encontrado')
        log(f'{repo}: repositório não encontrado')
        return res
    cfg = load_json_file(repo / CONFIG_NAME)
    if not cfg or cfg.get('groupMode') is not True or not comms_cfg(cfg)['enabled']:
        res['skipped'] = 'comunicação desligada neste protótipo'
        return res
    remote, branch = entry.get('remote') or cfg.get('remote', 'origin'), entry.get('branch') or comms_cfg(cfg)['branch']
    live, err = ls_remote_head(repo, remote, branch)
    if live is None:
        res['errors'].append(f'ls-remote falhou: {err}')
        log(f'{repo}: git ls-remote falhou ({err})')
        return res
    never = entry.get('lastSeenSha') is None or entry.get('lastCheckedAt') is None
    if live != entry.get('lastSeenSha') or never:
        if live:
            ok, err = fetch_comms(repo, remote, branch)
            if not ok:
                res['errors'].append(f'fetch falhou: {err}')
                log(f'{repo}: git fetch falhou ({err})')
                return res
        roster = remote_roster(repo, cfg)
        events = read_events(repo, remote, branch)
        pending = compute_pending(events, entry.get('actorEmail', ''), roster, cfg)
        old = set(entry.get('notifiedIds') or [])
        new_ids = [i for i in pending['ids'] if i not in old]
        res.update({'count': len(pending['ids']), 'new': len(new_ids)})
        kept = [i for i in pending['ids'] if i in old]
        if new_ids and notify:
            text = f'Você tem {len(pending["ids"])} recado(s) em {repo.name}'
            if detail == 'sender' and pending['senders']:
                text += f' (de: {", ".join(display_names(pending["senders"], roster, cfg))})'
            sent = send_notification(NOTIFY_TITLE, text)
            res['notification'] = sent
            res['notified'] = bool(sent['sent'])
            kept = pending['ids'] if sent['sent'] or sent['channel'] == 'log' else kept
        elif not notify:
            kept = pending['ids']
        entry['notifiedIds'] = sorted(kept)
        entry['lastSeenSha'] = live
    else:
        res['count'] = len(entry.get('notifiedIds') or [])
        res['skipped'] = 'sem mudança no remoto'
    entry['lastCheckedAt'] = iso(now_utc())
    return res


def cmd_run_once(args):
    rotate_log()
    reg = load_registry()
    if reg is None or not reg.get('repos'):
        return emit(True, 'NOTHING_REGISTERED', compact=True), 0
    entries = reg['repos']
    if args.repo:
        entries = [r for r in entries if same_path(r.get('path', ''), args.repo)]
        if not entries:
            return emit(False, 'REPO_NOT_REGISTERED', problems=[problem(
                'REPO_NOT_REGISTERED', f'{args.repo} não está registrado no vigia.')], compact=True), 1
    lock = acquire_lock()
    if lock is None:
        return emit(True, 'BUSY', data={'message': 'outra varredura está em andamento'}, compact=True), 0
    try:
        results = [check_repo(e, args.notify, reg.get('detail') or 'count') for e in entries]
        fresh = load_registry() or reg  # reaproveita o registro mais novo (um install pode ter rodado no meio)
        for res, entry in zip(results, entries):
            for target in fresh['repos']:
                if same_path(target.get('path', ''), entry.get('path', '')):
                    for k in ('lastSeenSha', 'notifiedIds', 'lastCheckedAt'):
                        target[k] = entry.get(k)
        save_registry(fresh)
    except OSError as e:
        log(f'run-once: erro ao gravar o registro: {e}')
        return emit(True, 'RUN_DONE', data={'repos': [], 'error': str(e)}, compact=True), 0
    finally:
        release_lock(lock)
    return emit(True, 'RUN_DONE', data={'notify': args.notify, 'repos': results}, compact=True), 0


# ------------------------------------------------------------------ doctor

def is_auth_error(err):
    low = (err or '').lower()
    return any(m in low for m in ('could not read username', 'could not read password', 'authentication failed',
                                  'permission denied', 'terminal prompts disabled', 'host key verification failed',
                                  'invalid username or password', 'access denied'))


def cmd_doctor(args):
    checks = []

    def add(name, level, message):
        checks.append({'name': name, 'level': level, 'message': message})

    os_name = detect_os()
    r = run_external(['git', '--version'])
    add('git', 'ok' if r.rc == 0 else 'fail', r.out.strip() if r.rc == 0 else 'git não está instalado ou fora do PATH')
    d = data_dir()
    probe = d
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    add('diretorio-de-dados', 'ok' if os.access(str(probe), os.W_OK) else 'fail',
        f'{d} ' + ('gravável' if os.access(str(probe), os.W_OK) else 'sem permissão de escrita'))
    reg = load_registry()
    if reg is None:
        add('registro', 'fail', 'vigia não instalado (sem watch.json): rode install --repo <pasta> --execute')
    else:
        add('registro', 'ok', f'{len(reg["repos"])} repositório(s) registrado(s)')
    copy_version = installed_version()
    if copy_version is None:
        add('copia-instalada', 'fail', f'cópia instalada ausente em {installed_script()}: rode install --execute')
    elif copy_version != WATCH_VERSION or (reg and reg.get('version') != WATCH_VERSION):
        add('versao', 'warn', f'cópia instalada {copy_version} (registro {(reg or {}).get("version")}) × este '
                              f'script {WATCH_VERSION}: rode install --repo <pasta> --execute de novo')
    else:
        add('versao', 'ok', f'versão {WATCH_VERSION}')
    plan = Plan(os_name, (reg or {}).get('intervalMinutes') or DEFAULT_INTERVAL)
    registered, kind = scheduler_state(plan)
    if not registered:
        add('agendamento', 'fail', f'nenhum agendamento ({kind}) registrado: rode install --execute')
    else:
        text = scheduler_text(plan, kind)
        py_ok = text is not None and (xml_escape(sys.executable) in text or sys.executable in text
                                      or (os_name == 'windows' and windows_python() in text))
        script_ok = text is not None and (xml_escape(str(installed_script())) in text
                                          or str(installed_script()) in text)
        if text is None:
            add('agendamento', 'ok', f'agendamento {kind} registrado (conteúdo não verificável)')
        elif script_ok and py_ok:
            add('agendamento', 'ok', f'agendamento {kind} aponta para a cópia instalada e para {sys.executable}')
        else:
            add('agendamento', 'warn', f'agendamento {kind} não aponta para a cópia instalada e/ou para o Python '
                                       f'atual ({sys.executable}): rode install --execute de novo')
    notifier = {'macos': 'osascript', 'linux': 'notify-send', 'windows': 'powershell'}[os_name]
    if which(notifier):
        add('notificador', 'ok', f'{notifier} disponível')
    else:
        add('notificador', 'warn' if os_name == 'linux' else 'fail',
            f'{notifier} não encontrado' + (': os avisos só irão para o log (instale libnotify-bin)'
                                            if os_name == 'linux' else ''))
    repos = (reg or {}).get('repos', [])
    if args.repo:
        repos = [r for r in repos if same_path(r.get('path', ''), args.repo)]
        if not repos:
            add('repo', 'fail', f'{args.repo} não está registrado no vigia')
    for entry in repos:
        repo = Path(entry.get('path', ''))
        if not repo.is_dir():
            add(f'repo:{repo.name}', 'fail', f'{repo} não existe mais')
            continue
        live, err = ls_remote_head(repo, entry.get('remote', 'origin'), entry.get('branch', 'comms'))
        if live is None:
            if is_auth_error(err):
                add(f'repo:{repo.name}', 'fail', AUTH_MESSAGE + f' ({err.splitlines()[-1] if err else ""})')
            elif 'tempo esgotado' in err:
                add(f'repo:{repo.name}', 'warn', 'git ls-remote não respondeu a tempo (rede lenta ou sem conexão)')
            else:
                add(f'repo:{repo.name}', 'fail', f'git ls-remote falhou: {err.splitlines()[-1] if err else "?"}')
        elif live == '':
            add(f'repo:{repo.name}', 'ok', 'remoto acessível; a branch de comunicação ainda não existe nele')
        else:
            add(f'repo:{repo.name}', 'ok', 'remoto acessível sem pedir senha')
    ok = not any(c['level'] == 'fail' for c in checks)
    probs = [problem('DOCTOR_' + c['level'].upper(), f'{c["name"]}: {c["message"]}') for c in checks
             if c['level'] != 'ok']
    return emit(ok, 'DOCTOR_OK' if ok else 'DOCTOR_PROBLEMS', data={'os': os_name, 'checks': checks},
                problems=probs), (0 if ok else 1)


def scheduler_text(plan, kind):
    """Texto do agendamento registrado (para conferir caminhos); None se não dá para ler."""
    try:
        if kind == 'launchd':
            return plan.plist_path.read_text(encoding='utf-8')
        if kind == 'systemd':
            return (plan.unit_dir / f'{UNIT_NAME}.service').read_text(encoding='utf-8')
        if kind == 'cron':
            return crontab_text()
    except OSError:
        return None
    r = run_external(['schtasks', '/Query', '/TN', WIN_TASK, '/V', '/FO', 'LIST'])
    return r.out if r.rc == 0 and r.out.strip() else None


# ------------------------------------------------------------------ CLI

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('install')
    p.add_argument('--repo', required=True)
    p.add_argument('--interval', type=int, help=f'minutos entre varreduras (mín {MIN_INTERVAL}, padrão {DEFAULT_INTERVAL})')
    p.add_argument('--detail', choices=('count', 'sender'))
    p.add_argument('--execute', action='store_true')
    p = sub.add_parser('uninstall')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--repo')
    g.add_argument('--all', action='store_true')
    p.add_argument('--execute', action='store_true')
    sub.add_parser('status')
    p = sub.add_parser('run-once')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--notify', dest='notify', action='store_true', default=True)
    g.add_argument('--no-notify', dest='notify', action='store_false')
    p.add_argument('--repo')
    p = sub.add_parser('doctor')
    p.add_argument('--repo')
    return ap


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    handler = {'install': cmd_install, 'uninstall': cmd_uninstall, 'status': cmd_status,
               'run-once': cmd_run_once, 'doctor': cmd_doctor}[args.cmd]
    return handler(args)[1]  # cada handler devolve (retorno do emit, código de saída)


if __name__ == '__main__':
    sys.exit(main())
