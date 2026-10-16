import base64

from beanagile.core import auth


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
