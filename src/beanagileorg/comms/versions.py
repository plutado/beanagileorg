"""Deck versions and the draft-to-presented workflow.

A version is a complete snapshot of a deck (its settings and every slide), numbered per deck. Versions are saved on
request with a note, and automatically when a deck goes to review, is approved or presented, and before a restore.
An approved or presented deck is locked: editing it starts a new draft, so what was approved stays exactly as it was.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models

router = APIRouter()
SLIDE_FIELDS = ("position", "layout", "content", "notes", "transition", "hidden")
DECK_FIELDS = ("title", "theme", "transition")
# from -> allowed next statuses
FLOW = {
    "draft": ("in review", "approved"),
    "in review": ("draft", "approved"),
    "approved": ("presented", "draft"),
    "presented": ("presented", "draft"),
}
LOCKED = ("approved", "presented")


def require_write(viewer: Viewer) -> None:
    if not viewer.has_scope("full"):
        raise HTTPException(403, "This needs the full scope.")


def deck_or_404(conn, deck_id: int) -> dict:
    deck = models.decks.fetch(conn, deck_id)
    if deck is None:
        raise HTTPException(404, "No deck with that id.")
    return deck


def ensure_editable(conn, deck_id: int) -> None:
    """Called before any change to a deck's content."""
    deck = deck_or_404(conn, deck_id)
    if deck["status"] in LOCKED:
        raise HTTPException(409, f"This deck is {deck['status']}. Start a new draft to change it, so the {deck['status']} version stays as it was.")


def snapshot(conn, deck_id: int) -> dict:
    deck = deck_or_404(conn, deck_id)
    slides = models.slides.fetch_all(conn, "deck_id = ?", (deck_id,))
    return {"deck": {k: deck[k] for k in DECK_FIELDS}, "slides": [{"id": s["id"], **{k: s[k] for k in SLIDE_FIELDS}} for s in slides]}


