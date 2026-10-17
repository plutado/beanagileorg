"""Culture and trust: the standards you hold yourself to, what you notice, a trust pulse, team agreements, and a
brief of what you were brought in to do, so the soft side of the job stays in view next to the delivery work.

Everything is private except team agreements, which the team makes together and can see on screen.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
BRIEF_KEY = "culture.role_brief"
PULSE_DAYS_KEY = "culture.pulse_days"
UNADDRESSED_DAYS = 7
PULSE_DIMENSIONS = [
    ("safety", "Safe to speak up and admit mistakes"),
    ("clarity", "Clear priorities and process"),
    ("trust", "Trust in leadership"),
    ("unity", "One team, not separate camps"),
    ("collaboration", "Working well together"),
    ("workload", "Sustainable workload"),
    ("recognition", "Good work is noticed"),
]
# Generic starting points, meant to be rewritten in your own words.
STARTER_STANDARDS = [
    ("Do what I say I'll do, and say so early when I can't.", "Trust is built from small promises kept, especially with a team that has seen a lot of change."),
    ("Be the same person in every room. What I say about someone, I'd say to them.", "Consistency is what makes a leader safe to be honest with."),
    ("Hold a high bar, explain why it matters, and help people reach it.", "High standards without support feel like judgment; support without standards drifts."),
    ("Name harmful behavior when I see it: privately first, and every time.", "What a leader tolerates becomes the culture."),
    ("No surprises. Bad news travels fast and comes with a plan.", "People trust leaders who tell them the truth early."),
    ("Make room for quiet voices before the loudest one settles it.", "The best idea in the room is often the one nobody pushed."),
    ("Replace chaos with just enough process, and drop process that doesn't help.", "Structure should make the work calmer, not heavier."),
    ("Disagree openly, then commit fully.", "Healthy conflict needs a clear way to end."),
]
STARTER_AGREEMENTS = [
    ("disagreement", "We disagree about ideas, not people."),
    ("disagreement", "Everyone gets heard before we decide; the decider says so out loud."),
    ("meetings", "Every meeting has a purpose and ends with a decision or a next step."),
    ("communication", "We raise blockers the same day, in the open."),
    ("code review", "Review comments explain why, and suggest rather than command."),
    ("quality", "Mistakes are discussed to learn, not to blame."),
    ("working together", "We ask for help early and offer it freely."),
]
EMPTY_BRIEF = {"focus": [], "must_haves": [], "situation": "", "keep": []}


def _today() -> date:
    return date.today()


def _setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def _put(conn, key, value) -> None:
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))


def todays_standard(conn) -> dict | None:
    active = models.standards.fetch_all(conn, "active = 1")
    return active[_today().toordinal() % len(active)] if active else None


def _unaddressed(conn) -> list[dict]:
    cutoff = (_today() - timedelta(days=UNADDRESSED_DAYS)).isoformat()
    return models.culture_observations.fetch_all(conn, "scope = 'my team' AND kind = 'concern' AND status != 'addressed' AND action IN ('not yet') AND date <= ?", (cutoff,))


@router.post("/api/culture/standards/starter", status_code=201)
def starter_standards(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]:
        raise HTTPException(409, "You already have standards. Edit them instead.")
    for pos, (text, why) in enumerate(STARTER_STANDARDS):
        models.standards.create(conn, {"text": text, "why": why, "position": pos}, viewer.source)
    return {"standards": len(STARTER_STANDARDS)}


@router.post("/api/culture/agreements/starter", status_code=201)
def starter_agreements(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Suggested agreements, loaded as proposals for the team to change, cut or agree."""
    require_write(viewer)
    team = body.get("team_id")
    if conn.execute("SELECT COUNT(*) FROM team_agreements WHERE team_id IS ?", (team,)).fetchone()[0]:
        raise HTTPException(409, "There are already agreements for this team.")
    for pos, (area, text) in enumerate(STARTER_AGREEMENTS):
        models.team_agreements.create(conn, {"text": text, "area": area, "team_id": team, "position": pos}, viewer.source)
    return {"agreements": len(STARTER_AGREEMENTS)}


