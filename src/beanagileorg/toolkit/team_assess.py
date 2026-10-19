"""Assessing the team you inherit: the criteria you judge people by (Table 7-1 of The First 90 Days, as a form),
and a private, person-by-person view built from a first impression and then evidence. Criteria and prompts are
in our own words.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .first90 import inherited_team, team_plan
from .routes import require_write, today

router = APIRouter()

CRITERIA = [
    ("competence", "Competence", "Do they have the skill and experience to do the job well?"),
    ("judgment", "Judgment", "Do they make sound calls, especially under pressure or when the team's interest means giving something up?"),
    ("energy", "Energy", "Do they bring the right energy, or are they burned out or checked out?"),
    ("focus", "Focus", "Do they set priorities and stick to them, or scatter in all directions?"),
    ("relationships", "Relationships", "Do they work well with others and support decisions the team makes together?"),
    ("trust", "Trust", "Do they keep their word and follow through on commitments?"),
]
REFLECTION = [
    "Do these weights match how you actually judge people when you're not thinking about it?",
    "Which criteria did you weight lowest? What could you miss about someone there?",
    "Why is your threshold the one where nothing else matters? Would everyone on your team agree it should be?",
]
LOW = 2  # a score at or below this on your threshold criterion is below the bar
CRITICAL = 7  # positions rated this or higher can't carry a B or C player for long
DYNAMICS_KEY = "team.dynamics"
ASSUMPTION = ("Your weights rest on beliefs about what you can and can't change in people. If you made trust your threshold because "
              "you believe trustworthiness can't be changed, you may be right, but be conscious that it's an assumption.")
INTERDEPENDENCE_ADVICE = {
    "independent": "People mostly work on their own, so a high-performing group may be enough; how well they work together matters less.",
    "mixed": "Some work is shared and some independent. Weigh relationships for the people whose work depends on others.",
    "interdependent": "The work depends on people working together, as in a Scrum team, so relationships deserve real weight: a team, not a group of individuals.",
}
SITUATION_ADVICE = {
    "turnaround": "In a turnaround you need people who can perform at a high level now, and whose experience fits a turnaround.",
    "start-up": "In a start-up you need people who can build from nothing and live with ambiguity.",
    "accelerated growth": "In fast growth you need people who can scale what works and bring discipline to it.",
    "realignment": "In a realignment there's usually time to develop a promising B player, especially in a less critical role.",
    "sustaining success": "In a sustaining success you may have time to develop one or two high-potential people from B to A.",
}
ALTERNATIVES = [
    ("message", "A clear, private message given about where they stand. People often choose to move on."),
    ("shift", "A role on the team that suits their skills better, at least for now."),
    ("shrink", "A much smaller role, so they aren't holding the team back."),
    ("elsewhere", "A move elsewhere in the organization, only if you're convinced they'll do well there. Passing on a problem damages your reputation."),
    ("backup", "A backup or successor in development, so the work carries on."),
    ("hr", "Your HR partner involved, and a factual record of performance kept."),
]
RESPECT = "However this ends, treat the person with respect. The rest of the team will judge you by how fairly you handle it."
DISPOSITION_HELP = "Place each person provisionally by about day 30, but only when you're at least 90% sure. If you're not, they stay in observe until you learn more."
STARTER_TEMPLATES = [
    {"name": "Software developer",
     "measures": ["Cycle time on their stories", "Review turnaround, given and received", "Escaped defects traced to their changes", "Share of sprint commitments finished"],
     "should_show": "A steady flow of small changes, reviews given as well as received, and problems raised early.",
     "should_not_show": "Story points used to rank people. Points estimate work for planning; they don't measure a person.",
     "questions": ["Walk me through a recent change, from ticket to production.", "How do you know your change works?", "What would you fix first in our codebase, and why?"],
     "warning_signs": ["Large changes merged at the end of the sprint", "Reviews that are always approved without comment", "Can't explain how their code is tested"]},
    {"name": "Salesforce developer",
     "measures": ["Apex tests with meaningful assertions, not only coverage (the platform requires 75% coverage to deploy to production)", "Failed deployments to higher sandboxes", "Governor limit errors", "Balance of declarative tools and code"],
     "should_show": "Choosing configuration or flows where they fit and code where it's needed, and changes moving cleanly through the sandboxes.",
     "should_not_show": "Coverage reached by tests that assert nothing.",
     "questions": ["When would you use a flow instead of Apex?", "How do you make a trigger safe for bulk data?", "How does a change get from your sandbox to production here?"],
     "warning_signs": ["Tests written only to reach coverage", "Hard-coded record IDs", "Changes made directly in production"]},
    {"name": "Integration (MuleSoft) developer",
     "measures": ["Integration error rate", "Time to detect and recover from a failed integration", "APIs reused rather than rebuilt", "APIs documented"],
     "should_show": "Integrations that fail visibly and recover cleanly, with monitoring and clear ownership.",
     "should_not_show": "Silent failures discovered by the business days later.",
     "questions": ["What happens when the system downstream is down?", "How do you version an API without breaking its users?", "How would you know an integration had stopped working?"],
     "warning_signs": ["No monitoring or alerts", "The same point-to-point integration built twice", "Credentials kept in code"]},
    {"name": "QA engineer",
     "measures": ["Escaped defects", "Share of the regression suite automated", "Time from a build to test feedback", "Defects caught in refinement rather than at the end"],
     "should_show": "Involvement from refinement onward, risk-based test plans, and a regression suite that gets faster over time.",
     "should_not_show": "Bug counts used as a measure of a person, or QA as a gate only at the end.",
     "questions": ["When time is short, how do you decide what to test?", "What would you automate first, and why?", "How should QA shape the definition of done?"],
     "warning_signs": ["Testing starts only after development finishes", "Regression run by hand every release with no plan to change it", "No say in the definition of done"]},
]



def latest_profile(conn) -> dict | None:
    rows = models.criteria_profiles.fetch_all(conn)
    return rows[0] if rows else None


def weighted(ratings: dict, weights: dict) -> float | None:
    scored = {k: (ratings.get(k) or {}).get("score") for k in weights}
    scored = {k: v for k, v in scored.items() if isinstance(v, (int, float))}
    total = sum(weights[k] for k in scored)
    return round(sum(scored[k] * weights[k] for k in scored) / total, 1) if total else None


@router.get("/api/team-assessment/guide")
def guide(viewer: Viewer = Depends(get_viewer)):
    return {"criteria": [{"key": k, "name": n, "question": q} for k, n, q in CRITERIA], "reflection": REFLECTION, "placements": models.PLACEMENTS,
            "changeable": models.CHANGEABLE, "interdependence": models.INTERDEPENDENCE, "interdependence_advice": INTERDEPENDENCE_ADVICE,
            "assumption": ASSUMPTION, "situation_fit": models.SITUATION_FIT, "dispositions": models.DISPOSITIONS, "disposition_help": DISPOSITION_HELP,
            "critical": CRITICAL, "alternatives": [{"key": k, "text": t} for k, t in ALTERNATIVES], "respect": RESPECT,
            "motivation": models.MOTIVATION}


@router.post("/api/team-assessment/criteria", status_code=201)
def save_criteria(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    weights = body.get("weights") or {}
    if set(weights) != set(models.EVAL_CRITERIA) or not all(isinstance(v, int) and 0 <= v <= 100 for v in weights.values()):
        raise HTTPException(400, "Give a whole number from 0 to 100 for each of the six criteria.")
    if sum(weights.values()) != 100:
        raise HTTPException(400, f"The weights add up to {sum(weights.values())}; they need to add up to 100.")
    if body.get("threshold") not in models.EVAL_CRITERIA:
        raise HTTPException(400, "Pick one threshold criterion.")
    changeable = {k: v for k, v in (body.get("changeable") or {}).items() if k in models.EVAL_CRITERIA and v in models.CHANGEABLE}
    return models.criteria_profiles.create(conn, {"date": today().isoformat(), "weights": weights, "threshold": body["threshold"],
                                                  "reflection": body.get("reflection") or "", "changeable": changeable,
                                                  "interdependence": body.get("interdependence") or None}, viewer.source)


@router.get("/api/team-assessment")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    prof = latest_profile(conn)
    weights = (prof or {}).get("weights") or {k: 1 for k in models.EVAL_CRITERIA}
    threshold = (prof or {}).get("threshold")
    by_person = {a["person_id"]: a for a in models.team_assessments.fetch_all(conn)}
    people = []
    for p in inherited_team(conn):
        a = by_person.get(p["id"])
        ratings = (a or {}).get("ratings") or {}
        th = (ratings.get(threshold) or {}).get("score") if threshold else None
        crit = (a or {}).get("criticality")
        people.append({"id": p["id"], "name": p["name"], "role": p.get("role"), "assessment": a,
                       "score": weighted(ratings, weights) if a else None, "below_threshold": isinstance(th, (int, float)) and th <= LOW,
                       "considered": bool(a and a.get("considered_on")),
                       "critical_gap": bool(a and a.get("placement") in ("B", "C") and isinstance(crit, int) and crit >= CRITICAL),
                       "disposition": (a.get("disposition") if a and a.get("confident") and a.get("disposition") else "observe")})
    plan = team_plan(conn)
    kinds = sorted({s["kind"] for s in models.situations.fetch_all(conn) if s.get("kind")})
    inter = (prof or {}).get("interdependence")
    warn_rel = bool(prof and inter == "interdependent" and (prof.get("weights") or {}).get("relationships", 0) < 15)
    return {"profile": prof, "profiles": len(models.criteria_profiles.fetch_all(conn)), "people": people,
            "conclusions_due": plan["conclusions_due"], "conclusions_day": plan["conclusions_day"],
            "missing": [x["name"] for x in people if not x["considered"]],
            "situations": [{"kind": k, "advice": SITUATION_ADVICE.get(k, "")} for k in kinds],
            "interdependence_advice": INTERDEPENDENCE_ADVICE.get(inter), "relationships_low": warn_rel,
            "dynamics": _dynamics(conn), "templates": [{"id": t["id"], "name": t["name"]} for t in models.role_templates.fetch_all(conn)]}


def _dynamics(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (DYNAMICS_KEY,)).fetchone()
    return json.loads(row["value"]) if row else {}


BEFORE_KEY = "team.before"
BEFORE_ROLES = [("influencer", "Had the most influence on key issues"), ("devils_advocate", "Played devil's advocate"), ("innovator", "The innovator"),
                ("avoider", "Avoided uncertainty"), ("listened_to", "The one everyone listened to most"), ("peacemaker", "The peacemaker"), ("rabble_rouser", "The rabble-rouser")]
CORE_MEETING = ("about right", "too inclusive", "too exclusive")
CORE_MEETING_ADVICE = {"too inclusive": "Shrink the core group and streamline the meetings: it signals that you value focus and efficiency.",
                       "too exclusive": "Broaden participation carefully: it signals that you won't play favorites or listen to only a few voices."}


@router.get("/api/team-assessment/before")
def get_before(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (BEFORE_KEY,)).fetchone()
    data = json.loads(row["value"]) if row else {}
    return {"data": data, "roles": [{"key": k, "label": l} for k, l in BEFORE_ROLES], "core_meeting": CORE_MEETING,
            "advice": CORE_MEETING_ADVICE.get(data.get("core_meeting"))}


@router.put("/api/team-assessment/before")
def put_before(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """How the team worked before you arrived: roles, meetings, decisions, and your predecessor's style next to yours."""
    require_write(viewer)
    role_keys = {k for k, _ in BEFORE_ROLES}
    clean = {"roles": {k: str(v) for k, v in (body.get("roles") or {}).items() if k in role_keys and str(v).strip()},
             **{k: str(body.get(k) or "") for k in ("meetings_often", "meetings_who", "meetings_agenda", "decisions", "predecessor_style", "style_difference", "keep", "change")},
             "core_meeting": body.get("core_meeting") if body.get("core_meeting") in CORE_MEETING else None}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (BEFORE_KEY, json.dumps(clean)))
    return clean


