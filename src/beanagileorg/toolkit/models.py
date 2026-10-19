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
DEVSYNC_KINDS = ("question", "offer to present", "decision needed", "idea", "action")
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
PLAN_STATUS = ("draft", "reviewed", "presented", "agreed")
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
ONBOARDING_CATEGORIES = ("accounts and access", "tools and setup", "business", "people", "ways of working", "systems and architecture", "learning", "first work", "admin and compliance")
ONBOARDING_OWNERS = ("new member", "manager", "buddy", "IT or admin")
ONBOARDING_TRACKS = ("Salesforce developer", "MuleSoft developer", "QA", "employee", "contractor")
ONBOARDING_STATUS = ("not started", "in progress", "done")
POLICY_CATEGORIES = ("branching", "code review", "testing", "release", "change management", "hotfix", "security", "data", "documentation", "communication", "other")
POLICY_STATUS = ("draft", "agreed", "retired")
GUIDE_STATUS = ("draft", "published")
GUIDE_FOCUS = ("want to work on", "practicing", "comfortable")
GUIDE_ORIGINS = ("built-in", "mine", "imported")
DEBT_CATEGORIES = ("maintainability", "stability", "performance", "cleanup", "revenue and conversion", "observability", "security", "delivery speed", "cost")
DEBT_EFFORT = ("S", "M", "L", "XL")
DEBT_STATUS = ("identified", "accepted", "planned", "in progress", "done", "won't fix")
DEBT_DECISIONS = ("fix now", "schedule", "accept for now", "won't fix")
BACKLOG_TYPES = ("story", "bug", "task", "spike", "tech debt")
BACKLOG_STATUS = ("needs refinement", "ready", "in sprint", "done", "removed")
ESTIMATE_CONFIDENCE = ("low", "medium", "high")
PLAN_STATUS_SPRINT = ("planning", "committed", "closed")
TEAM_KINDS = ("mine", "other")
TEAM_STATUS = ("on track", "at risk", "off track")
SOS_KINDS = ("issue", "dependency", "decision", "risk", "impediment", "knowledge")
SOS_STATUS = ("open", "in progress", "waiting", "done")
INFLUENCE = ("low", "medium", "high")
STANCE = ("champion", "supporter", "neutral", "skeptic", "blocker")
INTERACTION_KINDS = ("one-on-one", "meeting", "call", "message", "conversation", "other")
MOODS = ("great", "good", "mixed", "tense", "difficult")
COMMITMENT_DIRECTIONS = ("mine", "theirs")
COMMITMENT_STATES = ("open", "done", "dropped")
MANAGER_NOTE_KINDS = ("praise", "constructive", "win", "concern")
GROWTH_STATUS = ("active", "achieved", "paused", "dropped")
CULTURE_SCOPES = ("my team", "organization")
CULTURE_KINDS = ("concern", "positive")
CULTURE_CATEGORIES = ("intimidation or dominating", "chaos or missing process", "quiet voices unheard", "blame", "siloed teams", "disrespect", "burnout or overload",
                      "heroics", "great collaboration", "speaking up", "helping others", "other")
