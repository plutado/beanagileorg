"""Toolkit tables and their privacy-tagged records."""

from beanagile.core.privacy import Level
from beanagile.core.records import Field, Record

P, S, E = Level.PRIVATE, Level.PRESENTABLE, Level.EXPORTABLE

RELATIONSHIPS = ("employee", "contractor", "peer", "stakeholder", "manager", "vendor")
INTERVIEW_STATUS = ("planned", "done")
GOAL_STATUS = ("not started", "in progress", "done", "at risk")
TASK_STATUS = ("open", "done")
CADENCES = ("weekly", "every two weeks", "monthly", "quarterly", "once")

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

RECORDS = [people, interviews, learning_goals, learning_log, tasks, obligations]
