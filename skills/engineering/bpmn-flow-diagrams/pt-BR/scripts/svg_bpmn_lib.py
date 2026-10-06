"""
Biblioteca mínima (stdlib puro, sem dependências) para desenhar diagramas BPMN
em SVG puro, no estilo "Bizagi/Camunda": tarefas em retângulo arredondado com
gradiente azul, gateways em losango com símbolo (+/x/o), eventos em círculo,
objetos de dado com canto dobrado, repositórios de dado em cilindro.

Uso típico: copiar este arquivo para junto do script do diagrama, importar as
funções e montar um script específico por diagrama (ver example_svg.py e o
SKILL.md, seção "Ferramenta"). Este arquivo não deve ser editado por diagrama
— é a camada de formas reutilizável; a lógica de layout (que nó fica em que
coluna/raia) vive no script de cada diagrama. Não há roteamento automático de
seta: as polilinhas são calculadas pelo script (ver layout-grid.md).
"""

import textwrap
import xml.etree.ElementTree as ET

GATEWAY_SYMBOLS = ("x", "+", "o")
EVENT_KINDS = ("start", "end", "intermediate")
ARROW_KINDS = ("sequence", "message", "association")
STATUSES = ("gap", "confirmado", "bug")


def _check(value, allowed, name):
    if value not in allowed:
        raise ValueError(f"{name} inválido: {value!r} (aceitos: {', '.join(map(str, allowed))})")

# ---------- estilo (paleta) ----------

TASK_GRADIENT = ("#eef6fd", "#cfe3f8")  # topo -> base
TASK_STROKE = "#5b8dc9"
GATEWAY_FILL = ("#fff6df", "#fbe2a6")
GATEWAY_STROKE = "#c9962e"
START_FILL = "#eaf7ea"
START_STROKE = "#4a9d4a"
END_STROKE = "#333333"
DATA_STROKE = "#7a7a7a"
GAP_STROKE = "#d1453b"
CONFIRMADO_STROKE = "#2d9d5f"
BUG_STROKE = "#b5540e"
LANE_LABEL_FILL = "#f4f4f4"
TEXT_COLOR = "#1a1a1a"
DESC_COLOR = "#555555"


class Canvas:
    def __init__(self, width, height, title=None):
        self.width = width
        self.height = height
        self.title = title
        self.body = []
        self.defs = []
        self._grad_ids = set()

    def _ensure_task_gradient(self):
        if "taskGrad" in self._grad_ids:
            return
        self._grad_ids.add("taskGrad")
        top, bot = TASK_GRADIENT
        self.defs.append(
            f'<linearGradient id="taskGrad" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{top}"/>'
            f'<stop offset="100%" stop-color="{bot}"/>'
            f"</linearGradient>"
        )

    def _ensure_gateway_gradient(self):
        if "gwGrad" in self._grad_ids:
            return
        self._grad_ids.add("gwGrad")
        top, bot = GATEWAY_FILL
        self.defs.append(
            f'<linearGradient id="gwGrad" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{top}"/>'
            f'<stop offset="100%" stop-color="{bot}"/>'
            f"</linearGradient>"
        )

    def _ensure_arrowheads(self):
        if "arrow" in self._grad_ids:
            return
        self._grad_ids.add("arrow")
        self.defs.append(
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker>'
        )
        self.defs.append(
            '<marker id="arrowAssoc" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#888"/></marker>'
        )

    def add_raw(self, svg_fragment):
        self.body.append(svg_fragment)

    def save(self, path):
        """Grava o SVG e garante que o XML é bem formado. Levanta exceção se não for."""
        svg = self.to_svg()
        ET.fromstring(svg)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        return path

    def to_svg(self):
        defs = "".join(self.defs)
        body = "".join(self.body)
        title_svg = ""
        if self.title:
            title_svg = (
                f'<text x="20" y="30" font-family="Helvetica, Arial, sans-serif" '
                f'font-size="20" fill="{TEXT_COLOR}">{esc(self.title)}</text>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
            f'font-family="Helvetica, Arial, sans-serif">'
            f"<defs>{defs}</defs>"
            f'<rect x="0" y="0" width="{self.width}" height="{self.height}" fill="#ffffff"/>'
            f"{title_svg}{body}</svg>"
        )


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def wrap(text, width_chars):
    return textwrap.wrap(text, width_chars) or [""]


