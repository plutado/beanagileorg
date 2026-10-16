"""Technical debt: a classified register, a value-versus-effort view, a capacity policy, decisions and a leadership summary.

Scoring is deliberately simple so it can be explained in a meeting: value = impact + risk (each 1 to 5), effort is a
T-shirt size, and the quadrant comes from comparing the two. It is a starting point for a conversation, not a verdict.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
POLICY_KEY = "debt.policy"
EFFORT_WEIGHT = {"S": 1, "M": 2, "L": 3, "XL": 5}
OPEN = ("identified", "accepted", "planned", "in progress")
CATEGORY_HELP = {
    "maintainability": "Code that's hard to understand or change safely; fixing it makes every later change cheaper.",
    "stability": "Fragile areas that break, need manual fixes or cause incidents; fixing it makes the site steadier.",
    "performance": "Slow pages, jobs or queries; fixing it makes things faster for customers or the team.",
    "cleanup": "Old code, configuration, fields or integrations that no longer do anything; removing it cuts clutter and risk.",
    "revenue and conversion": "Debt that directly costs sales, sign-ups or conversions; fixing it shows up in business numbers.",
    "observability": "Missing logging, monitoring, alerts or useful error messages; fixing it means problems are seen sooner.",
    "security": "Outdated dependencies, weak access controls or exposed data; fixing it lowers the chance of a breach.",
    "delivery speed": "Slow builds, manual deployments or missing tests that slow the team down; fixing it speeds up delivery.",
    "cost": "Waste in licences, infrastructure or support effort; fixing it saves money.",
}
DEFAULT_POLICY = {"allocation": None, "agreed_with": "", "agreed_on": None, "approach": ""}


def score(item: dict) -> dict:
    """value 2..10 from impact + risk; quadrant from value against effort."""
    if not item.get("impact") or not item.get("risk") or not item.get("effort"):
        return {"value": None, "score": None, "quadrant": "not scored"}
    value = item["impact"] + item["risk"]
    weight = EFFORT_WEIGHT[item["effort"]]
    high_value, low_effort = value >= 7, weight <= 2
    quadrant = {(True, True): "quick win", (True, False): "big bet", (False, True): "fill-in", (False, False): "money pit"}[(high_value, low_effort)]
    return {"value": value, "score": round(value / weight, 1), "quadrant": quadrant}


def _policy(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (POLICY_KEY,)).fetchone()
    return {**DEFAULT_POLICY, **(json.loads(row["value"]) if row else {})}


@router.get("/api/debt/policy")
def get_policy(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return _policy(conn)


@router.put("/api/debt/policy")
def put_policy(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    pol = {**_policy(conn), **{k: body[k] for k in DEFAULT_POLICY if k in body}}
    if pol["allocation"] is not None:
        try:
            pol["allocation"] = int(pol["allocation"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "The allocation is a whole percentage, such as 20.") from exc
        if not 0 <= pol["allocation"] <= 100:
            raise HTTPException(400, "The allocation is a percentage from 0 to 100.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (POLICY_KEY, json.dumps(pol)))
    return pol


def _items(conn, viewer: Viewer) -> list[dict]:
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM systems")}
    out = []
    for d in models.tech_debt.visible_all(models.tech_debt.fetch_all(conn), viewer):
        out.append({**d, **score(d), "systems": [names[i] for i in d.get("system_ids", []) if i in names]})
    return out


def _capacity(conn, items: list[dict], policy: dict) -> dict | None:
    today = date.today().isoformat()
    s = conn.execute("SELECT id, number, capacity FROM sprints WHERE start_date <= ? AND (end_date IS NULL OR end_date >= ?) ORDER BY start_date DESC LIMIT 1", (today, today)).fetchone()
    if not s:
        return None
    planned = sum(i.get("points") or 0 for i in items if i.get("sprint_id") == s["id"] and i["status"] in OPEN)
    target = round(s["capacity"] * policy["allocation"] / 100) if s["capacity"] and policy["allocation"] is not None else None
    return {"sprint_id": s["id"], "sprint_number": s["number"], "capacity": s["capacity"], "planned_points": planned, "target_points": target,
            "share": round(100 * planned / s["capacity"]) if s["capacity"] else None}


@router.get("/api/debt/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    items = _items(conn, viewer)
    open_items = [i for i in items if i["status"] in OPEN]
    policy = _policy(conn)
    soon = (date.today() + timedelta(days=30)).isoformat()
    today = date.today().isoformat()
    return {
        "items": items,
        "categories": [{"key": c, "help": CATEGORY_HELP[c], "open": sum(c in (i.get("categories") or []) for i in open_items),
                        "points": sum(i.get("points") or 0 for i in open_items if c in (i.get("categories") or []))} for c in models.DEBT_CATEGORIES],
        "quadrants": {q: sum(i["quadrant"] == q for i in open_items) for q in ("quick win", "big bet", "fill-in", "money pit", "not scored")},
        "policy": policy,
        "capacity": _capacity(conn, items, policy),
        "due": [{"id": i["id"], "title": i["title"], "why": f"revisit {i['revisit_on']}" if i.get("revisit_on") and i["revisit_on"] <= soon and i["status"] == "accepted"
                 else f"needed by {i['trigger_date']}", "overdue": (i.get("revisit_on") or i.get("trigger_date") or "9999") < today}
                for i in open_items if (i["status"] == "accepted" and i.get("revisit_on") and i["revisit_on"] <= soon) or (i.get("trigger_date") and i["trigger_date"] <= soon)],
    }


@router.get("/api/tech-debt/{debt_id}/decisions")
def decisions(debt_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return models.debt_decisions.visible_all(models.debt_decisions.fetch_all(conn, "debt_id = ?", (debt_id,)), viewer)


@router.post("/api/tech-debt/{debt_id}/decide", status_code=201)
def decide(debt_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record a decision and move the item to match: fix now or schedule plans it, accept parks it with a revisit date."""
    require_write(viewer)
    if not models.tech_debt.fetch(conn, debt_id):
        raise HTTPException(404, "No such debt item.")
    decision = body.get("decision")
    if decision not in models.DEBT_DECISIONS:
        raise HTTPException(400, f"The decision is one of: {', '.join(models.DEBT_DECISIONS)}.")
    if decision == "accept for now" and not body.get("revisit_on"):
        raise HTTPException(400, "Accepted debt needs a date to look at it again.")
    row = models.debt_decisions.create(conn, {"debt_id": debt_id, "date": body.get("date") or date.today().isoformat(), "decision": decision,
                                              "rationale": body.get("rationale"), "decided_by": body.get("decided_by"), "revisit_on": body.get("revisit_on")}, viewer.source)
    status = {"fix now": "planned", "schedule": "planned", "accept for now": "accepted", "won't fix": "won't fix"}[decision]
    changes = {"status": status, "revisit_on": body.get("revisit_on") if decision == "accept for now" else None}
    if body.get("sprint_id"):
        changes["sprint_id"] = body["sprint_id"]
    models.tech_debt.update(conn, debt_id, changes, viewer.source)
    return row


