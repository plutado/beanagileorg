"""Aligning the team: goals broken into owned, measurable parts; the mix of push and pull (Figure 7-2 of The First
90 Days); the incentive equation; and a vision people would put in extra effort for (the Table 7-2 lenses). All
prompts are in our own words.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()

TOOLS_KEY, INCENTIVES_KEY, VISION_KEY = "align.tools", "align.incentives", "align.vision"
PUSH = [("incentives", "Incentives", "Rewards tied to results."), ("reporting", "Reporting", "Regular, visible reports on progress."),
        ("planning", "Planning", "Plans with owners and dates."), ("procedures", "Procedures", "Agreed ways of working, such as the definition of done."),
        ("mission", "Mission statement", "A statement of what the team is for.")]
PULL = [("vision", "Shared vision", "A vivid picture of a future people want to reach."), ("teamwork", "Teamwork", "Pride in working well together.")]
MIX_ADVICE = {
    "turnaround": "A turnaround supplies its own push: the trouble shows people something must be done. Add pull so they believe it can work.",
    "realignment": "A realignment rarely feels urgent, so push alone won't move people. Put more weight on pull: a compelling vision of what the team could become.",
    "start-up": "A start-up runs on pull: the excitement of building something. Add just enough push to focus it.",
    "accelerated growth": "Fast growth needs push to bring discipline, and pull to keep people together as the team grows.",
    "sustaining success": "Sustaining success needs pull to invent the next challenge, so people don't settle.",
}
SCALE = ("low", "medium", "high")
LAG = ("short", "medium", "long")
INCENTIVE_QUESTIONS = [
    ("nonmonetary_available", "How much can you offer in non-monetary rewards: recognition, growth, interesting work, advancement?", SCALE),
    ("nonmonetary_valued", "How much do your people value those rewards?", SCALE),
    ("measurable", "How easily can you see and measure each person's contribution?", SCALE),
    ("lag", "How long between the work and its results?", LAG),
    ("interdependence", "How much does success depend on people working together?", models.INTERDEPENDENCE),
]
SCRUM_INCENTIVES = ("A Scrum team succeeds or fails together, so reward the team for the sprint goal and the product goal, and keep "
                    "individual rewards for growth and craft. Ranking people by velocity or points turns teammates into rivals.")
LENSES = [
    ("commitment", "Commitment to an ideal", "A cause worth believing in, and worth some sacrifice."),
    ("results", "Great results", "Excellence, quality and getting better all the time; challenging work."),
    ("contribution", "Making a contribution", "Serving customers and colleagues well; leaving things better than you found them."),
    ("team", "Being part of a team", "Caring about the team's success; work that's rewarding because it's shared."),
    ("growth", "Growing as a person", "Being treated with respect, and given the means to reach your potential."),
    ("control", "Control of our destiny", "Leading rather than following; recognition for the team and the organization."),
    ("integrity", "Trust and integrity", "Honesty, ethics and fairness."),
]
VISION_CHECKS = [
    ("inspiration", "It draws on what people care about: teamwork, contribution, craft, not just numbers."),
    ("story", "It makes people part of a larger story that gives the work meaning."),
    ("vivid", "It's vivid: you can picture what it looks like when it's achieved, and how it will feel."),
]
VISION_TEST = "Why would people put in extra effort to reach the goals we've set?"
OFFSITE_KEY = "align.offsite"
OFFSITE_PURPOSES = [
    ("diagnostic", "Understand the business together", "A shared picture of where things stand and why."),
    ("strategy", "Define the vision and strategy", "Where we're going and how."),
    ("process", "Change how the team works", "Meetings, decisions, handoffs, agreements."),
    ("relationships", "Build or repair relationships", "Trust and understanding between people."),
    ("planning", "Make a plan and commit to it", "Who does what, by when."),
    ("conflict", "Work through conflict", "Surface disagreements and reach agreements."),
]
OFFSITE_FOUNDATIONS = ("diagnostic", "relationships")
FACILITATOR_HELP = ("Lead and facilitate it yourself only if you're a skilled facilitator, the team respects you, and it isn't caught up in "
                    "conflict. Otherwise bring in someone from outside: an expert in the subject, or someone skilled at running group process.")
DECISION_GUIDE = {
    "processes": [
        ("decide alone", "You make the call, with little or no consultation. Fast, but you may miss what others know and get lukewarm support."),
        ("consult and decide", "You gather information and views, individually or as a group, then make the call yourself."),
        ("build consensus", "You seek both input and buy-in. Not everyone must agree: enough believe it's right, and the rest can live with it and support it."),
        ("unanimous", "Everyone must agree. With more than a few people it drags on or ends in a weak compromise."),
    ],
    "questions": [
        ("divisive", "Will the decision create winners and losers, or share out pain?", "consult and decide"),
        ("implementation", "Does it need energetic follow-through from people whose work you can't easily see?", "build consensus"),
        ("inexperienced", "Is the team inexperienced, or still new to you?", "consult and decide"),
        ("authority", "Do you still need to establish your authority, for example with former peers?", "consult and decide"),
    ],
    "situations": {"start-up": "consult and decide", "turnaround": "consult and decide", "realignment": "build consensus", "sustaining success": "build consensus"},
    "fair": "Run a fair process: people support decisions they disagree with when they've been heard and given a plausible reason. Say which process you're using and why.",
    "charade": "Never fake consensus for a decision already made. It fools nobody and breeds cynicism; say you're consulting and deciding instead.",
    "switch": "You can switch: start building consensus and move to consult-and-decide if it gets divisive, or the other way if follow-through turns out to matter most.",
    "time": "Time pressure alone isn't a reason to decide alone: you may decide faster, then spend longer selling it or chasing half-hearted follow-through.",
}


def _get(conn, key, default):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def _put(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))


def incentive_mix(a: dict) -> list[dict]:
    """The incentive equation as advice: total = non-monetary + monetary; monetary = fixed + performance-based;
    performance-based = individual + group."""
    rank = {"low": 0, "medium": 1, "high": 2, "short": 0, "long": 2}
    out = []
    av, va = a.get("nonmonetary_available"), a.get("nonmonetary_valued")
    if av and va:
        out.append({"part": "Non-monetary or monetary", "advice": "Lean on non-monetary rewards: they're available and valued." if rank[av] >= 1 and rank[va] >= 1
                    else "Non-monetary rewards will carry less weight here; make sure pay and recognition line up."})
    me, lag = a.get("measurable"), a.get("lag")
    if me and lag:
        if rank[me] == 0 or rank[lag] == 2:
            adv = "Mostly fixed pay: contributions are hard to see or results come long after the work."
        elif rank[me] == 2 and rank[lag] == 0:
            adv = "More room for performance-based pay: contributions are visible and results come quickly."
        else:
            adv = "A balance of fixed and performance-based pay."
        out.append({"part": "Fixed or performance-based", "advice": adv})
    inter = a.get("interdependence")
    if inter:
        out.append({"part": "Individual or group", "advice": {
            "independent": "Mostly individual rewards: success is the sum of individual efforts.",
            "mixed": "Both: individual rewards for independent work, team rewards where people depend on each other.",
            "interdependent": "Mostly group rewards (team, then unit, then company): success depends on working together.",
        }[inter]})
    return out


def _measurable(g: dict) -> bool:
    return g.get("to_value") is not None and bool(g.get("by_date")) and (g.get("from_value") is not None or bool(g.get("metric_id")))


@router.get("/api/team-align")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    goals = models.team_goals.visible_all(models.team_goals.fetch_all(conn), viewer)
    for g in goals:
        g["measurable"] = _measurable(g)
    kinds = sorted({s["kind"] for s in models.situations.fetch_all(conn) if s.get("kind")})
    out = {"goals": goals, "goal_status": models.TEAM_GOAL_STATUS,
           "push": [{"key": k, "name": n, "what": w} for k, n, w in PUSH], "pull": [{"key": k, "name": n, "what": w} for k, n, w in PULL],
           "tools": _get(conn, TOOLS_KEY, {}), "mix": [{"kind": k, "advice": MIX_ADVICE[k]} for k in kinds if k in MIX_ADVICE],
           "incentive_questions": [{"key": k, "question": q, "options": o} for k, q, o in INCENTIVE_QUESTIONS], "scrum_incentives": SCRUM_INCENTIVES,
           "lenses": [{"key": k, "name": n, "what": w} for k, n, w in LENSES], "vision_checks": [{"key": k, "text": t} for k, t in VISION_CHECKS],
           "vision_test": VISION_TEST, "vision": _get(conn, VISION_KEY, {}),
           "offsite": _offsite(conn), "offsite_purposes": [{"key": k, "name": n, "what": w} for k, n, w in OFFSITE_PURPOSES], "facilitator_help": FACILITATOR_HELP}
    answers = _get(conn, INCENTIVES_KEY, {})
    if not answers.get("interdependence"):
        prof = models.criteria_profiles.fetch_all(conn)
        if prof and prof[0].get("interdependence"):
            answers = {**answers, "interdependence": prof[0]["interdependence"]}
    out["incentives"], out["incentive_mix"] = answers, incentive_mix(answers)
    if viewer.floor == Level.PRIVATE:
        counts = {m: 0 for m in models.MOTIVATION}
        for a in models.team_assessments.fetch_all(conn):
            if a.get("motivation"):
                counts[a["motivation"]] += 1
        out["motivation"] = counts
    return out


@router.put("/api/team-align/tools")
def put_tools(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {k for k, _, _ in PUSH + PULL}
    clean = {k: bool(v) for k, v in body.items() if k in keys}
    _put(conn, TOOLS_KEY, clean)
    return clean


@router.put("/api/team-align/incentives")
def put_incentives(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    clean = {}
    for k, _, options in INCENTIVE_QUESTIONS:
        v = body.get(k)
        if v not in (None, ""):
            if v not in options:
                raise HTTPException(400, f"{k} must be one of: {', '.join(options)}")
            clean[k] = v
    _put(conn, INCENTIVES_KEY, clean)
    return {"incentives": clean, "incentive_mix": incentive_mix(clean)}


@router.put("/api/team-align/vision")
def put_vision(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    lens_keys, check_keys = {k for k, _, _ in LENSES}, {k for k, _ in VISION_CHECKS}
    themes = []
    for t in body.get("themes") or []:
        if isinstance(t, dict) and str(t.get("theme") or "").strip():
            said = [x for x in t.get("said_in") or [] if isinstance(x, dict) and x.get("where")]
            themes.append({"theme": str(t["theme"]).strip(), "said_in": said[-50:]})
    clean = {"draft": str(body.get("draft") or ""), "why_effort": str(body.get("why_effort") or ""), "story": str(body.get("story") or ""),
             "lenses": [k for k in body.get("lenses") or [] if k in lens_keys], "checks": [k for k in body.get("checks") or [] if k in check_keys],
             "non_negotiables": str(body.get("non_negotiables") or ""), "open_to_input": str(body.get("open_to_input") or ""),
             "stories": str(body.get("stories") or ""), "channels": str(body.get("channels") or ""), "themes": themes[:5], "live_it": bool(body.get("live_it"))}
    _put(conn, VISION_KEY, clean)
    return clean


def _offsite(conn) -> dict:
    o = _get(conn, OFFSITE_KEY, {})
    purposes = o.get("purposes") or []
    warnings = []
    if len(purposes) > 2:
        warnings.append("That's more than two purposes. A day or two can realistically achieve two at most; pick the two that matter most.")
    if "strategy" in purposes and not any(p in purposes for p in OFFSITE_FOUNDATIONS) and not o.get("foundations_done"):
        warnings.append("Vision and strategy need foundations first: a shared understanding of the business and working relationships. Do those first, or confirm they're already in place.")
    return {**o, "warnings": warnings}


@router.put("/api/team-align/offsite")
def put_offsite(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    keys = {k for k, _, _ in OFFSITE_PURPOSES}
    clean = {"purposes": [p for p in body.get("purposes") or [] if p in keys], "foundations_done": bool(body.get("foundations_done")),
             "when": str(body.get("when") or ""), "where": str(body.get("where") or ""), "agenda": str(body.get("agenda") or ""),
             "facilitator": body.get("facilitator") if body.get("facilitator") in ("me", "outsider") else None, "facilitator_why": str(body.get("facilitator_why") or "")}
    _put(conn, OFFSITE_KEY, clean)
    return _offsite(conn)


def suggest_process(answers: dict, kinds: list[str]) -> dict:
    """Weigh the rules of thumb and the situation into a suggested process, with the reasons."""
    votes, reasons = {"consult and decide": 0, "build consensus": 0}, []
    for key, q, leans in DECISION_GUIDE["questions"]:
        if answers.get(key):
            votes[leans] += 1
            reasons.append(f"{q} Leans {leans}.")
    for k in kinds:
        leans = DECISION_GUIDE["situations"].get(k)
        if leans:
            votes[leans] += 0.5
            reasons.append(f"A {k} leans {leans}.")
    if not reasons:
        return {"process": None, "reasons": []}
    best = max(votes, key=lambda p: (votes[p], p == "build consensus"))
    return {"process": best, "reasons": reasons}


@router.get("/api/decisions/process-guide")
def process_guide(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    kinds = sorted({s["kind"] for s in models.situations.fetch_all(conn) if s.get("kind")})
    return {"processes": [{"key": k, "what": w} for k, w in DECISION_GUIDE["processes"]],
            "questions": [{"key": k, "question": q, "leans": l} for k, q, l in DECISION_GUIDE["questions"]],
            "situations": kinds, "fair": DECISION_GUIDE["fair"], "charade": DECISION_GUIDE["charade"], "switch": DECISION_GUIDE["switch"], "time": DECISION_GUIDE["time"]}


@router.post("/api/decisions/suggest")
def suggest(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    kinds = sorted({s["kind"] for s in models.situations.fetch_all(conn) if s.get("kind")})
    return suggest_process(body or {}, kinds)
