"""SQLite storage with numbered migrations. One connection per request keeps threading simple."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

CORE_MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password_hash TEXT NOT NULL,
            totp_secret TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE sessions (
            token_hash TEXT PRIMARY KEY,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            presentation INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE api_tokens (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            token_hash TEXT NOT NULL UNIQUE,
            scopes TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_used_at TEXT,
            revoked_at TEXT
        );
        CREATE TABLE change_log (
            id INTEGER PRIMARY KEY,
            at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            entity TEXT NOT NULL,
            record_id TEXT NOT NULL,
            field TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            source TEXT NOT NULL
        );
        CREATE INDEX change_log_record ON change_log (entity, record_id);
        CREATE TABLE export_log (
            id INTEGER PRIMARY KEY,
            at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            source TEXT NOT NULL
        );
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """,
    ),
]


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @contextmanager
    def session(self):
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def migrate(conn: sqlite3.Connection, namespace: str, migrations: list[tuple[int, str]]) -> list[int]:
    """Apply any migrations not yet recorded for this namespace. Each runs in its own transaction."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            namespace TEXT NOT NULL,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (namespace, version)
        )"""
    )
    applied = {
        row[0] for row in conn.execute("SELECT version FROM schema_migrations WHERE namespace = ?", (namespace,))
    }
    newly = []
    for version, sql in sorted(migrations):
        if version in applied:
            continue
        ns = namespace.replace("'", "''")
        conn.executescript(
            f"BEGIN;\n{sql}\nINSERT INTO schema_migrations (namespace, version) VALUES ('{ns}', {int(version)});\nCOMMIT;"
        )
        newly.append(version)
    return newly
