# Backlog

Everything planned for the apps, so nothing falls through the cracks. When one option is chosen over another, the one not chosen stays here until it's built. Items move to **Done** with the date.

Specs: toolkit and Comms studio planning docs (linked from the planning workspace README).

## In progress

Nothing right now.

## Next up

In the order the 90-day plan needs them:

- [ ] **On the company device (David):** turn on nightly backups (`beanagile schedule --write`, then `launchctl load`), choose an encrypted backup location, and set up the local domain (DNS records or hosts lines, Caddy, `caddy trust`) per docs/local-domain.md; publish site/ with the cat video for the public beanagile.org

## Toolkit, later versions

- [ ] Architecture: placeholder seed data; diagrams inside guides (Mermaid, vendored); export the system map as SVG or PNG for decks; data entities and which system is the source of truth for each; environment and deployment pipeline view per system; link incidents and test failures to integrations
- [ ] QA: placeholder seed data; pull automated suite results from Bitbucket Pipelines or another CI instead of typing them; a test-run section in the weekly status draft; per-story QA sign-off tied to PI planning stories; flaky-test tracking over time
- [ ] Business landscape: placeholder seed data; link assessments to listening-tour themes, incidents and metrics as evidence; a shareable summary of selected points for leadership; an org chart drawing; capabilities each system supports (a capability map)
- [ ] Plans: a version history of each plan as presented, so a later review can show what changed and why; a day-30/60/90 check-in that marks each item met, moved or dropped with a note
- [ ] Metrics: a small trend chart per metric, and automatic readings from Bitbucket or the release log
- [ ] Weekly status: let me edit the overall line and keep a history of sent drafts in the toolkit
- [ ] Roadmap: drag to reorder, and a timeline view

- [ ] Vendors: attach documents (contracts, statements of work) from the docs library, and a vendor scorecard reviewed at renewal
- [ ] Themes as their own records (version 1 stores them as tags on each one-on-one)
- [ ] Escalation playbook: reorder steps by dragging, and link incidents to sprints
- [ ] Documentation library: links to Odysseus documents with owner and last-reviewed date
- [ ] Decision log
- [ ] Meeting decks: saved sequences of live views, presented like slides
- [ ] Delivery dashboard
- [ ] Scrum of Scrums board from imported team status packs

## Design follow-ups

- [ ] Guided tours with Driver.js (MIT; pin a version at least two weeks old, bundled locally): a first-run tour per app (sidebar, command palette, presentation mode, main screens), per-screen tours from a "Take the tour" item in the command palette, tours defined as data next to each screen, styled to the design system. Shepherd.js and Intro.js ruled out: both AGPL-3.0.

- [ ] Per-screen polish: richer empty states with illustrations, inline editing patterns, and a consistent page header with actions on every screen
- [ ] Accessibility pass: contrast check of every token pair, screen reader labels, focus order in dialogs

## Comms studio, later versions

