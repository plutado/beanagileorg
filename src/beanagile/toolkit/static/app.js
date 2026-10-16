// Toolkit version 1 screens: Today, People, Skills and learning, Listening tour, Day-30 rollup, My development.
(function () {
  const { esc } = BA;
  const presenting = () => BA.session.presentation;

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
    const d = await BA.api(`/api/escalation/${id}`);
    const s = d.system;
    document.getElementById("view-title").textContent = s.name;
    const chain = (steps) =>
      steps.length
        ? `<ol class="chain">${steps.map((st) => `<li><b>${esc(st.person_name || "[No person]")}</b> <span class="pill">${esc(st.method)}</span>${st.note ? ` <span class="quiet">${esc(st.note)}</span>` : ""}
            ${presenting() ? "" : `<button class="btn danger" data-del-step="${st.id}">Remove</button>`}</li>`).join("")}</ol>`
        : '<p class="quiet">No steps yet.</p>';
    const roles = `<dl class="readonly"><dt>Owner</dt><dd>${esc(s.owner_name || "")}</dd><dt>First responder</dt><dd>${esc(s.first_responder_name || "")}</dd>
      <dt>Backup</dt><dd>${esc(s.backup_name || "")}</dd><dt>Opening a vendor case</dt><dd>${esc(s.how_to_open_case || "")}</dd>
      <dt>Business contacts</dt><dd>${esc(s.business_contacts || "")}</dd>${s.vendor_support !== undefined ? `<dt>Vendor support</dt><dd>${esc(s.vendor_support || "")}</dd>` : ""}</dl>`;
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
          <label>Business contacts<input name="business_contacts" value="${esc(s.business_contacts || "")}"></label></div>
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
      for (const k of ["owner_id", "first_responder_id", "backup_id"]) body[k] = body[k] ? Number(body[k]) : null;
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
})();
