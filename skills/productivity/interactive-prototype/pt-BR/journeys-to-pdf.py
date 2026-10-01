#!/usr/bin/env python3
"""Compila docs/user-journeys/**/*.md em um PDF navegável (Markdown -> HTML -> Chrome headless).

Contrato visual completo: JOURNEY-PDF-STYLE.md (mesma pasta). Só stdlib; requer Google Chrome/Chromium
(detectado em macOS/Linux/Windows; override por CHROME_PATH) e `pdftotext`/`pdfinfo` (poppler) para o mapa
de páginas do sumário.

Uso:
  python3 journeys-to-pdf.py --root docs/user-journeys --out docs/jornadas-usuario-<produto>.pdf \
      --title "Jornadas de Usuário — <Produto> Onboarding" \
      --subtitle "Protótipo navegável · v1.2.0 · 1 out 2026" \
      --footer "Fonte: docs/user-journeys · <Produto> · 1 out 2026" [--groups <personas.json>] \
      [--note "<aviso na capa>" [--note-title "Atenção!"]] [--work <scratch>]

Descoberta: cada .md com H1 `# [<PROD>-<ÁREA>-<PERSONA>-Jnn-FP|FAnn|FEnn] Título` e `status: active`.
Persona pelo prefixo do código no H1 (`ACME-ONB-PJ-J00-FP`); sem prefixo, pela pasta da jornada.
--groups (JSON, lista ordenada) define as personas: código, rótulo do grupo no sumário, tag de categoria,
subpasta ("" = raiz) e texto da legenda. Sem --groups, cada subpasta vira um grupo (código = nome da
pasta em maiúsculas; raiz = GERAL), em ordem alfabética com a raiz por último.
README.md, _archived/ e `status` != active são ignorados.
Seções "Histórico de mudanças" e "Cobertura de testes" não entram no PDF.
"""
import argparse, html, json, os, re, shutil, subprocess, sys, tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
]
KIND_RANK = {"FP": 0, "FA": 1, "FE": 2}
SKIP = {"Histórico de mudanças", "Cobertura de testes"}
INLINE = {"Objetivo": "Objetivo", "Ator(es)": "Ator", "Pré-condições": "Pré-condições", "Pré-condição": "Pré-condição"}

CSS = """
@page { size: A4 portrait; margin: 20mm 18mm; @bottom-center { content: counter(page); font-family: -apple-system,"Helvetica Neue",Arial,sans-serif; font-size: 8pt; color: #888; } }
@page :first { @bottom-center { content: ""; } }
* { box-sizing: border-box; }
body { font-family: -apple-system,"Helvetica Neue",Arial,sans-serif; font-size: 10.5pt; color: #1a1a1a; line-height: 1.5; margin: 0; }
.cover { page-break-after: always; }
h1 { font-size: 22pt; margin: 0 0 6px; }
.sub { color: #888; font-size: 9.5pt; padding-bottom: 14px; border-bottom: 1px solid #ddd; }
.note { margin: 14px 0 0; padding: 8px 12px; background: #fff8e1; border-left: 3px solid #e65100; font-size: 9pt; color: #5d4037; line-height: 1.45; page-break-inside: avoid; }
.note b { color: #e65100; }
.legend { margin: 14px 0 22px; font-size: 8.6pt; color: #555; padding-bottom: 12px; border-bottom: 1px solid #ddd; line-height: 2; }
.badge { display: inline-block; font-size: 7.5pt; font-weight: 700; padding: 1px 6px; border-radius: 3px; text-align: center; min-width: 26px; }
.badge-fp { background: #e8f5e9; color: #1b5e20; } .badge-fa { background: #fff8e1; color: #e65100; } .badge-fe { background: #fdecea; color: #b71c1c; }
.cover h2 { font-size: 14pt; margin: 0 0 8px; padding-bottom: 6px; border-bottom: 1px solid #ddd; }
.toc-group-header { font-size: 7.5pt; font-weight: 700; color: #555; text-transform: uppercase; letter-spacing: 0.07em; padding: 9px 0 3px; border-bottom: 1.5px solid #bbb; margin-top: 5px; }
.toc-entry { display: flex; align-items: baseline; gap: 5px; padding: 4px 0; border-bottom: 1px solid #eee; font-size: 9.5pt; }
.toc-badge-cell { flex-shrink: 0; }
.toc-title-cell { flex-shrink: 0; white-space: nowrap; padding-left: 2px; }
.toc-title-cell a { color: #1a1a1a; text-decoration: none; }
.toc-leader { flex: 1; border-bottom: 1px dotted #aaa; margin: 0 4px 3px; min-width: 16px; }
.toc-cat-cell { flex-shrink: 0; white-space: nowrap; color: #555; font-size: 8.5pt; }
.toc-page-cell { flex-shrink: 0; min-width: 20px; text-align: right; font-size: 8.5pt; color: #888; padding-left: 4px; }
.toc-page-ref { color: #888; text-decoration: none; }
.journey { page-break-before: always; }
.journey-header { background: #2c3e50; color: #fff; padding: 9px 14px 8px; border-radius: 5px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 11pt; }
.journey-cat { font-size: 8pt; font-weight: 400; opacity: .75; }
.jmeta { margin: 4px 0; }
.sh { font-size: 10.5pt; font-weight: 700; margin: 12px 0 4px; border-bottom: 1px solid #ccc; padding-bottom: 3px; page-break-after: avoid; }
h4 { font-size: 10pt; margin: 10px 0 3px; page-break-after: avoid; }
table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 4px 0 8px; }
thead { display: table-header-group; }
th { background: #2c3e50; color: #fff; padding: 5px 8px; text-align: left; }
td { padding: 5px 8px; border: 1px solid #d0d0d0; vertical-align: top; }
tr { page-break-inside: avoid; } tr:nth-child(even) td { background: #f6f8fa; }
ul, ol { margin: 4px 0 6px; padding-left: 20px; } li { margin: 2px 0; }
p { margin: 5px 0; } p.bdd { background: #f6f8fa; border-left: 3px solid #b0bec5; padding: 5px 10px; page-break-inside: avoid; }
code { font-family: Menlo,monospace; font-size: 8.5pt; background: #f0f0f0; padding: 0 3px; border-radius: 2px; }
a { color: #2c3e50; } .footer { margin-top: 18px; padding-top: 6px; border-top: 1px solid #ddd; font-size: 8pt; color: #888; }
"""


