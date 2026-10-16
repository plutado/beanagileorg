"""Toolkit tables and their privacy-tagged records."""

from beanagile.core.privacy import Level
from beanagile.core.records import Field, Record

P, S, E = Level.PRIVATE, Level.PRESENTABLE, Level.EXPORTABLE

RELATIONSHIPS = ("employee", "contractor", "peer", "stakeholder", "manager", "vendor")
INTERVIEW_STATUS = ("planned", "done")
GOAL_STATUS = ("not started", "in progress", "done", "at risk")
TASK_STATUS = ("open", "done")
CADENCES = ("weekly", "every two weeks", "monthly", "quarterly", "once")
ACTION_STATUS = ("open", "in progress", "waiting", "done")
ACTION_ORIGINS = ("dev sync", "retro", "incident", "one-on-one", "other")
SESSION_STATUS = ("proposed", "scheduled", "done")
STEP_METHODS = ("call", "page", "chat", "email", "in person")

MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE people (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            relationship TEXT,
            start_date TEXT,
            location TEXT,
            timezone TEXT,
            background TEXT,
            skills TEXT,
            certifications TEXT,
            goals TEXT,
            wants_to_learn TEXT,
            can_teach TEXT,
            working_style TEXT,
            support_notes TEXT,
            contact TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE interviews (
            id INTEGER PRIMARY KEY,
            person_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            date TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            working TEXT,
            frustrating TEXT,
            change_first TEXT,
            dont_change TEXT,
            systems TEXT,
            gaps TEXT,
            opportunities TEXT,
            themes TEXT
        );
        CREATE TABLE learning_goals (
            id INTEGER PRIMARY KEY,
            track TEXT,
            goal TEXT NOT NULL,
            evidence TEXT,
            target_day INTEGER,
            status TEXT NOT NULL DEFAULT 'not started',
            show_in_report INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE learning_log (
            id INTEGER PRIMARY KEY,
            goal_id INTEGER NOT NULL REFERENCES learning_goals (id) ON DELETE CASCADE,
            date TEXT,
            minutes INTEGER,
            note TEXT
        );
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            requested_by TEXT,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'open'
        );
        CREATE TABLE obligations (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            cadence TEXT NOT NULL DEFAULT 'weekly',
            next_due TEXT,
            last_done TEXT
        );
        """,
    ),
    (
        2,
        """
        CREATE TABLE action_items (
            id INTEGER PRIMARY KEY,
            concern TEXT NOT NULL,
            raised_by_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            raised_on TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            next_action TEXT,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            origin TEXT NOT NULL DEFAULT 'dev sync',
            learning INTEGER NOT NULL DEFAULT 0,
            incident_id INTEGER,
            notes TEXT
        );
        CREATE TABLE learning_sessions (
            id INTEGER PRIMARY KEY,
            topic TEXT NOT NULL,
            presenter_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            date TEXT,
            status TEXT NOT NULL DEFAULT 'proposed',
            action_item_id INTEGER REFERENCES action_items (id) ON DELETE SET NULL,
            notes TEXT
        );
        CREATE TABLE systems (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            how_to_open_case TEXT,
            vendor_support TEXT,
            business_contacts TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            first_responder_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            backup_id INTEGER REFERENCES people (id) ON DELETE SET NULL
        );
        CREATE TABLE severities (
            id INTEGER PRIMARY KEY,
            level TEXT NOT NULL,
            definition TEXT,
            response_time TEXT,
            who_is_paged TEXT,
            who_is_told TEXT
        );
        CREATE TABLE escalation_steps (
            id INTEGER PRIMARY KEY,
            system_id INTEGER REFERENCES systems (id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0,
            person_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            method TEXT NOT NULL DEFAULT 'call',
            out_of_hours INTEGER NOT NULL DEFAULT 0,
            note TEXT
        );
        CREATE TABLE incidents (
            id INTEGER PRIMARY KEY,
            date TEXT,
            system_id INTEGER REFERENCES systems (id) ON DELETE SET NULL,
            severity_id INTEGER REFERENCES severities (id) ON DELETE SET NULL,
            summary TEXT NOT NULL,
            people_ids TEXT,
            resolved_at TEXT,
            notes TEXT
        );
        """,
    ),
]

# Names and roles may show on a shared screen; everything personal stays private.
people = Record(
    entity="person",
    table="people",
    path="/api/people",
    order_by="active DESC, name",
    fields={
        "name": Field("text", S, required=True),
        "role": Field("text", S),
        "relationship": Field("text", S, choices=RELATIONSHIPS),
        "start_date": Field("date", P),
        "location": Field("text", P),
        "timezone": Field("text", P),
        "background": Field("text", P),
        "skills": Field("list", P),
        "certifications": Field("list", P),
        "goals": Field("text", P),
        "wants_to_learn": Field("list", P),
        "can_teach": Field("list", P),
        "working_style": Field("text", P),
        "support_notes": Field("text", P),
        "contact": Field("text", P),
        "active": Field("bool", S, default=True),
    },
)

# One-on-ones are private end to end; the rollup shares only themes and counts.
interviews = Record(
    entity="interview",
    table="interviews",
    path="/api/interviews",
    order_by="date IS NULL, date DESC",
    hide_when_empty=True,
    fields={
        "person_id": Field("int", P),
        "date": Field("date", P),
        "status": Field("text", P, choices=INTERVIEW_STATUS, default="planned"),
        "working": Field("text", P),
        "frustrating": Field("text", P),
        "change_first": Field("text", P),
        "dont_change": Field("text", P),
        "systems": Field("list", P),
        "gaps": Field("text", P),
        "opportunities": Field("text", P),
        "themes": Field("list", P),
    },
    computed={"person_name": ("(SELECT name FROM people p WHERE p.id = interviews.person_id)", P)},
)

# A learning goal is exportable only when marked for reporting; otherwise the whole record is private.
learning_goals = Record(
    entity="learning_goal",
    table="learning_goals",
    path="/api/learning-goals",
    order_by="target_day IS NULL, target_day, id",
    fields={
        "track": Field("text", E),
        "goal": Field("text", E, required=True),
        "evidence": Field("text", E),
        "target_day": Field("int", E),
        "status": Field("text", E, choices=GOAL_STATUS, default="not started"),
        "show_in_report": Field("bool", P, default=False),
    },
    computed={
        "minutes": ("(SELECT COALESCE(SUM(minutes), 0) FROM learning_log l WHERE l.goal_id = learning_goals.id)", E)
    },
    ceiling_sql="CASE WHEN show_in_report THEN 2 ELSE 0 END",
)

learning_log = Record(
    entity="learning_log",
    table="learning_log",
    path="/api/learning-log",
    order_by="date DESC, id DESC",
    hide_when_empty=True,
    fields={
        "goal_id": Field("int", P, required=True),
        "date": Field("date", P),
        "minutes": Field("int", P),
        "note": Field("text", P),
    },
)

tasks = Record(
    entity="task",
    table="tasks",
    path="/api/tasks",
    order_by="status = 'done', due IS NULL, due, id",
    hide_when_empty=True,
    fields={
        "title": Field("text", P, required=True),
        "requested_by": Field("text", P),
        "due": Field("date", P),
        "status": Field("text", P, choices=TASK_STATUS, default="open"),
    },
)

obligations = Record(
    entity="obligation",
    table="obligations",
    path="/api/obligations",
    order_by="next_due IS NULL, next_due, id",
    hide_when_empty=True,
    fields={
        "title": Field("text", P, required=True),
        "cadence": Field("text", P, choices=CADENCES, default="weekly"),
        "next_due": Field("date", P),
        "last_done": Field("date", P),
    },
)

# ---- day-30 batch: dev-sync log, group learning, escalation playbook ----

# The dev-sync log can show on a shared screen; only my notes stay private.
action_items = Record(
    entity="action_item",
    table="action_items",
    path="/api/actions",
    order_by="status = 'done', due IS NULL, due, id",
    fields={
        "concern": Field("text", S, required=True),
        "raised_by_id": Field("int", S),
        "raised_on": Field("date", S),
        "owner_id": Field("int", S),
        "next_action": Field("text", S),
        "due": Field("date", S),
        "status": Field("text", S, choices=ACTION_STATUS, default="open"),
        "origin": Field("text", S, choices=ACTION_ORIGINS, default="dev sync"),
        "learning": Field("bool", S, default=False),
        "incident_id": Field("int", S),
        "notes": Field("text", P),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = action_items.owner_id)", S),
        "raised_by_name": ("(SELECT name FROM people p WHERE p.id = action_items.raised_by_id)", S),
    },
)

learning_sessions = Record(
    entity="learning_session",
    table="learning_sessions",
    path="/api/learning-sessions",
    order_by="date IS NULL, date, id",
    fields={
        "topic": Field("text", S, required=True),
        "presenter_id": Field("int", S),
        "date": Field("date", S),
        "status": Field("text", S, choices=SESSION_STATUS, default="proposed"),
        "action_item_id": Field("int", S),
        "notes": Field("text", P),
    },
    computed={
        "presenter_name": ("(SELECT name FROM people p WHERE p.id = learning_sessions.presenter_id)", S),
        "source_concern": ("(SELECT concern FROM action_items a WHERE a.id = learning_sessions.action_item_id)", S),
    },
)

# Who to call is presentable; vendor phone lines and similar details stay private.
systems = Record(
    entity="system",
    table="systems",
    path="/api/systems",
    order_by="name",
    fields={
        "name": Field("text", S, required=True),
        "description": Field("text", S),
        "how_to_open_case": Field("text", S),
        "vendor_support": Field("text", P),
        "business_contacts": Field("text", S),
        "owner_id": Field("int", S),
        "first_responder_id": Field("int", S),
        "backup_id": Field("int", S),
    },
)

severities = Record(
    entity="severity",
    table="severities",
    path="/api/severities",
    order_by="level",
    fields={
        "level": Field("text", S, required=True),
        "definition": Field("text", S),
        "response_time": Field("text", S),
        "who_is_paged": Field("text", S),
        "who_is_told": Field("text", S),
    },
)

escalation_steps = Record(
    entity="escalation_step",
    table="escalation_steps",
    path="/api/escalation-steps",
    order_by="system_id, out_of_hours, position, id",
    fields={
        "system_id": Field("int", S, required=True),
        "position": Field("int", S, default=0),
        "person_id": Field("int", S),
        "method": Field("text", S, choices=STEP_METHODS, default="call"),
        "out_of_hours": Field("bool", S, default=False),
        "note": Field("text", P),
    },
    computed={"person_name": ("(SELECT name FROM people p WHERE p.id = escalation_steps.person_id)", S)},
)

incidents = Record(
    entity="incident",
    table="incidents",
    path="/api/incidents",
    order_by="date IS NULL, date DESC, id DESC",
    fields={
        "date": Field("date", S),
        "system_id": Field("int", S),
        "severity_id": Field("int", S),
        "summary": Field("text", S, required=True),
        "people_ids": Field("ids", S),
        "resolved_at": Field("date", S),
        "notes": Field("text", P),
    },
    computed={
        "system_name": ("(SELECT name FROM systems s WHERE s.id = incidents.system_id)", S),
        "severity_level": ("(SELECT level FROM severities v WHERE v.id = incidents.severity_id)", S),
    },
)

RECORDS = [
    people, interviews, learning_goals, learning_log, tasks, obligations,
    action_items, learning_sessions, systems, severities, escalation_steps, incidents,
]
