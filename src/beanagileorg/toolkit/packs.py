"""Sharing between installs: packs of chosen records and fields that one manager exports and another imports.

Granular by design. The exporter picks kinds, then records, then fields; private fields need their own tick and
some fields never leave. The importer sees a preview, decides record by record, and nothing changes until they
confirm. Each shared record carries a pack identity, so importing a newer pack updates rather than duplicates,
and an origin saying where it came from. See docs/specs/sharing-between-installs.md.
"""

import hashlib
import hmac
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
    team_links: tuple = ()  # fields pointing at a team: the same
    never: tuple = ("notes",)  # fields that never leave, and aren't offered
    describe: tuple = field(default_factory=tuple)  # fields shown beside each record when choosing
    children: tuple = ()  # (name, record, foreign key, fields): rows that belong to each record, such as a metric's readings

    @property
    def links(self) -> dict[str, str]:
        return {**{f: "people" for f in self.people_links}, **{f: "teams" for f in self.team_links}}

    def offered(self) -> list[str]:
        skip = set(self.links) | set(self.never) | set(PACK_COLUMNS)
        own = [f for f, spec in self.record.fields.items() if f not in skip and spec.type != "ids"]
        return own + ([self.children[0]] if self.children else [])

    def shareable(self) -> list[str]:
        return [f for f in self.offered() if f not in self.record.fields or self.record.fields[f].level != Level.PRIVATE]

    def private(self) -> list[str]:
        return [f for f in self.offered() if f in self.record.fields and self.record.fields[f].level == Level.PRIVATE]

    def child_rows(self, conn, rid: int) -> list[dict]:
        if not self.children:
            return []
        _, rec, fk, cols = self.children
        return [{c: r[c] for c in cols} for r in rec.fetch_all(conn, f"{fk} = ?", (rid,))]


KINDS = {k.key: k for k in (
    Kind("role_templates", "Role templates", models.role_templates, "name", describe=("name",)),
    Kind("sdlc_policies", "SDLC policies", models.sdlc_policies, "title", people_links=("owner_id",), describe=("category", "status")),
    Kind("regression_plans", "Regression plans", models.regression_plans, "title", people_links=("owner_id", "backup_owner_id", "signoff_by_id"),
         describe=("kind", "start_date", "status")),
    Kind("risks", "Risks", models.risks, "title", people_links=("owner_id",), never=("notes", "team_id"), describe=("level", "status", "due")),
    Kind("decisions_needed", "Decisions", models.decisions_needed, "decision", people_links=("from_id",), never=("team_id",), describe=("status", "needed_by")),
    Kind("sos_items", "Scrum of Scrums items", models.sos_items, "question", people_links=("owner_id",), team_links=("raised_by_team_id", "owner_team_id"),
         describe=("kind", "status", "due")),
    Kind("core_processes", "Core processes", models.core_processes, "name", people_links=("owner_id",), never=("notes", "team_id", "position"), describe=("importance", "aim")),
    Kind("metrics", "Metrics", models.metrics, "name", describe=("unit",), children=("readings", models.metric_readings, "metric_id", ("date", "value"))),
)}


def _kind(key: str) -> Kind:
    if key not in KINDS:
        raise HTTPException(400, f"Can't share that kind of record: {key}.")
    return KINDS[key]


def _names(conn, target: str = "people") -> dict[int, str]:
    rec = models.people if target == "people" else models.teams
    return {p["id"]: p["name"] for p in rec.fetch_all(conn)}


def _ids_by_name(conn, target: str) -> dict[str, int]:
    return {n.lower(): i for i, n in _names(conn, target).items()}


def sign(passphrase: str, digest: str) -> str:
    return hmac.new(passphrase.encode(), digest.encode(), hashlib.sha256).hexdigest()


