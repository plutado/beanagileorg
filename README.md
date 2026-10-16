# beanagile

Local-first supporting apps for engineering leaders. Each app runs on your own machine, listens only on localhost, and keeps its data in a SQLite file outside this repository.

- **Toolkit** (`beanagile toolkit`, port 8801): team, listening tour, sprints, roadmap, status and my development.
- **Comms studio** (`beanagile comms`, port 8802): messages, templates, writing checks, presentations and media.

Both run on their own. An [Odysseus](https://github.com/odysseus-dev/odysseus) hub is optional: when configured, the apps use it for documents, local models and scheduled jobs.

## Features

### Everywhere

- **Local and private by default.** Each app listens on localhost only and keeps its data in a SQLite file outside the repository.
- **Privacy levels.** Every field is tagged private, presentable or exportable, and the server filters every read. New fields default to private.
- **Presentation mode.** One switch (or Shift+P) before sharing your screen hides every private field on every screen, enforced on the server.
- **Sign-in.** One password per app, an optional authenticator (TOTP) and a throttle on failed attempts.
- **Scoped API tokens** for LLM clients and the other app: `export:read`, `present:read`, `full`, plus app scopes such as `delivery:write`.
- **Change log and export log.** Every data change records the field, old and new value and who made it (you or a named token), and every export records what went out.
- **Design system.** Tailwind CSS v4 tokens with light and dark themes, Inter type, Lucide icons and responsive layouts.
- **Command palette and shortcuts.** ⌘K or / jumps to any screen or runs an action; ? lists the shortcuts.
- **Placeholder data.** One click fills empty parts of an app with bracketed `[Placeholder]` values for trying things out.

### Toolkit

**Team**

- **Today:** overdue tasks and dev-sync items, what's due this week, obligations, this week's one-on-ones, learning goals at risk, vendor renewals and vendor concerns.
- **People and team profiles:** role, relationship, background, skills, certifications, goals, what each person wants to learn and can teach, working style and support notes. Only names and roles show in presentation mode.
- **Skills and learning:** a skills matrix and matches between who can teach and who wants to learn, each one proposable as a group learning session.
- **Listening tour:** one record per one-on-one with the same four questions every time (what's working, what's frustrating, what to change first, what not to change), plus systems mentioned, gaps, opportunities and themes. Private end to end.
- **Day-30 rollup:** themes ranked by how often they come up, with supporting quotes, gaps, opportunities and "don't change" notes, copyable as Markdown for the written diagnosis.

**Delivery**

- **Sprint notebook:** sprints with goals and dates, a private note per ceremony (planning, refinement, review, retro, dev sync, ad hoc, PI planning, end-of-PI demo) with prompts for what happened, what you noticed, implementation thoughts and follow-ups. Follow-ups become dev-sync items tied to the sprint, and anything still open shows in the next sprint's notebook.
- **SAFe-ready:** optional Program Increments and innovation and planning sprints.
- **Roadmap:** Agile adoption items with target days that turn into real dates once the contract start date is set, plus status and owner.
- **RACI:** decisions by role, with editable roles, a confirm status per row and a check for exactly one accountable person.
- **Risks and decisions:** risks by level, owner, next step and due date, and decisions needed with who decides, when, and the outcome.
- **Metrics:** baseline, target and readings over time for each measure, with an on-target indicator. Starter metrics are cycle time, deployment frequency, change failure rate and escaped defects.
- **Dev-sync log:** every question raised after standup, with who raised it, owner, next action, due date, status, origin and private notes. Overdue items stand out, and the group-learning flag proposes a presentation.
- **Group learning:** a schedule of short team presentations, fed by the dev-sync log and by teach/learn matches.
- **Vendors:** type, status, account contacts, support process, service promise, contract dates and renewal notice; commercial terms stay private. A private conversation log, open concerns with owners, and follow-ups that become dev-sync items.

**Reporting**

- **Weekly status:** a draft built only from exportable data (current sprint, milestones, risks, decisions, what shipped, next week, metrics and reportable learning goals) with a suggested overall color and the reason. Copy it as Markdown, or pull it into the Comms studio.

**Knowledge**

- **Escalation playbook:** systems with owner, first responder, backup and linked vendor, business-hours and out-of-hours escalation chains, severity levels, and an incident log whose follow-ups become dev-sync items.

**Me**

- **My development:** learning goals with time logged and a report toggle that controls what reaches status reports, plus tasks, recurring obligations and the contract start date.

**Starter content:** one click loads a generic Agile adoption roadmap, the five common RACI decisions and the four delivery metrics.

### Comms studio

**Messages**

- **This week:** messages due from your rhythms, drafts in progress and recently sent.
- **Messages:** draft, review, ready, sent and archived states, with a saved version on every edit and one-click restore.
- **Writing checks** that run as you type. Leftover placeholders block "ready"; jargon is flagged with a plainer word (built-in list plus your own glossary); long sentences and a missing opening summary get warnings.
- **Templates:** a starter kit of nine (weekly note, weekly status, alert, release notes, decision announcement, day-30 diagnosis, day-90 and quarterly review, team announcement, sprint review), each with default audiences and channel.
- **Comms calendar:** rhythms (weekly, every two weeks, monthly, quarterly) that create due items with a start-drafting date and a one-click draft from the right template.
- **Sent log:** the exact text, channel, audiences and check results of everything marked sent.
- **Audiences and channels:** who needs what, at what level of detail, and where they usually hear it.
- **Exports:** copy as text, download Markdown or print to PDF, each logged.
- **Toolkit connection:** pull the toolkit's weekly status draft into a message over an export-only token.
- **Privacy:** drafts are private; sent messages are shareable.

**Presentations**

- **Deck builder:** a three-pane editor (slide list with drag to reorder, live reveal.js canvas, inspector) over slides stored as structured data.
- **Eleven layouts:** title, section break, one big number, points (optionally revealed one at a time), quote, comparison, image, video, audio, animation and closing.
- **Media players:** video and audio with trim start and end, loop, poster frame, captions, and play on entering the slide, on a click or only when pressed.
- **Lottie animations:** loop, play once, play on a click, speed and frame segments. The light player runs no expressions.
- **Present:** full screen from the same renderer as the editor, with reveal.js's speaker view (notes, next slide, timer).
- **Media library:** uploads of video, audio, images, Lottie and WebVTT captions, with type checks, seekable playback, source and license recorded, and license details kept private.

## Run

```bash
uv sync
uv run beanagile toolkit
```

Then open http://127.0.0.1:8801. The first visit asks you to set a password.

For development, `uv run beanagile toolkit --reload` restarts on code changes.

## Shared base (`src/beanagile/core`)

| Piece | What it does |
| --- | --- |
| Sign-in | One user per app: scrypt password, optional authenticator (TOTP), sessions in a hashed cookie, a throttle on failed sign-ins |
| Privacy levels | Every field is tagged private, presentable or exportable. Reads are filtered on the server; untagged fields count as private |
| Presentation mode | A per-session switch that hides private fields everywhere, for screen sharing |
| API tokens | Scoped tokens for LLM clients and the other app: `export:read`, `present:read`, `full`, plus app scopes such as `delivery:write` |
| Change log | Every data change records the field, old and new value, and who made it |
| Exports | One path that filters to exportable fields and logs what went out |
| UI shell | Navigation, routing, presentation toggle and a Settings screen for sign-in, tokens and history |

## Design system

Styles come from one Tailwind CSS v4 source, `src/beanagile/core/static/app.src.css`: design tokens (light and dark), base styles and the shared components. The built `app.css` is committed, so running the apps needs no build step. After editing the source, rebuild with:

```bash
./scripts/build-css.sh
```

The script uses Tailwind's standalone CLI from `.tools/` (not committed). Icons are a Lucide subset (`scripts/build_icons.py`), and the font is Inter; both are vendored with their licenses. Press ⌘K in either app for the command palette, or ? for keyboard shortcuts.

## Data

Data lives in `~/.beanagile/<app>/` (override with `BEANAGILE_DATA`). Nothing in this repository is real data; examples and samples are always marked `[Placeholder]`.

Optional Odysseus link: set `BEANAGILE_ODYSSEUS_URL` and `BEANAGILE_ODYSSEUS_TOKEN`.

## Test

```bash
uv run pytest
```

## License

MIT. See [LICENSE](LICENSE). Odysseus is a separate AGPL-3.0 project; these apps only talk to it over its API and include none of its code.
