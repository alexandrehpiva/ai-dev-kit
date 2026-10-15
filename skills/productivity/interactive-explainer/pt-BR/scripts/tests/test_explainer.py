"""Testes dos scripts do interactive-explainer (unittest, só stdlib).

Rodar:  python3 -m unittest discover -s <skill>/scripts/tests -v

Os testes de render exigem Chrome/Chromium e são pulados sem ele (com mensagem explícita).
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
SKILL = SCRIPTS.parent
EXAMPLE = SKILL / 'examples' / 'online-order.data.json'
sys.path.insert(0, str(SCRIPTS))

import explainer_lib as lib  # noqa: E402


def load_example():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))


def run_script(name, *args, env=None):
    proc = subprocess.run([sys.executable, str(SCRIPTS / name), *args], capture_output=True, text=True, env=env)
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out = None
    return proc.returncode, out, proc.stderr


def errors_of(data, **kw):
    return [p for p in lib.validate(data, **kw) if p['level'] == 'error']


def has(problems, fragment):
    return any(fragment in p['msg'] or fragment in p['where'] for p in problems)


def board_stage(data, stage_index=1):
    return data['tabs'][1]['blocks'][0]['stages'][stage_index]


class ValidateExample(unittest.TestCase):
    def test_example_has_no_errors_or_warnings(self):
        problems = lib.validate(load_example())
        self.assertEqual([p for p in problems if p['level'] in ('error', 'warn')], [])

    def test_example_passes_require_source(self):
        self.assertEqual(errors_of(load_example(), require_source=True), [])

    def test_require_source_flags_a_node_without_source(self):
        d = load_example()
        d['tabs'][1]['blocks'][0]['stages'][1]['graph']['nodes'][0].pop('source', None)
        self.assertTrue(has(errors_of(d, require_source=True), 'source'))


class ValidateNegatives(unittest.TestCase):
    def test_missing_title(self):
        d = load_example(); d['meta'].pop('title')
        self.assertTrue(has(errors_of(d), 'meta.title'))

    def test_not_an_object(self):
        self.assertTrue(has(errors_of([]), 'objeto'))

    def test_no_tabs(self):
        d = load_example(); d['tabs'] = []
        self.assertTrue(has(errors_of(d), 'pelo menos uma aba'))

    def test_bad_tab_id(self):
        d = load_example(); d['tabs'][0]['id'] = 'Aba Um'
        self.assertTrue(has(errors_of(d), 'id da aba'))

    def test_duplicate_tab_id(self):
        d = load_example(); d['tabs'][1]['id'] = d['tabs'][0]['id']
        self.assertTrue(has(errors_of(d), 'repetido'))

    def test_unknown_block_type(self):
        d = load_example(); d['tabs'][0]['blocks'][0]['type'] = 'carousel'
        self.assertTrue(has(errors_of(d), 'tipo de bloco desconhecido'))

    def test_unknown_piece_type_is_only_a_warning(self):
        d = load_example(); board_stage(d)['graph']['nodes'][0]['type'] = 'robot'
        self.assertEqual(errors_of(d), [])
        self.assertTrue(any('sem declaração' in p['msg'] for p in lib.validate(d) if p['level'] == 'warn'))

    def test_edge_to_missing_node(self):
        d = load_example(); board_stage(d)['graph']['edges'][0]['to'] = 'fantasma'
        self.assertTrue(has(errors_of(d), 'nó inexistente'))

    def test_duplicate_node_id(self):
        d = load_example(); nodes = board_stage(d)['graph']['nodes']; nodes[1]['id'] = nodes[0]['id']
        self.assertTrue(has(errors_of(d), 'id de nó repetido'))

    def test_self_loop_edge(self):
        d = load_example(); g = board_stage(d)['graph']; g['edges'].append({'from': 'api', 'to': 'api', 'label': 'x'})
        self.assertTrue(has(errors_of(d), 'para ele mesmo'))

    def test_mixed_layout(self):
        d = load_example(); board_stage(d)['graph']['nodes'][0].pop('col')
        self.assertTrue(has(errors_of(d), 'layout misto'))

    def test_two_nodes_same_cell(self):
        d = load_example(); nodes = board_stage(d)['graph']['nodes']; nodes[1]['col'], nodes[1]['row'] = nodes[0]['col'], nodes[0]['row']
        self.assertTrue(has(errors_of(d), 'mesma célula'))

    def test_ref_missing_in_catalog(self):
        d = load_example(); board_stage(d)['graph']['nodes'][1]['refs'] = ['service:nao-existe']
        self.assertTrue(has(errors_of(d), 'não existe no catalog'))

    def test_chip_missing_in_catalog(self):
        d = load_example(); d['catalog']['service'][0]['rows'][2][1] = '@rule:fantasma'
        self.assertTrue(has(errors_of(d), 'chip @rule:fantasma'))

    def test_matrix_row_with_more_cells_than_columns(self):
        d = load_example(); d['tabs'][0]['blocks'][1]['rows'][0]['cells'].append('sobra')
        self.assertTrue(has(errors_of(d), 'células para'))

    def test_gate_miss_out_of_range(self):
        d = load_example(); gate = d['tabs'][0]['blocks'][4]['roles'][3]['samples'][0]; gate['miss'] = 99
        self.assertTrue(has(errors_of(d), 'miss fora da faixa'))

    def test_rail_loop_refers_to_missing_step(self):
        d = load_example(); d['tabs'][0]['blocks'][0]['loop']['to'] = 77
        self.assertTrue(has(errors_of(d), 'passo 77 não existe'))

    def test_rail_link_to_missing_block(self):
        d = load_example(); d['tabs'][0]['blocks'][0]['steps'][1]['go'] = 'papeis/nao-existe'
        self.assertTrue(has(errors_of(d), 'bloco inexistente'))

    def test_dangerous_markup_is_rejected(self):
        for bad in ('<script>alert(1)</script>', '<img src=x onerror=alert(1)>', '<a href="javascript:x()">a</a>'):
            d = load_example(); d['meta']['lead'] = bad
            self.assertTrue(has(errors_of(d), 'marcação perigosa'), bad)

    def test_new_piece_type_does_not_need_color(self):
        d = load_example(); d['pieceTypes']['robo'] = {'label': 'Robô'}
        self.assertEqual(errors_of(d), [])

    def test_bad_hex_color(self):
        d = load_example(); d['pieceTypes']['service']['color'] = 'azul'
        self.assertTrue(has(errors_of(d), '#RRGGBB'))

    def test_empty_stage_does_not_need_text(self):
        d = load_example(); st = board_stage(d, 3); st.pop('empty')
        self.assertEqual(errors_of(d), [])


class ValidateWarnings(unittest.TestCase):
    def warns(self, data):
        return [p for p in lib.validate(data) if p['level'] == 'warn']

    def test_long_node_title(self):
        d = load_example(); board_stage(d)['graph']['nodes'][0]['title'] = 'x' * 60
        self.assertTrue(has(self.warns(d), 'título longo'))

    def test_long_edge_label(self):
        d = load_example(); board_stage(d)['graph']['edges'][0]['label'] = 'um rótulo bem comprido demais'
        self.assertTrue(has(self.warns(d), 'rótulo longo'))

    def test_orphan_node_is_not_a_warning(self):
        d = load_example(); board_stage(d)['graph']['nodes'].append({'id': 'solto', 'type': 'file', 'title': 'Solto', 'col': 4, 'row': 3})
        self.assertFalse(has(self.warns(d), 'sem nenhuma aresta'))
        self.assertTrue(any('sem nenhuma aresta' in p['msg'] for p in lib.validate(d) if p['level'] == 'info'))

    def test_guard_without_edge_is_not_a_warning(self):
        d = load_example(); g = board_stage(d)['graph']; g['edges'] = [e for e in g['edges'] if e['from'] != 'r1']
        self.assertFalse(has(self.warns(d), 'trava r1'))

    def test_straight_edge_over_a_node(self):
        d = load_example(); g = board_stage(d)['graph']
        g['edges'].append({'from': 'cli', 'to': 'rec', 'label': 'direto'})  # mesma linha 1, passa por api e ev
        self.assertTrue(has(self.warns(d), 'passa por cima de'))

    def test_two_guards_same_column(self):
        d = load_example(); g = board_stage(d)['graph']
        g['nodes'].append({'id': 'r3', 'type': 'rule', 'title': 'Outra', 'col': 1, 'row': 4})
        g['edges'].append({'from': 'r3', 'to': 'api'})
        self.assertTrue(has(self.warns(d), 'travas na coluna'))

    def test_gate_without_missing_item_is_fine(self):
        d = load_example(); gate = d['tabs'][0]['blocks'][4]['roles'][3]['samples'][0]; gate.pop('miss')
        self.assertEqual(self.warns(d), [])

    def test_loop_without_label_is_fine(self):
        d = load_example(); d['tabs'][0]['blocks'][0]['loop'].pop('label')
        self.assertEqual(self.warns(d), [])


class Freedom(unittest.TestCase):
    """Nada além do mínimo é obrigatório: o conteúdo decide a estrutura."""

    def minimal(self, *blocks):
        return {'meta': {'title': 'Mínimo'}, 'tabs': [{'id': 'a', 'label': 'A', 'blocks': list(blocks)}]}

    def test_every_optional_field_can_be_omitted(self):
        d = self.minimal(
            {'type': 'board', 'stages': [{'title': 'Só um título'}]},
            {'type': 'roles', 'roles': [{'name': 'Sem resumo, sem lista, sem amostra'}]},
            {'type': 'rail', 'steps': [{'title': 'a'}, {'title': 'b'}], 'loop': {'from': [2], 'to': 1}},
            {'type': 'matrix', 'columns': ['x', 'y'], 'rows': [{'label': 'r', 'cells': ['só uma']}]},
        )
        self.assertEqual([p for p in lib.validate(d) if p['level'] in ('error', 'warn')], [])

    def test_no_piece_types_are_built_in(self):
        self.assertEqual(lib.piece_types({}), {})
        self.assertNotIn('DEFAULT_TYPES', Path(lib.TEMPLATE_PATH).read_text(encoding='utf-8'))

    def test_sample_block_validates_its_samples(self):
        ok = self.minimal({'type': 'sample', 'sample': {'kind': 'note', 'text': 'x'}})
        self.assertEqual([p for p in lib.validate(ok) if p['level'] == 'error'], [])
        bad = self.minimal({'type': 'sample', 'sample': {'kind': 'desenho'}})
        self.assertTrue(has(errors_of(bad), 'tipo de amostra desconhecido'))
        self.assertTrue(has(errors_of(self.minimal({'type': 'sample'})), 'precisa de'))

    def test_embed_needs_a_real_snippet(self):
        self.assertTrue(has(errors_of(self.minimal({'type': 'embed'})), 'embed precisa'))
        self.assertTrue(has(errors_of(self.minimal({'type': 'embed', 'snippet': 'nao-existe'})), 'snippet inexistente'))
        ok = self.minimal({'type': 'embed', 'snippet': 'swimlane', 'height': 520})
        self.assertEqual(errors_of(ok), [])

    def test_embed_html_is_injected_as_srcdoc_without_tripping_the_markup_filter(self):
        d = self.minimal({'type': 'embed', 'snippet': 'swimlane'})
        html = lib.build_html(d)
        self.assertIn('"srcdoc"', html)
        self.assertIn('Raias por responsável', html)
        with_script = self.minimal({'type': 'embed', 'srcdoc': '<script>1</script>'})
        self.assertEqual(errors_of(with_script), [])

    def test_embed_file_relative_to_the_data_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'meu.html').write_text('<p>meu visual</p>', encoding='utf-8')
            d = self.minimal({'type': 'embed', 'file': 'meu.html'})
            self.assertEqual([p for p in lib.validate(d, base_dir=tmp) if p['level'] == 'error'], [])
            self.assertTrue(has([p for p in lib.validate(d, base_dir=tmp + '/x') if p['level'] == 'error'], 'não encontrado'))
            self.assertIn('meu visual', lib.build_html(d, base_dir=tmp))

    def test_labels_are_overridable_in_the_template(self):
        tpl = Path(lib.TEMPLATE_PATH).read_text(encoding='utf-8')
        self.assertIn('meta.labels', tpl)
        for key in ("L('prev')", "L('play')", "L('unconfirmed')", "L('theme')"):
            self.assertIn(key, tpl)


class BlockSources(unittest.TestCase):
    def block(self, **extra):
        b = {'type': 'cards', 'items': [{'title': 'a'}, {'title': 'b'}]}
        b.update(extra)
        return {'meta': {'title': 'T'}, 'tabs': [{'id': 'a', 'label': 'A', 'blocks': [b]}]}

    def test_block_without_source_fails_only_with_require_source(self):
        self.assertEqual(errors_of(self.block()), [])
        self.assertTrue(has(errors_of(self.block(), require_source=True), 'sem "source"'))

    def test_block_level_source_covers_its_items(self):
        self.assertEqual(errors_of(self.block(source='docs/a.md, seção 1'), require_source=True), [])

    def test_item_level_source_or_hypothesis_also_covers(self):
        d = self.block(); d['tabs'][0]['blocks'][0]['items'][0].update(source='docs/a.md, 1'); d['tabs'][0]['blocks'][0]['items'][1].update(status='hipotese')
        self.assertEqual(errors_of(d, require_source=True), [])

    def test_matrix_and_sample_blocks_need_block_level_source(self):
        m = {'meta': {'title': 'T'}, 'tabs': [{'id': 'a', 'label': 'A', 'blocks': [{'type': 'matrix', 'columns': ['x'], 'rows': []}]}]}
        self.assertTrue(has(errors_of(m, require_source=True), 'bloco matrix sem'))
        m['tabs'][0]['blocks'][0]['status'] = 'hipotese'
        self.assertEqual(errors_of(m, require_source=True), [])

    def test_block_level_source_covers_graph_nodes_and_edges(self):
        d = load_example()
        board = d['tabs'][1]['blocks'][0]
        for st in board['stages']:
            for n in (st.get('graph') or {}).get('nodes', []): n.pop('source', None)
            for e in (st.get('graph') or {}).get('edges', []): e.pop('source', None)
        self.assertTrue(has(errors_of(d, require_source=True), 'sem "source"'))
        board['source'] = 'documento do exemplo, seção única'
        self.assertEqual([p for p in errors_of(d, require_source=True) if 'graph' in p['where']], [])

    def test_block_quote_is_verified_against_the_block_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'a.md').write_text('Regra: o limite é 5 tentativas.', encoding='utf-8')
            ok = self.block(source='a.md, regra', quote='o limite é 5 tentativas')
            self.assertEqual(errors_of(ok, require_source=True, source_root=tmp), [])
            bad = self.block(source='a.md, regra', quote='o limite é 3 tentativas')
            self.assertTrue(has(errors_of(bad, require_source=True, source_root=tmp), 'não aparece'))

    def test_summary_counts_blocks_items_and_hypotheses(self):
        d = self.block(source='x.md, 1'); d['tabs'][0]['blocks'][0]['items'][1].update(status='hipotese', note='falta confirmar')
        out, questions = lib.source_summary(d)
        self.assertEqual(out['hypotheses'], 1)
        self.assertTrue(any('falta confirmar' in q for q in questions))


class SourceProtections(unittest.TestCase):
    """Defesas contra desenho inventado: fonte em nó e aresta, hipótese explícita, arquivo e trecho conferidos."""

    def graph(self, d):
        return d['tabs'][1]['blocks'][0]['stages'][1]['graph']

    def test_edge_without_source_is_error_with_require_source(self):
        d = load_example(); self.graph(d)['edges'][0].pop('source')
        self.assertTrue(has(errors_of(d, require_source=True), 'aresta sem "source"'))

    def test_hypothesis_node_and_edge_do_not_need_source(self):
        d = load_example(); g = self.graph(d)
        g['nodes'][1].pop('source'); g['nodes'][1]['status'] = 'hipotese'
        for e in g['edges']:
            if 'api' in (e['from'], e['to']):
                e.pop('source', None); e['status'] = 'hipotese'
        self.assertEqual(errors_of(d, require_source=True), [])

    def test_invalid_status_is_error(self):
        d = load_example(); self.graph(d)['nodes'][0]['status'] = 'talvez'
        self.assertTrue(has(errors_of(d), 'status inválido'))

    def test_placeholder_source_is_rejected(self):
        d = load_example(); self.graph(d)['nodes'][0]['source'] = 'a definir'
        self.assertTrue(has(errors_of(d, require_source=True), 'genérico'))

    def test_quote_without_source_is_error(self):
        d = load_example(); n = self.graph(d)['nodes'][0]; n.pop('source'); n['quote'] = 'algo'
        self.assertTrue(has(errors_of(d, require_source=True), 'quote sem source'))

    def make_root(self, tmp, text='A API de pedidos confere o carrinho e pede a cobrança.'):
        (Path(tmp) / 'docs').mkdir()
        (Path(tmp) / 'docs' / 'checkout.md').write_text(text, encoding='utf-8')
        return tmp

    def test_source_file_must_exist_under_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            d = load_example(); self.graph(d)['nodes'][0]['source'] = 'docs/inexistente.md, seção 2'
            self.assertTrue(has(errors_of(d, require_source=True, source_root=root), 'nenhum arquivo citado existe'))

    def test_quote_must_appear_in_cited_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            d = load_example(); n = self.graph(d)['nodes'][1]
            n['source'] = 'docs/checkout.md, passo 2'
            n['quote'] = 'confere   o carrinho e pede a cobrança'  # espaços diferentes: normalizados
            only = [p for p in errors_of(d, require_source=True, source_root=root) if 'nodes[1]' in p['where']]
            self.assertEqual(only, [])
            n['quote'] = 'valida o estoque e envia o e-mail'
            self.assertTrue(has(errors_of(d, require_source=True, source_root=root), 'não aparece'))

    def test_path_traversal_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            d = load_example(); self.graph(d)['nodes'][0]['source'] = '../../etc/passwd.md'
            self.assertTrue(has(errors_of(d, require_source=True, source_root=root), 'nenhum arquivo citado existe'))

    def test_require_quote_demands_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            d = load_example()
            self.assertTrue(has(errors_of(d, require_source=True, source_root=root, require_quote=True), 'sem "quote"'))

    def test_cli_require_quote_without_root_is_usage_error(self):
        code, out, _ = run_script('validate-explainer.py', str(EXAMPLE), '--require-quote')
        self.assertEqual(code, 2)
        self.assertEqual(out['status'], 'UNREADABLE')

    def test_cli_reports_sources_and_questions(self):
        code, out, _ = run_script('validate-explainer.py', str(EXAMPLE), '--require-source')
        self.assertEqual(code, 0)
        self.assertGreaterEqual(out['data']['sources']['hypotheses'], 1)
        self.assertTrue(any('Confirmar hipótese' in q for q in out['questions']))

    def test_source_packet_lists_confirmed_claims_only(self):
        code, out, _ = run_script('source-packet.py', str(EXAMPLE), '--format', 'json')
        self.assertEqual(code, 0)
        self.assertEqual(out['status'], 'PACKET')
        refs = {c['ref'] for c in out['data']['claims']}
        self.assertNotIn('falta', refs)  # hipótese fica de fora
        self.assertIn('api', refs)
        code, out, _ = run_script('source-packet.py', str(EXAMPLE), '--format', 'json', '--include-hypotheses')
        self.assertIn('falta', {c['ref'] for c in out['data']['claims']})

    def test_engine_marks_hypothesis_on_screen(self):
        html = lib.build_html(load_example())
        self.assertIn("a confirmar", html)
        self.assertIn("hipotese", html)


class Build(unittest.TestCase):
    def test_build_embeds_data_and_title(self):
        html = lib.build_html(load_example())
        self.assertIn('<title>Do clique em Pagar à entrega</title>', html)
        self.assertNotIn(lib.DATA_PLACEHOLDER, html)
        self.assertNotIn(lib.TITLE_PLACEHOLDER, html)
        self.assertIn('"Loja Exemplo', html)

    def test_script_close_tag_is_escaped_in_payload(self):
        d = load_example(); d['meta']['lead'] = 'texto </script> com fim de script'
        html = lib.build_html(d)
        block = html.split('id="explainer-data">')[1].split('</script>')[0]
        self.assertNotIn('</', block)
        self.assertIn('<\\/script>', block)

    def test_title_is_html_escaped(self):
        d = load_example(); d['meta']['title'] = 'A & B <i>'
        self.assertIn('<title>A &amp; B &lt;i></title>', lib.build_html(d))

    def test_payload_round_trips(self):
        d = load_example()
        html = lib.build_html(d)
        block = html.split('id="explainer-data">')[1].split('</script>')[0].replace('<\\/', '</')
        self.assertEqual(json.loads(block), d)

    def test_template_without_markers_is_rejected(self):
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
            f.write('<html>sem marcadores</html>')
        try:
            with self.assertRaises(ValueError):
                lib.build_html(load_example(), f.name)
        finally:
            os.unlink(f.name)


class CliEnvelopes(unittest.TestCase):
    def test_validate_ok(self):
        code, out, _ = run_script('validate-explainer.py', str(EXAMPLE))
        self.assertEqual(code, 0)
        self.assertEqual(out['status'], 'VALID')
        self.assertTrue(out['ok'])

    def test_validate_invalid_exit_1(self):
        d = load_example(); d['meta'].pop('title')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'; p.write_text(json.dumps(d))
            code, out, _ = run_script('validate-explainer.py', str(p))
        self.assertEqual(code, 1)
        self.assertEqual(out['status'], 'INVALID')

    def test_validate_unreadable(self):
        code, out, _ = run_script('validate-explainer.py', '/nao/existe.json')
        self.assertEqual(code, 1)
        self.assertEqual(out['status'], 'UNREADABLE')

    def test_validate_broken_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'; p.write_text('{"meta": ')
            code, out, _ = run_script('validate-explainer.py', str(p))
        self.assertEqual(out['status'], 'UNREADABLE')
        self.assertIn('linha', out['problems'][0]['msg'])

    def test_validate_strict_fails_on_warning(self):
        d = load_example(); board_stage(d)['graph']['nodes'][0]['title'] = 'x' * 60
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'; p.write_text(json.dumps(d))
            ok_code, _, _ = run_script('validate-explainer.py', str(p))
            strict_code, out, _ = run_script('validate-explainer.py', str(p), '--strict')
        self.assertEqual(ok_code, 0)
        self.assertEqual(strict_code, 1)
        self.assertEqual(out['status'], 'INVALID')

    def test_usage_error_exit_2(self):
        code, _, _ = run_script('validate-explainer.py')
        self.assertEqual(code, 2)

    def test_build_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / 'sub' / 'out.html'
            code, out, _ = run_script('build-explainer.py', str(EXAMPLE), '--out', str(out_path))
            self.assertEqual(code, 0)
            self.assertEqual(out['status'], 'BUILT')
            self.assertTrue(out_path.is_file())
            self.assertGreater(out_path.stat().st_size, 50_000)

    def test_build_refuses_invalid_and_writes_nothing(self):
        d = load_example(); d['meta'].pop('title')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'; p.write_text(json.dumps(d))
            out_path = Path(tmp) / 'out.html'
            code, out, _ = run_script('build-explainer.py', str(p), '--out', str(out_path))
            self.assertEqual(code, 1)
            self.assertEqual(out['status'], 'INVALID')
            self.assertFalse(out_path.exists())

    def test_build_force_writes_invalid_draft(self):
        d = load_example(); d['tabs'][0]['blocks'][0]['loop']['to'] = 77
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'd.json'; p.write_text(json.dumps(d))
            out_path = Path(tmp) / 'out.html'
            code, out, _ = run_script('build-explainer.py', str(p), '--out', str(out_path), '--force')
            self.assertEqual(code, 0)
            self.assertTrue(out_path.exists())


class TemplateSyntax(unittest.TestCase):
    @unittest.skipUnless(subprocess.run(['which', 'node'], capture_output=True).returncode == 0, 'node ausente: checagem de sintaxe do motor pulada')
    def test_engine_script_parses(self):
        html = (SKILL / 'templates' / 'explainer-template.html').read_text(encoding='utf-8')
        engine = html.split('<script>')[1].split('</script>')[0]
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
            f.write(engine)
        try:
            proc = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        finally:
            os.unlink(f.name)


def _chrome_available():
    import importlib.util
    spec = importlib.util.spec_from_file_location('render_check', SCRIPTS / 'render-check.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path, _ = mod.find_chrome()
    return bool(path)


class RenderCheck(unittest.TestCase):
    def test_invalid_chrome_path_is_an_error_not_a_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = Path(tmp) / 'x.html'; html.write_text('<html></html>')
            env = dict(os.environ, CHROME_PATH='/nao/existe/chrome')
            code, out, _ = run_script('render-check.py', str(html), env=env)
        self.assertEqual(code, 1)
        self.assertEqual(out['status'], 'NO_CHROME')
        self.assertFalse(out['ok'])
        self.assertIn('CHROME_PATH', out['problems'][0]['msg'])

    def test_missing_file(self):
        code, out, _ = run_script('render-check.py', '/nao/existe.html')
        self.assertEqual(out['status'], 'UNREADABLE')

    @unittest.skipUnless(_chrome_available(), 'Chrome/Chromium ausente: testes de render pulados')
    def test_free_composition_renders_without_errors_and_shows_new_blocks(self):
        data = {'meta': {'title': 'Livre', 'labels': {'unconfirmed': 'por confirmar'}},
                'pieceTypes': {'ideia': {'label': 'Ideia'}},
                'tabs': [{'id': 'a', 'label': 'A', 'blocks': [
                    {'type': 'sample', 'title': 'Solta', 'sample': {'kind': 'note', 'title': 'x', 'text': 'y'}, 'source': 'a.md, 1'},
                    {'type': 'board', 'stages': [{'title': 'Só título'}, {'title': 'Com nós', 'graph': {
                        'nodes': [{'id': 'n1', 'type': 'ideia', 'title': 'Um'}, {'id': 'n2', 'type': 'ideia', 'title': 'Dois', 'status': 'hipotese'}],
                        'edges': [{'from': 'n1', 'to': 'n2', 'label': 'leva', 'status': 'hipotese'}]}}]},
                    {'type': 'matrix', 'columns': ['x', 'y'], 'rows': [{'label': 'r', 'cells': ['só uma']}]},
                    {'type': 'rail', 'steps': [{'title': 'a'}, {'title': 'b'}], 'loop': {'from': [2], 'to': 1}}]},
                    {'id': 'b', 'label': 'B', 'blocks': [{'type': 'embed', 'snippet': 'timeline', 'height': 500}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            src, out_path = Path(tmp) / 'd.json', Path(tmp) / 'out.html'
            src.write_text(json.dumps(data), encoding='utf-8')
            code, built, _ = run_script('build-explainer.py', str(src), '--out', str(out_path))
            self.assertEqual(built['status'], 'BUILT', built)
            html = out_path.read_text(encoding='utf-8')
            self.assertIn('"srcdoc"', html)
            code, out, _ = run_script('render-check.py', str(out_path), '--widths', '1440,375')
        self.assertEqual(out['status'], 'PASS', out)
        self.assertEqual(out['data']['counts']['error'], 0)

    @unittest.skipUnless(_chrome_available(), 'Chrome/Chromium ausente: testes de render pulados')
    def test_example_passes_at_three_widths(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / 'out.html'
            run_script('build-explainer.py', str(EXAMPLE), '--out', str(out_path))
            code, out, _ = run_script('render-check.py', str(out_path))
        self.assertEqual(code, 0, out)
        self.assertEqual(out['status'], 'PASS')
        self.assertEqual([s['width'] for s in out['data']['selftests']], [1440, 768, 375])
        for st in out['data']['selftests']:
            self.assertGreater(st['stats']['edges'], 10)

    @unittest.skipUnless(_chrome_available(), 'Chrome/Chromium ausente: testes de render pulados')
    def test_selftest_detects_edge_crossing_a_node(self):
        d = load_example(); g = board_stage(d)['graph']
        g['edges'].append({'from': 'cli', 'to': 'rec', 'label': 'direto'})
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / 'out.html'
            html = lib.build_html(d); out_path.write_text(html, encoding='utf-8')
            code, out, _ = run_script('render-check.py', str(out_path), '--widths', '1440')
        self.assertTrue(any('atravessa' in p['msg'] for p in out['problems']), out['problems'])
        self.assertEqual(out['status'], 'PASS')  # atravessar nó é aviso, não erro

    @unittest.skipUnless(_chrome_available(), 'Chrome/Chromium ausente: testes de render pulados')
    def test_broken_engine_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / 'out.html'
            out_path.write_text('<html><body><script>throw new Error("quebrou")</script></body></html>')
            code, out, _ = run_script('render-check.py', str(out_path), '--widths', '1440')
        self.assertEqual(code, 1)
        self.assertEqual(out['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
