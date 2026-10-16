import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from beanagileorg.core import auth, privacy
from beanagileorg.core.app import create_app, get_viewer
from beanagileorg.core.config import Settings
from beanagileorg.core.db import CORE_MIGRATIONS, Database, migrate
from beanagileorg.core.privacy import Level, filter_records

PASSWORD = "[placeholder-password]"

privacy.register("note", {"title": Level.EXPORTABLE, "detail": Level.PRESENTABLE, "secret": Level.PRIVATE})

router = APIRouter()


@router.get("/api/notes")
def notes(viewer=Depends(get_viewer)):
    rows = [
        {"id": 1, "title": "[Placeholder title]", "detail": "[Placeholder detail]", "secret": "[Placeholder secret]"},
        {"id": 2, "title": "[Placeholder title 2]", "detail": "[Placeholder]", "secret": "[Placeholder]", "privacy_ceiling": 0},
    ]
    return filter_records("note", rows, viewer.floor)


@pytest.fixture
def client(tmp_path):
    app = create_app(
        Settings(app="testapp", title="Test app", port=0, data_dir=tmp_path),
        nav=[{"path": "/home", "label": "Home"}],
        routers=[router],
    )
    return TestClient(app, follow_redirects=False)


def setup_user(client):
    res = client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    assert res.status_code == 303
    return res


def test_first_visit_goes_to_setup(client):
    assert client.get("/").headers["location"] == "/setup"
    assert client.get("/api/session").status_code == 401
    assert client.get("/api/health").json()["ok"] is True


def test_setup_rejects_short_password(client):
    res = client.post("/setup", data={"password": "short", "confirm": "short"})
    assert "at least 12" in res.text


def test_setup_signs_in_and_only_runs_once(client):
    setup_user(client)
    assert client.get("/api/session").json()["presentation"] is False
    assert client.get("/setup").headers["location"] == "/login"


def test_presentation_mode_filters_on_the_server(client):
    setup_user(client)
    full = client.get("/api/notes").json()
    assert len(full) == 2 and full[0]["secret"] == "[Placeholder secret]"

    client.post("/api/session/presentation", json={"on": True})
    shown = client.get("/api/notes").json()
    assert shown == [{"id": 1, "title": "[Placeholder title]", "detail": "[Placeholder detail]"}]
    assert client.get("/api/tokens").status_code == 403

    client.post("/api/session/presentation", json={"on": False})
    assert len(client.get("/api/notes").json()) == 2


def test_tokens_read_only_what_their_scope_allows(client):
    setup_user(client)
    export = client.post("/api/tokens", json={"name": "export", "scopes": ["export:read"]}).json()["token"]
    present = client.post("/api/tokens", json={"name": "present", "scopes": ["present:read"]}).json()["token"]

    anon = TestClient(client.app, follow_redirects=False)
    as_export = anon.get("/api/notes", headers={"Authorization": f"Bearer {export}"}).json()
    assert as_export == [{"id": 1, "title": "[Placeholder title]"}]
    as_present = anon.get("/api/notes", headers={"Authorization": f"Bearer {present}"}).json()
    assert as_present == [{"id": 1, "title": "[Placeholder title]", "detail": "[Placeholder detail]"}]
    assert anon.get("/api/tokens", headers={"Authorization": f"Bearer {export}"}).status_code == 403
    assert anon.get("/api/notes", headers={"Authorization": "Bearer ba_wrong"}).status_code == 401


def test_token_validation_and_revocation(client):
    setup_user(client)
    assert client.post("/api/tokens", json={"name": "x", "scopes": ["admin"]}).status_code == 400
    assert client.post("/api/tokens", json={"name": "x", "scopes": []}).status_code == 400
    token = client.post("/api/tokens", json={"name": "x", "scopes": ["export:read"]}).json()["token"]
    assert client.post("/api/tokens", json={"name": "x", "scopes": ["export:read"]}).status_code == 400
    token_id = client.get("/api/tokens").json()[0]["id"]
    assert client.delete(f"/api/tokens/{token_id}").status_code == 204
    anon = TestClient(client.app, follow_redirects=False)
    assert anon.get("/api/notes", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_login_throttle(client):
    setup_user(client)
    client.post("/logout")
    for _ in range(5):
        assert client.post("/login", data={"password": "wrong-password"}).status_code == 401
    assert client.post("/login", data={"password": PASSWORD}).status_code == 429


def test_totp_enrolment_and_login(client):
    setup_user(client)
    secret = client.post("/api/auth/totp/start").json()["secret"]
    assert client.post("/api/auth/totp/confirm", json={"code": "000000" if auth.totp_code(secret) != "000000" else "111111"}).status_code == 400
    assert client.post("/api/auth/totp/confirm", json={"code": auth.totp_code(secret)}).status_code == 200
    client.post("/logout")
    assert client.post("/login", data={"password": PASSWORD}).status_code == 401
    assert client.post("/login", data={"password": PASSWORD, "code": auth.totp_code(secret)}).status_code == 303


def test_password_change(client):
    setup_user(client)
    new = "[another-placeholder-password]"
    assert client.post("/api/auth/password", json={"current": "wrong", "new": new}).status_code == 400
    assert client.post("/api/auth/password", json={"current": PASSWORD, "new": new}).status_code == 200
    client.post("/logout")
    assert client.post("/login", data={"password": new}).status_code == 303


def test_migrations_are_idempotent(tmp_path):
    db = Database(tmp_path / "m.db")
    with db.session() as conn:
        assert migrate(conn, "core", CORE_MIGRATIONS) == [1]
        assert migrate(conn, "core", CORE_MIGRATIONS) == []


def test_real_apps_build(tmp_path):
    from beanagileorg.comms.app import build as build_comms
    from beanagileorg.toolkit.app import build as build_toolkit

    for build, name in ((build_toolkit, "toolkit"), (build_comms, "comms")):
        app = build(Settings(app=name, title=name, port=0, data_dir=tmp_path / name))
        c = TestClient(app, follow_redirects=False)
        assert c.get("/api/health").json()["app"] == name
        assert c.get("/static/app.js").status_code == 200
        assert c.get("/core-static/shell.js").status_code == 200


def test_static_files_are_revalidated(tmp_path):
    from fastapi.testclient import TestClient

    from beanagileorg.core.config import Settings
    from beanagileorg.toolkit.app import build

    c = TestClient(build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path)))
    assert c.get("/core-static/shell.js").headers["cache-control"] == "no-cache"
    assert c.get("/static/app.js").headers["cache-control"] == "no-cache"


def test_unknown_hosts_are_refused(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from beanagileorg.core.config import Settings
    from beanagileorg.toolkit.app import build

    monkeypatch.setenv("BEANAGILEORG_ALLOWED_HOSTS", "placeholder-host.test")
    app = build(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path))
    for host, ok in (("127.0.0.1:8801", True), ("localhost", True), ("toolkit.beanagile.org", True), ("placeholder-host.test", True),
                     ("comms.beanagile.org", False), ("evil.example", False)):
        status = TestClient(app, base_url=f"http://{host}").get("/health").status_code
        assert (status == 200) == ok, host
