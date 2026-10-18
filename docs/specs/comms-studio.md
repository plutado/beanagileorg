# Comms Studio Spec

Design spec, October 2026. Parts are built (messages, templates, checks, media, images, infographics, Ask); the rest is still the plan. Example values are [Placeholder]s.

The Comms studio is the second supporting app beside the toolkit (and the optional Odysseus hub) on a work laptop, at comms.beanagile.org. It's where leadership messages are written and checked, presentations are built and rehearsed, and media is produced. It can read only the toolkit's exportable data.

## Shape of the app

Same stack and habits as the toolkit, so the suite is maintained one way: Python with FastAPI, SQLite and plain JavaScript, in Docker, matching Odysseus's look.

| Decision | Proposal |
| --- | --- |
| Address | comms.beanagile.org on the device, bound to localhost; no public record |
| Users | One: me |
| Sign-in | Local password and TOTP, or shared with the toolkit if that's settled |
| Storage | Its own SQLite file; media files in a folder on the encrypted disk |
| Toolkit link | `export:read` token only: exportable fields, never private ones |
| Odysseus link | API token for documents (publishing finished pieces to the docs library), calendar (the comms cadence) and local models (writing checks) |
| Sending | The studio doesn't send anything itself. It must also run without Odysseus, with the model-based checks switched off, for lighter installs. It produces the text, PDF or file, and I post it in Teams, email or wherever it goes, then mark it sent |

**Version 1** (by day 5, for the first weekly note to my manager): messages, templates, audiences, the comms calendar, the sent log and the plain-language check.

**Later:** presentations by day 30 (the diagnosis), the remaining writing checks by day 45 (the first weekly status), media projects by day 75 (the first highlights video), and the questions log and measures by day 90.

## Message lifecycle

*(Diagram in the original doc: message lifecycle · 8 steps, 1 gate.)*

A failed check sends the draft back for fixing; once it passes, I export and post it myself, the sent log keeps its facts, and any questions it raises shape the next message.

## Data model

The spine is the **Message**: everything else is a template for it, a fact it rests on, a check run on it, or a record of where it went. People appear only as audience groups and free-text names, because named-person records stay in the toolkit.

### Messages

| Entity | Key fields | Links |
| --- | --- | --- |
| Message | title, type (weekly note, weekly status, alert, release notes, stakeholder update, team announcement, memo), body, state (draft, in review, ready, sent, archived) | Template; Audiences; Channel; FactSnapshot |
| MessageVersion | body, saved at | One Message |
| FactSnapshot | taken at, the toolkit facts used (dates, red/yellow/green, owners, risks), which endpoints | One Message |
| CheckResult | check type, result (pass, warn, fail), findings, run at | One Message |
| SentLogEntry | sent at, channel, audiences, exported file | One Message |

### Shaping messages

| Entity | Key fields | Links |
| --- | --- | --- |
| Template | name, type, sections with placeholders and fact bindings, default audience and channel | Messages made from it |
| Audience | name, what they need, detail level, style (story-first or data-first), preferred channel | Messages; Questions |
| Channel | name (for example a Teams channel, an email list or a meeting), notes | Messages |

### Presentations and media

| Entity | Key fields | Links |
| --- | --- | --- |
| Deck | title, occasion, date, target length, state, theme, narrative template | Audience; Slides; Rehearsals |
| Slide | order, layout, content fields, reveal order, transition, animations placed, fact bindings, speaker notes, optional link to a toolkit meeting deck view | One Deck |
| Rehearsal | date, run time, notes | One Deck |
| MediaProject | title, kind (highlights video, walkthrough, explainer), stage, due, where it's published | Audience; MediaAssets |
| MediaAsset | kind (script, storyboard, shot list, footage, edit, captions, export), file path, version | One MediaProject |
| Theme | name, source (Envato Elements or my own), item link, license reference, template file path, colors, fonts | ThemeLayouts; Decks |
| ThemeLayout | slide type (title, section, big number, chart, quote, timeline, comparison, people, closing), the template layout it uses | One Theme |
| NarrativeTemplate | name, the arc's beats in order, the slide type suggested for each beat | Decks built from it |
| Animation | name, Lottie file path, source (mine or licensed), license reference, length, named segments | Slides that place it |

### Rhythm and feedback

| Entity | Key fields | Links |
| --- | --- | --- |
| Cadence | message type, rhythm (weekly, every two weeks, monthly, quarterly), day, lead time | Generates CommsDue items |
| CommsDue | due date, status (upcoming, drafted, sent, missed) | One Cadence; the Message that met it |
| Question | asked by (free text), date, question, answer, status | Audience; the Message that answered it |
| Measure and MeasureReading | name, method; date, value | Readings belong to a Measure |

