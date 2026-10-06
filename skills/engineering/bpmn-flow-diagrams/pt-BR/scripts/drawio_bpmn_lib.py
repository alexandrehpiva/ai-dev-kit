"""Biblioteca stdlib para gerar diagramas BPMN em .drawio (mxGraph XML).

Aqui não se desenha pixel a pixel: cada forma vira uma célula mxGraph com id
estável, e cada seta referencia os ids de origem/destino (não coordenadas
soltas) com edgeStyle=orthogonalEdgeStyle. O draw.io calcula a rota e quem abrir
o arquivo pode arrastar qualquer caixa/seta sem reabrir o script gerador.

Uso: copie este arquivo para junto do script do diagrama, importe e monte o
diagrama (ver example_drawio.py). Não edite a lib por diagrama: a lógica de
layout (que nó fica em que coluna/raia) vive no script de cada diagrama.
"""
import html
import xml.etree.ElementTree as ET

GATEWAY_SYMBOLS = {"x": "X", "+": "+", "o": "O"}
EVENT_KINDS = ("start", "end", "intermediate")
EDGE_KINDS = ("sequence", "message", "association")
SIDES = {"l": (0, 0.5), "r": (1, 0.5), "t": (0.5, 0), "b": (0.5, 1)}

# status -> estilo de borda. gap = ausência confirmada; confirmado = verificado
# na fonte; bug = existe e roda, mas faz a coisa errada (ver shapes-and-colors.md).
STATUS_STYLE = {
    "gap": "strokeColor=#d1453b;dashed=1;dashPattern=5 4;strokeWidth=2;",
    "confirmado": "strokeColor=#2d9d5f;strokeWidth=3;",
    "bug": "strokeColor=#b5540e;strokeWidth=3;",
}


def _attr(text_html):
    """Valor de atributo XML a partir de um trecho HTML já seguro."""
    return html.escape(text_html, quote=True)


def label_value(text):
    """Texto puro -> valor de atributo. As células usam html=1, então o texto
    precisa de DOIS escapes (HTML e depois XML); sem isso, um '<' no rótulo vira tag."""
    return _attr(html.escape(str(text), quote=False))


def _check(value, allowed, name):
    if value not in allowed:
        raise ValueError(f"{name} inválido: {value!r} (aceitos: {', '.join(map(str, allowed))})")


def _style_with_status(base, status, default_stroke):
    if status is None:
        return base + f"strokeColor={default_stroke};"
    _check(status, STATUS_STYLE, "status")
    return base + STATUS_STYLE[status]


class Diagram:
    def __init__(self, name="BPMN"):
        self.name = name
        self.cells = []
        self.ids = set()
        self.edges = []  # (id, source, target)
        self._seq = 100

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
            '<mxfile host="app.diagrams.net">'
            f'<diagram name="{label_value(self.name)}" id="d1">'
            '<mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" '
            'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            'pageWidth="850" pageHeight="1100" math="0" shadow="0">'
            '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            f'{"".join(self.cells)}'
            '</root></mxGraphModel></diagram></mxfile>'
        )

    def save(self, path):
        """Grava o .drawio e garante que o XML é bem formado e que as setas
        apontam para ids existentes. Levanta exceção se não for."""
        xml = self.to_drawio()
        ET.fromstring(xml)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path


def add_lanes(dia, x, y, width, lanes, label_w=150):
    """lanes: lista de (label, altura). Desenha cada raia e o rótulo rotacionado
    na coluna esquerda. Retorna dict label -> (y_topo, y_base, y_meio)."""
    pos = {}
    cy = y
    total_h = sum(h for _, h in lanes)
    for label, h in lanes:
        dia.add_cell(
            f'<mxCell id="{dia.new_id("lane")}" value="" style="rounded=0;whiteSpace=wrap;html=1;'
            'fillColor=none;strokeColor=#333333;strokeWidth=1;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{cy}" width="{width}" height="{h}" as="geometry"/></mxCell>'
        )
        lw = max(h - 10, 40)  # largura do texto antes de rotacionar = altura da raia
        dia.add_cell(
            f'<mxCell id="{dia.new_id("lanelbl")}" value="{label_value(label)}" '
            'style="text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;'
            'rotation=-90;fontSize=13;" vertex="1" parent="1">'
            f'<mxGeometry x="{x + label_w / 2 - lw / 2}" y="{cy + h / 2 - 15}" '
            f'width="{lw}" height="30" as="geometry"/></mxCell>'
        )
        pos[label] = (cy, cy + h, cy + h / 2)
        cy += h
    dia.add_cell(
        f'<mxCell id="{dia.new_id("div")}" style="endArrow=none;html=1;strokeColor=#333333;'
        'strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x + label_w}" y="{y}" as="sourcePoint"/>'
        f'<mxPoint x="{x + label_w}" y="{y + total_h}" as="targetPoint"/>'
        '</mxGeometry></mxCell>'
    )
    return pos


