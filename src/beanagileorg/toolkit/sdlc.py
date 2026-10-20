"""The SDLC: lifecycle stages with entry and exit criteria, environments and the promotion path, and policies."""

from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.export import log_export
from beanagileorg.core.privacy import Level, Viewer

from . import models
from .routes import require_write

router = APIRouter()
ENTITIES = ("sdlc_stage", "sdlc_environment", "sdlc_policy")

# Generic Scrum practice. Anything that depends on how the company works is a [Placeholder] for the team to settle,
# and every policy starts as a draft. The Salesforce and MuleSoft pack swaps in sandbox-based environments and wording.
SALESFORCE_STAGES = [
    ("Intake", "Capture a need and decide whether it belongs on the backlog.",
     ["Someone can describe the problem and who has it"], ["Item is on the backlog with a clear title and a requester", "Product manager has set a rough priority"],
     "Write the problem, not the solution, as a Jira issue. Link the request, incident or idea it came from.", "Requester, product manager", "Jira issue on the backlog", ""),
    ("Refinement", "Make the item ready to build: understood, small enough, testable.",
     ["Item is near the top of the backlog"], ["Meets the definition of ready", "Acceptance criteria written and agreed", "Estimated by the team", "Dependencies and risks noted"],
     "Discuss with the team, split anything bigger than a few days, agree acceptance criteria with QA in the room.", "Product manager, developers, QA, architect when needed", "Jira story with acceptance criteria and an estimate", ""),
    ("Design", "Decide how to build it when the change touches architecture, data or integrations.",
     ["Story is refined", "The change touches integrations, the data model, security or more than one system"], ["Approach agreed with the architect", "An architecture decision record written for significant choices"],
     "Sketch the approach, check it against the system map, record the decision.", "Developer, architect", "Design notes, architecture decision record", "#/architecture/decisions"),
    ("Build", "Write the change and its automated tests in your own developer sandbox.",
     ["Story is in the sprint", "Design agreed if one was needed"], ["Changes retrieved from the developer sandbox into the story's branch", "Unit tests written and passing", "Works in the developer sandbox"],
     "Work in a branch named for the Jira key, such as ABC-123-short-name, so Bitbucket and Jira link up. Keep metadata and configuration in source control, not only in an org.", "Developers", "Branch, unit tests", ""),
    ("Code review", "A second developer checks the change before it merges.",
     ["Pull request open with a description and the Jira key in its title", "Automated checks passing"], ["At least one approval", "Comments resolved", "Merged, and deployed to the shared sandbox with everyone else's work"],
     "Review for correctness, tests, security, naming and fit with the architecture.", "Developers", "Approved pull request", ""),
    ("Test", "Prove the change works and didn't break anything.",
     ["Change is in the QA sandbox, on the release branch"], ["Acceptance criteria verified", "Affected smoke tests pass", "Defects fixed or logged with agreement", "QA sign-off recorded"],
     "Run the acceptance tests and the smoke tests for the affected area. Defects are logged in Jira and linked to the story; blockers go to the dev-sync log.", "QA, developers", "Test run results, QA sign-off", "#/qa"),
    ("User acceptance", "The business confirms the change does what they need.",
     ["QA sign-off", "[Placeholder: where user acceptance happens, if not the QA sandbox]"], ["Product manager or business owner accepts the story"],
     "Demo or hand over for user testing. Feedback either passes or becomes a new story.", "Product manager, business users", "Acceptance", ""),
    ("Release", "Move the change to production safely.",
     ["Accepted", "Release notes written", "Go/no-go decision made", "Not inside a freeze window, or an exception approved"], ["Deployed to production", "Post-release smoke tests pass", "Release announced"],
     "Follow the release checklist. Have a rollback plan. Run the regression plan for platform releases and peak-season changes.", "Release owner, developers, QA", "Release notes, deployment record", "#/qa/regression"),
    ("Support and learn", "Watch the change in production and learn from it.",
     ["Change is live"], ["No open incidents caused by the change", "Lessons taken to the retro"],
     "Monitor, handle incidents through the escalation playbook, and bring what we learned to the retro.", "Team, support", "Incident records, retro notes", "#/escalation"),
]
# Salesforce Core works by sandboxes, not Git flow or feature-branch flow: each developer builds in their own sandbox,
# merged work lands in a shared sandbox, then QA, then production. Branch names stay placeholders until confirmed.
# Sandbox types follow Salesforce's org development model (Trailhead): Developer sandboxes for each developer, a
# Developer Pro sandbox for integration, a Partial Copy sandbox for testing, and a Full sandbox for staging and training.
# (platform, name, purpose, data, deploys_by, refresh, branch, deploy_method)
SALESFORCE_ENVIRONMENTS = [
    ("Salesforce", "Developer sandboxes", "One per developer (Developer sandbox type): build and unit test a story in isolation.", "No production data", "Each developer", "Can refresh daily",
     "[Placeholder: a branch per story, named with the Jira key]", "[Placeholder: how changes are retrieved from the sandbox into the branch]"),
    ("Salesforce", "Integration sandbox (Developer Pro)", "Where merged work lands: every developer's changes together, so they're tested side by side.", "Configuration and seeded test data, no production data",
     "[Placeholder: pipeline or release owner]", "Can refresh daily", "[Placeholder: integration branch]", "[Placeholder: deployed when a pull request merges]"),
    ("Salesforce", "QA sandbox (Partial Copy)", "QA testing, regression and user acceptance of what's going into the next release.", "A sample of production data chosen by a sandbox template [Placeholder: masking]", "[Placeholder]", "Every 5 days at most",
     "[Placeholder: release branch]", "[Placeholder]"),
    ("Salesforce", "Full sandbox", "A full copy of production for staging, performance and load testing, and training.", "Full production data copy", "[Placeholder]", "Every 29 days at most",
     "", "[Placeholder]"),
    ("Salesforce", "Production", "Live.", "Production data", "[Placeholder: release owner]", "n/a", "[Placeholder: main branch]", "[Placeholder: deployed after the go/no-go]"),
    ("MuleSoft", "[Placeholder: to confirm whether MuleSoft is developed on or mainly used to connect third-party systems]", "[Placeholder]", "[Placeholder]", "[Placeholder]", "n/a", "", ""),
]
SALESFORCE_STAGE_ENVIRONMENTS = {"Build": "Developer sandbox", "Code review": "Integration sandbox (Developer Pro), after merge", "Test": "QA sandbox (Partial Copy)",
                      "User acceptance": "[Placeholder]", "Release": "Production"}
