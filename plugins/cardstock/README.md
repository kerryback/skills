# cardstock

Slide decks as HTML, PDF, and PPTX (image-only), built with Quarto reveal.js and
exported with Decktape.

The default styling replaces bullet lists with coloured cards, and adds section
dividers, comparison tables, and step flows. If you want it to look like
something else, say so — the theme is a stylesheet in the deck folder, and Claude
will change the colours, the type, or the whole look on request.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install cardstock@kerryback-skills
```

Then ask for a deck, or invoke it with `/cardstock`.

## Requirements

Quarto, for rendering. Decktape (via Node) only if you want PDF or PPTX — the
HTML deck needs nothing else.

## What you get

You present the HTML in a browser. The exports come off the same source:

| format | how | good for |
| --- | --- | --- |
| HTML | Quarto renders it | presenting; the only format with working links and transitions |
| PDF | Decktape | handouts, posting to a course site |
| PPTX | Decktape | handing to someone who wants PowerPoint — but see below |

The PPTX is one image per slide. Nothing in it is editable text, so treat it as
a delivery format, not a starting point. If someone needs a deck they can edit,
use the `pptx` skill instead and skip this one.

## Changing the look

Ask. "Make the cards green", "drop the cards and use plain bullets", "match my
department's palette", "bigger type, fewer words per slide" are all one-sentence
edits. The house style is a starting point, not a constraint — nothing about the
skill assumes you keep it.

## When to use something else

For a general "make me some slides" with no style in mind, the `pptx` skill
produces a natively editable PowerPoint and is usually the better default. Reach
for cardstock when you want the rendered look and the browser as the medium.
