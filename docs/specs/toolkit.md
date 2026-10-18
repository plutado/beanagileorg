# Toolkit App Spec

Design spec, October 2026. Written before the build; the code has since grown well past it (see the README for what exists today). Example values are [Placeholder]s.

The toolkit is a supporting app beside an optional hub app (Odysseus) on a work laptop: a local-only web app for running an engineering team, from one-on-ones and sprints to status, learning and escalations.

## Shape of the app

The proposal is a small web app on the same stack as Odysseus, so the same LLMs and habits work on both: Python with FastAPI, SQLite, and a plain JavaScript front end, run in Docker.

| Decision | Proposal |
| --- | --- |
| Address | toolkit.beanagile.org on the device (hub at beanagile.org), bound to localhost; publicly the domain shows only a cat video page |
| Users | One: me. No viewer accounts. Others see it over screen share or in exports |
| Sign-in | A local password and TOTP, because the device holds confidential data even offline |
| Storage | One SQLite file, apart from Odysseus's database |
| Odysseus link | Odysseus's REST API with a scoped token, plus an MCP server the toolkit exposes for Odysseus and other LLM clients |
| Look | Matches Odysseus's theme so the suite reads as one system on a shared screen |

**Version 1** (by day 1): listening tour, team profiles, day-30 rollup, my development, settings, presentation mode.

**Later versions:** dev-sync log and group learning (day 30), sprint notebook, roadmap, RACI and status (day 45), escalation playbook (day 30), meeting decks and dashboard (day 90). The dates follow the app plan's phases.

## Data model at a glance

*(Diagram in the original doc: toolkit data model · 6 areas around Person.)*

Person is the hub: profiles, owners, presenters, contacts and requesters all point to it. Sprint gives delivery records their place in time. A few records, such as Settings and Theme, stand alone.

## Data model

Twenty-odd entities in seven areas, all hanging off two spines: **Person** (anyone I work with) and **Sprint** (time). Every record also carries an id, created and updated times, a source (me or an agent), and entries in a shared change log.

### People and listening

| Entity | Key fields | Links |
| --- | --- | --- |
| Person | name, role, relationship (employee, contractor, peer, stakeholder, manager, vendor), start date, location and time zone, background, skills, certifications, goals, wants to learn, can teach, working style, support notes, contact details, active | Everything that names a person |
| Interview | date, status (planned, done), what's working, what's frustrating, change first, don't change, systems, gaps, opportunities | One Person; many Themes |
| Theme | name, description | Interviews, ceremony notes |

### Sprints and delivery

| Entity | Key fields | Links |
| --- | --- | --- |
| ProgramIncrement (optional) | number, start, end, objectives, objectives met; only used if the organization runs SAFe | Its Sprints |
| Sprint | number, start, end, goal, kind (development, or innovation and planning) | Ceremony notes, action items |
| CeremonyNote | type (planning, refinement, review, retro, dev sync, ad hoc, plus PI planning and the end-of-PI demo under SAFe), date, what happened, what I noticed, implementation thoughts, follow-ups, tags | One Sprint; Themes; can spawn action items or tasks |
| ActionItem | concern, date raised, next action, due, status (open, in progress, waiting, done), group-learning flag, origin (dev sync, retro, incident, one-on-one) | Raised by and owned by a Person; optional Sprint |
| LearningSession | topic, date, status (proposed, scheduled, done) | Presenter (Person); the ActionItem it came from |

### Plan and reporting

| Entity | Key fields | Links |
| --- | --- | --- |
| RoadmapItem | title, description, kind (ceremony, agreement, metric, milestone), target day, status (not started, in progress, done, at risk) | Owner (Person) |
| RaciDecision | decision, status (to confirm, confirmed, changed) | RaciAssignments |
| RaciAssignment | role, letter (R, A, C, I) | One RaciDecision; optional Person |
| Risk | title, impact, next step, due, status | Owner (Person); optional ActionItem |
| DecisionNeeded | decision, needed by, status | From whom (Person) |
| Metric and MetricReading | name, baseline, target; date, value | Readings belong to a Metric |
| StatusReport | week of, overall red/yellow/green, summary, frozen snapshot of the sections, state (draft, exported) | Pulls from roadmap, risks, decisions, learning goals |

### My development

| Entity | Key fields | Links |
| --- | --- | --- |
| LearningGoal | track, goal, evidence, target day, status, show-in-report flag | Log entries |
| LearningLogEntry | date, minutes, what I covered | One LearningGoal |
| Task | title, due, status | Requested by (Person) |
| Obligation | title, cadence, next due, last done | None |

### Escalation

| Entity | Key fields | Links |
| --- | --- | --- |
| System | name, description, vendor support and how to open a case | Owner, first responder, backup (People); business contacts |
| Severity | level, definition, response time, who is paged, who is told | Escalation steps |
| EscalationStep | order, method, out-of-hours flag | One System or Severity; one Person |
| Incident | date, severity, summary, resolved at | One System; People involved; follow-up ActionItems |

