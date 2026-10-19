"""The Agile reference: Scrum, common practices and SAFe, with how the team practices each one."""

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


def test_scrum_is_complete(client):
    d = client.get("/api/agile/reference").json()
    scrum = {e["key"]: e for e in d["entries"] if e["framework"] == "scrum"}
    for k in ("product-owner", "scrum-master", "developers", "sprint", "sprint-planning", "daily-scrum", "sprint-review", "retrospective",
              "product-backlog", "sprint-backlog", "increment", "product-goal", "sprint-goal", "definition-of-done"):
        assert k in scrum, k
    assert scrum["daily-scrum"]["timebox"] == "15 minutes"
    assert {e["kind"] for e in scrum.values()} >= {"accountability", "event", "artifact", "commitment"}
    safe = {e["key"] for e in d["entries"] if e["framework"] == "safe"}
    assert {"art", "rte", "pi", "pi-planning", "ip-iteration", "system-demo", "inspect-adapt", "roam", "wsjf"} <= safe
    assert "scrumguides.org" in d["sources"]["scrum"]["url"]


def test_marking_practice_and_coverage(client):
    assert client.put("/api/agile/practice/daily-scrum", json={"status": "practiced", "how": "[Placeholder]"}).status_code == 200
    assert client.put("/api/agile/practice/nope", json={}).status_code == 404
    assert client.put("/api/agile/practice/sprint", json={"status": "sometimes"}).status_code == 400
    d = client.get("/api/agile/reference").json()
    assert next(e for e in d["entries"] if e["key"] == "daily-scrum")["how"] == "[Placeholder]"
    assert d["coverage"]["scrum"]["practiced"] == 1


def test_every_toolkit_link_points_at_a_screen():
    from beanagileorg.toolkit.agile import REFERENCE
    from beanagileorg.toolkit.app import NAV

    paths = {n["path"] for n in NAV if n.get("path")}
    for e in REFERENCE:
        if e[7]:
            assert "/" + e[7][2:].split("/")[0] in paths, e[0]
