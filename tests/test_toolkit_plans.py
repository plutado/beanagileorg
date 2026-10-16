import pytest
from fastapi.testclient import TestClient

from beanagile.comms import messaging
from beanagile.comms.app import build as build_comms
from beanagile.core.config import Settings
from beanagile.toolkit import models
from beanagile.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_four_horizons_with_dates(client):
    o = client.get("/api/plans/overview").json()
    assert [(h["horizon_days"], h["first_day"], h["last_day"], h["start"]) for h in o["horizons"]] == [
        (30, 1, 30, None), (60, 31, 60, None), (90, 61, 90, None), (120, 91, 120, None), (150, 121, 150, None), (180, 151, 180, None)]
    client.put("/api/toolkit/settings", json={"start_date": "2026-11-02"})
    h = client.get("/api/plans/overview").json()["horizons"]
    assert (h[0]["start"], h[0]["end"], h[3]["start"], h[5]["end"]) == ("2026-11-02", "2026-12-01", "2027-01-31", "2027-04-30")


def test_items_dates_window_and_theme_coverage(client):
    client.put("/api/toolkit/settings", json={"start_date": "2026-11-02"})
    person = client.post("/api/people", json={"name": "[Person]"}).json()["id"]
    client.post("/api/interviews", json={"person_id": person, "status": "done", "themes": ["[Theme A]", "[Theme B]"], "gaps": "[Gap note]"})
    client.post("/api/plan-items", json={"plan_id": 1, "title": "[In window]", "due_day": 10, "themes": ["[Theme A]"]})
    client.post("/api/plan-items", json={"plan_id": 1, "title": "[Too late]", "due_day": 45})
    o = client.get("/api/plans/overview").json()
    items = o["horizons"][0]["items"]
    assert [(i["due"], i["outside"]) for i in items] == [("2026-11-11", False), ("2026-12-16", True)]
    assert {t["theme"]: t["plan_items"] for t in o["evidence"]["themes"]} == {"[Theme A]": 1, "[Theme B]": 0}
    assert o["evidence"]["notes"]["gaps"][0]["text"] == "[Gap note]"


def test_outline_is_exportable_only(client):
    client.post("/api/plan-items", json={"plan_id": 1, "kind": "outcome", "title": "[Shown]", "evidence": "[Private evidence]"})
    client.post("/api/plan-items", json={"plan_id": 1, "kind": "keep", "title": "[Keep]"})
    client.post("/api/plan-items", json={"plan_id": 2, "title": "[Dropped]", "status": "dropped"})
    client.patch("/api/plans/1", json={"summary": "[Headline]", "notes": "[Private plan note]"})
    out = client.get("/api/plans/outline").json()
    md = out["markdown"]
    assert "[Shown]" in md and "[Headline]" in md and "### What I won't change" in md
    assert "[Private evidence]" not in md and "[Private plan note]" not in md and "[Dropped]" not in md
    assert out["horizons"][0]["groups"]["outcome"] == [{"title": "[Shown]", "detail": None, "due": None}]
    token = client.post("/api/tokens", json={"name": "comms", "scopes": ["export:read"]}).json()["token"]
    anon = TestClient(client.app, follow_redirects=False)
    anon.headers["Authorization"] = f"Bearer {token}"
    assert anon.get("/api/plans/outline").json()["markdown"] == md
    assert anon.post("/api/plans/export").status_code == 403
    client.post("/api/plans/export")
    assert client.get("/api/exports").json()[0]["kind"] == "plans:markdown"


def test_presentation_hides_evidence(client):
    client.post("/api/plan-items", json={"plan_id": 1, "title": "[Shown]", "evidence": "[Private]"})
    client.post("/api/session/presentation", json={"on": True})
    o = client.get("/api/plans/overview").json()
    assert "evidence" not in o["horizons"][0]["items"][0] and "notes" not in o["evidence"]


def test_mark_presented(client):
    p = client.post("/api/plans/1/presented", json={"presented_on": "2026-11-12", "audience": "[Audience]"}).json()
    assert (p["status"], p["presented_on"], p["audience"]) == ("presented", "2026-11-12", "[Audience]")
    assert client.post("/api/plans/999/presented", json={}).status_code == 404


def test_migration_creates_six_monthly_plans(client):
    assert [p["horizon_days"] for p in client.get("/api/plans").json()] == [30, 60, 90, 120, 150, 180]
    assert models.MIGRATIONS[-1][0] == 6


def test_comms_builds_a_deck_from_the_plan(tmp_path, monkeypatch):
    comms = TestClient(build_comms(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path / "comms")), follow_redirects=False)
    comms.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    assert comms.post("/api/decks/from-toolkit-plan").status_code == 400
    comms.put("/api/connections", json={"toolkit_url": "http://127.0.0.1:8801", "toolkit_token": "ba_[placeholder]"})
    outline = {
        "title": "[Plan title]", "start_date": None, "heard": {"conversations": 2, "themes": [{"theme": "[Theme]", "count": 2}]},
        "horizons": [
            {"title": "[First]", "summary": "[Headline]", "start": None, "end": None,
             "groups": {"outcome": [{"title": "[Outcome]", "detail": "[Detail]", "due": None}], "action": [], "measure": [{"title": "[Measure]"}], "keep": [{"title": "[Keep]"}]}},
            {"title": "[Second]", "summary": None, "start": None, "end": None, "groups": {"outcome": [], "action": [], "measure": [], "keep": []}},
        ],
    }
    monkeypatch.setattr(messaging, "fetch_toolkit", lambda url, token, path, timeout=5.0: outline)
    res = comms.post("/api/decks/from-toolkit-plan").json()
    deck = comms.get(f"/api/decks/{res['deck_id']}/full").json()
    slides = deck["slides"]
    assert [s["layout"] for s in slides] == ["title", "bullets", "bullets", "bullets", "bullets", "bullets", "closing"]
    assert slides[1]["content"]["items"] == ["[Theme] (2 of 2)"]
    assert slides[2]["content"]["heading"] == "[Headline]" and "[Detail]" in slides[2]["notes"]
    assert slides[3]["content"]["items"][0].startswith("[Placeholder")
    assert slides[4]["content"]["items"] == ["[Measure]"] and slides[5]["content"]["items"] == ["[Keep]"]


def test_add_and_remove_plans(client):
    p = client.post("/api/plans", json={"horizon_days": 75, "title": "[Mid-quarter check]"}).json()
    h = client.get("/api/plans/overview").json()["horizons"]
    assert [(x["horizon_days"], x["first_day"]) for x in h][2:4] == [(75, 61), (90, 76)]
    assert client.post("/api/plans", json={"horizon_days": 75, "title": "[Duplicate]"}).status_code in (400, 409)
    client.post("/api/plan-items", json={"plan_id": p["id"], "title": "[Item]"})
    assert client.delete(f"/api/plans/{p['id']}").status_code == 204
    assert client.get("/api/plan-items").json() == []
    assert client.post("/api/plans", json={"horizon_days": 0, "title": "[Bad]"}).status_code == 400
