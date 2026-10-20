"""Weekly and sprint reports, the daily work log behind them, and the activity feed.

You note things as they happen (the work log) and keep working as usual; the change log already records
every update with a timestamp. A report for any week, or any sprint split into its weeks, is drafted from
both. Drafts are built at the audience's privacy level: leadership reports use only exportable data, your
manager's report can also use presentable data, and nothing private ever goes in. Private activity can be
promoted into the log on purpose, with an audience you choose.
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer
from beanagileorg.core.records import REGISTRY
from beanagileorg.core.sensitivity import JUDGMENT_TABLES

from . import models, weeks
from .reporting import _day_to_date, my_team_id
from .routes import START_DATE_KEY, require_write, today

router = APIRouter()

AUDIENCE_FLOOR = {"leadership": Level.EXPORTABLE, "my manager": Level.PRESENTABLE}
KIND_LABELS = {"win": "Win", "progress": "Progress", "blocker": "Blocker", "risk": "Risk", "decision": "Decision",
               "ask": "Ask", "next": "Next", "note": "Note"}

# What the activity feed follows: label, where it lives, the field that names it, and the statuses that count as finished.
SOURCES = {
    "action_item": ("Dev-sync item", "/dev-sync", "concern", {"done"}),
    "risk": ("Risk", "/risks", "title", {"closed"}),
    "decision_needed": ("Decision", "/risks", "decision", {"decided"}),
    "roadmap_item": ("Roadmap", "/roadmap", "title", {"done"}),
    "backlog_item": ("Story", "/planning", "title", {"done"}),
    "sos_item": ("Scrum of Scrums", "/sos", "question", {"done"}),
    "tech_debt": ("Tech debt", "/debt", "title", {"done"}),
    "incident": ("Incident", "/escalation", "summary", set()),
    "retro_commitment": ("Retro commitment", "/retros", "commitment", {"done"}),
    "commitment": ("Commitment", "/people", "title", {"done"}),
    "vendor_concern": ("Vendor concern", "/vendors", "title", {"resolved"}),
    "arch_decision": ("Architecture decision", "/architecture", "title", {"accepted"}),
    "interaction": ("Conversation", "/people", "title", set()),
    "test_run": ("Test run", "/qa", "name", {"done"}),
    "regression_plan": ("Regression plan", "/qa", "title", {"signed off", "done"}),
    "plan_item": ("Plan item", "/plans", "title", {"done"}),
    "pi_objective": ("PI objective", "/pi", "title", {"done"}),
    "growth_goal": ("Growth goal", "/people", "goal", {"achieved"}),
    "culture_observation": ("Culture note", "/culture/noticing", "title", {"addressed"}),
    "learning_session": ("Learning session", "/learning", "topic", {"done"}),
    "team_agreement": ("Team agreement", "/culture/agreements", "text", {"agreed"}),
    "change_request": ("Change request", "/changes", "title", {"decided"}),
    "team_change": ("Team change", "/first90/changes", "title", {"adopted"}),
}


def _parse(value: str | None, name: str) -> date:
    try:
        return date.fromisoformat(value) if value else today()
    except ValueError:
        raise HTTPException(400, f"{name} must be a date (YYYY-MM-DD).")


def _private(viewer: Viewer) -> bool:
    return viewer.floor == Level.PRIVATE


# ---- weeks ----


@router.get("/api/weeks")
def get_week(on: str | None = None, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The week a date falls in (today by default), plus the twelve weeks before it, for pickers."""
    d = _parse(on, "on")
    info = weeks.week_info(conn, d)
    recent = [weeks.week_info(conn, date.fromisoformat(info["start"]) - timedelta(days=7 * n)) for n in range(0, 13)]
    return {**info, "recent": recent, "week_start_day": weeks.week_start_day(conn), "report_day": weeks.report_day(conn)}


@router.put("/api/weeks/settings")
def put_week_settings(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = {}
    for key, setting in (("week_start_day", weeks.WEEK_START_KEY), ("report_day", weeks.REPORT_DAY_KEY)):
        if key in body:
            v = body[key]
            if not isinstance(v, int) or not 0 <= v <= 6:
                raise HTTPException(400, "Days are numbered 0 (Monday) to 6 (Sunday).")
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (setting, str(v)))
            out[key] = v
    return out


