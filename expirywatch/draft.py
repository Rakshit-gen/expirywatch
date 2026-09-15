"""Draft the concrete renewal checklist for a document, not just 'it's expiring'."""
from __future__ import annotations

import os

_TEMPLATES = {
    "passport": [
        "Check passport photo and validity requirements for your destination country",
        "Book an appointment at your nearest passport office or consulate",
        "Prepare 2 passport photos, your current passport, and the application form",
        "Pay the renewal fee and track processing time",
    ],
    "visa": [
        "Confirm which visa category you're renewing and required documents",
        "Check processing time at your consulate or embassy",
        "Prepare proof of purpose (employment, enrollment, etc.) and passport validity",
        "Submit the application before your current visa's grace period ends",
    ],
    "drivers_license": [
        "Check if renewal is available online or requires an in-person visit",
        "Confirm any required vision test or documentation",
        "Book a DMV/licensing authority appointment if needed",
        "Pay the renewal fee",
    ],
    "vehicle_registration": [
        "Confirm smog/emissions check requirements, if any",
        "Gather proof of insurance",
        "Renew online or at your local registration office",
        "Update your registration sticker/tag",
    ],
    "insurance": [
        "Compare your current premium against current market rates",
        "Contact your provider to confirm renewal terms and any changes",
        "Decide: renew, negotiate, or switch providers",
        "Confirm renewal in writing before the old policy lapses",
    ],
    "warranty": [
        "Locate your original receipt and warranty terms",
        "Confirm whether registration or a claim is required before expiry",
        "File a claim now if there's an unresolved issue",
    ],
    "subscription": [
        "Decide whether you still use this subscription",
        "Cancel or downgrade before the renewal date if not",
        "Check for an annual-billing discount if you're keeping it",
    ],
    "generic": [
        "Confirm the exact renewal deadline",
        "Locate the account, policy, or reference number",
        "Contact the provider to renew or cancel",
        "Get confirmation in writing",
    ],
}


def _llm_draft(doc_type: str, days_until_expiry: int) -> list[str] | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model="claude-sonnet-5", max_tokens=300)
        prompt = (
            f"Write a 3-5 step renewal checklist for a '{doc_type}' document "
            f"expiring in {days_until_expiry} days. One short step per line, "
            "no numbering, no extra text."
        )
        response = llm.invoke(prompt).content.strip()
        steps = [line.strip("- ").strip() for line in response.splitlines() if line.strip()]
        return steps or None
    except Exception:
        return None


def draft_checklist(doc_type: str, days_until_expiry: int) -> list[str]:
    return _llm_draft(doc_type, days_until_expiry) or _TEMPLATES.get(doc_type, _TEMPLATES["generic"])
