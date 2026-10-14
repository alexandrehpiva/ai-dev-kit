import json
import unittest
from pathlib import Path

from group_fixtures import ANA, BIA, CAIO, DANI, git_out, make_group_repo, member_clone, remote_sha
from helpers import TmpDirMixin, run, run_script, write

import protolib

PREVIEW = 'group-preview.py'
ARTIFACTS = 'artifacts.py'


def preview(repo, user, *extra):
    return run_script(PREVIEW, '--repo', repo, '--actor-email', user[1], *extra)


class PreviewBase(TmpDirMixin):
    def setUp(self):
        super().setUp()
        self.origin_repo, self.remote = make_group_repo(self.tmp)
        self.b = member_clone(self.remote, self.tmp, BIA)
        self.branch = 'preview/bia/opcao-a'

    def work(self):
        write(self.b / 'js/screens/a.js', "// tela A\nfunction telaA(){\n  return 'titulo da opcao A';\n}\n")
        write(self.b / 'js/screens/nova.js', '// arquivo novo, ainda sem add\n')
        write(self.b / 'dist/index.html', '<html>gerado</html>')

    def state(self):
        return (git_out(self.b, 'status', '--porcelain'), git_out(self.b, 'rev-parse', 'HEAD'),
                git_out(self.b, 'branch', '--show-current'), git_out(self.b, 'stash', 'list'))


