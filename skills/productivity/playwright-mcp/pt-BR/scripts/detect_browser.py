#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detecta o navegador padrão do sistema e os navegadores Chromium instalados.

Uso:
    python3 scripts/detect_browser.py [--os auto|macos|windows|linux] [--list-profiles]
    (Windows: py -3 scripts\\detect_browser.py)

Saída: um único JSON em stdout no formato
    {"ok": bool, "status": str, "data": {...}, "problems": [str], "next_steps": [str]}
Códigos de saída: 0 = ok; 1 = problema acionável; 2 = erro de uso.

Status possíveis:
    chromium_default      o padrão é Chromium (Chrome, Edge, Brave, Vivaldi, Opera, Arc, Chromium)
    non_chromium_default  o padrão não é Chromium (ou não foi detectado); data.recommended
                          traz o Chromium instalado preferido
    no_chromium           nenhum Chromium instalado
    unsupported_os        sistema operacional fora de macOS/Windows/Linux
    invalid_override      PWMCP_BROWSER_PATH aponta para algo inexistente (exit 2)

Variável de ambiente:
    PWMCP_BROWSER_PATH   força o executável (ou o .app no macOS) do navegador a usar.

--list-profiles acrescenta data.profiles: os perfis do navegador escolhido (pasta, qual foi o último
usado, se há Cookies), lidos de `Local State`. Nomes e e-mails dos perfis NUNCA são lidos nem impressos.

