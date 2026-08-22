# Shoji components

Every class below is defined in `shoji.scss`. Copy the markdown as shown.

## Palette

| Role | Color |
|---|---|
| Plum — titles, bands, table headers, rules | `#595460` |
| Dusty blue — margin block, bullets, links, sub-headings | `#97A7B8` |
| Deeper blue — bullets and `h3`, where `#97A7B8` is too light | `#6f8497` |
| Pale gray — page, card fills, table striping | `#EBEDEB` |
| Panel white | `#fbfbfa` |
| Body ink | `#3b3842` |
| Sage / sand — rare fourth and fifth categories | `#A5B592` / `#D1C499` |

Type is Meiryo when installed, otherwise Zen Kaku Gothic New from Google Fonts.
The `@import` needs network access the first time a viewer opens the deck;
without it the deck falls back to the system sans and still lays out correctly.

## Slide layouts

Four content layouts, so a run of slides doesn't share one silhouette. Vary them
deliberately: the band is the deck's rhythm, and every slide wearing it flattens
that out.

Default — title in a plum band across the top, body on the white panel below:

```markdown
## A slide title

Body content.
```

`.band-bottom` — body on the panel, title in a plum band at the foot with the
blue block beside it:

```markdown
## A slide title {.band-bottom}
```

`.plain-title` — no band; title in plum on the panel. The quietest layout, and
the one to use when the slide is already busy: code, a wide table, a dense
figure.

```markdown
## A slide title {.plain-title}
```

`.no-title` — hides the heading and reclaims its space. Keep a real heading in
the markdown anyway; it gives the slide a usable id.

```markdown
## Internal name {.no-title}
```

Picture layouts (`.image-left`, `.image-right`, below) drop the band too.

Section divider — any `#` heading slide gets the plum band automatically. Add
`{.divider}` to force the band on a `##` slide:

```markdown
# The palette

## Still a divider {.divider}
```

A divider can carry one line under its title:

```markdown
# Part two

Where the argument turns.
```

Title slide — comes from the front matter (`title`, `subtitle`, `author`,
`date`). Don't rebuild it.

## Standfirst and labels

```markdown
::: {.lead}
One sentence setting up the slide.
:::

[Small uppercase label]{.eyebrow}
```

`.eyebrow` is the safe form of `###` inside a div — a real heading there breaks
the deck (see the hard rules in SKILL.md). Outside a div, `###` gives the same
look.

## Cards

`.cards` is the grid; `.cards-2` and `.cards-3` fix the column count. Card titles
must be spans, never headings.

Keep long inline code out of a card. Inline code never wraps, so a backticked
string wider than the card forces that column open and squeezes the others into
unreadable slivers that spill past the base rule — a three-card row with
`/plugin install finance-data@kerryback-skills` in one card is enough to do it.
Put the command in a `.note` under the row, or in a `.lead` above it, where the
full panel width is available.

```markdown
::: {.cards .cards-3}
::: {.card}
[Plum]{.card-title}

What it is used for.
:::

::: {.card .card-blue}
[Dusty blue]{.card-title}

Variants: `.card-blue`, `.card-sage`, `.card-sand`.
:::

::: {.card}
[Pale gray]{.card-title}

The page behind the panel.
:::
:::
```

## Callouts

```markdown
::: {.note}
A quiet aside: pale fill, blue rule on the left.
:::

::: {.note .note-plum}
The same block in plum, for something that matters more.
:::
```

Quarto's own callouts are restyled to the same palette with their icons hidden:

```markdown
::: {.callout-important}
## Title

Body.
:::
```

`callout-note` is blue, `callout-important` plum, `callout-tip` sage,
`callout-warning` and `callout-caution` sand.

## Statistics

```markdown
::: {.stats}
::: {.stat}
[13]{.stat-value}
[slides in the source deck]{.stat-label}
:::
::: {.stat}
[3]{.stat-value}
[colors in the palette]{.stat-label}
:::
:::
```

Three stats across is comfortable; four is tight.

## Numbered steps

Plum squares instead of default numerals. Works as a div around a numbered list
or as a class on the list itself.

```markdown
::: {.steps}
1. First
2. Second
3. Third
:::
```

## Columns

`.compare` on the slide adds a plum hairline between the two columns.

```markdown
## Two columns {.compare}

:::: {.columns}
::: {.column width="50%"}
### Before

Text.
:::

::: {.column width="50%"}
### After

Text.
:::
::::
```

`###` is safe inside `.column` — Quarto builds those divs itself — but `.eyebrow`
is safe everywhere and never surprises.

## Picture layouts

Half the panel is the image, the rest is text. `.image-left` or `.image-right` on
the slide, the picture in `.image-panel`, the text in `.content-panel`.

```markdown
## Picture layouts {.image-left .no-title}

::: {.image-panel}
![](images/photo.jpg)
:::

::: {.content-panel}
[Picture layouts]{.eyebrow}

Text beside the picture.

- A short list works well here
- The column is narrow, so keep lines short
:::
```

The image is cropped to fill (`object-fit: cover`), so give it a portrait-ish
crop or accept the crop.

## Tables

Plain markdown tables get a plum header band, pale striping, and no vertical
rules:

```markdown
| Element | Size | Color |
|---|---|---|
| Slide title | 1.4em bold | plum |
| Body | 1em | ink |
```

## Code and math

Fenced code blocks get a pale fill and a plum left rule; `highlight-style: github`
in the front matter keeps the syntax colors quiet. Inline code sits in a tinted
chip and never breaks across lines — which is why it does not belong in a card,
a stat, or a compared column; anywhere narrow, it breaks the layout rather than
wrapping. LaTeX math renders through MathJax as usual.

````markdown
```python
def replicating_portfolio(u, d, r, cu, cd):
    delta = (cu - cd) / (u - d)
    return delta
```

The price is $C = \Delta S + B$.
````

## Blockquote

```markdown
> A quoted line gets a blue rule and muted type.
```
