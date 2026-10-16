from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings

NAV = [
    {"path": "/this-week", "label": "This week"},
    {"group": "Me"},
    {"path": "/settings", "label": "Settings"},
]

MIGRATIONS: list[tuple[int, str]] = []


def build(settings: Settings | None = None):
    settings = settings or Settings(app="comms", title="Comms studio", port=8802)
    return create_app(settings, nav=NAV, migrations=MIGRATIONS, static_dir=Path(__file__).parent / "static")
