from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def day(n):
    return (date.today() + timedelta(days=n)).isoformat()


def person(client, name, **kw):
    return client.post("/api/people", json={"name": name, **kw}).json()["id"]


def test_reporting_lines_and_org_chart(client):
    boss = person(client, "[Boss]", role="[Director]")
    mid = person(client, "[Manager]")
    dev = person(client, "[Developer]")
    client.patch(f"/api/people/{mid}", json={"manager_id": boss})
    client.patch(f"/api/people/{dev}", json={"manager_id": mid})
    assert client.patch(f"/api/people/{boss}", json={"manager_id": dev}).status_code == 400
    assert client.patch(f"/api/people/{boss}", json={"manager_id": boss}).status_code == 400
    assert client.patch(f"/api/people/{boss}", json={"manager_id": 999}).status_code == 400
    chart = client.get("/api/people/org-chart").json()
    root = chart["roots"][0]
    assert root["name"] == "[Boss]" and root["children"][0]["name"] == "[Manager]" and root["children"][0]["children"][0]["name"] == "[Developer]"
    assert client.get(f"/api/people/{dev}").json()["manager_name"] == "[Manager]"
    assert [r["name"] for r in client.get(f"/api/people/{mid}/crm").json()["reports"]] == ["[Developer]"]


def test_conversations_cadence_and_today(client):
    a = person(client, "[A]", cadence_days=14)
    b = person(client, "[B]", cadence_days=14)
    person(client, "[C]")
    client.post("/api/interactions", json={"date": day(-3), "kind": "one-on-one", "person_ids": [a], "takeaways": "[Remember this]"})
    client.patch(f"/api/people/{b}", json={"next_meeting": day(2), "key_dates": {"dates": [{"label": "[Work anniversary]", "date": day(3)}, {"label": ""}]}})
    o = {p["name"]: p for p in client.get("/api/people/overview").json()["people"]}
    assert (o["[A]"]["days_since"], o["[A]"]["due"]) == (3, False)
    assert (o["[B]"]["last_contact"], o["[B]"]["due"]) == (None, True) and o["[C]"]["due"] is False
    assert client.get(f"/api/people/{b}").json()["key_dates"] == {"dates": [{"label": "[Work anniversary]", "date": day(3)}]}
    t = client.get("/api/today").json()["people_due"]
    assert [c["name"] for c in t["check_ins"]] == ["[B]"]
    assert t["meetings"] == [{"id": b, "name": "[B]", "date": day(2)}]
    assert t["key_dates"][0]["label"] == "[Work anniversary]" and t["key_dates"][0]["days"] == 3


def test_prep_follow_ups_and_timeline(client):
    a = person(client, "[A]")
    team = client.get("/api/teams").json()[0]
    client.patch(f"/api/teams/{team['id']}", json={"scrum_master_id": a})
    i = client.post("/api/interactions", json={"date": day(-1), "kind": "one-on-one", "title": "[Weekly]", "person_ids": [a],
                                              "notes": "[Notes]", "follow_ups": "- [Send the doc]\n[Book a demo]\n"}).json()
    r = client.post(f"/api/interactions/{i['id']}/follow-up").json()
    assert [x["concern"] for x in r["created"]] == ["[Send the doc]", "[Book a demo]"] and r["created"][0]["origin"] == "one-on-one"
    assert client.post(f"/api/interactions/{i['id']}/follow-up").json()["created"] == []
    crm = client.get(f"/api/people/{a}/crm").json()
    assert crm["interactions"][0]["title"] == "[Weekly]" and len(crm["follow_ups"]) == 2
    assert crm["teams"] == [{"id": team["id"], "name": team["name"], "as": ["Scrum Master"]}]
    kinds = {e["kind"] for e in client.get(f"/api/people/{a}/timeline").json()["events"]}
    assert {"one-on-one", "dev-sync"} <= kinds


def test_field_choices(client):
    l = client.put("/api/people/layout", json={"hidden": ["personal_context", "skills", "not-a-field"]}).json()
    assert l["hidden"] == ["personal_context", "skills"] and "personal_context" in l["sensitive"]


def test_private_while_presenting(client):
    a = person(client, "[A]", role="[Title]", personal_context="[Sensitive]", location="[City]")
    client.post("/api/interactions", json={"date": day(0), "person_ids": [a], "notes": "[Private notes]"})
    client.post("/api/session/presentation", json={"on": True})
    o = client.get("/api/people/overview").json()
    assert o["private"] is False and "personal_context" not in o["people"][0] and "location" not in o["people"][0]
    crm = client.get(f"/api/people/{a}/crm").json()
    assert "interactions" not in crm and crm["person"]["role"] == "[Title]"
    assert client.get("/api/interactions").json() == []
    assert client.get(f"/api/people/{a}/timeline").json() == {"events": []}


