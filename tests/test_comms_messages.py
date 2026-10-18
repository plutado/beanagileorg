import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from beanagileorg.comms import app as app_module, checks
from beanagileorg.comms.app import build
from beanagileorg.core.config import Settings

PASSWORD = "[placeholder-password]"
CLEAN = "We shipped the first clean release this week.\n\n- [x] Release notes posted"


@pytest.fixture
def client(tmp_path):
    c = TestClient(build(Settings(app="comms", title="Comms", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    return c


@pytest.fixture
def kit(client):
    client.post("/api/comms/starter-kit")
    return client


# ---- checks ----


def by_check(results):
    return {r["check"]: r for r in results}


def test_placeholders_block():
    res = by_check(checks.run_checks("Intro.\n\n[Placeholder: one line] and [Placeholder name]"))
    assert res["placeholders"]["result"] == "fail" and res["placeholders"]["blocks"]
    assert checks.blocking(list(res.values())) == ["Placeholders left"]


def test_plain_language_flags_jargon_and_glossary_terms():
    res = by_check(checks.run_checks("We will leverage synergy. The SOQL limits bite.", [{"term": "SOQL", "plain": "the query language"}]))
    findings = " ".join(res["plain_language"]["findings"])
    assert '"leverage" → use' in findings and '"synergy"' in findings and '"SOQL" → the query language' in findings
    # Uppercase acronyms match case-sensitively, so ordinary words aren't flagged.
    assert by_check(checks.run_checks("We're on track for an eta of Friday."))["plain_language"]["result"] == "pass"


def test_long_sentences_and_summary_first():
    long_sentence = " ".join(["word"] * 30) + "."
    res = by_check(checks.run_checks(long_sentence))
    assert res["long_sentences"]["result"] == "warn"
    assert res["summary_first"]["result"] == "pass"
    long_opening = " ".join(["word"] * 60)
    assert by_check(checks.run_checks(long_opening))["summary_first"]["result"] == "warn"
    assert by_check(checks.run_checks("## Only a heading\n| a | b |"))["summary_first"]["findings"] == ["There's no opening summary."]


def test_tables_and_headings_are_not_prose():
    body = "Short opener.\n\n| Milestone | Date | Status | Owner | Note | Extra | More | Columns |\n| --- | --- |"
    assert by_check(checks.run_checks(body))["long_sentences"]["result"] == "pass"


# ---- starter kit and calendar ----


def test_starter_kit_loads_once(kit):
    assert len(kit.get("/api/templates").json()) == 10
    assert len(kit.get("/api/audiences").json()) == 6
    assert all(c["name"].startswith("[Placeholder") for c in kit.get("/api/channels").json())
    assert kit.post("/api/comms/starter-kit").status_code == 409


def test_this_week_reports_the_real_starter_template_count(client):
    offered = client.get("/api/this-week").json()["starter_templates"]
    loaded = client.post("/api/comms/starter-kit").json()["templates"]
    assert offered == loaded == len(client.get("/api/templates").json())
    js = (Path(app_module.__file__).parent / "static" / "app.js").read_text()
    assert "${week.starter_templates} templates" in js
    assert not re.search(r"starter kit: (one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve) templates", js)


def test_due_items_and_drafting(kit):
    due = kit.get("/api/this-week").json()["due"]
    assert {d["title"] for d in due} == {"Weekly note to leadership", "Weekly status"}
    first = due[0]
    msg = kit.post(f"/api/comms-due/{first['id']}/draft").json()
    assert msg["title"].startswith(first["title"]) and msg["state"] == "draft" and "[Placeholder" in msg["body"]
    again = kit.post(f"/api/comms-due/{first['id']}/draft").json()
    assert again["id"] == msg["id"]
    status = {d["id"]: d["status"] for d in kit.get("/api/comms-due").json()}
    assert status[first["id"]] == "drafted"


# ---- message lifecycle ----


def test_lifecycle_versions_and_sent_log(kit):
    tpl = kit.get("/api/templates").json()[0]
    msg = kit.post("/api/messages", json={"template_id": tpl["id"]}).json()
    assert msg["audience_ids"] == tpl["audience_ids"]
    assert kit.post(f"/api/messages/{msg['id']}/state", json={"state": "ready"}).status_code == 400
    assert kit.patch(f"/api/messages/{msg['id']}", json={"state": "sent"}).status_code == 400
    kit.patch(f"/api/messages/{msg['id']}", json={"body": CLEAN})
    assert len(kit.get(f"/api/messages/{msg['id']}/versions").json()) == 2
    assert kit.post(f"/api/messages/{msg['id']}/state", json={"state": "sent"}).status_code == 400
    assert kit.post(f"/api/messages/{msg['id']}/state", json={"state": "ready"}).json()["state"] == "ready"
    channel = kit.get("/api/channels").json()[0]
    sent = kit.post(f"/api/messages/{msg['id']}/state", json={"state": "sent", "channel_id": channel["id"]}).json()
    assert sent["state"] == "sent" and sent["sent_at"]
    log = kit.get("/api/sent-log").json()[0]
    assert log["channel"] == channel["name"] and log["audiences"]
    assert kit.patch(f"/api/messages/{msg['id']}", json={"body": "changed"}).status_code == 400
    copy = kit.post(f"/api/messages/{msg['id']}/duplicate").json()
    assert copy["state"] == "draft" and copy["body"] == CLEAN


def test_send_needs_a_channel(client):
    msg = client.post("/api/messages", json={"title": "[Placeholder title]", "body": CLEAN}).json()
    client.post(f"/api/messages/{msg['id']}/state", json={"state": "ready"})
    assert client.post(f"/api/messages/{msg['id']}/state", json={"state": "sent"}).status_code == 400


def test_drafts_private_sent_shareable(kit):
    draft = kit.post("/api/messages", json={"title": "[Draft]", "body": CLEAN}).json()
    sent = kit.post("/api/messages", json={"title": "[Sent]", "body": CLEAN}).json()
    kit.post(f"/api/messages/{sent['id']}/state", json={"state": "ready"})
    ch = kit.get("/api/channels").json()[0]["id"]
    kit.post(f"/api/messages/{sent['id']}/state", json={"state": "sent", "channel_id": ch})
    token = kit.post("/api/tokens", json={"name": "export", "scopes": ["export:read"]}).json()["token"]
    kit.post("/api/session/presentation", json={"on": True})
    assert [m["title"] for m in kit.get("/api/messages").json()] == ["[Sent]"]
    assert kit.get(f"/api/messages/{draft['id']}").status_code == 404
    anon = TestClient(kit.app, follow_redirects=False)
    anon.headers["Authorization"] = f"Bearer {token}"
    assert [m["title"] for m in anon.get("/api/messages").json()] == ["[Sent]"]
    assert anon.post("/api/messages", json={"title": "x"}).status_code == 403


def test_export_is_logged(kit):
    msg = kit.post("/api/messages", json={"title": "[Placeholder]", "body": CLEAN}).json()
    assert kit.post(f"/api/messages/{msg['id']}/export", json={"format": "markdown"}).json()["body"] == CLEAN
    assert kit.post(f"/api/messages/{msg['id']}/export", json={"format": "docx"}).status_code == 400
    assert kit.get("/api/exports").json()[0]["kind"] == "message:markdown"


def test_glossary_feeds_checks(client):
    client.post("/api/glossary", json={"term": "CDC", "plain": "change notifications"})
    res = client.post("/api/check", json={"body": "Turn on CDC."}).json()
    assert any("CDC" in f for r in res for f in r["findings"])
