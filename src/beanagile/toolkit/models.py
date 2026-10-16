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
ACTION_ORIGINS = ("dev sync", "retro", "incident", "one-on-one", "vendor", "other")
VENDOR_TYPES = ("platform vendor", "consulting partner", "contractor agency", "tooling", "other")
VENDOR_STATUS = ("active", "onboarding", "under review", "ended")
INTERACTION_CHANNELS = ("call", "meeting", "email", "chat", "other")
CONCERN_STATUS = ("open", "in progress", "resolved")
SPRINT_KINDS = ("development", "innovation and planning")
CEREMONY_TYPES = ("planning", "refinement", "review", "retro", "dev sync", "ad hoc", "pi planning", "pi demo")
ROADMAP_KINDS = ("ceremony", "agreement", "metric", "milestone")
ROADMAP_STATUS = ("not started", "in progress", "done", "at risk")
RACI_STATUS = ("to confirm", "confirmed", "changed")
RACI_LETTERS = ("R", "A", "C", "I")
RISK_STATUS = ("open", "watching", "closed")
RISK_LEVELS = ("high", "medium", "low")
DECISION_STATUS = ("open", "decided")
RETRO_FORMATS = {
    "went well / didn't / ideas": ("Went well", "Didn't go well", "Ideas"),
    "start / stop / continue": ("Start", "Stop", "Continue"),
    "mad / sad / glad": ("Mad", "Sad", "Glad"),
    "4 Ls": ("Liked", "Learned", "Lacked", "Longed for"),
}
COMMITMENT_STATUS = ("committed", "in progress", "done", "dropped")
PRIORITIES = ("highest", "high", "medium", "low")
WORK_STATUS = ("not started", "in progress", "done", "blocked")
OBJECTIVE_KINDS = ("committed", "stretch")
DEPENDENCY_STATUS = ("open", "met", "at risk")
MILESTONE_KINDS = ("release", "freeze", "demo", "innovation and planning", "other")
ROAM = ("unroamed", "resolved", "owned", "accepted", "mitigated")
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
    (
        3,
        """
        CREATE TABLE vendors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'other',
            status TEXT NOT NULL DEFAULT 'active',
            support_process TEXT,
            service_promise TEXT,
            contract_start TEXT,
            contract_end TEXT,
            renewal_notice_days INTEGER NOT NULL DEFAULT 60,
            contact_ids TEXT,
            commercial_terms TEXT,
            notes TEXT
        );
        CREATE TABLE vendor_interactions (
            id INTEGER PRIMARY KEY,
            vendor_id INTEGER NOT NULL REFERENCES vendors (id) ON DELETE CASCADE,
            date TEXT,
            channel TEXT NOT NULL DEFAULT 'call',
            people_ids TEXT,
            summary TEXT NOT NULL,
            concerns TEXT
        );
        CREATE TABLE vendor_concerns (
            id INTEGER PRIMARY KEY,
            vendor_id INTEGER NOT NULL REFERENCES vendors (id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            raised_on TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            resolution TEXT,
            interaction_id INTEGER REFERENCES vendor_interactions (id) ON DELETE SET NULL
        );
        ALTER TABLE action_items ADD COLUMN vendor_id INTEGER REFERENCES vendors (id) ON DELETE SET NULL;
        ALTER TABLE systems ADD COLUMN vendor_id INTEGER REFERENCES vendors (id) ON DELETE SET NULL;
        """,
    ),
    (
        4,
        """
        CREATE TABLE program_increments (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL,
            start_date TEXT,
            end_date TEXT,
            objectives TEXT,
            objectives_met TEXT
        );
        CREATE TABLE sprints (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL,
            start_date TEXT,
            end_date TEXT,
            goal TEXT,
            kind TEXT NOT NULL DEFAULT 'development',
            pi_id INTEGER REFERENCES program_increments (id) ON DELETE SET NULL
        );
        CREATE TABLE ceremony_notes (
            id INTEGER PRIMARY KEY,
            sprint_id INTEGER NOT NULL REFERENCES sprints (id) ON DELETE CASCADE,
            type TEXT NOT NULL DEFAULT 'planning',
            date TEXT,
            happened TEXT,
            noticed TEXT,
            thoughts TEXT,
            follow_ups TEXT,
            tags TEXT
        );
        ALTER TABLE action_items ADD COLUMN sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL;
        ALTER TABLE action_items ADD COLUMN note_id INTEGER REFERENCES ceremony_notes (id) ON DELETE SET NULL;
        CREATE TABLE roadmap_items (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            kind TEXT NOT NULL DEFAULT 'milestone',
            target_day INTEGER,
            status TEXT NOT NULL DEFAULT 'not started',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE raci_decisions (
            id INTEGER PRIMARY KEY,
            decision TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'to confirm',
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE raci_assignments (
            id INTEGER PRIMARY KEY,
            decision_id INTEGER NOT NULL REFERENCES raci_decisions (id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            letter TEXT NOT NULL,
            UNIQUE (decision_id, role)
        );
        CREATE TABLE risks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            impact TEXT,
            level TEXT NOT NULL DEFAULT 'medium',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            next_step TEXT,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            notes TEXT
        );
        CREATE TABLE decisions_needed (
            id INTEGER PRIMARY KEY,
            decision TEXT NOT NULL,
            from_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            needed_by TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            outcome TEXT
        );
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            unit TEXT,
            baseline REAL,
            target REAL,
            method TEXT,
            higher_is_better INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE metric_readings (
            id INTEGER PRIMARY KEY,
            metric_id INTEGER NOT NULL REFERENCES metrics (id) ON DELETE CASCADE,
            date TEXT,
            value REAL NOT NULL
        );
        """,
    ),
    (
        5,
        """
        CREATE TABLE retros (
            id INTEGER PRIMARY KEY,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            date TEXT,
            format TEXT NOT NULL DEFAULT 'went well / didn''t / ideas',
            attendee_ids TEXT,
            summary TEXT,
            note_id INTEGER REFERENCES ceremony_notes (id) ON DELETE SET NULL
        );
        CREATE TABLE retro_items (
            id INTEGER PRIMARY KEY,
            retro_id INTEGER NOT NULL REFERENCES retros (id) ON DELETE CASCADE,
            column_name TEXT NOT NULL,
            text TEXT NOT NULL,
            votes INTEGER NOT NULL DEFAULT 0,
            topic TEXT
        );
        CREATE TABLE retro_commitments (
            id INTEGER PRIMARY KEY,
            retro_id INTEGER NOT NULL REFERENCES retros (id) ON DELETE CASCADE,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            commitment TEXT NOT NULL,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'committed',
            outcome TEXT,
            reviewed_in_id INTEGER REFERENCES retros (id) ON DELETE SET NULL
        );
        ALTER TABLE program_increments ADD COLUMN confidence REAL;
        ALTER TABLE program_increments ADD COLUMN confidence_date TEXT;
        ALTER TABLE sprints ADD COLUMN capacity INTEGER;
        CREATE TABLE pi_objectives (
            id INTEGER PRIMARY KEY,
            pi_id INTEGER NOT NULL REFERENCES program_increments (id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'committed',
            value_planned INTEGER,
            value_actual INTEGER,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'not started'
        );
        CREATE TABLE epics (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT NOT NULL DEFAULT 'medium',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'not started',
            ticket_key TEXT
        );
        CREATE TABLE features (
            id INTEGER PRIMARY KEY,
            pi_id INTEGER REFERENCES program_increments (id) ON DELETE SET NULL,
            epic_id INTEGER REFERENCES epics (id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            description TEXT,
            acceptance TEXT,
            priority TEXT NOT NULL DEFAULT 'medium',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'not started',
            ticket_key TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE stories (
            id INTEGER PRIMARY KEY,
            feature_id INTEGER REFERENCES features (id) ON DELETE SET NULL,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            acceptance TEXT,
            points INTEGER,
            priority TEXT NOT NULL DEFAULT 'medium',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'not started',
            ticket_key TEXT
        );
        CREATE TABLE dependencies (
            id INTEGER PRIMARY KEY,
            pi_id INTEGER NOT NULL REFERENCES program_increments (id) ON DELETE CASCADE,
            feature_id INTEGER REFERENCES features (id) ON DELETE CASCADE,
            depends_on_id INTEGER REFERENCES features (id) ON DELETE SET NULL,
            team TEXT,
            description TEXT NOT NULL,
            needed_by_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'open'
        );
        CREATE TABLE pi_milestones (
            id INTEGER PRIMARY KEY,
            pi_id INTEGER NOT NULL REFERENCES program_increments (id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            date TEXT,
            kind TEXT NOT NULL DEFAULT 'other'
        );
        CREATE TABLE pi_risks (
            id INTEGER PRIMARY KEY,
            pi_id INTEGER NOT NULL REFERENCES program_increments (id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            roam TEXT NOT NULL DEFAULT 'unroamed',
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
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
        "vendor_id": Field("int", S),
        "sprint_id": Field("int", S),
        "note_id": Field("int", P),
        "notes": Field("text", P),
    },
    computed={
        "vendor_name": ("(SELECT name FROM vendors v WHERE v.id = action_items.vendor_id)", S),
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
        "vendor_id": Field("int", S),
    },
    computed={"vendor_name": ("(SELECT name FROM vendors v WHERE v.id = systems.vendor_id)", S)},
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

# ---- vendor relationships ----

# Who the vendors are and how to reach them can show on screen; money and my notes stay private.
vendors = Record(
    entity="vendor",
    table="vendors",
    path="/api/vendors",
    order_by="status = 'ended', name",
    fields={
        "name": Field("text", S, required=True),
        "type": Field("text", S, choices=VENDOR_TYPES, default="other"),
        "status": Field("text", S, choices=VENDOR_STATUS, default="active"),
        "support_process": Field("text", S),
        "service_promise": Field("text", S),
        "contract_start": Field("date", S),
        "contract_end": Field("date", S),
        "renewal_notice_days": Field("int", S, default=60),
        "contact_ids": Field("ids", S),
        "commercial_terms": Field("text", P),
        "notes": Field("text", P),
    },
    computed={
        "open_concerns": ("(SELECT COUNT(*) FROM vendor_concerns c WHERE c.vendor_id = vendors.id AND c.status != 'resolved')", S),
        "last_contact": ("(SELECT MAX(date) FROM vendor_interactions i WHERE i.vendor_id = vendors.id)", S),
    },
)

# Conversations with vendors are private notes.
vendor_interactions = Record(
    entity="vendor_interaction",
    table="vendor_interactions",
    path="/api/vendor-interactions",
    order_by="date IS NULL, date DESC, id DESC",
    hide_when_empty=True,
    fields={
        "vendor_id": Field("int", P, required=True),
        "date": Field("date", P),
        "channel": Field("text", P, choices=INTERACTION_CHANNELS, default="call"),
        "people_ids": Field("ids", P),
        "summary": Field("text", P, required=True),
        "concerns": Field("text", P),
    },
)

vendor_concerns = Record(
    entity="vendor_concern",
    table="vendor_concerns",
    path="/api/vendor-concerns",
    order_by="status = 'resolved', due IS NULL, due, id",
    fields={
        "vendor_id": Field("int", S, required=True),
        "title": Field("text", S, required=True),
        "raised_on": Field("date", S),
        "owner_id": Field("int", S),
        "due": Field("date", S),
        "status": Field("text", S, choices=CONCERN_STATUS, default="open"),
        "resolution": Field("text", P),
        "interaction_id": Field("int", P),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = vendor_concerns.owner_id)", S),
        "vendor_name": ("(SELECT name FROM vendors v WHERE v.id = vendor_concerns.vendor_id)", S),
    },
)

# ---- day-45 batch: sprints, roadmap, RACI, risks, decisions, metrics ----

program_increments = Record(
    entity="program_increment",
    table="program_increments",
    path="/api/program-increments",
    order_by="number DESC",
    fields={
        "number": Field("int", E, required=True),
        "start_date": Field("date", E),
        "end_date": Field("date", E),
        "objectives": Field("text", E),
        "objectives_met": Field("text", E),
        "confidence": Field("number", S),
        "confidence_date": Field("date", S),
    },
)

# Sprint dates and goals are exportable; the notebook entries are private.
sprints = Record(
    entity="sprint",
    table="sprints",
    path="/api/sprints",
    order_by="number DESC",
    fields={
        "number": Field("int", E, required=True),
        "start_date": Field("date", E),
        "end_date": Field("date", E),
        "goal": Field("text", E),
        "kind": Field("text", E, choices=SPRINT_KINDS, default="development"),
        "pi_id": Field("int", E),
        "capacity": Field("int", S),
    },
    computed={"note_count": ("(SELECT COUNT(*) FROM ceremony_notes n WHERE n.sprint_id = sprints.id)", P)},
)

ceremony_notes = Record(
    entity="ceremony_note",
    table="ceremony_notes",
    path="/api/ceremony-notes",
    order_by="date IS NULL, date, id",
    hide_when_empty=True,
    fields={
        "sprint_id": Field("int", P, required=True),
        "type": Field("text", P, choices=CEREMONY_TYPES, default="planning"),
        "date": Field("date", P),
        "happened": Field("text", P),
        "noticed": Field("text", P),
        "thoughts": Field("text", P),
        "follow_ups": Field("text", P),
        "tags": Field("list", P),
    },
)

roadmap_items = Record(
    entity="roadmap_item",
    table="roadmap_items",
    path="/api/roadmap",
    order_by="target_day IS NULL, target_day, position, id",
    fields={
        "title": Field("text", E, required=True),
        "description": Field("text", E),
        "kind": Field("text", E, choices=ROADMAP_KINDS, default="milestone"),
        "target_day": Field("int", E),
        "status": Field("text", E, choices=ROADMAP_STATUS, default="not started"),
        "owner_id": Field("int", S),
        "position": Field("int", S, default=0),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = roadmap_items.owner_id)", S)},
)

raci_decisions = Record(
    entity="raci_decision",
    table="raci_decisions",
    path="/api/raci-decisions",
    order_by="position, id",
    fields={
        "decision": Field("text", S, required=True),
        "status": Field("text", S, choices=RACI_STATUS, default="to confirm"),
        "position": Field("int", S, default=0),
    },
)

risks = Record(
    entity="risk",
    table="risks",
    path="/api/risks",
    order_by="status = 'closed', CASE level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, due IS NULL, due",
    fields={
        "title": Field("text", E, required=True),
        "impact": Field("text", E),
        "level": Field("text", E, choices=RISK_LEVELS, default="medium"),
        "owner_id": Field("int", E),
        "next_step": Field("text", E),
        "due": Field("date", E),
        "status": Field("text", E, choices=RISK_STATUS, default="open"),
        "notes": Field("text", P),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = risks.owner_id)", E)},
)

decisions_needed = Record(
    entity="decision_needed",
    table="decisions_needed",
    path="/api/decisions-needed",
    order_by="status = 'decided', needed_by IS NULL, needed_by",
    fields={
        "decision": Field("text", E, required=True),
        "from_id": Field("int", E),
        "needed_by": Field("date", E),
        "status": Field("text", E, choices=DECISION_STATUS, default="open"),
        "outcome": Field("text", E),
    },
    computed={"from_name": ("(SELECT name FROM people p WHERE p.id = decisions_needed.from_id)", E)},
)

metrics = Record(
    entity="metric",
    table="metrics",
    path="/api/metrics",
    order_by="name",
    fields={
        "name": Field("text", E, required=True),
        "unit": Field("text", E),
        "baseline": Field("number", E),
        "target": Field("number", E),
        "method": Field("text", E),
        "higher_is_better": Field("bool", E, default=True),
    },
    computed={
        "latest": ("(SELECT value FROM metric_readings r WHERE r.metric_id = metrics.id ORDER BY date DESC, id DESC LIMIT 1)", E),
        "latest_date": ("(SELECT date FROM metric_readings r WHERE r.metric_id = metrics.id ORDER BY date DESC, id DESC LIMIT 1)", E),
    },
)

metric_readings = Record(
    entity="metric_reading",
    table="metric_readings",
    path="/api/metric-readings",
    order_by="metric_id, date, id",
    fields={"metric_id": Field("int", E, required=True), "date": Field("date", E), "value": Field("number", E, required=True)},
)

# ---- retrospectives: the team's shared record (my private impressions stay in the sprint notebook) ----

retros = Record(
    entity="retro",
    table="retros",
    path="/api/retros",
    order_by="date IS NULL, date DESC, id DESC",
    fields={
        "sprint_id": Field("int", S),
        "date": Field("date", S),
        "format": Field("text", S, choices=tuple(RETRO_FORMATS), default="went well / didn't / ideas"),
        "attendee_ids": Field("ids", S),
        "summary": Field("text", S),
        "note_id": Field("int", P),
    },
    computed={
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = retros.sprint_id)", S),
        "item_count": ("(SELECT COUNT(*) FROM retro_items i WHERE i.retro_id = retros.id)", S),
        "commitment_count": ("(SELECT COUNT(*) FROM retro_commitments c WHERE c.retro_id = retros.id)", S),
    },
)

retro_items = Record(
    entity="retro_item",
    table="retro_items",
    path="/api/retro-items",
    order_by="votes DESC, id",
    fields={
        "retro_id": Field("int", S, required=True),
        "column_name": Field("text", S, required=True),
        "text": Field("text", S, required=True),
        "votes": Field("int", S, default=0),
        "topic": Field("text", S),
    },
)

retro_commitments = Record(
    entity="retro_commitment",
    table="retro_commitments",
    path="/api/retro-commitments",
    order_by="status IN ('done', 'dropped'), due IS NULL, due, id",
    fields={
        "retro_id": Field("int", S, required=True),
        "sprint_id": Field("int", S),
        "commitment": Field("text", S, required=True),
        "owner_id": Field("int", S),
        "due": Field("date", S),
        "status": Field("text", S, choices=COMMITMENT_STATUS, default="committed"),
        "outcome": Field("text", S),
        "reviewed_in_id": Field("int", S),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = retro_commitments.owner_id)", S),
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = retro_commitments.sprint_id)", S),
    },
)

# ---- PI planning: done in the room with everyone, so presentable throughout ----

pi_objectives = Record(
    entity="pi_objective",
    table="pi_objectives",
    path="/api/pi-objectives",
    order_by="kind = 'stretch', value_planned IS NULL, value_planned DESC, id",
    fields={
        "pi_id": Field("int", E, required=True),
        "title": Field("text", E, required=True),
        "kind": Field("text", E, choices=OBJECTIVE_KINDS, default="committed"),
        "value_planned": Field("int", E),
        "value_actual": Field("int", E),
        "owner_id": Field("int", S),
        "status": Field("text", E, choices=WORK_STATUS, default="not started"),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = pi_objectives.owner_id)", S)},
)

epics = Record(
    entity="epic",
    table="epics",
    path="/api/epics",
    order_by="CASE priority WHEN 'highest' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id",
    fields={
        "title": Field("text", S, required=True),
        "description": Field("text", S),
        "priority": Field("text", S, choices=PRIORITIES, default="medium"),
        "owner_id": Field("int", S),
        "status": Field("text", S, choices=WORK_STATUS, default="not started"),
        "ticket_key": Field("text", S),
    },
)

features = Record(
    entity="feature",
    table="features",
    path="/api/features",
    order_by="CASE priority WHEN 'highest' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, position, id",
    fields={
        "pi_id": Field("int", S),
        "epic_id": Field("int", S),
        "title": Field("text", S, required=True),
        "description": Field("text", S),
        "acceptance": Field("text", S),
        "priority": Field("text", S, choices=PRIORITIES, default="medium"),
        "owner_id": Field("int", S),
        "status": Field("text", S, choices=WORK_STATUS, default="not started"),
        "ticket_key": Field("text", S),
        "position": Field("int", S, default=0),
    },
    computed={
        "epic_title": ("(SELECT title FROM epics e WHERE e.id = features.epic_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = features.owner_id)", S),
        "points": ("(SELECT COALESCE(SUM(points), 0) FROM stories s WHERE s.feature_id = features.id)", S),
        "story_count": ("(SELECT COUNT(*) FROM stories s WHERE s.feature_id = features.id)", S),
    },
)

stories = Record(
    entity="story",
    table="stories",
    path="/api/stories",
    order_by="CASE priority WHEN 'highest' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id",
    fields={
        "feature_id": Field("int", S),
        "sprint_id": Field("int", S),
        "title": Field("text", S, required=True),
        "acceptance": Field("text", S),
        "points": Field("int", S),
        "priority": Field("text", S, choices=PRIORITIES, default="medium"),
        "owner_id": Field("int", S),
        "status": Field("text", S, choices=WORK_STATUS, default="not started"),
        "ticket_key": Field("text", S),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = stories.owner_id)", S)},
)

dependencies = Record(
    entity="dependency",
    table="dependencies",
    path="/api/dependencies",
    order_by="status = 'met', id",
    fields={
        "pi_id": Field("int", S, required=True),
        "feature_id": Field("int", S),
        "depends_on_id": Field("int", S),
        "team": Field("text", S),
        "description": Field("text", S, required=True),
        "needed_by_id": Field("int", S),
        "status": Field("text", S, choices=DEPENDENCY_STATUS, default="open"),
    },
    computed={
        "feature_title": ("(SELECT title FROM features f WHERE f.id = dependencies.feature_id)", S),
        "depends_on_title": ("(SELECT title FROM features f WHERE f.id = dependencies.depends_on_id)", S),
        "needed_by_number": ("(SELECT number FROM sprints s WHERE s.id = dependencies.needed_by_id)", S),
    },
)

pi_milestones = Record(
    entity="pi_milestone",
    table="pi_milestones",
    path="/api/pi-milestones",
    order_by="date IS NULL, date, id",
    fields={
        "pi_id": Field("int", E, required=True),
        "title": Field("text", E, required=True),
        "date": Field("date", E),
        "kind": Field("text", E, choices=MILESTONE_KINDS, default="other"),
    },
)

pi_risks = Record(
    entity="pi_risk",
    table="pi_risks",
    path="/api/pi-risks",
    order_by="roam != 'unroamed', id",
    fields={
        "pi_id": Field("int", S, required=True),
        "title": Field("text", S, required=True),
        "roam": Field("text", S, choices=ROAM, default="unroamed"),
        "owner_id": Field("int", S),
        "notes": Field("text", P),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = pi_risks.owner_id)", S)},
)

RECORDS = [
    people, interviews, learning_goals, learning_log, tasks, obligations,
    action_items, learning_sessions, systems, severities, escalation_steps, incidents,
    vendors, vendor_interactions, vendor_concerns,
    program_increments, sprints, ceremony_notes, roadmap_items, raci_decisions, risks, decisions_needed, metrics, metric_readings,
    retros, retro_items, retro_commitments,
    pi_objectives, epics, features, stories, dependencies, pi_milestones, pi_risks,
]
