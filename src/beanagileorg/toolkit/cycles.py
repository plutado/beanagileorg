"""90-day cycles: the first 90 days, then the same rhythm of planning, execution and review, cycle after cycle.

Each cycle covers a span of days in the role (90 by default, or matched to Program Increments). It has a focus and a
few goals, takes in the plan items and early wins due in its days, can link a Program Increment, and ends with a
review: the delivery scorecard kept as it stood, a mandate snapshot, what went well and what to change, and a
one-page summary for your manager.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()
LENGTH_KEY = "cycles.length_days"
DEFAULT_LENGTH = 90
MANAGER = Viewer(floor=Level.PRESENTABLE, source="cycle")


def length(conn) -> int:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (LENGTH_KEY,)).fetchone()
    return int(row["value"]) if row else DEFAULT_LENGTH


def bounds(n: int, size: int) -> tuple[int, int]:
    return (n - 1) * size + 1, n * size


def current(conn) -> tuple[int | None, int | None]:
    from .first90 import day_number, start_date
    day = day_number(start_date(conn))
    if not day or day < 1:
        return None, day
    return (day - 1) // length(conn) + 1, day


def ensure(conn, upto: int, source: str = "me") -> None:
    have = {r["number"] for r in conn.execute("SELECT number FROM cycles")}
    for n in range(1, upto + 1):
        if n not in have:
            models.cycles.create(conn, {"number": n}, source)


def _date(start: date | None, day: int) -> str | None:
    return (start + timedelta(days=day - 1)).isoformat() if start else None


def describe(conn, c: dict, viewer: Viewer, size: int, now_n: int | None) -> dict:
    from .first90 import start_date
    start = start_date(conn)
    lo, hi = bounds(c["number"], size)
    items = models.plan_items.visible_all(models.plan_items.fetch_all(conn, "due_day BETWEEN ? AND ? AND status != 'dropped'", (lo, hi)), viewer)
    pi = models.program_increments.fetch(conn, c["pi_id"]) if c.get("pi_id") else None
    state = "current" if now_n == c["number"] else "past" if now_n and c["number"] < now_n else "upcoming"
    return {**models.cycles.visible(c, viewer), "start_day": lo, "end_day": hi, "start_date": _date(start, lo), "end_date": _date(start, hi), "state": state,
            "items": [{"id": i["id"], "title": i["title"], "status": i["status"], "due_day": i["due_day"], "early_win": bool(i.get("early_win"))} for i in items],
            "done": sum(1 for i in items if i["status"] == "done"), "total": len(items),
            "pi": {"id": pi["id"], "number": pi["number"]} if pi else None}


@router.get("/api/cycles/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    size = length(conn)
    n, day = current(conn)
    if viewer.floor == Level.PRIVATE and not viewer.guarded:
        ensure(conn, max(2, (n or 1) + 1), viewer.source)
    rows = models.cycles.fetch_all(conn)
    return {"length_days": size, "day": day, "current": n, "day_in_cycle": ((day - 1) % size) + 1 if n else None,
            "cycles": [describe(conn, c, viewer, size, n) for c in rows],
            "pis": [{"id": p["id"], "number": p["number"]} for p in models.program_increments.fetch_all(conn)]}


@router.put("/api/cycles/settings")
def settings(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Cycle length in days: 90 by default, or the length of your Program Increments (between 8 and 17 weeks)."""
    require_write(viewer)
    try:
        days = int(body.get("length_days"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, "Give the cycle length in days.") from exc
    if not 56 <= days <= 120:
        raise HTTPException(400, "A cycle is between 56 and 120 days (8 to 17 weeks).")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (LENGTH_KEY, str(days)))
    return {"length_days": days}


def _cycle(conn, n: int) -> dict:
    rows = models.cycles.fetch_all(conn, "number = ?", (n,))
    if not rows:
        raise HTTPException(404, "No such cycle.")
    return rows[0]


