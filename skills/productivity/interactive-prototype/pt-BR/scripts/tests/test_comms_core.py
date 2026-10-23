import json
import unittest
from pathlib import Path

from group_fixtures import ANA, BIA, CAIO, DANI, EDU, git_out, make_group_repo, member_clone, remote_sha
from helpers import TmpDirMixin, run, run_script

import comms_store as cs
import protolib

SETUP, SEND, INBOX, ACK, HOOK = ('comms-setup.py', 'comms-send.py', 'comms-inbox.py', 'comms-ack.py',
                                 'comms-hook.py')


def call(script, repo, user, *extra):
    return run_script(script, '--repo', repo, '--actor-email', user[1], *extra)


class CommsBase(TmpDirMixin):
    def setUp(self):
        super().setUp()
        self.ana_repo, self.remote = make_group_repo(self.tmp)
        self.bia_repo = member_clone(self.remote, self.tmp, BIA)
        self.caio_repo = member_clone(self.remote, self.tmp, CAIO)
        self.dani_repo = member_clone(self.remote, self.tmp, DANI)
        self.edu_repo = member_clone(self.remote, self.tmp, EDU)

    def enable(self):
        code, env, out, err = call(SETUP, self.ana_repo, ANA, '--enable', '--execute')
        self.assertEqual((code, env['status']), (0, 'ENABLED'), out + err)
        for repo in (self.bia_repo, self.caio_repo, self.dani_repo, self.edu_repo):
            cfg = json.loads((Path(repo) / 'prototype.config.json').read_text(encoding='utf-8'))
            cfg['comms'] = {'enabled': True, 'branch': 'comms', 'expiryDays': 30, 'reminderHours': 24}
            (Path(repo) / 'prototype.config.json').write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')

    def send(self, repo, user, kind='message', to=('bia@example.test',), subject='Oi', body='texto', *extra, ok=True):
        args = ['--kind', kind, '--subject', subject, '--body', body]
        for t in to:
            args += ['--to', t]
        code, env, out, err = call(SEND, repo, user, *args, *extra, '--execute')
        if ok:
            self.assertEqual((code, env['status']), (0, 'SENT'), out + err)
        return code, env

    def inbox(self, repo, user, *extra):
        code, env, out, err = call(INBOX, repo, user, *extra)
        self.assertEqual(code, 0, out + err)
        return env

    def comms_files(self):
        return [p for p in run(['git', '--git-dir', str(self.remote), 'ls-tree', '-r', '--name-only', 'comms']
                               ).stdout.split() if p.startswith('events/')]


class Setup(CommsBase, unittest.TestCase):
    def test_given_non_promoter_when_enable_then_refused(self):
        code, env, _, _ = call(SETUP, self.bia_repo, BIA, '--enable', '--execute')
        self.assertEqual((code, env['status']), (1, 'NOT_ALLOWED'))

    def test_given_promoter_when_enable_dry_run_then_nothing_is_written(self):
        code, env, _, _ = call(SETUP, self.ana_repo, ANA, '--enable')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'))
        self.assertNotIn('comms', json.loads((Path(self.ana_repo) / 'prototype.config.json').read_text()))
        self.assertEqual(run(['git', '--git-dir', str(self.remote), 'branch', '--list', 'comms']).stdout, '')

    def test_given_promoter_when_enable_then_orphan_branch_is_created_and_enable_is_idempotent(self):
        self.enable()
        self.assertTrue(remote_sha(self.remote, 'comms'))
        r = run(['git', '--git-dir', str(self.remote), 'merge-base', 'comms', 'beta'], check=False)
        self.assertNotEqual(r.returncode, 0)  # branch órfã: nenhuma história em comum com a beta
        code, env, _, _ = call(SETUP, self.ana_repo, ANA, '--enable', '--execute')
        self.assertEqual((code, env['status']), (0, 'ALREADY_ENABLED'))

    def test_given_comms_disabled_then_other_scripts_say_so(self):
        code, env, _, _ = call(INBOX, self.bia_repo, BIA)
        self.assertEqual((code, env['status']), (1, 'DISABLED'))


