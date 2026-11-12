#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passo 0 da skill google-forms: adaptador fino sobre o check_setup.py da skill playwright-mcp.

Uso:
    python3 scripts/check_setup.py [--harness auto|claude|cursor|vscode|codex|gemini|windsurf]
                                   [--server-name playwright-browser] [--project-dir <pasta>]
    (Windows: py -3 scripts\\check_setup.py ...)

A instalação, o registro e a verificação do Playwright MCP são da skill `playwright-mcp`. Este
script apenas:
  1. localiza o scripts/check_setup.py dela (ordem: variável GFORMS_PLAYWRIGHT_MCP_DIR; pasta irmã
     `playwright-mcp` ao lado da pasta desta skill; layout do repositório
     ../../playwright-mcp/pt-BR a partir desta skill);
  2. roda-o como subprocesso, com o mesmo interpretador e `-I -B`, sempre com `--mode extension`
     (a skill google-forms só usa o modo extensão), repassando --harness, --server-name e
     --project-dir; o ambiente (inclusive PLAYWRIGHT_MCP_EXTENSION_TOKEN) é herdado, e o valor do
     token nunca é lido aqui;
  3. devolve o mesmo contrato {"ok","status","data","problems","next_steps"} e os mesmos códigos de
     saída, acrescentando o que é do Forms: data.optional.pyyaml (+ problema e próximo passo quando
     falta PyYAML; nunca muda o status), o aviso de pasta-da-skill como raiz do projeto, e o próximo
     passo de `ready` (abrir https://docs.google.com/forms/u/0/ e conferir a lista de formulários).

Status do playwright-mcp repassados sem alteração: node_missing | node_too_old | browser_issue |
    mcp_not_registered | token_missing | ready | usage_error.
Status próprios deste adaptador: playwright_mcp_missing (a skill playwright-mcp não foi achada;
    instale-a) | playwright_mcp_error (o check_setup.py dela não rodou ou não devolveu JSON).
Códigos de saída: 0 = ready; 1 = problema acionável; 2 = erro de uso.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)

PM_ENV = "GFORMS_PLAYWRIGHT_MCP_DIR"
PM_SCRIPT = os.path.join("scripts", "check_setup.py")
PM_TIMEOUT = 120
FORMS_URL = "https://docs.google.com/forms/u/0/"
PM_SKILL_FILES = "setup.md, extension-mode.md, harnesses.md e troubleshooting.md"
INSTALL_HINT = ("ai-dev-kit skills install --skills productivity/playwright-mcp --target claude "
                "(Cursor: --target cursor)")


class Context(object):
    """Ambiente da execução (injetável nos testes): variáveis de ambiente e pasta desta skill."""

    def __init__(self, environ=None, skill_dir=None):
        self.environ = dict(os.environ) if environ is None else dict(environ)
        self.skill_dir = skill_dir or SKILL_DIR


def result(ok, status, data, problems, next_steps):
    return {"ok": ok, "status": status, "data": data, "problems": problems, "next_steps": next_steps}


def emit(payload):
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        sys.stdout.write(out + "\n")
    except UnicodeEncodeError:  # console Windows sem UTF-8
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


class _Parser(argparse.ArgumentParser):
    """argparse que devolve JSON de erro de uso (exit 2) em vez de texto; ajuda em pt-BR."""

    def __init__(self, *args, **kwargs):
        kwargs["add_help"] = False
        super(_Parser, self).__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")

    def format_help(self):
        text = super(_Parser, self).format_help()
        for en, pt in (("usage:", "uso:"), ("optional arguments:", "opções:"), ("options:", "opções:")):
            text = text.replace(en, pt, 1) if en in text else text
        return text

    def error(self, message):
        emit(result(False, "usage_error", {}, ["Uso inválido: %s" % message], [self.format_usage().strip()]))
        sys.exit(2)


# ---------------------------------------------------------------------------
# Localização da skill playwright-mcp
# ---------------------------------------------------------------------------

def _has_check_setup(path):
    return os.path.isfile(os.path.join(path, PM_SCRIPT))


def candidate_dirs(skill_dir):
    """Pastas candidatas, da instalada (irmã) à do repositório, com e sem resolver symlinks."""
    bases = []
    for b in (os.path.abspath(skill_dir), os.path.realpath(skill_dir)):
        if b not in bases:
            bases.append(b)
    out = []
    for b in bases:
        parent = os.path.dirname(b)
        for cand in (os.path.join(parent, "playwright-mcp"),
                     os.path.join(os.path.dirname(parent), "playwright-mcp", "pt-BR")):
            cand = os.path.normpath(cand)
            if cand not in out:
                out.append(cand)
    return out


