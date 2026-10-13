"""Testes do component-scan.py: cabeçalhos, duplicação, regras de negócio e catálogo."""

import json
import unittest

from helpers import TmpDirMixin, run_script, write

GOOD_HEADER = '''/**
 * @purpose Mostra um aviso curto.
 * @props texto (string)
 * @state uncontrolled — dono: o próprio componente
 * @a11y role="status"
 */
function alertaHTML(texto){ return `<div class="alerta">${texto}</div>`; }
'''


def screen(name, rows):
    body = '\n'.join(f'    <p class="linha-{i}">Texto {i}</p>' for i in rows)
    return f'''function screen{name}(){{
  return `<div class="cartao">
    <h2 class="titulo">Título</h2>
{body}
  </div>`;
}}
'''


class ScanBase(TmpDirMixin):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'proto'
        (self.repo / 'js' / 'components').mkdir(parents=True)
        (self.repo / 'js' / 'screens').mkdir()

    def scan(self, *flags):
        code, env, out, err = run_script('component-scan.py', '--repo', self.repo, *flags)
        self.assertIsNotNone(env, out + err)
        return code, env

    def codes(self, env):
        return [p['code'] for p in env['problems']]


class TestLint(ScanBase, unittest.TestCase):
    def test_given_valid_header_when_lint_then_clean(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER)
        code, env = self.scan('--lint')
        self.assertEqual((code, env['status'], env['ok']), (0, 'CLEAN', True))

    def test_given_no_header_when_lint_then_header_missing(self):
        write(self.repo / 'js/components/alerta.js', 'function alertaHTML(){ return ``; }\n')
        code, env = self.scan('--lint')
        self.assertEqual(code, 1)
        self.assertEqual(env['status'], 'ISSUES')
        self.assertIn('header-missing', self.codes(env))

    def test_given_plain_comment_without_tags_when_lint_then_header_missing(self):
        write(self.repo / 'js/components/alerta.js', '/* só um comentário */\nfunction a(){}\n')
        _, env = self.scan('--lint')
        self.assertIn('header-missing', self.codes(env))

    def test_given_missing_a11y_when_lint_then_tag_missing(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace(' * @a11y role="status"\n', ''))
        _, env = self.scan('--lint')
        self.assertEqual(self.codes(env), ['header-tag-missing'])
        self.assertIn('@a11y', env['problems'][0]['message'])

    def test_given_invalid_state_when_lint_then_state_invalid(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace('uncontrolled', 'semi-controlado'))
        _, env = self.scan('--lint')
        self.assertIn('header-state-invalid', self.codes(env))

    def test_given_state_without_owner_when_lint_then_owner_missing(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace(' — dono: o próprio componente', ''))
        _, env = self.scan('--lint')
        self.assertIn('header-state-owner-missing', self.codes(env))

    def test_given_date_in_header_when_lint_then_history_flagged(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace('Mostra um aviso curto.', 'Mostra um aviso (2026-01-02).'))
        _, env = self.scan('--lint')
        self.assertIn('header-history', self.codes(env))

    def test_given_unknown_tag_when_lint_then_flagged(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace(' */', ' * @autor alguém\n */', 1))
        _, env = self.scan('--lint')
        self.assertIn('header-unknown-tag', self.codes(env))

    def test_given_multiline_tag_values_when_lint_then_clean(self):
        text = GOOD_HEADER.replace('@props texto (string)', '@props\n *   texto (string)\n *   tipo (string)')
        write(self.repo / 'js/components/alerta.js', text)
        code, _ = self.scan('--lint')
        self.assertEqual(code, 0)

    def test_given_default_flags_when_clean_then_runs_all_checks_without_writing(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER)
        code, env = self.scan()
        self.assertEqual(code, 0)
        self.assertEqual(env['data']['checks'], ['lint', 'duplicates', 'rules'])
        self.assertFalse((self.repo / 'docs').exists())

    def test_given_folder_without_js_when_scan_then_usage_error(self):
        code, env, _, _ = run_script('component-scan.py', '--repo', self.tmp)
        self.assertEqual(code, 2)
        self.assertEqual(env['status'], 'USAGE')


