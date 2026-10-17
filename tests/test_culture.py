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


def test_standards_rotate_and_self_check(client):
    assert client.get("/api/culture/overview").json()["today"] is None
    assert client.post("/api/culture/standards/starter").status_code == 201
    assert client.post("/api/culture/standards/starter").status_code == 409
    d = client.get("/api/culture/overview").json()
    active = d["standards"]
    assert len(active) == 8 and d["today"]["id"] == active[date.today().toordinal() % 8]["id"]
    assert client.post("/api/culture/self-check", json={"ratings": [{"standard_id": active[0]["id"], "rating": 9}]}).status_code == 400
    r = client.post("/api/culture/self-check", json={"ratings": [{"standard_id": active[0]["id"], "rating": 4, "note": "[Moment]"}, {"standard_id": active[1]["id"], "rating": 2}]})
    assert r.json()["saved"] == 2
    d = client.get("/api/culture/overview").json()
    assert d["standards"][0]["last"]["rating"] == 4 and d["self_check_trend"][-1]["average"] == 3.0 and d["last_self_check"] == day(0)
    client.patch(f"/api/standards/{active[0]['id']}", json={"active": False})
    for n in range(7):  # whichever day it is, a standard no longer in use never comes up
        client.patch(f"/api/standards/{active[n]['id']}", json={"active": False})
    assert client.get("/api/culture/overview").json()["today"]["id"] == active[7]["id"]


def test_unaddressed_concerns_reach_today(client):
    obs = lambda **kw: client.post("/api/culture-observations", json={"title": "[Observation]", **kw}).json()["id"]
    old = obs(date=day(-10))
    obs(date=day(-10), scope="organization")
    obs(date=day(-10), kind="positive")
    obs(date=day(-2))
    obs(date=day(-10), action="spoke privately")
    follow = obs(date=day(0), action="watching", follow_up=day(3))
    t = client.get("/api/today").json()["culture"]
    assert [o["id"] for o in t["unaddressed"]] == [old] and [o["id"] for o in t["follow_ups"]] == [follow]
    assert t["pulse_due"] is False and t["standard"] is None
    client.patch(f"/api/culture-observations/{old}", json={"status": "addressed"})
    assert client.get("/api/today").json()["culture"]["unaddressed"] == []
    d = client.get("/api/culture/overview").json()
    assert d["open"] == {"my team": 3, "organization": 1, "positive": 1}


def test_pulse_cadence(client):
    assert client.get("/api/culture/overview").json()["pulse_due"] is True
    client.post("/api/trust-pulses", json={"date": day(-20), "source": "my read", "scores": {"safety": 3, "clarity": 2}})
    assert client.get("/api/today").json()["culture"]["pulse_due"] is True
    assert client.put("/api/culture/settings", json={"pulse_days": 0}).status_code == 400
    client.put("/api/culture/settings", json={"pulse_days": 30})
    d = client.get("/api/culture/overview").json()
    assert d["pulse_due"] is False and d["pulses"][0]["scores"]["clarity"] == 2 and len(d["dimensions"]) == 7


def test_agreements_and_brief_privacy(client):
    assert client.post("/api/culture/agreements/starter", json={}).status_code == 201
    assert client.post("/api/culture/agreements/starter", json={}).status_code == 409
    agr = client.get("/api/team-agreements").json()
    assert agr and all(a["status"] == "proposed" for a in agr)
    client.patch(f"/api/team-agreements/{agr[0]['id']}", json={"status": "agreed", "agreed_on": day(0), "review_on": day(-1)})
    client.put("/api/culture/role-brief", json={"focus": ["[Focus one]", " ", 3], "situation": "[Situation]"})
    client.post("/api/culture-observations", json={"title": "[Observation]"})
    d = client.get("/api/culture/overview").json()
    assert d["brief"]["focus"] == ["[Focus one]"] and len(d["agreements_due"]) == 1
    client.post("/api/session/presentation", json={"on": True})
    d = client.get("/api/culture/overview").json()
    assert d["private"] is False and "brief" not in d and d["agreements"]
    assert client.get("/api/culture/role-brief").json()["focus"] == []
    assert client.get("/api/culture-observations").json() == []
    assert client.get("/api/standards").json() == []
