#!/usr/bin/env node
// Varredura automatizada de acessibilidade (axe-core via Playwright) em vários viewports e estados.
//
// Uso:
//   node axe-scan.mjs --check-tools
//   node axe-scan.mjs --url <http(s)://… | arquivo.html> [--url …] [--viewport desktop,tablet,mobile]
//        [--scenario cenarios.json] [--keyboard-trace 40] [--tags wcag2a,wcag2aa] [--experimental]
//        [--max-nodes 10] [--out resultado.json]
//
// Saída (stdout): {"ok","status","data","problems","questions"}.
//   status: "ok" | "missing-tools" | "missing-browser" | "invalid-input" | "error".
// Achado não é falha do script: o código de saída é 0 quando a varredura rodou. A saída é evidência
// para o relatório, nunca veredito de conformidade (ver METHOD.md da skill).
//
// Ferramentas (não vão na skill): playwright-core + @axe-core/playwright, instaladas em
// A11Y_TOOLS_DIR (padrão: ~/.cache/ai-dev-kit/accessibility-review) — Node >= 22.12.
// Navegador: Chrome instalado (padrão) | A11Y_BROWSER_CHANNEL | A11Y_BROWSER_PATH | Chromium do Playwright.

import { createRequire } from 'node:module';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import {
  DEFAULT_TAGS, FORCE_ENABLE_RULES, MAX_WAIT_MS, VIEWPORT_PRESETS, analyzeKeyboardTrace, envelope,
  normalizeUrl, parseArgs, parseViewport, simplifyAxe, summarizeByCriterion, validateScenario, wcagCodes,
} from './scan-lib.mjs';

const TOOLS_DIR = process.env.A11Y_TOOLS_DIR || join(homedir(), '.cache', 'ai-dev-kit', 'accessibility-review');
const PINNED = { 'playwright-core': '1.64.1', '@axe-core/playwright': '4.14.0' };
const INSTALL_CMD = `npm install --prefix "${TOOLS_DIR}" playwright-core@${PINNED['playwright-core']} @axe-core/playwright@${PINNED['@axe-core/playwright']}`;
const HELP = `Uso: node axe-scan.mjs --url <url|arquivo> [--viewport desktop,tablet,mobile] [--scenario arq.json]
       [--keyboard-trace N] [--tags …] [--experimental] [--max-nodes N] [--out arq.json] | --check-tools
Viewports prontos: ${Object.keys(VIEWPORT_PRESETS).join(', ')} (ou LARGURAxALTURA).`;

function done(result, code = 0) {
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  process.exit(code);
}

function loadTools() {
  const missing = [];
  const tools = {};
  for (const dir of [TOOLS_DIR, process.cwd()]) {
    try {
      const req = createRequire(join(dir, 'noop.js'));
      tools.chromium = tools.chromium || req('playwright-core').chromium;
      tools.AxeBuilder = tools.AxeBuilder || req('@axe-core/playwright').AxeBuilder || req('@axe-core/playwright').default;
      tools.axeVersion = tools.axeVersion || req('axe-core/package.json').version;
      tools.playwrightVersion = tools.playwrightVersion || req('playwright-core/package.json').version;
    } catch (e) { missing.push(`${dir}: ${e.code || e.message}`); }
    if (tools.chromium && tools.AxeBuilder) return { tools };
  }
  return { error: missing };
}

async function launchBrowser(chromium) {
  const attempts = [];
  const exe = process.env.A11Y_BROWSER_PATH;
  if (exe) {
    if (!existsSync(exe)) throw Object.assign(new Error(`A11Y_BROWSER_PATH aponta para algo inexistente: ${exe}`), { code: 'bad-override' });
    return chromium.launch({ executablePath: exe });
  }
  const channel = process.env.A11Y_BROWSER_CHANNEL;
  const order = channel ? [{ channel }] : [{ channel: 'chrome' }, {}];
  for (const opt of order) {
    try { return await chromium.launch(opt); } catch (e) { attempts.push(`${opt.channel || 'chromium do Playwright'}: ${String(e.message).split('\n')[0]}`); }
  }
  throw Object.assign(new Error(attempts.join(' | ')), { code: 'no-browser' });
}

async function runSteps(page, steps) {
  for (const step of steps || []) {
    if ('click' in step) await page.locator(step.click).first().click({ timeout: 8000 });
    else if ('fill' in step) await page.locator(step.fill.selector).first().fill(step.fill.value, { timeout: 8000 });
    else if ('press' in step) {
      if (typeof step.press === 'string') await page.keyboard.press(step.press);
      else await page.locator(step.press.selector || 'body').first().press(step.press.key);
    } else if ('waitFor' in step) await page.locator(step.waitFor).first().waitFor({ timeout: 8000 });
    else if ('wait' in step) await page.waitForTimeout(Math.min(step.wait, MAX_WAIT_MS));
    else if ('eval' in step) await page.evaluate(step.eval);
  }
}

