# Backlog

Everything planned for the apps, so nothing falls through the cracks. When one option is chosen over another, the one not chosen stays here until it's built. Items move to **Done** with the date.

Specs: toolkit and Comms studio planning docs (linked from the planning workspace README).

## In progress

Nothing right now.

## Next up

- [ ] **Comms studio version 1:** messages, templates, audiences and channels, comms calendar, sent log, plain-language check
- [ ] **Deck builder prototype (Comms studio):** reveal.js and lottie-web bundled locally, three-pane editor (slide list, live canvas, inspector), a first set of layouts, placeholder content

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

- [ ] Writing checks: placeholders left, one version of the truth, no surprises, stale facts, sensitive content, summary first, questions answered
- [ ] Fact snapshots from the toolkit over an `export:read` token
- [ ] Deck builder, full: theme layouts, narrative templates and outline-first skeletons, headline check, fact-bound numbers and charts, custom HTML slide in a sandbox, speaker view and rehearsal log
- [ ] **Media players in slides:** video and audio elements with play, pause, scrub and volume; trim start and end; play on entering the slide or on a click step; loop; poster frame; captions track; controllable from the speaker view
- [ ] Lottie animation library with play triggers, speed and segments
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

- [x] 2026-10-15: Toolkit version 1: people and team profiles, skills and learning matrix with teach/learn matches, listening tour, day-30 rollup with Markdown copy, my development (learning goals and log, tasks, obligations, contract start date), Today, placeholder data loader, reusable records layer in the base, 36 tests
- [x] 2026-10-15: Shared base (sign-in, sessions, privacy levels, presentation mode, scoped tokens, change and export logs, UI shell) and toolkit and Comms studio skeletons
- [x] 2026-10-15: Licensed presentation templates kept out of the repo
