"""Sprint planning beside Jira: the backlog of candidate stories, refinement against a definition of ready, estimation,
capacity from who's available, and pulling, committing and closing each sprint.

Jira stays the system of record. Stories come in by pasting their keys and titles; the toolkit adds the thinking around
them: readiness, technical notes, vote spread, capacity and the commitment, and a summary to carry back.
"""

import json
import re
from datetime import date, timedelta
from statistics import median

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer
from beanagileorg.core.records import ISSUE_KEY_RE

from . import models
from .routes import require_write

router = APIRouter()
DOR_KEY = "planning.definition_of_ready"
STARTER_DOR = [
    "Has a Jira key and a clear title",
    "The problem or user story is written down",
    "Acceptance criteria agreed, with QA",
    "Dependencies known, and none blocking",
    "Technical approach discussed (design agreed if it needs one)",
    "Small enough to finish in one sprint",
    "Estimated by the team",
]
# INVEST in plain words: a common test of a well-formed story, offered as definition-of-ready checks.
INVEST = [
    "Independent: can be built and released without waiting on another story",
    "Negotiable: the details are open to conversation, not a fixed contract",
    "Valuable: delivers something a user, customer or the business will notice",
    "Estimable: the team understands it well enough to size it",
    "Small: fits comfortably in one sprint",
    "Testable: the acceptance criteria say how we'll know it's done",
]
LINE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*-\d+)\s*[-:|\t]?\s*(.*?)\s*(?:[|\t]\s*(\d{1,3})\s*(?:pts?|points)?)?\s*$")
TEAM = ("employee", "contractor")


def _today() -> str:
    return date.today().isoformat()


def _dor(conn) -> list[str]:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (DOR_KEY,)).fetchone()
    return json.loads(row["value"]) if row else []


PRODUCT_GOAL_KEY = "planning.product_goal"


def product_goal(conn) -> dict:
    """The Scrum Guide's commitment for the Product Backlog: the one long-term objective sprint goals step toward."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (PRODUCT_GOAL_KEY,)).fetchone()
    return json.loads(row["value"]) if row else {"text": "", "updated_on": None}


def working_days(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    d, e, n = date.fromisoformat(start), date.fromisoformat(end), 0
    while d <= e:
        n += d.weekday() < 5
        d += timedelta(days=1)
    return n


def spread(votes: list[dict]) -> dict | None:
    """The latest round's votes, and whether they're far enough apart to talk about before settling."""
    if not votes:
        return None
    last = max(v["round"] for v in votes)
    pts = [v["points"] for v in votes if v["round"] == last]
    lo, hi = min(pts), max(pts)
    return {"round": last, "votes": [{"person": v.get("person_name"), "points": v["points"]} for v in votes if v["round"] == last],
            "low": lo, "high": hi, "median": median(pts), "discuss": hi - lo >= 3 and hi >= 2 * max(lo, 1)}


def _decorate(conn, items: list[dict]) -> list[dict]:
    dor = _dor(conn)
    votes = {}
    for v in models.estimate_votes.fetch_all(conn):
        votes.setdefault(v["item_id"], []).append(v)
    out = []
    for i in items:
        met = [c for c in dor if c in (i.get("ready_checks") or [])]
        out.append({**i, "ready_met": len(met), "ready_total": len(dor), "spread": spread(votes.get(i["id"], []))})
    return out


# ---- definition of ready ----


@router.get("/api/planning/definition-of-ready")
def get_dor(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"items": _dor(conn)}


@router.put("/api/planning/definition-of-ready")
def put_dor(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    items = [i.strip() for i in body.get("items", []) if isinstance(i, str) and i.strip()]
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (DOR_KEY, json.dumps(items)))
    return {"items": items}


@router.post("/api/planning/definition-of-ready/invest")
def invest_dor(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Add the six INVEST checks to the definition of ready, skipping any already there."""
    require_write(viewer)
    current = _dor(conn)
    return put_dor({"items": current + [i for i in INVEST if i not in current]}, viewer, conn)


