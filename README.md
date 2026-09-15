# expirywatch

Deadline reminders that are the same 30 days flat for everything miss both
ends: a passport renewal can take months to process, a warranty claim window
closes in days. `expirywatch` tracks real-world document deadlines with a
lead time matched to the document type, and instead of just pinging you,
drafts the actual steps to renew.

Built as a [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph`:
extract (type + date) then a lead-time lookup then a conditional branch
(inside the reminder window or not) then, if due, draft a checklist and
notify. Heuristic extraction and static checklists by default, refined by an
LLM call if `ANTHROPIC_API_KEY` is set. Storage is local SQLite, nothing
leaves your machine unless you opt into the LLM step.

## Install

```bash
pip install -e .
# optional, for LLM-assisted extraction and tailored checklists:
pip install -e ".[llm]"
```

## Use

```bash
# track something directly
expirywatch add --type passport --expires 2027-06-01

# or pull it out of pasted email/OCR text
expirywatch scan renewal_email.txt

# see what you're tracking
expirywatch list

# run this on a cron/launchd schedule; it only speaks up when something
# has actually entered its reminder window
expirywatch check
```

```
[insurance expiring 2026-09-20]
Renewal window is open (lead time: 14d).
- Compare your current premium against current market rates
- Contact your provider to confirm renewal terms and any changes
- Decide: renew, negotiate, or switch providers
- Confirm renewal in writing before the old policy lapses
```

## Lead times

| Document type | Reminder window |
|---|---|
| passport | 90 days |
| visa | 60 days |
| drivers_license / vehicle_registration | 30 days |
| insurance | 14 days |
| generic (unrecognized type) | 14 days |
| warranty / subscription | 7 days |

## Test it yourself

```bash
python tests/test_expirywatch.py
```

No API key or network access required, the LLM step is opt-in only.
