"""Releases: what's in each release, where it is on the path to production, the regression plan and QA sign-off,
the go/no-go decision with a readiness check, and how it went. The release log also gives two delivery measures:
how often you deploy, and what share of releases needed a fix.

Path step names come from your SDLC environments or from settings, never from code.
"""

import json
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

PATH_KEY = "releases.path"
DEFAULT_PATH = ["Developer sandbox", "Integration sandbox", "QA sandbox", "Staging", "Production"]
FAILED = ("hotfix", "rollback", "incident")
METRIC_NAMES = {"deployment_frequency": "Deployment frequency", "change_failure_rate": "Change failure rate"}


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def path_steps(conn) -> list[str]:
    saved = _setting(conn, PATH_KEY)
    if saved:
        return saved
    envs = [e["name"] for e in models.sdlc_environments.fetch_all(conn)]
    return envs or DEFAULT_PATH


@router.get("/api/releases/settings")
def get_settings(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"path": path_steps(conn), "custom": bool(_setting(conn, PATH_KEY)), "default": DEFAULT_PATH,
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
    if not items:
        raise HTTPException(400, "No stories are planned in that sprint yet.")
    keys = sorted({*(r.get("jira_keys") or []), *(i["jira_key"] for i in items if i.get("jira_key"))})
    return models.releases.update(conn, release_id, {"story_ids": [i["id"] for i in items], "jira_keys": keys}, viewer.source)


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
    return {"release": r, "stories": [{"id": s["id"], "title": s["title"], "jira_key": s.get("jira_key"), "status": s["status"], "points": s.get("points")} for s in stories],
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
    lines += ["", "## What changes for you", "- [Placeholder]", "", "## Who to ask", "[Placeholder name or channel]"]
    return {"markdown": "\n".join(lines)}


def release_metrics(conn, weeks: int = 8) -> dict:
    since = (today() - timedelta(weeks=weeks)).isoformat()
    done = [r for r in models.releases.fetch_all(conn, "released_on IS NOT NULL AND released_on >= ?", (since,))]
    judged = [r for r in done if r.get("outcome")]
    failed = [r for r in judged if r["outcome"] in FAILED]
    by_name = {m["name"].strip().lower(): m["id"] for m in models.metrics.fetch_all(conn)}
    return {"weeks": weeks, "released": len(done), "per_week": round(len(done) / weeks, 2),
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
    for key, value in (("deployment_frequency", m["per_week"]), ("change_failure_rate", m["change_failure_rate"])):
        mid = m["metric_ids"][key]
        if mid and value is not None:
            models.metric_readings.create(conn, {"metric_id": mid, "date": today().isoformat(), "value": value}, viewer.source)
            recorded.append(METRIC_NAMES[key])
    if not recorded:
        raise HTTPException(400, "Nothing to record. Add the Deployment frequency and Change failure rate metrics (the starter metrics include them), and log released releases with an outcome.")
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
