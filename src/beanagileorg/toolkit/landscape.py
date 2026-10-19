"""Business landscape: products and services, the organization by department, and a strengths/weaknesses/opportunities/threats view of each."""

from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
SUBJECTS = {"offering": models.offerings, "department": models.departments}


def _swot_counts(conn) -> dict:
    out = {}
    for r in conn.execute("SELECT subject_type, subject_id, quadrant, COUNT(*) n FROM assessments WHERE status != 'closed' GROUP BY 1, 2, 3"):
        out.setdefault((r["subject_type"], r["subject_id"]), {q: 0 for q in models.QUADRANTS})[r["quadrant"]] = r["n"]
    return out


def _names(conn, table: str, ids: list[int]) -> list[dict]:
    if not ids:
        return []
    rows = conn.execute(f"SELECT id, name FROM {table} WHERE id IN ({','.join('?' * len(ids))}) ORDER BY name", ids).fetchall()
    return [dict(r) for r in rows]


def _check_parent(conn, dept_id: int | None, parent_id) -> None:
    seen = set()
    while parent_id is not None:
        if parent_id == dept_id or parent_id in seen:
            raise HTTPException(400, "A department can't sit inside itself or one of its own teams.")
        seen.add(parent_id)
        row = conn.execute("SELECT parent_id FROM departments WHERE id = ?", (parent_id,)).fetchone()
        if row is None:
            raise HTTPException(400, "That parent department doesn't exist.")
        parent_id = row["parent_id"]


# ---- departments ----


