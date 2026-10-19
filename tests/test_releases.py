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


def test_direction_and_logged_decision(client):
    m = client.post("/api/metrics", json={"name": "[Escaped defects]", "higher_is_better": False}).json()["id"]
    for i, v in enumerate([8, 6, 4]):
        client.post("/api/metric-readings", json={"metric_id": m, "date": (date.today() - timedelta(days=30 - i)).isoformat(), "value": v})
    assert client.get("/api/metrics/directions").json()[str(m)] == "improving"
    week = client.get("/api/reports/weekly").json()["markdown"]
    assert "[Escaped defects]: 4" in week and "improving" in week
    p = client.post("/api/people", json={"name": "[Placeholder name 1]"}).json()["id"]
    r = client.post("/api/releases", json={"name": "[Release 1]"}).json()["id"]
    res = client.put(f"/api/releases/{r}/decision", json={"decision": "go", "decided_by_id": p, "decision_notes": "[Placeholder]"}).json()
    d = client.get(f"/api/decisions-needed/{res['logged_decision_id']}").json()
    assert d["status"] == "decided" and d["outcome"].startswith("Go: [Placeholder] (open at the time:") and d["from_id"] == p
    assert client.put(f"/api/releases/{r}/decision", json={"decision": "go", "decided_by_id": p}).json()["logged_decision_id"] is None


def test_calendar_restore_and_change_requests(client):
    t = date.today()
    client.post("/api/regression-plans", json={"title": "[Freeze]", "kind": "peak-season freeze", "start_date": (t + timedelta(days=10)).isoformat(), "end_date": (t + timedelta(days=20)).isoformat()})
    a = client.post("/api/releases", json={"name": "[Inside]", "planned_on": (t + timedelta(days=15)).isoformat()}).json()["id"]
    client.post("/api/releases", json={"name": "[Outside]", "planned_on": (t + timedelta(days=30)).isoformat()})
    cal = client.get("/api/releases/calendar").json()
    clash = {r["name"]: r["clashes"] for r in cal["releases"]}
    assert clash == {"[Inside]": ["[Freeze]"], "[Outside]": []} and len(cal["windows"]) == 1
    inc = client.post("/api/incidents", json={"summary": "[Outage]", "date": (t - timedelta(days=6)).isoformat(), "resolved_at": (t - timedelta(days=4)).isoformat()}).json()["id"]
    client.post("/api/releases", json={"name": "[Failed]", "status": "released", "released_on": (t - timedelta(days=6)).isoformat(), "outcome": "rollback", "incident_id": inc})
    m = client.get("/api/releases/metrics").json()
    assert m["time_to_restore"] == 2.0 and m["restores"] == 1
    sp = client.post("/api/sprints", json={"number": 3}).json()["id"]
    cr = client.post("/api/change-requests", json={"title": "[Urgent fix]", "requested_on": t.isoformat(), "sprint_id": sp, "decision": "accepted with a swap", "status": "decided"}).json()["id"]
    client.post("/api/change-requests", json={"title": "[Deferred]", "requested_on": t.isoformat(), "sprint_id": sp, "decision": "deferred to the backlog"})
    client.patch(f"/api/releases/{a}", json={"sprint_id": sp})
    assert client.post(f"/api/releases/{a}/from-sprint").json()["change_request_ids"] == [cr]
    assert "## Added during the sprint\n- [Urgent fix]" in client.get(f"/api/releases/{a}/notes").json()["markdown"]
    assert [c["title"] for c in client.get(f"/api/releases/{a}/detail").json()["change_requests"]] == ["[Urgent fix]"]