SALESFORCE_POLICIES = [
    ("branching", "Branching and merging", "Branch and commit names start with the Jira key, so work in Bitbucket shows up on the Jira issue. [Placeholder: the branching model in Bitbucket, for example short-lived feature branches merged to a main branch.]"),
    ("code review", "Code review", "Every change is reviewed by at least one other developer before it merges. [Placeholder: who can approve, and what reviewers check.]"),
    ("testing", "Testing and the definition of done", "A story is done only when it meets the definition of done, including QA sign-off. See the definition of done under QA resources."),
    ("release", "Release and go/no-go", "[Placeholder: release cadence, who decides go/no-go, and the release checklist.] The RACI lists who is accountable."),
    ("change management", "Production changes and approvals", "[Placeholder: which changes need approval before production, and from whom.]"),
    ("hotfix", "Hotfixes", "[Placeholder: when a fix can skip the normal cycle, who approves it, and how it is merged back.]"),
    ("release", "Freeze windows", "[Placeholder: peak-season and platform-release freeze dates, and how to ask for an exception.]"),
    ("branching", "Sandbox workflow", "Salesforce work moves through sandboxes rather than Git flow or feature-branch flow: each developer builds in their own sandbox, changes go into a branch for the story and a pull request, merged work is deployed to the integration sandbox (Developer Pro), the release is tested in the QA sandbox (Partial Copy), and production is deployed after the go/no-go. [Placeholder: how metadata moves between sandboxes and Bitbucket, branch names, who deploys each step, and how sandboxes are refreshed.]"),
    ("communication", "When we miss a sprint commitment", "Within a day of the sprint review, a short written or recorded note goes to [Placeholder: stakeholders and leadership]: what we committed, what we finished, why the gap, what we're changing, and the new forecast. The team discusses it at the retro, without blame."),
    ("communication", "When a release breaks production", "Fix first, then tell. A first note within [Placeholder: 30 minutes] to [Placeholder: who], updates every [Placeholder: hour] until it's resolved, then a blameless review within two working days: what happened, the impact, why testing didn't catch it, and what changes. Follows the escalation playbook."),
    ("communication", "When a risk becomes likely", "The owner adds it to the risk log the same day, with a next step and a date. It stays in the weekly report until it's closed or accepted, and leadership hears about it before it becomes a surprise."),
    ("data", "Test data", "[Placeholder: what data each environment may hold, and how production data is masked.]"),
]


_GENERIC_STAGE_TEXT = {
    "Build": ("Build", "Write the change and its automated tests in your own development environment.",
              ["Story is in the sprint", "Design agreed if one was needed"], ["Changes committed to the story's branch", "Unit tests written and passing", "Works in your development environment"],
              "Work in a branch named for the Jira key, such as ABC-123-short-name, so source control and Jira link up. Keep configuration in source control too.", "Developers", "Branch, unit tests", ""),
}


