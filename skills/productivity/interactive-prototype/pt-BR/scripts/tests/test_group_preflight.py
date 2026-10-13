"""Testes de group-preflight.py (remoto bare local; gh simulado em PATH isolado; sem rede)."""

import json
import os
import shutil
import stat
import unittest
from unittest import mock

from helpers import TmpDirMixin, clone, commit_all, make_repo, run, run_script, write

FAKE_GH = """#!/bin/sh
if [ "$1" = "api" ]; then
  case "$FAKE_GH_PROTECTION" in
    ok) echo '{}'; exit 0 ;;
    none) echo 'gh: Branch not protected (HTTP 404)' >&2; exit 1 ;;
    *) echo 'gh: Not Found (HTTP 404)' >&2; exit 1 ;;
  esac
fi
exit 1
"""

PROMOTION = 'promove\n\nPrototype-Promotion: v1.0.0\n'


class PreflightBase(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        git_real = shutil.which('git')
        self.add_tool('git', f'#!/bin/sh\nexec "{git_real}" "$@"\n')
        gcfg = self.tmp / 'global.gitconfig'
        gcfg.write_text('')
        patcher = mock.patch.dict(os.environ, {'PATH': str(self.bin), 'GIT_CONFIG_GLOBAL': str(gcfg),
                                               'GIT_CONFIG_NOSYSTEM': '1'})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo, self.remote = make_repo(self.tmp)
        write(self.repo / 'index.html', 'v0')
        self.base = commit_all(self.repo, 'inicio')
        run(['git', '-C', str(self.repo), 'push', '-q', 'origin', 'main'])

    def add_tool(self, name, body):
        p = self.bin / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def write_cfg(self, **cfg):
        write(self.repo / 'prototype.config.json', json.dumps(cfg))

    def v2(self, **extra):
        cfg = {'skill': {'name': 'interactive-prototype', 'version': '2.0.0'}, 'groupMode': True,
               'remote': 'origin', 'branches': {'official': 'main', 'beta': 'beta',
                                                'draftPattern': 'draft/{member}'},
               'members': [{'email': 'ana@example.test'}], 'docs': {'autoMaintain': False}}
        cfg.update(extra)
        self.write_cfg(**cfg)

    def push_beta(self):
        run(['git', '-C', str(self.repo), 'push', '-q', 'origin', 'main:refs/heads/beta'])

    def pf(self, *args):
        return run_script('group-preflight.py', '--repo', self.repo, *args)

    def remote_heads(self):
        out = run(['git', 'ls-remote', '--heads', str(self.remote)]).stdout
        return {l.split('\t')[1][len('refs/heads/'):]: l.split('\t')[0] for l in out.splitlines()}

    def cfg(self):
        return json.loads((self.repo / 'prototype.config.json').read_text())

    @staticmethod
    def codes(env):
        return {p['code'] for p in env['problems']}


class TestLegacyV1(PreflightBase):
    def test_v1_human_output_and_exit_zero(self):
        self.write_cfg(groupMode=True, sharedBranch='main', remote='origin')
        code, env, out, _ = self.pf()
        self.assertEqual(code, 0, out)
        self.assertIsNone(env)
        for needle in ('repositório git', 'remoto "origin" configurado', 'remoto alcançável',
                       'branch compartilhada "main" existe no remoto', 'acesso de push conferido'):
            self.assertIn(needle, out)
        self.assertNotIn('beta', out)

    def test_v1_disabled_does_nothing(self):
        self.write_cfg(groupMode=False, sharedBranch='main')
        code, _, out, _ = self.pf()
        self.assertEqual(code, 0)
        self.assertIn('desligado', out)

    def test_v1_force_check_without_config(self):
        code, _, out, _ = self.pf('--force-check')
        self.assertEqual(code, 0, out)

    def test_v1_missing_branch_fails(self):
        self.write_cfg(groupMode=True, sharedBranch='release', remote='origin')
        code, _, out, _ = self.pf()
        self.assertEqual(code, 1)
        self.assertIn('FALHA', out)
        self.assertIn('"release" não existe no remoto', out)

    def test_v1_enable_preserves_other_keys(self):
        self.write_cfg(groupMode=False, sharedBranch='main', remote='origin', extra={'k': 1})
        code, _, out, _ = self.pf('--enable')
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cfg(), {'groupMode': True, 'sharedBranch': 'main', 'remote': 'origin',
                                      'extra': {'k': 1}})

    def test_enable_failure_does_not_write(self):
        self.write_cfg(groupMode=False, sharedBranch='release')
        code, _, out, _ = self.pf('--enable')
        self.assertEqual(code, 1)
        self.assertIn('NÃO ativado', out)
        self.assertFalse(self.cfg()['groupMode'])


