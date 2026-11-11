#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o JS de `--init-script` que reidrata o sessionStorage por origem.

Por que existe: o `storageState` do Playwright leva cookies, localStorage e IndexedDB, mas NÃO o
sessionStorage. A saída deste script é um init-script que, a cada página, grava no sessionStorage as
chaves da origem corrente (só se ainda não existirem, a menos que --overwrite).

Uso:
    python3 scripts/make_init_script.py --input session-storage.json            (plano: só resumo)
    python3 scripts/make_init_script.py --input session-storage.json --output init-session.js [--overwrite] [--force]
    (Windows: py -3 scripts\\make_init_script.py ...)

Entrada: JSON `{"https://exemplo.com": {"chave": "valor", ...}, ...}` (origem -> chaves), exportado
com `browser_evaluate` (ver templates/export-storage-state.md). O sessionStorage pode conter tokens:
a saída NUNCA imprime valores; o arquivo gerado recebe chmod 600 e deve ser apagado depois do uso.

Sem --output nada é gravado: o JSON de saída traz só o resumo (origens, quantidade de chaves, tamanho).
Com --output grava o arquivo; recusa sobrescrever um arquivo existente sem --force.
Use no MCP: `--init-script <arquivo>` (junto de `--isolated --storage-state <state.json>`).

Saída: JSON {"ok","status","data","problems","next_steps"}. Status: planned | written | usage_error.
Códigos de saída: 0 ok; 1 problema acionável; 2 erro de uso. Python 3.8+, só biblioteca padrão.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detect_browser as db  # noqa: E402

ORIGIN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://[^/\s?#]+$")

# O mesmo código está em templates/init-script-session-storage.js (com um exemplo no lugar de __DATA__).
TEMPLATE = """(() => {
  const DATA = __DATA__;
  const OVERWRITE = __OVERWRITE__;
  const items = DATA[location.origin];
  if (!items) return;
  try {
    for (const [k, v] of Object.entries(items)) {
      if (OVERWRITE || sessionStorage.getItem(k) === null) sessionStorage.setItem(k, v);
    }
  } catch (e) { /* sessionStorage indisponível nesta origem (about:blank, iframe sandbox) */ }
})();
"""


def validate(doc):
    """Devolve (erro|None, resumo). O resumo não contém valores."""
    if not isinstance(doc, dict) or not doc:
        return "O JSON precisa ser um objeto {origem: {chave: valor}} não vazio.", None
    summary = []
    for origin, items in doc.items():
        if not ORIGIN_RE.match(origin):
            return "Origem inválida: %r (esperado esquema://host[:porta], sem barra final)." % origin, None
        if not isinstance(items, dict):
            return "Origem %s: o valor precisa ser um objeto {chave: valor}." % origin, None
        for k, v in items.items():
            if not isinstance(v, str):
                return "Origem %s, chave %r: valores do sessionStorage são strings." % (origin, k), None
        summary.append({"origin": origin, "keys": len(items), "chars": sum(len(k) + len(v) for k, v in items.items())})
    return None, summary


def js_literal(obj):
    """JSON seguro para embutir em JS (U+2028/2029 e '<' escapados)."""
    out = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return out.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029").replace("<", "\\u003c")


def render(doc, overwrite=False):
    return TEMPLATE.replace("__DATA__", js_literal(doc)).replace("__OVERWRITE__", "true" if overwrite else "false")


def run(args):
    problems, next_steps = [], []
    try:
        with open(args.input, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return 2, db.result(False, "usage_error", {}, ["Não consegui ler --input (%s): %s" % (exc.__class__.__name__, exc)], [])
    err, summary = validate(doc)
    if err:
        return 2, db.result(False, "usage_error", {}, [err], [])
    data = {"input": os.path.abspath(args.input), "output": None, "origins": summary,
            "total_keys": sum(s["keys"] for s in summary), "overwrite": bool(args.overwrite)}
    script = render(doc, args.overwrite)
    data["script_chars"] = len(script)
    if not args.output:
        next_steps.append("Plano apenas (valores não são impressos). Rode com --output <arquivo.js> para gravar.")
        return 0, db.result(True, "planned", data, problems, next_steps)
    out = os.path.abspath(os.path.expanduser(args.output))
    data["output"] = out
    if os.path.exists(out) and not args.force:
        return 1, db.result(False, "usage_error", data,
                            ["O arquivo %s já existe; use --force para sobrescrever." % out], [])
    d = os.path.dirname(out)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(script)
    if os.name == "posix":
        os.chmod(out, 0o600)
    problems.append("O arquivo contém dados de sessão: não versione e apague ao terminar.")
    next_steps.append("Use no MCP: --isolated --storage-state <state.json> --init-script %s" % out)
    return 0, db.result(True, "written", data, problems, next_steps)


def build_parser():
    ap = db._Parser(description="Gera o init-script que reidrata o sessionStorage (plano por padrão).")
    ap.add_argument("--input", required=True, help="JSON {origem: {chave: valor}}")
    ap.add_argument("--output", default=None, help="arquivo .js a gravar (sem isto: só resumo)")
    ap.add_argument("--overwrite", action="store_true", help="regrava chaves que o site já criou (padrão: só as ausentes)")
    ap.add_argument("--force", action="store_true", help="sobrescreve o --output existente")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    code, payload = run(args)
    db.emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