def test_roster_import_and_placeholders(client):
    roster = {"me": "me", "people": [
        {"key": "me", "name": "[Me]", "reports_to": "boss"},
        {"key": "boss", "name": "[My manager]", "relationship": "manager"},
        {"key": "a", "name": "[Senior engineer]", "role": "Senior engineer", "relationship": "employee", "reports_to": "me", "on_team": True, "tags": ["senior"]},
        {"key": "b", "name": "[Contractor]", "relationship": "contractor", "reports_to": "me", "on_team": True},
        {"key": "c", "name": "Real Peer", "relationship": "peer"},
    ]}
    r = client.post("/api/people/roster", json={**roster, "acknowledged": True}).json()
    assert len(r["created"]) == 5 and r["team_members"] == 2 and r["me"]
    again = client.post("/api/people/roster", json=roster).json()
    assert again["created"] == [] and len(again["reused"]) == 5
    people = {p["name"]: p for p in client.get("/api/people").json()}
    assert people["[Senior engineer]"]["placeholder"] and not people["Real Peer"]["placeholder"]
    assert people["[Senior engineer]"]["manager_id"] == people["[Me]"]["id"] and people["[Me]"]["manager_id"] == people["[My manager]"]["id"]
    reports = client.get("/api/people/reports").json()
    assert {x["name"] for x in reports["reports"]} == {"[Senior engineer]", "[Contractor]"}
    team = next(t for t in client.get("/api/teams").json() if t["kind"] == "mine")
    assert set(team["member_ids"]) == {people["[Senior engineer]"]["id"], people["[Contractor]"]["id"]}
    # giving a stand-in a real name clears the mark, and keeps everything recorded against them
    pid = people["[Senior engineer]"]["id"]
    client.post("/api/interactions", json={"date": "2026-10-01", "person_ids": [pid], "title": "[Chat]"})
    assert client.patch(f"/api/people/{pid}", json={"name": "Real Engineer"}).json()["placeholder"] is False
    assert client.get(f"/api/people/{pid}/crm").json()["person"]["name"] == "Real Engineer"
    assert client.post("/api/people/roster", json={"people": [{"key": "x", "name": "[X]", "reports_to": "nobody"}]}).status_code == 400
    assert client.post("/api/people/roster", json={"people": []}).status_code == 400
    assert client.post("/api/people/roster", json={"me": "zzz", "people": [{"key": "y", "name": "[Y]"}]}).status_code == 400


def test_relationship_balance_and_peer_nudge(client):
    from datetime import date, timedelta
    d = lambda n: (date.today() + timedelta(days=n)).isoformat()
    boss = client.post("/api/people", json={"name": "[Boss]", "relationship": "manager"}).json()["id"]
    bigboss = client.post("/api/people", json={"name": "[Boss's boss]"}).json()["id"]
    client.patch(f"/api/people/{boss}", json={"manager_id": bigboss})
    me = client.post("/api/people", json={"name": "[Me]", "manager_id": boss}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    rep = client.post("/api/people", json={"name": "[Report]"}).json()["id"]
    client.patch(f"/api/people/{rep}", json={"manager_id": me})
    peer = client.post("/api/people", json={"name": "[Peer]", "relationship": "peer", "influence": "high"}).json()["id"]
    talk = client.post("/api/people", json={"name": "[Talked peer]", "relationship": "peer"}).json()["id"]
    vendor = client.post("/api/people", json={"name": "[Vendor]", "relationship": "vendor"}).json()["id"]
    for who, when in [([boss], -2), ([bigboss], -5), ([boss, rep], -8), ([talk], -40), ([vendor], -3)]:
        client.post("/api/interactions", json={"date": d(when), "person_ids": who, "kind": "meeting"})
    b = client.get("/api/people/balance").json()
    assert b["counts"] == {"up": 3, "down": 1, "sideways": 0, "outward": 1} and b["previous"]["sideways"] == 1 and b["top_heavy"]
    assert [p["name"] for p in b["peers"]] == ["[Peer]", "[Talked peer]"] and all(p["quiet"] for p in b["peers"])
    nudge = client.get("/api/today").json()["people_due"]["sideways"]
    assert nudge["top_heavy"] and nudge["quiet"][0]["id"] == peer
    client.patch(f"/api/people/{peer}", json={"offer_them": "[Help]", "need_from_them": "[QA time]"})
    client.post("/api/interactions", json={"date": d(0), "person_ids": [peer, talk]})
    client.post("/api/interactions", json={"date": d(-1), "person_ids": [peer]})
    client.post("/api/interactions", json={"date": d(-1), "person_ids": [talk]})
    b = client.get("/api/people/balance").json()
    assert b["counts"]["sideways"] == 3 and not b["top_heavy"] and b["peers"][0]["offer_them"] in ("[Help]", None)
    assert client.get("/api/today").json()["people_due"]["sideways"] is None
    assert client.get("/api/people/balance?days=3").status_code == 400
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/people/balance").json() == {"hidden": True}
    assert "offer_them" not in client.get(f"/api/people/{peer}").json()
