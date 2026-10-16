from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings
from beanagile.core.privacy import Level

from . import models
from .routes import router

NAV = [
    {"path": "/today", "label": "Today"},
    {"group": "Team"},
    {"path": "/people", "label": "People"},
    {"path": "/skills", "label": "Skills and learning"},
    {"path": "/listening", "label": "Listening tour"},
    {"path": "/rollup", "label": "Day-30 rollup"},
    {"group": "Delivery"},
    {"path": "/dev-sync", "label": "Dev-sync log"},
    {"path": "/learning", "label": "Group learning"},
    {"group": "Knowledge"},
    {"path": "/escalation", "label": "Escalation playbook"},
    {"group": "Me"},
    {"path": "/me", "label": "My development"},
    {"path": "/settings", "label": "Settings"},
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