def _plain(v):
    """Whole-number floats as ints, so a pack that passed through a browser (where 30.0 becomes 30) still checks out."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    return v


def checksum(kinds: dict) -> str:
    return hashlib.sha256(json.dumps(_plain(kinds), sort_keys=True, default=str).encode()).hexdigest()


# ---- choosing what goes in ----


@router.get("/api/packs/kinds")
def kinds(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    out = []
    for k in KINDS.values():
        rows = k.record.fetch_all(conn)
        out.append({"key": k.key, "label": k.label, "count": len(rows), "natural": k.natural, "shareable": k.shareable(), "private": k.private() if viewer.floor == Level.PRIVATE else [],
                    "links": list(k.links), "never": list(k.never),
                    "records": [{"id": r["id"], "label": r[k.natural], "detail": [str(r[d]) for d in k.describe if d != k.natural and r.get(d)],
                                 "shared_before": bool(r.get("pack_uid")), "origin": r.get("origin") or None} for r in rows]})
    return {"kinds": out, "actions": ACTIONS}


def build_pack(conn, viewer: Viewer, selection: dict, from_name: str = "", about: str = "", assign: bool = False, passphrase: str = "") -> dict:
    """Build a pack from a selection: {kind: {ids, fields, private_fields, links: {field: name|drop}}}."""
    if not isinstance(selection, dict) or not selection:
        raise HTTPException(400, "Choose at least one kind of record to share.")
    names = {"people": _names(conn, "people"), "teams": _names(conn, "teams")}
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
        links = {f: m for f, m in (sel.get("links") or {}).items() if f in k.links and m in ("name", "drop")}
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
            rec = {"uid": uid, "values": {c: (k.child_rows(conn, rid) if k.children and c == k.children[0] else r.get(c)) for c in cols}}
            named = {f: names[t].get(r.get(f)) for f, t in k.links.items() if links.get(f, "name") == "name" and r.get(f)}
            if named:
                rec["people"] = named
            records.append(rec)
        if records:
            kinds_out[key] = {"label": k.label, "fields": cols, "private_fields": private, "records": records}
    if not kinds_out:
        raise HTTPException(400, "Choose at least one record to share.")
    digest = checksum(kinds_out)
    pack = {"format": FORMAT, "version": VERSION, "created": today().isoformat(), "from": (from_name or "").strip()[:80],
            "about": (about or "").strip()[:500], "kinds": kinds_out, "checksum": digest}
    if passphrase:
        pack["signature"] = sign(passphrase, digest)
    return pack


@router.post("/api/packs/review")
def review(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """What a pack would contain, without writing anything or recording an export."""
    return build_pack(conn, viewer, body.get("selection") or {}, body.get("from") or "", body.get("about") or "")


@router.post("/api/packs/export")
def export(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    pack = build_pack(conn, viewer, body.get("selection") or {}, body.get("from") or "", body.get("about") or "", assign=True, passphrase=body.get("passphrase") or "")
    summary = ", ".join(f"{len(v['records'])} {v['label'].lower()}" for v in pack["kinds"].values())
    log_export(conn, "pack", f"Pack: {summary}", [r for v in pack["kinds"].values() for r in v["records"]], viewer.source)
    return pack


# ---- bringing it in ----


def _check(pack: dict, passphrase: str = "", require: bool = False) -> dict:
    if not isinstance(pack, dict) or pack.get("format") != FORMAT:
        raise HTTPException(400, "That isn't a beanagileorg pack.")
    if pack.get("version") != VERSION:
        raise HTTPException(400, f"This pack is version {pack.get('version')}; this copy reads version {VERSION}.")
    kinds_in = pack.get("kinds")
    if not isinstance(kinds_in, dict) or checksum(kinds_in) != pack.get("checksum"):
        raise HTTPException(400, "The pack's checksum doesn't match its contents, so it may have been changed on the way.")
    for key in kinds_in:
        _kind(key)
    if pack.get("signature") and require:
        if not passphrase:
            raise HTTPException(400, "This pack is signed. Enter the passphrase you agreed with the sender.")
        if not hmac.compare_digest(sign(passphrase, pack["checksum"]), pack["signature"]):
            raise HTTPException(400, "The passphrase doesn't match this pack's signature, so it may not be from who you think, or it was changed.")
    return kinds_in


def verified(pack: dict, passphrase: str) -> bool | None:
    """None when the pack isn't signed or no passphrase was given; otherwise whether the signature matches."""
    if not pack.get("signature") or not passphrase:
        return None
    return hmac.compare_digest(sign(passphrase, pack.get("checksum") or ""), pack["signature"])


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


def _current(conn, k: Kind, mine: dict | None) -> dict | None:
    if mine is None or not k.children:
        return mine
    return {**mine, k.children[0]: k.child_rows(conn, mine["id"])}


def _same(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list) and a and isinstance(a[0], dict):
        key = lambda r: json.dumps(_plain(r), sort_keys=True, default=str)
        return sorted(map(key, a)) == sorted(map(key, b))
    return a == b


