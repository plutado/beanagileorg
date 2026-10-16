import pytest
from fastapi.testclient import TestClient

from beanagile.core.config import Settings
from beanagile.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def case(client, title, **kw):
    return client.post("/api/test-cases", json={"title": title, **kw}).json()


def test_smoke_run_picks_active_smoke_cases(client):
    s = client.post("/api/systems", json={"name": "[System]"}).json()
    a = case(client, "[Smoke A]", system_id=s["id"])
    b = case(client, "[Both]", kind="smoke and regression")
    case(client, "[Regression only]", kind="regression")
    case(client, "[Retired]", active=False)
    run = client.post("/api/test-runs", json={"name": "[Run]", "select": "smoke"}).json()
    assert run["total"] == 2 and run["not_run"] == 2 and run["date"]
    board = client.get(f"/api/test-runs/{run['id']}/board").json()
    assert {r["case_id"] for r in board["results"]} == {a["id"], b["id"]}
    assert board["results"][0]["case"]["system_name"] == "[System]"
    only = client.post("/api/test-runs", json={"name": "[By system]", "select": "smoke", "system_id": s["id"]}).json()
    assert only["total"] == 1
    assert client.post("/api/test-runs", json={"name": "[None]", "case_ids": [999]}).status_code == 400


def test_results_tally_and_last_result(client):
    a = case(client, "[A]")
    b = case(client, "[B]")
    run = client.post("/api/test-runs", json={"name": "[Run]", "case_ids": [a["id"], b["id"]]}).json()
    results = client.get(f"/api/test-runs/{run['id']}/board").json()["results"]
    client.patch(f"/api/test-results/{results[0]['id']}", json={"result": "pass"})
    client.patch(f"/api/test-results/{results[1]['id']}", json={"result": "fail", "notes": "[What broke]"})
    run = client.get(f"/api/test-runs/{run['id']}").json()
    assert (run["passed"], run["failed"], run["not_run"]) == (1, 1, 0)
    assert {c["title"]: c["last_result"] for c in client.get("/api/test-cases").json()} == {"[A]": "pass", "[B]": "fail"}
    md = client.get(f"/api/test-runs/{run['id']}/summary").json()["markdown"]
    assert "1 passed, 1 failed" in md and "- [B]: [What broke]" in md
    assert client.patch(f"/api/test-results/{results[0]['id']}", json={"result": "maybe"}).status_code == 400


def test_failure_becomes_dev_sync_item(client):
    sprint = client.post("/api/sprints/next", json={}).json()
    owner = client.post("/api/people", json={"name": "[Owner]"}).json()
    c = case(client, "[Checkout works]", owner_id=owner["id"])
    run = client.post("/api/test-runs", json={"name": "[Sprint smoke]", "case_ids": [c["id"]], "sprint_id": sprint["id"]}).json()
    rid = client.get(f"/api/test-runs/{run['id']}/board").json()["results"][0]["id"]
    client.patch(f"/api/test-results/{rid}", json={"result": "fail"})
    item = client.post(f"/api/test-results/{rid}/follow-up", json={}).json()
    assert item["concern"] == "[Checkout works] failed in [Sprint smoke]" and item["origin"] == "testing"
    assert item["sprint_id"] == sprint["id"] and item["owner_id"] == owner["id"]
    assert client.post(f"/api/test-results/{rid}/follow-up", json={}).status_code == 409
    assert client.get("/api/qa/overview").json()["open_follow_ups"] == 1


def test_regression_plan_run_uses_its_cases(client):
    a = case(client, "[A]", kind="regression")
    case(client, "[B]", kind="regression")
    plan = client.post("/api/regression-plans", json={"title": "[Release plan]", "case_ids": [a["id"]], "start_date": "2099-01-01"}).json()
    run = client.post("/api/test-runs", json={"name": "[Regression]", "plan_id": plan["id"]}).json()
    assert run["total"] == 1 and run["kind"] == "regression" and run["plan_title"] == "[Release plan]"
    empty = client.post("/api/regression-plans", json={"title": "[No cases picked]"}).json()
    assert client.post("/api/test-runs", json={"name": "[All regression]", "plan_id": empty["id"]}).json()["total"] == 2
    assert [p["title"] for p in client.get("/api/qa/overview").json()["plans"]] == ["[Release plan]", "[No cases picked]"]


def test_suites_and_overview(client):
    client.post("/api/test-suites", json={"name": "[Unit suite]", "coverage": 80, "last_result": "passing"})
    client.post("/api/test-suites", json={"name": "[Apex suite]", "kind": "Apex", "coverage": 70, "last_result": "failing"})
    case(client, "[Never run]")
    o = client.get("/api/qa/overview").json()
    assert o["suites"]["average_coverage"] == 75.0 and [s["name"] for s in o["suites"]["failing"]] == ["[Apex suite]"]
    assert o["cases"]["never_run"] == 1 and o["cases"]["smoke"] == 1
    assert client.get("/api/test-suites").json()[0]["name"] == "[Apex suite]"


def test_definition_of_done_and_raci_link(client):
    assert client.get("/api/qa/definition-of-done").json() == {"items": []}
    assert len(client.post("/api/qa/definition-of-done/starter").json()["items"]) == 7
    assert client.post("/api/qa/definition-of-done/starter").status_code == 409
    assert client.put("/api/qa/definition-of-done", json={"items": ["[Item]", "  "]}).json() == {"items": ["[Item]"]}
    client.post("/api/delivery/starter")
    raci = client.get("/api/qa/overview").json()["raci"]
    assert "QA sign-off" in [r["decision"] for r in raci]


def test_run_notes_private(client):
    c = case(client, "[A]")
    run = client.post("/api/test-runs", json={"name": "[Run]", "case_ids": [c["id"]], "notes": "[Private]"}).json()
    client.post("/api/session/presentation", json={"on": True})
    assert "notes" not in client.get(f"/api/test-runs/{run['id']}/board").json()["run"]


def test_ui_origin_list_matches_the_model():
    """The dev-sync edit form must offer every origin, or saving would reset it."""
    import re
    from pathlib import Path

    from beanagile.toolkit import models

    js = (Path(models.__file__).parent / "static/app.js").read_text()
    listed = re.search(r"const ACTION_ORIGINS = \[(.*?)\];", js).group(1)
    assert [s.strip().strip('"') for s in listed.split(",")] == list(models.ACTION_ORIGINS)
