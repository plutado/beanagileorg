"""Judgments about people: what must never leave an install, and wording that deserves a second look before it does.

Some of what a manager writes is personal judgment (who is trustworthy, who resists, who is close to whom) or
personal information (health, family, someone's plans to leave). Shared with another manager, that can be unfair
to the person and can breach HR policy or privacy law. Three layers keep it in:

1. Whole kinds of record that are judgments about people never go in any pack, file or export. Tests hold every
   export path to this list.
2. Fields on a person that record judgment or personal context never leave. A few more (working style, tags,
   background) can leave only with a warning acknowledged by the exporter.
3. Free text that does go out is scanned for wording that sounds like a judgment about a person or like personal
   information, especially when a person is named or linked. Anything found is shown to the exporter, who must
   acknowledge it or leave it out, and to the importer, who must opt in to it.

The scan is a prompt to think, not a guarantee: it can't understand meaning, so it errs on the side of asking.
"""

import json
import re
import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException

from .privacy import Viewer

# Records that are, by their nature, judgments about people or private reflection. Never exported between installs.
JUDGMENT_TABLES = frozenset({
    "interviews", "manager_notes", "interactions", "commitments", "growth_goals", "team_assessments", "assessments",
    "culture_observations", "culture_reads", "trust_pulses", "influence_links", "power_coalitions", "alliance_plans",
    "mentoring_sessions", "first90_milestones", "reflections", "preference_assessments", "behavior_targets",
    "criteria_profiles", "boss_conversations", "alignment_checks", "learning_questions",
    "core_challenge_checks", "syndrome_checks", "disciplines", "day_reviews", "support_profiles", "support_checkins",
    "seat_candidates", "career_entries",
})

# Fields on a person that record judgment, influence or personal context. Never exported.
PERSON_NEVER = frozenset({
    "influence", "stance", "motivations", "personal_context", "things_to_remember", "key_dates", "opinion_leader",
    "power_sources", "change_style", "change_agent", "key_person", "offer_them", "need_from_them", "expects_from_me",
    "advice", "insight", "support_notes", "communication", "goals", "contact", "outside_org",
})

# Fields on a person that may carry judgment. They can leave only after a warning is acknowledged.
PERSON_CAUTION = {
    "working_style": "how someone works is your impression of them",
    "tags": "tags often carry labels about a person",
    "background": "career history is personal information",
}

# Wording that sounds like a judgment about a person, or like personal information. A trailing * matches any ending;
# otherwise the whole word or phrase. Everyday engineering words ("blocker", "raise a risk", "system health") are left out.
TERMS = {
    "judgment": (
        "untrustworth*", "trustworth*", "dishonest*", "liar", "lying", "lazy", "incompetent*", "useless", "weak link",
        "toxic", "difficult person", "difficult to work with", "abrasive", "arrogant", "attitude problem", "bad attitude",
        "unreliable", "sloppy", "not a team player", "can't be trusted", "cannot be trusted", "drama", "bully*",
        "manipulat*", "passive-aggressive", "whiner", "whining", "gossip*", "low performer*", "underperform*",
        "poor performer*", "dead weight", "out of their depth", "out of his depth", "out of her depth", "resistant",
        "resists change", "obstructive", "opponent*", "enemy", "enemies", "saboteur*", "sabotag*", "hidden agenda",
        "ally of", "in the pocket", "loyal to", "can't stand", "has it in for",
    ),
    "employment": (
        "performance improvement plan", "pip", "disciplinar*", "written warning", "final warning", "fired", "firing",
        "let go", "terminat* employment", "layoff*", "laid off", "redundanc*", "demot*", "flight risk",
        "looking to leave", "job hunting", "interviewing elsewhere", "resign*", "salary", "salaries", "pay rise",
        "compensation", "grievance*", "complaint against", "hr investigation", "misconduct", "harass*",
    ),
    "personal": (
        "health condition", "health issue*", "medical", "illness", "off sick", "sick leave", "diagnos*", "therapy",
        "therapist", "mental health", "anxiety", "depression", "depressed", "burnout", "burned out", "burnt out",
        "pregnan*", "maternity", "paternity", "divorc*", "family issue*", "bereave*", "grief", "disabilit*", "disabled",
        "accommodation*", "religio*", "immigration", "visa status",
    ),
}

REASONS = {
    "judgment": "may be a judgment about a person",
    "employment": "may touch on someone's employment or pay",
    "personal": "may be personal information",
    "name": "names a person",
    "custom": "matches a word on your own list",
}

TERMS_KEY = "sensitivity.terms"
MAX_TERMS = 200

def _term(t: str) -> str:
    return re.escape(t[:-1]) + r"\w*" if t.endswith("*") else re.escape(t) + r"(?!\w)"


_PATTERNS = {group: re.compile(r"(?<!\w)(" + "|".join(_term(t) for t in terms) + r")", re.IGNORECASE) for group, terms in TERMS.items()}


def people_names(conn) -> list[str]:
    """Names to look for in free text: each person's full name, and a first name that's distinctive enough."""
    try:
        rows = conn.execute("SELECT name FROM people").fetchall()
    except sqlite3.Error:  # an app without People
        return []
    full = [r["name"].strip() for r in rows if r["name"] and r["name"].strip()]
    firsts = [n.split()[0] for n in full if not n.startswith("[") and " " in n]
    counts = {f.lower(): firsts.count(f) for f in firsts}
    return sorted(set(full) | {f for f in firsts if len(f) >= 3 and counts[f.lower()] == 1}, key=len, reverse=True)


