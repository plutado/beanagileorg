"""Starter kit: generic templates, audiences, channels and cadences. Specific names stay bracketed placeholders."""

from datetime import date, timedelta

from . import models

CHANNELS = [
    ("[Placeholder team chat channel]", "chat"),
    ("[Placeholder leadership email list]", "email"),
    ("[Placeholder stakeholder meeting]", "meeting"),
]

AUDIENCES = [
    ("Leadership", "Health of delivery, risks, decisions needed, capacity", "summary first", 1),
    ("Product", "Capacity, tradeoffs, dates, what's ready to ship", "full detail", 0),
    ("Stakeholders and other departments", "What's changing for them, when, and how to get help", "what changes for them", 2),
    ("Other engineering teams", "Integration and API changes, release timing, incidents", "technical", 0),
    ("QA and design", "What's coming, what's ready, what changed", "full detail", 0),
    ("The team", "The same picture leadership sees, plus why decisions were made", "full detail", 0),
]

WEEKLY_STATUS = """**Overall: [Green / Yellow / Red]** [Placeholder: one sentence on where things stand and why]

## Milestones
| Milestone | Target date | Status | Owner | Note |
| --- | --- | --- | --- | --- |
| [Placeholder milestone] | [Placeholder date] | [Green / Yellow / Red] | [Placeholder name] | [Placeholder note] |

## Risks and issues
| Risk or issue | Impact | Owner | Next step | Due |
| --- | --- | --- | --- | --- |
| [Placeholder risk] | [Placeholder impact] | [Placeholder name] | [Placeholder next step] | [Placeholder date] |

## Decisions needed
| Decision | From whom | Needed by |
| --- | --- | --- |
| [Placeholder decision] | [Placeholder name] | [Placeholder date] |

## Shipped this week
- [Placeholder item]

## Next week
- [Placeholder item]

## My development
- [Placeholder learning goal]: [Placeholder progress and evidence]

## Asks and answers
- [Placeholder: help needed, or answers to last week's questions]

Questions or pushback: [Placeholder: how to reach me]"""

