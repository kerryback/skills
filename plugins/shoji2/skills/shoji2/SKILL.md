---
name: shoji2
description: >-
  Build a Quarto reveal.js slide deck in the Shoji 2 style — the plum, pale-gray
  and dusty-blue Shoji theme with a slimmer frame and smaller type, so a slide
  holds appreciably more: thin rules, a shallow title band, tight margins, plus
  the same cards, callouts, stats, steps, and half-bleed picture layouts,
  rendered to HTML and exported to PDF. Use when the user invokes /shoji2, asks
  for a shoji2 deck by name, or is editing a deck already built with this theme.
  For the original, roomier-framed version use the shoji skill; for a general
  "make me slides" with no style named, prefer the pptx skill.
---

# Shoji 2

Author a presentation as a Quarto reveal.js deck: Markdown in a `.qmd`, a
vendored `.scss` theme, `quarto render` to a self-contained `.html`, decktape to
PDF. The theme does the visual work — the frame, the palette, the tracking, and
a small set of components — so slides look designed without hand-placed boxes.

The look comes from Microsoft's Shoji PowerPoint theme: plum `#595460`, pale gray
`#EBEDEB`, dusty blue `#97A7B8`, bold titles with wide letter spacing, and a
Mondrian-ish grid of rectangles filling the canvas. Every rectangle and rule in
this theme lands on one of a few shared lines, so the shapes line up both within
a slide and from slide to slide. Each layout is a different selection of
rectangles from those lines, which is why the layout classes exist: the source
deck moves its title band and blocks around, and so should a deck built with
this.

## What Shoji 2 changes

Shoji 2 is the same design with the frame pulled in and the type set down. On
the same 1280×720 canvas:

| | shoji | shoji2 |
|---|---|---|
| Rules and block edges | 6px | 4px |
| Title band height | 137px | 108px |
| Left seam | 102px (8%) | 72px (5.6%) |
| Base rule | 626px (87%) | 660px (92%) |
| Text margins, left / right / foot | 165 / 115 / 118 | 116 / 76 / 80 |
| Root font size | 32px | 28px |

The text area goes from 1000×425 to 1088×504 — 29% more room — and the smaller
type puts roughly two-thirds again as much content on a slide before it
overflows. The interior lines are untouched (the foot strip still splits at 38%,
the picture layouts still meet at the panel's midpoint), so the proportions read
as Shoji; only the frame's share of the canvas shrinks.

Nothing else differs. The class vocabulary is identical, so an existing shoji
deck converts by pointing `theme:` at `shoji2.scss` — then re-check every slide,
because the type change reflows everything.

## When to use this vs. other deck skills

- Use shoji2 when the user asks for it by name, or when editing a deck whose
  front matter already points at `shoji2.scss`.
- Use the `shoji` skill for the original: a heavier frame, larger type, less on
  each slide. Reach for it when the deck is sparse and wants the air.
- Use the `pptx` skill for a general request with no style named, and always
  when the user needs a natively editable PowerPoint.
- Shoji 2 suits text- and code-heavy academic decks that were fighting the
  panel's edges: same quiet palette, appreciably more canvas.

## Prerequisites

- Quarto, to render. `quarto --version`.
- decktape plus Node, only for PDF export. `npm install -g decktape`.

Render first; only chase a missing tool if the render actually fails.

## Workflow

### 1 — Scaffold the deck folder

Work in a folder that will be the deliverable, and put the theme beside the
`.qmd` so the relative `theme:` resolves:

- Copy `assets/shoji2.scss` into the deck folder.
- Copy `assets/starter.qmd` and rename it, or write fresh front matter:

```
---
title: "Your title"
subtitle: "Optional subtitle"
author: "Kerry Back"
date: today
format:
  revealjs:
    theme: shoji2.scss
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
bottom rule. The slimmer frame buys room, it does not buy a safety net — and the
smaller type makes it easy to keep adding until a slide is a wall. Serve the deck
and screenshot each slide, then look at them.

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
- No long inline code inside a card, a stat, or a compared column. Inline code
  never wraps, so one wide backticked string forces its column open and collapses
  the rest of the row. Put commands and paths in a `.note`, a `.lead`, or a
  fenced block, where the full panel width is available.
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
  1280×720 CSS pixels but is presented full-screen. Figures may run to 470px tall
  here, against 400px in shoji.
- The extra room is for breathing space and for figures, not a licence to fill
  the slide. Body type is 28px on a canvas shown at a distance; a slide that uses
  every pixel of the wider panel is a slide nobody at the back can read.
