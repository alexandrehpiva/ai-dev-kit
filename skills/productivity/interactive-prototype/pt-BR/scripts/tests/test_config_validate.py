import copy
import json
import unittest

import helpers
import protolib
import skillfake as sf


class ConfigValidateTests(helpers.TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = sf.make_skill(self.tmp)
        self.repo = self.tmp / 'proto'
        self.repo.mkdir()

    def validate(self, *extra):
        code, env, err = sf.run(self.skill, 'config-validate.py', '--repo', self.repo, *extra)
        self.assertIsNotNone(env, err)
        return code, env

    def paths(self, env):
        return [p['path'] for p in env['problems']]

    def test_config_v2_valido(self):
        sf.write_cfg(self.repo, sf.valid_cfg(artifacts=[sf.artifact()]))
        code, env = self.validate()
        self.assertEqual((code, env['status'], env['ok']), (0, 'VALID', True), env)
        self.assertEqual(env['problems'], [])

    def test_sem_config(self):
        code, env = self.validate()
        self.assertEqual((code, env['status']), (0, 'NO_CONFIG'))

    def test_sem_config_exigindo_promoter_falha(self):
        code, env = self.validate('--require-promoter')
        self.assertEqual((code, env['status']), (1, 'NO_CONFIG'))

    def test_json_quebrado(self):
        (self.repo / 'prototype.config.json').write_text('{ nao e json', encoding='utf-8')
        code, env = self.validate()
        self.assertEqual((code, env['status']), (1, 'INVALID'))
        self.assertEqual(env['problems'][0]['code'], 'JSON')

    def test_legado_v1_nao_e_erro(self):
        sf.write_cfg(self.repo, {'groupMode': True, 'sharedBranch': 'main', 'remote': 'origin'})
        code, env = self.validate()
        self.assertEqual((code, env['status'], env['data']['legacy']), (0, 'LEGACY', True))

    def test_legado_com_tipo_errado_e_invalido(self):
        sf.write_cfg(self.repo, {'groupMode': 'sim', 'remote': 'origin'})
        code, env = self.validate()
        self.assertEqual((code, env['status']), (1, 'INVALID'))
        self.assertEqual(self.paths(env), ['groupMode'])

    def test_legado_com_require_promoter_falha(self):
        sf.write_cfg(self.repo, {'groupMode': False, 'remote': 'origin'})
        code, env = self.validate('--require-promoter')
        self.assertEqual((code, env['status']), (1, 'LEGACY'))

    def test_campo_obrigatorio_enum_e_tipo_com_caminho(self):
        cfg = sf.valid_cfg(members=[sf.member(), sf.member('bia@example.test')])
        cfg['members'][1]['profile'] = 'gerente'
        cfg['members'][1]['roles'] = 'promoter'
        del cfg['members'][1]['registeredAt']
        sf.write_cfg(self.repo, cfg)
        code, env = self.validate()
        self.assertEqual(code, 1)
        self.assertEqual(env['status'], 'INVALID')
        self.assertIn('members[1].profile', self.paths(env))
        self.assertIn('members[1].roles', self.paths(env))
        self.assertIn('members[1].registeredAt', self.paths(env))
        msg = next(p['message'] for p in env['problems'] if p['path'] == 'members[1].profile')
        self.assertTrue(msg.startswith('members[1].profile:'))

    def test_campo_desconhecido_barrado_mas_doc_aceito(self):
        cfg = sf.valid_cfg(_doc='comentario')
        cfg['policy']['_doc'] = 'ok'
        cfg['branches']['extra'] = 1
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['branches.extra'])

    def test_formatos_email_data_e_semver(self):
        cfg = sf.valid_cfg()
        cfg['members'][0]['email'] = 'sem-arroba'
        cfg['members'][0]['registeredAt'] = '2026-13-45T00:00:00Z'
        cfg['skill']['version'] = '2.0'
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(set(self.paths(env)), {'members[0].email', 'members[0].registeredAt', 'skill.version'})

    def test_artefato_enums_e_versao(self):
        cfg = sf.valid_cfg(artifacts=[sf.artifact(status='quebrado', version='1.2', kind='x')])
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertTrue({'artifacts[0].status', 'artifacts[0].version', 'artifacts[0].kind'} <= set(self.paths(env)))

    def test_inteiro_nao_aceita_booleano(self):
        cfg = sf.valid_cfg()
        cfg['policy']['pendingExpiryDays'] = True
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['policy.pendingExpiryDays'])

    def test_emails_duplicados_ignorando_caixa(self):
        cfg = sf.valid_cfg(members=[sf.member(), sf.member('ANA@example.test')])
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['members[1].email'])

    def test_ids_de_artefato_duplicados(self):
        cfg = sf.valid_cfg(artifacts=[sf.artifact('a', 'preview'), sf.artifact('a', 'preview')])
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['artifacts[1].id'])

    def test_no_maximo_um_official_e_um_beta(self):
        cfg = sf.valid_cfg(artifacts=[sf.artifact('o1', 'official'), sf.artifact('o2', 'official'),
                                      sf.artifact('b1', 'beta'), sf.artifact('b2', 'beta')])
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['artifacts[1].kind', 'artifacts[3].kind'])

    def test_artefato_revogado_libera_o_lugar(self):
        cfg = sf.valid_cfg(artifacts=[sf.artifact('o1', 'official', status='revoked'), sf.artifact('o2', 'official')])
        sf.write_cfg(self.repo, cfg)
        code, env = self.validate()
        self.assertEqual((code, env['status']), (0, 'VALID'), env)

    def test_owner_inexistente(self):
        sf.write_cfg(self.repo, sf.valid_cfg(artifacts=[sf.artifact(owner='fantasma@example.test')]))
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['artifacts[0].owner'])

    def test_branches_oficial_e_beta_iguais(self):
        cfg = sf.valid_cfg()
        cfg['branches']['beta'] = 'main'
        sf.write_cfg(self.repo, cfg)
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['branches.beta'])

    def test_group_mode_exige_promoter_aprovado(self):
        cfg = sf.valid_cfg(members=[sf.member(roles=('contributor',)), sf.member('bia@example.test', status='pending')])
        sf.write_cfg(self.repo, cfg)
        code, env = self.validate()
        self.assertEqual((code, env['status'], self.paths(env)), (1, 'INVALID', ['members']))

    def test_group_mode_desligado_dispensa_promoter_mas_require_promoter_exige(self):
        sf.write_cfg(self.repo, sf.valid_cfg(group=False, members=[sf.member(roles=('contributor',))]))
        self.assertEqual(self.validate()[1]['status'], 'VALID')
        code, env = self.validate('--require-promoter')
        self.assertEqual((code, env['status']), (1, 'INVALID'))

    def test_status_diverge_do_ultimo_historico(self):
        m = sf.member()
        m['statusHistory'].append({'status': 'revoked', 'at': sf.NOW, 'commit': None, 'by': 'ana@example.test'})
        sf.write_cfg(self.repo, sf.valid_cfg(group=False, members=[m]))
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['members[0].status'])

    def test_historico_vazio_e_reportado(self):
        m = sf.member()
        m['statusHistory'] = []
        sf.write_cfg(self.repo, sf.valid_cfg(group=False, members=[m]))
        _, env = self.validate()
        self.assertEqual(self.paths(env), ['members[0].statusHistory'])

    def test_by_aceita_self_setup_e_email(self):
        m = sf.member()
        m['statusHistory'] = [{'status': 'pending', 'at': sf.NOW, 'commit': 'abc1234', 'by': 'self'},
                              {'status': 'approved', 'at': sf.NOW, 'commit': None, 'by': 'ana@example.test'}]
        sf.write_cfg(self.repo, sf.valid_cfg(members=[m]))
        self.assertEqual(self.validate()[1]['status'], 'VALID')
        m['statusHistory'][1]['by'] = 'qualquer coisa'
        sf.write_cfg(self.repo, sf.valid_cfg(members=[m]))
        self.assertEqual(self.paths(self.validate()[1]), ['members[0].statusHistory[1].by'])

    def test_raiz_nao_objeto(self):
        (self.repo / 'prototype.config.json').write_text('[1]', encoding='utf-8')
        code, env = self.validate()
        self.assertEqual((code, env['status']), (1, 'INVALID'))

    def test_pasta_inexistente_e_uso_incorreto(self):
        code, env, _ = sf.run(self.skill, 'config-validate.py', '--repo', self.tmp / 'nao-existe')
        self.assertEqual((code, env['status']), (2, 'BAD_USAGE'))

    def test_schema_real_e_coerente_com_protolib(self):
        schema = json.loads((helpers.SCRIPTS.parent / 'templates' / 'prototype.config.schema.json').read_text())
        self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
        d = schema['$defs']
        self.assertEqual(tuple(d['member']['properties']['roles']['items']['enum']), protolib.ROLES)
        self.assertEqual(tuple(d['member']['properties']['profile']['enum']), protolib.PROFILES)
        self.assertEqual(tuple(d['member']['properties']['identityEvidence']['enum']), protolib.EVIDENCE)
        self.assertEqual(tuple(d['memberStatus']['enum']), protolib.MEMBER_STATUSES)
        art = d['artifact']['properties']
        self.assertEqual(tuple(art['kind']['enum']), protolib.ARTIFACT_KINDS)
        self.assertEqual(tuple(art['status']['enum']), protolib.ARTIFACT_STATUSES)
        self.assertEqual(tuple(art['delivery']['enum']), protolib.DELIVERIES)
        self.assertIn('_doc', schema['properties'])


if __name__ == '__main__':
    unittest.main()
