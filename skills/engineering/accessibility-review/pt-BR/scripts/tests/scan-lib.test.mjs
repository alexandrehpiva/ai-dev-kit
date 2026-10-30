// Testes do scan-lib.mjs e da varredura de ponta a ponta. Rodar (em scripts/): node --test tests/scan-lib.test.mjs
// A parte de ponta a ponta usa Chrome + axe e é ignorada quando as ferramentas não estão instaladas.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import {
  analyzeKeyboardTrace, normalizeUrl, parseArgs, parseViewport, simplifyAxe, summarizeByCriterion, validateScenario, wcagCodes,
} from '../scan-lib.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCAN = join(HERE, '..', 'axe-scan.mjs');
const FIX = join(HERE, 'fixtures');

test('wcagCodes lê tags de critério e ignora tags de nível', () => {
  assert.deepEqual(wcagCodes(['cat.color', 'wcag2aa', 'wcag143', 'wcag1410', 'wcag21aa', 'wcag22aa', 'best-practice']), ['1.4.3', '1.4.10']);
});

test('parseViewport aceita preset e LARGURAxALTURA e rejeita o resto', () => {
  assert.equal(parseViewport('mobile-320').width, 320);
  assert.deepEqual(parseViewport('1024x768'), { name: '1024x768', width: 1024, height: 768, isMobile: false, hasTouch: false });
  assert.equal(parseViewport('1024x768').hasTouch, false);
  assert.equal(parseViewport('600x900').hasTouch, true);
  assert.equal(parseViewport('celular'), null);
});

test('parseArgs junta repetições, valida números e acusa argumento desconhecido', () => {
  const { opts, problems } = parseArgs(['--url', 'a.html', '--url', 'b.html', '--viewport', 'desktop,mobile', '--keyboard-trace', '30', '--experimental']);
  assert.deepEqual(opts.urls, ['a.html', 'b.html']);
  assert.deepEqual(opts.viewports, ['desktop', 'mobile']);
  assert.equal(opts.keyboardTrace, 30);
  assert.equal(opts.experimental, true);
  assert.deepEqual(problems, []);
  assert.equal(parseArgs(['--max-nodes', 'abc']).problems.length, 1);
  assert.equal(parseArgs(['--url']).problems.length, 1);
  assert.equal(parseArgs(['--rm']).problems.length, 1);
});

test('normalizeUrl aceita http(s), file e caminho local; recusa outros esquemas', () => {
  const n = (u) => normalizeUrl(u, '/work', pathToFileURL, resolve);
  assert.equal(n('http://localhost:5173/').url, 'http://localhost:5173/');
  assert.equal(n('protótipo/index.html').url, 'file:///work/prot%C3%B3tipo/index.html');
  assert.match(n('javascript:alert(1)').error, /esquema não permitido/);
  assert.match(n('data:text/html,x').error, /esquema não permitido/);
});

test('validateScenario exige nome único e passos com uma ação válida', () => {
  assert.equal(validateScenario({}).problems.length, 1);
  const ok = validateScenario({ scans: [{ name: 'a', steps: [{ click: '#x' }, { fill: { selector: '#c', value: '1' } }, { press: 'Tab' }, { wait: 200 }] }] });
  assert.deepEqual(ok.problems, []);
  const bad = validateScenario({ scans: [
    { name: 'a', steps: [{ click: 1 }, { wait: 99999 }, { hover: '#x' }, { click: '#x', wait: 1 }] },
    { name: 'a', viewports: ['xyz'] },
  ] });
  assert.equal(bad.problems.length, 6);
});

test('simplifyAxe limita nós, encurta HTML e preserva critérios', () => {
  const nodes = Array.from({ length: 5 }, (_, i) => ({ target: [`#n${i}`], html: `<p>${'x'.repeat(500)}</p>`, failureSummary: 'Fix any of the following:\n  contrast' }));
  const out = simplifyAxe({ violations: [{ id: 'color-contrast', impact: 'serious', tags: ['wcag2aa', 'wcag143'], help: 'h', helpUrl: 'u', nodes }], incomplete: [], passes: [{ id: 'label' }], inapplicable: [{ id: 'blink' }] }, 2);
  assert.equal(out.violations[0].nodeCount, 5);
  assert.equal(out.violations[0].nodes.length, 2);
  assert.ok(out.violations[0].nodes[0].html.length <= 200);
  assert.deepEqual(out.violations[0].wcag, ['1.4.3']);
  assert.deepEqual(out.passed, ['label']);
});

