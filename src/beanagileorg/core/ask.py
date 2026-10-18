"""Ask: plain-language questions answered from the app's own data, by whichever model you connect.

The plumbing is model-agnostic:

- **Providers.** Any OpenAI-compatible chat API (Ollama, LM Studio, vLLM, Odysseus if it speaks that API, OpenAI
  itself) or Anthropic's Messages API. Local by default. The API key lives in a file in the data folder, readable
  only by you, never in the database and never sent back to the browser.
- **Context through tools, not a giant prompt.** The model gets a short description of the app and its sections,
  then calls tools: a full-text search over every record the viewer may see, read one record, list records of a
  kind, and whatever the app adds (Today, the weekly report). It pulls only what a question needs.
- **Privacy follows the viewer.** Tools run at the viewer's privacy level, so presentation mode only ever reaches
  presentable data. A cloud provider gets exportable data only, unless you explicitly allow more; every question
  sent to a cloud provider is recorded in the export log.
- **Answers cite their sources** as [entity:id], which the page turns into links.
"""

import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from .app import get_conn, get_viewer, require_full
from .export import log_export
from .privacy import Level, Viewer
from .records import REGISTRY

SETTINGS_KEY = "ask.settings"
SECRET_FILE = "ask-secret.json"
DEFAULTS = {"provider": "openai", "base_url": "http://127.0.0.1:11434/v1", "model": "qwen3.6:35b-a3b", "allow_private_cloud": False, "max_rounds": 6,
            "release_after": True}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_TOOL_CHARS = 6000


@dataclass
class AskApp:
    """What an app tells Ask about itself: its name, its sections, where records live, and any extra tools."""
    name: str
    sections: list[dict]  # {"path", "label", "purpose"}
    links: dict[str, str] = field(default_factory=dict)  # entity -> path template, "{id}" replaced
    extra_tools: list[dict] = field(default_factory=list)  # {"name", "description", "parameters", "run": fn(conn, viewer, args) -> str}


# ---- settings and secrets ----


def _settings(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (SETTINGS_KEY,)).fetchone()
    return {**DEFAULTS, **(json.loads(row["value"]) if row else {})}


def _secret_path(request: Request) -> Path:
    return Path(request.app.state.settings.data_dir) / SECRET_FILE


def _read_key(request: Request) -> str | None:
    try:
        return json.loads(_secret_path(request).read_text()).get("api_key") or None
    except (FileNotFoundError, ValueError):
        return None


def _write_key(request: Request, key: str | None) -> None:
    p = _secret_path(request)
    if not key:
        p.unlink(missing_ok=True)
        return
    p.write_text(json.dumps({"api_key": key}))
    os.chmod(p, 0o600)


