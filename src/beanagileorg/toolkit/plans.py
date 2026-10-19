"""The 30/60/90-day and six-month plans: horizons with dates, evidence from the listening tour, and an exportable outline."""

import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

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
    plan = models.plans.update(conn, plan_id, {"status": "presented", "presented_on": when, "audience": body.get("audience")}, viewer.source)
    take_version(conn, plan_id, f"Presented{' to ' + body['audience'] if body.get('audience') else ''}", "", viewer.source, when)
    return plan


# ---- versions and check-ins ----
# A version is the plan as it stood (title, headline and items) when it was presented or at a moment you chose.

VERSION_FIELDS = ("title", "kind", "due_day", "status", "detail", "early_win")
CHECKIN_OUTCOMES = ("met", "partly", "moved", "dropped")


def _snapshot(conn, plan_id: int) -> dict:
    plan = models.plans.fetch(conn, plan_id)
    items = models.plan_items.fetch_all(conn, "plan_id = ?", (plan_id,))
    return {"title": plan["title"], "summary": plan.get("summary"), "horizon_days": plan["horizon_days"],
            "items": [{"id": i["id"], **{k: i.get(k) for k in VERSION_FIELDS}} for i in items]}


def take_version(conn, plan_id: int, label: str, reason: str, source: str, when: str | None = None) -> dict:
    return models.plan_versions.create(conn, {"plan_id": plan_id, "taken_on": when or date.today().isoformat(), "label": label,
                                              "reason": reason, "snapshot": _snapshot(conn, plan_id)}, source)


@router.post("/api/plans/{plan_id}/versions", status_code=201)
def save_version(plan_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if not models.plans.fetch(conn, plan_id):
        raise HTTPException(404, "No such plan.")
    return take_version(conn, plan_id, (body.get("label") or "Saved version").strip(), body.get("reason") or "", viewer.source)


@router.get("/api/plans/{plan_id}/versions")
def list_versions(plan_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return [{k: v[k] for k in ("id", "taken_on", "label", "reason")} | {"items": len((v.get("snapshot") or {}).get("items") or [])}
            for v in models.plan_versions.fetch_all(conn, "plan_id = ?", (plan_id,))]


def compare(old: dict, new: dict) -> dict:
    """What changed between two snapshots: items added, removed, and changed field by field."""
    before = {i["id"]: i for i in old.get("items") or []}
    after = {i["id"]: i for i in new.get("items") or []}
    changed = []
    for iid in before.keys() & after.keys():
        diffs = [{"field": k, "was": before[iid].get(k), "now": after[iid].get(k)} for k in VERSION_FIELDS if before[iid].get(k) != after[iid].get(k)]
        if diffs:
            changed.append({"id": iid, "title": after[iid]["title"], "changes": diffs})
    return {"added": [after[i] for i in after.keys() - before.keys()], "removed": [before[i] for i in before.keys() - after.keys()], "changed": changed,
            "summary_changed": old.get("summary") != new.get("summary"), "title_changed": old.get("title") != new.get("title"),
            "was_summary": old.get("summary"), "now_summary": new.get("summary")}


@router.get("/api/plans/{plan_id}/compare")
def compare_version(plan_id: int, version_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    v = models.plan_versions.fetch(conn, version_id)
    if v is None or v["plan_id"] != plan_id:
        raise HTTPException(404, "No such version of this plan.")
    return {"version": {k: v[k] for k in ("id", "taken_on", "label", "reason")}, **compare(v.get("snapshot") or {}, _snapshot(conn, plan_id))}


@router.put("/api/plan-items/{item_id}/checkin")
def checkin(item_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Mark an item at a checkpoint: met (done), partly, moved (to a new day or the next plan) or dropped, with a note."""
    require_write(viewer)
    item = models.plan_items.fetch(conn, item_id)
    if item is None:
        raise HTTPException(404, "No such plan item.")
    outcome = body.get("outcome")
    if outcome is None:
        return models.plan_items.update(conn, item_id, {"checkin": {}}, viewer.source)
    if outcome not in CHECKIN_OUTCOMES:
        raise HTTPException(400, f"Pick one of: {', '.join(CHECKIN_OUTCOMES)}.")
    note = str(body.get("note") or "")
    if outcome in ("moved", "dropped") and not note.strip():
        raise HTTPException(400, "Say why it moved or was dropped; that's what the review needs.")
    changes = {"checkin": {"outcome": outcome, "note": note, "on": date.today().isoformat(), "was_day": item.get("due_day"), "was_plan_id": item["plan_id"]}}
    if outcome == "met":
        changes["status"] = "done"
    elif outcome == "dropped":
        changes["status"] = "dropped"
    elif outcome == "moved":
        if body.get("plan_id"):
            if not models.plans.fetch(conn, int(body["plan_id"])):
                raise HTTPException(400, "That plan doesn't exist.")
            changes["plan_id"] = int(body["plan_id"])
        if body.get("due_day") is not None:
            changes["due_day"] = int(body["due_day"])
        if "plan_id" not in changes and "due_day" not in changes:
            raise HTTPException(400, "Say where it moved: a new day, another plan, or both.")
    return models.plan_items.update(conn, item_id, changes, viewer.source)


@router.get("/api/plans/{plan_id}/checkin")
def checkin_summary(plan_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Where the plan stands at its checkpoint, and a Markdown summary to share."""
    plan = models.plans.fetch(conn, plan_id)
    if plan is None:
        raise HTTPException(404, "No such plan.")
    items = [i for i in models.plan_items.fetch_all(conn) if i["plan_id"] == plan_id or ((i.get("checkin") or {}).get("was_plan_id") == plan_id)]
    counts = {o: 0 for o in CHECKIN_OUTCOMES} | {"not checked": 0}
    for i in items:
        counts[(i.get("checkin") or {}).get("outcome") or "not checked"] += 1
    titles = {p["id"]: p["title"] for p in models.plans.fetch_all(conn)}
    lines = [f"# {plan['title']}: check-in", ""]
    if plan.get("summary"):
        lines += [f"*{plan['summary']}*", ""]
    labels = {"met": "Met", "partly": "Partly met", "moved": "Moved", "dropped": "Dropped"}
    for o in CHECKIN_OUTCOMES:
        group = [i for i in items if (i.get("checkin") or {}).get("outcome") == o]
        if group:
            lines += [f"## {labels[o]} ({len(group)})"]
            for i in group:
                c = i["checkin"]
                where = f" (now {titles.get(i['plan_id'], 'another plan')}{', day ' + str(i['due_day']) if i.get('due_day') else ''})" if o == "moved" else ""
                lines.append(f"- {i['title']}{where}" + (f": {c['note']}" if c.get("note") else ""))
            lines.append("")
    rest = [i for i in items if not (i.get("checkin") or {}).get("outcome") and i["status"] != "dropped"]
    if rest:
        lines += [f"## Not yet checked ({len(rest)})"] + [f"- {i['title']}" for i in rest]
    return {"counts": counts, "markdown": "\n".join(lines).rstrip() + "\n"}


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
