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


def people(client):
    return [client.post("/api/people", json={"name": n}).json()["id"] for n in ("[Asker]", "[Expert]", "[Decider]", "[Owner]")]


def test_board_and_update_script(client):
    asker, expert, decider, owner = people(client)
    a = client.post("/api/actions", json={"concern": "[Should we adopt X?]", "raised_by_id": asker, "owner_id": owner, "kind": "decision needed",
                                          "expert_ids": [expert], "decider_id": decider, "next_action": "[Spike X]", "due": (TODAY + timedelta(days=5)).isoformat(),
                                          "jira_keys": ["abc-7"], "notes": "[Private note]"}).json()["id"]
    client.post("/api/actions", json={"concern": "[Not shared]"})
    assert client.get("/api/dev-sync/board").json()["rows"] == []
    client.patch(f"/api/actions/{a}", json={"on_board": True, "status": "in progress", "update_url": "https://share.example/m/[token]", "update_on": TODAY.isoformat()})
    rows = client.get("/api/dev-sync/board").json()["rows"]
    assert len(rows) == 1 and rows[0]["experts"] == ["[Expert]"] and rows[0]["decider"] == "[Decider]" and rows[0]["kind"] == "decision needed"
    md = client.post("/api/dev-sync/board/export").json()["markdown"]
    assert "[Should we adopt X?] (ABC-7)" in md and "[Private note]" not in md and "[Not shared]" not in md and "share.example" in md
    s = client.get(f"/api/actions/{a}/update-script").json()["markdown"]
    assert "raised in dev sync by [Asker]" in s and "open to in progress" in s and "Worked through with [Expert]" in s
    assert "Decision with [Decider]" in s and "Next: [Spike X], owned by [Owner]" in s and "ABC-7" in s
    assert client.get("/api/actions/999/update-script").status_code == 404
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/dev-sync/board").json() == {"hidden": True}
    assert client.get(f"/api/actions/{a}/update-script").status_code == 403


def test_report_video_script(client):
    monday = TODAY - timedelta(days=TODAY.weekday())
    client.post("/api/log-entries", json={"date": TODAY.isoformat(), "kind": "win", "text": "[A win]"})
    client.post("/api/log-entries", json={"date": TODAY.isoformat(), "kind": "blocker", "text": "[A blocker]"})
    s = client.get(f"/api/reports/script?kind=weekly&week={monday.isoformat()}").json()
    assert s["title"].endswith("video script") and "## What went well\n- [A win]" in s["markdown"] and "[A blocker]" in s["markdown"]
    sid = client.post("/api/sprints", json={"number": 2, "start_date": monday.isoformat(), "end_date": (monday + timedelta(days=11)).isoformat(), "goal": "[Goal]"}).json()["id"]
    assert "## Results\n- 0 of 0 committed points done" in client.get(f"/api/reports/script?kind=sprint&sprint_id={sid}").json()["markdown"]
    assert client.get("/api/reports/script?kind=sprint").status_code == 400


def test_new_starters(client):
    client.post("/api/sdlc/starter")
    titles = [p["title"] for p in client.get("/api/sdlc-policies").json() if p["category"] == "communication"]
    assert set(titles) == {"When we miss a sprint commitment", "When a release breaks production", "When a risk becomes likely"}
    client.post("/api/culture/agreements/starter", json={})
    assert any("No meetings to plan meetings" in a["text"] for a in client.get("/api/team-agreements").json())
