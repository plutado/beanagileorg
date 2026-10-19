"""Releases: the path to production, filling from a sprint, the readiness check, release notes, and the
release log's delivery measures."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_path_comes_from_settings_or_sdlc(client):
    assert client.get("/api/releases/settings").json()["path"][-1] == "Production"
    client.post("/api/sdlc-environments", json={"name": "[Env A]", "position": 0})
    client.post("/api/sdlc-environments", json={"name": "[Env B]", "position": 1})
    assert client.get("/api/releases/settings").json()["path"] == ["[Env A]", "[Env B]"]
    assert client.put("/api/releases/settings", json={"path": ["[One]", "[Two]"]}).json()["custom"]
    r = client.post("/api/releases", json={"name": "[Release 1]"}).json()
    steps = client.post(f"/api/releases/{r['id']}/start-path").json()["path"]["steps"]
    assert [s["step"] for s in steps] == ["[One]", "[Two]"]
    assert client.post(f"/api/releases/{r['id']}/start-path").status_code == 409


def test_from_sprint_readiness_and_notes(client):
    sp = client.post("/api/sprints", json={"number": 1}).json()["id"]
    a = client.post("/api/backlog-items", json={"title": "[Story A]", "jira_key": "ABC-1", "sprint_id": sp, "status": "done"}).json()["id"]
    b = client.post("/api/backlog-items", json={"title": "[Story B]", "sprint_id": sp, "status": "in sprint"}).json()["id"]
    r = client.post("/api/releases", json={"name": "[Release 1]", "sprint_id": sp}).json()
    filled = client.post(f"/api/releases/{r['id']}/from-sprint").json()
    assert sorted(filled["story_ids"]) == sorted([a, b]) and filled["jira_keys"] == ["ABC-1"]
    client.post(f"/api/releases/{r['id']}/start-path")
    rd = client.get(f"/api/releases/{r['id']}/detail").json()["readiness"]
    assert not rd["ready"] and {c["key"]: c["ok"] for c in rd["checks"]} == {"stories": False, "regression": False, "qa": False, "path": False}
    client.patch(f"/api/backlog-items/{b}", json={"status": "done"})
    plan = client.post("/api/regression-plans", json={"title": "[Plan]", "status": "signed off"}).json()["id"]
    steps = client.get(f"/api/releases/{r['id']}").json()["path"]["steps"]
    for s in steps[:-1]:
        s["done_on"] = date.today().isoformat()
    client.patch(f"/api/releases/{r['id']}", json={"regression_plan_id": plan, "qa_signoff_on": date.today().isoformat(), "path": {"steps": steps}})
    assert client.get(f"/api/releases/{r['id']}/detail").json()["readiness"]["ready"]
    md = client.get(f"/api/releases/{r['id']}/notes").json()["markdown"]
    assert "- [Story A] (ABC-1)" in md and "- [Story B]" in md


def test_release_log_metrics_and_today(client):
    t = date.today()
    for i, outcome in enumerate(["clean", "hotfix", "clean", None]):
        client.post("/api/releases", json={"name": f"[R{i}]", "status": "released", "released_on": (t - timedelta(days=3 + i)).isoformat(), "outcome": outcome})
    m = client.get("/api/releases/metrics").json()
    assert m["released"] == 4 and m["judged"] == 3 and m["failed"] == 1 and m["change_failure_rate"] == 33.3
    assert client.post("/api/releases/metrics/record").status_code == 400
    client.post("/api/metrics", json={"name": "Change failure rate"})
    assert client.post("/api/releases/metrics/record").json()["recorded"] == ["Change failure rate"]
    client.post("/api/releases", json={"name": "[Soon]", "planned_on": (t + timedelta(days=2)).isoformat()})
    kinds = {x["name"]: x["kind"] for x in client.get("/api/today").json()["releases"]}
    assert kinds["[Soon]"] == "not ready" and kinds["[R3]"] == "outcome"
