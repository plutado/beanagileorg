from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
TODAY = date.today()
MONDAY = TODAY - timedelta(days=TODAY.weekday())


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def sprint_with_stories(client):
    sid = client.post("/api/sprints", json={"number": 5, "start_date": MONDAY.isoformat(), "end_date": (MONDAY + timedelta(days=11)).isoformat(), "goal": "[Goal]"}).json()["id"]
    story = lambda title, pts, rank, status="in sprint": client.post("/api/backlog-items", json={"title": title, "points": pts, "rank": rank, "sprint_id": sid, "status": status}).json()["id"]
    return sid, story("[High priority]", 5, 1), story("[Low priority]", 3, 9), story("[Done already]", 2, 2, "done")


def cr(client, **kw):
    return client.post("/api/change-requests", json={"title": "[Request]", "requested_on": TODAY.isoformat(), "points": 3, "source": "leadership", **kw}).json()["id"]


def test_impact_lists_swap_candidates(client):
    sid, high, low, done = sprint_with_stories(client)
    c = cr(client)
    imp = client.get(f"/api/change-requests/{c}/assess").json()["impact"]
    assert imp["sprint"]["id"] == sid and imp["in_sprint"] == 10 and imp["done"] == 2 and imp["remaining"] == 8
    assert [x["id"] for x in imp["candidates"]] == [low, high]  # lowest priority first, finished work excluded


def test_swap_moves_stories_and_counts_scope(client):
    sid, high, low, done = sprint_with_stories(client)
    c = cr(client, jira_keys=["web-9"])
    assert client.post(f"/api/change-requests/{c}/decide", json={"decision": "accepted with a swap"}).status_code == 400
    assert client.post(f"/api/change-requests/{c}/decide", json={"decision": "accepted with a swap", "swap_out_ids": [done]}).status_code == 400
    r = client.post(f"/api/change-requests/{c}/decide", json={"decision": "accepted with a swap", "swap_out_ids": [low], "reason": "[Why]"}).json()
    req = r["request"]
    assert req["status"] == "decided" and req["points_out"] == 3 and req["swapped_out_ids"] == [low] and req["sprint_id"] == sid
    out = client.get(f"/api/backlog-items/{low}").json()
    assert out["sprint_id"] is None and out["status"] == "ready"
    new = client.get(f"/api/backlog-items/{req['backlog_item_id']}").json()
    assert new["sprint_id"] == sid and new["status"] == "in sprint" and new["jira_key"] == "WEB-9" and new["points"] == 3
    assert client.post(f"/api/change-requests/{c}/decide", json={"decision": "rejected", "reason": "x"}).status_code == 409
    ov = client.get("/api/change-requests/overview").json()
    assert ov["churn"][-1]["points_in"] == 3 and ov["churn"][-1]["points_out"] == 3 and ov["untold"][0]["id"] == c
    rep = client.get(f"/api/reports/sprint?sprint_id={sid}").json()
    assert rep["scope"] == {"requests": 1, "accepted": 1, "points_in": 3, "points_out": 3}
    assert "net +0" in rep["markdown"] and "[Request] (from leadership): accepted with a swap, 3 pts, 3 pts swapped out" in rep["markdown"]
    assert "## Scope changes" in client.get("/api/reports/weekly").json()["markdown"]


def test_defer_reject_absorb_and_today(client):
    sid, high, low, done = sprint_with_stories(client)
    a, b, d = cr(client, title="[Defer me]"), cr(client, title="[Reject me]"), cr(client, title="[Absorb me]", points=40)
    due = client.get("/api/today").json()["changes"]
    assert {w["id"] for w in due["waiting"]} == {a, b, d}
    assert client.post(f"/api/change-requests/{a}/decide", json={"decision": "deferred to the backlog"}).status_code == 400  # needs a reason
    client.post(f"/api/change-requests/{a}/decide", json={"decision": "deferred to the backlog", "reason": "[Next sprint]"})
    item = client.get(f"/api/backlog-items/{client.get(f'/api/change-requests/{a}').json()['backlog_item_id']}").json()
    assert item["sprint_id"] is None and item["status"] == "needs refinement"
    client.post(f"/api/change-requests/{b}/decide", json={"decision": "rejected", "reason": "[Not worth it]"})
    assert client.get(f"/api/change-requests/{b}").json()["backlog_item_id"] is None
    r = client.post(f"/api/change-requests/{d}/decide", json={"decision": "accepted without a swap"}).json()
    assert r["request"]["points_out"] == 0
    assert client.post(f"/api/change-requests/{b}/told", json={}).json()["communicated_on"] == TODAY.isoformat()
    due = client.get("/api/today").json()["changes"]
    assert due["waiting"] == [] and {u["id"] for u in due["untold"]} == {a, d}
    assert client.post(f"/api/change-requests/{cr(client)}/told", json={}).status_code == 400


def test_policy_and_privacy(client):
    assert "product owner" in client.get("/api/change-requests/policy").json()["starter"]
    client.put("/api/change-requests/policy", json={"policy": "[Our policy]"})
    assert client.get("/api/change-requests/overview").json()["policy"] == "[Our policy]"
    sprint_with_stories(client)
    c = cr(client, description="[Detail for manager]", notes="[Private note]")
    client.post(f"/api/change-requests/{c}/decide", json={"decision": "rejected", "reason": "[Reason]"})
    lead = client.get("/api/reports/weekly?audience=leadership").json()["markdown"]
    assert "[Request] (from leadership): rejected, 3 pts. [Reason]" in lead and "[Private note]" not in lead
    client.post("/api/session/presentation", json={"on": True})
    shown = client.get(f"/api/change-requests/{c}").json()
    assert "notes" not in shown and shown["description"] == "[Detail for manager]"
    assert client.get(f"/api/change-requests/{c}/assess").json()["impact"] is None