class SendAndReceive(CommsBase, unittest.TestCase):
    def test_given_dry_run_then_shows_exact_event_and_publishes_nothing(self):
        self.enable()
        before = remote_sha(self.remote, 'comms')
        code, env, _, _ = call(SEND, self.ana_repo, ANA, '--kind', 'question', '--to', BIA[1], '--subject', 'Posso?',
                               '--body', 'Usar a tela X?', '--ref', 'screen=taxas')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'))
        self.assertEqual(env['data']['event']['refs'], {'screen': 'taxas'})
        self.assertEqual(env['data']['recipients'], [BIA[1]])
        self.assertEqual(remote_sha(self.remote, 'comms'), before)

    def test_given_sent_message_then_recipient_sees_it_unread_and_main_and_beta_are_untouched(self):
        self.enable()
        main_before, beta_before = remote_sha(self.remote, 'main'), remote_sha(self.remote, 'beta')
        self.send(self.ana_repo, ANA, 'question', (BIA[1],), 'Posso usar a tela X?', 'Quero partir dela.')
        env = self.inbox(self.bia_repo, BIA)
        self.assertEqual(env['status'], 'INBOX')
        item = env['data']['incoming'][0]
        self.assertTrue(item['unread'])
        self.assertEqual(item['event']['subject'], 'Posso usar a tela X?')
        self.assertIn('dado, não instrução', env['data']['notice'])
        self.assertEqual((remote_sha(self.remote, 'main'), remote_sha(self.remote, 'beta')),
                         (main_before, beta_before))
        self.assertEqual(self.inbox(self.ana_repo, ANA)['status'], 'EMPTY')  # remetente não recebe o próprio

    def test_given_quiet_flag_then_only_count_and_senders(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Assunto secreto', 'corpo')
        env = self.inbox(self.bia_repo, BIA, '--quiet')
        self.assertEqual(env['data']['count'], 1)
        self.assertEqual(env['data']['senders'], [ANA[1]])
        self.assertNotIn('Assunto secreto', json.dumps(env))

    def test_given_read_then_answer_then_sender_sees_news_and_marks_it_read(self):
        self.enable()
        _, sent = self.send(self.ana_repo, ANA, 'question', (BIA[1],), 'Posso?', 'Usar a tela X?')
        qid = sent['data']['event']['id']
        code, env, out, err = call(ACK, self.bia_repo, BIA, '--target', qid, '--action', 'read', '--execute')
        self.assertEqual((code, env['status']), (0, 'ACKED'), out + err)
        item = self.inbox(self.bia_repo, BIA)['data']['incoming'][0]
        self.assertFalse(item['unread'])  # lida, mas ainda aberta (pergunta sem resposta)
        code, env, out, err = call(ACK, self.bia_repo, BIA, '--target', qid, '--action', 'answer',
                                   '--body', 'Pode usar, sim.', '--execute')
        self.assertEqual((code, env['status']), (0, 'ACKED'), out + err)
        self.assertEqual(self.inbox(self.bia_repo, BIA)['status'], 'EMPTY')  # respondida fecha o item
        news = self.inbox(self.ana_repo, ANA)['data']['news']
        self.assertEqual(news[0]['receipt']['body'], 'Pode usar, sim.')
        rid = news[0]['receipt']['id']
        code, env, _, _ = call(ACK, self.ana_repo, ANA, '--target', rid, '--action', 'read', '--execute')
        self.assertEqual((code, env['status']), (0, 'ACKED'))
        self.assertEqual(self.inbox(self.ana_repo, ANA)['data']['news'], [])

    def test_given_confirm_then_choice_must_be_one_of_the_options(self):
        self.enable()
        _, sent = self.send(self.ana_repo, ANA, 'confirm', (BIA[1],), 'Publicar hoje?', '', '--option', 'sim',
                            '--option', 'não')
        cid = sent['data']['event']['id']
        code, env, _, _ = call(ACK, self.bia_repo, BIA, '--target', cid, '--action', 'answer', '--choice', 'talvez')
        self.assertEqual((code, env['status']), (1, 'BAD_CHOICE'))
        code, env, _, _ = call(ACK, self.bia_repo, BIA, '--target', cid, '--action', 'answer', '--choice', 'sim',
                               '--execute')
        self.assertEqual((code, env['status']), (0, 'ACKED'))

    def test_given_task_then_accept_keeps_it_open_until_done(self):
        self.enable()
        _, sent = self.send(self.ana_repo, ANA, 'task', (BIA[1],), 'Revisar textos', 'Tela de taxas.')
        tid = sent['data']['event']['id']
        call(ACK, self.bia_repo, BIA, '--target', tid, '--action', 'accept', '--execute')
        item = self.inbox(self.bia_repo, BIA)['data']['incoming'][0]
        self.assertTrue(item['accepted'])
        call(ACK, self.bia_repo, BIA, '--target', tid, '--action', 'done', '--execute')
        self.assertEqual(self.inbox(self.bia_repo, BIA)['status'], 'EMPTY')

    def test_given_cancel_then_only_sender_can_and_item_disappears(self):
        self.enable()
        _, sent = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Ops', 'texto')
        mid = sent['data']['event']['id']
        code, env, _, _ = call(ACK, self.bia_repo, BIA, '--target', mid, '--action', 'cancel')
        self.assertEqual((code, env['status']), (1, 'NOT_OWNER'))
        code, env, _, _ = call(ACK, self.ana_repo, ANA, '--target', mid, '--action', 'cancel', '--execute')
        self.assertEqual((code, env['status']), (0, 'ACKED'))
        self.assertEqual(self.inbox(self.bia_repo, BIA)['status'], 'EMPTY')


class Permissions(CommsBase, unittest.TestCase):
    def test_given_rejected_member_then_cannot_send_or_read(self):
        self.enable()
        code, env = self.send(self.dani_repo, DANI, 'message', (BIA[1],), ok=False)
        self.assertEqual((code, env['status']), (1, 'NOT_ALLOWED'))
        code, env, _, _ = call(INBOX, self.dani_repo, DANI)
        self.assertEqual((code, env['status']), (1, 'NOT_ALLOWED'))

    def test_given_pending_member_then_sends_only_to_promoters(self):
        self.enable()
        code, env = self.send(self.caio_repo, CAIO, 'message', (BIA[1],), ok=False)
        self.assertEqual((code, env['status']), (1, 'PENDING_SCOPE'))
        code, env = self.send(self.caio_repo, CAIO, 'message', ('@promoters',), 'Quando me aprovam?', 'oi', ok=False)
        self.assertEqual((code, env['status']), (0, 'SENT'))
        self.assertEqual(self.inbox(self.ana_repo, ANA)['data']['incoming'][0]['event']['from'], CAIO[1])

    def test_given_pending_member_then_reads_only_what_is_addressed_directly(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', ('@all',), 'Para todos', 'x')
        self.assertEqual(self.inbox(self.caio_repo, CAIO)['status'], 'EMPTY')
        self.assertEqual(self.inbox(self.bia_repo, BIA)['status'], 'INBOX')
        self.send(self.ana_repo, ANA, 'message', (CAIO[1],), 'Para o Caio', 'x')
        self.assertEqual([i['event']['subject'] for i in self.inbox(self.caio_repo, CAIO)['data']['incoming']],
                         ['Para o Caio'])

    def test_given_all_address_then_approved_members_get_it_but_not_the_sender(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', ('@all',), 'Aviso', 'x')
        for repo, user, expected in ((self.bia_repo, BIA, 'INBOX'), (self.edu_repo, EDU, 'INBOX'),
                                     (self.ana_repo, ANA, 'EMPTY'), (self.dani_repo, DANI, None)):
            if expected:
                self.assertEqual(self.inbox(repo, user)['status'], expected)

    def test_given_unknown_or_rejected_recipient_then_refused(self):
        self.enable()
        for to in ('ninguem@example.test', DANI[1]):
            code, env = self.send(self.ana_repo, ANA, 'message', (to,), ok=False)
            self.assertEqual((code, env['status']), (1, 'UNKNOWN_RECIPIENT'))

    def test_given_secret_in_text_then_refused_without_echoing_it(self):
        self.enable()
        secret = 'ghp_' + 'a1B2c3D4e5F6g7H8i9J0k1L2'
        code, env = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Chave', f'use {secret}', ok=False)
        self.assertEqual((code, env['status']), (1, 'SECRET_DETECTED'))
        self.assertNotIn(secret, json.dumps(env))
        code, env = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Senha', 'senha: abc12345', ok=False)
        self.assertEqual(env['status'], 'SECRET_DETECTED')

    def test_given_limits_then_refused(self):
        self.enable()
        code, env = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'x' * 121, ok=False)
        self.assertEqual(env['status'], 'BAD_SUBJECT')
        code, env = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'ok', 'y' * 2001, ok=False)
        self.assertEqual(env['status'], 'BODY_TOO_LONG')


class Delivery(CommsBase, unittest.TestCase):
    def test_given_two_senders_pushing_with_stale_state_then_both_events_survive_without_conflict(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (EDU[1],), 'Da Ana', 'x')
        # a Bia ainda não sincronizou nada: a ponta local dela é velha
        self.send(self.bia_repo, BIA, 'message', (EDU[1],), 'Da Bia', 'x')
        subjects = sorted(i['event']['subject'] for i in self.inbox(self.edu_repo, EDU)['data']['incoming'])
        self.assertEqual(subjects, ['Da Ana', 'Da Bia'])
        self.assertEqual(len(self.comms_files()), 2)

    def test_given_offline_then_event_is_kept_locally_and_goes_with_next_send(self):
        self.enable()
        run(['git', '-C', str(self.bia_repo), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        code, env = self.send(self.bia_repo, BIA, 'message', (EDU[1],), 'Offline', 'x', ok=False, *())
        self.assertEqual((code, env['status']), (1, 'NOT_SYNCED'))
        self.assertEqual(self.comms_files(), [])
        run(['git', '-C', str(self.bia_repo), 'remote', 'set-url', 'origin', str(self.remote)])
        self.send(self.bia_repo, BIA, 'message', (EDU[1],), 'Online', 'x')
        subjects = sorted(i['event']['subject'] for i in self.inbox(self.edu_repo, EDU)['data']['incoming'])
        self.assertEqual(subjects, ['Offline', 'Online'])

    def test_given_expired_message_then_it_leaves_the_inbox_but_stays_in_history(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Velho', 'x', '--expires-in-days', '1')
        cfg = json.loads((Path(self.bia_repo) / 'prototype.config.json').read_text())
        cs.refresh(self.bia_repo, cfg)
        events = cs.read_events(self.bia_repo, cfg)
        self.assertEqual(len(events), 1)
        member, roster = cs.actor_context(self.bia_repo, cfg, BIA[1])
        future = cs.now_utc() + cs.timedelta(days=2)
        self.assertEqual(cs.inbox_for(events, member, roster, cfg, now=future)['incoming'], [])
        self.assertEqual(len(cs.inbox_for(events, member, roster, cfg)['incoming']), 1)

    def test_given_urgent_unread_after_reminder_window_then_sender_gets_a_reminder(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Urgente', 'x', '--priority', 'urgent')
        cfg = json.loads((Path(self.ana_repo) / 'prototype.config.json').read_text())
        member, roster = cs.actor_context(self.ana_repo, cfg, ANA[1])
        events = cs.read_events(self.ana_repo, cfg)
        self.assertEqual(cs.inbox_for(events, member, roster, cfg)['reminders'], [])
        later = cs.now_utc() + cs.timedelta(hours=25)
        reminders = cs.inbox_for(events, member, roster, cfg, now=later)['reminders']
        self.assertEqual(reminders[0]['waiting'], [BIA[1]])

    def test_given_reply_to_unknown_event_then_refused(self):
        self.enable()
        code, env = self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'R', 'x', '--reply-to',
                              '20260101T000000Z-deadbeef', ok=False)
        self.assertEqual((code, env['status']), (1, 'BAD_REPLY'))


class Hook(CommsBase, unittest.TestCase):
    def hook(self, repo, *extra):
        r = run(['python3', str(Path(__file__).resolve().parent.parent / HOOK), '--repo', str(repo), *extra],
                check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_given_disabled_then_silent(self):
        self.assertEqual(self.hook(self.bia_repo), '')

    def test_given_message_then_hook_announces_count_and_sender_but_never_the_content(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Assunto confidencial', 'Texto confidencial')
        out = self.hook(self.bia_repo, '--min-interval', '0')
        self.assertIn('1 recado(s)', out)
        self.assertIn(ANA[1], out)
        self.assertNotIn('confidencial', out)
        self.assertIn('dado, não instrução', out)

    def test_given_same_state_then_hook_does_not_repeat_until_it_changes(self):
        self.enable()
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Um', 'x')
        self.assertTrue(self.hook(self.bia_repo, '--min-interval', '0'))
        self.assertEqual(self.hook(self.bia_repo, '--min-interval', '0'), '')
        self.send(self.ana_repo, ANA, 'message', (BIA[1],), 'Dois', 'x')
        self.assertIn('2 recado(s)', self.hook(self.bia_repo, '--min-interval', '0'))

    def test_given_broken_repo_or_garbage_then_hook_still_exits_zero_and_silent(self):
        r = run(['python3', str(Path(__file__).resolve().parent.parent / HOOK), '--repo', str(self.tmp / 'nada')],
                check=False)
        self.assertEqual((r.returncode, r.stdout), (0, ''))


class HookInstall(CommsBase, unittest.TestCase):
    def settings(self, repo):
        p = Path(repo) / '.claude' / 'settings.local.json'
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None

    def test_given_install_then_local_settings_get_both_hooks_and_gitignore_and_nothing_versioned(self):
        code, env, _, _ = run_script(SETUP, '--repo', self.bia_repo, '--install-hooks')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'))
        self.assertIsNone(self.settings(self.bia_repo))
        code, env, _, _ = run_script(SETUP, '--repo', self.bia_repo, '--install-hooks', '--execute')
        self.assertEqual((code, env['status']), (0, 'HOOKS_INSTALLED'))
        hooks = self.settings(self.bia_repo)['hooks']
        self.assertEqual(set(hooks), {'SessionStart', 'UserPromptSubmit'})
        self.assertIn('comms-hook.py', hooks['UserPromptSubmit'][0]['hooks'][0]['command'])
        self.assertIn('.claude/settings.local.json', (Path(self.bia_repo) / '.gitignore').read_text().split())
        self.assertFalse((Path(self.bia_repo) / '.claude' / 'settings.json').exists())
        code, env, _, _ = run_script(SETUP, '--repo', self.bia_repo, '--install-hooks', '--execute')
        self.assertEqual(env['status'], 'HOOKS_ALREADY_INSTALLED')

    def test_given_foreign_hooks_then_install_and_uninstall_keep_them(self):
        p = Path(self.bia_repo) / '.claude'
        p.mkdir()
        foreign = {'hooks': {'UserPromptSubmit': [{'hooks': [{'type': 'command', 'command': 'echo outro'}]}]},
                   'permissions': {'allow': ['Bash(ls)']}}
        (p / 'settings.local.json').write_text(json.dumps(foreign), encoding='utf-8')
        run_script(SETUP, '--repo', self.bia_repo, '--install-hooks', '--execute')
        self.assertEqual(len(self.settings(self.bia_repo)['hooks']['UserPromptSubmit']), 2)
        code, env, _, _ = run_script(SETUP, '--repo', self.bia_repo, '--uninstall-hooks', '--execute')
        self.assertEqual(env['status'], 'HOOKS_REMOVED')
        after = self.settings(self.bia_repo)
        self.assertEqual(after['permissions'], foreign['permissions'])
        self.assertEqual(after['hooks'], foreign['hooks'])


class StoreUnits(unittest.TestCase):
    def test_secret_patterns_do_not_flag_normal_text(self):
        self.assertEqual(cs.secret_hits('Posso usar a tela de taxas como base? Versão v1.2.0-beta.3.'), [])
        self.assertTrue(cs.secret_hits('-----BEGIN RSA PRIVATE KEY-----'))
        self.assertTrue(cs.secret_hits('tok' + 'en = ' + 'abcdef' + '123456'))

    def test_event_id_and_path_roundtrip(self):
        eid = cs.new_id()
        self.assertRegex(eid, cs.ID_RE.pattern)
        self.assertRegex(cs.event_path(eid), cs.EVENT_PATH_RE.pattern)

    def test_rate_limit_counts_only_the_last_hour_of_the_same_sender(self):
        sender = {'email': ANA[1], 'status': 'approved', 'roles': ['promoter']}
        roster = {'members': [sender, {'email': BIA[1], 'status': 'approved', 'roles': ['contributor']}]}
        now = cs.now_utc()
        existing = [{'from': ANA[1], 'at': cs.iso(now)}] * cs.MAX_PER_HOUR
        with self.assertRaises(cs.CommsError) as ctx:
            cs.validate_event({'kind': 'message', 'to': [BIA[1]], 'subject': 's', 'body': 'b'}, sender, roster,
                              existing)
        self.assertEqual(ctx.exception.code, 'RATE_LIMIT')
        old = [{'from': ANA[1], 'at': cs.iso(now - cs.timedelta(hours=2))}] * cs.MAX_PER_HOUR
        cs.validate_event({'kind': 'message', 'to': [BIA[1]], 'subject': 's', 'body': 'b'}, sender, roster, old)


if __name__ == '__main__':
    unittest.main()
