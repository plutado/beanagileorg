"""The dev sync as a living board, and short updates on its rows.

Rows switched on for the board can be shared (today as a copied table, later on the share site), each with
a link to its latest update presentation. "Make an update" drafts a two-to-three-minute script from a row's
history, so a follow-up reaches people on their own time instead of waiting for the next meeting. The same
script drafting turns a weekly or sprint report into a short recorded update.
"""

import json
import re

from fastapi import APIRouter, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
BOARD_COLUMNS = ("Topic", "Kind", "Asked by", "Experts", "Decision maker", "Next action", "Due", "Status", "Latest update")


def _names(conn) -> dict[int, str]:
    return {p["id"]: p["name"] for p in models.people.fetch_all(conn)}


def board_rows(conn) -> list[dict]:
    names = _names(conn)
    out = []
    for r in models.action_items.fetch_all(conn, "on_board = 1 AND NOT COALESCE(never_share, 0)"):  # the board is shared
        out.append({"id": r["id"], "topic": r["concern"], "kind": r.get("kind") or "", "asked_by": r.get("raised_by_name") or "", "asked_on": r.get("raised_on"),
                    "experts": [names[i] for i in r.get("expert_ids") or [] if i in names], "decider": r.get("decider_name") or "",
                    "next_action": r.get("next_action") or "", "due": r.get("due"), "status": r["status"], "jira_keys": r.get("jira_keys") or [],
                    "update_url": r.get("update_url"), "update_on": r.get("update_on")})
    return out


