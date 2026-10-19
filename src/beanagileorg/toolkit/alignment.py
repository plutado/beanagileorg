"""Organizational alignment: how strategic direction, structure, core processes and skills fit together in one
area, inside an open system shaped by the outside world and by the internal climate and culture.

The model follows Figure 6-1 of The First 90 Days (Michael Watkins); the prompts, the Scrum lens and the traps
are written in our own words.
"""

from fastapi import APIRouter, Depends

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models

router = APIRouter()

# (key, name, what it is, prompts, Scrum lens, where to look in the toolkit)
ELEMENTS = [
    ("direction", "Strategic direction", "Mission, vision and strategy: where the area is heading and why.", [
        "Can people on the team say what the area is for, and what matters most this year?",
        "Does the roadmap follow from that, or from whoever asked last?",
        "Is there a product goal, and do sprint goals connect to it?",
    ], "Scrum needs a product goal and a single ordered backlog. Without them, sprint goals become lists of tickets.",
     [("/roadmap", "Roadmap"), ("/landscape", "Business landscape")]),
    ("structure", "Structure", "How people are grouped into units, and how their work is coordinated, measured and rewarded.", [
        "Who owns which systems and customers? Is ownership clear, or split between groups?",
        "Do the measures and rewards push people to work together, or against each other?",
        "Are decision rights clear: who decides, who is consulted?",
        "Are teams built around products and outcomes, or around components and specialties?",
    ], "Scrum practices stall when structure fights them: individual targets, work split by specialty, one team serving several masters. Check this before blaming the team.",
     [("/teams", "Teams"), ("/raci", "RACI")]),
    ("processes", "Core processes", "The ways work moves from idea to value: planning, building, testing, releasing, supporting.", [
        "Where does work wait, and where does it get redone?",
        "Is the path to production written down, followed, and the same for everyone?",
        "Which process would, if improved, move overall performance the most?",
    ], "The Scrum events, the definition of done and the release path are core processes. Look at which ones actually happen, and how well.",
     [("/processes", "Core processes"), ("/sdlc", "SDLC"), ("/agile/coverage", "Agile practice coverage"), ("/qa", "QA resources")]),
    ("skills", "Skill bases", "The capabilities of the key groups of people.", [
        "Which skills does the strategy need that the team doesn't have yet?",
        "Where does knowledge sit with one person?",
        "Are people learning the skills the next year will need, or only the last year's?",
    ], "Cross-functional teams need testing, platform and integration skills inside the team, not borrowed from outside it.",
     [("/skills", "Skills and learning"), ("/people", "People")]),
]
# Each element touches its neighbors around the diamond.
LINKS = [("direction", "structure"), ("structure", "skills"), ("skills", "processes"), ("processes", "direction")]
EXTERNAL = [
    ("customers", "Customers"), ("distributors", "Distributors and channels"), ("suppliers", "Suppliers and vendors"),
    ("competitors", "Competitors"), ("governments", "Governments and regulators"), ("ngos", "NGOs and interest groups"),
    ("investors", "Investors and owners"), ("media", "Media"),
]
FITS = ("aligned", "strained", "misaligned")
TRAPS = [
    ("Change for change's sake", "Visible changes to strategy or structure made to leave a mark, before you understand the business."),
    ("One approach for every situation", "Radical moves suit a turnaround; a realignment or a sustaining success usually needs subtle, step-by-step change."),
    ("Restructuring around deeper problems", "If the real trouble is in processes, skills or culture, a new org chart moves the problem and costs you credibility."),
    ("Structures too complex", "Shared accountability can help, but keep lines of accountability as clear and simple as the goals allow."),
    ("Overestimating capacity for change", "People who have been through a string of recent changes can absorb less. Go step by step where the situation allows."),
]
# Strategic direction in three parts, so debates about labels don't get in the way.
DIRECTION_PARTS = [
    ("mission", "Mission: what", "What the area will achieve."),
    ("vision", "Vision: why", "Why people should care enough to do their best work."),
    ("strategy", "Strategy: how", "How time, money and people will be spent, and how decisions get made, to achieve the mission."),
]
FOUR_CS = [
    ("customers", "Customers", "Which customers, inside or outside, do we keep serving, and what do we offer them? What do we stop doing, and what do we start, and when?"),
    ("capital", "Capital", "Where do we invest, and where do we hold back? What extra money, people or time will we need, when, and where from?"),
    ("capabilities", "Capabilities", "What are we good at, and not? What can we build on, what must we build up, and what must we create or bring in?"),
    ("commitments", "Commitments", "Which big decisions about resources are coming, and when? Which past commitments, hard to reverse, do we live with or try to unwind?"),
]
WONT_DO = "What will we not do? A direction that rules nothing out isn't one. In Scrum, it's what backlog ordering and saying no protect."
DIRECTION_TESTS = [
    ("coherence", "Coherence", "Do the parts connect? Break the plans into customers, products, technology, functional plans and goals, and look for the thread: does the roadmap match the budget, the capacity and the skills it needs?"),
    ("adequacy", "Adequacy", "Is it enough for what the area must do in the next two or three years, and for the wider organization's goals? Are resources secured to carry it out?"),
    ("making", "How it was made", "Who drove it? A rushed direction may not be thought through; one that took forever may be a political compromise nobody believes in."),
    ("implementation", "Implementation", "Is it being pursued with energy? Judge by what people do, not what they say: do day-to-day decisions match it, which goals are really being chased, are the stated measures used to decide things, do people work across functions where it needs them to, and is there a way to build the new skills it calls for?"),
]
IMPLEMENTATION_SCRUM = "Sprint goals and the work actually finished show what a team really pursues. Work that keeps landing outside the product goal is an implementation signal; look at it together in the retrospective."
# Where the problem lies, and what to do about the direction.
VERDICTS = [
    ("formulation", "The direction itself is the problem"),
    ("implementation", "The direction is fine; carrying it out is the problem"),
    ("both", "Both"),
    ("neither", "Neither: it's sound and being pursued"),
]
MOVES = [
    ("leave", "Leave the direction as it is", "Put your effort into how it's carried out, or elsewhere."),
    ("tweak", "Adjust it modestly now, plan bigger changes later", "Small changes early, such as a goal raised a little or an investment brought forward. Save bigger changes until you've learned more and built support."),
    ("reexamine", "Raise questions so it gets looked at again", "If it's the wrong path, don't change it alone: raise questions with your manager and others so they re-examine it. Build the case below."),
]
TEST_RATINGS = ("sound", "some gaps", "weak")
DIRECTION_SCRUM = "At team level, the product goal is the mission, and sprint goals are steps toward it. A product goal people can say in a sentence is the first sign of a coherent direction."
# Every pair of elements can be out of step. The first four are the common ones.
MISMATCHES = [
    ("direction", "skills", "Does the team have the skills the direction needs? For example, a goal of faster experiments with nobody trained in the techniques that allow them."),
    ("direction", "processes", "Do the processes serve the direction? For example, a new customer focus with no way to gather and learn from those customers' needs."),
    ("structure", "processes", "Do the processes work across the structure? For example, teams split by product with no way to share what works between them."),
    ("structure", "skills", "Do people have the skills the structure asks for? For example, a move to shared accountability where people still expect to get things done through authority, not influence."),
    ("direction", "structure", "Is the area organized around what it's trying to achieve, or around how it used to work?"),
    ("processes", "skills", "Can people actually run the processes? A release process nobody is trained in exists only on paper."),
]
MISMATCH_STATES = ("fits", "mismatch")
SEQUENCES = {
    "turnaround": ("Direction first: it's usually not adequate. Then bring structure in line with it, then processes and skills.", ["direction", "structure", "processes", "skills"]),
    "realignment": ("Direction and structure are rarely the real problem. Look first at processes and skills; touch structure and direction only if the diagnosis says so.", ["processes", "skills", "structure", "direction"]),
    "other": ("Follow the logic of a long voyage: destination and route (direction), then the boat (structure), how it's fitted out (processes), and the crew (skills). Keep watching for reefs that aren't on the chart.", ["direction", "structure", "processes", "skills"]),
}
CLOSE_THE_LOOP = "Close the loop. What you learn about structure, processes and skills shows the team's capability and its capacity for change, which in turn shows what change of direction is realistic, and how fast."
# Structure in four parts, the balances every structure strikes, and the problems that come with them.
STRUCTURE_CAUTION = "Structure decides who has authority to do what, so changing it moves power. Change it only when it's clearly needed, as in a turnaround or fast growth. In a realignment, with no crisis to drive it, early structural change is risky."
STRUCTURE_PARTS = [
    ("units", "Units", "How people are grouped: by function, product, customer or place.", [
        "Does the grouping help the area achieve its mission and carry out its strategy?",
        "Are the right people in the right places for the core objectives?",
    ]),
    ("reporting", "Reporting lines and integration", "Who reports to whom, how effort is coordinated, and how work moves between units.", [
        "Do reporting lines help line up effort? Is it clear who's accountable for what?",
        "Is the work of different units joined up well, or does it fall between them?",
    ]),
    ("decisions", "Decision rights and rules", "Who can decide what, and the rules that keep decisions in line with the strategy.", [
        "Are decisions made by the people with the most relevant knowledge?",
        "Is the balance right between deciding centrally and locally, and between standard and custom?",
    ]),
    ("incentives", "Measures and incentives", "What people are measured on and rewarded for.", [
        "Are we measuring and rewarding what matters most to the strategy?",
        "Is the balance right between fixed and performance-based rewards, and between individual and team incentives?",
    ]),
]
BALANCES = [
    ("central", "Decisions made centrally", "Decisions made locally"),
    ("standard", "Standard ways of working", "Custom to each team or customer"),
    ("rewards", "Fixed rewards", "Performance-based rewards"),
    ("incentives", "Individual incentives", "Team incentives"),
]
BALANCE_STEPS = ("far left", "leans left", "balanced", "leans right", "far right")
STRUCTURE_PROBLEMS = [
    ("silos", "Silos of excellence", "Grouping like with like builds deep expertise but isolates it. Who bridges the gaps, and are there cross-team mechanisms and shared goals?", "/sos", "Scrum of Scrums"),
    ("scope", "Decision scope too narrow or too broad", "Too central, and decisions are slow, poorly informed and wear out the few who make them. Too broad without the bigger picture, and people make unwise calls.", "/raci", "RACI"),
    ("incentives", "Incentives to do the wrong thing", "People do what they're rewarded for. Rewards that serve individuals at the group's expense, or reward neither, pull people apart.", "/metrics", "Metrics"),
    ("accountability", "Compartments or blurred accountability", "Hierarchy keeps accountability clear but traps information; shared or matrix reporting spreads information but can leave nobody accountable.", "/raci", "RACI"),
]
STRUCTURE_SCRUM = "Scrum's three accountabilities (product owner, Scrum Master, developers) are decision rights: the product owner orders the backlog, the developers decide how to do the work. A cross-functional team and the Scrum of Scrums are integration mechanisms. Team goals are the incentive Scrum relies on; individual velocity targets undo it."
CLIMATE_PROMPT = "What is the climate like: morale, trust, energy, and how recent changes have landed? The culture map holds the deeper read."


