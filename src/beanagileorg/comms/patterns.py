"""Decks that learn from what you've presented before.

For an audience, look at your approved and presented decks for them and how each went (the outcome noted after
presenting), and suggest the length, the mix of slides, the structure of the deck that worked best, and how much
detail to put on slides versus notes. A new deck can start from that pattern: last time's structure with its
headings as bracketed placeholders, and this week's facts pulled fresh from the toolkit into the notes. Patterns come
only from your own decks.
"""

from collections import Counter
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
STATUS_WEIGHT = {"presented": 2.0, "approved": 1.0}
LANDED_WEIGHT = {"well": 1.5, "mixed": 1.0, "poorly": 0.4}
LENGTH_NUDGE = {"too long": -0.15, "too short": 0.15, "about right": 0.0}
# The slide every layout starts from when a pattern is turned into a new deck.
PLACEHOLDER = {
    "bullets": {"items": ["[Placeholder point 1]", "[Placeholder point 2]", "[Placeholder point 3]"]},
    "big-number": {"number": "[00%]", "caption": "[Placeholder caption]"},
    "comparison": {"left_title": "[Before]", "left_items": ["[Placeholder]"], "right_title": "[After]", "right_items": ["[Placeholder]"]},
    "quote": {"quote": "[Placeholder quote]", "attribution": "[Placeholder name]"},
    "table": {"rows": ["[Column] | [Column]", "[Placeholder] | [Placeholder]"]},
    "code": {"language": "plaintext", "code": "[Placeholder code]"},
    "shapes": {"shapes": ["a | #4f46e5 | 120", "b | #0891b2 | 120"]},
}


def _key(audience: str | None) -> str:
    return " ".join((audience or "").lower().split())


def _outcomes(conn, deck_id: int) -> list[dict]:
    return models.deck_outcomes.fetch_all(conn, "deck_id = ?", (deck_id,))


def _weight(deck: dict, outcomes: list[dict]) -> float:
    w = STATUS_WEIGHT.get(deck["status"], 0.0)
    if outcomes:
        w = max(w, 1.0) * LANDED_WEIGHT.get(outcomes[0]["landed"], 1.0)
    return w


def _weighted_median(values: list[tuple[float, float]]) -> float | None:
    """values: (value, weight)."""
    values = sorted(v for v in values if v[1] > 0)
    total = sum(w for _, w in values)
    if not total:
        return None
    run = 0.0
    for v, w in values:
        run += w
        if run >= total / 2:
            return v
    return values[-1][0]


def learn(conn, audience: str, private: bool = False) -> dict:
    key = _key(audience)
    decks = [d for d in models.decks.fetch_all(conn) if _key(d.get("audience")) == key]
    used = []
    for d in decks:
        outs = _outcomes(conn, d["id"])
        w = _weight(d, outs)
        if w <= 0:
            continue
        slides = sorted((s for s in models.slides.fetch_all(conn, "deck_id = ?", (d["id"],)) if not s["hidden"]), key=lambda s: (s["position"], s["id"]))
        used.append({"deck": d, "slides": slides, "outcomes": outs, "weight": round(w, 2)})
    if not used:
        return {"audience": audience, "decks_used": [], "target_slides": None, "mix": [], "outline": [], "advice": [
            "No approved or presented decks for this audience yet. Once you present one and note how it went, suggestions appear here."]}
    all_outcomes = [o for u in used for o in u["outcomes"]]
    base = _weighted_median([(len(u["slides"]), u["weight"]) for u in used]) or 0
    nudges = [LENGTH_NUDGE[o["length"]] for o in all_outcomes if o.get("length") in LENGTH_NUDGE]
    target = max(3, round(base * (1 + (sum(nudges) / len(nudges) if nudges else 0))))
    mix = Counter()
    for u in used:
        for s in u["slides"]:
            mix[s["layout"]] += u["weight"] / max(1, len(u["slides"]))
    total = sum(mix.values()) or 1
    best = max(used, key=lambda u: (u["weight"], u["deck"]["id"]))
    outline = [{"layout": s["layout"], "heading": (s["content"] or {}).get("heading") or ""} for s in best["slides"]]
    # Trim toward the target from the middle, dropping the least typical layouts first; never the opening or closing.
    while len(outline) > target and len(outline) > 2:
        middle = range(1, len(outline) - 1)
        drop = min(middle, key=lambda i: (mix[outline[i]["layout"]], -i))
        outline.pop(drop)
    advice = []
    if nudges:
        lean = sum(nudges) / len(nudges)
        if lean < 0:
            advice.append(f"Past decks for this audience ran long. Aim for about {target} slides.")
        elif lean > 0:
            advice.append(f"This audience wanted more last time. About {target} slides fits.")
        else:
            advice.append(f"The length has landed about right. Keep to about {target} slides.")
    else:
        advice.append(f"About {target} slides, the typical length of what you've shown this audience.")
    details = Counter(o["detail"] for o in all_outcomes if o.get("detail"))
    if details.get("needed more", 0) > details.get("needed less", 0):
        advice.append("They asked for more detail: keep slides simple and put the depth in an appendix or the speaker notes, ready for questions.")
    elif details.get("needed less", 0) > details.get("needed more", 0):
        advice.append("They wanted less detail: one point per slide, numbers rounded, and the rest in the notes.")
    landed = Counter(o["landed"] for o in all_outcomes if o.get("landed"))
    if landed:
        advice.append(f"Outcomes so far: {', '.join(f'{n} {k}' for k, n in landed.most_common())}.")
    notes = [o["note"] for o in all_outcomes if o.get("note")] if private else []  # outcome notes are private
    if notes:
        advice.append(f"Your last note: \"{notes[0]}\"")
    return {
        "audience": audience, "target_slides": target, "outline": outline,
        "mix": [{"layout": k, "share": round(100 * v / total)} for k, v in mix.most_common()],
        "best_deck": {"id": best["deck"]["id"], "title": best["deck"]["title"]},
        "decks_used": [{"id": u["deck"]["id"], "title": u["deck"]["title"], "status": u["deck"]["status"], "slides": len(u["slides"]), "weight": u["weight"],
                        "landed": u["outcomes"][0]["landed"] if u["outcomes"] else None} for u in sorted(used, key=lambda u: -u["weight"])],
        "advice": advice,
    }


