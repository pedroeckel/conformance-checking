from typing import List
from streamlit import session_state as st_ss
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge

def ensure_flow_state_slot(slot: str) -> None:
    if slot not in st_ss:
        # Compat com diferentes versões do streamlit_flow
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
    try:
        new_state = streamlit_flow(key=key, state=st_ss[slot], fit_view=fit_view, height=height)
        if new_state is not None:
            st_ss[slot] = new_state
    except TypeError:
        state_obj = st_ss[slot]
        try:
            nodes = state_obj.nodes; edges = state_obj.edges
        except AttributeError:
            nodes = state_obj["nodes"]; edges = state_obj["edges"]
        streamlit_flow(key=key, nodes=nodes, edges=edges, fit_view=fit_view, height=height)
