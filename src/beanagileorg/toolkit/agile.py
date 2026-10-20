"""An Agile reference: SAFe, the framework the toolkit is built around; Scrum, how each team inside it works (its
accountabilities, events, artifacts and commitments); and the common practices teams add, with how each is done here.

Every description is written in our own words. The Scrum Guide itself is at scrumguides.org; SAFe and Scaled
Agile Framework are registered trademarks of Scaled Agile, Inc., and its own material is at scaledagileframework.com.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from beanagileorg.core.app import get_conn, get_viewer
from beanagileorg.core.privacy import Viewer

from .routes import require_write

router = APIRouter()
PRACTICE_KEY = "agile.practice"
SPRINT_WEEKS_KEY = "agile.sprint_weeks"
DEFAULT_SPRINT_WEEKS = 2
# The Scrum Guide's maximum length for each event in a one-month sprint; shorter sprints get proportionally shorter events.
MONTH_MAX_HOURS = {"sprint-planning": 8, "sprint-review": 4, "retrospective": 3}
WEEK_WORDS = {1: "one-week", 2: "two-week", 3: "three-week", 4: "four-week"}


def _hours(h: float) -> str:
    total = int(round(h * 60))
    hrs, mins = divmod(total, 60)
    if not hrs:
        return f"{mins} minutes"
    if mins == 30:
        return "an hour and a half" if hrs == 1 else f"{hrs} and a half hours"
    head = "1 hour" if hrs == 1 else f"{hrs} hours"
    return f"{head} {mins} minutes" if mins else head


def timebox_for(key: str, weeks: int) -> str | None:
    """The timebox for an event, given the team's sprint length."""
    if key == "sprint":
        return f"{WEEK_WORDS[weeks].replace('-', ' ').capitalize()}s, your team's length (the Scrum Guide allows up to one month)"
    if key in MONTH_MAX_HOURS:
        return f"Up to {_hours(MONTH_MAX_HOURS[key] * weeks / 4)} for a {WEEK_WORDS[weeks]} sprint (the Scrum Guide's maximum is {MONTH_MAX_HOURS[key]} hours for a one-month sprint)"
    return None
STATUSES = ("not yet", "partly", "practiced", "not used here")
SOURCES = {
    "scrum": ("The Scrum Guide", "https://scrumguides.org"),
    "safe": ("SAFe (Scaled Agile Framework), a registered trademark of Scaled Agile, Inc.", "https://scaledagileframework.com"),
}

