import unittest

import helpers
import skillfake as sf

OWNER = ['--owner', 'ana@example.test']


class ArtifactsTests(helpers.TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = sf.make_skill(self.tmp)
        self.repo = self.tmp / 'proto'
        self.repo.mkdir()
        self.members = [sf.member(), sf.member('bia@example.test', status='pending', roles=('contributor',)),
                        sf.member('caio@example.test', status='revoked', roles=('contributor',))]
        sf.write_cfg(self.repo, sf.valid_cfg(members=self.members))

    def art(self, *args):
        code, env, err = sf.run(self.skill, 'artifacts.py', '--repo', self.repo, *args)
        self.assertIsNotNone(env, err)
        return code, env

    def stored(self, art_id):
        return next(a for a in sf.read_cfg(self.repo)['artifacts'] if a['id'] == art_id)

    def register(self, art_id='beta', kind='beta', *extra):
        return self.art('register', '--id', art_id, '--kind', kind, '--delivery', 'claude-artifact', *OWNER, *extra)

    def test_list_vazio_e_com_itens(self):
        code, env = self.art('list')
        self.assertEqual((code, env['status'], env['data']['count']), (0, 'OK', 0))
        self.register('beta', 'beta', '--url', 'https://example.test/b')
        self.assertEqual(self.art('list')[1]['data']['count'], 1)

    def test_register_com_url_fica_stale_e_usa_branch_do_config(self):
        code, env = self.register('beta', 'beta', '--url', 'https://example.test/b', '--label', 'Beta',
                                  '--purpose', 'validar', '--source-ref', 'beta@abc1234')
        self.assertEqual((code, env['status']), (0, 'REGISTERED'), env)
        a = self.stored('beta')
        self.assertEqual((a['status'], a['branch'], a['version'], a['pendingVersion'], a['publishedAt'], a['publishedBy']),
                         ('stale', 'beta', None, None, None, None))
        self.assertEqual((a['label'], a['purpose'], a['sourceRef']), ('Beta', 'validar', 'beta@abc1234'))

    def test_register_sem_link_fica_missing_e_preview_sem_branch(self):
        self.register('pv1', 'preview')
        a = self.stored('pv1')
        self.assertEqual((a['status'], a['branch']), ('missing', None))

    def test_register_arquivo(self):
        code, env = self.art('register', '--id', 'f1', '--kind', 'preview', '--delivery', 'file', '--path', 'dist/index.html', *OWNER)
        self.assertEqual(code, 0, env)
        self.assertEqual(self.stored('f1')['path'], 'dist/index.html')

    def test_register_recusas(self):
        self.register('beta', 'beta')
        cases = [
            (self.register('beta', 'preview'), 'DUPLICATE_ID'),
            (self.register('beta2', 'beta'), 'DUPLICATE_KIND'),
            (self.register('x', 'preview', '--url', 'ftp://x'), 'BAD_URL'),
            (self.register('y', 'preview', '--url', 'https://example.test/y', '--path', 'a'), 'BAD_LOCATION'),
            (self.art('register', '--id', 'z', '--kind', 'preview', '--delivery', 'file', '--url', 'https://example.test/z', *OWNER), 'BAD_LOCATION'),
            (self.art('register', '--id', 'w', '--kind', 'preview', '--delivery', 'claude-artifact', '--owner', 'ninguem@example.test'), 'UNKNOWN_OWNER'),
        ]
        for (code, env), expected in cases:
            self.assertEqual((code, env['status'], env['problems'][0]['code']), (1, 'REFUSED', expected), env)
        self.assertEqual(len(sf.read_cfg(self.repo)['artifacts']), 1)

    def test_enum_invalido_e_uso_incorreto(self):
        code, env = self.art('register', '--id', 'a', '--kind', 'gamma', '--delivery', 'file', *OWNER)
        self.assertEqual((code, env['status']), (2, 'BAD_USAGE'))
        code, env = self.art('set-status', '--id', 'a', '--status', 'inventado')
        self.assertEqual((code, env['status']), (2, 'BAD_USAGE'))

    def test_published_beta_normaliza_versao_e_limpa_pendencia(self):
        self.register('beta', 'beta', '--url', 'https://example.test/b')
        self.art('mark-stale', '--id', 'beta', '--pending-version', 'v1.0.0-beta.2')
        self.assertEqual(self.stored('beta')['pendingVersion'], 'v1.0.0-beta.2')
        code, env = self.art('published', '--id', 'beta', '--version', '1.0.0-beta.2', '--actor', 'bia@example.test')
        self.assertEqual((code, env['status']), (0, 'PUBLISHED'), env)
        a = self.stored('beta')
        self.assertEqual((a['version'], a['status'], a['pendingVersion'], a['publishedBy']),
                         ('v1.0.0-beta.2', 'current', None, 'bia@example.test'))
        self.assertRegex(a['publishedAt'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    def test_published_valida_versao_pelo_tipo(self):
        self.register('beta', 'beta')
        self.register('off', 'official')
        for args, code_expected in [
            (('beta', 'v1.0.0'), 'BAD_VERSION'), (('off', 'v1.0.0-beta.1'), 'BAD_VERSION'),
            (('off', 'abc'), 'BAD_VERSION')]:
            code, env = self.art('published', '--id', args[0], '--version', args[1], '--actor', 'ana@example.test')
            self.assertEqual((code, env['problems'][0]['code']), (1, code_expected))
        code, env = self.art('published', '--id', 'off', '--actor', 'ana@example.test')
        self.assertEqual(env['problems'][0]['code'], 'BAD_VERSION')

    def test_published_ator_e_permissao(self):
        self.register('off', 'official')
        for who, expected in [('bia@example.test', 'BAD_ACTOR'), ('caio@example.test', 'BAD_ACTOR'), ('zz@example.test', 'BAD_ACTOR')]:
            code, env = self.art('published', '--id', 'off', '--version', 'v1.0.0', '--actor', who)
            self.assertEqual((code, env['problems'][0]['code']), (1, expected), who)
        self.register('pv', 'preview')
        code, env = self.art('published', '--id', 'pv', '--actor', 'caio@example.test')
        self.assertEqual(code, 1)
        code, env = self.art('published', '--id', 'pv', '--actor', 'bia@example.test')
        self.assertEqual(code, 0, env)
        self.assertIsNone(self.stored('pv')['version'])
        self.assertEqual(self.stored('pv')['status'], 'current')

    def test_artefato_inexistente(self):
        code, env = self.art('mark-stale', '--id', 'nada', '--pending-version', 'v1.0.0')
        self.assertEqual((code, env['problems'][0]['code']), (1, 'NOT_FOUND'))

    def test_mark_stale_valida_versao(self):
        self.register('off', 'official')
        code, env = self.art('mark-stale', '--id', 'off', '--pending-version', 'v1.0.0-beta.1')
        self.assertEqual((code, env['problems'][0]['code']), (1, 'BAD_VERSION'))
        code, _ = self.art('mark-stale', '--id', 'off', '--pending-version', 'v1.1.0')
        self.assertEqual(code, 0)
        self.assertEqual(self.stored('off')['pendingVersion'], 'v1.1.0')

    def test_revoke_guarda_motivo_e_bloqueia_publicacao(self):
        self.register('off', 'official', '--url', 'https://example.test/o')
        code, env = self.art('revoke', '--id', 'off', '--reason', '  link vazou  ')
        self.assertEqual((code, env['status']), (0, 'REVOKED'), env)
        a = self.stored('off')
        self.assertEqual((a['status'], a['revokedReason']), ('revoked', 'link vazou'))
        self.assertEqual(self.art('published', '--id', 'off', '--version', 'v1.0.0', '--actor', 'ana@example.test')[1]['problems'][0]['code'], 'REVOKED')
        self.assertEqual(self.art('mark-stale', '--id', 'off', '--pending-version', 'v1.0.1')[1]['problems'][0]['code'], 'REVOKED')
        self.assertEqual(self.art('revoke', '--id', 'off', '--reason', '   ')[1]['problems'][0]['code'], 'BAD_REASON')

    def test_revogado_libera_novo_oficial(self):
        self.register('off', 'official')
        self.art('revoke', '--id', 'off', '--reason', 'trocado')
        code, env = self.register('off2', 'official')
        self.assertEqual(code, 0, env)

    def test_set_status(self):
        self.register('beta', 'beta')
        code, env = self.art('set-status', '--id', 'beta', '--status', 'current')
        self.assertEqual((code, env['problems'][0]['code']), (1, 'BAD_STATUS'))
        self.art('revoke', '--id', 'beta', '--reason', 'teste')
        code, env = self.art('set-status', '--id', 'beta', '--status', 'missing')
        self.assertEqual((code, env['status']), (0, 'STATUS_SET'))
        a = self.stored('beta')
        self.assertEqual(a['status'], 'missing')
        self.assertNotIn('revokedReason', a)

    def test_set_status_current_apos_publicar(self):
        self.register('beta', 'beta')
        self.art('published', '--id', 'beta', '--version', 'v1.0.0-beta.1', '--actor', 'ana@example.test')
        self.art('set-status', '--id', 'beta', '--status', 'stale')
        code, _ = self.art('set-status', '--id', 'beta', '--status', 'current')
        self.assertEqual(code, 0)

    def test_config_resultante_continua_valido(self):
        self.register('off', 'official', '--url', 'https://example.test/o')
        self.art('published', '--id', 'off', '--version', 'v1.0.0', '--actor', 'ana@example.test')
        code, env, _ = sf.run(self.skill, 'config-validate.py', '--repo', self.repo)
        self.assertEqual((code, env['status']), (0, 'VALID'), env)

    def test_recusa_se_config_ficar_invalido(self):
        cfg = sf.read_cfg(self.repo)
        cfg['branches']['beta'] = 'main'
        sf.write_cfg(self.repo, cfg)
        code, env = self.register('beta', 'beta')
        self.assertEqual(code, 0)  # problema pré-existente não bloqueia
        cfg = sf.read_cfg(self.repo)
        cfg['members'][0]['email'] = 'ANA@example.test'
        cfg['artifacts'][0]['owner'] = 'ANA@example.test'
        cfg['members'].append(sf.member('ana@example.test'))
        sf.write_cfg(self.repo, cfg)
        before = (self.repo / 'prototype.config.json').read_text()
        code, env = self.register('novo', 'preview')
        self.assertEqual(code, 0)  # duplicata de e-mail já existia: não é novo
        self.assertNotEqual(before, (self.repo / 'prototype.config.json').read_text())

    def test_exige_config_v2(self):
        (self.repo / 'prototype.config.json').unlink()
        code, env = self.art('list')
        self.assertEqual((code, env['status']), (1, 'NO_CONFIG'))
        sf.write_cfg(self.repo, {'groupMode': False})
        code, env = self.art('list')
        self.assertEqual((code, env['status']), (1, 'LEGACY'))

    def test_escrita_atomica_sem_residuos_e_json_preservado(self):
        self.register('beta', 'beta')
        self.assertEqual([p.name for p in self.repo.iterdir() if p.name.endswith('.tmp')], [])
        text = (self.repo / 'prototype.config.json').read_text()
        self.assertTrue(text.endswith('\n'))
        self.assertIn('"id": "beta"', text)

    def test_json_quebrado(self):
        (self.repo / 'prototype.config.json').write_text('{', encoding='utf-8')
        code, env = self.art('list')
        self.assertEqual((code, env['status']), (1, 'INVALID'))


if __name__ == '__main__':
    unittest.main()
