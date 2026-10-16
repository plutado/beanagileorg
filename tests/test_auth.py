import base64

from fastapi.testclient import TestClient

from beanagile.core import auth
from beanagile.core.config import Settings


def test_password_round_trip():
    stored = auth.hash_password("[placeholder-password]")
    assert auth.verify_password("[placeholder-password]", stored)
    assert not auth.verify_password("wrong-password", stored)


def test_password_hashes_are_salted():
    assert auth.hash_password("same") != auth.hash_password("same")


def test_verify_rejects_garbage():
    assert not auth.verify_password("x", "not-a-hash")


def test_totp_matches_rfc6238_vector():
    # RFC 6238 test secret "12345678901234567890", T=59s: 8-digit code 94287082, so 6 digits are 287082.
    secret = base64.b32encode(b"12345678901234567890").decode()
    assert auth.totp_code(secret, at=59) == "287082"


def test_totp_window():
    secret = auth.new_totp_secret()
    code = auth.totp_code(secret, at=1_000_000)
    assert auth.verify_totp(secret, code, at=1_000_000 + 30)
    assert not auth.verify_totp(secret, code, at=1_000_000 + 120)


def test_throttle():
    t = auth.LoginThrottle(limit=2, period=60)
    assert t.allowed("a")
    t.fail("a")
    t.fail("a")
    assert not t.allowed("a")
    assert t.allowed("b")
    t.reset("a")
    assert t.allowed("a")


def test_each_app_has_its_own_session_cookie(tmp_path):
    """Both apps run on 127.0.0.1, and browsers share cookies across ports."""
    from beanagile.comms.app import build as build_comms
    from beanagile.toolkit.app import build as build_toolkit

    toolkit = TestClient(build_toolkit(Settings(app="toolkit", title="T", port=0, data_dir=tmp_path / "t")), follow_redirects=False)
    comms = TestClient(build_comms(Settings(app="comms", title="C", port=0, data_dir=tmp_path / "c")), follow_redirects=False)
    a = toolkit.post("/setup", data={"password": "[placeholder-password]", "confirm": "[placeholder-password]"})
    b = comms.post("/setup", data={"password": "[placeholder-password]", "confirm": "[placeholder-password]"})
    assert "ba_session_toolkit" in a.cookies and "ba_session_comms" in b.cookies