class TestV2Branches(PreflightBase):
    def test_missing_beta_fails_with_instruction(self):
        self.v2()
        code, env, out, _ = self.pf('--json')
        self.assertEqual((code, env['status']), (1, 'NOT_READY'))
        self.assertIn('BETA_BRANCH_MISSING', self.codes(env))
        self.assertIn('--create-beta', next(p['message'] for p in env['problems']))
        self.assertNotIn('beta', self.remote_heads())

    def test_missing_beta_human(self):
        self.v2()
        code, _, out, _ = self.pf()
        self.assertEqual(code, 1)
        self.assertIn('FALHA', out)
        self.assertIn('--create-beta', out)

    def test_create_beta_from_official(self):
        self.v2()
        code, env, out, _ = self.pf('--json', '--create-beta')
        self.assertEqual(code, 0, out)
        self.assertEqual(self.remote_heads()['beta'], self.base)
        self.assertIn('BETA_CREATED', [c['code'] for c in env['data']['checks']])
        local = run(['git', '-C', str(self.repo), 'rev-parse', 'refs/heads/beta']).stdout.strip()
        self.assertEqual(local, self.base)

    def test_create_beta_not_needed_when_it_exists(self):
        self.v2()
        self.push_beta()
        before = self.remote_heads()
        code, env, *_ = self.pf('--json', '--create-beta')
        self.assertEqual(code, 0)
        self.assertEqual(self.remote_heads(), before)
        self.assertNotIn('BETA_CREATED', [c['code'] for c in env['data']['checks']])

    def test_create_beta_never_rewrites_existing_beta(self):
        self.v2()
        self.push_beta()
        other = clone(self.remote, self.tmp / 'other', ('Beto', 'beto@example.test'))
        run(['git', '-C', str(other), 'checkout', '-q', '-b', 'beta', 'origin/beta'])
        write(other / 'x.txt', 'beta')
        tip = commit_all(other, 'na beta')
        run(['git', '-C', str(other), 'push', '-q', 'origin', 'beta'])
        self.pf('--create-beta')
        self.assertEqual(self.remote_heads()['beta'], tip)

    def test_official_missing_on_remote(self):
        self.v2(branches={'official': 'trunk', 'beta': 'beta', 'draftPattern': 'draft/{member}'})
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 1)
        self.assertIn('OFFICIAL_BRANCH_MISSING', self.codes(env))

    def test_remote_unreachable(self):
        self.v2()
        run(['git', '-C', str(self.repo), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 1)
        self.assertIn('REMOTE_UNREACHABLE', self.codes(env))

    def test_remote_not_configured(self):
        self.v2(remote='upstream')
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 1)
        self.assertIn('REMOTE_NOT_CONFIGURED', self.codes(env))

    def test_ready_envelope(self):
        self.v2()
        self.push_beta()
        code, env, *_ = self.pf('--json')
        self.assertEqual((code, env['ok'], env['status']), (0, True, 'READY'))
        d = env['data']
        self.assertEqual((d['configVersion'], d['official'], d['beta'], d['enabled']), (2, 'main', 'beta', False))
        self.assertEqual(d['anomalies'], [])
        codes = [c['code'] for c in d['checks']]
        for expected in ('REMOTE_REACHABLE', 'OFFICIAL_BRANCH_OK', 'BETA_BRANCH_OK', 'PUSH_OK', 'OFFICIAL_CLEAN'):
            self.assertIn(expected, codes)

    def test_json_disabled(self):
        self.v2(groupMode=False)
        code, env, *_ = self.pf('--json')
        self.assertEqual((code, env['status']), (0, 'DISABLED'))

    def test_json_invalid_config(self):
        write(self.repo / 'prototype.config.json', '{x')
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 1)
        self.assertIn('CONFIG_INVALID', self.codes(env))

    def test_enable_v2_preserves_everything(self):
        self.v2(groupMode=False, members=[{'email': 'ana@example.test', 'roles': ['promoter']}], custom=7)
        self.push_beta()
        before = self.cfg()
        code, env, out, _ = self.pf('--json', '--enable')
        self.assertEqual(code, 0, out)
        self.assertTrue(env['data']['enabled'])
        after = self.cfg()
        self.assertTrue(after.pop('groupMode'))
        before.pop('groupMode')
        self.assertEqual(after, before)
        self.assertNotIn('sharedBranch', after)

    def test_enable_v2_blocked_by_missing_beta(self):
        self.v2(groupMode=False)
        code, env, *_ = self.pf('--json', '--enable')
        self.assertEqual(code, 1)
        self.assertFalse(env['data']['enabled'])
        self.assertFalse(self.cfg()['groupMode'])

    def test_create_beta_then_enable_in_one_run(self):
        self.v2(groupMode=False)
        code, _, out, _ = self.pf('--create-beta', '--enable')
        self.assertEqual(code, 0, out)
        self.assertTrue(self.cfg()['groupMode'])
        self.assertIn('beta', self.remote_heads())