# ---------- raias (pool/lanes) ----------

def add_pool(canvas, x, y, width, lanes, label_col_w=150):
    """lanes: lista de (lane_id, label, height). Retorna dict lane_id ->
    (y_top, y_bottom, y_mid) em coordenadas absolutas do canvas."""
    total_h = sum(h for _, _, h in lanes)
    canvas.add_raw(
        f'<rect x="{x}" y="{y}" width="{width}" height="{total_h}" '
        f'fill="none" stroke="#333" stroke-width="1.5"/>'
    )
    canvas.add_raw(
        f'<line x1="{x + label_col_w}" y1="{y}" x2="{x + label_col_w}" '
        f'y2="{y + total_h}" stroke="#333" stroke-width="1.5"/>'
    )
    positions = {}
    cursor = y
    for lane_id, label, h in lanes:
        if cursor != y:
            canvas.add_raw(
                f'<line x1="{x}" y1="{cursor}" x2="{x + width}" y2="{cursor}" '
                f'stroke="#333" stroke-width="1"/>'
            )
        mid = cursor + h / 2
        # o texto é rotacionado: o comprimento disponível é a altura da raia
        lines = wrap(label, max(8, int((h - 10) / 8.5)))
        lx = x + label_col_w / 2
        for i, line in enumerate(lines):
            ly = lx + (i - (len(lines) - 1) / 2) * 18
            canvas.add_raw(
                f'<text x="{ly}" y="{mid}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="15" fill="{TEXT_COLOR}" '
                f'transform="rotate(-90 {ly} {mid})">{esc(line)}</text>'
            )
        positions[lane_id] = (cursor, cursor + h, mid)
        cursor += h
    return positions


# ---------- formas ----------

def _status_stroke(status):
    if status is not None:
        _check(status, STATUSES, "status")
    if status == "gap":
        return GAP_STROKE, "5,4", 2.5
    if status == "confirmado":
        return CONFIRMADO_STROKE, "0", 2.5
    if status == "bug":
        # laranja-queimado sólido, mais grosso: distinto do vermelho tracejado
        # (gap = ausência confirmada) e do verde sólido (confirmado). bug = existe
        # e RODA, mas faz a coisa errada. Ver shapes-and-colors.md.
        return BUG_STROKE, "0", 3.2
    return None


def add_task(canvas, cx, cy, title, desc=None, w=160, h=76, status=None):
    canvas._ensure_task_gradient()
    x, y = cx - w / 2, cy - h / 2
    canvas.add_raw(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" ry="12" '
        f'fill="url(#taskGrad)" stroke="{TASK_STROKE}" stroke-width="1.5"/>'
    )
    extra = _status_stroke(status)
    if extra:
        stroke, dash, sw = extra
        dash_attr = f' stroke-dasharray="{dash}"' if dash != "0" else ""
        canvas.add_raw(
            f'<rect x="{x - 4}" y="{y - 4}" width="{w + 8}" height="{h + 8}" '
            f'rx="15" ry="15" fill="none" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'
        )
    lines = wrap(title, 22)
    ty = cy - (len(lines) - 1) * 8 - (6 if desc else 0)
    for line in lines:
        canvas.add_raw(
            f'<text x="{cx}" y="{ty}" text-anchor="middle" font-size="13" '
            f'font-weight="600" fill="{TEXT_COLOR}">{esc(line)}</text>'
        )
        ty += 16
    if desc:
        dlines = wrap(desc, 26)[:2]
        dy = ty + 2
        for line in dlines:
            canvas.add_raw(
                f'<text x="{cx}" y="{dy}" text-anchor="middle" font-size="10.5" '
                f'fill="{DESC_COLOR}">{esc(line)}</text>'
            )
            dy += 12
    return {"c": (cx, cy), "l": (x, cy), "r": (x + w, cy), "t": (cx, y), "b": (cx, y + h)}


