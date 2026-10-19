"""Change requests: new work that arrives while a sprint is running.

Scrum's rule of thumb: once a sprint starts, nothing is added that puts the sprint goal at risk. New work
goes to the product backlog for the next sprint unless it truly can't wait. When it can't, the product owner
decides, with the team, what comes out to make room (a swap of about the same size), or whether the sprint
goal itself has changed. This module records each request, the assessment, the decision and who was told,
moves the stories in and out of the sprint when a decision is applied, and counts scope change per sprint.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .reporting import current_sprint, my_team_id
from .routes import require_write, today

router = APIRouter()
POLICY_KEY = "changes.policy"
FULL = Viewer(floor=Level.PRIVATE, source="changes")
UNDECIDED = ("received", "assessing")

STARTER_POLICY = """**How we handle requests during a sprint**

1. Anyone can raise a request, but it comes to the product owner, not straight to a developer.
2. By default, new work goes to the product backlog and is considered at the next sprint planning.
3. If it can't wait, we look at it within one working day: what it's worth, how big it is, and whether it puts the sprint goal at risk.
4. The product owner decides, with the team:
   - **Swap**: take out unstarted work of about the same size so the sprint stays achievable.
   - **Absorb**: only for small work that fits in the slack we planned for.
   - **Defer** to the backlog, with a date we'll look at it.
   - **Reject**, with the reason.
   - **Cancel the sprint**: only if the sprint goal no longer makes sense. We then plan a new sprint.
5. Production emergencies follow the escalation playbook and are logged here afterwards.
6. Whoever asked hears the decision and the reason the same day.
7. We look at how much scope changed at every retrospective.

