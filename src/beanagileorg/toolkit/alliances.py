"""Creating alliances: whose support each early win needs, the winning and blocking alliances, the influence
network behind the decision makers, and what moves the pivotal people. After chapter 8 of The First 90 Days
(Michael Watkins); prompts and playbook in our own words.
"""

from fastapi import APIRouter, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models

router = APIRouter()

PLAN_STANCES = ("for", "undecided", "against")
MOTIVATORS = ("recognition", "control", "power", "belonging", "growth")
RESIST = [
    ("status quo", "Comfortable with how things are", "Show what staying put costs, and what stays the same."),
    ("competence", "Afraid of looking incompetent after the change", "Offer training, time and support before you ask for results."),
    ("values", "Sees a threat to what they value", "Connect the change to the values they hold, and show what it protects."),
    ("power", "Would lose power or influence", "Look for a role in the new way of working, or a trade elsewhere."),
    ("allies", "Worried about people they care about", "Show how those people come through it, or what you'll do for them."),
]
PERSUADABLE = [
    ("indifferent", "Indifferent", "Trade: your support for something they care about, in return for theirs."),
    ("undecided", "Undecided", "Find out why, then educate and persuade."),
    ("waiting", "Waiting to see which way the wind blows", "Show momentum, so joining looks like the safe bet."),
]
SUPPORTERS = [
    "Look for people who share your vision, who pushed for similar change before, who are quietly improving things on a small scale, and newcomers not yet used to the old ways.",
    "Don't take support for granted. Keep supporters close, and ask them to help persuade others, with the strongest arguments you have.",
    "Consider alliances of convenience: people you disagree with elsewhere, but who share your view on this issue.",
    "Where someone you get on with disagrees on this issue, explain why, solve the problem together, and make up for their loss elsewhere if you can.",
]
OPPONENTS = "Probe the reasons before labeling anyone an opponent. A converted skeptic, or someone written off who proves themselves, makes a story that travels."
PHASING = "If people doubt that promises will be kept, phase the change in, each step tied to success on the one before."
STATUS_QUO = "If someone believes resisting can keep things as they are, show them the status quo is no longer an option. Once change looks certain, opposition often turns into a contest over what kind of change."
FORCES = "We tend to blame personality and overlook the situation. Look at the pressures on each person: goals, incentives, peers. Strengthen what pushes them your way and remove what holds them back."


@router.get("/api/alliances/guide")
def guide(viewer: Viewer = Depends(get_viewer)):
    return {"stances": PLAN_STANCES, "motivators": MOTIVATORS, "power_sources": models.POWER_SOURCES,
            "resist": [{"key": k, "reason": r, "response": a} for k, r, a in RESIST], "persuadable": [{"key": k, "name": n, "approach": a} for k, n, a in PERSUADABLE],
            "supporters": SUPPORTERS, "opponents": OPPONENTS, "phasing": PHASING, "status_quo": STATUS_QUO, "forces": FORCES}


@router.get("/api/alliance-plans/{plan_id}/diagram")
def diagram(plan_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The people in the plan, their stance on it, and the influence links among them and onto them."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    plan = models.alliance_plans.fetch(conn, plan_id)
    if plan is None:
        raise HTTPException(404, "No such alliance plan.")
    rows = (plan.get("rows") or {}).get("rows") or []
    stance = {r["person_id"]: r.get("stance") for r in rows if r.get("person_id")}
    core = set(stance) | set(plan["winning_ids"]) | set(plan["blocking_ids"])
    links = models.influence_links.fetch_all(conn)
    # Bring in the people who influence anyone in the plan, one step out.
    ids = core | {l["from_id"] for l in links if l["to_id"] in core}
    people = {p["id"]: p for p in models.people.fetch_all(conn) if p["id"] in ids}
    nodes = [{"id": i, "name": people[i]["name"], "stance": stance.get(i), "opinion_leader": bool(people[i].get("opinion_leader")),
              "winning": i in plan["winning_ids"], "blocking": i in plan["blocking_ids"]} for i in ids if i in people]
    edges = [{"from": l["from_id"], "to": l["to_id"], "strength": l["strength"], "topic": l.get("topic")} for l in links if l["from_id"] in ids and l["to_id"] in ids]
    return {"nodes": nodes, "edges": edges}
