"""Core processes: the ways the team turns work into value, judged on productivity, timeliness, reliability and
quality, with a workflow map of who hands what to whom, so the team can find bottlenecks and failing handoffs.

After the core-process ideas in chapter 6 of The First 90 Days (Michael Watkins), in our own words.
"""

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()

# (key, name, question, the metrics that usually measure it)
MEASURES = [
    ("productivity", "Productivity", "Does it turn people's time and knowledge into value efficiently?", ["Deployment frequency", "Throughput"]),
    ("timeliness", "Timeliness", "Does it deliver value when it's needed?", ["Cycle time", "Lead time"]),
    ("reliability", "Reliability", "Does it hold up, or break down too often?", ["Change failure rate", "Time to restore"]),
    ("quality", "Quality", "Does it meet the quality standard, every time?", ["Escaped defects"]),
]
RATINGS = ("strong", "adequate", "weak")
AIMS = {
    "execution": "Flawless execution: reliable, high quality, low cost. Specify both the ends and the means (methods, tools, checklists) in detail.",
    "innovation": "Innovation: define the ends clearly and check progress at key milestones, but leave people free to choose the means.",
    "both": "Parts of it need each. Specify the means where reliability matters, and only the ends where you want new ideas.",
}
STARTER = ["Request intake", "Backlog refinement", "Building and code review", "Testing and QA", "Release and deploy", "Production support and incidents"]
FOCUS_LIMIT = 3
SCRUM = ("A workflow map is the start of a value stream. Make the board's columns match the real steps, so work waiting at a "
         "handoff is visible, and use the retrospective to pick the next handoff or bottleneck to fix.")


def _metric_ids(conn) -> dict:
    by_name = {m["name"].strip().lower(): m["id"] for m in models.metrics.fetch_all(conn)}
    return {k: [{"name": n, "id": by_name[n.lower()]} for n in names if n.lower() in by_name] for k, _, _, names in MEASURES}


@router.get("/api/processes/guide")
def guide(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    focus = conn.execute("SELECT COUNT(*) FROM core_processes WHERE focus = 1").fetchone()[0]
    return {"measures": [{"key": k, "name": n, "question": q, "metrics": names} for k, n, q, names in MEASURES], "ratings": RATINGS,
            "aims": AIMS, "importance": models.PROCESS_IMPORTANCE, "starter": STARTER, "focus_limit": FOCUS_LIMIT, "focus_count": focus,
            "linked_metrics": _metric_ids(conn), "scrum": SCRUM}


@router.post("/api/core-processes/starter", status_code=201)
def starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM core_processes").fetchone()[0]:
        raise HTTPException(409, "You already have processes listed. Add to them instead.")
    for pos, name in enumerate(STARTER):
        models.core_processes.create(conn, {"name": name, "position": pos}, viewer.source)
    return {"processes": len(STARTER)}


@router.post("/api/core-processes/{process_id}/from-sdlc")
def from_sdlc(process_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Fill the workflow map from the SDLC stages: each stage becomes a step, with its roles as who does it."""
    require_write(viewer)
    proc = models.core_processes.fetch(conn, process_id)
    if proc is None:
        raise HTTPException(404, "No such process.")
    if (proc.get("map") or {}).get("steps"):
        raise HTTPException(409, "This map already has steps. Clear them first.")
    stages = models.sdlc_stages.fetch_all(conn)
    if not stages:
        raise HTTPException(400, "No SDLC stages yet. Load the starter SDLC first.")
    steps = [{"text": st["name"], "who": (st.get("roles") or "").split(",")[0].strip() or "[Who]", "passes": "", "bottleneck": False, "handoff_issue": ""} for st in stages]
    return models.core_processes.update(conn, process_id, {"map": {"steps": steps}}, viewer.source)


@router.post("/api/core-processes/{process_id}/step-to")
def step_to(process_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn a bottleneck or a failing handoff into a dev-sync item or a risk."""
    require_write(viewer)
    proc = models.core_processes.fetch(conn, process_id)
    if proc is None:
        raise HTTPException(404, "No such process.")
    steps = (proc.get("map") or {}).get("steps") or []
    i, kind = body.get("index"), body.get("to")
    if not isinstance(i, int) or not 0 <= i < len(steps) or kind not in ("devsync", "risk"):
        raise HTTPException(400, "Pick a step, and dev sync or risk.")
    st = steps[i]
    issue = st.get("handoff_issue") or ""
    nxt = steps[i + 1]["text"] if i + 1 < len(steps) else None
    title = f"{proc['name']}: {issue} ({st['text']} to {nxt})" if issue and nxt else f"{proc['name']}: bottleneck at {st['text']}"
    if kind == "risk":
        rec = models.risks.create(conn, {"title": title, "team_id": proc.get("team_id")}, viewer.source)
    else:
        rec = models.action_items.create(conn, {"concern": title, "origin": "other", "team_id": proc.get("team_id")}, viewer.source)
    return {"id": rec["id"], "to": kind}
