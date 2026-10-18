from pathlib import Path

from beanagileorg.core.app import create_app
from beanagileorg.core.config import Settings

from . import models
from .messaging import router as messaging_router
from .routes import router
from .versions import router as versions_router
from .visuals import router as visuals_router
from beanagileorg.core.ask import AskApp, build_router as build_ask_router
from beanagileorg.core.help import COMMS

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
    {"path": "/infographics", "icon": "chart-column", "label": "Infographics"},
    {"path": "/media", "icon": "film", "label": "Media library"},
    {"group": "Me"},
    {"path": "/connections", "icon": "send", "label": "Connections"},
    {"path": "/help", "icon": "circle-help", "label": "Help"},
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
            versions_router,
            visuals_router,
            build_ask_router(lambda: AskApp(name="Comms studio", sections=[{"path": i["path"], "label": i["label"], "purpose": COMMS.get(i["path"], {}).get("purpose", "")} for i in NAV if i.get("path")], links={"message": "/messages/{id}", "deck": "/decks/{id}", "infographic": "/infographics"})),
            router,
            *(r.router() for r in (models.decks, models.slides, models.media, models.infographics, models.messages, models.templates,
                                   models.audiences, models.channels, models.cadences, models.glossary)),
        ],
        static_dir=Path(__file__).parent / "static",
    )
