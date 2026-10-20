"""The delivery scorecard and the day-90 summary for your manager.

The scorecard puts the six-month bar in numbers: sprint commitments kept, how releases went, and each metric against
its baseline and target. The day-90 summary draws on all three First 90 days tracks (your plan, your team, new
people) and the scorecard, at the level your manager may see.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()
MANAGER = Viewer(floor=Level.PRESENTABLE, source="day90")


def _metric_status(m: dict) -> str:
    latest, base, target = m.get("latest"), m.get("baseline"), m.get("target")
    if latest is None:
        return "no reading"
    if target is None:
        return "tracking"
    up = m.get("higher_is_better") is not False
    if (latest >= target) if up else (latest <= target):
        return "met"
    if base is not None and ((latest > base) if up else (latest < base)):
        return "improving"
    if base is not None and latest == base:
        return "flat"
    return "behind" if base is not None else "tracking"


def scorecard(conn, viewer: Viewer) -> dict:
    t = today()
    plans = [p for p in models.sprint_plans.fetch_all(conn, "status = 'closed' AND committed_points IS NOT NULL") if p.get("committed_points")]
    plans.sort(key=lambda p: p.get("closed_on") or "", reverse=True)
    sprints = []
    for p in plans[:6]:
        sp = models.sprints.fetch(conn, p["sprint_id"])
        pct = round(100 * (p.get("completed_points") or 0) / p["committed_points"])
        sprints.append({"number": sp["number"] if sp else None, "committed": p["committed_points"], "completed": p.get("completed_points") or 0, "kept_pct": pct, "kept": pct >= 90})
    since = (t - timedelta(days=90)).isoformat()
    rel = [r for r in models.releases.visible_all(models.releases.fetch_all(conn, "status = 'released' AND released_on >= ?", (since,)), viewer)]
    outcomes = {o: sum(1 for r in rel if r.get("outcome") == o) for o in models.RELEASE_OUTCOMES}
    judged = sum(outcomes.values())
    metrics = [{"id": m["id"], "name": m["name"], "unit": m.get("unit"), "baseline": m.get("baseline"), "latest": m.get("latest"), "target": m.get("target"),
                "higher_is_better": m.get("higher_is_better"), "status": _metric_status(m)}
               for m in models.metrics.visible_all(models.metrics.fetch_all(conn), viewer)]
    return {
        "sprints": list(reversed(sprints)),
        "commitments_kept": f"{sum(1 for s in sprints if s['kept'])} of {len(sprints)}" if sprints else None,
        "releases": {"count": len(rel), "outcomes": outcomes, "change_failure_pct": round(100 * (judged - outcomes["clean"]) / judged) if judged else None},
        "metrics": metrics,
    }


@router.get("/api/scorecard")
def get_scorecard(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return scorecard(conn, viewer)


def _scorecard_md(sc: dict) -> list[str]:
    md = ["## Delivery scorecard"]
    if sc["sprints"]:
        md.append(f"- Sprint commitments kept (90% or more of committed points): {sc['commitments_kept']} recent sprints ("
                  + ", ".join(f"sprint {s['number']}: {s['kept_pct']}%" for s in sc["sprints"]) + ")")
    r = sc["releases"]
    if r["count"]:
        md.append(f"- Releases in the last 90 days: {r['count']}, of which {r['outcomes']['clean']} clean"
                  + (f"; change failure rate {r['change_failure_pct']}%" if r["change_failure_pct"] is not None else ""))
    for m in sc["metrics"]:
        unit = f" {m['unit']}" if m.get("unit") else ""
        fmt = lambda v: "–" if v is None else f"{v:g}{unit}"
        md.append(f"- {m['name']}: baseline {fmt(m['baseline'])}, now {fmt(m['latest'])}, target {fmt(m['target'])} ({m['status']})")
    if len(md) == 1:
        md.append("- [Placeholder: baselines are being set]")
    return md


def day90_summary(conn) -> dict:
    """At the level your manager may see: plans, early wins, mandate outcomes, the listening tour, the team, new people, the scorecard."""
    from .first90 import day_number, start_date, team_track

    start = start_date(conn)
    day = day_number(start)
    lines = [f"# Day-90 summary{f' (day {day})' if day else ''}", "",
             "[Placeholder: one paragraph on where things stand against what we agreed, in plain words.]", ""]
    plans = models.plans.fetch_all(conn)
    items = models.plan_items.fetch_all(conn)
    if plans:
        lines.append("## The plan")
        for p in sorted(plans, key=lambda p: p["horizon_days"] or 0):
            mine = [i for i in items if i["plan_id"] == p["id"] and i["status"] != "dropped"]
            lines.append(f"- {p['title']}: {sum(1 for i in mine if i['status'] == 'done')} of {len(mine)} done")
        wins = [i for i in items if i.get("early_win") and i["status"] != "dropped"]
        if wins:
            lines += ["", "## Early wins"] + [f"- {i['title']}: {i['status']}" for i in wins]
        lines.append("")
    mandate = next(iter(models.mandates.fetch_all(conn, "mine = 1")), None)
    if mandate:
        outcomes = models.mandate_items.fetch_all(conn, "mandate_id = ? AND kind = 'outcome'", (mandate["id"],))
        if outcomes:
            lines += ["## Mandate outcomes"] + [f"- {o['text']}: {o['status']}" + (f" (due day {o['due_day']})" if o.get("due_day") else "") for o in outcomes] + [""]
    done = conn.execute("SELECT COUNT(*) FROM interviews WHERE status = 'done'").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM interviews").fetchone()[0]
    if total:
        lines += ["## Listening tour", f"- {done} of {total} conversations held", ""]
    team = team_track(conn)
    if team["people"]:
        lines += ["## The team"] + [f"- {p['name']}: {p['done']} of {p['total']} first-90 milestones done" + (f", {p['late']} late" if p.get("late") else "") for p in team["people"]] + [""]
    obs = models.onboardings.visible_all(models.onboardings.fetch_all(conn), MANAGER)
    if obs:
        lines += ["## New people"] + [f"- {o.get('person_name')}: onboarding {o.get('done_count')} of {o.get('total')} done ({o['status']})" for o in obs] + [""]
    lines += _scorecard_md(scorecard(conn, MANAGER)) + ["", "## Next 90 days", "- [Placeholder: the priorities for days 91 to 180, and what I need from you]"]
    return {"title": f"Day-90 summary{f' (day {day})' if day else ''}", "markdown": "\n".join(lines) + "\n", "day": day}


@router.get("/api/first90/day90-summary")
def get_day90(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    return day90_summary(conn)


@router.post("/api/first90/day90-summary/export")
def export_day90(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = day90_summary(conn)
    log_export(conn, "day90:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out
