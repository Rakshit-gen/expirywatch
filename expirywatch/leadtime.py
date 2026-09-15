"""How much lead time each document type actually needs before it expires.

A flat "remind me 30 days before" misses both ends: a passport renewal can
take months, a warranty claim window closes in days.
"""
from __future__ import annotations

import datetime
import json
import os

LEAD_TIMES_DAYS = {
    "passport": 90,
    "visa": 60,
    "drivers_license": 30,
    "vehicle_registration": 30,
    "insurance": 14,
    "warranty": 7,
    "subscription": 7,
    "generic": 14,
}

DEFAULT_LEAD_TIME_DAYS = LEAD_TIMES_DAYS["generic"]


def load_policy(path: str | None = None) -> dict[str, int]:
    """Merge user-defined lead times over the built-in defaults.

    Reads from `path`, then $EXPIRYWATCH_POLICY, then ~/.expirywatch_policy.json
    if present. A policy file is just {"doc_type": lead_time_days, ...}; it can
    add new types or override existing ones without touching this module.
    """
    policy = dict(LEAD_TIMES_DAYS)
    candidate = path or os.environ.get("EXPIRYWATCH_POLICY") or os.path.expanduser("~/.expirywatch_policy.json")
    if os.path.exists(candidate):
        with open(candidate) as f:
            policy.update(json.load(f))
    return policy


def lead_time_for(doc_type: str, policy: dict[str, int] | None = None) -> int:
    table = policy if policy is not None else LEAD_TIMES_DAYS
    return table.get(doc_type, table.get("generic", DEFAULT_LEAD_TIME_DAYS))


def is_due(expiry_date: str, lead_time_days: int, today: str | None = None) -> bool:
    expiry = datetime.date.fromisoformat(expiry_date)
    today_date = datetime.date.fromisoformat(today) if today else datetime.date.today()
    remind_from = expiry - datetime.timedelta(days=lead_time_days)
    return today_date >= remind_from
