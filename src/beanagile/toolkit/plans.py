"""The 30/60/90-day and six-month plans: horizons with dates, evidence from the listening tour, and an exportable outline."""

import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer
from beanagile.core.export import log_export
from beanagile.core.privacy import Level, Viewer

from . import models
from .routes import START_DATE_KEY, build_rollup, require_write

router = APIRouter()
KIND_TITLES = {"outcome": "Outcomes", "action": "Actions", "measure": "How we'll know", "keep": "What I won't change"}


def _start(conn) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return row["value"] if row else None


def _day(start: str | None, n: int | None) -> str | None:
    if not start or n is None:
        return None
    return (date.fromisoformat(start) + timedelta(days=n - 1)).isoformat()


def build_plans(conn, viewer: Viewer) -> dict:
    start = _start(conn)
    plans = models.plans.visible_all(models.plans.fetch_all(conn), viewer)
    items = models.plan_items.visible_all(models.plan_items.fetch_all(conn), viewer)
    horizons, first = [], 1
    for plan in plans:
        last = plan["horizon_days"]
        own = [dict(i, due=_day(start, i.get("due_day"))) for i in items if i["plan_id"] == plan["id"]]
        for i in own:
            day = i.get("due_day")
            i["outside"] = day is not None and not first <= day <= last
        horizons.append({**plan, "first_day": first, "last_day": last, "start": _day(start, first), "end": _day(start, last), "items": own})
        first = last + 1
    return {"start_date": start, "horizons": horizons}


@router.get("/api/plans/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    data = build_plans(conn, viewer)
    rollup = build_rollup(conn, viewer.floor)
    cited = {}
    for h in data["horizons"]:
        for i in h["items"]:
            for t in i.get("themes") or []:
                cited[t] = cited.get(t, 0) + 1
    data["evidence"] = {
        "done": rollup["done"],
        "planned": rollup["planned"],
        "themes": [{**t, "plan_items": cited.get(t["theme"], 0)} for t in rollup["themes"]],
    }
    if viewer.floor == Level.PRIVATE:
        data["evidence"]["notes"] = rollup["notes"]
    return data


def _check_horizon(body: dict) -> None:
    if "horizon_days" in body:
        try:
            ok = int(body["horizon_days"]) >= 1
        except (TypeError, ValueError):
            ok = False
        if not ok:
            raise HTTPException(400, "The last day must be a whole number of 1 or more.")


@router.post("/api/plans", status_code=201)
def create_plan(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _check_horizon(body)
    try:
        return models.plans.visible(models.plans.create(conn, body, viewer.source), viewer)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "There's already a plan ending on that day.") from exc


@router.patch("/api/plans/{plan_id}")
def update_plan(plan_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _check_horizon(body)
    try:
        plan = models.plans.update(conn, plan_id, body, viewer.source)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "There's already a plan ending on that day.") from exc
    if plan is None:
        raise HTTPException(404, "No such plan.")
    return models.plans.visible(plan, viewer)


@router.post("/api/plans/{plan_id}/presented")
def mark_presented(plan_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if not models.plans.fetch(conn, plan_id):
        raise HTTPException(404, "No such plan.")
    when = body.get("presented_on") or date.today().isoformat()
    return models.plans.update(conn, plan_id, {"status": "presented", "presented_on": when, "audience": body.get("audience")}, viewer.source)


def build_outline(conn) -> dict:
    """Exportable only: what can go in front of leadership or into a deck."""
    exporter = Viewer(floor=Level.EXPORTABLE, source="outline", scopes=frozenset({"export:read"}))
    data = build_plans(conn, exporter)
    rollup = build_rollup(conn, Level.EXPORTABLE)
    lines = ["# My 30-, 60- and 90-day and six-month plans", ""]
    if data["start_date"]:
        lines += [f"Start date: {data['start_date']}", ""]
    if rollup["done"]:
        lines += [f"## What I heard ({rollup['done']} conversations)", ""]
        lines += [f"- {t['theme']} ({t['count']} of {rollup['done']})" for t in rollup["themes"][:6]] + [""]
    horizons = []
    for h in data["horizons"]:
        dates = f" ({h['start']} to {h['end']})" if h["start"] else ""
        lines += [f"## {h['title']}{dates}", ""]
        if h.get("summary"):
            lines += [h["summary"], ""]
        groups = {}
        for i in h["items"]:
            if i["status"] != "dropped":
                groups.setdefault(i["kind"], []).append(i)
        for kind, title in KIND_TITLES.items():
            if groups.get(kind):
                lines += [f"### {title}"] + [f"- {i['title']}" + (f" (by {i['due']})" if i.get("due") else "") for i in groups[kind]] + [""]
        horizons.append({
            "title": h["title"], "summary": h.get("summary"), "start": h["start"], "end": h["end"],
            "groups": {kind: [{"title": i["title"], "detail": i.get("detail"), "due": i.get("due")} for i in groups.get(kind, [])] for kind in KIND_TITLES},
        })
    if not any(h["items"] for h in data["horizons"]):
        lines += ["[Placeholder: add outcomes and actions to each plan]"]
    return {
        "title": "My 30-, 60- and 90-day and six-month plans",
        "start_date": data["start_date"],
        "heard": {"conversations": rollup["done"], "themes": rollup["themes"][:6]},
        "kind_titles": KIND_TITLES,
        "horizons": horizons,
        "markdown": "\n".join(lines).rstrip() + "\n",
    }


@router.get("/api/plans/outline")
def outline(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_outline(conn)


@router.post("/api/plans/export")
def export(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    data = build_outline(conn)
    log_export(conn, "plans:markdown", data["title"], [{"markdown": data["markdown"]}], viewer.source)
    return data