Somente leitura: o script nunca altera registro, plist, perfis ou configurações.
Requer Python 3.8+ e apenas a biblioteca padrão.
"""

import argparse
import json
import ntpath
import os
import plistlib
import posixpath
import re
import shlex
import shutil
import subprocess
import sys

OVERRIDE_ENV = "PWMCP_BROWSER_PATH"
EXTENSION_ID = "mmlmfjhmonkocbjadbfplnigmagldckm"

WIN_ROOTS = ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)")

# Tabela de navegadores conhecidos.
# Fontes: macOS conferido localmente (Chrome, Edge, Brave); demais derivados do registro de
# navegadores do Playwright (playwright-core), do pacote default-browser e de fóruns —
# vários caminhos de Windows/Linux estão [não verificado].
# preference: menor = preferido quando o padrão não é Chromium (Chrome > Edge > Brave > Vivaldi > ...).
BROWSERS = {
    "chrome": {
        "name": "Google Chrome", "chromium": True, "channel": "chrome", "preference": 1,
        "mac_bundles": ["com.google.chrome"], "mac_app": "Google Chrome.app", "mac_exe": "Google Chrome",
        "mac_udd": "Google/Chrome",
        "win_progids": ["ChromeHTML"], "win_rel": [r"Google\Chrome\Application\chrome.exe"],
        "win_udd": ("LOCALAPPDATA", r"Google\Chrome\User Data"),
        "linux_desktops": ["google-chrome.desktop", "com.google.Chrome.desktop"],
        "linux_bins": ["/opt/google/chrome/chrome", "google-chrome-stable", "google-chrome"],
        "linux_udd": "google-chrome", "flatpak": "com.google.Chrome", "snap": None,
    },
    "chrome-beta": {
        "name": "Google Chrome Beta", "chromium": True, "channel": "chrome-beta", "preference": 5,
        "mac_bundles": ["com.google.chrome.beta"], "mac_app": "Google Chrome Beta.app",
        "mac_exe": "Google Chrome Beta", "mac_udd": "Google/Chrome Beta",
        "win_progids": ["ChromeBHTML"], "win_rel": [r"Google\Chrome Beta\Application\chrome.exe"],
        "win_udd": ("LOCALAPPDATA", r"Google\Chrome Beta\User Data"),
        "linux_desktops": ["google-chrome-beta.desktop"],
        "linux_bins": ["/opt/google/chrome-beta/chrome", "google-chrome-beta"],
        "linux_udd": "google-chrome-beta", "flatpak": None, "snap": None,
    },
    "chrome-dev": {
        "name": "Google Chrome Dev", "chromium": True, "channel": "chrome-dev", "preference": 6,
        "mac_bundles": ["com.google.chrome.dev"], "mac_app": "Google Chrome Dev.app",
        "mac_exe": "Google Chrome Dev", "mac_udd": "Google/Chrome Dev",
        "win_progids": ["ChromeDHTML"], "win_rel": [r"Google\Chrome Dev\Application\chrome.exe"],
        "win_udd": ("LOCALAPPDATA", r"Google\Chrome Dev\User Data"),
        "linux_desktops": ["google-chrome-unstable.desktop"],
        "linux_bins": ["/opt/google/chrome-unstable/chrome", "google-chrome-unstable"],
        "linux_udd": "google-chrome-unstable", "flatpak": None, "snap": None,
    },
    "chrome-canary": {
        "name": "Google Chrome Canary", "chromium": True, "channel": "chrome-canary", "preference": 7,
        "mac_bundles": ["com.google.chrome.canary"], "mac_app": "Google Chrome Canary.app",
        "mac_exe": "Google Chrome Canary", "mac_udd": "Google/Chrome Canary",
        "win_progids": [], "win_rel": [r"Google\Chrome SxS\Application\chrome.exe"],
        "win_udd": ("LOCALAPPDATA", r"Google\Chrome SxS\User Data"),
        "linux_desktops": ["google-chrome-canary.desktop"],
        "linux_bins": ["/opt/google/chrome-canary/chrome", "google-chrome-canary"],
        "linux_udd": "google-chrome-canary", "flatpak": None, "snap": None,
    },
    "msedge": {
        "name": "Microsoft Edge", "chromium": True, "channel": "msedge", "preference": 2,
        "mac_bundles": ["com.microsoft.edgemac"], "mac_app": "Microsoft Edge.app", "mac_exe": "Microsoft Edge",
        "mac_udd": "Microsoft Edge",
        "win_progids": ["MSEdgeHTM"], "win_rel": [r"Microsoft\Edge\Application\msedge.exe"],
        "win_udd": ("LOCALAPPDATA", r"Microsoft\Edge\User Data"),
        "linux_desktops": ["microsoft-edge.desktop", "com.microsoft.Edge.desktop"],
        "linux_bins": ["/opt/microsoft/msedge/msedge", "microsoft-edge-stable", "microsoft-edge"],
        "linux_udd": "microsoft-edge", "flatpak": "com.microsoft.Edge", "snap": None,
    },
    "msedge-beta": {
        "name": "Microsoft Edge Beta", "chromium": True, "channel": "msedge-beta", "preference": 8,
        "mac_bundles": ["com.microsoft.edgemac.beta"], "mac_app": "Microsoft Edge Beta.app",
        "mac_exe": "Microsoft Edge Beta", "mac_udd": "Microsoft Edge Beta",
        "win_progids": ["MSEdgeBHTML"], "win_rel": [r"Microsoft\Edge Beta\Application\msedge.exe"],
        "win_udd": ("LOCALAPPDATA", r"Microsoft\Edge Beta\User Data"),
        "linux_desktops": ["microsoft-edge-beta.desktop"],
        "linux_bins": ["/opt/microsoft/msedge-beta/msedge", "microsoft-edge-beta"],
        "linux_udd": "microsoft-edge-beta", "flatpak": None, "snap": None,
    },
    "msedge-dev": {
        "name": "Microsoft Edge Dev", "chromium": True, "channel": "msedge-dev", "preference": 9,
        "mac_bundles": ["com.microsoft.edgemac.dev"], "mac_app": "Microsoft Edge Dev.app",
        "mac_exe": "Microsoft Edge Dev", "mac_udd": "Microsoft Edge Dev",
        "win_progids": ["MSEdgeDHTML"], "win_rel": [r"Microsoft\Edge Dev\Application\msedge.exe"],
        "win_udd": ("LOCALAPPDATA", r"Microsoft\Edge Dev\User Data"),
        "linux_desktops": ["microsoft-edge-dev.desktop"],
        "linux_bins": ["/opt/microsoft/msedge-dev/msedge", "microsoft-edge-dev"],
        "linux_udd": "microsoft-edge-dev", "flatpak": None, "snap": None,
    },
    "brave": {
        "name": "Brave Browser", "chromium": True, "channel": None, "preference": 3,
        "mac_bundles": ["com.brave.browser"], "mac_app": "Brave Browser.app", "mac_exe": "Brave Browser",
        "mac_udd": "BraveSoftware/Brave-Browser",
        "win_progids": ["BraveHTML"], "win_rel": [r"BraveSoftware\Brave-Browser\Application\brave.exe"],
        "win_udd": ("LOCALAPPDATA", r"BraveSoftware\Brave-Browser\User Data"),
        "linux_desktops": ["brave-browser.desktop", "com.brave.Browser.desktop", "brave_brave.desktop"],
        "linux_bins": ["brave-browser", "brave-browser-stable", "/opt/brave.com/brave/brave"],
        "linux_udd": "BraveSoftware/Brave-Browser", "flatpak": "com.brave.Browser", "snap": "brave",
    },
    "brave-beta": {
        "name": "Brave Browser Beta", "chromium": True, "channel": None, "preference": 10,
        "mac_bundles": ["com.brave.browser.beta"], "mac_app": "Brave Browser Beta.app",
        "mac_exe": "Brave Browser Beta", "mac_udd": "BraveSoftware/Brave-Browser-Beta",
        "win_progids": ["BraveBHTML", "BraveDHTML"],
        "win_rel": [r"BraveSoftware\Brave-Browser-Beta\Application\brave.exe"],
        "win_udd": ("LOCALAPPDATA", r"BraveSoftware\Brave-Browser-Beta\User Data"),
        "linux_desktops": ["brave-browser-beta.desktop"], "linux_bins": ["brave-browser-beta"],
        "linux_udd": "BraveSoftware/Brave-Browser-Beta", "flatpak": None, "snap": None,
    },
    "brave-nightly": {
        "name": "Brave Browser Nightly", "chromium": True, "channel": None, "preference": 11,
        "mac_bundles": ["com.brave.browser.nightly"], "mac_app": "Brave Browser Nightly.app",
        "mac_exe": "Brave Browser Nightly", "mac_udd": "BraveSoftware/Brave-Browser-Nightly",
        "win_progids": ["BraveSSHTM"],
        "win_rel": [r"BraveSoftware\Brave-Browser-Nightly\Application\brave.exe"],
        "win_udd": ("LOCALAPPDATA", r"BraveSoftware\Brave-Browser-Nightly\User Data"),
        "linux_desktops": ["brave-browser-nightly.desktop"], "linux_bins": ["brave-browser-nightly"],
        "linux_udd": "BraveSoftware/Brave-Browser-Nightly", "flatpak": None, "snap": None,
    },
    "vivaldi": {
        "name": "Vivaldi", "chromium": True, "channel": None, "preference": 4,
        "mac_bundles": ["com.vivaldi.vivaldi"], "mac_app": "Vivaldi.app", "mac_exe": "Vivaldi",
        "mac_udd": "Vivaldi",
        "win_progids": ["VivaldiHTM"], "win_rel": [r"Vivaldi\Application\vivaldi.exe"],
        "win_udd": ("LOCALAPPDATA", r"Vivaldi\User Data"),
        "linux_desktops": ["vivaldi-stable.desktop", "com.vivaldi.Vivaldi.desktop"],
        "linux_bins": ["vivaldi-stable", "vivaldi", "/opt/vivaldi/vivaldi"],
        "linux_udd": "vivaldi", "flatpak": "com.vivaldi.Vivaldi", "snap": None,
    },
    "opera": {
        "name": "Opera", "chromium": True, "channel": None, "preference": 13,
        "mac_bundles": ["com.operasoftware.opera"], "mac_app": "Opera.app", "mac_exe": "Opera",
        "mac_udd": "com.operasoftware.Opera",
        "win_progids": ["OperaStable"], "win_rel": [r"Programs\Opera\opera.exe"],
        "win_udd": ("APPDATA", r"Opera Software\Opera Stable"),
        "linux_desktops": ["opera.desktop", "com.opera.Opera.desktop"], "linux_bins": ["opera"],
        "linux_udd": "opera", "flatpak": "com.opera.Opera", "snap": None,
    },
    "arc": {
        "name": "Arc", "chromium": True, "channel": None, "preference": 14,
        "mac_bundles": ["company.thebrowser.browser"], "mac_app": "Arc.app", "mac_exe": "Arc",
        "mac_udd": "Arc/User Data",
        "win_progids": [], "win_rel": [], "win_udd": ("LOCALAPPDATA", r"Arc\User Data"),
        "linux_desktops": [], "linux_bins": [], "linux_udd": None, "flatpak": None, "snap": None,
    },
    "chromium": {
        "name": "Chromium", "chromium": True, "channel": None, "preference": 12,
        "mac_bundles": ["org.chromium.chromium"], "mac_app": "Chromium.app", "mac_exe": "Chromium",
        "mac_udd": "Chromium",
        "win_progids": ["ChromiumHTM"], "win_rel": [r"Chromium\Application\chrome.exe"],
        "win_udd": ("LOCALAPPDATA", r"Chromium\User Data"),
        "linux_desktops": ["chromium.desktop", "chromium-browser.desktop", "chromium_chromium.desktop",
                           "org.chromium.Chromium.desktop"],
        "linux_bins": ["chromium", "chromium-browser"],
        "linux_udd": "chromium", "flatpak": "org.chromium.Chromium", "snap": "chromium",
    },
    # Não-Chromium: só para classificar o padrão.
    "safari": {"name": "Safari", "chromium": False, "mac_bundles": ["com.apple.safari"]},
    "firefox": {
        "name": "Firefox", "chromium": False, "mac_bundles": ["org.mozilla.firefox"],
        "win_progids": ["FirefoxURL", "FirefoxHTML"],
        "linux_desktops": ["firefox.desktop", "firefox_firefox.desktop", "org.mozilla.firefox.desktop",
                           "firefox-esr.desktop"],
    },
    "edge-legacy": {"name": "Microsoft Edge (legado, EdgeHTML)", "chromium": False,
                    "win_progids": ["AppXq0fevzme2pys62n3e0fbqa7peapykr8v"]},
    "ie": {"name": "Internet Explorer", "chromium": False, "win_progids": ["IE.HTTP"]},
}

# Identificação por trecho do caminho do executável (ordem importa: chromium antes de chrome).
EXE_PATTERNS = [
    ("msedge", ("msedge", "microsoft edge", "microsoft-edge")),
    ("brave", ("brave",)),
    ("vivaldi", ("vivaldi",)),
    ("opera", ("opera",)),
    ("arc", ("arc.app", "arc.exe", "thebrowsercompany")),
    ("chromium", ("chromium",)),
    ("chrome", ("chrome",)),
    ("firefox", ("firefox",)),
    ("safari", ("safari",)),
]

# Caminhos onde o Playwright acha cada canal sozinho (sem --executable-path).
# Fonte: registro de navegadores do playwright-core (registry/index.ts).
PLAYWRIGHT_MAC = {
    "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "chrome-beta": "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
    "chrome-dev": "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev",
    "chrome-canary": "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "msedge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "msedge-beta": "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta",
    "msedge-dev": "/Applications/Microsoft Edge Dev.app/Contents/MacOS/Microsoft Edge Dev",
}
PLAYWRIGHT_LINUX = {
    "chrome": "/opt/google/chrome/chrome",
    "chrome-beta": "/opt/google/chrome-beta/chrome",
    "chrome-dev": "/opt/google/chrome-unstable/chrome",
    "chrome-canary": "/opt/google/chrome-canary/chrome",
    "msedge": "/opt/microsoft/msedge/msedge",
    "msedge-beta": "/opt/microsoft/msedge-beta/msedge",
    "msedge-dev": "/opt/microsoft/msedge-dev/msedge",
}
PLAYWRIGHT_WIN_REL = {
    "chrome": r"Google\Chrome\Application\chrome.exe",
    "chrome-beta": r"Google\Chrome Beta\Application\chrome.exe",
    "chrome-dev": r"Google\Chrome Dev\Application\chrome.exe",
    "chrome-canary": r"Google\Chrome SxS\Application\chrome.exe",
    "msedge": r"Microsoft\Edge\Application\msedge.exe",
    "msedge-beta": r"Microsoft\Edge Beta\Application\msedge.exe",
    "msedge-dev": r"Microsoft\Edge Dev\Application\msedge.exe",
}

REG_USERCHOICE = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\{scheme}\{leaf}"


# ---------------------------------------------------------------------------
# Acesso ao sistema (injetável nos testes)
# ---------------------------------------------------------------------------

def host_os():
    """Devolve 'macos', 'windows', 'linux' ou o nome cru do sistema."""
    p = sys.platform
    if p == "darwin":
        return "macos"
    if p.startswith("win") or p == "cygwin":
        return "windows"
    if p.startswith("linux"):
        return "linux"
    return p


class SystemEnv(object):
    """Fachada de leitura do sistema. Os testes substituem por uma versão falsa."""

    def __init__(self, os_name=None, environ=None):
        self.os_name = os_name or host_os()
        self.environ = dict(os.environ) if environ is None else dict(environ)
        self.path = ntpath if self.os_name == "windows" else posixpath

    # --- caminhos e arquivos
    def home(self):
        if self.os_name == "windows":
            h = self.environ.get("USERPROFILE")
            if h:
                return h
        h = self.environ.get("HOME")
        return h or os.path.expanduser("~")

    def exists(self, p):
        return bool(p) and os.path.exists(p)

    def isfile(self, p):
        return bool(p) and os.path.isfile(p)

    def isdir(self, p):
        return bool(p) and os.path.isdir(p)

    def listdir(self, p):
        try:
            return sorted(os.listdir(p))
        except OSError:
            return []

    def read_bytes(self, p):
        try:
            with open(p, "rb") as fh:
                return fh.read()
        except (OSError, IOError):
            return None

    def read_text(self, p):
        b = self.read_bytes(p)
        if b is None:
            return None
        return b.decode("utf-8", errors="replace")

    def which(self, name):
        return shutil.which(name, path=self.environ.get("PATH"))

    def run(self, cmd, timeout=5, cwd=None):
        """Executa um comando (somente-leitura, exceto o registro do configure_mcp.py). Devolve (returncode|None, stdout)."""
        try:
            cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=timeout, check=False, cwd=cwd)
        except (OSError, subprocess.SubprocessError):
            return None, ""
        return cp.returncode, cp.stdout.decode("utf-8", errors="replace")

    # --- registro do Windows (somente leitura)
    def reg_get(self, hive, subkey, value_name):
        """Lê um valor REG_SZ. value_name '' = valor padrão. Devolve str ou None."""
        try:
            import winreg  # noqa: WPS433 (só existe no Windows)
        except ImportError:
            winreg = None
        if winreg is not None:
            root = {"HKCU": winreg.HKEY_CURRENT_USER, "HKCR": winreg.HKEY_CLASSES_ROOT,
                    "HKLM": winreg.HKEY_LOCAL_MACHINE}[hive]
            try:
                with winreg.OpenKey(root, subkey) as k:
                    val, _ = winreg.QueryValueEx(k, value_name)
                    return str(val)
            except OSError:
                return None
        if self.os_name != "windows":
            return None
        cmd = ["reg", "query", hive + "\\" + subkey]
        cmd += ["/ve"] if value_name == "" else ["/v", value_name]
        rc, out = self.run(cmd)
        if rc != 0:
            return None
        return parse_reg_query(out, value_name)


def parse_reg_query(output, value_name):
    """Extrai o valor de uma saída de `reg query`.

    Linhas no formato: '    ProgId    REG_SZ    ChromeHTML'. Para o valor padrão
    (value_name == '') o nome vem localizado ('(Default)', '(Padrão)'...), então
    pega a primeira linha REG_*.
    """
    rx = re.compile(r"^\s+(.*?)\s{2,}(REG_[A-Z_]+)\s{2,}(.*?)\s*$")
    for line in output.splitlines():
        m = rx.match(line)
        if not m:
            continue
        name, _typ, val = m.group(1), m.group(2), m.group(3)
        if value_name == "":
            return val
        if name.lower() == value_name.lower():
            return val
    return None


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def make_entry(key, executable, user_data_dir, packaging, env, name=None, raw_id=None, chromium=None):
    info = BROWSERS.get(key, {})
    channel = info.get("channel")
    is_chromium = info.get("chromium", False) if chromium is None else chromium
    entry = {
        "name": name or info.get("name") or (key or "desconhecido"),
        "id": key or "unknown",
        "raw_id": raw_id,
        "executable": executable,
        "user_data_dir": user_data_dir,
        "chromium": bool(is_chromium),
        "playwright_channel": channel if is_chromium else None,
        "needs_executable_path": bool(is_chromium) and not playwright_finds_channel(channel, env),
        "packaging": packaging,
    }
    return entry


def playwright_finds_channel(channel, env):
    """True se o Playwright acha o canal sozinho (executável no caminho padrão dele)."""
    if not channel:
        return False
    for cand in playwright_default_paths(channel, env):
        if env.exists(cand):
            return True
    return False


def playwright_default_paths(channel, env):
    if env.os_name == "macos":
        p = PLAYWRIGHT_MAC.get(channel)
        return [p] if p else []
    if env.os_name == "linux":
        p = PLAYWRIGHT_LINUX.get(channel)
        return [p] if p else []
    if env.os_name == "windows":
        rel = PLAYWRIGHT_WIN_REL.get(channel)
        if not rel:
            return []
        out = []
        for root in WIN_ROOTS:
            base = win_env(env, root)
            if base:
                out.append(ntpath.join(base, rel))
        return out
    return []


def win_env(env, name):
    """Variável de ambiente do Windows (nome sem diferenciar maiúsculas)."""
    low = name.lower()
    for k, v in env.environ.items():
        if k.lower() == low:
            return v
    return None


def expand_win_vars(s, env):
    def repl(m):
        v = win_env(env, m.group(1))
        return v if v is not None else m.group(0)
    return re.sub(r"%([^%]+)%", repl, s)


def identify_by_path(path):
    low = (path or "").replace("\\", "/").lower()
    for key, needles in EXE_PATTERNS:
        for n in needles:
            if n in low:
                return key
    return None


def key_for_bundle(bundle_id):
    b = (bundle_id or "").lower()  # o plist do LaunchServices grava em minúsculas
    for key, info in BROWSERS.items():
        if b in [x.lower() for x in info.get("mac_bundles", [])]:
            return key
    return None


def key_for_progid(progid):
    """ProgId → chave. Tenta exato e depois sem sufixo '.hash' ou '-hash' (regra do default-browser)."""
    if not progid:
        return None
    cands = [progid, re.split(r"[.\-]", progid, maxsplit=1)[0]]
    for c in cands:
        for key, info in BROWSERS.items():
            if c.lower() in [x.lower() for x in info.get("win_progids", [])]:
                return key
    return None


def key_for_desktop(desktop):
    d = (desktop or "").lower()
    for key, info in BROWSERS.items():
        if d in [x.lower() for x in info.get("linux_desktops", [])]:
            return key
    return None


def chromium_heuristic_mac_app(app, env):
    """Inferência: apps Chromium trazem um '*Framework.framework' com nome Chromium/Chrome/etc."""
    fw = env.path.join(app, "Contents", "Frameworks")
    for name in env.listdir(fw):
        low = name.lower()
        if low.endswith("framework.framework") and any(
                k in low for k in ("chromium", "chrome", "brave", "edge", "vivaldi", "opera", "arc")):
            return True
    return False


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------

MAC_JXA = ('ObjC.import("AppKit"); '
           '$.NSWorkspace.sharedWorkspace.URLForApplicationToOpenURL('
           '$.NSURL.URLWithString("https://example.com")).path.js')


def mac_launchservices_bundle(env):
    """Lê LSHandlers do plist do LaunchServices (https, depois http). Devolve bundle id ou None."""
    p = env.path.join(env.home(), "Library", "Preferences", "com.apple.LaunchServices",
                      "com.apple.launchservices.secure.plist")
    raw = env.read_bytes(p)
    if not raw:
        return None
    try:
        data = plistlib.loads(raw)
    except Exception:  # plist corrompido ou formato inesperado
        return None
    handlers = data.get("LSHandlers", []) if isinstance(data, dict) else []
    for scheme in ("https", "http"):
        for h in handlers:
            if not isinstance(h, dict):
                continue
            if str(h.get("LSHandlerURLScheme", "")).lower() != scheme:
                continue
            role = h.get("LSHandlerRoleAll")
            if role and role != "-":
                return str(role)
    return None


def mac_read_info(app, env):
    raw = env.read_bytes(env.path.join(app, "Contents", "Info.plist"))
    if not raw:
        return {}
    try:
        d = plistlib.loads(raw)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def mac_app_entry(key, app, env, raw_id=None):
    info = mac_read_info(app, env)
    binfo = BROWSERS.get(key, {})
    exe_name = info.get("CFBundleExecutable") or binfo.get("mac_exe")
    if not exe_name:
        return None
    exe = env.path.join(app, "Contents", "MacOS", exe_name)
    if not env.isfile(exe):
        return None
    udd = None
    if binfo.get("mac_udd"):
        udd = env.path.join(env.home(), "Library", "Application Support", binfo["mac_udd"])
    chromium = None
    name = None
    if key is None:
        chromium = chromium_heuristic_mac_app(app, env)
        name = info.get("CFBundleName") or env.path.basename(app)
    return make_entry(key, exe, udd, "native", env, name=name,
                      raw_id=raw_id or info.get("CFBundleIdentifier"), chromium=chromium)


def mac_scan(env):
    out = []
    roots = ["/Applications", env.path.join(env.home(), "Applications")]
    for key, info in BROWSERS.items():
        if not info.get("chromium") or not info.get("mac_app"):
            continue
        for root in roots:
            app = env.path.join(root, info["mac_app"])
            if env.isdir(app):
                e = mac_app_entry(key, app, env)
                if e:
                    out.append(e)
                    break
    return out


def mac_find_app(bundle_id, env):
    """Localiza o .app por bundle id (case-insensitive) via Spotlight."""
    rc, out = env.run(["mdfind", 'kMDItemCFBundleIdentifier == "%s"c' % bundle_id])
    if rc == 0:
        for line in out.splitlines():
            line = line.strip()
            if line.endswith(".app"):
                return line
    return None


def detect_macos(env, problems):
    installed = mac_scan(env)
    source = "launchservices_plist"
    bundle = mac_launchservices_bundle(env)
    app_from_ws = None
    if not bundle:
        rc, out = env.run(["osascript", "-l", "JavaScript", "-e", MAC_JXA])
        path = out.strip() if rc == 0 else ""
        if path.endswith(".app"):
            app_from_ws = path
            bundle = mac_read_info(path, env).get("CFBundleIdentifier")
            source = "nsworkspace"
    if not bundle:
        bundle = "com.apple.Safari"
        source = "system_default_assumed"
        problems.append("Nenhum handler https/http no LaunchServices: assumido Safari, o padrão do macOS "
                        "[inferência].")
    key = key_for_bundle(bundle)
    default = None
    if key and not BROWSERS[key].get("chromium"):
        default = make_entry(key, None, None, "native", env, raw_id=bundle)
    elif key:
        default = next((e for e in installed if e["id"] == key), None)
        if default is None:
            app = app_from_ws or mac_find_app(bundle, env)
            if app:
                default = mac_app_entry(key, app, env, raw_id=bundle)
                if default:
                    installed.append(default)
        if default is None:
            problems.append("O navegador padrão (%s) está registrado, mas o executável não foi encontrado."
                            % BROWSERS[key]["name"])
            default = make_entry(key, None, None, "native", env, raw_id=bundle)
        else:
            default = dict(default, raw_id=bundle)
    else:
        app = app_from_ws or mac_find_app(bundle, env)
        if app:
            default = mac_app_entry(None, app, env, raw_id=bundle)
            if default and default["chromium"]:
                problems.append("Navegador padrão desconhecido (%s); classificado como Chromium por "
                                "heurística [inferência]." % bundle)
        if default is None:
            default = make_entry(None, None, None, "native", env, name=bundle, raw_id=bundle, chromium=False)
    return default, installed, source


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

def parse_command_exe(cmd):
    """Primeiro token de uma linha de comando do registro (entre aspas ou até o espaço)."""
    if not cmd:
        return None
    cmd = cmd.strip()
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        return cmd[1:end] if end > 0 else cmd[1:]
    m = re.match(r"(.+?\.exe)\b", cmd, re.IGNORECASE)
    if m:
        return m.group(1)
    return cmd.split(" ", 1)[0]


def win_udd(key, env):
    spec = BROWSERS.get(key, {}).get("win_udd")
    if not spec:
        return None
    base = win_env(env, spec[0])
    return ntpath.join(base, spec[1]) if base else None


def win_scan(env):
    out = []
    for key, info in BROWSERS.items():
        if not info.get("chromium"):
            continue
        found = None
        for rel in info.get("win_rel", []):
            for root in WIN_ROOTS:
                base = win_env(env, root)
                if not base:
                    continue
                cand = ntpath.join(base, rel)
                if env.isfile(cand):
                    found = cand
                    break
            if found:
                break
        if found:
            out.append(make_entry(key, found, win_udd(key, env), "native", env))
    return out


def detect_windows(env, problems):
    installed = win_scan(env)
    progid = None
    source = None
    for scheme in ("https", "http"):
        progid = env.reg_get("HKCU", REG_USERCHOICE.format(scheme=scheme, leaf="UserChoice"), "ProgId")
        if progid:
            source = "registry:%s\\UserChoice" % scheme
            latest = env.reg_get("HKCU", REG_USERCHOICE.format(scheme=scheme, leaf="UserChoiceLatest"),
                                 "ProgId")
            if latest and latest != progid:
                problems.append("UserChoice (%s) e UserChoiceLatest (%s) divergem; usado UserChoice. "
                                "Confirme com o usuário qual é o navegador padrão [não verificado]."
                                % (progid, latest))
            break
    if not progid:
        problems.append("UserChoice ausente no registro: não foi possível detectar o navegador padrão.")
        return None, installed, "registry"
    key = key_for_progid(progid)
    cmd = env.reg_get("HKCR", progid + r"\shell\open\command", "")
    exe = parse_command_exe(cmd)
    if exe:
        exe = expand_win_vars(exe, env)
    if key is None and exe:
        key = identify_by_path(exe)
    if key and not BROWSERS[key].get("chromium"):
        return make_entry(key, exe, None, "native", env, raw_id=progid), installed, source
    if key is None:
        problems.append("ProgId desconhecido (%s); não deu para classificar o navegador." % progid)
        return (make_entry(None, exe, None, "native", env, name=progid, raw_id=progid, chromium=False),
                installed, source)
    default = None
    if exe and env.isfile(exe):
        default = make_entry(key, exe, win_udd(key, env), "native", env, raw_id=progid)
        if not any(e["id"] == key for e in installed):
            installed.append(default)
    else:
        default = next((e for e in installed if e["id"] == key), None)
        if default:
            default = dict(default, raw_id=progid)
        else:
            problems.append("O navegador padrão (%s) está registrado, mas o executável não foi encontrado."
                            % BROWSERS[key]["name"])
            default = make_entry(key, exe, win_udd(key, env), "native", env, raw_id=progid)
    return default, installed, source


# ---------------------------------------------------------------------------
# Linux
# ---------------------------------------------------------------------------

def linux_desktop_dirs(env):
    home = env.home()
    data_home = env.environ.get("XDG_DATA_HOME") or posixpath.join(home, ".local", "share")
    dirs = [data_home]
    dirs += [d for d in (env.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
    dirs += [posixpath.join(home, ".local/share/flatpak/exports/share"), "/var/lib/flatpak/exports/share"]
    out = [posixpath.join(d, "applications") for d in dirs]
    out.append("/var/lib/snapd/desktop/applications")
    seen = []
    for d in out:
        if d not in seen:
            seen.append(d)
    return seen


def parse_desktop_exec(text):
    """Primeira linha Exec= da seção [Desktop Entry], já sem códigos %U/%f etc."""
    section = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s
            continue
        if section == "[Desktop Entry]" and s.startswith("Exec="):
            try:
                argv = shlex.split(s[len("Exec="):])
            except ValueError:
                argv = s[len("Exec="):].split()
            return [a for a in argv if not re.match(r"^%[a-zA-Z]$", a)]
    return None


def linux_exec_info(argv, desktop_path, env):
    """Interpreta o Exec: devolve (executável, empacotamento, app_id)."""
    argv = list(argv or [])
    while argv and (argv[0] == "env" or (argv[0] and "=" in argv[0] and not argv[0].startswith("/"))):
        argv.pop(0)
    if not argv:
        return None, "native", None
    first = argv[0]
    if posixpath.basename(first) == "flatpak":
        app_id = None
        seen_run = False
        for a in argv[1:]:
            if a == "run":
                seen_run = True
                continue
            if seen_run and not a.startswith("-") and not a.startswith("@@"):
                app_id = a
                break
        exe = None
        if app_id:
            for d in (posixpath.join(env.home(), ".local/share/flatpak/exports/bin"),
                      "/var/lib/flatpak/exports/bin"):
                c = posixpath.join(d, app_id)
                if env.exists(c):
                    exe = c
                    break
        return exe, "flatpak", app_id
    if first.startswith("/snap/") or (desktop_path or "").startswith("/var/lib/snapd/"):
        return first if first.startswith("/") else env.which(first), "snap", posixpath.basename(first)
    exe = first if first.startswith("/") else env.which(first)
    return exe, "native", None


def linux_udd(key, packaging, app_id, env):
    info = BROWSERS.get(key, {})
    sub = info.get("linux_udd")
    if not sub:
        return None
    home = env.home()
    if packaging == "flatpak":
        app_id = app_id or info.get("flatpak")
        return posixpath.join(home, ".var/app", app_id, "config", sub) if app_id else None
    if packaging == "snap":
        if key == "chromium":
            return posixpath.join(home, "snap/chromium/common/chromium")  # [não verificado]
        return None
    cfg = env.environ.get("XDG_CONFIG_HOME") or posixpath.join(home, ".config")
    return posixpath.join(cfg, sub)


def linux_scan(env):
    out = []
    home = env.home()
    for key, info in BROWSERS.items():
        if not info.get("chromium"):
            continue
        native = None
        for b in info.get("linux_bins", []):
            cand = b if b.startswith("/") else env.which(b)
            if cand and env.exists(cand):
                native = cand
                break
        if native:
            out.append(make_entry(key, native, linux_udd(key, "native", None, env), "native", env))
        fid = info.get("flatpak")
        if fid:
            for d in (posixpath.join(home, ".local/share/flatpak/exports/bin"), "/var/lib/flatpak/exports/bin"):
                c = posixpath.join(d, fid)
                if env.exists(c):
                    out.append(make_entry(key, c, linux_udd(key, "flatpak", fid, env), "flatpak", env))
                    break
        sn = info.get("snap")
        if sn and env.exists("/snap/bin/" + sn):
            out.append(make_entry(key, "/snap/bin/" + sn, linux_udd(key, "snap", None, env), "snap", env))
    return out


def detect_linux(env, problems):
    installed = linux_scan(env)
    cands = []
    rc, out = env.run(["xdg-mime", "query", "default", "x-scheme-handler/https"])
    if rc == 0 and out.strip().endswith(".desktop"):
        cands.append(("xdg-mime", out.strip()))
    rc, out = env.run(["xdg-settings", "get", "default-web-browser"])
    if rc == 0 and out.strip().endswith(".desktop"):
        cands.append(("xdg-settings", out.strip()))
    if not cands:
        rc, out = env.run(["gio", "mime", "x-scheme-handler/https"])
        m = re.search(r"([\w.\-]+\.desktop)", out or "") if rc == 0 else None
        if m:
            cands.append(("gio", m.group(1)))
    if not cands:
        problems.append("Não foi possível ler o navegador padrão (xdg-mime/xdg-settings/gio ausentes ou "
                        "sem resposta).")
        return None, installed, "xdg"
    if len(cands) > 1 and cands[0][1] != cands[1][1]:
        problems.append("xdg-mime (%s) e xdg-settings (%s) divergem; usado xdg-mime. Confirme com o "
                        "usuário." % (cands[0][1], cands[1][1]))
    source, desktop = cands[0]
    desktop_path = None
    for d in linux_desktop_dirs(env):
        c = posixpath.join(d, desktop)
        if env.isfile(c):
            desktop_path = c
            break
    argv = None
    if desktop_path:
        argv = parse_desktop_exec(env.read_text(desktop_path) or "")
    exe, packaging, app_id = linux_exec_info(argv, desktop_path, env) if argv else (None, "native", None)
    if desktop_path and "/flatpak/" in desktop_path:
        packaging = "flatpak"
    key = key_for_desktop(desktop) or (identify_by_path(app_id or exe or desktop))
    if key and not BROWSERS[key].get("chromium"):
        return make_entry(key, exe, None, packaging, env, raw_id=desktop), installed, source
    if key is None:
        problems.append("Arquivo .desktop desconhecido (%s); não deu para classificar o navegador." % desktop)
        return (make_entry(None, exe, None, packaging, env, name=desktop, raw_id=desktop, chromium=False),
                installed, source)
    match = next((e for e in installed if e["id"] == key and e["packaging"] == packaging), None)
    if match:
        default = dict(match, raw_id=desktop)
    else:
        default = make_entry(key, exe, linux_udd(key, packaging, app_id, env), packaging, env, raw_id=desktop)
        if exe and env.exists(exe):
            installed.append(default)
        else:
            problems.append("O navegador padrão (%s) está registrado, mas o executável não foi encontrado."
                            % BROWSERS[key]["name"])
    return default, installed, source


# ---------------------------------------------------------------------------
# Override e montagem do resultado
# ---------------------------------------------------------------------------

def entry_from_path(path, env):
    """Monta a entrada a partir de um caminho dado pelo usuário (variável ou --browser)."""
    path = path.strip().strip('"')
    if env.os_name == "windows":
        path = expand_win_vars(path, env)
    path = os.path.expanduser(path) if path.startswith("~") else path
    if not env.exists(path):
        return None, "O caminho não existe: %s" % path
    exe = path
    key = identify_by_path(path)
    if env.os_name == "macos" and path.rstrip("/").endswith(".app") and env.isdir(path):
        e = mac_app_entry(key, path.rstrip("/"), env)
        if e is None:
            return None, "O .app não tem executável em Contents/MacOS: %s" % path
        return e, None
    if env.isdir(path):
        return None, "O caminho é uma pasta, não um executável: %s" % path
    packaging = "native"
    if env.os_name == "linux":
        if path.startswith("/snap/"):
            packaging = "snap"
        elif "/flatpak/exports/bin/" in path:
            packaging = "flatpak"
    udd = None
    if key and BROWSERS.get(key, {}).get("chromium"):
        if env.os_name == "macos" and BROWSERS[key].get("mac_udd"):
            udd = env.path.join(env.home(), "Library", "Application Support", BROWSERS[key]["mac_udd"])
        elif env.os_name == "windows":
            udd = win_udd(key, env)
        elif env.os_name == "linux":
            app_id = posixpath.basename(path) if packaging == "flatpak" else None
            udd = linux_udd(key, packaging, app_id, env)
    chromium = None
    if key is None:
        chromium = True  # o usuário apontou explicitamente; assumimos Chromium (ver problems)
    return make_entry(key, exe, udd, packaging, env, name=None if key else posixpath.basename(path),
                      chromium=chromium), None


# ---------------------------------------------------------------------------
# Perfis do navegador (somente leitura; sem nomes nem e-mails)
# ---------------------------------------------------------------------------

PROFILE_DIR_RE = re.compile(r"^(Default|Profile \d+|Guest Profile|System Profile)$")


def cookies_paths(profile_dir, env):
    """Caminhos de Cookies que existem no perfil. Chrome/Edge no Windows usam Network/Cookies;
    macOS/Linux (v157 conferido) usam <perfil>/Cookies. Aceita os dois."""
    out = []
    for rel in (("Network", "Cookies"), ("Cookies",)):
        cand = env.path.join(profile_dir, *rel)
        if env.isfile(cand):
            out.append(cand)
    return out


def list_profiles(user_data_dir, env):
    """Lê `Local State` e devolve {"user_data_dir","exists","last_used","last_active","profiles":[...]}.

    Só usa as CHAVES de profile.info_cache e os campos last_used/last_active_profiles; os valores
    de info_cache (nome, e-mail da conta) não são lidos para a saída.
    """
    info = {"user_data_dir": user_data_dir, "exists": False, "last_used": None, "last_active": [],
            "profiles": []}
    if not user_data_dir or not env.isdir(user_data_dir):
        return info
    info["exists"] = True
    raw = env.read_text(env.path.join(user_data_dir, "Local State"))
    keys, last_used, last_active = [], None, []
    if raw:
        try:
            doc = json.loads(raw)
        except ValueError:
            doc = {}
        prof = doc.get("profile") if isinstance(doc, dict) else None
        if isinstance(prof, dict):
            cache = prof.get("info_cache")
            if isinstance(cache, dict):
                keys = [k for k in cache if isinstance(k, str)]
            if isinstance(prof.get("last_used"), str):
                last_used = prof["last_used"]
            la = prof.get("last_active_profiles")
            if isinstance(la, list):
                last_active = [x for x in la if isinstance(x, str)]
    on_disk = [d for d in env.listdir(user_data_dir) if PROFILE_DIR_RE.match(d)
               and env.isdir(env.path.join(user_data_dir, d))]
    names = sorted(set(keys) | set(on_disk), key=lambda n: (n != "Default", n))
    info["last_used"] = last_used
    info["last_active"] = last_active
    preferred = last_active[0] if last_active else last_used
    for n in names:
        pdir = env.path.join(user_data_dir, n)
        info["profiles"].append({
            "dir": n,
            "exists_on_disk": env.isdir(pdir),
            "last_active": n in last_active or n == last_used,
            "cookies": [c[len(user_data_dir):].lstrip("/\\") for c in cookies_paths(pdir, env)],
        })
    info["suggested"] = preferred if preferred in names else ("Default" if "Default" in names else
                                                               (names[0] if names else None))
    return info


def pick_browser(spec, env):
    """Resolve --browser auto|<id>|<caminho>. Devolve (entrada|None, problemas).

    auto = recomendado do detect(); <id> = um id conhecido (brave, chrome, msedge...) instalado;
    <caminho> = executável/.app informado pelo usuário.
    """
    problems = []
    spec = (spec or "auto").strip()
    if spec == "auto":
        _, payload = detect(env, "auto")
        problems += ["detect_browser: " + p for p in payload["problems"]]
        if payload["status"] == "invalid_override":
            return None, problems
        return payload["data"].get("recommended"), problems
    low = spec.lower()
    alias = {"edge": "msedge", "google-chrome": "chrome"}
    low = alias.get(low, low)
    if low in BROWSERS and BROWSERS[low].get("chromium"):
        _, payload = detect(env, "auto")
        for e in payload["data"].get("installed", []):
            if e["id"] == low:
                return e, problems
        problems.append("%s não está instalado (nem foi achado nos caminhos padrão)." % BROWSERS[low]["name"])
        return None, problems
    entry, err = entry_from_path(spec, env)
    if entry is None:
        problems.append("--browser: %s" % err)
    return entry, problems


def pick_recommended(installed):
    cands = [e for e in installed if e.get("chromium") and e.get("executable")]
    cands.sort(key=lambda e: (e["packaging"] != "native",
                              BROWSERS.get(e["id"], {}).get("preference", 99)))
    return cands[0] if cands else None


def detect(env, os_choice="auto", with_profiles=False):
    """Executa a detecção e devolve (exit_code, payload)."""
    problems = []
    next_steps = []
    os_name = env.os_name if os_choice == "auto" else os_choice
    if os_name != env.os_name:
        env.os_name = os_name
        env.path = ntpath if os_name == "windows" else posixpath
        problems.append("--os %s diferente do sistema atual: só faz sentido para testes; os caminhos "
                        "lidos são do sistema real." % os_name)
    data = {"os": os_name, "source": None, "override": None, "default": None,
            "installed": [], "recommended": None}
    if os_name not in ("macos", "windows", "linux"):
        return 1, result(False, "unsupported_os", data,
                         problems + ["Sistema operacional não suportado: %s." % os_name],
                         ["Use macOS, Windows ou Linux."])

    override = env.environ.get(OVERRIDE_ENV)
    if override:
        entry, err = entry_from_path(override, env)
        data["override"] = override
        if entry is None:
            return 2, result(False, "invalid_override", data,
                             problems + ["%s inválido: %s" % (OVERRIDE_ENV, err)],
                             ["Corrija ou remova a variável %s e rode de novo." % OVERRIDE_ENV])

    if os_name == "macos":
        default, installed, source = detect_macos(env, problems)
    elif os_name == "windows":
        default, installed, source = detect_windows(env, problems)
    else:
        default, installed, source = detect_linux(env, problems)
        if not (env.environ.get("DISPLAY") or env.environ.get("WAYLAND_DISPLAY")):
            problems.append("Sem $DISPLAY/$WAYLAND_DISPLAY: o Playwright MCP roda headless e o login "
                            "manual no navegador fica impossível (use xvfb-run ou o modo headless com cópia do perfil).")

    if override:
        if entry["id"] == "unknown":
            problems.append("%s não corresponde a um navegador conhecido; assumido Chromium. Confirme "
                            "com o usuário." % OVERRIDE_ENV)
        data["default"] = entry
        data["source"] = "env:" + OVERRIDE_ENV
        data["detected_default"] = default
    else:
        data["default"] = default
        data["source"] = source
    data["installed"] = installed
    chosen = data["default"]

    for e in installed + ([chosen] if chosen else []):
        if e and e.get("packaging") in ("flatpak", "snap"):
            problems.append("%s instalado via %s: o modo perfil (--user-data-dir) não é suportado nesse "
                            "empacotamento; o modo extensão é [não verificado]. Prefira pacote nativo "
                            "(.deb/.rpm)." % (e["name"], e["packaging"]))
            break

    if chosen and chosen.get("chromium") and chosen.get("executable"):
        data["recommended"] = chosen
        status, ok, code = "chromium_default", True, 0
        next_steps.append("Use %s (%s) no configure_mcp.py com --browser auto." % (chosen["name"],
                                                                                 chosen["executable"]))
    else:
        rec = pick_recommended(installed)
        data["recommended"] = rec
        if rec:
            status, ok, code = "non_chromium_default", True, 0
            nm = chosen["name"] if chosen else "não detectado"
            next_steps.append("O padrão (%s) não serve para o Playwright MCP. Confirme com o usuário o uso "
                              "de %s, que está instalado e tem a sessão logada dele?" % (nm, rec["name"]))
        else:
            status, ok, code = "no_chromium", False, 1
            next_steps.append("Nenhum navegador Chromium instalado. Pergunte ao usuário se pode instalar o "
                              "Google Chrome (macOS: brew install --cask google-chrome; Windows: winget "
                              "install --id Google.Chrome -e; Linux: pacote .deb/.rpm oficial).")
    if with_profiles:
        data["profiles"] = list_profiles((chosen or {}).get("user_data_dir"), env) if chosen else None
    return code, result(ok, status, data, problems, next_steps)


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


def main(argv=None, env=None):
    ap = _Parser(description="Detecta o navegador padrão e os Chromium instalados (somente leitura).")
    ap.add_argument("--os", default="auto", choices=["auto", "macos", "windows", "linux"], help="sistema operacional (padrão: auto)")
    ap.add_argument("--list-profiles", action="store_true",
                    help="inclui data.profiles com os perfis do navegador escolhido (sem nomes nem e-mails)")
    args = ap.parse_args(argv)
    code, payload = detect(env or SystemEnv(), args.os, with_profiles=args.list_profiles)
    emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
