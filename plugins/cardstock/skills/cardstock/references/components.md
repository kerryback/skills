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

- `.explainer` — small muted note under content (a caption/aside).
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
  with `.step-card` (`.step-icon`, `.step-title`, `.step-desc`).
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
| A quotation | `{.quote-slide}` |
| A slide that overflows | add `{.shrink}` or split into two `##` slides |
