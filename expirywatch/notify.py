"""Surface a reminder: always to stdout, best-effort as a native OS notification."""
from __future__ import annotations

import subprocess
import sys

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
