"""Find everything in the toolkit that references a Jira key, across every record that holds one."""

from fastapi import APIRouter, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer
from beanagileorg.core.records import ISSUE_KEY_RE

from . import models

router = APIRouter()

# record, the field that names it, the section it lives in, and how to link to it
SOURCES = [
    (models.action_items, "concern", "Dev-sync item", lambda r: f"/dev-sync/{r['id']}"),
    (models.retro_commitments, "commitment", "Retro commitment", lambda r: f"/retros/{r['retro_id']}"),
    (models.risks, "title", "Risk", lambda r: "/risks"),
    (models.decisions_needed, "decision", "Decision needed", lambda r: "/risks"),
    (models.roadmap_items, "title", "Roadmap item", lambda r: "/roadmap"),
    (models.test_cases, "title", "Test case", lambda r: "/qa/library"),
    (models.test_results, "notes", "Test result", lambda r: f"/qa/run-{r['run_id']}"),
    (models.incidents, "summary", "Incident", lambda r: "/escalation"),
    (models.onboarding_tasks, "title", "Onboarding item", lambda r: f"/onboarding/{r['onboarding_id']}"),
    (models.vendor_concerns, "title", "Vendor concern", lambda r: f"/vendors/{r['vendor_id']}"),
    (models.arch_decisions, "title", "Architecture decision", lambda r: "/architecture/decisions"),
    (models.tech_debt, "title", "Tech debt", lambda r: "/debt"),
    (models.sos_items, "question", "ART sync item", lambda r: "/sos"),
    (models.backlog_items, "title", "Backlog story", lambda r: f"/planning/{r['sprint_id']}" if r.get("sprint_id") else "/planning"),
    (models.epics, "title", "Epic", lambda r: "/pi"),
    (models.features, "title", "Feature", lambda r: f"/pi/{r['pi_id']}" if r.get("pi_id") else "/pi"),
    (models.stories, "title", "Story", lambda r: "/pi"),
]


@router.get("/api/jira/{key}")
def find(key: str, viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    key = key.strip().upper()
    if not ISSUE_KEY_RE.match(key):
        raise HTTPException(400, "That doesn't look like a Jira key such as ABC-123.")
    found = []
    for record, name_field, kind, link in SOURCES:
        col = "jira_keys" if "jira_keys" in record.fields else "jira_key" if "jira_key" in record.fields else "ticket_key"
        where = f"{col} LIKE ?" if col == "jira_keys" else f"{col} = ?"
        arg = f'%"{key}"%' if col == "jira_keys" else key
        for r in record.visible_all(record.fetch_all(conn, where, (arg,)), viewer):
            found.append({"kind": kind, "title": r.get(name_field) or r.get("title") or kind, "route": link(r)})
    return {"key": key, "found": found}
