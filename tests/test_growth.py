"""Agreements in the retro, growth paths, the new member's own onboarding page, and feedback into the template."""

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


def test_retro_shows_agreed_team_agreements(c):
    c.post("/api/team-agreements", json={"text": "[Standup at 9:30]", "status": "agreed", "review_on": "2026-10-01"})
    c.post("/api/team-agreements", json={"text": "[Proposed one]", "status": "proposed"})
    rid = c.post("/api/retros", json={"date": "2026-10-20", "format": "start / stop / continue"}).json()["id"]
    b = c.get(f"/api/retros/{rid}/board").json()
    assert [a["text"] for a in b["agreements"]] == ["[Standup at 9:30]"] and b["agreements"][0]["due_review"]


def test_growth_paths_place_reports(c):
    me = c.post("/api/people", json={"name": "[Me]", "active": True}).json()["id"]
    c.put("/api/people/me", json={"person_id": me})
    assert c.post("/api/growth-paths/starter").json()["levels"] == 4
    assert c.post("/api/growth-paths/starter").status_code == 409
    lv = c.get("/api/growth-paths").json()["tracks"][0]["levels"][1]["id"]
    rep = c.post("/api/people", json={"name": "[Report]", "active": True, "manager_id": me, "growth_level_id": lv}).json()["id"]
    g = c.get("/api/growth-paths").json()
    assert g["tracks"][0]["levels"][1]["people"] == [{"id": rep, "name": "[Report]"}] and g["reports"][0]["growth_level_id"] == lv


def test_new_member_page_and_feedback_to_template(c):
    pid = c.post("/api/people", json={"name": "[New 1]", "active": True}).json()["id"]
    c.post("/api/onboarding-items", json={"title": "[Read the SDLC]", "due_day": 2})
    ob = c.post("/api/onboardings", json={"person_id": pid}).json()["id"]
    c.put("/api/share-base-url", json={"base_url": "http://127.0.0.1:8801"})
    link = c.post(f"/api/onboardings/{ob}/links", json={}).json()
    assert link["recipient"] == "[New 1]" and link["url"].startswith("http://127.0.0.1:8801/shared/")
    path = "/shared/" + link["url"].split("/shared/")[1]
    c.cookies.clear()
    page = c.post(path, data={"code": link["code"]})
    assert page.status_code == 200 and "Welcome, [New 1]" in page.text and "[Read the SDLC]" in page.text
    c.post("/login", data={"password": PASSWORD})
    assert c.get(f"/api/onboardings/{ob}/links").json()["links"][0]["views"] == 1
    fb = c.post("/api/onboarding-feedback", json={"onboarding_id": ob, "date": "2026-10-20", "missing": "[Who to ask about sandboxes]", "suggestion": "[Sandbox walkthrough in week 1]"}).json()["id"]
    item = c.post(f"/api/onboarding-feedback/{fb}/to-item", json={"due_day": 5}).json()
    assert item["title"] == "[Sandbox walkthrough in week 1]" and item["due_day"] == 5
    assert c.get(f"/api/onboarding-feedback/{fb}").json()["status"] == "used"
