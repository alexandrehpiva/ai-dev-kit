#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte um FORM-SPEC aprovado no literal JS `var SPEC = {...}` do templates/build-form.gs.

Uso:
    python3 <pasta-da-skill>/scripts/spec_to_gs.py SPEC.json|SPEC.yaml --out build-form-gerado.gs [--template T.gs] [--force]
    python3 <pasta-da-skill>/scripts/spec_to_gs.py SPEC.json|SPEC.yaml --literal
    (Windows: py -3 <pasta-da-skill>\\scripts\\spec_to_gs.py ...)
    <pasta-da-skill> = a pasta onde está o SKILL.md desta skill.

Fluxo: carrega o spec (mesmo carregador do validate_spec.py), roda a validação `--for-build`
(só segue se ok: status approved, sem erros, sem pending_owner) e converte para o literal JS
no formato que o build-form.gs espera (mesmos nomes de campo e valores do spec, sem convenção
própria). Isso elimina a transcrição manual do spec.

Saídas (exatamente uma das duas):
    --out ARQ   grava o build-form.gs COMPLETO com o SPEC preenchido: só o bloco entre os
                marcadores `// >>> SPEC:BEGIN` e `// <<< SPEC:END` do template é substituído.
                Recusa sobrescrever arquivo existente sem --force. JSON do resultado em stdout.
    --literal   imprime só `var SPEC = {...};` em stdout (para colar no lugar do bloco).
                O JSON do resultado vai para stderr; em caso de recusa, stdout fica vazio.

JSON do resultado: {"ok","status","data","problems","next_steps"}. data.pending_ui lista o
que o Apps Script NÃO aplica (o agente conclui pela interface); data.warnings, as ressalvas.
Status: generated | literal | invalid | pending_owner | template_issue | exists | usage_error.
Códigos de saída: 0 ok; 1 problema acionável (spec recusado, template sem marcadores, arquivo
já existe); 2 erro de uso.

Strings: as quebras de linha finais são removidas (sobra dos blocos YAML `>`/`|`).
Strings JS: aspas simples, escapes para \\ ' quebras de linha, controles, U+2028/U+2029,
substitutos soltos, e `<` antes de `/` ou `!` (evita `</script>` e `<!--`) vira \\x3C.
Somente leitura do spec e do template. Requer Python 3.8+ e apenas a biblioteca padrão
(PyYAML opcional, para .yaml). Se o literal não puder ser gerado (NaN, infinito, chave
não textual), recusa com status invalid.
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import validate_spec as vs  # noqa: E402

BEGIN = "// >>> SPEC:BEGIN"
END = "// <<< SPEC:END"
DEFAULT_TEMPLATE = os.path.join(os.path.dirname(HERE), "templates", "build-form.gs")
IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
INLINE_MAX = 96


class LiteralError(ValueError):
    pass


# --------------------------------------------------------------------------------------
# Literal JS
# --------------------------------------------------------------------------------------
def js_string(text):
    """String JS entre aspas simples, segura para colar em HTML/Apps Script."""
    out = []
    n = len(text)
    for i, ch in enumerate(text):
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == "'":
            out.append("\\'")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "<" and i + 1 < n and text[i + 1] in "/!":
            out.append("\\x3C")
        elif o < 0x20 or o == 0x7F:
            out.append("\\x%02X" % o)
        elif o in (0x2028, 0x2029) or 0xD800 <= o <= 0xDFFF or o == 0xFEFF:
            out.append("\\u%04X" % o)
        elif unicodedata.category(ch) in ("Cc", "Cf") and o < 0x10000:
            out.append("\\u%04X" % o)
        else:
            out.append(ch)
    return "'" + "".join(out) + "'"


def js_key(key):
    if not isinstance(key, str):
        raise LiteralError("chave não textual: %r" % (key,))
    if key == "__proto__":
        return "['__proto__']"  # em literal, `__proto__:` trocaria o protótipo
    return key if IDENT.match(key) else js_string(key)


def _scalar(node):
    if node is None:
        return "null"
    if node is True:
        return "true"
    if node is False:
        return "false"
    if isinstance(node, int):
        return str(node)
    if isinstance(node, float):
        if math.isnan(node) or math.isinf(node):
            raise LiteralError("número não finito no spec")
        return repr(node)
    if isinstance(node, str):
        return js_string(node)
    raise LiteralError("tipo sem equivalente JS: %s" % type(node).__name__)