@router.put("/api/team-assessment/dynamics")
def put_dynamics(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """How the team works as a whole: alliances, who defers to whom, and whether one-on-one answers were too uniform or too scattered."""
    require_write(viewer)
    keep = {k: str(body.get(k) or "") for k in ("alliances", "deference", "consistency", "notes")}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (DYNAMICS_KEY, json.dumps(keep)))
    return keep


@router.post("/api/role-templates/starter", status_code=201)
def starter_templates(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    have = {t["name"] for t in models.role_templates.fetch_all(conn)}
    added = [models.role_templates.create(conn, t, viewer.source)["id"] for t in STARTER_TEMPLATES if t["name"] not in have]
    if not added:
        raise HTTPException(409, "You already have the starter templates.")
    return {"templates": len(added)}


@router.put("/api/team-assessment/{person_id:int}")
def put_assessment(person_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Create or update the assessment of one person. The first impression, once dated, is kept as written."""
    require_write(viewer)
    if not models.people.fetch(conn, person_id):
        raise HTTPException(404, "No such person.")
    ratings = body.get("ratings") or {}
    for k, v in ratings.items():
        sc = (v or {}).get("score")
        if k not in models.EVAL_CRITERIA or (sc is not None and (not isinstance(sc, int) or not 1 <= sc <= 5)):
            raise HTTPException(400, "Score each criterion from 1 to 5.")
    crit = body.get("criticality")
    if crit is not None and (not isinstance(crit, int) or not 1 <= crit <= 10):
        raise HTTPException(400, "Rate how critical the position is from 1 to 10.")
    fields = {k: body[k] for k in ("ratings", "placement", "group_role", "considered_on", "notes", "criticality", "situation_fit",
                                   "situation_notes", "judgment", "disposition", "confident", "template_id", "alternatives", "motivation") if k in body}
    row = conn.execute("SELECT id FROM team_assessments WHERE person_id = ?", (person_id,)).fetchone()
    existing = models.team_assessments.fetch(conn, row["id"]) if row else None
    if "first_impression" in body and not (existing and existing.get("first_on")):
        fields["first_impression"] = body["first_impression"]
        if (body["first_impression"] or "").strip():
            fields["first_on"] = today().isoformat()
    if existing:
        return models.team_assessments.update(conn, existing["id"], fields, viewer.source)
    return models.team_assessments.create(conn, {"person_id": person_id, **fields}, viewer.source)
