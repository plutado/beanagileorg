"""Accelerating everyone: where transitions are happening, setting people up to succeed, and a shared way of doing it.

A transition heat map by unit, a set-up-to-fail check on each onboarding, support items by type of transition, open
seats whose transition risk carries from interview into onboarding (and back again as lessons), a development grid
of each person's roles by function and situation, and a one-page playbook in the toolkit's common language.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

TRANSITION_COLUMNS = [("onboarding", "Onboarding"), ("promotion", "Promotion"), ("moves", "Moves between teams"), ("geographic", "Geographic moves"), ("lateral", "Lateral moves")]
JOINING = ("new hire", "contractor", "move between teams")

# (day, owner, category, title, description) added to an onboarding by type of transition, on top of the checklist.
TYPE_ITEMS = {
    "all": [
        (7, "manager", "people", "Day-7 check-in: what's clear, what isn't, what's in the way", "Short and on the calendar before they start. Set check-ins are what keep support from slipping."),
        (60, "manager", "people", "Day-60 check-in: early wins, relationships, and what to adjust", ""),
    ],
    "new hire": [
        (5, "manager", "people", "Introduce them to the people who'll shape their success", "Product, QA, the architect, key stakeholders. New people can't tell yet who matters."),
        (10, "manager", "people", "Walk through how things really get done here", "The unwritten rules, who to ask, what's been tried before."),
    ],
    "contractor": [
        (5, "manager", "people", "Introduce them to the people they'll depend on", "Contractors are the most often left to sink or swim."),
        (10, "manager", "ways of working", "Make sure they know the team's ways of working and definition of done", ""),
    ],
    "move between teams": [
        (5, "manager", "people", "Introduce them to the new team's stakeholders", ""),
        (10, "manager", "ways of working", "Talk through how this team works differently from their last one", "Teams have their own subcultures; name the differences."),
    ],
    "promotion": [
        (-3, "manager", "people", "Cover their old work: who takes it, and by when", "Promoted people left doing two jobs lose the critical early weeks of the new one."),
        (-3, "manager", "learning", "Schedule the training they need now, not in months", ""),
        (7, "manager", "people", "Agree what success looks like at the new level", "Different skills and behaviors from what got them promoted."),
        (14, "new member", "learning", "Self-assessment against the new level", ""),
        (30, "new member", "learning", "Personal development plan for the new level", ""),
    ],
    "lateral move": [
        (7, "manager", "people", "Agree what's different about this role, and what carries over", ""),
    ],
}

# Ways organizations set people up to fail, in plain words. "auto" ones are read from the toolkit.
RISK_CHECK = [
    ("expectations", "all", "They know what's expected and what they can decide (their mandate is agreed).", "auto"),
    ("situation", "all", "They were placed with the situation in mind, not only their skills.", "manual"),
    ("leap", "all", "The step up isn't too big to absorb all at once.", "manual"),
    ("support", "all", "They have real support: a buddy and set check-ins, not sink or swim.", "auto"),
    ("next_level", "promotion", "They were judged on what the new level needs, not only on doing the old job well.", "manual"),
    ("training", "promotion", "Training comes now, not months later.", "manual"),
    ("old_job", "promotion", "Their old work is covered, so they aren't doing two jobs.", "auto"),
    ("fit", "joining", "Fit with the culture was weighed when hiring, not only capabilities.", "auto"),
    ("culture_help", "joining", "Someone helps them read the culture: a culture guide or a mentor.", "auto"),
    ("stakeholders", "joining", "They're connected early with the people who'll shape their success.", "auto"),
]

EXISTING_SUPPORT_KEY = "transitions.existing_support"
EXISTING_SUPPORT = [
    ("framework", "There's a shared framework and language for planning transitions"),
    ("onboarding", "New hires get structured onboarding beyond access and a ticket"),
    ("contractors", "Contractors get the same start as employees"),
    ("promotion", "Newly promoted people get support and training at the start"),
    ("roles", "Managers, buddies, HR and mentors each know their part"),
    ("data", "Someone knows where and when transitions are happening"),
    ("hiring", "Hiring weighs cultural fit and transition risk, and passes what it learns to onboarding"),
]


def _settings_json(conn, key: str) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else {}


def add_type_items(conn, ob: dict, source: str) -> int:
    """Called when an onboarding starts: the set check-ins and the items for its type of transition."""
    items = TYPE_ITEMS["all"] + TYPE_ITEMS.get(ob.get("transition_type") or "", [])
    for day, owner, cat, title, desc in items:
        models.onboarding_tasks.create(conn, {"onboarding_id": ob["id"], "title": title, "description": desc or None, "category": cat,
                                              "due_day": day, "owner_role": owner}, source)
    return len(items)


def _task_done(conn, ob_id: int, words: str) -> bool | None:
    rows = conn.execute("SELECT done FROM onboarding_tasks WHERE onboarding_id = ? AND lower(title) LIKE ?", (ob_id, f"%{words}%")).fetchall()
    return None if not rows else any(r["done"] for r in rows)


def risk_check(conn, ob: dict) -> dict:
    kind = ob.get("transition_type")
    groups = {"all"} | ({"promotion"} if kind == "promotion" else set()) | ({"joining"} if kind in JOINING else set())
    manual = ob.get("risk_check") or {}
    pid = ob["person_id"]
    auto = {
        "expectations": bool(conn.execute("SELECT 1 FROM mandates WHERE person_id = ? AND status = 'agreed'", (pid,)).fetchone()),
        "support": bool(ob.get("buddy_id")) and bool(conn.execute("SELECT 1 FROM onboarding_tasks WHERE onboarding_id = ? AND lower(title) LIKE '%check-in%'", (ob["id"],)).fetchone()),
        "old_job": _task_done(conn, ob["id"], "cover their old work"),
        "fit": bool((ob.get("risk_profile") or {}).get("culture")) or None,
        "culture_help": bool(ob.get("mentor_id")) or _task_done(conn, ob["id"], "culture guide") or _task_done(conn, ob["id"], "really get done"),
        "stakeholders": _task_done(conn, ob["id"], "introduce them"),
    }
    out = []
    for key, group, text, how in RISK_CHECK:
        if group not in groups:
            continue
        m = manual.get(key) or {}
        status = m.get("status")
        if not status and how == "auto" and auto.get(key) is not None:
            status = "ok" if auto[key] else "risk"
        out.append({"key": key, "group": group, "text": text, "auto": how == "auto", "status": status, "note": m.get("note")})
    return {"type": kind, "items": out, "risks": sum(1 for i in out if i["status"] == "risk"), "open": sum(1 for i in out if not i["status"])}


@router.get("/api/onboardings/{ob_id}/risk-check")
def get_risk_check(ob_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    ob = models.onboardings.fetch(conn, ob_id)
    if not ob:
        raise HTTPException(404, "No such onboarding.")
    return {**risk_check(conn, ob), "risk_profile": ob.get("risk_profile") or {}}


@router.put("/api/onboardings/{ob_id}/risk-check")
def save_risk_check(ob_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    ob = models.onboardings.fetch(conn, ob_id)
    if not ob:
        raise HTTPException(404, "No such onboarding.")
    keys = {k for k, *_ in RISK_CHECK}
    cur = ob.get("risk_check") or {}
    for k, v in body.items():
        if k not in keys or not isinstance(v, dict):
            continue
        if v.get("status") not in (None, "ok", "risk", "na"):
            raise HTTPException(400, "Each answer is ok, risk or not applicable.")
        cur[k] = {"status": v.get("status"), "note": (v.get("note") or None) and str(v["note"])[:500]}
    models.onboardings.update(conn, ob_id, {"risk_check": cur}, viewer.source)
    return risk_check(conn, models.onboardings.fetch(conn, ob_id))


# ---- the heat map ----


def _evidence(conn, team_id: int | None) -> dict | None:
    if not team_id:
        return None
    team = models.teams.fetch(conn, team_id)
    if not team:
        return None
    members = team.get("member_ids") or []
    since = (today() - timedelta(days=180)).isoformat()
    marks = ",".join("?" * len(members)) or "NULL"
    recent = conn.execute(f"SELECT COUNT(*) FROM people WHERE id IN ({marks}) AND start_date >= ?", (*members, since)).fetchone()[0] if members else 0
    onboarding = conn.execute(f"SELECT COUNT(*) FROM onboardings WHERE person_id IN ({marks}) AND status != 'done'", tuple(members)).fetchone()[0] if members else 0
    seats = conn.execute("SELECT COUNT(*) FROM open_seats WHERE team_id = ? AND status IN ('open', 'interviewing')", (team_id,)).fetchone()[0]
    return {"team": team["name"], "members": len(members), "started_recently": recent, "onboarding": onboarding, "open_seats": seats}


@router.get("/api/transitions")
def transitions(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    units = models.transition_units.visible_all(models.transition_units.fetch_all(conn), viewer)
    rank = {"high": 3, "medium": 2, "low": 1}
    hot = sorted(((rank.get(u.get(k) or "", 0), u["unit"], label) for u in units for k, label in TRANSITION_COLUMNS if rank.get(u.get(k) or "", 0) >= 3), reverse=True)
    out = {"columns": [{"key": k, "label": l} for k, l in TRANSITION_COLUMNS], "intensity": list(models.INTENSITY),
           "units": [{**u, "evidence": _evidence(conn, u.get("team_id"))} for u in units],
           "priorities": [f"{label}: {unit}" for _, unit, label in hot]}
    if viewer.floor == Level.PRIVATE and not viewer.guarded:
        ticked = _settings_json(conn, EXISTING_SUPPORT_KEY)
        out["existing_support"] = [{"key": k, "label": l, "status": (ticked.get(k) or {}).get("status"), "note": (ticked.get(k) or {}).get("note")} for k, l in EXISTING_SUPPORT]
        filled = models.open_seats.fetch_all(conn, "status = 'filled' AND lessons IS NOT NULL AND lessons != ''")
        out["lessons"] = [{"seat": s["title"], "lessons": s["lessons"], "risks_real": s.get("risks_real") or {}} for s in filled]
    return out


@router.put("/api/transitions/existing-support")
def save_existing_support(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {k for k, _ in EXISTING_SUPPORT}
    cur = _settings_json(conn, EXISTING_SUPPORT_KEY)
    for k, v in body.items():
        if k in keys and isinstance(v, dict):
            if v.get("status") not in (None, "yes", "partly", "no"):
                raise HTTPException(400, "Each answer is yes, partly or no.")
            cur[k] = {"status": v.get("status"), "note": v.get("note") or None}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (EXISTING_SUPPORT_KEY, json.dumps(cur)))
    return {"saved": cur}


# ---- open seats: transition risk from interview into onboarding, and lessons back ----

RISK_AREAS = [("culture", "Fit with how things are done here"), ("situation", "Experience with this kind of situation"),
              ("stakeholders", "Building the relationships the role needs"), ("leap", "Size of the step up")]


@router.get("/api/open-seats/{seat_id}/detail", dependencies=[Depends(no_judgments)])
def seat_detail(seat_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    seat = models.open_seats.fetch(conn, seat_id)
    if not seat:
        raise HTTPException(404, "No such seat.")
    cands = models.seat_candidates.fetch_all(conn, "seat_id = ?", (seat_id,))
    ob = models.onboardings.fetch(conn, seat["onboarding_id"]) if seat.get("onboarding_id") else None
    day = None
    if ob and ob.get("start_date"):
        day = (date.today() - date.fromisoformat(ob["start_date"])).days + 1
    return {"seat": seat, "candidates": cands, "risk_areas": [{"key": k, "label": l} for k, l in RISK_AREAS],
            "onboarding": ob, "day": day, "lessons_due": bool(day and day >= 90 and not seat.get("lessons"))}


@router.post("/api/open-seats/{seat_id}/hire", status_code=201)
def hire(seat_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Fill the seat: a person (or the one named), an onboarding of the right type, and the interview's risk profile carried in."""
    require_write(viewer)
    seat = models.open_seats.fetch(conn, seat_id)
    if not seat:
        raise HTTPException(404, "No such seat.")
    if seat["status"] in ("filled", "closed"):
        raise HTTPException(409, "This seat is already filled or closed.")
    kind = body.get("transition_type") or "new hire"
    if kind not in models.TRANSITION_TYPES:
        raise HTTPException(400, "Unknown type of transition.")
    cand = models.seat_candidates.fetch(conn, body["candidate_id"]) if body.get("candidate_id") else None
    if body.get("candidate_id") and (not cand or cand["seat_id"] != seat_id):
        raise HTTPException(400, "That candidate isn't for this seat.")
    pid = body.get("person_id")
    if pid:
        if not models.people.fetch(conn, pid):
            raise HTTPException(400, "No such person.")
    else:
        name = (body.get("name") or (cand or {}).get("name") or "").strip()
        if not name:
            raise HTTPException(400, "Name who's joining, or pick someone already in People.")
        pid = models.people.create(conn, {"name": name, "role": seat["title"], "active": True, "start_date": body.get("start_date"),
                                          "relationship": "contractor" if kind == "contractor" else "employee",
                                          "placeholder": name.startswith("[")}, viewer.source)["id"]
    profile = {k: v for k, v in ((cand or {}).get("risks") or {}).items() if v}
    if seat.get("culture_notes"):
        profile.setdefault("culture", seat["culture_notes"])
    from .onboarding import start_onboarding
    ob = start_onboarding({"person_id": pid, "start_date": body.get("start_date"), "tracks": body.get("tracks") or [], "transition_type": kind,
                           "risk_profile": profile, "seat_id": seat_id}, viewer, conn)
    if cand:
        models.seat_candidates.update(conn, cand["id"], {"decision": "hired"}, viewer.source)
    team = models.teams.fetch(conn, seat["team_id"]) if seat.get("team_id") else None
    if team and pid not in (team.get("member_ids") or []):
        models.teams.update(conn, team["id"], {"member_ids": (team.get("member_ids") or []) + [pid]}, viewer.source)
    models.open_seats.update(conn, seat_id, {"status": "filled", "person_id": pid, "onboarding_id": ob["id"], "filled_on": today().isoformat()}, viewer.source)
    return {"person_id": pid, "onboarding_id": ob["id"]}


