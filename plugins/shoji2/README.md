# shoji2

Shoji with the frame pulled in. Same Quarto reveal.js theme built from the
PowerPoint design of the same name — plum `#595460`, pale gray `#EBEDEB`, dusty
blue `#97A7B8`, bold letter-spaced titles, a Mondrian-ish grid of rectangles —
but the rectangles are thinner, the margins tighter and the type smaller, so
each slide carries appreciably more.

## What differs from shoji

On the same 1280×720 canvas:

| | shoji | shoji2 |
|---|---|---|
| Rules and block edges | 6px | 4px |
| Title band height | 137px | 108px |
| Left seam | 102px (8%) | 72px (5.6%) |
| Base rule | 626px (87%) | 660px (92%) |
| Text margins, left / right / foot | 165 / 115 / 118 | 116 / 76 / 80 |
| Root font size | 32px | 28px |
| Figure height cap | 400px | 470px |

The text area goes from 1000×425 to 1088×504 — 29% more room — and the smaller
type puts roughly two-thirds again as much on a slide before it overflows. The
interior lines don't move: the foot strip still splits at 38% and the picture
layouts still meet at the panel's midpoint, so the proportions still read as
Shoji. Only the frame's share of the canvas shrinks.

Everything else is identical, including every class name. An existing shoji deck
converts by pointing `theme:` at `shoji2.scss` — then look at every slide again,
because the type change reflows all of them.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install shoji2@kerryback
```

Then ask for a deck, or invoke it with `/shoji2`.

## Requirements

- Quarto, to render.
- Node plus decktape, only if you want a PDF.

## Layouts

| Class | Layout |
|---|---|
| (none) | Title in a plum band across the top |
| `.band-bottom` | Title in a plum band along the foot, blue block beside it |
| `.plain-title` | No band; plum title on the white panel |
| `.no-title` | Heading hidden, its space reclaimed |
| `.image-left` / `.image-right` | Picture fills half the panel, text beside it |

Vary them — three slides running with the band in the same place is the thing to
avoid. Components (cards, callouts, stats, numbered steps, compared columns,
picture layouts) are documented in
[`skills/shoji2/references/components.md`](skills/shoji2/references/components.md).

## The one authoring trap

Never put a markdown heading inside a fenced div. Pandoc fuses the two into a
`<section>`, which reveal reads as a vertical stack: the frame doubles up and
forward navigation jumps back to slide 1. Use `[Title]{.card-title}` inside a
card and `[Label]{.eyebrow}` inside any other div.

## Notes

The deck's front matter needs `width: 1280`, `height: 720`, `margin: 0` and
`max-scale: 5`. The grid is specified in px, which are canvas units and scale
with the deck — but only at that canvas size; 1280×720 is 16:9, so the canvas is
the shape of the screen rather than being letterboxed inside it; `max-scale`
lifts reveal's default 2× cap, which would otherwise stop the deck growing at
2560px; and reveal's default 10% margin scales the canvas by 0.9, which leaves
1px slivers along the seams.