CULTURE_ACTIONS = ("not yet", "watching", "spoke privately", "raised with the team", "raised with my manager", "agreement or process change", "escalated")
CULTURE_STATUS = ("open", "watching", "addressed")
SEVERITY = ("low", "medium", "high")
AGREEMENT_AREAS = ("working together", "disagreement", "meetings", "code review", "communication", "quality", "other")
AGREEMENT_STATUS = ("proposed", "agreed", "retired")
LOG_KINDS = ("win", "progress", "blocker", "risk", "decision", "ask", "next", "note")
LOG_AUDIENCES = ("leadership", "my manager", "just me")
REPORT_KINDS = ("weekly", "sprint")
REPORT_AUDIENCES = ("leadership", "my manager")
REPORT_STATUS = ("draft", "sent")
CHANGE_AREAS = ("process", "ceremonies", "quality", "tooling", "communication", "roles", "other")
CHANGE_STATUS = ("idea", "announced", "trial", "review", "adopted", "dropped")
MANDATE_STATUS = ("draft", "discussed", "agreed")
LEARNING_AREAS = ("business", "past", "present", "future", "people", "culture", "technical", "products and customers", "politics")
LEARNING_STATUS = ("open", "answered", "dropped")
HYPOTHESIS_VERDICTS = ("testing", "supported", "disproved", "mixed")
SITUATION_KINDS = ("start-up", "turnaround", "accelerated growth", "realignment", "sustaining success")
SITUATION_ELEMENTS = ("product", "process", "project", "system", "team")
CHANGE_STYLES = ("hero", "steward", "both")
CONVERSATION_STATUS = ("not started", "in progress", "settled")
BEHAVIOR_PATTERNS = ("lack of focus", "lack of discipline", "lack of innovation", "lack of teamwork", "lack of urgency", "other")
BEHAVIOR_STATUS = ("noticed", "working on it", "improving", "changed")
PRACTICE_STATUS = ("shared", "trying", "adopted", "dropped")
MANDATE_ITEM_KINDS = ("outcome", "decision")
AUTHORITY = ("to clarify", "I decide", "I decide and inform", "I recommend, someone else decides", "I'm consulted", "not mine")
MANDATE_ITEM_STATUS = ("open", "on track", "at risk", "done", "dropped")
CR_SOURCES = ("leadership", "stakeholder", "product owner", "customer", "production issue", "another team", "the team")
CR_URGENCY = ("next sprint is fine", "this sprint", "emergency")
CR_GOAL_IMPACT = ("doesn't affect the goal", "puts the goal at risk", "changes the goal", "makes the goal obsolete")
CR_STATUS = ("received", "assessing", "decided", "closed")
CR_DECISIONS = ("accepted with a swap", "accepted without a swap", "deferred to the backlog", "rejected", "sprint cancelled")
PULSE_SOURCES = ("my read", "team survey")
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
    (
        15,
        """
        CREATE TABLE backlog_items (
            id INTEGER PRIMARY KEY,
            jira_key TEXT,
            title TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'story',
            description TEXT,
            acceptance TEXT,
            technical_notes TEXT,
            dependencies TEXT,
            rank INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'needs refinement',
            ready_checks TEXT,
            points INTEGER,
            confidence TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            carried_from_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            feature_id INTEGER REFERENCES features (id) ON DELETE SET NULL,
            debt_id INTEGER REFERENCES tech_debt (id) ON DELETE SET NULL,
            system_ids TEXT,
            labels TEXT,
            added_on DATE,
            notes TEXT
        );
        CREATE UNIQUE INDEX backlog_items_jira ON backlog_items (jira_key) WHERE jira_key IS NOT NULL;
        CREATE TABLE estimate_votes (
            id INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES backlog_items (id) ON DELETE CASCADE,
            person_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            points INTEGER NOT NULL,
            round INTEGER NOT NULL DEFAULT 1,
            date DATE
        );
        CREATE TABLE sprint_plans (
            id INTEGER PRIMARY KEY,
            sprint_id INTEGER NOT NULL UNIQUE REFERENCES sprints (id) ON DELETE CASCADE,
            focus_factor REAL NOT NULL DEFAULT 0.8,
            capacity_override INTEGER,
            status TEXT NOT NULL DEFAULT 'planning',
            committed_points INTEGER,
            committed_on DATE,
            completed_points INTEGER,
            closed_on DATE,
            notes TEXT
        );
        CREATE TABLE sprint_availability (
            id INTEGER PRIMARY KEY,
            sprint_id INTEGER NOT NULL REFERENCES sprints (id) ON DELETE CASCADE,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            days INTEGER,
            note TEXT,
            UNIQUE (sprint_id, person_id)
        );
        """,
    ),
    (
        16,
        """
        ALTER TABLE sdlc_environments ADD COLUMN branch TEXT;
        ALTER TABLE sdlc_environments ADD COLUMN deploy_method TEXT;
        """,
    ),
    (
        17,
        """
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'other',
            purpose TEXT,
            product_owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            scrum_master_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            lead_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            member_ids TEXT,
            jira_project TEXT,
            board_url TEXT,
            cadence TEXT,
            system_ids TEXT,
            status TEXT,
            status_note TEXT,
            status_date DATE,
            current_sprint TEXT,
            sprint_ends DATE,
            current_goal TEXT,
            notes TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO teams (name, kind, position) VALUES ('My team', 'mine', 0);
        ALTER TABLE action_items ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE action_items SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE sprints ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE sprints SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE risks ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE risks SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE decisions_needed ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE decisions_needed SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE retros ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE retros SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE test_runs ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE test_runs SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE tech_debt ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE tech_debt SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        ALTER TABLE backlog_items ADD COLUMN team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL;
        UPDATE backlog_items SET team_id = (SELECT id FROM teams WHERE kind = 'mine' LIMIT 1);
        CREATE TRIGGER action_items_default_team AFTER INSERT ON action_items WHEN NEW.team_id IS NULL
        BEGIN UPDATE action_items SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER sprints_default_team AFTER INSERT ON sprints WHEN NEW.team_id IS NULL
        BEGIN UPDATE sprints SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER risks_default_team AFTER INSERT ON risks WHEN NEW.team_id IS NULL
        BEGIN UPDATE risks SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER decisions_needed_default_team AFTER INSERT ON decisions_needed WHEN NEW.team_id IS NULL
        BEGIN UPDATE decisions_needed SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER retros_default_team AFTER INSERT ON retros WHEN NEW.team_id IS NULL
        BEGIN UPDATE retros SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER test_runs_default_team AFTER INSERT ON test_runs WHEN NEW.team_id IS NULL
        BEGIN UPDATE test_runs SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER tech_debt_default_team AFTER INSERT ON tech_debt WHEN NEW.team_id IS NULL
        BEGIN UPDATE tech_debt SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TRIGGER backlog_items_default_team AFTER INSERT ON backlog_items WHEN NEW.team_id IS NULL
        BEGIN UPDATE backlog_items SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TABLE sos_items (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'issue',
            details TEXT,
            raised_by_team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            team_ids TEXT,
            stakeholder_ids TEXT,
            owner_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            owner_team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            outcome TEXT,
            raised_on DATE,
            due DATE,
            status TEXT NOT NULL DEFAULT 'open',
            resolution TEXT,
            jira_keys TEXT,
            notes TEXT
        );
        CREATE TABLE sos_meetings (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            team_ids TEXT,
            item_ids TEXT,
            summary TEXT,
            notes TEXT
        );
        """,
    ),
    (
        18,
        """
        ALTER TABLE people ADD COLUMN tags TEXT;
        ALTER TABLE people ADD COLUMN cadence_days INTEGER;
        ALTER TABLE people ADD COLUMN influence TEXT;
        ALTER TABLE people ADD COLUMN stance TEXT;
        ALTER TABLE people ADD COLUMN communication TEXT;
        ALTER TABLE people ADD COLUMN motivations TEXT;
        ALTER TABLE people ADD COLUMN personal_context TEXT;
        ALTER TABLE people ADD COLUMN things_to_remember TEXT;
        ALTER TABLE people ADD COLUMN key_dates TEXT;
        ALTER TABLE people ADD COLUMN next_meeting DATE;
        ALTER TABLE people ADD COLUMN manager_id INTEGER REFERENCES people (id) ON DELETE SET NULL;
        CREATE TABLE interactions (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            kind TEXT NOT NULL DEFAULT 'one-on-one',
            title TEXT,
            person_ids TEXT,
            notes TEXT,
            takeaways TEXT,
            follow_ups TEXT,
            mood TEXT
        );
        ALTER TABLE action_items ADD COLUMN interaction_id INTEGER REFERENCES interactions (id) ON DELETE SET NULL;
        """,
    ),
    (
        19,
        """
        CREATE TABLE commitments (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            direction TEXT NOT NULL DEFAULT 'mine',
            title TEXT NOT NULL,
            details TEXT,
            due DATE,
            status TEXT NOT NULL DEFAULT 'open',
            done_on DATE,
            created_on DATE,
            interaction_id INTEGER REFERENCES interactions (id) ON DELETE SET NULL,
            jira_keys TEXT
        );
        CREATE TABLE manager_notes (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            date DATE NOT NULL,
            kind TEXT NOT NULL DEFAULT 'praise',
            note TEXT NOT NULL,
            shared INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE growth_goals (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            goal TEXT NOT NULL,
            measure TEXT,
            target_date DATE,
            status TEXT NOT NULL DEFAULT 'active',
            progress TEXT,
            updated DATE
        );
        """,
    ),
    (
        20,
        """
        CREATE TABLE standards (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            why TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE standard_checks (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            standard_id INTEGER NOT NULL REFERENCES standards (id) ON DELETE CASCADE,
            rating INTEGER NOT NULL,
            note TEXT
        );
        CREATE TABLE trust_pulses (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            source TEXT NOT NULL DEFAULT 'my read',
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            scores TEXT,
            respondents INTEGER,
            notes TEXT
        );
        CREATE TABLE culture_observations (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            scope TEXT NOT NULL DEFAULT 'my team',
            kind TEXT NOT NULL DEFAULT 'concern',
            category TEXT,
            title TEXT NOT NULL,
            details TEXT,
            people_ids TEXT,
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            severity TEXT,
            action TEXT NOT NULL DEFAULT 'not yet',
            status TEXT NOT NULL DEFAULT 'open',
            follow_up DATE,
            outcome TEXT
        );
        CREATE TABLE team_agreements (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            area TEXT NOT NULL DEFAULT 'working together',
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'proposed',
            agreed_on DATE,
            review_on DATE,
            position INTEGER NOT NULL DEFAULT 0
        );
        """,
    ),
    (
        21,
        """
        CREATE TABLE work_log (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            kind TEXT NOT NULL DEFAULT 'progress',
            text TEXT NOT NULL,
            details TEXT,
            audience TEXT NOT NULL DEFAULT 'leadership',
            jira_keys TEXT,
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            source_entity TEXT,
            source_id INTEGER
        );
        CREATE INDEX work_log_date ON work_log (date);
        CREATE TRIGGER work_log_default_team AFTER INSERT ON work_log WHEN NEW.team_id IS NULL
        BEGIN UPDATE work_log SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TABLE reports (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL DEFAULT 'weekly',
            audience TEXT NOT NULL DEFAULT 'leadership',
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            markdown TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            sent_on DATE,
            sent_to TEXT,
            created_on DATE NOT NULL DEFAULT CURRENT_DATE
        );
        """,
    ),
    (
        22,
        """
        CREATE TABLE change_requests (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            source TEXT NOT NULL DEFAULT 'stakeholder',
            requested_by_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            requested_on DATE NOT NULL,
            needed_by DATE,
            sprint_id INTEGER REFERENCES sprints (id) ON DELETE SET NULL,
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            urgency TEXT NOT NULL DEFAULT 'this sprint',
            value TEXT,
            goal_impact TEXT,
            points INTEGER,
            status TEXT NOT NULL DEFAULT 'received',
            decision TEXT,
            decided_by_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            decided_on DATE,
            decision_reason TEXT,
            swapped_out_ids TEXT,
            points_out INTEGER,
            backlog_item_id INTEGER REFERENCES backlog_items (id) ON DELETE SET NULL,
            communicated_on DATE,
            jira_keys TEXT,
            notes TEXT
        );
        CREATE TRIGGER change_requests_default_team AFTER INSERT ON change_requests WHEN NEW.team_id IS NULL
        BEGIN UPDATE change_requests SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        """,
    ),
    (
        23,
        """
        CREATE TABLE team_changes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            area TEXT NOT NULL DEFAULT 'process',
            why TEXT,
            what_changes TEXT,
            how_we_try TEXT,
            status TEXT NOT NULL DEFAULT 'idea',
            announced_on DATE,
            trial_start DATE,
            review_on DATE,
            decided_on DATE,
            outcome TEXT,
            team_feedback TEXT,
            agreement_id INTEGER REFERENCES team_agreements (id) ON DELETE SET NULL,
            team_id INTEGER REFERENCES teams (id) ON DELETE SET NULL,
            notes TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TRIGGER team_changes_default_team AFTER INSERT ON team_changes WHEN NEW.team_id IS NULL
        BEGIN UPDATE team_changes SET team_id = (SELECT id FROM teams WHERE kind = 'mine' ORDER BY id LIMIT 1) WHERE id = NEW.id; END;
        CREATE TABLE first90_milestones (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            due_day INTEGER NOT NULL,
            auto TEXT,
            done_on DATE,
            note TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        """,
    ),
    (
        24,
        """
        ALTER TABLE people ADD COLUMN placeholder INTEGER NOT NULL DEFAULT 0;
        """,
    ),
    (
        25,
        """
        CREATE TABLE mandates (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            mine INTEGER NOT NULL DEFAULT 0,
            purpose TEXT,
            boundaries TEXT,
            resources TEXT,
            questions TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            agreed_with_id INTEGER REFERENCES people (id) ON DELETE SET NULL,
            agreed_on DATE,
            review_on DATE,
            notes TEXT
        );
        CREATE UNIQUE INDEX mandates_person ON mandates (person_id);
        CREATE TABLE mandate_items (
            id INTEGER PRIMARY KEY,
            mandate_id INTEGER NOT NULL REFERENCES mandates (id) ON DELETE CASCADE,
            kind TEXT NOT NULL DEFAULT 'outcome',
            text TEXT NOT NULL,
            measure TEXT,
            due_day INTEGER,
            authority TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            position INTEGER NOT NULL DEFAULT 0
        );
        """,
    ),
    (
        26,
        """
        ALTER TABLE people ADD COLUMN offer_them TEXT;
        ALTER TABLE people ADD COLUMN need_from_them TEXT;
        """,
    ),
    (
        27,
        """
        CREATE TABLE learning_questions (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            area TEXT NOT NULL DEFAULT 'present',
            ask_ids TEXT,
            due_day INTEGER,
            answer TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE situations (
            id INTEGER PRIMARY KEY,
            area TEXT NOT NULL,
            kind TEXT,
            evidence TEXT,
            approach TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        ALTER TABLE plan_items ADD COLUMN early_win INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE plans ADD COLUMN agreed_on DATE;
        ALTER TABLE plans ADD COLUMN agreed_with_id INTEGER REFERENCES people (id) ON DELETE SET NULL;
        CREATE TABLE boss_conversations (
            id INTEGER PRIMARY KEY,
            topic TEXT NOT NULL,
            prompt TEXT,
            held_on DATE,
            agreed TEXT,
            open_points TEXT,
            next_on DATE,
            notes TEXT,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE mentoring_sessions (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            date DATE NOT NULL,
            topic TEXT,
            notes TEXT,
            next_step TEXT,
            next_on DATE
        );
        CREATE TABLE mentored_practices (
            id INTEGER PRIMARY KEY,
            person_id INTEGER NOT NULL REFERENCES people (id) ON DELETE CASCADE,
            practice TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'shared',
            since DATE,
            notes TEXT
        );
        """,
    ),
    (
        28,
        """
        ALTER TABLE action_items ADD COLUMN kind TEXT;
        ALTER TABLE action_items ADD COLUMN expert_ids TEXT;
        ALTER TABLE action_items ADD COLUMN decider_id INTEGER REFERENCES people (id) ON DELETE SET NULL;
        ALTER TABLE action_items ADD COLUMN on_board INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE action_items ADD COLUMN update_url TEXT;
        ALTER TABLE action_items ADD COLUMN update_on DATE;
        """,
    ),
    (
        29,
        """
        ALTER TABLE people ADD COLUMN expects_from_me TEXT;
        ALTER TABLE systems ADD COLUMN business_contact_ids TEXT;
        CREATE TABLE culture_reads (
            id INTEGER PRIMARY KEY,
            unit TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            symbols TEXT,
            influence TEXT,
            meetings TEXT,
            execution TEXT,
            conflict TEXT,
            recognition TEXT,
            ends_means TEXT,
            power TEXT,
            adapt_or_change TEXT,
            privacy_ceiling INTEGER,
            source TEXT NOT NULL DEFAULT 'me',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE glossary_terms (
            id INTEGER PRIMARY KEY,
            term TEXT NOT NULL,
            meaning TEXT,
            used_by TEXT,
            privacy_ceiling INTEGER,
            source TEXT NOT NULL DEFAULT 'me',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    (
        30,
        """
        CREATE TABLE preference_assessments (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            scores TEXT,
            notes TEXT,
            privacy_ceiling INTEGER,
            source TEXT NOT NULL DEFAULT 'me',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    (
        31,
        """
        ALTER TABLE preference_assessments ADD COLUMN hammer TEXT;
        ALTER TABLE preference_assessments ADD COLUMN plan TEXT;
        ALTER TABLE people ADD COLUMN advice TEXT;
        """,
    ),
    (
        32,
        """
        ALTER TABLE learning_questions ADD COLUMN hypothesis TEXT;
        ALTER TABLE learning_questions ADD COLUMN disprove_if TEXT;
        ALTER TABLE learning_questions ADD COLUMN verdict TEXT;
        """,
    ),
    (
        33,
        """
        ALTER TABLE interviews ADD COLUMN if_you_were_me TEXT;
        ALTER TABLE interviews ADD COLUMN how_answered TEXT;
        ALTER TABLE people ADD COLUMN insight TEXT;
        """,
    ),
    (
        34,
        """
        ALTER TABLE situations ADD COLUMN history TEXT;
        ALTER TABLE situations ADD COLUMN mood TEXT;
        """,
    ),
    (
        35,
        """
        ALTER TABLE situations ADD COLUMN opportunities TEXT;
        """,
    ),
    (
        36,
        """
        ALTER TABLE situations ADD COLUMN element TEXT;
        ALTER TABLE situations ADD COLUMN effort INTEGER;
        """,
    ),
    (
        37,
        """
        ALTER TABLE metrics ADD COLUMN benchmark TEXT;
        ALTER TABLE metrics ADD COLUMN benchmark_source TEXT;
        """,
    ),
    (
        38,
        """
        ALTER TABLE people ADD COLUMN change_style TEXT;
        """,
    ),
    (
        39,
        """
        ALTER TABLE boss_conversations ADD COLUMN status TEXT;
        ALTER TABLE boss_conversations ADD COLUMN next_30 TEXT;
        """,
    ),
    (
        40,
        """
        ALTER TABLE first90_milestones ADD COLUMN not_done INTEGER NOT NULL DEFAULT 0;
        """,
    ),
    (
        41,
        """
        ALTER TABLE plan_items ADD COLUMN serves_id INTEGER REFERENCES mandate_items (id) ON DELETE SET NULL;
        ALTER TABLE plan_items ADD COLUMN behavior TEXT;
        ALTER TABLE team_changes ADD COLUMN wave INTEGER;
        CREATE TABLE behavior_targets (
            id INTEGER PRIMARY KEY,
            pattern TEXT NOT NULL,
            symptoms TEXT,
            target TEXT,
            status TEXT NOT NULL DEFAULT 'noticed',
            notes TEXT,
            position INTEGER NOT NULL DEFAULT 0,
            privacy_ceiling INTEGER,
            source TEXT NOT NULL DEFAULT 'me',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    (
        42,
        """
        ALTER TABLE plan_items ADD COLUMN ew_scores TEXT;
        """,
    ),
    (
        43,
        """
        ALTER TABLE plan_items ADD COLUMN fog_lamp TEXT;
        ALTER TABLE plan_items ADD COLUMN lead_id INTEGER REFERENCES people (id) ON DELETE SET NULL;
        ALTER TABLE plan_items ADD COLUMN member_ids TEXT;
        ALTER TABLE people ADD COLUMN change_agent INTEGER NOT NULL DEFAULT 0;
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
        "tags": Field("list", P),
        "cadence_days": Field("int", P),
        "influence": Field("text", P, choices=INFLUENCE),
        "stance": Field("text", P, choices=STANCE),
        "communication": Field("text", P),
        "motivations": Field("text", P),
        "personal_context": Field("text", P),
        "things_to_remember": Field("list", P),
        "key_dates": Field("json", P),
        "next_meeting": Field("date", P),
        "manager_id": Field("int", S),
        "placeholder": Field("bool", S, default=False),
        "offer_them": Field("text", P),
        "need_from_them": Field("text", P),
        "expects_from_me": Field("text", P),
        "advice": Field("list", P),
        "insight": Field("list", P),
        "change_style": Field("text", P, choices=CHANGE_STYLES),
        "change_agent": Field("bool", P, default=False),
    },
    computed={
        "manager_name": ("(SELECT name FROM people m WHERE m.id = people.manager_id)", S),
        "department_name": ("(SELECT name FROM departments d WHERE d.id = people.department_id)", S),
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
        "if_you_were_me": Field("text", P),
        "how_answered": Field("text", P),
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
        "team_id": Field("int", S),
        "interaction_id": Field("int", P),
        "kind": Field("text", S, choices=DEVSYNC_KINDS),
        "expert_ids": Field("ids", S),
        "decider_id": Field("int", S),
        "on_board": Field("bool", P, default=False),
        "update_url": Field("text", S),
        "update_on": Field("date", S),
    },
    computed={
        "vendor_name": ("(SELECT name FROM vendors v WHERE v.id = action_items.vendor_id)", S),
        "owner_name": ("(SELECT name FROM people p WHERE p.id = action_items.owner_id)", S),
        "raised_by_name": ("(SELECT name FROM people p WHERE p.id = action_items.raised_by_id)", S),
        "decider_name": ("(SELECT name FROM people p WHERE p.id = action_items.decider_id)", S),
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
        "business_contact_ids": Field("ids", S),
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
        "team_id": Field("int", S),
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
        "team_id": Field("int", S),
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
        "team_id": Field("int", S),
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
        "benchmark": Field("text", E),
        "benchmark_source": Field("text", E),
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
        "team_id": Field("int", S),
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
        "agreed_on": Field("date", S),
        "agreed_with_id": Field("int", S),
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
        "early_win": Field("bool", E, default=False),
        "serves_id": Field("int", S),
        "ew_scores": Field("json", P),  # the early wins evaluation: impact, soon, foundation, behavior, 0 to 4 each
        "fog_lamp": Field("json", S),  # the project plan: focus, oversight, goals, leadership, abilities, means, process
        "lead_id": Field("int", S),
        "member_ids": Field("ids", S),
        "behavior": Field("text", S),
        "position": Field("int", S, default=0),
    },
    computed={"owner_name": ("(SELECT name FROM people p WHERE p.id = plan_items.owner_id)", S),
              "ew_total": ("(SELECT CASE WHEN plan_items.ew_scores IS NULL THEN NULL ELSE (SELECT SUM(value) FROM json_each(plan_items.ew_scores)) END)", P)},
)

# ---- business landscape: structure is presentable; the assessment is the company's confidential view, so private ----

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
        "team_id": Field("int", S),
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
        "branch": Field("text", E),
        "deploy_method": Field("text", E),
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
        "team_id": Field("int", S),
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

# ---- sprint planning: the backlog of candidate stories beside Jira, estimates, and each sprint's plan ----

backlog_items = Record(
    entity="backlog_item",
    table="backlog_items",
    path="/api/backlog-items",
    order_by="status IN ('done', 'removed'), rank, id",
    fields={
        "jira_key": Field("key", S),
        "title": Field("text", S, required=True),
        "item_type": Field("text", S, choices=BACKLOG_TYPES, default="story"),
        "description": Field("text", S),
        "acceptance": Field("text", S),
        "technical_notes": Field("text", S),
        "dependencies": Field("text", S),
        "rank": Field("int", S, default=0),
        "status": Field("text", S, choices=BACKLOG_STATUS, default="needs refinement"),
        "ready_checks": Field("list", S),
        "points": Field("int", S),
        "confidence": Field("text", S, choices=ESTIMATE_CONFIDENCE),
        "owner_id": Field("int", S),
        "sprint_id": Field("int", S),
        "carried_from_id": Field("int", S),
        "feature_id": Field("int", S),
        "debt_id": Field("int", S),
        "system_ids": Field("ids", S),
        "labels": Field("list", S),
        "added_on": Field("date", S),
        "notes": Field("text", P),
        "team_id": Field("int", S),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = backlog_items.owner_id)", S),
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = backlog_items.sprint_id)", S),
        "carried_from_number": ("(SELECT number FROM sprints s WHERE s.id = backlog_items.carried_from_id)", S),
        "feature_title": ("(SELECT title FROM features f WHERE f.id = backlog_items.feature_id)", S),
        "debt_title": ("(SELECT title FROM tech_debt d WHERE d.id = backlog_items.debt_id)", S),
    },
)

