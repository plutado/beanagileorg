from pathlib import Path

from beanagileorg.core.app import create_app
from beanagileorg.core.config import Settings
from beanagileorg.core.privacy import Level

from . import models
from .planning import router as planning_router
from .plans import router as plans_router
from .landscape import router as landscape_router
from .qa import router as qa_router
from .architecture import router as architecture_router
from .onboarding import router as onboarding_router
from .sdlc import router as sdlc_router
from .coaching import router as coaching_router, seed_once
from .debt import router as debt_router
from .jira import router as jira_router
from .sprint_planning import router as sprint_planning_router
from .teams import router as teams_router
from .people_crm import router as people_crm_router
from .culture import router as culture_router
from .reports import router as reports_router
from .changes import router as changes_router
from .first90 import router as first90_router
from .mandates import router as mandates_router
from .accelerate import router as accelerate_router
from .devsync import router as devsync_router
from .ask_info import info as ask_info
from beanagileorg.core.ask import build_router as build_ask_router
from .reporting import router as reporting_router
from .routes import router

NAV = [
    {"path": "/today", "icon": "sun", "label": "Today"},
    {"path": "/search", "icon": "search", "label": "Search"},
    {"group": "Team"},
    {"path": "/people", "icon": "users", "label": "People"},
    {"path": "/culture", "icon": "heart-handshake", "label": "Culture and trust"},
    {"path": "/first90", "icon": "calendar-days", "label": "First 90 days"},
    {"path": "/onboarding", "icon": "list-checks", "label": "Onboarding"},
    {"path": "/skills", "icon": "graduation-cap", "label": "Skills and learning"},
    {"path": "/listening", "icon": "messages-square", "label": "Listening tour"},
    {"path": "/rollup", "icon": "chart-column", "label": "Day-30 rollup"},
    {"group": "Across teams"},
    {"path": "/teams", "icon": "users-round", "label": "Teams"},
    {"path": "/sos", "icon": "network", "label": "Scrum of Scrums"},
    {"group": "Delivery"},
    {"path": "/sdlc", "icon": "git-branch", "label": "SDLC"},
    {"path": "/planning", "icon": "list-ordered", "label": "Sprint planning"},
    {"path": "/changes", "icon": "arrow-left-right", "label": "Change requests"},
    {"path": "/sprints", "icon": "notebook-pen", "label": "Sprint notebook"},
    {"path": "/retros", "icon": "refresh-ccw", "label": "Retrospectives"},
    {"path": "/pi", "icon": "kanban", "label": "PI planning"},
    {"path": "/roadmap", "icon": "map", "label": "Roadmap"},
    {"path": "/raci", "icon": "grid-3x3", "label": "RACI"},
    {"path": "/debt", "icon": "wrench", "label": "Tech debt"},
    {"path": "/risks", "icon": "triangle-alert", "label": "Risks and decisions"},
    {"path": "/metrics", "icon": "gauge", "label": "Metrics"},
    {"path": "/qa", "icon": "flask-conical", "label": "QA resources"},
    {"path": "/dev-sync", "icon": "list-checks", "label": "Dev-sync log"},
    {"path": "/learning", "icon": "presentation", "label": "Group learning"},
    {"path": "/vendors", "icon": "handshake", "label": "Vendors"},
    {"group": "Reporting"},
    {"path": "/plans", "icon": "flag", "label": "30/60/90 plans"},
    {"path": "/status", "icon": "file-text", "label": "Reports"},
    {"group": "Knowledge"},
    {"path": "/architecture", "icon": "network", "label": "Architecture and tools"},
    {"path": "/landscape", "icon": "building-2", "label": "Business landscape"},
    {"path": "/escalation", "icon": "siren", "label": "Escalation playbook"},
    {"group": "Me"},
    {"path": "/coaching", "icon": "compass", "label": "Coaching"},
    {"path": "/me", "icon": "user-round", "label": "My development"},
    {"path": "/help", "icon": "circle-help", "label": "Help"},
    {"path": "/settings", "icon": "settings", "label": "Settings"},
]

# Write scope for agents that update delivery records; it reads presentable fields.
SCOPES = {"delivery:write": Level.PRESENTABLE}


def build(settings: Settings | None = None):
    settings = settings or Settings(app="toolkit", title="Toolkit", port=8801)
    app = create_app(
        settings,
        nav=NAV,
        migrations=models.MIGRATIONS,
        routers=[router, reporting_router, planning_router, plans_router, landscape_router, qa_router, architecture_router, onboarding_router, sdlc_router, coaching_router, debt_router, jira_router, sprint_planning_router, teams_router, people_crm_router, culture_router, reports_router, changes_router, first90_router, mandates_router, accelerate_router, devsync_router, build_ask_router(lambda: ask_info(NAV)), *(record.router() for record in models.RECORDS)],
        static_dir=Path(__file__).parent / "static",
        scopes=SCOPES,
    )
    with app.state.db.session() as conn:
        seed_once(conn)
    return app
