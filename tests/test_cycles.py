"""90-day cycles: the current cycle, plan items by cycle, length setting, review, summary and Today prompts."""

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


def start_on_day(c, day):
    c.put("/api/toolkit/settings", json={"start_date": (date.today() - timedelta(days=day - 1)).isoformat()})


def test_cycles_follow_the_day_and_take_in_plan_items(c):
    start_on_day(c, 100)
    plan = c.get("/api/plans").json()[0]["id"]
    c.post("/api/plan-items", json={"plan_id": plan, "title": "[First cycle item]", "due_day": 45, "status": "done"})
    c.post("/api/plan-items", json={"plan_id": plan, "title": "[Second cycle win]", "due_day": 120, "early_win": True})
    o = c.get("/api/cycles/overview").json()
    assert o["current"] == 2 and o["day_in_cycle"] == 10 and [x["number"] for x in o["cycles"]] == [1, 2, 3]
    one, two = o["cycles"][0], o["cycles"][1]
    assert one["state"] == "past" and two["state"] == "current" and two["start_day"] == 91 and two["end_day"] == 180
    assert [i["title"] for i in one["items"]] == ["[First cycle item]"] and two["items"][0]["early_win"]
    assert c.get("/api/today").json()["cycle"]["focus_needed"]
    c.patch(f"/api/cycles/{two['id']}", json={"focus": "[Stable releases, every sprint]", "goals": ["[Two clean releases]"]})
    assert c.get("/api/today").json()["cycle"] is None
    assert c.put("/api/cycles/settings", json={"length_days": 30}).status_code == 400
    c.put("/api/cycles/settings", json={"length_days": 70})
    assert c.get("/api/cycles/overview").json()["current"] == 2


def test_review_snapshots_and_summary(c):
    start_on_day(c, 85)
    me = c.post("/api/people", json={"name": "[Me]", "active": True}).json()["id"]
    c.put("/api/people/me", json={"person_id": me})
    c.post("/api/mandates/mine", json={})
    c.get("/api/cycles/overview")
    assert c.get("/api/today").json()["cycle"]["review_due"]
    r = c.post("/api/cycles/1/review", json={"went_well": "[Release rhythm]", "to_change": "[Refinement]", "next_focus": "[QA built in]"}).json()
    assert r["status"] == "reviewed" and r["scorecard"] is not None
    assert any(v["label"] == "Cycle 1 review" for v in c.get(f"/api/mandates/{c.get('/api/mandates').json()[0]['id']}/versions").json())
    s = c.get("/api/cycles/1/summary").json()["markdown"]
    assert s.startswith("# Cycle 1 summary (days 1 to 90)") and "Went well: [Release rhythm]" in s and "- [QA built in]" in s
    c.post("/api/cycles/1/summary/export")
    assert c.get("/api/exports").json()[0]["kind"] == "cycle:markdown"
    assert c.get("/api/today").json()["cycle"] is None


def test_core_challenges_check_at_each_cycle_end(c):
    start_on_day(c, 181)
    assert c.get("/api/today").json()["self"]["challenge_check_due"] == 180


def test_cycles_follow_dated_pis_then_fall_back_to_the_set_length(c):
    start_on_day(c, 100)
    start = date.today() - timedelta(days=99)
    day = lambda n: (start + timedelta(days=n - 1)).isoformat()
    c.post("/api/program-increments", json={"number": 1, "start_date": day(1), "end_date": day(40)})  # too short to be cycle 1
    p2 = c.post("/api/program-increments", json={"number": 2, "start_date": day(41), "end_date": day(70)}).json()["id"]
    p3 = c.post("/api/program-increments", json={"number": 3, "start_date": day(71), "end_date": day(140)}).json()["id"]
    o = c.get("/api/cycles/overview").json()
    spans = [(x["number"], x["start_day"], x["end_day"], x["pi"]["id"] if x["pi"] else None) for x in o["cycles"]]
    assert spans[:2] == [(1, 1, 70, p2), (2, 71, 140, p3)] and o["current"] == 2 and o["day_in_cycle"] == 30
    assert o["cycles"][1]["follows_pi"] and o["follow_pis"]
    c.put("/api/cycles/settings", json={"follow_pis": False})
    o = c.get("/api/cycles/overview").json()
    assert (o["cycles"][0]["start_day"], o["cycles"][0]["end_day"]) == (1, 90) and o["current"] == 2 and not o["follow_pis"]
