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


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


# ---- retrospectives ----


def test_retro_board_columns_votes_and_commit(client):
    s = client.post("/api/sprints/next", json={"start_date": day(-10)}).json()
    r = client.post("/api/retros", json={"sprint_id": s["id"], "format": "start / stop / continue", "date": day(0)}).json()
    item = client.post("/api/retro-items", json={"retro_id": r["id"], "column_name": "Stop", "text": "[Point]", "topic": "[topic]"}).json()
    assert client.post(f"/api/retro-items/{item['id']}/vote", json={}).json()["votes"] == 1
    c = client.post(f"/api/retro-items/{item['id']}/commit", json={}).json()
    assert c["commitment"] == "[Point]" and c["sprint_id"] == s["id"] and c["status"] == "committed"
    board = client.get(f"/api/retros/{r['id']}/board").json()
    assert board["columns"] == ["Start", "Stop", "Continue"]
    assert board["items"]["Stop"][0]["votes"] == 1
    assert [x["id"] for x in board["commitments"]] == [c["id"]]
    assert client.get("/api/retros").json()[0]["commitment_count"] == 1
    assert client.get("/api/retros/999/board").status_code == 404


def test_commitments_carry_forward_until_reviewed(client):
    s1 = client.post("/api/sprints/next", json={"start_date": day(-20)}).json()
    s2 = client.post("/api/sprints/next", json={}).json()
    r1 = client.post("/api/retros", json={"sprint_id": s1["id"], "date": day(-7)}).json()
    c = client.post("/api/retro-commitments", json={"retro_id": r1["id"], "sprint_id": s1["id"], "commitment": "[We will]"}).json()
    r2 = client.post("/api/retros", json={"sprint_id": s2["id"], "date": day(0)}).json()
    assert [x["id"] for x in client.get(f"/api/retros/{r2['id']}/board").json()["carried_forward"]] == [c["id"]]
    assert [x["id"] for x in client.get("/api/improvements").json()] == [c["id"]]
    reviewed = client.post(f"/api/retro-commitments/{c['id']}/review", json={"status": "done", "outcome": "[Outcome]", "reviewed_in_id": r2["id"]}).json()
    assert reviewed["reviewed_in_id"] == r2["id"] and reviewed["outcome"] == "[Outcome]"
    assert client.get(f"/api/retros/{r2['id']}/board").json()["carried_forward"] == []


def test_recurring_topics(client):
    s1 = client.post("/api/sprints/next", json={"start_date": day(-20)}).json()
    s2 = client.post("/api/sprints/next", json={}).json()
    for s in (s1, s2):
        r = client.post("/api/retros", json={"sprint_id": s["id"]}).json()
        client.post("/api/retro-items", json={"retro_id": r["id"], "column_name": "Ideas", "text": "[Point]", "topic": "[Deploys]"})
    client.post("/api/retro-items", json={"retro_id": r["id"], "column_name": "Ideas", "text": "[Once]", "topic": "[Once]"})
    patterns = client.get("/api/retros/patterns").json()
    assert len(patterns) == 1 and patterns[0]["retros"] == 2 and patterns[0]["sprints"] == [1, 2]


# ---- PI planning ----


def pi_with_sprints(client):
    pi = client.post("/api/program-increments", json={"number": 1}).json()
    s1 = client.post("/api/sprints/next", json={"start_date": day(-5)}).json()
    s2 = client.post("/api/sprints/next", json={}).json()
    for s in (s1, s2):
        client.patch(f"/api/sprints/{s['id']}", json={"pi_id": pi["id"], "capacity": 30})
    return pi, s1, s2


def test_pi_board_capacity_and_predictability(client):
    pi, s1, s2 = pi_with_sprints(client)
    epic = client.post("/api/epics", json={"title": "[Epic]", "priority": "high"}).json()
    f = client.post("/api/features", json={"pi_id": pi["id"], "epic_id": epic["id"], "title": "[Feature]"}).json()
    client.post("/api/stories", json={"feature_id": f["id"], "sprint_id": s1["id"], "title": "[Story A]", "points": 5})
    client.post("/api/stories", json={"feature_id": f["id"], "title": "[Story B]", "points": 3})
    client.post("/api/pi-objectives", json={"pi_id": pi["id"], "title": "[Objective]", "value_planned": 8, "value_actual": 6})
    client.post("/api/pi-objectives", json={"pi_id": pi["id"], "title": "[Stretch]", "kind": "stretch", "value_planned": 5})
    board = client.get(f"/api/pis/{pi['id']}/board").json()
    assert [(s["number"], s["planned_points"], s["capacity"]) for s in board["sprints"]] == [(1, 5, 30), (2, 0, 30)]
    assert board["features"][0]["epic_title"] == "[Epic]" and board["features"][0]["points"] == 8
    assert board["predictability"] == 75
    assert client.get("/api/pis/999/board").status_code == 404


def test_pi_dependencies_milestones_risks_and_confidence(client):
    pi, s1, s2 = pi_with_sprints(client)
    a = client.post("/api/features", json={"pi_id": pi["id"], "title": "[A]"}).json()
    b = client.post("/api/features", json={"pi_id": pi["id"], "title": "[B]"}).json()
    client.post("/api/dependencies", json={"pi_id": pi["id"], "feature_id": a["id"], "depends_on_id": b["id"], "description": "[Need]", "needed_by_id": s2["id"]})
    client.post("/api/pi-milestones", json={"pi_id": pi["id"], "title": "[Release]", "date": day(0)})
    client.post("/api/pi-risks", json={"pi_id": pi["id"], "title": "[Risk]", "notes": "[Private]"})
    board = client.get(f"/api/pis/{pi['id']}/board").json()
    dep = board["dependencies"][0]
    assert (dep["feature_title"], dep["depends_on_title"], dep["needed_by_number"]) == ("[A]", "[B]", 2)
    assert board["milestones"][0]["title"] == "[Release]" and board["risks"][0]["roam"] == "unroamed"
    assert client.post(f"/api/pis/{pi['id']}/confidence", json={"votes": [4, 4, 3, 5]}).json()["confidence"] == 4.0
    assert client.post(f"/api/pis/{pi['id']}/confidence", json={"votes": [9]}).status_code == 400
    client.post("/api/session/presentation", json={"on": True})
    shown = client.get(f"/api/pis/{pi['id']}/board").json()
    assert "notes" not in shown["risks"][0] and shown["features"]
