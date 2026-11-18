#!/usr/bin/env python3
"""Gera o HTML do lote de chamados a partir da especificação JSON (stdlib pura).

Uso:  python3 build_tickets_html.py <spec.json> <saida.html> [--template caminho.html]

O PDF sai do HTML pela skill generate-pdf-report (scripts/html_to_pdf.py dela).

Marcação aceita nos textos da especificação:
  `código`            -> <code>
  **negrito**         -> <b>
  [A CONFIRMAR: ...]  -> destaque amarelo (classe pend)
Todo o resto é escapado, inclusive placeholders como <ARN_KMS>, que sem escape somem no PDF.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "tickets.template.html"
DEFAULT_ACCENT = "#1f4e79"
DEFAULT_ACCENT_SOFT = "#e8eef6"
KINDS = {"new", "optional", "adjustment", "note"}

PENDING_RE = re.compile(r"\[A CONFIRMAR[^\]]*\]")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def inline(text):
    """Escapa o texto e aplica a marcação mínima (código, negrito, pendência)."""
    if not isinstance(text, str):
        raise ValueError("texto esperado, recebido %r" % (text,))
    out = html.escape(text, quote=False)
    out = CODE_RE.sub(lambda m: "<code>%s</code>" % m.group(1), out)
    out = BOLD_RE.sub(lambda m: "<b>%s</b>" % m.group(1), out)
    out = PENDING_RE.sub(lambda m: '<span class="pend">%s</span>' % m.group(0), out)
    return out


def render_items(items, depth=0):
    """Lista de tópicos: string, {"code": ...}, {"group": título, "items": [...]}, {"text": ...}."""
    parts = []
    bullets = []

    def flush():
        if bullets:
            parts.append("<ul>%s</ul>" % "".join(bullets))
            bullets.clear()

    for item in items:
        if isinstance(item, str):
            bullets.append("<li>%s</li>" % inline(item))
        elif isinstance(item, dict) and "code" in item:
            flush()
            parts.append("<pre>%s</pre>" % html.escape(item["code"], quote=False))
        elif isinstance(item, dict) and "group" in item:
            flush()
            tag = "h5" if depth == 0 else "h6"
            parts.append(
                '<div class="group"><%s>%s</%s>%s</div>'
                % (tag, inline(item["group"]), tag, render_items(item.get("items", []), depth + 1))
            )
        elif isinstance(item, dict) and "text" in item:
            flush()
            parts.append("<p>%s</p>" % inline(item["text"]))
        else:
            raise ValueError("item de lista não reconhecido: %r" % (item,))
    flush()
    return "".join(parts)


def render_sections(sections):
    out = []
    for section in sections:
        out.append("<h4>%s</h4>" % inline(section["title"]))
        out.append(render_items(section.get("items", [])))
    return "".join(out)


def render_signature(requester):
    if not requester:
        return ""
    lines = []
    for key, label in (("name", "Nome"), ("network_user", "Usuário de rede"), ("email", "E-mail")):
        if requester.get(key):
            lines.append("%s: %s" % (label, inline(requester[key])))
    return '<p class="signature">%s</p>' % "<br>".join(lines) if lines else ""


def render_card(card):
    if not card:
        return ""
    rows = "".join("<p><b>%s:</b> %s</p>" % (inline(c["label"]), inline(c["text"])) for c in card)
    return '<div class="card">%s</div>' % rows


def render_ticket(ticket, requester):
    kind = ticket.get("kind", "new")
    if kind not in KINDS:
        raise ValueError("%s: kind inválido %r (use %s)" % (ticket.get("code"), kind, sorted(KINDS)))
    head = '<div class="head"><span class="code">%s</span><h2>%s</h2>%s</div>' % (
        inline(ticket["code"]),
        inline(ticket["title"]),
        '<span class="order">%s</span>' % inline(ticket["order"]) if ticket.get("order") else "",
    )
    body = [head, render_card(ticket.get("card"))]
    if kind == "note":
        body.append(render_sections(ticket.get("sections", [])))
    else:
        paste = ticket["paste"]
        inner = ["<p>%s</p>" % inline(paste["lead"]), render_sections(paste.get("sections", []))]
        if paste.get("signature", True):
            inner.append(render_signature(requester))
        body.append('<div class="label">Texto para colar</div>')
        body.append('<div class="paste">%s</div>' % "".join(inner))
    return '<section class="ticket kind-%s">%s</section>' % (kind, "".join(body))


def render_intro(spec):
    doc = spec["document"]
    out = ["<h1>%s</h1>" % inline(doc["title"])]
    if doc.get("subtitle"):
        out.append('<p class="sub">%s</p>' % inline(doc["subtitle"]))
    box = []
    for row in spec.get("intro", []):
        box.append("<p><b>%s:</b> %s</p>" % (inline(row["label"]), inline(row["text"])))
    if spec.get("before_opening"):
        box.append("<p><b>Antes de abrir:</b></p><ul>%s</ul>"
                   % "".join("<li>%s</li>" % inline(t) for t in spec["before_opening"]))
    if spec.get("closing_note"):
        box.append("<p>%s</p>" % inline(spec["closing_note"]))
    tickets = [t for t in spec["tickets"] if t.get("kind", "new") != "note"]
    if tickets:
        cols = spec.get("summary_columns", ["Código", "Recurso", "O que pede"])
        head = "".join("<th>%s</th>" % inline(c) for c in cols)
        rows = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (inline(t["code"]), inline(t.get("summary", t["title"])), inline(t.get("summary_request", "")))
            for t in tickets
        )
        box.append('<table class="summary"><tr>%s</tr>%s</table>' % (head, rows))
    out.append('<div class="box intro">%s</div>' % "".join(box))
    return "".join(out)


def build(spec, template_text):
    doc = spec["document"]
    theme = doc.get("theme", {})
    body = render_intro(spec) + "".join(render_ticket(t, spec.get("requester")) for t in spec["tickets"])
    return (
        template_text.replace("{{file_title}}", html.escape(doc.get("file_title", doc["title"]), quote=False))
        .replace("{{accent}}", theme.get("accent", DEFAULT_ACCENT))
        .replace("{{accent_soft}}", theme.get("accent_soft", DEFAULT_ACCENT_SOFT))
        .replace("{{body}}", body)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera o HTML do lote de chamados.")
    parser.add_argument("spec")
    parser.add_argument("output")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    args = parser.parse_args(argv)
    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        html_text = build(spec, Path(args.template).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1
    Path(args.output).write_text(html_text, encoding="utf-8")
    print("OK: %s (%d chamados)" % (args.output, len(spec["tickets"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
