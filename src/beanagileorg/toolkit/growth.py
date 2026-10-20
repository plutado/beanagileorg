"""Growth paths, the new member's own onboarding page, and their feedback on onboarding."""

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from beanagileorg.core import shares
from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

STARTER_LEVELS = [
    ("[Track: engineering]", "[Level 1]", "[Placeholder: what's expected at this level]", "[Placeholder: what moves someone to the next level]"),
    ("[Track: engineering]", "[Level 2]", "[Placeholder: what's expected at this level]", "[Placeholder: what moves someone to the next level]"),
    ("[Track: engineering]", "[Level 3]", "[Placeholder: what's expected at this level]", "[Placeholder: what moves someone to the next level]"),
    ("[Track: engineering]", "[Level 4]", "[Placeholder: what's expected at this level]", ""),
]


@router.post("/api/growth-paths/starter", status_code=201)
def starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A placeholder track to replace with the organization's real levels once you know them."""
    require_write(viewer)
    if conn.execute("SELECT COUNT(*) FROM growth_levels").fetchone()[0]:
        raise HTTPException(409, "There are already levels. Edit those instead.")
    for pos, (track, level, exp, up) in enumerate(STARTER_LEVELS):
        models.growth_levels.create(conn, {"track": track, "level": level, "position": pos, "expectations": exp, "move_up": up or None}, viewer.source)
    return {"levels": len(STARTER_LEVELS)}


@router.get("/api/growth-paths")
def growth_paths(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Each track's levels, and (privately) where each of your reports sits on them."""
    from .people_crm import me_id

    levels = models.growth_levels.visible_all(models.growth_levels.fetch_all(conn), viewer)
    tracks = {}
    for lv in levels:
        tracks.setdefault(lv["track"], []).append({**lv, "people": []})
    out = {"tracks": [{"track": t, "levels": ls} for t, ls in tracks.items()]}
    if viewer.floor == Level.PRIVATE and not viewer.guarded:
        me = me_id(conn)
        reports = [p for p in models.people.fetch_all(conn, "active = 1") if me and p.get("manager_id") == me]
        by_id = {lv["id"]: lv for t in out["tracks"] for lv in t["levels"]}
        for p in reports:
            if p.get("growth_level_id") in by_id:
                by_id[p["growth_level_id"]]["people"].append({"id": p["id"], "name": p["name"]})
        out["reports"] = [{"id": p["id"], "name": p["name"], "growth_level_id": p.get("growth_level_id")} for p in reports]
    return out


# ---- the new member's own page: a timed link to their checklist ----

SHARE_KIND = "onboarding:checklist"


def _render_checklist(conn, ob_id: int) -> dict:
    from .onboarding import build_checklist

    if not models.onboardings.fetch(conn, ob_id):
        raise shares.ShareGone("This onboarding no longer exists.")
    return build_checklist(conn, ob_id, Viewer(floor=Level.PRESENTABLE, source="share"))


shares.register(SHARE_KIND, _render_checklist)


@router.post("/api/onboardings/{ob_id}/links", status_code=201)
def make_link(ob_id: int, request: Request, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A read-only page of their checklist the new member can open themselves, without access to anything else."""
    from .self_manage import _local, _share_base

    require_write(viewer)
    ob = models.onboardings.fetch(conn, ob_id)
    if not ob:
        raise HTTPException(404, "No such onboarding.")
    try:
        made = shares.create_link(conn, SHARE_KIND, ob_id, body.get("recipient") or ob.get("person_name") or "", int(body.get("hours") or 168),
                                  None if body.get("max_views") in (None, "", 0) else int(body["max_views"]), viewer.source)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    base = _share_base(conn, request)
    return {**{k: made[k] for k in ("id", "code", "expires_at", "recipient", "max_views")}, "url": f"{base}/shared/{made['token']}", "local_only": _local(base)}


@router.get("/api/onboardings/{ob_id}/links")
def list_links(ob_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"links": shares.list_links(conn, SHARE_KIND, ob_id)}


@router.delete("/api/onboardings/{ob_id}/links/{link_id}", status_code=204)
def revoke_link(ob_id: int, link_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if not shares.revoke(conn, link_id, SHARE_KIND, ob_id):
        raise HTTPException(404, "No active link with that id.")


# ---- feedback into the template ----


@router.post("/api/onboarding-feedback/{fid}/to-item", status_code=201)
def feedback_to_item(fid: int, body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Turn a new member's suggestion into a checklist template item, so the next person benefits."""
    require_write(viewer)
    fb = models.onboarding_feedback.fetch(conn, fid)
    if not fb:
        raise HTTPException(404, "No such feedback.")
    title = (body.get("title") or fb.get("suggestion") or fb.get("missing") or "").strip()
    if not title:
        raise HTTPException(400, "Say what the new item should be.")
    item = models.onboarding_items.create(conn, {"title": title[:200], "due_day": body.get("due_day"), "owner_role": body.get("owner_role") or "manager",
                                                 "category": body.get("category") or "people", "tracks": [], "position": 999}, viewer.source)
    models.onboarding_feedback.update(conn, fid, {"status": "used"}, viewer.source)
    return item
