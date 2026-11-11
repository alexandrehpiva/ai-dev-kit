#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera e mescla a configuração do Playwright MCP para cada harness.

Uso:
    python3 scripts/configure_mcp.py --harness <claude|cursor|vscode|codex|gemini|windsurf>
        --scope user|project --mode extension|profile
        [--browser auto|<caminho>] [--server-name playwright-browser] [--version 0.0.85]
        [--user-data-dir <pasta>] [--profile-dir-name "Profile 1"]
        [--windows-launcher cmd|npx] [--project-dir <pasta>] [--config-file <arquivo>]
        [--force] [--apply]

Sem --apply NADA é gravado: o script mostra o plano (data.diff). Com --apply grava,
fazendo antes um backup <arquivo>.bak-<AAAAMMDD-HHMMSS>. Outros servidores do arquivo
são preservados. Se já existir um servidor com o mesmo nome e conteúdo diferente, o
status é `conflict` e nada é alterado (a menos que --force).

O token da Playwright Extension NUNCA é gravado: o bloco gerado referencia a variável
de ambiente PLAYWRIGHT_MCP_EXTENSION_TOKEN com a sintaxe de expansão de cada harness
(ou pede o valor em prompt, no VS Code).

Saída: JSON {"ok","status","data","problems","next_steps"} em stdout. Toda a saída é
redigida: valores de env/headers e args com cara de credencial (de QUALQUER servidor do
arquivo) aparecem como "<redacted:N chars>"; referências (${VAR}, ${env:VAR}, ${input:x},
%VAR%, $VAR) aparecem como estão. Com --apply o arquivo recebe os valores reais.
--scope project é recusado (usage_error) se --project-dir (padrão: cwd) for a pasta da skill.
Status: planned | applied | already_configured | conflict | browser_issue | usage_error.
Códigos de saída: 0 ok; 1 problema acionável (conflict, browser_issue); 2 erro de uso.

Variável de ambiente: GFORMS_MCP_VERSION sobrepõe a versão padrão do pacote.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import argparse
import difflib
import json
import ntpath
import os
import posixpath
import re
import shlex
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detect_browser as db  # noqa: E402

DEFAULT_SERVER_NAME = "playwright-browser"
DEFAULT_VERSION = "0.0.85"
VERSION_ENV = "GFORMS_MCP_VERSION"
TOKEN_ENV = "PLAYWRIGHT_MCP_EXTENSION_TOKEN"
VSCODE_INPUT_ID = "playwright-extension-token"
HARNESS_NAMES = ("claude", "cursor", "vscode", "codex", "gemini", "windsurf")

# Formato de cada harness. Fonte: documentação oficial de cada harness, lida em 2026-11-11.
#   claude   .mcp.json (projeto) / ~/.claude.json (user), chave mcpServers, ${VAR}  [OF]
#   cursor   .cursor/mcp.json / ~/.cursor/mcp.json, chave mcpServers, ${env:VAR}     [OF]
#   vscode   .vscode/mcp.json, chave "servers", inputs + ${input:id}                 [OF]
#            mcp.json do perfil do usuário: caminho por SO [não verificado]
#   codex    .codex/config.toml / ~/.codex/config.toml, [mcp_servers.<nome>], env_vars [OF]
#   gemini   .gemini/settings.json / ~/.gemini/settings.json, mcpServers, $VAR/${VAR} [OF]
#   windsurf ~/.codeium/windsurf/mcp_config.json, mcpServers                         [não verificado]
HARNESS_INFO = {
    "claude": {"format": "json", "key": "mcpServers", "label": "Claude Code"},
    "cursor": {"format": "json", "key": "mcpServers", "label": "Cursor"},
    "vscode": {"format": "json", "key": "servers", "label": "VS Code / Copilot"},
    "codex": {"format": "toml", "key": "mcp_servers", "label": "Codex"},
    "gemini": {"format": "json", "key": "mcpServers", "label": "Gemini CLI"},
    "windsurf": {"format": "json", "key": "mcpServers", "label": "Windsurf"},
}


class UsageError(Exception):
    pass


# Pasta da skill (pai de scripts/). Escopo project nunca pode apontar para dentro dela.
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def inside_skill_dir(path, skill_dir=None):
    """True se `path` (caminho absoluto do SO atual) é a pasta da skill ou está dentro dela."""
    if not path or not os.path.isabs(path):
        return False
    base = os.path.normcase(os.path.realpath(skill_dir or SKILL_DIR))
    cand = os.path.normcase(os.path.realpath(path))
    try:
        return os.path.commonpath([base, cand]) == base
    except ValueError:  # unidades diferentes no Windows
        return False


# ---------------------------------------------------------------------------
# Redação de segredos (só para EXIBIÇÃO: o arquivo gravado mantém os valores reais)
# ---------------------------------------------------------------------------

# Referências a variável não são segredo: ${VAR}, ${env:VAR}, ${input:x}, %VAR%, $VAR.
_REF_RE = re.compile(r"\$\{(?:env:|input:)?[A-Za-z0-9_.\-]+\}|\$[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*%")
# Nomes de chave/flag que sugerem credencial.
_SECRET_NAME_RE = re.compile(r"token|secret|passw|pwd|api[-_]?key|apikey|auth(?!ors?(?![a-z]))|credential|bearer|"
                             r"private[-_]?key|access[-_]?key|client[-_]?key|session|cookie|signature",
                             re.I)
