"""Local SQLite storage for tracked documents. Stdlib only."""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass

DEFAULT_DB_PATH = os.path.expanduser("~/.expirywatch.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    source TEXT,
    notified_at TEXT
);
"""


@dataclass
class Document:
    id: int
    doc_type: str
    expiry_date: str
    source: str | None
    notified_at: str | None


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def add_document(conn: sqlite3.Connection, doc_type: str, expiry_date: str, source: str = "manual") -> int:
    cur = conn.execute(
        "INSERT INTO documents (doc_type, expiry_date, source) VALUES (?, ?, ?)",
        (doc_type, expiry_date, source),
    )
    conn.commit()
    return cur.lastrowid


def list_documents(conn: sqlite3.Connection, only_unnotified: bool = False) -> list[Document]:
    query = "SELECT id, doc_type, expiry_date, source, notified_at FROM documents"
    if only_unnotified:
        query += " WHERE notified_at IS NULL"
    query += " ORDER BY expiry_date ASC"
    return [Document(*row) for row in conn.execute(query).fetchall()]


def mark_notified(conn: sqlite3.Connection, doc_id: int, notified_at: str) -> None:
    conn.execute("UPDATE documents SET notified_at = ? WHERE id = ?", (notified_at, doc_id))
    conn.commit()