### Docs and decisions

| Entity | Key fields | Links |
| --- | --- | --- |
| DocLink | title, category (SDLC, agreements, releases, runbooks, architecture, onboarding, glossary), last reviewed | Odysseus document id; owner (Person) |
| Decision | date, decision, tradeoff | Decided by (Person); optional DocLink |

### Presenting and settings

| Entity | Key fields | Links |
| --- | --- | --- |
| MeetingDeck and DeckSlide | deck name; slide order, view, filter | Slides point at any screen |
| Settings | contract start date, renewal day, presentation defaults, Odysseus address, token reference | None |

## Privacy levels

Every field is tagged in the schema with one of three levels. Presentation mode and exports filter on the tag, so nothing private relies on me remembering to hide it.

| Level | Who sees it | Examples |
| --- | --- | --- |
| Private | Me only, never on a shared screen or in an export | One-on-one answers, support notes, working style, ceremony notes, contact details, dynamics notes, private tasks |
| Presentable | Me, and on screen in presentation mode | Themes and counts, skills matrix without names, action items, roadmap, RACI, escalation chain without phone numbers |
| Exportable | Anywhere, including PDF and HTML exports | Status report sections, roadmap status, metrics, decisions, learning goals marked for reporting, rollup themes and counts, sprint dates and goals |

Rules:

- A new field defaults to private until it is tagged otherwise.
- A record can be made more private than its fields' defaults, never less.
- Exports run through one filter and show a preview before they're saved. Each export is logged with what it contained.
- Agent access follows the same tags: a token scoped to exportable data can't read private fields.

## Screens

Sixteen screens in five groups down a left-hand menu. The home screen answers "what needs me today", and every screen has a presentation-mode version.

| Screen | Purpose | Key actions | In presentation mode |
| --- | --- | --- | --- |
| Today | What needs me now: overdue actions, today's ceremonies, obligations due, open follow-ups | Jump to any item; quick capture | Hidden (personal) |
| **Team** |  |  |  |
| People | Profiles for everyone I work with | Add, edit, see their one-on-ones and actions | Names and roles only |
| Skills and learning | Skills matrix; who can teach and who wants to learn | Propose a learning session from a match | Matrix without names |
| Listening tour | One-on-one records with the same four questions | Plan, record, tag themes | Hidden |
| Day-30 rollup | Themes ranked, gaps, opportunities, "don't change" | Copy into the diagnosis | Themes and counts only |
| **Delivery** |  |  |  |
| Sprints | Current, past and future sprints with my ceremony notes | Open a ceremony note; turn a follow-up into an action | Sprint dates and goals only |
| Dev-sync log | Every question raised after standup, with owner and due date | Add, update, filter by owner or overdue | Shown, without private notes |
| Group learning | Schedule of short team presentations | Schedule, assign presenter | Shown |
| Roadmap | Agile adoption items with target days and status | Update status | Shown |
| RACI | Decisions by role | Edit cells, confirm rows | Shown |
| **Reporting** |  |  |  |
| Weekly status | Draft built from roadmap, risks, decisions and learning goals | Edit, preview export, export to PDF or HTML | Shown (exportable fields) |
| Meeting decks | Saved sequences of live views | Build a deck, present it like slides | This is presentation mode |
| **Knowledge** |  |  |  |
| Docs library | SDLC, agreements, runbooks and more, held in Odysseus | Open in Odysseus, mark reviewed | Titles and shareable docs |
| Escalation playbook | Systems, severities, chains, incident log | Look up who to call; log an incident | Chains without phone numbers |
| **Me** |  |  |  |
| My development | Learning goals, log, tasks, obligations | Log time, tick off, choose what reports to my manager | Only goals marked for reporting |
| Settings | Start date, presentation defaults, Odysseus connection, backups | Set the start date once; test the connection | Hidden |

## Talking to Odysseus

Traffic runs both ways over localhost. The toolkit calls Odysseus's API with a scoped token, and Odysseus reaches the toolkit through an MCP server the toolkit exposes. Neither touches the other's database. The toolkit must also run without Odysseus, with documents, local-model drafting and scheduled jobs simply switched off, so other managers can use a lighter install.

**Toolkit to Odysseus**

| Need | Odysseus feature | Status in today's Odysseus |
| --- | --- | --- |
| Docs library, plan documents | Documents, with version history | Exists; reachable through the token-gated `/api/codex` endpoints |
| Ceremonies and obligations on the calendar | Calendar events | Exists; same endpoints |
| Quick to-dos mirrored as notes | Notes and checklists | Exists; same endpoints |
| Drafting with a local model (status draft, rollup summary) | Chat with local models via Ollama | Unconfirmed for outside apps; the fallback is calling Ollama directly |
| Weekly drafting jobs | Scheduled AI tasks | Exists inside Odysseus; whether outside apps can create them is unconfirmed |

**Odysseus to toolkit**