estimate_votes = Record(
    entity="estimate_vote",
    table="estimate_votes",
    path="/api/estimate-votes",
    order_by="item_id, round, id",
    fields={
        "item_id": Field("int", S, required=True),
        "person_id": Field("int", S),
        "points": Field("int", S, required=True),
        "round": Field("int", S, default=1),
        "date": Field("date", S),
    },
    computed={"person_name": ("(SELECT name FROM people p WHERE p.id = estimate_votes.person_id)", S)},
)

sprint_plans = Record(
    entity="sprint_plan",
    table="sprint_plans",
    path="/api/sprint-plans",
    order_by="sprint_id",
    fields={
        "sprint_id": Field("int", S, required=True),
        "focus_factor": Field("number", S, default=0.8),
        "capacity_override": Field("int", S),
        "status": Field("text", S, choices=PLAN_STATUS_SPRINT, default="planning"),
        "committed_points": Field("int", S),
        "committed_on": Field("date", S),
        "completed_points": Field("int", S),
        "closed_on": Field("date", S),
        "notes": Field("text", P),
    },
)

sprint_availability = Record(
    entity="sprint_availability",
    table="sprint_availability",
    path="/api/sprint-availability",
    order_by="sprint_id, id",
    fields={
        "sprint_id": Field("int", S, required=True),
        "person_id": Field("int", S, required=True),
        "days": Field("int", S),
        "note": Field("text", P),
    },
)

