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
    assert client.get("/api/people/advice-network").json()["missing"] == ["cultural", "political", "personal"]
    a = client.post("/api/people", json={"name": "[Placeholder name 1]", "advice": ["technical", "political"]}).json()["id"]
    n = client.get("/api/people/advice-network").json()
    assert [x["id"] for x in n["kinds"]["political"]] == [a] and n["missing"] == ["cultural", "personal"]


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


def test_criteria_and_team_assessment(client):
    w = {"competence": 30, "judgment": 20, "energy": 10, "focus": 10, "relationships": 10, "trust": 20}
    assert client.post("/api/team-assessment/criteria", json={"weights": {**w, "trust": 25}, "threshold": "trust"}).status_code == 400
    assert client.post("/api/team-assessment/criteria", json={"weights": w}).status_code == 400
    assert client.post("/api/team-assessment/criteria", json={"weights": w, "threshold": "trust"}).status_code == 201
    me = client.post("/api/people", json={"name": "[Placeholder me]"}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    p = client.post("/api/people", json={"name": "[Placeholder name 1]", "manager_id": me}).json()["id"]
    r = client.put(f"/api/team-assessment/{p}", json={"first_impression": "[Placeholder first read]"}).json()
    assert r["first_on"]
    again = client.put(f"/api/team-assessment/{p}", json={"first_impression": "[Rewritten]", "ratings": {"competence": {"score": 5}, "trust": {"score": 2}}, "considered_on": date.today().isoformat()}).json()
    assert again["first_impression"] == "[Placeholder first read]"
    o = client.get("/api/team-assessment").json()
    row = next(x for x in o["people"] if x["id"] == p)
    assert row["below_threshold"] and row["score"] == 3.8 and row["considered"] and o["missing"] == []
    assert client.put(f"/api/team-assessment/{p}", json={"ratings": {"competence": {"score": 9}}}).status_code == 400


def test_assessment_context_dispositions_and_templates(client):
    w = {"competence": 30, "judgment": 25, "energy": 10, "focus": 15, "relationships": 5, "trust": 15}
    client.post("/api/team-assessment/criteria", json={"weights": w, "threshold": "trust", "changeable": {"trust": "no", "energy": "bogus"}, "interdependence": "interdependent"})
    prof = client.get("/api/criteria-profiles").json()[0]
    assert prof["changeable"] == {"trust": "no"} and prof["interdependence"] == "interdependent"
    me = client.post("/api/people", json={"name": "[Placeholder me]"}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    p = client.post("/api/people", json={"name": "[Placeholder name 1]", "manager_id": me}).json()["id"]
    client.put(f"/api/team-assessment/{p}", json={"placement": "B", "criticality": 8, "disposition": "keep and develop"})
    o = client.get("/api/team-assessment").json()
    row = o["people"][0]
    assert o["relationships_low"] and row["critical_gap"] and row["disposition"] == "observe"
    client.put(f"/api/team-assessment/{p}", json={"confident": True})
    assert client.get("/api/team-assessment").json()["people"][0]["disposition"] == "keep and develop"
    assert client.put(f"/api/team-assessment/{p}", json={"criticality": 11}).status_code == 400
    assert client.put("/api/team-assessment/dynamics", json={"alliances": "[Placeholder]"}).json()["alliances"] == "[Placeholder]"
    assert client.post("/api/role-templates/starter").json()["templates"] == 2  # generic: software developer, QA engineer
    assert client.post("/api/role-templates/starter").status_code == 409
    client.put("/api/toolkit/settings", json={"platform": "salesforce"})
    assert client.post("/api/role-templates/starter").json()["templates"] == 2  # the Salesforce and MuleSoft roles
    i = client.post("/api/interviews", json={"person_id": p, "status": "done", "how_we_work": "[Placeholder]", "ownership": "owns problems"}).json()
    assert i["ownership"] == "owns problems" and client.get("/api/rollup").json()["notes"]["how_we_work"][0]["text"] == "[Placeholder]"


def test_team_alignment(client):
    g = client.post("/api/team-goals", json={"title": "[Placeholder goal]", "whole_team": True}).json()
    client.post("/api/team-goals", json={"title": "[Placeholder part]", "parent_id": g["id"], "from_value": 6, "to_value": 2, "by_date": "2027-03-31"})
    goals = {x["title"]: x for x in client.get("/api/team-align").json()["goals"]}
    assert not goals["[Placeholder goal]"]["measurable"] and goals["[Placeholder part]"]["measurable"]
    assert client.put("/api/team-align/tools", json={"vision": True, "bogus": True}).json() == {"vision": True}
    r = client.put("/api/team-align/incentives", json={"nonmonetary_available": "high", "nonmonetary_valued": "medium", "measurable": "low", "lag": "long", "interdependence": "interdependent"}).json()
    parts = {x["part"]: x["advice"] for x in r["incentive_mix"]}
    assert parts["Fixed or performance-based"].startswith("Mostly fixed") and parts["Individual or group"].startswith("Mostly group")
    assert client.put("/api/team-align/incentives", json={"lag": "forever"}).status_code == 400
    v = client.put("/api/team-align/vision", json={"draft": "[Placeholder vision]", "lenses": ["team", "nope"], "checks": ["vivid"]}).json()
    assert v["lenses"] == ["team"] and v["checks"] == ["vivid"]
    client.post("/api/situations", json={"area": "[Area]", "kind": "realignment"})
    assert client.get("/api/team-align").json()["mix"][0]["kind"] == "realignment"


def test_vision_offsite_before_and_decisions(client):
    v = client.put("/api/team-align/vision", json={"draft": "[Placeholder]", "themes": [{"theme": "[Theme A]", "said_in": [{"date": "2026-10-19", "where": "[weekly note]"}]}, {"theme": ""}], "live_it": True}).json()
    assert v["themes"] == [{"theme": "[Theme A]", "said_in": [{"date": "2026-10-19", "where": "[weekly note]"}]}] and v["live_it"]
    o = client.put("/api/team-align/offsite", json={"purposes": ["strategy", "planning", "conflict"]}).json()
    assert len(o["warnings"]) == 2
    assert client.put("/api/team-align/offsite", json={"purposes": ["diagnostic", "relationships"]}).json()["warnings"] == []
    b = client.put("/api/team-assessment/before", json={"roles": {"peacemaker": "[Placeholder]", "bogus": "x"}, "core_meeting": "too inclusive"}).json()
    assert b["roles"] == {"peacemaker": "[Placeholder]"} and client.get("/api/team-assessment/before").json()["advice"].startswith("Shrink")
    r = client.post("/api/decisions/suggest", json={"divisive": True, "inexperienced": True}).json()
    assert r["process"] == "consult and decide" and len(r["reasons"]) == 2
    client.post("/api/situations", json={"area": "[Area]", "kind": "realignment"})
    assert client.post("/api/decisions/suggest", json={"implementation": True}).json()["process"] == "build consensus"
    d = client.post("/api/decisions-needed", json={"decision": "[Placeholder decision]", "process": "build consensus", "process_told": True}).json()
    assert d["process"] == "build consensus" and d["process_told"]
    assert client.post("/api/culture/agreements/distributed").json()["agreements"] == 6
    assert client.post("/api/culture/agreements/distributed").status_code == 409


def test_alliances(client):
    a = client.post("/api/people", json={"name": "[Decider A]"}).json()["id"]
    b = client.post("/api/people", json={"name": "[Decider B]"}).json()["id"]
    c = client.post("/api/people", json={"name": "[Influencer C]", "opinion_leader": True, "power_sources": ["expertise"]}).json()["id"]
    d = client.post("/api/people", json={"name": "[Blocker D]"}).json()["id"]
    client.post("/api/influence-links", json={"from_id": c, "to_id": a, "strength": 3, "topic": "[branding]"})
    plan = client.post("/api/alliance-plans", json={"title": "[Placeholder early win]"}).json()
    rows = {"rows": [{"person_id": a, "what": "[approve]", "stance": "undecided"}, {"person_id": b, "stance": "for"}, {"person_id": d, "stance": "against"}]}
    client.patch(f"/api/alliance-plans/{plan['id']}", json={"rows": rows, "winning_ids": [a, b], "blocking_ids": [d], "pivotal": {str(d): {"resist": ["power"], "status_quo": True}}})
    dg = client.get(f"/api/alliance-plans/{plan['id']}/diagram").json()
    ids = {n["id"]: n for n in dg["nodes"]}
    assert set(ids) == {a, b, c, d} and ids[c]["opinion_leader"] and ids[d]["blocking"] and ids[a]["winning"]
    assert dg["edges"] == [{"from": c, "to": a, "strength": 3, "topic": "[branding]"}]
    g = client.get("/api/alliances/guide").json()
    assert len(g["resist"]) == 5 and len(g["persuadable"]) == 3
    assert client.post("/api/power-coalitions", json={"name": "[Placeholder coalition]", "member_ids": [c, d]}).status_code == 201


def test_influence_strategy_and_today(client):
    plan = client.post("/api/alliance-plans", json={"title": "[Placeholder early win]"}).json()
    st = {"counter": [{"argument": "[More meetings]", "answer": "[None beyond Scrum]"}], "path": [{"step": "[Explore]", "done": True}],
          "events": [{"title": "[Review]", "date": date.today().isoformat(), "done": False}, {"title": "[Later]", "date": "2099-01-01"}]}
    client.patch(f"/api/alliance-plans/{plan['id']}", json={"strategy": st})
    due = client.get("/api/today").json()["alliances"]
    assert [e["title"] for e in due] == ["[Review]"]
    g = client.get("/api/alliances/guide").json()
    assert [f["key"] for f in g["framing"]] == ["logos", "ethos", "pathos"] and len(g["social_checks"]) == 3 and len(g["path_starter"]) == 5
