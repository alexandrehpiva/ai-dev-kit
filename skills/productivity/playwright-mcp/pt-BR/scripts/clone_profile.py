#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copia o perfil de um navegador Chromium para uma pasta NOVA, pronta para o Playwright MCP headless.

Uso:
    python3 scripts/clone_profile.py [--browser auto|brave|chrome|msedge|chromium|<caminho>]
        [--profile auto|Default|"Profile N"] [--level minimal|light|full]
        [--dest <pasta>] [--replace] [--dry-run] [--source-dir <user-data-dir>]
    Sem --dest usa a pasta padrão por sistema (macOS ~/Library/Application Support/playwright-mcp-copies/
    <navegador>-<perfil>; Linux ~/.local/share/playwright-mcp-copies/...; Windows %LOCALAPPDATA%\\playwright-mcp-copies\\...).
    (Windows: py -3 scripts\\clone_profile.py ...)

O que faz, em ordem:
  1. acha o navegador (detect_browser) e o perfil (padrão: o último ativo, lido de `Local State`);
  2. valida a pasta destino: precisa estar vazia OU ter o marcador `.pwmcp-clone.json` desta
     ferramenta (e então só com --replace). Pasta alheia é SEMPRE recusada, mesmo com --replace.
     Também recusa destino dentro de repositório git (.git), cofre Obsidian (.obsidian), pastas
     sincronizadas (iCloud, Google Drive, Dropbox, OneDrive) e link simbólico;
  3. copia `Local State` + o perfil conforme o nível:
       minimal  só `Local State` e os `Cookies` (instantâneo SQLite) — cobre a maioria dos logins
       light    perfil sem caches, extensões, histórico, favicons, sessões e senhas salvas (padrão)
       full     perfil inteiro (só sem travas e sem `Sessions`)
  4. tira um instantâneo consistente dos bancos de Cookies com sqlite3 (`mode=ro` + backup) e
     confere `PRAGMA integrity_check`; remove `Singleton*` e `lockfile` da cópia;
  5. grava `pwmcp-config.json` (launchOptions por sistema) e o marcador (com o navegador e o executável
     da cópia) dentro da pasta destino, cria a pasta de saída do MCP ao lado da cópia
     (<destino>-output, para --output-dir) e imprime o comando do Playwright MCP.

NUNCA escreve na pasta de origem: o banco de origem é aberto só para leitura e todo arquivo
novo nasce em --dest. Com --dry-run nada é criado: mostra o plano (o que entra, o que sai, tamanho).

A cópia pode ser reaberta várias vezes, desde que SEMPRE com a mesma config (mesmo executável que a
criou + `ignoreDefaultArgs` certo). Refaça com --replace (na mesma pasta) quando (a) ela foi aberta
sem a config certa (o Chromium apaga os cookies dela), (b) a sessão expirou ou o site pediu login
de novo, (c) você quer dados mais novos. A pasta destino é equivalente a uma senha (tem os cookies
da sessão): apague ao terminar.

Saída: JSON {"ok","status","data","problems","next_steps"} em stdout.
Status: planned | cloned | browser_issue | profile_issue | dest_conflict | copy_failed.
(dest_conflict inclui destino em pasta git/Obsidian/sincronizada ou link simbólico.)
Códigos de saída: 0 ok; 1 problema acionável; 2 erro de uso.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import fnmatch
import json
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import configure_mcp as cm  # noqa: E402
import detect_browser as db  # noqa: E402

MARKER = cm.CLONE_MARKER
MARKER_TOOL = "pwmcp-clone_profile"
CONFIG_NAME = "pwmcp-config.json"
LEVELS = ("minimal", "light", "full")
PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9 _.\-]+$")
STANDARD_PROFILE_RE = re.compile(r"^(Default|Profile \d+|Guest Profile|System Profile)$")
# Componentes de caminho que indicam pasta sincronizada com a nuvem (comparação sem caixa).
SYNC_FOLDER_NAMES = ("mobile documents", "icloud drive", "google drive", "dropbox")
SYNC_FOLDER_PREFIXES = ("googledrive", "onedrive", "dropbox")

