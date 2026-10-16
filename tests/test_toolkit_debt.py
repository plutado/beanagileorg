from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit import debt
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def day(n):
    return (date.today() + timedelta(days=n)).isoformat()


def test_scoring_and_quadrants():
    assert debt.score({"impact": 4, "risk": 4, "effort": "S"}) == {"value": 8, "score": 8.0, "quadrant": "quick win"}
    assert debt.score({"impact": 5, "risk": 3, "effort": "XL"})["quadrant"] == "big bet"
    assert debt.score({"impact": 2, "risk": 2, "effort": "M"})["quadrant"] == "fill-in"
    assert debt.score({"impact": 1, "risk": 2, "effort": "L"})["quadrant"] == "money pit"
    assert debt.score({"impact": 3})["quadrant"] == "not scored"


def test_overview_counts_and_capacity(client):
    s = client.post("/api/sprints/next", json={"start_date": day(-2)}).json()
    client.patch(f"/api/sprints/{s['id']}", json={"capacity": 40})
    client.put("/api/debt/policy", json={"allocation": 20, "agreed_with": "[Manager]"})
    client.post("/api/tech-debt", json={"title": "[Flaky checkout job]", "categories": ["stability", "revenue and conversion"], "impact": 5, "risk": 4, "effort": "M", "points": 5, "sprint_id": s["id"], "status": "planned"})
    client.post("/api/tech-debt", json={"title": "[No alerts on sync]", "categories": ["observability"], "impact": 3, "risk": 4, "effort": "S", "points": 3})
    client.post("/api/tech-debt", json={"title": "[Done one]", "categories": ["cleanup"], "status": "done"})
    o = client.get("/api/debt/overview").json()
    cats = {c["key"]: c["open"] for c in o["categories"]}
    assert cats["stability"] == 1 and cats["observability"] == 1 and cats["cleanup"] == 0
    assert o["quadrants"]["quick win"] == 2
    assert o["capacity"] == {"sprint_id": s["id"], "sprint_number": 1, "capacity": 40, "planned_points": 5, "target_points": 8, "share": 12}
    assert client.put("/api/debt/policy", json={"allocation": 140}).status_code == 400


def test_decisions_move_the_item(client):
    d = client.post("/api/tech-debt", json={"title": "[Old integration]", "categories": ["cleanup"]}).json()
    assert client.post(f"/api/tech-debt/{d['id']}/decide", json={"decision": "accept for now"}).status_code == 400
    client.post(f"/api/tech-debt/{d['id']}/decide", json={"decision": "accept for now", "revisit_on": day(10), "decided_by": "[Leader]", "rationale": "[Peak season first]"})
    item = client.get(f"/api/tech-debt/{d['id']}").json()
    assert (item["status"], item["revisit_on"]) == ("accepted", day(10))
    assert client.get("/api/today").json()["debt_due"] == [{"id": d["id"], "title": "[Old integration]", "when": day(10), "kind": "revisit"}]
    client.post(f"/api/tech-debt/{d['id']}/decide", json={"decision": "schedule"})
    item = client.get(f"/api/tech-debt/{d['id']}").json()
    assert (item["status"], item["revisit_on"]) == ("planned", None)
    assert [x["decision"] for x in client.get(f"/api/tech-debt/{d['id']}/decisions").json()] == ["schedule", "accept for now"]
    assert client.post(f"/api/tech-debt/{d['id']}/decide", json={"decision": "maybe"}).status_code == 400
    assert client.post("/api/tech-debt/999/decide", json={"decision": "schedule"}).status_code == 404


def test_summary_is_shareable_only(client):
    client.put("/api/debt/policy", json={"allocation": 15, "agreed_with": "[Manager]", "agreed_on": "2026-11-20"})
    client.post("/api/tech-debt", json={"title": "[Slow search]", "categories": ["performance"], "impact": 4, "risk": 3, "effort": "M", "cost_of_delay": "[Lost conversions]", "notes": "[Private]", "evidence": "[Private evidence]"})
    d = client.post("/api/tech-debt", json={"title": "[Legacy job]", "categories": ["cleanup"]}).json()
    client.post(f"/api/tech-debt/{d['id']}/decide", json={"decision": "accept for now", "revisit_on": "2027-01-15"})
    md = client.post("/api/debt/summary/export").json()["markdown"]
    assert "15% of each sprint" in md and "agreed with [Manager] on 2026-11-20" in md
    assert "| Performance | 1 |" in md and "| [Slow search] | [Lost conversions] | performance | 7/10 | M |" in md
    assert "- [Legacy job] (revisit 2027-01-15)" in md
    assert "[Private]" not in md and "[Private evidence]" not in md
    assert client.get("/api/exports").json()[0]["kind"] == "debt:markdown"


def test_system_page_lists_its_debt(client):
    s = client.post("/api/systems", json={"name": "[System]"}).json()
    client.post("/api/tech-debt", json={"title": "[Debt on system]", "system_ids": [s["id"]], "categories": ["maintainability"]})
    client.post("/api/tech-debt", json={"title": "[Fixed]", "system_ids": [s["id"]], "status": "done"})
    assert [x["title"] for x in client.get(f"/api/architecture/system/{s['id']}").json()["debt"]] == ["[Debt on system]"]


def test_updates_add_new_starter_coaching_without_reviving_deletions(tmp_path):
    first = TestClient(build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path)), follow_redirects=False)
    first.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    guides = {g["slug"]: g["id"] for g in first.get("/api/coaching/library").json()["guides"]}
    assert "tech-debt-case" in guides and "/debt" in first.get("/api/coaching/tips").json()
    # Pretend this install was set up before version 2, and that the leader deleted a guide.
    first.delete(f"/api/coaching-guides/{guides['tech-debt-case']}")
    first.delete(f"/api/coaching-guides/{guides['assertiveness']}")
    for t in first.get("/api/coaching-tips").json():
        if t["route"] == "/debt":
            first.delete(f"/api/coaching-tips/{t['id']}")
    db = first.app.state.db
    with db.session() as conn:
        conn.execute("UPDATE settings SET value = '1' WHERE key = 'coaching.starter_version'")
    again = TestClient(build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path)), follow_redirects=False)
    again.post("/login", data={"password": PASSWORD})
    slugs = {g["slug"] for g in again.get("/api/coaching/library").json()["guides"]}
    assert "tech-debt-case" in slugs and "assertiveness" not in slugs
    assert len(again.get("/api/coaching/tips").json()["/debt"]) == 2
