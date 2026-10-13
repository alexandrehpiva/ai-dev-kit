import json
import os
import stat
import unittest
from pathlib import Path

from group_fixtures import (ANA, BIA, CAIO, DANI, add_pending, commit_body, git_out, make_group_repo,
                            member_clone, remote_entries, remote_file, remote_sha)
from helpers import TmpDirMixin, commit_all, run, run_script, write

import changelog_tools as ct
import protolib

SHARE = 'group-share.py'
PEND = protolib.CHANGELOG_PENDING


def share(repo, user, *extra):
    return run_script(SHARE, '--repo', repo, '--actor-email', user[1], *extra)


class ShareBase(TmpDirMixin):
    def setUp(self):
        super().setUp()
        self.origin_repo, self.remote = make_group_repo(self.tmp)
        self.a = member_clone(self.remote, self.tmp, ANA)
        self.b = member_clone(self.remote, self.tmp, BIA)

    def edit_screen(self, repo, text, rel='js/screens/a.js'):
        p = Path(repo) / rel
        write(p, p.read_text(encoding='utf-8').replace("'titulo original'", text) if p.exists() else text)


class DryRun(ShareBase, unittest.TestCase):
    def test_given_changes_when_dry_run_then_returns_plan_and_writes_nothing(self):
        self.edit_screen(self.b, "'titulo da bia'")
        add_pending(self.b, 'Muda o título da tela A.')
        before = (git_out(self.b, 'status', '--porcelain'), git_out(self.b, 'for-each-ref'))
        code, env, out, err = share(self.b, BIA)
        self.assertEqual(code, 0, err + out)
        plan = env['data']['plan']
        self.assertEqual(env['status'], 'DRY_RUN')
        self.assertEqual(plan['draftBranch'], 'draft/bia')
        self.assertEqual(plan['betaVersion'], 'v1.0.0-beta.1')
        self.assertIn('js/screens/a.js', plan['filesToCommit'])
        self.assertEqual(plan['pendingChanges'], ['Muda o título da tela A.'])
        self.assertTrue(plan['remoteTrackingFresh'])
        self.assertEqual(before, (git_out(self.b, 'status', '--porcelain'), git_out(self.b, 'for-each-ref')))


class Permissions(ShareBase, unittest.TestCase):
    def test_rejected_and_unknown_members_are_refused(self):
        for email in (DANI[1], 'ninguem@example.test'):
            code, env, _, _ = run_script(SHARE, '--repo', self.b, '--actor-email', email)
            self.assertEqual(code, 1)
            self.assertEqual(env['status'], 'NOT_ALLOWED')

    def test_pending_member_can_share(self):
        code, env, _, _ = share(self.b, CAIO)
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'))

    def test_promoter_with_pending_members_needs_vetting_done(self):
        code, env, _, _ = share(self.a, ANA)
        self.assertEqual((code, env['status']), (1, 'VETTING_REQUIRED'))
        self.assertEqual(env['data']['pendingMembers'], [CAIO[1]])
        code, env, _, _ = share(self.a, ANA, '--vetting-done')
        self.assertEqual((code, env['status']), (0, 'DRY_RUN'))

    def test_legacy_config_is_refused(self):
        write(self.b / protolib.CONFIG_NAME, json.dumps({'groupMode': True, 'sharedBranch': 'main'}))
        code, env, _, _ = share(self.b, BIA)
        self.assertEqual(env['status'], 'INVALID_CONFIG')
        self.assertEqual(env['problems'][0]['code'], 'CONFIG_LEGACY')


