#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica se o ambiente está pronto para o Playwright MCP da skill google-forms.

Uso:
    python3 scripts/check_setup.py [--harness auto|claude|cursor|vscode|codex|gemini|windsurf]
                                   [--server-name playwright-browser] [--project-dir <pasta>]
    (Windows: py -3 scripts\\check_setup.py ...)

Checa, sem alterar nada: Node/npx e versão; servidor MCP registrado nos arquivos de
configuração dos harnesses (escopos user e project); token da Playwright Extension
(só presença e tamanho, nunca o valor); navegador (via detect_browser) e se a extensão
aparece instalada no perfil do navegador (só existência de <perfil>/Extensions/<id>/; não
lê Preferences nem nenhum outro arquivo do perfil).

Nunca imprime valores de env/headers: só os nomes das chaves; args com cara de credencial
saem como "<redacted:N chars>" (mesma redação do configure_mcp.py).

Saída: JSON {"ok","status","data","problems","next_steps"} em stdout.
Aviso opcional: data.optional.pyyaml=false (+ next_step) quando falta PyYAML; nunca muda o status.
Status (em ordem de prioridade): node_missing | node_too_old | browser_issue |
    mcp_not_registered | token_missing | ready.
Códigos de saída: 0 = ready; 1 = problema acionável; 2 = erro de uso.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import configure_mcp as cm  # noqa: E402
import detect_browser as db  # noqa: E402

MIN_NODE_MAJOR = 20  # playwright-core 1.65 declara engines.node >=20 (conferido com `npm view` em 2026-11-11)


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def check_node(env, problems):
    info = {"found": False, "path": None, "version": None, "major": None, "npx_path": None}
    node = env.which("node")
    info["path"] = node
    info["npx_path"] = env.which("npx")
    if not node:
        return info
    rc, out = env.run([node, "-v"])
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", (out or "").strip())
    if rc != 0 or not m:
        problems.append("node encontrado em %s, mas 'node -v' falhou." % node)
        return info
    info["found"] = True
    info["version"] = out.strip()
    info["major"] = int(m.group(1))
    if info["major"] % 2 == 1:
        problems.append("Node %s é linha ímpar (nunca vira LTS); funciona, mas prefira uma LTS ativa."
                        % info["version"])
    if not info["npx_path"]:
        problems.append("npx não encontrado no PATH (vem com o npm).")
    return info


# ---------------------------------------------------------------------------
# Dependência opcional (não bloqueia o status)
# ---------------------------------------------------------------------------

