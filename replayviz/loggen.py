# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Iterable, List, Tuple, Union, Mapping, Sequence
from datetime import datetime, timedelta, timezone

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

ActivitySeq = Union[str, Sequence[str]]
FreqTable = Union[
    Mapping[Tuple[str, ...], int],
    Iterable[Tuple[int, ActivitySeq]],
]


def _parse_trace(trace: ActivitySeq) -> Tuple[str, ...]:
    """Aceita 'a,c,d' | '(a, c, d, e, h)' | ['a','c','d'] e devolve ('a','c','d')."""
    if isinstance(trace, (list, tuple)):
        return tuple(str(x).strip() for x in trace)
    s = str(trace).strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return tuple(parts)


def _normalize_freq_table(table: FreqTable) -> List[Tuple[Tuple[str, ...], int]]:
    """Converte qualquer formato aceito para lista padronizada [(('a','b'), 3), ...]."""
    if isinstance(table, Mapping):
        return [(tuple(k), int(v)) for k, v in table.items()]
    out: List[Tuple[Tuple[str, ...], int]] = []
    for freq, tr in table:
        out.append((_parse_trace(tr), int(freq)))
    return out


def build_xes_from_frequencies(
    freq_table: FreqTable,
    out_path: str,
    *,
    activity_labels: Mapping[str, str] | None = None,
    add_timestamps: bool = True,
    base_time: datetime | None = None,
    delta_between_cases: timedelta = timedelta(minutes=3),
    delta_between_events: timedelta = timedelta(seconds=15),
    case_prefix: str = "σ",
    keep_activity_letters_in_concept_name: bool = True,
) -> EventLog:
    rows = _normalize_freq_table(freq_table)
    log = EventLog()

    if add_timestamps:
        if base_time is None:
            base_time = datetime.now(timezone.utc).replace(microsecond=0)
        current_case_start = base_time
    else:
        current_case_start = None  # type: ignore

    case_counter = 0
    for _, (activities, freq) in enumerate(rows, start=1):
        for _ in range(freq):
            case_counter += 1
            tr = Trace()
            tr.attributes["concept:name"] = f"{case_prefix}{case_counter}"

            if add_timestamps:
                t0 = current_case_start
            for pos, act in enumerate(activities):
                ev_name = (
                    act
                    if keep_activity_letters_in_concept_name
                    else activity_labels.get(act, act) if activity_labels else act
                )
                e = Event({"concept:name": ev_name})

                if activity_labels:
                    e["activity:label"] = activity_labels.get(act, act)

                if add_timestamps:
                    e["time:timestamp"] = t0 + pos * delta_between_events  # type: ignore
                    e["lifecycle:transition"] = "complete"

                tr.append(e)

            log.append(tr)

            if add_timestamps:
                current_case_start += delta_between_cases  # type: ignore

    xes_exporter.apply(log, out_path)
    return log