def add_gateway(canvas, cx, cy, symbol="x", size=54, status=None):
    _check(symbol, GATEWAY_SYMBOLS, "symbol")
    canvas._ensure_gateway_gradient()
    half = size / 2
    pts = f"{cx},{cy-half} {cx+half},{cy} {cx},{cy+half} {cx-half},{cy}"
    canvas.add_raw(
        f'<polygon points="{pts}" fill="url(#gwGrad)" stroke="{GATEWAY_STROKE}" stroke-width="1.5"/>'
    )
    extra = _status_stroke(status)
    if extra:
        stroke, dash, sw = extra
        dash_attr = f' stroke-dasharray="{dash}"' if dash != "0" else ""
        big = half + 6
        pts2 = f"{cx},{cy-big} {cx+big},{cy} {cx},{cy+big} {cx-big},{cy}"
        canvas.add_raw(
            f'<polygon points="{pts2}" fill="none" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'
        )
    s = size * 0.22
    if symbol == "+":
        canvas.add_raw(
            f'<line x1="{cx-s}" y1="{cy}" x2="{cx+s}" y2="{cy}" stroke="{GATEWAY_STROKE}" stroke-width="2.5"/>'
            f'<line x1="{cx}" y1="{cy-s}" x2="{cx}" y2="{cy+s}" stroke="{GATEWAY_STROKE}" stroke-width="2.5"/>'
        )
    elif symbol == "x":
        canvas.add_raw(
            f'<line x1="{cx-s}" y1="{cy-s}" x2="{cx+s}" y2="{cy+s}" stroke="{GATEWAY_STROKE}" stroke-width="2.5"/>'
            f'<line x1="{cx-s}" y1="{cy+s}" x2="{cx+s}" y2="{cy-s}" stroke="{GATEWAY_STROKE}" stroke-width="2.5"/>'
        )
    elif symbol == "o":
        canvas.add_raw(
            f'<circle cx="{cx}" cy="{cy}" r="{s}" fill="none" stroke="{GATEWAY_STROKE}" stroke-width="2.5"/>'
        )
    return {"c": (cx, cy), "l": (cx - half, cy), "r": (cx + half, cy), "t": (cx, cy - half), "b": (cx, cy + half)}


def add_event(canvas, cx, cy, kind="start", label=None, size=44):
    _check(kind, EVENT_KINDS, "kind")
    r = size / 2
    if kind == "start":
        canvas.add_raw(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{START_FILL}" stroke="{START_STROKE}" stroke-width="2"/>'
        )
    elif kind == "end":
        canvas.add_raw(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="{END_STROKE}" stroke-width="4"/>'
        )
    else:  # intermediate
        canvas.add_raw(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="{START_STROKE}" stroke-width="2"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r-4}" fill="none" stroke="{START_STROKE}" stroke-width="1.5"/>'
        )
    if label:
        for i, line in enumerate(wrap(label, 16)):
            canvas.add_raw(
                f'<text x="{cx}" y="{cy + r + 16 + i * 13}" text-anchor="middle" '
                f'font-size="11" fill="{TEXT_COLOR}">{esc(line)}</text>'
            )
    return {"c": (cx, cy), "l": (cx - r, cy), "r": (cx + r, cy), "t": (cx, cy - r), "b": (cx, cy + r)}


