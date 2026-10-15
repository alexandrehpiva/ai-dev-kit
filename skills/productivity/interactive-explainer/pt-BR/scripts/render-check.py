#!/usr/bin/env python3
"""Verifica um explicador gerado num Chrome/Chromium headless: geometria das setas, erros de script e capturas.

  python3 render-check.py <explicador.html> [--widths 1440,768,375] [--shots <pasta>] [--views a,b/c/0]
                          [--height 1400] [--no-selftest] [--timeout 90]

O que roda (para cada largura):
  1. Autoteste do motor (`?selftest`): para cada etapa de cada quadro mede nós, setas e rótulos e relata
     nós sobrepostos, seta que não encosta nas caixas, seta que atravessa um nó (aviso), rótulo que cobre
     um nó (aviso), dois rótulos sobrepostos (aviso) e rolagem horizontal da PÁGINA (erro).
  2. Erros de console/JS capturados do próprio Chrome.
  2b. Com --no-selftest (HTML que não veio do motor, como os snippets) só roda a conferência de console.
  3. Com --shots, uma captura PNG por visão (`--views`, padrão: cada aba) e largura.
Status do envelope:
  PASS       nenhum erro (avisos podem existir)
  FAIL       pelo menos um erro (geometria, JS, página que rola de lado) — ok=false
  NO_CHROME  Chrome não encontrado; defina CHROME_PATH — ok=false (não foi possível verificar)
  UNREADABLE o arquivo não existe — ok=false
Override: CHROME_PATH aponta para o executável; se apontar para algo inexistente, é erro (não cai em default).
Limite: o Chrome headless mede o layout real, mas não substitui olhar uma captura: a skill manda fazer os dois.
Exit: 0 ok, 1 problemas, 2 uso incorreto.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explainer_lib as lib  # noqa: E402

MAC_APPS = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
]
LINUX_BINS = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']


def find_chrome():
    """Devolve (caminho, erro). Override inexistente é erro, não cai em default."""
    override = os.environ.get('CHROME_PATH')
    if override:
        if not Path(override).is_file():
            return None, f'CHROME_PATH aponta para algo inexistente: {override}'
        return override, None
    candidates = []
    if sys.platform == 'darwin':
        candidates = MAC_APPS
    elif sys.platform.startswith('win'):
        for var in ('ProgramFiles', 'ProgramFiles(x86)', 'LocalAppData'):
            base = os.environ.get(var)
            if base:
                candidates.append(str(Path(base) / 'Google/Chrome/Application/chrome.exe'))
                candidates.append(str(Path(base) / 'Microsoft/Edge/Application/msedge.exe'))
    for path in candidates:
        if Path(path).is_file():
            return path, None
    for name in LINUX_BINS:
        found = shutil.which(name)
        if found:
            return found, None
    return None, 'Chrome/Chromium não encontrado; defina CHROME_PATH com o executável'


HARNESS = """<!doctype html><meta charset="utf-8"><title>harness</title>
<style>html,body{margin:0;background:#8a8a8a}iframe{border:0;display:block;width:%(w)dpx;height:%(h)dpx;background:#fff}</style>
<iframe id="f" src="%(src)s"></iframe>
<script>
var f = document.getElementById('f');
f.addEventListener('load', function () {
  var w = f.contentWindow;
  if (%(selftest)s) {
    (w.document.fonts && w.document.fonts.ready ? w.document.fonts.ready : Promise.resolve()).then(function () { return w.ExplainerSelfTest(); })
      .then(function (r) { document.documentElement.setAttribute('data-selftest', JSON.stringify(r)); })
      .catch(function (e) { document.documentElement.setAttribute('data-selftest-error', String(e)); });
  }
});
</script>
"""


def write_harness(directory, src, width, height, selftest):
    """O Chrome headless não aceita janela menor que ~500px: o explicador roda num iframe da largura exata,
    e as media queries valem para a largura do iframe. Exige --allow-file-access-from-files (mesma origem)."""
    path = Path(directory) / f'harness-{width}-{abs(hash((src, selftest))) % 10**8}.html'
    path.write_text(HARNESS % {'w': width, 'h': height, 'src': src, 'selftest': 'true' if selftest else 'false'}, encoding='utf-8')
    return path


def base_cmd(chrome, width, height, profile):
    cmd = [chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
           '--disable-extensions', '--force-device-scale-factor=1', '--allow-file-access-from-files',
           f'--user-data-dir={profile}', f'--window-size={max(width, 520)},{height}']
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        cmd.append('--no-sandbox')  # Chrome como root (contêiner) exige; fora disso mantém o sandbox
    return cmd


def run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def parse_selftest(dom):
    m = re.search(r'data-selftest="([^"]*)"', dom)
    if not m:
        return None
    return json.loads(html.unescape(m.group(1)))


CONSOLE_RE = re.compile(r'CONSOLE[^\]]*\]\s*"(.*)", source:', re.S)


def console_errors(stderr):
    out = []
    for line in stderr.splitlines():
        if 'CONSOLE' not in line:
            continue
        m = CONSOLE_RE.search(line)
        msg = m.group(1) if m else line
        if msg.startswith('SELFTEST '):
            continue
        if re.search(r'Uncaught|TypeError|ReferenceError|SyntaxError|Failed to load resource|net::ERR', msg):
            out.append(msg[:300])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html')
    ap.add_argument('--widths', default='1440,768,375')
    ap.add_argument('--shots')
    ap.add_argument('--views')
    ap.add_argument('--height', type=int, default=1400)
    ap.add_argument('--no-selftest', action='store_true')
    ap.add_argument('--timeout', type=int, default=90)
    args = ap.parse_args(argv)

    path = Path(args.html).resolve()
    if not path.is_file():
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': str(path), 'msg': 'arquivo não encontrado'}]))
    try:
        widths = [int(w) for w in args.widths.split(',') if w.strip()]
    except ValueError:
        lib.emit(lib.envelope(False, 'UNREADABLE', problems=[{'level': 'error', 'where': '--widths', 'msg': 'lista de inteiros separados por vírgula'}]), 2)
    chrome, err = find_chrome()
    if not chrome:
        lib.emit(lib.envelope(False, 'NO_CHROME', problems=[{'level': 'error', 'where': 'chrome', 'msg': err}],
                              questions=['Informe o caminho do Chrome/Chromium em CHROME_PATH para eu poder verificar o render.']))

    problems, selftests, shots, console = [], [], [], []
    uri = path.as_uri()
    with tempfile.TemporaryDirectory(prefix='explainer-check-') as profile:
        if not args.no_selftest:
            for w in widths:
                harness = write_harness(profile, uri, w, args.height, True)
                cmd = base_cmd(chrome, w, args.height, profile) + ['--enable-logging=stderr', '--v=0', '--virtual-time-budget=12000', '--dump-dom', harness.as_uri()]
                proc = run(cmd, args.timeout)
                if proc is None:
                    problems.append({'level': 'error', 'where': f'selftest@{w}', 'msg': f'Chrome não terminou em {args.timeout}s'})
                    continue
                result = parse_selftest(proc.stdout)
                if result is None:
                    problems.append({'level': 'error', 'where': f'selftest@{w}', 'msg': 'o autoteste não escreveu resultado (motor ausente, JS quebrado ou HTML que não é um explicador)'})
                    continue
                selftests.append({'width': w, 'stats': result['stats'], 'ok': result['ok']})
                for p in result['problems']:
                    problems.append({'level': p['level'], 'where': f'{p["where"]}@{w}', 'msg': p['msg']})
                for msg in console_errors(proc.stderr):
                    console.append(f'@{w}: {msg}')
                    problems.append({'level': 'error', 'where': f'console@{w}', 'msg': msg})
        if args.no_selftest:
            # sem autoteste (HTML que não é gerado pelo motor, ex.: snippets): ainda confere erros de console e rolagem horizontal
            for w in widths:
                harness = write_harness(profile, uri, w, args.height, False)
                cmd = base_cmd(chrome, w, args.height, profile) + ['--enable-logging=stderr', '--v=0', '--virtual-time-budget=6000', '--dump-dom', harness.as_uri()]
                proc = run(cmd, args.timeout)
                if proc is None:
                    problems.append({'level': 'error', 'where': f'console@{w}', 'msg': f'Chrome não terminou em {args.timeout}s'})
                    continue
                for msg in console_errors(proc.stderr):
                    console.append(f'@{w}: {msg}')
                    problems.append({'level': 'error', 'where': f'console@{w}', 'msg': msg})
        if args.shots:
            outdir = Path(args.shots)
            outdir.mkdir(parents=True, exist_ok=True)
            views = [v for v in (args.views or '').split(',') if v]
            if not views:
                ms = re.findall(r'<script type="application/json" id="explainer-data">(.*?)</script>', path.read_text(encoding='utf-8'), re.S)
                try:
                    views = [t['id'] for t in json.loads(ms[-1].replace('<\\/', '</'))['tabs']] if ms else ['']
                except (ValueError, KeyError, TypeError):
                    views = ['']
            for w in widths:
                for v in views:
                    name = re.sub(r'[^A-Za-z0-9_.-]+', '_', v or 'inicio')
                    target = outdir / f'{path.stem}-{name}-{w}.png'
                    if target.exists():
                        target.unlink()
                    harness = write_harness(profile, f'{uri}#{v}' if v else uri, w, args.height, False)
                    cmd = base_cmd(chrome, w, args.height, profile) + ['--virtual-time-budget=8000', f'--screenshot={target}', harness.as_uri()]
                    proc = run(cmd, args.timeout)
                    if proc is None or not target.exists():
                        problems.append({'level': 'error', 'where': f'captura {v}@{w}', 'msg': 'o Chrome não gerou a captura'})
                    else:
                        shots.append(str(target))

    counts = lib.summarize(problems)
    ok = counts['error'] == 0
    status = 'PASS' if ok else 'FAIL'
    if not selftests and not args.no_selftest and ok:
        status, ok = 'FAIL', False
    lib.emit(lib.envelope(ok, status, data={'chrome': chrome, 'counts': counts, 'selftests': selftests, 'screenshots': shots, 'console': console}, problems=problems))


if __name__ == '__main__':
    main()
