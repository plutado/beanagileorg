"""Joining an organization from outside: the culture map, the glossary, what people expect from you, meeting
the people around your systems before an incident, and the informal 360 at each checkpoint."""

from datetime import date

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


def test_culture_map_starts_with_three_units(client):
    assert client.post("/api/culture/map/starter").json()["units"] == 3
    assert client.post("/api/culture/map/starter").status_code == 409
    units = client.get("/api/culture-reads").json()
    assert [u["unit"] for u in units] == ["My team", "A team I'm integrating", "The wider organization"]
    r = client.patch(f"/api/culture-reads/{units[0]['id']}", json={"meetings": "[Placeholder: decisions happen beforehand]", "power": "[Placeholder]"})
    assert r.json()["meetings"].startswith("[Placeholder")


def test_glossary_terms(client):
    client.post("/api/glossary-terms", json={"term": "[Acronym B]", "meaning": "[Meaning]", "used_by": "[Team]"})
    client.post("/api/glossary-terms", json={"term": "[acronym A]"})
    assert [t["term"] for t in client.get("/api/glossary-terms").json()] == ["[acronym A]", "[Acronym B]"]


def test_expects_from_me(client):
    p = client.post("/api/people", json={"name": "[Placeholder name 1]", "expects_from_me": "[Placeholder: weekly numbers]"}).json()
    assert client.get(f"/api/people/{p['id']}").json()["expects_from_me"] == "[Placeholder: weekly numbers]"


def test_neighbors_before_the_fire(client):
    a = client.post("/api/people", json={"name": "[Placeholder name 1]"}).json()["id"]
    b = client.post("/api/people", json={"name": "[Placeholder name 2]"}).json()["id"]
    client.post("/api/systems", json={"name": "[System A]", "first_responder_id": a, "business_contact_ids": [a, b]})
    n = client.get("/api/today").json()["people_due"]["neighbors"]
    assert {x["id"] for x in n} == {a, b} and next(x for x in n if x["id"] == a)["systems"] == ["[System A]"]
    client.post("/api/interactions", json={"date": date.today().isoformat(), "person_ids": [b]})
    assert [x["id"] for x in client.get("/api/today").json()["people_due"]["neighbors"]] == [a]


def test_checkpoint_keeps_the_informal_360(client):
    client.put("/api/first90/checkpoints/30", json={"adapting": "[Placeholder: what my manager and peers said]"})
    cp = client.get("/api/first90/overview").json()["checkpoints"][0]
    assert cp["day"] == 30 and cp["adapting"].startswith("[Placeholder")


def test_problem_preferences_find_blind_spots(client):
    grid = client.get("/api/preferences").json()
    assert len(grid["areas"]) == 5 and len(grid["kinds"]) == 3 and grid["assessments"] == []
    scores = {f"{a['key']}.{k['key']}": (3 if k["key"] == "political" else 8) for a in grid["areas"] for k in grid["kinds"]}
    scores["finance.technical"] = scores["finance.cultural"] = 2
    r = client.post("/api/preferences", json={"scores": scores}).json()
    assert r["columns"]["political"] == 15 and r["blind_spots"]["kinds"] == ["political"] and r["blind_spots"]["areas"] == ["finance"]
    assert {g["slug"] for g in r["guides"]} >= {"peer-relationships", "tech-debt-case"}
    assert client.post("/api/preferences", json={"scores": {"people.technical": 11}}).status_code == 400
    partial = client.post("/api/preferences", json={"scores": {"people.technical": 2}}).json()
    assert partial["complete"] is False and partial["blind_spots"] == {"kinds": [], "areas": []}
    assert len(client.get("/api/preferences").json()["assessments"]) == 2


def test_hammer_and_compensation_plan(client):
    grid = client.get("/api/preferences").json()
    scores = {f"{a['key']}.{k['key']}": 8 for a in grid["areas"] for k in grid["kinds"]}
    scores.update({"finance.technical": 2, "finance.political": 2, "finance.cultural": 2})
    r = client.post("/api/preferences", json={"scores": scores, "hammer": "[Placeholder: detail turns into control]"}).json()
    assert r["hammer"].startswith("[Placeholder") and r["blind_spots"]["areas"] == ["finance"]
    p = client.post("/api/people", json={"name": "[Placeholder name 1]"}).json()["id"]
    plan = {"finance": {"how": "backstop", "person_id": p, "note": "[Placeholder]"}}
    assert client.patch(f"/api/preference-assessments/{r['id']}", json={"plan": plan}).json()["plan"] == plan


def test_advice_network(client):
    assert client.get("/api/people/advice-network").json()["missing"] == ["political", "personal"]
    a = client.post("/api/people", json={"name": "[Placeholder name 1]", "advice": ["technical", "political"]}).json()["id"]
    n = client.get("/api/people/advice-network").json()
    assert [x["id"] for x in n["kinds"]["political"]] == [a] and n["missing"] == ["personal"]


def test_predictable_surprises_scan(client):
    scan = client.get("/api/risks/surprise-scan").json()
    assert [a["key"] for a in scan["areas"]] == ["external", "market", "internal", "politics"] and all(a["prompts"] for a in scan["areas"])
    r = client.post("/api/risks", json={"title": "[Placeholder surprise]", "surprise_area": "internal"}).json()
    assert r["surprise_area"] == "internal"
    assert next(a for a in client.get("/api/risks/surprise-scan").json()["areas"] if a["key"] == "internal")["open"] == 1
    assert client.post("/api/risks", json={"title": "[Placeholder]", "surprise_area": "weather"}).status_code == 400


