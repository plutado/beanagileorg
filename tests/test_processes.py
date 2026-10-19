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
