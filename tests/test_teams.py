from datetime import date, timedelta

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


def day(n):
    return (date.today() + timedelta(days=n)).isoformat()


def test_upgrade_puts_existing_work_on_my_team(tmp_path):
    db = Database(tmp_path / "old.db")
    with db.session() as conn:
        migrate(conn, "toolkit", models.MIGRATIONS[:16])
        conn.execute("INSERT INTO action_items (concern) VALUES ('[Existing]')")
        conn.execute("INSERT INTO sprints (number) VALUES (1)")
        migrate(conn, "toolkit", models.MIGRATIONS)
        mine = conn.execute("SELECT id FROM teams WHERE kind = 'mine'").fetchone()[0]
        assert conn.execute("SELECT team_id FROM action_items").fetchone()[0] == mine
        assert conn.execute("SELECT team_id FROM sprints").fetchone()[0] == mine


def test_new_records_default_to_my_team(client):
    mine = client.get("/api/teams").json()[0]
    assert (mine["name"], mine["kind"]) == ("My team", "mine")
    other = client.post("/api/teams", json={"name": "[Other team]"}).json()
    assert client.post("/api/actions", json={"concern": "[Mine]"}).json()["team_id"] == mine["id"]
    assert client.post("/api/risks", json={"title": "[Theirs]", "team_id": other["id"]}).json()["team_id"] == other["id"]


def test_each_team_numbers_its_own_sprints(client):
    other = client.post("/api/teams", json={"name": "[Other team]"}).json()
    a1 = client.post("/api/sprints/next", json={"start_date": day(-3)}).json()
    a2 = client.post("/api/sprints/next", json={}).json()
    b1 = client.post("/api/sprints/next", json={"team_id": other["id"], "start_date": day(-1)}).json()
    assert (a1["number"], a2["number"], b1["number"]) == (1, 2, 1)
    assert client.get("/api/sprints/current").json()["id"] == a1["id"]


def test_planning_uses_team_members_and_team_velocity(client):
    dev = client.post("/api/people", json={"name": "[Dev]", "relationship": "employee"}).json()["id"]
    client.post("/api/people", json={"name": "[Someone else]", "relationship": "employee"})
    mine = client.get("/api/teams").json()[0]
    client.patch(f"/api/teams/{mine['id']}", json={"member_ids": [dev]})
    s = client.post("/api/sprints/next", json={"start_date": day(7)}).json()
    people = client.get(f"/api/sprint-planning/{s['id']}").json()["people"]
    assert [p["name"] for p in people] == ["[Dev]"]


def test_status_is_dated_and_my_team_is_protected(client):
    mine = client.get("/api/teams").json()[0]
    t = client.patch(f"/api/teams/{mine['id']}", json={"status": "at risk", "status_note": "[Note]"}).json()
    assert t["status_date"] == day(0)
    assert client.patch(f"/api/teams/{mine['id']}", json={"kind": "other"}).status_code == 400
    assert client.delete(f"/api/teams/{mine['id']}").status_code == 400
    other = client.post("/api/teams", json={"name": "[Other]"}).json()
    assert client.delete(f"/api/teams/{other['id']}").status_code == 204


def test_scrum_of_scrums_log_meeting_summary_and_today(client):
    mine = client.get("/api/teams").json()[0]
    other = client.post("/api/teams", json={"name": "[Other team]", "current_sprint": "[Their sprint 4]", "status": "on track"}).json()
    owner = client.post("/api/people", json={"name": "[Owner]"}).json()["id"]
    late = client.post("/api/sos-items", json={"question": "[Shared API contract]", "kind": "dependency", "team_ids": [mine["id"], other["id"]], "owner_id": owner,
                                              "outcome": "[Agreed contract]", "due": day(-2), "jira_keys": "abc-5", "notes": "[Private]"}).json()
    client.post("/api/sos-items", json={"question": "[Settled]", "status": "done", "resolution": "[Decided X]", "owner_team_id": other["id"]})
    o = client.get("/api/sos/overview").json()
    assert o["overdue"] == [late["id"]] and o["counts"]["dependency"] == 1
    ov = {t["name"]: t for t in client.get("/api/teams/overview").json()}
    assert ov["[Other team]"]["open_sos"] == 1 and ov["[Other team]"]["dependencies"] == 1 and ov["[Other team]"]["overdue_sos"] == 1
    assert [i["question"] for i in client.get(f"/api/teams/{other['id']}/detail").json()["sos_open"]] == ["[Shared API contract]"]
    m = client.post("/api/sos/meetings/start").json()
    assert m["item_ids"] == [late["id"]] and len(m["team_ids"]) == 2
    md = client.post("/api/sos/summary/export").json()["markdown"]
    assert "| [Other team] | on track" in md and "[Their sprint 4]" in md and "## Overdue" in md and "[Shared API contract] (ABC-5)" in md
    assert "[Settled]: [Decided X]" in md and "[Private]" not in md
    assert client.get("/api/today").json()["sos_due"][0]["overdue"] is True
    assert [f["kind"] for f in client.get("/api/jira/ABC-5").json()["found"]] == ["Scrum of Scrums item"]
