from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
TODAY = date.today()


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def d(n):
    return (TODAY + timedelta(days=n)).isoformat()


def setup(client, day=20):
    client.put("/api/toolkit/settings", json={"start_date": d(-day + 1)})
    boss = client.post("/api/people", json={"name": "[Boss]", "relationship": "manager"}).json()["id"]
    me = client.post("/api/people", json={"name": "[Me]", "manager_id": boss}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    rep = client.post("/api/people", json={"name": "[Report]", "relationship": "employee"}).json()["id"]
    client.patch(f"/api/people/{rep}", json={"manager_id": me})
    return boss, me, rep


def test_my_mandate_lifecycle(client):
    assert client.post("/api/mandates/mine", json={}).status_code == 400  # no "me" yet
    boss, me, rep = setup(client)
    assert client.get("/api/today").json()["mandates"]["agree_mine"]["exists"] is False
    m = client.post("/api/mandates/mine", json={}).json()
    assert client.post("/api/mandates/mine", json={}).status_code == 409
    full = client.get(f"/api/mandates/{m['id']}/full").json()
    assert len(full["decisions"]) == 10 and full["to_clarify"] == 10
    client.post("/api/mandate-items", json={"mandate_id": m["id"], "kind": "outcome", "text": "[Outcome]", "due_day": 30, "status": "at risk"})
    full = client.get(f"/api/mandates/{m['id']}/full").json()
    assert full["outcomes"][0]["due"] == d(10) and full["at_risk"] == 1
    a = client.post(f"/api/mandates/{m['id']}/agree", json={}).json()
    assert a["status"] == "agreed" and a["agreed_with_id"] == boss and a["review_on"] == d(90)
    assert client.get("/api/today").json()["mandates"]["agree_mine"] is None
    assert "[Outcome]: at risk" in client.get("/api/reports/weekly?audience=my manager").json()["markdown"]
    assert "my mandate" not in client.get("/api/reports/weekly?audience=leadership").json()["markdown"].lower()
    md = client.post(f"/api/mandates/{m['id']}/export").json()["markdown"]
    assert "Agreed with [Boss]" in md and "| Release go/no-go | to clarify |" in md


def test_import_and_brief(client):
    setup(client)
    body = {"purpose": "[Purpose]", "questions": "- [Question]", "outcomes": [{"text": "[A]", "due_day": 14}], "decisions": [{"text": "[Hiring]", "authority": "I recommend, someone else decides"}]}
    r = client.post("/api/mandates/import", json=body).json()
    assert r["added"] == 2 and r["fields"] == ["purpose", "questions"]
    assert client.post("/api/mandates/import", json=body).json()["added"] == 0
    assert client.post("/api/mandates/import", json={"decisions": [{"text": "[X]", "authority": "whenever"}]}).status_code == 400
    client.put("/api/culture/role-brief", json={"focus": ["[A]", "[From brief]"]})
    assert client.post("/api/mandates/mine/from-brief").json()["added"] == 1
    full = client.get(f"/api/mandates/{r['mandate_id']}/full").json()
    assert [o["text"] for o in full["outcomes"]] == ["[A]", "[From brief]"] and full["decisions"][0]["authority"] == "I recommend, someone else decides"


def test_report_mandate_ticks_milestone_and_privacy(client):
    boss, me, rep = setup(client, day=50)
    client.post("/api/first90/team/start", json={})
    assert client.post(f"/api/mandates/for/{me}", json={}).status_code == 400
    m = client.post(f"/api/mandates/for/{rep}", json={}).json()
    ms = next(x for x in client.get("/api/first90/team").json()["people"][0]["milestones"] if x["auto"] == "mandate")
    assert ms["late"] and not ms["done"]
    client.post(f"/api/mandates/{m['id']}/agree", json={})
    assert client.get(f"/api/mandates/{m['id']}").json()["agreed_with_id"] == me
    ms = next(x for x in client.get("/api/first90/team").json()["people"][0]["milestones"] if x["auto"] == "mandate")
    assert ms["done"] == d(0) and ms["seen_in_data"]
    ov = client.get("/api/mandates/overview").json()
    assert ov["reports"][0]["mandate"]["status"] == "agreed"
    mine = client.post("/api/mandates/mine", json={}).json()
    client.patch(f"/api/mandates/{mine['id']}", json={"purpose": "[My purpose]", "notes": "[Private]"})
    client.post("/api/session/presentation", json={"on": True})
    assert client.get(f"/api/mandates/{m['id']}/full").json() == {"hidden": True}
    shown = client.get(f"/api/mandates/{mine['id']}/full").json()
    assert shown["purpose"] == "[My purpose]" and "notes" not in shown and len(shown["decisions"]) == 10
