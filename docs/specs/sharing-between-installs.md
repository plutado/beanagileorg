# Sharing between installs

A plan, partly built. Steps 1 to 3 below are done for role templates, SDLC policies and regression plans (Share with another manager in the toolkit), alongside the roster file and the coaching pack. Engineering managers who each run their own copy of the toolkit sometimes want to share part of what they hold: a roster, a few risks, a regression plan, an SDLC policy, the role templates they use, a team's status. They should be able to do that without ever giving each other access to their copies, and without sharing anything they didn't choose.

## Principles

1. **Each install owns its data.** Nothing is read from another install directly. Sharing happens through a **pack**: a file one manager exports and another imports.
2. **Granular by default.** Nobody shares "everything". You choose the kinds of record, then the individual records, then the fields within them. The starting selection is empty, not full.
3. **Privacy levels still hold.** A pack can never carry more than the exporter could show while presenting, unless they deliberately add private fields one by one. Some things never leave at all: notes on people, conversations, feedback, assessments, reflections, the culture log, and credentials of any kind.
4. **Look before you merge.** Importing always shows a preview of what would be added, what would change and what conflicts, and the importer decides record by record. Nothing changes until they confirm.
5. **Merging is repeatable.** Importing the same pack twice changes nothing. Importing a newer version of a pack updates only what changed, and only where the importer agrees.
6. **Everything is recorded.** Every export goes in the export log (what, how many records, a checksum). Every import goes in an import log, and each imported record remembers where it came from.

## What can be shared

Roughly in the order to build:

| Kind | Typical use | Notes |
| --- | --- | --- |
| Roster | Moving a team, a new manager taking over | Built: People → Fields → Export a roster |
| Coaching pack | Guides, tips and prompts | Built: Coaching → Packs |
| Role templates | How to judge people in a function | Shareable as written |
| SDLC stages and policies | Aligning teams on one process | Agreed policies, with their dates |
| Regression plans and the release path | Coordinating release windows and freezes | Owners as names, not links |
| Risks and decisions | A shared risk across teams | Shareable fields only; notes stay |
| Scrum of Scrums items | Dependencies between teams | Matched by item, both sides keep their own copy |
| Agile practices and their status | A Scrum of Scrums view of adoption | Status and "how we do it here" |
| Metrics and readings | Comparing trends, never people | Team-level measures only |
| Team status pack | A roll-up for a manager of managers | Already planned as "status packs back" |
| Core processes and workflow maps | Improving a cross-team process | Steps and handoffs |

Kinds that never go in a pack: assessments, influence maps and alliance plans, culture notes, trust pulses, one-on-one records, reflections, private notes on any record, settings and tokens.

## Choosing what goes in (export)

The export screen works in three steps, each narrowing the last:

1. **Kinds.** Tick the kinds of record to include. Nothing is ticked to start with.
2. **Records.** For each kind, pick records one by one, or by filter: a team, a date range, a status, a tag, the records linked to a given release or sprint. A count shows as you go.
3. **Fields.** For each kind, the shareable fields are listed and on by default; you can switch any off. Private fields are listed separately, off, each marked private, and each needs its own tick. Fields that never leave aren't listed at all.

Then a **review** shows exactly what's in the pack, record by record, before anything is written. The pack can be saved as a file, or copied.

**Links between records.** If a chosen record points at another (a risk's owner, a release's sprint, a story's feature), the review says so. You choose whether to include the linked record, include it as a name only (the default for people), or drop the link.

## Bringing it in (import and merge)

1. **Read the pack.** Check its format, version and checksum, and show who it says it's from, when, and what it contains. Refuse anything that isn't a beanagileorg pack.
2. **Match.** Each incoming record is matched against what's already here: first by its pack identity (if it came from this pack before), then by a natural key (a person's name, a guide's short name, a policy's title, a release's name), then not at all.
3. **Preview.** Group the results: new, unchanged, would change (with a field-by-field difference), and conflicts (both sides changed the same field since the last import). Each record has a choice:
   - **Add** (new records) or **skip**.
   - **Update**: take the incoming values for the fields that changed.
   - **Keep mine**: leave this record as it is.
   - **Merge fields**: choose field by field, for conflicts.
   - **Add as a copy**: keep both, the incoming one marked with where it came from.
4. **Confirm.** Apply the choices in one go. Linked records resolve to what's already here where they match; otherwise to a name, or a placeholder in [brackets], never to a guess.
5. **Record.** The import log notes the pack, who it said it was from, what was added, updated and skipped, and when. Each imported record keeps its origin ("from [pack name], [date]"), shown on the record.

## The pack format

A single JSON file:

- An envelope: `format` ("beanagileorg.pack"), `version`, `created`, an optional `from` (the exporter's chosen display name; no machine or account details), a free-text `about`, and a `checksum` of the contents.
- `kinds`: for each kind, the field list that was included, and the records.
- Each record carries a **pack identity**: a random id assigned the first time a record is exported, stored on the record, and reused on later exports, so a newer pack updates rather than duplicates.
- Links between records point at pack identities within the pack, or carry a name only.
- Dates as ISO strings; no database ids, file paths, hosts or tokens.

The roster and coaching pack formats stay readable as they are, and become kinds within the general pack.

## Safety

- Packs are plain files, moved however the managers like (a message, a shared drive). The apps never send them anywhere.
- Optionally, a pack can be signed with a passphrase both managers know, so the importer can tell it wasn't changed on the way.
- A later option, using timed sharing: one manager offers a pack for a limited time over the local network or Tailscale, and the other pulls it, read-only, with the same preview and confirmation. Still no access to the exporter's copy.

## Building it in steps

1. **Pack identity and the import log.** Add a pack identity to shareable records (a migration), an import log, and an origin field.
2. **The general export screen** with kinds, records, fields and review, starting with role templates, SDLC policies and regression plans.
3. **Import with preview and per-record choices**, starting with the same kinds.
4. **Links between records**, with name-only and placeholder handling.
5. **More kinds**, in the order of the table above, each with its own natural key and field list.
6. **Roster and coaching pack** folded in as kinds, keeping their current files readable.
7. **Signing and timed pulls.**

Each step ships with tests that export from one install and import into another, and that private and never-shared fields don't appear in any pack unless chosen.