def build_summary(conn) -> dict:
    exporter = Viewer(floor=Level.EXPORTABLE, source="debt", scopes=frozenset({"export:read"}))
    items = _items(conn, exporter)
    open_items = [i for i in items if i["status"] in OPEN]
    policy = _policy(conn)
    cap = _capacity(conn, items, policy)
    lines = ["# Technical debt summary", "", f"{len(open_items)} open items, {sum(i.get('points') or 0 for i in open_items)} points estimated.", ""]
    if policy["allocation"] is not None:
        agreed = f", agreed with {policy['agreed_with']}" + (f" on {policy['agreed_on']}" if policy["agreed_on"] else "") if policy["agreed_with"] else ""
        lines += [f"**Capacity policy:** {policy['allocation']}% of each sprint goes to technical debt{agreed}."]
        if cap and cap["capacity"]:
            lines += [f"Sprint {cap['sprint_number']}: {cap['planned_points']} of {cap['capacity']} points planned on debt ({cap['share']}%), against a target of {cap['target_points']}."]
        lines += [""]
    lines += ["## By category", "", "| Category | Open items | Points |", "| --- | --- | --- |"]
    for c in models.DEBT_CATEGORIES:
        n = [i for i in open_items if c in (i.get("categories") or [])]
        if n:
            lines.append(f"| {c[0].upper() + c[1:]} | {len(n)} | {sum(i.get('points') or 0 for i in n)} |")
    ranked = sorted([i for i in open_items if i["score"] is not None and i["status"] != "accepted"], key=lambda i: -i["score"])[:10]
    if ranked:
        lines += ["", "## Highest value for the effort", "", "| Item | Why it matters | Categories | Value | Effort | Needed by |", "| --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {i['title']}{' (' + i['ticket_key'] + ')' if i.get('ticket_key') else ''} | {i.get('cost_of_delay') or ''} | {', '.join(i.get('categories') or [])} | {i['value']}/10 | {i['effort']} | {i.get('trigger_date') or ''} |" for i in ranked]
    accepted = [i for i in open_items if i["status"] == "accepted"]
    if accepted:
        lines += ["", "## Accepted for now", "", "Debt we've chosen to live with, and when we'll look again.", ""]
        lines += [f"- {i['title']} (revisit {i.get('revisit_on') or 'not set'})" for i in accepted]
    done = [i for i in items if i["status"] == "done"]
    if done:
        lines += ["", "## Paid down", ""] + [f"- {i['title']}" for i in done[:10]]
    return {"title": "Technical debt summary", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/debt/summary")
def summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_summary(conn)


@router.post("/api/debt/summary/export")
def export_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_summary(conn)
    log_export(conn, "debt:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


def debt_due(conn) -> list[dict]:
    """For Today: accepted debt due a second look, and debt with a deadline, in the next 14 days."""
    soon = (date.today() + timedelta(days=14)).isoformat()
    rows = conn.execute(
        "SELECT id, title, status, revisit_on, trigger_date FROM tech_debt WHERE status IN ('identified', 'accepted', 'planned', 'in progress') "
        "AND ((status = 'accepted' AND revisit_on <= ?) OR trigger_date <= ?)", (soon, soon)).fetchall()
    return [{"id": r["id"], "title": r["title"], "when": r["revisit_on"] if r["status"] == "accepted" and r["revisit_on"] and r["revisit_on"] <= soon else r["trigger_date"],
             "kind": "revisit" if r["status"] == "accepted" and r["revisit_on"] and r["revisit_on"] <= soon else "deadline"} for r in rows]
