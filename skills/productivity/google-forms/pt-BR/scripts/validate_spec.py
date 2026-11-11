#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida de forma determinística um FORM-SPEC (o plano aprovado de um Google Forms).

Uso:
    python3 scripts/validate_spec.py SPEC.json|SPEC.yaml [--for-build] [--format json|text]
    python3 scripts/validate_spec.py --rules [--format json|text]
    (Windows: py -3 scripts\\validate_spec.py ...)

Entrada: `.json` (biblioteca padrão) ou `.yaml`/`.yml` (usa PyYAML se estiver instalado; não
há parser YAML próprio: sem PyYAML, converta o spec para JSON ou instale o PyYAML: `pip install pyyaml`).

Saída (stdout): um único JSON {"ok", "status", "data", "problems", "next_steps"}
(ou texto legível com --format text). Códigos de saída: 0 = ok; 1 = problema acionável;
2 = erro de uso.

Status:
    valid                 nenhum achado
    valid_with_warnings   só avisos (inclui itens PENDENTE_UI e heurísticas)
    invalid               pelo menos um erro (ou, com --for-build, spec que não está `approved`)
    pending_owner         sem erros, mas há `pending_owner` (decisão do dono): bloqueia a aprovação
    usage_error           arquivo ausente, extensão não suportada, PyYAML ausente, argumentos ruins

Prioridade quando há mais de um: invalid > pending_owner > valid_with_warnings > valid.
Exit 0 só em valid e valid_with_warnings.

`--for-build` exige `status: approved` (e `approved_at`) no spec, sem erros e sem
`pending_owner`; use antes de construir. Sem a flag, um spec `draft` correto é `valid`.

Cada achado: {"id_regra", "severidade": "erro"|"aviso", "caminho", "mensagem"} (+ "heuristica": true
quando a regra é por palavras-chave, e "pendente_ui": true nos itens que o Apps Script não cria).
Os ids de regra são estáveis; `--rules` lista o catálogo completo.

