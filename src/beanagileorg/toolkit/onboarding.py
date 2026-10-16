"""Onboarding: a checklist template by track, copied into a plan for each new team member with dates from their start."""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()
PHASES = [("Before day 1", None, 0), ("Week 1", 1, 7), ("Weeks 2 to 4", 8, 30), ("Days 31 to 90", 31, 90), ("After day 90", 91, None)]

SD, MD, QA, EMP, CON = "Salesforce developer", "MuleSoft developer", "QA", "employee", "contractor"
# (day, owner, category, title, description, link, tracks). Generic practice only; anything company-specific is a [Placeholder].
STARTER = [
    (-7, "IT or admin", "accounts and access", "Request accounts: email, chat, Bitbucket and Jira", "Also [Placeholder: sign-in system and any other tools]. Ask early; access is the most common day-one blocker.", "", []),
    (-7, "manager", "accounts and access", "Request a Salesforce sandbox user with the right permission sets", "Which sandbox and permission sets: [Placeholder].", "", [SD, QA]),
    (-7, "manager", "accounts and access", "Request Anypoint Platform access for the right business groups and environments", "", "", [MD]),
    (-5, "manager", "people", "Pick a buddy and brief them", "The buddy answers the small questions, pairs on the first story and checks in daily in week 1.", "", []),
    (-3, "manager", "ways of working", "Add them to the team's ceremonies, channels and distribution lists", "", "", []),
    (-3, "manager", "admin and compliance", "Confirm contract dates, agency contact and how time is reported", "", "", [CON]),
    (1, "manager", "people", "Welcome one-on-one: the role, the first 30 days, how we work", "Share this checklist. Agree how often you'll check in during the first month.", "", []),
    (1, "buddy", "people", "Buddy walk-through: the team, the tools, where things live", "", "", []),
    (1, "new member", "tools and setup", "Set up the laptop and development tools", "[Placeholder: standard tool list and setup guide].", "", []),
    (1, "new member", "admin and compliance", "Complete required company training", "[Placeholder: where the training lives and what's required].", "", [EMP]),
    (2, "new member", "ways of working", "Read our SDLC: how work moves from idea to production", "Note anything that's unclear and bring it to your buddy.", "#/sdlc", []),
    (2, "new member", "ways of working", "Read the definition of done", "", "#/qa/dod", []),
    (2, "new member", "tools and setup", "Learn the team's Jira board: how stories move, the workflow states and how to pick up work", "[Placeholder: board name and project key].", "", []),
    (3, "new member", "systems and architecture", "Tour the system map and the systems we own", "", "#/architecture", []),
    (3, "new member", "systems and architecture", "Read the architecture guides for your area", "", "#/architecture/guides", []),
    (3, "new member", "tools and setup", "Clone the Salesforce project from Bitbucket and deploy it to your sandbox", "", "", [SD]),
    (3, "new member", "tools and setup", "Run a MuleSoft application locally and deploy it to a non-production environment", "", "", [MD]),
    (3, "new member", "ways of working", "Walk through the smoke test library and run one smoke test", "", "#/qa/library", [QA]),
    (4, "new member", "ways of working", "Learn who decides what", "The RACI shows who is responsible, accountable, consulted and informed for the main decisions.", "#/raci", []),
    (5, "new member", "people", "Meet each team member for 20 minutes", "Ask what they work on, what they wish they'd known in their first month, and how they like to be contacted.", "#/people", []),
    (5, "new member", "ways of working", "Attend every ceremony this sprint", "Planning, daily standup, refinement, review and retro.", "", []),
    (10, "new member", "first work", "Pair on a first story with your buddy, through code review to done", "", "", [SD, MD]),
    (10, "new member", "first work", "Pair on testing a story through to QA sign-off", "", "", [QA]),
    (10, "new member", "systems and architecture", "Read the escalation playbook and shadow a support handoff", "", "#/escalation", []),
    (14, "new member", "learning", "Learn how we test: smoke tests, automated suites and regression plans", "", "#/qa", [SD, MD]),
    (14, "new member", "learning", "Salesforce learning: [Placeholder: Trailhead modules for the clouds we use]", "", "", [SD]),
    (14, "new member", "learning", "MuleSoft learning: [Placeholder: courses]", "", "", [MD]),
    (20, "new member", "first work", "Take a story from refinement to done on your own", "", "", [SD, MD, QA]),
    (30, "manager", "people", "30-day check-in: what's working, what's confusing, what to change", "Ask what this checklist missed, and update the template.", "", []),
    (45, "new member", "first work", "Lead a refinement session or demo at sprint review", "", "", []),
    (60, "new member", "learning", "Give a short group-learning talk on something you've learned here", "", "#/learning", []),
    (90, "manager", "people", "90-day review, with feedback both ways", "", "", []),
]


def _day(start: str | None, n: int | None) -> str | None:
    if not start or n is None:
        return None
    # Day 1 is the start date; -7 is a week before it, and 0 is the day before.
    offset = n - 1 if n >= 1 else (n if n < 0 else -1)
    return (date.fromisoformat(start) + timedelta(days=offset)).isoformat()


def _phase(day: int | None) -> str:
    if day is None:
        return "No date"
    for name, lo, hi in PHASES:
        if (lo is None or day >= lo) and (hi is None or day <= hi):
            return name
    return "No date"