def add_data_object(canvas, cx, cy, label, w=54, h=66):
    x, y = cx - w / 2, cy - h / 2
    fold = 14
    path = (
        f"M{x},{y} L{x+w-fold},{y} L{x+w},{y+fold} L{x+w},{y+h} L{x},{y+h} Z"
    )
    canvas.add_raw(f'<path d="{path}" fill="#ffffff" stroke="{DATA_STROKE}" stroke-width="1.3"/>')
    canvas.add_raw(
        f'<path d="M{x+w-fold},{y} L{x+w-fold},{y+fold} L{x+w},{y+fold}" '
        f'fill="none" stroke="{DATA_STROKE}" stroke-width="1.3"/>'
    )
    for i in range(3):
        ly = y + h * 0.45 + i * 8
        canvas.add_raw(
            f'<line x1="{x+8}" y1="{ly}" x2="{x+w-8}" y2="{ly}" stroke="#bbb" stroke-width="1"/>'
        )
    for i, line in enumerate(wrap(label, 16)):
        canvas.add_raw(
            f'<text x="{cx}" y="{y + h + 14 + i * 12}" text-anchor="middle" '
            f'font-size="10.5" fill="{TEXT_COLOR}">{esc(line)}</text>'
        )
    return {"c": (cx, cy), "l": (x, cy), "r": (x + w, cy), "t": (cx, y), "b": (cx, y + h)}


def add_data_store(canvas, cx, cy, label, w=76, h=54):
    x, y = cx - w / 2, cy - h / 2
    ry = 9
    canvas.add_raw(
        f'<path d="M{x},{y+ry} A{w/2},{ry} 0 0 1 {x+w},{y+ry} L{x+w},{y+h-ry} '
        f'A{w/2},{ry} 0 0 1 {x},{y+h-ry} Z" fill="#ffffff" stroke="{DATA_STROKE}" stroke-width="1.3"/>'
    )
    canvas.add_raw(
        f'<ellipse cx="{cx}" cy="{y+ry}" rx="{w/2}" ry="{ry}" fill="#ffffff" stroke="{DATA_STROKE}" stroke-width="1.3"/>'
    )
    for i, line in enumerate(wrap(label, 16)):
        canvas.add_raw(
            f'<text x="{cx}" y="{y + h + 14 + i * 12}" text-anchor="middle" '
            f'font-size="10.5" fill="{TEXT_COLOR}">{esc(line)}</text>'
        )
    return {"c": (cx, cy), "l": (x, cy), "r": (x + w, cy), "t": (cx, y), "b": (cx, y + h)}


# ---------- conectores ----------

def add_arrow(canvas, points, kind="sequence", label=None):
    """points: lista de (x,y) — reta ou polilinha cotovelo já calculada
    pelo script do diagrama (não há roteamento automático)."""
    _check(kind, ARROW_KINDS, "kind")
    canvas._ensure_arrowheads()
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    if kind == "sequence":
        canvas.add_raw(
            f'<path d="{d}" fill="none" stroke="#333" stroke-width="1.6" marker-end="url(#arrow)"/>'
        )
    elif kind == "message":
        canvas.add_raw(
            f'<path d="{d}" fill="none" stroke="#333" stroke-width="1.6" '
            f'stroke-dasharray="6,4" marker-end="url(#arrow)"/>'
        )
    else:  # association (linha para dado, sem seta cheia)
        canvas.add_raw(
            f'<path d="{d}" fill="none" stroke="{DATA_STROKE}" stroke-width="1.2" '
            f'stroke-dasharray="3,3" marker-end="url(#arrowAssoc)"/>'
        )
    if label:
        seg = len(points) // 2
        ax, ay = points[seg - 1] if seg > 0 else points[0]
        bx, by = points[seg]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        w = 8 + len(label) * 6.2
        canvas.add_raw(
            f'<rect x="{mx-w/2}" y="{my-16}" width="{w}" height="14" fill="#ffffff" opacity="0.85"/>'
            f'<text x="{mx}" y="{my-6}" text-anchor="middle" font-size="10.5" fill="#333">{esc(label)}</text>'
        )