Somente leitura: o script nunca altera o spec. Requer Python 3.8+ e apenas a biblioteca padrão
(PyYAML opcional).
"""

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

PENDING = "pending_owner"
MAX_ITEMS = 300
MAX_SECTIONS = 75
SUBMIT = "submit"

# --------------------------------------------------------------------------------------
# Catálogo de regras: id -> (severidade padrão, descrição). IDs são estáveis.
# --------------------------------------------------------------------------------------
RULES = {
    # Entrada
    "SPEC-IO-01": ("erro", "Arquivo não é JSON/YAML válido ou a raiz não é um objeto."),
    "SPEC-IO-02": ("erro", "Chave duplicada no objeto (JSON): a última sobrescreveria a anterior."),
    # Estrutura
    "SPEC-STR-01": ("erro", "Campo obrigatório ausente ou com tipo errado (meta.title, sections, listas, objetos)."),
    "SPEC-STR-02": ("aviso", "spec_version diferente de 1 (versão do contrato que este validador conhece)."),
    "SPEC-STR-03": ("erro", "Seção sem itens."),
    "SPEC-STR-04": ("aviso", "version ausente ou não é inteiro >= 1."),
    # IDs
    "SPEC-ID-01": ("erro", "id fora do formato (seções s<n>, itens q<n>, n inteiro >= 1 sem zeros à esquerda)."),
    "SPEC-ID-02": ("erro", "id duplicado no spec inteiro."),
    "SPEC-ID-03": ("erro", "Não existe a seção s1."),
    "SPEC-ID-04": ("aviso", "ids fora de ordem crescente (itens numeram o formulário inteiro; indício de id reaproveitado)."),
    # Limites
    "SPEC-LIM-01": ("erro", "Mais de 300 itens no total."),
    "SPEC-LIM-02": ("erro", "Mais de 75 seções."),
    # Títulos
    "SPEC-TIT-01": ("erro", "Título vazio ou padrão (\"Pergunta sem título\", \"Opção 1\"...) em formulário, item, seção, opção ou grade."),
    "SPEC-TIT-02": ("erro", "Seção além da primeira sem título."),
    # Opções
    "SPEC-OPT-01": ("erro", "Opções repetidas dentro do mesmo item (ou linhas/colunas de grade repetidas)."),
    "SPEC-OPT-02": ("erro", "multiple_choice e dropdown precisam de pelo menos 2 opções."),
    "SPEC-OPT-03": ("erro", "Opções/grade ausentes, vazias ou mal formadas (cada opção é {value: ...})."),
    # Tipos
    "SPEC-TYPE-01": ("erro", "Tipo de item inexistente ou ausente."),
    "SPEC-TYPE-02": ("erro", "Campo exigido pelo tipo está ausente ou inválido (scale, rating, grid, image, video, file_upload...)."),
    "SPEC-TYPE-03": ("aviso", "Campo que não se aplica ao tipo do item (seria ignorado na construção)."),
    "SPEC-TYPE-04": ("erro", "other: true só existe em multiple_choice e checkboxes."),
    "SPEC-TYPE-05": ("aviso", "Campo desconhecido (possível erro de digitação)."),
    "SPEC-TYPE-06": ("erro", "required/personal com tipo errado (devem ser booleanos)."),
    # Validação de resposta
    "SPEC-VAL-01": ("erro", "validation.kind incompatível com o tipo do item."),
    "SPEC-VAL-02": ("erro", "validation.rule inexistente para o kind."),
    "SPEC-VAL-03": ("erro", "validation.value com formato errado para o kind/rule."),
    "SPEC-VAL-04": ("erro", "validation sem mensagem de erro própria (validation.error)."),
    "SPEC-VAL-05": ("aviso", "Expressão regular que o Python não compila (o dialeto do Forms não é documentado)."),
    # Ramificação
    "SPEC-NAV-01": ("erro", "go_to/after_section não é next, submit nem id de seção existente."),
    "SPEC-NAV-02": ("erro", "go_to/after_section aponta para s1 (proibido)."),
    "SPEC-NAV-03": ("erro", "go_to fora de multiple_choice/dropdown."),
    "SPEC-NAV-04": ("erro", "Item com go_to em algumas opções mas não em todas (escreva next explícito)."),
    "SPEC-NAV-05": ("erro", "Item com go_to e other: true."),
    "SPEC-NAV-06": ("erro", "Mais de uma pergunta com go_to na mesma seção."),
    "SPEC-NAV-07": ("erro", "Seção com pergunta de go_to declara também after_section."),
    "SPEC-NAV-08": ("erro", "Seção inalcançável a partir de s1."),
    "SPEC-NAV-09": ("erro", "Ciclo na navegação entre seções."),
    "SPEC-NAV-10": ("aviso", "Navegação para seção anterior (sem ciclo); confirme que é intencional."),
    # Quiz
    "SPEC-QUIZ-01": ("erro", "points/answer_key/feedback com quiz.enabled desligado."),
    "SPEC-QUIZ-02": ("erro", "points/answer_key em tipo não pontuável, ou feedback.right/wrong sem escolha com gabarito."),
    "SPEC-QUIZ-03": ("erro", "answer_key inválido: não é lista, valor que não existe em options, ou mais de 1 valor em multiple_choice/dropdown."),
    "SPEC-QUIZ-04": ("erro", "points inválido (inteiro >= 0) ou feedback mal formado."),
    "SPEC-QUIZ-05": ("aviso", "points sem answer_key, ou answer_key sem points."),
    "SPEC-QUIZ-06": ("erro", "after_manual_review sem collect_email."),
    # Configurações e dependências
    "SPEC-CFG-01": ("erro", "Valor fora da enumeração permitida (status, account_type, build.path, collect_email...)."),
    "SPEC-CFG-02": ("erro", "send_copy diferente de never exige collect_email diferente de none."),
    "SPEC-CFG-03": ("erro", "publish.audience incoerente (domain só em workspace; specific exige responders)."),
    "SPEC-CFG-04": ("aviso", "Heurística: exige login Google (limit_one_response, verified, file_upload) mas a descrição não avisa."),
    "SPEC-CFG-05": ("erro", "settings.close inválido (um critério só; at ISO; response_limit inteiro > 0)."),
    "SPEC-CFG-06": ("aviso", "Tema: cor inválida ou com contraste < 4,5 com texto branco; ou publish.published false."),
    "SPEC-CFG-07": ("erro", "Escala/rating/file_upload com limites inválidos."),
    "SPEC-CFG-08": ("aviso", "Valor não confirmado no editor (max_files, max_size) [comunidade]."),
    # Caminho de construção
    "SPEC-BLD-01": ("erro", "file_upload exige build.path: ui."),
    "SPEC-BLD-02": ("erro", "Recurso do spec sem suporte em build.path: api."),
    "SPEC-BLD-03": ("aviso", "PENDENTE_UI: recurso que só a interface aplica (build.path: apps_script)."),
    "SPEC-BLD-04": ("aviso", "PENDENTE_UI: linear_scale com high 2 no Apps Script (cria com 3)."),
    "SPEC-BLD-05": ("aviso", "PENDENTE_UI: video.caption no Apps Script."),
    "SPEC-BLD-06": ("aviso", "PENDENTE_UI: answer_key com go_to no mesmo item no Apps Script."),
    "SPEC-BLD-07": ("aviso", "PENDENTE_UI: grid.shuffle_rows no Apps Script."),
    "SPEC-BLD-08": ("aviso", "Suporte [não verificado] no caminho escolhido (rating; publicação por audiência)."),
    # Dados pessoais
    "SPEC-PRIV-01": ("erro", "personal: true ou collect_email sem entrada no privacy.inventory (ou entrada órfã)."),
    "SPEC-PRIV-02": ("erro", "privacy.personal_data incoerente com itens, inventário ou coleta de e-mail."),
    "SPEC-PRIV-03": ("erro", "Inventário sem purpose; ou legal_basis/controller/contact/retention/sharing vazios; decided_by diferente de owner."),
    "SPEC-PRIV-04": ("aviso", "Heurística: meta.description sem aviso de privacidade com dado pessoal."),
    "SPEC-PRIV-05": ("aviso", "Heurística: dado sensível (CPF, RG, nascimento, endereço) pedido; exige justificativa explícita do dono."),
    "SPEC-PRIV-06": ("erro", "E-mail pedido como pergunta com collect_email ligado (erro se validation.rule email; aviso heurístico se só o título cita e-mail)."),
    "SPEC-PRIV-07": ("aviso", "Heurística: item parece coletar dado pessoal mas está com personal: false (ou inventário cita item sem personal: true)."),
    "SPEC-PRIV-08": ("aviso", "Heurística: personal_data sensitive/minors sem opção \"Prefiro não responder\"."),
    # Uso
    "SPEC-USE-01": ("erro", "Pergunta sem `use` preenchido."),
    "SPEC-USE-02": ("erro", "brief.goal ausente (nada a que ligar o `use`)."),
    # Segurança
    "SPEC-SEC-01": ("erro", "Heurística por palavras-chave: título pede senha, token, código de verificação ou dado de cartão."),
    # Aprovação
    "SPEC-APR-01": ("erro", "status inválido (draft | approved)."),
    "SPEC-APR-02": ("erro", "status approved sem approved_at ISO válido."),
    "SPEC-APR-03": ("erro", "status approved com pending_owner remanescente."),
    "SPEC-APR-04": ("erro", "--for-build exige status approved e o spec não está aprovado."),
    "SPEC-APR-05": ("aviso", "approved_at preenchido em spec que não está approved."),
    "SPEC-OWN-01": ("aviso", "Campo com pending_owner: decisão do dono pendente (status pending_owner; bloqueia aprovação)."),
}
PENDING_UI_RULES = {"SPEC-BLD-03", "SPEC-BLD-04", "SPEC-BLD-05", "SPEC-BLD-06", "SPEC-BLD-07"}
HEURISTIC_RULES = {"SPEC-CFG-04", "SPEC-PRIV-04", "SPEC-PRIV-05", "SPEC-PRIV-07", "SPEC-PRIV-08",
                   "SPEC-SEC-01", "SPEC-VAL-05"}

# --------------------------------------------------------------------------------------
# Tabelas do contrato
# --------------------------------------------------------------------------------------
QUESTION_TYPES = ("short_text", "paragraph", "multiple_choice", "checkboxes", "dropdown", "linear_scale",
                  "rating", "mc_grid", "checkbox_grid", "date", "time", "file_upload")
NON_QUESTION_TYPES = ("title_description", "image", "video")
ALL_TYPES = QUESTION_TYPES + NON_QUESTION_TYPES
CHOICE_TYPES = ("multiple_choice", "checkboxes", "dropdown")
BRANCH_TYPES = ("multiple_choice", "dropdown")
GRID_TYPES = ("mc_grid", "checkbox_grid")
SCORABLE_TYPES = ("short_text", "multiple_choice", "checkboxes", "dropdown", "mc_grid", "checkbox_grid")

COMMON_KEYS = {"id", "type", "title", "description", "required", "use", "personal", "validation",
               "points", "answer_key", "feedback"}
# campo específico -> tipos onde se aplica
TYPE_FIELDS = {
    "options": CHOICE_TYPES, "other": ("multiple_choice", "checkboxes"), "shuffle_options": CHOICE_TYPES,
    "scale": ("linear_scale",), "rating": ("rating",), "grid": GRID_TYPES, "date": ("date",),
    "time": ("time",), "file_upload": ("file_upload",), "image": ("image",), "video": ("video",),
}
VALIDATION_TYPES = ("short_text", "paragraph", "checkboxes")
VALIDATION_RULES = {
    "number": ("gt", "gte", "lt", "lte", "eq", "neq", "between", "not_between", "is_number", "whole_number"),
    "text": ("contains", "not_contains", "email", "url"),
    "length": ("max_chars", "min_chars"),
    "regex": ("contains", "not_contains", "matches", "not_matches"),
    "selection": ("at_least", "at_most", "exactly"),
}
VALIDATION_KINDS_BY_TYPE = {
    "short_text": ("number", "text", "length", "regex"),
    "paragraph": ("length", "regex"),
    "checkboxes": ("selection",),
}
ENUMS = {
    "status": ("draft", "approved"),
    "account_type": ("personal", "workspace"),
    "build.path": ("ui", "apps_script", "api"),
    "personal_data": ("none", "personal", "sensitive", "minors"),
    "collect_email": ("none", "verified", "responder_input"),
    "send_copy": ("never", "when_requested", "always"),
    "quiz.release": ("immediately", "after_manual_review"),
    "publish.audience": ("anyone_with_link", "domain", "specific"),
    "responses.sheet": ("none", "new", "existing"),
}
DEFAULT_TITLES = {
    "pergunta sem titulo", "untitled question", "sem titulo", "formulario sem titulo", "untitled form",
    "titulo", "titulo do formulario", "pergunta", "question", "secao sem titulo", "untitled section",
    "opcao", "option", "descricao do formulario",
}
DEFAULT_TITLE_RE = re.compile(r"^(opcao|option|pergunta|question|secao|section|linha|row|coluna|column)\s*\d+$")
SEC_ID_RE = re.compile(r"^s[1-9][0-9]*$")
ITEM_ID_RE = re.compile(r"^q[1-9][0-9]*$")
YOUTUBE_RE = re.compile(r"^https?://(www\.|m\.)?(youtube\.com/(watch\?|embed/|shorts/)|youtu\.be/)", re.I)
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# Heurística de credenciais, sobre texto normalizado (sem acento, minúsculo).
SECRET_PATTERNS = [
    (r"\bsenha", "senha"), (r"\bpassword\b|\bpasswd\b|\bpasscode\b", "senha"),
    (r"\btoken\b", "token"), (r"\b(otp|2fa|mfa)\b", "código de verificação"),
    (r"codigo (de )?(verificacao|seguranca|confirmacao|autenticacao|acesso|sms)", "código de verificação"),
    (r"\bcodigo (enviado|recebido)", "código de verificação"),
    (r"\bcvv\b|\bcvc\b|\bcsc\b", "dado de cartão"),
    (r"\bcartao\b|\bcartoes\b|\bcard number\b|credit card", "dado de cartão"),
    (r"chave (de )?api|api[ -]?key|\bsecret\b|chave secreta|passphrase|frase[- ]senha", "credencial"),
    (r"\bpin\b", "PIN"),
]
SENSITIVE_PERSONAL_RE = re.compile(r"\bcpf\b|\brg\b|data de nascimento|\bnascimento\b|endereco|\bcep\b|passaporte|\bcnh\b")
PERSONAL_HINT_RE = re.compile(r"\bcpf\b|\brg\b|telefone|celular|whatsapp|e-?mail|nome completo|"
                              r"data de nascimento|endereco|\bcep\b")
EMAIL_TITLE_RE = re.compile(r"e-?mail")
PRIVACY_NOTICE_WORDS = ("dados", "privacidade", "lgpd", "http", "titular")
LOGIN_WORDS = ("login", "logad", "conta google", "entrar", "faca log")


def norm(text):
    """Minúsculas sem acento, para busca por palavras-chave."""
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKD", text)
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


def is_pending(value):
    return isinstance(value, str) and value.strip() == PENDING


def is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def blank(value):
    return value is None or (isinstance(value, str) and not value.strip()) or \
        (isinstance(value, (list, dict)) and not value)


def contrast_with_white(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    chans = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255.0
        chans.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]
    return 1.05 / (lum + 0.05)


def sdict(parent, key):
    v = parent.get(key) if isinstance(parent, dict) else None
    return v if isinstance(v, dict) else {}


# --------------------------------------------------------------------------------------
# Verificador
# --------------------------------------------------------------------------------------
class Checker(object):
    def __init__(self, spec, for_build=False):
        self.spec = spec
        self.for_build = for_build
        self.findings = []
        self.pending_paths = []
        self.sections = []          # [(path, dict, id|None)]
        self.sec_index = {}         # id -> índice da 1ª ocorrência
        self.items = []             # [(path, dict, índice_da_seção)]
        self.item_by_id = {}
        self.build_path = None
        self.quiz_on = False
        self.collect_email = "none"
        self.account_type = None
        self.reach = {}

    # ---- util ----
    def add(self, rule, path, message, severity=None):
        sev = severity or RULES[rule][0]
        heuristic = rule in HEURISTIC_RULES or (rule == "SPEC-PRIV-06" and sev == "aviso")
        if heuristic and not message.startswith("Heurística"):
            message = "Heurística: " + message
        f = {"id_regra": rule, "severidade": sev, "caminho": path, "mensagem": message}
        if heuristic:
            f["heuristica"] = True
        if rule in PENDING_UI_RULES:
            f["pendente_ui"] = True
        self.findings.append(f)

    def get_obj(self, parent, key, required=False):
        v = parent.get(key) if isinstance(parent, dict) else None
        if v is None:
            if required:
                self.add("SPEC-STR-01", key, "Campo obrigatório `%s` ausente." % key)
            return {}
        if not isinstance(v, dict):
            if not is_pending(v):
                self.add("SPEC-STR-01", key, "`%s` deveria ser um objeto." % key)
            return {}
        return v

    def enum(self, value, name, path):
        if value is None or is_pending(value):
            return
        if not isinstance(value, (str, bool, int, float)) or value not in ENUMS[name]:
            self.add("SPEC-CFG-01", path, "Valor %r inválido para %s; permitidos: %s." %
                     (value, name, ", ".join(ENUMS[name])))

    # ---- orquestração ----
    def run(self):
        self.walk_pending(self.spec, "")
        self.check_root()
        self.check_ids_and_limits()
        for path, item, si in self.items:
            self.check_item(path, item, si)
        self.check_navigation()
        self.check_privacy()
        self.check_settings_dependencies()
        self.check_build_path()
        self.check_approval()
        return self.findings

    def walk_pending(self, node, path):
        if is_pending(node):
            self.pending_paths.append(path or "(raiz)")
        elif isinstance(node, dict):
            for k, v in node.items():
                self.walk_pending(v, "%s.%s" % (path, k) if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                self.walk_pending(v, "%s[%d]" % (path, i))

    # ---- raiz, meta, brief, enums, coleta de seções/itens ----
    def check_root(self):
        spec = self.spec
        sv = spec.get("spec_version")
        if sv is None:
            self.add("SPEC-STR-01", "spec_version", "Campo obrigatório `spec_version` ausente.")
        elif sv != 1:
            self.add("SPEC-STR-02", "spec_version", "spec_version %r: este validador conhece a versão 1." % (sv,))
        v = spec.get("version")
        if not is_int(v) or v < 1:
            self.add("SPEC-STR-04", "version", "`version` deve ser inteiro >= 1 (valor atual: %r)." % (v,))

        status = spec.get("status")
        if status is None:
            self.add("SPEC-STR-01", "status", "Campo obrigatório `status` ausente (draft | approved).")
        elif status not in ENUMS["status"]:
            self.add("SPEC-APR-01", "status", "status %r inválido; use draft ou approved." % (status,))

        meta = self.get_obj(spec, "meta", required=True)
        title = meta.get("title")
        if blank(title) or not isinstance(title, str):
            self.add("SPEC-STR-01", "meta.title", "meta.title é obrigatório e deve ser texto.")
        elif self.is_default_title(title):
            self.add("SPEC-TIT-01", "meta.title", "Título padrão %r: escreva um título real." % title)
        if blank(meta.get("language")):
            self.add("SPEC-STR-01", "meta.language", "meta.language ausente (ex.: pt-BR).", severity="aviso")

        brief = self.get_obj(spec, "brief", required=True)
        if blank(brief.get("goal")):
            self.add("SPEC-USE-02", "brief.goal", "brief.goal ausente: sem objetivo não há como julgar o `use` de cada pergunta.")
        self.account_type = brief.get("account_type")
        self.enum(self.account_type, "account_type", "brief.account_type")

        build = self.get_obj(spec, "build", required=True)
        self.build_path = build.get("path")
        if self.build_path is None:
            self.add("SPEC-STR-01", "build.path", "Campo obrigatório `build.path` ausente (ui | apps_script | api).")
        self.enum(self.build_path, "build.path", "build.path")

        settings = self.get_obj(spec, "settings")
        ce = settings.get("collect_email", "none")
        self.collect_email = ce if isinstance(ce, str) else "none"
        self.enum(settings.get("collect_email"), "collect_email", "settings.collect_email")
        self.enum(settings.get("send_copy"), "send_copy", "settings.send_copy")

        quiz = self.get_obj(spec, "quiz")
        self.quiz_on = quiz.get("enabled") is True
        self.enum(quiz.get("release"), "quiz.release", "quiz.release")

        publish = self.get_obj(spec, "publish")
        self.enum(publish.get("audience"), "publish.audience", "publish.audience")
        responses = self.get_obj(spec, "responses")
        self.enum(responses.get("sheet"), "responses.sheet", "responses.sheet")
        if responses.get("sheet") == "existing" and blank(responses.get("sheet_ref")):
            self.add("SPEC-CFG-01", "responses.sheet_ref", "responses.sheet: existing exige sheet_ref (nome ou URL).")

        privacy = self.get_obj(spec, "privacy", required=True)
        self.enum(privacy.get("personal_data"), "personal_data", "privacy.personal_data")
        self.get_obj(spec, "theme")

        sections = spec.get("sections")
        if not isinstance(sections, list) or not sections:
            self.add("SPEC-STR-01", "sections", "`sections` deve ser uma lista com pelo menos uma seção.")
            sections = []
        for i, sec in enumerate(sections):
            spath = "sections[%d]" % i
            if not isinstance(sec, dict):
                self.add("SPEC-STR-01", spath, "Cada seção deve ser um objeto.")
                continue
            sid = sec.get("id") if isinstance(sec.get("id"), str) else None
            self.sections.append((spath, sec, sid))
        for si, (spath, sec, sid) in enumerate(self.sections):
            if sid is not None and sid not in self.sec_index:
                self.sec_index[sid] = si
            items = sec.get("items")
            if items is None or (isinstance(items, list) and not items):
                self.add("SPEC-STR-03", spath + ".items", "A seção %s não tem nenhum item." % (sid or spath))
                continue
            if not isinstance(items, list):
                self.add("SPEC-STR-01", spath + ".items", "`items` da seção %s deve ser uma lista." % (sid or spath))
                continue
            for j, it in enumerate(items):
                ipath = "%s.items[%d]" % (spath, j)
                if not isinstance(it, dict):
                    self.add("SPEC-STR-01", ipath, "Cada item deve ser um objeto.")
                    continue
                self.items.append((ipath, it, si))

    # ---- ids e limites ----
    def check_ids_and_limits(self):
        seen = {}
        last_sec = 0
        for si, (spath, sec, sid) in enumerate(self.sections):
            idpath = spath + ".id"
            if sid is None:
                self.add("SPEC-ID-01", idpath, "Seção sem `id` textual (esperado s1, s2...).")
                continue
            if not SEC_ID_RE.match(sid):
                self.add("SPEC-ID-01", idpath, "id de seção %r fora do formato s<n> (ex.: s1)." % sid)
            else:
                n = int(sid[1:])
                if n <= last_sec:
                    self.add("SPEC-ID-04", idpath, "id %s fora de ordem crescente (anterior: s%d)." % (sid, last_sec))
                last_sec = max(last_sec, n)
            if sid in seen:
                self.add("SPEC-ID-02", idpath, "id %r duplicado (já usado em %s)." % (sid, seen[sid]))
            else:
                seen[sid] = spath
        if "s1" not in self.sec_index:
            self.add("SPEC-ID-03", "sections", "Não existe a seção `s1` (a primeira seção deve ter id s1).")
        last_q = 0
        for ipath, it, si in self.items:
            iid = it.get("id")
            if not isinstance(iid, str):
                self.add("SPEC-ID-01", ipath + ".id", "Item sem `id` textual (esperado q1, q2...).")
                continue
            if not ITEM_ID_RE.match(iid):
                self.add("SPEC-ID-01", ipath + ".id", "id de item %r fora do formato q<n> (ex.: q1)." % iid)
            else:
                n = int(iid[1:])
                if n <= last_q:
                    self.add("SPEC-ID-04", ipath + ".id",
                             "id %s fora de ordem crescente (anterior: q%d); ids não são reaproveitados nem reordenados." % (iid, last_q))
                last_q = max(last_q, n)
            if iid in seen:
                self.add("SPEC-ID-02", ipath + ".id", "id %r duplicado (já usado em %s)." % (iid, seen[iid]))
            else:
                seen[iid] = ipath
                self.item_by_id[iid] = (ipath, it)
        if len(self.items) > MAX_ITEMS:
            self.add("SPEC-LIM-01", "sections", "%d itens; o Forms aceita no máximo %d." % (len(self.items), MAX_ITEMS))
        if len(self.sections) > MAX_SECTIONS:
            self.add("SPEC-LIM-02", "sections", "%d seções; o Forms aceita no máximo %d." % (len(self.sections), MAX_SECTIONS))
        for si, (spath, sec, sid) in enumerate(self.sections):
            if si == 0:
                continue
            t = sec.get("title")
            if blank(t):
                self.add("SPEC-TIT-02", spath + ".title", "Seção %s sem título (só a primeira usa o cabeçalho do formulário)." % (sid or spath))
            elif isinstance(t, str) and self.is_default_title(t):
                self.add("SPEC-TIT-01", spath + ".title", "Título padrão %r na seção %s." % (t, sid or spath))

    @staticmethod
    def is_default_title(text):
        n = re.sub(r"\s+", " ", norm(text))
        return n in DEFAULT_TITLES or bool(DEFAULT_TITLE_RE.match(n))

    # ---- itens ----
    def check_item(self, path, item, si):
        itype = item.get("type")
        iid = item.get("id", path)
        if itype not in ALL_TYPES:
            self.add("SPEC-TYPE-01", path + ".type", "Tipo %r inexistente; válidos: %s." % (itype, ", ".join(ALL_TYPES)))
            return
        is_question = itype in QUESTION_TYPES
        for k in item:
            if k in COMMON_KEYS:
                continue
            if k in TYPE_FIELDS:
                if itype not in TYPE_FIELDS[k]:
                    if k == "other":
                        self.add("SPEC-TYPE-04", path + ".other", "other: true só existe em multiple_choice e checkboxes (tipo: %s)." % itype)
                    else:
                        self.add("SPEC-TYPE-03", "%s.%s" % (path, k), "`%s` não se aplica ao tipo %s; seria ignorado." % (k, itype))
            else:
                self.add("SPEC-TYPE-05", "%s.%s" % (path, k), "Campo desconhecido `%s` (erro de digitação?)." % k)
        title = item.get("title")
        if itype == "title_description" or is_question:
            if blank(title) or not isinstance(title, str):
                self.add("SPEC-TIT-01", path + ".title", "Item %s sem título." % iid)
            elif self.is_default_title(title):
                self.add("SPEC-TIT-01", path + ".title", "Título padrão %r no item %s." % (title, iid))
        for key in ("required", "personal"):
            val = item.get(key)
            if val is not None and not isinstance(val, bool) and not is_pending(val):
                self.add("SPEC-TYPE-06", "%s.%s" % (path, key), "`%s` deve ser true ou false." % key)
        if not is_question:
            for key in ("required", "personal"):
                if item.get(key) is True:
                    self.add("SPEC-TYPE-03", "%s.%s" % (path, key), "`%s` não se aplica a %s." % (key, itype))
        if is_question and blank(item.get("use")):
            self.add("SPEC-USE-01", path + ".use", "Pergunta %s sem `use` (para que a resposta serve)." % iid)
        getattr(self, "type_" + itype)(path, item)
        if item.get("validation") is not None:
            self.check_validation(path, item)
        if itype in CHOICE_TYPES:
            self.check_options(path, item)
        if is_question or itype == "title_description":
            self.check_secrets(path, item)
        self.check_quiz_fields(path, item)

    def type_plain(self, path, item):
        pass

    type_short_text = type_paragraph = type_dropdown = type_multiple_choice = type_plain
    type_checkboxes = type_title_description = type_plain

    def type_linear_scale(self, path, item):
        sc = item.get("scale")
        p = path + ".scale"
        if not isinstance(sc, dict):
            self.add("SPEC-TYPE-02", p, "linear_scale exige `scale: {low, high, low_label, high_label}`.")
            return
        low, high = sc.get("low"), sc.get("high")
        ok = True
        if not is_int(low) or low not in (0, 1):
            self.add("SPEC-CFG-07", p + ".low", "scale.low deve ser 0 ou 1 (atual: %r)." % (low,))
            ok = False
        if not is_int(high) or not 2 <= high <= 10:
            self.add("SPEC-CFG-07", p + ".high", "scale.high deve ser inteiro de 2 a 10 (atual: %r)." % (high,))
            ok = False
        if ok and high <= low:
            self.add("SPEC-CFG-07", p, "scale.high (%d) precisa ser maior que scale.low (%d)." % (high, low))
            ok = False
        for lab in ("low_label", "high_label"):
            if blank(sc.get(lab)):
                self.add("SPEC-CFG-07", "%s.%s" % (p, lab), "Falta rótulo na ponta da escala (`%s`)." % lab)
        if ok and high == 2 and self.build_path == "apps_script":
            self.add("SPEC-BLD-04", p + ".high",
                     "PENDENTE_UI: no Apps Script high vai de 3 a 10; o script cria com 3 e o ajuste para 2 é pela interface. "
                     "Use build.path: ui ou high >= 3.")

    def type_rating(self, path, item):
        r = item.get("rating")
        p = path + ".rating"
        if not isinstance(r, dict):
            self.add("SPEC-TYPE-02", p, "rating exige `rating: {levels, icon}`.")
            return
        lv = r.get("levels")
        if not is_int(lv) or not 3 <= lv <= 10:
            self.add("SPEC-CFG-07", p + ".levels", "rating.levels deve ser inteiro de 3 a 10 (atual: %r)." % (lv,))
        if r.get("icon") not in ("star", "heart", "thumb_up"):
            self.add("SPEC-CFG-07", p + ".icon", "rating.icon deve ser star, heart ou thumb_up (atual: %r)." % (r.get("icon"),))

    def type_grid(self, path, item):
        g = item.get("grid")
        p = path + ".grid"
        if not isinstance(g, dict):
            self.add("SPEC-TYPE-02", p, "Grade exige `grid: {rows, columns}`.")
            return
        for key in ("rows", "columns"):
            vals = g.get(key)
            if not isinstance(vals, list) or not vals or not all(isinstance(v, str) and v.strip() for v in vals):
                self.add("SPEC-OPT-03", "%s.%s" % (p, key), "grid.%s deve ser lista de textos não vazios, com pelo menos 1." % key)
                continue
            self.check_unique(vals, "%s.%s" % (p, key), "grid.%s" % key)
            for k, v in enumerate(vals):
                if self.is_default_title(v):
                    self.add("SPEC-TIT-01", "%s.%s[%d]" % (p, key, k), "Rótulo padrão %r em grid.%s." % (v, key))

    type_mc_grid = type_checkbox_grid = type_grid

    def type_date(self, path, item):
        d = item.get("date")
        if d is not None and (not isinstance(d, dict) or any(not isinstance(v, bool) for v in d.values())):
            self.add("SPEC-TYPE-02", path + ".date", "date deve ser {include_year: bool, include_time: bool}.")

    def type_time(self, path, item):
        t = item.get("time")
        if t is not None and (not isinstance(t, dict) or any(not isinstance(v, bool) for v in t.values())):
            self.add("SPEC-TYPE-02", path + ".time", "time deve ser {duration: bool}.")

    def type_file_upload(self, path, item):
        f = item.get("file_upload")
        p = path + ".file_upload"
        if self.build_path not in (None, "ui") and not is_pending(self.build_path):
            self.add("SPEC-BLD-01", p, "file_upload só pode ser criado pela interface; build.path é %r (use ui)." % (self.build_path,))
        if not isinstance(f, dict):
            self.add("SPEC-TYPE-02", p, "file_upload exige `file_upload: {types, max_files, max_size}`.")
            return
        types = f.get("types")
        if not isinstance(types, list) or not types or not all(isinstance(t, str) and t.strip() for t in types):
            self.add("SPEC-CFG-07", p + ".types", "file_upload.types deve ser lista não vazia de categorias (ex.: pdf, image).")
        mf = f.get("max_files")
        if isinstance(mf, bool) or mf not in (1, 5, 10):
            self.add("SPEC-CFG-08", p + ".max_files", "max_files %r: o editor oferece 1, 5 ou 10 [comunidade; confirmar no editor]." % (mf,))
        if str(f.get("max_size")).replace(" ", "").upper() not in ("1MB", "10MB", "100MB", "1GB", "10GB"):
            self.add("SPEC-CFG-08", p + ".max_size", "max_size %r: o editor oferece 1MB, 10MB, 100MB, 1GB ou 10GB [comunidade; confirmar no editor]." % (f.get("max_size"),))

    def type_image(self, path, item):
        im = item.get("image")
        p = path + ".image"
        if not isinstance(im, dict):
            self.add("SPEC-TYPE-02", p, "image exige `image: {source, alt_text, width}`.")
            return
        if blank(im.get("source")):
            self.add("SPEC-TYPE-02", p + ".source", "image.source ausente (URL ou caminho).")
        if blank(im.get("alt_text")):
            self.add("SPEC-TYPE-02", p + ".alt_text", "Falta alt_text (descrição para leitor de tela).", severity="aviso")
        w = im.get("width")
        if w is not None and (not is_num(w) or not 0 <= w <= 740):
            self.add("SPEC-TYPE-02", p + ".width", "image.width deve estar entre 0 e 740 px (atual: %r)." % (w,))

    def type_video(self, path, item):
        v = item.get("video")
        p = path + ".video"
        if not isinstance(v, dict):
            self.add("SPEC-TYPE-02", p, "video exige `video: {youtube_url, caption}`.")
            return
        url = v.get("youtube_url")
        if not isinstance(url, str) or not YOUTUBE_RE.match(url.strip()):
            self.add("SPEC-TYPE-02", p + ".youtube_url", "video.youtube_url deve ser um link do YouTube (atual: %r)." % (url,))
        if self.build_path == "apps_script" and not blank(v.get("caption")):
            self.add("SPEC-BLD-05", p + ".caption",
                     "PENDENTE_UI: o FormApp não tem método para a legenda do vídeo; aplique pela interface.")

    # ---- opções ----
    def check_unique(self, values, path, label):
        seen = {}
        for k, v in enumerate(values):
            key = re.sub(r"\s+", " ", norm(v)) if isinstance(v, str) else repr(v)
            if key in seen:
                self.add("SPEC-OPT-01", "%s[%d]" % (path, k), "%s repetido(a): %r (igual ao índice %d)." % (label, v, seen[key]))
            else:
                seen[key] = k

    def check_options(self, path, item):
        itype = item.get("type")
        opts = item.get("options")
        p = path + ".options"
        if not isinstance(opts, list) or not opts:
            self.add("SPEC-OPT-03" if itype == "checkboxes" else "SPEC-OPT-02", p,
                     "%s precisa de `options` com %s." % (itype, "pelo menos 1 opção" if itype == "checkboxes" else "pelo menos 2 opções"))
            return
        values = []
        for k, o in enumerate(opts):
            op = "%s[%d]" % (p, k)
            if not isinstance(o, dict) or not isinstance(o.get("value"), str) or blank(o.get("value")):
                self.add("SPEC-OPT-03", op, "Cada opção deve ser {value: \"texto\"} com texto não vazio.")
                continue
            if self.is_default_title(o["value"]):
                self.add("SPEC-TIT-01", op + ".value", "Opção com texto padrão: %r." % o["value"])
            values.append(o["value"])
        self.check_unique(values, p, "Opção")
        if itype in BRANCH_TYPES and len(opts) < 2:
            self.add("SPEC-OPT-02", p, "%s precisa de pelo menos 2 opções." % itype)
        with_goto = [k for k, o in enumerate(opts) if isinstance(o, dict) and o.get("go_to") is not None]
        if with_goto:
            if itype not in BRANCH_TYPES:
                self.add("SPEC-NAV-03", "%s[%d].go_to" % (p, with_goto[0]), "go_to só existe em multiple_choice e dropdown (tipo: %s)." % itype)
            else:
                missing = [k for k, o in enumerate(opts) if isinstance(o, dict) and o.get("go_to") is None]
                if missing:
                    self.add("SPEC-NAV-04", "%s[%d]" % (p, missing[0]),
                             "Há opções com go_to e opções sem; escreva `go_to: next` explícito em todas (faltam %d)." % len(missing))
                if item.get("other") is True:
                    self.add("SPEC-NAV-05", path + ".other", "Item com go_to não pode ter other: true.")

    # ---- validation ----
    def check_validation(self, path, item):
        v = item.get("validation")
        p = path + ".validation"
        itype = item.get("type")
        if not isinstance(v, dict):
            self.add("SPEC-VAL-03", p, "validation deve ser {kind, rule, value, error}.")
            return
        if itype not in VALIDATION_TYPES:
            self.add("SPEC-VAL-01", p, "O tipo %s não aceita validation (só short_text, paragraph, checkboxes)." % itype)
            return
        kind = v.get("kind")
        if kind not in VALIDATION_KINDS_BY_TYPE[itype]:
            self.add("SPEC-VAL-01", p + ".kind", "kind %r incompatível com %s; use: %s." %
                     (kind, itype, ", ".join(VALIDATION_KINDS_BY_TYPE[itype])))
            return
        rule, value = v.get("rule"), v.get("value")
        if rule not in VALIDATION_RULES[kind]:
            self.add("SPEC-VAL-02", p + ".rule", "rule %r inexistente para kind %s; use: %s." % (rule, kind, ", ".join(VALIDATION_RULES[kind])))
            return
        if blank(v.get("error")):
            self.add("SPEC-VAL-04", p + ".error", "Falta mensagem de erro própria dizendo o problema e como corrigir.")
        pv = p + ".value"
        if kind == "number":
            if rule in ("between", "not_between"):
                if not (isinstance(value, list) and len(value) == 2 and all(is_num(x) for x in value)):
                    self.add("SPEC-VAL-03", pv, "%s exige [min, max] numéricos." % rule)
                elif value[0] > value[1]:
                    self.add("SPEC-VAL-03", pv, "min (%s) maior que max (%s)." % (value[0], value[1]))
            elif rule in ("is_number", "whole_number"):
                if value is not None:
                    self.add("SPEC-VAL-03", pv, "%s não usa value (omita ou null)." % rule)
            elif not is_num(value):
                self.add("SPEC-VAL-03", pv, "%s exige value numérico." % rule)
        elif kind == "text":
            if rule in ("email", "url"):
                if not blank(value):
                    self.add("SPEC-VAL-03", pv, "%s não usa value (deixe vazio)." % rule)
            elif not isinstance(value, str) or not value:
                self.add("SPEC-VAL-03", pv, "%s exige value de texto não vazio." % rule)
        elif kind == "length":
            if not is_int(value) or value < (1 if rule == "max_chars" else 0):
                self.add("SPEC-VAL-03", pv, "%s exige inteiro %s." % (rule, ">= 1" if rule == "max_chars" else ">= 0"))
        elif kind == "regex":
            if not isinstance(value, str) or not value:
                self.add("SPEC-VAL-03", pv, "%s exige padrão (texto) não vazio." % rule)
            else:
                try:
                    re.compile(value)
                except re.error as exc:
                    self.add("SPEC-VAL-05", pv, "o padrão não compila no Python (%s); confira no editor do Forms." % exc)
        elif kind == "selection":
            n = len(item["options"]) if isinstance(item.get("options"), list) else None
            if not is_int(value) or value < 1:
                self.add("SPEC-VAL-03", pv, "%s exige inteiro >= 1." % rule)
            elif n is not None and value > n:
                self.add("SPEC-VAL-03", pv, "%s %d, mas o item só tem %d opções." % (rule, value, n))

    # ---- quiz ----
    def check_quiz_fields(self, path, item):
        itype = item.get("type")
        pts, key, fb = item.get("points"), item.get("answer_key"), item.get("feedback")
        used = [k for k, val in (("points", pts), ("answer_key", key), ("feedback", fb)) if val is not None]
        if not used:
            return
        if not self.quiz_on:
            self.add("SPEC-QUIZ-01", "%s.%s" % (path, used[0]), "%s só existe com quiz.enabled: true." % ", ".join(used))
            return
        if itype not in SCORABLE_TYPES and (pts is not None or key is not None):
            self.add("SPEC-QUIZ-02", path, "points/answer_key só em %s (tipo: %s)." % (", ".join(SCORABLE_TYPES), itype))
        if pts is not None and (not is_int(pts) or pts < 0):
            self.add("SPEC-QUIZ-04", path + ".points", "points deve ser inteiro >= 0 (atual: %r)." % (pts,))
        if key is not None:
            if not isinstance(key, list) or not key:
                self.add("SPEC-QUIZ-03", path + ".answer_key", "answer_key deve ser lista não vazia de valores corretos.")
            elif itype in CHOICE_TYPES:
                opt_values = [o.get("value") for o in item["options"] if isinstance(o, dict)] \
                    if isinstance(item.get("options"), list) else []
                for k, val in enumerate(key):
                    if val not in opt_values:
                        self.add("SPEC-QUIZ-03", "%s.answer_key[%d]" % (path, k), "Valor %r não existe em options." % (val,))
                if itype in BRANCH_TYPES and len(key) != 1:
                    self.add("SPEC-QUIZ-03", path + ".answer_key", "%s aceita uma única resposta correta (há %d)." % (itype, len(key)))
        if (pts is None) != (key is None) and itype in SCORABLE_TYPES:
            self.add("SPEC-QUIZ-05", path, "points e answer_key andam juntos: informe os dois (ou nenhum).")
        if fb is not None:
            if not isinstance(fb, dict) or any(k not in ("right", "wrong", "general") for k in fb):
                self.add("SPEC-QUIZ-04", path + ".feedback", "feedback deve ser {right, wrong, general} (todos opcionais).")
            else:
                if ("right" in fb or "wrong" in fb) and (itype not in CHOICE_TYPES or key is None):
                    self.add("SPEC-QUIZ-02", path + ".feedback", "feedback.right/wrong só em escolha (múltipla escolha, caixas, lista) com answer_key.")
                if "general" in fb and itype not in SCORABLE_TYPES:
                    self.add("SPEC-QUIZ-02", path + ".feedback.general", "feedback só em tipos pontuáveis.")
        has_goto = isinstance(item.get("options"), list) and any(
            isinstance(o, dict) and o.get("go_to") is not None for o in item["options"])
        if key is not None and has_goto and self.build_path == "apps_script":
            self.add("SPEC-BLD-06", path,
                     "PENDENTE_UI: no Apps Script o gabarito não é aplicado em item com go_to; marque a resposta correta pela interface.")

    # ---- segurança (heurística) ----
    def check_secrets(self, path, item):
        title = norm(item.get("title"))
        if not title:
            return
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, title):
                self.add("SPEC-SEC-01", path + ".title",
                         "o título parece pedir %s (%r). É proibido pedir senha, token, código de verificação ou dado de cartão: "
                         "remova o item. Se for falso positivo, reescreva o título sem essa palavra." % (label, item.get("title")))
                return

    # ---- navegação ----
    def resolve(self, target, si):
        """Índice da seção, SUBMIT ou None (inválido)."""
        if target == "next":
            return si + 1 if si + 1 < len(self.sections) else SUBMIT
        if target == SUBMIT:
            return SUBMIT
        if isinstance(target, str) and target in self.sec_index:
            return self.sec_index[target]
        return None

    def check_target(self, target, path, si):
        if is_pending(target):
            return "skip"
        if not isinstance(target, str) or (target not in ("next", SUBMIT) and target not in self.sec_index):
            self.add("SPEC-NAV-01", path, "Destino %r inexistente; use next, submit ou o id de uma seção do spec." % (target,))
            return None
        if target == "s1":
            self.add("SPEC-NAV-02", path, "Destino s1 é proibido (volta ao início e cria ciclo); para recomeçar use submit e explique na mensagem de confirmação.")
            return None
        return self.resolve(target, si)

    def label(self, i):
        return self.sections[i][2] or "sections[%d]" % i

    def check_navigation(self):
        n = len(self.sections)
        edges = {i: set() for i in range(n)}
        goto_by_section = {i: [] for i in range(n)}
        for ipath, it, si in self.items:
            opts = it.get("options")
            if it.get("type") in BRANCH_TYPES and isinstance(opts, list) and any(
                    isinstance(o, dict) and o.get("go_to") is not None for o in opts):
                goto_by_section[si].append((ipath, it))
        for si, (spath, sec, sid) in enumerate(self.sections):
            gq = goto_by_section[si]
            has_after = sec.get("after_section") is not None
            if len(gq) > 1:
                self.add("SPEC-NAV-06", gq[1][0], "Seção %s tem %d perguntas com go_to (%s); deixe só uma." %
                         (sid, len(gq), ", ".join(str(q[1].get("id")) for q in gq)))
            if gq and has_after:
                self.add("SPEC-NAV-07", spath + ".after_section",
                         "Seção %s tem pergunta com go_to e declara after_section; a navegação por resposta prevalece, remova after_section." % sid)
            outs = []
            for ipath, it in gq:
                for k, o in enumerate(it["options"]):
                    if not isinstance(o, dict):
                        continue
                    if o.get("go_to") is not None:
                        r = self.check_target(o["go_to"], "%s.options[%d].go_to" % (ipath, k), si)
                        outs.append(self.resolve("next", si) if r == "skip" else r)
                    else:
                        outs.append(self.resolve("next", si))
                if it.get("required") is not True:
                    outs.append(self.resolve("next", si))  # pode deixar em branco e seguir
            r_after = None
            if has_after:
                r_after = self.check_target(sec["after_section"], spath + ".after_section", si)
                if r_after == "skip":
                    r_after = self.resolve("next", si)
            if not gq:
                outs.append(r_after if has_after else self.resolve("next", si))
            for r in outs:
                if r is not None:
                    edges[si].add(r)
        if "s1" in self.sec_index:
            start = self.sec_index["s1"]
            seen, stack = {start}, [start]
            while stack:
                u = stack.pop()
                for v in edges[u]:
                    if v != SUBMIT and v not in seen:
                        seen.add(v)
                        stack.append(v)
            for si, (spath, sec, sid) in enumerate(self.sections):
                if si not in seen:
                    self.add("SPEC-NAV-08", spath, "Seção %s inalcançável a partir de s1: nenhuma navegação chega até ela." % (sid or spath))
        # ciclos: DFS iterativo com cores
        color = {i: 0 for i in range(n)}
        cycle_edges = set()
        reported = set()

        def nbrs(u):
            return iter(sorted(v for v in edges[u] if v != SUBMIT))

        for root in range(n):
            if color[root]:
                continue
            stack = [root]
            iters = {root: nbrs(root)}
            color[root] = 1
            while stack:
                u = stack[-1]
                try:
                    v = next(iters[u])
                except StopIteration:
                    color[u] = 2
                    stack.pop()
                    continue
                if color[v] == 1:
                    cyc = stack[stack.index(v):] + [v]
                    for a, b in zip(cyc, cyc[1:]):
                        cycle_edges.add((a, b))
                    key = frozenset(cyc)
                    if key not in reported:
                        reported.add(key)
                        self.add("SPEC-NAV-09", self.sections[u][0], "Ciclo na navegação: %s. O respondente pode nunca chegar ao envio." %
                                 " -> ".join(self.label(i) for i in cyc))
                elif color[v] == 0:
                    color[v] = 1
                    stack.append(v)
                    iters[v] = nbrs(v)
        for u in range(n):
            for v in sorted(x for x in edges[u] if x != SUBMIT):
                if v <= u and (u, v) not in cycle_edges:
                    self.add("SPEC-NAV-10", self.sections[u][0], "A seção %s navega para uma seção anterior (%s) sem formar ciclo; confirme que é intencional." %
                             (self.label(u), self.label(v)))
        self.reach = {"edges": {self.label(u): sorted("submit" if v == SUBMIT else self.label(v) for v in vs)
                                for u, vs in edges.items()}}

    # ---- dados pessoais ----
    def check_privacy(self):
        spec = self.spec
        privacy = sdict(spec, "privacy")
        pdata = privacy.get("personal_data")
        collect = self.collect_email
        inventory = privacy.get("inventory")
        inv_items = {}
        if inventory is not None and not isinstance(inventory, list):
            self.add("SPEC-STR-01", "privacy.inventory", "privacy.inventory deve ser uma lista.")
            inventory = []
        for k, e in enumerate(inventory or []):
            ep = "privacy.inventory[%d]" % k
            if not isinstance(e, dict) or blank(e.get("item")) or not isinstance(e.get("item"), str):
                self.add("SPEC-PRIV-01", ep, "Cada entrada do inventário precisa de `item` (id do item ou collect_email).")
                continue
            ref = e["item"]
            inv_items[ref] = ep
            if blank(e.get("purpose")):
                self.add("SPEC-PRIV-03", ep + ".purpose", "Entrada %s sem `purpose` (finalidade)." % ref)
            if ref == "collect_email":
                if collect == "none":
                    self.add("SPEC-PRIV-01", ep + ".item", "Inventário cita collect_email, mas settings.collect_email é none.")
            elif ref not in self.item_by_id:
                self.add("SPEC-PRIV-01", ep + ".item", "Inventário cita o item %r, que não existe no spec." % ref)
            elif self.item_by_id[ref][1].get("personal") is not True:
                self.add("SPEC-PRIV-07", self.item_by_id[ref][0] + ".personal",
                         "o item %s está no inventário mas não tem personal: true." % ref)
        personal_items = [(p, it) for p, it, _ in self.items if it.get("personal") is True]
        for p, it in personal_items:
            if it.get("id") not in inv_items:
                self.add("SPEC-PRIV-01", p + ".personal", "Item %s tem personal: true mas não está no privacy.inventory." % it.get("id"))
        email_on = collect in ("verified", "responder_input")
        if email_on and "collect_email" not in inv_items:
            self.add("SPEC-PRIV-01", "settings.collect_email", "collect_email %s coleta dado pessoal e precisa de uma entrada `item: collect_email` no inventário." % collect)
        has_personal = bool(personal_items) or email_on or bool(inv_items)
        if pdata == "none" and has_personal:
            self.add("SPEC-PRIV-02", "privacy.personal_data", "personal_data é none, mas há item personal, inventário ou coleta de e-mail.")
        if pdata in ("personal", "sensitive", "minors") and not has_personal:
            self.add("SPEC-PRIV-02", "privacy.personal_data", "personal_data é %s, mas nenhum item, inventário ou coleta de e-mail declara dado pessoal." % pdata)
        if pdata in ("personal", "sensitive", "minors"):
            for key in ("controller", "contact", "retention", "sharing"):
                if blank(privacy.get(key)):
                    self.add("SPEC-PRIV-03", "privacy." + key, "Com dado pessoal, `privacy.%s` deve ser preenchido pelo dono." % key)
            lb = privacy.get("legal_basis")
            if blank(lb):
                self.add("SPEC-PRIV-03", "privacy.legal_basis", "Com dado pessoal, `privacy.legal_basis` deve ter ao menos uma entrada decidida pelo dono.")
            elif isinstance(lb, list):
                for k, e in enumerate(lb):
                    if not isinstance(e, dict) or blank(e.get("purpose")) or blank(e.get("basis")):
                        self.add("SPEC-PRIV-03", "privacy.legal_basis[%d]" % k, "Cada base legal precisa de `purpose` e `basis`.")
            else:
                self.add("SPEC-PRIV-03", "privacy.legal_basis", "privacy.legal_basis deve ser uma lista de {purpose, basis}.")
            if privacy.get("decided_by") != "owner":
                self.add("SPEC-PRIV-03", "privacy.decided_by", "decided_by deve ser `owner`: o agente nunca decide base legal.")
            desc = norm(sdict(spec, "meta").get("description"))
            if not any(w in desc for w in PRIVACY_NOTICE_WORDS):
                self.add("SPEC-PRIV-04", "meta.description", "a descrição não parece trazer o aviso de privacidade (quem coleta, para quê, por quanto tempo, com quem, como exercer direitos).")
            if pdata in ("sensitive", "minors"):
                found = any("prefiro nao responder" in norm(o.get("value")) for _, it, _ in self.items
                            for o in (it.get("options") if isinstance(it.get("options"), list) else [])
                            if isinstance(o, dict))
                if not found:
                    self.add("SPEC-PRIV-08", "privacy.personal_data", "dado %s sem nenhuma opção \"Prefiro não responder\" nas perguntas sensíveis." % pdata)
        for p, it, _ in self.items:
            if it.get("type") not in QUESTION_TYPES:
                continue
            t = norm(it.get("title"))
            val = it.get("validation") if isinstance(it.get("validation"), dict) else {}
            if SENSITIVE_PERSONAL_RE.search(t):
                self.add("SPEC-PRIV-05", p + ".title", "o título pede dado sensível (%r); exige justificativa explícita do dono registrada no spec." % it.get("title"))
            if it.get("personal") is not True and it.get("id") not in inv_items and PERSONAL_HINT_RE.search(t):
                self.add("SPEC-PRIV-07", p + ".personal", "o item %s parece coletar dado pessoal (%r) mas está com personal: false." % (it.get("id"), it.get("title")))
            if email_on:
                if val.get("rule") == "email":
                    self.add("SPEC-PRIV-06", p + ".validation", "Pergunta de e-mail (validation email) com collect_email %s: o e-mail seria pedido duas vezes." % collect)
                elif EMAIL_TITLE_RE.search(t):
                    self.add("SPEC-PRIV-06", p + ".title", "o título cita e-mail e collect_email é %s; se for o e-mail do respondente, remova a pergunta." % collect, severity="aviso")

    # ---- dependências de configuração ----
    def check_settings_dependencies(self):
        spec = self.spec
        settings = sdict(spec, "settings")
        collect = self.collect_email
        sc = settings.get("send_copy")
        if sc not in (None, "never") and not is_pending(sc) and sc in ENUMS["send_copy"] and collect == "none":
            self.add("SPEC-CFG-02", "settings.send_copy", "send_copy %s exige collect_email diferente de none." % sc)
        quiz = sdict(spec, "quiz")
        if self.quiz_on and quiz.get("release") == "after_manual_review" and collect == "none":
            self.add("SPEC-QUIZ-06", "quiz.release", "after_manual_review exige collect_email diferente de none.")
        publish = sdict(spec, "publish")
        aud = publish.get("audience")
        if aud == "domain" and self.account_type != "workspace" and not is_pending(self.account_type):
            self.add("SPEC-CFG-03", "publish.audience", "audience: domain só com account_type: workspace (atual: %s)." % self.account_type)
        if aud == "specific" and blank(publish.get("responders")):
            self.add("SPEC-CFG-03", "publish.responders", "audience: specific exige responders (pessoas ou grupos).")
        if publish.get("published") is False:
            self.add("SPEC-CFG-06", "publish.published", "published: false: ninguém responde, nem com o link.")
        close = settings.get("close")
        if isinstance(close, dict):
            at, lim = close.get("at"), close.get("response_limit")
            if at is not None and lim is not None and not is_pending(at) and not is_pending(lim):
                self.add("SPEC-CFG-05", "settings.close", "Use um critério só de encerramento: at ou response_limit.")
            if at is not None and not is_pending(at) and not self.valid_iso_datetime(at):
                self.add("SPEC-CFG-05", "settings.close.at", "close.at deve ser data e hora ISO (ex.: 2026-12-01T18:00:00-03:00).")
            if lim is not None and not is_pending(lim) and (not is_int(lim) or lim < 1):
                self.add("SPEC-CFG-05", "settings.close.response_limit", "response_limit deve ser inteiro >= 1.")
        elif close is not None and not is_pending(close):
            self.add("SPEC-CFG-05", "settings.close", "settings.close deve ser {at, response_limit}.")
        theme = sdict(spec, "theme")
        for key in ("color", "background_color"):
            c = theme.get(key)
            if c is None or is_pending(c):
                continue
            if not isinstance(c, str) or not HEX_RE.match(c):
                self.add("SPEC-CFG-06", "theme." + key, "Cor %r inválida; use hex (#3f51b5)." % (c,))
            elif key == "color" and contrast_with_white(c) < 4.5:
                self.add("SPEC-CFG-06", "theme.color", "Cor %s tem contraste %.2f com texto branco (mínimo 4,5)." % (c, contrast_with_white(c)))
        needs_login = []
        if settings.get("limit_one_response") is True:
            needs_login.append("limit_one_response")
        if collect == "verified":
            needs_login.append("collect_email: verified")
        if any(it.get("type") == "file_upload" for _, it, _ in self.items):
            needs_login.append("file_upload")
        if needs_login:
            texts = [norm(sdict(spec, "meta").get("description"))] + [norm(it.get("description")) for _, it, _ in self.items]
            if not any(any(w in t for w in LOGIN_WORDS) for t in texts):
                self.add("SPEC-CFG-04", "meta.description", "o spec usa %s (exige login Google), mas nenhuma descrição avisa que é preciso entrar com conta Google." % ", ".join(needs_login))

    @staticmethod
    def valid_iso_datetime(value):
        if not isinstance(value, str):
            return False
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            datetime.datetime.fromisoformat(s)
        except ValueError:
            return False
        return "T" in s or " " in s

    # ---- caminho de construção ----
    def check_build_path(self):
        path = self.build_path
        if path not in ("apps_script", "api"):
            return
        spec = self.spec
        settings = sdict(spec, "settings")
        theme = sdict(spec, "theme")
        quiz = sdict(spec, "quiz")
        responses = sdict(spec, "responses")
        publish = sdict(spec, "publish")
        close = sdict(settings, "close")

        def used(v):
            return v is not None and v is not False and not is_pending(v) and v != ""

        ui_only = []
        for key in ("header_image", "color", "background_color", "font"):
            if used(theme.get(key)):
                ui_only.append(("theme." + key, "tema (%s)" % key))
        if used(settings.get("send_copy")) and settings.get("send_copy") != "never":
            ui_only.append(("settings.send_copy", "cópia ao respondente"))
        if used(close.get("at")) or used(close.get("response_limit")):
            ui_only.append(("settings.close", "encerramento automático"))
        if self.quiz_on and quiz.get("release") == "after_manual_review":
            ui_only.append(("quiz.release", "liberação da nota após revisão manual"))
        if settings.get("disable_autosave") is True:
            ui_only.append(("settings.disable_autosave", "desativar salvamento automático [não verificado no FormApp]"))
        for p_, desc in ui_only:
            if path == "apps_script":
                self.add("SPEC-BLD-03", p_, "PENDENTE_UI: %s só a interface aplica; com build.path apps_script fica para depois "
                         "(liste em meta.owner_notes e confira na verificação final)." % desc)
            else:
                self.add("SPEC-BLD-02", p_, "%s não existe na Forms API; use build.path: ui (ou apps_script + ajuste pela interface)." % desc)
        if path == "api":
            for key, label in (("allow_edit", "editar após envio"), ("limit_one_response", "limitar a 1 resposta"),
                               ("progress_bar", "barra de progresso"), ("shuffle_questions", "embaralhar perguntas"),
                               ("show_summary", "resumo dos resultados")):
                if settings.get(key) is True:
                    self.add("SPEC-BLD-02", "settings." + key, "%s não existe na Forms API; use build.path: ui ou apps_script." % label)
            if used(settings.get("confirmation_message")):
                self.add("SPEC-BLD-02", "settings.confirmation_message", "mensagem de confirmação não existe na Forms API; use build.path: ui ou apps_script.")
            if responses.get("sheet") in ("new", "existing"):
                self.add("SPEC-BLD-02", "responses.sheet", "a Forms API só lê a planilha (linkedSheetId); use build.path: ui ou apps_script.")
            for ipath, it, si in self.items:
                if it.get("validation") is not None:
                    self.add("SPEC-BLD-02", ipath + ".validation", "validação de resposta não existe na Forms API.")
                if sdict(it, "grid").get("one_per_column") is True:
                    self.add("SPEC-BLD-02", ipath + ".grid.one_per_column", "limite de uma resposta por coluna não existe na Forms API.")
            for si, (spath, sec, sid) in enumerate(self.sections):
                a = sec.get("after_section")
                if a is not None and a != "next" and not is_pending(a):
                    self.add("SPEC-BLD-02", spath + ".after_section", "a navegação por seção (after_section) não existe na Forms API (pageBreakItem não tem campos).")
            if publish.get("audience") in ("domain", "specific"):
                self.add("SPEC-BLD-08", "publish.audience", "audiência %s não é configurável na Forms API (só via Drive API ou interface) [não verificado o fluxo completo]." % publish.get("audience"))
        for ipath, it, si in self.items:
            if it.get("type") == "rating":
                self.add("SPEC-BLD-08", ipath, "rating: criação [não verificada] em %s; confirme antes de usar ou prefira build.path: ui." % path)
            if path == "apps_script" and sdict(it, "grid").get("shuffle_rows") is True:
                self.add("SPEC-BLD-07", ipath + ".grid.shuffle_rows", "PENDENTE_UI: embaralhar linhas da grade não tem método no FormApp [não verificado].")

    # ---- aprovação ----
    def check_approval(self):
        spec = self.spec
        status = spec.get("status")
        at = spec.get("approved_at")
        if status == "approved":
            if at is None or not self.valid_iso_date(at):
                self.add("SPEC-APR-02", "approved_at", "status approved exige approved_at com a data ISO da aprovação explícita (ex.: \"2026-11-11\").")
            if self.pending_paths:
                self.add("SPEC-APR-03", "status", "status approved mas há %d campo(s) pending_owner (%s); spec com pending_owner não pode ser aprovado."
                         % (len(self.pending_paths), ", ".join(self.pending_paths[:5]) + ("..." if len(self.pending_paths) > 5 else "")))
        elif not blank(at):
            self.add("SPEC-APR-05", "approved_at", "approved_at preenchido, mas o status é %r." % (status,))
        for p in self.pending_paths:
            self.add("SPEC-OWN-01", p, "decisão do dono pendente (pending_owner): pergunte ao dono antes de aprovar.")
        if self.for_build and status != "approved":
            self.add("SPEC-APR-04", "status", "--for-build exige status approved; o spec está %r. Apresente ao dono e aguarde a aprovação explícita." % (status,))

    @staticmethod
    def valid_iso_date(v):
        if not isinstance(v, str):
            return False
        try:
            datetime.date.fromisoformat(v.strip()[:10])
            return True
        except ValueError:
            return False


# --------------------------------------------------------------------------------------
# Entrada / saída
# --------------------------------------------------------------------------------------
DUP_KEY = "\0duplicates"


def result(ok, status, data, problems, next_steps):
    return {"ok": ok, "status": status, "data": data, "problems": problems, "next_steps": next_steps}


def import_yaml():
    try:
        import yaml
        return yaml
    except ImportError:
        return None


def _json_pairs(pairs):
    obj, dups = {}, []
    for k, v in pairs:
        if k in obj:
            dups.append(k)
        obj[k] = v
    if dups:
        obj[DUP_KEY] = dups
    return obj


def find_duplicates(node, path=""):
    out = []
    if isinstance(node, dict):
        for d in node.get(DUP_KEY, []):
            out.append("%s.%s" % (path, d) if path else d)
        for k, v in node.items():
            if k != DUP_KEY:
                out.extend(find_duplicates(v, "%s.%s" % (path, k) if path else str(k)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(find_duplicates(v, "%s[%d]" % (path, i)))
    return out


def plain(node):
    """Remove marcadores internos e normaliza datas do YAML (approved_at: 2026-11-11 sem aspas)."""
    if isinstance(node, dict):
        return {str(k): plain(v) for k, v in node.items() if k != DUP_KEY}
    if isinstance(node, list):
        return [plain(v) for v in node]
    if isinstance(node, (datetime.datetime, datetime.date)):
        return node.isoformat()
    return node


def usage_error(message, steps=None):
    return 2, result(False, "usage_error", {}, [message], steps or [])


def load_spec(path, yaml_module):
    """Devolve (erro_de_uso | None, dados | None, achados_de_entrada)."""
    if not os.path.isfile(path):
        return usage_error("Arquivo não encontrado: %s" % path, ["Confira o caminho do spec (.json, .yaml ou .yml)."]), None, []
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".json", ".yaml", ".yml"):
        return usage_error("Extensão %r não suportada (use .json, .yaml ou .yml)." % ext,
                           ["Converta o spec para JSON ou renomeie o arquivo."]), None, []
    try:
        with open(path, "rb") as fh:
            raw = fh.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return usage_error("Não consegui ler %s como UTF-8: %s" % (path, exc)), None, []
    extra = []
    if ext == ".json":
        try:
            data = json.loads(raw, object_pairs_hook=_json_pairs)
        except ValueError as exc:
            return None, None, [("SPEC-IO-01", "(arquivo)", "JSON inválido: %s" % exc)]
        extra = [("SPEC-IO-02", d, "Chave duplicada no JSON: a última sobrescreve a anterior.") for d in find_duplicates(data)]
    else:
        if yaml_module is None:
            return usage_error(
                "PyYAML não está instalado e este script não traz parser YAML próprio.",
                ["Escreva o spec em JSON (a skill aceita .json) e rode no .json.",
                 "Ou instale a dependência: python3 -m pip install --user pyyaml (Windows: py -3 -m pip install --user pyyaml). Se o Python for gerenciado pelo sistema (erro externally-managed-environment): python3 -m venv .venv && .venv/bin/pip install pyyaml (Windows: .venv\\Scripts\\pip) e rode o validador com .venv/bin/python (Windows: .venv\\Scripts\\python)."]), None, []
        try:
            data = yaml_module.safe_load(raw)
        except Exception as exc:  # yaml.YAMLError e variantes
            return None, None, [("SPEC-IO-01", "(arquivo)", "YAML inválido: %s" % str(exc).replace("\n", " "))]
    data = plain(data)
    if not isinstance(data, dict):
        return None, None, [("SPEC-IO-01", "(raiz)", "A raiz do spec deve ser um objeto (mapa), não %s." % type(data).__name__)]
    return None, data, extra


def counts_for(checker, findings):
    return {
        "sections": len(checker.sections),
        "items": len(checker.items),
        "questions": sum(1 for _, it, _ in checker.items if it.get("type") in QUESTION_TYPES),
        "errors": sum(1 for f in findings if f["severidade"] == "erro"),
        "warnings": sum(1 for f in findings if f["severidade"] == "aviso"),
        "pending_ui": sum(1 for f in findings if f.get("pendente_ui")),
        "pending_owner": len(checker.pending_paths),
    }


def build_payload(path, spec, input_findings, for_build):
    findings = [{"id_regra": r, "severidade": "erro", "caminho": p, "mensagem": m} for r, p, m in input_findings]
    checker = Checker(spec if spec is not None else {}, for_build)
    spec_status = None
    if spec is not None:
        findings += checker.run()
        spec_status = spec.get("status")
    hard_errors = [f for f in findings if f["severidade"] == "erro" and f["id_regra"] != "SPEC-APR-04"]
    not_approved = any(f["id_regra"] == "SPEC-APR-04" for f in findings)
    if hard_errors:
        status = "invalid"
    elif checker.pending_paths:
        status = "pending_owner"
    elif not_approved:
        status = "invalid"
    elif findings:
        status = "valid_with_warnings"
    else:
        status = "valid"
    ok = status in ("valid", "valid_with_warnings")
    problems = ["[%s] %s: %s" % (f["id_regra"], f["caminho"], f["mensagem"]) for f in findings if f["severidade"] == "erro"]
    if status == "pending_owner":
        problems += ["[SPEC-OWN-01] %s: decisão do dono pendente." % p for p in checker.pending_paths]
    data = {
        "file": path,
        "spec_status": spec_status,
        "for_build": for_build,
        "counts": counts_for(checker, findings),
        "findings": findings,
        "pending_owner": list(checker.pending_paths),
        "pending_ui": [{"caminho": f["caminho"], "id_regra": f["id_regra"], "mensagem": f["mensagem"]}
                       for f in findings if f.get("pendente_ui")],
        "section_graph": checker.reach.get("edges", {}),
    }
    steps = []
    if status == "invalid":
        if not_approved and not hard_errors:
            steps.append("O spec está correto mas ainda não aprovado: apresente ao dono (FORM-SPEC.md, \"Como apresentar o spec para aprovação\") e, só após a aprovação explícita, ponha status: approved e approved_at.")
        else:
            steps.append("Corrija cada erro listado em `problems` (ou transforme em pergunta ao dono) e rode o validador de novo.")
    elif status == "pending_owner":
        steps.append("Pergunte ao dono cada campo `pending_owner` (data.pending_owner): base legal, controlador, contato, retenção e compartilhamento são decisões dele, nunca do agente. Sem resposta, ofereça o formulário sem dado pessoal.")
    elif status == "valid_with_warnings":
        steps.append("Leia os avisos: heurísticas pedem julgamento humano; PENDENTE_UI entra na lista de ajustes manuais da entrega.")
    if ok and not for_build:
        steps.append("Antes de construir, rode de novo com --for-build (exige status approved).")
    if ok and for_build:
        steps.append("Spec aprovado e válido: pode construir pelo caminho build.path.")
    return (0 if ok else 1), result(ok, status, data, problems, steps)


def render_text(payload):
    d = payload["data"]
    lines = ["Status: %s (ok=%s)" % (payload["status"], str(payload["ok"]).lower())]
    if "file" in d:
        c = d.get("counts", {})
        lines.append("Arquivo: %s" % d["file"])
        lines.append("Seções: %s | Itens: %s | Perguntas: %s | Erros: %s | Avisos: %s | PENDENTE_UI: %s | pending_owner: %s" % (
            c.get("sections"), c.get("items"), c.get("questions"), c.get("errors"), c.get("warnings"),
            c.get("pending_ui"), c.get("pending_owner")))
        for f in d.get("findings", []):
            tag = "ERRO " if f["severidade"] == "erro" else "AVISO"
            lines.append("  %s %s %s: %s" % (tag, f["id_regra"], f["caminho"], f["mensagem"]))
    elif "rules" in d:
        for rid, sev, desc in d["rules"]:
            lines.append("  %s [%s] %s" % (rid, sev, desc))
    else:
        for p in payload["problems"]:
            lines.append("Problema: %s" % p)
    for s in payload["next_steps"]:
        lines.append("Próximo passo: %s" % s)
    return "\n".join(lines) + "\n"


def emit(payload, fmt="json"):
    out = render_text(payload) if fmt == "text" else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        sys.stdout.write(out)
    except UnicodeEncodeError:  # console Windows sem UTF-8
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


class _Parser(argparse.ArgumentParser):
    """argparse que devolve JSON de erro de uso (exit 2) em vez de texto; ajuda em pt-BR."""

    def __init__(self, *args, **kwargs):
        kwargs["add_help"] = False
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")

    def format_help(self):
        text = super().format_help()
        for en, pt in (("usage:", "uso:"), ("positional arguments:", "argumentos posicionais:"),
                       ("optional arguments:", "opções:"), ("options:", "opções:")):
            text = text.replace(en, pt, 1) if en in text else text
        return text

    def error(self, message):
        emit(result(False, "usage_error", {}, ["Uso inválido: %s" % message], [self.format_usage().strip()]))
        sys.exit(2)


def rules_payload():
    rules = [[rid, sev, desc] for rid, (sev, desc) in sorted(RULES.items())]
    return result(True, "valid", {"rules": rules, "pending_ui_rules": sorted(PENDING_UI_RULES),
                                  "heuristic_rules": sorted(HEURISTIC_RULES)}, [], [])


def main(argv=None, yaml_module=False):
    """`yaml_module=False` (padrão) tenta importar PyYAML; os testes injetam um módulo ou None."""
    ap = _Parser(description="Valida um FORM-SPEC (JSON ou YAML) de forma determinística.")
    ap.add_argument("spec", nargs="?", help="caminho do spec (.json, .yaml, .yml)")
    ap.add_argument("--for-build", action="store_true", help="exige status approved (usar antes de construir)")
    ap.add_argument("--format", default="json", choices=["json", "text"], help="formato da saída (padrão: json)")
    ap.add_argument("--rules", action="store_true", help="lista o catálogo de ids de regra e sai")
    args = ap.parse_args(argv)
    if args.rules:
        emit(rules_payload(), args.format)
        return 0
    if not args.spec:
        code, payload = usage_error("Informe o caminho do spec.", ["python3 <pasta-da-skill>/scripts/validate_spec.py SPEC.json [--for-build] [--format text] (Windows: py -3 ...)"])
        emit(payload, args.format)
        return code
    ymod = import_yaml() if yaml_module is False else yaml_module
    err, data, extra = load_spec(args.spec, ymod)
    if err:
        emit(err[1], args.format)
        return err[0]
    code, payload = build_payload(args.spec, data, extra, args.for_build)
    emit(payload, args.format)
    return code


if __name__ == "__main__":
    sys.exit(main())
