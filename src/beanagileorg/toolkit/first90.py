"""First 90 days: one view of three tracks that start together.

Your own first 90 days (plans, listening tour, reflections), each new hire's onboarding, and the team you
inherit, for whom these are the first 90 days with a new manager who is bringing change. The inherited team
gets milestones per person, a "Working with me" page, check-ins at days 30, 60 and 90, and a visible list of
the changes you're introducing, each announced, tried, reviewed together and then kept or dropped.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .people_crm import me_id
from .routes import START_DATE_KEY, require_write, today

router = APIRouter()
TEMPLATE_KEY = "first90.template"
WORKING_KEY = "first90.working_with_me"
CHECKPOINTS_KEY = "first90.checkpoints"
CHECKPOINT_DAYS = (30, 60, 90)

STARTER_TEMPLATE = [
    {"title": "First one-on-one: get to know them, and how they like to work", "due_day": 7, "auto": "one_on_one"},
    {"title": "Share 'Working with me' and ask what they'd want me to know about them", "due_day": 14, "auto": None},
    {"title": "Listening tour conversation", "due_day": 21, "auto": "interview"},
    {"title": "Career conversation: where they want to go, and what would help", "due_day": 30, "auto": None},
    {"title": "Agree their mandate: what's expected in their role, and what they can decide", "due_day": 45, "auto": "mandate"},
    {"title": "Growth goal agreed", "due_day": 60, "auto": "growth_goal"},
    {"title": "Feedback both ways: ask for feedback on me, and share mine", "due_day": 75, "auto": "feedback"},
    {"title": "Day-90 check-in: what's changed for them, what's next", "due_day": 90, "auto": None},
]

STARTER_WORKING = """## Working with me

