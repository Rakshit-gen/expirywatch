"""LangGraph wiring: extract -> lead-time lookup -> (due? draft+notify : store only).

The extractor, drafter, and notifier are swappable: build_graph(extractor=...,
drafter=..., notifier=..., policy=...) picks by name from the
expirywatch.plugins registries (see extract.py, draft.py, notify.py, or
register your own).
"""
from __future__ import annotations

import datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from . import draft as _draft  # noqa: F401  (registers built-in drafters)
from . import extract as _extract  # noqa: F401  (registers built-in extractors)
from . import notify as _notify  # noqa: F401  (registers built-in notifiers)
from .leadtime import LEAD_TIMES_DAYS, is_due
from .plugins import DRAFTERS, EXTRACTORS, NOTIFIERS


class State(TypedDict, total=False):
    raw_text: str | None
    doc_type: str
    expiry_date: str
    source: str
    today: str | None  # override for tests; defaults to real today
    lead_time_days: int
    due: bool
    checklist: list[str]


def route_after_leadtime(state: State) -> str:
    return "draft" if state["due"] else "skip"


def build_graph(extractor: str = "hybrid", drafter: str = "hybrid", notifier: str = "console", policy: dict | None = None):
    extract_fn = EXTRACTORS[extractor]
    draft_fn = DRAFTERS[drafter]
    notify_fn = NOTIFIERS[notifier]
    lead_times = policy if policy is not None else LEAD_TIMES_DAYS

    def node_extract(state: State) -> dict:
        if state.get("raw_text"):
            result = extract_fn(state["raw_text"])
            if result is None:
                return {"doc_type": "generic", "expiry_date": ""}
            doc_type, expiry_date = result
            return {"doc_type": doc_type, "expiry_date": expiry_date, "source": "scan"}
        return {}  # doc_type/expiry_date already provided (manual add)

    def node_leadtime(state: State) -> dict:
        days = lead_times.get(state["doc_type"], lead_times.get("generic", 14))
        if not state.get("expiry_date"):
            return {"lead_time_days": days, "due": False}
        due = is_due(state["expiry_date"], days, state.get("today"))
        return {"lead_time_days": days, "due": due}

    def node_draft(state: State) -> dict:
        today = datetime.date.fromisoformat(state["today"]) if state.get("today") else datetime.date.today()
        expiry = datetime.date.fromisoformat(state["expiry_date"])
        days_until = (expiry - today).days
        return {"checklist": draft_fn(state["doc_type"], days_until)}

    def node_notify(state: State) -> dict:
        steps = "\n".join(f"- {s}" for s in state["checklist"])
        notify_fn(
            f"{state['doc_type']} expiring {state['expiry_date']}",
            f"Renewal window is open (lead time: {state['lead_time_days']}d).\n{steps}",
        )
        return {}

    graph = StateGraph(State)
    graph.add_node("extract", node_extract)
    graph.add_node("leadtime", node_leadtime)
    graph.add_node("draft", node_draft)
    graph.add_node("notify", node_notify)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "leadtime")
    graph.add_conditional_edges("leadtime", route_after_leadtime, {"draft": "draft", "skip": END})
    graph.add_edge("draft", "notify")
    graph.add_edge("notify", END)

    return graph.compile()
