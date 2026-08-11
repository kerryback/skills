---
name: cardstock
description: >-
  Build a slide deck in Kerry Back's Quarto reveal.js house style — a vendored
  theme with cards, section dividers, comparison tables, and step flows,
  rendered to HTML and exported to PDF, PowerPoint, or PNG. Use when the user
  invokes /cardstock, asks for a cardstock deck by name, or is editing a deck
  already built with it. For a general request to make slides or a
  presentation with no style specified, prefer the pptx skill.
---

# Cardstock

Author a presentation as a Quarto **reveal.js** deck: you write plain-text
Markdown in a `.qmd` file, Quarto renders it to a self-contained `.html` deck
that presents in any browser, and (optionally) decktape exports it to PDF, PNG
images, or PowerPoint. A vendored theme does the visual heavy lifting — cards,
callouts, dividers, tables, and diagram layouts — so decks look designed, not
defaulted.

This is the "let the browser lay it out" approach: you describe structure in
Markdown and use theme classes; you never hand-place text boxes at inch
coordinates on a blank canvas.

## When to use this vs. the `pptx` skill

- Use **cardstock** when the user asks for it — `/cardstock`, "a cardstock
  deck", "the usual deck style" — or when editing a deck already built with this
  theme. The deliverable is an HTML deck you present in a browser, exportable to
  PDF, PNG, or an image-based PPTX.
- Use the **`pptx` skill** for a general "make me slides" or "build a deck" with
  no style named. It is also the right choice whenever the user needs a
  *natively editable* PowerPoint — real text boxes and shapes they will rework —
  since decktape's PPTX export here is image-per-slide.
- **Don't reach for cardstock by default.** It imposes one specific house style;
  someone who just wants slides is usually better served by PowerPoint. When it
  is genuinely unclear, ask.

## Prerequisites

- **Quarto** — required to render. Check: `quarto --version`. Ships with Academic
  Studio; if missing, install from Help → Run Setup…
- **Node.js + decktape** — only needed for PDF/PPTX/PNG export. `node` ships with
  Academic Studio; `decktape` is an opt-in program under Help → Run Setup…
  (or `npm install -g decktape`). Not needed just to build and present.

Don't probe for these up front. Render first; if `quarto` is genuinely missing,
point the user at Run Setup, then continue.

## Workflow

### 1 — Scaffold the deck folder
Work in a dedicated folder (the deliverable). Put the theme next to the `.qmd`
so the relative `theme:` reference resolves:

- Copy `assets/revealjs-style.scss` into the deck folder.
- Start from `assets/starter.qmd` (copy it and rename), or write a fresh `.qmd`
  with the front matter shown below.

Front matter for a standalone deck (mirrors the theme's expectations — keep
`auto-stretch: false` and the 1920×1080 canvas):

```
---
title: "Your Title"
subtitle: "Optional subtitle"
author: "Name<br>Affiliation"
format:
  revealjs:
    theme: [default, revealjs-style.scss]
    highlight-style: monokai
    slide-number: 'c/t'
    transition: fade
    navigation-mode: linear
    width: 1920
    height: 1080
    margin: 0.05
    center: true
    auto-stretch: false
---
```

### 2 — Write the slides
Each `##` heading starts a new slide. Body content is normal Markdown plus the
theme's component classes. Read `references/components.md` and lay content out
with those components (cards, callouts, dividers, tables) instead of hand-rolled
CSS — that is what makes the deck look consistent.

Do not write speaker notes. No `::: {.notes}` blocks — the presenter narrates
live, and a note block is somewhere for cut text to hide instead of being cut.

### 3 — Prune every slide you draft

A slide is a visual aid for someone talking over it. A sentence that says what
the presenter is about to say competes with them, and the audience reads it
instead of listening. Draft first, then cut — and cut with fresh eyes, because
the sentences you just wrote all feel necessary.

This is sentence-level surgery, not word-level. Delete whole sentences, whole
bullets, whole explainers. Leave the sentences that survive exactly as written;
squeezing words out of a kept sentence makes it terser without making the slide
quieter, and it costs the author their voice.

After drafting a slide, or a run of them, dispatch a subagent over the `.qmd`
with this brief:

