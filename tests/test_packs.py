"""Sharing between installs: a pack of chosen records and fields, exported from one install and merged into another."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


def make(tmp_path, name):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path / name)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


@pytest.fixture
def two(tmp_path):
    return make(tmp_path, "a"), make(tmp_path, "b")


def test_granular_export(two):
    a, _ = two
    owner = a.post("/api/people", json={"name": "[Owner A]"}).json()["id"]
    p1 = a.post("/api/sdlc-policies", json={"title": "[Policy 1]", "body": "[Body]", "status": "agreed", "owner_id": owner}).json()["id"]
    a.post("/api/sdlc-policies", json={"title": "[Policy 2]"})
    k = {x["key"]: x for x in a.get("/api/packs/kinds").json()["kinds"]}
    assert "notes" not in k["regression_plans"]["shareable"] and k["sdlc_policies"]["links"] == ["owner_id"]
    assert a.post("/api/packs/review", json={"selection": {}}).status_code == 400
    sel = {"sdlc_policies": {"ids": [p1], "fields": ["status"], "links": {"owner_id": "name"}}}
    pack = a.post("/api/packs/export", json={"selection": sel, "from": "[Manager A]"}).json()
    recs = pack["kinds"]["sdlc_policies"]["records"]
    assert len(recs) == 1 and recs[0]["values"] == {"title": "[Policy 1]", "status": "agreed"} and recs[0]["people"] == {"owner_id": "[Owner A]"}
    assert a.get(f"/api/sdlc-policies/{p1}").json()["pack_uid"] == recs[0]["uid"]
    dropped = a.post("/api/packs/review", json={"selection": {"sdlc_policies": {"ids": [p1], "fields": [], "links": {"owner_id": "drop"}}}}).json()
    assert "people" not in dropped["kinds"]["sdlc_policies"]["records"][0]


def test_import_preview_merge_and_repeat(two):
    a, b = two
    rt = a.post("/api/role-templates", json={"name": "[Role A]", "measures": ["[M1]"], "should_show": "[Show]", "notes": "[Private note]"}).json()["id"]
    sel = {"role_templates": {"ids": [rt], "fields": ["measures", "should_show", "notes"]}}
    pack = a.post("/api/packs/export", json={"selection": sel, "from": "[Manager A]"}).json()
    assert "notes" not in pack["kinds"]["role_templates"]["records"][0]["values"]
    view = b.post("/api/packs/inspect", json={"pack": pack}).json()
    assert view["kinds"][0]["records"][0]["status"] == "new"
    assert b.post("/api/packs/apply", json={"pack": pack}).json()["added"] == 1
    mine = next(t for t in b.get("/api/role-templates").json() if t["name"] == "[Role A]")
    assert mine["origin"]["from"] == "[Manager A]" and mine["measures"] == ["[M1]"]
    again = b.post("/api/packs/inspect", json={"pack": pack}).json()["kinds"][0]["records"][0]
    assert again["status"] == "unchanged"
    assert b.post("/api/packs/apply", json={"pack": pack}).json()["skipped"] == 1
    # both sides change the same field: a conflict, kept by default, mergeable field by field
    a.patch(f"/api/role-templates/{rt}", json={"should_show": "[Theirs]", "measures": ["[M1]", "[M2]"]})
    b.patch(f"/api/role-templates/{mine['id']}", json={"should_show": "[Mine]"})
    newer = a.post("/api/packs/export", json={"selection": sel, "from": "[Manager A]"}).json()
    rec = b.post("/api/packs/inspect", json={"pack": newer}).json()["kinds"][0]["records"][0]
    assert rec["status"] == "conflict" and rec["default"] == "keep"
    assert {d["field"]: d["conflict"] for d in rec["diffs"]} == {"should_show": True, "measures": False}
    decision = {"role_templates": {rec["uid"]: {"action": "merge", "fields": {"should_show": "mine", "measures": "theirs"}}}}
    assert b.post("/api/packs/apply", json={"pack": newer, "decisions": decision}).json()["updated"] == 1
    merged = b.get(f"/api/role-templates/{mine['id']}").json()
    assert merged["should_show"] == "[Mine]" and merged["measures"] == ["[M1]", "[M2]"]
    assert len(b.get("/api/packs/log").json()["imports"]) == 3


def test_tampered_pack_and_copy(two):
    a, b = two
    p = a.post("/api/regression-plans", json={"title": "[Plan]", "kind": "peak-season freeze"}).json()["id"]
    pack = a.post("/api/packs/export", json={"selection": {"regression_plans": {"ids": [p], "fields": ["kind"]}}}).json()
    bad = {**pack, "kinds": {**pack["kinds"]}}
    bad["kinds"]["regression_plans"] = {**pack["kinds"]["regression_plans"], "records": []}
    assert b.post("/api/packs/inspect", json={"pack": bad}).status_code == 400
    assert b.post("/api/packs/inspect", json={"pack": {"format": "other"}}).status_code == 400
    b.post("/api/regression-plans", json={"title": "[Plan]", "kind": "other"})
    rec = b.post("/api/packs/inspect", json={"pack": pack}).json()["kinds"][0]["records"][0]
    assert rec["status"] == "changed"
    r = b.post("/api/packs/apply", json={"pack": pack, "decisions": {"regression_plans": {rec["uid"]: {"action": "copy"}}}}).json()
    assert r["copied"] == 1 and any(x["title"].startswith("[Plan] (from") for x in b.get("/api/regression-plans").json())