@router.get("/api/dev-sync/board")
def board(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The rows switched on for the board, with only their shareable columns."""
    if viewer.floor != Level.PRIVATE:
        return {"hidden": True}
    return {"columns": list(BOARD_COLUMNS), "rows": board_rows(conn)}


def board_markdown(rows: list[dict]) -> str:
    cell = lambda v: str(v or "").replace("|", "/").replace("\n", " ")
    lines = ["| " + " | ".join(BOARD_COLUMNS) + " |", "| " + " | ".join("---" for _ in BOARD_COLUMNS) + " |"]
    for r in rows:
        topic = r["topic"] + (f" ({', '.join(r['jira_keys'])})" if r["jira_keys"] else "")
        update = f"[{r['update_on'] or 'update'}]({r['update_url']})" if r.get("update_url") else ""
        lines.append("| " + " | ".join(cell(v) for v in (topic, r["kind"], r["asked_by"], ", ".join(r["experts"]), r["decider"], r["next_action"], r["due"], r["status"])) + f" | {update} |")
    return "\n".join(lines)


@router.post("/api/dev-sync/board/export")
def export_board(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    rows = board_rows(conn)
    md = "# Dev-sync board\n\n" + (board_markdown(rows) if rows else "_Nothing on the board yet._")
    log_export(conn, "dev-sync:board", "Dev-sync board", [{"markdown": md}], viewer.source)
    return {"markdown": md, "rows": len(rows)}


def _history(conn, item_id: int) -> list[str]:
    rows = conn.execute("SELECT date(datetime(at, 'localtime')) AS d, old_value, new_value FROM change_log WHERE entity = 'action_item' AND record_id = ? "
                        "AND field = 'status' AND old_value IS NOT NULL ORDER BY id", (str(item_id),)).fetchall()
    return [f"{r['d']}: {r['old_value']} to {r['new_value']}" for r in rows]


@router.get("/api/actions/{item_id}/update-script")
def update_script(item_id: int, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """A two-to-three-minute script for an update on one dev-sync row, to record or turn into a short deck."""
    if viewer.floor != Level.PRIVATE:
        raise HTTPException(403, "Hidden while presenting.")
    r = models.action_items.fetch(conn, item_id)
    if not r:
        raise HTTPException(404, "No such item.")
    names = _names(conn)
    experts = [names[i] for i in r.get("expert_ids") or [] if i in names]
    keys = ", ".join(r.get("jira_keys") or [])
    hist = _history(conn, item_id)
    done = r["status"] == "done"
    md = [f"# Update: {r['concern']}", "",
          "About 2 to 3 minutes. Read it through once, then say it in your own words.", "",
          "## 1. The hook (10 seconds)",
          f"A quick update on {'a question' if r.get('kind') == 'question' else 'something'} raised in dev sync"
          + (f" by {r['raised_by_name']}" if r.get("raised_by_name") else "") + (f" on {r['raised_on']}" if r.get("raised_on") else "")
          + f": {r['concern']} [Placeholder: why it matters, in one sentence]", "",
          "## 2. What's happened (45 seconds)"]
    md += [f"- {h}" for h in hist] or ["- [Placeholder: what's been done since it was raised]"]
    if experts:
        md.append(f"- Worked through with {', '.join(experts)}")
    if keys:
        md.append(f"- Tracked in Jira: {keys}")
    md += ["", "## 3. Where it landed (45 seconds)"]
    if done:
        md.append("- It's done. [Placeholder: the outcome, and what changes for people]")
    else:
        md.append(f"- Next: {r.get('next_action') or '[Placeholder next step]'}" + (f", owned by {r['owner_name']}" if r.get("owner_name") else "") + (f", by {r['due']}" if r.get("due") else ""))
    if r.get("decider_name"):
        md.append(f"- Decision with {r['decider_name']}: [Placeholder: decided, or what they need to decide]")
    md += ["", "## 4. The ask (15 seconds)",
           "- [Placeholder: one specific ask, such as 'Reply by Thursday if you'd do it differently', or 'Nothing needed; this is for your information']", "",
           "## On screen",
           "- Open on the dev-sync row, then show the Jira issue or the change itself, then close on the next step and date.", "",
           "## Email summary (three lines)",
           f"1. {r['concern']}",
           f"2. {'Done: [Placeholder outcome]' if done else 'Next: ' + (r.get('next_action') or '[Placeholder]')}",
           "3. [Placeholder: the ask and the respond-by date]"]
    return {"title": f"Update: {r['concern']}", "markdown": "\n".join(md)}


def report_script(markdown: str, title: str, kind: str) -> str:
    """Turn a report's sections into a short narrated script: open with the headline, a beat per section, close with the ask."""
    sections, current = {}, None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current and line.startswith("- ") and "[Placeholder" not in line:
            sections[current].append(line[2:].strip())
    head = next((l for l in markdown.splitlines() if l.startswith("**Overall")), "")
    colour = re.search(r"Overall: (\w+)", head)
    out = [f"# {title}: video script", "", f"About {'2 to 3' if kind == 'weekly' else '3 to 4'} minutes. One take is fine; the transcript carries the detail.", "",
           "## Open (15 seconds)", f"[Placeholder: the one sentence that matters most this {'week' if kind == 'weekly' else 'sprint'}]"
           + (f" Overall we're {colour.group(1).lower()}." if colour else ""), ""]
    beats = [("Highlights", "What went well"), ("Delivered", "What we delivered"), ("Results", "Results"), ("Scope changes", "What changed mid-stream"),
             ("Scope changes during the sprint", "What changed mid-sprint"), ("Blockers and risks", "What's in the way"), ("Decisions", "Decisions"),
             ("Changes I'm bringing to the team", "Changes in how we work"), ("Progress on my mandate", "Progress on what I committed to"), ("Next week", "What's next"), ("Next sprint", "What's next")]
    for key, label in beats:
        items = sections.get(key)
        if items:
            out += [f"## {label}"] + [f"- {i}" for i in items[:4]] + [""]
    out += ["## Close (15 seconds)", "- [Placeholder: one ask, with a respond-by date, or 'nothing needed from you this week']", "",
            "## On screen", "- The sprint board or dashboard while you talk through results; the risk list for what's in the way; end on the ask."]
    return "\n".join(out)


@router.get("/api/reports/script")
def script(kind: str = "weekly", week: str | None = None, sprint_id: int | None = None, audience: str = "leadership",
           viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    from .reports import _parse, build_sprint, build_weekly

    if viewer.floor != Level.PRIVATE:
        raise HTTPException(403, "Hidden while presenting.")
    if kind == "sprint":
        if sprint_id is None:
            raise HTTPException(400, "Pick a sprint.")
        rep = build_sprint(conn, sprint_id, audience)
    else:
        rep = build_weekly(conn, _parse(week, "week"), audience)
    return {"title": rep["title"] + ": video script", "markdown": report_script(rep["markdown"], rep["title"], kind)}
