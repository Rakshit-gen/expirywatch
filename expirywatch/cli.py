from __future__ import annotations

import argparse
import datetime
import sys

from .graph import build_graph
from .leadtime import load_policy
from .plugins import DRAFTERS, EXTRACTORS, NOTIFIERS
from .store import add_document, connect, list_documents, mark_notified


def _today(args: argparse.Namespace) -> str:
    return args.today or datetime.date.today().isoformat()


def _build_graph(args: argparse.Namespace):
    return build_graph(
        extractor=args.extractor,
        drafter=args.drafter,
        notifier=args.notifier,
        policy=load_policy(args.policy),
    )


def cmd_add(args: argparse.Namespace) -> int:
    conn = connect()
    graph = _build_graph(args)
    result = graph.invoke({"doc_type": args.type, "expiry_date": args.expires, "today": args.today})
    doc_id = add_document(conn, args.type, args.expires, source="manual")
    if result.get("due"):
        mark_notified(conn, doc_id, _today(args))
    print(f"Tracking {args.type}, expires {args.expires} (id={doc_id}).")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    text = open(args.file).read()
    graph = _build_graph(args)
    result = graph.invoke({"raw_text": text, "today": args.today})
    if not result.get("expiry_date"):
        print("Could not find a date in that text.", file=sys.stderr)
        return 1

    conn = connect()
    doc_id = add_document(conn, result["doc_type"], result["expiry_date"], source="scan")
    if result.get("due"):
        mark_notified(conn, doc_id, _today(args))
    print(f"Tracking {result['doc_type']}, expires {result['expiry_date']} (id={doc_id}).")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    conn = connect()
    graph = _build_graph(args)
    due_count = 0
    for doc in list_documents(conn, only_unnotified=True):
        result = graph.invoke(
            {"doc_type": doc.doc_type, "expiry_date": doc.expiry_date, "today": args.today}
        )
        if result.get("due"):
            due_count += 1
            mark_notified(conn, doc.id, _today(args))
    if due_count == 0:
        print("Nothing due yet.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = connect()
    for doc in list_documents(conn):
        status = "notified" if doc.notified_at else "tracking"
        print(f"[{doc.id}] {doc.doc_type:<22} expires {doc.expiry_date}  ({status})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="expirywatch", description="Type-aware deadline tracking for real-world documents.")
    parser.add_argument("--today", help=argparse.SUPPRESS)  # override for testing
    parser.add_argument("--extractor", default="hybrid", choices=sorted(EXTRACTORS), help="default: hybrid")
    parser.add_argument("--drafter", default="hybrid", choices=sorted(DRAFTERS), help="default: hybrid")
    parser.add_argument("--notifier", default="console", choices=sorted(NOTIFIERS), help="default: console")
    parser.add_argument("--policy", help="JSON file of {doc_type: lead_time_days} overrides")
    parser.add_argument("--list-plugins", action="store_true", help="list registered extractors/drafters/notifiers and exit")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="track a document directly")
    p_add.add_argument("--type", required=True, help="e.g. passport, visa, drivers_license, insurance, warranty")
    p_add.add_argument("--expires", required=True, help="YYYY-MM-DD")
    p_add.set_defaults(func=cmd_add)

    p_scan = sub.add_parser("scan", help="extract type+expiry from a text file (email, OCR dump)")
    p_scan.add_argument("file")
    p_scan.set_defaults(func=cmd_scan)

    p_check = sub.add_parser("check", help="notify for anything now inside its reminder window")
    p_check.set_defaults(func=cmd_check)

    p_list = sub.add_parser("list", help="list tracked documents")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)

    if args.list_plugins:
        print("extractors:", ", ".join(sorted(EXTRACTORS)))
        print("drafters:  ", ", ".join(sorted(DRAFTERS)))
        print("notifiers: ", ", ".join(sorted(NOTIFIERS)))
        return 0

    if not args.command:
        parser.error("a command is required (add/scan/check/list)")

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
