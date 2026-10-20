"""Learning answers into the landscape, suggested questions, the change list, the stakeholder map, balance and mentoring."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def test_learning_answers_become_assessments_and_themes_suggest_questions(c):
    q = c.post("/api/learning-questions", json={"question": "[How do releases work?]"}).json()["id"]
    dept = c.post("/api/departments", json={"name": "[Engineering]"}).json()["id"]
    assert c.post(f"/api/learning-questions/{q}/to-assessment", json={"subject_type": "department", "subject_id": dept}).status_code == 409
    c.patch(f"/api/learning-questions/{q}", json={"answer": "[Manual deploys on Fridays]\n[More detail]"})
    a = c.post(f"/api/learning-questions/{q}/to-assessment", json={"subject_type": "department", "subject_id": dept, "quadrant": "threat"}).json()
    assert a["title"] == "[Manual deploys on Fridays]" and a["quadrant"] == "threat" and "[How do releases work?]" in a["evidence"]
    pid = c.post("/api/people", json={"name": "[P1]", "active": True}).json()["id"]
    c.post("/api/interviews", json={"person_id": pid, "status": "done", "themes": ["[Release pain]", "[unclear priorities]"]})
    c.post("/api/interviews", json={"person_id": pid, "status": "done", "themes": ["[release pain]"]})
    s = c.get("/api/learning-questions/suggestions").json()["suggestions"]
    assert s[0]["theme"] == "[release pain]" and s[0]["times"] == 2


def test_change_list_links_and_stakeholder_map(c):
    ag = c.post("/api/team-agreements", json={"text": "[Standup at 9:30]", "status": "agreed"}).json()["id"]
    pol = c.post("/api/sdlc-policies", json={"title": "[Two approvals]"}).json()["id"]
    c.post("/api/team-changes", json={"title": "[Daily standup]", "why": "[See blockers early]", "status": "adopted", "agreement_id": ag})
    c.post("/api/team-changes", json={"title": "[Pull requests]", "status": "trial", "how_we_try": "[Two sprints]", "policy_id": pol, "notes": "[Private note]"})
    md = c.get("/api/team-changes/summary").json()["markdown"]
    assert md.index("## Trial") < md.index("## Adopted") and "Became our agreement: [Standup at 9:30]" in md and "Became our SDLC policy: [Two approvals]" in md
    assert "[Private note]" not in md
    c.post("/api/people", json={"name": "[Skeptic]", "active": True, "influence": "high", "stance": "skeptic", "need_from_them": "[Sign-off]"})
    c.post("/api/people", json={"name": "[Half known]", "active": True, "influence": "low"})
    m = c.get("/api/people/stakeholder-map").json()
    assert m["grid"]["high"]["skeptic"][0]["name"] == "[Skeptic]" and m["focus"][0]["name"] == "[Skeptic]" and m["unplaced"][0]["name"] == "[Half known]"


def test_working_with_me_field_and_mentoring_in_my_manager_report(c):
    pid = c.post("/api/people", json={"name": "[Report 1]", "active": True, "working_with_me": "[Mornings are for focus]"}).json()
    assert pid["working_with_me"] == "[Mornings are for focus]"
    mgr = c.post("/api/people", json={"name": "[Other manager]", "active": True}).json()["id"]
    c.post("/api/mentoring-sessions", json={"person_id": mgr, "date": date.today().isoformat(), "topic": "[Retros]", "notes": "[Private]"})
    c.post("/api/mentored-practices", json={"person_id": mgr, "practice": "[Retro formats]", "status": "adopted", "since": date.today().isoformat()})
    wk = c.get("/api/weeks").json()["start"]
    mine = c.get(f"/api/reports/weekly?week={wk}&audience=my%20manager").json()["markdown"]
    assert "## Mentoring the other managers" in mine and "[Other manager] adopted [Retro formats]" in mine and "[Private]" not in mine
    assert "Mentoring the other managers" not in c.get(f"/api/reports/weekly?week={wk}").json()["markdown"]
