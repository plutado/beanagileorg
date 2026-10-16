"""Sprint notebook, RACI matrix and the weekly status draft.

The status draft is always built at the exportable privacy level, whoever asks for it, so it can go
straight into a message without carrying anything private.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer, require_full
from beanagile.core.changelog import record_changes
from beanagile.core.export import log_export
from beanagile.core.privacy import Level, Viewer

from . import models
from .routes import START_DATE_KEY, create_action, require_write, today

router = APIRouter()
RACI_ROLES_KEY = "toolkit.raci_roles"
DEFAULT_ROLES = ["Director", "Engineering manager", "Product", "Architect", "Engineers", "QA", "Design", "Stakeholders"]
EXPORT = Viewer(floor=Level.EXPORTABLE, source="status-draft")


def _setting(conn, key: str):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


# ---- sprint notebook ----


def current_sprint(conn) -> dict | None:
    t = today().isoformat()
    found = models.sprints.fetch_all(conn, "start_date <= ? AND (end_date IS NULL OR end_date >= ?)", (t, t))
    if found:
        return found[0]
    latest = models.sprints.fetch_all(conn)
    return latest[0] if latest else None


@router.get("/api/sprints/current")
def get_current_sprint(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    sprint = current_sprint(conn)
    return models.sprints.visible(sprint, viewer) if sprint else None


@router.post("/api/sprints/next", status_code=201)
def next_sprint(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    latest = models.sprints.fetch_all(conn)
    prev = latest[0] if latest else None
    start = date.fromisoformat(prev["end_date"]) + timedelta(days=1) if prev and prev["end_date"] else today()
    if body.get("start_date"):
        try:
            start = date.fromisoformat(body["start_date"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "start_date must be a date like 2026-11-02.") from exc
    data = {
        "number": (prev["number"] + 1) if prev else 1,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=13)).isoformat(),
        "kind": "development",
        "pi_id": prev["pi_id"] if prev else None,
        **body,
    }
    return models.sprints.create(conn, data, viewer.source)


@router.get("/api/sprints/{sprint_id}/notebook")
def notebook(sprint_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    sprint = models.sprints.fetch(conn, sprint_id)
    if sprint is None:
        raise HTTPException(404, "No sprint with that id.")
    earlier = models.sprints.fetch_all(conn, "number < ?", (sprint["number"],))
    previous = earlier[0] if earlier else None
    carry = []
    if previous:
        carry = models.action_items.fetch_all(conn, "sprint_id = ? AND status != 'done'", (previous["id"],))
    pi = models.program_increments.fetch(conn, sprint["pi_id"]) if sprint["pi_id"] else None
    return {
        "sprint": models.sprints.visible(sprint, viewer),
        "pi": models.program_increments.visible(pi, viewer) if pi else None,
        "notes": models.ceremony_notes.visible_all(models.ceremony_notes.fetch_all(conn, "sprint_id = ?", (sprint_id,)), viewer),
        "items": models.action_items.visible_all(models.action_items.fetch_all(conn, "sprint_id = ?", (sprint_id,)), viewer),
        "carry_over": models.action_items.visible_all(carry, viewer),
        "previous_id": previous["id"] if previous else None,
    }


@router.post("/api/ceremony-notes/{note_id}/follow-up", status_code=201)
def note_follow_up(note_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A follow-up from a ceremony becomes a dev-sync item tied to the sprint, so the next planning note shows it if open."""
    require_write(viewer)
    note = models.ceremony_notes.fetch(conn, note_id)
    if note is None:
        raise HTTPException(404, "No ceremony note with that id.")
    data = {
        **body,
        "origin": "retro" if note["type"] == "retro" else "dev sync",
        "sprint_id": note["sprint_id"],
        "note_id": note_id,
    }
    data.setdefault("concern", (note["follow_ups"] or "").strip().splitlines()[0] if note["follow_ups"] else f"Follow-up from {note['type']}")
    return create_action(data, viewer, conn)


# ---- RACI ----


def raci_roles(conn) -> list[str]:
    raw = _setting(conn, RACI_ROLES_KEY)
    return json.loads(raw) if raw else list(DEFAULT_ROLES)


