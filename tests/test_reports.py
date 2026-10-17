from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit import weeks
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
TODAY = date.today()
MONDAY = TODAY - timedelta(days=TODAY.weekday())


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def iso(d):
    return d.isoformat()


def test_week_math():
    wed = date(2026, 10, 14)
    assert weeks.week_bounds(wed) == (date(2026, 10, 12), date(2026, 10, 18))
    assert weeks.week_bounds(wed, 6) == (date(2026, 10, 11), date(2026, 10, 17))  # weeks starting Sunday
    sprint = {"start_date": "2026-10-12", "end_date": "2026-10-23"}
    assert weeks.sprint_weeks(sprint) == [(date(2026, 10, 12), date(2026, 10, 18)), (date(2026, 10, 19), date(2026, 10, 23))]
    assert weeks.sprint_week(sprint, date(2026, 10, 13)) == (1, 2) and weeks.sprint_week(sprint, date(2026, 10, 21)) == (2, 2)
    assert weeks.sprint_week(sprint, date(2026, 10, 30)) is None


def test_week_info_and_settings(client):
    client.put("/api/toolkit/settings", json={"start_date": iso(MONDAY - timedelta(days=14))})
    client.post("/api/sprints", json={"number": 7, "start_date": iso(MONDAY - timedelta(days=7)), "end_date": iso(MONDAY + timedelta(days=4)), "goal": "[Sprint goal]"})
    w = client.get("/api/weeks").json()
    assert w["start"] == iso(MONDAY) and w["role_week"] == 3 and w["sprint"]["label"] == "Sprint 7, week 2 of 2" and len(w["recent"]) == 13
    assert w["recent"][1]["sprint"]["week"] == 1
    st = client.get(f"/api/weeks/stamp?on={iso(MONDAY - timedelta(days=5))}").json()
    assert st["sprint_number"] == 7 and st["sprint_week"] == 1 and st["role_week"] == 2
    assert client.put("/api/weeks/settings", json={"week_start_day": 9}).status_code == 400
    client.put("/api/weeks/settings", json={"week_start_day": 6, "report_day": 3})
    w = client.get("/api/weeks").json()
    assert date.fromisoformat(w["start"]).weekday() == 6 and w["report_day"] == 3


def test_weekly_report_respects_audience(client):
    client.post("/api/sprints", json={"number": 3, "start_date": iso(MONDAY), "end_date": iso(MONDAY + timedelta(days=11))})
    log = lambda **kw: client.post("/api/log-entries", json={"date": iso(TODAY), **kw}).status_code
    assert log(text="[Win for leadership]", kind="win", jira_keys=["abc-1"]) == 201
    log(text="[Progress for my manager]", audience="my manager")
    log(text="[Just for me]", audience="just me")
    log(text="[Blocker]", kind="blocker")
    log(text="[Ask]", kind="ask")
    log(text="[Note]", kind="note")
    lead = client.get("/api/reports/weekly?audience=leadership").json()
    md = lead["markdown"]
    assert "[Win for leadership] (ABC-1)" in md and "[Blocker]" in md and "[Ask]" in md
    assert "[Progress for my manager]" not in md and "[Just for me]" not in md and "[Note]" not in md
    assert "Sprint 3, week 1 of 2" in md and lead["sprint_id"]
    mgr = client.get("/api/reports/weekly?audience=my manager").json()["markdown"]
    assert "[Progress for my manager]" in mgr and "[Just for me]" not in mgr
    assert client.get("/api/reports/weekly?audience=everyone").status_code == 400
    # an earlier week has nothing of this week's
    prev = client.get(f"/api/reports/weekly?week={iso(MONDAY - timedelta(days=7))}").json()["markdown"]
    assert "[Win for leadership]" not in prev
    # presenting never shows a just-me entry, and an export-only token only gets the leadership draft
    client.post("/api/session/presentation", json={"on": True})
    assert all(e["text"] != "[Just for me]" for e in client.get("/api/log-entries").json())


def test_finished_work_and_sprint_report(client):
    sid = client.post("/api/sprints", json={"number": 4, "start_date": iso(MONDAY), "end_date": iso(MONDAY + timedelta(days=11)), "goal": "[Goal]"}).json()["id"]
    a = client.post("/api/backlog-items", json={"title": "[Story A]", "points": 5, "sprint_id": sid, "status": "in sprint"}).json()["id"]
    client.post("/api/backlog-items", json={"title": "[Story B]", "points": 3, "sprint_id": sid, "status": "in sprint"})
    client.patch(f"/api/backlog-items/{a}", json={"status": "done"})
    r = client.post("/api/roadmap", json={"title": "[Milestone]", "status": "in progress"}).json()["id"]
    client.patch(f"/api/roadmap/{r}", json={"status": "done"})
    client.post("/api/log-entries", json={"date": iso(TODAY), "text": "[Sprint win]", "kind": "win"})
    week = client.get("/api/reports/weekly").json()
    assert week["counts"]["stories"] == 1 and week["counts"]["points"] == 5 and "- [Milestone]" in week["markdown"]
    assert "5 of 8 points done so far" in week["markdown"] and "[Story A]" not in week["markdown"]
    rep = client.get(f"/api/reports/sprint?sprint_id={sid}").json()
    assert [w["week"] for w in rep["weeks"]] == [1, 2] and rep["progress"]["done_points"] == 5
    assert "## Week 1" in rep["markdown"] and "## Week 2" in rep["markdown"] and "[Sprint win]" in rep["markdown"]
    assert "1 story (3 points) not finished" in rep["markdown"]
    assert client.get("/api/reports/sprint").json()["sprint_id"] == sid
    assert client.get("/api/reports/sprint?sprint_id=999").status_code == 404


def test_activity_promote_and_today(client):
    rid = client.post("/api/risks", json={"title": "[Risk]", "level": "medium"}).json()["id"]
    client.patch(f"/api/risks/{rid}", json={"status": "closed"})
    act = client.get("/api/activity").json()
    events = act["days"][0]["events"]
    assert {e["event"] for e in events} == {"added", "finished"} and act["days"][0]["stamp"]["week_start"] == iso(MONDAY)
    body = {"entity": "risk", "id": rid, "date": iso(TODAY), "kind": "win", "text": "[Risk closed]"}
    assert client.post("/api/activity/promote", json=body).status_code == 201
    assert client.post("/api/activity/promote", json=body).status_code == 409
    assert client.post("/api/activity/promote", json={**body, "id": 999}).status_code == 400
    assert all(e["promoted"] for e in client.get("/api/activity").json()["days"][0]["events"] if e["entity"] == "risk")
    due = client.get("/api/today").json()["reports"]
    assert due["logged_today"] == 1 and due["weekly"] is not None
    rep = client.get(f"/api/reports/weekly?week={due['weekly']['start']}").json()
    saved = client.post("/api/reports", json={k: rep[k] for k in ("kind", "audience", "period_start", "period_end", "title", "markdown")})
    assert saved.status_code == 201
    assert client.get("/api/today").json()["reports"]["weekly"] is None
    assert client.post("/api/reports/exported", json={"title": rep["title"], "markdown": rep["markdown"]}).json() == {"logged": True}
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/activity").json() == {"hidden": True}
