"""The portfolio: strategic themes, epics with a lean business case, the Kanban's rules, WIP limits and the MVP decision."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
CASE = {"hypothesis": "[Hypothesis]", "outcomes": "[Outcomes]", "leading_indicators": "[Indicators]", "mvp": "[MVP]"}


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def test_epic_needs_a_business_case_to_be_ready_and_ranks_by_wsjf(c):
    theme = c.post("/api/strategic-themes", json={"name": "[Theme]", "objective": "[Objective]"}).json()["id"]
    a = c.post("/api/epics", json={"title": "[Epic A]", "theme_id": theme, "business_value": 8, "time_criticality": 5, "risk_reduction": 3, "job_size": 8}).json()["id"]
    b = c.post("/api/epics", json={"title": "[Epic B]", "theme_id": theme, "epic_type": "enabler", "business_value": 5, "time_criticality": 8, "risk_reduction": 8, "job_size": 3}).json()["id"]
    r = c.post(f"/api/epics/{a}/move", json={"to": "ready"})
    assert r.status_code == 400 and "the hypothesis" in r.json()["detail"] and "the MVP" in r.json()["detail"]
    for e in (a, b):
        c.patch(f"/api/epics/{e}", json=CASE)
        assert c.post(f"/api/epics/{e}/move", json={"to": "ready"}).json()["kanban_state"] == "ready"
    o = c.get("/api/portfolio").json()
    ready = next(col for col in o["columns"] if col["state"] == "ready")
    assert [e["title"] for e in ready["epics"]] == ["[Epic B]", "[Epic A]"] and ready["epics"][0]["wsjf"] == 7.0
    assert o["themes"][0]["epics"] == 2 and o["themes"][0]["active_epics"] == 2 and o["unthemed"] == 0


def test_wip_limits_and_the_mvp_decision(c):
    c.put("/api/portfolio/wip", json={"implementing MVP": 1})
    ids = []
    for n in (1, 2):
        e = c.post("/api/epics", json={"title": f"[Epic {n}]", **CASE}).json()["id"]
        ids.append(e)
    assert c.post(f"/api/epics/{ids[0]}/move", json={"to": "implementing MVP"}).status_code == 200
    assert c.post(f"/api/epics/{ids[1]}/move", json={"to": "implementing MVP"}).status_code == 409
    assert c.post(f"/api/epics/{ids[1]}/move", json={"to": "implementing MVP", "over_limit": True}).status_code == 200
    assert c.get("/api/portfolio").json()["columns"][4]["over"] is True
    assert c.post(f"/api/epics/{ids[0]}/move", json={"to": "implementing persevere"}).status_code == 400
    d = c.post(f"/api/epics/{ids[0]}/decide", json={"decision": "persevere", "notes": "[Indicators moved]"}).json()
    assert d["kanban_state"] == "implementing persevere" and d["decision_notes"] == "[Indicators moved]"
    assert c.post(f"/api/epics/{ids[1]}/decide", json={"decision": "pivot"}).json()["kanban_state"] == "analyzing"
    assert c.post(f"/api/epics/{ids[1]}/decide", json={"decision": "stop"}).status_code == 400  # only while the MVP is running
    assert c.put("/api/portfolio/wip", json={"funnel": 2}).status_code == 400


def test_epic_detail_rolls_up_its_features(c):
    e = c.post("/api/epics", json={"title": "[Epic]"}).json()["id"]
    pi = c.post("/api/program-increments", json={"number": 1}).json()["id"]
    f1 = c.post("/api/features", json={"title": "[Feature 1]", "epic_id": e, "pi_id": pi, "status": "done"}).json()["id"]
    c.post("/api/features", json={"title": "[Feature 2]", "epic_id": e})
    c.post("/api/stories", json={"title": "[Story]", "feature_id": f1, "points": 5})
    d = c.get(f"/api/epics/{e}/detail").json()
    assert [f["title"] for f in d["features"]] == ["[Feature 1]", "[Feature 2]"] and d["features"][0]["pi_number"] == 1
    assert d["points"] == 5 and d["done_points"] == 5 and d["epic"]["case_missing"]
