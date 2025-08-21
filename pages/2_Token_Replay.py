# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Union
import io
import streamlit as st
import pandas as pd
from pm4py.objects.log.obj import EventLog
from pm4py.algo.conformance.tokenreplay import algorithm as token_based_replay

from replayviz.pm4py_model import build_tiny_log, build_net_N3
from replayviz.flowviz import (
    build_normative_flow_N3, build_nodes_edges_for_marking_N3
)
from replayviz import (
    markings_along_trace, markings_equal, format_marking,
    ensure_flow_state_slot, update_flow_state_slot, render_flow_slot,
)

st.set_page_config(page_title="Token Replay — N₃", layout="wide")
st.title("Token-Based Replay (N₃) — normativo acima, Petri com fichas abaixo")

@st.cache_data
def load_event_log(src: Optional[Union[str, bytes]]) -> EventLog:
    if isinstance(src, bytes):
        return build_tiny_log(io.BytesIO(src))
    if isinstance(src, str) and src:
        return build_tiny_log(src)
    return build_tiny_log()

st.subheader("Seleção do Log")
uploaded = st.file_uploader(
    "Arquivo de log (XES)", type=["xes"],
    help="Deixe vazio para utilizar o log de exemplo embutido",
)
path_input = st.text_input("Ou caminho para um log existente", "")
src: Optional[Union[str, bytes]] = None
if uploaded is not None:
    src = uploaded.getvalue()
elif path_input:
    src = path_input
log = load_event_log(src)

# Sidebar: apenas escolha de traço
with st.sidebar:
    st.header("Parâmetros do Replay")
    trace_idx = st.selectbox("Trace", options=list(range(1, len(log)+1)), index=0) - 1

# Modelo N₃
net, im, fm, places, trans = build_net_N3()
replay_result = token_based_replay.apply(log, net, im, fm)

seq = markings_along_trace(net, im, log[trace_idx], trans)
max_step = seq[-1][0] if seq else 0

if "frame" not in st.session_state: st.session_state.frame = 0
if "last_params" not in st.session_state: st.session_state.last_params = None
curr_params = (trace_idx, max_step)
if st.session_state.last_params != curr_params:
    st.session_state.last_params = curr_params
    st.session_state.frame = 0
st.session_state.frame = max(0, min(st.session_state.frame, max_step))

# 1) Normativo N₃ (topo)
st.subheader("Modelo normativo (referência)")
n_nodes, n_edges = build_normative_flow_N3()
ensure_flow_state_slot("flow_norm_on_replay_page")
update_flow_state_slot("flow_norm_on_replay_page", n_nodes, n_edges)
render_flow_slot("flow_norm_on_replay_page", key="norm_replay_page", height=260, fit_view=True)

st.markdown("---")

# 2) Controles + Petri com fichas (abaixo)
st.subheader("Controles (somente manual)")
c1, c2, c3 = st.columns([1,1,1])
if c1.button("⏮ Prev"):  st.session_state.frame = max(0, st.session_state.frame - 1)
if c2.button("⏭ Next"):  st.session_state.frame = min(max_step, st.session_state.frame + 1)
if c3.button("⟲ Reset"): st.session_state.frame = 0

st.slider("Passo", 0, max_step, key="frame", help="0 = estado inicial")

st.subheader(f"Replay do Trace {trace_idx+1} — passo {st.session_state.frame}/{max_step}")
st.markdown("**Traço selecionado:** " + " → ".join(ev["concept:name"] for ev in log[trace_idx]))

prev_marking = seq[st.session_state.frame - 1][1] if st.session_state.frame > 0 else None
_, marking, fired_name = seq[st.session_state.frame]

nodes, edges = build_nodes_edges_for_marking_N3(
    net=net, places=places, trans=trans, marking=marking,
    fired_transition_name=(fired_name if st.session_state.frame > 0 else None),
    prev_marking=prev_marking
)

ensure_flow_state_slot("flow_trace_vertical_n3")
update_flow_state_slot("flow_trace_vertical_n3", nodes, edges)
render_flow_slot("flow_trace_vertical_n3", key="trace_vertical_n3", height=360, fit_view=True)

reached = markings_equal(marking, fm)
badge = "✅ **Final atingido**" if reached else "⌛ **Final não atingido**"
fired_txt = f"Transição disparada: **{fired_name}**" if fired_name else "Sem disparo."
st.markdown(badge + " &nbsp;&nbsp;|&nbsp;&nbsp; " + fired_txt)
st.markdown(f"Marcação atual: `{format_marking(marking)}`")
st.markdown(f"Marcação final requerida: `{format_marking(fm)}`")

# Métricas
st.subheader("Métricas do Token-Based Replay")
def _scalar(x): return "—" if x is None else x
def _name(obj) -> str: return getattr(obj, "name", str(obj))
def _fmt_marking_like(val) -> str:
    if val is None: return "—"
    if hasattr(val, "items"):
        try: return "{ " + ", ".join(f"{_name(p)}:{v}" for p, v in val.items()) + " }"
        except Exception: return str(val)
    if isinstance(val, (list, tuple, set)):
        try: return ", ".join(_name(x) for x in val)
        except Exception: return ", ".join(str(x) for x in val)
    return str(val)
def _fmt_seq_of_transitions(val) -> str:
    if val is None: return "—"
    if isinstance(val, (list, tuple, set)):
        out = []
        for x in val:
            if isinstance(x, tuple):
                t = _name(x[0]) if len(x) > 0 else ""
                lab = x[1] if len(x) > 1 else ""
                if not isinstance(lab, str): lab = _name(lab)
                out.append(f"({t},{lab})" if lab != "" else f"({t})")
            else:
                out.append(_name(x))
        return ", ".join(out)
    return _name(val)

rows: List[Dict[str, Any]] = []
for i, r in enumerate(replay_result, start=1):
    rows.append({
        "trace": i,
        "trace_is_fit": _scalar(r.get("trace_is_fit")),
        "trace_fitness": _scalar(r.get("trace_fitness")),
        "missing": _scalar(r.get("missing_tokens")),
        "remaining": _scalar(r.get("remaining_tokens")),
        "consumed": _scalar(r.get("consumed_tokens")),
        "produced": _scalar(r.get("produced_tokens")),
        "reached_marking": _fmt_marking_like(r.get("reached_marking")),
        "enabled_transitions": _fmt_seq_of_transitions(r.get("enabled_transitions_in_marking")),
        "activated_transitions": _fmt_seq_of_transitions(r.get("activated_transitions")),
        "transitions_with_problems": _fmt_seq_of_transitions(r.get("transitions_with_problems")),
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True)