def add_task(dia, cx, cy, title, desc=None, w=160, h=76, status=None):
    nid = dia.new_id("task")
    label = f"<b>{html.escape(str(title), quote=False)}</b>"
    if desc:
        label += ('<br><font style="font-size:10px" color="#555555">'
                  f'{html.escape(str(desc), quote=False)}</font>')
    style = _style_with_status(
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#eef6fd;fontSize=12;"
        "align=center;verticalAlign=middle;spacing=6;", status, "#5b8dc9")
    dia.add_cell(
        f'<mxCell id="{nid}" value="{_attr(label)}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    return nid


def add_gateway(dia, cx, cy, symbol="x", size=54, status=None):
    _check(symbol, GATEWAY_SYMBOLS, "symbol")
    nid = dia.new_id("gw")
    style = _style_with_status(
        "rhombus;whiteSpace=wrap;html=1;fillColor=#fff6df;fontSize=18;fontStyle=1;"
        "align=center;verticalAlign=middle;", status, "#c9962e")
    dia.add_cell(
        f'<mxCell id="{nid}" value="{GATEWAY_SYMBOLS[symbol]}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}" as="geometry"/></mxCell>'
    )
    return nid


def add_event(dia, cx, cy, kind="start", label=None, size=44):
    _check(kind, EVENT_KINDS, "kind")
    nid = dia.new_id("ev")
    style = {
        "start": "ellipse;fillColor=#eaf7ea;strokeColor=#4a9d4a;strokeWidth=2;",
        "end": "ellipse;fillColor=#ffffff;strokeColor=#333333;strokeWidth=4;",
        "intermediate": "shape=doubleEllipse;fillColor=#ffffff;strokeColor=#4a9d4a;strokeWidth=2;",
    }[kind]
    dia.add_cell(
        f'<mxCell id="{nid}" value="{label_value(label) if label else ""}" '
        f'style="{style}whiteSpace=wrap;html=1;fontSize=11;verticalLabelPosition=bottom;'
        'verticalAlign=top;align=center;" vertex="1" parent="1">'
        f'<mxGeometry x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}" as="geometry"/></mxCell>'
    )
    return nid


def add_data_object(dia, cx, cy, label, w=54, h=66):
    nid = dia.new_id("data")
    dia.add_cell(
        f'<mxCell id="{nid}" value="{label_value(label)}" style="shape=note;whiteSpace=wrap;html=1;'
        'size=14;fillColor=#ffffff;strokeColor=#7a7a7a;fontSize=10.5;verticalLabelPosition=bottom;'
        'verticalAlign=top;align=center;" vertex="1" parent="1">'
        f'<mxGeometry x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    return nid


def add_data_store(dia, cx, cy, label, w=76, h=54):
    nid = dia.new_id("store")
    dia.add_cell(
        f'<mxCell id="{nid}" value="{label_value(label)}" style="shape=cylinder3;whiteSpace=wrap;html=1;'
        'fillColor=#f5f5f5;strokeColor=#666666;fontSize=10.5;verticalLabelPosition=bottom;'
        'verticalAlign=top;align=center;" vertex="1" parent="1">'
        f'<mxGeometry x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    return nid


def add_edge(dia, src_id, src_side, dst_id, dst_side, kind="sequence", label=None, via=None):
    """Seta entre dois ids. src_side/dst_side: l, r, t, b. via: lista opcional de
    (x, y) para forçar a rota (ex.: laço de retry passando abaixo da fileira)."""
    _check(src_side, SIDES, "src_side")
    _check(dst_side, SIDES, "dst_side")
    _check(kind, EDGE_KINDS, "kind")
    ex, ey = SIDES[src_side]
    tx, ty = SIDES[dst_side]
    base = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
    style = base + {
        "sequence": "endArrow=block;endFill=1;strokeColor=#333333;",
        "message": "dashed=1;dashPattern=6 4;endArrow=block;endFill=1;strokeColor=#333333;",
        "association": "dashed=1;dashPattern=1 2;endArrow=open;endFill=0;strokeColor=#888888;",
    }[kind]
    eid = dia.new_id("edge")
    waypoints = ""
    if via:
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in via)
        waypoints = f'<Array as="points">{pts}</Array>'
    dia.add_cell(
        f'<mxCell id="{eid}" value="{label_value(label) if label else ""}" '
        f'style="{style}exitX={ex};exitY={ey};exitDx=0;exitDy=0;'
        f'entryX={tx};entryY={ty};entryDx=0;entryDy=0;fontSize=10.5;labelBackgroundColor=#ffffff;" '
        f'edge="1" parent="1" source="{src_id}" target="{dst_id}">'
        f'<mxGeometry relative="1" as="geometry">{waypoints}</mxGeometry></mxCell>'
    )
    dia.edges.append((eid, src_id, dst_id))
    return eid
