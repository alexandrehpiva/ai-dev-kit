"""Fluxo ponta a ponta do modo grupo entre scripts: scaffold → setup → beta → compartilhar → vetar → promover."""

import json
import unittest

from helpers import TmpDirMixin, clone, run, run_script
import protolib as pl


def git(repo, *a):
    return run(['git', '-C', str(repo), *a]).stdout.strip()


def ok(test, res, status=None):
    code, env, out, err = res
    test.assertIsNotNone(env, out + err)
    test.assertTrue(env['ok'], out)
    if status:
        test.assertEqual(env['status'], status, out)
    return env


class E2EGroupFlow(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.remote = self.tmp / 'remote.git'
        run(['git', 'init', '-q', '--bare', '-b', 'main', str(self.remote)])
        self.ana = self.tmp / 'ana'
        r = run(['python3', str(pl.skill_root() / 'scripts' / 'scaffold.py'), '--name', 'Demo App', '--out', str(self.ana),
                 '--group-mode'])
        self.assertIn('gerado', r.stdout)
        run(['git', '-C', str(self.ana), 'config', 'user.name', 'Ana'])
        run(['git', '-C', str(self.ana), 'config', 'user.email', 'ana@example.test'])
        run(['git', '-C', str(self.ana), 'config', 'commit.gpgsign', 'false'])
        git(self.ana, 'remote', 'add', 'origin', str(self.remote))
        git(self.ana, 'add', '-A')
        git(self.ana, 'commit', '-qm', 'init')
        git(self.ana, 'push', '-q', 'origin', 'main')
        ok(self, run_script('group-setup.py', '--repo', self.ana, '--actor-name', 'Ana', '--actor-email',
                            'ana@example.test', '--promoters-policy', 'all-members', '--docs-auto-maintain', 'true'))
        git(self.ana, 'add', '-A')
        git(self.ana, 'commit', '-qm', 'setup')
        git(self.ana, 'push', '-q', 'origin', 'main')
        ok(self, run_script('group-preflight.py', '--repo', self.ana, '--force-check', '--create-beta', '--json'))
        ok(self, run_script('group-preflight.py', '--repo', self.ana, '--enable', '--json'))
        # bootstrap: a config com o modo ligado entra nas duas camadas de uma vez (ainda não há promoção)
        git(self.ana, 'add', '-A')
        git(self.ana, 'commit', '-qm', 'chore: ativa modo grupo')
        git(self.ana, 'push', '-q', 'origin', 'main')
        git(self.ana, 'push', '-q', 'origin', 'main:beta')

    def edit_welcome(self, repo, text, name='welcome'):
        p = repo / f'js/screens/shared/{name}.js'
        p.write_text(p.read_text(encoding='utf-8') + f'\n// {text}\n', encoding='utf-8')

    def share(self, repo, email, **kw):
        return run_script('group-share.py', '--repo', repo, '--actor-email', email, '--execute')

    def test_full_cycle(self):
        # Ana (promoter) compartilha o primeiro lote
        self.edit_welcome(self.ana, 'ana')
        env = ok(self, self.share(self.ana, 'ana@example.test'), 'SHARED')
        self.assertEqual(env['data']['version'], 'v0.0.0-beta.1')

        # Bob clona a branch oficial (a cópia de config dele pode estar velha), registra-se e compartilha
        bob = clone(self.remote, self.tmp / 'bob', ('Bob', 'bob@example.test'))
        code, env, *_ = run_script('identity-check.py', '--repo', bob, '--no-host')
        self.assertEqual(env['status'], 'UNKNOWN')
        ok(self, run_script('identity-check.py', '--repo', bob, '--no-host', '--register'), 'IDENTIFIED_PENDING')
        self.edit_welcome(bob, 'bob', 'resultado')
        env = ok(self, self.share(bob, 'bob@example.test'), 'SHARED')
        self.assertEqual(env['data']['version'], 'v0.0.0-beta.2')

        # Ana (promoter) vê a pendência e reprova; o rollback é um commit só na beta
        git(self.ana, 'fetch', '-q')
        git(self.ana, 'checkout', '-q', 'beta')
        git(self.ana, 'merge', '-q', '--ff-only', 'origin/beta')
        vet = ['member-vetting.py', '--repo', self.ana, '--actor-email', 'ana@example.test']
        env = ok(self, run_script(*vet, 'list'))
        self.assertEqual([m['email'] for m in env['data']['pending']], ['bob@example.test'])
        ok(self, run_script(*vet, 'reject', '--email', 'bob@example.test', '--reason', 'teste', '--execute'), 'REJECTED')
        self.assertNotIn('// bob', (self.ana / 'js/screens/shared/resultado.js').read_text(encoding='utf-8'))

        # Reprovado não consegue mais compartilhar (o roster que vale é o da beta no remoto)
        self.edit_welcome(bob, 'bob de novo', 'resultado')
        code, env, out, err = self.share(bob, 'bob@example.test')
        self.assertEqual((code, env['status']), (1, 'NOT_ALLOWED'), out)

        # Reintegração desfaz o rollback
        ok(self, run_script(*vet, 'reinstate', '--email', 'bob@example.test', '--roles', 'contributor', '--execute'))
        self.assertIn('// bob', (self.ana / 'js/screens/shared/resultado.js').read_text(encoding='utf-8'))

        # Promoção: simulação mostra o que vai ao cliente; execução avança a oficial por fast-forward
        prom = ['group-promote.py', '--repo', self.ana, '--actor-email', 'ana@example.test']
        env = ok(self, run_script(*prom), 'DRY_RUN')
        actors = {a['actor'] for a in env['data']['plan']['willReachClient']['byActor']}
        self.assertEqual(actors, {'ana@example.test', 'bob@example.test'})
        env = ok(self, run_script(*prom, '--bump', 'minor', '--execute'), 'PROMOTED')
        self.assertEqual(git(self.ana, 'rev-parse', 'origin/beta'), git(self.ana, 'ls-remote', 'origin', 'main').split()[0])
        self.assertIn(pl.T_PROMOTION, git(self.ana, 'log', '-1', '--format=%B'))

        # Anomalia: commit direto na oficial depois da promoção é apontado pelo preflight
        git(self.ana, 'checkout', '-q', 'main')
        git(self.ana, 'merge', '-q', '--ff-only', 'origin/main')
        self.edit_welcome(self.ana, 'direto na oficial')
        git(self.ana, 'commit', '-qam', 'fora da skill')
        git(self.ana, 'push', '-q', 'origin', 'main')
        code, env, out, err = run_script('group-preflight.py', '--repo', self.ana, '--json')
        self.assertEqual(code, 1, out)
        self.assertIn('ANOMALY', json.dumps(env), out)


if __name__ == '__main__':
    unittest.main()
