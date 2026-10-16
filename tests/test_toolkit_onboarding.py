from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagile.core.config import Settings
from beanagile.toolkit import onboarding
from beanagile.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def person(client, name="[New member]"):
    return client.post("/api/people", json={"name": name, "role": "[Role]"}).json()["id"]


def test_starter_loads_once(client):
    assert client.post("/api/onboarding/starter").json()["items"] == len(onboarding.STARTER)
    assert client.post("/api/onboarding/starter").status_code == 409


def test_starter_invents_nothing_specific():
    """Company-specific details stay as [Placeholder] for David to fill in."""
    for day, owner, cat, title, desc, link, tracks in onboarding.STARTER:
        assert link == "" or link.startswith("#/")
        for word in ("Jira", "Okta", "Slack", "Teams", "Workday", "Confluence"):
            assert word not in title + desc


def test_checklist_follows_tracks_and_dates(client):
    client.post("/api/onboarding/starter")
    pid = person(client)
    sf = client.post("/api/onboardings", json={"person_id": pid, "start_date": "2026-11-02", "tracks": ["Salesforce developer", "employee"]}).json()
    qa = client.post("/api/onboardings", json={"person_id": person(client, "[QA person]"), "tracks": ["QA", "contractor"]}).json()
    everyone = sum(1 for s in onboarding.STARTER if not s[6])
    assert sf["copied"] == everyone + sum(1 for s in onboarding.STARTER if s[6] and set(s[6]) & {"Salesforce developer", "employee"})
    titles = {t["title"] for p in client.get(f"/api/onboardings/{qa['id']}/board").json()["phases"] for t in p["tasks"]}
    assert "Run a MuleSoft application locally and deploy it to a non-production environment" not in titles
    assert "Confirm contract dates, agency contact and how time is reported" in titles
    board = client.get(f"/api/onboardings/{sf['id']}/board").json()
    assert [p["name"] for p in board["phases"]] == ["Before day 1", "Week 1", "Weeks 2 to 4", "Days 31 to 90"]
    first = board["phases"][1]["tasks"][0]
    assert first["due_day"] == 1 and first["due"] == "2026-11-02"
    assert board["phases"][0]["tasks"][0]["due"] == "2026-10-26"  # day -7: a week before


def test_done_sets_date_and_progress(client):
    client.post("/api/onboarding-items", json={"title": "[Item]", "due_day": 1})
    ob = client.post("/api/onboardings", json={"person_id": person(client)}).json()
    tid = client.get(f"/api/onboardings/{ob['id']}/board").json()["phases"][0]["tasks"][0]["id"]
    done = client.patch(f"/api/onboarding-tasks/{tid}", json={"done": True}).json()
    assert done["done"] and done["done_on"] == date.today().isoformat()
    assert client.get(f"/api/onboardings/{ob['id']}").json()["done_count"] == 1
    assert client.patch(f"/api/onboarding-tasks/{tid}", json={"done": False}).json()["done_on"] is None


def test_template_edits_dont_touch_started_checklists(client):
    item = client.post("/api/onboarding-items", json={"title": "[Original]", "due_day": 2}).json()
    ob = client.post("/api/onboardings", json={"person_id": person(client)}).json()
    client.patch(f"/api/onboarding-items/{item['id']}", json={"title": "[Changed]"})
    client.post("/api/onboarding-items", json={"title": "[Retired]", "active": False})
    tasks = client.get(f"/api/onboardings/{ob['id']}/board").json()["phases"][0]["tasks"]
    assert [t["title"] for t in tasks] == ["[Original]"]


def test_checklist_markdown_and_today(client):
    start = (date.today() - timedelta(days=3)).isoformat()
    client.post("/api/onboarding-items", json={"title": "[Manager prep]", "due_day": -1, "owner_role": "manager"})
    client.post("/api/onboarding-items", json={"title": "[Read this]", "due_day": 2, "link": "#/sdlc"})
    client.post("/api/onboarding-items", json={"title": "[Course]", "due_day": 5, "link": "https://example.invalid/course"})
    buddy = person(client, "[Buddy]")
    ob = client.post("/api/onboardings", json={"person_id": person(client), "start_date": start, "buddy_id": buddy}).json()
    tasks = client.get(f"/api/onboardings/{ob['id']}/board").json()
    assert tasks["overdue"] == 2 and tasks["by_owner"]["manager"] == 1
    client.patch(f"/api/onboarding-tasks/{tasks['phases'][0]['tasks'][0]['id']}", json={"notes": "[Private note]"})
    md = client.post(f"/api/onboardings/{ob['id']}/checklist/export").json()["markdown"]
    assert "# Welcome, [New member]" in md and "Your buddy: [Buddy]." in md
    assert "- [ ] [Manager prep] (manager)" in md and "#/sdlc" not in md and "https://example.invalid/course" in md and "[Private note]" not in md
    assert client.get("/api/exports").json()[0]["kind"] == "onboarding:markdown"
    due = client.get("/api/today").json()["onboarding_due"]
    assert [d["title"] for d in due] == ["[Manager prep]"] and due[0]["overdue"]


def test_needs_a_real_person(client):
    assert client.post("/api/onboardings", json={"person_id": 999}).status_code == 400
