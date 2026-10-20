"""Managing yourself through a transition, and helping your people manage themselves.

For you: a check against the eight core challenges of a transition, a self-check for four patterns transitions tend
to bring out, personal disciplines, and a short end-of-day and end-of-week review. For each of your people: what
they choose to tell you about how they're managing, with their consent recorded, and a summary for HR that holds
only what they agreed to share. All of it is private: never presented, packed, read by a token or sent to a cloud
model.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

# One question per stage of the transition, in plain words, each with where to work on it.
CORE_CHALLENGES = [
    ("prepare", "Prepare yourself", "Have I let go of my last role and taken on the mindset this one needs?", "/me", "new-role-mindset"),
    ("learn", "Accelerate your learning", "Do I know what I need to learn, from whom, and how to learn it faster?", "/listening", "learn-fast"),
    ("situation", "Match strategy to situation", "Have I named the kind of situation I'm in, and what it means I should and shouldn't do?", "/first90", "read-the-situation"),
    ("negotiate", "Negotiate success", "Is the relationship with my manager working: expectations clear and resources agreed?", "/first90", "your-manager"),
    ("wins", "Secure early wins", "Is my time going to the few priorities that build momentum toward the bigger goals?", "/plans", "early-wins"),
    ("alignment", "Achieve alignment", "Am I finding and fixing what's out of step between direction, structure, processes and skills?", "/alignment", "org-as-a-system"),
    ("team", "Build your team", "Am I assessing and shaping the team to fit what we need to achieve?", "/first90", "building-the-team"),
    ("alliances", "Create alliances", "Am I building support inside and outside, so I'm not pushing everything uphill alone?", "/alliances", "building-alliances"),
]
CHECK_DAYS = (30, 60, 90)

# Four patterns a transition tends to amplify.
SYNDROMES = [
    ("boundaries", "Undefended boundaries", "Saying yes to everything; people bring you more and respect your time less.",
     "Decide what you will and won't take on, write it down, and hold it."),
    ("brittleness", "Brittleness", "Holding to an early call that isn't working; only one right way to reach a goal.",
     "Be firm on outcomes and flexible on means. Make early calls reversible, and say so when you change your mind."),
    ("isolation", "Isolation", "Relying on a few people or official reports; bad news reaches you late or not at all.",
     "Widen who you hear from, ask what you're not hearing, and thank people who bring bad news."),
    ("avoidance", "Work avoidance", "Staying busy with other work so a hard call can wait.",
     "Name the hard calls, give each a date, and make one this week."),
]

# The six disciplines the book suggests, in plain words. You can add your own.
BUILTIN_DISCIPLINES = [
    ("plan", "Plan to plan", "Ten minutes at the end of each day and week: planned against done, and what matters next."),
    ("important", "Focus on the important", "A protected block most days for the work that matters, with notifications off."),
    ("defer", "Defer commitment", "No yes on the spot: \"let me think about it and get back to you by [day]\"."),
    ("balcony", "Go to the balcony", "In a heated moment, step back, take the wide view, then act."),
    ("check_in", "Check in with yourself", "A regular, honest look at how you're reacting, turned into one action."),
    ("quit", "Know when to quit", "Stop at the point of diminishing returns and take a real break."),
]
SUPPORT_SYNDROMES = [k for k, *_ in SYNDROMES]

# Your working base in the first week or two, so the basics don't drain attention from the work.
WORKING_BASE = [
    ("access", "Device, accounts and access working: email, chat, the tools the team uses"),
    ("place", "A place to work set up, wherever you'll work from"),
    ("calendar", "Calendar shaped the way you want: one-on-ones, focus time, your review rhythm"),
    ("routines", "Daily and weekly routines in place: end-of-day review, a focus block"),
    ("support", "Expectations agreed with anyone who supports you directly"),
    ("stopgaps", "Stopgaps for anything that isn't ready yet, so nothing waits on it"),
]
BASE_KEY = "self.working_base"


def _base(conn) -> dict:
    import json
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (BASE_KEY,)).fetchone()
    return json.loads(row["value"]) if row else {}


def day_of_role(conn) -> int | None:
    from .coaching import _day_of_role
    return _day_of_role(conn)


def _scale(v, name: str):
    if v in (None, ""):
        return None
    try:
        v = int(v)
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, f"{name} is a number from 1 to 5.") from exc
    if not 1 <= v <= 5:
        raise HTTPException(400, f"{name} is a number from 1 to 5.")
    return v


def challenge_result(scores: dict) -> dict:
    rated = {k: v for k, v in (scores or {}).items() if v}
    low = min(rated.values()) if rated else None
    return {"weakest": [k for k, v in rated.items() if v == low and low <= 3] if rated else [], "average": round(sum(rated.values()) / len(rated), 1) if rated else None}


def reflection_insight(conn) -> dict:
    """The dip three to six months in, and the signs of going over the top of the stress curve."""
    day = day_of_role(conn)
    entries = models.reflections.fetch_all(conn)[:6]
    over = None
    loads = [e["load"] for e in entries if e.get("load")]
    energy = [e["energy"] for e in entries if e.get("energy")]
    if len(loads) >= 2 and len(energy) >= 2 and loads[0] >= 4 and loads[0] > loads[-1] and energy[0] < energy[-1]:
        over = "Load is rising while energy falls. That's the over-the-top side of the stress curve: drop or defer something, and protect a real break."
    return {"day": day, "in_dip": bool(day and 90 <= day <= 180), "dip_start": 90, "dip_end": 180, "over_the_top": over}


@router.get("/api/self", dependencies=[Depends(no_judgments)])
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    t = today()
    checks = models.core_challenge_checks.fetch_all(conn)
    synd = models.syndrome_checks.fetch_all(conn)
    discs = models.disciplines.fetch_all(conn)
    week_start = (t - timedelta(days=t.weekday())).isoformat()
    reviews = models.day_reviews.fetch_all(conn, "date >= ?", ((t - timedelta(days=13)).isoformat(),))
    return {
        "day": day_of_role(conn),
        "challenges": [{"key": k, "chapter": c, "question": q, "path": p, "guide": g} for k, c, q, p, g in CORE_CHALLENGES],
        "checks": [{**c, **challenge_result(c.get("scores"))} for c in checks],
        "syndromes": [{"key": k, "name": n, "signs": s, "counter": c} for k, n, s, c in SYNDROMES],
        "syndrome_checks": synd,
        "disciplines": discs,
        "builtin_disciplines": [{"key": k, "name": n, "success": s} for k, n, s in BUILTIN_DISCIPLINES],
        "today_review": next((r for r in reviews if r["date"] == t.isoformat() and r["kind"] == "day"), None),
        "week_review": next((r for r in reviews if r["date"] >= week_start and r["kind"] == "week"), None),
        "recent_reviews": reviews,
        "insight": reflection_insight(conn),
        "working_base": [{"key": k, "label": l, "done_on": _base(conn).get(k)} for k, l in WORKING_BASE],
    }


@router.put("/api/self/working-base")
def save_base(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Tick off your working base: {key: true|false}."""
    import json
    require_write(viewer)
    done = _base(conn)
    for k, _ in WORKING_BASE:
        if k in body:
            if body[k]:
                done.setdefault(k, today().isoformat())
            else:
                done.pop(k, None)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (BASE_KEY, json.dumps(done)))
    return {"done": done}


