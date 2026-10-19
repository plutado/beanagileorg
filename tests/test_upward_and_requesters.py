"""Change requests: who asks most and a policy summary to share. Culture: the upward questions log."""

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


def test_requesters_and_summary(client):
    t = date.today().isoformat()
    a = client.post("/api/people", json={"name": "[Asker A]"}).json()["id"]
    for decision in ("accepted with a swap", "rejected", "deferred to the backlog"):
        client.post("/api/change-requests", json={"title": "[Request]", "requested_on": t, "requested_by_id": a, "decision": decision, "source": "leadership", "urgency": "emergency"})
    who = client.get("/api/change-requests/requesters").json()
    p = who["people"][0]
    assert p["name"] == "[Asker A]" and p["requests"] == 3 and p["accepted"] == 1 and p["accepted_pct"] == 33 and p["emergencies"] == 3
    assert who["sources"][0]["name"] == "leadership"
    md = client.get("/api/change-requests/policy-summary").json()["markdown"]
    assert md.startswith("# Asking for work during a sprint") and "## How to ask" in md


def test_upward_questions(client):
    t = date.today()
    q = client.post("/api/upward-questions", json={"question": "[Placeholder question]", "anonymous": True, "sent_on": (t - timedelta(days=20)).isoformat(), "status": "sent"}).json()
    assert q["asked_by_id"] is None
    assert client.get("/api/today").json()["culture"]["upward_waiting"][0]["id"] == q["id"]
    r = client.patch(f"/api/upward-questions/{q['id']}", json={"answer": "[Placeholder answer]", "answered_on": (t - timedelta(days=5)).isoformat(), "status": "answered"}).json()
    assert r["days_to_answer"] == 15
    today = client.get("/api/today").json()["culture"]
    assert today["upward_waiting"] == [] and today["upward_untold"][0]["id"] == q["id"]
