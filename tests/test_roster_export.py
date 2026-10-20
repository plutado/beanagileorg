"""Exporting People as a roster file, in the format the import reads, so a team can move between installs."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


def make(tmp_path, name):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path / name)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_roster_round_trip(tmp_path):
    a = make(tmp_path, "a")
    roster = {"me": "me", "people": [
        {"key": "me", "name": "[Me]", "role": "[Manager]", "reports_to": "boss"},
        {"key": "boss", "name": "[Boss]", "relationship": "manager"},
        {"key": "e1", "name": "[Engineer 1]", "relationship": "employee", "reports_to": "me", "on_team": True, "tags": ["[tag]"], "background": "[Private]"},
        {"key": "x", "name": "[Somebody else]", "relationship": "stakeholder"},
    ]}
    assert a.post("/api/people/roster", json=roster).status_code == 409  # tags and background: a second look first
    assert [c["name"] for c in a.post("/api/people/roster/check-import", json=roster).json()["checks"]] == ["[Engineer 1]"]
    a.post("/api/people/roster", json={**roster, "acknowledged": True})
    team = a.post("/api/people/roster/export", json={}).json()
    names = {p["name"]: p for p in team["people"]}
    assert set(names) == {"[Me]", "[Boss]", "[Engineer 1]"} and team["me"] == names["[Me]"]["key"]
    assert names["[Engineer 1]"]["reports_to"] == "me" and names["[Engineer 1]"]["on_team"] and names["[Engineer 1]"]["placeholder"]
    assert "tags" not in names["[Engineer 1]"] and "background" not in names["[Engineer 1]"]
    assert names["[Me]"]["reports_to"] == names["[Boss]"]["key"]
    held = a.post("/api/people/roster/export", json={"scope": "everyone", "include_private": True})
    assert held.status_code == 409  # tags and background may carry judgments: a second look first
    checks = a.post("/api/people/roster/check", json={"scope": "everyone", "include_private": True}).json()["checks"]
    assert [c["name"] for c in checks] == ["[Engineer 1]"] and {f["field"] for f in checks[0]["findings"]} == {"tags", "background"}
    full = a.post("/api/people/roster/export", json={"scope": "everyone", "include_private": True, "acknowledged": True}).json()
    eng = next(p for p in full["people"] if p["name"] == "[Engineer 1]")
    assert len(full["people"]) == 4 and eng["tags"] == ["[tag]"] and eng["background"] == "[Private]"
    assert any(e["kind"] == "people:roster" for e in a.get("/api/exports").json())
    b = make(tmp_path, "b")
    r = b.post("/api/people/roster", json=team).json()
    assert sorted(r["created"]) == ["[Boss]", "[Engineer 1]", "[Me]"]
    people = {p["name"]: p for p in b.get("/api/people").json()}
    assert people["[Engineer 1]"]["manager_id"] == people["[Me]"]["id"]
    assert b.post("/api/people/roster", json=team).json()["created"] == []
