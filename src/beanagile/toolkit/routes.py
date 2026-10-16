"""Toolkit endpoints beyond plain records: rollup, skills, Today, obligations, settings, placeholder data."""

import sqlite3
from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer, require_full
from beanagile.core.dates import next_occurrence
from beanagile.core.privacy import Level, Viewer

from . import models
from .seed import load_placeholders

router = APIRouter()
START_DATE_KEY = "toolkit.start_date"
NOTE_FIELDS = ("change_first", "frustrating", "dont_change", "gaps", "opportunities")


def today() -> date:
    return date.today()


def require_write(viewer: Viewer) -> None:
    if not viewer.has_scope("full"):
        raise HTTPException(403, "This needs the full scope.")


# ---- rollup ----


def build_rollup(conn, floor: Level) -> dict:
    records = models.interviews.fetch_all(conn)
    done = [r for r in records if r["status"] == "done"]
    themes = Counter(t for r in done for t in r["themes"])
    out = {
        "done": len(done),
        "planned": len(records) - len(done),
        "themes": [{"theme": t, "count": n} for t, n in themes.most_common()],
    }
    if floor <= Level.PRESENTABLE:
        systems = Counter(s for r in done for s in r["systems"])
        out["systems"] = [{"system": s, "count": n} for s, n in systems.most_common()]
    if floor == Level.PRIVATE:
        out["notes"] = {
            key: [{"person": r["person_name"], "text": r[key]} for r in done if r[key]] for key in NOTE_FIELDS
        }
        out["theme_quotes"] = {
            t: [
                {"person": r["person_name"], "text": r["change_first"] or r["frustrating"]}
                for r in done
                if t in r["themes"] and (r["change_first"] or r["frustrating"])
            ]
            for t in themes
        }
    return out