# Itens do 1º nível da pasta do perfil que o nível "light" NÃO copia.
# Caches e dados pesados que não participam do login; `Login Data*` (senhas salvas) fica de fora
# por mínimo privilégio: sessão por cookie não precisa delas.
LIGHT_EXCLUDE = (
    "Service Worker", "Cache", "Code Cache", "GPUCache", "DawnGraphiteCache", "DawnWebGPUCache",
    "DawnCache", "GraphiteDawnCache", "adblock_cache", "Shared Dictionary", "blob_storage",
    "File System", "Extension*", "History*", "Favicons*", "Media Cache", "Login Data*",
    "Sessions", "Current Session", "Current Tabs", "Last Session", "Last Tabs",
)
FULL_EXCLUDE = ("Sessions", "Current Session", "Current Tabs", "Last Session", "Last Tabs")
# Travas: Singleton* e lockfile (macOS/Linux/Windows) no 1º nível da cópia e do perfil.
LOCK_PATTERNS = ("Singleton*", "lockfile")
SQLITE_SIDECAR = ("-journal", "-wal", "-shm")

DEFAULT_COOKIES_REL = (("Network", "Cookies"), ("Cookies",))


class UsageError(Exception):
    pass


# ---------------------------------------------------------------------------
# Config do MCP por sistema
# ---------------------------------------------------------------------------

def ignore_default_args(os_name):
    """Argumentos padrão do Playwright que impedem decifrar cookies de um perfil real.

    macOS: --use-mock-keychain (troca a chave do Chaveiro por uma fixa). Linux: --password-store=basic
    (ignora o keyring). Windows: o Playwright também lista os dois, mas são flags de macOS/Linux sem
    efeito no Windows [inferência]; nenhum ignoreDefaultArgs é necessário.
    """
    if os_name == "macos":
        return ["--use-mock-keychain"]
    if os_name == "linux":
        return ["--password-store=basic"]
    return []


def build_config(os_name, profile_dir):
    """Conteúdo de pwmcp-config.json (para `--config`)."""
    launch = {"headless": True}
    ign = ignore_default_args(os_name)
    if ign:
        launch["ignoreDefaultArgs"] = ign
    if profile_dir and profile_dir != "Default":
        launch["args"] = ["--profile-directory=%s" % profile_dir]
    return {"browser": {"browserName": "chromium", "launchOptions": launch}}


def mcp_argv(os_name, version, exe, dest, config_path, output_dir=None):
    tail = ["-y", "@playwright/mcp@%s" % version, "--headless", "--executable-path", exe,
            "--user-data-dir", dest, "--config", config_path]
    if output_dir:
        tail += ["--output-dir", output_dir]
    if os_name == "windows":
        return ["cmd", "/c", "npx"] + tail
    return ["npx"] + tail


def quote_argv(os_name, argv):
    if os_name == "windows":
        return subprocess.list2cmdline(argv)
    import shlex
    return " ".join(shlex.quote(a) for a in argv)


# ---------------------------------------------------------------------------
# Plano de cópia
# ---------------------------------------------------------------------------

def _matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def dir_size(path):
    total = 0
    files = 0
    for root, _dirs, names in os.walk(path):
        for n in names:
            try:
                total += os.lstat(os.path.join(root, n)).st_size
                files += 1
            except OSError:
                pass
    return total, files


def entry_size(path):
    if os.path.islink(path):
        return 0, 0
    if os.path.isdir(path):
        return dir_size(path)
    try:
        return os.lstat(path).st_size, 1
    except OSError:
        return 0, 0


def is_sqlite_cookie_rel(rel_parts):
    return tuple(rel_parts) in DEFAULT_COOKIES_REL


