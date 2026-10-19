"""Plans: versions saved when presented or on demand, what changed since, and checkpoint check-ins."""

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


def plan(client, day):
    return next(p["id"] for p in client.get("/api/plans").json() if p["horizon_days"] == day)


def test_versions_and_compare(client):
    p30 = plan(client, 30)
    a = client.post("/api/plan-items", json={"plan_id": p30, "title": "[Item A]", "due_day": 10}).json()["id"]
    client.post("/api/plan-items", json={"plan_id": p30, "title": "[Item B]"})
    client.post(f"/api/plans/{p30}/presented", json={"audience": "[Manager]"})
    v = client.get(f"/api/plans/{p30}/versions").json()
    assert len(v) == 1 and v[0]["label"] == "Presented to [Manager]" and v[0]["items"] == 2
    client.patch(f"/api/plan-items/{a}", json={"due_day": 20})
    client.post("/api/plan-items", json={"plan_id": p30, "title": "[Item C]"})
    c = client.get(f"/api/plans/{p30}/compare?version_id={v[0]['id']}").json()
    assert [i["title"] for i in c["added"]] == ["[Item C]"] and c["changed"][0]["changes"] == [{"field": "due_day", "was": 10, "now": 20}]
    assert client.post(f"/api/plans/{p30}/versions", json={"label": "[Day-30 review]"}).status_code == 201
    assert len(client.get(f"/api/plans/{p30}/versions").json()) == 2


def test_checkin(client):
    p30, p60 = plan(client, 30), plan(client, 60)
    a = client.post("/api/plan-items", json={"plan_id": p30, "title": "[Met item]"}).json()["id"]
    b = client.post("/api/plan-items", json={"plan_id": p30, "title": "[Moved item]", "due_day": 20}).json()["id"]
    d = client.post("/api/plan-items", json={"plan_id": p30, "title": "[Dropped item]"}).json()["id"]
    assert client.put(f"/api/plan-items/{a}/checkin", json={"outcome": "met"}).json()["status"] == "done"
    assert client.put(f"/api/plan-items/{b}/checkin", json={"outcome": "moved"}).status_code == 400
    assert client.put(f"/api/plan-items/{b}/checkin", json={"outcome": "moved", "note": "[Waiting on access]"}).status_code == 400
    moved = client.put(f"/api/plan-items/{b}/checkin", json={"outcome": "moved", "note": "[Waiting on access]", "plan_id": p60, "due_day": 45}).json()
    assert moved["plan_id"] == p60 and moved["due_day"] == 45 and moved["checkin"]["was_day"] == 20
    assert client.put(f"/api/plan-items/{d}/checkin", json={"outcome": "dropped", "note": "[No longer needed]"}).json()["status"] == "dropped"
    s = client.get(f"/api/plans/{p30}/checkin").json()
    assert s["counts"]["met"] == 1 and s["counts"]["moved"] == 1 and s["counts"]["dropped"] == 1
    assert "- [Moved item] (now Days 31 to 60, day 45): [Waiting on access]" in s["markdown"]
