"""Architecture: systems and tools, the integrations between them, decision records, guides and the system map."""

from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer
from beanagile.core.privacy import Viewer

from . import models
from .routes import require_write

router = APIRouter()


def _check_integration(conn, body: dict, current: dict | None = None) -> None:
    merged = {**(current or {}), **body}
    ends = [merged.get("from_id"), merged.get("to_id"), merged.get("via_id")]
    for sid in filter(None, ends):
        if not models.systems.fetch(conn, sid):
            raise HTTPException(400, "That system doesn't exist.")
    if merged.get("from_id") == merged.get("to_id"):
        raise HTTPException(400, "An integration needs two different systems.")
    if merged.get("via_id") and merged["via_id"] in (merged.get("from_id"), merged.get("to_id")):
        raise HTTPException(400, "The middle system has to be a third system, such as MuleSoft.")


@router.post("/api/integrations", status_code=201)
def create_integration(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _check_integration(conn, body)
    return models.integrations.visible(models.integrations.create(conn, body, viewer.source), viewer)


@router.patch("/api/integrations/{integration_id}")
def update_integration(integration_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    current = models.integrations.fetch(conn, integration_id)
    if current is None:
        raise HTTPException(404, "No such integration.")
    _check_integration(conn, body, current)
    return models.integrations.visible(models.integrations.update(conn, integration_id, body, viewer.source), viewer)


@router.post("/api/arch-decisions", status_code=201)
def create_decision(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Decision records are numbered in order and never renumbered."""
    require_write(viewer)
    nxt = conn.execute("SELECT COALESCE(MAX(number), 0) + 1 FROM arch_decisions").fetchone()[0]
    body = {**body, "number": nxt}
    body.setdefault("date", date.today().isoformat())
    return models.arch_decisions.visible(models.arch_decisions.create(conn, body, viewer.source), viewer)


@router.post("/api/guides", status_code=201)
def create_guide(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    return models.guides.visible(models.guides.create(conn, {**body, "updated": date.today().isoformat()}, viewer.source), viewer)


@router.patch("/api/guides/{guide_id}")
def update_guide(guide_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    guide = models.guides.update(conn, guide_id, {**body, "updated": date.today().isoformat()}, viewer.source)
    if guide is None:
        raise HTTPException(404, "No such guide.")
    return models.guides.visible(guide, viewer)


@router.get("/api/architecture/map")
def system_map(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    systems = [s for s in models.systems.fetch_all(conn) if s["lifecycle"] != "retired"]
    ids = {s["id"] for s in systems}
    edges = [i for i in models.integrations.fetch_all(conn, "status != 'retired'") if i["from_id"] in ids and i["to_id"] in ids]
    linked = {x for e in edges for x in (e["from_id"], e["to_id"], e["via_id"]) if x}
    # Tools only appear on the map when something connects to them.
    nodes = [s for s in systems if s["kind"] != "tool" or s["id"] in linked]
    keep = ("id", "name", "kind", "category", "criticality", "lifecycle")
    return {
        "nodes": [{k: s[k] for k in keep} for s in nodes],
        "edges": [{k: e[k] for k in ("id", "name", "from_id", "to_id", "via_id", "pattern", "direction", "status", "criticality", "data")} for e in edges],
    }


@router.get("/api/architecture/summary")
def summary(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    systems = [s for s in models.systems.fetch_all(conn) if s["lifecycle"] != "retired"]
    live = models.integrations.fetch_all(conn, "status != 'retired'")
    gaps = []
    for s in systems:
        missing = [label for key, label in (("owner_id", "owner"), ("description", "description"), ("docs_link", "docs link")) if not s[key]]
        if s["kind"] != "tool" and missing:
            gaps.append({"id": s["id"], "name": s["name"], "missing": missing, "criticality": s["criticality"]})
    gaps.sort(key=lambda g: ({"high": 0, "medium": 1, "low": 2}.get(g["criticality"], 3), g["name"]))
    by_kind = {k: sum(s["kind"] == k for s in systems) for k in models.SYSTEM_KINDS}
    return {
        "by_kind": by_kind,
        "integrations": len(live),
        "by_pattern": {p: sum(i["pattern"] == p for i in live) for p in models.INTEGRATION_PATTERNS if any(i["pattern"] == p for i in live)},
        "unowned_integrations": [{"id": i["id"], "name": i["name"]} for i in live if not i["owner_id"]],
        "documentation_gaps": gaps,
        "decisions": {s: conn.execute("SELECT COUNT(*) FROM arch_decisions WHERE status = ?", (s,)).fetchone()[0] for s in models.ADR_STATUS},
    }


@router.get("/api/architecture/system/{system_id}")
def system_detail(system_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    system = models.systems.fetch(conn, system_id)
    if system is None:
        raise HTTPException(404, "No such system.")
    links = models.integrations.fetch_all(conn, "from_id = ? OR to_id = ? OR via_id = ?", (system_id,) * 3)
    offerings = [o for o in models.offerings.fetch_all(conn) if system_id in o["system_ids"]]
    decisions = [d for d in models.arch_decisions.fetch_all(conn) if system_id in d["system_ids"]]
    guides = [g for g in models.guides.fetch_all(conn) if system_id in g["system_ids"]]
    cases = conn.execute("SELECT COUNT(*) FROM test_cases WHERE system_id = ? AND active = 1", (system_id,)).fetchone()[0]
    suites = models.test_suites.fetch_all(conn, "system_id = ?", (system_id,))
    return {
        "system": models.systems.visible(system, viewer),
        "outbound": models.integrations.visible_all([i for i in links if i["from_id"] == system_id], viewer),
        "inbound": models.integrations.visible_all([i for i in links if i["to_id"] == system_id], viewer),
        "carries": models.integrations.visible_all([i for i in links if i["via_id"] == system_id], viewer),
        "offerings": [{"id": o["id"], "name": o["name"]} for o in offerings],
        "decisions": [{"id": d["id"], "number": d["number"], "title": d["title"], "status": d["status"]} for d in decisions],
        "guides": [{"id": g["id"], "title": g["title"]} for g in guides],
        "testing": {"manual_cases": cases, "suites": [{"id": s["id"], "name": s["name"], "kind": s["kind"], "last_result": s["last_result"], "coverage": s["coverage"]} for s in suites]},
    }
