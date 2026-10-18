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


def test_revisions_and_restore(client):
    s = client.post("/api/sprints/next", json={}).json()
    n = client.post("/api/ceremony-notes", json={"sprint_id": s["id"], "type": "retro", "happened": "[First draft]\n[Line two]"}).json()
    client.patch(f"/api/ceremony-notes/{n['id']}", json={"happened": "[First draft]\n[Line two, edited]\n[Line three]"})
    h = client.get(f"/api/history/ceremony_note/{n['id']}").json()
    assert len(h["revisions"]) == 2 and h["exists"]
    latest = next(c for c in h["revisions"][0]["changes"] if c["field"] == "happened")
    assert latest["long"] and latest["old"] == "[First draft]\n[Line two]"
    client.post(f"/api/history/ceremony_note/{n['id']}/restore", json={"change_id": latest["change_id"], "which": "old"})
    assert client.get(f"/api/ceremony-notes/{n['id']}").json()["happened"] == "[First draft]\n[Line two]"
    assert len(client.get(f"/api/history/ceremony_note/{n['id']}").json()["revisions"]) == 3


def test_restore_decodes_lists_and_numbers(client):
    d = client.post("/api/tech-debt", json={"title": "[Debt]", "categories": ["stability"], "impact": 2}).json()
    client.patch(f"/api/tech-debt/{d['id']}", json={"categories": ["performance", "cost"], "impact": 5})
    changes = {c["field"]: c for c in client.get(f"/api/history/tech_debt/{d['id']}").json()["revisions"][0]["changes"]}
    for f in ("categories", "impact"):
        client.post(f"/api/history/tech_debt/{d['id']}/restore", json={"change_id": changes[f]["change_id"]})
    back = client.get(f"/api/tech-debt/{d['id']}").json()
    assert (back["categories"], back["impact"]) == (["stability"], 2)


def test_history_is_private(client):
    p = client.post("/api/people", json={"name": "[Person]", "support_notes": "[Private]"}).json()
    assert client.get("/api/history/nothing/1").status_code == 404
    token = client.post("/api/tokens", json={"name": "reader", "scopes": ["export:read"]}).json()["token"]
    anon = TestClient(client.app)
    anon.headers["Authorization"] = f"Bearer {token}"
    assert anon.get(f"/api/history/person/{p['id']}").status_code == 403
    client.post("/api/session/presentation", json={"on": True})
    assert client.get(f"/api/history/person/{p['id']}").status_code == 403


def test_retro_detail_history_button_points_at_the_retro():
    """The retro form's actions row once referenced an undefined `i`, which crashed every retro page."""
    import re
    from pathlib import Path

    from beanagileorg.toolkit import app as toolkit_app

    js = (Path(toolkit_app.__file__).parent / "static/app.js").read_text()
    start = js.index('id="del">Delete retro</button>')
    actions = js[start : js.index("</div></form>", start)]
    assert re.findall(r"BA\.historyButton\(([^)]*)\)", actions) == ['"retro", id']
