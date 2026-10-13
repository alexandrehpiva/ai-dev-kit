import json
import unittest

from helpers import SCRIPTS, TmpDirMixin, write

import changelog_tools as ct
import protolib

PEND = protolib.CHANGELOG_PENDING
TEMPLATE_JS = (SCRIPTS.parent / 'templates' / ct.CHANGELOG_REL).read_text(encoding='utf-8')


def E(version, *changes, date='2026-01-01'):
    return {'version': version, 'date': date, 'changes': list(changes)}


class ParseAndRender(TmpDirMixin, unittest.TestCase):
    def test_given_template_when_parsed_then_reads_pending_entry(self):
        _, entries, _ = ct.parse_text(TEMPLATE_JS)
        self.assertEqual(entries[0]['version'], PEND)
        self.assertEqual(len(entries[0]['changes']), 1)

    def test_given_file_when_written_then_text_outside_array_is_byte_identical(self):
        repo = self.tmp
        original = TEMPLATE_JS.replace('\n', '\r\n', 3)  # inclui CRLF no prefixo
        (repo / 'js/components').mkdir(parents=True)
        with open(repo / ct.CHANGELOG_REL, 'w', encoding='utf-8', newline='') as f:
            f.write(original)
        prefix, _, suffix = ct.parse_text(original)
        ct.write_entries(repo, [E('v1.0.0', 'x')])
        with open(repo / ct.CHANGELOG_REL, encoding='utf-8', newline='') as f:
            new = f.read()
        self.assertTrue(new.startswith(prefix))
        self.assertTrue(new.endswith(suffix))
        self.assertEqual(ct.read_entries(repo), [E('v1.0.0', 'x')])

    def test_given_quotes_backslashes_and_script_tag_when_roundtrip_then_text_preserved(self):
        tricky = ["it's \"quoted\"", 'C:\\pasta\\arquivo', 'fecha </script> aqui', 'linha\nquebrada', '`crase` ${x}']
        text = ct.render_text('const CHANGELOG = ', [E('v1.0.0', *tricky)], ';\n')
        self.assertNotIn('</script>', text)
        self.assertEqual(ct.parse_text(text)[1][0]['changes'], tricky)

    def test_given_comments_double_quotes_and_unquoted_keys_when_parsed_then_ok(self):
        text = ('const CHANGELOG = [ // topo\n { "version": "v1.0.0", date: \'2026-01-01\', /* c */ changes: '
                '["a", \'b\\\'c\',], },\n];')
        self.assertEqual(ct.parse_text(text)[1], [E('v1.0.0', 'a', "b'c")])

    def test_given_invalid_literal_when_parsed_then_raises(self):
        with self.assertRaises(ct.ChangelogError):
            ct.parse_text('const CHANGELOG = [ { version: `v1` } ];')
        with self.assertRaises(ct.ChangelogError):
            ct.parse_text('const OUTRO = [];')


class Versions(unittest.TestCase):
    ENTRIES = [E(PEND, 'p'), E('v1.2.0-beta.2', 'b2'), E('v1.2.0-beta.1', 'b1'), E('v1.2.0', 'o'),
               E('v1.1.9', 'old'), E('v1.1.9-beta.7', 'velha')]

    def test_last_official_is_highest_official(self):
        self.assertEqual(ct.last_official(self.ENTRIES), 'v1.2.0')
        self.assertIsNone(ct.last_official([E(PEND, 'p')]))

    def test_next_beta_number_counts_only_same_base(self):
        self.assertEqual(ct.next_beta_number(self.ENTRIES, 'v1.2.0'), 3)
        self.assertEqual(ct.next_beta_number(self.ENTRIES, 'v1.3.0'), 1)

    def test_rename_pending_keeps_order_and_sets_date(self):
        out = ct.rename_pending(self.ENTRIES, 'v1.2.0-beta.3', '2026-03-03')
        self.assertEqual(out[0], E('v1.2.0-beta.3', 'p', date='2026-03-03'))
        self.assertEqual(self.ENTRIES[0]['version'], PEND)  # não muta a entrada original

    def test_rename_pending_without_pending_creates_entry(self):
        out = ct.rename_pending([E('v1.0.0', 'a')], 'v1.0.0-beta.1', '2026-03-03', fallback_changes=['lote'])
        self.assertEqual(out[0], E('v1.0.0-beta.1', 'lote', date='2026-03-03'))

    def test_consolidate_betas_joins_without_duplicates_and_removes_betas(self):
        entries = [E(PEND, 'p'), E('v1.0.0-beta.2', 'c', 'a'), E('v1.0.0-beta.1', 'a', 'b'), E('v1.0.0', 'o')]
        out = ct.consolidate_betas(entries, 'v1.1.0', '2026-04-04')
        self.assertEqual([e['version'] for e in out], [PEND, 'v1.1.0', 'v1.0.0'])
        self.assertEqual(out[1]['changes'], ['c', 'a', 'b'])
        self.assertEqual(ct.next_beta_number(out, ct.last_official(out)), 1)


