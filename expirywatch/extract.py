"""Pull a document type and expiry date out of raw text (an email, a scan's OCR text).

Regex/keyword heuristics by default, no network or API key needed. If
ANTHROPIC_API_KEY is set, an LLM handles the free-form cases the heuristics
miss (odd date phrasing, unlisted document types).
"""
from __future__ import annotations

import datetime
import os
import re

from .leadtime import LEAD_TIMES_DAYS
from .plugins import register_extractor

_ISO_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_TYPE_KEYWORDS = {
    "passport": ["passport"],
    "visa": ["visa"],
    "drivers_license": ["driver's license", "drivers license", "driving licence", "dl renewal"],
    "vehicle_registration": ["vehicle registration", "car registration", "registration renewal"],
    "insurance": ["insurance", "policy"],
    "warranty": ["warranty"],
    "subscription": ["subscription", "membership"],
}

_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%d %B %Y", "%b %d, %Y"]

_DATE_PATTERN = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}/\d{1,2}/\d{4}"
    r"|[A-Z][a-z]+ \d{1,2},? \d{4}"
    r"|\d{1,2} [A-Z][a-z]+ \d{4}"
    r")\b"
)


def _guess_type(text: str) -> str:
    lowered = text.lower()
    for doc_type in LEAD_TIMES_DAYS:
        for kw in _TYPE_KEYWORDS.get(doc_type, []):
            if kw in lowered:
                return doc_type
    return "generic"


def _parse_date(raw: str) -> str | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw.replace(",", ""), fmt.replace(",", "")).date().isoformat()
        except ValueError:
            continue
    return None


def _guess_date(text: str) -> str | None:
    for match in _DATE_PATTERN.finditer(text):
        parsed = _parse_date(match.group(1))
        if parsed:
            return parsed
    return None


def _llm_extract(text: str) -> tuple[str, str] | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model="claude-sonnet-5", max_tokens=100)
        known_types = ", ".join(LEAD_TIMES_DAYS)
        prompt = (
            f"Extract the document type and expiry date from this text.\n\n{text}\n\n"
            f"Reply with exactly two lines: the doc type (one of {known_types}, or "
            "'generic' if none fit) and the expiry date in YYYY-MM-DD format. "
            "No other text."
        )
        response = llm.invoke(prompt).content.strip()
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        if len(lines) >= 2:
            doc_type, date_str = lines[0], lines[1]
            datetime.date.fromisoformat(date_str)  # validate
            return doc_type, date_str
    except Exception:
        pass
    return None


@register_extractor("regex")
def regex_extract(text: str) -> tuple[str, str] | None:
    """Keyword + regex only, no LLM call even if a key is set. Fast, offline, handles common phrasing."""
    date = _guess_date(text)
    if not date:
        return None
    return _guess_type(text), date


@register_extractor("strict-iso")
def strict_iso_extract(text: str) -> tuple[str, str] | None:
    """Only matches exact YYYY-MM-DD dates. For already-structured input (CSV dumps, forms)."""
    match = _ISO_DATE_PATTERN.search(text)
    if not match:
        return None
    return _guess_type(text), match.group(1)


@register_extractor("hybrid")
def extract(text: str) -> tuple[str, str] | None:
    """LLM first if ANTHROPIC_API_KEY is set (handles odd phrasing/unlisted types), else regex fallback."""
    llm_result = _llm_extract(text)
    if llm_result:
        return llm_result
    return regex_extract(text)
