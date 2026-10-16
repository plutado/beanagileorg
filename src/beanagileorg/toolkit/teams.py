"""Teams and the Scrum of Scrums: your team and the teams around it, and the cross-team log above them.

Your own team's work is tracked in full elsewhere in the toolkit (every delivery record carries a team). Other teams
are tracked lightly: who they are, their current sprint and goal, a status, and what's open between you.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
OPEN = ("open", "in progress", "waiting")


def _today() -> str:
    return date.today().isoformat()


def _involves(item: dict, team_id: int) -> bool:
    return team_id in (item.get("team_ids") or []) or team_id in (item.get("owner_team_id"), item.get("raised_by_team_id"))


def _names(conn, ids: list[int]) -> list[dict]:
    if not ids:
        return []
    rows = conn.execute(f"SELECT id, name, role FROM people WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall()
    return [dict(r) for r in rows]


@router.patch("/api/teams/{team_id}")
def update_team(team_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A new status or status note is stamped with today's date, so it's clear how fresh it is."""
    require_write(viewer)
    current = models.teams.fetch(conn, team_id)
    if current is None:
        raise HTTPException(404, "No such team.")
    if any(k in body and body[k] != current[k] for k in ("status", "status_note")) and "status_date" not in body:
        body = {**body, "status_date": _today()}
    if body.get("kind") == "other" and current["kind"] == "mine" and conn.execute("SELECT COUNT(*) FROM teams WHERE kind = 'mine'").fetchone()[0] == 1:
        raise HTTPException(400, "Keep at least one team as yours.")
    return models.teams.visible(models.teams.update(conn, team_id, body, viewer.source), viewer)


