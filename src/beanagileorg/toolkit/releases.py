"""Releases: what's in each release, where it is on the path to production, the regression plan and QA sign-off,
the go/no-go decision with a readiness check, and how it went. The release log also gives two delivery measures:
how often you deploy, and what share of releases needed a fix.

Path step names come from your SDLC environments or from settings, never from code.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

PATH_KEY = "releases.path"
DEFAULT_PATH = ["Development", "Integration", "QA", "Staging", "Production"]
SALESFORCE_PATH = ["Developer sandbox", "Integration sandbox", "QA sandbox", "Staging", "Production"]
FAILED = ("hotfix", "rollback", "incident")
METRIC_NAMES = {"deployment_frequency": "Deployment frequency", "change_failure_rate": "Change failure rate", "time_to_restore": "Time to restore"}
CLASH_KINDS = ("platform release", "Salesforce release", "peak-season freeze")


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def path_steps(conn) -> list[str]:
    saved = _setting(conn, PATH_KEY)
    if saved:
        return saved
    envs = [e["name"] for e in models.sdlc_environments.fetch_all(conn)]
    return envs or default_path(conn)


def default_path(conn) -> list[str]:
    from .routes import platform

    return SALESFORCE_PATH if platform(conn) == "salesforce" else DEFAULT_PATH


@router.get("/api/releases/settings")
def get_settings(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"path": path_steps(conn), "custom": bool(_setting(conn, PATH_KEY)), "default": default_path(conn),
            "from_sdlc": [e["name"] for e in models.sdlc_environments.fetch_all(conn)]}


@router.put("/api/releases/settings")
def put_settings(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    steps = [str(s).strip() for s in body.get("path") or [] if str(s).strip()]
    if steps:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (PATH_KEY, json.dumps(steps[:12])))
    else:
        conn.execute("DELETE FROM settings WHERE key = ?", (PATH_KEY,))
    return get_settings(viewer, conn)


def _release(conn, release_id: int) -> dict:
    r = models.releases.fetch(conn, release_id)
    if r is None:
        raise HTTPException(404, "No such release.")
    return r


@router.post("/api/releases/{release_id}/start-path")
def start_path(release_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    r = _release(conn, release_id)
    if (r.get("path") or {}).get("steps"):
        raise HTTPException(409, "This release already has its path.")
    steps = [{"step": s, "planned": None, "done_on": None, "notes": ""} for s in path_steps(conn)]
    return models.releases.update(conn, release_id, {"path": {"steps": steps}}, viewer.source)


@router.post("/api/releases/{release_id}/from-sprint")
def from_sprint(release_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Fill the release with the stories planned in its sprint, and their Jira keys."""
    require_write(viewer)
    r = _release(conn, release_id)
    if not r.get("sprint_id"):
        raise HTTPException(400, "Pick the release's sprint first.")
    items = models.backlog_items.fetch_all(conn, "sprint_id = ? AND status != 'removed'", (r["sprint_id"],))
    crs = [c for c in models.change_requests.fetch_all(conn, "sprint_id = ?", (r["sprint_id"],)) if (c.get("decision") or "").startswith("accepted")]
    if not items and not crs:
        raise HTTPException(400, "No stories are planned in that sprint yet.")
    keys = sorted({*(r.get("jira_keys") or []), *(i["jira_key"] for i in items if i.get("jira_key")), *(k for c in crs for k in (c.get("jira_keys") or []))})
    return models.releases.update(conn, release_id, {"story_ids": [i["id"] for i in items], "jira_keys": keys,
                                                     "change_request_ids": sorted({*(r.get("change_request_ids") or []), *(c["id"] for c in crs)})}, viewer.source)


def readiness(conn, r: dict) -> dict:
    stories = models.backlog_items.fetch_all(conn, f"id IN ({','.join('?' * len(r['story_ids']))})", tuple(r["story_ids"])) if r.get("story_ids") else []
    open_stories = [s["title"] for s in stories if s["status"] != "done"]
    steps = (r.get("path") or {}).get("steps") or []
    before_last = [s for s in steps[:-1] if not s.get("done_on")]
    checks = [
        {"key": "stories", "label": "Every story in the release is done", "ok": bool(stories) and not open_stories,
         "detail": f"{len(open_stories)} not done" if open_stories else ("no stories linked" if not stories else "")},
        {"key": "regression", "label": "The regression plan is signed off", "ok": r.get("regression_status") in ("signed off", "done"),
         "detail": "" if r.get("regression_plan_id") else "no regression plan linked"},
        {"key": "qa", "label": "QA has signed off", "ok": bool(r.get("qa_signoff_on")), "detail": ""},
        {"key": "path", "label": "Every step before production is done", "ok": bool(steps) and not before_last,
         "detail": ", ".join(s["step"] for s in before_last) if before_last else ("no path yet" if not steps else "")},
    ]
    return {"checks": checks, "ready": all(c["ok"] for c in checks)}


