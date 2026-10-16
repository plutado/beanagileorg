// Shared UI shell: API helper, hash router, navigation, presentation mode and the security settings view.
// Apps load after this file and register their screens with BA.view(path, {title, render}).
(function () {
  const BA = (window.BA = { views: {}, session: null });

  BA.esc = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  BA.api = async (path, opts = {}) => {
    const init = { credentials: "same-origin", headers: { "Content-Type": "application/json" }, ...opts };
    if (init.body !== undefined && typeof init.body !== "string") init.body = JSON.stringify(init.body);
    const res = await fetch(path, init);
    if (res.status === 401) {
      location.href = "/login";
      throw new Error("Not signed in");
    }
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(typeof detail.detail === "string" ? detail.detail : res.statusText);
    }
    return res.status === 204 ? null : res.json();
  };

  BA.icon = (name, cls = "") =>
    `<svg class="icon ${cls}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="/core-static/vendor/icons.svg#${name}"></use></svg>`;

  BA.toast = (message) => {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.hidden = false;
    clearTimeout(BA._toastTimer);
    BA._toastTimer = setTimeout(() => (el.hidden = true), 3000);
  };

  BA.view = (path, def) => {
    BA.views[path] = def;
  };

  // ---- small helpers shared by app screens ----

  BA.today = () => {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  };

  BA.fmtDate = (s) =>
    s ? new Date(s + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "";

  BA.chips = (items) => (items || []).map((x) => `<span class="pill">${BA.esc(x)}</span>`).join(" ");

  BA.statusPill = (s) => {
    const cls = { done: "good", "at risk": "bad", "in progress": "warn", planned: "warn", open: "warn" }[s] || "";
    return s ? `<span class="pill ${cls}">${BA.esc(s)}</span>` : "";
  };

  // Field spec: {name, label, type: text|textarea|date|number|select|list|checkbox, options, numeric}
  BA.input = (f, value) => {
    const id = `f-${f.name}`;
    const v = value ?? (f.type === "list" ? [] : "");
    const attrs = `id="${id}" name="${BA.esc(f.name)}"${f.required ? " required" : ""}${f.placeholder ? ` placeholder="${BA.esc(f.placeholder)}"` : ""}`;
    let control;
    switch (f.type) {
      case "textarea":
        control = `<textarea ${attrs}>${BA.esc(v)}</textarea>`;
        break;
      case "select":
        control = `<select ${attrs}>${f.blank !== false ? '<option value=""></option>' : ""}${f.options
          .map((o) => {
            const val = o.value ?? o;
            return `<option value="${BA.esc(val)}"${String(val) === String(v) ? " selected" : ""}>${BA.esc(o.label ?? o)}</option>`;
          })
          .join("")}</select>`;
        break;
      case "list":
      case "keys":
        control = `<input ${attrs} value="${BA.esc(v.join(", "))}">`;
        break;
      case "checkbox":
        return `<label class="check"><input type="checkbox" ${attrs}${v ? " checked" : ""}> ${BA.esc(f.label)}</label>`;
      case "number":
        control = `<input type="number" ${attrs} value="${BA.esc(v)}">`;
        break;
      case "date":
        control = `<input type="date" ${attrs} value="${BA.esc(v)}">`;
        break;
      default:
        control = `<input ${attrs} value="${BA.esc(v)}">`;
    }
    const hint = f.hint ? ` <span class="quiet">${BA.esc(f.hint)}</span>` : "";
    return `<label for="${id}">${BA.esc(f.label)}${hint}${control}</label>`;
  };

  BA.form = (fields, rec = {}) => fields.map((f) => BA.input(f, rec[f.name])).join("");

  BA.readForm = (form, fields) => {
    const out = {};
    for (const f of fields) {
      const el = form.elements[f.name];
      if (!el) continue;
      if (f.type === "list") out[f.name] = el.value.split(",").map((s) => s.trim()).filter(Boolean);
      else if (f.type === "keys") out[f.name] = el.value;
      else if (f.type === "checkbox") out[f.name] = el.checked;
      else if (f.type === "number" || f.numeric) out[f.name] = el.value === "" ? null : Number(el.value);
      else out[f.name] = el.value;
    }
    return out;
  };

  // Read-only view of whatever fields the server returned (used in presentation mode).
  BA.readOnly = (fields, rec) =>
    `<dl class="readonly">${fields
      .filter((f) => rec[f.name] !== undefined && rec[f.name] !== null && rec[f.name] !== "")
      .map((f) => {
        const v = rec[f.name];
        const shown = Array.isArray(v) ? BA.chips(v) : typeof v === "boolean" ? (v ? "Yes" : "No") : BA.esc(v);
        return `<dt>${BA.esc(f.label)}</dt><dd>${shown}</dd>`;
      })
      .join("")}</dl>`;


  // Minimal, safe Markdown for previews: headings, lists, tables, bold, italics, paragraphs.
  BA.md = (text) => {
    const esc = BA.esc;
    // Escaped first, so only these patterns become markup; links must be http(s).
    const inline = (s) =>
      esc(s)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
        .replace(/(^|\W)_(.+?)_(?=\W|$)/g, "$1<i>$2</i>");
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
        out.push(`<div class="tablewrap"><table class="data"><thead><tr>${cells(body[0]).map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${body
          .slice(1)
          .map((r) => `<tr>${cells(r).map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`)
          .join("")}</tbody></table></div>`);
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
    return `<div class="md">${out.join("")}</div>`;
  };

  // Backups: each one is restored to a scratch folder and checked before it counts.
  async function renderBackups(el) {
    const d = await BA.api("/api/backups");
    const last = d.backups[0];
    const kb = (n) => `${Math.max(1, Math.round(n / 1024))} KB`;
    el.innerHTML = `<h2>Backups</h2>
      <p class="quiet">Each backup is a snapshot of this app's data, checked straight away by restoring it to a scratch folder and comparing every table. Kept in <code>${BA.esc(d.location)}</code>.</p>
      <div class="row">${last ? `<span class="pill ${last.ok ? "good" : "bad"}">${last.ok ? "last backup checked" : "last backup failed its check"}</span><span class="quiet">${BA.esc(last.at || last.file)}</span>` : '<span class="pill warn">no backups yet</span>'}
        <span class="pill ${d.scheduled ? "good" : "warn"}">${d.scheduled ? "nightly schedule saved" : "no nightly schedule"}</span><span class="spacer"></span><button class="btn primary" id="backup-now">Back up now</button></div>
      ${d.backups.length ? `<div class="tablewrap"><table class="data"><thead><tr><th>Backup</th><th>Size</th><th>Rows</th><th>Check</th></tr></thead><tbody>${d.backups
        .map((b) => `<tr><td>${BA.esc(b.file)}</td><td>${kb(b.bytes)}</td><td>${b.rows ?? ""}</td><td>${b.ok ? '<span class="pill good">restores cleanly</span>' : b.ok === false ? `<span class="pill bad" title="${BA.esc((b.problems || []).join("; "))}">failed</span>` : '<span class="quiet">not checked</span>'}</td></tr>`)
        .join("")}</tbody></table></div>${d.count > d.backups.length ? `<p class="quiet">${d.count - d.backups.length} older backups not shown.</p>` : ""}` : ""}
      <p class="quiet">Nightly backups and restores run from the terminal: <code>beanagileorg schedule --write</code> saves a nightly job, and <code>beanagileorg restore FILE --app ${BA.esc(BA.session.app)}</code> puts a backup back (stop the app first).</p>`;
    el.querySelector("#backup-now").onclick = BA.guard(async () => {
      const r = await BA.api("/api/backups", { method: "POST" });
      BA.toast(r.ok ? "Backed up and checked." : "The backup failed its check: " + r.problems.join("; "));
      renderBackups(el);
    });
  }

  // Coaching tips: a short nudge at the top of each landing page, pointing to a guide. Hidden while presenting.
  const COACH_OFF = "ba-coach-off", COACH_HIDDEN = "ba-coach-hidden";
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private window: tips just reappear */ } },
  };
  BA.coachTips = null;
  BA.coachIndex = {};
  async function loadTips() {
    if (!BA.coachTips) {
      BA.coachTips = BA.api("/api/coaching/tips").then((r) => (r && r.tips ? r : { tips: r || {}, guide_base: "#/coaching/" })).catch(() => ({ tips: {}, guide_base: "#/coaching/" }));
    }
    return BA.coachTips;
  }
  BA.coachingOn = () => !store.get(COACH_OFF, false);
  BA.setCoaching = (on) => { store.set(COACH_OFF, !on); if (on) store.set(COACH_HIDDEN, []); };
  async function showCoachTip(main, key) {
    if (BA.session.presentation || main.hasAttribute("data-layout") || !BA.coachingOn() || store.get(COACH_HIDDEN, []).includes(key)) return;
    const { tips, guide_base } = await loadTips();
    const list = tips[key] || [];
    if (!list.length || location.hash.slice(1).replace(/\/$/, "") !== key && location.hash) return;
    const i = (BA.coachIndex[key] || 0) % list.length;
    const tip = list[i];
    const external = !guide_base.startsWith("#");
    const el = document.createElement("aside");
    el.className = "coach-tip";
    el.innerHTML = `${BA.icon("lightbulb")}<div class="coach-text"><span>${BA.esc(tip.text)}</span>
      ${tip.guide ? ` <a href="${BA.esc(guide_base + tip.guide)}"${external ? ' target="_blank" rel="noopener"' : ""}>${BA.esc(tip.title || "Read the guide")}</a>` : ""}</div>
      <div class="coach-actions">${list.length > 1 ? `<button class="icon-btn" title="Next tip" data-next>${i + 1}/${list.length}</button>` : ""}
      <button class="icon-btn" title="Hide tips on this page" data-hide>${BA.icon("x")}</button></div>`;
    main.prepend(el);
    const next = el.querySelector("[data-next]");
    if (next) next.onclick = () => { BA.coachIndex[key] = i + 1; el.remove(); showCoachTip(main, key); };
    el.querySelector("[data-hide]").onclick = () => {
      store.set(COACH_HIDDEN, [...store.get(COACH_HIDDEN, []), key]);
      el.remove();
      BA.toast("Tips hidden on this page. Turn them back on in Settings.");
    };
  }

  // Section intros: what this section is for and how to use it. Open on the first visit, then folded to one line.
  const INTRO_SEEN = "ba-intro-seen";
  BA.help = null;
  const loadHelp = () => (BA.help ||= BA.api("/api/help").catch(() => ({})));
  const navLabel = (path) => (BA.session.nav.find((n) => n.path === path) || {}).label;
  const relatedLinks = (list) => (list || []).map((r) => `<a href="#${BA.esc(r)}">${BA.esc(navLabel(r) || (r.startsWith("/coaching/") ? "Guide: " + r.split("/")[2].replace(/-/g, " ") : r))}</a>`).join(", ");
  function introBody(h) {
    return `<p>${BA.esc(h.purpose)}</p>${h.steps && h.steps.length ? `<ol class="intro-steps">${h.steps.map((s) => `<li>${BA.esc(s)}</li>`).join("")}</ol>` : ""}
      ${h.privacy ? `<p class="quiet">${BA.icon("eye-off")} ${BA.esc(h.privacy)}</p>` : ""}${h.related && h.related.length ? `<p class="quiet">See also: ${relatedLinks(h.related)}</p>` : ""}`;
  }
  async function showIntro(main, key) {
    if (BA.session.presentation || main.hasAttribute("data-layout") || key === "/help") return;
    const h = (await loadHelp())[key];
    if (!h) return;
    const seen = store.get(INTRO_SEEN, []);
    const el = document.createElement("details");
    el.className = "section-intro";
    if (!seen.includes(key)) el.open = true;
    el.innerHTML = `<summary>${BA.icon("info")}<span>About this section</span></summary><div class="intro-body">${introBody(h)}
      <div class="row"><span class="spacer"></span><button class="btn" type="button" data-gotit>Got it</button></div></div>`;
    main.prepend(el);
    const mark = () => { const s = store.get(INTRO_SEEN, []); if (!s.includes(key)) store.set(INTRO_SEEN, [...s, key]); };
    el.querySelector("[data-gotit]").onclick = () => { mark(); el.open = false; };
    el.addEventListener("toggle", () => { if (!el.open) mark(); });
  }

  BA.view("/help", {
    title: "Help",
    async render(main) {
      const help = await loadHelp();
      const groups = [];
      let current = { name: "", items: [] };
      for (const n of BA.session.nav) {
        if (n.group) { if (current.items.length) groups.push(current); current = { name: n.group, items: [] }; }
        else if (n.path && help[n.path]) current.items.push(n);
      }
      if (current.items.length) groups.push(current);
      main.innerHTML = `<section class="card"><h2>How to use ${BA.esc(BA.session.title)}</h2>
          <p>Every section, what it's for and how to use it. The same explanation sits at the top of each section under <b>About this section</b>.</p>
          <p class="quiet">Press <kbd>⌘K</kbd> or <kbd>/</kbd> to jump anywhere, <kbd>?</kbd> for keyboard shortcuts, and <kbd>Shift</kbd>+<kbd>P</kbd> for presentation mode before sharing your screen.</p>
          <div class="row"><button class="btn" id="intros-reset">Show every section's intro again</button></div></section>
        ${groups.map((g) => `<section class="card"><h2>${BA.esc(g.name || "Start here")}</h2>${g.items.map((n) => `<div class="help-item" id="help-${BA.esc(n.path.slice(1))}">
            <h3><a href="#${BA.esc(n.path)}">${BA.icon(n.icon)} ${BA.esc(n.label)}</a></h3>${introBody(help[n.path])}</div>`).join("")}</section>`).join("")}`;
      main.querySelector("#intros-reset").onclick = () => { store.set(INTRO_SEEN, []); BA.toast("Each section's intro will open again on your next visit."); };
    },
  });

  // Jira keys: shown as links when the toolkit knows the Jira address, with a small inline editor.
  BA.jiraUrl = null;
  BA.issueKeys = (keys) =>
    (Array.isArray(keys) ? keys : keys ? [keys] : [])
      .map((k) => (BA.jiraUrl ? `<a class="pill issue" href="${BA.esc(BA.jiraUrl)}/browse/${encodeURIComponent(k)}" target="_blank" rel="noopener" title="Open in Jira">${BA.esc(k)}</a>` : `<span class="pill issue">${BA.esc(k)}</span>`))
      .join(" ");
  BA.keysEditor = (path, keys, field = "jira_keys") => {
    const list = Array.isArray(keys) ? keys : keys ? [keys] : [];
    const edit = BA.session.presentation ? "" : ` <button type="button" class="link-btn" data-keys-edit="${BA.esc(path)}" data-keys-field="${field}" data-keys="${BA.esc(list.join(", "))}" title="${field === "ticket_key" ? "Jira key" : "Jira keys"}">${list.length ? "edit" : "+ Jira"}</button>`;
    return `<span class="issue-keys">${BA.issueKeys(list)}${edit}</span>`;
  };
  // Capture phase, so the click doesn't also open a clickable row underneath.
  document.addEventListener("click", async (e) => {
    const b = e.target.closest && e.target.closest("[data-keys-edit]");
    if (!b) return;
    e.preventDefault();
    e.stopPropagation();
    const single = b.dataset.keysField === "ticket_key";
    const value = prompt(single ? "Jira key, such as ABC-123. Leave empty to clear." : "Jira keys, separated by commas, such as ABC-123, ABC-124. Leave empty to clear.", b.dataset.keys);
    if (value === null) return;
    try {
      await BA.api(b.dataset.keysEdit, { method: "PATCH", body: { [b.dataset.keysField]: value } });
      BA.rerender();
    } catch (err) {
      BA.toast(err.message);
    }
  }, true);

  BA.guard = (fn) => async (...args) => {
    try {
      await fn(...args);
    } catch (err) {
      BA.toast(err.message);
    }
  };

  BA.go = (path) => {
    if (location.hash === "#" + path) route();
    else location.hash = path;
  };

  BA.rerender = () => route();

  function matchView(path) {
    let best = null;
    for (const key of Object.keys(BA.views)) {
      if ((path === key || path.startsWith(key + "/")) && (!best || key.length > best.length)) best = key;
    }
    return best;
  }

  function renderNav(current) {
    const nav = document.getElementById("nav");
    nav.innerHTML = BA.session.nav
      .map((item) =>
        item.group
          ? `<div class="group">${BA.esc(item.group)}</div>`
          : `<a href="#${BA.esc(item.path)}" class="${current === item.path ? "on" : ""}">${BA.icon(item.icon || "chevron-right")}${BA.esc(item.label)}</a>`
      )
      .join("");
  }

  function renderPresentation() {
    const on = BA.session.presentation;
    document.body.classList.toggle("presenting", on);
    document.getElementById("present-badge").hidden = !on;
    const btn = document.getElementById("present-toggle");
    btn.innerHTML = `${BA.icon(on ? "eye" : "eye-off")}${on ? "Stop presentation mode" : "Presentation mode"}`;
    btn.classList.toggle("primary", on);
  }

  async function route() {
    const path = location.hash.slice(1) || BA.session.nav.find((i) => i.path)?.path || "/settings";
    const key = matchView(path);
    const def = key ? BA.views[key] : null;
    renderNav(key);
    const main = document.getElementById("view");
    if (BA.cleanup) {
      try {
        BA.cleanup();
      } catch (err) {
        console.error(err);
      }
      BA.cleanup = null;
    }
    main.removeAttribute("data-layout");
    document.getElementById("view-title").textContent = def ? def.title : "Not found";
    document.title = `${def ? def.title + " · " : ""}${BA.session.title}`;
    closeOverlay();
    main.innerHTML = '<div class="skeleton"><div></div><div></div><div></div><div></div></div>';
    main.classList.remove("entering");
    document.body.classList.remove("nav-open");
    if (!def) {
      main.innerHTML = '<p class="empty">There is no screen here.</p>';
      return;
    }
    try {
      const param = path.slice(key.length).replace(/^\//, "");
      const rendering = def.render(main, param);
      await rendering;
      if (!param) {
        await showCoachTip(main, key);
        await showIntro(main, key);
      }
      void main.offsetWidth;
      main.classList.add("entering");
    } catch (err) {
      main.innerHTML = `<p class="error">${BA.esc(err.message)}</p>`;
    }
  }

  async function togglePresentation() {
    try {
      BA.session = await BA.api("/api/session/presentation", { method: "POST", body: { on: !BA.session.presentation } });
    } catch (err) {
      BA.toast(`Couldn't change presentation mode: ${err.message}`);
      return;
    }
    renderPresentation();
    route();
  }

  // ---- Settings: sign-in, tokens, history (core screen every app gets) ----

  BA.view("/settings", {
    title: "Settings",
    async render(main) {
      if (BA.session.presentation) {
        main.innerHTML = '<p class="empty">Settings are hidden while presenting.</p>';
        return;
      }
      const [tokens, scopes, changes, exports] = await Promise.all([
        BA.api("/api/tokens"),
        BA.api("/api/scopes"),
        BA.api("/api/changes?limit=20"),
        BA.api("/api/exports"),
      ]);
      main.innerHTML = `
        <section class="card">
          <h2>Presentation mode</h2>
          <p class="quiet">Turn on <b>Presentation mode</b> before sharing your screen. The server then hides every private field, whatever screen you open.</p>
          <p>Odysseus link: <span class="pill">${BA.esc(BA.session.odysseus)}</span></p>
        </section>
        <section class="card">
          <h2>Sign-in</h2>
          <div id="totp"></div>
          <h3>Change password</h3>
          <form id="pw-form" class="grid2">
            <label>Current password<input type="password" name="current" required></label>
            <label>New password<input type="password" name="new" minlength="12" required></label>
            <div><button class="btn" type="submit">Change password</button></div>
          </form>
        </section>
        <section class="card">
          <h2>API tokens</h2>
          <p class="quiet">For LLM clients and the other apps. A token only reads what its scope allows.</p>
          <div id="new-token"></div>
          <div class="tablewrap"><table class="data"><thead><tr><th>Name</th><th>Scopes</th><th>Created</th><th>Last used</th><th></th></tr></thead>
          <tbody>${
            tokens
              .map(
                (t) => `<tr><td>${BA.esc(t.name)}</td><td>${t.scopes.map((s) => `<span class="pill">${BA.esc(s)}</span>`).join(" ")}</td>
              <td>${BA.esc(t.created_at)}</td><td>${BA.esc(t.last_used_at || "never")}</td>
              <td>${t.revoked_at ? '<span class="pill bad">revoked</span>' : `<button class="btn danger" data-revoke="${t.id}">Revoke</button>`}</td></tr>`
              )
              .join("") || '<tr><td colspan="5" class="empty">No tokens yet.</td></tr>'
          }</tbody></table></div>
          <form id="token-form">
            <label>Name<input name="name" placeholder="[Placeholder token name]" required></label>
            <div class="row">${scopes
              .map((s) => `<label class="check"><input type="checkbox" name="scope" value="${BA.esc(s.scope)}"> ${BA.esc(s.scope)} <span class="quiet">(reads ${BA.esc(s.reads)})</span></label>`)
              .join("")}</div>
            <button class="btn primary" type="submit">Create token</button>
          </form>
        </section>
        <section class="card"><h2>Coaching tips</h2><p class="quiet">A short tip at the top of each screen, linking to a coaching guide. Tips never show while presenting.</p>
          <label class="check"><input type="checkbox" id="coach-on"${BA.coachingOn() ? " checked" : ""}> Show coaching tips</label> <span class="quiet">(turning them on also brings back tips you hid on single pages)</span></section>
        <section class="card" id="backups"><h2>Backups</h2><p class="quiet">Loading…</p></section>
        <section class="card">
          <h2>Recent changes</h2>
          <div class="tablewrap"><table class="data"><thead><tr><th>When</th><th>Record</th><th>Field</th><th>By</th></tr></thead><tbody>${
            changes.map((c) => `<tr><td>${BA.esc(c.at)}</td><td>${BA.esc(c.entity)} ${BA.esc(c.record_id)}</td><td>${BA.esc(c.field)}</td><td>${BA.esc(c.source)}</td></tr>`).join("") ||
            '<tr><td colspan="4" class="empty">No changes yet.</td></tr>'
          }</tbody></table></div>
        </section>
        <section class="card">
          <h2>Exports</h2>
          <div class="tablewrap"><table class="data"><thead><tr><th>When</th><th>What</th><th>Records</th><th>By</th></tr></thead><tbody>${
            exports.map((e) => `<tr><td>${BA.esc(e.at)}</td><td>${BA.esc(e.title)}</td><td>${e.record_count}</td><td>${BA.esc(e.source)}</td></tr>`).join("") ||
            '<tr><td colspan="4" class="empty">Nothing exported yet.</td></tr>'
          }</tbody></table></div>
        </section>`;

      renderTotp(main.querySelector("#totp"));
      renderBackups(main.querySelector("#backups"));
      main.querySelector("#coach-on").onchange = (e) => { BA.setCoaching(e.target.checked); BA.toast(e.target.checked ? "Coaching tips on." : "Coaching tips off."); };

      main.querySelector("#pw-form").onsubmit = async (e) => {
        e.preventDefault();
        const f = new FormData(e.target);
        try {
          await BA.api("/api/auth/password", { method: "POST", body: { current: f.get("current"), new: f.get("new") } });
          e.target.reset();
          BA.toast("Password changed. Other sessions were signed out.");
        } catch (err) {
          BA.toast(err.message);
        }
      };

      main.querySelector("#token-form").onsubmit = async (e) => {
        e.preventDefault();
        const f = new FormData(e.target);
        try {
          const res = await BA.api("/api/tokens", { method: "POST", body: { name: f.get("name"), scopes: f.getAll("scope") } });
          await route();
          document.getElementById("new-token").innerHTML = `<p>${BA.esc(res.note)}</p><p class="secret">${BA.esc(res.token)}</p>`;
        } catch (err) {
          BA.toast(err.message);
        }
      };

      main.querySelectorAll("[data-revoke]").forEach((btn) => {
        btn.onclick = async () => {
          await BA.api(`/api/tokens/${btn.dataset.revoke}`, { method: "DELETE" });
          route();
        };
      });
    },
  });

  function renderTotp(el) {
    if (BA.session.totp_enabled) {
      el.innerHTML = `<p><span class="pill good">Authenticator on</span></p>
        <form id="totp-off" class="row"><input type="password" name="password" placeholder="Password to switch it off" required style="max-width:280px">
        <button class="btn danger" type="submit">Switch off</button></form>`;
      el.querySelector("#totp-off").onsubmit = async (e) => {
        e.preventDefault();
        try {
          await BA.api("/api/auth/totp/disable", { method: "POST", body: { password: new FormData(e.target).get("password") } });
          BA.session.totp_enabled = false;
          renderTotp(el);
        } catch (err) {
          BA.toast(err.message);
        }
      };
      return;
    }
    el.innerHTML = `<p class="quiet">Add an authenticator app for a second sign-in step.</p><button class="btn" id="totp-start" type="button">Set up authenticator</button>`;
    el.querySelector("#totp-start").onclick = async () => {
      const res = await BA.api("/api/auth/totp/start", { method: "POST" });
      el.innerHTML = `<p>Add this key to your authenticator app, then enter the code it shows.</p>
        <p class="secret">${BA.esc(res.secret)}</p><p class="quiet secret">${BA.esc(res.uri)}</p>
        <form id="totp-confirm" class="row"><input name="code" inputmode="numeric" placeholder="6-digit code" required style="max-width:160px">
        <button class="btn primary" type="submit">Confirm</button></form>`;
      el.querySelector("#totp-confirm").onsubmit = async (e) => {
        e.preventDefault();
        try {
          await BA.api("/api/auth/totp/confirm", { method: "POST", body: { code: new FormData(e.target).get("code") } });
          BA.session.totp_enabled = true;
          renderTotp(el);
          BA.toast("Authenticator is on.");
        } catch (err) {
          BA.toast(err.message);
        }
      };
    };
  }

  // ---- command palette, keyboard shortcuts, theme ----

  BA.commands = [];
  BA.command = (cmd) => BA.commands.push(cmd);

  const THEMES = ["system", "light", "dark"];
  const themeIcon = { system: "monitor", light: "sun", dark: "moon" };
  function currentTheme() {
    try {
      return localStorage.getItem("ba-theme") || "system";
    } catch (e) {
      return "system";
    }
  }
  function applyTheme(theme) {
    if (theme === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("ba-theme", theme);
    } catch (e) {}
    const btn = document.getElementById("theme-toggle");
    btn.innerHTML = BA.icon(themeIcon[theme]);
    btn.title = `Theme: ${theme} (click to change)`;
  }
  const cycleTheme = () => applyTheme(THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length]);

  const typing = (e) => {
    const el = e.target;
    return el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));
  };

  function closeOverlay() {
    document.querySelectorAll(".overlay").forEach((o) => o.remove());
  }

  function openPalette() {
    closeOverlay();
    const navItems = BA.session.nav
      .filter((i) => i.path)
      .map((i) => ({ label: i.label, hint: "Go to", icon: i.icon || "chevron-right", run: () => BA.go(i.path) }));
    const items = [
      ...navItems,
      ...BA.commands,
      { label: BA.session.presentation ? "Stop presentation mode" : "Turn on presentation mode", hint: "Shift+P", icon: "eye-off", run: togglePresentation },
      { label: "Change theme", hint: "light, dark or system", icon: "moon", run: cycleTheme },
      { label: "Keyboard shortcuts", hint: "?", icon: "keyboard", run: openShortcuts },
      { label: "Sign out", icon: "log-out", run: () => document.querySelector(".signout").submit() },
    ];
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.innerHTML = `<div class="palette" role="dialog" aria-label="Command palette">
      <div class="palette-search">${BA.icon("search", "quiet")}<input id="palette-input" placeholder="Jump to a screen or run an action…" autocomplete="off"></div>
      <ul id="palette-list" role="listbox"></ul>
      <div class="palette-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></div></div>`;
    document.body.appendChild(overlay);
    const input = overlay.querySelector("input");
    const list = overlay.querySelector("ul");
    let shown = items;
    let active = 0;
    const score = (label, q) => {
      const l = label.toLowerCase();
      if (!q) return 1;
      if (l.startsWith(q)) return 3;
      if (l.includes(q)) return 2;
      const initials = l.split(/\s+/).map((w) => w[0]).join("");
      return initials.startsWith(q) ? 1.5 : 0;
    };
    const draw = () => {
      const q = input.value.trim().toLowerCase();
      shown = items.map((i) => [i, score(i.label, q)]).filter(([, s]) => s > 0).sort((a, b) => b[1] - a[1]).map(([i]) => i);
      active = Math.min(active, Math.max(0, shown.length - 1));
      list.innerHTML =
        shown.map((i, n) => `<li role="option" data-n="${n}" class="${n === active ? "active" : ""}">${BA.icon(i.icon || "chevron-right")}${BA.esc(i.label)}${i.hint ? `<span class="hint">${BA.esc(i.hint)}</span>` : ""}</li>`).join("") ||
        '<li class="quiet">No matches</li>';
      list.querySelector(".active")?.scrollIntoView({ block: "nearest" });
    };
    const run = (i) => {
      closeOverlay();
      if (i) i.run();
    };
    input.oninput = () => {
      active = 0;
      draw();
    };
    input.onkeydown = (e) => {
      if (e.key === "ArrowDown") (active = Math.min(active + 1, shown.length - 1)), draw(), e.preventDefault();
      else if (e.key === "ArrowUp") (active = Math.max(active - 1, 0)), draw(), e.preventDefault();
      else if (e.key === "Enter") run(shown[active]);
      else if (e.key === "Escape") closeOverlay();
    };
    list.onclick = (e) => {
      const li = e.target.closest("li[data-n]");
      if (li) run(shown[Number(li.dataset.n)]);
    };
    overlay.onclick = (e) => e.target === overlay && closeOverlay();
    draw();
    input.focus();
  }

  function openShortcuts() {
    closeOverlay();
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.innerHTML = `<div class="dialog" role="dialog" aria-label="Keyboard shortcuts"><h2>Keyboard shortcuts</h2><dl>
      <dt><kbd>⌘</kbd> <kbd>K</kbd> or <kbd>/</kbd></dt><dd>Jump to a screen or run an action</dd>
      <dt><kbd>Shift</kbd> <kbd>P</kbd></dt><dd>Presentation mode on or off</dd>
      <dt><kbd>Shift</kbd> <kbd>T</kbd></dt><dd>Change theme</dd>
      <dt><kbd>?</kbd></dt><dd>This list</dd>
      <dt><kbd>Esc</kbd></dt><dd>Close a dialog</dd></dl>
      <div class="actions"><button class="btn" type="button">Close</button></div></div>`;
    document.body.appendChild(overlay);
    overlay.onclick = (e) => (e.target === overlay || e.target.closest("button")) && closeOverlay();
  }

  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      document.querySelector(".palette") ? closeOverlay() : openPalette();
      return;
    }
    if (e.key === "Escape") return closeOverlay();
    if (typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === "/") (e.preventDefault(), openPalette());
    else if (e.key === "?") openShortcuts();
    else if (e.key === "P" && e.shiftKey) togglePresentation();
    else if (e.key === "T" && e.shiftKey) cycleTheme();
  });

  async function boot() {
    BA.session = await BA.api("/api/session");
    renderPresentation();
    document.getElementById("present-toggle").onclick = togglePresentation;
    document.getElementById("open-palette").onclick = openPalette;
    document.getElementById("shortcuts-btn").onclick = openShortcuts;
    document.getElementById("theme-toggle").onclick = cycleTheme;
    document.getElementById("nav-toggle").onclick = () => document.body.classList.toggle("nav-open");
    applyTheme(currentTheme());
    window.addEventListener("hashchange", route);
    route();
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
