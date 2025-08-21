from typing import Dict, List, Tuple, Optional
from pm4py.objects.log.obj import Trace
from pm4py.objects.petri_net.obj import PetriNet, Marking

def pre_places(net: PetriNet, t: PetriNet.Transition):
    return [a.source for a in net.arcs if a.target == t]

def post_places(net: PetriNet, t: PetriNet.Transition):
    return [a.target for a in net.arcs if a.source == t]

def is_enabled(net: PetriNet, marking: Marking, t: PetriNet.Transition) -> bool:
    return all(marking.get(p, 0) >= 1 for p in pre_places(net, t))

def fire(net: PetriNet, marking: Marking, t: PetriNet.Transition) -> Marking:
    new_m = Marking(marking)
    for p in pre_places(net, t):
        new_m[p] = new_m.get(p, 0) - 1
    for p in post_places(net, t):
        new_m[p] = new_m.get(p, 0) + 1
    for p in list(new_m.keys()):
        if new_m[p] <= 0:
            del new_m[p]
    return new_m

def markings_along_trace(
    net: PetriNet, im: Marking, trace: Trace, trans: Dict[str, PetriNet.Transition]
) -> List[Tuple[int, Marking, Optional[str]]]:
    """
    Retorna sequência [(k, marking_k, nome_transicao_disparada_ou_None)].
    k=0 é o estado inicial (im).
    """
    seq: List[Tuple[int, Marking, Optional[str]]] = [(0, Marking(im), None)]
    m = Marking(im)
    for k, ev in enumerate(trace, start=1):
        label = ev["concept:name"]
        fired = None
        t = trans.get(label)
        if t is not None and is_enabled(net, m, t):
            m = fire(net, m, t)
            fired = t.name
        seq.append((k, Marking(m), fired))
    return seq

def markings_equal(m1: Marking, m2: Marking) -> bool:
    keys = set(m1.keys()) | set(m2.keys())
    return all(m1.get(p, 0) == m2.get(p, 0) for p in keys)

def format_marking(m: Marking) -> str:
    return "{ " + ", ".join(f"{getattr(p,'name',str(p))}:{m.get(p,0)}" for p in m.keys()) + " }"
