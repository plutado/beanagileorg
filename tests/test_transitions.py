"""Accelerating everyone (chapter 10): heat map, set-up-to-fail check, types, open seats, development grid, kit."""

from datetime import date, timedelta

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


def person(c, name, **kw):
    return c.post("/api/people", json={"name": name, "active": True, **kw}).json()["id"]


def test_heat_map_with_evidence_and_existing_support(c):
    recent = (date.today() - timedelta(days=30)).isoformat()
    a, b = person(c, "[New 1]", start_date=recent), person(c, "[Old 1]", start_date="2020-01-01")
    team = c.post("/api/teams", json={"name": "[Team A]", "kind": "mine", "member_ids": [a, b]}).json()["id"]
    c.post("/api/transition-units", json={"unit": "[Team A]", "team_id": team, "change_event": "[Rapid growth]", "onboarding": "high", "lateral": "medium"})
    c.post("/api/transition-units", json={"unit": "[Unit B]", "change_event": "[Acquisition]", "moves": "high"})
    c.post("/api/open-seats", json={"title": "[Engineer seat]", "team_id": team})
    t = c.get("/api/transitions").json()
    ev = t["units"][0]["evidence"]
    assert ev["started_recently"] == 1 and ev["open_seats"] == 1 and t["units"][1]["evidence"] is None
    assert set(t["priorities"]) == {"Onboarding: [Team A]", "Moves between teams: [Unit B]"}
    assert len(t["existing_support"]) == 7
    c.put("/api/transitions/existing-support", json={"contractors": {"status": "no", "note": "[Note]"}})
    assert next(x for x in c.get("/api/transitions").json()["existing_support"] if x["key"] == "contractors")["status"] == "no"
    assert c.put("/api/transitions/existing-support", json={"framework": {"status": "maybe"}}).status_code == 400


def test_types_add_items_and_risk_check(c):
    pid, buddy = person(c, "[Promoted 1]"), person(c, "[Buddy]")
    ob = c.post("/api/onboardings", json={"person_id": pid, "transition_type": "promotion", "buddy_id": buddy}).json()
    titles = {t["title"] for p in c.get(f"/api/onboardings/{ob['id']}/board").json()["phases"] for t in p["tasks"]}
    assert "Cover their old work: who takes it, and by when" in titles and "Agree what success looks like at the new level" in titles
    assert any(t.startswith("Day-7 check-in") for t in titles)
    rc = c.get(f"/api/onboardings/{ob['id']}/risk-check").json()
    keys = {i["key"]: i for i in rc["items"]}
    assert "old_job" in keys and "fit" not in keys  # promotion, not joining
    assert keys["support"]["status"] == "ok" and keys["expectations"]["status"] == "risk" and keys["old_job"]["status"] == "risk"
    task = next(t for p in c.get(f"/api/onboardings/{ob['id']}/board").json()["phases"] for t in p["tasks"] if t["title"].startswith("Cover their old work"))
    c.patch(f"/api/onboarding-tasks/{task['id']}", json={"done": True})
    rc = c.put(f"/api/onboardings/{ob['id']}/risk-check", json={"leap": {"status": "risk", "note": "[Big step]"}}).json()
    keys = {i["key"]: i for i in rc["items"]}
    assert keys["old_job"]["status"] == "ok" and keys["leap"]["note"] == "[Big step]" and rc["risks"] == 2
    joiner = c.post("/api/onboardings", json={"person_id": person(c, "[Joiner]"), "transition_type": "contractor"}).json()
    jk = {i["key"] for i in c.get(f"/api/onboardings/{joiner['id']}/risk-check").json()["items"]}
    assert {"fit", "culture_help", "stakeholders"} <= jk and "old_job" not in jk


def test_open_seat_hire_carries_risk_and_asks_for_lessons(c):
    team = c.post("/api/teams", json={"name": "[Team A]", "kind": "mine", "member_ids": []}).json()["id"]
    seat = c.post("/api/open-seats", json={"title": "[Salesforce developer]", "team_id": team, "situation": "turnaround", "risk_tolerance": "medium",
                                           "culture_notes": "[Direct feedback culture]"}).json()["id"]
    cand = c.post("/api/seat-candidates", json={"seat_id": seat, "name": "[Candidate 1]", "risks": {"situation": "[Only sustaining roles]", "leap": ""}}).json()["id"]
    start = (date.today() - timedelta(days=95)).isoformat()
    r = c.post(f"/api/open-seats/{seat}/hire", json={"candidate_id": cand, "start_date": start, "transition_type": "new hire"}).json()
    ob = c.get(f"/api/onboardings/{r['onboarding_id']}/risk-check").json()
    assert ob["risk_profile"] == {"situation": "[Only sustaining roles]", "culture": "[Direct feedback culture]"}
    assert {i["key"]: i["status"] for i in ob["items"]}["fit"] == "ok"
    assert r["person_id"] in c.get(f"/api/teams/{team}").json()["member_ids"]
    d = c.get(f"/api/open-seats/{seat}/detail").json()
    assert d["seat"]["status"] == "filled" and d["lessons_due"] and d["candidates"][0]["decision"] == "hired"
    assert [s["title"] for s in c.get("/api/today").json()["seats_due"]] == ["[Salesforce developer]"]
    c.patch(f"/api/open-seats/{seat}", json={"risks_real": {"situation": True}, "lessons": "[Turnaround pace was the real gap]"})
    assert c.get("/api/today").json()["seats_due"] == []
    assert c.get("/api/transitions").json()["lessons"][0]["lessons"] == "[Turnaround pace was the real gap]"
    assert c.post(f"/api/open-seats/{seat}/hire", json={"name": "[Someone]"}).status_code == 409


def test_development_grid_and_kit(c):
    pid = person(c, "[Me]")
    c.post("/api/career-entries", json={"person_id": pid, "title": "[First lead role]", "function": "Engineering", "situation": "turnaround"})
    c.post("/api/career-entries", json={"person_id": pid, "title": "[Task force]", "function": "Operations", "situation": "start-up", "kind": "project"})
    g = c.get(f"/api/people/{pid}/development-grid").json()
    assert g["grid"]["Engineering"]["turnaround"][0]["n"] == 1 and g["grid"]["Operations"]["start-up"][0]["kind"] == "project"
    assert set(g["blank_situations"]) == {"accelerated growth", "realignment", "sustaining success"}
    kit = c.get("/api/transition-kit").json()
    assert "Five conversations" in kit["playbook"] and "[Name]" in kit["template"]
    c.post("/api/transition-kit/export", json={"which": "template"})
    assert c.get("/api/exports").json()[0]["kind"] == "transition-kit:template"
    token = c.post("/api/tokens", json={"name": "[Hub]", "scopes": ["full"]}).json()["token"]
    c.cookies.clear()
    assert c.get(f"/api/people/{pid}/development-grid", headers={"Authorization": f"Bearer {token}"}).status_code == 403