def find_playwright_mcp(environ, skill_dir):
    """Devolve (pasta|None, erro|None, tentativas). Variável inválida é erro: nunca cai em outro caminho."""
    override = (environ.get(PM_ENV) or "").strip()
    if override:
        path = os.path.abspath(os.path.expanduser(override))
        if _has_check_setup(path):
            return path, None, [path]
        return None, ("%s aponta para %s, que não tem %s (a pasta da skill playwright-mcp)."
                      % (PM_ENV, path, PM_SCRIPT.replace(os.sep, "/"))), [path]
    tried = candidate_dirs(skill_dir)
    for cand in tried:
        if _has_check_setup(cand):
            return cand, None, tried
    return None, None, tried


# ---------------------------------------------------------------------------
# Execução e adaptação
# ---------------------------------------------------------------------------

def run_playwright_mcp(pm_dir, forwarded, environ, timeout=PM_TIMEOUT):
    """Roda o check_setup.py da playwright-mcp. Devolve (exit, payload|None, erro|None)."""
    cmd = [sys.executable, "-I", "-B", os.path.join(pm_dir, PM_SCRIPT), "--mode", "extension"] + forwarded
    try:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                            env=dict(environ), check=False)
    except subprocess.TimeoutExpired:
        return None, None, "o check_setup.py da skill playwright-mcp passou de %d s sem responder." % timeout
    except OSError as exc:
        return None, None, "não consegui executar o check_setup.py da skill playwright-mcp (%s)." % exc
    out = cp.stdout.decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(out)
    except ValueError:
        tail = cp.stderr.decode("utf-8", errors="replace").strip()[-400:]
        return cp.returncode, None, ("o check_setup.py da skill playwright-mcp terminou com código %s e não "
                                     "devolveu JSON%s." % (cp.returncode, (": " + tail) if tail else ""))
    if not isinstance(payload, dict) or "status" not in payload:
        return cp.returncode, None, "a saída do check_setup.py da skill playwright-mcp não tem o contrato esperado."
    return cp.returncode, payload, None


def pyyaml_available():
    """True se o Python que roda este script enxerga o PyYAML (o validate_spec.py usa o mesmo python3)."""
    try:
        return importlib.util.find_spec("yaml") is not None
    except (ImportError, ValueError):
        return False


def inside_skill_dir(path, skill_dir):
    """True se `path` é a pasta desta skill ou está dentro dela."""
    if not path or not os.path.isabs(path):
        return False
    base = os.path.normcase(os.path.realpath(skill_dir))
    cand = os.path.normcase(os.path.realpath(path))
    try:
        return os.path.commonpath([base, cand]) == base
    except ValueError:  # unidades diferentes no Windows
        return False


_SCRIPT_REF = re.compile(r"(?<![\w/\\.-])(configure_mcp|detect_browser|clone_profile)\.py")


def _qualify(text, pm_dir):
    """Troca `configure_mcp.py` (e afins) pelo caminho real na skill playwright-mcp, para o comando rodar."""
    return _SCRIPT_REF.sub(lambda m: '"%s"' % os.path.join(pm_dir, "scripts", m.group(1) + ".py"), text)


def pyyaml_items(data, problems, next_steps):
    if pyyaml_available():
        data["optional"]["pyyaml"] = True
        return
    data["optional"]["pyyaml"] = False
    problems.append("PyYAML ausente: o validate_spec.py não lê spec em .yaml (aviso; não altera o status).")
    next_steps.append("Instale com python3 -m pip install --user pyyaml (Windows: py -3 -m pip install "
                      "--user pyyaml). Se o pip recusar (ambiente gerenciado, erro externally-managed-environment): "
                      "python3 -m venv .venv && .venv/bin/pip install pyyaml (Windows: .venv\\Scripts\\pip) e rode o "
                      "validate_spec.py com o python do venv. Ou escreva o spec em JSON.")


def skill_dir_warning(args, ctx):
    project_dir = os.path.abspath(args.project_dir or os.getcwd())
    if inside_skill_dir(project_dir, ctx.skill_dir):
        return ("A raiz do projeto analisada (%s) é a pasta da skill google-forms ou fica dentro dela: os "
                "registros de escopo project/local não refletem o projeto do usuário. Rode a partir da raiz do "
                "projeto (python3 <pasta-da-skill>/scripts/check_setup.py) ou passe --project-dir." % project_dir)
    return None