test('summarizeByCriterion soma nós por critério e lista regras que passaram', () => {
  const run = { axe: { violations: [{ id: 'link-name', wcag: ['2.4.4', '4.1.2'], nodeCount: 2 }], incomplete: [{ id: 'color-contrast', wcag: ['1.4.3'], nodeCount: 1 }], passed: ['label'] }, ruleCodes: { label: ['4.1.2'] } };
  const by = summarizeByCriterion([run, run]);
  assert.equal(by['2.4.4'].violations, 4);
  assert.equal(by['1.4.3'].incomplete, 2);
  assert.deepEqual(by['4.1.2'].passedRules, ['label']);
  assert.deepEqual(Object.keys(by), ['1.4.3', '2.4.4', '4.1.2']);
});

test('analyzeKeyboardTrace sinaliza revisita, coberto, fora da tela e sem indicador', () => {
  const stop = (target, extra = {}) => ({ target, tag: 'button', visibleInViewport: true, obscured: false, indicator: true, ...extra });
  assert.deepEqual(analyzeKeyboardTrace([stop('a'), stop('b'), stop('c')]), []);
  const kinds = analyzeKeyboardTrace([stop('a'), stop('b', { obscured: true }), stop('c', { visibleInViewport: false }), stop('d', { indicator: false }), stop('d')]).map((f) => f.kind);
  assert.deepEqual(kinds.sort(), ['no-indicator-detected', 'obscured', 'offscreen', 'possible-trap', 'repeat']);
});

const tools = spawnSync('node', [SCAN, '--check-tools'], { encoding: 'utf8' });
const hasTools = tools.status === 0;

test('varredura real: página com defeitos é acusada e página correta não', { skip: !hasTools && 'ferramentas (playwright-core, @axe-core/playwright) não instaladas' }, () => {
  const run = (file, vp) => JSON.parse(spawnSync('node', [SCAN, '--url', join(FIX, file), '--viewport', vp, '--keyboard-trace', '15'], { encoding: 'utf8' }).stdout);
  const bad = run('bad.html', 'desktop');
  assert.equal(bad.ok, true, JSON.stringify(bad.problems));
  const ids = bad.data.runs[0].axe.violations.map((v) => v.id);
  for (const id of ['image-alt', 'button-name', 'label', 'color-contrast', 'document-title', 'html-has-lang', 'link-name', 'target-size']) assert.ok(ids.includes(id), `faltou ${id}`);
  assert.ok(!ids.includes('region'), 'regra de boas práticas não deve rodar com tags WCAG');
  assert.equal(bad.data.byCriterion['2.5.8'].violations >= 1, true);
  const good = run('good.html', 'mobile-320');
  assert.deepEqual(good.data.runs[0].axe.violations, []);
  assert.equal(good.data.runs[0].layout.horizontalOverflow, false);
  assert.equal(good.data.runs[0].keyboard.completedCycle, true);
  assert.deepEqual(good.data.runs[0].keyboard.flags, []);
});

test('varredura real: cenário com passos captura o estado posterior ao clique', { skip: !hasTools && 'ferramentas não instaladas' }, () => {
  const out = JSON.parse(spawnSync('node', [SCAN, '--scenario', join(FIX, 'scenario.json')], { encoding: 'utf8' }).stdout);
  assert.equal(out.ok, true, JSON.stringify(out.problems));
  const imgs = (name) => out.data.runs.find((r) => r.scan === name).axe.violations.find((v) => v.id === 'image-alt').nodeCount;
  assert.equal(imgs('inicial'), 1);
  assert.equal(imgs('depois-do-clique'), 2);
});

test('entrada inválida falha com envelope claro e código 2', () => {
  const r = spawnSync('node', [SCAN, '--url', 'javascript:alert(1)'], { encoding: 'utf8' });
  const hasToolsOrNot = JSON.parse(r.stdout);
  assert.equal(r.status, 2);
  assert.ok(['invalid-input', 'missing-tools'].includes(hasToolsOrNot.status));
});
