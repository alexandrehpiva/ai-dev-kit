#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica se o ambiente está pronto para o Playwright MCP da skill playwright-mcp.

Uso:
    python3 scripts/check_setup.py [--harness auto|claude|cursor|vscode|codex|gemini|windsurf]
                                   [--server-name <nome>] [--project-dir <pasta>]
                                   [--mode extension|headless-profile|headless-state]
                                   [--copy-dir <pasta>] [--state-file <arquivo>] [--max-age-hours 24]
    (Windows: py -3 scripts\\check_setup.py ...)

Checa, sem alterar nada: Node/npx e versão; servidor MCP registrado nos arquivos de
configuração dos harnesses (escopos user e project); token da Playwright Extension
(só presença e tamanho, nunca o valor); navegador (via detect_browser) e se a extensão
aparece instalada no perfil do navegador (só existência de <perfil>/Extensions/<id>/; não
lê Preferences nem nenhum outro arquivo do perfil).

Com --mode headless-profile confere também a cópia do perfil (pasta, marcador do clone_profile.py,
travas Singleton*/lockfile, idade, pwmcp-config.json com o ignoreDefaultArgs do SO e
--profile-directory quando o perfil não é Default). Com --mode headless-state confere o
storageState (existe, JSON com cookies, permissão 600 em macOS/Linux, idade) e o --isolated.
A pasta/arquivo vêm de --copy-dir/--state-file ou do servidor registrado. Nunca lê o conteúdo dos
cookies: só a estrutura do JSON do state (chaves) e o JSON de config/marcador gerados pela skill.

Nunca imprime valores de env/headers: só os nomes das chaves; args com cara de credencial
saem como "<redacted:N chars>" (mesma redação do configure_mcp.py).

Saída: JSON {"ok","status","data","problems","next_steps"} em stdout.
Status (em ordem de prioridade): node_missing | node_too_old | browser_issue |
    copy_issue | state_issue | mcp_not_registered | token_missing | ready.