# Contêineres cujos valores são todos tratados como segredo.
_SECRET_CONTAINERS = ("env", "headers", "http_headers", "env_http_headers")
# Prefixos conhecidos de tokens (OpenAI, GitHub, GitLab, Slack, AWS, Google, JWT).
_TOKEN_PREFIX_RE = re.compile(r"^(sk-|sk_|ghp_|gho_|ghs_|ghu_|github_pat_|glpat-|xox[abprs]-|AKIA|ASIA|AIza|"
                              r"ya29\.|eyJ[A-Za-z0-9_\-]{10,})")
_SCRUB_MIN_LEN = 8  # rede de segurança em texto livre: só valores com cara de token (ver _scrubbable)


def _scrubbable(value):
    """Valor aprendido que também é trocado em texto livre: >= 8 caracteres e com dígito ou símbolo.
    Palavras comuns (nomes, 'production') ficam só na redação estrutural e na de literal entre aspas,
    para não corromper caminhos e mensagens."""
    return len(value) >= _SCRUB_MIN_LEN and bool(re.search(r"[0-9\-_.+/=:@]", value))


def is_reference(value):
    """True se o valor só contém referências a variáveis (opcionalmente com 'Bearer '/'Basic ')."""
    if not isinstance(value, str) or not _REF_RE.search(value):
        return False
    rest = _REF_RE.sub("", value)
    rest = re.sub(r"(?i)\b(bearer|basic|token)\b", "", rest)
    return rest.strip() == ""


def placeholder(value):
    return "<redacted:%d chars>" % len(value)