@router.get("/api/weeks/stamp")
def get_stamp(on: str, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return weeks.stamp(conn, _parse(on, "on"))


# ---- activity ----


def _name(entity: str, rec: dict) -> str:
    field = SOURCES[entity][2]
    text = (rec.get(field) or "").strip()
    return (text[:140] + "…") if len(text) > 140 else text or f"[{SOURCES[entity][0]} {rec['id']}]"


def activity(conn, start: date, end: date) -> list[dict]:
    """What was added or changed status between two dates (inclusive), from the change log, newest first."""
    ents = tuple(SOURCES)
    marks = ",".join("?" * len(ents))
    s, e = start.isoformat(), end.isoformat()
    events = []
    created = conn.execute(
        f"SELECT entity, record_id, MIN(datetime(at, 'localtime')) AS at FROM change_log WHERE entity IN ({marks}) "
        "GROUP BY entity, record_id HAVING date(at) BETWEEN ? AND ?", (*ents, s, e)).fetchall()
    for r in created:
        events.append({"entity": r["entity"], "id": int(r["record_id"]), "at": r["at"], "event": "added"})
    changed = conn.execute(
        f"SELECT entity, record_id, old_value, new_value, datetime(at, 'localtime') AS at FROM change_log WHERE entity IN ({marks}) "
        "AND field = 'status' AND old_value IS NOT NULL AND date(datetime(at, 'localtime')) BETWEEN ? AND ?", (*ents, s, e)).fetchall()
    for r in changed:
        done = r["new_value"] in SOURCES[r["entity"]][3]
        events.append({"entity": r["entity"], "id": int(r["record_id"]), "at": r["at"], "event": "finished" if done else "status",
                       "from": r["old_value"], "to": r["new_value"]})
    out = []
    for ev in events:
        rec = REGISTRY[ev["entity"]].fetch(conn, ev["id"])
        if not rec:
            continue  # deleted since
        label, path, _, _ = SOURCES[ev["entity"]]
        out.append({**ev, "date": ev["at"][:10], "type": label, "path": path, "title": _name(ev["entity"], rec),
                    "points": rec.get("points") if ev["entity"] == "backlog_item" else None,
                    "promoted": bool(conn.execute("SELECT 1 FROM work_log WHERE source_entity = ? AND source_id = ?", (ev["entity"], ev["id"])).fetchone())})
    out.sort(key=lambda x: x["at"], reverse=True)
    return out


@router.get("/api/activity")
def get_activity(start: str | None = None, end: str | None = None, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Private: everything you did or changed in a period, by day, with each day's week and sprint week."""
    if not _private(viewer):
        return {"hidden": True}
    s = _parse(start, "start")
    e = _parse(end, "end") if end else s + timedelta(days=6)
    if e < s:
        raise HTTPException(400, "The end date is before the start date.")
    events = activity(conn, s, e)
    if viewer.guarded:
        events = [ev for ev in events if REGISTRY[ev["entity"]].table not in JUDGMENT_TABLES]
    log = models.work_log.fetch_all(conn, "date BETWEEN ? AND ?", (s.isoformat(), e.isoformat()))
    days = {}
    for ev in events:
        days.setdefault(ev["date"], {"events": [], "log": []})["events"].append(ev)
    for entry in log:
        days.setdefault(entry["date"], {"events": [], "log": []})["log"].append(entry)
    return {"start": s.isoformat(), "end": e.isoformat(),
            "days": [{"date": d, "stamp": weeks.stamp(conn, d), **v} for d, v in sorted(days.items(), reverse=True)]}


@router.post("/api/activity/promote", status_code=201)
def promote(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn something from the activity feed into a work log entry, with the words and audience you choose."""
    require_write(viewer)
    entity, rid = body.get("entity"), body.get("id")
    if entity not in SOURCES or not isinstance(rid, int) or not REGISTRY[entity].fetch(conn, rid):
        raise HTTPException(400, "That item doesn't exist.")
    if conn.execute("SELECT 1 FROM work_log WHERE source_entity = ? AND source_id = ?", (entity, rid)).fetchone():
        raise HTTPException(409, "Already in the work log.")
    data = {k: body.get(k) for k in ("date", "kind", "text", "audience", "jira_keys") if body.get(k) is not None}
    data.update(source_entity=entity, source_id=rid)
    return models.work_log.create(conn, data, viewer.source)


# ---- report building ----


def _log(conn, s: date, e: date, floor: Level, kinds: tuple) -> list[dict]:
    rows = models.work_log.fetch_all(conn, f"date BETWEEN ? AND ? AND kind IN ({','.join('?' * len(kinds))})", (s.isoformat(), e.isoformat(), *kinds))
    return sorted(models.work_log.visible_all(rows, Viewer(floor=floor, source="report")), key=lambda r: (r["date"], r["id"]))


def _bullet(entry: dict, with_day: bool = False) -> str:
    keys = entry.get("jira_keys") or []
    day = f"{datetime.fromisoformat(entry['date']).strftime('%a')}: " if with_day else ""
    return f"- {day}{entry['text']}" + (f" ({', '.join(keys)})" if keys else "")


def _finished(conn, entity: str, s: date, e: date) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT record_id FROM change_log WHERE entity = ? AND field = 'status' AND new_value IN ({}) "
        "AND date(datetime(at, 'localtime')) BETWEEN ? AND ?".format(",".join("?" * len(SOURCES[entity][3]))),
        (entity, *SOURCES[entity][3], s.isoformat(), e.isoformat())).fetchall()
    return [r["record_id"] for r in rows]


def _stories_done(conn, s: date, e: date, sprint_id: int | None = None) -> tuple[int, int]:
    ids = _finished(conn, "backlog_item", s, e)
    if not ids:
        return 0, 0
    q = f"SELECT COUNT(*) AS n, COALESCE(SUM(points), 0) AS pts FROM backlog_items WHERE status = 'done' AND id IN ({','.join('?' * len(ids))})"
    args = list(ids)
    if sprint_id:
        q += " AND sprint_id = ?"
        args.append(sprint_id)
    row = conn.execute(q, args).fetchone()
    return row["n"], row["pts"]


def _roadmap(conn, floor: Level) -> list[dict]:
    start = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    items = models.roadmap_items.visible_all(models.roadmap_items.fetch_all(conn), Viewer(floor=floor, source="report"))
    for r in items:
        r["target_date"] = _day_to_date(start["value"] if start else None, r.get("target_day"))
    return items


def _sprint_progress(conn, sprint: dict) -> dict:
    plan = conn.execute("SELECT committed_points, completed_points, status FROM sprint_plans WHERE sprint_id = ?", (sprint["id"],)).fetchone()
    done = conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(points), 0) AS pts FROM backlog_items WHERE sprint_id = ? AND status = 'done'", (sprint["id"],)).fetchone()
    total = conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(points), 0) AS pts FROM backlog_items WHERE sprint_id = ? AND status != 'removed'", (sprint["id"],)).fetchone()
    committed = plan["committed_points"] if plan and plan["committed_points"] is not None else total["pts"]
    return {"committed": committed, "done_points": done["pts"], "done_stories": done["n"], "stories": total["n"],
            "plan_status": plan["status"] if plan else None, "completed": plan["completed_points"] if plan else None}


def _overall(risks: list[dict], decisions: list[dict], roadmap: list[dict], on: str) -> tuple[str, str]:
    if any(r["level"] == "high" and r["status"] == "open" for r in risks):
        return "Red", "a high risk is open"
    if any(r["status"] == "at risk" and r.get("target_date") and r["target_date"] < on for r in roadmap):
        return "Red", "an at-risk milestone has passed its date"
    if any(r["status"] == "at risk" for r in roadmap) or any(d.get("needed_by") and d["needed_by"] < on for d in decisions):
        return "Yellow", "something is at risk or a decision is overdue"
    return "Green", "on track"


def _table(headers, rows) -> str:
    if not rows:
        return "_None._"
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    return "\n".join(lines + ["| " + " | ".join("" if c in (None, "") else str(c) for c in row) + " |" for row in rows])


def build_weekly(conn, week_of: date, audience: str = "leadership") -> dict:
    if audience not in AUDIENCE_FLOOR:
        raise HTTPException(400, "Audience is leadership or my manager.")
    floor = AUDIENCE_FLOOR[audience]
    viewer = Viewer(floor=floor, source="report")
    info = weeks.week_info(conn, week_of)
    s, e = date.fromisoformat(info["start"]), date.fromisoformat(info["end"])
    roadmap = _roadmap(conn, floor)
    risks = models.risks.visible_all(models.risks.fetch_all(conn, "status != 'closed'"), viewer)
    decisions = models.decisions_needed.visible_all(models.decisions_needed.fetch_all(conn, "status = 'open'"), viewer)
    overall, why = _overall(risks, decisions, roadmap, e.isoformat())
    done_ids = set(_finished(conn, "roadmap_item", s, e))
    shipped = [r for r in roadmap if str(r["id"]) in done_ids and r["status"] == "done"]
    n_stories, pts = _stories_done(conn, s, e)
    nxt_end = (e + timedelta(days=7)).isoformat()
    upcoming = [r for r in roadmap if r["status"] != "done" and r.get("target_date") and e.isoformat() < r["target_date"] <= nxt_end]
    highlights = _log(conn, s, e, floor, ("win", "progress"))
    issues = _log(conn, s, e, floor, ("blocker", "risk"))
    decided = _log(conn, s, e, floor, ("decision",))
    asks = _log(conn, s, e, floor, ("ask",))
    nexts = _log(conn, s, e, floor, ("next",))
    metrics = models.metrics.visible_all(models.metrics.fetch_all(conn), viewer)

    context = [info["label"]]
    if info["sprint"]:
        context.append(info["sprint"]["label"])
    if audience == "my manager" and info["role_week"]:
        context.append(f"week {info['role_week']} in the role")
    md = [f"**Overall: {overall}** [Placeholder: one sentence on where things stand. Suggested reason: {why}.]", "", " · ".join(context), ""]
    if info["sprint"]:
        sp = models.sprints.fetch(conn, info["sprint"]["id"])
        prog = _sprint_progress(conn, sp)
        md += ["## Sprint", f"Sprint {sp['number']}" + (f": {sp['goal']}" if sp.get("goal") else ""),
               f"- {prog['done_points']} of {prog['committed']} points done so far ({prog['done_stories']} of {prog['stories']} stories)"
               + (f", ending {weeks.fmt(date.fromisoformat(sp['end_date']))}" if sp.get("end_date") else ""), ""]
    if audience == "my manager":
        mine = models.mandates.fetch_all(conn, "mine = 1")
        if mine:
            outs = models.mandate_items.visible_all(models.mandate_items.fetch_all(conn, "mandate_id = ? AND kind = 'outcome' AND status != 'dropped'", (mine[0]["id"],)), viewer)
            if outs:
                md += ["## Progress on my mandate"] + [f"- {o['text']}: {o['status']}" for o in outs] + [""]
    md += ["## Highlights"] + ([_bullet(h, audience == "my manager") for h in highlights] or ["- [Placeholder: add wins and progress to the work log as they happen]"])
    delivered = [f"- {r['title']}" + (f" ({', '.join(r['jira_keys'])})" if r.get("jira_keys") else "") for r in shipped]
    if n_stories:
        delivered.append(f"- {n_stories} {'story' if n_stories == 1 else 'stories'} finished ({pts} points)")
    md += ["", "## Delivered"] + (delivered or ["- Nothing marked finished this week."])
    md += ["", "## Blockers and risks"] + [_bullet(i) for i in issues]
    md += [_table(["Risk", "Level", "Owner", "Next step", "Due"], [(r["title"], r["level"], r.get("owner_name"), r.get("next_step"), r.get("due")) for r in risks])]
    from .changes import changes_between, report_lines

    moved = conn.execute(
        "SELECT DISTINCT record_id FROM change_log WHERE entity = 'team_change' AND field = 'status' AND date(datetime(at, 'localtime')) BETWEEN ? AND ?",
        (s.isoformat(), e.isoformat())).fetchall()
    team_moves = models.team_changes.visible_all([c for c in (models.team_changes.fetch(conn, int(r["record_id"])) for r in moved) if c], viewer)
    team_moves = [c for c in team_moves if c.get("title")]  # only shown where the audience may see them
    if team_moves:
        md += ["", "## Changes I'm bringing to the team"] + [f"- {c['title']}: {c['status']}" + (f". {c['outcome']}" if c.get("outcome") and c["status"] in ("adopted", "dropped") else "") for c in team_moves]

    scope = changes_between(conn, s.isoformat(), e.isoformat(), floor)
    if scope:
        md += ["", "## Scope changes"] + report_lines(scope)
    md += ["", "## Decisions"] + [_bullet(d) for d in decided] + [_table(["Decision needed", "From", "Needed by"], [(d["decision"], d.get("from_name"), d.get("needed_by")) for d in decisions])]
    if asks:
        md += ["", "## Asks"] + [_bullet(a) for a in asks]
    nxt = [_bullet(n) for n in nexts] + [f"- {r['title']} (due {r['target_date']})" for r in upcoming]
    md += ["", "## Next week"] + (nxt or ["- [Placeholder item]"])
    if metrics:
        from .releases import metric_direction

        def line(m):
            d = metric_direction(conn, m)
            trend = {"improving": ", improving", "worsening": ", getting worse", "flat": ", holding steady"}.get(d, "")
            return (f"- {m['name']}: {m['latest'] if m.get('latest') is not None else 'no reading yet'}{(' ' + m['unit']) if m.get('unit') else ''}"
                    + (f" (target {m['target']:g})" if m.get("target") is not None else "") + trend)
        md += ["", "## Metrics"] + [line(m) for m in metrics]
    title = f"Weekly report: {info['label'].replace('Week of ', 'week of ')}"
    return {"kind": "weekly", "audience": audience, "week": info, "period_start": info["start"], "period_end": info["end"],
            "sprint_id": info["sprint"]["id"] if info["sprint"] else None, "overall": overall, "reason": why, "title": title,
            "counts": {"scope_changes": len(scope), "highlights": len(highlights), "issues": len(issues), "stories": n_stories, "points": pts, "shipped": len(shipped)},
            "markdown": "\n".join(md)}


def build_sprint(conn, sprint_id: int, audience: str = "leadership") -> dict:
    if audience not in AUDIENCE_FLOOR:
        raise HTTPException(400, "Audience is leadership or my manager.")
    sprint = models.sprints.fetch(conn, sprint_id)
    if not sprint or not sprint.get("start_date"):
        raise HTTPException(404 if not sprint else 400, "No such sprint." if not sprint else "Give the sprint a start date first.")
    floor = AUDIENCE_FLOOR[audience]
    parts = weeks.sprint_weeks(sprint)
    s, e = parts[0][0], parts[-1][1]
    prog = _sprint_progress(conn, sprint)
    roadmap = _roadmap(conn, floor)
    md = [f"Sprint {sprint['number']}: {weeks.fmt(s)} to {weeks.fmt(e)}, {e.year}", ""]
    md += ["## Goal", sprint.get("goal") or "[Placeholder sprint goal]", "", "**Did we meet it?** [Placeholder: yes, partly or no, and why]", ""]
    md += ["## Results",
           f"- {prog['done_points']} of {prog['committed']} committed points done ({prog['done_stories']} of {prog['stories']} stories)"]
    if prog["committed"]:
        md[-1] += f", {round(100 * prog['done_points'] / prog['committed'])}%"
    carried = conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(points), 0) AS pts FROM backlog_items WHERE sprint_id = ? AND status NOT IN ('done', 'removed')", (sprint_id,)).fetchone()
    carried_next = conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(points), 0) AS pts FROM backlog_items WHERE carried_from_id = ?", (sprint_id,)).fetchone()
    left = carried_next if carried_next["n"] else carried
    if left["n"]:
        md.append(f"- {left['n']} {'story' if left['n'] == 1 else 'stories'} ({left['pts']} points) not finished" + (", carried into the next sprint" if carried_next["n"] else ""))
    from .changes import report_lines

    crs = models.change_requests.visible_all(models.change_requests.fetch_all(conn, "sprint_id = ?", (sprint_id,)), Viewer(floor=floor, source="report"))
    accepted = [c for c in crs if c.get("decision") in ("accepted with a swap", "accepted without a swap")]
    p_in, p_out = sum(c.get("points") or 0 for c in accepted), sum(c.get("points_out") or 0 for c in accepted)
    if crs:
        md.append(f"- Scope changed by {len(crs)} request{'s' if len(crs) != 1 else ''} during the sprint: {p_in} points added, {p_out} taken out, net {p_in - p_out:+d}")
    history = conn.execute(
        "SELECT s.number, p.completed_points FROM sprints s JOIN sprint_plans p ON p.sprint_id = s.id WHERE s.team_id IS ? AND p.completed_points IS NOT NULL "
        "AND s.number <= ? ORDER BY s.number DESC LIMIT 5", (sprint.get("team_id"), sprint["number"])).fetchall()
    if len(history) > 1:
        md.append("- Velocity, recent sprints: " + ", ".join(f"Sprint {h['number']}: {h['completed_points']}" for h in reversed(history)))
    week_rows = []
    for n, (ws, we) in enumerate(parts, 1):
        stories, pts = _stories_done(conn, ws, we, sprint_id)
        done_ids = set(_finished(conn, "roadmap_item", ws, we))
        shipped = [r for r in roadmap if str(r["id"]) in done_ids and r["status"] == "done"]
        highlights = _log(conn, ws, we, floor, ("win", "progress", "decision"))
        issues = _log(conn, ws, we, floor, ("blocker", "risk"))
        week_rows.append((n, ws, we, stories, pts))
        md += ["", f"## Week {n} ({weeks.fmt(ws)} to {weeks.fmt(we)})", f"- {stories} {'story' if stories == 1 else 'stories'} finished ({pts} points)"]
        md += [f"- Delivered: {r['title']}" for r in shipped]
        md += [_bullet(h, audience == "my manager") for h in highlights]
        md += [_bullet(i).replace("- ", "- Blocker or risk: ", 1) for i in issues]
    if crs:
        md += ["", "## Scope changes during the sprint"] + report_lines(crs)
    retro = conn.execute("SELECT COUNT(*) FROM retro_commitments WHERE sprint_id = ?", (sprint_id,)).fetchone()[0]
    md += ["", "## Retrospective", f"- {retro} improvement{'s' if retro != 1 else ''} agreed for next sprint" if retro else "- [Placeholder: what the team agreed to change]"]
    md += ["", "## Next sprint", "- [Placeholder: goal and focus]"]
    return {"kind": "sprint", "audience": audience, "sprint": {"id": sprint["id"], "number": sprint["number"], "goal": sprint.get("goal")},
            "period_start": s.isoformat(), "period_end": e.isoformat(), "sprint_id": sprint_id, "progress": prog,
            "scope": {"requests": len(crs), "accepted": len(accepted), "points_in": p_in, "points_out": p_out},
            "weeks": [{"week": n, "start": a.isoformat(), "end": b.isoformat(), "stories": st, "points": p} for n, a, b, st, p in week_rows],
            "title": f"Sprint {sprint['number']} report", "markdown": "\n".join(md)}


@router.get("/api/reports/weekly")
def weekly(week: str | None = None, audience: str = "leadership", viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor == Level.EXPORTABLE:
        audience = "leadership"
    return build_weekly(conn, _parse(week, "week"), audience)


@router.get("/api/reports/sprint")
def sprint_report(sprint_id: int | None = None, audience: str = "leadership", viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor == Level.EXPORTABLE:
        audience = "leadership"
    if sprint_id is None:
        from .reporting import current_sprint

        cur = current_sprint(conn)
        if not cur:
            raise HTTPException(404, "No sprints yet.")
        sprint_id = cur["id"]
    return build_sprint(conn, sprint_id, audience)


@router.post("/api/reports/exported")
def exported(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Log that a report's text was copied out, as every export is."""
    require_write(viewer)
    title, md = body.get("title"), body.get("markdown")
    if not title or not md:
        raise HTTPException(400, "A title and the report text are needed.")
    log_export(conn, f"report:{body.get('kind') or 'weekly'}", title, [{"markdown": md}], viewer.source)
    return {"logged": True}


def reports_due(conn) -> dict:
    """For Today: last week's report if it hasn't been saved, a finished sprint without a report, and today's log count."""
    t = today()
    start_day = weeks.week_start_day(conn)
    this_start, _ = weeks.week_bounds(t, start_day)
    out = {"weekly": None, "sprint": None, "logged_today": conn.execute("SELECT COUNT(*) FROM work_log WHERE date = ?", (t.isoformat(),)).fetchone()[0]}
    offset, report_offset = (t.weekday() - start_day) % 7, (weeks.report_day(conn) - start_day) % 7
    due_week = this_start if offset >= report_offset else this_start - timedelta(days=7)
    has_activity = conn.execute("SELECT 1 FROM change_log WHERE date(datetime(at, 'localtime')) >= ? LIMIT 1", (due_week.isoformat(),)).fetchone()
    if has_activity and not conn.execute("SELECT 1 FROM reports WHERE kind = 'weekly' AND period_start = ?", (due_week.isoformat(),)).fetchone():
        out["weekly"] = weeks.week_info(conn, due_week)
    team = my_team_id(conn)
    ended = models.sprints.fetch_all(conn, "team_id IS ? AND end_date < ? AND end_date >= ?", (team, t.isoformat(), (t - timedelta(days=7)).isoformat()))
    for sp in ended:
        if not conn.execute("SELECT 1 FROM reports WHERE kind = 'sprint' AND sprint_id = ?", (sp["id"],)).fetchone():
            out["sprint"] = {"id": sp["id"], "number": sp["number"], "end_date": sp["end_date"]}
            break
    return out
