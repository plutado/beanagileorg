"""Starter coaching content: guides for engineering leaders, short tips for each screen, and reflection prompts.

This is a first draft meant to be edited. The toolkit copies it into its database once, where it can be changed,
deleted or added to; after that this file is only used to restore a built-in guide, or as the Comms studio's
fallback tips when it isn't connected to the toolkit. The text is original to beanagileorg (MIT). Books are named
as further reading only; nothing is quoted from them.
"""

THEMES = [
    ("transition", "Your transition", "The mindset, habits and relationships that carry you through a new or growing role."),
    ("team", "Leading the team", "One-on-ones, feedback, trust and growing people."),
    ("agile", "Agile practice", "Bringing in Scrum and quality as a coach, not an enforcer."),
    ("stakeholders", "Stakeholders and communication", "Honest status, clear priorities and saying no well."),
    ("culture", "Culture and trust", "Safety, consistency and standards: the culture people feel every day, and how a leader shapes it."),
    ("leaders", "Leading leaders", "Mentoring other managers and coordinating across teams."),
    ("partners", "Vendors and partners", "Getting the most from the people outside your team."),
]

F90 = "The First 90 Days (Michael Watkins)"
SG = "The Scrum Guide"
UA = "Untapped Agility"
MEA = "More Effective Agile"
TLS = "The Lean Startup"