def is_local(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower()
    return host in LOCAL_HOSTS or host.endswith(".localhost") or host.endswith(".local")


def effective_floor(viewer: Viewer, s: dict) -> Level:
    floor = viewer.floor
    cloud = s["provider"] == "anthropic" or not is_local(s["base_url"])
    if cloud and not s.get("allow_private_cloud"):
        floor = max(floor, Level.EXPORTABLE)
    return floor


# ---- the search index over everything visible ----

_INDEX_CACHE: dict = {}
_INDEX_LOCK = threading.Lock()


def _text_of(rec: dict) -> str:
    parts = []
    for k, v in rec.items():
        if k in ("id",) or v in (None, "", [], {}) or k.endswith("_id") or k.endswith("_ids"):
            continue
        if isinstance(v, (list, dict)):
            v = json.dumps(v, ensure_ascii=False)
        parts.append(f"{k}: {v}")
    return "\n".join(parts)


def _title_of(rec: dict) -> str:
    for k in ("title", "name", "concern", "question", "decision", "goal", "summary", "text", "topic", "practice", "commitment", "area", "date"):
        if rec.get(k):
            return str(rec[k])[:120]
    return f"#{rec['id']}"


def build_index(conn, floor: Level) -> sqlite3.Connection:
    """An in-memory full-text index of every record visible at this floor; rebuilt only when data changes."""
    stamp = conn.execute("SELECT COALESCE(MAX(id), 0) FROM change_log").fetchone()[0]
    cached = _INDEX_CACHE.get(int(floor))
    if cached and cached[0] == stamp and cached[2] == conn.execute("PRAGMA database_list").fetchone()["file"]:
        return cached[1]
    viewer = Viewer(floor=floor, source="ask")
    idx = sqlite3.connect(":memory:", check_same_thread=False)
    idx.execute("CREATE VIRTUAL TABLE docs USING fts5(entity UNINDEXED, rid UNINDEXED, title, body, tokenize='porter unicode61')")
    for entity, record in REGISTRY.items():
        try:
            rows = record.visible_all(record.fetch_all(conn), viewer)
        except sqlite3.Error:
            continue
        for r in rows:
            body = _text_of(r)
            if body:
                idx.execute("INSERT INTO docs VALUES (?, ?, ?, ?)", (entity, r["id"], _title_of(r), body))
    _INDEX_CACHE[int(floor)] = (stamp, idx, conn.execute("PRAGMA database_list").fetchone()["file"])
    return idx


def search(conn, floor: Level, query: str, limit: int = 8) -> list[dict]:
    with _INDEX_LOCK:
        return _search(conn, floor, query, limit)


def _search(conn, floor: Level, query: str, limit: int) -> list[dict]:
    idx = build_index(conn, floor)
    terms = [t for t in re.findall(r"[\w'-]+", query.lower()) if len(t) > 1]
    if not terms:
        return []
    match = " OR ".join(f'"{t}"' for t in terms[:12])
    rows = idx.execute("SELECT entity, rid, title, snippet(docs, 3, '', '', ' … ', 24) FROM docs WHERE docs MATCH ? ORDER BY bm25(docs) LIMIT ?",
                       (match, max(1, min(limit, 50)))).fetchall()
    return [{"entity": e, "id": i, "title": t, "snippet": s} for e, i, t, s in rows]


# ---- tools ----


def _base_tools(app: AskApp) -> list[dict]:
    kinds = ", ".join(sorted(REGISTRY))
    return [
        {"name": "search", "description": "Full-text search across every record in the app (people, dev-sync items, risks, decisions, plans, reports, notes and more). Use it first for almost any question.",
         "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Keywords"}, "limit": {"type": "integer", "description": "How many results, up to 20"}}, "required": ["query"]}},
        {"name": "get_record", "description": f"Read one record in full. entity is one of: {kinds}.",
         "parameters": {"type": "object", "properties": {"entity": {"type": "string"}, "id": {"type": "integer"}}, "required": ["entity", "id"]}},
        {"name": "list_records", "description": f"List the most recent records of one kind, optionally only those with a given status. entity is one of: {kinds}.",
         "parameters": {"type": "object", "properties": {"entity": {"type": "string"}, "status": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["entity"]}},
    ] + [{k: t[k] for k in ("name", "description", "parameters")} for t in app.extra_tools]


def _clip(obj) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s if len(s) <= MAX_TOOL_CHARS else s[:MAX_TOOL_CHARS] + " …(cut)"


def run_tool(app: AskApp, conn, floor: Level, name: str, args: dict) -> str:
    viewer = Viewer(floor=floor, source="ask")
    try:
        if name == "search":
            return _clip(search(conn, floor, str(args.get("query", "")), int(args.get("limit") or 8)))
        if name == "get_record":
            rec = REGISTRY.get(str(args.get("entity")))
            if not rec:
                return "Unknown entity."
            r = rec.fetch(conn, int(args.get("id") or 0))
            shown = rec.visible(r, viewer) if r else None
            return _clip(shown) if shown else "Not found, or not visible here."
        if name == "list_records":
            rec = REGISTRY.get(str(args.get("entity")))
            if not rec:
                return "Unknown entity."
            rows = rec.fetch_all(conn, "status = ?", (args["status"],)) if args.get("status") and "status" in rec.fields else rec.fetch_all(conn)
            return _clip(rec.visible_all(rows, viewer)[: max(1, min(int(args.get("limit") or 15), 40))])
        for t in app.extra_tools:
            if t["name"] == name:
                return _clip(t["run"](conn, viewer, args))
        return "Unknown tool."
    except (ValueError, TypeError, sqlite3.Error, HTTPException) as e:
        return f"The tool failed: {e}"


