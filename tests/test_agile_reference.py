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


FAKE_GUIDE = "<html><body><nav>skip me</nav><h1>[Placeholder guide title]</h1><h2>Purpose</h2><p>[Placeholder purpose]</p>" \
    "<h2>Scrum Definition</h2><p>[Placeholder definition, <strong>with bold</strong>.]</p>" \
    "<ol><li><p>[Step one]</p></li><li><p>[Step two]</p></li></ol><ul><li>[A bullet]</li></ul><h2>Scrum Theory</h2><h3>Transparency</h3>" \
    + "".join(f"<p>[Placeholder paragraph {n}] Scrum</p>" for n in range(120)) + "<p>Creative Commons notice</p></body></html>"


def test_import_guide_and_study_plan(client, monkeypatch):
    from beanagileorg.toolkit import agile

    assert client.get("/api/agile/guide").json()["markdown"] is None
    monkeypatch.setattr(agile, "fetch_official", lambda url=agile.GUIDE_URL: FAKE_GUIDE)
    r = client.post("/api/agile/guide/import").json()
    assert r["sections"] == 4
    g = client.get("/api/agile/guide").json()
    assert g["markdown"].startswith("# [Placeholder guide title]") and "skip me" not in g["markdown"]
    assert g["definition"] == "[Placeholder definition, **with bold**.]\n\n1. [Step one]\n2. [Step two]\n\n- [A bullet]" and g["how"] == "imported"
    assert client.post("/api/agile/guide/study-plan").json()["created"] == 4
    assert client.post("/api/agile/guide/study-plan").json()["created"] == 0


def test_import_failure_and_paste(client, monkeypatch):
    from beanagileorg.toolkit import agile

    def boom(url=None):
        raise OSError("offline")

    monkeypatch.setattr(agile, "fetch_official", boom)
    assert client.post("/api/agile/guide/import").status_code == 502
    client.put("/api/agile/guide", json={"markdown": "# [Pasted]\n\n## Scrum Definition\n\n[Placeholder]", "source": "[Placeholder source]"})
    g = client.get("/api/agile/guide").json()
    assert g["how"] == "pasted" and g["definition"] == "[Placeholder]"
    client.put("/api/agile/definitions", json={"definitions": [{"title": "[Agile]", "text": "[Placeholder]", "source": "[Source]"}, {"text": ""}]})
    assert len(client.get("/api/agile/guide").json()["definitions"]) == 1
