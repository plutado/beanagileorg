# Backlog

Everything planned for the apps, so nothing falls through the cracks. When one option is chosen over another, the one not chosen stays here until it's built. Items move to **Done** with the date.

Specs: toolkit and Comms studio planning docs (linked from the planning workspace README).

## In progress

Nothing right now.

## Next up

In the order the 90-day plan needs them:

- [ ] **Toolkit, day-30 batch:** dev-sync action log, group learning schedule, escalation playbook (details under Toolkit, later versions)
- [ ] **Toolkit, day-45 batch:** sprint notebook, Agile roadmap items, RACI, risks and decisions, weekly status draft that feeds the Comms studio
- [ ] **Platform before real data:** nightly backups with a tested restore, local beanagile.org setup

## Toolkit, later versions

- [ ] Themes as their own records (version 1 stores them as tags on each one-on-one)
- [ ] Group learning: "propose a session" from a teach/learn match
- [ ] Dev-sync action log, with overdue view and group-learning flag
- [ ] Group learning schedule, with teach/learn matches from team profiles
- [ ] Sprint notebook: sprints, a private note per ceremony, follow-ups that carry into the next planning note
- [ ] SAFe support: optional Program Increments, innovation and planning sprints, PI planning and end-of-PI demo notes
- [ ] Agile roadmap items with target days and status
- [ ] RACI matrix with confirm status per row
- [ ] Risks, decisions needed, metrics and metric readings
- [ ] Weekly status draft (`/api/status/draft`) and the filtered export with preview
- [ ] Escalation playbook: systems, severities, escalation steps, incident log
- [ ] Documentation library: links to Odysseus documents with owner and last-reviewed date
- [ ] Decision log
- [ ] Meeting decks: saved sequences of live views, presented like slides
- [ ] Delivery dashboard
- [ ] Scrum of Scrums board from imported team status packs

## Comms studio, later versions

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

- [x] 2026-10-15: Comms studio version 1: messages with draft, review, ready, sent and archived states; versions on every body change; starter kit of nine templates, six audiences, placeholder channels and weekly rhythms; comms calendar with due items and start-drafting dates; sent log that keeps the exact text, channel, audiences and check results; checks for placeholders left (blocks ready), plain language with a glossary, long sentences and summary first; export by copy, Markdown download or print to PDF, each logged; drafts private, sent messages shareable; 54 tests

- [x] 2026-10-15: Deck builder prototype: reveal.js 5.1.0 and lottie-web 5.12.2 (light player) bundled locally with checksums verified; decks, slides and a media library with uploads and seekable playback; one renderer for editor and present page; three-pane editor with drag-to-reorder, live canvas and inspector; 11 layouts (title, section, big number, points, quote, comparison, image, video, audio, animation, closing); video and audio players with trim, loop, poster, captions and play-on-enter or on-click; Lottie with loop, play-once, on-click, speed and segments; full-screen present page with speaker notes; placeholder deck with generated tone and animation; 43 tests

- [x] 2026-10-15: Toolkit version 1: people and team profiles, skills and learning matrix with teach/learn matches, listening tour, day-30 rollup with Markdown copy, my development (learning goals and log, tasks, obligations, contract start date), Today, placeholder data loader, reusable records layer in the base, 36 tests
- [x] 2026-10-15: Shared base (sign-in, sessions, privacy levels, presentation mode, scoped tokens, change and export logs, UI shell) and toolkit and Comms studio skeletons
- [x] 2026-10-15: Licensed presentation templates kept out of the repo