def plan_profile(profile_src, level):
    """Lista o 1º nível do perfil e decide o que entra. Devolve (incluídos, excluídos).

    Cada item: {"name", "kind", "bytes", "files"}. No nível minimal, nada do perfil entra além dos
    Cookies (tratados à parte).
    """
    included, excluded = [], []
    try:
        names = sorted(os.listdir(profile_src))
    except OSError:
        names = []
    excl = {"minimal": None, "light": LIGHT_EXCLUDE, "full": FULL_EXCLUDE}[level]
    for n in names:
        p = os.path.join(profile_src, n)
        kind = "dir" if os.path.isdir(p) and not os.path.islink(p) else "file"
        if _matches(n, LOCK_PATTERNS):
            excluded.append({"name": n, "kind": kind, "reason": "trava"})
            continue
        if excl is None:
            excluded.append({"name": n, "kind": kind, "reason": "nível minimal"})
            continue
        if _matches(n, excl):
            size, files = entry_size(p)
            excluded.append({"name": n, "kind": kind, "reason": "nível %s" % level, "bytes": size})
            continue
        if os.path.islink(p):
            excluded.append({"name": n, "kind": "link", "reason": "link simbólico"})
            continue
        size, files = entry_size(p)
        included.append({"name": n, "kind": kind, "bytes": size, "files": files})
    return included, excluded


def cookie_sources(profile_src):
    """Bancos de Cookies que existem na origem, como listas de partes relativas ao perfil."""
    out = []
    for rel in DEFAULT_COOKIES_REL:
        if os.path.isfile(os.path.join(profile_src, *rel)):
            out.append(rel)
    return out


# ---------------------------------------------------------------------------
# Cópia
# ---------------------------------------------------------------------------

def sqlite_snapshot(src, dst):
    """Instantâneo consistente de um SQLite: origem aberta só para leitura, backup para dst.

    Devolve (integrity_ok, linhas_de_cookies|None). Levanta sqlite3.Error/OSError se falhar.
    """
    uri = pathlib.Path(os.path.abspath(src)).as_uri() + "?mode=ro"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    last = None
    for _ in range(4):
        try:
            s = sqlite3.connect(uri, uri=True, timeout=5)
            try:
                d = sqlite3.connect(dst)
                try:
                    s.backup(d)
                finally:
                    d.close()
            finally:
                s.close()
            last = None
            break
        except sqlite3.Error as exc:
            last = exc
            if os.path.exists(dst):
                os.unlink(dst)
            time.sleep(0.5)
    if last is not None:
        raise last
    chk = sqlite3.connect(dst)
    try:
        res = chk.execute("PRAGMA integrity_check").fetchall()
        ok = len(res) == 1 and str(res[0][0]).lower() == "ok"
        rows = None
        try:
            rows = chk.execute("SELECT count(*) FROM cookies").fetchone()[0]
        except sqlite3.Error:
            rows = None
    finally:
        chk.close()
    return ok, rows


def copy_tree(src, dst, skipped):
    """Copia uma pasta arquivo a arquivo; erros por arquivo vão para `skipped` (não derrubam a cópia)."""
    copied = 0
    for root, dirs, names in os.walk(src):
        rel = os.path.relpath(root, src)
        target = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for n in names:
            sp = os.path.join(root, n)
            if os.path.islink(sp):
                continue
            try:
                shutil.copy2(sp, os.path.join(target, n))
                copied += 1
            except (OSError, shutil.Error) as exc:
                skipped.append({"file": os.path.relpath(sp, src), "error": exc.__class__.__name__})
    return copied


def remove_locks(folder):
    removed = []
    try:
        names = os.listdir(folder)
    except OSError:
        return removed
    for n in names:
        if _matches(n, LOCK_PATTERNS):
            p = os.path.join(folder, n)
            try:
                if os.path.isdir(p) and not os.path.islink(p):
                    shutil.rmtree(p)
                else:
                    os.unlink(p)
                removed.append(n)
            except OSError:
                pass
    return removed


# ---------------------------------------------------------------------------
# Destino
# ---------------------------------------------------------------------------

def default_dest(entry_id, profile, env):
    """Pasta padrão da cópia: fora de repositórios e de pastas sincronizadas, por sistema."""
    if env.os_name == "windows":
        base = db.win_env(env, "LOCALAPPDATA") or os.path.join(env.home(), "AppData", "Local")
    elif env.os_name == "macos":
        base = os.path.join(env.home(), "Library", "Application Support")
    else:
        base = os.path.join(env.home(), ".local", "share")
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", "%s-%s" % (entry_id or "browser", profile or "Default")).strip("-")
    return os.path.join(base, "playwright-mcp-copies", name)


def _norm(p):
    return os.path.normcase(os.path.realpath(p))