> You are pruning slides for a live talk. The presenter narrates; the slide
> supports. Read each slide and list the sentences and bullets to delete.
>
> Delete: a sentence that explains or justifies what the slide already states;
> transitions and foreshadowing ("we come back to this after the break");
> narration of what the audience can already see, including a caption under an
> obvious screenshot; a second sentence that restates the first in other words;
> a card description that merely expands the card's title.
>
> Keep: the claim itself, and anything the audience cannot reconstruct from
> hearing it once — a number, a name, a series ID, a file path, a command to
> type, a line of code.
>
> Work at the level of whole sentences and whole lines. Never edit inside a
> sentence you are keeping, never add content, and never rewrite for style.
>
> Report each cut as the exact text to delete, slide by slide, with one clause
> saying why.

Apply the cuts you agree with. Keep anything genuinely load-bearing, but treat
deletion as the default — the presenter will say it. The slide must still be
coherent on its own; it must not deliver the talk.

**What over-writing looks like.** Four patterns, all of them from real decks:

*Narrating the visual.* A slide showing real output from a script, captioned
"The script produces facts and Claude writes the report — that division is the
whole point of a skill." The output is on screen and the point is the
presenter's line. Cut the caption; keep the output.

*Foreshadowing.* "Set `tools=[]` and `permission_mode` to `dontAsk`. These are
the two lines that matter for security, and we come back to both after the
break." Cut the second sentence. The break will come.

*Expanding the title.* A card headed "Switching is one string" whose body opens
"Switching from one model to another takes a single string." Cut that sentence
and let the body start with the example.

*The agenda with descriptions.* Five cards, each a topic plus a sentence saying
what the topic will cover. Cut all five sentences. The five topics are the
agenda; the sentences are the talk.

*Cards built to carry an argument.* A slide reading "The skill and the app
answer the questions you thought of when you built the watchlist," under two
cards listing what they do well and three example questions they cannot answer.
The cards are the presenter working through the argument out loud. Cut both.
One more sentence finishes the slide: "An agent can answer questions the user
thinks of on the spot."

### 4 — Render and check every slide
```
quarto render <name>.qmd          # produces <name>.html
```
Reading the `.qmd` will not tell you whether a slide fits. Serve the rendered
deck over HTTP (reveal decks do not run from `file://`), then screenshot each
slide at 1920×1080 by navigating to `<url>#/<n>` for `n` from 0 through the
slide count, and tile the results into one contact sheet. A clipped caption, an
image that came out too small to read, or a wall of unreadable body text is
obvious in the tiles and invisible in the source. Then open the few slides that
look wrong at full size to confirm.

Fix a dense slide with `.shrink`, by splitting it into two `##` slides, or by
cutting the detail. Note that `.shrink` only fixes *vertical*
overflow — a slide that is too wide needs a different layout.

### 5 — Say what would make it better
Do not stop at "it renders." Once the draft is whole, read it as a sequence and
tell the user, unprompted, what would raise it — a few concrete lines, not a
survey of everything possible:

- Layouts that repeat, and what to put in their place.
- Claims the deck asserts but could show: a screenshot of the real tool, a real
  number from the user's own data, a chart instead of four bullets.
- Assets already on hand and going unused — check the deck's `images/` folder
  against what the slides actually reference.
- Anything running long, thin, or duplicated against a companion deck.

Name the slide, name the change, and offer to make it. When a suggestion needs
something only the user can supply — a screenshot of their screen, a file, a
number — say so and offer to do the parts that do not.

### 6 — Export (optional)
For PDF, PNG images, or an image-based PPTX, read `references/export.md` and use
decktape on the rendered `.html`.

### 7 — Offer a structural overview (longer decks)
Once a deck runs long, or after a round of restructuring, offer to generate a
standalone HTML overview: every section and slide with a one-sentence
description, plus flags for duplication, overflowing slides, agenda drift, and
orphans. Read `references/overview.md` for how to measure the deck and lay the
page out. Offer it — don't build one unasked, and don't regenerate silently.

## Conventions (hard rules)

These keep decks rendering cleanly — follow them exactly:

- `##` starts a new slide. Do **not** put `---` horizontal rules between slides;
  they create unwanted blank slides.
