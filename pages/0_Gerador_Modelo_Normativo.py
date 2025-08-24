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

# Utilidades --------------------------------------------------------------

def get_flow_state():
    fs = st.session_state[STATE_SLOT]
    try:
        return fs.nodes, fs.edges  # type: ignore[attr-defined]
    except AttributeError:
        return fs["nodes"], fs["edges"]


def ensure_default_flow():
    nodes, edges = get_flow_state()
    if nodes:
        return

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


def add_node(label: str) -> None:
    nodes, edges = get_flow_state()
    existing_ids = [n.id if hasattr(n, "id") else n["id"] for n in nodes]
    if label in existing_ids:
        st.warning("Quadrante já existe")
        return

    if hasattr(nodes[0], "pos"):
        last_x = max(n.pos[0] for n in nodes)
        y = nodes[0].pos[1]
        prev_id = nodes[-1].id
    else:
        last_x = max(n["position"]["x"] for n in nodes)
        y = nodes[0]["position"]["y"]
        prev_id = nodes[-1]["id"]

    x = last_x + NODE_SPACING
    nodes.append(
        StreamlitFlowNode(
            id=label,
            pos=(x, y),
            data={"content": f"<div><b>{label}</b></div>"},
            node_type="default",
            source_position="right",
            target_position="left",
        )
    )
    edges.append(
        StreamlitFlowEdge(
            id=f"e_{prev_id}_{label}", source=prev_id, target=label, label="",
        )
    )
    update_flow_state_slot(STATE_SLOT, nodes, edges)
    st.toast(f"Quadrante '{label}' adicionado")


# Modelo padrão: sequência a → c → d → e → h
default_sequence = ["a", "c", "d", "e", "h"]
ensure_default_flow()

# Adiciona novos quadrantes ------------------------------------------------
with st.form("add_node_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    new_label = col1.text_input("Nome do novo quadrante")
    submitted = col2.form_submit_button("Adicionar")
    if submitted and new_label:
        add_node(new_label)

# Renderiza o editor de fluxo
render_flow_slot(STATE_SLOT, key="norm_builder", height=400, fit_view=True)

# Exporta para JSON -------------------------------------------------------
nodes, edges = get_flow_state()
export_data = {
    "nodes": [n.__dict__ if hasattr(n, "__dict__") else n for n in nodes],
    "edges": [e.__dict__ if hasattr(e, "__dict__") else e for e in edges],
}

with st.expander("Pré-visualização do JSON"):
    st.code(json.dumps(export_data, ensure_ascii=False, indent=2), language="json")

st.download_button(
    "Exportar modelo",
    data=json.dumps(export_data, ensure_ascii=False, indent=2),
    file_name="modelo_normativo.json",
    mime="application/json",
)

st.caption(
    "Altere o fluxo acima e use **Exportar modelo** para salvar o modelo em JSON.",
)

