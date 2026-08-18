# shoji

Slide decks in the Shoji style: a Quarto reveal.js theme built from the
PowerPoint design of the same name — plum `#595460`, pale gray `#EBEDEB`, dusty
blue `#97A7B8`, bold letter-spaced titles, and a Mondrian-ish grid of rectangles
filling the canvas.

Every rectangle and rule lands on one of a few lines measured out of the
original .pptx — vertical at 8%, 38% and 91%, horizontal at 12%, 19%, 50%, 69%
and 87% — so shapes line up within a slide and from slide to slide. Slide titles
sit in a full-bleed plum band; each layout moves that band and the blocks around,
the way the source deck's layouts do.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install shoji@kerryback
```

Then ask for a deck, or invoke it with `/shoji`.

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
[`skills/shoji/references/components.md`](skills/shoji/references/components.md).

## The one authoring trap

Never put a markdown heading inside a fenced div. Pandoc fuses the two into a
`<section>`, which reveal reads as a vertical stack: the frame doubles up and
forward navigation jumps back to slide 1. Use `[Title]{.card-title}` inside a
card and `[Label]{.eyebrow}` inside any other div.

## Notes

The deck's front matter needs `width: 1050`, `height: 700` and `margin: 0`. The
grid is specified in px, which are canvas units and scale with the deck — but
only at that canvas size, and reveal's default 10% margin scales the canvas by
0.9, which leaves 1px slivers along the seams.