- Use **plain triple-backtick code fences with no language specifier** (just
  ```` ``` ````), not ```` ```python ````/```` ```sql ````. The theme styles
  code blocks; a language tag can fight the highlighter.
- A card is a color variant on its own (e.g. `::: {.card-blue}`). There is no
  `.card` class — never pair it with a variant. Each variant carries its own
  padding, rounding, and shadow, and the grid wrappers style the variants
  directly, so a bare variant is fully styled whether it stands alone or sits in
  a `.two-cards`/`.three-cards`/`.four-cards` grid.
  One exception: a deck built against a vendored theme older than 1.3.0 keyed
  those wrapper rules off a literal `.card` class, so there `::: {.card-blue}`
  silently lost its bold card title and its smaller list text. Before editing an
  existing deck, check whether its `.scss` mentions `.card` at all; if it does,
  follow whichever convention that file and its slides already use.
- Use **relative paths** for images and assets (`![](images/chart.png)`), never
  absolute paths — the deck folder moves.
- Preserve the user's wording. When restyling or restructuring a deck, change
  layout/classes only; don't rewrite the text unless asked.

## Authoring guidance

- One idea per slide. Keep on-slide text light; let cards and whitespace carry
  it. Elaboration gets deleted, not relocated.
- **Write for a presenter, not a reader.** The deck is projected while someone
  talks; it is not a handout. Every sentence on a slide is a sentence the
  presenter now has to either read aloud or talk around. Give the slide the
  claim and the un-guessable specifics, and leave the argument to the voice in
  the room.
- **Prefer multi-card layouts to bullet lists when the item text is long.** A
  handful of one-line bullets is fine; but once items run to a phrase or
  sentence each, put them in `.two-cards`/`.three-cards`/`.four-cards` — the
  cards give each point room to breathe and read as designed rather than as a
  dumped list.
- **Try hard to avoid nested (indented) lists — use a multi-card layout
  instead.** A parent bullet with sub-bullets almost always wants to be a card
  per parent, with the sub-points as the card's short bullets or lines. Nested
  lists look cramped and default; cards don't.
- Vary the layout from slide to slide. A deck whose content slides are mostly
  the same wrapper reads as a form someone filled in — on a projector the
  audience sees one silhouette for the whole session. `.two-cards` is the easy
  default and so the one to ration: no single layout on more than about a third
  of the content slides, and never the same wrapper three slides running. The
  same goes for color — a deck that only ever reaches for `.card-blue` and
  `.card-amber` has a two-color palette by accident, not by choice.
- Spend the whole vocabulary. `.stat-cards`, `.timeline`, `.comparison-table`,
  `.step-flow`, `.six-cards`, `.tool-grid`, `.quote-slide`, and the image
  layouts exist so that a deck has more than one shape. Before writing a fourth
  `.two-cards`, check `references/components.md` for something that fits the
  content better — a headline number, a sequence, a real comparison.
- Use `.explainer` sparingly. It is an aside, and an aside under every slide is
  not an aside — it flattens emphasis and teaches the audience to skip the last
  line. Roughly one content slide in four is plenty. If the note is
  load-bearing, it belongs in the slide's content; if it is narration, it
  belongs nowhere in the file — the presenter says it.
- Tell an explainer from a punchline before choosing either. A punchline is the
  claim the slide is built toward; it gets `.punchline` (dark navy), and it is
  the one thing worth holding back with `.fragment`. An explainer is a caveat,
  a source note, or a figure caption; it supports the slide without concluding
  it and stays on screen throughout. Do not dress a footnote as a punchline —
  that spends the slide's loudest element on a detail — and do not bury a real
  takeaway in small grey type. `.punchline` replaces the older habit of ending a
  slide with a bare `::: {.card .card-dark}`. See `references/components.md`.
- Fragments are for sequence, not decoration. The two places they earn their
  keep are a `.step-flow` walked a step at a time (the arrows draw themselves
  as each step lands) and a `.punchline` held until the setup above it has been
  made. Resist walking bullet lists — that is the PowerPoint habit the card
  layouts exist to replace.
- A picture is the strongest change of pace available. A screenshot of the real
  thing, a diagram, or a chart breaks a run of card slides better than any card
  variant can. If the deck describes software the user actually runs, show it
  running: `{.top-aligned}` for a wide capture, `{.image-slide}` for a centered
  one. Prefer a real artifact over a described one — a slide that asserts the
  tool is good is weaker than one that shows its output.
- Open major parts with a divider slide: `## Section Title {.section-divider}`.
- **Prefer SVG or matplotlib images for figures and charts.** The canvas is
  1920×1080 and often projected, so vector art stays sharp — generate charts
  with matplotlib (save as `.svg`, or high-resolution PNG via
  `savefig(..., dpi=200)`) and prefer `.svg` for diagrams and logos. Avoid
  low-resolution raster screenshots, which look soft when scaled up.
- Reach for the right component: side-by-side → `.two-cards`/`.three-cards`;
  a metric → `.stat-cards`; a process → `.step-flow`; a before/after or
  problem/solution → two cards; a comparison → `.comparison-table`.
- The theme's default title slide is dark with an amber-accented subtitle — a
  `title:`/`subtitle:` in the front matter is enough; don't rebuild it.
