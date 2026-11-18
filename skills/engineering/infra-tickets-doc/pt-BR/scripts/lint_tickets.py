#!/usr/bin/env python3
"""Lint da especificação JSON do lote de chamados (stdlib pura).

Uso:  python3 lint_tickets.py <spec.json> [--max-item 300]

Erros (saída 1): aspas angulares, código repetido, chamado sem texto, deploy sem "Build e deploy"
completo, JSON inválido em bloco, segredo aparente, política com Action curinga.
Avisos (saída 0): tópico longo, frase de bastidor ou padrão do provedor, nome de outro ambiente,
falta de "Preciso de volta" nos casos que devolvem algo, Resource curinga com escrita, sem solicitante.
É heurístico: não substitui a releitura nem o revisor SRE.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ANGLE_QUOTES = ("«", "»")

DEPLOY_KEYWORDS = {
    "repositório": re.compile(r"reposit[óo]rio", re.I),
    "Dockerfile": re.compile(r"dockerfile", re.I),
    "imagem": re.compile(r"imag(em|ens)|image", re.I),
    "entrypoint/command": re.compile(r"entrypoint|command", re.I),
    "variáveis por Deployment": re.compile(r"vari[áa]ve", re.I),
    "branch": re.compile(r"branch", re.I),
}
CONTAINER_HINT = re.compile(r"deployment|helm|kubernetes|\beks\b|\bgke\b|\baks\b|contêiner|container|docker", re.I)
RETURN_CASES = {"relational-database", "encryption-keys", "static-site-cdn", "kubernetes-deploy", "api-gateway", "cache"}

BACKSTAGE_PHRASES = [
    "nunca por chamado", "nunca por chat", "a aplicação não precisa", "pode abrir sem esperar",
    "é opcional", "(opcional", "pode esperar", "de propósito", "a grafia", "uso exclusivo desse",
    "janela de exclusão", "rotação desligada", "sem eventos de dados", "sem object lock",
    "sem job de migration", "max_connections", "política de tls",
]

SECRET_PATTERNS = [
    ("chave de acesso AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("token GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("token Slack", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b")),
    ("senha em texto", re.compile(r"\b(password|senha|secret)\s*[:=]\s*[\"']?[^\s\"'<\[]{6,}", re.I)),
]

ENV_LEAK = {
    "hml": re.compile(r"[-/_.](prd|prod)\b", re.I),
    "prd": re.compile(r"[-/_.](hml|homolog)\b", re.I),
}

READ_PREFIXES = ("list", "describe", "get", "head")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append("ERRO %s: %s" % (where, msg))

    def warn(self, where, msg):
        self.warnings.append("AVISO %s: %s" % (where, msg))


def iter_items(items):
    """Percorre tópicos aninhados devolvendo (tipo, valor)."""
    for item in items:
        if isinstance(item, str):
            yield "text", item
        elif isinstance(item, dict):
            if "code" in item:
                yield "code", item["code"]
            if "text" in item:
                yield "text", item["text"]
            if "group" in item:
                yield "text", item["group"]
                yield from iter_items(item.get("items", []))


def section_text(section):
    return "\n".join([section.get("title", "")] + [v for _, v in iter_items(section.get("items", []))])


def ticket_sections(ticket):
    if ticket.get("kind") == "note":
        return ticket.get("sections", [])
    return (ticket.get("paste") or {}).get("sections", [])


def ticket_text(ticket):
    paste = ticket.get("paste") or {}
    parts = [paste.get("lead", "")] + [section_text(s) for s in ticket_sections(ticket)]
    return "\n".join(parts)


def check_json_block(where, code, report):
    stripped = code.strip()
    if not stripped.startswith(("{", "[")):
        return
    try:
        doc = json.loads(stripped)
    except json.JSONDecodeError as exc:
        report.error(where, "bloco JSON inválido (%s)" % exc)
        return
    statements = doc.get("Statement", []) if isinstance(doc, dict) else []
    if isinstance(statements, dict):
        statements = [statements]
    for st in statements:
        if not isinstance(st, dict) or st.get("Effect") != "Allow":
            continue
        actions = st.get("Action", [])
        actions = [actions] if isinstance(actions, str) else actions
        resources = st.get("Resource", [])
        resources = [resources] if isinstance(resources, str) else resources
        if any(a == "*" or a.endswith(":*") for a in actions):
            report.error(where, "política com Action curinga (%s); peça ações exatas" % st.get("Sid", "sem Sid"))
        if "*" in resources:
            writes = [a for a in actions if not a.split(":")[-1].lower().startswith(READ_PREFIXES)]
            if writes:
                report.warn(where, "Resource \"*\" com ações de escrita %s; restrinja por ARN" % writes)


def check_build_and_deploy(code, ticket, report):
    case = ticket.get("case", "")
    text = ticket_text(ticket)
    needs = case == "kubernetes-deploy" or (case == "ci-cd-pipeline" and CONTAINER_HINT.search(text))
    if not needs:
        return
    sections = [s for s in ticket_sections(ticket) if s.get("title", "").strip().lower() == "build e deploy"]
    if not sections:
        report.error(code, "chamado de deploy sem a seção \"Build e deploy\" (repositório, Dockerfile, imagens, "
                           "entrypoint, variáveis por Deployment, branch)")
        return
    body = section_text(sections[0])
    missing = [name for name, rx in DEPLOY_KEYWORDS.items() if not rx.search(body)]
    if missing:
        report.error(code, "seção \"Build e deploy\" incompleta; falta: %s" % ", ".join(missing))


def lint(spec, raw_text="", max_item=300):
    report = Report()
    for quote in ANGLE_QUOTES:
        if quote in raw_text:
            report.error("documento", "aspas angulares encontradas; use aspas duplas comuns")
            break

    env = (spec.get("document") or {}).get("environment", "")
    if not spec.get("requester"):
        report.warn("documento", "sem solicitante (requester); o rodapé dos textos fica vazio")

    seen = set()
    pending = 0
    for ticket in spec.get("tickets", []):
        code = ticket.get("code", "?")
        if code in seen:
            report.error(code, "código de chamado repetido")
        seen.add(code)
        kind = ticket.get("kind", "new")
        if kind != "note":
            paste = ticket.get("paste") or {}
            if not paste.get("lead") or not paste.get("sections"):
                report.error(code, "chamado sem \"Texto para colar\" (lead e ao menos uma seção)")
                continue
            if len(paste["lead"]) > max_item + 100:
                report.warn(code, "primeira frase longa (%d caracteres); diga o pedido em uma frase" % len(paste["lead"]))

        text = ticket_text(ticket)
        pending += len(re.findall(r"\[A CONFIRMAR", text))
        lowered = text.lower()
        for phrase in BACKSTAGE_PHRASES:
            if phrase in lowered:
                report.warn(code, "frase de bastidor ou padrão do provedor: \"%s\"" % phrase)
        for label, rx in SECRET_PATTERNS:
            if rx.search(text):
                report.error(code, "possível segredo (%s); chamado leva nomes, nunca valores" % label)
        if env in ENV_LEAK and ENV_LEAK[env].search(text):
            report.warn(code, "nome de outro ambiente no texto de %s: %s" % (env, ENV_LEAK[env].search(text).group(0)))

        for section in ticket_sections(ticket):
            for kind_item, value in iter_items(section.get("items", [])):
                if kind_item == "code":
                    check_json_block(code, value, report)
                elif len(value) > max_item:
                    report.warn(code, "tópico longo (%d caracteres) em \"%s\"; quebre em um fato por linha"
                                % (len(value), section.get("title", "")))

        check_build_and_deploy(code, ticket, report)
        if kind != "note" and ticket.get("case") in RETURN_CASES:
            titles = [s.get("title", "").strip().lower() for s in ticket_sections(ticket)]
            if "preciso de volta" not in titles:
                report.warn(code, "caso %s costuma devolver algo; falta a seção \"Preciso de volta\"" % ticket.get("case"))
    return report, pending


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint do lote de chamados (JSON).")
    parser.add_argument("spec")
    parser.add_argument("--max-item", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        raw = Path(args.spec).read_text(encoding="utf-8")
        spec = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print("ERRO: não consegui ler a especificação: %s" % exc)
        return 1
    report, pending = lint(spec, raw, args.max_item)
    for line in report.errors + report.warnings:
        print(line)
    print("Resumo: %d erro(s), %d aviso(s), %d pendência(s) [A CONFIRMAR]."
          % (len(report.errors), len(report.warnings), pending))
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
