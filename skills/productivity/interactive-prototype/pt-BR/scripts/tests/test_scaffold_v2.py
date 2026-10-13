"""Testes do scaffold.py v2: config v2, templates de agentes/docs, build, sintaxe JS e component-scan limpo."""

import json
import re
import shutil
import subprocess
import sys
import unittest

import protolib
from helpers import SCRIPTS, TmpDirMixin, run_script

NODE = shutil.which('node')


def scaffold(out, *extra):
    return run_script('scaffold.py', '--name', 'Produto Teste', '--out', out, *extra)


class TestScaffoldV2(TmpDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.out = self.tmp / 'proto'
        code, _, stdout, stderr = scaffold(self.out)
        self.assertEqual(code, 0, stdout + stderr)
        self.assertEqual(stderr, '')

    def read(self, rel):
        return (self.out / rel).read_text(encoding='utf-8')

    def test_given_scaffold_when_done_then_agent_and_docs_files_exist(self):
        for rel in ('AGENTS.md', 'CLAUDE.md', 'docs/business-rules.md', 'docs/components.md',
                    'docs/design-system.md', 'js/components/modal.js'):
            self.assertTrue((self.out / rel).is_file(), rel)
        self.assertFalse((self.out / 'business-rules.md').exists())
        self.assertFalse((self.out / 'components.md').exists())
        self.assertFalse((self.out / 'prototype.config.schema.json').exists())

    def test_given_agents_md_then_short_generic_and_stamped(self):
        text = self.read('AGENTS.md')
        self.assertLessEqual(len(text.splitlines()), 60)
        self.assertIn('interactive-prototype', text)
        self.assertIn('PARE', text)
        self.assertIn(protolib.skill_version() or '2.0.0', text)
        self.assertEqual(self.read('CLAUDE.md').strip(), '@AGENTS.md')

    def test_given_no_unrendered_placeholders_anywhere(self):
        leftovers = [str(p.relative_to(self.out)) for p in self.out.rglob('*')
                     if p.is_file() and '.git' not in p.parts and '@@' in p.read_text(encoding='utf-8', errors='ignore')]
        self.assertEqual(leftovers, [])

    def test_given_config_when_scaffold_then_v2_shape_and_group_mode_false(self):
        cfg = json.loads(self.read('prototype.config.json'))
        self.assertEqual(cfg['skill'], {'name': 'interactive-prototype', 'version': protolib.skill_version() or '2.0.0'})
        self.assertIs(cfg['groupMode'], False)
        self.assertEqual(cfg['branches'], {'official': 'main', 'beta': 'beta', 'draftPattern': 'draft/{member}'})
        self.assertEqual((cfg['members'], cfg['artifacts']), ([], []))
        self.assertNotIn('sharedBranch', cfg)

    def test_given_group_mode_flag_then_config_still_false(self):
        out = self.tmp / 'grupo'
        code, _, stdout, stderr = scaffold(out, '--group-mode')
        self.assertEqual(code, 0, stdout + stderr)
        cfg = json.loads((out / 'prototype.config.json').read_text(encoding='utf-8'))
        self.assertIs(cfg['groupMode'], False)

    def test_given_dry_run_then_nothing_written(self):
        out = self.tmp / 'seco'
        code, _, stdout, _ = scaffold(out, '--dry-run')
        self.assertEqual(code, 0)
        self.assertFalse(out.exists())
        self.assertIn('docs/business-rules.md', stdout)
        self.assertNotIn('prototype.config.schema.json', stdout)

    def test_given_non_empty_dir_then_refuses(self):
        code, _, _, _ = scaffold(self.out)
        self.assertNotEqual(code, 0)

    def test_given_no_git_flag_then_no_repo_created(self):
        out = self.tmp / 'semgit'
        code, _, _, _ = scaffold(out, '--no-git')
        self.assertEqual(code, 0)
        self.assertFalse((out / '.git').exists())

    def test_given_default_scaffold_then_no_git_remote(self):
        r = subprocess.run(['git', '-C', str(self.out), 'remote'], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), '')

    def test_given_scaffold_then_build_runs(self):
        r = subprocess.run([sys.executable, 'build.py'], cwd=self.out, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        dist = self.read('dist/index.html')
        self.assertIn('function modalHTML', dist)
        self.assertNotIn('<script src="js/', dist)

    @unittest.skipUnless(NODE, 'node não instalado')
    def test_given_scaffold_then_every_js_passes_node_check(self):
        files = sorted(self.out.rglob('*.js'))
        self.assertGreater(len(files), 8)
        for f in files:
            r = subprocess.run([NODE, '--check', str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f'{f.name}: {r.stderr}')

    def test_given_index_html_then_scripts_exist_and_modal_loads_before_changelog(self):
        html = self.read('index.html')
        scripts = re.findall(r'<script src="([^"]+)"></script>', html)
        for s in scripts:
            self.assertTrue((self.out / s).is_file(), s)
        self.assertLess(scripts.index('js/components/modal.js'), scripts.index('js/components/changelog-modal.js'))
        self.assertIn('id="prototype-version-badge"', html)
        self.assertIn('const CHANGELOG = [', self.read('js/components/changelog-modal.js'))

    def test_given_skeleton_then_component_scan_is_clean(self):
        code, env, out, err = run_script('component-scan.py', '--repo', self.out)
        self.assertEqual((code, env['status']), (0, 'CLEAN'), out + err)
        self.assertEqual(sorted(c['name'] for c in env['data']['components']),
                         ['changelog-modal', 'demo-button', 'modal', 'stepper'])
        for c in env['data']['components']:
            self.assertTrue(c['hasHeader'], c['name'])

    def test_given_skeleton_then_catalog_is_generated_and_not_a_placeholder(self):
        text = self.read('docs/components.md')
        self.assertIn('GERADO por component-scan.py', text)
        for name in ('stepper', 'demo-button', 'modal', 'changelog-modal'):
            self.assertIn(f'| `{name}` |', text)

    def test_given_skeleton_when_header_removed_then_scan_reports(self):
        modal = self.out / 'js/components/modal.js'
        modal.write_text(re.sub(r'^/\*\*.*?\*/\n', '', modal.read_text(encoding='utf-8'), flags=re.S), encoding='utf-8')
        code, env, _, _ = run_script('component-scan.py', '--repo', self.out, '--lint')
        self.assertEqual(code, 1)
        self.assertIn('header-missing', [p['code'] for p in env['problems']])


if __name__ == '__main__':
    unittest.main()