def custom_terms(conn) -> list[str]:
    """Your own words to treat as sensitive, kept in settings. Same syntax as the built-in list (a trailing * for any ending)."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (TERMS_KEY,)).fetchone()
    try:
        terms = json.loads(row["value"]) if row else []
    except (TypeError, ValueError):
        return []
    return [t for t in terms if isinstance(t, str) and t.strip()]


def compile_terms(terms) -> re.Pattern | None:
    terms = [t.strip() for t in terms or () if t.strip() and t.strip() != "*"]
    return re.compile(r"(?<!\w)(" + "|".join(_term(t) for t in terms) + r")", re.IGNORECASE) if terms else None


def context(conn) -> dict:
    """Everything a scan needs from this install: the names of people here and your own word list."""
    return {"names": people_names(conn), "custom": compile_terms(custom_terms(conn))}


def scan_text(text, names=(), custom: re.Pattern | None = None) -> dict[str, list[str]]:
    """What in this text deserves a second look, by group: {"judgment": [...], "personal": [...], "name": [...]}."""
    if not isinstance(text, str) or not text.strip():
        return {}
    found = {}
    for group, pat in [*_PATTERNS.items(), *([("custom", custom)] if custom else [])]:
        hits = sorted({m.group(1).lower().strip() for m in pat.finditer(text)})
        if hits:
            found[group] = hits
    named = [n for n in names if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", text, re.IGNORECASE)]
    if named:
        found["name"] = named
    return found


def _texts(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _texts(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _texts(v)


def check_record(values: dict, names=(), linked_people=(), extra: list | None = None, custom: re.Pattern | None = None) -> dict | None:
    """Look over one outgoing record. Returns None, or {"level": "warn" | "note", "findings": [...]}.

    "warn" (must be acknowledged, or the record left out): personal or employment wording anywhere, or judgment
    wording in a record that names or links a person, or a word on your own list. "note" (shown, nothing required): a person named in free text,
    or judgment wording with no person in sight.
    """
    findings, groups, about_person = [], set(), bool(linked_people)
    for f, v in (values or {}).items():
        hit = {}
        for t in _texts(v):
            for g, terms in scan_text(t, names, custom).items():
                hit.setdefault(g, set()).update(terms)
        for g, terms in hit.items():
            groups.add(g)
            findings.append({"field": f, "reason": REASONS[g], "words": sorted(terms)})
        if "name" in hit:
            about_person = True
    for e in extra or []:
        groups.add("judgment")
        findings.append(e)
    if not findings:
        return None
    warn = bool(groups & {"personal", "employment", "custom"}) or ("judgment" in groups and about_person)
    return {"level": "warn" if warn else "note", "findings": findings}


def check_text(text: str, ctx: dict) -> dict | None:
    """Look over a document about to leave (a report, a plan, a message), paragraph by paragraph.

    Each paragraph is judged on its own, so a name in one and a judgment word in another don't add up to a warning.
    Returns None, or {"level", "findings": [{"reason", "words", "excerpt"}]} with the paragraphs that need a look.
    """
    findings, level = [], "note"
    for para in re.split(r"\n\s*\n|\n(?=\s*[-*#|]|\s*\d+\.)", text or ""):
        found = check_record({"text": para}, ctx["names"], custom=ctx["custom"])
        if not found:
            continue
        if found["level"] == "warn":
            level = "warn"
        excerpt = " ".join(para.split())[:200]
        for f in found["findings"]:
            findings.append({"reason": f["reason"], "words": f["words"], "excerpt": excerpt, "level": found["level"]})
    return {"level": level, "findings": findings} if findings else None


def build_router() -> APIRouter:
    from .app import get_conn, get_viewer, require_full  # imported here to avoid a circular import

    router = APIRouter()

    @router.post("/api/sensitivity/scan")
    def scan(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
        """Check text before it leaves: wording that may judge a person, touch on employment or pay, or be personal."""
        text = body.get("text")
        if not isinstance(text, str):
            raise HTTPException(400, "Send the text to check.")
        return check_text(text[:200_000], context(conn)) or {"level": None, "findings": []}

    @router.get("/api/sensitivity/terms")
    def get_terms(viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        return {"terms": custom_terms(conn), "built_in": {g: list(t) for g, t in TERMS.items()}}

    @router.put("/api/sensitivity/terms")
    def put_terms(body: dict = Body(...), viewer: Viewer = Depends(require_full), conn=Depends(get_conn)):
        terms = body.get("terms")
        if not isinstance(terms, list) or not all(isinstance(t, str) for t in terms):
            raise HTTPException(400, "Send a list of words or phrases.")
        clean = sorted({" ".join(t.split())[:60] for t in terms if t.strip() and t.strip() != "*"}, key=str.lower)
        if len(clean) > MAX_TERMS:
            raise HTTPException(400, f"Keep the list to {MAX_TERMS} words or phrases.")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (TERMS_KEY, json.dumps(clean)))
        return {"terms": clean, "built_in": {g: list(t) for g, t in TERMS.items()}}

    return router