def save(conn, deck_id: int, source: str, kind: str = "saved", label: str | None = None, note: str | None = None) -> dict:
    snap = snapshot(conn, deck_id)
    status = models.decks.fetch(conn, deck_id)["status"]
    number = conn.execute("SELECT COALESCE(MAX(number), 0) + 1 FROM deck_versions WHERE deck_id = ?", (deck_id,)).fetchone()[0]
    conn.execute("INSERT INTO deck_versions (deck_id, number, label, kind, status, note, snapshot, slide_count, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (deck_id, number, label, kind, status, note, json.dumps(snap), len(snap["slides"]), source))
    return {"number": number, "kind": kind, "label": label, "status": status, "slide_count": len(snap["slides"])}


def _version(conn, deck_id: int, number: int) -> dict:
    row = conn.execute("SELECT * FROM deck_versions WHERE deck_id = ? AND number = ?", (deck_id, number)).fetchone()
    if row is None:
        raise HTTPException(404, "No such version.")
    return {**dict(row), "snapshot": json.loads(row["snapshot"])}


@router.get("/api/decks/{deck_id}/versions")
def list_versions(deck_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    deck = models.decks.visible(deck_or_404(conn, deck_id), viewer)
    rows = conn.execute("SELECT number, label, kind, status, note, slide_count, saved_at, source FROM deck_versions WHERE deck_id = ? ORDER BY number DESC", (deck_id,)).fetchall()
    return {"deck": deck, "versions": [dict(r) for r in rows], "next": list(FLOW[deck["status"]])}


@router.post("/api/decks/{deck_id}/versions", status_code=201)
def save_version(deck_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    deck_or_404(conn, deck_id)
    return save(conn, deck_id, viewer.source, "saved", (body.get("label") or "").strip() or None, (body.get("note") or "").strip() or None)


@router.post("/api/decks/{deck_id}/status")
def change_status(deck_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Move the deck along: draft -> in review -> approved -> presented. Each step is snapshotted; going back to draft unlocks it."""
    require_write(viewer)
    deck = deck_or_404(conn, deck_id)
    to = body.get("status")
    if to not in FLOW[deck["status"]]:
        allowed = ", ".join(FLOW[deck["status"]])
        raise HTTPException(400, f"A {deck['status']} deck can move to: {allowed}.")
    changes = {"status": to}
    if to == "presented":
        changes.update({"presented_on": body.get("presented_on") or None, "audience": body.get("audience") or deck["audience"]})
    models.decks.update(conn, deck_id, changes, viewer.source)
    kind = {"in review": "sent for review", "approved": "approved", "presented": "presented", "draft": "new draft" if deck["status"] in LOCKED else "changes requested"}[to]
    version = save(conn, deck_id, viewer.source, kind, body.get("label"), body.get("note"))
    return {"status": to, "version": version}


def _full(conn, deck_id: int, snap: dict, viewer: Viewer) -> dict:
    deck = models.decks.visible(deck_or_404(conn, deck_id), viewer)
    return {"deck": {**deck, **snap["deck"]}, "slides": sorted(snap["slides"], key=lambda s: (s["position"], s["id"])),
            "media": models.media.visible_all(models.media.fetch_all(conn), viewer)}


@router.get("/api/decks/{deck_id}/versions/{number}/full")
def version_full(deck_id: int, number: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The same shape as /full, so a saved version can be previewed or presented."""
    v = _version(conn, deck_id, number)
    return {**_full(conn, deck_id, v["snapshot"], viewer), "version": {k: v[k] for k in ("number", "label", "kind", "status", "note", "saved_at")}}


def _summary(slide: dict) -> str:
    c = slide.get("content") or {}
    return c.get("heading") or c.get("quote") or c.get("number") or slide["layout"]


@router.get("/api/decks/{deck_id}/compare")
def compare(deck_id: int, a: int, b: str = "current", viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """What changed from version a to version b (or to the current deck): slides added, removed, changed and moved."""
    old = _version(conn, deck_id, a)["snapshot"]
    new = snapshot(conn, deck_id) if b == "current" else _version(conn, deck_id, int(b))["snapshot"]
    before = {s["id"]: s for s in old["slides"]}
    after = {s["id"]: s for s in new["slides"]}
    order_before = [s["id"] for s in sorted(old["slides"], key=lambda s: (s["position"], s["id"]))]
    order_after = [s["id"] for s in sorted(new["slides"], key=lambda s: (s["position"], s["id"]))]
    changed = []
    for sid in [x for x in order_after if x in before]:
        fields = []
        o, n = before[sid], after[sid]
        if o["layout"] != n["layout"]:
            fields.append("layout")
        keys = sorted(set(o["content"] or {}) | set(n["content"] or {}))
        fields += [f"content: {k}" for k in keys if (o["content"] or {}).get(k) != (n["content"] or {}).get(k)]
        fields += [k for k in ("notes", "transition", "hidden") if o[k] != n[k]]
        if fields:
            changed.append({"id": sid, "title": _summary(n), "position": order_after.index(sid) + 1, "fields": fields})
    common_before = [x for x in order_before if x in after]
    common_after = [x for x in order_after if x in before]
    moved = [{"id": x, "title": _summary(after[x]), "from": order_before.index(x) + 1, "to": order_after.index(x) + 1}
             for x in common_after if common_before.index(x) != common_after.index(x)]
    return {
        "a": a, "b": b,
        "deck": [k for k in DECK_FIELDS if old["deck"].get(k) != new["deck"].get(k)],
        "added": [{"id": x, "title": _summary(after[x]), "position": order_after.index(x) + 1} for x in order_after if x not in before],
        "removed": [{"id": x, "title": _summary(before[x]), "position": order_before.index(x) + 1} for x in order_before if x not in after],
        "changed": changed, "moved": moved,
    }


@router.post("/api/decks/{deck_id}/versions/{number}/restore")
def restore(deck_id: int, number: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Bring back a version. The current state is saved first, and the deck goes back to draft."""
    require_write(viewer)
    target = _version(conn, deck_id, number)["snapshot"]
    saved = save(conn, deck_id, viewer.source, "before restore", note=f"Saved automatically before restoring version {number}")
    keep = {s["id"] for s in target["slides"]}
    for s in models.slides.fetch_all(conn, "deck_id = ?", (deck_id,)):
        if s["id"] not in keep:
            models.slides.delete(conn, s["id"], viewer.source)
    for s in target["slides"]:
        values = {k: s[k] for k in SLIDE_FIELDS}
        current = models.slides.fetch(conn, s["id"])
        if current and current["deck_id"] == deck_id:
            models.slides.update(conn, s["id"], values, viewer.source)
        elif current is None:
            # Put it back under its old id, so later comparisons still line up.
            conn.execute("INSERT INTO slides (id, deck_id, position, layout, content, notes, transition, hidden) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (s["id"], deck_id, s["position"], s["layout"], json.dumps(s["content"] or {}), s["notes"], s["transition"], int(bool(s["hidden"]))))
        else:
            models.slides.create(conn, {"deck_id": deck_id, **values}, viewer.source)
    models.decks.update(conn, deck_id, {**target["deck"], "status": "draft"}, viewer.source)
    return {"restored": number, "saved_first": saved["number"]}


@router.post("/api/decks/{deck_id}/copy", status_code=201)
def copy(deck_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A separate deck to adapt, say for another audience. It starts as a draft with its own history."""
    require_write(viewer)
    src = deck_or_404(conn, deck_id)
    title = (body.get("title") or "").strip() or f"{src['title']} (copy)"
    latest = conn.execute("SELECT MAX(number) FROM deck_versions WHERE deck_id = ?", (deck_id,)).fetchone()[0]
    new = models.decks.create(conn, {"title": title, "theme": src["theme"], "transition": src["transition"],
                                     "copied_from": f"{src['title']}" + (f", version {latest}" if latest else "")}, viewer.source)
    for s in models.slides.fetch_all(conn, "deck_id = ?", (deck_id,)):
        models.slides.create(conn, {"deck_id": new["id"], **{k: s[k] for k in SLIDE_FIELDS}}, viewer.source)
    save(conn, new["id"], viewer.source, "copied", note=f"Copied from {src['title']}")
    return models.decks.fetch(conn, new["id"])


# ---- edits to a deck's content go through here, so a locked deck stays as it was ----


@router.patch("/api/slides/{slide_id}")
def update_slide(slide_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    slide = models.slides.fetch(conn, slide_id)
    if slide is None:
        raise HTTPException(404, "No slide with that id.")
    ensure_editable(conn, slide["deck_id"])
    return models.slides.visible(models.slides.update(conn, slide_id, body, viewer.source), viewer)


@router.delete("/api/slides/{slide_id}", status_code=204)
def delete_slide(slide_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    slide = models.slides.fetch(conn, slide_id)
    if slide is None:
        raise HTTPException(404, "No slide with that id.")
    ensure_editable(conn, slide["deck_id"])
    models.slides.delete(conn, slide_id, viewer.source)


@router.patch("/api/decks/{deck_id}")
def update_deck(deck_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Title, theme and transition are content; status moves only through /status."""
    require_write(viewer)
    if "status" in body:
        raise HTTPException(400, "Change a deck's status with the workflow buttons, so each step is saved as a version.")
    if any(k in body for k in DECK_FIELDS):
        ensure_editable(conn, deck_id)
    else:
        deck_or_404(conn, deck_id)
    return models.decks.visible(models.decks.update(conn, deck_id, body, viewer.source), viewer)
