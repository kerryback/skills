# elegant-pdf

Branded documents built from a small HTML design system and rendered with
headless Chrome.

For the things that aren't slides and aren't papers: a one-page announcement, a
conference program, a report, a handbook. You describe it, Claude writes the
HTML against the theme, and it comes out as a PDF or an image.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install elegant-pdf@kerryback
```

Then describe the document you want.

## Requirements

Headless Chrome, Chromium, or Edge for rendering — you almost certainly have one
already. The JPEG step uses `sips`, built into macOS, or ImageMagick's `magick`
elsewhere. No network access needed at any point.

## Two shapes

| | output |
| --- | --- |
| one page — flyer, announcement, invitation | 2× JPEG for posting or emailing, or a clickable PDF |
| multi-page — program, report, handbook | clickable PDF with a cover, running footer, and page numbers |

The 2× JPEG matters for anything going onto a screen: a 1× export looks soft on
every display made in the last decade.

## Recolouring

The default palette is Rice Business navy and gold. It is one block in
`theme.css`, and changing it changes the whole document — so "make this in
Georgetown's colours" is a real one-line edit rather than a find-and-replace
through the markup.

The components — cover, section headers, cards, tables, footers — all read from
that palette, which is why the recolour holds together instead of leaving stray
navy in three places.
