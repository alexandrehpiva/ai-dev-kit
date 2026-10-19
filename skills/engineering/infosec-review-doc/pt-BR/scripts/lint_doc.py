#!/usr/bin/env python3
"""Checagens mecânicas do documento de revisão de segurança (HTML e, opcionalmente, PDF). Stdlib pura.

Uso:
  python3 lint_doc.py documento.html [--pdf documento.pdf] [--forbid termos.txt]
                      [--max-pages 26] [--origin-col Origem] [--min-words 40]
                      [--ambiguous "Plataforma X=Produto Y"] ... [--json]

Falhas (exit 1): marcadores esquecidos (TODO/TBD/XXX/{{/lorem), link interno sem destino, id repetido,
célula da coluna de origem vazia ou sem chip, linha do sumário sem página, termo proibido,
HTML vazio. Avisos (exit 0): página quase vazia, excesso de páginas, nome ambíguo sem qualificador.
Informação: lista todas as ocorrências de "proposta".
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

PLACEHOLDER = re.compile(r"\bTODO\b|\bTBD\b|\bXXX\b|\{\{|\}\}|\{\w+\(|lorem ipsum", re.I)


class Doc(HTMLParser):
    def __init__(self, origin_col):
        super().__init__(convert_charrefs=True)
        self.origin_col = origin_col.lower()
        self.ids, self.ids_dup, self.hrefs = set(), set(), []
        self.text = []
        self.skip = 0
        self.in_cell = None          # (tag, índice)
        self.cell_text, self.cell_chip = "", False
        self.row = []
        self.table_head = None
        self.table_stack = []
        self.origin_issues = []
        self.toc_empty = []
        self.in_toc_li = False
        self.toc_p = None
        self.span_stack = []

    # -- estrutura
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("style", "script"):
            self.skip += 1
        if "id" in a:
            if a["id"] in self.ids:
                self.ids_dup.add(a["id"])
            self.ids.add(a["id"])
        if tag == "a" and a.get("href", "").startswith("#") and len(a["href"]) > 1:
            self.hrefs.append(a["href"][1:])
        cls = a.get("class", "") or ""
        if tag == "table":
            self.table_stack.append({"head": None, "rows": []})
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.in_cell = tag
            self.cell_text, self.cell_chip = "", False
        if tag == "span":
            self.span_stack.append(cls)
            if "chip" in cls.split():
                self.cell_chip = True
            if "p" in cls.split() and self.in_toc_li:
                self.toc_p = ""
        if tag == "li" and self._in_toc():
            self.in_toc_li = True
            self.toc_p = None
        if tag == "ul" and "toc" in cls.split():
            self.toc_depth = True

    def _in_toc(self):
        return getattr(self, "toc_depth", False)

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self.skip -= 1
        if tag == "span" and self.span_stack:
            cls = self.span_stack.pop()
            if "p" in cls.split() and self.in_toc_li and (self.toc_p is None or not self.toc_p.strip()):
                self.toc_empty.append(True)
        if tag in ("td", "th") and self.in_cell:
            self.row.append((self.in_cell, self.cell_text.strip(), self.cell_chip))
            self.in_cell = None
        if tag == "tr" and self.table_stack:
            t = self.table_stack[-1]
            if self.row and all(c[0] == "th" for c in self.row):
                t["head"] = [c[1].lower() for c in self.row]
            elif self.row:
                t["rows"].append(self.row)
            self.row = []
        if tag == "table" and self.table_stack:
            t = self.table_stack.pop()
            if t["head"] and self.origin_col in t["head"]:
                idx = t["head"].index(self.origin_col)
                for r in t["rows"]:
                    if idx >= len(r) or not r[idx][1] or not r[idx][2]:
                        first = r[0][1][:50] if r else "?"
                        self.origin_issues.append(first)
        if tag == "li":
            self.in_toc_li = False
        if tag == "ul":
            self.toc_depth = False

    def handle_data(self, data):
        if self.skip:
            return
        self.text.append(data)
        if self.in_cell:
            self.cell_text += data
        if self.in_toc_li and self.span_stack and "p" in self.span_stack[-1].split():
            self.toc_p = (self.toc_p or "") + data


def pdf_pages(pdf):
    if not shutil.which("pdfinfo"):
        return None, []
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    words = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"], capture_output=True, text=True).stdout
        words.append(len(t.split()))
    return n, words


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--pdf")
    ap.add_argument("--forbid", help="arquivo com um termo proibido por linha (sem diferenciar maiúsculas)")
    ap.add_argument("--max-pages", type=int)
    ap.add_argument("--min-words", type=int, default=40, help="página com menos palavras é avisada (padrão 40)")
    ap.add_argument("--origin-col", default="Origem")
    ap.add_argument("--ambiguous", action="append", default=[], help='"nome ambíguo=qualificador" (repetível)')
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = Path(args.html).read_text(encoding="utf-8")
    d = Doc(args.origin_col)
    d.feed(raw)
    text = re.sub(r"\s+", " ", " ".join(d.text))
    errors, warnings, info = [], [], []

    if len(text) < 200:
        errors.append("HTML praticamente vazio (%d caracteres de texto)" % len(text))
    for m in sorted(set(x.group(0).lower() for x in PLACEHOLDER.finditer(text))):
        errors.append("marcador esquecido no texto: %r" % m)
    for h in sorted(set(d.hrefs)):
        if h not in d.ids:
            errors.append("link interno sem destino: #%s" % h)
    for i in sorted(d.ids_dup):
        errors.append("id repetido: %s" % i)
    for first in d.origin_issues:
        errors.append("coluna %s vazia ou sem chip na linha que começa com %r" % (args.origin_col, first))
    if d.toc_empty:
        if args.pdf:
            errors.append("%d linha(s) do sumário sem número de página" % len(d.toc_empty))
        else:
            warnings.append("%d linha(s) do sumário sem número de página (sem --pdf)" % len(d.toc_empty))
    if args.forbid:
        for term in Path(args.forbid).read_text(encoding="utf-8").splitlines():
            term = term.strip()
            if term and not term.startswith("#") and term.lower() in text.lower():
                errors.append("termo proibido presente: %r" % term)
    for spec in args.ambiguous:
        name, _, qual = spec.partition("=")
        for m in re.finditer(re.escape(name), text):
            after = text[m.end():m.end() + 60]
            before = text[max(0, m.start() - 20):m.start()]
            if qual and qual.lower() not in (after + before).lower():
                warnings.append("nome ambíguo %r sem %r por perto: …%s…" % (name, qual, text[max(0, m.start() - 30):m.end() + 40]))

    props = [m.start() for m in re.finditer(r"proposta", text, re.I)]
    for pos in props:
        info.append("proposta: …%s…" % text[max(0, pos - 40):pos + 60])

    if args.pdf:
        n, words = pdf_pages(args.pdf)
        if n is None:
            warnings.append("pdfinfo/pdftotext ausentes: checagens de página não feitas")
        else:
            if args.max_pages and n > args.max_pages:
                warnings.append("PDF com %d páginas (limite %d)" % (n, args.max_pages))
            for i, w in enumerate(words, 1):
                if i > 1 and w < args.min_words:   # capa (1) tem pouco texto por desenho
                    warnings.append("página %d com só %d palavras (órfã ou quase vazia?)" % (i, w))
            info.append("PDF: %d páginas" % n)

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings, "info": info}, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print("FALHA:", e)
        for w in warnings:
            print("AVISO:", w)
        for i in info:
            print("INFO:", i)
        print("%s — %d falha(s), %d aviso(s)" % ("REPROVADO" if errors else "OK", len(errors), len(warnings)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