[Placeholder: who can approve an emergency when the product owner is away]"""


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


@router.get("/api/change-requests/policy")
def get_policy(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"policy": _setting(conn, POLICY_KEY, ""), "starter": STARTER_POLICY}


@router.put("/api/change-requests/policy")
def put_policy(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    text = (body.get("policy") or "").strip()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (POLICY_KEY, text))
    return {"policy": text}


def sprint_impact(conn, sprint_id: int) -> dict:
    """Where the sprint stands, and the unfinished stories that could come out to make room."""
    from .sprint_planning import build_plan

    plan = build_plan(conn, sprint_id, FULL)
    s = plan["sprint"]
    items = [i for i in plan["pulled"] if i["status"] not in ("done", "removed")]
    done = sum(i.get("points") or 0 for i in plan["pulled"] if i["status"] == "done")
    in_sprint = sum(i.get("points") or 0 for i in plan["pulled"] if i["status"] != "removed")
    committed = (plan["plan"] or {}).get("committed_points")
    end = date.fromisoformat(s["end_date"]) if s.get("end_date") else None
    crs = models.change_requests.fetch_all(conn, "sprint_id = ?", (sprint_id,))
    accepted = [c for c in crs if c["decision"] in ("accepted with a swap", "accepted without a swap")]
    return {
        "sprint": {"id": s["id"], "number": s["number"], "goal": s.get("goal"), "start_date": s.get("start_date"), "end_date": s.get("end_date")},
        "capacity": plan["capacity"]["points"], "committed": committed, "in_sprint": in_sprint, "done": done, "remaining": in_sprint - done,
        "days_left": max((end - today()).days + 1, 0) if end else None,
        # Lowest priority first: the usual candidates to come out.
        "candidates": sorted([{"id": i["id"], "title": i["title"], "jira_key": i.get("jira_key"), "points": i.get("points"), "rank": i.get("rank"),
                               "owner_name": i.get("owner_name")} for i in items], key=lambda i: -(i["rank"] or 0)),
        "changes": {"requests": len(crs), "accepted": len(accepted),
                    "points_in": sum(c["points"] or 0 for c in accepted), "points_out": sum(c["points_out"] or 0 for c in accepted)},
    }


def churn(conn, team_id: int | None, limit: int = 8) -> list[dict]:
    """Scope change per sprint, oldest first: how many requests, what was decided, points in and out."""
    sprints = models.sprints.fetch_all(conn, "team_id IS ?", (team_id,))[:limit]
    out = []
    for s in reversed(sprints):
        crs = models.change_requests.fetch_all(conn, "sprint_id = ?", (s["id"],))
        accepted = [c for c in crs if c["decision"] in ("accepted with a swap", "accepted without a swap")]
        committed = conn.execute("SELECT committed_points FROM sprint_plans WHERE sprint_id = ?", (s["id"],)).fetchone()
        pin = sum(c["points"] or 0 for c in accepted)
        out.append({"sprint_id": s["id"], "number": s["number"], "requests": len(crs), "accepted": len(accepted),
                    "deferred": sum(1 for c in crs if c["decision"] == "deferred to the backlog"),
                    "rejected": sum(1 for c in crs if c["decision"] == "rejected"),
                    "points_in": pin, "points_out": sum(c["points_out"] or 0 for c in accepted),
                    "committed": committed["committed_points"] if committed else None,
                    "changed_pct": round(100 * pin / committed["committed_points"]) if committed and committed["committed_points"] else None})
    return out


@router.get("/api/change-requests/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    team = my_team_id(conn)
    sprint = current_sprint(conn)
    crs = models.change_requests.visible_all(models.change_requests.fetch_all(conn), viewer)
    t = today()
    running = sprint and sprint.get("start_date") and sprint["start_date"] <= t.isoformat() and (not sprint.get("end_date") or sprint["end_date"] >= t.isoformat())
    return {
        "sprint": sprint_impact(conn, sprint["id"]) if sprint else None, "running": bool(running),
        "open": [c for c in crs if c["status"] in UNDECIDED],
        "untold": [c for c in crs if c["status"] == "decided" and not c.get("communicated_on")],
        "recent": [c for c in crs if c["status"] in ("decided", "closed")][:10],
        "churn": churn(conn, team), "policy": _setting(conn, POLICY_KEY, ""),
    }


@router.get("/api/change-requests/{cr_id}/assess")
def assess(cr_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    cr = models.change_requests.fetch(conn, cr_id)
    if not cr:
        raise HTTPException(404, "No such change request.")
    sprint_id = cr["sprint_id"] or (current_sprint(conn) or {}).get("id")
    return {"request": models.change_requests.visible(cr, viewer), "impact": sprint_impact(conn, sprint_id) if sprint_id and viewer.floor == Level.PRIVATE else None}


@router.post("/api/change-requests/{cr_id}/decide")
def decide(cr_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record the decision and apply it: swapped-out stories go back to the backlog, accepted work joins the sprint, deferred work joins the backlog."""
    require_write(viewer)
    cr = models.change_requests.fetch(conn, cr_id)
    if not cr:
        raise HTTPException(404, "No such change request.")
    if cr["status"] in ("decided", "closed"):
        raise HTTPException(409, "This request has already been decided. Edit it instead.")
    decision = body.get("decision")
    if decision not in models.CR_DECISIONS:
        raise HTTPException(400, "Choose a decision.")
    reason = (body.get("reason") or "").strip()
    if decision in ("rejected", "deferred to the backlog", "sprint cancelled") and not reason:
        raise HTTPException(400, "Say why, so the requester hears a reason.")
    points = body.get("points", cr["points"])
    sprint_id = cr["sprint_id"] or (current_sprint(conn) or {}).get("id")
    accepted = decision in ("accepted with a swap", "accepted without a swap")
    if accepted and not sprint_id:
        raise HTTPException(400, "There's no sprint to add this to.")
    swap = [i for i in body.get("swap_out_ids") or [] if isinstance(i, int)]
    if decision == "accepted with a swap" and not swap:
        raise HTTPException(400, "Pick the stories that come out to make room.")
    out_items = []
    for sid in swap:
        item = models.backlog_items.fetch(conn, sid)
        if not item or item["sprint_id"] != sprint_id or item["status"] in ("done", "removed"):
            raise HTTPException(400, "Only unfinished stories in this sprint can be swapped out.")
        out_items.append(item)
    for item in out_items:
        models.backlog_items.update(conn, item["id"], {"sprint_id": None, "status": "ready"}, viewer.source)
    item_id = cr["backlog_item_id"]
    if accepted or decision == "deferred to the backlog":
        fields = {"sprint_id": sprint_id if accepted else None, "status": "in sprint" if accepted else "needs refinement"}
        if item_id and models.backlog_items.fetch(conn, item_id):
            models.backlog_items.update(conn, item_id, fields, viewer.source)
        else:
            keys = cr.get("jira_keys") or []
            new = models.backlog_items.create(conn, {"title": cr["title"], "description": cr.get("description"), "points": points,
                                                     "jira_key": keys[0] if keys else None, "added_on": today().isoformat(),
                                                     "team_id": cr.get("team_id"), "notes": f"From change request {cr_id}", **fields}, viewer.source)
            item_id = new["id"]
    updated = models.change_requests.update(conn, cr_id, {
        "status": "decided", "decision": decision, "decision_reason": reason or None, "decided_on": body.get("decided_on") or today().isoformat(),
        "decided_by_id": body.get("decided_by_id") or cr.get("decided_by_id"), "points": points, "sprint_id": sprint_id,
        "swapped_out_ids": [i["id"] for i in out_items], "points_out": sum(i.get("points") or 0 for i in out_items) if out_items else (0 if accepted else None),
        "backlog_item_id": item_id,
    }, viewer.source)
    warning = None
    if decision == "accepted without a swap" and sprint_id:
        imp = sprint_impact(conn, sprint_id)
        if imp["capacity"] and imp["in_sprint"] > imp["capacity"]:
            warning = f"The sprint now holds {imp['in_sprint']} points against a capacity of {imp['capacity']}."
    return {"request": updated, "warning": warning}


