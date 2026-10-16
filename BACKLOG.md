# Backlog

Everything planned for the apps, so nothing falls through the cracks. When one option is chosen over another, the one not chosen stays here until it's built. Items move to **Done** with the date.

Specs: toolkit and Comms studio planning docs (linked from the planning workspace README).

## In progress

Nothing right now.

## Next up

In the order the 90-day plan needs them:

- [ ] **Vendor relationships (toolkit):** vendors with type, account contacts (from People), support process, contract and renewal dates, service promise and private commercial terms; a communication log (date, vendor, people, channel, summary, concerns, follow-ups that become dev-sync items); open concerns per vendor; renewals on Today; escalation systems linked to their vendor
- [ ] **Toolkit, day-45 batch:** sprint notebook, Agile roadmap items, RACI, risks and decisions, weekly status draft that feeds the Comms studio
- [ ] **Platform before real data:** nightly backups with a tested restore, local beanagile.org setup

## Toolkit, later versions

- [ ] Themes as their own records (version 1 stores them as tags on each one-on-one)
- [ ] Sprint notebook: sprints, a private note per ceremony, follow-ups that carry into the next planning note
- [ ] SAFe support: optional Program Increments, innovation and planning sprints, PI planning and end-of-PI demo notes
- [ ] Agile roadmap items with target days and status
- [ ] RACI matrix with confirm status per row
- [ ] Risks, decisions needed, metrics and metric readings
- [ ] Weekly status draft (`/api/status/draft`) and the filtered export with preview
- [ ] Escalation playbook: reorder steps by dragging, and link incidents to sprints once sprints exist
- [ ] Dev-sync log: link items to a sprint once the sprint notebook exists
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
- [ ] Fact snapshots from the toolkit over an `export:read` token
- [ ] Deck builder, full: theme layouts, narrative templates and outline-first skeletons, headline check, fact-bound numbers and charts, custom HTML slide in a sandbox, speaker view and rehearsal log
- [ ] Media players: control playback from the speaker view (players work on the slide in the prototype)
- [ ] Lottie: preview segments by frame in the inspector
- [ ] Themes from Envato Elements: template folder outside the repo, layouts mapped to slide types
- [ ] Export: single-file HTML deck, PDF, PowerPoint on the template
- [ ] Media production board: script, storyboard, shot list, recording, edit, captions, review, publish
- [ ] Questions log and communication measures

## Shared base and platform

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

- [x] 2026-10-15: Design system pass: Tailwind CSS v4.3.3 (standalone CLI, checksum verified) building one shared stylesheet; light and dark tokens with a theme switch (system, light, dark); Inter and a Lucide icon subset vendored with licenses; new shell with icon navigation, command palette (Cmd+K or /) with app actions, keyboard shortcuts (?, Shift+P, Shift+T), loading skeletons, view transitions, mobile menu; restyled buttons, inputs, cards, tables, pills, dialogs, toasts and sign-in pages

- [x] 2026-10-15: Toolkit day-30 batch: dev-sync action log (owners, due dates, overdue view, filters, private notes, group-learning flag that proposes a session); group learning schedule (from dev sync or proposed from teach/learn matches); escalation playbook (systems with owner, first responder and backup, business-hours and out-of-hours chains, severity levels, incident log with follow-ups that become dev-sync items; vendor lines private); Today shows overdue dev-sync items; placeholder data fills only empty parts; 61 tests

- [x] 2026-10-15: Comms studio version 1: messages with draft, review, ready, sent and archived states; versions on every body change; starter kit of nine templates, six audiences, placeholder channels and weekly rhythms; comms calendar with due items and start-drafting dates; sent log that keeps the exact text, channel, audiences and check results; checks for placeholders left (blocks ready), plain language with a glossary, long sentences and summary first; export by copy, Markdown download or print to PDF, each logged; drafts private, sent messages shareable; 54 tests

- [x] 2026-10-15: Deck builder prototype: reveal.js 5.1.0 and lottie-web 5.12.2 (light player) bundled locally with checksums verified; decks, slides and a media library with uploads and seekable playback; one renderer for editor and present page; three-pane editor with drag-to-reorder, live canvas and inspector; 11 layouts (title, section, big number, points, quote, comparison, image, video, audio, animation, closing); video and audio players with trim, loop, poster, captions and play-on-enter or on-click; Lottie with loop, play-once, on-click, speed and segments; full-screen present page with speaker notes; placeholder deck with generated tone and animation; 43 tests

- [x] 2026-10-15: Toolkit version 1: people and team profiles, skills and learning matrix with teach/learn matches, listening tour, day-30 rollup with Markdown copy, my development (learning goals and log, tasks, obligations, contract start date), Today, placeholder data loader, reusable records layer in the base, 36 tests
- [x] 2026-10-15: Shared base (sign-in, sessions, privacy levels, presentation mode, scoped tokens, change and export logs, UI shell) and toolkit and Comms studio skeletons
- [x] 2026-10-15: Licensed presentation templates kept out of the repo
