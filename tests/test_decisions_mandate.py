"""Mandate links and versions, decision rights on the RACI, the decision log, SDLC stage links and versions."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


@pytest.fixture
def c(tmp_path):
    client = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return client


def my_mandate(c):
    me = c.post("/api/people", json={"name": "[Me]", "active": True}).json()["id"]
    c.put("/api/people/me", json={"person_id": me})
    m = c.post("/api/mandates/mine", json={}).json()
    return m["id"]


def test_outcomes_show_what_serves_them_and_versions_compare(c):
    mid = my_mandate(c)
    out = c.post("/api/mandate-items", json={"mandate_id": mid, "kind": "outcome", "text": "[Stable releases]", "due_day": 180}).json()["id"]
    dec = c.post("/api/mandate-items", json={"mandate_id": mid, "kind": "decision", "text": "[Release go or no-go]", "authority": "to clarify"}).json()["id"]
    plans = c.get("/api/plans").json()
    c.post("/api/plan-items", json={"plan_id": plans[0]["id"], "title": "[One clean release]", "serves_id": out})
    c.post("/api/roadmap", json={"title": "[Release checklist live]", "serves_id": out})
    full = c.get(f"/api/mandates/{mid}/full").json()
    served = full["outcomes"][0]["served_by"]
    assert {s["kind"] for s in served} == {"plan item", "roadmap"}
    c.post(f"/api/mandates/{mid}/agree", json={})
    v1 = c.get(f"/api/mandates/{mid}/versions").json()
    assert len(v1) == 1 and v1[0]["label"].startswith("Agreed")
    c.patch(f"/api/mandate-items/{dec}", json={"authority": "I decide and inform"})
    c.post("/api/mandate-items", json={"mandate_id": mid, "kind": "outcome", "text": "[Scrum of Scrums running]"})
    v2 = c.post(f"/api/mandates/{mid}/versions", json={"label": "Day 90"}).json()["id"]
    cmp = c.get(f"/api/mandates/{mid}/compare?a={v1[0]['id']}&b={v2}").json()
    assert cmp["after"] == "Day 90" and cmp["outcomes"] == [{"change": "added", "text": "[Scrum of Scrums running]"}]
    assert cmp["decisions"][0]["fields"]["authority"] == ["to clarify", "I decide and inform"]
    assert c.get(f"/api/mandates/{mid}/compare?a={v1[0]['id']}").json()["after"] == "Now"
    raci = c.get("/api/raci").json()
    assert {"text": "[Release go or no-go]", "authority": "I decide and inform"} in raci["mandate_rights"]


def test_decision_log_gathers_every_kind(c):
    d = c.post("/api/decisions-needed", json={"decision": "[Which test tool]"}).json()["id"]
    c.patch(f"/api/decisions-needed/{d}", json={"status": "decided", "outcome": "[Tool A]", "process": "consult and decide"})
    c.post("/api/arch-decisions", json={"title": "[Use platform events]", "status": "accepted", "date": "2026-10-01", "decision": "[Yes]"})
    c.post("/api/releases", json={"name": "[R1]", "decision": "go", "decided_on": "2026-10-05"})
    c.post("/api/team-changes", json={"title": "[Daily standup]", "status": "adopted", "decided_on": "2026-10-10"})
    log = c.get("/api/decision-log").json()
    kinds = [x["kind"] for x in log["decisions"]]
    assert {"decision", "architecture", "release", "team change"} <= set(kinds)
    assert [x["title"] for x in c.get("/api/decision-log?kind=release").json()["decisions"]] == ["[R1]"]
    assert next(x for x in log["decisions"] if x["kind"] == "decision")["how"] == "consult and decide"


def test_sdlc_stage_links_raci_and_versions(c):
    rd = c.post("/api/raci-decisions", json={"decision": "[Promote to production]"}).json()
    st = c.post("/api/sdlc-stages", json={"name": "[Release]", "position": 1, "raci_ids": [rd["id"]]}).json()
    assert c.get("/api/raci").json()["decisions"][0]["stages"] == ["[Release]"]
    v = c.post("/api/sdlc/versions", json={"reason": "[Policy agreed]"}).json()
    assert v["reason"] == "[Policy agreed]" and "[Release]" in v["markdown"]
    assert c.post("/api/sdlc/versions", json={}).json().get("unchanged")
    c.post("/api/sdlc-policies", json={"title": "[Two approvals]", "body": "[Body]", "status": "agreed"})
    assert not c.post("/api/sdlc/versions", json={"reason": "[Second]"}).json().get("unchanged")
    assert len(c.get("/api/sdlc-versions").json()) == 2