TEMPLATES = [
    ("Weekly note to leadership", "weekly note", [0],
     "[Placeholder: one line on the week]\n\n## Your top three\n- [Placeholder: your first priority, and where it stands]\n- [Placeholder: second]\n- [Placeholder: third]\n\n## What I learned\n- [Placeholder]\n\n## What I'm watching\n- [Placeholder]\n\n## What I need\n- [Placeholder]"),
    ("Weekly status", "weekly status", [0, 1, 2], WEEKLY_STATUS),
    ("Risk or incident alert", "alert", [0],
     "[Placeholder: what happened or is at risk, in one sentence]\n\n**Impact:** [Placeholder]\n\n**Owner:** [Placeholder name]\n\n**What we're doing:** [Placeholder]\n\n**Next update:** [Placeholder time]"),
    ("Release notes", "release notes", [2, 3],
     "[Placeholder: what this release changes, in one sentence]\n\n## What changes for you\n- [Placeholder]\n\n## When\n[Placeholder date and time]\n\n## Who to ask\n[Placeholder name or channel]\n\n## Walkthrough\n[Placeholder link to the walkthrough video]"),
    ("Decision announcement", "decision announcement", [2],
     "**Decision:** [Placeholder: the decision in one sentence]\n\n**Why:** [Placeholder]\n\n**The tradeoff:** [Placeholder: what we chose not to do]\n\n**Who decided:** [Placeholder name]\n\n**What changes:** [Placeholder]"),
    ("Day-30 diagnosis", "review", [0],
     "[Placeholder: the headline finding in one sentence]\n\n## What I found\n[Placeholder]\n\n## The top three problems\n1. [Placeholder]\n2. [Placeholder]\n3. [Placeholder]\n\n## The plan for the next 60 days\n- [Placeholder]"),
    ("Day-90 and quarterly review", "review", [0, 1],
     "[Placeholder: where things stand in one sentence]\n\n## Results against the scorecard\n- [Placeholder]\n\n## Metrics\n- [Placeholder]\n\n## What's next\n- [Placeholder]\n\n## What we need\n- [Placeholder]"),
    ("Team announcement", "team announcement", [5],
     "[Placeholder: the news in one sentence]\n\n**Why:** [Placeholder]\n\n**What it means for you:** [Placeholder]\n\n**Where to ask:** [Placeholder channel]"),
    ("Video pitch", "video pitch", [0, 2, 3],
     "**Script (2 to 4 minutes)**\n\n1. **Hook:** [Placeholder: the problem or opportunity in one sentence, and why now]\n2. **What the data shows:** [Placeholder: two or three facts from the toolkit: metrics, sprint results, incidents]\n3. **What I propose:** [Placeholder: the recommendation, and the options I weighed]\n4. **What it means for you:** [Placeholder: what changes for this audience]\n5. **The ask:** [Placeholder: one specific ask, and a respond-by date]\n\n**Framing** (who is this for, and what will move them?)\n- **Logos, data and reasoning:** [Placeholder: the facts and logic this audience trusts]\n- **Ethos, principles:** [Placeholder: the principle or policy that says this is right]\n- **Pathos, meaning:** [Placeholder: why it matters to them, and the story that shows it]\n\n**Counterarguments to address:** [Placeholder: the objection you expect, raised in its weak form and answered]\n\n**On screen:** [Placeholder: slides or demo steps for each beat]\n\n---\n\n**Email to send with it**\n\n[Placeholder: poster image linking to the video]\n\n- [Placeholder: summary line 1]\n- [Placeholder: summary line 2]\n- [Placeholder: summary line 3]\n\n**The ask:** [Placeholder] by [Placeholder date]. Reply here, or in the comments under the video.\n\nThe transcript is below the video for anyone who'd rather read."),
    ("Sprint review invite and recap", "stakeholder update", [2, 1],
     "[Placeholder: the sprint goal in one sentence]\n\n## What we'll show\n- [Placeholder]\n\n## Recap\n- [Placeholder]\n\n**Highlights video:** [Placeholder link]"),
]


def _next_weekday(weekday: int) -> date:
    today = date.today()
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def load_starter_kit(conn, source: str) -> dict:
    channels = [models.channels.create(conn, {"name": n, "kind": k}, source) for n, k in CHANNELS]
    audiences = [
        models.audiences.create(conn, {"name": n, "needs": needs, "detail_level": lvl, "channel_id": channels[ch]["id"]}, source)
        for n, needs, lvl, ch in AUDIENCES
    ]
    templates = {}
    for name, kind, aud, body in TEMPLATES:
        templates[name] = models.templates.create(
            conn,
            {"name": name, "type": kind, "body": body, "audience_ids": [audiences[i]["id"] for i in aud],
             "channel_id": channels[1]["id"] if aud == [0] else channels[0]["id"]},
            source,
        )
    friday = _next_weekday(4)
    cadences = [
        ("Weekly note to leadership", "weekly note", "weekly", friday, "Weekly note to leadership", True),
        ("Weekly status", "weekly status", "weekly", friday, "Weekly status", True),
        ("Sprint review invite and recap", "stakeholder update", "every two weeks", friday + timedelta(days=7), "Sprint review invite and recap", False),
        ("Quarterly review", "review", "quarterly", friday + timedelta(days=84), "Day-90 and quarterly review", False),
    ]
    for title, kind, rhythm, first, tpl, active in cadences:
        models.cadences.create(
            conn,
            {"title": title, "message_type": kind, "rhythm": rhythm, "next_due": first.isoformat(), "lead_days": 2,
             "template_id": templates[tpl]["id"], "active": active},
            source,
        )
    return {"channels": len(channels), "audiences": len(audiences), "templates": len(templates), "cadences": len(cadences)}
