# beanagileorg

[![CI](https://github.com/plutado/beanagileorg/actions/workflows/ci.yml/badge.svg)](https://github.com/plutado/beanagileorg/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

**Be an Agile organization.** beanagileorg is a private, local toolkit for the people who bring Agile to software teams and keep it working: engineering managers, Scrum Masters and delivery leads. It starts from Scrum as the Scrum Guide defines it, helps a team adopt it one trial at a time, scales to a Scrum of Scrums and is ready for SAFe, and keeps the people side (trust, one-on-ones, a new leader's first 90 days) beside the delivery side.

Two small web apps run on your own machine: a **Toolkit** for leading the team and its delivery (sprints, retros, the backlog, the Scrum of Scrums, people, plans and reports), and a **Comms studio** for the updates and decks that make progress visible. Everything is stored in a SQLite file on your disk, the apps listen on localhost only, and every field carries a privacy level, so you can share your screen in a meeting without exposing private notes. No account, no cloud service and no telemetry.

| | |
| --- | --- |
| ![Toolkit: Today](docs/images/toolkit-today.png) | ![Toolkit: org chart](docs/images/toolkit-org-chart.png) |
| **Today**: what needs you, across the whole toolkit | **People**: an org chart drawn from reporting lines |
| ![Toolkit: sprint planning](docs/images/toolkit-sprint-planning.png) | ![Comms studio: deck builder](docs/images/comms-deck-builder.png) |
| **Sprint planning**: capacity, availability and ready stories | **Comms studio**: the reveal.js deck builder |

All screenshots use the built-in placeholder data; every value in brackets is invented.

## Who it's for

People responsible for making Agile real, not just named: a manager bringing Scrum to a team that has been working ad hoc, a Scrum Master who wants the events, artifacts and commitments to actually work, or a leader asked to spread good practice across several teams and run their Scrum of Scrums. It suits someone starting a new leadership role (the First 90 days screens, listening tour and 30/60/90 plans are built for that) as well as someone running an established team week to week, and it keeps everything in one private place instead of scattered across documents, spreadsheets and chat.

## Becoming an Agile organization

How the toolkit maps onto the work of adopting Agile:

| | Where it lives |
| --- | --- |
| **Start from the definition.** Import the official Scrum Guide into your own data, read it together in four planned team sessions, and see the definition of Scrum first. | Agile reference |
| **Know where you stand.** Every Scrum accountability, event, artifact and commitment, common practices and SAFe concepts, each marked as practiced, partly or not yet, with a coverage view of the gaps. | Agile reference |
| **Run the events.** Sprint planning against capacity and a sprint goal, the daily scrum's follow-ups, sprint reviews and retrospectives whose commitments are reviewed next time. | Sprint planning, Dev-sync log, Sprint notebook, Retrospectives |
| **Keep the artifacts honest.** One refined, estimated product backlog beside Jira, sprint backlogs, a definition of ready and a definition of done, with QA built in. | Sprint planning, QA resources, SDLC |
| **Bring change in well.** Each change announced with its reason, tried for a set time, reviewed with the team and then kept or dropped, in waves rather than all at once, with team agreements and the behaviors you want to shift. | First 90 days, Culture and trust |
| **Read the situation.** Diagnose each area as a start-up, turnaround, accelerated growth, realignment or sustaining success, and lead change at the pace each needs. | First 90 days |
| **Make the case with facts.** Delivery metrics beside outside benchmarks such as DORA, sprint and weekly reports, and updates that need no meeting. | Metrics, Reports, Comms studio |
| **Scale it.** Teams, a Scrum of Scrums with owners and dates on every cross-team item, PI planning when the organization runs SAFe, and support for mentoring other managers as they adopt the practices. | Teams, Scrum of Scrums, PI planning, First 90 days |

## Status

Actively developed and used daily by the author. It works end to end and has a test suite that runs on every push, but it is young: the database schema may still change between versions (upgrades are applied automatically on start), and there are no tagged releases yet. Back up your data before pulling a new version (`beanagileorg backup all`).

## Quick start

You need [uv](https://docs.astral.sh/uv/) (on macOS or Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`; see its docs for Windows). uv fetches Python 3.12 or later for you if it isn't already installed.

```bash
git clone https://github.com/plutado/beanagileorg.git
cd beanagileorg
uv sync
uv run beanagileorg toolkit    # http://127.0.0.1:8801
uv run beanagileorg comms      # http://127.0.0.1:8802, in a second terminal
```

The first visit to each app asks you to choose a password (at least 12 characters); each app has its own. An authenticator code (TOTP) can be added later under Settings.

To look around without entering anything real, press **Load placeholder data** on the Toolkit's empty Today screen, and **Load placeholder deck** under Decks in the Comms studio. Every placeholder value is in brackets so it can't pass for real data.

Data goes to `~/.beanagileorg/<app>/`. To try the apps against a throwaway folder instead, set `BEANAGILEORG_DATA`:

```bash
BEANAGILEORG_DATA=/tmp/beanagileorg-demo uv run beanagileorg toolkit
```

## Search and Ask

**Search** needs nothing extra. Open Search in the sidebar, or press ⌘K (or /), type a word or two and choose *Search everything*. It's a keyword search over every record you can see, best matches first, grouped by kind, each linking to the record.

**Ask** answers questions in plain sentences ("what's overdue?", "who haven't I talked to this month?"), with links to the records it used. It needs a model. Under the hood it uses the same search, plus tools to read records and lists, so nothing needs indexing by hand: the index is built in memory from your data and rebuilt automatically whenever something changes.

To set Ask up with a local model:

1. Install [Ollama](https://ollama.com) and pull a model that supports tool calling, for example:

   ```bash
   ollama pull qwen3.6:35b-a3b
   ```

   Larger models answer better but need more memory; a smaller tool-calling model works on modest hardware.
2. In the app, open **Settings → Ask**. Keep the provider as OpenAI-compatible, the address as `http://127.0.0.1:11434/v1`, and set the model name you pulled.
3. Ask a question from the box on Today (Toolkit) or This week (Comms studio).

Any OpenAI-compatible server works the same way (LM Studio, vLLM, a hosted endpoint). Anthropic is supported too: choose it and paste an API key, which is stored in a file in your data folder readable only by you, never in the database or the browser. A cloud provider sees shareable data only unless you explicitly allow more, and every question sent to one is logged under Exports. With a local model, an option unloads it after each answer to free memory.

Image generation in the Comms studio is also optional: point it at any local server with an OpenAI-style images API (the default address is `http://127.0.0.1:8710/v1`). Infographics need no model.

## Built with

- **Python 3.12+** with **FastAPI** and **Uvicorn**, and **SQLite** through the standard library. Three runtime dependencies in total.
- **Plain JavaScript** front ends with no build step for the apps themselves.
- **Tailwind CSS v4** (standalone CLI) for one shared design system with light and dark themes; the built CSS is committed.
- **reveal.js** for decks, **lottie-web** (light player) for animations, **highlight.js** for code blocks, **Lucide** icons and the **Inter** typeface, all vendored with their licenses so the apps work offline.
- **uv** for environments and the lockfile, **pytest** for the test suite.
- Optional: a local model through **Ollama** or any OpenAI-compatible server for Ask, and a local image service for generated illustrations.

## Features

### Everywhere

- **Local and private by default.** Each app listens on localhost only and keeps its data in a SQLite file outside the repository.
- **Privacy levels.** Every field is tagged private, presentable or exportable, and the server filters every read. New fields default to private.
- **Presentation mode.** One switch (or Shift+P) before sharing your screen hides every private field on every screen, enforced on the server.
- **Sign-in.** One password per app, an optional authenticator (TOTP) and a throttle on failed attempts.
- **Scoped API tokens** for LLM clients and the other app: `export:read`, `present:read`, `full`, plus app scopes such as `delivery:write`.
- **Change log and export log.** Every data change records the field, old and new value and who made it (you or a named token), and every export records what went out.
- **Design system.** Tailwind CSS v4 tokens with light and dark themes, Inter type, Lucide icons and responsive layouts.
- **History.** Records you write in (notes, meeting summaries, guides, decisions, policies, stories and more) keep every saved change, compared line by line, with a way to restore an earlier version.
- **Code blocks.** Paste code between triple backticks in any longer text box (Apex, SOQL, LWC markup, JSON, YAML and more) and it's kept exactly as pasted and shown like a code editor, with a copy button.
- **Jira keys.** Anything tracked in Jira (dev-sync items, risks, roadmap items, tests and test failures, incidents, retro commitments, onboarding items, vendor concerns, decisions, stories and tech debt) can carry its Jira keys, which link straight to the issue once the Jira address is set. Find a Jira key shows everywhere a key is mentioned.
- **Built-in guidance.** Every section explains its purpose and how to use it at the top of the page, and the Help page gathers them into one guide.
- **Command palette and shortcuts.** ⌘K or / jumps to any screen or runs an action; ? lists the shortcuts.
- **Backups that are checked.** `beanagileorg backup all` snapshots each app's data and restores it to a scratch folder to prove it's good; `beanagileorg restore` puts one back without deleting what was there; `beanagileorg schedule` sets up nightly backups. See [docs/backups.md](docs/backups.md).
- **Local domain.** Open the apps at https://toolkit.beanagile.org and https://comms.beanagile.org on your own machine, with Caddy and local certificates; requests addressed to any other name are refused. See [docs/local-domain.md](docs/local-domain.md).
- **Design specs.** The company-neutral plans the apps were built from, plus the video message platform still to come. See [docs/specs](docs/specs/README.md).
- **Placeholder data.** One click fills empty parts of an app with bracketed `[Placeholder]` values for trying things out.
- **Search.** A keyword search over every record you can see, from the sidebar or the command palette, with no model needed.
- **Ask.** A question box answers plain-language questions from the app's own data, with links to the records it used. Any model: a local one through Ollama by default, any OpenAI-compatible server (LM Studio, vLLM, Odysseus) or a hosted provider, set under Settings. The model reaches the data through search and lookup tools at your privacy level; a cloud provider gets shareable data only unless you allow more, every cloud question is logged, and a local model can be unloaded after each answer to free memory.

### Toolkit

**Team**

- **Today:** an Ask box, a quick work log, and what needs you: overdue tasks and dev-sync items, what's due this week, obligations, one-on-ones and check-ins, commitments, change requests waiting, reports due, culture follow-ups and today's standard, First 90 days milestones and check-ins, mandate reviews, quiet peers, people named on your systems you haven't met yet, vendor renewals and learning goals at risk.
- **People, a private CRM:** a page for everyone you work with: title, location, contact, who they report to, teams, how they like to communicate, what motivates them, things to remember and key dates. Log every one-on-one, meeting and call with notes, takeaways and follow-ups; see relationship health against a check-in cadence, a Before you meet summary and a timeline across the toolkit. Choose which fields to use; sensitive notes stay masked until you show them, and private fields never appear while presenting.
- **Manager tools:** mark yourself, and your direct reports get a Manager tab: growth goals, a log of praise, feedback, wins and concerns (marked shared or not), and a drafted one-on-one agenda. Commitments both ways on anyone's page (what you owe them, what they owe you), with yours due and theirs late on Today.
- **Org chart:** reporting lines drawn from each person's Reports to, with every person a link to their page.
- **Placeholders and rosters:** stand-in people in [brackets] until you know who they are, marked and filterable; a real name clears the mark and keeps their history. Import a whole team from a roster file: people, reporting lines, team membership and which record is you.
- **Relationship balance:** your conversations split up (your management chain), down (your reporting line), sideways (peers) and outward, against the period before, with peers listed quietest first. Each person can carry what you can offer them, what you need from them, what they expect from you, and the kind of advice you go to them for. Today nudges when conversations skew upward or a key peer goes quiet.
- **Culture and trust:** your standards (one shown on Today each day, with a weekly self-check), a private log of what you notice (intimidation, chaos from missing process, quiet voices, blame, and the good moments), a trust pulse over time, team agreements, a role brief, **behaviors to change** (the patterns that stand in the way, such as lack of focus or discipline, and how you want people to work instead), a **culture map** that reads each unit (your team, a team you're integrating, the wider organization) in three layers (what's visible, everyday norms such as how influence, meetings, conflict and recognition work, and the assumptions about power underneath), and a **glossary** of the local language.
- **First 90 days:** three tracks side by side by day number: yours (plans, listening tour, reflections), each new hire's onboarding, and the team you inherit, whose first 90 days with you get milestones, a "Working with me" page, a plan for how you'll engage each audience in your first days, check-ins at days 30, 60 and 90 (each with an informal 360 on how you're adapting), and a visible list of the changes you're bringing (announced, tried, reviewed, then kept or dropped), grouped into waves, with a warning when too many are under way at once, and a readiness check on each (awareness, diagnosis, vision, plan, support) that says whether to plan and implement or to build the missing piece together first. Also: mandates for you and each report (purpose, outcomes, decision rights, proposals and open questions, agreed with a review date), a situation diagnosis per area (start-up, turnaround, accelerated growth, realignment or sustaining success, each with its usual mood, your job with it, its pace, and its typical challenges and opportunities, plus how the area got here, a warning when areas need different paces, and a portfolio view that sorts your areas into the five situations with a share of effort for each, checks that the kind of situation you most enjoy isn't getting the most effort by default, and copies as Markdown to share; turnarounds and realignments also show how to lead change in each: learning, intent, priorities, team, early wins and alliances; each situation notes whether it calls for a hero or a steward, and the portfolio checks that against your own style and shows your team's mix), a learning agenda (starter questions on the business, the people, the culture, the history and how decisions really get made, which turn into hypotheses to test as you learn, with a warning when technical questions crowd out culture and politics), a view of whose perspective you're learning from (customers, vendors, the frontline, integrators, natural historians and more) and which gaps remain, a checklist of structured ways to learn, a phased learning plan from before day 1 to day 60 (including two reviews of your hypotheses with your manager), conversations with your manager (where each stands and its priorities for the next 30 days, your manager's top three priorities, three things for the next one-on-one, what they're protective of, a resource menu of what each level of support buys, how they like to work, and what to ask them for given your situations), the same five conversations with each of your reports (situation, expectations, resources, style, development) with status and priorities, the managers you mentor, and a Momentum card.
- **Onboarding:** a checklist template by track (Salesforce, MuleSoft, QA, employee, contractor) from the week before day 1 to day 90, copied for each new member with real dates, progress, items for you, the buddy and IT, a materials list, and a Markdown checklist to send them. Hires from outside the company get a business orientation and a culture guide as well as a buddy. Items due for you show on Today.
- **Skills and learning:** a skills matrix and matches between who can teach and who wants to learn, each one proposable as a group learning session.
- **Listening tour:** one record per one-on-one with the same five questions every time (what's working, what's frustrating, what to change first, what not to change, and what they'd focus on in your place), a private note on how each person answered, plus systems mentioned, gaps, opportunities and themes. Private end to end.
- **Day-30 rollup:** themes ranked by how often they come up, with supporting quotes, gaps, opportunities and "don't change" notes, copyable as Markdown for the written diagnosis.

**Across teams**

- **Teams:** your team and the teams you work with or oversee, with members, roles, Jira project, current sprint and goal, and a dated status. Delivery records carry a team, each team numbers its own sprints, and a team picker filters the delivery screens.
- **Scrum of Scrums:** the cross-team log of questions, dependencies, decisions, risks, impediments and knowledge, each with stakeholders, an owner, the outcome expected and a date; meetings that walk every open item; and a summary for the layer above.

**Delivery**

- **Agile reference:** every Scrum accountability, event, artifact and commitment (with timeboxes), the practices teams commonly add (refinement, definition of ready, estimation, velocity, working agreements, Scrum of Scrums and more), and SAFe's main concepts (agile release trains, planning intervals, PI planning, the IP iteration, system demo, inspect and adapt, ROAM, WSJF and more). Once the Scrum Guide is imported, each Scrum entry shows the guide's own wording with a link to its section; otherwise entries carry clearly labelled summaries in original words. Each links to where the toolkit supports it, and records how far the team practices it and how; a coverage view shows the gaps. The Scrum Guide itself can be imported from scrumguides.org into your own data (or pasted in), read by section with its Creative Commons attribution, shown on screen, and studied with the team in four planned reading sessions; the Scrum tab opens with its definition of Scrum and any other definitions you add.
- **SDLC:** how work moves from idea to production: stages with when each starts and when it's done, who's involved and what it produces; environments and the promotion path for Salesforce and MuleSoft; policies from draft to agreed; change history; and the whole thing as one Markdown document to share.
- **Sprint planning:** the backlog of candidate stories beside Jira (paste keys and titles), refined against a definition of ready and estimated together with team votes; then plan each sprint from who's available and recent velocity, pull ready stories up to capacity, set the goal, commit, and close the sprint to carry unfinished work over. A plan summary copies back to Jira.
- **Sprint notebook:** sprints with goals and dates, a private note per ceremony (planning, refinement, review, retro, dev sync, ad hoc, PI planning, end-of-PI demo) with prompts for what happened, what you noticed, implementation thoughts and follow-ups. Follow-ups become dev-sync items tied to the sprint, and anything still open shows in the next sprint's notebook.
- **SAFe-ready:** optional Program Increments and innovation and planning sprints.
- **Retrospectives:** a shared board per sprint in four formats, with votes and topic tags; commitments with owner, due date and status, tagged to the sprint they came from; each retro opens by reviewing earlier commitments; a running improvement backlog and a list of topics that keep coming back.
- **PI planning:** objectives with planned and actual business value and predictability; epics, features and stories with priority, acceptance criteria, points and ticket keys; a program board by sprint with capacity checks and milestones; dependencies, ROAM risks and the confidence vote. Presentable throughout.
- **Roadmap:** Agile adoption items with target days that turn into real dates once your start date is set, plus status and owner.
- **RACI:** decisions by role, with editable roles, a confirm status per row and a check for exactly one accountable person.
- **Tech debt:** a register classified by what fixing each item buys (maintainability, stability, performance, cleanup, revenue and conversion, observability, security, delivery speed, cost), scored by impact, risk and effort into quick wins, big bets, fill-ins and money pits; an agreed share of sprint capacity checked each sprint; a decision log with revisit dates; and a shareable summary for leadership.
- **Risks and decisions:** risks by level, owner, next step and due date, and decisions needed with who decides, when, and the outcome. **Look for predictable surprises** walks four areas (the outside world, customers and strategy, inside the team, politics) with prompts, plus a reminder to join up silos; anything you spot becomes a risk tagged with its area.
- **Metrics:** baseline, target, an optional outside benchmark with its source, and readings over time for each measure, with an on-target indicator. Starter metrics are cycle time, deployment frequency, change failure rate, escaped defects, meetings per week and meeting reschedule rate.
- **QA resources:** a manual test library anyone can follow (steps, expected result, owner, last result), test runs with pass, fail, blocked or skipped per case and failures sent to the dev-sync log, an inventory of automated suites (unit, Apex, MUnit, end-to-end) with coverage and latest result, regression plans for each Salesforce release and peak-season freeze with owner, backup and sign-off, and the definition of done.
- **Dev-sync log:** every question raised after standup, with its kind (question, offer to present, decision needed, idea, action), who raised it, experts, decision maker, owner, next action, due date, status, origin and private notes. Overdue items stand out, and the group-learning flag proposes a presentation. Rows switched onto the dev-sync board copy out with only their shareable columns, and Make an update drafts a short script for a recorded update on any row.
- **Change requests:** work that arrives mid-sprint, logged with its source, urgency, size and effect on the sprint goal; the sprint's capacity and unfinished stories beside it; a decision on Scrum's terms (swap, absorb, defer, reject, cancel the sprint) that moves the stories; a record of when the requester heard; a team policy; and scope change per sprint.
- **Group learning:** a schedule of short team presentations, fed by the dev-sync log and by teach/learn matches.
- **Vendors:** type, status, account contacts, support process, service promise, contract dates and renewal notice; commercial terms stay private. A private conversation log, open concerns with owners, and follow-ups that become dev-sync items.

**Reporting**

- **30/60/90 plans:** one plan per month for the first six months (add more for a finer step or a longer view), with a headline each and dates from the start date. Items are outcomes, actions, measures or things you won't change, each tagged with the listening-tour themes behind it. Early wins can be linked to the agreed outcome they serve and the behavior they start to change, with a flag on any that serve no outcome. Each can be scored with an early wins evaluation (four questions, 0 to 4 each), and candidates are ranked so you keep three or four. Each early win can be planned as a project with FOG LAMP (focus, oversight, goals, leadership, abilities, means, process), with a lead and team from People; change agents are marked on their pages, listed on First 90 days and offered first as project leads. A side panel shows which themes no item answers yet. Copy the outline as Markdown, or build a deck from it in the Comms studio.
- **Work log:** wins, progress, blockers, decisions, asks and what's next, noted as they happen, each for leadership, your manager or just you.
- **Weekly and sprint reports:** every date lands in its week, week in the role and sprint week (a two-week sprint has a week 1 and a week 2). A weekly report for any week, for leadership (exportable data only) or your manager, with a suggested overall color; a sprint report with the goal, points against commitment, what carried over, scope changes and each sprint week. Edit, copy, save, mark sent, or turn either into a short video script. Activity shows everything you moved forward in a week, with Add to log.

**Knowledge**

- **Architecture and tools:** one catalog of the systems we run and the tools we build with (what each is, how we use it, environments, stack, docs, owner, lifecycle, criticality, private known issues); the integrations between them, including the middleware they pass through; a system map drawn from those integrations; numbered architecture decision records; and plain-language guides in Markdown.
- **Business landscape:** the products, services and internal platforms your company offers, with owner, customers, systems, vendors and maturity; the organization as a tree of divisions, departments and teams with leaders and people; a private assessment for each, taken outside first (threats and opportunities, then the weaknesses and strengths that bear on them, sometimes called TOWS), with evidence, source and confidence, and a combined matrix. Link a weakness or strength to its threat or opportunity and Priorities pairs them up: blunt the threats you're weak against, pursue the opportunities you're strong for. Any point or priority can become a roadmap item or a risk.
- **Organizational alignment:** a diagnosis of how an area's strategic direction, structure, core processes and skills fit together, drawn as an open system with the outside players around it and climate and culture at the center. Each element has prompts, a Scrum lens (Scrum practices stall when structure and incentives fight them) and links to the Teams, RACI, SDLC, Agile coverage and Skills pages. Direction gets its own check: mission (what), vision (why) and strategy (how), what you won't do, four questions on customers, capital, capabilities and commitments, and tests for coherence, adequacy, how it was made and implementation (judged by what people do, not what they say). A verdict says whether the problem is in the direction or in how it's carried out, and suggests what to do: leave it, adjust it modestly now and plan bigger changes later, or raise questions so it gets re-examined. Mark where any two elements are out of step (the arrow turns red), pick the situation to see where to start (a turnaround starts with direction, a realignment with processes and skills), name the root cause, write the case to make when the fix sits above you, and keep the five traps in view. Private.
- **Escalation playbook:** systems with owner, first responder, backup, business contacts linked to People, and linked vendor, business-hours and out-of-hours escalation chains, severity levels, and an incident log whose follow-ups become dev-sync items.

**Coaching**

- **Guides:** an editable library for engineering leaders in seven themes, with a strong focus on the transition into a new role: mindset, assertiveness, learning fast, the manager relationship, early wins, managing yourself and earning trust, plus joining from outside, your mandate, leading change, leading upward, culture and trust, peer relationships, change mid-sprint, team leadership, agile practice, stakeholders, leading leaders and vendors. Each guide has what to do, what to watch out for, questions to ask yourself and things to try this week. Rewrite, delete or add guides, and note what inspired them.
- **Coaching where you work:** guidance isn't confined to the Coaching section. Each screen offers tips and links to the guides that fit what you're doing there, and every new section ships with its own.
- **Tips on every screen:** a short coaching tip at the top of each landing page in both apps, linking to a guide, edited per screen, hidden while presenting.
- **Reflection journal:** private prompts for each stage of the role, with energy and confidence over time.
- **Coaching packs:** share your guides, tips and prompts with other leaders (never your notes or reflections) and import theirs.

**Me**

- **My development:** learning goals with time logged and a report toggle that controls what reaches status reports, plus tasks, recurring obligations and your start date.
- **Problem preferences:** a self-assessment of which kinds of problems you're drawn to, across five areas (people, finance, product and customers, delivery and operations, engineering) and three kinds (technical, political, cultural). Totals that fall noticeably below your strongest are flagged as likely blind spots, each with guides to strengthen it and a plan to compensate (discipline, a backstop from People, or an advisor). Name your "hammer" too: the strengths that could misfire in a new role. Earlier ratings are kept to compare.
- **Advice network:** mark people as technical, political or personal advisors; My development shows the mix and flags when political counsel or personal advice is missing.

**Starter content:** one click loads a generic Agile adoption roadmap, the five common RACI decisions and the delivery metrics.

### Comms studio

**Messages**

- **This week:** messages due from your rhythms, drafts in progress and recently sent.
- **Messages:** draft, review, ready, sent and archived states, with a saved version on every edit and one-click restore.
- **Writing checks** that run as you type. Leftover placeholders block "ready"; jargon is flagged with a plainer word (built-in list plus your own glossary); long sentences and a missing opening summary get warnings.
- **Templates:** a starter kit of ten (weekly note, weekly status, alert, release notes, decision announcement, day-30 diagnosis, day-90 and quarterly review, team announcement, sprint review, video pitch), each with default audiences and channel.
- **Comms calendar:** rhythms (weekly, every two weeks, monthly, quarterly) that create due items with a start-drafting date and a one-click draft from the right template.
- **Sent log:** the exact text, channel, audiences and check results of everything marked sent.
- **Audiences and channels:** who needs what, at what level of detail, and where they usually hear it.
- **Exports:** copy as text, download Markdown or print to PDF, each logged.
- **Toolkit connection:** pull the toolkit's weekly status draft into a message, or build a deck from its 30/60/90 plans, over an export-only token.
- **Privacy:** drafts are private; sent messages are shareable.

**Presentations**

- **Deck builder:** a three-pane editor (slide list with drag to reorder, live reveal.js canvas, inspector) over slides stored as structured data.
- **Eleven layouts:** title, section break, one big number, points (optionally revealed one at a time), quote, comparison, image, video, audio, animation and closing.
- **Media players:** video and audio with trim start and end, loop, poster frame, captions, and play on entering the slide, on a click or only when pressed.
- **Lottie animations:** loop, play once, play on a click, speed and frame segments. The light player runs no expressions.
- **Versions and review:** save named versions, compare them slide by slide, restore one, and move a deck from draft to review to approved to presented, with each step saved. Approved decks are locked until you start a new draft; any saved version can be presented, and a deck can be copied for another audience.
- **Present:** full screen from the same renderer as the editor, with reveal.js's speaker view (notes, next slide, timer).
- **Media library:** uploads of video, audio, images, Lottie and WebVTT captions, with type checks, seekable playback, source and license recorded, and license details kept private.

**Visuals**

- **Images:** generate illustrations, slide backgrounds and thumbnails from a description through a local image service (FLUX.2 Klein on Apple Silicon by default), with a house style added to every prompt. Generated images are filed as such, with their prompt, model and seed.
- **Infographics:** big numbers, bars, timelines, steps, before and after, and progress, drawn from data rather than generated, so every word and number is exact. The local model can draft one from a request and the toolkit's facts; edit it with a live preview and export a crisp PNG to the media library.
- **Ask:** the same question box as the toolkit, with its own model settings.

## What's next

Headline items from the [backlog](BACKLOG.md), which lists everything planned in more detail:

- **Jira API sync:** read issue status and summary through a read-only Jira token so keys show live status, and import backlog, sprints and stories instead of pasting them.
- **MCP server:** expose the toolkit's search and lookup tools to local assistants and LLM clients, scoped like the existing API tokens.
- **Encrypted backups:** optional passphrase encryption of backup archives and a second backup location.
- **Guided tours:** a first-run tour per app and per-screen tours from the command palette, built on Driver.js (MIT) and bundled locally.
- **Accessibility pass:** a contrast check of every design token pair, screen reader labels, and focus order in dialogs.
- **Packaging for other managers:** a lighter install, a setup script, and export and import of practice packs, so other managers can run their own install without forking.
- **Timed sharing:** a read-only, presentable view shared on the same network or over Tailscale, with an access code, auto-timeout and a visit log.
- **Smarter Ask:** semantic search with local embeddings beside full-text search, streamed answers, and suggested questions on Today.

## Shared base (`src/beanagileorg/core`)

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

Styles come from one Tailwind CSS v4 source, `src/beanagileorg/core/static/app.src.css`: design tokens (light and dark), base styles and the shared components. The built `app.css` is committed, so running the apps needs no build step. After editing the source, rebuild with:

```bash
./scripts/build-css.sh
```

The script uses Tailwind's standalone CLI from `.tools/` (not committed). Icons are a Lucide subset (`scripts/build_icons.py`), and the font is Inter; both are vendored with their licenses. Press ⌘K in either app for the command palette, or ? for keyboard shortcuts.

## Commands

| Command | What it does |
| --- | --- |
| `beanagileorg toolkit` / `beanagileorg comms` | Run an app (localhost only; `--port` to change the port, `--reload` for development) |
| `beanagileorg backup all` | Back up every app and check each backup |
| `beanagileorg backups toolkit` | List backups and their check results |
| `beanagileorg verify FILE` | Check a backup without changing anything |
| `beanagileorg restore FILE --app toolkit` | Put a backup back (stop the app first) |
| `beanagileorg schedule [--write]` | Nightly backups with launchd (macOS) |
| `beanagileorg domain [--caddyfile]` | Local beanagile.org setup |

## Data

Data lives in `~/.beanagileorg/<app>/` (override with `BEANAGILEORG_DATA`). Nothing in this repository is real data; examples and samples are always marked `[Placeholder]`.

Both apps run on their own. An [Odysseus](https://github.com/odysseus-dev/odysseus) hub is optional: set `BEANAGILEORG_ODYSSEUS_URL` and `BEANAGILEORG_ODYSSEUS_TOKEN` and the apps use it for documents, local models and scheduled jobs.

## Development

```bash
uv run beanagileorg toolkit --reload   # restart on code changes
uv run pytest -q                       # the test suite, also run by CI on every push
```

## License

MIT. See [LICENSE](LICENSE). Odysseus is a separate AGPL-3.0 project; these apps only talk to it over its API and include none of its code.
