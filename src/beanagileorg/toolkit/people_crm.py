"""People as a CRM: conversations and notes, relationship health, one-on-one prep, a timeline across the toolkit,
an org chart from reporting lines, and your choice of which profile fields to show.

Everything here is private. Sensitive fields are masked in the page until you choose to show them, and private
fields never appear while presenting.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer, no_judgments
from beanagileorg.core.privacy import Level, Viewer
from beanagileorg.core.sensitivity import PERSON_CAUTION, PERSON_NEVER, check_record, compile_terms, custom_terms

from . import models
from .routes import create_action, require_write

router = APIRouter()
LAYOUT_KEY = "people.hidden_fields"
ME_KEY = "people.me_id"
SENSITIVE = ("personal_context", "support_notes", "key_dates", "motivations")
OPTIONAL = ("start_date", "location", "timezone", "background", "skills", "certifications", "goals", "wants_to_learn", "can_teach", "working_style",
            "support_notes", "contact", "tags", "cadence_days", "influence", "stance", "communication", "motivations", "personal_context",
            "things_to_remember", "key_dates", "next_meeting", "manager_id", "offer_them", "need_from_them", "expects_from_me", "advice", "insight", "change_style", "change_agent", "key_person", "power_sources", "opinion_leader")


def _today() -> date:
    return date.today()


def _involves(ids_json: str | None, person_id: int) -> bool:
    return person_id in (json.loads(ids_json) if ids_json else [])


def _last_contacts(conn) -> dict[int, str]:
    out: dict[int, str] = {}
    for r in conn.execute("SELECT date, person_ids FROM interactions WHERE date <= ?", (_today().isoformat(),)):
        for pid in json.loads(r["person_ids"] or "[]"):
            out[pid] = max(out.get(pid, ""), r["date"])
    for r in conn.execute("SELECT person_id, date FROM interviews WHERE status = 'done' AND date IS NOT NULL"):
        if r["person_id"]:
            out[r["person_id"]] = max(out.get(r["person_id"], ""), r["date"])
    return out


# ---- your choice of fields ----


@router.get("/api/people/layout")
def get_layout(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (LAYOUT_KEY,)).fetchone()
    return {"hidden": json.loads(row["value"]) if row else [], "optional": list(OPTIONAL), "sensitive": list(SENSITIVE)}


@router.put("/api/people/layout")
def put_layout(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    hidden = [f for f in body.get("hidden", []) if f in OPTIONAL]
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (LAYOUT_KEY, json.dumps(hidden)))
    return get_layout(viewer, conn)


# ---- who you are, and who reports to you ----


def me_id(conn) -> int | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (ME_KEY,)).fetchone()
    if not row:
        return None
    pid = int(row["value"])
    return pid if conn.execute("SELECT 1 FROM people WHERE id = ?", (pid,)).fetchone() else None


@router.get("/api/people/me")
def get_me(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return {"person_id": me_id(conn)}


@router.put("/api/people/me")
def put_me(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    pid = body.get("person_id")
    if pid is None:
        conn.execute("DELETE FROM settings WHERE key = ?", (ME_KEY,))
        return {"person_id": None}
    if models.people.fetch(conn, pid) is None:
        raise HTTPException(400, "That person isn't in People.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (ME_KEY, str(pid)))
    return {"person_id": pid}


@router.patch("/api/commitments/{commitment_id}")
def update_commitment(commitment_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Marking a commitment done records the day; reopening it clears that."""
    require_write(viewer)
    if "status" in body and "done_on" not in body:
        body = {**body, "done_on": _today().isoformat() if body["status"] == "done" else None}
    c = models.commitments.update(conn, commitment_id, body, viewer.source)
    if c is None:
        raise HTTPException(404, "No such commitment.")
    return c


