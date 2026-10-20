"""Getting up to speed on purpose: a learning agenda, a diagnosis of each area's situation, the conversations
that set you up with your manager, the managers you mentor, and a read on momentum.

The starter questions, situation descriptions and conversation prompts are original to beanagileorg, written
for a new engineering manager. The ideas behind them are common to the transition literature (see Coaching
for further reading); nothing is quoted from a book.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .people_crm import me_id
from .routes import START_DATE_KEY, require_write, today

router = APIRouter()

STARTER_QUESTIONS = [
    ("present", "How much Agile does the team actually practice? Which ceremonies happen, which artifacts exist (backlog, sprint goal, definition of done, board), and how disciplined is it?", 7),
    ("present", "Does an SDLC exist, and what shape is it: written down or tribal, followed or skipped under pressure, and where does it break?", 7),
    ("past", "What has been tried before to bring in Scrum or a QA process, and what happened?", 21),
    ("present", "Which compliance or integration constraint most limits our speed today, and what would loosen it?", 21),
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
    ("politics", "What is my manager proud of or protective of: things they built, people they're loyal to?", 14),
    ("politics", "How does my manager's own boss judge them, and how does my work fit into that?", 21),
    ("present", "Where are the most promising opportunities to improve: the processes whose improvement would move overall performance?", 21),
    ("people", "Who, at any level, has the drive to help lead change and could lead an early project?", 21),
    ("present", "What time bombs are ticking: what do people already know could go wrong, that nobody has acted on?", 21),
]

# Predictable surprises: problems people could have seen coming. Each area has prompts for a deliberate look,
# especially at the areas you're least comfortable with, and at problems whose pieces sit with different groups.
SURPRISE_SCAN = [
    ("external", "Outside world", "Rules, the economy, platforms and partners that could change under you.", [
        "Is a regulation, audit or compliance date coming that the team's systems must meet?",
        "Do the platforms you build on have scheduled releases, version retirements or price changes ahead?",
        "Could a partner, vendor or public event (a seasonal peak, an outage elsewhere) put sudden load or change on your systems?",
    ]),
    ("market", "Customers, markets and strategy", "Shifts in what customers need, what competitors do, and where the business is heading.", [
        "Which customers or business users are unhappy, and does anyone with power know?",
        "Is the business strategy changing in a way the team's roadmap hasn't caught up with?",
        "Are there commitments made to customers or the business that the team can't actually meet?",
    ]),
    ("internal", "Inside the team", "Capabilities, processes, people and systems that could fail without warning.", [
        "Which systems or processes does only one person understand?",
        "When do contracts, licenses, certificates or support agreements end?",
        "What has broken before and been patched rather than fixed?",
        "Where is the team quietly working around a tool, a process or a missing skill?",
    ]),
    ("politics", "Politics", "People and alliances that could undermine you or the change.", [
        "Who could be working against the change while appearing to support it?",
        "Which person, product or decision is off limits to criticize, and why?",
        "Could a promise your predecessor made, or a peer's agenda, land on you?",
    ]),
]
SILO_PROMPT = "Which problem has its pieces held by different groups, so that no one sees the whole of it? Put the people together."

SITUATION_GUIDE = {
    "start-up": ("Something new is being built: a team, a product or a way of working. There's little to protect yet, and energy is high but unfocused.",
                 "Bring people, structure and a clear first goal quickly. Decide more yourself at first, then hand over as the team forms.",
                   'Excited but scattered: lots of energy, little focus yet.', 'Channel the energy: set a clear first goal and decide what not to do.', 'fast', 'Build quickly'),
    "turnaround": ("Something important is in trouble and people know it. Delay makes it worse.",
                   "Act early and visibly on the few things that matter most. Be direct about the problem, protect what still works, and show progress fast.",
                   "People know it's in trouble and may be close to despair, or arguing about the fix.", 'Give them a concrete plan and a reason to believe it will work. Make the tough calls with what you know, then adjust.', 'fast', 'Act fast: ready, fire, aim'),
    "accelerated growth": ("Things work, and demand is growing faster than the way of working can handle.",
                           "Add structure, process and people at the pace of growth, without losing what made it work.",
                   'Busy and stretched; structure feels like it slows things down.', 'Help people see why discipline now protects what made it work: shared processes and systems, and onboarding newcomers into the culture.', 'fast', 'Move fast, with structure'),
    "realignment": ("Things are drifting toward trouble, but many people don't see it yet, or don't want to.",
                    "Build a shared understanding of the problem before pushing solutions. Make the case with evidence, and enlist the people who already see it.",
                   "Comfortable or in denial: many don't see the clouds gathering.", 'Make the problem visible with facts, create urgency without blame, and build on the islands of strength.', 'learn', 'Learn first: ready, aim, fire'),
    "sustaining success": ("Things are going well and the job is to keep them that way, and find the next step.",
                           "Learn deeply before changing anything. Protect what works, avoid needless disruption, and look for the next opportunity.",
                   'Proud and possibly complacent.', 'Invent the challenge: keep people stretched, find the next direction for growth, and protect what works.', 'learn', 'Learn deeply first: ready, aim, fire'),
}
# Typical challenges and opportunities in each situation, after the STARS model in The First 90 Days, in our own words.
SITUATION_FACTORS = {
    "start-up": (["Building the strategy, structure and ways of working from nothing", "Recruiting a team and turning it into one team", "Making do with limited resources"],
                 ["You can do things right from the start", "People are energized by what's possible", "There are no old habits to undo"]),
    "turnaround": (["Re-energizing people who are demoralized", "Making good decisions under time pressure", "Going deep enough, including hard choices about work and people"],
                   ["Everyone agrees change is needed", "People affected outside the team tend to offer support", "A little success goes a long way"]),
    "accelerated growth": (["Putting in the structure and systems to scale", "Bringing many new people in without losing the culture"],
                           ["Growth itself motivates people", "People are willing to stretch, and to stretch the people around them"]),
    "realignment": (["Convincing people that change is necessary", "Carefully reshaping the leadership group and refocusing the team"],
                    ["There are real pockets of strength to build on", "People want to keep seeing themselves as successful"]),
    "sustaining success": (["Living in the shadow of a well-liked former leader and the team they built", "Playing good defense before launching too many new initiatives", "Finding the next level"],
                           ["A strong team may already be in place", "People are motivated to continue a record of success", "Foundations for continued success may already exist"]),
}

# How the six moves of a transition differ between a turnaround and a realignment, after Table 3-3 in The First 90
# Days, in our own words.
PLAYBOOK_LEVERS = ["Learn", "Strategic intent", "Priorities", "Your team", "Early wins", "Alliances"]
SITUATION_PLAYBOOK = {
    "turnaround": ["Learn the technical side fast: strategy, customers, systems and process. Be ready to act quickly.",
                   "Cut what isn't core, and say clearly what the team will become.",
                   "Make faster, bolder moves, mostly on strategy and structure.",
                   "Change people at the top where you need to, and bring in outside talent.",
                   "Move people from despair to hope with visible results.",
                   "Win support and resources from your manager and other stakeholders."],
    "realignment": ["Learn the culture and politics above all. Prepare deliberately before acting.",
                    "Sharpen and build on the strengths already there, and encourage new ideas.",
                    "Make slower, more deliberate moves, mostly on systems, skills and culture.",
                    "Make a few high-payoff changes, and promote promising people from within.",
                    "Move people from denial to awareness with facts: clear metrics, outside benchmarks, respected outside voices.",
                    "Build alliances sideways and down, so changes are actually carried out."],
}

# What to ask your manager for in each situation, after Table 4-2 in The First 90 Days, in our own words.
MANAGER_SUPPORT_BASE = ["Help getting the resources you need quickly", "Clear, measurable goals", "Guidance at the big decision points", "Help staying focused"]
MANAGER_SUPPORT = {
    "start-up": [],
    "turnaround": ["Backing for tough calls about people", "Help changing how the team is seen outside it", "A push to cut deep enough, fast enough"],
    "accelerated growth": ["Support for investment at the right pace, in the right places", "Help making the case for new systems and structure"],
    "realignment": ["Help making the case for change, especially if you're new to the organization"],
    "sustaining success": ["Constant reality checks: is this really doing well, or quietly drifting?", "Support for playing good defense and avoiding damaging mistakes", "Help finding the next level"],
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


@router.get("/api/risks/surprise-scan")
def surprise_scan(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    counts = dict(conn.execute("SELECT surprise_area, COUNT(*) FROM risks WHERE status != 'closed' AND surprise_area IS NOT NULL GROUP BY surprise_area").fetchall())
    return {"areas": [{"key": k, "name": n, "what": w, "prompts": p, "open": counts.get(k, 0)} for k, n, w, p in SURPRISE_SCAN],
            "silos": SILO_PROMPT}


@router.get("/api/learning-questions/agenda", dependencies=[Depends(no_judgments)])
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
    balance = learning_balance(qs)
    balance["realignment"] = bool(conn.execute("SELECT 1 FROM situations WHERE kind = 'realignment'").fetchone())
    return {"questions": qs, "areas": list(models.LEARNING_AREAS), "balance": balance, "sources": insight_sources(conn),
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
    return {k: {"what": w, "approach": a, "mood": m, "mood_job": j, "pace": p, "pace_label": pl,
                "challenges": SITUATION_FACTORS[k][0], "opportunities": SITUATION_FACTORS[k][1],
                "style": SITUATION_STYLE[k], "style_label": STYLE_LABELS[SITUATION_STYLE[k]], "from_manager": MANAGER_SUPPORT_BASE + MANAGER_SUPPORT[k],
                "playbook": [{"lever": l, "move": mv} for l, mv in zip(PLAYBOOK_LEVERS, SITUATION_PLAYBOOK[k])] if k in SITUATION_PLAYBOOK else []}
            for k, (w, a, m, j, p, pl) in SITUATION_GUIDE.items()}


PREFERRED_KEY = "first90.preferred_situation"
STYLE_KEY = "first90.my_change_style"
# Which leadership style each situation usually calls for: a hero who takes charge, or a steward who builds consensus.
SITUATION_STYLE = {"start-up": "hero", "turnaround": "hero", "accelerated growth": "both", "realignment": "steward", "sustaining success": "steward"}
STYLE_LABELS = {"hero": "Hero: takes charge, decides fast, leads from the front",
                "steward": "Steward: builds shared understanding and consensus, patient and systematic",
                "both": "Some of each"}


@router.get("/api/situations/portfolio")
def portfolio(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Your areas sorted into the five situations, with the share of your effort each gets over the next 90 days.
    A check that the situation you enjoy most isn't quietly getting the most effort."""
    areas = models.situations.visible_all(models.situations.fetch_all(conn), viewer)
    kinds = list(models.SITUATION_KINDS)
    groups = {k: [a for a in areas if a.get("kind") == k] for k in kinds}
    effort = {k: sum(a.get("effort") or 0 for a in groups[k]) for k in kinds}
    total = sum(effort.values())
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (PREFERRED_KEY,)).fetchone()
    preferred = row["value"] if row and viewer.floor == Level.PRIVATE else None
    top = max(kinds, key=lambda k: effort[k]) if total else None
    style = None
    team_mix = None
    if viewer.floor == Level.PRIVATE:
        r = conn.execute("SELECT value FROM settings WHERE key = ?", (STYLE_KEY,)).fetchone()
        style = r["value"] if r else None
        from .people_crm import me_id

        me = me_id(conn)
        reports = models.people.fetch_all(conn, "manager_id = ? AND active = 1", (me,)) if me else []
        team_mix = {s: sum(1 for p in reports if p.get("change_style") == s) for s in models.CHANGE_STYLES}
        team_mix["unknown"] = sum(1 for p in reports if not p.get("change_style"))
    hero_effort = sum(effort[k] for k in kinds if SITUATION_STYLE[k] == "hero")
    steward_effort = sum(effort[k] for k in kinds if SITUATION_STYLE[k] == "steward")
    mismatch = None
    if style == "hero" and steward_effort > hero_effort:
        mismatch = "hero"
    elif style == "steward" and hero_effort > steward_effort:
        mismatch = "steward"
    return {"groups": [{"kind": k, "areas": groups[k], "effort": effort[k], "style": SITUATION_STYLE[k]} for k in kinds],
            "undecided": [a for a in areas if not a.get("kind")], "total": total, "preferred": preferred,
            "preference_check": bool(preferred and top == preferred and len([k for k in kinds if effort[k]]) > 1),
            "my_style": style, "style_mismatch": mismatch, "team_mix": team_mix}