class Union(unittest.TestCase):
    def test_union_by_version_sorted_desc_with_pending_on_top(self):
        ours = [E(PEND, 'meu'), E('v1.0.0-beta.1', 'a'), E('v1.0.0', 'o')]
        theirs = [E('v1.0.0-beta.2', 'b'), E('v1.0.0-beta.1', 'a', 'a2'), E('v1.0.0', 'o')]
        out = ct.union_entries(ours, theirs)
        self.assertEqual([e['version'] for e in out], [PEND, 'v1.0.0-beta.2', 'v1.0.0-beta.1', 'v1.0.0'])
        self.assertEqual(out[2]['changes'], ['a', 'a2'])

    def test_pending_is_kept_from_whoever_has_it_even_if_base_had_it(self):
        base = [E(PEND, 'x'), E('v1.0.0', 'o')]
        out = ct.union_entries([E('v1.0.0', 'o')], [E(PEND, 'x', 'y'), E('v1.0.0', 'o')], base)
        self.assertEqual(out[0], E(PEND, 'x', 'y'))

    def test_with_base_versions_removed_on_one_side_do_not_come_back(self):
        base = [E('v1.0.0-beta.1', 'a'), E('v1.0.0', 'o')]
        theirs = [E('v1.1.0', 'a'), E('v1.0.0', 'o')]  # promoção consolidou a beta
        ours = [E(PEND, 'novo'), E('v1.0.0-beta.1', 'a'), E('v1.0.0', 'o')]
        out = ct.union_entries(ours, theirs, base)
        self.assertEqual([e['version'] for e in out], [PEND, 'v1.1.0', 'v1.0.0'])

    def test_resolve_changelog_text_conflicting_prefix_raises(self):
        base = ct.render_text('/* a */ const CHANGELOG = ', [], ';')
        ours = ct.render_text('/* b */ const CHANGELOG = ', [], ';')
        theirs = ct.render_text('/* c */ const CHANGELOG = ', [], ';')
        with self.assertRaises(ct.ConflictError):
            ct.resolve_changelog_text(base, ours, theirs)
        theirs_entries = ct.render_text('/* a */ const CHANGELOG = ', [E('v1.0.0')], ';')
        merged = ct.resolve_changelog_text(base, ours, theirs_entries)
        self.assertTrue(merged.startswith('/* b */'))
        self.assertEqual(ct.parse_text(merged)[1][0]['version'], 'v1.0.0')


