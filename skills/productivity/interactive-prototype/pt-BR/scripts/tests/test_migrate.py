import json
import shutil
import subprocess
import unittest

import helpers
import skillfake as sf

ACTOR = ['--actor-name', 'Ana Teste', '--actor-email', 'Ana@example.test']
ANSWERS_SOLO = {'promoters_policy': 'all-members', 'docs_auto_maintain': False}
ANSWERS_GROUP = {**ANSWERS_SOLO, 'artifact_official': {'url': 'https://example.test/o'},
                 'artifact_beta': {'create': True}}


def snapshot(repo):
    return {str(p.relative_to(repo)): (p.read_bytes() if p.is_file() else None)
            for p in sorted(repo.rglob('*')) if '.git' not in p.parts}


class MigrateTests(helpers.TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.skill = sf.make_skill(self.tmp)
        self.repo = self.tmp / 'meu-proto'
        self.repo.mkdir()
        (self.repo / 'index.html').write_text('<html></html>', encoding='utf-8')

    def migrate(self, *args, skill=None):
        code, env, err = sf.run(skill or self.skill, 'migrate.py', '--repo', self.repo, *args)
        self.assertIsNotNone(env, err)
        return code, env

    def execute(self, answers, *extra):
        return self.migrate('--execute', '--answers-json', json.dumps(answers), *extra)

    def legacy(self, group):
        sf.write_cfg(self.repo, {'groupMode': group, 'sharedBranch': 'main', 'remote': 'upstream'})

    # --- plan ---
    def test_plan_nao_escreve_e_traz_perguntas_obrigatorias(self):
        self.legacy(False)
        before = snapshot(self.repo)
        code, env = self.migrate()
        self.assertEqual((code, env['status']), (0, 'PLAN'))
        self.assertEqual(snapshot(self.repo), before)
        ids = [q['id'] for q in env['questions']]
        self.assertEqual(ids, ['promoters_policy', 'docs_auto_maintain'])
        q = env['questions'][0]
        self.assertEqual((q['options'], q['default']), (['all-members', 'listed'], 'all-members'))
        self.assertTrue(env['data']['steps'])
        self.assertEqual(env['data']['migrationsPending'][0]['to'], '2.0.0')

    def test_plan_grupo_pergunta_artefatos(self):
        self.legacy(True)
        _, env = self.migrate('--plan')
        self.assertEqual([q['id'] for q in env['questions']],
                         ['promoters_policy', 'docs_auto_maintain', 'artifact_official', 'artifact_beta'])
        self.assertTrue(env['data']['requiresActor'])

    def test_plan_com_respostas_nao_repete_perguntas(self):
        self.legacy(False)
        _, env = self.migrate('--answers-json', json.dumps({'promoters_policy': 'listed'}))
        self.assertEqual([q['id'] for q in env['questions']], ['docs_auto_maintain'])

    def test_plan_sem_config_cria_v2_minimo(self):
        before = snapshot(self.repo)
        code, env = self.migrate()
        self.assertEqual((code, env['status']), (0, 'PLAN'))
        self.assertIn('Criar prototype.config.json v2', env['data']['steps'][0])
        self.assertEqual(snapshot(self.repo), before)

    # --- execute: recusas ---
    def test_execute_sem_respostas_pede_respostas(self):
        self.legacy(False)
        before = snapshot(self.repo)
        code, env = self.migrate('--execute', *ACTOR)
        self.assertEqual((code, env['status']), (1, 'NEEDS_ANSWERS'))
        self.assertEqual(len(env['questions']), 2)
        self.assertEqual(snapshot(self.repo), before)

    def test_execute_grupo_sem_ator_recusa(self):
        self.legacy(True)
        before = snapshot(self.repo)
        code, env = self.execute(ANSWERS_GROUP)
        self.assertEqual((code, env['status']), (1, 'NEEDS_ACTOR'))
        self.assertEqual(snapshot(self.repo), before)

    def test_resposta_invalida(self):
        self.legacy(False)
        code, env = self.execute({'promoters_policy': 'qualquer', 'docs_auto_maintain': 'talvez'}, *ACTOR)
        self.assertEqual((code, env['status']), (1, 'BAD_ANSWERS'))
        self.assertEqual(len(env['problems']), 2)

    def test_resposta_de_artefato_ambigua(self):
        self.legacy(True)
        bad = {**ANSWERS_GROUP, 'artifact_official': {'url': 'https://example.test/o', 'path': 'x.html'}}
        code, env = self.execute(bad, *ACTOR)
        self.assertEqual((code, env['status']), (1, 'BAD_ANSWERS'))

    def test_ator_pela_metade_e_uso_incorreto(self):
        self.legacy(False)
        code, env = self.migrate('--execute', '--actor-name', 'Ana')
        self.assertEqual((code, env['status']), (2, 'BAD_USAGE'))

    def test_nao_e_prototipo(self):
        (self.repo / 'index.html').unlink()
        code, env = self.migrate()
        self.assertEqual((code, env['status']), (1, 'NOT_A_PROTOTYPE'))

    def test_skill_sem_versao_recusa(self):
        self.legacy(False)
        shutil.rmtree(self.tmp / 'skill')
        skill = sf.make_skill(self.tmp, version=None)
        code, env = self.migrate(skill=skill)
        self.assertEqual((code, env['status']), (1, 'SKILL_VERSION_MISSING'))

    def test_prototipo_mais_novo_so_consulta(self):
        cfg = sf.valid_cfg()
        cfg['skill']['version'] = '3.0.0'
        sf.write_cfg(self.repo, cfg)
        before = snapshot(self.repo)
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual((code, env['status'], env['data']['mode']), (1, 'SKILL_OUTDATED', 'consult'))
        self.assertEqual(snapshot(self.repo), before)

    # --- execute: caminho feliz ---
    def test_migracao_solo_v1_para_v2(self):
        self.legacy(False)
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        cfg = sf.read_cfg(self.repo)
        self.assertEqual(cfg['skill'], {'name': 'interactive-prototype', 'version': '2.0.0'})
        self.assertEqual((cfg['groupMode'], cfg['remote']), (False, 'upstream'))
        self.assertNotIn('sharedBranch', cfg)
        self.assertEqual(cfg['branches'], {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'})
        self.assertEqual(cfg['policy']['promoters'], 'all-members')
        self.assertIs(cfg['docs']['autoMaintain'], False)
        self.assertEqual(cfg['artifacts'], [])
        (m,) = cfg['members']
        self.assertEqual((m['email'], m['status'], m['identityEvidence']), ('Ana@example.test', 'approved', 'unverified'))
        self.assertIn('promoter', m['roles'])
        self.assertEqual(m['statusHistory'][-1]['by'], 'setup')

    def test_migracao_grupo_registra_artefatos_e_preserva_shared_branch(self):
        sf.write_cfg(self.repo, {'groupMode': True, 'sharedBranch': 'trunk', 'remote': 'origin'})
        code, env = self.execute(ANSWERS_GROUP, *ACTOR, '--actor-evidence', 'git-only', '--actor-profile', 'product')
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        cfg = sf.read_cfg(self.repo)
        self.assertEqual(cfg['branches']['official'], 'trunk')
        self.assertEqual(cfg['members'][0]['identityEvidence'], 'git-only')
        self.assertEqual(cfg['members'][0]['profile'], 'product')
        off, beta = cfg['artifacts']
        self.assertEqual((off['kind'], off['status'], off['url'], off['delivery'], off['version'], off['pendingVersion']),
                         ('official', 'stale', 'https://example.test/o', 'claude-artifact', None, None))
        self.assertEqual((beta['kind'], beta['status'], beta['branch']), ('beta', 'missing', 'beta'))
        self.assertNotIn('url', beta)
        self.assertEqual(off['owner'], 'Ana@example.test')

    def test_artefato_por_caminho_vira_file(self):
        self.legacy(True)
        ans = {**ANSWERS_GROUP, 'artifact_official': {'path': 'dist/index.html'}}
        self.execute(ans, *ACTOR)
        off = sf.read_cfg(self.repo)['artifacts'][0]
        self.assertEqual((off['delivery'], off['path'], off['status']), ('file', 'dist/index.html', 'stale'))

    def test_respostas_de_arquivo(self):
        self.legacy(False)
        f = self.tmp / 'ans.json'
        f.write_text(json.dumps({'promoters_policy': 'listed', 'docs_auto_maintain': 'true'}), encoding='utf-8')
        code, env = self.migrate('--execute', '--answers', f, *ACTOR)
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        cfg = sf.read_cfg(self.repo)
        self.assertEqual(cfg['policy']['promoters'], 'listed')
        self.assertIs(cfg['docs']['autoMaintain'], True)

    def test_sem_config_com_index_cria_v2_solo(self):
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        cfg = sf.read_cfg(self.repo)
        self.assertEqual((cfg['groupMode'], cfg['remote']), (False, 'origin'))
        self.assertIn('prototype.config.json', env['data']['created'])

    def test_templates_renderizados_e_nao_sobrescreve(self):
        self.legacy(False)
        (self.repo / 'CLAUDE.md').write_text('meu conteudo\n', encoding='utf-8')
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual(code, 0, env)
        self.assertEqual((self.repo / 'AGENTS.md').read_text(), '# Agentes de meu-proto\nskill 2.0.0\n')
        self.assertEqual((self.repo / 'docs/business-rules.md').read_text(), '# Regras de meu-proto\n')
        self.assertEqual((self.repo / 'docs/components.md').read_text(), '# Componentes (skill 2.0.0)\n')
        self.assertEqual((self.repo / 'CLAUDE.md').read_text(), 'meu conteudo\n')
        self.assertIn('CLAUDE.md', env['data']['skipped'])
        self.assertIn('AGENTS.md', env['data']['created'])

    def test_template_ausente_vira_aviso(self):
        self.legacy(False)
        (self.tmp / 'skill/templates/docs/components.md').unlink()
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual(code, 0, env)
        self.assertFalse((self.repo / 'docs/components.md').exists())
        self.assertTrue(any('docs/components.md' in w for w in env['data']['warnings']))

    def test_templates_dir_alternativo(self):
        self.legacy(False)
        alt = self.tmp / 'alt'
        (alt / 'docs').mkdir(parents=True)
        (alt / 'AGENTS.md').write_text('alt @@NAME@@', encoding='utf-8')
        code, env = self.execute(ANSWERS_SOLO, *ACTOR, '--templates-dir', alt)
        self.assertEqual(code, 0, env)
        self.assertEqual((self.repo / 'AGENTS.md').read_text(), 'alt meu-proto')
        self.assertFalse((self.repo / 'CLAUDE.md').exists())
        self.assertEqual(len(env['data']['warnings']), 3)

    def test_gitignore_criado_acrescentado_e_respeitado(self):
        self.legacy(False)
        self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual((self.repo / '.gitignore').read_text().count('dist/'), 1)

        repo2 = self.tmp / 'outro'
        repo2.mkdir()
        (repo2 / 'index.html').write_text('x')
        (repo2 / '.gitignore').write_text('node_modules/', encoding='utf-8')
        sf.write_cfg(repo2, {'groupMode': False})
        sf.run(self.skill, 'migrate.py', '--repo', repo2, '--execute', '--answers-json', json.dumps(ANSWERS_SOLO), *ACTOR)
        self.assertEqual((repo2 / '.gitignore').read_text(), 'node_modules/\ndist/\n')

        repo3 = self.tmp / 'terceiro'
        repo3.mkdir()
        (repo3 / 'index.html').write_text('x')
        (repo3 / '.gitignore').write_text('/dist\n', encoding='utf-8')
        sf.run(self.skill, 'migrate.py', '--repo', repo3, '--execute', '--answers-json', json.dumps(ANSWERS_SOLO), *ACTOR)
        self.assertEqual((repo3 / '.gitignore').read_text(), '/dist\n')

    def test_idempotente(self):
        self.legacy(True)
        self.execute(ANSWERS_GROUP, *ACTOR)
        after_first = snapshot(self.repo)
        code, env = self.execute(ANSWERS_GROUP, *ACTOR)
        self.assertEqual((code, env['status']), (0, 'UP_TO_DATE'))
        self.assertEqual(snapshot(self.repo), after_first)
        cfg = sf.read_cfg(self.repo)
        self.assertEqual((len(cfg['members']), len(cfg['artifacts'])), (1, 2))

    def test_retomada_apos_interrupcao_nao_duplica(self):
        self.legacy(False)
        (self.repo / 'AGENTS.md').write_text('feito antes', encoding='utf-8')
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual(code, 0, env)
        self.assertEqual((self.repo / 'AGENTS.md').read_text(), 'feito antes')

    def test_config_resultante_valida(self):
        self.legacy(True)
        self.execute(ANSWERS_GROUP, *ACTOR)
        code, env, _ = sf.run(self.skill, 'config-validate.py', '--repo', self.repo, '--require-promoter')
        self.assertEqual((code, env['status']), (0, 'VALID'), env)

    def test_config_invalido_apos_migrar_nao_escreve_nada(self):
        sf.write_cfg(self.repo, {'groupMode': False, 'sharedBranch': 'beta'})
        before = snapshot(self.repo)
        code, env = self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual((code, env['status']), (1, 'INVALID'))
        self.assertEqual([p['path'] for p in env['problems']], ['branches.beta'])
        self.assertEqual(snapshot(self.repo), before)

    def test_bump_final_quando_skill_esta_a_frente(self):
        self.legacy(False)
        shutil.rmtree(self.tmp / 'skill')
        skill = sf.make_skill(self.tmp, version='2.2.0')
        code, env = self.migrate('--execute', '--answers-json', json.dumps(ANSWERS_SOLO), *ACTOR, skill=skill)
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        self.assertEqual(sf.read_cfg(self.repo)['skill']['version'], '2.2.0')
        self.assertEqual([s['type'] for s in env['data']['migrationsPending']], ['migration', 'version-bump'])

    def test_bump_puro_em_config_v2_nao_exige_ator_nem_respostas(self):
        sf.write_cfg(self.repo, sf.valid_cfg(group=False))
        shutil.rmtree(self.tmp / 'skill')
        skill = sf.make_skill(self.tmp, version='2.1.0')
        code, env = self.migrate('--execute', skill=skill)
        self.assertEqual((code, env['status']), (0, 'MIGRATED'), env)
        self.assertEqual(sf.read_cfg(self.repo)['skill']['version'], '2.1.0')

    def test_ator_nao_promoter_nao_migra(self):
        cfg = sf.valid_cfg(members=[sf.member(), sf.member('bia@example.test', roles=('contributor',))])
        sf.write_cfg(self.repo, cfg)
        shutil.rmtree(self.tmp / 'skill')
        skill = sf.make_skill(self.tmp, version='2.1.0')
        before = snapshot(self.repo)
        code, env = self.migrate('--execute', '--actor-name', 'Bia', '--actor-email', 'bia@example.test', skill=skill)
        self.assertEqual((code, env['status']), (1, 'NOT_PROMOTER'))
        self.assertEqual(snapshot(self.repo), before)

    def test_nunca_toca_no_git(self):
        helpers.run(['git', 'init', '-q', '-b', 'main', str(self.repo)])
        self.legacy(False)
        self.execute(ANSWERS_SOLO, *ACTOR)
        log = subprocess.run(['git', '-C', str(self.repo), 'log', '--oneline'], capture_output=True, text=True)
        self.assertNotEqual(log.returncode, 0)  # nenhum commit criado
        status = subprocess.run(['git', '-C', str(self.repo), 'status', '--porcelain'], capture_output=True, text=True).stdout
        self.assertIn('prototype.config.json', status)

    def test_sem_arquivos_temporarios_residuais(self):
        self.legacy(False)
        self.execute(ANSWERS_SOLO, *ACTOR)
        self.assertEqual([p.name for p in self.repo.iterdir() if p.name.endswith('.tmp')], [])


if __name__ == '__main__':
    unittest.main()
