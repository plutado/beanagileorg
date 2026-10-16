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


def person(client, name):
    return client.post("/api/people", json={"name": name}).json()["id"]


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def test_action_items_summary_and_names(client):
    a, b = person(client, "[A]"), person(client, "[B]")
    client.post("/api/actions", json={"concern": "[C1]", "raised_by_id": a, "owner_id": b, "due": day(-1)})
    client.post("/api/actions", json={"concern": "[C2]", "owner_id": a, "due": day(3)})
    client.post("/api/actions", json={"concern": "[C3]", "owner_id": a, "status": "done", "due": day(-5)})
    assert client.get("/api/actions/summary").json() == {"open": 2, "overdue": 1, "due_soon": 1, "learning": 0}
    first = client.get("/api/actions").json()[0]
    assert first["concern"] == "[C1]" and first["owner_name"] == "[B]" and first["raised_by_name"] == "[A]"
    assert first["raised_on"] == date.today().isoformat()
    assert [i["concern"] for i in client.get("/api/today").json()["overdue_actions"]] == ["[C1]"]


def test_action_validation(client):
    assert client.post("/api/actions", json={}).status_code == 400
    assert client.post("/api/actions", json={"concern": "x", "status": "maybe"}).status_code == 400
    assert client.post("/api/actions", json={"concern": "x", "owner_id": 999}).status_code == 400


def test_learning_flag_proposes_one_session(client):
    owner = person(client, "[Owner]")
    item = client.post("/api/actions", json={"concern": "[Topic]", "owner_id": owner}).json()
    assert client.get("/api/learning-sessions").json() == []
    client.patch(f"/api/actions/{item['id']}", json={"learning": True})
    client.patch(f"/api/actions/{item['id']}", json={"next_action": "[Next]"})
    sessions = client.get("/api/learning-sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["topic"] == "[Topic]" and sessions[0]["presenter_name"] == "[Owner]" and sessions[0]["source_concern"] == "[Topic]"


def test_dev_sync_notes_private_while_presenting(client):
    client.post("/api/actions", json={"concern": "[Shown]", "notes": "[Private note]"})
    client.post("/api/session/presentation", json={"on": True})
    item = client.get("/api/actions").json()[0]
    assert item["concern"] == "[Shown]" and "notes" not in item


def test_escalation_chain_and_privacy(client):
    owner, responder = person(client, "[Owner]"), person(client, "[Responder]")
    sys = client.post("/api/systems", json={"name": "[System]", "owner_id": owner, "vendor_support": "[Vendor line]"}).json()
    client.post("/api/escalation-steps", json={"system_id": sys["id"], "person_id": responder, "method": "chat", "position": 0})
    client.post("/api/escalation-steps", json={"system_id": sys["id"], "person_id": owner, "method": "page", "out_of_hours": True})
    client.post("/api/severities", json={"level": "Sev 1", "who_is_paged": "[Placeholder]"})
    chain = client.get(f"/api/escalation/{sys['id']}").json()
    assert chain["system"]["owner_name"] == "[Owner]" and chain["system"]["vendor_support"] == "[Vendor line]"
    assert [s["person_name"] for s in chain["business_hours"]] == ["[Responder]"]
    assert [s["method"] for s in chain["out_of_hours"]] == ["page"]
    assert chain["severities"][0]["level"] == "Sev 1"
    client.post("/api/session/presentation", json={"on": True})
    assert "vendor_support" not in client.get(f"/api/escalation/{sys['id']}").json()["system"]
    assert client.get("/api/escalation/999").status_code == 404


def test_incident_follow_up_becomes_action_item(client):
    sys = client.post("/api/systems", json={"name": "[System]"}).json()
    inc = client.post("/api/incidents", json={"summary": "[Outage]", "system_id": sys["id"], "date": day(0)}).json()
    assert client.get("/api/incidents").json()[0]["system_name"] == "[System]"
    item = client.post(f"/api/incidents/{inc['id']}/follow-up", json={}).json()
    assert item["origin"] == "incident" and item["incident_id"] == inc["id"] and item["concern"] == "Follow-up: [Outage]"


def test_seed_fills_only_empty_parts(client):
    person(client, "[Existing person]")
    loaded = client.post("/api/seed-placeholders").json()
    assert "people" not in loaded and loaded["action_items"] == 6 and loaded["systems"] == 3
    assert len(client.get("/api/people").json()) == 1
    assert client.post("/api/seed-placeholders").status_code == 409
    sessions = client.get("/api/learning-sessions").json()
    assert len(sessions) == 3 and sessions[0]["status"] == "scheduled"
