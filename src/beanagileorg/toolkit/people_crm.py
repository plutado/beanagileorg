"""People as a CRM: conversations and notes, relationship health, one-on-one prep, a timeline across the toolkit,
an org chart from reporting lines, and your choice of which profile fields to show.

Everything here is private. Sensitive fields are masked in the page until you choose to show them, and private
fields never appear while presenting.
"""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import create_action, require_write

router = APIRouter()
LAYOUT_KEY = "people.hidden_fields"
ME_KEY = "people.me_id"
SENSITIVE = ("personal_context", "support_notes", "key_dates", "motivations")
OPTIONAL = ("start_date", "location", "timezone", "background", "skills", "certifications", "goals", "wants_to_learn", "can_teach", "working_style",
            "support_notes", "contact", "tags", "cadence_days", "influence", "stance", "communication", "motivations", "personal_context",
            "things_to_remember", "key_dates", "next_meeting", "manager_id", "offer_them", "need_from_them")


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


@router.get("/api/people/{person_id}/agenda")
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


@router.get("/api/people/{person_id}/crm")
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


@router.get("/api/people/{person_id}/timeline")
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
    return {"sideways": sideways, "check_ins": due, "key_dates": sorted(dates, key=lambda d: d["days"]), "meetings": sorted(meetings, key=lambda m: m["date"]),
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
        data = {k: e[k] for k in ("role", "relationship", "background", "tags", "working_style", "support_notes", "start_date") if e.get(k) is not None}
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
    return {"created": created, "reused": reused, "me": me, "team_members": len(on_team)}
