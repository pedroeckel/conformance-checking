# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="PM4Py TBR — Multipáginas", layout="wide")

st.title("Conformance via Token-Based Replay (PM4Py)")
st.markdown(
    """
Este app possui duas páginas no menu à esquerda:

1. **Modelo Normativo** — visualização do fluxo normativo (alto nível).
2. **Token Replay** — execução do TBR com controles manuais, contendo **o modelo normativo no topo** e **o replay abaixo**, **empilhados verticalmente** (não lado a lado), para facilitar a inspeção em modelos grandes.
"""
)
st.info("Use o menu à esquerda para navegar.")
