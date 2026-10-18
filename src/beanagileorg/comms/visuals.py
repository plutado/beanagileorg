"""Images and infographics for messages and decks.

Images come from an image service with an OpenAI-style API: by default a local FLUX.2 Klein server on
port 8710. Generated images go into the media library marked "generated", with the prompt, model and
seed that made them.

Infographics are not generated as pictures, because image models garble words and invent numbers. An infographic
is a small piece of data (a template and its items) that the page draws as a crisp graphic, so every word and
number is exactly what was entered or drafted from the toolkit's facts. The local model can draft one from a
request and those facts; the draft is checked against the template before it's saved. A PNG export goes into the
media library for slides and email.
"""

import base64
import json
import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.ask import _post_json, complete, effective_floor, settings_and_key
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import _store, media_dir, require_write

router = APIRouter()
IMAGES_KEY = "comms.images"
IMAGE_DEFAULTS = {"base_url": "http://127.0.0.1:8710/v1", "model": "flux2-klein-4b",
                  "style": "clean, modern editorial illustration, flat shapes, soft natural light, muted palette with one accent colour, no text, no logos"}
SIZES = {"slide": (1344, 768), "square": (1024, 1024), "portrait": (768, 1152), "thumbnail": (1280, 720)}
LIMITS = {"stats": (2, 4), "bars": (2, 8), "timeline": (2, 7), "steps": (2, 6), "compare": (0, 0), "progress": (0, 0)}


def _get(conn, key, default):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return {**default, **(json.loads(row["value"]) if row else {})}


# ---- images ----


