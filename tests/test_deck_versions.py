import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms.app import build
from beanagileorg.core.config import Settings

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def deck(client):
    d = client.post("/api/decks", json={"title": "[Deck]"}).json()
    a = client.post(f"/api/decks/{d['id']}/slides", json={"layout": "title", "content": {"heading": "[Title slide]"}}).json()
    b = client.post(f"/api/decks/{d['id']}/slides", json={"layout": "bullets", "content": {"heading": "[Points]", "items": ["[One]"]}}).json()
    return d, a, b


def test_save_versions_and_compare(client):
    d, a, b = deck(client)
    v1 = client.post(f"/api/decks/{d['id']}/versions", json={"label": "[First cut]", "note": "[Note]"}).json()
    assert (v1["number"], v1["slide_count"], v1["status"]) == (1, 2, "draft")
    client.patch(f"/api/slides/{b['id']}", json={"content": {"heading": "[Points, reworded]", "items": ["[One]"]}})
    c = client.post(f"/api/decks/{d['id']}/slides", json={"layout": "closing", "content": {"heading": "[Thanks]"}}).json()
    client.delete(f"/api/slides/{a['id']}")
    diff = client.get(f"/api/decks/{d['id']}/compare?a=1").json()
    assert [x["title"] for x in diff["added"]] == ["[Thanks]"] and [x["title"] for x in diff["removed"]] == ["[Title slide]"]
    assert diff["changed"][0]["fields"] == ["content: heading"]
    listed = client.get(f"/api/decks/{d['id']}/versions").json()
    assert listed["versions"][0]["label"] == "[First cut]" and listed["next"] == ["in review", "approved"]


def test_workflow_locks_approved_decks(client):
    d, a, b = deck(client)
    r = client.post(f"/api/decks/{d['id']}/status", json={"status": "in review", "note": "[For Brian]"}).json()
    assert r["status"] == "in review" and r["version"]["kind"] == "sent for review"
    assert client.post(f"/api/decks/{d['id']}/status", json={"status": "presented"}).status_code == 400
    client.post(f"/api/decks/{d['id']}/status", json={"status": "approved"})
    locked = client.patch(f"/api/slides/{a['id']}", json={"notes": "[Edit]"})
    assert locked.status_code == 409 and "Start a new draft" in locked.json()["detail"]
    assert client.post(f"/api/decks/{d['id']}/slides", json={"layout": "section"}).status_code == 409
    assert client.patch(f"/api/decks/{d['id']}", json={"title": "[New title]"}).status_code == 409
    assert client.patch(f"/api/decks/{d['id']}", json={"status": "draft"}).status_code == 400
    p = client.post(f"/api/decks/{d['id']}/status", json={"status": "presented", "presented_on": "2026-11-20", "audience": "[Leadership]"}).json()
    assert p["version"]["kind"] == "presented"
    deckrow = client.get(f"/api/decks/{d['id']}").json()
    assert (deckrow["status"], deckrow["presented_on"], deckrow["audience"]) == ("presented", "2026-11-20", "[Leadership]")
    nd = client.post(f"/api/decks/{d['id']}/status", json={"status": "draft"}).json()
    assert nd["version"]["kind"] == "new draft"
    assert client.patch(f"/api/slides/{a['id']}", json={"notes": "[Edit]"}).status_code == 200
    kinds = [v["kind"] for v in client.get(f"/api/decks/{d['id']}/versions").json()["versions"]]
    assert kinds == ["new draft", "presented", "approved", "sent for review"]


def test_restore_keeps_slide_ids_and_saves_first(client):
    d, a, b = deck(client)
    client.post(f"/api/decks/{d['id']}/versions", json={})
    client.delete(f"/api/slides/{a['id']}")
    client.patch(f"/api/slides/{b['id']}", json={"notes": "[Changed]"})
    client.post(f"/api/decks/{d['id']}/slides", json={"layout": "quote", "content": {"quote": "[Extra]"}})
    r = client.post(f"/api/decks/{d['id']}/versions/1/restore").json()
    assert r == {"restored": 1, "saved_first": 2}
    full = client.get(f"/api/decks/{d['id']}/full").json()
    assert sorted(s["id"] for s in full["slides"]) == sorted([a["id"], b["id"]])
    assert next(s for s in full["slides"] if s["id"] == b["id"])["notes"] is None
    assert client.get(f"/api/decks/{d['id']}/compare?a=1").json() == {"a": 1, "b": "current", "deck": [], "added": [], "removed": [], "changed": [], "moved": []}


def test_present_a_version_and_copy(client):
    d, a, b = deck(client)
    client.post(f"/api/decks/{d['id']}/versions", json={"label": "[Approved one]"})
    client.patch(f"/api/slides/{a['id']}", json={"content": {"heading": "[Newer title]"}})
    old = client.get(f"/api/decks/{d['id']}/versions/1/full").json()
    assert old["slides"][0]["content"]["heading"] == "[Title slide]" and old["version"]["label"] == "[Approved one]" and "media" in old
    cp = client.post(f"/api/decks/{d['id']}/copy", json={"title": "[For the team]"}).json()
    assert cp["title"] == "[For the team]" and cp["status"] == "draft" and "[Deck], version 1" in cp["copied_from"]
    assert len(client.get(f"/api/decks/{cp['id']}/full").json()["slides"]) == 2
    assert client.get(f"/api/decks/{cp['id']}/versions").json()["versions"][0]["kind"] == "copied"
    assert client.get(f"/api/decks/{d['id']}/versions/9/full").status_code == 404