# ---- teams and the Scrum of Scrums: structure is presentable; private notes stay private ----

teams = Record(
    entity="team",
    table="teams",
    path="/api/teams",
    order_by="kind = 'other', position, name",
    fields={
        "name": Field("text", S, required=True),
        "kind": Field("text", S, choices=TEAM_KINDS, default="other"),
        "purpose": Field("text", S),
        "product_owner_id": Field("int", S),
        "scrum_master_id": Field("int", S),
        "lead_id": Field("int", S),
        "member_ids": Field("ids", S),
        "jira_project": Field("text", S),
        "board_url": Field("text", S),
        "cadence": Field("text", S),
        "system_ids": Field("ids", S),
        "status": Field("text", S, choices=TEAM_STATUS),
        "status_note": Field("text", S),
        "status_date": Field("date", S),
        "current_sprint": Field("text", S),
        "sprint_ends": Field("date", S),
        "current_goal": Field("text", S),
        "notes": Field("text", P),
        "position": Field("int", S, default=0),
    },
    computed={
        "product_owner_name": ("(SELECT name FROM people p WHERE p.id = teams.product_owner_id)", S),
        "scrum_master_name": ("(SELECT name FROM people p WHERE p.id = teams.scrum_master_id)", S),
        "lead_name": ("(SELECT name FROM people p WHERE p.id = teams.lead_id)", S),
    },
)