@router.post("/api/departments", status_code=201)
def create_department(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    _check_parent(conn, None, body.get("parent_id"))
    return models.departments.visible(models.departments.create(conn, body, viewer.source), viewer)


@router.patch("/api/departments/{dept_id}")
def update_department(dept_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if "parent_id" in body:
        _check_parent(conn, dept_id, body["parent_id"])
    dept = models.departments.update(conn, dept_id, body, viewer.source)
    if dept is None:
        raise HTTPException(404, "No such department.")
    return models.departments.visible(dept, viewer)


def _delete_subject(conn, kind: str, record_id: int, viewer: Viewer) -> None:
    require_write(viewer)
    if not SUBJECTS[kind].fetch(conn, record_id):
        raise HTTPException(404, f"No such {kind}.")
    for a in models.assessments.fetch_all(conn, "subject_type = ? AND subject_id = ?", (kind, record_id)):
        models.assessments.delete(conn, a["id"], viewer.source)
    SUBJECTS[kind].delete(conn, record_id, viewer.source)


@router.delete("/api/departments/{dept_id}", status_code=204)
def delete_department(dept_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Teams under it move up to its parent; its assessments go with it."""
    dept = models.departments.fetch(conn, dept_id)
    if dept:
        for child in models.departments.fetch_all(conn, "parent_id = ?", (dept_id,)):
            models.departments.update(conn, child["id"], {"parent_id": dept["parent_id"]}, viewer.source)
    _delete_subject(conn, "department", dept_id, viewer)


@router.delete("/api/offerings/{offering_id}", status_code=204)
def delete_offering(offering_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    _delete_subject(conn, "offering", offering_id, viewer)


@router.get("/api/landscape/org")
def org(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    depts = models.departments.visible_all(models.departments.fetch_all(conn), viewer)
    people = [p for p in models.people.fetch_all(conn) if p["active"]]
    offers = models.offerings.fetch_all(conn, "status != 'retired'")
    counts = _swot_counts(conn) if viewer.floor == Level.PRIVATE else {}
    nodes = {}
    for d in depts:
        nodes[d["id"]] = {
            **d,
            "people": [{"id": p["id"], "name": p["name"], "role": p["role"]} for p in people if p["department_id"] == d["id"]],
            "offerings": [{"id": o["id"], "name": o["name"]} for o in offers if o["department_id"] == d["id"]],
            "swot": counts.get(("department", d["id"])),
            "children": [],
        }
    roots = []
    for d in depts:
        parent = nodes.get(d["parent_id"])
        (parent["children"] if parent else roots).append(nodes[d["id"]])
    return {"tree": roots, "unassigned": [{"id": p["id"], "name": p["name"], "role": p["role"]} for p in people if not p["department_id"]]}


# ---- offerings ----


@router.get("/api/landscape/offerings")
def offering_list(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    counts = _swot_counts(conn) if viewer.floor == Level.PRIVATE else {}
    out = []
    for o in models.offerings.visible_all(models.offerings.fetch_all(conn), viewer):
        out.append({**o, "systems": _names(conn, "systems", o["system_ids"]), "vendors": _names(conn, "vendors", o["vendor_ids"]),
                    "swot": counts.get(("offering", o["id"]))})
    return out


# ---- one subject, and the whole matrix ----


@router.get("/api/landscape/{kind}/{record_id}")
def subject(kind: str, record_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if kind not in SUBJECTS:
        raise HTTPException(404, "Not a landscape subject.")
    rec = SUBJECTS[kind].fetch(conn, record_id)
    if rec is None:
        raise HTTPException(404, f"No such {kind}.")
    out = {"kind": kind, "subject": SUBJECTS[kind].visible(rec, viewer)}
    if kind == "offering":
        out["systems"] = _names(conn, "systems", rec["system_ids"])
        out["vendors"] = _names(conn, "vendors", rec["vendor_ids"])
    else:
        out["children"] = [{"id": d["id"], "name": d["name"], "kind": d["kind"]} for d in models.departments.fetch_all(conn, "parent_id = ?", (record_id,))]
        out["people"] = [{"id": p["id"], "name": p["name"], "role": p["role"]} for p in models.people.fetch_all(conn, "department_id = ? AND active = 1", (record_id,))]
        out["offerings"] = [{"id": o["id"], "name": o["name"], "kind": o["kind"]} for o in models.offerings.fetch_all(conn, "department_id = ?", (record_id,))]
    chain, parent = [], rec.get("department_id") if kind == "offering" else rec.get("parent_id")
    while parent is not None and len(chain) < 20:
        d = models.departments.fetch(conn, parent)
        if d is None:
            break
        chain.insert(0, {"id": d["id"], "name": d["name"]})
        parent = d["parent_id"]
    out["path"] = chain
    if viewer.floor == Level.PRIVATE:
        items = models.assessments.fetch_all(conn, "subject_type = ? AND subject_id = ?", (kind, record_id))
        out["assessments"] = {q: [a for a in items if a["quadrant"] == q] for q in models.QUADRANTS}
        out["priorities"] = priorities(items)
    return out


def priorities(items: list[dict]) -> list[dict]:
    """TOWS: start outside. Each open threat or opportunity, with the weaknesses and strengths that bear on it.
    A threat you're weak against needs blunting; an opportunity you're strong for is worth pursuing."""
    by_target: dict[int, list[dict]] = {}
    for a in items:
        if a.get("bears_on_id") and a["status"] != "closed":
            by_target.setdefault(a["bears_on_id"], []).append({"id": a["id"], "title": a["title"], "quadrant": a["quadrant"]})
    out = []
    for a in items:
        if a["quadrant"] not in ("threat", "opportunity") or a["status"] == "closed":
            continue
        linked = by_target.get(a["id"], [])
        weak = [x for x in linked if x["quadrant"] == "weakness"]
        strong = [x for x in linked if x["quadrant"] == "strength"]
        urgent = bool(weak) if a["quadrant"] == "threat" else bool(strong)
        out.append({"id": a["id"], "title": a["title"], "move": "blunt" if a["quadrant"] == "threat" else "pursue", "urgent": urgent,
                    "weaknesses": weak, "strengths": strong, "subject_type": a["subject_type"], "subject_id": a["subject_id"],
                    "subject_name": a.get("subject_name"), "confidence": a["confidence"], "roadmap_item_id": a["roadmap_item_id"]})
    rank = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda p: (not p["urgent"], not (p["weaknesses"] or p["strengths"]), rank.get(p["confidence"], 3), p["id"]))
    return out


@router.get("/api/landscape/swot")
def swot(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"private": True, "quadrants": {}}
    items = models.assessments.fetch_all(conn, "status != 'closed'")
    return {"private": False, "quadrants": {q: [a for a in items if a["quadrant"] == q] for q in models.QUADRANTS}, "priorities": priorities(items)}


# ---- acting on an assessment ----


def _assessment(conn, assessment_id: int) -> dict:
    a = models.assessments.fetch(conn, assessment_id)
    if a is None:
        raise HTTPException(404, "No such assessment.")
    return a


@router.post("/api/assessments/{assessment_id}/to-roadmap", status_code=201)
def to_roadmap(assessment_id: int, priority: bool = False, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The roadmap is shareable, so only the title goes across; the evidence stays here. As a priority, a threat
    becomes "Blunt: ..." and an opportunity "Pursue: ..."."""
    require_write(viewer)
    a = _assessment(conn, assessment_id)
    if a["roadmap_item_id"]:
        raise HTTPException(409, "This is already on the roadmap.")
    title = a["title"]
    if priority and a["quadrant"] in ("threat", "opportunity"):
        title = f"{'Blunt' if a['quadrant'] == 'threat' else 'Pursue'}: {title}"
    item = models.roadmap_items.create(conn, {"title": title}, viewer.source)
    return models.assessments.update(conn, assessment_id, {"roadmap_item_id": item["id"], "status": "acted on"}, viewer.source)


@router.post("/api/assessments/{assessment_id}/to-risk", status_code=201)
def to_risk(assessment_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    a = _assessment(conn, assessment_id)
    if a["risk_id"]:
        raise HTTPException(409, "This is already logged as a risk.")
    level = {"high": "high", "medium": "medium", "low": "low"}[a["confidence"]]
    risk = models.risks.create(conn, {"title": a["title"], "level": level, "notes": a["evidence"]}, viewer.source)
    return models.assessments.update(conn, assessment_id, {"risk_id": risk["id"], "status": "acted on"}, viewer.source)
