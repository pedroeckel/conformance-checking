# -*- coding: utf-8 -*-
import streamlit as st
from replayviz import ensure_flow_state_slot, update_flow_state_slot, render_flow_slot
from replayviz.pm4py_model import build_net_N3
from replayviz.flowviz import build_normative_flow_N3

st.set_page_config(page_title="Modelo Normativo N₃", layout="wide")
st.title("Modelo Normativo — N₃")

# constrói o net (apenas para referência de consistência)
net, im, fm, places, trans = build_net_N3()

nodes, edges = build_normative_flow_N3()
ensure_flow_state_slot("flow_norm_n3")
update_flow_state_slot("flow_norm_n3", nodes, edges)
render_flow_slot("flow_norm_n3", key="norm_n3", height=280, fit_view=True)

st.caption("Layout conforme o diagrama N₃: split paralelo após **a**, ramos **c**/**d**, join em **e**, depois **h** até **end**.")