sos_items = Record(
    entity="sos_item",
    table="sos_items",
    path="/api/sos-items",
    order_by="status = 'done', due IS NULL, due, id",
    fields={
        "question": Field("text", S, required=True),
        "kind": Field("text", S, choices=SOS_KINDS, default="issue"),
        "details": Field("text", S),
        "raised_by_team_id": Field("int", S),
        "team_ids": Field("ids", S),
        "stakeholder_ids": Field("ids", S),
        "owner_id": Field("int", S),
        "owner_team_id": Field("int", S),
        "outcome": Field("text", S),
        "raised_on": Field("date", S),
        "due": Field("date", S),
        "status": Field("text", S, choices=SOS_STATUS, default="open"),
        "resolution": Field("text", S),
        "jira_keys": Field("keys", S),
        "notes": Field("text", P),
    },
    computed={
        "owner_name": ("(SELECT name FROM people p WHERE p.id = sos_items.owner_id)", S),
        "owner_team_name": ("(SELECT name FROM teams t WHERE t.id = sos_items.owner_team_id)", S),
        "raised_by_team_name": ("(SELECT name FROM teams t WHERE t.id = sos_items.raised_by_team_id)", S),
    },
)

sos_meetings = Record(
    entity="sos_meeting",
    table="sos_meetings",
    path="/api/sos-meetings",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", S, required=True),
        "team_ids": Field("ids", S),
        "item_ids": Field("ids", S),
        "summary": Field("text", S),
        "notes": Field("text", P),
    },
)

