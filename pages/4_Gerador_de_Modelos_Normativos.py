# -*- coding: utf-8 -*-
import json
import streamlit as st
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from replayviz import ensure_flow_state_slot, update_flow_state_slot, render_flow_slot

st.set_page_config(page_title="Gerador de Modelo Normativo", layout="wide")
st.title("Gerador de Modelo Normativo")

# espaço em session_state para o fluxo
slot_name = "norm_builder"
ensure_flow_state_slot(slot_name)
slot = st.session_state[slot_name]
try:
    has_nodes = bool(slot.nodes)
except AttributeError:
    has_nodes = bool(slot["nodes"])

# estado inicial com sequência a->c->d->e->h
if not has_nodes:
    labels = ["a", "c", "d", "e", "h"]
    nodes = []
    edges = []
    for i, label in enumerate(labels):
        nodes.append(
            StreamlitFlowNode(
                id=f"n{i}",
                pos=(i * 120.0, 0.0),
                data={"content": f"<div><b>{label}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
            )
        )
    for i in range(len(labels) - 1):
        edges.append(
            StreamlitFlowEdge(
                id=f"e_{i}",
                source=f"n{i}",
                target=f"n{i+1}",
                label="",
            )
        )
    update_flow_state_slot(slot_name, nodes, edges)

# componente streamlit_flow interativo
render_flow_slot(slot_name, key="norm_builder", height=400, fit_view=True)

# exporta o modelo como JSON para reutilização
slot = st.session_state[slot_name]
try:
    nodes = [n.__dict__ for n in slot.nodes]
    edges = [e.__dict__ for e in slot.edges]
except AttributeError:
    nodes = slot["nodes"]
    edges = slot["edges"]

export_obj = {"nodes": nodes, "edges": edges}
export_json = json.dumps(export_obj, ensure_ascii=False, indent=2)
st.download_button(
    "Exportar modelo", export_json, file_name="modelo_normativo.json", mime="application/json"
)
