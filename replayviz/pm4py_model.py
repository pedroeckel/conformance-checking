from typing import Dict, Tuple, Union, Optional, IO
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.log.importer.xes import importer as xes_importer

def build_tiny_log(log: Optional[Union[str, IO, EventLog]] = None) -> EventLog:
    """Return an :class:`EventLog`.

    When ``log`` is provided, it can either be a path to a log, a file-like
    object or an :class:`EventLog` instance. In such cases the provided log is
    returned/loaded instead of creating the bundled tiny example.
    """
    if log is not None:
        if isinstance(log, EventLog):
            return log
        return xes_importer.apply(log)

    log = EventLog()
    # Exemplos simples coerentes com N₃
    # a c d e h
    t1 = Trace([Event({"concept:name": "a"}),
                Event({"concept:name": "c"}),
                Event({"concept:name": "d"}),
                Event({"concept:name": "e"}),
                Event({"concept:name": "h"})])
    # ordem c/d trocada, continua válida (AND)
    t2 = Trace([Event({"concept:name": "a"}),
                Event({"concept:name": "d"}),
                Event({"concept:name": "c"}),
                Event({"concept:name": "e"}),
                Event({"concept:name": "h"})])
    for tr in (t1, t2):
        log.append(tr)
    return log

def build_net_N3() -> Tuple[
    PetriNet, Marking, Marking, Dict[str, PetriNet.Place], Dict[str, PetriNet.Transition]
]:
    """
    N₃ (start) — a — (split) — c/d — (join) — e — p5 — h — (end)
    AND-split após 'a' (produz p1 e p2). AND-join em 'e' (requer p3 e p4).
    """
    net = PetriNet("N3")

    # places
    p_start = PetriNet.Place("p_start")
    p1 = PetriNet.Place("p1")
    p2 = PetriNet.Place("p2")
    p3 = PetriNet.Place("p3")
    p4 = PetriNet.Place("p4")
    p5 = PetriNet.Place("p5")
    p_end = PetriNet.Place("p_end")
    net.places.update({p_start, p1, p2, p3, p4, p5, p_end})
    places = {p.name: p for p in net.places}

    # transitions (labels iguais aos eventos)
    a = PetriNet.Transition("a", "a")
    c = PetriNet.Transition("c", "c")
    d = PetriNet.Transition("d", "d")
    e = PetriNet.Transition("e", "e")
    h = PetriNet.Transition("h", "h")
    net.transitions.update({a, c, d, e, h})
    trans = {t.name: t for t in net.transitions}

    # arcs
    petri_utils.add_arc_from_to(p_start, a, net)
    petri_utils.add_arc_from_to(a, p1, net)
    petri_utils.add_arc_from_to(a, p2, net)

    petri_utils.add_arc_from_to(p1, c, net)
    petri_utils.add_arc_from_to(c, p3, net)

    petri_utils.add_arc_from_to(p2, d, net)
    petri_utils.add_arc_from_to(d, p4, net)

    # AND-join em e: precisa de p3 e p4
    petri_utils.add_arc_from_to(p3, e, net)
    petri_utils.add_arc_from_to(p4, e, net)
    petri_utils.add_arc_from_to(e, p5, net)

    petri_utils.add_arc_from_to(p5, h, net)
    petri_utils.add_arc_from_to(h, p_end, net)

    im = Marking({p_start: 1})
    fm = Marking({p_end: 1})
    return net, im, fm, places, trans
