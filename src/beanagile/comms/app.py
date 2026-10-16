from pathlib import Path

from beanagile.core.app import create_app
from beanagile.core.config import Settings

from . import models
from .messaging import router as messaging_router
from .routes import router

NAV = [
    {"path": "/this-week", "icon": "calendar-clock", "label": "This week"},
    {"group": "Messages"},
    {"path": "/messages", "icon": "mail", "label": "Messages"},
    {"path": "/templates", "icon": "layout-template", "label": "Templates"},
    {"path": "/calendar", "icon": "calendar-days", "label": "Comms calendar"},
    {"path": "/sent", "icon": "send", "label": "Sent log"},
    {"path": "/audiences", "icon": "users", "label": "Audiences and channels"},
    {"path": "/plain-language", "icon": "spell-check", "label": "Plain language"},
    {"group": "Presentations"},
    {"path": "/decks", "icon": "presentation", "label": "Decks"},
    {"path": "/media", "icon": "film", "label": "Media library"},
    {"group": "Me"},
    {"path": "/settings", "icon": "settings", "label": "Settings"},
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
