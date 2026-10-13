"""Biblioteca mínima (só stdlib) para gerar diagramas C4 em .drawio.

Implementa as regras de notação de https://c4model.com/diagrams/notation e o
checklist de https://c4model.com/diagrams/checklist: título com tipo e escopo,
legenda obrigatória (gerada automaticamente), tipo/descrição em todo elemento,
tecnologia em todo contêiner/componente, seta unidirecional com rótulo
específico e tecnologia/protocolo entre contêineres. `save()` roda `lint()` e
recusa gravar diagrama que viole alguma regra.

Os tokens visuais (cores, tamanhos) vêm de `c4-style-tokens.json`, ao lado.
Cores são escolha deste kit (contraste WCAG AA >= 4.5 com texto branco/escuro),
não prescrição do C4.

Níveis aceitos (`level`): context, container, component, dynamic, deployment.
Coordenadas em pixels; a ordem de criação é a ordem de empilhamento
(boundaries primeiro, elementos depois, setas por último).
"""
import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path

TOKENS = json.loads((Path(__file__).with_name("c4-style-tokens.json")).read_text(encoding="utf-8"))
COL = TOKENS["colors"]

LEVELS = {"context", "container", "component", "dynamic", "deployment"}
# Elementos permitidos por nível (primários + de apoio, conforme as páginas de
# cada diagrama em c4model.com/diagrams/*).
ALLOWED = {
    "context": {"person", "system", "external_system"},
    "container": {"person", "system", "external_system", "container", "boundary_system"},
    "component": {"person", "system", "external_system", "container", "component", "boundary_container"},
    "dynamic": {"person", "system", "external_system", "container", "component",
                "boundary_system", "boundary_container"},
    "deployment": {"node", "container_instance", "system_instance", "infra_node"},
}
VAGUE_LABELS = {"uses", "use", "usa", "usar", "uso", "calls", "chama"}
SIDES = {"l": (0, 0.5), "r": (1, 0.5), "t": (0.5, 0), "b": (0.5, 1)}


def _esc(text):
    return html.escape(text, quote=True)