@router.delete("/api/teams/{team_id}", status_code=204)
def delete_team(team_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    t = models.teams.fetch(conn, team_id)
    if t is None:
        raise HTTPException(404, "No such team.")
    if t["kind"] == "mine" and conn.execute("SELECT COUNT(*) FROM teams WHERE kind = 'mine'").fetchone()[0] == 1:
        raise HTTPException(400, "This is your only team. Rename it instead of deleting it.")
    models.teams.delete(conn, team_id, viewer.source)


def _counts(conn, table: str, team_id: int, where: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE team_id = ? AND {where}", (team_id,)).fetchone()[0]


@router.get("/api/teams/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    items = models.sos_items.fetch_all(conn)
    today = _today()
    out = []
    for t in models.teams.visible_all(models.teams.fetch_all(conn), viewer):
        mine = [i for i in items if _involves(i, t["id"]) and i["status"] in OPEN]
        sprint = conn.execute("SELECT number, goal, end_date FROM sprints WHERE team_id = ? AND start_date <= ? AND (end_date IS NULL OR end_date >= ?) ORDER BY start_date DESC LIMIT 1",
                              (t["id"], today, today)).fetchone()
        out.append({**t, "members": _names(conn, t["member_ids"]),
                    "open_sos": len(mine), "overdue_sos": sum(1 for i in mine if i["due"] and i["due"] < today),
                    "dependencies": sum(1 for i in mine if i["kind"] == "dependency"),
                    "open_actions": _counts(conn, "action_items", t["id"], "status != 'done'"),
                    "open_risks": _counts(conn, "risks", t["id"], "status != 'closed'"),
                    "sprint": dict(sprint) if sprint else None})
    return out


@router.get("/api/teams/{team_id}/detail")
def detail(team_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    t = models.teams.fetch(conn, team_id)
    if t is None:
        raise HTTPException(404, "No such team.")
    items = [i for i in models.sos_items.visible_all(models.sos_items.fetch_all(conn), viewer) if _involves(i, team_id)]
    systems = conn.execute(f"SELECT id, name FROM systems WHERE id IN ({','.join('?' * len(t['system_ids'])) or 'NULL'})", t["system_ids"]).fetchall() if t["system_ids"] else []
    return {
        "team": models.teams.visible(t, viewer),
        "members": _names(conn, t["member_ids"]),
        "systems": [dict(s) for s in systems],
        "sos_open": [i for i in items if i["status"] in OPEN],
        "sos_done": [i for i in items if i["status"] == "done"][:10],
        "risks": models.risks.visible_all(models.risks.fetch_all(conn, "team_id = ? AND status != 'closed'", (team_id,)), viewer),
        "actions": models.action_items.visible_all(models.action_items.fetch_all(conn, "team_id = ? AND status != 'done'", (team_id,)), viewer)[:15],
        "sprints": models.sprints.visible_all(models.sprints.fetch_all(conn, "team_id = ?", (team_id,)), viewer)[:6],
    }


@router.get("/api/sos/overview")
def sos_overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    today, week = _today(), (date.today() + timedelta(days=7)).isoformat()
    items = models.sos_items.visible_all(models.sos_items.fetch_all(conn), viewer)
    open_items = [i for i in items if i["status"] in OPEN]
    teams = {t["id"]: t["name"] for t in models.teams.fetch_all(conn)}
    return {
        "items": items,
        "teams": [{"id": k, "name": v} for k, v in teams.items()],
        "counts": {k: sum(1 for i in open_items if i["kind"] == k) for k in models.SOS_KINDS},
        "overdue": [i["id"] for i in open_items if i["due"] and i["due"] < today],
        "due_soon": [i["id"] for i in open_items if i["due"] and today <= i["due"] <= week],
        "meetings": models.sos_meetings.visible_all(models.sos_meetings.fetch_all(conn), viewer)[:10],
    }


@router.post("/api/sos/meetings/start", status_code=201)
def start_meeting(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A meeting record for today, listing every open item and every team, ready for notes."""
    require_write(viewer)
    open_ids = [i["id"] for i in models.sos_items.fetch_all(conn) if i["status"] in OPEN]
    team_ids = [t["id"] for t in models.teams.fetch_all(conn)]
    return models.sos_meetings.create(conn, {"date": _today(), "item_ids": open_ids, "team_ids": team_ids}, viewer.source)


def build_summary(conn) -> dict:
    """For leadership: each team's status, what's open across teams, what's late, and what was settled recently."""
    viewer = Viewer(floor=Level.PRESENTABLE, source="sos", scopes=frozenset())
    today = _today()
    teams = models.teams.visible_all(models.teams.fetch_all(conn), viewer)
    names = {t["id"]: t["name"] for t in teams}
    items = models.sos_items.visible_all(models.sos_items.fetch_all(conn), viewer)
    open_items = [i for i in items if i["status"] in OPEN]
    lines = ["# Scrum of Scrums summary", "", f"As of {today}.", "", "## Teams", "", "| Team | Status | Sprint | Goal | Note |", "| --- | --- | --- | --- | --- |"]
    for t in teams:
        lines.append(f"| {t['name']} | {t.get('status') or 'not set'}{' (' + t['status_date'] + ')' if t.get('status_date') else ''} | {t.get('current_sprint') or ''} | {t.get('current_goal') or ''} | {t.get('status_note') or ''} |")
    late = [i for i in open_items if i["due"] and i["due"] < today]
    if late:
        lines += ["", "## Overdue", ""] + [f"- {i['question']} (owner: {i.get('owner_name') or names.get(i.get('owner_team_id')) or 'unassigned'}, due {i['due']})" for i in late]
    if open_items:
        lines += ["", "## Open across teams", "", "| Item | Kind | Teams | Owner | Outcome expected | Due |", "| --- | --- | --- | --- | --- | --- |"]
        for i in open_items:
            involved = ", ".join(names[x] for x in (i.get("team_ids") or []) if x in names)
            owner = i.get("owner_name") or names.get(i.get("owner_team_id")) or ""
            keys = f" ({', '.join(i['jira_keys'])})" if i.get("jira_keys") else ""
            lines.append(f"| {i['question']}{keys} | {i['kind']} | {involved} | {owner} | {i.get('outcome') or ''} | {i.get('due') or ''} |")
    recent = [i for i in items if i["status"] == "done"][:8]
    if recent:
        lines += ["", "## Settled recently", ""] + [f"- {i['question']}: {i.get('resolution') or 'done'}" for i in recent]
    return {"title": "Scrum of Scrums summary", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/sos/summary")
def summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_summary(conn)


@router.post("/api/sos/summary/export")
def export_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_summary(conn)
    log_export(conn, "sos:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


def sos_due(conn) -> list[dict]:
    """For Today: Scrum of Scrums items overdue or due in the next seven days."""
    week = (date.today() + timedelta(days=7)).isoformat()
    rows = models.sos_items.fetch_all(conn, "status != 'done' AND due IS NOT NULL AND due <= ?", (week,))
    return [{"id": r["id"], "question": r["question"], "due": r["due"], "overdue": r["due"] < _today(), "owner": r["owner_name"] or r["owner_team_name"]} for r in rows]
