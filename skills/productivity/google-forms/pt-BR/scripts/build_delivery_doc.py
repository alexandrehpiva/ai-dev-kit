#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta, valida e renderiza o documento de entrega (PDF) de um formulário.

Uso:
    python3 scripts/build_delivery_doc.py delivery.json --out entrega/formulario-v1.pdf
    python3 scripts/build_delivery_doc.py delivery.json --html-only [--html saida.html]
    (Windows: py -3 scripts\\build_delivery_doc.py delivery.json --out entrega\\formulario-v1.pdf)

Opções: --out PDF | --html-only | --html CAMINHO | --template ARQ | --css ARQ | --strict
        --generated-at TEXTO (fixa o carimbo de data; útil em testes)
Sem --out e sem --html-only o uso é inválido (usage_error): o script não adivinha o destino.

Saída: um único JSON em stdout, {"ok","status","data","problems","next_steps"}.
Códigos de saída: 0 = built/html_only; 1 = invalid/render_failed; 2 = erro de uso.
Status: built | html_only | invalid | render_failed | usage_error.
Avisos (não impedem a montagem) aparecem em problems com o prefixo "Aviso:"; com --strict
viram erro. Entre eles, avisos de CONTEÚDO do contrato (DELIVERY-DOC.md): seção reservada sem o
conteúdo mínimo (tabela «Em resumo», link do respondente e de edição por extenso, FAQ de 6 a 12
perguntas, tabela de caminhos quando há ramificação, glossário mínimo...) e citação sem link
(«Pergunta N», «Seção N», «Figura N» fora de link no mesmo parágrafo; termo do glossário que
aparece em uma seção sem nenhum link para ele). Requer Python 3.8+ e apenas a biblioteca padrão. Nunca acessa a rede.

======================================================================================
ESQUEMA DO delivery.json (UTF-8; fonte de verdade executável; schema_version = 1)
======================================================================================
Caminhos de imagem são relativos à pasta do delivery.json.

{
  "schema_version": 1,
  "meta": {
    "form_title": str*            título do formulário
    "version": str*               versão do documento/formulário (ex.: "1.2")
    "date": str*                  data do documento (texto livre, ex.: "2026-11-11")
    "owner": str*                 dono do formulário
    "subtitle": str               subtítulo da capa (padrão: "Manual de uso, referência e histórico do formulário")
    "approved_by": str, "approved_at": str     aprovação do dono (opcional)
    "confidentiality": str        rótulo (padrão "Uso interno")
    "form_status": str            ex.: "publicado" (aparece na nota da capa)
    "document_title": str         aceito e ignorado (o título do HTML é fixo no template)
    "language": "pt-BR"           aceito (só pt-BR)
    "links": {"respondent_url": https*, "edit_url": https, "responses_url": https, "sheet_url": https|null}
    "ux_verdict": {"verdict": "APROVADO" | "APROVADO COM RESSALVAS" | "REPROVADO"*,
                   "reviewed_at": str, "reviewer": str,
                   "accepted_caveats": [str], "pending_decisions": [str], "not_verified": [str]}
  },
  "sections": [ {"id": <id reservado>*, "title": str, "body_md": Markdown restrito} ],
  "form_sections": [ {"id": "s1"*, "title": str*, "description": str, "after": str} ],
  "items": [ {"id": "q3"*, "section": "s1" (obrigatório se houver form_sections),
              "number": int, "kind": "question"|"title_description"|"image"|"video" (padrão question),
              "type_label": str*, "title": str*, "description": str|null (texto literal),
              "required": bool, "options": [str | {"label": str, "goes_to": "s2"|"next"|"submit"}],
              "validation": null | str | {"rule": str, "error": str},
              "quiz": null | {"points": int, "correct": str|[str], "feedback": str},
              "use": Markdown inline* ("Para que serve"), "personal_data": bool,
              "badges": subconjunto de obrigatoria|opcional|ramificacao|quiz (padrão: derivado)} ],
  "glossary": [ {"slug": "ramificacao"*, "term": str*, "definition": Markdown inline*} ],
  "history": [ {"version": str*, "date": str*, "change": str*, "requested_by": str, "approved_by": str} ],
  "captures": [ {"file": "capturas/03-x.png"*, "taken_at": str*, "viewport": "1280x800",
                 "form_version": str*, "source": str, "masked": true*} ]
}
(* = obrigatório.) ids (seção do formulário, item, termo): kebab-case ASCII `[a-z][a-z0-9-]*`.

Seções do documento (`sections[].id`), nesta ordem, sem repetir e sem `capa`/`sumario`
(vindos do template): visao-geral, acesso-e-links, passo-a-passo-respondente, funcionalidades,
particularidades, respostas, editar-e-manter, privacidade, perguntas-frequentes, referencia,
glossario, historico. As nove primeiras exigem body_md não vazio. `referencia`, `glossario` e
`historico` são GERADAS (de items+form_sections, glossary, history+ux_verdict); o body_md delas
é só uma introdução opcional e a entrada em `sections` pode até faltar (título padrão).

Âncoras geradas: item-<id>, secao-<id> (ficha de seção do formulário), termo-<slug>,
fig-<arquivo-sem-extensão> (numeração "Figura N" via CSS, na ordem de aparição), cit-<n>
(trecho citante, alvo dos backlinks «Citada em»), <id-da-seção>-<título> ou o {#id} explícito
nos títulos.

======================================================================================
MARKDOWN RESTRITO (corpo das seções; HTML cru NUNCA é aceito: tudo é escapado)
======================================================================================
Blocos
  ## Título            subtítulo (h3; entra no sumário, nível 2).   ### Título  (h4; sumário nível 3)
  #### Título          h5 (fora do sumário).  Opcional: `## Título {#id-explicito}`.
  parágrafo            linhas consecutivas; linha em branco separa.
  - item / * item      lista; 1. item  lista ordenada. Um nível de aninhamento (2+ espaços).
  | a | b |            tabela pipe; 2ª linha |---|:--:|---:| define alinhamento.
  ![legenda](capturas/01-x.png)   imagem sozinha na linha -> figure.screenshot numerada.
                       A imagem deve estar em `captures` (masked=true, form_version = meta.version).
                       Legenda obrigatória; prefixo "Figura:" é removido (o número vem do CSS).
  ::: screens-pair     par desktop + celular: exatamente 2 imagens; fecha com `:::` sozinho.
  ::: step Título      passo numerado (conteúdo livre dentro, inclusive imagem); fecha com `:::`.
  > [!NOTE] / [!TIP] / [!WARNING] / [!IMPORTANT]   callout; linhas seguintes com `> `.
  ```                  bloco de código (fechado por ```).     ---   linha horizontal.
