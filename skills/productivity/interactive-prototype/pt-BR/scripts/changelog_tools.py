"""Changelog, badge e merge do prototype.config.json para o modo grupo (módulo, sem CLI; só stdlib).

O changelog vive em `js/components/changelog-modal.js` como literal JS:
  const CHANGELOG = [ { version: '...', date: 'YYYY-MM-DD', changes: ['...'] }, ... ];
Só o literal do array é reescrito; o restante do arquivo é preservado byte a byte.

Ordem das versões (decrescente): `Pendente` no topo; depois `vX.Y.(Z+1)` > `vX.Y.Z-beta.N` > ... >
`vX.Y.Z-beta.1` > `vX.Y.Z`, porque as betas de um ciclo são posteriores à oficial que lhes serve de base.
"""

import copy
import json
import re
from pathlib import Path

import protolib

CHANGELOG_REL = 'js/components/changelog-modal.js'
INDEX_REL = 'index.html'
PENDING = protolib.CHANGELOG_PENDING
DECISIONS = ('approved', 'rejected', 'revoked')

_DECL_RE = re.compile(r'\bconst\s+CHANGELOG\s*=\s*\[')
_BADGE_RE = re.compile(
    r'(<(?P<tag>[A-Za-z][\w-]*)\b[^>]*\bid=["\']prototype-version-badge["\'][^>]*>)(?P<inner>.*?)(</(?P=tag)\s*>)',
    re.S)
BADGE_SUFFIX = ' · protótipo'


class ChangelogError(ValueError):
    pass


class BadgeNotFound(ValueError):
    pass


class ConflictError(Exception):
    """Conflito que não dá para resolver mecanicamente; `keys` lista o que divergiu."""

    def __init__(self, keys, message=None):
        self.keys = list(keys)
        super().__init__(message or f'conflito em: {", ".join(self.keys)}')


# ---------------------------------------------------------------- parser do literal JS