def _applies(item: dict, tracks: list[str]) -> bool:
    return not item["tracks"] or any(t in tracks for t in item["tracks"])


@router.post("/api/onboarding/starter", status_code=201)
def load_starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM onboarding_items").fetchone()[0]:
        raise HTTPException(409, "There's already a checklist. Edit it instead.")
    for pos, (day, owner, cat, title, desc, link, tracks) in enumerate(STARTER):
        models.onboarding_items.create(conn, {"title": title, "description": desc or None, "category": cat, "due_day": day, "owner_role": owner,
                                              "tracks": tracks, "link": link or None, "position": pos}, viewer.source)
    return {"items": len(STARTER)}


@router.post("/api/onboardings", status_code=201)
def start_onboarding(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Copy the checklist items that apply to this person's tracks; later template edits don't change a plan in progress."""
    require_write(viewer)
    if not models.people.fetch(conn, body.get("person_id") or 0):
        raise HTTPException(400, "Pick the person who's joining (add them under People first).")
    ob = models.onboardings.create(conn, body, viewer.source)
    tracks = ob["tracks"]
    copied = 0
    for item in models.onboarding_items.fetch_all(conn, "active = 1"):
        if _applies(item, tracks):
            models.onboarding_tasks.create(conn, {"onboarding_id": ob["id"], "item_id": item["id"], **{k: item[k] for k in ("title", "description", "category", "due_day", "owner_role", "link", "minutes")}}, viewer.source)
            copied += 1
    return {**models.onboardings.visible(models.onboardings.fetch(conn, ob["id"]), viewer), "copied": copied}


@router.patch("/api/onboarding-tasks/{task_id}")
def update_task(task_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if "done" in body and "done_on" not in body:
        body = {**body, "done_on": date.today().isoformat() if body["done"] else None}
    task = models.onboarding_tasks.update(conn, task_id, body, viewer.source)
    if task is None:
        raise HTTPException(404, "No such task.")
    return models.onboarding_tasks.visible(task, viewer)


def _board(conn, ob_id: int, viewer: Viewer) -> dict:
    ob = models.onboardings.fetch(conn, ob_id)
    if ob is None:
        raise HTTPException(404, "No such onboarding.")
    today = date.today().isoformat()
    tasks = []
    for t in models.onboarding_tasks.visible_all(models.onboarding_tasks.fetch_all(conn, "onboarding_id = ?", (ob_id,)), viewer):
        due = _day(ob["start_date"], t["due_day"])
        tasks.append({**t, "due": due, "overdue": bool(due and due < today and not t["done"]), "phase": _phase(t["due_day"])})
    order = [p[0] for p in PHASES] + ["No date"]
    phases = [{"name": n, "tasks": [t for t in tasks if t["phase"] == n]} for n in order]
    return {"onboarding": models.onboardings.visible(ob, viewer), "phases": [p for p in phases if p["tasks"]],
            "overdue": sum(t["overdue"] for t in tasks), "by_owner": {o: sum(1 for t in tasks if t["owner_role"] == o and not t["done"]) for o in models.ONBOARDING_OWNERS}}


@router.get("/api/onboardings/{ob_id}/board")
def board(ob_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return _board(conn, ob_id, viewer)


def build_checklist(conn, ob_id: int, viewer: Viewer) -> dict:
    """A Markdown checklist to send the new member. Links inside the toolkit are left out, since they can't open it."""
    d = _board(conn, ob_id, viewer)
    ob = d["onboarding"]
    lines = [f"# Welcome, {ob['person_name']}", ""]
    if ob["start_date"]:
        lines += [f"Your start date: {ob['start_date']}." + (f" Your buddy: {ob['buddy_name']}." if ob.get("buddy_name") else ""), ""]
    for p in d["phases"]:
        lines += [f"## {p['name']}", ""]
        for t in p["tasks"]:
            who = "" if t["owner_role"] == "new member" else f" ({t['owner_role']})"
            when = f" by {t['due']}" if t["due"] else ""
            link = f" {t['link']}" if (t.get("link") or "").startswith(("http://", "https://")) else ""
            lines.append(f"- [{'x' if t['done'] else ' '}] {t['title']}{who}{when}{link}")
        lines.append("")
    return {"title": f"Onboarding checklist: {ob['person_name']}", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/onboardings/{ob_id}/checklist")
def checklist(ob_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_checklist(conn, ob_id, viewer)


@router.post("/api/onboardings/{ob_id}/checklist/export")
def export_checklist(ob_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_checklist(conn, ob_id, viewer)
    log_export(conn, "onboarding:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


def onboarding_due(conn, today: str, week: str) -> list[dict]:
    """Open tasks for you or a buddy that are overdue or due this week, across every onboarding in progress."""
    out = []
    for ob in models.onboardings.fetch_all(conn, "status != 'done' AND start_date IS NOT NULL"):
        for t in models.onboarding_tasks.fetch_all(conn, "onboarding_id = ? AND done = 0 AND owner_role IN ('manager', 'buddy', 'IT or admin')", (ob["id"],)):
            due = _day(ob["start_date"], t["due_day"])
            if due and due <= week:
                out.append({"onboarding_id": ob["id"], "person_name": ob["person_name"], "id": t["id"], "title": t["title"], "owner_role": t["owner_role"], "due": due, "overdue": due < today})
    return sorted(out, key=lambda x: x["due"])