def _generic_stage(stage: tuple) -> tuple:
    if stage[0] in _GENERIC_STAGE_TEXT:
        return _GENERIC_STAGE_TEXT[stage[0]]
    swap = lambda v: [x.replace("the shared sandbox", "the shared integration environment").replace("the QA sandbox", "the QA environment") for x in v] if isinstance(v, list) else v
    return tuple(swap(v) for v in stage)


STARTER_STAGES = [_generic_stage(st) for st in SALESFORCE_STAGES]
# (platform, name, purpose, data, deploys_by, refresh, branch, deploy_method)
STARTER_ENVIRONMENTS = [
    ("Application", "Local development", "Each developer builds and tests a story in isolation.", "No production data", "Each developer", "n/a",
     "[Placeholder: a branch per story, named with the Jira key]", ""),
    ("Application", "Integration", "Where merged work lands and automated checks run, so everyone's changes are tested together.", "Seeded test data, no production data",
     "[Placeholder: the pipeline or release owner]", "[Placeholder]", "[Placeholder: main or integration branch]", "[Placeholder: deployed when a pull request merges]"),
    ("Application", "QA", "QA testing, regression and user acceptance of what's going into the next release.", "[Placeholder: test data, masked if copied from production]",
     "[Placeholder]", "[Placeholder]", "[Placeholder: release branch]", "[Placeholder]"),
    ("Application", "Staging", "A production-like environment for final checks, performance testing and training.", "[Placeholder]", "[Placeholder]", "[Placeholder]", "", "[Placeholder]"),
    ("Application", "Production", "Live.", "Production data", "[Placeholder: release owner]", "n/a", "[Placeholder: main branch]", "[Placeholder: deployed after the go/no-go]"),
]
STAGE_ENVIRONMENTS = {"Build": "Local development", "Code review": "Integration, after merge", "Test": "QA", "User acceptance": "[Placeholder]", "Release": "Production"}
STARTER_POLICIES = [
    (c, t, b.replace("work in Bitbucket", "work in source control").replace("the branching model in Bitbucket", "the branching model"))
    for c, t, b in SALESFORCE_POLICIES if t != "Sandbox workflow"
] + [("branching", "Environments and promotion", "Work moves through the environments in order: local development, integration, QA, staging, then production. [Placeholder: how a change is promoted, and who can deploy to each environment.]")]


def starter_content(conn) -> tuple:
    from .routes import platform

    if platform(conn) == "salesforce":
        return SALESFORCE_STAGES, SALESFORCE_ENVIRONMENTS, SALESFORCE_STAGE_ENVIRONMENTS, SALESFORCE_POLICIES
    return STARTER_STAGES, STARTER_ENVIRONMENTS, STAGE_ENVIRONMENTS, STARTER_POLICIES


