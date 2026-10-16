import pytest
from fastapi.testclient import TestClient

from beanagile.core.config import Settings
from beanagile.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_org_tree_people_and_offerings(client):
    top = client.post("/api/departments", json={"name": "[Division]", "kind": "division"}).json()
    dept = client.post("/api/departments", json={"name": "[Department]", "parent_id": top["id"]}).json()
    team = client.post("/api/departments", json={"name": "[Team]", "kind": "team", "parent_id": dept["id"]}).json()
    client.post("/api/people", json={"name": "[Placed]", "department_id": team["id"]})
    client.post("/api/people", json={"name": "[Unplaced]"})
    client.post("/api/offerings", json={"name": "[Offering]", "department_id": dept["id"]})
    org = client.get("/api/landscape/org").json()
    d = org["tree"][0]["children"][0]
    assert d["name"] == "[Department]" and d["offerings"] == [{"id": 1, "name": "[Offering]"}]
    assert d["children"][0]["people"][0]["name"] == "[Placed]"
    assert [p["name"] for p in org["unassigned"]] == ["[Unplaced]"]
    assert [p["name"] for p in client.get(f"/api/landscape/department/{team['id']}").json()["path"]] == ["[Division]", "[Department]"]


def test_departments_cannot_loop(client):
    a = client.post("/api/departments", json={"name": "[A]"}).json()
    b = client.post("/api/departments", json={"name": "[B]", "parent_id": a["id"]}).json()
    assert client.patch(f"/api/departments/{a['id']}", json={"parent_id": b["id"]}).status_code == 400
    assert client.patch(f"/api/departments/{a['id']}", json={"parent_id": a["id"]}).status_code == 400
    assert client.post("/api/departments", json={"name": "[C]", "parent_id": 999}).status_code == 400


def test_deleting_a_department_moves_teams_up(client):
    a = client.post("/api/departments", json={"name": "[A]"}).json()
    b = client.post("/api/departments", json={"name": "[B]", "parent_id": a["id"]}).json()
    c = client.post("/api/departments", json={"name": "[C]", "parent_id": b["id"]}).json()
    client.post("/api/assessments", json={"subject_type": "department", "subject_id": b["id"], "quadrant": "strength", "title": "[Point]"})
    assert client.delete(f"/api/departments/{b['id']}").status_code == 204
    assert client.get(f"/api/departments/{c['id']}").json()["parent_id"] == a["id"]
    assert client.get("/api/assessments").json() == []


def test_offering_links_and_swot_counts(client):
    s = client.post("/api/systems", json={"name": "[System]"}).json()
    v = client.post("/api/vendors", json={"name": "[Vendor]"}).json()
    o = client.post("/api/offerings", json={"name": "[Offering]", "system_ids": [s["id"]], "vendor_ids": [v["id"]], "maturity": "growing"}).json()
    for q in ("weakness", "weakness", "opportunity"):
        client.post("/api/assessments", json={"subject_type": "offering", "subject_id": o["id"], "quadrant": q, "title": f"[{q}]"})
    client.post("/api/assessments", json={"subject_type": "offering", "subject_id": o["id"], "quadrant": "threat", "title": "[Closed]", "status": "closed"})
    listed = client.get("/api/landscape/offerings").json()[0]
    assert listed["systems"] == [{"id": s["id"], "name": "[System]"}] and listed["vendors"][0]["name"] == "[Vendor]"
    assert listed["swot"] == {"strength": 0, "weakness": 2, "opportunity": 1, "threat": 0}
    detail = client.get(f"/api/landscape/offering/{o['id']}").json()
    assert len(detail["assessments"]["weakness"]) == 2 and len(detail["assessments"]["threat"]) == 1
    swot = client.get("/api/landscape/swot").json()["quadrants"]
    assert swot["threat"] == [] and swot["weakness"][0]["subject_name"] == "[Offering]"
    assert client.get("/api/landscape/thing/1").status_code == 404
    assert client.post("/api/assessments", json={"subject_type": "offering", "subject_id": o["id"], "quadrant": "maybe", "title": "[X]"}).status_code == 400


def test_assessment_to_roadmap_and_risk(client):
    o = client.post("/api/offerings", json={"name": "[Offering]"}).json()
    a = client.post("/api/assessments", json={"subject_type": "offering", "subject_id": o["id"], "quadrant": "opportunity", "title": "[Idea]", "evidence": "[Private evidence]", "confidence": "high"}).json()
    done = client.post(f"/api/assessments/{a['id']}/to-roadmap").json()
    item = client.get(f"/api/roadmap/{done['roadmap_item_id']}").json()
    assert item["title"] == "[Idea]" and not item.get("description") and done["status"] == "acted on"
    assert client.post(f"/api/assessments/{a['id']}/to-roadmap").status_code == 409
    done = client.post(f"/api/assessments/{a['id']}/to-risk").json()
    risk = client.get(f"/api/risks/{done['risk_id']}").json()
    assert (risk["title"], risk["level"], risk["notes"]) == ("[Idea]", "high", "[Private evidence]")


def test_assessment_is_private(client):
    o = client.post("/api/offerings", json={"name": "[Shown]", "description": "[Shown too]", "notes": "[Private note]"}).json()
    client.post("/api/assessments", json={"subject_type": "offering", "subject_id": o["id"], "quadrant": "weakness", "title": "[Private]"})
    client.post("/api/session/presentation", json={"on": True})
    listed = client.get("/api/landscape/offerings").json()[0]
    assert listed["name"] == "[Shown]" and "notes" not in listed and listed["swot"] is None
    assert "assessments" not in client.get(f"/api/landscape/offering/{o['id']}").json()
    assert client.get("/api/landscape/swot").json() == {"private": True, "quadrants": {}}
    assert client.get("/api/assessments").json() == []