# (key, framework, kind, name, what it is, why it matters, timebox or cadence, where it lives in the toolkit)
REFERENCE = [
    # ---- Scrum: foundations
    ("empiricism", "scrum", "foundation", "Empiricism: transparency, inspection, adaptation",
     "Scrum rests on learning from experience. The work and progress are visible to everyone (transparency), the team checks them often (inspection), and it changes course as soon as something is off (adaptation).",
     "Every event exists to inspect and adapt something. If an event isn't leading to a change when one is needed, it has become a ritual.", None, None),
    ("values", "scrum", "foundation", "Scrum values: commitment, focus, openness, respect, courage",
     "Five values the team lives by: committing to its goals, focusing on the sprint's work, being open about work and problems, respecting one another as capable people, and having the courage to do the right thing and tackle hard problems.",
     "The events and artifacts only work when people trust each other enough to be honest about progress and problems.", None, "#/culture/agreements"),
    ("scrum-team", "scrum", "foundation", "The Scrum Team",
     "A small, cross-functional, self-managing team, usually ten people or fewer: one Product Owner, one Scrum Master and the Developers. It has all the skills needed to create value each sprint, and decides internally who does what, when and how.",
     "Small teams communicate better and move faster. When a team grows too large, split it into several teams that share one Product Goal, one Product Backlog and one Product Owner.", None, "#/teams"),
    # ---- Scrum: accountabilities
    ("product-owner", "scrum", "accountability", "Product Owner",
     "One person accountable for maximizing the value of the product: developing and communicating the Product Goal, creating and ordering Product Backlog items, and keeping the backlog clear and visible. They may delegate the work but stay accountable.",
     "Without one clear owner of priority, the team gets pulled in many directions and nobody can say no.", None, "#/planning"),
    ("scrum-master", "scrum", "accountability", "Scrum Master",
     "Accountable for the Scrum Team's effectiveness: helping the team and organization understand and use Scrum, coaching self-management, removing impediments, and making sure the events happen, stay positive and keep to their timebox.",
     "A servant leader for the team and the wider organization. In a team new to Scrum, this role carries much of the change.", None, None),
    ("developers", "scrum", "accountability", "Developers",
     "The people who create the usable increment each sprint, whatever their specialty (engineering, testing, design). They plan the sprint, hold themselves to the Definition of Done, adapt their plan daily toward the Sprint Goal, and hold each other accountable.",
     "Quality is the whole team's job, not a later step done by someone else.", None, "#/people"),
    # ---- Scrum: events
    ("sprint", "scrum", "event", "The Sprint",
     "A fixed-length container of one month or less in which the team turns ideas into value. A new sprint starts immediately after the last one ends. Changes that would endanger the Sprint Goal aren't made; scope can be clarified and renegotiated with the Product Owner as more is learned.",
     "A steady rhythm makes delivery predictable and gives the organization regular chances to inspect and change direction.", None, "#/sprints"),
    ("sprint-planning", "scrum", "event", "Sprint Planning",
     "Starts the sprint. The team agrees why the sprint is valuable (the Sprint Goal), what can be done (items pulled from the Product Backlog), and how the work will get done (a plan for delivering the increment).",
     "A shared goal lets the team adapt the details without losing sight of what matters.", None, "#/planning"),
    ("daily-scrum", "scrum", "event", "Daily Scrum",
     "A short daily event for the Developers to inspect progress toward the Sprint Goal and adapt the plan for the next day. Same time and place each day. The format is theirs to choose.",
     "Surfaces impediments early and reduces the need for other meetings. Detailed discussions happen right after, with only the people who need to be there.", "15 minutes", "#/dev-sync"),
    ("sprint-review", "scrum", "event", "Sprint Review",
     "The team shows stakeholders what it accomplished and discusses what changed in the environment. Together they decide what to do next, which may adjust the Product Backlog. A working session, not a presentation.",
     "Keeps the product pointed at what stakeholders actually need, and builds trust through working results.", None, "#/sprints"),
    ("retrospective", "scrum", "event", "Sprint Retrospective",
     "The team inspects how the last sprint went for individuals, interactions, processes, tools and its Definition of Done, and picks the most helpful improvements to act on, sometimes in the very next sprint.",
     "The engine of continuous improvement. Retros that never lead to change soon lose the team's attention.", None, "#/retros"),
    # ---- Scrum: artifacts and their commitments
    ("product-backlog", "scrum", "artifact", "Product Backlog",
     "An ordered, emerging list of what is needed to improve the product: the single source of work for the Scrum Team. Items near the top are refined until they're ready to be selected in Sprint Planning.",
     "One visible, ordered list makes priorities transparent and stops side-channel requests from quietly taking over.", None, "#/planning"),
    ("product-goal", "scrum", "commitment", "Product Goal",
     "The commitment for the Product Backlog: a future state of the product the team works toward. The team meets or abandons one before taking on the next.",
     "Gives the backlog a direction, so priorities can be judged against something.", None, "#/roadmap"),
    ("sprint-backlog", "scrum", "artifact", "Sprint Backlog",
     "The Sprint Goal, the Product Backlog items selected for the sprint, and the Developers' plan for delivering them. It's updated throughout the sprint as the team learns.",
     "Makes the sprint's work and progress visible in real time, by and for the Developers.", None, "#/planning"),
    ("sprint-goal", "scrum", "commitment", "Sprint Goal",
     "The commitment for the Sprint Backlog: the single objective for the sprint. It gives the team flexibility in exactly what work it does, and coherence so people work together rather than on separate initiatives.",
     "When surprises hit, the team adjusts the work and protects the goal.", None, "#/planning"),
    ("increment", "scrum", "artifact", "Increment",
     "A concrete, usable step toward the Product Goal. Each one adds to everything before it and is thoroughly verified so they work together. Several can be created in a sprint, and they can be released at any time.",
     "Only work that meets the Definition of Done counts. Undone work isn't shown at the review; it goes back to the backlog.", None, "#/sdlc"),
    ("definition-of-done", "scrum", "commitment", "Definition of Done",
     "The commitment for the Increment: a formal description of the quality the increment must meet. If the organization has a standard, the team follows it as a minimum.",
     "Creates a shared understanding of what finished means, and is where quality expectations (tests, review, documentation) become concrete.", None, "#/qa/dod"),
    # ---- common practices teams add to Scrum
    ("refinement", "practice", "practice", "Backlog refinement",
     "An ongoing activity, not a Scrum event: breaking backlog items down, adding detail, estimating and ordering them so the top of the backlog is ready for planning. Many teams hold a regular session for it.",
     "Short, effective Sprint Planning depends on refinement having happened before it.", "Commonly no more than about a tenth of the team's time; for a two-week sprint, often one or two sessions of an hour", "#/planning"),
    ("definition-of-ready", "practice", "practice", "Definition of Ready",
     "A team's own checklist for when a backlog item is clear enough to bring into a sprint: understood, small enough, acceptance criteria written, dependencies known. Not part of Scrum, and best used as guidance rather than a gate.",
     "Cuts mid-sprint surprises caused by vague work.", None, "#/planning"),
    ("user-stories", "practice", "practice", "User stories and acceptance criteria",
     "A common way to write backlog items from the user's point of view, with the conditions that must be true for the item to be accepted.",
     "Keeps the conversation on the value to users, and gives testers and developers the same target.", None, "#/planning"),
    ("estimation", "practice", "practice", "Estimation: story points and planning poker",
     "Relative sizing of backlog items by the people who'll do the work, often with planning poker so everyone estimates before anyone is anchored by others.",
     "Big spreads in estimates reveal different understandings worth discussing before the work starts.", None, "#/planning"),
    ("velocity", "practice", "practice", "Velocity and capacity",
     "How much a team typically completes per sprint, used with who's available to plan a realistic amount of work.",
     "A planning aid for the team, never a target or a way to compare teams.", None, "#/planning"),
    ("burndown", "practice", "practice", "Burndown and burnup charts",
     "Charts of work remaining (or completed) over a sprint or release, showing whether the team is on track.",
     "Make progress visible at a glance, if they're kept honest.", None, "#/status"),
    ("board", "practice", "practice", "Task board and WIP limits",
     "A visible board of the sprint's work by state (to do, in progress, in review, done), often with limits on how much can be in progress at once.",
     "Limiting work in progress finishes things faster and exposes bottlenecks.", None, None),
    ("spike", "practice", "practice", "Spike",
     "A short, timeboxed piece of work to answer a question or reduce uncertainty before committing to the real work.",
     "Turns unknowns into estimates.", None, "#/planning"),
    ("working-agreement", "practice", "practice", "Team working agreement",
     "The team's own agreements on how it works together: meetings, code review, disagreement, communication.",
     "Agreements the team makes are ones it keeps.", None, "#/culture/agreements"),
    ("release-planning", "practice", "practice", "Release planning and release readiness",
     "Planning what goes into a release and checking it's ready: testing, sign-off, communication, rollback.",
     "Most broken releases trace back to skipped readiness steps.", None, "#/sdlc"),
    ("scrum-of-scrums", "practice", "practice", "Scrum of Scrums (in SAFe, the coach sync)",
     "A regular meeting of representatives from several teams to manage dependencies, risks and blockers across them.",
     "Keeps teams that share a product from surprising each other.", "Often two or three times a week", "#/sos"),
    ("delivery-metrics", "practice", "practice", "Delivery metrics",
     "A few measures of the delivery system, such as cycle time, deployment frequency, change failure rate and escaped defects, compared with outside benchmarks.",
     "Facts make the case for change better than opinions. Measure the system, never individuals.", None, "#/metrics"),
    # ---- SAFe: roles and structure
    ("art", "safe", "structure", "Agile Release Train (ART)",
     "A long-lived team of agile teams, typically 50 to 125 people, that plans, commits, delivers and inspects together toward a shared mission.",
     "Aligns many teams to one cadence and one backlog, so dependencies get handled in planning rather than discovered in delivery.", None, "#/teams"),
    ("rte", "safe", "role", "Release Train Engineer (RTE)",
     "The servant leader and coach for an ART: facilitating its events, helping manage risks and dependencies, and driving continuous improvement. Something like a chief Scrum Master for the train.",
     "Someone has to own how the train runs, not just what it builds.", None, "#/sos"),
    ("product-management", "safe", "role", "Product Management",
     "Owns the ART's backlog and its vision and roadmap, working with Product Owners on each team, who own their team backlogs.",
     "Splits product ownership across levels so each team still has a clear owner of priority.", None, "#/roadmap"),
    ("system-architect", "safe", "role", "System Architect",
     "Guides the technical direction of the ART: architecture, the runway for upcoming features, and the non-functional requirements.",
     "Keeps many teams building one coherent system.", None, "#/architecture"),
    ("business-owners", "safe", "role", "Business Owners",
     "The few stakeholders accountable for the business outcomes of an ART. They assign business value to PI objectives and take part in PI Planning.",
     "Connects the train's plans to what the business actually values.", None, "#/pi"),
    # ---- SAFe: events and timeboxes
    ("pi", "safe", "event", "Planning Interval (PI), formerly Program Increment",
     "The ART's planning and delivery timebox, usually 8 to 12 weeks: several development iterations followed by an Innovation and Planning iteration.",
     "A longer, shared cadence that lets many teams plan together and deliver integrated value.", "Usually 8 to 12 weeks", "#/pi"),
    ("pi-planning", "safe", "event", "PI Planning",
     "A face-to-face (or well-run remote) event, often two days, where all the teams on an ART plan the next PI together: they draft plans, surface dependencies and risks, and commit to PI objectives.",
     "The heartbeat of SAFe: alignment that would otherwise take weeks of meetings happens in the room.", "Every PI, usually two days", "#/pi"),
    ("pi-objectives", "safe", "artifact", "PI objectives",
     "What each team and the ART intend to achieve in the PI, split into committed and uncommitted (stretch) objectives, with business value assigned by Business Owners and actual value scored at the end.",
     "Turns plans into business outcomes, and the planned-versus-actual comparison shows predictability.", None, "#/pi"),
    ("iteration", "safe", "event", "Iterations (SAFe's sprints)",
     "The team-level timebox inside a PI, usually two weeks, with iteration planning, a daily stand-up, an iteration review and a retrospective, much as in Scrum.",
     "Teams keep their own rhythm while fitting the train's cadence.", "Usually two weeks", "#/sprints"),
    ("ip-iteration", "safe", "event", "Innovation and Planning (IP) iteration",
     "The last iteration of a PI, set aside for innovation, learning, final integration, the Inspect and Adapt workshop and the next PI Planning. It also acts as an estimating buffer.",
     "Protects time for improvement and planning that would otherwise be squeezed out by delivery.", "One iteration per PI", "#/pi"),
    ("art-sync", "safe", "event", "ART sync: coach sync and PO sync",
     "Regular syncs for the train: Scrum Masters (or team coaches) and the RTE review progress, dependencies and impediments (the coach sync, close to a Scrum of Scrums), and Product Owners with Product Management review scope and priorities (the PO sync).",
     "Keeps the train's plan on track between PI Planning events.", "Usually weekly", "#/sos"),
    ("system-demo", "safe", "event", "System demo",
     "An integrated demonstration of what the whole ART built in the latest iteration, shown to stakeholders and Business Owners.",
     "Shows real, integrated progress across teams, not separate team demos.", "Every iteration", "#/sprints"),
    ("inspect-adapt", "safe", "event", "Inspect and Adapt (I&A)",
     "A workshop at the end of each PI: the current state of the solution is demonstrated, quantitative results are reviewed, and a structured problem-solving session produces improvement items for the next PI.",
     "The train's retrospective, with data.", "Every PI", "#/retros"),
    # ---- SAFe: artifacts and practices
    ("art-backlog", "safe", "artifact", "ART backlog, formerly the Program Backlog",
     "The ART's ordered list of upcoming features and enablers, owned by Product Management.",
     "One backlog for the train, so team backlogs stay aligned.", None, "#/planning"),
    ("features-enablers", "safe", "artifact", "Epics, capabilities, features, enablers and stories",
     "SAFe's levels of work: epics (large initiatives at portfolio level), capabilities (for large solutions), features (sized to fit one PI), and stories (sized to fit one iteration). Enablers are the technical and architectural work that supports them.",
     "Lets strategy flow down into team-sized work and progress roll back up.", None, "#/pi"),
    ("planning-board", "safe", "artifact", "ART planning board, formerly the Program Board",
     "A visual board built during PI Planning showing when features will be delivered, the dependencies between teams, and key milestones.",
     "Makes cross-team dependencies impossible to miss.", None, "#/pi"),
    ("roam", "safe", "practice", "ROAM risks",
     "Sorting each risk raised in PI Planning into Resolved, Owned, Accepted or Mitigated.",
     "Every risk leaves the room with a clear status and, usually, an owner.", None, "#/pi"),
    ("confidence-vote", "safe", "practice", "Confidence vote",
     "At the end of PI Planning, everyone votes on their confidence in the plan, often fist-of-five. Low confidence leads to rework until the plan is credible.",
     "Surfaces doubts before commitment rather than after.", None, "#/pi"),
    ("wsjf", "safe", "practice", "Weighted Shortest Job First (WSJF)",
     "A way to order work by the cost of delaying it divided by its size, so the most valuable small items go first.",
     "Replaces arguing about priority with an explicit, repeatable comparison.", None, "#/debt"),
    ("runway", "safe", "practice", "Architectural runway",
     "The existing code, components and technical infrastructure needed to implement upcoming features without excessive redesign.",
     "Teams slow down sharply when they run out of runway; enablers keep it extended.", None, "#/architecture"),
    ("cd-pipeline", "safe", "practice", "Continuous delivery pipeline and DevOps",
     "The flow of work from idea to release: continuous exploration, continuous integration, continuous deployment and release on demand.",
     "Frequent, low-risk releases depend on automating and owning the whole path.", None, "#/sdlc"),
    ("lpm", "safe", "practice", "Lean Portfolio Management and value streams",
     "Aligning strategy, funding and governance to value streams, the sequences of steps that deliver value to customers, rather than funding projects one by one.",
     "Funds long-lived teams around value instead of temporary projects.", None, "#/landscape"),
    ("solution-train", "safe", "structure", "Solution train",
     "For very large solutions, several ARTs (and suppliers) coordinated on a shared cadence, with roles that mirror the ART's at a higher level.",
     "Only needed when one train can't build the solution alone.", None, None),
]