def to_js(node, level=0, indent="  "):
    """Objeto/lista -> JS legível; coleções curtas só com escalares ficam numa linha."""
    if isinstance(node, dict):
        if not node:
            return "{}"
        items = [(js_key(k), v) for k, v in node.items()]
        if all(not isinstance(v, (dict, list)) for _, v in items):
            inline = "{ " + ", ".join("%s: %s" % (k, _scalar(v)) for k, v in items) + " }"
            if len(inline) <= INLINE_MAX:
                return inline
        pad = indent * (level + 1)
        body = ",\n".join("%s%s: %s" % (pad, k, to_js(v, level + 1, indent)) for k, v in items)
        return "{\n%s\n%s}" % (body, indent * level)
    if isinstance(node, list):
        if not node:
            return "[]"
        if all(not isinstance(v, (dict, list)) for v in node):
            inline = "[" + ", ".join(_scalar(v) for v in node) + "]"
            if len(inline) <= INLINE_MAX:
                return inline
        flat = [to_js(v, level + 1, indent) for v in node]
        if all("\n" not in f for f in flat) and all(isinstance(v, dict) for v in node):
            inline = "[ " + ", ".join(flat) + " ]"
            if len(inline) <= INLINE_MAX:
                return inline
        pad = indent * (level + 1)
        return "[\n%s\n%s]" % (",\n".join(pad + f for f in flat), indent * level)
    return _scalar(node)


def normalize(node):
    """Tira as quebras de linha finais das strings (artefato dos blocos YAML `>` e `|`)."""
    if isinstance(node, dict):
        return {k: normalize(v) for k, v in node.items()}
    if isinstance(node, list):
        return [normalize(v) for v in node]
    if isinstance(node, str):
        return node.rstrip("\n")
    return node


def spec_literal(spec):
    """`var SPEC = {...};` (sem banner). Strings perdem as quebras de linha finais (ver normalize)."""
    return "var SPEC = %s;" % to_js(normalize(spec))


def spec_digest(spec):
    canon = json.dumps(spec, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("ascii")).hexdigest()


def safe_name(path):
    return re.sub(r"[^\w.\- ]", "_", os.path.basename(path))[:80]


def build_block(spec, source_path):
    """Texto que fica ENTRE os marcadores (banner + literal)."""
    banner = "// Gerado por scripts/spec_to_gs.py a partir de %s (spec sha256 %s). Não edite à mão." % (
        safe_name(source_path), spec_digest(spec)[:16])
    return banner + "\n" + spec_literal(spec)


# --------------------------------------------------------------------------------------
# Template
# --------------------------------------------------------------------------------------
def render_gs(template_text, block):
    """Substitui o bloco entre os marcadores; devolve (texto, None) ou (None, mensagem)."""
    lines = template_text.split("\n")
    begins = [i for i, l in enumerate(lines) if l.strip().startswith(BEGIN)]
    ends = [i for i, l in enumerate(lines) if l.strip().startswith(END)]
    if len(begins) != 1 or len(ends) != 1:
        return None, "o template precisa ter exatamente 1 marcador `%s` e 1 `%s` (achei %d e %d)" % (
            BEGIN, END, len(begins), len(ends))
    if begins[0] >= ends[0]:
        return None, "o marcador SPEC:BEGIN precisa vir antes do SPEC:END"
    out = lines[:begins[0] + 1] + block.split("\n") + lines[ends[0]:]
    return "\n".join(out), None


