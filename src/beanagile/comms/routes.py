"""Comms studio endpoints for decks, slides, media files, placeholder content and the present page."""

import html
import shutil
from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from beanagile.core.app import get_conn, get_viewer
from beanagile.core.privacy import Viewer

from . import mediafiles, models

router = APIRouter()
STATIC = Path(__file__).parent / "static"


def require_write(viewer: Viewer) -> None:
    if not viewer.has_scope("full"):
        raise HTTPException(403, "This needs the full scope.")


def media_dir(request: Request) -> Path:
    path = request.app.state.settings.data_dir / "media"
    path.mkdir(parents=True, exist_ok=True)
    return path


def deck_or_404(conn, deck_id: int) -> dict:
    deck = models.decks.fetch(conn, deck_id)
    if deck is None:
        raise HTTPException(404, "No deck with that id.")
    return deck


def deck_slides(conn, deck_id: int) -> list[dict]:
    return models.slides.fetch_all(conn, "deck_id = ?", (deck_id,))


def _renumber(conn, slides: list[dict], source: str) -> None:
    for position, slide in enumerate(slides):
        if slide["position"] != position:
            models.slides.update(conn, slide["id"], {"position": position}, source)


# ---- decks and slides ----


@router.get("/api/decks/{deck_id}/full")
def deck_full(deck_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    deck = models.decks.visible(deck_or_404(conn, deck_id), viewer)
    if deck is None:
        raise HTTPException(404, "No deck with that id.")
    return {
        "deck": deck,
        "slides": models.slides.visible_all(deck_slides(conn, deck_id), viewer),
        "media": models.media.visible_all(models.media.fetch_all(conn), viewer),
    }


@router.post("/api/decks/{deck_id}/slides", status_code=201)
def add_slide(deck_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    deck_or_404(conn, deck_id)
    slides = deck_slides(conn, deck_id)
    after = body.pop("after_id", None)
    index = next((i + 1 for i, s in enumerate(slides) if s["id"] == after), len(slides))
    created = models.slides.create(conn, {**body, "deck_id": deck_id, "position": index}, viewer.source)
    slides.insert(index, created)
    _renumber(conn, slides, viewer.source)
    return models.slides.fetch(conn, created["id"])


@router.post("/api/slides/{slide_id}/duplicate", status_code=201)
def duplicate_slide(slide_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    original = models.slides.fetch(conn, slide_id)
    if original is None:
        raise HTTPException(404, "No slide with that id.")
    copy = {k: original[k] for k in ("layout", "content", "notes", "transition", "hidden")}
    return add_slide(original["deck_id"], {**copy, "after_id": slide_id}, viewer, conn)


@router.post("/api/decks/{deck_id}/reorder")
def reorder(deck_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    deck_or_404(conn, deck_id)
    slides = {s["id"]: s for s in deck_slides(conn, deck_id)}
    order = body.get("slide_ids")
    if not isinstance(order, list) or sorted(order) != sorted(slides):
        raise HTTPException(400, "slide_ids must list every slide in the deck exactly once.")
    _renumber(conn, [slides[i] for i in order], viewer.source)
    return models.slides.visible_all(deck_slides(conn, deck_id), viewer)


# ---- media ----


@router.post("/api/media/upload", status_code=201)
def upload_media(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(""),
    source: str = Form("mine"),
    license_ref: str = Form(""),
    viewer: Viewer = Depends(get_viewer),
    conn=Depends(get_conn),
):
    require_write(viewer)
    try:
        kind, mime, ext = mediafiles.classify(file.filename)
    except mediafiles.MediaError as exc:
        raise HTTPException(400, str(exc)) from exc
    folder = media_dir(request)
    tmp = folder / f".upload-{id(file)}{ext}"
    with tmp.open("wb") as out:
        shutil.copyfileobj(file.file, out, length=1024 * 1024)
    size = tmp.stat().st_size
    try:
        if size == 0 or size > mediafiles.MAX_BYTES:
            raise mediafiles.MediaError("The file is empty or larger than 2 GB.")
        mediafiles.check_content(kind, tmp)
    except mediafiles.MediaError as exc:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, str(exc)) from exc
    return _store(conn, tmp, folder, kind, mime, ext, size, name or Path(file.filename).stem, source, license_ref, viewer)


def _store(conn, tmp: Path, folder: Path, kind, mime, ext, size, name, source, license_ref, viewer) -> dict:
    rec = models.media.create(
        conn,
        {"kind": kind, "name": name[:200], "file_name": "pending", "mime": mime, "size_bytes": size,
         "source": source, "license_ref": license_ref or None},
        viewer.source,
    )
    final = f"{rec['id']}{ext}"
    tmp.rename(folder / final)
    return models.media.update(conn, rec["id"], {"file_name": final}, viewer.source)


@router.get("/api/media/{media_id}/file")
def media_file(media_id: int, request: Request, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    rec = models.media.fetch(conn, media_id)
    if rec is None or models.media.visible(rec, viewer) is None:
        raise HTTPException(404, "No media with that id.")
    path = media_dir(request) / Path(rec["file_name"]).name
    if not path.is_file():
        raise HTTPException(404, "The file for this media is missing.")
    return FileResponse(
        path,
        media_type=rec["mime"],
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600"},
    )


@router.post("/api/media")
def create_media_without_file():
    raise HTTPException(400, "Add media by uploading a file to /api/media/upload.")


@router.delete("/api/media/{media_id}", status_code=204)
def delete_media(media_id: int, request: Request, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rec = models.media.fetch(conn, media_id)
    if rec is None:
        raise HTTPException(404, "No media with that id.")
    (media_dir(request) / Path(rec["file_name"]).name).unlink(missing_ok=True)
    models.media.delete(conn, media_id, viewer.source)


# ---- placeholder deck ----


@router.post("/api/comms/seed-placeholders", status_code=201)
def seed(request: Request, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    folder = media_dir(request)

    def make(kind, mime, ext, name, data: bytes) -> dict:
        tmp = folder / f".seed-{name}{ext}"
        tmp.write_bytes(data)
        return _store(conn, tmp, folder, kind, mime, ext, len(data), name, "placeholder", "", viewer)

    tone = make("audio", "audio/wav", ".wav", "[Placeholder tone]", mediafiles.placeholder_tone())
    anim = make("lottie", "application/json", ".json", "[Placeholder animation]", mediafiles.placeholder_lottie())
    deck = models.decks.create(conn, {"title": "[Placeholder deck title]"}, viewer.source)
    slides = [
        ("title", {"heading": "[Placeholder deck title]", "subheading": "[Placeholder subtitle]"}),
        ("section", {"heading": "[Placeholder section]"}),
        ("big-number", {"heading": "[Placeholder headline: the point of this slide]", "number": "[00%]", "caption": "[Placeholder caption]"}),
        ("bullets", {"heading": "[Placeholder headline]", "items": ["[Placeholder point 1]", "[Placeholder point 2]", "[Placeholder point 3]"], "step": True}),
        ("lottie", {"heading": "[Placeholder headline]", "media_id": anim["id"], "play": "loop", "speed": 1, "caption": "[Placeholder caption]"}),
        ("comparison", {"heading": "[Placeholder headline]", "left_title": "[Placeholder before]", "left_items": ["[Placeholder]", "[Placeholder]"],
                        "right_title": "[Placeholder after]", "right_items": ["[Placeholder]", "[Placeholder]"]}),
        ("quote", {"quote": "[Placeholder quote]", "attribution": "[Placeholder name]"}),
        ("audio", {"heading": "[Placeholder headline]", "media_id": tone["id"], "play": "click", "caption": "[Placeholder caption]"}),
        ("video", {"heading": "[Placeholder headline]", "play": "click"}),
        ("image", {"heading": "[Placeholder headline]", "caption": "[Placeholder caption]"}),
        ("closing", {"heading": "[Placeholder closing line]", "subheading": "[Placeholder next step]"}),
    ]
    for position, (layout, content) in enumerate(slides):
        models.slides.create(
            conn,
            {"deck_id": deck["id"], "position": position, "layout": layout, "content": content,
             "notes": f"[Placeholder speaker notes for slide {position + 1}]"},
            viewer.source,
        )
    return {"deck_id": deck["id"], "slides": len(slides)}


# ---- present page ----


@router.get("/present/{deck_id}", response_class=HTMLResponse)
def present_page(deck_id: int):
    page = (STATIC / "present.html").read_text()
    return HTMLResponse(page.replace("{{DECK_ID}}", html.escape(str(deck_id))))