// Percorre o foco com Tab e descreve cada parada. Heurística: o veredito é manual (manual-checks.md).
async function keyboardTrace(page, limit) {
  await page.evaluate(() => { if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); window.scrollTo(0, 0); });
  const stops = [];
  let completedCycle = false;
  let pendingBody = null;
  for (let i = 0; i < limit; i++) {
    await page.keyboard.press('Tab');
    const stop = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return { target: null, tag: 'none' };
      const css = (e) => {
        if (e.id) return `${e.tagName.toLowerCase()}#${CSS.escape(e.id)}`;
        const parts = [];
        for (let n = e; n && n.nodeType === 1 && parts.length < 4; n = n.parentElement) {
          const sib = n.parentElement ? [...n.parentElement.children].filter((c) => c.tagName === n.tagName) : [n];
          parts.unshift(`${n.tagName.toLowerCase()}${sib.length > 1 ? `:nth-of-type(${sib.indexOf(n) + 1})` : ''}`);
        }
        return parts.join(' > ');
      };
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      // Elemento inline pode quebrar linha: o retângulo englobante cobre vizinhos. Testa o centro de
      // cada fragmento e só considera coberto se nenhum deles aponta para o próprio elemento.
      const frags = [...el.getClientRects()].filter((f) => f.width > 0 && f.height > 0);
      const covered = frags.length > 0 && frags.every((f) => {
        const cx = Math.min(Math.max(f.left + f.width / 2, 0), innerWidth - 1);
        const cy = Math.min(Math.max(f.top + f.height / 2, 0), innerHeight - 1);
        const top = document.elementFromPoint(cx, cy);
        return !!top && top !== el && !el.contains(top) && !top.contains(el);
      });
      const outlined = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0;
      const labelled = el.getAttribute('aria-label') || (el.labels && el.labels[0] && el.labels[0].textContent) || el.textContent || el.getAttribute('title') || el.getAttribute('alt') || '';
      return {
        target: css(el), tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || null,
        name: labelled.replace(/\s+/g, ' ').trim().slice(0, 80),
        rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        visibleInViewport: r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth,
        obscured: covered,
        indicator: outlined || cs.boxShadow !== 'none',
      };
    });
    // Tab que sai da página passa pelo body (interface do navegador) antes de voltar ao primeiro
    // elemento: isso fecha o ciclo e não é achado. Body no meio do percurso é foco perdido.
    if (stops.length && stop.target === stops[0].target) { completedCycle = true; break; }
    if (stops.length && (stop.tag === 'body' || stop.tag === 'html') && i === limit - 1) { stops.push(stop); break; }
    if (stops.length && (stop.tag === 'body' || stop.tag === 'html')) {
      pendingBody = stop;
      continue;
    }
    if (pendingBody) { stops.push(pendingBody); pendingBody = null; }
    stops.push(stop);
  }
  return { stops, completedCycle, limit, flags: analyzeKeyboardTrace(stops) };
}

