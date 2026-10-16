from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings
from beanagile.core.privacy import Level

NAV = [
    {"path": "/today", "label": "Today"},
    {"group": "Me"},
    {"path": "/settings", "label": "Settings"},
]

MIGRATIONS: list[tuple[int, str]] = []

# Write scope for agents that update delivery records; it reads presentable fields.
SCOPES = {"delivery:write": Level.PRESENTABLE}


def build(settings: Settings | None = None):
    settings = settings or Settings(app="toolkit", title="Toolkit", port=8801)
    return create_app(
        settings,
        nav=NAV,
        migrations=MIGRATIONS,
        static_dir=Path(__file__).parent / "static",
        scopes=SCOPES,
    )
