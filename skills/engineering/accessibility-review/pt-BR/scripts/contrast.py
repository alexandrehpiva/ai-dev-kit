#!/usr/bin/env python3
"""Razão de contraste WCAG entre duas cores (critérios 1.4.3 e 1.4.11).

Uso:
  python3 contrast.py <texto> <fundo>            # ex.: contrast.py '#767676' '#ffffff'
  python3 contrast.py --tokens pares.json        # {"nome": {"fg": "#...", "bg": "#..."}, ...}

Cores: #rgb, #rrggbb, rgb(r, g, b). Sem transparência: componha a cor sobre o fundo antes.
Saída: {"ok","status","data","problems","questions"}; data.results[] com ratio e veredito de
limiar (texto normal 4.5, texto grande 3, componente de interface/gráfico 3). O limiar é cálculo;
o enquadramento do elemento (é texto grande? é componente que comunica?) é decisão do avaliador.
Biblioteca padrão apenas.
"""
from __future__ import annotations

import json
import re
import sys

NORMAL, LARGE, NON_TEXT = 4.5, 3.0, 3.0


def parse_color(text):
    """Devolve (r, g, b) 0-255 ou levanta ValueError."""
    t = str(text).strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", t)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", t)
    if m:
        rgb = tuple(int(x) for x in m.groups())
        if max(rgb) > 255:
            raise ValueError(f"componente fora de 0-255: {text}")
        return rgb
    raise ValueError(f"cor não reconhecida (use #rgb, #rrggbb ou rgb(r,g,b); sem transparência): {text}")


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = luminance(parse_color(fg)), luminance(parse_color(bg))
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def evaluate(fg, bg):
    r = ratio(fg, bg)
    # Trunca (não arredonda) a 2 casas: 4.499 não vira 4.5 e passa por engano.
    shown = int(r * 100) / 100
    return {
        "fg": fg, "bg": bg, "ratio": shown,
        "texto_normal_1_4_3": shown >= NORMAL,
        "texto_grande_1_4_3": shown >= LARGE,
        "componente_1_4_11": shown >= NON_TEXT,
    }


def envelope(ok, status, data=None, problems=None, questions=None):
    return {"ok": ok, "status": status, "data": data or {}, "problems": problems or [], "questions": questions or []}


def main(argv):
    results, problems = [], []
    if len(argv) == 2 and argv[0] == "--tokens":
        try:
            with open(argv[1], encoding="utf-8") as fh:
                tokens = json.load(fh)
        except (OSError, ValueError) as exc:
            print(json.dumps(envelope(False, "invalid-input", problems=[f"arquivo ilegível: {exc}"]), ensure_ascii=False))
            return 2
        for name, pair in tokens.items():
            try:
                results.append({"name": name, **evaluate(pair["fg"], pair["bg"])})
            except (KeyError, TypeError, ValueError) as exc:
                problems.append(f"{name}: {exc}")
    elif len(argv) == 2 and not argv[0].startswith("--"):
        try:
            results.append(evaluate(argv[0], argv[1]))
        except ValueError as exc:
            problems.append(str(exc))
    else:
        print(__doc__)
        return 2
    ok = bool(results) and not problems
    print(json.dumps(envelope(ok, "ok" if ok else "invalid-input", {"results": results}, problems), ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
