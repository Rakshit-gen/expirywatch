"""LangGraph wiring: extract -> lead-time lookup -> (due? draft+notify : store only)."""
from __future__ import annotations

import datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .draft import draft_checklist
from .extract import extract
from .leadtime import is_due, lead_time_for
from .notify import notify


class State(TypedDict, total=False):
    raw_text: str | None
    doc_type: str
    expiry_date: str
    source: str
    today: str | None  # override for tests; defaults to real today
    lead_time_days: int
    due: bool
    checklist: list[str]


def node_extract(state: State) -> dict:
    if state.get("raw_text"):
        result = extract(state["raw_text"])
        if result is None:
            return {"doc_type": "generic", "expiry_date": ""}
        doc_type, expiry_date = result
        return {"doc_type": doc_type, "expiry_date": expiry_date, "source": "scan"}
    return {}  # doc_type/expiry_date already provided (manual add)


def node_leadtime(state: State) -> dict:
    days = lead_time_for(state["doc_type"])
    due = is_due(state["expiry_date"], days, state.get("today"))
    return {"lead_time_days": days, "due": due}


def route_after_leadtime(state: State) -> str:
    return "draft" if state["due"] else "skip"


def node_draft(state: State) -> dict:
    today = datetime.date.fromisoformat(state["today"]) if state.get("today") else datetime.date.today()
    expiry = datetime.date.fromisoformat(state["expiry_date"])
    days_until = (expiry - today).days
    return {"checklist": draft_checklist(state["doc_type"], days_until)}


def node_notify(state: State) -> dict:
    steps = "\n".join(f"- {s}" for s in state["checklist"])
    notify(
        f"{state['doc_type']} expiring {state['expiry_date']}",
        f"Renewal window is open (lead time: {state['lead_time_days']}d).\n{steps}",
    )
    return {}


def build_graph():
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
