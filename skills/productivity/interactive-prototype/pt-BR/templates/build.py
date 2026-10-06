#!/usr/bin/env python3
"""Recompila index.html + styles/ + js/ em dist/index.html (arquivo único, autocontido).

Só stdlib. O index.html é o manifesto da ordem de carga: cada <link rel="stylesheet">,
<script src> e <img src> local é embutido no dist/index.html. dist/ é gerado — nunca editar à mão
(e não é versionado: está no .gitignore).
"""

import base64
import mimetypes
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'index.html')
DIST = os.path.join(ROOT, 'dist', 'index.html')

REMOTE = re.compile(r'^(https?:)?//|^data:')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    with open(path, 'rb') as f:
        return f'data:{mime};base64,' + base64.b64encode(f.read()).decode('ascii')


def inline_css(match):
    return f'<style>\n{read(os.path.join(ROOT, match.group(1)))}</style>'


def inline_js(match):
    return f'<script>\n{read(os.path.join(ROOT, match.group(1)))}</script>'


def inline_img(match):
    pre, src, post = match.groups()
    if REMOTE.match(src):  # imagens remotas ou já embutidas ficam como estão
        return match.group(0)
    return f'<img{pre} src="{data_uri(os.path.join(ROOT, src))}"{post}>'


def inline_icon(match):
    pre, href, post = match.groups()
    if REMOTE.match(href):
        return match.group(0)
    return f'<link{pre} href="{data_uri(os.path.join(ROOT, href))}"{post}>'


def build():
    html = read(SRC)

    # 1) <img src> local → base64. Roda ANTES do inline de JS: depois dele o HTML passa a conter o
    #    texto-fonte dos .js (com `<img ...>` em template strings de runtime) e o regex casaria com eles.
    html = re.sub(r'<img([^>]*?)\ssrc="([^"]+)"([^>]*)>', inline_img, html)
    # 2) favicon/ícones locais → base64 (mesma razão: funcionar em arquivo único isolado)
    html = re.sub(r'<link([^>]*?rel="(?:icon|shortcut icon|apple-touch-icon)"[^>]*?)\shref="([^"]+)"([^>]*)>',
                  inline_icon, html)
    # 3) CSS e JS
    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', lambda m: m.group(0) if REMOTE.match(m.group(1)) else inline_css(m), html)
    html = re.sub(r'<script src="([^"]+)"></script>', lambda m: m.group(0) if REMOTE.match(m.group(1)) else inline_js(m), html)

    os.makedirs(os.path.dirname(DIST), exist_ok=True)
    with open(DIST, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓  dist/index.html  ({os.path.getsize(DIST):,} bytes  |  index.html {os.path.getsize(SRC):,} bytes)')


if __name__ == '__main__':
    try:
        build()
    except FileNotFoundError as e:
        print(f'Erro: {e}', file=sys.stderr)
        sys.exit(1)