def system_prompt(app: AskApp, conn, floor: Level) -> str:
    counts = []
    for entity, record in REGISTRY.items():
        try:
            n = conn.execute(f"SELECT COUNT(*) FROM {record.table}").fetchone()[0]
        except sqlite3.Error:
            continue
        if n:
            counts.append(f"{entity} ({n})")
    sections = "\n".join(f"- {s['label']} ({s['path']}): {s['purpose']}" for s in app.sections)
    level = {Level.PRIVATE: "everything, including private notes", Level.PRESENTABLE: "only what may be shown on a shared screen",
             Level.EXPORTABLE: "only data marked as shareable"}[floor]
    return f"""You answer questions about the {app.name}, a private work app for an engineering manager. Answer only from the app's data, which you reach through tools.

Rules:
- Use tools before answering: search first, then read the records you need. Don't guess or invent facts, names, numbers or dates.
- If the data doesn't answer the question, say so plainly, and suggest where in the app it would be recorded.
- Be brief and specific: lead with the answer, then the few facts behind it. Plain words; short bullets when there are several items.
- Cite every record you rely on as [entity:id], for example [action_item:12] or [person:3].
- You can see {level}. Don't mention what you can't see.
- Today is {time.strftime('%Y-%m-%d')}.

Sections of the app:
{sections}

Records it holds, by kind: {', '.join(counts) or 'none yet'}."""


# ---- providers ----