class TestDuplicates(ScanBase, unittest.TestCase):
    def test_given_near_identical_screen_functions_when_duplicates_then_flagged(self):
        write(self.repo / 'js/screens/a.js', screen('A', range(1, 6)))
        write(self.repo / 'js/screens/b.js', screen('B', range(1, 6)))
        code, env = self.scan('--duplicates')
        self.assertEqual(code, 1)
        self.assertIn('duplicate-function', self.codes(env))

    def test_given_same_html_block_in_two_screens_when_duplicates_then_block_flagged(self):
        block = '''  <div class="cartao">
    <h2 class="titulo">Título</h2>
    <p class="texto">Mesmo texto</p>
  </div>'''
        write(self.repo / 'js/screens/a.js', f'function screenA(){{\n  return `\n{block}\n    <span>só A</span>`;\n}}\n')
        write(self.repo / 'js/screens/b.js', f'function screenB(){{\n  return `<main>\n{block}\n    <em>só B</em></main>`;\n}}\n')
        _, env = self.scan('--duplicates')
        self.assertIn('duplicate-block', self.codes(env))

    def test_given_distinct_screens_when_duplicates_then_clean(self):
        write(self.repo / 'js/screens/a.js', screen('A', range(1, 6)))
        write(self.repo / 'js/screens/b.js', '''function screenB(){
  return `<section class="hero">
    <h1>Outra</h1>
    <ul class="lista"><li>a</li><li>b</li></ul>
    <form class="form"><input class="campo"></form>
  </section>`;
}
''')
        code, _ = self.scan('--duplicates')
        self.assertEqual(code, 0)

    def test_given_similar_component_names_when_duplicates_then_flagged(self):
        write(self.repo / 'js/components/stepper.js', GOOD_HEADER.replace('alertaHTML', 'passoA'))
        write(self.repo / 'js/components/steppers.js', GOOD_HEADER.replace('alertaHTML', 'passoB'))
        _, env = self.scan('--duplicates')
        self.assertIn('similar-component-name', self.codes(env))

    def test_given_distinct_components_when_duplicates_then_clean(self):
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER)
        write(self.repo / 'js/components/tabela.js', GOOD_HEADER.replace('alertaHTML', 'tabelaHTML'))
        code, _ = self.scan('--duplicates')
        self.assertEqual(code, 0)


RULES_DOC = '''# Regras

<!-- exemplo comentado:
| BR-77 | Regra de exemplo | origem | tela | proposta |
-->

| id | Regra | Origem | Telas afetadas | Status |
|---|---|---|---|---|
| BR-01 | Regra usada | produto | a | aplicada |
| BR-02 | Regra sem uso | produto | b | aplicada |
| BR-03 | Regra antiga | produto | c | obsoleta |
'''


class TestRules(ScanBase, unittest.TestCase):
    def test_given_orphan_and_unknown_when_rules_then_both_flagged_and_comment_ignored(self):
        write(self.repo / 'docs/business-rules.md', RULES_DOC)
        write(self.repo / 'js/screens/a.js', '// @rule BR-01\n// @rule BR-09\nfunction screenA(){ return ``; }\n')
        code, env = self.scan('--rules')
        self.assertEqual(code, 1)
        by_code = {p['code']: p['message'] for p in env['problems']}
        self.assertIn('BR-02', by_code['rule-orphan'])
        self.assertIn('BR-09', by_code['rule-unknown'])
        self.assertEqual(sorted(by_code), ['rule-orphan', 'rule-unknown'])  # BR-03 obsoleta e BR-77 comentada: ignoradas
        self.assertEqual(env['data']['rules'], {'defined': 3, 'referenced': 2})

    def test_given_rules_tag_in_component_header_when_rules_then_counts_as_use(self):
        write(self.repo / 'docs/business-rules.md', RULES_DOC)
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace(' * @a11y', ' * @rules BR-01, BR-02\n * @a11y'))
        code, env = self.scan('--rules')
        self.assertEqual(code, 0, env['problems'])

    def test_given_reference_without_rules_file_when_rules_then_unknown(self):
        write(self.repo / 'js/screens/a.js', '// @rule BR-05\nfunction screenA(){ return ``; }\n')
        _, env = self.scan('--rules')
        self.assertEqual(self.codes(env), ['rule-unknown'])

    def test_given_no_rules_and_no_refs_when_rules_then_clean(self):
        write(self.repo / 'js/screens/a.js', 'function screenA(){ return ``; }\n')
        code, _ = self.scan('--rules')
        self.assertEqual(code, 0)


class TestCatalog(ScanBase, unittest.TestCase):
    def setUp(self):
        super().setUp()
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER)
        write(self.repo / 'js/screens/a.js', 'function screenA(){ return alertaHTML("oi"); }\n')

    def test_given_components_when_write_catalog_then_generated_with_marker_and_usage(self):
        code, env = self.scan('--write-catalog')
        self.assertEqual(code, 0)
        self.assertTrue(env['data']['catalog']['written'])
        text = (self.repo / 'docs/components.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('<!-- GERADO por component-scan.py'))
        row = next(line for line in text.splitlines() if line.startswith('| `alerta`'))
        self.assertIn('uncontrolled', row)
        self.assertIn('`screens/a`', row)

    def test_given_catalog_up_to_date_when_lint_then_clean_and_rewrite_is_noop(self):
        self.scan('--write-catalog')
        code, _ = self.scan('--lint')
        self.assertEqual(code, 0)
        _, env = self.scan('--write-catalog')
        self.assertFalse(env['data']['catalog']['written'])

    def test_given_header_changed_after_catalog_when_lint_then_stale(self):
        self.scan('--write-catalog')
        write(self.repo / 'js/components/alerta.js', GOOD_HEADER.replace('Mostra um aviso curto.', 'Mostra um aviso longo.'))
        _, env = self.scan('--lint')
        self.assertEqual(self.codes(env), ['catalog-stale'])

    def test_given_component_without_header_when_write_catalog_then_row_warns(self):
        write(self.repo / 'js/components/solto.js', 'function solto(){}\n')
        self.scan('--write-catalog')
        text = (self.repo / 'docs/components.md').read_text(encoding='utf-8')
        self.assertIn('sem cabeçalho de contrato', text)


if __name__ == '__main__':
    unittest.main()