class Execute(ShareBase, unittest.TestCase):
    def test_given_batch_when_shared_then_beta_gets_numbered_version_and_trailers(self):
        self.edit_screen(self.b, "'titulo da bia'")
        add_pending(self.b, 'Muda o título da tela A.')
        code, env, out, err = share(self.b, BIA, '--execute')
        self.assertEqual(code, 0, out + err)
        d = env['data']
        self.assertEqual(env['status'], 'SHARED')
        self.assertEqual(d['version'], 'v1.0.0-beta.1')
        self.assertEqual(d['identityEvidence'], 'git-only')
        self.assertEqual([a['id'] for a in d['artifactsToUpdate']], ['beta'])
        self.assertEqual(remote_sha(self.remote, 'beta'), d['betaSha'])
        self.assertEqual(remote_sha(self.remote, 'draft/bia'), d['betaSha'])
        entries = remote_entries(self.remote, 'beta')
        self.assertEqual(entries[0], {'version': 'v1.0.0-beta.1', 'date': entries[0]['date'],
                                      'changes': ['Muda o título da tela A.']})
        self.assertNotIn(PEND, [e['version'] for e in entries])
        self.assertIn('v1.0.0-beta.1 · protótipo', remote_file(self.remote, 'beta', 'index.html'))
        self.assertIn('titulo da bia', remote_file(self.remote, 'beta', 'js/screens/a.js'))
        bump = protolib.parse_trailers(commit_body(self.remote, 'beta'))
        batch = protolib.parse_trailers(commit_body(self.remote, 'beta~1'))
        for tr in (bump, batch):
            self.assertEqual(tr[protolib.T_ACTOR], BIA[1])
            self.assertEqual(tr[protolib.T_MEMBER_STATUS], 'approved')
            self.assertEqual(tr[protolib.T_IDENTITY], 'git-only')
        self.assertTrue(commit_body(self.remote, 'beta').startswith('chore(prototype): bump version to v1.0.0-beta.1'))
        self.assertEqual(remote_sha(self.remote, 'main'), git_out(self.origin_repo, 'rev-parse', 'main'))
        self.assertTrue((self.b / 'dist' / 'index.html').exists())
        self.assertNotIn('dist/', git_out(self.b, 'ls-files'))

    def test_two_clones_share_concurrently_changelog_resolved_mechanically(self):
        write(self.a / 'js/screens/nova-a.js', '// tela nova da Ana\n')
        add_pending(self.a, 'Tela nova da Ana.')
        write(self.b / 'js/screens/nova-b.js', '// tela nova da Bia\n')
        add_pending(self.b, 'Tela nova da Bia.')
        code, env_a, out, err = share(self.a, ANA, '--execute', '--vetting-done')
        self.assertEqual(code, 0, out + err)
        code, env_b, out, err = share(self.b, BIA, '--execute')
        self.assertEqual(code, 0, out + err)
        self.assertEqual(env_a['data']['version'], 'v1.0.0-beta.1')
        self.assertEqual(env_b['data']['version'], 'v1.0.0-beta.2')
        self.assertIn(ct.CHANGELOG_REL, [r['path'] for r in env_b['data']['autoResolved']])
        entries = remote_entries(self.remote, 'beta')
        self.assertEqual([(e['version'], e['changes']) for e in entries],
                         [('v1.0.0-beta.2', ['Tela nova da Bia.']), ('v1.0.0-beta.1', ['Tela nova da Ana.']),
                          ('v1.0.0', ['Primeira versão oficial.'])])
        self.assertIn('v1.0.0-beta.2 · protótipo', remote_file(self.remote, 'beta', 'index.html'))
        for rel in ('js/screens/nova-a.js', 'js/screens/nova-b.js'):
            self.assertTrue(remote_file(self.remote, 'beta', rel))

    def test_perceptible_conflict_aborts_merge_and_reports_both_sides(self):
        self.edit_screen(self.a, "'titulo da ana'")
        add_pending(self.a, 'Título da Ana.')
        self.assertEqual(share(self.a, ANA, '--execute', '--vetting-done')[0], 0)
        beta_before = remote_sha(self.remote, 'beta')
        self.edit_screen(self.b, "'titulo da bia'")
        add_pending(self.b, 'Título da Bia.')
        code, env, out, err = share(self.b, BIA, '--execute')
        self.assertEqual((code, env['status']), (1, 'CONFLICTS'), out + err)
        conflicts = env['data']['conflicts']
        self.assertEqual([c['path'] for c in conflicts], ['js/screens/a.js'])
        self.assertEqual(conflicts[0]['ours']['actor'], BIA[1])
        self.assertEqual(conflicts[0]['theirs']['actor'], ANA[1])
        self.assertTrue(env['questions'])
        self.assertFalse((self.b / '.git' / 'MERGE_HEAD').exists())
        self.assertEqual(git_out(self.b, 'status', '--porcelain'), '')
        self.assertEqual(remote_sha(self.remote, 'beta'), beta_before)
        self.assertEqual(ct.read_entries(self.b)[0]['version'], PEND)

    def _conflict_setup(self):
        self.edit_screen(self.a, "'titulo da ana'")
        add_pending(self.a, 'Título da Ana.')
        self.assertEqual(share(self.a, ANA, '--execute', '--vetting-done')[0], 0)
        self.edit_screen(self.b, "'titulo da bia'")
        add_pending(self.b, 'Título da Bia.')

    def _decisions_file(self, keep, what='ordem do titulo; ver | depois'):
        path = Path(self.tmp) / f'decisions-{keep}.json'
        path.write_text(json.dumps({'decisions': [{'path': 'js/screens/a.js', 'keep': keep, 'what': what}]}),
                        encoding='utf-8')
        return str(path)

    def test_given_user_decision_when_sharing_then_merge_keeps_chosen_side_and_records_trailer(self):
        self._conflict_setup()
        code, env, out, err = share(self.b, BIA, '--execute', '--decisions', self._decisions_file('theirs'))
        self.assertEqual((code, env['status']), (0, 'SHARED'), out + err)
        self.assertIn('titulo da ana', remote_file(self.remote, 'beta', 'js/screens/a.js'))
        decided = env['data']['decidedConflicts'][0]
        self.assertEqual((decided['kept'], decided['dropped']), (ANA[1], BIA[1]))
        trailer = git_out(self.b, 'log', '--merges', '-1', '--format=%(trailers:key=Prototype-Conflict-Decision,'
                          'valueonly)').strip()
        self.assertIn(f'kept={ANA[1]}; dropped={BIA[1]}; by={BIA[1]}', trailer)
        self.assertNotIn('|', trailer.split('what=')[1])

    def test_given_decision_keep_mine_then_own_version_wins(self):
        self._conflict_setup()
        code, env, out, err = share(self.b, BIA, '--execute', '--decisions', self._decisions_file('mine'))
        self.assertEqual((code, env['status']), (0, 'SHARED'), out + err)
        self.assertIn('titulo da bia', remote_file(self.remote, 'beta', 'js/screens/a.js'))

    def test_given_decision_then_non_conflicting_changes_of_dropped_side_are_kept(self):
        a_file = Path(self.a) / 'js/screens/a.js'
        a_file.write_text(a_file.read_text(encoding='utf-8').replace("'titulo original'", "'titulo da ana'")
                          + "\nfunction ajudaDaAna() {}\n", encoding='utf-8')
        add_pending(self.a, 'Título e ajuda da Ana.')
        self.assertEqual(share(self.a, ANA, '--execute', '--vetting-done')[0], 0)
        self.edit_screen(self.b, "'titulo da bia'")
        add_pending(self.b, 'Título da Bia.')
        code, env, out, err = share(self.b, BIA, '--execute', '--decisions', self._decisions_file('mine'))
        self.assertEqual((code, env['status']), (0, 'SHARED'), out + err)
        merged = remote_file(self.remote, 'beta', 'js/screens/a.js')
        self.assertIn('titulo da bia', merged)
        self.assertNotIn('titulo da ana', merged)
        self.assertIn('ajudaDaAna', merged)
        self.assertEqual(env['data']['decidedConflicts'][0]['dropped'], ANA[1])

    def test_given_promoter_with_pending_members_then_save_only_is_not_blocked(self):
        self.edit_screen(self.a, "'titulo da ana'")
        add_pending(self.a, 'Título da Ana.')
        code, env, _, _ = share(self.a, ANA)
        self.assertEqual((code, env['status']), (1, 'VETTING_REQUIRED'))
        code, env, out, err = share(self.a, ANA, '--mode', 'save-only', '--execute')
        self.assertEqual((code, env['status']), (0, 'SAVED'), out + err)

    def _combined_file(self, name, text):
        path = Path(self.tmp) / name
        path.write_text(text, encoding='utf-8')
        return str(path)

    def _decisions_json(self, name, items):
        path = Path(self.tmp) / name
        path.write_text(json.dumps({'decisions': items}), encoding='utf-8')
        return str(path)

    def test_given_combined_decision_then_final_content_is_recorded_and_both_authors_are_listed(self):
        self._conflict_setup()
        final = self._combined_file('final-a.js', "'titulo combinado'\n")
        dec = self._decisions_json('combined.json', [{'path': 'js/screens/a.js', 'keep': 'combined',
                                                      'what': 'titulo combinado', 'file': final}])
        code, env, out, err = share(self.b, BIA, '--execute', '--decisions', dec)
        self.assertEqual((code, env['status']), (0, 'SHARED'), out + err)
        self.assertEqual(remote_file(self.remote, 'beta', 'js/screens/a.js').strip(), "'titulo combinado'")
        decided = env['data']['decidedConflicts'][0]
        self.assertEqual((decided['keep'], decided['dropped']), ('combined', ANA[1]))

    def _config_conflict_setup(self, first, second, first_value, second_value):
        """`first` compartilha primeiro; `second` fica com o mesmo campo do config diferente (conflito)."""
        for (repo, user), value in (((first), first_value), ((second), second_value)):
            cfg_path = Path(repo) / 'prototype.config.json'
            cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
            cfg['policy']['pendingExpiryDays'] = value
            cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            add_pending(repo, f'Prazo {value}.')
            if (repo, user) == first:
                self.assertEqual(share(repo, user, '--execute', '--vetting-done')[0], 0)

    def _config_decision(self, repo, name, mutate=None, keep='combined'):
        cfg = json.loads((Path(repo) / 'prototype.config.json').read_text(encoding='utf-8'))
        cfg['policy']['pendingExpiryDays'] = 4
        if mutate:
            mutate(cfg)
        final = self._combined_file(f'{name}-final.json', json.dumps(cfg, indent=2, ensure_ascii=False) + '\n')
        return self._decisions_json(f'{name}.json', [{'path': 'prototype.config.json', 'keep': keep,
                                                      'what': 'prazo 4 dias', 'file': final}])

    def test_given_same_config_key_changed_on_both_sides_then_decision_mine_is_ignored(self):
        self._config_conflict_setup((self.a, ANA), (self.b, BIA), 3, 5)
        dec = self._decisions_json('cfg-mine.json', [{'path': 'prototype.config.json', 'keep': 'mine', 'what': 'x'}])
        code, env, _, _ = share(self.b, BIA, '--execute', '--decisions', dec)
        self.assertEqual((code, env['status']), (1, 'CONFLICTS'))
        self.assertEqual([c['path'] for c in env['data']['conflicts']], ['prototype.config.json'])
        self.assertIn('combined', ' '.join(env['questions']))

    def test_given_contributor_combined_config_then_conflict_remains(self):
        self._config_conflict_setup((self.a, ANA), (self.b, BIA), 3, 5)
        code, env, _, _ = share(self.b, BIA, '--execute', '--decisions', self._config_decision(self.b, 'contrib'))
        self.assertEqual((code, env['status']), (1, 'CONFLICTS'))

    def test_given_promoter_combined_config_then_share_continues_and_roster_comes_from_the_merge(self):
        self._config_conflict_setup((self.b, BIA), (self.a, ANA), 5, 3)

        def tamper(cfg):  # arquivo tenta reabrir o reprovado e apagar um membro
            for m in cfg['members']:
                if m['email'] == DANI[1]:
                    m['status'] = 'pending'
            cfg['members'] = [m for m in cfg['members'] if m['email'] != CAIO[1]]
        code, env, out, err = share(self.a, ANA, '--execute', '--vetting-done',
                                    '--decisions', self._config_decision(self.a, 'promoter', tamper))
        self.assertEqual((code, env['status']), (0, 'SHARED'), out + err)
        beta_cfg = json.loads(remote_file(self.remote, 'beta', 'prototype.config.json'))
        self.assertEqual(beta_cfg['policy']['pendingExpiryDays'], 4)
        by_email = {m['email']: m for m in beta_cfg['members']}
        self.assertEqual(by_email[DANI[1]]['status'], 'rejected')
        self.assertIn(CAIO[1], by_email)

    def test_given_invalid_decisions_file_then_refuses_without_touching_anything(self):
        self._conflict_setup()
        bad = Path(self.tmp) / 'bad.json'
        bad.write_text('{"decisions":[{"path":"js/screens/a.js","keep":"talvez","what":"x"}]}', encoding='utf-8')
        code, env, _, _ = share(self.b, BIA, '--execute', '--decisions', str(bad))
        self.assertEqual((code, env['status']), (1, 'INVALID_DECISIONS'))

    def test_given_decision_for_other_file_then_conflict_still_reported(self):
        self._conflict_setup()
        other = Path(self.tmp) / 'other.json'
        other.write_text('{"decisions":[{"path":"js/screens/outra.js","keep":"mine","what":"x"}]}', encoding='utf-8')
        code, env, _, _ = share(self.b, BIA, '--execute', '--decisions', str(other))
        self.assertEqual((code, env['status']), (1, 'CONFLICTS'))

    def test_given_recorded_decision_then_affected_person_finds_it(self):
        self._conflict_setup()
        self.assertEqual(share(self.b, BIA, '--execute', '--decisions', self._decisions_file('theirs'))[0], 0)
        code, env, out, err = run_script('conflict-decisions.py', '--repo', self.b, '--actor-email', BIA[1])
        self.assertEqual((code, env['status']), (0, 'DECISIONS'), out + err)
        self.assertEqual(env['data']['decisions'][0]['keptBy'], ANA[1])
        code, env, _, _ = run_script('conflict-decisions.py', '--repo', self.b, '--actor-email', ANA[1])
        self.assertEqual((code, env['status']), (0, 'NONE'))

    def test_config_conflict_is_merged_mechanically(self):
        cfg_a = json.loads((self.a / protolib.CONFIG_NAME).read_text(encoding='utf-8'))
        cfg_a['artifacts'][1]['version'] = 'v1.0.0-beta.9'
        write(self.a / protolib.CONFIG_NAME, json.dumps(cfg_a, ensure_ascii=False, indent=2) + '\n')
        add_pending(self.a, 'Artefato beta atualizado.')
        self.assertEqual(share(self.a, ANA, '--execute', '--vetting-done')[0], 0)
        cfg_b = json.loads((self.b / protolib.CONFIG_NAME).read_text(encoding='utf-8'))
        cfg_b['artifacts'][1]['publishedAt'] = '2026-02-02T00:00:00Z'
        cfg_b['members'][2]['status'] = 'approved'
        cfg_b['members'][2]['statusChangedAt'] = '2026-02-02T00:00:00Z'
        write(self.b / protolib.CONFIG_NAME, json.dumps(cfg_b, ensure_ascii=False, indent=2) + '\n')
        add_pending(self.b, 'Caio aprovado.')
        code, env, out, err = share(self.b, BIA, '--execute')
        self.assertEqual(code, 0, out + err)
        merged = json.loads(remote_file(self.remote, 'beta', protolib.CONFIG_NAME))
        self.assertEqual(merged['artifacts'][1]['version'], 'v1.0.0-beta.9')
        self.assertEqual(merged['members'][2]['status'], 'approved')

    def test_save_only_pushes_draft_keeps_pending_and_leaves_beta(self):
        beta_before = remote_sha(self.remote, 'beta')
        self.edit_screen(self.b, "'rascunho'")
        add_pending(self.b, 'Rascunho em andamento.')
        code, env, out, err = share(self.b, BIA, '--mode', 'save-only', '--execute')
        self.assertEqual((code, env['status']), (0, 'SAVED'), out + err)
        self.assertNotIn('version', env['data'])
        self.assertEqual(remote_sha(self.remote, 'beta'), beta_before)
        self.assertEqual(remote_entries(self.remote, 'draft/bia')[0]['version'], PEND)

    def test_paths_limit_batch_and_dist_is_never_committed(self):
        self.edit_screen(self.b, "'so este'")
        write(self.b / 'js/screens/fora.js', '// fora do lote\n')
        write(self.b / 'dist/extra.txt', 'x')
        run(['git', '-C', str(self.b), 'add', '-f', 'dist/extra.txt'])
        add_pending(self.b, 'Só a tela A.')
        code, env, out, err = share(self.b, BIA, '--paths', 'js/screens/a.js', '--execute')
        self.assertEqual(code, 0, out + err)
        files = git_out(self.b, 'show', '--name-only', '--format=', env['data']['commitSha']).splitlines()
        self.assertEqual(sorted(files), ['js/components/changelog-modal.js', 'js/screens/a.js'])
        self.assertIn('?? js/screens/fora.js', git_out(self.b, 'status', '--porcelain'))

    def test_offline_commits_locally_without_version(self):
        run(['git', '-C', str(self.b), 'remote', 'set-url', 'origin', str(self.tmp / 'nao-existe.git')])
        self.edit_screen(self.b, "'offline'")
        add_pending(self.b, 'Feito sem rede.')
        code, env, out, err = share(self.b, BIA, '--execute')
        self.assertEqual((code, env['status']), (1, 'NOT_SYNCED'), out + err)
        self.assertNotIn('version', env['data'])
        self.assertEqual(git_out(self.b, 'rev-parse', '--abbrev-ref', 'HEAD'), 'draft/bia')
        self.assertEqual(git_out(self.b, 'rev-parse', 'HEAD'), env['data']['commitSha'])
        self.assertEqual(ct.read_entries(self.b)[0]['version'], PEND)
        self.assertIn('v1.0.0 · protótipo', (self.b / 'index.html').read_text(encoding='utf-8'))

    def test_push_race_retries_from_fetch_and_takes_next_number(self):
        # Clone C prepara um "share" concorrente que o hook de pre-push do A envia no meio do push do A.
        c = member_clone(self.remote, self.tmp, CAIO)
        run(['git', '-C', str(c), 'checkout', '-q', 'beta'])
        write(c / 'js/screens/caio.js', '// tela do Caio\n')
        prefix, entries, suffix = ct.parse_text((c / ct.CHANGELOG_REL).read_text(encoding='utf-8'))
        entries.insert(0, {'version': 'v1.0.0-beta.1', 'date': '2026-02-01', 'changes': ['Tela do Caio.']})
        write(c / ct.CHANGELOG_REL, ct.render_text(prefix, entries, suffix))
        commit_all(c, 'feat: tela do caio')
        marker = self.tmp / 'raced'
        hook = self.a / '.git' / 'hooks' / 'pre-push'
        write(hook, '#!/bin/sh\nunset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE\n'
                    f'if [ ! -f "{marker}" ]; then touch "{marker}"; '
                    f'git -C "{c}" push -q origin HEAD:refs/heads/beta; fi\nexit 0\n')
        os.chmod(hook, os.stat(hook).st_mode | stat.S_IEXEC)
        write(self.a / 'js/screens/ana.js', '// tela da Ana\n')
        add_pending(self.a, 'Tela da Ana.')
        code, env, out, err = share(self.a, ANA, '--execute', '--vetting-done')
        self.assertEqual(code, 0, out + err)
        self.assertEqual(env['data']['attempts'], 2)
        self.assertEqual(env['data']['version'], 'v1.0.0-beta.2')
        self.assertEqual([e['version'] for e in remote_entries(self.remote, 'beta')],
                         ['v1.0.0-beta.2', 'v1.0.0-beta.1', 'v1.0.0'])

    def test_max_retries_exhausted_reports_push_rejected(self):
        hook = self.a / '.git' / 'hooks' / 'pre-push'
        write(hook, '#!/bin/sh\necho "rejected by test hook" >&2\nexit 1\n')
        os.chmod(hook, os.stat(hook).st_mode | stat.S_IEXEC)
        add_pending(self.a, 'Qualquer coisa.')
        write(self.a / 'js/screens/x.js', '// x\n')
        code, env, out, err = share(self.a, ANA, '--execute', '--vetting-done', '--max-retries', '1')
        self.assertEqual((code, env['status']), (1, 'PUSH_REJECTED'), out + err)
        self.assertEqual(env['data']['attempts'], 2)
        self.assertEqual(ct.read_entries(self.a)[0]['version'], PEND)


if __name__ == '__main__':
    unittest.main()
