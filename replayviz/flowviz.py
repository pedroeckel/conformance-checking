from typing import Dict, List, Optional, Tuple
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.log.obj import Trace
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
import re
import networkx as nx

def _token_html(k: int, max_dots: int = 6) -> str:
    if k <= 0:
        return ""
    if k <= max_dots:
        return "<span>" + ("&bull; " * k).strip() + "</span>"
    return "<span>" + ("&bull; " * max_dots).strip() + f" <strong>+{k - max_dots}</strong></span>"

def _place_style(tokens: int, consumed=False, produced=False) -> dict:
    border = "#6b7280"; bg = "#ffffff"
    if consumed: border, bg = "#ef4444", "#fee2e2"
    if produced: border, bg = "#10b981", "#ecfdf5"
    return {
        "border": f"2px solid {border}",
        "borderRadius": "9999px",
        "width": 28, "height": 28,
        "display": "flex", "alignItems": "center", "justifyContent": "center",
        "background": bg, "color": "#111827", "fontSize": "12px",
        "lineHeight": "12px", "padding": "2px",
    }

def _calc_text_box(text: str, char_w: int = 8, padding: int = 12, min_w: int = 34) -> int:
    """Estimate a box width (in px) from its text content."""
    lines = text.split("\n")
    content_w = max(len(line) for line in lines) * char_w + padding
    return max(min_w, content_w)


def _trans_style(name: str, highlighted: bool = False) -> dict:
    border = "#111827"
    bg = "#ffffff"
    if highlighted:
        border, bg = "#ef4444", "#fee2e2"
    width = _calc_text_box(name)
    return {
        "border": f"2px solid {border}",
        "borderRadius": "4px",
        "width": width,
        "height": 34,
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "background": bg,
        "color": "#111827",
        "fontWeight": 700,
        "boxShadow": "0 0 0 0",
        "padding": "0 4px",
    }

def _label_under(text: str) -> Tuple[str, int, int]:
    """HTML for a small label under a transition plus its preferred size."""
    lines = text.split("\n")
    tx = "<br/>".join(lines)
    width = _calc_text_box(text, char_w=6, padding=6, min_w=0)
    height = max(14 * len(lines), 14)
    html = (
        f"<div style='text-align:center;font-size:12px;line-height:14px;color:#111827'>{tx}</div>"
    )
    return html, width, height


def _auto_layout(nodes: Dict[str, StreamlitFlowNode], edges: List[StreamlitFlowEdge]) -> None:
    """Atribui coordenadas usando um layout de força do NetworkX."""
    G = nx.DiGraph()
    for nid in nodes:
        G.add_node(nid)
    for e in edges:
        G.add_edge(e.source, e.target)

    fixed_pos: Dict[str, Tuple[float, float]] = {}
    fixed_nodes: List[str] = []
    if "p_start" in nodes:
        fixed_pos["p_start"] = (-1.5, 0.0)
        fixed_nodes.append("p_start")
    if "p_end" in nodes:
        fixed_pos["p_end"] = (1.5, 0.0)
        fixed_nodes.append("p_end")

    if fixed_nodes:
        pos = nx.spring_layout(G, seed=42, pos=fixed_pos, fixed=fixed_nodes)
    else:
        pos = nx.spring_layout(G, seed=42)

    scale = 220
    for nid, (x, y) in pos.items():
        nodes[nid].pos = (float(x * scale), float(-y * scale))

    # curvas para arestas que apontam para trás
    for e in edges:
        sx, _ = nodes[e.source].pos
        tx, _ = nodes[e.target].pos
        if sx > tx:
            e.type = "smoothstep"

def _layout_coords():
    """
    Coordenadas fixas para N₃ (em px), para bater com a estética do diagrama:
    linha superior:  p_start — a — p1 — c — p3 ——\
                                             \     e — p5 — h — p_end
    linha inferior:              p2 — d — p4 ——/
    """
    return {
        # y=60 (linha média), y=20 (topo), y=100 (baixo)
        "p_start": (  0, 60),
        "a":       ( 80, 60),
        "p1":      (160, 20),
        "p2":      (160,100),
        "c":       (240, 20),
        "d":       (240,100),
        "p3":      (320, 20),
        "p4":      (320,100),
        "e":       (420, 60),
        "p5":      (500, 60),
        "h":       (580, 60),
        "p_end":   (660, 60),
    }

