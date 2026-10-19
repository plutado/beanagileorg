"""Organizational alignment: how strategic direction, structure, core processes and skills fit together in one
area, inside an open system shaped by the outside world and by the internal climate and culture.

The model follows Figure 6-1 of The First 90 Days (Michael Watkins); the prompts, the Scrum lens and the traps
are written in our own words.
"""

from fastapi import APIRouter, Depends

from beanagileorg.core.app import get_viewer
from beanagileorg.core.privacy import Viewer

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
     [("/sdlc", "SDLC"), ("/agile/coverage", "Agile practice coverage"), ("/qa", "QA resources")]),
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
CLIMATE_PROMPT = "What is the climate like: morale, trust, energy, and how recent changes have landed? The culture map holds the deeper read."


@router.get("/api/alignment/guide")
def alignment_guide(viewer: Viewer = Depends(get_viewer)):
    return {
        "elements": [{"key": k, "name": n, "what": w, "prompts": p, "scrum": s, "look": [{"path": a, "label": b} for a, b in look]} for k, n, w, p, s, look in ELEMENTS],
        "links": LINKS,
        "external": [{"key": k, "name": n} for k, n in EXTERNAL],
        "fits": FITS,
        "traps": [{"name": n, "what": w} for n, w in TRAPS],
        "climate": CLIMATE_PROMPT,
    }