GUIDES = [
    # ---------------------------------------------------------------- your transition
    {
        "slug": "new-role-mindset", "theme": "transition", "minutes": 6,
        "title": "Taking on a new role: the mindset",
        "summary": "A new role asks you to stop proving what you already know and start learning what you don't, in public, without losing your footing.",
        "why": "Most stumbles in a new role come from carrying the habits of the last one: solving problems yourself, moving at your old pace, or acting before you understand. The skills that got you hired are a starting point, not the job.",
        "practices": [
            "Name what's different. Write down three ways this role differs from your last one (scope, people, how success is judged) and keep the list where you'll see it.",
            "Treat the first weeks as a learning job. Your output is understanding: of the people, the systems, the history and what leadership actually wants.",
            "Expect a dip. Feeling less capable for a while is normal when everything is new. It's a sign you're stretching, not that you chose wrong.",
            "Shift from doing to enabling. Your value now is in what the team does without you, not in what you do for them.",
            "Pick your pace on purpose. Move quickly on learning and relationships, and more slowly on changes to how people work.",
        ],
        "pitfalls": [
            "Arriving with the answer. A fix that worked elsewhere can fail here for reasons you can't see yet.",
            "Hiding behind activity. Busy days can mask that you haven't learned what matters.",
            "Trying to win every early conversation. You need allies more than points.",
        ],
        "questions": [
            "What did my last role reward that this one doesn't?",
            "Where am I still acting like an individual contributor?",
            "What would I be doing differently if I trusted that the learning dip is temporary?",
        ],
        "try": [
            "Write a one-paragraph note to yourself on what success looks like at day 90, and reread it every Friday.",
            "Block two hours this week for learning only: reading docs, the system map or past retros.",
        ],
        "related": ["/plans", "/listening", "/coaching/reflect"], "reading": [F90],
    },
    {
        "slug": "assertiveness", "theme": "transition", "minutes": 7,
        "title": "Being assertive without being abrasive",
        "summary": "Say what you think, ask for what you need and hold a line when it matters, while staying curious and kind.",
        "why": "New leaders often swing between two failures: staying quiet to fit in, or pushing hard to prove themselves. Both cost trust. Assertiveness is the middle path: clear, direct and respectful, so people always know where you stand.",
        "practices": [
            "State your view early and plainly. \"I see it differently, and here's why\" beats hinting and hoping someone notices.",
            "Separate the person from the position. You can disagree firmly with an idea and stay warm toward the person who holds it.",
            "Make clear requests. Say what you need, by when, and why it matters: \"Can you have the test plan ready by Thursday so QA can start Monday?\"",
            "Say no with a reason and an alternative. \"Not this sprint, because it would push out the release. We can look at it in refinement next week.\"",
            "Disagree, then commit. Once a decision is made, back it fully in public, even if you argued against it.",
            "Use silence. After you've made your point, stop talking and let the other person respond.",
        ],
        "pitfalls": [
            "Over-explaining or apologising before you speak. It reads as doubt.",
            "Saying yes to everything early on to be liked. It sets expectations you can't keep.",
            "Confusing volume or speed with conviction.",
            "Letting a bad commitment stand because raising it feels awkward.",
        ],
        "questions": [
            "Where have I stayed quiet recently when my view would have helped?",
            "Is there a request I've been hinting at instead of asking for?",
            "Who do I need to disagree with respectfully this week?",
        ],
        "try": [
            "In your next meeting, give your view before you're asked, in one or two sentences.",
            "Practise one clear no this week, with a reason and an alternative.",
            "After a hard conversation, note what you said, how it landed and what you'd change.",
        ],
        "related": ["/coaching/reflect", "/risks", "/raci"], "reading": [F90],
    },
    {
        "slug": "learn-fast", "theme": "transition", "minutes": 6,
        "title": "Learn fast and on purpose",
        "summary": "Decide what you need to learn, who can teach you, and how you'll know you understand, instead of absorbing whatever comes your way.",
        "why": "Everyone tells a new leader something. Without a plan, you learn the loudest stories, not the most important ones. A learning agenda keeps you honest and shortens the time before you can act well.",
        "practices": [
            "Write a learning agenda: the questions you need answered about the work, the people, the systems and the history.",
            "Ask everyone the same few questions, so you can compare answers. The listening tour uses four for this reason.",
            "Learn from several directions: your team, peers, product, customers, support and leadership each see a different piece.",
            "Hold your early views as hypotheses. Write them down, then look for evidence that would prove them wrong.",
            "Read the artifacts: past retros, incidents, the backlog, release history. They show what people actually do, not what they say.",
        ],
        "pitfalls": [
            "Talking more than listening in early conversations.",
            "Forming a firm judgment about a person or system in the first two weeks.",
            "Only learning from people who are easy to reach.",
        ],
        "questions": [
            "What are the five questions I most need answered by day 30?",
            "Whose view have I not heard yet?",
            "Which of my early impressions am I least sure of?",
        ],
        "try": [
            "List every one-on-one you still need in the listening tour and schedule the next three.",
            "Read the last three retros or incident write-ups before Friday.",
        ],
        "related": ["/listening", "/rollup", "/architecture", "/landscape"], "reading": [F90],
    },
    {
        "slug": "read-the-situation", "theme": "transition", "minutes": 5,
        "title": "Read the situation before you act",
        "summary": "Is the team broken, drifting, growing or doing well? The right first moves depend on the answer.",
        "why": "The same action can help one team and hurt another. Pushing hard for change in a team that's working can break what's good; going slowly in a team that's failing lets damage grow. Diagnose first.",
        "practices": [
            "Ask what's working and what isn't, and weigh both. Every team has something worth keeping.",
            "Look at outcomes, not only opinions: delivery dates, escaped defects, incidents, turnover.",
            "Judge urgency honestly. Is there a fire, a slow leak, or mostly room to improve?",
            "Match your pace to the situation: decisive where things are failing, patient where they're mostly sound.",
            "Different parts of your area can be in different situations. Diagnose each.",
        ],
        "pitfalls": [
            "Assuming the team needs fixing because you were hired.",
            "Ignoring signs of real trouble to avoid seeming negative.",
            "Applying one plan to every part of a mixed situation.",
        ],
        "questions": [
            "If I changed nothing for a month, what would get worse?",
            "What must I protect while I change other things?",
            "Which part of my area most needs attention first?",
        ],
        "try": [
            "Write a short diagnosis of each area you own: working, drifting or failing, with your evidence.",
            "Add the 'don't change' notes from the listening tour to your plan as things to keep.",
        ],
        "related": ["/rollup", "/landscape/swot", "/plans"], "reading": [F90],
    },
    {
        "slug": "your-manager", "theme": "transition", "minutes": 6,
        "title": "Building the relationship with your manager",
        "summary": "Agree early on what success looks like, how you'll keep them informed, and what support you need.",
        "why": "Your manager shapes your resources, your reputation and how your work is judged. Many new leaders assume alignment that isn't there, then discover the gap at review time.",
        "practices": [
            "Agree on what success looks like at 30, 60 and 90 days, in writing, and revisit it.",
            "Learn how they like to be informed: detail or summary, written or spoken, how often.",
            "Bring bad news early, with what you're doing about it. Surprises cost more trust than problems.",
            "Ask what they're worried about. It tells you what matters most to them.",
            "Bring options, not only problems, and make clear what you need from them.",
        ],
        "pitfalls": [
            "Waiting for them to define success for you.",
            "Only sharing good news.",
            "Over-reporting activity instead of outcomes.",
        ],
        "questions": [
            "Could I describe my manager's top three priorities right now?",
            "What have I not told them that they'd want to know?",
            "Have we agreed how my first 90 days will be judged?",
        ],
        "try": [
            "Share your 30/60/90 plan draft and ask what's missing.",
            "Send a short weekly status, even if it isn't asked for yet.",
        ],
        "related": ["/plans", "/status", "/me"], "reading": [F90],
    },
    {
        "slug": "early-wins", "theme": "transition", "minutes": 5,
        "title": "Early wins that build credibility",
        "summary": "Pick a few visible improvements that solve real problems people already feel, and deliver them well.",
        "why": "Early wins give people a reason to believe change is possible and give you the credibility to take on harder work. The wrong early win, one that ignores how the team works or solves a problem nobody has, costs more than it earns.",
        "practices": [
            "Choose problems the team already complains about. You'll find them in the listening tour themes.",
            "Keep them small enough to finish in weeks, not months.",
            "Involve the team. A win they helped shape is theirs, not yours.",
            "Make the result visible: in a sprint review, a retro or the weekly status.",
            "Tie each win to the bigger direction, so it's a first step, not a one-off.",
        ],
        "pitfalls": [
            "Choosing a win to impress leadership that the team doesn't care about.",
            "Changing something people value to show you're in charge.",
            "Taking on too many at once and finishing none.",
        ],
        "questions": [
            "Which complaint came up in most of my one-on-ones?",
            "What could the team see improve within a month?",
            "Who should share the credit?",
        ],
        "try": [
            "Pick one listening-tour theme with no plan item yet and add a small win for it.",
        ],
        "related": ["/plans", "/rollup", "/retros"], "reading": [F90],
    },
    {
        "slug": "managing-yourself", "theme": "transition", "minutes": 6,
        "title": "Managing yourself: energy, doubt and stress",
        "summary": "Look after the person doing the leading. Your steadiness is part of what the team relies on.",
        "why": "Transitions are tiring: new people, new systems, constant judgment calls. Leaders who run on adrenaline make worse decisions and pass their stress on. Steady habits make you more effective, not less committed.",
        "practices": [
            "Protect a few routines: sleep, exercise, a hard stop most days.",
            "Keep a short weekly reflection: what went well, what drained you, what you'll change.",
            "Build a support network outside your chain: a peer, a mentor, a friend who's led a team.",
            "Notice doubt without obeying it. Feeling unsure in a new role is common, even for people who are doing well.",
            "Decide what you won't do. Saying no protects time for what matters.",
        ],
        "pitfalls": [
            "Proving commitment with long hours.",
            "Making big decisions when exhausted or upset.",
            "Going it alone because asking for help feels like weakness.",
        ],
        "questions": [
            "What gave me energy this week, and what drained it?",
            "Who can I talk to honestly about how this is going?",
            "What's one thing I could stop doing?",
        ],
        "try": [
            "Write a reflection entry this Friday and rate your energy.",
            "Schedule one conversation with someone outside your team who you trust.",
        ],
        "related": ["/coaching/reflect", "/me"], "reading": [F90],
    },
    {
        "slug": "earning-trust", "theme": "transition", "minutes": 6,
        "title": "Earning trust with a team that's seen turnover",
        "summary": "Teams that have lost people and leaders before will wait to see if you're different. Consistency wins them over.",
        "why": "After turnover, people are tired of new leaders with new plans. Trust comes from small promises kept, honest answers and showing that you've listened before you change things.",
        "practices": [
            "Make small promises and keep every one of them.",
            "Say what you heard in the listening tour, back to the team, before you announce changes.",
            "Be honest about what you don't know and what you can't change.",
            "Keep what works. Saying \"we're keeping this\" builds as much trust as fixing something.",
            "Follow up on every concern raised, even if the answer is no.",
        ],
        "pitfalls": [
            "Criticising previous leaders or decisions.",
            "Announcing a big plan in your first weeks.",
            "Overpromising on things like headcount or tools you don't control.",
        ],
        "questions": [
            "What have I promised, and have I delivered it?",
            "What would the team say I've heard so far?",
            "Is there a concern I haven't closed the loop on?",
        ],
        "try": [
            "Share a short 'what I heard' summary with the team after the listening tour.",
            "Check the dev-sync log for anything you own that's overdue.",
        ],
        "related": ["/rollup", "/dev-sync", "/people"], "reading": [F90, UA],
    },
    # ---------------------------------------------------------------- leading the team
    {
        "slug": "one-on-ones", "theme": "team", "minutes": 5,
        "title": "One-on-ones that matter",
        "summary": "Their time, their agenda, every week or two, protected from cancellation.",
        "why": "One-on-ones are where you learn what's really going on, where people raise problems early and where you help them grow. Status updates belong elsewhere.",
        "practices": [
            "Let them set the agenda. Ask what's on their mind before you raise anything.",
            "Keep a running note per person, so you remember what you discussed and what you owe them.",
            "Rotate deeper questions: what's frustrating, what they want to learn, how you could help more.",
            "Don't cancel. Move it if you must, but keep the rhythm.",
            "End with any actions and who owns them.",
        ],
        "pitfalls": [
            "Turning it into a status meeting.",
            "Doing most of the talking.",
            "Cancelling when you're busy, which tells people where they rank.",
        ],
        "questions": [
            "When did each person last tell me something difficult?",
            "Do I know what each person wants to learn next?",
        ],
        "try": [
            "Ask one person this week: \"What's one thing I could do to make your work easier?\"",
        ],
        "related": ["/people", "/listening", "/skills"], "reading": [],
    },
    {
        "slug": "feedback", "theme": "team", "minutes": 6,
        "title": "Giving and asking for feedback",
        "summary": "Specific, timely and about the work. And ask for it as often as you give it.",
        "why": "People can't improve what they don't know about. Teams with regular, kind and direct feedback fix problems while they're small.",
        "practices": [
            "Describe the situation, what the person did and the effect, then ask for their view.",
            "Give it soon, in private for anything hard, in public for praise.",
            "Praise specifically: name the behaviour you want more of.",
            "Ask for feedback on yourself regularly, and thank people when they give it, especially when it stings.",
            "Follow up: notice and say when someone has acted on feedback.",
        ],
        "pitfalls": [
            "Saving feedback for a review.",
            "Vague praise (\"great job\") that teaches nothing.",
            "Sandwiching criticism so the message gets lost.",
        ],
        "questions": [
            "Who needs feedback from me that I've been putting off?",
            "When did I last ask my team how I'm doing?",
        ],
        "try": [
            "Give one piece of specific praise and one piece of constructive feedback this week.",
            "In a one-on-one, ask: \"What should I start, stop or keep doing?\"",
        ],
        "related": ["/people", "/coaching/reflect"], "reading": [],
    },
    {
        "slug": "psychological-safety", "theme": "team", "minutes": 6,
        "title": "Making it safe to speak up",
        "summary": "Teams do their best work when people can raise problems, admit mistakes and disagree without fear.",
        "why": "If people hide bad news, you learn about problems late, when they're expensive. Safety isn't about being soft; it's about making candour normal so the team can hold high standards.",
        "practices": [
            "Respond to bad news with curiosity, not blame: \"Thanks for raising it. What do we know?\"",
            "Admit your own mistakes out loud.",
            "Ask quieter people for their view directly, and give them time.",
            "Run blameless reviews of incidents: look at the system, not the person.",
            "Act on what people raise, or explain why not, so speaking up feels worth it.",
        ],
        "pitfalls": [
            "Shooting the messenger, even with a sigh or a look.",
            "Saying \"my door is always open\" and waiting.",
            "Letting a few voices dominate every meeting.",
        ],
        "questions": [
            "When did someone last tell me I was wrong?",
            "Who rarely speaks in our ceremonies, and why?",
        ],
        "try": [
            "In your next retro, start by sharing something you'd do differently.",
        ],
        "related": ["/retros", "/escalation", "/dev-sync"], "reading": [UA],
    },
    {
        "slug": "integrating-teams", "theme": "team", "minutes": 6,
        "title": "Bringing an acquired team into the fold",
        "summary": "Two teams, two histories, two ways of working. Respect both while building one team.",
        "why": "Acquired teams often feel judged and anxious about their future, while the existing team may feel threatened. Integration fails when one side's way is imposed without understanding why the other side worked the way it did.",
        "practices": [
            "Learn how each team works and why before choosing a common way.",
            "Name what each team does well and keep the best of both.",
            "Mix people on real work early: pairing, shared stories, joint refinement.",
            "Be clear about what's decided and what's still open. Uncertainty fuels rumours.",
            "Give people the same access, tools and information from day one.",
        ],
        "pitfalls": [
            "Calling one team's way 'the right way' by default.",
            "Keeping the teams separate for too long.",
            "Leaving questions about roles and futures unanswered.",
        ],
        "questions": [
            "What does each team believe the other does better?",
            "Where are the two ways of working actually in conflict?",
        ],
        "try": [
            "Pair someone from each team on a story this sprint.",
        ],
        "related": ["/people", "/sdlc", "/onboarding"], "reading": [UA],
    },
    {
        "slug": "delegation", "theme": "team", "minutes": 5,
        "title": "Delegating and growing people",
        "summary": "Hand over outcomes, not tasks, with the right amount of support for each person.",
        "why": "If you keep doing the work, you become the bottleneck and your team stops growing. Good delegation matches the support to the person's experience with that kind of work.",
        "practices": [
            "Delegate the outcome and the why, not every step.",
            "Agree how much check-in the person wants: tell me when it's done, or walk me through your plan first.",
            "Delegate stretch work deliberately, with a safety net.",
            "Resist taking it back when it's done differently from how you'd do it.",
            "Use the skills matrix to match stretch work to what people want to learn.",
        ],
        "pitfalls": [
            "Delegating only the boring work.",
            "Hovering, then taking over.",
            "Delegating without the authority to decide.",
        ],
        "questions": [
            "What am I doing that someone on my team could do, and would grow from?",
            "Who's ready for a stretch?",
        ],
        "try": [
            "Hand one recurring task you own to someone who wants to learn it.",
        ],
        "related": ["/skills", "/learning", "/raci"], "reading": [],
    },
    # ---------------------------------------------------------------- agile practice
    {
        "slug": "introducing-scrum", "theme": "agile", "minutes": 6,
        "title": "Bringing in Scrum as a coach, not a cop",
        "summary": "Start with the problems people feel, introduce practices that solve them, and let the team own the result.",
        "why": "Imposed process gets followed on paper and ignored in practice. Teams adopt practices that make their work visibly better, especially when they help design them.",
        "practices": [
            "Explain the why behind each practice in terms of the team's own pains.",
            "Introduce changes a few at a time and review them at retros.",
            "Start with the basics done well: a clear sprint goal, a real definition of done, honest retros.",
            "Let the team adjust practices once they understand the purpose.",
            "Use the Scrum Guide as the shared reference, so it's not your opinion against theirs.",
        ],
        "pitfalls": [
            "Rolling out every ceremony and artefact at once.",
            "Measuring adoption by attendance instead of results.",
            "Treating Scrum as the goal rather than a way to deliver better.",
        ],
        "questions": [
            "Which practice would solve the team's biggest complaint?",
            "What has the team decided for itself recently?",
        ],
        "try": [
            "At the next retro, ask the team to pick one practice to try for two sprints.",
        ],
        "related": ["/roadmap", "/sdlc", "/retros"], "reading": [SG, UA, MEA],
    },
    {
        "slug": "ceremonies", "theme": "agile", "minutes": 7,
        "title": "Making each ceremony earn its time",
        "summary": "Every meeting should leave the team clearer and better able to deliver. If it doesn't, change it.",
        "why": "Ceremonies that feel like rituals drain energy and get skipped. Each one has a purpose; keep it focused on that purpose and short.",
        "practices": [
            "Planning: agree a sprint goal first, then pull work that serves it, within real capacity.",
            "Daily standup: talk about progress toward the goal and blockers, not a list of yesterday's tasks. Take problem-solving to the dev sync afterwards.",
            "Refinement: make the next sprint's work ready, with acceptance criteria and QA in the room.",
            "Review: show working software to the people who asked for it and listen to their reaction.",
            "Retro: pick one or two changes and follow through. See the retro guide.",
            "Keep timeboxes and start on time.",
        ],
        "pitfalls": [
            "Standups that turn into status reports to the manager.",
            "Reviews with slides instead of working software.",
            "Planning that fills capacity to 100%.",
        ],
        "questions": [
            "Which ceremony does the team find least useful, and why?",
            "Does every ceremony end with something decided or clearer?",
        ],
        "try": [
            "Ask the team to rate each ceremony's usefulness from 1 to 5 at the next retro.",
        ],
        "related": ["/sprints", "/dev-sync", "/sdlc"], "reading": [SG, MEA],
    },
    {
        "slug": "retros", "theme": "agile", "minutes": 5,
        "title": "Retros that change things",
        "summary": "A retro is only as good as the commitments it produces and keeps.",
        "why": "Teams stop caring about retros when the same issues come up every time and nothing changes. A few real commitments, reviewed next time, make the retro worth everyone's hour.",
        "practices": [
            "Open by reviewing last time's commitments: done, in progress or dropped, and why.",
            "Vary the format so people think freshly.",
            "Commit to one or two changes, each with an owner and a date.",
            "Tag recurring topics, and treat repeats as a sign the fix didn't work.",
            "Make it safe: what's said in the retro is about the system, not individuals.",
        ],
        "pitfalls": [
            "Long lists of actions nobody owns.",
            "The manager talking first and most.",
            "Skipping the retro when the sprint went well.",
        ],
        "questions": [
            "Which commitments from past retros actually happened?",
            "What topic keeps coming back?",
        ],
        "try": [
            "Look at the recurring topics in Retrospectives and bring the top one to the next retro.",
        ],
        "related": ["/retros"], "reading": [SG, UA],
    },
    {
        "slug": "metrics-without-blame", "theme": "agile", "minutes": 5,
        "title": "Using metrics without blame",
        "summary": "Measure the system to improve it, never to rank people.",
        "why": "Metrics help a team see whether changes work. Used to judge individuals, they get gamed and trust disappears.",
        "practices": [
            "Measure team-level flow: cycle time, deployment frequency, change failure rate, escaped defects.",
            "Set a baseline before you set a target.",
            "Look at trends over weeks, not single readings.",
            "Discuss metrics with the team, and ask what they think is driving them.",
            "Pair each number with the story behind it.",
        ],
        "pitfalls": [
            "Comparing velocity between teams or people.",
            "Setting targets that reward cutting corners.",
            "Collecting numbers nobody looks at.",
        ],
        "questions": [
            "Would the team say our metrics help them, or watch them?",
            "Which metric would tell us if our last change worked?",
        ],
        "try": [
            "Share one metric trend at sprint review and ask the team what they see.",
        ],
        "related": ["/metrics", "/status"], "reading": [MEA, TLS],
    },
    {
        "slug": "quality-culture", "theme": "agile", "minutes": 6,
        "title": "Building quality in, not testing it in",
        "summary": "Quality is everyone's job, from refinement to release, with QA as partners rather than gatekeepers.",
        "why": "When quality is left to the end, defects are expensive and QA becomes a bottleneck. Building it into every stage makes delivery faster and calmer.",
        "practices": [
            "Bring QA into refinement to shape acceptance criteria.",
            "Agree a definition of done that includes tests and QA sign-off.",
            "Automate the checks you run often; keep manual testing for what needs human judgment.",
            "Keep a smoke test library anyone can run after a deploy.",
            "Plan regression testing for platform releases and peak seasons ahead of time.",
        ],
        "pitfalls": [
            "Treating QA as the last step before release.",
            "Skipping tests to hit a date, then paying for it in production.",
            "Counting test cases instead of asking what they protect.",
        ],
        "questions": [
            "Where do our defects come from: unclear requirements, code, or untested paths?",
            "Could a new developer run our smoke tests today?",
        ],
        "try": [
            "Review the definition of done with the team and add anything missing.",
        ],
        "related": ["/qa", "/qa/dod", "/sdlc"], "reading": [MEA],
    },
    # ---------------------------------------------------------------- stakeholders
    {
        "slug": "honest-status", "theme": "stakeholders", "minutes": 5,
        "title": "Status reports people can trust",
        "summary": "Report the real colour early, with what you're doing about it and what you need.",
        "why": "Status that's always green stops being read. Leaders trust teams that raise problems early and clearly, because it lets them help while help is still useful.",
        "practices": [
            "Lead with the overall picture in one sentence.",
            "Use red and yellow honestly, with the reason and the plan.",
            "Say what you need: a decision, a resource, a trade-off.",
            "Keep the format the same every week so changes stand out.",
            "Report outcomes and risks, not lists of activity.",
        ],
        "pitfalls": [
            "Watermelon status: green outside, red inside.",
            "Burying the important line in the middle.",
            "Only reporting when asked.",
        ],
        "questions": [
            "Is there anything in my status I'd be uncomfortable being asked about?",
            "What decision do I need from leadership this week?",
        ],
        "try": [
            "Read this week's status draft and make the first line the most important thing.",
        ],
        "related": ["/status", "/risks"], "reading": [],
    },
    {
        "slug": "saying-no-to-scope", "theme": "stakeholders", "minutes": 5,
        "title": "Protecting focus: priorities and saying no",
        "summary": "Every yes is a no to something else. Make the trade-off visible and let the right person decide.",
        "why": "Teams that take everything on finish little and burn out. Clear priorities, and a clear owner for them, let you say no without making it personal.",
        "practices": [
            "Keep one ordered backlog, owned by the product manager.",
            "When new work arrives, ask what it replaces.",
            "Show the cost of interruptions: what slipped and why.",
            "Agree who decides priority, and point requests there.",
            "Say no to the timing, not the person: \"Not now, here's when we could.\"",
        ],
        "pitfalls": [
            "Accepting side requests that never reach the backlog.",
            "Letting the loudest stakeholder set the order.",
            "Saying yes and hoping capacity appears.",
        ],
        "questions": [
            "What did we take on this sprint that wasn't planned?",
            "Who decides priority when two stakeholders disagree?",
        ],
        "try": [
            "Next time a request arrives mid-sprint, ask: \"What should we drop to make room?\"",
        ],
        "related": ["/raci", "/pi", "/roadmap"], "reading": [MEA, TLS],
    },
    # ---------------------------------------------------------------- leading leaders
    {
        "slug": "mentoring-managers", "theme": "leaders", "minutes": 6,
        "title": "Mentoring other engineering managers",
        "summary": "Share your practices as options, not rules, and help others adapt them to their teams.",
        "why": "What works for your team won't fit every team as-is. Mentoring well means teaching the reasoning behind a practice, so others can make it their own.",
        "practices": [
            "Start with their goals and problems, not your toolkit.",
            "Share practice packs as starting points they can change.",
            "Ask questions before giving answers.",
            "Meet regularly and follow up on what they tried.",
            "Learn from them too. Mentoring runs both ways.",
        ],
        "pitfalls": [
            "Expecting others to copy your approach exactly.",
            "Giving advice nobody asked for.",
            "Mentoring only when there's a problem.",
        ],
        "questions": [
            "What does this manager want to get better at?",
            "What have I learned from the managers I mentor?",
        ],
        "try": [
            "Ask a peer manager what's hardest for them right now, and just listen.",
        ],
        "related": ["/learning", "/me"], "reading": [UA],
    },
    {
        "slug": "scrum-of-scrums", "theme": "leaders", "minutes": 5,
        "title": "Coordinating across teams",
        "summary": "A short, regular forum where teams surface dependencies and blockers that cross team lines.",
        "why": "As soon as several teams depend on each other, problems hide in the gaps between them. A scrum of scrums or similar forum keeps those gaps visible.",
        "practices": [
            "Keep it short and focused on dependencies, risks and blockers.",
            "Send someone who knows the work, not always the manager.",
            "Track cross-team dependencies with an owner and a needed-by date.",
            "Escalate quickly what the forum can't solve.",
        ],
        "pitfalls": [
            "Turning it into a round of status updates.",
            "Discovering dependencies only at release time.",
        ],
        "questions": [
            "Which of our dependencies on other teams are at risk?",
        ],
        "try": [
            "List open dependencies in PI planning and check each one's owner.",
        ],
        "related": ["/pi", "/architecture/integrations"], "reading": [MEA],
    },
    # ---------------------------------------------------------------- partners
    {
        "slug": "vendor-partnerships", "theme": "partners", "minutes": 5,
        "title": "Working well with vendors and contractors",
        "summary": "Treat vendors as partners with clear expectations, regular contact and a written record.",
        "why": "Vendors and contractors can extend your team, or quietly become your biggest risk. Clear expectations and steady contact make the difference.",
        "practices": [
            "Write down what you expect: service levels, contacts, how to escalate.",
            "Meet regularly, not only when something breaks.",
            "Keep a log of conversations and commitments.",
            "Raise concerns early and specifically, with an owner and a date.",
            "Watch renewal dates well ahead of time.",
            "Include contractors in team rituals so they're part of the team.",
        ],
        "pitfalls": [
            "Only talking to a vendor during an incident.",
            "Letting renewals roll over without a review.",
            "Treating contractors as outsiders.",
        ],
        "questions": [
            "Which vendor relationship worries me most, and why?",
            "When does each contract renew?",
        ],
        "try": [
            "Log your last conversation with each key vendor, and any follow-ups.",
        ],
        "related": ["/vendors", "/escalation"], "reading": [],
    },
    # ---------------------------------------------------------------- added in starter version 2
    {
        "slug": "tech-debt-case", "theme": "stakeholders", "minutes": 7, "since": 2,
        "title": "Making the case for technical debt",
        "summary": "Talk about debt in terms leadership already cares about: risk, speed, customers and money, and agree a steady share of capacity instead of fighting for every item.",
        "why": "\"Technical debt\" means little to people outside engineering, so it loses to feature work every time it's argued in the abstract. Framed as what it costs the business today, and what it will cost if left, it becomes an ordinary trade-off leaders can weigh.",
        "practices": [
            "Classify each item by what fixing it buys: stability, performance, revenue, security, speed of delivery, lower cost, better visibility, easier change or less clutter.",
            "Describe the cost of leaving it in business terms: incidents, hours lost, slower releases, lost conversions, audit findings.",
            "Score value and effort simply, so the reasoning fits on one slide, and lead with the quick wins.",
            "Agree a standing share of each sprint for debt with your manager and product, and report against it, so you don't negotiate every item from scratch.",
            "Tie debt to dates that force the issue: a platform release, peak season, a contract renewal, an end-of-support date.",
            "When debt is accepted, record who decided, why, and when you'll look again. Accepting debt on purpose is fine; forgetting it isn't.",
        ],
        "pitfalls": [
            "Asking for a \"cleanup sprint\" with no business reason attached.",
            "Treating every item as urgent, which makes none of them credible.",
            "Hiding debt work inside feature estimates without saying so.",
            "Letting accepted debt drift with no date to revisit it.",
        ],
        "questions": [
            "Which three debt items would leadership care about most, and why?",
            "What did debt cost us last quarter in incidents, hours or lost sales?",
            "Have we agreed how much capacity goes to debt, and are we keeping to it?",
        ],
        "try": [
            "Pick your top three debt items and write one sentence each on what leaving them costs the business.",
            "Propose a capacity share for debt at your next one-on-one with your manager.",
        ],
        "related": ["/debt", "/risks", "/architecture"], "reading": [MEA],
    },
    # ---------------------------------------------------------------- added in starter version 3
    {
        "slug": "refinement-and-estimation", "theme": "agile", "minutes": 6, "since": 3,
        "title": "Refinement and estimation that make planning easy",
        "summary": "Most sprint planning problems are refinement problems. Stories that are ready and estimated make planning short and the commitment real.",
        "why": "When stories arrive at planning half-understood, the meeting turns into refinement, estimates are guesses, and the sprint fills with surprises. A steady habit of refinement during the sprint, against an agreed definition of ready, fixes that.",
        "practices": [
            "Keep two sprints' worth of stories near the top of the backlog refined and ready.",
            "Refine with the whole team in the room, including QA, so acceptance criteria and test approach are shared.",
            "Write down the technical approach and dependencies while the conversation is fresh.",
            "Estimate together, in relative points, and vote at the same time so nobody anchors on the first number.",
            "When votes spread widely, ask the highest and lowest to explain. The difference is usually something one of them knows.",
            "Plan to the team's real capacity: recent velocity, adjusted for who's away. Leave room for the unexpected.",
            "Start planning with the sprint goal, then pull the stories that serve it.",
        ],
        "pitfalls": [
            "Refining stories for the first time in sprint planning.",
            "Treating estimates as promises, or comparing velocity between teams.",
            "Filling capacity to 100% and leaving no room for support work and surprises.",
            "Pulling stories that aren't ready because they're urgent.",
        ],
        "questions": [
            "How many ready stories are on the backlog right now, in points?",
            "Which story's estimate spread the most last time, and what did we learn?",
            "Did we finish what we committed to last sprint? If not, why?",
        ],
        "try": [
            "Hold a 45-minute refinement session mid-sprint, and aim to leave it with the next sprint's stories ready.",
            "Agree a definition of ready with the team and check the top five stories against it.",
        ],
        "related": ["/planning", "/sprints", "/qa"], "reading": [SG, MEA],
    },
    # ---------------------------------------------------------------- culture and trust
    {
        "slug": 'culture-of-trust', "theme": "culture", "minutes": 6, "since": 6,
        "title": 'Building a culture of trust',
        "summary": "Trust is built in small, repeated moments: doing what you said, protecting people who speak up, and telling the truth when it's awkward.",
        "why": "A team that has been through heavy turnover has learned to be careful. People watch a new leader for months before they believe anything has changed. Speeches don't move that; a long run of small, consistent actions does.",
        "practices": [
            "Keep small promises visibly. Write down what you said you'd do and close the loop, even when the answer is no.",
            'Thank people specifically, and in public, when they raise a problem early or admit a mistake.',
            "Share what you know about what's coming, including the uncertain parts. Silence gets filled with rumours.",
            'Ask for feedback on yourself, act on some of it, and say that you did.',
            "Treat people the same whether or not they're in the room.",
            'Take a regular read of how safe and clear things feel, and look at the trend, not one score.',
        ],
        "pitfalls": [
            'Expecting trust because of your title or your track record somewhere else.',
            'Reacting badly once to bad news. One sharp reaction undoes months of invitation.',
            'Asking for openness, then repeating something said in confidence.',
        ],
        "questions": [
            'What did I promise this week, and did I deliver it?',
            'Who has stopped bringing me problems, and why?',
            "When did someone last tell me something I didn't want to hear? How did I respond?",
        ],
        "try": [
            'Take a trust pulse now and again in two weeks. Pick the lowest line and do one thing about it.',
            "In your next one-on-ones, ask: what's one thing I could do that would make your work easier?",
        ],
        "related": ['/culture', '/people', '/retros'], "reading": [],
    },
    {
        "slug": 'strong-and-quiet-voices', "theme": "culture", "minutes": 5, "since": 6,
        "title": 'Strong opinions and quiet voices',
        "summary": "Meetings tend to belong to whoever talks first and loudest. A leader's job is to make sure the best idea wins, not the most confident one.",
        "why": 'When a few strong voices dominate, the rest of the team stops offering ideas, and you lose what they know. It rarely looks like a problem from the front of the room, because the quiet simply stay quiet.',
        "practices": [
            'Give people time to think before discussing: a minute of silent writing, then go round the room.',
            'Ask the quietest person first, by name, with a question they can answer well.',
            'Gather estimates and opinions at the same time so nobody anchors on the first answer.',
            "When someone talks over another person, bring it back: 'Hold on, I want to hear the rest of that.'",
            "Talk privately with people who dominate. Most don't realize the effect, and many will help once they do.",
            'Offer written channels for people who think better after the meeting.',
        ],
        "pitfalls": [
            'Taking silence as agreement.',
            'Rewarding speed of answer over quality of thought.',
            'Shaming a dominant person in front of the group. Address it privately.',
        ],
        "questions": [
            'In my last three meetings, who spoke least? What might they have known?',
            'Do decisions here tend to go to the person who argues hardest?',
        ],
        "try": [
            'Run your next retro with silent writing first and a round where everyone speaks once before open discussion.',
        ],
        "related": ['/culture', '/retros', '/planning'], "reading": [],
    },
    {
        "slug": 'calling-out-harm', "theme": "culture", "minutes": 6, "since": 6,
        "title": 'Calling out intimidation and harmful behavior',
        "summary": 'What a leader tolerates becomes the standard. Address harmful behavior early, privately first, and about the behavior rather than the person.',
        "why": 'Intimidation, belittling and blame spread quietly. The people affected rarely complain, and everyone else learns what is allowed. Leaving it alone is a decision, and the team notices it.',
        "practices": [
            'Write down what you saw soon after: what was said or done, the date, and the effect on others. Specifics beat impressions.',
            'Talk to the person privately and soon. Describe the behavior and its effect, then ask for their view.',
            'Be clear about what needs to change, and follow up on a date.',
            "Check in with the people affected. Make sure they know you noticed and that they won't pay for speaking up.",
            "If it continues, or it's serious, take it to your manager or HR, following your company's process.",
            'Recognize good behavior too: people who make room for others, admit mistakes, or help a colleague.',
        ],
        "pitfalls": [
            'Waiting for someone to complain formally before acting.',
            'Excusing behavior because the person is a high performer.',
            'Labelling the person instead of describing what they did.',
            'Raising it once and never following up.',
        ],
        "questions": [
            "Is there a behavior on my team I've been hoping will go away on its own?",
            'Would a new team member think this behavior is normal here?',
        ],
        "try": [
            "Note anything you've been putting off under Culture and trust, decide on one step, and set a follow-up date.",
        ],
        "related": ['/culture', '/people', '/coaching/feedback'], "reading": [],
    },
    {
        "slug": 'consistency-and-integrity', "theme": "culture", "minutes": 5, "since": 6,
        "title": 'Being consistent every day',
        "summary": "A reputation for integrity comes from doing the same right thing on hard days as on easy ones, so people can predict how you'll act.",
        "why": "People trust leaders they can predict. If your standards bend under pressure, or depend on who's asking, people learn to manage you instead of telling you the truth.",
        "practices": [
            'Write down the handful of standards you hold yourself to, in your own words, and read them often.',
            'Check yourself weekly against them, honestly, and note a moment that showed each one, either way.',
            'Apply the same rules to senior and junior people, and to people you like and people you find difficult.',
            "When you get something wrong, say so plainly and say what you'll do differently.",
            'Explain your decisions, including the trade-offs, so people can see the reasoning is consistent.',
        ],
        "pitfalls": [
            'Lowering the bar quietly when a deadline is close.',
            "Holding the team to standards you don't meet yourself.",
            'Treating integrity as a trait you have rather than a habit you practice.',
        ],
        "questions": [
            'Where did I bend a standard this week, and was it a good reason or a convenient one?',
            "Could my team predict how I'd react to a missed deadline? To bad news?",
        ],
        "try": [
            'Do the weekly self-check under Culture and trust for a month and look at the trend.',
        ],
        "related": ['/culture', '/coaching/culture-of-trust'], "reading": [],
    },
    {
        "slug": 'order-without-bureaucracy', "theme": "culture", "minutes": 5, "since": 6,
        "title": 'Order without bureaucracy',
        "summary": 'Chaos wears people out. A small amount of clear, agreed process gives a team calm and predictability without slowing it down.',
        "why": 'When nobody knows how work arrives, who decides, or what done means, every day becomes a scramble and the loudest request wins. People feel it as stress, not as a process problem. Adding the right little bit of structure is one of the kindest things a leader can do.',
        "practices": [
            'Start with the pain people already feel: surprise requests, unclear priorities, broken handoffs.',
            'Agree a few simple rules with the team: one way work comes in, who sets priority, what done means.',
            'Write them down where everyone can see them, and mark them agreed.',
            'Protect the team from work that skips the process, politely and every time.',
            "Review the rules at retros. Drop the ones that don't help.",
        ],
        "pitfalls": [
            'Adding process for its own sake, or all at once.',
            "Imposing rules the team didn't help shape.",
            'Making exceptions for whoever pushes hardest; that brings the chaos back.',
        ],
        "questions": [
            "Where does work arrive without warning, and who decides whether it's taken on?",
            'What do people find most chaotic right now?',
        ],
        "try": [
            'Ask the team for the one rule that would make the next sprint calmer, agree it, and try it for two sprints.',
        ],
        "related": ['/culture', '/sdlc', '/roadmap'], "reading": [UA],
    },
    {
        "slug": 'challenging-the-organization', "theme": "culture", "minutes": 6, "since": 6,
        "title": 'Challenging the wider organization well',
        "summary": "Some of what hurts your team comes from outside it. Raise it with evidence and a proposal, through the right people, and keep your team's trust while you do.",
        "why": 'Teams notice whether their leader is willing to stand up for them. But a challenge that arrives as a complaint, or goes round people, costs credibility. Done well, pushing back makes you more trusted on both sides.',
        "practices": [
            'Collect specifics before raising anything: what happens, how often, and the cost to delivery or to people.',
            'Bring a proposal, not just a problem, and be open to a better one.',
            'Raise it with your manager first, and agree who else should hear it.',
            'Pick the few things that matter most. Challenging everything gets you tuned out.',
            'Tell your team what you raised and what happened, even when nothing has changed yet.',
        ],
        "pitfalls": [
            'Venting about other teams to your own.',
            "Going over someone's head without talking to them first.",
            "Promising your team a change you can't deliver.",
        ],
        "questions": [
            'Which organization-wide habit costs my team the most?',
            'What evidence do I have, and who could change it?',
        ],
        "try": [
            'Note organization-wide patterns under Culture and trust for a month, then bring the top one to your manager with a proposal.',
        ],
        "related": ['/culture', '/sos', '/coaching/your-manager'], "reading": [],
    },
]

