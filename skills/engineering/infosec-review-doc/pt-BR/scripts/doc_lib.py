#!/usr/bin/env python3
"""Biblioteca para gerar o documento de revisão de segurança (HTML -> PDF, stdlib pura).

Uso (veja templates/build_doc.example.py):

    import sys; sys.path.insert(0, "<pasta desta skill>/scripts")
    from doc_lib import *
    cfg = DocConfig(product="...", ...)
    build(cfg, body_fn, SECTIONS, "saida.html", "saida.pdf")

Requer Chrome/Chromium (override: CHROME_PATH). Para o sumário com páginas, `pdftotext` e `pdfinfo`
(poppler); sem eles o PDF sai com o sumário sem números e `build` avisa.
"""
import base64
import html as _html
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

CHROME_TIMEOUT_S = 120
MAC_APPS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
LINUX_BINS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


# ----------------------------------------------------------------------------- configuração
@dataclass
class DocConfig:
    product: str                      # nome completo do produto (cabeçalho e capa)
    doc_type: str                     # ex.: "Documentação para a Segurança da Informação"
    version: str = "1.0"
    date_long: str = ""               # "19 de outubro de 2026"
    date_short: str = ""              # "19/10/2026"
    eyebrow: str = ""                 # ex.: "Cliente × Autor" (capa)
    subtitle: str = ""                # uma frase na capa
    meta_rows: list = field(default_factory=list)   # [(rótulo, valor)] na capa: destinatário, elaborado por...
    accent: str = "#1F4FD1"
    accent_soft: str = "#E8EEFC"
    logo: str = ""                    # caminho de PNG/SVG opcional (capa)
    font: str = ""                    # caminho de TTF/WOFF2 opcional, incorporado em base64
    confidential_label: str = "Confidencial"
    cover_label: str = "Documento confidencial"
    lang: str = "pt-BR"
    page_word: str = "Página"
    of_word: str = "de"
    skip_pages: int = 2               # capa + sumário: a medição de seções começa depois
    diag_size_mm: tuple = (440, 380)  # folha do diagrama


def esc(s):
    return _html.escape(str(s), quote=True)


def _b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