- Odysseus already connects to MCP servers as a client. Registering the toolkit's MCP server there lets Odysseus's agent answer "what's overdue?" or "draft this week's status" from toolkit data.
- The toolkit's MCP server enforces privacy levels per token, so Odysseus's agent sees only what its token allows.
- Any model routing rule applies here too: toolkit data goes to local models unless the company approves a cloud provider.

**An example flow, drafting the weekly status:** the toolkit gathers roadmap changes, open risks, pending decisions and reportable learning goals. It sends exportable fields only to a local model for a first draft, and saves the draft. I edit it, preview the export, and export to PDF.

## Toolkit API and MCP tools

One REST API serves the screens, LLM clients and the MCP server alike, so every route passes the same sign-in and privacy checks.

**REST.** One resource per entity under `/api/` (for example `/api/people`, `/api/interviews`, `/api/sprints/{id}/notes`, `/api/actions`), with list, read, create, update and archive. Plus three special routes:

- `/api/rollup`: the day-30 rollup, computed
- `/api/status/draft`: builds a status draft from current records
- `/api/export`: the single filtered export path, with preview

**Token scopes.**

| Scope | Can read | Can write |
| --- | --- | --- |
| export:read | Exportable fields | Nothing |
| present:read | Presentable and exportable fields | Nothing |
| delivery:write | Presentable fields | Action items, roadmap, RACI, sprints (not ceremony notes) |
| full | Everything | Everything; for my own sessions and code work only |

**MCP tools,** a first set for Odysseus's agent and Claude Code:

- `list_overdue_actions`, `add_action_item`, `update_action_item`
- `get_rollup`, `list_themes`
- `draft_weekly_status`, `get_roadmap`, `update_roadmap_status`
- `current_sprint`, `add_ceremony_note` (full scope only)
- `log_learning`, `list_obligations_due`
- `escalation_for(system, severity)`

**Code and config work.** LLMs that change the toolkit's code (Claude Code on the device) work in the repository, never through the API. Data changes go through the API so they're logged; schema changes go through migrations.

**The Comms studio.** A second supporting app at comms.beanagile.org handles messages, presentations and media. It holds an `export:read` token only, so it reads roadmap status, risks, decisions, metrics and reportable learning goals, and nothing private. The toolkit still assembles the weekly status from its records (`/api/status/draft`). The studio turns that into the message, checks it against current facts, and keeps the sent log. The Comms studio gets its own spec later.

## Storage, backups and imports

One SQLite file on the device's encrypted disk, backed up automatically and never synced to a cloud folder.

- **Backups:** a nightly snapshot using SQLite's online backup (the same approach as `odysseus-backup`), kept for `[Placeholder]` days on the encrypted disk or an encrypted external drive. A restore is tested once a month.
- **Migrations:** schema changes ship as numbered migrations, so code changes by an LLM can't silently alter data.
- **Import from the prototype:** the tracker prototype's JSON export (one-on-ones, actions, learning sessions) maps straight onto Interview, ActionItem and LearningSession. It holds placeholder data only, so it's useful for testing, not as real records.
- **Import from planning docs:** the plan, communication plan, learning plan and this spec come in as Odysseus documents. Roadmap items, RACI rows and learning goals are re-entered as structured records.
- **Contract end:** one command exports everything, or wipes it, per the data agreement with the company.

## Ad-hoc sharing (optional)

By default the hub and apps answer only on localhost. With IT's agreement, one Share control in the hub can open them to people nearby for a set time.

| Mode | Reaches | Turned on by | Caution |
| --- | --- | --- | --- |
| Local only (default) | Me | Always on | None |
| Same network | People in the room or building | Proxy listens on the LAN address; room.beanagile.org is pointed at it through the DNS provider's API | Office Wi-Fi may block device-to-device traffic, and IT may not allow it |
| Tailscale | Invited people, anywhere | `tailscale serve` on, devices shared | Guests need Tailscale |
| Public tunnel with login | Anyone allowed | Tunnel started | Puts data on the internet; only with written approval |

Guardrails for every mode except local only: guests get a read-only view filtered to presentable fields on the server, need an access code shown on my screen, and lose access after `[Placeholder]` minutes. A banner shows while sharing is on, and every visit is logged. A wildcard certificate for beanagile.org comes from Let's Encrypt through a DNS challenge, so HTTPS works without anything public and app names stay out of certificate logs. Same-network sharing uses room.beanagile.org.

## Open questions

- [ ] Can outside apps call Odysseus's local models and create scheduled tasks through its API, or does the toolkit call Ollama directly?
- [ ] Does the toolkit get its own sign-in, or reuse Odysseus's accounts through a token exchange?
- [ ] Same stack as Odysseus (FastAPI, SQLite, plain JavaScript), or something else for the front end?
- [ ] Which sharing modes, if any, IT will allow on their network
- [ ] Which DNS provider hosts beanagile.org (it needs an API for the sharing toggle and certificates), and where the public cat video page is hosted
- [ ] How long to keep backups, and where the encrypted copy lives
