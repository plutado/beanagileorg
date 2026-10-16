from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings

from . import models
from .messaging import router as messaging_router
from .routes import router

NAV = [
    {"path": "/this-week", "label": "This week"},
    {"group": "Messages"},
    {"path": "/messages", "label": "Messages"},
    {"path": "/templates", "label": "Templates"},
    {"path": "/calendar", "label": "Comms calendar"},
    {"path": "/sent", "label": "Sent log"},
    {"path": "/audiences", "label": "Audiences and channels"},
    {"path": "/plain-language", "label": "Plain language"},
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
        routers=[
            messaging_router,
            router,
            *(r.router() for r in (models.decks, models.slides, models.media, models.messages, models.templates,
                                   models.audiences, models.channels, models.cadences, models.glossary)),
        ],
        static_dir=Path(__file__).parent / "static",
    )
