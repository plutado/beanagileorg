"""The decision log: every decision recorded anywhere in the toolkit, in one list by date.

Decisions needed, architecture decisions, tech debt calls, change requests, release go or no-go, team changes kept or
dropped, and agreed mandates, each with who decided, how and what was decided, at the viewer's privacy level.
"""

from fastapi import APIRouter, Depends

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from . import models

router = APIRouter()
KINDS = ("decision", "architecture", "tech debt", "change request", "release", "team change", "mandate")


def _decided_on(conn, entity: str, rid: int, value: str) -> str | None:
    row = conn.execute("SELECT MAX(date(datetime(at, 'localtime'))) AS d FROM change_log WHERE entity = ? AND record_id = ? AND field = 'status' AND new_value = ?",
                       (entity, str(rid), value)).fetchone()
    return row["d"] if row else None


def decision_log(conn, viewer: Viewer) -> list[dict]:
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM people")}
    out = []

    def add(kind, when, title, decision, who=None, how=None, path=None):
        if title:
            out.append({"kind": kind, "date": when, "title": title, "decision": decision, "who": who, "how": how, "path": path})

    for d in models.decisions_needed.visible_all(models.decisions_needed.fetch_all(conn, "status = 'decided'"), viewer):
        add("decision", _decided_on(conn, "decision_needed", d["id"], "decided"), d["decision"], d.get("outcome"), names.get(d.get("from_id")), d.get("process"), "/risks")
    for a in models.arch_decisions.visible_all(models.arch_decisions.fetch_all(conn, "status IN ('accepted', 'superseded')"), viewer):
        add("architecture", a.get("date"), a["title"], a.get("decision"), names.get(a.get("decided_by_id")), None, "/architecture")
    debts = {d["id"]: d["title"] for d in models.tech_debt.visible_all(models.tech_debt.fetch_all(conn), viewer)}
    for x in models.debt_decisions.visible_all(models.debt_decisions.fetch_all(conn), viewer):
        add("tech debt", x["date"], debts.get(x["debt_id"]), x["decision"] + (f": {x['rationale']}" if x.get("rationale") else ""), x.get("decided_by"), None, "/debt")
    for c in models.change_requests.visible_all(models.change_requests.fetch_all(conn, "decision IS NOT NULL AND decision != ''"), viewer):
        add("change request", c.get("decided_on"), c["title"], c["decision"] + (f" ({c['decision_reason']})" if c.get("decision_reason") else ""), names.get(c.get("decided_by_id")), None, f"/changes/{c['id']}")
    for r in models.releases.visible_all(models.releases.fetch_all(conn, "decision IS NOT NULL AND decision != ''"), viewer):
        add("release", r.get("decided_on"), r["name"], r["decision"] + (f": {r['decision_notes']}" if r.get("decision_notes") else ""), names.get(r.get("decided_by_id")), None, f"/releases/{r['id']}")
    for t in models.team_changes.visible_all(models.team_changes.fetch_all(conn, "status IN ('adopted', 'dropped')"), viewer):
        add("team change", t.get("decided_on"), t["title"], t["status"] + (f": {t['outcome']}" if t.get("outcome") else ""), None, "reviewed with the team", "/first90/changes")
    for m in models.mandates.visible_all(models.mandates.fetch_all(conn, "status = 'agreed'"), viewer):
        add("mandate", m.get("agreed_on"), f"Mandate: {names.get(m['person_id'], '')}".strip(), "agreed", names.get(m.get("agreed_with_id")), None, "/first90/mandates")
    out.sort(key=lambda x: x["date"] or "", reverse=True)
    return out


@router.get("/api/decision-log")
def get_decision_log(kind: str | None = None, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    rows = decision_log(conn, viewer)
    return {"kinds": list(KINDS), "decisions": [r for r in rows if not kind or r["kind"] == kind]}
