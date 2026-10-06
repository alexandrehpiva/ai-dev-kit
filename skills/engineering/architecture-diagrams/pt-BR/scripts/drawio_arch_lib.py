"""Biblioteca mínima (só stdlib) para gerar diagramas de arquitetura .drawio
com ícones oficiais `mxgraph.aws4`, no padrão visual descrito em
`visual-patterns.md`: contêineres de fronteira, serviços como cartões com
ícone, setas numeradas coloridas por tema de fluxo, legenda e notas.

Uso: ver `example_architecture.py`. Coordenadas em pixels; a ordem de
criação define o empilhamento (grupos primeiro, serviços depois, setas
por último).
"""
import html
import xml.etree.ElementTree as ET

INK = "#232F3E"
MUTED = "#5A6570"
BORDER = "#B0B7C3"

# Paleta de categoria de serviço: (cor do ícone, cor do degradê). O cartão
# usa a cor do ícone na borda.
CATEGORIES = {
    "compute": ("#D05C17", "#F78E04"),
    "storage": ("#277116", "#60A337"),
    "database": ("#3334B9", "#4D72F3"),
    "network": ("#5A30B5", "#945DF2"),
    "integration": ("#BC1356", "#F34482"),
    "security": ("#C7131F", "#F54749"),
    "management": ("#BC1356", "#F34482"),
    "neutral": (INK, None),
}

# Cores de seta por tema de fluxo (um tema = um caminho lógico do sistema).
THEMES = {
    "main": INK,
    "orange": "#ED7100",
    "blue": "#2E73B8",
    "green": "#3F8624",
    "red": "#D13212",
    "pink": "#E7157B",
    "purple": "#8C4FFF",
}

# Pastéis para caixas de sistemas externos: (preenchimento, borda).
PASTELS = {
    "purple": ("#F0EAFF", "#5A30B5"),
    "orange": ("#FFF4E5", "#D05C17"),
    "blue": ("#EAF3FF", "#3334B9"),
    "green": ("#EAF6E7", "#277116"),
    "gray": ("#F2F4F7", "#5A6570"),
}

SIDES = {"l": (0, 0.5), "r": (1, 0.5), "t": (0.5, 0), "b": (0.5, 1)}


def esc(text):
    """Escapa texto para atributo/valor do XML; \\n vira quebra de linha HTML."""
    return html.escape(text, quote=True).replace("\n", "&lt;br&gt;")


def _check(value, allowed, name):
    if value not in allowed:
        raise ValueError(f"{name}={value!r} inválido; use um de {sorted(allowed)}")


class Diagram:
    def __init__(self, name="Arquitetura", width=1600, height=1000):
        self.name, self.width, self.height = name, width, height
        self.cells, self.ids, self.edges, self._seq = [], set(), [], 100

    def new_id(self, prefix):
        self._seq += 1
        nid = f"{prefix}{self._seq}"
        self.ids.add(nid)
        return nid

    def add_cell(self, xml):
        self.cells.append(xml)

    def to_drawio(self):
        for eid, src, dst in self.edges:
            for ref in (src, dst):
                if ref not in self.ids:
                    raise ValueError(f"seta {eid} referencia id inexistente: {ref}")
        return (
            '<mxfile host="app.diagrams.net"><diagram name="%s" id="d1">'
            '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
            'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            'pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
            '<root><mxCell id="0"/><mxCell id="1" parent="0"/>%s</root>'
            '</mxGraphModel></diagram></mxfile>'
            % (html.escape(self.name, quote=True), self.width, self.height, "".join(self.cells))
        )

    def save(self, path):
        """Grava o .drawio validando XML bem formado e setas com ids existentes."""
        xml = self.to_drawio()
        ET.fromstring(xml)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path