def seats_due(conn) -> list[dict]:
    """For Today: filled seats past day 90 with no note yet on which risks turned out real."""
    out = []
    for s in models.open_seats.fetch_all(conn, "status = 'filled' AND (lessons IS NULL OR lessons = '') AND onboarding_id IS NOT NULL"):
        ob = models.onboardings.fetch(conn, s["onboarding_id"])
        if ob and ob.get("start_date") and (date.today() - date.fromisoformat(ob["start_date"])).days + 1 >= 90:
            out.append({"id": s["id"], "title": s["title"]})
    return out


# ---- the development grid ----


@router.get("/api/people/{person_id}/development-grid", dependencies=[Depends(no_judgments)])
def development_grid(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    if not models.people.fetch(conn, person_id):
        raise HTTPException(404, "No such person.")
    entries = models.career_entries.fetch_all(conn, "person_id = ?", (person_id,))
    functions = list(models.CAREER_FUNCTIONS) + sorted({e["function"] for e in entries if e.get("function") and e["function"] not in models.CAREER_FUNCTIONS})
    grid = {f: {s: [] for s in models.SITUATION_KINDS} for f in functions}
    for n, e in enumerate(entries, 1):
        if e.get("function") in grid and e.get("situation") in models.SITUATION_KINDS:
            grid[e["function"]][e["situation"]].append({"n": n, "id": e["id"], "title": e["title"], "kind": e["kind"]})
    used_s = {e.get("situation") for e in entries}
    return {"entries": entries, "functions": functions, "situations": list(models.SITUATION_KINDS), "grid": grid,
            "blank_situations": [s for s in models.SITUATION_KINDS if s not in used_s] if entries else []}


@router.get("/api/me/person")
def my_person(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    from .people_crm import me_id
    return {"person_id": me_id(conn)}


# ---- the common core kit ----

PLAYBOOK = """# How we handle transitions

Everyone joining, moving or stepping up uses the same few ideas, so conversations about getting up to speed are quick and honest.

## The situation
Name what you've inherited: a start-up, a turnaround, accelerated growth, a realignment or sustaining success. Most roles are a mix. Each calls for a different approach.

## What to learn
What you need to learn (technical, cultural and political), from whom, and how fast. Write it down as a learning plan.

## Five conversations with your manager
The situation, expectations, how you'll work together, the resources you need, and how you're developing. Have them early and return to them.

## Early wins
A few wins that build credibility and serve the bigger goals, achieved in the way you want the team to work.

## Alliances
Who you need, inside and outside the team, and what each needs from you.

## Support
Every new person gets a 30/60/90 plan, a buddy, introductions to the people who'll shape their success, and check-ins at days 7, 30, 60 and 90. Nobody is left to sink or swim.
"""

TEMPLATE = """# 90-day plan: [Name], [Role]

**Start date:** [Date] · **Type of transition:** [new hire / contractor / move between teams / promotion / lateral move]

## The situation
[Start-up / turnaround / accelerated growth / realignment / sustaining success, and why]

## Days 1 to 30: learn
- What I need to learn: [Placeholder]
- Who I'll learn from: [Placeholder]
- Conversations with my manager: situation, expectations, working style

## Days 31 to 60: early wins
- Early win: [Placeholder], serving [goal]
- Relationships to build: [Placeholder]

## Days 61 to 90: build momentum
- [Placeholder]

## Support
- Buddy: [Name] · Mentor or culture guide: [Name] · HR contact: [Name]
- Check-ins: day 7, 30, 60, 90
"""


@router.get("/api/transition-kit")
def transition_kit(viewer: Viewer = Depends(get_viewer)):
    return {"playbook": PLAYBOOK, "template": TEMPLATE}


@router.post("/api/transition-kit/export")
def export_kit(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    which = body.get("which") if body.get("which") in ("playbook", "template") else "playbook"
    md = PLAYBOOK if which == "playbook" else TEMPLATE
    log_export(conn, f"transition-kit:{which}", "Transition playbook" if which == "playbook" else "90-day plan template", [{"markdown": md}], viewer.source)
    return {"markdown": md}
