"""Surface a reminder: always to stdout, best-effort as a native OS notification."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request

from .plugins import register_notifier


@register_notifier("console")
def notify(title: str, message: str) -> None:
    print(f"\n[{title}]\n{message}")

    if sys.platform == "darwin":
        script = f'display notification {message!r} with title {title!r}'
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass  # ponytail: best-effort only, stdout above is the reliable path


@register_notifier("webhook")
def webhook_notify(title: str, message: str) -> None:
    """POST {title, message} as JSON to $EXPIRYWATCH_WEBHOOK_URL (e.g. a Slack incoming webhook, ntfy.sh)."""
    print(f"\n[{title}]\n{message}")

    url = os.environ.get("EXPIRYWATCH_WEBHOOK_URL")
    if not url:
        return
    body = json.dumps({"title": title, "message": message}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except (OSError, ValueError):
        pass  # ponytail: best-effort only, stdout above is the reliable path