def _saved(conn) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (PRACTICE_KEY,)).fetchone()
    return json.loads(row["value"]) if row else {}


@router.get("/api/agile/reference")
def reference(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """The reference, with how the team practices each entry. Status and notes show while presenting; they describe
    the team's way of working, not anyone in particular."""
    saved = _saved(conn)
    wrow = conn.execute("SELECT value FROM settings WHERE key = ?", (SPRINT_WEEKS_KEY,)).fetchone()
    weeks = int(wrow["value"]) if wrow else DEFAULT_SPRINT_WEEKS
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (GUIDE_KEY,)).fetchone()
    md = json.loads(row["value"])["markdown"] if row else None
    entries = []
    for k, f, kind, n, w, y, t, link in REFERENCE:
        e = {"key": k, "framework": f, "kind": kind, "name": n, "what": w, "why": y, "timebox": timebox_for(k, weeks) or t, "link": link,
             "status": saved.get(k, {}).get("status", "not yet"), "how": saved.get(k, {}).get("how", ""), "guide_text": None, "guide_section": None}
        if md and k in GUIDE_SECTIONS:
            found = guide_section(md, *GUIDE_SECTIONS[k])
            if found:
                e["guide_section"], e["guide_text"] = found
        entries.append(e)
    coverage = {}
    for e in entries:
        c = coverage.setdefault(e["framework"], {s: 0 for s in STATUSES})
        c[e["status"]] += 1
    coverage = {k: coverage[k] for k in ("safe", "scrum", "practice") if k in coverage}  # SAFe first, Scrum as its team level
    return {"entries": entries, "statuses": list(STATUSES), "coverage": coverage, "sprint_weeks": weeks,
            "sources": {k: {"label": v[0], "url": v[1]} for k, v in SOURCES.items()}}


