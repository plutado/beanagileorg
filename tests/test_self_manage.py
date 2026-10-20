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


def test_timed_hr_link(c):
    pid = c.post("/api/people", json={"name": "[Engineer 2]", "active": True}).json()["id"]
    c.put(f"/api/people/{pid}/support", json={"consent_manager_on": date.today().isoformat()})
    c.post(f"/api/people/{pid}/support/checkins", json={"support_wanted": "[Shared line]"})
    assert c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": "[HR contact]"}).status_code == 409  # no HR consent
    c.put(f"/api/people/{pid}/support", json={"consent_hr": True})
    c.post(f"/api/people/{pid}/support/checkins", json={"support_wanted": "[Visible to HR]", "hard": "[Not for HR]", "share_hr": False})
    c.post(f"/api/people/{pid}/support/checkins", json={"support_wanted": "[Visible to HR]", "share_hr": True})
    assert c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": " ", "hours": 24}).status_code == 400
    assert c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": "[HR contact]", "hours": 5}).status_code == 400
    c.put("/api/share-base-url", json={"base_url": "http://127.0.0.1:8801"})
    link = c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": "[HR contact]", "hours": 24, "max_views": 2}).json()
    assert link["local_only"] and link["url"].startswith("http://127.0.0.1:8801/shared/bsh_")
    path = "/shared/" + link["url"].split("/shared/")[1]
    c.cookies.clear()  # the recipient isn't signed in
    form = c.get(path)
    assert form.status_code == 200 and "access code" in form.text and "[Visible to HR]" not in form.text
    assert form.headers["cache-control"] == "no-store" and "noindex" in form.headers["x-robots-tag"]
    assert "match" in c.post(path, data={"code": "AAAA-AAAA"}).text
    page = c.post(path, data={"code": link["code"].lower()})
    assert page.status_code == 200 and "[Visible to HR]" in page.text and "[Not for HR]" not in page.text and "1 more time" in page.text
    assert c.get("/api/people").status_code == 401  # the link opens nothing else
    c.post(path, data={"code": link["code"]})
    assert c.post(path, data={"code": link["code"]}).status_code == 410  # views used up
    c.post("/login", data={"password": PASSWORD})
    links = c.get(f"/api/people/{pid}/support/hr-links").json()["links"]
    assert links[0]["status"] == "used up" and links[0]["views"] == 2
    kinds = [e["kind"] for e in c.get("/api/exports").json()]
    assert kinds.count("share:view") == 2 and "share:create" in kinds
    # Withdrawing consent stops a live link at once; revoking does too; wrong codes lock it.
    two = c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": "[HR contact]", "hours": 1}).json()
    p2 = "/shared/" + two["url"].split("/shared/")[1]
    c.put(f"/api/people/{pid}/support", json={"consent_hr": False})
    assert "no longer shared" in c.post(p2, data={"code": two["code"]}).text
    c.put(f"/api/people/{pid}/support", json={"consent_hr": True})
    assert c.delete(f"/api/people/{pid}/support/hr-links/{two['id']}").status_code == 204
    assert c.post(p2, data={"code": two["code"]}).status_code == 410
    three = c.post(f"/api/people/{pid}/support/hr-links", json={"recipient": "[HR contact]", "hours": 1}).json()
    p3 = "/shared/" + three["url"].split("/shared/")[1]
    for _ in range(5):
        r = c.post(p3, data={"code": "WRONG"})
    assert r.status_code == 410 and "locked" in r.text
    assert c.post(p3, data={"code": three["code"]}).status_code == 410
    assert c.get("/shared/bsh_nonsense").status_code == 410
    c.put("/api/share-base-url", json={"base_url": "https://machine-name.example.net"})
    assert not c.get(f"/api/people/{pid}/support/hr-links").json()["local_only"]
    assert c.put("/api/share-base-url", json={"base_url": "https://[bad"}).status_code == 400
