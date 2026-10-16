"""Scoped API tokens for LLM clients and the other apps. Only a hash is stored; the token is shown once."""

import json
import sqlite3

from .auth import hash_token, new_token
from .privacy import SCOPE_FLOORS


class TokenError(ValueError):
    pass


def create_token(conn: sqlite3.Connection, name: str, scopes: list[str]) -> str:
    name = (name or "").strip()
    if not name:
        raise TokenError("A token needs a name.")
    unknown = [s for s in scopes if s not in SCOPE_FLOORS]
    if not scopes or unknown:
        raise TokenError(f"Unknown or missing scopes: {', '.join(unknown) or 'none given'}")
    token = new_token("ba")
    try:
        conn.execute(
            "INSERT INTO api_tokens (name, token_hash, scopes) VALUES (?, ?, ?)",
            (name, hash_token(token), json.dumps(sorted(set(scopes)))),
        )
    except sqlite3.IntegrityError as exc:
        raise TokenError(f"A token named {name!r} already exists.") from exc
    return token


def lookup_token(conn: sqlite3.Connection, token: str) -> dict | None:
    row = conn.execute(
        "SELECT id, name, scopes FROM api_tokens WHERE token_hash = ? AND revoked_at IS NULL", (hash_token(token),)
    ).fetchone()
    if row is None:
        return None
    conn.execute("UPDATE api_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
    return {"id": row["id"], "name": row["name"], "scopes": json.loads(row["scopes"])}


def list_tokens(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, scopes, created_at, last_used_at, revoked_at FROM api_tokens ORDER BY id"
    ).fetchall()
    return [{**dict(r), "scopes": json.loads(r["scopes"])} for r in rows]


def revoke_token(conn: sqlite3.Connection, token_id: int) -> bool:
    cur = conn.execute(
        "UPDATE api_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE id = ? AND revoked_at IS NULL", (token_id,)
    )
    return cur.rowcount == 1
