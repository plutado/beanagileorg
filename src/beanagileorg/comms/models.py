"""Comms studio tables: decks, slides and the media library."""

from beanagileorg.core.privacy import Level
from beanagileorg.core.records import Field, Record

S, P, E = Level.PRESENTABLE, Level.PRIVATE, Level.EXPORTABLE

LAYOUTS = (
    "title", "section", "big-number", "bullets", "quote", "comparison",
    "image", "video", "audio", "lottie", "closing",
)
TRANSITIONS = ("none", "fade", "slide", "convex", "concave", "zoom")
MEDIA_KINDS = ("video", "audio", "image", "lottie", "captions")
MEDIA_SOURCES = ("mine", "licensed", "placeholder")

MESSAGE_TYPES = (
    "weekly note", "weekly status", "alert", "release notes", "stakeholder update",
    "decision announcement", "team announcement", "review", "memo", "other",
)
MESSAGE_STATES = ("draft", "in review", "ready", "sent", "archived")
DETAIL_LEVELS = ("summary first", "full detail", "technical", "what changes for them")
CHANNEL_KINDS = ("chat", "email", "meeting", "document", "other")
RHYTHMS = ("weekly", "every two weeks", "monthly", "quarterly")

DECK_STATUS = ("draft", "in review", "approved", "presented")

MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE decks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            theme TEXT NOT NULL DEFAULT 'beanagileorg',
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
    (
        2,
        """
        CREATE TABLE channels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'other',
            notes TEXT
        );
        CREATE TABLE audiences (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            needs TEXT,
            detail_level TEXT,
            channel_id INTEGER REFERENCES channels (id) ON DELETE SET NULL
        );
        CREATE TABLE templates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'other',
            body TEXT,
            audience_ids TEXT,
            channel_id INTEGER REFERENCES channels (id) ON DELETE SET NULL
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'other',
            body TEXT,
            state TEXT NOT NULL DEFAULT 'draft',
            audience_ids TEXT,
            channel_id INTEGER REFERENCES channels (id) ON DELETE SET NULL,
            template_id INTEGER REFERENCES templates (id) ON DELETE SET NULL,
            sent_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE message_versions (
            id INTEGER PRIMARY KEY,
            message_id INTEGER NOT NULL REFERENCES messages (id) ON DELETE CASCADE,
            body TEXT,
            saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        );
        CREATE TABLE cadences (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'other',
            rhythm TEXT NOT NULL DEFAULT 'weekly',
            next_due TEXT,
            lead_days INTEGER NOT NULL DEFAULT 2,
            template_id INTEGER REFERENCES templates (id) ON DELETE SET NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE comms_due (
            id INTEGER PRIMARY KEY,
            cadence_id INTEGER NOT NULL REFERENCES cadences (id) ON DELETE CASCADE,
            due TEXT NOT NULL,
            message_id INTEGER REFERENCES messages (id) ON DELETE SET NULL,
            UNIQUE (cadence_id, due)
        );
        CREATE TABLE sent_log (
            id INTEGER PRIMARY KEY,
            message_id INTEGER REFERENCES messages (id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            type TEXT,
            sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            channel TEXT,
            audiences TEXT,
            body TEXT,
            body_sha256 TEXT NOT NULL,
            checks TEXT,
            source TEXT NOT NULL
        );
        CREATE TABLE glossary (
            id INTEGER PRIMARY KEY,
            term TEXT NOT NULL,
            plain TEXT
        );
        """,
    ),
    (
        3,
        """
        ALTER TABLE decks ADD COLUMN status TEXT NOT NULL DEFAULT 'draft';
        ALTER TABLE decks ADD COLUMN audience TEXT;
        ALTER TABLE decks ADD COLUMN presented_on DATE;
        ALTER TABLE decks ADD COLUMN copied_from TEXT;
        CREATE TABLE deck_versions (
            id INTEGER PRIMARY KEY,
            deck_id INTEGER NOT NULL REFERENCES decks (id) ON DELETE CASCADE,
            number INTEGER NOT NULL,
            label TEXT,
            kind TEXT NOT NULL DEFAULT 'saved',
            status TEXT,
            note TEXT,
            snapshot TEXT NOT NULL,
            slide_count INTEGER,
            saved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
            source TEXT,
            UNIQUE (deck_id, number)
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
        "theme": Field("text", S, default="beanagileorg"),
        "transition": Field("text", S, choices=TRANSITIONS, default="slide"),
        "status": Field("text", S, choices=DECK_STATUS, default="draft"),
        "audience": Field("text", S),
        "presented_on": Field("date", S),
        "copied_from": Field("text", S),
    },
    computed={
        "slide_count": ("(SELECT COUNT(*) FROM slides s WHERE s.deck_id = decks.id)", S),
        "version_count": ("(SELECT COUNT(*) FROM deck_versions v WHERE v.deck_id = decks.id)", S),
        "latest_version": ("(SELECT MAX(number) FROM deck_versions v WHERE v.deck_id = decks.id)", S),
    },
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


# ---- version 1: messages, templates, audiences, channels, calendar, plain language ----

channels = Record(
    entity="channel",
    table="channels",
    path="/api/channels",
    order_by="name",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=CHANNEL_KINDS, default="other"),
        "notes": Field("text", P),
    },
)

audiences = Record(
    entity="audience",
    table="audiences",
    path="/api/audiences",
    order_by="name",
    fields={
        "name": Field("text", S, required=True),
        "needs": Field("text", S),
        "detail_level": Field("text", S, choices=DETAIL_LEVELS),
        "channel_id": Field("int", S),
    },
)

templates = Record(
    entity="template",
    table="templates",
    path="/api/templates",
    order_by="name",
    fields={
        "name": Field("text", S, required=True),
        "type": Field("text", S, choices=MESSAGE_TYPES, default="other"),
        "body": Field("text", S),
        "audience_ids": Field("ids", S),
        "channel_id": Field("int", S),
    },
)

# Drafts are private; a message becomes shareable once it has been sent.
messages = Record(
    entity="message",
    table="messages",
    path="/api/messages",
    order_by="CASE state WHEN 'draft' THEN 0 WHEN 'in review' THEN 1 WHEN 'ready' THEN 2 ELSE 3 END, id DESC",
    fields={
        "title": Field("text", E, required=True),
        "type": Field("text", E, choices=MESSAGE_TYPES, default="other"),
        "body": Field("text", E),
        "state": Field("text", E, choices=MESSAGE_STATES, default="draft"),
        "audience_ids": Field("ids", E),
        "channel_id": Field("int", E),
        "template_id": Field("int", E),
        "sent_at": Field("text", E),
    },
    ceiling_sql="CASE WHEN state IN ('sent', 'archived') THEN 2 ELSE 0 END",
)

cadences = Record(
    entity="cadence",
    table="cadences",
    path="/api/cadences",
    order_by="active DESC, next_due IS NULL, next_due",
    fields={
        "title": Field("text", S, required=True),
        "message_type": Field("text", S, choices=MESSAGE_TYPES, default="other"),
        "rhythm": Field("text", S, choices=RHYTHMS, default="weekly"),
        "next_due": Field("date", S),
        "lead_days": Field("int", S, default=2),
        "template_id": Field("int", S),
        "active": Field("bool", S, default=True),
    },
)

glossary = Record(
    entity="glossary_term",
    table="glossary",
    path="/api/glossary",
    order_by="term",
    fields={"term": Field("text", S, required=True), "plain": Field("text", S)},
)
