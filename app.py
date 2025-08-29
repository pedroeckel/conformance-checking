# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="PM4Py TBR — Multipáginas", layout="wide")

st.title("Conformance via Token-Based Replay (PM4Py)")
st.markdown(
    """
Este app possui cinco páginas no menu à esquerda:

1. **Gerador de Modelo Normativo** — crie um fluxo normativo interativo e exporte o resultado.
2. **Modelo Normativo** — visualização do fluxo normativo (alto nível).
3. **Token Replay** — execução do TBR com controles manuais, contendo **o modelo normativo no topo** e **o replay abaixo**, **empilhados verticalmente** (não lado a lado), para facilitar a inspeção em modelos grandes.
4. **Gerador de Logs XES/CSV** — criação de logs sintéticos a partir de frequências de traços, com opção de download em XES ou CSV.
5. **Alignments** — execução do algoritmo de alignments do PM4Py a partir de um log CSV, exibindo os resultados completos.

"""
)
st.info("Use o menu à esquerda para navegar.")