Inline
  **negrito**  *itálico*  `código`  [[Ctrl]] (tecla -> <kbd class="kbd">)
  [texto](#ancora)     link interno (âncora precisa existir; falha se não existir)
  [texto](https://...) link externo (só https; recebe marca visual ↗). http, mailto,
                       javascript: e caminhos relativos NÃO são aceitos.
  [Figura 3](#fig-03-x) citação de figura: o número é conferido com a figura real; toda
                       figura precisa ser citada ao menos uma vez.
  {{meta.form_title}} {{meta.version}} {{meta.date}} {{meta.owner}} {{links.respondent_url}}
  {{links.edit_url}} {{links.responses_url}} {{links.sheet_url}}   substituídos antes da conversão.
Títulos não são permitidos dentro de callouts/passos/pares.

======================================================================================
TEMPLATE (templates/delivery-doc/template.html + styles.css)
======================================================================================
Placeholders {{...}} resolvidos: inline_css, form_title_css, form_title, cover_subtitle,
version, date, owner, ux_verdict, ux_verdict_class (ok|attention|fail), cover_note, toc
(<ol class="toc-list">), sections, colophon, generated_at, respondent_url, edit_url,
responses_url, sheet_url. Placeholder desconhecido no template é erro. <link rel=stylesheet>
local também é embutido. O template deve trazer id="capa" e id="sumario".
"""

import argparse
import base64
import datetime
import glob
import html
import json
import mimetypes
import os
import pathlib
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zlib
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_TEMPLATE = os.path.join(SKILL_DIR, "templates", "delivery-doc", "template.html")
SISTER_ENV = "GFORMS_HTML_TO_PDF"
SCHEMA_VERSION = 1

BODY_ORDER = ["visao-geral", "acesso-e-links", "passo-a-passo-respondente", "funcionalidades",
              "particularidades", "respostas", "editar-e-manter", "privacidade",
              "perguntas-frequentes", "referencia", "glossario", "historico"]
GENERATED = ("referencia", "glossario", "historico")
RESERVED_IDS = ["capa", "sumario"] + BODY_ORDER
DEFAULT_TITLES = {
    "visao-geral": "Visão geral",
    "acesso-e-links": "Acesso e links",
    "passo-a-passo-respondente": "Passo a passo para quem responde",
    "funcionalidades": "Funcionalidades",
    "particularidades": "Particularidades",
    "respostas": "Respostas",
    "editar-e-manter": "Editar e manter",
    "privacidade": "Privacidade",
    "perguntas-frequentes": "Perguntas frequentes",
    "referencia": "Referência do formulário",
    "glossario": "Glossário",
    "historico": "Histórico",
}
KNOWN_PLACEHOLDERS = {
    "inline_css", "form_title_css", "form_title", "cover_subtitle", "version", "date", "owner",
    "ux_verdict", "ux_verdict_class", "cover_note", "toc", "sections", "colophon", "generated_at",
    "respondent_url", "edit_url", "responses_url", "sheet_url",
}
KINDS = ("question", "title_description", "image", "video")
BADGE_NAMES = ("obrigatoria", "opcional", "ramificacao", "quiz")
VERDICTS = {"APROVADO": "ok", "APROVADO COM RESSALVAS": "attention", "REPROVADO": "fail"}
CALLOUTS = {"NOTE": ("note", "Nota"), "TIP": ("tip", "Dica"), "WARNING": ("warning", "Atenção"),
            "IMPORTANT": ("important", "Importante")}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".svg": "image/svg+xml"}
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ANCHOR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

JARGON = [
    (r"snapshot", "snapshot"), (r"\bref=", "ref="), (r"browser_\w+", "browser_*"),
    (r"\bspec\b", "spec"), (r"\bYAML\b", "YAML"), (r"\bJSON\b", "JSON"),
    (r"FORM-SPEC", "FORM-SPEC"), (r"PENDENTE_UI", "PENDENTE_UI"), (r"pending_owner", "pending_owner"),
    (r"\bMCP\b", "MCP"), (r"Playwright", "Playwright"), (r"\bitemId\b", "itemId"),
    (r"batchUpdate", "batchUpdate"), (r"\bendpoint\b", "endpoint"), (r"\bsubagentes?\b", "subagente"),
    (r"\bagentes?\b", "agente"),
]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
SAFE_MAIL_DOMAINS = ("example.com", "example.org", "example.net", "exemplo.com", "exemplo.org",
                     "exemplo.com.br")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def esc(text):
    return html.escape("" if text is None else str(text), quote=True)


def slugify(text):
    s = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "x"


def plain(md):
    """Texto simples de um trecho de Markdown inline (para sumário, alt e rótulos)."""
    s = re.sub(r"`([^`]*)`", r"\1", md)
    s = re.sub(r"\[\[([^\[\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[([^\[\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<![\*\w])\*([^*]+)\*(?![\*\w])", r"\1", s)
    return s.strip()


class Issues(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        if msg not in self.errors:
            self.errors.append(msg)

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)


class Ctx(object):
    """Estado compartilhado de uma montagem."""

    def __init__(self, base_dir, meta, captures, issues):
        self.base_dir = base_dir
        self.meta = meta
        self.captures = captures          # caminho normalizado -> entrada
        self.issues = issues
        self.figures = []                 # {n,id,caption,file}
        self.fig_ids = set()
        self.fig_refs = []                # (alvo, rótulo, seção)
        self.cites = []                   # {target,id,section,heading,owner}
        self.toc = []                     # (section_id, nível, texto, id)
        self.heading_ids = set()
        self.cite_n = 0
        self.uri_cache = {}
        self.used_captures = set()

    def embed(self, rel):
        if rel in self.uri_cache:
            return self.uri_cache[rel]
        full = os.path.join(self.base_dir, *rel.split("/"))
        ext = os.path.splitext(rel)[1].lower()
        if ext not in IMAGE_TYPES:
            self.issues.error("Imagem com formato não aceito (use png, jpg ou svg): %s" % rel)
            uri = None
        elif not os.path.isfile(full):
            self.issues.error("Imagem inexistente: %s (procurada em %s)" % (rel, full))
            uri = None
        else:
            with open(full, "rb") as fh:
                raw = fh.read()
            uri = "data:%s;base64,%s" % (IMAGE_TYPES[ext], base64.b64encode(raw).decode("ascii"))
        self.uri_cache[rel] = uri
        return uri


# ---------------------------------------------------------------------------
# Conversor Markdown restrito -> HTML
# ---------------------------------------------------------------------------

_CODE = re.compile(r"(`+)(.+?)\1")
_KBD = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
_LINK = re.compile(r"\[([^\[\]\n]+)\]\(([^()\s]+)\)")
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_ITAL = re.compile(r"(?<![\*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\*\w])")
_HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*(?:\{#([A-Za-z0-9][A-Za-z0-9_-]*)\})?\s*$")
_IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^()\s]+)\)\s*$")
_LISTITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_FENCE = re.compile(r"^```")
_CONTAINER = re.compile(r"^:::\s*(\S+)\s*(.*?)\s*$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_HR = re.compile(r"^(-{3,}|\*{3,})\s*$")
_CALLOUT = re.compile(r"^\[!(NOTE|TIP|WARNING|IMPORTANT)\]\s*(.*)$", re.I)


class Converter(object):
    """Converte o Markdown restrito de uma seção. Nunca emite HTML vindo do usuário."""

    def __init__(self, ctx, section_id, section_title=""):
        self.ctx = ctx
        self.section_id = section_id
        self.section_title = section_title
        self.heading = None
        self.step_n = 0
        self.owner = None

    # ---- inline
    def inline(self, text):
        text = (text or "").replace("\x00", "")
        slots = []

        def stash(h):
            slots.append(h)
            return "\x00%d\x00" % (len(slots) - 1)

        text = _CODE.sub(lambda m: stash("<code>%s</code>" % esc(m.group(2).strip())), text)
        text = _KBD.sub(lambda m: stash('<kbd class="kbd">%s</kbd>' % esc(m.group(1).strip())), text)
        text = _LINK.sub(lambda m: stash(self._link(m.group(1), m.group(2), slots)), text)
        out = self._rich(text)
        while "\x00" in out:
            out = re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], out)
        return out

    @staticmethod
    def _rich(text):
        s = html.escape(text, quote=False)
        s = _BOLD.sub(r"<strong>\1</strong>", s)
        s = _ITAL.sub(r"<em>\1</em>", s)
        return s

    def _link(self, label, url, slots):
        label_html = self._rich(label)
        if url.startswith("#"):
            if not ANCHOR_RE.match(url[1:]):
                self.ctx.issues.error("Âncora inválida no link [%s](%s)." % (label, url))
                return label_html
            target = url[1:]
            attrs = ' class="xref" href="#%s"' % esc(target)
            if target.startswith(("item-", "secao-", "termo-")):
                if target != self.owner:
                    self.ctx.cite_n += 1
                    cid = "cit-%d" % self.ctx.cite_n
                    self.ctx.cites.append({"target": target, "id": cid, "section": self.section_id,
                                           "section_title": self.section_title,
                                           "heading": self.heading})
                    attrs += ' id="%s"' % cid
            elif target.startswith("fig-"):
                self.ctx.fig_refs.append((target, plain(label), self.section_id))
            return "<a%s>%s</a>" % (attrs, label_html)
        if url.lower().startswith("https://") and len(url) > 8 and " " not in url:
            return ('<a class="external" href="%s" target="_blank" rel="noopener noreferrer">%s'
                    '<span class="ext-mark" aria-hidden="true"> \u2197</span></a>' % (esc(url), label_html))
        self.ctx.issues.error("Link não permitido [%s](%s): só âncoras (#id) e https://." % (label, url))
        return label_html

    # ---- blocos
    def convert(self, md):
        lines = (md or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        return self._blocks(lines, 0)

    def _starts_block(self, lines, i):
        line = lines[i]
        s = line.strip()
        if not s:
            return True
        if _FENCE.match(s) or _CONTAINER.match(s) or s == ":::" or s.startswith(">"):
            return True
        if _HEADING.match(s) or _IMAGE.match(s) or _HR.match(s) or _LISTITEM.match(line):
            return True
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]) and "|" in lines[i + 1]:
            return True
        return False

    def _blocks(self, lines, depth):
        out = []
        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            s = line.strip()
            if not s:
                i += 1
                continue
            if _FENCE.match(s):
                j = i + 1
                buf = []
                while j < n and not _FENCE.match(lines[j].strip()):
                    buf.append(lines[j])
                    j += 1
                if j >= n:
                    self.ctx.issues.error("Bloco de código sem fechamento (```) na seção %s." % self.section_id)
                out.append("<pre><code>%s</code></pre>" % esc("\n".join(buf)))
                i = j + 1
                continue
            m = _CONTAINER.match(s)
            if m:
                i = self._container(lines, i, m, depth, out)
                continue
            if s == ":::":
                self.ctx.issues.error("`:::` de fechamento sem bloco aberto na seção %s." % self.section_id)
                i += 1
                continue
            m = _HEADING.match(s)
            if m:
                out.append(self._heading(m, depth))
                i += 1
                continue
            if _HR.match(s):
                out.append("<hr>")
                i += 1
                continue
            m = _IMAGE.match(s)
            if m:
                out.append(self._figure(m.group(1), m.group(2)))
                i += 1
                continue
            if s.startswith(">"):
                i = self._quote(lines, i, depth, out)
                continue
            if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]) and "|" in lines[i + 1]:
                i = self._table(lines, i, out)
                continue
            if _LISTITEM.match(line):
                i = self._list(lines, i, out)
                continue
            buf = [s]
            i += 1
            while i < n and not self._starts_block(lines, i):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>%s</p>" % self.inline(" ".join(buf)))
        return "\n".join(out)

    def _heading(self, m, depth):
        hashes, text, explicit = m.group(1), m.group(2), m.group(3)
        if depth > 0:
            self.ctx.issues.error("Título não permitido dentro de callout/passo/par (seção %s): %s"
                                  % (self.section_id, text))
            return "<p><strong>%s</strong></p>" % self.inline(text)
        level = len(hashes)
        if level == 1:
            self.ctx.issues.error("`#` (título de nível 1) é reservado; use ## na seção %s: %s"
                                  % (self.section_id, text))
            level = 2
        tag = "h%d" % (level + 1)
        hid = explicit or "%s-%s" % (self.section_id, slugify(plain(text)))
        if not explicit:
            base, k = hid, 2
            while hid in self.ctx.heading_ids:
                hid = "%s-%d" % (base, k)
                k += 1
        self.ctx.heading_ids.add(hid)
        if level in (2, 3):
            self.ctx.toc.append((self.section_id, level, plain(text), hid))
        if level == 2:
            self.heading = plain(text)
        return '<%s id="%s">%s</%s>' % (tag, esc(hid), self.inline(text), tag)

    def _figure(self, alt, path):
        ctx = self.ctx
        caption = re.sub(r"^\s*Figura\s*\d*\s*[:\u2014-]\s*", "", alt).strip()
        if not caption:
            ctx.issues.error("Figura sem legenda: %s" % path)
        rel = posixpath.normpath(path.replace("\\", "/"))
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", rel) or rel.startswith("/") or rel.startswith(".."):
            ctx.issues.error("Imagem fora da pasta do delivery.json ou com caminho não permitido: %s" % path)
            return '<p class="missing">[imagem inválida: %s]</p>' % esc(path)
        fid = "fig-" + slugify(posixpath.splitext(posixpath.basename(rel))[0])
        if fid in ctx.fig_ids:
            ctx.issues.error("Imagem usada mais de uma vez (âncora duplicada %s): %s" % (fid, rel))
        ctx.fig_ids.add(fid)
        cap = ctx.captures.get(rel)
        ctx.used_captures.add(rel)
        if cap is None:
            ctx.issues.error("Imagem não registrada em `captures`: %s" % rel)
        else:
            if cap.get("masked") is not True:
                ctx.issues.error("Captura sem masked=true (privacidade): %s" % rel)
            if str(cap.get("form_version")) != str(ctx.meta.get("version")):
                ctx.issues.error("Captura %s é da versão %s do formulário, mas meta.version é %s."
                                 % (rel, cap.get("form_version"), ctx.meta.get("version")))
        uri = ctx.embed(rel)
        ctx.figures.append({"n": len(ctx.figures) + 1, "id": fid, "caption": caption, "file": rel})
        if uri is None:
            return '<p class="missing">[imagem ausente: %s]</p>' % esc(rel)
        return ('<figure class="screenshot" id="%s"><img src="%s" alt="%s">'
                '<figcaption>%s</figcaption></figure>' % (fid, uri, esc(caption), self.inline(caption)))

    def _container(self, lines, i, m, depth, out):
        name, title = m.group(1), m.group(2)
        j, d = i + 1, 1
        while j < len(lines):
            t = lines[j].strip()
            if t == ":::":
                d -= 1
                if d == 0:
                    break
            elif _CONTAINER.match(t):
                d += 1
            j += 1
        if j >= len(lines):
            self.ctx.issues.error("Bloco `::: %s` sem fechamento (`:::`) na seção %s." % (name, self.section_id))
        inner = self._blocks(lines[i + 1:j], depth + 1)
        if name == "step":
            self.step_n += 1
            head = '<h3 class="step-title">%s</h3>' % self.inline(title) if title else ""
            out.append('<div class="step" data-n="%d">%s%s</div>' % (self.step_n, head, inner))
        elif name == "screens-pair":
            if inner.count("<figure") != 2:
                self.ctx.issues.error("`::: screens-pair` exige exatamente 2 imagens (seção %s)." % self.section_id)
            inner = inner.replace('<figure class="screenshot"', '<figure class="screenshot desktop"', 1)
            k = inner.rfind('<figure class="screenshot"')
            if k >= 0:
                inner = inner[:k] + '<figure class="screenshot mobile"' + inner[k + len('<figure class="screenshot"'):]
            out.append('<div class="screens-pair">%s</div>' % inner)
        else:
            self.ctx.issues.error("Bloco desconhecido `::: %s` (use step ou screens-pair)." % name)
            out.append(inner)
        return j + 1

    def _quote(self, lines, i, depth, out):
        buf = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
            i += 1
        m = _CALLOUT.match(buf[0].strip()) if buf else None
        if m:
            cls, label = CALLOUTS[m.group(1).upper()]
            rest = ([m.group(2)] if m.group(2) else []) + buf[1:]
            out.append('<div class="callout %s" role="note">%s</div>' % (cls, self._blocks(rest, depth + 1)))
        else:
            out.append("<blockquote>%s</blockquote>" % self._blocks(buf, depth + 1))
        return i

    def _table(self, lines, i, out):
        def cells(row):
            row = row.strip()
            if row.startswith("|"):
                row = row[1:]
            if row.endswith("|") and not row.endswith("\\|"):
                row = row[:-1]
            return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]

        head = cells(lines[i])
        aligns = []
        for c in cells(lines[i + 1]):
            if c.startswith(":") and c.endswith(":"):
                aligns.append("center")
            elif c.endswith(":"):
                aligns.append("right")
            else:
                aligns.append("left")
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i]:
            rows.append(cells(lines[i]))
            i += 1

        def style(k):
            return ' style="text-align:%s"' % aligns[k] if k < len(aligns) and aligns[k] != "left" else ""

        h = "".join('<th scope="col"%s>%s</th>' % (style(k), self.inline(c)) for k, c in enumerate(head))
        body = []
        for r in rows:
            r = (r + [""] * len(head))[:len(head)]
            body.append("<tr>%s</tr>" % "".join("<td%s>%s</td>" % (style(k), self.inline(c))
                                                for k, c in enumerate(r)))
        out.append('<table class="data"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
                   % (h, "".join(body)))
        return i

    def _list(self, lines, i, out):
        entries = []  # [indent, ordered, start, [textos]]
        while i < len(lines):
            line = lines[i]
            m = _LISTITEM.match(line)
            if m:
                marker = m.group(2)
                ordered = marker[0].isdigit()
                entries.append([len(m.group(1).expandtabs(4)), ordered,
                                int(marker[:-1]) if ordered else None, [m.group(3).strip()]])
                i += 1
            elif not line.strip():
                k = i
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and (_LISTITEM.match(lines[k]) or
                                       (lines[k].startswith("  ") and entries)):
                    i = k
                else:
                    break
            elif line.startswith((" ", "\t")) and entries:
                entries[-1][3].append(line.strip())
                i += 1
            else:
                break
        base = entries[0][0]
        top = []
        for e in entries:
            if e[0] >= base + 2 and top:
                top[-1][1].append(e)
            else:
                top.append((e, []))

        def render(items, ordered, start):
            tag = "ol" if ordered else "ul"
            attr = ' start="%d"' % start if ordered and start not in (None, 1) else ""
            return "<%s%s>%s</%s>" % (tag, attr, "".join(items), tag)

        def group(pairs):
            res, cur, cur_kind, cur_start = [], [], None, None
            for e, kids in pairs:
                if cur_kind is not None and e[1] != cur_kind:
                    res.append(render(cur, cur_kind, cur_start))
                    cur = []
                if not cur:
                    cur_kind, cur_start = e[1], e[2]
                cur.append("<li>%s</li>" % self.inline(" ".join(e[3])))
            if cur:
                res.append(render(cur, cur_kind, cur_start))
            return "".join(res)

        parts, cur, cur_kind, cur_start = [], [], None, None
        for e, kids in top:
            if cur_kind is not None and e[1] != cur_kind:
                parts.append(render(cur, cur_kind, cur_start))
                cur = []
            if not cur:
                cur_kind, cur_start = e[1], e[2]
            nested = ""
            if kids:
                if any(k[0] >= kids[0][0] + 2 for k in kids[1:]):
                    self.ctx.issues.warn("Lista com mais de 1 nível de aninhamento (seção %s): achatada."
                                         % self.section_id)
                nested = group([(k, []) for k in kids])
            cur.append("<li>%s%s</li>" % (self.inline(" ".join(e[3])), nested))
        if cur:
            parts.append(render(cur, cur_kind, cur_start))
        out.append("".join(parts))
        return i


# ---------------------------------------------------------------------------
# Esquema do delivery.json
# ---------------------------------------------------------------------------

def _is_str(v):
    return isinstance(v, str) and v.strip() != ""


def validate_schema(d, issues):
    """Valida o delivery.json. Registra erros em issues; devolve True se dá para montar."""
    if not isinstance(d, dict):
        issues.error("delivery.json precisa ser um objeto JSON.")
        return False
    if d.get("schema_version") != SCHEMA_VERSION:
        issues.error("schema_version deve ser %d (veio %r)." % (SCHEMA_VERSION, d.get("schema_version")))
    meta = d.get("meta")
    if not isinstance(meta, dict):
        issues.error("`meta` ausente ou inválido.")
        return False
    for k in ("form_title", "version", "date", "owner"):
        if not _is_str(meta.get(k)):
            issues.error("meta.%s é obrigatório (texto não vazio)." % k)
    links = meta.get("links")
    if not isinstance(links, dict):
        issues.error("meta.links ausente.")
    else:
        if not _is_str(links.get("respondent_url")):
            issues.error("meta.links.respondent_url é obrigatório.")
        for k in ("respondent_url", "edit_url", "responses_url", "sheet_url"):
            v = links.get(k)
            if v is not None and not (isinstance(v, str) and v.startswith("https://")):
                issues.error("meta.links.%s precisa ser um endereço https:// (ou null)." % k)
    uv = meta.get("ux_verdict")
    if not isinstance(uv, dict) or uv.get("verdict") not in VERDICTS:
        issues.error("meta.ux_verdict.verdict é obrigatório: %s." % " | ".join(sorted(VERDICTS)))
    else:
        for k in ("accepted_caveats", "pending_decisions", "not_verified"):
            if k in uv and not (isinstance(uv[k], list) and all(isinstance(x, str) for x in uv[k])):
                issues.error("meta.ux_verdict.%s deve ser uma lista de textos." % k)

    secs = d.get("sections")
    seen_order = -1
    seen = set()
    if not isinstance(secs, list) or not secs:
        issues.error("`sections` ausente ou vazio.")
    else:
        for s in secs:
            sid = s.get("id") if isinstance(s, dict) else None
            if sid in ("capa", "sumario"):
                issues.error("sections não deve conter `%s` (vem do template)." % sid)
            elif sid not in BODY_ORDER:
                issues.error("Seção com id não reservado: %r (permitidos: %s)." % (sid, ", ".join(BODY_ORDER)))
            else:
                if sid in seen:
                    issues.error("Seção repetida: %s." % sid)
                seen.add(sid)
                pos = BODY_ORDER.index(sid)
                if pos < seen_order:
                    issues.error("Seção %s fora da ordem do contrato." % sid)
                seen_order = max(seen_order, pos)
                if "title" in s and not _is_str(s.get("title")):
                    issues.error("Seção %s com title vazio." % sid)
                if not isinstance(s.get("body_md", ""), str):
                    issues.error("Seção %s: body_md deve ser texto." % sid)
        for sid in BODY_ORDER:
            if sid not in GENERATED and sid not in seen:
                issues.error("Seção obrigatória ausente: %s." % sid)

    fs = d.get("form_sections", [])
    fsids = set()
    if not isinstance(fs, list):
        issues.error("form_sections deve ser uma lista.")
        fs = []
    for f in fs:
        fid = f.get("id") if isinstance(f, dict) else None
        if not (isinstance(fid, str) and ID_RE.match(fid)) or not _is_str(f.get("title")):
            issues.error("form_sections: cada seção precisa de id kebab-case e title (%r)." % (f,))
            continue
        if fid in fsids:
            issues.error("form_sections: id repetido %s." % fid)
        fsids.add(fid)

    items = d.get("items")
    itemids = set()
    if not isinstance(items, list) or not items:
        issues.error("`items` ausente ou vazio (a referência é obrigatória).")
        items = []
    for it in items:
        if not isinstance(it, dict):
            issues.error("items: cada item deve ser um objeto.")
            continue
        iid = it.get("id")
        if not (isinstance(iid, str) and ID_RE.match(iid)):
            issues.error("items: id inválido %r (kebab-case ASCII, começa com letra)." % (iid,))
            continue
        if iid in itemids:
            issues.error("items: id repetido %s." % iid)
        itemids.add(iid)
        for k in ("title", "type_label", "use"):
            if not _is_str(it.get(k)):
                issues.error("Item %s: `%s` é obrigatório." % (iid, k))
        if it.get("kind", "question") not in KINDS:
            issues.error("Item %s: kind deve ser %s." % (iid, "|".join(KINDS)))
        if fs and it.get("section") not in fsids:
            issues.error("Item %s: section %r não existe em form_sections." % (iid, it.get("section")))
        for b in it.get("badges", []) or []:
            if b not in BADGE_NAMES:
                issues.error("Item %s: badge inválido %r." % (iid, b))
        for o in it.get("options", []) or []:
            lab = o if isinstance(o, str) else (o.get("label") if isinstance(o, dict) else None)
            if not _is_str(lab):
                issues.error("Item %s: opção sem label." % iid)
            if isinstance(o, dict) and o.get("goes_to") not in (None, "next", "submit") \
                    and o.get("goes_to") not in fsids:
                issues.error("Item %s: goes_to %r não é seção do formulário, next nem submit."
                             % (iid, o.get("goes_to")))
        v = it.get("validation")
        if v is not None and not (isinstance(v, str) or isinstance(v, dict)):
            issues.error("Item %s: validation deve ser null, texto ou {rule, error}." % iid)
        q = it.get("quiz")
        if q is not None and not isinstance(q, dict):
            issues.error("Item %s: quiz deve ser null ou objeto." % iid)

    gl = d.get("glossary", [])
    if not isinstance(gl, list) or not gl:
        issues.error("`glossary` ausente ou vazio (o glossário é obrigatório).")
        gl = []
    slugs = set()
    for g in gl:
        slug = g.get("slug") if isinstance(g, dict) else None
        if not (isinstance(slug, str) and ID_RE.match(slug)) or not _is_str(g.get("term")) \
                or not _is_str(g.get("definition")):
            issues.error("glossary: cada termo precisa de slug kebab-case, term e definition (%r)." % (g,))
            continue
        if slug in slugs:
            issues.error("glossary: slug repetido %s." % slug)
        slugs.add(slug)

    hist = d.get("history")
    if not isinstance(hist, list) or not hist:
        issues.error("`history` ausente ou vazio.")
    else:
        for h in hist:
            if not isinstance(h, dict) or not all(_is_str(h.get(k)) for k in ("version", "date", "change")):
                issues.error("history: cada linha precisa de version, date e change (%r)." % (h,))

    caps = d.get("captures")
    if not isinstance(caps, list):
        issues.error("`captures` ausente (lista; cada imagem do corpo precisa estar registrada).")
    else:
        for c in caps:
            if not isinstance(c, dict) or not _is_str(c.get("file")) or not _is_str(c.get("taken_at")) \
                    or c.get("form_version") in (None, ""):
                issues.error("captures: cada entrada precisa de file, taken_at e form_version (%r)." % (c,))
    return not issues.errors


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------

def substitute_meta(md, meta):
    lk = meta.get("links") or {}
    vals = {"meta.form_title": meta.get("form_title"), "meta.version": meta.get("version"),
            "meta.date": meta.get("date"), "meta.owner": meta.get("owner")}
    for k in ("respondent_url", "edit_url", "responses_url", "sheet_url"):
        vals["links." + k] = lk.get(k)
    return vals


def expand_tokens(md, meta, issues, where):
    vals = substitute_meta(md, meta)

    def rep(m):
        key = m.group(1)
        if key not in vals:
            issues.error("Token desconhecido {{%s}} em %s." % (key, where))
            return m.group(0)
        v = vals[key]
        if v in (None, ""):
            issues.error("Token {{%s}} usado em %s, mas o valor está vazio." % (key, where))
            return ""
        return str(v)

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", rep, md or "")


def css_string(text):
    s = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return s.replace("<", "\\3c ")


def section_label(order_titles, sid):
    return order_titles.get(sid, sid)


def render_item_cards(ctx, d, issues, conv):
    """Referência: ficha de seção do formulário + ficha de cada item."""
    fsecs = d.get("form_sections") or []
    items = d["items"]
    sec_title = {}
    for k, f in enumerate(fsecs, 1):
        sec_title[f["id"]] = "Seção %d — %s" % (k, f["title"])
    item_by_id = {it["id"]: it for it in items}

    def item_label(it):
        if it.get("kind", "question") == "question" and it.get("number"):
            return "Pergunta %s — %s" % (it["number"], it["title"])
        return it["title"]

    def badge(cls, text):
        return '<span class="badge %s">%s</span>' % (cls, text)

    def item_card(it):
        iid = it["id"]
        conv.owner = "item-" + iid
        kind = it.get("kind", "question")
        opts = it.get("options") or []
        badges = it.get("badges")
        if badges is None:
            badges = []
            if kind == "question":
                badges.append("obrigatoria" if it.get("required") else "opcional")
            if any(isinstance(o, dict) and o.get("goes_to") for o in opts):
                badges.append("ramificacao")
            if it.get("quiz"):
                badges.append("quiz")
        names = {"obrigatoria": ("required", "Obrigatória"), "opcional": ("optional", "Opcional"),
                 "ramificacao": ("branch", "Ramificação"), "quiz": ("quiz", "Quiz")}
        bhtml = "".join(badge(*names[b]) for b in badges)
        idtxt = ("P%s" % it["number"]) if kind == "question" and it.get("number") else iid.upper()
        fields = ["<dt>Tipo</dt><dd>%s</dd>" % esc(it["type_label"])]
        if kind == "question":
            fields.append("<dt>Obrigatória</dt><dd>%s</dd>" % ("Sim" if it.get("required") else "Não"))
        if it.get("description"):
            fields.append("<dt>Texto que aparece</dt><dd>%s</dd>" % esc(it["description"]))
        if opts:
            lis = []
            for o in opts:
                label = o if isinstance(o, str) else o["label"]
                dest = "" if isinstance(o, str) else o.get("goes_to")
                extra = ""
                if dest == "next":
                    extra = " \u2192 vai para a próxima seção"
                elif dest == "submit":
                    extra = " \u2192 envia o formulário"
                elif dest:
                    extra = ' \u2192 vai para <a class="xref" href="#secao-%s">%s</a>' % (
                        esc(dest), esc(sec_title.get(dest, dest)))
                    ctx.cite_n += 1
                    ctx.cites.append({"target": "secao-" + dest, "id": "cit-%d" % ctx.cite_n,
                                      "section": "referencia", "section_title": conv.section_title,
                                      "heading": item_label(it)})
                    extra = extra.replace('<a class="xref"', '<a id="cit-%d" class="xref"' % ctx.cite_n)
                lis.append("<li>%s%s</li>" % (esc(label), extra))
            fields.append("<dt>Opções</dt><dd><ul>%s</ul></dd>" % "".join(lis))
        v = it.get("validation")
        if v:
            if isinstance(v, str):
                fields.append("<dt>Validação</dt><dd>%s</dd>" % esc(v))
            else:
                txt = esc(v.get("rule", ""))
                if v.get("error"):
                    txt += "<br>Mensagem de erro: \u00ab%s\u00bb" % esc(v["error"])
                fields.append("<dt>Validação</dt><dd>%s</dd>" % txt)
        q = it.get("quiz")
        if q:
            qt = "Vale %s ponto(s)." % esc(q.get("points", "?")) if q.get("points") is not None else ""
            cor = q.get("correct")
            if cor:
                cor = ", ".join(cor) if isinstance(cor, list) else cor
                qt += " Resposta correta: %s." % esc(cor)
            if q.get("feedback"):
                qt += " Retorno: \u00ab%s\u00bb" % esc(q["feedback"])
            fields.append("<dt>Quiz</dt><dd>%s</dd>" % qt.strip())
        if it.get("personal_data"):
            fields.append("<dt>Dado pessoal</dt><dd>Sim. Veja a seção "
                          '<a class="xref" href="#privacidade">Privacidade</a>.</dd>')
        fields.append("<!--cited-dl:item-%s-->" % iid)
        use = conv.inline(it["use"])
        conv.owner = None
        return ('<article class="item-card" id="item-%s"><header class="item-head"><span class="item-id">%s</span>'
                '<h4 class="item-title">%s</h4><span class="badges">%s</span></header>'
                '<dl class="item-fields">%s</dl><p class="item-use"><strong>Para que serve:</strong> %s</p>'
                '<p class="backlink"><a href="#sumario">\u2191 voltar ao sumário</a></p></article>'
                % (esc(iid), esc(idtxt), esc(item_label(it)), bhtml, "".join(fields), use))

    def section_card(f, k):
        sid = f["id"]
        mine = [it for it in items if it.get("section") == sid]
        fields = []
        if f.get("description"):
            fields.append("<dt>Texto que aparece</dt><dd>%s</dd>" % esc(f["description"]))
        if f.get("after"):
            fields.append("<dt>Depois desta seção</dt><dd>%s</dd>" % esc(f["after"]))
        if mine:
            lis = []
            for it in mine:
                ctx.cite_n += 1
                ctx.cites.append({"target": "item-" + it["id"], "id": "cit-%d" % ctx.cite_n,
                                  "section": "referencia", "section_title": conv.section_title,
                                  "heading": "Seção %d — %s" % (k, f["title"])})
                lis.append('<li><a id="cit-%d" class="xref" href="#item-%s">%s</a></li>'
                           % (ctx.cite_n, esc(it["id"]), esc(item_label(it))))
            fields.append("<dt>Itens desta seção</dt><dd><ul>%s</ul></dd>" % "".join(lis))
        fields.append("<!--cited-dl:secao-%s-->" % sid)
        title = "Seção %d — %s" % (k, f["title"])
        ctx.toc.append(("referencia", 2, title, "secao-" + sid))
        return ('<article class="item-card section-card" id="secao-%s"><header class="item-head">'
                '<span class="item-id">S%d</span><h4 class="item-title">%s</h4></header>'
                '<dl class="item-fields">%s</dl>'
                '<p class="backlink"><a href="#sumario">\u2191 voltar ao sumário</a></p></article>'
                % (esc(sid), k, esc(title), "".join(fields)))

    out = []
    for it in [i for i in items if not fsecs and True]:
        out.append(item_card(it))
    if fsecs:
        for k, f in enumerate(fsecs, 1):
            out.append(section_card(f, k))
            for it in items:
                if it.get("section") == f["id"]:
                    out.append(item_card(it))
    return "\n".join(out), item_by_id


# ---------------------------------------------------------------------------
# Avisos de conteúdo (nunca erros): o contrato de DELIVERY-DOC.md, conferido pelo build
# ---------------------------------------------------------------------------

_BLOCK_TAG = re.compile(r"(</?(?:p|li|td|th|dt|dd|tr|h[1-6]|figcaption|pre|div|ul|ol|table|thead|tbody|"
                        r"blockquote|section|figure)\b[^>]*>)", re.I)
_SKIP_OPEN = re.compile(r"^<(h[1-6]|figcaption|pre)\b", re.I)
_SKIP_CLOSE = re.compile(r"^</(h[1-6]|figcaption|pre)\b", re.I)
_LINK_HTML = re.compile(r"<a\b[^>]*href=\"#([^\"]*)\"[^>]*>(.*?)</a>", re.S | re.I)
_MENTION = re.compile(r"\b(Pergunta|Seção|Figura)\s+(\d+)\b")
REQUIRED_TERMS = (("carimbo", "Carimbo de data/hora"), ("despublicad", "Despublicado"),
                  ("planilha", "Link para as Planilhas"))


def _text_of(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def _blocks_of(inner):
    """Divide o HTML de uma seção em blocos de texto corrido: (texto fora de links, rótulos dos links, alvos).
    Títulos, legendas e código não entram (o título de uma tela pode dizer «Pergunta 3» sem ser citação)."""
    out, skip, chunk = [], 0, []
    for tok in _BLOCK_TAG.split(inner):
        if _BLOCK_TAG.fullmatch(tok):
            if chunk:
                out.append("".join(chunk))
                chunk = []
            if _SKIP_OPEN.match(tok):
                skip += 1
            elif _SKIP_CLOSE.match(tok) and skip:
                skip -= 1
        elif not skip:
            chunk.append(tok)
    if chunk:
        out.append("".join(chunk))
    res = []
    for frag in out:
        frag = re.sub(r"<kbd\b.*?</kbd>|<code\b.*?</code>", "", frag, flags=re.S | re.I)
        links = [(m.group(1), _text_of(m.group(2))) for m in _LINK_HTML.finditer(frag)]
        free = _text_of(_LINK_HTML.sub(" ", frag))
        res.append((free, links))
    return res


def content_warnings(d, written, titles, issues):
    """Avisos de conteúdo mínimo por seção e de citação sem link. Heurística conservadora:
    prefere calar a gerar ruído (ver DELIVERY-DOC.md, seção 7)."""
    meta = d["meta"]
    uv = meta["ux_verdict"]
    lk = meta.get("links") or {}

    def body(sid):
        return written.get(sid, ("", ""))[0]

    def inner(sid):
        return written.get(sid, ("", ""))[1]

    vg = body("visao-geral")
    if "<table" not in inner("visao-geral"):
        issues.warn("Visão geral sem a tabela «Em resumo» (objetivo, público, prazo, tempo de preenchimento, "
                    "idioma, dado pessoal, conta Google).")
    if (uv.get("not_verified") or []) and not re.search(r"^>\s*\[!IMPORTANT\]", vg, re.M | re.I):
        issues.warn("Há itens em meta.ux_verdict.not_verified, mas a Visão geral não tem a caixa "
                    "«O que ainda não foi conferido» (> [!IMPORTANT]).")
    ac = body("acesso-e-links")
    if lk.get("respondent_url") and lk["respondent_url"] not in ac:
        issues.warn("Acesso e links não traz o link do respondente por extenso (use {{links.respondent_url}}).")
    if lk.get("edit_url") and lk["edit_url"] not in ac:
        issues.warn("Acesso e links não traz o link de edição por extenso (use {{links.edit_url}}).")
    if "despublicad" in str(meta.get("form_status") or "").lower():
        if not re.search(r"^>\s*\[!WARNING\]", ac, re.M | re.I):
            issues.warn("Formulário despublicado: Acesso e links precisa da caixa > [!WARNING] com o link "
                        "provisório e os passos para publicar.")
        if not re.search(r"^>\s*\[!IMPORTANT\]\s*\n?>?\s*\**«?Restrito", ac, re.M | re.I):
            issues.warn("Formulário despublicado: o link de edição deve ficar em uma caixa "
                        "> [!IMPORTANT] que começa com «Restrito».")
    pp = body("passo-a-passo-respondente")
    if d.get("captures") and "::: screens-pair" not in pp:
        issues.warn("O passo a passo tem capturas registradas, mas nenhum par ::: screens-pair "
                    "(computador + celular de cada tela).")
    branching = any(isinstance(o, dict) and o.get("goes_to") not in (None, "next")
                    for it in d["items"] for o in (it.get("options") or []))
    if branching and "<table" not in inner("passo-a-passo-respondente"):
        issues.warn("O formulário tem ramificação, mas o passo a passo não traz a tabela «mapa de caminhos».")
    if "<table" not in inner("editar-e-manter"):
        issues.warn("Editar e manter sem a tabela «Quero… / Faça… / Cuidado».")
    if any(it.get("personal_data") for it in d["items"]) and "<table" not in inner("privacidade"):
        issues.warn("Há perguntas com dado pessoal, mas Privacidade não traz a tabela «Dado → pergunta → para que serve».")
    n_faq = len(re.findall(r"^##\s+\S", body("perguntas-frequentes"), re.M))
    if not 6 <= n_faq <= 12:
        issues.warn("Perguntas frequentes tem %d perguntas (título ##); o contrato pede de 6 a 12." % n_faq)
    terms_txt = " ".join((g["slug"] + " " + g["term"]).lower() for g in d["glossary"])
    for key, name in REQUIRED_TERMS:
        if key not in terms_txt:
            issues.warn("Glossário sem o termo mínimo «%s»." % name)

    # citação sem link
    glossary = [(g["slug"], g["term"]) for g in d["glossary"]]
    for sid, (_, html_inner) in written.items():
        blocks = _blocks_of(html_inner)
        seen = set()
        for free, links in blocks:
            labels = " ".join(t for _, t in links)
            for m in _MENTION.finditer(free):
                token = "%s %s" % (m.group(1), m.group(2))
                if token in labels or (sid, token) in seen:
                    continue
                seen.add((sid, token))
                issues.warn("«%s» citada sem link na seção %s: aponte para a ficha ou a figura." % (token, sid))
        linked = set(t for _, links in blocks for t, _ in links)
        for slug, term in glossary:
            if "termo-" + slug in linked:
                continue
            pat = re.compile(r"(?<![\w])%s(?![\w])" % re.escape(term))
            if any(pat.search(re.sub(r"«[^»]*»", "", free)) for free, _ in blocks):
                issues.warn("O termo «%s» aparece na seção %s sem link para o glossário (#termo-%s)."
                            % (term, sid, slug))



def build_html(d, base_dir, template_path, css_path, generated_at, issues):
    """Monta o HTML final. Devolve (html, ctx) ou (None, ctx) se faltar entrada fundamental."""
    meta = d["meta"]
    captures = {}
    for c in d.get("captures", []):
        key = posixpath.normpath(str(c["file"]).replace("\\", "/"))
        captures[key] = c
    ctx = Ctx(base_dir, meta, captures, issues)

    try:
        with open(template_path, "r", encoding="utf-8") as fh:
            tpl = fh.read()
    except (OSError, IOError) as exc:
        issues.error("Template ilegível (%s): %s" % (template_path, exc))
        return None, ctx
    tpl = re.sub(r"<!--.*?-->", "", tpl, flags=re.S)
    unknown = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", tpl)) - KNOWN_PLACEHOLDERS)
    if unknown:
        issues.error("Placeholder(s) desconhecido(s) no template: %s." % ", ".join(unknown))
    tpl_dir = os.path.dirname(os.path.abspath(template_path))

    css_text, css_src = None, None
    if css_path:
        css_src = css_path
    else:
        m = re.search(r"<link\b[^>]*rel=[\"']stylesheet[\"'][^>]*>", tpl, re.I)
        if m:
            h = re.search(r"href=[\"']([^\"']+)[\"']", m.group(0))
            if h and not re.match(r"^[a-z]+://", h.group(1)):
                css_src = os.path.join(tpl_dir, h.group(1))
        if css_src is None:
            cand = os.path.join(tpl_dir, "styles.css")
            css_src = cand if os.path.isfile(cand) else None
    if css_src:
        try:
            with open(css_src, "r", encoding="utf-8") as fh:
                css_text = fh.read()
        except (OSError, IOError) as exc:
            issues.error("CSS ilegível (%s): %s" % (css_src, exc))
    else:
        issues.warn("Nenhum CSS encontrado: o documento sairá sem estilo.")
    if css_text and re.search(r"url\(\s*[\"']?https?:", css_text):
        issues.warn("O CSS referencia recurso externo (http): o PDF depende de rede.")

    user_sections = {s["id"]: s for s in d["sections"]}
    titles = {}
    for sid in BODY_ORDER:
        s = user_sections.get(sid, {})
        titles[sid] = (s.get("title") or DEFAULT_TITLES[sid]).strip()

    rendered = []
    written = {}   # id -> (Markdown expandido, HTML convertido), só das seções escritas à mão
    for sid in BODY_ORDER:
        s = user_sections.get(sid, {})
        conv = Converter(ctx, sid, titles[sid])
        body_md = expand_tokens(s.get("body_md", ""), meta, issues, "a seção %s" % sid)
        inner = conv.convert(body_md)
        if sid not in GENERATED and sid != "glossario":
            written[sid] = (body_md, inner)
        if sid not in GENERATED and not body_md.strip():
            issues.error("Seção vazia: %s." % sid)
        if sid == "referencia":
            cards, _ = render_item_cards(ctx, d, issues, conv)
            intro = '<div class="ref-intro">%s</div>' % inner if inner else ""
            inner = intro + "\n" + cards
        elif sid == "glossario":
            terms = []
            for g in d["glossary"]:
                conv.owner = "termo-" + g["slug"]
                terms.append('<dt id="termo-%s">%s</dt><dd>%s<!--cited-p:termo-%s--></dd>'
                             % (esc(g["slug"]), esc(g["term"]), conv.inline(g["definition"]), esc(g["slug"])))
            conv.owner = None
            inner = (('<div class="ref-intro">%s</div>' % inner) if inner else "") + \
                '<dl class="glossary">%s</dl>' % "".join(terms)
        elif sid == "historico":
            rows = []
            for h in d["history"]:
                rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    esc(h["version"]), esc(h["date"]), esc(h["change"]),
                    esc(h.get("requested_by", "")), esc(h.get("approved_by", ""))))
            table = ('<table class="data"><thead><tr><th scope="col">Versão</th><th scope="col">Data</th>'
                     '<th scope="col">O que mudou</th><th scope="col">Quem pediu</th>'
                     '<th scope="col">Quem aprovou</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows))
            uv = meta["ux_verdict"]
            cls = VERDICTS[uv["verdict"]]
            ctx.heading_ids.add("historico-resultado-ux")
            ctx.toc.append(("historico", 2, "Resultado da revisão de experiência de uso",
                            "historico-resultado-ux"))
            ux = ['<h3 id="historico-resultado-ux">Resultado da revisão de experiência de uso</h3>',
                  '<p><span class="verdict %s">%s</span></p>' % (cls, esc(uv["verdict"]))]
            facts = []
            if uv.get("reviewed_at"):
                facts.append("Data da revisão: %s." % esc(uv["reviewed_at"]))
            if uv.get("reviewer"):
                facts.append("Quem revisou: %s." % esc(uv["reviewer"]))
            if meta.get("approved_by"):
                facts.append("Aprovado por %s%s." % (esc(meta["approved_by"]),
                                                      (" em %s" % esc(meta["approved_at"])) if meta.get("approved_at") else ""))
            if facts:
                ux.append("<p>%s</p>" % " ".join(facts))
            def _lst(items):
                return "<ul>%s</ul>" % "".join("<li>%s</li>" % conv.inline(c) for c in items)
            cav = uv.get("accepted_caveats") or []
            pend = uv.get("pending_decisions") or []
            if cav:
                ux.append("<p><strong>Ressalvas aceitas pelo dono</strong></p>")
                ux.append(_lst(cav))
            if pend:
                ux.append("<p><strong>%s</strong></p>" % ("Decisões pendentes do dono" if cav
                                                         else "Ressalvas e decisões pendentes do dono"))
                ux.append(_lst(pend))
            if not cav and not pend:
                ux.append("<p><strong>Ressalvas aceitas pelo dono</strong></p>")
                ux.append("<p>Nenhuma ressalva registrada.</p>")
            nv = uv.get("not_verified") or []
            ux.append("<p><strong>O que ainda não foi conferido</strong></p>")
            ux.append(_lst(nv) if nv else "<p>Nenhum item registrado como não verificado.</p>")
            inner = (('<div class="ref-intro">%s</div>' % inner) if inner else "") + table + "\n".join(ux)
        cls_extra = " faq" if sid == "perguntas-frequentes" else ""
        rendered.append('<section class="doc-section%s" id="%s"><h2>%s</h2>\n%s\n'
                        '<p class="backlink"><a href="#sumario">\u2191 voltar ao sumário</a></p></section>'
                        % (cls_extra, sid, esc(titles[sid]), inner))
    body = "\n".join(rendered)

    # ---- citações de figuras
    nums = {f["id"]: f["n"] for f in ctx.figures}
    cited = set()
    for target, label, sec in ctx.fig_refs:
        if target not in nums:
            continue  # âncora inexistente: pego pela validação de links
        cited.add(target)
        m = re.match(r"^Figura\s+(\d+)$", label)
        if m and int(m.group(1)) != nums[target]:
            issues.error("Citação «%s» aponta para %s, que é a Figura %d (seção %s)."
                         % (label, target, nums[target], sec))
    for f in ctx.figures:
        if f["id"] not in cited:
            issues.error("Figura %d (%s) nunca é citada no texto por link [Figura %d](#%s)."
                         % (f["n"], f["file"], f["n"], f["id"]))
    for rel in captures:
        if rel not in ctx.used_captures:
            issues.warn("Captura registrada mas não usada no corpo: %s." % rel)

    # ---- backlinks «Citada em»
    by_target = {}
    for c in ctx.cites:
        by_target.setdefault(c["target"], []).append(c)

    def cited_html(m):
        mode, target = m.group(1), m.group(2)
        seen, links = set(), []
        for c in by_target.get(target, []):
            label = c["section_title"] + (" \u203a %s" % c["heading"] if c["heading"] else "")
            if label in seen:
                continue
            seen.add(label)
            links.append('<a class="xref" href="#%s">%s</a>' % (c["id"], esc(label)))
        if not links:
            return ""
        word = "Citado em" if target.startswith("termo-") else "Citada em"
        if mode == "dl":
            return "<dt>%s</dt><dd>%s</dd>" % (word, "; ".join(links))
        return '<p class="cited-by">%s: %s</p>' % (word, "; ".join(links))

    body = re.sub(r"<!--cited-(dl|p):([\w-]+)-->", cited_html, body)
    body_cited = set(c["target"] for c in ctx.cites if c["section"] != "referencia")
    for it in d["items"]:
        if "item-" + it["id"] not in body_cited:
            issues.warn("Item sem nenhuma citação no corpo: %s (%s)." % (it["id"], it["title"]))
    for g in d["glossary"]:
        if "termo-" + g["slug"] not in body_cited:
            issues.warn("Termo do glossário nunca citado no corpo: %s." % g["slug"])

    content_warnings(d, written, titles, issues)

    # ---- sumário
    li = []
    by_sec = {}
    for sec, lvl, text, hid in ctx.toc:
        by_sec.setdefault(sec, []).append((lvl, text, hid))
    for sid in BODY_ORDER:
        li.append('<li class="l1"><a href="#%s">%s</a></li>' % (sid, esc(titles[sid])))
        for lvl, text, hid in by_sec.get(sid, []):
            li.append('<li class="l%d"><a href="#%s">%s</a></li>' % (lvl, esc(hid), esc(text)))
    if ctx.figures:
        li.append('<li class="l1"><a href="#%s">Lista de figuras</a></li>' % ctx.figures[0]["id"])
        for f in ctx.figures:
            li.append('<li class="l2"><a href="#%s">Figura %d \u2014 %s</a></li>'
                      % (f["id"], f["n"], esc(f["caption"])))
    toc = '<ol class="toc-list">\n%s\n</ol>' % "\n".join(li)

    # ---- placeholders do template
    uv = meta["ux_verdict"]
    lk = meta.get("links") or {}
    conf = meta.get("confidentiality") or "Uso interno"
    note = conf + "."
    if meta.get("form_status"):
        note += " Estado do formulário: %s." % meta["form_status"]
    values = {
        "inline_css": css_text or "",
        "form_title_css": css_string(meta["form_title"]),
        "form_title": esc(meta["form_title"]),
        "cover_subtitle": esc(meta.get("subtitle") or "Manual de uso, referência e histórico do formulário"),
        "version": esc(meta["version"]), "date": esc(meta["date"]), "owner": esc(meta["owner"]),
        "ux_verdict": esc(uv["verdict"].capitalize()), "ux_verdict_class": VERDICTS[uv["verdict"]],
        "cover_note": esc(note), "toc": toc, "sections": body,
        "colophon": esc("%s \u2014 versão %s \u2014 %s \u2014 %s" % (meta["form_title"], meta["version"],
                                                              meta["date"], conf)),
        "generated_at": esc(generated_at),
        "respondent_url": esc(lk.get("respondent_url") or ""), "edit_url": esc(lk.get("edit_url") or ""),
        "responses_url": esc(lk.get("responses_url") or ""), "sheet_url": esc(lk.get("sheet_url") or ""),
    }
    out = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values.get(m.group(1), m.group(0)), tpl)
    if css_text and "{{inline_css}}" not in tpl:
        link = re.search(r"<link\b[^>]*rel=[\"']stylesheet[\"'][^>]*>", out, re.I)
        if link:
            out = out.replace(link.group(0), "<style>\n" + css_text + "\n</style>", 1)
    return out, ctx


# ---------------------------------------------------------------------------
# Validação do HTML final
# ---------------------------------------------------------------------------

class _Collector(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.ids = []
        self.hrefs = []
        self.text = []
        self.fig_stack = []
        self.fig_problems = []
        self.external = []
        self._skip = 0
        self._in_cap = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a and a["id"] is not None:
            self.ids.append(a["id"])
        if tag == "a" and (a.get("href") or "").startswith("#"):
            self.hrefs.append(a["href"][1:])
        if tag in ("style", "script"):
            self._skip += 1
        if tag in ("img", "script", "link", "iframe", "source"):
            ref = a.get("src") or (a.get("href") if tag == "link" else None) or ""
            if re.match(r"^https?:", ref, re.I):
                self.external.append(ref)
        if tag == "figure" and "screenshot" in (a.get("class") or "").split():
            self.fig_stack.append({"id": a.get("id"), "cap": "", "img": False})
        if tag == "img" and self.fig_stack:
            self.fig_stack[-1]["img"] = True
        if tag == "figcaption":
            self._in_cap = True

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip:
            self._skip -= 1
        if tag in ("td", "th", "li", "p", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "tr") and not self._skip:
            self.text.append(" ")  # separa células e blocos: evita «a@x.com» + «12/03» virar «a@x.com12/03»
        if tag == "figcaption":
            self._in_cap = False
        if tag == "figure" and self.fig_stack:
            f = self.fig_stack.pop()
            if not f["cap"].strip():
                self.fig_problems.append("Figura sem legenda (%s)." % (f["id"] or "sem id"))
            if not f["img"]:
                self.fig_problems.append("Figura sem imagem (%s)." % (f["id"] or "sem id"))

    def handle_data(self, data):
        if self._skip:
            return
        self.text.append(data)
        if self._in_cap and self.fig_stack:
            self.fig_stack[-1]["cap"] += data


def validate_html(doc, issues):
    col = _Collector()
    col.feed(doc)
    col.close()
    seen, dup = set(), []
    for i in col.ids:
        if i in seen and i not in dup:
            dup.append(i)
        seen.add(i)
    for i in dup:
        issues.error("Id duplicado: %s." % i)
    for h in sorted(set(col.hrefs) - seen):
        issues.error("Link interno quebrado: href=\"#%s\" não tem id correspondente." % h)
    for rid in RESERVED_IDS:
        if rid not in seen:
            issues.error("Id reservado ausente no documento: %s." % rid)
    for p in col.fig_problems:
        issues.error(p)
    for ext in col.external[:5]:
        issues.warn("Recurso externo no HTML (o PDF dependeria de rede): %s." % ext[:80])
    for m in re.finditer(r"\{\{\s*[\w.]+\s*\}\}", "".join(col.text)):
        issues.error("Placeholder não resolvido no texto: %s." % m.group(0))
        break
    text = "".join(col.text)
    for pat, name in JARGON:
        found = re.findall(pat, text, re.I if name not in ("YAML", "JSON", "MCP") else 0)
        if found:
            issues.warn("Jargão de agente no texto (%s, %d ocorrência(s)): reescreva para o leitor humano."
                        % (name, len(found)))
    mails = set()
    for m in EMAIL_RE.finditer(text):
        dom = m.group(1).lower()
        if not any(dom == s or dom.endswith("." + s) for s in SAFE_MAIL_DOMAINS):
            mails.add(m.group(0))
    for mail in sorted(mails):
        local = mail.split("@")[0]
        issues.warn("Possível e-mail real no texto (%s***@%s): confira a privacidade."
                    % (local[:2], mail.split("@")[1]))
    return col


# ---------------------------------------------------------------------------
# Renderização do PDF
# ---------------------------------------------------------------------------

def find_sister_script(environ=None):
    """Acha o html_to_pdf.py da skill generate-pdf-report. Devolve (caminho|None, erro|None)."""
    environ = os.environ if environ is None else environ
    ov = environ.get(SISTER_ENV)
    if ov:
        if not os.path.isfile(ov):
            return None, "%s aponta para algo inexistente: %s" % (SISTER_ENV, ov)
        return ov, None
    pats = ["../generate-pdf-report/scripts/html_to_pdf.py", "../generate-pdf-report/*/scripts/html_to_pdf.py",
            "../../generate-pdf-report/*/scripts/html_to_pdf.py",
            "../../generate-pdf-report/scripts/html_to_pdf.py"]
    for p in pats:
        hits = sorted(glob.glob(os.path.normpath(os.path.join(SKILL_DIR, p))))
        if hits:
            return hits[0], None
    return None, None


def inspect_pdf(path):
    """Devolve dict(valid, pages, links). Conta também dentro de streams comprimidos."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except (OSError, IOError):
        return {"valid": False, "pages": 0, "links": 0}
    if not data.startswith(b"%PDF"):
        return {"valid": False, "pages": 0, "links": 0}
    blobs = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        chunk = m.group(1)
        if len(chunk) > 30 * 1024 * 1024:
            continue
        try:
            blobs.append(zlib.decompress(chunk))
        except zlib.error:
            continue
    pages = sum(len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", b)) for b in blobs)
    links = sum(len(re.findall(rb"/Subtype\s*/Link(?![a-zA-Z])", b)) for b in blobs)
    return {"valid": True, "pages": pages, "links": links}


def _run(cmd, timeout):
    try:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "tempo esgotado (%ds)" % timeout
    except OSError as exc:
        return None, str(exc)
    tail = (cp.stdout + b"\n" + cp.stderr).decode("utf-8", errors="replace")
    tail = "\n".join(l for l in tail.splitlines() if "task_policy" not in l and l.strip())[-500:]
    return cp.returncode, tail


def render_pdf(html_path, pdf_path, environ=None, timeout=120):
    """Renderiza. Devolve (renderer|None, mensagens de falha)."""
    problems = []
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    parent = os.path.dirname(os.path.abspath(pdf_path))
    if not os.path.isdir(parent):
        os.makedirs(parent)
    sister, err = find_sister_script(environ)
    if err:
        return None, [err], True
    if sister:
        rc, tail = _run([sys.executable, sister, html_path, pdf_path], timeout)
        if rc == 0 and inspect_pdf(pdf_path)["valid"]:
            return "generate-pdf-report", problems, False
        problems.append("html_to_pdf.py da skill irmã falhou (%s): %s" % (rc, tail))
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    else:
        problems.append("html_to_pdf.py da skill generate-pdf-report não encontrado; usando o Chromium detectado.")
    sys.path.insert(0, HERE)
    try:
        import detect_browser
        payload = detect_browser.detect(detect_browser.SystemEnv())[1]
    finally:
        sys.path.pop(0)
    pdata = payload.get("data") or {}
    cands = []
    if str(pdata.get("source", "")).startswith("env:") and (pdata.get("default") or {}).get("executable"):
        cands.append(pdata["default"])  # GFORMS_BROWSER_PATH explícito vale primeiro
    order = ["chrome", "msedge", "chromium", "chrome-beta", "msedge-beta", "vivaldi", "brave"]
    inst = [e for e in pdata.get("installed", []) if e.get("chromium") and e.get("executable")]
    inst.sort(key=lambda e: order.index(e.get("id")) if e.get("id") in order else 50)
    cands.extend(inst)
    seen, uniq = set(), []
    for e in cands:
        if e["executable"] not in seen:
            seen.add(e["executable"])
            uniq.append(e)
    if not uniq:
        problems.append("Nenhum Chromium encontrado (detect_browser: %s)." % payload.get("status"))
        return None, problems, False
    # Observado no macOS: o Brave headless fica pendurado em --print-to-pdf; por isso Chrome/Edge vêm antes.
    for e in uniq[:3]:
        exe = e["executable"]
        tmp = tempfile.mkdtemp(prefix="gforms-pdf-")
        cmd = [exe, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--user-data-dir=" + tmp,
               "--print-to-pdf=" + os.path.abspath(pdf_path)]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")
            problems.append("Executando como root: o Chromium foi chamado com --no-sandbox (esperado em contêiner).")
        cmd.append(pathlib.Path(os.path.abspath(html_path)).as_uri())
        rc, tail = _run(cmd, 60 if e is not uniq[0] else timeout)
        shutil.rmtree(tmp, ignore_errors=True)
        if inspect_pdf(pdf_path)["valid"]:
            return "chromium:" + e.get("name", os.path.basename(exe)), problems, False
        problems.append("%s não gerou o PDF (exit %s): %s" % (e.get("name", exe), rc, tail))
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    return None, problems, False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def result(ok, status, data, problems, next_steps):
    return {"ok": ok, "status": status, "data": data, "problems": problems, "next_steps": next_steps}


def emit(payload):
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        sys.stdout.write(out + "\n")
    except UnicodeEncodeError:
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        emit(result(False, "usage_error", {}, ["Uso inválido: %s" % message], [self.format_usage().strip()]))
        sys.exit(2)


def finish(status, ok, code, data, issues, next_steps):
    problems = list(issues.errors) + ["Aviso: " + w for w in issues.warnings]
    data["errors"] = list(issues.errors)
    data["warnings"] = list(issues.warnings)
    emit(result(ok, status, data, problems, next_steps))
    return code


def main(argv=None, env=None):
    ap = _Parser(description="Monta, valida e renderiza o documento de entrega do formulário.")
    ap.add_argument("delivery", help="caminho do delivery.json")
    ap.add_argument("--out", help="PDF de saída")
    ap.add_argument("--html-only", action="store_true", help="só gera o HTML")
    ap.add_argument("--html", help="caminho do HTML (padrão: ao lado do PDF ou do delivery.json)")
    ap.add_argument("--template", help="template.html (padrão: templates/delivery-doc/template.html da skill)")
    ap.add_argument("--css", help="styles.css (padrão: o referenciado pelo template ou styles.css ao lado)")
    ap.add_argument("--strict", action="store_true", help="avisos viram erros")
    ap.add_argument("--generated-at", help="carimbo de data (padrão: agora)")
    args = ap.parse_args(argv)
    environ = (env if isinstance(env, dict) else None)

    if not args.out and not args.html_only:
        emit(result(False, "usage_error", {}, ["Informe --out arquivo.pdf ou --html-only."],
                    ["Exemplo: build_delivery_doc.py delivery.json --out entrega/formulario-v1.pdf"]))
        return 2
    if args.out and args.html_only:
        emit(result(False, "usage_error", {}, ["--out e --html-only são excludentes."], []))
        return 2
    dpath = os.path.abspath(args.delivery)
    if not os.path.isfile(dpath):
        emit(result(False, "usage_error", {"delivery": dpath}, ["delivery.json não encontrado: %s" % dpath],
                    ["Confira o caminho."]))
        return 2
    issues = Issues()
    data = {"delivery": dpath}
    try:
        with open(dpath, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except (ValueError, OSError) as exc:
        issues.error("delivery.json ilegível ou com JSON inválido: %s" % exc)
        return finish("invalid", False, 1, data, issues, ["Corrija o JSON e rode de novo."])

    if not validate_schema(d, issues):
        return finish("invalid", False, 1, data, issues,
                      ["Corrija o delivery.json (nunca o HTML gerado) e rode de novo."])

    now = args.generated_at or datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    template = os.path.abspath(args.template or DEFAULT_TEMPLATE)
    doc, ctx = build_html(d, os.path.dirname(dpath), template, args.css, now, issues)
    if doc is not None:
        validate_html(doc, issues)
    data["figures"] = len(ctx.figures)
    data["items"] = len(d["items"])
    if args.strict and issues.warnings:
        for w in issues.warnings:
            issues.error("(--strict) " + w)
        issues.warnings = []
    if issues.errors or doc is None:
        return finish("invalid", False, 1, data, issues,
                      ["Corrija os erros no delivery.json e gere de novo; nada foi gravado."])

    if args.html:
        html_path = os.path.abspath(args.html)
    elif args.out:
        html_path = os.path.splitext(os.path.abspath(args.out))[0] + ".html"
    else:
        html_path = os.path.splitext(dpath)[0] + ".html"
    parent = os.path.dirname(html_path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    data["html"] = html_path
    internal = len(re.findall(r'<a [^>]*href="#', doc))
    data["internal_links"] = internal
    if args.html_only:
        return finish("html_only", True, 0, data, issues,
                      ["Abra o HTML no navegador para conferir; para o PDF, rode com --out arquivo.pdf."])

    pdf_path = os.path.abspath(args.out)
    renderer, probs, usage = render_pdf(html_path, pdf_path, environ)
    for p in probs:
        if renderer is None:
            issues.error(p)
        else:
            issues.warn(p)
    if usage:
        return finish("usage_error", False, 2, data, issues, ["Corrija a variável %s." % SISTER_ENV])
    if renderer is None:
        return finish("render_failed", False, 1, data, issues,
                      ["O HTML foi gravado em %s. Instale/aponte um Chrome (CHROME_PATH ou "
                       "GFORMS_BROWSER_PATH) e rode de novo." % html_path])
    info = inspect_pdf(pdf_path)
    data.update({"pdf": pdf_path, "renderer": renderer, "pages": info["pages"],
                 "link_annotations": info["links"], "size_kb": round(os.path.getsize(pdf_path) / 1024.0)})
    if info["links"] < internal:
        issues.warn("O PDF tem %d anotações de link, menos que os %d links internos esperados: "
                    "confira se os links clicam." % (info["links"], internal))
    return finish("built", True, 0, data, issues,
                  ["Abra o PDF e execute o checklist de QA (DELIVERY-DOC.md, seção 8)."])


if __name__ == "__main__":
    sys.exit(main())
