"""Connecting what you learn and plan: learning answers into the business landscape, questions suggested from the
listening tour, a shareable list of the changes you're bringing, and a stakeholder map of influence against stance."""

from collections import Counter

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()
TEAM = Viewer(floor=Level.PRESENTABLE, source="team")


@router.post("/api/learning-questions/{qid}/to-assessment", status_code=201)
def to_assessment(qid: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn an answered learning question into a point in the business landscape: a strength, weakness, opportunity or threat."""
    require_write(viewer)
    q = models.learning_questions.fetch(conn, qid)
    if not q:
        raise HTTPException(404, "No such learning question.")
    if not (q.get("answer") or "").strip():
        raise HTTPException(409, "Answer the question first.")
    if body.get("subject_type") not in models.SUBJECT_TYPES or not body.get("subject_id"):
        raise HTTPException(400, "Pick the offering or department it's about.")
    title = (body.get("title") or q["answer"].strip().split("\n")[0])[:160]
    return models.assessments.create(conn, {"subject_type": body["subject_type"], "subject_id": int(body["subject_id"]), "quadrant": body.get("quadrant") or "weakness",
                                            "title": title, "evidence": f"Learning question: {q['question']}\n\n{q['answer']}", "source": body.get("source") or "listening tour",
                                            "date": today().isoformat()}, viewer.source)


@router.get("/api/learning-questions/suggestions", dependencies=[Depends(no_judgments)])
def suggestions(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Themes that keep coming up in the listening tour but no learning question covers yet."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    counts = Counter(t.strip().lower() for i in models.interviews.fetch_all(conn) for t in (i.get("themes") or []) if t and t.strip())
    asked = " ".join((q["question"] or "").lower() for q in models.learning_questions.fetch_all(conn))
    out = [{"theme": t, "times": n, "question": f"What's behind \"{t}\", and what would change it?"} for t, n in counts.most_common() if t not in asked]
    return {"suggestions": out[:8]}


def changes_summary(conn) -> dict:
    """The changes you're bringing, in one page the team can see: what, why, how we'll try it, and where each stands."""
    changes = models.team_changes.visible_all(models.team_changes.fetch_all(conn), TEAM)
    order = {s: i for i, s in enumerate(("trial", "review", "announced", "idea", "adopted", "dropped"))}
    changes.sort(key=lambda c: (order.get(c["status"], 9), c.get("position") or 0))
    agreements = {a["id"]: a["text"] for a in models.team_agreements.fetch_all(conn)}
    policies = {p["id"]: p["title"] for p in models.sdlc_policies.fetch_all(conn)}
    lines = ["# Changes we're making", "", "One at a time: each is announced, tried for a set time, reviewed together, and then kept or dropped.", ""]
    for status in ("trial", "review", "announced", "idea", "adopted", "dropped"):
        group = [c for c in changes if c["status"] == status]
        if not group:
            continue
        lines += [f"## {status.capitalize()}", ""]
        for c in group:
            lines.append(f"- **{c['title']}**" + (f": {c['why']}" if c.get("why") else ""))
            if c.get("how_we_try"):
                lines.append(f"  - How we'll try it: {c['how_we_try']}")
            if c.get("review_on") and status in ("trial", "announced"):
                lines.append(f"  - Review on {c['review_on']}")
            if c.get("agreement_id") in agreements:
                lines.append(f"  - Became our agreement: {agreements[c['agreement_id']]}")
            if c.get("policy_id") in policies:
                lines.append(f"  - Became our SDLC policy: {policies[c['policy_id']]}")
        lines.append("")
    if len(lines) == 4:
        lines.append("Nothing yet.")
    return {"title": "Changes we're making", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/team-changes/summary")
def get_changes_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return changes_summary(conn)


@router.post("/api/team-changes/summary/export")
def export_changes_summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = changes_summary(conn)
    log_export(conn, "team-changes:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


@router.get("/api/people/stakeholder-map", dependencies=[Depends(no_judgments)])
def stakeholder_map(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Influence against stance, from what you've noted on each person, with what each of you offers and needs beside it."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    people = [p for p in models.people.fetch_all(conn, "active = 1") if p.get("influence") or p.get("stance")]
    grid = {i: {s: [] for s in models.STANCE} for i in reversed(models.INFLUENCE)}
    unplaced = []
    for p in people:
        entry = {"id": p["id"], "name": p["name"], "role": p.get("role"), "offer_them": p.get("offer_them"), "need_from_them": p.get("need_from_them")}
        if p.get("influence") in models.INFLUENCE and p.get("stance") in models.STANCE:
            grid[p["influence"]][p["stance"]].append(entry)
        else:
            unplaced.append({**entry, "influence": p.get("influence"), "stance": p.get("stance")})
    focus = [e for s in ("skeptic", "blocker", "neutral") for e in grid["high"][s]]
    return {"influence": list(reversed(models.INFLUENCE)), "stances": list(models.STANCE), "grid": grid, "unplaced": unplaced, "focus": focus}