class C4Diagram:
    def __init__(self, level, scope, width=1500, height=1000, title=None):
        if level not in LEVELS:
            raise ValueError(f"level={level!r}; use um de {sorted(LEVELS)}")
        self.level, self.scope, self.width, self.height = level, scope, width, height
        names = {"context": "System Context", "container": "Container", "component": "Component",
                 "dynamic": "Dynamic", "deployment": "Deployment"}
        self.title = title or f"{names[level]} diagram for {scope}"
        self.cells, self.elements, self.edges = [], {}, []
        self._seq = 100
        self._used_kinds, self._used_edge_styles = set(), set()

    def _id(self, prefix):
        self._seq += 1
        return f"{prefix}{self._seq}"

    def _vertex(self, vid, value, style, x, y, w, h):
        self.cells.append(
            f'<mxCell id="{vid}" value="{value}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    @staticmethod
    def _label(name, type_line, desc, fg):
        v = f'<b style="font-size:14px">{html.escape(name)}</b>'
        v += f'<div style="font-size:11px">[{html.escape(type_line)}]</div>'
        if desc:
            v += f'<div style="font-size:12px;margin-top:6px">{html.escape(desc)}</div>'
        return _esc(f'<span style="color:{fg}">{v}</span>')

    def _element(self, kind, name, type_line, desc, x, y, w, h, style, fg, **meta):
        vid = self._id("el")
        self.elements[vid] = dict(kind=kind, name=name, type_line=type_line, desc=desc,
                                  tech=meta.get("tech"), box=(x, y, w, h))
        self._used_kinds.add(meta.get("legend_key", kind))
        self._vertex(vid, self._label(name, type_line, desc, fg), style, x, y, w, h)
        return vid

    # --- elementos estáticos -------------------------------------------------
    def person(self, x, y, name, desc, external=False, w=200, h=150):
        c = COL["person_external"] if external else COL["person"]
        style = (f"html=1;whiteSpace=wrap;align=center;verticalAlign=middle;shape=mxgraph.c4.person2;"
                 f"fillColor={c};strokeColor={c};fontColor=#FFFFFF;fontSize=12;resizable=0;")
        return self._element("person", name, "Person", desc, x, y, w, h, style, "#FFFFFF",
                             legend_key="person_external" if external else "person")

    def system(self, x, y, name, desc, external=False, w=240, h=130):
        if external:
            style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={COL['system_external']};"
                     f"strokeColor={COL['system_external_border']};strokeWidth=2;dashed=1;dashPattern=8 4;"
                     f"fontColor=#FFFFFF;align=center;verticalAlign=middle;fontSize=12;")
            return self._element("external_system", name, "External Software System", desc, x, y, w, h,
                                 style, "#FFFFFF")
        style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={COL['system']};"
                 f"strokeColor={COL['system_border']};strokeWidth=2;fontColor=#FFFFFF;align=center;"
                 f"verticalAlign=middle;fontSize=12;")
        return self._element("system", name, "Software System", desc, x, y, w, h, style, "#FFFFFF")

    def container(self, x, y, name, tech, desc, shape="box", w=240, h=130):
        """shape: box | database | webapp | mobile | queue (forma só reforça o tipo; a
        tecnologia vai sempre no rótulo)."""
        shapes = {
            "box": "rounded=1;arcSize=8;",
            "database": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=15;",
            "webapp": "shape=mxgraph.mockup.containers.browserWindow;mainText=;strokeColor2=#FFFFFF;",
            "mobile": "rounded=1;arcSize=14;",
            "queue": "shape=process;backgroundOutline=1;size=0.08;",
        }
        if shape not in shapes:
            raise ValueError(f"shape={shape!r}; use um de {sorted(shapes)}")
        style = (f"{shapes[shape]}whiteSpace=wrap;html=1;fillColor={COL['container']};"
                 f"strokeColor={COL['container_border']};strokeWidth=2;fontColor=#FFFFFF;"
                 f"align=center;verticalAlign=middle;fontSize=12;")
        if shape == "webapp":
            style = (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor={COL['container']};"
                     f"strokeColor={COL['container_border']};strokeWidth=2;fontColor=#FFFFFF;"
                     f"align=center;verticalAlign=middle;fontSize=12;")
        return self._element("container", name, f"Container: {tech}", desc, x, y, w, h, style, "#FFFFFF",
                             tech=tech)

    def component(self, x, y, name, tech, desc, w=240, h=120):
        style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={COL['component']};"
                 f"strokeColor={COL['component_border']};strokeWidth=2;fontColor={COL['ink']};"
                 f"align=center;verticalAlign=middle;fontSize=12;")
        return self._element("component", name, f"Component: {tech}", desc, x, y, w, h, style,
                             COL["ink"], tech=tech)

    def boundary(self, x, y, w, h, name, kind="system"):
        """kind: system | container (fronteira tracejada com título e tipo)."""
        if kind not in ("system", "container"):
            raise ValueError("kind deve ser 'system' ou 'container'")
        vid = self._id("bd")
        self.elements[vid] = dict(kind=f"boundary_{kind}", name=name, type_line=kind, desc="x", tech=None,
                                  box=(x, y, w, h))
        self._used_kinds.add("boundary")
        label = _esc(f'<b style="font-size:13px">{html.escape(name)}</b>'
                     f'<div style="font-size:11px">[{kind.capitalize()}]</div>')
        style = (f"rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor=none;strokeColor={COL['boundary']};"
                 f"strokeWidth=2;dashed=1;dashPattern=10 6;verticalAlign=top;align=left;spacingLeft=12;"
                 f"spacingTop=6;fontColor={COL['boundary']};fontSize=12;")
        self._vertex(vid, label, style, x, y, w, h)
        return vid

    # --- implantação -----------------------------------------------------------
    def node(self, x, y, w, h, name, tech):
        vid = self._id("nd")
        self.elements[vid] = dict(kind="node", name=name, type_line=f"Deployment Node: {tech}", desc="x",
                                  tech=tech, box=(x, y, w, h))
        self._used_kinds.add("node")
        label = _esc(f'<b style="font-size:13px">{html.escape(name)}</b>'
                     f'<div style="font-size:11px">[Deployment Node: {html.escape(tech)}]</div>')
        style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={COL['node_fill']};strokeColor={COL['boundary']};"
                 f"strokeWidth=2;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;"
                 f"fontColor={COL['ink']};fontSize=12;")
        self._vertex(vid, label, style, x, y, w, h)
        return vid

    def container_instance(self, x, y, name, tech, desc, w=240, h=110):
        style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor={COL['container']};"
                 f"strokeColor={COL['container_border']};strokeWidth=2;fontColor=#FFFFFF;align=center;"
                 f"verticalAlign=middle;fontSize=12;")
        return self._element("container_instance", name, f"Container: {tech}", desc, x, y, w, h, style,
                             "#FFFFFF", tech=tech, legend_key="container")

    def infra_node(self, x, y, name, tech, desc, w=240, h=90):
        style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=8;fillColor=#FFFFFF;strokeColor={COL['boundary']};"
                 f"strokeWidth=2;dashed=1;dashPattern=4 3;fontColor={COL['ink']};align=center;"
                 f"verticalAlign=middle;fontSize=12;")
        return self._element("infra_node", name, f"Infrastructure Node: {tech}", desc, x, y, w, h, style,
                             COL["ink"], tech=tech)

    # --- relações ----------------------------------------------------------------
    def rel(self, src, dst, label, tech=None, asynchronous=False, src_side="r", dst_side="l",
            via=None, step=None, src_at=None, dst_at=None):
        """Seta UNIDIRECIONAL de src para dst. `label` descreve a intenção (evite 'Usa');
        `tech` é o protocolo/tecnologia (obrigatório entre contêineres/componentes);
        `step` numera a ordem (diagramas dinâmicos). `src_at`/`dst_at` = (fx, fy) em frações
        0..1 do retângulo, para sair/entrar fora do centro do lado (evita setas sobrepostas)."""
        for ref in (src, dst):
            if ref not in self.elements:
                raise ValueError(f"id inexistente: {ref}")
        text = f"{step}. {label}" if step is not None else label
        value = f'<div style="font-size:11px"><b>{html.escape(text)}</b>'
        if tech:
            value += f'<br>[{html.escape(tech)}]'
        value += "</div>"
        ex, ey = src_at or SIDES[src_side]
        tx, ty = dst_at or SIDES[dst_side]
        dash = f"dashed=1;dashPattern=6 4;strokeWidth=2;" if asynchronous else "strokeWidth=2;"
        eid = self._id("rl")
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in (via or []))
        wp = f'<Array as="points">{pts}</Array>' if pts else ""
        self.cells.append(
            f'<mxCell id="{eid}" value="{_esc(value)}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;'
            f'endArrow=blockThin;endFill=1;{dash}strokeColor={COL["edge"]};fontColor={COL["ink"]};'
            f'labelBackgroundColor=#FFFFFF;fontSize=11;exitX={ex};exitY={ey};exitDx=0;exitDy=0;'
            f'entryX={tx};entryY={ty};entryDx=0;entryDy=0;" edge="1" parent="1" source="{src}" target="{dst}">'
            f'<mxGeometry relative="1" as="geometry">{wp}</mxGeometry></mxCell>')
        self.edges.append(dict(id=eid, src=src, dst=dst, label=label, tech=tech, step=step,
                               src_side=src_side, dst_side=dst_side, direct=not (via or src_at or dst_at)))
        self._used_edge_styles.add("async" if asynchronous else "sync")
        return eid

    # --- verificação e saída -------------------------------------------------------
    def lint(self):
        errs = []
        if not self.title or self.scope.lower() not in self.title.lower():
            errs.append("título deve descrever tipo e escopo do diagrama")
        for vid, e in self.elements.items():
            if e["kind"] not in ALLOWED[self.level]:
                errs.append(f"{e['name']}: elemento '{e['kind']}' não pertence a um diagrama '{self.level}' "
                            "(misturar níveis de abstração)")
            if not e["name"].strip():
                errs.append(f"elemento {vid} sem nome")
            if not (e["desc"] or "").strip():
                errs.append(f"{e['name']}: falta descrição curta de responsabilidade")
            if e["kind"] in ("container", "component", "container_instance", "infra_node", "node") \
                    and not (e["tech"] or "").strip():
                errs.append(f"{e['name']}: falta tecnologia explícita")
        for r in self.edges:
            if not (r["label"] or "").strip():
                errs.append(f"seta {r['src']}->{r['dst']} sem rótulo")
            elif r["label"].strip().lower() in VAGUE_LABELS:
                errs.append(f"seta '{r['label']}' é vaga; descreva a intenção (ex.: 'Lê pedidos de')")
            kinds = {self.elements[r["src"]]["kind"], self.elements[r["dst"]]["kind"]}
            if kinds <= {"container", "component", "container_instance", "boundary_system",
                         "boundary_container"} and not (r["tech"] or "").strip() and self.level != "deployment":
                errs.append(f"seta '{r['label']}' entre contêineres/componentes sem tecnologia/protocolo")
            if r["direct"]:
                gap = self._gap(r)
                need = self._label_need(r)
                if gap is not None and gap < need:
                    errs.append(f"seta '{r['label']}': rótulo precisa de ~{need}px entre os elementos e há "
                                f"{gap}px; aumente o espaçamento ou use via/src_at")
            if self.level == "dynamic" and r["step"] is None:
                errs.append(f"seta '{r['label']}' em diagrama dinâmico sem número de ordem")
        return errs

    def _gap(self, r):
        sx, sy, sw, sh = self.elements[r["src"]]["box"]
        dx, dy, dw, dh = self.elements[r["dst"]]["box"]
        pair = (r["src_side"], r["dst_side"])
        if pair == ("r", "l"):
            return dx - (sx + sw)
        if pair == ("l", "r"):
            return sx - (dx + dw)
        if pair == ("b", "t"):
            return dy - (sy + sh)
        if pair == ("t", "b"):
            return sy - (dy + dh)
        return None

    @staticmethod
    def _label_need(r):
        text = f"{r['step']}. {r['label']}" if r["step"] is not None else r["label"]
        wide = max(len(text) * 6.6, (len(r["tech"]) + 2) * 6.0 if r["tech"] else 0) + 24
        horizontal = (r["src_side"], r["dst_side"]) in (("r", "l"), ("l", "r"))
        return int(wide) if horizontal else 70

    def _legend(self):
        w, row = 360, 26
        items = []
        names = {"person": ("Person", COL["person"], False),
                 "person_external": ("External person", COL["person_external"], True),
                 "system": ("Software System (em escopo)", COL["system"], False),
                 "external_system": ("External Software System", COL["system_external"], True),
                 "container": ("Container", COL["container"], False),
                 "component": ("Component", COL["component"], False),
                 "node": ("Deployment Node", COL["node_fill"], False),
                 "infra_node": ("Infrastructure Node", "#FFFFFF", True)}
        for k in ["person", "person_external", "system", "external_system", "container", "component",
                  "node", "infra_node"]:
            if k in self._used_kinds:
                items.append(("box", k) + names[k][:1] + (names[k][1], names[k][2]))
        if "boundary" in self._used_kinds:
            items.append(("boundary", "boundary", "Boundary (fronteira do sistema/contêiner)", "", True))
        if "sync" in self._used_edge_styles:
            items.append(("line", "sync", "Relação síncrona (seta cheia, aponta para quem é chamado)", "", False))
        if "async" in self._used_edge_styles:
            items.append(("line", "async", "Relação assíncrona (seta tracejada)", "", True))
        h = 40 + row * (len(items) + 1)
        max_x = max((b[0] + b[2] for b in (e["box"] for e in self.elements.values())), default=0)
        max_y = max((b[1] + b[3] for b in (e["box"] for e in self.elements.values())), default=0)
        x, y = 30, max_y + 50
        self.width = max(self.width, max_x + 40, x + w + 30)
        self.height = y + h + 30
        self._vertex("lgbox", _esc("<b>Legenda</b>"),
                     f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={COL['boundary']};"
                     f"align=left;verticalAlign=top;spacingLeft=10;spacingTop=4;fontSize=12;"
                     f"fontColor={COL['ink']};", x, y, w, h)
        for i, (shape, key, text, fill, dashed) in enumerate(items):
            ly = y + 40 + row * i
            if shape == "line":
                dash = "dashed=1;dashPattern=6 4;" if dashed else ""
                self.cells.append(
                    f'<mxCell id="lgl{i}" value="" style="endArrow=blockThin;endFill=1;html=1;{dash}strokeWidth=2;'
                    f'strokeColor={COL["edge"]};" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                    f'<mxPoint x="{x + 12}" y="{ly + 10}" as="sourcePoint"/>'
                    f'<mxPoint x="{x + 52}" y="{ly + 10}" as="targetPoint"/></mxGeometry></mxCell>')
            else:
                dash = "dashed=1;dashPattern=6 4;" if dashed else ""
                bg = "none" if shape == "boundary" else fill
                stroke = COL["boundary"] if shape == "boundary" or key in ("infra_node", "node") else (
                    COL["system_external_border"] if key in ("external_system", "person_external") else fill)
                self._vertex(f"lgs{i}", "", f"rounded=1;html=1;fillColor={bg};strokeColor={stroke};"
                             f"strokeWidth=2;{dash}", x + 12, y + 44 + row * i - 4, 40, 18)
            self._vertex(f"lgt{i}", _esc(text),
                         f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=11;"
                         f"fontColor={COL['ink']};", x + 60, y + 36 + row * i, w - 68, row - 2)
        self._vertex("lgn", _esc("Setas unidirecionais: o rótulo descreve a intenção; [colchetes] = tecnologia."),
                     f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=10;"
                     f"fontColor={COL['muted']};", x + 12, y + 36 + row * len(items), w - 20, row)

    def to_drawio(self):
        title = _esc(f'<b style="font-size:18px">{html.escape(self.title)}</b>')
        head = [f'<mxCell id="ttl" value="{title}" style="text;html=1;whiteSpace=wrap;align=left;'
                f'verticalAlign=middle;fontColor={COL["ink"]};" vertex="1" parent="1">'
                f'<mxGeometry x="30" y="14" width="{self.width - 60}" height="36" as="geometry"/></mxCell>']
        legend_start = len(self.cells)
        self._legend()
        legend_cells = self.cells[legend_start:]
        del self.cells[legend_start:]
        body = head + self.cells + legend_cells
        return ('<mxfile host="app.diagrams.net"><diagram name="%s" id="d1"><mxGraphModel dx="1200" dy="800" '
                'grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
                'pageScale="1" pageWidth="%d" pageHeight="%d" math="0" shadow="0"><root><mxCell id="0"/>'
                '<mxCell id="1" parent="0"/>%s</root></mxGraphModel></diagram></mxfile>'
                % (_esc(self.title), self.width, self.height, "".join(body)))

    def save(self, path):
        errs = self.lint()
        if errs:
            raise ValueError("diagrama viola a notação C4:\n - " + "\n - ".join(errs))
        xml = self.to_drawio()
        ET.fromstring(xml)
        Path(path).write_text(xml, encoding="utf-8")
        return str(path)
