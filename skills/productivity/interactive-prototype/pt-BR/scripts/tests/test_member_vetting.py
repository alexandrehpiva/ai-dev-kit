"""Testes de member-vetting.py: repo de promoter + remoto bare local + clones de outras pessoas."""

import json
import os
import shutil
import unittest
from datetime import datetime, timedelta, timezone

from helpers import SCRIPTS, TmpDirMixin, clone, commit_all, make_repo, run, run_script, write

import protolib as pl

SCRIPT = 'member-vetting.py'
ANA = ('Ana Teste', 'ana@example.test')
BRUNO = ('Bruno Teste', 'bruno@example.test')
CARLA = ('Carla Teste', 'carla@example.test')
HOME_V1 = 'const HOME_TITLE = "Início";\n\n// bloco de textos\n\n// fim do bloco\n\nconst HOME_TEXT = "Olá";\n'
HOME_BRUNO = HOME_V1.replace('"Olá"', '"Olá, pessoa"')
CHANGELOG_JS = """const CHANGELOG = [
  { version: 'v0.1.0-beta.1', date: '2026-01-02', changes: [
    'Tela inicial',
  ] },
  { version: 'v0.1.0', date: '2026-01-01', changes: [
    'Esqueleto',
  ] },
];
"""
ROLLBACK_LINE = 'Revertido: trabalho de membro não aprovado'


def git(repo, *args):
    return run(['git', '-C', str(repo), *args]).stdout.strip()


def member(name, email, status, roles, at='2026-01-01T00:00:00Z', commit=None):
    return {'name': name, 'email': email, 'roles': roles, 'profile': 'product', 'status': status,
            'registeredAt': at, 'statusChangedAt': at, 'statusChangedAtCommit': commit,
            'statusHistory': [{'status': status, 'at': at, 'commit': commit, 'by': 'setup'}],
            'identityEvidence': 'git-only'}


def commit_trailers(repo, message, actor):
    run(['git', '-C', str(repo), 'add', '-A'])
    msg = f'{message}\n\n{pl.T_ACTOR}: {actor}\n{pl.T_MEMBER_STATUS}: pending\n'
    run(['git', '-C', str(repo), 'commit', '-q', '-m', msg])
    return git(repo, 'rev-parse', 'HEAD')


def trailers(repo, ref='HEAD'):
    return pl.parse_trailers(git(repo, 'log', '-1', '--format=%B', ref))


def cfg_at(repo, ref):
    return json.loads(git(repo, 'show', f'{ref}:{pl.CONFIG_NAME}'))


FAKE_SCAN = """import json, re, sys
from pathlib import Path
repo = Path(sys.argv[sys.argv.index('--repo') + 1])
probs = []
for f in sorted(repo.glob('js/**/*.js')):
    text = f.read_text(encoding='utf-8')
    if 'TODO-SCAN' in text:
        probs.append({'code': 'LINT', 'message': f'pendência em {f.relative_to(repo)}'})
    for ref in re.findall(r'@uses (\\S+)', text):
        if not (repo / ref).exists():
            probs.append({'code': 'RULES', 'message': f'{f.relative_to(repo)} usa {ref}, que não existe'})
print(json.dumps({'ok': not probs, 'status': 'ISSUES' if probs else 'CLEAN', 'data': {}, 'problems': probs}))
sys.exit(1 if probs else 0)
"""