## Screens

Ten screens. The home screen answers "what do I owe people this week", and the editor is where most time is spent.

| Screen | Purpose | Key actions |
| --- | --- | --- |
| This week | Messages due, drafts in progress, unanswered questions, upcoming presentations | Open a due item as a draft from its template |
| Message editor | Write a message with its facts and checks beside it | Pull fresh facts, run checks, compare versions, preview the export, mark ready, export, mark sent |
| Messages | Every message by type, audience and state | Filter, search, duplicate last week's |
| Templates | The template library | Edit sections, placeholders and fact bindings |
| Audiences and channels | The audience map from the communication plan | See what each audience heard recently and what's overdue for them |
| Presentations | The deck builder: slides, themes, Lottie animations, speaker notes and rehearsals | Outline, build slides, rehearse with a timer, export to PDF or PowerPoint, open the linked live view in the toolkit |
| Media | Production board for videos and explainers | Move a project through its stages; attach scripts, storyboards and files |
| Questions | Questions from stakeholders and their answers | Log a question, link the message that answered it |
| Measures | The communication plan's measures over time | Add a reading, such as survey results |

**Added October 2026:** an **Infographics** screen (draft from a request and the toolkit's facts, edit with a live preview, export a PNG), **image generation** inside the media library, and an **Ask** box with its own model settings. These are described in the sections below.

Presenting from the studio: everything except unsent drafts is meant to be seen, so on a shared screen the studio only hides drafts and the questions log's names.

## Templates

Ten starting templates, including a video pitch: the script beats (hook, the data, the proposal, what it means for you, the ask), on-screen notes, and the email to send with it. Each opens with its answer first, and fills its facts from the toolkit so dates and colors are never retyped.

| Template | Audience | Sections | Facts pulled in |
| --- | --- | --- | --- |
| Weekly note to my manager (first 30 days) | My manager | What I learned, what I'm watching, what I need | Listening-tour progress (counts only) |
| Weekly status | My manager, product, stakeholders | Overall color and one line, milestones, risks, decisions needed, shipped, next week, my development, asks and answers | Roadmap, milestones, risks, decisions, reportable learning goals |
| Risk or incident alert | My manager and whoever is affected | What happened or is at risk, impact, owner, what we're doing, time of the next update | The risk or incident's exportable summary |
| Release notes | Cloud users, other engineering teams | What changes for you, when, who to ask, link to the walkthrough video | Release date and items, once releases are tracked |
| Decision announcement | Whoever the decision affects | The decision, why, the tradeoff, who decided, what changes | The Decision record |
| Day-30 diagnosis | My manager | What I found, the top three problems, the plan for the next 60 days | Rollup themes with counts |
| Day-90 and quarterly review | My manager, leadership, department heads | Results against the scorecard, metrics, what's next, what we need | Metrics, roadmap, scorecard |
| Team announcement | The team | What, why, what it means for you, where to ask | None by default |
| Sprint review invite and recap | Stakeholders | Sprint goal, what we'll show or showed, link to the highlights video | Sprint goal and dates |

Every section in a template is written as a bracketed placeholder, such as `[Placeholder: one line on where things stand]`. A message can't be marked ready while any placeholder is left.

## Writing checks

Eight checks run on every draft before it can be marked ready. Most are plain rules; only the language suggestions use a model, and that model is local.

| Check | Looks at | Reports | Effect |
| --- | --- | --- | --- |
| Placeholders left | Any `[Placeholder` text still in the draft | Each one, highlighted | Blocks "ready" |
| One version of the truth | Dates, colors and owners in the text against the latest toolkit facts and what other audiences were told recently | Each mismatch, side by side | Blocks "ready" until fixed or I note why |
| No surprises | Red or at-risk items, slipped dates and overdue decisions the toolkit knows about | Anything relevant to this audience that the draft leaves out | Warns; I tick it off or add it |
| Stale facts | Age of the fact snapshot | How old it is | Warns past `[Placeholder]` hours; one click refreshes |
| Sensitive content | A private-terms list I keep, plus phone numbers and email addresses | Each hit | Blocks "ready" |
| Plain language | Words in the glossary or on a jargon list, long sentences | Each, with a plain alternative suggested by the local model | Warns |
| Summary first and length | The opening lines and word count against the audience's target | Whether the answer comes first; words over target | Hint |
| Questions answered | Open questions from this audience | Any the draft doesn't address | Warns |

Every check result is saved with the message, so I can show later what was checked before something went out.

## Reading from the toolkit

The studio reads from the toolkit and never writes to it. With an `export:read` token, the toolkit returns only exportable fields; the filter sits on the toolkit side, so a bug in the studio can't widen it.

| Toolkit endpoint | Used for |
| --- | --- |
| `/api/status/draft` | The weekly status skeleton |
| `/api/roadmap` and milestones | Dates and colors in status and reviews |
| `/api/risks`, `/api/decisions` | Alerts, decision announcements, the no-surprises check |
| `/api/metrics` | Reviews and the measures screen |
| `/api/learning-goals?reportable=true` | The "my development" line |
| `/api/rollup` (themes and counts only) | The day-30 diagnosis |
| `/api/sprints/current` (dates and goal only) | Sprint review invites and recaps |

**Fact snapshots.** Each draft records the facts it was written from, with the time. A sent message keeps its snapshot forever, so I can show what was true when it went out, even after the toolkit's records change.

**When the toolkit isn't running,** the studio still opens and edits drafts from their last snapshot. The stale-facts check flags them until a refresh.

## Presentations and media

Decks and videos follow fixed pipelines, so each one shows where it stands at a glance and nothing ships unrehearsed or uncaptioned.

**Deck pipeline:** outline, then slides, then speaker notes, then a timed rehearsal, then delivery, then the export kept with its date.

- An outline starts from the matching template's sections, so the day-30 diagnosis deck and its written version say the same thing.
- A slide can link to a live toolkit view, so in the meeting I can switch from a slide to the real roadmap or rollup in presentation mode.
- Rehearsals record run time against the target length, plus notes on what to cut.

**Media pipeline:** script, storyboard, shot list, recording, edit, captions, review, then internal publishing.

- Each stage holds its files (paths on the encrypted disk) and a due date. The board shows what's stuck.
- Captions are a required stage, not optional.
- Recordings of real work go through the same privacy rule as screens: shot in presentation mode, with no private fields on screen.
- Publishing means wherever the company lets videos be hosted internally, which is still to learn.

## Images and infographics

Built October 2026. Pictures and data visuals are made two different ways, because image models garble words and invent numbers.

- **Images** come from a local image service with an OpenAI-style API, such as a FLUX model served on the same machine. Four shapes: slide, video thumbnail, square, portrait. A house style is added to every prompt so images look like one family. Results land in the media library marked generated, with the prompt, model and seed. Subjects are the author, designed characters or animals, never a real colleague.
- **Infographics** are data the page draws: big numbers, bars, timeline, steps, before and after, and progress, in a 16:9 layout for slides. The local model can draft one from a request plus the toolkit's facts (weekly or sprint report, status, plans); anything it can't find comes back as \[Placeholder\], and every draft is checked against its template. Edit in a form with a live preview, save, and export a crisp PNG to the media library.
- **Later:** a brand palette setting, inserting images and infographics straight into deck slides, a chart template from Jira sprint data, and image edits and upscaling.

## Ask and AI drafting

The same Ask plumbing as the toolkit: any model (local Ollama by default, any OpenAI-compatible server, or Anthropic), set under Settings. A plain completion helper drafts structured content, such as infographics, from facts the studio supplies. The studio reads the toolkit only through its export-only token, so drafts are built from shareable data. A local model can be unloaded after each answer to share memory on a laptop.

## Video pitches and delivery

Video is the format for one-to-many updates: a two-to-four-minute pitch with a written summary, one ask and a respond-by date. The toolkit drafts scripts for dev-sync updates and for weekly and sprint reports; the video pitch template carries the beats. Delivery is planned in the [video message platform spec](video-message-platform.md): a gated share.beanagile.org site (a small Drupal site on a web host) with personal links, transcripts and private-by-default comments. Video generation itself is deferred: a hosted video service for short animated pieces, or ComfyUI on a rented GPU for anything custom.

## Themes and storytelling

Many stakeholders respond to a well-told, good-looking story more than to raw data, so generated decks start from professionally designed themes and a narrative structure, and the numbers serve the story.

**Themes from Envato Elements.** A template subscription such as Envato Elements is the main source of presentation designs.

- Templates are downloaded as PowerPoint where possible. The studio opens a template and fills its own slide layouts, so the design stays intact.
- Template files live in a local themes folder on the device and never go into the MIT repository, because the Envato license doesn't allow redistribution.
- Each template used is registered to the project in Envato Elements, and the theme record keeps the item link and license reference.
- A theme maps its layouts to the slide types the studio generates: title, section break, one big number, chart, quote, timeline, comparison, team or people, closing. A layout with no match falls back to a plain one in the theme's colors and fonts.
- The same theme's colors and fonts style the live HTML version of a deck, for presenting from the studio itself.

**Storytelling built in.**

- **Narrative templates** set the arc before any slide exists: situation, complication, resolution; what, so what, now what; or problem, options, recommendation.
- **Headline titles:** each slide's title states its point as a sentence, and a check flags titles that are only topics.
- **One idea per slide,** with numbers shown as one big figure or a simple chart rather than tables.
- **Audience style:** each audience is marked story-first or data-first. Story-first decks put detail in an appendix and speaker notes.
- **Speaker notes and rehearsal** carry the detail, so slides stay clean.

**HTML decks as a first-class format.** Live decks are built with JavaScript and HTML, not just exported from PowerPoint:

- **reveal.js** (MIT) is the deck engine: slides as HTML, a speaker notes view, step-by-step reveals, animated transitions between slides, and PDF export.
- **lottie-web** (MIT) plays Lottie animations, such as vector motion exported from After Effects, for animated titles, diagrams and transitions.
- Charts are drawn as simple SVG from the toolkit's facts, so they animate in and stay sharp at any size.
- Libraries are bundled locally with their licenses, not loaded from a CDN, so decks work offline on the device. Lottie files I didn't make myself stay in the local themes folder, like the templates.
- Theme colors and fonts from the Envato template style the HTML deck, so both formats look like one design.

**Export.** PowerPoint built on the Envato template, the HTML deck (presented live or saved as a single file), and a PDF of either.

## Deck builder

An interactive editor inside the Comms studio for building presentations visually. reveal.js renders every slide and lottie-web plays every animation, so the editing preview, the live presentation and the export are the same thing.

**The editor, three panes:**

| Pane | What it does |
| --- | --- |
| Slide list | Thumbnails in order; drag to reorder, duplicate, hide, group into sections |
| Canvas | The current slide, live in the chosen theme, at presentation size; click any element to edit it in place |
| Inspector | Layout, content fields, data binding, animation and transition settings, speaker notes |

**What a slide is made of.** Each slide is structured data, not free-form HTML: a layout from the theme (title, section, big number, chart, quote, timeline, comparison, people, closing) plus its fields. One renderer turns that data and the theme into reveal.js HTML, so every slide stays on-theme and can also be exported to the PowerPoint template.

**Animation with Lottie:**

- An animation library holds Lottie files: my own exports from After Effects, or licensed ones kept in the local themes folder.
- Place an animation on a slide, then set when it plays (on entering the slide, on a click step, or looping), its speed, and which segment to play.
- Text, charts and images can also come in step by step using reveal.js reveals, in an order set in the inspector.
- Transitions between slides, including reveal.js's automatic animation of elements that appear on consecutive slides.

**Story and data aids:**

- **Outline first:** pick a narrative template and the builder creates the skeleton slides, one per story beat, ready to fill.
- **Live numbers:** a big-number or chart element can be bound to toolkit facts. It uses the message's fact snapshot and refreshes on request.
- **Headline check:** flags slide titles that are topics rather than points, with a local-model suggestion.
- **Custom slide:** for the occasional slide that needs it, a block of my own HTML and CSS, rendered in a sandbox so it can't break the deck.

**Video and audio:**

- Video and audio elements sit on a slide like any other, playing local files from the device.
- Player controls on the slide and in the speaker view: play, pause, scrub, volume and mute.
- Set a start and end point to play just a clip, a poster frame to show before it plays, and whether it loops.
- Choose when it plays: on entering the slide, on a click step, or only when I press play.
- A captions track can be attached to any video and is on by default.
- The media library tracks each file's source and license, and links to the media production board, so a finished highlights video can drop straight into a deck.

**Presenting:** present full screen from the builder with reveal.js's speaker view (notes, next slide, timer), and rehearsal runs logged with their time.

**Export:** a single self-contained HTML file for offline presenting, a PDF, and PowerPoint on the Envato template, where Lottie animations become a still frame.

## Open questions

- [ ] Confirm the toolkit's exportable tags cover what the studio needs (rollup themes and counts, sprint dates and goals were added to the toolkit spec for this)
- [ ] Video hosting: the plan is a gated share.beanagile.org (see the video message platform spec). Confirm whether a company video platform should be used for some audiences, and which recording and editing tools I'll use
- [ ] Shared sign-in with the toolkit, or separate
- [ ] Whether the studio should ever post to Teams or email directly, or always hand me the text to post
- [ ] Target lengths per audience for the summary-first check
- [ ] How long sent messages and their snapshots are kept, and what happens to them when the role ends
- [ ] Which Envato Elements templates to start with: one theme for leadership reviews, one for team-facing decks