# Short nudges shown at the top of each screen; each points to a guide. Keyed by route, shared by both apps.
TIPS = {
    "/culture": [('What you tolerate becomes the standard. Address harmful behavior early, privately, and follow up.', 'calling-out-harm', 6),
                 ("Read today's standard before your first meeting, and look for one chance to live it.", 'consistency-and-integrity', 6),
                 ("Note the good moments too. Reinforcing what you want to see works faster than correcting what you don't.", 'culture-of-trust', 6)],
    "/today": [("Start the day by protecting one block of time for the most important thing, not the most urgent.", "managing-yourself")],
    "/people": [("Keep a running note for each person, so every one-on-one picks up where the last one left off.", "one-on-ones"),
                ("Set a check-in cadence for the people who matter most. Relationships fade quietly when you're busy.", "one-on-ones", 5),
                ("Ask each person what they want to learn next, and look for work that stretches them toward it.", "delegation"),
                ("Treat people the same whether or not they're in the room. People notice.", 'culture-of-trust', 6)],
    "/onboarding": [("A new member's first week sets how they'll feel about the team. Make sure their buddy checks in daily.", "earning-trust"),
                    ("At the 30-day check-in, ask what the checklist missed and update the template.", "feedback")],
    "/skills": [("Match stretch work to what people want to learn. Growth is one of the best reasons people stay.", "delegation")],
    "/listening": [("Ask everyone the same questions so you can compare answers. Listen more than you talk.", "learn-fast"),
                   ("Hold early impressions as hypotheses. Write down what would prove them wrong.", "read-the-situation")],
    "/rollup": [("Share what you heard with the team before announcing changes. It shows you listened.", "earning-trust"),
                ("The 'don't change' notes matter as much as the complaints. Plan to keep them.", "read-the-situation")],
    "/sdlc": [("A process the team helped write is one they'll follow. Agree policies together and mark them agreed.", "introducing-scrum"),
              ('A few clear, agreed rules beat chaos and beat bureaucracy. Start with the pain people already feel.', 'order-without-bureaucracy', 6)],
    "/sprints": [("Start planning with a sprint goal, then pull work that serves it, within real capacity.", "ceremonies")],
    "/teams": [("Update each team's status in one line whenever you hear news. A dated status beats a detailed stale one.", "scrum-of-scrums", 4),
               ('Notice patterns across teams, not just inside yours. Note them under Culture and trust with evidence.', 'challenging-the-organization', 6)],
    "/sos": [("Every cross-team item needs one owner, a due date and the outcome you expect. Otherwise it just gets discussed again next week.", "scrum-of-scrums", 4),
             ("Keep the Scrum of Scrums short: dependencies, risks and blockers. Escalate quickly what it can't solve.", "scrum-of-scrums", 4),
             ('When an organization-wide habit keeps hurting delivery, bring evidence and a proposal, not a complaint.', 'challenging-the-organization', 6)],
    "/planning": [("Keep two sprints' worth of stories refined and ready, so planning is short and the commitment is real.", "refinement-and-estimation", 3),
                  ("When estimates spread widely, ask the highest and lowest to explain before voting again.", "refinement-and-estimation", 3),
                  ("Plan to recent velocity, adjusted for who's away, and leave room for surprises.", "refinement-and-estimation", 3)],
    "/retros": [("Open every retro by reviewing last time's commitments. That's what makes retros worth the hour.", "retros"),
                ("If you're the manager, speak last.", "psychological-safety"),
                ('Start with a minute of silent writing so the quiet voices get heard before the loud ones.', 'strong-and-quiet-voices', 6)],
    "/pi": [("Make cross-team dependencies visible early, each with an owner and a needed-by date.", "scrum-of-scrums")],
    "/roadmap": [("Introduce practices a few at a time, and review each at a retro before adding more.", "introducing-scrum")],
    "/raci": [("When two stakeholders disagree on priority, the RACI tells you who decides. Point requests there.", "saying-no-to-scope")],
    "/risks": [("Raise risks early, with a plan. Surprises cost more trust than problems.", "your-manager")],
    "/debt": [("Describe each debt item by what leaving it costs the business, not by how ugly the code is.", "tech-debt-case", 2),
              ("Agree a standing share of each sprint for debt, then report against it, instead of arguing every item.", "tech-debt-case", 2)],
    "/metrics": [("Measure the system, never individuals. Set a baseline before a target.", "metrics-without-blame")],
    "/qa": [("Bring QA into refinement. Quality built in costs less than quality tested in.", "quality-culture")],
    "/dev-sync": [("Follow up on every item, even when the answer is no. Closed loops build trust.", "earning-trust")],
    "/learning": [("Teaching others is one of the fastest ways to learn. Invite people to present what they know.", "delegation")],
    "/vendors": [("Talk to key vendors regularly, not only during incidents.", "vendor-partnerships")],
    "/plans": [("Agree what success looks like at each step with your manager, in writing.", "your-manager"),
               ("Pick a few early wins that solve problems people already feel.", "early-wins")],
    "/status": [("Lead with the real colour and what you need. Status that's always green stops being read.", "honest-status")],
    "/architecture": [("Read the artifacts: the system map, past decisions and incidents show how things really work.", "learn-fast")],
    "/landscape": [("Diagnose each area separately. Some parts need fixing; others need protecting.", "read-the-situation")],
    "/escalation": [("Review incidents without blame: look at the system, not the person.", "psychological-safety")],
    "/me": [("Look after the person doing the leading. Rate your energy each week and notice the trend.", "managing-yourself")],
    "/this-week": [("Send updates on a steady rhythm, even when there's little news. Consistency builds trust.", "honest-status")],
    "/messages": [("Put the most important sentence first. Most people read only the opening.", "honest-status")],
    "/templates": [("A template keeps your updates consistent, so changes stand out.", "honest-status")],
    "/calendar": [("Plan your communication rhythm before you need it, so updates never feel like a surprise.", "your-manager")],
    "/audiences": [("Different audiences need different detail. Ask each how they like to be informed.", "your-manager")],
    "/plain-language": [("Plain words build trust. Jargon makes people feel left out.", "honest-status")],
    "/decks": [("Show working software in reviews, not slides, whenever you can. Save decks for leadership stories.", "ceremonies")],
}

