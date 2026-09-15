"""Self-check: no pytest required, run directly with `python tests/test_expirywatch.py`."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from expirywatch.draft import draft_checklist
from expirywatch.extract import extract
from expirywatch.graph import build_graph
from expirywatch.leadtime import is_due, lead_time_for
from expirywatch.plugins import DRAFTERS, EXTRACTORS, NOTIFIERS


def test_passport_needs_longer_lead_time_than_insurance():
    assert lead_time_for("passport") > lead_time_for("insurance")


def test_is_due_respects_lead_time_window():
    # insurance (14d lead time) expiring in 10 days: due now.
    assert is_due("2026-09-26", lead_time_for("insurance"), today="2026-09-16")
    # passport (90d lead time) expiring in 10 days should ALSO already be due...
    assert is_due("2026-09-26", lead_time_for("passport"), today="2026-09-16")
    # ...but a passport expiring in a year is not due yet.
    assert not is_due("2027-09-26", lead_time_for("passport"), today="2026-09-16")


def test_extract_finds_type_and_date_in_free_text():
    result = extract("Your passport expires on 2027-03-01, please renew soon.")
    assert result == ("passport", "2027-03-01")


def test_extract_returns_none_without_a_date():
    assert extract("no date anywhere in this text") is None


def test_draft_checklist_is_type_specific():
    passport_steps = draft_checklist("passport", days_until_expiry=30)
    warranty_steps = draft_checklist("warranty", days_until_expiry=5)
    assert passport_steps != warranty_steps
    assert len(passport_steps) >= 3


def test_graph_routes_due_item_through_draft_and_notify():
    app = build_graph()
    result = app.invoke({"doc_type": "insurance", "expiry_date": "2026-09-20", "today": "2026-09-16"})
    assert result["due"] is True
    assert len(result["checklist"]) > 0


def test_graph_skips_draft_for_item_not_yet_due():
    app = build_graph()
    result = app.invoke({"doc_type": "passport", "expiry_date": "2027-09-20", "today": "2026-09-16"})
    assert result["due"] is False
    assert "checklist" not in result


def test_builtin_plugins_are_registered():
    assert {"regex", "strict-iso", "hybrid"} <= set(EXTRACTORS)
    assert {"minimal", "template", "hybrid"} <= set(DRAFTERS)
    assert {"console", "webhook"} <= set(NOTIFIERS)


def test_strict_iso_extractor_ignores_fuzzy_dates():
    assert EXTRACTORS["strict-iso"]("insurance due 2026-09-20") == ("insurance", "2026-09-20")
    assert EXTRACTORS["strict-iso"]("insurance due March 20, 2026") is None


def test_minimal_drafter_is_a_single_line():
    assert len(DRAFTERS["minimal"]("passport", 30)) == 1


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} checks passed")