def inline(t, name2anchor):
    t = html.escape(t, quote=False)

    def link(m):
        base = os.path.basename(m.group(2).split("#")[0])
        return '<a href="#%s">%s</a>' % (name2anchor[base], m.group(1)) if base in name2anchor else m.group(1)

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"(?<![\w*])\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", t)


def render(body, n2a):
    lines, out, i = body.split("\n"), [], 0
    bullet = lambda s: re.match(r"^\s*[-*] ", s)
    number = lambda s: re.match(r"^\d+\. ", s)
    while i < len(lines):
        l = lines[i]
        if not l.strip():
            i += 1
        elif l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            t = "<table><thead><tr>%s</tr></thead><tbody>" % "".join("<th>%s</th>" % inline(c, n2a) for c in cells(rows[0]))
            for r in rows[2:]:
                t += "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, n2a) for c in cells(r))
            out.append(t + "</tbody></table>")
        elif l.startswith("### "):
            out.append("<h4>%s</h4>" % inline(l[4:], n2a)); i += 1
        elif bullet(l) or number(l):
            tag, test, items = ("ul", bullet, []) if bullet(l) else ("ol", number, [])
            while i < len(lines) and test(lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i])); i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x, n2a) for x in items), tag))
        else:
            p = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("|", "### ")) and not bullet(lines[i]) and not number(lines[i]):
                p.append(lines[i]); i += 1
            cls = ' class="bdd"' if p[0].startswith("**Cenário") else ""
            out.append("<p%s>%s</p>" % (cls, "<br>".join(inline(x, n2a) for x in p)))
    return "\n".join(out)


def find_chrome():
    env = os.environ.get("CHROME_PATH", "")
    if env and not (os.path.isfile(env) or shutil.which(env)):
        sys.exit("CHROME_PATH aponta para um executável inexistente: " + env)
    for c in [env] + CHROME_CANDIDATES:
        if c and (os.path.isfile(c) or shutil.which(c)):
            return c if os.path.isfile(c) else shutil.which(c)
    sys.exit("Chrome/Chromium não encontrado. Defina CHROME_PATH com o caminho do executável.")


