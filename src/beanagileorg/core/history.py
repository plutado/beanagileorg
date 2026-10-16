"""Revision history for any record, read from the change log, with restore of an earlier value.

Every create and update already writes one change-log row per field (old value, new value, who, when). This groups
those rows into revisions and lets you put back an earlier value of a field. Private: it's hidden while presenting
and never available to tokens below the full scope.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from .privacy import Viewer

LONG = 120  # values longer than this are shown as a line-by-line comparison


def _record(entity: str):
    from .records import REGISTRY  # imported here to avoid a circular import

    rec = REGISTRY.get(entity)
    if rec is None:
        raise HTTPException(404, "There's no history for that kind of record.")
    return rec


def decode(field_type: str, raw: str | None):
    if raw is None:
        return None
    if field_type in ("list", "ids", "keys", "json", "int", "number", "bool"):
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw
    return raw


def build_router() -> APIRouter:
    from .app import get_conn, require_full  # imported here to avoid a circular import

    router = APIRouter()

    @router.get("/api/history/{entity}/{record_id}")
    def history(entity: str, record_id: int, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        if viewer.presentation:
            raise HTTPException(403, "History is hidden while presenting.")
        rec = _record(entity)
        rows = conn.execute("SELECT id, at, field, old_value, new_value, source FROM change_log WHERE entity = ? AND record_id = ? ORDER BY id DESC LIMIT 500",
                            (entity, str(record_id))).fetchall()
        revisions = []
        for r in rows:
            if r["field"] not in rec.fields:
                continue
            # One save writes each field once, so a repeated field (or a new time or author) means an earlier save.
            last = revisions[-1] if revisions else None
            if not last or (last["at"], last["source"]) != (r["at"], r["source"]) or any(c["field"] == r["field"] for c in last["changes"]):
                revisions.append({"at": r["at"], "source": r["source"], "changes": []})
            ftype = rec.fields[r["field"]].type
            old, new = decode(ftype, r["old_value"]), decode(ftype, r["new_value"])
            long = any(isinstance(v, str) and (len(v) > LONG or "\n" in v) for v in (old, new))
            revisions[-1]["changes"].append({"change_id": r["id"], "field": r["field"], "old": old, "new": new, "long": long})
        current = rec.fetch(conn, record_id)
        return {"entity": entity, "record_id": record_id, "exists": current is not None, "revisions": revisions}


    @router.post("/api/history/{entity}/{record_id}/restore")
    def restore(entity: str, record_id: int, body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        """Put a field back to the value it had before (which = "old") or after (which = "new") a given change."""
        rec = _record(entity)
        row = conn.execute("SELECT field, old_value, new_value FROM change_log WHERE id = ? AND entity = ? AND record_id = ?",
                           (body.get("change_id"), entity, str(record_id))).fetchone()
        if row is None:
            raise HTTPException(404, "That change isn't in this record's history.")
        if row["field"] not in rec.fields:
            raise HTTPException(400, "That field no longer exists.")
        if rec.fetch(conn, record_id) is None:
            raise HTTPException(404, "This record was deleted, so there's nothing to restore into.")
        raw = row["new_value"] if body.get("which") == "new" else row["old_value"]
        value = decode(rec.fields[row["field"]].type, raw)
        updated = rec.update(conn, record_id, {row["field"]: value}, viewer.source)
        return rec.visible(updated, viewer)

    return router