[Placeholder: a sentence or two about who you are and why you're here.]

**What I've been asked to do**
- [Placeholder: e.g. bring in Scrum and a clear QA process, make releases more predictable, bring the two Salesforce teams together]

**How I work**
- I'd rather hear bad news early than good news late. You won't get in trouble for raising a problem.
- I'll tell you what I know as soon as I can share it, and say so when I don't know.
- If you ask me something, you'll get an answer, even if the answer is no or not yet.
- [Placeholder: how and when to reach you, and how you like to communicate]

**What you can expect from me**
- A regular one-on-one that's your time, not a status meeting.
- Feedback directly and privately, and I'll ask for yours on me.
- A conversation about where you want your career to go, in our first month.

**How to work with me without a meeting**
- I share most updates as short videos and written notes, with a transcript, so you can take them in when it suits you.
- Reply in writing, in the comments under a video, or with a quick message. I read everything and answer the same day.
- I won't add meetings beyond our Scrum ceremonies and the dev sync. If something needs a conversation, I'll ask for one; it won't be a meeting to plan a meeting.

**What I'll change, and how**
- I'll bring changes one at a time. Each one is announced first, tried for a set time, and reviewed with you before we keep it or drop it.
- You can see every change, and where it stands, in one place.

**What I'll protect**
- [Placeholder: what's working today that you don't want to lose]

**What I'd like from you**
- Tell me what's working and what isn't, especially in our first few weeks.
- [Placeholder]
"""

STATUS_DATE = {"announced": "announced_on", "trial": "trial_start", "adopted": "decided_on", "dropped": "decided_on"}


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except ValueError:
        return row["value"]


def _put(conn, key, value) -> None:
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))


def start_date(conn) -> date | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return date.fromisoformat(row["value"]) if row and row["value"] else None


def day_number(start: date | None, on: date | None = None) -> int | None:
    return ((on or today()) - start).days + 1 if start else None


def _due(start: date | None, n: int) -> str | None:
    return (start + timedelta(days=n - 1)).isoformat() if start else None


def inherited_team(conn) -> list[dict]:
    """Your direct reports who aren't being onboarded as new hires: the team you inherited."""
    me = me_id(conn)
    if not me:
        return []
    new_hires = {r["person_id"] for r in conn.execute("SELECT person_id FROM onboardings").fetchall()}
    return [p for p in models.people.fetch_all(conn, "manager_id = ? AND active = 1", (me,)) if p["id"] not in new_hires]


def _auto_done(conn, pid: int, auto: str | None, start: date | None) -> str | None:
    """The date the data shows a milestone happened, when it's one the toolkit can see for itself."""
    since = start.isoformat() if start else "0000-01-01"
    if auto == "one_on_one":
        row = conn.execute("SELECT MIN(date) AS d FROM interactions WHERE kind = 'one-on-one' AND date >= ? AND EXISTS (SELECT 1 FROM json_each(person_ids) WHERE value = ?)", (since, pid)).fetchone()
    elif auto == "interview":
        row = conn.execute("SELECT MIN(date) AS d FROM interviews WHERE person_id = ? AND status = 'done'", (pid,)).fetchone()
    elif auto == "growth_goal":
        row = conn.execute(
            "SELECT MIN(date(datetime(c.at, 'localtime'))) AS d FROM change_log c JOIN growth_goals g ON c.entity = 'growth_goal' AND c.record_id = CAST(g.id AS TEXT) "
            "WHERE g.person_id = ? AND g.status != 'dropped'", (pid,)).fetchone()  # when the goal was first written down
    elif auto == "mandate":
        row = conn.execute("SELECT agreed_on AS d FROM mandates WHERE person_id = ? AND status = 'agreed'", (pid,)).fetchone()
    elif auto == "feedback":
        row = conn.execute("SELECT MIN(date) AS d FROM manager_notes WHERE person_id = ? AND shared = 1 AND date >= ?", (pid, since)).fetchone()
    else:
        return None
    return row["d"] if row else None


def team_track(conn) -> dict:
    start = start_date(conn)
    t = today().isoformat()
    people = []
    for p in inherited_team(conn):
        ms = []
        for m in models.first90_milestones.fetch_all(conn, "person_id = ?", (p["id"],)):
            seen = _auto_done(conn, p["id"], m.get("auto"), start)
            done_on = m["done_on"] or seen
            due = _due(start, m["due_day"])
            ms.append({**m, "due": due, "done": done_on, "seen_in_data": bool(seen and not m["done_on"]), "late": bool(not done_on and due and due < t)})
        nxt = next((m for m in ms if not m["done"]), None)
        people.append({"id": p["id"], "name": p["name"], "role": p.get("role"), "milestones": ms, "done": sum(1 for m in ms if m["done"]),
                       "total": len(ms), "late": sum(1 for m in ms if m["late"]), "next": nxt})
    return {"start_date": start.isoformat() if start else None, "day": day_number(start), "people": people, "has_me": bool(me_id(conn))}


def checkpoints(conn) -> list[dict]:
    """The team check-ins at days 30, 60 and 90: when each falls, whether a trust pulse was taken near it, and your notes."""
    start = start_date(conn)
    saved = _setting(conn, CHECKPOINTS_KEY, {}) or {}
    out = []
    for n in CHECKPOINT_DAYS:
        due = _due(start, n)
        pulse = None
        if due:
            d = date.fromisoformat(due)
            row = conn.execute("SELECT date FROM trust_pulses WHERE date BETWEEN ? AND ? ORDER BY date DESC LIMIT 1",
                               ((d - timedelta(days=10)).isoformat(), (d + timedelta(days=10)).isoformat())).fetchone()
            pulse = row["date"] if row else None
        s = saved.get(str(n), {})
        out.append({"day": n, "due": due, "pulse_on": pulse, "done_on": s.get("done_on"), "notes": s.get("notes", ""),
                    "heard": s.get("heard", ""), "changed": s.get("changed", ""), "adapting": s.get("adapting", "")})
    return out


@router.get("/api/first90/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    start = start_date(conn)
    t = today()
    changes = models.team_changes.visible_all(models.team_changes.fetch_all(conn), viewer)
    out = {"start_date": start.isoformat() if start else None, "day": day_number(start),
           "changes": {s: sum(1 for c in changes if c["status"] == s) for s in models.CHANGE_STATUS},
           "working_with_me": bool(_setting(conn, WORKING_KEY)), "private": viewer.floor == Level.PRIVATE}
    # New hires: each on their own clock, from their start date.
    hires = []
    for ob in models.onboardings.visible_all(models.onboardings.fetch_all(conn, "status != 'done'"), viewer):
        s = date.fromisoformat(ob["start_date"]) if ob.get("start_date") else None
        hires.append({"id": ob["id"], "name": ob.get("person_name"), "role": ob.get("person_role"), "start_date": ob.get("start_date"),
                      "day": day_number(s), "done": ob.get("done_count"), "total": ob.get("total")})
    out["new_hires"] = hires
    if viewer.floor != Level.PRIVATE:
        return out
    from .accelerate import momentum

    out["momentum"] = momentum(conn)
    plans = models.plans.fetch_all(conn)
    items = models.plan_items.fetch_all(conn)
    out["me"] = {
        "plans": [{"id": p["id"], "title": p["title"], "horizon_days": p["horizon_days"], "status": p["status"],
                   "done": sum(1 for i in items if i["plan_id"] == p["id"] and i["status"] == "done"),
                   "total": sum(1 for i in items if i["plan_id"] == p["id"] and i["status"] != "dropped"),
                   "due": _due(start, p["horizon_days"])} for p in plans],
        "listening": {"done": conn.execute("SELECT COUNT(*) FROM interviews WHERE status = 'done'").fetchone()[0],
                      "total": conn.execute("SELECT COUNT(*) FROM interviews").fetchone()[0]},
        "reflections": conn.execute("SELECT COUNT(*) FROM reflections").fetchone()[0],
        "items_due": [{"title": i["title"], "due": _due(start, i["due_day"]), "plan_id": i["plan_id"]} for i in items
                      if i["status"] in ("planned", "in progress") and i.get("due_day") and start and _due(start, i["due_day"]) <= (t + timedelta(days=7)).isoformat()][:8],
    }
    team = team_track(conn)
    out["team"] = {"people": [{k: p[k] for k in ("id", "name", "role", "done", "total", "late", "next")} for p in team["people"]], "has_me": team["has_me"]}
    out["checkpoints"] = checkpoints(conn)
    return out


@router.get("/api/first90/team")
def get_team(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    return {**team_track(conn), "checkpoints": checkpoints(conn), "template": _setting(conn, TEMPLATE_KEY) or STARTER_TEMPLATE}


@router.post("/api/first90/team/start", status_code=201)
def start_team(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Give each inherited team member (or the ones named) the milestone list, skipping anyone who already has it."""
    require_write(viewer)
    team = {p["id"] for p in inherited_team(conn)}
    wanted = body.get("person_ids") or sorted(team)
    if not wanted:
        raise HTTPException(400, "Pick your own record under People ('This is me') and set who reports to you first.")
    template = _setting(conn, TEMPLATE_KEY) or STARTER_TEMPLATE
    started = []
    for pid in wanted:
        if not models.people.fetch(conn, pid):
            raise HTTPException(400, "That person doesn't exist.")
        if conn.execute("SELECT 1 FROM first90_milestones WHERE person_id = ?", (pid,)).fetchone():
            continue
        for pos, m in enumerate(template):
            models.first90_milestones.create(conn, {"person_id": pid, "title": m["title"], "due_day": m["due_day"], "auto": m.get("auto"), "position": pos}, viewer.source)
        started.append(pid)
    return {"started": started}


@router.put("/api/first90/template")
def put_template(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    items = body.get("items")
    autos = {None, "one_on_one", "interview", "growth_goal", "feedback", "mandate"}
    if not isinstance(items, list) or not items:
        raise HTTPException(400, "Give at least one milestone.")
    clean = []
    for m in items:
        title, due = (m.get("title") or "").strip(), m.get("due_day")
        if not title or not isinstance(due, int) or not 1 <= due <= 365 or m.get("auto") not in autos:
            raise HTTPException(400, "Each milestone needs a title and a day from 1 to 365.")
        clean.append({"title": title, "due_day": due, "auto": m.get("auto")})
    _put(conn, TEMPLATE_KEY, sorted(clean, key=lambda m: m["due_day"]))
    return {"items": clean}


@router.put("/api/first90/checkpoints/{day}")
def put_checkpoint(day: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if day not in CHECKPOINT_DAYS:
        raise HTTPException(404, "Check-ins are at days 30, 60 and 90.")
    saved = _setting(conn, CHECKPOINTS_KEY, {}) or {}
    saved[str(day)] = {k: body.get(k) for k in ("done_on", "notes", "heard", "changed", "adapting")}
    _put(conn, CHECKPOINTS_KEY, saved)
    return saved[str(day)]


@router.get("/api/first90/working-with-me")
def get_working(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    # Written to be shared with the team, so it shows while presenting too.
    return {"text": _setting(conn, WORKING_KEY, "") or "", "starter": STARTER_WORKING}


@router.put("/api/first90/working-with-me")
def put_working(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    text = (body.get("text") or "").strip()
    _put(conn, WORKING_KEY, text)
    return {"text": text}


@router.post("/api/team-changes/{change_id}/advance")
def advance(change_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Move a change to its next stage and date it. Reviewing it together comes before keeping or dropping it."""
    require_write(viewer)
    ch = models.team_changes.fetch(conn, change_id)
    if not ch:
        raise HTTPException(404, "No such change.")
    status = body.get("status")
    if status not in models.CHANGE_STATUS:
        raise HTTPException(400, "Unknown stage.")
    if status in ("adopted", "dropped") and ch["status"] not in ("trial", "review"):
        raise HTTPException(400, "Try it and review it with the team before keeping or dropping it.")
    on = body.get("on") or today().isoformat()
    data = {"status": status}
    if status in STATUS_DATE:
        data[STATUS_DATE[status]] = on
    if status == "trial" and not ch.get("review_on") and not body.get("review_on"):
        data["review_on"] = (date.fromisoformat(on) + timedelta(days=28)).isoformat()  # about two sprints
    for k in ("review_on", "outcome", "team_feedback"):
        if body.get(k) is not None:
            data[k] = body[k]
    return models.team_changes.update(conn, change_id, data, viewer.source)


def first90_due(conn) -> dict:
    """For Today: late team milestones, a check-in falling this week, and changes due for review."""
    t = today()
    week = (t + timedelta(days=7)).isoformat()
    late = [{"person": p["name"], "person_id": p["id"], "title": m["title"], "due": m["due"]}
            for p in team_track(conn)["people"] for m in p["milestones"] if m["late"]]
    soon = [c for c in checkpoints(conn) if c["due"] and not c["done_on"] and c["due"] <= week and c["due"] >= (t - timedelta(days=14)).isoformat()]
    reviews = [{"id": c["id"], "title": c["title"], "review_on": c["review_on"]}
               for c in models.team_changes.fetch_all(conn, "status IN ('trial', 'review') AND review_on IS NOT NULL AND review_on <= ?", (week,))]
    return {"late": late[:8], "checkpoint": soon[0] if soon else None, "reviews": reviews}


# ---- the five conversations with each of your reports ----
# Transition others as you'd want to be transitioned: the same five conversations you hold with your manager.

REPORT_CONV_KEY = "first90.report_conversations"
FIVE_CONVERSATIONS = ["situation", "expectations", "resources", "style", "development"]
FIVE_STATUS = ("not started", "in progress", "settled")


@router.get("/api/first90/report-conversations")
def report_conversations(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    me = me_id(conn)
    saved = _setting(conn, REPORT_CONV_KEY, {}) or {}
    reports = models.people.fetch_all(conn, "manager_id = ? AND active = 1", (me,)) if me else []
    rows = []
    for p in reports:
        mine = saved.get(str(p["id"]), {})
        rows.append({"id": p["id"], "name": p["name"], "role": p.get("role"),
                     "cells": {t: {"status": mine.get(t, {}).get("status", "not started"), "priority": bool(mine.get(t, {}).get("priority"))} for t in FIVE_CONVERSATIONS}})
    return {"topics": FIVE_CONVERSATIONS, "statuses": list(FIVE_STATUS), "reports": rows, "has_me": bool(me)}


@router.put("/api/first90/report-conversations/{person_id}/{topic}")
def put_report_conversation(person_id: int, topic: str, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if topic not in FIVE_CONVERSATIONS:
        raise HTTPException(404, "No such conversation.")
    if not models.people.fetch(conn, person_id):
        raise HTTPException(404, "No such person.")
    status = body.get("status", "not started")
    if status not in FIVE_STATUS:
        raise HTTPException(400, "Unknown status.")
    saved = _setting(conn, REPORT_CONV_KEY, {}) or {}
    saved.setdefault(str(person_id), {})[topic] = {"status": status, "priority": bool(body.get("priority"))}
    _put(conn, REPORT_CONV_KEY, saved)
    return saved[str(person_id)][topic]
