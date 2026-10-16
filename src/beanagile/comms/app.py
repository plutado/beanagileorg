from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings

from . import models
from .routes import router

NAV = [
    {"path": "/this-week", "label": "This week"},
    {"group": "Presentations"},
    {"path": "/decks", "label": "Decks"},
    {"path": "/media", "label": "Media library"},
    {"group": "Me"},
    {"path": "/settings", "label": "Settings"},
]


def build(settings: Settings | None = None):
    settings = settings or Settings(app="comms", title="Comms studio", port=8802)
    return create_app(
        settings,
        nav=NAV,
        migrations=models.MIGRATIONS,
        # Custom routes first, so /api/media/upload isn't read as a media id.
        routers=[router, models.decks.router(), models.slides.router(), models.media.router()],
        static_dir=Path(__file__).parent / "static",
    )
