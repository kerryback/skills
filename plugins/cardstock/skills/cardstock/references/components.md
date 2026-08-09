# Theme component vocabulary

Every class below is defined in `assets/revealjs-style.scss`. Prefer these over
hand-written CSS — they give the deck one consistent look. Snippets are Quarto
Markdown; drop them into a slide (the body under a `##` heading).

## Cards (side-by-side content)

Cards are the workhorse layout. Reach for them whenever list items run long, and
especially instead of nested/indented lists: one card per would-be parent
bullet, with its sub-points as the card's short lines. Long bullet lists and
nested lists read as cramped and default; cards read as designed.

Wrappers lay out a CSS grid, one column per card:

- `.two-cards` — 2 columns
- `.three-cards` — 3 columns
- `.four-cards` — 4 columns
- `.six-cards` — 3×2 grid of short label cards

Inside a wrapper, each card is `::: {.card-COLOR}` — the color variant on its
own. There is no separate `.card` class.

```
::: {.three-cards}
::: {.card-blue}
[Card Title]{.card-title}

- bullet
- bullet
:::
::: {.card-amber}
[Card Title]{.card-title}

- bullet
:::
::: {.card-teal}
[Card Title]{.card-title}

- bullet
:::
:::
```

Color variants: `.card-blue`, `.card-amber`, `.card-teal`, `.card-purple`,
`.card-red`, `.card-dark` (dark navy, white text). Inside a wrapper,
`.card-light` (light-blue tint) is also available.

- `[Title]{.card-title}` is the bold, color-matched heading at the top of a card.
- A single card can stand alone outside a wrapper (e.g. `::: {.card-red}`);
  every variant carries its own padding, rounding, and shadow. Inside a wrapper
  the wrapper restyles it for the grid cell.

## Section dividers

A full-bleed dark slide that opens a part of the talk:

```
## Part Two: Methods {.section-divider}
```

## Callouts and boxes

- `.explainer` — small muted note under content (a caption/aside). Ration it.
  One per slide across a whole deck is the most common way a cardstock deck goes
  flat: the notes stop reading as notes, and the audience learns to skip the
  last line. About one content slide in four. If it carries real weight, put it
  in the content; if it is narration, put it in `::: {.notes}`.
- `.punchline` — dark navy block for the line the slide is built toward.
- `.highlight-box` — emphasized callout with a blue left border.
- `.info-box` — light panel with an optional `[Title]{.box-title}`.
- `.comparison-table` — wraps a Markdown table in the styled comparison look.

```
::: {.highlight-box}
The key point you want to land, in one or two lines.
:::

::: {.explainer}
A quieter note that adds context without competing for attention.
:::
```

### Explainer or punchline?

These two look nothing alike and are constantly confused, because both sit at
the bottom of a slide. The test is whether the line concludes the slide or
merely supports it.

A punchline is the claim the slide exists to make — "an agent is not a
different technology," "the best guardrail is a tool the agent does not have."
It gets the dark block, and it is the one thing on a cardstock slide worth
holding back:

```
::: {.punchline .fragment}
The skill is not prompting --- it is describing the goal well and
judging the result. [Delegation, not dictation.]{.accent}
:::
```

An explainer is a caveat, a source note, a mechanical detail, or a figure
caption. It supports the slide without concluding it, so it should be on screen
the whole time — fragmenting a footnote just makes people wait for something
that was never the point.

Two failure modes, both common. Dressing a footnote as a punchline spends the
slide's strongest visual on a detail and drains the emphasis from the slides
that have earned it. Leaving a real punchline in small grey type buries the
one sentence the audience should remember. When a line does both jobs at once
— skill attribution followed by a real claim, say — split it: the attribution
stays an explainer, the claim becomes the punchline.

`.punchline` supersedes writing a bare `::: {.card .card-dark}` at the end of a
slide, which is what decks did before the class existed. It is the same navy;
the difference is that it is named for its job and carries the space above it
that separates a conclusion from one more card.

