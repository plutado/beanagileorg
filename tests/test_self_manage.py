"""Managing yourself (chapter 9) and helping your people manage themselves."""

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


def test_reflection_scores_dip_and_over_the_top(c):
    start_on_day(c, 120)
    for i, (energy, load) in enumerate([(4, 2), (3, 3), (2, 5)]):
        c.post("/api/reflections", json={"date": (date.today() - timedelta(days=14 - i * 7)).isoformat(), "entry": "[Entry]", "energy": energy, "load": load, "in_control": 3})
    r = c.get("/api/coaching/reflect").json()
    assert r["insight"]["in_dip"] and r["insight"]["over_the_top"]
    assert r["trend"][-1]["load"] == 5 and r["trend"][-1]["day"] == 120
    assert len(r["take_stock"]) == 7


def test_core_challenges_and_self_check(c):
    start_on_day(c, 31)
    o = c.get("/api/self").json()
    assert len(o["challenges"]) == 8 and len(o["syndromes"]) == 4
    assert c.get("/api/today").json()["self"]["challenge_check_due"] == 30
    r = c.post("/api/self/challenges", json={"scores": {"learn": 2, "team": 4, "alliances": 2, "bogus": 5}, "notes": {"learn": "[Note]"}}).json()
    assert sorted(r["weakest"]) == ["alliances", "learn"] and "bogus" not in r["scores"]
    assert c.get("/api/today").json()["self"]["challenge_check_due"] is None
    assert c.post("/api/self/challenges", json={"scores": {"learn": 9}}).status_code == 400
    assert c.get("/api/today").json()["self"]["self_check_due"]
    c.post("/api/self/syndromes", json={"ratings": {"isolation": 4}, "evidence": {"isolation": "[Evidence]"}, "asked": "[Trusted person]"})
    assert not c.get("/api/today").json()["self"]["self_check_due"]


def test_disciplines_review_and_working_base(c):
    start_on_day(c, 3)
    assert c.post("/api/self/disciplines/starter").json()["added"] == 6
    assert c.post("/api/self/disciplines/starter").json()["added"] == 0
    ids = [d["id"] for d in c.get("/api/self").json()["disciplines"]][:2]
    assert not c.get("/api/today").json()["self"]["review_done"]
    c.put("/api/self/review", json={"planned": "[Plan]", "done": "[Done]", "tomorrow": ["[One]", " "], "kept_ids": ids + [999]})
    rev = c.put("/api/self/review", json={"notes": "[Note]"}).json()
    assert rev["tomorrow"] == ["[One]"] and rev["kept_ids"] == ids and rev["notes"] == "[Note]"
    assert c.get("/api/today").json()["self"]["review_done"]
    assert c.get("/api/today").json()["self"]["working_base_left"] == 6
    c.put("/api/self/working-base", json={"access": True, "place": True})
    assert c.get("/api/today").json()["self"]["working_base_left"] == 4


def test_asks_im_considering(c):
    soon = (date.today() + timedelta(days=2)).isoformat()
    c.post("/api/tasks", json={"title": "[Join a new working group]", "requested_by": "[Peer]", "status": "considering", "answer_by": soon})
    asks = c.get("/api/today").json()["self"]["asks"]
    assert [a["title"] for a in asks] == ["[Join a new working group]"] and not asks[0]["late"]


def test_advice_grid(c):
    c.post("/api/people", json={"name": "[Inside adviser]", "active": True, "advice": ["technical", "cultural"]})
    c.post("/api/people", json={"name": "[Outside adviser]", "active": True, "advice": ["political"], "outside_org": True})
    a = c.get("/api/people/advice-network").json()
    assert [p["name"] for p in a["grid"]["outside"]["political"]] == ["[Outside adviser]"]
    q = {x["key"]: x["met"] for x in a["qualities"]}
    assert q["mix_kinds"] and q["mix_places"] and not q["loyal_outside"]
    c.put("/api/people/advice-network/qualities", json={"loyal_outside": True, "mix_kinds": False})
    q = {x["key"]: x["met"] for x in c.get("/api/people/advice-network").json()["qualities"]}
    assert q["loyal_outside"] and q["mix_kinds"]


def test_support_needs_consent_and_hr_gets_only_what_was_shared(c):
    pid = c.post("/api/people", json={"name": "[Engineer 1]", "active": True}).json()["id"]
    assert c.post(f"/api/people/{pid}/support/checkins", json={"energy": 3}).status_code == 409
    c.put(f"/api/people/{pid}/support", json={"consent_manager_on": date.today().isoformat(), "how_to_support": "[Fewer interruptions]"})
    first = c.post(f"/api/people/{pid}/support/checkins", json={"energy": 2, "load": 5, "hard": "[Kept private]", "share_hr": True}).json()
    assert first["share_hr"] is False  # no HR consent yet, so nothing can be marked for HR
    assert c.post(f"/api/people/{pid}/support/hr-summary").status_code == 409
    prof = c.put(f"/api/people/{pid}/support", json={"consent_hr": True}).json()
    assert prof["consent_hr_on"] == date.today().isoformat()
    c.post(f"/api/people/{pid}/support/checkins", json={"energy": 3, "support_wanted": "[A quieter week]", "syndromes": ["boundaries", "bogus"], "share_hr": True})
    s = c.get(f"/api/people/{pid}/support").json()
    assert len(s["checkins"]) == 2 and s["checkins"][0]["syndromes"] == ["boundaries"]
    out = c.post(f"/api/people/{pid}/support/hr-summary").json()
    assert "[A quieter week]" in out["markdown"] and "[Kept private]" not in out["markdown"] and "Undefended boundaries" in out["markdown"]
    assert any(e["kind"] == "support:hr" for e in c.get("/api/exports").json())
    token = c.post("/api/tokens", json={"name": "[Hub]", "scopes": ["full"]}).json()["token"]
    c.cookies.clear()
    h = {"Authorization": f"Bearer {token}"}
    assert c.get(f"/api/people/{pid}/support", headers=h).status_code == 403
    assert c.post(f"/api/people/{pid}/support/hr-summary", headers=h).status_code == 403
