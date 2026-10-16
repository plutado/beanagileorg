"""The single export path: filter to exportable fields, preview, then log what went out."""

import hashlib
import json
import sqlite3

from .privacy import Level, filter_records


def prepare_export(entity: str, records: list[dict]) -> list[dict]:
    return filter_records(entity, records, Level.EXPORTABLE)


def log_export(conn: sqlite3.Connection, kind: str, title: str, records: list[dict], source: str) -> dict:
    content = json.dumps(records, sort_keys=True, default=str)
    digest = hashlib.sha256(content.encode()).hexdigest()
    conn.execute(
        "INSERT INTO export_log (kind, title, record_count, content_sha256, source) VALUES (?, ?, ?, ?, ?)",
        (kind, title, len(records), digest, source),
    )
    return {"kind": kind, "title": title, "record_count": len(records), "content_sha256": digest}


def recent_exports(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        "SELECT at, kind, title, record_count, content_sha256, source FROM export_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