@router.get("/api/raci")
def raci(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    cells = {}
    for row in conn.execute("SELECT decision_id, role, letter FROM raci_assignments"):
        cells.setdefault(row["decision_id"], {})[row["role"]] = row["letter"]
    decisions = models.raci_decisions.visible_all(models.raci_decisions.fetch_all(conn), viewer)
    for d in decisions:
        d["cells"] = cells.get(d["id"], {})
    return {"roles": raci_roles(conn), "decisions": decisions}


@router.put("/api/raci/roles")
def put_roles(body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    roles = [r.strip() for r in body.get("roles", []) if isinstance(r, str) and r.strip()]
    if not roles:
        raise HTTPException(400, "List at least one role.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (RACI_ROLES_KEY, json.dumps(roles)))
    return {"roles": roles}


@router.put("/api/raci/{decision_id}/cell")
def put_cell(decision_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if models.raci_decisions.fetch(conn, decision_id) is None:
        raise HTTPException(404, "No RACI decision with that id.")
    role, letter = body.get("role"), body.get("letter") or None
    if role not in raci_roles(conn):
        raise HTTPException(400, "Unknown role.")
    if letter is not None and letter not in models.RACI_LETTERS:
        raise HTTPException(400, "Letter must be R, A, C or I.")
    old = conn.execute("SELECT letter FROM raci_assignments WHERE decision_id = ? AND role = ?", (decision_id, role)).fetchone()
    if letter is None:
        conn.execute("DELETE FROM raci_assignments WHERE decision_id = ? AND role = ?", (decision_id, role))
    else:
        conn.execute(
            "INSERT INTO raci_assignments (decision_id, role, letter) VALUES (?, ?, ?) "
            "ON CONFLICT (decision_id, role) DO UPDATE SET letter = excluded.letter",
            (decision_id, role, letter),
        )
    record_changes(conn, "raci_decision", decision_id, {role: old["letter"] if old else None}, {role: letter}, viewer.source)
    accountable = conn.execute(
        "SELECT COUNT(*) FROM raci_assignments WHERE decision_id = ? AND letter = 'A'", (decision_id,)
    ).fetchone()[0]
    return {"role": role, "letter": letter, "accountable_count": accountable}


@router.post("/api/delivery/starter", status_code=201)
def delivery_starter(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    from .starter import load_starter

    loaded = load_starter(conn, viewer.source)
    if not loaded:
        raise HTTPException(409, "The roadmap, RACI and metrics already have content.")
    return loaded


# ---- weekly status draft ----


def _day_to_date(start: str | None, target_day: int | None) -> str | None:
    if not start or target_day is None:
        return None
    return (date.fromisoformat(start) + timedelta(days=target_day - 1)).isoformat()


def _changed_to(conn, entity: str, field: str, value: str, since: str) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT record_id FROM change_log WHERE entity = ? AND field = ? AND new_value = ? AND at >= ?",
        (entity, field, value, since),
    ).fetchall()
    return [r["record_id"] for r in rows]


def build_status(conn) -> dict:
    t = today()
    week_of = t - timedelta(days=t.weekday())
    start = _setting(conn, START_DATE_KEY)
    roadmap = models.roadmap_items.visible_all(models.roadmap_items.fetch_all(conn), EXPORT)
    for r in roadmap:
        r["target_date"] = _day_to_date(start, r.get("target_day"))
    horizon = (t + timedelta(days=14)).isoformat()
    milestones = [
        r for r in roadmap
        if r["status"] != "done" and (r["kind"] == "milestone" or r["status"] == "at risk" or (r["target_date"] and r["target_date"] <= horizon))
    ]
    risks = models.risks.visible_all(models.risks.fetch_all(conn, "status != 'closed'"), EXPORT)
    decisions = models.decisions_needed.visible_all(models.decisions_needed.fetch_all(conn, "status = 'open'"), EXPORT)
    since = (t - timedelta(days=7)).isoformat()
    done_ids = set(_changed_to(conn, "roadmap_item", "status", "done", since))
    shipped = [r for r in roadmap if str(r["id"]) in done_ids and r["status"] == "done"]
    week_end = (t + timedelta(days=7)).isoformat()
    next_week = [r for r in roadmap if r["status"] != "done" and r["target_date"] and t.isoformat() <= r["target_date"] <= week_end]
    metrics = models.metrics.visible_all(models.metrics.fetch_all(conn), EXPORT)
    goals = models.learning_goals.visible_all(models.learning_goals.fetch_all(conn), EXPORT)
    sprint = current_sprint(conn)

    t_iso = t.isoformat()
    late_risk = any(r["level"] == "high" for r in risks if r["status"] == "open")
    late_milestone = any(r["status"] == "at risk" and r["target_date"] and r["target_date"] < t_iso for r in roadmap)
    if late_risk or late_milestone:
        overall, why = "Red", "a high risk is open" if late_risk else "an at-risk milestone has passed its date"
    elif any(r["status"] == "at risk" for r in roadmap) or any(d.get("needed_by") and d["needed_by"] < t_iso for d in decisions):
        overall, why = "Yellow", "something is at risk or a decision is overdue"
    else:
        overall, why = "Green", "on track"

    def table(headers, rows):
        if not rows:
            return "_None this week._"
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines += ["| " + " | ".join(str(c if c not in (None, "") else "") for c in row) + " |" for row in rows]
        return "\n".join(lines)

    rag = {"done": "Green", "in progress": "Green", "not started": "Green", "at risk": "Yellow"}
    md = [
        f"**Overall: {overall}** [Placeholder: one sentence on where things stand. Suggested reason: {why}.]",
        "",
    ]
    if sprint:
        md += [f"Sprint {sprint['number']} ({sprint['start_date'] or '?'} to {sprint['end_date'] or '?'}): {sprint['goal'] or '[Placeholder sprint goal]'}", ""]
    md += ["## Milestones", table(["Milestone", "Target", "Status"], [(r["title"], r["target_date"] or (f"Day {r['target_day']}" if r.get("target_day") else ""), rag[r["status"]]) for r in milestones])]
    md += ["", "## Risks and issues", table(["Risk or issue", "Level", "Owner", "Next step", "Due"], [(r["title"], r["level"], r.get("owner_name"), r.get("next_step"), r.get("due")) for r in risks])]
    md += ["", "## Decisions needed", table(["Decision", "From whom", "Needed by"], [(d["decision"], d.get("from_name"), d.get("needed_by")) for d in decisions])]
    md += ["", "## Shipped this week"] + ([f"- {r['title']}" for r in shipped] or ["- [Placeholder item]"])
    md += ["", "## Next week"] + ([f"- {r['title']}" for r in next_week] or ["- [Placeholder item]"])
    if metrics:
        md += ["", "## Metrics"] + [
            f"- {m['name']}: {m['latest'] if m['latest'] is not None else 'no reading yet'}{(' ' + m['unit']) if m.get('unit') else ''}"
            + (f" (target {m['target']:g})" if m.get("target") is not None else "")
            for m in metrics
        ]
    if goals:
        md += ["", "## My development"] + [
            f"- {g['goal']}: {g['status']}" + (f", {round(g['minutes'] / 60, 1):g} h logged" if g.get("minutes") else "") for g in goals
        ]
    md += ["", "## Asks and answers", "- [Placeholder: help needed, or answers to last week's questions]"]
    return {
        "week_of": week_of.isoformat(),
        "overall": overall,
        "reason": why,
        "facts": {
            "sprint": models.sprints.visible(sprint, EXPORT) if sprint else None,
            "milestones": milestones, "risks": risks, "decisions": decisions, "shipped": shipped,
            "next_week": next_week, "metrics": metrics, "learning_goals": goals,
        },
        "title": f"Weekly status: week of {week_of.isoformat()}",
        "markdown": "\n".join(md),
    }


@router.get("/api/status/draft")
def status_draft(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_status(conn)


@router.post("/api/status/export")
def status_export(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    draft = build_status(conn)
    log_export(conn, "status:markdown", draft["title"], [{"markdown": draft["markdown"]}], viewer.source)
    return draft