def test_alignment_check(client):
    g = client.get("/api/alignment/guide").json()
    assert [e["key"] for e in g["elements"]] == ["direction", "structure", "processes", "skills"] and len(g["external"]) == 8 and len(g["traps"]) == 5
    assert all(e["prompts"] and e["scrum"] and e["look"] for e in g["elements"])
    c = client.post("/api/alignment-checks", json={"area": "[Placeholder area]"}).json()
    body = {"elements": {"structure": {"fit": "misaligned", "notes": "[Placeholder]"}}, "external": {"customers": "[Placeholder]"}, "root_cause": "structure", "the_case": "[Placeholder case]"}
    r = client.patch(f"/api/alignment-checks/{c['id']}", json=body).json()
    assert r["elements"]["structure"]["fit"] == "misaligned" and r["root_cause"] == "structure"
    assert client.patch(f"/api/alignment-checks/{c['id']}", json={"root_cause": "people"}).status_code == 400


def test_alignment_direction_mismatches_and_sequence(client):
    g = client.get("/api/alignment/guide").json()
    assert [p["key"] for p in g["direction"]["parts"]] == ["mission", "vision", "strategy"] and len(g["direction"]["four_cs"]) == 4
    assert [t["key"] for t in g["direction"]["tests"]][-1] == "implementation" and {m["key"] for m in g["direction"]["moves"]} == {"leave", "tweak", "reexamine"}
    assert len(g["mismatches"]) == 6 and sum(m["common"] for m in g["mismatches"]) == 4
    assert g["sequences"]["realignment"]["order"][0] == "processes" and g["sequences"]["turnaround"]["order"][0] == "direction"
    client.post("/api/situations", json={"area": "[Placeholder area]", "kind": "realignment"})
    assert client.get("/api/alignment/guide").json()["situations"]["[placeholder area]"] == "realignment"
    c = client.post("/api/alignment-checks", json={"area": "[Placeholder area]"}).json()
    body = {"sequence": "realignment", "direction": {"mission": "[Placeholder]", "tests": {"coherence": {"rating": "weak"}}}, "mismatches": {"structure-skills": {"state": "mismatch"}}}
    r = client.patch(f"/api/alignment-checks/{c['id']}", json=body).json()
    assert r["sequence"] == "realignment" and r["mismatches"]["structure-skills"]["state"] == "mismatch"


def test_tows_priorities(client):
    d = client.post("/api/departments", json={"name": "[Placeholder department]"}).json()["id"]
    a = lambda q, t, **kw: client.post("/api/assessments", json={"subject_type": "department", "subject_id": d, "quadrant": q, "title": t, **kw}).json()
    threat, opp = a("threat", "[Threat]"), a("opportunity", "[Opportunity]")
    a("weakness", "[Weakness]", bears_on_id=threat["id"])
    s = client.get(f"/api/landscape/department/{d}").json()
    first = s["priorities"][0]
    assert first["id"] == threat["id"] and first["move"] == "blunt" and first["urgent"] and first["weaknesses"][0]["title"] == "[Weakness]"
    assert s["priorities"][1]["move"] == "pursue" and not s["priorities"][1]["urgent"]
    r = client.post(f"/api/assessments/{threat['id']}/to-roadmap?priority=true").json()
    assert any(i["title"] == "Blunt: [Threat]" for i in client.get("/api/roadmap").json()) and r["status"] == "acted on"
    assert len(client.get("/api/landscape/swot").json()["priorities"]) == 2


def test_alignment_structure(client):
    S = client.get("/api/alignment/guide").json()["structure"]
    assert [p["key"] for p in S["parts"]] == ["units", "reporting", "decisions", "incentives"] and len(S["balances"]) == 4 and len(S["problems"]) == 4
    c = client.post("/api/alignment-checks", json={"area": "[Placeholder area]"}).json()
    st = {"parts": {"incentives": {"fit": "misaligned"}}, "balances": {"incentives": {"now": 0, "should": 3}}, "problems": {"silos": {"seen": True}}}
    assert client.patch(f"/api/alignment-checks/{c['id']}", json={"structure": st}).json()["structure"]["balances"]["incentives"]["should"] == 3


def test_team_plan_and_key_people(client):
    tp = client.get("/api/first90/team-plan").json()
    assert tp["conclusions_day"] == 60 and tp["act_day"] == 90 and len(tp["stages"]) == 4
    assert client.put("/api/first90/team-plan", json={"conclusions_day": 80, "act_day": 70}).status_code == 400
    r = client.put("/api/first90/team-plan", json={"alignment_stage": 2, "team_stage": 0}).json()
    assert r["out_of_step"] is True
    p = client.post("/api/people", json={"name": "[Placeholder name 1]", "key_person": True}).json()
    assert [x["id"] for x in client.get("/api/today").json()["first90"]["unrecognized"]] == [p["id"]]
    client.post("/api/manager-notes", json={"person_id": p["id"], "date": date.today().isoformat(), "note": "[Placeholder praise]", "kind": "praise"})
    assert client.get("/api/today").json()["first90"]["unrecognized"] == []
