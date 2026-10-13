"""Testes de identity-check.py (repos temporários; CLIs de host simuladas por scripts em PATH isolado)."""

import json
import os
import shutil
import stat
import unittest
from unittest import mock

from helpers import TmpDirMixin, commit_all, make_repo, run, run_script, write

FAKE_GH = """#!/bin/sh
case "$1 $2" in
  "auth status") [ "$FAKE_GH_AUTH" = "fail" ] && exit 1; exit 0 ;;
  "api user") echo "$FAKE_GH_LOGIN"; exit 0 ;;
esac
exit 1
"""


class IdentityBase(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        git_real = shutil.which('git')
        self.add_tool('git', f'#!/bin/sh\nexec "{git_real}" "$@"\n')
        gcfg = self.tmp / 'global.gitconfig'
        gcfg.write_text('')
        self.gcfg = gcfg
        patcher = mock.patch.dict(os.environ, {
            'PATH': str(self.bin), 'GIT_CONFIG_GLOBAL': str(gcfg), 'GIT_CONFIG_NOSYSTEM': '1',
            'FAKE_GH_LOGIN': 'ana-gh'})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo, _ = make_repo(self.tmp)

    def add_tool(self, name, body):
        p = self.bin / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def member(self, email='ana@example.test', status='approved', roles=('promoter',), **extra):
        m = {'name': 'Ana Teste', 'email': email, 'roles': list(roles), 'profile': 'product', 'status': status,
             'registeredAt': '2026-01-01T00:00:00Z', 'statusChangedAt': '2026-01-01T00:00:00Z',
             'statusChangedAtCommit': None, 'statusHistory': [], 'identityEvidence': 'git-only'}
        m.update(extra)
        return m

    def config(self, members, **extra):
        cfg = {'skill': {'name': 'interactive-prototype', 'version': '2.0.0'}, 'groupMode': True,
               'remote': 'origin', 'policy': {'promoters': 'listed', 'requireSignedCommits': False,
                                              'pendingExpiryDays': 7}, 'members': members}
        cfg.update(extra)
        write(self.repo / 'prototype.config.json', json.dumps(cfg))

    def check(self, *args):
        return run_script('identity-check.py', '--repo', self.repo, *args)

    def saved_members(self):
        return json.loads((self.repo / 'prototype.config.json').read_text())['members']


class TestStatuses(IdentityBase):
    def test_no_config_is_solo(self):
        code, env, *_ = self.check()
        self.assertEqual((code, env['status'], env['data']['mode']), (0, 'NO_CONFIG', 'edit'))

    def test_given_config_without_group_mode_then_person_is_identified_by_git_only(self):
        self.config([], groupMode=False)
        code, env, *_ = self.check('--no-host')
        self.assertEqual((code, env['status'], env['data']['mode']), (0, 'SOLO', 'edit'))
        self.assertTrue(env['data']['name'] and env['data']['email'])
        self.assertEqual(self.saved_members(), [])

    def test_invalid_config(self):
        write(self.repo / 'prototype.config.json', '{nope')
        code, env, *_ = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(env['problems'][0]['code'], 'CONFIG_INVALID')

    def test_not_a_repo_exits_2(self):
        r = run_script('identity-check.py', '--repo', self.tmp / 'bin')
        self.assertEqual(r[0], 2)

    def test_approved_promoter_sees_pending_members(self):
        self.config([self.member(),
                     self.member('novo@example.test', status='pending', roles=('contributor',),
                                 registeredAt='2020-01-01T00:00:00Z', identityEvidence='host-verified')])
        code, env, *_ = self.check('--no-host')
        d = env['data']
        self.assertEqual((code, env['status'], d['mode']), (0, 'IDENTIFIED_APPROVED', 'edit'))
        self.assertTrue(d['canPromote'] and d['canDecideMembers'])
        self.assertEqual(d['roles'], ['promoter'])
        p = d['pendingMembers'][0]
        self.assertEqual(p['email'], 'novo@example.test')
        self.assertTrue(p['expired'])
        self.assertGreater(p['daysPending'], 7)
        self.assertEqual(p['identityEvidence'], 'host-verified')

    def test_approved_contributor_cannot_promote(self):
        self.config([self.member(roles=('contributor',))])
        _, env, *_ = self.check('--no-host')
        d = env['data']
        self.assertEqual(env['status'], 'IDENTIFIED_APPROVED')
        self.assertFalse(d['canPromote'] or d['canDecideMembers'])
        self.assertNotIn('pendingMembers', d)

    def test_pending_is_edit_limited(self):
        self.config([self.member(status='pending', roles=('promoter',))])
        code, env, *_ = self.check('--no-host')
        d = env['data']
        self.assertEqual((code, env['status'], d['mode']), (0, 'IDENTIFIED_PENDING', 'edit-limited'))
        self.assertFalse(d['canPromote'] or d['canDecideMembers'])

    def test_pending_expired_warns(self):
        self.config([self.member(status='pending', roles=('contributor',), registeredAt='2020-01-01T00:00:00Z')])
        code, env, *_ = self.check('--no-host')
        self.assertEqual(code, 0)
        self.assertIn('PENDING_EXPIRED', [p['code'] for p in env['problems']])

    def test_rejected_and_revoked_are_consult(self):
        for status, expected in (('rejected', 'REJECTED'), ('revoked', 'REVOKED')):
            with self.subTest(status):
                self.config([self.member(status=status)])
                code, env, *_ = self.check('--no-host')
                self.assertEqual((code, env['status'], env['data']['mode']), (1, expected, 'consult'))
                self.assertFalse(env['data']['canPromote'])

    def test_unknown_is_consult_with_question(self):
        self.config([self.member('outra@example.test')])
        code, env, *_ = self.check('--no-host')
        self.assertEqual((code, env['status'], env['data']['mode']), (1, 'UNKNOWN', 'consult'))
        self.assertTrue(env['questions'])
        self.assertEqual(len(self.saved_members()), 1)

    def test_email_match_is_case_insensitive(self):
        self.config([self.member('ANA@Example.Test')])
        _, env, *_ = self.check('--no-host')
        self.assertEqual(env['status'], 'IDENTIFIED_APPROVED')


class TestGitIdentity(IdentityBase):
    def unset_local(self):
        run(['git', '-C', str(self.repo), 'config', '--unset', 'user.name'])
        run(['git', '-C', str(self.repo), 'config', '--unset', 'user.email'])

    def test_missing_identity(self):
        self.config([self.member()])
        self.unset_local()
        code, env, *_ = self.check('--no-host')
        self.assertEqual((code, env['status'], env['data']['mode']), (1, 'NO_IDENTITY', 'consult'))
        self.assertTrue(env['questions'])

    def test_flags_fill_identity_without_writing_git_config(self):
        self.config([self.member()])
        self.unset_local()
        _, env, *_ = self.check('--no-host', '--name', 'Ana Teste', '--email', 'Ana@Example.Test')
        self.assertEqual(env['status'], 'IDENTIFIED_APPROVED')
        self.assertEqual(env['data']['email'], 'ana@example.test')
        self.assertEqual(run(['git', '-C', str(self.repo), 'config', '--local', '--get', 'user.email'],
                             check=False).returncode, 1)

    def test_set_local_git_identity_never_global(self):
        self.config([self.member()])
        self.unset_local()
        _, env, *_ = self.check('--no-host', '--name', 'Ana Teste', '--email', 'ana@example.test',
                                '--set-local-git-identity')
        self.assertTrue(env['data']['localIdentitySet'])
        local = run(['git', '-C', str(self.repo), 'config', '--local', '--get', 'user.email']).stdout.strip()
        self.assertEqual(local, 'ana@example.test')
        self.assertNotIn('ana@example.test', self.gcfg.read_text())

    def test_global_fallback(self):
        self.config([self.member()])
        self.unset_local()
        run(['git', 'config', '--file', str(self.gcfg), 'user.name', 'Ana Teste'])
        run(['git', 'config', '--file', str(self.gcfg), 'user.email', 'ana@example.test'])
        _, env, *_ = self.check('--no-host')
        self.assertEqual(env['status'], 'IDENTIFIED_APPROVED')

    def test_signed_commits_warning(self):
        self.config([self.member()], policy={'promoters': 'listed', 'requireSignedCommits': True,
                                             'pendingExpiryDays': 7})
        _, env, *_ = self.check('--no-host')
        self.assertIn('UNSIGNED_COMMITS_REQUIRED', [p['code'] for p in env['problems']])
        run(['git', '-C', str(self.repo), 'config', 'commit.gpgsign', 'true'])
        _, env, *_ = self.check('--no-host')
        self.assertNotIn('UNSIGNED_COMMITS_REQUIRED', [p['code'] for p in env['problems']])


class TestHostLayer(IdentityBase):
    def set_remote(self, url):
        run(['git', '-C', str(self.repo), 'remote', 'set-url', 'origin', url])

    def test_no_signal_is_git_only(self):
        self.config([self.member()])
        _, env, *_ = self.check()
        self.assertEqual((env['data']['evidence'], env['data']['detectedHostLogin']), ('git-only', None))

    def test_gh_login_is_host_verified(self):
        self.add_tool('gh', FAKE_GH)
        self.set_remote('https://github.example.test/org/repo.git')
        self.config([self.member(hostLogin='ana-gh')])
        _, env, *_ = self.check()
        self.assertEqual((env['status'], env['data']['evidence'], env['data']['detectedHostLogin']),
                         ('IDENTIFIED_APPROVED', 'host-verified', 'ana-gh'))

    def test_gh_not_authenticated_is_git_only(self):
        self.add_tool('gh', FAKE_GH)
        self.set_remote('https://github.example.test/org/repo.git')
        self.config([self.member()])
        with mock.patch.dict(os.environ, {'FAKE_GH_AUTH': 'fail'}):
            _, env, *_ = self.check()
        self.assertEqual(env['data']['evidence'], 'git-only')

    def test_no_host_flag_skips_gh(self):
        self.add_tool('gh', FAKE_GH)
        self.set_remote('https://github.example.test/org/repo.git')
        self.config([self.member()])
        _, env, *_ = self.check('--no-host')
        self.assertEqual((env['data']['evidence'], env['data']['detectedHostLogin']), ('git-only', None))

    def test_glab_login(self):
        self.add_tool('glab', '#!/bin/sh\n[ "$1" = "api" ] && echo \'{"username":"ana-gl"}\' && exit 0\nexit 1\n')
        self.set_remote('https://gitlab.example.test/org/repo.git')
        self.config([self.member()])
        _, env, *_ = self.check()
        self.assertEqual(env['data']['detectedHostLogin'], 'ana-gl')

    def test_mismatch_with_roster_host_login(self):
        self.add_tool('gh', FAKE_GH)
        self.set_remote('https://github.example.test/org/repo.git')
        self.config([self.member(hostLogin='outra-pessoa')])
        code, env, *_ = self.check()
        self.assertEqual((code, env['status'], env['data']['mode']), (1, 'MISMATCH', 'consult'))
        self.assertFalse(env['data']['canPromote'])

    def test_url_user_is_signal_and_password_never_printed(self):
        self.set_remote('https://ana-url:s3cr3t-pass@git.example.test/org/repo.git')
        self.config([self.member()])
        _, env, out, err = self.check()
        self.assertEqual((env['data']['evidence'], env['data']['detectedHostLogin']), ('host-verified', 'ana-url'))
        self.assertNotIn('s3cr3t-pass', out + err)

    def test_token_as_url_user_is_ignored_and_not_printed(self):
        token = 'ghp_' + 'a1B2c3D4' * 4
        self.set_remote(f'https://{token}@git.example.test/org/repo.git')
        self.config([self.member()])
        _, env, out, err = self.check()
        self.assertEqual(env['data']['evidence'], 'git-only')
        self.assertNotIn(token, out + err)

    def test_ssh_remote_gives_no_signal(self):
        self.set_remote('git@git.example.test:org/repo.git')
        self.config([self.member()])
        _, env, *_ = self.check()
        self.assertEqual(env['data']['evidence'], 'git-only')


class TestRegister(IdentityBase):
    def test_register_unknown_creates_pending_member(self):
        self.config([self.member('outra@example.test')])
        write(self.repo / 'a.txt', 'x')
        sha = commit_all(self.repo, 'init')
        code, env, *_ = self.check('--no-host', '--register', '--name', 'Beto Teste', '--email', 'Beto@Example.Test')
        self.assertEqual((code, env['status'], env['data']['registered'], env['data']['mode']),
                         (0, 'IDENTIFIED_PENDING', True, 'edit-limited'))
        m = self.saved_members()[1]
        self.assertEqual((m['email'], m['name'], m['status'], m['roles'], m['profile']),
                         ('beto@example.test', 'Beto Teste', 'pending', ['contributor'], 'product'))
        self.assertEqual(m['identityEvidence'], 'git-only')
        self.assertEqual(m['statusChangedAtCommit'], sha)
        self.assertEqual(m['registeredAt'], m['statusChangedAt'])
        h = m['statusHistory'][0]
        self.assertEqual((h['status'], h['by'], h['commit']), ('pending', 'self', sha))

    def test_register_without_commits_uses_null(self):
        self.config([])
        self.check('--no-host', '--register')
        self.assertIsNone(self.saved_members()[0]['statusChangedAtCommit'])

    def test_register_is_idempotent(self):
        self.config([])
        self.check('--no-host', '--register')
        code, env, *_ = self.check('--no-host', '--register')
        self.assertEqual((code, env['status'], env['data']['registered']), (0, 'IDENTIFIED_PENDING', False))
        self.assertEqual(len(self.saved_members()), 1)

    def test_register_does_not_duplicate_existing_any_status(self):
        for status, expected in (('approved', 'IDENTIFIED_APPROVED'), ('rejected', 'REJECTED'),
                                 ('revoked', 'REVOKED')):
            with self.subTest(status):
                self.config([self.member('ANA@example.test', status=status)])
                _, env, *_ = self.check('--no-host', '--register')
                self.assertEqual(env['status'], expected)
                self.assertFalse(env['data']['registered'])
                self.assertEqual(len(self.saved_members()), 1)
                self.assertEqual(self.saved_members()[0]['status'], status)

    def test_register_without_flag_does_not_write(self):
        self.config([])
        self.check('--no-host')
        self.assertEqual(self.saved_members(), [])

    def test_register_stores_host_evidence(self):
        self.add_tool('gh', FAKE_GH)
        run(['git', '-C', str(self.repo), 'remote', 'set-url', 'origin', 'https://github.example.test/o/r.git'])
        self.config([])
        self.check('--register')
        m = self.saved_members()[0]
        self.assertEqual((m['identityEvidence'], m['hostLogin']), ('host-verified', 'ana-gh'))

    def test_register_requires_identity(self):
        self.config([])
        run(['git', '-C', str(self.repo), 'config', '--unset', 'user.email'])
        code, env, *_ = self.check('--no-host', '--register')
        self.assertEqual((code, env['status']), (1, 'NO_IDENTITY'))
        self.assertEqual(self.saved_members(), [])


if __name__ == '__main__':
    unittest.main()
