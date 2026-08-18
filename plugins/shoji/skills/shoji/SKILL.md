---
name: shoji
description: >-
  Build a Quarto reveal.js slide deck in the Shoji style — a plum, pale-gray and
  dusty-blue theme derived from the PowerPoint design of the same name, with an
  offset panel frame, letter-spaced titles, cards, callouts, stats, steps, and
  half-bleed picture layouts, rendered to HTML and exported to PDF. Use when the
  user invokes /shoji, asks for a shoji deck by name, or is editing a deck
  already built with this theme. For a general "make me slides" with no style
  named, prefer the pptx skill.
---

# Shoji

Author a presentation as a Quarto reveal.js deck: Markdown in a `.qmd`, a
vendored `.scss` theme, `quarto render` to a self-contained `.html`, decktape to
PDF. The theme does the visual work — the frame, the palette, the tracking, and
a small set of components — so slides look designed without hand-placed boxes.

The look comes from Microsoft's Shoji PowerPoint theme: plum `#595460`, pale gray
`#EBEDEB`, dusty blue `#97A7B8`, bold titles with wide letter spacing, and a
Mondrian-ish grid of rectangles filling the canvas. Every rectangle and rule in
this theme lands on one of a few shared lines measured out of that .pptx —
vertical at 8%, 38% and 91%, horizontal at 12%, 19%, 50%, 69% and 87% — so the
shapes line up both within a slide and from slide to slide. Each layout is a
different selection of rectangles from those lines, which is why the layout
classes exist: the source deck moves its title band and blocks around, and so
should a deck built with this.

## When to use this vs. other deck skills

- Use shoji when the user asks for it by name, or when editing a deck whose
  front matter already points at `shoji.scss`.
- Use the `pptx` skill for a general request with no style named, and always
  when the user needs a natively editable PowerPoint.
- Shoji suits text- and code-heavy academic decks: quiet palette, generous line
  spacing, plenty of room inside the panel.

## Prerequisites

- Quarto, to render. `quarto --version`.
- decktape plus Node, only for PDF export. `npm install -g decktape`.

Render first; only chase a missing tool if the render actually fails.

## Workflow

### 1 — Scaffold the deck folder

Work in a folder that will be the deliverable, and put the theme beside the
`.qmd` so the relative `theme:` resolves:

- Copy `assets/shoji.scss` into the deck folder.
- Copy `assets/starter.qmd` and rename it, or write fresh front matter:

```
---
title: "Your title"
subtitle: "Optional subtitle"
author: "Kerry Back"
date: today
format:
  revealjs:
    theme: shoji.scss
    width: 1280
    height: 720
    margin: 0
    max-scale: 5
    slide-number: c/t
    footer: "Course or talk name"
    highlight-style: github
---
```

`width: 1280`, `height: 720`, `margin: 0` and `max-scale: 5` are load bearing.

- The grid is specified in px, which are canvas units and scale with the deck —
  but only if the canvas is that size.
- 1280×720 is 16:9. Reveal scales the canvas but never reshapes it, so a canvas
  that is not the screen's shape is letterboxed: the frame's rectangles sit in a
  fixed region while the pale viewport background fills the rest of the window.
- `margin: 0` matters twice over: reveal's default 10% margin scales the canvas
  by 0.9, which puts every edge on a fractional device pixel and leaves 1px
  slivers of the wrong colour along the seams.
- `max-scale: 5` overrides reveal's default cap of 2×. Without it the deck stops
  growing at 2560px and just sits in the middle of any larger window.

### 2 — Write the slides

`##` starts a slide; `#` starts a section divider, which the theme renders as a
plum band automatically. Body content is plain Markdown plus the theme's classes
— read `references/components.md` and build with those rather than ad-hoc CSS.

No speaker notes. The presenter narrates; a `::: {.notes}` block is a place for
cut text to hide instead of being cut.

### 3 — Prune what you drafted

A slide is a visual aid for someone talking over it. Cut whole sentences and
whole bullets, not words inside kept sentences: anything that explains what the
slide already states, narrates what the audience can see, foreshadows a later
slide, or expands a card's own title. Keep the claim and the specifics nobody
can reconstruct from hearing them once — a number, a name, a path, a command,
a line of code.

### 4 — Render and look at every slide

```
quarto render <name>.qmd
```

Reading the `.qmd` will not tell you whether a slide fits, and this theme does
not shrink text to fit: content longer than the panel runs straight past the
bottom rule. Serve the deck and screenshot each slide, then look at them.

```
python3 -m http.server 8712 &
```

Reveal decks need HTTP; they misbehave from `file://`. Walk the deck with
`window.Reveal.next()` between screenshots rather than jumping by hash — id-based
hash navigation can bounce back to slide 1.

Fix an overflowing slide by splitting it or cutting content.

### 5 — Say what would make it better

Once the draft is whole, read it as a sequence and tell the user, unprompted,
what would raise it: layouts that repeat, claims the deck asserts but could show,
a real number or screenshot instead of four bullets. Name the slide, name the
change, offer to make it.

### 6 — Export (optional)

```
decktape reveal http://127.0.0.1:8712/<name>.html <name>.pdf --size 1280x720
```

decktape hangs on `file://` URLs — always give it the served URL. The exported
PDF keeps the frame, the footer, and the slide numbers.

## Conventions (hard rules)

- Never put a markdown heading inside a fenced div. Pandoc fuses the heading and
  the div into a `<section>`, reveal reads that as a vertical stack, the frame
  doubles up and forward navigation jumps back to slide 1. Inside a `.card` use
  `[Title]{.card-title}`; inside any other div use `[Label]{.eyebrow}`. The
  slide's own `##` heading is fine and gives the slide a usable id.
- `##` starts a slide. No `---` rules between slides; they create blank ones.
- Keep the title's letter spacing. The tracking is what makes this design read
  the way it does — don't override `letter-spacing` on headings.
- Relative paths for images and assets; the deck folder moves.
- Preserve the user's wording when restyling an existing deck. Change classes
  and layout, not prose, unless asked.

## Authoring guidance

- One idea per slide; let the panel's whitespace carry the rest.
- Vary the slide layout, not just the components. The banded default is the
  workhorse; move the band to the foot with `.band-bottom` every few slides, drop
  it with `.plain-title` when the slide already carries a lot (code, a wide
  table, a figure), and break the run with a picture layout. Three consecutive
  slides with the band in the same place is the thing to avoid — on a projector
  the audience sees one silhouette for the whole session.
- Vary the components too. Cards are the easy default and so the one to ration —
  no single one on more than about a third of the content slides.
  `references/components.md` has stats, steps, compared columns, and picture
  layouts for exactly this reason.
- Prefer cards to bullet lists once items run past a phrase each; prefer a
  picture layout to a fifth card slide.
- Open each major part with a `#` heading — the plum band is the deck's rhythm.
- The palette is three colors. `.card-sage` and `.card-sand` exist for the rare
  fourth category; reaching for them often turns a quiet design loud.
- Charts and diagrams as SVG or high-dpi PNG from matplotlib. The canvas is only
  1280×720 CSS pixels but is presented full-screen.