@router.get("/api/releases/{release_id}/detail")
def detail(release_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    r = models.releases.visible(_release(conn, release_id), viewer)
    full = _release(conn, release_id)
    stories = models.backlog_items.fetch_all(conn, f"id IN ({','.join('?' * len(full['story_ids']))})", tuple(full["story_ids"])) if full.get("story_ids") else []
    crs = [c for c in models.change_requests.fetch_all(conn) if c["id"] in (full.get("change_request_ids") or [])]
    return {"release": r, "stories": [{"id": s["id"], "title": s["title"], "jira_key": s.get("jira_key"), "status": s["status"], "points": s.get("points")} for s in stories],
            "change_requests": [{"id": c["id"], "title": c["title"], "decision": c.get("decision"), "requested_on": c.get("requested_on"), "points": c.get("points")} for c in crs],
            "readiness": readiness(conn, full), "path_steps": path_steps(conn)}


@router.get("/api/releases/{release_id}/notes")
def notes(release_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Release notes as Markdown, built from shareable fields only."""
    r = _release(conn, release_id)
    stories = models.backlog_items.fetch_all(conn, f"id IN ({','.join('?' * len(r['story_ids']))})", tuple(r["story_ids"])) if r.get("story_ids") else []
    when = r.get("released_on") or r.get("planned_on")
    lines = [f"# {r['name']}", ""]
    if when:
        lines += [f"**{'Released' if r.get('released_on') else 'Planned for'}:** {when}", ""]
    lines += ["## What's in it"] + ([f"- {s['title']}" + (f" ({s['jira_key']})" if s.get("jira_key") else "") for s in stories] or ["- [Placeholder: what this release changes]"])
    crs = [c for c in models.change_requests.fetch_all(conn) if c["id"] in (r.get("change_request_ids") or []) and not c.get("never_share")]
    if crs:
        lines += ["", "## Added during the sprint"] + [f"- {c['title']}" for c in crs]
    lines += ["", "## What changes for you", "- [Placeholder]", "", "## Who to ask", "[Placeholder name or channel]"]
    return {"markdown": "\n".join(lines)}


def release_metrics(conn, weeks: int = 8) -> dict:
    since = (today() - timedelta(weeks=weeks)).isoformat()
    done = [r for r in models.releases.fetch_all(conn, "released_on IS NOT NULL AND released_on >= ?", (since,))]
    judged = [r for r in done if r.get("outcome")]
    failed = [r for r in judged if r["outcome"] in FAILED]
    by_name = {m["name"].strip().lower(): m["id"] for m in models.metrics.fetch_all(conn)}
    restores = []
    for r in failed:
        inc = models.incidents.fetch(conn, r["incident_id"]) if r.get("incident_id") else None
        if inc and inc.get("date") and inc.get("resolved_at"):
            restores.append((date.fromisoformat(inc["resolved_at"]) - date.fromisoformat(inc["date"])).days)
    return {"weeks": weeks, "released": len(done), "per_week": round(len(done) / weeks, 2),
            "time_to_restore": round(sum(restores) / len(restores), 1) if restores else None, "restores": len(restores),
            "judged": len(judged), "failed": len(failed), "change_failure_rate": round(100 * len(failed) / len(judged), 1) if judged else None,
            "metric_ids": {k: by_name.get(v.lower()) for k, v in METRIC_NAMES.items()}, "metric_names": METRIC_NAMES}


@router.get("/api/releases/metrics")
def get_metrics(weeks: int = 8, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return release_metrics(conn, max(1, min(weeks, 52)))


@router.post("/api/releases/metrics/record", status_code=201)
def record_metrics(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record today's deployment frequency and change failure rate as readings on the matching metrics."""
    require_write(viewer)
    m = release_metrics(conn, max(1, min(int(body.get("weeks") or 8), 52)))
    recorded = []
    for key, value in (("deployment_frequency", m["per_week"]), ("change_failure_rate", m["change_failure_rate"]), ("time_to_restore", m["time_to_restore"])):
        mid = m["metric_ids"][key]
        if mid and value is not None:
            models.metric_readings.create(conn, {"metric_id": mid, "date": today().isoformat(), "value": value}, viewer.source)
            recorded.append(METRIC_NAMES[key])
    if not recorded:
        raise HTTPException(400, "Nothing to record. Add the Deployment frequency, Change failure rate or Time to restore metrics, and log released releases with an outcome (and, for failures, a linked incident with its resolved date).")
    return {"recorded": recorded}


def releases_due(conn) -> list[dict]:
    """For Today: releases due within a week that aren't ready, and released ones with no outcome recorded."""
    t = today()
    week = (t + timedelta(days=7)).isoformat()
    out = []
    for r in models.releases.fetch_all(conn, "status NOT IN ('released', 'cancelled') AND planned_on IS NOT NULL AND planned_on <= ?", (week,)):
        rd = readiness(conn, r)
        if not rd["ready"]:
            out.append({"id": r["id"], "name": r["name"], "kind": "not ready", "date": r["planned_on"], "missing": sum(not c["ok"] for c in rd["checks"])})
    for r in models.releases.fetch_all(conn, "released_on IS NOT NULL AND outcome IS NULL AND released_on <= ?", ((t - timedelta(days=2)).isoformat(),)):
        out.append({"id": r["id"], "name": r["name"], "kind": "outcome", "date": r["released_on"], "missing": 0})
    return out[:8]


def metric_direction(conn, m: dict, n: int = 3) -> str | None:
    """Improving, worsening or flat, from the last few readings and whether higher is better. None with fewer than two."""
    rows = conn.execute("SELECT value FROM metric_readings WHERE metric_id = ? AND value IS NOT NULL ORDER BY date DESC, id DESC LIMIT ?", (m["id"], n)).fetchall()
    vals = [r["value"] for r in rows][::-1]
    if len(vals) < 2:
        return None
    change = vals[-1] - vals[0]
    scale = max(abs(v) for v in vals) or 1
    if abs(change) / scale < 0.05:
        return "flat"
    better = change > 0 if m.get("higher_is_better", True) else change < 0
    return "improving" if better else "worsening"


@router.get("/api/metrics/directions")
def directions(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {m["id"]: metric_direction(conn, m) for m in models.metrics.fetch_all(conn)}


DECISION_PROCESS = "consult and decide"


@router.put("/api/releases/{release_id}/decision")
def decide(release_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record go or no-go on the release, and log it under Risks and decisions with who decided and any checks still open."""
    require_write(viewer)
    r = _release(conn, release_id)
    decision = body.get("decision")
    if decision not in models.RELEASE_DECISIONS:
        raise HTTPException(400, f"Pick one of: {', '.join(models.RELEASE_DECISIONS)}.")
    fields = {"decision": decision, "decided_by_id": body.get("decided_by_id"), "decided_on": body.get("decided_on") or (today().isoformat() if decision != "pending" else None),
              "decision_notes": body.get("decision_notes") or ""}
    updated = models.releases.update(conn, release_id, fields, viewer.source)
    logged = None
    if decision != "pending" and decision != r.get("decision"):
        rd = readiness(conn, updated)
        open_checks = [c["label"] for c in rd["checks"] if not c["ok"]]
        outcome = ("Go" if decision == "go" else "No-go") + (f": {fields['decision_notes']}" if fields["decision_notes"] else "")
        if open_checks:
            outcome += f" (open at the time: {'; '.join(open_checks)})"
        logged = models.decisions_needed.create(conn, {"decision": f"Release {r['name']}: go or no-go", "from_id": fields["decided_by_id"], "needed_by": r.get("planned_on"),
                                                        "status": "decided", "outcome": outcome, "process": DECISION_PROCESS, "jira_keys": r.get("jira_keys") or [],
                                                        "team_id": r.get("team_id")}, viewer.source)["id"]
    return {"release": updated, "logged_decision_id": logged}


@router.get("/api/releases/calendar")
def calendar(days_back: int = 14, days_ahead: int = 120, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Releases and regression windows (platform releases, peak-season freezes) on one timeline, with clashes."""
    t = today()
    lo, hi = (t - timedelta(days=max(0, days_back))).isoformat(), (t + timedelta(days=max(7, min(days_ahead, 365)))).isoformat()
    windows = []
    for p in models.regression_plans.fetch_all(conn):
        s, e = p.get("start_date"), p.get("end_date") or p.get("start_date")
        if s and e >= lo and s <= hi:
            windows.append({"id": p["id"], "title": p["title"], "kind": p["kind"], "start": s, "end": e, "status": p["status"]})
    rels = []
    for r in models.releases.fetch_all(conn, "status != 'cancelled'"):
        d = r.get("released_on") or r.get("planned_on")
        if d and lo <= d <= hi:
            clashes = [w["title"] for w in windows if w["kind"] in CLASH_KINDS and w["start"] <= d <= w["end"]]
            rels.append({"id": r["id"], "name": r["name"], "date": d, "released": bool(r.get("released_on")), "outcome": r.get("outcome"), "clashes": clashes})
    return {"from": lo, "to": hi, "today": t.isoformat(), "windows": windows, "releases": rels, "clash_kinds": CLASH_KINDS}
