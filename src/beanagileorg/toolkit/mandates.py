"""Mandates: what a role is for, what it's expected to deliver, and what it can decide.

Yours is worked out with your manager: the outcomes you're expected to deliver and by when, the decisions you can
make on your own and the ones you only recommend, the boundaries, the resources, and the questions still open.
Each of your reports gets the same, worked out with you. Agreeing a report's mandate completes their
"agree what's expected in their role" milestone in First 90 days.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .people_crm import me_id
from .routes import START_DATE_KEY, require_write, today

router = APIRouter()

MY_DECISIONS = [
    "Sprint scope and priorities, with the product owner",
    "How the team works: ceremonies, process and definition of done",
    "Technical and architecture decisions",
    "Release go/no-go",
    "Hiring, and adding or ending contractors",
    "Performance concerns and other people decisions",
    "Tools and spending",
    "Vendor relationships",
    "Commitments to other teams",
    "Changes to the team's structure or roles",
]
REPORT_DECISIONS = [
    "How they approach and sequence their own work",
    "Technical choices within their stories",
    "Approving pull requests",
    "Estimates for their work",
    "Talking directly with stakeholders",
    "Raising and escalating risks",
]


def _start(conn) -> date | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return date.fromisoformat(row["value"]) if row and row["value"] else None


def _full(conn, m: dict, viewer: Viewer) -> dict:
    start = _start(conn)
    items = models.mandate_items.visible_all(models.mandate_items.fetch_all(conn, "mandate_id = ?", (m["id"],)), viewer)
    for i in items:
        i["due"] = (start + timedelta(days=i["due_day"] - 1)).isoformat() if start and i.get("due_day") else None
    outcomes = [i for i in items if i["kind"] == "outcome"]
    decisions = [i for i in items if i["kind"] == "decision"]
    return {**m, "outcomes": outcomes, "decisions": decisions,
            "to_clarify": sum(1 for d in decisions if d.get("authority") in (None, "to clarify")),
            "at_risk": sum(1 for o in outcomes if o["status"] == "at risk"), "done": sum(1 for o in outcomes if o["status"] == "done")}


def _get(conn, mandate_id: int) -> dict:
    m = models.mandates.fetch(conn, mandate_id)
    if not m:
        raise HTTPException(404, "No such mandate.")
    return m


def _create(conn, person_id: int, mine: bool, decisions: list[str], source: str) -> dict:
    if conn.execute("SELECT 1 FROM mandates WHERE person_id = ?", (person_id,)).fetchone():
        raise HTTPException(409, "There's already a mandate for this person.")
    m = models.mandates.create(conn, {"person_id": person_id, "mine": mine}, source)
    for pos, text in enumerate(decisions):
        models.mandate_items.create(conn, {"mandate_id": m["id"], "kind": "decision", "text": text, "authority": "to clarify", "position": pos}, source)
    return m


@router.get("/api/mandates/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    me = me_id(conn)
    mine = models.mandates.fetch_all(conn, "mine = 1")
    out = {"me": me, "mine": _full(conn, models.mandates.visible(mine[0], viewer), viewer) if mine and models.mandates.visible(mine[0], viewer) else None}
    if viewer.floor != Level.PRIVATE:
        return out
    reports = models.people.fetch_all(conn, "manager_id = ? AND active = 1", (me,)) if me else []
    by_person = {m["person_id"]: m for m in models.mandates.fetch_all(conn, "mine = 0")}
    out["reports"] = []
    for p in reports:
        m = by_person.get(p["id"])
        out["reports"].append({"person_id": p["id"], "name": p["name"], "role": p.get("role"), "placeholder": bool(p.get("placeholder")),
                               "mandate": {k: v for k, v in _full(conn, m, viewer).items() if k not in ("outcomes", "decisions")} if m else None})
    brief = conn.execute("SELECT value FROM settings WHERE key = 'culture.role_brief'").fetchone()
    out["has_brief"] = bool(brief)
    return out


@router.post("/api/mandates/mine", status_code=201)
def create_mine(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    me = me_id(conn)
    if not me:
        raise HTTPException(400, "Pick your own record under People ('This is me') first.")
    return _create(conn, me, True, MY_DECISIONS if body.get("starter", True) else [], viewer.source)


@router.post("/api/mandates/for/{person_id}", status_code=201)
def create_for(person_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if not models.people.fetch(conn, person_id):
        raise HTTPException(404, "No such person.")
    if person_id == me_id(conn):
        raise HTTPException(400, "That's you. Use your own mandate.")
    return _create(conn, person_id, False, REPORT_DECISIONS if body.get("starter", True) else [], viewer.source)


@router.get("/api/mandates/{mandate_id}/full")
def full(mandate_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    m = models.mandates.visible(_get(conn, mandate_id), viewer)
    if not m:
        return {"hidden": True}
    return _full(conn, m, viewer)


@router.post("/api/mandates/{mandate_id}/agree")
def agree(mandate_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record that the mandate was agreed: with whom, when, and when to look at it again."""
    require_write(viewer)
    m = _get(conn, mandate_id)
    on = body.get("on") or today().isoformat()
    review = body.get("review_on") or (date.fromisoformat(on) + timedelta(days=90)).isoformat()
    who = body.get("agreed_with_id")
    if who is None:
        if m["mine"]:
            row = conn.execute("SELECT manager_id FROM people WHERE id = ?", (m["person_id"],)).fetchone()
            who = row["manager_id"] if row else None
        else:
            who = me_id(conn)
    return models.mandates.update(conn, mandate_id, {"status": "agreed", "agreed_on": on, "review_on": review, "agreed_with_id": who}, viewer.source)


