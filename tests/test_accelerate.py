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


def start(client, day):
    client.put("/api/toolkit/settings", json={"start_date": d(-day + 1)})


def test_learning_agenda(client):
    start(client, 25)
    assert client.post("/api/learning-questions/starter").json()["questions"] == 37
    assert client.post("/api/learning-questions/starter").status_code == 409
    a = client.get("/api/learning-questions/agenda").json()
    late = [q for q in a["questions"] if q["late"]]
    assert a["counts"]["open"] == 37 and late and all(q["due_day"] < 25 for q in late)
    assert {q["area"] for q in a["questions"]} == set(a["areas"])
    peer = client.post("/api/people", json={"name": "[Peer]"}).json()["id"]
    q = late[0]
    client.patch(f"/api/learning-questions/{q['id']}", json={"status": "answered", "answer": "[Answer]", "ask_ids": [peer]})
    a = client.get("/api/learning-questions/agenda").json()
    done = next(x for x in a["questions"] if x["id"] == q["id"])
    assert not done["late"] and done["ask_names"] == ["[Peer]"] and a["late"] == len(late) - 1
    assert client.get("/api/today").json()["accelerate"]["learning_late_count"] == len(late) - 1
    client.post("/api/session/presentation", json={"on": True})
    assert client.get("/api/learning-questions/agenda").json() == {"hidden": True}


def test_situations(client):
    assert set(client.get("/api/situations/guide").json()) == {"start-up", "turnaround", "accelerated growth", "realignment", "sustaining success"}
    assert client.post("/api/situations/starter").json()["areas"] == 6
    s = client.get("/api/situations").json()[0]
    client.patch(f"/api/situations/{s['id']}", json={"kind": "turnaround", "evidence": "[Private evidence]", "approach": "[Approach]"})
    assert client.patch(f"/api/situations/{s['id']}", json={"kind": "chaos"}).status_code == 400
    client.post("/api/session/presentation", json={"on": True})
    shown = client.get("/api/situations").json()[0]
    assert shown["kind"] == "turnaround" and shown["approach"] == "[Approach]" and "evidence" not in shown


def test_manager_conversations_and_plan_agreement(client):
    start(client, 22)
    boss = client.post("/api/people", json={"name": "[Boss]", "relationship": "manager"}).json()["id"]
    me = client.post("/api/people", json={"name": "[Me]", "manager_id": boss}).json()["id"]
    client.put("/api/people/me", json={"person_id": me})
    assert client.post("/api/boss-conversations/starter").json()["conversations"] == 6
    assert len(client.get("/api/today").json()["accelerate"]["boss_unheld"]) == 6
    first = client.get("/api/boss-conversations").json()[0]
    client.patch(f"/api/boss-conversations/{first['id']}", json={"held_on": d(-1), "agreed": "[Agreed]"})
    assert "The situation" not in client.get("/api/today").json()["accelerate"]["boss_unheld"]
    plan = next(p["id"] for p in client.get("/api/plans").json() if p["horizon_days"] == 90)
    p = client.post(f"/api/plans/{plan}/agree", json={}).json()
    assert p["status"] == "agreed" and p["agreed_with_id"] == boss and p["agreed_on"] == d(0)


def test_early_wins_mentoring_and_momentum(client):
    start(client, 30)
    plan = next(p["id"] for p in client.get("/api/plans").json() if p["horizon_days"] == 30)
    a = client.post("/api/plan-items", json={"plan_id": plan, "title": "[Win A]", "early_win": True}).json()["id"]
    client.post("/api/plan-items", json={"plan_id": plan, "title": "[Win B]", "early_win": True})
    client.post("/api/plan-items", json={"plan_id": plan, "title": "[Not a win]"})
    client.patch(f"/api/plan-items/{a}", json={"status": "done"})
    mgr = client.post("/api/people", json={"name": "[Other manager]", "relationship": "peer"}).json()["id"]
    ov = client.get("/api/mentoring/overview").json()
    assert ov["mentees"] == [] and ov["candidates"][0]["id"] == mgr
    client.post("/api/mentoring-sessions", json={"person_id": mgr, "date": d(-3), "topic": "[Sprint goals]", "next_step": "[Try it]", "next_on": d(2)})
    pr = client.post("/api/mentored-practices", json={"person_id": mgr, "practice": "[Sprint goals]"}).json()["id"]
    client.patch(f"/api/mentored-practices/{pr}", json={"status": "adopted", "since": d(0)})
    ov = client.get("/api/mentoring/overview").json()
    assert ov["mentees"][0]["adopted"] == 1 and ov["mentees"][0]["next_on"] == d(2) and ov["totals"]["adopted"] == 1
    assert client.get("/api/today").json()["accelerate"]["mentoring"][0]["name"] == "[Other manager]"
    client.post("/api/log-entries", json={"date": d(0), "kind": "win", "text": "[Win]"})
    client.post("/api/trust-pulses", json={"date": d(-14), "source": "my read", "scores": {"safety": 2, "clarity": 2}})
    client.post("/api/trust-pulses", json={"date": d(0), "source": "my read", "scores": {"safety": 4, "clarity": 3}})
    m = client.get("/api/first90/overview").json()["momentum"]
    assert m == {"early_wins": {"done": 1, "total": 2}, "changes_kept": 0, "wins_30": 1, "practices_adopted": 1, "trust": {"now": 3.5, "before": 2.0}}
    client.post("/api/session/presentation", json={"on": True})
    hidden = client.get("/api/mentoring/overview").json()
    assert hidden["hidden"] and hidden["adopted"][0]["practice"] == "[Sprint goals]"
    assert "momentum" not in client.get("/api/first90/overview").json()