def _vertex(dia, prefix, value, style, x, y, w, h):
    vid = dia.new_id(prefix)
    dia.add_cell(
        f'<mxCell id="{vid}" value="{value}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    return vid


def add_title(dia, x, y, title, subtitle=None, w=900):
    """Título (e subtítulo opcional) no topo do diagrama."""
    value = f"&lt;b&gt;&lt;font style=&quot;font-size: 20px&quot;&gt;{esc(title)}&lt;/font&gt;&lt;/b&gt;"
    if subtitle:
        value += f"&lt;br&gt;&lt;font color=&quot;{MUTED}&quot;&gt;{esc(subtitle)}&lt;/font&gt;"
    return _vertex(dia, "title", value,
                   f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=14;fontColor={INK};",
                   x, y, w, 60)


GROUP_KINDS = {
    # (shape de grupo da AWS, cor da borda, tracejado)
    "cloud": ("mxgraph.aws4.group_aws_cloud_alt", INK, False),
    "network": ("mxgraph.aws4.group_vpc2", "#8C4FFF", False),
    "dashed": (None, "#879196", True),
}


def add_group(dia, x, y, w, h, label, kind="dashed"):
    """Contêiner de fronteira: 'cloud' (nuvem), 'network' (rede privada) ou
    'dashed' (agrupamento lógico cinza tracejado, também para 'fora da nuvem')."""
    _check(kind, GROUP_KINDS, "kind")
    shape, color, dashed = GROUP_KINDS[kind]
    if shape:
        style = (f"points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],"
                 f"[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;"
                 f"gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=0;"
                 f"collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon={shape};"
                 f"strokeColor={color};fillColor=none;verticalAlign=top;align=left;spacingLeft=30;"
                 f"fontColor={color};dashed=0;")
    else:
        style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor={color};dashed=1;"
                 f"dashPattern=8 8;strokeWidth=1.5;verticalAlign=top;align=left;spacingLeft=12;"
                 f"spacingTop=4;fontSize=12;fontStyle=1;fontColor={MUTED};arcSize=4;")
    return _vertex(dia, "grp", esc(label), style, x, y, w, h)


def add_actor(dia, x, y, label, size=56):
    """Ator de origem (usuário/cliente) — ícone `user` com rótulo abaixo."""
    style = (f"sketch=0;outlineConnect=0;fontColor={INK};fillColor={INK};strokeColor=#ffffff;"
             "dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;"
             "fontSize=12;fontStyle=1;aspect=fixed;shape=mxgraph.aws4.resourceIcon;"
             "resIcon=mxgraph.aws4.user;")
    return _vertex(dia, "actor", esc(label), style, x, y, size, size)