@router.post("/api/self/challenges", status_code=201)
def save_challenges(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {k for k, *_ in CORE_CHALLENGES}
    scores = {k: _scale(v, "Each rating") for k, v in (body.get("scores") or {}).items() if k in keys}
    if not any(scores.values()):
        raise HTTPException(400, "Rate at least one challenge from 1 to 5.")
    notes = {k: str(v)[:1000] for k, v in (body.get("notes") or {}).items() if k in keys and v}
    rec = models.core_challenge_checks.create(conn, {"date": body.get("date") or today().isoformat(), "scores": scores, "notes": notes}, viewer.source)
    return {**rec, **challenge_result(scores)}


@router.post("/api/self/syndromes", status_code=201)
def save_syndromes(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {k for k, *_ in SYNDROMES}
    ratings = {k: _scale(v, "Each rating") for k, v in (body.get("ratings") or {}).items() if k in keys}
    if not any(ratings.values()):
        raise HTTPException(400, "Rate at least one pattern from 1 (not at all) to 5 (a lot).")
    evidence = {k: str(v)[:1000] for k, v in (body.get("evidence") or {}).items() if k in keys and v}
    return models.syndrome_checks.create(conn, {"date": body.get("date") or today().isoformat(), "ratings": ratings, "evidence": evidence,
                                                "asked": body.get("asked") or None, "notes": body.get("notes") or None}, viewer.source)


@router.post("/api/self/disciplines/starter", status_code=201)
def add_builtin_disciplines(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Add the six suggested disciplines you don't have yet. Untick the ones you don't need."""
    require_write(viewer)
    have = {d["builtin"] for d in models.disciplines.fetch_all(conn) if d.get("builtin")}
    added = []
    for pos, (k, name, success) in enumerate(BUILTIN_DISCIPLINES):
        if k not in have:
            added.append(models.disciplines.create(conn, {"name": name, "success": success, "builtin": k, "position": pos}, viewer.source))
    return {"added": len(added)}


@router.put("/api/self/review")
def save_review(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The end-of-day (or end-of-week) review: one per day, saved again to update it."""
    require_write(viewer)
    kind = body.get("kind") or "day"
    if kind not in ("day", "week"):
        raise HTTPException(400, "The review is for a day or a week.")
    when = body.get("date") or today().isoformat()
    data = {k: body.get(k) for k in ("planned", "done", "notes") if k in body}
    if "tomorrow" in body:
        data["tomorrow"] = [str(x).strip() for x in body.get("tomorrow") or [] if str(x).strip()][:10]
    if "kept_ids" in body:
        known = {d["id"] for d in models.disciplines.fetch_all(conn)}
        data["kept_ids"] = [i for i in body.get("kept_ids") or [] if i in known]
    row = conn.execute("SELECT id FROM day_reviews WHERE date = ? AND kind = ?", (when, kind)).fetchone()
    if row:
        return models.day_reviews.update(conn, row["id"], data, viewer.source)
    return models.day_reviews.create(conn, {"date": when, "kind": kind, **data}, viewer.source)


def self_due(conn) -> dict:
    """For Today: the review, a core-challenges check near day 30, 60 and 90, a monthly self-check, and asks to answer."""
    t = today()
    day = day_of_role(conn)
    left = [l for k, l in WORKING_BASE if k not in _base(conn)]
    out = {"working_base_left": len(left) if day and day <= 14 else 0, "review_done": bool(conn.execute("SELECT 1 FROM day_reviews WHERE date = ? AND kind = 'day'", (t.isoformat(),)).fetchone())}
    week_start = (t - timedelta(days=t.weekday())).isoformat()
    out["week_review_due"] = t.weekday() >= 4 and not conn.execute("SELECT 1 FROM day_reviews WHERE date >= ? AND kind = 'week'", (week_start,)).fetchone()
    out["challenge_check_due"] = None
    if day:
        for d in CHECK_DAYS:
            if d - 3 <= day <= d + 10:
                start = (t - timedelta(days=day - (d - 3))).isoformat()
                if not conn.execute("SELECT 1 FROM core_challenge_checks WHERE date >= ?", (start,)).fetchone():
                    out["challenge_check_due"] = d
    last = conn.execute("SELECT MAX(date) AS d FROM syndrome_checks").fetchone()["d"]
    out["self_check_due"] = bool(day and day >= 14 and (not last or date.fromisoformat(last) <= t - timedelta(days=30)))
    out["disciplines"] = [{"id": d["id"], "name": d["name"]} for d in models.disciplines.fetch_all(conn, "active = 1")]
    rows = models.day_reviews.fetch_all(conn, "date = ? AND kind = 'day'", (t.isoformat(),))
    out["review"] = rows[0] if rows else None
    week = (t + timedelta(days=7)).isoformat()
    out["asks"] = [{"id": x["id"], "title": x["title"], "requested_by": x.get("requested_by"), "answer_by": x["answer_by"], "late": x["answer_by"] < t.isoformat()}
                   for x in models.tasks.fetch_all(conn, "status = 'considering' AND answer_by IS NOT NULL AND answer_by <= ?", (week,))]
    return out


# ---- helping your people manage themselves ----


def _person(conn, person_id: int) -> dict:
    p = models.people.fetch(conn, person_id)
    if not p:
        raise HTTPException(404, "No such person.")
    return p


def _profile(conn, person_id: int) -> dict | None:
    rows = models.support_profiles.fetch_all(conn, "person_id = ?", (person_id,))
    return rows[0] if rows else None


@router.get("/api/people/{person_id}/support", dependencies=[Depends(no_judgments)])
def support(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    _person(conn, person_id)
    checkins = models.support_checkins.fetch_all(conn, "person_id = ?", (person_id,))
    return {"profile": _profile(conn, person_id), "checkins": checkins,
            "syndromes": [{"key": k, "name": n, "signs": s} for k, n, s, _ in SYNDROMES],
            "disciplines": [n for _, n, _ in BUILTIN_DISCIPLINES],
            "trend": [{"date": c["date"], "energy": c["energy"], "load": c["load"], "in_control": c["in_control"]} for c in reversed(checkins[:12])]}


@router.put("/api/people/{person_id}/support")
def save_profile(person_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Their consent and how they'd like to be supported. Consent to share with HR is theirs to give and to withdraw."""
    require_write(viewer)
    _person(conn, person_id)
    allowed = ("consent_manager_on", "consent_hr", "consent_hr_on", "how_to_support", "supporter_ids", "notes")
    data = {k: body[k] for k in allowed if k in body}
    if data.get("consent_hr") and not data.get("consent_hr_on"):
        data["consent_hr_on"] = today().isoformat()
    if "consent_hr" in data and not data["consent_hr"]:
        data["consent_hr_on"] = None
    prof = _profile(conn, person_id)
    if prof:
        return models.support_profiles.update(conn, prof["id"], data, viewer.source)
    return models.support_profiles.create(conn, {"person_id": person_id, **data}, viewer.source)


@router.post("/api/people/{person_id}/support/checkins", status_code=201)
def add_checkin(person_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _person(conn, person_id)
    prof = _profile(conn, person_id)
    if not prof or not prof.get("consent_manager_on"):
        raise HTTPException(409, "Record that they've agreed to share this with you first. It's their information.")
    data = {"person_id": person_id, "date": body.get("date") or today().isoformat()}
    for k in ("energy", "load", "in_control"):
        data[k] = _scale(body.get(k), k.replace("_", " ").capitalize())
    for k in ("going_well", "hard", "support_wanted"):
        data[k] = (body.get(k) or None) and str(body[k])[:2000]
    data["syndromes"] = [s for s in body.get("syndromes") or [] if s in SUPPORT_SYNDROMES]
    data["disciplines"] = [str(s)[:120] for s in body.get("disciplines") or []][:10]
    data["share_hr"] = bool(body.get("share_hr")) and bool(prof.get("consent_hr"))
    return models.support_checkins.create(conn, data, viewer.source)


def hr_summary(conn, person_id: int) -> dict:
    p = _person(conn, person_id)
    prof = _profile(conn, person_id)
    if not prof or not prof.get("consent_hr"):
        raise HTTPException(409, f"{p['name']} hasn't agreed to share this with HR.")
    shared = [c for c in models.support_checkins.fetch_all(conn, "person_id = ? AND share_hr = 1", (person_id,))]
    names = {s: n for s, n, *_ in SYNDROMES}
    lines = [f"# Support summary: {p['name']}", "",
             f"Shared with HR with {p['name']}'s agreement, given {prof['consent_hr_on'] or 'on record'}. It holds only the check-ins they chose to share.", ""]
    if prof.get("how_to_support"):
        lines += ["## How they'd like to be supported", "", prof["how_to_support"], ""]
    if not shared:
        lines += ["No check-ins marked to share yet."]
    for c in reversed(shared):
        lines += [f"## {c['date']}", ""]
        scores = [f"{label} {c[k]}/5" for k, label in (("energy", "energy"), ("load", "load"), ("in_control", "in control")) if c.get(k)]
        if scores:
            lines += ["- " + ", ".join(scores)]
        for k, label in (("going_well", "Going well"), ("hard", "Hard right now"), ("support_wanted", "Support that would help")):
            if c.get(k):
                lines += [f"- **{label}:** {c[k]}"]
        if c.get("syndromes"):
            lines += ["- **Patterns they recognize:** " + ", ".join(names.get(s, s) for s in c["syndromes"])]
        if c.get("disciplines"):
            lines += ["- **Working on:** " + ", ".join(c["disciplines"])]
        lines += [""]
    return {"title": f"Support summary: {p['name']}", "markdown": "\n".join(lines).rstrip() + "\n", "checkins": len(shared)}


@router.post("/api/people/{person_id}/support/hr-summary", dependencies=[Depends(no_judgments)])
def export_hr_summary(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A summary for HR of only what the person agreed to share. Signed in directly, not while presenting; logged."""
    require_write(viewer)
    if viewer.floor != Level.PRIVATE:
        raise HTTPException(403, "Not available while presenting.")
    out = hr_summary(conn, person_id)
    log_export(conn, "support:hr", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out
