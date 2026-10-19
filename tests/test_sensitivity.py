"""Judgments about people: what never leaves, and the second look before wording that might be one does."""

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.core.records import Record
from beanagileorg.core.sensitivity import JUDGMENT_TABLES, PERSON_NEVER, check_record, scan_text
from beanagileorg.toolkit import models, packs, people_crm
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"


def make(tmp_path, name):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path / name)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


def test_scan_skips_everyday_engineering_words():
    assert scan_text("Pipeline blocker: raise a risk on system health, then fire the deploy job") == {}
    found = scan_text("[Person 1] is untrustworthy and a flight risk", ["[Person 1]"])
    assert found == {"judgment": ["untrustworthy"], "employment": ["flight risk"], "name": ["[Person 1]"]}
    assert scan_text("Started a PIP")["employment"] == ["pip"]


def test_levels():
    assert check_record({"title": "[Person 2] seems resistant"}, ["[Person 2]"])["level"] == "warn"
    assert check_record({"title": "Vendor is resistant"})["level"] == "note"  # no person in sight
    assert check_record({"next_step": "Pair with [Person 2]"}, ["[Person 2]"])["level"] == "note"
    assert check_record({"impact": "Out on sick leave"})["level"] == "warn"
    assert check_record({"title": "Upgrade the integration runtime"}) is None


def test_judgment_records_and_fields_never_travel():
    tables = {v.table for v in vars(models).values() if isinstance(v, Record)}
    assert JUDGMENT_TABLES <= tables, "every listed table exists"
    assert not {k.record.table for k in packs.KINDS.values()} & JUDGMENT_TABLES
    assert PERSON_NEVER <= set(models.people.fields)
    assert not set(people_crm.ROSTER_SHAREABLE + people_crm.ROSTER_PRIVATE) & PERSON_NEVER
    assert "support_notes" not in people_crm.ROSTER_PRIVATE


def test_pack_needs_a_second_look_and_the_importer_opts_in(tmp_path):
    a, b = make(tmp_path, "a"), make(tmp_path, "b")
    who = a.post("/api/people", json={"name": "[Person 1]"}).json()["id"]
    bad = a.post("/api/risks", json={"title": "[Person 1] can't be trusted with releases", "owner_id": who}).json()["id"]
    fine = a.post("/api/risks", json={"title": "[Risk 2]", "impact": "[Impact]"}).json()["id"]
    pol = a.post("/api/risks", json={"title": "[Risk 3]", "surprise_area": "politics"}).json()["id"]
    sel = {"risks": {"ids": [bad, fine, pol], "fields": ["impact", "surprise_area"], "links": {"owner_id": "name"}}}
    checks = a.post("/api/packs/review", json={"selection": sel}).json()["checks"]
    by = {c["id"]: c for c in checks}
    assert by[bad]["level"] == "warn" and fine not in by and by[pol]["level"] == "note"
    held = a.post("/api/packs/export", json={"selection": sel})
    assert held.status_code == 409
    pack = a.post("/api/packs/export", json={"selection": sel, "acknowledged": True}).json()
    assert "acknowledged" in a.get("/api/exports").json()[0]["title"]
    rows = {r["label"]: r for r in b.post("/api/packs/inspect", json={"pack": pack}).json()["kinds"][0]["records"]}
    flagged = rows["[Person 1] can't be trusted with releases"]
    assert flagged["check"]["level"] == "warn" and flagged["default"] == "skip"
    assert rows["[Risk 2]"]["check"] is None and rows["[Risk 2]"]["default"] == "add"
    # Leaving the flagged record out needs no acknowledgment.
    assert a.post("/api/packs/export", json={"selection": {"risks": {**sel["risks"], "ids": [fine]}}}).status_code == 200


def test_roster_never_carries_support_notes(tmp_path):
    a = make(tmp_path, "a")
    a.post("/api/people", json={"name": "[Person 1]", "active": True, "support_notes": "[Private support]", "stance": "skeptic", "motivations": "[Motivations]"})
    r = a.post("/api/people/roster/export", json={"scope": "everyone", "include_private": True, "acknowledged": True}).json()
    p = next(x for x in r["people"] if x["name"] == "[Person 1]")
    assert not {"support_notes", "stance", "motivations"} & set(p)
