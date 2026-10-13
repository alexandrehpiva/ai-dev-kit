import json
import unittest

from helpers import TmpDirMixin, run_script, write, make_repo
import protolib as pl


def v2(extra=None):
    cfg = {'skill': {'name': 'interactive-prototype', 'version': '2.0.0'}, 'groupMode': False,
           'remote': 'origin', 'branches': {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'},
           'policy': {'promoters': 'all-members', 'requireSignedCommits': False, 'pendingExpiryDays': 7},
           'docs': {'autoMaintain': False}, 'members': [], 'artifacts': []}
    cfg.update(extra or {})
    return cfg


class GroupSetupTest(TmpDirMixin, unittest.TestCase):
    def repo(self, cfg):
        repo, _ = make_repo(self.tmp)
        write(repo / pl.CONFIG_NAME, json.dumps(cfg))
        return repo

    def test_first_promoter_and_policy(self):
        repo = self.repo(v2())
        code, env, *_ = run_script('group-setup.py', '--repo', repo, '--actor-name', 'Ana', '--actor-email',
                                   'Ana@Example.test', '--promoters-policy', 'listed', '--docs-auto-maintain', 'true')
        self.assertEqual((code, env['status']), (0, 'SETUP_DONE'), env)
        cfg = json.loads((repo / pl.CONFIG_NAME).read_text())
        m = cfg['members'][0]
        self.assertEqual((m['email'], m['status'], m['roles']), ('ana@example.test', 'approved', ['promoter', 'contributor']))
        self.assertEqual(m['statusHistory'][0]['by'], 'setup')
        self.assertEqual(cfg['policy']['promoters'], 'listed')
        self.assertTrue(cfg['docs']['autoMaintain'])
        self.assertFalse(cfg['groupMode'])

    def test_idempotent(self):
        repo = self.repo(v2())
        args = ('--repo', repo, '--actor-name', 'Ana', '--actor-email', 'ana@example.test')
        run_script('group-setup.py', *args)
        code, env, *_ = run_script('group-setup.py', *args)
        self.assertEqual((code, env['status']), (0, 'NOTHING_TO_DO'))
        self.assertEqual(len(json.loads((repo / pl.CONFIG_NAME).read_text())['members']), 1)

    def test_legacy_config_needs_migration(self):
        repo = self.repo({'groupMode': False, 'sharedBranch': 'main', 'remote': 'origin'})
        code, env, *_ = run_script('group-setup.py', '--repo', repo, '--actor-name', 'Ana', '--actor-email', 'a@example.test')
        self.assertEqual((code, env['status']), (1, 'NEEDS_MIGRATION'))


if __name__ == '__main__':
    unittest.main()
