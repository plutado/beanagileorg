import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit import sdlc
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_starter_loads_once_and_policies_start_as_drafts(client):
    out = client.post("/api/sdlc/starter").json()
    assert out == {"stages": 9, "environments": 6, "policies": 12}
    assert client.post("/api/sdlc/starter").status_code == 409
    d = client.get("/api/sdlc").json()
    assert [s["name"] for s in d["stages"]][:2] == ["Intake", "Refinement"] and d["stages"][-1]["name"] == "Support and learn"
    assert {p["status"] for p in d["policies"]} == {"draft"}
    assert [g["platform"] for g in d["environments"]] == ["MuleSoft", "Salesforce"]
    assert [e["name"] for e in d["environments"][1]["environments"]][-1] == "Production"


def test_starter_invents_nothing_specific():
    text = repr(sdlc.STARTER_STAGES) + repr(sdlc.STARTER_ENVIRONMENTS) + repr(sdlc.STARTER_POLICIES)
    for word in ("Copado", "Gearset", "GitHub", "Jenkins", "ServiceNow", "Okta"):
        assert word not in text


def test_move_keeps_positions_tidy(client):
    a = client.post("/api/sdlc-stages", json={"name": "[A]", "position": 0}).json()
    b = client.post("/api/sdlc-stages", json={"name": "[B]", "position": 1}).json()
    c = client.post("/api/sdlc-stages", json={"name": "[C]", "position": 2}).json()
    assert client.post(f"/api/sdlc-stages/{c['id']}/move", json={"direction": "up"}).json() == [a["id"], c["id"], b["id"]]
    assert client.post(f"/api/sdlc-stages/{a['id']}/move", json={"direction": "up"}).json() == [a["id"], c["id"], b["id"]]
    assert [s["position"] for s in client.get("/api/sdlc").json()["stages"]] == [0, 1, 2]
    assert client.post("/api/sdlc-stages/999/move", json={"direction": "up"}).status_code == 404


def test_document_is_exportable_only(client):
    s = client.post("/api/systems", json={"name": "[Tool]"}).json()
    client.post("/api/sdlc-stages", json={"name": "[Build]", "entry_criteria": ["[Ready]"], "exit_criteria": ["[Tested]"], "system_ids": [s["id"]], "notes": "[Private]"})
    client.post("/api/sdlc-environments", json={"name": "[Sandbox]", "platform": "[Platform]", "notes": "[Private env]"})
    client.post("/api/sdlc-policies", json={"title": "[Agreed]", "status": "agreed", "body": "[Rule]"})
    client.post("/api/sdlc-policies", json={"title": "[Retired]", "status": "retired"})
    md = client.post("/api/sdlc/document/export").json()["markdown"]
    assert "## 1. [Build]" in md and "- [Ready]" in md and "- [ ] [Tested]" in md and "Tools: [Tool]" in md
    assert "| [Sandbox] |" in md and "### [Agreed]" in md and "[Rule]" in md
    assert "[Private]" not in md and "[Private env]" not in md and "[Retired]" not in md
    assert client.get("/api/exports").json()[0]["kind"] == "sdlc:markdown"
    token = client.post("/api/tokens", json={"name": "reader", "scopes": ["export:read"]}).json()["token"]
    anon = TestClient(client.app)
    anon.headers["Authorization"] = f"Bearer {token}"
    assert anon.get("/api/sdlc/document").json()["markdown"] == md
    assert "history" not in anon.get("/api/sdlc").json()


def test_history_tracks_changes(client):
    st = client.post("/api/sdlc-stages", json={"name": "[Stage]"}).json()
    client.patch(f"/api/sdlc-stages/{st['id']}", json={"purpose": "[Why]"})
    assert any(h["field"] == "purpose" for h in client.get("/api/sdlc").json()["history"])
