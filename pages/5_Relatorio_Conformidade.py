# -*- coding: utf-8 -*-
"""Página de relatório de conformidade usando token replay."""

from typing import Any, Dict, List, Optional, Union

import pandas as pd
import streamlit as st

from pm4py.algo.conformance.tokenreplay import algorithm as token_based_replay
from pm4py.objects.log.obj import EventLog

from replayviz.pm4py_model import build_net_N3, build_tiny_log
from replayviz.utils_xes import read_xes_any


st.set_page_config(page_title="Relatório – Conformidade", layout="wide")
st.title("RELATÓRIO – CONFORMIDADE")


@st.cache_data(show_spinner=False)
def load_event_log_any(src: Optional[Union[str, bytes]]) -> EventLog:
    """Carrega um log de eventos a partir de bytes/caminho ou exemplo."""
    if src is None:
        return build_tiny_log()
    return read_xes_any(src)


# -----------------------------
# Seleção do log
# -----------------------------
st.subheader("Seleção do Log")
uploaded = st.file_uploader("Carregue um XES", type=["xes", "xes.gz"])
path_input = st.text_input("Ou caminho para um log existente", "")

src: Optional[Union[str, bytes]]
if uploaded is not None:
    src = uploaded.getvalue()
elif path_input.strip():
    src = path_input.strip()
else:
    src = None

try:
    log: EventLog = load_event_log_any(src)
    if src is None:
        st.info(f"Usando log de demonstração (traços: {len(log)})")
    else:
        st.success(f"Log carregado (traços: {len(log)})")
except Exception as e:  # pragma: no cover - mensagem ao usuário
    st.error(f"Falha ao carregar o log: {e}")
    st.stop()


# -----------------------------
# Token replay
# -----------------------------
net, im, fm, _, trans = build_net_N3()
replay_result = token_based_replay.apply(log, net, im, fm)


def _name(obj: Any) -> str:
    if obj is None:
        return "—"
    if hasattr(obj, "label") and obj.label:
        return obj.label  # type: ignore[attr-defined]
    if hasattr(obj, "name"):
        return obj.name  # type: ignore[attr-defined]
    return str(obj)


def _fmt_seq_of_transitions(seq: Any) -> str:
    if not seq:
        return "—"
    return ", ".join(_name(x) for x in seq)


variant_rows: List[Dict[str, Any]] = []
for i, (r, tr) in enumerate(zip(replay_result, log), start=1):
    variant = " → ".join(ev["concept:name"] for ev in tr)
    variant_rows.append(
        {
            "trace": i,
            "variant": variant,
            "trace_is_fit": r.get("trace_is_fit"),
            "trace_fitness": r.get("trace_fitness"),
            "enabled_transitions": _fmt_seq_of_transitions(
                r.get("enabled_transitions_in_marking")
            ),
        }
    )

df_variants_base = pd.DataFrame(variant_rows)


def _mode_or_dash(s: pd.Series) -> str:
    s = s.replace({None: pd.NA, "—": pd.NA})
    m = s.mode(dropna=True)
    return m.iloc[0] if not m.empty else "—"


# Agregação por variante

df_variants = (
    df_variants_base.groupby("variant", dropna=False)
    .agg(
        frequency=("trace", "size"),
        trace_fitness_mean=("trace_fitness", "mean"),
        enabled_transitions_mode=("enabled_transitions", _mode_or_dash),
    )
    .reset_index()
    .sort_values(["frequency"], ascending=[False])
)

# -----------------------------
# Métricas de conformidade
# -----------------------------
model_activities = set(trans.keys())


def _missing_extra(variant: str) -> pd.Series:
    acts = set(variant.split(" → ")) if variant else set()
    missing = model_activities - acts
    extra = acts - model_activities
    return pd.Series(
        {
            "missing_abs": len(missing),
            "extra_abs": len(extra),
            "missing_percent": len(missing) / len(model_activities)
            if model_activities
            else 0.0,
            "extra_percent": len(extra) / len(acts) if acts else 0.0,
        }
    )


df_variants = df_variants.join(df_variants["variant"].apply(_missing_extra))

for col in ["trace_fitness_mean", "missing_percent", "extra_percent"]:
    df_variants[col] = df_variants[col].round(3)

# Agregações para o log inteiro

total_traces = df_variants["frequency"].sum()
variant_lengths = df_variants["variant"].apply(lambda s: len(s.split(" → ")) if s else 0)

total_missing = (df_variants["missing_abs"] * df_variants["frequency"]).sum()
total_extra = (df_variants["extra_abs"] * df_variants["frequency"]).sum()

global_missing_percent = (
    total_missing / (len(model_activities) * total_traces) if total_traces else 0.0
)

total_events = (variant_lengths * df_variants["frequency"]).sum()
global_extra_percent = total_extra / total_events if total_events else 0.0

global_trace_fitness = (
    (df_variants["trace_fitness_mean"] * df_variants["frequency"]).sum() / total_traces
    if total_traces
    else 0.0
)

# -----------------------------
# Relatório
# -----------------------------

st.subheader(
    "Atividades que estão no modelo normativo mas não estão em uma variante do log"
)
st.dataframe(
    df_variants[["variant", "frequency", "missing_abs", "missing_percent"]],
    use_container_width=True,
)
st.write(
    f"Total: {total_missing} ({global_missing_percent:.3f}%) em relação a todas as variantes"
)

st.subheader(
    "Atividades que estão em uma variante do log mas não estão no modelo normativo"
)
st.dataframe(
    df_variants[["variant", "frequency", "extra_abs", "extra_percent"]],
    use_container_width=True,
)
st.write(
    f"Total: {total_extra} ({global_extra_percent:.3f}%) em relação a todas as variantes"
)

st.subheader("Fitness")
st.dataframe(
    df_variants[["variant", "frequency", "trace_fitness_mean"]],
    use_container_width=True,
)
st.write(f"Fitness médio do log: {global_trace_fitness:.3f}")

st.subheader(
    "Atividades presentes nas variantes que foram 'by-passadas' no modelo normativo"
)
st.dataframe(
    df_variants[["variant", "frequency", "enabled_transitions_mode"]],
    use_container_width=True,
)
