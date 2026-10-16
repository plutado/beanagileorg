"""Toolkit endpoints beyond plain records: rollup, skills, Today, obligations, settings, placeholder data."""

import calendar
from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer, require_full
from beanagile.core.privacy import Level, Viewer

from . import models
from .seed import load_placeholders

router = APIRouter()
START_DATE_KEY = "toolkit.start_date"
NOTE_FIELDS = ("change_first", "frustrating", "dont_change", "gaps", "opportunities")


def today() -> date:
    return date.today()


def add_months(d: date, months: int) -> date:
    year, month = divmod(d.month - 1 + months, 12)
    year, month = d.year + year, month + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def next_occurrence(d: date, cadence: str) -> date | None:
    if cadence == "weekly":
        return d + timedelta(days=7)
    if cadence == "every two weeks":
        return d + timedelta(days=14)
    if cadence == "monthly":
        return add_months(d, 1)
    if cadence == "quarterly":
        return add_months(d, 3)
    return None


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
        "people_count": conn.execute("SELECT COUNT(*) FROM people").fetchone()[0],
    }


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
    if conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]:
        raise HTTPException(409, "Placeholder data only loads into an empty toolkit.")
    return load_placeholders(conn, viewer.source)
