"""What each section is for and how to use it, shown at the top of each landing page and on the Help page.

Plain, short and practical. Every navigation entry in both apps has an entry here (a test checks this).
"""

from fastapi import APIRouter, Depends

from .privacy import Viewer

TOOLKIT = {
    "/today": {
        "purpose": "Your starting point each morning: everything that needs you today or this week, pulled from the rest of the toolkit.",
        "steps": ["Clear anything overdue first.", "Mark tasks and obligations done right here.", "Follow a link to deal with an item in its own section.",
                  "Ask a question in plain words at the top; the answer comes from your own data, with links to the records it used."],
        "privacy": "Private. Hidden while presenting.",
        "related": ["/me", "/dev-sync", "/onboarding"],
    },
    "/people": {
        "purpose": "Your private CRM for everyone you work with: team members, peers, stakeholders and vendor contacts. What matters to each person, every conversation, follow-ups, and who reports to whom.",
        "steps": ["Add each person with their title and relationship; set who they report to, and an Org chart builds itself.",
                  "Log one-on-ones, meetings and calls on their Conversations tab, with notes, takeaways and follow-ups that can go to the dev-sync log.",
                  "Set a check-in cadence; anyone past it shows on Today. Check Before you meet on their Overview for your last notes and open follow-ups.",
                  "Track commitments both ways on anyone's Overview: what you owe them and what they owe you.",
                  "Pick your own record ('This is me'); your direct reports get a Manager tab with growth goals, a feedback and wins log, and a drafted one-on-one agenda.",
                  "Choose which fields you use under Fields. Sensitive notes stay masked until you click Show.",
                  "Check Balance to see how your conversations split up, down and sideways, and which peers have gone quiet. Note what you can offer each peer."],
        "privacy": "Only names, titles, departments and reporting lines show while presenting; notes and conversations are private.",
        "related": ["/listening", "/teams", "/coaching/one-on-ones"],
    },
    "/culture": {
        "purpose": "Keep trust, safety and your own standards in front of you: what you notice in the culture, how the team feels, how you're living your standards, and what the team has agreed.",
        "steps": ["Write your standards under My standards (or start from suggestions). One shows on Today each day.",
                  "Under Noticing, log what you see: intimidation, chaos from missing process, quiet voices, and good moments too.",
                  "Concerns on your team still at 'not yet' after a week show on Today, as do follow-up dates.",
                  "Take a trust pulse every couple of weeks, from your own read or a team survey, and watch the trend.",
                  "Agree team agreements together, show them at retros, and fill in the Role brief so the mandate stays in view."],
        "privacy": "Only agreed team agreements show while presenting; everything else is private.",
        "related": ["/people", "/retros", "/coaching/calling-out-harm"],
    },
    "/changes": {
        "purpose": "Handle work that arrives in the middle of a sprint: record the request, judge it against the sprint goal, decide with the product owner, adjust the sprint, and tell the requester.",
        "steps": ["Log each request as it arrives: what, who asked, why it matters, how urgent and roughly how big.",
                  "Open it to see the sprint's capacity, what's done and the unfinished stories that could come out.",
                  "Decide with the product owner: swap work out, absorb a small one, defer it to the backlog, reject it, or cancel the sprint if the goal no longer makes sense.",
                  "Applying the decision moves the stories: swapped-out work goes back to the backlog and accepted work joins the sprint.",
                  "Mark when the requester was told. Scope change per sprint feeds the sprint report and the retro."],
        "privacy": "Titles, sources, decisions and points can go in leadership reports; descriptions and who asked show only to your manager or you; notes are private.",
        "related": ["/planning", "/status", "/coaching/change-mid-sprint"],
    },
    "/first90": {
        "purpose": "Your first 90 days, each new hire's, and the team you inherit, side by side by day: for them it's the first 90 days with a new manager who is bringing change.",
        "steps": ["Set your start date in Settings and pick your own record under People, so the team and the day count are known.",
                  "Give your inherited team their milestones: first one-on-one, career conversation, growth goal, feedback both ways, a day-90 check-in.",
                  "Write 'Working with me' and share it in week one: how you work, what you've been asked to do, what you'll change and protect.",
                  "Add each change you're bringing. Announce it, try it for a set time, review it with the team, then keep or drop it.",
                  "Hold check-ins at days 30, 60 and 90: a trust pulse, what you heard, and what changed because of it.",
                  "Under Mandates, write down what your role is for, what it must deliver and what you can decide, then agree it with your manager. Do the same with each report.",
                  "Diagnose each area's situation, keep a learning agenda of what to find out and from whom, and track the managers you mentor. Momentum shows on the overview."],
        "privacy": "Working with me and the team changes can be shown while presenting; milestones, check-in notes and your own track are private.",
        "related": ["/onboarding", "/plans", "/coaching/leading-change"],
    },
    "/onboarding": {
        "purpose": "Bring new team members in smoothly, with a checklist that runs from the week before they start to day 90.",
        "steps": ["Load the starter checklist, then edit the template under Checklist template.", "When someone joins, add them under People, then build their checklist with their start date, buddy and tracks.",
                  "Tick items off as they're done; your own items show on Today.", "Copy the checklist to send it to them."],
        "privacy": "Checklists are shareable; your notes on how it's going stay private.",
        "related": ["/people", "/sdlc", "/coaching/earning-trust"],
    },
    "/skills": {
        "purpose": "See who knows what across the team, and match people who can teach with people who want to learn.",
        "steps": ["Fill in skills, can teach and wants to learn on each person's profile.", "Check the matrix for gaps and single points of failure.",
                  "Turn a teach-and-learn match into a group learning session."],
        "privacy": "Counts show while presenting; who knows what stays private.",
        "related": ["/people", "/learning"],
    },
    "/listening": {
        "purpose": "Run your listening tour: one record per one-on-one, with the same four questions every time so you can compare answers.",
        "steps": ["Plan a one-on-one with each person.", "Afterwards, record what's working, what's frustrating, what to change first and what not to change.",
                  "Tag themes and systems as you go; they feed the day-30 rollup."],
        "privacy": "Private end to end. Only theme counts are ever shared.",
        "related": ["/rollup", "/plans", "/coaching/learn-fast"],
    },
    "/rollup": {
        "purpose": "What the listening tour is telling you: themes ranked by how often they come up, with quotes, gaps, opportunities and the things not to change.",
        "steps": ["Check it as one-on-ones finish.", "Use the themes to shape your 30/60/90 plans.", "Copy it as Markdown for your written diagnosis."],
        "privacy": "Quotes and names are private; theme counts can be shown.",
        "related": ["/listening", "/plans"],
    },
    "/teams": {
        "purpose": "Your team and the teams around it: who's on each, who leads it, its Jira project and board, its current sprint and goal, and a dated status.",
        "steps": ["Rename My team and fill in its members, product owner and Scrum Master.", "Add the other teams you work with or oversee, with their contacts and Jira project.",
                  "Update each team's status in a line when you hear how they're doing; it's stamped with the date.",
                  "With more than one team, a team picker appears on delivery screens to filter by team."],
        "privacy": "Teams can be shown on screen; private notes stay private.",
        "related": ["/sos", "/people", "/coaching/scrum-of-scrums"],
    },
    "/sos": {
        "purpose": "The Scrum of Scrums log: questions, dependencies, decisions, risks, impediments and knowledge that cross team lines, each with stakeholders, an owner, the outcome expected and a date.",
        "steps": ["Log each cross-team item with the teams involved, its stakeholders, an owner, the outcome or deliverable, and a due date.",
                  "Start a meeting to walk every open item, update them in the log, and write a short summary.",
                  "Record the resolution when an item is settled.", "Copy the leadership summary for the layer above."],
        "privacy": "Items and meeting summaries can be shared; private notes stay private.",
        "related": ["/teams", "/pi", "/coaching/scrum-of-scrums"],
    },
    "/sdlc": {
        "purpose": "How work moves from idea to production: the stages, when each starts and is done, the environments, and the policies the team has agreed.",
        "steps": ["Load the starter SDLC, then replace every [Placeholder] with how your team really works.", "Agree policies with the team and mark them agreed with the date.",
                  "Copy the whole SDLC as Markdown to share it; new members are linked to it from onboarding."],
        "privacy": "Shareable, except private notes.",
        "related": ["/qa", "/onboarding", "/raci"],
    },
    "/planning": {
        "purpose": "Plan each sprint beside Jira: the backlog of candidate stories, refinement until they're ready, estimating together, and pulling stories in against the team's real capacity.",
        "steps": ["Paste stories from Jira (key and title, one per line) into the Backlog, in priority order.",
                  "Refine each one: the story, acceptance criteria, technical notes and dependencies, checked against the definition of ready.",
                  "Estimate together; a wide spread of votes means talk it through and vote again.",
                  "In Plan a sprint, set availability and the goal, pull ready stories up to capacity, commit, then copy the plan back to Jira. Close the sprint to record what got done and carry the rest over."],
        "privacy": "Stories and plans can be shown on screen; private notes stay private.",
        "related": ["/sprints", "/pi", "/debt", "/coaching/refinement-and-estimation"],
    },
    "/sprints": {
        "purpose": "Your private notebook for each sprint: what happened in each ceremony, what you noticed, and the follow-ups that came out of it.",
        "steps": ["Start the next sprint with its goal and dates.", "Write a note after each ceremony using the prompts.", "Turn follow-ups into dev-sync items; open ones carry into the next sprint."],
        "privacy": "Sprint goals and dates are shareable; the notes are private.",
        "related": ["/retros", "/dev-sync", "/coaching/ceremonies"],
    },
    "/retros": {
        "purpose": "Run retrospectives the team can see: points by column, votes, and commitments to change, each tagged to the sprint it came from.",
        "steps": ["Start a retro for the sprint and pick a format.", "Open by reviewing earlier commitments: done, in progress or dropped.",
                  "Add points, vote, and turn the top ones into commitments with an owner and date.", "Watch recurring topics; a repeat means the last fix didn't work."],
        "privacy": "Built to show on screen during the retro. Keep your own impressions in the sprint notebook.",
        "related": ["/sprints", "/coaching/retros"],
    },
    "/pi": {
        "purpose": "Plan a Program Increment if your organization runs SAFe: objectives, features, stories, dependencies, milestones and risks on one board.",
        "steps": ["Create the PI and assign its sprints in the sprint notebook.", "Add objectives with business value, then features and stories in each sprint, each with its Jira key.",
                  "Check capacity per sprint, log dependencies and risks, and record the confidence vote."],
        "privacy": "Built to present; only risk notes are private.",
        "related": ["/sprints", "/roadmap", "/coaching/scrum-of-scrums"],
    },
    "/roadmap": {
        "purpose": "Your Agile adoption roadmap: what you'll introduce and when, by day of your contract.",
        "steps": ["Load the starter roadmap or add your own items.", "Set your start date in My development to turn days into dates.", "Update status as items land; it feeds the weekly status."],
        "privacy": "Shareable.",
        "related": ["/status", "/plans", "/coaching/introducing-scrum"],
    },
    "/raci": {
        "purpose": "Who is responsible, accountable, consulted and informed for the decisions that matter.",
        "steps": ["Load the five common decisions or add your own.", "Edit the roles to match your organization.", "Fill each cell; aim for exactly one accountable person per decision, then confirm each row with the people in it."],
        "privacy": "Shareable.",
        "related": ["/sdlc", "/qa", "/coaching/saying-no-to-scope"],
    },
    "/debt": {
        "purpose": "A register of technical debt, classified by what fixing it buys (stability, performance, revenue, observability and more), so you can weigh it against business priorities with leadership.",
        "steps": ["Log each item with its categories, what leaving it costs the business, and impact, risk and effort.", "Use Value and effort to find quick wins and to question money pits.",
                  "Agree a standing share of sprint capacity under Policy, and record each fix-now, schedule or accept decision with a date to revisit.",
                  "Copy the Leadership summary for priority conversations."],
        "privacy": "The register and summary are shareable; private notes and evidence stay private.",
        "related": ["/architecture", "/risks", "/coaching/tech-debt-case"],
    },
    "/risks": {
        "purpose": "Keep risks and pending decisions visible, with an owner, a next step and a date.",
        "steps": ["Log a risk with its level, owner and next step.", "Log decisions you need from others, with who decides and by when.", "Record the outcome when a decision is made."],
        "privacy": "Risks and decisions are shareable; notes are private.",
        "related": ["/status", "/coaching/your-manager"],
    },
    "/metrics": {
        "purpose": "Track a few delivery measures over time, with a baseline and a target, to see whether changes are working.",
        "steps": ["Load the four starter metrics or add your own.", "Record a baseline before setting a target.", "Add readings regularly and look at the trend, not single numbers."],
        "privacy": "Shareable.",
        "related": ["/status", "/coaching/metrics-without-blame"],
    },
    "/qa": {
        "purpose": "Everything about testing: manual test cases, test runs, automated suites, regression plans and the definition of done.",
        "steps": ["Write smoke and regression tests in the Test library.", "Start a run after a deploy, mark each case, and send failures to the dev-sync log.",
                  "Record automated suites and their latest results.", "Plan regression for each platform release and peak-season freeze."],
        "privacy": "Shareable; run and suite notes are private.",
        "related": ["/sdlc", "/architecture", "/coaching/quality-culture"],
    },
    "/dev-sync": {
        "purpose": "Track every question and problem raised after standup until it's resolved, with an owner, a next action and a date.",
        "steps": ["Add an item when something comes up in standup or anywhere else.", "Give it an owner, next action and due date, and the Jira keys it relates to.", "Close it when it's done; overdue items show on Today.",
                  "Note the kind (question, offer to present, decision needed), the experts and the decision maker.",
                  "Put rows on the dev-sync board to share them; Make an update drafts a short script you can record, then link the update on the row."],
        "privacy": "Items are presentable; private notes stay private.",
        "related": ["/today", "/learning", "/coaching/earning-trust"],
    },
    "/learning": {
        "purpose": "A schedule of short team presentations, so people share what they know.",
        "steps": ["Accept proposals from the dev-sync log and the skills matrix.", "Schedule a date and presenter.", "Mark it done afterwards."],
        "privacy": "Shareable.",
        "related": ["/skills", "/dev-sync"],
    },
    "/vendors": {
        "purpose": "A light CRM for vendors and contractors: contacts, support process, contracts, a conversation log and open concerns.",
        "steps": ["Add each vendor with contacts, support process and contract dates.", "Log conversations and turn follow-ups into dev-sync items.", "Track concerns with an owner and date; renewals show on Today."],
        "privacy": "Commercial terms, notes and conversations are private.",
        "related": ["/escalation", "/coaching/vendor-partnerships"],
    },
    "/plans": {
        "purpose": "Your 30/60/90-day and six-month plans, built from the listening tour and ready to present.",
        "steps": ["Write a headline for each month.", "Add outcomes, actions, measures and what you won't change, tagged with the themes behind them.",
                  "Check What I heard for themes no item answers yet.", "Copy the outline, or build a deck from it in the Comms studio, and mark the plans presented."],
        "privacy": "Plans are shareable; your evidence notes are private.",
        "related": ["/rollup", "/status", "/coaching/your-manager"],
    },
    "/status": {
        "purpose": "Weekly and sprint reports drafted from what you log each day and what you update in the toolkit, for leadership or for your manager.",
        "steps": ["Log wins, progress, blockers, decisions, asks and what's next as they happen, from Today or the Work log, and pick who each one is for.",
                  "Each entry and update lands in its week and sprint week: a two-week sprint has a week 1 and a week 2.",
                  "Open the Weekly report, pick the week and the audience, read the draft and edit it; then copy it or save it as sent.",
                  "At the end of a sprint, the Sprint report shows the goal, points done, what carried over and each week of the sprint.",
                  "Check Activity for anything you moved forward but didn't log, and add it to the log in your own words.",
                  "Video script turns any weekly or sprint report into a short narrated script to record."],
        "privacy": "Leadership reports use only exportable data and entries marked for leadership; your manager's report can also use entries marked for them. Just-me entries and Activity stay private.",
        "related": ["/sprints", "/risks", "/coaching/honest-status"],
    },
    "/architecture": {
        "purpose": "How your systems and tools fit together: a catalog, the integrations between them, a system map, decision records and guides.",
        "steps": ["Add each system and tool with what it is, who owns it and how you use it.", "Add integrations, including the middleware they pass through; the map draws itself.",
                  "Record significant technical decisions, and write guides that explain how things work."],
        "privacy": "Shareable, except known issues and integration notes.",
        "related": ["/escalation", "/qa", "/landscape"],
    },
    "/landscape": {
        "purpose": "The business you support: products and services, the organization by department, and an honest assessment of strengths, weaknesses, opportunities and threats.",
        "steps": ["Add products and services with owner, customers and systems.", "Build the organization tree and place people in it.",
                  "Assess each offering and department with evidence and a confidence level; turn points into roadmap items or risks."],
        "privacy": "Structure can be shown; the assessment is private and never exported.",
        "related": ["/architecture", "/coaching/read-the-situation"],
    },
    "/escalation": {
        "purpose": "Who to call when something breaks: systems with owners and backups, escalation chains, severity levels and an incident log.",
        "steps": ["Add each system with owner, first responder and backup.", "Set business-hours and out-of-hours escalation steps.", "Log incidents and turn follow-ups into dev-sync items."],
        "privacy": "Shareable, except vendor support details.",
        "related": ["/architecture", "/vendors", "/coaching/psychological-safety"],
    },
    "/coaching": {
        "purpose": "Guides, tips and reflection for leading well, especially through a new or growing role. Everything here is yours to edit.",
        "steps": ["Browse guides and mark the ones you're working on.", "Rewrite or delete what doesn't fit, and write your own as you read.",
                  "Use Reflect each week to note what you're learning and how you're doing.", "Edit the tips that appear on each screen under Tips and prompts."],
        "privacy": "Guides and tips are shareable as a pack; your notes, focus and reflections are private.",
        "related": ["/me", "/coaching/reflect"],
    },
    "/me": {
        "purpose": "Your own development and workload: learning goals with time logged, ad hoc tasks, recurring obligations and your contract start date.",
        "steps": ["Set your start date; it turns day numbers into dates across the toolkit.", "Set your Jira address, so every Jira key in the toolkit becomes a link.", "Add learning goals and log time; tick 'show in report' for goals leadership should see.",
                  "Track tasks and obligations; they show on Today."],
        "privacy": "Private, except learning goals you choose to report.",
        "related": ["/today", "/coaching"],
    },
    "/settings": {
        "purpose": "Sign-in, API tokens, coaching tips, backups and the history of changes and exports.",
        "steps": ["Turn on an authenticator for sign-in.", "Create a token with the least access it needs.", "Back up now, or check that nightly backups are passing."],
        "privacy": "Hidden while presenting.",
        "related": [],
    },
}

