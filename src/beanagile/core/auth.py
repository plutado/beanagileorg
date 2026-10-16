"""Single-user sign-in: scrypt passwords, optional TOTP, hashed session and API tokens. Standard library only."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

MIN_PASSWORD_LENGTH = 12
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, dklen=32, **_SCRYPT)
    n, r, p = _SCRYPT["n"], _SCRYPT["r"], _SCRYPT["p"]
    return f"scrypt${n}${r}${p}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        salt, expected = base64.b64decode(salt_b64), base64.b64decode(dk_b64)
        dk = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk, expected)


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_code(secret: str, at: float | None = None, step: int = 30, digits: int = 6) -> str:
    key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    counter = int((time.time() if at is None else at) // step)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 10**digits
    return f"{value:0{digits}d}"


def verify_totp(secret: str, code: str, at: float | None = None, window: int = 1) -> bool:
    now = time.time() if at is None else at
    code = (code or "").strip()
    return any(hmac.compare_digest(totp_code(secret, now + i * 30), code) for i in range(-window, window + 1))


def totp_uri(secret: str, label: str, issuer: str) -> str:
    return f"otpauth://totp/{quote(issuer)}:{quote(label)}?secret={secret}&issuer={quote(issuer)}"


def new_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class LoginThrottle:
    """At most `limit` failed sign-ins per client within `period` seconds."""

    def __init__(self, limit: int = 5, period: int = 300) -> None:
        self.limit, self.period = limit, period
        self._failures: dict[str, list[float]] = {}

    def allowed(self, client: str) -> bool:
        cutoff = time.time() - self.period
        recent = [t for t in self._failures.get(client, []) if t > cutoff]
        self._failures[client] = recent
        return len(recent) < self.limit

    def fail(self, client: str) -> None:
        self._failures.setdefault(client, []).append(time.time())

    def reset(self, client: str) -> None:
        self._failures.pop(client, None)
