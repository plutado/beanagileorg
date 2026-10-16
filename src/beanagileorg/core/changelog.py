"""Shared change log: every data change records what changed and who made it (me or a named token)."""

import json
import sqlite3


def _text(value) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value)


def record_changes(
    conn: sqlite3.Connection, entity: str, record_id, old: dict | None, new: dict | None, source: str
) -> int:
    """Log one row per changed field. A create has old=None; a delete has new=None."""
    old, new = old or {}, new or {}
    count = 0
    for name in sorted(set(old) | set(new)):
        if name == "id" or old.get(name) == new.get(name):
            continue
        conn.execute(
            "INSERT INTO change_log (entity, record_id, field, old_value, new_value, source) VALUES (?, ?, ?, ?, ?, ?)",
            (entity, str(record_id), name, _text(old.get(name)), _text(new.get(name)), source),
        )
        count += 1
    return count


def recent_changes(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    rows = conn.execute(
        "SELECT at, entity, record_id, field, old_value, new_value, source FROM change_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
