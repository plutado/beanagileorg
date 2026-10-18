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
    # How did we get here? Ask before changing anything.
    ("past", "How has the team performed over the last year or two, and how was that measured?", 21),
    ("past", "What happened when goals or commitments were missed?", 21),
    ("past", "What has the team asked for, more than once, and never received?", 14),
    ("present", "Is the stated strategy the one the organization is actually pursuing?", 45),
    ("present", "What lurking surprises or political missteps could knock me off track?", 21),
    ("future", "Where are the pockets of excellence I can build on?", 30),
    ("culture", "Which parts of the culture should be kept, and which need to change?", 60),
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
    return {"questions": qs, "areas": list(models.LEARNING_AREAS), "balance": learning_balance(qs), "sources": insight_sources(conn),
            "counts": {s: sum(1 for q in qs if q["status"] == s) for s in models.LEARNING_STATUS}, "late": sum(1 for q in qs if q["late"])}


LEARNING_DOMAINS = {"technical": ("technical", "products and customers", "business"), "people": ("people",), "culture": ("culture",), "politics": ("politics",)}


def learning_balance(qs: list[dict]) -> dict:
    """How the open questions split across technical, people, culture and politics. It's easy to learn the technical
    side and shortchange culture and politics, so say so when that happens."""
    open_qs = [q for q in qs if q["status"] == "open"]
    counts = {d: sum(1 for q in open_qs if q["area"] in areas) for d, areas in LEARNING_DOMAINS.items()}
    tagged = sum(counts.values())
    soft = counts["culture"] + counts["politics"]
    return {"counts": counts, "untagged": len(open_qs) - tagged,
            "technical_heavy": tagged >= 6 and counts["technical"] > 0.5 * tagged and soft < 0.25 * tagged,
            "hypotheses": sum(1 for q in qs if q.get("hypothesis")), "testing": sum(1 for q in qs if q.get("verdict") == "testing")}


# Where insight comes from: people with different vantage points, inside and outside the team.
INSIGHT_KINDS = [
    ("customer", "Customers and business users"), ("vendor", "Vendors and suppliers"), ("frontline", "Frontline engineers and operations"),
    ("sales", "Sales and customer service"), ("staff", "Finance, legal and HR"), ("integrator", "Integrators: project and product managers"),
    ("historian", "Natural historians: people who've been here a long time"),
]


def insight_sources(conn) -> dict:
    from .people_crm import _last_contacts

    last = _last_contacts(conn)
    kinds = {k: [] for k, _ in INSIGHT_KINDS}
    for p in models.people.fetch_all(conn, "active = 1"):
        for k in p.get("insight") or []:
            if k in kinds:
                kinds[k].append({"id": p["id"], "name": p["name"], "heard": p["id"] in last})
    tagged = sum(len(v) for v in kinds.values())
    out = [{"key": k, "label": label, "people": kinds[k], "heard": sum(1 for x in kinds[k] if x["heard"])} for k, label in INSIGHT_KINDS]
    return {"kinds": out, "gaps": [x["key"] for x in out if not x["heard"]] if tagged >= 3 else []}


LEARNING_METHODS_KEY = "first90.learning_methods"
LEARNING_METHODS = [
    ("survey", "Climate or engagement survey", "Culture and morale, if results exist for your group.", "#/culture/pulse"),
    ("slices", "Interviews across a slice", "Everyone at one level (horizontal) or down through levels (vertical), same questions.", "#/listening"),
    ("feedback", "Feed back to the group", "Share your themes and questions with the people you interviewed, together.", "#/rollup"),
    ("focus", "Focus groups", "A group that does similar work, to probe a shared concern and see who leads.", None),
    ("decision", "Analyze a past decision", "Trace how a recent important decision was made and who influenced it.", None),
    ("process", "Process analysis", "Chart a key process end to end and find where work waits.", "#/sdlc"),
    ("tours", "Tours", "Time with the people closest to the product and the customer.", None),
    ("pilots", "Pilot projects", "Small changes, and how the organization responds to them.", "#/first90/changes"),
    ("assimilation", "New-leader assimilation", "A facilitated session where your team's questions reach you without names attached.", None),
]
METHOD_STATUS = ("not yet", "planned", "done", "not needed")