@router.post("/api/change-requests/{cr_id}/told")
def told(cr_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    cr = models.change_requests.fetch(conn, cr_id)
    if not cr or cr["status"] in UNDECIDED:
        raise HTTPException(400, "Decide the request before recording that the requester was told.")
    return models.change_requests.update(conn, cr_id, {"communicated_on": body.get("on") or today().isoformat()}, viewer.source)


def changes_due(conn) -> dict:
    """For Today: requests waiting for a decision (oldest first), and decisions nobody has been told about yet."""
    t = today()
    waiting = models.change_requests.fetch_all(conn, "status IN ('received', 'assessing')")
    return {
        "waiting": sorted([{"id": c["id"], "title": c["title"], "urgency": c["urgency"], "days": (t - date.fromisoformat(c["requested_on"])).days} for c in waiting], key=lambda c: -c["days"]),
        "untold": [{"id": c["id"], "title": c["title"], "decision": c["decision"]} for c in models.change_requests.fetch_all(conn, "status = 'decided' AND communicated_on IS NULL")],
    }


def changes_between(conn, start: str, end: str, floor: Level) -> list[dict]:
    """Requests raised or decided in a period, at a privacy level, for reports."""
    rows = models.change_requests.fetch_all(conn, "(requested_on BETWEEN ? AND ?) OR (decided_on BETWEEN ? AND ?)", (start, end, start, end))
    return models.change_requests.visible_all(rows, Viewer(floor=floor, source="report"))


def report_lines(crs: list[dict]) -> list[str]:
    lines = []
    for c in crs:
        what = c.get("decision") or "awaiting a decision"
        size = []
        if c.get("points") is not None:
            size.append(f"{c['points']} pts")
        if c.get("points_out"):
            size.append(f"{c['points_out']} pts swapped out")
        lines.append(f"- {c['title']} (from {c['source']}): {what}" + (f", {', '.join(size)}" if size else "")
                     + (f". {c['decision_reason']}" if c.get("decision_reason") else ""))
    return lines


ACCEPTED = ("accepted with a swap", "accepted without a swap")


def requesters(conn, viewer: Viewer) -> dict:
    """Who asks for work mid-sprint most often, by person and by source, and what share was accepted."""
    crs = models.change_requests.visible_all(models.change_requests.fetch_all(conn), viewer)
    names = {p["id"]: p["name"] for p in models.people.fetch_all(conn)}

    def group(key):
        out = {}
        for c in crs:
            k = key(c)
            if k is None:
                continue
            g = out.setdefault(k, {"requests": 0, "accepted": 0, "deferred": 0, "rejected": 0, "emergencies": 0, "last": None})
            g["requests"] += 1
            g["accepted"] += c.get("decision") in ACCEPTED
            g["deferred"] += c.get("decision") == "deferred to the backlog"
            g["rejected"] += c.get("decision") == "rejected"
            g["emergencies"] += c.get("urgency") == "emergency"
            if c.get("requested_on") and (not g["last"] or c["requested_on"] > g["last"]):
                g["last"] = c["requested_on"]
        rows = [{"name": k, **v, "accepted_pct": round(100 * v["accepted"] / v["requests"]) if v["requests"] else None} for k, v in out.items()]
        return sorted(rows, key=lambda r: (-r["requests"], r["name"]))

    people = group(lambda c: names.get(c.get("requested_by_id")) if c.get("requested_by_id") else None)
    return {"people": people, "sources": group(lambda c: c.get("source")), "total": len(crs)}


@router.get("/api/change-requests/requesters")
def get_requesters(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return requesters(conn, viewer)


@router.get("/api/change-requests/policy-summary")
def policy_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A short summary for the people who send requests: the policy, and what's happened recently. Shareable fields only."""
    policy = _setting(conn, POLICY_KEY, "") or STARTER_POLICY
    recent = churn(conn, my_team_id(conn), 4)
    lines = ["# Asking for work during a sprint", "", "How the team handles new requests once a sprint has started, so you know what to expect.", "", policy.strip(), ""]
    if any(s["requests"] for s in recent):
        req = sum(s["requests"] for s in recent)
        acc = sum(s["accepted"] for s in recent)
        lines += ["## Recently", "", f"Over the last {len(recent)} sprint{'s' if len(recent) != 1 else ''}: {req} request{'s' if req != 1 else ''}, {acc} accepted into the sprint, "
                  f"{sum(s['deferred'] for s in recent)} moved to the backlog, {sum(s['rejected'] for s in recent)} declined.", ""]
    lines += ["## How to ask", "", "Send it to the product owner with what it is, why it matters now, and when it's needed. You'll hear back with a decision and the reason."]
    return {"markdown": "\n".join(lines).rstrip() + "\n"}
