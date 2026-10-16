"""Comms studio tables: decks, slides and the media library."""

from beanagile.core.privacy import Level
from beanagile.core.records import Field, Record

S, P = Level.PRESENTABLE, Level.PRIVATE

LAYOUTS = (
    "title", "section", "big-number", "bullets", "quote", "comparison",
    "image", "video", "audio", "lottie", "closing",
)
TRANSITIONS = ("none", "fade", "slide", "convex", "concave", "zoom")
MEDIA_KINDS = ("video", "audio", "image", "lottie", "captions")
MEDIA_SOURCES = ("mine", "licensed", "placeholder")

MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE decks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            theme TEXT NOT NULL DEFAULT 'beanagile',
            transition TEXT NOT NULL DEFAULT 'slide',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE slides (
            id INTEGER PRIMARY KEY,
            deck_id INTEGER NOT NULL REFERENCES decks (id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0,
            layout TEXT NOT NULL,
            content TEXT,
            notes TEXT,
            transition TEXT,
            hidden INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX slides_deck ON slides (deck_id, position);
        CREATE TABLE media (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            mime TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            source TEXT NOT NULL DEFAULT 'mine',
            license_ref TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
]

# Decks are made to be shown, so their content is presentable. Speaker notes are presentable too:
# they never render on a slide, and the speaker view needs them while presenting.
decks = Record(
    entity="deck",
    table="decks",
    path="/api/decks",
    order_by="id DESC",
    fields={
        "title": Field("text", S, required=True),
        "theme": Field("text", S, default="beanagile"),
        "transition": Field("text", S, choices=TRANSITIONS, default="slide"),
    },
    computed={"slide_count": ("(SELECT COUNT(*) FROM slides s WHERE s.deck_id = decks.id)", S)},
)

slides = Record(
    entity="slide",
    table="slides",
    path="/api/slides",
    order_by="deck_id, position, id",
    fields={
        "deck_id": Field("int", S, required=True),
        "position": Field("int", S, default=0),
        "layout": Field("text", S, required=True, choices=LAYOUTS),
        "content": Field("json", S, default={}),
        "notes": Field("text", S),
        "transition": Field("text", S, choices=TRANSITIONS),
        "hidden": Field("bool", S, default=False),
    },
)

media = Record(
    entity="media",
    table="media",
    path="/api/media",
    order_by="id DESC",
    fields={
        "kind": Field("text", S, required=True, choices=MEDIA_KINDS),
        "name": Field("text", S, required=True),
        "file_name": Field("text", S, required=True),
        "mime": Field("text", S, required=True),
        "size_bytes": Field("int", S, required=True),
        "source": Field("text", S, choices=MEDIA_SOURCES, default="mine"),
        "license_ref": Field("text", P),
    },
)