@router.put("/api/agile/sprint-length")
def put_sprint_length(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    weeks = body.get("weeks")
    if weeks not in WEEK_WORDS:
        raise HTTPException(400, "Sprints are one to four weeks.")
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (SPRINT_WEEKS_KEY, str(weeks)))
    return {"weeks": weeks}


@router.put("/api/agile/practice/{key}")
def put_practice(key: str, body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    require_write(viewer)
    if key not in {e[0] for e in REFERENCE}:
        raise HTTPException(404, "No such entry.")
    status = body.get("status", "not yet")
    if status not in STATUSES:
        raise HTTPException(400, "Unknown status.")
    saved = _saved(conn)
    saved[key] = {"status": status, "how": (body.get("how") or "").strip()}
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (PRACTICE_KEY, json.dumps(saved)))
    return saved[key]


# ---- the Scrum Guide itself ----
# The Scrum Guide is published under Creative Commons Attribution-ShareAlike 4.0. Rather than ship a copy in this
# MIT-licensed code, the toolkit imports the official text into your own data when you ask it to (or you paste it in),
# and shows it with its attribution and license.

GUIDE_KEY = "agile.scrum_guide"
DEFINITIONS_KEY = "agile.definitions"
GUIDE_URL = "https://scrumguides.org/scrum-guide.html"
GUIDE_LICENSE = "Creative Commons Attribution-ShareAlike 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)"
# Which section of the Scrum Guide each Scrum entry comes from, and whether its subsections belong with it.
GUIDE_SECTIONS = {
    "empiricism": ("Scrum Theory", True), "values": ("Scrum Values", False), "scrum-team": ("Scrum Team", False),
    "product-owner": ("Product Owner", False), "scrum-master": ("Scrum Master", False), "developers": ("Developers", False),
    "sprint": ("The Sprint", False), "sprint-planning": ("Sprint Planning", False), "daily-scrum": ("Daily Scrum", False),
    "sprint-review": ("Sprint Review", False), "retrospective": ("Sprint Retrospective", False),
    "product-backlog": ("Product Backlog", False), "product-goal": ("Product Backlog", False),
    "sprint-backlog": ("Sprint Backlog", False), "sprint-goal": ("Sprint Backlog", False),
    "increment": ("Increment", False), "definition-of-done": ("Increment", False),
}


