from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms import messaging
from beanagileorg.comms.app import build as build_comms
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


# ---- sprint notebook ----


def test_next_sprint_numbers_and_dates(client):
    s1 = client.post("/api/sprints/next", json={"start_date": "2026-10-05", "goal": "[Goal]"}).json()
    assert (s1["number"], s1["start_date"], s1["end_date"]) == (1, "2026-10-05", "2026-10-18")
    s2 = client.post("/api/sprints/next", json={}).json()
    assert (s2["number"], s2["start_date"], s2["end_date"]) == (2, "2026-10-19", "2026-11-01")
    assert client.post("/api/sprints/next", json={"start_date": "soon"}).status_code == 400


def test_current_sprint(client):
    client.post("/api/sprints/next", json={"start_date": day(-20)})
    current = client.post("/api/sprints/next", json={"start_date": day(-2)}).json()
    assert client.get("/api/sprints/current").json()["id"] == current["id"]


def test_retro_follow_up_carries_into_next_sprint(client):
    s1 = client.post("/api/sprints/next", json={"start_date": day(-20)}).json()
    s2 = client.post("/api/sprints/next", json={}).json()
    note = client.post("/api/ceremony-notes", json={"sprint_id": s1["id"], "type": "retro", "follow_ups": "[Fix deploys]\n[Other]"}).json()
    item = client.post(f"/api/ceremony-notes/{note['id']}/follow-up", json={}).json()
    assert item["concern"] == "[Fix deploys]" and item["origin"] == "retro" and item["sprint_id"] == s1["id"]
    nb = client.get(f"/api/sprints/{s2['id']}/notebook").json()
    assert [i["concern"] for i in nb["carry_over"]] == ["[Fix deploys]"] and nb["previous_id"] == s1["id"]
    client.patch(f"/api/actions/{item['id']}", json={"status": "done"})
    assert client.get(f"/api/sprints/{s2['id']}/notebook").json()["carry_over"] == []


def test_ceremony_notes_private(client):
    s = client.post("/api/sprints/next", json={"goal": "[Shown goal]"}).json()
    client.post("/api/ceremony-notes", json={"sprint_id": s["id"], "noticed": "[Private]"})
    client.post("/api/session/presentation", json={"on": True})
    nb = client.get(f"/api/sprints/{s['id']}/notebook").json()
    assert nb["notes"] == [] and nb["sprint"]["goal"] == "[Shown goal]"
    assert "note_count" not in client.get("/api/sprints").json()[0]


# ---- RACI ----


def test_raci_cells_roles_and_accountable(client):
    d = client.post("/api/raci-decisions", json={"decision": "[Decision]"}).json()
    assert client.put(f"/api/raci/{d['id']}/cell", json={"role": "Product", "letter": "A"}).json()["accountable_count"] == 1
    assert client.put(f"/api/raci/{d['id']}/cell", json={"role": "Architect", "letter": "A"}).json()["accountable_count"] == 2
    client.put(f"/api/raci/{d['id']}/cell", json={"role": "Architect", "letter": None})
    assert client.get("/api/raci").json()["decisions"][0]["cells"] == {"Product": "A"}
    assert client.put(f"/api/raci/{d['id']}/cell", json={"role": "Nobody", "letter": "R"}).status_code == 400
    assert client.put(f"/api/raci/{d['id']}/cell", json={"role": "Product", "letter": "X"}).status_code == 400
    client.put("/api/raci/roles", json={"roles": ["[Role A]", "[Role B]"]})
    assert client.get("/api/raci").json()["roles"] == ["[Role A]", "[Role B]"]
    assert any(c["entity"] == "raci_decision" for c in client.get("/api/changes").json())


# ---- starter content ----


def test_starter_loads_once(client):
    loaded = client.post("/api/delivery/starter").json()
    assert loaded == {"roadmap_items": 15, "raci_decisions": 5, "metrics": 4}
    assert client.post("/api/delivery/starter").status_code == 409


# ---- status draft ----


def test_status_draft_overall_and_sections(client):
    client.put("/api/toolkit/settings", json={"start_date": day(-10)})
    assert client.get("/api/status/draft").json()["overall"] == "Green"
    r = client.post("/api/roadmap", json={"title": "[Shipped item]", "target_day": 5}).json()
    client.patch(f"/api/roadmap/{r['id']}", json={"status": "done"})
    client.post("/api/roadmap", json={"title": "[Due soon]", "target_day": 14})
    client.post("/api/roadmap", json={"title": "[At risk]", "target_day": 30, "status": "at risk"})
    assert client.get("/api/status/draft").json()["overall"] == "Yellow"
    client.post("/api/risks", json={"title": "[High risk]", "level": "high"})
    draft = client.get("/api/status/draft").json()
    assert draft["overall"] == "Red"
    md = draft["markdown"]
    assert "- [Shipped item]" in md and "- [Due soon]" in md and "[High risk]" in md and "[Placeholder" in md


def test_status_draft_has_only_exportable_data(client):
    client.post("/api/learning-goals", json={"goal": "[Reported goal]", "show_in_report": True})
    client.post("/api/learning-goals", json={"goal": "[Private goal]"})
    client.post("/api/risks", json={"title": "[Risk]", "notes": "[Private risk note]"})
    md = client.get("/api/status/draft").json()["markdown"]
    assert "[Reported goal]" in md and "[Private goal]" not in md and "[Private risk note]" not in md
    token = client.post("/api/tokens", json={"name": "comms", "scopes": ["export:read"]}).json()["token"]
    anon = TestClient(client.app, follow_redirects=False)
    anon.headers["Authorization"] = f"Bearer {token}"
    assert anon.get("/api/status/draft").json()["markdown"] == md
    assert anon.post("/api/status/export").status_code == 403


def test_status_export_is_logged(client):
    client.post("/api/status/export")
    assert client.get("/api/exports").json()[0]["kind"] == "status:markdown"


# ---- comms connection ----


@pytest.fixture
def comms(tmp_path):
    c = TestClient(build_comms(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path / "comms")), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_comms_pulls_status_with_token(comms, monkeypatch):
    assert comms.get("/api/toolkit/status-draft").status_code == 400
    assert comms.put("/api/connections", json={"toolkit_url": "ftp://x"}).status_code == 400
    saved = comms.put("/api/connections", json={"toolkit_url": "http://127.0.0.1:8801", "toolkit_token": "ba_[placeholder]"}).json()
    assert saved == {"toolkit_url": "http://127.0.0.1:8801", "token_set": True}
    calls = []

    def fake_fetch(url, token, path, timeout=5.0):
        calls.append((url, token, path))
        return {"week_of": "2026-10-12", "overall": "Green", "markdown": "[Placeholder draft]"}

    monkeypatch.setattr(messaging, "fetch_toolkit", fake_fetch)
    assert comms.get("/api/toolkit/status-draft").json()["markdown"] == "[Placeholder draft]"
    assert calls == [("http://127.0.0.1:8801", "ba_[placeholder]", "/api/status/draft")]
    assert comms.put("/api/connections", json={"clear_token": True}).json()["token_set"] is False


def test_comms_reports_unreachable_toolkit(comms):
    comms.put("/api/connections", json={"toolkit_url": "http://127.0.0.1:9", "toolkit_token": "ba_[placeholder]"})
    res = comms.get("/api/toolkit/status-draft")
    assert res.status_code == 502 and "Couldn't reach" in res.json()["detail"]
