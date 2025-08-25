from typing import List
from streamlit import session_state as st_ss
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge


def ensure_flow_state_slot(slot: str) -> None:
    if slot not in st_ss:
        try:
            from streamlit_flow.state import StreamlitFlowState
            st_ss[slot] = StreamlitFlowState(nodes=[], edges=[])
        except Exception:
            st_ss[slot] = {"nodes": [], "edges": []}

def update_flow_state_slot(slot: str, nodes: List[StreamlitFlowNode], edges: List[StreamlitFlowEdge]) -> None:
    fs = st_ss[slot]
    try:
        fs.nodes = nodes; fs.edges = edges
    except AttributeError:
        fs["nodes"] = nodes; fs["edges"] = edges

def render_flow_slot(slot: str, key: str, height: int = 400, fit_view: bool = True) -> None:
    """
    Chama streamlit_flow com a menor assinatura comum entre versões,
    sem impor layout do frontend (usa as posições `pos` vindas do Python).
    """
    state_obj = st_ss[slot]
    # 1) API nova (com 'state')
    try:
        new_state = streamlit_flow(key=key, state=state_obj, fit_view=fit_view, height=height)
        if new_state is not None:
            st_ss[slot] = new_state
        return
    except TypeError:
        pass

    # 2) Fallback: API antiga (com 'nodes'/'edges')
    try:
        nodes = state_obj.nodes; edges = state_obj.edges  # type: ignore[attr-defined]
    except AttributeError:
        nodes = state_obj["nodes"]; edges = state_obj["edges"]
    streamlit_flow(key=key, nodes=nodes, edges=edges, fit_view=fit_view, height=height)