def guide_section(md: str, title: str, with_sub: bool = False) -> tuple[int, str] | None:
    """A section of the imported guide by its heading: its index among the guide's sections, and its text."""
    lines = md.splitlines()
    heads = [(n, len(ln) - len(ln.lstrip("#")), ln.lstrip("#").strip()) for n, ln in enumerate(lines) if ln.startswith("## ") or ln.startswith("### ")]
    for idx, (n, level, text) in enumerate(heads):
        if text.lower() != title.lower():
            continue
        end = len(lines)
        for m, lv, _ in heads[idx + 1:]:
            if lv <= level or not with_sub:
                end = m
                break
        body = [ln for ln in lines[n + 1:end]]
        if with_sub:
            body = [("**" + ln.lstrip("#").strip() + "**") if ln.startswith("#") else ln for ln in body]
        return idx, _join([ln for ln in body if ln.strip()])
    return None


STUDY_SESSIONS = [
    "Scrum Guide, part 1: purpose, definition, theory and values",
    "Scrum Guide, part 2: the Scrum Team (Developers, Product Owner, Scrum Master)",
    "Scrum Guide, part 3: the events (Sprint, Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective)",
    "Scrum Guide, part 4: the artifacts and their commitments, and the end note",
]


def html_to_markdown(html: str) -> str:
    """Turn the guide's HTML into plain Markdown: headings, paragraphs, lists and bold, from the first heading on."""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.out, self.buf, self.started, self.skip = [], [], False, 0
            self.lists = []  # open lists, innermost last: [kind, count]
            self.pending = None  # the marker for the list item we're inside, until its first line is written

        def flush(self, prefix=""):
            text = " ".join("".join(self.buf).split())
            if text:
                if self.pending:
                    prefix, self.pending = self.pending, None
                self.out.append(prefix + text)
            self.buf = []

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "nav", "header", "footer"):
                self.skip += 1
            if tag == "h1":
                self.started = True
            if not self.started or self.skip:
                return
            if tag in ("ol", "ul"):
                self.flush()
                self.lists.append([tag, 0])
            elif tag == "li":
                self.flush()
                indent = "   " * (len(self.lists) - 1) if self.lists else ""
                if self.lists and self.lists[-1][0] == "ol":
                    self.lists[-1][1] += 1
                    self.pending = f"{indent}{self.lists[-1][1]}. "
                else:
                    self.pending = f"{indent}- "
            elif tag in ("h1", "h2", "h3", "p"):
                self.flush()
            elif tag in ("strong", "b"):
                self.buf.append("**")
            elif tag == "br":
                self.buf.append(" ")

        def handle_endtag(self, tag):
            if tag in ("script", "style", "nav", "header", "footer") and self.skip:
                self.skip -= 1
                return
            if not self.started or self.skip:
                return
            prefix = {"h1": "# ", "h2": "## ", "h3": "### "}.get(tag)
            if tag in ("strong", "b"):
                self.buf.append("**")
            elif tag in ("ol", "ul"):
                self.flush()
                if self.lists:
                    self.lists.pop()
            elif prefix is not None or tag in ("p", "li"):
                self.flush(prefix or "")

        def handle_data(self, data):
            if self.started and not self.skip:
                self.buf.append(data)

    p = P()
    p.feed(html)
    p.flush()
    import re

    lines = [re.sub(r"\*\*\s*(.*?)\s*\*\*", r"**\1**", ln) if ln.count("**") % 2 == 0 else ln.replace("**", "") for ln in p.out]
    return _join(lines)