class TestAnomaly(PreflightBase):
    def setUp(self):
        super().setUp()
        self.v2()
        self.push_beta()

    def push_main(self, name, text, message):
        write(self.repo / name, text)
        sha = commit_all(self.repo, message)
        run(['git', '-C', str(self.repo), 'push', '-q', 'origin', 'main'])
        return sha

    def test_no_trailer_no_anomaly(self):
        self.push_main('a.txt', 'a', 'commit solto')
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['anomalies'], [])

    def test_commits_after_last_promotion_are_anomalies(self):
        self.push_main('p.txt', 'p', PROMOTION)
        direct = self.push_main('d.txt', 'd', 'mexe direto na oficial')
        code, env, out, _ = self.pf('--json')
        self.assertEqual(code, 1)
        self.assertIn('OFFICIAL_ANOMALY', self.codes(env))
        [a] = env['data']['anomalies']
        self.assertEqual((a['sha'], a['author'], a['subject']), (direct[:7], 'Ana Teste', 'mexe direto na oficial'))

    def test_human_output_lists_anomaly(self):
        self.push_main('p.txt', 'p', PROMOTION)
        self.push_main('d.txt', 'd', 'mexe direto na oficial')
        code, _, out, _ = self.pf()
        self.assertEqual(code, 1)
        self.assertIn('ANOMALIA', out)
        self.assertIn('Ana Teste', out)
        self.assertIn('mexe direto na oficial', out)

    def test_promotion_tip_is_clean(self):
        self.push_main('x.txt', 'x', 'antes da promoção')
        self.push_main('p.txt', 'p', PROMOTION)
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['anomalies'], [])

    def test_only_latest_promotion_counts(self):
        self.push_main('p1.txt', '1', PROMOTION)
        self.push_main('x.txt', 'x', 'depois da primeira')
        self.push_main('p2.txt', '2', 'promove de novo\n\nPrototype-Promotion: v1.1.0\n')
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['anomalies'], [])

    def test_trailer_text_in_body_is_not_a_promotion(self):
        self.push_main('x.txt', 'x', 'assunto\n\nmenciona Prototype-Promotion: v9 no meio\n\nfim do corpo')
        self.push_main('y.txt', 'y', 'outro')
        code, env, *_ = self.pf('--json')
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['anomalies'], [])

    def test_anomaly_blocks_enable(self):
        cfg = self.cfg()
        cfg['groupMode'] = False
        self.write_cfg(**cfg)
        self.push_main('p.txt', 'p', PROMOTION)
        self.push_main('d.txt', 'd', 'direto')
        code, *_ = self.pf('--enable')
        self.assertEqual(code, 1)
        self.assertFalse(self.cfg()['groupMode'])

    def test_v1_has_no_anomaly_check(self):
        self.write_cfg(groupMode=True, sharedBranch='main', remote='origin')
        self.push_main('p.txt', 'p', PROMOTION)
        self.push_main('d.txt', 'd', 'direto')
        code, _, out, _ = self.pf()
        self.assertEqual(code, 0)
        self.assertNotIn('ANOMALIA', out)


class TestProtection(PreflightBase):
    def setUp(self):
        super().setUp()
        self.v2()
        self.push_beta()

    def use_github_url(self):
        url = 'https://github.example.test/org/repo.git'
        run(['git', '-C', str(self.repo), 'remote', 'set-url', 'origin', url])
        run(['git', '-C', str(self.repo), 'config', f'url.{self.remote}.insteadOf', url])

    def protection(self, env):
        return [c for c in env['data']['checks'] if c['code'].startswith(('PROTECTION', 'BRANCH_UNPROT'))]

    def test_without_gh_is_inconclusive_and_non_blocking(self):
        code, env, out, _ = self.pf('--json')
        self.assertEqual(code, 0, out)
        items = self.protection(env)
        self.assertEqual(len(items), 2)
        self.assertTrue(all(i['status'] == 'INCONCLUSIVO' for i in items))
        self.assertTrue(all('proteger' in i['message'] for i in items))

    def test_human_inconclusive_line(self):
        _, _, out, _ = self.pf()
        self.assertIn('INCONCLUSIVO', out)

    def test_protected_ok(self):
        self.use_github_url()
        self.add_tool('gh', FAKE_GH)
        with mock.patch.dict(os.environ, {'FAKE_GH_PROTECTION': 'ok'}):
            code, env, out, _ = self.pf('--json')
        self.assertEqual(code, 0, out)
        self.assertEqual({i['status'] for i in self.protection(env)}, {'OK'})

    def test_confirmed_unprotected_warns(self):
        self.use_github_url()
        self.add_tool('gh', FAKE_GH)
        with mock.patch.dict(os.environ, {'FAKE_GH_PROTECTION': 'none'}):
            code, env, *_ = self.pf('--json')
        # proteção ausente é aviso, não bloqueio (pode não existir no plano gratuito)
        self.assertEqual(code, 0)
        self.assertIn('BRANCH_UNPROTECTED', self.codes(env))

    def test_no_permission_is_inconclusive(self):
        self.use_github_url()
        self.add_tool('gh', FAKE_GH)
        with mock.patch.dict(os.environ, {'FAKE_GH_PROTECTION': 'denied'}):
            code, env, *_ = self.pf('--json')
        self.assertEqual(code, 0)
        self.assertEqual({i['status'] for i in self.protection(env)}, {'INCONCLUSIVO'})


if __name__ == '__main__':
    unittest.main()
