"""Toolkit tables and their privacy-tagged records."""

from beanagileorg.core.privacy import Level
from beanagileorg.core.records import Field, Record

P, S, E = Level.PRIVATE, Level.PRESENTABLE, Level.EXPORTABLE

RELATIONSHIPS = ("employee", "contractor", "peer", "stakeholder", "manager", "vendor")
INTERVIEW_STATUS = ("planned", "done")
GOAL_STATUS = ("not started", "in progress", "done", "at risk")
TASK_STATUS = ("open", "done")
CADENCES = ("weekly", "every two weeks", "monthly", "quarterly", "once")
ACTION_STATUS = ("open", "in progress", "waiting", "done")
ACTION_ORIGINS = ("dev sync", "retro", "incident", "one-on-one", "vendor", "testing", "other")
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
PLAN_STATUS = ("draft", "reviewed", "presented")
PLAN_ITEM_KINDS = ("outcome", "action", "measure", "keep")
PLAN_ITEM_STATUS = ("planned", "in progress", "done", "dropped")
DEPARTMENT_KINDS = ("division", "department", "team")
OFFERING_KINDS = ("product", "service", "internal platform")
MATURITY = ("idea", "emerging", "growing", "mature", "declining", "sunsetting")
OFFERING_STATUS = ("active", "planned", "retired")
QUADRANTS = ("strength", "weakness", "opportunity", "threat")
ASSESSMENT_SOURCES = ("listening tour", "metrics", "incident", "vendor", "customer feedback", "document", "my observation")
CONFIDENCE = ("low", "medium", "high")
ASSESSMENT_STATUS = ("open", "acted on", "closed")
SUBJECT_TYPES = ("offering", "department")
TEST_KINDS = ("smoke", "regression", "smoke and regression")
RUN_KINDS = ("smoke", "regression", "release check", "exploratory")
RUN_STATUS = ("planned", "in progress", "done")
RESULTS = ("not run", "pass", "fail", "blocked", "skipped")
SUITE_KINDS = ("unit", "integration", "end-to-end", "Apex", "MUnit", "performance", "other")
SUITE_RESULTS = ("unknown", "passing", "failing", "flaky")
REGRESSION_KINDS = ("Salesforce release", "peak-season freeze", "major release", "other")
REGRESSION_STATUS = ("planned", "in progress", "signed off", "done")
SYSTEM_KINDS = ("platform", "application", "integration", "data store", "external service", "tool")
LIFECYCLE = ("planned", "active", "retiring", "retired")
CRITICALITY = ("high", "medium", "low")
INTEGRATION_PATTERNS = ("API", "event", "batch", "file transfer", "database link", "manual")
INTEGRATION_DIRECTIONS = ("one way", "two way")
INTEGRATION_STATUS = ("planned", "live", "retiring", "retired")
ADR_STATUS = ("proposed", "accepted", "superseded", "rejected")
ONBOARDING_CATEGORIES = ("accounts and access", "tools and setup", "people", "ways of working", "systems and architecture", "learning", "first work", "admin and compliance")
ONBOARDING_OWNERS = ("new member", "manager", "buddy", "IT or admin")
ONBOARDING_TRACKS = ("Salesforce developer", "MuleSoft developer", "QA", "employee", "contractor")
ONBOARDING_STATUS = ("not started", "in progress", "done")
POLICY_CATEGORIES = ("branching", "code review", "testing", "release", "change management", "hotfix", "security", "data", "documentation", "other")
POLICY_STATUS = ("draft", "agreed", "retired")
GUIDE_STATUS = ("draft", "published")
GUIDE_FOCUS = ("want to work on", "practicing", "comfortable")
GUIDE_ORIGINS = ("built-in", "mine", "imported")
DEBT_CATEGORIES = ("maintainability", "stability", "performance", "cleanup", "revenue and conversion", "observability", "security", "delivery speed", "cost")
DEBT_EFFORT = ("S", "M", "L", "XL")
DEBT_STATUS = ("identified", "accepted", "planned", "in progress", "done", "won't fix")
DEBT_DECISIONS = ("fix now", "schedule", "accept for now", "won't fix")
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
    (
        6,
        """
        CREATE TABLE plans (
            id INTEGER PRIMARY KEY,
            horizon_days INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            presented_on DATE,
            audience TEXT,
            notes TEXT
        );
        INSERT INTO plans (horizon_days, title) VALUES
            (30, 'First 30 days'), (60, 'Days 31 to 60'), (90, 'Days 61 to 90'),
            (120, 'Month 4'), (150, 'Month 5'), (180, 'Month 6');
        CREATE TABLE plan_items (
            id INTEGER PRIMARY KEY,
            plan_id INTEGER NOT NULL REFERENCES plans (id) ON DELETE CASCADE,
            kind TEXT NOT NULL DEFAULT 'action',
            title TEXT NOT NULL,
            detail TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            due_day INTEGER,
            status TEXT NOT NULL DEFAULT 'planned',
            themes TEXT,
            evidence TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        """,
    ),
    (
        7,
        """
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'department',
            parent_id INTEGER REFERENCES departments (id) ON DELETE SET NULL,
            leader_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            purpose TEXT,
            notes TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        ALTER TABLE people ADD COLUMN department_id INTEGER REFERENCES departments (id) ON DELETE SET NULL;
        CREATE TABLE offerings (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'product',
            description TEXT,
            customers TEXT,
            department_id INTEGER REFERENCES departments (id) ON DELETE SET NULL,
            system_ids TEXT,
            vendor_ids TEXT,
            maturity TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT
        );
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY,
            subject_type TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            quadrant TEXT NOT NULL,
            title TEXT NOT NULL,
            evidence TEXT,
            source TEXT,
            confidence TEXT NOT NULL DEFAULT 'medium',
            date DATE,
            status TEXT NOT NULL DEFAULT 'open',
            roadmap_item_id INTEGER REFERENCES roadmap_items (id) ON DELETE SET NULL,
            risk_id INTEGER REFERENCES risks (id) ON DELETE SET NULL
        );
        CREATE INDEX assessments_subject ON assessments (subject_type, subject_id);
        """,
    ),
    (
        8,
        """
        CREATE TABLE test_cases (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            system_id INTEGER REFERENCES systems (id) ON DELETE SET NULL,
            area TEXT,
            kind TEXT NOT NULL DEFAULT 'smoke',
            priority TEXT NOT NULL DEFAULT 'medium',
            preconditions TEXT,
            steps TEXT,
            expected TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE regression_plans (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'Salesforce release',
            start_date DATE,
            end_date DATE,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            backup_owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            scope TEXT,
            case_ids TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            signoff_by_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            signoff_date DATE,
            notes TEXT
        );
        CREATE TABLE test_runs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'smoke',
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            plan_id INTEGER REFERENCES regression_plans (id) ON DELETE SET NULL,
            release TEXT,
            environment TEXT,
            date DATE,
            tester_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'in progress',
            notes TEXT
        );
        CREATE TABLE test_results (
            id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL REFERENCES test_runs (id) ON DELETE CASCADE,
            case_id INTEGER NOT NULL REFERENCES test_cases (id) ON DELETE CASCADE,
            result TEXT NOT NULL DEFAULT 'not run',
            notes TEXT,
            action_item_id INTEGER REFERENCES action_items (id) ON DELETE SET NULL,
            UNIQUE (run_id, case_id)
        );
        CREATE TABLE test_suites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'unit',
            system_id INTEGER REFERENCES systems (id) ON DELETE SET NULL,
            framework TEXT,
            location TEXT,
            ci_link TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            test_count INTEGER,
            coverage REAL,
            last_result TEXT NOT NULL DEFAULT 'unknown',
            last_run DATE,
            notes TEXT
        );
        """,
    ),
    (
        9,
        """
        ALTER TABLE systems ADD COLUMN kind TEXT NOT NULL DEFAULT 'application';
        ALTER TABLE systems ADD COLUMN category TEXT;
        ALTER TABLE systems ADD COLUMN how_we_use TEXT;
        ALTER TABLE systems ADD COLUMN environments TEXT;
        ALTER TABLE systems ADD COLUMN tech TEXT;
        ALTER TABLE systems ADD COLUMN docs_link TEXT;
        ALTER TABLE systems ADD COLUMN admin_id INTEGER REFERENCES people (id) ON DELETE SET NULL;
        ALTER TABLE systems ADD COLUMN lifecycle TEXT NOT NULL DEFAULT 'active';
        ALTER TABLE systems ADD COLUMN criticality TEXT;
        ALTER TABLE systems ADD COLUMN known_issues TEXT;
        CREATE TABLE integrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            from_id INTEGER NOT NULL REFERENCES systems (id) ON DELETE CASCADE,
            to_id INTEGER NOT NULL REFERENCES systems (id) ON DELETE CASCADE,
            via_id INTEGER REFERENCES systems (id) ON DELETE SET NULL,
            pattern TEXT NOT NULL DEFAULT 'API',
            direction TEXT NOT NULL DEFAULT 'one way',
            data TEXT,
            frequency TEXT,
            protocol TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            criticality TEXT,
            status TEXT NOT NULL DEFAULT 'live',
            notes TEXT
        );
        CREATE TABLE arch_decisions (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'proposed',
            date DATE,
            context TEXT,
            decision TEXT,
            consequences TEXT,
            alternatives TEXT,
            system_ids TEXT,
            decided_by_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            superseded_by_id INTEGER REFERENCES arch_decisions (id) ON DELETE SET NULL
        );
        CREATE TABLE guides (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT,
            body TEXT,
            system_ids TEXT,
            audience TEXT,
            updated DATE
        );
        """,
    ),
    (
        10,
        """
        CREATE TABLE onboarding_items (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL DEFAULT 'ways of working',
            due_day INTEGER,
            owner_role TEXT NOT NULL DEFAULT 'new member',
            tracks TEXT,
            link TEXT,
            minutes INTEGER,
            active INTEGER NOT NULL DEFAULT 1,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE onboardings (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            start_date DATE,
            tracks TEXT,
            buddy_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'in progress',
            notes TEXT
        );
        CREATE TABLE onboarding_tasks (
            id INTEGER PRIMARY KEY,
            onboarding_id INTEGER NOT NULL REFERENCES onboardings (id) ON DELETE CASCADE,
            item_id INTEGER REFERENCES onboarding_items (id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL DEFAULT 'ways of working',
            due_day INTEGER,
            owner_role TEXT NOT NULL DEFAULT 'new member',
            link TEXT,
            minutes INTEGER,
            done INTEGER NOT NULL DEFAULT 0,
            done_on DATE,
            notes TEXT
        );
        """,
    ),
    (
        11,
        """
        CREATE TABLE sdlc_stages (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            purpose TEXT,
            entry_criteria TEXT,
            exit_criteria TEXT,
            activities TEXT,
            roles TEXT,
            artifacts TEXT,
            system_ids TEXT,
            environment TEXT,
            duration TEXT,
            links TEXT,
            notes TEXT
        );
        CREATE TABLE sdlc_environments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            platform TEXT,
            purpose TEXT,
            data TEXT,
            deploys_by TEXT,
            refresh TEXT,
            system_id INTEGER REFERENCES systems (id) ON DELETE SET NULL,
            notes TEXT
        );
        CREATE TABLE sdlc_policies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'other',
            body TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            agreed_on DATE,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL
        );
        """,
    ),
    (
        12,
        """
        CREATE TABLE coaching_guides (
            id INTEGER PRIMARY KEY,
            slug TEXT NOT NULL UNIQUE,
            theme TEXT NOT NULL DEFAULT 'transition',
            title TEXT NOT NULL,
            summary TEXT,
            why TEXT,
            practices TEXT,
            pitfalls TEXT,
            questions TEXT,
            try_this TEXT,
            body TEXT,
            related TEXT,
            reading TEXT,
            inspired_by TEXT,
            minutes INTEGER,
            origin TEXT NOT NULL DEFAULT 'mine',
            status TEXT NOT NULL DEFAULT 'published',
            focus TEXT,
            my_notes TEXT
        );
        CREATE TABLE coaching_tips (
            id INTEGER PRIMARY KEY,
            route TEXT NOT NULL,
            text TEXT NOT NULL,
            guide_slug TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE coaching_prompts (
            id INTEGER PRIMARY KEY,
            phase TEXT NOT NULL DEFAULT 'Any time',
            text TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE reflections (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            prompt TEXT,
            entry TEXT,
            energy INTEGER,
            confidence INTEGER,
            tags TEXT
        );
        """,
    ),
    (
        13,
        """
        CREATE TABLE tech_debt (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            categories TEXT,
            system_ids TEXT,
            impact INTEGER,
            risk INTEGER,
            effort TEXT,
            points INTEGER,
            cost_of_delay TEXT,
            evidence TEXT,
            trigger_date DATE,
            trigger_reason TEXT,
            status TEXT NOT NULL DEFAULT 'identified',
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            ticket_key TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            revisit_on DATE,
            identified_on DATE,
            raised_by TEXT,
            notes TEXT
        );
        CREATE TABLE debt_decisions (
            id INTEGER PRIMARY KEY,
            debt_id INTEGER NOT NULL REFERENCES tech_debt (id) ON DELETE CASCADE,
            date DATE NOT NULL,
            decision TEXT NOT NULL,
            rationale TEXT,
            decided_by TEXT,
            revisit_on DATE
        );
        """,
    ),
    (
        14,
        """
        ALTER TABLE action_items ADD COLUMN jira_keys TEXT;
        ALTER TABLE retro_commitments ADD COLUMN jira_keys TEXT;
        ALTER TABLE risks ADD COLUMN jira_keys TEXT;
        ALTER TABLE decisions_needed ADD COLUMN jira_keys TEXT;
        ALTER TABLE roadmap_items ADD COLUMN jira_keys TEXT;
        ALTER TABLE test_cases ADD COLUMN jira_keys TEXT;
        ALTER TABLE test_results ADD COLUMN jira_keys TEXT;
        ALTER TABLE incidents ADD COLUMN jira_keys TEXT;
        ALTER TABLE onboarding_tasks ADD COLUMN jira_keys TEXT;
        ALTER TABLE vendor_concerns ADD COLUMN jira_keys TEXT;
        ALTER TABLE arch_decisions ADD COLUMN jira_keys TEXT;
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
        "department_id": Field("int", S),
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
        "jira_keys": Field("keys", S),
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
        "kind": Field("text", S, choices=SYSTEM_KINDS, default="application"),
        "category": Field("text", S),
        "how_we_use": Field("text", S),
        "environments": Field("list", S),
        "tech": Field("list", S),
        "docs_link": Field("text", S),
        "admin_id": Field("int", S),
        "lifecycle": Field("text", S, choices=LIFECYCLE, default="active"),
        "criticality": Field("text", S, choices=CRITICALITY),
        "known_issues": Field("text", P),
    },
    computed={
        "vendor_name": ("(SELECT name FROM vendors v WHERE v.id = systems.vendor_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = systems.owner_id)", S),
        "admin_name": ("(SELECT name FROM people p WHERE p.id = systems.admin_id)", S),
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
        "jira_keys": Field("keys", S),
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
        "jira_keys": Field("keys", S),
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
        "jira_keys": Field("keys", E),
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
        "jira_keys": Field("keys", E),
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
        "jira_keys": Field("keys", E),
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
        "jira_keys": Field("keys", S),
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
        "ticket_key": Field("key", S),
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
        "ticket_key": Field("key", S),
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
        "ticket_key": Field("key", S),
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

# ---- 30/60/90-day and six-month plans: shared with leadership, so exportable; the evidence stays private ----

plans = Record(
    entity="plan",
    table="plans",
    path="/api/plans",
    order_by="horizon_days",
    fields={
        "horizon_days": Field("int", E, required=True),
        "title": Field("text", E, required=True),
        "summary": Field("text", E),
        "status": Field("text", S, choices=PLAN_STATUS, default="draft"),
        "presented_on": Field("date", S),
        "audience": Field("text", S),
        "notes": Field("text", P),
    },
)

plan_items = Record(
    entity="plan_item",
    table="plan_items",
    path="/api/plan-items",
    order_by="plan_id, position, id",
    fields={
        "plan_id": Field("int", E, required=True),
        "kind": Field("text", E, choices=PLAN_ITEM_KINDS, default="action"),
        "title": Field("text", E, required=True),
        "detail": Field("text", E),
        "owner_id": Field("int", S),
        "due_day": Field("int", E),
        "status": Field("text", E, choices=PLAN_ITEM_STATUS, default="planned"),
        "themes": Field("list", S),
        "evidence": Field("text", P),
        "position": Field("int", S, default=0),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = plan_items.owner_id)", S)},
)

# ---- business landscape: structure is presentable; the assessment is [employer]'s confidential view, so private ----

departments = Record(
    entity="department",
    table="departments",
    path="/api/departments",
    order_by="position, name",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=DEPARTMENT_KINDS, default="department"),
        "parent_id": Field("int", S),
        "leader_id": Field("int", S),
        "purpose": Field("text", S),
        "notes": Field("text", P),
        "position": Field("int", S, default=0),
    },
    computed={
        "leader_name": ("(SELECT name FROM people p WHERE p.id = departments.leader_id)", S),
        "parent_name": ("(SELECT name FROM departments d WHERE d.id = departments.parent_id)", S),
    },
)

offerings = Record(
    entity="offering",
    table="offerings",
    path="/api/offerings",
    order_by="status = 'retired', name",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=OFFERING_KINDS, default="product"),
        "description": Field("text", S),
        "customers": Field("text", S),
        "department_id": Field("int", S),
        "system_ids": Field("ids", S),
        "vendor_ids": Field("ids", S),
        "maturity": Field("text", S, choices=MATURITY),
        "status": Field("text", S, choices=OFFERING_STATUS, default="active"),
        "notes": Field("text", P),
    },
    computed={"department_name": ("(SELECT name FROM departments d WHERE d.id = offerings.department_id)", S)},
)

assessments = Record(
    entity="assessment",
    table="assessments",
    path="/api/assessments",
    order_by="status = 'closed', CASE confidence WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, id",
    fields={
        "subject_type": Field("text", P, required=True, choices=SUBJECT_TYPES),
        "subject_id": Field("int", P, required=True),
        "quadrant": Field("text", P, required=True, choices=QUADRANTS),
        "title": Field("text", P, required=True),
        "evidence": Field("text", P),
        "source": Field("text", P, choices=ASSESSMENT_SOURCES),
        "confidence": Field("text", P, choices=CONFIDENCE, default="medium"),
        "date": Field("date", P),
        "status": Field("text", P, choices=ASSESSMENT_STATUS, default="open"),
        "roadmap_item_id": Field("int", P),
        "risk_id": Field("int", P),
    },
    computed={
        "subject_name": ("(CASE assessments.subject_type WHEN 'offering' THEN (SELECT name FROM offerings o WHERE o.id = assessments.subject_id) ELSE (SELECT name FROM departments d WHERE d.id = assessments.subject_id) END)", P),
    },
    hide_when_empty=True,
)

# ---- QA resources: how the team tests is presentable; run notes stay private ----

test_cases = Record(
    entity="test_case",
    table="test_cases",
    path="/api/test-cases",
    order_by="active DESC, system_id IS NULL, area, title",
    fields={
        "title": Field("text", S, required=True),
        "system_id": Field("int", S),
        "area": Field("text", S),
        "kind": Field("text", S, choices=TEST_KINDS, default="smoke"),
        "priority": Field("text", S, choices=PRIORITIES, default="medium"),
        "preconditions": Field("text", S),
        "steps": Field("text", S),
        "expected": Field("text", S),
        "owner_id": Field("int", S),
        "active": Field("bool", S, default=True),
        "jira_keys": Field("keys", S),
    },
    computed={
        "system_name": ("(SELECT name FROM systems s WHERE s.id = test_cases.system_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = test_cases.owner_id)", S),
        "last_result": ("(SELECT r.result FROM test_results r JOIN test_runs u ON u.id = r.run_id WHERE r.case_id = test_cases.id AND r.result != 'not run' ORDER BY u.date DESC, u.id DESC LIMIT 1)", S),
        "last_run": ("(SELECT u.date FROM test_results r JOIN test_runs u ON u.id = r.run_id WHERE r.case_id = test_cases.id AND r.result != 'not run' ORDER BY u.date DESC, u.id DESC LIMIT 1)", S),
    },
)

regression_plans = Record(
    entity="regression_plan",
    table="regression_plans",
    path="/api/regression-plans",
    order_by="status IN ('signed off', 'done'), start_date IS NULL, start_date",
    fields={
        "title": Field("text", E, required=True),
        "kind": Field("text", E, choices=REGRESSION_KINDS, default="Salesforce release"),
        "start_date": Field("date", E),
        "end_date": Field("date", E),
        "owner_id": Field("int", S),
        "backup_owner_id": Field("int", S),
        "scope": Field("text", S),
        "case_ids": Field("ids", S),
        "status": Field("text", E, choices=REGRESSION_STATUS, default="planned"),
        "signoff_by_id": Field("int", S),
        "signoff_date": Field("date", E),
        "notes": Field("text", P),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = regression_plans.owner_id)", S),
        "backup_owner_name": ("(SELECT name FROM people p WHERE p.id = regression_plans.backup_owner_id)", S),
        "signoff_by_name": ("(SELECT name FROM people p WHERE p.id = regression_plans.signoff_by_id)", S),
    },
)

test_runs = Record(
    entity="test_run",
    table="test_runs",
    path="/api/test-runs",
    order_by="date IS NULL, date DESC, id DESC",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=RUN_KINDS, default="smoke"),
        "sprint_id": Field("int", S),
        "plan_id": Field("int", S),
        "release": Field("text", S),
        "environment": Field("text", S),
        "date": Field("date", S),
        "tester_id": Field("int", S),
        "status": Field("text", S, choices=RUN_STATUS, default="in progress"),
        "notes": Field("text", P),
    },
    computed={
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = test_runs.sprint_id)", S),
        "tester_name": ("(SELECT name FROM people p WHERE p.id = test_runs.tester_id)", S),
        "plan_title": ("(SELECT title FROM regression_plans g WHERE g.id = test_runs.plan_id)", S),
        "total": ("(SELECT COUNT(*) FROM test_results r WHERE r.run_id = test_runs.id)", S),
        "passed": ("(SELECT COUNT(*) FROM test_results r WHERE r.run_id = test_runs.id AND r.result = 'pass')", S),
        "failed": ("(SELECT COUNT(*) FROM test_results r WHERE r.run_id = test_runs.id AND r.result = 'fail')", S),
        "blocked": ("(SELECT COUNT(*) FROM test_results r WHERE r.run_id = test_runs.id AND r.result = 'blocked')", S),
        "not_run": ("(SELECT COUNT(*) FROM test_results r WHERE r.run_id = test_runs.id AND r.result = 'not run')", S),
    },
)

test_results = Record(
    entity="test_result",
    table="test_results",
    path="/api/test-results",
    order_by="run_id, id",
    fields={
        "run_id": Field("int", S, required=True),
        "case_id": Field("int", S, required=True),
        "result": Field("text", S, choices=RESULTS, default="not run"),
        "notes": Field("text", S),
        "action_item_id": Field("int", S),
        "jira_keys": Field("keys", S),
    },
)

test_suites = Record(
    entity="test_suite",
    table="test_suites",
    path="/api/test-suites",
    order_by="last_result = 'failing' DESC, last_result = 'flaky' DESC, name",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=SUITE_KINDS, default="unit"),
        "system_id": Field("int", S),
        "framework": Field("text", S),
        "location": Field("text", S),
        "ci_link": Field("text", S),
        "owner_id": Field("int", S),
        "test_count": Field("int", S),
        "coverage": Field("number", S),
        "last_result": Field("text", S, choices=SUITE_RESULTS, default="unknown"),
        "last_run": Field("date", S),
        "notes": Field("text", P),
    },
    computed={
        "system_name": ("(SELECT name FROM systems s WHERE s.id = test_suites.system_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = test_suites.owner_id)", S),
    },
)

# ---- architecture: how the systems fit together; known weaknesses and integration notes stay private ----

integrations = Record(
    entity="integration",
    table="integrations",
    path="/api/integrations",
    order_by="status = 'retired', name",
    fields={
        "name": Field("text", S, required=True),
        "from_id": Field("int", S, required=True),
        "to_id": Field("int", S, required=True),
        "via_id": Field("int", S),
        "pattern": Field("text", S, choices=INTEGRATION_PATTERNS, default="API"),
        "direction": Field("text", S, choices=INTEGRATION_DIRECTIONS, default="one way"),
        "data": Field("text", S),
        "frequency": Field("text", S),
        "protocol": Field("text", S),
        "owner_id": Field("int", S),
        "criticality": Field("text", S, choices=CRITICALITY),
        "status": Field("text", S, choices=INTEGRATION_STATUS, default="live"),
        "notes": Field("text", P),
    },
    computed={
        "from_name": ("(SELECT name FROM systems s WHERE s.id = integrations.from_id)", S),
        "to_name": ("(SELECT name FROM systems s WHERE s.id = integrations.to_id)", S),
        "via_name": ("(SELECT name FROM systems s WHERE s.id = integrations.via_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = integrations.owner_id)", S),
    },
)

arch_decisions = Record(
    entity="arch_decision",
    table="arch_decisions",
    path="/api/arch-decisions",
    order_by="number DESC",
    fields={
        "number": Field("int", S),
        "title": Field("text", S, required=True),
        "status": Field("text", S, choices=ADR_STATUS, default="proposed"),
        "date": Field("date", S),
        "context": Field("text", S),
        "decision": Field("text", S),
        "consequences": Field("text", S),
        "alternatives": Field("text", S),
        "system_ids": Field("ids", S),
        "decided_by_id": Field("int", S),
        "superseded_by_id": Field("int", S),
        "jira_keys": Field("keys", S),
    },
    computed={
        "decided_by_name": ("(SELECT name FROM people p WHERE p.id = arch_decisions.decided_by_id)", S),
        "superseded_by_number": ("(SELECT number FROM arch_decisions d WHERE d.id = arch_decisions.superseded_by_id)", S),
    },
)

guides = Record(
    entity="guide",
    table="guides",
    path="/api/guides",
    order_by="title",
    fields={
        "title": Field("text", S, required=True),
        "summary": Field("text", S),
        "body": Field("text", S),
        "system_ids": Field("ids", S),
        "audience": Field("text", S),
        "updated": Field("date", S),
    },
)

# ---- onboarding: the checklist and material for a new team member; how it went for them stays private ----

onboarding_items = Record(
    entity="onboarding_item",
    table="onboarding_items",
    path="/api/onboarding-items",
    order_by="due_day IS NULL, due_day, position, id",
    fields={
        "title": Field("text", S, required=True),
        "description": Field("text", S),
        "category": Field("text", S, choices=ONBOARDING_CATEGORIES, default="ways of working"),
        "due_day": Field("int", S),
        "owner_role": Field("text", S, choices=ONBOARDING_OWNERS, default="new member"),
        "tracks": Field("list", S),
        "link": Field("text", S),
        "minutes": Field("int", S),
        "active": Field("bool", S, default=True),
        "position": Field("int", S, default=0),
    },
)

onboardings = Record(
    entity="onboarding",
    table="onboardings",
    path="/api/onboardings",
    order_by="status = 'done', start_date DESC, id DESC",
    fields={
        "person_id": Field("int", S, required=True),
        "start_date": Field("date", S),
        "tracks": Field("list", S),
        "buddy_id": Field("int", S),
        "status": Field("text", S, choices=ONBOARDING_STATUS, default="in progress"),
        "notes": Field("text", P),
    },
    computed={
        "person_name": ("(SELECT name FROM people p WHERE p.id = onboardings.person_id)", S),
        "person_role": ("(SELECT role FROM people p WHERE p.id = onboardings.person_id)", S),
        "buddy_name": ("(SELECT name FROM people p WHERE p.id = onboardings.buddy_id)", S),
        "total": ("(SELECT COUNT(*) FROM onboarding_tasks t WHERE t.onboarding_id = onboardings.id)", S),
        "done_count": ("(SELECT COUNT(*) FROM onboarding_tasks t WHERE t.onboarding_id = onboardings.id AND t.done = 1)", S),
    },
)

onboarding_tasks = Record(
    entity="onboarding_task",
    table="onboarding_tasks",
    path="/api/onboarding-tasks",
    order_by="onboarding_id, due_day IS NULL, due_day, id",
    fields={
        "onboarding_id": Field("int", S, required=True),
        "item_id": Field("int", S),
        "title": Field("text", S, required=True),
        "description": Field("text", S),
        "category": Field("text", S, choices=ONBOARDING_CATEGORIES, default="ways of working"),
        "due_day": Field("int", S),
        "owner_role": Field("text", S, choices=ONBOARDING_OWNERS, default="new member"),
        "link": Field("text", S),
        "minutes": Field("int", S),
        "done": Field("bool", S, default=False),
        "done_on": Field("date", S),
        "notes": Field("text", P),
        "jira_keys": Field("keys", S),
    },
)

# ---- SDLC: how work moves from idea to production; a shared document, so exportable ----

sdlc_stages = Record(
    entity="sdlc_stage",
    table="sdlc_stages",
    path="/api/sdlc-stages",
    order_by="position, id",
    fields={
        "name": Field("text", E, required=True),
        "position": Field("int", E, default=0),
        "purpose": Field("text", E),
        "entry_criteria": Field("list", E),
        "exit_criteria": Field("list", E),
        "activities": Field("text", E),
        "roles": Field("text", E),
        "artifacts": Field("text", E),
        "system_ids": Field("ids", E),
        "environment": Field("text", E),
        "duration": Field("text", E),
        "links": Field("text", E),
        "notes": Field("text", P),
    },
)

sdlc_environments = Record(
    entity="sdlc_environment",
    table="sdlc_environments",
    path="/api/sdlc-environments",
    order_by="platform, position, id",
    fields={
        "name": Field("text", E, required=True),
        "position": Field("int", E, default=0),
        "platform": Field("text", E),
        "purpose": Field("text", E),
        "data": Field("text", E),
        "deploys_by": Field("text", E),
        "refresh": Field("text", E),
        "system_id": Field("int", E),
        "notes": Field("text", P),
    },
    computed={"system_name": ("(SELECT name FROM systems s WHERE s.id = sdlc_environments.system_id)", E)},
)

sdlc_policies = Record(
    entity="sdlc_policy",
    table="sdlc_policies",
    path="/api/sdlc-policies",
    order_by="status = 'retired', category, title",
    fields={
        "title": Field("text", E, required=True),
        "category": Field("text", E, choices=POLICY_CATEGORIES, default="other"),
        "body": Field("text", E),
        "status": Field("text", E, choices=POLICY_STATUS, default="draft"),
        "agreed_on": Field("date", E),
        "owner_id": Field("int", S),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = sdlc_policies.owner_id)", S)},
)

# ---- coaching: guides, tips and prompts are shareable with other leaders; your notes and reflections are private ----

coaching_guides = Record(
    entity="coaching_guide",
    table="coaching_guides",
    path="/api/coaching-guides",
    order_by="theme, title",
    fields={
        "slug": Field("text", E, required=True),
        "theme": Field("text", E, default="transition"),
        "title": Field("text", E, required=True),
        "summary": Field("text", E),
        "why": Field("text", E),
        "practices": Field("list", E),
        "pitfalls": Field("list", E),
        "questions": Field("list", E),
        "try_this": Field("list", E),
        "body": Field("text", E),
        "related": Field("list", E),
        "reading": Field("list", E),
        "inspired_by": Field("text", E),
        "minutes": Field("int", E),
        "origin": Field("text", E, choices=GUIDE_ORIGINS, default="mine"),
        "status": Field("text", E, choices=GUIDE_STATUS, default="published"),
        "focus": Field("text", P, choices=GUIDE_FOCUS),
        "my_notes": Field("text", P),
    },
)

coaching_tips = Record(
    entity="coaching_tip",
    table="coaching_tips",
    path="/api/coaching-tips",
    order_by="route, position, id",
    fields={
        "route": Field("text", E, required=True),
        "text": Field("text", E, required=True),
        "guide_slug": Field("text", E),
        "active": Field("bool", E, default=True),
        "position": Field("int", E, default=0),
    },
)

coaching_prompts = Record(
    entity="coaching_prompt",
    table="coaching_prompts",
    path="/api/coaching-prompts",
    order_by="position, id",
    fields={
        "phase": Field("text", E, default="Any time"),
        "text": Field("text", E, required=True),
        "active": Field("bool", E, default=True),
        "position": Field("int", E, default=0),
    },
)

reflections = Record(
    entity="reflection",
    table="reflections",
    path="/api/reflections",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "prompt": Field("text", P),
        "entry": Field("text", P),
        "energy": Field("int", P),
        "confidence": Field("int", P),
        "tags": Field("list", P),
    },
    hide_when_empty=True,
)

# ---- technical debt: the register is shareable with leadership; notes stay private ----

tech_debt = Record(
    entity="tech_debt",
    table="tech_debt",
    path="/api/tech-debt",
    order_by="status IN ('done', 'won''t fix'), id DESC",
    fields={
        "title": Field("text", E, required=True),
        "description": Field("text", E),
        "categories": Field("list", E),
        "system_ids": Field("ids", E),
        "impact": Field("int", E),
        "risk": Field("int", E),
        "effort": Field("text", E, choices=DEBT_EFFORT),
        "points": Field("int", E),
        "cost_of_delay": Field("text", E),
        "evidence": Field("text", S),
        "trigger_date": Field("date", E),
        "trigger_reason": Field("text", E),
        "status": Field("text", E, choices=DEBT_STATUS, default="identified"),
        "sprint_id": Field("int", E),
        "ticket_key": Field("key", E),
        "owner_id": Field("int", S),
        "revisit_on": Field("date", E),
        "identified_on": Field("date", E),
        "raised_by": Field("text", S),
        "notes": Field("text", P),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = tech_debt.owner_id)", S),
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = tech_debt.sprint_id)", E),
    },
)

debt_decisions = Record(
    entity="debt_decision",
    table="debt_decisions",
    path="/api/debt-decisions",
    order_by="date DESC, id DESC",
    fields={
        "debt_id": Field("int", E, required=True),
        "date": Field("date", E, required=True),
        "decision": Field("text", E, choices=DEBT_DECISIONS, required=True),
        "rationale": Field("text", E),
        "decided_by": Field("text", E),
        "revisit_on": Field("date", E),
    },
)

RECORDS = [
    people, interviews, learning_goals, learning_log, tasks, obligations,
    action_items, learning_sessions, systems, severities, escalation_steps, incidents,
    vendors, vendor_interactions, vendor_concerns,
    program_increments, sprints, ceremony_notes, roadmap_items, raci_decisions, risks, decisions_needed, metrics, metric_readings,
    retros, retro_items, retro_commitments,
    pi_objectives, epics, features, stories, dependencies, pi_milestones, pi_risks,
    plans, plan_items,
    departments, offerings, assessments,
    test_cases, regression_plans, test_runs, test_results, test_suites,
    integrations, arch_decisions, guides,
    onboarding_items, onboardings, onboarding_tasks,
    sdlc_stages, sdlc_environments, sdlc_policies,
    coaching_guides, coaching_tips, coaching_prompts, reflections,
    tech_debt, debt_decisions,
]
