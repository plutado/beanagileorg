"""Placeholder data for trying the toolkit. Every value is bracketed so it can't pass for real data."""

from datetime import date, timedelta

from . import models

RELATIONSHIPS = ["employee", "employee", "employee", "contractor", "contractor", "contractor", "peer", "stakeholder"]


def _day(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def _empty(conn, table: str) -> bool:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def load_placeholders(conn, source: str) -> dict:
    """Fill each empty part of the toolkit with bracketed placeholders. Parts that already have data are left alone."""
    loaded = {}
    if _empty(conn, "people"):
        loaded.update(_core(conn, source))
    person_ids = [r[0] for r in conn.execute("SELECT id FROM people ORDER BY id LIMIT 6")]
    if person_ids and _empty(conn, "action_items"):
        loaded.update(_dev_sync(conn, source, person_ids))
    if person_ids and _empty(conn, "systems"):
        loaded.update(_escalation(conn, source, person_ids))
    return loaded


def _core(conn, source: str) -> dict:
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


def _dev_sync(conn, source: str, people: list[int]) -> dict:
    from .routes import propose_session

    pick = lambda i: people[i % len(people)]
    rows = [
        (1, 0, 0, -9, 5, "in progress", True),
        (2, 1, 2, -8, -2, "open", False),
        (3, 2, 0, -6, 7, "open", True),
        (4, 3, 1, -4, -1, "waiting", False),
        (5, 2, 0, -3, 10, "open", True),
        (6, 1, 2, -11, -4, "done", False),
    ]
    for n, raised, owner, raised_on, due, status, learning in rows:
        item = models.action_items.create(
            conn,
            {"concern": f"[Placeholder concern {n}]", "raised_by_id": pick(raised), "owner_id": pick(owner),
             "raised_on": _day(raised_on), "next_action": f"[Placeholder next action {n}]", "due": _day(due),
             "status": status, "learning": learning},
            source,
        )
        propose_session(conn, item, source)
    first = conn.execute("SELECT id FROM learning_sessions ORDER BY id LIMIT 1").fetchone()
    if first:
        models.learning_sessions.update(conn, first[0], {"date": _day(12), "status": "scheduled"}, source)
    return {"action_items": len(rows), "learning_sessions": conn.execute("SELECT COUNT(*) FROM learning_sessions").fetchone()[0]}


def _escalation(conn, source: str, people: list[int]) -> dict:
    pick = lambda i: people[i % len(people)]
    severities = [
        models.severities.create(
            conn,
            {"level": f"Sev {n}", "definition": f"[Placeholder definition for Sev {n}]", "response_time": f"[Placeholder response time {n}]",
             "who_is_paged": f"[Placeholder who is paged at Sev {n}]", "who_is_told": f"[Placeholder who is told at Sev {n}]"},
            source,
        )
        for n in (1, 2, 3)
    ]
    systems = []
    for n in (1, 2, 3):
        system = models.systems.create(
            conn,
            {"name": f"[Placeholder system {n}]", "description": f"[Placeholder description {n}]",
             "how_to_open_case": f"[Placeholder: how to open a vendor case for system {n}]",
             "vendor_support": f"[Placeholder vendor support line {n}]", "business_contacts": f"[Placeholder business contacts {n}]",
             "owner_id": pick(n), "first_responder_id": pick(n + 1), "backup_id": pick(n + 2)},
            source,
        )
        systems.append(system)
        for position, (person, method, ooh) in enumerate([(n + 1, "chat", False), (n, "call", False), (n + 2, "page", True), (n, "call", True)]):
            models.escalation_steps.create(
                conn,
                {"system_id": system["id"], "position": position, "person_id": pick(person), "method": method, "out_of_hours": ooh},
                source,
            )
    models.incidents.create(
        conn,
        {"date": _day(-6), "system_id": systems[0]["id"], "severity_id": severities[1]["id"], "summary": "[Placeholder incident summary]",
         "people_ids": [pick(1), pick(2)], "resolved_at": _day(-6)},
        source,
    )
    return {"systems": len(systems), "severities": len(severities), "incidents": 1}
