"""Coaching in the toolkit: an editable library of guides, tips for each screen, reflection prompts and a journal.

The starter content in core/coaching.py is copied in once. After that it belongs to the leader: edit it, delete it,
write new guides, or import a pack from someone else. Deleted built-in guides can be restored from the starter.
"""

import json
import re
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core import coaching as starter
from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import START_DATE_KEY, require_write

router = APIRouter()
SEEDED_KEY = "coaching.seeded"
GUIDE_FIELDS = ("slug", "theme", "title", "summary", "why", "practices", "pitfalls", "questions", "try_this", "body", "related", "reading", "inspired_by", "minutes", "status")


def _guide_row(g: dict, origin: str) -> dict:
    return {"slug": g["slug"], "theme": g["theme"], "title": g["title"], "summary": g["summary"], "why": g["why"], "practices": g["practices"],
            "pitfalls": g["pitfalls"], "questions": g["questions"], "try_this": g["try"], "related": g["related"], "reading": g["reading"],
            "minutes": g.get("minutes"), "origin": origin}


VERSION_KEY = "coaching.starter_version"


def seed_once(conn) -> bool:
    """Copy the starter content in on first run. Later versions add only what's new, so anything deleted stays deleted."""
    seeded = conn.execute("SELECT 1 FROM settings WHERE key = ?", (SEEDED_KEY,)).fetchone()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (VERSION_KEY,)).fetchone()
    have = int(row["value"]) if row else (1 if seeded else 0)
    if have >= starter.STARTER_VERSION:
        return False
    newer = lambda since: since > have
    for g in starter.GUIDES:
        if newer(g.get("since", 1)) and not conn.execute("SELECT 1 FROM coaching_guides WHERE slug = ?", (g["slug"],)).fetchone():
            models.coaching_guides.create(conn, _guide_row(g, "built-in"), "starter")
    for pos, (route, text, slug, since) in enumerate(starter.tip_entries()):
        if newer(since):
            models.coaching_tips.create(conn, {"route": route, "text": text, "guide_slug": slug, "position": pos}, "starter")
    if newer(starter.TAKE_STOCK_SINCE):
        for i, text in enumerate(starter.TAKE_STOCK_PROMPTS):
            models.coaching_prompts.create(conn, {"phase": "Take stock", "text": text, "position": 900 + i}, "starter")
    if not have:
        pos = 0
        for name, _, _, prompts in starter.REFLECTION_PHASES:
            for text in prompts:
                models.coaching_prompts.create(conn, {"phase": name, "text": text, "position": pos}, "starter")
                pos += 1
        for text in starter.ANYTIME_PROMPTS:
            models.coaching_prompts.create(conn, {"phase": "Any time", "text": text, "position": pos}, "starter")
            pos += 1
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (SEEDED_KEY, date.today().isoformat()))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (VERSION_KEY, str(starter.STARTER_VERSION)))
    return True


def _slugify(title: str, conn) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "guide"
    slug, n = base, 2
    while conn.execute("SELECT 1 FROM coaching_guides WHERE slug = ?", (slug,)).fetchone():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _themes(conn) -> list[dict]:
    known = [{"key": k, "title": t, "summary": s} for k, t, s in starter.THEMES]
    used = {r[0] for r in conn.execute("SELECT DISTINCT theme FROM coaching_guides")}
    return known + [{"key": u, "title": u[:1].upper() + u[1:], "summary": ""} for u in sorted(used - {k["key"] for k in known})]