@router.get("/api/rollup")
def rollup(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_rollup(conn, viewer.floor)


@router.get("/api/rollup/markdown")
def rollup_markdown(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    data = build_rollup(conn, Level.PRIVATE)
    lines = [f"# Day-30 rollup ({data['done']} one-on-ones)", "", "## Themes"]
    lines += [f"- **{t['theme']}** ({t['count']} of {data['done']})" for t in data["themes"]]
    titles = {
        "gaps": "Gaps",
        "opportunities": "Opportunities",
        "dont_change": "What not to change",
        "change_first": "What to change first",
    }
    for key, title in titles.items():
        lines += ["", f"## {title}"] + [f"- {n['text']}" for n in data["notes"][key]]
    return {"markdown": "\n".join(lines)}


# ---- skills and learning ----


@router.get("/api/skills")
def skills(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor == Level.EXPORTABLE:
        return {"skills": []}
    active = [p for p in models.people.fetch_all(conn) if p["active"]]
    topics = sorted({s for p in active for key in ("skills", "can_teach", "wants_to_learn") for s in p[key]})
    out = {
        "skills": [
            {
                "skill": s,
                "people": sum(s in p["skills"] for p in active),
                "can_teach": sum(s in p["can_teach"] for p in active),
                "wants_to_learn": sum(s in p["wants_to_learn"] for p in active),
            }
            for s in topics
        ]
    }
    if viewer.floor == Level.PRIVATE:
        out["matrix"] = [
            {k: p[k] for k in ("id", "name", "role", "skills", "can_teach", "wants_to_learn")} for p in active
        ]
        out["matches"] = [
            {
                "topic": t,
                "teachers": [p["name"] for p in active if t in p["can_teach"]],
                "learners": [p["name"] for p in active if t in p["wants_to_learn"]],
            }
            for t in topics
            if any(t in p["can_teach"] for p in active) and any(t in p["wants_to_learn"] for p in active)
        ]
    return out


# ---- Today ----


@router.get("/api/today")
def today_view(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor > Level.PRIVATE:
        return {"hidden": True}
    t, week = today().isoformat(), (today() + timedelta(days=7)).isoformat()
    open_tasks = models.tasks.fetch_all(conn, "status = 'open' AND due IS NOT NULL")
    return {
        "today": t,
        "overdue_tasks": [x for x in open_tasks if x["due"] < t],
        "tasks_due_soon": [x for x in open_tasks if t <= x["due"] <= week],
        "obligations_due": models.obligations.fetch_all(conn, "next_due IS NOT NULL AND next_due <= ?", (week,)),
        "upcoming_interviews": models.interviews.fetch_all(
            conn, "status = 'planned' AND date IS NOT NULL AND date <= ?", (week,)
        ),
        "goals_at_risk": models.learning_goals.visible_all(
            models.learning_goals.fetch_all(conn, "status = 'at risk'"), viewer
        ),
        "overdue_actions": models.action_items.fetch_all(conn, "status != 'done' AND due IS NOT NULL AND due < ?", (t,)),
        "people_count": conn.execute("SELECT COUNT(*) FROM people").fetchone()[0],
    }


# ---- dev-sync log and group learning ----


def propose_session(conn, item: dict, source: str) -> None:
    """A dev-sync item flagged for group learning gets one proposed session, presented by its owner."""
    if not item["learning"]:
        return
    if conn.execute("SELECT 1 FROM learning_sessions WHERE action_item_id = ?", (item["id"],)).fetchone():
        return
    models.learning_sessions.create(
        conn, {"topic": item["concern"], "presenter_id": item["owner_id"], "action_item_id": item["id"]}, source
    )


@router.post("/api/actions", status_code=201)
def create_action(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    body.setdefault("raised_on", today().isoformat())
    try:
        item = models.action_items.create(conn, body, viewer.source)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(400, "That refers to a person who doesn't exist.") from exc
    propose_session(conn, item, viewer.source)
    return models.action_items.visible(item, viewer)


@router.patch("/api/actions/{item_id}")
def update_action(item_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    try:
        item = models.action_items.update(conn, item_id, body, viewer.source)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(400, "That refers to a person who doesn't exist.") from exc
    if item is None:
        raise HTTPException(404, "No action item with that id.")
    propose_session(conn, item, viewer.source)
    return models.action_items.visible(item, viewer)


@router.get("/api/actions/summary")
def action_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    t, week = today().isoformat(), (today() + timedelta(days=7)).isoformat()
    open_items = models.action_items.fetch_all(conn, "status != 'done'")
    return {
        "open": len(open_items),
        "overdue": sum(1 for i in open_items if i["due"] and i["due"] < t),
        "due_soon": sum(1 for i in open_items if i["due"] and t <= i["due"] <= week),
        "learning": conn.execute("SELECT COUNT(*) FROM action_items WHERE learning = 1").fetchone()[0],
    }


# ---- escalation playbook ----


@router.get("/api/escalation/{system_id}")
def escalation(system_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    system = models.systems.fetch(conn, system_id)
    if system is None:
        raise HTTPException(404, "No system with that id.")
    names = {p["id"]: p["name"] for p in models.people.fetch_all(conn)}
    steps = models.escalation_steps.visible_all(models.escalation_steps.fetch_all(conn, "system_id = ?", (system_id,)), viewer)
    shown = models.systems.visible(system, viewer)
    for role in ("owner", "first_responder", "backup"):
        shown[f"{role}_name"] = names.get(system[f"{role}_id"])
    return {
        "system": shown,
        "business_hours": [s for s in steps if not s["out_of_hours"]],
        "out_of_hours": [s for s in steps if s["out_of_hours"]],
        "severities": models.severities.visible_all(models.severities.fetch_all(conn), viewer),
        "recent_incidents": models.incidents.visible_all(models.incidents.fetch_all(conn, "system_id = ?", (system_id,)), viewer)[:5],
    }


@router.post("/api/incidents/{incident_id}/follow-up", status_code=201)
def incident_follow_up(incident_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    incident = models.incidents.fetch(conn, incident_id)
    if incident is None:
        raise HTTPException(404, "No incident with that id.")
    data = {**body, "origin": "incident", "incident_id": incident_id}
    data.setdefault("concern", f"Follow-up: {incident['summary']}")
    return create_action(data, viewer, conn)


# ---- obligations ----


@router.post("/api/obligations/{obligation_id}/done")
def obligation_done(obligation_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rec = models.obligations.fetch(conn, obligation_id)
    if rec is None:
        raise HTTPException(404, "No obligation with that id.")
    now = today()
    nxt = date.fromisoformat(rec["next_due"]) if rec["next_due"] else now
    while True:
        nxt = next_occurrence(nxt, rec["cadence"])
        if nxt is None or nxt > now:
            break
    return models.obligations.update(
        conn,
        obligation_id,
        {"last_done": now.isoformat(), "next_due": nxt.isoformat() if nxt else None},
        viewer.source,
    )


# ---- settings ----


@router.get("/api/toolkit/settings")
def get_settings(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return {"start_date": row["value"] if row else None}


@router.put("/api/toolkit/settings")
def put_settings(body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    start = body.get("start_date") or None
    if start is not None:
        try:
            date.fromisoformat(start)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "start_date must be a date like 2026-11-02.") from exc
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (START_DATE_KEY, start))
    else:
        conn.execute("DELETE FROM settings WHERE key = ?", (START_DATE_KEY,))
    return {"start_date": start}


# ---- placeholder data ----


@router.post("/api/seed-placeholders", status_code=201)
def seed(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    loaded = load_placeholders(conn, viewer.source)
    if not loaded:
        raise HTTPException(409, "Placeholder data only loads into empty parts of the toolkit, and none are empty.")
    return loaded
