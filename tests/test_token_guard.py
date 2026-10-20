"""API tokens never carry judgments about people, whatever their scope, unless granted judgments:read."""

import re

import pytest
from fastapi.testclient import TestClient

from beanagileorg.core.config import Settings
from beanagileorg.core.records import REGISTRY
from beanagileorg.core.sensitivity import JUDGMENT_TABLES, PERSON_NEVER
from beanagileorg.toolkit.app import build

PASSWORD = "[placeholder-password]"
MARK = "[JMARK]"


def _value(name, f, pid):
    if f.choices:
        return f.choices[0]
    return {"text": MARK, "date": "2026-10-01", "int": pid if name.endswith("_id") else 1, "number": 1, "bool": True,
            "list": [MARK], "ids": [pid], "json": {}, "key": "ABC-1", "keys": []}[f.type]


@pytest.fixture
def seeded(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    pid = c.post("/api/people", json={"name": "[Person 1]", "active": True, "role": "[Role]"}).json()["id"]
    people = REGISTRY["person"] if "person" in REGISTRY else next(r for r in REGISTRY.values() if r.table == "people")
    c.patch(f"/api/people/{pid}", json={f: _value(f, people.fields[f], pid) for f in PERSON_NEVER})
    made = []
    for rec in REGISTRY.values():
        if rec.table not in JUDGMENT_TABLES:
            continue
        body = {n: _value(n, f, pid) for n, f in rec.fields.items()}
        r = c.post(rec.path, json=body)
        if r.status_code in (200, 201):
            made.append(rec.table)
    return c, pid, made


def _get_paths(app, pid):
    for path, ops in app.openapi()["paths"].items():
        if "get" in ops and path.startswith("/api/"):
            yield re.sub(r"\{[^}]+\}", str(pid), path)


def test_tokens_never_receive_judgments(seeded):
    c, pid, made = seeded
    assert len(made) >= len(JUDGMENT_TABLES) - 4, f"could only seed {sorted(made)}"
    me = c.get(f"/api/people/{pid}").json()
    assert MARK in str(me)  # signed in directly, you see your own notes
    token = c.post("/api/tokens", json={"name": "[Full token]", "scopes": ["full"]}).json()["token"]
    c.cookies.clear()
    leaks = []
    for path in sorted(set(_get_paths(c.app, pid))):
        r = c.get(path, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200 and MARK in r.text:
            leaks.append(path)
    for path, ops in c.app.openapi()["paths"].items():  # exports compose text, so they're checked too
        if "post" in ops and path.startswith("/api/") and ("export" in path or "draft" in path or "summary" in path):
            r = c.post(re.sub(r"\{[^}]+\}", str(pid), path), json={}, headers={"Authorization": f"Bearer {token}"})
            if r.status_code in (200, 201) and MARK in r.text:
                leaks.append(f"POST {path}")
    assert leaks == [], "\n".join(leaks)


def test_judgments_scope_lifts_the_guard(seeded):
    c, pid, _ = seeded
    token = c.post("/api/tokens", json={"name": "[Trusted token]", "scopes": ["full", "judgments:read"]}).json()["token"]
    c.cookies.clear()
    assert MARK in c.get(f"/api/people/{pid}", headers={"Authorization": f"Bearer {token}"}).text


def test_never_share_stays_in(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    keep = c.post("/api/risks", json={"title": "[Sensitive risk]", "level": "high"}).json()["id"]
    c.post("/api/risks", json={"title": "[Ordinary risk]", "level": "low"})
    assert c.patch(f"/api/risks/{keep}", json={"never_share": True}).json()["never_share"]
    assert {r["title"] for r in c.get("/api/risks").json()} == {"[Sensitive risk]", "[Ordinary risk]"}  # you still see it
    kinds = {k["key"]: k for k in c.get("/api/packs/kinds").json()["kinds"]}
    assert kinds["risks"]["never_shared"] == 1 and [r["label"] for r in kinds["risks"]["records"]] == ["[Ordinary risk]"]
    assert "never_share" not in kinds["risks"]["private"] + kinds["risks"]["shareable"]
    assert c.post("/api/packs/review", json={"selection": {"risks": {"ids": [keep], "fields": []}}}).status_code == 400
    for path in ("/api/reports/weekly", "/api/status/draft"):  # what goes to leadership leaves it out
        text = c.get(path).text
        assert "[Sensitive risk]" not in text and "[Ordinary risk]" in text, path
    token = c.post("/api/tokens", json={"name": "[Hub]", "scopes": ["full"]}).json()["token"]
    c.post("/api/session/presentation", json={"on": True})
    assert "[Sensitive risk]" not in c.get("/api/risks").text and "[Ordinary risk]" in c.get("/api/risks").text
    c.post("/api/session/presentation", json={"on": False})
    c.cookies.clear()
    assert "[Sensitive risk]" not in c.get("/api/risks", headers={"Authorization": f"Bearer {token}"}).text


def test_never_share_on_changes_debt_and_team_changes(tmp_path):
    c = TestClient(build(Settings(app="toolkit", title="Toolkit", port=0, data_dir=tmp_path)), follow_redirects=False)
    c.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    made = {}
    for path, body in [("/api/change-requests", {"title": "[Marked request]", "source": "stakeholder", "requested_on": "2026-10-19"}),
                       ("/api/tech-debt", {"title": "[Marked debt]"}), ("/api/team-changes", {"title": "[Marked change]"})]:
        rid = c.post(path, json=body).json()["id"]
        assert c.patch(f"{path}/{rid}", json={"never_share": True}).json()["never_share"]
        made[path] = rid
    rel = c.post("/api/releases", json={"name": "[Release 1]", "change_request_ids": [made["/api/change-requests"]]}).json()["id"]
    assert "[Marked request]" not in c.get(f"/api/releases/{rel}/notes").json()["markdown"]
    assert "[Marked debt]" not in c.post("/api/debt/summary/export", json={}).text
    token = c.post("/api/tokens", json={"name": "[Hub]", "scopes": ["full"]}).json()["token"]
    c.post("/api/session/presentation", json={"on": True})
    for path in made:
        assert "[Marked" not in c.get(path).text, path
    c.post("/api/session/presentation", json={"on": False})
    c.cookies.clear()
    for path in made:
        assert "[Marked" not in c.get(path, headers={"Authorization": f"Bearer {token}"}).text, path