def pyyaml_available():
    """True se o Python que roda este script enxerga o PyYAML (o validate_spec.py usa o mesmo python3)."""
    try:
        return importlib.util.find_spec("yaml") is not None
    except (ImportError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Registros MCP
# ---------------------------------------------------------------------------

def _servers_from_file(harness, path, env, project_dir, red=None):
    """Lê o arquivo e devolve (dict de servidores, erro|None). `red` aprende os segredos do arquivo."""
    text = env.read_text(path)
    if text is None:
        return {}, None
    try:
        if cm.HARNESS_INFO[harness]["format"] == "toml":
            doc = cm.toml_loads(text)
        else:
            doc, _ = cm.load_json(text)
    except ValueError as exc:
        return {}, "arquivo ilegível (%s)" % exc
    if red is not None:
        red.tree(doc)
    servers = doc.get(cm.HARNESS_INFO[harness]["key"]) if isinstance(doc, dict) else None
    out = dict(servers) if isinstance(servers, dict) else {}
    # Claude Code: escopo local = ~/.claude.json → projects[<pasta>].mcpServers
    if harness == "claude" and path.endswith(".claude.json") and isinstance(doc, dict):
        out = {k: dict(v, _scope="user") if isinstance(v, dict) else v for k, v in out.items()}
        proj = (doc.get("projects") or {}).get(project_dir)
        if isinstance(proj, dict):
            for k, v in (proj.get("mcpServers") or {}).items():
                if isinstance(v, dict):
                    out.setdefault(k, dict(v, _scope="local"))
    return out, None


def find_registrations(harnesses, server_name, env, project_dir, problems, red=None):
    regs = []
    for h in harnesses:
        for scope in ("user", "project"):
            try:
                path, _ = cm.config_path(h, scope, env, project_dir)
            except cm.UsageError:
                continue
            if not env.exists(path):
                continue
            servers, err = _servers_from_file(h, path, env, project_dir, red)
            if err:
                problems.append("%s: %s" % (path, err))
                continue
            for name, srv in servers.items():
                if not isinstance(srv, dict):
                    continue
                args = [str(a) for a in (srv.get("args") or [])]
                is_pw = any("@playwright/mcp" in a for a in args) or "@playwright/mcp" in str(srv.get("command"))
                if name == server_name or is_pw:
                    regs.append(describe_server(h, srv.get("_scope", scope), path, name, srv, server_name,
                                                red))
    return regs


def describe_server(harness, scope, path, name, srv, wanted, red=None):
    args = [str(a) for a in (srv.get("args") or [])]
    env_cfg = srv.get("env") if isinstance(srv.get("env"), dict) else {}
    pkg = next((a for a in args if "@playwright/mcp" in a), None)
    exe = None
    if "--executable-path" in args:
        i = args.index("--executable-path")
        exe = args[i + 1] if i + 1 < len(args) else None
    token_cfg = None
    if cm.TOKEN_ENV in env_cfg:
        v = str(env_cfg[cm.TOKEN_ENV])
        if v.startswith("${input:"):
            token_cfg = "vscode_input"
        elif re.match(r"^\$\{?(env:)?%s\}?$" % cm.TOKEN_ENV, v) or "%" + cm.TOKEN_ENV + "%" == v:
            token_cfg = "env_reference"
        else:
            token_cfg = "literal"  # valor gravado no arquivo: nunca é impresso
    elif cm.TOKEN_ENV in (srv.get("env_vars") or []):
        token_cfg = "env_forward"
    return {
        "harness": harness, "scope": scope, "file": path, "name": name, "matches_name": name == wanted,
        "command": srv.get("command"), "args": (red or cm.Redactor()).args(args), "package": pkg,
        "mode": "extension" if "--extension" in args else ("profile" if "--user-data-dir" in args
                                                           else "default"),
        "executable_path": exe, "env_keys": sorted(env_cfg.keys()), "token_config": token_cfg,
        "windows_c_corrupted": any(a.lower() in ("c:/", "c:\\") for a in args[:1]),
    }


# ---------------------------------------------------------------------------
# Extensão no perfil do navegador (somente leitura)
# ---------------------------------------------------------------------------

def extension_installed(user_data_dir, env):
    """Procura a Playwright Extension nos perfis (Default, Profile N). None = não deu para checar."""
    if not user_data_dir or not env.isdir(user_data_dir):
        return None, []
    found, checked = [], []
    for prof in env.listdir(user_data_dir):
        if prof != "Default" and not re.match(r"^Profile \d+$", prof):
            continue
        checked.append(prof)
        base = env.path.join(user_data_dir, prof)
        # Só existência da pasta da extensão; nenhum arquivo do perfil é lido.
        if env.isdir(env.path.join(base, "Extensions", db.EXTENSION_ID)):
            found.append(prof)
    return (bool(found) if checked else None), found


# ---------------------------------------------------------------------------
# Fluxo
# ---------------------------------------------------------------------------

def check(args, env):
    """Executa as checagens e devolve o payload já redigido para exibição."""
    red = cm.Redactor()
    code, payload = _check(args, env, red)
    return code, red.payload(payload)


def _check(args, env, red):
    problems, next_steps = [], []
    project_dir = os.path.abspath(args.project_dir or os.getcwd())
    if cm.inside_skill_dir(project_dir):
        problems.append("A raiz do projeto analisada (%s) é a pasta da skill ou fica dentro dela: os registros "
                        "de escopo project/local não refletem o projeto do usuário. Rode a partir da raiz do "
                        "projeto (python3 <pasta-da-skill>/scripts/check_setup.py) ou passe --project-dir."
                        % project_dir)
    data = {"node": None, "harnesses_checked": [], "registrations": [], "selected": None,
            "token": None, "browser": None, "extension": None, "optional": {"pyyaml": True}}

    node = check_node(env, problems)
    data["node"] = node

    _, bpayload = db.detect(env, "auto")
    rec = bpayload["data"].get("recommended")
    data["browser"] = {"status": bpayload["status"], "default": bpayload["data"].get("default"),
                       "recommended": rec}
    problems += ["detect_browser: " + p for p in bpayload["problems"]]

    harnesses = list(cm.HARNESS_NAMES) if args.harness == "auto" else [args.harness]
    data["harnesses_checked"] = harnesses
    regs = find_registrations(harnesses, args.server_name, env, project_dir, problems, red)
    data["registrations"] = regs
    named = [r for r in regs if r["matches_name"]]
    sel = named[0] if named else None
    data["selected"] = sel
    if not named and regs:
        problems.append("Há Playwright MCP registrado com outro nome (%s); a skill espera '%s'."
                        % (", ".join(sorted(set(r["name"] for r in regs))), args.server_name))
    if len(named) > 1:
        problems.append("O servidor '%s' aparece em %d lugares; o harness pode usar qualquer um deles."
                        % (args.server_name, len(named)))

    browser_bad = bpayload["status"] in ("no_chromium", "unsupported_os", "invalid_override")
    if sel:
        if sel["windows_c_corrupted"]:
            problems.append("O 1º argumento virou 'C:/' (bug conhecido do 'claude mcp add' com cmd /c); "
                            "reconfigure com configure_mcp.py.")
            browser_bad = True
        if sel["executable_path"] and not env.exists(sel["executable_path"]):
            problems.append("--executable-path aponta para algo inexistente: %s" % sel["executable_path"])
            browser_bad = True
        if sel["package"] and sel["package"].endswith("@latest"):
            problems.append("Versão não fixada (@latest): o registry pode servir outra versão; prefira fixar.")
        if sel["token_config"] == "literal" and sel["scope"] == "project":
            problems.append("Token gravado em texto puro num arquivo de projeto (%s). Troque por referência "
                            "à variável de ambiente e gere um token novo na extensão." % sel["file"])

    # Token (só presença/tamanho).
    token = {"required": bool(sel and sel["mode"] == "extension"), "source": None,
             "env_present": bool(env.environ.get(cm.TOKEN_ENV)),
             "env_length": len(env.environ.get(cm.TOKEN_ENV) or "")}
    if token["required"]:
        if sel["token_config"] in ("literal", "vscode_input"):
            token["source"] = sel["token_config"]
        elif token["env_present"]:
            token["source"] = "environment"
    data["token"] = token

    # Extensão no perfil do navegador que o MCP usa.
    if sel and sel["mode"] == "extension":
        target = None
        if sel["executable_path"]:
            target, _ = db.entry_from_path(sel["executable_path"], env)
        if target is None:
            target = rec
        installed, profiles = extension_installed((target or {}).get("user_data_dir"), env)
        data["extension"] = {"browser": (target or {}).get("name"), "installed": installed,
                             "profiles": profiles}
        if installed is False:
            next_steps.append("A Playwright Extension não aparece nos perfis de %s: peça ao usuário para "
                              "instalá-la (https://chromewebstore.google.com/detail/playwright-extension/%s)."
                              % (target["name"], db.EXTENSION_ID))

    # Status por prioridade.
    if not node["found"]:
        status = "node_missing"
        next_steps.insert(0, "Instale o Node.js LTS (>= %d) — ver setup.md — e reabra o terminal." % MIN_NODE_MAJOR)
    elif not node["npx_path"]:
        status = "node_missing"
        next_steps.insert(0, "npx ausente: reinstale o Node.js LTS (traz npm/npx).")
    elif node["major"] < MIN_NODE_MAJOR:
        status = "node_too_old"
        next_steps.insert(0, "Node %s é antigo; instale uma LTS >= %d." % (node["version"], MIN_NODE_MAJOR))
    elif browser_bad:
        status = "browser_issue"
        next_steps.insert(0, "Resolva o navegador (rode detect_browser.py) e reconfigure com configure_mcp.py.")
    elif not sel:
        status = "mcp_not_registered"
        next_steps.insert(0, "Registre o servidor com configure_mcp.py (plano, revisão do usuário, --apply).")
    elif token["required"] and not token["source"]:
        status = "token_missing"
        next_steps.insert(0, "Defina %s no ambiente do harness (sem colar no chat) e reinicie o harness."
                          % cm.TOKEN_ENV)
    else:
        status = "ready"
        next_steps.insert(0, "Faça a verificação final: browser_navigate em https://docs.google.com/forms/u/0/ "
                          "e confira que aparece a lista de formulários, não a tela de login.")
    # Aviso não bloqueante: sem PyYAML o validate_spec.py recusa spec .yaml (usage_error), mas JSON funciona.
    if not pyyaml_available():
        data["optional"]["pyyaml"] = False
        problems.append("PyYAML ausente: o validate_spec.py não lê spec em .yaml (aviso; não altera o status).")
        next_steps.append("Instale com python3 -m pip install --user pyyaml (Windows: py -3 -m pip install "
                          "--user pyyaml). Se o pip recusar (ambiente gerenciado, erro externally-managed-environment): "
                          "python3 -m venv .venv && .venv/bin/pip install pyyaml (Windows: .venv\\Scripts\\pip) e rode o "
                          "validate_spec.py com o python do venv. Ou escreva o spec em JSON.")
    ok = status == "ready"
    return (0 if ok else 1), db.result(ok, status, data, problems, next_steps)


def build_parser():
    ap = db._Parser(description="Verifica Node, registro do MCP, token e navegador (somente leitura).")
    ap.add_argument("--harness", default="auto", choices=["auto"] + list(cm.HARNESS_NAMES), help="aplicativo a conferir (padrão: auto)")
    ap.add_argument("--server-name", default=cm.DEFAULT_SERVER_NAME, help="nome do servidor MCP a procurar (padrão %s)" % cm.DEFAULT_SERVER_NAME)
    ap.add_argument("--project-dir", default=None, help="raiz do projeto (padrão: diretório atual)")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    code, payload = check(args, env or db.SystemEnv())
    db.emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
