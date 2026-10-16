import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.core.db import Database, migrate
from beanagileorg.toolkit import models
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_keys_are_cleaned_and_checked(client):
    a = client.post("/api/actions", json={"concern": "[Concern]", "jira_keys": "abc-1, ABC-1 def-22"}).json()
    assert a["jira_keys"] == ["ABC-1", "DEF-22"]
    assert client.patch(f"/api/actions/{a['id']}", json={"jira_keys": ["xyz-3"]}).json()["jira_keys"] == ["XYZ-3"]
    bad = client.patch(f"/api/actions/{a['id']}", json={"jira_keys": "ABC-1, nope"})
    assert bad.status_code == 400 and "NOPE" in bad.json()["detail"]
    assert client.patch(f"/api/actions/{a['id']}", json={"jira_keys": ""}).json()["jira_keys"] == []


def test_single_jira_key_fields(client):
    pi = client.post("/api/program-increments", json={"number": 1}).json()
    f = client.post("/api/features", json={"pi_id": pi["id"], "title": "[Feature]", "ticket_key": "abc-9"}).json()
    assert f["ticket_key"] == "ABC-9"
    assert client.patch(f"/api/features/{f['id']}", json={"ticket_key": "ABC-1, ABC-2"}).status_code == 400
    assert client.patch(f"/api/features/{f['id']}", json={"ticket_key": ""}).json()["ticket_key"] is None


def test_jira_address_setting(client):
    assert client.put("/api/toolkit/settings", json={"jira_url": "placeholder.atlassian.net"}).status_code == 400
    s = client.put("/api/toolkit/settings", json={"jira_url": "https://placeholder.atlassian.net/"}).json()
    assert s["jira_url"] == "https://placeholder.atlassian.net"
    client.put("/api/toolkit/settings", json={"start_date": "2026-11-02"})
    assert client.get("/api/toolkit/settings").json() == {"start_date": "2026-11-02", "jira_url": "https://placeholder.atlassian.net"}
    assert client.put("/api/toolkit/settings", json={"jira_url": ""}).json()["jira_url"] is None


def test_find_everything_that_mentions_a_key(client):
    client.post("/api/actions", json={"concern": "[Dev-sync item]", "jira_keys": ["ABC-1"]})
    client.post("/api/risks", json={"title": "[Risk]", "jira_keys": ["ABC-1", "ABC-10"]})
    client.post("/api/tech-debt", json={"title": "[Debt]", "ticket_key": "ABC-1"})
    client.post("/api/test-cases", json={"title": "[Case]", "jira_keys": ["ABC-10"]})
    found = client.get("/api/jira/abc-1").json()
    assert found["key"] == "ABC-1"
    assert sorted((f["kind"], f["title"]) for f in found["found"]) == [("Dev-sync item", "[Dev-sync item]"), ("Risk", "[Risk]"), ("Tech debt", "[Debt]")]
    assert [f["kind"] for f in client.get("/api/jira/ABC-10").json()["found"]] == ["Risk", "Test case"]
    assert client.get("/api/jira/not-a-key").status_code == 400


def test_run_summary_lists_bug_keys(client):
    c = client.post("/api/test-cases", json={"title": "[Checkout]"}).json()
    run = client.post("/api/test-runs", json={"name": "[Run]", "case_ids": [c["id"]]}).json()
    rid = client.get(f"/api/test-runs/{run['id']}/board").json()["results"][0]["id"]
    client.patch(f"/api/test-results/{rid}", json={"result": "fail", "jira_keys": "abc-77"})
    assert "- [Checkout] [ABC-77]" in client.get(f"/api/test-runs/{run['id']}/summary").json()["markdown"]


def test_upgrade_adds_jira_columns(tmp_path):
    db = Database(tmp_path / "old.db")
    with db.session() as conn:
        migrate(conn, "toolkit", models.MIGRATIONS[:13])
        conn.execute("INSERT INTO risks (title) VALUES ('[Existing]')")
        migrate(conn, "toolkit", models.MIGRATIONS)
        assert tuple(conn.execute("SELECT title, jira_keys FROM risks").fetchone()) == ("[Existing]", None)