@router.post("/api/culture/self-check", status_code=201)
def self_check(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Rate yourself against each standard (1 to 5) in one go, with an optional note on each."""
    require_write(viewer)
    when = body.get("date") or _today().isoformat()
    saved = 0
    for r in body.get("ratings", []):
        if isinstance(r.get("rating"), int) and 1 <= r["rating"] <= 5 and models.standards.fetch(conn, r.get("standard_id") or 0):
            models.standard_checks.create(conn, {"date": when, "standard_id": r["standard_id"], "rating": r["rating"], "note": r.get("note") or None}, viewer.source)
            saved += 1
    if not saved:
        raise HTTPException(400, "Rate at least one standard from 1 to 5.")
    return {"saved": saved, "date": when}


@router.get("/api/culture/role-brief")
def get_brief(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return EMPTY_BRIEF
    return {**EMPTY_BRIEF, **_setting(conn, BRIEF_KEY, {})}


@router.put("/api/culture/role-brief")
def put_brief(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    clean = lambda v: [x.strip() for x in v if isinstance(x, str) and x.strip()] if isinstance(v, list) else []
    brief = {"focus": clean(body.get("focus")), "must_haves": clean(body.get("must_haves")), "keep": clean(body.get("keep")), "situation": (body.get("situation") or "").strip()}
    _put(conn, BRIEF_KEY, brief)
    return brief


@router.put("/api/culture/settings")
def put_settings(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    days = body.get("pulse_days")
    if not isinstance(days, int) or not 1 <= days <= 120:
        raise HTTPException(400, "The pulse cadence is a number of days from 1 to 120.")
    _put(conn, PULSE_DAYS_KEY, days)
    return {"pulse_days": days}


@router.get("/api/culture/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    agreements = models.team_agreements.visible_all(models.team_agreements.fetch_all(conn), viewer)
    out = {"dimensions": [{"key": k, "label": l} for k, l in PULSE_DIMENSIONS], "agreements": agreements}
    if viewer.floor != Level.PRIVATE:
        return {**out, "private": False}
    today = _today()
    pulse_days = _setting(conn, PULSE_DAYS_KEY, 14)
    pulses = models.trust_pulses.fetch_all(conn)
    mine = [p for p in pulses if p["source"] == "my read"]
    last = mine[0] if mine else None
    standards = models.standards.fetch_all(conn)
    checks = models.standard_checks.fetch_all(conn)
    latest_rating = {}
    for c in checks:
        latest_rating.setdefault(c["standard_id"], c)
    weeks = {}
    for c in checks:
        wk = date.fromisoformat(c["date"]) - timedelta(days=date.fromisoformat(c["date"]).weekday())
        weeks.setdefault(wk.isoformat(), []).append(c["rating"])
    observations = models.culture_observations.fetch_all(conn)
    open_obs = [o for o in observations if o["status"] != "addressed"]
    return {
        **out, "private": True,
        "today": todays_standard(conn),
        "standards": [{**s, "last": latest_rating.get(s["id"])} for s in standards],
        "self_check_trend": [{"week": w, "average": round(sum(r) / len(r), 1)} for w, r in sorted(weeks.items())[-8:]],
        "last_self_check": checks[0]["date"] if checks else None,
        "pulse_days": pulse_days,
        "pulse_due": last is None or (today - date.fromisoformat(last["date"])).days >= pulse_days,
        "pulses": pulses[:12],
        "open": {"my team": sum(1 for o in open_obs if o["scope"] == "my team" and o["kind"] == "concern"),
                 "organization": sum(1 for o in open_obs if o["scope"] == "organization" and o["kind"] == "concern"),
                 "positive": sum(1 for o in observations if o["kind"] == "positive" and o["date"] >= (today - timedelta(days=30)).isoformat())},
        "unaddressed": _unaddressed(conn),
        "follow_ups": [o for o in open_obs if o["follow_up"] and o["follow_up"] <= (today + timedelta(days=7)).isoformat()],
        "agreements_due": [a for a in agreements if a["status"] == "agreed" and a.get("review_on") and a["review_on"] <= today.isoformat()],
        "brief": {**EMPTY_BRIEF, **_setting(conn, BRIEF_KEY, {})},
    }


def culture_due(conn) -> dict:
    """For Today: one of your standards to keep in mind, harmful behavior left unaddressed, follow-ups, and a pulse reminder."""
    std = todays_standard(conn)
    mine = models.trust_pulses.fetch_all(conn, "source = 'my read'")
    days = _setting(conn, PULSE_DAYS_KEY, 14)
    week = (_today() + timedelta(days=7)).isoformat()
    return {
        "standard": {"id": std["id"], "text": std["text"]} if std else None,
        "unaddressed": [{"id": o["id"], "title": o["title"], "date": o["date"]} for o in _unaddressed(conn)],
        "follow_ups": [{"id": o["id"], "title": o["title"], "follow_up": o["follow_up"]} for o in models.culture_observations.fetch_all(conn, "status != 'addressed' AND follow_up IS NOT NULL AND follow_up <= ?", (week,))],
        "pulse_due": bool(mine) and (_today() - date.fromisoformat(mine[0]["date"])).days >= days,
    }
