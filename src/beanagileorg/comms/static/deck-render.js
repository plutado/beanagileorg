// One renderer for every deck: the editor canvas and the present page both use it, so what you build is what you show.
// Slides are structured data (a layout plus its fields); this turns them into reveal.js sections and runs media and Lottie.
(function () {
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  const HEADLINE = { name: "heading", label: "Headline", hint: "state the point as a sentence" };
  const PLAY_MEDIA = {
    name: "play",
    label: "Plays",
    type: "select",
    options: [
      ["click", "On the next click"],
      ["enter", "When the slide opens"],
      ["manual", "Only when I press play"],
    ],
  };
  const FRAGMENT_STYLE = {
    name: "fragment_style",
    label: "Reveal style",
    type: "select",
    options: [
      ["", "Fade in"], ["fade-up", "Fade up"], ["fade-left", "Fade from the right"], ["grow", "Grow"], ["shrink", "Shrink"],
      ["fade-in-then-semi-out", "Fade in, then dim"], ["highlight-current-blue", "Highlight the current one"], ["highlight-red", "Turn red"], ["fade-out", "Fade out"],
    ],
  };
  const CODE_LANGUAGES = [["javascript", "JavaScript"], ["typescript", "TypeScript"], ["python", "Python"], ["java", "Java"], ["sql", "SQL"],
    ["html", "HTML"], ["css", "CSS"], ["json", "JSON"], ["yaml", "YAML"], ["bash", "Shell"], ["plaintext", "Plain text"]];
  // Options every slide has, whatever its layout: how it sits in the deck and what's behind it.
  const SLIDE_OPTIONS = [
    { name: "vertical", label: "Stack under the previous slide (a vertical slide: down arrow, not next)", type: "checkbox" },
    { name: "auto_animate", label: "Auto-animate from the previous slide (matching headings, code and shapes move into place)", type: "checkbox" },
    { name: "bg_color", label: "Background colour", hint: "such as #0f172a" },
    { name: "bg_gradient", label: "Background gradient", type: "select", options: [["", "None"], ["dusk", "Dusk"], ["ocean", "Ocean"], ["sunrise", "Sunrise"], ["forest", "Forest"], ["night", "Night"]] },
    { name: "bg_image", label: "Background image", type: "media", kind: "image" },
    { name: "bg_size", label: "Background image size", type: "select", options: [["cover", "Fill the slide"], ["contain", "Fit inside"], ["tile", "Tile"]] },
    { name: "bg_transition", label: "Background transition", type: "select", options: [["", "Deck default"], ["fade", "Fade"], ["slide", "Slide"], ["zoom", "Zoom"], ["convex", "Convex"], ["none", "None"]] },
    { name: "dark", label: "Light text (for dark backgrounds)", type: "checkbox" },
  ];
  const GRADIENTS = {
    dusk: "linear-gradient(135deg, #312e81 0%, #7c3aed 55%, #db2777 100%)",
    ocean: "linear-gradient(135deg, #0c4a6e 0%, #0891b2 60%, #67e8f9 100%)",
    sunrise: "linear-gradient(135deg, #f97316 0%, #fb7185 50%, #fde68a 100%)",
    forest: "linear-gradient(160deg, #052e16 0%, #15803d 60%, #a3e635 100%)",
    night: "radial-gradient(circle at 30% 20%, #1e293b 0%, #020617 70%)",
  };
  const TRIM = [
    { name: "start", label: "Start at (seconds)", type: "number", step: 0.1 },
    { name: "end", label: "Stop at (seconds)", type: "number", step: 0.1 },
    { name: "loop", label: "Loop", type: "checkbox" },
  ];

  const LAYOUTS = {
    title: { label: "Title", fields: [{ name: "heading", label: "Title" }, { name: "subheading", label: "Subtitle" }] },
    section: { label: "Section break", fields: [{ name: "heading", label: "Section title" }] },
    "big-number": {
      label: "One big number",
      fields: [HEADLINE, { name: "number", label: "Number" }, { name: "caption", label: "Caption" }],
    },
    bullets: {
      label: "Points",
      fields: [
        HEADLINE,
        { name: "items", label: "Points", type: "lines", hint: "one per line" },
        { name: "ordered", label: "Numbered", type: "checkbox" },
        { name: "step", label: "Reveal one at a time", type: "checkbox" },
        FRAGMENT_STYLE,
      ],
    },
    code: {
      label: "Code",
      fields: [
        HEADLINE,
        { name: "language", label: "Language", type: "select", options: CODE_LANGUAGES },
        { name: "code", label: "Code", type: "textarea" },
        { name: "steps", label: "Highlight steps", hint: "line ranges, one step per |, such as 1-3|5|7-9" },
        { name: "animate_id", label: "Animate with the next slide's code as", hint: "the same name on both slides, with auto-animate on" },
      ],
    },
    table: {
      label: "Table",
      fields: [HEADLINE, { name: "rows", label: "Rows", type: "lines", hint: "one row per line, cells split by |; the first row is the header" }, { name: "step", label: "Reveal rows one at a time", type: "checkbox" }],
    },
    "fit-text": { label: "Fit text", fields: [{ name: "heading", label: "Words", hint: "a few words, sized to fill the slide" }, { name: "subheading", label: "Small line under it" }] },
    shapes: {
      label: "Shapes",
      fields: [
        HEADLINE,
        { name: "shapes", label: "Shapes", type: "lines", hint: "one per line: name | colour | size, such as a | #4f46e5 | 120" },
        { name: "arrange", label: "Arrange", type: "select", options: [["row", "In a row"], ["column", "In a column"], ["stack", "Stacked on top of each other"]] },
      ],
    },
    quote: { label: "Quote", fields: [{ name: "quote", label: "Quote", type: "textarea" }, { name: "attribution", label: "Attribution" }] },
    comparison: {
      label: "Comparison",
      fields: [
        HEADLINE,
        { name: "left_title", label: "Left title" },
        { name: "left_items", label: "Left points", type: "lines", hint: "one per line" },
        { name: "right_title", label: "Right title" },
        { name: "right_items", label: "Right points", type: "lines", hint: "one per line" },
      ],
    },
    image: { label: "Image", fields: [HEADLINE, { name: "media_id", label: "Image", type: "media", kind: "image" }, { name: "caption", label: "Caption" }] },
    video: {
      label: "Video",
      fields: [
        HEADLINE,
        { name: "media_id", label: "Video", type: "media", kind: "video" },
        { name: "poster_id", label: "Poster frame", type: "media", kind: "image" },
        { name: "captions_id", label: "Captions (WebVTT)", type: "media", kind: "captions" },
        PLAY_MEDIA,
        ...TRIM,
        { name: "muted", label: "Start muted", type: "checkbox" },
      ],
    },
    audio: {
      label: "Audio",
      fields: [HEADLINE, { name: "media_id", label: "Audio", type: "media", kind: "audio" }, { name: "caption", label: "Caption" }, PLAY_MEDIA, ...TRIM],
    },
    lottie: {
      label: "Animation",
      fields: [
        HEADLINE,
        { name: "media_id", label: "Lottie animation", type: "media", kind: "lottie" },
        { name: "caption", label: "Caption" },
        {
          name: "play",
          label: "Plays",
          type: "select",
          options: [
            ["loop", "Loops while the slide is open"],
            ["enter", "Once when the slide opens"],
            ["click", "On the next click"],
          ],
        },
        { name: "speed", label: "Speed", type: "number", step: 0.25 },
        { name: "segment_start", label: "From frame", type: "number" },
        { name: "segment_end", label: "To frame", type: "number" },
      ],
    },
    closing: { label: "Closing", fields: [{ name: "heading", label: "Closing line" }, { name: "subheading", label: "Next step" }] },
  };

  const url = (id) => `/api/media/${id}/file`;
  const num = (v) => (v === null || v === undefined || v === "" ? "" : String(Number(v)));
  const missing = (text) => `<div class="ba-missing">${esc(text)}</div>`;
  const headline = (c) => (c.heading ? `<h2 class="ba-headline">${esc(c.heading)}</h2>` : "");
  const caption = (c) => (c.caption ? `<p class="ba-caption">${esc(c.caption)}</p>` : "");
  const list = (items, step, ordered, style) => {
    const tag = ordered ? "ol" : "ul";
    const cls = step ? ` class="fragment${style ? " " + esc(style) : ""}"` : "";
    return `<${tag}>${(items || []).map((i) => `<li${cls}>${esc(i)}</li>`).join("")}</${tag}>`;
  };
  // "1-3|5" becomes [[1,2,3],[5]]: one highlight step per group of line ranges. An empty group ("|3-4") means
  // every line, so the code can open in full before the first highlight.
  const parseSteps = (text) =>
    String(text || "").trim() ? String(text).split("|").map((part) => part.split(",").flatMap((r) => {
      const [a, b] = r.trim().split("-").map(Number);
      if (!a) return [];
      return Array.from({ length: (b || a) - a + 1 }, (_, i) => a + i);
    })) : [];
  const highlight = (code, lang) => {
    if (window.hljs && lang && lang !== "plaintext" && window.hljs.getLanguage(lang)) {
      try { return window.hljs.highlight(code, { language: lang, ignoreIllegals: true }).value; } catch { /* fall through to plain */ }
    }
    return esc(code);
  };
  // Split highlighted HTML into lines without breaking spans that cross a line end.
  function codeLines(html) {
    const out = [];
    let open = [];
    for (const raw of html.split("\n")) {
      const line = open.join("") + raw;
      const tags = raw.match(/<span[^>]*>|<\/span>/g) || [];
      for (const t of tags) t === "</span>" ? open.pop() : open.push(t);
      out.push(line + "</span>".repeat(open.length));
    }
    return out;
  }
  // An invisible reveal.js step: clicking forward plays the target instead of revealing text.
  const trigger = (id) => `<span class="fragment ba-trigger" data-target="${id}"></span>`;

  function mediaTag(tag, slide, c, file, media) {
    const id = `ba-media-${slide.id}`;
    const poster = tag === "video" && media[c.poster_id] ? ` poster="${url(c.poster_id)}"` : "";
    const track = tag === "video" && media[c.captions_id] ? `<track kind="captions" src="${url(c.captions_id)}" default>` : "";
    return `<${tag} id="${id}" class="ba-media ba-${tag}" controls playsinline preload="metadata" src="${url(file.id)}"
      data-play="${esc(c.play || "click")}" data-start="${num(c.start)}" data-end="${num(c.end)}"${c.loop ? ' data-loop="1"' : ""}${c.muted ? " muted" : ""}${poster}>${track}</${tag}>${c.play === "click" || !c.play ? trigger(id) : ""}`;
  }

  function body(slide, media) {
    const c = slide.content || {};
    switch (slide.layout) {
      case "title":
        return `<div class="ba-center"><h1>${esc(c.heading)}</h1>${c.subheading ? `<p class="ba-sub">${esc(c.subheading)}</p>` : ""}</div>`;
      case "section":
        return `<div class="ba-center ba-section-wrap"><div class="ba-rule"></div><h1>${esc(c.heading)}</h1></div>`;
      case "big-number":
        return `${headline(c)}<div class="ba-number">${esc(c.number)}</div>${caption(c)}`;
      case "bullets":
        return `${headline(c)}${list(c.items, c.step, c.ordered, c.fragment_style)}`;
      case "code": {
        const lines = codeLines(highlight(String(c.code || "").replace(/^\n+|\s+$/g, ""), c.language));
        const steps = parseSteps(c.steps);
        const id = `ba-code-${slide.id}`;
        return `${headline(c)}<pre class="ba-code"${c.animate_id ? ` data-id="code-${esc(c.animate_id)}"` : ""}><code id="${id}" class="hljs" data-steps='${esc(JSON.stringify(steps))}'>${lines
          .map((l, i) => `<span class="ba-line" data-line="${i + 1}"><span class="ba-ln">${i + 1}</span>${l || " "}</span>`).join("")}</code></pre>${steps.slice(1).map((_, k) => `<span class="fragment ba-trigger ba-code-step" data-code="${id}" data-step="${k + 1}"></span>`).join("")}`;
      }
      case "table": {
        const rows = (c.rows || []).map((r) => r.split("|").map((x) => x.trim()));
        if (!rows.length) return headline(c) + missing("[Placeholder: add rows, cells split by |]");
        const [head, ...rest] = rows;
        return `${headline(c)}<table class="ba-table"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rest
          .map((r) => `<tr${c.step ? ' class="fragment"' : ""}>${r.map((x) => `<td>${esc(x)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
      }
      case "fit-text":
        // Wrapped in a plain block: as a flex item the heading would stretch to full width and fitty would see no room to grow.
        return `<div class="ba-center"><div class="ba-fit"><h1 class="r-fit-text">${esc(c.heading)}</h1></div>${c.subheading ? `<p class="ba-sub">${esc(c.subheading)}</p>` : ""}</div>`;
      case "shapes": {
        const shapes = (c.shapes || []).map((line) => line.split("|").map((x) => x.trim())).filter((x) => x[0]);
        return `${headline(c)}<div class="ba-shapes ba-shapes-${esc(c.arrange || "row")}${c.arrange === "stack" ? " r-stack" : ""}">${shapes
          .map(([name, colour, size], i) => `<div class="ba-shape" data-id="shape-${esc(name)}" style="background:${esc(colour || "#4f46e5")};width:${Number(size) || 120}px;height:${Number(size) || 120}px;${c.arrange === "stack" ? `margin-left:${i * 48}px;margin-top:${i * 36}px;` : ""}"><span>${esc(name)}</span></div>`)
          .join("")}</div>`;
      }
      case "quote":
        return `<div class="ba-center"><blockquote class="ba-quote">${esc(c.quote)}</blockquote>${c.attribution ? `<p class="ba-attrib">${esc(c.attribution)}</p>` : ""}</div>`;
      case "comparison":
        return `${headline(c)}<div class="ba-columns"><div><h3>${esc(c.left_title)}</h3>${list(c.left_items)}</div><div><h3>${esc(c.right_title)}</h3>${list(c.right_items)}</div></div>`;
      case "image": {
        const img = media[c.media_id];
        return `${headline(c)}${img ? `<img class="ba-image" src="${url(img.id)}" alt="${esc(c.caption || img.name)}">` : missing("[Placeholder: choose an image]")}${caption(c)}`;
      }
      case "video": {
        const v = media[c.media_id];
        return `${headline(c)}${v ? mediaTag("video", slide, c, v, media) : missing("[Placeholder: choose a video]")}${caption(c)}`;
      }
      case "audio": {
        const a = media[c.media_id];
        return `${headline(c)}<div class="ba-audio-wrap">${a ? mediaTag("audio", slide, c, a, media) : missing("[Placeholder: choose an audio file]")}</div>${caption(c)}`;
      }
      case "lottie": {
        const a = media[c.media_id];
        if (!a) return headline(c) + missing("[Placeholder: choose an animation]");
        const id = `ba-lottie-${slide.id}`;
        return `${headline(c)}<div id="${id}" class="ba-lottie" data-src="${url(a.id)}" data-play="${esc(c.play || "loop")}"
          data-speed="${num(c.speed) || 1}" data-seg-start="${num(c.segment_start)}" data-seg-end="${num(c.segment_end)}"></div>${caption(c)}${c.play === "click" ? trigger(id) : ""}`;
      }
      case "closing":
        return `<div class="ba-center ba-closing"><h1>${esc(c.heading)}</h1>${c.subheading ? `<p class="ba-sub">${esc(c.subheading)}</p>` : ""}</div>`;
      default:
        return missing(`[Unknown layout: ${slide.layout}]`);
    }
  }

  // The section's attributes from the slide options: transition, auto-animate and the background behind it.
  function attrs(s, media) {
    const c = s.content || {};
    const a = [];
    if (s.transition) a.push(`data-transition="${esc(s.transition)}"`);
    if (c.auto_animate) a.push("data-auto-animate");
    if (c.bg_color) a.push(`data-background-color="${esc(c.bg_color)}"`);
    if (c.bg_gradient && GRADIENTS[c.bg_gradient]) a.push(`data-background-gradient="${esc(GRADIENTS[c.bg_gradient])}"`);
    if (c.bg_image && media[c.bg_image]) {
      a.push(`data-background-image="${url(c.bg_image)}"`);
      if (c.bg_size === "tile") a.push('data-background-size="160px" data-background-repeat="repeat"');
      else if (c.bg_size === "contain") a.push('data-background-size="contain"');
    }
    if (c.bg_transition) a.push(`data-background-transition="${esc(c.bg_transition)}"`);
    return a.join(" ");
  }

  function section(s, media) {
    const dark = s.content?.dark ? " ba-dark" : "";
    return `<section data-slide-id="${s.id}" class="ba-slide ba-layout-${esc(s.layout)}${dark}" ${attrs(s, media)}>
          ${body(s, media)}${s.notes ? `<aside class="notes">${esc(s.notes)}</aside>` : ""}</section>`;
  }

  // Slides marked "stack under the previous slide" become a vertical stack beneath the slide before them.
  function render(slides, mediaList, opts = {}) {
    const media = Object.fromEntries((mediaList || []).map((m) => [m.id, m]));
    const groups = [];
    for (const s of slides.filter((s) => opts.includeHidden || !s.hidden)) {
      if (s.content?.vertical && groups.length) groups[groups.length - 1].push(s);
      else groups.push([s]);
    }
    return groups.map((g) => (g.length === 1 ? section(g[0], media) : `<section class="ba-stack">${g.map((s) => section(s, media)).join("")}</section>`)).join("");
  }

  // ---- runtime: plays media and Lottie on slide changes and click steps ----

  function attach(deck) {
    const anims = new Map();
    // While the editor jumps between slides, media shouldn't start playing on its own.
    let quiet = false;
    const startOf = (m) => (m.dataset.start === "" ? 0 : Number(m.dataset.start));
    const endOf = (m) => (m.dataset.end === "" ? null : Number(m.dataset.end));

    function anim(el) {
      if (!window.lottie) return null;
      if (!anims.has(el)) {
        const a = window.lottie.loadAnimation({ container: el, renderer: "svg", loop: el.dataset.play === "loop", autoplay: false, path: el.dataset.src });
        a.setSpeed(Number(el.dataset.speed) || 1);
        anims.set(el, a);
      }
      return anims.get(el);
    }

    function playAnim(el) {
      const a = anim(el);
      if (!a) return;
      const s = el.dataset.segStart, e = el.dataset.segEnd;
      if (s !== "" && e !== "") a.playSegments([Number(s), Number(e)], true);
      else a.goToAndPlay(0, true);
    }

    function wire(m) {
      if (m.dataset.wired) return;
      m.dataset.wired = "1";
      m.addEventListener("loadedmetadata", () => startOf(m) && (m.currentTime = startOf(m)));
      m.addEventListener("play", () => m.currentTime < startOf(m) && (m.currentTime = startOf(m)));
      m.addEventListener("timeupdate", () => {
        const end = endOf(m);
        if (end !== null && m.currentTime >= end) {
          if (m.dataset.loop) m.currentTime = startOf(m);
          else m.pause();
        }
      });
      m.addEventListener("ended", () => {
        if (m.dataset.loop) {
          m.currentTime = startOf(m);
          m.play().catch(() => {});
        }
      });
    }

    function playMedia(m) {
      wire(m);
      const end = endOf(m);
      if (m.currentTime < startOf(m) || (end !== null && m.currentTime >= end)) m.currentTime = startOf(m);
      m.play().catch(() => {});
    }

    function enter(slide) {
      if (!slide) return;
      slide.querySelectorAll(".ba-media").forEach((m) => {
        wire(m);
        if (m.dataset.play === "enter" && !quiet) playMedia(m);
      });
      slide.querySelectorAll(".ba-lottie").forEach((el) => {
        if (el.dataset.play === "loop" || el.dataset.play === "enter") playAnim(el);
        else anim(el)?.goToAndStop(0, true);
      });
    }

    function leave(slide) {
      if (!slide) return;
      slide.querySelectorAll(".ba-media").forEach((m) => m.pause());
      slide.querySelectorAll(".ba-lottie").forEach((el) => anims.get(el)?.goToAndStop(0, true));
    }

    // Code steps: show the highlighted lines for the step reached, and dim the rest.
    function codeStep(code, step) {
      const steps = JSON.parse(code.dataset.steps || "[]");
      const on = steps[step] && steps[step].length ? new Set(steps[step]) : null;
      code.querySelectorAll(".ba-line").forEach((l) => l.classList.toggle("ba-dim", !!on && !on.has(Number(l.dataset.line))));
    }
    function codeSync(slide) {
      slide?.querySelectorAll("code[data-steps]").forEach((code) => {
        const shown = slide.querySelectorAll(`.ba-code-step.visible[data-code="${code.id}"]`).length;
        codeStep(code, shown);
      });
    }
    deck.on("ready", (e) => codeSync(e.currentSlide));
    deck.on("slidechanged", (e) => codeSync(e.currentSlide));
    deck.on("fragmentshown", (e) => e.fragment?.dataset.code && codeSync(deck.getCurrentSlide()));
    deck.on("fragmenthidden", (e) => e.fragment?.dataset.code && codeSync(deck.getCurrentSlide()));

    const target = (e) => (e.fragment?.dataset.target ? document.getElementById(e.fragment.dataset.target) : null);
    deck.on("ready", (e) => enter(e.currentSlide));
    deck.on("slidechanged", (e) => {
      leave(e.previousSlide);
      enter(e.currentSlide);
    });
    deck.on("fragmentshown", (e) => {
      const el = target(e);
      if (!el) return;
      if (el.classList.contains("ba-lottie")) playAnim(el);
      else if (!quiet) playMedia(el);
    });
    deck.on("fragmenthidden", (e) => {
      const el = target(e);
      if (el) el.classList.contains("ba-lottie") ? anims.get(el)?.goToAndStop(0, true) : el.pause();
    });

    return {
      refresh: () => enter(deck.getCurrentSlide()),
      // Run a programmatic navigation without starting media.
      quietly(fn) {
        quiet = true;
        try {
          fn();
        } finally {
          setTimeout(() => (quiet = false), 100);
        }
      },
      clear() {
        anims.forEach((a) => a.destroy());
        anims.clear();
      },
    };
  }

  // Where a slide sits in the rendered deck, as reveal.js indices, so the editor can jump to slides inside a stack.
  function indicesOf(deck, root, id) {
    const el = root.querySelector(`section[data-slide-id="${id}"]`);
    return el ? deck.getIndices(el) : null;
  }

  window.BADeck = { LAYOUTS, SLIDE_OPTIONS, render, attach, esc, indicesOf };
})();