@router.post("/api/sdlc/starter", status_code=201)
def starter(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if conn.execute("SELECT (SELECT COUNT(*) FROM sdlc_stages) + (SELECT COUNT(*) FROM sdlc_environments) + (SELECT COUNT(*) FROM sdlc_policies)").fetchone()[0]:
        raise HTTPException(409, "The SDLC already has content. Edit it instead.")
    stages_, environments, stage_envs, policies = starter_content(conn)
    for pos, (name, purpose, entry, exit_, activities, roles, artifacts, links) in enumerate(stages_):
        models.sdlc_stages.create(conn, {"name": name, "position": pos, "purpose": purpose, "entry_criteria": entry, "exit_criteria": exit_,
                                         "activities": activities, "roles": roles, "artifacts": artifacts, "links": links or None,
                                         "environment": stage_envs.get(name)}, viewer.source)
    for pos, (platform, name, purpose, data, deploys, refresh, branch, method) in enumerate(environments):
        models.sdlc_environments.create(conn, {"platform": platform, "name": name, "position": pos, "purpose": purpose, "data": data, "deploys_by": deploys,
                                               "refresh": refresh, "branch": branch or None, "deploy_method": method or None}, viewer.source)
    for category, title, body in policies:
        models.sdlc_policies.create(conn, {"category": category, "title": title, "body": body}, viewer.source)
    return {"stages": len(stages_), "environments": len(environments), "policies": len(policies)}


@router.post("/api/sdlc-stages/{stage_id}/move")
def move(stage_id: int, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Swap a stage with its neighbour, then renumber so positions stay 0, 1, 2..."""
    require_write(viewer)
    stages = models.sdlc_stages.fetch_all(conn)
    ids = [s["id"] for s in stages]
    if stage_id not in ids:
        raise HTTPException(404, "No such stage.")
    i = ids.index(stage_id)
    j = i + (1 if body.get("direction") == "down" else -1)
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
    for pos, sid in enumerate(ids):
        if next(s for s in stages if s["id"] == sid)["position"] != pos:
            models.sdlc_stages.update(conn, sid, {"position": pos}, viewer.source)
    return [s["id"] for s in models.sdlc_stages.fetch_all(conn)]


def _build(conn, viewer: Viewer) -> dict:
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM systems")}
    stages = [{**s, "systems": [names[i] for i in s["system_ids"] if i in names]} for s in models.sdlc_stages.visible_all(models.sdlc_stages.fetch_all(conn), viewer)]
    envs = models.sdlc_environments.visible_all(models.sdlc_environments.fetch_all(conn), viewer)
    platforms = {}
    for e in envs:
        platforms.setdefault(e["platform"] or "Other", []).append(e)
    return {"stages": stages, "environments": [{"platform": p, "environments": l} for p, l in platforms.items()],
            "policies": models.sdlc_policies.visible_all(models.sdlc_policies.fetch_all(conn), viewer)}


@router.get("/api/sdlc")
def overview(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    data = _build(conn, viewer)
    if viewer.floor == Level.PRIVATE:
        rows = conn.execute(
            f"SELECT at, entity, record_id, field, source FROM change_log WHERE entity IN ({','.join('?' * len(ENTITIES))}) ORDER BY id DESC LIMIT 30", ENTITIES
        ).fetchall()
        data["history"] = [dict(r) for r in rows]
    return data


def build_document(conn) -> dict:
    exporter = Viewer(floor=Level.EXPORTABLE, source="sdlc", scopes=frozenset({"export:read"}))
    d = _build(conn, exporter)
    lines = ["# How we deliver: our SDLC", ""]
    if d["stages"]:
        lines += ["Work moves through these stages: " + " → ".join(s["name"] for s in d["stages"]) + ".", ""]
    for n, s in enumerate(d["stages"], 1):
        lines += [f"## {n}. {s['name']}", ""]
        if s["purpose"]:
            lines += [s["purpose"], ""]
        if s["entry_criteria"]:
            lines += ["**Starts when**", ""] + [f"- {c}" for c in s["entry_criteria"]] + [""]
        if s["activities"]:
            lines += ["**What happens**", "", s["activities"], ""]
        if s["exit_criteria"]:
            lines += ["**Done when**", ""] + [f"- [ ] {c}" for c in s["exit_criteria"]] + [""]
        extra = [f"Who: {s['roles']}" if s["roles"] else "", f"Produces: {s['artifacts']}" if s["artifacts"] else "",
                 f"Environment: {s['environment']}" if s["environment"] else "", f"Tools: {', '.join(s['systems'])}" if s["systems"] else "",
                 f"Typical time: {s['duration']}" if s["duration"] else ""]
        if any(extra):
            lines += [" · ".join(x for x in extra if x), ""]
    if d["environments"]:
        lines += ["## Environments", ""]
        for group in d["environments"]:
            lines += [f"### {group['platform']}", "", " → ".join(e["name"] for e in group["environments"]), ""]
            lines += ["| Environment | Purpose | Branch | How changes arrive | Data | Who deploys | Refresh |", "| --- | --- | --- | --- | --- | --- | --- |"]
            lines += [f"| {e['name']} | {e['purpose'] or ''} | {e.get('branch') or ''} | {e.get('deploy_method') or ''} | {e['data'] or ''} | {e['deploys_by'] or ''} | {e['refresh'] or ''} |" for e in group["environments"]] + [""]
    live = [p for p in d["policies"] if p["status"] != "retired"]
    if live:
        lines += ["## Policies", ""]
        for p in live:
            lines += [f"### {p['title']}" + (" (draft)" if p["status"] == "draft" else ""), "", p["body"] or "", ""]
    return {"title": "How we deliver: our SDLC", "markdown": "\n".join(lines).rstrip() + "\n"}


@router.post("/api/sdlc/versions", status_code=201)
def save_version(body: dict = Body(default={}), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Keep the SDLC document as it stands now, for example when a policy is agreed."""
    require_write(viewer)
    doc = build_document(conn)
    last = models.sdlc_versions.fetch_all(conn)
    if last and last[0]["markdown"].strip() == doc["markdown"].strip():
        return {**last[0], "unchanged": True}
    return models.sdlc_versions.create(conn, {"taken_on": date.today().isoformat(), "reason": (body.get("reason") or None) and str(body["reason"])[:200],
                                              "markdown": doc["markdown"]}, viewer.source)


@router.get("/api/sdlc/document")
def document(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    return build_document(conn)


@router.post("/api/sdlc/document/export")
def export_document(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    out = build_document(conn)
    log_export(conn, "sdlc:markdown", out["title"], [{"markdown": out["markdown"]}], viewer.source)
    return out
