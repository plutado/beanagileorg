"""Sharing between installs: packs of chosen records and fields that one manager exports and another imports.

Granular by design. The exporter picks kinds, then records, then fields; private fields need their own tick and
some fields never leave. The importer sees a preview, decides record by record, and nothing changes until they
confirm. Each shared record carries a pack identity, so importing a newer pack updates rather than duplicates,
and an origin saying where it came from. See docs/specs/sharing-between-installs.md.
"""

import hashlib
import json
import secrets
from dataclasses import dataclass, field

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write, today

router = APIRouter()

FORMAT, VERSION = "beanagileorg.pack", 1
PACK_COLUMNS = ("pack_uid", "origin")
ACTIONS = ("add", "skip", "update", "keep", "merge", "copy")


@dataclass
class Kind:
    key: str
    label: str
    record: object
    natural: str  # the field that identifies a record across installs when there's no pack identity yet
    people_links: tuple = ()  # fields pointing at a person: sent as a name only, or dropped
    never: tuple = ("notes",)  # fields that never leave, and aren't offered
    describe: tuple = field(default_factory=tuple)  # fields shown beside each record when choosing

    def offered(self) -> list[str]:
        skip = set(self.people_links) | set(self.never) | set(PACK_COLUMNS)
        return [f for f, spec in self.record.fields.items() if f not in skip and spec.type != "ids"]

    def shareable(self) -> list[str]:
        return [f for f in self.offered() if self.record.fields[f].level != Level.PRIVATE]

    def private(self) -> list[str]:
        return [f for f in self.offered() if self.record.fields[f].level == Level.PRIVATE]


KINDS = {k.key: k for k in (
    Kind("role_templates", "Role templates", models.role_templates, "name", describe=("name",)),
    Kind("sdlc_policies", "SDLC policies", models.sdlc_policies, "title", people_links=("owner_id",), describe=("category", "status")),
    Kind("regression_plans", "Regression plans", models.regression_plans, "title", people_links=("owner_id", "backup_owner_id", "signoff_by_id"),
         describe=("kind", "start_date", "status")),
)}


def _kind(key: str) -> Kind:
    if key not in KINDS:
        raise HTTPException(400, f"Can't share that kind of record: {key}.")
    return KINDS[key]


def _names(conn) -> dict[int, str]:
    return {p["id"]: p["name"] for p in models.people.fetch_all(conn)}


def checksum(kinds: dict) -> str:
    return hashlib.sha256(json.dumps(kinds, sort_keys=True, default=str).encode()).hexdigest()


# ---- choosing what goes in ----


