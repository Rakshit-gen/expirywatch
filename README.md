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

## Custom lead times

Add or override lead times without touching code, via a JSON policy file:

```bash
echo '{"gym_membership": 3}' > ~/.expirywatch_policy.json
expirywatch add --type gym_membership --expires 2026-10-01
```

Looked up from `--policy PATH`, then `$EXPIRYWATCH_POLICY`, then
`~/.expirywatch_policy.json`, merged over the built-in table.

## Extending

The extractor, drafter, and notifier are plugins, picked by name:

```bash
expirywatch --list-plugins
# extractors: hybrid, regex, strict-iso
# drafters:   hybrid, minimal, template
# notifiers:  console, webhook

expirywatch --extractor regex --drafter minimal --notifier webhook check
```

`webhook` posts `{"title", "message"}` as JSON to `$EXPIRYWATCH_WEBHOOK_URL`
(a Slack incoming webhook, ntfy.sh, whatever takes a JSON POST).

Register your own before building the graph:

```python
from expirywatch.plugins import register_extractor, register_drafter, register_notifier

@register_extractor("my-extractor")
def my_extractor(text):
    ...
    return (doc_type, expiry_date_iso)  # or None

@register_drafter("my-drafter")
def my_drafter(doc_type, days_until_expiry):
    ...
    return ["step one", "step two"]

@register_notifier("my-notifier")
def my_notifier(title, message):
    ...
```

Then pass `--extractor my-extractor` / `--drafter my-drafter` /
`--notifier my-notifier` on the CLI, or the matching keyword to `build_graph()`
directly.

## Test it yourself

```bash
python tests/test_expirywatch.py
```

No API key or network access required, the LLM step is opt-in only.
