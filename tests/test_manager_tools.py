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


def day(n):
    return (date.today() + timedelta(days=n)).isoformat()


def setup(client):
    me = client.post("/api/people", json={"name": "[Me]"}).json()["id"]
    rep = client.post("/api/people", json={"name": "[Report One]", "manager_id": None}).json()["id"]
    peer = client.post("/api/people", json={"name": "[Peer]"}).json()["id"]
    client.patch(f"/api/people/{rep}", json={"manager_id": me})
    return me, rep, peer


def test_me_and_direct_reports(client):
    me, rep, peer = setup(client)
    assert client.get("/api/people/reports").json() == {"me": None, "reports": []}
    assert client.put("/api/people/me", json={"person_id": 999}).status_code == 400
    client.put("/api/people/me", json={"person_id": me})
    r = client.get("/api/people/reports").json()
    assert r["me"] == me and [x["name"] for x in r["reports"]] == ["[Report One]"]
    assert client.get(f"/api/people/{rep}/crm").json()["is_report"] is True
    assert client.get(f"/api/people/{peer}/crm").json()["is_report"] is False
    assert client.get(f"/api/people/{me}/crm").json()["is_me"] is True


def test_commitments_both_ways_and_today(client):
    me, rep, peer = setup(client)
    client.put("/api/people/me", json={"person_id": me})
    mine = client.post("/api/commitments", json={"person_id": rep, "direction": "mine", "title": "[Get them access]", "due": day(-1)}).json()
    client.post("/api/commitments", json={"person_id": rep, "direction": "theirs", "title": "[Draft the design]", "due": day(-2)})
    client.post("/api/commitments", json={"person_id": peer, "direction": "mine", "title": "[Intro to vendor]", "due": day(3)})
    r = client.get("/api/people/reports").json()["reports"][0]
    assert (r["i_owe"], r["they_owe"], r["late"]) == (1, 1, 2)
    t = client.get("/api/today").json()["people_due"]
    assert [(c["title"], c["late"]) for c in t["i_owe"]] == [("[Get them access]", True), ("[Intro to vendor]", False)]
    assert [c["title"] for c in t["they_owe_late"]] == ["[Draft the design]"]
    done = client.patch(f"/api/commitments/{mine['id']}", json={"status": "done"}).json()
    assert done["done_on"] == day(0)
    assert client.patch(f"/api/commitments/{mine['id']}", json={"status": "open"}).json()["done_on"] is None


def test_manager_tab_and_agenda(client):
    me, rep, peer = setup(client)
    client.put("/api/people/me", json={"person_id": me})
    client.post("/api/interactions", json={"date": day(-7), "person_ids": [rep], "takeaways": "[Last time's takeaway]"})
    client.post("/api/commitments", json={"person_id": rep, "direction": "theirs", "title": "[Their task]", "due": day(2)})
    client.post("/api/commitments", json={"person_id": rep, "direction": "mine", "title": "[My task]"})
    client.post("/api/growth-goals", json={"person_id": rep, "goal": "[Lead a refinement]", "progress": "[Did one with help]"})
    client.post("/api/manager-notes", json={"person_id": rep, "date": day(0), "kind": "praise", "note": "[Great demo]"})
    client.post("/api/manager-notes", json={"person_id": rep, "date": day(0), "kind": "concern", "note": "[Private concern]"})
    shared = client.post("/api/manager-notes", json={"person_id": rep, "date": day(0), "kind": "constructive", "note": "[Already shared]", "shared": True})
    crm = client.get(f"/api/people/{rep}/crm").json()
    assert len(crm["manager"]["goals"]) == 1 and len(crm["manager"]["notes"]) == 3
    assert "manager" not in client.get(f"/api/people/{peer}/crm").json()
    md = client.get(f"/api/people/{rep}/agenda").json()["markdown"]
    assert "# One-on-one with [Report One]" in md and "[Last time's takeaway]" in md
    assert f"- [ ] [Their task] (due {day(2)})" in md and "- [ ] [My task]" in md and "[Lead a refinement]: [Did one with help]" in md
    assert "Praise: [Great demo]" in md and "[Private concern]" not in md and "[Already shared]" not in md
    assert client.get("/api/people/reports").json()["reports"][0]["unshared"] == 1


def test_private_while_presenting(client):
    me, rep, peer = setup(client)
    client.post("/api/commitments", json={"person_id": rep, "title": "[Mine]"})
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/commitments").json() == []
    assert client.get(f"/api/people/{rep}/agenda").status_code == 403
