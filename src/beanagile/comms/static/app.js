// Comms studio screens: This week, Decks (list and the three-pane deck builder), Media library.
(function () {
  const { esc } = BA;
  const TRANSITIONS = ["slide", "fade", "convex", "concave", "zoom", "none"];
  const SOURCES = [
    ["mine", "Mine"],
    ["licensed", "Licensed (for example Envato Elements)"],
    ["placeholder", "Placeholder"],
  ];

  // ---- load reveal.js, lottie-web and the renderer once ----

  let assets = null;
  function loadAssets() {
    const css = (href) =>
      new Promise((ok) => {
        const l = Object.assign(document.createElement("link"), { rel: "stylesheet", href, onload: ok, onerror: ok });
        document.head.appendChild(l);
      });
    const js = (src) =>
      new Promise((ok, fail) => {
        const s = Object.assign(document.createElement("script"), { src, onload: ok, onerror: () => fail(new Error(`Couldn't load ${src}`)) });
        document.head.appendChild(s);
      });
    assets ||= Promise.all([css("/static/vendor/reveal/reveal.css"), css("/static/deck-theme.css")]).then(() =>
      Promise.all([js("/static/vendor/reveal/reveal.js"), js("/static/vendor/lottie/lottie_light.min.js"), js("/static/deck-render.js")])
    );
    return assets;
  }

  async function upload(file, extra = {}) {
    const fd = new FormData();
    fd.append("file", file);
    for (const [k, v] of Object.entries(extra)) fd.append(k, v ?? "");
    const res = await fetch("/api/media/upload", { method: "POST", body: fd, credentials: "same-origin" });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    return res.json();
  }

  const debounce = (fn, ms) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  // ---------------------------------------------------------------- This week

  const MESSAGE_TYPES = ["weekly note", "weekly status", "alert", "release notes", "stakeholder update", "decision announcement", "team announcement", "review", "memo", "other"];
  const DETAIL_LEVELS = ["summary first", "full detail", "technical", "what changes for them"];
  const CHANNEL_KINDS = ["chat", "email", "meeting", "document", "other"];
  const RHYTHMS = ["weekly", "every two weeks", "monthly", "quarterly"];
  const presenting = () => BA.session.presentation;

  BA.command({ label: "New message", hint: "Messages", icon: "plus", run: () => BA.go("/messages") });
  BA.command({ label: "New deck", hint: "Decks", icon: "plus", run: () => BA.go("/decks") });
  BA.command({ label: "Upload media", hint: "Media library", icon: "film", run: () => BA.go("/media") });
  const stateClass = { draft: "", "in review": "warn", ready: "good", sent: "good", archived: "", overdue: "bad", "start drafting": "warn", drafted: "warn", upcoming: "" };
  const pill = (s) => `<span class="pill ${stateClass[s] || ""}">${esc(s)}</span>`;

  // Minimal, safe Markdown for previews: headings, lists, tables, bold, italics, links-as-text, paragraphs.
  function md(text) {
    const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|\W)_(.+?)_(?=\W|$)/g, "$1<i>$2</i>");
    const out = [];
    const lines = (text || "").split("\n");
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (/^\s*$/.test(line)) continue;
      const h = line.match(/^(#{1,3})\s+(.*)/);
      if (h) {
        out.push(`<h${h[1].length + 1}>${inline(h[2])}</h${h[1].length + 1}>`);
        continue;
      }
      if (line.trim().startsWith("|")) {
        const rows = [];
        while (i < lines.length && lines[i].trim().startsWith("|")) rows.push(lines[i++].trim());
        i--;
        const cells = (r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        const body = rows.filter((r) => !/^\|[\s:|-]+\|$/.test(r));
        out.push(`<table class="data"><thead><tr>${cells(body[0]).map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${body
          .slice(1)
          .map((r) => `<tr>${cells(r).map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`)
          .join("")}</tbody></table>`);
        continue;
      }
      const li = line.match(/^\s*([-*]|\d+\.)\s+(.*)/);
      if (li) {
        const ordered = /\d/.test(li[1]);
        const items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*([-*]|\d+\.)\s+/, ""));
        i--;
        out.push(`<${ordered ? "ol" : "ul"}>${items.map((x) => `<li>${inline(x)}</li>`).join("")}</${ordered ? "ol" : "ul"}>`);
        continue;
      }
      const para = [line];
      while (i + 1 < lines.length && lines[i + 1].trim() && !/^(#|\||\s*([-*]|\d+\.)\s)/.test(lines[i + 1])) para.push(lines[++i]);
      out.push(`<p>${inline(para.join(" "))}</p>`);
    }
    return out.join("");
  }

  const lookups = async () => {
    const [audiences, channels, templates] = await Promise.all([BA.api("/api/audiences"), BA.api("/api/channels"), BA.api("/api/templates")]);
    return { audiences, channels, templates };
  };

  // ---------------------------------------------------------------- This week

  BA.view("/this-week", {
    title: "This week",
    async render(main) {
      const [week, templates] = await Promise.all([BA.api("/api/this-week"), BA.api("/api/templates")]);
      if (!templates.length && !presenting()) {
        main.innerHTML = `<section class="card"><h2>Set up the studio</h2>
          <p class="quiet">Load the starter kit: nine templates (weekly status, alerts, release notes, reviews and more), common audiences, placeholder channels, and a weekly cadence. Edit any of it afterwards.</p>
          <button class="btn primary" id="kit">Load starter kit</button></section>`;
        main.querySelector("#kit").onclick = BA.guard(async () => {
          await BA.api("/api/comms/starter-kit", { method: "POST" });
          BA.rerender();
        });
        return;
      }
      const dueRow = (d) => `<div class="item">${pill(d.status)}<span><b>${esc(d.title)}</b> <span class="quiet">due ${BA.fmtDate(d.due)}</span></span><span class="spacer"></span>
        ${d.message_id ? `<a class="btn" href="#/messages/${d.message_id}">Open</a>` : `<button class="btn primary" data-draft="${d.id}">Start draft</button>`}</div>`;
      main.innerHTML = `<div class="cards">
        <section class="card"><h2>Due</h2>${week.due.map(dueRow).join("") || '<p class="quiet">Nothing due in the next two weeks. Set rhythms in the <a href="#/calendar">comms calendar</a>.</p>'}</section>
        <section class="card"><h2>In progress</h2>${
          week.drafts.map((m) => `<div class="item">${pill(m.state)}<a href="#/messages/${m.id}">${esc(m.title)}</a></div>`).join("") || '<p class="quiet">No drafts.</p>'
        }<div class="actions"><a class="btn" href="#/messages">New message</a></div></section>
        <section class="card"><h2>Recently sent</h2>${
          week.recently_sent.map((m) => `<div class="item"><a href="#/messages/${m.id}">${esc(m.title)}</a><span class="spacer"></span><span class="quiet">${esc((m.sent_at || "").slice(0, 10))}</span></div>`).join("") ||
          '<p class="quiet">Nothing sent yet.</p>'
        }</section></div>`;
      main.querySelectorAll("[data-draft]").forEach((b) => {
        b.onclick = BA.guard(async () => {
          const m = await BA.api(`/api/comms-due/${b.dataset.draft}/draft`, { method: "POST" });
          BA.go(`/messages/${m.id}`);
        });
      });
    },
  });

  // ---------------------------------------------------------------- Messages

  BA.view("/messages", {
    title: "Messages",
    async render(main, param) {
      if (param) return messageEditor(main, Number(param));
      const [messages, { audiences, templates }] = await Promise.all([BA.api("/api/messages"), lookups()]);
      const names = (ids) => audiences.filter((a) => ids.includes(a.id)).map((a) => a.name).join(", ");
      main.innerHTML = `
        ${presenting() ? '<p class="quiet">Drafts are hidden while presenting; only sent messages show.</p>' : `<section class="card"><h2>New message</h2><form id="new" class="row">
          <select name="template_id" style="max-width:300px"><option value="">Blank message</option>${templates.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select>
          <input name="title" placeholder="Title (optional with a template)" style="max-width:340px">
          <button class="btn primary" type="submit">Create</button></form></section>`}
        <div class="tablewrap"><table class="data"><thead><tr><th>Title</th><th>Type</th><th>State</th><th>Audiences</th></tr></thead><tbody>${
          messages
            .map((m) => `<tr class="clickable" data-id="${m.id}"><td>${esc(m.title)}</td><td>${esc(m.type)}</td><td>${pill(m.state)}</td><td>${esc(names(m.audience_ids || []))}</td></tr>`)
            .join("") || '<tr><td colspan="4" class="empty">No messages yet.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/messages/${tr.dataset.id}`)));
      const form = main.querySelector("#new");
      if (form)
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          const f = new FormData(form);
          const body = {};
          if (f.get("template_id")) body.template_id = Number(f.get("template_id"));
          if (f.get("title")) body.title = f.get("title");
          if (!body.template_id && !body.title) body.title = "[Untitled message]";
          const m = await BA.api("/api/messages", { method: "POST", body });
          BA.go(`/messages/${m.id}`);
        });
    },
  });

  async function messageEditor(main, id) {
    const [m, { audiences, channels }] = await Promise.all([BA.api(`/api/messages/${id}`), lookups()]);
    document.getElementById("view-title").textContent = m.title;
    const locked = m.state === "sent" || m.state === "archived";
    const audienceBoxes = audiences
      .map((a) => `<label class="check"><input type="checkbox" name="aud" value="${a.id}"${(m.audience_ids || []).includes(a.id) ? " checked" : ""}${locked ? " disabled" : ""}> ${esc(a.name)} <span class="quiet">(${esc(a.detail_level || "")})</span></label>`)
      .join("");
    const channelOpts = (sel) => `<option value="">Choose a channel</option>${channels.map((c) => `<option value="${c.id}"${c.id === sel ? " selected" : ""}>${esc(c.name)}</option>`).join("")}`;
    const actions = {
      draft: [["in review", "Send for review"], ["ready", "Mark ready"], ["archived", "Archive"]],
      "in review": [["ready", "Mark ready"], ["draft", "Back to draft"]],
      ready: [["sent", "Mark sent"], ["draft", "Back to draft"]],
      sent: [["archived", "Archive"]],
      archived: [["draft", "Restore as draft"]],
    }[m.state];
    main.innerHTML = `<p><a href="#/messages">All messages</a></p>
      <div class="msg-grid">
        <form id="msg" class="card">
          <div class="row">${pill(m.state)}${m.sent_at ? `<span class="quiet">sent ${esc(m.sent_at)}</span>` : ""}<span class="spacer"></span>
            ${actions.map(([s, label]) => `<button class="btn${s === "ready" || s === "sent" ? " primary" : ""}" type="button" data-state="${s}">${label}</button>`).join("")}</div>
          <div class="grid2">
            <label>Title<input name="title" value="${esc(m.title)}"${locked ? " disabled" : ""}></label>
            <label>Type<select name="type"${locked ? " disabled" : ""}>${MESSAGE_TYPES.map((t) => `<option${t === m.type ? " selected" : ""}>${t}</option>`).join("")}</select></label>
          </div>
          <label>Audiences</label><div class="row">${audienceBoxes || '<span class="quiet">Add audiences under Audiences and channels.</span>'}</div>
          <label>Channel<select name="channel_id"${locked ? " disabled" : ""}>${channelOpts(m.channel_id)}</select></label>
          <label>Message <span class="quiet">Markdown: # headings, - lists, | tables |, **bold**</span>
            <textarea name="body" class="msg-body"${locked ? " readonly" : ""}>${esc(m.body)}</textarea></label>
          <div class="actions"><button class="btn left" type="button" id="dup">Duplicate</button>
            <button class="btn" type="button" data-export="text">Copy text</button>
            <button class="btn" type="button" data-export="markdown">Download .md</button>
            <button class="btn" type="button" data-export="print">Print or save PDF</button></div>
        </form>
        <div>
          <section class="card"><h2>Checks</h2><div id="checks"></div></section>
          <section class="card"><h2>Preview</h2><div id="preview" class="msg-preview"></div></section>
          <section class="card"><h2>Versions</h2><div id="versions"></div></section>
        </div>
      </div>`;
    const form = main.querySelector("#msg");
    const previewEl = main.querySelector("#preview");
    const checksEl = main.querySelector("#checks");

    const showChecks = (results) => {
      checksEl.innerHTML = results
        .map((r) => `<div class="check-row"><span class="pill ${r.result === "pass" ? "good" : r.result === "fail" ? "bad" : "warn"}">${r.result}</span> <b>${esc(r.label)}</b>${r.blocks && r.result === "fail" ? ' <span class="quiet">blocks "ready"</span>' : ""}
          ${r.findings.length ? `<ul class="quiet">${r.findings.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}</div>`)
        .join("");
    };
    const refresh = BA.guard(async () => {
      previewEl.innerHTML = md(form.elements.body.value);
      showChecks(await BA.api("/api/check", { method: "POST", body: { body: form.elements.body.value } }));
    });
    const loadVersions = BA.guard(async () => {
      const vs = await BA.api(`/api/messages/${id}/versions`);
      main.querySelector("#versions").innerHTML =
        vs.map((v, i) => `<div class="item"><span class="quiet">${esc(v.saved_at)} · ${esc(v.source)}</span><span class="spacer"></span>${i && !locked ? `<button class="btn" data-restore="${v.id}">Restore</button>` : i ? "" : '<span class="pill">current</span>'}</div>`).join("") ||
        '<p class="quiet">No versions yet.</p>';
      main.querySelectorAll("[data-restore]").forEach((b) => {
        b.onclick = BA.guard(async () => {
          const v = vs.find((x) => x.id === Number(b.dataset.restore));
          form.elements.body.value = v.body;
          await save();
          refresh();
        });
      });
    });
    const save = BA.guard(async () => {
      if (locked) return;
      await BA.api(`/api/messages/${id}`, {
        method: "PATCH",
        body: {
          title: form.elements.title.value,
          type: form.elements.type.value,
          channel_id: form.elements.channel_id.value ? Number(form.elements.channel_id.value) : null,
          audience_ids: [...form.querySelectorAll('input[name="aud"]:checked')].map((x) => Number(x.value)),
          body: form.elements.body.value,
        },
      });
      loadVersions();
    });
    const saveSoon = debounce(save, 900);
    const refreshSoon = debounce(refresh, 400);
    form.oninput = () => {
      refreshSoon();
      saveSoon();
    };
    form.onchange = (e) => (e.target.tagName === "SELECT" || e.target.type === "checkbox" ? save() : null);

    main.querySelectorAll("[data-state]").forEach((b) => {
      b.onclick = BA.guard(async () => {
        await save();
        const body = { state: b.dataset.state };
        if (body.state === "sent") {
          const ch = form.elements.channel_id.value;
          if (!ch) throw new Error("Choose the channel it went out on first.");
          if (!confirm("Mark this as sent? It's logged with its text and check results, and can't be edited afterwards.")) return;
          body.channel_id = Number(ch);
        }
        await BA.api(`/api/messages/${id}/state`, { method: "POST", body });
        BA.rerender();
      });
    });
    main.querySelector("#dup").onclick = BA.guard(async () => {
      const copy = await BA.api(`/api/messages/${id}/duplicate`, { method: "POST" });
      BA.go(`/messages/${copy.id}`);
    });
    main.querySelectorAll("[data-export]").forEach((b) => {
      b.onclick = BA.guard(async () => {
        await save();
        const fmt = b.dataset.export;
        const res = await BA.api(`/api/messages/${id}/export`, { method: "POST", body: { format: fmt } });
        if (fmt === "text") {
          await navigator.clipboard.writeText(res.body);
          BA.toast("Copied. Logged as an export.");
        } else if (fmt === "markdown") {
          const a = Object.assign(document.createElement("a"), {
            href: URL.createObjectURL(new Blob([res.body], { type: "text/markdown" })),
            download: `${res.title.replace(/[^\w\- ]+/g, "").trim() || "message"}.md`,
          });
          a.click();
        } else {
          const w = window.open("", "_blank");
          w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(res.title)}</title>
            <style>body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#1c1c1a}
            table{border-collapse:collapse;width:100%;margin:12px 0}th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}th{background:#f2f1ed}</style></head>
            <body><h1>${esc(res.title)}</h1>${md(res.body)}</body></html>`);
          w.document.close();
          w.focus();
          w.print();
        }
      });
    });
    refresh();
    loadVersions();
  }

  // ---------------------------------------------------------------- Templates

  BA.view("/templates", {
    title: "Templates",
    async render(main, param) {
      const { audiences, channels, templates } = await lookups();
      if (param) {
        const t = templates.find((x) => x.id === Number(param));
        if (!t) throw new Error("No template with that id.");
        document.getElementById("view-title").textContent = t.name;
        main.innerHTML = `<p><a href="#/templates">All templates</a></p><form id="tpl" class="card">
          <div class="grid2"><label>Name<input name="name" value="${esc(t.name)}"></label>
          <label>Type<select name="type">${MESSAGE_TYPES.map((x) => `<option${x === t.type ? " selected" : ""}>${x}</option>`).join("")}</select></label></div>
          <label>Default audiences</label><div class="row">${audiences.map((a) => `<label class="check"><input type="checkbox" name="aud" value="${a.id}"${t.audience_ids.includes(a.id) ? " checked" : ""}> ${esc(a.name)}</label>`).join("")}</div>
          <label>Default channel<select name="channel_id"><option value=""></option>${channels.map((c) => `<option value="${c.id}"${c.id === t.channel_id ? " selected" : ""}>${esc(c.name)}</option>`).join("")}</select></label>
          <label>Body <span class="quiet">keep sections as [Placeholder: …] so the check catches anything left unfilled</span><textarea name="body" class="msg-body">${esc(t.body)}</textarea></label>
          <div class="actions"><button class="btn danger left" type="button" id="del">Delete</button><button class="btn" type="button" id="use">Write a message from this</button><button class="btn primary" type="submit">Save</button></div></form>`;
        const form = main.querySelector("#tpl");
        const body = () => ({
          name: form.elements.name.value,
          type: form.elements.type.value,
          body: form.elements.body.value,
          channel_id: form.elements.channel_id.value ? Number(form.elements.channel_id.value) : null,
          audience_ids: [...form.querySelectorAll('input[name="aud"]:checked')].map((x) => Number(x.value)),
        });
        form.onsubmit = BA.guard(async (e) => {
          e.preventDefault();
          await BA.api(`/api/templates/${t.id}`, { method: "PATCH", body: body() });
          BA.toast("Saved.");
        });
        main.querySelector("#use").onclick = BA.guard(async () => {
          await BA.api(`/api/templates/${t.id}`, { method: "PATCH", body: body() });
          const m = await BA.api("/api/messages", { method: "POST", body: { template_id: t.id } });
          BA.go(`/messages/${m.id}`);
        });
        main.querySelector("#del").onclick = BA.guard(async () => {
          if (!confirm("Delete this template? Messages made from it stay.")) return;
          await BA.api(`/api/templates/${t.id}`, { method: "DELETE" });
          BA.go("/templates");
        });
        return;
      }
      main.innerHTML = `<section class="card"><form id="new" class="row"><input name="name" placeholder="New template name" required style="max-width:340px">
        <button class="btn primary" type="submit">Add template</button></form></section>
        <div class="tablewrap"><table class="data"><thead><tr><th>Template</th><th>Type</th><th>Default audiences</th></tr></thead><tbody>${
          templates
            .map((t) => `<tr class="clickable" data-id="${t.id}"><td>${esc(t.name)}</td><td>${esc(t.type)}</td><td>${esc(audiences.filter((a) => t.audience_ids.includes(a.id)).map((a) => a.name).join(", "))}</td></tr>`)
            .join("") || '<tr><td colspan="3" class="empty">No templates yet. Load the starter kit from This week.</td></tr>'
        }</tbody></table></div>`;
      main.querySelectorAll("tr[data-id]").forEach((tr) => (tr.onclick = () => BA.go(`/templates/${tr.dataset.id}`)));
      main.querySelector("#new").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const t = await BA.api("/api/templates", { method: "POST", body: { name: new FormData(e.target).get("name"), body: "[Placeholder: opening line]" } });
        BA.go(`/templates/${t.id}`);
      });
    },
  });

  // ---------------------------------------------------------------- Comms calendar

  BA.view("/calendar", {
    title: "Comms calendar",
    async render(main) {
      const [cadences, due, templates] = await Promise.all([BA.api("/api/cadences"), BA.api("/api/comms-due"), BA.api("/api/templates")]);
      const tplName = (id) => templates.find((t) => t.id === id)?.name || "";
      main.innerHTML = `
        <section class="card"><h2>Rhythms</h2>
          <p class="quiet">Each rhythm creates due items from its first due date onward. Drafting starts "lead days" before each one.</p>
          <div class="tablewrap"><table class="data"><thead><tr><th>Rhythm</th><th>Type</th><th>Repeats</th><th>First due</th><th>Lead days</th><th>Template</th><th>On</th><th></th></tr></thead><tbody>${
            cadences
              .map((c) => `<tr><td>${esc(c.title)}</td><td>${esc(c.message_type)}</td><td>${esc(c.rhythm)}</td><td>${BA.fmtDate(c.next_due)}</td><td>${c.lead_days}</td>
                <td>${esc(tplName(c.template_id))}</td><td><input type="checkbox" data-active="${c.id}"${c.active ? " checked" : ""}></td>
                <td><button class="btn danger" data-del="${c.id}">Delete</button></td></tr>`)
              .join("") || '<tr><td colspan="8" class="empty">No rhythms yet.</td></tr>'
          }</tbody></table></div>
          <form id="add" class="grid2">
            <label>Name<input name="title" required placeholder="[Placeholder rhythm name]"></label>
            <label>Type<select name="message_type">${MESSAGE_TYPES.map((t) => `<option>${t}</option>`).join("")}</select></label>
            <label>Repeats<select name="rhythm">${RHYTHMS.map((r) => `<option>${r}</option>`).join("")}</select></label>
            <label>First due<input type="date" name="next_due" required value="${BA.today()}"></label>
            <label>Lead days<input type="number" name="lead_days" value="2" min="0"></label>
            <label>Template<select name="template_id"><option value=""></option>${templates.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select></label>
            <div class="actions"><button class="btn primary" type="submit">Add rhythm</button></div></form></section>
        <section class="card"><h2>Due items</h2>${
          due.map((d) => `<div class="item">${pill(d.status)}<span>${esc(d.title)}</span><span class="spacer"></span><span class="quiet">${BA.fmtDate(d.due)}</span>
            ${d.message_id ? `<a class="btn" href="#/messages/${d.message_id}">Open</a>` : `<button class="btn" data-draft="${d.id}">Start draft</button>`}</div>`).join("") ||
          '<p class="quiet">Nothing scheduled.</p>'
        }</section>`;
      main.querySelector("#add").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(e.target);
        await BA.api("/api/cadences", {
          method: "POST",
          body: {
            title: f.get("title"),
            message_type: f.get("message_type"),
            rhythm: f.get("rhythm"),
            next_due: f.get("next_due"),
            lead_days: Number(f.get("lead_days") || 0),
            template_id: f.get("template_id") ? Number(f.get("template_id")) : null,
          },
        });
        BA.rerender();
      });
      main.querySelectorAll("[data-active]").forEach((el) => (el.onchange = BA.guard(async () => {
        await BA.api(`/api/cadences/${el.dataset.active}`, { method: "PATCH", body: { active: el.checked } });
        BA.rerender();
      })));
      main.querySelectorAll("[data-del]").forEach((el) => (el.onclick = BA.guard(async () => {
        if (!confirm("Delete this rhythm and its upcoming due items?")) return;
        await BA.api(`/api/cadences/${el.dataset.del}`, { method: "DELETE" });
        BA.rerender();
      })));
      main.querySelectorAll("[data-draft]").forEach((b) => (b.onclick = BA.guard(async () => {
        const m = await BA.api(`/api/comms-due/${b.dataset.draft}/draft`, { method: "POST" });
        BA.go(`/messages/${m.id}`);
      })));
    },
  });

  // ---------------------------------------------------------------- Sent log

  BA.view("/sent", {
    title: "Sent log",
    async render(main) {
      const rows = await BA.api("/api/sent-log");
      main.innerHTML = `<p class="quiet">Every message marked sent, with when, where and to whom. The text is kept exactly as sent.</p>
        <div class="tablewrap"><table class="data"><thead><tr><th>Sent</th><th>Message</th><th>Type</th><th>Channel</th><th>Audiences</th><th>Check warnings</th></tr></thead><tbody>${
          rows
            .map((r) => `<tr><td>${esc(r.sent_at)}</td><td>${r.message_id ? `<a href="#/messages/${r.message_id}">${esc(r.title)}</a>` : esc(r.title)}</td><td>${esc(r.type)}</td>
              <td>${esc(r.channel)}</td><td>${esc(r.audiences.join(", "))}</td><td>${r.warnings}</td></tr>`)
            .join("") || '<tr><td colspan="6" class="empty">Nothing sent yet.</td></tr>'
        }</tbody></table></div>`;
    },
  });

  // ---------------------------------------------------------------- Audiences and channels

  BA.view("/audiences", {
    title: "Audiences and channels",
    async render(main) {
      const { audiences, channels } = await lookups();
      const chOpts = (sel) => `<option value=""></option>${channels.map((c) => `<option value="${c.id}"${c.id === sel ? " selected" : ""}>${esc(c.name)}</option>`).join("")}`;
      main.innerHTML = `
        <section class="card"><h2>Audiences</h2><p class="quiet">Who needs what from engineering. Changes save as you go.</p>
          <div class="tablewrap"><table class="data"><thead><tr><th>Audience</th><th>What they need</th><th>Detail level</th><th>Usual channel</th><th></th></tr></thead><tbody>${audiences
            .map((a) => `<tr data-aud="${a.id}"><td><input name="name" value="${esc(a.name)}"></td><td><input name="needs" value="${esc(a.needs)}"></td>
              <td><select name="detail_level"><option value=""></option>${DETAIL_LEVELS.map((d) => `<option${d === a.detail_level ? " selected" : ""}>${d}</option>`).join("")}</select></td>
              <td><select name="channel_id">${chOpts(a.channel_id)}</select></td><td><button class="btn danger" data-del-aud="${a.id}">Delete</button></td></tr>`)
            .join("")}</tbody></table></div>
          <form id="add-aud" class="row"><input name="name" placeholder="New audience" required style="max-width:300px"><button class="btn primary" type="submit">Add audience</button></form></section>
        <section class="card"><h2>Channels</h2>
          <div class="tablewrap"><table class="data"><thead><tr><th>Channel</th><th>Kind</th><th>Notes</th><th></th></tr></thead><tbody>${channels
            .map((c) => `<tr data-ch="${c.id}"><td><input name="name" value="${esc(c.name)}"></td>
              <td><select name="kind">${CHANNEL_KINDS.map((k) => `<option${k === c.kind ? " selected" : ""}>${k}</option>`).join("")}</select></td>
              <td><input name="notes" value="${esc(c.notes)}"></td><td><button class="btn danger" data-del-ch="${c.id}">Delete</button></td></tr>`)
            .join("")}</tbody></table></div>
          <form id="add-ch" class="row"><input name="name" placeholder="[Placeholder channel name]" required style="max-width:300px"><button class="btn primary" type="submit">Add channel</button></form></section>`;
      const wire = (attr, path) =>
        main.querySelectorAll(`tr[${attr}]`).forEach((tr) => {
          tr.onchange = BA.guard(async (e) => {
            const el = e.target;
            const value = el.name === "channel_id" ? (el.value ? Number(el.value) : null) : el.value;
            await BA.api(`${path}/${tr.getAttribute(attr)}`, { method: "PATCH", body: { [el.name]: value } });
            BA.toast("Saved.");
          });
        });
      wire("data-aud", "/api/audiences");
      wire("data-ch", "/api/channels");
      const del = (attr, path) =>
        main.querySelectorAll(`[${attr}]`).forEach((b) => (b.onclick = BA.guard(async () => {
          if (!confirm("Delete it?")) return;
          await BA.api(`${path}/${b.getAttribute(attr)}`, { method: "DELETE" });
          BA.rerender();
        })));
      del("data-del-aud", "/api/audiences");
      del("data-del-ch", "/api/channels");
      main.querySelector("#add-aud").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/audiences", { method: "POST", body: { name: new FormData(e.target).get("name") } });
        BA.rerender();
      });
      main.querySelector("#add-ch").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        await BA.api("/api/channels", { method: "POST", body: { name: new FormData(e.target).get("name") } });
        BA.rerender();
      });
    },
  });

  // ---------------------------------------------------------------- Plain language

  BA.view("/plain-language", {
    title: "Plain language",
    async render(main) {
      const [terms, builtIn] = await Promise.all([BA.api("/api/glossary"), BA.api("/api/plain-language/jargon")]);
      main.innerHTML = `
        <section class="card"><h2>My terms</h2><p class="quiet">Platform terms, acronyms or jargon to flag in messages, with the plain way to say it. These also feed the stakeholder explainers later.</p>
          ${terms.map((t) => `<div class="item"><b>${esc(t.term)}</b><span class="quiet">${t.plain ? "→ " + esc(t.plain) : ""}</span><span class="spacer"></span><button class="btn danger" data-del="${t.id}">Delete</button></div>`).join("") || '<p class="quiet">None yet.</p>'}
          <form id="add" class="row"><input name="term" placeholder="Term, for example an acronym" required style="max-width:240px">
            <input name="plain" placeholder="Plain alternative" style="max-width:300px"><button class="btn primary" type="submit">Add term</button></form></section>
        <section class="card"><h2>Built-in list</h2><p class="quiet">Always checked.</p>
          ${builtIn.map((t) => `<span class="pill">${esc(t.term)} → ${esc(t.plain)}</span>`).join(" ")}</section>`;
      main.querySelector("#add").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(e.target);
        await BA.api("/api/glossary", { method: "POST", body: { term: f.get("term"), plain: f.get("plain") } });
        BA.rerender();
      });
      main.querySelectorAll("[data-del]").forEach((b) => (b.onclick = BA.guard(async () => {
        await BA.api(`/api/glossary/${b.dataset.del}`, { method: "DELETE" });
        BA.rerender();
      })));
    },
  });

  // ---------------------------------------------------------------- Decks

  BA.view("/decks", {
    title: "Decks",
    async render(main, param) {
      if (param) return editor(main, Number(param));
      const decks = await BA.api("/api/decks");
      main.innerHTML = `
        <section class="card"><form id="new-deck" class="row">
          <input name="title" placeholder="[Placeholder deck title]" required style="max-width:420px">
          <button class="btn primary" type="submit">New deck</button><span class="spacer"></span>
          <button class="btn" type="button" id="seed">Load placeholder deck</button></form></section>
        <div class="deck-cards">${
          decks.map((d) => `<div class="card deck-card" data-id="${d.id}"><h2>${esc(d.title)}</h2><p class="quiet">${d.slide_count} slides · ${esc(d.transition)} transition</p></div>`).join("") ||
          '<p class="empty">No decks yet.</p>'
        }</div>`;
      main.querySelectorAll(".deck-card").forEach((c) => (c.onclick = () => BA.go(`/decks/${c.dataset.id}`)));
      main.querySelector("#new-deck").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const deck = await BA.api("/api/decks", { method: "POST", body: { title: new FormData(e.target).get("title") } });
        await BA.api(`/api/decks/${deck.id}/slides`, { method: "POST", body: { layout: "title", content: { heading: deck.title } } });
        BA.go(`/decks/${deck.id}`);
      });
      main.querySelector("#seed").onclick = BA.guard(async () => {
        const res = await BA.api("/api/comms/seed-placeholders", { method: "POST" });
        BA.go(`/decks/${res.deck_id}`);
      });
    },
  });

  // ---- the deck builder ----

  async function editor(main, deckId) {
    await loadAssets();
    const { LAYOUTS, render, attach } = window.BADeck;
    let data = await BA.api(`/api/decks/${deckId}/full`);
    let current = data.slides[0]?.id ?? null;
    document.getElementById("view-title").textContent = data.deck.title;
    main.dataset.layout = "editor";
    main.innerHTML = `<div class="ed">
      <div class="ed-bar">
        <input id="deck-title" value="${esc(data.deck.title)}" aria-label="Deck title">
        <select id="deck-transition" aria-label="Transition">${TRANSITIONS.map((t) => `<option${t === data.deck.transition ? " selected" : ""}>${t}</option>`).join("")}</select>
        <span class="spacer"></span><a class="btn" href="#/decks">All decks</a>
        <button class="btn primary" id="present" type="button">Present</button></div>
      <aside class="ed-list"><div id="slide-list"></div>
        <div class="ed-add"><select id="new-layout">${Object.entries(LAYOUTS).map(([k, l]) => `<option value="${k}">${esc(l.label)}</option>`).join("")}</select>
        <button class="btn" id="add-slide" type="button">Add slide</button></div></aside>
      <section class="ed-canvas"><div class="ed-stage"><div class="reveal ba-theme" id="ed-reveal" tabindex="0"><div class="slides"></div></div></div>
        <p class="quiet">Click the slide, then use the arrow keys to step through reveals. Present opens it full screen; press S there for speaker notes.</p></section>
      <aside class="ed-inspector" id="inspector"></aside></div>`;

    const listEl = main.querySelector("#slide-list");
    const inspector = main.querySelector("#inspector");
    const revealEl = main.querySelector("#ed-reveal");
    const deck = new Reveal(revealEl, {
      embedded: true,
      keyboardCondition: "focused",
      hash: false,
      center: false,
      progress: false,
      width: 1280,
      height: 720,
      margin: 0.04,
      transition: data.deck.transition,
    });
    const runtime = attach(deck);
    await deck.initialize();
    BA.cleanup = () => {
      runtime.clear();
      deck.destroy();
    };

    const slide = () => data.slides.find((s) => s.id === current);
    const indexOf = (id) => data.slides.findIndex((s) => s.id === id);
    const titleOf = (s) => s.content?.heading || s.content?.quote || "[Untitled]";

    async function reload(selectId) {
      data = await BA.api(`/api/decks/${deckId}/full`);
      current = selectId ?? (data.slides.some((s) => s.id === current) ? current : data.slides[0]?.id ?? null);
      renderAll();
    }

    function renderCanvas() {
      runtime.clear();
      revealEl.querySelector(".slides").innerHTML = render(data.slides, data.media, { includeHidden: true });
      deck.sync();
      const i = indexOf(current);
      runtime.quietly(() => {
        if (i >= 0) deck.slide(i, 0, 99);
        runtime.refresh();
      });
    }

    function renderList() {
      listEl.innerHTML =
        data.slides
          .map((s, i) => `<div class="ed-thumb${s.id === current ? " on" : ""}${s.hidden ? " is-hidden" : ""}" draggable="true" data-id="${s.id}">
            <span class="ed-num">${i + 1}</span><div><div class="ed-thumb-title">${esc(titleOf(s))}</div>
            <div class="quiet">${esc(LAYOUTS[s.layout]?.label || s.layout)}${s.hidden ? " · hidden" : ""}</div></div></div>`)
          .join("") || '<p class="quiet">No slides yet.</p>';
      let dragId = null;
      listEl.querySelectorAll(".ed-thumb").forEach((el) => {
        const id = Number(el.dataset.id);
        el.onclick = () => select(id);
        el.ondragstart = () => (dragId = id);
        el.ondragover = (e) => {
          e.preventDefault();
          el.classList.add("drop-before");
        };
        el.ondragleave = () => el.classList.remove("drop-before");
        el.ondrop = BA.guard(async (e) => {
          e.preventDefault();
          el.classList.remove("drop-before");
          if (dragId === null || dragId === id) return;
          const order = data.slides.map((s) => s.id).filter((x) => x !== dragId);
          order.splice(order.indexOf(id), 0, dragId);
          data.slides = await BA.api(`/api/decks/${deckId}/reorder`, { method: "POST", body: { slide_ids: order } });
          renderAll();
        });
      });
    }

    function select(id) {
      current = id;
      renderList();
      renderInspector();
      const i = indexOf(id);
      if (i >= 0 && deck.getIndices().h !== i) runtime.quietly(() => deck.slide(i, 0, 99));
    }

    deck.on("slidechanged", (e) => {
      const id = Number(e.currentSlide?.dataset.slideId);
      if (id && id !== current) {
        current = id;
        renderList();
        renderInspector();
      }
    });

    // ---- inspector ----

    function field(f, v) {
      const name = `c.${f.name}`;
      const hint = f.hint ? ` <span class="quiet">${esc(f.hint)}</span>` : "";
      const wrap = (control) => `<label>${esc(f.label)}${hint}${control}</label>`;
      switch (f.type) {
        case "lines":
          return wrap(`<textarea name="${name}">${esc((v || []).join("\n"))}</textarea>`);
        case "textarea":
          return wrap(`<textarea name="${name}">${esc(v)}</textarea>`);
        case "checkbox":
          return `<label class="check"><input type="checkbox" name="${name}"${v ? " checked" : ""}> ${esc(f.label)}</label>`;
        case "number":
          return wrap(`<input type="number" name="${name}" step="${f.step || 1}" value="${esc(v ?? "")}">`);
        case "select":
          return wrap(`<select name="${name}">${f.options.map(([val, label]) => `<option value="${val}"${val === (v || f.options[0][0]) ? " selected" : ""}>${esc(label)}</option>`).join("")}</select>`);
        case "media": {
          const opts = data.media.filter((m) => m.kind === f.kind);
          return wrap(`<span class="media-pick"><select name="${name}" data-kind="${f.kind}"><option value="">None</option>${opts
            .map((m) => `<option value="${m.id}"${m.id === v ? " selected" : ""}>${esc(m.name)}</option>`)
            .join("")}</select><button class="btn" type="button" data-upload="${f.name}" data-kind="${f.kind}">Upload</button></span>`);
        }
        default:
          return wrap(`<input name="${name}" value="${esc(v)}">`);
      }
    }

    function readContent(form, spec) {
      const content = {};
      for (const f of spec.fields) {
        const el = form.elements[`c.${f.name}`];
        if (!el) continue;
        if (f.type === "lines") content[f.name] = el.value.split("\n").map((s) => s.trim()).filter(Boolean);
        else if (f.type === "checkbox") content[f.name] = el.checked;
        else if (f.type === "number" || f.type === "media") content[f.name] = el.value === "" ? null : Number(el.value);
        else content[f.name] = el.value;
      }
      return content;
    }

    function renderInspector() {
      const s = slide();
      if (!s) {
        inspector.innerHTML = '<p class="quiet">Add a slide to start.</p>';
        return;
      }
      const spec = LAYOUTS[s.layout] || { fields: [] };
      inspector.innerHTML = `<h2>Slide ${indexOf(s.id) + 1}</h2><form id="insp">
        <label>Layout<select name="layout">${Object.entries(LAYOUTS).map(([k, l]) => `<option value="${k}"${k === s.layout ? " selected" : ""}>${esc(l.label)}</option>`).join("")}</select></label>
        ${spec.fields.map((f) => field(f, s.content?.[f.name])).join("")}
        <label>Transition<select name="transition"><option value="">Deck default</option>${TRANSITIONS.map((t) => `<option${t === s.transition ? " selected" : ""}>${t}</option>`).join("")}</select></label>
        <label>Speaker notes<textarea name="notes">${esc(s.notes)}</textarea></label>
        <label class="check"><input type="checkbox" name="hidden"${s.hidden ? " checked" : ""}> Hide this slide when presenting</label>
        <div class="actions"><button class="btn danger left" type="button" id="del-slide">Delete</button><button class="btn" type="button" id="dup-slide">Duplicate</button></div>
        <input type="file" id="insp-file" hidden></form>`;
      const form = inspector.querySelector("#insp");
      const save = BA.guard(async (relayout) => {
        const body = {
          layout: form.elements.layout.value,
          content: { ...(s.content || {}), ...readContent(form, spec) },
          notes: form.elements.notes.value,
          transition: form.elements.transition.value,
          hidden: form.elements.hidden.checked,
        };
        const updated = await BA.api(`/api/slides/${s.id}`, { method: "PATCH", body });
        data.slides[indexOf(s.id)] = updated;
        renderList();
        renderCanvas();
        if (relayout) renderInspector();
      });
      const saveSoon = debounce(() => save(false), 450);
      form.oninput = (e) => (e.target.type === "text" || e.target.tagName === "TEXTAREA" || e.target.type === "number" ? saveSoon() : null);
      form.onchange = (e) => {
        if (e.target.type === "file") return;
        if (e.target.tagName === "SELECT" || e.target.type === "checkbox") save(e.target.name === "layout");
      };
      inspector.querySelector("#del-slide").onclick = BA.guard(async () => {
        if (!confirm("Delete this slide?")) return;
        const i = indexOf(s.id);
        await BA.api(`/api/slides/${s.id}`, { method: "DELETE" });
        await reload(data.slides[i + 1]?.id ?? data.slides[i - 1]?.id ?? null);
      });
      inspector.querySelector("#dup-slide").onclick = BA.guard(async () => {
        const copy = await BA.api(`/api/slides/${s.id}/duplicate`, { method: "POST" });
        await reload(copy.id);
      });
      const fileInput = inspector.querySelector("#insp-file");
      inspector.querySelectorAll("[data-upload]").forEach((btn) => {
        btn.onclick = () => {
          fileInput.dataset.field = btn.dataset.upload;
          fileInput.accept = { video: "video/*", audio: "audio/*", image: "image/*", lottie: ".json", captions: ".vtt" }[btn.dataset.kind];
          fileInput.click();
        };
      });
      fileInput.onchange = BA.guard(async () => {
        const file = fileInput.files[0];
        if (!file) return;
        BA.toast("Uploading…");
        const rec = await upload(file);
        data.media.unshift(rec);
        const content = { ...(s.content || {}), ...readContent(form, spec), [fileInput.dataset.field]: rec.id };
        const updated = await BA.api(`/api/slides/${s.id}`, { method: "PATCH", body: { content } });
        data.slides[indexOf(s.id)] = updated;
        renderAll();
        BA.toast("Uploaded.");
      });
    }

    function renderAll() {
      renderList();
      renderCanvas();
      renderInspector();
    }

    main.querySelector("#add-slide").onclick = BA.guard(async () => {
      const layout = main.querySelector("#new-layout").value;
      const created = await BA.api(`/api/decks/${deckId}/slides`, { method: "POST", body: { layout, content: {}, after_id: current } });
      await reload(created.id);
    });
    main.querySelector("#deck-title").onchange = BA.guard(async (e) => {
      await BA.api(`/api/decks/${deckId}`, { method: "PATCH", body: { title: e.target.value } });
      document.getElementById("view-title").textContent = e.target.value;
    });
    main.querySelector("#deck-transition").onchange = BA.guard(async (e) => {
      await BA.api(`/api/decks/${deckId}`, { method: "PATCH", body: { transition: e.target.value } });
      deck.configure({ transition: e.target.value });
    });
    main.querySelector("#present").onclick = () => window.open(`/present/${deckId}#/${Math.max(0, indexOf(current))}`, "_blank");

    renderAll();
  }

  // ---------------------------------------------------------------- Media library

  BA.view("/media", {
    title: "Media library",
    async render(main) {
      await loadAssets();
      const items = await BA.api("/api/media");
      main.innerHTML = `
        <section class="card"><h2>Add media</h2>
          <p class="quiet">Video, audio, images, Lottie animations (.json) and captions (.vtt). Files stay on this computer. Licensed files, such as Envato Elements downloads, are never committed to the code repository.</p>
          <form id="up" class="grid2">
            <label>File<input type="file" name="file" required></label>
            <label>Name<input name="name" placeholder="[Placeholder name]"></label>
            <label>Source<select name="source">${SOURCES.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")}</select></label>
            <label>License reference<input name="license_ref" placeholder="[Placeholder license or item link]"></label>
            <div class="actions"><button class="btn primary" type="submit">Upload</button></div></form></section>
        <div class="media-grid">${
          items
            .map((m) => {
              const src = `/api/media/${m.id}/file`;
              const preview = {
                video: `<video src="${src}" controls preload="metadata"></video>`,
                audio: `<audio src="${src}" controls preload="metadata"></audio>`,
                image: `<img src="${src}" alt="${esc(m.name)}">`,
                lottie: `<div class="lottie-preview" data-src="${src}"></div>`,
                captions: '<p class="quiet">WebVTT captions</p>',
              }[m.kind];
              return `<div class="media-card"><div>${preview}</div>
                <input value="${esc(m.name)}" data-rename="${m.id}" aria-label="Name">
                <div class="row"><span class="pill">${esc(m.kind)}</span><span class="pill">${esc(m.source)}</span>
                <span class="quiet">${Math.max(1, Math.round(m.size_bytes / 1024))} KB</span><span class="spacer"></span>
                <button class="btn danger" data-del="${m.id}">Delete</button></div></div>`;
            })
            .join("") || '<p class="empty">No media yet.</p>'
        }</div>`;
      const anims = [];
      main.querySelectorAll(".lottie-preview").forEach((el) => {
        anims.push(window.lottie.loadAnimation({ container: el, renderer: "svg", loop: true, autoplay: true, path: el.dataset.src }));
      });
      BA.cleanup = () => anims.forEach((a) => a.destroy());
      main.querySelector("#up").onsubmit = BA.guard(async (e) => {
        e.preventDefault();
        const f = new FormData(e.target);
        BA.toast("Uploading…");
        await upload(f.get("file"), { name: f.get("name"), source: f.get("source"), license_ref: f.get("license_ref") });
        BA.rerender();
      });
      main.querySelectorAll("[data-rename]").forEach((el) => {
        el.onchange = BA.guard(() => BA.api(`/api/media/${el.dataset.rename}`, { method: "PATCH", body: { name: el.value } }));
      });
      main.querySelectorAll("[data-del]").forEach((el) => {
        el.onclick = BA.guard(async () => {
          if (!confirm("Delete this file? Slides using it will show a placeholder.")) return;
          await BA.api(`/api/media/${el.dataset.del}`, { method: "DELETE" });
          BA.rerender();
        });
      });
    },
  });
})();
