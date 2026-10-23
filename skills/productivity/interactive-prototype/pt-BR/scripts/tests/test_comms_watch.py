"""Testes do vigia local de recados (comms-watch.py). Repositórios temporários com remoto bare local, sem rede.

Comandos do SO (launchctl, systemctl, crontab, schtasks, osascript, notify-send, powershell) são substituídos
por stubs em Python (INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR) que gravam as chamadas. O teste real no macOS só roda
com COMMS_WATCH_REAL_MACOS=1 em um macOS.
"""

import importlib.util
import json
import os
import plistlib
import secrets
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from helpers import SCRIPTS, TmpDirMixin, run, run_script
from group_fixtures import ANA, BIA, CAIO, EDU, make_group_repo, member_clone

import comms_store as cs  # noqa: E402

WATCH = SCRIPTS / 'comms-watch.py'
_spec = importlib.util.spec_from_file_location('comms_watch_mod', str(WATCH))
cw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cw)

STUB_NAMES = ('launchctl', 'systemctl', 'crontab', 'schtasks', 'osascript', 'notify-send', 'powershell')

STUB_BODY = '''#!{python}
import json, os, shutil, sys

here = os.path.dirname(os.path.realpath(__file__))
name = os.path.basename(sys.argv[0])
args = sys.argv[1:]


def flag(n):
    return os.path.join(here, n)


def has(n):
    return os.path.exists(flag(n))


def touch(n, text=''):
    with open(flag(n), 'w') as fh:
        fh.write(text)


def drop(n):
    if has(n):
        os.remove(flag(n))


stdin = None
if name in ('crontab',) and args[:1] == ['-']:
    stdin = sys.stdin.read()
with open(flag('calls.jsonl'), 'a') as fh:
    fh.write(json.dumps({{'cmd': name, 'args': args, 'stdin': stdin}}) + '\\n')

code = 0
if name == 'launchctl':
    sub = args[0] if args else ''
    if sub == 'print':
        code = 0 if has('launchctl.loaded') else 113
    elif sub == 'bootstrap':
        touch('launchctl.loaded')
    elif sub == 'bootout':
        code = 0 if has('launchctl.loaded') else 3
        drop('launchctl.loaded')
elif name == 'systemctl':
    sub = args[1] if len(args) > 1 else ''
    if sub == 'show-environment':
        code = int(open(flag('systemd_rc')).read()) if has('systemd_rc') else 0
    elif sub == 'is-enabled':
        code = 0 if has('systemctl.enabled') else 1
    elif sub == 'enable':
        touch('systemctl.enabled')
    elif sub == 'disable':
        drop('systemctl.enabled')
elif name == 'crontab':
    if args == ['-l']:
        if has('crontab.txt'):
            sys.stdout.write(open(flag('crontab.txt')).read())
        else:
            sys.stderr.write('no crontab for user\\n')
            code = 1
    elif args == ['-']:
        touch('crontab.txt', stdin)
    elif args == ['-r']:
        drop('crontab.txt')
elif name == 'schtasks':
    sub = args[0].lower() if args else ''
    if sub == '/query':
        if has('schtasks.task'):
            sys.stdout.write(open(flag('schtasks.task')).read())
        else:
            code = 1
    elif sub == '/create':
        touch('schtasks.task', ' '.join(args))
    elif sub == '/delete':
        drop('schtasks.task')
elif name == 'git':
    real = os.environ['STUB_REAL_GIT']
    if 'ls-remote' in args and has('git_auth_fail'):
        sys.stderr.write("fatal: could not read Username for 'https://example.test': terminal prompts disabled\\n")
        sys.exit(128)
    os.execv(real, [real] + args)
sys.exit(code)
'''


def write_stub(directory, name):
    path = Path(directory) / name
    path.write_text(STUB_BODY.format(python=sys.executable), encoding='utf-8')
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_world(tmp):
    """Protótipo com comunicação ligada: Ana (promoter), Bia (contributor), Caio (pendente), Edu (promoter)."""
    repo, remote = make_group_repo(tmp)
    rc, env, out, err = run_script('comms-setup.py', '--repo', repo, '--actor-email', ANA[1], '--enable', '--execute')
    assert rc == 0, (out, err)
    run(['git', '-C', str(repo), 'add', '-A'])
    run(['git', '-C', str(repo), 'commit', '-q', '-m', 'chore: liga a comunicação'])
    run(['git', '-C', str(repo), 'push', '-q', 'origin', 'main'])
    run(['git', '-C', str(repo), 'push', '-q', 'origin', 'main:refs/heads/beta'])
    clones = {'ana': repo}
    for key, user in (('bia', BIA), ('caio', CAIO), ('edu', EDU)):
        clones[key] = member_clone(remote, tmp, user)
    return clones, remote


EMAILS = {'ana': ANA[1], 'bia': BIA[1], 'caio': CAIO[1], 'edu': EDU[1]}


def send(clone, sender, kind, to, subject='Assunto-SIGILOSO-123', body='corpo-sigiloso-456', *extra):
    args = ['--repo', clone, '--actor-email', EMAILS[sender], '--kind', kind, '--subject', subject, '--body', body]
    for t in ([to] if isinstance(to, str) else to):
        args += ['--to', EMAILS.get(t, t)]
    rc, env, out, err = run_script('comms-send.py', *args, *extra, '--execute')
    assert rc == 0, (out, err)
    return env['data']['event']['id']


def ack(clone, actor, target, action, *extra):
    rc, env, out, err = run_script('comms-ack.py', '--repo', clone, '--actor-email', EMAILS[actor], '--target', target,
                                   '--action', action, *extra, '--execute')
    assert rc == 0, (out, err)
    return env['data']['receipt']['id']


def inbox_count(clone, actor):
    rc, env, out, err = run_script('comms-inbox.py', '--repo', clone, '--actor-email', EMAILS[actor], '--quiet')
    assert env is not None, (out, err)
    return env['data']['count']


