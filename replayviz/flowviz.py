from typing import Dict, List, Optional, Tuple
from pm4py.objects.petri_net.obj import PetriNet, Marking
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge

# Subtitles (descriptions) under each transition. External callers may
# provide their own mapping; this serves only as a default example.
DEFAULT_TRANS_DESCR: Dict[str, str] = {
    "a": "register\nrequest",
    "c": "examine\ncasually",
    "d": "check\nticket",
    "e": "decide",
    "h": "reject\nrequest",
}

def _token_html(k: int, max_dots: int = 6) -> str:
    if k <= 0: return ""
    if k <= max_dots:
        return "<span>" + ("&bull; " * k).strip() + "</span>"
    return "<span>" + ("&bull; " * max_dots).strip() + f" <strong>+{k-max_dots}</strong></span>"

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

def _trans_style(highlighted: bool = False) -> dict:
    border = "#111827"; bg = "#ffffff"
    if highlighted: border, bg = "#ef4444", "#fee2e2"
    return {
        "border": f"2px solid {border}",
        "borderRadius": "4px",
        "width": 34, "height": 34,
        "display": "flex", "alignItems": "center", "justifyContent": "center",
        "background": bg, "color": "#111827", "fontWeight": 700,
        "boxShadow": "0 0 0 0",
    }

def _label_under(text: str) -> str:
    # dois níveis: id (negrito) em cima, descrição pequena em baixo (quebra de linha com <br/>)
    tx = text.replace("\n", "<br/>")
    return f"<div style='text-align:center;font-size:12px;line-height:14px;color:#111827'>{tx}</div>"

def default_layout() -> Dict[str, Tuple[int, int]]:
    """Example coordinates for a simple Petri net (in pixels)."""
    return {
        # y=60 (middle line), y=20 (top), y=100 (bottom)
        "p_start": (0, 60),
        "a": (80, 60),
        "p1": (160, 20),
        "p2": (160, 100),
        "c": (240, 20),
        "d": (240, 100),
        "p3": (320, 20),
        "p4": (320, 100),
        "e": (420, 60),
        "p5": (500, 60),
        "h": (580, 60),
        "p_end": (660, 60),
    }

def build_nodes_edges_for_marking(
    net: PetriNet,
    marking: Marking,
    fired_transition_name: Optional[str],
    prev_marking: Optional[Marking] = None,
    layout: Dict[str, Tuple[int, int]] | None = None,
    trans_descr: Dict[str, str] | None = None,
) -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    layout = layout or {}
    trans_descr = trans_descr or {}

    consumed, produced = {}, {}
    if prev_marking is not None:
        for p in net.places:
            name = p.name
            k_prev = prev_marking.get(p, 0)
            k_now = marking.get(p, 0)
            consumed[name] = k_now < k_prev
            produced[name] = k_now > k_prev

    nodes: List[StreamlitFlowNode] = []
    for p in net.places:
        name = p.name
        pos = layout.get(name, (0, 0))
        k = marking.get(p, 0)
        nodes.append(
            StreamlitFlowNode(
                id=name,
                pos=pos,
                data={"content": _token_html(k)},
                node_type="default",
                source_position="right",
                target_position="left",
                style=_place_style(k, consumed=consumed.get(name, False), produced=produced.get(name, False)),
            )
        )

    for t in net.transitions:
        name = t.name
        pos = layout.get(name, (0, 0))
        hl = fired_transition_name == name
        nodes.append(
            StreamlitFlowNode(
                id=name,
                pos=pos,
                data={"content": f"<div><b>{name}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=_trans_style(highlighted=hl),
            )
        )
        nodes.append(
            StreamlitFlowNode(
                id=f"{name}_lbl",
                pos=(pos[0], pos[1] + 40),
                data={"content": _label_under(trans_descr.get(t.label or name, t.label or name))},
                node_type="default",
                source_position="right",
                target_position="left",
                style={"border": "0", "background": "transparent", "width": 120, "height": 30},
            )
        )

    edges: List[StreamlitFlowEdge] = []
    for arc in net.arcs:
        src = arc.source.name
        dst = arc.target.name
        edges.append(
            StreamlitFlowEdge(
                id=f"e_{src}_{dst}",
                source=src,
                target=dst,
                label="",
                animated=False,
            )
        )
    return nodes, edges

# Build a static representation of a net using given layout and labels

def build_normative_flow(
    net: PetriNet,
    layout: Dict[str, Tuple[int, int]],
    trans_descr: Dict[str, str],
) -> Tuple[List[StreamlitFlowNode], List[StreamlitFlowEdge]]:
    nodes: List[StreamlitFlowNode] = []
    edges: List[StreamlitFlowEdge] = []

    for p in net.places:
        name = p.name
        if name in layout:
            nodes.append(
                StreamlitFlowNode(
                    id=f"norm_{name}",
                    pos=layout[name],
                    data={"content": ""},
                    node_type="default",
                    source_position="right",
                    target_position="left",
                    style={"border": "2px solid #6b7280", "borderRadius": "9999px", "width": 28, "height": 28, "background": "#fff"},
                )
            )

    for t in net.transitions:
        name = t.name
        if name in layout:
            nodes.append(
                StreamlitFlowNode(
                    id=f"norm_{name}",
                    pos=layout[name],
                    data={"content": f"<div><b>{name}</b></div>"},
                    node_type="default",
                    source_position="right",
                    target_position="left",
                    style={"border": "2px solid #111827", "borderRadius": "4px", "width": 34, "height": 34, "background": "#fff", "fontWeight": 700},
                )
            )
            nodes.append(
                StreamlitFlowNode(
                    id=f"norm_{name}_lbl",
                    pos=(layout[name][0], layout[name][1] + 40),
                    data={"content": _label_under(trans_descr.get(t.label or name, t.label or name))},
                    node_type="default",
                    source_position="right",
                    target_position="left",
                    style={"border": "0", "background": "transparent", "width": 120, "height": 30},
                )
            )

    for arc in net.arcs:
        src = arc.source.name
        dst = arc.target.name
        if src in layout and dst in layout:
            edges.append(
                StreamlitFlowEdge(
                    id=f"ne_{src}_{dst}",
                    source=f"norm_{src}",
                    target=f"norm_{dst}",
                    label="",
                    animated=False,
                )
            )
    return nodes, edges
