import unittest

from group_fixtures import (ANA, BIA, CAIO, EDU, SCREEN_A, add_pending, commit_body, git_out, make_group_repo,
                            member_clone, remote_entries, remote_file, remote_sha)
from helpers import TmpDirMixin, run, run_script, write

import protolib

PROMOTE = 'group-promote.py'
SHARE = 'group-share.py'


def promote(repo, user, *extra):
    return run_script(PROMOTE, '--repo', repo, '--actor-email', user[1], *extra)


def share(repo, user, *extra):
    code, env, out, err = run_script(SHARE, '--repo', repo, '--actor-email', user[1], '--execute',
                                     '--vetting-done', *extra)
    assert code == 0, out + err
    return env


def remote_is_ancestor(remote, a, b):
    return run(['git', '--git-dir', str(remote), 'merge-base', '--is-ancestor', a, b], check=False).returncode == 0


class PromoteBase(TmpDirMixin):
    def setUp(self):
        super().setUp()
        self.origin_repo, self.remote = make_group_repo(self.tmp)
        self.a = member_clone(self.remote, self.tmp, ANA)
        self.b = member_clone(self.remote, self.tmp, BIA)

    def share_screen_edit(self, repo, user, text, line):
        p = repo / 'js/screens/a.js'
        write(p, p.read_text(encoding='utf-8').replace("'titulo original'", text))
        add_pending(repo, line)
        return share(repo, user)

    def share_new_screen(self, repo, user, name, line):
        write(repo / f'js/screens/{name}.js', f'// tela {name}\n')
        add_pending(repo, line)
        return share(repo, user)


class Plan(PromoteBase, unittest.TestCase):
    def test_contributor_cannot_promote(self):
        code, env, _, _ = promote(self.b, BIA)
        self.assertEqual((code, env['status']), (1, 'NOT_PROMOTER'))

    def test_dry_run_groups_by_actor_flags_pending_and_writes_nothing(self):
        self.share_screen_edit(self.a, ANA, "'titulo da ana'", 'Título da Ana.')
        self.share_new_screen(self.b, BIA, 'nova-b', 'Tela nova da Bia.')
        c = member_clone(self.remote, self.tmp, CAIO)
        self.share_new_screen(c, CAIO, 'nova-c', 'Tela nova do Caio.')
        run(['git', '-C', str(self.a), 'fetch', '-q', 'origin'])
        before = git_out(self.a, 'for-each-ref'), remote_sha(self.remote, 'main')
        code, env, out, err = promote(self.a, ANA)
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'), out + err)
        d = env['data']
        self.assertEqual(d['version'], 'v1.1.0')
        self.assertEqual(d['plan']['bumpLevel'], 'minor')
        actors = {g['actor']: g for g in d['willReachClient']['byActor']}
        self.assertEqual(set(actors), {ANA[1], BIA[1], CAIO[1]})
        self.assertEqual(actors[CAIO[1]]['memberStatus'], 'pending')
        self.assertEqual(actors[BIA[1]]['identityEvidence'], 'git-only')
        self.assertEqual(d['willReachClient']['pendingMembers'], [{'email': CAIO[1], 'status': 'pending'}])
        self.assertNotIn('extraConfirmation', d)
        self.assertEqual(before, (git_out(self.a, 'for-each-ref'), remote_sha(self.remote, 'main')))

    def test_auto_bump_is_patch_without_new_screen_and_git_only_promoter_needs_extra_confirmation(self):
        self.share_screen_edit(self.b, BIA, "'ajuste'", 'Ajuste de texto.')
        e = member_clone(self.remote, self.tmp, EDU)
        code, env, _, _ = promote(e, EDU)
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['version'], 'v1.0.1')
        self.assertTrue(env['data']['extraConfirmation'])

    def test_nothing_to_promote(self):
        code, env, _, _ = promote(self.a, ANA)
        self.assertEqual((code, env['status']), (1, 'NOTHING_TO_PROMOTE'))