class _Parser:
    def __init__(self, text, pos):
        self.t, self.i = text, pos

    def error(self, msg):
        line = self.t.count('\n', 0, self.i) + 1
        raise ChangelogError(f'{CHANGELOG_REL}: {msg} (linha {line})')

    def ws(self):
        t = self.t
        while self.i < len(t):
            c = t[self.i]
            if c in ' \t\r\n\ufeff':
                self.i += 1
            elif t.startswith('//', self.i):
                j = t.find('\n', self.i)
                self.i = len(t) if j < 0 else j + 1
            elif t.startswith('/*', self.i):
                j = t.find('*/', self.i + 2)
                if j < 0:
                    self.error('comentário não fechado')
                self.i = j + 2
            else:
                return

    def value(self):
        self.ws()
        if self.i >= len(self.t):
            self.error('fim inesperado')
        c = self.t[self.i]
        if c == '[':
            return self.array()
        if c == '{':
            return self.obj()
        if c in '\'"':
            return self.string()
        if self.t.startswith('null', self.i):
            self.i += 4
            return None
        self.error(f'valor não suportado começando em {c!r}')

    def array(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.i < len(self.t) and self.t[self.i] == ']':
                self.i += 1
                return out
            out.append(self.value())
            self.ws()
            if self.i < len(self.t) and self.t[self.i] == ',':
                self.i += 1
            elif self.i < len(self.t) and self.t[self.i] == ']':
                continue
            else:
                self.error('esperado "," ou "]"')

    def obj(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.i < len(self.t) and self.t[self.i] == '}':
                self.i += 1
                return out
            if self.i < len(self.t) and self.t[self.i] in '\'"':
                key = self.string()
            else:
                m = re.compile(r'[A-Za-z_$][\w$]*').match(self.t, self.i)
                if not m:
                    self.error('chave inválida')
                key, self.i = m.group(0), m.end()
            self.ws()
            if self.i >= len(self.t) or self.t[self.i] != ':':
                self.error('esperado ":"')
            self.i += 1
            out[key] = self.value()
            self.ws()
            if self.i < len(self.t) and self.t[self.i] == ',':
                self.i += 1
            elif self.i < len(self.t) and self.t[self.i] == '}':
                continue
            else:
                self.error('esperado "," ou "}"')

    _ESC = {'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'f': '\f', 'v': '\v', '0': '\0'}

    def string(self):
        q = self.t[self.i]
        self.i += 1
        buf = []
        t = self.t
        while True:
            if self.i >= len(t):
                self.error('string não fechada')
            c = t[self.i]
            if c == q:
                self.i += 1
                return ''.join(buf)
            if c == '\n':
                self.error('quebra de linha dentro de string')
            if c == '\\':
                n = t[self.i + 1:self.i + 2]
                if n == 'u':
                    if t[self.i + 2:self.i + 3] == '{':
                        j = t.index('}', self.i + 3)
                        buf.append(chr(int(t[self.i + 3:j], 16)))
                        self.i = j + 1
                    else:
                        buf.append(chr(int(t[self.i + 2:self.i + 6], 16)))
                        self.i += 6
                    continue
                if n == 'x':
                    buf.append(chr(int(t[self.i + 2:self.i + 4], 16)))
                    self.i += 4
                    continue
                if n == '\r' and t[self.i + 2:self.i + 3] == '\n':
                    self.i += 3
                    continue
                if n == '\n':
                    self.i += 2
                    continue
                buf.append(self._ESC.get(n, n))
                self.i += 2
                continue
            buf.append(c)
            self.i += 1


def parse_text(text):
    """Devolve (prefixo, entradas, sufixo); prefixo/sufixo são o texto fora do literal do array."""
    m = _DECL_RE.search(text)
    if not m:
        raise ChangelogError(f'{CHANGELOG_REL}: declaração "const CHANGELOG = [" não encontrada')
    start = m.end() - 1
    p = _Parser(text, start)
    arr = p.array()
    entries = []
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get('version'), str):
            raise ChangelogError(f'{CHANGELOG_REL}: entrada sem "version" de texto')
        changes = e.get('changes', [])
        if not isinstance(changes, list) or not all(isinstance(c, str) for c in changes):
            raise ChangelogError(f'{CHANGELOG_REL}: "changes" de {e["version"]} deve ser lista de textos')
        e['changes'] = list(changes)
        e.setdefault('date', '')
        entries.append(e)
    return text[:start], entries, text[p.i:]


def js_string(s):
    s = (s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
         .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029').replace('</', '<\\/'))
    return "'" + s + "'"


def _js_value(v):
    if v is None:
        return 'null'
    if isinstance(v, list):
        return '[' + ', '.join(_js_value(x) for x in v) + ']'
    return js_string(str(v))


def render_entries(entries):
    lines = ['[']
    for e in entries:
        head = f"  {{ version: {js_string(e['version'])}, date: {js_string(e.get('date') or '')}"
        for k, v in e.items():
            if k not in ('version', 'date', 'changes'):
                key = k if re.fullmatch(r'[A-Za-z_$][\w$]*', k) else js_string(k)
                head += f', {key}: {_js_value(v)}'
        changes = e.get('changes') or []
        if not changes:
            lines.append(head + ', changes: [] },')
            continue
        lines.append(head + ', changes: [')
        lines.extend(f'    {js_string(c)},' for c in changes)
        lines.append('  ] },')
    lines.append(']')
    return '\n'.join(lines)


def render_text(prefix, entries, suffix):
    return prefix + render_entries(entries) + suffix


def _read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def _write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def changelog_path(repo):
    return Path(repo) / CHANGELOG_REL


def read_entries(repo):
    return parse_text(_read(changelog_path(repo)))[1]


def write_entries(repo, entries):
    path = changelog_path(repo)
    prefix, _, suffix = parse_text(_read(path))
    _write(path, render_text(prefix, entries, suffix))


# ---------------------------------------------------------------- versões

def is_pending(entry):
    return entry.get('version') == PENDING


def version_key(version):
    p = protolib.parse_version(version)
    if not p:
        return None
    major, minor, patch, beta = p
    return (major, minor, patch, 0 if beta is None else 1, beta or 0)


def is_beta(entry):
    p = protolib.parse_version(entry.get('version'))
    return bool(p) and p[3] is not None


def is_official(entry):
    p = protolib.parse_version(entry.get('version'))
    return bool(p) and p[3] is None


def last_official(entries):
    """Maior versão oficial `vX.Y.Z` presente (texto) ou None."""
    best = None
    for e in entries:
        if is_official(e) and (best is None or version_key(e['version']) > version_key(best)):
            best = e['version']
    return protolib.format_version(*protolib.parse_version(best)[:3]) if best else None


def _base_tuple(base):
    if isinstance(base, (tuple, list)):
        return tuple(base[:3])
    p = protolib.parse_version(base)
    if not p:
        raise ValueError(f'versão base inválida: {base!r}')
    return p[:3]


def next_beta_number(entries, base):
    base = _base_tuple(base)
    nums = [protolib.parse_version(e['version'])[3] for e in entries
            if is_beta(e) and protolib.parse_version(e['version'])[:3] == base]
    return max(nums, default=0) + 1


def dedupe(lines):
    seen, out = set(), []
    for line in lines:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out


def sort_entries(entries):
    pending = [e for e in entries if is_pending(e)]
    versioned = [e for e in entries if not is_pending(e) and version_key(e['version'])]
    other = [e for e in entries if not is_pending(e) and not version_key(e['version'])]
    versioned.sort(key=lambda e: version_key(e['version']), reverse=True)
    return pending + versioned + other


def normalize_entries(entries):
    """Junta entradas repetidas da mesma versão (linhas sem duplicar) e reordena."""
    by, order = {}, []
    for e in entries:
        v = e['version']
        if v in by:
            by[v]['changes'] = dedupe(by[v]['changes'] + e.get('changes', []))
        else:
            by[v] = copy.deepcopy(e)
            by[v]['changes'] = dedupe(by[v].get('changes', []))
            order.append(v)
    return sort_entries([by[v] for v in order])


def rename_pending(entries, new_version, date, fallback_changes=None):
    """Renomeia a entrada Pendente para `new_version`. Sem Pendente, cria entrada com `fallback_changes`."""
    out = copy.deepcopy(entries)
    for e in out:
        if is_pending(e):
            e['version'], e['date'] = new_version, date
            return normalize_entries(out)
    out.append({'version': new_version, 'date': date,
                'changes': list(fallback_changes or ['Alterações sem descrição no changelog.'])})
    return normalize_entries(out)


def consolidate_betas(entries, new_official, date, changes=None):
    """Troca todas as entradas beta por UMA entrada oficial com as linhas delas (ordem preservada, sem repetir)."""
    betas = [e for e in entries if is_beta(e)]
    lines = dedupe([c for e in betas for c in e.get('changes', [])]) if changes is None else dedupe(changes)
    if not lines:
        lines = ['Promoção sem alterações descritas no changelog.']
    rest = [copy.deepcopy(e) for e in entries if not is_beta(e) and e.get('version') != new_official]
    rest.append({'version': new_official, 'date': date, 'changes': lines})
    return sort_entries(rest)


def _merge_lines(ours, theirs, base):
    if base is None:
        return dedupe(ours + theirs)
    removed = {line for line in base if line not in ours or line not in theirs}
    return [line for line in dedupe(ours + theirs) if line not in removed]


def union_entries(ours, theirs, base=None):
    """União por `version`. Com `base` (merge de 3 vias), versão/linha removida de um dos lados não volta."""
    o = {e['version']: e for e in normalize_entries(ours)}
    t = {e['version']: e for e in normalize_entries(theirs)}
    b = {e['version']: e for e in normalize_entries(base)} if base is not None else None
    out = []
    for v in list(o) + [v for v in t if v not in o]:
        in_o, in_t = v in o, v in t
        # Pendente é trabalho não numerado de alguém: nunca some num merge.
        if b is not None and v in b and not (in_o and in_t) and v != PENDING:
            continue
        if in_o and in_t:
            e = copy.deepcopy(o[v])
            e['changes'] = _merge_lines(o[v]['changes'], t[v]['changes'],
                                        b[v]['changes'] if b is not None and v in b else None)
        else:
            e = copy.deepcopy(o[v] if in_o else t[v])
        out.append(e)
    return sort_entries(out)


def resolve_changelog_text(base_text, ours_text, theirs_text):
    """Merge mecânico do arquivo do changelog; levanta ConflictError se o texto fora do array divergir."""
    try:
        op, oe, osuf = parse_text(ours_text)
        tp, te, tsuf = parse_text(theirs_text)
    except ChangelogError as e:
        raise ConflictError([CHANGELOG_REL], str(e))
    bp = be = bsuf = None
    if base_text is not None:
        try:
            bp, be, bsuf = parse_text(base_text)
        except ChangelogError:
            pass

    def pick(o, t, b, name):
        if o == t:
            return o
        if b is not None and o == b:
            return t
        if b is not None and t == b:
            return o
        raise ConflictError([name], f'texto fora do CHANGELOG divergiu ({name})')

    prefix = pick(op, tp, bp, 'prefix')
    suffix = pick(osuf, tsuf, bsuf, 'suffix')
    return render_text(prefix, union_entries(oe, te, be), suffix)


# ---------------------------------------------------------------- badge

def badge_text(html):
    m = _BADGE_RE.search(html)
    return m.group('inner') if m else None


def set_badge_text(html, version_text):
    if not protolib.parse_version(version_text):
        raise ValueError(f'versão inválida para o badge: {version_text!r}')
    m = _BADGE_RE.search(html)
    if not m:
        raise BadgeNotFound('#prototype-version-badge não encontrado em index.html')
    return html[:m.start('inner')] + f'{version_text}{BADGE_SUFFIX}' + html[m.end('inner'):]


def normalize_badge(html, placeholder='@@PROTOTYPE_BADGE@@'):
    m = _BADGE_RE.search(html)
    if not m:
        return html
    return html[:m.start('inner')] + placeholder + html[m.end('inner'):]


def set_badge(repo, version_text):
    """Troca só o texto interno do badge; devolve True se o arquivo mudou."""
    path = Path(repo) / INDEX_REL
    html = _read(path)
    new = set_badge_text(html, version_text)
    if new != html:
        _write(path, new)
        return True
    return False


# ---------------------------------------------------------------- prototype.config.json

_MISSING = object()


def _pick_member(a, b):
    if a == b:
        return copy.deepcopy(a)
    sa, sb = a.get('status'), b.get('status')
    if sa in DECISIONS and sb == 'pending':
        win = a
    elif sb in DECISIONS and sa == 'pending':
        win = b
    else:
        win = a if (a.get('statusChangedAt') or '') >= (b.get('statusChangedAt') or '') else b
    merged = copy.deepcopy(win)
    hist, seen = [], set()
    for h in (a.get('statusHistory') or []) + (b.get('statusHistory') or []):
        k = json.dumps(h, sort_keys=True)
        if k not in seen:
            seen.add(k)
            hist.append(h)
    if hist:
        merged['statusHistory'] = sorted(hist, key=lambda h: h.get('at') or '')
    return merged


def _artifact_rank(a):
    k = version_key(a.get('version')) if a.get('version') else None
    return (1 if k else 0, k or (), a.get('publishedAt') or '')


def _merge_list(ours, theirs, key_fn, pick):
    o_items = [x for x in (ours or []) if isinstance(x, dict)]
    t_index = {key_fn(x): x for x in (theirs or []) if isinstance(x, dict)}
    out, used = [], set()
    for x in o_items:
        k = key_fn(x)
        used.add(k)
        out.append(pick(x, t_index[k]) if k in t_index else copy.deepcopy(x))
    out.extend(copy.deepcopy(x) for k, x in t_index.items() if k not in used)
    return out


def merge_config(base, ours, theirs):
    """Merge do prototype.config.json; ConflictError(keys) quando a mesma chave mudou diferente nos dois lados.

    Membros nunca são apagados no merge (o roster é trilha de auditoria: sai-se por `revoked`).
    """
    base = base or {}
    out = {}
    conflicts = []
    for k in list(ours) + [k for k in theirs if k not in ours]:
        if k == 'members':
            out[k] = _merge_list(ours.get(k), theirs.get(k),
                                 lambda m: protolib.norm_email(m.get('email')), _pick_member)
            continue
        if k == 'artifacts':
            out[k] = _merge_list(ours.get(k), theirs.get(k), lambda a: a.get('id'),
                                 lambda a, b: copy.deepcopy(a if _artifact_rank(a) >= _artifact_rank(b) else b))
            continue
        o, t, b = ours.get(k, _MISSING), theirs.get(k, _MISSING), base.get(k, _MISSING)
        if o == t:
            val = o
        elif o == b:
            val = t
        elif t == b:
            val = o
        else:
            conflicts.append(k)
            continue
        if val is not _MISSING:
            out[k] = copy.deepcopy(val)
    if conflicts:
        raise ConflictError(conflicts, 'prototype.config.json: alterado de formas diferentes nos dois lados: '
                            + ', '.join(conflicts))
    return out


def resolve_config_text(base_text, ours_text, theirs_text):
    try:
        ours, theirs = json.loads(ours_text), json.loads(theirs_text)
    except json.JSONDecodeError as e:
        raise ConflictError([protolib.CONFIG_NAME], f'{protolib.CONFIG_NAME} inválido num dos lados: {e}')
    try:
        base = json.loads(base_text) if base_text else {}
    except json.JSONDecodeError:
        base = {}
    return json.dumps(merge_config(base, ours, theirs), ensure_ascii=False, indent=2) + '\n'
