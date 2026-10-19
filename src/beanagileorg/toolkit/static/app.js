// Toolkit version 1 screens: Today, People, Skills and learning, Listening tour, Day-30 rollup, My development.
(function () {
  const { esc } = BA;
  // A day of the role, for when there's no confirmed start date to turn it into a real one.
  BA.roleDay = (n) => (n == null || n === "" ? "" : n < 1 ? "before day 1" : `Day ${n} · week ${Math.ceil(n / 7)}`);
  const presenting = () => BA.session.presentation;
  // Before sign-in finishes there's nothing on screen yet, so just remember the address; redraw only an open screen.
  BA.api("/api/toolkit/settings").then((s) => { if (s && s.jira_url && s.jira_url !== BA.jiraUrl) { BA.jiraUrl = s.jira_url; if (BA.session) BA.rerender(); } }).catch(() => {});

  BA.command({ label: "Add a dev-sync item", hint: "Dev-sync log", icon: "plus", run: () => BA.go("/dev-sync") });
  BA.command({ label: "Plan a one-on-one", hint: "Listening tour", icon: "plus", run: () => BA.go("/listening") });
  BA.command({ label: "Add a person", hint: "People", icon: "plus", run: () => BA.go("/people") });
  BA.command({ label: "Log a vendor conversation", hint: "Vendors", icon: "handshake", run: () => BA.go("/vendors") });
  BA.command({ label: "Write a ceremony note", hint: "Sprint notebook", icon: "notebook-pen", run: async () => {
    const s = await BA.api("/api/sprints/current");
    BA.go(s ? `/sprints/${s.id}` : "/sprints");
  } });
  BA.command({ label: "Run a retrospective", hint: "Retrospectives", icon: "refresh-ccw", run: () => BA.go("/retros") });
  BA.command({ label: "Open the PI planning board", hint: "PI planning", icon: "kanban", run: () => BA.go("/pi") });
  BA.command({ label: "Work on the 30/60/90 plans", hint: "30/60/90 plans", icon: "flag", run: () => BA.go("/plans") });
  BA.command({ label: "Assess a product, service or department", hint: "Business landscape", icon: "building-2", run: () => BA.go("/landscape/swot") });
  BA.command({ label: "Start a smoke test run", hint: "QA resources", icon: "flask-conical", run: () => BA.go("/qa/runs") });
  BA.command({ label: "Open the system map", hint: "Architecture and tools", icon: "network", run: () => BA.go("/architecture") });
  BA.command({ label: "Start onboarding a new team member", hint: "Onboarding", icon: "list-checks", run: () => BA.go("/onboarding") });
  BA.command({ label: "Open our SDLC", hint: "SDLC", icon: "git-branch", run: () => BA.go("/sdlc") });
  BA.command({ label: "Write a reflection", hint: "Coaching", icon: "notebook", run: () => BA.go("/coaching/reflect") });
  BA.command({ label: "Browse coaching guides", hint: "Coaching", icon: "compass", run: () => BA.go("/coaching") });
  BA.command({ label: "Log technical debt", hint: "Tech debt", icon: "wrench", run: () => BA.go("/debt") });
  BA.command({ label: "Find a Jira key", hint: "Search everything that references it", icon: "search", run: () => { const k = prompt("Jira key, such as ABC-123"); if (k) BA.go(`/jira/${k.trim().toUpperCase()}`); } });
  BA.command({ label: "Plan the next sprint", hint: "Sprint planning", icon: "list-ordered", run: () => BA.go("/planning/plan") });
  BA.command({ label: "Paste stories from Jira into the backlog", hint: "Sprint planning", icon: "list-ordered", run: () => BA.go("/planning") });
  BA.command({ label: "Log a Scrum of Scrums item", hint: "Scrum of Scrums", icon: "network", run: () => BA.go("/sos") });
  BA.command({ label: "Update a team's status", hint: "Teams", icon: "users-round", run: () => BA.go("/teams") });
  BA.command({ label: "Log a conversation with someone", hint: "People", icon: "users", run: () => BA.go("/people") });
  BA.command({ label: "Open the org chart", hint: "People", icon: "users", run: () => BA.go("/people/org") });
  BA.command({ label: "Note something about the culture", hint: "Culture and trust", icon: "heart-handshake", run: () => BA.go("/culture/noticing") });
  BA.command({ label: "Take the trust pulse", hint: "Culture and trust", icon: "heart-handshake", run: () => BA.go("/culture/pulse") });
  BA.command({ label: "Ask the toolkit", hint: "Ask", icon: "sparkles", run: () => { BA.go("/today"); setTimeout(() => document.querySelector(".ask-form input")?.focus(), 400); } });
  BA.command({ label: "Weekly report", hint: "Reports", icon: "file-text", run: () => BA.go("/status") });
  BA.command({ label: "Sprint report", hint: "Reports", icon: "file-text", run: () => BA.go("/status/sprint") });
  BA.command({ label: "New change request", hint: "Change requests", icon: "arrow-left-right", run: () => BA.go("/changes/new") });
  BA.command({ label: "Log something", hint: "Work log", icon: "file-text", run: () => BA.go("/status/log") });
  BA.command({ label: "Log learning time", hint: "My development", icon: "graduation-cap", run: () => BA.go("/me") });

  const RELATIONSHIPS = ["employee", "contractor", "peer", "stakeholder", "manager", "vendor"];
  const GOAL_STATUS = ["not started", "in progress", "done", "at risk"];
  const CADENCES = ["weekly", "every two weeks", "monthly", "quarterly", "once"];

  const PERSON_FIELDS = [
    { name: "name", label: "Name", required: true },
    { name: "role", label: "Role" },
    { name: "relationship", label: "Relationship", type: "select", options: RELATIONSHIPS },
    { name: "start_date", label: "Start date", type: "date" },
    { name: "location", label: "Location" },
    { name: "timezone", label: "Time zone" },
    { name: "background", label: "Background", type: "textarea", hint: "where they're from, past roles, how they joined" },
    { name: "skills", label: "Skills", type: "list", hint: "comma separated" },
    { name: "certifications", label: "Certifications", type: "list" },
    { name: "goals", label: "Goals and plans", type: "textarea" },
    { name: "wants_to_learn", label: "Wants to learn", type: "list" },
    { name: "can_teach", label: "Can teach", type: "list" },
    { name: "working_style", label: "Working style", type: "textarea", hint: "feedback, recognition, communication, focus time" },
    { name: "support_notes", label: "Support notes", type: "textarea" },
    { name: "contact", label: "Contact details" },
    { name: "active", label: "Active", type: "checkbox" },
  ];

  const INTERVIEW_FIELDS = (people) => [
    { name: "person_id", label: "Person", type: "select", numeric: true, options: people.map((p) => ({ value: p.id, label: p.name })) },
    { name: "date", label: "Date", type: "date" },
    { name: "status", label: "Status", type: "select", blank: false, options: ["planned", "done"] },
    { name: "working", label: "What's working?", type: "textarea" },
    { name: "frustrating", label: "What's frustrating?", type: "textarea" },
    { name: "change_first", label: "What would you change first?", type: "textarea" },
    { name: "dont_change", label: "What should I not change?", type: "textarea" },
    { name: "if_you_were_me", label: "If you were me, what would you focus on first?", type: "textarea" },
    { name: "systems", label: "Products and systems mentioned", type: "list", hint: "comma separated" },
    { name: "gaps", label: "Gaps", type: "textarea" },
    { name: "opportunities", label: "Opportunities", type: "textarea" },
    { name: "themes", label: "Themes", type: "list", hint: "comma separated; these roll up into the day-30 diagnosis" },
    { name: "how_answered", label: "How they answered (private)", type: "textarea", hint: "direct or evasive, takes responsibility or points fingers, whole business or one silo" },
  ];

  // ---------------------------------------------------------------- Today

  BA.view("/today", {
    title: "Today",
    async render(main) {
      const d = await BA.api("/api/today");
      if (d.hidden) {
        main.innerHTML = '<p class="empty">Today is personal, so it\'s hidden while presenting.</p>';
        return;
      }
      if (!d.people_count) {
        main.innerHTML = `<section class="card"><h2>The toolkit is empty</h2>
          <p class="quiet">Start adding people, or load placeholder data to try it out. Every placeholder value is in brackets so it can't pass for real data.</p>
          <button class="btn primary" id="seed">Load placeholder data</button></section>`;
        main.querySelector("#seed").onclick = BA.guard(async () => {
          await BA.api("/api/seed-placeholders", { method: "POST" });
          BA.toast("Placeholder data loaded.");
          BA.rerender();
        });
        return;
      }
      const taskRow = (t) => `<div class="item"><span>${esc(t.title)}</span><span class="spacer"></span>
        <span class="quiet">${BA.fmtDate(t.due)}</span><button class="btn" data-task="${t.id}">Done</button></div>`;
      const empty = (msg) => `<p class="quiet">${msg}</p>`;
      const rep = d.reports || {};
      main.innerHTML = `<div id="ask-host"></div><div class="cards">
        <section class="card log-today"><h2>Work log</h2>
          <form id="quick-log" class="row"><select name="kind" style="max-width:120px">${LOG_KINDS.filter((k) => k !== "note").concat("note").map((k) => `<option value="${k}">${esc(LOG_LABELS[k])}</option>`).join("")}</select>
            <input name="text" required placeholder="What happened? It goes into this week's report" style="flex:1;min-width:200px"><button class="btn primary" type="submit">Log</button></form>
          <p class="quiet">${rep.logged_today ? `${rep.logged_today} logged today. ` : "Nothing logged today yet. "}<a href="#/status/log">Work log</a></p>
          ${rep.weekly ? `<div class="item"><span class="pill warn">report</span><a href="#/status?week=${rep.weekly.start}">Weekly report for ${esc(rep.weekly.label.replace("Week of ", "the week of "))}</a></div>` : ""}
          ${rep.sprint ? `<div class="item"><span class="pill warn">report</span><a href="#/status/sprint?sprint=${rep.sprint.id}">Sprint ${rep.sprint.number} has ended: write its report</a></div>` : ""}</section>
        ${BA.backupWarning(d.backup)}
        ${d.accelerate && (d.accelerate.learning_late_count || d.accelerate.boss_unheld.length || d.accelerate.mentoring.length) ? `<section class="card"><h2>Getting up to speed</h2>
          ${d.accelerate.boss_unheld.length ? `<div class="item"><span class="pill warn">manager</span><a href="#/first90/mandates">Not yet discussed with your manager: ${esc(d.accelerate.boss_unheld.join(", ").toLowerCase())}</a></div>` : ""}
          ${d.accelerate.learning_late.map((q) => `<div class="item"><span class="pill">learn</span><a href="#/first90/learning">${esc(q.question)}</a></div>`).join("")}${d.accelerate.learning_late_count > d.accelerate.learning_late.length ? `<p class="quiet">and ${d.accelerate.learning_late_count - d.accelerate.learning_late.length} more open questions past their day</p>` : ""}
          ${d.accelerate.mentoring.map((m) => `<div class="item"><span class="pill">mentoring</span><a href="#/first90/mentoring">${esc(m.name || "")}: ${esc(m.next_step || "follow up")}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(m.next_on)}</span></div>`).join("")}</section>` : ""}
        ${d.mandates && (d.mandates.agree_mine || d.mandates.reviews.length) ? `<section class="card"><h2>Mandates</h2>
          ${d.mandates.agree_mine ? `<div class="item"><span class="pill warn">day ${d.mandates.agree_mine.day}</span><a href="#/first90/${d.mandates.agree_mine.id ? `mandate/${d.mandates.agree_mine.id}` : "mandates"}">${d.mandates.agree_mine.exists ? "Agree your mandate with your manager" : "Write down your mandate, then agree it with your manager"}</a></div>` : ""}
          ${d.mandates.reviews.map((m) => `<div class="item"><span class="pill">review</span><a href="#/first90/mandate/${m.id}">${m.mine ? "Your mandate" : `${esc(m.name || "")}'s mandate`}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(m.review_on)}</span></div>`).join("")}</section>` : ""}
        ${d.first90 && (d.first90.late.length || d.first90.checkpoint || d.first90.reviews.length) ? `<section class="card"><h2>First 90 days</h2>
          ${d.first90.checkpoint ? `<div class="item"><span class="pill warn">check-in</span><a href="#/first90/team">Day-${d.first90.checkpoint.day} team check-in</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(d.first90.checkpoint.due)}</span></div>` : ""}
          ${d.first90.reviews.map((c) => `<div class="item"><span class="pill">review</span><a href="#/first90/changes">Review with the team: ${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(c.review_on)}</span></div>`).join("")}
          ${d.first90.late.map((m) => `<div class="item"><span class="pill bad">late</span><a href="#/first90/team">${esc(m.person)}: ${esc(m.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(m.due)}</span></div>`).join("")}</section>` : ""}
        ${d.changes && (d.changes.waiting.length || d.changes.untold.length) ? `<section class="card"><h2>Change requests</h2>
          ${d.changes.waiting.map((c) => `<div class="item"><span class="pill ${c.urgency === "emergency" ? "bad" : "warn"}">decide</span><a href="#/changes/${c.id}">${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${c.days ? `${c.days} day${c.days === 1 ? "" : "s"} waiting` : "today"}</span></div>`).join("")}
          ${d.changes.untold.map((c) => `<div class="item"><span class="pill">tell them</span><a href="#/changes/${c.id}">${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${esc(c.decision)}</span></div>`).join("")}</section>` : ""}
        <section class="card"><h2>Overdue</h2>${d.overdue_tasks.map(taskRow).join("") || empty("Nothing overdue.")}</section>
        <section class="card"><h2>Dev-sync items overdue</h2>${
          d.overdue_actions.map((a) => `<div class="item"><a href="#/dev-sync/${a.id}">${esc(a.concern)}</a><span class="spacer"></span><span class="quiet">${esc(a.owner_name || "")} · ${BA.fmtDate(a.due)}</span></div>`).join("") ||
          empty("Nothing overdue in the dev-sync log.")
        }</section>
        <section class="card"><h2>Vendors</h2>${
          [
            ...d.vendor_renewals.map((v) => `<div class="item"><span class="pill ${v.days_left <= 14 ? "bad" : "warn"}">renews in ${v.days_left} days</span><a href="#/vendors/${v.id}">${esc(v.name)}</a></div>`),
            ...d.vendor_concerns.map((c) => `<div class="item"><span class="pill">concern</span><a href="#/vendors/${c.vendor_id}">${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(c.due)}</span></div>`),
          ].join("") || empty("No renewals or vendor concerns coming up.")
        }</section>
        ${d.culture && (d.culture.standard || d.culture.unaddressed.length || d.culture.follow_ups.length || d.culture.pulse_due) ? `<section class="card culture-today"><h2>Culture and trust</h2>
          ${d.culture.standard ? `<blockquote class="standard-quote">${esc(d.culture.standard.text)}</blockquote>` : ""}
          ${d.culture.unaddressed.map((o) => `<div class="item"><span class="pill bad">unaddressed</span><a href="#/culture/noticing">${esc(o.title)}</a><span class="spacer"></span><span class="quiet">noticed ${BA.fmtDate(o.date)}</span></div>`).join("")}
          ${d.culture.follow_ups.map((o) => `<div class="item"><span class="pill warn">follow up</span><a href="#/culture/noticing">${esc(o.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(o.follow_up)}</span></div>`).join("")}
          ${d.culture.pulse_due ? '<div class="item"><span class="pill">pulse</span><a href="#/culture/pulse">Time for a trust pulse</a></div>' : ""}</section>` : ""}
        ${d.people_due && d.people_due.neighbors && d.people_due.neighbors.length ? `<section class="card"><h2>Meet them before an incident</h2>
          <p class="quiet">People named on your systems you haven't had a conversation with yet. Better to meet now than in the middle of an outage.</p>
          ${d.people_due.neighbors.map((n) => `<div class="item"><a href="#/people/${n.id}">${esc(n.name)}</a><span class="spacer"></span><span class="quiet">${esc(n.systems.join(", "))}</span></div>`).join("")}</section>` : ""}
        ${d.people_due && d.people_due.sideways ? `<section class="card"><h2>Peers</h2>
          ${d.people_due.sideways.top_heavy ? `<p>In the last 30 days you had <b>${d.people_due.sideways.up}</b> conversation${d.people_due.sideways.up === 1 ? "" : "s"} up your management chain and <b>${d.people_due.sideways.sideways}</b> with peers. Peers will make or break most of what you're trying to change.</p>` : ""}
          ${d.people_due.sideways.quiet.map((q) => `<div class="item"><span class="pill warn">quiet</span><a href="#/people/${q.id}">${esc(q.name)}</a><span class="spacer"></span><span class="quiet">${q.days_since == null ? "no conversation yet" : `${q.days_since} days`}</span></div>`).join("")}
          <p><a href="#/people/balance">Relationship balance</a></p></section>` : ""}
        ${d.people_due && (d.people_due.check_ins.length || d.people_due.key_dates.length || d.people_due.meetings.length || (d.people_due.i_owe || []).length || (d.people_due.they_owe_late || []).length) ? `<section class="card"><h2>People</h2>
          ${(d.people_due.i_owe || []).map((c) => `<div class="item"><span class="pill ${c.late ? "bad" : "warn"}">I owe</span><a href="#/people/${c.person_id}">${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${esc(c.name)} · ${BA.fmtDate(c.due)}</span></div>`).join("")}
          ${(d.people_due.they_owe_late || []).map((c) => `<div class="item"><span class="pill">follow up</span><a href="#/people/${c.person_id}">${esc(c.title)}</a><span class="spacer"></span><span class="quiet">${esc(c.name)} · was due ${BA.fmtDate(c.due)}</span></div>`).join("")}
          ${d.people_due.meetings.map((m) => `<div class="item"><span class="pill">meeting</span><a href="#/people/${m.id}">${esc(m.name)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(m.date)}</span></div>`).join("")}
          ${d.people_due.check_ins.map((c) => `<div class="item"><span class="pill warn">check in</span><a href="#/people/${c.id}">${esc(c.name)}</a><span class="spacer"></span><span class="quiet">last ${c.days_since == null ? "never" : c.days_since + " days ago"} · every ${c.cadence_days}</span></div>`).join("")}
          ${d.people_due.key_dates.map((k) => `<div class="item"><span class="pill">${esc(k.label)}</span><a href="#/people/${k.id}">${esc(k.name)}</a><span class="spacer"></span><span class="quiet">${k.days === 0 ? "today" : "in " + k.days + " days"}</span></div>`).join("")}</section>` : ""}
        ${d.sos_due && d.sos_due.length ? `<section class="card"><h2>Scrum of Scrums</h2>${d.sos_due.map((x) => `<div class="item">${x.overdue ? '<span class="pill bad">overdue</span>' : ""}<a href="#/sos">${esc(x.question)}</a><span class="spacer"></span><span class="quiet">${esc(x.owner || "no owner")} · ${BA.fmtDate(x.due)}</span></div>`).join("")}</section>` : ""}
        ${d.planning_due && d.planning_due.length ? `<section class="card"><h2>Sprint planning</h2>${d.planning_due.map((p) => `<div class="item"><a href="#/planning/${p.sprint_id}">Plan sprint ${p.number}</a><span class="spacer"></span><span class="quiet">starts ${BA.fmtDate(p.start_date)} · ${p.ready_stories} ready stories, ${p.ready_points} points</span></div>`).join("")}</section>` : ""}
        ${d.debt_due && d.debt_due.length ? `<section class="card"><h2>Technical debt</h2>${d.debt_due.map((x) => `<div class="item"><span class="pill ${x.kind === "deadline" ? "warn" : ""}">${x.kind === "deadline" ? "needed by" : "revisit"}</span><a href="#/debt">${esc(x.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(x.when)}</span></div>`).join("")}</section>` : ""}
        ${d.onboarding_due.length ? `<section class="card"><h2>Onboarding</h2>${d.onboarding_due.map((o) => `<div class="item">${o.overdue ? '<span class="pill bad">overdue</span>' : ""}<a href="#/onboarding/${o.onboarding_id}">${esc(o.title)}</a><span class="spacer"></span><span class="quiet">${esc(o.person_name)} · ${esc(o.owner_role)} · ${BA.fmtDate(o.due)}</span></div>`).join("")}</section>` : ""}
        <section class="card"><h2>Due in the next 7 days</h2>${d.tasks_due_soon.map(taskRow).join("") || empty("Nothing due this week.")}</section>
        <section class="card"><h2>Obligations</h2>${
          d.obligations_due
            .map((o) => `<div class="item"><span>${esc(o.title)}</span><span class="spacer"></span><span class="quiet">${BA.fmtDate(o.next_due)}</span>
              <button class="btn" data-obligation="${o.id}">Done</button></div>`)
            .join("") || empty("No obligations due this week.")
        }</section>
        <section class="card"><h2>One-on-ones this week</h2>${
          d.upcoming_interviews
            .map((i) => `<div class="item"><a href="#/listening/${i.id}">${esc(i.person_name || "[No person set]")}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(i.date)}</span></div>`)
            .join("") || empty("None scheduled this week.")
        }</section>
        <section class="card"><h2>Learning goals at risk</h2>${
          d.goals_at_risk.map((g) => `<div class="item"><a href="#/me">${esc(g.goal)}</a></div>`).join("") || empty("None at risk.")
        }</section></div>`;
      BA.askBox(main.querySelector("#ask-host"), { placeholder: "Ask the toolkit, such as: what's overdue, who haven't I talked to, what decisions are open?" });
      const ql = main.querySelector("#quick-log");
      ql.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(ql);
        await BA.api("/api/log-entries", { method: "POST", body: { date: BA.today(), kind: f.get("kind"), text: f.get("text") } });
        BA.toast("Logged.");
        BA.rerender();
      });
      main.querySelectorAll("[data-task]").forEach((b) => {
        b.onclick = BA.guard(async () => {
          await BA.api(`/api/tasks/${b.dataset.task}`, { method: "PATCH", body: { status: "done" } });
          BA.rerender();
        });
      });
      main.querySelectorAll("[data-obligation]").forEach((b) => {
        b.onclick = BA.guard(async () => {
          await BA.api(`/api/obligations/${b.dataset.obligation}/done`, { method: "POST" });
          BA.rerender();
        });
      });
    },
  });

  // ---------------------------------------------------------------- People

  // ---- People: a private CRM ----

  const INFLUENCE = ["low", "medium", "high"];
  const STANCE = ["champion", "supporter", "neutral", "skeptic", "blocker"];
  const STANCE_TONES = { champion: "good", supporter: "good", neutral: "", skeptic: "warn", blocker: "bad" };
  const INTERACTION_KINDS = ["one-on-one", "meeting", "call", "message", "conversation", "other"];
  const MOODS = ["great", "good", "mixed", "tense", "difficult"];
  const FIELD_LABELS = { start_date: "Start date", location: "Location", timezone: "Time zone", background: "Background", skills: "Skills", certifications: "Certifications", goals: "Goals and plans",
    wants_to_learn: "Wants to learn", can_teach: "Can teach", working_style: "Working style", support_notes: "Support notes", contact: "Contact details", tags: "Tags", cadence_days: "Check-in cadence",
    influence: "Influence", stance: "Stance", communication: "How they like to communicate", motivations: "What motivates them", personal_context: "Personal context",
    things_to_remember: "Things to remember", key_dates: "Key dates", next_meeting: "Next meeting", manager_id: "Reports to", offer_them: "What I can offer them", need_from_them: "What I need from them", expects_from_me: "What they expect from me", advice: "Advice I go to them for", insight: "Insight they bring", change_style: "Style when leading change" };
  const peopleTabs = (active) => `<nav class="tabs">${[["", "People"], ["org", "Org chart"], ["balance", "Balance"], ["fields", "Fields"]].map(([k, l]) => `<a href="#/people${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${l}</a>`).join("")}</nav>`;
  const revealed = (id) => { try { return sessionStorage.getItem(`ba-reveal-${id}`) === "1"; } catch { return false; } };
  const masked = (id, label, html) => `<div class="sensitive${revealed(id) ? " shown" : ""}"><div class="sensitive-head"><b>${esc(label)}</b><span class="spacer"></span>
      <button type="button" class="link-btn" data-reveal>${revealed(id) ? "Hide" : "Show"}</button></div><div class="sensitive-body">${html}</div></div>`;
  const ago = (days) => (days == null ? "never" : days === 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`);

  BA.view("/people", {
    title: "People",
    async render(main, param) {
      if (param === "org") return renderOrgChart(main);
      if (param === "fields") return renderPeopleFields(main);
      if (param === "balance") return renderBalance(main);
      if (param) return renderPerson(main, Number(param));
      const [d, rep] = await Promise.all([BA.api("/api/people/overview"), BA.api("/api/people/reports")]);
      const ro = presenting();
      const f = (() => { try { return JSON.parse(sessionStorage.getItem("ba-people-filter") || "{}"); } catch { return {}; } })();
      const tags = [...new Set(d.people.flatMap((p) => p.tags || []))].sort();
      const shown = d.people.filter((p) => (f.inactive || p.active) && (!f.rel || p.relationship === f.rel) && (!f.tag || (p.tags || []).includes(f.tag)) && (!f.due || p.due) && (!f.ph || p.placeholder));
      const youCard = !d.private ? "" : rep.me == null
        ? `<section class="card"><h2>You and your reports</h2><p class="quiet">Pick your own record, so anyone whose Reports to is you shows up here as a direct report, with commitments, goals and feedback.</p>
            ${ro ? "" : `<div class="row"><select id="me-pick" style="max-width:260px"><option value="">Which of these people is you?</option>${d.people.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("")}</select></div>`}</section>`
        : `<section class="card"><div class="row"><h2>Your direct reports</h2><span class="spacer"></span><a href="#/people/${rep.me}" class="quiet">your page</a></div>${rep.reports.length
            ? `<div class="tablewrap"><table class="data"><thead><tr><th>Name</th><th>Last talked</th><th>I owe</th><th>They owe</th><th>Goals</th><th>Feedback to share</th></tr></thead><tbody>${rep.reports.map((r) => `<tr class="clickable" data-id="${r.id}">
                <td><b>${esc(r.name)}</b><div class="quiet">${esc(r.role || "")}</div></td><td>${ago(r.days_since)}${r.next_meeting ? `<div class="quiet">next ${BA.fmtDate(r.next_meeting)}</div>` : ""}</td>
                <td>${r.i_owe || ""}</td><td>${r.they_owe || ""}${r.late ? ` <span class="pill bad">${r.late} late</span>` : ""}</td><td>${r.goals || ""}</td><td>${r.unshared ? `<span class="pill warn">${r.unshared}</span>` : ""}</td></tr>`).join("")}</tbody></table></div>`
            : '<p class="quiet">No one reports to you yet. Set <b>Reports to</b> on your reports\' Details tabs.</p>'}</section>`;
      main.innerHTML = `${peopleTabs("")}${youCard}
        ${d.private ? `<div class="row"><select id="pf-rel" style="max-width:180px"><option value="">Every relationship</option>${opts(RELATIONSHIPS, f.rel)}</select>
          ${tags.length ? `<select id="pf-tag" style="max-width:180px"><option value="">Every tag</option>${opts(tags, f.tag)}</select>` : ""}
          <label class="check"><input type="checkbox" id="pf-due"${f.due ? " checked" : ""}> Due for a check-in</label><label class="check"><input type="checkbox" id="pf-inactive"${f.inactive ? " checked" : ""}> Show inactive</label>${d.people.some((p) => p.placeholder) ? `<label class="check"><input type="checkbox" id="pf-ph"${f.ph ? " checked" : ""}> Placeholders only</label>` : ""}</div>` : ""}
        ${d.people.some((p) => p.placeholder) && !ro ? `<p class="quiet ph-note"><span class="pill warn">placeholder</span> ${d.people.filter((p) => p.placeholder).length} people are stand-ins until you know who they are. Open one and give it the real name on Details; the placeholder mark clears itself, and everything you've recorded stays.</p>` : ""}
        <div class="tablewrap"><table class="data"><thead><tr><th>Name</th><th>Role</th><th>Relationship</th>${d.private ? "<th>Last contact</th><th>Follow-ups</th>" : ""}</tr></thead><tbody>${
          shown.map((p) => `<tr class="clickable" data-id="${p.id}"><td><b>${esc(p.name)}</b>${d.private && (p.tags || []).length ? ` ${BA.chips(p.tags)}` : ""}${p.active ? "" : ' <span class="pill">inactive</span>'}${p.placeholder ? ' <span class="pill warn">placeholder</span>' : ""}</td>
            <td>${esc(p.role || "")}${p.manager_name ? `<div class="quiet">reports to ${esc(p.manager_name)}</div>` : ""}</td><td>${esc(p.relationship || "")}</td>
            ${d.private ? `<td>${p.due ? '<span class="pill warn">due</span> ' : ""}${ago(p.days_since)}${p.next_meeting ? `<div class="quiet">next ${BA.fmtDate(p.next_meeting)}</div>` : ""}</td><td>${p.open_follow_ups || ""}</td>` : ""}</tr>`).join("") ||
          '<tr><td colspan="5" class="empty">No one matches.</td></tr>'}</tbody></table></div>
        ${ro ? "" : `<section class="card" style="margin-top:16px"><h2>Add a person</h2><form id="add" class="grid2">${BA.form(PERSON_FIELDS.slice(0, 3))}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form></section>`}`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/people/${tr.dataset.id}`)));
      const mePick = main.querySelector("#me-pick");
      if (mePick) mePick.onchange = BA.guard(async () => { if (!mePick.value) return; await BA.api("/api/people/me", { method: "PUT", body: { person_id: Number(mePick.value) } }); BA.rerender(); });
      const save = () => { sessionStorage.setItem("ba-people-filter", JSON.stringify({ rel: main.querySelector("#pf-rel")?.value || "", tag: main.querySelector("#pf-tag")?.value || "", due: !!main.querySelector("#pf-due")?.checked, inactive: !!main.querySelector("#pf-inactive")?.checked, ph: !!main.querySelector("#pf-ph")?.checked })); BA.rerender(); };
      main.querySelectorAll("#pf-rel, #pf-tag, #pf-due, #pf-inactive, #pf-ph").forEach((el) => (el.onchange = save));
      const add = main.querySelector("#add");
      if (add) add.onsubmit = BA.guard(async (e) => { e.preventDefault(); const rec = await BA.api("/api/people", { method: "POST", body: BA.readForm(add, PERSON_FIELDS.slice(0, 3)) }); BA.go(`/people/${rec.id}`); });
    },
  });

  async function renderBalance(main) {
    let days = 30;
    try { days = Number(sessionStorage.getItem("ba-balance-days")) || 30; } catch {}
    const d = await BA.api(`/api/people/balance?days=${days}`);
    if (d.hidden) { main.innerHTML = `${peopleTabs("balance")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const labels = { up: ["Up", "your manager and their chain"], down: ["Down", "your reports and their teams"], sideways: ["Sideways", "peers"], outward: ["Outward", "stakeholders, vendors and others"] };
    const total = Object.values(d.counts).reduce((a, b) => a + b, 0);
    const delta = (k) => { const n = d.counts[k] - d.previous[k]; return n ? `<span class="quiet">${n > 0 ? "+" : ""}${n} vs the ${d.days} days before</span>` : `<span class="quiet">same as before</span>`; };
    main.innerHTML = `${peopleTabs("balance")}
      ${d.has_me ? "" : '<section class="card"><p>Pick your own record ("This is me") and set who you report to, so the toolkit knows who is up, down and sideways.</p></section>'}
      <section class="card"><div class="row"><h2>Where your conversations go</h2><span class="spacer"></span><select id="bal-days" style="max-width:150px">${[14, 30, 60, 90].map((n) => `<option value="${n}"${n === d.days ? " selected" : ""}>Last ${n} days</option>`).join("")}</select></div>
        <p class="quiet">Conversations logged under People, counted once for each direction they touch. A new leader tends to spend too much time upward; peers decide whether most of what you're changing will stick.</p>
        ${total ? `<div class="balance-bar">${["up", "down", "sideways", "outward"].map((k) => d.counts[k] ? `<span class="b-${k}" style="flex:${d.counts[k]}" title="${labels[k][0]}: ${d.counts[k]}">${labels[k][0]}</span>` : "").join("")}</div>` : ""}
        <div class="stat-row">${["up", "down", "sideways", "outward"].map((k) => `<div class="b-tile b-${k}-tile"><b>${d.counts[k]}</b><span>${labels[k][0]}: ${labels[k][1]}</span>${delta(k)}</div>`).join("")}</div>
        ${d.top_heavy ? `<p class="callout warn">More of your conversations went up than sideways. Pick one peer from the list below and set up a conversation this week.</p>` : d.counts.sideways ? '<p class="quiet">Sideways is holding its own.</p>' : ""}</section>
      <section class="card"><h2>Peers</h2><p class="quiet">Quietest first. Mark someone as a peer under their Details to see them here. Write down what you can offer each one and what you need from them: peer relationships run on exchange.</p>
        ${d.peers.length ? `<div class="tablewrap"><table class="data"><thead><tr><th>Peer</th><th>Influence</th><th>Last talked</th><th>What I can offer</th><th>What I need</th></tr></thead><tbody>${d.peers.map((p) => `<tr class="clickable" data-id="${p.id}">
            <td><b>${esc(p.name)}</b>${p.placeholder ? ' <span class="pill warn">placeholder</span>' : ""}<div class="quiet">${esc(p.role || "")}</div></td><td>${esc(p.influence || "")}${p.stance ? `<div class="quiet">${esc(p.stance)}</div>` : ""}</td>
            <td>${p.quiet ? '<span class="pill warn">quiet</span> ' : ""}${ago(p.days_since)}</td><td class="quiet">${esc((p.offer_them || "").slice(0, 90)) || "–"}</td><td class="quiet">${esc((p.need_from_them || "").slice(0, 90)) || "–"}</td></tr>`).join("")}</tbody></table></div>`
          : '<p class="quiet">No peers yet. Add the managers and leads at your level under People, with relationship "peer".</p>'}</section>`;
    main.querySelector("#bal-days").onchange = (e) => { try { sessionStorage.setItem("ba-balance-days", e.target.value); } catch {} BA.rerender(); };
    main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/people/${tr.dataset.id}`)));
  }

  async function renderOrgChart(main) {
    const d = await BA.api("/api/people/org-chart");
    const node = (n) => `<li><div class="org-node"><a href="#/people/${n.id}"><b>${esc(n.name)}</b></a>${n.role ? `<span class="quiet">${esc(n.role)}</span>` : ""}<span class="spacer"></span>
        ${n.department ? `<span class="pill">${esc(n.department)}</span>` : ""}${n.children.length ? `<span class="quiet">${n.children.length} report${n.children.length === 1 ? "" : "s"}</span>` : ""}</div>
        ${n.children.length ? `<ul>${n.children.map(node).join("")}</ul>` : ""}</li>`;
    main.innerHTML = `${peopleTabs("org")}
      <p class="quiet">Reporting lines, from each person's <b>Reports to</b>. Click anyone to open their page: title, location, contact details, conversations and follow-ups. Departments are in the <a href="#/landscape/org">business landscape</a>.</p>
      <section class="card">${d.roots.length ? `<ul class="org-tree">${d.roots.map(node).join("")}</ul>` : '<p class="quiet">No one yet.</p>'}
        ${d.with_manager ? "" : '<p class="quiet">Nobody has a manager set yet, so everyone sits at the top. Set <b>Reports to</b> on each person\'s Details tab.</p>'}</section>`;
  }

  async function renderPeopleFields(main) {
    const l = await BA.api("/api/people/layout");
    const ro = presenting();
    main.innerHTML = `${peopleTabs("fields")}
      <section class="card"><h2>Which fields to show</h2><p class="quiet">Untick the fields you don't use; they disappear from every person's page and form. Nothing already written is deleted, and you can turn a field back on any time. Sensitive fields (marked) are masked on the page until you choose to show them.</p>
        <form id="layout"><div class="case-picks">${l.optional.map((f) => `<label class="check"><input type="checkbox" name="show" value="${f}"${l.hidden.includes(f) ? "" : " checked"}${ro ? " disabled" : ""}> ${esc(FIELD_LABELS[f] || f)}${l.sensitive.includes(f) ? ' <span class="pill warn">sensitive</span>' : ""}</label>`).join("")}</div>
        ${ro ? "" : '<div class="actions"><button class="btn primary" type="submit">Save</button></div>'}</form></section>
      ${ro ? "" : `<section class="card"><h2>Import a roster</h2><p class="quiet">Add a whole team at once from a roster file: people, who reports to whom, who's on your team, and which record is you. Stand-ins in [brackets] are marked as placeholders. Anyone already here with the same name is left alone, so importing twice adds nothing.</p>
        <div class="row"><input type="file" id="roster-file" accept=".json,application/json"></div><textarea id="roster-text" rows="6" class="mono" placeholder='{"me": "me", "people": [{"key": "me", "name": "[Me]"}, {"key": "a", "name": "[Engineer 1]", "relationship": "employee", "reports_to": "me", "on_team": true}]}'></textarea>
        <div class="actions"><button class="btn primary" id="roster-go">Import</button></div></section>`}`;
    const rf = main.querySelector("#roster-file");
    if (rf) {
      rf.onchange = async () => { if (rf.files[0]) main.querySelector("#roster-text").value = await rf.files[0].text(); };
      main.querySelector("#roster-go").onclick = BA.guard(async () => {
        let body;
        try { body = JSON.parse(main.querySelector("#roster-text").value); } catch { throw new Error("That isn't valid roster JSON."); }
        const r = await BA.api("/api/people/roster", { method: "POST", body });
        BA.toast(`Added ${r.created.length}${r.reused.length ? `, ${r.reused.length} already here` : ""}.`);
        BA.go("/people");
      });
    }
    const form = main.querySelector("#layout");
    if (!ro) form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const showing = new FormData(form).getAll("show");
      await BA.api("/api/people/layout", { method: "PUT", body: { hidden: l.optional.filter((f) => !showing.includes(f)) } });
      BA.toast("Saved.");
    });
  }

  function commitmentsCard(d, p) {
    const first = esc(p.name.split(" ")[0]);
    const today = BA.today();
    const row = (c) => `<div class="item commitment${c.status !== "open" ? " done" : ""}" data-commit="${c.id}"><label class="check"><input type="checkbox" data-done${c.status === "done" ? " checked" : ""}> <span>${esc(c.title)}</span></label>
        ${BA.issueKeys(c.jira_keys)}<span class="spacer"></span>${c.due ? `<span class="${c.status === "open" && c.due < today ? "pill bad" : "quiet"}">${BA.fmtDate(c.due)}</span>` : ""}${c.status === "done" ? `<span class="quiet">done ${BA.fmtDate(c.done_on)}</span>` : ""}
        <button class="icon-btn" type="button" data-del-commit title="Delete">${BA.icon("x")}</button></div>`;
    const list = (dir) => d.commitments.filter((c) => c.direction === dir).map(row).join("") || '<p class="quiet">Nothing open.</p>';
    return `<section class="card"><h2>Commitments</h2><div class="grid2"><div><h3>I owe ${first}</h3>${list("mine")}</div><div><h3>${first} owes me</h3>${list("theirs")}</div></div>
      <form id="add-commit" class="row" style="margin-top:8px"><select name="direction" style="max-width:160px"><option value="mine">I'll do</option><option value="theirs">${first} will do</option></select>
        <input name="title" required placeholder="What, specifically" style="flex:1;min-width:220px"><input type="date" name="due" style="max-width:160px"><button class="btn" type="submit">Add</button></form></section>`;
  }

  function wireCommitments(box, personId, again) {
    const add = box.querySelector("#add-commit");
    if (add) add.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(add); await BA.api("/api/commitments", { method: "POST", body: { person_id: personId, direction: fd.get("direction"), title: fd.get("title"), due: fd.get("due") || null, created_on: BA.today() } }); again(); });
    box.querySelectorAll("[data-commit]").forEach((row) => {
      row.querySelector("[data-done]").onchange = BA.guard(async (e) => { await BA.api(`/api/commitments/${row.dataset.commit}`, { method: "PATCH", body: { status: e.target.checked ? "done" : "open" } }); again(); });
      row.querySelector("[data-del-commit]").onclick = BA.guard(async () => { if (!confirm("Delete this commitment? Marking it done keeps the record.")) return; await BA.api(`/api/commitments/${row.dataset.commit}`, { method: "DELETE" }); again(); });
    });
  }

  async function renderPerson(main, id, tab) {
    const [d, layout, people] = await Promise.all([BA.api(`/api/people/${id}/crm`), BA.api("/api/people/layout"), BA.api("/api/people")]);
    const p = d.person;
    document.getElementById("view-title").textContent = p.name;
    const ro = presenting();
    const show = (f) => !layout.hidden.includes(f);
    const sens = (f) => layout.sensitive.includes(f);
    let current = tab || sessionStorage.getItem("ba-person-tab") || "overview";
    if (current === "manager" && !d.is_report) current = "overview";
    const tabs = `<nav class="tabs">${[["overview", "Overview"], ["conversations", "Conversations"], ...(d.is_report ? [["manager", "Manager"]] : []), ["timeline", "Timeline"], ["details", "Details"]].filter(([k]) => !ro || k === "overview")
      .map(([k, l]) => `<a href="#/people/${id}" data-ptab="${k}" class="${k === current ? "active" : ""}">${l}</a>`).join("")}</nav>`;
    const fact = (f, label, val) => (show(f) && val ? `<div><span class="quiet">${esc(label)}</span> ${val}</div>` : "");
    const header = `<section class="card"><div class="row"><h2>${esc(p.name)}</h2>${p.active === false ? '<span class="pill">inactive</span>' : ""}${p.placeholder ? '<span class="pill warn" title="A stand-in until you know who this is. Give it the real name on Details.">placeholder</span>' : ""}<span class="spacer"></span>
        ${p.stance && show("stance") ? tonePill(p.stance, STANCE_TONES) : ""}${p.influence && show("influence") ? `<span class="pill">${esc(p.influence)} influence</span>` : ""}</div>
      <div class="facts">${p.role ? `<div><span class="quiet">Title</span> ${esc(p.role)}</div>` : ""}${p.relationship ? `<div><span class="quiet">Relationship</span> ${esc(p.relationship)}</div>` : ""}
        ${p.manager_id && show("manager_id") ? `<div><span class="quiet">Reports to</span> <a href="#/people/${p.manager_id}">${esc(p.manager_name || "")}</a></div>` : ""}
        ${p.department_name ? `<div><span class="quiet">Department</span> ${esc(p.department_name)}</div>` : ""}
        ${fact("location", "Location", esc(p.location || ""))}${fact("timezone", "Time zone", esc(p.timezone || ""))}${fact("contact", "Contact", esc(p.contact || ""))}${fact("start_date", "Started", BA.fmtDate(p.start_date))}</div>
      ${(p.tags || []).length && show("tags") ? `<p>${BA.chips(p.tags)}</p>` : ""}
      ${d.reports.length ? `<p class="quiet">Reports: ${d.reports.map((r) => `<a href="#/people/${r.id}">${esc(r.name)}</a>`).join(", ")}</p>` : ""}
      ${d.teams.length ? `<p class="quiet">Teams: ${d.teams.map((t) => `<a href="#/teams/${t.id}">${esc(t.name)}</a> (${t.as.join(", ")})`).join(" · ")}</p>` : ""}</section>`;
    if (ro) {
      main.innerHTML = `<p><a href="#/people">All people</a></p>${header}`;
      return;
    }
    main.innerHTML = `<p><a href="#/people">All people</a> · <a href="#/people/org">Org chart</a></p>${header}${tabs}<div id="ptab"></div>`;
    main.querySelectorAll("[data-ptab]").forEach((a) => (a.onclick = (e) => { e.preventDefault(); sessionStorage.setItem("ba-person-tab", a.dataset.ptab); renderPerson(main, id, a.dataset.ptab); }));
    const box = main.querySelector("#ptab");
    const wireReveal = () => box.querySelectorAll("[data-reveal]").forEach((b) => (b.onclick = () => {
      const on = !revealed(id);
      try { sessionStorage.setItem(`ba-reveal-${id}`, on ? "1" : "0"); } catch {}
      box.querySelectorAll(".sensitive").forEach((s) => s.classList.toggle("shown", on));
      box.querySelectorAll("[data-reveal]").forEach((x) => (x.textContent = on ? "Hide" : "Show"));
    }));

    if (current === "overview") {
      const h = d.health;
      const md = (f) => (p[f] ? BA.md(p[f]) : "");
      const block = (f) => (show(f) && p[f] ? (sens(f) ? masked(id, FIELD_LABELS[f] || f, md(f)) : `<h3>${esc(FIELD_LABELS[f] || f)}</h3>${md(f)}`) : "");
      const keyDates = ((p.key_dates || {}).dates || []);
      box.innerHTML = `<div class="cards">
          <section class="card"><h2>Relationship</h2><p>Last contact: <b>${ago(h.days_since)}</b>${h.cadence_days ? ` · check in every ${h.cadence_days} days` : ""}${h.due ? ' <span class="pill warn">due for a check-in</span>' : ""}</p>
            ${h.next_meeting ? `<p>Next meeting: ${BA.fmtDate(h.next_meeting)}</p>` : ""}
            ${d.upcoming_dates.length ? `<p>${d.upcoming_dates.map((x) => `<span class="pill">${esc(x.label)} ${x.days === 0 ? "today" : "in " + x.days + " days"}</span>`).join(" ")}</p>` : ""}
            <button class="btn primary" type="button" id="log-talk">${BA.icon("plus")} Log a conversation</button>
            ${d.is_me ? '<p class="quiet">This is you.</p>' : ""}</section>
          <section class="card"><h2>Before you meet</h2>
            ${d.interactions[0] ? `<p class="quiet">Last time (${BA.fmtDate(d.interactions[0].date)}${d.interactions[0].title ? ", " + esc(d.interactions[0].title) : ""}):</p>${BA.md(d.interactions[0].takeaways || d.interactions[0].notes || "")}` : '<p class="quiet">No conversations logged yet.</p>'}
            ${(p.things_to_remember || []).length && show("things_to_remember") ? `<h3>Things to remember</h3><ul class="checklist">${p.things_to_remember.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
            ${d.follow_ups.length ? `<h3>Open follow-ups</h3>${d.follow_ups.map((a) => `<div class="item"><a href="#/dev-sync/${a.id}">${esc(a.concern)}</a><span class="spacer"></span>${BA.statusPill(a.status)}</div>`).join("")}` : ""}
            ${d.sos.length ? `<h3>Across teams</h3>${d.sos.map((s) => `<div class="item"><a href="#/sos">${esc(s.question)}</a><span class="spacer"></span><span class="quiet">${s.due ? BA.fmtDate(s.due) : ""}</span></div>`).join("")}` : ""}</section></div>
        ${commitmentsCard(d, p)}
        ${(show("offer_them") && p.offer_them) || (show("need_from_them") && p.need_from_them) ? `<section class="card exchange"><h2>The exchange</h2><div class="grid2"><div><h3>What I can offer them</h3>${p.offer_them ? BA.md(p.offer_them) : '<p class="quiet">Not written yet.</p>'}</div>
          <div><h3>What I need from them</h3>${p.need_from_them ? BA.md(p.need_from_them) : '<p class="quiet">Not written yet.</p>'}</div></div></section>` : ""}
        ${show("expects_from_me") && p.expects_from_me ? `<section class="card"><h2>What they expect from me</h2>${BA.md(p.expects_from_me)}</section>` : ""}
        <section class="card"><h2>About ${esc(p.name.split(" ")[0])}</h2>
          ${block("communication")}${block("working_style")}${block("goals")}${block("background")}
          ${show("skills") && (p.skills || []).length ? `<h3>Skills</h3><p>${BA.chips(p.skills)}</p>` : ""}
          ${block("motivations")}${block("support_notes")}${block("personal_context")}
          ${show("key_dates") && keyDates.length ? masked(id, "Key dates", `<ul class="checklist">${keyDates.map((x) => `<li>${esc(x.label)}: ${BA.fmtDate(x.date)}</li>`).join("")}</ul>`) : ""}
          <p class="quiet">Edit any of this on the Details tab. Choose which fields appear under <a href="#/people/fields">Fields</a>.</p></section>`;
      wireReveal();
      wireCommitments(box, id, () => renderPerson(main, id, "overview"));
      box.querySelector("#log-talk").onclick = () => { sessionStorage.setItem("ba-person-tab", "conversations"); renderPerson(main, id, "conversations"); };
      return;
    }

    if (current === "conversations") {
      const pname = Object.fromEntries(people.map((x) => [x.id, x.name]));
      const others = (ids) => ids.filter((x) => x !== id).map((x) => pname[x]).filter(Boolean);
      box.innerHTML = `<form id="talk" class="card"><h2>Log a conversation</h2><div class="grid2">
          <label>Date<input type="date" name="date" value="${BA.today()}" required></label><label>Kind<select name="kind">${opts(INTERACTION_KINDS, "one-on-one")}</select></label>
          <label>Topic<input name="title" placeholder="What it was about"></label><label>How it went<select name="mood"><option value=""></option>${opts(MOODS)}</select></label></div>
          <label>Also there</label><div class="case-picks">${people.filter((x) => x.id !== id).map((x) => `<label class="check"><input type="checkbox" name="with" value="${x.id}"> ${esc(x.name)}</label>`).join("")}</div>
          <label>Notes <span class="quiet">(Markdown; private)</span><textarea name="notes" rows="6"></textarea></label>
          <label>Takeaways <span class="quiet">(what you'll want to remember next time)</span><textarea name="takeaways" rows="2"></textarea></label>
          <div class="grid2"><label>I'll do <span class="quiet">(one per line; added to my commitments to ${esc(p.name.split(" ")[0])})</span><textarea name="i_will" rows="3"></textarea></label>
            <label>${esc(p.name.split(" ")[0])} will do <span class="quiet">(one per line; added to their commitments)</span><textarea name="they_will" rows="3"></textarea></label></div>
          <label>Follow-ups for the team <span class="quiet">(one per line; each can become a dev-sync item)</span><textarea name="follow_ups" rows="2"></textarea></label>
          <label class="check">Next meeting <input type="date" name="next_meeting" value="${esc(p.next_meeting || "")}" style="max-width:170px"></label>
          <div class="actions"><button class="btn primary" type="submit">Save</button></div></form>
        <section class="card"><h2>Conversations</h2>${d.interactions.map((i) => `<details class="plan-item" data-talk="${i.id}"><summary><span class="quiet">${BA.fmtDate(i.date)}</span><span class="pill">${esc(i.kind)}</span><b>${esc(i.title || "")}</b>
            <span class="spacer"></span>${i.mood ? `<span class="quiet">${esc(i.mood)}</span>` : ""}${others(i.person_ids).length ? `<span class="quiet">with ${esc(others(i.person_ids).join(", "))}</span>` : ""}</summary>
            ${i.notes ? BA.md(i.notes) : ""}${i.takeaways ? `<h4>Takeaways</h4>${BA.md(i.takeaways)}` : ""}${i.follow_ups ? `<h4>Follow-ups</h4>${BA.md(i.follow_ups.split("\n").filter(Boolean).map((x) => "- " + x.replace(/^[-*•]\s*/, "")).join("\n"))}
              <button class="btn" type="button" data-follow>Send follow-ups to the dev-sync log</button>` : ""}
            <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("interaction", i.id)}</div></details>`).join("") || '<p class="quiet">Nothing logged yet.</p>'}</section>`;
      const form = box.querySelector("#talk");
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const talk = await BA.api("/api/interactions", { method: "POST", body: { date: fd.get("date"), kind: fd.get("kind"), title: fd.get("title") || null, mood: fd.get("mood") || null,
          person_ids: [id, ...fd.getAll("with").map(Number)], notes: fd.get("notes"), takeaways: fd.get("takeaways"), follow_ups: fd.get("follow_ups") } });
        for (const [field, direction] of [["i_will", "mine"], ["they_will", "theirs"]])
          for (const line of (fd.get(field) || "").split("\n").map((x) => x.replace(/^[-*•]\s*/, "").trim()).filter(Boolean))
            await BA.api("/api/commitments", { method: "POST", body: { person_id: id, direction, title: line, created_on: BA.today(), interaction_id: talk.id } });
        if ((fd.get("next_meeting") || null) !== (p.next_meeting || null)) await BA.api(`/api/people/${id}`, { method: "PATCH", body: { next_meeting: fd.get("next_meeting") || null } });
        BA.toast("Saved.");
        renderPerson(main, id, "conversations");
      });
      box.querySelectorAll("[data-talk]").forEach((det) => {
        const tid = det.dataset.talk;
        const fb = det.querySelector("[data-follow]");
        if (fb) fb.onclick = BA.guard(async () => { const r = await BA.api(`/api/interactions/${tid}/follow-up`, { method: "POST" }); BA.toast(r.created.length ? `${r.created.length} added to the dev-sync log.` : "Those are already in the dev-sync log."); });
        det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this conversation?")) return; await BA.api(`/api/interactions/${tid}`, { method: "DELETE" }); renderPerson(main, id, "conversations"); });
      });
      return;
    }

    if (current === "manager") {
      const m = d.manager;
      const KIND_TONES = { praise: "good", win: "good", constructive: "warn", concern: "bad" };
      const ag = await BA.api(`/api/people/${id}/agenda`);
      box.innerHTML = `<div class="cards">
          <section class="card"><div class="row"><h2>Mandate</h2><span class="spacer"></span><a class="btn" href="#/first90/mandates">Mandates</a></div><p class="quiet">What their role is for, what it's expected to deliver, and what they can decide on their own.</p></section>
          <section class="card"><h2>Growth goals</h2>${m.goals.map((g) => `<details class="plan-item${g.status !== "active" ? " dropped" : ""}" data-goal="${g.id}"><summary><b>${esc(g.goal)}</b><span class="spacer"></span>
              ${g.target_date ? `<span class="quiet">${BA.fmtDate(g.target_date)}</span>` : ""}${BA.statusPill(g.status === "active" ? "in progress" : g.status === "achieved" ? "done" : g.status)}</summary>
              ${g.measure ? `<p class="quiet">Measure: ${esc(g.measure)}</p>` : ""}${g.progress ? BA.md(g.progress) : ""}
              <form class="goal-edit"><label>Progress<textarea name="progress" rows="2">${esc(g.progress || "")}</textarea></label><div class="row"><select name="status" style="max-width:140px">${opts(["active", "achieved", "paused", "dropped"], g.status)}</select>
                <button class="btn" type="submit">Save</button><span class="spacer"></span><button class="icon-btn" type="button" data-del-goal title="Delete">${BA.icon("x")}</button></div></form></details>`).join("") || '<p class="quiet">No goals yet.</p>'}
            <form id="add-goal" class="row" style="margin-top:8px"><input name="goal" required placeholder="A goal they're working toward" style="flex:1;min-width:200px"><input name="measure" placeholder="How we'll know" style="max-width:200px">
              <input type="date" name="target_date" style="max-width:160px"><button class="btn" type="submit">Add</button></form></section>
          <section class="card"><h2>Next one-on-one</h2><p class="quiet">Drafted from what's owed each way, their goals, feedback you haven't shared yet and open items.</p>
            <details><summary>Show the agenda</summary><div class="msg-preview">${BA.md(ag.markdown)}</div></details><div class="row"><button class="btn" type="button" id="copy-agenda">${BA.icon("copy")} Copy agenda</button></div></section></div>
        <section class="card"><h2>Feedback, wins and concerns</h2><p class="quiet">A running log for review time. Tick <b>shared</b> once you've told them; unshared praise and feedback lands on the next agenda.</p>
          <form id="add-note" class="row"><select name="kind" style="max-width:150px">${opts(["praise", "constructive", "win", "concern"], "praise")}</select><input name="note" required placeholder="What happened, specifically" style="flex:1;min-width:240px">
            <input type="date" name="date" value="${BA.today()}" style="max-width:160px"><button class="btn primary" type="submit">Add</button></form>
          ${m.notes.map((n) => `<div class="item" data-mnote="${n.id}"><span class="quiet">${BA.fmtDate(n.date)}</span>${tonePill(n.kind, KIND_TONES)}<span>${esc(n.note)}</span><span class="spacer"></span>
            <label class="check"><input type="checkbox" data-shared${n.shared ? " checked" : ""}> shared</label><button class="icon-btn" type="button" data-del-note title="Delete">${BA.icon("x")}</button></div>`).join("") || '<p class="quiet">Nothing logged yet.</p>'}</section>`;
      const again = () => renderPerson(main, id, "manager");
      box.querySelector("#add-goal").onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(e.target); await BA.api("/api/growth-goals", { method: "POST", body: { person_id: id, goal: fd.get("goal"), measure: fd.get("measure") || null, target_date: fd.get("target_date") || null, updated: BA.today() } }); again(); });
      box.querySelectorAll("[data-goal]").forEach((g) => {
        g.querySelector("form").onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(e.target); await BA.api(`/api/growth-goals/${g.dataset.goal}`, { method: "PATCH", body: { progress: fd.get("progress"), status: fd.get("status"), updated: BA.today() } }); again(); });
        g.querySelector("[data-del-goal]").onclick = BA.guard(async () => { if (!confirm("Delete this goal?")) return; await BA.api(`/api/growth-goals/${g.dataset.goal}`, { method: "DELETE" }); again(); });
      });
      box.querySelector("#add-note").onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(e.target); await BA.api("/api/manager-notes", { method: "POST", body: { person_id: id, kind: fd.get("kind"), note: fd.get("note"), date: fd.get("date") } }); again(); });
      box.querySelectorAll("[data-mnote]").forEach((row) => {
        row.querySelector("[data-shared]").onchange = BA.guard(async (e) => { await BA.api(`/api/manager-notes/${row.dataset.mnote}`, { method: "PATCH", body: { shared: e.target.checked } }); BA.toast("Saved."); });
        row.querySelector("[data-del-note]").onclick = BA.guard(async () => { if (!confirm("Delete this note?")) return; await BA.api(`/api/manager-notes/${row.dataset.mnote}`, { method: "DELETE" }); again(); });
      });
      box.querySelector("#copy-agenda").onclick = BA.guard(async () => { await navigator.clipboard.writeText(ag.markdown); BA.toast("Agenda copied."); });
      return;
    }

    if (current === "timeline") {
      const tl = await BA.api(`/api/people/${id}/timeline`);
      box.innerHTML = `<section class="card"><h2>Timeline</h2><p class="quiet">Everything in the toolkit involving ${esc(p.name)}: conversations, listening-tour notes, dev-sync items, Scrum of Scrums items and retros.</p>
        ${tl.events.map((ev) => `<div class="item"><span class="quiet tl-date">${BA.fmtDate(ev.date) || "no date"}</span><span class="pill">${esc(ev.kind)}</span><a href="#${esc(ev.route)}">${esc(ev.title)}</a><span class="spacer"></span><span class="quiet">${esc(ev.detail || "")}</span></div>`).join("") || '<p class="quiet">Nothing yet.</p>'}</section>`;
      return;
    }

    // details
    const base = PERSON_FIELDS.filter((f) => ["name", "role", "relationship", "active"].includes(f.name) || show(f.name));
    const extra = (f, html) => (show(f) ? html : "");
    const keyDates = ((p.key_dates || {}).dates || []);
    const field = (f, inner) => (sens(f) ? masked(id, FIELD_LABELS[f], inner) : `<label>${esc(FIELD_LABELS[f])}${inner}</label>`);
    box.innerHTML = `<form id="person" class="card"><div class="grid2">${BA.form(base.filter((f) => !layout.sensitive.includes(f.name)), p)}
        ${extra("manager_id", `<label>Reports to<select name="manager_id">${personOptions(people.filter((x) => x.id !== id), p.manager_id)}</select></label>`)}
        ${extra("tags", `<label>Tags <span class="quiet">(comma separated)</span><input name="tags" value="${esc((p.tags || []).join(", "))}"></label>`)}
        ${extra("cadence_days", `<label>Check in every <span class="quiet">(days)</span><input type="number" min="1" name="cadence_days" value="${esc(p.cadence_days ?? "")}"></label>`)}
        ${extra("next_meeting", `<label>Next meeting<input type="date" name="next_meeting" value="${esc(p.next_meeting || "")}"></label>`)}
        ${extra("influence", `<label>Influence<select name="influence"><option value=""></option>${opts(INFLUENCE, p.influence)}</select></label>`)}
        ${extra("stance", `<label>Stance<select name="stance"><option value=""></option>${opts(STANCE, p.stance)}</select></label>`)}</div>
        ${extra("communication", `<label>How they like to communicate<textarea name="communication" rows="2">${esc(p.communication || "")}</textarea></label>`)}
        ${extra("offer_them", `<label>What I can offer them <span class="quiet">(help, information, support for what they care about)</span><textarea name="offer_them" rows="2">${esc(p.offer_them || "")}</textarea></label>`)}
        ${extra("need_from_them", `<label>What I need from them <span class="quiet">(support, information, decisions, introductions)</span><textarea name="need_from_them" rows="2">${esc(p.need_from_them || "")}</textarea></label>`)}
        ${extra("advice", `<label>Advice I go to them for <span class="quiet">(your advice network)</span></label><div class="case-picks">${[["technical", "Technical: expertise to get the work done"], ["political", "Political: how the organization really works"], ["personal", "Personal: perspective and balance"]].map(([k, l]) => `<label class="check"><input type="checkbox" name="advice" value="${k}"${(p.advice || []).includes(k) ? " checked" : ""}> ${l}</label>`).join("")}</div>`)}
        ${extra("insight", `<label>Insight they bring <span class="quiet">(where their view of the organization comes from)</span></label><div class="case-picks">${[["customer", "Customer or business user"], ["vendor", "Vendor or supplier"], ["frontline", "Frontline"], ["sales", "Sales or service"], ["staff", "Finance, legal or HR"], ["integrator", "Integrator"], ["historian", "Natural historian"]].map(([k, l]) => `<label class="check"><input type="checkbox" name="insight" value="${k}"${(p.insight || []).includes(k) ? " checked" : ""}> ${l}</label>`).join("")}</div>`)}
        ${extra("change_style", `<label>Style when leading change <span class="quiet">(your read; private)</span><select name="change_style"><option value=""></option>${[["hero", "Hero: takes charge, moves fast"], ["steward", "Steward: builds consensus, patient"], ["both", "Some of each"]].map(([k, l]) => `<option value="${k}"${p.change_style === k ? " selected" : ""}>${l}</option>`).join("")}</select></label>`)}
        ${extra("expects_from_me", `<label>What they expect from me <span class="quiet">(especially anyone who shapes how my work is judged)</span><textarea name="expects_from_me" rows="2">${esc(p.expects_from_me || "")}</textarea></label>`)}
        ${extra("things_to_remember", `<label>Things to remember <span class="quiet">(one per line)</span><textarea name="things_to_remember" rows="3">${esc((p.things_to_remember || []).join("\n"))}</textarea></label>`)}
        ${["motivations", "support_notes", "personal_context"].filter(show).map((f) => field(f, `<textarea name="${f}" rows="3">${esc(p[f] || "")}</textarea>`)).join("")}
        ${extra("key_dates", field("key_dates", `<div id="key-dates">${[...keyDates, { label: "", date: "" }].map((x) => `<div class="row kd"><input name="kd_label" value="${esc(x.label)}" placeholder="Such as: work anniversary" style="max-width:240px"><input type="date" name="kd_date" value="${esc(x.date)}" style="max-width:170px"></div>`).join("")}</div>`))}
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button>${d.is_me ? "" : '<button class="btn" type="button" id="this-is-me">This is me</button>'}${BA.historyButton("person", id)}<button class="btn primary" type="submit">Save</button></div></form>
      <section class="card"><div class="row"><h2>Listening tour</h2><span class="spacer"></span><button class="btn" id="plan">Plan a listening-tour one-on-one</button></div><p class="quiet">The five standard questions, kept separately in the Listening tour.</p></section>`;
    wireReveal();
    const form = box.querySelector("#person");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const body = BA.readForm(form, base.filter((f) => !layout.sensitive.includes(f.name)));
      if (form.elements.manager_id) body.manager_id = numOrNull(fd.get("manager_id"));
      if (form.elements.tags) body.tags = fd.get("tags").split(",").map((x) => x.trim()).filter(Boolean);
      if (form.elements.cadence_days) body.cadence_days = numOrNull(fd.get("cadence_days"));
      if (form.elements.next_meeting) body.next_meeting = fd.get("next_meeting") || null;
      for (const f of ["influence", "stance"]) if (form.elements[f]) body[f] = fd.get(f) || null;
      for (const f of ["communication", "motivations", "support_notes", "personal_context", "offer_them", "need_from_them", "expects_from_me"]) if (form.elements[f]) body[f] = fd.get(f);
      if (form.querySelector('input[name="advice"]')) body.advice = fd.getAll("advice");
      if (form.querySelector('input[name="insight"]')) body.insight = fd.getAll("insight");
      if (form.elements.change_style) body.change_style = fd.get("change_style") || null;
      if (form.elements.things_to_remember) body.things_to_remember = fd.get("things_to_remember").split("\n").map((x) => x.trim()).filter(Boolean);
      if (form.querySelector("#key-dates")) {
        const labels = fd.getAll("kd_label"), dates = fd.getAll("kd_date");
        body.key_dates = { dates: labels.map((l, i) => ({ label: l.trim(), date: dates[i] })).filter((x) => x.label && x.date) };
      }
      await BA.api(`/api/people/${id}`, { method: "PATCH", body });
      BA.toast("Saved.");
      renderPerson(main, id, "details");
    });
    const meB = box.querySelector("#this-is-me");
    if (meB) meB.onclick = BA.guard(async () => { await BA.api("/api/people/me", { method: "PUT", body: { person_id: id } }); BA.toast("Noted: this is you. Anyone who reports to you now shows as a direct report."); });
    box.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm(`Delete ${p.name}? Their conversations and one-on-ones stay, without this person.`)) return;
      await BA.api(`/api/people/${id}`, { method: "DELETE" });
      BA.go("/people");
    });
    box.querySelector("#plan").onclick = BA.guard(async () => {
      const i = await BA.api("/api/interviews", { method: "POST", body: { person_id: id, date: BA.today(), status: "planned" } });
      BA.go(`/listening/${i.id}`);
    });
  }


  // ---------------------------------------------------------------- Skills and learning

  BA.view("/skills", {
    title: "Skills and learning",
    async render(main) {
      const d = await BA.api("/api/skills");
      const counts = `<section class="card"><h2>Skills across the team</h2><div class="tablewrap"><table class="data">
        <thead><tr><th>Skill</th><th>People with it</th><th>Can teach</th><th>Want to learn</th></tr></thead><tbody>${
          d.skills.map((s) => `<tr><td>${esc(s.skill)}</td><td>${s.people}</td><td>${s.can_teach}</td><td>${s.wants_to_learn}</td></tr>`).join("") ||
          '<tr><td colspan="4" class="empty">No skills recorded yet. Add them on each person\'s profile.</td></tr>'
        }</tbody></table></div></section>`;
      if (!d.matrix) {
        main.innerHTML = counts;
        return;
      }
      const topics = d.skills.map((s) => s.skill);
      const mark = (p, t) =>
        [p.skills.includes(t) ? "has" : "", p.can_teach.includes(t) ? "teaches" : "", p.wants_to_learn.includes(t) ? "wants" : ""]
          .filter(Boolean)
          .map((m) => `<span class="pill ${m === "teaches" ? "good" : m === "wants" ? "warn" : ""}">${m}</span>`)
          .join(" ");
      main.innerHTML = `
        <section class="card"><h2>Teach and learn matches</h2>
          <p class="quiet">Ideas for group learning sessions. Proposing one adds it to the <a href="#/learning">group learning schedule</a>.</p>${
            d.matches.map((m) => `<div class="item"><b>${esc(m.topic)}</b><span class="spacer"></span><span>${esc(m.teachers.join(", "))} could teach ${esc(m.learners.join(", "))}</span>
              <button class="btn" data-propose="${esc(m.topic)}" data-teacher="${esc(m.teachers[0])}">Propose a session</button></div>`).join("") ||
            '<p class="quiet">No matches yet.</p>'
          }</section>
        <section class="card"><h2>Skills matrix</h2><div class="tablewrap"><table class="data">
          <thead><tr><th>Person</th>${topics.map((t) => `<th>${esc(t)}</th>`).join("")}</tr></thead><tbody>${d.matrix
            .map((p) => `<tr><td><a href="#/people/${p.id}">${esc(p.name)}</a></td>${topics.map((t) => `<td>${mark(p, t)}</td>`).join("")}</tr>`)
            .join("")}</tbody></table></div></section>${counts}`;
      main.querySelectorAll("[data-propose]").forEach((b) => {
        b.onclick = BA.guard(async () => {
          const presenter = d.matrix.find((p) => p.name === b.dataset.teacher);
          await BA.api("/api/learning-sessions", { method: "POST", body: { topic: b.dataset.propose, presenter_id: presenter ? presenter.id : null } });
          BA.toast("Proposed. It's on the group learning schedule.");
        });
      });
    },
  });

  // ---------------------------------------------------------------- Listening tour

  BA.view("/listening", {
    title: "Listening tour",
    async render(main, param) {
      if (presenting()) {
        main.innerHTML = '<p class="empty">One-on-ones are private, so they\'re hidden while presenting. The day-30 rollup shows themes and counts.</p>';
        return;
      }
      const people = await BA.api("/api/people");
      if (param) return renderInterview(main, Number(param), people);
      const interviews = await BA.api("/api/interviews");
      const done = interviews.filter((i) => i.status === "done").length;
      main.innerHTML = `
        <section class="card"><div class="row"><h2>${done} of ${interviews.length} one-on-ones done</h2></div>
          <form id="plan" class="row">
            <select name="person_id" required style="max-width:280px"><option value="">Choose a person</option>${people.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("")}</select>
            <input type="date" name="date" value="${BA.today()}" style="max-width:180px">
            <button class="btn primary" type="submit">Plan a one-on-one</button></form></section>
        <div class="tablewrap"><table class="data"><thead><tr><th>Date</th><th>Person</th><th>Status</th><th>Themes</th></tr></thead><tbody>${
          interviews
            .map((i) => `<tr class="clickable" data-id="${i.id}"><td>${BA.fmtDate(i.date)}</td><td>${esc(i.person_name || "[No person set]")}</td>
              <td>${BA.statusPill(i.status)}</td><td>${BA.chips(i.themes)}</td></tr>`)
            .join("") || '<tr><td colspan="4" class="empty">No one-on-ones yet.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/listening/${tr.dataset.id}`)));
      const plan = main.querySelector("#plan");
      plan.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(plan);
        const i = await BA.api("/api/interviews", {
          method: "POST",
          body: { person_id: Number(f.get("person_id")), date: f.get("date"), status: "planned" },
        });
        BA.go(`/listening/${i.id}`);
      });
    },
  });

  async function renderInterview(main, id, people) {
    const rec = await BA.api(`/api/interviews/${id}`);
    const fields = INTERVIEW_FIELDS(people);
    const all = await BA.api("/api/interviews");
    const known = [...new Set(all.flatMap((i) => i.themes))];
    document.getElementById("view-title").textContent = `One-on-one: ${rec.person_name || "[No person set]"}`;
    main.innerHTML = `<p><a href="#/listening">All one-on-ones</a></p>
      <form id="iv" class="card">
        <div class="grid2">${BA.form(fields.slice(0, 3), rec)}</div>
        <h3>The same five questions, every time</h3>${BA.form(fields.slice(3, 8), rec)}
        <h3>What I heard</h3>${BA.form(fields.slice(8), rec)}
        ${known.length ? `<p class="quiet">Themes so far: ${BA.chips(known)}</p>` : ""}
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button>${BA.historyButton("interview", id)}<button class="btn primary" type="submit">Save</button></div>
      </form>`;
    const form = main.querySelector("#iv");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api(`/api/interviews/${id}`, { method: "PATCH", body: BA.readForm(form, fields) });
      BA.toast("Saved.");
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm("Delete this one-on-one?")) return;
      await BA.api(`/api/interviews/${id}`, { method: "DELETE" });
      BA.go("/listening");
    });
  }

  // ---------------------------------------------------------------- Day-30 rollup

  BA.view("/rollup", {
    title: "Day-30 rollup",
    async render(main) {
      const d = await BA.api("/api/rollup");
      const max = Math.max(1, ...d.themes.map((t) => t.count));
      const quotes = (t) =>
        (d.theme_quotes?.[t] || []).map((q) => `<div class="quiet private-only">${esc(q.person || "[No person]")}: ${esc(q.text)}</div>`).join("");
      const notes = (key, title) =>
        d.notes
          ? `<section class="card"><h2>${title}</h2>${
              d.notes[key].map((n) => `<div class="item"><span>${esc(n.text)}</span><span class="spacer"></span><span class="quiet">${esc(n.person || "")}</span></div>`).join("") ||
              '<p class="quiet">Nothing yet.</p>'
            }</section>`
          : "";
      main.innerHTML = `
        <section class="card"><div class="row"><h2>Themes from ${d.done} one-on-ones</h2><span class="spacer"></span>
          ${d.notes ? '<button class="btn" id="md">Copy as Markdown</button>' : ""}</div>
          <p class="quiet">${d.planned} still planned. This is the raw material for the written diagnosis.</p>${
            d.themes
              .map((t) => `<div class="item" style="display:block"><b>${esc(t.theme)}</b> <span class="quiet">${t.count} of ${d.done}</span>
                <div class="bar" style="width:${(t.count / max) * 100}%"></div>${quotes(t.theme)}</div>`)
              .join("") || '<p class="quiet">No themes tagged yet. Add them to each one-on-one.</p>'
          }</section>
        ${d.systems ? `<section class="card"><h2>Products and systems mentioned</h2>${d.systems.map((s) => `<span class="pill">${esc(s.system)} · ${s.count}</span>`).join(" ") || '<p class="quiet">None yet.</p>'}</section>` : ""}
        <div class="cards">${notes("gaps", "Gaps")}${notes("opportunities", "Opportunities")}${notes("dont_change", "What not to change")}${notes("change_first", "What to change first")}${notes("if_you_were_me", "If you were me, I'd focus on")}</div>`;
      const md = main.querySelector("#md");
      if (md)
        md.onclick = BA.guard(async () => {
          const { markdown } = await BA.api("/api/rollup/markdown");
          await navigator.clipboard.writeText(markdown);
          BA.toast("Copied.");
        });
    },
  });

  // ---------------------------------------------------------------- My development

  async function renderPreferences(main) {
    if (presenting()) { main.innerHTML = '<p class="empty">Private, so hidden while presenting.</p>'; return; }
    const [d, people] = await Promise.all([BA.api("/api/preferences"), BA.api("/api/people")]);
    document.getElementById("view-title").textContent = "Problem preferences";
    const last = d.assessments[0];
    const cell = (a, k, i) => `<td><label style="display:flex;flex-direction:column;gap:4px;font-weight:400"><span class="quiet">${esc(a.cells[i])}</span><input type="number" min="1" max="10" name="${a.key}.${k.key}" value="${esc((last && last.scores && last.scores[a.key + "." + k.key]) || "")}" required style="max-width:70px"></label></td>`;
    const lowK = new Set(last ? last.blind_spots.kinds : []), lowA = new Set(last ? last.blind_spots.areas : []);
    const label = (list, key) => (list.find((x) => x.key === key) || {}).label || key;
    main.innerHTML = `<p><a href="#/me">My development</a></p>
      <form id="prefs" class="card"><h2>How much do you enjoy solving each kind of problem?</h2>
        <p class="quiet">Rate each from 1 (very little) to 10 (a great deal). Rate your interest, not your skill or experience, and judge each one on its own. We tend to drift toward the problems we enjoy, so the low ones are where blind spots grow. Inspired by The First 90 Days. Private.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th></th>${d.kinds.map((k) => `<th>${esc(k.label)}<div class="quiet" style="font-weight:400;text-transform:none">${esc(k.about)}</div></th>`).join("")}<th>Total</th></tr></thead>
          <tbody>${d.areas.map((a) => `<tr><th>${esc(a.label)}</th>${d.kinds.map((k, i) => cell(a, k, i)).join("")}<td><b>${last ? last.rows[a.key] : "–"}</b>${lowA.has(a.key) ? ' <span class="pill warn">low</span>' : ""}</td></tr>`).join("")}
          <tr><th>Total</th>${d.kinds.map((k) => `<td><b>${last ? last.columns[k.key] : "–"}</b>${lowK.has(k.key) ? ' <span class="pill warn">low</span>' : ""}</td>`).join("")}<td></td></tr></tbody></table></div>
        <label><b>My hammer</b> <span class="quiet">What has made you successful so far, and how could each strength misfire here? (Attention to detail can turn into micromanaging.)</span><textarea name="hammer" rows="3">${esc((last && last.hammer) || "")}</textarea></label>
        <label>Notes <span class="quiet">(optional)</span><textarea name="notes" rows="2"></textarea></label>
        <div class="actions"><button class="btn primary" type="submit">Save my ratings</button></div></form>
      <section class="card"><h2>Hero or steward?</h2><p class="quiet">When you lead change, is your reflex to take charge and move fast (hero), or to build shared understanding and consensus (steward)? Turnarounds and start-ups call for the hero; realignments and sustaining success for the steward. Your situation portfolio checks the fit.</p>
        <select id="my-style" style="max-width:420px"><option value="">Not noted</option>${d.styles.map((s) => `<option value="${s.key}"${d.my_style === s.key ? " selected" : ""}>${esc(s.label)}</option>`).join("")}</select></section>
      ${last && last.complete ? `<section class="card"><h2>Possible blind spots</h2>${last.blind_spots.kinds.length || last.blind_spots.areas.length
        ? `<p>${[...last.blind_spots.kinds.map((k) => `${label(d.kinds, k)} problems`), ...last.blind_spots.areas.map((a) => label(d.areas, a))].map(esc).join(", ")} scored noticeably lower than your strongest. Guides that help:</p>
           <ul>${last.guides.map((g) => `<li><a href="#/coaching/${g.slug}">${esc(g.title)}</a></li>`).join("")}</ul>
           <form id="comp"><h3>How I'll compensate</h3><p class="quiet">For each one: lean on discipline (time for it even when you'd rather not), a backstop (someone strong there to rely on and learn from), or an advisor.</p>
             ${[...last.blind_spots.kinds.map((k) => [k, label(d.kinds, k) + " problems"]), ...last.blind_spots.areas.map((a) => [a, label(d.areas, a)])].map(([key, name]) => { const pl = (last.plan || {})[key] || {}; return `<div class="row" data-comp="${key}" style="align-items:center;margin-bottom:6px"><b style="min-width:180px">${esc(name)}</b>
               <select name="how" style="max-width:150px">${["", "discipline", "backstop", "advisor"].map((h) => `<option value="${h}"${pl.how === h ? " selected" : ""}>${h || "How?"}</option>`).join("")}</select>
               <select name="person" style="max-width:220px"><option value="">Person (optional)</option>${people.map((p) => `<option value="${p.id}"${pl.person_id === p.id ? " selected" : ""}>${esc(p.name)}</option>`).join("")}</select>
               <input name="note" value="${esc(pl.note || "")}" placeholder="What I'll do" style="flex:1;min-width:180px"></div>`; }).join("")}
             <div class="actions"><button class="btn" type="submit">Save my plan</button></div></form>`
        : '<p class="quiet">Nothing stands out as noticeably lower. A balanced profile, at least in what you enjoy.</p>'}</section>` : ""}
      ${d.assessments.length > 1 ? `<section class="card"><h2>Earlier ratings</h2>${d.assessments.slice(1).map((p) => `<div class="item">${BA.fmtDate(p.date)}<span class="spacer"></span><span class="quiet">${d.kinds.map((k) => `${esc(k.label)} ${p.columns[k.key]}`).join(" · ")}</span></div>`).join("")}</section>` : ""}`;
    const form = main.querySelector("#prefs");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const scores = {};
      for (const [k, v] of fd.entries()) if (k.includes(".")) scores[k] = Number(v);
      await BA.api("/api/preferences", { method: "POST", body: { scores, notes: fd.get("notes"), hammer: fd.get("hammer") } });
      BA.toast("Saved.");
      BA.rerender();
    });
    main.querySelector("#my-style").onchange = BA.guard(async (e) => { await BA.api("/api/situations/my-style", { method: "PUT", body: { style: e.target.value || null } }); BA.toast("Saved."); });
    const comp = main.querySelector("#comp");
    if (comp) comp.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const plan = {};
      comp.querySelectorAll("[data-comp]").forEach((r) => {
        const person = r.querySelector('[name="person"]').value;
        plan[r.dataset.comp] = { how: r.querySelector('[name="how"]').value || null, person_id: person ? Number(person) : null, note: r.querySelector('[name="note"]').value };
      });
      await BA.api(`/api/preference-assessments/${last.id}`, { method: "PATCH", body: { plan } });
      BA.toast("Saved.");
    });
  }

  BA.view("/me", {
    title: "My development",
    async render(main, param) {
      if (param === "preferences") return renderPreferences(main);
      const [settings, goals, log, tasks, obligations, advice] = await Promise.all([
        BA.api("/api/toolkit/settings"),
        BA.api("/api/learning-goals"),
        BA.api("/api/learning-log"),
        BA.api("/api/tasks"),
        BA.api("/api/obligations"),
        BA.api("/api/people/advice-network"),
      ]);
      const start = settings.start_date;
      const dayDate = (n) => {
        if (n == null) return "";
        if (!start) return BA.roleDay(n);
        const d = new Date(start + "T12:00:00");
        d.setDate(d.getDate() + n - 1);
        return `Day ${n} · ${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
      };
      const hours = (m) => (m ? `${Math.round((m / 60) * 10) / 10} h` : "");

      if (presenting()) {
        main.innerHTML = `<section class="card"><h2>Learning goals</h2><div class="tablewrap"><table class="data">
          <thead><tr><th>Track</th><th>Goal</th><th>Target</th><th>Status</th><th>Time</th></tr></thead><tbody>${
            goals.map((g) => `<tr><td>${esc(g.track)}</td><td>${esc(g.goal)}</td><td>${dayDate(g.target_day)}</td><td>${BA.statusPill(g.status)}</td><td>${hours(g.minutes)}</td></tr>`).join("") ||
            '<tr><td colspan="5" class="empty">No goals marked for reporting.</td></tr>'
          }</tbody></table></div></section>`;
        return;
      }

      const recentLog = (goalId) =>
        log
          .filter((l) => l.goal_id === goalId)
          .slice(0, 3)
          .map((l) => `<div class="quiet">${BA.fmtDate(l.date)} · ${l.minutes || 0} min · ${esc(l.note)}</div>`)
          .join("");

      main.innerHTML = `
        <section class="card"><div class="row"><h2>Problem preferences</h2><span class="spacer"></span><a class="btn" href="#/me/preferences">Take the assessment</a></div>
          <p class="quiet">Which kinds of problems you're drawn to, and which you tend to avoid. Low scores point to likely blind spots, each with guides to strengthen it.</p></section>
        <section class="card"><h2>My advice network</h2>${[["technical", "Technical"], ["political", "Political"], ["personal", "Personal"]].map(([k, l]) => `<div class="item"><b style="min-width:90px">${l}</b>${advice.kinds[k].map((p) => `<a href="#/people/${p.id}">${esc(p.name)}</a>`).join(", ") || '<span class="quiet">No one yet</span>'}</div>`).join("")}
          ${advice.missing.length ? `<p class="callout warn">No ${advice.missing.join(" or ")} advisor yet. The higher you go, the more you need counsel on how the organization works and someone to keep you steady.</p>` : ""}
          <p class="quiet">Mark advisors on each person's page under Details. <a href="#/coaching/new-role-mindset">Why it matters</a></p></section>
        <section class="card"><h2>Start date</h2><p class="quiet">Leave it blank until your start date is confirmed. Until then everything stays as "Day N · week N", and nothing is marked late or counted down.</p>
          <form id="start" class="row"><input type="date" name="start_date" value="${esc(start || "")}" style="max-width:200px">
          <button class="btn" type="submit">Save</button><span class="quiet">Turns every "Day N" into a real date.</span></form></section>
        <section class="card"><h2>Jira</h2>
          <form id="jira" class="row"><input name="jira_url" value="${esc(settings.jira_url || "")}" placeholder="https://[your-site].atlassian.net" style="max-width:360px">
          <button class="btn" type="submit">Save</button><span class="quiet">Turns every Jira key in the toolkit into a link. Use <b>Find a Jira key</b> (⌘K) to see everywhere a key is mentioned.</span></form></section>

        <section class="card"><h2>Learning goals</h2>
          <p class="quiet">Goals marked "Report" are the ones your manager sees in status reports and presentation mode.</p>
          <div class="tablewrap"><table class="data"><thead><tr><th>Track</th><th>Goal</th><th>Target</th><th>Status</th><th>Time</th><th>Report</th><th></th></tr></thead><tbody>${goals
            .map((g) => `<tr><td>${esc(g.track)}</td><td>${esc(g.goal)}<div class="quiet">${esc(g.evidence)}</div>${recentLog(g.id)}</td>
              <td>${dayDate(g.target_day)}</td>
              <td><select data-goal-status="${g.id}">${GOAL_STATUS.map((s) => `<option${s === g.status ? " selected" : ""}>${s}</option>`).join("")}</select></td>
              <td>${hours(g.minutes)}</td>
              <td><input type="checkbox" data-goal-report="${g.id}"${g.show_in_report ? " checked" : ""}></td>
              <td><button class="btn" data-log="${g.id}">Log time</button> <button class="btn danger" data-goal-del="${g.id}">Delete</button></td></tr>
              <tr id="log-${g.id}" hidden><td colspan="7"><form class="row" data-log-form="${g.id}">
                <input type="date" name="date" value="${BA.today()}" style="max-width:170px">
                <input type="number" name="minutes" placeholder="Minutes" min="1" required style="max-width:120px">
                <input name="note" placeholder="What I covered" style="max-width:360px">
                <button class="btn primary" type="submit">Add</button></form></td></tr>`)
            .join("") || '<tr><td colspan="7" class="empty">No learning goals yet.</td></tr>'}</tbody></table></div>
          <form id="add-goal" class="grid2">
            ${BA.form([
              { name: "track", label: "Track" },
              { name: "goal", label: "Goal", required: true },
              { name: "evidence", label: "Evidence" },
              { name: "target_day", label: "Target day", type: "number" },
            ])}
            <div class="actions"><button class="btn primary" type="submit">Add goal</button></div></form></section>

        <div class="cards">
          <section class="card"><h2>Tasks</h2>${tasks
            .map((t) => `<div class="item"><input type="checkbox" data-task="${t.id}"${t.status === "done" ? " checked" : ""}>
              <span${t.status === "done" ? ' class="quiet"' : ""}>${esc(t.title)}</span><span class="spacer"></span>
              <span class="quiet">${esc(t.requested_by || "")} ${BA.fmtDate(t.due)}</span></div>`)
            .join("") || '<p class="quiet">No tasks.</p>'}
            <form id="add-task">${BA.form([
              { name: "title", label: "Task", required: true },
              { name: "requested_by", label: "Requested by" },
              { name: "due", label: "Due", type: "date" },
            ])}<div class="actions"><button class="btn primary" type="submit">Add task</button></div></form></section>

          <section class="card"><h2>Obligations</h2>${obligations
            .map((o) => `<div class="item"><span>${esc(o.title)}</span><span class="pill">${esc(o.cadence)}</span><span class="spacer"></span>
              <span class="quiet">next ${BA.fmtDate(o.next_due) || "not set"}</span><button class="btn" data-ob-done="${o.id}">Done</button></div>`)
            .join("") || '<p class="quiet">No obligations.</p>'}
            <form id="add-ob">${BA.form([
              { name: "title", label: "Obligation", required: true },
              { name: "cadence", label: "Cadence", type: "select", blank: false, options: CADENCES },
              { name: "next_due", label: "Next due", type: "date" },
            ])}<div class="actions"><button class="btn primary" type="submit">Add obligation</button></div></form></section>
        </div>`;

      const on = (sel, fn) => main.querySelectorAll(sel).forEach((el) => fn(el));
      main.querySelector("#start").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/toolkit/settings", { method: "PUT", body: { start_date: new FormData(e.target).get("start_date") || null } });
        BA.rerender();
      });
      main.querySelector("#jira").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const s = await BA.api("/api/toolkit/settings", { method: "PUT", body: { jira_url: new FormData(e.target).get("jira_url") } });
        BA.jiraUrl = s.jira_url || null;
        BA.toast(s.jira_url ? "Jira keys now link to " + s.jira_url : "Jira links turned off.");
      });
      on("[data-goal-status]", (el) => (el.onchange = BA.guard(() => BA.api(`/api/learning-goals/${el.dataset.goalStatus}`, { method: "PATCH", body: { status: el.value } }))));
      on("[data-goal-report]", (el) => (el.onchange = BA.guard(() => BA.api(`/api/learning-goals/${el.dataset.goalReport}`, { method: "PATCH", body: { show_in_report: el.checked } }))));
      on("[data-goal-del]", (el) =>
        (el.onclick = BA.guard(async () => {
          if (!confirm("Delete this goal and its log?")) return;
          await BA.api(`/api/learning-goals/${el.dataset.goalDel}`, { method: "DELETE" });
          BA.rerender();
        }))
      );
      on("[data-log]", (el) => (el.onclick = () => (main.querySelector(`#log-${el.dataset.log}`).hidden = false)));
      on("[data-log-form]", (form) =>
        (form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          await BA.api("/api/learning-log", {
            method: "POST",
            body: { goal_id: Number(form.dataset.logForm), date: f.get("date"), minutes: Number(f.get("minutes")), note: f.get("note") },
          });
          BA.rerender();
        }))
      );
      main.querySelector("#add-goal").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const body = BA.readForm(e.target, [{ name: "track" }, { name: "goal" }, { name: "evidence" }, { name: "target_day", type: "number" }]);
        await BA.api("/api/learning-goals", { method: "POST", body });
        BA.rerender();
      });
      on("[data-task]", (el) =>
        (el.onchange = BA.guard(async () => {
          await BA.api(`/api/tasks/${el.dataset.task}`, { method: "PATCH", body: { status: el.checked ? "done" : "open" } });
          BA.rerender();
        }))
      );
      main.querySelector("#add-task").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/tasks", { method: "POST", body: BA.readForm(e.target, [{ name: "title" }, { name: "requested_by" }, { name: "due" }]) });
        BA.rerender();
      });
      on("[data-ob-done]", (el) =>
        (el.onclick = BA.guard(async () => {
          await BA.api(`/api/obligations/${el.dataset.obDone}/done`, { method: "POST" });
          BA.rerender();
        }))
      );
      main.querySelector("#add-ob").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/obligations", { method: "POST", body: BA.readForm(e.target, [{ name: "title" }, { name: "cadence" }, { name: "next_due" }]) });
        BA.rerender();
      });
    },
  });

  // ---------------------------------------------------------------- Dev-sync log

  const ACTION_STATUS = ["open", "in progress", "waiting", "done"];
  const ACTION_ORIGINS = ["dev sync", "retro", "incident", "one-on-one", "vendor", "testing", "other"];
  // Teams: a picker on delivery screens filters lists to one team; new records go to the chosen team (or yours).
  BA.teamList = [];
  const loadTeams = () => BA.api("/api/teams").then((ts) => { const grew = ts.length > 1 && BA.teamList.length < 2; BA.teamList = ts; if (grew && BA.session) BA.rerender(); }).catch(() => {});
  loadTeams();
  const teamFilter = () => { try { return localStorage.getItem("ba-team") || ""; } catch { return ""; } };
  const inTeam = (r) => !teamFilter() || String(r.team_id) === teamFilter();
  const newTeamId = () => (teamFilter() ? Number(teamFilter()) : null);
  const keepTeam = (list) => list.splice(0, list.length, ...list.filter(inTeam));
  const TEAM_ROUTES = ["/dev-sync", "/sprints", "/risks", "/retros", "/qa", "/debt", "/planning"];
  BA.afterRender = (main, key, param) => {
    const showsLists = key === "/qa" ? param === "runs" : key === "/planning" ? !param || param === "plan" || /^\d+$/.test(param) : !param;
    if (BA.teamList.length < 2 || !TEAM_ROUTES.includes(key) || !showsLists || main.querySelector(":scope > .team-pick")) return;
    const el = document.createElement("div");
    el.className = "team-pick";
    el.innerHTML = `<label class="check">${BA.icon("users-round")} Team <select data-team-pick><option value="">All teams</option>${BA.teamList.map((t) => `<option value="${t.id}"${String(t.id) === teamFilter() ? " selected" : ""}>${esc(t.name)}${t.kind === "mine" ? " (mine)" : ""}</option>`).join("")}</select></label>`;
    main.prepend(el);
    el.querySelector("select").onchange = (e) => { try { localStorage.setItem("ba-team", e.target.value); } catch {} BA.rerender(); };
  };
  const personOptions = (people, sel) => `<option value=""></option>${people.map((p) => `<option value="${p.id}"${p.id === sel ? " selected" : ""}>${esc(p.name)}</option>`).join("")}`;
  const ACTION_FIELDS = (people) => [
    { name: "concern", label: "Question or concern", type: "textarea", required: true },
    { name: "raised_by_id", label: "Raised by", type: "select", numeric: true, options: people.map((p) => ({ value: p.id, label: p.name })) },
    { name: "raised_on", label: "Raised", type: "date" },
    { name: "owner_id", label: "Owner", type: "select", numeric: true, options: people.map((p) => ({ value: p.id, label: p.name })) },
    { name: "next_action", label: "Next action" },
    { name: "due", label: "Due", type: "date" },
    { name: "status", label: "Status", type: "select", blank: false, options: ACTION_STATUS },
    { name: "origin", label: "Came from", type: "select", blank: false, options: ACTION_ORIGINS },
    { name: "learning", label: "Group learning: worth a short team presentation", type: "checkbox" },
    { name: "kind", label: "Kind", type: "select", options: ["question", "offer to present", "decision needed", "idea", "action"] },
    { name: "decider_id", label: "Decision maker", type: "select", numeric: true, options: people.map((p) => ({ value: p.id, label: p.name })) },
    { name: "jira_keys", label: "Jira keys", type: "keys", placeholder: "ABC-123, ABC-124" },
    { name: "on_board", label: "On the dev-sync board (shareable)", type: "checkbox" },
    { name: "update_url", label: "Latest update (link to the presentation)" },
    { name: "update_on", label: "Update posted", type: "date" },
    { name: "notes", label: "My notes (private)", type: "textarea" },
  ];

  BA.view("/dev-sync", {
    title: "Dev-sync log",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderAction(main, Number(param), people);
      const [items, summary] = await Promise.all([BA.api("/api/actions"), BA.api("/api/actions/summary")]);
      keepTeam(items);
      const t = BA.today();
      const late = (i) => i.status !== "done" && i.due && i.due < t;
      const state = BA._devSyncFilter || (BA._devSyncFilter = { status: "active", owner: "" });
      const shown = items.filter(
        (i) =>
          (state.status === "all" || (state.status === "active" ? i.status !== "done" : state.status === "overdue" ? late(i) : i.status === state.status)) &&
          (!state.owner || String(i.owner_id) === state.owner)
      );
      const owners = [...new Map(items.filter((i) => i.owner_id).map((i) => [i.owner_id, i.owner_name])).entries()];
      main.innerHTML = `
        <div class="stats-row">
          <div class="card stat"><b>${summary.open}</b><span>open</span></div>
          <div class="card stat${summary.overdue ? " bad" : ""}"><b>${summary.overdue}</b><span>overdue</span></div>
          <div class="card stat"><b>${summary.due_soon}</b><span>due in 7 days</span></div>
          <div class="card stat"><b>${summary.learning}</b><span>flagged for group learning</span></div>
        </div>
        ${presenting() ? "" : `<section class="card"><h2>Add an item</h2><p class="quiet">Anything raised after standup that's too big for it. Every item gets an owner and a next step.</p>
          <form id="add" class="grid2">${BA.form(ACTION_FIELDS(people).slice(0, 9).filter((f) => f.name !== "raised_on"), { status: "open", origin: "dev sync" })}
          <div class="actions"><button class="btn primary" type="submit">Add</button></div></form></section>`}
        <div class="row" style="margin-bottom:10px">
          <select id="f-status" style="max-width:180px">${["active", "overdue", ...ACTION_STATUS, "all"].map((s) => `<option${s === state.status ? " selected" : ""}>${s}</option>`).join("")}</select>
          <select id="f-owner" style="max-width:240px"><option value="">All owners</option>${owners.map(([id, n]) => `<option value="${id}"${String(id) === state.owner ? " selected" : ""}>${esc(n)}</option>`).join("")}</select>
        </div>
        <div class="tablewrap"><table class="data"><thead><tr><th>Question or concern</th><th>Kind</th><th>Raised by</th><th>Owner</th><th>Next action</th><th>Due</th><th>Status</th><th>Learning</th></tr></thead><tbody>${
          shown
            .map((i) => `<tr class="clickable" data-id="${i.id}"><td>${esc(i.concern)} ${BA.issueKeys(i.jira_keys)}${i.on_board ? ' <span class="pill accent" title="On the dev-sync board">board</span>' : ""}${i.update_url ? ` <a href="${esc(i.update_url)}" target="_blank" rel="noopener" class="pill good" onclick="event.stopPropagation()">update</a>` : ""}</td><td class="quiet">${esc(i.kind || "")}</td><td>${esc(i.raised_by_name || "")}</td><td>${esc(i.owner_name || "")}</td>
              <td>${esc(i.next_action)}</td><td${late(i) ? ' class="late"' : ""}>${BA.fmtDate(i.due)}</td>
              <td>${late(i) ? '<span class="pill bad">overdue</span>' : BA.statusPill(i.status)}</td><td>${i.learning ? '<span class="pill">yes</span>' : ""}</td></tr>`)
            .join("") || '<tr><td colspan="8" class="empty">Nothing matches.</td></tr>'
        }</tbody></table></div>
        <p class="quiet">I own the follow-up on every item, so nothing raised gets dropped.</p>
        ${presenting() ? "" : `<section class="card"><div class="row"><h2>Dev-sync board</h2><span class="spacer"></span><button class="btn" id="copy-board">Copy the board as Markdown</button></div>
          <p class="quiet">Rows marked "On the dev-sync board" with their shareable columns: topic, kind, who asked, experts, decision maker, next action, due, status and a link to the latest update. Until the share site exists, paste it into a page or message; later it becomes a gated board where each row opens its update presentation.</p></section>`}`;
      main.querySelector("#f-status").onchange = (e) => ((state.status = e.target.value), BA.rerender());
      main.querySelector("#f-owner").onchange = (e) => ((state.owner = e.target.value), BA.rerender());
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/dev-sync/${tr.dataset.id}`)));
      const cb = main.querySelector("#copy-board");
      if (cb) cb.onclick = BA.guard(async () => { const r = await BA.api("/api/dev-sync/board/export", { method: "POST" }); await navigator.clipboard.writeText(r.markdown); BA.toast(`Copied ${r.rows} row${r.rows === 1 ? "" : "s"}. Logged as an export.`); });
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          await BA.api("/api/actions", { method: "POST", body: { ...BA.readForm(add, ACTION_FIELDS(people).slice(0, 9).filter((f) => f.name !== "raised_on")), team_id: newTeamId() } });
          BA.rerender();
        });
    },
  });

  async function renderAction(main, id, people) {
    const rec = await BA.api(`/api/actions/${id}`);
    const fields = ACTION_FIELDS(people);
    document.getElementById("view-title").textContent = "Dev-sync item";
    if (presenting()) {
      main.innerHTML = `<section class="card">${BA.readOnly(fields.map((f) => (f.name.endsWith("_id") ? { ...f, name: f.name.replace("_id", "_name") } : f)), rec)}</section><p><a href="#/dev-sync">Dev-sync log</a></p>`;
      return;
    }
    main.innerHTML = `<p><a href="#/dev-sync">Dev-sync log</a></p><form id="item" class="card"><div class="grid2">${BA.form(fields, rec)}</div>
      <label>Subject matter experts</label><div class="case-picks">${people.filter((p) => p.active !== false).map((p) => `<label class="check"><input type="checkbox" name="expert_ids" value="${p.id}"${(rec.expert_ids || []).includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
      <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button>${BA.historyButton("action_item", id)}<button class="btn" type="button" id="make-update">Make an update</button><button class="btn primary" type="submit">Save</button></div></form>
      <section class="card" id="update-box" hidden></section>`;
    const form = main.querySelector("#item");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api(`/api/actions/${id}`, { method: "PATCH", body: { ...BA.readForm(form, fields), expert_ids: new FormData(form).getAll("expert_ids").map(Number) } });
      BA.toast("Saved.");
    });
    main.querySelector("#make-update").onclick = BA.guard(async () => {
      const s = await BA.api(`/api/actions/${id}/update-script`);
      const box = main.querySelector("#update-box");
      box.hidden = false;
      box.innerHTML = `<div class="row"><h2>Update script</h2><span class="spacer"></span><button class="btn" id="copy-script">Copy</button></div>
        <p class="quiet">A two-to-three-minute script drafted from this row. Record it, or build a short deck from it in the Comms studio (Video pitch template), then paste the link above under "Latest update" and save.</p>
        <div class="msg-preview">${BA.md(s.markdown)}</div>`;
      box.querySelector("#copy-script").onclick = BA.guard(async () => { await navigator.clipboard.writeText(s.markdown); BA.toast("Copied."); });
      box.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm("Delete this item?")) return;
      await BA.api(`/api/actions/${id}`, { method: "DELETE" });
      BA.go("/dev-sync");
    });
  }

  // ---------------------------------------------------------------- Group learning

  BA.view("/learning", {
    title: "Group learning",
    async render(main) {
      const [sessions, people] = await Promise.all([BA.api("/api/learning-sessions"), BA.api("/api/people")]);
      main.innerHTML = `<p class="quiet">Short team presentations on topics raised in dev sync or matched from team profiles.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Date</th><th>Topic</th><th>Presenter</th><th>Status</th><th>From</th>${presenting() ? "" : "<th></th>"}</tr></thead><tbody>${
          sessions
            .map((s) =>
              presenting()
                ? `<tr><td>${BA.fmtDate(s.date) || "Not set"}</td><td>${esc(s.topic)}</td><td>${esc(s.presenter_name || "Needs a presenter")}</td><td>${BA.statusPill(s.status === "proposed" ? "planned" : s.status)} ${esc(s.status)}</td><td class="quiet">${esc(s.source_concern || "")}</td></tr>`
                : `<tr data-id="${s.id}"><td><input type="date" name="date" value="${esc(s.date || "")}"></td><td><input name="topic" value="${esc(s.topic)}"></td>
                  <td><select name="presenter_id">${personOptions(people, s.presenter_id)}</select></td>
                  <td><select name="status">${["proposed", "scheduled", "done"].map((x) => `<option${x === s.status ? " selected" : ""}>${x}</option>`).join("")}</select></td>
                  <td class="quiet">${s.action_item_id ? `<a href="#/dev-sync/${s.action_item_id}">${esc(s.source_concern || "dev sync")}</a>` : "team profiles or added here"}</td>
                  <td><button class="btn danger" data-del="${s.id}">Delete</button></td></tr>`
            )
            .join("") || `<tr><td colspan="6" class="empty">No sessions yet. Flag a dev-sync item for group learning, or propose one from Skills and learning.</td></tr>`
        }</tbody></table></div>
        ${presenting() ? "" : `<section class="card" style="margin-top:16px"><form id="add" class="row">
          <input name="topic" placeholder="Topic" required style="max-width:340px"><select name="presenter_id" style="max-width:240px">${personOptions(people)}</select>
          <input type="date" name="date" style="max-width:180px"><button class="btn primary" type="submit">Add session</button></form></section>`}`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => {
        tr.onchange = BA.guard(async (e) => {
          const el = e.target;
          const value = el.name === "presenter_id" ? (el.value ? Number(el.value) : null) : el.value;
          await BA.api(`/api/learning-sessions/${tr.dataset.id}`, { method: "PATCH", body: { [el.name]: value } });
          BA.toast("Saved.");
        });
      });
      main.querySelectorAll("[data-del]").forEach((b) => (b.onclick = BA.guard(async () => {
        if (!confirm("Delete this session?")) return;
        await BA.api(`/api/learning-sessions/${b.dataset.del}`, { method: "DELETE" });
        BA.rerender();
      })));
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          await BA.api("/api/learning-sessions", {
            method: "POST",
            body: { topic: f.get("topic"), presenter_id: f.get("presenter_id") ? Number(f.get("presenter_id")) : null, date: f.get("date"), status: f.get("date") ? "scheduled" : "proposed" },
          });
          BA.rerender();
        });
    },
  });

  // ---------------------------------------------------------------- Escalation playbook

  BA.view("/escalation", {
    title: "Escalation playbook",
    async render(main, param) {
      const [systems, severities, incidents, people] = await Promise.all([
        BA.api("/api/systems"), BA.api("/api/severities"), BA.api("/api/incidents"), BA.api("/api/people"),
      ]);
      if (param) return renderEscalationSystem(main, Number(param), people, severities);
      const sysName = (id) => systems.find((s) => s.id === id)?.name || "";
      main.innerHTML = `
        <section class="card"><h2>Who to call</h2><p class="quiet">Pick a system to see its owner, first responder, backup and the escalation chain for business hours and out of hours.</p>
          <div class="deck-like">${systems.map((s) => `<a class="card sys-card" href="#/escalation/${s.id}"><b>${esc(s.name)}</b><div class="quiet">${esc(s.description || "")}</div></a>`).join("") || '<p class="quiet">No systems yet.</p>'}</div>
          ${presenting() ? "" : `<form id="add-sys" class="row"><input name="name" placeholder="[Placeholder system name]" required style="max-width:300px"><button class="btn primary" type="submit">Add system</button></form>`}</section>
        <section class="card"><h2>Severity levels</h2><div class="tablewrap"><table class="data"><thead><tr><th>Level</th><th>What it means</th><th>Response time</th><th>Who is paged</th><th>Who is told</th></tr></thead><tbody>${
          severities.map((v) => `<tr><td><b>${esc(v.level)}</b></td><td>${esc(v.definition)}</td><td>${esc(v.response_time)}</td><td>${esc(v.who_is_paged)}</td><td>${esc(v.who_is_told)}</td></tr>`).join("") ||
          '<tr><td colspan="5" class="empty">No severity levels yet.</td></tr>'
        }</tbody></table></div>
          ${presenting() ? "" : `<form id="add-sev" class="grid2">${BA.form([
            { name: "level", label: "Level", required: true, placeholder: "Sev 1" },
            { name: "definition", label: "What it means" },
            { name: "response_time", label: "Response time" },
            { name: "who_is_paged", label: "Who is paged" },
            { name: "who_is_told", label: "Who is told" },
          ])}<div class="actions"><button class="btn primary" type="submit">Add level</button></div></form>`}</section>
        <section class="card"><h2>Incident log</h2><div class="tablewrap"><table class="data"><thead><tr><th>Date</th><th>System</th><th>Severity</th><th>Summary</th><th>Resolved</th>${presenting() ? "" : "<th></th>"}</tr></thead><tbody>${
          incidents
            .map((i) => `<tr><td>${BA.fmtDate(i.date)}</td><td>${esc(i.system_name || "")}</td><td>${esc(i.severity_level || "")}</td><td>${esc(i.summary)} ${BA.keysEditor(`/api/incidents/${i.id}`, i.jira_keys)}</td>
              <td>${i.resolved_at ? BA.fmtDate(i.resolved_at) : '<span class="pill bad">open</span>'}</td>
              ${presenting() ? "" : `<td><button class="btn" data-follow="${i.id}">Add follow-up</button>${i.resolved_at ? "" : ` <button class="btn" data-resolve="${i.id}">Resolved</button>`}</td>`}</tr>`)
            .join("") || '<tr><td colspan="6" class="empty">No incidents logged.</td></tr>'
        }</tbody></table></div>
          ${presenting() ? "" : `<form id="add-inc" class="grid2">
            <label>Date<input type="date" name="date" value="${BA.today()}"></label>
            <label>System<select name="system_id">${`<option value=""></option>` + systems.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("")}</select></label>
            <label>Severity<select name="severity_id">${`<option value=""></option>` + severities.map((v) => `<option value="${v.id}">${esc(v.level)}</option>`).join("")}</select></label>
            <label>Summary<input name="summary" required></label>
            <div class="actions"><button class="btn primary" type="submit">Log incident</button></div></form>`}</section>`;
      const num = (v) => (v ? Number(v) : null);
      const on = (sel, fn) => { const el = main.querySelector(sel); if (el) el.onsubmit = BA.guard(async (e) => { e.preventDefault(); await fn(new FormData(e.target)); BA.rerender(); }); };
      on("#add-sys", async (f) => {
        const s = await BA.api("/api/systems", { method: "POST", body: { name: f.get("name") } });
        BA.go(`/escalation/${s.id}`);
      });
      on("#add-sev", (f) => BA.api("/api/severities", { method: "POST", body: Object.fromEntries(f) }));
      on("#add-inc", (f) =>
        BA.api("/api/incidents", { method: "POST", body: { date: f.get("date"), system_id: num(f.get("system_id")), severity_id: num(f.get("severity_id")), summary: f.get("summary") } })
      );
      main.querySelectorAll("[data-follow]").forEach((b) => (b.onclick = BA.guard(async () => {
        const item = await BA.api(`/api/incidents/${b.dataset.follow}/follow-up`, { method: "POST", body: {} });
        BA.go(`/dev-sync/${item.id}`);
      })));
      main.querySelectorAll("[data-resolve]").forEach((b) => (b.onclick = BA.guard(async () => {
        await BA.api(`/api/incidents/${b.dataset.resolve}`, { method: "PATCH", body: { resolved_at: BA.today() } });
        BA.rerender();
      })));
    },
  });

  async function renderEscalationSystem(main, id, people, severities) {
    const [d, vendors] = await Promise.all([BA.api(`/api/escalation/${id}`), BA.api("/api/vendors")]);
    const s = d.system;
    document.getElementById("view-title").textContent = s.name;
    const chain = (steps) =>
      steps.length
        ? `<ol class="chain">${steps.map((st) => `<li><b>${esc(st.person_name || "[No person]")}</b> <span class="pill">${esc(st.method)}</span>${st.note ? ` <span class="quiet">${esc(st.note)}</span>` : ""}
            ${presenting() ? "" : `<button class="btn danger" data-del-step="${st.id}">Remove</button>`}</li>`).join("")}</ol>`
        : '<p class="quiet">No steps yet.</p>';
    const roles = `<dl class="readonly"><dt>Owner</dt><dd>${esc(s.owner_name || "")}</dd><dt>First responder</dt><dd>${esc(s.first_responder_name || "")}</dd>
      <dt>Backup</dt><dd>${esc(s.backup_name || "")}</dd><dt>Opening a vendor case</dt><dd>${esc(s.how_to_open_case || "")}</dd>
      <dt>Business contacts</dt><dd>${[...(s.business_contact_ids || []).map((pid) => { const p = people.find((x) => x.id === pid); return p ? `<a href="#/people/${pid}">${esc(p.name)}</a>` : ""; }).filter(Boolean), ...(s.business_contacts ? [esc(s.business_contacts)] : [])].join(", ")}</dd>
      <dt>Vendor</dt><dd>${s.vendor_id ? `<a href="#/vendors/${s.vendor_id}">${esc(s.vendor_name || "vendor")}</a>` : ""}</dd>${s.vendor_support !== undefined ? `<dt>Vendor support</dt><dd>${esc(s.vendor_support || "")}</dd>` : ""}</dl>`;
    main.innerHTML = `<p><a href="#/escalation">Escalation playbook</a></p>
      <div class="cards">
        <section class="card"><h2>Who owns it</h2>${roles}</section>
        <section class="card"><h2>Business hours</h2>${chain(d.business_hours)}</section>
        <section class="card"><h2>Out of hours</h2>${chain(d.out_of_hours)}</section>
      </div>
      ${presenting() ? "" : `<section class="card"><h2>Add a step</h2><form id="step" class="row">
          <select name="person_id" required style="max-width:240px">${personOptions(people)}</select>
          <select name="method" style="max-width:140px">${["call", "page", "chat", "email", "in person"].map((m) => `<option>${m}</option>`).join("")}</select>
          <label class="check"><input type="checkbox" name="out_of_hours"> Out of hours</label>
          <input name="note" placeholder="Note (private)" style="max-width:260px"><button class="btn primary" type="submit">Add step</button></form></section>
        <form id="sys" class="card"><h2>Edit system</h2><div class="grid2">
          <label>Name<input name="name" value="${esc(s.name)}"></label>
          <label>Description<input name="description" value="${esc(s.description || "")}"></label>
          <label>Owner<select name="owner_id">${personOptions(people, s.owner_id)}</select></label>
          <label>First responder<select name="first_responder_id">${personOptions(people, s.first_responder_id)}</select></label>
          <label>Backup<select name="backup_id">${personOptions(people, s.backup_id)}</select></label>
          <label>Opening a vendor case<input name="how_to_open_case" value="${esc(s.how_to_open_case || "")}"></label>
          <label>Vendor support (private)<input name="vendor_support" value="${esc(s.vendor_support || "")}"></label>
          <label>Other business contacts <span class="quiet">(not in People)</span><input name="business_contacts" value="${esc(s.business_contacts || "")}"></label>
          <label>Vendor<select name="vendor_id"><option value=""></option>${vendors.map((v) => `<option value="${v.id}"${v.id === s.vendor_id ? " selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label></div>
          <label>Business contacts in People <span class="quiet">(Today reminds you to meet anyone you haven't talked to yet)</span></label><div class="case-picks">${people.filter((p) => p.active !== false).map((p) => `<label class="check"><input type="checkbox" name="business_contact_ids" value="${p.id}"${(s.business_contact_ids || []).includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
          <div class="actions"><button class="btn danger left" type="button" id="del">Delete system</button><button class="btn primary" type="submit">Save</button></div></form>`}
      <section class="card"><h2>Recent incidents</h2>${
        d.recent_incidents.map((i) => `<div class="item">${BA.fmtDate(i.date)} <b>${esc(i.severity_level || "")}</b> ${esc(i.summary)}</div>`).join("") || '<p class="quiet">None logged.</p>'
      }</section>`;
    if (presenting()) return;
    const step = main.querySelector("#step");
    step.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(step);
      const ooh = !!f.get("out_of_hours");
      const count = (ooh ? d.out_of_hours : d.business_hours).length;
      await BA.api("/api/escalation-steps", {
        method: "POST",
        body: { system_id: id, person_id: Number(f.get("person_id")), method: f.get("method"), out_of_hours: ooh, position: count, note: f.get("note") },
      });
      BA.rerender();
    });
    main.querySelectorAll("[data-del-step]").forEach((b) => (b.onclick = BA.guard(async () => {
      await BA.api(`/api/escalation-steps/${b.dataset.delStep}`, { method: "DELETE" });
      BA.rerender();
    })));
    const sys = main.querySelector("#sys");
    sys.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(sys);
      const body = Object.fromEntries(f);
      for (const k of ["owner_id", "first_responder_id", "backup_id", "vendor_id"]) body[k] = body[k] ? Number(body[k]) : null;
      body.business_contact_ids = f.getAll("business_contact_ids").map(Number);
      await BA.api(`/api/systems/${id}`, { method: "PATCH", body });
      BA.toast("Saved.");
      BA.rerender();
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm("Delete this system and its escalation chain?")) return;
      await BA.api(`/api/systems/${id}`, { method: "DELETE" });
      BA.go("/escalation");
    });
  }

  // ---------------------------------------------------------------- Vendors

  const VENDOR_TYPES = ["platform vendor", "consulting partner", "contractor agency", "tooling", "other"];
  const VENDOR_STATUS = ["active", "onboarding", "under review", "ended"];
  const CHANNELS = ["call", "meeting", "email", "chat", "other"];
  const tonePill = (text, tones) => `<span class="pill ${tones[text] || ""}">${esc(text)}</span>`;
  const VENDOR_TONES = { active: "good", onboarding: "warn", "under review": "warn", ended: "" };
  const CONCERN_TONES = { open: "warn", "in progress": "warn", resolved: "good" };
  const renewalPill = (v) => {
    if (!v.contract_end) return "";
    const days = Math.round((new Date(v.contract_end + "T12:00:00") - new Date(BA.today() + "T12:00:00")) / 864e5);
    if (days < 0) return '<span class="pill bad">contract ended</span>';
    if (days <= (v.renewal_notice_days || 0)) return `<span class="pill ${days <= 14 ? "bad" : "warn"}">renews in ${days} days</span>`;
    return `<span class="quiet">renews ${BA.fmtDate(v.contract_end)}</span>`;
  };

  BA.view("/vendors", {
    title: "Vendors",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderVendor(main, Number(param), people);
      const vendors = await BA.api("/api/vendors");
      main.innerHTML = `
        ${presenting() ? "" : `<section class="card"><h2>Add a vendor</h2><form id="add" class="grid2">
          <label>Name<input name="name" required placeholder="[Placeholder vendor name]"></label>
          <label>Type<select name="type">${VENDOR_TYPES.map((x) => `<option>${x}</option>`).join("")}</select></label>
          <div class="actions"><button class="btn primary" type="submit">Add vendor</button></div></form></section>`}
        <div class="tablewrap"><table class="data"><thead><tr><th>Vendor</th><th>Type</th><th>Status</th><th>Renewal</th><th>Open concerns</th><th>Last contact</th></tr></thead><tbody>${
          vendors
            .map((v) => `<tr class="clickable" data-id="${v.id}"><td><b>${esc(v.name)}</b></td><td>${esc(v.type)}</td><td>${tonePill(v.status, VENDOR_TONES)}</td>
              <td>${renewalPill(v)}</td><td>${v.open_concerns ? `<span class="pill warn">${v.open_concerns}</span>` : '<span class="quiet">none</span>'}</td><td>${BA.fmtDate(v.last_contact) || '<span class="quiet">never</span>'}</td></tr>`)
            .join("") || '<tr><td colspan="6" class="empty">No vendors yet.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/vendors/${tr.dataset.id}`)));
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          const v = await BA.api("/api/vendors", { method: "POST", body: { name: f.get("name"), type: f.get("type") } });
          BA.go(`/vendors/${v.id}`);
        });
    },
  });

  async function renderVendor(main, id, people) {
    const d = await BA.api(`/api/vendors/${id}/overview`);
    const v = d.vendor;
    document.getElementById("view-title").textContent = v.name;
    const concerns = `<section class="card"><h2>Open concerns</h2>${
      d.concerns
        .map((c) => `<div class="item">${tonePill(c.status, CONCERN_TONES)}
          <span>${esc(c.title)}</span>${BA.keysEditor(`/api/vendor-concerns/${c.id}`, c.jira_keys)}<span class="spacer"></span><span class="quiet">${esc(c.owner_name || "")} ${BA.fmtDate(c.due)}</span>
          ${presenting() || c.status === "resolved" ? "" : `<button class="btn" data-resolve="${c.id}">Resolved</button>`}</div>`)
        .join("") || '<p class="quiet">No concerns logged.</p>'
    }${presenting() ? "" : `<form id="add-concern" class="row" style="margin-top:10px">
        <input name="title" placeholder="New concern" required style="max-width:320px">
        <select name="owner_id" style="max-width:220px">${personOptions(people)}</select>
        <input type="date" name="due" style="max-width:170px"><button class="btn primary" type="submit">Add concern</button></form>`}</section>`;
    const followUps = `<section class="card"><h2>Follow-ups in the dev-sync log</h2>${
      d.follow_ups.map((a) => `<div class="item">${BA.statusPill(a.status)}<a href="#/dev-sync/${a.id}">${esc(a.concern)}</a><span class="spacer"></span><span class="quiet">${esc(a.owner_name || "")} ${BA.fmtDate(a.due)}</span></div>`).join("") ||
      '<p class="quiet">None yet. Add one from a logged conversation.</p>'
    }</section>`;
    const systems = d.systems.length ? `<p>Escalation: ${d.systems.map((s) => `<a href="#/escalation/${s.id}">${esc(s.name)}</a>`).join(", ")}</p>` : "";
    const summary = `<dl class="readonly"><dt>Type</dt><dd>${esc(v.type)}</dd><dt>Status</dt><dd>${esc(v.status)}</dd>
      <dt>Contract</dt><dd>${BA.fmtDate(v.contract_start)}${v.contract_end ? " to " + BA.fmtDate(v.contract_end) : ""} ${renewalPill(v)}</dd>
      <dt>Account contacts</dt><dd>${v.contacts.map((c) => `<a href="#/people/${c.id}">${esc(c.name)}</a>`).join(", ") || '<span class="quiet">none</span>'}</dd>
      <dt>Getting support</dt><dd>${esc(v.support_process || "")}</dd><dt>Service promise</dt><dd>${esc(v.service_promise || "")}</dd></dl>${systems}`;
    if (presenting()) {
      main.innerHTML = `<p><a href="#/vendors">All vendors</a></p><div class="cards"><section class="card"><h2>Overview</h2>${summary}</section>${concerns}</div>${followUps}`;
      return;
    }
    main.innerHTML = `<p><a href="#/vendors">All vendors</a></p>
      <div class="cards"><section class="card"><h2>Overview</h2>${summary}</section>${concerns}</div>
      <section class="card"><h2>Log a conversation</h2><form id="log" class="grid2">
        <label>Date<input type="date" name="date" value="${BA.today()}"></label>
        <label>Channel<select name="channel">${CHANNELS.map((c) => `<option>${c}</option>`).join("")}</select></label>
        <label>Summary<textarea name="summary" required placeholder="What was discussed and agreed"></textarea></label>
        <label>Concerns raised<textarea name="concerns" placeholder="Anything they're worried about, or we are"></textarea></label>
        <label>Who was involved</label><div class="row">${people.map((p) => `<label class="check"><input type="checkbox" name="people" value="${p.id}"${v.contact_ids.includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
        <div class="actions"><button class="btn primary" type="submit">Log conversation</button></div></form></section>
      <section class="card"><h2>Conversation log</h2>${
        d.interactions
          .map((i) => `<div class="item" style="display:block"><div class="row"><b>${BA.fmtDate(i.date)}</b><span class="pill">${esc(i.channel)}</span>
              <span class="quiet">${esc((i.people || []).join(", "))}</span><span class="spacer"></span><button class="btn" data-follow="${i.id}">Add follow-up</button></div>
              <div style="margin:6px 0 0">${BA.md(i.summary)}</div>${i.concerns ? `<p class="quiet" style="margin:4px 0 0">Concerns: ${esc(i.concerns)}</p>` : ""}</div>`)
          .join("") || '<p class="quiet">No conversations logged yet.</p>'
      }</section>
      ${followUps}
      <form id="vendor" class="card"><h2>Edit vendor</h2><div class="grid2">
        <label>Name<input name="name" value="${esc(v.name)}"></label>
        <label>Type<select name="type">${VENDOR_TYPES.map((x) => `<option${x === v.type ? " selected" : ""}>${x}</option>`).join("")}</select></label>
        <label>Status<select name="status">${VENDOR_STATUS.map((x) => `<option${x === v.status ? " selected" : ""}>${x}</option>`).join("")}</select></label>
        <label>Renewal notice (days)<input type="number" name="renewal_notice_days" value="${esc(v.renewal_notice_days)}"></label>
        <label>Contract start<input type="date" name="contract_start" value="${esc(v.contract_start || "")}"></label>
        <label>Contract end<input type="date" name="contract_end" value="${esc(v.contract_end || "")}"></label>
        <label>Getting support<textarea name="support_process">${esc(v.support_process || "")}</textarea></label>
        <label>Service promise<textarea name="service_promise">${esc(v.service_promise || "")}</textarea></label>
        <label>Commercial terms (private)<textarea name="commercial_terms">${esc(v.commercial_terms || "")}</textarea></label>
        <label>My notes (private)<textarea name="notes">${esc(v.notes || "")}</textarea></label>
        <label>Account contacts</label><div class="row">${people.map((p) => `<label class="check"><input type="checkbox" name="contacts" value="${p.id}"${v.contact_ids.includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div></div>
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete vendor</button><button class="btn primary" type="submit">Save</button></div></form>`;
    const ids = (form, name) => [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((x) => Number(x.value));
    const log = main.querySelector("#log");
    log.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(log);
      await BA.api("/api/vendor-interactions", {
        method: "POST",
        body: { vendor_id: id, date: f.get("date"), channel: f.get("channel"), summary: f.get("summary"), concerns: f.get("concerns"), people_ids: ids(log, "people") },
      });
      BA.toast("Conversation logged.");
      BA.rerender();
    });
    main.querySelectorAll("[data-follow]").forEach((b) => (b.onclick = BA.guard(async () => {
      const item = await BA.api(`/api/vendor-interactions/${b.dataset.follow}/follow-up`, { method: "POST", body: {} });
      BA.go(`/dev-sync/${item.id}`);
    })));
    main.querySelectorAll("[data-resolve]").forEach((b) => (b.onclick = BA.guard(async () => {
      await BA.api(`/api/vendor-concerns/${b.dataset.resolve}`, { method: "PATCH", body: { status: "resolved" } });
      BA.rerender();
    })));
    const addConcern = main.querySelector("#add-concern");
    addConcern.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(addConcern);
      await BA.api("/api/vendor-concerns", {
        method: "POST",
        body: { vendor_id: id, title: f.get("title"), owner_id: f.get("owner_id") ? Number(f.get("owner_id")) : null, due: f.get("due"), raised_on: BA.today() },
      });
      BA.rerender();
    });
    const form = main.querySelector("#vendor");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      await BA.api(`/api/vendors/${id}`, {
        method: "PATCH",
        body: {
          name: f.get("name"), type: f.get("type"), status: f.get("status"),
          renewal_notice_days: Number(f.get("renewal_notice_days") || 0),
          contract_start: f.get("contract_start"), contract_end: f.get("contract_end"),
          support_process: f.get("support_process"), service_promise: f.get("service_promise"),
          commercial_terms: f.get("commercial_terms"), notes: f.get("notes"), contact_ids: ids(form, "contacts"),
        },
      });
      BA.toast("Saved.");
      BA.rerender();
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm("Delete this vendor with its conversations and concerns? Dev-sync follow-ups stay.")) return;
      await BA.api(`/api/vendors/${id}`, { method: "DELETE" });
      BA.go("/vendors");
    });
  }

  // ---------------------------------------------------------------- Sprint notebook

  const CEREMONIES = ["planning", "refinement", "review", "retro", "dev sync", "ad hoc", "pi planning", "pi demo"];
  const ceremonyLabel = { "pi planning": "PI planning", "pi demo": "End-of-PI demo", "dev sync": "Dev sync", "ad hoc": "Ad hoc" };
  const cLabel = (c) => ceremonyLabel[c] || c[0].toUpperCase() + c.slice(1);
  const sprintRange = (s) => `${BA.fmtDate(s.start_date)} to ${BA.fmtDate(s.end_date)}`;

  BA.view("/sprints", {
    title: "Sprint notebook",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderSprint(main, Number(param), people);
      const [sprints, current, pis] = await Promise.all([BA.api("/api/sprints"), BA.api("/api/sprints/current"), BA.api("/api/program-increments")]);
      keepTeam(sprints);
      const piName = (id) => pis.find((p) => p.id === id)?.number;
      main.innerHTML = `
        <section class="card"><div class="row"><h2>${current ? `Sprint ${current.number}` : "No sprints yet"}</h2><span class="spacer"></span>
          ${presenting() ? "" : '<button class="btn primary" id="next">Start the next sprint</button>'}</div>
          ${current ? `<p>${esc(current.goal || "")}</p><p class="quiet">${sprintRange(current)} · ${esc(current.kind)}${current.pi_id ? ` · PI ${piName(current.pi_id)}` : ""}</p>
            <div class="actions"><a class="btn" href="#/sprints/${current.id}">Open the notebook</a></div>` : '<p class="quiet">Start the first sprint to begin taking ceremony notes.</p>'}</section>
        <div class="tablewrap"><table class="data"><thead><tr><th>Sprint</th><th>Dates</th><th>Goal</th><th>Kind</th><th>PI</th>${presenting() ? "" : "<th>Notes</th>"}</tr></thead><tbody>${
          sprints.map((s) => `<tr class="clickable" data-id="${s.id}"><td><b>${s.number}</b></td><td>${sprintRange(s)}</td><td>${esc(s.goal || "")}</td><td>${esc(s.kind)}</td><td>${s.pi_id ? piName(s.pi_id) : ""}</td>${presenting() ? "" : `<td>${s.note_count}</td>`}</tr>`).join("") ||
          '<tr><td colspan="6" class="empty">No sprints yet.</td></tr>'
        }</tbody></table></div>
        <section class="card" style="margin-top:16px"><h2>Program Increments</h2><p class="quiet">Only if the organization runs SAFe: several development sprints, then an innovation and planning sprint.</p>${
          pis.map((p) => `<div class="item"><b>PI ${p.number}</b><span class="quiet">${BA.fmtDate(p.start_date)} to ${BA.fmtDate(p.end_date)}</span><span>${esc(p.objectives || "")}</span></div>`).join("") || '<p class="quiet">None.</p>'
        }${presenting() ? "" : `<form id="add-pi" class="row" style="margin-top:8px"><input type="number" name="number" placeholder="PI number" required style="max-width:130px">
          <input type="date" name="start_date" style="max-width:170px"><input type="date" name="end_date" style="max-width:170px">
          <input name="objectives" placeholder="Objectives" style="max-width:320px"><button class="btn" type="submit">Add PI</button></form>`}</section>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/sprints/${tr.dataset.id}`)));
      const next = main.querySelector("#next");
      if (next)
        next.onclick = BA.guard(async () => {
          const s = await BA.api("/api/sprints/next", { method: "POST", body: newTeamId() ? { team_id: newTeamId() } : {} });
          BA.go(`/sprints/${s.id}`);
        });
      const addPi = main.querySelector("#add-pi");
      if (addPi)
        addPi.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(addPi);
          await BA.api("/api/program-increments", { method: "POST", body: { number: Number(f.get("number")), start_date: f.get("start_date"), end_date: f.get("end_date"), objectives: f.get("objectives") } });
          BA.rerender();
        });
    },
  });

  async function renderSprint(main, id, people) {
    const [d, pis] = await Promise.all([BA.api(`/api/sprints/${id}/notebook`), BA.api("/api/program-increments")]);
    const s = d.sprint;
    document.getElementById("view-title").textContent = `Sprint ${s.number}`;
    const itemRow = (i) => `<div class="item">${BA.statusPill(i.status)}<a href="#/dev-sync/${i.id}">${esc(i.concern)}</a><span class="spacer"></span><span class="quiet">${esc(i.owner_name || "")} ${BA.fmtDate(i.due)}</span></div>`;
    const head = `<section class="card"><h2>${esc(s.goal || "[No goal set]")}</h2><p class="quiet">${sprintRange(s)} · ${esc(s.kind)}${d.pi ? ` · PI ${d.pi.number}` : ""}</p></section>`;
    if (presenting()) {
      main.innerHTML = `<p><a href="#/sprints">All sprints</a></p>${head}<p class="quiet">Ceremony notes are private, so they're hidden while presenting.</p>`;
      return;
    }
    const noteCard = (n) => `<form class="card note" data-note="${n.id}"><div class="row"><h2>${cLabel(n.type)}</h2><span class="quiet">${BA.fmtDate(n.date)}</span><span class="spacer"></span>
        <select name="type" style="max-width:170px">${CEREMONIES.map((c) => `<option value="${c}"${c === n.type ? " selected" : ""}>${cLabel(c)}</option>`).join("")}</select>
        <input type="date" name="date" value="${esc(n.date || "")}" style="max-width:170px"></div>
      <div class="grid2">
        <label>What happened<textarea name="happened">${esc(n.happened || "")}</textarea></label>
        <label>What I noticed <span class="quiet">energy, who spoke and who didn't</span><textarea name="noticed">${esc(n.noticed || "")}</textarea></label>
        <label>Implementation thoughts<textarea name="thoughts">${esc(n.thoughts || "")}</textarea></label>
        <label>Follow-ups <span class="quiet">one per line</span><textarea name="follow_ups">${esc(n.follow_ups || "")}</textarea></label></div>
      <div class="actions"><button class="btn danger left" type="button" data-del-note="${n.id}">Delete</button>${BA.historyButton("ceremony_note", n.id)}
        <button class="btn" type="button" data-follow-note="${n.id}">First follow-up to dev-sync log</button><button class="btn primary" type="submit">Save</button></div></form>`;
    main.innerHTML = `<p><a href="#/sprints">All sprints</a></p>${head}
      ${d.carry_over.length ? `<section class="card"><h2>Still open from the last sprint</h2>${d.carry_over.map(itemRow).join("")}</section>` : ""}
      <section class="card"><h2>Add a ceremony note</h2><form id="add-note" class="row">
        <select name="type" style="max-width:200px">${CEREMONIES.map((c) => `<option value="${c}">${cLabel(c)}</option>`).join("")}</select>
        <input type="date" name="date" value="${BA.today()}" style="max-width:170px"><button class="btn primary" type="submit">Add note</button></form></section>
      ${d.notes.map(noteCard).join("") || '<p class="quiet">No notes in this sprint yet.</p>'}
      <section class="card"><h2>Dev-sync items from this sprint</h2>${d.items.map(itemRow).join("") || '<p class="quiet">None yet.</p>'}</section>
      <form id="edit-sprint" class="card"><h2>Sprint details</h2><div class="grid2">
        <label>Goal<input name="goal" value="${esc(s.goal || "")}"></label>
        <label>Kind<select name="kind">${["development", "innovation and planning"].map((k) => `<option${k === s.kind ? " selected" : ""}>${k}</option>`).join("")}</select></label>
        <label>Start<input type="date" name="start_date" value="${esc(s.start_date || "")}"></label>
        <label>End<input type="date" name="end_date" value="${esc(s.end_date || "")}"></label>
        <label>Program Increment<select name="pi_id"><option value=""></option>${pis.map((p) => `<option value="${p.id}"${p.id === s.pi_id ? " selected" : ""}>PI ${p.number}</option>`).join("")}</select></label></div>
        <div class="actions"><button class="btn primary" type="submit">Save</button></div></form>`;
    const addNote = main.querySelector("#add-note");
    addNote.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(addNote);
      await BA.api("/api/ceremony-notes", { method: "POST", body: { sprint_id: id, type: f.get("type"), date: f.get("date") } });
      BA.rerender();
    });
    main.querySelectorAll("form.note").forEach((form) => {
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        await BA.api(`/api/ceremony-notes/${form.dataset.note}`, { method: "PATCH", body: Object.fromEntries(f) });
        BA.toast("Saved.");
      });
    });
    main.querySelectorAll("[data-del-note]").forEach((b) => (b.onclick = BA.guard(async () => {
      if (!confirm("Delete this note?")) return;
      await BA.api(`/api/ceremony-notes/${b.dataset.delNote}`, { method: "DELETE" });
      BA.rerender();
    })));
    main.querySelectorAll("[data-follow-note]").forEach((b) => (b.onclick = BA.guard(async () => {
      const form = b.closest("form");
      await BA.api(`/api/ceremony-notes/${b.dataset.followNote}`, { method: "PATCH", body: Object.fromEntries(new FormData(form)) });
      const item = await BA.api(`/api/ceremony-notes/${b.dataset.followNote}/follow-up`, { method: "POST", body: {} });
      BA.go(`/dev-sync/${item.id}`);
    })));
    const edit = main.querySelector("#edit-sprint");
    edit.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(edit);
      await BA.api(`/api/sprints/${id}`, {
        method: "PATCH",
        body: { goal: f.get("goal"), kind: f.get("kind"), start_date: f.get("start_date"), end_date: f.get("end_date"), pi_id: f.get("pi_id") ? Number(f.get("pi_id")) : null },
      });
      BA.toast("Saved.");
      BA.rerender();
    });
  }

  // ---------------------------------------------------------------- Roadmap

  const ROADMAP_STATUS = ["not started", "in progress", "done", "at risk"];
  const ROADMAP_KINDS = ["ceremony", "agreement", "metric", "milestone"];
  const dayDateOf = (start, n) => {
    if (n == null) return "";
    if (!start) return `Day ${n}`;
    const d = new Date(start + "T12:00:00");
    d.setDate(d.getDate() + n - 1);
    return `Day ${n} · ${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
  };
  const starterButton = (what) =>
    presenting() ? "" : `<section class="card"><p class="quiet">Load the starter ${what}: the Agile adoption roadmap, the five RACI decisions and the four delivery metrics. Edit any of it afterwards.</p><button class="btn primary" data-starter>Load starter content</button></section>`;
  const wireStarter = (main) => {
    const b = main.querySelector("[data-starter]");
    if (b) b.onclick = BA.guard(async () => (await BA.api("/api/delivery/starter", { method: "POST" }), BA.rerender()));
  };

  BA.view("/roadmap", {
    title: "Roadmap",
    async render(main) {
      const [items, settings, people] = await Promise.all([BA.api("/api/roadmap"), BA.api("/api/toolkit/settings"), BA.api("/api/people")]);
      if (!items.length) {
        main.innerHTML = starterButton("roadmap");
        wireStarter(main);
        return;
      }
      const done = items.filter((i) => i.status === "done").length;
      main.innerHTML = `<p class="quiet">${done} of ${items.length} done. ${settings.start_date ? "" : 'Set the contract start date under <a href="#/me">My development</a> to turn days into dates.'}</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Item</th><th>Kind</th><th>Target</th><th>Status</th><th>Owner</th>${presenting() ? "" : "<th></th>"}</tr></thead><tbody>${items
          .map((i) => presenting()
            ? `<tr><td><b>${esc(i.title)}</b> ${BA.issueKeys(i.jira_keys)}<div class="quiet">${esc(i.description || "")}</div></td><td>${esc(i.kind)}</td><td>${dayDateOf(settings.start_date, i.target_day)}</td><td>${BA.statusPill(i.status)}</td><td>${esc(i.owner_name || "")}</td></tr>`
            : `<tr data-id="${i.id}"><td><b>${esc(i.title)}</b> ${BA.keysEditor(`/api/roadmap/${i.id}`, i.jira_keys)}<div class="quiet">${esc(i.description || "")}</div></td><td>${esc(i.kind)}</td>
              <td><input type="number" name="target_day" value="${esc(i.target_day ?? "")}" style="max-width:90px"> <span class="quiet">${dayDateOf(settings.start_date, i.target_day).replace(/^Day \d+ · /, "")}</span></td>
              <td><select name="status">${ROADMAP_STATUS.map((s) => `<option${s === i.status ? " selected" : ""}>${s}</option>`).join("")}</select></td>
              <td><select name="owner_id">${personOptions(people, i.owner_id)}</select></td><td><button class="btn danger" data-del="${i.id}">Delete</button></td></tr>`)
          .join("")}</tbody></table></div>
        ${presenting() ? "" : `<section class="card" style="margin-top:16px"><form id="add" class="row"><input name="title" placeholder="New roadmap item" required style="max-width:300px">
          <select name="kind" style="max-width:150px">${ROADMAP_KINDS.map((k) => `<option>${k}</option>`).join("")}</select>
          <input type="number" name="target_day" placeholder="Target day" style="max-width:120px"><button class="btn primary" type="submit">Add</button></form></section>`}`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onchange = BA.guard(async (e) => {
        const el = e.target;
        const value = el.name === "status" ? el.value : el.value === "" ? null : Number(el.value);
        await BA.api(`/api/roadmap/${tr.dataset.id}`, { method: "PATCH", body: { [el.name]: value } });
        if (el.name !== "owner_id") BA.rerender();
        else BA.toast("Saved.");
      })));
      main.querySelectorAll("[data-del]").forEach((b) => (b.onclick = BA.guard(async () => {
        if (!confirm("Delete this roadmap item?")) return;
        await BA.api(`/api/roadmap/${b.dataset.del}`, { method: "DELETE" });
        BA.rerender();
      })));
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          await BA.api("/api/roadmap", { method: "POST", body: { title: f.get("title"), kind: f.get("kind"), target_day: f.get("target_day") ? Number(f.get("target_day")) : null } });
          BA.rerender();
        });
    },
  });

  // ---------------------------------------------------------------- RACI

  BA.view("/raci", {
    title: "RACI",
    async render(main) {
      const d = await BA.api("/api/raci");
      if (!d.decisions.length) {
        main.innerHTML = starterButton("RACI");
        wireStarter(main);
        return;
      }
      const aCount = (dec) => Object.values(dec.cells).filter((l) => l === "A").length;
      const cell = (dec, role) =>
        presenting()
          ? `<td class="raci-cell">${esc(dec.cells[role] || "")}</td>`
          : `<td class="raci-cell"><select data-cell="${dec.id}" data-role="${esc(role)}"><option value=""></option>${["R", "A", "C", "I"].map((l) => `<option${dec.cells[role] === l ? " selected" : ""}>${l}</option>`).join("")}</select></td>`;
      main.innerHTML = `<p class="quiet">R does the work. A makes the final call, exactly one per row. C is asked before. I is told after. Blank cells are still to learn.</p>
        <div class="tablewrap"><table class="data raci"><thead><tr><th>Decision</th>${d.roles.map((r) => `<th>${esc(r)}</th>`).join("")}<th>Status</th></tr></thead><tbody>${d.decisions
          .map((dec) => `<tr><td><b>${esc(dec.decision)}</b>${aCount(dec) === 1 ? "" : ` <span class="pill ${aCount(dec) ? "bad" : "warn"}">${aCount(dec) ? "more than one A" : "no A yet"}</span>`}</td>
            ${d.roles.map((r) => cell(dec, r)).join("")}
            <td>${presenting() ? esc(dec.status) : `<select data-status="${dec.id}">${["to confirm", "confirmed", "changed"].map((s) => `<option${s === dec.status ? " selected" : ""}>${s}</option>`).join("")}</select>`}</td></tr>`)
          .join("")}</tbody></table></div>
        ${presenting() ? "" : `<section class="card" style="margin-top:16px"><form id="add" class="row"><input name="decision" placeholder="New decision" required style="max-width:320px"><button class="btn primary" type="submit">Add decision</button></form>
          <form id="roles" class="row" style="margin-top:10px"><input name="roles" value="${esc(d.roles.join(", "))}"><button class="btn" type="submit">Save roles</button></form>
          <p class="quiet">Roles are generic on purpose; rename them to fit the organization.</p></section>`}`;
      main.querySelectorAll("[data-cell]").forEach((sel) => (sel.onchange = BA.guard(async () => {
        await BA.api(`/api/raci/${sel.dataset.cell}/cell`, { method: "PUT", body: { role: sel.dataset.role, letter: sel.value || null } });
        BA.rerender();
      })));
      main.querySelectorAll("[data-status]").forEach((sel) => (sel.onchange = BA.guard(async () => {
        await BA.api(`/api/raci-decisions/${sel.dataset.status}`, { method: "PATCH", body: { status: sel.value } });
        BA.toast("Saved.");
      })));
      const add = main.querySelector("#add");
      if (add) {
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          await BA.api("/api/raci-decisions", { method: "POST", body: { decision: new FormData(add).get("decision"), position: d.decisions.length } });
          BA.rerender();
        });
        main.querySelector("#roles").onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          await BA.api("/api/raci/roles", { method: "PUT", body: { roles: new FormData(e.target).get("roles").split(",") } });
          BA.rerender();
        });
      }
    },
  });

  // ---------------------------------------------------------------- Risks and decisions

  BA.view("/risks", {
    title: "Risks and decisions",
    async render(main) {
      const [risks, decisions, people] = await Promise.all([BA.api("/api/risks"), BA.api("/api/decisions-needed"), BA.api("/api/people")]);
      keepTeam(risks);
      keepTeam(decisions);
      const levelPill = (l) => `<span class="pill ${l === "high" ? "bad" : l === "medium" ? "warn" : ""}">${esc(l)}</span>`;
      const ro = presenting();
      main.innerHTML = `
        <section class="card"><h2>Risks and issues</h2><div class="tablewrap"><table class="data"><thead><tr><th>Level</th><th>Risk or issue</th><th>Impact</th><th>Owner</th><th>Next step</th><th>Due</th><th>Status</th></tr></thead><tbody>${
          risks.map((r) => `<tr data-risk="${r.id}"><td>${levelPill(r.level)}</td><td><b>${esc(r.title)}</b> ${BA.keysEditor(`/api/risks/${r.id}`, r.jira_keys)}</td><td>${esc(r.impact || "")}</td><td>${esc(r.owner_name || "")}</td>
            <td>${esc(r.next_step || "")}</td><td>${BA.fmtDate(r.due)}</td>
            <td>${ro ? esc(r.status) : `<select name="status">${["open", "watching", "closed"].map((s) => `<option${s === r.status ? " selected" : ""}>${s}</option>`).join("")}</select>`}</td></tr>`).join("") ||
          '<tr><td colspan="7" class="empty">No risks logged.</td></tr>'
        }</tbody></table></div>
        ${ro ? "" : `<form id="add-risk" class="grid2">
          <label>Risk or issue<input name="title" required></label><label>Impact<input name="impact"></label>
          <label>Level<select name="level"><option>high</option><option selected>medium</option><option>low</option></select></label>
          <label>Owner<select name="owner_id">${personOptions(people)}</select></label>
          <label>Next step<input name="next_step"></label><label>Due<input type="date" name="due"></label>
          <div class="actions"><button class="btn primary" type="submit">Add risk</button></div></form>`}</section>
        <section class="card"><h2>Decisions needed</h2><div class="tablewrap"><table class="data"><thead><tr><th>Decision</th><th>From whom</th><th>Needed by</th><th>Status</th><th>Outcome</th></tr></thead><tbody>${
          decisions.map((d) => `<tr data-dec="${d.id}"><td><b>${esc(d.decision)}</b> ${BA.keysEditor(`/api/decisions-needed/${d.id}`, d.jira_keys)}</td><td>${esc(d.from_name || "")}</td><td>${BA.fmtDate(d.needed_by)}</td>
            <td>${ro ? esc(d.status) : `<select name="status">${["open", "decided"].map((s) => `<option${s === d.status ? " selected" : ""}>${s}</option>`).join("")}</select>`}</td>
            <td>${ro ? esc(d.outcome || "") : `<input name="outcome" value="${esc(d.outcome || "")}">`}</td></tr>`).join("") ||
          '<tr><td colspan="5" class="empty">No decisions pending.</td></tr>'
        }</tbody></table></div>
        ${ro ? "" : `<form id="add-dec" class="row" style="margin-top:10px"><input name="decision" placeholder="Decision needed" required style="max-width:320px">
          <select name="from_id" style="max-width:220px">${personOptions(people)}</select><input type="date" name="needed_by" style="max-width:170px">
          <button class="btn primary" type="submit">Add decision</button></form>`}</section>`;
      const num = (v) => (v ? Number(v) : null);
      main.querySelectorAll("tr[data-risk]").forEach((tr) => (tr.onchange = BA.guard(async (e) => {
        await BA.api(`/api/risks/${tr.dataset.risk}`, { method: "PATCH", body: { [e.target.name]: e.target.value } });
        BA.toast("Saved.");
      })));
      main.querySelectorAll("tr[data-dec]").forEach((tr) => (tr.onchange = BA.guard(async (e) => {
        await BA.api(`/api/decisions-needed/${tr.dataset.dec}`, { method: "PATCH", body: { [e.target.name]: e.target.value } });
        BA.toast("Saved.");
      })));
      const addRisk = main.querySelector("#add-risk");
      if (addRisk) {
        addRisk.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(addRisk));
          f.owner_id = num(f.owner_id);
          f.team_id = newTeamId();
          await BA.api("/api/risks", { method: "POST", body: f });
          BA.rerender();
        });
        main.querySelector("#add-dec").onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(e.target));
          f.from_id = num(f.from_id);
          f.team_id = newTeamId();
          await BA.api("/api/decisions-needed", { method: "POST", body: f });
          BA.rerender();
        });
      }
    },
  });

  // ---------------------------------------------------------------- Metrics

  BA.view("/metrics", {
    title: "Metrics",
    async render(main) {
      const metrics = await BA.api("/api/metrics");
      if (!metrics.length) {
        main.innerHTML = starterButton("metrics");
        wireStarter(main);
        return;
      }
      const fmt = (v, u) => (v === null || v === undefined ? '<span class="quiet">not set</span>' : `${Number(v).toLocaleString()} ${esc(u || "")}`);
      const onTrack = (m) => {
        if (m.latest == null || m.target == null) return "";
        const good = m.higher_is_better ? m.latest >= m.target : m.latest <= m.target;
        return `<span class="pill ${good ? "good" : "warn"}">${good ? "on target" : "off target"}</span>`;
      };
      main.innerHTML = `<p class="quiet">A few measures the team agrees to watch. Baselines come first; targets are the team's choice. An outside benchmark shows where the team stands without it being anyone's opinion.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Metric</th><th>Baseline</th><th>Target</th><th>Benchmark</th><th>Latest</th><th></th>${presenting() ? "" : "<th>Add a reading</th>"}</tr></thead><tbody>${metrics
          .map((m) => `<tr data-id="${m.id}"><td><b>${esc(m.name)}</b><div class="quiet">${esc(m.method || "")}</div></td>
            <td>${presenting() ? fmt(m.baseline, m.unit) : `<input type="number" step="any" name="baseline" value="${esc(m.baseline ?? "")}" style="max-width:110px">`}</td>
            <td>${presenting() ? fmt(m.target, m.unit) : `<input type="number" step="any" name="target" value="${esc(m.target ?? "")}" style="max-width:110px">`}</td>
            <td>${presenting() ? `${esc(m.benchmark || "")}<div class="quiet">${esc(m.benchmark_source || "")}</div>` : `<input name="benchmark" value="${esc(m.benchmark || "")}" placeholder="Outside reference" style="max-width:150px"><input name="benchmark_source" value="${esc(m.benchmark_source || "")}" placeholder="Source" style="max-width:150px;margin-top:4px">`}</td>
            <td>${fmt(m.latest, m.unit)}<div class="quiet">${BA.fmtDate(m.latest_date)}</div></td><td>${onTrack(m)}</td>
            ${presenting() ? "" : `<td><span class="row"><input type="date" data-rdate="${m.id}" value="${BA.today()}" style="max-width:160px"><input type="number" step="any" data-rval="${m.id}" placeholder="Value" style="max-width:100px"><button class="btn" data-radd="${m.id}">Add</button></span></td>`}</tr>`)
          .join("")}</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onchange = BA.guard(async (e) => {
        if (["benchmark", "benchmark_source"].includes(e.target.name)) { await BA.api(`/api/metrics/${tr.dataset.id}`, { method: "PATCH", body: { [e.target.name]: e.target.value || null } }); BA.toast("Saved."); return; }
        if (!["baseline", "target"].includes(e.target.name)) return;
        await BA.api(`/api/metrics/${tr.dataset.id}`, { method: "PATCH", body: { [e.target.name]: e.target.value === "" ? null : Number(e.target.value) } });
        BA.rerender();
      })));
      main.querySelectorAll("[data-radd]").forEach((b) => (b.onclick = BA.guard(async () => {
        const id = b.dataset.radd;
        const value = main.querySelector(`[data-rval="${id}"]`).value;
        if (value === "") throw new Error("Enter a value first.");
        await BA.api("/api/metric-readings", { method: "POST", body: { metric_id: Number(id), date: main.querySelector(`[data-rdate="${id}"]`).value, value: Number(value) } });
        BA.rerender();
      })));
    },
  });

  // ---------------------------------------------------------------- Weekly status

  // ---------------------------------------------------------------- Reports and the work log

  const LOG_KINDS = ["win", "progress", "blocker", "risk", "decision", "ask", "next", "note"];
  const LOG_LABELS = { win: "Win", progress: "Progress", blocker: "Blocker", risk: "Risk", decision: "Decision", ask: "Ask", next: "Next", note: "Note" };
  const LOG_TONES = { win: "good", progress: "accent", blocker: "bad", risk: "warn", decision: "", ask: "warn", next: "", note: "" };
  const LOG_AUDIENCES = ["leadership", "my manager", "just me"];
  const reportTabs = (active) => `<nav class="tabs">${[["", "Weekly report"], ["sprint", "Sprint report"], ["log", "Work log"], ["activity", "Activity"], ["saved", "Saved"]]
    .map(([k, l]) => `<a href="#/status${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${l}</a>`).join("")}</nav>`;
  const weekChip = (st) => st ? `<span class="week-chip" title="Week starting ${esc(st.week_start)}">W${st.iso_week}${st.role_week ? ` · role wk ${st.role_week}` : ""}${st.sprint_number ? ` · S${st.sprint_number} wk ${st.sprint_week}/${st.sprint_weeks}` : ""}</span>` : "";
  const hashQuery = () => new URLSearchParams((location.hash.split("?")[1] || ""));
  const keysIn = (v) => (v || "").split(/[,\s]+/).map((x) => x.trim()).filter(Boolean);

  // The draft, editable before it's copied or saved; edits stay in this browser tab until saved.
  function reportEditor(main, rep, kind) {
    const key = `ba-report-${kind}-${rep.audience}-${rep.period_start}`;
    let text = rep.markdown;
    try { text = sessionStorage.getItem(key) || rep.markdown; } catch {}
    const ro = presenting();
    const box = main.querySelector("#report-box");
    box.innerHTML = `<div class="row"><div class="seg" id="rep-mode"><button type="button" data-mode="preview" class="on">Preview</button><button type="button" data-mode="edit"${ro ? " disabled" : ""}>Edit</button></div>
        ${text !== rep.markdown ? '<span class="pill warn">edited</span><button class="btn" type="button" id="rep-reset">Start again from the data</button>' : ""}<span class="spacer"></span>
        ${ro ? "" : '<button class="btn" id="rep-script" title="A short narrated script from this report, to record as a video update">Video script</button><button class="btn" id="rep-copy">Copy Markdown</button><button class="btn" id="rep-save">Save draft</button><button class="btn primary" id="rep-sent">Save as sent</button>'}</div>
      <div id="rep-preview" class="msg-preview">${BA.md(text)}</div><textarea id="rep-text" rows="24" class="mono" hidden>${esc(text)}</textarea>`;
    const ta = box.querySelector("#rep-text"), pv = box.querySelector("#rep-preview");
    box.querySelectorAll("[data-mode]").forEach((b) => (b.onclick = () => {
      box.querySelectorAll("[data-mode]").forEach((x) => x.classList.toggle("on", x === b));
      const edit = b.dataset.mode === "edit";
      ta.hidden = !edit; pv.hidden = edit;
      if (!edit) pv.innerHTML = BA.md(ta.value);
    }));
    ta.oninput = () => { try { sessionStorage.setItem(key, ta.value); } catch {} };
    const reset = box.querySelector("#rep-reset");
    if (reset) reset.onclick = () => { try { sessionStorage.removeItem(key); } catch {} BA.rerender(); };
    if (ro) return;
    const body = (extra = {}) => ({ kind, audience: rep.audience, period_start: rep.period_start, period_end: rep.period_end, sprint_id: rep.sprint_id || null, title: rep.title, markdown: ta.value, ...extra });
    box.querySelector("#rep-script").onclick = BA.guard(async () => {
      const q = kind === "sprint" ? `kind=sprint&sprint_id=${rep.sprint_id}` : `kind=weekly&week=${rep.period_start}`;
      const s = await BA.api(`/api/reports/script?${q}&audience=${encodeURIComponent(rep.audience)}`);
      let sb = main.querySelector("#script-box");
      if (!sb) { sb = document.createElement("section"); sb.className = "card"; sb.id = "script-box"; box.after(sb); }
      sb.innerHTML = `<div class="row"><h2>Video script</h2><span class="spacer"></span><button class="btn" id="copy-vs">Copy</button></div><p class="quiet">Drafted from this report's sections. Say it in your own words; send the report itself as the written version.</p><div class="msg-preview">${BA.md(s.markdown)}</div>`;
      sb.querySelector("#copy-vs").onclick = BA.guard(async () => { await navigator.clipboard.writeText(s.markdown); BA.toast("Copied."); });
      sb.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    box.querySelector("#rep-copy").onclick = BA.guard(async () => {
      await navigator.clipboard.writeText(ta.value);
      await BA.api("/api/reports/exported", { method: "POST", body: { title: rep.title, markdown: ta.value, kind } });
      BA.toast("Copied. Logged as an export.");
    });
    box.querySelector("#rep-save").onclick = BA.guard(async () => { await BA.api("/api/reports", { method: "POST", body: body() }); try { sessionStorage.removeItem(key); } catch {} BA.toast("Saved under Saved."); });
    box.querySelector("#rep-sent").onclick = BA.guard(async () => {
      const to = prompt("Who did it go to? (optional)", rep.audience === "my manager" ? "[Manager]" : "[Leadership group]");
      if (to === null) return;
      await BA.api("/api/reports", { method: "POST", body: body({ status: "sent", sent_on: BA.today(), sent_to: to || null }) });
      try { sessionStorage.removeItem(key); } catch {}
      BA.toast("Saved as sent.");
      BA.go("/status/saved");
    });
  }

  const audiencePick = (aud) => `<div class="seg" id="aud">${["leadership", "my manager"].map((a) => `<button type="button" data-aud="${a}" class="${a === aud ? "on" : ""}">${a === "leadership" ? "Leadership" : "My manager"}</button>`).join("")}</div>`;
  const getAud = () => { try { return sessionStorage.getItem("ba-report-aud") || "leadership"; } catch { return "leadership"; } };
  const bindAud = (main) => main.querySelectorAll("[data-aud]").forEach((b) => (b.onclick = () => { try { sessionStorage.setItem("ba-report-aud", b.dataset.aud); } catch {} BA.rerender(); }));

  BA.view("/status", {
    title: "Reports",
    async render(main, param) {
      const views = { sprint: renderSprintReport, log: renderWorkLog, activity: renderActivity, saved: renderSaved };
      if (views[param]) return views[param](main);
      const q = hashQuery(), aud = getAud();
      const wk = await BA.api(`/api/weeks${q.get("week") ? `?on=${q.get("week")}` : ""}`);
      const rep = await BA.api(`/api/reports/weekly?week=${wk.start}&audience=${encodeURIComponent(aud)}`);
      const tone = { Green: "good", Yellow: "warn", Red: "bad" }[rep.overall];
      main.innerHTML = `${reportTabs("")}
        <section class="card"><div class="row"><select id="week-pick" style="max-width:340px">${wk.recent.map((w) => `<option value="${w.start}"${w.start === wk.start ? " selected" : ""}>${esc(w.label)}${w.sprint ? ` · ${esc(w.sprint.label)}` : ""}</option>`).join("")}</select>
          ${audiencePick(aud)}<span class="pill ${tone}">${esc(rep.overall)}</span><span class="quiet">suggested because ${esc(rep.reason)}</span></div>
          <p class="quiet">${[wk.sprint ? esc(wk.sprint.label) : "", wk.role_week ? `Week ${wk.role_week} in the role` : "", `${rep.counts.highlights} ${rep.counts.highlights === 1 ? "highlight" : "highlights"} and ${rep.counts.issues} ${rep.counts.issues === 1 ? "blocker or risk" : "blockers or risks"} logged`, `${rep.counts.stories} ${rep.counts.stories === 1 ? "story" : "stories"} finished (${rep.counts.points} points)`].filter(Boolean).join(" · ")}.
            ${aud === "leadership" ? "Built only from exportable data and work log entries marked for leadership." : "Also includes work log entries marked for your manager. Nothing private."} <a href="#/status/activity?week=${wk.start}">See everything that happened this week</a>.</p></section>
        <section class="card" id="report-box"></section>
        ${presenting() ? "" : `<details class="card"><summary><b>Week settings</b></summary><div class="row"><label>Weeks start on <select id="ws">${["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((n, i) => `<option value="${i}"${i === wk.week_start_day ? " selected" : ""}>${n}</option>`).join("")}</select></label>
          <label>Weekly report is due on <select id="rd">${["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((n, i) => `<option value="${i}"${i === wk.report_day ? " selected" : ""}>${n}</option>`).join("")}</select></label></div>
          <p class="quiet">Set your start date in Settings to count weeks in the role. Sprint weeks come from each sprint's start date: a two-week sprint has a week 1 and a week 2.</p></details>`}`;
      reportEditor(main, rep, "weekly");
      bindAud(main);
      main.querySelector("#week-pick").onchange = (e) => BA.go(`/status?week=${e.target.value}`);
      const ws = main.querySelector("#ws");
      if (ws) {
        ws.onchange = BA.guard(async () => { await BA.api("/api/weeks/settings", { method: "PUT", body: { week_start_day: Number(ws.value) } }); BA.rerender(); });
        main.querySelector("#rd").onchange = BA.guard(async (e) => { await BA.api("/api/weeks/settings", { method: "PUT", body: { report_day: Number(e.target.value) } }); BA.toast("Saved."); });
      }
    },
  });

  async function renderSprintReport(main) {
    const sprints = (await BA.api("/api/sprints")).filter((s) => s.start_date);
    keepTeam(sprints);
    if (!sprints.length) { main.innerHTML = `${reportTabs("sprint")}<p class="empty">No sprints with a start date yet. Add one in the <a href="#/sprints">Sprint notebook</a>.</p>`; return; }
    const q = hashQuery(), aud = getAud();
    const current = await BA.api("/api/sprints/current");
    const sid = Number(q.get("sprint")) || (current && current.id) || sprints[0].id;
    const rep = await BA.api(`/api/reports/sprint?sprint_id=${sid}&audience=${encodeURIComponent(aud)}`);
    const p = rep.progress;
    main.innerHTML = `${reportTabs("sprint")}
      <section class="card"><div class="row"><select id="sprint-pick" style="max-width:260px">${sprints.map((s) => `<option value="${s.id}"${s.id === sid ? " selected" : ""}>Sprint ${s.number} (${BA.fmtDate(s.start_date)})</option>`).join("")}</select>${audiencePick(aud)}</div>
        <div class="sprint-weeks">${rep.weeks.map((w) => `<div class="sw"><b>Week ${w.week}</b><span class="quiet">${BA.fmtDate(w.start)} to ${BA.fmtDate(w.end)}</span><span>${w.stories} stories · ${w.points} points</span>
          <a href="#/status?week=${w.start}">Weekly report</a></div>`).join("")}
          <div class="sw"><b>Sprint</b><span class="quiet">${esc(rep.sprint.goal || "No goal set")}</span><span>${p.done_points} of ${p.committed} points · ${p.done_stories} of ${p.stories} stories</span></div></div></section>
      <section class="card" id="report-box"></section>`;
    reportEditor(main, rep, "sprint");
    bindAud(main);
    main.querySelector("#sprint-pick").onchange = (e) => BA.go(`/status/sprint?sprint=${e.target.value}`);
  }

  async function renderWorkLog(main) {
    const ro = presenting();
    const q = hashQuery();
    const wk = await BA.api(`/api/weeks${q.get("week") ? `?on=${q.get("week")}` : ""}`);
    const entries = await BA.api("/api/log-entries");
    const shown = entries.filter((e) => e.date >= wk.recent[wk.recent.length - 1].start);
    const byWeek = wk.recent.map((w) => [w, shown.filter((e) => e.date >= w.start && e.date <= w.end)]).filter(([, l]) => l.length);
    const fields = (e = {}) => `<div class="row"><input type="date" name="date" value="${esc(e.date || BA.today())}" style="max-width:160px"><select name="kind" style="max-width:130px">${LOG_KINDS.map((k) => `<option value="${k}"${k === (e.kind || "progress") ? " selected" : ""}>${LOG_LABELS[k]}</option>`).join("")}</select>
        <select name="audience" style="max-width:150px" title="Who can see this">${LOG_AUDIENCES.map((a) => `<option value="${a}"${a === (e.audience || "leadership") ? " selected" : ""}>For ${a}</option>`).join("")}</select>
        <input name="jira_keys" value="${esc((e.jira_keys || []).join(", "))}" placeholder="Jira keys (optional)" style="max-width:200px"></div>
      <input name="text" value="${esc(e.text || "")}" required placeholder="What happened, in a sentence you'd put in the report">
      <textarea name="details" rows="2" placeholder="Details (optional)">${esc(e.details || "")}</textarea>`;
    const read = (form) => { const f = new FormData(form); return { date: f.get("date"), kind: f.get("kind"), audience: f.get("audience"), jira_keys: keysIn(f.get("jira_keys")), text: f.get("text"), details: f.get("details") || null }; };
    main.innerHTML = `${reportTabs("log")}
      <p class="quiet">Note things as they happen: wins, progress, blockers, decisions, asks and what's next. Each entry lands in the week and sprint week of its date, and flows into the weekly and sprint reports for the audience you choose. "Just me" entries never leave the toolkit.</p>
      ${ro ? "" : `<form id="add-log" class="card log-form"><h2>Log something</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Log</button></div></form>`}
      ${byWeek.map(([w, list]) => `<section class="card"><div class="row"><h2>${esc(w.label)}</h2>${w.sprint ? `<span class="pill">${esc(w.sprint.label)}</span>` : ""}${w.role_week ? `<span class="quiet">week ${w.role_week} in the role</span>` : ""}<span class="spacer"></span><a href="#/status?week=${w.start}">Report</a></div>
        ${list.map((e) => `<details class="plan-item log-entry" data-log="${e.id}"><summary><span class="quiet log-day">${BA.fmtDate(e.date)}</span><span class="pill ${LOG_TONES[e.kind]}">${LOG_LABELS[e.kind]}</span><span>${esc(e.text)}</span>${(e.jira_keys || []).map((k) => `<span class="jira-key">${esc(k)}</span>`).join("")}<span class="spacer"></span><span class="quiet">${esc(e.audience)}</span></summary>
          ${e.details ? BA.md(e.details) : ""}${ro ? "" : `<form>${fields(e)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("log_entry", e.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("")}</section>`).join("") || '<p class="empty">Nothing logged in the last 12 weeks.</p>'}`;
    if (ro) return;
    const add = main.querySelector("#add-log");
    add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/log-entries", { method: "POST", body: read(add) }); BA.toast("Logged."); BA.rerender(); });
    main.querySelectorAll("[data-log]").forEach((det) => {
      const id = det.dataset.log, form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/log-entries/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this entry?")) return; await BA.api(`/api/log-entries/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderActivity(main) {
    const q = hashQuery();
    const wk = await BA.api(`/api/weeks${q.get("week") ? `?on=${q.get("week")}` : ""}`);
    const d = await BA.api(`/api/activity?start=${wk.start}&end=${wk.end}`);
    if (d.hidden) { main.innerHTML = `${reportTabs("activity")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const evText = (ev) => ev.event === "added" ? "added" : ev.event === "finished" ? `finished (${esc(ev.to)})` : `${esc(ev.from)} → ${esc(ev.to)}`;
    main.innerHTML = `${reportTabs("activity")}
      <section class="card"><div class="row"><select id="week-pick" style="max-width:340px">${wk.recent.map((w) => `<option value="${w.start}"${w.start === wk.start ? " selected" : ""}>${esc(w.label)}${w.sprint ? ` · ${esc(w.sprint.label)}` : ""}</option>`).join("")}</select></div>
        <p class="quiet">Everything you added or moved forward in the toolkit this week, by day. Private. Use "Add to log" to put something into a report, in your own words and for the audience you choose.</p></section>
      ${d.days.map((day) => `<section class="card"><div class="row"><h2>${new Date(day.date + "T12:00").toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}</h2>${weekChip(day.stamp)}</div>
        ${day.log.map((e) => `<div class="item"><span class="pill ${LOG_TONES[e.kind]}">${LOG_LABELS[e.kind]}</span><span>${esc(e.text)}</span><span class="spacer"></span><span class="quiet">logged · ${esc(e.audience)}</span></div>`).join("")}
        ${day.events.map((ev, i) => `<div class="item"><span class="pill${ev.event === "finished" ? " good" : ""}">${esc(ev.type)}</span><a href="#${ev.path}">${esc(ev.title)}</a><span class="quiet">${evText(ev)}${ev.points ? ` · ${ev.points} pts` : ""}</span><span class="spacer"></span>
          ${ev.promoted ? '<span class="quiet">in the log</span>' : `<button class="btn" data-promote="${day.date}|${i}">Add to log</button>`}</div>`).join("")}</section>`).join("") || '<p class="empty">Nothing recorded this week.</p>'}`;
    main.querySelector("#week-pick").onchange = (e) => BA.go(`/status/activity?week=${e.target.value}`);
    main.querySelectorAll("[data-promote]").forEach((b) => (b.onclick = BA.guard(async () => {
      const [dd, i] = b.dataset.promote.split("|");
      const ev = d.days.find((x) => x.date === dd).events[Number(i)];
      const text = prompt("How should this read in a report?", `${ev.event === "finished" ? "Finished: " : ""}${ev.title}`);
      if (!text) return;
      const kind = ev.event === "finished" ? "win" : ev.entity === "risk" ? "risk" : ev.entity === "decision_needed" ? "decision" : "progress";
      await BA.api("/api/activity/promote", { method: "POST", body: { entity: ev.entity, id: ev.id, date: ev.date, kind, text, audience: "my manager" } });
      BA.toast("Added to the work log, for your manager. Change the audience in the Work log.");
      BA.rerender();
    })));
  }

  async function renderSaved(main) {
    const list = await BA.api("/api/reports");
    const ro = presenting();
    main.innerHTML = `${reportTabs("saved")}
      <section class="card"><h2>Saved reports</h2><p class="quiet">What you saved or sent, as it read at the time. Edits keep a history.</p>
        ${list.map((r) => `<details class="plan-item" data-rep="${r.id}"><summary><span class="pill ${r.status === "sent" ? "good" : ""}">${esc(r.status)}</span><b>${esc(r.title)}</b><span class="quiet">${esc(r.audience)}</span><span class="spacer"></span>
            <span class="quiet">${r.sent_on ? `sent ${BA.fmtDate(r.sent_on)}${r.sent_to ? ` to ${esc(r.sent_to)}` : ""}` : `saved ${BA.fmtDate(r.created_on)}`}</span></summary>
          <div class="msg-preview">${BA.md(r.markdown)}</div>
          ${ro ? "" : `<div class="actions"><button class="btn danger left" data-del>Delete</button>${BA.historyButton("report", r.id)}<button class="btn" data-copy>Copy Markdown</button>${r.status === "sent" ? "" : '<button class="btn primary" data-sent>Mark sent</button>'}</div>`}</details>`).join("") || '<p class="quiet">Nothing saved yet.</p>'}</section>`;
    if (ro) return;
    main.querySelectorAll("[data-rep]").forEach((det) => {
      const r = list.find((x) => x.id === Number(det.dataset.rep));
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this saved report?")) return; await BA.api(`/api/reports/${r.id}`, { method: "DELETE" }); BA.rerender(); });
      det.querySelector("[data-copy]").onclick = BA.guard(async () => { await navigator.clipboard.writeText(r.markdown); await BA.api("/api/reports/exported", { method: "POST", body: { title: r.title, markdown: r.markdown, kind: r.kind } }); BA.toast("Copied. Logged as an export."); });
      const sent = det.querySelector("[data-sent]");
      if (sent) sent.onclick = BA.guard(async () => { const to = prompt("Who did it go to? (optional)", ""); if (to === null) return; await BA.api(`/api/reports/${r.id}`, { method: "PATCH", body: { status: "sent", sent_on: BA.today(), sent_to: to || null } }); BA.rerender(); });
    });
  }

  // ---------------------------------------------------------------- Retrospectives

  const RETRO_FORMATS = ["went well / didn't / ideas", "start / stop / continue", "mad / sad / glad", "4 Ls"];
  const COMMIT_STATUS = ["committed", "in progress", "done", "dropped"];
  const COMMIT_TONES = { committed: "", "in progress": "warn", done: "good", dropped: "" };

  BA.view("/retros", {
    title: "Retrospectives",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderRetro(main, Number(param), people);
      const [retros, sprints, current, improvements, patterns] = await Promise.all([
        BA.api("/api/retros"), BA.api("/api/sprints"), BA.api("/api/sprints/current"), BA.api("/api/improvements"), BA.api("/api/retros/patterns"),
      ]);
      keepTeam(retros);
      keepTeam(sprints);
      const open = improvements.filter((c) => c.status === "committed" || c.status === "in progress");
      main.innerHTML = `
        ${presenting() ? "" : `<section class="card"><h2>New retrospective</h2><form id="new" class="row">
          <select name="sprint_id" style="max-width:200px"><option value="">No sprint</option>${sprints.map((s) => `<option value="${s.id}"${current && s.id === current.id ? " selected" : ""}>Sprint ${s.number}</option>`).join("")}</select>
          <select name="format" style="max-width:240px">${RETRO_FORMATS.map((f) => `<option>${f}</option>`).join("")}</select>
          <input type="date" name="date" value="${BA.today()}" style="max-width:170px"><button class="btn primary" type="submit">Start retro</button></form></section>`}
        <div class="cards">
          <section class="card"><h2>Improvement backlog</h2><p class="quiet">Every commitment still open, from whichever sprint it came up in.</p>${
            open.map((c) => `<div class="item">${tonePill(c.status, COMMIT_TONES)}<span>${esc(c.commitment)}</span><span class="spacer"></span><span class="quiet">${c.sprint_number ? `sprint ${c.sprint_number}` : ""} ${esc(c.owner_name || "")}</span></div>`).join("") ||
            '<p class="quiet">Nothing open. Every commitment is done or dropped.</p>'
          }</section>
          <section class="card"><h2>Recurring topics</h2><p class="quiet">Topics tagged in more than one retro.</p>${
            patterns.map((p) => `<div class="item"><b>${esc(p.topic)}</b><span class="spacer"></span><span class="quiet">${p.retros} retros · sprints ${p.sprints.join(", ")}</span>${p.listening_theme ? '<span class="pill">also a listening-tour theme</span>' : ""}</div>`).join("") ||
            '<p class="quiet">No repeats yet. Tag discussion items with a topic to spot them.</p>'
          }</section></div>
        <div class="tablewrap"><table class="data"><thead><tr><th>Date</th><th>Sprint</th><th>Format</th><th>Items</th><th>Commitments</th></tr></thead><tbody>${
          retros.map((r) => `<tr class="clickable" data-id="${r.id}"><td>${BA.fmtDate(r.date)}</td><td>${r.sprint_number ? `Sprint ${r.sprint_number}` : ""}</td><td>${esc(r.format)}</td><td>${r.item_count}</td><td>${r.commitment_count}</td></tr>`).join("") ||
          '<tr><td colspan="5" class="empty">No retrospectives yet.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/retros/${tr.dataset.id}`)));
      const form = main.querySelector("#new");
      if (form)
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          const r = await BA.api("/api/retros", { method: "POST", body: { sprint_id: f.get("sprint_id") ? Number(f.get("sprint_id")) : null, format: f.get("format"), date: f.get("date"), team_id: newTeamId() } });
          BA.go(`/retros/${r.id}`);
        });
    },
  });

  async function renderRetro(main, id, people) {
    const d = await BA.api(`/api/retros/${id}/board`);
    const r = d.retro;
    const ro = presenting();
    document.getElementById("view-title").textContent = `Retrospective${r.sprint_number ? `: sprint ${r.sprint_number}` : ""}`;
    const itemCard = (i) => `<div class="retro-item"><div>${esc(i.text)}</div><div class="row">
        ${i.topic ? `<span class="pill">${esc(i.topic)}</span>` : ""}<span class="spacer"></span>
        <button class="icon-btn" title="Vote" data-vote="${i.id}">${BA.icon("thumbs-up")}</button><b>${i.votes}</b>
        ${ro ? "" : `<button class="btn" data-commit="${i.id}" title="Make this a commitment">Commit</button>`}</div></div>`;
    main.innerHTML = `<p><a href="#/retros">All retrospectives</a></p>
      <section class="card"><div class="row"><h2>${r.date ? BA.fmtDate(r.date) : "No date set"}</h2><span class="pill">${esc(r.format)}</span><span class="spacer"></span>
        <span class="quiet">${r.attendees.length ? "With " + esc(r.attendees.join(", ")) : ""}</span></div>
        ${r.summary ? BA.md(r.summary) : ""}
        ${ro ? "" : `<p class="quiet">Your private impressions belong in the <a href="#/sprints${r.sprint_id ? "/" + r.sprint_id : ""}">sprint notebook</a>'s retro note.</p>`}</section>
      ${d.carried_forward.length ? `<section class="card"><h2>Did we do what we said?</h2><p class="quiet">Open commitments from earlier retros.</p>${d.carried_forward
        .map((c) => `<div class="item" data-carry="${c.id}"><span>${esc(c.commitment)}</span>${BA.keysEditor(`/api/retro-commitments/${c.id}`, c.jira_keys)}<span class="quiet">${c.sprint_number ? `sprint ${c.sprint_number}` : ""} ${esc(c.owner_name || "")}</span><span class="spacer"></span>
          ${ro ? tonePill(c.status, COMMIT_TONES) : `<select name="status" style="max-width:140px">${COMMIT_STATUS.map((s) => `<option${s === c.status ? " selected" : ""}>${s}</option>`).join("")}</select>
          <input name="outcome" placeholder="Outcome" value="${esc(c.outcome || "")}" style="max-width:220px">`}</div>`)
        .join("")}</section>` : ""}
      <div class="retro-board" style="grid-template-columns: repeat(${d.columns.length}, minmax(220px, 1fr))">${d.columns
        .map((col) => `<section class="card retro-col"><h2>${esc(col)}</h2>${(d.items[col] || []).map(itemCard).join("") || '<p class="quiet">Nothing yet.</p>'}
          ${ro ? "" : `<form class="add-item" data-col="${esc(col)}"><input name="text" placeholder="Add a point" required><input name="topic" placeholder="Topic tag (optional)"><button class="btn" type="submit">Add</button></form>`}</section>`)
        .join("")}</div>
      <section class="card"><h2>What we're committing to</h2>${
        d.commitments.map((c) => `<div class="item" data-cm="${c.id}"><span>${esc(c.commitment)}</span>${BA.keysEditor(`/api/retro-commitments/${c.id}`, c.jira_keys)}<span class="spacer"></span>
          ${ro ? `${esc(c.owner_name || "")} ${BA.fmtDate(c.due)} ${tonePill(c.status, COMMIT_TONES)}` : `<select name="owner_id" style="max-width:200px">${personOptions(people, c.owner_id)}</select>
          <input type="date" name="due" value="${esc(c.due || "")}" style="max-width:160px">
          <select name="status" style="max-width:140px">${COMMIT_STATUS.map((s) => `<option${s === c.status ? " selected" : ""}>${s}</option>`).join("")}</select>`}</div>`).join("") ||
        '<p class="quiet">No commitments yet. Use "Commit" on a point, or add one here.</p>'
      }${ro ? "" : `<form id="add-cm" class="row" style="margin-top:10px"><input name="commitment" placeholder="We will…" required style="max-width:380px">
        <select name="owner_id" style="max-width:200px">${personOptions(people)}</select><input type="date" name="due" style="max-width:160px"><button class="btn primary" type="submit">Add commitment</button></form>`}</section>
      ${ro ? "" : `<form id="retro-edit" class="card"><h2>Retro details</h2><div class="grid2">
        <label>Format<select name="format">${RETRO_FORMATS.map((f) => `<option${f === r.format ? " selected" : ""}>${f}</option>`).join("")}</select></label>
        <label>Date<input type="date" name="date" value="${esc(r.date || "")}"></label>
        <label>Summary<textarea name="summary">${esc(r.summary || "")}</textarea></label>
        <div><label>Who was there</label><div class="row">${people.map((p) => `<label class="check"><input type="checkbox" name="att" value="${p.id}"${r.attendee_ids.includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div></div></div>
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete retro</button>${BA.historyButton("retro", id)}<button class="btn primary" type="submit">Save</button></div></form>`}`;
    main.querySelectorAll("[data-vote]").forEach((b) => (b.onclick = BA.guard(async () => (await BA.api(`/api/retro-items/${b.dataset.vote}/vote`, { method: "POST", body: {} }), BA.rerender()))));
    if (ro) return;
    main.querySelectorAll("form.add-item").forEach((form) => (form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      await BA.api("/api/retro-items", { method: "POST", body: { retro_id: id, column_name: form.dataset.col, text: f.get("text"), topic: f.get("topic") } });
      BA.rerender();
    })));
    main.querySelectorAll("[data-commit]").forEach((b) => (b.onclick = BA.guard(async () => (await BA.api(`/api/retro-items/${b.dataset.commit}/commit`, { method: "POST", body: {} }), BA.rerender()))));
    main.querySelectorAll("[data-carry]").forEach((row) => (row.onchange = BA.guard(async (e) => {
      await BA.api(`/api/retro-commitments/${row.dataset.carry}/review`, { method: "POST", body: { [e.target.name]: e.target.value, reviewed_in_id: id } });
      BA.toast("Recorded.");
    })));
    main.querySelectorAll("[data-cm]").forEach((row) => (row.onchange = BA.guard(async (e) => {
      const el = e.target;
      await BA.api(`/api/retro-commitments/${row.dataset.cm}`, { method: "PATCH", body: { [el.name]: el.name === "owner_id" ? (el.value ? Number(el.value) : null) : el.value } });
      BA.toast("Saved.");
    })));
    main.querySelector("#add-cm").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      await BA.api("/api/retro-commitments", { method: "POST", body: { retro_id: id, sprint_id: r.sprint_id, commitment: f.get("commitment"), owner_id: f.get("owner_id") ? Number(f.get("owner_id")) : null, due: f.get("due") } });
      BA.rerender();
    });
    const edit = main.querySelector("#retro-edit");
    edit.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(edit);
      await BA.api(`/api/retros/${id}`, { method: "PATCH", body: { format: f.get("format"), date: f.get("date"), summary: f.get("summary"), attendee_ids: [...edit.querySelectorAll('input[name="att"]:checked')].map((x) => Number(x.value)) } });
      BA.rerender();
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm("Delete this retro with its points and commitments?")) return;
      await BA.api(`/api/retros/${id}`, { method: "DELETE" });
      BA.go("/retros");
    });
  }

  // ---------------------------------------------------------------- PI planning

  const PRIORITIES = ["highest", "high", "medium", "low"];
  const WORK_STATUS = ["not started", "in progress", "done", "blocked"];
  const PRIORITY_TONES = { highest: "bad", high: "warn", medium: "", low: "" };
  const ROAM = ["unroamed", "resolved", "owned", "accepted", "mitigated"];
  const MILESTONE_KINDS = ["release", "freeze", "demo", "innovation and planning", "other"];
  const opts = (list, sel) => list.map((x) => `<option${x === sel ? " selected" : ""}>${x}</option>`).join("");

  BA.view("/pi", {
    title: "PI planning",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderPi(main, Number(param), people);
      const pis = await BA.api("/api/program-increments");
      main.innerHTML = `<p class="quiet">For organizations running SAFe: plan a Program Increment's objectives, features, stories, dependencies and risks together, then present the board.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>PI</th><th>Dates</th><th>Objectives</th><th>Confidence</th></tr></thead><tbody>${
          pis.map((p) => `<tr class="clickable" data-id="${p.id}"><td><b>PI ${p.number}</b></td><td>${BA.fmtDate(p.start_date)} to ${BA.fmtDate(p.end_date)}</td><td>${esc(p.objectives || "")}</td>
            <td>${p.confidence != null ? `<span class="pill ${p.confidence >= 3 ? "good" : "warn"}">${p.confidence} of 5</span>` : '<span class="quiet">not voted</span>'}</td></tr>`).join("") ||
          '<tr><td colspan="4" class="empty">No Program Increments yet.</td></tr>'
        }</tbody></table></div>
        ${presenting() ? "" : `<section class="card" style="margin-top:16px"><form id="add-pi" class="row"><input type="number" name="number" placeholder="PI number" value="${(pis[0]?.number || 0) + 1}" required style="max-width:120px">
          <input type="date" name="start_date" style="max-width:170px"><input type="date" name="end_date" style="max-width:170px"><button class="btn primary" type="submit">New PI</button></form></section>`}`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/pi/${tr.dataset.id}`)));
      const add = main.querySelector("#add-pi");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          const pi = await BA.api("/api/program-increments", { method: "POST", body: { number: Number(f.get("number")), start_date: f.get("start_date"), end_date: f.get("end_date") } });
          BA.go(`/pi/${pi.id}`);
        });
    },
  });

  async function renderPi(main, id, people) {
    const [d, epics, allSprints] = await Promise.all([BA.api(`/api/pis/${id}/board`), BA.api("/api/epics"), BA.api("/api/sprints")]);
    const p = d.pi;
    const ro = presenting();
    document.getElementById("view-title").textContent = `PI ${p.number}`;
    const sprintCols = [...d.sprints, { id: null, number: null }];
    const storyChip = (s) => `<div class="story-chip" title="${esc(s.acceptance || "")}"><span>${esc(s.title)}</span>${s.points != null ? `<b>${s.points}</b>` : ""}</div>`;
    const cellStories = (fid, sid) => d.stories.filter((s) => s.feature_id === fid && (s.sprint_id ?? null) === sid).map(storyChip).join("");
    const capacity = (s) => {
      if (!s.id) return '<span class="quiet">not in a sprint</span>';
      const over = s.capacity != null && s.planned_points > s.capacity;
      return `<span class="pill ${over ? "bad" : "good"}">${s.planned_points}${s.capacity != null ? ` of ${s.capacity}` : ""} pts</span>`;
    };
    const board = `<div class="tablewrap"><table class="data pi-board"><thead><tr><th>Feature</th>${sprintCols
      .map((s) => `<th>${s.id ? `Sprint ${s.number}${s.kind === "innovation and planning" ? " (IP)" : ""}` : "Unscheduled"}<div>${capacity(s)}</div></th>`).join("")}</tr></thead><tbody>
      <tr class="milestones-row"><td><b>Milestones</b></td>${sprintCols.map((s) => `<td>${s.id ? d.milestones.filter((m) => m.date && s.start_date && m.date >= s.start_date && m.date <= (s.end_date || m.date)).map((m) => `<span class="pill warn">${esc(m.title)}</span>`).join(" ") : d.milestones.filter((m) => !m.date).map((m) => `<span class="pill">${esc(m.title)}</span>`).join(" ")}</td>`).join("")}</tr>
      ${d.features.map((f) => `<tr><td><b>${esc(f.title)}</b> ${tonePill(f.priority, PRIORITY_TONES)}<div class="quiet">${[f.epic_title, `${f.points} pts`].filter(Boolean).map(esc).join(" · ")} ${BA.keysEditor(`/api/features/${f.id}`, f.ticket_key, "ticket_key")}</div></td>${sprintCols.map((s) => `<td>${cellStories(f.id, s.id)}</td>`).join("")}</tr>`).join("") ||
        `<tr><td colspan="${sprintCols.length + 1}" class="empty">No features yet.</td></tr>`}
      </tbody></table></div>`;
    main.innerHTML = `<p><a href="#/pi">All PIs</a></p>
      <section class="card"><div class="row"><h2>PI ${p.number}</h2><span class="quiet">${BA.fmtDate(p.start_date)} to ${BA.fmtDate(p.end_date)}</span><span class="spacer"></span>
        ${p.confidence != null ? `<span class="pill ${p.confidence >= 3 ? "good" : "warn"}">confidence ${p.confidence} of 5 · ${BA.fmtDate(p.confidence_date)}</span>` : ""}
        ${d.predictability != null ? `<span class="pill ${d.predictability >= 80 ? "good" : "warn"}">predictability ${d.predictability}%</span>` : ""}</div>
        ${d.sprints.length ? "" : '<p class="quiet">Assign sprints to this PI from the sprint notebook (Sprint details, Program Increment) to build the board.</p>'}
        ${ro ? "" : `<form id="vote" class="row"><input name="votes" placeholder="Confidence votes, e.g. 4, 4, 3, 5" style="max-width:300px"><button class="btn" type="submit">Record fist-of-five</button></form>`}</section>

      <section class="card"><h2>PI objectives</h2><div class="tablewrap"><table class="data"><thead><tr><th>Objective</th><th>Kind</th><th>Business value planned</th><th>Actual</th><th>Status</th></tr></thead><tbody>${
        d.objectives.map((o) => `<tr data-obj="${o.id}"><td><b>${esc(o.title)}</b></td><td>${esc(o.kind)}</td>
          <td>${ro ? (o.value_planned ?? "") : `<input type="number" min="1" max="10" name="value_planned" value="${esc(o.value_planned ?? "")}" style="max-width:80px">`}</td>
          <td>${ro ? (o.value_actual ?? "") : `<input type="number" min="0" max="10" name="value_actual" value="${esc(o.value_actual ?? "")}" style="max-width:80px">`}</td>
          <td>${ro ? esc(o.status) : `<select name="status">${opts(WORK_STATUS, o.status)}</select>`}</td></tr>`).join("") || '<tr><td colspan="5" class="empty">No objectives yet.</td></tr>'
      }</tbody></table></div>
      ${ro ? "" : `<form id="add-obj" class="row" style="margin-top:10px"><input name="title" placeholder="Objective" required style="max-width:360px"><select name="kind" style="max-width:140px"><option>committed</option><option>stretch</option></select>
        <input type="number" name="value_planned" min="1" max="10" placeholder="Value 1-10" style="max-width:120px"><button class="btn primary" type="submit">Add objective</button></form>`}</section>

      <section class="card"><h2>Program board</h2>${board}</section>

      ${ro ? "" : `<div class="cards">
        <section class="card"><h2>Add a feature</h2><form id="add-feature">
          <label>Feature<input name="title" required></label>
          <div class="grid2"><label>Epic<select name="epic_id"><option value=""></option>${epics.map((e) => `<option value="${e.id}">${esc(e.title)}</option>`).join("")}</select></label>
          <label>Priority<select name="priority">${opts(PRIORITIES, "medium")}</select></label>
          <label>Owner<select name="owner_id">${personOptions(people)}</select></label><label>Jira key<input name="ticket_key" placeholder="ABC-123"></label></div>
          <label>Acceptance criteria<textarea name="acceptance"></textarea></label>
          <div class="actions"><button class="btn primary" type="submit">Add feature</button></div></form></section>
        <section class="card"><h2>Add a story</h2><form id="add-story">
          <label>Story<input name="title" required></label>
          <div class="grid2"><label>Feature<select name="feature_id">${d.features.map((f) => `<option value="${f.id}">${esc(f.title)}</option>`).join("")}</select></label>
          <label>Sprint<select name="sprint_id"><option value="">Unscheduled</option>${d.sprints.map((s) => `<option value="${s.id}">Sprint ${s.number}</option>`).join("")}</select></label>
          <label>Points<input type="number" name="points" min="0"></label><label>Priority<select name="priority">${opts(PRIORITIES, "medium")}</select></label></div>
          <label>Acceptance criteria<textarea name="acceptance"></textarea></label>
          <div class="actions"><button class="btn primary" type="submit">Add story</button></div></form></section>
        <section class="card"><h2>Epics</h2>${epics.map((e) => `<div class="item"><b>${esc(e.title)}</b>${tonePill(e.priority, PRIORITY_TONES)}<span class="spacer"></span><span class="quiet">${esc(e.ticket_key || "")} ${esc(e.status)}</span></div>`).join("") || '<p class="quiet">No epics yet.</p>'}
          <form id="add-epic" class="row" style="margin-top:8px"><input name="title" placeholder="Epic" required style="max-width:240px"><select name="priority" style="max-width:120px">${opts(PRIORITIES, "medium")}</select><button class="btn" type="submit">Add epic</button></form></section>
      </div>`}

      <section class="card"><h2>Stories</h2><div class="tablewrap"><table class="data"><thead><tr><th>Story</th><th>Feature</th><th>Sprint</th><th>Points</th><th>Priority</th><th>Status</th></tr></thead><tbody>${
        d.stories.map((s) => `<tr data-story="${s.id}"><td>${esc(s.title)} ${BA.keysEditor(`/api/stories/${s.id}`, s.ticket_key, "ticket_key")}</td><td>${esc(d.features.find((f) => f.id === s.feature_id)?.title || "")}</td>
          <td>${ro ? (d.sprints.find((x) => x.id === s.sprint_id)?.number ?? "") : `<select name="sprint_id"><option value="">Unscheduled</option>${d.sprints.map((x) => `<option value="${x.id}"${x.id === s.sprint_id ? " selected" : ""}>Sprint ${x.number}</option>`).join("")}</select>`}</td>
          <td>${ro ? (s.points ?? "") : `<input type="number" name="points" value="${esc(s.points ?? "")}" style="max-width:80px">`}</td>
          <td>${tonePill(s.priority, PRIORITY_TONES)}</td><td>${ro ? esc(s.status) : `<select name="status">${opts(WORK_STATUS, s.status)}</select>`}</td></tr>`).join("") ||
        '<tr><td colspan="6" class="empty">No stories yet.</td></tr>'
      }</tbody></table></div></section>

      <div class="cards">
        <section class="card"><h2>Dependencies</h2>${d.dependencies.map((x) => `<div class="item" data-dep="${x.id}"><span><b>${esc(x.feature_title || "")}</b> needs ${esc(x.depends_on_title || x.team || "")}: ${esc(x.description)}${x.needed_by_number ? ` <span class="quiet">by sprint ${x.needed_by_number}</span>` : ""}</span><span class="spacer"></span>
            ${ro ? esc(x.status) : `<select name="status" style="max-width:120px">${opts(["open", "met", "at risk"], x.status)}</select>`}</div>`).join("") || '<p class="quiet">No dependencies logged.</p>'}
          ${ro ? "" : `<form id="add-dep" style="margin-top:8px"><div class="grid2">
            <label>Feature<select name="feature_id">${d.features.map((f) => `<option value="${f.id}">${esc(f.title)}</option>`).join("")}</select></label>
            <label>Depends on feature<select name="depends_on_id"><option value=""></option>${d.features.map((f) => `<option value="${f.id}">${esc(f.title)}</option>`).join("")}</select></label>
            <label>Or another team<input name="team"></label>
            <label>Needed by<select name="needed_by_id"><option value=""></option>${d.sprints.map((s) => `<option value="${s.id}">Sprint ${s.number}</option>`).join("")}</select></label></div>
            <label>What's needed<input name="description" required></label><div class="actions"><button class="btn" type="submit">Add dependency</button></div></form>`}</section>
        <section class="card"><h2>Risks (ROAM)</h2>${d.risks.map((x) => `<div class="item" data-pirisk="${x.id}"><span>${esc(x.title)}</span><span class="quiet">${esc(x.owner_name || "")}</span><span class="spacer"></span>
            ${ro ? `<span class="pill ${x.roam === "unroamed" ? "bad" : ""}">${esc(x.roam)}</span>` : `<select name="roam" style="max-width:130px">${opts(ROAM, x.roam)}</select>`}</div>`).join("") || '<p class="quiet">No risks logged.</p>'}
          ${ro ? "" : `<form id="add-pirisk" class="row" style="margin-top:8px"><input name="title" placeholder="Risk" required style="max-width:220px"><select name="owner_id" style="max-width:180px">${personOptions(people)}</select><button class="btn" type="submit">Add risk</button></form>`}</section>
        <section class="card"><h2>Milestones and events</h2>${d.milestones.map((m) => `<div class="item"><span class="pill">${esc(m.kind)}</span><span>${esc(m.title)}</span><span class="spacer"></span><span class="quiet">${BA.fmtDate(m.date)}</span></div>`).join("") || '<p class="quiet">None yet.</p>'}
          ${ro ? "" : `<form id="add-ms" class="row" style="margin-top:8px"><input name="title" placeholder="Milestone" required style="max-width:200px"><select name="kind" style="max-width:150px">${opts(MILESTONE_KINDS, "release")}</select><input type="date" name="date" style="max-width:160px"><button class="btn" type="submit">Add</button></form>`}</section>
      </div>
      ${ro ? "" : `<section class="card"><h2>Sprint capacity</h2><div class="row">${d.sprints.map((s) => `<label class="check">Sprint ${s.number} <input type="number" data-capacity="${s.id}" value="${esc(s.capacity ?? "")}" placeholder="points" style="max-width:100px"></label>`).join("") || '<span class="quiet">No sprints in this PI yet.</span>'}</div></section>`}`;
    if (ro) return;
    const num = (v) => (v === "" || v == null ? null : Number(v));
    const post = (sel, path, shape) => {
      const form = main.querySelector(sel);
      if (form) form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(path, { method: "POST", body: shape(new FormData(form)) }); BA.rerender(); });
    };
    post("#add-obj", "/api/pi-objectives", (f) => ({ pi_id: id, title: f.get("title"), kind: f.get("kind"), value_planned: num(f.get("value_planned")) }));
    post("#add-feature", "/api/features", (f) => ({ pi_id: id, title: f.get("title"), epic_id: num(f.get("epic_id")), priority: f.get("priority"), owner_id: num(f.get("owner_id")), ticket_key: f.get("ticket_key"), acceptance: f.get("acceptance"), position: d.features.length }));
    post("#add-story", "/api/stories", (f) => ({ title: f.get("title"), feature_id: num(f.get("feature_id")), sprint_id: num(f.get("sprint_id")), points: num(f.get("points")), priority: f.get("priority"), acceptance: f.get("acceptance") }));
    post("#add-epic", "/api/epics", (f) => ({ title: f.get("title"), priority: f.get("priority") }));
    post("#add-dep", "/api/dependencies", (f) => ({ pi_id: id, feature_id: num(f.get("feature_id")), depends_on_id: num(f.get("depends_on_id")), team: f.get("team"), description: f.get("description"), needed_by_id: num(f.get("needed_by_id")) }));
    post("#add-pirisk", "/api/pi-risks", (f) => ({ pi_id: id, title: f.get("title"), owner_id: num(f.get("owner_id")) }));
    post("#add-ms", "/api/pi-milestones", (f) => ({ pi_id: id, title: f.get("title"), kind: f.get("kind"), date: f.get("date") }));
    const vote = main.querySelector("#vote");
    vote.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const votes = new FormData(vote).get("votes").split(/[\s,]+/).filter(Boolean).map(Number);
      await BA.api(`/api/pis/${id}/confidence`, { method: "POST", body: { votes } });
      BA.rerender();
    });
    const patchRows = (attr, path, numeric) =>
      main.querySelectorAll(`[${attr}]`).forEach((row) => (row.onchange = BA.guard(async (e) => {
        const el = e.target;
        await BA.api(`${path}/${row.getAttribute(attr)}`, { method: "PATCH", body: { [el.name]: numeric.includes(el.name) ? num(el.value) : el.value } });
        BA.rerender();
      })));
    patchRows("data-obj", "/api/pi-objectives", ["value_planned", "value_actual"]);
    patchRows("data-story", "/api/stories", ["sprint_id", "points"]);
    patchRows("data-dep", "/api/dependencies", []);
    patchRows("data-pirisk", "/api/pi-risks", []);
    main.querySelectorAll("[data-capacity]").forEach((el) => (el.onchange = BA.guard(async () => {
      await BA.api(`/api/sprints/${el.dataset.capacity}`, { method: "PATCH", body: { capacity: num(el.value) } });
      BA.rerender();
    })));
  }

  // ---------------------------------------------------------------- 30/60/90-day and six-month plans

  const PLAN_KINDS = ["outcome", "action", "measure", "keep"];
  const PLAN_KIND_TITLES = { outcome: "Outcomes", action: "Actions", measure: "How we'll know", keep: "What I won't change" };
  const PLAN_ITEM_STATUS = ["planned", "in progress", "done", "dropped"];
  const PLAN_STATUS_TONES = { draft: "", reviewed: "warn", presented: "accent", agreed: "good" };
  const NOTE_TITLES = { change_first: "What to change first", frustrating: "What's frustrating", gaps: "Gaps", opportunities: "Opportunities", dont_change: "What not to change", if_you_were_me: "If you were me" };

  BA.view("/plans", {
    title: "30/60/90 plans",
    async render(main) {
      const [d, people, mov] = await Promise.all([BA.api("/api/plans/overview"), BA.api("/api/people"), BA.api("/api/mandates/overview")]);
      const ro = presenting();
      const ev = d.evidence;
      const outcomes = (mov.mine && mov.mine.outcomes) || [];
      const outcomeName = (id) => (outcomes.find((o) => o.id === id) || {}).text;
      const themeNames = ev.themes.map((t) => t.theme);
      const uncovered = ev.themes.filter((t) => !t.plan_items);
      const dateRange = (h) => (h.start ? `${BA.fmtDate(h.start)} to ${BA.fmtDate(h.end)}` : `Days ${h.first_day} to ${h.last_day}`);
      const itemRow = (i) => `<details class="plan-item${i.status === "dropped" ? " dropped" : ""}" data-item="${i.id}"><summary>
          <span>${esc(i.title)}</span><span class="spacer"></span>
          ${i.themes?.length ? BA.chips(i.themes) : ""}
          ${i.due ? `<span class="quiet">${BA.fmtDate(i.due)}</span>` : i.due_day ? `<span class="quiet">${BA.roleDay(i.due_day)}</span>` : ""}
          ${i.outside ? '<span class="pill warn" title="The day falls outside this plan\'s window">outside window</span>' : ""}
          ${i.early_win ? `<span class="pill accent" title="An early win: a visible improvement people will notice">early win</span>${!ro && outcomes.length && !i.serves_id ? '<span class="pill warn" title="This early win isn\'t linked to an agreed outcome">serves no outcome</span>' : ""}` : ""}${i.owner_name ? `<span class="quiet">${esc(i.owner_name)}</span>` : ""}${BA.statusPill(i.status)}</summary>
        ${i.detail ? BA.md(i.detail) : ""}
        ${ro ? "" : `<form class="edit-item"><div class="grid2">
          <label>Title<input name="title" value="${esc(i.title)}" required></label>
          <label>Kind<select name="kind">${opts(PLAN_KINDS, i.kind)}</select></label>
          <label>Day <span class="quiet">(day of the role)</span><input type="number" min="1" name="due_day" value="${esc(i.due_day ?? "")}"></label>
          <label>Status<select name="status">${opts(PLAN_ITEM_STATUS, i.status)}</select></label>
          <label>Owner<select name="owner_id">${personOptions(people, i.owner_id)}</select></label>
          <label>Themes <span class="quiet">(comma separated)</span><input name="themes" value="${esc((i.themes || []).join(", "))}" list="plan-themes"></label>
          <label class="check"><input type="checkbox" name="early_win"${i.early_win ? " checked" : ""}> An early win <span class="quiet">(a visible improvement people will notice)</span></label>
          <label>Serves which agreed outcome <span class="quiet">(early wins should do double duty)</span><select name="serves_id"><option value=""></option>${outcomes.map((o) => `<option value="${o.id}"${o.id === i.serves_id ? " selected" : ""}>${esc(o.text.slice(0, 90))}</option>`).join("")}</select></label>
          <label>Behavior it starts to change<input name="behavior" value="${esc(i.behavior || "")}" placeholder="Such as: slips raised early instead of at the deadline"></label></div>
          <label>Detail<textarea name="detail">${esc(i.detail || "")}</textarea></label>
          <label>Evidence <span class="quiet">(private: who said it, what you saw)</span><textarea name="evidence">${esc(i.evidence || "")}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" data-del="${i.id}">Delete</button><button class="btn primary" type="submit">Save</button></div></form>`}</details>`;
      const horizon = (h) => {
        const groups = PLAN_KINDS.map((k) => [k, h.items.filter((i) => i.kind === k)]).filter(([, list]) => list.length);
        return `<section class="card plan-horizon" data-plan="${h.id}">
          <div class="row"><h2>${esc(h.title)}</h2><span class="quiet">${dateRange(h)}</span><span class="spacer"></span>
            ${tonePill(h.status, PLAN_STATUS_TONES)}${h.agreed_on ? `<span class="quiet">agreed ${BA.fmtDate(h.agreed_on)}</span>` : h.presented_on ? `<span class="quiet">${BA.fmtDate(h.presented_on)}${h.audience ? ` · ${esc(h.audience)}` : ""}</span>` : ""}
            ${ro || h.status === "agreed" ? "" : `<button class="btn" type="button" data-agree-plan="${h.id}" title="Your manager has agreed this plan">Mark agreed</button>`}</div>
          ${ro ? "" : `<details class="plan-settings"><summary class="quiet">Rename, change the last day, or delete</summary><form class="edit-plan row">
            <input name="title" value="${esc(h.title)}" required style="max-width:240px"><label class="check">Ends on day <input type="number" name="horizon_days" min="1" value="${h.horizon_days}" required style="max-width:90px"></label>
            <button class="btn" type="submit">Save</button><span class="spacer"></span><button class="btn danger" type="button" data-del-plan="${h.id}">Delete plan</button></form></details>`}
          ${ro ? (h.summary ? `<p>${esc(h.summary)}</p>` : "") : `<label>The headline for this stretch<textarea name="summary" class="plan-summary" placeholder="What will be true by day ${h.last_day}?">${esc(h.summary || "")}</textarea></label>`}
          ${groups.map(([k, list]) => `<h3>${PLAN_KIND_TITLES[k]}</h3>${list.map(itemRow).join("")}`).join("") || '<p class="quiet">Nothing here yet.</p>'}
          ${ro ? "" : `<form class="plan-add row"><select name="kind" style="max-width:150px">${PLAN_KINDS.map((k) => `<option value="${k}">${k === "keep" ? "won't change" : k}</option>`).join("")}</select>
            <input name="title" placeholder="Add to this plan" required style="max-width:340px"><input type="number" name="due_day" min="${h.first_day}" max="${h.last_day}" placeholder="Day" style="max-width:90px">
            <input name="themes" placeholder="Themes" list="plan-themes" style="max-width:180px"><button class="btn" type="submit">Add</button></form>`}</section>`;
      };
      main.innerHTML = `
        <datalist id="plan-themes">${themeNames.map((n) => `<option value="${esc(n)}">`).join("")}</datalist>
        <section class="card"><div class="row"><h2>Plans for the first six months</h2><span class="spacer"></span>
          ${ro ? "" : `<button class="btn" id="copy-outline">Copy outline as Markdown</button>`}</div>
          <p class="quiet">${d.start_date ? `Starting ${BA.fmtDate(d.start_date)}.` : 'Set the contract start date in <a href="#/me">My development</a> to turn days into dates.'}
            Built from the listening tour: ${ev.done} conversation${ev.done === 1 ? "" : "s"} done${ev.planned ? `, ${ev.planned} still planned` : ""}. The Comms studio can turn the outline into a deck.</p>
          ${ro ? "" : `<form id="presented" class="row"><input type="date" name="presented_on" value="${BA.today()}" style="max-width:170px"><input name="audience" placeholder="Who you presented to" style="max-width:260px">
            <button class="btn" type="submit">Mark all presented</button></form>`}</section>
        <div class="plan-layout"><div class="plan-horizons">${d.horizons.map(horizon).join("")}
          ${ro ? "" : `<section class="card"><h2>Add a plan</h2><p class="quiet">For a finer step (a two-week check-in) or a longer view (month 9, month 12). Each plan runs from the day after the one before it.</p>
            <form id="add-plan" class="row"><input name="title" placeholder="Name, such as Month 9" required style="max-width:260px"><label class="check">Ends on day <input type="number" name="horizon_days" min="1" required style="max-width:90px"></label><button class="btn primary" type="submit">Add plan</button></form></section>`}</div>
          <aside><section class="card"><h2>What I heard</h2>${
            ev.themes.length
              ? `<p class="quiet">Themes from the listening tour, with how many plan items answer each.</p>${ev.themes
                  .map((t) => `<div class="item"><span>${esc(t.theme)}</span><span class="quiet">${t.count} of ${ev.done}</span><span class="spacer"></span>${t.plan_items ? `<span class="pill good">${t.plan_items} in plan</span>` : '<span class="pill warn">not in plan yet</span>'}</div>`)
                  .join("")}${uncovered.length && !ro ? `<p class="quiet">${uncovered.length} theme${uncovered.length === 1 ? "" : "s"} not answered yet. Address each one, or say why it waits.</p>` : ""}`
              : '<p class="quiet">No themes yet. Tag themes on finished one-on-ones in the Listening tour.</p>'
          }</section>
          ${ev.notes ? `<section class="card"><h2>Notes to draw on</h2><p class="quiet">Private. From finished one-on-ones.</p>${Object.entries(NOTE_TITLES)
            .filter(([k]) => ev.notes[k]?.length)
            .map(([k, title]) => `<details><summary>${title} (${ev.notes[k].length})</summary>${ev.notes[k].map((n) => `<p><b>${esc(n.person || "")}</b> ${esc(n.text)}</p>`).join("")}</details>`)
            .join("") || '<p class="quiet">Nothing yet.</p>'}</section>` : ""}</aside></div>`;
      if (ro) return;
      const num = (v) => (v === "" || v == null ? null : Number(v));
      const themes = (v) => (v || "").split(",").map((s) => s.trim()).filter(Boolean);
      main.querySelectorAll(".plan-horizon").forEach((sec) => {
        const planId = Number(sec.dataset.plan);
        sec.querySelector(".plan-summary").onchange = BA.guard(async (e) => {
          await BA.api(`/api/plans/${planId}`, { method: "PATCH", body: { summary: e.target.value } });
          BA.toast("Saved.");
        });
        const edit = sec.querySelector("form.edit-plan");
        edit.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(edit);
          await BA.api(`/api/plans/${planId}`, { method: "PATCH", body: { title: f.get("title"), horizon_days: Number(f.get("horizon_days")) } });
          BA.rerender();
        });
        sec.querySelector("[data-del-plan]").onclick = BA.guard(async () => {
          const n = d.horizons.find((h) => h.id === planId).items.length;
          if (!confirm(n ? `Delete this plan and its ${n} item${n === 1 ? "" : "s"}?` : "Delete this plan?")) return;
          await BA.api(`/api/plans/${planId}`, { method: "DELETE" });
          BA.rerender();
        });
        const add = sec.querySelector("form.plan-add");
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          await BA.api("/api/plan-items", { method: "POST", body: { plan_id: planId, kind: f.get("kind"), title: f.get("title"), due_day: num(f.get("due_day")), themes: themes(f.get("themes")) } });
          BA.rerender();
        });
      });
      main.querySelectorAll("details[data-item]").forEach((det) => {
        const id = det.dataset.item;
        const form = det.querySelector("form.edit-item");
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          await BA.api(`/api/plan-items/${id}`, { method: "PATCH", body: {
            title: f.get("title"), kind: f.get("kind"), due_day: num(f.get("due_day")), status: f.get("status"),
            owner_id: num(f.get("owner_id")), themes: themes(f.get("themes")), detail: f.get("detail"), evidence: f.get("evidence"), early_win: !!det.querySelector("[name=early_win]")?.checked, serves_id: num(f.get("serves_id")), behavior: f.get("behavior") || null,
          } });
          BA.rerender();
        });
        det.querySelector("[data-del]").onclick = BA.guard(async () => {
          if (!confirm("Delete this plan item?")) return;
          await BA.api(`/api/plan-items/${id}`, { method: "DELETE" });
          BA.rerender();
        });
      });
      const addPlan = main.querySelector("#add-plan");
      addPlan.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(addPlan);
        await BA.api("/api/plans", { method: "POST", body: { title: f.get("title"), horizon_days: Number(f.get("horizon_days")) } });
        BA.rerender();
      });
      main.querySelector("#copy-outline").onclick = BA.guard(async () => {
        const out = await BA.api("/api/plans/export", { method: "POST", body: {} });
        await navigator.clipboard.writeText(out.markdown);
        BA.toast("Outline copied. Only shareable fields are included.");
      });
      main.querySelectorAll("[data-agree-plan]").forEach((b) => (b.onclick = BA.guard(async () => { await BA.api(`/api/plans/${b.dataset.agreePlan}/agree`, { method: "POST", body: {} }); BA.toast("Marked agreed with your manager."); BA.rerender(); })));
      const presented = main.querySelector("#presented");
      presented.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(presented);
        for (const h of d.horizons) await BA.api(`/api/plans/${h.id}/presented`, { method: "POST", body: { presented_on: f.get("presented_on"), audience: f.get("audience") } });
        BA.rerender();
      });
    },
  });

  // ---------------------------------------------------------------- Business landscape

  const OFFERING_KINDS = ["product", "service", "internal platform"];
  const MATURITY = ["idea", "emerging", "growing", "mature", "declining", "sunsetting"];
  const OFFERING_STATUS = ["active", "planned", "retired"];
  const DEPT_KINDS = ["division", "department", "team"];
  const QUADRANTS = ["strength", "weakness", "opportunity", "threat"];
  const Q_TITLES = { strength: "Strengths", weakness: "Weaknesses", opportunity: "Opportunities", threat: "Threats" };
  const Q_TONES = { strength: "good", weakness: "bad", opportunity: "accent", threat: "warn" };
  const SOURCES = ["listening tour", "metrics", "incident", "vendor", "customer feedback", "document", "my observation"];
  const MATURITY_TONES = { emerging: "accent", growing: "good", mature: "good", declining: "warn", sunsetting: "bad" };

  const swotBadges = (s) => (s ? QUADRANTS.filter((q) => s[q]).map((q) => `<span class="pill ${Q_TONES[q]}" title="${Q_TITLES[q]}">${q[0].toUpperCase()} ${s[q]}</span>`).join(" ") : "");
  const landscapeTabs = (active) => `<nav class="tabs">${[["", "Products and services"], ["org", "Organization"], ["swot", "Assessment"]]
    .map(([k, label]) => `<a href="#/landscape${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const deptOptions = (depts, sel, skip) => `<option value=""></option>${depts.filter((d) => d.id !== skip).map((d) => `<option value="${d.id}"${d.id === sel ? " selected" : ""}>${esc(d.name)}</option>`).join("")}`;

  BA.view("/landscape", {
    title: "Business landscape",
    async render(main, param) {
      if (param && /^[od]-\d+$/.test(param)) return renderSubject(main, param[0] === "o" ? "offering" : "department", Number(param.slice(2)));
      if (param === "org") return renderOrg(main);
      if (param === "swot") return renderSwot(main);
      const [offers, depts] = await Promise.all([BA.api("/api/landscape/offerings"), BA.api("/api/departments")]);
      const ro = presenting();
      main.innerHTML = `${landscapeTabs("")}
        <p class="quiet">What the company offers today, who owns it and what it runs on. Open one to assess it.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Name</th><th>Kind</th><th>Owner</th><th>Maturity</th><th>Runs on</th><th>Assessment</th></tr></thead><tbody>${
          offers.map((o) => `<tr class="clickable${o.status === "retired" ? " muted" : ""}" data-id="${o.id}"><td><b>${esc(o.name)}</b>${o.status !== "active" ? ` <span class="pill">${esc(o.status)}</span>` : ""}<div class="quiet">${esc(o.customers || "")}</div></td>
            <td>${esc(o.kind)}</td><td>${esc(o.department_name || "")}</td><td>${o.maturity ? tonePill(o.maturity, MATURITY_TONES) : ""}</td>
            <td>${BA.chips(o.systems.map((s) => s.name))}</td><td>${swotBadges(o.swot)}</td></tr>`).join("") ||
          '<tr><td colspan="6" class="empty">No products or services yet.</td></tr>'
        }</tbody></table></div>
        ${ro ? "" : `<section class="card" style="margin-top:16px"><h2>Add a product or service</h2><form id="add-offer" class="row">
          <input name="name" placeholder="Name" required style="max-width:260px"><select name="kind" style="max-width:170px">${opts(OFFERING_KINDS, "product")}</select>
          <select name="department_id" style="max-width:220px" title="Owning department">${deptOptions(depts).replace('<option value=""></option>', '<option value="">Owning department</option>')}</select>
          <select name="maturity" style="max-width:150px"><option value="">Maturity</option>${opts(MATURITY)}</select><button class="btn primary" type="submit">Add</button></form></section>`}`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/landscape/o-${tr.dataset.id}`)));
      const add = main.querySelector("#add-offer");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(add);
          const o = await BA.api("/api/offerings", { method: "POST", body: { name: f.get("name"), kind: f.get("kind"), department_id: f.get("department_id") ? Number(f.get("department_id")) : null, maturity: f.get("maturity") || null } });
          BA.go(`/landscape/o-${o.id}`);
        });
    },
  });

  async function renderOrg(main) {
    const [d, depts, people] = await Promise.all([BA.api("/api/landscape/org"), BA.api("/api/departments"), BA.api("/api/people")]);
    const ro = presenting();
    const node = (n) => `<li><div class="org-node"><a href="#/landscape/d-${n.id}"><b>${esc(n.name)}</b></a><span class="pill">${esc(n.kind)}</span>
        ${n.leader_name ? `<span class="quiet">led by ${esc(n.leader_name)}</span>` : ""}<span class="spacer"></span>
        ${n.people.length ? `<span class="org-people">${n.people.map((x) => `<a href="#/people/${x.id}" title="${esc(x.role || "")}">${esc(x.name)}</a>`).join(", ")}</span>` : ""}
        ${n.offerings.length ? BA.chips(n.offerings.map((o) => o.name)) : ""}${swotBadges(n.swot)}</div>
        ${n.children.length ? `<ul>${n.children.map(node).join("")}</ul>` : ""}</li>`;
    main.innerHTML = `${landscapeTabs("org")}
      <section class="card"><h2>Organization by department</h2>${d.tree.length ? `<ul class="org-tree">${d.tree.map(node).join("")}</ul>` : '<p class="quiet">No departments yet. Add the top level first, then the departments and teams inside it.</p>'}</section>
      ${ro ? "" : `<section class="card"><h2>Add a division, department or team</h2><form id="add-dept" class="row">
        <input name="name" placeholder="Name" required style="max-width:240px"><select name="kind" style="max-width:150px">${opts(DEPT_KINDS, "department")}</select>
        <select name="parent_id" style="max-width:220px">${deptOptions(depts).replace('<option value=""></option>', '<option value="">Top level</option>')}</select>
        <select name="leader_id" style="max-width:200px">${personOptions(people).replace('<option value=""></option>', '<option value="">Leader</option>')}</select><button class="btn primary" type="submit">Add</button></form></section>
      ${d.unassigned.length && depts.length ? `<section class="card"><h2>People not placed yet</h2>${d.unassigned.map((p) => `<div class="item"><span>${esc(p.name)}</span><span class="quiet">${esc(p.role || "")}</span><span class="spacer"></span><select data-place="${p.id}" style="max-width:220px">${deptOptions(depts)}</select></div>`).join("")}</section>` : ""}`}`;
    if (ro) return;
    const add = main.querySelector("#add-dept");
    add.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(add);
      const num = (v) => (v ? Number(v) : null);
      await BA.api("/api/departments", { method: "POST", body: { name: f.get("name"), kind: f.get("kind"), parent_id: num(f.get("parent_id")), leader_id: num(f.get("leader_id")) } });
      BA.rerender();
    });
    main.querySelectorAll("[data-place]").forEach((sel) => (sel.onchange = BA.guard(async () => {
      await BA.api(`/api/people/${sel.dataset.place}`, { method: "PATCH", body: { department_id: sel.value ? Number(sel.value) : null } });
      BA.rerender();
    })));
  }

  async function renderSwot(main) {
    const d = await BA.api("/api/landscape/swot");
    if (d.private) {
      main.innerHTML = `${landscapeTabs("swot")}<p class="empty">The assessment is private, so it's hidden while presenting.</p>`;
      return;
    }
    const filter = sessionStorage.getItem("ba-swot-filter") || "all";
    const shown = (a) => filter === "all" || a.subject_type === filter;
    main.innerHTML = `${landscapeTabs("swot")}
      <div class="row"><p class="quiet">Every open point across products, services and departments. Private: it never leaves this app.</p><span class="spacer"></span>
        <select id="swot-filter" style="max-width:200px">${[["all", "Everything"], ["offering", "Products and services"], ["department", "Departments"]].map(([v, l]) => `<option value="${v}"${v === filter ? " selected" : ""}>${l}</option>`).join("")}</select></div>
      <div class="swot-grid">${QUADRANTS.map((q) => {
        const list = d.quadrants[q].filter(shown);
        return `<section class="card swot-${q}"><h2>${Q_TITLES[q]} <span class="quiet">${list.length}</span></h2>${list
          .map((a) => `<div class="item"><span><a href="#/landscape/${a.subject_type === "offering" ? "o" : "d"}-${a.subject_id}">${esc(a.subject_name || "")}</a>: ${esc(a.title)}</span><span class="spacer"></span><span class="quiet">${esc(a.confidence)} confidence</span></div>`)
          .join("") || '<p class="quiet">Nothing yet.</p>'}</section>`;
      }).join("")}</div>`;
    main.querySelector("#swot-filter").onchange = (e) => {
      sessionStorage.setItem("ba-swot-filter", e.target.value);
      BA.rerender();
    };
  }

  async function renderSubject(main, kind, id) {
    const [d, depts, people, systems, vendors] = await Promise.all([
      BA.api(`/api/landscape/${kind}/${id}`), BA.api("/api/departments"), BA.api("/api/people"), BA.api("/api/systems"), BA.api("/api/vendors"),
    ]);
    const s = d.subject;
    const ro = presenting();
    const isOffer = kind === "offering";
    document.getElementById("view-title").textContent = s.name;
    const crumbs = [`<a href="#/landscape${isOffer ? "" : "/org"}">${isOffer ? "Products and services" : "Organization"}</a>`, ...d.path.map((p) => `<a href="#/landscape/d-${p.id}">${esc(p.name)}</a>`)].join(" / ");
    const checks = (list, chosen, name) => list.map((x) => `<label class="check"><input type="checkbox" name="${name}" value="${x.id}"${chosen.includes(x.id) ? " checked" : ""}> ${esc(x.name)}</label>`).join("") || '<span class="quiet">None recorded yet.</span>';
    const facts = isOffer
      ? `${s.description ? BA.md(s.description) : '<p class="quiet">No description yet.</p>'}
        <div class="row">${[s.kind, s.status].map((x) => `<span class="pill">${esc(x)}</span>`).join(" ")}${s.maturity ? tonePill(s.maturity, MATURITY_TONES) : ""}
          ${s.department_name ? `<span class="quiet">Owned by ${esc(s.department_name)}</span>` : ""}</div>
        ${s.customers ? `<p class="quiet">Serves: ${esc(s.customers)}</p>` : ""}
        <p>Runs on: ${BA.chips(d.systems.map((x) => x.name)) || '<span class="quiet">no systems linked</span>'} · Vendors: ${BA.chips(d.vendors.map((x) => x.name)) || '<span class="quiet">none linked</span>'}</p>`
      : `${s.purpose ? BA.md(s.purpose) : '<p class="quiet">No purpose written yet.</p>'}
        <div class="row"><span class="pill">${esc(s.kind)}</span>${s.leader_name ? `<span class="quiet">Led by ${esc(s.leader_name)}</span>` : ""}</div>
        ${d.children.length ? `<p>Inside it: ${d.children.map((c) => `<a href="#/landscape/d-${c.id}">${esc(c.name)}</a>`).join(", ")}</p>` : ""}
        ${d.people.length ? `<p>People: ${esc(d.people.map((p) => p.name).join(", "))}</p>` : ""}
        ${d.offerings.length ? `<p>Owns: ${d.offerings.map((o) => `<a href="#/landscape/o-${o.id}">${esc(o.name)}</a>`).join(", ")}</p>` : ""}`;
    const aItem = (a) => `<details class="plan-item" data-a="${a.id}"><summary><span>${esc(a.title)}</span><span class="spacer"></span>
        ${a.source ? `<span class="quiet">${esc(a.source)}</span>` : ""}<span class="pill">${esc(a.confidence)}</span>${a.status !== "open" ? `<span class="pill good">${esc(a.status)}</span>` : ""}</summary>
        ${a.evidence ? BA.md(a.evidence) : '<p class="quiet">No evidence written down yet.</p>'}
        <div class="row">${a.date ? `<span class="quiet">${BA.fmtDate(a.date)}</span>` : ""}<span class="spacer"></span>
          ${a.roadmap_item_id ? '<a href="#/roadmap">On the roadmap</a>' : `<button class="btn" data-roadmap="${a.id}">Add to roadmap</button>`}
          ${a.risk_id ? '<a href="#/risks">Logged as a risk</a>' : `<button class="btn" data-risk="${a.id}">Log as a risk</button>`}
          <select data-status="${a.id}" style="max-width:130px">${opts(["open", "acted on", "closed"], a.status)}</select>
          <button class="icon-btn" title="Delete" data-del-a="${a.id}">${BA.icon("x")}</button></div></details>`;
    main.innerHTML = `<p>${crumbs}</p>
      <section class="card"><h2>${esc(s.name)}</h2>${facts}</section>
      ${d.assessments ? `<div class="swot-grid">${QUADRANTS.map((q) => `<section class="card swot-${q}"><h2>${Q_TITLES[q]}</h2>${d.assessments[q].map(aItem).join("") || '<p class="quiet">Nothing yet.</p>'}</section>`).join("")}</div>
        <section class="card"><h2>Add to the assessment</h2><form id="add-a">
          <div class="row"><select name="quadrant" style="max-width:160px">${opts(QUADRANTS, "weakness")}</select><input name="title" placeholder="The point, in a sentence" required style="max-width:420px"></div>
          <label>Evidence <span class="quiet">(what you saw or heard, and from whom)</span><textarea name="evidence"></textarea></label>
          <div class="row"><select name="source" style="max-width:190px"><option value="">Source</option>${opts(SOURCES)}</select>
            <select name="confidence" style="max-width:170px">${opts(["low", "medium", "high"], "medium")}</select><input type="date" name="date" value="${BA.today()}" style="max-width:170px">
            <button class="btn primary" type="submit">Add</button></div></form></section>` : ""}
      ${ro ? "" : `<form id="edit-subject" class="card"><h2>Details</h2><div class="grid2">
        <label>Name<input name="name" value="${esc(s.name)}" required></label>
        <label>Kind<select name="kind">${opts(isOffer ? OFFERING_KINDS : DEPT_KINDS, s.kind)}</select></label>
        ${isOffer ? `<label>Owning department<select name="department_id">${deptOptions(depts, s.department_id)}</select></label>
          <label>Maturity<select name="maturity"><option value=""></option>${opts(MATURITY, s.maturity)}</select></label>
          <label>Status<select name="status">${opts(OFFERING_STATUS, s.status)}</select></label>
          <label>Who it serves<input name="customers" value="${esc(s.customers || "")}"></label>`
        : `<label>Inside<select name="parent_id">${deptOptions(depts, s.parent_id, s.id)}</select></label>
          <label>Leader<select name="leader_id">${personOptions(people, s.leader_id)}</select></label>`}</div>
        <label>${isOffer ? "What it is" : "Purpose"}<textarea name="${isOffer ? "description" : "purpose"}">${esc((isOffer ? s.description : s.purpose) || "")}</textarea></label>
        ${isOffer ? `<label>Systems it runs on</label><div class="row">${checks(systems, s.system_ids, "system_ids")}</div>
          <label>Vendors involved</label><div class="row">${checks(vendors, s.vendor_ids, "vendor_ids")}</div>` : ""}
        <label>Private notes<textarea name="notes">${esc(s.notes || "")}</textarea></label>
        <div class="actions"><button class="btn danger left" type="button" id="del-subject">Delete</button>${BA.historyButton(kind, id)}<button class="btn primary" type="submit">Save</button></div></form>`}`;
    if (ro) return;
    const num = (v) => (v ? Number(v) : null);
    const edit = main.querySelector("#edit-subject");
    edit.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(edit);
      const body = { name: f.get("name"), kind: f.get("kind"), notes: f.get("notes") };
      if (isOffer) Object.assign(body, { department_id: num(f.get("department_id")), maturity: f.get("maturity") || null, status: f.get("status"), customers: f.get("customers"), description: f.get("description"),
        system_ids: f.getAll("system_ids").map(Number), vendor_ids: f.getAll("vendor_ids").map(Number) });
      else Object.assign(body, { parent_id: num(f.get("parent_id")), leader_id: num(f.get("leader_id")), purpose: f.get("purpose") });
      await BA.api(`/api/${isOffer ? "offerings" : "departments"}/${id}`, { method: "PATCH", body });
      BA.rerender();
    });
    main.querySelector("#del-subject").onclick = BA.guard(async () => {
      if (!confirm(isOffer ? "Delete this and its assessment?" : "Delete this? Teams inside it move up a level, and its assessment is deleted.")) return;
      await BA.api(`/api/${isOffer ? "offerings" : "departments"}/${id}`, { method: "DELETE" });
      BA.go(isOffer ? "/landscape" : "/landscape/org");
    });
    const addA = main.querySelector("#add-a");
    if (!addA) return;
    addA.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(addA);
      await BA.api("/api/assessments", { method: "POST", body: { subject_type: kind, subject_id: id, quadrant: f.get("quadrant"), title: f.get("title"), evidence: f.get("evidence"), source: f.get("source") || null, confidence: f.get("confidence"), date: f.get("date") || null } });
      BA.rerender();
    });
    const act = (attr, fn) => main.querySelectorAll(`[${attr}]`).forEach((el) => (el.onclick = BA.guard(async (e) => { e.preventDefault(); await fn(el.getAttribute(attr), el); BA.rerender(); })));
    act("data-roadmap", (aid) => BA.api(`/api/assessments/${aid}/to-roadmap`, { method: "POST", body: {} }).then(() => BA.toast("Added to the roadmap. Only the title went across.")));
    act("data-risk", (aid) => BA.api(`/api/assessments/${aid}/to-risk`, { method: "POST", body: {} }));
    act("data-del-a", (aid) => (confirm("Delete this point?") ? BA.api(`/api/assessments/${aid}`, { method: "DELETE" }) : null));
    main.querySelectorAll("[data-status]").forEach((sel) => (sel.onchange = BA.guard(async () => {
      await BA.api(`/api/assessments/${sel.dataset.status}`, { method: "PATCH", body: { status: sel.value } });
      BA.rerender();
    })));
  }

  // ---------------------------------------------------------------- QA resources

  const TEST_KINDS = ["smoke", "regression", "smoke and regression"];
  const RUN_KINDS = ["smoke", "regression", "release check", "exploratory"];
  const RESULTS = ["pass", "fail", "blocked", "skipped"];
  const RESULT_TONES = { pass: "good", fail: "bad", blocked: "warn", skipped: "", "not run": "" };
  const SUITE_KINDS = ["unit", "integration", "end-to-end", "Apex", "MUnit", "performance", "other"];
  const SUITE_RESULTS = ["unknown", "passing", "failing", "flaky"];
  const SUITE_TONES = { passing: "good", failing: "bad", flaky: "warn", unknown: "" };
  const REG_KINDS = ["Salesforce release", "peak-season freeze", "major release", "other"];
  const REG_STATUS = ["planned", "in progress", "signed off", "done"];
  const qaTabs = (active) => `<nav class="tabs">${[["", "Overview"], ["library", "Test library"], ["runs", "Runs"], ["suites", "Automated tests"], ["regression", "Regression plans"], ["dod", "Definition of done"]]
    .map(([k, label]) => `<a href="#/qa${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const tally = (r) => `<span class="tally">${r.passed ? `<span class="pill good">${r.passed} pass</span>` : ""}${r.failed ? `<span class="pill bad">${r.failed} fail</span>` : ""}${r.blocked ? `<span class="pill warn">${r.blocked} blocked</span>` : ""}${r.not_run ? `<span class="pill">${r.not_run} not run</span>` : ""}</span>`;
  const sysOptions = (systems, sel, blank = "") => `<option value="">${blank}</option>${systems.map((s) => `<option value="${s.id}"${s.id === sel ? " selected" : ""}>${esc(s.name)}</option>`).join("")}`;
  const numOrNull = (v) => (v === "" || v == null ? null : Number(v));

  BA.view("/qa", {
    title: "QA resources",
    async render(main, param) {
      if (param && param.startsWith("run-")) return renderRun(main, Number(param.slice(4)));
      const views = { library: renderLibrary, runs: renderRuns, suites: renderSuites, regression: renderRegression, dod: renderDod };
      if (views[param]) return views[param](main);
      const o = await BA.api("/api/qa/overview");
      const stat = (n, label, tone = "") => `<section class="card stat"><div class="stat-n ${tone}">${n ?? "–"}</div><div class="quiet">${label}</div></section>`;
      main.innerHTML = `${qaTabs("")}
        <div class="stats">${stat(o.cases.active, `manual test cases (${o.cases.smoke} smoke, ${o.cases.regression} regression)`)}${stat(o.cases.never_run, "never run", o.cases.never_run ? "warn" : "")}
          ${stat(o.cases.failing.length, "failing or blocked last time", o.cases.failing.length ? "bad" : "good")}${stat(o.suites.average_coverage != null ? o.suites.average_coverage + "%" : null, `average coverage across ${o.suites.count} automated suites`)}
          ${o.open_follow_ups != null ? stat(o.open_follow_ups, "open test follow-ups in the dev-sync log", o.open_follow_ups ? "warn" : "") : ""}</div>
        <div class="cards">
          <section class="card"><h2>Needs attention</h2>${[
            ...o.cases.failing.map((c) => `<div class="item"><span class="pill bad">case</span><span>${esc(c.title)}</span><span class="spacer"></span><span class="quiet">${esc(c.system_name || "")}</span></div>`),
            ...o.suites.failing.map((s) => `<div class="item">${tonePill(s.last_result, SUITE_TONES)}<span>${esc(s.name)}</span></div>`),
          ].join("") || '<p class="quiet">Nothing failing.</p>'}</section>
          <section class="card"><h2>Coming up</h2>${o.plans.map((p) => `<div class="item"><a href="#/qa/regression">${esc(p.title)}</a><span class="quiet">${esc(p.kind)}</span><span class="spacer"></span><span class="quiet">${p.start_date ? BA.fmtDate(p.start_date) : ""}${p.owner_name ? " · " + esc(p.owner_name) : ""}</span></div>`).join("") || '<p class="quiet">No regression plans ahead.</p>'}</section>
          <section class="card"><h2>Recent runs</h2>${o.recent_runs.map((r) => `<div class="item"><a href="#/qa/run-${r.id}">${esc(r.name)}</a><span class="spacer"></span>${tally(r)}</div>`).join("") || '<p class="quiet">No runs yet.</p>'}</section>
          <section class="card"><h2>Definition of done</h2>${o.definition_of_done.length ? `<ul class="checklist">${o.definition_of_done.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : '<p class="quiet">Not agreed yet. <a href="#/qa/dod">Write it with the team</a>.</p>'}
            ${o.raci.length ? `<p class="quiet">Who decides, from the <a href="#/raci">RACI</a>: ${o.raci.map((r) => `${esc(r.decision)} (${Object.entries(r.cells).filter(([, l]) => l === "A").map(([role]) => esc(role)).join(", ") || "no one accountable yet"})`).join("; ")}</p>` : ""}</section>
        </div>`;
    },
  });

  async function renderLibrary(main) {
    const [cases, systems, people] = await Promise.all([BA.api("/api/test-cases"), BA.api("/api/systems"), BA.api("/api/people")]);
    const ro = presenting();
    const filter = (() => { try { return JSON.parse(sessionStorage.getItem("ba-qa-filter") || "{}"); } catch { return {}; } })();
    const shown = cases.filter((c) => (!filter.system || String(c.system_id) === filter.system) && (!filter.kind || c.kind === filter.kind) && (filter.retired || c.active));
    const groups = {};
    shown.forEach((c) => (groups[c.system_name || "No system"] ??= []).push(c));
    const caseRow = (c) => `<details class="plan-item${c.active ? "" : " dropped"}" data-case="${c.id}"><summary><span>${esc(c.title)}</span><span class="spacer"></span>
        ${BA.issueKeys(c.jira_keys)}${c.area ? `<span class="quiet">${esc(c.area)}</span>` : ""}<span class="pill">${esc(c.kind)}</span>${tonePill(c.priority, PRIORITY_TONES)}
        ${c.last_result ? `${tonePill(c.last_result, RESULT_TONES)}<span class="quiet">${BA.fmtDate(c.last_run)}</span>` : '<span class="quiet">never run</span>'}</summary>
        ${c.preconditions ? `<h4>Before you start</h4>${BA.md(c.preconditions)}` : ""}${c.steps ? `<h4>Steps</h4>${BA.md(c.steps)}` : ""}${c.expected ? `<h4>Expected result</h4>${BA.md(c.expected)}` : ""}
        ${ro ? "" : `<form class="edit-case"><div class="grid2">
          <label>Title<input name="title" value="${esc(c.title)}" required></label><label>System<select name="system_id">${sysOptions(systems, c.system_id)}</select></label>
          <label>Area<input name="area" value="${esc(c.area || "")}"></label><label>Kind<select name="kind">${opts(TEST_KINDS, c.kind)}</select></label>
          <label>Priority<select name="priority">${opts(PRIORITIES, c.priority)}</select></label><label>Owner<select name="owner_id">${personOptions(people, c.owner_id)}</select></label>
          <label>Jira keys <span class="quiet">(the test, or stories it covers)</span><input name="jira_keys" value="${esc((c.jira_keys || []).join(", "))}" placeholder="ABC-123"></label></div>
          <label>Before you start <span class="quiet">(data, accounts, environment)</span><textarea name="preconditions">${esc(c.preconditions || "")}</textarea></label>
          <label>Steps <span class="quiet">(a numbered list works best)</span><textarea name="steps" rows="5">${esc(c.steps || "")}</textarea></label>
          <label>Expected result<textarea name="expected">${esc(c.expected || "")}</textarea></label>
          <label class="check"><input type="checkbox" name="active"${c.active ? " checked" : ""}> In use</label>
          <div class="actions"><button class="btn danger left" type="button" data-del-case="${c.id}">Delete</button>${BA.historyButton("test_case", c.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`;
    main.innerHTML = `${qaTabs("library")}
      <div class="row"><p class="quiet">Manual tests anyone on the team can follow. Smoke tests are the quick checks after every deploy; regression tests go into release plans.</p><span class="spacer"></span>
        <select id="f-system" style="max-width:200px">${sysOptions(systems, numOrNull(filter.system), "All systems")}</select>
        <select id="f-kind" style="max-width:200px"><option value="">All kinds</option>${opts(TEST_KINDS, filter.kind)}</select>
        <label class="check"><input type="checkbox" id="f-retired"${filter.retired ? " checked" : ""}> Show retired</label></div>
      ${Object.entries(groups).map(([name, list]) => `<section class="card"><h2>${esc(name)} <span class="quiet">${list.length}</span></h2>${list.map(caseRow).join("")}</section>`).join("") || '<p class="empty">No test cases yet.</p>'}
      ${ro ? "" : `<section class="card"><h2>Add a test case</h2><form id="add-case" class="row">
        <input name="title" placeholder="What it checks" required style="max-width:320px"><select name="system_id" style="max-width:200px">${sysOptions(systems, null, "System")}</select>
        <input name="area" placeholder="Area" style="max-width:160px"><select name="kind" style="max-width:190px">${opts(TEST_KINDS, "smoke")}</select>
        <button class="btn primary" type="submit">Add</button></form><p class="quiet">Systems come from the <a href="#/escalation">escalation playbook</a>. Open a case after adding it to write the steps.</p></section>`}`;
    const saveFilter = () => {
      sessionStorage.setItem("ba-qa-filter", JSON.stringify({ system: main.querySelector("#f-system").value, kind: main.querySelector("#f-kind").value, retired: main.querySelector("#f-retired").checked }));
      BA.rerender();
    };
    ["#f-system", "#f-kind", "#f-retired"].forEach((s) => (main.querySelector(s).onchange = saveFilter));
    if (ro) return;
    const add = main.querySelector("#add-case");
    add.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(add);
      await BA.api("/api/test-cases", { method: "POST", body: { title: f.get("title"), system_id: numOrNull(f.get("system_id")), area: f.get("area"), kind: f.get("kind") } });
      BA.rerender();
    });
    main.querySelectorAll("details[data-case]").forEach((det) => {
      const id = det.dataset.case;
      const form = det.querySelector("form.edit-case");
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        await BA.api(`/api/test-cases/${id}`, { method: "PATCH", body: { title: f.get("title"), system_id: numOrNull(f.get("system_id")), area: f.get("area"), kind: f.get("kind"), priority: f.get("priority"),
          owner_id: numOrNull(f.get("owner_id")), preconditions: f.get("preconditions"), steps: f.get("steps"), expected: f.get("expected"), active: form.elements.active.checked, jira_keys: f.get("jira_keys") } });
        BA.rerender();
      });
      det.querySelector("[data-del-case]").onclick = BA.guard(async () => {
        if (!confirm("Delete this test case and its past results? Unticking 'In use' keeps the history.")) return;
        await BA.api(`/api/test-cases/${id}`, { method: "DELETE" });
        BA.rerender();
      });
    });
  }

  async function renderRuns(main) {
    const [runs, systems, sprints, plans, people, current] = await Promise.all([
      BA.api("/api/test-runs"), BA.api("/api/systems"), BA.api("/api/sprints"), BA.api("/api/regression-plans"), BA.api("/api/people"), BA.api("/api/sprints/current"),
    ]);
    keepTeam(runs);
    keepTeam(sprints);
    const ro = presenting();
    main.innerHTML = `${qaTabs("runs")}
      ${ro ? "" : `<section class="card"><h2>Start a run</h2><form id="start-run"><div class="grid2">
        <label>Name<input name="name" required placeholder="Such as: smoke after the [release name] deploy"></label>
        <label>What to test<select name="select"><option value="smoke">Every smoke test</option><option value="regression">Every regression test</option><option value="all">Every active test</option></select></label>
        <label>Only this system<select name="system_id">${sysOptions(systems, null, "All systems")}</select></label>
        <label>Or a regression plan's cases<select name="plan_id"><option value=""></option>${plans.map((p) => `<option value="${p.id}">${esc(p.title)}</option>`).join("")}</select></label>
        <label>Sprint<select name="sprint_id"><option value=""></option>${sprints.map((s) => `<option value="${s.id}"${current && s.id === current.id ? " selected" : ""}>Sprint ${s.number}</option>`).join("")}</select></label>
        <label>Tester<select name="tester_id">${personOptions(people)}</select></label>
        <label>Environment<input name="environment" placeholder="Such as: production, full sandbox"></label><label>Release<input name="release"></label></div>
        <div class="actions"><button class="btn primary" type="submit">${BA.icon("play")} Start run</button></div></form></section>`}
      <div class="tablewrap"><table class="data"><thead><tr><th>Run</th><th>Date</th><th>Kind</th><th>For</th><th>Results</th><th>Status</th></tr></thead><tbody>${
        runs.map((r) => `<tr class="clickable" data-id="${r.id}"><td><b>${esc(r.name)}</b>${r.environment ? `<div class="quiet">${esc(r.environment)}</div>` : ""}</td><td>${BA.fmtDate(r.date)}</td><td>${esc(r.kind)}</td>
          <td>${[r.sprint_number ? `Sprint ${r.sprint_number}` : "", r.plan_title ? esc(r.plan_title) : "", r.release ? esc(r.release) : ""].filter(Boolean).join(" · ")}</td><td>${tally(r)}</td><td>${BA.statusPill(r.status)}</td></tr>`).join("") ||
        '<tr><td colspan="6" class="empty">No runs yet.</td></tr>'
      }</tbody></table></div>`;
    main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/qa/run-${tr.dataset.id}`)));
    const form = main.querySelector("#start-run");
    if (form)
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        const body = { name: f.get("name"), select: f.get("select"), system_id: numOrNull(f.get("system_id")), plan_id: numOrNull(f.get("plan_id")), sprint_id: numOrNull(f.get("sprint_id")),
          tester_id: numOrNull(f.get("tester_id")), environment: f.get("environment"), release: f.get("release"), kind: f.get("select") === "regression" ? "regression" : "smoke", team_id: newTeamId() };
        const run = await BA.api("/api/test-runs", { method: "POST", body });
        BA.go(`/qa/run-${run.id}`);
      });
  }

  async function renderRun(main, id) {
    const d = await BA.api(`/api/test-runs/${id}/board`);
    const r = d.run;
    const ro = presenting();
    document.getElementById("view-title").textContent = r.name;
    const row = (x) => `<div class="run-row result-${x.result.replace(" ", "-")}" data-result="${x.id}">
        <details><summary><b>${esc(x.case.title)}</b> <span class="quiet">${esc([x.case.system_name, x.case.area].filter(Boolean).join(" · "))}</span></summary>
          ${x.case.preconditions ? `<h4>Before you start</h4>${BA.md(x.case.preconditions)}` : ""}${x.case.steps ? `<h4>Steps</h4>${BA.md(x.case.steps)}` : '<p class="quiet">No steps written yet.</p>'}${x.case.expected ? `<h4>Expected result</h4>${BA.md(x.case.expected)}` : ""}</details>
        <div class="row">${ro ? tonePill(x.result, RESULT_TONES) : `<div class="seg">${RESULTS.map((v) => `<button type="button" class="${x.result === v ? "on " + (RESULT_TONES[v] || "") : ""}" data-set="${v}">${v}</button>`).join("")}</div>
          <input name="notes" placeholder="What happened" value="${esc(x.notes || "")}" style="max-width:340px">
          ${BA.keysEditor(`/api/test-results/${x.id}`, x.jira_keys)}
          ${x.action_item_id ? '<a href="#/dev-sync">In the dev-sync log</a>' : (x.result === "fail" || x.result === "blocked") ? '<button class="btn" type="button" data-follow>Send to dev-sync</button>' : ""}`}</div></div>`;
    main.innerHTML = `<p><a href="#/qa/runs">All runs</a></p>
      <section class="card"><div class="row"><h2>${esc(r.name)}</h2><span class="quiet">${BA.fmtDate(r.date)} · ${esc(r.kind)}${r.environment ? " · " + esc(r.environment) : ""}${r.tester_name ? " · " + esc(r.tester_name) : ""}</span><span class="spacer"></span>${tally(r)}</div>
        ${ro ? "" : `<div class="row"><select id="run-status" style="max-width:150px">${opts(["planned", "in progress", "done"], r.status)}</select><button class="btn" id="copy-summary">${BA.icon("copy")} Copy summary</button>
          <span class="spacer"></span><button class="btn danger" id="del-run">Delete run</button></div>`}</section>
      <section class="card">${d.results.map(row).join("")}</section>`;
    if (ro) return;
    main.querySelectorAll("[data-result]").forEach((el) => {
      const rid = el.dataset.result;
      el.querySelectorAll("[data-set]").forEach((b) => (b.onclick = BA.guard(async () => {
        await BA.api(`/api/test-results/${rid}`, { method: "PATCH", body: { result: b.dataset.set } });
        BA.rerender();
      })));
      el.querySelector('input[name="notes"]').onchange = BA.guard(async (e) => {
        await BA.api(`/api/test-results/${rid}`, { method: "PATCH", body: { notes: e.target.value } });
        BA.toast("Saved.");
      });
      const follow = el.querySelector("[data-follow]");
      if (follow) follow.onclick = BA.guard(async () => {
        await BA.api(`/api/test-results/${rid}/follow-up`, { method: "POST", body: {} });
        BA.toast("Added to the dev-sync log.");
        BA.rerender();
      });
    });
    main.querySelector("#run-status").onchange = BA.guard(async (e) => {
      await BA.api(`/api/test-runs/${id}`, { method: "PATCH", body: { status: e.target.value } });
      BA.toast("Saved.");
    });
    main.querySelector("#copy-summary").onclick = BA.guard(async () => {
      const s = await BA.api(`/api/test-runs/${id}/summary`);
      await navigator.clipboard.writeText(s.markdown);
      BA.toast("Summary copied.");
    });
    main.querySelector("#del-run").onclick = BA.guard(async () => {
      if (!confirm("Delete this run and its results?")) return;
      await BA.api(`/api/test-runs/${id}`, { method: "DELETE" });
      BA.go("/qa/runs");
    });
  }

  async function renderSuites(main) {
    const [suites, systems, people] = await Promise.all([BA.api("/api/test-suites"), BA.api("/api/systems"), BA.api("/api/people")]);
    const ro = presenting();
    const link = (v) => (v && /^https?:\/\//.test(v) ? `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(v.replace(/^https?:\/\//, "").slice(0, 40))}</a>` : esc(v || ""));
    const suiteRow = (s) => `<details class="plan-item" data-suite="${s.id}"><summary><b>${esc(s.name)}</b><span class="pill">${esc(s.kind)}</span><span class="quiet">${esc(s.system_name || "")}</span><span class="spacer"></span>
        ${s.test_count != null ? `<span class="quiet">${s.test_count} tests</span>` : ""}${s.coverage != null ? `<span class="quiet">${s.coverage}% coverage</span>` : ""}${tonePill(s.last_result, SUITE_TONES)}${s.last_run ? `<span class="quiet">${BA.fmtDate(s.last_run)}</span>` : ""}</summary>
        <p>${[s.framework ? esc(s.framework) : "", s.location ? `Lives in ${link(s.location)}` : "", s.ci_link ? `CI: ${link(s.ci_link)}` : "", s.owner_name ? `Owner: ${esc(s.owner_name)}` : ""].filter(Boolean).join(" · ") || '<span class="quiet">No details yet.</span>'}</p>
        ${ro ? "" : `<form class="edit-suite"><div class="grid2">
          <label>Name<input name="name" value="${esc(s.name)}" required></label><label>Kind<select name="kind">${opts(SUITE_KINDS, s.kind)}</select></label>
          <label>System<select name="system_id">${sysOptions(systems, s.system_id)}</select></label><label>Framework<input name="framework" value="${esc(s.framework || "")}"></label>
          <label>Where it lives <span class="quiet">(repo path or link)</span><input name="location" value="${esc(s.location || "")}"></label><label>CI link<input name="ci_link" value="${esc(s.ci_link || "")}"></label>
          <label>Owner<select name="owner_id">${personOptions(people, s.owner_id)}</select></label><label>Number of tests<input type="number" name="test_count" value="${esc(s.test_count ?? "")}"></label>
          <label>Coverage %<input type="number" step="0.1" name="coverage" value="${esc(s.coverage ?? "")}"></label><label>Latest result<select name="last_result">${opts(SUITE_RESULTS, s.last_result)}</select></label>
          <label>Last run<input type="date" name="last_run" value="${esc(s.last_run || "")}"></label></div>
          <label>Private notes<textarea name="notes">${esc(s.notes || "")}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" data-del-suite="${s.id}">Delete</button><button class="btn primary" type="submit">Save</button></div></form>`}</details>`;
    main.innerHTML = `${qaTabs("suites")}
      <p class="quiet">Every automated suite: unit and integration tests, Apex tests, MuleSoft MUnit tests and end-to-end checks, where each lives, and how it did last time.</p>
      <section class="card">${suites.map(suiteRow).join("") || '<p class="quiet">No suites recorded yet.</p>'}</section>
      ${ro ? "" : `<section class="card"><h2>Add a suite</h2><form id="add-suite" class="row"><input name="name" placeholder="Suite name" required style="max-width:280px">
        <select name="kind" style="max-width:150px">${opts(SUITE_KINDS, "unit")}</select><select name="system_id" style="max-width:200px">${sysOptions(systems, null, "System")}</select>
        <input name="location" placeholder="Repo path or link" style="max-width:240px"><button class="btn primary" type="submit">Add</button></form></section>`}`;
    if (ro) return;
    main.querySelector("#add-suite").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      await BA.api("/api/test-suites", { method: "POST", body: { name: f.get("name"), kind: f.get("kind"), system_id: numOrNull(f.get("system_id")), location: f.get("location") } });
      BA.rerender();
    });
    main.querySelectorAll("details[data-suite]").forEach((det) => {
      const id = det.dataset.suite;
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        await BA.api(`/api/test-suites/${id}`, { method: "PATCH", body: { name: f.get("name"), kind: f.get("kind"), system_id: numOrNull(f.get("system_id")), framework: f.get("framework"), location: f.get("location"),
          ci_link: f.get("ci_link"), owner_id: numOrNull(f.get("owner_id")), test_count: numOrNull(f.get("test_count")), coverage: numOrNull(f.get("coverage")), last_result: f.get("last_result"),
          last_run: f.get("last_run") || null, notes: f.get("notes") } });
        BA.rerender();
      });
      det.querySelector("[data-del-suite]").onclick = BA.guard(async () => {
        if (!confirm("Delete this suite?")) return;
        await BA.api(`/api/test-suites/${id}`, { method: "DELETE" });
        BA.rerender();
      });
    });
  }

  async function renderRegression(main) {
    const [plans, cases, people] = await Promise.all([BA.api("/api/regression-plans"), BA.api("/api/test-cases"), BA.api("/api/people")]);
    const ro = presenting();
    const pool = cases.filter((c) => c.active && c.kind !== "smoke");
    const planCard = (p) => `<section class="card" data-plan="${p.id}"><div class="row"><h2>${esc(p.title)}</h2><span class="pill">${esc(p.kind)}</span><span class="spacer"></span>${BA.statusPill(p.status)}</div>
        <p class="quiet">${p.start_date ? `${BA.fmtDate(p.start_date)}${p.end_date ? " to " + BA.fmtDate(p.end_date) : ""} · ` : ""}Owner: ${esc(p.owner_name || "not named")} · Backup: ${esc(p.backup_owner_name || "not named")}
          ${p.signoff_date ? ` · Signed off ${BA.fmtDate(p.signoff_date)}${p.signoff_by_name ? " by " + esc(p.signoff_by_name) : ""}` : ""}</p>
        ${p.scope ? BA.md(p.scope) : ""}
        <p>${p.case_ids.length ? `${p.case_ids.length} regression case${p.case_ids.length === 1 ? "" : "s"} picked.` : "No cases picked, so a run uses every active regression test."}</p>
        ${ro ? "" : `<div class="row"><button class="btn primary" type="button" data-run>${BA.icon("play")} Start a run from this plan</button></div>
        <details><summary>Edit the plan and pick cases</summary><form class="edit-reg"><div class="grid2">
          <label>Title<input name="title" value="${esc(p.title)}" required></label><label>Kind<select name="kind">${opts(REG_KINDS, p.kind)}</select></label>
          <label>Starts<input type="date" name="start_date" value="${esc(p.start_date || "")}"></label><label>Ends<input type="date" name="end_date" value="${esc(p.end_date || "")}"></label>
          <label>Owner<select name="owner_id">${personOptions(people, p.owner_id)}</select></label><label>Backup<select name="backup_owner_id">${personOptions(people, p.backup_owner_id)}</select></label>
          <label>Status<select name="status">${opts(REG_STATUS, p.status)}</select></label><label>Signed off by<select name="signoff_by_id">${personOptions(people, p.signoff_by_id)}</select></label>
          <label>Sign-off date<input type="date" name="signoff_date" value="${esc(p.signoff_date || "")}"></label></div>
          <label>Scope <span class="quiet">(what changes, what's at risk, what's out)</span><textarea name="scope">${esc(p.scope || "")}</textarea></label>
          <label>Cases</label><div class="case-picks">${pool.map((c) => `<label class="check"><input type="checkbox" name="case_ids" value="${c.id}"${p.case_ids.includes(c.id) ? " checked" : ""}> ${esc(c.title)} <span class="quiet">${esc(c.system_name || "")}</span></label>`).join("") || '<span class="quiet">No regression cases in the library yet.</span>'}</div>
          <label>Private notes<textarea name="notes">${esc(p.notes || "")}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" data-del-reg>Delete</button><button class="btn primary" type="submit">Save</button></div></form></details>`}</section>`;
    main.innerHTML = `${qaTabs("regression")}
      <p class="quiet">A plan for each Salesforce release and each peak-season freeze: what to test, who owns it, who backs them up, and who signs off.</p>
      ${plans.map(planCard).join("") || '<p class="empty">No regression plans yet.</p>'}
      ${ro ? "" : `<section class="card"><h2>New regression plan</h2><form id="add-reg" class="row"><input name="title" placeholder="Such as: [Salesforce release name] regression" required style="max-width:320px">
        <select name="kind" style="max-width:190px">${opts(REG_KINDS, "Salesforce release")}</select><input type="date" name="start_date" style="max-width:170px">
        <select name="owner_id" style="max-width:200px">${personOptions(people).replace('<option value=""></option>', '<option value="">Owner</option>')}</select><button class="btn primary" type="submit">Add</button></form></section>`}`;
    if (ro) return;
    main.querySelector("#add-reg").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      await BA.api("/api/regression-plans", { method: "POST", body: { title: f.get("title"), kind: f.get("kind"), start_date: f.get("start_date") || null, owner_id: numOrNull(f.get("owner_id")) } });
      BA.rerender();
    });
    main.querySelectorAll("[data-plan]").forEach((sec) => {
      const id = Number(sec.dataset.plan);
      const plan = plans.find((p) => p.id === id);
      sec.querySelector("[data-run]").onclick = BA.guard(async () => {
        const run = await BA.api("/api/test-runs", { method: "POST", body: { name: plan.title, plan_id: id, kind: "regression" } });
        BA.go(`/qa/run-${run.id}`);
      });
      const form = sec.querySelector("form.edit-reg");
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        await BA.api(`/api/regression-plans/${id}`, { method: "PATCH", body: { title: f.get("title"), kind: f.get("kind"), start_date: f.get("start_date") || null, end_date: f.get("end_date") || null,
          owner_id: numOrNull(f.get("owner_id")), backup_owner_id: numOrNull(f.get("backup_owner_id")), status: f.get("status"), signoff_by_id: numOrNull(f.get("signoff_by_id")),
          signoff_date: f.get("signoff_date") || null, scope: f.get("scope"), case_ids: f.getAll("case_ids").map(Number), notes: f.get("notes") } });
        BA.rerender();
      });
      sec.querySelector("[data-del-reg]").onclick = BA.guard(async () => {
        if (!confirm("Delete this regression plan? Its runs stay.")) return;
        await BA.api(`/api/regression-plans/${id}`, { method: "DELETE" });
        BA.rerender();
      });
    });
  }

  async function renderDod(main) {
    const [dod, o] = await Promise.all([BA.api("/api/qa/definition-of-done"), BA.api("/api/qa/overview")]);
    const ro = presenting();
    main.innerHTML = `${qaTabs("dod")}
      <section class="card"><h2>Definition of done</h2><p class="quiet">What has to be true before the team calls a story done. Agree it together and revisit it at retros.</p>
        ${dod.items.length ? `<ul class="checklist">${dod.items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : '<p class="quiet">Nothing agreed yet.</p>'}
        ${ro ? "" : `<form id="dod"><label>One item per line<textarea name="items" rows="8">${esc(dod.items.join("\n"))}</textarea></label>
          <div class="actions">${dod.items.length ? "" : '<button class="btn left" type="button" id="dod-starter">Load a starter list</button>'}<button class="btn primary" type="submit">Save</button></div></form>`}</section>
      <section class="card"><h2>Who decides</h2>${o.raci.length ? o.raci.map((r) => `<div class="item"><b>${esc(r.decision)}</b><span class="spacer"></span>${Object.entries(r.cells).map(([role, l]) => `<span class="pill${l === "A" ? " good" : ""}">${esc(role)}: ${l}</span>`).join(" ") || '<span class="quiet">no one assigned yet</span>'}</div>`).join("")
        : '<p class="quiet">No QA or release decisions in the RACI yet. The starter content there includes QA sign-off and release go/no-go.</p>'}<p><a href="#/raci">Open the RACI</a></p></section>`;
    if (ro) return;
    main.querySelector("#dod").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api("/api/qa/definition-of-done", { method: "PUT", body: { items: new FormData(e.target).get("items").split("\n") } });
      BA.toast("Saved.");
      BA.rerender();
    });
    const starter = main.querySelector("#dod-starter");
    if (starter) starter.onclick = BA.guard(async () => (await BA.api("/api/qa/definition-of-done/starter", { method: "POST", body: {} }), BA.rerender()));
  }

  // ---------------------------------------------------------------- Architecture and tools

  const SYSTEM_KINDS = ["platform", "application", "integration", "data store", "external service", "tool"];
  const KIND_TITLES = { platform: "Platforms", application: "Applications", integration: "Integration layer", "data store": "Data stores", "external service": "External services", tool: "Tools" };
  const LIFECYCLE = ["planned", "active", "retiring", "retired"];
  const CRIT = ["high", "medium", "low"];
  const CRIT_TONES = { high: "bad", medium: "warn", low: "" };
  const PATTERNS = ["API", "event", "batch", "file transfer", "database link", "manual"];
  const INT_STATUS = ["planned", "live", "retiring", "retired"];
  const ADR_STATUS = ["proposed", "accepted", "superseded", "rejected"];
  const ADR_TONES = { proposed: "warn", accepted: "good", superseded: "", rejected: "" };
  const LANES = [["external service"], ["platform", "application"], ["integration"], ["data store"], ["tool"]];
  const LANE_TITLES = ["External services", "Applications and platforms", "Integration layer", "Data stores", "Tools"];
  const archTabs = (active) => `<nav class="tabs">${[["", "System map"], ["systems", "Systems and tools"], ["integrations", "Integrations"], ["decisions", "Decisions"], ["guides", "Guides"]]
    .map(([k, label]) => `<a href="#/architecture${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const adrLabel = (n) => `ADR-${String(n).padStart(3, "0")}`;
  const linkOut = (v) => (v && /^https?:\/\//.test(v) ? `<a href="${esc(v)}" target="_blank" rel="noopener">${esc(v.replace(/^https?:\/\//, "").slice(0, 48))} ${BA.icon("external-link")}</a>` : esc(v || ""));
  const flow = (i) => `${esc(i.from_name)} ${i.direction === "two way" ? "⇄" : "→"} ${i.via_name ? `${esc(i.via_name)} ${i.direction === "two way" ? "⇄" : "→"} ` : ""}${esc(i.to_name)}`;

  // Lanes left to right, one box per system, a curve per hop. Built as SVG text, so it needs no drawing library.
  function systemMapSvg(map) {
    const W = 200, H = 46, GAPX = 90, GAPY = 22, TOP = 44, PAD = 16;
    const lanes = LANES.map((kinds, i) => ({ title: LANE_TITLES[i], nodes: map.nodes.filter((n) => kinds.includes(n.kind)) })).filter((l) => l.nodes.length);
    const pos = {};
    lanes.forEach((lane, li) => lane.nodes.forEach((n, ni) => (pos[n.id] = { x: PAD + li * (W + GAPX), y: TOP + ni * (H + GAPY), n })));
    const width = PAD * 2 + lanes.length * W + (lanes.length - 1) * GAPX;
    const height = TOP + Math.max(...lanes.map((l) => l.nodes.length)) * (H + GAPY) + PAD;
    const hop = (a, b, e, two) => {
      const A = pos[a], B = pos[b];
      if (!A || !B) return "";
      let d;
      if (A.x === B.x) {
        const x = A.x + W, y1 = A.y + H / 2, y2 = B.y + H / 2;
        d = `M${x},${y1} C${x + 60},${y1} ${x + 60},${y2} ${x},${y2}`;
      } else {
        const right = B.x > A.x;
        const x1 = right ? A.x + W : A.x, x2 = right ? B.x : B.x + W, y1 = A.y + H / 2, y2 = B.y + H / 2, mid = (x1 + x2) / 2;
        d = `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`;
      }
      return `<path d="${d}" class="edge${e.status === "planned" ? " planned" : ""}${e.criticality === "high" ? " critical" : ""}" data-ends="${a},${b}${e.via_id ? "," + e.via_id : ""}" marker-end="url(#arrow)"${two ? ' marker-start="url(#arrow-back)"' : ""}>
        <title>${esc(e.name)} · ${esc(e.pattern)}${e.data ? " · " + esc(e.data) : ""}</title></path>`;
    };
    const edges = map.edges.map((e) => {
      const two = e.direction === "two way";
      return e.via_id && pos[e.via_id] ? hop(e.from_id, e.via_id, e, two) + hop(e.via_id, e.to_id, e, two) : hop(e.from_id, e.to_id, e, two);
    }).join("");
    const label = (s) => (s.length > 26 ? s.slice(0, 25) + "…" : s);
    const nodes = Object.values(pos).map(({ x, y, n }) => `<g class="node${n.criticality === "high" ? " critical" : ""}${n.lifecycle !== "active" ? " faded" : ""}" data-node="${n.id}" transform="translate(${x},${y})">
        <rect width="${W}" height="${H}" rx="8"></rect><text x="12" y="20" class="node-name">${esc(label(n.name))}</text>
        <text x="12" y="36" class="node-sub">${esc(n.category || n.kind)}${n.lifecycle !== "active" ? " · " + esc(n.lifecycle) : ""}</text><title>${esc(n.name)}</title></g>`).join("");
    const heads = lanes.map((l, i) => `<text x="${PAD + i * (W + GAPX)}" y="24" class="lane-title">${esc(l.title.toUpperCase())}</text>`).join("");
    return `<svg class="system-map" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="System map">
      <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z"></path></marker>
      <marker id="arrow-back" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M10,0 L0,5 L10,10 z"></path></marker></defs>
      ${heads}${edges}${nodes}</svg>`;
  }

  BA.view("/architecture", {
    title: "Architecture and tools",
    async render(main, param) {
      if (param && /^s-\d+$/.test(param)) return renderSystem(main, Number(param.slice(2)));
      if (param && /^g-\d+$/.test(param)) return renderGuide(main, Number(param.slice(2)));
      const views = { systems: renderSystems, integrations: renderIntegrations, decisions: renderDecisions, guides: renderGuides };
      if (views[param]) return views[param](main);
      const [map, sum] = await Promise.all([BA.api("/api/architecture/map"), BA.api("/api/architecture/summary")]);
      main.innerHTML = `${archTabs("")}
        <div class="row">${Object.entries(sum.by_kind).filter(([, n]) => n).map(([k, n]) => `<span class="pill">${n} ${esc(k)}${n === 1 ? "" : "s"}</span>`).join(" ")}
          <span class="pill">${sum.integrations} integration${sum.integrations === 1 ? "" : "s"}</span><span class="spacer"></span>
          <span class="quiet">Hover a system to trace its connections; click to open it.</span></div>
        <section class="card map-card">${map.nodes.length ? `<div class="map-scroll">${systemMapSvg(map)}</div>
          <p class="quiet legend"><span class="key solid"></span> live <span class="key dashed"></span> planned <span class="key red"></span> high criticality · Tools show only when something connects to them.</p>`
          : '<p class="quiet">No systems yet. Add them under Systems and tools, then connect them under Integrations.</p>'}</section>
        <div class="cards">
          <section class="card"><h2>Documentation gaps</h2>${sum.documentation_gaps.map((g) => `<div class="item"><a href="#/architecture/s-${g.id}">${esc(g.name)}</a>${g.criticality ? tonePill(g.criticality, CRIT_TONES) : ""}<span class="spacer"></span><span class="quiet">no ${g.missing.join(", no ")}</span></div>`).join("") || '<p class="quiet">Every system has an owner, a description and a docs link.</p>'}</section>
          <section class="card"><h2>Integrations with no owner</h2>${sum.unowned_integrations.map((i) => `<div class="item"><a href="#/architecture/integrations">${esc(i.name)}</a></div>`).join("") || '<p class="quiet">None.</p>'}
            ${Object.keys(sum.by_pattern).length ? `<p class="quiet">By pattern: ${Object.entries(sum.by_pattern).map(([p, n]) => `${esc(p)} ${n}`).join(" · ")}</p>` : ""}</section>
          <section class="card"><h2>Decisions</h2><p>${ADR_STATUS.map((s) => `${tonePill(s, ADR_TONES)} ${sum.decisions[s]}`).join(" ")}</p><p><a href="#/architecture/decisions">Open the decision log</a></p></section>
        </div>`;
      const svg = main.querySelector(".system-map");
      if (!svg) return;
      svg.querySelectorAll("[data-node]").forEach((g) => {
        const id = g.dataset.node;
        g.onmouseenter = () => {
          svg.classList.add("tracing");
          svg.querySelectorAll(".edge").forEach((p) => p.classList.toggle("lit", p.dataset.ends.split(",").includes(id)));
          g.classList.add("lit");
        };
        g.onmouseleave = () => {
          svg.classList.remove("tracing");
          svg.querySelectorAll(".lit").forEach((x) => x.classList.remove("lit"));
        };
        g.onclick = () => BA.go(`/architecture/s-${id}`);
      });
    },
  });

  async function renderSystems(main) {
    const systems = await BA.api("/api/systems");
    const ro = presenting();
    const filter = sessionStorage.getItem("ba-arch-kind") || "";
    const shown = systems.filter((s) => (!filter || (filter === "systems" ? s.kind !== "tool" : s.kind === filter)) && s.lifecycle !== "retired");
    const groups = SYSTEM_KINDS.map((k) => [k, shown.filter((s) => s.kind === k)]).filter(([, l]) => l.length);
    const retired = systems.filter((s) => s.lifecycle === "retired");
    main.innerHTML = `${archTabs("systems")}
      <div class="row"><p class="quiet">One list for the systems we run and the tools we build with. The escalation playbook, QA and the business landscape use the same list.</p><span class="spacer"></span>
        <select id="kind-filter" style="max-width:200px"><option value="">Everything</option><option value="systems"${filter === "systems" ? " selected" : ""}>Systems only</option>${SYSTEM_KINDS.map((k) => `<option value="${k}"${k === filter ? " selected" : ""}>${KIND_TITLES[k]}</option>`).join("")}</select></div>
      ${groups.map(([k, list]) => `<section class="card"><h2>${KIND_TITLES[k]} <span class="quiet">${list.length}</span></h2><div class="sys-grid">${list.map((s) => `<a class="sys-card" href="#/architecture/s-${s.id}">
          <div class="row"><b>${esc(s.name)}</b><span class="spacer"></span>${s.criticality ? tonePill(s.criticality, CRIT_TONES) : ""}${s.lifecycle !== "active" ? `<span class="pill warn">${esc(s.lifecycle)}</span>` : ""}</div>
          <div class="quiet">${esc(s.category || "")}${s.owner_name ? `${s.category ? " · " : ""}${esc(s.owner_name)}` : ""}</div>
          ${s.description ? `<p class="clamp">${esc(s.description)}</p>` : ""}${s.tech?.length ? `<div>${BA.chips(s.tech)}</div>` : ""}</a>`).join("")}</div></section>`).join("") || '<p class="empty">Nothing here yet.</p>'}
      ${retired.length ? `<p class="quiet">Retired: ${retired.map((s) => `<a href="#/architecture/s-${s.id}">${esc(s.name)}</a>`).join(", ")}</p>` : ""}
      ${ro ? "" : `<section class="card"><h2>Add a system or tool</h2><form id="add-sys" class="row"><input name="name" placeholder="Name" required style="max-width:260px">
        <select name="kind" style="max-width:180px">${opts(SYSTEM_KINDS, "application")}</select><input name="category" placeholder="Category, such as CRM or source control" style="max-width:280px">
        <button class="btn primary" type="submit">Add</button></form></section>`}`;
    main.querySelector("#kind-filter").onchange = (e) => {
      sessionStorage.setItem("ba-arch-kind", e.target.value);
      BA.rerender();
    };
    const add = main.querySelector("#add-sys");
    if (add)
      add.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(add);
        const s = await BA.api("/api/systems", { method: "POST", body: { name: f.get("name"), kind: f.get("kind"), category: f.get("category") } });
        BA.go(`/architecture/s-${s.id}`);
      });
  }

  async function renderSystem(main, id) {
    const [d, people, vendors] = await Promise.all([BA.api(`/api/architecture/system/${id}`), BA.api("/api/people"), BA.api("/api/vendors")]);
    const s = d.system;
    const ro = presenting();
    document.getElementById("view-title").textContent = s.name;
    const intList = (list, empty) => list.map((i) => `<div class="item"><span>${flow(i)}</span><span class="spacer"></span><span class="pill">${esc(i.pattern)}</span>${i.data ? `<span class="quiet">${esc(i.data)}</span>` : ""}${i.status !== "live" ? `<span class="pill warn">${esc(i.status)}</span>` : ""}</div>`).join("") || `<p class="quiet">${empty}</p>`;
    main.innerHTML = `<p><a href="#/architecture/systems">Systems and tools</a></p>
      <section class="card"><div class="row"><h2>${esc(s.name)}</h2><span class="pill">${esc(s.kind)}</span>${s.category ? `<span class="quiet">${esc(s.category)}</span>` : ""}<span class="spacer"></span>
          ${s.criticality ? tonePill(s.criticality, CRIT_TONES) : ""}<span class="pill${s.lifecycle === "active" ? " good" : " warn"}">${esc(s.lifecycle)}</span></div>
        ${s.description ? BA.md(s.description) : '<p class="quiet">No description yet. What is it, in a sentence or two?</p>'}
        ${s.how_we_use ? `<h3>How we use it</h3>${BA.md(s.how_we_use)}` : ""}
        <div class="facts">
          ${s.owner_name ? `<div><span class="quiet">Owner</span> ${esc(s.owner_name)}</div>` : ""}${s.admin_name ? `<div><span class="quiet">Admin</span> ${esc(s.admin_name)}</div>` : ""}
          ${s.vendor_name ? `<div><span class="quiet">Vendor</span> ${esc(s.vendor_name)}</div>` : ""}${s.environments?.length ? `<div><span class="quiet">Environments</span> ${BA.chips(s.environments)}</div>` : ""}
          ${s.tech?.length ? `<div><span class="quiet">Built with</span> ${BA.chips(s.tech)}</div>` : ""}${s.docs_link ? `<div><span class="quiet">Docs</span> ${linkOut(s.docs_link)}</div>` : ""}
        </div>
        ${s.known_issues ? `<h3>Known issues <span class="quiet">(private)</span></h3>${BA.md(s.known_issues)}` : ""}
        <p class="quiet"><a href="#/escalation">Escalation playbook</a>${d.offerings.length ? ` · Supports: ${d.offerings.map((o) => `<a href="#/landscape/o-${o.id}">${esc(o.name)}</a>`).join(", ")}` : ""}</p></section>
      <div class="cards">
        <section class="card"><h2>Sends to</h2>${intList(d.outbound, "Nothing recorded.")}</section>
        <section class="card"><h2>Receives from</h2>${intList(d.inbound, "Nothing recorded.")}</section>
        ${d.carries.length ? `<section class="card"><h2>Carries</h2>${intList(d.carries, "")}</section>` : ""}
        <section class="card"><h2>Testing</h2><p>${d.testing.manual_cases} manual test case${d.testing.manual_cases === 1 ? "" : "s"} in use. <a href="#/qa/library">Test library</a></p>
          ${d.testing.suites.map((x) => `<div class="item"><span>${esc(x.name)}</span><span class="pill">${esc(x.kind)}</span><span class="spacer"></span>${x.coverage != null ? `<span class="quiet">${x.coverage}%</span>` : ""}${tonePill(x.last_result, SUITE_TONES)}</div>`).join("")}</section>
        ${d.debt && d.debt.length ? `<section class="card"><h2>Technical debt</h2>${d.debt.map((x) => `<div class="item"><a href="#/debt">${esc(x.title)}</a><span class="spacer"></span>${BA.chips(x.categories)}${BA.statusPill(x.status)}</div>`).join("")}</section>` : ""}
        <section class="card"><h2>Decisions and guides</h2>${[...d.decisions.map((x) => `<div class="item"><a href="#/architecture/decisions">${adrLabel(x.number)} ${esc(x.title)}</a><span class="spacer"></span>${tonePill(x.status, ADR_TONES)}</div>`),
          ...d.guides.map((g) => `<div class="item"><a href="#/architecture/g-${g.id}">${esc(g.title)}</a><span class="spacer"></span><span class="quiet">guide</span></div>`)].join("") || '<p class="quiet">None linked yet.</p>'}</section>
      </div>
      ${ro ? "" : `<form id="edit-sys" class="card"><h2>Details</h2><div class="grid2">
        <label>Name<input name="name" value="${esc(s.name)}" required></label><label>Kind<select name="kind">${opts(SYSTEM_KINDS, s.kind)}</select></label>
        <label>Category<input name="category" value="${esc(s.category || "")}" placeholder="Such as CRM, integration platform, source control"></label>
        <label>Lifecycle<select name="lifecycle">${opts(LIFECYCLE, s.lifecycle)}</select></label>
        <label>Criticality<select name="criticality"><option value=""></option>${opts(CRIT, s.criticality)}</select></label>
        <label>Vendor<select name="vendor_id"><option value=""></option>${vendors.map((v) => `<option value="${v.id}"${v.id === s.vendor_id ? " selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label>
        <label>Owner<select name="owner_id">${personOptions(people, s.owner_id)}</select></label><label>Admin<select name="admin_id">${personOptions(people, s.admin_id)}</select></label>
        <label>Environments <span class="quiet">(comma separated)</span><input name="environments" value="${esc((s.environments || []).join(", "))}"></label>
        <label>Built with <span class="quiet">(comma separated)</span><input name="tech" value="${esc((s.tech || []).join(", "))}"></label>
        <label>Docs link<input name="docs_link" value="${esc(s.docs_link || "")}"></label></div>
        <label>What it is<textarea name="description">${esc(s.description || "")}</textarea></label>
        <label>How we use it<textarea name="how_we_use">${esc(s.how_we_use || "")}</textarea></label>
        <label>Known issues <span class="quiet">(private: weaknesses, tech debt, workarounds)</span><textarea name="known_issues">${esc(s.known_issues || "")}</textarea></label>
        <div class="actions"><button class="btn danger left" type="button" id="del-sys">Delete</button>${BA.historyButton("system", id)}<button class="btn primary" type="submit">Save</button></div></form>`}`;
    if (ro) return;
    const form = main.querySelector("#edit-sys");
    const list = (v) => (v || "").split(",").map((x) => x.trim()).filter(Boolean);
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      await BA.api(`/api/systems/${id}`, { method: "PATCH", body: { name: f.get("name"), kind: f.get("kind"), category: f.get("category"), lifecycle: f.get("lifecycle"), criticality: f.get("criticality") || null,
        vendor_id: numOrNull(f.get("vendor_id")), owner_id: numOrNull(f.get("owner_id")), admin_id: numOrNull(f.get("admin_id")), environments: list(f.get("environments")), tech: list(f.get("tech")),
        docs_link: f.get("docs_link"), description: f.get("description"), how_we_use: f.get("how_we_use"), known_issues: f.get("known_issues") } });
      BA.rerender();
    });
    main.querySelector("#del-sys").onclick = BA.guard(async () => {
      if (!confirm("Delete this system? Its integrations go with it, and it's removed from the escalation playbook. Setting it to retired keeps the history.")) return;
      await BA.api(`/api/systems/${id}`, { method: "DELETE" });
      BA.go("/architecture/systems");
    });
  }

  async function renderIntegrations(main) {
    const [ints, systems, people] = await Promise.all([BA.api("/api/integrations"), BA.api("/api/systems"), BA.api("/api/people")]);
    const ro = presenting();
    const live = systems.filter((s) => s.lifecycle !== "retired");
    const sysSel = (name, sel, blank) => `<select name="${name}"${blank ? "" : " required"}><option value="">${blank || ""}</option>${live.map((s) => `<option value="${s.id}"${s.id === sel ? " selected" : ""}>${esc(s.name)}</option>`).join("")}</select>`;
    const fields = (i = {}) => `<div class="grid2">
        <label>Name<input name="name" value="${esc(i.name || "")}" required placeholder="Such as: orders to fulfillment"></label><label>Pattern<select name="pattern">${opts(PATTERNS, i.pattern || "API")}</select></label>
        <label>From${sysSel("from_id", i.from_id)}</label><label>To${sysSel("to_id", i.to_id)}</label>
        <label>Through <span class="quiet">(middleware, such as MuleSoft)</span>${sysSel("via_id", i.via_id, "Direct")}</label><label>Direction<select name="direction">${opts(["one way", "two way"], i.direction || "one way")}</select></label>
        <label>Data it carries<input name="data" value="${esc(i.data || "")}"></label><label>How often<input name="frequency" value="${esc(i.frequency || "")}" placeholder="Such as: real time, nightly"></label>
        <label>Protocol<input name="protocol" value="${esc(i.protocol || "")}" placeholder="Such as: REST, SOAP, SFTP, platform events"></label><label>Owner<select name="owner_id">${personOptions(people, i.owner_id)}</select></label>
        <label>Criticality<select name="criticality"><option value=""></option>${opts(CRIT, i.criticality)}</select></label><label>Status<select name="status">${opts(INT_STATUS, i.status || "live")}</select></label></div>
        <label>Private notes <span class="quiet">(failure modes, retries, quirks)</span><textarea name="notes">${esc(i.notes || "")}</textarea></label>`;
    const read = (form) => {
      const f = new FormData(form);
      return { name: f.get("name"), pattern: f.get("pattern"), from_id: numOrNull(f.get("from_id")), to_id: numOrNull(f.get("to_id")), via_id: numOrNull(f.get("via_id")), direction: f.get("direction"),
        data: f.get("data"), frequency: f.get("frequency"), protocol: f.get("protocol"), owner_id: numOrNull(f.get("owner_id")), criticality: f.get("criticality") || null, status: f.get("status"), notes: f.get("notes") };
    };
    main.innerHTML = `${archTabs("integrations")}
      <p class="quiet">Every connection between systems: what moves, how, how often, and who owns it.</p>
      <section class="card">${ints.map((i) => `<details class="plan-item${i.status === "retired" ? " dropped" : ""}" data-int="${i.id}"><summary><b>${esc(i.name)}</b><span class="quiet">${flow(i)}</span><span class="spacer"></span>
          <span class="pill">${esc(i.pattern)}</span>${i.frequency ? `<span class="quiet">${esc(i.frequency)}</span>` : ""}${i.criticality ? tonePill(i.criticality, CRIT_TONES) : ""}${i.status !== "live" ? `<span class="pill warn">${esc(i.status)}</span>` : ""}</summary>
          <p>${[i.data ? `Carries ${esc(i.data)}` : "", i.protocol ? esc(i.protocol) : "", i.owner_name ? `Owner: ${esc(i.owner_name)}` : "No owner yet"].filter(Boolean).join(" · ")}</p>
          ${ro ? "" : `<form class="edit-int">${fields(i)}<div class="actions"><button class="btn danger left" type="button" data-del-int>Delete</button>${BA.historyButton("integration", i.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("") || '<p class="quiet">No integrations yet.</p>'}</section>
      ${ro ? "" : live.length < 2 ? '<p class="quiet">Add at least two systems first.</p>' : `<form id="add-int" class="card"><h2>Add an integration</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form>`}`;
    if (ro) return;
    const add = main.querySelector("#add-int");
    if (add) add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/integrations", { method: "POST", body: read(add) }); BA.rerender(); });
    main.querySelectorAll("[data-int]").forEach((det) => {
      const id = det.dataset.int;
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/integrations/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del-int]").onclick = BA.guard(async () => {
        if (!confirm("Delete this integration?")) return;
        await BA.api(`/api/integrations/${id}`, { method: "DELETE" });
        BA.rerender();
      });
    });
  }

  async function renderDecisions(main) {
    const [adrs, systems, people] = await Promise.all([BA.api("/api/arch-decisions"), BA.api("/api/systems"), BA.api("/api/people")]);
    const ro = presenting();
    const sysName = Object.fromEntries(systems.map((s) => [s.id, s.name]));
    const section = (title, text) => (text ? `<h4>${title}</h4>${BA.md(text)}` : "");
    main.innerHTML = `${archTabs("decisions")}
      <p class="quiet">Architecture decision records: one page per significant technical decision, with the context, what was decided, what it costs, and what else was considered. Numbers never change; a replaced decision is marked superseded.</p>
      <section class="card">${adrs.map((a) => `<details class="plan-item${a.status === "superseded" || a.status === "rejected" ? " dropped" : ""}" data-adr="${a.id}"><summary><b>${adrLabel(a.number)}</b><span>${esc(a.title)}</span><span class="spacer"></span>
          ${a.date ? `<span class="quiet">${BA.fmtDate(a.date)}</span>` : ""}${tonePill(a.status, ADR_TONES)}${a.superseded_by_number ? `<span class="quiet">by ${adrLabel(a.superseded_by_number)}</span>` : ""}</summary>
          ${a.system_ids.length || a.jira_keys.length ? `<p>${BA.issueKeys(a.jira_keys)} ${BA.chips(a.system_ids.map((x) => sysName[x]).filter(Boolean))}</p>` : ""}
          ${section("Context", a.context)}${section("Decision", a.decision)}${section("Consequences", a.consequences)}${section("Alternatives considered", a.alternatives)}
          ${a.decided_by_name ? `<p class="quiet">Decided by ${esc(a.decided_by_name)}</p>` : ""}
          ${ro ? "" : `<form class="edit-adr"><div class="grid2"><label>Title<input name="title" value="${esc(a.title)}" required></label><label>Status<select name="status">${opts(ADR_STATUS, a.status)}</select></label>
            <label>Date<input type="date" name="date" value="${esc(a.date || "")}"></label><label>Decided by<select name="decided_by_id">${personOptions(people, a.decided_by_id)}</select></label>
            <label>Jira keys<input name="jira_keys" value="${esc((a.jira_keys || []).join(", "))}" placeholder="ABC-123"></label>
            <label>Superseded by<select name="superseded_by_id"><option value=""></option>${adrs.filter((x) => x.id !== a.id).map((x) => `<option value="${x.id}"${x.id === a.superseded_by_id ? " selected" : ""}>${adrLabel(x.number)} ${esc(x.title)}</option>`).join("")}</select></label></div>
            <label>Context <span class="quiet">(the problem and the forces at play)</span><textarea name="context">${esc(a.context || "")}</textarea></label>
            <label>Decision<textarea name="decision">${esc(a.decision || "")}</textarea></label>
            <label>Consequences <span class="quiet">(what gets easier, what gets harder)</span><textarea name="consequences">${esc(a.consequences || "")}</textarea></label>
            <label>Alternatives considered<textarea name="alternatives">${esc(a.alternatives || "")}</textarea></label>
            <label>Systems</label><div class="case-picks">${systems.map((s) => `<label class="check"><input type="checkbox" name="system_ids" value="${s.id}"${a.system_ids.includes(s.id) ? " checked" : ""}> ${esc(s.name)}</label>`).join("")}</div>
            <div class="actions"><button class="btn danger left" type="button" data-del-adr>Delete</button>${BA.historyButton("arch_decision", a.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("") || '<p class="quiet">No decisions recorded yet.</p>'}</section>
      ${ro ? "" : `<section class="card"><h2>Record a decision</h2><form id="add-adr" class="row"><input name="title" placeholder="Such as: use platform events for order updates" required style="max-width:420px"><button class="btn primary" type="submit">Add</button></form>
        <p class="quiet">It starts as proposed. Open it to write the context and options, then mark it accepted.</p></section>`}`;
    if (ro) return;
    main.querySelector("#add-adr").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api("/api/arch-decisions", { method: "POST", body: { title: new FormData(e.target).get("title") } });
      BA.rerender();
    });
    main.querySelectorAll("[data-adr]").forEach((det) => {
      const id = det.dataset.adr;
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(form);
        await BA.api(`/api/arch-decisions/${id}`, { method: "PATCH", body: { title: f.get("title"), status: f.get("status"), date: f.get("date") || null, decided_by_id: numOrNull(f.get("decided_by_id")),
          superseded_by_id: numOrNull(f.get("superseded_by_id")), context: f.get("context"), decision: f.get("decision"), consequences: f.get("consequences"), alternatives: f.get("alternatives"),
          system_ids: f.getAll("system_ids").map(Number), jira_keys: f.get("jira_keys") } });
        BA.rerender();
      });
      det.querySelector("[data-del-adr]").onclick = BA.guard(async () => {
        if (!confirm("Delete this decision record? Marking it rejected or superseded keeps the history.")) return;
        await BA.api(`/api/arch-decisions/${id}`, { method: "DELETE" });
        BA.rerender();
      });
    });
  }

  async function renderGuides(main) {
    const [guides, systems] = await Promise.all([BA.api("/api/guides"), BA.api("/api/systems")]);
    const ro = presenting();
    const sysName = Object.fromEntries(systems.map((s) => [s.id, s.name]));
    main.innerHTML = `${archTabs("guides")}
      <p class="quiet">Plain-language explainers: how a system works, how a flow runs end to end, how to set up a sandbox, how a release goes out. Written in Markdown.</p>
      <div class="sys-grid">${guides.map((g) => `<a class="sys-card" href="#/architecture/g-${g.id}"><b>${esc(g.title)}</b>${g.summary ? `<p class="clamp">${esc(g.summary)}</p>` : ""}
          <div class="quiet">${[g.audience, g.updated ? "updated " + BA.fmtDate(g.updated) : ""].filter(Boolean).map(esc).join(" · ")}</div>
          ${g.system_ids.length ? `<div>${BA.chips(g.system_ids.map((x) => sysName[x]).filter(Boolean))}</div>` : ""}</a>`).join("") || '<p class="empty">No guides yet.</p>'}</div>
      ${ro ? "" : `<section class="card" style="margin-top:16px"><h2>Write a guide</h2><form id="add-guide" class="row"><input name="title" placeholder="Such as: how an order reaches fulfillment" required style="max-width:420px"><button class="btn primary" type="submit">Start writing</button></form></section>`}`;
    const add = main.querySelector("#add-guide");
    if (add)
      add.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const g = await BA.api("/api/guides", { method: "POST", body: { title: new FormData(add).get("title") } });
        BA.go(`/architecture/g-${g.id}`);
      });
  }

  async function renderGuide(main, id) {
    const [g, systems] = await Promise.all([BA.api(`/api/guides/${id}`), BA.api("/api/systems")]);
    const ro = presenting();
    document.getElementById("view-title").textContent = g.title;
    const linked = systems.filter((s) => g.system_ids.includes(s.id));
    main.innerHTML = `<p><a href="#/architecture/guides">All guides</a></p>
      <article class="card guide"><h2>${esc(g.title)}</h2>${g.summary ? `<p class="quiet">${esc(g.summary)}</p>` : ""}
        ${g.body ? BA.md(g.body) : '<p class="quiet">Nothing written yet.</p>'}
        <p class="quiet">${[g.audience ? "For " + esc(g.audience) : "", g.updated ? "Updated " + BA.fmtDate(g.updated) : ""].filter(Boolean).join(" · ")}
          ${linked.length ? ` · ${linked.map((s) => `<a href="#/architecture/s-${s.id}">${esc(s.name)}</a>`).join(", ")}` : ""}</p></article>
      ${ro ? "" : `<details class="card" ${g.body ? "" : "open"}><summary><b>Edit</b></summary><form id="edit-guide">
        <div class="grid2"><label>Title<input name="title" value="${esc(g.title)}" required></label><label>For<input name="audience" value="${esc(g.audience || "")}" placeholder="Such as: new developers, product managers"></label></div>
        <label>Summary<input name="summary" value="${esc(g.summary || "")}"></label>
        <label>Guide <span class="quiet">(Markdown: # headings, lists, **bold**, links)</span><textarea name="body" rows="16" class="mono">${esc(g.body || "")}</textarea></label>
        <label>Systems</label><div class="case-picks">${systems.map((s) => `<label class="check"><input type="checkbox" name="system_ids" value="${s.id}"${g.system_ids.includes(s.id) ? " checked" : ""}> ${esc(s.name)}</label>`).join("")}</div>
        <div class="actions"><button class="btn danger left" type="button" id="del-guide">Delete</button>${BA.historyButton("guide", id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}`;
    if (ro) return;
    const form = main.querySelector("#edit-guide");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      await BA.api(`/api/guides/${id}`, { method: "PATCH", body: { title: f.get("title"), audience: f.get("audience"), summary: f.get("summary"), body: f.get("body"), system_ids: f.getAll("system_ids").map(Number) } });
      BA.rerender();
    });
    main.querySelector("#del-guide").onclick = BA.guard(async () => {
      if (!confirm("Delete this guide?")) return;
      await BA.api(`/api/guides/${id}`, { method: "DELETE" });
      BA.go("/architecture/guides");
    });
  }

  // ---------------------------------------------------------------- Onboarding

  const OB_CATEGORIES = ["accounts and access", "tools and setup", "people", "ways of working", "systems and architecture", "learning", "first work", "admin and compliance"];
  const OB_OWNERS = ["new member", "manager", "buddy", "IT or admin"];
  const OB_TRACKS = ["Salesforce developer", "MuleSoft developer", "QA", "employee", "contractor"];
  const OB_PHASES = [["Before day 1", null, 0], ["Week 1", 1, 7], ["Weeks 2 to 4", 8, 30], ["Days 31 to 90", 31, 90], ["After day 90", 91, null]];
  const OWNER_TONES = { manager: "warn", buddy: "good", "IT or admin": "", "new member": "accent" };
  const obPhase = (day) => (day == null ? "No date" : (OB_PHASES.find(([, lo, hi]) => (lo == null || day >= lo) && (hi == null || day <= hi)) || ["No date"])[0]);
  const dayLabel = (n) => (n == null ? "" : n === 0 || n === -1 ? "the day before" : n < 0 ? `${-n} days before` : `day ${n}`);
  const obTabs = (active) => `<nav class="tabs">${[["", "New members"], ["template", "Checklist template"], ["materials", "Materials"]]
    .map(([k, label]) => `<a href="#/onboarding${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const openLink = (link) => (!link ? "" : link.startsWith("#/") ? `<a class="btn" href="${esc(link)}">Open</a>` : /^https?:\/\//.test(link) ? `<a class="btn" href="${esc(link)}" target="_blank" rel="noopener">Open ${BA.icon("external-link")}</a>` : "");
  const progress = (done, total) => `<div class="progress" title="${done} of ${total} done"><span style="width:${total ? Math.round((100 * done) / total) : 0}%"></span></div>`;

  BA.view("/onboarding", {
    title: "Onboarding",
    async render(main, param) {
      if (param === "template") return renderObTemplate(main);
      if (param === "materials") return renderObMaterials(main);
      if (param && /^\d+$/.test(param)) return renderOnboarding(main, Number(param));
      const [obs, people, items] = await Promise.all([BA.api("/api/onboardings"), BA.api("/api/people"), BA.api("/api/onboarding-items")]);
      const ro = presenting();
      main.innerHTML = `${obTabs("")}
        ${!items.length && !ro ? `<section class="card"><h2>Start with a checklist</h2><p class="quiet">The starter checklist covers access, setup, people, ways of working, systems, learning and first work, from the week before day 1 to day 90, with separate items for Salesforce developers, MuleSoft developers, QA, employees and contractors. Anything specific to your company is a [Placeholder] for you to fill in.</p>
          <button class="btn primary" id="ob-starter">Load the starter checklist</button></section>` : ""}
        <div class="sys-grid">${obs.map((o) => `<a class="sys-card" href="#/onboarding/${o.id}"><div class="row"><b>${esc(o.person_name)}</b><span class="spacer"></span>${BA.statusPill(o.status)}</div>
            <div class="quiet">${esc(o.person_role || "")}${o.start_date ? ` · starts ${BA.fmtDate(o.start_date)}` : ""}${o.buddy_name ? ` · buddy ${esc(o.buddy_name)}` : ""}</div>
            ${progress(o.done_count, o.total)}<div class="quiet">${o.done_count} of ${o.total} done</div>${o.tracks.length ? `<div>${BA.chips(o.tracks)}</div>` : ""}</a>`).join("") || '<p class="empty">Nobody being onboarded yet.</p>'}</div>
        ${ro ? "" : `<section class="card" style="margin-top:16px"><h2>Someone's joining</h2><form id="start-ob"><div class="grid2">
          <label>Who <span class="quiet">(add them under <a href="#/people">People</a> first)</span><select name="person_id" required>${personOptions(people)}</select></label>
          <label>Start date<input type="date" name="start_date"></label>
          <label>Buddy<select name="buddy_id">${personOptions(people)}</select></label></div>
          <label>Tracks <span class="quiet">(items for every track are always included)</span></label><div class="row">${OB_TRACKS.map((t) => `<label class="check"><input type="checkbox" name="tracks" value="${t}"> ${t}</label>`).join("")}</div>
          <div class="actions"><button class="btn primary" type="submit">Build their checklist</button></div></form></section>`}`;
      const starter = main.querySelector("#ob-starter");
      if (starter) starter.onclick = BA.guard(async () => { await BA.api("/api/onboarding/starter", { method: "POST", body: {} }); BA.rerender(); });
      const form = main.querySelector("#start-ob");
      if (form)
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          const ob = await BA.api("/api/onboardings", { method: "POST", body: { person_id: numOrNull(f.get("person_id")), start_date: f.get("start_date") || null, buddy_id: numOrNull(f.get("buddy_id")), tracks: f.getAll("tracks") } });
          BA.toast(`${ob.copied} items copied from the checklist.`);
          BA.go(`/onboarding/${ob.id}`);
        });
    },
  });

  async function renderOnboarding(main, id) {
    const [d, people] = await Promise.all([BA.api(`/api/onboardings/${id}/board`), BA.api("/api/people")]);
    const o = d.onboarding;
    const ro = presenting();
    document.getElementById("view-title").textContent = `Onboarding: ${o.person_name}`;
    const task = (t) => `<div class="ob-task${t.done ? " done" : ""}" data-task="${t.id}">
        <label class="check"><input type="checkbox" data-done${t.done ? " checked" : ""}${ro ? " disabled" : ""}> <span>${esc(t.title)}</span></label>
        <span class="spacer"></span>${t.owner_role !== "new member" ? `<span class="pill ${OWNER_TONES[t.owner_role] || ""}">${esc(t.owner_role)}</span>` : ""}
        ${t.due ? `<span class="${t.overdue ? "pill bad" : "quiet"}">${BA.fmtDate(t.due)}</span>` : `<span class="quiet">${dayLabel(t.due_day)}</span>`}${openLink(t.link)}${BA.keysEditor(`/api/onboarding-tasks/${t.id}`, t.jira_keys)}
        ${t.description || !ro ? `<details><summary class="quiet">More</summary>${t.description ? BA.md(t.description) : ""}
          ${ro ? "" : `<label>Notes <span class="quiet">(private)</span><textarea data-notes>${esc(t.notes || "")}</textarea></label><button class="btn danger" type="button" data-del>Remove from this checklist</button>`}</details>` : ""}</div>`;
    main.innerHTML = `<p><a href="#/onboarding">All new members</a></p>
      <section class="card"><div class="row"><h2>${esc(o.person_name)}</h2><span class="quiet">${esc(o.person_role || "")}</span><span class="spacer"></span>
          ${ro ? BA.statusPill(o.status) : `<select id="ob-status" style="max-width:150px">${opts(["not started", "in progress", "done"], o.status)}</select>`}</div>
        <p class="quiet">${o.start_date ? `Starts ${BA.fmtDate(o.start_date)}` : "No start date yet, so items show as days"}${o.buddy_name ? ` · Buddy: ${esc(o.buddy_name)}` : ""}</p>
        ${progress(o.done_count, o.total)}<div class="row"><span class="quiet">${o.done_count} of ${o.total} done</span>${d.overdue ? `<span class="pill bad">${d.overdue} overdue</span>` : ""}
          ${Object.entries(d.by_owner).filter(([, n]) => n).map(([who, n]) => `<span class="pill ${OWNER_TONES[who] || ""}">${n} open for ${esc(who === "new member" ? "them" : who)}</span>`).join(" ")}<span class="spacer"></span>
          ${ro ? "" : `<button class="btn" id="copy-ob">${BA.icon("copy")} Copy checklist to send</button>`}</div>
        ${o.tracks.length ? `<p>${BA.chips(o.tracks)}</p>` : ""}</section>
      ${d.phases.map((p) => `<section class="card"><h2>${esc(p.name)} <span class="quiet">${p.tasks.filter((t) => t.done).length} of ${p.tasks.length}</span></h2>${p.tasks.map(task).join("")}</section>`).join("") || '<p class="empty">No items. Add some below, or load the checklist template first.</p>'}
      ${ro ? "" : `<section class="card"><h2>Add an item just for ${esc(o.person_name)}</h2><form id="add-task" class="row"><input name="title" required placeholder="What needs doing" style="max-width:360px">
          <input type="number" name="due_day" placeholder="Day" style="max-width:90px"><select name="owner_role" style="max-width:160px">${opts(OB_OWNERS, "new member")}</select><button class="btn" type="submit">Add</button></form></section>
        <form id="edit-ob" class="card"><h2>Details</h2><div class="grid2"><label>Start date<input type="date" name="start_date" value="${esc(o.start_date || "")}"></label><label>Buddy<select name="buddy_id">${personOptions(people, o.buddy_id)}</select></label></div>
          <label>Private notes <span class="quiet">(how it's going)</span><textarea name="notes">${esc(o.notes || "")}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" id="del-ob">Delete</button><button class="btn primary" type="submit">Save</button></div></form>`}`;
    if (ro) return;
    main.querySelectorAll("[data-task]").forEach((row) => {
      const tid = row.dataset.task;
      row.querySelector("[data-done]").onchange = BA.guard(async (e) => { await BA.api(`/api/onboarding-tasks/${tid}`, { method: "PATCH", body: { done: e.target.checked } }); BA.rerender(); });
      const notes = row.querySelector("[data-notes]");
      if (notes) notes.onchange = BA.guard(async () => { await BA.api(`/api/onboarding-tasks/${tid}`, { method: "PATCH", body: { notes: notes.value } }); BA.toast("Saved."); });
      const del = row.querySelector("[data-del]");
      if (del) del.onclick = BA.guard(async () => { if (!confirm("Remove this item from their checklist? The template keeps it.")) return; await BA.api(`/api/onboarding-tasks/${tid}`, { method: "DELETE" }); BA.rerender(); });
    });
    main.querySelector("#ob-status").onchange = BA.guard(async (e) => { await BA.api(`/api/onboardings/${id}`, { method: "PATCH", body: { status: e.target.value } }); BA.toast("Saved."); });
    main.querySelector("#copy-ob").onclick = BA.guard(async () => {
      const out = await BA.api(`/api/onboardings/${id}/checklist/export`, { method: "POST", body: {} });
      await navigator.clipboard.writeText(out.markdown);
      BA.toast("Checklist copied. Private notes aren't included.");
    });
    main.querySelector("#add-task").onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      await BA.api("/api/onboarding-tasks", { method: "POST", body: { onboarding_id: id, title: f.get("title"), due_day: numOrNull(f.get("due_day")), owner_role: f.get("owner_role") } });
      BA.rerender();
    });
    const edit = main.querySelector("#edit-ob");
    edit.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(edit);
      await BA.api(`/api/onboardings/${id}`, { method: "PATCH", body: { start_date: f.get("start_date") || null, buddy_id: numOrNull(f.get("buddy_id")), notes: f.get("notes") } });
      BA.rerender();
    });
    main.querySelector("#del-ob").onclick = BA.guard(async () => {
      if (!confirm("Delete this onboarding and its checklist?")) return;
      await BA.api(`/api/onboardings/${id}`, { method: "DELETE" });
      BA.go("/onboarding");
    });
  }

  async function renderObTemplate(main) {
    const items = await BA.api("/api/onboarding-items");
    const ro = presenting();
    const filter = sessionStorage.getItem("ba-ob-track") || "";
    const shown = items.filter((i) => !filter || !i.tracks.length || i.tracks.includes(filter));
    const groups = [...OB_PHASES.map(([n]) => n), "No date"].map((n) => [n, shown.filter((i) => obPhase(i.due_day) === n)]).filter(([, l]) => l.length);
    const fields = (i = {}) => `<div class="grid2"><label>Title<input name="title" value="${esc(i.title || "")}" required></label><label>Category<select name="category">${opts(OB_CATEGORIES, i.category || "ways of working")}</select></label>
        <label>Day <span class="quiet">(1 is the first day; -7 is a week before)</span><input type="number" name="due_day" value="${esc(i.due_day ?? "")}"></label><label>Who does it<select name="owner_role">${opts(OB_OWNERS, i.owner_role || "new member")}</select></label>
        <label>Link <span class="quiet">(a toolkit page such as #/sdlc, or a web address)</span><input name="link" value="${esc(i.link || "")}"></label><label>Minutes <span class="quiet">(for reading or courses)</span><input type="number" name="minutes" value="${esc(i.minutes ?? "")}"></label></div>
        <label>Tracks <span class="quiet">(none ticked means everyone)</span></label><div class="row">${OB_TRACKS.map((t) => `<label class="check"><input type="checkbox" name="tracks" value="${t}"${(i.tracks || []).includes(t) ? " checked" : ""}> ${t}</label>`).join("")}</div>
        <label>Details<textarea name="description">${esc(i.description || "")}</textarea></label>
        ${i.id ? `<label class="check"><input type="checkbox" name="active"${i.active ? " checked" : ""}> In use</label>` : ""}`;
    const read = (form) => {
      const f = new FormData(form);
      const body = { title: f.get("title"), category: f.get("category"), due_day: numOrNull(f.get("due_day")), owner_role: f.get("owner_role"), link: f.get("link") || null, minutes: numOrNull(f.get("minutes")), tracks: f.getAll("tracks"), description: f.get("description") };
      if (form.elements.active) body.active = form.elements.active.checked;
      return body;
    };
    main.innerHTML = `${obTabs("template")}
      <div class="row"><p class="quiet">The checklist every new member starts from. Changes here apply to the next person; checklists already started keep their own copy.</p><span class="spacer"></span>
        <select id="ob-track" style="max-width:220px"><option value="">Every track</option>${OB_TRACKS.map((t) => `<option${t === filter ? " selected" : ""}>${t}</option>`).join("")}</select></div>
      ${groups.map(([n, list]) => `<section class="card"><h2>${esc(n)} <span class="quiet">${list.length}</span></h2>${list.map((i) => `<details class="plan-item${i.active ? "" : " dropped"}" data-item="${i.id}"><summary><span>${esc(i.title)}</span><span class="spacer"></span>
          ${i.tracks.length ? BA.chips(i.tracks) : ""}<span class="quiet">${esc(i.category)}</span>${i.owner_role !== "new member" ? `<span class="pill ${OWNER_TONES[i.owner_role] || ""}">${esc(i.owner_role)}</span>` : ""}<span class="quiet">${dayLabel(i.due_day)}</span></summary>
          ${i.description ? BA.md(i.description) : ""}${ro ? "" : `<form class="edit-item">${fields(i)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button><button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("")}</section>`).join("") ||
        '<p class="empty">No checklist yet. Load the starter checklist from the New members tab, or add items below.</p>'}
      ${ro ? "" : `<form id="add-item" class="card"><h2>Add an item</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form>`}`;
    main.querySelector("#ob-track").onchange = (e) => { sessionStorage.setItem("ba-ob-track", e.target.value); BA.rerender(); };
    if (ro) return;
    const add = main.querySelector("#add-item");
    add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/onboarding-items", { method: "POST", body: read(add) }); BA.rerender(); });
    main.querySelectorAll("details[data-item]").forEach((det) => {
      const iid = det.dataset.item;
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/onboarding-items/${iid}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this item from the template? Checklists already started keep it. Unticking 'In use' hides it instead.")) return; await BA.api(`/api/onboarding-items/${iid}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderObMaterials(main) {
    const items = (await BA.api("/api/onboarding-items")).filter((i) => i.active && (i.link || i.category === "learning" || i.minutes));
    const groups = OB_CATEGORIES.map((c) => [c, items.filter((i) => i.category === c)]).filter(([, l]) => l.length);
    const total = items.reduce((n, i) => n + (i.minutes || 0), 0);
    main.innerHTML = `${obTabs("materials")}
      <p class="quiet">Everything a new member reads, watches or works through, taken from the checklist template: toolkit pages such as the SDLC, definition of done and architecture guides, plus outside courses and documents.${total ? ` About ${Math.round(total / 60)} hours in all.` : ""}</p>
      ${groups.map(([c, list]) => `<section class="card"><h2>${esc(c[0].toUpperCase() + c.slice(1))}</h2>${list.map((i) => `<div class="item"><span>${esc(i.title)}</span><span class="spacer"></span>
          ${i.tracks.length ? BA.chips(i.tracks) : ""}${i.minutes ? `<span class="quiet">${i.minutes} min</span>` : ""}<span class="quiet">${dayLabel(i.due_day)}</span>${openLink(i.link)}</div>`).join("")}</section>`).join("") ||
        '<p class="empty">No materials yet. Give checklist items a link or mark them as learning.</p>'}`;
  }

  // ---------------------------------------------------------------- SDLC

  const POLICY_CATEGORIES = ["branching", "code review", "testing", "release", "change management", "hotfix", "security", "data", "documentation", "other"];
  const POLICY_TONES = { draft: "warn", agreed: "good", retired: "" };
  const sdlcTabs = (active) => `<nav class="tabs">${[["", "Lifecycle"], ["environments", "Environments"], ["policies", "Policies"], ["history", "History and sharing"]]
    .map(([k, label]) => `<a href="#/sdlc${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const lines = (v) => (v || "").split("\n").map((x) => x.trim()).filter(Boolean);

  BA.view("/sdlc", {
    title: "SDLC",
    async render(main, param) {
      const d = await BA.api("/api/sdlc");
      const ro = presenting();
      const empty = !d.stages.length && !d.environments.length && !d.policies.length;
      const starterCard = empty && !ro ? `<section class="card"><h2>Start from a draft</h2><p class="quiet">Nine stages from intake to support, each with when it starts, what happens and when it's done; Salesforce and MuleSoft environments; and draft policies for branching, review, testing, release, changes, hotfixes, freezes and test data. Anything specific to how your company works is a [Placeholder] for the team to settle.</p>
        <button class="btn primary" id="sdlc-starter">Load the starter SDLC</button></section>` : "";
      const bindStarter = () => { const b = main.querySelector("#sdlc-starter"); if (b) b.onclick = BA.guard(async () => { await BA.api("/api/sdlc/starter", { method: "POST", body: {} }); BA.rerender(); }); };
      if (param === "environments") return renderEnvs(main, d, ro, starterCard, bindStarter);
      if (param === "policies") return renderPolicies(main, d, ro, starterCard, bindStarter);
      if (param === "history") return renderSdlcHistory(main, d, ro);
      const systems = await BA.api("/api/systems");
      const stage = (s, i) => `<section class="card sdlc-stage" id="stage-${s.id}" data-stage="${s.id}">
          <div class="row"><span class="stage-n">${i + 1}</span><h2>${esc(s.name)}</h2><span class="spacer"></span>${s.duration ? `<span class="quiet">${esc(s.duration)}</span>` : ""}
            ${ro ? "" : `<button class="icon-btn" title="Move earlier" data-move="up"${i === 0 ? " disabled" : ""}>${BA.icon("arrow-up")}</button><button class="icon-btn" title="Move later" data-move="down"${i === d.stages.length - 1 ? " disabled" : ""}>${BA.icon("arrow-down")}</button>`}</div>
          ${s.purpose ? `<p>${esc(s.purpose)}</p>` : ""}
          <div class="stage-cols"><div><h4>Starts when</h4>${s.entry_criteria.length ? `<ul class="checklist">${s.entry_criteria.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : '<p class="quiet">Not written yet.</p>'}</div>
            <div><h4>Done when</h4>${s.exit_criteria.length ? `<ul class="checklist exit">${s.exit_criteria.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : '<p class="quiet">Not written yet.</p>'}</div></div>
          ${s.activities ? `<h4>What happens</h4>${BA.md(s.activities)}` : ""}
          <div class="facts">${s.roles ? `<div><span class="quiet">Who</span> ${esc(s.roles)}</div>` : ""}${s.artifacts ? `<div><span class="quiet">Produces</span> ${esc(s.artifacts)}</div>` : ""}
            ${s.environment ? `<div><span class="quiet">Environment</span> ${esc(s.environment)}</div>` : ""}${s.systems.length ? `<div><span class="quiet">Tools</span> ${BA.chips(s.systems)}</div>` : ""}
            ${s.links ? `<div><span class="quiet">See also</span> ${lines(s.links).map((l) => l.startsWith("#/") ? `<a href="${esc(l)}">${esc(l.slice(2))}</a>` : /^https?:\/\//.test(l) ? `<a href="${esc(l)}" target="_blank" rel="noopener">${esc(l)}</a>` : esc(l)).join(", ")}</div>` : ""}</div>
          ${ro ? "" : `<details><summary class="quiet">Edit this stage</summary><form class="edit-stage"><div class="grid2">
            <label>Name<input name="name" value="${esc(s.name)}" required></label><label>Typical time<input name="duration" value="${esc(s.duration || "")}" placeholder="Such as: one to two days"></label>
            <label>Who's involved<input name="roles" value="${esc(s.roles || "")}"></label><label>What it produces<input name="artifacts" value="${esc(s.artifacts || "")}"></label>
            <label>Environment<input name="environment" value="${esc(s.environment || "")}"></label><label>See also <span class="quiet">(one toolkit page or link per line)</span><textarea name="links" rows="2">${esc(s.links || "")}</textarea></label></div>
            <label>Purpose<input name="purpose" value="${esc(s.purpose || "")}"></label>
            <div class="grid2"><label>Starts when <span class="quiet">(one per line)</span><textarea name="entry_criteria" rows="4">${esc(s.entry_criteria.join("\n"))}</textarea></label>
              <label>Done when <span class="quiet">(one per line)</span><textarea name="exit_criteria" rows="4">${esc(s.exit_criteria.join("\n"))}</textarea></label></div>
            <label>What happens<textarea name="activities">${esc(s.activities || "")}</textarea></label>
            <label>Tools</label><div class="case-picks">${systems.map((x) => `<label class="check"><input type="checkbox" name="system_ids" value="${x.id}"${s.system_ids.includes(x.id) ? " checked" : ""}> ${esc(x.name)}</label>`).join("") || '<span class="quiet">Add systems and tools under Architecture first.</span>'}</div>
            <label>Private notes<textarea name="notes">${esc(s.notes || "")}</textarea></label>
            <div class="actions"><button class="btn danger left" type="button" data-del>Delete stage</button>${BA.historyButton("sdlc_stage", s.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}</section>`;
      main.innerHTML = `${sdlcTabs("")}${starterCard}
        ${d.stages.length ? `<nav class="stage-flow">${d.stages.map((s, i) => `<a href="#stage-${s.id}" data-jump="${s.id}"><span>${i + 1}</span>${esc(s.name)}</a>`).join("")}</nav>` : ""}
        ${d.stages.map(stage).join("")}
        ${ro ? "" : `<section class="card"><h2>Add a stage</h2><form id="add-stage" class="row"><input name="name" required placeholder="Stage name" style="max-width:280px"><button class="btn" type="submit">Add at the end</button></form></section>`}`;
      bindStarter();
      main.querySelectorAll("[data-jump]").forEach((a) => (a.onclick = (e) => { e.preventDefault(); document.getElementById(`stage-${a.dataset.jump}`).scrollIntoView({ behavior: "smooth" }); }));
      if (ro) return;
      main.querySelector("#add-stage").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/sdlc-stages", { method: "POST", body: { name: new FormData(e.target).get("name"), position: d.stages.length } });
        BA.rerender();
      });
      main.querySelectorAll("[data-stage]").forEach((sec) => {
        const id = sec.dataset.stage;
        sec.querySelectorAll("[data-move]").forEach((b) => (b.onclick = BA.guard(async () => { await BA.api(`/api/sdlc-stages/${id}/move`, { method: "POST", body: { direction: b.dataset.move } }); BA.rerender(); })));
        const form = sec.querySelector("form");
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          await BA.api(`/api/sdlc-stages/${id}`, { method: "PATCH", body: { name: f.get("name"), duration: f.get("duration"), roles: f.get("roles"), artifacts: f.get("artifacts"), environment: f.get("environment"),
            links: f.get("links"), purpose: f.get("purpose"), entry_criteria: lines(f.get("entry_criteria")), exit_criteria: lines(f.get("exit_criteria")), activities: f.get("activities"),
            system_ids: f.getAll("system_ids").map(Number), notes: f.get("notes") } });
          BA.rerender();
        });
        sec.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this stage?")) return; await BA.api(`/api/sdlc-stages/${id}`, { method: "DELETE" }); BA.rerender(); });
      });
    },
  });

  async function renderEnvs(main, d, ro, starterCard, bindStarter) {
    const systems = await BA.api("/api/systems");
    const fields = (e = {}) => `<div class="grid2"><label>Name<input name="name" value="${esc(e.name || "")}" required></label><label>Platform<input name="platform" value="${esc(e.platform || "")}" placeholder="Such as: Salesforce, MuleSoft"></label>
        <label>Order in the path<input type="number" name="position" value="${esc(e.position ?? "")}"></label><label>System<select name="system_id">${sysOptions(systems, e.system_id)}</select></label>
        <label>Purpose<input name="purpose" value="${esc(e.purpose || "")}"></label><label>Data it holds<input name="data" value="${esc(e.data || "")}"></label>
        <label>Who deploys<input name="deploys_by" value="${esc(e.deploys_by || "")}"></label><label>Refresh<input name="refresh" value="${esc(e.refresh || "")}" placeholder="Such as: after each platform release"></label>
        <label>Branch <span class="quiet">(the Bitbucket branch tied to this environment)</span><input name="branch" value="${esc(e.branch || "")}"></label><label>How changes arrive<input name="deploy_method" value="${esc(e.deploy_method || "")}" placeholder="Such as: deployed when a pull request merges"></label></div>
        <label>Private notes<textarea name="notes">${esc(e.notes || "")}</textarea></label>`;
    const read = (form) => { const f = new FormData(form); return { name: f.get("name"), platform: f.get("platform") || null, position: numOrNull(f.get("position")) ?? 0, system_id: numOrNull(f.get("system_id")), purpose: f.get("purpose"), data: f.get("data"), deploys_by: f.get("deploys_by"), refresh: f.get("refresh"), branch: f.get("branch"), deploy_method: f.get("deploy_method"), notes: f.get("notes") }; };
    main.innerHTML = `${sdlcTabs("environments")}${starterCard}
      <p class="quiet">Where changes go on their way to production, in order, what each environment is for, and the branch tied to it. Salesforce work moves through sandboxes rather than Git flow.</p>
      <details class="card env-ref"><summary><b>Salesforce's reference model</b><span class="quiet">the org development model, from Trailhead</span></summary>
        <div class="tablewrap"><table class="data"><thead><tr><th>Stage</th><th>Sandbox type</th><th>Data</th><th>Refresh</th></tr></thead><tbody>
          <tr><td>Develop and test, one per developer</td><td>Developer</td><td>Configuration only</td><td>Daily</td></tr>
          <tr><td>Build the release: everyone's merged work together</td><td>Developer Pro</td><td>Configuration and seeded test data</td><td>Daily</td></tr>
          <tr><td>Test the release, including user acceptance</td><td>Partial Copy</td><td>A sample of production data, chosen by a template</td><td>Every 5 days</td></tr>
          <tr><td>Staging, performance testing and training</td><td>Full</td><td>A full copy of production</td><td>Every 29 days</td></tr>
          <tr><td>Release</td><td>Production</td><td>Live</td><td>n/a</td></tr></tbody></table></div>
        <p class="quiet">Changes are kept in source control and deployed from there at each step. Sources: <a href="https://trailhead.salesforce.com/content/learn/modules/org-development-model" target="_blank" rel="noopener">Trailhead: Org Development Model</a> · <a href="https://developer.salesforce.com/docs/platform/sfvscode-extensions/guide/orgdev.html" target="_blank" rel="noopener">Salesforce docs</a></p></details>
      ${d.environments.map((g) => `<section class="card"><h2>${esc(g.platform)}</h2><div class="env-path">${g.environments.map((e) => `<span class="env-box">${esc(e.name)}${e.branch ? `<small>${esc(e.branch)}</small>` : ""}</span>`).join('<span class="env-arrow">→</span>')}</div>
        ${g.environments.map((e) => `<details class="plan-item" data-env="${e.id}"><summary><b>${esc(e.name)}</b><span class="quiet">${esc(e.purpose || "")}</span><span class="spacer"></span>${e.data ? `<span class="quiet">${esc(e.data)}</span>` : ""}</summary>
          <p>${[e.branch ? `Branch: ${esc(e.branch)}` : "", e.deploy_method ? `Changes arrive: ${esc(e.deploy_method)}` : "", e.deploys_by ? `Deploys: ${esc(e.deploys_by)}` : "", e.refresh ? `Refresh: ${esc(e.refresh)}` : "", e.system_name ? `System: ${esc(e.system_name)}` : ""].filter(Boolean).join(" · ")}</p>
          ${ro ? "" : `<form>${fields(e)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button><button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("")}</section>`).join("") || (starterCard ? "" : '<p class="empty">No environments yet.</p>')}
      ${ro ? "" : `<form id="add-env" class="card"><h2>Add an environment</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form>`}`;
    bindStarter();
    if (ro) return;
    const add = main.querySelector("#add-env");
    add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/sdlc-environments", { method: "POST", body: read(add) }); BA.rerender(); });
    main.querySelectorAll("[data-env]").forEach((det) => {
      const id = det.dataset.env, form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/sdlc-environments/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this environment?")) return; await BA.api(`/api/sdlc-environments/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderPolicies(main, d, ro, starterCard, bindStarter) {
    const people = await BA.api("/api/people");
    const groups = POLICY_CATEGORIES.map((c) => [c, d.policies.filter((p) => p.category === c)]).filter(([, l]) => l.length);
    const read = (form) => { const f = new FormData(form); return { title: f.get("title"), category: f.get("category"), status: f.get("status"), agreed_on: f.get("agreed_on") || null, owner_id: numOrNull(f.get("owner_id")), body: f.get("body") }; };
    main.innerHTML = `${sdlcTabs("policies")}${starterCard}
      <p class="quiet">The rules the team has agreed. A policy stays a draft until the team agrees it; mark it agreed with the date so everyone knows it's in force.</p>
      ${groups.map(([c, list]) => `<section class="card"><h2>${esc(c[0].toUpperCase() + c.slice(1))}</h2>${list.map((p) => `<details class="plan-item${p.status === "retired" ? " dropped" : ""}" data-policy="${p.id}"><summary><b>${esc(p.title)}</b><span class="spacer"></span>
          ${tonePill(p.status, POLICY_TONES)}${p.agreed_on ? `<span class="quiet">${BA.fmtDate(p.agreed_on)}</span>` : ""}${p.owner_name ? `<span class="quiet">${esc(p.owner_name)}</span>` : ""}</summary>
          ${p.body ? BA.md(p.body) : '<p class="quiet">Not written yet.</p>'}
          ${ro ? "" : `<form><div class="grid2"><label>Title<input name="title" value="${esc(p.title)}" required></label><label>Category<select name="category">${opts(POLICY_CATEGORIES, p.category)}</select></label>
            <label>Status<select name="status">${opts(["draft", "agreed", "retired"], p.status)}</select></label><label>Agreed on<input type="date" name="agreed_on" value="${esc(p.agreed_on || "")}"></label>
            <label>Owner<select name="owner_id">${personOptions(people, p.owner_id)}</select></label></div>
            <label>Policy <span class="quiet">(Markdown)</span><textarea name="body" rows="6">${esc(p.body || "")}</textarea></label>
            <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("sdlc_policy", p.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("")}</section>`).join("") || (starterCard ? "" : '<p class="empty">No policies yet.</p>')}
      ${ro ? "" : `<section class="card"><h2>Add a policy</h2><form id="add-policy" class="row"><input name="title" required placeholder="Policy title" style="max-width:320px"><select name="category" style="max-width:190px">${opts(POLICY_CATEGORIES, "other")}</select><button class="btn" type="submit">Add</button></form></section>`}`;
    bindStarter();
    if (ro) return;
    main.querySelector("#add-policy").onsubmit = BA.guard(async (e) => { e.preventDefault(); const f = new FormData(e.target); await BA.api("/api/sdlc-policies", { method: "POST", body: { title: f.get("title"), category: f.get("category") } }); BA.rerender(); });
    main.querySelectorAll("[data-policy]").forEach((det) => {
      const id = det.dataset.policy, form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/sdlc-policies/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this policy? Marking it retired keeps the record.")) return; await BA.api(`/api/sdlc-policies/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderSdlcHistory(main, d, ro) {
    const doc = await BA.api("/api/sdlc/document");
    const label = { sdlc_stage: "stage", sdlc_environment: "environment", sdlc_policy: "policy" };
    main.innerHTML = `${sdlcTabs("history")}
      <section class="card"><div class="row"><h2>Share it</h2><span class="spacer"></span>${ro ? "" : `<button class="btn primary" id="copy-sdlc">${BA.icon("copy")} Copy as Markdown</button>`}</div>
        <p class="quiet">The whole SDLC as one document, without private notes: for the team wiki, a new member, or leadership. New members get a link to it in their onboarding checklist.</p>
        <details><summary>Preview</summary><div class="msg-preview">${BA.md(doc.markdown)}</div></details></section>
      ${d.history ? `<section class="card"><h2>Recent changes</h2><div class="tablewrap"><table class="data"><thead><tr><th>When</th><th>What</th><th>Field</th><th>By</th></tr></thead><tbody>${
        d.history.map((h) => `<tr><td>${esc(h.at)}</td><td>${label[h.entity] || esc(h.entity)} ${esc(h.record_id)}</td><td>${esc(h.field)}</td><td>${esc(h.source)}</td></tr>`).join("") || '<tr><td colspan="4" class="empty">No changes yet.</td></tr>'
      }</tbody></table></div></section>` : ""}`;
    const copy = main.querySelector("#copy-sdlc");
    if (copy) copy.onclick = BA.guard(async () => {
      const out = await BA.api("/api/sdlc/document/export", { method: "POST", body: {} });
      await navigator.clipboard.writeText(out.markdown);
      BA.toast("SDLC copied as Markdown.");
    });
  }

  // ---------------------------------------------------------------- Coaching

  const FOCUS = ["want to work on", "practicing", "comfortable"];
  const FOCUS_TONES = { "want to work on": "warn", practicing: "accent", comfortable: "good" };
  const ORIGIN_TONES = { "built-in": "", mine: "good", imported: "accent" };
  const COMMS_SCREENS = [["/this-week", "Comms: This week"], ["/messages", "Comms: Messages"], ["/templates", "Comms: Templates"], ["/calendar", "Comms: Calendar"],
    ["/audiences", "Comms: Audiences"], ["/plain-language", "Comms: Plain language"], ["/decks", "Comms: Decks"], ["/media", "Comms: Media"]];
  const screenLabel = (route) => (BA.session.nav.find((n) => n.path === route) || {}).label || (COMMS_SCREENS.find(([r]) => r === route) || [, route])[1];
  const coachTabs = (active) => `<nav class="tabs">${[["", "Guides"], ["reflect", "Reflect"], ["tips", "Tips and prompts"], ["share", "Share"]]
    .map(([k, label]) => `<a href="#/coaching${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const asLines = (v) => (v || "").split("\n").map((x) => x.trim()).filter(Boolean);

  BA.view("/coaching", {
    title: "Coaching",
    async render(main, param) {
      if (param === "reflect") return renderReflect(main);
      if (param === "tips") return renderCoachTips(main);
      if (param === "share") return renderCoachShare(main);
      if (param) return renderGuide(main, param);
      const lib = await BA.api("/api/coaching/library");
      const ro = presenting();
      const f = (() => { try { return JSON.parse(sessionStorage.getItem("ba-coach-filter") || "{}"); } catch { return {}; } })();
      const q = (f.q || "").toLowerCase();
      const shown = lib.guides.filter((g) => (!f.theme || g.theme === f.theme) && (!f.focus || g.focus === f.focus) && (!q || `${g.title} ${g.summary || ""} ${g.inspired_by || ""}`.toLowerCase().includes(q)));
      const working = lib.guides.filter((g) => g.focus === "want to work on" || g.focus === "practicing");
      const card = (g) => `<a class="sys-card" href="#/coaching/${esc(g.slug)}"><div class="row"><b>${esc(g.title)}</b><span class="spacer"></span>
          ${g.status === "draft" ? '<span class="pill warn">draft</span>' : ""}${g.focus ? tonePill(g.focus, FOCUS_TONES) : ""}</div>
          ${g.summary ? `<p class="clamp">${esc(g.summary)}</p>` : ""}
          <div class="quiet">${[g.minutes ? `${g.minutes} min` : "", g.origin, g.inspired_by ? `inspired by ${g.inspired_by}` : ""].filter(Boolean).map(esc).join(" · ")}</div></a>`;
      main.innerHTML = `${coachTabs("")}
        <p class="quiet">Guides for the mindset, habits and practices of leading an engineering team, especially through a new or growing role. Every guide is yours to edit: rewrite the built-in ones, delete what doesn't fit, and add your own as you read.</p>
        ${working.length ? `<section class="card"><h2>What I'm working on</h2>${working.map((g) => `<div class="item"><a href="#/coaching/${esc(g.slug)}">${esc(g.title)}</a><span class="spacer"></span>${tonePill(g.focus, FOCUS_TONES)}</div>`).join("")}</section>` : ""}
        <div class="row"><input id="cf-q" placeholder="Search guides" value="${esc(f.q || "")}" style="max-width:260px">
          <select id="cf-theme" style="max-width:240px"><option value="">Every theme</option>${lib.themes.map((th) => `<option value="${esc(th.key)}"${th.key === f.theme ? " selected" : ""}>${esc(th.title)}</option>`).join("")}</select>
          <select id="cf-focus" style="max-width:200px"><option value="">Any focus</option>${opts(FOCUS, f.focus)}</select></div>
        ${lib.themes.map((th) => [th, shown.filter((g) => g.theme === th.key)]).filter(([, l]) => l.length).map(([th, l]) => `<section class="card"><h2>${esc(th.title)}</h2>${th.summary ? `<p class="quiet">${esc(th.summary)}</p>` : ""}<div class="sys-grid">${l.map(card).join("")}</div></section>`).join("") ||
          '<p class="empty">No guides match.</p>'}
        ${ro ? "" : `<section class="card"><h2>Write a guide</h2><form id="add-guide" class="row"><input name="title" required placeholder="Title" style="max-width:340px">
          <input name="theme" list="coach-themes" placeholder="Theme" style="max-width:200px"><datalist id="coach-themes">${lib.themes.map((th) => `<option value="${esc(th.key)}">${esc(th.title)}</option>`).join("")}</datalist>
          <input name="inspired_by" placeholder="Inspired by (book, chapter)" style="max-width:280px"><button class="btn primary" type="submit">Start writing</button></form>
          ${lib.restorable.length ? `<details><summary class="quiet">Restore a built-in guide you deleted (${lib.restorable.length})</summary>${lib.restorable.map((r) => `<div class="item"><span>${esc(r.title)}</span><span class="spacer"></span><button class="btn" data-restore="${esc(r.slug)}">Restore</button></div>`).join("")}</details>` : ""}</section>`}`;
      const save = () => { sessionStorage.setItem("ba-coach-filter", JSON.stringify({ q: main.querySelector("#cf-q").value, theme: main.querySelector("#cf-theme").value, focus: main.querySelector("#cf-focus").value })); BA.rerender(); };
      main.querySelector("#cf-theme").onchange = save;
      main.querySelector("#cf-focus").onchange = save;
      main.querySelector("#cf-q").onchange = save;
      if (ro) return;
      main.querySelector("#add-guide").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const g = await BA.api("/api/coaching-guides", { method: "POST", body: { title: fd.get("title"), theme: fd.get("theme") || "transition", inspired_by: fd.get("inspired_by") || null, status: "draft" } });
        BA.go(`/coaching/${g.slug}`);
      });
      main.querySelectorAll("[data-restore]").forEach((b) => (b.onclick = BA.guard(async () => { await BA.api(`/api/coaching/restore/${b.dataset.restore}`, { method: "POST" }); BA.rerender(); })));
    },
  });

  async function renderGuide(main, slug) {
    const d = await BA.api(`/api/coaching/guide/${encodeURIComponent(slug)}`);
    const g = d.guide;
    const ro = presenting();
    document.getElementById("view-title").textContent = g.title;
    const list = (title, items, cls = "") => (items && items.length ? `<h3>${title}</h3><ul class="checklist ${cls}">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "");
    const theme = d.themes.find((th) => th.key === g.theme);
    main.innerHTML = `<p><a href="#/coaching">All guides</a></p>
      <article class="card guide coaching-guide"><div class="row"><span class="quiet">${esc(theme ? theme.title : g.theme)}</span><span class="spacer"></span>
          ${g.status === "draft" ? '<span class="pill warn">draft</span>' : ""}${tonePill(g.origin, ORIGIN_TONES)}${g.minutes ? `<span class="quiet">${g.minutes} min</span>` : ""}</div>
        <h2>${esc(g.title)}</h2>${g.summary ? `<p class="lead">${esc(g.summary)}</p>` : ""}
        ${g.why ? `<h3>Why it matters</h3>${BA.md(g.why)}` : ""}
        ${list("What to do", g.practices)}${list("Watch out for", g.pitfalls)}${list("Ask yourself", g.questions)}
        ${g.try_this && g.try_this.length ? `<h3>Try this week</h3>${g.try_this.map((x, i) => `<div class="item"><span>${esc(x)}</span><span class="spacer"></span>${ro ? "" : `<button class="btn" data-task="${i}">Add as a task</button>`}</div>`).join("")}` : ""}
        ${g.body ? `<h3>More</h3>${BA.md(g.body)}` : ""}
        ${g.related && g.related.length ? `<p class="quiet">Where this shows up: ${g.related.map((r) => `<a href="#${esc(r)}">${esc(screenLabel(r.split("/").slice(0, 2).join("/")) || r)}</a>`).join(", ")}</p>` : ""}
        ${g.reading && g.reading.length ? `<p class="quiet">Further reading: ${esc(g.reading.join("; "))}</p>` : ""}
        ${g.inspired_by ? `<p class="quiet">Inspired by ${esc(g.inspired_by)}</p>` : ""}</article>
      ${ro ? "" : `<section class="card"><h2>For me <span class="quiet">(private)</span></h2><div class="row"><label class="check">My focus <select id="g-focus" style="max-width:200px"><option value=""></option>${opts(FOCUS, g.focus)}</select></label>
          <span class="spacer"></span><a class="btn" href="#/coaching/reflect" id="g-reflect">${BA.icon("notebook")} Reflect on this</a></div>
        <label>My notes<textarea id="g-notes" rows="4">${esc(g.my_notes || "")}</textarea></label></section>
      ${d.tips.length ? `<section class="card"><h2>Tips that point here</h2>${d.tips.map((tp) => `<div class="item"><span>${esc(tp.text)}</span><span class="spacer"></span><span class="quiet">${esc(screenLabel(tp.route))}</span></div>`).join("")}<p class="quiet"><a href="#/coaching/tips">Edit tips</a></p></section>` : ""}
      <details class="card"><summary><b>Edit this guide</b></summary><form id="edit-guide"><div class="grid2">
        <label>Title<input name="title" value="${esc(g.title)}" required></label><label>Theme<input name="theme" value="${esc(g.theme)}" list="coach-themes-e"><datalist id="coach-themes-e">${d.themes.map((th) => `<option value="${esc(th.key)}">${esc(th.title)}</option>`).join("")}</datalist></label>
        <label>Status<select name="status">${opts(["draft", "published"], g.status)}</select></label><label>Reading time (minutes)<input type="number" name="minutes" value="${esc(g.minutes ?? "")}"></label>
        <label>Inspired by <span class="quiet">(book and chapter, talk, article)</span><input name="inspired_by" value="${esc(g.inspired_by || "")}"></label>
        <label>Further reading <span class="quiet">(one per line)</span><textarea name="reading" rows="2">${esc((g.reading || []).join("\n"))}</textarea></label></div>
        <label>Summary<textarea name="summary" rows="2">${esc(g.summary || "")}</textarea></label>
        <label>Why it matters<textarea name="why" rows="3">${esc(g.why || "")}</textarea></label>
        <div class="grid2"><label>What to do <span class="quiet">(one per line)</span><textarea name="practices" rows="6">${esc((g.practices || []).join("\n"))}</textarea></label>
          <label>Watch out for <span class="quiet">(one per line)</span><textarea name="pitfalls" rows="6">${esc((g.pitfalls || []).join("\n"))}</textarea></label>
          <label>Ask yourself <span class="quiet">(one per line)</span><textarea name="questions" rows="4">${esc((g.questions || []).join("\n"))}</textarea></label>
          <label>Try this week <span class="quiet">(one per line)</span><textarea name="try_this" rows="4">${esc((g.try_this || []).join("\n"))}</textarea></label></div>
        <label>More <span class="quiet">(Markdown: anything else, such as your own reading notes)</span><textarea name="body" rows="6" class="mono">${esc(g.body || "")}</textarea></label>
        <label>Screens it relates to <span class="quiet">(one per line, such as /retros)</span><textarea name="related" rows="2">${esc((g.related || []).join("\n"))}</textarea></label>
        <div class="actions"><button class="btn danger left" type="button" id="del-guide">Delete guide</button>${BA.historyButton("coaching_guide", g.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}`;
    if (ro) return;
    main.querySelector("#g-focus").onchange = BA.guard(async (e) => { await BA.api(`/api/coaching-guides/${g.id}`, { method: "PATCH", body: { focus: e.target.value || null } }); BA.toast("Saved."); });
    main.querySelector("#g-notes").onchange = BA.guard(async (e) => { await BA.api(`/api/coaching-guides/${g.id}`, { method: "PATCH", body: { my_notes: e.target.value } }); BA.toast("Saved."); });
    main.querySelector("#g-reflect").onclick = () => sessionStorage.setItem("ba-reflect-prompt", `On "${g.title}": ${(g.questions && g.questions[0]) || "what am I taking from this?"}`);
    main.querySelectorAll("[data-task]").forEach((b) => (b.onclick = BA.guard(async () => {
      await BA.api("/api/tasks", { method: "POST", body: { title: g.try_this[Number(b.dataset.task)], requested_by: `Coaching: ${g.title}` } });
      b.disabled = true;
      b.textContent = "Added";
    })));
    const form = main.querySelector("#edit-guide");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      await BA.api(`/api/coaching-guides/${g.id}`, { method: "PATCH", body: { title: fd.get("title"), theme: fd.get("theme") || "transition", status: fd.get("status"), minutes: numOrNull(fd.get("minutes")),
        inspired_by: fd.get("inspired_by") || null, reading: asLines(fd.get("reading")), summary: fd.get("summary"), why: fd.get("why"), practices: asLines(fd.get("practices")), pitfalls: asLines(fd.get("pitfalls")),
        questions: asLines(fd.get("questions")), try_this: asLines(fd.get("try_this")), body: fd.get("body"), related: asLines(fd.get("related")) } });
      BA.coachTips = null;
      BA.rerender();
    });
    main.querySelector("#del-guide").onclick = BA.guard(async () => {
      if (!confirm(g.origin === "built-in" ? "Delete this guide? You can restore the original later from the guides page." : "Delete this guide? This can't be undone.")) return;
      await BA.api(`/api/coaching-guides/${g.id}`, { method: "DELETE" });
      BA.coachTips = null;
      BA.go("/coaching");
    });
  }

  async function renderReflect(main) {
    const d = await BA.api("/api/coaching/reflect");
    if (d.hidden) { main.innerHTML = `${coachTabs("reflect")}<p class="empty">Reflections are private, so they're hidden while presenting.</p>`; return; }
    const pre = sessionStorage.getItem("ba-reflect-prompt") || "";
    sessionStorage.removeItem("ba-reflect-prompt");
    const scale = (name) => `<select name="${name}" style="max-width:90px"><option value=""></option>${[1, 2, 3, 4, 5].map((n) => `<option>${n}</option>`).join("")}</select>`;
    const W = 320, H = 70, pts = d.trend.filter((x) => x.energy || x.confidence);
    const line = (key) => pts.map((x, i) => (x[key] ? `${(i * W) / Math.max(1, pts.length - 1)},${H - ((x[key] - 1) / 4) * (H - 10) - 5}` : null)).filter(Boolean).join(" ");
    const chart = pts.length > 1 ? `<svg class="trend" viewBox="0 0 ${W} ${H}" role="img" aria-label="Energy and confidence over recent reflections"><polyline points="${line("energy")}" class="t-energy"></polyline><polyline points="${line("confidence")}" class="t-confidence"></polyline></svg>
      <p class="quiet legend"><span class="key solid"></span> energy <span class="key dashed"></span> confidence, from 1 to 5, last ${pts.length} entries</p>` : "";
    main.innerHTML = `${coachTabs("reflect")}
      <section class="card"><h2>${d.day ? `Day ${d.day}` : "Reflect"} <span class="quiet">${esc(d.phase)}</span></h2>
        <p class="quiet">A few minutes a week on how it's going: what you're learning, where you were assertive, what's draining you. Private, never exported.${d.day ? "" : ' Set your start date in <a href="#/me">My development</a> to get prompts for each stage of the role.'}</p>
        <div class="prompt-chips">${[...d.prompts, ...d.anytime].map((p) => `<button type="button" class="chip-btn" data-prompt="${esc(p.text)}">${esc(p.text)}</button>`).join("")}</div>
        <form id="add-reflection"><label>Prompt<input name="prompt" value="${esc(pre)}" placeholder="Pick one above or write your own"></label>
          <label>Reflection<textarea name="entry" rows="6" required></textarea></label>
          <div class="row"><label class="check">Energy ${scale("energy")}</label><label class="check">Confidence ${scale("confidence")}</label>
            <input type="date" name="date" value="${BA.today()}" style="max-width:170px"><input name="tags" placeholder="Tags, comma separated" style="max-width:220px"><span class="spacer"></span><button class="btn primary" type="submit">Save</button></div></form></section>
      <div class="cards">${chart ? `<section class="card"><h2>How I've been</h2>${chart}</section>` : ""}
        ${d.focus.length ? `<section class="card"><h2>Guides I'm working on</h2>${d.focus.map((x) => `<div class="item"><a href="#/coaching/${esc(x.slug)}">${esc(x.title)}</a><span class="spacer"></span>${tonePill(x.focus, FOCUS_TONES)}</div>`).join("")}</section>` : ""}</div>
      <section class="card"><h2>Past reflections</h2>${d.entries.map((e) => `<details class="plan-item" data-r="${e.id}"><summary><span class="quiet">${BA.fmtDate(e.date)}</span><span>${esc(e.prompt || (e.entry || "").slice(0, 80))}</span><span class="spacer"></span>
          ${e.energy ? `<span class="quiet">energy ${e.energy}</span>` : ""}${e.confidence ? `<span class="quiet">confidence ${e.confidence}</span>` : ""}${(e.tags || []).length ? BA.chips(e.tags) : ""}</summary>${BA.md(e.entry || "")}
          <div class="actions"><button class="btn danger" type="button" data-del>Delete</button></div></details>`).join("") || '<p class="quiet">Nothing yet.</p>'}</section>`;
    const form = main.querySelector("#add-reflection");
    main.querySelectorAll("[data-prompt]").forEach((b) => (b.onclick = () => { form.elements.prompt.value = b.dataset.prompt; form.elements.entry.focus(); }));
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      await BA.api("/api/reflections", { method: "POST", body: { date: fd.get("date"), prompt: fd.get("prompt") || null, entry: fd.get("entry"), energy: numOrNull(fd.get("energy")), confidence: numOrNull(fd.get("confidence")), tags: asLines((fd.get("tags") || "").replace(/,/g, "\n")) } });
      BA.toast("Saved.");
      BA.rerender();
    });
    main.querySelectorAll("[data-r]").forEach((det) => (det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this reflection?")) return; await BA.api(`/api/reflections/${det.dataset.r}`, { method: "DELETE" }); BA.rerender(); })));
  }

  async function renderCoachTips(main) {
    const [tips, prompts, lib, reflect] = await Promise.all([BA.api("/api/coaching-tips"), BA.api("/api/coaching-prompts"), BA.api("/api/coaching/library"), BA.api("/api/coaching/reflect")]);
    const ro = presenting();
    const screens = [...BA.session.nav.filter((n) => n.path && n.path !== "/settings" && n.path !== "/coaching").map((n) => [n.path, n.label]), ...COMMS_SCREENS];
    const guideOpts = (sel) => `<option value="">No guide</option>${lib.guides.map((g) => `<option value="${esc(g.slug)}"${g.slug === sel ? " selected" : ""}>${esc(g.title)}</option>`).join("")}`;
    const byRoute = screens.map(([r, label]) => [r, label, tips.filter((t) => t.route === r)]);
    const phases = reflect.phases || ["Any time"];
    main.innerHTML = `${coachTabs("tips")}
      <p class="quiet">Tips appear at the top of each screen, one at a time, linking to a guide. Prompts feed the reflection journal at each stage of the role.</p>
      <section class="card"><h2>Tips by screen</h2>${byRoute.map(([r, label, list]) => `<details class="plan-item"${list.length ? "" : ' data-empty="1"'}><summary><b>${esc(label)}</b><span class="spacer"></span><span class="quiet">${list.length} tip${list.length === 1 ? "" : "s"}</span></summary>
          ${list.map((t) => `<form class="tip-row row" data-tip="${t.id}"><input name="text" value="${esc(t.text)}" style="flex:1;min-width:220px"${ro ? " disabled" : ""}><select name="guide_slug" style="max-width:240px"${ro ? " disabled" : ""}>${guideOpts(t.guide_slug)}</select>
            <label class="check"><input type="checkbox" name="active"${t.active ? " checked" : ""}${ro ? " disabled" : ""}> on</label>${ro ? "" : '<button class="btn" type="submit">Save</button><button class="icon-btn" type="button" title="Delete" data-del>' + BA.icon("x") + "</button>"}</form>`).join("")}
          ${ro ? "" : `<form class="add-tip row" data-route="${esc(r)}"><input name="text" required placeholder="A new tip for this screen" style="flex:1;min-width:220px"><select name="guide_slug" style="max-width:240px">${guideOpts("")}</select><button class="btn" type="submit">Add</button></form>`}</details>`).join("")}</section>
      <section class="card"><h2>Reflection prompts</h2>${phases.map((ph) => `<h3>${esc(ph)}</h3>${prompts.filter((p) => p.phase === ph).map((p) => `<form class="row" data-prompt="${p.id}"><input name="text" value="${esc(p.text)}" style="flex:1;min-width:220px"${ro ? " disabled" : ""}>
          <label class="check"><input type="checkbox" name="active"${p.active ? " checked" : ""}${ro ? " disabled" : ""}> on</label>${ro ? "" : '<button class="btn" type="submit">Save</button><button class="icon-btn" type="button" title="Delete" data-del>' + BA.icon("x") + "</button>"}</form>`).join("")}
        ${ro ? "" : `<form class="add-prompt row" data-phase="${esc(ph)}"><input name="text" required placeholder="A new prompt" style="flex:1;min-width:220px"><button class="btn" type="submit">Add</button></form>`}`).join("")}</section>`;
    if (ro) return;
    const done = () => { BA.coachTips = null; BA.rerender(); };
    main.querySelectorAll("[data-tip]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/coaching-tips/${f.dataset.tip}`, { method: "PATCH", body: { text: f.elements.text.value, guide_slug: f.elements.guide_slug.value || null, active: f.elements.active.checked } }); BA.coachTips = null; BA.toast("Saved."); });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { await BA.api(`/api/coaching-tips/${f.dataset.tip}`, { method: "DELETE" }); done(); });
    });
    main.querySelectorAll(".add-tip").forEach((f) => (f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/coaching-tips", { method: "POST", body: { route: f.dataset.route, text: f.elements.text.value, guide_slug: f.elements.guide_slug.value || null } }); done(); })));
    main.querySelectorAll("[data-prompt]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/coaching-prompts/${f.dataset.prompt}`, { method: "PATCH", body: { text: f.elements.text.value, active: f.elements.active.checked } }); BA.toast("Saved."); });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { await BA.api(`/api/coaching-prompts/${f.dataset.prompt}`, { method: "DELETE" }); done(); });
    });
    main.querySelectorAll(".add-prompt").forEach((f) => (f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/coaching-prompts", { method: "POST", body: { phase: f.dataset.phase, text: f.elements.text.value } }); done(); })));
  }

  async function renderCoachShare(main) {
    const ro = presenting();
    main.innerHTML = `${coachTabs("share")}
      <section class="card"><h2>Share your coaching with other leaders</h2>
        <p class="quiet">A coaching pack holds your published guides, tips and reflection prompts. It never includes your notes, focus or reflections. Another leader can import it into their own copy.</p>
        ${ro ? "" : `<div class="row"><button class="btn primary" id="pack-download">Download pack</button><button class="btn" id="pack-copy">${BA.icon("copy")} Copy pack</button></div>`}</section>
      ${ro ? "" : `<section class="card"><h2>Import a pack</h2><p class="quiet">New guides, tips and prompts are added. A guide you already have (same short name) is skipped, unless you choose to replace it; your notes on it are kept either way.</p>
        <form id="pack-import"><label>Pack file<input type="file" name="file" accept=".json,application/json"></label><label>Or paste it<textarea name="text" rows="5" class="mono"></textarea></label>
          <label class="check"><input type="checkbox" name="replace"> Replace guides I already have</label><div class="actions"><button class="btn primary" type="submit">Import</button></div></form><div id="pack-result"></div></section>`}`;
    if (ro) return;
    const getPack = () => BA.api("/api/coaching/pack/export", { method: "POST", body: {} });
    main.querySelector("#pack-download").onclick = BA.guard(async () => {
      const pack = await getPack();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(pack, null, 2)], { type: "application/json" }));
      a.download = `coaching-pack-${pack.exported}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
    main.querySelector("#pack-copy").onclick = BA.guard(async () => { await navigator.clipboard.writeText(JSON.stringify(await getPack(), null, 2)); BA.toast("Pack copied."); });
    const form = main.querySelector("#pack-import");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const file = form.elements.file.files[0];
      const raw = file ? await file.text() : form.elements.text.value;
      let pack;
      try { pack = JSON.parse(raw); } catch { throw new Error("That isn't valid JSON."); }
      const r = await BA.api("/api/coaching/pack/import", { method: "POST", body: { pack, replace: form.elements.replace.checked } });
      BA.coachTips = null;
      main.querySelector("#pack-result").innerHTML = `<p><span class="pill good">imported</span> ${r.guides_added} guides added, ${r.guides_replaced} replaced, ${r.guides_skipped} skipped; ${r.tips_added} tips and ${r.prompts_added} prompts added.</p>`;
    });
  }

  // ---------------------------------------------------------------- Technical debt

  const DEBT_CATS = ["maintainability", "stability", "performance", "cleanup", "revenue and conversion", "observability", "security", "delivery speed", "cost"];
  const DEBT_STATUS = ["identified", "accepted", "planned", "in progress", "done", "won't fix"];
  const DEBT_DECISIONS = ["fix now", "schedule", "accept for now", "won't fix"];
  const QUAD_TONES = { "quick win": "good", "big bet": "accent", "fill-in": "", "money pit": "bad", "not scored": "warn" };
  const debtTabs = (active) => `<nav class="tabs">${[["", "Register"], ["matrix", "Value and effort"], ["summary", "Leadership summary"], ["policy", "Policy"]]
    .map(([k, label]) => `<a href="#/debt${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const cap = (s) => s[0].toUpperCase() + s.slice(1);

  BA.view("/debt", {
    title: "Tech debt",
    async render(main, param) {
      const d = await BA.api("/api/debt/overview");
      if (param === "matrix") return renderDebtMatrix(main, d);
      if (param === "summary") return renderDebtSummary(main, d);
      if (param === "policy") return renderDebtPolicy(main, d);
      const [systems, people, sprints] = await Promise.all([BA.api("/api/systems"), BA.api("/api/people"), BA.api("/api/sprints")]);
      const ro = presenting();
      keepTeam(d.items);
      const f = (() => { try { return JSON.parse(sessionStorage.getItem("ba-debt-filter") || "{}"); } catch { return {}; } })();
      const shown = d.items.filter((i) => (!f.cat || (i.categories || []).includes(f.cat)) && (!f.quad || i.quadrant === f.quad) && (f.closed || !["done", "won't fix"].includes(i.status)))
        .sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
      const scale = (name, v) => `<select name="${name}"><option value=""></option>${[1, 2, 3, 4, 5].map((n) => `<option${n === v ? " selected" : ""}>${n}</option>`).join("")}</select>`;
      const fields = (i = {}) => `<div class="grid2"><label>Title<input name="title" value="${esc(i.title || "")}" required></label>
          <label>Status<select name="status">${opts(DEBT_STATUS, i.status || "identified")}</select></label>
          <label>Impact if fixed <span class="quiet">(1 to 5)</span>${scale("impact", i.impact)}</label><label>Risk if left <span class="quiet">(1 to 5)</span>${scale("risk", i.risk)}</label>
          <label>Effort<select name="effort"><option value=""></option>${opts(["S", "M", "L", "XL"], i.effort)}</select></label><label>Points<input type="number" name="points" value="${esc(i.points ?? "")}"></label>
          <label>Needed by <span class="quiet">(a date that forces it)</span><input type="date" name="trigger_date" value="${esc(i.trigger_date || "")}"></label><label>Because<input name="trigger_reason" value="${esc(i.trigger_reason || "")}" placeholder="Such as: platform release, peak season, end of support"></label>
          <label>Sprint<select name="sprint_id"><option value=""></option>${sprints.map((s) => `<option value="${s.id}"${s.id === i.sprint_id ? " selected" : ""}>Sprint ${s.number}</option>`).join("")}</select></label>
          <label>Owner<select name="owner_id">${personOptions(people, i.owner_id)}</select></label><label>Jira key<input name="ticket_key" value="${esc(i.ticket_key || "")}" placeholder="ABC-123"></label>
          <label>Raised by<input name="raised_by" value="${esc(i.raised_by || "")}"></label></div>
        <label>Categories <span class="quiet">(what fixing it buys; pick all that apply)</span></label><div class="row">${DEBT_CATS.map((c) => `<label class="check" title="${esc((d.categories.find((x) => x.key === c) || {}).help || "")}"><input type="checkbox" name="categories" value="${c}"${(i.categories || []).includes(c) ? " checked" : ""}> ${c}</label>`).join("")}</div>
        <label>What it is<textarea name="description" rows="2">${esc(i.description || "")}</textarea></label>
        <label>What leaving it costs <span class="quiet">(in business terms: incidents, hours, slower releases, lost sales)</span><textarea name="cost_of_delay" rows="2">${esc(i.cost_of_delay || "")}</textarea></label>
        <label>Evidence <span class="quiet">(incidents, metrics, tickets)</span><textarea name="evidence" rows="2">${esc(i.evidence || "")}</textarea></label>
        <label>Systems</label><div class="case-picks">${systems.map((s) => `<label class="check"><input type="checkbox" name="system_ids" value="${s.id}"${(i.system_ids || []).includes(s.id) ? " checked" : ""}> ${esc(s.name)}</label>`).join("") || '<span class="quiet">Add systems under Architecture to link them.</span>'}</div>
        <label>Private notes<textarea name="notes" rows="2">${esc(i.notes || "")}</textarea></label>`;
      const read = (form) => { const fd = new FormData(form); return { title: fd.get("title"), status: fd.get("status"), impact: numOrNull(fd.get("impact")), risk: numOrNull(fd.get("risk")), effort: fd.get("effort") || null,
        points: numOrNull(fd.get("points")), trigger_date: fd.get("trigger_date") || null, trigger_reason: fd.get("trigger_reason"), sprint_id: numOrNull(fd.get("sprint_id")), owner_id: numOrNull(fd.get("owner_id")),
        ticket_key: fd.get("ticket_key"), raised_by: fd.get("raised_by"), categories: fd.getAll("categories"), description: fd.get("description"), cost_of_delay: fd.get("cost_of_delay"), evidence: fd.get("evidence"),
        system_ids: fd.getAll("system_ids").map(Number), notes: fd.get("notes") }; };
      const item = (i) => `<details class="plan-item${["done", "won't fix"].includes(i.status) ? " dropped" : ""}" data-debt="${i.id}"><summary><b>${esc(i.title)}</b><span class="spacer"></span>
          ${BA.issueKeys(i.ticket_key)}${BA.chips(i.categories)}${tonePill(i.quadrant, QUAD_TONES)}${i.value ? `<span class="quiet">value ${i.value} · ${esc(i.effort)}</span>` : ""}${i.trigger_date ? `<span class="pill warn">by ${BA.fmtDate(i.trigger_date)}</span>` : ""}${BA.statusPill(i.status)}</summary>
          ${i.description ? BA.md(i.description) : ""}${i.cost_of_delay ? `<p><b>Cost of leaving it:</b> ${esc(i.cost_of_delay)}</p>` : ""}
          <p class="quiet">${[i.systems.length ? `Systems: ${i.systems.map(esc).join(", ")}` : "", i.owner_name ? `Owner: ${esc(i.owner_name)}` : "", i.sprint_number ? `Sprint ${i.sprint_number}` : "", i.points ? `${i.points} points` : "",
            i.revisit_on ? `Revisit ${BA.fmtDate(i.revisit_on)}` : ""].filter(Boolean).join(" · ")} ${BA.keysEditor(`/api/tech-debt/${i.id}`, i.ticket_key, "ticket_key")}</p>
          <div class="decisions" data-decisions="${i.id}"></div>
          ${ro ? "" : `<form class="decide row"><select name="decision" style="max-width:160px">${opts(DEBT_DECISIONS, "schedule")}</select><input name="decided_by" placeholder="Decided by" style="max-width:180px">
            <input type="date" name="revisit_on" title="Revisit on (needed when accepting)" style="max-width:160px"><input name="rationale" placeholder="Why" style="flex:1;min-width:200px"><button class="btn" type="submit">Record decision</button></form>
            <div class="row"><button class="btn" type="button" data-to-backlog>${BA.icon("list-ordered")} Add to the sprint backlog</button></div>
            <details><summary class="quiet">Edit</summary><form class="edit-debt">${fields(i)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("tech_debt", i.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}</details>`;
      main.innerHTML = `${debtTabs("")}
        <div class="stats">${d.categories.filter((c) => c.open).map((c) => `<section class="card stat" title="${esc(c.help)}"><div class="stat-n">${c.open}</div><div class="quiet">${esc(cap(c.key))}${c.points ? ` · ${c.points} pts` : ""}</div></section>`).join("") ||
          '<section class="card stat"><div class="stat-n">0</div><div class="quiet">open items</div></section>'}</div>
        ${d.capacity && d.policy.allocation != null ? `<p class="quiet">Sprint ${d.capacity.sprint_number}: ${d.capacity.planned_points} points of debt planned${d.capacity.capacity ? ` of ${d.capacity.capacity} (${d.capacity.share}%), against an agreed ${d.policy.allocation}%` : ""}. <a href="#/debt/policy">Policy</a></p>` : ""}
        <div class="row"><select id="df-cat" style="max-width:220px"><option value="">Every category</option>${DEBT_CATS.map((c) => `<option value="${c}"${c === f.cat ? " selected" : ""}>${cap(c)}</option>`).join("")}</select>
          <select id="df-quad" style="max-width:180px"><option value="">Any quadrant</option>${opts(["quick win", "big bet", "fill-in", "money pit", "not scored"], f.quad)}</select>
          <label class="check"><input type="checkbox" id="df-closed"${f.closed ? " checked" : ""}> Show done and won't fix</label><span class="spacer"></span><span class="quiet">Sorted by value for the effort</span></div>
        <section class="card">${shown.map(item).join("") || '<p class="quiet">No debt logged yet, or none matches.</p>'}</section>
        ${ro ? "" : `<form id="add-debt" class="card"><h2>Log technical debt</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form>`}`;
      const saveF = () => { sessionStorage.setItem("ba-debt-filter", JSON.stringify({ cat: main.querySelector("#df-cat").value, quad: main.querySelector("#df-quad").value, closed: main.querySelector("#df-closed").checked })); BA.rerender(); };
      ["#df-cat", "#df-quad", "#df-closed"].forEach((s) => (main.querySelector(s).onchange = saveF));
      main.querySelectorAll("[data-debt]").forEach((det) => det.addEventListener("toggle", async () => {
        const box = det.querySelector("[data-decisions]");
        if (!det.open || box.dataset.loaded) return;
        const ds = await BA.api(`/api/tech-debt/${det.dataset.debt}/decisions`);
        box.dataset.loaded = "1";
        box.innerHTML = ds.length ? `<h4>Decisions</h4>${ds.map((x) => `<div class="item"><span class="pill">${esc(x.decision)}</span><span>${esc(x.rationale || "")}</span><span class="spacer"></span><span class="quiet">${[x.decided_by, BA.fmtDate(x.date), x.revisit_on ? "revisit " + BA.fmtDate(x.revisit_on) : ""].filter(Boolean).map(esc).join(" · ")}</span></div>`).join("")}` : "";
      }));
      if (ro) return;
      const add = main.querySelector("#add-debt");
      add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/tech-debt", { method: "POST", body: { ...read(add), identified_on: BA.today(), team_id: newTeamId() } }); BA.rerender(); });
      main.querySelectorAll("[data-debt]").forEach((det) => {
        const id = det.dataset.debt;
        const dec = det.querySelector("form.decide");
        dec.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const fd = new FormData(dec);
          await BA.api(`/api/tech-debt/${id}/decide`, { method: "POST", body: { decision: fd.get("decision"), decided_by: fd.get("decided_by"), revisit_on: fd.get("revisit_on") || null, rationale: fd.get("rationale") } });
          BA.toast("Decision recorded.");
          BA.rerender();
        });
        const form = det.querySelector("form.edit-debt");
        form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/tech-debt/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
        det.querySelector("[data-to-backlog]").onclick = BA.guard(async () => { await BA.api(`/api/tech-debt/${id}/to-backlog`, { method: "POST" }); BA.toast("Added to the sprint backlog for refinement."); });
        det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this debt item and its decisions? Marking it won't fix keeps the record.")) return; await BA.api(`/api/tech-debt/${id}`, { method: "DELETE" }); BA.rerender(); });
      });
    },
  });

  function renderDebtMatrix(main, d) {
    const items = d.items.filter((i) => i.value && !["done", "won't fix"].includes(i.status));
    const W = 640, H = 400, L = 56, B = 40, T = 16, R = 16;
    const xs = { S: 0, M: 1, L: 2, XL: 3 };
    const x = (e) => L + ((xs[e] + 0.5) * (W - L - R)) / 4;
    const y = (v) => T + ((10 - v) * (H - T - B)) / 8;
    const seen = {};
    const dots = items.map((i) => {
      const k = `${i.effort}-${i.value}`;
      const n = (seen[k] = (seen[k] || 0) + 1) - 1;
      const cx = x(i.effort) + ((n % 3) - 1) * 16, cy = y(i.value) + Math.floor(n / 3) * 16;
      return `<g class="dot q-${i.quadrant.replace(" ", "-")}"><circle cx="${cx}" cy="${cy}" r="7"></circle><title>${esc(i.title)}: value ${i.value}, effort ${i.effort}, ${i.quadrant}</title></g>`;
    }).join("");
    const midX = L + (W - L - R) / 2, midY = y(6.5);
    const label = (tx, ty, text, anchor) => `<text x="${tx}" y="${ty}" class="q-label" text-anchor="${anchor}">${text}</text>`;
    main.innerHTML = `${debtTabs("matrix")}
      <section class="card"><h2>Value against effort</h2><p class="quiet">Value is impact if fixed plus risk if left (2 to 10). Hover a dot for the item. Quick wins first; big bets need a plan and a sponsor; money pits need a very good reason.</p>
        ${items.length ? `<div class="map-scroll"><svg class="debt-matrix" viewBox="0 0 ${W} ${H}" role="img" aria-label="Technical debt by value and effort">
          <rect x="${L}" y="${T}" width="${midX - L}" height="${midY - T}" class="quad qw"></rect><rect x="${midX}" y="${T}" width="${W - R - midX}" height="${midY - T}" class="quad bb"></rect>
          <rect x="${L}" y="${midY}" width="${midX - L}" height="${H - B - midY}" class="quad fi"></rect><rect x="${midX}" y="${midY}" width="${W - R - midX}" height="${H - B - midY}" class="quad mp"></rect>
          ${label(L + 8, T + 16, "QUICK WINS", "start")}${label(W - R - 8, T + 16, "BIG BETS", "end")}${label(L + 8, H - B - 8, "FILL-INS", "start")}${label(W - R - 8, H - B - 8, "MONEY PITS", "end")}
          ${["S", "M", "L", "XL"].map((e) => `<text x="${x(e)}" y="${H - B + 22}" class="axis" text-anchor="middle">${e}</text>`).join("")}
          ${[2, 4, 6, 8, 10].map((v) => `<text x="${L - 10}" y="${y(v) + 4}" class="axis" text-anchor="end">${v}</text>`).join("")}
          <text x="${(L + W - R) / 2}" y="${H - 4}" class="axis-title" text-anchor="middle">Effort</text><text x="14" y="${(T + H - B) / 2}" class="axis-title" text-anchor="middle" transform="rotate(-90 14 ${(T + H - B) / 2})">Value</text>
          ${dots}</svg></div>` : '<p class="quiet">Score items with impact, risk and effort to see them here.</p>'}</section>
      <div class="stats">${["quick win", "big bet", "fill-in", "money pit", "not scored"].map((q) => `<section class="card stat"><div class="stat-n">${d.quadrants[q]}</div><div class="quiet">${q}${q === "not scored" ? "" : "s"}</div></section>`).join("")}</div>`;
  }

  async function renderDebtSummary(main, d) {
    const s = await BA.api("/api/debt/summary");
    main.innerHTML = `${debtTabs("summary")}
      <section class="card"><div class="row"><h2>For leadership and stakeholders</h2><span class="spacer"></span>${presenting() ? "" : `<button class="btn primary" id="copy-debt">${BA.icon("copy")} Copy as Markdown</button>`}</div>
        <p class="quiet">Built only from shareable fields: what's open by category, the highest value for the effort, what's been accepted and when it will be revisited, and the capacity policy.</p>
        <div class="msg-preview">${BA.md(s.markdown)}</div></section>`;
    const c = main.querySelector("#copy-debt");
    if (c) c.onclick = BA.guard(async () => { const out = await BA.api("/api/debt/summary/export", { method: "POST", body: {} }); await navigator.clipboard.writeText(out.markdown); BA.toast("Summary copied."); });
  }

  function renderDebtPolicy(main, d) {
    const p = d.policy;
    const ro = presenting();
    main.innerHTML = `${debtTabs("policy")}
      <section class="card"><h2>Capacity for debt</h2><p class="quiet">Agree a standing share of each sprint for technical debt with your manager and product. Then the conversation is about which items, not whether to do any.</p>
        ${ro ? `<p>${p.allocation != null ? `${p.allocation}% of each sprint${p.agreed_with ? `, agreed with ${esc(p.agreed_with)}` : ""}${p.agreed_on ? ` on ${BA.fmtDate(p.agreed_on)}` : ""}.` : "Not agreed yet."}</p>${p.approach ? BA.md(p.approach) : ""}`
          : `<form id="debt-policy"><div class="grid2"><label>Share of each sprint (%)<input type="number" min="0" max="100" name="allocation" value="${esc(p.allocation ?? "")}"></label>
            <label>Agreed with<input name="agreed_with" value="${esc(p.agreed_with || "")}"></label><label>Agreed on<input type="date" name="agreed_on" value="${esc(p.agreed_on || "")}"></label></div>
            <label>How we decide <span class="quiet">(Markdown: when debt jumps the queue, who decides, how often we review)</span><textarea name="approach" rows="5">${esc(p.approach || "")}</textarea></label>
            <div class="actions"><button class="btn primary" type="submit">Save</button></div></form>`}
        ${d.capacity ? `<p class="quiet">This sprint (${d.capacity.sprint_number}): ${d.capacity.planned_points} points of debt planned${d.capacity.capacity ? ` of ${d.capacity.capacity}` : ""}${d.capacity.target_points != null ? `, target ${d.capacity.target_points}` : ""}. Set sprint capacity in PI planning or the sprint notebook.</p>` : ""}</section>
      <section class="card"><h2>Categories</h2><p class="quiet">Classify each item by what fixing it buys. An item can sit in more than one.</p>
        ${d.categories.map((c) => `<div class="item"><b>${esc(cap(c.key))}</b><span>${esc(c.help)}</span></div>`).join("")}</section>
      <section class="card"><h2>How items are scored</h2><ul class="checklist"><li><b>Impact if fixed</b>, 1 to 5: how much better things get.</li><li><b>Risk if left</b>, 1 to 5: how likely and how bad the harm is if nothing changes.</li>
        <li><b>Value</b> is the two added together, 2 to 10. <b>Effort</b> is S, M, L or XL.</li><li>Value of 7 or more with effort S or M is a <b>quick win</b>; with L or XL a <b>big bet</b>. Lower value with S or M is a <b>fill-in</b>; with L or XL a <b>money pit</b>.</li></ul>
        <p class="quiet">The score starts a conversation; it doesn't end one. A date that forces the issue, such as a platform release or peak season, can move anything up.</p></section>`;
    const form = main.querySelector("#debt-policy");
    if (form) form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(form); await BA.api("/api/debt/policy", { method: "PUT", body: { allocation: fd.get("allocation") === "" ? null : Number(fd.get("allocation")), agreed_with: fd.get("agreed_with"), agreed_on: fd.get("agreed_on") || null, approach: fd.get("approach") } }); BA.toast("Saved."); BA.rerender(); });
  }

  // ---------------------------------------------------------------- Find a Jira key

  BA.view("/jira", {
    title: "Find a Jira key",
    async render(main, param) {
      const key = (param || "").toUpperCase();
      main.innerHTML = `<section class="card"><form id="jira-find" class="row"><input name="key" value="${esc(key)}" placeholder="ABC-123" required style="max-width:220px"><button class="btn primary" type="submit">${BA.icon("search")} Find</button>
          <span class="quiet">Everything in the toolkit that mentions this key.${BA.jiraUrl ? "" : ' Set your Jira address in <a href="#/me">My development</a> to turn keys into links.'}</span></form></section><div id="jira-results"></div>`;
      main.querySelector("#jira-find").onsubmit = (e) => { e.preventDefault(); BA.go(`/jira/${new FormData(e.target).get("key").trim().toUpperCase()}`); };
      if (!key) return;
      const r = await BA.api(`/api/jira/${encodeURIComponent(key)}`);
      document.getElementById("view-title").textContent = key;
      main.querySelector("#jira-results").innerHTML = `<section class="card"><h2>${BA.issueKeys([r.key])} <span class="quiet">${r.found.length} mention${r.found.length === 1 ? "" : "s"}</span></h2>${
        r.found.map((f) => `<div class="item"><span class="pill">${esc(f.kind)}</span><a href="#${esc(f.route)}">${esc(f.title)}</a></div>`).join("") || '<p class="quiet">Nothing in the toolkit mentions this key yet.</p>'}</section>`;
    },
  });

  // ---------------------------------------------------------------- Sprint planning

  const BACKLOG_TYPES = ["story", "bug", "task", "spike", "tech debt"];
  const BACKLOG_TONES = { "needs refinement": "warn", ready: "good", "in sprint": "accent", done: "good", removed: "" };
  const planTabs = (active) => `<nav class="tabs">${[["", "Backlog"], ["plan", "Plan a sprint"], ["ready", "Definition of ready"]]
    .map(([k, label]) => `<a href="#/planning${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${label}</a>`).join("")}</nav>`;
  const readiness = (i) => (i.ready_total ? `<span class="pill ${i.ready_met === i.ready_total ? "good" : "warn"}" title="Definition of ready">${i.ready_met}/${i.ready_total} ready</span>` : "");
  const spreadPill = (s) => (!s ? "" : s.discuss ? `<span class="pill bad" title="Votes ${s.votes.map((v) => v.points).join(", ")}">spread ${s.low} to ${s.high}: talk it through</span>` : `<span class="pill" title="Votes ${s.votes.map((v) => v.points).join(", ")}">votes ${s.low}${s.high !== s.low ? "–" + s.high : ""}</span>`);
  const ptsLabel = (i) => (i.points != null ? `<b class="pts">${i.points}</b>` : '<span class="pill warn">not estimated</span>');

  BA.view("/planning", {
    title: "Sprint planning",
    async render(main, param) {
      if (param === "ready") return renderDor(main);
      if (param === "plan" || /^\d+$/.test(param || "")) return renderPlan(main, param === "plan" ? null : Number(param));
      const [d, people, pis] = await Promise.all([BA.api("/api/backlog"), BA.api("/api/people"), BA.api("/api/program-increments")]);
      const team = people.filter((p) => p.active && ["employee", "contractor"].includes(p.relationship));
      const ro = presenting();
      keepTeam(d.items);
      const filter = sessionStorage.getItem("ba-backlog-filter") || "";
      const items = d.items.filter((i) => !filter || i.status === filter);
      const item = (i, idx) => `<details class="plan-item backlog-item" data-item="${i.id}"><summary>
          ${ro ? "" : `<span class="rank-btns"><button class="icon-btn" type="button" title="Move up" data-move="-1"${idx === 0 ? " disabled" : ""}>${BA.icon("arrow-up")}</button><button class="icon-btn" type="button" title="Move down" data-move="1"${idx === items.length - 1 ? " disabled" : ""}>${BA.icon("arrow-down")}</button></span>`}
          ${BA.keysEditor(`/api/backlog-items/${i.id}`, i.jira_key, "jira_key")}<b>${esc(i.title)}</b><span class="spacer"></span>
          ${i.item_type !== "story" ? `<span class="pill">${esc(i.item_type)}</span>` : ""}${i.carried_from_number ? `<span class="pill warn">carried from sprint ${i.carried_from_number}</span>` : ""}
          ${readiness(i)}${spreadPill(i.spread)}${ptsLabel(i)}${tonePill(i.status, BACKLOG_TONES)}</summary>
        <div class="grid2 backlog-detail">
          <div>${i.description ? `<h4>Story</h4>${BA.md(i.description)}` : ""}${i.acceptance ? `<h4>Acceptance criteria</h4>${BA.md(i.acceptance)}` : ""}
            ${i.technical_notes ? `<h4>Technical notes</h4>${BA.md(i.technical_notes)}` : ""}${i.dependencies ? `<h4>Dependencies</h4><p>${esc(i.dependencies)}</p>` : ""}
            ${[i.feature_title ? `Feature: ${esc(i.feature_title)}` : "", i.debt_title ? `From tech debt: <a href="#/debt">${esc(i.debt_title)}</a>` : "", i.owner_name ? `Owner: ${esc(i.owner_name)}` : ""].filter(Boolean).map((x) => `<p class="quiet">${x}</p>`).join("")}</div>
          <div>${d.definition_of_ready.length ? `<h4>Definition of ready</h4>${d.definition_of_ready.map((c) => `<label class="check"><input type="checkbox" data-check="${esc(c)}"${(i.ready_checks || []).includes(c) ? " checked" : ""}${ro ? " disabled" : ""}> ${esc(c)}</label>`).join("<br>")}` : '<p class="quiet">Agree a <a href="#/planning/ready">definition of ready</a> to check stories against.</p>'}
            ${ro ? "" : `<h4>Estimate together</h4><form class="votes">${team.map((p) => `<label class="vote">${esc(p.name)}<select name="v-${p.id}"><option value=""></option>${[0, 1, 2, 3, 5, 8, 13, 21].map((n) => `<option>${n}</option>`).join("")}</select></label>`).join("") || '<span class="quiet">Add team members under People to vote.</span>'}
              <button class="btn" type="submit">Record votes</button></form>`}</div></div>
        ${ro ? "" : `<div class="row"><select name="status" data-field="status" style="max-width:170px">${opts(["needs refinement", "ready", "removed"], i.status)}</select>
          <label class="check">Points <input type="number" min="0" data-field="points" value="${esc(i.points ?? "")}" style="max-width:80px"></label>
          <label class="check">Confidence <select data-field="confidence" style="max-width:110px"><option value=""></option>${opts(["low", "medium", "high"], i.confidence)}</select></label></div>
        <details><summary class="quiet">Edit details</summary><form class="edit-item"><div class="grid2">
          <label>Title<input name="title" value="${esc(i.title)}" required></label><label>Type<select name="item_type">${opts(BACKLOG_TYPES, i.item_type)}</select></label>
          <label>Owner<select name="owner_id">${personOptions(people, i.owner_id)}</select></label>
          <label>PI feature <span class="quiet">(optional)</span><select name="feature_id" data-features><option value=""></option></select></label></div>
          <label>Story <span class="quiet">(the problem or user story)</span><textarea name="description" rows="3">${esc(i.description || "")}</textarea></label>
          <label>Acceptance criteria<textarea name="acceptance" rows="3">${esc(i.acceptance || "")}</textarea></label>
          <label>Technical notes <span class="quiet">(approach, risks, what to touch)</span><textarea name="technical_notes" rows="3">${esc(i.technical_notes || "")}</textarea></label>
          <label>Dependencies<input name="dependencies" value="${esc(i.dependencies || "")}"></label>
          <label>Private notes<textarea name="notes" rows="2">${esc(i.notes || "")}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("backlog_item", i.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}</details>`;
      main.innerHTML = `${planTabs("")}
        <p class="quiet">The next set of candidate stories for the upcoming sprint, in priority order. Bring them over from Jira, refine them until they're ready, estimate together, then pull them into a sprint.</p>
        ${ro ? "" : `<details class="card"${d.items.length ? "" : " open"}><summary><b>Bring stories over from Jira</b></summary>
          <form id="paste"><label>One per line: the Jira key, then the title. Add <code>| 5</code> at the end for points.<textarea name="text" rows="5" class="mono" placeholder="ABC-123 [Placeholder story title]&#10;ABC-124 [Placeholder story title] | 3"></textarea></label>
            <label class="check"><input type="checkbox" name="update"> Update titles and points of stories already here</label><div class="actions"><button class="btn primary" type="submit">Add to backlog</button></div></form><div id="paste-result"></div></details>`}
        <div class="row"><select id="bf" style="max-width:200px"><option value="">Everything open</option>${opts(["needs refinement", "ready"], filter)}</select><span class="spacer"></span>
          <span class="quiet">${d.items.filter((i) => i.status === "ready").length} ready, ${d.items.filter((i) => i.status === "ready").reduce((n, i) => n + (i.points || 0), 0)} points · <a href="#/planning/plan">Plan a sprint</a></span></div>
        <section class="card">${items.map(item).join("") || '<p class="quiet">The backlog is empty.</p>'}</section>
        ${ro ? "" : `<section class="card"><h2>Add one story</h2><form id="add-item" class="row"><input name="jira_key" placeholder="ABC-123" style="max-width:130px"><input name="title" required placeholder="Title" style="flex:1;min-width:220px">
          <select name="item_type" style="max-width:140px">${opts(BACKLOG_TYPES, "story")}</select><button class="btn" type="submit">Add</button></form></section>`}`;
      main.querySelector("#bf").onchange = (e) => { sessionStorage.setItem("ba-backlog-filter", e.target.value); BA.rerender(); };
      if (ro) return;
      const features = (await Promise.all(pis.slice(0, 3).map((p) => BA.api(`/api/pis/${p.id}/board`).then((b) => b.features.map((f) => ({ ...f, pi: p.number })))))).flat();
      main.querySelectorAll("[data-features]").forEach((sel) => {
        const cur = Number(sel.closest("[data-item]") && d.items.find((i) => i.id === Number(sel.closest("[data-item]").dataset.item))?.feature_id);
        sel.innerHTML += features.map((f) => `<option value="${f.id}"${f.id === cur ? " selected" : ""}>PI ${f.pi}: ${esc(f.title)}</option>`).join("");
      });
      const paste = main.querySelector("#paste");
      paste.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const r = await BA.api("/api/backlog/paste", { method: "POST", body: { text: paste.elements.text.value, update: paste.elements.update.checked, team_id: newTeamId() } });
        BA.toast(`${r.added} added, ${r.updated} updated, ${r.skipped} already here${r.not_understood.length ? `, ${r.not_understood.length} lines not understood` : ""}.`);
        BA.rerender();
      });
      main.querySelector("#add-item").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        await BA.api("/api/backlog-items", { method: "POST", body: { jira_key: fd.get("jira_key") || null, title: fd.get("title"), item_type: fd.get("item_type"), rank: d.items.length + 1, added_on: BA.today(), team_id: newTeamId() } });
        BA.rerender();
      });
      const ids = items.map((i) => i.id);
      main.querySelectorAll("[data-item]").forEach((det) => {
        const id = Number(det.dataset.item);
        const it = d.items.find((i) => i.id === id);
        det.querySelectorAll("[data-move]").forEach((b) => (b.onclick = BA.guard(async (e) => {
          e.preventDefault();
          const pos = ids.indexOf(id), to = pos + Number(b.dataset.move);
          const order = [...ids];
          [order[pos], order[to]] = [order[to], order[pos]];
          await BA.api("/api/backlog/reorder", { method: "POST", body: { ids: order } });
          BA.rerender();
        })));
        det.querySelectorAll("[data-check]").forEach((cb) => (cb.onchange = BA.guard(async () => {
          const checks = [...det.querySelectorAll("[data-check]:checked")].map((x) => x.dataset.check);
          await BA.api(`/api/backlog-items/${id}`, { method: "PATCH", body: { ready_checks: checks } });
          BA.toast(checks.length === d.definition_of_ready.length ? "Meets the definition of ready." : "Saved.");
        })));
        det.querySelectorAll("[data-field]").forEach((el) => (el.onchange = BA.guard(async () => {
          const f = el.dataset.field;
          const value = f === "points" ? numOrNull(el.value) : el.value || null;
          if (f === "status" && value === "ready" && it.ready_total && it.ready_met < it.ready_total && !confirm("This story doesn't meet every item in the definition of ready yet. Mark it ready anyway?")) { el.value = it.status; return; }
          await BA.api(`/api/backlog-items/${id}`, { method: "PATCH", body: { [f]: value } });
          BA.rerender();
        })));
        const votes = det.querySelector("form.votes");
        if (votes) votes.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const vs = team.map((p) => ({ person_id: p.id, points: numOrNull(votes.elements[`v-${p.id}`].value) })).filter((v) => v.points != null);
          const s = await BA.api(`/api/backlog-items/${id}/votes`, { method: "POST", body: { votes: vs } });
          BA.toast(s.discuss ? `Votes run from ${s.low} to ${s.high}. Ask the highest and lowest to explain, then vote again.` : `Votes agree around ${s.median}.`);
          if (!s.discuss && it.points == null) await BA.api(`/api/backlog-items/${id}`, { method: "PATCH", body: { points: Math.round(s.median) } });
          BA.rerender();
        });
        const form = det.querySelector("form.edit-item");
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const fd = new FormData(form);
          await BA.api(`/api/backlog-items/${id}`, { method: "PATCH", body: { title: fd.get("title"), item_type: fd.get("item_type"), owner_id: numOrNull(fd.get("owner_id")), feature_id: numOrNull(fd.get("feature_id")),
            description: fd.get("description"), acceptance: fd.get("acceptance"), technical_notes: fd.get("technical_notes"), dependencies: fd.get("dependencies"), notes: fd.get("notes") } });
          BA.rerender();
        });
        det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this story from the backlog? Marking it removed keeps the record.")) return; await BA.api(`/api/backlog-items/${id}`, { method: "DELETE" }); BA.rerender(); });
      });
    },
  });

  async function renderPlan(main, sprintId) {
    const sprints = await BA.api("/api/sprints");
    keepTeam(sprints);
    const ro = presenting();
    if (!sprints.length) { main.innerHTML = `${planTabs("plan")}<p class="empty">Start a sprint in the <a href="#/sprints">sprint notebook</a> first.</p>`; return; }
    if (!sprintId) {
      const today = BA.today();
      const upcoming = [...sprints].sort((a, b) => a.number - b.number).find((s) => s.start_date && s.start_date >= today) || [...sprints].sort((a, b) => b.number - a.number)[0];
      sprintId = upcoming.id;
    }
    const d = await BA.api(`/api/sprint-planning/${sprintId}`);
    const s = d.sprint, c = d.capacity, plan = d.plan;
    document.getElementById("view-title").textContent = `Sprint ${s.number} planning`;
    const pct = c.points ? Math.min(100, Math.round((100 * c.planned) / c.points)) : 0;
    const over = c.points != null && c.planned > c.points;
    const row = (i, inSprint) => `<div class="plan-row" data-row="${i.id}">${BA.issueKeys(i.jira_key)}<span>${esc(i.title)}</span>${i.carried_from_number ? `<span class="pill warn">carried</span>` : ""}
        <span class="spacer"></span>${readiness(i)}${spreadPill(i.spread)}${ptsLabel(i)}
        ${ro ? (inSprint ? tonePill(i.status, BACKLOG_TONES) : "") : inSprint
          ? `${plan.status !== "planning" ? `<select data-status style="max-width:120px">${opts(["in sprint", "done", "removed"], i.status === "ready" ? "in sprint" : i.status)}</select>` : ""}<button class="icon-btn" title="Back to the backlog" data-return>${BA.icon("undo-2")}</button>`
          : `<button class="btn" data-pull>${BA.icon("arrow-big-up")} Pull in</button>`}</div>`;
    const vel = c.velocity.history;
    const maxV = Math.max(1, ...vel.map((v) => v.completed));
    main.innerHTML = `${planTabs("plan")}
      <div class="row"><select id="sprint-pick" style="max-width:220px">${[...sprints].sort((a, b) => b.number - a.number).map((x) => `<option value="${x.id}"${x.id === s.id ? " selected" : ""}>Sprint ${x.number}${x.start_date ? " · " + BA.fmtDate(x.start_date) : ""}</option>`).join("")}</select>
        ${tonePill(plan.status, { planning: "warn", committed: "accent", closed: "good" })}<span class="quiet">${d.working_days ? `${d.working_days} working days` : "Set sprint dates in the sprint notebook"}</span><span class="spacer"></span>
        ${ro ? "" : `<button class="btn" id="copy-plan">${BA.icon("copy")} Copy plan</button>`}</div>
      <section class="card"><h2>Sprint goal</h2>${ro || plan.status === "closed" ? `<p>${esc(s.goal || "Not set.")}</p>` : `<textarea id="goal" rows="2" placeholder="What will be true at the end of this sprint?">${esc(s.goal || "")}</textarea>`}</section>
      <div class="cards">
        <section class="card"><h2>Capacity</h2>
          <div class="cap-bar${over ? " over" : ""}"><span style="width:${pct}%"></span></div>
          <p><b>${c.planned}</b> of <b>${c.points ?? "?"}</b> points planned${over ? ' <span class="pill bad">over capacity</span>' : ""}${c.unestimated ? ` <span class="pill warn">${c.unestimated} not estimated</span>` : ""}</p>
          <p class="quiet">${c.full_days ? `${c.available_days} of ${c.full_days} person-days available` : "Add team members under People to plan by availability"}${c.velocity.average != null ? ` · recent velocity ${c.velocity.average}` : ""}${c.suggested != null ? ` · suggested ${c.suggested}` : ""}</p>
          ${ro ? "" : `<label class="check">Capacity override <input type="number" id="cap-override" min="0" value="${esc(plan.capacity_override ?? "")}" style="max-width:90px"></label>`}
          ${vel.length ? `<div class="vel">${vel.map((v) => `<div title="Sprint ${v.sprint}: ${v.completed} points"><span style="height:${Math.round((100 * v.completed) / maxV)}%"></span><small>${v.sprint}</small></div>`).join("")}</div><p class="quiet">Completed points, recent sprints</p>` : ""}</section>
        <section class="card"><h2>Who's available</h2>${d.people.map((p) => `<div class="item"><span>${esc(p.name)}</span><span class="spacer"></span>${ro ? `<span class="quiet">${p.days ?? "?"} days</span>`
          : `<input type="number" min="0" data-avail="${p.person_id}" value="${esc(p.days ?? "")}" style="max-width:70px"><span class="quiet">days</span>`}</div>`).join("") || '<p class="quiet">No team members yet. Add people with the employee or contractor relationship.</p>'}</section>
      </div>
      <div class="plan-cols">
        <section class="card"><h2>In sprint ${s.number} <span class="quiet">${d.pulled.length}</span></h2>${d.pulled.map((i) => row(i, true)).join("") || '<p class="quiet">Nothing pulled in yet.</p>'}</section>
        ${plan.status === "closed" ? "" : `<section class="card"><h2>Ready on the backlog <span class="quiet">${d.ready.length}</span></h2>${d.ready.map((i) => row(i, false)).join("") || '<p class="quiet">No ready stories. <a href="#/planning">Refine the backlog</a>.</p>'}</section>`}
      </div>
      ${ro ? "" : `<div class="row">${plan.status === "planning" ? `<button class="btn primary" id="commit">Commit the sprint</button>` : ""}${plan.status === "committed" ? `<button class="btn" id="close-sprint">Close the sprint</button>` : ""}
        ${plan.status === "committed" ? `<span class="quiet">Committed ${plan.committed_points} points on ${BA.fmtDate(plan.committed_on)}.</span>` : ""}${plan.status === "closed" ? `<span class="quiet">Closed: ${plan.completed_points} of ${plan.committed_points ?? "?"} points done.</span>` : ""}</div>`}`;
    main.querySelector("#sprint-pick").onchange = (e) => BA.go(`/planning/${e.target.value}`);
    if (ro) return;
    const goal = main.querySelector("#goal");
    if (goal) goal.onchange = BA.guard(async () => { await BA.api(`/api/sprints/${s.id}`, { method: "PATCH", body: { goal: goal.value } }); BA.toast("Goal saved."); });
    main.querySelector("#cap-override").onchange = BA.guard(async (e) => { await BA.api(`/api/sprint-plans/${plan.id}`, { method: "PATCH", body: { capacity_override: numOrNull(e.target.value) } }); BA.rerender(); });
    main.querySelectorAll("[data-avail]").forEach((el) => (el.onchange = BA.guard(async () => { await BA.api(`/api/sprint-planning/${s.id}/availability`, { method: "PUT", body: { person_id: Number(el.dataset.avail), days: numOrNull(el.value) } }); BA.rerender(); })));
    main.querySelectorAll("[data-row]").forEach((r) => {
      const id = Number(r.dataset.row);
      const pullB = r.querySelector("[data-pull]");
      if (pullB) pullB.onclick = BA.guard(async () => { const res = await BA.api(`/api/sprint-planning/${s.id}/pull`, { method: "POST", body: { item_id: id } }); if (res.warning) BA.toast(res.warning); BA.rerender(); });
      const ret = r.querySelector("[data-return]");
      if (ret) ret.onclick = BA.guard(async () => { await BA.api(`/api/sprint-planning/${s.id}/return`, { method: "POST", body: { item_id: id } }); BA.rerender(); });
      const st = r.querySelector("[data-status]");
      if (st) st.onchange = BA.guard(async () => { await BA.api(`/api/backlog-items/${id}`, { method: "PATCH", body: { status: st.value } }); BA.rerender(); });
    });
    const commitB = main.querySelector("#commit");
    if (commitB) commitB.onclick = BA.guard(async () => {
      if (over && !confirm(`That's ${c.planned} points against a capacity of ${c.points}. Commit anyway?`)) return;
      await BA.api(`/api/sprint-planning/${s.id}/commit`, { method: "POST", body: { goal: goal ? goal.value : null } });
      BA.toast("Sprint committed.");
      BA.rerender();
    });
    const closeB = main.querySelector("#close-sprint");
    if (closeB) closeB.onclick = BA.guard(async () => {
      if (!confirm("Close the sprint? Unfinished stories carry into the next sprint (or back to the backlog if there isn't one).")) return;
      const r = await BA.api(`/api/sprint-planning/${s.id}/close`, { method: "POST", body: {} });
      BA.toast(`${r.completed_points} points done; ${r.carried} stories carried over.`);
      BA.rerender();
    });
    main.querySelector("#copy-plan").onclick = BA.guard(async () => { const out = await BA.api(`/api/sprint-planning/${s.id}/summary/export`, { method: "POST", body: {} }); await navigator.clipboard.writeText(out.markdown); BA.toast("Plan copied."); });
  }

  async function renderDor(main) {
    const d = await BA.api("/api/planning/definition-of-ready");
    const ro = presenting();
    main.innerHTML = `${planTabs("ready")}
      <section class="card"><h2>Definition of ready</h2><p class="quiet">What a story needs before the team pulls it into a sprint. Each backlog story is checked against this list. Agree it with the team, then revisit it at retros.</p>
        ${d.items.length ? `<ul class="checklist">${d.items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : '<p class="quiet">Nothing agreed yet.</p>'}
        ${ro ? "" : `<form id="dor"><label>One item per line<textarea name="items" rows="8">${esc(d.items.join("\n"))}</textarea></label>
          <div class="actions">${d.items.length ? "" : '<button class="btn left" type="button" id="dor-starter">Load a starter list</button>'}<button class="btn primary" type="submit">Save</button></div></form>`}
        <p class="quiet">Its partner, the <a href="#/qa/dod">definition of done</a>, lives under QA resources.</p></section>`;
    if (ro) return;
    main.querySelector("#dor").onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/planning/definition-of-ready", { method: "PUT", body: { items: new FormData(e.target).get("items").split("\n") } }); BA.toast("Saved."); BA.rerender(); });
    const st = main.querySelector("#dor-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/planning/definition-of-ready/starter", { method: "POST", body: {} }); BA.rerender(); });
  }

  // ---------------------------------------------------------------- Teams and the Scrum of Scrums

  const TEAM_STATUS = ["on track", "at risk", "off track"];
  const TEAM_TONES = { "on track": "good", "at risk": "warn", "off track": "bad" };
  const SOS_KINDS = ["issue", "dependency", "decision", "risk", "impediment", "knowledge"];
  const SOS_STATUS = ["open", "in progress", "waiting", "done"];
  const SOS_TONES = { open: "warn", "in progress": "accent", waiting: "", done: "good" };

  BA.view("/teams", {
    title: "Teams",
    async render(main, param) {
      if (param && /^\d+$/.test(param)) return renderTeam(main, Number(param));
      const teams = await BA.api("/api/teams/overview");
      const ro = presenting();
      const card = (t) => `<a class="sys-card team-card" href="#/teams/${t.id}"><div class="row"><b>${esc(t.name)}</b>${t.kind === "mine" ? '<span class="pill">my team</span>' : ""}<span class="spacer"></span>${t.status ? tonePill(t.status, TEAM_TONES) : '<span class="quiet">no status</span>'}</div>
          ${t.status_note ? `<p class="clamp">${esc(t.status_note)}</p>` : ""}
          <div class="quiet">${[t.sprint ? `Sprint ${t.sprint.number}` : t.current_sprint ? esc(t.current_sprint) : "", t.members.length ? `${t.members.length} people` : "", t.jira_project ? `Jira ${esc(t.jira_project)}` : "", t.status_date ? `updated ${BA.fmtDate(t.status_date)}` : ""].filter(Boolean).join(" · ")}</div>
          <div class="row">${t.open_sos ? `<span class="pill${t.overdue_sos ? " bad" : ""}">${t.open_sos} open across teams${t.overdue_sos ? `, ${t.overdue_sos} late` : ""}</span>` : ""}${t.dependencies ? `<span class="pill warn">${t.dependencies} dependencies</span>` : ""}
            ${t.kind === "mine" && t.open_actions ? `<span class="pill">${t.open_actions} dev-sync</span>` : ""}${t.kind === "mine" && t.open_risks ? `<span class="pill">${t.open_risks} risks</span>` : ""}</div></a>`;
      main.innerHTML = `<p class="quiet">Your team, and the teams you work with or oversee. Your team's work is tracked across the toolkit; other teams are tracked lightly here, with what's open between you in the <a href="#/sos">Scrum of Scrums</a>.</p>
        <div class="sys-grid">${teams.map(card).join("")}</div>
        ${ro ? "" : `<section class="card" style="margin-top:16px"><h2>Add a team</h2><form id="add-team" class="row"><input name="name" required placeholder="Team name" style="max-width:280px">
          <input name="jira_project" placeholder="Jira project key" style="max-width:160px"><button class="btn primary" type="submit">Add</button></form></section>`}`;
      const add = main.querySelector("#add-team");
      if (add) add.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(add); const t = await BA.api("/api/teams", { method: "POST", body: { name: fd.get("name"), jira_project: fd.get("jira_project") || null } }); loadTeams(); BA.go(`/teams/${t.id}`); });
    },
  });

  async function renderTeam(main, id) {
    const [d, people, systems] = await Promise.all([BA.api(`/api/teams/${id}/detail`), BA.api("/api/people"), BA.api("/api/systems")]);
    const t = d.team;
    const ro = presenting();
    document.getElementById("view-title").textContent = t.name;
    const sosRow = (i) => `<div class="item">${tonePill(i.status, SOS_TONES)}<span class="pill">${esc(i.kind)}</span><a href="#/sos">${esc(i.question)}</a>${BA.issueKeys(i.jira_keys)}<span class="spacer"></span><span class="quiet">${esc(i.owner_name || i.owner_team_name || "")}${i.due ? " · " + BA.fmtDate(i.due) : ""}</span></div>`;
    main.innerHTML = `<p><a href="#/teams">All teams</a></p>
      <section class="card"><div class="row"><h2>${esc(t.name)}</h2>${t.kind === "mine" ? '<span class="pill">my team</span>' : ""}<span class="spacer"></span>${t.status ? tonePill(t.status, TEAM_TONES) : ""}${t.status_date ? `<span class="quiet">${BA.fmtDate(t.status_date)}</span>` : ""}</div>
        ${t.purpose ? BA.md(t.purpose) : ""}${t.status_note ? `<p><b>Status:</b> ${esc(t.status_note)}</p>` : ""}
        <div class="facts">${[t.product_owner_name ? `<div><span class="quiet">Product owner</span> ${esc(t.product_owner_name)}</div>` : "", t.scrum_master_name ? `<div><span class="quiet">Scrum Master</span> ${esc(t.scrum_master_name)}</div>` : "",
          t.lead_name ? `<div><span class="quiet">Lead</span> ${esc(t.lead_name)}</div>` : "", t.jira_project ? `<div><span class="quiet">Jira project</span> ${esc(t.jira_project)}</div>` : "", t.cadence ? `<div><span class="quiet">Cadence</span> ${esc(t.cadence)}</div>` : "",
          t.current_sprint || t.current_goal ? `<div><span class="quiet">Current sprint</span> ${esc(t.current_sprint || "")}${t.sprint_ends ? ` (ends ${BA.fmtDate(t.sprint_ends)})` : ""}${t.current_goal ? `: ${esc(t.current_goal)}` : ""}</div>` : "",
          t.board_url ? `<div><span class="quiet">Board</span> ${/^https?:/.test(t.board_url) ? `<a href="${esc(t.board_url)}" target="_blank" rel="noopener">open ${BA.icon("external-link")}</a>` : esc(t.board_url)}</div>` : ""].join("")}</div>
        ${d.members.length ? `<p>${d.members.map((m) => `<a href="#/people/${m.id}">${esc(m.name)}</a>${m.role ? ` <span class="quiet">${esc(m.role)}</span>` : ""}`).join(" · ")}</p>` : ""}
        ${d.systems.length ? `<p class="quiet">Owns: ${d.systems.map((s) => `<a href="#/architecture/s-${s.id}">${esc(s.name)}</a>`).join(", ")}</p>` : ""}</section>
      ${ro ? "" : `<section class="card"><h2>Status update</h2><form id="team-status" class="row"><select name="status" style="max-width:150px"><option value=""></option>${opts(TEAM_STATUS, t.status)}</select>
        <input name="status_note" value="${esc(t.status_note || "")}" placeholder="One line on where things stand" style="flex:1;min-width:240px">
        ${t.kind === "other" ? `<input name="current_sprint" value="${esc(t.current_sprint || "")}" placeholder="Their sprint" style="max-width:140px"><input type="date" name="sprint_ends" value="${esc(t.sprint_ends || "")}" style="max-width:160px">
          <input name="current_goal" value="${esc(t.current_goal || "")}" placeholder="Their sprint goal" style="max-width:260px">` : ""}<button class="btn primary" type="submit">Save</button></form></section>`}
      <div class="cards">
        <section class="card"><h2>Open across teams</h2>${d.sos_open.map(sosRow).join("") || '<p class="quiet">Nothing open with this team.</p>'}<p class="quiet"><a href="#/sos">Scrum of Scrums</a></p></section>
        ${t.kind === "mine" ? `<section class="card"><h2>This team's open work</h2>${d.sprints.length ? `<p class="quiet">Latest sprint: ${d.sprints[0].number}${d.sprints[0].goal ? ", " + esc(d.sprints[0].goal) : ""}</p>` : ""}
          <p>${d.actions.length} open dev-sync items · ${d.risks.length} open risks</p>${d.risks.slice(0, 5).map((r) => `<div class="item"><a href="#/risks">${esc(r.title)}</a><span class="spacer"></span><span class="quiet">${esc(r.level)}</span></div>`).join("")}</section>` : ""}
        ${d.sos_done.length ? `<section class="card"><h2>Settled recently</h2>${d.sos_done.map((i) => `<div class="item"><span>${esc(i.question)}</span><span class="spacer"></span><span class="quiet">${esc(i.resolution || "")}</span></div>`).join("")}</section>` : ""}
      </div>
      ${ro ? "" : `<details class="card"><summary><b>Team details</b></summary><form id="team-edit"><div class="grid2">
        <label>Name<input name="name" value="${esc(t.name)}" required></label><label>Whose<select name="kind"><option value="mine"${t.kind === "mine" ? " selected" : ""}>My team</option><option value="other"${t.kind === "other" ? " selected" : ""}>Another team</option></select></label>
        <label>Product owner<select name="product_owner_id">${personOptions(people, t.product_owner_id)}</select></label><label>Scrum Master<select name="scrum_master_id">${personOptions(people, t.scrum_master_id)}</select></label>
        <label>Lead or manager<select name="lead_id">${personOptions(people, t.lead_id)}</select></label><label>Jira project key<input name="jira_project" value="${esc(t.jira_project || "")}"></label>
        <label>Board link<input name="board_url" value="${esc(t.board_url || "")}"></label><label>Cadence<input name="cadence" value="${esc(t.cadence || "")}" placeholder="Such as: two-week sprints, starting Mondays"></label></div>
        <label>Purpose<textarea name="purpose" rows="2">${esc(t.purpose || "")}</textarea></label>
        <label>Members</label><div class="case-picks">${people.map((p) => `<label class="check"><input type="checkbox" name="member_ids" value="${p.id}"${t.member_ids.includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("") || '<span class="quiet">Add people first.</span>'}</div>
        <label>Systems it owns</label><div class="case-picks">${systems.map((s) => `<label class="check"><input type="checkbox" name="system_ids" value="${s.id}"${t.system_ids.includes(s.id) ? " checked" : ""}> ${esc(s.name)}</label>`).join("") || '<span class="quiet">Add systems under Architecture.</span>'}</div>
        <label>Private notes<textarea name="notes" rows="2">${esc(t.notes || "")}</textarea></label>
        <div class="actions"><button class="btn danger left" type="button" id="del-team">Delete team</button>${BA.historyButton("team", id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}`;
    if (ro) return;
    const st = main.querySelector("#team-status");
    st.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(st);
      const body = { status: fd.get("status") || null, status_note: fd.get("status_note") };
      if (t.kind === "other") Object.assign(body, { current_sprint: fd.get("current_sprint"), sprint_ends: fd.get("sprint_ends") || null, current_goal: fd.get("current_goal") });
      await BA.api(`/api/teams/${id}`, { method: "PATCH", body });
      BA.rerender();
    });
    const form = main.querySelector("#team-edit");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      await BA.api(`/api/teams/${id}`, { method: "PATCH", body: { name: fd.get("name"), kind: fd.get("kind"), product_owner_id: numOrNull(fd.get("product_owner_id")), scrum_master_id: numOrNull(fd.get("scrum_master_id")),
        lead_id: numOrNull(fd.get("lead_id")), jira_project: fd.get("jira_project"), board_url: fd.get("board_url"), cadence: fd.get("cadence"), purpose: fd.get("purpose"),
        member_ids: fd.getAll("member_ids").map(Number), system_ids: fd.getAll("system_ids").map(Number), notes: fd.get("notes") } });
      loadTeams();
      BA.rerender();
    });
    main.querySelector("#del-team").onclick = BA.guard(async () => { if (!confirm("Delete this team? Records tied to it are kept, without a team.")) return; await BA.api(`/api/teams/${id}`, { method: "DELETE" }); loadTeams(); BA.go("/teams"); });
  }

  BA.view("/sos", {
    title: "Scrum of Scrums",
    async render(main, param) {
      if (param === "summary") return renderSosSummary(main);
      if (param && /^m-\d+$/.test(param)) return renderSosMeeting(main, Number(param.slice(2)));
      const [d, people] = await Promise.all([BA.api("/api/sos/overview"), BA.api("/api/people")]);
      const ro = presenting();
      const teamName = Object.fromEntries(d.teams.map((x) => [x.id, x.name]));
      const f = (() => { try { return JSON.parse(sessionStorage.getItem("ba-sos-filter") || "{}"); } catch { return {}; } })();
      const shown = d.items.filter((i) => (f.done || i.status !== "done") && (!f.kind || i.kind === f.kind) && (!f.team || i.owner_team_id === Number(f.team) || (i.team_ids || []).includes(Number(f.team)) || i.raised_by_team_id === Number(f.team)));
      const teamChecks = (sel, name) => d.teams.map((x) => `<label class="check"><input type="checkbox" name="${name}" value="${x.id}"${(sel || []).includes(x.id) ? " checked" : ""}> ${esc(x.name)}</label>`).join("");
      const teamOpts = (sel) => `<option value=""></option>${d.teams.map((x) => `<option value="${x.id}"${x.id === sel ? " selected" : ""}>${esc(x.name)}</option>`).join("")}`;
      const fields = (i = {}) => `<div class="grid2"><label>Question or topic<input name="question" value="${esc(i.question || "")}" required></label><label>Kind<select name="kind">${opts(SOS_KINDS, i.kind || "issue")}</select></label>
          <label>Raised by team<select name="raised_by_team_id">${teamOpts(i.raised_by_team_id)}</select></label><label>Owning team<select name="owner_team_id">${teamOpts(i.owner_team_id)}</select></label>
          <label>Owner<select name="owner_id">${personOptions(people, i.owner_id)}</select></label><label>Due<input type="date" name="due" value="${esc(i.due || "")}"></label>
          <label>Status<select name="status">${opts(SOS_STATUS, i.status || "open")}</select></label><label>Jira keys<input name="jira_keys" value="${esc((i.jira_keys || []).join(", "))}" placeholder="ABC-123"></label></div>
        <label>Outcome or deliverable expected<input name="outcome" value="${esc(i.outcome || "")}" placeholder="What 'done' looks like"></label>
        <label>Teams involved</label><div class="row">${teamChecks(i.team_ids, "team_ids")}</div>
        <label>Stakeholders</label><div class="case-picks">${people.map((p) => `<label class="check"><input type="checkbox" name="stakeholder_ids" value="${p.id}"${(i.stakeholder_ids || []).includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
        <label>Details<textarea name="details" rows="3">${esc(i.details || "")}</textarea></label>
        ${i.id ? `<label>Resolution <span class="quiet">(what was decided or delivered)</span><input name="resolution" value="${esc(i.resolution || "")}"></label>` : ""}
        <label>Private notes<textarea name="notes" rows="2">${esc(i.notes || "")}</textarea></label>`;
      const read = (form) => { const fd = new FormData(form); return { question: fd.get("question"), kind: fd.get("kind"), raised_by_team_id: numOrNull(fd.get("raised_by_team_id")), owner_team_id: numOrNull(fd.get("owner_team_id")),
        owner_id: numOrNull(fd.get("owner_id")), due: fd.get("due") || null, status: fd.get("status"), jira_keys: fd.get("jira_keys"), outcome: fd.get("outcome"), team_ids: fd.getAll("team_ids").map(Number),
        stakeholder_ids: fd.getAll("stakeholder_ids").map(Number), details: fd.get("details"), ...(form.elements.resolution ? { resolution: fd.get("resolution") } : {}), notes: fd.get("notes") }; };
      const pname = Object.fromEntries(people.map((p) => [p.id, p.name]));
      const row = (i) => `<details class="plan-item${i.status === "done" ? " dropped" : ""}" data-sos="${i.id}"><summary>${tonePill(i.status, SOS_TONES)}<span class="pill">${esc(i.kind)}</span><b>${esc(i.question)}</b>${BA.issueKeys(i.jira_keys)}<span class="spacer"></span>
          <span class="quiet">${esc(i.owner_name || i.owner_team_name || "no owner")}</span>${i.due ? `<span class="${d.overdue.includes(i.id) ? "pill bad" : "quiet"}">${BA.fmtDate(i.due)}</span>` : ""}</summary>
          ${i.outcome ? `<p><b>Outcome expected:</b> ${esc(i.outcome)}</p>` : ""}${i.details ? BA.md(i.details) : ""}
          <p class="quiet">${[(i.team_ids || []).length ? "Teams: " + i.team_ids.map((x) => esc(teamName[x] || "")).join(", ") : "", (i.stakeholder_ids || []).length ? "Stakeholders: " + i.stakeholder_ids.map((x) => esc(pname[x] || "")).join(", ") : "",
            i.raised_by_team_name ? "Raised by " + esc(i.raised_by_team_name) : ""].filter(Boolean).join(" · ")}</p>${i.resolution ? `<p><b>Resolution:</b> ${esc(i.resolution)}</p>` : ""}
          ${ro ? "" : `<form class="edit-sos">${fields(i)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("sos_item", i.id)}<button class="btn primary" type="submit">Save</button></div></form>`}</details>`;
      main.innerHTML = `<nav class="tabs"><a href="#/sos" class="active">Log</a><a href="#/sos/summary">Leadership summary</a></nav>
        <p class="quiet">The cross-team log: questions, dependencies, decisions, risks, impediments and knowledge that cross team lines, each with stakeholders, an owner, the outcome expected and a date.</p>
        <div class="stats">${SOS_KINDS.map((k) => `<section class="card stat"><div class="stat-n">${d.counts[k]}</div><div class="quiet">open ${k === "knowledge" ? "knowledge items" : k + (k.endsWith("y") ? "" : "s")}</div></section>`).join("").replace("open dependencys", "open dependencies")}</div>
        <div class="row"><select id="sf-team" style="max-width:200px"><option value="">Every team</option>${d.teams.map((x) => `<option value="${x.id}"${String(x.id) === f.team ? " selected" : ""}>${esc(x.name)}</option>`).join("")}</select>
          <select id="sf-kind" style="max-width:170px"><option value="">Every kind</option>${opts(SOS_KINDS, f.kind)}</select><label class="check"><input type="checkbox" id="sf-done"${f.done ? " checked" : ""}> Show done</label><span class="spacer"></span>
          ${d.overdue.length ? `<span class="pill bad">${d.overdue.length} overdue</span>` : ""}${ro ? "" : `<button class="btn" id="start-meeting">Start a meeting</button>`}</div>
        <section class="card">${shown.map(row).join("") || '<p class="quiet">Nothing logged yet, or nothing matches.</p>'}</section>
        ${ro ? "" : `<form id="add-sos" class="card"><h2>Log an item</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form>`}
        ${d.meetings.length ? `<section class="card"><h2>Meetings</h2>${d.meetings.map((m) => `<div class="item"><a href="#/sos/m-${m.id}">${BA.fmtDate(m.date)}</a><span class="spacer"></span><span class="quiet">${(m.item_ids || []).length} items</span></div>`).join("")}</section>` : ""}`;
      const saveF = () => { sessionStorage.setItem("ba-sos-filter", JSON.stringify({ team: main.querySelector("#sf-team").value, kind: main.querySelector("#sf-kind").value, done: main.querySelector("#sf-done").checked })); BA.rerender(); };
      ["#sf-team", "#sf-kind", "#sf-done"].forEach((s) => (main.querySelector(s).onchange = saveF));
      if (ro) return;
      const add = main.querySelector("#add-sos");
      add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/sos-items", { method: "POST", body: { ...read(add), raised_on: BA.today() } }); BA.rerender(); });
      main.querySelector("#start-meeting").onclick = BA.guard(async () => { const m = await BA.api("/api/sos/meetings/start", { method: "POST" }); BA.go(`/sos/m-${m.id}`); });
      main.querySelectorAll("[data-sos]").forEach((det) => {
        const id = det.dataset.sos, form = det.querySelector("form");
        form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/sos-items/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
        det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this item? Marking it done keeps the record.")) return; await BA.api(`/api/sos-items/${id}`, { method: "DELETE" }); BA.rerender(); });
      });
    },
  });

  async function renderSosMeeting(main, id) {
    const [m, d] = await Promise.all([BA.api(`/api/sos-meetings/${id}`), BA.api("/api/sos/overview")]);
    const ro = presenting();
    const byId = Object.fromEntries(d.items.map((i) => [i.id, i]));
    const teamName = Object.fromEntries(d.teams.map((x) => [x.id, x.name]));
    document.getElementById("view-title").textContent = `Scrum of Scrums, ${BA.fmtDate(m.date)}`;
    main.innerHTML = `<p><a href="#/sos">Scrum of Scrums</a></p>
      <section class="card"><h2>${BA.fmtDate(m.date)}</h2><p class="quiet">Teams: ${(m.team_ids || []).map((x) => esc(teamName[x] || "")).join(", ")}</p>
        <h3>Walk the open items</h3>${(m.item_ids || []).map((iid) => byId[iid]).filter(Boolean).map((i) => `<div class="item">${tonePill(i.status, SOS_TONES)}<span class="pill">${esc(i.kind)}</span><span>${esc(i.question)}</span><span class="spacer"></span><span class="quiet">${esc(i.owner_name || i.owner_team_name || "no owner")}${i.due ? " · " + BA.fmtDate(i.due) : ""}</span></div>`).join("") || '<p class="quiet">Nothing was open.</p>'}
        <p class="quiet">Update each item in the <a href="#/sos">log</a> as you go.</p>
        ${ro ? (m.summary ? BA.md(m.summary) : "") : `<form id="meeting"><label>Summary <span class="quiet">(shareable: what was agreed, what's next)</span><textarea name="summary" rows="5">${esc(m.summary || "")}</textarea></label>
          <label>Private notes<textarea name="notes" rows="3">${esc(m.notes || "")}</textarea></label><div class="actions">${BA.historyButton("sos_meeting", id)}<button class="btn primary" type="submit">Save</button></div></form>`}</section>`;
    const form = main.querySelector("#meeting");
    if (form) form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(form); await BA.api(`/api/sos-meetings/${id}`, { method: "PATCH", body: { summary: fd.get("summary"), notes: fd.get("notes") } }); BA.toast("Saved."); });
  }

  async function renderSosSummary(main) {
    const s = await BA.api("/api/sos/summary");
    main.innerHTML = `<nav class="tabs"><a href="#/sos">Log</a><a href="#/sos/summary" class="active">Leadership summary</a></nav>
      <section class="card"><div class="row"><h2>For leadership</h2><span class="spacer"></span>${presenting() ? "" : `<button class="btn primary" id="copy-sos">${BA.icon("copy")} Copy as Markdown</button>`}</div>
        <p class="quiet">Each team's status, what's overdue, what's open across teams with owners and dates, and what was settled recently. Private notes are left out.</p>
        <div class="msg-preview">${BA.md(s.markdown)}</div></section>`;
    const c = main.querySelector("#copy-sos");
    if (c) c.onclick = BA.guard(async () => { const out = await BA.api("/api/sos/summary/export", { method: "POST", body: {} }); await navigator.clipboard.writeText(out.markdown); BA.toast("Summary copied."); });
  }

  // ---------------------------------------------------------------- Culture and trust

  const C_CATEGORIES = ["intimidation or dominating", "chaos or missing process", "quiet voices unheard", "blame", "siloed teams", "disrespect", "burnout or overload", "heroics", "great collaboration", "speaking up", "helping others", "other"];
  const C_ACTIONS = ["not yet", "watching", "spoke privately", "raised with the team", "raised with my manager", "agreement or process change", "escalated"];
  const C_STATUS = ["open", "watching", "addressed"];
  const C_STATUS_TONES = { open: "warn", watching: "accent", addressed: "good" };
  const A_AREAS = ["working together", "disagreement", "meetings", "code review", "communication", "quality", "other"];
  const cultureTabs = (active) => `<nav class="tabs">${[["", "Overview"], ["noticing", "Noticing"], ["pulse", "Trust pulse"], ["standards", "My standards"], ["agreements", "Team agreements"], ["map", "Culture map"], ["glossary", "Glossary"], ["behaviors", "Behaviors to change"], ["brief", "Role brief"]]
    .map(([k, l]) => `<a href="#/culture${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${l}</a>`).join("")}</nav>`;
  const bars = (vals, max = 5) => `<span class="mini-bars">${vals.map((v) => `<span title="${v ?? "–"}" style="height:${v ? Math.round((v / max) * 100) : 4}%"></span>`).join("")}</span>`;

  BA.view("/culture", {
    title: "Culture and trust",
    async render(main, param) {
      const views = { noticing: renderNoticing, pulse: renderPulse, standards: renderStandards, agreements: renderAgreements, map: renderCultureMap, glossary: renderGlossary, behaviors: renderBehaviors, brief: renderBrief };
      if (views[param]) return views[param](main);
      const d = await BA.api("/api/culture/overview");
      if (!d.private) {
        main.innerHTML = `${cultureTabs("")}<section class="card"><h2>Team agreements</h2>${agreementsList(d.agreements.filter((a) => a.status === "agreed"))}</section>`;
        return;
      }
      const last = d.pulses.find((p) => p.source === "my read");
      main.innerHTML = `${cultureTabs("")}
        ${d.today ? `<section class="card"><blockquote class="standard-quote">${esc(d.today.text)}</blockquote>${d.today.why ? `<p class="quiet">${esc(d.today.why)}</p>` : ""}<p class="quiet">One of <a href="#/culture/standards">your standards</a>, a different one each day.</p></section>`
          : `<section class="card"><h2>Start with your standards</h2><p class="quiet">The handful of commitments you hold yourself to. One shows here and on Today each day, so they stay in mind.</p><a class="btn primary" href="#/culture/standards">Write my standards</a></section>`}
        <div class="cards">
          <section class="card"><h2>Needs attention</h2>${[...d.unaddressed.map((o) => `<div class="item"><span class="pill bad">unaddressed</span><a href="#/culture/noticing">${esc(o.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(o.date)}</span></div>`),
            ...d.follow_ups.map((o) => `<div class="item"><span class="pill warn">follow up</span><a href="#/culture/noticing">${esc(o.title)}</a><span class="spacer"></span><span class="quiet">${BA.fmtDate(o.follow_up)}</span></div>`)].join("") || '<p class="quiet">Nothing waiting on you.</p>'}
            <p class="quiet">${d.open["my team"]} open on your team · ${d.open.organization} in the wider organization · ${d.open.positive} good things noted this month</p></section>
          <section class="card"><h2>Trust pulse</h2>${last ? `<p class="quiet">Your last read: ${BA.fmtDate(last.date)}</p>${d.dimensions.map((dim) => `<div class="item"><span>${esc(dim.label)}</span><span class="spacer"></span>${bars(d.pulses.filter((p) => p.source === "my read").slice(0, 6).reverse().map((p) => (p.scores || {})[dim.key]))}<b>${(last.scores || {})[dim.key] ?? "–"}</b></div>`).join("")}`
            : '<p class="quiet">No pulse yet.</p>'}${d.pulse_due ? `<p><a class="btn" href="#/culture/pulse">Take the pulse</a></p>` : ""}</section>
          <section class="card"><h2>Living my standards</h2>${d.self_check_trend.length ? `<p>${bars(d.self_check_trend.map((w) => w.average))} <span class="quiet">weekly average, last ${d.self_check_trend.length} weeks</span></p>` : ""}
            <p class="quiet">${d.last_self_check ? `Last self-check ${BA.fmtDate(d.last_self_check)}.` : "No self-check yet."}</p><a class="btn" href="#/culture/standards">Weekly self-check</a></section>
          <section class="card"><h2>Team agreements</h2><p>${d.agreements.filter((a) => a.status === "agreed").length} agreed · ${d.agreements.filter((a) => a.status === "proposed").length} proposed</p>
            ${d.agreements_due.length ? `<p class="pill warn">${d.agreements_due.length} due for review</p>` : ""}<a href="#/culture/agreements">See them</a></section>
        </div>
        ${d.brief.focus.length || d.brief.situation ? `<section class="card"><h2>What I was brought in to do</h2>${d.brief.focus.length ? `<ul class="checklist">${d.brief.focus.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}${d.brief.situation ? BA.md(d.brief.situation) : ""}<p class="quiet"><a href="#/culture/brief">Role brief</a></p></section>`
          : `<section class="card"><h2>Role brief</h2><p class="quiet">Write down what you were brought in to do and the situation you inherited, so it stays beside the day-to-day. <a href="#/culture/brief">Write it</a>.</p></section>`}`;
    },
  });

  async function renderNoticing(main) {
    const [obs, people] = await Promise.all([BA.api("/api/culture-observations"), BA.api("/api/people")]);
    const ro = presenting();
    if (ro) { main.innerHTML = `${cultureTabs("noticing")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const f = (() => { try { return JSON.parse(sessionStorage.getItem("ba-cul-filter") || "{}"); } catch { return {}; } })();
    const shown = obs.filter((o) => (!f.scope || o.scope === f.scope) && (!f.kind || o.kind === f.kind) && (f.done || o.status !== "addressed"));
    const pname = Object.fromEntries(people.map((p) => [p.id, p.name]));
    const fields = (o = {}) => `<div class="grid2"><label>What you noticed<input name="title" value="${esc(o.title || "")}" required></label>
        <label>Kind<select name="kind">${opts(["concern", "positive"], o.kind || "concern")}</select></label>
        <label>Where<select name="scope">${opts(["my team", "organization"], o.scope || "my team")}</select></label><label>Category<select name="category"><option value=""></option>${opts(C_CATEGORIES, o.category)}</select></label>
        <label>Severity<select name="severity"><option value=""></option>${opts(["low", "medium", "high"], o.severity)}</select></label><label>Date<input type="date" name="date" value="${esc(o.date || BA.today())}"></label>
        <label>What I did<select name="action">${opts(C_ACTIONS, o.action || "not yet")}</select></label><label>Status<select name="status">${opts(C_STATUS, o.status || "open")}</select></label>
        <label>Follow up on<input type="date" name="follow_up" value="${esc(o.follow_up || "")}"></label></div>
        <label>Details <span class="quiet">(what happened, specifically; the effect on people)</span><textarea name="details" rows="3">${esc(o.details || "")}</textarea></label>
        <label>People involved</label><div class="case-picks">${people.map((p) => `<label class="check"><input type="checkbox" name="people_ids" value="${p.id}"${(o.people_ids || []).includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
        ${o.id ? `<label>Outcome<input name="outcome" value="${esc(o.outcome || "")}"></label>` : ""}`;
    const read = (form) => { const fd = new FormData(form); return { title: fd.get("title"), kind: fd.get("kind"), scope: fd.get("scope"), category: fd.get("category") || null, severity: fd.get("severity") || null, date: fd.get("date"),
      action: fd.get("action"), status: fd.get("status"), follow_up: fd.get("follow_up") || null, details: fd.get("details"), people_ids: fd.getAll("people_ids").map(Number), ...(form.elements.outcome ? { outcome: fd.get("outcome") } : {}) }; };
    main.innerHTML = `${cultureTabs("noticing")}
      <p class="quiet">A private log of what you see: intimidation, chaos from missing process, quiet voices drowned out, blame, siloed camps, and the good moments worth reinforcing. Harmful things on your own team left at "not yet" for a week show on Today.</p>
      <form id="add-obs" class="card"><h2>Note something</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Save</button></div></form>
      <div class="row"><select id="cf-scope" style="max-width:170px"><option value="">Everywhere</option>${opts(["my team", "organization"], f.scope)}</select><select id="cf-kind" style="max-width:150px"><option value="">Concerns and positives</option>${opts(["concern", "positive"], f.kind)}</select>
        <label class="check"><input type="checkbox" id="cf-done"${f.done ? " checked" : ""}> Show addressed</label></div>
      <section class="card">${shown.map((o) => `<details class="plan-item${o.status === "addressed" ? " dropped" : ""}" data-obs="${o.id}"><summary><span class="pill ${o.kind === "positive" ? "good" : o.severity === "high" ? "bad" : "warn"}">${esc(o.kind)}</span><b>${esc(o.title)}</b><span class="spacer"></span>
          ${o.category ? `<span class="quiet">${esc(o.category)}</span>` : ""}<span class="quiet">${esc(o.scope)}</span>${tonePill(o.status, C_STATUS_TONES)}<span class="quiet">${BA.fmtDate(o.date)}</span></summary>
          ${o.details ? BA.md(o.details) : ""}<p class="quiet">${[(o.people_ids || []).length ? "People: " + o.people_ids.map((x) => esc(pname[x] || "")).join(", ") : "", "What I did: " + esc(o.action), o.outcome ? "Outcome: " + esc(o.outcome) : ""].filter(Boolean).join(" · ")}</p>
          <form class="edit-obs">${fields(o)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("culture_observation", o.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`).join("") || '<p class="quiet">Nothing noted yet.</p>'}</section>`;
    const save = () => { sessionStorage.setItem("ba-cul-filter", JSON.stringify({ scope: main.querySelector("#cf-scope").value, kind: main.querySelector("#cf-kind").value, done: main.querySelector("#cf-done").checked })); BA.rerender(); };
    ["#cf-scope", "#cf-kind", "#cf-done"].forEach((s) => (main.querySelector(s).onchange = save));
    const add = main.querySelector("#add-obs");
    add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/culture-observations", { method: "POST", body: read(add) }); BA.toast("Noted."); BA.rerender(); });
    main.querySelectorAll("[data-obs]").forEach((det) => {
      const id = det.dataset.obs, form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/culture-observations/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this note?")) return; await BA.api(`/api/culture-observations/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderPulse(main) {
    const d = await BA.api("/api/culture/overview");
    if (!d.private) { main.innerHTML = `${cultureTabs("pulse")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const teams = BA.teamList || [];
    const scale = (key) => `<div class="seg pulse-seg">${[1, 2, 3, 4, 5].map((n) => `<label><input type="radio" name="${key}" value="${n}"><span>${n}</span></label>`).join("")}</div>`;
    const rows = d.pulses;
    main.innerHTML = `${cultureTabs("pulse")}
      <form id="pulse" class="card"><h2>Take the pulse</h2><p class="quiet">Your honest read of the team right now, from 1 (worrying) to 5 (strong). Or enter the averages from an anonymous team survey. Every ${d.pulse_days} days is a good rhythm.</p>
        <div class="row"><select name="source" style="max-width:160px"><option value="my read">My read</option><option value="team survey">Team survey</option></select><input type="date" name="date" value="${BA.today()}" style="max-width:170px">
          ${teams.length > 1 ? `<select name="team_id" style="max-width:200px"><option value="">All my teams</option>${teams.map((x) => `<option value="${x.id}">${esc(x.name)}</option>`).join("")}</select>` : ""}<input type="number" name="respondents" min="1" placeholder="Respondents (survey)" style="max-width:190px"></div>
        ${d.dimensions.map((dim) => `<div class="item pulse-row"><span>${esc(dim.label)}</span><span class="spacer"></span>${scale(dim.key)}</div>`).join("")}
        <label>What's behind the scores<textarea name="notes" rows="3"></textarea></label>
        <div class="actions"><label class="check left">Remind me every <input type="number" id="pulse-days" min="1" max="120" value="${d.pulse_days}" style="max-width:70px"> days</label><button class="btn primary" type="submit">Save pulse</button></div></form>
      <section class="card"><h2>Over time</h2>${rows.length ? `<div class="tablewrap"><table class="data"><thead><tr><th>Date</th><th>Source</th>${d.dimensions.map((dim) => `<th title="${esc(dim.label)}">${esc(dim.key)}</th>`).join("")}<th>Notes</th></tr></thead><tbody>${rows.map((p) => `<tr><td>${BA.fmtDate(p.date)}</td><td>${esc(p.source)}${p.respondents ? ` (${p.respondents})` : ""}</td>
          ${d.dimensions.map((dim) => { const v = (p.scores || {})[dim.key]; return `<td><span class="score s${v || 0}">${v ?? "–"}</span></td>`; }).join("")}<td class="quiet">${esc((p.notes || "").slice(0, 120))}</td></tr>`).join("")}</tbody></table></div>` : '<p class="quiet">No pulses yet.</p>'}</section>`;
    const form = main.querySelector("#pulse");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const scores = Object.fromEntries(d.dimensions.map((dim) => [dim.key, numOrNull(fd.get(dim.key))]).filter(([, v]) => v != null));
      if (!Object.keys(scores).length) throw new Error("Score at least one line from 1 to 5.");
      await BA.api("/api/trust-pulses", { method: "POST", body: { source: fd.get("source"), date: fd.get("date"), team_id: numOrNull(fd.get("team_id")), respondents: numOrNull(fd.get("respondents")), scores, notes: fd.get("notes") } });
      BA.toast("Pulse saved.");
      BA.rerender();
    });
    main.querySelector("#pulse-days").onchange = BA.guard(async (e) => { await BA.api("/api/culture/settings", { method: "PUT", body: { pulse_days: Number(e.target.value) } }); BA.toast("Saved."); });
  }

  async function renderStandards(main) {
    const d = await BA.api("/api/culture/overview");
    if (!d.private) { main.innerHTML = `${cultureTabs("standards")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const active = d.standards.filter((s) => s.active);
    main.innerHTML = `${cultureTabs("standards")}
      <section class="card"><h2>My standards</h2><p class="quiet">The commitments you hold yourself to as a leader, in your own words. One appears on Today each day. Keep the list short enough to remember.</p>
        ${d.standards.map((s) => `<details class="plan-item${s.active ? "" : " dropped"}" data-std="${s.id}"><summary><b>${esc(s.text)}</b><span class="spacer"></span>${s.last ? `<span class="quiet">last ${s.last.rating}/5</span>` : ""}</summary>
          ${s.why ? `<p class="quiet">${esc(s.why)}</p>` : ""}<form class="edit-std"><label>Standard<input name="text" value="${esc(s.text)}" required></label><label>Why it matters to me<input name="why" value="${esc(s.why || "")}"></label>
          <div class="actions"><label class="check left"><input type="checkbox" name="active"${s.active ? " checked" : ""}> In use</label><button class="btn danger" type="button" data-del>Delete</button>${BA.historyButton("standard", s.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`).join("") ||
          '<p class="quiet">None yet. Start from a suggested list and rewrite it, or add your own.</p>'}
        <form id="add-std" class="row" style="margin-top:8px"><input name="text" required placeholder="A commitment, such as: no surprises" style="flex:1;min-width:240px"><button class="btn" type="submit">Add</button>
          ${d.standards.length ? "" : '<button class="btn" type="button" id="std-starter">Start from suggestions</button>'}</form></section>
      ${active.length ? `<form id="check" class="card"><h2>Weekly self-check</h2><p class="quiet">How well did you live each one this week? Be honest; this is only for you.</p>
        ${active.map((s) => `<div class="pulse-row item"><span>${esc(s.text)}</span><span class="spacer"></span><div class="seg pulse-seg">${[1, 2, 3, 4, 5].map((n) => `<label><input type="radio" name="r-${s.id}" value="${n}"><span>${n}</span></label>`).join("")}</div></div>
          <input name="n-${s.id}" placeholder="A moment that shows it, either way (optional)" class="check-note">`).join("")}
        <div class="actions"><button class="btn primary" type="submit">Save self-check</button></div></form>` : ""}`;
    main.querySelector("#add-std").onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/standards", { method: "POST", body: { text: new FormData(e.target).get("text"), position: d.standards.length } }); BA.rerender(); });
    const st = main.querySelector("#std-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/culture/standards/starter", { method: "POST" }); BA.rerender(); });
    main.querySelectorAll("[data-std]").forEach((det) => {
      const id = det.dataset.std, form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(form); await BA.api(`/api/standards/${id}`, { method: "PATCH", body: { text: fd.get("text"), why: fd.get("why"), active: form.elements.active.checked } }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this standard and its self-check history? Unticking 'In use' keeps the history.")) return; await BA.api(`/api/standards/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
    const check = main.querySelector("#check");
    if (check) check.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(check);
      const ratings = active.map((s) => ({ standard_id: s.id, rating: numOrNull(fd.get(`r-${s.id}`)), note: fd.get(`n-${s.id}`) })).filter((r) => r.rating);
      await BA.api("/api/culture/self-check", { method: "POST", body: { ratings } });
      BA.toast("Self-check saved.");
      BA.go("/culture");
    });
  }

  function agreementsList(list) {
    return A_AREAS.map((area) => [area, list.filter((a) => a.area === area)]).filter(([, l]) => l.length)
      .map(([area, l]) => `<h3>${esc(area[0].toUpperCase() + area.slice(1))}</h3><ul class="agreements">${l.map((a) => `<li>${esc(a.text)}</li>`).join("")}</ul>`).join("") || '<p class="quiet">No agreements yet.</p>';
  }

  async function renderAgreements(main) {
    const list = await BA.api("/api/team-agreements");
    const ro = presenting();
    const teams = BA.teamList || [];
    const tname = Object.fromEntries(teams.map((x) => [x.id, x.name]));
    main.innerHTML = `${cultureTabs("agreements")}
      <section class="card"><h2>How we work together</h2><p class="quiet">Agreements the team makes together: how we disagree, run meetings, review code and talk to each other. Show them on screen at a retro, and review them on the date you set.</p>
        ${agreementsList(list.filter((a) => a.status === "agreed"))}</section>
      ${ro ? "" : `<section class="card"><h2>All agreements</h2>${list.map((a) => `<form class="row agreement-row" data-agr="${a.id}"><input name="text" value="${esc(a.text)}" style="flex:1;min-width:240px"><select name="area" style="max-width:170px">${opts(A_AREAS, a.area)}</select>
          <select name="status" style="max-width:120px">${opts(["proposed", "agreed", "retired"], a.status)}</select><input type="date" name="review_on" value="${esc(a.review_on || "")}" title="Review on" style="max-width:160px">
          ${teams.length > 1 ? `<span class="quiet">${esc(tname[a.team_id] || "all teams")}</span>` : ""}<button class="btn" type="submit">Save</button><button class="icon-btn" type="button" data-del title="Delete">${BA.icon("x")}</button></form>`).join("") || '<p class="quiet">None yet.</p>'}
        <form id="add-agr" class="row" style="margin-top:8px"><input name="text" required placeholder="We agree that..." style="flex:1;min-width:240px"><select name="area" style="max-width:170px">${opts(A_AREAS, "working together")}</select><button class="btn" type="submit">Add as a proposal</button>
          ${list.length ? "" : '<button class="btn" type="button" id="agr-starter">Start from suggestions</button>'}</form>
        <p class="quiet">Suggestions load as proposals. Agree them with the team, then mark them agreed; the date is recorded.</p></section>`}`;
    if (ro) return;
    main.querySelector("#add-agr").onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(e.target); await BA.api("/api/team-agreements", { method: "POST", body: { text: fd.get("text"), area: fd.get("area") } }); BA.rerender(); });
    const st = main.querySelector("#agr-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/culture/agreements/starter", { method: "POST", body: {} }); BA.rerender(); });
    main.querySelectorAll("[data-agr]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const was = list.find((a) => a.id === Number(f.dataset.agr));
        const fd = new FormData(f);
        const body = { text: fd.get("text"), area: fd.get("area"), status: fd.get("status"), review_on: fd.get("review_on") || null };
        if (body.status === "agreed" && was.status !== "agreed") body.agreed_on = BA.today();
        await BA.api(`/api/team-agreements/${f.dataset.agr}`, { method: "PATCH", body });
        BA.toast("Saved.");
        BA.rerender();
      });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this agreement? Marking it retired keeps the record.")) return; await BA.api(`/api/team-agreements/${f.dataset.agr}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  // Three layers, as an anthropologist would read them: what's visible, the everyday norms, and the assumptions underneath.
  const CULTURE_PROMPTS = [
    ["Symbols and language", [["symbols", "What's visible", "Dress, office space, rituals, and the words and acronyms people use. Add terms to the glossary."]]],
    ["Everyday norms", [
      ["influence", "Influence", "How does an idea win support: a senior sponsor, or backing from peers and the team?"],
      ["meetings", "Meetings", "Are hard issues really discussed in meetings, or do meetings confirm what was agreed beforehand?"],
      ["execution", "Getting things done", "Does following the process matter more, or knowing the right people?"],
      ["conflict", "Conflict", "Can people raise difficult issues without fear, or is conflict avoided or pushed down?"],
      ["recognition", "Recognition", "Who gets noticed and promoted: the visible stars or the quiet collaborators?"],
      ["ends_means", "Ends and means", "Do results excuse how they were reached, or are the methods held to a standard too? Are the stated values backed by real consequences, good and bad?"],
    ]],
    ["Assumptions underneath", [["power", "Power and authority", "Does authority come with the position, with seniority, or from the ability to persuade and build consensus?"]]],
    ["So what", [["adapt_or_change", "Adapt or change", "Where will I adapt, and where will I deliberately work to change things? Say why."]]],
  ];

  async function renderCultureMap(main) {
    const ro = presenting();
    if (ro) { main.innerHTML = `${cultureTabs("map")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const units = await BA.api("/api/culture-reads");
    main.innerHTML = `${cultureTabs("map")}
      <section class="card"><h2>Read the culture like an anthropologist</h2><p class="quiet">One read per unit: your team, a team you're integrating, the wider organization. Subcultures differ, and the differences are often where integration gets hard. Fill it in slowly; norms and assumptions take weeks to see. Private.</p>
        ${units.length ? "" : '<button class="btn primary" id="map-starter">Start with three units</button>'}</section>
      ${units.map((u) => `<form class="card culture-read" data-read="${u.id}"><div class="row"><input name="unit" value="${esc(u.unit)}" style="font-weight:600;max-width:320px"><span class="spacer"></span>${BA.historyButton("culture_read", u.id)}</div>
        ${CULTURE_PROMPTS.map(([layer, fields]) => `<h3>${esc(layer)}</h3>${fields.map(([k, label, hint]) => `<label><b>${esc(label)}</b> <span class="quiet">${esc(hint)}</span><textarea name="${k}" rows="2">${esc(u[k] || "")}</textarea></label>`).join("")}`).join("")}
        <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button><button class="btn primary" type="submit">Save</button></div></form>`).join("")}
      ${units.length ? '<form id="add-unit" class="row card"><input name="unit" required placeholder="Another unit, such as a department you work with" style="flex:1"><button class="btn" type="submit">Add unit</button></form>' : ""}`;
    const st = main.querySelector("#map-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/culture/map/starter", { method: "POST" }); BA.rerender(); });
    const add = main.querySelector("#add-unit");
    if (add) add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/culture-reads", { method: "POST", body: { unit: new FormData(add).get("unit"), position: units.length } }); BA.rerender(); });
    main.querySelectorAll("[data-read]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/culture-reads/${f.dataset.read}`, { method: "PATCH", body: Object.fromEntries(new FormData(f)) }); BA.toast("Saved."); });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this unit's read?")) return; await BA.api(`/api/culture-reads/${f.dataset.read}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderBehaviors(main) {
    if (presenting()) { main.innerHTML = `${cultureTabs("behaviors")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const [list, guide] = await Promise.all([BA.api("/api/behavior-targets"), BA.api("/api/culture/behaviors/guide")]);
    const PATTERNS = ["lack of focus", "lack of discipline", "lack of innovation", "lack of teamwork", "lack of urgency", "other"];
    const STAT = ["noticed", "working on it", "improving", "changed"];
    const TONES = { noticed: "", "working on it": "warn", improving: "accent", changed: "good" };
    main.innerHTML = `${cultureTabs("behaviors")}
      <section class="card"><h2>Behaviors to change</h2><p class="quiet">Your goals are the destination; how people behave is part of how you get there. Name the patterns that stand in the way, what you see, and how you want people to work by the end of your time in the role. Then make your early wins start to shift them. Private.</p>
        <details><summary class="quiet">The usual patterns</summary>${Object.entries(guide).map(([k, v]) => `<p><b>${esc(k[0].toUpperCase() + k.slice(1))}:</b> ${esc(v)}</p>`).join("")}</details></section>
      ${list.map((b) => `<form class="card" data-bt="${b.id}"><div class="row"><select name="pattern" style="max-width:200px">${opts(PATTERNS, b.pattern)}</select><span class="pill ${TONES[b.status]}">${esc(b.status)}</span><span class="spacer"></span><select name="status" style="max-width:160px">${opts(STAT, b.status)}</select></div>
        <div class="grid2"><label>What I see<textarea name="symptoms" rows="2" placeholder="${esc(guide[b.pattern] || "")}">${esc(b.symptoms || "")}</textarea></label><label>How I want people to work by the end of my time here<textarea name="target" rows="2">${esc(b.target || "")}</textarea></label></div>
        <label>Notes and progress<textarea name="notes" rows="2">${esc(b.notes || "")}</textarea></label>
        <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("behavior_target", b.id)}<button class="btn primary" type="submit">Save</button></div></form>`).join("")}
      <form id="add-bt" class="card row"><select name="pattern" style="max-width:220px">${opts(PATTERNS, "lack of focus")}</select><button class="btn" type="submit">Add a behavior to change</button></form>`;
    main.querySelector("#add-bt").onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/behavior-targets", { method: "POST", body: { pattern: new FormData(e.target).get("pattern"), position: list.length } }); BA.rerender(); });
    main.querySelectorAll("[data-bt]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/behavior-targets/${f.dataset.bt}`, { method: "PATCH", body: Object.fromEntries(new FormData(f)) }); BA.toast("Saved."); BA.rerender(); });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this?")) return; await BA.api(`/api/behavior-targets/${f.dataset.bt}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderGlossary(main) {
    const terms = await BA.api("/api/glossary-terms");
    const ro = presenting();
    main.innerHTML = `${cultureTabs("glossary")}
      <section class="card"><h2>Speak like the locals</h2><p class="quiet">Acronyms, product and project names, and words that mean something particular here. Add them as you hear them; it's one of the quickest ways to fit in, and the list helps every new hire after you.</p>
        <input id="g-filter" placeholder="Filter" style="max-width:260px">
        <div class="tablewrap"><table class="data"><thead><tr><th>Term</th><th>Meaning</th><th>Used by</th>${ro ? "" : "<th></th>"}</tr></thead><tbody>${terms.map((t) => `<tr data-term="${t.id}" data-text="${esc((t.term + " " + (t.meaning || "") + " " + (t.used_by || "")).toLowerCase())}"><td><b>${esc(t.term)}</b></td><td>${esc(t.meaning || "")}</td><td class="quiet">${esc(t.used_by || "")}</td>${ro ? "" : `<td><button class="icon-btn" data-del title="Delete">${BA.icon("x")}</button></td>`}</tr>`).join("") || `<tr><td colspan="4" class="quiet">No terms yet.</td></tr>`}</tbody></table></div></section>
      ${ro ? "" : `<form id="add-term" class="card row"><input name="term" required placeholder="Term" style="max-width:200px"><input name="meaning" placeholder="What it means" style="flex:1;min-width:220px"><input name="used_by" placeholder="Who uses it" style="max-width:200px"><button class="btn primary" type="submit">Add</button></form>`}`;
    main.querySelector("#g-filter").oninput = (e) => { const q = e.target.value.toLowerCase(); main.querySelectorAll("[data-term]").forEach((r) => (r.style.display = r.dataset.text.includes(q) ? "" : "none")); };
    if (ro) return;
    main.querySelector("#add-term").onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/glossary-terms", { method: "POST", body: Object.fromEntries(new FormData(e.target)) }); BA.rerender(); });
    main.querySelectorAll("[data-term] [data-del]").forEach((b) => (b.onclick = BA.guard(async () => { await BA.api(`/api/glossary-terms/${b.closest("[data-term]").dataset.term}`, { method: "DELETE" }); BA.rerender(); })));
  }

  async function renderBrief(main) {
    const b = await BA.api("/api/culture/role-brief");
    const ro = presenting();
    if (ro) { main.innerHTML = `${cultureTabs("brief")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const lines = (v) => (v || []).join("\n");
    main.innerHTML = `${cultureTabs("brief")}
      <form id="brief" class="card"><h2>Role brief</h2><p class="quiet">What you were brought in to do, and the situation you inherited. It sits on the Culture overview so the day-to-day never crowds it out. Private. The outcomes you're expected to deliver, and what you can decide, go in <a href="#/first90/mandates">your mandate</a>.</p>
        <label>What I was brought in to do <span class="quiet">(one per line)</span><textarea name="focus" rows="5">${esc(lines(b.focus))}</textarea></label>
        <label>What they said they needed in the person <span class="quiet">(one per line)</span><textarea name="must_haves" rows="4">${esc(lines(b.must_haves))}</textarea></label>
        <label>The situation I inherited <span class="quiet">(Markdown)</span><textarea name="situation" rows="5">${esc(b.situation || "")}</textarea></label>
        <label>What to protect while I change things <span class="quiet">(one per line)</span><textarea name="keep" rows="3">${esc(lines(b.keep))}</textarea></label>
        <div class="actions"><button class="btn primary" type="submit">Save</button></div></form>`;
    const form = main.querySelector("#brief");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const split = (k) => fd.get(k).split("\n").map((x) => x.trim()).filter(Boolean);
      await BA.api("/api/culture/role-brief", { method: "PUT", body: { focus: split("focus"), must_haves: split("must_haves"), keep: split("keep"), situation: fd.get("situation") } });
      BA.toast("Saved.");
    });
  }

  // ---------------------------------------------------------------- Change requests

  const CR_SOURCES = ["leadership", "stakeholder", "product owner", "customer", "production issue", "another team", "the team"];
  const CR_URGENCY = ["next sprint is fine", "this sprint", "emergency"];
  const CR_IMPACT = ["doesn't affect the goal", "puts the goal at risk", "changes the goal", "makes the goal obsolete"];
  const CR_DECISIONS = [
    ["accepted with a swap", "Swap", "Take out unstarted work of about the same size, so the sprint stays achievable."],
    ["accepted without a swap", "Absorb", "Only for small work that fits in the slack you planned for."],
    ["deferred to the backlog", "Defer", "It goes to the backlog for a coming sprint planning. Say when it'll be looked at."],
    ["rejected", "Reject", "Not worth doing, or not now. Give the reason."],
    ["sprint cancelled", "Cancel the sprint", "Only when the sprint goal no longer makes sense. Then plan a new sprint."],
  ];
  const CR_STATUS_TONES = { received: "warn", assessing: "warn", decided: "good", closed: "" };
  const decisionTone = (d) => ({ "accepted with a swap": "accent", "accepted without a swap": "accent", "deferred to the backlog": "", rejected: "bad", "sprint cancelled": "bad" })[d] || "";
  const changeTabs = (active) => `<nav class="tabs">${[["", "Overview"], ["new", "New request"], ["all", "All requests"], ["policy", "Our policy"]]
    .map(([k, l]) => `<a href="#/changes${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${l}</a>`).join("")}</nav>`;
  const crRow = (c) => `<div class="item"><span class="pill ${CR_STATUS_TONES[c.status]}">${esc(c.status)}</span><a href="#/changes/${c.id}">${esc(c.title)}</a>${c.decision ? `<span class="pill ${decisionTone(c.decision)}">${esc(c.decision)}</span>` : ""}
    <span class="spacer"></span><span class="quiet">${esc(c.source)}${c.requested_by_name ? ` · ${esc(c.requested_by_name)}` : ""}${c.sprint_number ? ` · sprint ${c.sprint_number}` : ""} · ${BA.fmtDate(c.requested_on)}</span></div>`;

  BA.view("/changes", {
    title: "Change requests",
    async render(main, param) {
      if (param === "new") return renderNewChange(main);
      if (param === "all") return renderAllChanges(main);
      if (param === "policy") return renderChangePolicy(main);
      if (param) return renderChange(main, Number(param));
      const d = await BA.api("/api/change-requests/overview");
      const s = d.sprint;
      const maxPts = Math.max(1, ...d.churn.map((c) => Math.max(c.points_in, c.points_out)));
      main.innerHTML = `${changeTabs("")}
        ${s ? `<section class="card"><div class="row"><h2>Sprint ${s.sprint.number}${d.running ? "" : " (not running today)"}</h2><span class="spacer"></span>${s.days_left != null ? `<span class="quiet">${s.days_left} day${s.days_left === 1 ? "" : "s"} left</span>` : ""}</div>
          <p>${esc(s.sprint.goal || "No sprint goal set.")}</p>
          <div class="stat-row"><div><b>${s.capacity ?? "–"}</b><span>capacity</span></div><div><b>${s.committed ?? "–"}</b><span>committed</span></div><div><b>${s.in_sprint}</b><span>in the sprint now</span></div><div><b>${s.done}</b><span>done</span></div>
            <div><b>${s.changes.points_in}</b><span>points added by requests</span></div><div><b>${s.changes.points_out}</b><span>points swapped out</span></div></div></section>` : '<section class="card"><p class="quiet">No sprint yet. Requests can still be logged and deferred to the backlog.</p></section>'}
        <div class="cards">
          <section class="card"><h2>Waiting for a decision</h2>${d.open.map(crRow).join("") || '<p class="quiet">Nothing waiting.</p>'}${presenting() ? "" : '<p><a class="btn" href="#/changes/new">New request</a></p>'}</section>
          <section class="card"><h2>Decided, requester not told yet</h2>${d.untold.map(crRow).join("") || '<p class="quiet">Everyone has heard back.</p>'}</section>
        </div>
        <section class="card"><h2>Scope change by sprint</h2>${d.churn.some((c) => c.requests) ? `<div class="churn">${d.churn.map((c) => `<div class="churn-col" title="${c.requests} requests: ${c.accepted} accepted, ${c.deferred} deferred, ${c.rejected} rejected">
            <div class="churn-bars"><span class="in" style="height:${Math.round((c.points_in / maxPts) * 100)}%"></span><span class="out" style="height:${Math.round((c.points_out / maxPts) * 100)}%"></span></div>
            <b>S${c.number}</b><span class="quiet">${c.requests} req${c.changed_pct != null ? ` · ${c.changed_pct}%` : ""}</span></div>`).join("")}</div>
          <p class="quiet"><span class="legend in"></span> points added <span class="legend out"></span> points swapped out. The percentage is points added against what was committed at planning.</p>` : '<p class="quiet">No requests recorded against a sprint yet.</p>'}</section>
        <section class="card"><h2>Recently decided</h2>${d.recent.map(crRow).join("") || '<p class="quiet">None yet.</p>'}</section>
        ${d.policy ? "" : '<section class="card"><h2>Write your policy</h2><p class="quiet">Agree with your product owner how mid-sprint requests are handled, and share it with stakeholders before the first one arrives. <a href="#/changes/policy">Start from a draft</a>.</p></section>'}`;
    },
  });

  function changeFields(c, people) {
    return `<div class="grid2"><label>What's being asked<input name="title" value="${esc(c.title || "")}" required></label>
      <label>Asked by<select name="requested_by_id"><option value=""></option>${people.map((p) => `<option value="${p.id}"${p.id === c.requested_by_id ? " selected" : ""}>${esc(p.name)}</option>`).join("")}</select></label>
      <label>Where it came from<select name="source">${opts(CR_SOURCES, c.source || "stakeholder")}</select></label><label>Asked on<input type="date" name="requested_on" value="${esc(c.requested_on || BA.today())}" required></label>
      <label>How urgent<select name="urgency">${opts(CR_URGENCY, c.urgency || "this sprint")}</select></label><label>Needed by<input type="date" name="needed_by" value="${esc(c.needed_by || "")}"></label>
      <label>Rough size (points)<input type="number" min="0" name="points" value="${esc(c.points ?? "")}"></label><label>Effect on the sprint goal<select name="goal_impact"><option value=""></option>${opts(CR_IMPACT, c.goal_impact)}</select></label>
      <label>Jira keys<input name="jira_keys" value="${esc((c.jira_keys || []).join(", "))}" placeholder="Optional"></label></div>
      <label>Why it matters (the value, in the requester's words)<input name="value" value="${esc(c.value || "")}"></label>
      <label>Details<textarea name="description" rows="3">${esc(c.description || "")}</textarea></label>
      <label>Private notes<textarea name="notes" rows="2">${esc(c.notes || "")}</textarea></label>`;
  }
  const readChange = (form) => { const f = new FormData(form); return { title: f.get("title"), requested_by_id: numOrNull(f.get("requested_by_id")), source: f.get("source"), requested_on: f.get("requested_on"), urgency: f.get("urgency"),
    needed_by: f.get("needed_by") || null, points: numOrNull(f.get("points")), goal_impact: f.get("goal_impact") || null, jira_keys: keysIn(f.get("jira_keys")), value: f.get("value") || null, description: f.get("description") || null, notes: f.get("notes") || null }; };

  async function renderNewChange(main) {
    if (presenting()) { main.innerHTML = `${changeTabs("new")}<p class="empty">Hidden while presenting.</p>`; return; }
    const [people, current] = await Promise.all([BA.api("/api/people"), BA.api("/api/sprints/current")]);
    main.innerHTML = `${changeTabs("new")}<form id="new-cr" class="card"><h2>New change request</h2>
      <p class="quiet">Capture it as it arrives, even if the answer will be "next sprint". ${current ? `It will be weighed against Sprint ${current.number}.` : ""}</p>${changeFields({}, people)}
      <div class="actions"><button class="btn primary" type="submit">Save and assess</button></div></form>`;
    const form = main.querySelector("#new-cr");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const c = await BA.api("/api/change-requests", { method: "POST", body: { ...readChange(form), sprint_id: current ? current.id : null } });
      BA.go(`/changes/${c.id}`);
    });
  }

  async function renderChange(main, id) {
    const [a, people] = await Promise.all([BA.api(`/api/change-requests/${id}/assess`), BA.api("/api/people")]);
    const c = a.request, imp = a.impact, ro = presenting();
    const open = c.status === "received" || c.status === "assessing";
    const swapPicker = imp && imp.candidates.length ? `<div class="swap-list">${imp.candidates.map((i) => `<label class="check swap-item"><input type="checkbox" name="swap" value="${i.id}" data-pts="${i.points || 0}"> <span>${esc(i.title)}</span>${i.jira_key ? `<span class="jira-key">${esc(i.jira_key)}</span>` : ""}<span class="spacer"></span><span class="quiet">${i.points ?? "?"} pts${i.owner_name ? ` · ${esc(i.owner_name)}` : ""}</span></label>`).join("")}</div>
      <p class="swap-balance quiet" id="balance"></p>` : '<p class="quiet">No unfinished stories in the sprint to swap out.</p>';
    main.innerHTML = `${changeTabs("")}
      <section class="card"><div class="row"><h2>${esc(c.title)}</h2>${tonePill(c.status, CR_STATUS_TONES)}${c.decision ? `<span class="pill ${decisionTone(c.decision)}">${esc(c.decision)}</span>` : ""}<span class="spacer"></span>${BA.historyButton("change_request", c.id)}</div>
        <p class="quiet">${[`From ${esc(c.source)}${c.requested_by_name ? ` (${esc(c.requested_by_name)})` : ""}`, `asked ${BA.fmtDate(c.requested_on)}`, esc(c.urgency), c.needed_by ? `needed by ${BA.fmtDate(c.needed_by)}` : "", c.points != null ? `${c.points} points` : "not sized", c.goal_impact ? esc(c.goal_impact) : ""].filter(Boolean).join(" · ")}</p>
        ${c.value ? `<p><b>Why it matters:</b> ${esc(c.value)}</p>` : ""}${c.description ? BA.md(c.description) : ""}
        ${c.status === "decided" || c.status === "closed" ? `<p><b>Decision:</b> ${esc(c.decision)}${c.decided_by_name ? ` by ${esc(c.decided_by_name)}` : ""} on ${BA.fmtDate(c.decided_on)}.${c.decision_reason ? ` ${esc(c.decision_reason)}` : ""}${c.points_out ? ` ${c.points_out} points swapped out.` : ""}</p>
          <p>${c.communicated_on ? `Requester told ${BA.fmtDate(c.communicated_on)}.` : ro ? "Requester not told yet." : '<button class="btn primary" id="told">I\'ve told the requester</button>'}${c.backlog_item_id ? ` <a href="#/planning">See it in Sprint planning</a>` : ""}</p>` : ""}</section>
      ${imp ? `<section class="card"><h2>Sprint ${imp.sprint.number}: where it stands</h2><p>${esc(imp.sprint.goal || "No sprint goal set.")}</p>
        <div class="stat-row"><div><b>${imp.capacity ?? "–"}</b><span>capacity</span></div><div><b>${imp.in_sprint}</b><span>points in the sprint</span></div><div><b>${imp.done}</b><span>done</span></div><div><b>${imp.remaining}</b><span>left</span></div>${imp.days_left != null ? `<div><b>${imp.days_left}</b><span>days left</span></div>` : ""}</div>
        ${c.points != null && imp.capacity ? `<p class="quiet">Adding ${c.points} points without a swap would put the sprint at ${imp.in_sprint + c.points} of ${imp.capacity}.</p>` : ""}</section>` : ""}
      ${open && !ro ? `<form id="decide" class="card"><h2>Decide</h2>
        <p class="quiet">Ask: what is it worth, how big is it, and does it put the sprint goal at risk? The product owner makes the call, with the team.</p>
        <div class="decision-options">${CR_DECISIONS.map(([v, l, help], i) => `<label class="decision-opt"><input type="radio" name="decision" value="${v}"${i === 2 ? " checked" : ""}><span><b>${l}</b><small>${help}</small></span></label>`).join("")}</div>
        <div id="swap-box" hidden><h3>What comes out</h3><p class="quiet">Lowest priority first. Prefer stories nobody has started.</p>${swapPicker}</div>
        <div class="grid2"><label>Decided by<select name="decided_by_id"><option value=""></option>${people.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("")}</select></label>
          <label>Size (points)<input type="number" min="0" name="points" value="${esc(c.points ?? "")}"></label></div>
        <label>Reason <span class="quiet">(what the requester will hear)</span><textarea name="reason" rows="2"></textarea></label>
        <div class="actions"><button class="btn" type="button" id="assessing"${c.status === "assessing" ? " disabled" : ""}>Mark as being assessed</button><button class="btn primary" type="submit">Record and apply the decision</button></div></form>` : ""}
      ${ro ? "" : `<details class="card"><summary><b>Edit the request</b></summary><form id="edit-cr">${changeFields(c, people)}<div class="actions"><button class="btn danger left" type="button" id="del-cr">Delete</button><button class="btn primary" type="submit">Save</button></div></form></details>`}`;
    if (ro) return;
    const edit = main.querySelector("#edit-cr");
    edit.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/change-requests/${id}`, { method: "PATCH", body: readChange(edit) }); BA.toast("Saved."); BA.rerender(); });
    main.querySelector("#del-cr").onclick = BA.guard(async () => { if (!confirm("Delete this request? Stories it moved stay where they are.")) return; await BA.api(`/api/change-requests/${id}`, { method: "DELETE" }); BA.go("/changes"); });
    const toldBtn = main.querySelector("#told");
    if (toldBtn) toldBtn.onclick = BA.guard(async () => { await BA.api(`/api/change-requests/${id}/told`, { method: "POST", body: {} }); BA.rerender(); });
    const form = main.querySelector("#decide");
    if (!form) return;
    const swapBox = main.querySelector("#swap-box"), bal = main.querySelector("#balance");
    const update = () => {
      swapBox.hidden = form.elements.decision.value !== "accepted with a swap";
      if (!bal) return;
      const out = [...form.querySelectorAll("[name=swap]:checked")].reduce((n, x) => n + Number(x.dataset.pts), 0);
      const inPts = numOrNull(form.elements.points.value) || 0;
      bal.innerHTML = `Coming in: <b>${inPts}</b> points · going out: <b>${out}</b> points · ${out >= inPts ? "the sprint stays the same size or smaller" : `the sprint grows by ${inPts - out} points`}`;
    };
    form.querySelectorAll("[name=decision], [name=swap], [name=points]").forEach((el) => (el.oninput = el.onchange = update));
    update();
    main.querySelector("#assessing").onclick = BA.guard(async () => { await BA.api(`/api/change-requests/${id}`, { method: "PATCH", body: { status: "assessing" } }); BA.rerender(); });
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      const body = { decision: f.get("decision"), reason: f.get("reason"), decided_by_id: numOrNull(f.get("decided_by_id")), points: numOrNull(f.get("points")), swap_out_ids: f.getAll("swap").map(Number) };
      if (body.decision === "sprint cancelled" && !confirm("Cancel the sprint? Do this only when the sprint goal no longer makes sense. Nothing is moved automatically; plan a new sprint next.")) return;
      const r = await BA.api(`/api/change-requests/${id}/decide`, { method: "POST", body });
      BA.toast(r.warning || "Decision recorded. Now tell the requester.");
      BA.rerender();
    });
  }

  async function renderAllChanges(main) {
    const list = await BA.api("/api/change-requests");
    main.innerHTML = `${changeTabs("all")}<section class="card"><h2>All requests</h2>${list.map(crRow).join("") || '<p class="quiet">None yet.</p>'}</section>`;
  }

  async function renderChangePolicy(main) {
    const d = await BA.api("/api/change-requests/policy");
    const ro = presenting();
    main.innerHTML = `${changeTabs("policy")}
      <section class="card"><h2>How we handle requests during a sprint</h2>${d.policy ? BA.md(d.policy) : '<p class="quiet">No policy yet.</p>'}</section>
      ${ro ? "" : `<form id="policy" class="card"><h2>Edit</h2><p class="quiet">Agree it with your product owner and the team, then walk your stakeholders through it. Markdown works.</p>
        <textarea name="policy" rows="16">${esc(d.policy || "")}</textarea><div class="actions">${d.policy ? "" : '<button class="btn left" type="button" id="starter">Start from a draft</button>'}<button class="btn primary" type="submit">Save</button></div></form>`}`;
    if (ro) return;
    const form = main.querySelector("#policy");
    form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/change-requests/policy", { method: "PUT", body: { policy: form.elements.policy.value } }); BA.toast("Saved."); BA.rerender(); });
    const st = main.querySelector("#starter");
    if (st) st.onclick = () => { form.elements.policy.value = d.starter; };
  }

  // ---------------------------------------------------------------- First 90 days

  const CHANGE_AREAS = ["process", "ceremonies", "quality", "tooling", "communication", "roles", "other"];
  const CHANGE_STAGES = ["idea", "announced", "trial", "review", "adopted", "dropped"];
  const STAGE_TONES = { idea: "", announced: "accent", trial: "warn", review: "warn", adopted: "good", dropped: "" };
  const NEXT_STAGE = { idea: ["announced", "Announce it"], announced: ["trial", "Start the trial"], trial: ["review", "Review with the team"] };
  const AUTO_LABELS = { one_on_one: "a one-on-one logged under People", interview: "a listening tour conversation marked done", growth_goal: "a growth goal on their Manager tab", feedback: "feedback marked shared on their Manager tab", mandate: "their mandate marked agreed" };
  const f90Tabs = (active) => `<nav class="tabs">${[["", "Overview"], ["mandates", "Mandates"], ["situation", "Situation"], ["learning", "Learning agenda"], ["team", "The team I inherit"], ["changes", "Changes I'm bringing"], ["mentoring", "Mentoring"], ["working", "Working with me"]]
    .map(([k, l]) => `<a href="#/first90${k ? "/" + k : ""}" class="${k === active ? "active" : ""}">${l}</a>`).join("")}</nav>`;
  const f90Progress = (done, total) => `<span class="progress"><span style="width:${total ? Math.round((100 * done) / total) : 0}%"></span></span><span class="quiet">${done ?? 0} of ${total ?? 0}</span>`;
  const f90_dayLabel = (n) => n == null ? "not started" : n < 1 ? `starts in ${1 - n} day${1 - n === 1 ? "" : "s"}` : n > 90 ? `day ${n}, past 90` : `day ${n}`;

  BA.view("/first90", {
    title: "First 90 days",
    async render(main, param) {
      const views = { team: renderF90Team, changes: renderF90Changes, working: renderWorking, mandates: renderMandates, situation: renderSituation, learning: renderLearning, mentoring: renderMentoring };
      if (views[param]) return views[param](main);
      if (param && param.startsWith("mandate/")) return renderMandate(main, Number(param.split("/")[1]));
      const d = await BA.api("/api/first90/overview");
      const ch = d.changes;
      main.innerHTML = `${f90Tabs("")}
        <section class="card f90-head"><div class="row"><h2>${d.day ? `Day ${d.day} of 90` : "Set your start date"}</h2><span class="spacer"></span>${d.start_date ? `<span class="quiet">started ${BA.fmtDate(d.start_date)}</span>` : '<a class="btn" href="#/settings">Set start date</a>'}</div>
          ${d.day ? `<div class="f90-bar"><span style="width:${Math.min(100, Math.max(0, Math.round((d.day / 90) * 100)))}%"></span>${[30, 60, 90].map((n) => `<i style="left:${(n / 90) * 100}%">${n}</i>`).join("")}</div>` : ""}
          <p class="quiet">Three tracks that start together: yours, each new hire's, and the team you inherit, for whom this is the first 90 days with you.</p></section>
        ${d.momentum ? `<section class="card"><h2>Momentum</h2><p class="quiet">Signs that good things are happening, which is what builds credibility and trust.</p>
          <div class="stat-row"><div><b>${d.momentum.early_wins.done} of ${d.momentum.early_wins.total}</b><span><a href="#/plans">early wins</a> landed</span></div><div><b>${d.momentum.changes_kept}</b><span><a href="#/first90/changes">changes</a> kept</span></div>
            <div><b>${d.momentum.wins_30}</b><span><a href="#/status/log">wins</a> logged in 30 days</span></div><div><b>${d.momentum.practices_adopted}</b><span>practices other managers <a href="#/first90/mentoring">adopted</a></span></div>
            <div><b>${d.momentum.trust.now ?? "–"}</b><span><a href="#/culture/pulse">trust pulse</a>${d.momentum.trust.before != null ? ` (was ${d.momentum.trust.before})` : ""}</span></div></div></section>` : ""}
        <div class="cards f90-tracks">
          ${d.private ? `<section class="card"><h2>Me</h2>
            ${d.me.plans.map((p) => `<div class="item"><a href="#/plans">${esc(p.title)}</a><span class="spacer"></span>${f90Progress(p.done, p.total)}<span class="pill ${p.status === "presented" ? "good" : ""}">${esc(p.status)}</span></div>`).join("") || '<p class="quiet">No 30/60/90 plans yet. <a href="#/plans">Start them</a>.</p>'}
            <div class="item"><a href="#/listening">Listening tour</a><span class="spacer"></span>${f90Progress(d.me.listening.done, d.me.listening.total)}</div>
            <div class="item"><a href="#/coaching/reflect">Reflections</a><span class="spacer"></span><span class="quiet">${d.me.reflections} written</span></div>
            ${d.me.items_due.length ? `<h3>Due this week</h3>${d.me.items_due.map((i) => `<div class="item"><span>${esc(i.title)}</span><span class="spacer"></span><span class="quiet">${BA.fmtDate(i.due)}</span></div>`).join("")}` : ""}</section>` : ""}
          <section class="card"><h2>New hires</h2>${d.new_hires.map((h) => `<div class="item"><a href="#/onboarding/${h.id}">${esc(h.name || "")}</a><span class="quiet">${esc(h.role || "")}</span><span class="spacer"></span><span class="quiet">${f90_dayLabel(h.day)}</span>${f90Progress(h.done, h.total)}</div>`).join("") || '<p class="quiet">Nobody being onboarded. <a href="#/onboarding">Onboarding</a>.</p>'}</section>
        </div>
${d.private ? `<section class="card f90-team"><h2>The team I inherit</h2>${d.team.people.map((p) => `<div class="item"><a href="#/first90/team">${esc(p.name)}</a><span class="quiet">${p.next ? esc(p.next.title.split(":")[0]) : p.total ? "all done" : "not started"}</span><span class="spacer"></span>${p.late ? `<span class="pill bad">${p.late} late</span>` : ""}${f90Progress(p.done, p.total)}</div>`).join("")
            || (d.team.has_me ? '<p class="quiet">Nobody reports to you yet, apart from new hires. Set "Reports to" under People.</p>' : '<p class="quiet">Pick your own record under <a href="#/people">People</a> ("This is me") and set who reports to you.</p>')}</section>` : ""}
        ${d.private ? `<section class="card"><h2>Team check-ins</h2><div class="checkpoints">${d.checkpoints.map((c) => `<a class="checkpoint${c.done_on ? " done" : ""}" href="#/first90/team"><b>Day ${c.day}</b><span class="quiet">${c.due ? BA.fmtDate(c.due) : "–"}</span>
            <span>${c.done_on ? "held" : c.due && c.due < BA.today() ? "due" : "coming up"}</span><span class="quiet">${c.pulse_on ? `pulse ${BA.fmtDate(c.pulse_on)}` : "no pulse yet"}</span></a>`).join("")}</div></section>` : ""}
        <section class="card"><h2>Changes I'm bringing</h2><div class="stage-strip">${CHANGE_STAGES.map((s) => `<a href="#/first90/changes"><b>${ch[s]}</b><span>${s}</span></a>`).join("")}</div>
          ${d.working_with_me ? "" : '<p class="quiet">You haven\'t written "Working with me" yet. <a href="#/first90/working">Write it</a> before your first team meeting.</p>'}</section>`;
    },
  });

  async function renderF90Team(main) {
    const [d, rc] = await Promise.all([BA.api("/api/first90/team"), BA.api("/api/first90/report-conversations")]);
    const RC_TONES = { "not started": "", "in progress": "warn", settled: "good" };
    const rcCard = rc.hidden || !rc.reports.length ? "" : `<section class="card"><h2>The five conversations with each person</h2>
      <p class="quiet">Transition others as you'd want to be transitioned. Introduce the five conversations in week one, start with the situation and expectations, and mark the ones that are priorities. Click a cell to move it along.</p>
      <div class="tablewrap"><table class="data"><thead><tr><th>Person</th>${rc.topics.map((t) => `<th>${esc(t)}</th>`).join("")}</tr></thead><tbody>${rc.reports.map((r) => `<tr><td><a href="#/people/${r.id}">${esc(r.name)}</a></td>${rc.topics.map((t) => `<td><span class="row" style="gap:4px;flex-wrap:nowrap"><button type="button" class="pill ${RC_TONES[r.cells[t].status]}" data-rc="${r.id}" data-topic="${t}" data-status="${r.cells[t].status}" style="cursor:pointer;border:0">${esc(r.cells[t].status)}</button><button type="button" class="icon-btn" data-rcp="${r.id}" data-topic="${t}" data-prio="${r.cells[t].priority ? 1 : 0}" title="${r.cells[t].priority ? "A priority" : "Mark as a priority"}">${r.cells[t].priority ? "★" : "☆"}</button></span></td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`;
    if (d.hidden) { main.innerHTML = `${f90Tabs("team")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const unstarted = d.people.filter((p) => !p.total);
    main.innerHTML = `${f90Tabs("team")}
      <p class="quiet">The people who reported to someone else before you arrived. Their first 90 days with you run from your start date${d.start_date ? ` (${BA.fmtDate(d.start_date)}, day ${d.day})` : ""}. Some milestones tick themselves when the toolkit sees them happen.</p>
      ${!d.start_date ? '<section class="card"><p>Set your start date in <a href="#/settings">Settings</a> to date the milestones.</p></section>' : ""}
      ${unstarted.length ? `<section class="card"><div class="row"><span>${unstarted.map((p) => esc(p.name)).join(", ")} ${unstarted.length === 1 ? "has" : "have"} no milestones yet.</span><span class="spacer"></span><button class="btn primary" id="f90-start">Give them the milestones</button></div></section>` : ""}
      ${d.people.filter((p) => p.total).map((p) => `<section class="card"><div class="row"><h2><a href="#/people/${p.id}">${esc(p.name)}</a></h2><span class="quiet">${esc(p.role || "")}</span><span class="spacer"></span>${p.late ? `<span class="pill bad">${p.late} late</span>` : ""}${f90Progress(p.done, p.total)}</div>
        ${p.milestones.map((m) => `<div class="item milestone${m.done ? " done" : ""}" data-ms="${m.id}"><label class="check"><input type="checkbox"${m.done ? " checked" : ""}></label>
          <span class="ms-day">${BA.roleDay(m.due_day)}</span><span>${esc(m.title)}</span><span class="spacer"></span>
          ${m.seen_in_data ? `<span class="quiet" title="Seen: ${esc(AUTO_LABELS[m.auto] || "")}">seen ${BA.fmtDate(m.done)}</span>` : m.done ? `<span class="quiet">${BA.fmtDate(m.done)}</span>` : m.late ? `<span class="pill bad">due ${BA.fmtDate(m.due)}</span>` : `<span class="quiet">${m.due ? BA.fmtDate(m.due) : ""}</span>`}</div>`).join("")}</section>`).join("")}
      ${!d.people.length ? `<section class="card"><p class="quiet">${d.has_me ? 'Nobody reports to you yet, apart from new hires. Set "Reports to" on each person under People.' : 'Pick your own record under <a href="#/people">People</a> ("This is me"), then set who reports to you.'}</p></section>` : ""}
      ${rcCard}
      <section class="card"><h2>Team check-ins at days 30, 60 and 90</h2><p class="quiet">Take a <a href="#/culture/pulse">trust pulse</a> near each one, ask the listening tour questions again, and tell the team what changed because of what they said.</p>
        ${d.checkpoints.map((c) => `<details class="plan-item${c.done_on ? " dropped" : ""}" data-cp="${c.day}"${!c.done_on && c.due && c.due <= BA.today() ? " open" : ""}><summary><b>Day ${c.day}</b><span class="quiet">${c.due ? BA.fmtDate(c.due) : ""}</span><span class="spacer"></span>${c.pulse_on ? `<span class="pill good">pulse ${BA.fmtDate(c.pulse_on)}</span>` : '<span class="pill">no pulse</span>'}${c.done_on ? `<span class="pill good">held ${BA.fmtDate(c.done_on)}</span>` : ""}</summary>
          <form><label>What I heard<textarea name="heard" rows="2">${esc(c.heard || "")}</textarea></label><label>What changed because of it <span class="quiet">(tell the team this)</span><textarea name="changed" rows="2">${esc(c.changed || "")}</textarea></label>
          <label>How I'm adapting <span class="quiet">(an informal 360: ask your manager and a few peers)</span><textarea name="adapting" rows="2">${esc(c.adapting || "")}</textarea></label>
          <label>Notes<textarea name="notes" rows="2">${esc(c.notes || "")}</textarea></label><div class="actions"><label class="left">Held on <input type="date" name="done_on" value="${esc(c.done_on || "")}"></label><button class="btn primary" type="submit">Save</button></div></form></details>`).join("")}</section>
      <details class="card"><summary><b>Milestone template</b></summary><p class="quiet">What every inherited team member gets. Changes apply to people you start from now on. One per line: day, then the milestone.</p>
        <form id="tpl"><textarea name="tpl" rows="10" class="mono">${esc(d.template.map((m) => `${m.due_day} | ${m.title}${m.auto ? ` | auto:${m.auto}` : ""}`).join("\n"))}</textarea><div class="actions"><button class="btn primary" type="submit">Save template</button></div></form></details>`;
    const st = main.querySelector("#f90-start");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/first90/team/start", { method: "POST", body: {} }); BA.rerender(); });
    const cell = (pid, t) => rc.reports.find((r) => r.id === Number(pid)).cells[t];
    main.querySelectorAll("[data-rc]").forEach((b) => (b.onclick = BA.guard(async () => {
      const next = rc.statuses[(rc.statuses.indexOf(b.dataset.status) + 1) % rc.statuses.length];
      await BA.api(`/api/first90/report-conversations/${b.dataset.rc}/${b.dataset.topic}`, { method: "PUT", body: { status: next, priority: cell(b.dataset.rc, b.dataset.topic).priority } }); BA.rerender(); })));
    main.querySelectorAll("[data-rcp]").forEach((b) => (b.onclick = BA.guard(async () => {
      await BA.api(`/api/first90/report-conversations/${b.dataset.rcp}/${b.dataset.topic}`, { method: "PUT", body: { status: cell(b.dataset.rcp, b.dataset.topic).status, priority: b.dataset.prio !== "1" } }); BA.rerender(); })));
    main.querySelectorAll("[data-ms] input").forEach((cb) => (cb.onchange = BA.guard(async () => {
      await BA.api(`/api/first90-milestones/${cb.closest("[data-ms]").dataset.ms}`, { method: "PATCH", body: cb.checked ? { done_on: BA.today(), not_done: false } : { done_on: null, not_done: true } });
      BA.rerender();
    })));
    main.querySelectorAll("[data-cp]").forEach((det) => {
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const f = new FormData(form); await BA.api(`/api/first90/checkpoints/${det.dataset.cp}`, { method: "PUT", body: { heard: f.get("heard"), changed: f.get("changed"), adapting: f.get("adapting"), notes: f.get("notes"), done_on: f.get("done_on") || null } }); BA.toast("Saved."); BA.rerender(); });
    });
    const tpl = main.querySelector("#tpl");
    tpl.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const items = tpl.elements.tpl.value.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
        const [day, title, auto] = l.split("|").map((x) => x.trim());
        return { due_day: Number(day), title, auto: auto && auto.startsWith("auto:") ? auto.slice(5) : null };
      });
      await BA.api("/api/first90/template", { method: "PUT", body: { items } });
      BA.toast("Template saved.");
    });
  }

  async function renderF90Changes(main) {
    const list = await BA.api("/api/team-changes");
    const ro = presenting();
    const fields = (c = {}) => `<div class="grid2"><label>The change<input name="title" value="${esc(c.title || "")}" required></label><label>Area<select name="area">${opts(CHANGE_AREAS, c.area || "process")}</select></label>
        <label>Review with the team on<input type="date" name="review_on" value="${esc(c.review_on || "")}"></label>
        <label>Wave <span class="quiet">(first: early wins; second: deeper change; third: fine-tuning)</span><select name="wave"><option value=""></option>${[[1, "First"], [2, "Second"], [3, "Fine-tuning"]].map(([v, l]) => `<option value="${v}"${c.wave === v ? " selected" : ""}>${l}</option>`).join("")}</select></label></div>
      <label>Why: the problem it solves <span class="quiet">(in the team's words if you can)</span><textarea name="why" rows="2">${esc(c.why || "")}</textarea></label>
      <label>What changes for people day to day<textarea name="what_changes" rows="2">${esc(c.what_changes || "")}</textarea></label>
      <label>How we'll try it, and how we'll know it helped<textarea name="how_we_try" rows="2">${esc(c.how_we_try || "")}</textarea></label>
      ${c.id ? `<label>What the team said<textarea name="team_feedback" rows="2">${esc(c.team_feedback || "")}</textarea></label><label>Outcome<input name="outcome" value="${esc(c.outcome || "")}"></label>` : ""}
      <label>Private notes<textarea name="notes" rows="2">${esc(c.notes || "")}</textarea></label>`;
    const read = (form) => { const f = new FormData(form); const o = {}; for (const k of ["title", "area", "why", "what_changes", "how_we_try", "team_feedback", "outcome", "notes"]) if (form.elements[k]) o[k] = f.get(k) || null; if (form.elements.wave) o.wave = f.get("wave") ? Number(f.get("wave")) : null; o.review_on = f.get("review_on") || null; return o; };
    const card = (c) => `<details class="plan-item change-card" data-ch="${c.id}"><summary><span class="pill ${STAGE_TONES[c.status]}">${esc(c.status)}</span><b>${esc(c.title)}</b><span class="quiet">${esc(c.area)}${c.wave ? ` · wave ${c.wave}` : ""}</span><span class="spacer"></span>
        <span class="quiet">${c.status === "trial" && c.review_on ? `review ${BA.fmtDate(c.review_on)}` : c.decided_on ? BA.fmtDate(c.decided_on) : c.trial_start ? `trial from ${BA.fmtDate(c.trial_start)}` : c.announced_on ? `announced ${BA.fmtDate(c.announced_on)}` : ""}</span></summary>
      ${c.why ? `<p><b>Why:</b> ${esc(c.why)}</p>` : ""}${c.what_changes ? `<p><b>What changes:</b> ${esc(c.what_changes)}</p>` : ""}${c.how_we_try ? `<p><b>How we'll try it:</b> ${esc(c.how_we_try)}</p>` : ""}
      ${c.team_feedback ? `<p><b>What the team said:</b> ${esc(c.team_feedback)}</p>` : ""}${c.outcome ? `<p><b>Outcome:</b> ${esc(c.outcome)}</p>` : ""}
      ${ro ? "" : `<div class="actions">${NEXT_STAGE[c.status] ? `<button class="btn primary" data-next="${NEXT_STAGE[c.status][0]}">${NEXT_STAGE[c.status][1]}</button>` : ""}
        ${["trial", "review"].includes(c.status) ? '<button class="btn" data-next="adopted">Keep it</button><button class="btn" data-next="dropped">Drop it</button>' : ""}</div>
        <details><summary class="quiet">Edit</summary><form>${fields(c)}<div class="actions"><button class="btn danger left" type="button" data-del>Delete</button>${BA.historyButton("team_change", c.id)}<button class="btn primary" type="submit">Save</button></div></form></details>`}</details>`;
    const live = list.filter((c) => !["adopted", "dropped"].includes(c.status)), done = list.filter((c) => ["adopted", "dropped"].includes(c.status));
    main.innerHTML = `${f90Tabs("changes")}
      <p class="quiet">Every change you bring, where the team can see it: announced with the reason, tried for a set time, reviewed together, then kept or dropped. This page can be shown to the team while presenting.</p>
      ${!ro && list.filter((c) => ["announced", "trial", "review"].includes(c.status)).length > 3 ? '<p class="callout warn">More than three changes are under way at once. If you keep changing things, nobody can tell what\'s working, and people tire. Let some settle before starting more.</p>' : ""}
      <section class="card"><h2>In progress</h2>${live.map(card).join("") || '<p class="quiet">Nothing yet.</p>'}</section>
      ${done.length ? `<section class="card"><h2>Decided</h2>${done.map(card).join("")}</section>` : ""}
      ${ro ? "" : `<form id="add-ch" class="card"><h2>A change to bring</h2>${fields()}<div class="actions"><button class="btn primary" type="submit">Add as an idea</button></div></form>`}`;
    if (ro) return;
    const add = main.querySelector("#add-ch");
    add.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/team-changes", { method: "POST", body: { ...read(add), position: list.length } }); BA.rerender(); });
    main.querySelectorAll("[data-ch]").forEach((det) => {
      const id = det.dataset.ch, c = list.find((x) => x.id === Number(id));
      det.querySelectorAll("[data-next]").forEach((b) => (b.onclick = BA.guard(async () => {
        const status = b.dataset.next, body = { status };
        if (status === "adopted" || status === "dropped") {
          const outcome = prompt(status === "adopted" ? "What did the team decide, and why keep it?" : "Why drop it? Say what you learned.", c.outcome || "");
          if (outcome === null) return;
          body.outcome = outcome;
        }
        await BA.api(`/api/team-changes/${id}/advance`, { method: "POST", body });
        BA.toast(status === "trial" ? "Trial started. A review date is set about two sprints out." : "Updated.");
        BA.rerender();
      })));
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api(`/api/team-changes/${id}`, { method: "PATCH", body: read(form) }); BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this change? Dropping it keeps the record.")) return; await BA.api(`/api/team-changes/${id}`, { method: "DELETE" }); BA.rerender(); });
    });
  }

  async function renderWorking(main) {
    const d = await BA.api("/api/first90/working-with-me");
    const ro = presenting();
    main.innerHTML = `${f90Tabs("working")}
      <section class="card working-doc">${d.text ? BA.md(d.text) : '<p class="quiet">Not written yet.</p>'}</section>
      ${ro ? "" : `<form id="ww" class="card"><h2>Edit</h2><p class="quiet">A page about how you work, what you've been asked to do, and how you'll bring change, in your own words. Share it in week one and ask what they'd add. It can be shown while presenting.</p>
        <textarea name="text" rows="20">${esc(d.text || "")}</textarea>
        <div class="actions">${d.text ? '<button class="btn left" type="button" id="ww-copy">Copy Markdown</button>' : '<button class="btn left" type="button" id="ww-starter">Start from a draft</button>'}<button class="btn primary" type="submit">Save</button></div></form>`}`;
    if (ro) return;
    const form = main.querySelector("#ww");
    form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/first90/working-with-me", { method: "PUT", body: { text: form.elements.text.value } }); BA.toast("Saved."); BA.rerender(); });
    const st = main.querySelector("#ww-starter");
    if (st) st.onclick = () => { form.elements.text.value = d.starter; };
    const cp = main.querySelector("#ww-copy");
    if (cp) cp.onclick = BA.guard(async () => { await navigator.clipboard.writeText(d.text); BA.toast("Copied."); });
  }

  // ---- Mandates ----

  const AUTHORITY = ["to clarify", "I decide", "I decide and inform", "I recommend, someone else decides", "I'm consulted", "not mine"];
  const AUTH_TONES = { "to clarify": "warn", "I decide": "good", "I decide and inform": "good", "I recommend, someone else decides": "accent", "I'm consulted": "", "not mine": "" };
  const M_STATUS = ["open", "on track", "at risk", "done", "dropped"];
  const M_TONES = { open: "", "on track": "good", "at risk": "bad", done: "good", dropped: "" };
  const MANDATE_TONES = { draft: "", discussed: "warn", agreed: "good" };

  async function renderMandates(main) {
    const d = await BA.api("/api/mandates/overview");
    const ro = presenting(), m = d.mine;
    main.innerHTML = `${f90Tabs("mandates")}
      <p class="quiet">A mandate is the shared understanding of a role: what it's for, what it's expected to deliver and by when, what it can decide alone, and what it can only recommend. Work out yours with your manager early, and each report's with them.</p>
      <section class="card"><div class="row"><h2>My mandate</h2>${m ? tonePill(m.status, MANDATE_TONES) : ""}<span class="spacer"></span>${m ? `<a class="btn" href="#/first90/mandate/${m.id}">Open</a>` : ""}</div>
        ${m ? `${m.purpose ? `<p>${esc(m.purpose)}</p>` : '<p class="quiet">No purpose written yet.</p>'}
          <div class="stat-row"><div><b>${m.outcomes.length}</b><span>expected outcomes</span></div><div><b>${m.done}</b><span>done</span></div><div><b>${m.at_risk}</b><span>at risk</span></div><div><b>${m.to_clarify}</b><span>decisions to clarify</span></div></div>
          ${m.status === "agreed" ? `<p class="quiet">Agreed${m.agreed_with_name ? ` with ${esc(m.agreed_with_name)}` : ""} on ${BA.fmtDate(m.agreed_on)}. Review ${BA.fmtDate(m.review_on)}.</p>` : ""}`
        : d.me ? (ro ? '<p class="quiet">Not started.</p>' : '<p class="quiet">Not started. It begins with a list of common decision areas, each marked "to clarify". Set the authority you plan to propose for each before you meet your manager.</p><button class="btn primary" id="start-mine">Start my mandate</button>')
        : '<p class="quiet">Pick your own record under <a href="#/people">People</a> ("This is me") first.</p>'}</section>
      ${d.reports ? `<section class="card"><h2>My team's mandates</h2><p class="quiet">Agreeing one completes that person's "agree their mandate" milestone in First 90 days.</p>
        ${d.reports.map((r) => `<div class="item"><a href="#/people/${r.person_id}">${esc(r.name)}</a>${r.placeholder ? '<span class="pill warn">placeholder</span>' : ""}<span class="quiet">${esc(r.role || "")}</span><span class="spacer"></span>
          ${r.mandate ? `${tonePill(r.mandate.status, MANDATE_TONES)}<span class="quiet">${r.mandate.to_clarify ? `${r.mandate.to_clarify} to clarify` : ""}</span><a class="btn" href="#/first90/mandate/${r.mandate.id}">Open</a>` : ro ? "" : `<button class="btn" data-start="${r.person_id}">Start</button>`}</div>`).join("") || '<p class="quiet">Nobody reports to you yet.</p>'}</section>` : ""}`;
    if (d.reports !== undefined) {
      const [convs, focus] = await Promise.all([BA.api("/api/boss-conversations"), BA.api("/api/first90/manager-focus")]);
      const CONV_TONES = { "not started": "", "in progress": "warn", settled: "good" };
      const fbox = document.createElement("section");
      fbox.className = "card";
      const three = (name, list, ph) => [0, 1, 2].map((i) => `<input name="${name}" value="${esc(list[i] || "")}" placeholder="${ph} ${i + 1}" style="margin-bottom:4px">`).join("");
      fbox.innerHTML = ro ? `<h2>My manager's top three</h2>${focus.hidden ? "" : `<ol>${focus.priorities.map((p) => `<li>${esc(p)}</li>`).join("")}</ol>`}` : `<h2>Keep it focused</h2>
        <form id="mfocus"><div class="grid2"><div><b>My manager's top three priorities</b><p class="quiet">Aim early wins at these and touch on them every time you talk.</p>${three("priorities", focus.priorities, "[Placeholder: priority]")}</div>
          <div><b>Three things for our next one-on-one</b><p class="quiet">At most three. Everything else goes in the written note.</p>${three("next_three", focus.next_three, "[Placeholder: thing]")}</div></div>
          <label><b>How my manager likes to work</b> <span class="quiet">(how they prefer to communicate, how often, how much detail, and which decisions they want to be consulted on. Ask someone they trust; then adapt.)</span><textarea name="style" rows="2">${esc(focus.style)}</textarea></label>
          <label><b>What my manager is protective of</b> <span class="quiet">(private: things they built, people they're loyal to. Find out before proposing changes; float ideas as trial balloons.)</span><textarea name="protective" rows="2">${esc(focus.protective)}</textarea></label>
          <p><b>Resource menu</b> <span class="quiet">Lay out what different levels of support buy, all at once and early, rather than going back for more.</span></p>
          <div class="tablewrap"><table class="data"><thead><tr><th>Option</th><th>What it costs</th><th>What it delivers</th></tr></thead><tbody>${[...focus.menu, {}, {}].slice(0, Math.max(3, focus.menu.length + 1)).map((r) => `<tr class="menu-row"><td><input name="m_option" value="${esc(r.option || "")}" placeholder="[Placeholder: e.g. current team]"></td><td><input name="m_cost" value="${esc(r.cost || "")}" placeholder="[Placeholder]"></td><td><input name="m_delivers" value="${esc(r.delivers || "")}" placeholder="[Placeholder]"></td></tr>`).join("")}</tbody></table></div>
          <div class="actions">${focus.menu.length ? '<button class="btn" type="button" id="menu-md">Copy menu as Markdown</button>' : ""}<button class="btn primary" type="submit">Save</button></div></form>
        <p><b>What to ask your manager for</b> <span class="quiet">(${focus.kinds.length ? `given your ${focus.kinds.map(esc).join(", ")} areas` : "set situations to tailor this"})</span></p><ul>${focus.asks.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>
        <p class="quiet">Don't stay away, don't surprise them, and bring a plan, not just a problem. <a href="#/coaching/your-manager">More</a></p>`;
      main.appendChild(fbox);
      const mf = fbox.querySelector("#mfocus");
      if (mf) mf.onsubmit = BA.guard(async (e) => { e.preventDefault(); const f = new FormData(mf);
        const menu = [...mf.querySelectorAll(".menu-row")].map((r) => ({ option: r.querySelector('[name="m_option"]').value, cost: r.querySelector('[name="m_cost"]').value, delivers: r.querySelector('[name="m_delivers"]').value }));
        await BA.api("/api/first90/manager-focus", { method: "PUT", body: { priorities: f.getAll("priorities"), next_three: f.getAll("next_three"), protective: f.get("protective"), style: f.get("style"), menu } }); BA.toast("Saved."); BA.rerender(); });
      const mmd = fbox.querySelector("#menu-md");
      if (mmd) mmd.onclick = () => { navigator.clipboard.writeText(["| Option | What it costs | What it delivers |", "| --- | --- | --- |", ...focus.menu.map((r) => `| ${r.option} | ${r.cost} | ${r.delivers} |`)].join("\n")); BA.toast("Copied."); };
      const box = document.createElement("section");
      box.className = "card";
      box.innerHTML = `<h2>Conversations with my manager</h2><p class="quiet">The conversations that set you up to succeed. Start with the situation, expectations and working style; take up resources once you've learned enough to ask well; bring up your development once the relationship is established, a few months in. Write down what was agreed, and come back to them.</p>
        ${convs.length ? `<div class="tablewrap"><table class="data"><thead><tr><th>Conversation</th><th>Where it stands</th><th>Next 30 days</th></tr></thead><tbody>${convs.map((c) => `<tr><td>${esc(c.topic)}</td><td><span class="pill ${CONV_TONES[c.status || "not started"]}">${esc(c.status || "not started")}</span></td><td class="quiet">${esc(c.next_30 || "")}</td></tr>`).join("")}</tbody></table></div>` : ""}
        ${convs.map((c) => `<details class="plan-item${c.held_on ? "" : ""}" data-conv="${c.id}"><summary>${c.held_on ? '<span class="pill good">held</span>' : '<span class="pill">not yet</span>'}<b>${esc(c.topic)}</b><span class="spacer"></span><span class="quiet">${c.held_on ? BA.fmtDate(c.held_on) : ""}${c.next_on ? ` · next ${BA.fmtDate(c.next_on)}` : ""}</span></summary>
          <p class="quiet">${esc(c.prompt || "")}</p>${ro ? (c.agreed ? BA.md(c.agreed) : "") : `<form><div class="grid2"><label>Held on<input type="date" name="held_on" value="${esc(c.held_on || "")}"></label><label>Come back to it on<input type="date" name="next_on" value="${esc(c.next_on || "")}"></label></div>
          <label>Where it stands<select name="status">${opts(["not started", "in progress", "settled"], c.status || "not started")}</select></label>
          <label>What we agreed<textarea name="agreed" rows="2">${esc(c.agreed || "")}</textarea></label><label>Still open<textarea name="open_points" rows="2">${esc(c.open_points || "")}</textarea></label>
          <label>Priorities for the next 30 days<textarea name="next_30" rows="2">${esc(c.next_30 || "")}</textarea></label>
          <div class="actions"><button class="btn primary" type="submit">Save</button></div></form>`}</details>`).join("") || (ro ? '<p class="quiet">None yet.</p>' : '<button class="btn" id="conv-start">List the conversations</button>')}
        <p class="quiet">Agreeing the plan itself is marked on <a href="#/plans">30/60/90 plans</a> with "Mark agreed".</p>`;
      main.appendChild(box);
      const cs = box.querySelector("#conv-start");
      if (cs) cs.onclick = BA.guard(async () => { await BA.api("/api/boss-conversations/starter", { method: "POST" }); BA.rerender(); });
      box.querySelectorAll("[data-conv]").forEach((det) => {
        const form = det.querySelector("form");
        if (form) form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const f = new FormData(form); await BA.api(`/api/boss-conversations/${det.dataset.conv}`, { method: "PATCH", body: { held_on: f.get("held_on") || null, next_on: f.get("next_on") || null, status: f.get("status"), agreed: f.get("agreed") || null, open_points: f.get("open_points") || null, next_30: f.get("next_30") || null } }); BA.toast("Saved."); BA.rerender(); });
      });
    }
    const sm = main.querySelector("#start-mine");
    if (sm) sm.onclick = BA.guard(async () => { const r = await BA.api("/api/mandates/mine", { method: "POST", body: {} }); BA.go(`/first90/mandate/${r.id}`); });
    main.querySelectorAll("[data-start]").forEach((b) => (b.onclick = BA.guard(async () => { const r = await BA.api(`/api/mandates/for/${b.dataset.start}`, { method: "POST", body: {} }); BA.go(`/first90/mandate/${r.id}`); })));
  }

  async function renderMandate(main, id) {
    const m = await BA.api(`/api/mandates/${id}/full`);
    if (m.hidden) { main.innerHTML = `${f90Tabs("mandates")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const ro = presenting();
    document.getElementById("view-title").textContent = m.mine ? "My mandate" : `${m.person_name}'s mandate`;
    const textBlock = (key, label, help, rows = 3) => ro ? (m[key] ? `<h3>${label}</h3>${BA.md(m[key])}` : "") : `<label>${label} <span class="quiet">${help}</span><textarea name="${key}" rows="${rows}">${esc(m[key] || "")}</textarea></label>`;
    main.innerHTML = `${f90Tabs("mandates")}
      <section class="card"><div class="row"><h2>${m.mine ? "My mandate" : esc(m.person_name)}</h2>${tonePill(m.status, MANDATE_TONES)}<span class="spacer"></span>${ro ? "" : `${BA.historyButton("mandate", m.id)}<button class="btn" id="m-copy">Copy as Markdown</button>
          ${m.status === "draft" ? '<button class="btn" id="m-discussed">Mark discussed</button>' : ""}${m.status !== "agreed" ? `<button class="btn primary" id="m-agree">Mark agreed</button>` : ""}`}</div>
        <p class="quiet">${m.status === "agreed" ? `Agreed${m.agreed_with_name ? ` with ${esc(m.agreed_with_name)}` : ""} on ${BA.fmtDate(m.agreed_on)}. Review on ${BA.fmtDate(m.review_on)}.` : m.mine ? "Bring this to your manager as your proposal: the outcomes you recommend and, decision by decision, the authority you propose. Invite changes, then mark it agreed." : "Work this out with them, not for them, then mark it agreed."}</p>
        <form id="m-text">${textBlock("purpose", "What the role is for", "(a sentence or two)", 2)}</form></section>
      <section class="card"><h2>What success looks like</h2><p class="quiet">The outcomes expected, how you'll know, and roughly by when (day of your first 90).</p>
        ${m.outcomes.map((o) => `<div class="item mandate-row" data-item="${o.id}">${ro ? `<span>${esc(o.text)}</span><span class="quiet">${esc(o.measure || "")}</span><span class="spacer"></span>${tonePill(o.status, M_TONES)}` :
          `<input name="text" value="${esc(o.text)}" style="flex:2;min-width:200px"><input name="measure" value="${esc(o.measure || "")}" placeholder="How we'll know" style="flex:1.4;min-width:150px">
           <input name="due_day" type="number" min="1" value="${esc(o.due_day ?? "")}" placeholder="Day" style="width:76px" title="${o.due ? BA.fmtDate(o.due) : "Day of your first 90"}"><select name="status" style="max-width:120px">${opts(M_STATUS, o.status)}</select><button class="icon-btn" data-del title="Remove">${BA.icon("x")}</button>`}</div>`).join("") || '<p class="quiet">None yet.</p>'}
        ${ro ? "" : `<form id="add-outcome" class="row" style="margin-top:8px"><input name="text" required placeholder="An outcome, such as: Scrum running where it's missing" style="flex:1;min-width:240px"><button class="btn" type="submit">Add</button>
          ${m.mine ? '<button class="btn" type="button" id="from-brief">Add from my Role brief</button>' : ""}</form>`}</section>
      <section class="card"><h2>Decisions</h2><p class="quiet">For each area: can ${m.mine ? "you" : "they"} decide alone, decide and then inform, only recommend, or just be consulted? "To clarify" means it hasn't been discussed yet.</p>
        ${m.decisions.map((dd) => `<div class="item mandate-row" data-item="${dd.id}">${ro ? `<span>${esc(dd.text)}</span><span class="spacer"></span>${tonePill(dd.authority || "to clarify", AUTH_TONES)}` :
          `<input name="text" value="${esc(dd.text)}" style="flex:2;min-width:200px"><select name="authority" style="max-width:260px">${opts(AUTHORITY, dd.authority || "to clarify")}</select><button class="icon-btn" data-del title="Remove">${BA.icon("x")}</button>`}</div>`).join("") || '<p class="quiet">None yet.</p>'}
        ${ro ? "" : '<form id="add-decision" class="row" style="margin-top:8px"><input name="text" required placeholder="A decision area" style="flex:1;min-width:240px"><button class="btn" type="submit">Add</button></form>'}</section>
      <section class="card"><form id="m-more">${textBlock("boundaries", "Boundaries", "(what's out of scope, or needs sign-off)")}${textBlock("resources", "Resources and support", "(people, budget, tools, help)")}
        ${textBlock("questions", "Proposals and open questions", m.mine ? "(what you'll recommend, and the few things only your manager can answer)" : "(what you'll propose to them, and what you need to hear from them)", 8)}${ro ? "" : `${textBlock("notes", "Private notes", "")}<div class="actions"><button class="btn primary" type="submit">Save</button></div>`}</form></section>
      ${m.mine && !ro ? `<details class="card"><summary><b>Import from a file</b></summary><p class="quiet">Fill this mandate from a JSON file with purpose, resources, boundaries, questions, outcomes and decisions. Anything already here is kept; nothing is added twice.</p>
        <input type="file" id="m-file" accept=".json,application/json"><textarea id="m-json" rows="5" class="mono"></textarea><div class="actions"><button class="btn primary" id="m-import">Import</button></div></details>` : ""}`;
    if (ro) return;
    const patchItem = (row) => BA.guard(async () => {
      const body = {};
      row.querySelectorAll("input, select").forEach((el) => (body[el.name] = el.name === "due_day" ? numOrNull(el.value) : el.value || null));
      await BA.api(`/api/mandate-items/${row.dataset.item}`, { method: "PATCH", body });
      BA.toast("Saved.");
    });
    main.querySelectorAll("[data-item]").forEach((row) => {
      row.querySelectorAll("input, select").forEach((el) => (el.onchange = patchItem(row)));
      row.querySelector("[data-del]").onclick = BA.guard(async () => { await BA.api(`/api/mandate-items/${row.dataset.item}`, { method: "DELETE" }); BA.rerender(); });
    });
    const addItem = (form, kind) => (form.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/mandate-items", { method: "POST", body: { mandate_id: id, kind, text: form.elements.text.value, position: 99, ...(kind === "decision" ? { authority: "to clarify" } : {}) } }); BA.rerender(); }));
    addItem(main.querySelector("#add-outcome"), "outcome");
    addItem(main.querySelector("#add-decision"), "decision");
    const saveText = (form) => BA.guard(async (e) => { if (e) e.preventDefault(); const body = {}; form.querySelectorAll("textarea").forEach((el) => (body[el.name] = el.value || null)); await BA.api(`/api/mandates/${id}`, { method: "PATCH", body }); BA.toast("Saved."); });
    main.querySelector("#m-more").onsubmit = saveText(main.querySelector("#m-more"));
    main.querySelector("#m-text textarea").onchange = saveText(main.querySelector("#m-text"));
    const fb = main.querySelector("#from-brief");
    if (fb) fb.onclick = BA.guard(async () => { const r = await BA.api("/api/mandates/mine/from-brief", { method: "POST" }); BA.toast(r.added ? `Added ${r.added} from the Role brief.` : "Nothing new in the Role brief."); BA.rerender(); });
    const disc = main.querySelector("#m-discussed");
    if (disc) disc.onclick = BA.guard(async () => { await BA.api(`/api/mandates/${id}`, { method: "PATCH", body: { status: "discussed" } }); BA.rerender(); });
    const ag = main.querySelector("#m-agree");
    if (ag) ag.onclick = BA.guard(async () => {
      if (m.to_clarify && !confirm(`${m.to_clarify} decision area${m.to_clarify === 1 ? " is" : "s are"} still "to clarify". Mark agreed anyway?`)) return;
      await BA.api(`/api/mandates/${id}/agree`, { method: "POST", body: {} });
      BA.toast("Agreed. A review is set for 90 days from now.");
      BA.rerender();
    });
    main.querySelector("#m-copy").onclick = BA.guard(async () => { const r = await BA.api(`/api/mandates/${id}/export`, { method: "POST" }); await navigator.clipboard.writeText(r.markdown); BA.toast("Copied. Logged as an export."); });
    const mf = main.querySelector("#m-file");
    if (mf) {
      mf.onchange = async () => { if (mf.files[0]) main.querySelector("#m-json").value = await mf.files[0].text(); };
      main.querySelector("#m-import").onclick = BA.guard(async () => {
        let body;
        try { body = JSON.parse(main.querySelector("#m-json").value); } catch { throw new Error("That isn't valid JSON."); }
        const r = await BA.api("/api/mandates/import", { method: "POST", body });
        BA.toast(`Added ${r.added} item${r.added === 1 ? "" : "s"}${r.fields.length ? ` and ${r.fields.join(", ")}` : ""}.`);
        BA.rerender();
      });
    }
  }

  // ---- Situation, learning agenda and mentoring ----

  const SIT_KINDS = ["start-up", "turnaround", "accelerated growth", "realignment", "sustaining success"];
  const SIT_TONES = { "start-up": "accent", turnaround: "bad", "accelerated growth": "good", realignment: "warn", "sustaining success": "good" };
  const LEARN_AREAS = ["business", "past", "present", "future", "people", "culture", "technical", "products and customers", "politics"];
  const VERDICT_TONES = { testing: "accent", supported: "good", disproved: "bad", mixed: "warn" };
  const PRACTICE_STATUS = ["shared", "trying", "adopted", "dropped"];
  const PRACTICE_TONES = { shared: "", trying: "warn", adopted: "good", dropped: "" };

  async function renderSituation(main) {
    const [list, guide, pf] = await Promise.all([BA.api("/api/situations"), BA.api("/api/situations/guide"), BA.api("/api/situations/portfolio")]);
    const ro = presenting();
    const pfMarkdown = () => ["# Situation portfolio", "", "| Situation | Areas | Pace | Share of effort |", "| --- | --- | --- | --- |",
      ...pf.groups.filter((g) => g.areas.length).map((g) => `| ${g.kind} | ${g.areas.map((a) => a.area + (a.element ? ` (${a.element})` : "")).join(", ")} | ${guide[g.kind].pace_label} | ${pf.total ? Math.round((g.effort / pf.total) * 100) + "%" : "–"} |`),
      "", ...pf.groups.flatMap((g) => g.areas.filter((a) => a.approach).map((a) => `- **${a.area}:** ${a.approach}`))].join("\n");
    const portfolioCard = `<section class="card"><div class="row"><h2>Portfolio</h2><span class="spacer"></span>${list.length ? '<button class="btn" type="button" id="pf-md">Copy as Markdown</button>' : ""}</div>
      <p class="quiet">Your areas sorted into the five situations, with the share of your effort each should get over the next 90 days. A shared way to talk with your manager and team about what you'll handle fast, what you'll learn first, and why.</p>
      <div class="tablewrap"><table class="data"><thead><tr><th>Situation</th><th>Areas</th><th>Pace</th><th>Effort</th></tr></thead><tbody>${pf.groups.map((g) => `<tr><td><span class="pill ${SIT_TONES[g.kind]}">${esc(g.kind)}</span></td><td>${g.areas.map((a) => esc(a.area) + (a.element ? ` <span class="quiet">(${esc(a.element)})</span>` : "")).join(", ") || '<span class="quiet">–</span>'}</td><td class="quiet">${g.areas.length ? `${esc(guide[g.kind].pace_label)} · ${esc(g.style === "both" ? "hero and steward" : g.style)}` : ""}</td><td>${g.effort ? g.effort + "%" : ""}</td></tr>`).join("")}</tbody></table></div>
      ${pf.total && pf.total !== 100 ? `<p class="callout warn">Effort adds up to ${pf.total}%. Adjust the areas so it comes to 100%.</p>` : ""}
      ${pf.undecided.length ? `<p class="quiet">Not decided yet: ${pf.undecided.map((a) => esc(a.area)).join(", ")}.</p>` : ""}
      ${ro ? "" : `<div class="row" style="align-items:center"><label class="quiet" style="margin:0">The situation I most enjoy leading <select id="pf-pref" style="max-width:200px"><option value=""></option>${opts(SIT_KINDS, pf.preferred)}</select></label></div>
        ${pf.style_mismatch === "hero" ? '<p class="callout warn">Most of your effort is in situations that call for a steward, and your natural style is the hero. Move deliberately, lean on stewards on your team for counsel and outreach, and save the decisive energy for what is truly broken.</p>' : ""}
        ${pf.style_mismatch === "steward" ? '<p class="callout warn">Most of your effort is in situations that call for a hero, and your natural style is the steward. Decide faster than feels comfortable, and don\'t spend time building consensus where the need is obvious.</p>' : ""}
        ${pf.team_mix && (pf.team_mix.hero + pf.team_mix.steward + pf.team_mix.both + pf.team_mix.unknown) ? `<p class="quiet">Your team: ${pf.team_mix.hero} hero, ${pf.team_mix.steward} steward, ${pf.team_mix.both} both${pf.team_mix.unknown ? `, ${pf.team_mix.unknown} not noted` : ""}. Every team needs both. ${pf.my_style ? "" : '<a href="#/me/preferences">Note your own style</a>.'}</p>` : ""}
        ${pf.preference_check ? `<p class="callout warn">The most effort is going to ${esc(pf.preferred)}, the kind of situation you most enjoy. Make sure that's what the work needs, not your preference.</p>` : ""}`}</section>`;
    main.innerHTML = `${f90Tabs("situation")}
      ${portfolioCard}
      <p class="quiet">Different parts of the same job can need very different approaches. For each area, decide what kind of situation it's in, why you think so, and what that means for how you'll act there. Revisit it after the listening tour.</p>
      ${(() => { const fast = list.filter((s) => s.kind && guide[s.kind].pace === "fast"), slow = list.filter((s) => s.kind && guide[s.kind].pace === "learn");
        return fast.length && slow.length ? `<p class="callout warn">Your areas call for different paces. Act quickly on ${fast.map((s) => esc(s.area)).join(", ")}; learn first on ${slow.map((s) => esc(s.area)).join(", ")}. Don't let one pace set the other.</p>` : ""; })()}
      <details class="card"><summary><b>The five kinds of situation</b></summary>${SIT_KINDS.map((k) => `<div class="sit-guide"><span class="pill ${SIT_TONES[k]}">${k}</span><p>${esc(guide[k].what)}</p><p class="quiet"><b>Usually calls for:</b> ${esc(guide[k].approach)}</p><p class="quiet"><b>The mood:</b> ${esc(guide[k].mood)} <b>Your job:</b> ${esc(guide[k].mood_job)} <b>Pace:</b> ${esc(guide[k].pace_label)} <b>Usually calls for:</b> ${esc(guide[k].style_label)}</p><p class="quiet"><b>Ask your manager for:</b> ${guide[k].from_manager.slice(4).map(esc).join("; ") || "the basics: resources, clear goals, guidance at big decisions, focus"}.</p><div class="grid2"><div><b>Typical challenges</b><ul>${guide[k].challenges.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></div><div><b>Typical opportunities</b><ul>${guide[k].opportunities.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></div></div>${guide[k].playbook.length ? `<p><b>The six moves here:</b></p><ul>${guide[k].playbook.map((p) => `<li><b>${esc(p.lever)}:</b> ${esc(p.move)}</li>`).join("")}</ul>` : ""}</div>`).join("")}</details>
      <section class="card">${list.map((s) => ro ? `<div class="sit-row"><div class="row"><b>${esc(s.area)}</b>${s.kind ? `<span class="pill ${SIT_TONES[s.kind]}">${esc(s.kind)}</span>` : '<span class="pill">not decided</span>'}</div>${s.approach ? `<p>${esc(s.approach)}</p>` : ""}</div>`
        : `<form class="sit-row" data-sit="${s.id}"><div class="row"><input name="area" value="${esc(s.area)}" style="max-width:260px;font-weight:600"><select name="kind" style="max-width:200px"><option value="">Not decided</option>${opts(SIT_KINDS, s.kind)}</select><select name="element" style="max-width:130px" title="What kind of piece it is"><option value="">Kind of piece</option>${opts(["product", "process", "project", "system", "team"], s.element)}</select><input name="effort" type="number" min="0" max="100" value="${esc(s.effort ?? "")}" placeholder="Effort %" title="Share of your effort over the next 90 days" style="width:96px"><span class="spacer"></span><button class="icon-btn" type="button" data-del title="Remove">${BA.icon("x")}</button></div>
          ${s.kind ? `<p class="quiet"><span class="pill">${esc(guide[s.kind].pace_label)}</span> ${esc(guide[s.kind].mood_job)}</p><p class="quiet"><b>Watch for:</b> ${guide[s.kind].challenges.map(esc).join("; ")}. <b>Build on:</b> ${guide[s.kind].opportunities.map(esc).join("; ")}.</p>${guide[s.kind].playbook.length ? `<details><summary class="quiet">How to lead change here</summary><ul>${guide[s.kind].playbook.map((p) => `<li><b>${esc(p.lever)}:</b> ${esc(p.move)}</li>`).join("")}</ul></details>` : ""}` : ""}
          <div class="grid2"><label>Why I think so <span class="quiet">(private)</span><textarea name="evidence" rows="2">${esc(s.evidence || "")}</textarea></label>
          <label>How it got here <span class="quiet">(private; the history behind it)</span><textarea name="history" rows="2">${esc(s.history || "")}</textarea></label>
          <label>Opportunities I see <span class="quiet">(private; what to build on)</span><textarea name="opportunities" rows="2">${esc(s.opportunities || "")}</textarea></label>
          <label>The mood I'm seeing <span class="quiet">(private)</span><textarea name="mood" rows="2" placeholder="${s.kind ? esc(guide[s.kind].mood) : ""}">${esc(s.mood || "")}</textarea></label><label>What it means for how I act here<textarea name="approach" rows="2" placeholder="${s.kind ? esc(guide[s.kind].approach) : ""}">${esc(s.approach || "")}</textarea></label></div>
          <div class="actions"><button class="btn" type="submit">Save</button></div></form>`).join("") || '<p class="quiet">No areas yet.</p>'}
        ${ro ? "" : `<form id="add-sit" class="row" style="margin-top:8px"><input name="area" required placeholder="An area, such as: Release management" style="flex:1;min-width:220px"><button class="btn" type="submit">Add</button>${list.length ? "" : '<button class="btn" type="button" id="sit-starter">Start with common areas</button>'}</form>`}</section>`;
    const md = main.querySelector("#pf-md");
    if (md) md.onclick = () => { navigator.clipboard.writeText(pfMarkdown()); BA.toast("Copied."); };
    if (ro) return;
    main.querySelector("#pf-pref").onchange = BA.guard(async (e) => { await BA.api("/api/situations/preferred", { method: "PUT", body: { kind: e.target.value || null } }); BA.rerender(); });
    main.querySelectorAll("[data-sit]").forEach((f) => {
      f.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(f); await BA.api(`/api/situations/${f.dataset.sit}`, { method: "PATCH", body: { area: fd.get("area"), kind: fd.get("kind") || null, element: fd.get("element") || null, effort: numOrNull(fd.get("effort")), evidence: fd.get("evidence") || null, history: fd.get("history") || null, mood: fd.get("mood") || null, opportunities: fd.get("opportunities") || null, approach: fd.get("approach") || null } }); BA.toast("Saved."); BA.rerender(); });
      f.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Remove this area?")) return; await BA.api(`/api/situations/${f.dataset.sit}`, { method: "DELETE" }); BA.rerender(); });
    });
    main.querySelector("#add-sit").onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/situations", { method: "POST", body: { area: e.target.elements.area.value, position: list.length } }); BA.rerender(); });
    const st = main.querySelector("#sit-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/situations/starter", { method: "POST" }); BA.rerender(); });
  }

  async function renderLearning(main) {
    const [d, people, methods, lplan] = await Promise.all([BA.api("/api/learning-questions/agenda"), BA.api("/api/people"), BA.api("/api/first90/learning-methods"), BA.api("/api/first90/learning-plan")]);
    if (d.hidden) { main.innerHTML = `${f90Tabs("learning")}<p class="empty">Private, so hidden while presenting.</p>`; return; }
    const f = (() => { try { return sessionStorage.getItem("ba-learn-filter") || "open"; } catch { return "open"; } })();
    const shown = d.questions.filter((q) => f === "all" || q.status === f);
    const pick = (q) => `<div class="case-picks ask-pick">${people.filter((p) => p.active !== false).map((p) => `<label class="check"><input type="checkbox" name="ask_ids" value="${p.id}"${(q.ask_ids || []).includes(p.id) ? " checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>`;
    main.innerHTML = `${f90Tabs("learning")}
      <p class="quiet">Be deliberate about what you need to learn, from whom, and by when. Questions about the past explain how things got this way; the present shows how work really happens; the future is what the business is counting on. Add what comes up in the listening tour.</p>
      <section class="card"><div class="row"><h2>Learning agenda</h2><span class="quiet">${d.counts.open} open · ${d.counts.answered} answered${d.late ? ` · <span class="pill warn">${d.late} past their day</span>` : ""}</span><span class="spacer"></span>
        <div class="seg" id="lq-filter">${[["open", "Open"], ["answered", "Answered"], ["all", "All"]].map(([k, l]) => `<button type="button" data-f="${k}" class="${k === f ? "on" : ""}">${l}</button>`).join("")}</div></div>
        ${d.balance ? `<div class="item"><span class="quiet">Open questions: ${["technical", "people", "culture", "politics"].map((k) => `${k} ${d.balance.counts[k]}`).join(" · ")}${d.balance.hypotheses ? ` · ${d.balance.hypotheses} hypotheses, ${d.balance.testing} being tested` : ""}</span></div>
          ${d.balance.technical_heavy ? `<p class="callout warn">Most of your questions are technical. Culture and politics are harder to see and easier to get wrong; add a few questions about how decisions really get made and what the culture rewards.${d.balance.realignment ? " At least one of your areas is a realignment, where cultural and political learning matters most." : ""}</p>` : ""}` : ""}
        ${LEARN_AREAS.map((a) => [a, shown.filter((q) => q.area === a)]).filter(([, l]) => l.length).map(([a, l]) => `<h3>${esc(a[0].toUpperCase() + a.slice(1))}</h3>${l.map((q) => `<details class="plan-item${q.status !== "open" ? " dropped" : ""}" data-q="${q.id}"><summary>
            ${q.late ? '<span class="pill warn">late</span>' : q.status === "answered" ? '<span class="pill good">answered</span>' : ""}${q.verdict ? `<span class="pill ${VERDICT_TONES[q.verdict] || ""}">${esc(q.verdict)}</span>` : ""}<span>${esc(q.question)}</span><span class="spacer"></span><span class="quiet">${q.ask_names.length ? esc(q.ask_names.join(", ")) + " · " : ""}${q.due ? BA.fmtDate(q.due) : BA.roleDay(q.due_day)}</span></summary>
          <form><label>Question<input name="question" value="${esc(q.question)}"></label><div class="grid2"><label>Area<select name="area">${opts(LEARN_AREAS, q.area)}</select></label><label>By day<input type="number" min="1" name="due_day" value="${esc(q.due_day ?? "")}"></label>
            <label>Status<select name="status">${opts(["open", "answered", "dropped"], q.status)}</select></label></div><label>Who could answer it</label>${pick(q)}
            <label>What I learned<textarea name="answer" rows="3">${esc(q.answer || "")}</textarea></label>
            <details${q.hypothesis ? " open" : ""}><summary class="quiet">Turn it into a hypothesis</summary><label>What I think is going on<textarea name="hypothesis" rows="2">${esc(q.hypothesis || "")}</textarea></label>
              <label>What would prove it wrong<textarea name="disprove_if" rows="2">${esc(q.disprove_if || "")}</textarea></label><label>Verdict<select name="verdict"><option value=""></option>${opts(["testing", "supported", "disproved", "mixed"], q.verdict)}</select></label></details>
            <div class="actions"><button class="btn danger left" type="button" data-del>Delete</button><button class="btn primary" type="submit">Save</button></div></form></details>`).join("")}`).join("") || '<p class="quiet">Nothing here.</p>'}
        <form id="add-q" class="row" style="margin-top:10px"><select name="area" style="max-width:190px">${opts(LEARN_AREAS, "present")}</select><input name="question" required placeholder="What do you need to find out?" style="flex:1;min-width:240px"><input type="number" name="due_day" min="1" placeholder="By day" style="width:90px"><button class="btn" type="submit">Add</button>
          ${d.questions.length ? "" : '<button class="btn" type="button" id="lq-starter">Start from suggested questions</button>'}</form></section>
      <section class="card"><div class="row"><h2>Learning plan</h2><span class="quiet">${lplan.done} of ${lplan.total} done</span></div>
        <p class="quiet">The agenda says what to learn; the plan says how. Learning is the main job of the first 30 days. Collect, distill, form hypotheses and test them, and review them with your manager as you go.</p>
        ${lplan.phases.map((p) => `<h3>${esc(p.phase)}</h3>${p.steps.map((s) => `<div class="item" data-step="${s.key}"><label class="check" style="flex:1"><input type="checkbox"${s.done ? " checked" : ""}> <span${s.done ? ' class="quiet"' : ""}>${s.link ? `${esc(s.text)} <a href="${s.link}">Open</a>` : esc(s.text)}</span></label><span class="quiet">${s.due ? BA.fmtDate(s.due) : BA.roleDay(s.day)}</span></div>`).join("")}`).join("")}</section>
      <div class="cards">
        <section class="card"><h2>Who you're learning from</h2><p class="quiet">Different vantage points, inside and outside the team. Tag people under Details on their page.</p>
          ${d.sources.kinds.map((k) => `<div class="item"><span>${esc(k.label)}</span><span class="spacer"></span><span class="quiet">${k.people.length ? k.people.map((p) => `<a href="#/people/${p.id}"${p.heard ? "" : ' title="Not talked to yet"'}>${esc(p.name)}${p.heard ? "" : " (not yet)"}</a>`).join(", ") : "No one tagged"}</span></div>`).join("")}
          ${d.sources.gaps.length ? `<p class="callout warn">No conversation yet with: ${d.sources.gaps.map((g) => esc(d.sources.kinds.find((k) => k.key === g).label.split(":")[0].toLowerCase())).join(", ")}.</p>` : ""}</section>
        <section class="card"><h2>Ways to learn</h2><p class="quiet">Talking to people is only one method. A little structure gets you more, faster.</p>
          ${methods.methods.map((m) => `<form class="row" data-method="${m.key}" style="align-items:center;margin-bottom:6px"><span style="flex:1;min-width:180px"><b>${m.link ? `<a href="${m.link}">${esc(m.label)}</a>` : esc(m.label)}</b><br><span class="quiet">${esc(m.about)}</span></span>
            <select name="status" style="max-width:120px">${opts(methods.statuses, m.status)}</select><input name="notes" value="${esc(m.notes)}" placeholder="Notes" style="max-width:200px"><button class="btn" type="submit">Save</button></form>`).join("")}</section>
      </div>`;
    main.querySelectorAll("[data-step] input").forEach((cb) => (cb.onchange = BA.guard(async () => { await BA.api(`/api/first90/learning-plan/${cb.closest("[data-step]").dataset.step}`, { method: "PUT", body: { done: cb.checked } }); BA.rerender(); })));
    main.querySelectorAll("[data-method]").forEach((f) => (f.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(f); await BA.api(`/api/first90/learning-methods/${f.dataset.method}`, { method: "PUT", body: { status: fd.get("status"), notes: fd.get("notes") } }); BA.toast("Saved."); })));
    main.querySelectorAll("[data-f]").forEach((b) => (b.onclick = () => { try { sessionStorage.setItem("ba-learn-filter", b.dataset.f); } catch {} BA.rerender(); }));
    main.querySelectorAll("[data-q]").forEach((det) => {
      const form = det.querySelector("form");
      form.onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(form);
        await BA.api(`/api/learning-questions/${det.dataset.q}`, { method: "PATCH", body: { question: fd.get("question"), area: fd.get("area"), due_day: numOrNull(fd.get("due_day")), status: fd.get("status"), answer: fd.get("answer") || null, hypothesis: fd.get("hypothesis") || null, disprove_if: fd.get("disprove_if") || null, verdict: fd.get("verdict") || null, ask_ids: fd.getAll("ask_ids").map(Number) } });
        BA.rerender(); });
      det.querySelector("[data-del]").onclick = BA.guard(async () => { if (!confirm("Delete this question?")) return; await BA.api(`/api/learning-questions/${det.dataset.q}`, { method: "DELETE" }); BA.rerender(); });
    });
    main.querySelector("#add-q").onsubmit = BA.guard(async (e) => { e.preventDefault(); const fd = new FormData(e.target); await BA.api("/api/learning-questions", { method: "POST", body: { question: fd.get("question"), area: fd.get("area"), due_day: numOrNull(fd.get("due_day")), position: d.questions.length } }); BA.rerender(); });
    const st = main.querySelector("#lq-starter");
    if (st) st.onclick = BA.guard(async () => { await BA.api("/api/learning-questions/starter", { method: "POST" }); BA.rerender(); });
  }

  async function renderMentoring(main) {
    const d = await BA.api("/api/mentoring/overview");
    if (d.hidden) {
      main.innerHTML = `${f90Tabs("mentoring")}<section class="card"><h2>Practices other teams have adopted</h2>${d.adopted.map((p) => `<div class="item"><span>${esc(p.practice)}</span><span class="spacer"></span><span class="quiet">${esc(p.person_name || "")}</span></div>`).join("") || '<p class="quiet">None yet.</p>'}</section>`;
      return;
    }
    main.innerHTML = `${f90Tabs("mentoring")}
      <p class="quiet">The other managers you mentor, and the practices they pick up from you as yours prove out. Adopted practices count toward Momentum, and are the clearest evidence that this part of the role is working.</p>
      <div class="stat-row" style="margin-bottom:12px">${PRACTICE_STATUS.map((s) => `<div><b>${d.totals[s]}</b><span>${s}</span></div>`).join("")}</div>
      ${d.mentees.map((m) => `<section class="card" data-mentee="${m.id}"><div class="row"><h2><a href="#/people/${m.id}">${esc(m.name)}</a></h2><span class="quiet">${esc(m.role || "")}</span><span class="spacer"></span><span class="quiet">${m.last ? `last session ${BA.fmtDate(m.last)}` : "no sessions yet"}${m.next_on ? ` · next ${BA.fmtDate(m.next_on)}` : ""}</span></div>
        <h3>Practices</h3>${m.practices.map((p) => `<div class="item" data-practice="${p.id}"><span>${esc(p.practice)}</span><span class="spacer"></span><select style="max-width:130px">${opts(PRACTICE_STATUS, p.status)}</select></div>`).join("") || '<p class="quiet">None yet.</p>'}
        <form class="row add-practice"><input name="practice" required placeholder="A practice you've shared, such as: sprint goals" style="flex:1;min-width:220px"><button class="btn" type="submit">Add</button></form>
        <h3>Sessions</h3>${m.sessions.slice(0, 5).map((s) => `<div class="item"><span class="quiet">${BA.fmtDate(s.date)}</span><span>${esc(s.topic || "")}</span><span class="spacer"></span><span class="quiet">${esc(s.next_step || "")}</span></div>`).join("") || '<p class="quiet">None yet.</p>'}
        <form class="add-session"><div class="grid2"><label>Date<input type="date" name="date" value="${BA.today()}"></label><label>Topic<input name="topic"></label><label>Next step<input name="next_step"></label><label>Follow up on<input type="date" name="next_on"></label></div>
          <label>Notes<textarea name="notes" rows="2"></textarea></label><div class="actions"><button class="btn" type="submit">Log a session</button></div></form></section>`).join("")}
      <section class="card"><h2>Start mentoring someone</h2>${d.candidates.length ? `<form id="new-mentee" class="row"><select name="person" style="max-width:280px">${d.candidates.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("")}</select><input name="practice" placeholder="A first practice to share (optional)" style="flex:1;min-width:200px"><button class="btn primary" type="submit">Start</button></form>`
        : '<p class="quiet">Add the managers you\'ll mentor under People, as peers.</p>'}</section>`;
    main.querySelectorAll("[data-mentee]").forEach((sec) => {
      const pid = Number(sec.dataset.mentee);
      sec.querySelectorAll("[data-practice] select").forEach((s) => (s.onchange = BA.guard(async () => {
        const body = { status: s.value };
        if (s.value === "adopted") body.since = BA.today();
        await BA.api(`/api/mentored-practices/${s.closest("[data-practice]").dataset.practice}`, { method: "PATCH", body }); BA.toast("Saved."); BA.rerender();
      })));
      const ap = sec.querySelector(".add-practice");
      ap.onsubmit = BA.guard(async (e) => { e.preventDefault(); await BA.api("/api/mentored-practices", { method: "POST", body: { person_id: pid, practice: ap.elements.practice.value, since: BA.today() } }); BA.rerender(); });
      const as = sec.querySelector(".add-session");
      as.onsubmit = BA.guard(async (e) => { e.preventDefault(); const f = new FormData(as); await BA.api("/api/mentoring-sessions", { method: "POST", body: { person_id: pid, date: f.get("date"), topic: f.get("topic") || null, next_step: f.get("next_step") || null, next_on: f.get("next_on") || null, notes: f.get("notes") || null } }); BA.toast("Logged."); BA.rerender(); });
    });
    const nm = main.querySelector("#new-mentee");
    if (nm) nm.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      const f = new FormData(nm), pid = Number(f.get("person"));
      if (f.get("practice")) await BA.api("/api/mentored-practices", { method: "POST", body: { person_id: pid, practice: f.get("practice"), since: BA.today() } });
      else await BA.api("/api/mentoring-sessions", { method: "POST", body: { person_id: pid, date: BA.today(), topic: "Getting started" } });
      BA.rerender();
    });
  }
})();