async function main() {
  const { opts, problems } = parseArgs(process.argv.slice(2));
  if (opts.help) { process.stdout.write(`${HELP}\n`); process.exit(0); }
  if (problems.length) done(envelope(false, 'invalid-input', {}, problems), 2);

  const { tools, error } = loadTools();
  if (opts.checkTools) {
    if (tools) done(envelope(true, 'ok', { axe: tools.axeVersion, playwrightCore: tools.playwrightVersion, toolsDir: TOOLS_DIR }));
    done(envelope(false, 'missing-tools', { toolsDir: TOOLS_DIR, installCommand: INSTALL_CMD }, error, ['Posso rodar o comando de instalação em toolsDir?']), 2);
  }
  if (!tools) done(envelope(false, 'missing-tools', { toolsDir: TOOLS_DIR, installCommand: INSTALL_CMD }, error, ['Posso rodar o comando de instalação em toolsDir?']), 2);

  let scans = [];
  const inputProblems = [];
  if (opts.scenario) {
    let doc;
    try { doc = JSON.parse(readFileSync(resolve(opts.scenario), 'utf8')); } catch (e) { inputProblems.push(`cenário ilegível: ${e.message}`); }
    if (doc) {
      const v = validateScenario(doc);
      // Caminho relativo num cenário vale a partir da pasta do próprio arquivo.
      scans = v.scans.map((scan) => ({ ...scan, base: dirname(resolve(opts.scenario)) }));
      inputProblems.push(...v.problems);
    }
  }
  opts.urls.forEach((u, i) => scans.push({ name: opts.urls.length === 1 && !scans.length ? 'pagina' : `url-${i + 1}`, url: u, steps: [] }));
  if (!scans.length) inputProblems.push('informe --url ou --scenario');
  const viewportSpecs = opts.viewports.length ? opts.viewports : ['desktop', 'tablet', 'mobile'];
  for (const vp of viewportSpecs) if (!parseViewport(vp)) inputProblems.push(`viewport inválido: ${vp}`);
  const urls = new Map();
  for (const scan of scans) {
    const n = normalizeUrl(scan.url || opts.urls[0] || '', scan.base || process.cwd(), pathToFileURL, resolve);
    if (n.error || !n.url) inputProblems.push(`${scan.name}: ${n.error || 'falta "url" (use --url como padrão)'}`);
    else urls.set(scan.name, n.url);
  }
  if (inputProblems.length) done(envelope(false, 'invalid-input', {}, inputProblems), 2);

  const tags = opts.tags || [...DEFAULT_TAGS, ...(opts.experimental ? ['experimental'] : [])];
  let browser;
  try { browser = await launchBrowser(tools.chromium); } catch (e) {
    done(envelope(false, e.code === 'bad-override' ? 'error' : 'missing-browser',
      { installCommand: `npx --prefix "${TOOLS_DIR}" playwright-core install chromium` }, [e.message],
      e.code === 'bad-override' ? [] : ['Posso instalar o Chromium do Playwright, ou há um Chrome para usar via A11Y_BROWSER_PATH?']), 2);
  }

  const runs = [];
  const runProblems = [];
  try {
    for (const scan of scans) {
      for (const vpSpec of scan.viewports || viewportSpecs) {
        const vp = parseViewport(vpSpec);
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, isMobile: vp.isMobile, hasTouch: vp.hasTouch, deviceScaleFactor: vp.isMobile ? 2 : 1 });
        const page = await context.newPage();
        const label = `${scan.name} @ ${vp.name}`;
        try {
          await page.goto(urls.get(scan.name), { waitUntil: 'load', timeout: 30000 });
          await runSteps(page, scan.steps);
          // options() substitui o filtro de tags do builder: chamar antes de withTags().
          const builder = new tools.AxeBuilder({ page });
          builder.options({ rules: Object.fromEntries(FORCE_ENABLE_RULES.map((id) => [id, { enabled: true }])) });
          builder.withTags(tags);
          const raw = await builder.analyze();
          const ruleCodes = {};
          for (const r of [...raw.violations, ...raw.incomplete, ...raw.passes, ...raw.inapplicable]) ruleCodes[r.id] = wcagCodes(r.tags);
          const run = {
            scan: scan.name, url: urls.get(scan.name), viewport: { name: vp.name, width: vp.width, height: vp.height },
            title: await page.title(), axe: simplifyAxe(raw, opts.maxNodes), ruleCodes,
          };
          // Evidência para 1.4.10 (Realinhar): em 320 px não pode haver rolagem horizontal da página.
          const dim = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
          run.layout = { ...dim, horizontalOverflow: dim.scrollWidth > dim.clientWidth + 1 };
          if (opts.keyboardTrace) run.keyboard = await keyboardTrace(page, opts.keyboardTrace);
          runs.push(run);
        } catch (e) { runProblems.push(`${label}: ${String(e.message).split('\n')[0]}`); } finally { await context.close(); }
      }
    }
  } finally { await browser.close(); }

  const data = {
    tool: { axe: tools.axeVersion, playwrightCore: tools.playwrightVersion },
    tags, forcedRules: FORCE_ENABLE_RULES, viewports: viewportSpecs,
    runs: runs.map(({ ruleCodes, ...rest }) => ({ ...rest, axe: { ...rest.axe, passed: rest.axe.passed.length, inapplicable: rest.axe.inapplicable.length, passedRules: rest.axe.passed } })),
    byCriterion: summarizeByCriterion(runs),
    notice: 'Resultado automatizado cobre parte dos critérios; sem achado não significa conforme. Complete com manual-checks.md.',
  };
  const result = envelope(runs.length > 0, runs.length ? (runProblems.length ? 'partial' : 'ok') : 'error', data, runProblems);
  if (opts.out) writeFileSync(resolve(opts.out), `${JSON.stringify(result, null, 2)}\n`);
  done(result, runs.length ? 0 : 2);
}

main().catch((e) => done(envelope(false, 'error', {}, [String(e && e.message ? e.message : e)]), 2));
