"""Registries for the swappable pieces: extractors, drafters, notifiers.

Built-in implementations register themselves on import (see extract.py,
draft.py, notify.py). To add your own, register before building the graph:

    from expirywatch.plugins import register_notifier

    @register_notifier("slack")
    def slack_notify(title, message):
        ...

Then pass --notifier slack on the CLI, or notifier="slack" to build_graph().
"""
from __future__ import annotations

from typing import Callable

EXTRACTORS: dict[str, Callable] = {}
DRAFTERS: dict[str, Callable] = {}
NOTIFIERS: dict[str, Callable] = {}


def register_extractor(name: str):
    def deco(fn: Callable) -> Callable:
        EXTRACTORS[name] = fn
        return fn

    return deco


def register_drafter(name: str):
    def deco(fn: Callable) -> Callable:
        DRAFTERS[name] = fn
        return fn

    return deco


def register_notifier(name: str):
    def deco(fn: Callable) -> Callable:
        NOTIFIERS[name] = fn
        return fn

    return deco
