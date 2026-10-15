#!/usr/bin/env python3
"""Biblioteca comum dos scripts do interactive-explainer (só stdlib).

Contém: carregamento dos dados, validação do contrato (EXPLAINER-DATA-FORMAT.md), geração do HTML e
o envelope JSON usado por todos os scripts da skill:

    {"ok": bool, "status": str, "data": {...}, "problems": [...], "questions": [...]}

Convenção de saída: exit 0 = ok, 1 = problemas (dados inválidos, falha de render), 2 = uso incorreto.
"""

import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_ROOT / 'templates' / 'explainer-template.html'
DATA_PLACEHOLDER = '/*__EXPLAINER_DATA__*/'
TITLE_PLACEHOLDER = '{{TITLE}}'

ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')
NODE_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')
HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')
CHIP_RE = re.compile(r'@([A-Za-z][\w-]*):([\w.\-/]+)')
DANGEROUS_RE = re.compile(r'<\s*script|javascript:|\son\w+\s*=', re.I)

STATUS_VALUES = {'confirmado', 'hipotese'}
SOURCE_EXTS = ('md', 'py', 'js', 'ts', 'tsx', 'jsx', 'json', 'yml', 'yaml', 'html', 'css', 'txt', 'sql', 'sh', 'go', 'rs', 'java',
               'kt', 'swift', 'toml', 'ini', 'cfg', 'xml', 'csv', 'prisma', 'graphql', 'proto', 'tf', 'pdf', 'rb', 'php', 'cs', 'c', 'h', 'cpp')
FILE_TOKEN_RE = re.compile(r'(?<![\w./-])((?:\.{1,2}/)*[\w][\w./-]*\.(?:' + '|'.join(SOURCE_EXTS) + r'))(?![\w])')
PLACEHOLDER_SOURCE_RE = re.compile(r'^\s*(n/?a|a definir|tbd|todo|fonte|source|sem fonte|\?+|-+|\.+|…)\s*$', re.I)
MAX_SOURCE_FILE = 5_000_000

BLOCK_TYPES = {'text', 'rail', 'matrix', 'cards', 'phrase', 'roles', 'board', 'sample', 'embed', 'html'}
SNIPPETS_DIR = SKILL_ROOT / 'snippets'
CLAIM_ITEMS = {'rail': 'steps', 'cards': 'items', 'roles': 'roles'}  # blocos cujos itens afirmam fatos
SAMPLE_KINDS = {'code', 'note', 'table', 'list', 'gate', 'html'}
# Nenhum tipo de peça vem pronto: o autor declara os seus em pieceTypes (sem isso, o nó usa um estilo neutro).
ICON_NAMES = {
    'person', 'bot', 'book', 'check', 'code', 'file', 'lock', 'db', 'cloud', 'mail', 'clock', 'bolt',
    'flag', 'search', 'shield', 'branch', 'cube', 'gear', 'queue', 'state',
}

# Orçamentos de texto (aviso, não erro): acima disso a caixa quebra em muitas linhas ou o rótulo colide.
BUDGET = {'node_title': 32, 'node_sub': 48, 'edge_label': 16, 'tab_label': 24, 'step_title': 28,
          'stage_title': 30, 'body': 400, 'code_lines': 28, 'max_cols': 8, 'max_rows': 5}


def envelope(ok, status, data=None, problems=None, questions=None):
    return {'ok': ok, 'status': status, 'data': data or {}, 'problems': problems or [], 'questions': questions or []}


def emit(env, exit_code=None):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(exit_code if exit_code is not None else (0 if env['ok'] else 1))


def load_data(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f'arquivo de dados não encontrado: {p}')
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as err:
        raise ValueError(f'JSON inválido em {p}: linha {err.lineno}, coluna {err.colno}: {err.msg}') from err


class Problems:
    def __init__(self):
        self.items = []

    def add(self, level, where, msg):
        self.items.append({'level': level, 'where': where, 'msg': msg})

    def error(self, where, msg):
        self.add('error', where, msg)

    def warn(self, where, msg):
        self.add('warn', where, msg)

    def info(self, where, msg):
        self.add('info', where, msg)

    @property
    def errors(self):
        return [p for p in self.items if p['level'] == 'error']


