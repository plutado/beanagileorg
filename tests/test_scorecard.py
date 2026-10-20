"""Day-90 summary, delivery scorecard, status overall line and sent history, monthly roll-up."""

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


def test_scorecard(c):
    sp1 = c.post("/api/sprints", json={"number": 1, "start_date": "2026-09-01", "end_date": "2026-09-14"}).json()["id"]
    sp2 = c.post("/api/sprints", json={"number": 2, "start_date": "2026-09-15", "end_date": "2026-09-28"}).json()["id"]
    c.post("/api/sprint-plans", json={"sprint_id": sp1, "status": "closed", "committed_points": 20, "completed_points": 19, "closed_on": "2026-09-14"})
    c.post("/api/sprint-plans", json={"sprint_id": sp2, "status": "closed", "committed_points": 20, "completed_points": 12, "closed_on": "2026-09-28"})
    recent = (date.today() - timedelta(days=10)).isoformat()
    c.post("/api/releases", json={"name": "[R1]", "status": "released", "released_on": recent, "outcome": "clean"})
    c.post("/api/releases", json={"name": "[R2]", "status": "released", "released_on": recent, "outcome": "hotfix"})
    m = c.post("/api/metrics", json={"name": "[Change failure rate]", "unit": "%", "baseline": 30, "target": 15, "higher_is_better": False}).json()["id"]
    c.post("/api/metric-readings", json={"metric_id": m, "date": recent, "value": 20})
    sc = c.get("/api/scorecard").json()
    assert [s["kept_pct"] for s in sc["sprints"]] == [95, 60] and sc["commitments_kept"] == "1 of 2"
    assert sc["releases"]["change_failure_pct"] == 50
    assert sc["metrics"][0]["status"] == "improving"
    c.post("/api/metric-readings", json={"metric_id": m, "date": date.today().isoformat(), "value": 14})
    assert c.get("/api/scorecard").json()["metrics"][0]["status"] == "met"


def test_day90_summary(c):
    pid = c.post("/api/people", json={"name": "[New 1]", "active": True}).json()["id"]
    c.post("/api/onboardings", json={"person_id": pid})
    c.post("/api/interviews", json={"person_id": pid, "status": "done"})
    out = c.get("/api/first90/day90-summary").json()
    assert out["markdown"].startswith("# Day-90 summary") and "## Delivery scorecard" in out["markdown"] and "[New 1]" in out["markdown"]
    assert "1 of 1 conversations held" in out["markdown"]
    c.post("/api/first90/day90-summary/export")
    assert c.get("/api/exports").json()[0]["kind"] == "day90:markdown"


def test_status_overall_line_and_history(c):
    d = c.get("/api/status/draft").json()
    assert d["suggested"] == d["overall"] and not d["edited"]
    d = c.put("/api/status/overall", json={"overall": "Yellow", "line": "[Waiting on a decision about the release window]"}).json()
    assert d["overall"] == "Yellow" and d["markdown"].startswith("**Overall: Yellow** [Waiting on a decision")
    assert c.put("/api/status/overall", json={"overall": "Purple"}).status_code == 400
    sent = c.post("/api/status/sent", json={"sent_to": "[My manager]"}).json()
    assert sent["kind"] == "status" and sent["status"] == "sent"
    c.post("/api/status/sent", json={})  # sending again the same week updates, doesn't duplicate
    assert len(c.get("/api/status/history").json()) == 1
    assert c.put("/api/status/overall", json={}).json()["edited"] is False


def test_monthly_rollup(c):
    month = date.today().strftime("%Y-%m")
    rid = c.post("/api/roadmap", json={"title": "[Milestone A]"}).json()["id"]
    c.patch(f"/api/roadmap/{rid}", json={"status": "done"})
    did = c.post("/api/decisions-needed", json={"decision": "[Decision A]"}).json()["id"]
    c.patch(f"/api/decisions-needed/{did}", json={"status": "decided", "outcome": "[Go]"})
    c.post("/api/status/sent", json={})
    r = c.get(f"/api/reports/monthly?month={month}").json()
    assert r["kind"] == "monthly" and "[Milestone A]" in r["markdown"] and "[Decision A]: [Go]" in r["markdown"] and "Week of" in r["markdown"]
    assert c.get("/api/reports/monthly?month=bad").status_code == 400


def test_weekly_report_uses_my_overall_line(c):
    wk = c.get("/api/weeks").json()["start"]
    c.put("/api/status/overall", json={"week_of": wk, "overall": "Red", "line": "[A release broke the site]"})
    r = c.get(f"/api/reports/weekly?week={wk}").json()
    assert r["overall"] == "Red" and r["my_line"] == "[A release broke the site]" and "**Overall: Red** [A release broke the site]" in r["markdown"]
    assert c.put("/api/status/overall", json={"week_of": "nope"}).status_code == 400
