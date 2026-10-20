"""Retrospectives (the team's shared record) and PI planning boards."""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()

# ---- retrospectives ----


def _retro_or_404(conn, retro_id: int) -> dict:
    retro = models.retros.fetch(conn, retro_id)
    if retro is None:
        raise HTTPException(404, "No retro with that id.")
    return retro


@router.get("/api/retros/{retro_id}/board")
def retro_board(retro_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    retro = _retro_or_404(conn, retro_id)
    columns = models.RETRO_FORMATS.get(retro["format"], ())
    items = models.retro_items.visible_all(models.retro_items.fetch_all(conn, "retro_id = ?", (retro_id,)), viewer)
    grouped = {c: [i for i in items if i["column_name"] == c] for c in columns}
    others = [i for i in items if i["column_name"] not in columns]
    if others:
        grouped["Other"] = others
    # Commitments from earlier retros that are still open: "did we do what we said?"
    earlier = models.retro_commitments.fetch_all(
        conn,
        "retro_id != ? AND status IN ('committed', 'in progress') AND retro_id IN "
        "(SELECT id FROM retros WHERE COALESCE(date, '') <= COALESCE(?, '9999'))",
        (retro_id, retro["date"]),
    )
    names = {p["id"]: p["name"] for p in models.people.fetch_all(conn)}
    shown = models.retros.visible(retro, viewer)
    shown["attendees"] = [names[i] for i in retro["attendee_ids"] if i in names]
    agreed = models.team_agreements.visible_all(models.team_agreements.fetch_all(
        conn, "status = 'agreed' AND (team_id IS NULL OR team_id IS ?)", (retro.get("team_id"),)), viewer)
    on = retro["date"] or date.today().isoformat()
    for a in agreed:
        a["due_review"] = bool(a.get("review_on") and a["review_on"] <= on)
    return {
        "agreements": agreed,
        "retro": shown,
        "columns": list(grouped),
        "items": grouped,
        "commitments": models.retro_commitments.visible_all(
            models.retro_commitments.fetch_all(conn, "retro_id = ?", (retro_id,)), viewer
        ),
        "carried_forward": models.retro_commitments.visible_all(earlier, viewer),
    }


@router.post("/api/retro-items/{item_id}/vote")
def vote(item_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    item = models.retro_items.fetch(conn, item_id)
    if item is None:
        raise HTTPException(404, "No retro item with that id.")
    delta = -1 if body.get("delta") == -1 else 1
    return models.retro_items.update(conn, item_id, {"votes": max(0, item["votes"] + delta)}, viewer.source)


@router.post("/api/retro-items/{item_id}/commit", status_code=201)
def commit_from_item(item_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn a discussion item into a commitment, tagged to the sprint where the topic surfaced."""
    require_write(viewer)
    item = models.retro_items.fetch(conn, item_id)
    if item is None:
        raise HTTPException(404, "No retro item with that id.")
    retro = _retro_or_404(conn, item["retro_id"])
    data = {"retro_id": retro["id"], "sprint_id": retro["sprint_id"], "commitment": item["text"], **body}
    return models.retro_commitments.create(conn, data, viewer.source)


@router.post("/api/retro-commitments/{commitment_id}/review")
def review_commitment(commitment_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record the outcome of an earlier commitment at a later retro."""
    require_write(viewer)
    if models.retro_commitments.fetch(conn, commitment_id) is None:
        raise HTTPException(404, "No commitment with that id.")
    changes = {k: body[k] for k in ("status", "outcome", "reviewed_in_id") if k in body}
    return models.retro_commitments.update(conn, commitment_id, changes, viewer.source)


@router.get("/api/improvements")
def improvements(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Every retro commitment across sprints: the running improvement backlog, open ones first."""
    return models.retro_commitments.visible_all(models.retro_commitments.fetch_all(conn), viewer)


@router.get("/api/retros/patterns")
def patterns(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Topics that come up in more than one retro, with the sprints where they surfaced."""
    rows = conn.execute(
        """SELECT LOWER(TRIM(i.topic)) AS key, i.topic, r.id AS retro_id, s.number AS sprint_number
           FROM retro_items i JOIN retros r ON r.id = i.retro_id LEFT JOIN sprints s ON s.id = r.sprint_id
           WHERE i.topic IS NOT NULL AND TRIM(i.topic) != ''"""
    ).fetchall()
    seen = defaultdict(lambda: {"topic": None, "retros": set(), "sprints": set()})
    for r in rows:
        entry = seen[r["key"]]
        entry["topic"] = entry["topic"] or r["topic"].strip()
        entry["retros"].add(r["retro_id"])
        if r["sprint_number"] is not None:
            entry["sprints"].add(r["sprint_number"])
    themes = {t.lower() for i in models.interviews.fetch_all(conn) for t in i["themes"]}
    out = [
        {"topic": e["topic"], "retros": len(e["retros"]), "sprints": sorted(e["sprints"]),
         "listening_theme": key in themes if viewer.floor == 0 else None}
        for key, e in seen.items() if len(e["retros"]) > 1
    ]
    return sorted(out, key=lambda e: -e["retros"])


# ---- PI planning ----


@router.get("/api/pis/{pi_id}/board")
def pi_board(pi_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    pi = models.program_increments.fetch(conn, pi_id)
    if pi is None:
        raise HTTPException(404, "No PI with that id.")
    sprints = models.sprints.fetch_all(conn, "pi_id = ?", (pi_id,))
    sprints.sort(key=lambda s: s["number"])
    features = models.features.fetch_all(conn, "pi_id = ?", (pi_id,))
    feature_ids = [f["id"] for f in features]
    sprint_ids = [s["id"] for s in sprints]
    marks = ",".join("?" for _ in feature_ids) or "NULL"
    smarks = ",".join("?" for _ in sprint_ids) or "NULL"
    stories = models.stories.fetch_all(conn, f"feature_id IN ({marks}) OR sprint_id IN ({smarks})", (*feature_ids, *sprint_ids))
    load = defaultdict(int)
    for s in stories:
        if s["sprint_id"]:
            load[s["sprint_id"]] += s["points"] or 0
    sprint_view = []
    for s in models.sprints.visible_all(sprints, viewer):
        s["planned_points"] = load.get(s["id"], 0)
        sprint_view.append(s)
    objectives = models.pi_objectives.fetch_all(conn, "pi_id = ?", (pi_id,))
    committed = [o for o in objectives if o["kind"] == "committed"]
    planned = sum(o["value_planned"] or 0 for o in committed)
    actual = sum(o["value_actual"] or 0 for o in committed)
    epic_ids = {f["epic_id"] for f in features if f["epic_id"]}
    return {
        "pi": models.program_increments.visible(pi, viewer),
        "sprints": sprint_view,
        "objectives": models.pi_objectives.visible_all(objectives, viewer),
        "predictability": round(100 * actual / planned) if planned and any(o["value_actual"] is not None for o in committed) else None,
        "epics": models.epics.visible_all([e for e in models.epics.fetch_all(conn) if e["id"] in epic_ids], viewer),
        "features": models.features.visible_all(features, viewer),
        "stories": models.stories.visible_all(stories, viewer),
        "dependencies": models.dependencies.visible_all(models.dependencies.fetch_all(conn, "pi_id = ?", (pi_id,)), viewer),
        "milestones": models.pi_milestones.visible_all(models.pi_milestones.fetch_all(conn, "pi_id = ?", (pi_id,)), viewer),
        "risks": models.pi_risks.visible_all(models.pi_risks.fetch_all(conn, "pi_id = ?", (pi_id,)), viewer),
    }


@router.post("/api/pis/{pi_id}/confidence")
def confidence_vote(pi_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record the fist-of-five confidence vote: the votes given, stored as their average."""
    require_write(viewer)
    if models.program_increments.fetch(conn, pi_id) is None:
        raise HTTPException(404, "No PI with that id.")
    votes = body.get("votes")
    if not isinstance(votes, list) or not votes or not all(isinstance(v, int) and 1 <= v <= 5 for v in votes):
        raise HTTPException(400, "votes must be a list of whole numbers from 1 to 5.")
    from datetime import date

    return models.program_increments.update(
        conn, pi_id, {"confidence": round(sum(votes) / len(votes), 1), "confidence_date": date.today().isoformat()}, viewer.source
    )