- [ ] Generators layer (Comms studio): one connector per outside creative service, all delivering into the media library with provenance recorded (service, model, prompt, date, plan terms) and a "generated" label; prompts never carry confidential detail
- [ ] Higgsfield connector: generate b-roll, motion backgrounds, animated title cards and short explainer clips from a prompt or still, straight into the media library
- [ ] Canva integration (Canva Connect API, signed in with David's Canva Pro account): browse designs from the media library, pull exports (PDF, PNG, MP4) straight in, send deck slides or images to Canva for polish, "open in Canva" links. Only exportable or presentable content ever goes to Canva. Confirm which API features the Pro plan includes before building. Until then, export from Canva and upload.

- [ ] Deck builder: undo and redo, keyboard shortcuts in the slide list, and real slide thumbnails
- [ ] Deck builder: image positioning and sizing controls, and a second image layout (full-bleed)
- [ ] Deck builder: per-element reveal order in the inspector (version 1 reveals points in order)
- [ ] Present page: rehearsal timer and rehearsal log

- [ ] Writing checks, remaining: one version of the truth, no surprises, stale facts, sensitive content, questions answered
- [ ] Plain-language rewrite suggestions from a local model (version 1 suggests from the jargon list and glossary)
- [ ] Message editor: per-audience length targets, and side-by-side version compare
- [ ] Fact snapshots from the toolkit over an `export:read` token (the status draft pull is done; snapshots per message are next)
- [ ] Deck builder, full: theme layouts, narrative templates and outline-first skeletons, headline check, fact-bound numbers and charts, custom HTML slide in a sandbox, speaker view and rehearsal log
- [ ] Media players: control playback from the speaker view (players work on the slide in the prototype)
- [ ] Lottie: preview segments by frame in the inspector
- [ ] Themes from Envato Elements: template folder outside the repo, layouts mapped to slide types
- [ ] Export: single-file HTML deck, PDF, PowerPoint on the template
- [ ] Media production board: script, storyboard, shot list, recording, edit, captions, review, publish
- [ ] Questions log and communication measures

## Shared base and platform

- [ ] Backups: optional encryption of backup archives with a passphrase (age or similar); copy each night's backup to a second location; a warning on Today when the last good backup is more than two days old
- [ ] Timed sharing (Share control): same-network and Tailscale modes, read-only presentable view, access code, auto-timeout, banner, visit log
- [ ] Optional Odysseus integration: documents, calendar, local models, scheduled jobs
- [ ] MCP server exposing toolkit tools, scoped like the API
- [ ] Nightly backups with a tested restore
- [ ] Local domain setup: beanagile.org override, reverse proxy, wildcard certificate via DNS challenge
- [ ] Packaging for other managers: lighter install, setup script, practice packs export and import
- [ ] Docker setup for the company device

## Housekeeping

- [ ] Fill in the LICENSE copyright holder (currently a placeholder)

## Done

- [x] 2026-10-16: Platform before real data. `beanagile backup` takes a consistent snapshot of each app's database and media while it runs, writes a manifest of row counts, then restores it to a scratch folder and checks integrity, every table's row count and every file before calling it good; keeps the newest 30; `backups`, `verify` and `restore` commands (restore checks first, refuses a running app, and sets current data aside rather than deleting it); `schedule` writes a launchd job for nightly backups; a Backups panel in each app's Settings with Back up now and each backup's check result. Local domain: the apps refuse requests addressed to unknown hostnames (blocks DNS rebinding) and accept 127.0.0.1, localhost and <app>.beanagile.org plus BEANAGILE_ALLOWED_HOSTS; `beanagile domain` prints the hosts lines and a Caddy config with local HTTPS; docs/backups.md and docs/local-domain.md; site/ holds the public cat-video page; 122 tests

- [x] 2026-10-16: Architecture and tools. One catalog for systems and tools (shared with the escalation playbook, QA and the business landscape) with kind, category, what it is, how we use it, environments, what it's built with, docs link, owner, admin, vendor, lifecycle, criticality and private known issues; integrations between systems with the middleware they pass through, pattern, direction, data, frequency, protocol, owner, criticality, status and private notes; a system map drawn from the integrations in lanes (external services, applications and platforms, integration layer, data stores, connected tools) where hovering a system traces its connections; a page per system showing what it sends and receives, what it carries, the offerings it supports, its tests and suites, decisions and guides; numbered architecture decision records (context, decision, consequences, alternatives, superseded by); Markdown guides linked to systems; documentation gaps and unowned integrations called out. Also: Markdown now renders numbered and bulleted lists properly and supports links and inline code; static files are revalidated on every load so an update never leaves old screens in the browser; 114 tests

- [x] 2026-10-16: QA resources. A manual test library (title, system, area, smoke or regression, priority, before-you-start, steps, expected result, owner, in use) grouped by system with filters and each case's last result; test runs started from every smoke or regression test, one system, or a regression plan, with pass, fail, blocked or skipped per case, notes, a tally and a copyable summary; a failed or blocked case goes to the dev-sync log tagged to the run's sprint and the case owner; an automated test inventory (unit, integration, end-to-end, Apex, MUnit, performance) with where each lives, CI link, test count, coverage and latest result; regression plans for Salesforce releases and peak-season freezes with owner, backup, scope, picked cases, status and sign-off; the definition of done with a starter list, and the QA and release rows from the RACI; an overview of what's failing, never run and coming up. Fixed: the dev-sync edit form now offers the vendor and testing origins, so saving those items no longer resets where they came from; 106 tests

- [x] 2026-10-16: Business landscape. Products, services and internal platforms with what each is, who it serves, owning department, systems and vendors it relies on, maturity and status; the organization as a tree of divisions, departments and teams with leaders, people placed in them and the offerings they own (department loops are refused; deleting one moves its teams up); a strengths, weaknesses, opportunities and threats assessment for each offering and department with evidence, source, confidence, date and status, plus a combined matrix filtered by kind; an opportunity or weakness can become a roadmap item (title only, since the roadmap is shareable) or a risk; structure is presentable, the assessment is private and hidden while presenting; 98 tests

- [x] 2026-10-16: 30/60/90-day and six-month plans. Six plans, one per month (first 30 days, days 31 to 60, days 61 to 90, months 4, 5 and 6), created by the database upgrade; plans can be added (a finer check-in or a longer view such as month 9), renamed, re-dated or deleted; each with a headline, dates from the contract start date and a draft, reviewed or presented status with date and audience; items as outcomes, actions, measures or "what I won't change", with day, owner, status, listening-tour themes and private evidence; a flag for items outside their window; a "What I heard" panel showing which themes no item answers yet, plus the private one-on-one notes; an exportable outline copied as Markdown (logged); the Comms studio builds a deck from the outline over the export-only token (title, what I heard, one slide per stretch with details in the speaker notes, measures, what stays, closing). Fixed: each app now has its own session cookie, so signing in to one no longer signs you out of the other; 92 tests

- [x] 2026-10-16: Retrospectives and PI planning. Retros: a shared record per sprint with format (went well / didn't / ideas, start / stop / continue, mad / sad / glad, 4 Ls), attendees and summary; points by column with votes and topic tags; commitments with owner, due date and status, tagged to the sprint where they came up; each retro opens with earlier open commitments to review; a running improvement backlog; recurring topics across retros, flagged when they match a listening-tour theme. PI planning: objectives (committed and stretch, planned and actual business value, predictability); epics, features and stories with priority, owner, acceptance criteria, points and ticket keys; a program board of features by sprint with capacity against planned points and a milestones row; dependencies with needed-by sprint; milestones and events; risks by ROAM with private notes; the fist-of-five confidence vote; 83 tests

- [x] 2026-10-16: Toolkit day-45 batch: sprint notebook (sprints, start-next-sprint, private ceremony notes per sprint with prompts, follow-ups that become dev-sync items and carry into the next sprint), optional SAFe Program Increments and innovation and planning sprints; Agile roadmap with target days turned into dates; RACI matrix with editable roles and a one-accountable check; risks, decisions needed, metrics and readings; starter content (roadmap, RACI decisions, delivery metrics); weekly status draft built only from exportable data with a suggested overall color; Comms studio pulls the draft over an export-only token from a Connections screen; 78 tests

- [x] 2026-10-15: Vendor relationships: vendors (type, status, account contacts from People, support process, service promise, contract dates, renewal notice, private commercial terms and notes); private conversation log with who was involved; open concerns with owners and due dates; follow-ups from a conversation become dev-sync items tagged with the vendor; renewals and due concerns on Today; escalation systems link to their vendor; database upgrade tested; 67 tests

- [x] 2026-10-15: Design system pass: Tailwind CSS v4.3.3 (standalone CLI, checksum verified) building one shared stylesheet; light and dark tokens with a theme switch (system, light, dark); Inter and a Lucide icon subset vendored with licenses; new shell with icon navigation, command palette (Cmd+K or /) with app actions, keyboard shortcuts (?, Shift+P, Shift+T), loading skeletons, view transitions, mobile menu; restyled buttons, inputs, cards, tables, pills, dialogs, toasts and sign-in pages

- [x] 2026-10-15: Toolkit day-30 batch: dev-sync action log (owners, due dates, overdue view, filters, private notes, group-learning flag that proposes a session); group learning schedule (from dev sync or proposed from teach/learn matches); escalation playbook (systems with owner, first responder and backup, business-hours and out-of-hours chains, severity levels, incident log with follow-ups that become dev-sync items; vendor lines private); Today shows overdue dev-sync items; placeholder data fills only empty parts; 61 tests

- [x] 2026-10-15: Comms studio version 1: messages with draft, review, ready, sent and archived states; versions on every body change; starter kit of nine templates, six audiences, placeholder channels and weekly rhythms; comms calendar with due items and start-drafting dates; sent log that keeps the exact text, channel, audiences and check results; checks for placeholders left (blocks ready), plain language with a glossary, long sentences and summary first; export by copy, Markdown download or print to PDF, each logged; drafts private, sent messages shareable; 54 tests

- [x] 2026-10-15: Deck builder prototype: reveal.js 5.1.0 and lottie-web 5.12.2 (light player) bundled locally with checksums verified; decks, slides and a media library with uploads and seekable playback; one renderer for editor and present page; three-pane editor with drag-to-reorder, live canvas and inspector; 11 layouts (title, section, big number, points, quote, comparison, image, video, audio, animation, closing); video and audio players with trim, loop, poster, captions and play-on-enter or on-click; Lottie with loop, play-once, on-click, speed and segments; full-screen present page with speaker notes; placeholder deck with generated tone and animation; 43 tests

- [x] 2026-10-15: Toolkit version 1: people and team profiles, skills and learning matrix with teach/learn matches, listening tour, day-30 rollup with Markdown copy, my development (learning goals and log, tasks, obligations, contract start date), Today, placeholder data loader, reusable records layer in the base, 36 tests
- [x] 2026-10-15: Shared base (sign-in, sessions, privacy levels, presentation mode, scoped tokens, change and export logs, UI shell) and toolkit and Comms studio skeletons
- [x] 2026-10-15: Licensed presentation templates kept out of the repo
