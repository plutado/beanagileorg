"""What Ask needs to know about the toolkit: its sections, where each kind of record opens, and two extra tools."""

from beanagileorg.core.ask import AskApp
from beanagileorg.core.help import TOOLKIT
from beanagileorg.core.privacy import Level

# Where a cited record opens in the toolkit.
LINKS = {
    "person": "/people/{id}", "action_item": "/dev-sync/{id}", "change_request": "/changes/{id}", "mandate": "/first90/mandate/{id}",
    "retro": "/retros/{id}", "onboarding": "/onboarding/{id}", "risk": "/risks", "decision_needed": "/risks", "roadmap_item": "/roadmap",
    "backlog_item": "/planning", "sprint": "/sprints", "sos_item": "/sos", "team": "/teams", "tech_debt": "/debt", "vendor": "/vendors",
    "alignment_check": "/alignment", "core_process": "/processes/{id}", "skill_gap": "/skills", "criteria_profile": "/me/criteria", "team_goal": "/team-align", "alliance_plan": "/alliances/{id}", "release": "/releases/{id}", "influence_link": "/alliances", "power_coalition": "/alliances", "role_template": "/first90/team", "team_assessment": "/first90/team", "knowledge_source": "/skills", "culture_observation": "/culture/noticing", "culture_read": "/culture/map", "glossary_term": "/culture/glossary", "behavior_target": "/culture/behaviors", "preference_assessment": "/me/preferences", "trust_pulse": "/culture/pulse", "team_agreement": "/culture/agreements", "standard": "/culture/standards",
    "log_entry": "/status/log", "report": "/status/saved", "team_change": "/first90/changes", "learning_question": "/first90/learning",
    "situation": "/first90/situation", "boss_conversation": "/first90/mandates", "mentoring_session": "/first90/mentoring", "mentored_practice": "/first90/mentoring",
    "plan": "/plans", "plan_item": "/plans", "interview": "/listening", "interaction": "/people", "commitment": "/people", "growth_goal": "/people",
    "manager_note": "/people", "learning_session": "/learning", "metric": "/metrics", "incident": "/escalation", "system": "/architecture",
    "integration": "/architecture", "arch_decision": "/architecture", "sdlc_policy": "/sdlc/policies", "sdlc_stage": "/sdlc", "sdlc_environment": "/sdlc/environments",
    "test_case": "/qa", "test_run": "/qa", "regression_plan": "/qa", "coaching_guide": "/coaching", "reflection": "/coaching/reflect",
}


def _today(conn, viewer, args):
    if viewer.floor != Level.PRIVATE:
        return "Today is private, so it isn't available here."
    from .routes import today_view

    return today_view(viewer=viewer, conn=conn)


def _weekly(conn, viewer, args):
    from datetime import date

    from .reports import build_weekly

    audience = "my manager" if viewer.floor <= Level.PRESENTABLE else "leadership"
    on = date.fromisoformat(args["week"]) if args.get("week") else date.today()
    return build_weekly(conn, on, audience)["markdown"]


def info(nav: list[dict]) -> AskApp:
    sections = [{"path": i["path"], "label": i["label"], "purpose": TOOLKIT.get(i["path"], {}).get("purpose", "")} for i in nav if i.get("path")]
    return AskApp(
        name="toolkit",
        sections=sections,
        links=LINKS,
        extra_tools=[
            {"name": "today", "description": "Everything that needs attention today or this week: overdue items, follow-ups, check-ins, reports due, culture and First 90 days nudges.",
             "parameters": {"type": "object", "properties": {}}, "run": _today},
            {"name": "weekly_report", "description": "The weekly report draft for a week (default this week): sprint progress, highlights, delivered, risks, decisions, next week.",
             "parameters": {"type": "object", "properties": {"week": {"type": "string", "description": "Any date in the week, YYYY-MM-DD"}}}, "run": _weekly},
        ],
    )
