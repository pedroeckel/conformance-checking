from typing import Dict, List, Optional, Tuple
from pm4py.objects.petri_net.obj import PetriNet, Marking
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge

# Subtítulos (descrições) sob cada transição, como na figura
TRANS_DESCR = {
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
    for tname in ["a","c","d","e","h"]:
        t = trans[tname]; hl = (fired_transition_name == tname)
        nodes.append(
            StreamlitFlowNode(
                id=tname, pos=pos[tname],
                data={"content": f"<div><b>{tname}</b></div>"},
                node_type="default", source_position="right", target_position="left",
                style=_trans_style(highlighted=hl)
            )
        )
        # label embaixo
        nodes.append(
            StreamlitFlowNode(
                id=f"{tname}_lbl",
                pos=(pos[tname][0], pos[tname][1] + 40),  # logo abaixo
                data={"content": _label_under(TRANS_DESCR.get(tname, tname))},
                node_type="default", source_position="right", target_position="left",
                style={"border":"0","background":"transparent","width":120,"height":30}
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
        nodes.append(StreamlitFlowNode(
            id=f"norm_{tid}", pos=pos[tid], data={"content": f"<div><b>{tid}</b></div>"},
            node_type="default", source_position="right", target_position="left",
            style={"border":"2px solid #111827","borderRadius":"4px","width":34,"height":34,"background":"#fff","fontWeight":700}
        ))
        nodes.append(StreamlitFlowNode(
            id=f"norm_{tid}_lbl",
            pos=(pos[tid][0], pos[tid][1] + 40),
            data={"content": _label_under(TRANS_DESCR.get(tid, tid))},
            node_type="default", source_position="right", target_position="left",
            style={"border":"0","background":"transparent","width":120,"height":30}
        ))

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