def load_groups(path, root):
    """Lista ordenada de personas: dict(code, label, tag, folder, legend)."""
    if path:
        gs = json.load(open(path, encoding="utf-8"))
    else:
        subs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith((".", "_")))
        gs = [dict(code=d.upper(), folder=d) for d in subs]
        seen = {g["code"] for g in gs}
        for dp, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if not d.startswith("_")]
            for f in fs:
                if f.endswith(".md") and f.lower() != "readme.md":
                    m = re.match(r"# \[[A-Z0-9]+-[A-Z0-9]+-([A-Z0-9]+)-J\d+-", open(os.path.join(dp, f), encoding="utf-8").readline())
                    if m and m.group(1) not in seen:
                        seen.add(m.group(1)); gs.append(dict(code=m.group(1), folder="\0"))
        gs = sorted(gs, key=lambda g: g["code"]) + [dict(code="GERAL", label="Geral", folder="")]
    for g in gs:
        g.setdefault("label", g["code"]); g.setdefault("tag", g["code"])
        g.setdefault("folder", g["code"].lower()); g.setdefault("legend", g["label"])
    return gs


def discover(root, groups):
    found, codes = [], [g["code"] for g in groups]
    by_folder = {g["folder"].lower(): g["code"] for g in groups}
    for dp, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if not d.startswith("_")]
        for f in fs:
            if not f.endswith(".md") or f.lower() == "readme.md":
                continue
            s = open(os.path.join(dp, f), encoding="utf-8").read()
            m = re.match(r"# \[([A-Z0-9]+)-([A-Z0-9]+)-(?:([A-Z0-9]+)-)?J(\d+)-(FP|FA\d*|FE\d*)\] (.+)", s.split("\n")[0])
            if not m or not re.search(r"^status:\s*active", s, re.M):
                continue
            rel = os.path.relpath(dp, root).lower()
            rel = "" if rel == "." else rel
            grp = m.group(3) if m.group(3) in codes else by_folder.get(rel)
            if grp is None:
                sys.exit("Persona de %s não está em --groups (prefixo %r, pasta %r)" % (f, m.group(3), rel or "raiz"))
            prod, area, jn, kind, title = m.group(1), m.group(2), int(m.group(4)), m.group(5), m.group(6).strip()
            secs = [(x.split("\n")[0].strip(), "\n".join(x.split("\n")[1:]).strip()) for x in re.split(r"^## ", s, flags=re.M)[1:]]
            n = int(re.sub(r"\D", "", kind) or 0)
            found.append(dict(file=f, grp=grp, prod=prod, area=area, jn=jn, kind=kind, k=kind[:2], n=n, title=title, secs=secs,
                              code="J%02d-%s" % (jn, kind), key=(codes.index(grp), jn, KIND_RANK[kind[:2]], n)))
    return sorted(found, key=lambda j: j["key"])


