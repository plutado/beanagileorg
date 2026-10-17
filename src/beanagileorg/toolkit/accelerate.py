"""Getting up to speed on purpose: a learning agenda, a diagnosis of each area's situation, the conversations
that set you up with your manager, the managers you mentor, and a read on momentum.

The starter questions, situation descriptions and conversation prompts are original to beanagileorg, written
for a new engineering manager. The ideas behind them are common to the transition literature (see Coaching
for further reading); nothing is quoted from a book.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .people_crm import me_id
from .routes import START_DATE_KEY, require_write, today

router = APIRouter()

STARTER_QUESTIONS = [
    ("past", "What has been tried before to bring in Scrum or a QA process, and what happened?", 21),
    ("past", "Why have people left the team, in their words and in their managers'?", 21),
    ("past", "What did the team's previous managers do that people valued?", 30),
    ("present", "Where does work get stuck between a request and production?", 14),
    ("present", "What does a release look like today, from start to finish?", 14),
    ("present", "What does the team think is working, and what would they change first?", 21),
    ("future", "What is the business counting on this team for over the next year?", 30),
    ("future", "What would make this team's work much harder six months from now?", 45),
    ("people", "Who has influence beyond their title, on the team and around it?", 30),
    ("people", "Who is the go-to expert for each system, and what happens when they're away?", 21),
    ("technical", "Which parts of the platform are fragile, and why?", 30),
    ("technical", "How much testing and deployment is automated today?", 21),
    ("products and customers", "Which products and customers matter most to the business, and why?", 30),
    ("politics", "Where do stakeholders' priorities conflict, and who settles it?", 45),
    ("politics", "Which decisions are made formally, and which happen in hallways?", 45),
]

SITUATION_GUIDE = {
    "start-up": ("Something new is being built: a team, a product or a way of working. There's little to protect yet, and energy is high but unfocused.",
                 "Bring people, structure and a clear first goal quickly. Decide more yourself at first, then hand over as the team forms."),
    "turnaround": ("Something important is in trouble and people know it. Delay makes it worse.",
                   "Act early and visibly on the few things that matter most. Be direct about the problem, protect what still works, and show progress fast."),
    "accelerated growth": ("Things work, and demand is growing faster than the way of working can handle.",
                           "Add structure, process and people at the pace of growth, without losing what made it work."),
    "realignment": ("Things are drifting toward trouble, but many people don't see it yet, or don't want to.",
                    "Build a shared understanding of the problem before pushing solutions. Make the case with evidence, and enlist the people who already see it."),
    "sustaining success": ("Things are going well and the job is to keep them that way, and find the next step.",
                           "Learn deeply before changing anything. Protect what works, avoid needless disruption, and look for the next opportunity."),
}
STARTER_AREAS = ["The team", "Delivery and Agile practice", "Quality and releases", "The Salesforce platform", "MuleSoft and integrations", "Stakeholder relationships"]

BOSS_TOPICS = [
    ("The situation", "Bring your read of the situation (what's working, what isn't, what kind of situation it is) and test it against theirs. Ask for the history only they know: what's been tried, who matters, where the sensitivities are."),
    ("Expectations", "Propose what success looks like at 30, 60 and 90 days and six months, and how you'll report on it. Ask what must not go wrong."),
    ("Working style", "Propose a rhythm: how often you meet, what you'll send each week, what you'll handle yourself and what you'll bring to them. Ask what they want to hear about first."),
    ("Resources", "Bring what you have and what would let you go faster, as a recommendation with options and their trade-offs."),
    ("My development", "Say where you want to grow in this role and how they can help, including what you'll learn from their knowledge of the organization."),
    ("The 90-day plan", "Present the plan as your recommendation, invite changes, and agree it together. Give them a one-line version they can share upward."),
]


def _start(conn) -> date | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return date.fromisoformat(row["value"]) if row and row["value"] else None


def _due(start, n):
    return (start + timedelta(days=n - 1)).isoformat() if start and n else None


# ---- learning agenda ----


@router.post("/api/learning-questions/starter", status_code=201)
def learning_starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM learning_questions").fetchone()[0]:
        raise HTTPException(409, "You already have a learning agenda. Add to it instead.")
    for pos, (area, q, day) in enumerate(STARTER_QUESTIONS):
        models.learning_questions.create(conn, {"question": q, "area": area, "due_day": day, "position": pos}, viewer.source)
    return {"questions": len(STARTER_QUESTIONS)}


@router.get("/api/learning-questions/agenda")
def agenda(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    start, t = _start(conn), today().isoformat()
    names = {p["id"]: p["name"] for p in models.people.fetch_all(conn)}
    qs = models.learning_questions.fetch_all(conn)
    for q in qs:
        q["due"] = _due(start, q.get("due_day"))
        q["late"] = q["status"] == "open" and bool(q["due"]) and q["due"] < t
        q["ask_names"] = [names[i] for i in q.get("ask_ids") or [] if i in names]
    return {"questions": qs, "areas": list(models.LEARNING_AREAS),
            "counts": {s: sum(1 for q in qs if q["status"] == s) for s in models.LEARNING_STATUS}, "late": sum(1 for q in qs if q["late"])}


# ---- situation diagnosis ----


@router.get("/api/situations/guide")
def situation_guide(viewer: Viewer = Depends(get_viewer)):
    return {k: {"what": w, "approach": a} for k, (w, a) in SITUATION_GUIDE.items()}


@router.post("/api/situations/starter", status_code=201)
def situation_starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM situations").fetchone()[0]:
        raise HTTPException(409, "You've already started the diagnosis.")
    for pos, area in enumerate(STARTER_AREAS):
        models.situations.create(conn, {"area": area, "position": pos}, viewer.source)
    return {"areas": len(STARTER_AREAS)}


# ---- conversations with your manager, and agreeing the plan ----


@router.post("/api/boss-conversations/starter", status_code=201)
def boss_starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM boss_conversations").fetchone()[0]:
        raise HTTPException(409, "The conversations are already listed.")
    for pos, (topic, prompt) in enumerate(BOSS_TOPICS):
        models.boss_conversations.create(conn, {"topic": topic, "prompt": prompt, "position": pos}, viewer.source)
    return {"conversations": len(BOSS_TOPICS)}


@router.post("/api/plans/{plan_id}/agree")
def agree_plan(plan_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Record that a plan was agreed, and with whom (your manager by default)."""
    require_write(viewer)
    if not models.plans.fetch(conn, plan_id):
        raise HTTPException(404, "No such plan.")
    who = body.get("agreed_with_id")
    if who is None and me_id(conn):
        row = conn.execute("SELECT manager_id FROM people WHERE id = ?", (me_id(conn),)).fetchone()
        who = row["manager_id"] if row else None
    return models.plans.update(conn, plan_id, {"status": "agreed", "agreed_on": body.get("on") or today().isoformat(), "agreed_with_id": who}, viewer.source)


