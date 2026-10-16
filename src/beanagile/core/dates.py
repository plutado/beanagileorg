"""Date helpers shared by the apps: month arithmetic and recurring cadences."""

import calendar
from datetime import date, timedelta

CADENCES = ("weekly", "every two weeks", "monthly", "quarterly", "once")


def add_months(d: date, months: int) -> date:
    year, month = divmod(d.month - 1 + months, 12)
    year, month = d.year + year, month + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def next_occurrence(d: date, cadence: str) -> date | None:
    if cadence == "weekly":
        return d + timedelta(days=7)
    if cadence == "every two weeks":
        return d + timedelta(days=14)
    if cadence == "monthly":
        return add_months(d, 1)
    if cadence == "quarterly":
        return add_months(d, 3)
    return None