@router.put("/api/situations/my-style")
def put_my_style(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    s = body.get("style")
    if s and s not in models.CHANGE_STYLES:
        raise HTTPException(400, "Choose hero, steward or both.")
    if s:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (STYLE_KEY, s))
    else:
        conn.execute("DELETE FROM settings WHERE key = ?", (STYLE_KEY,))
    return {"style": s}


@router.put("/api/situations/preferred")
def put_preferred(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    k = body.get("kind")
    if k and k not in models.SITUATION_KINDS:
        raise HTTPException(400, "Unknown situation.")
    if k:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (PREFERRED_KEY, k))
    else:
        conn.execute("DELETE FROM settings WHERE key = ?", (PREFERRED_KEY,))
    return {"preferred": k}


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


MANAGER_FOCUS_KEY = "first90.manager_focus"


@router.get("/api/first90/manager-focus")
def manager_focus(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Your manager's top three priorities, the three things for your next one-on-one, and what to ask them for given
    the situations in your portfolio."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (MANAGER_FOCUS_KEY,)).fetchone()
    saved = json.loads(row["value"]) if row else {}
    kinds = [r["kind"] for r in conn.execute("SELECT DISTINCT kind FROM situations WHERE kind IS NOT NULL")]
    asks = list(MANAGER_SUPPORT_BASE)
    for k in kinds:
        asks += [a for a in MANAGER_SUPPORT.get(k, []) if a not in asks]
    return {"priorities": (saved.get("priorities") or [])[:3], "next_three": (saved.get("next_three") or [])[:3], "kinds": kinds, "asks": asks,
            "protective": saved.get("protective") or "", "menu": saved.get("menu") or [], "style": saved.get("style") or ""}


@router.put("/api/first90/manager-focus")
def put_manager_focus(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    clean = lambda xs: [str(x).strip() for x in (xs or []) if str(x).strip()][:3]
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (MANAGER_FOCUS_KEY,)).fetchone()
    saved = json.loads(row["value"]) if row else {}
    if "priorities" in body:
        saved["priorities"] = clean(body.get("priorities"))
    if "next_three" in body:
        saved["next_three"] = clean(body.get("next_three"))
    if "protective" in body:
        saved["protective"] = (body.get("protective") or "").strip()
    if "style" in body:
        saved["style"] = (body.get("style") or "").strip()
    if "menu" in body:
        saved["menu"] = [{k: str(r.get(k) or "").strip() for k in ("option", "cost", "delivers")} for r in (body.get("menu") or [])
                         if isinstance(r, dict) and str(r.get("option") or "").strip()][:8]
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (MANAGER_FOCUS_KEY, json.dumps(saved)))
    return saved


# ---- managers you mentor ----


@router.get("/api/mentoring/overview", dependencies=[Depends(no_judgments)])
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


@router.get("/api/preferences", dependencies=[Depends(no_judgments)])
def preferences(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    past = models.preference_assessments.fetch_all(conn)
    r = conn.execute("SELECT value FROM settings WHERE key = ?", (STYLE_KEY,)).fetchone()
    return {"my_style": r["value"] if r else None, "styles": [{"key": k, "label": v} for k, v in STYLE_LABELS.items()],
            "kinds": [{"key": k, "label": l, "about": d} for k, l, d in PREF_KINDS],
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