def _post_json(url: str, headers: dict, body: dict, timeout: float = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise HTTPException(502, f"The model provider answered {e.code}: {e.read().decode()[:300]}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise HTTPException(502, f"Couldn't reach the model provider at {url}: {e}")


def _openai_turn(s: dict, key: str | None, messages: list, tools: list) -> tuple[str | None, list[dict], dict]:
    body = {"model": s["model"], "messages": messages, "tools": [{"type": "function", "function": t} for t in tools], "temperature": 0.2}
    out = _post_json(s["base_url"].rstrip("/") + "/chat/completions", {"Authorization": f"Bearer {key}"} if key else {}, body)
    msg = out["choices"][0]["message"]
    calls = [{"id": c.get("id") or f"call_{i}", "name": c["function"]["name"], "args": json.loads(c["function"].get("arguments") or "{}")}
             for i, c in enumerate(msg.get("tool_calls") or [])]
    return msg.get("content"), calls, msg


def _anthropic_turn(s: dict, key: str | None, system: str, messages: list, tools: list) -> tuple[str | None, list[dict], list]:
    body = {"model": s["model"], "max_tokens": 1500, "system": system, "messages": messages,
            "tools": [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools]}
    out = _post_json(s["base_url"].rstrip("/") + "/v1/messages", {"x-api-key": key or "", "anthropic-version": "2023-06-01"}, body)
    text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")
    calls = [{"id": b["id"], "name": b["name"], "args": b.get("input") or {}} for b in out.get("content", []) if b.get("type") == "tool_use"]
    return text or None, calls, out.get("content", [])


def release(s: dict) -> None:
    """On a shared machine, unload a local Ollama model right after use, so it doesn't hold ~20 GB while idle.

    Ollama's OpenAI-compatible API has no keep-alive setting, so this calls its native API with keep_alive 0, the
    same way a local image server can free memory before loading an image model. Silent if it isn't Ollama.
    """
    if not s.get("release_after") or s["provider"] == "anthropic" or not is_local(s["base_url"]):
        return
    u = urlparse(s["base_url"])
    native = f"{u.scheme}://{u.netloc}/api/generate"
    try:
        req = urllib.request.Request(native, data=json.dumps({"model": s["model"], "keep_alive": 0}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10).close()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        pass


def complete(s: dict, key: str | None, system: str, user: str, max_tokens: int = 1500) -> str:
    """One plain request and answer, no tools: for drafting text or structured JSON from facts the caller supplies."""
    if s["provider"] == "anthropic":
        out = _post_json(s["base_url"].rstrip("/") + "/v1/messages", {"x-api-key": key or "", "anthropic-version": "2023-06-01"},
                         {"model": s["model"], "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]})
        text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")
    else:
        out = _post_json(s["base_url"].rstrip("/") + "/chat/completions", {"Authorization": f"Bearer {key}"} if key else {},
                         {"model": s["model"], "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.3})
        text = out["choices"][0]["message"].get("content") or ""
    release(s)
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def settings_and_key(conn, request: Request) -> tuple[dict, str | None]:
    return _settings(conn), _read_key(request)


def ask(app: AskApp, conn, viewer: Viewer, s: dict, key: str | None, question: str, history: list[dict] | None = None) -> dict:
    floor = effective_floor(viewer, s)
    tools = _base_tools(app)
    system = system_prompt(app, conn, floor)
    used, cited = [], set()
    prior = [{"role": h["role"], "content": h["content"]} for h in (history or [])[-6:] if h.get("role") in ("user", "assistant") and h.get("content")]
    answer = None
    if s["provider"] == "anthropic":
        messages = prior + [{"role": "user", "content": question}]
        for _ in range(int(s.get("max_rounds") or 6)):
            text, calls, content = _anthropic_turn(s, key, system, messages, tools)
            if not calls:
                answer = text
                break
            messages.append({"role": "assistant", "content": content})
            results = []
            for c in calls:
                used.append({"tool": c["name"], "args": c["args"]})
                results.append({"type": "tool_result", "tool_use_id": c["id"], "content": run_tool(app, conn, floor, c["name"], c["args"])})
            messages.append({"role": "user", "content": results})
    else:
        messages = [{"role": "system", "content": system}] + prior + [{"role": "user", "content": question}]
        for _ in range(int(s.get("max_rounds") or 6)):
            text, calls, msg = _openai_turn(s, key, messages, tools)
            if not calls:
                answer = text
                break
            messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": msg.get("tool_calls")})
            for c in calls:
                used.append({"tool": c["name"], "args": c["args"]})
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": run_tool(app, conn, floor, c["name"], c["args"])})
    release(s)
    if answer is None:
        answer = "I couldn't finish within the allowed number of steps. Try a narrower question."
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()  # some local models think out loud
    for entity, rid in re.findall(r"\[([a-z_]+):(\d+)\]", answer):
        if entity in REGISTRY:
            cited.add((entity, int(rid)))
    citations = []
    for entity, rid in sorted(cited):
        rec = REGISTRY[entity].fetch(conn, rid)
        shown = REGISTRY[entity].visible(rec, Viewer(floor=floor, source="ask")) if rec else None
        if shown:
            path = app.links.get(entity, "")
            citations.append({"entity": entity, "id": rid, "title": _title_of(shown), "path": path.replace("{id}", str(rid)) if path else None})
    return {"answer": answer, "citations": citations, "tools_used": used, "floor": floor.name.lower(),
            "provider": s["provider"], "model": s["model"], "local": s["provider"] != "anthropic" and is_local(s["base_url"])}


# ---- routes ----


def build_router(app_info: Callable[[], AskApp]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/ask/settings")
    def get_settings(request: Request, viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        s = _settings(conn)
        return {**s, "has_key": bool(_read_key(request)), "local": s["provider"] != "anthropic" and is_local(s["base_url"])}

    @router.put("/api/ask/settings")
    def put_settings(request: Request, body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        s = _settings(conn)
        if body.get("provider") not in (None, "openai", "anthropic"):
            raise HTTPException(400, "The provider is openai (any OpenAI-compatible API, including Ollama) or anthropic.")
        for k in ("provider", "base_url", "model"):
            if body.get(k):
                s[k] = str(body[k]).strip()
        if "allow_private_cloud" in body:
            s["allow_private_cloud"] = bool(body["allow_private_cloud"])
        if "release_after" in body:
            s["release_after"] = bool(body["release_after"])
        if not s["base_url"].startswith(("http://", "https://")):
            raise HTTPException(400, "The address starts with http:// or https://.")
        if "api_key" in body:
            _write_key(request, (body.get("api_key") or "").strip() or None)
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (SETTINGS_KEY, json.dumps({k: s[k] for k in DEFAULTS})))
        return {**s, "has_key": bool(_read_key(request)), "local": s["provider"] != "anthropic" and is_local(s["base_url"])}

    @router.post("/api/ask")
    def post_ask(request: Request, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        q = (body.get("question") or "").strip()
        if not q:
            raise HTTPException(400, "Ask a question.")
        if len(q) > 2000:
            raise HTTPException(400, "Keep the question under 2,000 characters.")
        s = _settings(conn)
        result = ask(app_info(), conn, viewer, s, _read_key(request), q, body.get("history"))
        if not result["local"]:
            log_export(conn, "ask:cloud", f"Question to {s['model']}", [{"question": q, "floor": result["floor"]}], viewer.source)
        return result

    @router.get("/api/ask/search")
    def get_search(q: str, limit: int = 10, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        """The same search the model uses: a plain keyword search over everything you can see, no model needed.
        Each result carries the path to open it, where the app has one."""
        links = app_info().links
        out = search(conn, viewer.floor, q, max(1, min(limit, 50)))
        for r in out:
            path = links.get(r["entity"], "")
            r["path"] = path.replace("{id}", str(r["id"])) if path else None
        return out

    return router