# ---- conversations with people: private end to end ----

interactions = Record(
    entity="interaction",
    table="interactions",
    path="/api/interactions",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "kind": Field("text", P, choices=INTERACTION_KINDS, default="one-on-one"),
        "title": Field("text", P),
        "person_ids": Field("ids", P),
        "notes": Field("text", P),
        "takeaways": Field("text", P),
        "follow_ups": Field("text", P),
        "mood": Field("text", P, choices=MOODS),
    },
    hide_when_empty=True,
)

# ---- being someone's manager (and keeping your word to anyone): private end to end ----

commitments = Record(
    entity="commitment",
    table="commitments",
    path="/api/commitments",
    order_by="status != 'open', due IS NULL, due, id",
    fields={
        "person_id": Field("int", P, required=True),
        "direction": Field("text", P, choices=COMMITMENT_DIRECTIONS, default="mine"),
        "title": Field("text", P, required=True),
        "details": Field("text", P),
        "due": Field("date", P),
        "status": Field("text", P, choices=COMMITMENT_STATES, default="open"),
        "done_on": Field("date", P),
        "created_on": Field("date", P),
        "interaction_id": Field("int", P),
        "jira_keys": Field("keys", P),
    },
    computed={"person_name": ("(SELECT name FROM people p WHERE p.id = commitments.person_id)", P)},
    hide_when_empty=True,
)

manager_notes = Record(
    entity="manager_note",
    table="manager_notes",
    path="/api/manager-notes",
    order_by="date DESC, id DESC",
    fields={
        "person_id": Field("int", P, required=True),
        "date": Field("date", P, required=True),
        "kind": Field("text", P, choices=MANAGER_NOTE_KINDS, default="praise"),
        "note": Field("text", P, required=True),
        "shared": Field("bool", P, default=False),
    },
    hide_when_empty=True,
)

growth_goals = Record(
    entity="growth_goal",
    table="growth_goals",
    path="/api/growth-goals",
    order_by="status != 'active', target_date IS NULL, target_date, id",
    fields={
        "person_id": Field("int", P, required=True),
        "goal": Field("text", P, required=True),
        "measure": Field("text", P),
        "target_date": Field("date", P),
        "status": Field("text", P, choices=GROWTH_STATUS, default="active"),
        "progress": Field("text", P),
        "updated": Field("date", P),
    },
    hide_when_empty=True,
)

# ---- culture and trust: your standards, what you notice, the trust pulse (private); team agreements are shareable ----

standards = Record(
    entity="standard",
    table="standards",
    path="/api/standards",
    order_by="active DESC, position, id",
    fields={
        "text": Field("text", P, required=True),
        "why": Field("text", P),
        "active": Field("bool", P, default=True),
        "position": Field("int", P, default=0),
    },
    hide_when_empty=True,
)

standard_checks = Record(
    entity="standard_check",
    table="standard_checks",
    path="/api/standard-checks",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "standard_id": Field("int", P, required=True),
        "rating": Field("int", P, required=True),
        "note": Field("text", P),
    },
    hide_when_empty=True,
)

trust_pulses = Record(
    entity="trust_pulse",
    table="trust_pulses",
    path="/api/trust-pulses",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "source": Field("text", P, choices=PULSE_SOURCES, default="my read"),
        "team_id": Field("int", P),
        "scores": Field("json", P),
        "respondents": Field("int", P),
        "notes": Field("text", P),
    },
    hide_when_empty=True,
)

culture_observations = Record(
    entity="culture_observation",
    table="culture_observations",
    path="/api/culture-observations",
    order_by="status = 'addressed', date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "scope": Field("text", P, choices=CULTURE_SCOPES, default="my team"),
        "kind": Field("text", P, choices=CULTURE_KINDS, default="concern"),
        "category": Field("text", P, choices=CULTURE_CATEGORIES),
        "title": Field("text", P, required=True),
        "details": Field("text", P),
        "people_ids": Field("ids", P),
        "team_id": Field("int", P),
        "severity": Field("text", P, choices=SEVERITY),
        "action": Field("text", P, choices=CULTURE_ACTIONS, default="not yet"),
        "status": Field("text", P, choices=CULTURE_STATUS, default="open"),
        "follow_up": Field("date", P),
        "outcome": Field("text", P),
    },
    hide_when_empty=True,
)

# A read of the culture, one per unit (your team, a team you're integrating, the wider organization), in three
# layers: symbols and language, everyday norms, and the assumptions underneath. Private.
culture_reads = Record(
    entity="culture_read",
    table="culture_reads",
    path="/api/culture-reads",
    order_by="position, id",
    fields={
        "unit": Field("text", P, required=True),
        "position": Field("int", P, default=0),
        "symbols": Field("text", P),
        "influence": Field("text", P),
        "meetings": Field("text", P),
        "execution": Field("text", P),
        "conflict": Field("text", P),
        "recognition": Field("text", P),
        "ends_means": Field("text", P),
        "power": Field("text", P),
        "adapt_or_change": Field("text", P),
    },
    hide_when_empty=True,
)

