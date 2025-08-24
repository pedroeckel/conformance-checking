# -*- coding: utf-8 -*-
import streamlit as st
from replayviz.loggen import build_xes_from_frequencies
from pm4py import convert_to_dataframe

st.set_page_config(page_title="Gerador de Logs XES/CSV", layout="wide")
st.title("Gerador de Logs XES/CSV")

st.markdown(
    "Forneça rótulos de atividades e uma tabela de frequências de traços para gerar um log sintético e baixá-lo em XES ou CSV."
)

default_labels = """a: register request
b: examine thoroughly
c: examine casually
d: check ticket
e: decide
f: reinitiate request
g: pay compensation
h: reject request"""

default_freqs = """455, (a, c, d, e, h)
191, (a, b, d, e, g)
177, (a, d, e, g)
144, (a, b, d, e, h)
"""


def parse_labels(text: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            labels[key.strip()] = val.strip()
    return labels


def parse_freqs(text: str):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            freq_part, trace_part = line.split(",", 1)
            try:
                freq = int(freq_part.strip())
            except ValueError:
                continue
            rows.append((freq, trace_part.strip()))
    return rows

labels_txt = st.text_area(
    "Rótulos das atividades (um por linha: letra: descrição)",
    value=default_labels,
    height=180,
)
freqs_txt = st.text_area(
    "Tabela de frequências (freq, (seq de atividades))",
    value=default_freqs,
    height=180,
)
out_path = st.text_input("Arquivo de saída", "Lfull.xes")
add_timestamps = st.checkbox("Gerar timestamps sintéticos", True)

if st.button("Gerar Log"):
    act_labels = parse_labels(labels_txt)
    freqs = parse_freqs(freqs_txt)
    log = build_xes_from_frequencies(
        freqs,
        out_path=out_path,
        activity_labels=act_labels or None,
        add_timestamps=add_timestamps,
    )
    df = convert_to_dataframe(log)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    csv_name = out_path.rsplit(".", 1)[0] + ".csv"
    st.success(f"XES salvo em: {out_path}  - casos: {len(log)}")
    with open(out_path, "rb") as f:
        st.download_button("Baixar XES", data=f.read(), file_name=out_path)
    st.download_button("Baixar CSV", data=csv_bytes, file_name=csv_name, mime="text/csv")

