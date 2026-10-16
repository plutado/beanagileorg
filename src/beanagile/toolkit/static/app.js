// Toolkit version 1 screens: Today, People, Skills and learning, Listening tour, Day-30 rollup, My development.
(function () {
  const { esc } = BA;
  const presenting = () => BA.session.presentation;

  BA.command({ label: "Add a dev-sync item", hint: "Dev-sync log", icon: "plus", run: () => BA.go("/dev-sync") });
  BA.command({ label: "Plan a one-on-one", hint: "Listening tour", icon: "plus", run: () => BA.go("/listening") });
  BA.command({ label: "Add a person", hint: "People", icon: "plus", run: () => BA.go("/people") });
  BA.command({ label: "Log a vendor conversation", hint: "Vendors", icon: "handshake", run: () => BA.go("/vendors") });
  BA.command({ label: "Write a ceremony note", hint: "Sprint notebook", icon: "notebook-pen", run: async () => {
    const s = await BA.api("/api/sprints/current");
    BA.go(s ? `/sprints/${s.id}` : "/sprints");
  } });
  BA.command({ label: "Weekly status draft", hint: "Reporting", icon: "file-text", run: () => BA.go("/status") });
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
    { name: "systems", label: "Products and systems mentioned", type: "list", hint: "comma separated" },
    { name: "gaps", label: "Gaps", type: "textarea" },
    { name: "opportunities", label: "Opportunities", type: "textarea" },
    { name: "themes", label: "Themes", type: "list", hint: "comma separated; these roll up into the day-30 diagnosis" },
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
      main.innerHTML = `<div class="cards">
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

  BA.view("/people", {
    title: "People",
    async render(main, param) {
      if (param) return renderPerson(main, Number(param));
      const people = await BA.api("/api/people");
      main.innerHTML = `
        ${presenting() ? "" : `<section class="card"><h2>Add a person</h2><form id="add" class="grid2">
          ${BA.form(PERSON_FIELDS.slice(0, 3))}<div class="actions"><button class="btn primary" type="submit">Add</button></div></form></section>`}
        <div class="tablewrap"><table class="data"><thead><tr><th>Name</th><th>Role</th><th>Relationship</th><th>Status</th></tr></thead><tbody>${
          people
            .map((p) => `<tr class="clickable" data-id="${p.id}"><td>${esc(p.name)}</td><td>${esc(p.role)}</td><td>${esc(p.relationship)}</td>
              <td>${p.active ? "" : '<span class="pill">inactive</span>'}</td></tr>`)
            .join("") || '<tr><td colspan="4" class="empty">No one yet.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/people/${tr.dataset.id}`)));
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const rec = await BA.api("/api/people", { method: "POST", body: BA.readForm(add, PERSON_FIELDS.slice(0, 3)) });
          BA.go(`/people/${rec.id}`);
        });
    },
  });

  async function renderPerson(main, id) {
    const rec = await BA.api(`/api/people/${id}`);
    document.getElementById("view-title").textContent = rec.name;
    if (presenting()) {
      main.innerHTML = `<section class="card">${BA.readOnly(PERSON_FIELDS, rec)}</section><p><a href="#/people">All people</a></p>`;
      return;
    }
    const interviews = (await BA.api("/api/interviews")).filter((i) => i.person_id === id);
    main.innerHTML = `<p><a href="#/people">All people</a></p>
      <form id="person" class="card"><div class="grid2">${BA.form(PERSON_FIELDS, rec)}</div>
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button><button class="btn primary" type="submit">Save</button></div></form>
      <section class="card"><div class="row"><h2>One-on-ones</h2><span class="spacer"></span><button class="btn" id="plan">Plan a one-on-one</button></div>${
        interviews.map((i) => `<div class="item"><a href="#/listening/${i.id}">${BA.fmtDate(i.date) || "[No date]"}</a> ${BA.statusPill(i.status)} ${BA.chips(i.themes)}</div>`).join("") ||
        '<p class="quiet">None yet.</p>'
      }</section>`;
    const form = main.querySelector("#person");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api(`/api/people/${id}`, { method: "PATCH", body: BA.readForm(form, PERSON_FIELDS) });
      BA.toast("Saved.");
      BA.rerender();
    });
    main.querySelector("#del").onclick = BA.guard(async () => {
      if (!confirm(`Delete ${rec.name}? Their one-on-ones stay, without a person.`)) return;
      await BA.api(`/api/people/${id}`, { method: "DELETE" });
      BA.go("/people");
    });
    main.querySelector("#plan").onclick = BA.guard(async () => {
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
        <h3>The same four questions, every time</h3>${BA.form(fields.slice(3, 7), rec)}
        <h3>What I heard</h3>${BA.form(fields.slice(7), rec)}
        ${known.length ? `<p class="quiet">Themes so far: ${BA.chips(known)}</p>` : ""}
        <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button><button class="btn primary" type="submit">Save</button></div>
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
        <div class="cards">${notes("gaps", "Gaps")}${notes("opportunities", "Opportunities")}${notes("dont_change", "What not to change")}${notes("change_first", "What to change first")}</div>`;
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

  BA.view("/me", {
    title: "My development",
    async render(main) {
      const [settings, goals, log, tasks, obligations] = await Promise.all([
        BA.api("/api/toolkit/settings"),
        BA.api("/api/learning-goals"),
        BA.api("/api/learning-log"),
        BA.api("/api/tasks"),
        BA.api("/api/obligations"),
      ]);
      const start = settings.start_date;
      const dayDate = (n) => {
        if (n == null) return "";
        if (!start) return `Day ${n}`;
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
        <section class="card"><h2>Contract start date</h2>
          <form id="start" class="row"><input type="date" name="start_date" value="${esc(start || "")}" style="max-width:200px">
          <button class="btn" type="submit">Save</button><span class="quiet">Turns every "Day N" into a real date.</span></form></section>

        <section class="card"><h2>Learning goals</h2>
          <p class="quiet">Goals marked "Report" are the ones Brian sees in status reports and presentation mode.</p>
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
  const ACTION_ORIGINS = ["dev sync", "retro", "incident", "one-on-one", "other"];
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
    { name: "notes", label: "My notes (private)", type: "textarea" },
  ];

  BA.view("/dev-sync", {
    title: "Dev-sync log",
    async render(main, param) {
      const people = await BA.api("/api/people");
      if (param) return renderAction(main, Number(param), people);
      const [items, summary] = await Promise.all([BA.api("/api/actions"), BA.api("/api/actions/summary")]);
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
        <div class="tablewrap"><table class="data"><thead><tr><th>Question or concern</th><th>Raised by</th><th>Owner</th><th>Next action</th><th>Due</th><th>Status</th><th>Learning</th></tr></thead><tbody>${
          shown
            .map((i) => `<tr class="clickable" data-id="${i.id}"><td>${esc(i.concern)}</td><td>${esc(i.raised_by_name || "")}</td><td>${esc(i.owner_name || "")}</td>
              <td>${esc(i.next_action)}</td><td${late(i) ? ' class="late"' : ""}>${BA.fmtDate(i.due)}</td>
              <td>${late(i) ? '<span class="pill bad">overdue</span>' : BA.statusPill(i.status)}</td><td>${i.learning ? '<span class="pill">yes</span>' : ""}</td></tr>`)
            .join("") || '<tr><td colspan="7" class="empty">Nothing matches.</td></tr>'
        }</tbody></table></div>
        <p class="quiet">I own the follow-up on every item, so nothing raised gets dropped.</p>`;
      main.querySelector("#f-status").onchange = (e) => ((state.status = e.target.value), BA.rerender());
      main.querySelector("#f-owner").onchange = (e) => ((state.owner = e.target.value), BA.rerender());
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/dev-sync/${tr.dataset.id}`)));
      const add = main.querySelector("#add");
      if (add)
        add.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          await BA.api("/api/actions", { method: "POST", body: BA.readForm(add, ACTION_FIELDS(people).slice(0, 9).filter((f) => f.name !== "raised_on")) });
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
      <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button><button class="btn primary" type="submit">Save</button></div></form>`;
    const form = main.querySelector("#item");
    form.onsubmit = BA.guard(async (e) => {
      e.preventDefault();
      await BA.api(`/api/actions/${id}`, { method: "PATCH", body: BA.readForm(form, fields) });
      BA.toast("Saved.");
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
      if (param) return renderSystem(main, Number(param), people, severities);
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
            .map((i) => `<tr><td>${BA.fmtDate(i.date)}</td><td>${esc(i.system_name || "")}</td><td>${esc(i.severity_level || "")}</td><td>${esc(i.summary)}</td>
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

  async function renderSystem(main, id, people, severities) {
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
      <dt>Business contacts</dt><dd>${esc(s.business_contacts || "")}</dd>
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
          <label>Business contacts<input name="business_contacts" value="${esc(s.business_contacts || "")}"></label>
          <label>Vendor<select name="vendor_id"><option value=""></option>${vendors.map((v) => `<option value="${v.id}"${v.id === s.vendor_id ? " selected" : ""}>${esc(v.name)}</option>`).join("")}</select></label></div>
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
          <span>${esc(c.title)}</span><span class="spacer"></span><span class="quiet">${esc(c.owner_name || "")} ${BA.fmtDate(c.due)}</span>
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
              <p style="margin:6px 0 0">${esc(i.summary)}</p>${i.concerns ? `<p class="quiet" style="margin:4px 0 0">Concerns: ${esc(i.concerns)}</p>` : ""}</div>`)
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
          const s = await BA.api("/api/sprints/next", { method: "POST", body: {} });
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
      <div class="actions"><button class="btn danger left" type="button" data-del-note="${n.id}">Delete</button>
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
            ? `<tr><td><b>${esc(i.title)}</b><div class="quiet">${esc(i.description || "")}</div></td><td>${esc(i.kind)}</td><td>${dayDateOf(settings.start_date, i.target_day)}</td><td>${BA.statusPill(i.status)}</td><td>${esc(i.owner_name || "")}</td></tr>`
            : `<tr data-id="${i.id}"><td><b>${esc(i.title)}</b><div class="quiet">${esc(i.description || "")}</div></td><td>${esc(i.kind)}</td>
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
      const levelPill = (l) => `<span class="pill ${l === "high" ? "bad" : l === "medium" ? "warn" : ""}">${esc(l)}</span>`;
      const ro = presenting();
      main.innerHTML = `
        <section class="card"><h2>Risks and issues</h2><div class="tablewrap"><table class="data"><thead><tr><th>Level</th><th>Risk or issue</th><th>Impact</th><th>Owner</th><th>Next step</th><th>Due</th><th>Status</th></tr></thead><tbody>${
          risks.map((r) => `<tr data-risk="${r.id}"><td>${levelPill(r.level)}</td><td><b>${esc(r.title)}</b></td><td>${esc(r.impact || "")}</td><td>${esc(r.owner_name || "")}</td>
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
          decisions.map((d) => `<tr data-dec="${d.id}"><td><b>${esc(d.decision)}</b></td><td>${esc(d.from_name || "")}</td><td>${BA.fmtDate(d.needed_by)}</td>
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
          await BA.api("/api/risks", { method: "POST", body: f });
          BA.rerender();
        });
        main.querySelector("#add-dec").onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(e.target));
          f.from_id = num(f.from_id);
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
      main.innerHTML = `<p class="quiet">A few measures the team agrees to watch. Baselines come first; targets are the team's choice.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Metric</th><th>Baseline</th><th>Target</th><th>Latest</th><th></th>${presenting() ? "" : "<th>Add a reading</th>"}</tr></thead><tbody>${metrics
          .map((m) => `<tr data-id="${m.id}"><td><b>${esc(m.name)}</b><div class="quiet">${esc(m.method || "")}</div></td>
            <td>${presenting() ? fmt(m.baseline, m.unit) : `<input type="number" step="any" name="baseline" value="${esc(m.baseline ?? "")}" style="max-width:110px">`}</td>
            <td>${presenting() ? fmt(m.target, m.unit) : `<input type="number" step="any" name="target" value="${esc(m.target ?? "")}" style="max-width:110px">`}</td>
            <td>${fmt(m.latest, m.unit)}<div class="quiet">${BA.fmtDate(m.latest_date)}</div></td><td>${onTrack(m)}</td>
            ${presenting() ? "" : `<td><span class="row"><input type="date" data-rdate="${m.id}" value="${BA.today()}" style="max-width:160px"><input type="number" step="any" data-rval="${m.id}" placeholder="Value" style="max-width:100px"><button class="btn" data-radd="${m.id}">Add</button></span></td>`}</tr>`)
          .join("")}</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onchange = BA.guard(async (e) => {
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

  BA.view("/status", {
    title: "Weekly status",
    async render(main) {
      const d = await BA.api("/api/status/draft");
      const tone = { Green: "good", Yellow: "warn", Red: "bad" }[d.overall];
      main.innerHTML = `<section class="card"><div class="row"><h2>Week of ${BA.fmtDate(d.week_of)}</h2><span class="pill ${tone}">${esc(d.overall)}</span>
          <span class="quiet">suggested because ${esc(d.reason)}</span><span class="spacer"></span>
          ${presenting() ? "" : '<button class="btn" id="copy">Copy Markdown</button>'}</div>
        <p class="quiet">Built only from exportable data: roadmap, risks, decisions, metrics and learning goals marked for reporting. The Comms studio can pull this draft straight into a message once it's connected with an export-only token.</p></section>
        <section class="card msg-preview">${BA.md(d.markdown)}</section>`;
      const copy = main.querySelector("#copy");
      if (copy)
        copy.onclick = BA.guard(async () => {
          const res = await BA.api("/api/status/export", { method: "POST" });
          await navigator.clipboard.writeText(res.markdown);
          BA.toast("Copied. Logged as an export.");
        });
    },
  });
})();
