"""Comms studio version 1 endpoints: messages and their states, checks, versions, exports, calendar, sent log."""

import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagile.core.app import get_conn, get_viewer, require_full
from beanagile.core.dates import next_occurrence
from beanagile.core.db import transaction
from beanagile.core.export import log_export
from beanagile.core.privacy import Viewer

from . import checks, models
from .starter import load_starter_kit

router = APIRouter()

TRANSITIONS = {
    "draft": {"in review", "ready", "archived"},
    "in review": {"draft", "ready", "archived"},
    "ready": {"draft", "in review", "sent", "archived"},
    "sent": {"archived"},
    "archived": {"draft"},
}
HORIZON_DAYS = 21


def require_write(viewer: Viewer) -> None:
    if not viewer.has_scope("full"):
        raise HTTPException(403, "This needs the full scope.")


def message_or_404(conn, message_id: int) -> dict:
    rec = models.messages.fetch(conn, message_id)
    if rec is None:
        raise HTTPException(404, "No message with that id.")
    return rec


def save_version(conn, message_id: int, body: str | None, source: str) -> None:
    conn.execute(
        "INSERT INTO message_versions (message_id, body, source) VALUES (?, ?, ?)", (message_id, body or "", source)
    )


def glossary(conn) -> list[dict]:
    return models.glossary.fetch_all(conn)


# ---- messages ----


