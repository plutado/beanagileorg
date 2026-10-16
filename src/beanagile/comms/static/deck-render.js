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
      fields: [HEADLINE, { name: "items", label: "Points", type: "lines", hint: "one per line" }, { name: "step", label: "Reveal one at a time", type: "checkbox" }],
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
  const list = (items, step) => `<ul>${(items || []).map((i) => `<li${step ? ' class="fragment"' : ""}>${esc(i)}</li>`).join("")}</ul>`;
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
        return `${headline(c)}${list(c.items, c.step)}`;
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

  function render(slides, mediaList, opts = {}) {
    const media = Object.fromEntries((mediaList || []).map((m) => [m.id, m]));
    return slides
      .filter((s) => opts.includeHidden || !s.hidden)
      .map(
        (s) => `<section data-slide-id="${s.id}" class="ba-slide ba-layout-${esc(s.layout)}"${s.transition ? ` data-transition="${esc(s.transition)}"` : ""}>
          ${body(s, media)}${s.notes ? `<aside class="notes">${esc(s.notes)}</aside>` : ""}</section>`
      )
      .join("");
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

  window.BADeck = { LAYOUTS, render, attach, esc };
})();