def build_html(js, a, pages, groups):
    anchor = lambda j: ("%s-%s" % (j["grp"], j["code"])).lower()
    n2a = {j["file"]: anchor(j) for j in js}
    toc = ""
    for G in groups:
        g, gname, gtag = G["code"], G["label"], G["tag"]
        items = [j for j in js if j["grp"] == g]
        if not items:
            continue
        toc += '<div class="toc-group-header">%s</div>' % html.escape(gname)
        for j in items:
            steps = 0
            for n, b in j["secs"]:
                if n == "Etapas":
                    steps = len([r for r in b.split("\n") if r.startswith("|")]) - 2
            cat = gtag + (" · %d etapas" % steps if j["k"] == "FP" and steps else "" if j["k"] == "FP" else " · " + j["kind"])
            an = anchor(j)
            toc += ('<div class="toc-entry"><span class="toc-badge-cell"><span class="badge badge-%s">%s</span></span>'
                    '<span class="toc-title-cell"><a href="#%s">%s-%s — %s</a></span><span class="toc-leader"></span>'
                    '<span class="toc-cat-cell">%s</span><span class="toc-page-cell"><a class="toc-page-ref" href="#%s">%s</a></span></div>'
                    % (j["k"].lower(), j["k"], an, g, j["code"], html.escape(j["title"]), cat, an, pages.get(an, "")))
    body = ""
    for idx, j in enumerate(js):
        gtag = {G["code"]: G["tag"] for G in groups}[j["grp"]]
        cat = gtag + ("" if j["k"] == "FP" else " · " + j["kind"])
        body += ('<div class="journey" id="%s"><div class="journey-header"><span>[%s-%s-%s-%s] %s</span><span class="journey-cat">%s</span></div>'
                 % (anchor(j), j["prod"], j["area"], j["grp"], j["code"], html.escape(j["title"]), cat))
        for n, b in j["secs"]:
            if n in SKIP:
                continue
            if n in INLINE:
                if re.search(r"^\s*[-*] ", b, re.M):
                    body += '<p class="jmeta"><b>%s:</b></p>%s' % (INLINE[n], render(b, n2a))
                else:
                    body += '<p class="jmeta"><b>%s:</b> %s</p>' % (INLINE[n], inline(b.replace("\n", " "), n2a))
            else:
                body += '<p class="sh">%s</p>%s' % (html.escape(n), render(b, n2a))
        if idx == len(js) - 1 and a.footer:
            body += '<div class="footer">%s</div>' % html.escape(a.footer)
        body += "</div>"
    used = {j["grp"] for j in js}
    personas = " &nbsp; ".join("<b>%s</b> = %s" % (html.escape(G["code"]), html.escape(G["legend"]))
                               for G in groups if G["code"] in used and G["legend"] != G["code"])
    legend = ('<span class="badge badge-fp">FP</span> = Fluxo Principal &nbsp; <span class="badge badge-fa">FA</span> = Fluxo Alternativo &nbsp; '
              '<span class="badge badge-fe">FE</span> = Fluxo de Exceção' + (" &nbsp;·&nbsp; " + personas if personas else ""))
    note = ('<div class="note"><b>%s</b><br>%s</div>' % (html.escape(a.note_title), html.escape(a.note))) if a.note else ""
    cover = '<div class="cover"><h1>%s</h1><div class="sub">%s</div>%s<div class="legend">%s</div><h2>Sumário</h2>%s</div>' % (
        html.escape(a.title), html.escape(a.subtitle), note, legend, toc)
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>%s</title><style>%s</style></head><body>%s%s</body></html>' % (
        html.escape(a.title), CSS, cover, body), anchor


def render_pdf(html_path, pdf_path):
    r = subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer", "--no-sandbox",
                        "--print-to-pdf=" + pdf_path, "file://" + html_path], capture_output=True, text=True)
    if "bytes written" not in r.stderr:
        sys.exit("Chrome não gerou o PDF:\n" + r.stderr[-800:])


def page_map(pdf, js, anchor):
    total = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    res = {}
    for p in range(2, total + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
        for j in js:
            if "[%s-%s-%s-%s]" % (j["prod"], j["area"], j["grp"], j["code"]) in t and anchor(j) not in res:
                res[anchor(j)] = p
    return res, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--title", required=True); ap.add_argument("--subtitle", required=True)
    ap.add_argument("--footer", default=""); ap.add_argument("--note", default=""); ap.add_argument("--note-title", default="Atenção!"); ap.add_argument("--work", default=tempfile.mkdtemp())
    ap.add_argument("--groups", default="", help="JSON com a lista ordenada de personas (ver JOURNEY-PDF-STYLE.md)")
    a = ap.parse_args()
    groups = load_groups(a.groups, a.root)
    js = discover(a.root, groups)
    if not js:
        sys.exit("Nenhuma jornada ativa encontrada em " + a.root)
    os.makedirs(a.work, exist_ok=True)
    hp, tmp = os.path.join(a.work, "journeys.html"), os.path.join(a.work, "pass1.pdf")
    doc, anchor = build_html(js, a, {}, groups)          # passo 1: sumário sem números
    open(hp, "w", encoding="utf-8").write(doc); render_pdf(hp, tmp)
    pages, total = page_map(tmp, js, anchor)     # passo 2: mapa de páginas reais
    doc, _ = build_html(js, a, pages, groups)            # passo 3: números hardcoded
    open(hp, "w", encoding="utf-8").write(doc); render_pdf(hp, a.out)
    pages2, total2 = page_map(a.out, js, anchor)  # passo 4: conferir que o mapa não mudou
    if pages2 != pages:
        doc, _ = build_html(js, a, pages2, groups); open(hp, "w", encoding="utf-8").write(doc); render_pdf(hp, a.out)
    print("PDF: %s (%d páginas, %d jornadas)\nHTML intermediário: %s" % (a.out, total2, len(js), hp))
    for j in js:
        print("  pág %-3s %s-%s" % (pages2.get(anchor(j), "?"), j["grp"], j["code"]))


if __name__ == "__main__":
    main()