def build_nodes_edges_for_marking_N3(
    net: PetriNet,
    places: Dict[str, PetriNet.Place],
    trans: Dict[str, PetriNet.Transition],
    marking: Marking,
    fired_transition_name: Optional[str],
    prev_marking: Optional[Marking] = None,
) -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    pos = _layout_coords()

    # consumo/produção
    consumed, produced = {}, {}
    if prev_marking is not None:
        for name, p in places.items():
            k_prev = prev_marking.get(p, 0)
            k_now  = marking.get(p, 0)
            consumed[name] = (k_now < k_prev)
            produced[name] = (k_now > k_prev)

    nodes: List[StreamlitFlowNode] = []

    # places (círculos pequenos) com bolinhas
    for pname in ["p_start","p1","p2","p3","p4","p5","p_end"]:
        p = places[pname]; k = marking.get(p, 0)
        nodes.append(
            StreamlitFlowNode(
                id=pname,
                pos=pos[pname],
                data={"content": _token_html(k)},
                node_type="default",
                source_position="right", target_position="left",
                style=_place_style(k, consumed=consumed.get(pname, False), produced=produced.get(pname, False))
            )
        )

    # transitions (caixinhas) + rótulo inferior igual à figura
    for tname in ["a", "c", "d", "e", "h"]:
        hl = (fired_transition_name == tname)
        t_style = _trans_style(tname, highlighted=hl)
        nodes.append(
            StreamlitFlowNode(
                id=tname,
                pos=pos[tname],
                data={"content": f"<div><b>{tname}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=t_style,
            )
        )

    # edges conforme N₃
    edges: List[StreamlitFlowEdge] = []
    def E(src, dst):
        edges.append(StreamlitFlowEdge(id=f"e_{src}_{dst}", source=src, target=dst, label="", animated=False))

    E("p_start","a"); E("a","p1"); E("a","p2")
    E("p1","c"); E("c","p3")
    E("p2","d"); E("d","p4")
    E("p3","e"); E("p4","e")
    E("e","p5"); E("p5","h"); E("h","p_end")

    return nodes, edges

# Modelo normativo equivalente (mesmo layout e rótulos “humanos”)
def build_normative_flow_N3() -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    pos = _layout_coords()
    nodes: List[StreamlitFlowNode] = []
    edges: List[StreamlitFlowEdge] = []

    def add_circle(pid):
        nodes.append(StreamlitFlowNode(
            id=f"norm_{pid}", pos=pos[pid], data={"content": ""}, node_type="default",
            source_position="right", target_position="left",
            style={"border":"2px solid #6b7280","borderRadius":"9999px","width":28,"height":28,"background":"#fff"}
        ))

    def add_box(tid):
        t_style = _trans_style(tid, highlighted=False)
        nodes.append(
            StreamlitFlowNode(
                id=f"norm_{tid}",
                pos=pos[tid],
                data={"content": f"<div><b>{tid}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=t_style,
            )
        )
        

    for pid in ["p_start","p1","p2","p3","p4","p5","p_end"]: add_circle(pid)
    for tid in ["a","c","d","e","h"]: add_box(tid)

    def E(src,dst):
        edges.append(StreamlitFlowEdge(id=f"ne_{src}_{dst}", source=f"norm_{src}", target=f"norm_{dst}", label="", animated=False))
    E("p_start","a"); E("a","p1"); E("a","p2")
    E("p1","c"); E("c","p3")
    E("p2","d"); E("d","p4")
    E("p3","e"); E("p4","e")
    E("e","p5"); E("p5","h"); E("h","p_end")

    return nodes, edges


def build_trace_flow(trace: Trace) -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    """Traço sequencial em estilo rede de Petri (lugares únicos)."""
    nodes: Dict[str, StreamlitFlowNode] = {}
    edges: List[StreamlitFlowEdge] = []
    order: Dict[str, int] = {}

    circle_style = {
        "border": "2px solid #6b7280",
        "borderRadius": "9999px",
        "width": 28,
        "height": 28,
        "background": "#fff",
    }

    nodes["p_start"] = StreamlitFlowNode(
        id="p_start",
        pos=(0, 0),
        data={"content": ""},
        node_type="default",
        source_position="right",
        target_position="left",
        style=circle_style,
    )
    order["p_start"] = 0
    idx = 1

    curr_place = "p_start"
    edge_idx = 0
    trans_nodes: Dict[str, str] = {}
    place_after: Dict[str, str] = {}

    for ev in trace:
        name = ev.get("concept:name", "?")
        slug = re.sub(r"[^0-9a-zA-Z_]+", "_", name)

        t_id = trans_nodes.setdefault(name, f"t_{slug}")
        if t_id not in nodes:
            nodes[t_id] = StreamlitFlowNode(
                id=t_id,
                pos=(0, 0),
                data={"content": f"<div><b>{name}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=_trans_style(name, highlighted=False),
            )
            order.setdefault(t_id, idx); idx += 1

        p_id = place_after.setdefault(name, f"p_{slug}")
        if p_id not in nodes:
            nodes[p_id] = StreamlitFlowNode(
                id=p_id,
                pos=(0, 0),
                data={"content": ""},
                node_type="default",
                source_position="right",
                target_position="left",
                style=circle_style,
            )
            order.setdefault(p_id, idx); idx += 1

        edges.append(StreamlitFlowEdge(id=f"e_{edge_idx}", source=curr_place, target=t_id, label="", animated=False))
        edge_idx += 1
        edges.append(StreamlitFlowEdge(id=f"e_{edge_idx}", source=t_id, target=p_id, label="", animated=False))
        edge_idx += 1
        curr_place = p_id

    nodes["p_end"] = StreamlitFlowNode(
        id="p_end",
        pos=(0, 0),
        data={"content": ""},
        node_type="default",
        source_position="right",
        target_position="left",
        style=circle_style,
    )
    order.setdefault("p_end", idx)
    edges.append(StreamlitFlowEdge(id=f"e_{edge_idx}", source=curr_place, target="p_end", label="", animated=False))

    spacing = 120
    for nid, node in nodes.items():
        x = order.get(nid, 0) * spacing
        y = 0.0 if nid.startswith("t") else 80.0
        node.pos = (float(x), float(y))

    for e in edges:
        sx = nodes[e.source].pos[0]
        tx = nodes[e.target].pos[0]
        if sx >= tx:
            e.type = "smoothstep"

    return list(nodes.values()), edges


def build_trace_replay_flow(
    trace: Trace,
    step: int,
    fired_event_label: Optional[str] = None,
) -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    """Fluxo do traço com marcação (1 token) no passo informado."""
    circle_style = {
        "border": "2px solid #6b7280",
        "borderRadius": "9999px",
        "width": 28,
        "height": 28,
        "background": "#fff",
    }

    nodes: Dict[str, StreamlitFlowNode] = {}
    edges: List[StreamlitFlowEdge] = []
    order: Dict[str, int] = {}

    nodes["p_start"] = StreamlitFlowNode(
        id="p_start",
        pos=(0, 0),
        data={"content": ""},
        node_type="default",
        source_position="right",
        target_position="left",
        style=circle_style,
    )
    order["p_start"] = 0

    trans_nodes: Dict[str, str] = {}
    place_after: Dict[str, str] = {}
    place_seq: List[str] = ["p_start"]
    trans_seq: List[str] = []

    curr_place = "p_start"
    edge_idx = 0
    idx = 1

    for ev in trace:
        name = ev.get("concept:name", "?")
        slug = re.sub(r"[^0-9a-zA-Z_]+", "_", name)

        t_id = trans_nodes.setdefault(name, f"t_{slug}")
        if t_id not in nodes:
            nodes[t_id] = StreamlitFlowNode(
                id=t_id,
                pos=(0, 0),
                data={"content": f"<div><b>{name}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=_trans_style(name, highlighted=False),
            )
            order.setdefault(t_id, idx); idx += 1

        p_id = place_after.setdefault(name, f"p_{slug}")
        if p_id not in nodes:
            nodes[p_id] = StreamlitFlowNode(
                id=p_id,
                pos=(0, 0),
                data={"content": ""},
                node_type="default",
                source_position="right",
                target_position="left",
                style=circle_style,
            )
            order.setdefault(p_id, idx); idx += 1

        edges.append(StreamlitFlowEdge(id=f"e_{edge_idx}", source=curr_place, target=t_id, label="", animated=False))
        edge_idx += 1
        edges.append(StreamlitFlowEdge(id=f"e_{edge_idx}", source=t_id, target=p_id, label="", animated=False))
        edge_idx += 1

        curr_place = p_id
        place_seq.append(p_id)
        trans_seq.append(t_id)

    nodes["p_end"] = StreamlitFlowNode(
        id="p_end",
        pos=(0, 0),
        data={"content": ""},
        node_type="default",
        source_position="right",
        target_position="left",
        style=circle_style,
    )
    order.setdefault("p_end", idx)
    edges.append(
        StreamlitFlowEdge(
            id=f"e_{edge_idx}",
            source=curr_place,
            target="p_end",
            label="",
            animated=False,
        )
    )
    place_seq.append("p_end")

    spacing = 120
    for nid, node in nodes.items():
        x = order.get(nid, 0) * spacing
        y = 0.0 if nid.startswith("t") else 80.0
        node.pos = (float(x), float(y))

    for e in edges:
        sx = nodes[e.source].pos[0]
        tx = nodes[e.target].pos[0]
        if sx >= tx:
            e.type = "smoothstep"

    # determina token e destaques
    step = max(0, min(step, len(place_seq) - 1))
    curr_place_id = place_seq[step]
    prev_place_id = place_seq[step - 1] if step > 0 else None
    fired_label = fired_event_label
    if fired_label is None and step > 0 and step - 1 < len(trace):
        fired_label = trace[step - 1].get("concept:name")

    for pid, node in nodes.items():
        if pid.startswith("p_"):
            tokens = 1 if pid == curr_place_id else 0
            consumed = pid == prev_place_id
            produced = pid == curr_place_id and step > 0
            node.data = {"content": _token_html(tokens)}
            node.style = _place_style(tokens, consumed=consumed, produced=produced)

    for name, t_id in trans_nodes.items():
        node = nodes[t_id]
        highlight = (name == fired_label)
        node.style = _trans_style(name, highlighted=highlight)

    return list(nodes.values()), edges


