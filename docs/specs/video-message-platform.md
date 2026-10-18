# Video message platform spec

Design spec, October 2026. Not built yet: the toolkit and Comms studio sides (dev-sync board columns, update scripts, video pitch template) exist; the share site does not. Example values are [Placeholder]s.

## Purpose and principles

A small, self-hosted platform for sending short video messages (pitches, demos, updates) to named people, each through their own link, with a viewing log and one clear ask. It replaces many hour-long meetings with something people watch on their own time, in the sender's own words.

Principles:

- **Async first.** A video plus a three-line summary and one ask replaces a meeting wherever a decision doesn't need everyone in a room.
- **Undiluted.** People hear the proposal as the sender drafted it, not as someone retold it.
- **Grounded.** Scripts are drafted from toolkit facts: metrics, sprint results, decisions needed.
- **Pragmatic safeguards, not heavy process.** Enough protection that the right people see the right video and copies don't spread: personal links, expiring streams, a viewing log. Nothing that slows a two-minute pitch down.
- **Reuse what works.** HLS streaming with hls.js and an existing web player. This adds a gate, not a new stack.
- **Separate from personal sites.** Messages live at their own subdomain (share.beanagile.org in this project), not on anyone's personal site.

## How it works end to end

The sender makes and tracks every message on their own machine; the web-hosted gatekeeper only stores, checks and serves; each recipient sees nothing until their own link is checked.

The one public-facing step is the gate in the middle: a link and, if required, a code tied to one person, before any video plays.

## Access tiers

Every recipient gets their own link, tied to their email address; the sender picks how strictly that link is checked, per message.

| Tier | How someone gets in | What it stops | Effort for the viewer |
| --- | --- | --- | --- |
| Personal link | A unique link per recipient, made for their email. The page knows who opened it. | Casual sharing; shows who watched | One click |
| Personal link + code | The link sends a six-digit code to that recipient's email; the page opens once it's entered. A trusted browser is remembered for 30 days. | A forwarded link: someone else can't get the code | One click and a code, once a month |
| Company sign-in (later) | Sign in with a work account, if the company's identity provider allows an outside app. | Everything above, without codes | Usually none, already signed in |

For every message:

- **Expiry.** Links stop working after a date the sender sets (default 30 days).
- **View limit.** Optional cap on how many times one person can open it.
- **Revoke.** One click removes access for one person or everyone; open sessions end at the next segment request.
- **Add people later.** New recipients get new links without resending to everyone.
- **No public index.** Nothing is listed or searchable; the site's home page shows only a public placeholder.

## Video protection tiers

Once someone is through the gate, the sender picks how hard the video is to copy; Standard covers most pitches and Protected covers anything with numbers or names.

| Tier | How it works | Good for |
| --- | --- | --- |
| Standard | HLS playlist and segments served only through the gatekeeper, never from a public folder. A copied segment URL needs a valid viewing session. | Pitches, demos, team updates |
| Protected | The gatekeeper rewrites each playlist so every segment URL is signed for that viewer and expires in 5 minutes. Download and picture-in-picture are off. The viewer's name and email sit faintly over the video as a watermark. | Proposals with numbers, plans, anything sensitive |
| Locked | Full DRM through a commercial video host. The gatekeeper still controls who gets the page. | Rarely needed internally; only if a message warrants it |

No tier stops someone filming a screen with a phone; the watermark is what discourages it, because the copy shows whose link it came from.

## The share site (Drupal)

The share site is its own Drupal site: developed locally in ddev, with its design taken from an HTML template kept inside the Drupal root, and deployed to a web host with `git pull` and `drush cr`. It lives in its own private repository, not the MIT beanagileorg repo, because it carries a licensed template.

**Why Drupal fits the gate.** Drupal's private file system serves a file only after code checks access. Every playlist, segment, transcript and deck file sits under `private://`, and a small custom module decides who may have it. Nothing is served to anonymous visitors except the link-and-code pages.

**New: a custom module, `ba_share`**

