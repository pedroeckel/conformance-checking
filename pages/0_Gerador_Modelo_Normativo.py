# -*- coding: utf-8 -*-
"""Página para edição/CRUD e exportação de modelos normativos (integração com streamlit_flow)."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Tuple

import streamlit as st
import pandas as pd
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge

from replayviz import ensure_flow_state_slot, update_flow_state_slot, render_flow_slot

# ------------------------------------------------------------------------------
# Configuração de página
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Gerador de Modelo Normativo", layout="wide")
st.title("Gerador de Modelo Normativo — Canvas + CRUD (streamlit_flow)")

# ------------------------------------------------------------------------------
# Estado base do fluxo
# ------------------------------------------------------------------------------
STATE_SLOT = "norm_model_builder"
ensure_flow_state_slot(STATE_SLOT)

# Layout default (bootstrap)
NODE_SPACING = 120.0
Y_POS = 80.0

# Sequência inicial padrão
default_sequence = ["a", "c", "d", "e", "h"]


# ------------------------------------------------------------------------------
# Helpers de normalização (objeto <-> dict) e utilidades
# ------------------------------------------------------------------------------

def _node_id(n: Any) -> str:
    if hasattr(n, "id"):
        return getattr(n, "id")
    if isinstance(n, dict):
        return n.get("id")
    raise TypeError("Nó sem 'id'.")

def _node_pos(n: Any) -> Tuple[float, float]:
    # Objetos
    if hasattr(n, "pos"):
        p = getattr(n, "pos")
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            return (float(p[0]), float(p[1]))
    if hasattr(n, "position"):
        p = getattr(n, "position")
        if isinstance(p, dict):
            return (float(p.get("x", 0)), float(p.get("y", 0)))
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            return (float(p[0]), float(p[1]))
    # Dicts
    if isinstance(n, dict):
        if "pos" in n and isinstance(n["pos"], (list, tuple)) and len(n["pos"]) >= 2:
            return (float(n["pos"][0]), float(n["pos"][1]))
        if "position" in n:
            p = n["position"]
            if isinstance(p, dict):
                return (float(p.get("x", 0)), float(p.get("y", 0)))
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                return (float(p[0]), float(p[1]))
    # Fallback defensivo
    raise TypeError("Não foi possível extrair a posição do nó (pos/position ausente).")

def _node_data_content(n: Any) -> str:
    data = getattr(n, "data", None)
    if isinstance(data, dict) and "content" in data:
        return str(data["content"])
    if isinstance(n, dict):
        data = n.get("data", {})
        if isinstance(data, dict) and "content" in data:
            return str(data["content"])
    return ""

def _node_type(n: Any) -> str:
    if hasattr(n, "node_type"):
        return getattr(n, "node_type") or "default"
    if isinstance(n, dict):
        return n.get("type") or n.get("node_type", "default")
    return "default"

def _node_source_position(n: Any) -> str:
    if hasattr(n, "source_position"):
        return getattr(n, "source_position") or "right"
    if isinstance(n, dict):
        return n.get("sourcePosition") or n.get("source_position", "right")
    return "right"

def _node_target_position(n: Any) -> str:
    if hasattr(n, "target_position"):
        return getattr(n, "target_position") or "left"
    if isinstance(n, dict):
        return n.get("targetPosition") or n.get("target_position", "left")
    return "left"

def _edge_id(e: Any) -> str:
    if hasattr(e, "id"):
        return getattr(e, "id")
    if isinstance(e, dict):
        return e.get("id")
    raise TypeError("Aresta sem 'id'.")

def _edge_src(e: Any) -> str:
    if hasattr(e, "source"):
        return getattr(e, "source")
    if isinstance(e, dict):
        return e.get("source")
    raise TypeError("Aresta sem 'source'.")

def _edge_dst(e: Any) -> str:
    if hasattr(e, "target"):
        return getattr(e, "target")
    if isinstance(e, dict):
        return e.get("target")
    raise TypeError("Aresta sem 'target'.")

def _edge_label(e: Any) -> str:
    if hasattr(e, "label"):
        return getattr(e, "label") or ""
    if isinstance(e, dict):
        return e.get("label", "")
    return ""

def _is_selected(x: Any) -> bool:
    """Detecta seleção trazida do canvas (ReactFlow costuma marcar selected=True)."""
    if hasattr(x, "selected"):
        try:
            return bool(getattr(x, "selected"))
        except Exception:
            pass
    if isinstance(x, dict):
        return bool(x.get("selected", False))
    # alguns wrappers trazem marcação em data
    data = getattr(x, "data", None)
    if isinstance(data, dict) and "selected" in data:
        return bool(data["selected"])
    return False

def _node_to_json(n: Any) -> Dict[str, Any]:
    x, y = _node_pos(n)
    return {
        "id": _node_id(n),
        "data": {"content": _node_data_content(n)},
        "position": {"x": x, "y": y},
        "type": _node_type(n),
        "sourcePosition": _node_source_position(n),
        "targetPosition": _node_target_position(n),
        # opcionalmente, serialize 'selected' se vier do canvas
        **({"selected": True} if _is_selected(n) else {}),
    }

def _edge_to_json(e: Any) -> Dict[str, Any]:
    base = {
        "id": _edge_id(e),
        "source": _edge_src(e),
        "target": _edge_dst(e),
        "label": _edge_label(e),
    }
    if _is_selected(e):
        base["selected"] = True
    return base

def _json_node_to_obj(d: Dict[str, Any]) -> StreamlitFlowNode:
    # Aceita 'position' dict ou 'pos' lista/tupla
    if "position" in d and isinstance(d["position"], dict):
        x = float(d["position"].get("x", 0))
        y = float(d["position"].get("y", 0))
    elif "pos" in d and isinstance(d["pos"], (list, tuple)) and len(d["pos"]) >= 2:
        x = float(d["pos"][0])
        y = float(d["pos"][1])
    else:
        x, y = 0.0, 0.0

    data = d.get("data") or {}
    content = data.get("content", f"<div><b>{d.get('id','')}</b></div>")

    node = StreamlitFlowNode(
        id=d.get("id"),
        pos=(x, y),
        data={"content": content, **({"selected": True} if d.get("selected") else {})},
        node_type=d.get("type", d.get("node_type", "default")),
        source_position=d.get("sourcePosition", d.get("source_position", "right")),
        target_position=d.get("targetPosition", d.get("target_position", "left")),
    )
    # se a classe expuser atributo selected, tente setar
    if hasattr(node, "selected") and d.get("selected") is True:
        try:
            setattr(node, "selected", True)
        except Exception:
            pass
    return node

def _json_edge_to_obj(d: Dict[str, Any]) -> StreamlitFlowEdge:
    e = StreamlitFlowEdge(
        id=d.get("id"),
        source=d.get("source"),
        target=d.get("target"),
        label=d.get("label", ""),
    )
    if hasattr(e, "selected") and d.get("selected") is True:
        try:
            setattr(e, "selected", True)
        except Exception:
            pass
    return e

def get_flow_state() -> Tuple[List[Any], List[Any]]:
    fs = st.session_state[STATE_SLOT]
    try:
        return fs.nodes, fs.edges  # type: ignore[attr-defined]
    except AttributeError:
        return fs["nodes"], fs["edges"]

def set_flow_state(nodes: List[Any], edges: List[Any]) -> None:
    update_flow_state_slot(STATE_SLOT, nodes, edges)

def ensure_default_flow() -> None:
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
        edges.append(StreamlitFlowEdge(id=f"e_{src}_{dst}", source=src, target=dst, label=""))
    set_flow_state(nodes, edges)


# ------------------------------------------------------------------------------
# Operações CRUD com consciência do canvas (seleção/posições trazidas pelo componente)
# ------------------------------------------------------------------------------

def add_node_right_of(node_id: str, new_id: str) -> None:
    nodes, edges = get_flow_state()
    if new_id in [_node_id(n) for n in nodes]:
        st.error(f"Já existe um nó com id '{new_id}'.")
        return
    base = next((n for n in nodes if _node_id(n) == node_id), None)
    if base is None:
        st.error(f"Nó '{node_id}' não encontrado.")
        return
    x, y = _node_pos(base)
    new_node = StreamlitFlowNode(
        id=new_id,
        pos=(x + NODE_SPACING, y),
        data={"content": f"<div><b>{new_id}</b></div>"},
        node_type=_node_type(base),
        source_position=_node_source_position(base),
        target_position=_node_target_position(base),
    )
    nodes.append(new_node)
    edges.append(StreamlitFlowEdge(id=f"e_{node_id}_{new_id}", source=node_id, target=new_id, label=""))
    set_flow_state(nodes, edges)
    st.toast(f"Nó '{new_id}' adicionado à direita de '{node_id}'.")

def create_edge_between(n_src: str, n_dst: str, eid: str | None = None, label: str = "") -> None:
    nodes, edges = get_flow_state()
    node_ids = {_node_id(n) for n in nodes}
    if n_src not in node_ids or n_dst not in node_ids:
        st.error("Source/target devem existir entre os nós.")
        return
    if eid is None:
        eid = f"e_{n_src}_{n_dst}"
    if eid in {_edge_id(e) for e in edges}:
        st.warning(f"Aresta '{eid}' já existe.")
        return
    edges.append(StreamlitFlowEdge(id=eid, source=n_src, target=n_dst, label=label))
    set_flow_state(nodes, edges)
    st.toast(f"Aresta '{eid}' criada ({n_src} → {n_dst}).")

def remove_selected() -> None:
    nodes, edges = get_flow_state()
    sel_nodes = {_node_id(n) for n in nodes if _is_selected(n)}
    sel_edges = {_edge_id(e) for e in edges if _is_selected(e)}
    if not sel_nodes and not sel_edges:
        st.info("Nenhum elemento selecionado no canvas.")
        return
    # remove arestas selecionadas
    edges = [e for e in edges if _edge_id(e) not in sel_edges]
    # remove arestas incidentes nos nós selecionados
    edges = [e for e in edges if _edge_src(e) not in sel_nodes and _edge_dst(e) not in sel_nodes]
    # remove nós
    nodes = [n for n in nodes if _node_id(n) not in sel_nodes]
    set_flow_state(nodes, edges)
    st.toast(f"Removido(s): {len(sel_nodes)} nó(s) e {len(sel_edges)} aresta(s) selecionados(as).")

def rename_selected_node(new_id: str) -> None:
    nodes, edges = get_flow_state()
    selected = [n for n in nodes if _is_selected(n)]
    if len(selected) != 1:
        st.error("Selecione exatamente 1 nó no canvas para renomear.")
        return
    old_id = _node_id(selected[0])
    if new_id == old_id:
        return
    if new_id in [_node_id(n) for n in nodes]:
        st.error(f"Já existe um nó com id '{new_id}'.")
        return
    # atualiza nó
    x, y = _node_pos(selected[0])
    updated = StreamlitFlowNode(
        id=new_id,
        pos=(x, y),
        data={"content": _node_data_content(selected[0]) or f"<div><b>{new_id}</b></div>"},
        node_type=_node_type(selected[0]),
        source_position=_node_source_position(selected[0]),
        target_position=_node_target_position(selected[0]),
    )
    for i, n in enumerate(nodes):
        if _node_id(n) == old_id:
            nodes[i] = updated
            break
    # atualiza arestas
    for j, e in enumerate(edges):
        sid, tid = _edge_src(e), _edge_dst(e)
        eid = _edge_id(e)
        changed = False
        if sid == old_id:
            sid = new_id
            changed = True
        if tid == old_id:
            tid = new_id
            changed = True
        if changed:
            edges[j] = StreamlitFlowEdge(id=f"e_{sid}_{tid}" if not eid else eid, source=sid, target=tid, label=_edge_label(e))
    set_flow_state(nodes, edges)
    st.toast(f"Nó renomeado: '{old_id}' → '{new_id}'.")

def duplicate_selected_node(new_id: str) -> None:
    nodes, edges = get_flow_state()
    selected = [n for n in nodes if _is_selected(n)]
    if len(selected) != 1:
        st.error("Selecione exatamente 1 nó no canvas para duplicar.")
        return
    if new_id in [_node_id(n) for n in nodes]:
        st.error(f"Já existe um nó com id '{new_id}'.")
        return
    base = selected[0]
    x, y = _node_pos(base)
    dup = StreamlitFlowNode(
        id=new_id,
        pos=(x + NODE_SPACING, y),
        data={"content": _node_data_content(base) or f"<div><b>{new_id}</b></div>"},
        node_type=_node_type(base),
        source_position=_node_source_position(base),
        target_position=_node_target_position(base),
    )
    nodes.append(dup)
    set_flow_state(nodes, edges)
    st.toast(f"Nó '{new_id}' criado como duplicata de '{_node_id(base)}'.")

def auto_layout_row(start_x: float | None = None, y: float | None = None) -> None:
    """Distribui todos os nós em linha com espaçamento fixo; preserva ordem atual."""
    nodes, edges = get_flow_state()
    if not nodes:
        return
    if start_x is None:
        # usa o menor x atual
        start_x = min(_node_pos(n)[0] for n in nodes)
    if y is None:
        # usa a mediana do y atual
        ys = sorted(_node_pos(n)[1] for n in nodes)
        y = ys[len(ys)//2]
    # reatribui posições
    new_nodes: List[Any] = []
    cur_x = start_x
    for n in nodes:
        new_nodes.append(StreamlitFlowNode(
            id=_node_id(n),
            pos=(cur_x, float(y)),
            data={"content": _node_data_content(n) or f"<div><b>{_node_id(n)}</b></div>"},
            node_type=_node_type(n),
            source_position=_node_source_position(n),
            target_position=_node_target_position(n),
        ))
        cur_x += NODE_SPACING
    set_flow_state(new_nodes, edges)
    st.toast("Auto-layout em linha aplicado.")


# ------------------------------------------------------------------------------
# Bootstrap do fluxo
# ------------------------------------------------------------------------------
ensure_default_flow()

# ------------------------------------------------------------------------------
# Controles globais
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("Ações rápidas (globais)")
    if st.button("Reiniciar para modelo padrão", type="secondary", use_container_width=True):
        st.session_state[STATE_SLOT] = {}
        ensure_flow_state_slot(STATE_SLOT)
        ensure_default_flow()
        st.success("Fluxo reiniciado para o modelo padrão.")
    st.caption("Use o canvas para mover/selecionar; use os controles da página para CRUD.")

# ------------------------------------------------------------------------------
# Canvas (streamlit_flow) — o componente atualiza o estado do slot
# ------------------------------------------------------------------------------
st.subheader("Editor visual (canvas)")
render_flow_slot(STATE_SLOT, key="norm_builder", height=460, fit_view=True)

# Após render, recupere o estado atualizado (posições/seleção vindas do canvas)
nodes, edges = get_flow_state()
selected_nodes = [_node_id(n) for n in nodes if _is_selected(n)]
selected_edges = [_edge_id(e) for e in edges if _is_selected(e)]

with st.expander("Seleção atual (canvas)"):
    st.write({"selected_nodes": selected_nodes, "selected_edges": selected_edges})

# ------------------------------------------------------------------------------
# Ações baseadas na SELEÇÃO do canvas (CRUD in-place)
# ------------------------------------------------------------------------------
st.subheader("Ações sobre a seleção (canvas)")
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    new_id = st.text_input("Novo nó (à direita do 1º selecionado)", key="add_right_newid")
    if st.button("Adicionar à direita", use_container_width=True):
        if not selected_nodes:
            st.error("Selecione um nó no canvas.")
        elif not new_id.strip():
            st.error("Informe o id do novo nó.")
        else:
            add_node_right_of(selected_nodes[0], new_id.strip())

with c2:
    if st.button("Criar aresta (2 nós sel.)", use_container_width=True):
        if len(selected_nodes) != 2:
            st.error("Selecione exatamente 2 nós no canvas (ordem = origem→destino).")
        else:
            create_edge_between(selected_nodes[0], selected_nodes[1])

with c3:
    rid = st.text_input("Renomear nó (novo id)", key="rename_sel_newid")
    if st.button("Renomear nó sel.", use_container_width=True):
        if not rid.strip():
            st.error("Informe o novo id.")
        else:
            rename_selected_node(rid.strip())

with c4:
    dup_id = st.text_input("Duplicar nó (novo id)", key="dup_sel_newid")
    if st.button("Duplicar nó sel.", use_container_width=True):
        if not dup_id.strip():
            st.error("Informe o novo id.")
        else:
            duplicate_selected_node(dup_id.strip())

with c5:
    if st.button("Remover selecionados", type="primary", use_container_width=True):
        remove_selected()

with c6:
    if st.button("Auto-layout em linha", use_container_width=True):
        auto_layout_row()

st.divider()

# ------------------------------------------------------------------------------
# CRUD tradicional + Edição em lote + Import/Export (com validação)
# ------------------------------------------------------------------------------
tab_nodes, tab_edges, tab_batch, tab_io = st.tabs(["Nós (CRUD)", "Arestas (CRUD)", "Edição em Lote", "Importar / Exportar"])

with tab_nodes:
    st.markdown("### Nós (CRUD por formulário)")
    nodes, edges = get_flow_state()
    nodes_df_view = pd.DataFrame([_node_to_json(n) for n in nodes])
    st.dataframe(nodes_df_view[["id", "position", "type"]], use_container_width=True, hide_index=True)

    st.markdown("#### Adicionar nó (formulário)")
    with st.form("form_add_node_manual"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        nid = c1.text_input("id", value="")
        x = c2.number_input("x", value=float(max([_node_pos(n)[0] for n in nodes], default=0.0) + NODE_SPACING))
        y = c3.number_input("y", value=float(_node_pos(nodes[0])[1] if nodes else Y_POS))
        ntype = c4.selectbox("node_type", ["default", "input", "output", "group"], index=0)
        content_html = st.text_input("content_html", value="")
        c5, c6 = st.columns(2)
        sp = c5.selectbox("source_position", ["left", "right", "top", "bottom"], index=1)
        tp = c6.selectbox("target_position", ["left", "right", "top", "bottom"], index=0)
        if st.form_submit_button("Adicionar"):
            if nid.strip():
                # usa função canvas-safe: inserir sem alterar seleção vem do próprio componente
                nodes2, edges2 = get_flow_state()
                if nid.strip() in [_node_id(n) for n in nodes2]:
                    st.error(f"Nó '{nid.strip()}' já existe.")
                else:
                    new_node = StreamlitFlowNode(
                        id=nid.strip(), pos=(x, y),
                        data={"content": content_html or f"<div><b>{nid.strip()}</b></div>"},
                        node_type=ntype, source_position=sp, target_position=tp,
                    )
                    nodes2.append(new_node)
                    set_flow_state(nodes2, edges2)
                    st.success(f"Nó '{nid.strip()}' adicionado.")

    st.markdown("#### Remover nó (formulário)")
    node_ids = [_node_id(n) for n in nodes]
    if node_ids:
        del_id = st.selectbox("Selecionar nó para remover", node_ids, key="delete_node_select_form")
        if st.button("Remover nó (formulário)", type="primary"):
            nodes2, edges2 = get_flow_state()
            nodes2 = [n for n in nodes2 if _node_id(n) != del_id]
            edges2 = [e for e in edges2 if _edge_src(e) != del_id and _edge_dst(e) != del_id]
            set_flow_state(nodes2, edges2)
            st.success(f"Nó '{del_id}' removido (com arestas incidentes).")

with tab_edges:
    st.markdown("### Arestas (CRUD por formulário)")
    nodes, edges = get_flow_state()
    edges_df_view = pd.DataFrame([_edge_to_json(e) for e in edges])
    st.dataframe(edges_df_view, use_container_width=True, hide_index=True)

    st.markdown("#### Adicionar aresta (formulário)")
    with st.form("form_add_edge_manual"):
        c1, c2, c3 = st.columns([2, 2, 1])
        eid = c1.text_input("id", value="")
        source = c2.selectbox("source", [_node_id(n) for n in nodes])
        target = c3.selectbox("target", [_node_id(n) for n in nodes], index=min(1, len(nodes)-1) if nodes else 0)
        label = st.text_input("label", value="")
        if st.form_submit_button("Adicionar"):
            if eid.strip():
                create_edge_between(source, target, eid.strip(), label)
            else:
                st.error("Informe um id para a aresta.")

    st.markdown("#### Remover aresta (formulário)")
    edge_ids = [_edge_id(e) for e in edges]
    if edge_ids:
        del_eid = st.selectbox("Selecionar aresta para remover", edge_ids, key="delete_edge_select_form")
        if st.button("Remover aresta (formulário)", type="primary"):
            nodes2, edges2 = get_flow_state()
            edges2 = [e for e in edges2 if _edge_id(e) != del_eid]
            set_flow_state(nodes2, edges2)
            st.success(f"Aresta '{del_eid}' removida.")

with tab_batch:
    st.markdown("### Edição em lote (Nós e Arestas)")
    nodes, edges = get_flow_state()
    nodes_df = pd.DataFrame([_node_to_json(n) for n in nodes])
    edges_df = pd.DataFrame([_edge_to_json(e) for e in edges])

    st.markdown("#### Nós")
    nodes_edit = st.data_editor(
        nodes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="nodes_editor",
        column_config={
            "id": st.column_config.TextColumn("id", required=True),
            "position": st.column_config.Column("position"),
            "type": st.column_config.SelectboxColumn("type", options=["default", "input", "output", "group"]),
        },
    )

    st.markdown("#### Arestas")
    edges_edit = st.data_editor(
        edges_df,
        num_rows="dynamic",
        use_container_width=True,
        key="edges_editor",
        column_config={
            "id": st.column_config.TextColumn("id", required=True),
            "source": st.column_config.SelectboxColumn("source", options=list(nodes_edit["id"]) if not nodes_edit.empty else []),
            "target": st.column_config.SelectboxColumn("target", options=list(nodes_edit["id"]) if not nodes_edit.empty else []),
            "label": st.column_config.TextColumn("label"),
        },
    )

    def _nodes_df_to_objs(df: pd.DataFrame) -> List[StreamlitFlowNode]:
        out: List[StreamlitFlowNode] = []
        for _, r in df.iterrows():
            node_id = str(r["id"])
            pos = r.get("position", {"x": 0, "y": 0}) or {"x": 0, "y": 0}
            x = float(pos.get("x", 0)) if isinstance(pos, dict) else float(0)
            y = float(pos.get("y", 0)) if isinstance(pos, dict) else float(0)
            ntype = str(r.get("type", "default"))
            out.append(StreamlitFlowNode(
                id=node_id, pos=(x, y),
                data={"content": f"<div><b>{node_id}</b></div>"},
                node_type=ntype,
                source_position="right",
                target_position="left",
            ))
        return out

    def _edges_df_to_objs(df: pd.DataFrame) -> List[StreamlitFlowEdge]:
        out: List[StreamlitFlowEdge] = []
        for _, r in df.iterrows():
            out.append(StreamlitFlowEdge(
                id=str(r["id"]),
                source=str(r["source"]),
                target=str(r["target"]),
                label=str(r.get("label", "")),
            ))
        return out

    def _validate_integrity(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        msgs: List[str] = []
        ok = True
        if nodes_df["id"].duplicated().any():
            ok = False
            dups = nodes_df[nodes_df["id"].duplicated()]["id"].tolist()
            msgs.append(f"Nós com IDs duplicados: {dups}")
        node_ids = set(nodes_df["id"].astype(str))
        missing_src = [row.id for row in edges_df.itertuples() if str(row.source) not in node_ids]
        missing_tgt = [row.id for row in edges_df.itertuples() if str(row.target) not in node_ids]
        if missing_src:
            ok = False
            msgs.append(f"Arestas com source inexistente: {missing_src}")
        if missing_tgt:
            ok = False
            msgs.append(f"Arestas com target inexistente: {missing_tgt}")
        if edges_df["id"].duplicated().any():
            ok = False
            dups = edges_df[edges_df["id"].duplicated()]["id"].tolist()
            msgs.append(f"Arestas com IDs duplicados: {dups}")
        return ok, msgs

    if st.button("Aplicar mudanças (validar e salvar)"):
        ok, msgs = _validate_integrity(nodes_edit, edges_edit)
        if not ok:
            for m in msgs:
                st.error(m)
            st.stop()
        new_nodes = _nodes_df_to_objs(nodes_edit)
        new_edges = _edges_df_to_objs(edges_edit)
        set_flow_state(new_nodes, new_edges)
        st.success("Mudanças aplicadas com sucesso.")

with tab_io:
    st.markdown("### Importar / Exportar JSON")
    nodes, edges = get_flow_state()
    export_data = {
        "nodes": [_node_to_json(n) for n in nodes],
        "edges": [_edge_to_json(e) for e in edges],
    }
    with st.expander("Pré-visualização do JSON atual"):
        st.code(json.dumps(export_data, ensure_ascii=False, indent=2), language="json")
    st.download_button(
        "Exportar modelo (JSON)",
        data=json.dumps(export_data, ensure_ascii=False, indent=2),
        file_name="modelo_normativo.json",
        mime="application/json",
    )
    st.markdown("#### Importar de JSON")
    imported = st.text_area("Cole o JSON do modelo (nodes/edges)", value="", height=180)
    if st.button("Importar JSON"):
        try:
            data = json.loads(imported)
            raw_nodes = data.get("nodes", [])
            raw_edges = data.get("edges", [])
            new_nodes = [_json_node_to_obj(d) for d in raw_nodes]
            new_edges = [_json_edge_to_obj(d) for d in raw_edges]
            # Validação básica
            ndf = pd.DataFrame([_node_to_json(n) for n in new_nodes])
            edf = pd.DataFrame([_edge_to_json(e) for e in new_edges])
            node_ids = set(ndf["id"].astype(str))
            missing_src = [row.id for row in edf.itertuples() if str(row.source) not in node_ids]
            missing_tgt = [row.id for row in edf.itertuples() if str(row.target) not in node_ids]
            if missing_src or missing_tgt:
                if missing_src:
                    st.error(f"Arestas com source inexistente: {missing_src}")
                if missing_tgt:
                    st.error(f"Arestas com target inexistente: {missing_tgt}")
                st.stop()
            set_flow_state(new_nodes, new_edges)
            st.success("Modelo importado com sucesso.")
        except Exception as ex:
            st.exception(ex)

# Rodapé
st.caption(
    "Edite no canvas (streamlit_flow) e use os botões de CRUD baseados na seleção. "
    "A qualquer momento, exporte/importa o JSON com o estado atual."
)
