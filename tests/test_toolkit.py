from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build
from beanagileorg.core.dates import add_months, next_occurrence

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def token(client, scopes):
    return client.post("/api/tokens", json={"name": "-".join(scopes), "scopes": scopes}).json()["token"]


def as_token(client, tok):
    anon = TestClient(client.app, follow_redirects=False)
    anon.headers["Authorization"] = f"Bearer {tok}"
    return anon


def present(client, on=True):
    client.post("/api/session/presentation", json={"on": on})


# ---- records ----


def test_person_crud_and_change_log(client):
    rec = client.post("/api/people", json={"name": "[Placeholder name]", "skills": ["[Placeholder skill]", " "]}).json()
    assert rec["skills"] == ["[Placeholder skill]"] and rec["active"] is True
    updated = client.patch(f"/api/people/{rec['id']}", json={"role": "[Placeholder role]"}).json()
    assert updated["role"] == "[Placeholder role]"
    fields = {c["field"] for c in client.get("/api/changes").json() if c["entity"] == "person"}
    assert {"name", "role", "skills"} <= fields
    assert client.delete(f"/api/people/{rec['id']}").status_code == 204
    assert client.get(f"/api/people/{rec['id']}").status_code == 404


def test_validation(client):
    assert client.post("/api/people", json={}).status_code == 400
    assert client.post("/api/people", json={"name": "x", "nickname": "y"}).status_code == 400
    assert client.post("/api/people", json={"name": "x", "relationship": "friend"}).status_code == 400
    assert client.post("/api/people", json={"name": "x", "start_date": "Nov 2"}).status_code == 400
    assert client.post("/api/learning-log", json={"goal_id": 999, "minutes": 10}).status_code == 400


def test_people_in_presentation_mode_show_names_roles_and_department_only(client):
    client.post("/api/people", json={"name": "[Placeholder name]", "role": "[Placeholder role]", "support_notes": "[Placeholder]"})
    present(client)
    shown = client.get("/api/people").json()[0]
    assert set(shown) == {"id", "name", "role", "relationship", "active", "department_id", "department_name", "manager_id", "manager_name"}


def test_export_token_sees_no_people_or_one_on_ones(client):
    pid = client.post("/api/people", json={"name": "[Placeholder name]"}).json()["id"]
    client.post("/api/interviews", json={"person_id": pid, "status": "done", "themes": ["[Placeholder theme]"]})
    export = as_token(client, token(client, ["export:read"]))
    assert export.get("/api/people").json() == [{"id": pid}]
    assert export.get("/api/interviews").json() == []
    assert export.post("/api/people", json={"name": "x"}).status_code == 403


def test_one_on_ones_hidden_while_presenting(client):
    client.post("/api/interviews", json={"status": "planned", "working": "[Placeholder]"})
    present(client)
    assert client.get("/api/interviews").json() == []


def test_learning_goals_reportable_only_when_marked(client):
    client.post("/api/learning-goals", json={"goal": "[Placeholder goal A]", "show_in_report": True})
    hidden = client.post("/api/learning-goals", json={"goal": "[Placeholder goal B]"}).json()
    client.post("/api/learning-log", json={"goal_id": hidden["id"], "minutes": 30})
    export = as_token(client, token(client, ["export:read"]))
    goals = export.get("/api/learning-goals").json()
    assert [g["goal"] for g in goals] == ["[Placeholder goal A]"]
    assert "show_in_report" not in goals[0] and "privacy_ceiling" not in goals[0]
    mine = {g["goal"]: g for g in client.get("/api/learning-goals").json()}
    assert mine["[Placeholder goal B]"]["minutes"] == 30


# ---- computed views ----


def test_rollup_counts_and_privacy(client):
    pid = client.post("/api/people", json={"name": "[Placeholder name]"}).json()["id"]
    for themes in (["[T1]", "[T2]"], ["[T1]"]):
        client.post(
            "/api/interviews",
            json={"person_id": pid, "status": "done", "themes": themes, "systems": ["[S]"], "gaps": "[Placeholder gap]"},
        )
    client.post("/api/interviews", json={"status": "planned"})
    full = client.get("/api/rollup").json()
    assert full["done"] == 2 and full["planned"] == 1
    assert full["themes"][0] == {"theme": "[T1]", "count": 2}
    assert full["notes"]["gaps"][0]["text"] == "[Placeholder gap]"
    assert "[Placeholder gap]" in client.get("/api/rollup/markdown").json()["markdown"]
    export = as_token(client, token(client, ["export:read"]))
    assert set(export.get("/api/rollup").json()) == {"done", "planned", "themes"}
    present(client)
    shown = client.get("/api/rollup").json()
    assert "notes" not in shown and "systems" in shown
    assert client.get("/api/rollup/markdown").status_code == 403


def test_skills_matrix_and_matches(client):
    client.post("/api/people", json={"name": "[A]", "skills": ["[X]"], "can_teach": ["[X]"]})
    client.post("/api/people", json={"name": "[B]", "wants_to_learn": ["[X]"]})
    full = client.get("/api/skills").json()
    assert full["matches"] == [{"topic": "[X]", "teachers": ["[A]"], "learners": ["[B]"]}]
    present(client)
    shown = client.get("/api/skills").json()
    assert "matrix" not in shown and shown["skills"][0] == {"skill": "[X]", "people": 1, "can_teach": 1, "wants_to_learn": 1}


def test_today_and_placeholder_seed(client):
    assert client.get("/api/today").json()["people_count"] == 0
    loaded = client.post("/api/seed-placeholders").json()
    assert loaded["people"] == 8
    assert client.post("/api/seed-placeholders").status_code == 409
    today = client.get("/api/today").json()
    assert len(today["overdue_tasks"]) == 1 and len(today["upcoming_interviews"]) == 2
    names = [p["name"] for p in client.get("/api/people").json()]
    assert all(n.startswith("[Placeholder") for n in names)
    present(client)
    assert client.get("/api/today").json() == {"hidden": True}


def test_obligation_done_advances(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    ob = client.post("/api/obligations", json={"title": "[Placeholder]", "cadence": "weekly", "next_due": yesterday}).json()
    done = client.post(f"/api/obligations/{ob['id']}/done").json()
    assert done["last_done"] == date.today().isoformat()
    assert done["next_due"] == (date.today() + timedelta(days=6)).isoformat()
    once = client.post("/api/obligations", json={"title": "[Placeholder]", "cadence": "once"}).json()
    assert client.post(f"/api/obligations/{once['id']}/done").json()["next_due"] is None


def test_start_date_setting(client):
    assert client.put("/api/toolkit/settings", json={"start_date": "bad"}).status_code == 400
    assert client.put("/api/toolkit/settings", json={"start_date": "2026-11-02"}).json()["start_date"] == "2026-11-02"
    assert client.get("/api/toolkit/settings").json()["start_date"] == "2026-11-02"


def test_date_helpers():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert next_occurrence(date(2026, 1, 1), "quarterly") == date(2026, 4, 1)
    assert next_occurrence(date(2026, 1, 1), "once") is None