def _is_item(line: str) -> bool:
    import re

    return bool(re.match(r"^\s*(-|\d+\.)\s", line))


def _join(lines: list[str]) -> str:
    """Blank lines between blocks, but consecutive list items stay together so they render as one list."""
    out = ""
    for n, ln in enumerate(lines):
        if n:
            prev = lines[n - 1]
            same_list = _is_item(ln) and _is_item(prev) and ln.lstrip()[0].isdigit() == prev.lstrip()[0].isdigit()
            out += "\n" if same_list else "\n\n"
        out += ln
    return out.strip()


def _sections(md: str) -> list[str]:
    return [ln.lstrip("#").strip() for ln in md.splitlines() if ln.startswith("## ") or ln.startswith("### ")]


def _definition(md: str) -> str:
    """The text of the guide's own definition section, if it has one."""
    out, inside = [], False
    for ln in md.splitlines():
        if ln.startswith("#"):
            if inside:
                break
            inside = "definition" in ln.lower()
            continue
        if inside and ln.strip():
            out.append(ln.rstrip())
    return _join(out)


def _get_json(conn, key, default):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def _put_json(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))


def fetch_official(url: str = GUIDE_URL) -> str:
    """Fetch a page. Some Python installs (notably on macOS) can't verify certificates on their own, so fall back to
    the system's curl, which uses the operating system's certificates."""
    import shutil
    import subprocess
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "beanagileorg"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.URLError:
        if not shutil.which("curl"):
            raise
        out = subprocess.run(["curl", "-fsSL", "--max-time", "20", url], capture_output=True, check=True)
        return out.stdout.decode("utf-8", "replace")