class WatchCase(TmpDirMixin, unittest.TestCase):
    os_name = 'macos'

    def setUp(self):
        super().setUp()
        self.home = self.tmp / 'home'
        self.chome = self.tmp / 'data dir'
        self.stubs = self.tmp / 'stubs'
        for d in (self.home, self.stubs):
            d.mkdir()
        for n in STUB_NAMES:
            write_stub(self.stubs, n)
        self.label = 'dev.interactive-prototype.comms-watch.unittest'
        import shutil
        self.real_git = shutil.which('git')

    def env(self, os_name=None):
        env = dict(os.environ)
        env.pop('XDG_CONFIG_HOME', None)
        env.pop('XDG_DATA_HOME', None)
        env.update({'HOME': str(self.home), 'INTERACTIVE_PROTOTYPE_COMMS_HOME': str(self.chome),
                    'INTERACTIVE_PROTOTYPE_COMMS_OS': os_name or self.os_name,
                    'INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR': str(self.stubs),
                    'INTERACTIVE_PROTOTYPE_COMMS_LABEL': self.label, 'STUB_REAL_GIT': self.real_git})
        return env

    def watch(self, *args, os_name=None):
        r = subprocess.run([sys.executable, str(WATCH), *map(str, args)], capture_output=True, text=True,
                           env=self.env(os_name))
        try:
            envelope = json.loads(r.stdout)
        except json.JSONDecodeError:
            envelope = None
        return r.returncode, envelope, r.stdout, r.stderr

    def calls(self, name=None):
        path = self.stubs / 'calls.jsonl'
        if not path.exists():
            return []
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
        return [r for r in rows if name is None or r['cmd'] == name]

    def notifications(self):
        return self.calls('osascript')

    def register(self, clone, *extra):
        rc, env, out, err = self.watch('install', '--repo', clone, '--execute', *extra)
        self.assertEqual(rc, 0, (out, err))
        return env

    def run_once(self, clone, notify=True):
        rc, env, out, err = self.watch('run-once', '--notify' if notify else '--no-notify', '--repo', clone)
        self.assertEqual(rc, 0, (out, err))
        return env['data']['repos'][0]

    def read_registry(self):
        return json.loads((self.chome / 'watch.json').read_text(encoding='utf-8'))


# ====================================================================== (1) golden dos conteúdos gerados

class GoldenGeradores(unittest.TestCase):
    def test_dado_caminhos_com_espaco_e_aspas_quando_gerar_plist_entao_xml_valido_e_escapado(self):
        python = '/opt/Meu Python/bin/python3'
        script = '/Users/a b/Library/Application Support/x&y/"comms-watch".py'
        text = cw.gen_launchd_plist('dev.exemplo.watch', python, script, 7, '/tmp/log dir/watch.log',
                                    {'INTERACTIVE_PROTOTYPE_COMMS_HOME': '/tmp/a&b'})
        data = plistlib.loads(text.encode('utf-8'))
        self.assertEqual(data['Label'], 'dev.exemplo.watch')
        self.assertEqual(data['ProgramArguments'], [python, script, 'run-once', '--notify'])
        self.assertEqual(data['StartInterval'], 420)
        self.assertIs(data['RunAtLoad'], True)
        self.assertEqual(data['StandardOutPath'], '/tmp/log dir/watch.log')
        self.assertEqual(data['StandardErrorPath'], '/tmp/log dir/watch.log')
        self.assertEqual(data['ProcessType'], 'Background')
        self.assertEqual(data['EnvironmentVariables'], {'INTERACTIVE_PROTOTYPE_COMMS_HOME': '/tmp/a&b'})
        self.assertIn('x&amp;y', text)
        self.assertIn('<integer>420</integer>', text)

    def test_dado_caminho_com_percent_e_aspas_quando_gerar_systemd_entao_execstart_entre_aspas_e_escapado(self):
        service, timer = cw.gen_systemd_units('/usr/bin/python 3', '/home/a b/50%/"w".py', 5)
        self.assertIn('Type=oneshot', service)
        self.assertIn('ExecStart="/usr/bin/python 3" "/home/a b/50%%/\\"w\\".py" run-once --notify', service)
        for line in ('OnBootSec=1min', 'OnUnitActiveSec=5min', 'Persistent=true', 'WantedBy=timers.target',
                     'Unit=interactive-prototype-comms-watch.service'):
            self.assertIn(line, timer)

    def test_dado_intervalo_quando_gerar_cron_entao_linha_com_marcador_dbus_e_escapes(self):
        text = cw.gen_cron_entry('/usr/bin/python3', '/home/a b/w%x.py', 5, 1000, '/home/a b/watch.log')
        lines = text.splitlines()
        self.assertEqual(lines[0], '# interactive-prototype-comms-watch')
        self.assertTrue(lines[1].startswith('*/5 * * * * DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '))
        self.assertIn("/usr/bin/python3 '/home/a b/w\\%x.py' run-once --notify >> '/home/a b/watch.log' 2>&1",
                      lines[1])
        self.assertEqual(cw.strip_cron_block('MAILTO=x\n' + text + 'outra\n'), 'MAILTO=x\noutra\n')

    def test_dado_caminhos_do_windows_quando_gerar_schtasks_entao_tr_com_aspas_internas_escapadas(self):
        args = cw.gen_schtasks_create('C:\\Program Files\\Python\\pythonw.exe', 'C:\\Users\\A B\\comms-watch.py', 5)
        self.assertEqual(args[:9], ['schtasks', '/Create', '/SC', 'MINUTE', '/MO', '5', '/TN',
                                    'InteractivePrototypeCommsWatch', '/TR'])
        self.assertEqual(args[9], '"C:\\Program Files\\Python\\pythonw.exe" "C:\\Users\\A B\\comms-watch.py" '
                                  'run-once --notify')
        self.assertEqual(args[10], '/F')
        line = subprocess.list2cmdline(args)
        self.assertIn('/TR "\\"C:\\Program Files\\Python\\pythonw.exe\\" \\"C:\\Users\\A B\\comms-watch.py\\" '
                      'run-once --notify" /F', line)

    def test_dado_texto_com_aspas_e_barras_quando_gerar_osascript_entao_escapa_barra_e_aspas(self):
        script = cw.gen_osascript('Recados "do" time', 'Você tem 2 recado(s) em a\\b "c"\npasta')
        self.assertEqual(script, 'display notification "Você tem 2 recado(s) em a\\\\b \\"c\\" pasta" '
                                 'with title "Recados \\"do\\" time"')

    def test_dado_texto_com_xml_e_apostrofo_quando_gerar_toast_entao_xml_escapado_e_aspas_simples_duplicadas(self):
        script = cw.gen_toast_script('T <1>', "Pasta d'a & <b>")
        self.assertIn('&lt;1&gt;', script)
        self.assertIn("d''a &amp; &lt;b&gt;", script)
        self.assertIn('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe', script)
        self.assertIn('ToastNotificationManager', script)
        cmd = cw.gen_powershell_cmd('t', 'x')
        self.assertEqual(cmd[:6], ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                                   '-Command'])

    def test_dado_variavel_de_os_quando_detectar_entao_respeita_a_sobrescrita(self):
        old = os.environ.get(cw.ENV_OS)
        try:
            for name in ('macos', 'linux', 'windows'):
                os.environ[cw.ENV_OS] = name
                self.assertEqual(cw.detect_os(), name)
        finally:
            if old is None:
                os.environ.pop(cw.ENV_OS, None)
            else:
                os.environ[cw.ENV_OS] = old