class Execute(PromoteBase, unittest.TestCase):
    def test_promotion_consolidates_betas_fast_forwards_official_and_restarts_beta_numbering(self):
        self.share_screen_edit(self.a, ANA, "'titulo da ana'", 'Título da Ana.')
        self.share_new_screen(self.b, BIA, 'nova-b', 'Tela nova da Bia.')
        run(['git', '-C', str(self.a), 'fetch', '-q', 'origin'])
        beta_before = remote_sha(self.remote, 'beta')
        code, env, out, err = promote(self.a, ANA, '--execute')
        self.assertEqual((code, env['status']), (0, 'PROMOTED'), out + err)
        d = env['data']
        self.assertEqual(d['version'], 'v1.1.0')
        self.assertEqual(remote_sha(self.remote, 'main'), remote_sha(self.remote, 'beta'))
        self.assertEqual(remote_sha(self.remote, 'main'), d['officialSha'])
        self.assertTrue(remote_is_ancestor(self.remote, beta_before, 'main'))
        self.assertEqual({a['kind'] for a in d['artifactsToUpdate']}, {'official', 'beta'})
        entries = remote_entries(self.remote, 'main')
        self.assertEqual([(e['version'], e['changes']) for e in entries],
                         [('v1.1.0', ['Tela nova da Bia.', 'Título da Ana.']), ('v1.0.0', ['Primeira versão oficial.'])])
        self.assertIn('v1.1.0 · protótipo', remote_file(self.remote, 'main', 'index.html'))
        tr = protolib.parse_trailers(commit_body(self.remote, 'main'))
        self.assertEqual(tr[protolib.T_PROMOTION], 'v1.1.0')
        self.assertEqual(tr[protolib.T_ACTOR], ANA[1])
        self.assertEqual(git_out(self.a, 'status', '--porcelain'), '')
        nxt = self.share_screen_edit(self.b, BIA, "'depois'", 'Depois da promoção.')
        self.assertEqual(nxt['data']['version'], 'v1.1.0-beta.1')

    def test_dirty_worktree_is_refused(self):
        self.share_screen_edit(self.b, BIA, "'x'", 'x')
        write(self.a / 'index.html', 'sujo')
        code, env, _, _ = promote(self.a, ANA, '--execute')
        self.assertEqual((code, env['status']), (1, 'WORKTREE_DIRTY'))

    def test_official_push_failure_is_resumed_without_new_version(self):
        self.share_screen_edit(self.b, BIA, "'x'", 'Ajuste.')
        hook = self.remote / 'hooks' / 'update'
        write(hook, '#!/bin/sh\n[ "$1" = "refs/heads/main" ] && exit 1\nexit 0\n')
        hook.chmod(0o755)
        code, env, out, err = promote(self.a, ANA, '--execute')
        self.assertEqual((code, env['status']), (1, 'PUSH_REJECTED'), out + err)
        hook.unlink()
        code, env, out, err = promote(self.a, ANA, '--execute')
        self.assertEqual((code, env['status']), (0, 'RESUMED'), out + err)
        self.assertEqual(env['data']['version'], 'v1.0.1')
        self.assertEqual(remote_sha(self.remote, 'main'), remote_sha(self.remote, 'beta'))