# --------------------------------------------------------------------------------------
# O que o Apps Script não faz (espelha o build-form.gs)
# --------------------------------------------------------------------------------------
def pending_ui(spec):
    """Lista de {campo, valor, motivo[, condicao]} que o build-form.gs deixa para a interface.

    Só o que é determinável do spec. Falhas em tempo de execução (por exemplo setValidation
    recusado) aparecem no log do script como PENDENTE_UI e não entram aqui.
    """
    out = []

    def add(campo, valor, motivo, condicao=None):
        row = {"campo": campo, "valor": valor, "motivo": motivo}
        if condicao:
            row["condicao"] = condicao
        out.append(row)

    meta = spec.get("meta") or {}
    st = spec.get("settings") or {}
    quiz = spec.get("quiz") or {}
    th = spec.get("theme") or {}
    rs = spec.get("responses") or {}
    pub = spec.get("publish") or {}

    if meta.get("document_title"):
        add("meta.document_title", meta["document_title"], "nome do arquivo no Drive: renomear pela interface")
    if quiz.get("enabled"):
        add("quiz.release", quiz.get("release") or "immediately", "liberação da nota não existe no FormApp")
        add("quiz.respondent_sees", quiz.get("respondent_sees") or "(padrão do editor)",
            "o que o respondente vê da nota: só pela interface")
    if st.get("send_copy") and st["send_copy"] != "never":
        add("settings.send_copy", st["send_copy"], "cópia da resposta ao respondente: só pela interface")
    if st.get("disable_autosave"):
        add("settings.disable_autosave", True, "salvamento automático: só pela interface")
    close = st.get("close") or {}
    if close.get("at"):
        add("settings.close.at", close["at"], "encerramento por data: só pela interface")
    if close.get("response_limit"):
        add("settings.close.response_limit", close["response_limit"], "limite de respostas: só pela interface")
    for k in ("header_image", "color", "background_color", "font"):
        if th.get(k):
            add("theme." + k, th[k], "tema: só pela interface")

    sections = spec.get("sections") or []
    for sec in sections:
        for it in sec.get("items") or []:
            iid, t = it.get("id"), it.get("type")
            if t in ("rating", "file_upload"):
                add("%s (%s)" % (iid, t), it.get(t) or {}, "item AUSENTE no form: criar pela interface na posição de %s" % iid)
                continue
            if t == "linear_scale" and ((it.get("scale") or {}).get("high") or 5) < 3:
                add(iid + ".scale", it.get("scale"), "FormApp exige high de 3 a 10: criado com 3; ajustar pela interface")
            if t in ("mc_grid", "checkbox_grid") and (it.get("grid") or {}).get("shuffle_rows"):
                add(iid + ".grid.shuffle_rows", True, "embaralhar linhas: só pela interface")
            if t == "image":
                src = (it.get("image") or {}).get("source") or "(vazio)"
                add(iid + ".image.source", src, "imagem: enviar pela interface",
                    "a menos que OPTS.fetchImages = true e a fonte seja http(s)")
            if t == "video" and (it.get("video") or {}).get("caption"):
                add(iid + ".video.caption", it["video"]["caption"], "FormApp não tem legenda de vídeo")
            if quiz.get("enabled"):
                key = it.get("answer_key")
                has_nav = t in ("multiple_choice", "dropdown") and any(
                    isinstance(o, dict) and o.get("go_to") for o in it.get("options") or [])
                if key and has_nav:
                    add(iid + ".answer_key", key, "gabarito junto com navegação: marcar pela interface")
                if key and t in ("short_text", "mc_grid", "checkbox_grid"):
                    add(iid + ".answer_key", key, "FormApp não define gabarito neste tipo")
                fb = it.get("feedback") or {}
                can_fb = t in ("multiple_choice", "checkboxes", "dropdown") and bool(key)
                for k in ("right", "wrong"):
                    if fb.get(k) and not can_fb:
                        add("%s.feedback.%s" % (iid, k), fb[k], "feedback certo/errado só em escolha com gabarito")
                if fb.get("general"):
                    add(iid + ".feedback.general", fb["general"], "feedback geral: só pela interface")

    for i, sec in enumerate(sections):
        a = sec.get("after_section")
        if a and a not in ("next", "submit") and i == len(sections) - 1:
            add(sec.get("id", "?") + ".after_section", a, "última seção: só submit faz sentido")

    if rs.get("sheet") in ("new", "existing"):
        if rs.get("sheet") == "existing" and not re.match(r"^https?://", rs.get("sheet_ref") or ""):
            add("responses.sheet", "existing %s" % (rs.get("sheet_ref") or ""),
                "planilha existente só por URL: vincule pela interface")
        if rs.get("sheet_access"):
            add("responses.sheet_access", rs["sheet_access"], "compartilhamento da planilha: só pela interface")

    cond = "só se OPTS.publish = true (publicação autorizada pelo dono)"
    if pub.get("audience") and not (pub.get("audience") == "specific" and pub.get("responders")):
        add("publish.audience", pub["audience"], 'conferir "Acesso geral" em Publicar', cond)
    if pub.get("notify_responders"):
        add("publish.notify_responders", True, "aviso aos respondentes: só pela interface", cond)
    return out


def warnings_for(spec):
    w = []
    build = spec.get("build") or {}
    if build.get("path") and build["path"] != "apps_script":
        w.append("build.path = %s: este conversor serve o caminho apps_script; confira o plano antes de executar." % build["path"])
    sections = spec.get("sections") or []
    if sections and (sections[0].get("title") or sections[0].get("description")):
        w.append("s1: o build-form.gs usa meta.title/description na 1ª seção; title/description de s1 serão ignorados.")
    return w


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------
def result(ok, status, data, problems, next_steps):
    return {"ok": ok, "status": status, "data": data, "problems": problems, "next_steps": next_steps}


def emit(payload, stream):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        stream.write(text)
    except UnicodeEncodeError:  # console Windows sem UTF-8
        stream.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        emit(result(False, "usage_error", {}, ["Uso inválido: %s" % message], [self.format_usage().strip()]),
             sys.stdout)
        sys.exit(2)