@router.post("/api/messages", status_code=201)
def create_message(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    data = {k: v for k, v in body.items() if k not in ("state", "sent_at")}
    template_id = data.get("template_id")
    if template_id:
        tpl = models.templates.fetch(conn, template_id)
        if tpl is None:
            raise HTTPException(400, "That template doesn't exist.")
        data.setdefault("title", tpl["name"])
        data.setdefault("type", tpl["type"])
        data.setdefault("body", tpl["body"])
        data.setdefault("audience_ids", tpl["audience_ids"])
        data.setdefault("channel_id", tpl["channel_id"])
    rec = models.messages.create(conn, data, viewer.source)
    save_version(conn, rec["id"], rec["body"], viewer.source)
    return rec


@router.patch("/api/messages/{message_id}")
def update_message(message_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if {"state", "sent_at"} & set(body):
        raise HTTPException(400, "Change state with /api/messages/{id}/state.")
    old = message_or_404(conn, message_id)
    if old["state"] in ("sent", "archived"):
        raise HTTPException(400, "Sent messages can't be edited. Duplicate it to write a new version.")
    rec = models.messages.update(conn, message_id, body, viewer.source)
    if "body" in body and (rec["body"] or "") != (old["body"] or ""):
        save_version(conn, message_id, rec["body"], viewer.source)
    return rec


@router.post("/api/messages/{message_id}/duplicate", status_code=201)
def duplicate_message(message_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    old = message_or_404(conn, message_id)
    copy = {k: old[k] for k in ("type", "body", "audience_ids", "channel_id", "template_id")}
    return create_message({**copy, "title": f"{old['title']} (copy)"}, viewer, conn)


@router.get("/api/messages/{message_id}/checks")
def message_checks(message_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rec = message_or_404(conn, message_id)
    return checks.run_checks(rec["body"], glossary(conn))


@router.post("/api/check")
def check_text(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Check unsaved text, so the editor can show results while typing."""
    return checks.run_checks(str(body.get("body") or ""), glossary(conn))


@router.get("/api/messages/{message_id}/versions")
def versions(message_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    message_or_404(conn, message_id)
    rows = conn.execute(
        "SELECT id, body, saved_at, source FROM message_versions WHERE message_id = ? ORDER BY id DESC LIMIT 50",
        (message_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/api/messages/{message_id}/state")
def change_state(message_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rec = message_or_404(conn, message_id)
    target = body.get("state")
    if target not in TRANSITIONS.get(rec["state"], set()):
        raise HTTPException(400, f"A {rec['state']} message can't move to {target!r}.")
    results = checks.run_checks(rec["body"], glossary(conn))
    if target in ("ready", "sent") and checks.blocking(results):
        raise HTTPException(400, f"Fix these first: {', '.join(checks.blocking(results))}.")
    changes: dict = {"state": target}
    if target == "sent":
        channel_id = body.get("channel_id") or rec["channel_id"]
        channel = models.channels.fetch(conn, channel_id) if channel_id else None
        if channel is None:
            raise HTTPException(400, "Choose the channel it went out on.")
        names = [a["name"] for a in models.audiences.fetch_all(conn) if a["id"] in rec["audience_ids"]]
        sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """INSERT INTO sent_log (message_id, title, type, sent_at, channel, audiences, body, body_sha256, checks, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id, rec["title"], rec["type"], sent_at, channel["name"], json.dumps(names), rec["body"] or "",
                hashlib.sha256((rec["body"] or "").encode()).hexdigest(), json.dumps(results), viewer.source,
            ),
        )
        changes.update({"sent_at": sent_at, "channel_id": channel["id"]})
    # State changes go around the PATCH guard on purpose, through the records layer so they're logged.
    return models.messages.update(conn, message_id, changes, viewer.source)


@router.post("/api/messages/{message_id}/export")
def export_message(message_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rec = message_or_404(conn, message_id)
    fmt = body.get("format", "text")
    if fmt not in ("text", "markdown", "print"):
        raise HTTPException(400, "format must be text, markdown or print.")
    log_export(conn, f"message:{fmt}", rec["title"], [{"id": rec["id"], "body": rec["body"]}], viewer.source)
    return {"title": rec["title"], "body": rec["body"] or ""}


@router.get("/api/sent-log")
def sent_log(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    rows = conn.execute(
        "SELECT id, message_id, title, type, sent_at, channel, audiences, body_sha256, checks, source FROM sent_log ORDER BY id DESC LIMIT 200"
    ).fetchall()
    out = []
    for r in rows:
        rec = dict(r)
        rec["audiences"] = json.loads(rec["audiences"] or "[]")
        rec["warnings"] = sum(1 for c in json.loads(rec.pop("checks") or "[]") if c["result"] != "pass")
        out.append(rec)
    return out


# ---- comms calendar ----


def ensure_due(conn) -> None:
    """Create due items for every active cadence from its first due date up to the horizon."""
    horizon = date.today() + timedelta(days=HORIZON_DAYS)
    for c in models.cadences.fetch_all(conn, "active = 1 AND next_due IS NOT NULL"):
        d = date.fromisoformat(c["next_due"])
        while d is not None and d <= horizon:
            conn.execute("INSERT OR IGNORE INTO comms_due (cadence_id, due) VALUES (?, ?)", (c["id"], d.isoformat()))
            d = next_occurrence(d, c["rhythm"])


def due_items(conn, start: str, end: str) -> list[dict]:
    rows = conn.execute(
        """SELECT d.id, d.due, d.message_id, c.id AS cadence_id, c.title, c.message_type, c.lead_days, c.template_id,
                  m.state AS message_state, m.title AS message_title
           FROM comms_due d JOIN cadences c ON c.id = d.cadence_id LEFT JOIN messages m ON m.id = d.message_id
           WHERE d.due BETWEEN ? AND ? ORDER BY d.due, c.title""",
        (start, end),
    ).fetchall()
    today = date.today().isoformat()
    out = []
    for r in rows:
        rec = dict(r)
        if rec["message_state"] in ("sent", "archived"):
            rec["status"] = "sent"
        elif rec["due"] < today:
            rec["status"] = "overdue"
        elif rec["message_id"]:
            rec["status"] = "drafted"
        else:
            start_on = (date.fromisoformat(rec["due"]) - timedelta(days=rec["lead_days"] or 0)).isoformat()
            rec["status"] = "start drafting" if start_on <= today else "upcoming"
        out.append(rec)
    return out


@router.get("/api/this-week")
def this_week(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    ensure_due(conn)
    today = date.today()
    due = due_items(conn, (today - timedelta(days=30)).isoformat(), (today + timedelta(days=14)).isoformat())
    due = [d for d in due if d["status"] != "sent" or d["due"] >= (today - timedelta(days=7)).isoformat()]
    drafts = models.messages.visible_all(models.messages.fetch_all(conn, "state IN ('draft', 'in review', 'ready')"), viewer)
    sent = models.messages.visible_all(models.messages.fetch_all(conn, "state = 'sent'"), viewer)[:5]
    return {"today": today.isoformat(), "due": due if viewer.has_scope("full") else [], "drafts": drafts, "recently_sent": sent}


@router.get("/api/comms-due")
def calendar(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    ensure_due(conn)
    today = date.today()
    return due_items(conn, (today - timedelta(days=30)).isoformat(), (today + timedelta(days=HORIZON_DAYS)).isoformat())


@router.post("/api/comms-due/{due_id}/draft", status_code=201)
def draft_from_due(due_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    row = conn.execute(
        "SELECT d.id, d.due, d.message_id, c.title, c.message_type, c.template_id FROM comms_due d JOIN cadences c ON c.id = d.cadence_id WHERE d.id = ?",
        (due_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "No due item with that id.")
    if row["message_id"] and models.messages.fetch(conn, row["message_id"]):
        return models.messages.fetch(conn, row["message_id"])
    data = {"title": f"{row['title']}: {row['due']}", "type": row["message_type"]}
    if row["template_id"] and models.templates.fetch(conn, row["template_id"]):
        data["template_id"] = row["template_id"]
    rec = create_message(data, viewer, conn)
    with transaction(conn):
        conn.execute("UPDATE comms_due SET message_id = ? WHERE id = ?", (rec["id"], due_id))
    return rec


# ---- plain language and starter kit ----


@router.get("/api/plain-language/jargon")
def jargon():
    return [{"term": k, "plain": v} for k, v in sorted(checks.JARGON.items(), key=lambda kv: kv[0].lower())]


@router.post("/api/comms/starter-kit", status_code=201)
def starter_kit(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]:
        raise HTTPException(409, "The starter kit only loads when there are no templates yet.")
    return load_starter_kit(conn, viewer.source)


# ---- connection to the toolkit (export-only token) ----

TOOLKIT_URL_KEY = "comms.toolkit_url"
TOOLKIT_TOKEN_KEY = "comms.toolkit_token"
DEFAULT_TOOLKIT_URL = "http://127.0.0.1:8801"


def _get_setting(conn, key):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def fetch_toolkit(url: str, token: str, path: str, timeout: float = 5.0) -> dict:
    request = urllib.request.Request(f"{url.rstrip('/')}{path}", headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


@router.get("/api/connections")
def get_connections(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    return {"toolkit_url": _get_setting(conn, TOOLKIT_URL_KEY) or DEFAULT_TOOLKIT_URL, "token_set": bool(_get_setting(conn, TOOLKIT_TOKEN_KEY))}


@router.put("/api/connections")
def put_connections(body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
    url = (body.get("toolkit_url") or DEFAULT_TOOLKIT_URL).strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "The toolkit address must start with http:// or https://.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (TOOLKIT_URL_KEY, url))
    token = (body.get("toolkit_token") or "").strip()
    if body.get("clear_token"):
        conn.execute("DELETE FROM settings WHERE key = ?", (TOOLKIT_TOKEN_KEY,))
    elif token:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (TOOLKIT_TOKEN_KEY, token))
    return get_connections(viewer, conn)


@router.get("/api/toolkit/status-draft")
def toolkit_status_draft(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Pull the toolkit's weekly status draft. The toolkit token should have the export:read scope only."""
    require_write(viewer)
    url = _get_setting(conn, TOOLKIT_URL_KEY) or DEFAULT_TOOLKIT_URL
    token = _get_setting(conn, TOOLKIT_TOKEN_KEY)
    if not token:
        raise HTTPException(400, "Connect the toolkit first: add an export-only token under Connections.")
    try:
        return fetch_toolkit(url, token, "/api/status/draft")
    except urllib.error.HTTPError as exc:
        raise HTTPException(502, "The toolkit turned the token down. Create a new export:read token in the toolkit's Settings." if exc.code in (401, 403) else f"The toolkit answered with an error ({exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HTTPException(502, f"Couldn't reach the toolkit at {url}. Is it running?") from exc