# A self-assessment of which kinds of problems you're drawn to, so you can spot likely blind spots. Private.
preference_assessments = Record(
    entity="preference_assessment",
    table="preference_assessments",
    path="/api/preference-assessments",
    order_by="date DESC, id DESC",
    fields={
        "date": Field("date", P, required=True),
        "scores": Field("json", P),
        "notes": Field("text", P),
        "hammer": Field("text", P),
        "plan": Field("json", P),
    },
    hide_when_empty=True,
)

# The local language: acronyms, product and project names, and words that mean something particular here.
glossary_terms = Record(
    entity="glossary_term",
    table="glossary_terms",
    path="/api/glossary-terms",
    order_by="term COLLATE NOCASE",
    fields={
        "term": Field("text", S, required=True),
        "meaning": Field("text", S),
        "used_by": Field("text", S),
    },
)

# The patterns of behavior that stand in the way of the goals, and what you want instead by the end of your time in
# the role. Private.
behavior_targets = Record(
    entity="behavior_target",
    table="behavior_targets",
    path="/api/behavior-targets",
    order_by="status = 'changed', position, id",
    fields={
        "pattern": Field("text", P, required=True, choices=BEHAVIOR_PATTERNS),
        "symptoms": Field("text", P),
        "target": Field("text", P),
        "status": Field("text", P, choices=BEHAVIOR_STATUS, default="noticed"),
        "notes": Field("text", P),
        "position": Field("int", P, default=0),
    },
    hide_when_empty=True,
)

team_agreements = Record(
    entity="team_agreement",
    table="team_agreements",
    path="/api/team-agreements",
    order_by="status = 'retired', area, position, id",
    fields={
        "text": Field("text", S, required=True),
        "area": Field("text", S, choices=AGREEMENT_AREAS, default="working together"),
        "team_id": Field("int", S),
        "status": Field("text", S, choices=AGREEMENT_STATUS, default="proposed"),
        "agreed_on": Field("date", S),
        "review_on": Field("date", S),
        "position": Field("int", S, default=0),
    },
)

# A daily note of what happened. Its audience caps who can ever see it: leadership reports, your manager's, or only you.
work_log = Record(
    entity="log_entry",
    table="work_log",
    path="/api/log-entries",
    order_by="date DESC, id DESC",
    ceiling_sql="CASE audience WHEN 'just me' THEN 0 WHEN 'my manager' THEN 1 ELSE 2 END",
    fields={
        "date": Field("date", E, required=True),
        "kind": Field("text", E, choices=LOG_KINDS, default="progress"),
        "text": Field("text", E, required=True),
        "details": Field("text", E),
        "audience": Field("text", E, choices=LOG_AUDIENCES, default="leadership"),
        "jira_keys": Field("keys", E),
        "team_id": Field("int", S),
        "source_entity": Field("text", P),
        "source_id": Field("int", P),
    },
)

# Reports as sent: the edited text is kept, with who it went to and when.
reports = Record(
    entity="report",
    table="reports",
    path="/api/reports",
    order_by="period_start DESC, id DESC",
    ceiling_sql="CASE audience WHEN 'my manager' THEN 1 ELSE 2 END",
    fields={
        "kind": Field("text", E, choices=REPORT_KINDS, default="weekly"),
        "audience": Field("text", E, choices=REPORT_AUDIENCES, default="leadership"),
        "period_start": Field("date", E, required=True),
        "period_end": Field("date", E, required=True),
        "sprint_id": Field("int", E),
        "title": Field("text", E, required=True),
        "markdown": Field("text", E, required=True),
        "status": Field("text", E, choices=REPORT_STATUS, default="draft"),
        "sent_on": Field("date", E),
        "sent_to": Field("text", P),
        "created_on": Field("date", E),
    },
    computed={"sprint_number": ("(SELECT number FROM sprints s WHERE s.id = reports.sprint_id)", E)},
)

# Work that arrives in the middle of a sprint: how it was assessed, who decided, what was swapped out and who was told.
change_requests = Record(
    entity="change_request",
    table="change_requests",
    path="/api/change-requests",
    order_by="status IN ('decided', 'closed'), requested_on DESC, id DESC",
    fields={
        "title": Field("text", E, required=True),
        "description": Field("text", S),
        "source": Field("text", E, choices=CR_SOURCES, default="stakeholder"),
        "requested_by_id": Field("int", S),
        "requested_on": Field("date", E, required=True),
        "needed_by": Field("date", E),
        "sprint_id": Field("int", E),
        "team_id": Field("int", S),
        "urgency": Field("text", E, choices=CR_URGENCY, default="this sprint"),
        "value": Field("text", E),
        "goal_impact": Field("text", E, choices=CR_GOAL_IMPACT),
        "points": Field("int", E),
        "status": Field("text", E, choices=CR_STATUS, default="received"),
        "decision": Field("text", E, choices=CR_DECISIONS),
        "decided_by_id": Field("int", S),
        "decided_on": Field("date", E),
        "decision_reason": Field("text", E),
        "swapped_out_ids": Field("ids", S),
        "points_out": Field("int", E),
        "backlog_item_id": Field("int", S),
        "communicated_on": Field("date", E),
        "jira_keys": Field("keys", E),
        "notes": Field("text", P),
    },
    computed={
        "requested_by_name": ("(SELECT name FROM people p WHERE p.id = change_requests.requested_by_id)", S),
        "decided_by_name": ("(SELECT name FROM people p WHERE p.id = change_requests.decided_by_id)", S),
        "sprint_number": ("(SELECT number FROM sprints s WHERE s.id = change_requests.sprint_id)", E),
    },
)

# A change you're bringing to the team, made visible: announced, tried, reviewed together, then kept or dropped.
team_changes = Record(
    entity="team_change",
    table="team_changes",
    path="/api/team-changes",
    order_by="status IN ('adopted', 'dropped'), position, id",
    fields={
        "title": Field("text", S, required=True),
        "area": Field("text", S, choices=CHANGE_AREAS, default="process"),
        "why": Field("text", S),
        "what_changes": Field("text", S),
        "how_we_try": Field("text", S),
        "wave": Field("int", S),
        "status": Field("text", S, choices=CHANGE_STATUS, default="idea"),
        "announced_on": Field("date", S),
        "trial_start": Field("date", S),
        "review_on": Field("date", S),
        "decided_on": Field("date", S),
        "outcome": Field("text", S),
        "team_feedback": Field("text", S),
        "agreement_id": Field("int", S),
        "team_id": Field("int", S),
        "notes": Field("text", P),
        "position": Field("int", S, default=0),
    },
)