@router.get("/api/alignment/guide")
def alignment_guide(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    situations = {s["area"].strip().lower(): s["kind"] for s in models.situations.fetch_all(conn) if s.get("kind")}
    return {
        "direction": {"parts": [{"key": k, "name": n, "what": w} for k, n, w in DIRECTION_PARTS],
                      "four_cs": [{"key": k, "name": n, "prompt": q} for k, n, q in FOUR_CS], "wont_do": WONT_DO,
                      "tests": [{"key": k, "name": n, "prompt": q} for k, n, q in DIRECTION_TESTS], "ratings": TEST_RATINGS, "scrum": DIRECTION_SCRUM,
                      "implementation_scrum": IMPLEMENTATION_SCRUM, "verdicts": [{"key": k, "label": l} for k, l in VERDICTS],
                      "moves": [{"key": k, "label": l, "why": w} for k, l, w in MOVES]},
        "mismatches": [{"key": f"{a}-{b}", "a": a, "b": b, "question": q, "common": i < 4} for i, (a, b, q) in enumerate(MISMATCHES)],
        "mismatch_states": MISMATCH_STATES,
        "sequences": {k: {"why": w, "order": o} for k, (w, o) in SEQUENCES.items()},
        "close_the_loop": CLOSE_THE_LOOP,
        "structure": {"caution": STRUCTURE_CAUTION, "scrum": STRUCTURE_SCRUM,
                      "parts": [{"key": k, "name": n, "what": w, "prompts": p} for k, n, w, p in STRUCTURE_PARTS],
                      "balances": [{"key": k, "left": l, "right": r} for k, l, r in BALANCES], "steps": BALANCE_STEPS,
                      "problems": [{"key": k, "name": n, "what": w, "path": a, "label": b} for k, n, w, a, b in STRUCTURE_PROBLEMS]},
        "situations": situations,
        "elements": [{"key": k, "name": n, "what": w, "prompts": p, "scrum": s, "look": [{"path": a, "label": b} for a, b in look]} for k, n, w, p, s, look in ELEMENTS],
        "links": LINKS,
        "external": [{"key": k, "name": n} for k, n in EXTERNAL],
        "fits": FITS,
        "traps": [{"name": n, "what": w} for n, w in TRAPS],
        "climate": CLIMATE_PROMPT,
    }
