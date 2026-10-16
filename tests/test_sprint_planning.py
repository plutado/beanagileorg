from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit import sprint_planning as sp
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def monday(offset_weeks=0):
    d = date.today() + timedelta(days=7 * offset_weeks)
    return (d - timedelta(days=d.weekday())).isoformat()


def test_paste_from_jira(client):
    r = client.post("/api/backlog/paste", json={"text": "abc-1 [First story]\nABC-2 - [Second story] | 5\nnot a story line\nABC-1 [Renamed]"}).json()
    assert (r["added"], r["skipped"], r["not_understood"]) == (2, 1, ["not a story line"])
    items = client.get("/api/backlog").json()["items"]
    assert [(i["jira_key"], i["title"], i["points"], i["status"]) for i in items] == [("ABC-1", "[First story]", None, "needs refinement"), ("ABC-2", "[Second story]", 5, "needs refinement")]
    assert client.post("/api/backlog/paste", json={"text": "ABC-1 [Renamed] | 3", "update": True}).json()["updated"] == 1
    assert client.get("/api/backlog").json()["items"][0]["title"] == "[Renamed]"
    dup = client.post("/api/backlog-items", json={"title": "[Dup]", "jira_key": "abc-2"})
    assert dup.status_code == 409 and "already recorded" in dup.json()["detail"]


def test_readiness_and_votes(client):
    client.post("/api/planning/definition-of-ready/starter")
    dor = client.get("/api/planning/definition-of-ready").json()["items"]
    item = client.post("/api/backlog-items", json={"title": "[Story]"}).json()
    client.patch(f"/api/backlog-items/{item['id']}", json={"ready_checks": dor[:3]})
    got = client.get("/api/backlog").json()["items"][0]
    assert (got["ready_met"], got["ready_total"]) == (3, len(dor))
    a = client.post("/api/people", json={"name": "[Dev A]", "relationship": "employee"}).json()["id"]
    b = client.post("/api/people", json={"name": "[Dev B]", "relationship": "employee"}).json()["id"]
    s = client.post(f"/api/backlog-items/{item['id']}/votes", json={"votes": [{"person_id": a, "points": 2}, {"person_id": b, "points": 8}]}).json()
    assert s["discuss"] and (s["low"], s["high"], s["round"]) == (2, 8, 1)
    s = client.post(f"/api/backlog-items/{item['id']}/votes", json={"votes": [{"person_id": a, "points": 5}, {"person_id": b, "points": 5}]}).json()
    assert not s["discuss"] and s["round"] == 2 and s["median"] == 5
    assert client.post(f"/api/backlog-items/{item['id']}/votes", json={"votes": []}).status_code == 400
    assert client.post(f"/api/backlog-items/{item['id']}/votes", json={"votes": [{"person_id": 999, "points": 3}]}).status_code == 400


def test_capacity_pull_commit_close(client):
    a = client.post("/api/people", json={"name": "[Dev A]", "relationship": "employee"}).json()["id"]
    client.post("/api/people", json={"name": "[Dev B]", "relationship": "contractor"}).json()
    client.post("/api/people", json={"name": "[Stakeholder]", "relationship": "stakeholder"})
    s1 = client.post("/api/sprints/next", json={"start_date": monday(-2)}).json()
    s2 = client.post("/api/sprints/next", json={}).json()
    s3 = client.post("/api/sprints/next", json={}).json()
    # sprint 1 closes at 20 points, which becomes velocity for sprint 2
    x = client.post("/api/backlog-items", json={"title": "[Done story]", "points": 20, "status": "ready"}).json()
    client.post(f"/api/sprint-planning/{s1['id']}/pull", json={"item_id": x["id"]})
    client.patch(f"/api/sprints/{s1['id']}", json={"goal": "[Goal 1]"})
    client.post(f"/api/sprint-planning/{s1['id']}/commit", json={})
    client.patch(f"/api/backlog-items/{x['id']}", json={"status": "done"})
    assert client.post(f"/api/sprint-planning/{s1['id']}/close", json={}).json()["completed_points"] == 20
    d = client.get(f"/api/sprint-planning/{s2['id']}").json()
    assert d["working_days"] == 10 and len(d["people"]) == 2
    assert d["capacity"]["velocity"]["average"] == 20 and d["capacity"]["suggested"] == 20
    client.put(f"/api/sprint-planning/{s2['id']}/availability", json={"person_id": a, "days": 5})
    cap = client.get(f"/api/sprint-planning/{s2['id']}").json()["capacity"]
    assert (cap["available_days"], cap["full_days"], cap["suggested"]) == (15, 20, 15)
    ready = client.post("/api/backlog-items", json={"title": "[Ready]", "points": 8, "status": "ready", "jira_key": "ABC-9", "dependencies": "[Needs the API]"}).json()
    rough = client.post("/api/backlog-items", json={"title": "[Rough]", "points": 3}).json()
    assert client.post(f"/api/sprint-planning/{s2['id']}/pull", json={"item_id": rough["id"]}).json()["warning"]
    client.post(f"/api/sprint-planning/{s2['id']}/pull", json={"item_id": ready["id"]})
    assert client.post(f"/api/sprint-planning/{s2['id']}/commit", json={}).status_code == 400  # no goal yet
    plan = client.post(f"/api/sprint-planning/{s2['id']}/commit", json={"goal": "[Goal 2]"}).json()
    assert (plan["status"], plan["committed_points"]) == ("committed", 11)
    assert client.get(f"/api/backlog-items/{ready['id']}").json()["status"] == "in sprint"
    md = client.post(f"/api/sprint-planning/{s2['id']}/summary/export").json()["markdown"]
    assert "**Goal:** [Goal 2]" in md and "| ABC-9 | [Ready] | 8 |" in md and "[Needs the API]" in md and "[Dev A]: 5 of 10 days" in md
    client.patch(f"/api/backlog-items/{ready['id']}", json={"status": "done"})
    r = client.post(f"/api/sprint-planning/{s2['id']}/close", json={}).json()
    assert (r["completed_points"], r["carried"], r["carried_to"]) == (8, 1, s3["id"])
    moved = client.get(f"/api/backlog-items/{rough['id']}").json()
    assert (moved["sprint_id"], moved["carried_from_id"]) == (s3["id"], s2["id"])


def test_debt_to_backlog_and_jira_search(client):
    d = client.post("/api/tech-debt", json={"title": "[Debt]", "ticket_key": "ABC-50", "points": 5}).json()
    item = client.post(f"/api/tech-debt/{d['id']}/to-backlog").json()
    assert (item["item_type"], item["jira_key"], item["debt_id"], item["points"]) == ("tech debt", "ABC-50", d["id"], 5)
    assert client.post(f"/api/tech-debt/{d['id']}/to-backlog").status_code == 409
    kinds = {f["kind"] for f in client.get("/api/jira/ABC-50").json()["found"]}
    assert kinds == {"Tech debt", "Backlog story"}


def test_today_shows_upcoming_planning(client):
    s = client.post("/api/sprints/next", json={"start_date": (date.today() + timedelta(days=2)).isoformat()}).json()
    client.post("/api/backlog-items", json={"title": "[Ready]", "points": 3, "status": "ready"})
    assert client.get("/api/today").json()["planning_due"] == [{"sprint_id": s["id"], "number": 1, "start_date": s["start_date"], "ready_stories": 1, "ready_points": 3}]


def test_working_days():
    assert sp.working_days("2026-11-02", "2026-11-15") == 10
    assert sp.working_days(None, "2026-11-15") is None
