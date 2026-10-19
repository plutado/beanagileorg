"""Assessing the team you inherit: the criteria you judge people by (Table 7-1 of The First 90 Days, as a form),
and a private, person-by-person view built from a first impression and then evidence. Criteria and prompts are
in our own words.
"""

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
    return {"criteria": [{"key": k, "name": n, "question": q} for k, n, q in CRITERIA], "reflection": REFLECTION, "placements": models.PLACEMENTS}


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
    return models.criteria_profiles.create(conn, {"date": today().isoformat(), "weights": weights, "threshold": body["threshold"],
                                                  "reflection": body.get("reflection") or ""}, viewer.source)


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
        people.append({"id": p["id"], "name": p["name"], "role": p.get("role"), "assessment": a,
                       "score": weighted(ratings, weights) if a else None, "below_threshold": isinstance(th, (int, float)) and th <= LOW,
                       "considered": bool(a and a.get("considered_on"))})
    plan = team_plan(conn)
    return {"profile": prof, "profiles": len(models.criteria_profiles.fetch_all(conn)), "people": people,
            "conclusions_due": plan["conclusions_due"], "conclusions_day": plan["conclusions_day"],
            "missing": [x["name"] for x in people if not x["considered"]]}


@router.put("/api/team-assessment/{person_id}")
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
    fields = {k: body[k] for k in ("ratings", "placement", "group_role", "considered_on", "notes") if k in body}
    row = conn.execute("SELECT id FROM team_assessments WHERE person_id = ?", (person_id,)).fetchone()
    existing = models.team_assessments.fetch(conn, row["id"]) if row else None
    if "first_impression" in body and not (existing and existing.get("first_on")):
        fields["first_impression"] = body["first_impression"]
        if (body["first_impression"] or "").strip():
            fields["first_on"] = today().isoformat()
    if existing:
        return models.team_assessments.update(conn, existing["id"], fields, viewer.source)
    return models.team_assessments.create(conn, {"person_id": person_id, **fields}, viewer.source)
