import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.core.db import Database, migrate
from beanagileorg.toolkit import models
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def system(client, name, **kw):
    return client.post("/api/systems", json={"name": name, **kw}).json()


def test_integration_rules(client):
    a, b, m = system(client, "[A]"), system(client, "[B]"), system(client, "[Middleware]", kind="integration")
    ok = client.post("/api/integrations", json={"name": "[Flow]", "from_id": a["id"], "to_id": b["id"], "via_id": m["id"]}).json()
    assert (ok["from_name"], ok["via_name"], ok["to_name"]) == ("[A]", "[Middleware]", "[B]")
    assert client.post("/api/integrations", json={"name": "[Loop]", "from_id": a["id"], "to_id": a["id"]}).status_code == 400
    assert client.post("/api/integrations", json={"name": "[Bad via]", "from_id": a["id"], "to_id": b["id"], "via_id": a["id"]}).status_code == 400
    assert client.post("/api/integrations", json={"name": "[Missing]", "from_id": a["id"], "to_id": 999}).status_code == 400
    assert client.patch(f"/api/integrations/{ok['id']}", json={"to_id": a["id"]}).status_code == 400


def test_map_skips_retired_and_unlinked_tools(client):
    a, b = system(client, "[App]"), system(client, "[Store]", kind="data store")
    system(client, "[Old]", lifecycle="retired")
    system(client, "[Editor]", kind="tool")
    git = system(client, "[Source control]", kind="tool")
    client.post("/api/integrations", json={"name": "[Writes]", "from_id": a["id"], "to_id": b["id"], "pattern": "database link"})
    client.post("/api/integrations", json={"name": "[Deploys]", "from_id": git["id"], "to_id": a["id"], "status": "planned"})
    m = client.get("/api/architecture/map").json()
    assert sorted(n["name"] for n in m["nodes"]) == ["[App]", "[Source control]", "[Store]"]
    assert len(m["edges"]) == 2


def test_system_detail_pulls_everything_together(client):
    a, b = system(client, "[A]", description="[What it is]", tech=["[Stack]"]), system(client, "[B]")
    client.post("/api/integrations", json={"name": "[Out]", "from_id": a["id"], "to_id": b["id"]})
    client.post("/api/integrations", json={"name": "[In]", "from_id": b["id"], "to_id": a["id"]})
    client.post("/api/offerings", json={"name": "[Offering]", "system_ids": [a["id"]]})
    client.post("/api/test-cases", json={"title": "[Case]", "system_id": a["id"]})
    client.post("/api/test-suites", json={"name": "[Suite]", "system_id": a["id"]})
    client.post("/api/arch-decisions", json={"title": "[Decision]", "system_ids": [a["id"]]})
    client.post("/api/guides", json={"title": "[Guide]", "system_ids": [a["id"]]})
    d = client.get(f"/api/architecture/system/{a['id']}").json()
    assert d["system"]["tech"] == ["[Stack]"]
    assert [i["name"] for i in d["outbound"]] == ["[Out]"] and [i["name"] for i in d["inbound"]] == ["[In]"]
    assert d["offerings"][0]["name"] == "[Offering]" and d["testing"]["manual_cases"] == 1 and d["testing"]["suites"][0]["name"] == "[Suite]"
    assert d["decisions"][0]["number"] == 1 and d["guides"][0]["title"] == "[Guide]"
    assert client.get("/api/architecture/system/999").status_code == 404


def test_decisions_are_numbered_and_guides_dated(client):
    one = client.post("/api/arch-decisions", json={"title": "[First]"}).json()
    two = client.post("/api/arch-decisions", json={"title": "[Second]", "number": 50}).json()
    assert (one["number"], two["number"], one["status"]) == (1, 2, "proposed") and one["date"]
    client.patch(f"/api/arch-decisions/{one['id']}", json={"status": "superseded", "superseded_by_id": two["id"]})
    assert client.get(f"/api/arch-decisions/{one['id']}").json()["superseded_by_number"] == 2
    g = client.post("/api/guides", json={"title": "[Guide]"}).json()
    assert g["updated"] and client.patch(f"/api/guides/{g['id']}", json={"body": "# [Heading]"}).json()["body"] == "# [Heading]"


def test_summary_gaps(client):
    system(client, "[Undocumented]", criticality="high")
    system(client, "[A tool]", kind="tool")
    owner = client.post("/api/people", json={"name": "[Owner]"}).json()
    system(client, "[Documented]", owner_id=owner["id"], description="[Desc]", docs_link="https://example.invalid/docs")
    s = client.get("/api/architecture/summary").json()
    assert [g["name"] for g in s["documentation_gaps"]] == ["[Undocumented]"]
    assert s["by_kind"]["tool"] == 1 and s["decisions"]["proposed"] == 0


def test_known_issues_and_integration_notes_private(client):
    a = system(client, "[A]", known_issues="[Weakness]")
    b = system(client, "[B]")
    client.post("/api/integrations", json={"name": "[Flow]", "from_id": a["id"], "to_id": b["id"], "notes": "[Quirk]"})
    client.post("/api/session/presentation", json={"on": True})
    d = client.get(f"/api/architecture/system/{a['id']}").json()
    assert "known_issues" not in d["system"] and "notes" not in d["outbound"][0] and d["system"]["name"] == "[A]"


def test_existing_systems_upgrade(tmp_path):
    db = Database(tmp_path / "old.db")
    with db.session() as conn:
        migrate(conn, "toolkit", models.MIGRATIONS[:8])
        conn.execute("INSERT INTO systems (name) VALUES ('[Existing]')")
        migrate(conn, "toolkit", models.MIGRATIONS)
        row = conn.execute("SELECT kind, lifecycle FROM systems").fetchone()
        assert (row["kind"], row["lifecycle"]) == ("application", "active")