def compare(k: Kind, rec: dict, mine: dict | None) -> dict:
    incoming = _clean(k, rec.get("values"))
    if mine is None:
        return {"status": "new", "diffs": [], "default": "add"}
    base = ((mine.get("origin") or {}).get("values")) or {}
    diffs = []
    for f, theirs in incoming.items():
        cur = mine.get(f)
        if _same(cur, theirs):
            continue
        # Child rows (such as readings) merge by adding what's missing and never removing, so they can't conflict.
        conflict = not (k.children and f == k.children[0]) and f in base and not _same(cur, base[f]) and not _same(theirs, base[f])
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
    names = {"people": _ids_by_name(conn, "people"), "teams": _ids_by_name(conn, "teams")}
    out = []
    for key, data in kinds_in.items():
        k = KINDS[key]
        rows = []
        for rec in data.get("records") or []:
            mine = _current(conn, k, _match(conn, k, rec))
            cmp = compare(k, rec, mine)
            people = {f: {"name": n, "found": n.lower() in names[k.links[f]], "kind": k.links[f]} for f, n in (rec.get("people") or {}).items() if f in k.links and n}
            rows.append({"uid": rec.get("uid"), "label": (rec.get("values") or {}).get(k.natural), "mine_id": mine["id"] if mine else None, **cmp, "people": people})
        out.append({"key": key, "label": k.label, "fields": data.get("fields") or [], "records": rows})
    return {"from": pack.get("from"), "about": pack.get("about"), "created": pack.get("created"), "kinds": out, "actions": ACTIONS,
            "signed": bool(pack.get("signature")), "verified": verified(pack, body.get("passphrase") or "")}


def _origin(pack: dict, values: dict) -> dict:
    return {"from": pack.get("from") or None, "created": pack.get("created"), "imported_on": today().isoformat(), "values": values}


@router.post("/api/packs/apply")
def apply(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Apply the importer's decisions: {kind: {uid: {action, fields: {field: mine|theirs}}}}. Records with no decision use the default."""
    require_write(viewer)
    pack = body.get("pack")
    kinds_in = _check(pack, body.get("passphrase") or "", require=True)
    decisions = body.get("decisions") or {}
    names = {"people": _ids_by_name(conn, "people"), "teams": _ids_by_name(conn, "teams")}
    result = {"added": 0, "updated": 0, "copied": 0, "skipped": 0, "kept": 0, "unmatched_people": []}
    for key, data in kinds_in.items():
        k = KINDS[key]
        for rec in data.get("records") or []:
            uid = rec.get("uid")
            mine = _current(conn, k, _match(conn, k, rec))
            cmp = compare(k, rec, mine)
            d = (decisions.get(key) or {}).get(uid) or {}
            action = d.get("action") or cmp["default"]
            if action not in ACTIONS:
                raise HTTPException(400, f"Unknown action: {action}.")
            incoming = _clean(k, rec.get("values"))
            links = {}
            for f, n in (rec.get("people") or {}).items():
                if f in k.links and n:
                    pid = names[k.links[f]].get(n.lower())
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
                kids = values.pop(k.children[0], None) if k.children else None
                created = k.record.create(conn, {**values, "pack_uid": new_uid, "origin": _origin(pack, incoming)}, viewer.source)
                if kids:
                    _add_children(conn, k, created["id"], kids, viewer.source)
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
            kids = changes.pop(k.children[0], None) if k.children else None
            k.record.update(conn, mine["id"], changes, viewer.source)
            if kids:
                _add_children(conn, k, mine["id"], kids, viewer.source)
            result["updated"] += 1
    result["unmatched_people"] = sorted(set(result["unmatched_people"]))
    conn.execute("INSERT INTO import_log (pack_from, pack_about, pack_created, checksum, summary, source) VALUES (?, ?, ?, ?, ?, ?)",
                 (pack.get("from"), pack.get("about"), pack.get("created"), pack.get("checksum"), json.dumps(result), viewer.source))
    return result


def _add_children(conn, k: Kind, rid: int, rows: list, source: str) -> None:
    """Add the incoming child rows (such as readings) that aren't here already; never delete local ones."""
    name, rec, fk, cols = k.children
    have = {json.dumps(r, sort_keys=True, default=str) for r in k.child_rows(conn, rid)}
    for r in rows or []:
        row = {c: r.get(c) for c in cols}
        if json.dumps(row, sort_keys=True, default=str) not in have:
            rec.create(conn, {**row, fk: rid}, source)


@router.get("/api/packs/log")
def log(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    imports = [dict(r) | {"summary": json.loads(r["summary"] or "{}")} for r in conn.execute("SELECT * FROM import_log ORDER BY id DESC LIMIT 50").fetchall()]
    exports = [dict(r) for r in conn.execute("SELECT at, title, record_count, content_sha256 FROM export_log WHERE kind = 'pack' ORDER BY id DESC LIMIT 50").fetchall()]
    return {"imports": imports, "exports": exports}
