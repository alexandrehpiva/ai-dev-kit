// Funções puras do axe-scan.mjs (sem rede, sem navegador): argumentos, viewports,
// validação de cenários, normalização do resultado do axe e envelope JSON.
// Testadas em tests/scan-lib.test.mjs (node --test).

export const DEFAULT_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

// Regras que o axe desliga por padrão mas que cobrem critérios A/AA: ligadas à força.
export const FORCE_ENABLE_RULES = ['target-size', 'audio-caption'];

export const VIEWPORT_PRESETS = {
  desktop: { width: 1280, height: 800, isMobile: false, hasTouch: false },
  tablet: { width: 820, height: 1180, isMobile: true, hasTouch: true },
  mobile: { width: 390, height: 844, isMobile: true, hasTouch: true },
  // 320 CSS px é a largura de referência do critério 1.4.10 (Realinhar).
  'mobile-320': { width: 320, height: 568, isMobile: true, hasTouch: true },
};

export const STEP_KINDS = ['click', 'fill', 'press', 'waitFor', 'wait', 'eval'];
export const MAX_WAIT_MS = 5000;

export function envelope(ok, status, data = {}, problems = [], questions = []) {
  return { ok, status, data, problems, questions };
}

export function parseViewport(spec) {
  const key = String(spec).trim();
  if (VIEWPORT_PRESETS[key]) return { name: key, ...VIEWPORT_PRESETS[key] };
  const m = key.match(/^(\d{2,5})x(\d{2,5})$/);
  if (!m) return null;
  const width = Number(m[1]);
  const height = Number(m[2]);
  return { name: key, width, height, isMobile: width < 900, hasTouch: width < 900 };
}

const FLAGS_WITH_VALUE = new Set([
  '--url', '--viewport', '--scenario', '--tags', '--max-nodes', '--out', '--keyboard-trace',
]);
const BOOLEAN_FLAGS = new Set(['--experimental', '--check-tools', '--help']);

export function parseArgs(argv) {
  const opts = {
    urls: [], viewports: [], scenario: null, tags: null, maxNodes: 10, out: null,
    keyboardTrace: 0, experimental: false, checkTools: false, help: false,
  };
  const problems = [];
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (BOOLEAN_FLAGS.has(flag)) {
      if (flag === '--experimental') opts.experimental = true;
      if (flag === '--check-tools') opts.checkTools = true;
      if (flag === '--help') opts.help = true;
      continue;
    }
    if (!FLAGS_WITH_VALUE.has(flag)) {
      problems.push(`argumento desconhecido: ${flag}`);
      continue;
    }
    const value = argv[++i];
    if (value === undefined || value.startsWith('--')) {
      problems.push(`${flag} exige um valor`);
      continue;
    }
    if (flag === '--url') opts.urls.push(value);
    else if (flag === '--viewport') opts.viewports.push(...value.split(',').filter(Boolean));
    else if (flag === '--scenario') opts.scenario = value;
    else if (flag === '--tags') opts.tags = value.split(',').filter(Boolean);
    else if (flag === '--out') opts.out = value;
    else if (flag === '--max-nodes' || flag === '--keyboard-trace') {
      const n = Number(value);
      if (!Number.isInteger(n) || n < 1 || n > 500) problems.push(`${flag} deve ser inteiro entre 1 e 500`);
      else if (flag === '--max-nodes') opts.maxNodes = n;
      else opts.keyboardTrace = n;
    }
  }
  return { opts, problems };
}