def _strings(obj, path=''):
    """Percorre o JSON devolvendo (caminho, texto) de todo valor string."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f'{path}.{k}' if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f'{path}[{i}]')


def piece_types(data):
    types = {}
    for tid, spec in (data.get('pieceTypes') or {}).items():
        types[tid] = bool(spec.get('guard', False)) if isinstance(spec, dict) else False
    return types


def validate(data, require_source=False, source_root=None, require_quote=False, base_dir=None):
    """Valida o dicionário de dados. Devolve a lista de problemas (error/warn/info).

    require_source: todo nó e toda aresta de um quadro precisa de `source` (exceto os marcados status=hipotese).
    source_root: pasta onde os arquivos citados em `source` devem existir; `quote` precisa aparecer num deles.
    require_quote: todo nó e toda aresta confirmados precisam de `quote` (exige source_root).
    base_dir: pasta do arquivo de dados, para conferir blocos embed com `file`.
    """
    pr = Problems()
    verifier = SourceVerifier(source_root, require_quote) if (source_root or require_quote) else None
    if not isinstance(data, dict):
        pr.error('raiz', 'o JSON precisa ser um objeto')
        return pr.items

    meta = data.get('meta')
    if not isinstance(meta, dict) or not str(meta.get('title', '')).strip():
        pr.error('meta.title', 'título obrigatório (vai para <title> e para o cabeçalho)')

    for path, text in _strings(data):
        if path.endswith('srcdoc'):
            continue  # HTML de embed: roda num iframe isolado (sandbox sem acesso à página)
        if DANGEROUS_RE.search(text):
            pr.error(path, 'marcação perigosa (<script>, javascript: ou atributo on*=): os textos aceitam só HTML inline simples')

    types = piece_types(data)
    for tid, spec in (data.get('pieceTypes') or {}).items():
        where = f'pieceTypes.{tid}'
        if not isinstance(spec, dict):
            pr.error(where, 'precisa ser um objeto')
            continue
        for key in ('color', 'colorLight'):
            if key in spec and not HEX_RE.match(str(spec[key])):
                pr.error(f'{where}.{key}', f'cor precisa ser hexadecimal #RRGGBB (veio {spec[key]!r})')
        icon = spec.get('icon')
        if icon and icon not in ICON_NAMES and 'iconSvg' not in spec:
            pr.warn(f'{where}.icon', f'ícone {icon!r} não existe no motor; use um de {sorted(ICON_NAMES)} ou forneça iconSvg')

    catalog = data.get('catalog') or {}
    cat_ids = {(t, it.get('id')) for t, items in catalog.items() if isinstance(items, list) for it in items if isinstance(it, dict)}
    for t in catalog:
        if t not in types:
            pr.warn(f'catalog.{t}', f'tipo de peça sem declaração em pieceTypes: {t} (a ficha funciona, mas sem cor nem ícone)')

    tabs = data.get('tabs')
    if not isinstance(tabs, list) or not tabs:
        pr.error('tabs', 'pelo menos uma aba é obrigatória')
        return pr.items

    tab_ids, block_ids, blocks_by_id = [], {}, {}
    for ti, tab in enumerate(tabs):
        where = f'tabs[{ti}]'
        tid = tab.get('id', '')
        if not ID_RE.match(str(tid)):
            pr.error(f'{where}.id', f'id da aba precisa casar {ID_RE.pattern} (vira parte da URL): {tid!r}')
        if tid in tab_ids:
            pr.error(f'{where}.id', f'id de aba repetido: {tid}')
        tab_ids.append(tid)
        if not str(tab.get('label', '')).strip():
            pr.error(f'{where}.label', 'rótulo da aba obrigatório')
        elif len(tab['label']) > BUDGET['tab_label']:
            pr.warn(f'{where}.label', f'rótulo longo ({len(tab["label"])} > {BUDGET["tab_label"]}): quebra a barra de abas no celular')
        if not isinstance(tab.get('blocks'), list) or not tab.get('blocks'):
            pr.error(f'{where}.blocks', 'a aba precisa de pelo menos um bloco')
            continue
        for bi, blk in enumerate(tab['blocks']):
            bw = f'{where}.blocks[{bi}]'
            if blk.get('type') not in BLOCK_TYPES:
                pr.error(f'{bw}.type', f'tipo de bloco desconhecido: {blk.get("type")!r} (válidos: {sorted(BLOCK_TYPES)})')
                continue
            bid = blk.get('id')
            if bid is not None:
                if not ID_RE.match(str(bid)):
                    pr.error(f'{bw}.id', f'id de bloco precisa casar {ID_RE.pattern}: {bid!r}')
                if bid in block_ids:
                    pr.error(f'{bw}.id', f'id de bloco repetido: {bid}')
                block_ids[bid] = (ti, tid)
                blocks_by_id[bid] = blk

    # Referências de link (rail.go) só podem ser conferidas depois de conhecer todos os ids.
    for ti, tab in enumerate(tabs):
        for bi, blk in enumerate(tab.get('blocks') or []):
            bw = f'tabs[{ti}].blocks[{bi}]'
            t = blk.get('type')
            if t == 'rail':
                _check_rail(blk, bw, tab_ids, block_ids, pr)
            elif t == 'matrix':
                _check_matrix(blk, bw, pr)
            elif t == 'cards':
                if not isinstance(blk.get('items'), list) or not blk['items']:
                    pr.error(f'{bw}.items', 'cards precisa de uma lista não vazia')
                if blk.get('cols', 4) not in (1, 2, 3, 4, 6, 12):
                    pr.warn(f'{bw}.cols', 'cols ideal: 1, 2, 3, 4, 6 ou 12 (divide a grade de 12 colunas)')
                for ii, it in enumerate(blk.get('items') or []):
                    if len(str(it.get('body', ''))) > BUDGET['body']:
                        pr.warn(f'{bw}.items[{ii}].body', 'texto longo para um cartão (> 400 caracteres)')
            elif t == 'roles':
                _check_roles(blk, bw, pr)
            elif t == 'sample':
                _check_sample_block(blk, bw, pr)
            elif t == 'embed':
                _check_embed(blk, bw, pr, base_dir)
            elif t == 'board':
                _check_board(blk, bw, types, cat_ids, pr, require_source, verifier)
            elif t == 'phrase':
                if not str(blk.get('text', '')).strip():
                    pr.error(f'{bw}.text', 'frase vazia')
            _check_block_sources(blk, bw, pr, require_source, verifier)

    for path, text in _strings(data):
        for m in CHIP_RE.finditer(text):
            tp, ident = m.group(1), m.group(2)
            if (tp in types or tp in catalog) and (tp, ident) not in cat_ids:
                pr.error(path, f'chip @{tp}:{ident} não existe em catalog.{tp}')
    return pr.items


def _check_rail(blk, bw, tab_ids, block_ids, pr):
    steps = blk.get('steps')
    if not isinstance(steps, list) or not steps:
        pr.error(f'{bw}.steps', 'rail precisa de passos')
        return
    ns = [str(s.get('n') if s.get('n') is not None else i + 1) for i, s in enumerate(steps)]
    if len(set(ns)) != len(ns):
        pr.error(f'{bw}.steps', 'números de passo (n) repetidos')
    for si, s in enumerate(steps):
        w = f'{bw}.steps[{si}]'
        if len(str(s.get('title', ''))) > BUDGET['step_title']:
            pr.warn(f'{w}.title', f'título longo ({len(s["title"])} > {BUDGET["step_title"]})')
        go = s.get('go')
        if go:
            tab, _, block = str(go).partition('/')
            if tab not in tab_ids:
                pr.error(f'{w}.go', f'link aponta para aba inexistente: {go}')
            elif block and block not in block_ids:
                pr.error(f'{w}.go', f'link aponta para bloco inexistente: {go}')
    loop = blk.get('loop')
    if loop:
        for k in loop.get('from', []):
            if str(k) not in ns:
                pr.error(f'{bw}.loop.from', f'passo {k} não existe')
        if str(loop.get('to')) not in ns:
            pr.error(f'{bw}.loop.to', f'passo {loop.get("to")} não existe')


def _check_matrix(blk, bw, pr):
    cols = blk.get('columns')
    if not isinstance(cols, list) or not cols:
        pr.error(f'{bw}.columns', 'matrix precisa de colunas')
        return
    for ri, row in enumerate(blk.get('rows') or []):
        cells = row.get('cells') or []
        if len(cells) > len(cols):
            pr.error(f'{bw}.rows[{ri}].cells', f'{len(cells)} células para {len(cols)} colunas (células a menos ficam vazias; a mais não têm onde aparecer)')
        for ci, c in enumerate(cells):
            if isinstance(c, dict) and 'tip' in c and not (isinstance(c['tip'], dict) and c['tip'].get('title')):
                pr.error(f'{bw}.rows[{ri}].cells[{ci}].tip', 'tip precisa de title (e items)')


def _check_sample(s, sw, pr):
    kind = s.get('kind') if isinstance(s, dict) else None
    if kind not in SAMPLE_KINDS:
        pr.error(f'{sw}.kind', f'tipo de amostra desconhecido: {kind!r} (válidos: {sorted(SAMPLE_KINDS)})')
    elif kind == 'gate':
        items = s.get('items') or []
        if not items:
            pr.error(f'{sw}.items', 'gate sem itens')
        miss = s.get('miss')
        if miss is not None and not (isinstance(miss, int) and 0 <= miss < len(items)):
            pr.error(f'{sw}.miss', f'miss fora da faixa 0..{len(items) - 1}')
    elif kind == 'table':
        ncols = len(s.get('columns') or [])
        for rj, row in enumerate(s.get('rows') or []):
            if len(row) != ncols:
                pr.error(f'{sw}.rows[{rj}]', f'{len(row)} células para {ncols} colunas')
    elif kind == 'code':
        lines = str(s.get('code', '')).count('\n') + 1
        if lines > BUDGET['code_lines']:
            pr.warn(f'{sw}.code', f'amostra de código com {lines} linhas (> {BUDGET["code_lines"]}): corte o que não carrega a ideia')


def _check_roles(blk, bw, pr):
    roles = blk.get('roles')
    if not isinstance(roles, list) or not roles:
        pr.error(f'{bw}.roles', 'roles precisa de pelo menos um item')
        return
    if len(roles) > 6:
        pr.warn(f'{bw}.roles', f'{len(roles)} cartões: acima de 6 a linha fica apertada')
    for ri, r in enumerate(roles):
        w = f'{bw}.roles[{ri}]'
        if not str(r.get('name', '')).strip():
            pr.error(f'{w}.name', 'obrigatório (é o rótulo do cartão)')
        samples = r.get('samples') or ([r['sample']] if r.get('sample') else [])
        for si, smp in enumerate(samples):
            _check_sample(smp, f'{w}.samples[{si}]', pr)


def _check_sample_block(blk, bw, pr):
    samples = blk.get('samples') or ([blk['sample']] if blk.get('sample') else [])
    if not samples:
        pr.error(f'{bw}.samples', 'sample precisa de "sample" ou "samples"')
    for si, smp in enumerate(samples):
        _check_sample(smp, f'{bw}.samples[{si}]', pr)


def _check_embed(blk, bw, pr, base_dir):
    if blk.get('srcdoc'):
        return
    snippet, file = blk.get('snippet'), blk.get('file')
    if not snippet and not file:
        pr.error(bw, 'embed precisa de "snippet" (nome em snippets/), "file" (HTML seu) ou "srcdoc"')
        return
    if snippet and not (SNIPPETS_DIR / f'{snippet}.html').is_file():
        pr.error(f'{bw}.snippet', f'snippet inexistente: {snippet!r} (disponíveis: {sorted(p.stem for p in SNIPPETS_DIR.glob("*.html"))})')
    if file and base_dir is not None and not (Path(base_dir) / file).is_file():
        pr.error(f'{bw}.file', f'arquivo não encontrado: {file}')
    h = blk.get('height')
    if h is not None and not (isinstance(h, int) and 200 <= h <= 2400):
        pr.warn(f'{bw}.height', 'altura do iframe entre 200 e 2400 px')


def _check_block_sources(blk, bw, pr, require_source, verifier):
    """Fonte, trecho e hipótese em blocos e itens. Com --require-source, um bloco que afirma fatos precisa de
    source/status no bloco (cobre os itens) ou em cada item; nunca é preciso inventar conteúdo para passar."""
    t = blk.get('type')
    if t not in ('rail', 'matrix', 'cards', 'roles', 'sample'):
        return
    _check_claim(blk, bw, 'bloco', pr, require_source, verifier, needs=False)
    covered = bool(blk.get('source')) or blk.get('status') == 'hipotese'
    key = CLAIM_ITEMS.get(t)
    if key:
        for ii, it in enumerate(blk.get(key) or []):
            if isinstance(it, dict):
                _check_claim(it, f'{bw}.{key}[{ii}]', 'item', pr, require_source, verifier, needs=require_source and not covered)
    elif require_source and not covered:
        pr.error(f'{bw}.source', f'bloco {t} sem "source" (ou status "hipotese")')


def _check_board(blk, bw, types, cat_ids, pr, require_source, verifier=None):
    _check_claim(blk, bw, 'bloco', pr, require_source, verifier, needs=False)
    stages = blk.get('stages')
    if not isinstance(stages, list) or not stages:
        pr.error(f'{bw}.stages', 'board precisa de pelo menos uma etapa')
        return
    start = blk.get('start', 0)
    if not (isinstance(start, int) and 0 <= start < len(stages)):
        pr.error(f'{bw}.start', f'start fora da faixa 0..{len(stages) - 1}')
    for si, st in enumerate(stages):
        sw = f'{bw}.stages[{si}]'
        if not str(st.get('title', '')).strip():
            pr.error(f'{sw}.title', 'obrigatório')
        elif len(st['title']) > BUDGET['stage_title']:
            pr.warn(f'{sw}.title', f'título longo ({len(st["title"])} > {BUDGET["stage_title"]}): estoura a pílula do passo')
        g = st.get('graph')
        if st.get('empty') and g:
            pr.warn(sw, 'etapa com "empty" e "graph": o motor mostra só o texto vazio')
        if not g:
            continue
        _check_claim(st, sw, 'etapa', pr, require_source, verifier, needs=False)
        inherited = any(bool(o.get('source')) or o.get('status') == 'hipotese' for o in (blk, st))
        _check_graph(g, sw, types, cat_ids, pr, require_source, verifier, inherited)


def _check_graph(g, sw, types, cat_ids, pr, require_source, verifier=None, inherited=False):
    nodes, edges = g.get('nodes') or [], g.get('edges') or []
    if not nodes:
        pr.error(f'{sw}.graph.nodes', 'grafo sem nós')
        return
    ids = [n.get('id') for n in nodes]
    for ni, n in enumerate(nodes):
        w = f'{sw}.graph.nodes[{ni}]'
        nid = n.get('id')
        if not NODE_ID_RE.match(str(nid)):
            pr.error(f'{w}.id', f'id de nó inválido: {nid!r}')
        if ids.count(nid) > 1:
            pr.error(f'{w}.id', f'id de nó repetido: {nid}')
        if n.get('type') not in types:
            pr.warn(f'{w}.type', f'tipo de peça sem declaração em pieceTypes: {n.get("type")!r} (usa o estilo neutro, com o próprio id como rótulo)')
        if not str(n.get('title', '')).strip():
            pr.error(f'{w}.title', 'obrigatório')
        elif len(n['title']) > BUDGET['node_title']:
            pr.warn(f'{w}.title', f'título longo ({len(n["title"])} > {BUDGET["node_title"]}): a caixa cresce e desalinha as setas')
        if len(str(n.get('sub', ''))) > BUDGET['node_sub']:
            pr.warn(f'{w}.sub', f'subtítulo longo ({len(n["sub"])} > {BUDGET["node_sub"]}): mova o excesso para "detail"')
        for ref in n.get('refs') or []:
            tp, _, ident = str(ref).partition(':')
            if (tp, ident) not in cat_ids:
                pr.error(f'{w}.refs', f'ref {ref!r} não existe no catalog')
        _check_claim(n, w, 'nó', pr, require_source, verifier, needs=require_source and not inherited)

    id_set = set(ids)
    connected = set()
    for ei, e in enumerate(edges):
        w = f'{sw}.graph.edges[{ei}]'
        for end in ('from', 'to'):
            if e.get(end) not in id_set:
                pr.error(f'{w}.{end}', f'aresta aponta para nó inexistente: {e.get(end)!r}')
        connected.update([e.get('from'), e.get('to')])
        if len(str(e.get('label', ''))) > BUDGET['edge_label']:
            pr.warn(f'{w}.label', f'rótulo longo ({len(e["label"])} > {BUDGET["edge_label"]}): use um verbo curto')
        if e.get('from') == e.get('to'):
            pr.error(w, 'aresta de um nó para ele mesmo (laço) não é suportada: modele como estado ou como dois nós')
        _check_claim(e, w, 'aresta', pr, require_source, verifier, needs=require_source and not inherited)
    by_id = {n.get('id'): n for n in nodes}
    for n in nodes:
        if n.get('id') not in connected and len(nodes) > 1:
            if types.get(n.get('type')):
                pr.info(f'{sw}.graph.nodes', f'trava {n.get("id")} sem aresta: ela não aparece presa a nenhuma peça')
            else:
                pr.info(f'{sw}.graph.nodes', f'nó {n.get("id")} sem nenhuma aresta (ok se ele é um elemento avulso)')
    has_col = [isinstance(n.get('col'), int) and isinstance(n.get('row'), int) for n in nodes]
    if any(has_col) and not all(has_col):
        pr.error(f'{sw}.graph.nodes', 'layout misto: ou todos os nós têm col e row, ou nenhum (o motor organiza sozinho)')
        return
    if not all(has_col):
        pr.info(f'{sw}.graph', 'layout automático: o autoteste do render confere colisões; revise o quadro no navegador')
        return
    cells = {}
    for n in nodes:
        key = (n['col'], n['row'])
        if key in cells:
            pr.error(f'{sw}.graph.nodes', f'nós {cells[key]} e {n["id"]} na mesma célula (col {key[0]}, row {key[1]})')
        cells[key] = n['id']
    cols = max(n['col'] for n in nodes) + 1
    rows = max(n['row'] for n in nodes) + 1
    if cols > BUDGET['max_cols']:
        pr.warn(f'{sw}.graph', f'{cols} colunas (> {BUDGET["max_cols"]}): o quadro rola na horizontal; considere dividir em duas etapas')
    if rows > BUDGET['max_rows']:
        pr.warn(f'{sw}.graph', f'{rows} linhas (> {BUDGET["max_rows"]}): considere dividir a etapa')
    guards_by_col = {}
    for n in nodes:
        if types.get(n.get('type')):
            guards_by_col.setdefault(n['col'], []).append(n['id'])
    for col, gl in guards_by_col.items():
        if len(gl) > 1:
            pr.warn(f'{sw}.graph', f'{len(gl)} travas na coluna {col}: a ligação vertical de uma passa por cima da outra')
    # Aresta reta na mesma linha atravessa as células do meio: se houver nó lá, a seta passa por cima dele.
    for ei, e in enumerate(edges):
        a, b = by_id.get(e.get('from')), by_id.get(e.get('to'))
        if not a or not b or types.get(a.get('type')) or types.get(b.get('type')):
            continue
        if a['row'] == b['row'] and b['col'] - a['col'] > 1:
            blockers = [cells[(c, a['row'])] for c in range(a['col'] + 1, b['col']) if (c, a['row']) in cells]
            if blockers:
                pr.warn(f'{sw}.graph.edges[{ei}]', f'aresta {a["id"]}→{b["id"]} é reta na linha {a["row"]} e passa por cima de {", ".join(blockers)}: mude a linha de um dos nós')
        if b['col'] <= a['col'] and a['col'] != b['col']:
            pr.info(f'{sw}.graph.edges[{ei}]', f'aresta {a["id"]}→{b["id"]} volta para a esquerda: será desenhada por baixo dos nós')


def _norm_ws(text):
    return re.sub(r'\s+', ' ', str(text)).strip()


class SourceVerifier:
    """Confere `source`/`quote` contra arquivos reais numa pasta-raiz. Sem raiz, só valida a forma."""

    def __init__(self, root, require_quote=False):
        self.root = Path(root).resolve() if root else None
        self.require_quote = require_quote
        self._cache = {}

    def files_cited(self, source):
        found = []
        for token in FILE_TOKEN_RE.findall(str(source)):
            if token.startswith(('http', 'www')):
                continue
            found.append(token)
        return found

    def resolve(self, token):
        if not self.root:
            return None
        candidate = (self.root / token).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def text_of(self, path):
        if path not in self._cache:
            if path.stat().st_size > MAX_SOURCE_FILE:
                self._cache[path] = None
            else:
                self._cache[path] = _norm_ws(path.read_text(encoding='utf-8', errors='replace'))
        return self._cache[path]


def _check_claim(item, where, kind, pr, require_source, verifier, needs=None):
    """Fonte de um nó ou de uma aresta: presença, qualidade, existência do arquivo e do trecho citado."""
    status = item.get('status')
    if status is not None and status not in STATUS_VALUES:
        pr.error(f'{where}.status', f'status inválido: {status!r} (válidos: {sorted(STATUS_VALUES)})')
        return
    if status == 'hipotese':
        pr.info(where, f'{kind} marcado como hipótese: aparece como "a confirmar" na tela e vira pergunta ao usuário')
        return
    source, quote = item.get('source'), item.get('quote')
    needs = require_source if needs is None else needs
    strict = require_source or (verifier is not None)
    level = pr.error if strict else pr.warn
    if not source:
        if needs:
            pr.error(f'{where}.source', f'{kind} sem "source" (fonte que confirma que ele existe e faz isso); sem fonte, marque status "hipotese"')
        if quote:
            pr.error(f'{where}.quote', 'quote sem source: o trecho precisa dizer de qual fonte vem')
        return
    if PLACEHOLDER_SOURCE_RE.match(str(source)) or len(str(source).strip()) < 6:
        level(f'{where}.source', f'source genérico demais ({source!r}): cite o arquivo, o documento ou a conversa')
    if not verifier:
        return
    tokens = verifier.files_cited(source)
    existing = [verifier.resolve(t) for t in tokens]
    existing = [e for e in existing if e]
    if verifier.root:
        if tokens and not existing:
            pr.error(f'{where}.source', f'nenhum arquivo citado existe em --source-root: {", ".join(tokens)}')
        elif not tokens:
            pr.warn(f'{where}.source', 'source não cita arquivo (conversa, documento externo): não dá para conferir mecanicamente')
    if verifier.require_quote and not quote:
        pr.error(f'{where}.quote', f'{kind} sem "quote": copie o trecho literal da fonte que sustenta a afirmação')
    if quote:
        if not verifier.root:
            pr.info(f'{where}.quote', 'quote não conferida (use --source-root)')
        elif existing:
            needle = _norm_ws(quote)
            if not any((verifier.text_of(e) or '') and needle in verifier.text_of(e) for e in existing):
                pr.error(f'{where}.quote', 'o trecho citado não aparece em nenhum dos arquivos da source (copie literalmente, sem parafrasear)')
        elif tokens:
            pass  # arquivo inexistente já foi reportado acima
        else:
            pr.error(f'{where}.quote', 'quote exige que a source cite um arquivo conferível')


def _iter_claims(data):
    """Percorre tudo que pode carregar source/quote/status: nós, arestas, etapas, blocos e itens de bloco."""
    for ti, tab in enumerate(data.get('tabs') or []):
        for bi, blk in enumerate(tab.get('blocks') or []):
            bw = f'tabs[{ti}].blocks[{bi}]'
            t = blk.get('type')
            if t in ('rail', 'matrix', 'cards', 'roles', 'sample'):
                yield 'bloco', bw, blk, str(blk.get('title') or t), blk
                for ii, it in enumerate(blk.get(CLAIM_ITEMS.get(t, ''), []) or []):
                    if isinstance(it, dict):
                        yield 'item', f'{bw}.{CLAIM_ITEMS[t]}[{ii}]', it, str(it.get('title') or it.get('name') or ii), blk
            if t != 'board':
                continue
            yield 'bloco', bw, blk, str(blk.get('title') or 'board'), blk
            for si, st in enumerate(blk.get('stages') or []):
                g = st.get('graph') or {}
                sw = f'{bw}.stages[{si}]'
                titles = {n.get('id'): n.get('title') for n in g.get('nodes') or []}
                yield 'etapa', sw, st, str(st.get('title') or si), blk
                for ii, n in enumerate(g.get('nodes') or []):
                    yield 'nó', f'{sw}.graph.nodes[{ii}]', n, str(n.get('title') or n.get('id')), blk
                for ii, e in enumerate(g.get('edges') or []):
                    yield 'aresta', f'{sw}.graph.edges[{ii}]', e, f'{titles.get(e.get("from"))} → {titles.get(e.get("to"))}', blk


def source_summary(data):
    """Conta o que afirma fatos por situação de fonte, para o relatório de evidências."""
    out = {'claims': 0, 'confirmed': 0, 'hypotheses': 0, 'with_source': 0, 'with_quote': 0, 'nodes': 0, 'edges': 0}
    questions = []
    for kind, where, it, label, _blk in _iter_claims(data):
        if kind in ('bloco', 'etapa', 'item') and not (it.get('source') or it.get('quote') or it.get('status')):
            continue
        out['claims'] += 1
        if kind == 'nó':
            out['nodes'] += 1
        elif kind == 'aresta':
            out['edges'] += 1
        if it.get('status') == 'hipotese':
            out['hypotheses'] += 1
            questions.append(f'Confirmar hipótese em {where}: {label}' + (f' ({it["note"]})' if it.get('note') else ''))
        else:
            out['confirmed'] += 1
        out['with_source'] += 1 if it.get('source') else 0
        out['with_quote'] += 1 if it.get('quote') else 0
    return out, questions


def resolve_embeds(data, base_dir=None):
    """Cópia dos dados com o HTML dos blocos embed (snippet ou file) injetado em `srcdoc`."""
    import copy
    out = copy.deepcopy(data)
    for tab in out.get('tabs') or []:
        for blk in tab.get('blocks') or []:
            if blk.get('type') != 'embed' or blk.get('srcdoc'):
                continue
            if blk.get('snippet'):
                path = SNIPPETS_DIR / f'{blk["snippet"]}.html'
            else:
                path = Path(base_dir or '.') / str(blk.get('file', ''))
            blk['srcdoc'] = path.read_text(encoding='utf-8')
    return out


def build_html(data, template_path=None, base_dir=None):
    data = resolve_embeds(data, base_dir)
    tpl = Path(template_path or TEMPLATE_PATH).read_text(encoding='utf-8')
    if DATA_PLACEHOLDER not in tpl or TITLE_PLACEHOLDER not in tpl:
        raise ValueError('template inválido: faltam os marcadores {{TITLE}} e /*__EXPLAINER_DATA__*/')
    payload = json.dumps(data, ensure_ascii=False, indent=1)
    payload = payload.replace('</', '<\\/').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    title = str(data['meta']['title']).replace('&', '&amp;').replace('<', '&lt;')
    return tpl.replace(TITLE_PLACEHOLDER, title).replace(DATA_PLACEHOLDER, payload)


def summarize(problems):
    out = {'error': 0, 'warn': 0, 'info': 0}
    for p in problems:
        out[p['level']] = out.get(p['level'], 0) + 1
    return out