COMMS = {
    "/this-week": {
        "purpose": "What you need to send this week: messages due from your rhythms, drafts in progress and what you sent recently.",
        "steps": ["Start a draft from anything due.", "Finish drafts in progress.", "Check what went out recently."],
        "privacy": "Drafts are private.",
        "related": ["/calendar", "/messages"],
    },
    "/messages": {
        "purpose": "Write, check and send leadership messages, with a saved version on every edit.",
        "steps": ["Start from a template or a blank message.", "Fix what the writing checks flag; leftover placeholders block 'ready'.",
                  "Pull in the toolkit's weekly status if it helps.", "Mark it sent to keep the exact text in the sent log."],
        "privacy": "Drafts are private; sent messages are shareable.",
        "related": ["/templates", "/sent", "/plain-language"],
    },
    "/templates": {
        "purpose": "Reusable starting points for the messages you send often, each with default audiences and channel.",
        "steps": ["Start from the built-in templates.", "Edit them to match how you write.", "Add your own for messages you repeat."],
        "privacy": "Shareable.",
        "related": ["/messages", "/calendar"],
    },
    "/calendar": {
        "purpose": "Your communication rhythm: weekly, fortnightly, monthly and quarterly messages that create due items ahead of time.",
        "steps": ["Add a rhythm for each regular message.", "Pick its template and audiences.", "Due items appear on This week with a start-drafting date."],
        "privacy": "Shareable.",
        "related": ["/this-week", "/templates"],
    },
    "/sent": {
        "purpose": "A record of exactly what went out: text, channel, audiences and check results.",
        "steps": ["Look up what you told whom, and when.", "Check what a message said before you follow up on it."],
        "privacy": "Shareable.",
        "related": ["/messages"],
    },
    "/audiences": {
        "purpose": "Who needs what, at what level of detail, and where they usually hear it.",
        "steps": ["Add each audience with the detail they want.", "Add channels and how each is used.", "Pick them on templates and messages."],
        "privacy": "Shareable.",
        "related": ["/templates", "/messages"],
    },
    "/plain-language": {
        "purpose": "Keep messages plain: the jargon list the writing checks use, with a plainer word for each.",
        "steps": ["Review the built-in list.", "Add words your organization overuses.", "The checks flag them as you type."],
        "privacy": "Shareable.",
        "related": ["/messages"],
    },
    "/decks": {
        "purpose": "Build and present HTML slide decks with a live editor, media and animations, with versions and a review workflow.",
        "steps": ["Start a deck, load the placeholder deck, or build one from the toolkit's 30/60/90 plans.", "Add slides from the eleven layouts and edit them in the inspector.",
                  "Open Versions to save a version with a note, compare it with now, or restore it; send the deck for review, approve it, and mark it presented. Approved and presented decks are locked until you start a new draft.",
                  "Present full screen, with speaker notes in the presenter view, or present any saved version while you draft the next one. Make a copy to adapt a deck for another audience."],
        "privacy": "Shareable.",
        "related": ["/media"],
    },
    "/infographics": {
        "purpose": "Clear, accurate infographics for messages and decks: big numbers, bars, timelines, steps, comparisons and progress, drawn from your data so every word and number is exact.",
        "steps": ["Describe what it should show, and pick facts from the toolkit (the weekly or sprint report) if you want the numbers filled in.",
                  "The model drafts it; check every number against the facts and edit anything in the form.",
                  "Save it, then export a PNG into the media library for slides, email and video thumbnails."],
        "privacy": "Built from the export-only toolkit connection, so only shareable data reaches it.",
        "related": ["/media", "/decks", "/messages"],
    },
    "/media": {
        "purpose": "Your library of video, audio, images, animations and captions for decks.",
        "steps": ["Upload a file and record where it came from and its license.", "Or generate an image from a description with the local image service; it's filed as generated, with its prompt.", "Use it in a deck slide."],
        "privacy": "License details are private.",
        "related": ["/decks"],
    },
    "/connections": {
        "purpose": "Connect the Comms studio to your toolkit, so it can pull the weekly status, your plans and your coaching tips.",
        "steps": ["In the toolkit's Settings, create a token with the export:read scope only.", "Paste it here with the toolkit's address.", "Test the connection."],
        "privacy": "The token can only ever read shareable data.",
        "related": ["/messages", "/decks"],
    },
    "/settings": TOOLKIT["/settings"],
}

HELP = {"toolkit": TOOLKIT, "comms": COMMS}


def router_for(app: str) -> APIRouter:
    from .app import get_viewer  # imported here to avoid a circular import

    router = APIRouter()

    @router.get("/api/help")
    def help_text(viewer: Viewer = Depends(get_viewer)):
        return HELP.get(app, {})

    return router
