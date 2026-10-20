"""Agile Release Trains: roles and teams, the ART backlog ranked by WSJF, PI cadence and predictability."""

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


def test_train_overview_ranks_the_backlog_by_wsjf_and_plans_into_a_pi(c):
    rte = c.post("/api/people", json={"name": "[RTE]", "active": True}).json()["id"]
    bo = c.post("/api/people", json={"name": "[Owner]", "active": True}).json()["id"]
    art = c.post("/api/arts", json={"name": "[Train]", "mission": "[Mission]", "rte_id": rte, "business_owner_ids": [bo]}).json()["id"]
    team = c.post("/api/teams", json={"name": "[Team A]", "art_id": art}).json()["id"]
    c.post("/api/teams", json={"name": "[Team B]"})
    pi = c.post("/api/program-increments", json={"number": 1, "art_id": art}).json()["id"]
    low = c.post("/api/features", json={"title": "[Low]", "art_id": art, "business_value": 3, "time_criticality": 2, "risk_reduction": 1, "job_size": 8}).json()["id"]
    high = c.post("/api/features", json={"title": "[High]", "art_id": art, "feature_type": "enabler", "business_value": 8, "time_criticality": 5, "risk_reduction": 3, "job_size": 2}).json()["id"]
    c.post("/api/features", json={"title": "[Unscored]", "art_id": art})
    o = c.get(f"/api/arts/{art}/overview").json()
    assert o["art"]["rte_name"] == "[RTE]" and o["business_owners"] == [{"id": bo, "name": "[Owner]"}]
    assert [t["id"] for t in o["teams"]] == [team] and "[Team B]" in [t["name"] for t in o["other_teams"]]
    assert [f["title"] for f in o["backlog"]] == ["[High]", "[Low]", "[Unscored]"] and o["backlog"][0]["wsjf"] == 8.0
    c.post(f"/api/features/{high}/plan", json={"pi_id": pi})
    assert [f["title"] for f in c.get(f"/api/arts/{art}/overview").json()["backlog"]] == ["[Low]", "[Unscored]"]
    assert c.post(f"/api/features/{low}/plan", json={"pi_id": 999}).status_code == 404


def test_predictability_counts_stretch_value_against_committed_plan(c):
    pi = c.post("/api/program-increments", json={"number": 2}).json()["id"]
    c.post("/api/pi-objectives", json={"pi_id": pi, "title": "[A]", "kind": "committed", "value_planned": 10, "value_actual": 8})
    c.post("/api/pi-objectives", json={"pi_id": pi, "title": "[B]", "kind": "committed", "value_planned": 10, "value_actual": 6})
    c.post("/api/pi-objectives", json={"pi_id": pi, "title": "[C]", "kind": "stretch", "value_planned": 4, "value_actual": 3})
    p = c.get(f"/api/pis/{pi}/cadence").json()["predictability"]
    assert p == {"planned": 20, "actual": 17, "percent": 85, "band": "healthy"}
    assert c.get(f"/api/pis/{pi}/board").json()["predictability"] == 85


def test_cadence_flags_missing_system_demos_and_inspect_adapt_feeds_the_backlog(c):
    pi = c.post("/api/program-increments", json={"number": 3}).json()["id"]
    done = c.post("/api/sprints", json={"number": 1, "pi_id": pi, "start_date": "2026-09-01", "end_date": "2026-09-14"}).json()["id"]
    later = c.post("/api/sprints", json={"number": 2, "pi_id": pi, "start_date": "2099-01-01", "end_date": "2099-01-14"}).json()["id"]
    cad = c.get(f"/api/pis/{pi}/cadence").json()
    assert [(s["id"], s["due"]) for s in cad["sprints"]] == [(done, True), (later, False)] and cad["inspect_adapt"] is None
    c.post("/api/system-demos", json={"pi_id": pi, "sprint_id": done, "date": "2026-09-14", "shown": "[Integrated feature]"})
    assert c.get(f"/api/pis/{pi}/cadence").json()["sprints"][0]["due"] is False
    ia = c.post(f"/api/pis/{pi}/inspect-adapt").json()
    assert c.post(f"/api/pis/{pi}/inspect-adapt").json()["id"] == ia["id"]
    c.patch(f"/api/inspect-adapts/{ia['id']}", json={"problem": "[Problem]", "improvements": ["[Automate the regression suite]"]})
    item = c.post(f"/api/inspect-adapts/{ia['id']}/to-backlog", json={"text": "[Automate the regression suite]"}).json()
    assert item["status"] == "ready" and item["labels"] == ["inspect and adapt", "PI 3"]
    assert c.post(f"/api/inspect-adapts/{ia['id']}/to-backlog", json={"text": "[Automate the regression suite]"}).status_code == 409
