"""Timed, read-only share links: one page, for one named person, for a limited time.

A link shows exactly one thing an app has registered (a "kind"), rendered fresh each time it's opened, so a change
upstream (such as consent withdrawn) takes effect at once. Each link expires, can be limited to a number of views,
needs an access code sent another way, locks after repeated wrong codes, and can be revoked. Creating and opening a
link are recorded in the export log. The recipient never signs in and never reaches anything else in the app.

The page only opens where the recipient can reach this machine, for example over a private network; add that
address to BEANAGILEORG_ALLOWED_HOSTS.
"""

import hmac
import html
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from .auth import hash_token, new_token
from .export import log_export

MAX_HOURS = 24 * 7
MAX_FAILURES = 5
HOURS_CHOICES = (1, 24, 72, 168)


class ShareGone(Exception):
    """Raised by a renderer when what the link shows is no longer available (for example, consent was withdrawn)."""


# kind -> renderer(conn, ref_id) -> {"title": str, "markdown": str}
RENDERERS: dict[str, Callable] = {}


def register(kind: str, renderer: Callable) -> None:
    RENDERERS[kind] = renderer


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def _code() -> str:
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no look-alikes
    raw = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def create_link(conn, kind: str, ref_id: int | None, recipient: str, hours: int = 24, max_views: int | None = 5, source: str = "me") -> dict:
    """Make a link. The token and code are returned once and stored only as hashes."""
    if kind not in RENDERERS:
        raise ValueError("Unknown kind of share.")
    recipient = " ".join((recipient or "").split())[:120]
    if not recipient:
        raise ValueError("Name who the link is for.")
    if hours not in HOURS_CHOICES:
        raise ValueError("Choose how long the link lasts: 1 hour, 1 day, 3 days or 7 days.")
    if max_views is not None and not 1 <= int(max_views) <= 50:
        raise ValueError("Allow between 1 and 50 views, or leave it unlimited until it expires.")
    token, code = new_token("bsh"), _code()
    expires = _now() + timedelta(hours=hours)
    cur = conn.execute(
        "INSERT INTO share_links (token_hash, kind, ref_id, recipient, code_hash, expires_at, max_views) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hash_token(token), kind, ref_id, recipient, hash_token(code.replace("-", "")), _stamp(expires), max_views),
    )
    log_export(conn, "share:create", f"Share link for {recipient} ({kind}), {hours} h", [{"kind": kind, "ref_id": ref_id, "recipient": recipient}], source)
    return {"id": cur.lastrowid, "token": token, "code": code, "expires_at": _stamp(expires), "recipient": recipient, "max_views": max_views}


def status_of(row) -> str:
    if row["revoked_at"]:
        return "locked" if row["failures"] >= MAX_FAILURES else "revoked"
    if row["expires_at"] <= _stamp(_now()):
        return "expired"
    if row["max_views"] is not None and row["views"] >= row["max_views"]:
        return "used up"
    return "active"


def list_links(conn, kind: str, ref_id: int | None) -> list[dict]:
    rows = conn.execute("SELECT * FROM share_links WHERE kind = ? AND ref_id IS ? ORDER BY id DESC", (kind, ref_id)).fetchall()
    return [{"id": r["id"], "recipient": r["recipient"], "created_at": r["created_at"], "expires_at": r["expires_at"], "views": r["views"],
             "max_views": r["max_views"], "last_viewed_at": r["last_viewed_at"], "status": status_of(r)} for r in rows]


def revoke(conn, link_id: int, kind: str, ref_id: int | None) -> bool:
    cur = conn.execute("UPDATE share_links SET revoked_at = ? WHERE id = ? AND kind = ? AND ref_id IS ? AND revoked_at IS NULL",
                       (_stamp(_now()), link_id, kind, ref_id))
    return cur.rowcount > 0


# ---- the page the recipient sees ----