Códigos de saída: 0 = ready; 1 = problema acionável; 2 = erro de uso.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import configure_mcp as cm  # noqa: E402
import clone_profile as cp  # noqa: E402
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
    def _val(flag):
        if flag in args:
            i = args.index(flag)
            return args[i + 1] if i + 1 < len(args) else None
        return None

    if "--extension" in args:
        mode = "extension"
    elif "--storage-state" in args:
        mode = "headless-state"
    elif "--user-data-dir" in args and "--config" in args:
        mode = "headless-profile"
    elif "--user-data-dir" in args:
        mode = "profile"
    else:
        mode = "default"
    return {
        "user_data_dir": _val("--user-data-dir"), "mcp_config": _val("--config"),
        "output_dir": _val("--output-dir"),
        "state_file": _val("--storage-state"), "isolated": "--isolated" in args,
        "headless": "--headless" in args,
        "harness": harness, "scope": scope, "file": path, "name": name, "matches_name": name == wanted,
        "command": srv.get("command"), "args": (red or cm.Redactor()).args(args), "package": pkg,
        "mode": mode,
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
# Modos headless (somente leitura)
# ---------------------------------------------------------------------------

def _age_hours(path_or_ts, env, is_ts=False):
    try:
        ts = path_or_ts if is_ts else os.path.getmtime(path_or_ts)
        return round((time.time() - ts) / 3600.0, 1)
    except OSError:
        return None


def check_copy(copy_dir, mcp_config, env, max_age, problems, next_steps, registered_exe=None, check_exe=False):
    """Confere a cópia do perfil. Devolve (info, ok)."""
    info = {"dir": copy_dir, "exists": False, "marker": False, "profile": None, "level": None,
            "locks": [], "age_hours": None, "config": None}
    ok = True
    if not copy_dir or not os.path.isdir(copy_dir):
        problems.append("A cópia do perfil não existe: %s." % copy_dir)
        next_steps.append("Crie a cópia com clone_profile.py (headless-logged.md).")
        return info, False
    info["exists"] = True
    marker = cp.read_marker(copy_dir)
    info["marker"] = marker is not None
    if marker is None:
        problems.append("%s não tem o marcador %s: não foi criada pelo clone_profile.py." % (copy_dir, cp.MARKER))
        ok = False
    else:
        info["profile"], info["level"] = marker.get("profile"), marker.get("level")
        info["browser"], info["marker_executable"] = marker.get("browser"), marker.get("executable")
        if check_exe:
            info["registered_executable"] = registered_exe
            if not registered_exe:
                problems.append("O servidor registrado não tem --executable-path: o MCP abriria o canal chrome, "
                                "não o navegador da cópia (%s); a chave dos cookies é por navegador e a cópia "
                                "abriria deslogada." % (marker.get("browser") or "desconhecido"))
                ok = False
            elif cm.same_browser(marker, registered_exe) is False:
                problems.append("O servidor registrado abre %s, mas a cópia foi feita com %s: a chave dos cookies é "
                                "por navegador, então a cópia abriria deslogada e seria estragada. Reconfigure com "
                                "configure_mcp.py (ele usa o navegador do marcador)."
                                % (registered_exe, marker.get("browser_name") or marker.get("browser")))
                ok = False
        created = marker.get("created_at")
        age = None
        if created:
            try:
                age = _age_hours(time.mktime(time.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")), env, is_ts=True)
            except (ValueError, OverflowError):
                age = None
        info["age_hours"] = age if age is not None else _age_hours(os.path.join(copy_dir, cp.MARKER), env)
        if info["age_hours"] is not None and info["age_hours"] > max_age:
            problems.append("A cópia tem %.1f h (limite %d h): a sessão pode ter expirado ou divergido do "
                            "navegador real. Refaça com clone_profile.py --replace." % (info["age_hours"], max_age))
            ok = False
    locks = []
    scan = [copy_dir]
    if info["profile"]:
        scan.append(os.path.join(copy_dir, info["profile"]))
    for folder in scan:
        try:
            names = os.listdir(folder)
        except OSError:
            names = []
        locks += [os.path.join(folder, n) for n in names if cp._matches(n, cp.LOCK_PATTERNS)]
    info["locks"] = locks
    if locks:
        problems.append("Há travas na cópia (%s): remova Singleton*/lockfile ou refaça a cópia."
                        % ", ".join(os.path.basename(x) for x in locks))
        ok = False
    cfg_path = mcp_config or os.path.join(copy_dir, cp.CONFIG_NAME)
    cfg_info = {"path": cfg_path, "exists": os.path.isfile(cfg_path), "ignore_default_args": None,
                "profile_directory_arg": None, "ok": False}
    info["config"] = cfg_info
    if not cfg_info["exists"]:
        problems.append("Config do MCP ausente: %s." % cfg_path)
        return info, False
    try:
        with open(cfg_path, encoding="utf-8") as fh:
            cfg = json.load(fh)
        launch = cfg["browser"]["launchOptions"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append("Config do MCP ilegível ou sem browser.launchOptions (%s)." % exc.__class__.__name__)
        return info, False
    ign = launch.get("ignoreDefaultArgs")
    cfg_info["ignore_default_args"] = ign
    need = cp.ignore_default_args(env.os_name)
    missing = [a for a in need if not (isinstance(ign, list) and a in ign)]
    if missing:
        problems.append("A config não tem ignoreDefaultArgs com %s: sem isso o navegador não decifra os "
                        "cookies da cópia e abre DESLOGADO (e apaga os cookies da cópia)." % ", ".join(missing))
        ok = False
    prof = info["profile"]
    pargs = [a for a in (launch.get("args") or []) if isinstance(a, str) and a.startswith("--profile-directory=")]
    cfg_info["profile_directory_arg"] = pargs[0].split("=", 1)[1] if pargs else None
    if prof and prof != "Default" and cfg_info["profile_directory_arg"] != prof:
        problems.append("Perfil '%s' (não é Default) sem args --profile-directory=%s na config: o Chromium abriria "
                        "um perfil vazio." % (prof, prof))
        ok = False
    cfg_info["ok"] = not missing and ok
    return info, ok


def check_state(state_file, isolated, max_age, problems, next_steps):
    """Confere o storageState sem ler valores. Devolve (info, ok)."""
    info = {"file": state_file, "exists": False, "cookies": None, "origins": None, "mode": None,
            "age_hours": None, "isolated": isolated}
    ok = True
    if not state_file or not os.path.isfile(state_file):
        problems.append("storageState ausente: %s." % state_file)
        next_steps.append("Exporte a sessão (templates/export-storage-state.md).")
        return info, False
    info["exists"] = True
    info["age_hours"] = _age_hours(state_file, None)
    if os.name == "posix":
        mode = os.stat(state_file).st_mode & 0o777
        info["mode"] = oct(mode)
        if mode & 0o077:
            problems.append("O storageState tem permissão %s: contém cookies; rode chmod 600." % oct(mode))
            ok = False
    try:
        with open(state_file, encoding="utf-8") as fh:
            doc = json.load(fh)
        info["cookies"] = len(doc.get("cookies") or [])
        info["origins"] = len(doc.get("origins") or [])
    except (OSError, ValueError, AttributeError):
        problems.append("O storageState não é um JSON válido.")
        return info, False
    if info["cookies"] == 0 and info["origins"] == 0:
        problems.append("O storageState está vazio (0 cookies, 0 origens): a sessão não foi exportada.")
        ok = False
    if info["age_hours"] is not None and info["age_hours"] > max_age:
        problems.append("O storageState tem %.1f h (limite %d h): a sessão pode ter expirado; exporte de novo."
                        % (info["age_hours"], max_age))
        ok = False
    if isolated is False:
        problems.append("O servidor registrado usa --storage-state sem --isolated: o MCP ignora o arquivo.")
        ok = False
    return info, ok


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
    auto_name = not args.server_name
    if auto_name:
        args.server_name = (cm.DEFAULT_SERVER_NAME if args.mode in (None, "extension")
                            else cm.HEADLESS_SERVER_NAME)
    project_dir = os.path.abspath(args.project_dir or os.getcwd())
    if cm.inside_skill_dir(project_dir):
        problems.append("A raiz do projeto analisada (%s) é a pasta da skill ou fica dentro dela: os registros "
                        "de escopo project/local não refletem o projeto do usuário. Rode a partir da raiz do "
                        "projeto (python3 <pasta-da-skill>/scripts/check_setup.py) ou passe --project-dir."
                        % project_dir)
    data = {"node": None, "harnesses_checked": [], "registrations": [], "selected": None,
            "token": None, "browser": None, "extension": None, "mode": None, "copy": None,
            "state": None}

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
    if auto_name and args.mode is None and not any(r["matches_name"] for r in regs):
        # Sem --mode nem --server-name: tenta também o nome padrão dos modos headless.
        alt = find_registrations(harnesses, cm.HEADLESS_SERVER_NAME, env, project_dir, [], red)
        if any(r["matches_name"] for r in alt):
            args.server_name, regs = cm.HEADLESS_SERVER_NAME, alt
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

    # Modos headless: cópia do perfil / storageState.
    mode = args.mode or (sel["mode"] if sel and sel["mode"] in ("headless-profile", "headless-state") else None)
    data["mode"] = mode
    mode_problem = None
    if mode == "headless-profile":
        copy_dir = args.copy_dir or (sel or {}).get("user_data_dir")
        if copy_dir:
            data["copy"], ok_copy = check_copy(os.path.abspath(os.path.expanduser(copy_dir)),
                                               (sel or {}).get("mcp_config"), env, args.max_age_hours,
                                               problems, next_steps,
                                               registered_exe=(sel or {}).get("executable_path"),
                                               check_exe=bool(sel and sel["mode"] == "headless-profile"))
            if not ok_copy:
                mode_problem = "copy_issue"
        else:
            problems.append("Sem --copy-dir e sem servidor headless-profile registrado: não sei qual cópia conferir.")
        if sel and sel["mode"] == "headless-profile" and not sel["headless"]:
            problems.append("O servidor registrado não tem --headless.")
        if sel and sel["mode"] == "headless-profile" and not sel.get("output_dir"):
            problems.append("O servidor registrado não tem --output-dir: snapshots e capturas de páginas logadas "
                            "vão para .playwright-mcp/ na pasta do projeto. Reconfigure com configure_mcp.py "
                            "(ele inclui --output-dir) ou ponha .playwright-mcp/ no .gitignore.")
    elif mode == "headless-state":
        sf = args.state_file or (sel or {}).get("state_file")
        if sf:
            data["state"], ok_state = check_state(os.path.abspath(os.path.expanduser(sf)),
                                                  (sel or {}).get("isolated") if sel else None,
                                                  args.max_age_hours, problems, next_steps)
            if not ok_state:
                mode_problem = "state_issue"
        else:
            problems.append("Sem --state-file e sem servidor headless-state registrado: não sei qual state conferir.")

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
    elif mode_problem:
        status = mode_problem
        next_steps.insert(0, "Corrija a cópia/estado conforme data.%s (problems) e rode de novo."
                          % ("copy" if mode_problem == "copy_issue" else "state"))
    elif not sel:
        status = "mcp_not_registered"
        next_steps.insert(0, "Registre o servidor com configure_mcp.py (plano, revisão do usuário, --apply).")
    elif token["required"] and not token["source"]:
        status = "token_missing"
        next_steps.insert(0, "Defina %s no ambiente do harness (sem colar no chat) e reinicie o harness."
                          % cm.TOKEN_ENV)
    else:
        status = "ready"
        next_steps.insert(0, "Faça a verificação final: browser_navigate em uma página só de leitura do site em que o "
                          "usuário deve estar logado e confira que NÃO aparece a tela de login.")
    ok = status == "ready"
    return (0 if ok else 1), db.result(ok, status, data, problems, next_steps)


def build_parser():
    ap = db._Parser(description="Verifica Node, registro do MCP, token e navegador (somente leitura).")
    ap.add_argument("--harness", default="auto", choices=["auto"] + list(cm.HARNESS_NAMES), help="aplicativo a conferir (padrão: auto)")
    ap.add_argument("--server-name", default=None, help="nome do servidor MCP a procurar (padrão: %s no modo extension; %s nos modos headless)" % (cm.DEFAULT_SERVER_NAME, cm.HEADLESS_SERVER_NAME))
    ap.add_argument("--project-dir", default=None, help="raiz do projeto (padrão: diretório atual)")
    ap.add_argument("--mode", default=None, choices=["extension", "headless-profile", "headless-state"],
                    help="modo a conferir (padrão: o do servidor registrado)")
    ap.add_argument("--copy-dir", default=None, help="headless-profile: pasta da cópia (padrão: a do servidor registrado)")
    ap.add_argument("--state-file", default=None, help="headless-state: storageState (padrão: o do servidor registrado)")
    ap.add_argument("--max-age-hours", type=int, default=24, help="idade máxima da cópia/state antes de avisar (padrão 24)")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    code, payload = check(args, env or db.SystemEnv())
    db.emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