def test_hypotheses_and_learning_balance(client):
    for n in range(6):
        client.post("/api/learning-questions", json={"question": f"[Technical question {n}]", "area": "technical"})
    b = client.get("/api/learning-questions/agenda").json()["balance"]
    assert b["counts"]["technical"] == 6 and b["technical_heavy"] is True
    q = client.post("/api/learning-questions", json={"question": "[Politics question]", "area": "politics"}).json()
    client.post("/api/learning-questions", json={"question": "[Culture question]", "area": "culture"})
    client.patch(f"/api/learning-questions/{q['id']}", json={"hypothesis": "[Placeholder]", "disprove_if": "[Placeholder]", "verdict": "testing"})
    b = client.get("/api/learning-questions/agenda").json()["balance"]
    assert b["technical_heavy"] is False and b["hypotheses"] == 1 and b["testing"] == 1


def test_sources_of_insight_and_learning_methods(client):
    ids = [client.post("/api/people", json={"name": f"[Placeholder name {n}]", "insight": [k]}).json()["id"] for n, k in enumerate(["historian", "integrator", "customer"])]
    s = client.get("/api/learning-questions/agenda").json()["sources"]
    assert {"historian", "integrator", "customer"} <= set(s["gaps"])
    client.post("/api/interactions", json={"date": date.today().isoformat(), "person_ids": [ids[0]]})
    s = client.get("/api/learning-questions/agenda").json()["sources"]
    assert "historian" not in s["gaps"] and next(k for k in s["kinds"] if k["key"] == "historian")["heard"] == 1
    m = client.get("/api/first90/learning-methods").json()
    assert len(m["methods"]) == 9 and all(x["status"] == "not yet" for x in m["methods"])
    client.put("/api/first90/learning-methods/decision", json={"status": "planned", "notes": "[Placeholder decision]"})
    assert client.put("/api/first90/learning-methods/nope", json={}).status_code == 404
    assert next(x for x in client.get("/api/first90/learning-methods").json()["methods"] if x["key"] == "decision")["status"] == "planned"


def test_listening_tour_fifth_question_rolls_up(client):
    p = client.post("/api/people", json={"name": "[Placeholder name 1]"}).json()["id"]
    client.post("/api/interviews", json={"person_id": p, "status": "done", "date": date.today().isoformat(), "if_you_were_me": "[Placeholder focus]", "how_answered": "[Placeholder]"})
    assert client.get("/api/rollup").json()["notes"]["if_you_were_me"][0]["text"] == "[Placeholder focus]"


def test_learning_plan_phases(client):
    p = client.get("/api/first90/learning-plan").json()
    assert [x["phase"] for x in p["phases"]] == ["Before day 1", "Soon after you start", "By day 30", "Days 31 to 60"] and p["done"] == 0
    client.put("/api/first90/learning-plan/top-down", json={"done": True})
    assert client.put("/api/first90/learning-plan/nope", json={}).status_code == 404
    p = client.get("/api/first90/learning-plan").json()
    assert p["done"] == 1 and next(s for ph in p["phases"] for s in ph["steps"] if s["key"] == "top-down")["done"] is True


def test_situation_guide_mood_pace_and_history(client):
    g = client.get("/api/situations/guide").json()
    assert g["turnaround"]["pace"] == "fast" and g["realignment"]["pace"] == "learn" and g["realignment"]["mood_job"]
    s = client.post("/api/situations", json={"area": "[Placeholder area]", "kind": "turnaround", "history": "[Placeholder]", "mood": "[Placeholder]"}).json()
    assert s["history"] == "[Placeholder]" and s["mood"] == "[Placeholder]"