@router.get("/api/images/settings")
def get_image_settings(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {**_get(conn, IMAGES_KEY, IMAGE_DEFAULTS), "sizes": list(SIZES)}


@router.put("/api/images/settings")
def put_image_settings(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    s = _get(conn, IMAGES_KEY, IMAGE_DEFAULTS)
    for k in ("base_url", "model", "style"):
        if body.get(k) is not None:
            s[k] = str(body[k]).strip()
    if not s["base_url"].startswith(("http://", "https://")):
        raise HTTPException(400, "The address starts with http:// or https://.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (IMAGES_KEY, json.dumps(s)))
    return s


@router.post("/api/media/generate", status_code=201)
def generate_image(request: Request, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Make an image from a prompt and file it in the media library as generated."""
    require_write(viewer)
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "Describe the image.")
    s = _get(conn, IMAGES_KEY, IMAGE_DEFAULTS)
    w, h = SIZES.get(body.get("size") or "slide", SIZES["slide"])
    full = f"{prompt}. {s['style']}" if body.get("use_style", True) and s.get("style") else prompt
    req = {"prompt": full, "width": w, "height": h, "model": body.get("model") or s["model"], "n": 1}
    if body.get("seed"):
        req["seed"] = int(body["seed"])
    out = _post_json(s["base_url"].rstrip("/") + "/images/generations", {}, req, timeout=600)
    try:
        data = base64.b64decode(out["data"][0]["b64_json"])
    except (KeyError, IndexError, ValueError):
        raise HTTPException(502, "The image service didn't return an image.")
    folder = media_dir(request)
    tmp = folder / f".gen-{date.today().isoformat()}-{len(data)}.png"
    tmp.write_bytes(data)
    name = (body.get("name") or prompt)[:80]
    rec = _store(conn, tmp, folder, "image", "image/png", ".png", len(data), name, "generated", "", viewer)
    details = {"prompt": prompt, "full_prompt": full, "model": req["model"], "size": [w, h], "seed": out["data"][0].get("seed") or req.get("seed"), "service": s["base_url"]}
    return models.media.update(conn, rec["id"], {"details": details}, viewer.source)


# ---- infographics ----


def _clean_text(v, n=120):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def validate_spec(spec: dict) -> dict:
    """Check an infographic against its template and trim it to what the page can draw."""
    if not isinstance(spec, dict) or spec.get("template") not in LIMITS:
        raise HTTPException(400, f"Pick a template: {', '.join(LIMITS)}.")
    t = spec["template"]
    out = {"template": t, "title": _clean_text(spec.get("title"), 90) or "[Placeholder title]", "subtitle": _clean_text(spec.get("subtitle"), 140),
           "note": _clean_text(spec.get("note"), 160)}
    lo, hi = LIMITS[t]
    items = spec.get("items") or []
    if t in ("stats", "bars", "timeline", "steps"):
        if not isinstance(items, list) or not lo <= len(items) <= hi:
            raise HTTPException(400, f"A {t} infographic has {lo} to {hi} items.")
        if t == "stats":
            out["items"] = [{"value": _clean_text(i.get("value"), 12), "label": _clean_text(i.get("label"), 60)} for i in items]
        elif t == "bars":
            try:
                out["items"] = [{"label": _clean_text(i.get("label"), 40), "value": float(i.get("value"))} for i in items]
            except (TypeError, ValueError):
                raise HTTPException(400, "Every bar needs a number.")
            out["unit"] = _clean_text(spec.get("unit"), 16)
        elif t == "timeline":
            out["items"] = [{"date": _clean_text(i.get("date"), 20), "label": _clean_text(i.get("label"), 60)} for i in items]
        else:
            out["items"] = [{"label": _clean_text(i.get("label"), 40), "detail": _clean_text(i.get("detail"), 90)} for i in items]
    elif t == "compare":
        side = lambda s: {"heading": _clean_text((s or {}).get("heading"), 30), "points": [_clean_text(p, 70) for p in ((s or {}).get("points") or [])][:5]}
        out["left"], out["right"] = side(spec.get("left")), side(spec.get("right"))
        if not out["left"]["points"] or not out["right"]["points"]:
            raise HTTPException(400, "Both sides of a comparison need at least one point.")
    else:
        try:
            done, total = float(spec.get("done")), float(spec.get("total"))
        except (TypeError, ValueError):
            raise HTTPException(400, "Progress needs numbers for done and total.")
        if total <= 0 or done < 0:
            raise HTTPException(400, "Total must be above zero.")
        out.update(done=done, total=total, label=_clean_text(spec.get("label"), 40), unit=_clean_text(spec.get("unit"), 16))
    return out


SCHEMA_HELP = """Templates and their JSON:
- stats: {"template":"stats","title","subtitle","items":[{"value":"8 of 10","label":"stories finished"}, ...2-4],"note"}
- bars: {"template":"bars","title","subtitle","unit":"points","items":[{"label":"Sprint 12","value":21}, ...2-8],"note"}
- timeline: {"template":"timeline","title","subtitle","items":[{"date":"Week 1","label":"Listening tour"}, ...2-7],"note"}
- steps: {"template":"steps","title","subtitle","items":[{"label":"Refine","detail":"stories ready before planning"}, ...2-6],"note"}
- compare: {"template":"compare","title","subtitle","left":{"heading":"Today","points":["..."]},"right":{"heading":"Proposed","points":["..."]},"note"}
- progress: {"template":"progress","title","subtitle","done":18,"total":24,"unit":"points","label":"Sprint 14","note"}"""


@router.post("/api/infographics/draft")
def draft_infographic(request: Request, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Draft an infographic with the configured model, from a request and, optionally, the toolkit's facts."""
    require_write(viewer)
    ask_text = (body.get("request") or "").strip()
    if not ask_text:
        raise HTTPException(400, "Say what the infographic should show.")
    facts = ""
    source = body.get("facts") or "none"
    if source != "none":
        from .messaging import _pull

        path = {"weekly": "/api/reports/weekly", "sprint": "/api/reports/sprint", "status": "/api/status/draft", "plans": "/api/plans/outline"}.get(source)
        if not path:
            raise HTTPException(400, "Facts come from weekly, sprint, status, plans or none.")
        pulled = _pull(conn, path)
        facts = pulled.get("markdown") or json.dumps(pulled)[:6000]
    s, key = settings_and_key(conn, request)
    system = ("You design one simple infographic for a leadership update. Reply with ONLY one JSON object, no prose, no code fence.\n" + SCHEMA_HELP +
              "\nRules: pick the template that fits the request. Use only numbers and names that appear in the facts; if a number isn't there, write "
              "[Placeholder] for it. Short labels, plain words, no jargon. The title states the point, for example 'We finished 8 of 10 stories', not 'Sprint results'.")
    user = f"Request: {ask_text}\n\nFacts:\n{facts or '(none given)'}"
    raw = complete(s, key, system, user)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise HTTPException(502, "The model didn't return an infographic. Try rephrasing the request.")
    try:
        spec = json.loads(m.group(0))
    except ValueError:
        raise HTTPException(502, "The model's draft wasn't valid. Try again.")
    return {"spec": validate_spec(spec), "facts_used": source, "model": s["model"]}


@router.post("/api/infographics/save", status_code=201)
def save_infographic(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    spec = validate_spec(body.get("spec") or {})
    if body.get("id"):
        if not models.infographics.fetch(conn, int(body["id"])):
            raise HTTPException(404, "No such infographic.")
        return models.infographics.update(conn, int(body["id"]), {"title": spec["title"], "template": spec["template"], "spec": spec}, viewer.source)
    return models.infographics.create(conn, {"title": spec["title"], "template": spec["template"], "spec": spec}, viewer.source)


@router.post("/api/infographics/{info_id}/png", status_code=201)
def export_png(info_id: int, request: Request, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Store the PNG the page drew, in the media library, and link it to the infographic."""
    require_write(viewer)
    info = models.infographics.fetch(conn, info_id)
    if not info:
        raise HTTPException(404, "No such infographic.")
    data_url = body.get("png") or ""
    if not data_url.startswith("data:image/png;base64,"):
        raise HTTPException(400, "Send the PNG as a data URL.")
    data = base64.b64decode(data_url.split(",", 1)[1])
    if not data.startswith(b"\x89PNG") or len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "That isn't a PNG image, or it's too large.")
    folder = media_dir(request)
    tmp = folder / f".info-{info_id}.png"
    tmp.write_bytes(data)
    rec = _store(conn, tmp, folder, "image", "image/png", ".png", len(data), f"Infographic: {info['title']}"[:200], "generated", "", viewer)
    models.media.update(conn, rec["id"], {"details": {"infographic_id": info_id, "template": info["template"]}}, viewer.source)
    models.infographics.update(conn, info_id, {"media_id": rec["id"]}, viewer.source)
    return {"media_id": rec["id"]}