@router.get("/api/people/reports")
def reports(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Your direct reports at a glance: what's owed each way, what's late, and when you last talked."""
    me = me_id(conn)
    if viewer.floor != Level.PRIVATE or me is None:
        return {"me": me, "reports": []}
    today = _today().isoformat()
    last = _last_contacts(conn)
    out = []
    for p in models.people.fetch_all(conn, "manager_id = ? AND active = 1", (me,)):
        cs = models.commitments.fetch_all(conn, "person_id = ? AND status = 'open'", (p["id"],))
        lc = last.get(p["id"])
        out.append({"id": p["id"], "name": p["name"], "role": p["role"], "last_contact": lc,
                    "days_since": (_today() - date.fromisoformat(lc)).days if lc else None, "next_meeting": p["next_meeting"],
                    "i_owe": sum(1 for c in cs if c["direction"] == "mine"), "they_owe": sum(1 for c in cs if c["direction"] == "theirs"),
                    "late": sum(1 for c in cs if c["due"] and c["due"] < today),
                    "goals": conn.execute("SELECT COUNT(*) FROM growth_goals WHERE person_id = ? AND status = 'active'", (p["id"],)).fetchone()[0],
                    "unshared": conn.execute("SELECT COUNT(*) FROM manager_notes WHERE person_id = ? AND shared = 0 AND kind IN ('praise', 'constructive')", (p["id"],)).fetchone()[0]})
    return {"me": me, "reports": out}


@router.get("/api/people/{person_id}/agenda", dependencies=[Depends(no_judgments)])
def agenda(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A draft agenda for your next one-on-one: what's owed each way, their goals, feedback to share, and what's open."""
    if viewer.floor != Level.PRIVATE:
        raise HTTPException(403, "Agendas are private.")
    p = models.people.fetch(conn, person_id)
    if p is None:
        raise HTTPException(404, "No such person.")
    first = p["name"].split(" ")[0]
    cs = models.commitments.fetch_all(conn, "person_id = ? AND status = 'open'", (person_id,))
    lines = [f"# One-on-one with {p['name']}", "", f"{p['next_meeting'] or _today().isoformat()}", ""]
    talks = [i for i in models.interactions.fetch_all(conn) if person_id in i["person_ids"]]
    if talks and talks[0]["takeaways"]:
        lines += ["## Since last time", "", talks[0]["takeaways"], ""]
    theirs = [c for c in cs if c["direction"] == "theirs"]
    mine = [c for c in cs if c["direction"] == "mine"]
    due = lambda c: f" (due {c['due']})" if c["due"] else ""
    if theirs:
        lines += [f"## {first}'s commitments", ""] + [f"- [ ] {c['title']}{due(c)}" for c in theirs] + [""]
    if mine:
        lines += ["## My commitments", ""] + [f"- [ ] {c['title']}{due(c)}" for c in mine] + [""]
    goals = models.growth_goals.fetch_all(conn, "person_id = ? AND status = 'active'", (person_id,))
    if goals:
        lines += ["## Growth goals", ""] + [f"- {g['goal']}" + (f": {g['progress']}" if g["progress"] else "") for g in goals] + [""]
    notes = models.manager_notes.fetch_all(conn, "person_id = ? AND shared = 0 AND kind IN ('praise', 'constructive')", (person_id,))
    if notes:
        lines += ["## Feedback to share", ""] + [f"- {n['kind'].capitalize()}: {n['note']}" for n in notes] + [""]
    items = models.action_items.fetch_all(conn, "status != 'done' AND (owner_id = ? OR raised_by_id = ?)", (person_id, person_id))
    if items:
        lines += ["## Open dev-sync items", ""] + [f"- {a['concern']}" for a in items] + [""]
    lines += ["## Their topics", "", "- ", "", "## Anything I can do to help?", ""]
    return {"markdown": "\n".join(lines).rstrip() + "\n"}


# ---- reporting lines ----


@router.patch("/api/people/{person_id}")
def update_person(person_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Like any update, but a manager can't be the person themselves or someone who reports to them."""
    require_write(viewer)
    if models.people.fetch(conn, person_id) is None:
        raise HTTPException(404, "No such person.")
    manager = body.get("manager_id")
    seen = set()
    while manager is not None:
        if manager == person_id or manager in seen:
            raise HTTPException(400, "That would make someone report to themselves through the chain.")
        seen.add(manager)
        row = conn.execute("SELECT manager_id FROM people WHERE id = ?", (manager,)).fetchone()
        if row is None:
            raise HTTPException(400, "That manager isn't in People.")
        manager = row["manager_id"]
    current = models.people.fetch(conn, person_id)
    if current["placeholder"] and "placeholder" not in body and body.get("name") and not body["name"].strip().startswith("["):
        body = {**body, "placeholder": False}  # a real name replaces a stand-in
    if "key_dates" in body:
        body = {**body, "key_dates": {"dates": [d for d in (body["key_dates"] or {}).get("dates", []) if isinstance(d, dict) and d.get("label") and d.get("date")]} if body["key_dates"] else {}}
    return models.people.visible(models.people.update(conn, person_id, body, viewer.source), viewer)


@router.get("/api/people/org-chart")
def org_chart(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    people = [p for p in models.people.visible_all(models.people.fetch_all(conn), viewer) if p.get("active", True)]
    ids = {p["id"] for p in people}
    nodes = {p["id"]: {"id": p["id"], "name": p["name"], "role": p.get("role"), "department": p.get("department_name"),
                       "relationship": p.get("relationship"), "children": []} for p in people}
    roots = []
    for p in people:
        boss = p.get("manager_id")
        (nodes[boss]["children"] if boss in ids else roots).append(nodes[p["id"]])
    return {"roots": roots, "with_manager": sum(1 for p in people if p.get("manager_id") in ids)}


# ---- the overview, a person's page, and their timeline ----


@router.get("/api/people/overview")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    people = models.people.visible_all(models.people.fetch_all(conn), viewer)
    if viewer.floor != Level.PRIVATE:
        return {"people": people, "private": False}
    last = _last_contacts(conn)
    today = _today()
    open_items = conn.execute("SELECT owner_id, raised_by_id FROM action_items WHERE status != 'done'").fetchall()
    out = []
    for p in people:
        lc = last.get(p["id"])
        days = (today - date.fromisoformat(lc)).days if lc else None
        due = bool(p.get("cadence_days") and p["active"] and (days is None or days > p["cadence_days"]))
        out.append({**p, "last_contact": lc, "days_since": days, "due": due,
                    "open_follow_ups": sum(1 for r in open_items if p["id"] in (r["owner_id"], r["raised_by_id"]))})
    return {"people": out, "private": True}


def _upcoming_dates(person: dict, within: int = 7) -> list[dict]:
    today, out = _today(), []
    for d in ((person.get("key_dates") or {}).get("dates") or []):
        try:
            when = date.fromisoformat(d["date"])
        except (KeyError, TypeError, ValueError):
            continue
        nxt = when.replace(year=today.year)
        if nxt < today:
            nxt = nxt.replace(year=today.year + 1)
        if (nxt - today).days <= within:
            out.append({"label": d["label"], "date": nxt.isoformat(), "days": (nxt - today).days})
    return out


@router.get("/api/people/{person_id}/crm", dependencies=[Depends(no_judgments)])
def crm(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    p = models.people.fetch(conn, person_id)
    if p is None:
        raise HTTPException(404, "No such person.")
    person = models.people.visible(p, viewer)
    out = {"person": person,
           "reports": [{"id": r["id"], "name": r["name"], "role": r["role"]} for r in models.people.fetch_all(conn, "manager_id = ? AND active = 1", (person_id,))],
           "teams": [{"id": t["id"], "name": t["name"], "as": [label for key, label in (("product_owner_id", "product owner"), ("scrum_master_id", "Scrum Master"), ("lead_id", "lead")) if t[key] == person_id] or ["member"]}
                     for t in models.teams.fetch_all(conn) if person_id in t["member_ids"] or person_id in (t["product_owner_id"], t["scrum_master_id"], t["lead_id"])]}
    if viewer.floor != Level.PRIVATE:
        return out
    talks = [i for i in models.interactions.fetch_all(conn) if person_id in i["person_ids"]]
    last = _last_contacts(conn).get(person_id)
    days = (_today() - date.fromisoformat(last)).days if last else None
    me = me_id(conn)
    out.update({
        "is_me": me == person_id, "is_report": me is not None and p["manager_id"] == me,
        "commitments": models.commitments.fetch_all(conn, "person_id = ? AND (status = 'open' OR done_on >= ?)", (person_id, (_today() - timedelta(days=30)).isoformat())),
        "interactions": talks[:25],
        "health": {"last_contact": last, "days_since": days, "cadence_days": p["cadence_days"],
                   "due": bool(p["cadence_days"] and (days is None or days > p["cadence_days"])), "next_meeting": p["next_meeting"]},
        "follow_ups": models.action_items.visible_all(models.action_items.fetch_all(conn, "status != 'done' AND (owner_id = ? OR raised_by_id = ?)", (person_id, person_id)), viewer),
        "sos": [{"id": s["id"], "question": s["question"], "status": s["status"], "due": s["due"]} for s in models.sos_items.fetch_all(conn, "status != 'done'")
                if s["owner_id"] == person_id or person_id in s["stakeholder_ids"]],
        "upcoming_dates": _upcoming_dates(p, 30),
    })
    if out["is_report"]:
        out["manager"] = {"notes": models.manager_notes.fetch_all(conn, "person_id = ?", (person_id,))[:50],
                          "goals": models.growth_goals.fetch_all(conn, "person_id = ?", (person_id,))}
    return out


@router.get("/api/people/{person_id}/timeline", dependencies=[Depends(no_judgments)])
def timeline(person_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    if viewer.floor != Level.PRIVATE:
        return {"events": []}
    if models.people.fetch(conn, person_id) is None:
        raise HTTPException(404, "No such person.")
    ev = []
    for i in models.interactions.fetch_all(conn):
        if person_id in i["person_ids"]:
            ev.append({"date": i["date"], "kind": i["kind"], "title": i["title"] or i["kind"], "route": f"/people/{person_id}", "detail": (i["takeaways"] or "")[:160]})
    for r in models.interviews.fetch_all(conn, "person_id = ?", (person_id,)):
        ev.append({"date": r["date"], "kind": "listening tour", "title": f"Listening-tour one-on-one ({r['status']})", "route": f"/listening/{r['id']}", "detail": ""})
    for a in models.action_items.fetch_all(conn, "owner_id = ? OR raised_by_id = ?", (person_id, person_id)):
        role = "owns" if a["owner_id"] == person_id else "raised"
        ev.append({"date": a["raised_on"], "kind": "dev-sync", "title": f"{role.capitalize()}: {a['concern']}", "route": f"/dev-sync/{a['id']}", "detail": a["status"]})
    for s in models.sos_items.fetch_all(conn):
        if s["owner_id"] == person_id or person_id in s["stakeholder_ids"]:
            ev.append({"date": s["raised_on"], "kind": "Scrum of Scrums", "title": s["question"], "route": "/sos", "detail": s["status"]})
    for r in models.retros.fetch_all(conn):
        if person_id in r["attendee_ids"]:
            ev.append({"date": r["date"], "kind": "retro", "title": f"Retrospective{' sprint ' + str(r['sprint_number']) if r['sprint_number'] else ''}", "route": f"/retros/{r['id']}", "detail": ""})
    ev.sort(key=lambda e: e["date"] or "", reverse=True)
    return {"events": ev[:200]}


@router.post("/api/interactions/{interaction_id}/follow-up", status_code=201)
def follow_up(interaction_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Each line under follow-ups becomes a dev-sync item tied to this conversation; lines already sent are skipped."""
    require_write(viewer)
    i = models.interactions.fetch(conn, interaction_id)
    if i is None:
        raise HTTPException(404, "No such conversation.")
    done = {r["concern"] for r in conn.execute("SELECT concern FROM action_items WHERE interaction_id = ?", (interaction_id,))}
    lines = [ln.strip().lstrip("-*• ").strip() for ln in (i["follow_ups"] or "").splitlines()]
    created = []
    for ln in lines:
        if ln and ln not in done:
            created.append(create_action({"concern": ln, "origin": "one-on-one" if i["kind"] == "one-on-one" else "other",
                                          "raised_by_id": i["person_ids"][0] if i["person_ids"] else None, "interaction_id": interaction_id}, viewer, conn))
    return {"created": created}


# ---- relationship balance: up, down and sideways ----

DIRECTIONS = ("up", "down", "sideways", "outward")
QUIET_DAYS = 21


def directions(conn) -> dict[int, str]:
    """Where each person sits relative to you: up your management chain, down in your reporting line, sideways among peers, or outward."""
    me = me_id(conn)
    people = models.people.fetch_all(conn)
    by_id = {p["id"]: p for p in people}
    up, cur, seen = set(), by_id.get(me, {}).get("manager_id") if me else None, set()
    while cur and cur not in seen:
        seen.add(cur)
        up.add(cur)
        cur = by_id.get(cur, {}).get("manager_id")
    down, frontier = set(), {me} if me else set()
    while frontier:
        frontier = {p["id"] for p in people if p.get("manager_id") in frontier and p["id"] not in down and p["id"] != me}
        down |= frontier
    out = {}
    for p in people:
        if p["id"] == me:
            continue
        rel = p.get("relationship")
        out[p["id"]] = ("up" if p["id"] in up or (rel == "manager" and p["id"] not in down) else "down" if p["id"] in down or rel in ("employee", "contractor")
                        else "sideways" if rel == "peer" else "outward")
    return out


def _counts(conn, where: dict[int, str], start: str, end: str) -> dict:
    counts = {d: 0 for d in DIRECTIONS}
    for r in conn.execute("SELECT person_ids FROM interactions WHERE date BETWEEN ? AND ?", (start, end)):
        for d in {where[pid] for pid in json.loads(r["person_ids"] or "[]") if pid in where}:
            counts[d] += 1
    return counts


def build_balance(conn, days: int = 30) -> dict:
    t = _today()
    where = directions(conn)
    start, prev_start = (t - timedelta(days=days - 1)).isoformat(), (t - timedelta(days=2 * days - 1)).isoformat()
    last = _last_contacts(conn)
    peers = []
    for p in models.people.fetch_all(conn, "active = 1"):
        if where.get(p["id"]) != "sideways":
            continue
        lc = last.get(p["id"])
        since = (t - date.fromisoformat(lc)).days if lc else None
        peers.append({"id": p["id"], "name": p["name"], "role": p.get("role"), "influence": p.get("influence"), "stance": p.get("stance"),
                      "last_contact": lc, "days_since": since, "quiet": since is None or since > QUIET_DAYS, "placeholder": bool(p.get("placeholder")),
                      "offer_them": p.get("offer_them"), "need_from_them": p.get("need_from_them"), "cadence_days": p.get("cadence_days")})
    peers.sort(key=lambda x: (x["days_since"] is not None, -(x["days_since"] or 0)))
    now = _counts(conn, where, start, t.isoformat())
    before = _counts(conn, where, prev_start, (t - timedelta(days=days)).isoformat())
    return {"days": days, "has_me": bool(me_id(conn)), "counts": now, "previous": before, "peers": peers,
            "people": {d: sum(1 for v in where.values() if v == d) for d in DIRECTIONS},
            "top_heavy": now["up"] >= 2 and now["up"] > now["sideways"]}


@router.get("/api/people/balance")
def balance(days: int = 30, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Private: how your conversations split between up, down, sideways and outward, and which peers have gone quiet."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    if not 7 <= days <= 180:
        raise HTTPException(400, "Look back between 7 and 180 days.")
    return build_balance(conn, days)


def neighbors(conn, last: dict | None = None) -> list[dict]:
    """People named on a system (owner, first responder, backup, business contacts) you haven't had a conversation
    with yet. Meet them before an incident, not during one."""
    last = _last_contacts(conn) if last is None else last
    me = me_id(conn)
    people = {p["id"]: p for p in models.people.fetch_all(conn, "active = 1")}
    found: dict[int, list[str]] = {}
    for s in models.systems.fetch_all(conn):
        ids = [s.get("owner_id"), s.get("first_responder_id"), s.get("backup_id"), *(s.get("business_contact_ids") or [])]
        for pid in ids:
            if pid and pid != me and pid in people and pid not in last and s["name"] not in found.setdefault(pid, []):
                found[pid].append(s["name"])
    return [{"id": pid, "name": people[pid]["name"], "systems": names} for pid, names in found.items() if names][:8]


def people_due(conn) -> dict:
    """For Today: people past their check-in cadence, key dates this week, and meetings planned this week."""
    today, week = _today(), (_today() + timedelta(days=7)).isoformat()
    last = _last_contacts(conn)
    due, dates, meetings = [], [], []
    for p in models.people.fetch_all(conn, "active = 1"):
        lc = last.get(p["id"])
        days = (today - date.fromisoformat(lc)).days if lc else None
        if p["cadence_days"] and (days is None or days > p["cadence_days"]):
            due.append({"id": p["id"], "name": p["name"], "days_since": days, "cadence_days": p["cadence_days"]})
        dates += [{"id": p["id"], "name": p["name"], **d} for d in _upcoming_dates(p)]
        if p["next_meeting"] and today.isoformat() <= p["next_meeting"] <= week:
            meetings.append({"id": p["id"], "name": p["name"], "date": p["next_meeting"]})
    bal = build_balance(conn) if me_id(conn) else None
    sideways = None
    if bal:
        key_quiet = [{"id": p["id"], "name": p["name"], "days_since": p["days_since"]} for p in bal["peers"] if p["quiet"] and p["influence"] == "high"]
        if bal["top_heavy"] or key_quiet:
            sideways = {"up": bal["counts"]["up"], "sideways": bal["counts"]["sideways"], "top_heavy": bal["top_heavy"], "quiet": key_quiet[:5]}
    open_c = models.commitments.fetch_all(conn, "status = 'open' AND due IS NOT NULL")
    return {"sideways": sideways, "neighbors": neighbors(conn, last), "check_ins": due, "key_dates": sorted(dates, key=lambda d: d["days"]), "meetings": sorted(meetings, key=lambda m: m["date"]),
            "i_owe": [{"id": c["id"], "person_id": c["person_id"], "name": c["person_name"], "title": c["title"], "due": c["due"], "late": c["due"] < today.isoformat()}
                      for c in open_c if c["direction"] == "mine" and c["due"] <= week],
            "they_owe_late": [{"id": c["id"], "person_id": c["person_id"], "name": c["person_name"], "title": c["title"], "due": c["due"]}
                              for c in open_c if c["direction"] == "theirs" and c["due"] < today.isoformat()]}


@router.post("/api/people/roster", status_code=201)
def import_roster(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Add a team in one go: people, who reports to whom, who's on your team, and which record is you.

    Each entry has a key so others can point at it ("reports_to": "<key>" or "me"). Anyone already in People
    with the same name is reused, so running it twice adds nothing. Stand-ins are marked as placeholders,
    to be replaced with the real person later.
    """
    require_write(viewer)
    entries = body.get("people")
    if not isinstance(entries, list) or not entries:
        raise HTTPException(400, "The roster needs a list of people.")
    checks = incoming_checks(conn, entries)
    drop = bool(body.get("drop_private"))
    if checks and not drop and not body.get("acknowledged"):
        raise HTTPException(409, f"This roster carries impressions or labels for {len(checks)} {'person' if len(checks) == 1 else 'people'} "
                                 "(working style, tags or background). Review them first, or import without them.")
    keys, created, reused = {}, [], []
    for e in entries:
        name = (e.get("name") or "").strip()
        if not name or not e.get("key"):
            raise HTTPException(400, "Each person needs a key and a name.")
        if e.get("relationship") and e["relationship"] not in models.RELATIONSHIPS:
            raise HTTPException(400, f"Unknown relationship for {name}.")
        row = conn.execute("SELECT id FROM people WHERE name = ?", (name,)).fetchone()
        if row:
            keys[e["key"]] = row["id"]
            reused.append(name)
            continue
        # Support notes and other judgment fields never come in, even from an older roster file that carried them.
        data = {k: e[k] for k in ("role", "relationship", "start_date", *(() if drop else PERSON_CAUTION)) if e.get(k) is not None}
        data.update(name=name, placeholder=bool(e.get("placeholder", name.startswith("["))))
        keys[e["key"]] = models.people.create(conn, data, viewer.source)["id"]
        created.append(name)
    me_key = body.get("me")
    if me_key:
        if me_key not in keys:
            raise HTTPException(400, "'me' must be the key of someone in the roster.")
        if not me_id(conn):
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (ME_KEY, str(keys[me_key])))
    me = me_id(conn)
    for e in entries:
        boss = e.get("reports_to")
        target = me if boss == "me" else keys.get(boss) if boss else None
        if boss and target is None:
            raise HTTPException(400, f"{e['name']} reports to someone who isn't in the roster.")
        if target and target != keys[e["key"]]:
            models.people.update(conn, keys[e["key"]], {"manager_id": target}, viewer.source)
    team = conn.execute("SELECT id, member_ids FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1").fetchone()
    on_team = [keys[e["key"]] for e in entries if e.get("on_team")]
    if team and on_team:
        members = json.loads(team["member_ids"]) if team["member_ids"] else []
        members += [m for m in on_team if m not in members]
        models.teams.update(conn, team["id"], {"member_ids": members}, viewer.source)
    left_out = sorted({f for e in entries for f in e if f in PERSON_NEVER})
    return {"created": created, "reused": reused, "me": me, "team_members": len(on_team), "left_out": left_out}


def incoming_checks(conn, entries: list) -> list[dict]:
    """New people in an incoming roster whose working style, tags or background deserve a second look."""
    have = {r["name"] for r in conn.execute("SELECT name FROM people").fetchall()}
    fresh = [e for e in entries if isinstance(e, dict) and (e.get("name") or "").strip() not in have]
    return roster_checks({"people": fresh}, compile_terms(custom_terms(conn)))


@router.post("/api/people/roster/check-import")
def check_roster_import(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """What in an incoming roster deserves a second look before it's imported. Changes nothing."""
    entries = body.get("people")
    if not isinstance(entries, list):
        raise HTTPException(400, "The roster needs a list of people.")
    return {"checks": incoming_checks(conn, entries), "never": sorted({f for e in entries if isinstance(e, dict) for f in e if f in PERSON_NEVER})}


ADVICE_KINDS = ("technical", "cultural", "political", "personal")
QUALITIES_KEY = "advice.qualities"
# Qualities of a good network. The first two are read from your data; you tick the rest yourself.
NETWORK_QUALITIES = [
    ("mix_kinds", "The right mix of technical advisers, cultural interpreters and political counselors", "auto"),
    ("mix_places", "The right mix of insiders and outsiders", "auto"),
    ("loyal_outside", "Outside supporters loyal to you, not to the organization", "manual"),
    ("trusted_inside", "Insiders you trust, whose agendas don't conflict with yours, who give straight advice", "manual"),
    ("constituencies", "People from the key groups, so you hear more than one or two views", "manual"),
]


@router.get("/api/people/advice-network", dependencies=[Depends(no_judgments)])
def advice_network(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Your advisers by the kind of advice they give, inside and outside the organization. Higher up, political counsel matters more."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    out = {k: [] for k in ADVICE_KINDS}
    grid = {place: {k: [] for k in ADVICE_KINDS} for place in ("inside", "outside")}
    for p in models.people.fetch_all(conn, "active = 1"):
        place = "outside" if p.get("outside_org") else "inside"
        for k in p.get("advice") or []:
            if k in out:
                out[k].append({"id": p["id"], "name": p["name"]})
                grid[place][k].append({"id": p["id"], "name": p["name"]})
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (QUALITIES_KEY,)).fetchone()
    ticked = json.loads(row["value"]) if row else {}
    auto = {"mix_kinds": all(out[k] for k in ("technical", "cultural", "political")),
            "mix_places": any(grid["inside"][k] for k in ADVICE_KINDS) and any(grid["outside"][k] for k in ADVICE_KINDS)}
    qualities = [{"key": k, "label": l, "auto": how == "auto", "met": auto[k] if how == "auto" else bool(ticked.get(k))} for k, l, how in NETWORK_QUALITIES]
    return {"kinds": out, "grid": grid, "qualities": qualities, "missing": [k for k in ("cultural", "political", "personal") if not out[k]],
            "gaps": [f"{place} {k}" for place in grid for k in ("technical", "cultural", "political") if not grid[place][k]]}


@router.put("/api/people/advice-network/qualities")
def save_qualities(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    manual = {k for k, _, how in NETWORK_QUALITIES if how == "manual"}
    ticked = {k: bool(v) for k, v in body.items() if k in manual}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (QUALITIES_KEY, json.dumps(ticked)))
    return {"ticked": ticked}


ROSTER_SHAREABLE = ("role", "relationship")
ROSTER_PRIVATE = ("tags", "background", "working_style", "start_date")  # support notes can hold health or personal context: never
if set(ROSTER_SHAREABLE + ROSTER_PRIVATE) & PERSON_NEVER:
    raise RuntimeError("The roster would carry judgments about people.")


def _roster_key(name: str, taken: set) -> str:
    import re

    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "person"
    key, n = base, 2
    while key in taken:
        key, n = f"{base}-{n}", n + 1
    taken.add(key)
    return key


def build_roster(conn, scope: str = "team", include_private: bool = False) -> dict:
    """People as a roster file in the same format the roster import reads, so a team can move between installs.

    By default only names, roles, relationships, reporting lines and team membership go out; private fields
    (tags, background, working style, start date) only when asked for. Notes, conversations, feedback, assessments,
    support notes and every field that records judgment or personal context never do.
    """
    me = me_id(conn)
    people = models.people.fetch_all(conn, "active = 1")
    by_id = {p["id"]: p for p in people}
    team = conn.execute("SELECT member_ids FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1").fetchone()
    members = set(json.loads(team["member_ids"]) if team and team["member_ids"] else [])
    if scope == "team":
        keep = members | {p["id"] for p in people if me and p.get("manager_id") == me}
        if me:
            keep.add(me)
            if by_id.get(me, {}).get("manager_id"):
                keep.add(by_id[me]["manager_id"])
        chosen = [p for p in people if p["id"] in keep]
    else:
        chosen = people
    taken, keys = set(), {}
    for p in chosen:
        keys[p["id"]] = _roster_key(p["name"], taken)
    out = []
    for p in chosen:
        e = {"key": keys[p["id"]], "name": p["name"]}
        for f in ROSTER_SHAREABLE + (ROSTER_PRIVATE if include_private else ()):
            if p.get(f) not in (None, "", []):
                e[f] = p[f]
        if p.get("manager_id"):
            e["reports_to"] = "me" if p["manager_id"] == me and me in keys else keys.get(p["manager_id"])
            if e["reports_to"] is None:
                del e["reports_to"]
        if p["id"] in members:
            e["on_team"] = True
        if p.get("placeholder"):
            e["placeholder"] = True
        out.append(e)
    roster = {"_about": "A roster exported from beanagileorg. Import it under People > Fields > Import a roster. Anyone already there with the same name is left alone.",
              "format": "beanagileorg.roster", "version": 1, "exported_on": date.today().isoformat(), "scope": scope, "private_fields": include_private, "people": out}
    if me and me in keys:
        roster["me"] = keys[me]
    return roster


def roster_checks(roster: dict, custom=None) -> list[dict]:
    """People in a roster whose private fields may carry a judgment or personal information."""
    out = []
    for p in roster.get("people") or []:
        findings = [{"field": f, "reason": why, "words": []} for f, why in PERSON_CAUTION.items() if p.get(f) not in (None, "", [])]
        found = check_record({f: p.get(f) for f in PERSON_CAUTION if p.get(f)}, custom=custom)
        findings += [x for x in (found or {}).get("findings", []) if x not in findings]
        if findings:
            out.append({"name": p["name"], "level": "warn", "findings": findings})
    return out


@router.post("/api/people/roster/check")
def check_roster(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """What in a roster export deserves a second look before it goes. Writes and records nothing."""
    scope = body.get("scope") if body.get("scope") in ("team", "everyone") else "team"
    include_private = bool(body.get("include_private")) and viewer.floor == Level.PRIVATE
    return {"checks": roster_checks(build_roster(conn, scope, include_private), compile_terms(custom_terms(conn))) if include_private else []}


@router.post("/api/people/roster/export")
def export_roster(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Export People as a roster file. Shareable fields by default; private ones only when asked, and never in presentation mode."""
    from beanagileorg.core.export import log_export

    require_write(viewer)
    scope = body.get("scope") if body.get("scope") in ("team", "everyone") else "team"
    include_private = bool(body.get("include_private")) and viewer.floor == Level.PRIVATE
    roster = build_roster(conn, scope, include_private)
    checks = roster_checks(roster, compile_terms(custom_terms(conn))) if include_private else []
    if checks and not body.get("acknowledged"):
        raise HTTPException(409, f"Private fields for {len(checks)} {'person' if len(checks) == 1 else 'people'} may carry a judgment or personal information. "
                                 "Review them first, or export without private fields.")
    note = f", {len(checks)} cautions acknowledged" if checks else ""
    log_export(conn, "people:roster", f"Roster ({scope}{', with private fields' if include_private else ''}{note})", roster["people"], viewer.source)
    return roster