def run(args, yaml_module):
    """Devolve (exit, payload, literal | None)."""
    if bool(args.out) == bool(args.literal):
        return 2, result(False, "usage_error", {}, ["Informe exatamente uma saída: --out ARQUIVO ou --literal."],
                         ["python3 <pasta-da-skill>/scripts/spec_to_gs.py SPEC.json --out build-form-gerado.gs (Windows: py -3)"]), None
    err, data, extra = vs.load_spec(args.spec, yaml_module)
    if err:
        return err[0], err[1], None
    code, vp = vs.build_payload(args.spec, data, extra, True)
    vd = vp["data"]
    validation = {
        "status": vp["status"],
        "counts": vd.get("counts"),
        "warnings": [f for f in vd.get("findings", []) if f["severidade"] == "aviso"],
    }
    if not vp["ok"] or data is None:
        steps = list(vp["next_steps"]) + ["Nada foi gerado: o conversor só aceita spec aprovado e válido (validate_spec.py --for-build)."]
        return 1, result(False, vp["status"], {"file": args.spec, "validation": validation},
                         vp["problems"], steps), None
    try:
        block = build_block(data, args.spec)
    except LiteralError as exc:
        return 1, result(False, "invalid", {"file": args.spec, "validation": validation},
                         ["Não consegui gerar o literal JS: %s" % exc],
                         ["Corrija o valor no spec e rode de novo."]), None
    pend = pending_ui(data)
    base = {
        "file": args.spec,
        "spec_sha256": spec_digest(data),
        "validation": validation,
        "pending_ui": pend,
        "warnings": warnings_for(data),
    }
    steps_pend = ["Conclua pela interface os %d itens de data.pending_ui e cite-os na entrega." % len(pend)] if pend else []

    if args.literal:
        base["literal_chars"] = len(block)
        return 0, result(True, "literal", base, [],
                         ["Cole o literal no lugar do bloco entre `%s` e `%s` do build-form.gs (ou use --out)." % (BEGIN, END)]
                         + steps_pend), block + "\n"

    tpl_path = args.template or DEFAULT_TEMPLATE
    try:
        with open(tpl_path, "rb") as fh:
            tpl = fh.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return 2, result(False, "usage_error", {"template": tpl_path},
                         ["Não consegui ler o template %s: %s" % (tpl_path, exc)], ["Informe --template com o build-form.gs."]), None
    text, why = render_gs(tpl, block)
    if why:
        base["template"] = tpl_path
        return 1, result(False, "template_issue", base, ["Template inválido: %s." % why],
                         ["Use o templates/build-form.gs da skill ou acrescente os dois marcadores em volta de `var SPEC = {...};`."]), None
    out_path = args.out
    if os.path.exists(out_path) and not args.force:
        base["out"] = out_path
        return 1, result(False, "exists", base, ["O arquivo de saída já existe: %s" % out_path],
                         ["Escolha outro --out ou repita com --force para sobrescrever."]), None
    try:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except OSError as exc:
        return 2, result(False, "usage_error", base, ["Não consegui gravar %s: %s" % (out_path, exc)],
                         ["Confira se a pasta existe e tem permissão de escrita."]), None
    base.update({"out": out_path, "template": tpl_path, "bytes": len(text.encode("utf-8")),
                 "out_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    return 0, result(True, "generated", base, [],
                     ["Cole o arquivo inteiro num projeto do Apps Script, fixe o manifesto (oauthScopes) e execute `criarFormulario` (apps-script.md)."]
                     + steps_pend), None


def main(argv=None, yaml_module=False):
    """`yaml_module=False` (padrão) tenta importar PyYAML; os testes injetam um módulo ou None."""
    ap = _Parser(description="Converte um FORM-SPEC aprovado no SPEC do build-form.gs.")
    ap.add_argument("spec", help="caminho do spec (.json, .yaml, .yml)")
    ap.add_argument("--out", help="grava o build-form.gs completo neste arquivo")
    ap.add_argument("--literal", action="store_true", help="imprime só `var SPEC = {...};` em stdout")
    ap.add_argument("--template", help="build-form.gs com marcadores (padrão: templates/build-form.gs da skill)")
    ap.add_argument("--force", action="store_true", help="sobrescreve o arquivo de --out")
    args = ap.parse_args(argv)
    ymod = vs.import_yaml() if yaml_module is False else yaml_module
    code, payload, literal = run(args, ymod)
    if args.literal and code != 2:
        if literal is not None:
            sys.stdout.write(literal)
        emit(payload, sys.stderr)
    else:
        emit(payload, sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
