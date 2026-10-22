"""The portfolio: strategic themes, epics as funded hypotheses, and the portfolio Kanban.

An epic starts in the funnel as an idea, is reviewed and then analyzed until it has a lean business case (the
hypothesis, the outcomes expected, the leading indicators that show early whether it's working, an MVP and
estimates). Ready epics are ranked by WSJF across all trains. While the MVP is implemented, the evidence decides:
persevere and keep investing, pivot back to analysis, or stop. WIP limits keep the analyzing and implementing
columns from filling up with more than the portfolio can carry.
"""

import json
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()
WIP_KEY = "portfolio.wip"
DEFAULT_WIP = {"analyzing": 3, "implementing MVP": 3, "implementing persevere": 5}
STATES = models.EPIC_STATES
CASE_FIELDS = ("hypothesis", "outcomes", "leading_indicators", "mvp")
CASE_LABELS = {"hypothesis": "the hypothesis", "outcomes": "the expected outcomes", "leading_indicators": "the leading indicators", "mvp": "the MVP"}


def _wip(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (WIP_KEY,)).fetchone()
    return {**DEFAULT_WIP, **(json.loads(row["value"]) if row else {})}


def _missing_case(epic: dict) -> list[str]:
    return [CASE_LABELS[f] for f in CASE_FIELDS if not (epic.get(f) or "").strip()]


def _epic_or_404(conn, epic_id: int) -> dict:
    e = models.epics.fetch(conn, epic_id)
    if e is None:
        raise HTTPException(404, "No such epic.")
    return e


@router.get("/api/portfolio")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    epics = models.epics.visible_all(models.epics.fetch_all(conn), viewer)
    wip = _wip(conn)
    columns = []
    for state in STATES:
        items = [e for e in epics if e["kanban_state"] == state]
        items.sort(key=lambda e: (e.get("wsjf") is None, -(e.get("wsjf") or 0), e["id"]))
        limit = wip.get(state)
        columns.append({"state": state, "epics": [{**e, "case_missing": _missing_case(e)} for e in items], "limit": limit,
                        "over": limit is not None and len(items) > limit})
    themes = models.strategic_themes.visible_all(models.strategic_themes.fetch_all(conn), viewer)
    for t in themes:
        mine = [e for e in epics if e.get("theme_id") == t["id"]]
        t["epics"] = len(mine)
        t["active_epics"] = sum(1 for e in mine if e["kanban_state"] not in ("funnel", "done"))
    return {"columns": columns, "themes": themes, "wip": wip, "unthemed": sum(1 for e in epics if not e.get("theme_id") and e["kanban_state"] != "done"),
            "arts": [{"id": a["id"], "name": a["name"]} for a in models.arts.fetch_all(conn)]}


@router.put("/api/portfolio/wip")
def set_wip(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    wip = _wip(conn)
    for state, n in body.items():
        if state not in DEFAULT_WIP:
            raise HTTPException(400, "WIP limits are for analyzing, implementing MVP and implementing persevere.")
        if n is not None and (not isinstance(n, int) or n < 1):
            raise HTTPException(400, "A WIP limit is a whole number of at least 1, or empty for none.")
        wip[state] = n
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (WIP_KEY, json.dumps(wip)))
    return wip


@router.post("/api/epics/{epic_id}/move")
def move(epic_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Move an epic on the portfolio Kanban. Ready needs a lean business case; persevere needs a persevere decision."""
    require_write(viewer)
    epic = _epic_or_404(conn, epic_id)
    to = body.get("to")
    if to not in STATES:
        raise HTTPException(400, f"Move to one of: {', '.join(STATES)}.")
    if STATES.index(to) >= STATES.index("ready") and to != "done":
        missing = _missing_case(epic)
        if missing:
            raise HTTPException(400, f"Write the lean business case first: {', '.join(missing)}.")
    if to == "implementing persevere" and epic.get("decision") != "persevere":
        raise HTTPException(400, "Record a persevere decision on the MVP first.")
    limit = _wip(conn).get(to)
    if limit is not None and to != epic["kanban_state"]:
        count = conn.execute("SELECT COUNT(*) FROM epics WHERE kanban_state = ?", (to,)).fetchone()[0]
        if count >= limit and not body.get("over_limit"):
            raise HTTPException(409, f"{to.capitalize()} is at its WIP limit of {limit}. Finish or stop something first, or move it anyway.")
    changes = {"kanban_state": to}
    if to == "implementing MVP":
        changes.update({"decision": None, "decision_date": None})
    return models.epics.update(conn, epic_id, changes, viewer.source)


@router.post("/api/epics/{epic_id}/decide")
def decide(epic_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Pivot or persevere on the MVP's evidence: persevere keeps investing, pivot goes back to analysis, stop ends it."""
    require_write(viewer)
    epic = _epic_or_404(conn, epic_id)
    decision = body.get("decision")
    if decision not in models.EPIC_DECISIONS:
        raise HTTPException(400, "Decide persevere, pivot or stop.")
    if epic["kanban_state"] != "implementing MVP":
        raise HTTPException(400, "Decide once the MVP is being implemented and there's evidence to go on.")
    state = {"persevere": "implementing persevere", "pivot": "analyzing", "stop": "done"}[decision]
    return models.epics.update(conn, epic_id, {"decision": decision, "decision_date": date.today().isoformat(),
                                               "decision_notes": (body.get("notes") or "").strip() or None, "kanban_state": state}, viewer.source)


@router.get("/api/epics/{epic_id}/detail")
def detail(epic_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    epic = models.epics.visible(_epic_or_404(conn, epic_id), viewer)
    features = models.features.visible_all(models.features.fetch_all(conn, "epic_id = ?", (epic_id,)), viewer)
    pis = {p["id"]: p["number"] for p in models.program_increments.fetch_all(conn)}
    for f in features:
        f["pi_number"] = pis.get(f.get("pi_id"))
    points = sum(f.get("points") or 0 for f in features)
    done_points = sum(f.get("points") or 0 for f in features if f["status"] == "done")
    return {"epic": {**epic, "case_missing": _missing_case(epic)}, "features": features, "points": points, "done_points": done_points,
            "themes": models.strategic_themes.visible_all(models.strategic_themes.fetch_all(conn, "status = 'active'"), viewer),
            "arts": [{"id": a["id"], "name": a["name"]} for a in models.arts.fetch_all(conn)]}
