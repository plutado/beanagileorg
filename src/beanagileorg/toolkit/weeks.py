"""Weeks and sprint weeks: which week a date falls in, which sprint, and which week of that sprint.

Every report and the activity feed use these, so a date always lands in the same week everywhere.
"""

from datetime import date, timedelta

from . import models

WEEK_START_KEY = "reports.week_start"  # 0 = Monday ... 6 = Sunday
REPORT_DAY_KEY = "reports.weekly_day"  # the weekday the weekly report is usually sent
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _int_setting(conn, key: str, default: int) -> int:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    try:
        return int(row["value"]) if row else default
    except ValueError:
        return default


def week_start_day(conn) -> int:
    return _int_setting(conn, WEEK_START_KEY, 0)


def report_day(conn) -> int:
    return _int_setting(conn, REPORT_DAY_KEY, 4)


def week_bounds(d: date, start_day: int = 0) -> tuple[date, date]:
    start = d - timedelta(days=(d.weekday() - start_day) % 7)
    return start, start + timedelta(days=6)


def sprint_for(conn, d: date, team_id: int | None = None) -> dict | None:
    """The team's sprint running on that date (your team by default)."""
    from .reporting import my_team_id

    team = team_id or my_team_id(conn)
    iso = d.isoformat()
    found = models.sprints.fetch_all(conn, "team_id IS ? AND start_date <= ? AND (end_date IS NULL OR end_date >= ?)", (team, iso, iso))
    return found[0] if found else None


def sprint_weeks(sprint: dict) -> list[tuple[date, date]]:
    """A sprint split into seven-day weeks from its start. A two-week sprint gives week 1 and week 2."""
    if not sprint.get("start_date"):
        return []
    start = date.fromisoformat(sprint["start_date"])
    end = date.fromisoformat(sprint["end_date"]) if sprint.get("end_date") else start + timedelta(days=13)
    weeks, cur = [], start
    while cur <= end:
        weeks.append((cur, min(cur + timedelta(days=6), end)))
        cur += timedelta(days=7)
    return weeks


def sprint_week(sprint: dict, d: date) -> tuple[int, int] | None:
    weeks = sprint_weeks(sprint)
    for n, (s, e) in enumerate(weeks, 1):
        if s <= d <= e:
            return n, len(weeks)
    return None


def role_week(conn, d: date) -> int | None:
    from .routes import START_DATE_KEY

    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    if not row or not row["value"]:
        return None
    start = date.fromisoformat(row["value"])
    return (d - start).days // 7 + 1 if d >= start else None


def fmt(d: date) -> str:
    return f"{d.strftime('%b')} {d.day}"


def week_info(conn, d: date) -> dict:
    """Everything about the week a date falls in: its dates, its week in the role, and its sprint week."""
    start, end = week_bounds(d, week_start_day(conn))
    info = {
        "start": start.isoformat(), "end": end.isoformat(), "iso_week": start.isocalendar()[1],
        "label": f"Week of {fmt(start)} to {fmt(end)}, {end.year}", "role_week": role_week(conn, start), "sprint": None,
    }
    # The sprint this week mostly belongs to: the one running mid-week, else at either end.
    sprint = sprint_for(conn, start + timedelta(days=3)) or sprint_for(conn, start) or sprint_for(conn, end)
    if sprint:
        pos = sprint_week(sprint, start + timedelta(days=3)) or sprint_week(sprint, start) or sprint_week(sprint, end)
        info["sprint"] = {"id": sprint["id"], "number": sprint["number"], "goal": sprint.get("goal"),
                          "week": pos[0] if pos else None, "weeks": pos[1] if pos else None,
                          "label": f"Sprint {sprint['number']}" + (f", week {pos[0]} of {pos[1]}" if pos else "")}
    return info


def stamp(conn, d: date | str | None) -> dict | None:
    """The short week notation for one date, shown beside dated records: week, role week, sprint week."""
    if not d:
        return None
    d = date.fromisoformat(d) if isinstance(d, str) else d
    start, _ = week_bounds(d, week_start_day(conn))
    sprint = sprint_for(conn, d)
    pos = sprint_week(sprint, d) if sprint else None
    return {"week_start": start.isoformat(), "iso_week": start.isocalendar()[1], "role_week": role_week(conn, d),
            "sprint_number": sprint["number"] if sprint else None, "sprint_week": pos[0] if pos else None,
            "sprint_weeks": pos[1] if pos else None}
