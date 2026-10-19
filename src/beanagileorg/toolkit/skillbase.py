"""Skill bases: the four kinds of knowledge a team runs on (individual, relational, embedded and meta), the
skills each core process needs and who holds them, and the gaps and underused resources worth acting on.

After the skill-base ideas in chapter 6 of The First 90 Days (Michael Watkins), in our own words.
"""

import json

from fastapi import APIRouter, Depends

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models

router = APIRouter()

KINDS = [
    ("individual", "Individual expertise", "What each person knows, from training, education and experience.",
     "Which skills do the core processes need that only one person has, or nobody?"),
    ("relational", "Working together", "How people combine what they know to reach a shared goal.",
     "Do people know how to work together: agreements, pairing, reviews, a shared definition of done?"),
    ("embedded", "Core technology", "The systems and tools the team's performance depends on.",
     "Which systems does the team depend on with no backup person or no documentation?"),
    ("meta", "Knowing where to go", "Where to find critical knowledge the team doesn't hold: vendors, partners, communities, outside experts.",
     "When the team is stuck, who outside it can help, and does everyone know?"),
]
UNDERUSED_PROMPTS = [
    "Who does much better than average, and what helps them: methods, tools, support from key people? Could the rest of the team use it?",
    "Which ideas have sat on the shelf for lack of interest or investment?",
    "Which tools or features do we already have, and barely use?",
]
CULTURE = ("Culture can't be changed directly. It follows the architecture (what's measured, how objectives and incentives are set) "
           "and what leaders do. Where success needs close teamwork, weight team goals; where work is independent and measurable, "
           "individual goals can carry more.")


def _in_use(conn) -> int:
    row = conn.execute("SELECT value FROM settings WHERE key = 'agile.practice'").fetchone()
    data = json.loads(row["value"]) if row else {}
    return sum(1 for v in data.values() if (v or {}).get("status") == "practiced")


@router.get("/api/skills/knowledge")
def knowledge(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    private = viewer.floor == Level.PRIVATE
    active = [p for p in models.people.fetch_all(conn) if p["active"]]
    holders: dict[str, list[str]] = {}
    for p in active:
        for sk in p["skills"]:
            holders.setdefault(sk, []).append(p["name"])
    systems = [s for s in models.systems.fetch_all(conn) if s.get("lifecycle") != "retired"]
    agreed = conn.execute("SELECT COUNT(*) FROM team_agreements WHERE status = 'agreed'").fetchone()[0]
    vendors = [v for v in models.vendors.fetch_all(conn) if v["status"] != "ended"]
    sources = models.knowledge_sources.fetch_all(conn)
    facts = {
        "individual": {"skills": len(holders), "single": sorted(s for s, h in holders.items() if len(h) == 1), "link": "/skills"},
        "relational": {"agreements": agreed, "practices_in_use": _in_use(conn), "link": "/culture/agreements"},
        "embedded": {"systems": len(systems), "no_backup": [s["name"] for s in systems if not s.get("backup_id")],
                     "no_docs": [s["name"] for s in systems if not s.get("docs_link")], "link": "/architecture"},
        "meta": {"vendors": len(vendors), "sources": len(sources), "link": "/vendors"},
    }
    if not private:
        facts["individual"]["single"] = len(facts["individual"]["single"])
    return {"kinds": [{"key": k, "name": n, "what": w, "prompt": q, "facts": facts[k]} for k, n, w, q in KINDS],
            "underused": UNDERUSED_PROMPTS, "culture": CULTURE, "private": private}


@router.get("/api/skills/coverage")
def coverage(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """For each core process, the skills it needs and how many people hold each: none or one is a gap."""
    private = viewer.floor == Level.PRIVATE
    active = [p for p in models.people.fetch_all(conn) if p["active"]]
    out = []
    for proc in models.core_processes.fetch_all(conn):
        if not proc.get("skills"):
            continue
        rows = []
        for sk in proc["skills"]:
            have = [p["name"] for p in active if any(x.strip().lower() == sk.strip().lower() for x in p["skills"])]
            rows.append({"skill": sk, "count": len(have), "people": have if private else None})
        out.append({"id": proc["id"], "name": proc["name"], "focus": proc["focus"], "skills": rows})
    return out