@router.post("/api/mandates/mine/from-brief")
def from_brief(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn the Role brief's 'what I was brought in to do' lines into expected outcomes."""
    require_write(viewer)
    import json

    mine = models.mandates.fetch_all(conn, "mine = 1")
    if not mine:
        raise HTTPException(400, "Start your mandate first.")
    row = conn.execute("SELECT value FROM settings WHERE key = 'culture.role_brief'").fetchone()
    focus = (json.loads(row["value"]) if row else {}).get("focus") or []
    have = {i["text"] for i in models.mandate_items.fetch_all(conn, "mandate_id = ?", (mine[0]["id"],))}
    added = 0
    for pos, text in enumerate(focus):
        if text not in have:
            models.mandate_items.create(conn, {"mandate_id": mine[0]["id"], "kind": "outcome", "text": text, "position": pos}, viewer.source)
            added += 1
    return {"added": added}


@router.post("/api/mandates/import")
def import_mandate(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Fill your mandate from a file: purpose, boundaries, resources, questions, outcomes and decisions. Safe to run twice."""
    require_write(viewer)
    mine = models.mandates.fetch_all(conn, "mine = 1")
    m = mine[0] if mine else create_mine({"starter": not body.get("decisions")}, viewer, conn)  # the common decision areas, unless the file lists its own
    fields = {k: body[k] for k in ("purpose", "boundaries", "resources", "questions") if body.get(k) and not m.get(k)}
    if fields:
        models.mandates.update(conn, m["id"], fields, viewer.source)
    have = {i["text"] for i in models.mandate_items.fetch_all(conn, "mandate_id = ?", (m["id"],))}
    added = 0
    for kind, key in (("outcome", "outcomes"), ("decision", "decisions")):
        for pos, item in enumerate(body.get(key) or []):
            text = (item.get("text") or "").strip()
            if not text or text in have:
                continue
            if item.get("authority") and item["authority"] not in models.AUTHORITY:
                raise HTTPException(400, f"Unknown authority for: {text}")
            models.mandate_items.create(conn, {"mandate_id": m["id"], "kind": kind, "text": text, "measure": item.get("measure"), "due_day": item.get("due_day"),
                                               "authority": item.get("authority") or ("to clarify" if kind == "decision" else None), "position": pos}, viewer.source)
            have.add(text)
            added += 1
    return {"mandate_id": m["id"], "added": added, "fields": sorted(fields)}


def mandate_markdown(conn, mandate_id: int, viewer: Viewer) -> dict:
    m = models.mandates.visible(_get(conn, mandate_id), viewer)
    if not m:
        raise HTTPException(404, "No such mandate.")
    f = _full(conn, m, viewer)
    title = f"Mandate: {f.get('person_name') or ''}".strip()
    md = [f"# {title}", ""]
    if f.get("status") == "agreed":
        md += [f"Agreed{' with ' + f['agreed_with_name'] if f.get('agreed_with_name') else ''} on {f['agreed_on']}. Next review {f.get('review_on') or 'not set'}.", ""]
    else:
        md += [f"Status: {f.get('status')}. [Placeholder: to discuss and agree]", ""]
    md += ["## What the role is for", f.get("purpose") or "[Placeholder]", ""]
    md += ["## What success looks like"] + ([f"- {o['text']}" + (f" (measure: {o['measure']})" if o.get("measure") else "") + (f", by {o['due']}" if o.get("due") else (f", by day {o['due_day']}" if o.get("due_day") else "")) for o in f["outcomes"]] or ["- [Placeholder]"])
    md += ["", "## Decisions", "| Area | Authority |", "| --- | --- |"] + [f"| {d['text']} | {d.get('authority') or 'to clarify'} |" for d in f["decisions"]]
    for key, label in (("boundaries", "Boundaries"), ("resources", "Resources and support"), ("questions", "Still to clarify")):
        if f.get(key):
            md += ["", f"## {label}", f[key]]
    return {"title": title, "markdown": "\n".join(md)}


@router.get("/api/mandates/{mandate_id}/markdown")
def markdown(mandate_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return mandate_markdown(conn, mandate_id, viewer)


@router.post("/api/mandates/{mandate_id}/export")
def export(mandate_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    doc = mandate_markdown(conn, mandate_id, Viewer(floor=Level.PRESENTABLE, source="mandate-export"))
    log_export(conn, "mandate:markdown", doc["title"], [{"markdown": doc["markdown"]}], viewer.source)
    return doc


def mandate_due(conn) -> dict:
    """For Today: your own mandate not yet agreed after two weeks in the role, and any mandate due for review."""
    t = today()
    start = _start(conn)
    mine = models.mandates.fetch_all(conn, "mine = 1")
    day = (t - start).days + 1 if start else None
    nudge = None
    if me_id(conn) and day and day >= 14 and (not mine or mine[0]["status"] != "agreed"):
        nudge = {"day": day, "exists": bool(mine), "id": mine[0]["id"] if mine else None}
    reviews = [{"id": m["id"], "name": m.get("person_name"), "mine": bool(m["mine"]), "review_on": m["review_on"]}
               for m in models.mandates.fetch_all(conn, "status = 'agreed' AND review_on IS NOT NULL AND review_on <= ?", ((t + timedelta(days=7)).isoformat(),))]
    return {"agree_mine": nudge, "reviews": reviews}