def _is_inside(child, parent):
    c, p = _norm(child), _norm(parent)
    try:
        return os.path.commonpath([c, p]) == p
    except ValueError:
        return False


def read_marker(dest):
    try:
        with open(os.path.join(dest, MARKER), encoding="utf-8") as fh:
            doc = json.load(fh)
        return doc if isinstance(doc, dict) and doc.get("tool") == MARKER_TOOL else None
    except (OSError, ValueError):
        return None


def risky_location(dest, home):
    """Motivo (texto) se o destino fica em repositório git, cofre Obsidian ou pasta sincronizada; senão None.

    Sobe os ancestrais (sem seguir para HOME e acima quando o destino está dentro do HOME, para que um
    HOME versionado como "dotfiles" não bloqueie o destino padrão).
    """
    real = os.path.realpath(dest)
    stop = os.path.realpath(home) if home else None
    inside_home = bool(stop) and _is_inside(real, stop) and _norm(real) != _norm(stop)
    for cand in dict.fromkeys((os.path.abspath(dest), real)):
        parts = [x for x in re.split(r"[\\/]+", cand) if x]
        for part in parts:
            low = part.lower()
            if low in SYNC_FOLDER_NAMES or any(low.startswith(pfx) for pfx in SYNC_FOLDER_PREFIXES):
                return "pasta sincronizada com a nuvem (%s)" % part
    cur = real
    while True:
        if inside_home and _norm(cur) == _norm(stop):
            break
        for marker, label in ((".git", "repositório git"), (".obsidian", "cofre Obsidian")):
            if os.path.lexists(os.path.join(cur, marker)):
                return "%s (%s em %s)" % (label, marker, cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def check_dest(dest, source_udd, env):
    """Devolve (None, estado) ou (mensagem_de_erro, None). estado: new | empty | marked."""
    if os.path.islink(dest):
        return "O destino é um link simbólico: %s. Escolha uma pasta de verdade." % dest, None
    if os.path.lexists(dest) and not os.path.isdir(dest):
        return "A pasta destino existe e não é uma pasta: %s" % dest, None
    home = env.home()
    if _norm(dest) in (_norm(os.sep), _norm(home)) or os.path.dirname(_norm(dest)) == _norm(dest):
        return "Destino perigoso (raiz do disco ou HOME): %s" % dest, None
    if source_udd and (_is_inside(dest, source_udd) or _is_inside(source_udd, dest)):
        return ("O destino não pode ficar dentro da pasta de dados do navegador nem conter ela (%s). "
                "Escolha uma pasta separada." % source_udd), None
    risk = risky_location(dest, home)
    if risk:
        return ("O destino fica em %s: a cópia tem cookies da sessão e não pode ser versionada nem "
                "sincronizada. Use a pasta padrão (omita --dest) ou outra fora disso." % risk), None
    if not os.path.isdir(dest):
        return None, "new"
    names = os.listdir(dest)
    if not names:
        return None, "empty"
    if read_marker(dest) is not None:
        return None, "marked"
    return ("A pasta destino não está vazia e não foi criada por esta ferramenta (sem %s): %s. "
            "Por segurança nada é apagado nem sobrescrito." % (MARKER, dest)), None


# ---------------------------------------------------------------------------
# Fluxo
# ---------------------------------------------------------------------------

def result(ok, status, data, problems, next_steps):
    return db.result(ok, status, data, problems, next_steps)


def run(args, env):
    problems, next_steps = [], []
    os_name = env.os_name
    data = {"browser": None, "source": None, "profile": None, "level": args.level, "dest": None,
            "dry_run": bool(args.dry_run), "included": [], "excluded": [], "cookie_databases": [],
            "bytes": None, "files": None, "cookie_rows": None, "config_path": None, "config": None,
            "mcp_command": None, "mcp_argv": None, "output_dir": None, "removed_locks": [], "skipped": []}

    # 1. navegador e perfil
    entry, bprob = db.pick_browser(args.browser, env)
    problems += bprob
    if entry is None or not entry.get("chromium") or not entry.get("executable"):
        problems.append("Nenhum navegador Chromium utilizável foi encontrado.")
        return 1, result(False, "browser_issue", data, problems,
                         ["Rode detect_browser.py e escolha o navegador com --browser <id|caminho>."])
    data["browser"] = {"name": entry["name"], "id": entry["id"], "executable": entry["executable"],
                       "packaging": entry.get("packaging")}
    if entry.get("packaging") in ("flatpak", "snap"):
        problems.append("%s via %s: o perfil fica numa pasta isolada e o modo headless com cópia não foi "
                        "testado nesse empacotamento [não verificado]." % (entry["name"], entry["packaging"]))
    source_udd = args.source_dir or entry.get("user_data_dir")
    if source_udd:
        source_udd = os.path.abspath(os.path.expanduser(source_udd))
    if not source_udd or not os.path.isdir(source_udd):
        problems.append("Pasta de dados do navegador não encontrada (%s). Informe com --source-dir."
                        % (source_udd or "desconhecida"))
        return 1, result(False, "profile_issue", data, problems, [])
    data["source"] = source_udd
    # Leitura do disco real com as regras de caminho do sistema em que o script roda.
    fs_env = db.SystemEnv(os_name=db.host_os(), environ=env.environ)
    prof_info = db.list_profiles(source_udd, fs_env)
    profile = args.profile
    if profile == "auto":
        profile = prof_info.get("suggested")
    bad_name = (not profile or profile in (".", "..") or not PROFILE_NAME_RE.match(profile)
                or ".." in profile or os.path.isabs(profile) or "/" in profile or "\\" in profile)
    if bad_name:
        problems.append("Nome de perfil inválido ou não encontrado: %r (use o nome de uma pasta de perfil, "
                        "como Default ou Profile 1)." % (profile,))
        return 1, result(False, "profile_issue", data, problems,
                         ["Rode detect_browser.py --list-profiles e escolha com --profile."])
    profile_src = os.path.join(source_udd, profile)
    if not os.path.isdir(profile_src):
        problems.append("O perfil '%s' não existe em %s. Perfis encontrados: %s."
                        % (profile, source_udd, ", ".join(p["dir"] for p in prof_info["profiles"]) or "nenhum"))
        return 1, result(False, "profile_issue", data, problems,
                         ["Rode detect_browser.py --list-profiles e escolha com --profile."])
    data["profile"] = profile
    if not STANDARD_PROFILE_RE.match(profile):
        problems.append("O nome de perfil '%s' não segue o padrão do Chromium (Default, Profile N): confira "
                        "com detect_browser.py --list-profiles." % profile)
    if not os.path.isfile(os.path.join(source_udd, "Local State")):
        problems.append("`Local State` ausente na origem: sem ele a cópia pode não decifrar os cookies "
                        "(no Windows ele guarda a chave de criptografia).")

    # Avisos sobre o estado do navegador de origem (somente leitura).
    for lock in ("SingletonLock", "lockfile"):
        if os.path.lexists(os.path.join(source_udd, lock)):
            problems.append("O navegador parece aberto (%s na pasta de dados). A cópia funciona, mas o "
                            "navegador grava cookies com atraso de ~30 s: login recente pode faltar."
                            % lock)
            break
    cookies_found = cookie_sources(profile_src)
    data["cookie_databases"] = ["/".join(r) for r in cookies_found]
    if not cookies_found:
        problems.append("Nenhum banco de Cookies em %s (%s ou Network/Cookies). Perfil sem sessão?"
                        % (profile, "Cookies"))
    for rel in cookies_found:
        try:
            age = time.time() - os.path.getmtime(os.path.join(profile_src, *rel))
        except OSError:
            continue
        if age < 30:
            problems.append("O banco de Cookies foi alterado há %d s: espere ~30 s depois do último login "
                            "e copie de novo, senão a sessão pode vir incompleta." % int(age))
            break

    # 2. destino
    dest = os.path.abspath(os.path.expanduser(args.dest)) if args.dest else default_dest(entry["id"], profile, env)
    data["dest"] = dest
    err, dstate = check_dest(dest, source_udd, env)
    if err:
        return 1, result(False, "dest_conflict", data, problems + [err],
                         ["Escolha uma pasta nova/vazia em --dest, ou omita --dest para usar o padrão: %s."
                          % default_dest(entry["id"], profile, env)])
    if dstate == "marked" and not args.replace:
        return 1, result(False, "dest_conflict", data,
                         problems + ["A pasta destino já tem uma cópia desta ferramenta: %s." % dest],
                         ["Use --replace para apagar a cópia anterior e refazer, ou outro --dest."])

    # 3. plano
    included, excluded = plan_profile(profile_src, args.level)
    est = sum(i["bytes"] for i in included)
    files = sum(i["files"] for i in included)
    shown = []  # o que a pessoa vê em data.included: Local State + Cookies (instantâneo) + itens do nível
    ls_path = os.path.join(source_udd, "Local State")
    if os.path.isfile(ls_path):
        ls_size = os.path.getsize(ls_path)
        shown.append({"name": "Local State", "kind": "file", "bytes": ls_size, "files": 1})
        est += ls_size
        files += 1
    for rel in cookies_found:  # os Cookies entram sempre, via instantâneo SQLite
        if args.level != "minimal":  # em light/full já estão nos itens do perfil
            break
        try:
            csize = os.path.getsize(os.path.join(profile_src, *rel))
        except OSError:
            csize = 0
        shown.append({"name": "/".join(rel) + " (instantâneo)", "kind": "file", "bytes": csize, "files": 1})
        est += csize
        files += 1
    if args.level == "minimal":  # Cookies/Network entram só pelo instantâneo, não como itens do nível
        for e in list(excluded):
            if e["name"] == "Cookies":  # já aparece em included, como instantâneo
                excluded.remove(e)
            elif e["name"] == "Network":
                e["reason"] = "nível minimal (só Network/Cookies entra, como instantâneo)"
    data["included"], data["excluded"] = shown + included, excluded
    data["bytes"], data["files"] = est, files

    config_path = os.path.join(dest, CONFIG_NAME)
    config = build_config(os_name, profile)
    version = os.environ.get(cm.VERSION_ENV) or cm.DEFAULT_VERSION
    output_dir = cm.output_dir_for(dest)
    argv = mcp_argv(os_name, version, entry["executable"], dest, config_path, output_dir)
    data["output_dir"] = output_dir
    data["config_path"], data["config"] = config_path, config
    data["mcp_argv"], data["mcp_command"] = argv, quote_argv(os_name, argv)
    if os_name == "linux" and hasattr(os, "geteuid") and os.geteuid() == 0:
        problems.append("Rodando como root no Linux: o Chromium recusa o sandbox; acrescente --no-sandbox "
                        "ao comando do MCP.")
    if os_name == "linux":
        next_steps.append("Linux: o keyring da sessão precisa estar destravado no MESMO ambiente em que o MCP "
                          "rodar (cookies v11). Sem keyring, perfis v10 funcionam.")
    if os_name == "windows":
        problems.append("Windows: cookies com criptografia ligada ao aplicativo (v20) podem não decifrar "
                        "numa cópia [não verificado]; se abrir deslogado, use o modo storageState.")

    if args.dry_run:
        next_steps.insert(0, "Plano apenas. Rode sem --dry-run para copiar; depois suba o MCP com data.mcp_command.")
        return 0, result(True, "planned", data, problems, next_steps)

    # 4. execução (só escreve em dest)
    if dstate == "marked":
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    try:
        os.chmod(dest, 0o700)
    except OSError:
        pass
    marker = {"tool": MARKER_TOOL, "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "browser": entry["id"], "browser_name": entry["name"], "executable": entry["executable"],
              "profile": profile, "level": args.level, "os": os_name}
    with open(os.path.join(dest, MARKER), "w", encoding="utf-8") as fh:
        json.dump(marker, fh, indent=2)

    skipped = data["skipped"]
    ls_src = os.path.join(source_udd, "Local State")
    if os.path.isfile(ls_src):
        try:
            shutil.copy2(ls_src, os.path.join(dest, "Local State"))
        except OSError as exc:
            skipped.append({"file": "Local State", "error": exc.__class__.__name__})
    profile_dst = os.path.join(dest, profile)
    os.makedirs(profile_dst, exist_ok=True)

    for item in included:
        sp = os.path.join(profile_src, item["name"])
        dp = os.path.join(profile_dst, item["name"])
        if item["kind"] == "dir":
            copy_tree(sp, dp, skipped)
        else:
            try:
                shutil.copy2(sp, dp)
            except (OSError, shutil.Error) as exc:
                skipped.append({"file": item["name"], "error": exc.__class__.__name__})

    rows_total = 0
    for rel in cookies_found:
        sp = os.path.join(profile_src, *rel)
        dp = os.path.join(profile_dst, *rel)
        for side in SQLITE_SIDECAR:  # restos copiados antes do instantâneo seriam inconsistentes
            if os.path.exists(dp + side):
                os.unlink(dp + side)
        if os.path.exists(dp):
            os.unlink(dp)
        try:
            ok, rows = sqlite_snapshot(sp, dp)
        except (sqlite3.Error, OSError) as exc:
            problems.append("Falha ao tirar o instantâneo de %s (%s: %s)." % ("/".join(rel), exc.__class__.__name__, exc))
            next_steps.append("Feche o navegador e tente de novo, ou use o modo storageState (exportar a sessão).")
            return 1, result(False, "copy_failed", data, problems, next_steps)
        if not ok:
            problems.append("integrity_check falhou em %s: a cópia dos Cookies está inconsistente." % "/".join(rel))
            return 1, result(False, "copy_failed", data, problems,
                             ["Espere ~30 s sem usar o navegador e refaça com --replace."])
        rows_total += rows or 0
    data["cookie_rows"] = rows_total if cookies_found else None

    try:  # pasta de saída do MCP (snapshots de páginas logadas) fora do projeto, ao lado da cópia
        os.makedirs(output_dir, exist_ok=True)
        os.chmod(output_dir, 0o700)
    except OSError as exc:
        problems.append("Não consegui criar a pasta de saída do MCP %s (%s)." % (output_dir, exc.__class__.__name__))
    data["removed_locks"] = remove_locks(dest) + remove_locks(profile_dst)
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
        fh.write("\n")
    if os.name == "posix":
        for p in (config_path, os.path.join(dest, MARKER)):
            try:
                os.chmod(p, 0o600)
            except OSError:
                pass
    if skipped:
        problems.append("%d arquivo(s) não puderam ser copiados (em uso ou sem permissão); veja data.skipped."
                        % len(skipped))
    real_bytes, real_files = dir_size(dest)
    data["bytes"], data["files"] = real_bytes, real_files

    next_steps.insert(0, "Suba o MCP com data.mcp_command (ou gere a configuração do harness com "
                         "configure_mcp.py --mode headless-profile --copy-dir <dest>).")
    next_steps.append("Reabra a cópia quantas vezes quiser, sempre com a MESMA config e o MESMO executável. "
                      "Refaça com --replace (mesma pasta) se abrir sem a config certa, se a sessão expirar "
                      "ou se quiser dados mais novos. Ao terminar, apague %s e %s (cookies e snapshots de "
                      "páginas logadas)." % (dest, output_dir))
    return 0, result(True, "cloned", data, problems, next_steps)


def build_parser():
    ap = db._Parser(description="Copia o perfil do navegador para uma pasta nova (headless logado).")
    ap.add_argument("--browser", default="auto", help="auto, id (brave, chrome, msedge, chromium...) ou caminho")
    ap.add_argument("--profile", default="auto", help='auto (último ativo), Default ou "Profile N"')
    ap.add_argument("--level", default="light", choices=list(LEVELS),
                    help="minimal = Local State + Cookies; light = sem caches (padrão); full = tudo")
    ap.add_argument("--dest", default=None, help="pasta destino (nova ou com o marcador desta ferramenta); padrão: playwright-mcp-copies/<navegador>-<perfil> na pasta de dados do usuário")
    ap.add_argument("--replace", action="store_true", help="refaz uma cópia anterior (só pasta com o marcador)")
    ap.add_argument("--dry-run", action="store_true", help="só mostra o plano; não cria nada")
    ap.add_argument("--source-dir", default=None, help="pasta de dados do navegador (padrão: a do navegador escolhido)")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    env = env or db.SystemEnv()
    try:
        code, payload = run(args, env)
    except UsageError as exc:
        code, payload = 2, result(False, "usage_error", {}, [str(exc)], [])
    db.emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
