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
    ("present", "How much Agile does the team actually practice? Which ceremonies happen, which artifacts exist (backlog, sprint goal, definition of done, board), and how disciplined is it?", 7),
    ("present", "Does an SDLC exist, and what shape is it: written down or tribal, followed or skipped under pressure, and where does it break?", 7),
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
    # Joining from outside: business orientation, stakeholder connection and cultural adaptation.
    ("business", "How does the company make money, and which products, customers and seasons matter most?", 14),
    ("business", "Which systems the team owns carry revenue or customer data, and what does it cost the business when they fail?", 14),
    ("business", "How does this team's work connect to the company's goals for this year?", 21),
    ("people", "Who could be my culture guides: one or two long-tenured colleagues willing to help me read how things really work?", 7),
    ("people", "Who do people actually go to for answers and before decisions, whatever the org chart says?", 30),
    ("culture", "What does the culture reward, what does it quietly discourage, and how are disagreements handled?", 30),
    ("business", "What are the company's brands and products? Use them as a customer, from the website to delivery, ideally before day one.", 7),
    ("business", "What is the operating model: how work, budget and decisions flow between the business, IT and this team?", 30),
    ("business", "When do annual planning and budgeting happen, and how does a team ask for people or tools?", 30),
    ("people", "When do performance reviews run, what form do they take, and how are ratings and pay decided?", 21),
    ("people", "What did the previous manager leave for each person: past reviews, goals, and promises made?", 14),
    ("people", "How do job levels, promotions and contractor conversions work here?", 30),
    ("politics", "Who besides my manager influences how my work is judged, and what do they expect from me?", 21),
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
    ("Expectations", "Propose what success looks like at 30, 60 and 90 days and six months, and how you'll report on it. Ask what must not go wrong. In your first week, recheck what was said while you were being hired: the scope of the role, how much room you have to change things, and the support you'll get."),
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


# ---- problem preferences ----
# Five areas of the business against three kinds of problem. The idea of rating your interest in each, to find likely
# blind spots, comes from The First 90 Days; the cells here are written for engineering leaders.

PREF_KINDS = [
    ("technical", "Technical", "Strategy, markets, technology and process"),
    ("political", "Political", "Power, influence and relationships"),
    ("cultural", "Cultural", "Values, norms and shared assumptions"),
]
PREF_AREAS = [
    ("people", "People", ["Career levels, reviews and how people are rewarded", "Team morale, especially through change", "Fairness in who gets opportunities and recognition"]),
    ("finance", "Finance", ["Budgets, licences and vendor costs", "Winning funding and headcount", "A habit of spending money wisely"]),
    ("product", "Product and customers", ["Product direction and the roadmap", "Relationships with customers and stakeholders", "Putting customers first across the team"]),
    ("delivery", "Delivery and operations", ["Quality, releases and reliability", "Vendors, partners and other teams you depend on", "A habit of continuous improvement"]),
    ("engineering", "Engineering", ["Architecture, tooling and delivery pipelines", "How engineering, product and the business work together", "Collaboration across teams"]),
]
PREF_GUIDES = {
    "technical": ["learn-fast", "metrics-without-blame"], "political": ["peer-relationships", "leading-upward"],
    "cultural": ["culture-of-trust", "joining-from-outside"], "people": ["one-on-ones", "feedback"], "finance": ["tech-debt-case"],
    "product": ["saying-no-to-scope", "honest-status"], "delivery": ["quality-culture", "vendor-partnerships"],
    "engineering": ["integrating-teams", "scrum-of-scrums"],
}


def _guides(keys):
    from beanagileorg.core.coaching import guide

    return [{"slug": s, "title": guide(s)["title"]} for k in keys for s in PREF_GUIDES.get(k, []) if guide(s)]


def preference_result(scores: dict) -> dict:
    """Row and column totals, and the ones noticeably lower than the strongest: possible blind spots."""
    val = lambda a, k: int((scores or {}).get(f"{a}.{k}") or 0)
    cols = {k: sum(val(a, k) for a, _, _ in PREF_AREAS) for k, _, _ in PREF_KINDS}
    rows = {a: sum(val(a, k) for k, _, _ in PREF_KINDS) for a, _, _ in PREF_AREAS}
    complete = all(val(a, k) for a, _, _ in PREF_AREAS for k, _, _ in PREF_KINDS)
    low_cols = [k for k, v in cols.items() if complete and v <= 0.8 * max(cols.values())]
    low_rows = [a for a, v in rows.items() if complete and v <= 0.75 * max(rows.values())]
    return {"columns": cols, "rows": rows, "complete": complete, "blind_spots": {"kinds": low_cols, "areas": low_rows},
            "guides": _guides(low_cols + low_rows)}


@router.get("/api/preferences")
def preferences(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    past = models.preference_assessments.fetch_all(conn)
    return {"kinds": [{"key": k, "label": l, "about": d} for k, l, d in PREF_KINDS],
            "areas": [{"key": a, "label": l, "cells": c} for a, l, c in PREF_AREAS],
            "assessments": [{**p, **preference_result(p.get("scores") or {})} for p in past]}


@router.post("/api/preferences", status_code=201)
def save_preferences(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {f"{a}.{k}" for a, _, _ in PREF_AREAS for k, _, _ in PREF_KINDS}
    scores = {k: int(v) for k, v in (body.get("scores") or {}).items() if k in keys and v not in (None, "")}
    if any(not 1 <= v <= 10 for v in scores.values()):
        raise HTTPException(400, "Rate each one from 1 to 10.")
    rec = models.preference_assessments.create(conn, {"date": body.get("date") or today().isoformat(), "scores": scores, "notes": body.get("notes"), "hammer": body.get("hammer")}, viewer.source)
    return {**rec, **preference_result(scores)}
