from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from beanagile.core.config import Settings
from beanagile.core.db import Database, migrate
from beanagile.toolkit import models
from beanagile.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def day(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def test_vendor_counts_and_overview(client):
    contact = client.post("/api/people", json={"name": "[Contact]", "relationship": "vendor"}).json()["id"]
    v = client.post("/api/vendors", json={"name": "[Vendor]", "type": "contractor agency", "contact_ids": [contact]}).json()
    client.post("/api/vendor-interactions", json={"vendor_id": v["id"], "date": day(-2), "summary": "[Summary]", "people_ids": [contact]})
    client.post("/api/vendor-concerns", json={"vendor_id": v["id"], "title": "[Concern]", "owner_id": contact, "due": day(3)})
    listed = client.get("/api/vendors").json()[0]
    assert listed["open_concerns"] == 1 and listed["last_contact"] == day(-2)
    o = client.get(f"/api/vendors/{v['id']}/overview").json()
    assert o["vendor"]["contacts"] == [{"id": contact, "name": "[Contact]"}]
    assert o["interactions"][0]["people"] == ["[Contact]"]
    assert o["concerns"][0]["owner_name"] == "[Contact]"
    assert client.get("/api/vendors/999/overview").status_code == 404


def test_follow_up_becomes_dev_sync_item(client):
    v = client.post("/api/vendors", json={"name": "[Vendor]"}).json()
    i = client.post("/api/vendor-interactions", json={"vendor_id": v["id"], "date": day(0), "summary": "[Summary]"}).json()
    item = client.post(f"/api/vendor-interactions/{i['id']}/follow-up", json={}).json()
    assert item["origin"] == "vendor" and item["vendor_name"] == "[Vendor]" and item["concern"].startswith("[Vendor]: follow-up")
    assert client.get(f"/api/vendors/{v['id']}/overview").json()["follow_ups"][0]["id"] == item["id"]


def test_renewals_respect_notice_window(client):
    client.post("/api/vendors", json={"name": "[Soon]", "contract_end": day(20), "renewal_notice_days": 30})
    client.post("/api/vendors", json={"name": "[Later]", "contract_end": day(200), "renewal_notice_days": 30})
    client.post("/api/vendors", json={"name": "[Ended]", "contract_end": day(5), "status": "ended"})
    assert [v["name"] for v in client.get("/api/vendors/renewals").json()] == ["[Soon]"]
    assert [v["name"] for v in client.get("/api/vendors/renewals?days=365").json()] == ["[Soon]", "[Later]"]
    assert [v["name"] for v in client.get("/api/today").json()["vendor_renewals"]] == ["[Soon]"]


def test_vendor_privacy(client):
    v = client.post("/api/vendors", json={"name": "[Vendor]", "commercial_terms": "[Terms]", "notes": "[Notes]"}).json()
    client.post("/api/vendor-interactions", json={"vendor_id": v["id"], "summary": "[Private conversation]"})
    client.post("/api/vendor-concerns", json={"vendor_id": v["id"], "title": "[Shown]", "resolution": "[Private]"})
    client.post("/api/session/presentation", json={"on": True})
    shown = client.get("/api/vendors").json()[0]
    assert "commercial_terms" not in shown and "notes" not in shown
    o = client.get(f"/api/vendors/{v['id']}/overview").json()
    assert o["interactions"] == [] and "resolution" not in o["concerns"][0]


def test_systems_link_to_vendors(client):
    v = client.post("/api/vendors", json={"name": "[Vendor]"}).json()
    s = client.post("/api/systems", json={"name": "[System]", "vendor_id": v["id"]}).json()
    assert client.get(f"/api/systems/{s['id']}").json()["vendor_name"] == "[Vendor]"
    assert client.get(f"/api/vendors/{v['id']}/overview").json()["systems"][0]["name"] == "[System]"


def test_migration_upgrades_an_existing_database(tmp_path):
    db = Database(tmp_path / "old.db")
    with db.session() as conn:
        migrate(conn, "toolkit", models.MIGRATIONS[:2])
        conn.execute("INSERT INTO action_items (concern) VALUES ('[Existing]')")
        assert migrate(conn, "toolkit", models.MIGRATIONS) == [3]
        assert conn.execute("SELECT vendor_id FROM action_items").fetchone()[0] is None