# ====================================================================== (5a) equivalência com o comms_store (sintético)

NOW = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)


def _t(days_ago):
    return (NOW - timedelta(days=days_ago, hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')


def _member(email, status, roles=()):
    return {'email': email, 'name': email.split('@')[0].title(), 'status': status, 'roles': list(roles)}


class EquivalenciaSintetica(unittest.TestCase):
    def test_dado_eventos_variados_quando_contar_entao_igual_ao_comms_store_para_cada_pessoa(self):
        roster = {'members': [_member('a@x.test', 'approved', ['promoter']), _member('b@x.test', 'approved'),
                              _member('c@x.test', 'pending'), _member('d@x.test', 'rejected'),
                              _member('e@x.test', 'approved', ['promoter'])]}
        cfg = dict(roster, comms={'enabled': True, 'branch': 'comms', 'expiryDays': 30})

        def ev(i, kind, frm, to=(), at=None, **extra):
            return dict({'id': i, 'kind': kind, 'from': frm, 'to': list(to), 'at': at or _t(1), 'subject': 's' + i},
                        **extra)
        events = [
            ev('M1', 'message', 'a@x.test', ['b@x.test']),
            ev('M2', 'message', 'a@x.test', ['@all']),
            ev('M3', 'message', 'b@x.test', ['@promoters']),
            ev('M4', 'question', 'a@x.test', ['b@x.test', 'c@x.test']),
            ev('M5', 'task', 'e@x.test', ['b@x.test']),
            ev('M6', 'confirm', 'a@x.test', ['@all'], options=['sim', 'nao'], priority='urgent'),
            ev('M7', 'message', 'a@x.test', ['b@x.test'], at=_t(40)),                      # expirado (30 dias)
            ev('M8', 'message', 'a@x.test', ['b@x.test'], expiresAt=_t(2)),                 # expirado explícito
            ev('M9', 'message', 'e@x.test', ['b@x.test']),                                  # cancelado pelo remetente
            ev('M10', 'handoff', 'e@x.test', ['b@x.test', 'a@x.test']),
            ev('M11', 'message', 'a@x.test', ['c@x.test']),
            ev('M12', 'message', 'a@x.test', ['d@x.test']),
            ev('M13', 'task', 'b@x.test', ['a@x.test']),
            ev('M14', 'question', 'b@x.test', ['a@x.test']),
            ev('M15', 'message', 'a@x.test', ['e@x.test'], expiresAt=_t(-5)),               # ainda vale
            {'id': 'R1', 'kind': 'read', 'from': 'b@x.test', 'target': 'M1', 'at': _t(0)},
            {'id': 'R2', 'kind': 'answer', 'from': 'b@x.test', 'target': 'M4', 'at': _t(0)},
            {'id': 'R3', 'kind': 'cancel', 'from': 'e@x.test', 'target': 'M9', 'at': _t(0)},
            {'id': 'R4', 'kind': 'cancel', 'from': 'b@x.test', 'target': 'M2', 'at': _t(0)},  # cancel de não-dono
            {'id': 'R5', 'kind': 'accept', 'from': 'a@x.test', 'target': 'M13', 'at': _t(0)},
            {'id': 'R6', 'kind': 'done', 'from': 'a@x.test', 'target': 'M13', 'at': _t(0)},
            {'id': 'R7', 'kind': 'read', 'from': 'b@x.test', 'target': 'R6', 'at': _t(0)},   # viu a novidade R6
            {'id': 'R8', 'kind': 'answer', 'from': 'a@x.test', 'target': 'M14', 'at': _t(0)},
            {'id': 'R9', 'kind': 'decline', 'from': 'b@x.test', 'target': 'M5', 'at': _t(0)},
            {'id': 'R10', 'kind': 'answer', 'from': 'b@x.test', 'target': 'M6', 'at': _t(0)},
            {'id': 'R11', 'kind': 'accept', 'from': 'b@x.test', 'target': 'M13', 'at': _t(0)},  # b é o remetente
            {'id': 'R12', 'kind': 'read', 'from': 'b@x.test', 'target': 'M10', 'at': _t(0)},
            {'id': 'R13', 'kind': 'answer', 'from': 'a@x.test', 'target': 'M7', 'at': _t(0)},
            {'id': 'R14', 'kind': 'read', 'from': 'c@x.test', 'target': 'M11', 'at': _t(0)},
        ]
        seen_nonzero = 0
        for email in ('a@x.test', 'b@x.test', 'c@x.test', 'e@x.test'):
            member = next(m for m in roster['members'] if m['email'] == email)
            expected = cs.pending_count(cs.inbox_for(events, member, roster, cfg, now=NOW))
            got = cw.compute_pending(events, email, roster, cfg, now=NOW)
            self.assertEqual(len(got['ids']), expected, email)
            seen_nonzero += expected
        self.assertGreater(seen_nonzero, 4)

    def test_dado_pessoa_fora_do_roster_quando_contar_entao_so_enderecamento_direto(self):
        roster = {'members': [_member('a@x.test', 'approved', ['promoter'])]}
        events = [{'id': 'M1', 'kind': 'message', 'from': 'a@x.test', 'to': ['@all'], 'at': _t(1)},
                  {'id': 'M2', 'kind': 'message', 'from': 'a@x.test', 'to': ['z@x.test'], 'at': _t(1)}]
        got = cw.compute_pending(events, 'z@x.test', roster, roster, now=NOW)
        self.assertEqual(got['ids'], ['M2'])


# ====================================================================== (2) e (3) install / uninstall

class InstalacaoMacos(WatchCase):
    def setUp(self):
        super().setUp()
        self.clones, self.remote = make_world(self.tmp)
        self.plist = self.home / 'Library' / 'LaunchAgents' / f'{self.label}.plist'

    def test_dado_repo_valido_quando_install_sem_execute_entao_simula_e_nao_cria_nada(self):
        rc, env, out, err = self.watch('install', '--repo', self.clones['bia'])
        self.assertEqual((rc, env['status']), (0, 'DRY_RUN'), (out, err))
        self.assertIn(self.label, env['data']['generated']['plist'])
        self.assertIn(str(self.plist), env['data']['plan']['files'])
        self.assertFalse(self.chome.exists())
        self.assertFalse(self.plist.exists())
        self.assertEqual([c for c in self.calls('launchctl') if c['args'][0] in ('bootstrap', 'bootout')], [])

    def test_dado_install_executado_quando_repetir_e_adicionar_outro_repo_entao_um_unico_agendamento(self):
        env = self.register(self.clones['bia'])
        self.assertEqual(env['status'], 'INSTALLED')
        self.assertEqual(self.read_registry()['repos'][0]['actorEmail'], BIA[1])
        self.assertEqual((self.chome / 'comms-watch.py').read_text(encoding='utf-8'),
                         WATCH.read_text(encoding='utf-8'))
        data = plistlib.loads(self.plist.read_bytes())
        self.assertEqual(data['ProgramArguments'], [sys.executable, str(self.chome / 'comms-watch.py'),
                                                    'run-once', '--notify'])
        self.assertEqual(data['StartInterval'], 300)
        boots = [c for c in self.calls('launchctl') if c['args'][0] == 'bootstrap']
        self.assertEqual(len(boots), 1)
        self.assertEqual(boots[0]['args'], ['bootstrap', f'gui/{os.getuid()}', str(self.plist)])

        again = self.register(self.clones['bia'])
        self.assertEqual(again['status'], 'ALREADY_INSTALLED')
        self.register(self.clones['edu'])
        reg = self.read_registry()
        self.assertEqual(sorted(Path(r['path']).name for r in reg['repos']), ['clone-bia', 'clone-edu'])
        self.assertEqual(len([c for c in self.calls('launchctl') if c['args'][0] == 'bootstrap']), 1)

        rc, st, out, err = self.watch('status')
        self.assertEqual(st['status'], 'INSTALLED')
        self.assertTrue(st['data']['scheduler']['registered'])
        self.assertFalse(st['data']['outdated'])
        self.assertEqual(len(st['data']['repos']), 2)

    def test_dado_dois_repos_quando_uninstall_um_e_depois_o_outro_entao_agendamento_some_so_no_ultimo(self):
        self.register(self.clones['bia'])
        self.register(self.clones['edu'])
        rc, env, out, err = self.watch('uninstall', '--repo', self.clones['bia'])
        self.assertEqual(env['status'], 'DRY_RUN')
        self.assertEqual(len(self.read_registry()['repos']), 2)
        rc, env, out, err = self.watch('uninstall', '--repo', self.clones['bia'], '--execute')
        self.assertEqual((rc, env['status']), (0, 'UNINSTALLED'), (out, err))
        self.assertEqual(len(self.read_registry()['repos']), 1)
        self.assertTrue(self.plist.exists())
        self.assertEqual([c for c in self.calls('launchctl') if c['args'][0] == 'bootout'][1:], [])
        rc, env, out, err = self.watch('uninstall', '--repo', self.clones['edu'], '--execute')
        self.assertEqual(env['status'], 'UNINSTALLED')
        self.assertFalse(self.plist.exists())
        self.assertFalse((self.chome / 'watch.json').exists())
        self.assertFalse((self.chome / 'comms-watch.py').exists())
        self.assertTrue(any(c['args'][0] == 'bootout' and c['args'][1] == f'gui/{os.getuid()}/{self.label}'
                            for c in self.calls('launchctl')))
        rc, env, out, err = self.watch('uninstall', '--all', '--execute')
        self.assertEqual((rc, env['status']), (0, 'NOT_INSTALLED'))

    def test_dado_intervalo_novo_quando_install_de_novo_entao_atualiza_o_agendamento(self):
        self.register(self.clones['bia'])
        env = self.register(self.clones['bia'], '--interval', '9')
        self.assertEqual(env['data']['schedulerAction'], 'updated')
        self.assertEqual(plistlib.loads(self.plist.read_bytes())['StartInterval'], 540)
        self.assertEqual(self.read_registry()['intervalMinutes'], 9)

    def test_dado_intervalo_menor_que_o_minimo_quando_install_entao_erro_de_uso(self):
        rc, env, out, err = self.watch('install', '--repo', self.clones['bia'], '--interval', '1')
        self.assertEqual((rc, env['status']), (2, 'BAD_INTERVAL'))

    def test_dado_protótipo_sem_comunicacao_ligada_quando_install_entao_not_enabled(self):
        plain_tmp = self.tmp / 'plain'
        plain_tmp.mkdir()
        repo, _ = make_group_repo(plain_tmp)
        rc, env, out, err = self.watch('install', '--repo', repo)
        self.assertEqual((rc, env['status']), (1, 'NOT_ENABLED'), (out, err))
        rc, env, out, err = self.watch('install', '--repo', self.tmp)
        self.assertEqual((rc, env['status']), (1, 'NOT_A_REPO'))

    def test_dado_git_sem_email_quando_install_entao_no_identity(self):
        run(['git', '-C', str(self.clones['bia']), 'config', 'user.email', ''])
        rc, env, out, err = self.watch('install', '--repo', self.clones['bia'], '--execute')
        self.assertEqual((rc, env['status']), (1, 'NO_IDENTITY'), (out, err))
        self.assertFalse(self.chome.exists())


class InstalacaoLinux(WatchCase):
    os_name = 'linux'

    def setUp(self):
        super().setUp()
        self.clones, self.remote = make_world(self.tmp)
        self.units = self.home / '.config' / 'systemd' / 'user'

    def test_dado_systemd_disponivel_quando_install_entao_unidades_e_enable_now_idempotentes(self):
        self.register(self.clones['bia'])
        service = (self.units / 'interactive-prototype-comms-watch.service').read_text(encoding='utf-8')
        timer = (self.units / 'interactive-prototype-comms-watch.timer').read_text(encoding='utf-8')
        self.assertIn(f'ExecStart="{sys.executable}" "{self.chome / "comms-watch.py"}" run-once --notify', service)
        self.assertIn('OnUnitActiveSec=5min', timer)
        sysd = [c['args'] for c in self.calls('systemctl')]
        self.assertIn(['--user', 'daemon-reload'], sysd)
        self.assertIn(['--user', 'enable', '--now', 'interactive-prototype-comms-watch.timer'], sysd)
        self.assertFalse((self.stubs / 'crontab.txt').exists())
        self.register(self.clones['edu'])
        enables = [a for a in [c['args'] for c in self.calls('systemctl')] if 'enable' in a]
        self.assertEqual(len(enables), 1)

        rc, env, out, err = self.watch('uninstall', '--all', '--execute')
        self.assertEqual(env['status'], 'UNINSTALLED')
        sysd = [c['args'] for c in self.calls('systemctl')]
        self.assertIn(['--user', 'disable', '--now', 'interactive-prototype-comms-watch.timer'], sysd)
        self.assertFalse((self.units / 'interactive-prototype-comms-watch.service').exists())
        self.assertFalse((self.units / 'interactive-prototype-comms-watch.timer').exists())

    def test_dado_systemd_sem_resposta_quando_install_entao_cai_para_cron_preservando_o_resto(self):
        (self.stubs / 'systemd_rc').write_text('1')
        (self.stubs / 'crontab.txt').write_text('MAILTO=eu@example.test\n0 1 * * * /bin/backup\n')
        env = self.register(self.clones['bia'])
        self.assertEqual(env['data']['schedulerKind'], 'cron')
        text = (self.stubs / 'crontab.txt').read_text()
        self.assertIn('MAILTO=eu@example.test', text)
        self.assertIn('0 1 * * * /bin/backup', text)
        self.assertEqual(text.count('# interactive-prototype-comms-watch'), 1)
        self.assertIn(f'*/5 * * * * DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{os.getuid()}/bus ', text)
        self.assertIn('run-once --notify', text)
        self.assertFalse(self.units.exists())
        writes = [c for c in self.calls('crontab') if c['args'] == ['-']]
        self.register(self.clones['edu'])
        self.assertEqual(len([c for c in self.calls('crontab') if c['args'] == ['-']]), len(writes))
        rc, env, out, err = self.watch('uninstall', '--all', '--execute')
        self.assertEqual(env['status'], 'UNINSTALLED')
        text = (self.stubs / 'crontab.txt').read_text()
        self.assertNotIn('interactive-prototype-comms-watch', text)
        self.assertIn('0 1 * * * /bin/backup', text)

    def test_dado_sem_notify_send_quando_run_once_entao_so_log_e_doctor_avisa(self):
        (self.stubs / 'notify-send').unlink()
        self.register(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        res = self.run_once(self.clones['bia'])
        self.assertEqual(res['count'], 1)
        self.assertEqual(res['notification']['channel'], 'log')
        self.assertFalse(res['notified'])
        rc, env, out, err = self.watch('doctor')
        level = {c['name']: c['level'] for c in env['data']['checks']}
        self.assertEqual(level['notificador'], 'warn')


class InstalacaoWindows(WatchCase):
    os_name = 'windows'

    def setUp(self):
        super().setUp()
        self.clones, self.remote = make_world(self.tmp)

    def test_dado_windows_quando_install_e_uninstall_entao_usa_schtasks_com_tr_entre_aspas(self):
        env = self.register(self.clones['bia'])
        create = [c['args'] for c in self.calls('schtasks') if c['args'][0] == '/Create']
        self.assertEqual(len(create), 1)
        args = create[0]
        self.assertEqual(args[:8], ['/Create', '/SC', 'MINUTE', '/MO', '5', '/TN', 'InteractivePrototypeCommsWatch',
                                    '/TR'])
        self.assertEqual(args[8], f'"{sys.executable}" "{self.chome / "comms-watch.py"}" run-once --notify')
        self.assertEqual(args[9], '/F')
        self.assertIn('/TR "', env['data']['generated']['command'])
        self.register(self.clones['edu'])
        self.assertEqual(len([c for c in self.calls('schtasks') if c['args'][0] == '/Create']), 1)
        self.watch('uninstall', '--all', '--execute')
        self.assertTrue(any(c['args'][:3] == ['/Delete', '/TN', 'InteractivePrototypeCommsWatch']
                            for c in self.calls('schtasks')))
        self.assertFalse((self.chome / 'watch.json').exists())

    def test_dado_windows_quando_notificar_entao_powershell_com_toast_e_sem_assunto(self):
        self.register(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        res = self.run_once(self.clones['bia'])
        self.assertTrue(res['notified'])
        ps = self.calls('powershell')
        self.assertEqual(len(ps), 1)
        script = ps[0]['args'][-1]
        self.assertEqual(ps[0]['args'][:5], ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                                             '-Command'])
        self.assertIn('Você tem 1 recado(s) em clone-bia', script)
        self.assertNotIn('Assunto-SIGILOSO', script)


# ====================================================================== (4) run-once

class RunOnce(WatchCase):
    def setUp(self):
        super().setUp()
        self.clones, self.remote = make_world(self.tmp)

    def test_dado_sem_recados_quando_run_once_entao_nenhuma_notificacao(self):
        self.register(self.clones['bia'])
        res = self.run_once(self.clones['bia'])
        self.assertEqual((res['count'], res['notified']), (0, False))
        self.assertEqual(self.notifications(), [])

    def test_dado_recado_novo_quando_run_once_entao_uma_notificacao_com_contagem_e_sem_assunto_nem_texto(self):
        self.register(self.clones['bia'])
        self.run_once(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        res = self.run_once(self.clones['bia'])
        self.assertEqual((res['count'], res['notified']), (1, True))
        calls = self.notifications()
        self.assertEqual(len(calls), 1)
        script = calls[0]['args'][1]
        self.assertEqual(script, 'display notification "Você tem 1 recado(s) em clone-bia" with title '
                                 '"Recados do time"')
        for secret in ('Assunto-SIGILOSO', 'corpo-sigiloso', ANA[1], 'Ana'):
            self.assertNotIn(secret, json.dumps(calls[0], ensure_ascii=False))

    def test_dado_notificado_quando_nada_mudar_entao_nao_repete_e_novo_recado_notifica_de_novo(self):
        self.register(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        self.run_once(self.clones['bia'])
        self.assertEqual(len(self.notifications()), 1)
        res = self.run_once(self.clones['bia'])
        self.assertFalse(res['notified'])
        self.assertEqual(len(self.notifications()), 1)
        send(self.clones['ana'], 'ana', 'question', 'bia')
        res = self.run_once(self.clones['bia'])
        self.assertTrue(res['notified'])
        self.assertEqual(res['count'], 2)
        self.assertEqual(len(self.notifications()), 2)
        self.assertIn('2 recado(s)', self.notifications()[1]['args'][1])

    def test_dado_recado_lido_ou_respondido_quando_run_once_entao_sai_da_contagem_sem_notificar(self):
        self.register(self.clones['bia'])
        m1 = send(self.clones['ana'], 'ana', 'message', 'bia')
        q1 = send(self.clones['ana'], 'ana', 'question', 'bia')
        self.run_once(self.clones['bia'])
        self.assertEqual(len(self.notifications()), 1)
        ack(self.clones['bia'], 'bia', m1, 'read')
        res = self.run_once(self.clones['bia'])
        self.assertEqual((res['count'], res['notified']), (1, False))
        self.assertEqual(self.read_registry()['repos'][0]['notifiedIds'], [q1])
        ack(self.clones['bia'], 'bia', q1, 'answer', '--body', 'ok')
        res = self.run_once(self.clones['bia'])
        self.assertEqual((res['count'], res['notified']), (0, False))
        self.assertEqual(self.read_registry()['repos'][0]['notifiedIds'], [])
        self.assertEqual(len(self.notifications()), 1)

    def test_dado_resposta_a_recado_enviado_quando_run_once_entao_remetente_e_avisado(self):
        self.register(self.clones['ana'])
        q = send(self.clones['ana'], 'ana', 'question', 'bia')
        self.assertEqual(self.run_once(self.clones['ana'])['count'], 0)
        ack(self.clones['bia'], 'bia', q, 'answer', '--body', 'resposta')
        res = self.run_once(self.clones['ana'])
        self.assertEqual((res['count'], res['notified']), (1, True))

    def test_dado_detail_sender_quando_notificar_entao_inclui_o_nome_do_roster_mas_nunca_o_assunto(self):
        self.register(self.clones['bia'], '--detail', 'sender')
        send(self.clones['ana'], 'ana', 'message', 'bia')
        self.run_once(self.clones['bia'])
        script = self.notifications()[0]['args'][1]
        self.assertIn('Você tem 1 recado(s) em clone-bia (de: Ana Teste)', script)
        self.assertNotIn('Assunto-SIGILOSO', script)

    def test_dado_recado_para_promoters_quando_run_once_entao_so_promoters_contam(self):
        for key in ('ana', 'bia', 'edu'):
            self.register(self.clones[key])
        send(self.clones['bia'], 'bia', 'message', '@promoters')
        self.assertEqual(self.run_once(self.clones['edu'])['count'], 1)
        self.assertEqual(self.run_once(self.clones['ana'])['count'], 1)
        self.assertEqual(self.run_once(self.clones['bia'])['count'], 0)
        self.assertEqual(len(self.notifications()), 2)

    def test_dado_membro_pendente_quando_run_once_entao_so_enxerga_enderecamento_direto(self):
        self.register(self.clones['caio'])
        send(self.clones['ana'], 'ana', 'message', '@all')
        self.assertEqual(self.run_once(self.clones['caio'])['count'], 0)
        self.assertEqual(self.notifications(), [])
        send(self.clones['ana'], 'ana', 'message', 'caio')
        res = self.run_once(self.clones['caio'])
        self.assertEqual((res['count'], res['notified']), (1, True))

    def test_dado_recado_cancelado_pelo_remetente_quando_run_once_entao_sai_da_contagem(self):
        self.register(self.clones['bia'])
        m = send(self.clones['ana'], 'ana', 'message', 'bia')
        self.assertEqual(self.run_once(self.clones['bia'], notify=False)['count'], 1)
        ack(self.clones['ana'], 'ana', m, 'cancel')
        self.assertEqual(self.run_once(self.clones['bia'], notify=False)['count'], 0)

    def test_dado_no_notify_quando_run_once_entao_atualiza_o_estado_sem_notificar_e_nao_notifica_depois(self):
        self.register(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        res = self.run_once(self.clones['bia'], notify=False)
        self.assertEqual((res['count'], res['notified']), (1, False))
        self.assertEqual(self.notifications(), [])
        self.assertTrue(self.read_registry()['repos'][0]['lastSeenSha'])
        self.assertEqual(self.run_once(self.clones['bia'])['notified'], False)

    def test_dado_remoto_inexistente_quando_run_once_entao_silencio_registrado_no_log_e_sem_notificacao(self):
        self.register(self.clones['bia'])
        send(self.clones['ana'], 'ana', 'message', 'bia')
        run(['git', '-C', str(self.clones['bia']), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        rc, env, out, err = self.watch('run-once', '--notify', '--repo', self.clones['bia'])
        self.assertEqual(rc, 0, (out, err))
        res = env['data']['repos'][0]
        self.assertTrue(res['errors'])
        self.assertIn('ls-remote', res['errors'][0])
        self.assertFalse(res['notified'])
        self.assertEqual(self.notifications(), [])
        self.assertIn('ls-remote', (self.chome / 'watch.log').read_text(encoding='utf-8'))
        self.assertIsNone(self.read_registry()['repos'][0]['lastSeenSha'])

    def test_dado_branch_de_comunicacao_inexistente_no_remoto_quando_run_once_entao_silencio_sem_erro(self):
        self.register(self.clones['bia'])
        run(['git', '--git-dir', str(self.remote), 'update-ref', '-d', 'refs/heads/comms'])
        run(['git', '-C', str(self.clones['bia']), 'update-ref', '-d', 'refs/remotes/origin/comms'])
        res = self.run_once(self.clones['bia'])
        self.assertEqual((res['count'], res['errors'], res['notified']), (0, [], False))

    def test_dado_log_grande_quando_run_once_entao_rotaciona_para_log_ponto_1(self):
        self.register(self.clones['bia'])
        self.chome.mkdir(parents=True, exist_ok=True)
        (self.chome / 'watch.log').write_text('x' * (210 * 1024), encoding='utf-8')
        self.run_once(self.clones['bia'])
        self.assertTrue((self.chome / 'watch.log.1').exists())

    def test_dado_repo_nao_registrado_quando_run_once_com_repo_entao_erro(self):
        self.register(self.clones['bia'])
        rc, env, out, err = self.watch('run-once', '--repo', self.clones['edu'])
        self.assertEqual((rc, env['status']), (1, 'REPO_NOT_REGISTERED'))


# ====================================================================== (5b) equivalência com comms-inbox (mensagens reais)

class EquivalenciaComInbox(WatchCase):
    def test_dado_fluxo_real_de_envios_e_recibos_quando_contar_entao_vigia_igual_a_comms_inbox_quiet(self):
        clones, _ = make_world(self.tmp)
        for key in clones:
            self.register(clones[key])
        history = []

        def compare(label):
            for key in ('ana', 'bia', 'caio', 'edu'):
                expected = inbox_count(clones[key], key)
                got = self.run_once(clones[key], notify=False)['count']
                self.assertEqual(got, expected, f'{label}: {key}')
                history.append((label, key, got))

        compare('vazio')
        m1 = send(clones['ana'], 'ana', 'message', 'bia')
        q1 = send(clones['ana'], 'ana', 'question', 'bia')
        m2 = send(clones['bia'], 'bia', 'message', '@promoters')
        c1 = send(clones['ana'], 'ana', 'confirm', '@all', 'Confirma?', 'x', '--option', 'Sim', '--option', 'Nao')
        t1 = send(clones['ana'], 'ana', 'task', 'caio')
        compare('enviados')
        ack(clones['bia'], 'bia', m1, 'read')
        r_q = ack(clones['bia'], 'bia', q1, 'answer', '--body', 'ok')
        r_c = ack(clones['edu'], 'edu', c1, 'answer', '--choice', 'Sim')
        r_t = ack(clones['caio'], 'caio', t1, 'accept')
        compare('respondidos')
        ack(clones['ana'], 'ana', r_q, 'read')
        compare('novidade lida')
        ack(clones['bia'], 'bia', m2, 'cancel')
        r_done = ack(clones['caio'], 'caio', t1, 'done')
        compare('cancelado e tarefa feita')
        send(clones['bia'], 'bia', 'message', 'edu', 'Urgente', 'x', '--priority', 'urgent')
        ack(clones['ana'], 'ana', r_c, 'read')
        ack(clones['ana'], 'ana', r_t, 'read')
        compare('urgente')
        self.assertGreater(max(h[2] for h in history), 0)
        self.assertEqual(len({h[0] for h in history}), 6)
        self.assertTrue(r_done)


# ====================================================================== (6) doctor

class Doctor(WatchCase):
    def setUp(self):
        super().setUp()
        self.clones, self.remote = make_world(self.tmp)

    def levels(self, env):
        return {c['name']: c['level'] for c in env['data']['checks']}

    def test_dado_instalacao_saudavel_quando_doctor_entao_sem_falhas(self):
        self.register(self.clones['bia'])
        rc, env, out, err = self.watch('doctor')
        self.assertEqual((rc, env['status']), (0, 'DOCTOR_OK'), out)
        levels = self.levels(env)
        for name in ('git', 'diretorio-de-dados', 'registro', 'versao', 'agendamento', 'notificador', 'repo:clone-bia'):
            self.assertEqual(levels[name], 'ok', (name, env['data']['checks']))

    def test_dado_nada_instalado_quando_doctor_entao_falha_e_sugere_instalar(self):
        rc, env, out, err = self.watch('doctor')
        self.assertEqual(rc, 1)
        levels = self.levels(env)
        self.assertEqual(levels['registro'], 'fail')
        self.assertEqual(levels['agendamento'], 'fail')

    def test_dado_git_que_pede_senha_quando_doctor_entao_fail_com_a_mensagem_pedida(self):
        self.register(self.clones['bia'])
        write_stub(self.stubs, 'git')
        (self.stubs / 'git_auth_fail').write_text('1')
        rc, env, out, err = self.watch('doctor')
        self.assertEqual(rc, 1)
        check = next(c for c in env['data']['checks'] if c['name'] == 'repo:clone-bia')
        self.assertEqual(check['level'], 'fail')
        self.assertIn('git não consegue autenticar sem pedir senha: configure chave SSH ou credential helper',
                      check['message'])

    def test_dado_remoto_inexistente_quando_doctor_entao_fail_de_ls_remote(self):
        self.register(self.clones['bia'])
        run(['git', '-C', str(self.clones['bia']), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        rc, env, out, err = self.watch('doctor', '--repo', self.clones['bia'])
        self.assertEqual(rc, 1)
        check = next(c for c in env['data']['checks'] if c['name'] == 'repo:clone-bia')
        self.assertEqual(check['level'], 'fail')
        self.assertIn('ls-remote', check['message'])

    def test_dado_copia_instalada_desatualizada_quando_doctor_entao_warn_sugerindo_install_execute(self):
        self.register(self.clones['bia'])
        copy = self.chome / 'comms-watch.py'
        copy.write_text(copy.read_text(encoding='utf-8').replace('WATCH_VERSION = "1.0.0"',
                                                                'WATCH_VERSION = "0.9.0"', 1), encoding='utf-8')
        rc, env, out, err = self.watch('doctor')
        check = next(c for c in env['data']['checks'] if c['name'] == 'versao')
        self.assertEqual(check['level'], 'warn')
        self.assertIn('install', check['message'])
        self.assertIn('--execute', check['message'])
        rc, st, out, err = self.watch('status')
        self.assertTrue(st['data']['outdated'])

    def test_dado_agendamento_apontando_para_outro_python_quando_doctor_entao_warn(self):
        self.register(self.clones['bia'])
        plist = self.home / 'Library' / 'LaunchAgents' / f'{self.label}.plist'
        plist.write_text(plist.read_text(encoding='utf-8').replace(sys.executable, '/outro/python'),
                         encoding='utf-8')
        rc, env, out, err = self.watch('doctor')
        self.assertEqual(self.levels(env)['agendamento'], 'warn')


# ====================================================================== (7) teste real no macOS (opt-in)

@unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('COMMS_WATCH_REAL_MACOS') == '1',
                     'teste real no macOS: defina COMMS_WATCH_REAL_MACOS=1')
class MacosReal(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.label = 'dev.interactive-prototype.comms-watch.test' + secrets.token_hex(4)
        self.chome = self.tmp / 'dados'
        self.plist = Path.home() / 'Library' / 'LaunchAgents' / f'{self.label}.plist'
        self.addCleanup(self.cleanup_real)

    def cleanup_real(self):
        subprocess.run(['launchctl', 'bootout', f'gui/{os.getuid()}/{self.label}'], capture_output=True)
        if self.plist.exists():
            self.plist.unlink()

    def watch(self, *args):
        env = dict(os.environ, INTERACTIVE_PROTOTYPE_COMMS_HOME=str(self.chome),
                   INTERACTIVE_PROTOTYPE_COMMS_LABEL=self.label)
        for k in ('INTERACTIVE_PROTOTYPE_COMMS_OS', 'INTERACTIVE_PROTOTYPE_COMMS_STUB_DIR'):
            env.pop(k, None)
        r = subprocess.run([sys.executable, str(WATCH), *map(str, args)], capture_output=True, text=True, env=env)
        return r.returncode, json.loads(r.stdout), r.stderr

    def launchctl_print(self):
        return subprocess.run(['launchctl', 'print', f'gui/{os.getuid()}/{self.label}'],
                              capture_output=True, text=True).returncode

    def test_dado_macos_real_quando_instalar_notificar_e_remover_entao_agendamento_surge_e_some(self):
        clones, _ = make_world(self.tmp)
        rc, env, err = self.watch('install', '--repo', clones['bia'], '--execute')
        self.assertEqual(rc, 0, env)
        self.assertTrue(self.plist.exists())
        time.sleep(2)  # RunAtLoad roda uma varredura sem recados
        self.assertEqual(self.launchctl_print(), 0)
        rc, st, err = self.watch('status')
        self.assertTrue(st['data']['scheduler']['registered'])
        self.assertEqual(st['data']['intervalMinutes'], 5)

        send(clones['ana'], 'ana', 'message', 'bia')
        rc, env, err = self.watch('run-once', '--notify', '--repo', clones['bia'])
        res = env['data']['repos'][0]
        self.assertEqual(rc, 0, env)
        self.assertEqual(res['count'], 1)
        self.assertTrue(res['notified'], env)
        self.assertEqual(res['notification'], {'sent': True, 'channel': 'osascript', 'rc': 0})
        log = (self.chome / 'watch.log').read_text(encoding='utf-8')
        self.assertIn('notificação via osascript rc=0', log)
        self.assertNotIn('Assunto-SIGILOSO', log)
        rc, env, err = self.watch('run-once', '--notify', '--repo', clones['bia'])
        self.assertFalse(env['data']['repos'][0]['notified'])

        rc, env, err = self.watch('uninstall', '--all', '--execute')
        self.assertEqual((rc, env['status']), (0, 'UNINSTALLED'), env)
        self.assertNotEqual(self.launchctl_print(), 0)
        self.assertFalse(self.plist.exists())
        leftovers = [p.name for p in (Path.home() / 'Library' / 'LaunchAgents').glob('*comms-watch.test*')
                     if self.label in p.name]
        self.assertEqual(leftovers, [])
        self.assertFalse(self.chome.exists())


if __name__ == '__main__':
    unittest.main()