# Each inherited team member's first 90 days with you, counted from your start date.
first90_milestones = Record(
    entity="first90_milestone",
    table="first90_milestones",
    path="/api/first90-milestones",
    order_by="person_id, due_day, position, id",
    hide_when_empty=True,
    fields={
        "person_id": Field("int", P, required=True),
        "title": Field("text", P, required=True),
        "due_day": Field("int", P, required=True),
        "auto": Field("text", P, choices=("one_on_one", "interview", "growth_goal", "feedback", "mandate")),
        "done_on": Field("date", P),
        "not_done": Field("bool", P, default=False),  # you've marked it not done, even if the data says it happened
        "note": Field("text", P),
        "position": Field("int", P, default=0),
    },
)

# What a role is for, what it must deliver, and what it can decide. Yours is agreed with your manager and can be
# shown to them; your reports' are private to you.
mandates = Record(
    entity="mandate",
    table="mandates",
    path="/api/mandates",
    order_by="mine DESC, id",
    ceiling_sql="CASE WHEN mine THEN 1 ELSE 0 END",
    hide_when_empty=True,
    fields={
        "person_id": Field("int", S, required=True),
        "mine": Field("bool", S, default=False),
        "purpose": Field("text", S),
        "boundaries": Field("text", S),
        "resources": Field("text", S),
        "questions": Field("text", S),
        "status": Field("text", S, choices=MANDATE_STATUS, default="draft"),
        "agreed_with_id": Field("int", S),
        "agreed_on": Field("date", S),
        "review_on": Field("date", S),
        "notes": Field("text", P),
    },
    computed={
        "person_name": ("(SELECT name FROM people p WHERE p.id = mandates.person_id)", S),
        "agreed_with_name": ("(SELECT name FROM people p WHERE p.id = mandates.agreed_with_id)", S),
    },
)

mandate_items = Record(
    entity="mandate_item",
    table="mandate_items",
    path="/api/mandate-items",
    order_by="mandate_id, kind, position, id",
    ceiling_sql="(SELECT CASE WHEN m.mine THEN 1 ELSE 0 END FROM mandates m WHERE m.id = mandate_items.mandate_id)",
    fields={
        "mandate_id": Field("int", S, required=True),
        "kind": Field("text", S, choices=MANDATE_ITEM_KINDS, default="outcome"),
        "text": Field("text", S, required=True),
        "measure": Field("text", S),
        "due_day": Field("int", S),
        "authority": Field("text", S, choices=AUTHORITY),
        "status": Field("text", S, choices=MANDATE_ITEM_STATUS, default="open"),
        "position": Field("int", S, default=0),
    },
)

# What you need to learn about the organization, from whom, and by when: the learning agenda.
learning_questions = Record(
    entity="learning_question",
    table="learning_questions",
    path="/api/learning-questions",
    order_by="status = 'open' DESC, due_day IS NULL, due_day, position, id",
    hide_when_empty=True,
    fields={
        "question": Field("text", P, required=True),
        "area": Field("text", P, choices=LEARNING_AREAS, default="present"),
        "ask_ids": Field("ids", P),
        "due_day": Field("int", P),
        "answer": Field("text", P),
        "hypothesis": Field("text", P),
        "disprove_if": Field("text", P),
        "verdict": Field("text", P, choices=HYPOTHESIS_VERDICTS),
        "status": Field("text", P, choices=LEARNING_STATUS, default="open"),
        "position": Field("int", P, default=0),
    },
)

# What kind of situation each area is in, and what that means for how you act there.
situations = Record(
    entity="situation",
    table="situations",
    path="/api/situations",
    order_by="position, id",
    fields={
        "area": Field("text", S, required=True),
        "kind": Field("text", S, choices=SITUATION_KINDS),
        "element": Field("text", S, choices=SITUATION_ELEMENTS),
        "effort": Field("int", S),
        "evidence": Field("text", P),
        "history": Field("text", P),
        "mood": Field("text", P),
        "opportunities": Field("text", P),
        "approach": Field("text", S),
        "position": Field("int", S, default=0),
    },
)

# The conversations with your manager that set you up to succeed, held and revisited.
boss_conversations = Record(
    entity="boss_conversation",
    table="boss_conversations",
    path="/api/boss-conversations",
    order_by="position, id",
    hide_when_empty=True,
    fields={
        "topic": Field("text", P, required=True),
        "prompt": Field("text", P),
        "held_on": Field("date", P),
        "status": Field("text", P, choices=CONVERSATION_STATUS, default="not started"),
        "agreed": Field("text", P),
        "open_points": Field("text", P),
        "next_30": Field("text", P),
        "next_on": Field("date", P),
        "notes": Field("text", P),
        "position": Field("int", P, default=0),
    },
)

# Managers you mentor: sessions, and the practices they've picked up from you.
mentoring_sessions = Record(
    entity="mentoring_session",
    table="mentoring_sessions",
    path="/api/mentoring-sessions",
    order_by="date DESC, id DESC",
    hide_when_empty=True,
    fields={
        "person_id": Field("int", P, required=True),
        "date": Field("date", P, required=True),
        "topic": Field("text", P),
        "notes": Field("text", P),
        "next_step": Field("text", P),
        "next_on": Field("date", P),
    },
)

mentored_practices = Record(
    entity="mentored_practice",
    table="mentored_practices",
    path="/api/mentored-practices",
    order_by="status = 'dropped', person_id, id",
    fields={
        "person_id": Field("int", S, required=True),
        "practice": Field("text", S, required=True),
        "status": Field("text", S, choices=PRACTICE_STATUS, default="shared"),
        "since": Field("date", S),
        "notes": Field("text", P),
    },
    computed={"person_name": ("(SELECT name FROM people p WHERE p.id = mentored_practices.person_id)", S)},
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
    backlog_items, estimate_votes, sprint_plans, sprint_availability,
    teams, sos_items, sos_meetings,
    interactions, commitments, manager_notes, growth_goals,
    standards, standard_checks, trust_pulses, culture_observations, culture_reads, glossary_terms, preference_assessments, behavior_targets, team_agreements, work_log, reports, change_requests, team_changes, first90_milestones, mandates, mandate_items, learning_questions, situations, boss_conversations, mentoring_sessions, mentored_practices,
]
