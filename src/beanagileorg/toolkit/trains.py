"""Agile Release Trains: the team of teams that plans and delivers together each PI.

A train has a mission, its roles (Release Train Engineer, Product Management, System Architect, Business Owners), the
teams on it and the PIs it runs. Its backlog is the features not yet planned into a PI, ranked by Weighted Shortest
Job First: cost of delay (business value + time criticality + risk reduction) divided by job size. Each PI has a
system demo every sprint and ends with Inspect and Adapt, and predictability is tracked from PI to PI.
"""

from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()


def predictability(conn, pi_id: int) -> dict:
    """SAFe's PI predictability: business value achieved on all objectives (stretch ones count when they land) over
    the value planned for the committed ones. 80 to 100 percent is the usual healthy band."""
    objectives = models.pi_objectives.fetch_all(conn, "pi_id = ?", (pi_id,))
    planned = sum(o["value_planned"] or 0 for o in objectives if o["kind"] == "committed")
    scored = [o for o in objectives if o["value_actual"] is not None]
    actual = sum(o["value_actual"] or 0 for o in scored)
    percent = round(100 * actual / planned) if planned and scored else None
    return {"planned": planned, "actual": actual if scored else None, "percent": percent,
            "band": None if percent is None else "healthy" if 80 <= percent <= 100 else "low" if percent < 80 else "over"}


def _art_or_404(conn, art_id: int) -> dict:
    art = models.arts.fetch(conn, art_id)
    if art is None:
        raise HTTPException(404, "No such train.")
    return art


def _rank(features: list[dict]) -> list[dict]:
    """WSJF first, highest first; features not yet scored follow in their priority order."""
    return sorted(features, key=lambda f: (f.get("wsjf") is None, -(f.get("wsjf") or 0)))


@router.get("/api/arts/{art_id}/overview")
def overview(art_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    art = models.arts.visible(_art_or_404(conn, art_id), viewer)
    teams = models.teams.visible_all(models.teams.fetch_all(conn, "art_id = ?", (art_id,)), viewer)
    pis = sorted(models.program_increments.fetch_all(conn, "art_id = ?", (art_id,)), key=lambda p: p["number"])
    backlog = _rank(models.features.visible_all(
        models.features.fetch_all(conn, "art_id = ? AND pi_id IS NULL AND status != 'done'", (art_id,)), viewer))
    owners = {p["id"]: p["name"] for p in models.people.fetch_all(conn) if p["id"] in (art.get("business_owner_ids") or [])}
    return {
        "art": art, "business_owners": [{"id": i, "name": owners[i]} for i in art.get("business_owner_ids") or [] if i in owners],
        "teams": teams, "other_teams": models.teams.visible_all(models.teams.fetch_all(conn, "art_id IS NULL"), viewer),
        "pis": [{**models.program_increments.visible(p, viewer), "predictability": predictability(conn, p["id"])} for p in pis],
        "backlog": backlog,
        "unassigned_pis": models.program_increments.visible_all(models.program_increments.fetch_all(conn, "art_id IS NULL"), viewer),
    }


@router.post("/api/features/{feature_id}/plan")
def plan_feature(feature_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Move a feature from the ART backlog into a PI (or back, with no PI)."""
    require_write(viewer)
    if models.features.fetch(conn, feature_id) is None:
        raise HTTPException(404, "No such feature.")
    pi_id = body.get("pi_id")
    if pi_id is not None and models.program_increments.fetch(conn, pi_id) is None:
        raise HTTPException(404, "No such PI.")
    return models.features.update(conn, feature_id, {"pi_id": pi_id}, viewer.source)


@router.get("/api/pis/{pi_id}/cadence")
def cadence(pi_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The PI's rhythm: a system demo for each development sprint, and Inspect and Adapt at the end."""
    pi = models.program_increments.fetch(conn, pi_id)
    if pi is None:
        raise HTTPException(404, "No such PI.")
    sprints = sorted(models.sprints.fetch_all(conn, "pi_id = ?", (pi_id,)), key=lambda s: s["number"])
    demos = {d["sprint_id"]: d for d in models.system_demos.visible_all(models.system_demos.fetch_all(conn, "pi_id = ?", (pi_id,)), viewer)}
    rows = models.inspect_adapts.fetch_all(conn, "pi_id = ?", (pi_id,))
    today = date.today().isoformat()
    return {
        "sprints": [{"id": s["id"], "number": s["number"], "kind": s["kind"], "end_date": s["end_date"],
                     "demo": demos.get(s["id"]), "due": bool(s["end_date"] and s["end_date"] <= today and s["kind"] == "development" and s["id"] not in demos)}
                    for s in sprints],
        "inspect_adapt": models.inspect_adapts.visible(rows[0], viewer) if rows else None,
        "predictability": predictability(conn, pi_id),
    }


@router.post("/api/pis/{pi_id}/inspect-adapt")
def start_inspect_adapt(pi_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Open (or return) the PI's Inspect and Adapt record."""
    require_write(viewer)
    if models.program_increments.fetch(conn, pi_id) is None:
        raise HTTPException(404, "No such PI.")
    rows = models.inspect_adapts.fetch_all(conn, "pi_id = ?", (pi_id,))
    if rows:
        return rows[0]
    return models.inspect_adapts.create(conn, {"pi_id": pi_id, "date": date.today().isoformat()}, viewer.source)


@router.post("/api/inspect-adapts/{ia_id}/to-backlog", status_code=201)
def improvement_to_backlog(ia_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """An improvement from the problem-solving workshop becomes a ready backlog item, so it gets done next PI."""
    require_write(viewer)
    ia = models.inspect_adapts.fetch(conn, ia_id)
    if ia is None:
        raise HTTPException(404, "No such Inspect and Adapt record.")
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Choose an improvement first.")
    pi = models.program_increments.fetch(conn, ia["pi_id"])
    label = f"PI {pi['number']}"
    if any(i["title"] == text[:200] and "inspect and adapt" in (i.get("labels") or []) for i in models.backlog_items.fetch_all(conn)):
        raise HTTPException(409, "That improvement is already on the backlog.")
    rank = conn.execute("SELECT COALESCE(MAX(rank), 0) + 1 FROM backlog_items").fetchone()[0]
    return models.backlog_items.create(conn, {
        "title": text[:200], "item_type": "task", "status": "ready", "description": f"An improvement from the {label} Inspect and Adapt workshop.",
        "labels": ["inspect and adapt", label], "rank": rank, "added_on": date.today().isoformat()}, viewer.source)