def _cssq(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


# ----------------------------------------------------------------------------- CSS
def css(cfg):
    dw, dh = cfg.diag_size_mm
    font_face = ""
    family = "DocFont,'Helvetica Neue',Helvetica,Arial,sans-serif"
    if cfg.font:
        ext = Path(cfg.font).suffix.lower().lstrip(".")
        mime = {"woff2": "font/woff2", "woff": "font/woff", "ttf": "font/ttf", "otf": "font/otf"}.get(ext, "font/ttf")
        font_face = ("@font-face{font-family:DocFont;font-weight:100 900;src:url(data:%s;base64,%s)}"
                     % (mime, _b64(cfg.font)))
    hdr = "font:500 7.5pt DocFont,Helvetica,Arial,sans-serif;color:#6B7A90"
    ftr = "font:400 7.5pt DocFont,Helvetica,Arial,sans-serif;color:#6B7A90"
    return font_face + """
:root{--ink:#14202E;--slate:#3B4A60;--muted:#6B7A90;--line:#D9E0EA;--soft:#F3F6FB;--accent:%(accent)s;--accent-soft:%(accent_soft)s;--warn:#B45309;--warn-soft:#FFF6E6;--ok:#14764A}
@page{size:A4;margin:24mm 18mm 22mm 18mm;
 @top-left{content:"%(prod)s";%(hdr)s;vertical-align:bottom;padding-bottom:4mm}
 @top-right{content:"%(dtype)s";%(hdr)s;vertical-align:bottom;padding-bottom:4mm}
 @bottom-left{content:"%(conf)s · Versão %(ver)s · %(dshort)s";%(ftr)s;vertical-align:top;padding-top:4mm}
 @bottom-right{content:"%(pw)s " counter(page) " %(ow)s " counter(pages);%(ftr)s;vertical-align:top;padding-top:4mm}}
@page cover{size:A4;margin:0;@top-left{content:none}@top-right{content:none}@bottom-left{content:none}@bottom-right{content:none}}
@page diag{size:%(dw)smm %(dh)smm;margin:20mm 12mm 17mm 12mm}
@page land{size:A4 landscape;margin:20mm 12mm 17mm 12mm}
*{box-sizing:border-box}
html{font-family:%(family)s;color:var(--ink);font-size:9.4pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0}
h1{font-size:19pt;line-height:1.2;margin:0 0 4mm;letter-spacing:-.01em;font-weight:700;break-after:avoid}
h2{font-size:12.5pt;margin:8mm 0 2.5mm;font-weight:700;color:var(--ink);break-after:avoid}
h3{font-size:10pt;margin:5mm 0 1.5mm;font-weight:700;color:var(--slate);break-after:avoid}
p{margin:0 0 2.6mm}
ul,ol{margin:0 0 3mm;padding-left:5mm}li{margin-bottom:1mm}
a{color:inherit;text-decoration:none}
.xr{color:var(--accent);border-bottom:.5pt dotted var(--accent)}
.sec{break-before:page}.sec-first{break-before:auto}
.eyebrow{font:500 7.5pt/1 DocFont,Helvetica,Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:2.5mm}
.lead{font-size:10.4pt;color:var(--slate);line-height:1.55}
table{width:100%%;border-collapse:collapse;margin:2mm 0 4mm;font-size:8.3pt;line-height:1.4}
th{background:var(--soft);text-align:left;font-weight:600;color:var(--slate);border-bottom:1.2pt solid var(--line);padding:1.8mm 2mm;vertical-align:bottom}
td{border-bottom:.6pt solid var(--line);padding:1.8mm 2mm;vertical-align:top}
tr{break-inside:avoid}thead{display:table-header-group}
td.k{font-weight:600;white-space:nowrap}
code,.mono{font-family:Menlo,'SF Mono',Consolas,monospace;font-size:.92em;background:var(--soft);padding:0 1mm;border-radius:1mm}
.chip{display:inline-block;font:600 6.6pt/1 DocFont,Helvetica,Arial,sans-serif;letter-spacing:.02em;border-radius:3mm;padding:1mm 2mm;margin:0 1mm 1mm 0;white-space:nowrap;background:var(--accent-soft);color:var(--accent)}
.chip.si{background:#FDECEF;color:#B3123A}.chip.doc{background:#E3F4EC;color:#14764A}.chip.eng{background:#EEE9FB;color:#5B34C9}
.chip.req{background:#E3F4EC;color:#14764A}.chip.prop{background:#FFF6E6;color:#B45309}.chip.inf{background:#E6F1FA;color:#0B5C99}.chip.prod{background:#FFF1DC;color:#9A5A04}
.callout{border-left:2.2pt solid var(--accent);background:var(--accent-soft);padding:3mm 4mm;margin:3mm 0 4mm;border-radius:0 1.5mm 1.5mm 0;break-inside:avoid}
.callout.warn{border-color:var(--warn);background:var(--warn-soft)}.callout b{color:var(--ink)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:4mm}
.card{border:.8pt solid var(--line);border-radius:2mm;padding:3.5mm 4mm;break-inside:avoid;background:#fff}.card h3{margin-top:0}
.kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:3mm 0 4mm}
.kpi div{border:.8pt solid var(--line);border-radius:2mm;padding:3mm;background:var(--soft)}
.kpi b{display:block;font-size:10pt;color:var(--accent);margin-bottom:1mm}
.small{font-size:7.8pt;color:var(--muted)}
.cover{page:cover;break-after:page;position:relative;height:297mm;width:210mm;background:#fff;overflow:hidden}
.cover .band{position:absolute;left:0;top:0;bottom:0;width:62mm;background:var(--accent-soft)}
.cover .stripe{position:absolute;left:0;width:62mm;height:2.2mm}
.cover .main{position:absolute;left:78mm;right:16mm;top:46mm}
.cover h1{font-size:30pt;line-height:1.12;margin:5mm 0 6mm}
.cover .sub{font-size:12.5pt;color:var(--slate);line-height:1.5}
.cover .meta{position:absolute;left:78mm;right:16mm;bottom:34mm;font-size:8.8pt;color:var(--slate)}
.cover .meta table{font-size:8.8pt;margin:0}.cover .meta td{border-bottom:.6pt solid var(--line);padding:2mm 0}
.cover .meta td:first-child{width:34mm;color:var(--muted);font-weight:500}
.cover .logo{position:absolute;left:78mm;top:22mm;width:34mm}
.cover .conf{position:absolute;left:78mm;bottom:18mm;font:600 7.5pt DocFont,Helvetica,Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.toc{list-style:none;padding:0;margin:3mm 0 6mm}
.toc li{display:flex;align-items:baseline;gap:2mm;margin:0;padding:1.6mm 0;border-bottom:.6pt solid var(--line);font-size:9.6pt}
.toc li a{display:flex;align-items:baseline;gap:2mm;width:100%%;color:inherit}
.toc li .n{width:8mm;color:var(--accent);font-weight:700}.toc li .t{flex:1}.toc li .p{color:var(--muted);font-variant-numeric:tabular-nums}
.diagpage{page:diag;break-before:page;break-after:page}
.diagbox{height:%(dbox)smm;width:100%%}.diagbox svg{width:100%%;height:100%%;display:block}
.land{page:land;break-before:page;break-after:page}.land h2{margin-top:0}
.flow{columns:2;column-gap:8mm;font-size:8.2pt;line-height:1.38;margin:2mm 0 0;padding-left:0;list-style:none}
.flow li{break-inside:avoid;margin-bottom:.8mm}
""" % dict(accent=cfg.accent, accent_soft=cfg.accent_soft, prod=_cssq(cfg.product), dtype=_cssq(cfg.doc_type),
           conf=_cssq(cfg.confidential_label), ver=_cssq(cfg.version), dshort=_cssq(cfg.date_short),
           pw=_cssq(cfg.page_word), ow=_cssq(cfg.of_word), hdr=hdr, ftr=ftr, dw=dw, dh=dh,
           dbox=dh - 58, family=family)


# ----------------------------------------------------------------------------- helpers de HTML
def tr(cells, head=False, k=False):
    tag = "th" if head else "td"
    out = []
    for i, c in enumerate(cells):
        cls = ' class="k"' if (k and i == 0 and not head) else ""
        out.append("<%s%s>%s</%s>" % (tag, cls, c, tag))
    return "<tr>" + "".join(out) + "</tr>"


def table(head, rows, widths=None, k=True):
    cg = ""
    if widths:
        cg = "<colgroup>" + "".join('<col style="width:%s">' % w for w in widths) + "</colgroup>"
    return ("<table>" + cg + "<thead>" + tr(head, True) + "</thead><tbody>"
            + "".join(tr(r, k=k) for r in rows) + "</tbody></table>")


def chip(kind, text):
    """kind: '' (azul, padrão) | si | doc | eng | req | prop | inf | prod (veja provenance-tags.md)."""
    return '<span class="chip%s">%s</span>' % ((" " + kind) if kind else "", text)


def callout(text, warn=False):
    return '<div class="callout%s">%s</div>' % (" warn" if warn else "", text)


def kpi(items):
    return '<div class="kpi">' + "".join("<div><b>%s</b>%s</div>" % (a, b) for a, b in items) + "</div>"


def cards(pairs):
    return '<div class="grid2">' + "".join('<div class="card"><h3>%s</h3>%s</div>' % (t, b) for t, b in pairs) + "</div>"


def xref(target, text):
    return "<a class='xr' href='#%s'>%s</a>" % (target, text)


def section(sid, kind_label, title, body, first=False, style=""):
    """Seção com eyebrow ('Seção 3' / 'Anexo A') e H1. `first` = sem quebra de página (seções curtas)."""
    cls = "sec-first" if first else "sec"
    st = ' style="%s"' % style if style else ""
    return ('<section class="%s" id="%s"%s><div class="eyebrow">%s</div><h1>%s</h1>%s</section>'
            % (cls, sid, st, kind_label, title, body))


def toc_html(sections, pages):
    """sections: [(id, label, title, kind)]; pages: {id: página}."""
    items = []
    for sid, label, title, _kind in sections:
        items.append('<li><a href="#%s"><span class="n">%s</span><span class="t">%s</span><span class="p">%s</span></a></li>'
                     % (sid, label, title, pages.get(sid, "")))
    return '<ul class="toc">' + "".join(items) + "</ul>"


def cover(cfg):
    logo = ""
    if cfg.logo:
        mime = "image/svg+xml" if cfg.logo.lower().endswith(".svg") else "image/png"
        logo = '<img class="logo" src="data:%s;base64,%s" alt="">' % (mime, _b64(cfg.logo))
    meta = "".join("<tr><td>%s</td><td>%s</td></tr>" % (a, b) for a, b in cfg.meta_rows)
    return """<section class="cover">
 <div class="band"></div>
 <div class="stripe" style="top:96mm;background:var(--accent)"></div>
 <div class="stripe" style="top:101mm;background:var(--ink)"></div>
 <div class="stripe" style="top:106mm;background:var(--accent)"></div>
 %s
 <div class="main"><div class="eyebrow">%s</div><h1>%s</h1><p class="sub">%s</p></div>
 <div class="meta"><table>%s<tr><td>Versão</td><td>%s · %s</td></tr></table></div>
 <div class="conf">%s</div>
</section>""" % (logo, cfg.eyebrow, cfg.product, cfg.subtitle, meta, cfg.version, cfg.date_long, cfg.cover_label)


def svg_inline(path):
    """Lê um SVG e o prepara para ocupar 100%% da caixa do diagrama (vetor no PDF)."""
    s = Path(path).read_text(encoding="utf-8")
    s = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", s).strip()
    s = re.sub(r'(<svg[^>]*?) style="[^"]*"', r"\1", s, count=1)
    s = re.sub(r'(<svg[^>]*?) width="[^"]*" height="[^"]*"',
               r'\1 width="100%" height="100%" preserveAspectRatio="xMidYMid meet"', s, count=1)
    return s


def diagram_pages(eyebrow, heading, svg_markup, flows, note="", flows_title="Ordem dos números do desenho", sid="s-arch"):
    """Página grande com o diagrama + página horizontal com a lista numerada [(n, texto)]."""
    flow_html = "".join("<li><b>%s</b> &nbsp;%s</li>" % (n, t) for n, t in flows)
    return ('<section class="diagpage" id="%s"><div class="eyebrow">%s</div><h2>%s</h2><div class="diagbox">%s</div></section>'
            '<section class="land"><div class="eyebrow">%s</div><h2>%s</h2><p class="small">%s</p><ul class="flow">%s</ul></section>'
            % (sid, eyebrow, heading, svg_markup, eyebrow, flows_title, note, flow_html))


def html_document(cfg, body):
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><title>%s — %s</title><style>%s</style></head><body>%s</body></html>'
            % (cfg.lang, esc(cfg.product), esc(cfg.doc_type), css(cfg), body))


