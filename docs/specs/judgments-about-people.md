# Judgments about people

Much of what a manager keeps in the toolkit is personal judgment: who is trustworthy, who resists a change, who is close to whom, who might leave. Some of it is personal information: health, family, pay. It helps the manager lead, but shared with another manager it can be unfair to the person, who never sees it or gets to answer it, and it can breach HR policy or privacy law. This spec lists where that data lives and how the toolkit keeps it in.

## Where it lives

| Area (screen) | What it holds | Risk if shared | Safeguard |
| --- | --- | --- | --- |
| People: stance, influence, opinion leader, power sources, change style, change agent, key person | Your read of each person's position and pull | Political labels that follow someone | Never leaves |
| People: motivations, personal context, things to remember, key dates, support notes, goals, contact | Personal and sometimes sensitive information | Privacy, health or family details | Never leaves |
| People: offer them, need from them, expects from me, advice, insight, communication | Relationship strategy | Reads as manipulation out of context | Never leaves |
| People: working style, tags, background | Impressions, labels, career history | Labels travel further than the note behind them | Roster export only, after a warning you confirm |
| Listening tour interviews | What people said, how they answered, what went unsaid | Breaks confidence | Never leaves |
| One-on-ones and interactions, manager notes, commitments, growth goals, mentoring | Private conversations and feedback | Breaks confidence; HR records | Never leaves |
| Team assessments, assessments, first-90 milestones | Your evaluation of each person | Performance judgments outside any HR process | Never leaves |
| Culture observations and reads, trust pulses, alignment checks | Your read of the culture and of named people in it | Blame and reputation | Never leaves |
| Influence links, coalitions, alliance plans | Who influences whom, who blocks | Political mapping of colleagues | Never leaves |
| Reflections, preferences, behavior targets, criteria, conversations with your manager, learning questions | Your own private reflection | Your own privacy | Never leaves |
| Risks, decisions, Scrum of Scrums items, core processes (shareable kinds) | Facts about work, but free text can name or describe a person | A "risk" that is really a judgment of someone | Scanned: flagged wording needs a second look |
| Risks filed under politics | Often about people | As above | Shown as a note |

## How it's kept in

1. **Whole kinds never leave.** The list lives in one place (core/sensitivity.py). No pack kind may use one of these tables, the app refuses to start if one does, and a test checks every listed table exists.
2. **Person fields never leave.** The roster export can't include them, and the app refuses to start if it tries. Support notes were taken out of the roster's private fields because they can hold health or personal context.
3. **Caution fields need a confirmation.** Exporting a roster with private fields first lists the people whose working style, tags or background would go, and asks you to confirm. The server refuses without that confirmation.
4. **Free text is scanned.** Before a pack goes, every value is checked for wording that sounds like a judgment of a person ("can't be trusted", "resistant", "low performer"), touches on employment or pay ("PIP", "flight risk", "resigned"), or is personal information ("sick leave", "divorce"), and for the names of people you hold. The review lists each finding by record and field, with a Leave it out button. Copy and Download ask you to confirm, and the server refuses the export without it. The export log notes how many cautions were confirmed.
   - **Second look** (must be confirmed): personal or employment wording anywhere, or judgment wording in a record that names or links a person.
   - **Note** (shown only): a person named in free text, judgment wording with no person in sight, or a risk filed under politics.
5. **The importer opts in.** The same scan runs on import. Flagged records start as Skip (or Keep mine), carry a "second look" mark, and applying them asks for confirmation.

The scan looks at wording, not meaning: it will miss some things and flag harmless ones. It's a prompt to think, backed by the coaching guide "Facts, not judgments, when you share about people".

## Everywhere else text leaves

6. **Copy, download and print.** Every Copy button for text (reports and the status draft, plans and check-ins, mandate documents, the Scrum of Scrums, dev-sync, sprint and debt summaries, agendas, release notes, onboarding plans) and Comms studio's copy, download and print run the same scan, a paragraph at a time, so a name in one paragraph and a judgment word in another don't add up. Only a second-look finding asks; a note doesn't interrupt.
7. **Comms studio drafts.** An "About people" writing check shows the same findings as you write. It warns and never blocks.
8. **Rosters coming in.** An incoming roster's working style, tags and background are listed before import; you bring them in or leave them out. Support notes, stances and other judgment fields never come in, even from an older file that carried them.
9. **Ask with a cloud model.** With private data allowed, judgments about people are still held back (search, lookups and summaries alike) unless a second box is ticked. A question that sounds like a judgment about someone asks before it's sent.
10. **Your own words.** Settings → Words that need a second look adds terms (a trailing * matches any ending) to every check above. Your words always ask.

## Tokens, the hub and records you mark

11. **API tokens never carry judgments.** Whatever its scope, a token (how the hub, LLM clients and the other app read the data) never receives judgment records, the person fields that record judgment, or records marked never share. Record reads filter them out; the screens that are about people (a person's CRM page, agenda and timeline, culture overview, team assessment, mentoring overview, preferences, the reflect page, the learning-questions agenda) refuse tokens; Today and Activity leave those parts out. A token gets them only with the judgments:read scope, which asks for confirmation when you create it. A test plants a marker in every judgment record and field, calls every read and export endpoint with a full-access token, and fails if the marker comes back.
12. **Never share, per record.** Risks, decisions, Scrum of Scrums items, core processes, metrics, SDLC policies, regression plans, role templates, dev-sync items, change requests, tech debt and team changes carry a never share? toggle beside their name. A marked record is private whatever its fields say: hidden while presenting, left out of the weekly report, the status draft, the Scrum of Scrums summary, the dev-sync board, release notes, the tech debt summary and the SDLC document, never offered in a pack, and never read by a token or a cloud model. You still see it.

One rule underneath: a reader marked "guarded" (a token, or a cloud model with private access) skips judgments about people and never-share records, wherever records are read.