// Só http(s) e arquivos locais: nunca javascript:, data: etc.
export function normalizeUrl(input, cwd, pathToFileURL, resolve) {
  if (/^https?:\/\//i.test(input) || /^file:\/\//i.test(input)) return { url: input };
  if (/^[a-z][a-z0-9+.-]*:/i.test(input) && !/^[a-z]:[\\/]/i.test(input)) {
    return { error: `esquema não permitido em --url: ${input.split(':')[0]}` };
  }
  return { url: pathToFileURL(resolve(cwd, input)).href };
}

export function validateScenario(doc) {
  const problems = [];
  if (!doc || !Array.isArray(doc.scans) || doc.scans.length === 0) {
    return { scans: [], problems: ['o arquivo de cenário precisa de "scans": [ ... ] não vazio'] };
  }
  const names = new Set();
  doc.scans.forEach((scan, idx) => {
    const where = `scans[${idx}]`;
    if (!scan || typeof scan.name !== 'string' || !scan.name.trim()) problems.push(`${where}: falta "name"`);
    else if (names.has(scan.name)) problems.push(`${where}: nome repetido "${scan.name}"`);
    else names.add(scan.name);
    if (scan.viewports !== undefined && !Array.isArray(scan.viewports)) problems.push(`${where}: "viewports" deve ser lista`);
    for (const vp of scan.viewports || []) {
      if (!parseViewport(vp)) problems.push(`${where}: viewport inválido "${vp}"`);
    }
    (scan.steps || []).forEach((step, j) => {
      const kinds = Object.keys(step || {}).filter((k) => STEP_KINDS.includes(k));
      const w = `${where}.steps[${j}]`;
      if (kinds.length !== 1 || Object.keys(step).length !== 1) {
        problems.push(`${w}: cada passo tem exatamente uma ação de ${STEP_KINDS.join(', ')}`);
        return;
      }
      const kind = kinds[0];
      const v = step[kind];
      if (kind === 'fill' && !(v && typeof v.selector === 'string' && typeof v.value === 'string')) problems.push(`${w}: fill exige {selector, value}`);
      if (kind === 'press' && !(typeof v === 'string' || (v && typeof v.key === 'string'))) problems.push(`${w}: press exige "Tecla" ou {selector, key}`);
      if (['click', 'waitFor', 'eval'].includes(kind) && typeof v !== 'string') problems.push(`${w}: ${kind} exige texto`);
      if (kind === 'wait' && !(Number.isInteger(v) && v >= 0 && v <= MAX_WAIT_MS)) problems.push(`${w}: wait exige inteiro de 0 a ${MAX_WAIT_MS} (ms)`);
    });
  });
  return { scans: doc.scans, problems };
}

// "wcag143" -> "1.4.3"; "wcag1410" -> "1.4.10"; tags de nível (wcag2a, wcag21aa) não casam.
export function wcagCodes(tags) {
  const codes = [];
  for (const tag of tags || []) {
    const m = String(tag).match(/^wcag(\d)(\d)(\d+)$/);
    if (m) codes.push(`${m[1]}.${m[2]}.${m[3]}`);
  }
  return codes;
}

function truncate(text, max) {
  const s = String(text == null ? '' : text).replace(/\s+/g, ' ').trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

function simplifyRule(rule, maxNodes) {
  return {
    id: rule.id,
    impact: rule.impact || null,
    wcag: wcagCodes(rule.tags),
    tags: (rule.tags || []).filter((t) => /^wcag(2a|2aa|21a|21aa|22aa|2aaa)$/.test(t) || t === 'best-practice'),
    help: rule.help,
    helpUrl: rule.helpUrl,
    nodeCount: (rule.nodes || []).length,
    nodes: (rule.nodes || []).slice(0, maxNodes).map((n) => ({
      target: (n.target || []).map(String),
      html: truncate(n.html, 200),
      summary: truncate(n.failureSummary, 300),
    })),
  };
}

export function simplifyAxe(results, maxNodes = 10) {
  return {
    violations: (results.violations || []).map((r) => simplifyRule(r, maxNodes)),
    incomplete: (results.incomplete || []).map((r) => simplifyRule(r, maxNodes)),
    passed: (results.passes || []).map((r) => r.id),
    inapplicable: (results.inapplicable || []).map((r) => r.id),
  };
}

// Agrega por critério: o que falhou, o que ficou "incompleto" e quais regras rodaram sem achado.
export function summarizeByCriterion(runs) {
  const by = {};
  const touch = (code) => (by[code] = by[code] || { violations: 0, incomplete: 0, rules: new Set(), passedRules: new Set() });
  for (const run of runs) {
    for (const v of run.axe.violations) for (const c of v.wcag) { const e = touch(c); e.violations += v.nodeCount; e.rules.add(v.id); }
    for (const v of run.axe.incomplete) for (const c of v.wcag) { const e = touch(c); e.incomplete += v.nodeCount; e.rules.add(v.id); }
    for (const id of run.axe.passed) for (const c of run.ruleCodes[id] || []) touch(c).passedRules.add(id);
  }
  const out = {};
  for (const code of Object.keys(by).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))) {
    out[code] = {
      violations: by[code].violations,
      incomplete: by[code].incomplete,
      rules: [...by[code].rules].sort(),
      passedRules: [...by[code].passedRules].sort(),
    };
  }
  return out;
}

// Descreve a parada de foco do teclado a partir do que o navegador devolveu (ver axe-scan.mjs).
export function analyzeKeyboardTrace(stops) {
  const flags = [];
  const seen = new Map();
  stops.forEach((s, i) => {
    if (!s.target) return;
    if (seen.has(s.target)) flags.push({ kind: 'repeat', at: i, target: s.target, firstAt: seen.get(s.target) });
    else seen.set(s.target, i);
    if (s.tag === 'body' || s.tag === 'html') flags.push({ kind: 'focus-on-body', at: i });
    if (s.obscured) flags.push({ kind: 'obscured', at: i, target: s.target });
    if (!s.visibleInViewport) flags.push({ kind: 'offscreen', at: i, target: s.target });
    if (s.indicator === false) flags.push({ kind: 'no-indicator-detected', at: i, target: s.target });
  });
  const trapIdx = stops.findIndex((s, i) => i > 0 && stops[i - 1].target && s.target === stops[i - 1].target);
  if (trapIdx > 0) flags.push({ kind: 'possible-trap', at: trapIdx, target: stops[trapIdx].target });
  return flags;
}