_INLINE = [(re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>")]


def markdown_to_html(md: str) -> str:
    """Headings, bullets and paragraphs with bold: all a summary needs. Everything is escaped first."""
    out, items = [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for line in (md or "").splitlines():
        text = html.escape(line.strip())
        for pat, rep in _INLINE:
            text = pat.sub(rep, text)
        if not text:
            flush()
        elif line.startswith("## "):
            flush()
            out.append(f"<h2>{text[3:]}</h2>")
        elif line.startswith("# "):
            flush()
            out.append(f"<h1>{text[2:]}</h1>")
        elif line.lstrip().startswith("- "):
            items.append(text[2:])
        else:
            flush()
            out.append(f"<p>{text}</p>")
    flush()
    return "\n".join(out)


_STYLE = """body{font:16px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;color:#1c1c1a;background:#fbfaf7}
h1{font-size:1.5rem}h2{font-size:1.1rem;margin-top:1.6em}.note{color:#6b6a65;font-size:.9rem}form{margin-top:24px}
input{font:inherit;padding:8px 10px;border:1px solid #ccc;border-radius:6px;letter-spacing:.1em;text-transform:uppercase}
button{font:inherit;padding:8px 14px;border:0;border-radius:6px;background:#4f46e5;color:#fff;margin-left:8px}.err{color:#b42318}
@media (prefers-color-scheme: dark){body{background:#151513;color:#e9e7e1}.note{color:#a3a19a}input{background:#22221f;color:#e9e7e1;border-color:#444}}"""


def _page(body: str, status: int = 200) -> HTMLResponse:
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Shared with you</title><style>{_STYLE}</style></head><body>{body}</body></html>"""
    r = HTMLResponse(doc, status_code=status)
    r.headers["Cache-Control"] = "no-store"
    r.headers["X-Robots-Tag"] = "noindex, nofollow"
    r.headers["Referrer-Policy"] = "no-referrer"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"
    return r


def _gone(msg: str = "This link isn't available. It may have expired or been withdrawn. Ask the person who sent it for a new one.") -> HTMLResponse:
    return _page(f"<h1>Not available</h1><p>{html.escape(msg)}</p>", 410)


def _code_form(error: str = "") -> HTMLResponse:
    return _page(f"""<h1>Shared with you</h1><p>Enter the access code you were sent separately.</p>
<form method="post"><input name="code" autocomplete="one-time-code" required autofocus aria-label="Access code" placeholder="XXXX-XXXX"><button type="submit">Open</button></form>
{f'<p class="err">{html.escape(error)}</p>' if error else ''}<p class="note">A private, read-only page. Opening it is recorded.</p>""")


def build_router(get_db: Callable) -> APIRouter:
    router = APIRouter()

    def _row(conn, token: str):
        return conn.execute("SELECT * FROM share_links WHERE token_hash = ?", (hash_token(token),)).fetchone()

    @router.get("/shared/{token}", include_in_schema=False)
    def open_form(token: str):
        with get_db().session() as conn:
            row = _row(conn, token)
            if not row or status_of(row) != "active":
                return _gone()
        return _code_form()

    @router.post("/shared/{token}", include_in_schema=False)
    def open_page(token: str, request: Request, code: str = Form("")):
        with get_db().session() as conn:
            row = _row(conn, token)
            if not row or status_of(row) != "active":
                return _gone()
            given = hash_token(re.sub(r"[^A-Za-z0-9]", "", code).upper())
            if not hmac.compare_digest(given, row["code_hash"]):
                failures = row["failures"] + 1
                conn.execute("UPDATE share_links SET failures = ?, revoked_at = CASE WHEN ? >= ? THEN ? ELSE revoked_at END WHERE id = ?",
                             (failures, failures, MAX_FAILURES, _stamp(_now()), row["id"]))
                if failures >= MAX_FAILURES:
                    return _gone("Too many wrong codes, so this link is now locked. Ask the person who sent it for a new one.")
                return _code_form("That code didn't match.")
            try:
                shown = RENDERERS[row["kind"]](conn, row["ref_id"])
            except ShareGone as exc:
                return _gone(str(exc)) if str(exc) else _gone()
            conn.execute("UPDATE share_links SET views = views + 1, last_viewed_at = ? WHERE id = ?", (_stamp(_now()), row["id"]))
            log_export(conn, "share:view", f"{shown['title']}, opened by {row['recipient']}", [{"link": row["id"]}], f"share:{row['recipient']}")
            left = None if row["max_views"] is None else row["max_views"] - row["views"] - 1
        note = f"Shared with {html.escape(row['recipient'])}. Read-only; this page expires {html.escape(row['expires_at'])} UTC" + (
            f", and can be opened {left} more time{'s' if left != 1 else ''}." if left is not None else ".")
        return _page(markdown_to_html(shown["markdown"]) + f'<p class="note">{note} Please don\'t forward it.</p>')

    return router
