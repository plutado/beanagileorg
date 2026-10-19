from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
TODAY = date.today()


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def d(n):
    return (TODAY + timedelta(days=n)).isoformat()


def team(client, started_days_ago=20):
    client.put("/api/toolkit/settings", json={"start_date": d(-started_days_ago + 1)})
    me = client.post("/api/people", json={"name": "[Me]"}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    old = client.post("/api/people", json={"name": "[Inherited one]", "relationship": "employee"}).json()["id"]
    new = client.post("/api/people", json={"name": "[New hire]", "relationship": "employee"}).json()["id"]
    for p in (old, new):
        client.patch(f"/api/people/{p}", json={"manager_id": me})
    client.post("/api/onboardings", json={"person_id": new, "start_date": d(-3)})
    return me, old, new


def test_inherited_team_gets_milestones(client):
    assert client.post("/api/first90/team/start", json={}).status_code == 400  # no "me" yet
    me, old, new = team(client)
    r = client.post("/api/first90/team/start", json={}).json()
    assert r["started"] == [old]  # the new hire is onboarded instead
    assert client.post("/api/first90/team/start", json={}).json()["started"] == []
    t = client.get("/api/first90/team").json()
    assert t["day"] == 20 and [p["name"] for p in t["people"]] == ["[Inherited one]"]
    ms = t["people"][0]["milestones"]
    assert len(ms) == 8 and ms[0]["due"] == d(-13) and ms[0]["late"] and not ms[3]["late"]  # day 7 passed, day 30 not yet


def test_milestones_seen_in_data(client):
    me, old, new = team(client)
    client.post("/api/first90/team/start", json={})
    client.post("/api/interactions", json={"date": d(-15), "kind": "one-on-one", "person_ids": [old]})
    client.post("/api/manager-notes", json={"person_id": old, "date": d(-1), "kind": "praise", "note": "[Note]", "shared": True})
    ms = {m["auto"]: m for m in client.get("/api/first90/team").json()["people"][0]["milestones"] if m["auto"]}
    assert ms["one_on_one"]["done"] == d(-15) and ms["one_on_one"]["seen_in_data"] and not ms["one_on_one"]["late"]
    assert ms["feedback"]["done"] == d(-1) and ms["growth_goal"]["done"] is None
    manual = [m for m in client.get("/api/first90/team").json()["people"][0]["milestones"] if not m["auto"]][0]
    client.patch(f"/api/first90-milestones/{manual['id']}", json={"done_on": d(0)})
    assert client.get("/api/first90/team").json()["people"][0]["done"] == 3
    # you can always untick one, even when the data says it happened
    client.patch(f"/api/first90-milestones/{ms['one_on_one']['id']}", json={"done_on": None, "not_done": True})
    again = {m["auto"]: m for m in client.get("/api/first90/team").json()["people"][0]["milestones"] if m["auto"]}
    assert again["one_on_one"]["done"] is None and not again["one_on_one"]["seen_in_data"]


def test_overview_three_tracks_and_today(client):
    me, old, new = team(client, started_days_ago=31)
    client.post("/api/first90/team/start", json={})
    client.post("/api/plans", json={"horizon_days": 30, "title": "[First 30 days]"})
    ov = client.get("/api/first90/overview").json()
    assert ov["day"] == 31 and ov["new_hires"][0]["name"] == "[New hire]" and ov["new_hires"][0]["day"] == 4
    assert ov["team"]["people"][0]["late"] >= 1 and ov["me"]["plans"][0]["due"] == d(-1)
    cp = {c["day"]: c for c in ov["checkpoints"]}
    assert cp[30]["due"] == d(-1) and cp[30]["pulse_on"] is None
    due = client.get("/api/today").json()["first90"]
    assert due["late"] and due["checkpoint"]["day"] == 30
    client.post("/api/trust-pulses", json={"date": d(0), "source": "my read", "scores": {"safety": 3}})
    client.put("/api/first90/checkpoints/30", json={"done_on": d(0), "heard": "[Heard]", "changed": "[Changed]"})
    assert client.put("/api/first90/checkpoints/45", json={}).status_code == 404
    cp = {c["day"]: c for c in client.get("/api/first90/overview").json()["checkpoints"]}
    assert cp[30]["pulse_on"] == d(0) and cp[30]["heard"] == "[Heard]"
    assert client.get("/api/today").json()["first90"]["checkpoint"] is None


def test_changes_lifecycle_and_privacy(client):
    c = client.post("/api/team-changes", json={"title": "[Daily stand-up]", "why": "[Why]", "notes": "[Private]"}).json()["id"]
    assert client.post(f"/api/team-changes/{c}/advance", json={"status": "adopted"}).status_code == 400  # must be tried first
    assert client.post(f"/api/team-changes/{c}/advance", json={"status": "announced"}).json()["announced_on"] == d(0)
    tr = client.post(f"/api/team-changes/{c}/advance", json={"status": "trial"}).json()
    assert tr["trial_start"] == d(0) and tr["review_on"] == d(28)
    client.patch(f"/api/team-changes/{c}", json={"review_on": d(2)})
    assert client.get("/api/today").json()["first90"]["reviews"][0]["id"] == c
    done = client.post(f"/api/team-changes/{c}/advance", json={"status": "adopted", "outcome": "[Kept it]"}).json()
    assert done["decided_on"] == d(0) and done["status"] == "adopted"
    mgr = client.get("/api/reports/weekly?audience=my manager").json()["markdown"]
    assert "[Daily stand-up]: adopted. [Kept it]" in mgr
    assert "[Daily stand-up]" not in client.get("/api/reports/weekly?audience=leadership").json()["markdown"]
    client.put("/api/first90/working-with-me", json={"text": "[How I work]"})
    client.post("/api/session/presentation", json={"on": True})
    shown = client.get(f"/api/team-changes/{c}").json()
    assert shown["why"] == "[Why]" and "notes" not in shown
    assert client.get("/api/first90/working-with-me").json()["text"] == "[How I work]"
    assert client.get("/api/first90/team").json() == {"hidden": True}
    assert "me" not in client.get("/api/first90/overview").json()


def test_template(client):
    assert client.put("/api/first90/template", json={"items": []}).status_code == 400
    assert client.put("/api/first90/template", json={"items": [{"title": "[A]", "due_day": 500}]}).status_code == 400
    client.put("/api/first90/template", json={"items": [{"title": "[Later]", "due_day": 40}, {"title": "[Sooner]", "due_day": 5}]})
    me, old, new = team(client)
    client.post("/api/first90/team/start", json={})
    assert [m["title"] for m in client.get("/api/first90/team").json()["people"][0]["milestones"]] == ["[Sooner]", "[Later]"]


def test_five_conversations_with_reports(client):
    me = client.post("/api/people", json={"name": "[Placeholder me]"}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    r = client.post("/api/people", json={"name": "[Placeholder report]", "manager_id": me}).json()["id"]
    g = client.get("/api/first90/report-conversations").json()
    assert g["topics"] == ["situation", "expectations", "resources", "style", "development"]
    assert client.put(f"/api/first90/report-conversations/{r}/situation", json={"status": "settled", "priority": True}).status_code == 200
    assert client.put(f"/api/first90/report-conversations/{r}/nope", json={}).status_code == 404
    row = next(x for x in client.get("/api/first90/report-conversations").json()["reports"] if x["id"] == r)
    assert row["cells"]["situation"] == {"status": "settled", "priority": True} and row["cells"]["style"]["status"] == "not started"