class MemberVettingTest(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._env = os.environ.get('MEMBER_VETTING_COMPONENT_SCAN')
        os.environ['MEMBER_VETTING_COMPONENT_SCAN'] = ''  # isola do component-scan real da skill
        self.ana, self.remote = make_repo(self.tmp, user=ANA)
        cfg = dict(pl.DEFAULT_CONFIG, skill={'name': pl.SKILL_NAME, 'version': '2.0.0'}, groupMode=True,
                   policy={'promoters': 'listed', 'requireSignedCommits': False, 'pendingExpiryDays': 7},
                   members=[member(*ANA, 'approved', ['promoter']), member(*CARLA, 'approved', ['contributor'])])
        write(self.ana / '.gitignore', 'dist/\n')
        shutil.copy(SCRIPTS.parent / 'templates' / 'build.py', self.ana / 'build.py')
        write(self.ana / 'index.html', '<html><body>\n<script src="js/screens/home.js"></script>\n</body></html>\n')
        write(self.ana / 'js/screens/home.js', HOME_V1)
        write(self.ana / 'js/components/changelog-modal.js', CHANGELOG_JS)
        write(self.ana / pl.CONFIG_NAME, json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
        commit_all(self.ana, 'chore: base')
        git(self.ana, 'push', '-q', 'origin', 'main')
        git(self.ana, 'switch', '-q', '-c', 'beta')
        git(self.ana, 'push', '-q', '-u', 'origin', 'beta')

        self.bruno = self.clone_beta('bruno', BRUNO)
        self.carla = self.clone_beta('carla', CARLA)
        # registro pendente do Bruno (âncora = HEAD da beta antes do registro)
        days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        cfg = json.loads((self.bruno / pl.CONFIG_NAME).read_text(encoding='utf-8'))
        cfg['members'].append(member(*BRUNO, 'pending', ['contributor'], days_ago, git(self.bruno, 'rev-parse', 'HEAD')))
        write(self.bruno / pl.CONFIG_NAME, json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
        self.b_reg = commit_trailers(self.bruno, 'chore(roster): registra bruno', BRUNO[1])
        write(self.bruno / 'js/components/card.js', 'function card(){ return "<div></div>"; }\n')
        self.b1 = commit_trailers(self.bruno, 'feat: card', BRUNO[1])
        write(self.bruno / 'js/screens/home.js', HOME_BRUNO)
        self.b2 = commit_all(self.bruno, 'feat: texto da home')  # sem trailer: vale o autor
        git(self.bruno, 'push', '-q', 'origin', 'beta')
        self.sync(self.ana)

    def tearDown(self):
        if self._env is None:
            os.environ.pop('MEMBER_VETTING_COMPONENT_SCAN', None)
        else:
            os.environ['MEMBER_VETTING_COMPONENT_SCAN'] = self._env
        super().tearDown()

    # -- utilidades
    def clone_beta(self, name, user):
        repo = clone(self.remote, self.tmp / name, user)
        git(repo, 'switch', '-q', 'beta')
        return repo

    def sync(self, repo):
        git(repo, 'pull', '-q', '--ff-only', 'origin', 'beta')

    def vet(self, *args, actor=ANA[1], repo=None):
        return run_script(SCRIPT, '--repo', repo or self.ana, '--actor-email', actor, *args)

    def promote(self, sha):
        git(self.ana, 'push', '-q', 'origin', f'{sha}:refs/heads/main')
        git(self.ana, 'fetch', '-q', 'origin')

    def carla_edits(self, path, text, msg):
        self.sync(self.carla)
        write(self.carla / path, text)
        sha = commit_trailers(self.carla, msg, CARLA[1])
        git(self.carla, 'push', '-q', 'origin', 'beta')
        self.sync(self.ana)
        return sha

    def assert_clean_at(self, head):
        self.assertEqual(git(self.ana, 'rev-parse', 'HEAD'), head)
        self.assertEqual(git(self.ana, 'status', '--porcelain'), '')
        self.assertEqual(git(self.ana, 'rev-parse', 'origin/beta'), head)
        self.assertFalse((self.ana / '.git' / 'prototype-member-vetting.json').exists())

    # -- testes
    def test_list_shows_pending_with_expiry(self):
        code, env, out, err = self.vet('list')
        self.assertEqual(code, 0, out + err)
        self.assertEqual([p['email'] for p in env['data']['pending']], [BRUNO[1]])
        self.assertGreaterEqual(env['data']['pending'][0]['daysPending'], 10)
        self.assertTrue(env['data']['pending'][0]['expired'])

    def test_only_approved_promoter_decides(self):
        for actor, repo in ((BRUNO[1], self.bruno), (CARLA[1], self.carla)):
            code, env, _, _ = self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor', '--execute',
                                       actor=actor, repo=repo)
            self.assertEqual((code, env['status']), (1, 'NOT_PROMOTER'))

    def test_report_groups_beta_only_official_and_dependents(self):
        self.promote(self.b1)
        c1 = self.carla_edits('js/screens/home.js', HOME_BRUNO + 'const HOME_FOOT = "Rodapé";\n', 'feat: rodapé')
        code, env, out, _ = self.vet('report', '--email', BRUNO[1])
        self.assertEqual(code, 0, out)
        d = env['data']
        self.assertEqual([c['sha'] for c in d['betaOnly']], [self.b2])
        self.assertEqual([c['sha'] for c in d['inOfficial']], [self.b1])
        self.assertTrue(d['inOfficial'][0]['inOfficial'] and d['betaOnly'][0]['betaOnly'])
        self.assertEqual(d['betaOnly'][0]['files'], ['js/screens/home.js'])
        self.assertEqual([c['sha'] for c in d['rosterOnly']], [self.b_reg])
        self.assertEqual([(c['sha'], c['files']) for c in d['dependents']], [(c1, ['js/screens/home.js'])])
        self.assertEqual(d['member']['identityEvidence'], 'git-only')
        self.assertIn('registeredAt', d['member'])

    def test_approve_dry_run_then_execute(self):
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'), out)
        self.assert_clean_at(head)
        code, env, out, _ = self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor', '--execute')
        self.assertEqual((code, env['status']), (0, 'APPROVED'), out)
        git(self.ana, 'fetch', '-q', 'origin')
        self.assertEqual(git(self.ana, 'rev-parse', 'origin/beta'), env['data']['commit'])
        self.assertEqual(git(self.ana, 'rev-parse', 'HEAD^'), head)
        m = pl.find_member(cfg_at(self.ana, 'origin/beta'), BRUNO[1])
        self.assertEqual((m['status'], m['roles'], m['decidedBy']), ('approved', ['contributor'], ANA[1]))
        self.assertEqual(m['statusChangedAtCommit'], head)
        self.assertEqual(m['statusHistory'][-1]['commit'], head)
        self.assertEqual(len(m['statusHistory']), 2)
        t = trailers(self.ana)
        self.assertEqual((t[pl.T_ACTOR], t[pl.T_MEMBER_STATUS]), (ANA[1], 'approved'))

    def test_reject_clean_rollback_keeps_official_items(self):
        self.promote(self.b1)
        main_before = git(self.ana, 'rev-parse', 'origin/main')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'não identificado')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'), out)
        self.assertEqual(env['data']['plan']['simulation']['prediction'], 'OK')
        self.assert_clean_at(head)
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'não identificado', '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertFalse(env['data']['requiresPromotion'])
        self.assertEqual(git(self.ana, 'rev-parse', 'HEAD^'), head)  # um único commit
        self.assertEqual((self.ana / 'js/screens/home.js').read_text(encoding='utf-8'), HOME_V1)
        self.assertTrue((self.ana / 'js/components/card.js').exists())  # já na oficial: intocado
        t = trailers(self.ana)
        self.assertEqual(t[pl.T_ROLLBACK_OF], self.b2)
        self.assertEqual(t[pl.T_ROLLBACK_REASON], 'não identificado')
        self.assertEqual(t['Prototype-Rollback-Member'], BRUNO[1])
        self.assertEqual(t[pl.T_ACTOR], ANA[1])
        m = pl.find_member(cfg_at(self.ana, 'HEAD'), BRUNO[1])
        self.assertEqual((m['status'], m['reason'], m['statusChangedAtCommit']), ('rejected', 'não identificado', head))
        self.assertEqual([h['status'] for h in m['statusHistory']], ['pending', 'rejected'])
        self.assert_clean_at(git(self.ana, 'rev-parse', 'HEAD'))
        self.assertEqual(git(self.ana, 'rev-parse', 'origin/main'), main_before)

    def test_reject_with_rollback_main_items_requires_promotion(self):
        self.promote(self.b1)
        main_before = git(self.ana, 'rev-parse', 'origin/main')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--rollback-main-items',
                                     '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertTrue(env['data']['requiresPromotion'])
        self.assertEqual(trailers(self.ana)[pl.T_ROLLBACK_OF], f'{self.b2},{self.b1}')  # inversa cronológica
        self.assertFalse((self.ana / 'js/components/card.js').exists())
        self.assertEqual(git(self.ana, 'rev-parse', 'origin/main'), main_before)

    def test_conflict_aborts_and_restores(self):
        c1 = self.carla_edits('js/screens/home.js', HOME_BRUNO.replace('pessoa', 'pessoa querida'), 'feat: texto')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r')
        self.assertEqual(env['data']['plan']['simulation']['prediction'], 'CONFLICT', out)
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--ack-dependents',
                                     '--execute')
        self.assertEqual((code, env['status']), (1, 'CONFLICT'), out)
        self.assertEqual(env['data']['conflictFiles'], ['js/screens/home.js'])
        self.assertEqual(env['data']['conflictCommit'], self.b2)
        self.assertEqual({c['sha'] for c in env['data']['involvedCommits']}, {self.b2, c1})
        self.assertEqual([c['sha'] for c in env['data']['dependents']], [c1])
        self.assert_clean_at(head)

    def test_conflict_left_then_finalize(self):
        self.carla_edits('js/screens/home.js', HOME_BRUNO.replace('pessoa', 'pessoa querida'), 'feat: texto')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--leave-conflicts',
                                     '--ack-dependents', '--execute')
        self.assertEqual((code, env['status']), (1, 'CONFLICT_LEFT'), out)
        self.assertIn('<<<<<<< ', (self.ana / 'js/screens/home.js').read_text(encoding='utf-8'))
        code, env, _, _ = self.vet('finalize', '--email', BRUNO[1], '--execute')
        self.assertEqual((code, env['status']), (1, 'UNRESOLVED_CONFLICTS'))
        write(self.ana / 'js/screens/home.js', HOME_V1.replace('Olá', 'Olá, querida'))
        code, env, out, _ = self.vet('finalize', '--email', BRUNO[1], '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertEqual(git(self.ana, 'rev-parse', 'HEAD^'), head)
        self.assertEqual(trailers(self.ana)[pl.T_ROLLBACK_OF], f'{self.b2},{self.b1}')  # b1 continuou após o conflito
        self.assertFalse((self.ana / 'js/components/card.js').exists())
        self.assertEqual(pl.find_member(cfg_at(self.ana, 'HEAD'), BRUNO[1])['status'], 'rejected')
        self.assert_clean_at(git(self.ana, 'rev-parse', 'HEAD'))

    def test_dependents_stop_rollback_until_ack(self):
        c1 = self.carla_edits('js/screens/home.js', HOME_BRUNO.replace('Início', 'Começo'), 'feat: título')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'), out)
        self.assertTrue(env['data']['requiresAck'])
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (1, 'DEPENDENTS_FOUND'), out)
        dep = env['data']['dependents']
        self.assertEqual([(d['sha'], d['authorEmail'], d['subject'], d['commonFiles']) for d in dep],
                         [(c1, CARLA[1], 'feat: título', ['js/screens/home.js'])])
        self.assert_clean_at(head)
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--ack-dependents', '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertEqual((self.ana / 'js/screens/home.js').read_text(encoding='utf-8'),
                         HOME_V1.replace('Início', 'Começo'))

    def test_rollback_adds_anonymous_changelog_line(self):
        self.sync(self.bruno)
        write(self.bruno / 'js/components/changelog-modal.js', CHANGELOG_JS.replace(
            "    'Tela inicial',\n", "    'Tela inicial',\n    'Card novo',\n"))
        commit_trailers(self.bruno, 'docs: changelog do card', BRUNO[1])
        git(self.bruno, 'push', '-q', 'origin', 'beta')
        self.carla_edits('js/components/changelog-modal.js', CHANGELOG_JS.replace(
            "    'Tela inicial',\n", "    'Tela inicial',\n    'Card novo',\n    'Rodapé',\n"), 'docs: changelog')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)  # changelog não gera dependente
        self.assertTrue(env['data']['changelogUpdated'])
        import changelog_tools as ct
        entries = ct.read_entries(self.ana)
        self.assertEqual(entries[0]['version'], 'v0.1.0-beta.1')
        self.assertEqual(entries[0]['changes'], ['Tela inicial', 'Rodapé', ROLLBACK_LINE])
        text = (self.ana / 'js/components/changelog-modal.js').read_text(encoding='utf-8').lower()
        self.assertNotIn('bruno', text)
        self.assert_clean_at(git(self.ana, 'rev-parse', 'HEAD'))

    def test_rollback_without_changelog_file_skips(self):
        git(self.ana, 'rm', '-q', 'js/components/changelog-modal.js')
        git(self.ana, 'commit', '-q', '-m', 'chore: sem changelog')
        git(self.ana, 'push', '-q', 'origin', 'beta')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertFalse(env['data']['changelogUpdated'])

    def test_broken_dependents_commit_nothing(self):
        self.sync(self.bruno)
        write(self.bruno / 'js/feature.js', 'function feature(){}\n')
        commit_trailers(self.bruno, 'feat: peça', BRUNO[1])
        git(self.bruno, 'push', '-q', 'origin', 'beta')
        self.carla_edits('index.html', '<html><body>\n<script src="js/screens/home.js"></script>\n'
                         '<script src="js/feature.js"></script>\n</body></html>\n', 'feat: usa a peça')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (1, 'DEPENDENTS_BROKEN'), out)
        self.assertEqual(env['problems'][0]['code'], 'BUILD_FAILED')
        self.assertTrue((self.ana / 'js/feature.js').exists())
        self.assert_clean_at(head)

    def use_fake_scan(self):
        path = self.tmp / 'fake-scan.py'
        write(path, FAKE_SCAN)
        os.environ['MEMBER_VETTING_COMPONENT_SCAN'] = str(path)

    def test_component_scan_preexisting_problems_do_not_block(self):
        self.use_fake_scan()
        self.carla_edits('js/legacy.js', '// TODO-SCAN\n', 'chore: legado')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (0, 'REJECTED'), out)
        self.assertIn('COMPONENT_SCAN_PREEXISTING', [n['code'] for n in env['data']['notes']])

    def test_component_scan_new_problem_blocks(self):
        self.use_fake_scan()
        self.carla_edits('js/screens/extra.js', '// @uses js/components/card.js\n', 'feat: usa o card')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r')
        self.assertEqual(env['data']['plan']['simulation']['prediction'], 'DEPENDENTS_BROKEN', out)
        code, env, out, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.assertEqual((code, env['status']), (1, 'DEPENDENTS_BROKEN'), out)
        self.assertEqual(env['problems'][0]['code'], 'COMPONENT_SCAN_FAILED')
        self.assert_clean_at(head)

    def test_reinstate_restores_work_and_history(self):
        self.vet('reject', '--email', BRUNO[1], '--reason', 'engano', '--execute')
        rollback = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reinstate', '--email', BRUNO[1], '--execute')
        self.assertEqual((code, env['status']), (0, 'REINSTATED'), out)
        self.assertEqual((self.ana / 'js/screens/home.js').read_text(encoding='utf-8'), HOME_BRUNO)
        self.assertTrue((self.ana / 'js/components/card.js').exists())
        self.assertEqual(trailers(self.ana)['Prototype-Reinstate-Of'], rollback)
        m = pl.find_member(cfg_at(self.ana, 'HEAD'), BRUNO[1])
        self.assertEqual((m['status'], m['roles']), ('approved', ['contributor']))
        self.assertEqual([h['status'] for h in m['statusHistory']], ['pending', 'rejected', 'approved'])
        self.assert_clean_at(git(self.ana, 'rev-parse', 'HEAD'))

    def test_reinstate_conflict_restores(self):
        self.vet('reject', '--email', BRUNO[1], '--reason', 'r', '--execute')
        self.carla_edits('js/screens/home.js', HOME_V1.replace('Olá', 'Oi'), 'feat: saudação')
        head = git(self.ana, 'rev-parse', 'HEAD')
        code, env, out, _ = self.vet('reinstate', '--email', BRUNO[1], '--execute')
        self.assertEqual((code, env['status']), (1, 'CONFLICT'), out)
        self.assertEqual(env['data']['conflictKind'], 'cherry-pick')  # tentou reaplicar os originais
        self.assert_clean_at(head)

    def test_blocks_dirty_worktree_and_stale_beta(self):
        write(self.ana / 'rascunho.txt', 'x')
        code, env, _, _ = self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor', '--execute')
        self.assertEqual((code, env['status']), (1, 'DIRTY_WORKTREE'))
        (self.ana / 'rascunho.txt').unlink()
        self.sync(self.carla)
        write(self.carla / 'notas.md', 'x\n')
        commit_trailers(self.carla, 'docs: notas', CARLA[1])
        git(self.carla, 'push', '-q', 'origin', 'beta')
        code, env, _, _ = self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor', '--execute')
        self.assertEqual((code, env['status']), (1, 'BETA_OUT_OF_SYNC'))

    def test_revoke_needs_cutoff(self):
        self.vet('approve', '--email', BRUNO[1], '--roles', 'contributor', '--execute')
        code, env, _, _ = self.vet('reject', '--email', BRUNO[1], '--reason', 'saiu', '--execute')
        self.assertEqual((code, env['status']), (1, 'NEEDS_CUTOFF'))


if __name__ == '__main__':
    unittest.main()