# ---- managers you mentor ----


@router.get("/api/mentoring/overview")
def mentoring(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        practices = models.mentored_practices.visible_all(models.mentored_practices.fetch_all(conn, "status = 'adopted'"), viewer)
        return {"hidden": True, "adopted": practices}
    sessions = models.mentoring_sessions.fetch_all(conn)
    practices = models.mentored_practices.fetch_all(conn)
    ids = sorted({s["person_id"] for s in sessions} | {p["person_id"] for p in practices})
    people = {p["id"]: p for p in models.people.fetch_all(conn)}
    out = []
    for pid in ids:
        p = people.get(pid)
        if not p:
            continue
        mine = [s for s in sessions if s["person_id"] == pid]
        pr = [x for x in practices if x["person_id"] == pid]
        nxt = min((s["next_on"] for s in mine if s.get("next_on")), default=None)
        out.append({"id": pid, "name": p["name"], "role": p.get("role"), "sessions": mine, "practices": pr, "last": mine[0]["date"] if mine else None,
                    "next_on": nxt, "adopted": sum(1 for x in pr if x["status"] == "adopted")})
    candidates = [{"id": p["id"], "name": p["name"]} for p in people.values() if p.get("relationship") in ("peer", "manager") and p["id"] not in ids and p.get("active", True)]
    return {"mentees": out, "candidates": candidates,
            "totals": {s: sum(1 for x in practices if x["status"] == s) for s in models.PRACTICE_STATUS}}


# ---- momentum ----


def momentum(conn) -> dict:
    """Signs that good things are happening: early wins landed, changes kept, wins logged, practices adopted, and the trust trend."""
    t = today()
    month = (t - timedelta(days=30)).isoformat()
    early = conn.execute("SELECT COUNT(*) AS n, SUM(status = 'done') AS done FROM plan_items WHERE early_win = 1 AND status != 'dropped'").fetchone()
    kept = conn.execute("SELECT COUNT(*) FROM team_changes WHERE status = 'adopted'").fetchone()[0]
    wins = conn.execute("SELECT COUNT(*) FROM work_log WHERE kind = 'win' AND date >= ?", (month,)).fetchone()[0]
    adopted = conn.execute("SELECT COUNT(*) FROM mentored_practices WHERE status = 'adopted'").fetchone()[0]
    pulses = [p for p in models.trust_pulses.fetch_all(conn, "source = 'my read'")][:2]
    avg = lambda p: round(sum(p["scores"].values()) / len(p["scores"]), 1) if p.get("scores") else None
    trend = {"now": avg(pulses[0]) if pulses else None, "before": avg(pulses[1]) if len(pulses) > 1 else None}
    return {"early_wins": {"done": early["done"] or 0, "total": early["n"]}, "changes_kept": kept, "wins_30": wins, "practices_adopted": adopted, "trust": trend}


def accelerate_due(conn) -> dict:
    """For Today: learning questions past their day, manager conversations not yet held three weeks in, and mentoring follow-ups."""
    t = today()
    start = _start(conn)
    day = (t - start).days + 1 if start else None
    late = [{"id": q["id"], "question": q["question"]} for q in models.learning_questions.fetch_all(conn, "status = 'open' AND due_day IS NOT NULL")
            if start and _due(start, q["due_day"]) < t.isoformat()]
    unheld = [c["topic"] for c in models.boss_conversations.fetch_all(conn, "held_on IS NULL")] if day and day >= 21 else []
    week = (t + timedelta(days=7)).isoformat()
    names = {p["id"]: p["name"] for p in models.people.fetch_all(conn)}
    latest = {}
    for s in models.mentoring_sessions.fetch_all(conn):  # newest first: only each person's latest session counts
        latest.setdefault(s["person_id"], s)
    follow = [{"person_id": s["person_id"], "name": names.get(s["person_id"]), "next_step": s.get("next_step"), "next_on": s["next_on"]}
              for s in latest.values() if s.get("next_on") and s["next_on"] <= week]
    return {"learning_late": late[:5], "learning_late_count": len(late), "boss_unheld": unheld, "mentoring": follow}
