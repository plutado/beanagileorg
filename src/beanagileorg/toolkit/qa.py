"""QA resources: the manual test library, test runs, automated suites, regression plans and the definition of done."""

import json
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import create_action, require_write

router = APIRouter()
DOD_KEY = "qa.definition_of_done"
# A generic starting point the team edits; nothing here is specific to any company.
STARTER_DOD = [
    "Acceptance criteria met and checked by the product manager",
    "Code reviewed by another developer",
    "Unit tests written and passing in CI",
    "Smoke tests for the affected area pass",
    "QA sign-off recorded",
    "Release notes and support notes updated",
    "Deployed to production, or ready for the next release",
]
CASE_FIELDS = ("title", "system_name", "area", "priority", "preconditions", "steps", "expected", "owner_name")


def _today() -> str:
    return date.today().isoformat()


def _run_or_404(conn, run_id: int) -> dict:
    run = models.test_runs.fetch(conn, run_id)
    if run is None:
        raise HTTPException(404, "No such test run.")
    return run


# ---- runs ----


@router.post("/api/test-runs", status_code=201)
def start_run(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Start a run with a result row per case: listed case_ids, a regression plan's cases, or every active case of a kind."""
    require_write(viewer)
    body = dict(body)
    case_ids = body.pop("case_ids", None)
    select = body.pop("select", None)
    system_id = body.pop("system_id", None)
    plan = None
    if body.get("plan_id"):
        plan = models.regression_plans.fetch(conn, body["plan_id"])
        if plan is None:
            raise HTTPException(400, "That regression plan doesn't exist.")
        body.setdefault("kind", "regression")
    if case_ids is None:
        if plan is not None and plan["case_ids"]:
            case_ids = plan["case_ids"]
        else:
            kinds = {"smoke": ("smoke", "smoke and regression"), "regression": ("regression", "smoke and regression")}.get(select or body.get("kind"), models.TEST_KINDS)
            cases = [c for c in models.test_cases.fetch_all(conn, "active = 1") if c["kind"] in kinds and (system_id is None or c["system_id"] == system_id)]
            case_ids = [c["id"] for c in cases]
    active = {r["id"] for r in conn.execute("SELECT id FROM test_cases WHERE active = 1")}
    case_ids = [c for c in dict.fromkeys(case_ids) if c in active]
    if not case_ids:
        raise HTTPException(400, "No active test cases match. Add cases to the library first.")
    body.setdefault("date", _today())
    run = models.test_runs.create(conn, body, viewer.source)
    for cid in case_ids:
        models.test_results.create(conn, {"run_id": run["id"], "case_id": cid}, viewer.source)
    return models.test_runs.visible(models.test_runs.fetch(conn, run["id"]), viewer)


@router.get("/api/test-runs/{run_id}/board")
def run_board(run_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    run = models.test_runs.visible(_run_or_404(conn, run_id), viewer)
    cases = {c["id"]: c for c in models.test_cases.fetch_all(conn)}
    results = []
    for r in models.test_results.fetch_all(conn, "run_id = ?", (run_id,)):
        c = cases.get(r["case_id"], {})
        results.append({**r, "case": {k: c.get(k) for k in CASE_FIELDS}})
    results.sort(key=lambda r: (r["case"]["system_name"] or "~", r["case"]["area"] or "", r["case"]["title"] or ""))
    return {"run": run, "results": results}


@router.post("/api/test-results/{result_id}/follow-up", status_code=201)
def result_follow_up(result_id: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A failed or blocked case becomes a dev-sync item tied to the run's sprint."""
    require_write(viewer)
    result = models.test_results.fetch(conn, result_id)
    if result is None:
        raise HTTPException(404, "No such result.")
    if result["action_item_id"]:
        raise HTTPException(409, "This already has a dev-sync item.")
    run = models.test_runs.fetch(conn, result["run_id"])
    case = models.test_cases.fetch(conn, result["case_id"])
    verb = "failed" if result["result"] == "fail" else "was blocked" if result["result"] == "blocked" else "needs a look"
    item = create_action(
        {"concern": f"{case['title']} {verb} in {run['name']}", "origin": "testing", "sprint_id": run["sprint_id"],
         "owner_id": body.get("owner_id") or case["owner_id"], "notes": result["notes"]},
        viewer, conn,
    )
    models.test_results.update(conn, result_id, {"action_item_id": item["id"]}, viewer.source)
    return item


def build_summary(conn, run_id: int) -> dict:
    run = _run_or_404(conn, run_id)
    cases = {c["id"]: c for c in models.test_cases.fetch_all(conn)}
    results = models.test_results.fetch_all(conn, "run_id = ?", (run_id,))
    label = lambda r: cases[r["case_id"]]["title"] + (f" ({cases[r['case_id']]['system_name']})" if cases[r["case_id"]]["system_name"] else "")
    lines = [f"# {run['name']}", "", f"{run['date'] or ''} · {run['kind']}" + (f" · {run['environment']}" if run["environment"] else "") + (f" · release {run['release']}" if run["release"] else ""), "",
             f"**{run['passed']} passed, {run['failed']} failed, {run['blocked']} blocked, {run['not_run']} not run** of {run['total']}.", ""]
    for result, title in (("fail", "Failed"), ("blocked", "Blocked"), ("not run", "Not run")):
        chosen = [r for r in results if r["result"] == result]
        if chosen:
            lines += [f"## {title}"] + [f"- {label(r)}" + (f": {r['notes']}" if r["notes"] else "") for r in chosen] + [""]
    return {"run_id": run_id, "markdown": "\n".join(lines).rstrip() + "\n"}


@router.get("/api/test-runs/{run_id}/summary")
def run_summary(run_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_summary(conn, run_id)


# ---- definition of done ----


def _dod(conn) -> list[str]:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (DOD_KEY,)).fetchone()
    return json.loads(row["value"]) if row else []


@router.get("/api/qa/definition-of-done")
def get_dod(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"items": _dod(conn)}


@router.put("/api/qa/definition-of-done")
def put_dod(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    items = [i.strip() for i in body.get("items", []) if isinstance(i, str) and i.strip()]
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (DOD_KEY, json.dumps(items)))
    return {"items": items}


@router.post("/api/qa/definition-of-done/starter")
def starter_dod(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if _dod(conn):
        raise HTTPException(409, "There's already a definition of done. Edit it instead.")
    return put_dod({"items": STARTER_DOD}, viewer, conn)


# ---- overview ----


@router.get("/api/qa/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    today = _today()
    cases = [c for c in models.test_cases.fetch_all(conn) if c["active"]]
    suites = models.test_suites.fetch_all(conn)
    covered = [s["coverage"] for s in suites if s["coverage"] is not None]
    plans = [p for p in models.regression_plans.fetch_all(conn) if p["status"] not in ("signed off", "done") and (not p["end_date"] or p["end_date"] >= today)]
    open_follow_ups = conn.execute(
        "SELECT COUNT(*) FROM action_items WHERE origin = 'testing' AND status != 'done'"
    ).fetchone()[0]
    raci = [d for d in models.raci_decisions.fetch_all(conn) if any(w in d["decision"].lower() for w in ("qa", "test", "release"))]
    cells = {}
    for row in conn.execute("SELECT decision_id, role, letter FROM raci_assignments"):
        cells.setdefault(row["decision_id"], {})[row["role"]] = row["letter"]
    return {
        "cases": {
            "active": len(cases),
            "smoke": sum(c["kind"] in ("smoke", "smoke and regression") for c in cases),
            "regression": sum(c["kind"] in ("regression", "smoke and regression") for c in cases),
            "never_run": sum(c["last_result"] is None for c in cases),
            "failing": [{"id": c["id"], "title": c["title"], "system_name": c["system_name"]} for c in cases if c["last_result"] in ("fail", "blocked")],
        },
        "suites": {
            "count": len(suites),
            "failing": [{"id": s["id"], "name": s["name"], "last_result": s["last_result"]} for s in suites if s["last_result"] in ("failing", "flaky")],
            "average_coverage": round(sum(covered) / len(covered), 1) if covered else None,
        },
        "plans": models.regression_plans.visible_all(plans, viewer),
        "recent_runs": models.test_runs.visible_all(models.test_runs.fetch_all(conn)[:5], viewer),
        "open_follow_ups": open_follow_ups if viewer.floor == Level.PRIVATE else None,
        "definition_of_done": _dod(conn),
        "raci": [{"decision": d["decision"], "status": d["status"], "cells": cells.get(d["id"], {})} for d in raci],
    }