# Reflection prompts by how far into the role you are (day numbers from the contract start date).
REFLECTION_PHASES = [
    ("Before you start", None, 0, [
        "What do I want people to say about me at day 90?",
        "What habits from my last role should I leave behind?",
        "What am I most nervous about, and what would help?",
    ]),
    ("The first week", 1, 7, [
        "What surprised me this week?",
        "Who did I meet who I want to learn more from?",
        "Where did I talk when I should have listened?",
    ]),
    ("Weeks 2 to 4", 8, 30, [
        "What pattern am I starting to see in what people tell me?",
        "Which of my early impressions has changed?",
        "What's one thing I said I'd do that I haven't done yet?",
        "Where did I hold back my view when it would have helped?",
    ]),
    ("Days 31 to 60", 31, 60, [
        "Is my first early win on track? What's in the way?",
        "Does my manager see my progress the way I do?",
        "What's draining my energy, and what could I change?",
    ]),
    ("Days 61 to 90", 61, 90, [
        "What will I be judged on at day 90, and how am I doing?",
        "What have I learned about leading this team that I didn't know at the start?",
        "What should I stop doing in the next 90 days?",
    ]),
    ("After day 90", 91, None, [
        "What's the next stretch for me as a leader?",
        "Who on my team is ready for more responsibility?",
        "What am I proud of this month?",
    ]),
]
ANYTIME_PROMPTS = [
    "Where was I assertive this week, and how did it land?",
    "What conversation am I avoiding, and what's the first sentence I could say?",
    "What gave me energy this week, and what drained it?",
    "What did I learn from a mistake this week?",
]


def guide(slug: str) -> dict | None:
    return next((g for g in GUIDES if g["slug"] == slug), None)


def phase_for(day: int | None) -> str:
    if day is None:
        return "Any time"
    for name, lo, hi, _ in REFLECTION_PHASES:
        if (lo is None or day >= lo) and (hi is None or day <= hi):
            return name
    return "Any time"


STARTER_VERSION = 6  # bump when adding guides or tips, and mark the new ones with "since"


def tip_entries():
    """(route, text, slug, since) for every starter tip."""
    for route, tips in TIPS.items():
        for tip in tips:
            text, slug, since = (*tip, 1)[:3]
            yield route, text, slug, since


def builtin_tips(paths: set[str]) -> dict:
    out = {}
    for route, text, slug, _ in tip_entries():
        if route in paths:
            out.setdefault(route, []).append({"text": text, "guide": slug, "title": guide(slug)["title"]})
    return out