class Badge(TmpDirMixin, unittest.TestCase):
    def test_set_badge_changes_only_inner_text(self):
        html = ('<p>v9.9.9 · protótipo</p>\n<button class="b" id="prototype-version-badge" onclick="x()">'
                'v0.0.0 · protótipo</button>\n')
        write(self.tmp / 'index.html', html)
        self.assertTrue(ct.set_badge(self.tmp, 'v1.2.3-beta.4'))
        new = (self.tmp / 'index.html').read_text(encoding='utf-8')
        self.assertEqual(new, html.replace('v0.0.0 · protótipo</button>', 'v1.2.3-beta.4 · protótipo</button>'))
        self.assertFalse(ct.set_badge(self.tmp, 'v1.2.3-beta.4'))

    def test_set_badge_rejects_invalid_version_and_missing_badge(self):
        write(self.tmp / 'index.html', '<button id="prototype-version-badge">v0.0.0 · protótipo</button>')
        with self.assertRaises(ValueError):
            ct.set_badge(self.tmp, 'Pendente')
        write(self.tmp / 'index.html', '<p>sem badge</p>')
        with self.assertRaises(ct.BadgeNotFound):
            ct.set_badge(self.tmp, 'v1.0.0')


def M(email, status, at, hist_at=None):
    return {'email': email, 'status': status, 'statusChangedAt': at,
            'statusHistory': [{'status': status, 'at': hist_at or at}]}


def A(id_, version, published):
    return {'id': id_, 'kind': 'beta', 'version': version, 'publishedAt': published}


class MergeConfig(unittest.TestCase):
    BASE = {'groupMode': True, 'policy': {'promoters': 'listed'}, 'members': [M('a@example.test', 'pending', 't1')],
            'artifacts': [A('beta', 'v1.0.0-beta.1', 't1')]}

    def test_decision_beats_pending_even_if_older(self):
        ours = dict(self.BASE, members=[M('a@example.test', 'pending', '2026-05-01T00:00:00Z')])
        theirs = dict(self.BASE, members=[M('a@example.test', 'approved', '2026-04-01T00:00:00Z')])
        out = ct.merge_config(self.BASE, ours, theirs)
        self.assertEqual(out['members'][0]['status'], 'approved')
        self.assertEqual(len(out['members'][0]['statusHistory']), 2)

    def test_between_decisions_most_recent_wins_and_members_are_united(self):
        ours = dict(self.BASE, members=[M('a@example.test', 'approved', '2026-04-01T00:00:00Z')])
        theirs = dict(self.BASE, members=[M('A@example.test', 'revoked', '2026-04-02T00:00:00Z'),
                                          M('b@example.test', 'pending', 't')])
        out = ct.merge_config(self.BASE, ours, theirs)
        self.assertEqual([m['status'] for m in out['members']], ['revoked', 'pending'])

    def test_artifacts_higher_version_wins_then_published_at(self):
        ours = dict(self.BASE, artifacts=[A('beta', 'v1.0.0-beta.2', '2026-01-01'), A('x', 'v1.0.0', '2026-01-01')])
        theirs = dict(self.BASE, artifacts=[A('beta', 'v1.0.0-beta.10', '2026-01-01'), A('x', 'v1.0.0', '2026-02-01')])
        out = {a['id']: a for a in ct.merge_config(self.BASE, ours, theirs)['artifacts']}
        self.assertEqual(out['beta']['version'], 'v1.0.0-beta.10')
        self.assertEqual(out['x']['publishedAt'], '2026-02-01')

    def test_other_keys_one_side_changed_takes_it_both_changed_raises(self):
        ours = dict(self.BASE, policy={'promoters': 'all-members'})
        out = ct.merge_config(self.BASE, ours, dict(self.BASE))
        self.assertEqual(out['policy'], {'promoters': 'all-members'})
        theirs = dict(self.BASE, policy={'promoters': 'other'}, groupMode=False)
        ours2 = dict(ours, groupMode=None)
        with self.assertRaises(ct.ConflictError) as cm:
            ct.merge_config(self.BASE, ours2, theirs)
        self.assertEqual(sorted(cm.exception.keys), ['groupMode', 'policy'])

    def test_resolve_config_text_outputs_json(self):
        text = ct.resolve_config_text(json.dumps(self.BASE), json.dumps(self.BASE), json.dumps(
            dict(self.BASE, remote='upstream')))
        self.assertEqual(json.loads(text)['remote'], 'upstream')


if __name__ == '__main__':
    unittest.main()
