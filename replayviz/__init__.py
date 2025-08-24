# replayviz/__init__.py

# Modelo / PM4Py
from .pm4py_model import build_tiny_log, build_net_N3

# Marcações / utilidades puras
from .markings import (
    pre_places, post_places, is_enabled, fire,
    markings_along_trace, markings_equal, format_marking
)

# Visualização (N3)
from .flowviz import (
    build_nodes_edges_for_marking_N3,
    build_normative_flow_N3,
    build_trace_flow,
)

# Estado do componente streamlit-flow
from .flow_state import (
    ensure_flow_state_slot, update_flow_state_slot, render_flow_slot
)

# Geração de logs XES
from .loggen import build_xes_from_frequencies


from .utils_xes import read_xes_any

