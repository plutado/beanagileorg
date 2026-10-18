"""Starter content for delivery: a generic Agile adoption roadmap, the RACI decisions and the delivery metrics.

This is real, generic structure (not sample data), so it isn't bracketed. Each part loads only when empty.
"""

from . import models

ROADMAP = [
    ("Observe current ceremonies", "Sit in on standups, planning and releases; change nothing", "ceremony", 30),
    ("Daily standup", "15 minutes, updates and blockers only", "ceremony", 35),
    ("Dev sync", "Right after standup, for anything too big for it; every item logged with an owner", "ceremony", 35),
    ("Team working agreement", "Written with the team: hours, decisions, disagreements", "agreement", 40),
    ("Weekly refinement", "With product, so stories arrive ready", "ceremony", 40),
    ("Definition of ready", "Agreed with product and QA", "agreement", 45),
    ("Definition of done", "Agreed with product and QA, QA sign-off built in", "agreement", 45),
    ("Board matches real flow", "Columns for code review and QA, so work sent back is visible", "milestone", 45),
    ("Two-week sprints with planning", "First sprint planned against honest capacity", "ceremony", 45),
    ("Retrospective", "Every sprint; act on at least one item each time", "ceremony", 60),
    ("First clean release", "Well communicated, with a rollback plan", "milestone", 60),
    ("Sprint review", "With stakeholders, once the rhythm holds", "ceremony", 75),
    ("Metric baselines", "Cycle time, deployment frequency, change failure rate, escaped defects", "metric", 90),
    ("Group learning sessions", "Short team presentations on topics flagged in dev syncs", "ceremony", 100),
    ("Rotate facilitation, set metric targets", "The team runs some ceremonies and picks its own targets", "milestone", 120),
]

RACI = ["Backlog priority", "Technical design", "Release go/no-go", "QA sign-off", "Production changes"]

METRICS = [
    ("Cycle time", "days", "From started to done, per story", False),
    ("Deployment frequency", "per week", "Production deployments", True),
    ("Change failure rate", "%", "Share of releases needing a fix or rollback", False),
    ("Escaped defects", "per sprint", "Bugs found after release", False),
    ("Meetings per week (team)", "meetings", "A weekly tally from the team's calendars; the cost of coordination", False),
    ("Meetings rescheduled", "%", "Share of planned meetings moved or cancelled each week; planning to plan", False),
]


def _empty(conn, table: str) -> bool:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def load_starter(conn, source: str) -> dict:
    loaded = {}
    if _empty(conn, "roadmap_items"):
        for position, (title, description, kind, day) in enumerate(ROADMAP):
            models.roadmap_items.create(
                conn, {"title": title, "description": description, "kind": kind, "target_day": day, "position": position}, source
            )
        loaded["roadmap_items"] = len(ROADMAP)
    if _empty(conn, "raci_decisions"):
        for position, decision in enumerate(RACI):
            models.raci_decisions.create(conn, {"decision": decision, "position": position}, source)
        loaded["raci_decisions"] = len(RACI)
    if _empty(conn, "metrics"):
        for name, unit, method, higher in METRICS:
            models.metrics.create(conn, {"name": name, "unit": unit, "method": method, "higher_is_better": higher}, source)
        loaded["metrics"] = len(METRICS)
    return loaded