@router.get("/api/packs/kinds")
def kinds(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    out = []
    for k in KINDS.values():
        rows = k.record.fetch_all(conn)
        out.append({"key": k.key, "label": k.label, "count": len(rows), "natural": k.natural, "shareable": k.shareable(), "private": k.private() if viewer.floor == Level.PRIVATE else [],
                    "links": list(k.people_links), "never": list(k.never),
                    "records": [{"id": r["id"], "label": r[k.natural], "detail": [str(r[d]) for d in k.describe if d != k.natural and r.get(d)],
                                 "shared_before": bool(r.get("pack_uid")), "origin": r.get("origin") or None} for r in rows]})
    return {"kinds": out, "actions": ACTIONS}


def build_pack(conn, viewer: Viewer, selection: dict, from_name: str = "", about: str = "", assign: bool = False) -> dict:
    """Build a pack from a selection: {kind: {ids, fields, private_fields, links: {field: name|drop}}}."""
    if not isinstance(selection, dict) or not selection:
        raise HTTPException(400, "Choose at least one kind of record to share.")
    names = _names(conn)
    kinds_out = {}
    for key, sel in selection.items():
        k = _kind(key)
        ids = [i for i in (sel.get("ids") or []) if isinstance(i, int)]
        if not ids:
            continue
        fields = [f for f in (sel.get("fields") or []) if f in k.shareable()]
        private = [f for f in (sel.get("private_fields") or []) if f in k.private()] if viewer.floor == Level.PRIVATE else []
        cols = fields + private
        if k.natural not in cols:
            cols.insert(0, k.natural)  # always send what identifies the record
        links = {f: m for f, m in (sel.get("links") or {}).items() if f in k.people_links and m in ("name", "drop")}
        records = []
        for rid in ids:
            r = k.record.fetch(conn, rid)
            if r is None:
                raise HTTPException(400, f"No such record in {k.label}.")
            uid = r.get("pack_uid")
            if not uid:
                uid = secrets.token_hex(8)
                if assign:
                    conn.execute(f"UPDATE {k.record.table} SET pack_uid = ? WHERE id = ?", (uid, rid))
            rec = {"uid": uid, "values": {c: r.get(c) for c in cols}}
            named = {f: names.get(r.get(f)) for f in k.people_links if links.get(f, "name") == "name" and r.get(f)}
            if named:
                rec["people"] = named
            records.append(rec)
        if records:
            kinds_out[key] = {"label": k.label, "fields": cols, "private_fields": private, "records": records}
    if not kinds_out:
        raise HTTPException(400, "Choose at least one record to share.")
    return {"format": FORMAT, "version": VERSION, "created": today().isoformat(), "from": (from_name or "").strip()[:80],
            "about": (about or "").strip()[:500], "kinds": kinds_out, "checksum": checksum(kinds_out)}


@router.post("/api/packs/review")
def review(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """What a pack would contain, without writing anything or recording an export."""
    return build_pack(conn, viewer, body.get("selection") or {}, body.get("from") or "", body.get("about") or "")


@router.post("/api/packs/export")
def export(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    pack = build_pack(conn, viewer, body.get("selection") or {}, body.get("from") or "", body.get("about") or "", assign=True)
    summary = ", ".join(f"{len(v['records'])} {v['label'].lower()}" for v in pack["kinds"].values())
    log_export(conn, "pack", f"Pack: {summary}", [r for v in pack["kinds"].values() for r in v["records"]], viewer.source)
    return pack


# ---- bringing it in ----


def _check(pack: dict) -> dict:
    if not isinstance(pack, dict) or pack.get("format") != FORMAT:
        raise HTTPException(400, "That isn't a beanagileorg pack.")
    if pack.get("version") != VERSION:
        raise HTTPException(400, f"This pack is version {pack.get('version')}; this copy reads version {VERSION}.")
    kinds_in = pack.get("kinds")
    if not isinstance(kinds_in, dict) or checksum(kinds_in) != pack.get("checksum"):
        raise HTTPException(400, "The pack's checksum doesn't match its contents, so it may have been changed on the way.")
    for key in kinds_in:
        _kind(key)
    return kinds_in


def _clean(k: Kind, values: dict) -> dict:
    """Only fields this kind can share, never the ones that must stay behind."""
    allowed = set(k.offered())
    return {f: v for f, v in (values or {}).items() if f in allowed}


def _match(conn, k: Kind, rec: dict) -> dict | None:
    row = conn.execute(f"SELECT id FROM {k.record.table} WHERE pack_uid = ?", (rec.get("uid"),)).fetchone()
    if row is None:
        nat = (rec.get("values") or {}).get(k.natural)
        if nat:
            row = conn.execute(f"SELECT id FROM {k.record.table} WHERE {k.natural} = ?", (nat,)).fetchone()
    return k.record.fetch(conn, row["id"]) if row else None


def compare(k: Kind, rec: dict, mine: dict | None) -> dict:
    incoming = _clean(k, rec.get("values"))
    if mine is None:
        return {"status": "new", "diffs": [], "default": "add"}
    base = ((mine.get("origin") or {}).get("values")) or {}
    diffs = []
    for f, theirs in incoming.items():
        cur = mine.get(f)
        if cur == theirs:
            continue
        conflict = f in base and cur != base[f] and theirs != base[f]
        diffs.append({"field": f, "mine": cur, "theirs": theirs, "conflict": conflict})
    if not diffs:
        return {"status": "unchanged", "diffs": [], "default": "skip"}
    status = "conflict" if any(d["conflict"] for d in diffs) else "changed"
    return {"status": status, "diffs": diffs, "default": "keep" if status == "conflict" else "update"}


@router.post("/api/packs/inspect")
def inspect(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Read a pack and show, record by record, what importing it would do. Changes nothing."""
    pack = body.get("pack")
    kinds_in = _check(pack)
    names = {n.lower(): i for i, n in _names(conn).items()}
    out = []
    for key, data in kinds_in.items():
        k = KINDS[key]
        rows = []
        for rec in data.get("records") or []:
            mine = _match(conn, k, rec)
            cmp = compare(k, rec, mine)
            people = {f: {"name": n, "found": n.lower() in names} for f, n in (rec.get("people") or {}).items() if f in k.people_links and n}
            rows.append({"uid": rec.get("uid"), "label": (rec.get("values") or {}).get(k.natural), "mine_id": mine["id"] if mine else None, **cmp, "people": people})
        out.append({"key": key, "label": k.label, "fields": data.get("fields") or [], "records": rows})
    return {"from": pack.get("from"), "about": pack.get("about"), "created": pack.get("created"), "kinds": out, "actions": ACTIONS}


def _origin(pack: dict, values: dict) -> dict:
    return {"from": pack.get("from") or None, "created": pack.get("created"), "imported_on": today().isoformat(), "values": values}


@router.post("/api/packs/apply")
def apply(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Apply the importer's decisions: {kind: {uid: {action, fields: {field: mine|theirs}}}}. Records with no decision use the default."""
    require_write(viewer)
    pack = body.get("pack")
    kinds_in = _check(pack)
    decisions = body.get("decisions") or {}
    names = {n.lower(): i for i, n in _names(conn).items()}
    result = {"added": 0, "updated": 0, "copied": 0, "skipped": 0, "kept": 0, "unmatched_people": []}
    for key, data in kinds_in.items():
        k = KINDS[key]
        for rec in data.get("records") or []:
            uid = rec.get("uid")
            mine = _match(conn, k, rec)
            cmp = compare(k, rec, mine)
            d = (decisions.get(key) or {}).get(uid) or {}
            action = d.get("action") or cmp["default"]
            if action not in ACTIONS:
                raise HTTPException(400, f"Unknown action: {action}.")
            incoming = _clean(k, rec.get("values"))
            links = {}
            for f, n in (rec.get("people") or {}).items():
                if f in k.people_links and n:
                    pid = names.get(n.lower())
                    if pid:
                        links[f] = pid
                    else:
                        result["unmatched_people"].append(n)
            if action == "skip" or (action == "keep" and mine is None):
                result["skipped"] += 1
                continue
            if action == "keep":
                result["kept"] += 1
                continue
            if mine is None or action in ("add", "copy"):
                values = {**incoming, **links}
                if mine is not None and action == "copy":
                    nat = values.get(k.natural) or ""
                    values[k.natural] = f"{nat} (from {pack.get('from') or 'a pack'})"
                new_uid = uid if mine is None else secrets.token_hex(8)
                k.record.create(conn, {**values, "pack_uid": new_uid, "origin": _origin(pack, incoming)}, viewer.source)
                result["copied" if mine is not None else "added"] += 1
                continue
            # update or merge an existing record
            if action == "update":
                changes = dict(incoming)
            else:  # merge: field by field
                choose = d.get("fields") or {}
                changes = {f: v for f, v in incoming.items() if choose.get(f, "theirs" if not any(x["field"] == f and x["conflict"] for x in cmp["diffs"]) else "mine") == "theirs"}
            changes.update({f: v for f, v in links.items() if f not in changes})
            changes.update({"pack_uid": mine.get("pack_uid") or uid, "origin": _origin(pack, incoming)})
            k.record.update(conn, mine["id"], changes, viewer.source)
            result["updated"] += 1
    result["unmatched_people"] = sorted(set(result["unmatched_people"]))
    conn.execute("INSERT INTO import_log (pack_from, pack_about, pack_created, checksum, summary, source) VALUES (?, ?, ?, ?, ?, ?)",
                 (pack.get("from"), pack.get("about"), pack.get("created"), pack.get("checksum"), json.dumps(result), viewer.source))
    return result


@router.get("/api/packs/log")
def log(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    imports = [dict(r) | {"summary": json.loads(r["summary"] or "{}")} for r in conn.execute("SELECT * FROM import_log ORDER BY id DESC LIMIT 50").fetchall()]
    exports = [dict(r) for r in conn.execute("SELECT at, title, record_count, content_sha256 FROM export_log WHERE kind = 'pack' ORDER BY id DESC LIMIT 50").fetchall()]
    return {"imports": imports, "exports": exports}
