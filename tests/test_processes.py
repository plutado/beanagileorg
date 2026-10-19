"""Core processes: ratings on four measures, a focus limit, a workflow map, and turning a failing handoff into work."""

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


def test_guide_and_starter(client):
    g = client.get("/api/processes/guide").json()
    assert [m["key"] for m in g["measures"]] == ["productivity", "timeliness", "reliability", "quality"] and g["focus_limit"] == 3
    assert client.post("/api/core-processes/starter").json()["processes"] == len(g["starter"])
    assert client.post("/api/core-processes/starter").status_code == 409


def test_linked_metrics(client):
    client.post("/api/metrics", json={"name": "Change failure rate"})
    assert client.get("/api/processes/guide").json()["linked_metrics"]["reliability"][0]["name"] == "Change failure rate"


def test_map_and_handoff_to_work(client):
    p = client.post("/api/core-processes", json={"name": "[Placeholder process]", "focus": True, "importance": "high", "aim": "execution"}).json()
    steps = [{"text": "[Build]", "who": "[Developers]", "passes": "[Change]", "bottleneck": False, "handoff_issue": "[Missing test notes]"},
             {"text": "[Test]", "who": "[QA]", "passes": "", "bottleneck": True, "handoff_issue": ""}]
    client.patch(f"/api/core-processes/{p['id']}", json={"map": {"steps": steps}, "ratings": {"reliability": {"rating": "weak"}}})
    r = client.post(f"/api/core-processes/{p['id']}/step-to", json={"index": 0, "to": "risk"}).json()
    assert "[Missing test notes] ([Build] to [Test])" in client.get(f"/api/risks/{r['id']}").json()["title"]
    a = client.post(f"/api/core-processes/{p['id']}/step-to", json={"index": 1, "to": "devsync"}).json()
    assert "bottleneck at [Test]" in client.get(f"/api/actions/{a['id']}").json()["concern"]
    assert client.post(f"/api/core-processes/{p['id']}/step-to", json={"index": 5, "to": "risk"}).status_code == 400
    assert client.post(f"/api/core-processes/{p['id']}/from-sdlc").status_code == 409


def test_from_sdlc_needs_stages(client):
    p = client.post("/api/core-processes", json={"name": "[Placeholder process]"}).json()
    assert client.post(f"/api/core-processes/{p['id']}/from-sdlc").status_code == 400
    client.post("/api/sdlc-stages", json={"name": "[Stage A]", "roles": "[Role A], [Role B]"})
    m = client.post(f"/api/core-processes/{p['id']}/from-sdlc").json()["map"]["steps"]
    assert m[0]["text"] == "[Stage A]" and m[0]["who"] == "[Role A]"


def test_skill_base(client):
    client.post("/api/people", json={"name": "[Placeholder name 1]", "skills": ["[Skill A]", "[Skill B]"]})
    client.post("/api/people", json={"name": "[Placeholder name 2]", "skills": ["[Skill A]"]})
    client.post("/api/systems", json={"name": "[System A]"})
    k = {x["key"]: x for x in client.get("/api/skills/knowledge").json()["kinds"]}
    assert k["individual"]["facts"]["single"] == ["[Skill B]"] and k["embedded"]["facts"]["no_backup"] == ["[System A]"]
    p = client.post("/api/core-processes", json={"name": "[Placeholder process]", "skills": ["[Skill A]", "[skill b]", "[Skill C]"]}).json()
    rows = {r["skill"]: r["count"] for r in client.get("/api/skills/coverage").json()[0]["skills"]}
    assert rows == {"[Skill A]": 2, "[skill b]": 1, "[Skill C]": 0}
    g = client.post("/api/skill-gaps", json={"title": "[Placeholder gap]", "kind": "embedded", "process_id": p["id"], "speed": "quick fix", "plan": "pair"}).json()
    assert g["process_name"] == "[Placeholder process]"
    assert client.post("/api/skill-gaps", json={"title": "[x]", "kind": "spiritual"}).status_code == 400
    assert client.post("/api/knowledge-sources", json={"name": "[Placeholder community]", "kind": "community"}).status_code == 201
