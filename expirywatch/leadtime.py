"""How much lead time each document type actually needs before it expires.

A flat "remind me 30 days before" misses both ends: a passport renewal can
take months, a warranty claim window closes in days.
"""
from __future__ import annotations

import datetime

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


def lead_time_for(doc_type: str) -> int:
    return LEAD_TIMES_DAYS.get(doc_type, DEFAULT_LEAD_TIME_DAYS)


def is_due(expiry_date: str, lead_time_days: int, today: str | None = None) -> bool:
    expiry = datetime.date.fromisoformat(expiry_date)
    today_date = datetime.date.fromisoformat(today) if today else datetime.date.today()
    remind_from = expiry - datetime.timedelta(days=lead_time_days)
    return today_date >= remind_from