def build_missing(err, tried, args, ctx):
    data = {"playwright_mcp": {"dir": None, "tried": tried}, "optional": {"pyyaml": True}}
    problems = [err or "A skill playwright-mcp não foi encontrada ao lado desta skill (pasta irmã "
                       "`playwright-mcp`) nem no layout do repositório."]
    warn = skill_dir_warning(args, ctx)
    if warn:
        problems.append(warn)
    if err:
        steps = ["Corrija ou remova a variável %s (ou aponte-a para a pasta da skill playwright-mcp)." % PM_ENV]
    else:
        steps = ["Instale a skill playwright-mcp, que a google-forms exige para o Playwright MCP: %s. Se ela já "
                 "está instalada em outro lugar, aponte %s para a pasta dela. Depois rode este check de novo."
                 % (INSTALL_HINT, PM_ENV)]
    pyyaml_items(data, problems, steps)
    return 1, result(False, "playwright_mcp_missing", data, problems, steps)


def build_error(msg, pm_dir, args, ctx):
    data = {"playwright_mcp": {"dir": pm_dir}, "optional": {"pyyaml": True}}
    problems = ["Falha ao consultar a skill playwright-mcp: %s" % msg]
    warn = skill_dir_warning(args, ctx)
    if warn:
        problems.append(warn)
    steps = ["Rode o check_setup.py da skill playwright-mcp direto (%s) para ver o erro, ou reinstale a skill."
             % os.path.join(pm_dir, PM_SCRIPT)]
    pyyaml_items(data, problems, steps)
    return 1, result(False, "playwright_mcp_error", data, problems, steps)


def adapt(payload, rc, pm_dir, args, ctx):
    status = payload.get("status")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    problems = [_qualify(str(p), pm_dir) for p in (payload.get("problems") or [])]
    steps = [_qualify(str(s), pm_dir) for s in (payload.get("next_steps") or [])]
    data["optional"] = {"pyyaml": True}
    data["playwright_mcp"] = {"dir": pm_dir}
    warn = skill_dir_warning(args, ctx)
    if warn:
        problems.append(warn)
    if status == "ready":
        # O próximo passo genérico da playwright-mcp cede lugar ao do Forms.
        steps = [s for s in steps if not s.startswith("Faça a verificação final")]
        steps.insert(0, "Faça a verificação final: browser_navigate em %s e confira que aparece a lista de "
                        "formulários, não a tela de login." % FORMS_URL)
    elif status != "usage_error":
        steps.append("Os passos acima citam arquivos da skill playwright-mcp (%s e outros; pasta: %s): leia o "
                     "que o status pedir antes de agir." % (PM_SKILL_FILES, pm_dir))
    pyyaml_items(data, problems, steps)
    ok = status == "ready"
    code = 0 if ok else (rc if rc in (1, 2) else 1)
    return code, result(ok, status, data, problems, steps)


def check(args, ctx):
    pm_dir, err, tried = find_playwright_mcp(ctx.environ, ctx.skill_dir)
    if not pm_dir:
        return build_missing(err, tried, args, ctx)
    forwarded = ["--harness", args.harness]
    if args.server_name:
        forwarded += ["--server-name", args.server_name]
    if args.project_dir:
        forwarded += ["--project-dir", args.project_dir]
    rc, payload, run_err = run_playwright_mcp(pm_dir, forwarded, ctx.environ)
    if payload is None:
        return build_error(run_err, pm_dir, args, ctx)
    return adapt(payload, rc, pm_dir, args, ctx)


def build_parser():
    ap = _Parser(description="Passo 0 da skill google-forms: confere Node, registro do Playwright MCP, token e "
                             "navegador pelo check_setup.py da skill playwright-mcp (somente leitura).")
    ap.add_argument("--harness", default="auto",
                    choices=["auto", "claude", "cursor", "vscode", "codex", "gemini", "windsurf"],
                    help="aplicativo a conferir (padrão: auto)")
    ap.add_argument("--server-name", default=None,
                    help="nome do servidor MCP a procurar (padrão da playwright-mcp no modo extension: "
                         "playwright-browser)")
    ap.add_argument("--project-dir", default=None, help="raiz do projeto (padrão: diretório atual)")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    code, payload = check(args, env or Context())
    emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
