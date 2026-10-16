"""A record type with typed, privacy-tagged fields and a standard REST router.

Every app entity goes through here, so reads are filtered by the viewer's privacy floor,
writes are validated and checked against a scope, and every change lands in the change log.
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field

from fastapi import APIRouter, Body, Depends, HTTPException

from .app import get_conn, get_viewer
from .changelog import record_changes
from .db import transaction
from .privacy import Level, Viewer, filter_record, register

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,19}-\d+$")  # Jira-style keys such as ABC-123


@dataclass(frozen=True)
class Field:
    type: str  # text | date | int | number | bool | list (of text) | ids (list of record ids) | json (an object)
    level: Level = Level.PRIVATE
    required: bool = False
    choices: tuple[str, ...] | None = None
    default: object = None


@dataclass
class Record:
    entity: str
    table: str
    path: str
    fields: dict[str, Field]
    write_scope: str = "full"
    order_by: str = "id"
    computed: dict[str, tuple[str, Level]] = field(default_factory=dict)
    ceiling_sql: str | None = None
    hide_when_empty: bool = False

    def __post_init__(self) -> None:
        levels = {name: f.level for name, f in self.fields.items()}
        levels.update({name: level for name, (_, level) in self.computed.items()})
        register(self.entity, levels)

    # ---- reading ----

    def _select(self) -> str:
        cols = ["id", *self.fields, *(f"{expr} AS {name}" for name, (expr, _) in self.computed.items())]
        if self.ceiling_sql:
            cols.append(f"{self.ceiling_sql} AS privacy_ceiling")
        return f"SELECT {', '.join(cols)} FROM {self.table}"

    def _decode(self, row: sqlite3.Row) -> dict:
        rec = dict(row)
        for name, f in self.fields.items():
            if f.type in ("list", "ids", "keys"):
                rec[name] = json.loads(rec[name]) if rec[name] else []
            elif f.type == "json":
                rec[name] = json.loads(rec[name]) if rec[name] else {}
            elif f.type == "bool":
                rec[name] = bool(rec[name])
        return rec

    def fetch(self, conn: sqlite3.Connection, record_id: int) -> dict | None:
        row = conn.execute(f"{self._select()} WHERE id = ?", (record_id,)).fetchone()
        return self._decode(row) if row else None

    def fetch_all(self, conn: sqlite3.Connection, where: str = "", params: tuple = ()) -> list[dict]:
        sql = f"{self._select()} {('WHERE ' + where) if where else ''} ORDER BY {self.order_by}"
        return [self._decode(r) for r in conn.execute(sql, params)]

    def visible(self, rec: dict, viewer: Viewer) -> dict | None:
        shown = filter_record(self.entity, rec, viewer.floor)
        if shown is None:
            return None
        if self.hide_when_empty and viewer.floor > Level.PRIVATE and set(shown) <= {"id"}:
            return None
        if viewer.floor == Level.PRIVATE:
            shown.pop("privacy_ceiling", None)
        return shown

    def visible_all(self, records: list[dict], viewer: Viewer) -> list[dict]:
        return [r for r in (self.visible(rec, viewer) for rec in records) if r is not None]

    # ---- writing ----

    def validate(self, data: dict, partial: bool) -> dict:
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise HTTPException(400, f"Unknown fields: {', '.join(unknown)}")
        out: dict = {}
        for name, f in self.fields.items():
            if name not in data:
                if not partial:
                    if f.required:
                        raise HTTPException(400, f"{name} is required.")
                    if f.default is not None:
                        out[name] = f.default
                continue
            out[name] = self._check(name, f, data[name])
        return out

    @staticmethod
    def _check(name: str, f: Field, value):
        if value is None or value == "":
            if f.required:
                raise HTTPException(400, f"{name} is required.")
            return {"list": [], "ids": [], "keys": [], "json": {}, "bool": False}.get(f.type)
        if f.type in ("text", "date"):
            if not isinstance(value, str):
                raise HTTPException(400, f"{name} must be text.")
            value = value.strip()
            if f.type == "date" and not DATE_RE.match(value):
                raise HTTPException(400, f"{name} must be a date like 2026-01-31.")
            if f.choices and value not in f.choices:
                raise HTTPException(400, f"{name} must be one of: {', '.join(f.choices)}")
            return value
        if f.type == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise HTTPException(400, f"{name} must be a whole number.")
            return value
        if f.type == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HTTPException(400, f"{name} must be a number.")
            return float(value)
        if f.type == "bool":
            if not isinstance(value, bool):
                raise HTTPException(400, f"{name} must be true or false.")
            return value
        if f.type == "ids":
            if not isinstance(value, list) or not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
                raise HTTPException(400, f"{name} must be a list of ids.")
            return list(dict.fromkeys(value))
        if f.type == "json":
            if not isinstance(value, dict):
                raise HTTPException(400, f"{name} must be an object.")
            return value
        if f.type in ("key", "keys"):
            # One issue key, or several (a list, or text split on commas and spaces); stored upper case, no repeats.
            parts = value if isinstance(value, list) else re.split(r"[\s,;]+", value) if isinstance(value, str) else None
            if parts is None or not all(isinstance(v, str) for v in parts):
                raise HTTPException(400, f"{name} must be issue keys such as ABC-123.")
            keys = list(dict.fromkeys(v.strip().upper() for v in parts if v.strip()))
            bad = [k for k in keys if not ISSUE_KEY_RE.match(k)]
            if bad:
                raise HTTPException(400, f"{', '.join(bad)} doesn't look like an issue key such as ABC-123.")
            if f.type == "key":
                if len(keys) > 1:
                    raise HTTPException(400, f"{name} takes one issue key.")
                return keys[0] if keys else None
            return keys
        if f.type == "list":
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise HTTPException(400, f"{name} must be a list of text.")
            return [v.strip() for v in value if v.strip()]
        raise HTTPException(500, f"Unsupported field type for {name}.")

    def _encode(self, values: dict) -> dict:
        out = {}
        for name, value in values.items():
            f = self.fields[name]
            if f.type in ("list", "ids", "keys", "json"):
                out[name] = json.dumps(value)
            else:
                out[name] = int(value) if f.type == "bool" else value
        return out

    def _plain(self, rec: dict | None) -> dict | None:
        return None if rec is None else {k: rec.get(k) for k in self.fields}

    def create(self, conn: sqlite3.Connection, data: dict, source: str) -> dict:
        values = self.validate(data, partial=False)
        enc = self._encode(values)
        with transaction(conn):
            if enc:
                cols = ", ".join(enc)
                cur = conn.execute(
                    f"INSERT INTO {self.table} ({cols}) VALUES ({', '.join('?' for _ in enc)})", tuple(enc.values())
                )
            else:
                cur = conn.execute(f"INSERT INTO {self.table} DEFAULT VALUES")
            rec = self.fetch(conn, cur.lastrowid)
            record_changes(conn, self.entity, rec["id"], None, self._plain(rec), source)
        return rec

    def update(self, conn: sqlite3.Connection, record_id: int, data: dict, source: str) -> dict | None:
        values = self.validate(data, partial=True)
        with transaction(conn):
            old = self.fetch(conn, record_id)
            if old is None:
                return None
            if values:
                enc = self._encode(values)
                conn.execute(
                    f"UPDATE {self.table} SET {', '.join(f'{c} = ?' for c in enc)} WHERE id = ?",
                    (*enc.values(), record_id),
                )
            new = self.fetch(conn, record_id)
            record_changes(conn, self.entity, record_id, self._plain(old), self._plain(new), source)
        return new

    def delete(self, conn: sqlite3.Connection, record_id: int, source: str) -> bool:
        with transaction(conn):
            old = self.fetch(conn, record_id)
            if old is None:
                return False
            conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (record_id,))
            record_changes(conn, self.entity, record_id, self._plain(old), None, source)
        return True

    # ---- HTTP ----

    def router(self) -> APIRouter:
        r = APIRouter()

        def check_write(viewer: Viewer) -> None:
            if not viewer.has_scope(self.write_scope):
                raise HTTPException(403, f"Changing {self.entity} records needs the {self.write_scope} scope.")

        def shown_or_404(rec: dict | None, viewer: Viewer) -> dict:
            shown = self.visible(rec, viewer) if rec else None
            if shown is None:
                raise HTTPException(404, f"No {self.entity} with that id.")
            return shown

        @r.get(self.path)
        def list_records(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
            return self.visible_all(self.fetch_all(conn), viewer)

        @r.get(self.path + "/{record_id}")
        def get_record(record_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
            return shown_or_404(self.fetch(conn, record_id), viewer)

        @r.post(self.path, status_code=201)
        def create_record(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
            check_write(viewer)
            try:
                rec = self.create(conn, body, viewer.source)
            except sqlite3.IntegrityError as exc:
                raise HTTPException(400, "That refers to a record that doesn't exist.") from exc
            return self.visible(rec, viewer) or {"id": rec["id"]}

        @r.patch(self.path + "/{record_id}")
        def update_record(
            record_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)
        ):
            check_write(viewer)
            try:
                rec = self.update(conn, record_id, body, viewer.source)
            except sqlite3.IntegrityError as exc:
                raise HTTPException(400, "That refers to a record that doesn't exist.") from exc
            if rec is None:
                raise HTTPException(404, f"No {self.entity} with that id.")
            return self.visible(rec, viewer) or {"id": rec["id"]}

        @r.delete(self.path + "/{record_id}", status_code=204)
        def delete_record(record_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
            check_write(viewer)
            if not self.delete(conn, record_id, viewer.source):
                raise HTTPException(404, f"No {self.entity} with that id.")

        return r
