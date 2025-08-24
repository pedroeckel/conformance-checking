# -*- coding: utf-8 -*-
"""Página para edição e exportação de modelos normativos."""

import json
import streamlit as st
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge

from replayviz import ensure_flow_state_slot, update_flow_state_slot, render_flow_slot

st.set_page_config(page_title="Gerador de Modelo Normativo", layout="wide")
st.title("Gerador de Modelo Normativo")

# Espaço de sessão onde o fluxo será guardado
STATE_SLOT = "norm_model_builder"
ensure_flow_state_slot(STATE_SLOT)

# Constantes de layout
NODE_SPACING = 120
Y_POS = 80

# Modelo padrão: sequência a → c → d → e → h
default_sequence = ["a", "c", "d", "e", "h"]
fs = st.session_state[STATE_SLOT]
try:
    has_nodes = bool(fs.nodes)  # type: ignore[attr-defined]
except AttributeError:
    has_nodes = bool(fs["nodes"])

if not has_nodes:
    nodes = []
    edges = []
    for i, label in enumerate(default_sequence):
        nodes.append(
            StreamlitFlowNode(
                id=label,
                pos=(i * NODE_SPACING, Y_POS),
                data={"content": f"<div><b>{label}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
            )
        )

    for src, dst in zip(default_sequence[:-1], default_sequence[1:]):
        edges.append(
            StreamlitFlowEdge(
                id=f"e_{src}_{dst}", source=src, target=dst, label="",
            )
        )

    update_flow_state_slot(STATE_SLOT, nodes, edges)

# Adiciona novos quadrantes
new_label = st.text_input("Nome do novo quadrante", key="new_node_label")
if st.button("Adicionar quadrante") and new_label:
    fs = st.session_state[STATE_SLOT]
    try:
        nodes = fs.nodes; edges = fs.edges  # type: ignore[attr-defined]
    except AttributeError:
        nodes = fs["nodes"]; edges = fs["edges"]

    existing_ids = [getattr(n, "id", n.get("id")) for n in nodes]
    if new_label not in existing_ids:
        try:
            last_x = max(n.pos[0] for n in nodes)
            y = nodes[0].pos[1]
            prev_id = nodes[-1].id
        except AttributeError:
            last_x = max(n["position"]["x"] for n in nodes)
            y = nodes[0]["position"]["y"]
            prev_id = nodes[-1]["id"]

        x = last_x + NODE_SPACING
        nodes.append(
            StreamlitFlowNode(
                id=new_label,
                pos=(x, y),
                data={"content": f"<div><b>{new_label}</b></div>"},
                node_type="default",
                source_position="right",
                target_position="left",
            )
        )
        edges.append(
            StreamlitFlowEdge(
                id=f"e_{prev_id}_{new_label}", source=prev_id, target=new_label, label="",
            )
        )
        update_flow_state_slot(STATE_SLOT, nodes, edges)

# Renderiza o editor de fluxo
render_flow_slot(STATE_SLOT, key="norm_builder", height=400, fit_view=True)

# Exporta para JSON
fs = st.session_state[STATE_SLOT]
try:
    nodes = fs.nodes; edges = fs.edges  # type: ignore[attr-defined]
except AttributeError:
    nodes = fs["nodes"]; edges = fs["edges"]

export_data = {
    "nodes": [n.__dict__ for n in nodes],
    "edges": [e.__dict__ for e in edges],
}

st.download_button(
    "Exportar modelo",
    data=json.dumps(export_data, ensure_ascii=False, indent=2),
    file_name="modelo_normativo.json",
    mime="application/json",
)

st.caption(
    "Altere o fluxo acima e use **Exportar modelo** para salvar o modelo em JSON."
)