@router.get("/api/decks/audiences")
def audiences(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Audiences you've made decks for, with how many decks and outcomes each has."""
    seen: dict[str, dict] = {}
    for d in models.decks.fetch_all(conn):
        k = _key(d.get("audience"))
        if not k:
            continue
        e = seen.setdefault(k, {"audience": d["audience"].strip(), "decks": 0, "presented": 0, "outcomes": 0})
        e["decks"] += 1
        e["presented"] += d["status"] == "presented"
        e["outcomes"] += len(_outcomes(conn, d["id"]))
    return sorted(seen.values(), key=lambda e: (-e["presented"], e["audience"].lower()))


@router.get("/api/decks/patterns")
def patterns(audience: str, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if not _key(audience):
        raise HTTPException(400, "Say which audience.")
    return learn(conn, audience, private=viewer.floor == Level.PRIVATE and not viewer.guarded)


@router.post("/api/decks/from-pattern", status_code=201)
def from_pattern(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Start a deck for an audience from what worked before, with this week's toolkit facts in the first slide's notes."""
    require_write(viewer)
    audience = (body.get("audience") or "").strip()
    p = learn(conn, audience, private=True) if audience else None
    if not p or not p["outline"]:
        raise HTTPException(400, "There's no pattern for that audience yet. Present a deck to them first.")
    title = (body.get("title") or "").strip() or f"[Placeholder title] for {audience}"
    deck = models.decks.create(conn, {"title": title, "audience": audience}, viewer.source)
    facts = None
    try:
        from .messaging import _pull

        facts = (_pull(conn, "/api/status/draft").get("markdown") or "").strip() or None
    except HTTPException:
        facts = None  # the toolkit isn't connected or running; the deck still starts from the pattern
    guide = "Started from what worked with " + audience + ". " + " ".join(p["advice"])
    for position, item in enumerate(p["outline"]):
        layout = item["layout"]
        content = dict(PLACEHOLDER.get(layout, {}))
        if position == 0:
            content["heading"] = title
            if layout == "title":
                content["subheading"] = f"[Placeholder subtitle] · {date.today().isoformat()}"
        elif item["heading"]:
            content["heading"] = f"[Last time: {item['heading']}]"
        notes = guide if position == 0 else None
        if position == 1 and facts:
            notes = "Fresh from the toolkit, for this deck:\n\n" + facts[:4000]
        models.slides.create(conn, {"deck_id": deck["id"], "position": position, "layout": layout, "content": content, "notes": notes}, viewer.source)
    return {"deck_id": deck["id"], "slides": len(p["outline"]), "facts": bool(facts)}