# ----------------------------------------------------------------------------- render e medição
def find_chrome():
    override = os.environ.get("CHROME_PATH")
    if override:
        if not Path(override).is_file():
            sys.exit("ERRO: CHROME_PATH aponta para algo inexistente: %s" % override)
        return override
    cands = MAC_APPS if sys.platform == "darwin" else []
    if sys.platform.startswith("win"):
        for var in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData"):
            base = os.environ.get(var)
            if base:
                cands.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
    for p in cands:
        if Path(p).is_file():
            return p
    for n in LINUX_BINS:
        f = shutil.which(n)
        if f:
            return f
    sys.exit("ERRO: Chrome/Chromium não encontrado. Defina CHROME_PATH.")


def html_to_pdf(html_path, pdf_path):
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    if pdf_path.exists():
        pdf_path.unlink()  # não confundir PDF antigo com sucesso desta execução
    cmd = [find_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=%s" % pdf_path]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--no-sandbox")
    cmd.append(html_path.as_uri())
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CHROME_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        sys.exit("ERRO: Chrome não terminou em %ss." % CHROME_TIMEOUT_S)
    if not pdf_path.exists() or not pdf_path.read_bytes().startswith(b"%PDF"):
        sys.exit("ERRO: PDF não foi gerado (exit=%s).\n%s" % (proc.returncode, proc.stderr[-600:]))
    return pdf_path