@router.get("/api/first90/learning-methods")
def learning_methods(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (LEARNING_METHODS_KEY,)).fetchone()
    saved = json.loads(row["value"]) if row else {}
    return {"statuses": list(METHOD_STATUS), "methods": [{"key": k, "label": l, "about": a, "link": link, "status": saved.get(k, {}).get("status", "not yet"), "notes": saved.get(k, {}).get("notes", "")}
                                                          for k, l, a, link in LEARNING_METHODS]}


@router.put("/api/first90/learning-methods/{key}")
def put_learning_method(key: str, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if key not in {k for k, *_ in LEARNING_METHODS}:
        raise HTTPException(404, "No such method.")
    if body.get("status", "not yet") not in METHOD_STATUS:
        raise HTTPException(400, "Unknown status.")
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (LEARNING_METHODS_KEY,)).fetchone()
    saved = json.loads(row["value"]) if row else {}
    saved[key] = {"status": body.get("status", "not yet"), "notes": body.get("notes") or ""}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (LEARNING_METHODS_KEY, json.dumps(saved)))
    return saved[key]


# A phased plan for how to learn, after the template in The First 90 Days, in our own words.
LEARNING_PLAN_KEY = "first90.learning_plan"
LEARNING_PLAN = [
    ("Before day 1", [
        ("research", 0, "Read what's public about the organization's strategy, structure, performance and people.", None),
        ("outside", 0, "Talk to people who see the team from outside: internal customers and suppliers, former employees, partners. Ask about history, politics and culture.", None),
        ("predecessor", 0, "Talk to your predecessor, if you can.", None),
        ("boss", 0, "Talk to your new manager about the situation and what they expect.", "#/first90/mandates"),
        ("hypotheses", 0, "Write down first impressions, early hypotheses, and the questions to ask once you arrive.", "#/first90/learning"),
    ]),
    ("Soon after you start", [
        ("data", 7, "Review operating plans, performance data and team records.", None),
        ("one-on-ones", 14, "Hold one-on-ones with each direct report, with the same questions each time.", "#/listening"),
        ("interfaces", 14, "Ask the people at the team's edges (service, sales, product, vendors) how things go between you.", None),
        ("top-down", 14, "Test alignment from the top down: ask leaders for the strategy, then see how far down it's understood.", None),
        ("bottom-up", 14, "Test awareness from the bottom up: ask the frontline about challenges and opportunities, then see whether leaders see them too.", None),
        ("boss-review-1", 20, "Review your hypotheses and findings with your manager.", "#/first90/mandates"),
    ]),
    ("By day 30", [
        ("feedback", 30, "Bring your preliminary findings back to the team as a group, and invite challenge.", "#/rollup"),
    ]),
    ("Days 31 to 60", [
        ("integrators", 40, "Meet the integrators: project and product managers who see across functions.", None),
        ("historians", 40, "Find the natural historians for the history, culture and politics. They can become allies.", None),
        ("outside-in", 45, "Look at the team from the outside in: how customers, vendors and partners see its strengths and weaknesses.", None),
        ("processes", 45, "Map a couple of key processes end to end with the groups involved.", "#/sdlc"),
        ("boss-review-2", 45, "Review what you've learned with your manager again.", "#/first90/mandates"),
    ]),
]


def _plan_saved(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (LEARNING_PLAN_KEY,)).fetchone()
    return json.loads(row["value"]) if row else {}


@router.get("/api/first90/learning-plan")
def learning_plan(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    start, saved = _start(conn), _plan_saved(conn)
    phases = [{"phase": name, "steps": [{"key": k, "day": d, "text": t, "link": link, "due": _due(start, d) if d else None,
                                          "done": bool(saved.get(k, {}).get("done")), "notes": saved.get(k, {}).get("notes", "")} for k, d, t, link in steps]}
              for name, steps in LEARNING_PLAN]
    total = sum(len(p["steps"]) for p in phases)
    return {"phases": phases, "done": sum(1 for p in phases for s in p["steps"] if s["done"]), "total": total}


@router.put("/api/first90/learning-plan/{key}")
def put_learning_step(key: str, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if key not in {k for _, steps in LEARNING_PLAN for k, *_ in steps}:
        raise HTTPException(404, "No such step.")
    saved = _plan_saved(conn)
    saved[key] = {"done": bool(body.get("done")), "notes": body.get("notes") or ""}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (LEARNING_PLAN_KEY, json.dumps(saved)))
    return saved[key]


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