| Piece | Does |
| --- | --- |
| Message content type | Title, summary, ask, respond-by, access tier, protection tier, expiry, and its parts: video, deck bundle, page, file |
| Recipient entity | Message, email, name, hashed link token, view limit, revoked date |
| Code and session handling | One-time codes by email, a 30-day trusted-browser cookie, hashed at rest |
| File access | Private-file access checks; in the Protected tier, playlists rewritten with signed, 5-minute segment URLs |
| View and reply log | Progress pings every 10 seconds, furthest point, finished, replies |
| API for the Comms studio | Token-protected routes to create messages, upload media, add or revoke recipients, and fetch views and replies |
| Watermark | The viewer's name and email over the player and transcript in the Protected tier |

**Routes**

| Path | Does |
| --- | --- |
| `/m/{token}` | Personal link: checks it, sends a code if needed, shows the watch page |
| `/m/{token}/code` | Checks the code; starts the session |
| `/system/files/...` | Private media, after `ba_share` checks the session or the signature and expiry |
| `/share/view` | Player progress pings |
| `/share/reply` | The viewer's reply to the ask |
| `/api/share/*` | For the Comms studio only |

**Email** goes through SMTP on the same domain (Drupal's mail system with SPF and DKIM set), so codes and invitations come from a consistent address.

Private files pass through PHP, which is fine for internal audiences of tens of people. If load ever grows, move media to object storage with signed URLs.

## Where it lives

One public subdomain carries everything shared outward: videos, presentations and pages, behind the same gate.

| Name | Points at | Who can reach it |
| --- | --- | --- |
| beanagile.org, www | The public project site | Anyone |
| toolkit, comms | 127.0.0.1, through a local proxy on the user's machine | Only the machine in use |
| share | The gatekeeper on a web host | Only people with a personal link |

**What share serves.** The gate doesn't care what's behind it. Each message is one of:

- **Video:** HLS with the transcript, as above.
- **Presentation:** a reveal.js deck exported from the Comms studio as a self-contained bundle (no CDN; Lottie and charts included), viewed in the browser, with speaker notes hidden.
- **Page:** a one-pager or proposal as HTML from Markdown.
- **File:** a PDF or slide export, shown in the browser and downloadable only if the sender allows.

A message can combine them, for example a two-minute video with the deck below it.

**DNS.** The DNS host manages the apex and `www` for the public site, `share` for the gatekeeper (with a Let's Encrypt certificate), and A records keeping `toolkit` and `comms` at 127.0.0.1. See [local-domain.md](../local-domain.md).

**Every subdomain is its own site.** Each public name is a separate Drupal instance with its own database, theme and repository, so a setting on one can never expose another.

The beanagileorg repository keeps only the Comms studio side of the hand-off: making HLS, uploading through the share site's API, drafting emails, and pulling back views and replies. The share site starts locally in ddev, so the hand-off is built and tested end to end on one machine before anything is deployed.

## The player

An hls.js player with a watch page around it.

- **The page:** the title, the three-line summary above the video, the ask and its respond-by date beside it, the transcript below, and a reply box.
- **Playback:** hls.js with adaptive renditions (for example 1080p, 720p, 480p), Safari's native HLS as a fallback, captions from a WebVTT file, and speed control.
- **Protected tier:** a watermark layer with the viewer's name and email, faint and slowly moving; download, the context menu and picture-in-picture turned off.
- **Progress:** a ping every 10 seconds with the furthest point reached, so the log shows who watched how much, not just who opened it.
- **Reply:** a short text answer to the ask ("Yes, go ahead", "Let's talk", or free text), stored against the recipient and sent back to the Comms studio.
- **Accessible:** keyboard controls, captions on by default where provided, a transcript for anyone who'd rather read.

**Transcript on every video.**

- **Made locally, at no cost.** A local Whisper model writes `transcript.json` (timed segments), `transcript.txt` and `transcript.vtt`, with the captions copied into the HLS folder.
- **Hallucinations filtered out.** Segments Whisper wasn't confident held speech (no-speech probability above 0.6 and low confidence) are dropped, as is repeated filler. A video with no speech says so ("No speech detected") instead of showing invented words.
- **Player.** media-chrome over hls.js: a captions button and a "Transcript (machine)" track, playback speed, and a big centred play button.
- **On the page.** A collapsible Transcript box below the video showing the line count and "click a time to jump". It's an ordered list where each line starts with a timestamp button that seeks the video and starts playing.
- **Honest about the source.** A note under the transcript names the method and date and warns that machine transcripts can mishear names and terms. For messages, the sender corrects the transcript before sending, and the note says it was reviewed.
- **For messages.** The line being spoken is highlighted as it plays; a search box jumps to matches; any line can be copied with its timestamp for a reply. The corrected text becomes the email's transcript and the written record of the proposal. In the Protected tier it carries the watermark and isn't offered as a download.

## Comments

Under the transcript, each viewer can comment. Every comment is private to the sender unless the viewer chooses to share it, because most people will want to give feedback the way they would in a one-on-one.

| Visibility | Who sees it | Default |
| --- | --- | --- |
| Just the sender | The viewer and the sender only. Replies stay in that private thread. | Yes |
| Shared with this message's viewers | Everyone who has a personal link to this message: always a small, named group, never the public | No, the viewer picks it |
| Shared, without my name | The same small group sees the comment as "A viewer"; the sender still knows who wrote it | No |

- **Tied to a moment.** A comment can be pinned to a time in the video: "Comment here" on a transcript line, or the current moment. A click on its timestamp jumps the video there.
- **The viewer stays in control.** They can edit or delete their own comments, and move one from private to shared or back. The page always shows plainly who can see each comment before it's posted.
- **Replies follow the comment.** A reply to a private comment is private to that viewer; a reply to a shared one is shared.
- **Moderation.** The sender can hide any shared comment from the group; the author still sees it, marked hidden.
- **Separate from the ask.** The one structured answer to the message's ask stays its own box; comments are for everything else.
- **Back in the toolkit.** New comments show on Today. A private comment can be saved to that person's conversations under People. Comments never appear in leadership reports or exports, and private ones are never shown in presentation mode.
- **Stored by `ba_share`** as a Comment entity: message, recipient, visibility, optional video time, text, created and edited dates, hidden flag, reply-to.

## The dev-sync board (learning culture)

The same gate, player, transcript and comments also serve a living board of the dev sync. It's a read-only view of the toolkit's dev-sync log, where every row can link to a short presentation updating it, so people follow up on their own time instead of waiting for the next meeting.

**In the toolkit (the living spreadsheet).** The dev-sync log records the topic, who raised it, owner, next action, due date, status, origin, Jira keys, and a learning flag for offers to present, plus:

- **Kind:** question, offer to present, decision needed, idea, or action.
- **Subject matter experts:** people picked from People.
- **Decision maker:** one person.
- **On the board:** a per-row switch. Only switched-on rows, and only their shareable columns, ever leave the toolkit.

**On the share site.** A board is a message of its own, sent through personal links like any other:

| Column | From the toolkit |
| --- | --- |
| Topic | The row's concern or question |
| Kind | Question, offer to present, decision, idea, action |
| Asked by | Who raised it, and when |
| Experts, Decision maker | As set in the toolkit |
| Next action, Due, Status | Kept current from the toolkit |
| Latest update | A link to the newest presentation about that row, with its date |

**From row to update.** On a dev-sync row in the toolkit, "Make an update" drafts a script from the row: what was asked, what's happened, the decision, and what's next. The sender records a short video or builds a deck, publishes it as a message, and its link lands on the row. On the board, a click on that row opens the presentation with its transcript and comments.

**Learning sessions.** Rows that are offers to present become group learning sessions in the toolkit. The recorded session is posted to the board under that row, building a searchable library of what the team has taught each other.

**Sync.** The toolkit pushes switched-on rows to the share site through its API whenever they change, and pulls back views and comments. The board never holds anything the toolkit didn't mark as shareable.

## Comms studio hand-off

The Comms studio, running locally, is where every message is made and tracked; the gatekeeper only stores and serves it.

1. **Script.** The "video pitch" template drafts a script from toolkit facts (metrics, sprint results, decisions needed), with a storyboard of slides or demo steps and a target length of 2 to 4 minutes.
2. **Record.** The sender records with their own tools; the studio takes the finished file.
3. **Transcode.** The studio runs ffmpeg locally to make HLS renditions, a poster image, a short animated preview for email, and captions. It drafts the transcript and summary with a local model where available.
4. **Upload.** Through the gatekeeper's API, with the access and protection tier, expiry and recipients picked from People.
5. **Send.** The studio drafts the email for each recipient: the preview image linking to their personal link, the three-line summary, the ask with its respond-by date, and the transcript. A matching chat post where that's the better channel. The sender sends them; nothing goes out automatically.
6. **Follow up.** Views and replies come back on a schedule. Replies can become decisions, commitments or dev-sync items in the toolkit; anyone who hasn't watched by the respond-by date shows on Today.

## Viewing log and analytics

For each message, the Comms studio shows one row per recipient, so the sender knows who has the message and who still needs a nudge.

| Column | Meaning |
| --- | --- |
| Opened | First time they opened their link |
| Watched | Furthest point reached, as a share of the video (for example 85%) |
| Finished | Watched to the end |
| Replied | Their answer to the ask, if any |
| Decided | The recorded outcome, linked to the toolkit decision or commitment |

Across messages: response rate, median time to reply, and how many meetings each pitch replaced (entered by hand). That last figure, set against the meeting-load and reschedule metrics, is the evidence for going async. The log records views for internal follow-up only; it never scores or ranks people.

## Pragmatic safeguards

The aim is to be efficient and effective with safeguards a security-minded colleague would recognise. These are on from day one:

- **Least exposure.** Unlisted, personal links only; no public pages but a placeholder; media outside the web root; links expire.
- **Know who saw what.** Every open and view is logged against a named recipient; revocation takes effect within minutes.
- **Secrets kept out of code.** The signing key, mail password and API token live in one file outside the web root, never in the repository; the repository holds no employer content.
- **Encrypted in transit.** HTTPS only, with HSTS. Session cookies are HttpOnly, Secure and SameSite.
- **Minimal personal data.** Only recipient names and email addresses, kept for 12 months after a message expires, then deleted.
- **Content discipline.** Video messages carry proposals, plans and progress. Detailed system weaknesses, personnel matters and anything under legal hold stay out, or go only to one person under the Protected tier.
- **Backups.** Nightly copy of the database and the media index to a private location; the media itself can be regenerated from the masters on the sender's machine.
- **Easy to retire.** One command exports every message and log; deleting the subdomain removes everything.

**If anyone asks how it works**, a short version to share:

> I send short video updates through a private page I host myself. Each person gets their own link, optionally confirmed with a code sent to their work email. Videos stream only through that page, expire on a date I set, and can be revoked at any time. Nothing is public or searchable, and I can see who has watched, so nobody needs a meeting just to hear an update. Happy to move it onto a company platform if you'd prefer.

## Build plan

Four stages, each usable on its own, so the first real pitch can go out after stage 2.

1. **Prototype (local).** The share site running in ddev with placeholder videos: personal links, codes printed to the console, Standard tier, viewing log. Tests for tokens, expiry and revocation.
2. **First real pitch.** Deploy to the subdomain with HTTPS and email codes; the Comms studio uploads one video and drafts the emails. Send a two-minute pitch to a few friendly recipients and watch the log.
3. **Protected tier and replies.** Signed, expiring segment URLs, the watermark, the reply box, and views and replies flowing back into the toolkit and Today.
4. **Polish.** The animated email preview, captions and transcripts drafted automatically, retention clean-up, export, and company sign-in if the identity provider allows it.

The Locked (DRM) tier is built only if a message ever needs it.

## Open decisions

- [ ] Hosting plan: shared hosting is enough for the prototype and first pitches; a VPS only if traffic or nginx signed links are needed.
- [ ] Which HTML template each Drupal site uses.
- [ ] Default access tier for new messages: personal link, or personal link plus code.
- [ ] Retention: 12 months after expiry, or shorter.
- [ ] Whether the company has its own video platform worth using instead for some audiences.
- [ ] Whether company videos may live on self-managed hosting at all; a deliberate call, made per organization.
