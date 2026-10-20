"""A feature tour deck, built in the deck builder itself.

It follows the order of the official reveal.js demo by Hakim El Hattab (MIT, revealjs.com), rewritten in our own
words and as structured slides, so it shows what the deck builder can do: vertical stacks, a hidden slide, code with
step-by-step highlights, auto-animate, fit text, reveal styles, transitions, backgrounds, lists, tables, quotes,
speaker notes and PDF export.
"""

TITLE = "Presenting with reveal.js: a feature tour"

CODE_1 = """function plan(sprint) {
  const goal = sprint.goal;
  return goal;
}"""

CODE_2 = """function plan(sprint) {
  const goal = sprint.goal;
  const ready = sprint.backlog.filter((s) => s.ready);
  const capacity = sprint.velocity * sprint.availability;

  let points = 0;
  const pulled = ready.filter((s) => (points += s.points) <= capacity);

  return { goal, pulled, points };
}"""

DARK = {"dark": True}

# (layout, content, notes, transition, hidden)
SLIDES = [
    ("title", {"heading": "Presenting with reveal.js", "subheading": "A tour of the deck builder, after the official reveal.js demo by Hakim El Hattab",
               "bg_gradient": "dusk", **DARK},
     "Every slide in this deck is structured data: a layout and its fields, rendered by one renderer in the editor and here.", None, False),
    ("bullets", {"heading": "Hello there", "items": ["reveal.js turns HTML into presentations", "The deck builder keeps each slide as a layout plus its fields",
                                                    "So what you build in the editor is exactly what you present"]},
     None, None, False),
    ("section", {"heading": "Vertical slides"}, "Press the down arrow, or Space to go through everything in order.", None, False),
    ("bullets", {"heading": "One level down", "items": ["Slides can stack under the slide before them", "Use them for detail people can skip",
                                                       "Space walks through every slide; the arrows let you choose"], "vertical": True},
     None, None, False),
    ("bullets", {"heading": "Two levels down", "items": ["Press the right arrow to climb back to the main track"], "vertical": True}, None, None, False),
    ("bullets", {"heading": "A hidden slide", "items": ["Hidden slides stay in the editor but never show when presenting"]},
     "You won't see this one in the presentation.", None, True),
    ("code", {"heading": "Pretty code", "language": "javascript", "code": CODE_1, "animate_id": "plan"},
     "Code is highlighted as you type it in the editor.", None, False),
    ("code", {"heading": "With animations", "language": "javascript", "code": CODE_2, "steps": "|3-4|6-7|9", "animate_id": "plan", "auto_animate": True},
     "Auto-animate grows the code from the last slide, then each click highlights the next lines.", None, False),
    ("bullets", {"heading": "Point of view", "items": ["Press Esc or O for an overview of every slide", "Press F for full screen, and Esc to come back"]},
     None, None, False),
    ("shapes", {"heading": "Auto-animate", "shapes": ["a | #4f46e5 | 110", "b | #0891b2 | 110", "c | #db2777 | 110"], "arrange": "row", "auto_animate": True},
     "Matching shapes on the next slides move, resize and recolor smoothly.", None, False),
    ("shapes", {"heading": "Auto-animate", "shapes": ["a | #7c3aed | 70", "b | #0e7490 | 160", "c | #f97316 | 100"], "arrange": "column", "auto_animate": True},
     None, None, False),
    ("shapes", {"heading": "Auto-animate", "shapes": ["a | #312e81 | 200", "b | #0891b2 | 150", "c | #f43f5e | 100"], "arrange": "stack", "auto_animate": True},
     None, None, False),
    ("bullets", {"heading": "Touch optimized", "items": ["Swipe through the slides on a phone or tablet"]}, None, None, False),
    ("fit-text", {"heading": "FIT TEXT", "subheading": "Words sized to fill the slide"}, None, None, False),
    ("bullets", {"heading": "Reveals", "items": ["Hit the next arrow", "to step through", "one point at a time"], "step": True, "fragment_style": "fade-up"},
     "Speaker notes follow along with each step.", None, False),
    ("bullets", {"heading": "Reveal styles", "items": ["Grow", "Fade in, then dim", "Highlight the current point"], "step": True,
                 "fragment_style": "highlight-current-blue", "vertical": True}, None, None, False),
    ("bullets", {"heading": "Transitions", "items": ["Each slide can set its own transition", "This one zooms in", "The deck default is set in the editor's toolbar"]},
     None, "zoom", False),
    ("section", {"heading": "Slide backgrounds", "bg_color": "#0f172a", **DARK}, "Press the down arrow to see more backgrounds.", None, False),
    ("bullets", {"heading": "Gradients", "items": ["Five built-in gradients, or any colour"], "bg_gradient": "ocean", "vertical": True, **DARK}, None, None, False),
    ("bullets", {"heading": "Background transitions", "items": ["Backgrounds can move differently from the slide in front of them"],
                 "bg_gradient": "sunrise", "bg_transition": "zoom", "vertical": True}, None, None, False),
    ("bullets", {"heading": "And images", "items": ["Choose any image from the media library as a background, filled, fitted or tiled"],
                 "bg_gradient": "night", "vertical": True, **DARK}, None, None, False),
    ("bullets", {"heading": "Marvelous list", "items": ["No order here", "Or here", "Or here", "Or here"]}, None, None, False),
    ("bullets", {"heading": "Fantastic ordered list", "items": ["One is smaller than", "Two is smaller than", "Three"], "ordered": True}, None, None, False),
    ("table", {"heading": "Tabular tables", "rows": ["Item | Value | Quantity", "Apples | $1 | 7", "Lemonade | $2 | 18", "Bread | $3 | 2"], "step": True},
     None, None, False),
    ("quote", {"quote": "Responding to change over following a plan.", "attribution": "Manifesto for Agile Software Development"}, None, None, False),
    ("bullets", {"heading": "Speaker view", "items": ["Press S for a separate window with notes, the next slide and a timer"]},
     "Only you see these notes, in the speaker view.", None, False),
    ("bullets", {"heading": "Export to PDF", "items": ["Add ?print-pdf to the present address", "Then print to PDF from the browser, in landscape with no margins"]},
     None, None, False),
    ("bullets", {"heading": "Take a moment", "items": ["Press B or the full stop to pause, and again to resume"]}, None, None, False),
    ("closing", {"heading": "The end", "subheading": "The tour follows the reveal.js demo by Hakim El Hattab (MIT, revealjs.com)", "bg_gradient": "dusk", **DARK},
     None, None, False),
]
