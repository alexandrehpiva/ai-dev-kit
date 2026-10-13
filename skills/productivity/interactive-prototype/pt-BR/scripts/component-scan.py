#!/usr/bin/env python3
"""Audita os componentes de um protótipo: cabeçalhos de contrato, duplicação, regras de negócio e catálogo.

Só stdlib. Imprime o envelope JSON de protolib.emit; status CLEAN | ISSUES; exit 0 / 1 / 2.

  python3 component-scan.py [--repo .] [--lint] [--duplicates] [--rules] [--write-catalog]

Sem nenhuma flag roda as três checagens (--lint, --duplicates, --rules) sem escrever nada.
Flags de checagem escolhem só as indicadas. --write-catalog (sozinha ou combinada) regenera
`docs/components.md` a partir dos cabeçalhos; é a única operação que escreve.

Contrato de componente (js/components/**/*.js): o arquivo abre com um bloco-comentário com as tags
@purpose, @props, @state, @a11y (obrigatórias), @slots, @events e @rules (opcionais).
@state começa por `controlled` | `uncontrolled` | `hybrid`, seguido de quem é o dono do estado.

Checagens:
  --lint        cabeçalho ausente, tag obrigatória faltando, @state inválido, tag desconhecida,
                histórico no cabeçalho (datas, "adicionado em…") e catálogo desatualizado.
  --duplicates  (a) funções de js/screens/** com estrutura HTML ≥ 0.8 parecida (≥ 6 linhas de tags);
                (b) blocos HTML de ≥ 3 linhas repetidos em 2+ telas; (c) componentes com nome ou
                estrutura muito parecidos.
  --rules       cruza `docs/business-rules.md` (ids BR-NN em tabela) com referências `@rule BR-NN`
                / `@rules BR-NN` no js/: regra órfã e referência a regra inexistente.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protolib  # noqa: E402

TAGS = ('purpose', 'props', 'slots', 'state', 'events', 'a11y', 'rules')
REQUIRED = ('purpose', 'props', 'state', 'a11y')
STATES = ('controlled', 'uncontrolled', 'hybrid')
SIMILARITY = 0.8
MIN_FUNCTION_LINES = 6
MIN_BLOCK_LINES = 3
CATALOG_MARKER = 'GERADO por component-scan.py'
RULES_FILE = Path('docs') / 'business-rules.md'
CATALOG_FILE = Path('docs') / 'components.md'
RETIRED_STATUSES = ('obsoleta',)

RULE_ID = re.compile(r'\bBR-\d+\b')
HISTORY = re.compile(
    r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(?:adicionad|criad|alterad)[oa] em\b'
    r'|\bantes (?:fazia|era)\b|\bfase \d', re.I)


# ---------------------------------------------------------------- leitura de js

def read(path):
    return Path(path).read_text(encoding='utf-8')


def rel(path, base):
    return Path(path).relative_to(base).as_posix()


def js_files(folder):
    return sorted(p for p in Path(folder).rglob('*.js') if p.is_file()) if Path(folder).is_dir() else []


def strip_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', text)


def _skip_quoted(t, i):
    q, i = t[i], i + 1
    while i < len(t):
        if t[i] == '\\':
            i += 2
        elif t[i] == q or t[i] == '\n':
            return i + 1
        else:
            i += 1
    return i


def _skip_template(t, i):
    i += 1
    while i < len(t):
        c = t[i]
        if c == '\\':
            i += 2
        elif c == '`':
            return i + 1
        elif c == '$' and t[i + 1:i + 2] == '{':
            i = _match(t, i + 1)
            if i < 0:
                return len(t)
        else:
            i += 1
    return i


def _skip_regex(t, i):
    i += 1
    in_class = False
    while i < len(t) and t[i] != '\n':
        c = t[i]
        if c == '\\':
            i += 2
            continue
        if c == '[':
            in_class = True
        elif c == ']':
            in_class = False
        elif c == '/' and not in_class:
            return i + 1
        i += 1
    return i


def _match(t, i):
    """t[i] abre ( [ ou {; devolve o índice logo após o fechamento correspondente, ou -1."""
    open_ch = t[i]
    close_ch = {'(': ')', '[': ']', '{': '}'}[open_ch]
    depth, prev = 0, ''
    while i < len(t):
        c = t[i]
        if c in '\'"':
            i, prev = _skip_quoted(t, i), 'x'
            continue
        if c == '`':
            i, prev = _skip_template(t, i), 'x'
            continue
        if c == '/' and t[i + 1:i + 2] == '/':
            j = t.find('\n', i)
            i = len(t) if j < 0 else j
            continue
        if c == '/' and t[i + 1:i + 2] == '*':
            j = t.find('*/', i + 2)
            i = len(t) if j < 0 else j + 2
            continue
        if c == '/' and (prev == '' or prev in '(,=:[!&|?{};'):
            i, prev = _skip_regex(t, i), 'x'
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        if not c.isspace():
            prev = c
        i += 1
    return -1


FUNC_START = re.compile(r'(?m)^(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(')
ARROW_START = re.compile(
    r'(?m)^(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)\n]*\)|[A-Za-z_$][\w$]*)\s*=>\s*')


def find_functions(text):
    """Funções de nível superior: [{name, body}]. Corpo = texto entre as chaves (inclusive)."""
    found = []
    for m in FUNC_START.finditer(text):
        end_params = _match(text, m.end() - 1)
        if end_params < 0:
            continue
        brace = text.find('{', end_params)
        if brace < 0 or text[end_params:brace].strip():
            continue
        end = _match(text, brace)
        if end > 0:
            found.append({'name': m.group(1), 'body': text[brace:end]})
    for m in ARROW_START.finditer(text):
        if text[m.end():m.end() + 1] == '{':
            end = _match(text, m.end())
            body = text[m.end():end] if end > 0 else ''
        else:
            end = text.find(';\n', m.end())
            body = text[m.end():end if end > 0 else len(text)]
        found.append({'name': m.group(1), 'body': body})
    return found


# ---------------------------------------------------------------- cabeçalhos

def parse_header(text):
    """Devolve {'tags': {nome: valor}, 'unknown': [...], 'block': str} ou None se não abre com /* */."""
    t = text.lstrip('﻿ \t\r\n')
    if not t.startswith('/*'):
        return None
    end = t.find('*/')
    if end < 0:
        return None
    tags, unknown, current = {}, [], None
    for raw in t[2:end].splitlines():
        line = raw.strip().lstrip('*').strip()
        m = re.match(r'^@([A-Za-z][A-Za-z0-9]*)\b\s*(.*)$', line)
        if m:
            current = m.group(1).lower()
            if current not in TAGS:
                unknown.append(current)
            tags[current] = m.group(2).strip()
        elif current and line:
            tags[current] = (tags[current] + ' ' + line).strip()
    return {'tags': tags, 'unknown': unknown, 'block': t[:end + 2]}


def component_name(path, comp_dir):
    return Path(rel(path, comp_dir)).with_suffix('').as_posix()


def load_components(repo):
    comp_dir = repo / 'js' / 'components'
    out = []
    for path in js_files(comp_dir):
        text = read(path)
        header = parse_header(text)
        funcs = find_functions(strip_comments(text))
        out.append({
            'name': component_name(path, comp_dir), 'path': path, 'file': rel(path, repo),
            'text': text, 'header': header,
            'tags': header['tags'] if header else {},
            'functions': [f['name'] for f in funcs if not f['name'].startswith('_')],
        })
    return out


def lint_components(components):
    problems = []

    def add(code, comp, msg):
        p = protolib.problem(code, f'{comp["file"]}: {msg}')
        p['file'] = comp['file']
        problems.append(p)

    for c in components:
        h = c['header']
        if not h or not h['tags']:
            add('header-missing', c, 'o arquivo não abre com o bloco-comentário de contrato '
                '(@purpose, @props, @state, @a11y; opcionais @slots, @events, @rules).')
            continue
        for tag in REQUIRED:
            if not h['tags'].get(tag):
                add('header-tag-missing', c, f'falta a tag obrigatória @{tag} no cabeçalho.')
        for tag in h['unknown']:
            add('header-unknown-tag', c, f'tag @{tag} não faz parte do contrato (use {", ".join("@" + t for t in TAGS)}).')
        state = h['tags'].get('state')
        if state:
            m = re.match(r'^(\w+)(.*)$', state)
            if not m or m.group(1) not in STATES:
                add('header-state-invalid', c, f'@state deve começar por {" | ".join(STATES)}; encontrado "{state[:40]}".')
            elif not re.sub(r'^[\s:—–\-,.;()]+', '', m.group(2)):
                add('header-state-owner-missing', c, '@state precisa dizer quem é o dono do estado '
                    '(ex.: "controlled — dono: state.js").')
        rules = h['tags'].get('rules')
        if rules and [w for w in re.split(r'[\s,;]+', rules) if w and not re.fullmatch(r'BR-\d+', w)]:
            add('header-rules-invalid', c, '@rules aceita só ids no formato BR-NN separados por vírgula.')
        if HISTORY.search(h['block']):
            add('header-history', c, 'o cabeçalho descreve contrato, não histórico: remova datas e '
                'narrativas ("adicionado em…", "antes fazia…").')
    return problems


# ---------------------------------------------------------------- duplicação

TAG_RE = re.compile(r'<(/?)([A-Za-z][\w-]*)([^<>]*)>')


def structure_lines(text):
    """Uma linha normalizada por linha-fonte que contém tags: tags + classes, sem texto nem atributos."""
    out = []
    for line in text.splitlines():
        toks = []
        for m in TAG_RE.finditer(line):
            closing, tag, attrs = m.groups()
            if closing:
                toks.append('/' + tag.lower())
                continue
            cm = re.search(r'class="([^"]*)"', attrs)
            cls = ''
            if cm:
                words = sorted(re.sub(r'\$\{[^}]*\}', '*', cm.group(1)).split())
                cls = '.' + '.'.join(words) if words else ''
            toks.append(tag.lower() + cls)
        if toks:
            out.append('|'.join(toks))
    return out


def duplicate_functions(repo):
    funcs = []
    for path in js_files(repo / 'js' / 'screens'):
        for f in find_functions(strip_comments(read(path))):
            seq = structure_lines(f['body'])
            if len(seq) >= MIN_FUNCTION_LINES:
                funcs.append((rel(path, repo), f['name'], seq))
    problems = []
    for i in range(len(funcs)):
        for j in range(i + 1, len(funcs)):
            a, b = funcs[i], funcs[j]
            ratio = difflib.SequenceMatcher(None, a[2], b[2], autojunk=False).ratio()
            if ratio >= SIMILARITY:
                p = protolib.problem(
                    'duplicate-function',
                    f'{a[1]}() em {a[0]} e {b[1]}() em {b[0]} têm a mesma estrutura HTML '
                    f'({round(ratio * 100)}% parecida): extraia um componente em js/components/.')
                p['files'] = [a[0], b[0]]
                problems.append(p)
    return problems


CLOSING_ONLY = re.compile(r'^(?:</[\w-]+>\s*|`;?|\);?|\}\s*)+$')


def html_lines(path):
    out = []
    for n, line in enumerate(read(path).splitlines(), 1):
        norm = ' '.join(line.split())
        if '<' in norm:
            out.append((n, norm))
    return out


def duplicate_blocks(repo):
    files = [(rel(p, repo), html_lines(p)) for p in js_files(repo / 'js' / 'screens')]
    problems = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            (fa, la), (fb, lb) = files[i], files[j]
            sm = difflib.SequenceMatcher(None, [x[1] for x in la], [x[1] for x in lb], autojunk=False)
            for blk in sm.get_matching_blocks():
                if blk.size < MIN_BLOCK_LINES:
                    continue
                lines = [la[blk.a + k][1] for k in range(blk.size)]
                if sum(1 for ln in lines if not CLOSING_ONLY.match(ln)) < 2:
                    continue
                a0, a1 = la[blk.a][0], la[blk.a + blk.size - 1][0]
                b0, b1 = lb[blk.b][0], lb[blk.b + blk.size - 1][0]
                p = protolib.problem(
                    'duplicate-block',
                    f'bloco HTML de {blk.size} linhas repetido em {fa} (linhas {a0}-{a1}) e {fb} '
                    f'(linhas {b0}-{b1}): extraia para um componente.')
                p['files'] = [fa, fb]
                problems.append(p)
    return problems


def similar_components(components):
    problems = []
    prepared = []
    for c in components:
        body = c['text'].replace(c['header']['block'], '', 1) if c['header'] else c['text']
        prepared.append((c, structure_lines(strip_comments(body))))
    for i in range(len(prepared)):
        for j in range(i + 1, len(prepared)):
            (a, sa), (b, sb) = prepared[i], prepared[j]
            name_ratio = difflib.SequenceMatcher(None, a['name'], b['name']).ratio()
            if name_ratio >= SIMILARITY:
                p = protolib.problem(
                    'similar-component-name',
                    f'componentes "{a["name"]}" e "{b["name"]}" têm nomes quase iguais: '
                    'reuse o existente ou diferencie o propósito.')
                p['files'] = [a['file'], b['file']]
                problems.append(p)
            for fa in a['functions']:
                for fb in b['functions']:
                    if difflib.SequenceMatcher(None, fa.lower(), fb.lower()).ratio() >= SIMILARITY:
                        p = protolib.problem(
                            'similar-component-function',
                            f'{fa}() em {a["file"]} e {fb}() em {b["file"]} têm nomes quase iguais: '
                            'provável duplicação de componente.')
                        p['files'] = [a['file'], b['file']]
                        problems.append(p)
            if len(sa) >= MIN_FUNCTION_LINES and len(sb) >= MIN_FUNCTION_LINES:
                ratio = difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio()
                if ratio >= SIMILARITY:
                    p = protolib.problem(
                        'similar-component-structure',
                        f'{a["file"]} e {b["file"]} geram HTML com estrutura {round(ratio * 100)}% '
                        'parecida: considere unificar num só componente.')
                    p['files'] = [a['file'], b['file']]
                    problems.append(p)
    return problems


# ---------------------------------------------------------------- regras de negócio

def load_rules(repo):
    """{id: status} lido das linhas de tabela de docs/business-rules.md; comentários HTML ignorados."""
    path = repo / RULES_FILE
    if not path.is_file():
        return None, []
    text = re.sub(r'<!--.*?-->', '', read(path), flags=re.S)
    rules, duplicates = {}, []
    for line in text.splitlines():
        if not line.lstrip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rid = cells[0].strip('`* ')
        if re.fullmatch(r'BR-\d+', rid):
            if rid in rules:
                duplicates.append(rid)
            rules[rid] = cells[-1].strip('`* ').lower() if len(cells) > 1 else ''
    return rules, duplicates


def rule_references(repo, components):
    """{id: [arquivos]} a partir de `@rule(s) BR-NN` no js/ e das tags @rules dos cabeçalhos."""
    refs = {}

    def add(rid, f):
        refs.setdefault(rid, [])
        if f not in refs[rid]:
            refs[rid].append(f)

    for path in js_files(repo / 'js'):
        for m in re.finditer(r'@rules?\b([^\n]*)', read(path)):
            for rid in RULE_ID.findall(m.group(1)):
                add(rid, rel(path, repo))
    for c in components:
        for rid in RULE_ID.findall(c['tags'].get('rules', '')):
            add(rid, c['file'])
    return refs


def check_rules(repo, components):
    rules, duplicates = load_rules(repo)
    refs = rule_references(repo, components)
    problems = []
    for rid in duplicates:
        problems.append(protolib.problem('rule-duplicate', f'{RULES_FILE.as_posix()}: o id {rid} aparece em mais de uma linha.'))
    for rid in sorted(refs, key=lambda r: int(r[3:])):
        if rules is None or rid not in rules:
            where = ', '.join(refs[rid])
            problems.append(protolib.problem('rule-unknown', f'{rid} é citada em {where}, mas não existe em {RULES_FILE.as_posix()}.'))
    for rid, status in sorted((rules or {}).items(), key=lambda kv: int(kv[0][3:])):
        if rid not in refs and status not in RETIRED_STATUSES:
            problems.append(protolib.problem(
                'rule-orphan', f'{rid} está em {RULES_FILE.as_posix()} mas nenhum código a cita '
                '(@rule ' + rid + '): aplique a regra na tela, cite-a ou marque como obsoleta.'))
    return problems, {'defined': len(rules or {}), 'referenced': len(refs)}


# ---------------------------------------------------------------- catálogo

def usage_map(repo, components):
    """componente → arquivos (js/screens, js/components, js/*.js e index.html) que chamam suas funções."""
    sources = []
    for path in js_files(repo / 'js'):
        sources.append((path, rel(path, repo / 'js')[:-3], strip_comments(read(path))))
    index = repo / 'index.html'
    if index.is_file():
        sources.append((index, 'index.html', read(index)))
    used = {}
    for c in components:
        users = set()
        for path, label, text in sources:
            if path == c['path']:
                continue
            if any(re.search(rf'(?<![\w$.]){re.escape(fn)}\s*\(', text) for fn in c['functions']):
                users.add(label)
        used[c['name']] = sorted(users)
    return used


def _cell(text, limit):
    text = ' '.join((text or '').split()).replace('|', '\\|')
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def build_catalog(repo, components):
    used = usage_map(repo, components)
    lines = [
        f'<!-- {CATALOG_MARKER} --write-catalog. NÃO EDITE À MÃO: altere o cabeçalho do componente e gere de novo. -->',
        '# Catálogo de componentes', '',
        'Contrato completo de cada componente: bloco-comentário no topo do arquivo em `js/components/`.', '',
    ]
    if not components:
        lines.append('_Nenhum componente em `js/components/`._')
    else:
        lines += ['| Componente | Arquivo | Propósito | Estado | Props | Usado por |', '|---|---|---|---|---|---|']
        for c in sorted(components, key=lambda c: c['name']):
            t = c['tags']
            users = ', '.join(f'`{u}`' for u in used[c['name']]) or '—'
            if not c['header'] or not t:
                purpose, state, props = '⚠ sem cabeçalho de contrato', '—', '—'
            else:
                purpose, state, props = _cell(t.get('purpose'), 140), _cell(t.get('state'), 90), _cell(t.get('props'), 110)
            lines.append(f'| `{c["name"]}` | `{c["file"]}` | {purpose} | {state} | {props} | {users} |')
    return '\n'.join(lines) + '\n'


def catalog_problems(repo, components):
    path = repo / CATALOG_FILE
    if not path.is_file():
        return []
    current = read(path)
    if CATALOG_MARKER not in current or current == build_catalog(repo, components):
        return []
    return [protolib.problem('catalog-stale', f'{CATALOG_FILE.as_posix()} está desatualizado em relação '
                             'aos cabeçalhos/usos: rode component-scan.py --write-catalog.')]


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.', help='Raiz do protótipo (default: .)')
    ap.add_argument('--lint', action='store_true', help='Valida os cabeçalhos de contrato dos componentes')
    ap.add_argument('--duplicates', action='store_true', help='Aponta duplicação de telas e componentes')
    ap.add_argument('--rules', action='store_true', help='Cruza regras de negócio com referências no código')
    ap.add_argument('--write-catalog', action='store_true', help='Gera docs/components.md')
    args = ap.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not (repo / 'js').is_dir():
        protolib.emit(False, 'USAGE', problems=[protolib.problem(
            'not-a-prototype', f'{repo} não tem a pasta js/: informe a raiz do protótipo em --repo.')])
        return 2

    chosen = [n for n in ('lint', 'duplicates', 'rules') if getattr(args, n)]
    if not chosen and not args.write_catalog:
        chosen = ['lint', 'duplicates', 'rules']

    components = load_components(repo)
    problems, data = [], {
        'repo': str(repo), 'checks': chosen,
        'components': [{'name': c['name'], 'file': c['file'], 'hasHeader': bool(c['header'] and c['header']['tags']),
                        'state': (c['tags'].get('state') or '').split(' ')[0] or None} for c in components],
    }
    if 'lint' in chosen:
        problems += lint_components(components) + catalog_problems(repo, components)
    if 'duplicates' in chosen:
        problems += duplicate_functions(repo) + duplicate_blocks(repo) + similar_components(components)
    if 'rules' in chosen:
        found, data['rules'] = check_rules(repo, components)
        problems += found
    if args.write_catalog:
        target = repo / CATALOG_FILE
        content = build_catalog(repo, components)
        changed = not target.is_file() or read(target) != content
        if changed:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        data['catalog'] = {'path': CATALOG_FILE.as_posix(), 'written': changed}

    return protolib.emit(not problems, 'ISSUES' if problems else 'CLEAN', data=data, problems=problems)


if __name__ == '__main__':
    sys.exit(main())