## Code, prompt, and response boxes

For showing code or an AI exchange (dark code panel, blue "user" panel, gray
"reply" panel):

```
::: {.code-box}
::: {.box-title}
Under the hood
:::
result = df.groupby("Category")["Revenue"].sum()
:::

::: {.prompt-box}
::: {.box-title}
What you tell Claude
:::
Summarize revenue by category and chart the top five.
:::
```

Inline shell command styling: `[quarto render deck.qmd]{.shell-cmd}`.

## Data-forward layouts

- `.stat-cards` — big-number metric cards (`.stat-number` + `.stat-label`).
- `.step-flow` (4 steps), `.step-flow-5`, `.step-flow-6` — arrowed process flow
  with `.step-card` (`.step-icon`, `.step-title`, `.step-desc`). Add `.fragment`
  to each `.step-card` to walk the flow a step at a time; the connecting arrows
  then draw themselves out as each next step lands, instead of standing there
  pointing at nothing. A numbered sequence is the layout that most wants this.
- `.timeline` — horizontal timeline of `.timeline-item`s.
- `.tool-grid` — 5-up grid of `.tool-card` icon tiles.

```
::: {.stat-cards}
::: {.stat-card}
[94×]{.stat-number}
[Price-to-sales]{.stat-label}
:::
::: {.stat-card}
[$18.7B]{.stat-number}
[Revenue]{.stat-label}
:::
::: {.stat-card}
[$1.75T]{.stat-number}
[Valuation]{.stat-label}
:::
:::
```

## Image slides

- `## Title {.image-slide}` — centered image slide with a caption.
- `## Title {.top-aligned}` — title on top, large image filling the rest.
- Wrap an image in `::: {.img-contain}` to keep it within the slide bounds.

```
## Results {.image-slide}

![](images/chart.png)
```

## Inline emphasis

- `[text]{.accent}` — blue emphasis (amber inside dark cards).
- `[text]{.amber}` — amber emphasis.

## Density and alignment helpers

- `{.shrink}` on a `##` heading — scales a dense slide down to fit.
- `{.centered-statement}` — large centered single statement, no heading rule.
- `{.quote-slide}` — dark quote slide (`.quote-text`, `.quote-source`,
  `.amber` for emphasis inside the quote).

## Keeping the deck varied

Cards are the workhorse, which is exactly why a deck drifts into using nothing
else. The components below the fold — `.stat-cards`, `.timeline`, `.tool-grid`,
`.comparison-table`, `.six-cards`, `.quote-slide`, and the image layouts — are
what give a deck more than one silhouette. They tend to go unused not because
they don't fit but because `.two-cards` always sort of fits.

Two checks worth running on a finished deck:

- Count the wrappers. If one layout carries more than about a third of the
  content slides, or the same wrapper runs three slides in a row, rework the
  middle one. Look for content that is really a number (`.stat-cards`), a
  sequence (`.step-flow`, `.timeline`), or a genuine A-vs-B (`.comparison-table`).
- Count the pictures. A deck about software with no screenshots in it is
  describing something it could be showing. Check `images/` for assets the
  slides never reference.

## Quick chooser

| You have… | Use |
|---|---|
| Two contrasting ideas (problem/solution, before/after) | `.two-cards` |
| Three or four parallel points | `.three-cards` / `.four-cards` |
| A headline number or two | `.stat-cards` |
| A process or pipeline | `.step-flow` / `-5` / `-6` |
| Dates / evolution over time | `.timeline` |
| A row of tools or logos | `.tool-grid` |
| A side-by-side comparison table | `.comparison-table` |
| One line that must land | `.highlight-box` or `{.centered-statement}` |
| The takeaway a slide is built toward | `.punchline` (add `.fragment`) |
| A caveat, source note, or figure caption | `.explainer` (no fragment) |
| A quotation | `{.quote-slide}` |
| A slide that overflows | add `{.shrink}` or split into two `##` slides |