def page_count(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else 0


def _compact(s):
    return re.sub(r"\s+", "", s).upper()


def measure(cfg, pdf, sections):
    """Página em que começa cada seção. Procura 'EYEBROW+número' no início da página (sem o cabeçalho
    corrente); para seções sem eyebrow no início, cai para o título. Retorna {} se faltar poppler."""
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        return {}
    n = page_count(pdf)
    texts = []
    for p in range(1, n + 1):
        texts.append(subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", str(pdf), "-"],
                                    capture_output=True, text=True).stdout)
    header = _compact(cfg.product + cfg.doc_type)
    comp = [_compact(t).replace(header, "", 1) for t in texts]
    pages = {}
    for sid, label, title, kind in sections:
        key = _compact("%s %s" % (kind, label))
        pat = re.compile(r"^%s(?!\d)" % re.escape(key))
        for i, t in enumerate(comp):
            if i >= cfg.skip_pages and pat.search(t):
                pages[sid] = i + 1
                break
        if sid not in pages:
            tk = _compact(title)
            for i, t in enumerate(comp):
                if i >= cfg.skip_pages and tk in t:
                    pages[sid] = i + 1
                    break
    return pages


def build(cfg, body_fn, sections, out_html, out_pdf):
    """Duas (ou três) passagens: renderiza, mede onde cada seção caiu e renderiza de novo com o sumário.
    body_fn(pages) -> HTML do <body> (capa, sumário via toc_html(sections, pages), seções)."""
    def render(pages):
        Path(out_html).write_text(html_document(cfg, body_fn(pages)), encoding="utf-8")
        html_to_pdf(out_html, out_pdf)

    render({})
    pages = measure(cfg, out_pdf, sections)
    if not pages:
        print("AVISO: pdftotext/pdfinfo ausentes — sumário sem números de página.")
        return {}
    render(pages)
    pages2 = measure(cfg, out_pdf, sections)
    if pages2 != pages:
        render(pages2)
        pages = pages2
    missing = [s[0] for s in sections if s[0] not in pages]
    if missing:
        print("AVISO: seções não localizadas no PDF:", ", ".join(missing))
    print("OK: %s — %d páginas; seções: %s" % (out_pdf, page_count(out_pdf), pages))
    return pages