class Urgent(PromoteBase, unittest.TestCase):
    def test_new_screen_is_not_urgent_sized(self):
        write(self.a / 'js/screens/grande.js', '// tela nova\n')
        add_pending(self.a, 'Tela nova.')
        run_script(SHARE, '--repo', self.a, '--actor-email', ANA[1], '--mode', 'save-only', '--execute', '--vetting-done')
        code, env, _, _ = promote(self.a, ANA, '--urgent')
        self.assertEqual((code, env['status']), (1, 'NOT_URGENT_SIZED'))

    def test_urgent_fix_goes_to_official_and_is_integrated_into_beta(self):
        self.share_new_screen(self.b, BIA, 'nova-b', 'Tela nova da Bia (ainda não aprovada).')
        run(['git', '-C', str(self.a), 'fetch', '-q', 'origin'])
        run(['git', '-C', str(self.a), 'checkout', '-q', '-b', 'draft/ana', 'origin/main'])
        p = self.a / 'js/screens/a.js'
        write(p, p.read_text(encoding='utf-8').replace("'titulo original'", "'titulo corrigido'"))
        add_pending(self.a, 'Corrige o título da tela A.')
        code, env, out, err = run_script(SHARE, '--repo', self.a, '--actor-email', ANA[1], '--mode', 'save-only', '--vetting-done',
                                         '--execute')
        self.assertEqual(code, 0, out + err)
        code, env, out, err = promote(self.a, ANA, '--urgent', '--execute')
        self.assertEqual((code, env['status']), (0, 'PROMOTED_URGENT'), out + err)
        self.assertEqual(env['data']['version'], 'v1.0.1')
        self.assertIn('titulo corrigido', remote_file(self.remote, 'main', 'js/screens/a.js'))
        self.assertNotIn('nova-b.js', git_out(self.a, 'ls-tree', '-r', '--name-only', 'origin/main'))
        main_entries = remote_entries(self.remote, 'main')
        self.assertEqual(main_entries[0], {'version': 'v1.0.1', 'date': main_entries[0]['date'],
                                           'changes': ['Corrige o título da tela A.']})
        self.assertEqual(protolib.parse_trailers(commit_body(self.remote, 'main'))[protolib.T_PROMOTION], 'v1.0.1')
        self.assertTrue(remote_is_ancestor(self.remote, 'main', 'beta'))
        self.assertEqual(env['data']['betaVersion'], 'v1.0.1-beta.1')
        self.assertIn('v1.0.1-beta.1 · protótipo', remote_file(self.remote, 'beta', 'index.html'))
        self.assertIn('titulo corrigido', remote_file(self.remote, 'beta', 'js/screens/a.js'))
        self.assertTrue(remote_file(self.remote, 'beta', 'js/screens/nova-b.js'))
        self.assertEqual(git_out(self.a, 'rev-parse', '--abbrev-ref', 'HEAD'), 'draft/ana')
        self.assertEqual(git_out(self.a, 'branch', '--list', 'hotfix/*'), '')


class Restore(PromoteBase, unittest.TestCase):
    def test_restore_previous_version_as_new_version_without_rewriting_history(self):
        self.share_new_screen(self.b, BIA, 'nova-b', 'Tela nova da Bia.')
        self.share_screen_edit(self.b, BIA, "'mudado'", 'Muda o título.')
        self.assertEqual(promote(self.a, ANA, '--execute')[0], 0)
        promoted = remote_sha(self.remote, 'main')
        run(['git', '-C', str(self.a), 'fetch', '-q', 'origin'])
        code, env, out, err = promote(self.a, ANA, '--restore-version', 'v1.0.0')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'), out + err)
        self.assertEqual(env['data']['version'], 'v1.1.1')
        self.assertIn('js/screens/nova-b.js', env['data']['willReachClient']['files'])
        code, env, out, err = promote(self.a, ANA, '--restore-version', 'v1.0.0', '--execute',
                                      '--reason', 'cliente pediu a versão anterior')
        self.assertEqual((code, env['status']), (0, 'RESTORED'), out + err)
        self.assertEqual(remote_file(self.remote, 'main', 'js/screens/a.js'), SCREEN_A)
        self.assertNotIn('nova-b.js', git_out(self.a, 'ls-tree', '-r', '--name-only', 'origin/main'))
        self.assertTrue(remote_is_ancestor(self.remote, promoted, 'main'))
        entries = remote_entries(self.remote, 'main')
        self.assertEqual([e['version'] for e in entries], ['v1.1.1', 'v1.1.0', 'v1.0.0'])
        self.assertIn('v1.1.1 · protótipo', remote_file(self.remote, 'main', 'index.html'))
        restore_tr = protolib.parse_trailers(commit_body(self.remote, 'main~1'))
        self.assertTrue(restore_tr[protolib.T_ROLLBACK_OF])
        self.assertEqual(restore_tr[protolib.T_ROLLBACK_REASON], 'cliente pediu a versão anterior')

    def test_unknown_version_is_reported(self):
        code, env, _, _ = promote(self.a, ANA, '--restore-version', 'v9.9.9')
        self.assertEqual((code, env['status']), (1, 'VERSION_NOT_FOUND'))


if __name__ == '__main__':
    unittest.main()
