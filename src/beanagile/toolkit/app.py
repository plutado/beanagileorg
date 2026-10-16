from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings
from beanagile.core.privacy import Level

from . import models
from .routes import router

NAV = [
    {"path": "/today", "icon": "sun", "label": "Today"},
    {"group": "Team"},
    {"path": "/people", "icon": "users", "label": "People"},
    {"path": "/skills", "icon": "graduation-cap", "label": "Skills and learning"},
    {"path": "/listening", "icon": "messages-square", "label": "Listening tour"},
    {"path": "/rollup", "icon": "chart-column", "label": "Day-30 rollup"},
    {"group": "Delivery"},
    {"path": "/dev-sync", "icon": "list-checks", "label": "Dev-sync log"},
    {"path": "/learning", "icon": "presentation", "label": "Group learning"},
    {"path": "/vendors", "icon": "handshake", "label": "Vendors"},
    {"group": "Knowledge"},
    {"path": "/escalation", "icon": "siren", "label": "Escalation playbook"},
    {"group": "Me"},
    {"path": "/me", "icon": "user-round", "label": "My development"},
    {"path": "/settings", "icon": "settings", "label": "Settings"},
]

# Write scope for agents that update delivery records; it reads presentable fields.
SCOPES = {"delivery:write": Level.PRESENTABLE}


def build(settings: Settings | None = None):
    settings = settings or Settings(app="toolkit", title="Toolkit", port=8801)
    return create_app(
        settings,
        nav=NAV,
        migrations=models.MIGRATIONS,
        routers=[router, *(record.router() for record in models.RECORDS)],
        static_dir=Path(__file__).parent / "static",
        scopes=SCOPES,
    )
