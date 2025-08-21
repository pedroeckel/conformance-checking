# -*- coding: utf-8 -*-
import streamlit as st
from replayviz import ensure_flow_state_slot, update_flow_state_slot, render_flow_slot
from replayviz.pm4py_model import build_net_from_file
from replayviz.flowviz import (
    build_normative_flow,
    default_layout,
    DEFAULT_TRANS_DESCR,
)


def main(
    model_path: str = "",
    layout: dict | None = None,
    labels: dict | None = None,
) -> None:
    st.set_page_config(page_title="Modelo Normativo", layout="wide")
    st.title("Modelo Normativo")

    model_path = st.text_input("Caminho do modelo (PNML)", value=model_path)
    layout = layout or default_layout()
    labels = labels or DEFAULT_TRANS_DESCR

    if model_path:
        net, im, fm, places, trans = build_net_from_file(model_path)
        nodes, edges = build_normative_flow(net, layout, labels)
        ensure_flow_state_slot("flow_norm")
        update_flow_state_slot("flow_norm", nodes, edges)
        render_flow_slot("flow_norm", key="norm", height=280, fit_view=True)
    else:
        st.info("Informe o caminho de um arquivo PNML para visualizar o modelo.")


if __name__ == "__main__":
    main()