@router.post("/api/cycles/{n}/review")
def review(n: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Close the cycle: keep the scorecard as it stands, snapshot the mandate, and note what went well and what to change."""
    from .mandates import snapshot
    from .scorecard import scorecard

    require_write(viewer)
    c = _cycle(conn, n)
    data = {"status": "reviewed", "reviewed_on": today().isoformat(), "scorecard": scorecard(conn, MANAGER)}
    for k in ("went_well", "to_change", "review_notes"):
        if k in body:
            data[k] = body[k] or None
    mine = next(iter(models.mandates.fetch_all(conn, "mine = 1")), None)
    if mine:
        snapshot(conn, mine["id"], f"Cycle {n} review", viewer)
    ensure(conn, n + 1, viewer.source)
    nxt = _cycle(conn, n + 1)
    if body.get("next_focus") and not nxt.get("focus"):
        models.cycles.update(conn, nxt["id"], {"focus": body["next_focus"]}, viewer.source)
    return models.cycles.update(conn, c["id"], data, viewer.source)


def summary(conn, n: int) -> dict:
    """One page for your manager: the cycle's focus and goals, plan items and wins, mandate outcomes, scorecard, and what's next."""
    from .scorecard import _scorecard_md, scorecard

    size = length(conn)
    now_n, _ = current(conn)
    c = describe(conn, _cycle(conn, n), MANAGER, size, now_n)
    lines = [f"# Cycle {n} summary (days {c['start_day']} to {c['end_day']})", "",
             "[Placeholder: one paragraph on where things stand against what we agreed for this cycle.]", ""]
    if c.get("focus"):
        lines += ["## Focus", "", c["focus"], ""]
    if c.get("goals"):
        lines += ["## Goals"] + [f"- {g}" for g in c["goals"]] + [""]
    if c["items"]:
        lines += [f"## The plan: {c['done']} of {c['total']} done"] + [f"- {i['title']}: {i['status']}" + (" (early win)" if i["early_win"] else "") for i in c["items"]] + [""]
    mine = next(iter(models.mandates.fetch_all(conn, "mine = 1")), None)
    if mine:
        outs = models.mandate_items.fetch_all(conn, "mandate_id = ? AND kind = 'outcome'", (mine["id"],))
        if outs:
            lines += ["## Mandate outcomes"] + [f"- {o['text']}: {o['status']}" for o in outs] + [""]
    sc = c.get("scorecard") if c.get("status") == "reviewed" and c.get("scorecard") else scorecard(conn, MANAGER)
    lines += _scorecard_md(sc) + [""]
    if c.get("went_well") or c.get("to_change"):
        lines += ["## Looking back"] + ([f"- Went well: {c['went_well']}"] if c.get("went_well") else []) + ([f"- To change: {c['to_change']}"] if c.get("to_change") else []) + [""]
    nxt = next(iter(models.cycles.fetch_all(conn, "number = ?", (n + 1,))), None)
    lines += ["## Next cycle", f"- {nxt['focus']}" if nxt and nxt.get("focus") else "- [Placeholder: the focus for the next 90 days, and what I need from you]"]
    return {"title": f"Cycle {n} summary", "markdown": "\n".join(lines) + "\n"}


@router.get("/api/cycles/{n}/summary")
def get_summary(n: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    return summary(conn, n)


@router.post("/api/cycles/{n}/summary/export")
def export_summary(n: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = summary(conn, n)
    log_export(conn, "cycle:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out


def cycles_due(conn) -> dict | None:
    """For Today: the cycle review in the last two weeks of a cycle, and a focus to set early in a new one."""
    n, day = current(conn)
    if not n:
        return None
    size = length(conn)
    lo, hi = bounds(n, size)
    row = next(iter(models.cycles.fetch_all(conn, "number = ?", (n,))), None)
    out = {"number": n, "day_in_cycle": day - lo + 1, "length": size}
    out["review_due"] = hi - day <= 13 and not (row and row["status"] == "reviewed")
    out["focus_needed"] = n > 1 and day - lo <= 13 and not (row and row.get("focus"))
    return out if out["review_due"] or out["focus_needed"] else None
