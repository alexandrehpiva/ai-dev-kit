#!/usr/bin/env python3
"""Valida o dicionário de eventos GA4 (CSV) contra os limites e regras oficiais. Stdlib pura, Python 3.9+.

Uso:
  python3 lint_event_dictionary.py dicionario.csv [--pii-terms termos.txt] [--allow document_type ...]
                                   [--max-key-events 5] [--warn-params 20] [--json]

Saída: JSON em stdout com `ok`, `problems` (erros, exit 1) e `warnings` (exit 0).
Exit 0 = sem erros; 1 = há erros; 2 = uso incorreto (arquivo ausente/ilegível).

Colunas obrigatórias do CSV: ver REQUIRED_COLUMNS. O campo `parameters` lista os parâmetros separados por `;`,
cada um como `nome` ou `nome:tipo` (o tipo é ignorado pelo lint).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------------------------------------
# LIMITES E REGRAS OFICIAIS — constante única. Fonte e data de acesso da pesquisa: 2026-11-16.
#   Limites de coleta (nome 40, parâmetros 25, nome de parâmetro 40, valor 100): https://support.google.com/analytics/answer/9267744
#   Regras de nome (letra inicial, letras/números/underscore, maiúsculas distintas): https://support.google.com/analytics/answer/13316687
#   Prefixos e nomes reservados: https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference
# Reconfirme na documentação vigente antes de publicar números (ver ga4-rules.md). A lista de reservados NÃO é exaustiva.
# ---------------------------------------------------------------------------------------------------------
LIMITS = {
    "event_name_max": 40,
    "param_name_max": 40,
    "params_per_event_max": 25,
}
FORBIDDEN_PREFIXES = ("_", "firebase_", "ga_", "google_", "gtag.")  # fonte: 13316687 + protocol reference
# [não confirmado] se todos valem também para nome de evento (a fonte os lista para parâmetros); aplicados por prudência.
RESERVED_EVENT_PREFIXES = ("dynamic_link_", "notification_", "firebase_")
RESERVED_EVENTS = {
    "ad_activeview", "ad_click", "ad_exposure", "ad_query", "ad_reward", "adunit_exposure", "app_clear_data",
    "app_exception", "app_install", "app_remove", "app_store_refund", "app_update", "app_upgrade", "error",
    "first_open", "first_visit", "os_update", "session_start", "user_engagement",
}
RESERVED_PARAMS = {"firebase_conversion"}
PARAMS_NOT_FOR_CUSTOM = {"currency", "user_id", "session_id"}  # 13316687: não servem como dimensão personalizada
# Eventos recomendados conhecidos (lista PARCIAL, lida em 2026-11-16); fora dela só gera aviso.
KNOWN_RECOMMENDED = {
    "login", "sign_up", "share", "search", "generate_lead", "qualify_lead", "disqualify_lead", "working_lead",
    "close_convert_lead", "close_unconvert_lead", "tutorial_begin", "tutorial_complete",
}
# ---------------------------------------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "id", "event_name", "event_type", "description", "when_fires", "gtm_trigger", "parameters", "key_event",
    "kpi", "owner", "implementer", "consent_required", "pii_reviewed", "acceptance_criteria", "status", "plan_version",
]
MUST_FILL = ["id", "event_name", "event_type", "when_fires", "gtm_trigger", "key_event", "owner", "acceptance_criteria", "status"]
EVENT_TYPES = {"automatic", "enhanced", "recommended", "custom"}
YES_NO = {"yes", "no", "sim", "nao", "não"}
SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
VALID_PARAM = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

# Termos (tokens do nome do parâmetro separados por "_") suspeitos de PII — configurável com --pii-terms.
DEFAULT_PII_TERMS = {
    "cpf", "cnpj", "rg", "cnh", "ssn", "passport", "passaporte", "email", "mail", "phone", "telefone", "celular",
    "fone", "whatsapp", "document", "documento", "address", "endereco", "logradouro", "cep", "zip", "postal",
    "birth", "birthday", "nascimento", "dob", "password", "senha", "latitude", "longitude", "lat", "lng",
    "nome", "name",
}
# `name`/`nome` só são suspeitos sozinhos ou acompanhados de uma palavra de pessoa (step_name, flow_name NÃO são).
PERSON_WORDS = {"first", "last", "full", "user", "customer", "person", "partner", "socio", "client", "cliente",
                "mother", "father", "mae", "pai", "legal", "holder", "titular", "company", "empresa", "razao"}
DEFAULT_ALLOW = {"document_type", "document_count", "documents_count", "document_status"}


def split_params(raw):
    out = []
    for item in (raw or "").split(";"):
        item = item.strip()
        if item:
            out.append(item.split(":", 1)[0].strip())
    return out


def pii_suspect(param, terms, allow):
    if param in allow:
        return None
    tokens = param.lower().split("_")
    for t in tokens:
        if t in ("name", "nome"):
            if len(tokens) == 1 or any(w in PERSON_WORDS for w in tokens):
                return t
            continue
        if t in terms:
            return t
    return None


def lint(rows, terms, allow, max_key_events, warn_params):
    problems, warnings = [], []

    def add(bucket, row, code, msg):
        bucket.append({"row": row["_line"], "id": row.get("id", ""), "event_name": row.get("event_name", ""),
                       "code": code, "message": msg})

    seen_ids, seen_names, key_events = {}, {}, 0
    for r in rows:
        name = (r.get("event_name") or "").strip()
        etype = (r.get("event_type") or "").strip().lower()
        for col in MUST_FILL:
            if not (r.get(col) or "").strip():
                add(problems, r, "missing_field", "coluna obrigatória vazia: %s" % col)
        if etype and etype not in EVENT_TYPES:
            add(problems, r, "bad_event_type", "event_type '%s' inválido (use %s)" % (etype, "/".join(sorted(EVENT_TYPES))))
        if (r.get("key_event") or "").strip().lower() not in YES_NO and (r.get("key_event") or "").strip():
            add(problems, r, "bad_key_event", "key_event deve ser yes/no (ou sim/não)")
        if (r.get("key_event") or "").strip().lower() in ("yes", "sim"):
            key_events += 1
        if not (r.get("description") or "").strip():
            add(warnings, r, "no_description", "descrição vazia")
        if not (r.get("pii_reviewed") or "").strip():
            add(warnings, r, "pii_not_reviewed", "pii_reviewed vazio: registre data e responsável da revisão de PII")
        if not (r.get("kpi") or "").strip():
            add(warnings, r, "orphan_event", "evento sem KPI/pergunta de negócio associado (evento órfão)")
        if not (r.get("implementer") or "").strip():
            add(warnings, r, "no_implementer", "implementador não informado")

        rid = (r.get("id") or "").strip()
        if rid:
            if rid in seen_ids:
                add(problems, r, "duplicate_id", "id repetido (linha %d)" % seen_ids[rid])
            seen_ids.setdefault(rid, r["_line"])

        if name:
            automatic = etype == "automatic"
            if len(name) > LIMITS["event_name_max"]:
                add(problems, r, "event_name_too_long", "nome com %d caracteres (limite %d)" % (len(name), LIMITS["event_name_max"]))
            if not SNAKE.match(name):
                add(problems, r, "not_snake_case", "nome fora de snake_case minúsculo (letra inicial; a-z, 0-9, _)")
            if not automatic:
                if name in RESERVED_EVENTS:
                    add(problems, r, "reserved_event", "nome reservado pelo GA4")
                for p in FORBIDDEN_PREFIXES + RESERVED_EVENT_PREFIXES:
                    if name.startswith(p):
                        add(problems, r, "forbidden_prefix", "prefixo proibido/reservado '%s'" % p)
                        break
            if name == "screen_view":
                add(warnings, r, "screen_view_web", "screen_view é evento de app; em web use page_view")
            if etype == "recommended" and name not in KNOWN_RECOMMENDED:
                add(warnings, r, "recommended_unknown",
                    "confirme na lista oficial de eventos recomendados (a lista do lint é parcial)")
            key = name
            if key in seen_names:
                add(problems, r, "duplicate_event", "event_name repetido (linha %d)" % seen_names[key])
            seen_names.setdefault(key, r["_line"])

        params = split_params(r.get("parameters"))
        if len(params) > LIMITS["params_per_event_max"]:
            add(problems, r, "too_many_params", "%d parâmetros (limite %d)" % (len(params), LIMITS["params_per_event_max"]))
        elif len(params) > warn_params:
            add(warnings, r, "many_params", "%d parâmetros: perto do limite %d" % (len(params), LIMITS["params_per_event_max"]))
        seen_p = set()
        for p in params:
            if p in seen_p:
                add(problems, r, "duplicate_param", "parâmetro repetido no evento: %s" % p)
            seen_p.add(p)
            if not VALID_PARAM.match(p):
                add(problems, r, "bad_param_name", "nome de parâmetro inválido: '%s' (letra inicial; letras, números, _)" % p)
                continue
            if len(p) > LIMITS["param_name_max"]:
                add(problems, r, "param_name_too_long", "%s: %d caracteres (limite %d)" % (p, len(p), LIMITS["param_name_max"]))
            for pre in FORBIDDEN_PREFIXES:
                if p.startswith(pre):
                    add(problems, r, "forbidden_param_prefix", "%s: prefixo proibido '%s'" % (p, pre))
                    break
            if p in RESERVED_PARAMS:
                add(problems, r, "reserved_param", "parâmetro reservado: %s" % p)
            if p in PARAMS_NOT_FOR_CUSTOM:
                add(warnings, r, "param_not_custom_dimension",
                    "%s não serve como dimensão personalizada; use o recurso próprio (ex.: user_id como config)" % p)
            hit = pii_suspect(p, terms, allow)
            if hit:
                add(problems, r, "pii_param", "%s: nome suspeito de PII (termo '%s'); use valor categorizado/ID opaco ou --allow" % (p, hit))
    if key_events > max_key_events:
        warnings.append({"row": 0, "id": "", "event_name": "", "code": "many_key_events",
                         "message": "%d key events (heurística do kit: poucos, só sucesso de negócio; limite sugerido %d)"
                                    % (key_events, max_key_events)})
    if not rows:
        problems.append({"row": 0, "id": "", "event_name": "", "code": "empty", "message": "dicionário sem linhas"})
    return problems, warnings


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
                continue
            row["_line"] = i
            rows.append(row)
    return cols, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--pii-terms", help="arquivo com termos PII adicionais (um por linha)")
    ap.add_argument("--allow", nargs="*", default=[], help="nomes de parâmetro liberados do teste de PII")
    ap.add_argument("--max-key-events", type=int, default=5)
    ap.add_argument("--warn-params", type=int, default=20)
    ap.add_argument("--json", action="store_true", help="(padrão) saída JSON; mantido por compatibilidade")
    a = ap.parse_args(argv)
    p = Path(a.csv)
    if not p.is_file():
        print(json.dumps({"ok": False, "problems": [{"code": "no_file", "message": "arquivo não encontrado: %s" % p}], "warnings": []}))
        return 2
    terms = set(DEFAULT_PII_TERMS)
    if a.pii_terms:
        tp = Path(a.pii_terms)
        if not tp.is_file():
            print(json.dumps({"ok": False, "problems": [{"code": "no_file", "message": "--pii-terms não encontrado: %s" % tp}], "warnings": []}))
            return 2
        terms |= {l.strip().lower() for l in tp.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
    try:
        cols, rows = load(p)
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        print(json.dumps({"ok": False, "problems": [{"code": "unreadable", "message": str(e)}], "warnings": []}))
        return 2
    missing = [c for c in REQUIRED_COLUMNS if c not in cols]
    if missing:
        out = {"ok": False, "problems": [{"row": 1, "code": "missing_columns", "message": "colunas ausentes: " + ", ".join(missing)}],
               "warnings": []}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1
    problems, warnings = lint(rows, terms, set(DEFAULT_ALLOW) | set(a.allow), a.max_key_events, a.warn_params)
    out = {"ok": not problems, "events": len(rows), "problems": problems, "warnings": warnings}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