class Redactor(object):
    """Aprende os segredos dos documentos lidos e devolve versões redigidas para exibição."""

    def __init__(self):
        self.secrets = set()
        self.literals = {}  # string original inteira -> string redigida

    def mask(self, value):
        if not isinstance(value, str) or value == "" or is_reference(value):
            return value
        self.secrets.add(value)
        return placeholder(value)

    def inline(self, s):
        """Redige trechos de credencial dentro de uma string comum."""
        if _TOKEN_PREFIX_RE.match(s):
            return self.mask(s)
        s = re.sub(r"(?i)(\bbearer\s+)(\S+)", lambda m: m.group(1) + self.mask(m.group(2)), s)
        s = re.sub(r"(?i)([?&][^=&#\s]*(?:token|key|secret|sig|auth|passw)[^=&#\s]*=)([^&#\s]+)",
                   lambda m: m.group(1) + self.mask(m.group(2)), s)
        s = re.sub(r"(://[^/\s:@]+:)([^@/\s]+)(@)", lambda m: m.group(1) + self.mask(m.group(2)) + m.group(3), s)
        return s

    def args(self, args):
        out, hide_next = [], False
        for a in args:
            if not isinstance(a, str):
                out.append(a)
                hide_next = False
                continue
            if hide_next and not a.startswith("-"):
                out.append(self.mask(a))
                hide_next = False
                continue
            hide_next = False
            m = re.match(r"^(--?[A-Za-z0-9_.\-]+)=(.*)$", a, re.S)
            if m and _SECRET_NAME_RE.search(m.group(1)):
                out.append(m.group(1) + "=" + self.mask(m.group(2)))
                continue
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*[=:]\s*(.+)$", a, re.S)
            if m and _SECRET_NAME_RE.search(m.group(1)):
                out.append(a[:m.start(2)] + self.mask(m.group(2)))
                continue
            if a.startswith("-") and _SECRET_NAME_RE.search(a):
                hide_next = True
                out.append(a)
                continue
            out.append(self.inline(a))
        return out

    def tree(self, obj, key=None, force=False):
        """Cópia redigida de um objeto JSON/TOML; registra cada string alterada."""
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                ks = k if isinstance(k, str) else ""
                f = force or ks.lower() in _SECRET_CONTAINERS or bool(_SECRET_NAME_RE.search(ks))
                out[k] = self.tree(v, ks, f)
            return out
        if isinstance(obj, list):
            if key == "args" and not force:
                red = self.args(obj)
                for o, r in zip(obj, red):
                    if isinstance(o, str) and o != r:
                        self.literals[o] = r
                return red
            return [self.tree(v, key, force) for v in obj]
        if isinstance(obj, str):
            red = self.mask(obj) if force else self.inline(obj)
            if red != obj:
                self.literals[obj] = red
            return red
        return obj

    def learn_text(self, text, fmt):
        """Lê o texto de configuração (json/toml) só para aprender os segredos."""
        if not text:
            return
        try:
            doc = toml_loads(text) if fmt == "toml" else load_json(text)[0]
        except ValueError:
            return
        self.tree(doc)

    def scrub(self, s):
        """Troca em texto livre toda ocorrência de segredo aprendido."""
        if not isinstance(s, str) or not (self.literals or self.secrets):
            return s
        for orig in sorted(self.literals, key=len, reverse=True):
            red = self.literals[orig]
            s = s.replace(json.dumps(orig, ensure_ascii=False), json.dumps(red, ensure_ascii=False))
            s = s.replace(json.dumps(orig), json.dumps(red))
            s = s.replace("'%s'" % orig, "'%s'" % red)
        for sec in sorted(self.secrets, key=len, reverse=True):
            if not _scrubbable(sec):
                continue
            for form in (sec, json.dumps(sec)[1:-1], json.dumps(sec, ensure_ascii=False)[1:-1]):
                s = s.replace(form, placeholder(sec))
        return s

    def payload(self, obj):
        """Aplica scrub em todas as strings (chaves inclusive) de um payload de saída."""
        if isinstance(obj, dict):
            return {self.scrub(k): self.payload(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.payload(v) for v in obj]
        if isinstance(obj, str):
            return self.scrub(obj)
        return obj


# ---------------------------------------------------------------------------
# Caminhos dos arquivos de configuração
# ---------------------------------------------------------------------------

def config_path(harness, scope, env, project_dir):
    """Devolve (caminho, notas). Levanta UsageError se a combinação não existir."""
    p = env.path
    home = env.home()
    notes = []
    if harness == "claude":
        if scope == "user":
            notes.append("Claude Code: o escopo user fica em ~/.claude.json, arquivo que o próprio Claude "
                         "Code reescreve o tempo todo. Prefira data.cli_command (claude mcp add-json), que "
                         "grava pelo próprio Claude Code; se aplicar o arquivo direto, faça com o Claude "
                         "Code fechado.")
            return p.join(home, ".claude.json"), notes
        return p.join(project_dir, ".mcp.json"), notes
    if harness == "cursor":
        return (p.join(home, ".cursor", "mcp.json") if scope == "user"
                else p.join(project_dir, ".cursor", "mcp.json")), notes
    if harness == "vscode":
        if scope == "project":
            return p.join(project_dir, ".vscode", "mcp.json"), notes
        notes.append("VS Code: caminho do mcp.json do perfil do usuário [não verificado]; confira com o "
                     "comando 'MCP: Open User Configuration' e use --config-file se for outro.")
        if env.os_name == "macos":
            return p.join(home, "Library", "Application Support", "Code", "User", "mcp.json"), notes
        if env.os_name == "windows":
            appdata = db.win_env(env, "APPDATA") or p.join(home, "AppData", "Roaming")
            return p.join(appdata, "Code", "User", "mcp.json"), notes
        cfg = env.environ.get("XDG_CONFIG_HOME") or p.join(home, ".config")
        return p.join(cfg, "Code", "User", "mcp.json"), notes
    if harness == "codex":
        if scope == "project":
            notes.append("Codex só lê .codex/config.toml de projeto marcado como confiável.")
            return p.join(project_dir, ".codex", "config.toml"), notes
        return p.join(home, ".codex", "config.toml"), notes
    if harness == "gemini":
        return (p.join(home, ".gemini", "settings.json") if scope == "user"
                else p.join(project_dir, ".gemini", "settings.json")), notes
    if harness == "windsurf":
        if scope == "project":
            raise UsageError("Windsurf: escopo project sem caminho confirmado; use --scope user ou informe "
                             "--config-file.")
        notes.append("Windsurf: ~/.codeium/windsurf/mcp_config.json [não verificado]; as docs migraram para "
                     "docs.devin.ai (~/.config/devin/mcp_config.json). Use --config-file se for o seu caso.")
        return p.join(home, ".codeium", "windsurf", "mcp_config.json"), notes
    raise UsageError("Harness desconhecido: %s" % harness)


def default_user_data_dir(env):
    if env.os_name == "windows":
        base = db.win_env(env, "LOCALAPPDATA") or ntpath.join(env.home(), "AppData", "Local")
        return ntpath.join(base, "google-forms-skill", "browser-profile")
    return posixpath.join(env.home(), ".local", "share", "google-forms-skill", "browser-profile")


# ---------------------------------------------------------------------------
# Montagem do bloco do servidor
# ---------------------------------------------------------------------------

def browser_args(mode, entry, user_data_dir, profile_dir_name):
    args = []
    channel = entry.get("playwright_channel")
    needs_exe = entry.get("needs_executable_path") or not channel
    if mode == "extension":
        args.append("--extension")
        # Chrome é o canal padrão; Edge precisa de --browser msedge (documentação do Playwright MCP).
        if channel and channel != "chrome":
            args += ["--browser", channel]
        if needs_exe:
            args += ["--executable-path", entry["executable"]]
        if profile_dir_name:
            args += ["--profile-dir-name", profile_dir_name]
    else:
        if needs_exe:
            args += ["--executable-path", entry["executable"]]
        else:
            args += ["--browser", channel]
        args += ["--user-data-dir", user_data_dir]
    return args


def token_reference(harness):
    """Valor que referencia a variável do token, sem gravar o segredo. None = sem expansão conhecida."""
    return {
        "claude": "${%s}" % TOKEN_ENV,          # [OF] expansão ${VAR} no .mcp.json
        "cursor": "${env:%s}" % TOKEN_ENV,      # [OF]
        "vscode": "${input:%s}" % VSCODE_INPUT_ID,  # [OF] inputs promptString
        "gemini": "${%s}" % TOKEN_ENV,          # [OF] $VAR / ${VAR} em env
    }.get(harness)


def build_server(harness, mode, entry, version, env, launcher, user_data_dir, profile_dir_name):
    """Devolve (bloco do servidor, input do VS Code ou None)."""
    npx_args = ["-y", "@playwright/mcp@%s" % version] + browser_args(mode, entry, user_data_dir,
                                                                   profile_dir_name)
    if env.os_name == "windows" and launcher == "cmd":
        command, args = "cmd", ["/c", "npx"] + npx_args
    else:
        command, args = "npx", npx_args
    vs_input = None
    if harness == "codex":
        server = {"command": command, "args": args}
        if mode == "extension":
            server["env_vars"] = [TOKEN_ENV]
        # O primeiro npx baixa o pacote: 10 s (padrão) pode não bastar [inferência].
        server["startup_timeout_sec"] = 60
        server["tool_timeout_sec"] = 120
        return server, None
    server = {}
    if harness in ("claude", "cursor", "vscode"):
        server["type"] = "stdio"
    server["command"] = command
    server["args"] = args
    ref = token_reference(harness)
    if mode == "extension" and ref:
        server["env"] = {TOKEN_ENV: ref}
    if harness == "vscode" and mode == "extension":
        vs_input = {"type": "promptString", "id": VSCODE_INPUT_ID,
                    "description": "Token da Playwright Extension (%s)" % TOKEN_ENV, "password": True}
    return server, vs_input


# ---------------------------------------------------------------------------
# JSON (aceita JSONC na leitura)
# ---------------------------------------------------------------------------

def strip_jsonc(text):
    """Remove comentários // e /* */ fora de strings e vírgulas finais."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(text):
    """Devolve (objeto, era_jsonc). Levanta ValueError se não for JSON nem JSONC."""
    if text is None or not text.strip():
        return {}, False
    try:
        return json.loads(text), False
    except ValueError:
        return json.loads(strip_jsonc(text)), True


def detect_indent(text):
    for line in (text or "").splitlines()[1:]:
        m = re.match(r"^([ \t]+)\S", line)
        if m:
            ws = m.group(1)
            return "\t" if ws.startswith("\t") else len(ws)
    return 2


def dump_json(obj, like_text):
    out = json.dumps(obj, ensure_ascii=False, indent=detect_indent(like_text))
    if like_text is None or like_text.endswith("\n") or not like_text:
        out += "\n"
    return out


def json_merge(text, harness, name, server, vs_input, force):
    """Devolve (novo_texto, estado, problemas). estado: add | same | conflict | replace | invalid."""
    problems = []
    try:
        doc, was_jsonc = load_json(text)
    except ValueError as exc:
        return None, "invalid", ["O arquivo não é JSON válido (%s); corrija-o à mão antes." % exc]
    if not isinstance(doc, dict):
        return None, "invalid", ["O arquivo não contém um objeto JSON na raiz."]
    key = HARNESS_INFO[harness]["key"]
    servers = doc.get(key)
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        return None, "invalid", ["A chave '%s' existe mas não é um objeto." % key]
    existing = servers.get(name)
    state = "add"
    if existing is not None:
        state = "same" if existing == server else "conflict"
    inputs_change = False
    if vs_input is not None:
        inputs = doc.get("inputs")
        if inputs is None:
            inputs = []
        if not isinstance(inputs, list):
            return None, "invalid", ["A chave 'inputs' existe mas não é uma lista."]
        same_id = [x for x in inputs if isinstance(x, dict) and x.get("id") == vs_input["id"]]
        if not same_id:
            inputs_change = True
        elif same_id[0] != vs_input and state != "conflict":
            state = "conflict"
            problems.append("Já existe um input '%s' diferente no arquivo." % vs_input["id"])
    if state == "same" and not inputs_change:
        return text, "same", problems
    if state == "same":
        state = "add"
    if state == "conflict" and not force:
        return text, "conflict", problems
    if was_jsonc:
        problems.append("O arquivo tem comentários ou vírgulas finais (JSONC): ao gravar eles serão "
                        "perdidos. Só aplique com --force e depois de avisar o usuário.")
        if not force:
            return text, "jsonc_needs_force", problems
    new_doc = dict(doc)
    new_servers = dict(servers)
    new_servers[name] = server
    if vs_input is not None:
        inputs = [x for x in (doc.get("inputs") or []) if not (isinstance(x, dict) and x.get("id") == vs_input["id"])]
        inputs.append(vs_input)
        new_doc["inputs"] = inputs
    new_doc[key] = new_servers
    return dump_json(new_doc, text), ("replace" if state == "conflict" else "add"), problems


# ---------------------------------------------------------------------------
# TOML (Codex): leitor mínimo + edição textual que preserva o resto do arquivo
# ---------------------------------------------------------------------------

class TomlError(ValueError):
    pass


def _skip_ws(s, i, newlines=True):
    n = len(s)
    while i < n:
        c = s[i]
        if c in " \t\r" or (newlines and c == "\n"):
            i += 1
        elif c == "#":
            j = s.find("\n", i)
            i = n if j < 0 else j
        else:
            break
    return i


def _parse_string(s, i):
    if s.startswith('"""', i) or s.startswith("'''", i):
        q = s[i:i + 3]
        j = s.find(q, i + 3)
        if j < 0:
            raise TomlError("string multilinha sem fim")
        body = s[i + 3:j]
        if body.startswith("\n"):
            body = body[1:]
        if q == '"""':
            body = json.loads('"%s"' % body.replace("\n", "\\n").replace('"', '\\"'))
        return body, j + 3
    if s[i] == "'":
        j = s.find("'", i + 1)
        if j < 0:
            raise TomlError("string literal sem fim")
        return s[i + 1:j], j + 1
    j = i + 1
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == '"':
            break
        if s[j] == "\n":
            raise TomlError("string sem fim")
        j += 1
    try:
        return json.loads(s[i:j + 1]), j + 1
    except ValueError:
        raise TomlError("string inválida")


def _parse_value(s, i):
    i = _skip_ws(s, i)
    if i >= len(s):
        raise TomlError("valor ausente")
    c = s[i]
    if c in "\"'":
        return _parse_string(s, i)
    if c == "[":
        arr = []
        i += 1
        while True:
            i = _skip_ws(s, i)
            if i < len(s) and s[i] == "]":
                return arr, i + 1
            v, i = _parse_value(s, i)
            arr.append(v)
            i = _skip_ws(s, i)
            if i < len(s) and s[i] == ",":
                i += 1
            elif i < len(s) and s[i] == "]":
                return arr, i + 1
            else:
                raise TomlError("array malformado")
    if c == "{":
        tbl = {}
        i += 1
        while True:
            i = _skip_ws(s, i, newlines=False)
            if i < len(s) and s[i] == "}":
                return tbl, i + 1
            keys, i = _parse_key(s, i)
            i = _skip_ws(s, i, newlines=False)
            if i >= len(s) or s[i] != "=":
                raise TomlError("tabela inline malformada")
            v, i = _parse_value(s, i + 1)
            _set_path(tbl, keys, v)
            i = _skip_ws(s, i, newlines=False)
            if i < len(s) and s[i] == ",":
                i += 1
    m = re.compile(r"[^\s,\]\}#]+").match(s, i)
    if not m:
        raise TomlError("valor inválido")
    tok = m.group(0)
    if tok == "true":
        return True, m.end()
    if tok == "false":
        return False, m.end()
    try:
        return int(tok.replace("_", ""), 0), m.end()
    except ValueError:
        pass
    try:
        return float(tok.replace("_", "")), m.end()
    except ValueError:
        return tok, m.end()  # datas e afins: mantidas como texto (não usamos)


def _parse_key(s, i):
    keys = []
    while True:
        i = _skip_ws(s, i, newlines=False)
        if i < len(s) and s[i] in "\"'":
            k, i = _parse_string(s, i)
        else:
            m = re.compile(r"[A-Za-z0-9_\-]+").match(s, i)
            if not m:
                raise TomlError("chave inválida")
            k, i = m.group(0), m.end()
        keys.append(k)
        i = _skip_ws(s, i, newlines=False)
        if i < len(s) and s[i] == ".":
            i += 1
            continue
        return keys, i


def _set_path(root, keys, value):
    cur = root
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
        if not isinstance(cur, dict):
            raise TomlError("chave redefinida")
    cur[keys[-1]] = value


def _get_table(root, keys, array=False):
    cur = root
    for idx, k in enumerate(keys):
        last = idx == len(keys) - 1
        if last and array:
            lst = cur.setdefault(k, [])
            lst.append({})
            return lst[-1]
        nxt = cur.setdefault(k, {})
        if isinstance(nxt, list):
            nxt = nxt[-1]
        cur = nxt
    return cur


def toml_loads(text):
    """Lê TOML com tomllib (Python 3.11+) ou, sem ele, com o leitor mínimo abaixo."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        return toml_loads_mini(text)
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise TomlError(str(exc))


def toml_loads_mini(text):
    """Leitor TOML mínimo (subconjunto usado por configs de harness: tabelas, strings, arrays,
    números, booleanos, tabelas inline, chaves com ponto). Não valida o TOML inteiro."""
    root = {}
    cur = root
    i = 0
    s = text
    while True:
        i = _skip_ws(s, i)
        if i >= len(s):
            return root
        if s.startswith("[[", i):
            keys, i = _parse_key(s, i + 2)
            if not s.startswith("]]", i):
                raise TomlError("cabeçalho [[...]] malformado")
            cur = _get_table(root, keys, array=True)
            i += 2
            continue
        if s[i] == "[":
            keys, i = _parse_key(s, i + 1)
            if i >= len(s) or s[i] != "]":
                raise TomlError("cabeçalho [...] malformado")
            cur = _get_table(root, keys)
            i += 1
            continue
        keys, i = _parse_key(s, i)
        i = _skip_ws(s, i, newlines=False)
        if i >= len(s) or s[i] != "=":
            raise TomlError("esperado '=' depois da chave")
        v, i = _parse_value(s, i + 1)
        _set_path(cur, keys, v)


def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)  # string básica TOML compatível
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join("%s = %s" % (toml_key(k), toml_value(x)) for k, x in v.items()) + " }"
    raise TypeError(type(v))


def toml_key(k):
    return k if re.match(r"^[A-Za-z0-9_\-]+$", k) else json.dumps(k)


def toml_block(name, server):
    lines = ["[mcp_servers.%s]" % toml_key(name)]
    for k, v in server.items():
        lines.append("%s = %s" % (toml_key(k), toml_value(v)))
    return "\n".join(lines) + "\n"


def toml_section_bounds(lines, name):
    """Linhas [início, fim) da tabela [mcp_servers.<name>] (incluindo subtabelas) ou None."""
    q = re.escape(name)
    head = re.compile(r'^\s*\[\s*mcp_servers\s*\.\s*(?:%s|"%s"|\'%s\')\s*(\]|\.)' % (q, q, q))
    start = None
    for idx, line in enumerate(lines):
        if start is None:
            if head.match(line):
                start = idx
            continue
        if re.match(r"^\s*\[", line) and not head.match(line):
            end = idx
            while end > start and not lines[end - 1].strip():
                end -= 1
            return start, end
    if start is None:
        return None
    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1
    return start, end


def toml_merge(text, name, server, force):
    text = text or ""
    try:
        doc = toml_loads(text)
    except TomlError as exc:
        return None, "invalid", ["O config.toml não pôde ser lido (%s); corrija-o à mão antes." % exc]
    servers = doc.get("mcp_servers") or {}
    existing = servers.get(name) if isinstance(servers, dict) else None
    if existing is None:
        sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        return text + sep + toml_block(name, server), "add", []
    if existing == server:
        return text, "same", []
    if not force:
        return text, "conflict", []
    lines = text.splitlines(True)
    b = toml_section_bounds(lines, name)
    if b is None:
        return text, "conflict", ["O servidor '%s' está definido em formato não tabular (inline/dotted); "
                                  "edite à mão." % name]
    start, end = b
    new = "".join(lines[:start]) + toml_block(name, server) + "".join(lines[end:])
    return new, "replace", []


# ---------------------------------------------------------------------------
# Escrita segura
# ---------------------------------------------------------------------------

def backup_path(path):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    cand = "%s.bak-%s" % (path, stamp)
    n = 1
    while os.path.exists(cand):
        cand = "%s.bak-%s-%d" % (path, stamp, n)
        n += 1
    return cand


def write_atomic(path, text):
    d = os.path.dirname(path) or "."
    if not os.path.isdir(d):
        os.makedirs(d)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        if os.path.exists(path):
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def make_diff(path, old, new, limit=300):
    lines = list(difflib.unified_diff((old or "").splitlines(True), (new or "").splitlines(True),
                                      fromfile=path + " (atual)", tofile=path + " (proposto)"))
    if len(lines) > limit:
        lines = lines[:limit] + ["... (diff truncado em %d linhas)\n" % limit]
    return "".join(lines)


# ---------------------------------------------------------------------------
# Comando alternativo via CLI do harness
# ---------------------------------------------------------------------------

def cli_command(harness, scope, name, server, env, mode):
    if harness == "claude":
        payload = json.dumps(server, ensure_ascii=False)
        if env.os_name == "windows":
            quoted = "'" + payload.replace("'", "''") + "'"  # PowerShell
        else:
            quoted = shlex.quote(payload)
        return "claude mcp add-json -s %s %s %s" % (scope, name, quoted)
    if harness == "vscode" and mode == "profile" and scope == "user":
        payload = dict(server, name=name)
        return "code --add-mcp %s" % shlex.quote(json.dumps(payload, ensure_ascii=False))
    return None


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def resolve_browser(spec, env, problems):
    """Devolve a entrada do navegador ou None (problema registrado)."""
    if spec and spec != "auto":
        entry, err = db.entry_from_path(spec, env)
        if entry is None:
            raise UsageError("--browser: %s" % err)
        return entry
    _, payload = db.detect(env, "auto")
    for p in payload["problems"]:
        problems.append("detect_browser: " + p)
    if payload["status"] == "invalid_override":
        raise UsageError(" ".join(payload["problems"]))
    rec = payload["data"].get("recommended")
    if payload["status"] == "non_chromium_default" and rec:
        problems.append("O navegador padrão não é Chromium; usado %s. Confirme com o usuário." % rec["name"])
    return rec


def configure(args, env):
    """Executa o fluxo e devolve o payload já redigido para exibição."""
    red = Redactor()
    code, payload = _configure(args, env, red)
    return code, red.payload(payload)


def _configure(args, env, red):
    problems, next_steps, notes = [], [], []
    if args.harness not in HARNESS_NAMES:
        raise UsageError("--harness inválido")
    if not re.match(r"^[A-Za-z0-9_\-]+$", args.server_name):
        raise UsageError("--server-name aceita só letras, números, '-' e '_'.")
    version = args.version or env.environ.get(VERSION_ENV) or DEFAULT_VERSION
    if not re.match(r"^(latest|next|[0-9A-Za-z.\-]+)$", version):
        raise UsageError("--version inválida: %s" % version)
    if args.mode == "extension" and args.user_data_dir:
        raise UsageError("--user-data-dir só vale com --mode profile.")
    if args.mode == "profile" and args.profile_dir_name:
        raise UsageError("--profile-dir-name só vale com --mode extension.")
    project_dir = os.path.abspath(args.project_dir or os.getcwd())
    if args.scope == "project" and not args.config_file and inside_skill_dir(project_dir):
        raise UsageError("--scope project apontando para a pasta da skill (%s): a configuração iria parar "
                         "dentro da skill. Rode o script a partir da raiz do projeto do usuário "
                         "(python3 <pasta-da-skill>/scripts/configure_mcp.py ...) ou passe "
                         "--project-dir <raiz do projeto>." % project_dir)

    if args.config_file:
        path, notes = os.path.abspath(os.path.expanduser(args.config_file)), []
    else:
        path, notes = config_path(args.harness, args.scope, env, project_dir)
    if inside_skill_dir(path):
        raise UsageError("O arquivo de configuração alvo (%s) fica dentro da pasta da skill. Rode a partir "
                         "da raiz do projeto do usuário ou passe --project-dir/--config-file fora da skill."
                         % path)

    data = {"harness": args.harness, "scope": args.scope, "mode": args.mode, "file": path,
            "server_name": args.server_name, "package": "@playwright/mcp@%s" % version,
            "browser": None, "server": None, "diff": "", "backup": None, "cli_command": None, "notes": notes}

    entry = resolve_browser(args.browser, env, problems)
    data["browser"] = entry
    if entry is None or not entry.get("chromium") or not entry.get("executable"):
        problems.append("Nenhum navegador Chromium utilizável foi encontrado.")
        next_steps.append("Rode detect_browser.py e resolva o navegador antes de configurar o MCP.")
        return 1, db.result(False, "browser_issue", data, problems, next_steps)
    if args.mode == "profile" and entry.get("packaging") in ("flatpak", "snap"):
        problems.append("%s via %s não suporta o modo perfil (sandbox); use --mode extension "
                        "[não verificado] ou instale o pacote nativo." % (entry["name"], entry["packaging"]))
        return 1, db.result(False, "browser_issue", data, problems, next_steps)
    if entry.get("packaging") in ("flatpak", "snap"):
        notes.append("Modo extensão com navegador %s: [não verificado]." % entry["packaging"])
    if args.mode == "extension" and entry.get("id") in ("opera", "arc"):
        problems.append("%s: instalar extensões da Chrome Web Store não está confirmado; o modo extensão "
                        "pode não funcionar [não verificado]." % entry["name"])

    user_data_dir = None
    if args.mode == "profile":
        user_data_dir = args.user_data_dir or default_user_data_dir(env)
        if args.user_data_dir:
            user_data_dir = os.path.abspath(os.path.expanduser(user_data_dir)) if env.os_name != "windows" \
                else user_data_dir
        udd_real = (entry.get("user_data_dir") or "").rstrip("/\\").lower()
        if udd_real and user_data_dir.rstrip("/\\").lower() == udd_real:
            raise UsageError("--user-data-dir não pode ser a pasta real do navegador (%s): conflita com o "
                             "navegador aberto e pode corromper o perfil. Use uma pasta dedicada."
                             % entry["user_data_dir"])
        if args.scope == "project":
            problems.append("Escopo project com --user-data-dir absoluto: o caminho é desta máquina e vai "
                            "para um arquivo versionável. Prefira --scope user.")

    if env.os_name == "windows" and args.windows_launcher == "npx":
        notes.append("Windows com 'npx' direto: há relatos de 'Connection closed'; se falhar, use "
                     "--windows-launcher cmd [comunidade].")
    if env.os_name == "windows" and args.windows_launcher == "cmd" and args.harness == "claude":
        notes.append("Se usar 'claude mcp add' com 'cmd /c', confira com 'claude mcp get %s': já houve bug "
                     "que trocou '/c' por 'C:/' [comunidade]." % args.server_name)

    server, vs_input = build_server(args.harness, args.mode, entry, version, env, args.windows_launcher,
                                    user_data_dir, args.profile_dir_name)
    data["server"] = red.tree(server)
    if vs_input:
        data["vscode_input"] = vs_input
    data["cli_command"] = cli_command(args.harness, args.scope, args.server_name, server, env, args.mode)

    old_text = env.read_text(path) if env.exists(path) else None
    if HARNESS_INFO[args.harness]["format"] == "toml":
        new_text, state, merge_problems = toml_merge(old_text, args.server_name, server, args.force)
    else:
        new_text, state, merge_problems = json_merge(old_text, args.harness, args.server_name, server,
                                                     vs_input, args.force)
    problems += merge_problems
    fmt = HARNESS_INFO[args.harness]["format"]
    red.learn_text(old_text, fmt)
    if new_text is not None:
        red.learn_text(new_text, fmt)

    if args.mode == "extension":
        token_steps(args.harness, env, next_steps, notes)

    if state == "invalid":
        return 1, db.result(False, "conflict", data, problems,
                            ["Corrija o arquivo %s à mão (ou escolha outro com --config-file)." % path])
    if state == "same":
        next_steps.insert(0, "Nada a fazer: o servidor '%s' já está configurado assim." % args.server_name)
        return 0, db.result(True, "already_configured", data, problems, next_steps)
    if state == "conflict":
        old_srv = _existing_server(old_text, args.harness, args.server_name)
        data["existing_server"] = red.tree(old_srv)
        problems.append("Já existe um servidor '%s' com configuração diferente em %s; nada foi alterado."
                        % (args.server_name, path))
        return 1, db.result(False, "conflict", data, problems,
                            ["Mostre ao usuário data.existing_server x data.server. Opções: usar outro "
                             "--server-name, ou --force para substituir (com backup)."] + next_steps)
    if state == "jsonc_needs_force":
        data["diff"] = ""
        return 1, db.result(False, "conflict", data, problems,
                            ["Peça autorização para reescrever o arquivo sem comentários e rode com --force."])

    # Exibição com segredos redigidos; o arquivo é gravado com new_text (valores reais).
    data["diff"] = make_diff(path, red.scrub(old_text), red.scrub(new_text))
    if state == "replace":
        problems.append("--force: o servidor '%s' existente será substituído." % args.server_name)

    if not args.apply:
        next_steps.insert(0, "Mostre data.diff ao usuário e, com a confirmação dele, rode de novo com --apply.")
        return 0, db.result(True, "planned", data, problems, next_steps)

    if old_text is not None:
        bak = backup_path(path)
        shutil.copy2(path, bak)
        data["backup"] = bak
    write_atomic(path, new_text)
    next_steps.insert(0, "Reinicie o %s para carregar o servidor e rode check_setup.py."
                      % HARNESS_INFO[args.harness]["label"])
    return 0, db.result(True, "applied", data, problems, next_steps)


def _existing_server(text, harness, name):
    try:
        if HARNESS_INFO[harness]["format"] == "toml":
            return (toml_loads(text or "").get("mcp_servers") or {}).get(name)
        doc, _ = load_json(text)
        return (doc.get(HARNESS_INFO[harness]["key"]) or {}).get(name)
    except (ValueError, AttributeError):
        return None


def token_steps(harness, env, next_steps, notes):
    """Instruções sobre o token (nunca lê nem imprime o valor; só verifica presença)."""
    if harness == "vscode":
        next_steps.append("O VS Code vai pedir o token (input '%s') na primeira vez; o usuário cola o valor "
                          "da página de status da extensão, nunca no chat." % VSCODE_INPUT_ID)
        return
    present = bool(env.environ.get(TOKEN_ENV))
    if env.os_name == "windows":
        how = 'setx %s "<token>" (e reabra terminal e harness)' % TOKEN_ENV
    else:
        how = "export %s=<token> no ~/.zshrc ou ~/.bashrc (ou cofre de segredos) e reabra o harness" % TOKEN_ENV
    if not present:
        next_steps.append("Defina a variável de ambiente %s pelo próprio usuário: %s. Nunca grave o valor em "
                          "arquivo de projeto nem cole no chat." % (TOKEN_ENV, how))
    if harness == "windsurf":
        notes.append("Windsurf: sintaxe de expansão de variável no mcp_config.json [não verificado]; o bloco "
                     "não tem 'env' e depende de o Windsurf herdar %s do ambiente." % TOKEN_ENV)
    if harness == "claude":
        notes.append("Claude Code: a expansão ${VAR} é documentada para .mcp.json; em ~/.claude.json "
                     "[não verificado].")
    if harness in ("cursor", "vscode", "windsurf") and env.os_name == "macos":
        notes.append("Apps abertos pelo Dock/Finder não herdam variáveis do shell [inferência]; abra o "
                     "editor pelo terminal depois do export.")


class _Parser(db._Parser):
    pass


def build_parser():
    ap = _Parser(description="Gera/mescla a config do Playwright MCP por harness (plano por padrão).")
    ap.add_argument("--harness", required=True, choices=list(HARNESS_NAMES), help="aplicativo cujo arquivo de configuração será gerado")
    ap.add_argument("--scope", required=True, choices=["user", "project"], help="user = config do usuário; project = config do projeto (nunca grava o token)")
    ap.add_argument("--mode", required=True, choices=["extension", "profile"], help="extension = navegador real do usuário; profile = perfil dedicado")
    ap.add_argument("--browser", default="auto", help="auto ou caminho do executável/.app")
    ap.add_argument("--server-name", default=DEFAULT_SERVER_NAME, help="nome do servidor MCP (padrão %s)" % DEFAULT_SERVER_NAME)
    ap.add_argument("--version", default=None, help="versão do @playwright/mcp (padrão %s)" % DEFAULT_VERSION)
    ap.add_argument("--user-data-dir", default=None, help="pasta dedicada do modo profile")
    ap.add_argument("--profile-dir-name", default=None, help='perfil do modo extension, ex.: "Profile 1"')
    ap.add_argument("--windows-launcher", default="cmd", choices=["cmd", "npx"],
                    help="Windows: 'cmd' gera cmd /c npx (padrão, mais robusto); 'npx' usa npx direto")
    ap.add_argument("--project-dir", default=None, help="raiz do projeto (padrão: diretório atual)")
    ap.add_argument("--config-file", default=None, help="força o arquivo de configuração alvo")
    ap.add_argument("--force", action="store_true", help="substitui servidor de mesmo nome (com backup)")
    ap.add_argument("--apply", action="store_true", help="grava de fato (sem isto, só plano)")
    return ap


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    env = env or db.SystemEnv()
    try:
        code, payload = configure(args, env)
    except UsageError as exc:
        code, payload = 2, db.result(False, "usage_error", {}, [str(exc)], [])
    db.emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
