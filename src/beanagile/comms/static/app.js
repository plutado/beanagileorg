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

  BA.view("/this-week", {
    title: "This week",
    async render(main) {
      main.innerHTML = `<section class="card"><h2>What I owe people this week</h2>
        <p class="quiet">Messages, templates and the comms calendar arrive with Comms studio version 1. The deck builder is ready under <a href="#/decks">Decks</a>.</p></section>`;
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
