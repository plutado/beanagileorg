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
          : `<a href="#${BA.esc(item.path)}" class="${current === item.path ? "on" : ""}">${BA.esc(item.label)}</a>`
      )
      .join("");
  }

  function renderPresentation() {
    const on = BA.session.presentation;
    document.body.classList.toggle("presenting", on);
    document.getElementById("present-badge").hidden = !on;
    const btn = document.getElementById("present-toggle");
    btn.textContent = on ? "Stop presenting" : "Present";
    btn.classList.toggle("primary", on);
  }

  async function route() {
    const path = location.hash.slice(1) || BA.session.nav.find((i) => i.path)?.path || "/settings";
    const key = matchView(path);
    const def = key ? BA.views[key] : null;
    renderNav(key);
    const main = document.getElementById("view");
    document.getElementById("view-title").textContent = def ? def.title : "Not found";
    document.title = `${def ? def.title + " · " : ""}${BA.session.title}`;
    main.innerHTML = "";
    if (!def) {
      main.innerHTML = '<p class="empty">There is no screen here.</p>';
      return;
    }
    try {
      await def.render(main, path.slice(key.length).replace(/^\//, ""));
    } catch (err) {
      main.innerHTML = `<p class="error">${BA.esc(err.message)}</p>`;
    }
  }

  async function togglePresentation() {
    BA.session = await BA.api("/api/session/presentation", { method: "POST", body: { on: !BA.session.presentation } });
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
          <p class="quiet">Use <b>Present</b> before sharing your screen. The server then hides every private field, whatever screen you open.</p>
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

  async function boot() {
    BA.session = await BA.api("/api/session");
    renderPresentation();
    document.getElementById("present-toggle").onclick = togglePresentation;
    window.addEventListener("hashchange", route);
    route();
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