class Snapshot(PreviewBase, unittest.TestCase):
    def test_given_dry_run_then_nothing_is_written(self):
        self.work()
        before = (self.state(), git_out(self.b, 'for-each-ref'))
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'DRY_RUN')
        self.assertEqual(env['data']['branch'], self.branch)
        self.assertEqual((self.state(), git_out(self.b, 'for-each-ref')), before)
        self.assertIsNone(remote_sha(self.remote, f'refs/heads/{self.branch}'))

    def test_given_working_tree_when_executed_then_branch_has_changes_untracked_and_no_dist(self):
        self.work()
        before = self.state()
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'SNAPSHOT')
        self.assertTrue(env['data']['pushed'])
        sha = remote_sha(self.remote, f'refs/heads/{self.branch}')
        self.assertEqual(sha, env['data']['sha'])
        self.assertEqual(env['data']['sourceRef'], f'{self.branch}@{sha[:7]}')
        files = run(['git', '--git-dir', str(self.remote), 'ls-tree', '-r', '--name-only', sha]).stdout.split()
        self.assertIn('js/screens/nova.js', files)
        self.assertNotIn('dist/index.html', files)
        shown = run(['git', '--git-dir', str(self.remote), 'show', f'{sha}:js/screens/a.js']).stdout
        self.assertIn('titulo da opcao A', shown)
        self.assertEqual(self.state(), before)  # trabalho, branch atual, índice e stash intactos

    def test_given_executed_then_commit_carries_trailers_and_parent_is_head(self):
        self.work()
        head = git_out(self.b, 'rev-parse', 'HEAD')
        preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        body = run(['git', '--git-dir', str(self.remote), 'log', '-1', '--format=%B', f'refs/heads/{self.branch}']).stdout
        trailers = protolib.parse_trailers(body)
        self.assertEqual(trailers[protolib.T_ACTOR], BIA[1])
        self.assertEqual(trailers['Prototype-Preview'], 'opcao-a')
        self.assertEqual(trailers['Prototype-Preview-Source'], 'working')
        self.assertEqual(trailers['Prototype-Preview-Base'], head)
        parents = run(['git', '--git-dir', str(self.remote), 'log', '-1', '--format=%P', f'refs/heads/{self.branch}']).stdout.split()
        self.assertEqual(parents, [head])

    def test_given_same_work_twice_then_no_new_commit(self):
        self.work()
        _, first, _, _ = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'SNAPSHOT_UNCHANGED')
        self.assertEqual(env['data']['sha'], first['data']['sha'])

    def test_given_more_work_then_new_commit_on_top_without_rewriting(self):
        self.work()
        _, first, _, _ = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        write(self.b / 'js/screens/nova.js', '// agora mudou\n')
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'SNAPSHOT')
        parents = run(['git', '--git-dir', str(self.remote), 'log', '-1', '--format=%P', f'refs/heads/{self.branch}']).stdout.split()
        self.assertEqual(parents, [first['data']['sha']])

    def test_given_clean_tree_then_nothing_to_snapshot(self):
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        self.assertEqual(env['status'], 'NOTHING_TO_SNAPSHOT')
        self.assertIsNone(remote_sha(self.remote, f'refs/heads/{self.branch}'))

    def test_given_stash_then_snapshot_includes_untracked_and_leaves_stash(self):
        self.work()
        run(['git', '-C', str(self.b), 'stash', 'push', '-u', '-q', '-m', 'variante'])
        before = git_out(self.b, 'stash', 'list')
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-b', '--source', 'stash@{0}', '--execute')
        self.assertEqual(code, 0, err + out)
        sha = remote_sha(self.remote, 'refs/heads/preview/bia/opcao-b')
        files = run(['git', '--git-dir', str(self.remote), 'ls-tree', '-r', '--name-only', sha]).stdout.split()
        self.assertIn('js/screens/nova.js', files)
        self.assertNotIn('dist/index.html', files)
        shown = run(['git', '--git-dir', str(self.remote), 'show', f'{sha}:js/screens/a.js']).stdout
        self.assertIn('titulo da opcao A', shown)
        self.assertEqual(git_out(self.b, 'stash', 'list'), before)

    def test_given_offline_remote_then_local_commit_and_not_synced(self):
        self.work()
        run(['git', '-C', str(self.b), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        code, env, out, err = preview(self.b, BIA, '--id', 'opcao-a', '--execute')
        self.assertEqual(code, 1)
        self.assertEqual(env['status'], 'NOT_SYNCED')
        self.assertFalse(env['data']['pushed'])
        self.assertTrue(git_out(self.b, 'rev-parse', f'refs/heads/{self.branch}'))


class Refusals(PreviewBase, unittest.TestCase):
    def test_given_bad_id_then_refused(self):
        code, env, _, _ = preview(self.b, BIA, '--id', 'Opção A!', '--execute')
        self.assertEqual(env['status'], 'BAD_ID')

    def test_given_other_source_then_refused(self):
        code, env, _, _ = preview(self.b, BIA, '--id', 'x', '--source', 'main', '--execute')
        self.assertEqual(env['status'], 'BAD_SOURCE')

    def test_given_rejected_member_then_not_allowed(self):
        dani = member_clone(self.remote, self.tmp, DANI)
        write(dani / 'js/screens/nova.js', 'x')
        code, env, _, _ = preview(dani, DANI, '--id', 'x', '--execute')
        self.assertEqual(env['status'], 'NOT_ALLOWED')

    def test_given_pending_member_then_allowed(self):
        caio = member_clone(self.remote, self.tmp, CAIO)
        write(caio / 'js/screens/nova.js', 'x')
        code, env, out, err = preview(caio, CAIO, '--id', 'x', '--execute')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'SNAPSHOT')

    def test_given_missing_config_then_invalid(self):
        (self.b / protolib.CONFIG_NAME).unlink()
        code, env, _, _ = preview(self.b, BIA, '--id', 'x', '--execute')
        self.assertEqual(env['status'], 'INVALID_CONFIG')


class Audit(PreviewBase, unittest.TestCase):
    def test_given_clean_repo_then_safe(self):
        code, env, out, err = preview(self.b, BIA, '--mode', 'audit')
        self.assertEqual(code, 0, err + out)
        self.assertEqual(env['status'], 'SAFE')

    def test_given_uncommitted_stash_and_unpushed_then_at_risk(self):
        self.work()
        run(['git', '-C', str(self.b), 'stash', 'push', '-u', '-q', '-m', 'v'])
        write(self.b / 'js/screens/nova.js', 'sem commit')
        run(['git', '-C', str(self.b), 'checkout', '-q', '-b', 'draft/bia'])
        write(self.b / 'js/screens/outra.js', 'commit local')
        run(['git', '-C', str(self.b), 'add', '-A'])
        run(['git', '-C', str(self.b), 'commit', '-q', '-m', 'local'])
        write(self.b / 'js/screens/solta.js', 'solta')
        code, env, _, _ = preview(self.b, BIA, '--mode', 'audit')
        codes = {p['code'] for p in env['problems']}
        self.assertEqual(env['status'], 'AT_RISK')
        self.assertTrue({'UNSAVED_WORK', 'STASHED_WORK', 'UNPUSHED_BRANCH'} <= codes, codes)

    def test_given_preview_without_branch_then_flagged_and_after_snapshot_safe(self):
        cfg = json.loads((self.b / protolib.CONFIG_NAME).read_text())
        cfg['artifacts'].append({'id': 'p1', 'kind': 'preview', 'branch': None, 'delivery': 'claude-artifact',
                                 'url': 'https://example.test/a', 'owner': BIA[1], 'version': None, 'status': 'current',
                                 'pendingVersion': None, 'publishedAt': None, 'publishedBy': None})
        cfg['artifacts'][-1].pop('branch')
        write(self.b / protolib.CONFIG_NAME, json.dumps(cfg, indent=2) + '\n')
        run(['git', '-C', str(self.b), 'add', '-A'])
        run(['git', '-C', str(self.b), 'commit', '-q', '-m', 'registra'])
        run(['git', '-C', str(self.b), 'push', '-q', 'origin', 'main'])
        _, env, _, _ = preview(self.b, BIA, '--mode', 'audit')
        self.assertIn('PREVIEW_WITHOUT_BRANCH', {p['code'] for p in env['problems']})


class UpdateSource(PreviewBase, unittest.TestCase):
    def test_given_preview_artifact_when_update_source_then_branch_and_ref_saved(self):
        reg = run_script(ARTIFACTS, '--repo', self.b, 'register', '--id', 'p1', '--kind', 'preview',
                         '--delivery', 'claude-artifact', '--owner', BIA[1], '--url', 'https://example.test/a')
        self.assertEqual(reg[0], 0, reg[2] + reg[3])
        code, env, out, err = run_script(ARTIFACTS, '--repo', self.b, 'update-source', '--id', 'p1',
                                         '--branch', self.branch, '--source-ref', f'{self.branch}@abc1234')
        self.assertEqual(code, 0, err + out)
        art = env['data']['artifact']
        self.assertEqual((art['branch'], art['sourceRef']), (self.branch, f'{self.branch}@abc1234'))

    def test_given_official_artifact_then_update_source_refused(self):
        code, env, _, _ = run_script(ARTIFACTS, '--repo', self.b, 'update-source', '--id', 'official',
                                     '--branch', 'x', '--source-ref', 'x@1')
        self.assertEqual(code, 1)
        self.assertEqual(env['problems'][0]['code'], 'BAD_KIND')


if __name__ == '__main__':
    unittest.main()
