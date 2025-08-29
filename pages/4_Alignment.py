# -*- coding: utf-8 -*-
"""Página de alignments baseada em PM4Py.

Permite o upload de um log em CSV e executa o algoritmo de
alignments sobre o modelo normativo N₃, exibindo os resultados
completos retornados pela API do PM4Py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import io

import pandas as pd
import streamlit as st

from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.objects.conversion.log import converter as log_converter

from replayviz.pm4py_model import build_net_N3


st.set_page_config(page_title="Alignments — N₃", layout="wide")
st.title("Alignments (N₃) — PM4Py")

st.subheader("Seleção do Log (CSV)")
uploaded = st.file_uploader("Carregue um CSV", type=["csv"])
path_input = st.text_input("Ou caminho para um CSV existente", "")

# Determina a origem do CSV e carrega em DataFrame
df: Optional[pd.DataFrame] = None
try:
    if uploaded is not None:
        df = pd.read_csv(io.BytesIO(uploaded.getvalue()))
    elif path_input.strip():
        df = pd.read_csv(path_input.strip())
    else:
        st.info("Carregue um CSV para prosseguir.")
        st.stop()
except Exception as e:  # pragma: no cover - mensagem ao usuário
    st.error(f"Falha ao ler o CSV: {e}")
    st.stop()

# Converte para EventLog
try:
    if "time:timestamp" in df.columns:
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    log = log_converter.apply(df)
    st.success(f"Log carregado (traços: {len(log)})")
except Exception as e:  # pragma: no cover - mensagem ao usuário
    st.error(f"Falha ao converter o log: {e}")
    st.stop()

# Modelo normativo N3
net, im, fm, _, _ = build_net_N3()

# Execução dos alignments
align_result = alignments.apply_log(log, net, im, fm)

rows: List[Dict[str, Any]] = []
for i, res in enumerate(align_result, start=1):
    row: Dict[str, Any] = {"trace": i}
    # inclui todos os campos retornados pela API
    row.update(res)
    rows.append(row)

st.subheader("Resultados dos Alignments")
st.dataframe(pd.DataFrame(rows), use_container_width=True)
