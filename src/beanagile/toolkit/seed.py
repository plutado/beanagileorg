"""Placeholder data for trying the toolkit. Every value is bracketed so it can't pass for real data."""

from datetime import date, timedelta

from . import models

RELATIONSHIPS = ["employee", "employee", "employee", "contractor", "contractor", "contractor", "peer", "stakeholder"]


def _day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def load_placeholders(conn, source: str) -> dict:
    ids = []
    for n, relationship in enumerate(RELATIONSHIPS, start=1):
        person = models.people.create(
            conn,
            {
                "name": f"[Placeholder name {n}]",
                "role": f"[Placeholder role {n}]",
                "relationship": relationship,
                "background": f"[Placeholder background {n}]",
                "skills": [f"[Placeholder skill {chr(64 + n)}]", f"[Placeholder skill {chr(65 + n % 4)}]"],
                "can_teach": [f"[Placeholder skill {chr(64 + n)}]"] if n % 2 else [],
                "wants_to_learn": [f"[Placeholder skill {chr(63 + n)}]"] if n % 2 == 0 else [],
                "goals": f"[Placeholder goals {n}]",
                "working_style": f"[Placeholder working style {n}]",
            },
            source,
        )
        ids.append(person["id"])

    for n, person_id in enumerate(ids[:4], start=1):
        models.interviews.create(
            conn,
            {
                "person_id": person_id,
                "date": _day(-14 + n * 3),
                "status": "done",
                "working": f"[Placeholder answer: what's working, {n}]",
                "frustrating": f"[Placeholder answer: what's frustrating, {n}]",
                "change_first": f"[Placeholder answer: change first, {n}]",
                "dont_change": f"[Placeholder answer: don't change, {n}]",
                "systems": ["[Placeholder system A]", f"[Placeholder system {'B' if n % 2 else 'C'}]"],
                "gaps": f"[Placeholder gap {n}]",
                "opportunities": f"[Placeholder opportunity {n}]",
                "themes": ["[Placeholder theme 1]", f"[Placeholder theme {n % 3 + 2}]"],
            },
            source,
        )
    for offset, person_id in zip((3, 6), ids[4:6]):
        models.interviews.create(conn, {"person_id": person_id, "date": _day(offset), "status": "planned"}, source)

    goals = [
        models.learning_goals.create(
            conn,
            {
                "track": f"[Placeholder track {n}]",
                "goal": f"[Placeholder learning goal {n}]",
                "evidence": f"[Placeholder evidence {n}]",
                "target_day": target,
                "status": status,
                "show_in_report": n != 3,
            },
            source,
        )
        for n, target, status in ((1, 30, "in progress"), (2, 90, "not started"), (3, 150, "at risk"))
    ]
    for goal, minutes in zip(goals, (90, 45, 30)):
        models.learning_log.create(
            conn, {"goal_id": goal["id"], "date": _day(-2), "minutes": minutes, "note": "[Placeholder note]"}, source
        )

    for n, (due, status) in enumerate(((-1, "open"), (2, "open"), (10, "open"), (-5, "done")), start=1):
        models.tasks.create(
            conn,
            {"title": f"[Placeholder task {n}]", "requested_by": f"[Placeholder name {n}]", "due": _day(due), "status": status},
            source,
        )
    for n, (cadence, due) in enumerate((("weekly", 1), ("every two weeks", 5), ("monthly", 20)), start=1):
        models.obligations.create(
            conn, {"title": f"[Placeholder obligation {n}]", "cadence": cadence, "next_due": _day(due)}, source
        )
    return {"people": len(ids), "interviews": 6, "learning_goals": len(goals), "tasks": 4, "obligations": 3}