def add_service(dia, x, y, title, desc=None, icon="lambda", category="compute", w=240, h=72):
    """Cartão de serviço: caixa branca com borda na cor da categoria, ícone
    oficial à esquerda, título em negrito e descrição curta cinza.
    `icon` é o nome após `mxgraph.aws4.` (ex.: 'lambda', 'api_gateway')."""
    _check(category, CATEGORIES, "category")
    fill, grad = CATEGORIES[category]
    value = f"&lt;b&gt;{esc(title)}&lt;/b&gt;"
    if desc:
        value += f"&lt;br&gt;&lt;font style=&quot;font-size: 10px&quot; color=&quot;{MUTED}&quot;&gt;{esc(desc)}&lt;/font&gt;"
    card = _vertex(dia, "svc", value,
                   f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={fill};"
                   f"strokeWidth=1.5;align=left;verticalAlign=middle;spacingLeft=64;spacingRight=6;"
                   f"fontSize=12;fontColor={INK};arcSize=12;", x, y, w, h)
    g = f"gradientColor={grad};gradientDirection=north;" if grad else ""
    _vertex(dia, "ico",
            "",
            f"sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],"
            f"[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],"
            f"[1,0.75,0]];outlineConnect=0;fillColor={fill};{g}strokeColor=#ffffff;dashed=0;"
            f"verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;"
            f"fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};",
            x + 8, y + (h - 48) // 2, 48, 48)
    return card


def add_external(dia, x, y, title, role, color="purple", w=310, h=80):
    """Caixa pastel de sistema fora da nuvem principal (terceiro, legado,
    provedor): título em negrito + uma linha de função."""
    _check(color, PASTELS, "color")
    fill, stroke = PASTELS[color]
    value = f"&lt;b&gt;{esc(title)}&lt;/b&gt;&lt;br&gt;{esc(role)}"
    return _vertex(dia, "ext", value,
                   f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                   f"align=center;verticalAlign=middle;fontSize=11;fontColor={INK};", x, y, w, h)


def add_edge(dia, src_id, src_side, dst_id, dst_side, label=None, step=None,
             theme="main", asynchronous=False, via=None):
    """Seta ortogonal entre dois ids. `step` numera a ordem do fluxo ("1. ...");
    `theme` colore o caminho; `asynchronous=True` tracejado (evento/fila);
    `via` lista (x, y) para forçar a rota e evitar cruzar caixas."""
    _check(src_side, SIDES, "src_side")
    _check(dst_side, SIDES, "dst_side")
    _check(theme, THEMES, "theme")
    color = THEMES[theme]
    text = f"{step}. {label}" if step is not None and label else (str(step) if step is not None else (label or ""))
    ex, ey = SIDES[src_side]
    tx, ty = SIDES[dst_side]
    dash = "dashed=1;dashPattern=6 4;strokeWidth=1.5;" if asynchronous else "strokeWidth=2;"
    eid = dia.new_id("edge")
    pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in (via or []))
    wp = f'<Array as="points">{pts}</Array>' if pts else ""
    dia.add_cell(
        f'<mxCell id="{eid}" value="{esc(text)}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;'
        f'html=1;jumpStyle=arc;endArrow=blockThin;endFill=1;{dash}strokeColor={color};'
        f'fontColor={color};fontStyle=1;fontSize=11;labelBackgroundColor=#FFFFFF;'
        f'exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={tx};entryY={ty};entryDx=0;entryDy=0;" '
        f'edge="1" parent="1" source="{src_id}" target="{dst_id}">'
        f'<mxGeometry relative="1" as="geometry">{wp}</mxGeometry></mxCell>'
    )
    dia.edges.append((eid, src_id, dst_id))
    return eid


def add_legend(dia, x, y, entries, w=420):
    """Legenda: `entries` é lista de (tema, texto, assíncrono). Desenha uma
    caixa e uma amostra de linha por entrada, mais a regra da numeração."""
    h = 36 + 22 * (len(entries) + 1)
    _vertex(dia, "leg", f"&lt;b&gt;Legenda&lt;/b&gt;",
            f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={BORDER};align=left;"
            f"verticalAlign=top;spacingLeft=10;spacingTop=4;fontSize=12;fontColor={INK};", x, y, w, h)
    for i, (theme, text, is_async) in enumerate(entries):
        ly = y + 42 + 24 * i
        dash = "dashed=1;dashPattern=6 4;strokeWidth=1.5;" if is_async else "strokeWidth=2;"
        dia.add_cell(
            f'<mxCell id="{dia.new_id("legl")}" value="" style="endArrow=blockThin;endFill=1;html=1;'
            f'{dash}strokeColor={THEMES[theme]};" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x + 12}" y="{ly}" as="sourcePoint"/>'
            f'<mxPoint x="{x + 62}" y="{ly}" as="targetPoint"/></mxGeometry></mxCell>'
        )
        _vertex(dia, "legt", esc(text),
                f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=11;fontColor={INK};",
                x + 72, y + 32 + 24 * i, w - 80, 20)
    _vertex(dia, "legn", esc("Os números nos rótulos indicam a ordem do fluxo."),
            f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=11;fontColor={MUTED};",
            x + 12, y + 32 + 24 * len(entries), w - 20, 20)


def add_notes(dia, x, y, notes, col_w=420, h=220, gap=20):
    """Cartões de notas no rodapé, lado a lado. `notes` = lista de
    (título, [linhas]). Detalhe técnico mora aqui, não nas caixas."""
    for i, (title, lines) in enumerate(notes):
        body = "&lt;br&gt;".join(esc("• " + ln) for ln in lines)
        _vertex(dia, "note", f"&lt;b&gt;{esc(title)}&lt;/b&gt;&lt;br&gt;&lt;br&gt;{body}",
                f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={BORDER};align=left;"
                f"verticalAlign=top;spacing=10;fontSize=11;fontColor={INK};",
                x + i * (col_w + gap), y, col_w, h)