@router.post("/api/planning/definition-of-ready/starter")
def starter_dor(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if _dor(conn):
        raise HTTPException(409, "There's already a definition of ready. Edit it instead.")
    return put_dor({"items": STARTER_DOR}, viewer, conn)


@router.get("/api/planning/product-goal")
def get_product_goal(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return product_goal(conn)


@router.put("/api/planning/product-goal")
def put_product_goal(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    value = {"text": (body.get("text") or "").strip(), "updated_on": _today()}
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                 (PRODUCT_GOAL_KEY, json.dumps(value)))
    return value


# ---- the backlog ----


@router.get("/api/backlog")
def backlog(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    items = models.backlog_items.visible_all(models.backlog_items.fetch_all(conn, "sprint_id IS NULL AND status NOT IN ('done', 'removed')"), viewer)
    return {"items": _decorate(conn, items), "definition_of_ready": _dor(conn), "product_goal": product_goal(conn)}


@router.post("/api/backlog/paste")
def paste(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """One story per line: "ABC-123 Title", optionally ending "| 5" for points. Known keys are skipped unless update is true."""
    require_write(viewer)
    lines = [ln for ln in (body.get("text") or "").splitlines() if ln.strip()]
    rank = conn.execute("SELECT COALESCE(MAX(rank), 0) FROM backlog_items").fetchone()[0]
    added, updated, skipped, problems = 0, 0, 0, []
    for ln in lines:
        m = LINE_RE.match(ln)
        if not m or not ISSUE_KEY_RE.match(m.group(1).upper()):
            problems.append(ln.strip()[:80])
            continue
        key, title, pts = m.group(1).upper(), m.group(2).strip() or m.group(1).upper(), m.group(3)
        found = models.backlog_items.fetch_all(conn, "jira_key = ?", (key,))
        if found:
            if body.get("update"):
                changes = {"title": title}
                if pts:
                    changes["points"] = int(pts)
                models.backlog_items.update(conn, found[0]["id"], changes, viewer.source)
                updated += 1
            else:
                skipped += 1
            continue
        rank += 1
        models.backlog_items.create(conn, {"jira_key": key, "title": title, "points": int(pts) if pts else None, "rank": rank, "added_on": _today(), "team_id": body.get("team_id")}, viewer.source)
        added += 1
    return {"added": added, "updated": updated, "skipped": skipped, "not_understood": problems}


@router.post("/api/backlog/reorder")
def reorder(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    ids = body.get("ids") or []
    for pos, item_id in enumerate(ids, 1):
        conn.execute("UPDATE backlog_items SET rank = ? WHERE id = ?", (pos, item_id))
    return {"order": ids}


@router.post("/api/backlog-items/{item_id}/votes", status_code=201)
def vote(item_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record a round of estimates, one per person. A new round replaces nothing; the spread uses the latest round."""
    require_write(viewer)
    if not models.backlog_items.fetch(conn, item_id):
        raise HTTPException(404, "No such backlog item.")
    entries = [v for v in body.get("votes", []) if isinstance(v.get("points"), int) and not isinstance(v.get("points"), bool)]
    if not entries:
        raise HTTPException(400, "Add at least one estimate in points.")
    known = {r[0] for r in conn.execute("SELECT id FROM people")}
    if any(v.get("person_id") is not None and v["person_id"] not in known for v in entries):
        raise HTTPException(400, "One of those people isn't in People.")
    last = conn.execute("SELECT COALESCE(MAX(round), 0) FROM estimate_votes WHERE item_id = ?", (item_id,)).fetchone()[0]
    for v in entries:
        models.estimate_votes.create(conn, {"item_id": item_id, "person_id": v.get("person_id"), "points": v["points"], "round": last + 1, "date": _today()}, viewer.source)
    return spread(models.estimate_votes.fetch_all(conn, "item_id = ?", (item_id,)))


@router.post("/api/tech-debt/{debt_id}/to-backlog", status_code=201)
def debt_to_backlog(debt_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    d = models.tech_debt.fetch(conn, debt_id)
    if d is None:
        raise HTTPException(404, "No such debt item.")
    if conn.execute("SELECT 1 FROM backlog_items WHERE debt_id = ?", (debt_id,)).fetchone():
        raise HTTPException(409, "This debt is already on the backlog.")
    if d["ticket_key"] and conn.execute("SELECT 1 FROM backlog_items WHERE jira_key = ?", (d["ticket_key"],)).fetchone():
        raise HTTPException(409, f"{d['ticket_key']} is already on the backlog.")
    rank = conn.execute("SELECT COALESCE(MAX(rank), 0) + 1 FROM backlog_items").fetchone()[0]
    return models.backlog_items.create(conn, {"jira_key": d["ticket_key"], "title": d["title"], "item_type": "tech debt", "description": d["description"],
                                              "points": d["points"], "debt_id": debt_id, "system_ids": d["system_ids"], "rank": rank, "added_on": _today()}, viewer.source)


# ---- planning a sprint ----


def _sprint_or_404(conn, sprint_id: int) -> dict:
    s = models.sprints.fetch(conn, sprint_id)
    if s is None:
        raise HTTPException(404, "No such sprint.")
    return s


def _plan(conn, sprint_id: int) -> dict:
    rows = models.sprint_plans.fetch_all(conn, "sprint_id = ?", (sprint_id,))
    return rows[0] if rows else models.sprint_plans.create(conn, {"sprint_id": sprint_id}, "planning")


def _velocity(conn, before_number: int, team_id: int | None) -> dict:
    rows = conn.execute(
        "SELECT s.number, p.completed_points FROM sprint_plans p JOIN sprints s ON s.id = p.sprint_id "
        "WHERE p.status = 'closed' AND p.completed_points IS NOT NULL AND s.number < ? AND s.team_id IS ? ORDER BY s.number DESC LIMIT 6", (before_number, team_id)).fetchall()
    history = [{"sprint": r["number"], "completed": r["completed_points"]} for r in reversed(rows)]
    recent = [h["completed"] for h in history[-3:]]
    return {"history": history, "average": round(sum(recent) / len(recent)) if recent else None}


def _timeboxes(conn) -> dict:
    """The Scrum Guide's limits for the events, scaled to the team's sprint length (set in the Agile reference)."""
    from .agile import DEFAULT_SPRINT_WEEKS, SPRINT_WEEKS_KEY, timebox_for

    row = conn.execute("SELECT value FROM settings WHERE key = ?", (SPRINT_WEEKS_KEY,)).fetchone()
    weeks = int(row["value"]) if row else DEFAULT_SPRINT_WEEKS
    return {"weeks": weeks, "planning": timebox_for("sprint-planning", weeks), "review": timebox_for("sprint-review", weeks),
            "retro": timebox_for("retrospective", weeks), "daily": "15 minutes, every working day"}


def build_plan(conn, sprint_id: int, viewer: Viewer) -> dict:
    s = _sprint_or_404(conn, sprint_id)
    plan = models.sprint_plans.visible(_plan(conn, sprint_id), viewer)
    days = working_days(s["start_date"], s["end_date"])
    # The sprint's team members if the team lists them; otherwise everyone who's an employee or contractor.
    members = []
    if s.get("team_id"):
        row = conn.execute("SELECT member_ids FROM teams WHERE id = ?", (s["team_id"],)).fetchone()
        members = json.loads(row["member_ids"]) if row and row["member_ids"] else []
    team = [p for p in models.people.fetch_all(conn) if p["active"] and (p["id"] in members if members else p["relationship"] in TEAM)]
    avail = {a["person_id"]: a for a in models.sprint_availability.fetch_all(conn, "sprint_id = ?", (sprint_id,))}
    people = [{"person_id": p["id"], "name": p["name"], "days": avail.get(p["id"], {}).get("days", days), "note": avail.get(p["id"], {}).get("note")} for p in team]
    full = (days or 0) * len(team)
    available = sum(p["days"] or 0 for p in people)
    ratio = available / full if full else None
    vel = _velocity(conn, s["number"], s.get("team_id"))
    suggested = round(vel["average"] * ratio) if vel["average"] is not None and ratio is not None else None
    capacity = plan["capacity_override"] or suggested or s["capacity"]
    pulled = _decorate(conn, models.backlog_items.visible_all(models.backlog_items.fetch_all(conn, "sprint_id = ?", (sprint_id,)), viewer))
    ready = _decorate(conn, models.backlog_items.visible_all(models.backlog_items.fetch_all(conn, "sprint_id IS NULL AND status = 'ready' AND team_id IS ?", (s.get("team_id"),)), viewer))
    prev = conn.execute("SELECT id, number FROM sprints WHERE number < ? AND team_id IS ? ORDER BY number DESC LIMIT 1", (s["number"], s.get("team_id"))).fetchone()
    carried = [i for i in pulled if i.get("carried_from_id")]
    planned_points = sum(i.get("points") or 0 for i in pulled)
    return {
        "sprint": models.sprints.visible(s, viewer), "plan": plan, "working_days": days, "people": people,
        "capacity": {"available_days": available, "full_days": full, "ratio": round(ratio, 2) if ratio is not None else None,
                     "velocity": vel, "suggested": suggested, "points": capacity, "planned": planned_points,
                     "unestimated": sum(1 for i in pulled if i.get("points") is None)},
        "pulled": pulled, "ready": ready, "carried": carried, "previous": dict(prev) if prev else None,
        "product_goal": product_goal(conn),
        "timeboxes": _timeboxes(conn),
    }


@router.get("/api/sprint-planning/{sprint_id}")
def planning(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_plan(conn, sprint_id, viewer)


@router.put("/api/sprint-planning/{sprint_id}/availability")
def set_availability(sprint_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _sprint_or_404(conn, sprint_id)
    pid = body.get("person_id")
    found = models.sprint_availability.fetch_all(conn, "sprint_id = ? AND person_id = ?", (sprint_id, pid))
    data = {k: body[k] for k in ("days", "note") if k in body}
    if found:
        models.sprint_availability.update(conn, found[0]["id"], data, viewer.source)
    else:
        models.sprint_availability.create(conn, {"sprint_id": sprint_id, "person_id": pid, **data}, viewer.source)
    return build_plan(conn, sprint_id, viewer)["capacity"]


@router.post("/api/sprint-planning/{sprint_id}/pull")
def pull(sprint_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _sprint_or_404(conn, sprint_id)
    item = models.backlog_items.fetch(conn, body.get("item_id") or 0)
    if item is None:
        raise HTTPException(404, "No such backlog item.")
    plan = _plan(conn, sprint_id)
    changes = {"sprint_id": sprint_id}
    if plan["status"] == "committed":
        changes["status"] = "in sprint"
    models.backlog_items.update(conn, item["id"], changes, viewer.source)
    return {"pulled": item["id"], "warning": None if item["status"] == "ready" else "This story isn't marked ready yet."}


@router.post("/api/sprint-planning/{sprint_id}/return")
def return_to_backlog(sprint_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    item = models.backlog_items.fetch(conn, body.get("item_id") or 0)
    if item is None or item["sprint_id"] != sprint_id:
        raise HTTPException(404, "That story isn't in this sprint.")
    models.backlog_items.update(conn, item["id"], {"sprint_id": None, "status": "ready" if item["status"] == "in sprint" else item["status"]}, viewer.source)
    return {"returned": item["id"]}


@router.post("/api/sprint-planning/{sprint_id}/commit")
def commit(sprint_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Snapshot what the team committed to, and mark the stories as in the sprint."""
    require_write(viewer)
    s = _sprint_or_404(conn, sprint_id)
    if body.get("goal") is not None:
        models.sprints.update(conn, sprint_id, {"goal": body["goal"]}, viewer.source)
    items = models.backlog_items.fetch_all(conn, "sprint_id = ?", (sprint_id,))
    if not items:
        raise HTTPException(400, "Pull at least one story into the sprint first.")
    if not (body.get("goal") or s["goal"]):
        raise HTTPException(400, "Write a sprint goal before committing.")
    for i in items:
        if i["status"] not in ("done", "removed"):
            models.backlog_items.update(conn, i["id"], {"status": "in sprint"}, viewer.source)
    plan = _plan(conn, sprint_id)
    return models.sprint_plans.update(conn, plan["id"], {"status": "committed", "committed_on": _today(), "committed_points": sum(i["points"] or 0 for i in items)}, viewer.source)


@router.post("/api/sprint-planning/{sprint_id}/close")
def close(sprint_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Count what got done; unfinished stories carry into the next sprint if there is one, or back to the backlog."""
    require_write(viewer)
    s = _sprint_or_404(conn, sprint_id)
    items = models.backlog_items.fetch_all(conn, "sprint_id = ?", (sprint_id,))
    done = sum(i["points"] or 0 for i in items if i["status"] == "done")
    nxt = conn.execute("SELECT id FROM sprints WHERE number > ? AND team_id IS ? ORDER BY number LIMIT 1", (s["number"], s["team_id"])).fetchone()
    to = body.get("carry_to", nxt["id"] if nxt else None)
    carried = 0
    for i in items:
        if i["status"] in ("done", "removed"):
            continue
        models.backlog_items.update(conn, i["id"], {"sprint_id": to, "carried_from_id": sprint_id, "status": "ready"}, viewer.source)
        carried += 1
    plan = _plan(conn, sprint_id)
    models.sprint_plans.update(conn, plan["id"], {"status": "closed", "completed_points": done, "closed_on": _today()}, viewer.source)
    return {"completed_points": done, "committed_points": plan["committed_points"], "carried": carried, "carried_to": to}


def _sprint_days(start: str, end: str) -> list[str]:
    d, e, out = date.fromisoformat(start), date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def burndown(conn, sprint_id: int) -> dict:
    """Points remaining at the end of each working day, rebuilt from the change log: when each story joined or left the
    sprint, and when it was marked done or removed. No daily data entry. The ideal line runs from what was in the sprint
    on its first day to zero on its last."""
    s = _sprint_or_404(conn, sprint_id)
    if not s.get("start_date") or not s.get("end_date"):
        return {"days": [], "reason": "Set the sprint's dates in the sprint notebook to see its burndown."}
    days = _sprint_days(s["start_date"], s["end_date"])
    if not days:
        return {"days": [], "reason": "The sprint has no working days."}
    sid = str(sprint_id)
    rows = conn.execute(
        "SELECT record_id, field, new_value, date(datetime(at, 'localtime')) AS d FROM change_log "
        "WHERE entity = 'backlog_item' AND field IN ('sprint_id', 'status') ORDER BY id").fetchall()
    ids = {r["record_id"] for r in rows if r["field"] == "sprint_id" and r["new_value"] == sid}
    ids |= {str(i["id"]) for i in models.backlog_items.fetch_all(conn, "sprint_id = ?", (sprint_id,))}
    items = {str(i["id"]): i for i in models.backlog_items.fetch_all(conn) if str(i["id"]) in ids}
    events = {}
    for r in rows:
        if r["record_id"] in items:
            events.setdefault(r["record_id"], []).append(r)

    def state(item_id: str, day: str) -> tuple[bool, str]:
        """Whether the story was in the sprint at the end of the given day, and its status then."""
        if item_id not in events:  # no history: in the sprint from the start, at its current status
            return True, items[item_id]["status"]
        in_sprint, status = False, "needs refinement"
        for e in events[item_id]:
            if e["d"] > day:
                break
            if e["field"] == "sprint_id":
                in_sprint = e["new_value"] == sid
            else:
                status = e["new_value"]
        return in_sprint, status

    def totals(day: str) -> tuple[int, int]:
        """(scope, remaining) in points at the end of the day; removed stories leave the scope."""
        scope = remaining = 0
        for i, item in items.items():
            in_sprint, status = state(i, day)
            if not in_sprint or status == "removed":
                continue
            scope += item.get("points") or 0
            if status != "done":
                remaining += item.get("points") or 0
        return scope, remaining

    start_scope = totals(days[0])[0]
    today = date.today().isoformat()
    out, prev_scope = [], None
    for n, day in enumerate(days):
        ideal = round(start_scope * (1 - n / (len(days) - 1)), 1) if len(days) > 1 else 0
        point = {"date": day, "ideal": ideal, "remaining": None, "scope": None, "change": 0}
        if day <= today:
            scope, remaining = totals(day)
            point.update(remaining=remaining, scope=scope, change=0 if prev_scope is None else scope - prev_scope)
            prev_scope = scope
        out.append(point)
    added = sum(p["change"] for p in out if p["change"] > 0)
    dropped = -sum(p["change"] for p in out if p["change"] < 0)
    return {"sprint": s["number"], "goal": s.get("goal"), "start_scope": start_scope, "days": out,
            "scope_added": added, "scope_removed": dropped, "unestimated": sum(1 for i in items if items[i].get("points") is None)}


@router.get("/api/sprint-planning/{sprint_id}/burndown")
def get_burndown(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return burndown(conn, sprint_id)


REVIEW_LABEL = "sprint review"


def _review_feedback(conn, number: int) -> list[dict]:
    tag = f"sprint {number}"
    return [i for i in models.backlog_items.fetch_all(conn) if REVIEW_LABEL in (i.get("labels") or []) and tag in (i.get("labels") or [])]


def build_review(conn, sprint_id: int, viewer: Viewer) -> dict:
    """What the sprint review works from: progress toward the sprint and product goals, the done work to show,
    what isn't done, and the feedback captured so far as new backlog items. A working session, not a presentation."""
    s = _sprint_or_404(conn, sprint_id)
    items = _decorate(conn, models.backlog_items.visible_all(models.backlog_items.fetch_all(conn, "sprint_id = ?", (sprint_id,)), viewer))
    carried = _decorate(conn, models.backlog_items.visible_all(models.backlog_items.fetch_all(conn, "carried_from_id = ?", (sprint_id,)), viewer))
    done = [i for i in items if i["status"] == "done"]
    open_ = [i for i in items if i["status"] not in ("done", "removed")] + [i for i in carried if i["id"] not in {x["id"] for x in items}]
    feedback = models.backlog_items.visible_all(_review_feedback(conn, s["number"]), viewer)
    pg = product_goal(conn)["text"]
    key = lambda i: f"{i['jira_key']} " if i.get("jira_key") else ""
    lines = [f"# Sprint {s['number']} review", ""]
    if pg:
        lines += [f"**Product goal:** {pg}", ""]
    lines += [f"**Sprint goal:** {s.get('goal') or '[Placeholder: sprint goal]'}", "",
              f"## Done and ready to show ({sum(i.get('points') or 0 for i in done)} points)", ""]
    lines += [f"- {key(i)}{i['title']}" for i in done] or ["- Nothing finished yet."]
    lines += ["", "## Not done", ""] + ([f"- {key(i)}{i['title']}" for i in open_] or ["- Everything planned is done."])
    lines += ["", "## Questions for the room", "", "- What did we learn about what users need?",
              "- What has changed in the market, the timeline or the budget?", "- What should we do next to move toward the product goal?"]
    if feedback:
        lines += ["", "## Feedback captured", ""] + [f"- {i['title']}" for i in feedback]
    return {"sprint": models.sprints.visible(s, viewer), "product_goal": pg, "done": done, "not_done": open_, "feedback": feedback,
            "timebox": _timeboxes(conn)["review"], "markdown": "\n".join(lines) + "\n"}


@router.get("/api/sprint-planning/{sprint_id}/review")
def get_review(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_review(conn, sprint_id, viewer)


@router.post("/api/sprint-planning/{sprint_id}/review/feedback", status_code=201)
def add_feedback(sprint_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Stakeholder feedback from the review becomes a backlog item to refine, so the review adjusts the backlog."""
    require_write(viewer)
    s = _sprint_or_404(conn, sprint_id)
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Write the feedback first.")
    who = (body.get("from") or "").strip()
    rank = conn.execute("SELECT COALESCE(MAX(rank), 0) + 1 FROM backlog_items").fetchone()[0]
    return models.backlog_items.create(conn, {
        "title": text[:200], "description": f"From the sprint {s['number']} review" + (f", raised by {who}." if who else "."),
        "labels": [REVIEW_LABEL, f"sprint {s['number']}"], "rank": rank, "added_on": _today()}, viewer.source)


def build_summary(conn, sprint_id: int) -> dict:
    d = build_plan(conn, sprint_id, Viewer(floor=Level.PRESENTABLE, source="plan", scopes=frozenset()))
    s, cap = d["sprint"], d["capacity"]
    lines = [f"# Sprint {s['number']} plan", ""]
    if s.get("start_date"):
        lines += [f"{s['start_date']} to {s.get('end_date') or ''}", ""]
    if d["product_goal"]["text"]:
        lines += [f"**Product goal:** {d['product_goal']['text']}", ""]
    lines += [f"**Goal:** {s.get('goal') or '[Placeholder: sprint goal]'}", ""]
    cap_line = f"**Capacity:** {cap['points']} points" if cap["points"] is not None else "**Capacity:** not set"
    if cap["ratio"] is not None and cap["full_days"]:
        cap_line += f" ({cap['available_days']} of {cap['full_days']} person-days available"
        cap_line += f", recent velocity {cap['velocity']['average']})" if cap["velocity"]["average"] is not None else ")"
    lines += [cap_line + f". Planned: {cap['planned']} points.", ""]
    if d["pulled"]:
        lines += ["| Jira | Story | Points | Owner |", "| --- | --- | --- | --- |"]
        lines += [f"| {i.get('jira_key') or ''} | {i['title']}{' (carried over)' if i.get('carried_from_id') else ''} | {i.get('points') if i.get('points') is not None else '?'} | {i.get('owner_name') or ''} |" for i in d["pulled"]]
    deps = [i for i in d["pulled"] if i.get("dependencies")]
    if deps:
        lines += ["", "## Dependencies to watch", ""] + [f"- {i.get('jira_key') or i['title']}: {i['dependencies']}" for i in deps]
    away = [p for p in d["people"] if d["working_days"] and (p["days"] or 0) < d["working_days"]]
    if away:
        lines += ["", "## Availability", ""] + [f"- {p['name']}: {p['days']} of {d['working_days']} days" for p in away]
    return {"title": f"Sprint {s['number']} plan", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/sprint-planning/{sprint_id}/summary")
def summary(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_summary(conn, sprint_id)


@router.post("/api/sprint-planning/{sprint_id}/summary/export")
def export_summary(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_summary(conn, sprint_id)
    log_export(conn, "sprint-plan:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


def planning_due(conn) -> list[dict]:
    """For Today: sprints starting in the next five days that aren't committed yet."""
    soon = (date.today() + timedelta(days=5)).isoformat()
    rows = conn.execute(
        "SELECT s.id, s.number, s.start_date FROM sprints s LEFT JOIN sprint_plans p ON p.sprint_id = s.id "
        "WHERE s.start_date >= ? AND s.start_date <= ? AND (p.status IS NULL OR p.status = 'planning') ORDER BY s.start_date", (_today(), soon)).fetchall()
    ready = conn.execute("SELECT COUNT(*), COALESCE(SUM(points), 0) FROM backlog_items WHERE sprint_id IS NULL AND status = 'ready'").fetchone()
    return [{"sprint_id": r["id"], "number": r["number"], "start_date": r["start_date"], "ready_stories": ready[0], "ready_points": ready[1]} for r in rows]
