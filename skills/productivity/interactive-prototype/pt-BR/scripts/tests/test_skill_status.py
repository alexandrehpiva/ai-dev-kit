import shutil
import unittest

import helpers
import skillfake as sf


class SkillStatusTests(helpers.TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'proto'
        self.repo.mkdir()

    def status(self, skill_version='2.0.0'):
        skill = self.tmp / 'skill'
        if not skill.exists():
            sf.make_skill(self.tmp, version=skill_version)
        code, env, err = sf.run(skill, 'skill-status.py', '--repo', self.repo)
        self.assertIsNotNone(env, err)
        return code, env

    def with_skill(self, version):
        shutil.rmtree(self.tmp / 'skill', ignore_errors=True)
        return self.status(version)

    def index(self):
        (self.repo / 'index.html').write_text('<html></html>', encoding='utf-8')

    def test_nao_e_prototipo(self):
        code, env = self.status()
        self.assertEqual((code, env['status']), (0, 'NOT_A_PROTOTYPE'))

    def test_sem_config_com_index_e_legado_migravel(self):
        self.index()
        code, env = self.status()
        self.assertEqual((code, env['status']), (0, 'NO_CONFIG'))
        self.assertEqual(env['data']['prototypeVersion'], '1.0.0')
        self.assertEqual(env['data']['migrationsPending'], [{'from': '1.0.0', 'to': '2.0.0', 'type': 'migration'}])
        self.assertFalse(env['data']['requiresPromoter'])

    def test_config_v1_sem_bloco_skill_e_legado(self):
        self.index()
        sf.write_cfg(self.repo, {'groupMode': True, 'sharedBranch': 'main', 'remote': 'origin'})
        code, env = self.status()
        self.assertEqual((code, env['status']), (0, 'PROTOTYPE_LEGACY'))
        self.assertTrue(env['data']['requiresPromoter'])
        self.assertEqual(env['data']['skillVersion'], '2.0.0')

    def test_atualizado(self):
        self.index()
        sf.write_cfg(self.repo, sf.valid_cfg(group=False))
        code, env = self.status()
        self.assertEqual((code, env['status']), (0, 'UP_TO_DATE'))
        self.assertEqual(env['data']['migrationsPending'], [])

    def test_prototipo_defasado_encadeia_saltos_em_ordem(self):
        self.index()
        sf.write_cfg(self.repo, sf.valid_cfg(group=False))
        code, env = self.with_skill('2.1.0')
        self.assertEqual((code, env['status']), (0, 'PROTOTYPE_OUTDATED'))
        self.assertEqual(env['data']['migrationsPending'], [{'from': '2.0.0', 'to': '2.1.0', 'type': 'version-bump'}])

    def test_legado_para_skill_futura_lista_migracao_e_bump(self):
        self.index()
        sf.write_cfg(self.repo, {'groupMode': False, 'remote': 'origin'})
        _, env = self.with_skill('2.3.0')
        self.assertEqual([(s['from'], s['to'], s['type']) for s in env['data']['migrationsPending']],
                         [('1.0.0', '2.0.0', 'migration'), ('2.0.0', '2.3.0', 'version-bump')])

    def test_skill_desatualizada_vira_consulta(self):
        self.index()
        cfg = sf.valid_cfg()
        cfg['skill']['version'] = '2.5.0'
        sf.write_cfg(self.repo, cfg)
        code, env = self.status()
        self.assertEqual((code, env['status'], env['data']['mode']), (0, 'SKILL_OUTDATED', 'consult'))
        self.assertEqual(env['data']['migrationsPending'], [])

    def test_skill_sem_versao_da_erro_claro(self):
        self.index()
        code, env = self.with_skill(None)
        self.assertEqual((code, env['status']), (1, 'SKILL_VERSION_MISSING'))
        self.assertIn('SKILL.md', env['problems'][0]['message'])

    def test_config_com_json_quebrado(self):
        self.index()
        (self.repo / 'prototype.config.json').write_text('{x', encoding='utf-8')
        code, env = self.status()
        self.assertEqual((code, env['status']), (1, 'INVALID_CONFIG'))

    def test_versao_do_prototipo_malformada(self):
        self.index()
        cfg = sf.valid_cfg()
        cfg['skill']['version'] = 'dois'
        sf.write_cfg(self.repo, cfg)
        code, env = self.status()
        self.assertEqual((code, env['status']), (1, 'INVALID_CONFIG'))

    def test_nao_altera_nada(self):
        self.index()
        sf.write_cfg(self.repo, {'groupMode': False, 'remote': 'origin'})
        before = sorted(p.name for p in self.repo.iterdir())
        text = (self.repo / 'prototype.config.json').read_text()
        self.status()
        self.assertEqual(before, sorted(p.name for p in self.repo.iterdir()))
        self.assertEqual(text, (self.repo / 'prototype.config.json').read_text())


if __name__ == '__main__':
    unittest.main()