@router.get("/api/agile/guide")
def get_guide(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    g = _get_json(conn, GUIDE_KEY, None)
    defs = _get_json(conn, DEFINITIONS_KEY, [])
    if not g:
        return {"markdown": None, "official_url": GUIDE_URL, "license": GUIDE_LICENSE, "definitions": defs}
    return {**g, "sections": _sections(g["markdown"]), "definition": _definition(g["markdown"]), "official_url": GUIDE_URL,
            "license": GUIDE_LICENSE, "definitions": defs}


@router.post("/api/agile/guide/import")
def import_guide(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Fetch the official Scrum Guide from scrumguides.org into your own data, with its attribution and license."""
    require_write(viewer)
    from datetime import date

    try:
        md = html_to_markdown(fetch_official())
    except Exception as exc:  # network down, site changed
        raise HTTPException(502, f"Couldn't fetch the Scrum Guide from scrumguides.org ({exc.__class__.__name__}). Paste it in instead.") from exc
    if len(md) < 2000 or "Scrum" not in md:
        raise HTTPException(502, "The page didn't look like the Scrum Guide. Paste it in instead.")
    g = {"markdown": md, "source": GUIDE_URL, "imported_on": date.today().isoformat(), "how": "imported"}
    _put_json(conn, GUIDE_KEY, g)
    return {"sections": len(_sections(md)), "characters": len(md)}


@router.put("/api/agile/guide")
def put_guide(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Paste the guide (or a translation, or a newer edition) in yourself."""
    require_write(viewer)
    from datetime import date

    md = (body.get("markdown") or "").strip()
    if not md:
        conn.execute("DELETE FROM settings WHERE key = ?", (GUIDE_KEY,))
        return {"markdown": None}
    g = {"markdown": md, "source": (body.get("source") or "").strip() or GUIDE_URL, "imported_on": date.today().isoformat(), "how": "pasted"}
    _put_json(conn, GUIDE_KEY, g)
    return g


@router.put("/api/agile/definitions")
def put_definitions(body: dict = Body(...), viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Short definitions you want the team to see, each with its source, such as a widely quoted definition of Agile."""
    require_write(viewer)
    defs = [{k: str(d.get(k) or "").strip() for k in ("title", "text", "source")} for d in (body.get("definitions") or [])
            if isinstance(d, dict) and str(d.get("text") or "").strip()][:10]
    _put_json(conn, DEFINITIONS_KEY, defs)
    return {"definitions": defs}


@router.post("/api/agile/guide/study-plan", status_code=201)
def study_plan(viewer: Viewer = Depends(get_viewer), conn=Depends(get_conn)):
    """Four group learning sessions to read and discuss the Scrum Guide together, one part at a time."""
    require_write(viewer)
    from . import models

    have = {r["topic"] for r in conn.execute("SELECT topic FROM learning_sessions")}
    made = [models.learning_sessions.create(conn, {"topic": t}, viewer.source)["id"] for t in STUDY_SESSIONS if t not in have]
    return {"created": len(made)}