@router.get("/api/coaching/library")
def library(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    guides = models.coaching_guides.visible_all(models.coaching_guides.fetch_all(conn), viewer)
    keep = ("id", "slug", "theme", "title", "summary", "minutes", "origin", "status", "inspired_by", "focus")
    have = {g["slug"] for g in guides}
    return {
        "themes": _themes(conn),
        "guides": [{k: g.get(k) for k in keep} for g in guides],
        "restorable": [{"slug": g["slug"], "title": g["title"]} for g in starter.GUIDES if g["slug"] not in have],
    }


@router.get("/api/coaching/guide/{slug}")
def guide(slug: str, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    rows = models.coaching_guides.fetch_all(conn, "slug = ?", (slug,))
    if not rows:
        raise HTTPException(404, "No such guide.")
    tips = models.coaching_tips.fetch_all(conn, "guide_slug = ?", (slug,))
    out = {"guide": models.coaching_guides.visible(rows[0], viewer), "tips": models.coaching_tips.visible_all(tips, viewer), "themes": _themes(conn)}
    if viewer.floor == Level.PRIVATE and not viewer.guarded:
        out["reflections"] = [{"id": r["id"], "date": r["date"], "prompt": r.get("prompt"), "entry": r.get("entry")} for r in models.reflections.fetch_all(conn, "guide_slug = ?", (slug,))][:10]
    return out


@router.post("/api/coaching-guides", status_code=201)
def create_guide(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if not (body.get("title") or "").strip():
        raise HTTPException(400, "Give the guide a title.")
    body = {**body, "slug": body.get("slug") or _slugify(body["title"], conn)}
    body.setdefault("origin", "mine")
    if conn.execute("SELECT 1 FROM coaching_guides WHERE slug = ?", (body["slug"],)).fetchone():
        raise HTTPException(409, "There's already a guide with that short name.")
    return models.coaching_guides.visible(models.coaching_guides.create(conn, body, viewer.source), viewer)


@router.post("/api/coaching/restore/{slug}", status_code=201)
def restore(slug: str, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    g = starter.guide(slug)
    if g is None:
        raise HTTPException(404, "That isn't one of the built-in guides.")
    if conn.execute("SELECT 1 FROM coaching_guides WHERE slug = ?", (slug,)).fetchone():
        raise HTTPException(409, "That guide is already in your library.")
    return models.coaching_guides.create(conn, _guide_row(g, "built-in"), viewer.source)


@router.get("/api/coaching/tips")
def tips(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Active tips by screen, with the guide each points to. Exportable, so the Comms studio can read its own screens' tips."""
    titles = {r["slug"]: r["title"] for r in conn.execute("SELECT slug, title FROM coaching_guides WHERE status = 'published'")}
    out = {}
    for t in models.coaching_tips.fetch_all(conn, "active = 1"):
        out.setdefault(t["route"], []).append({"id": t["id"], "text": t["text"], "guide": t["guide_slug"] if t["guide_slug"] in titles else None,
                                               "title": titles.get(t["guide_slug"])})
    return out


def _day_of_role(conn) -> int | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    if not row:
        return None
    return (date.today() - date.fromisoformat(row["value"])).days + 1


def _day_on(conn, when: str) -> int | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (START_DATE_KEY,)).fetchone()
    return (date.fromisoformat(when) - date.fromisoformat(row["value"])).days + 1 if row and when else None


def _insight(conn) -> dict:
    from .self_manage import reflection_insight
    return reflection_insight(conn)


@router.get("/api/coaching/reflect", dependencies=[Depends(no_judgments)])
def reflect(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    day = _day_of_role(conn)
    phase = starter.phase_for(day)
    prompts = models.coaching_prompts.fetch_all(conn, "active = 1")
    entries = models.reflections.fetch_all(conn)
    return {
        "day": day,
        "phase": phase,
        "prompts": [p for p in prompts if p["phase"] == phase],
        "anytime": [p for p in prompts if p["phase"] == "Any time"],
        "phases": [name for name, *_ in starter.REFLECTION_PHASES] + ["Any time", "Take stock"],
        "entries": entries[:30],
        "trend": [{"date": e["date"], "energy": e["energy"], "confidence": e["confidence"], "in_control": e.get("in_control"), "load": e.get("load"),
                   "day": _day_on(conn, e["date"])} for e in reversed(entries[:16])],
        "insight": _insight(conn),
        "take_stock": [p for p in prompts if p["phase"] == "Take stock"],
        "focus": [{"slug": g["slug"], "title": g["title"], "focus": g["focus"]} for g in models.coaching_guides.fetch_all(conn, "focus IS NOT NULL")],
        "guides": [{"slug": g["slug"], "title": g["title"]} for g in models.coaching_guides.fetch_all(conn, "status = 'published'")],
    }


def build_pack(conn) -> dict:
    """Guides, tips and prompts without anything private, for another leader to import."""
    exporter = Viewer(floor=Level.EXPORTABLE, source="pack", scopes=frozenset({"export:read"}))
    guides = models.coaching_guides.visible_all(models.coaching_guides.fetch_all(conn, "status = 'published'"), exporter)
    return {
        "kind": "beanagileorg.coaching-pack",
        "version": 1,
        "exported": date.today().isoformat(),
        "guides": [{k: g.get(k) for k in GUIDE_FIELDS if k != "status"} for g in guides],
        "tips": [{k: t[k] for k in ("route", "text", "guide_slug")} for t in models.coaching_tips.fetch_all(conn, "active = 1")],
        "prompts": [{k: p[k] for k in ("phase", "text")} for p in models.coaching_prompts.fetch_all(conn, "active = 1")],
    }


@router.get("/api/coaching/pack")
def pack(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_pack(conn)


@router.post("/api/coaching/pack/export")
def export_pack(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_pack(conn)
    log_export(conn, "coaching:pack", f"Coaching pack ({len(out['guides'])} guides)", [{"json": json.dumps(out)}], viewer.source)
    return out


@router.post("/api/coaching/pack/import")
def import_pack(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Add what's new. A guide whose short name you already have is skipped unless replace is true; your notes are kept."""
    require_write(viewer)
    data = body.get("pack") or {}
    if data.get("kind") != "beanagileorg.coaching-pack":
        raise HTTPException(400, "That isn't a beanagileorg coaching pack.")
    replace = bool(body.get("replace"))
    added = replaced = skipped = 0
    for g in data.get("guides", []):
        if not g.get("slug") or not g.get("title"):
            continue
        fields = {k: g.get(k) for k in GUIDE_FIELDS if k in g and k != "status"}
        existing = models.coaching_guides.fetch_all(conn, "slug = ?", (g["slug"],))
        if existing and replace:
            models.coaching_guides.update(conn, existing[0]["id"], {**fields, "origin": "imported"}, viewer.source)
            replaced += 1
        elif existing:
            skipped += 1
        else:
            models.coaching_guides.create(conn, {**fields, "origin": "imported"}, viewer.source)
            added += 1
    have_tips = {(t["route"], t["text"]) for t in models.coaching_tips.fetch_all(conn)}
    tips_added = 0
    for t in data.get("tips", []):
        if t.get("route") and t.get("text") and (t["route"], t["text"]) not in have_tips:
            models.coaching_tips.create(conn, {"route": t["route"], "text": t["text"], "guide_slug": t.get("guide_slug")}, viewer.source)
            tips_added += 1
    have_prompts = {(p["phase"], p["text"]) for p in models.coaching_prompts.fetch_all(conn)}
    prompts_added = 0
    for p in data.get("prompts", []):
        if p.get("text") and (p.get("phase") or "Any time", p["text"]) not in have_prompts:
            models.coaching_prompts.create(conn, {"phase": p.get("phase") or "Any time", "text": p["text"]}, viewer.source)
            prompts_added += 1
    return {"guides_added": added, "guides_replaced": replaced, "guides_skipped": skipped, "tips_added": tips_added, "prompts_added": prompts_added}


# ---- coaching suggested from what's happening ----


def suggestions(conn) -> list[dict]:
    """Guides that fit what's going on right now, each with the reason, at most four."""
    from datetime import timedelta

    t = date.today()
    t_iso = t.isoformat()
    published = {r["slug"]: r["title"] for r in conn.execute("SELECT slug, title FROM coaching_guides WHERE status = 'published'")}
    out = []

    def add(slug, why):
        if slug in published and slug not in {o["slug"] for o in out}:
            out.append({"slug": slug, "title": published[slug], "why": why})

    n = conn.execute("SELECT COUNT(*) FROM retro_commitments WHERE status IN ('committed', 'in progress') AND due IS NOT NULL AND due < ?", (t_iso,)).fetchone()[0]
    if n:
        add("retros", f"{n} retro commitment{'s are' if n != 1 else ' is'} past due. Did we do what we said?")
    if conn.execute("SELECT 1 FROM risks WHERE level = 'high' AND status = 'open'").fetchone():
        add("honest-status", "A high risk is open, so this week's status is likely red. Say it early and plainly.")
    recent = models.reflections.fetch_all(conn, "date >= ?", ((t - timedelta(days=21)).isoformat(),))[:3]
    if len(recent) == 3 and all((r.get("energy") or 5) <= 2 for r in recent):
        add("transition-traps", "Your energy has been low in your last three reflections.")
    from .self_manage import reflection_insight
    if reflection_insight(conn).get("over_the_top"):
        add("personal-disciplines", "Load is rising while energy falls. Time to drop or defer something.")
    closed = [p for p in models.sprint_plans.fetch_all(conn, "status = 'closed' AND committed_points > 0")]
    closed.sort(key=lambda p: p.get("closed_on") or "", reverse=True)
    if len(closed) >= 2 and all((p.get("completed_points") or 0) < 0.8 * p["committed_points"] for p in closed[:2]):
        add("refinement-and-estimation", "The last two sprints finished well short of their commitment.")
    sprint = conn.execute("SELECT id FROM sprints WHERE start_date <= ? AND (end_date IS NULL OR end_date >= ?) ORDER BY start_date DESC LIMIT 1", (t_iso, t_iso)).fetchone()
    if sprint and conn.execute("SELECT COUNT(*) FROM change_requests WHERE sprint_id = ? AND decision LIKE 'accepted%'", (sprint["id"],)).fetchone()[0] >= 2:
        add("change-mid-sprint", "Two or more changes have come into the current sprint.")
    from .people_crm import people_due
    due = people_due(conn)
    if len(due["check_ins"]) >= 2:
        add("one-on-ones", f"{len(due['check_ins'])} people are past their check-in cadence.")
    if due.get("sideways") and due["sideways"].get("top_heavy"):
        add("peer-relationships", "More of your conversations went up than sideways lately.")
    late_wins = conn.execute("SELECT COUNT(*) FROM plan_items WHERE early_win = 1 AND status NOT IN ('done', 'dropped') AND due_day IS NOT NULL AND due_day < ?",
                             (_day_of_role(conn) or 0,)).fetchone()[0]
    if late_wins:
        add("early-wins", f"{late_wins} early win{'s are' if late_wins != 1 else ' is'} past its day.")
    if conn.execute("SELECT 1 FROM culture_observations WHERE status = 'open' AND COALESCE(action, 'not yet') = 'not yet' AND date <= ?", ((t - timedelta(days=14)).isoformat(),)).fetchone():
        add("calling-out-harm", "Something you noted about the culture has gone two weeks without a response.")
    return out[:4]


@router.get("/api/coaching/suggestions", dependencies=[Depends(no_judgments)])
def get_suggestions(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    week = date.today().isocalendar()[1]
    prompts = models.coaching_prompts.fetch_all(conn, "active = 1")
    return {"suggestions": suggestions(conn), "prompt": prompts[week % len(prompts)]["text"] if prompts else None}
