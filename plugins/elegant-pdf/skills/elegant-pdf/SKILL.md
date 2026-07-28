---
name: elegant-pdf
description: >-
  Create elegant, branded documents from a small HTML design system rendered to
  PDF or image with headless Chrome. Use for a one-page flyer / announcement /
  invitation (export a crisp 2x JPEG or a clickable PDF) or a multi-page program,
  report, syllabus, handbook, or booklet (clickable PDF with a cover, running
  footer, and page numbers). Trigger on "make an elegant PDF/flyer/announcement",
  "a nice printable program/handout/booklet", "turn this into a polished PDF",
  "format this like the workshop flyer", or when a fixed-layout, print-quality
  document is wanted (not a reveal.js deck — use the slides skill for those).
  Default palette is Rice Business navy + gold; recolor by editing one block.
license: MIT
---

# elegant-pdf

Produce polished, reproducible documents by writing content HTML against a fixed
design system (`assets/theme.css`) and rendering it with headless Chrome. Two
shapes:

- **Sheet** — a single fixed-width canvas (`.sheet`, 1080px wide) for a flyer /
  announcement. Export a 2x JPEG (email, social, slides) and/or a 1-page PDF.
- **Pages** — Letter pages (`.page`) for a multi-page document: a `.cover` page
  plus content pages, a running footer, and page numbers. Export a PDF.

Real hyperlinks survive into the PDF. Fonts are system serif/sans (Georgia /
Helvetica), so rendering is reproducible with no web-font downloads.

## Workflow

1. **Set up a working copy.** Make a working directory and copy the design system
   plus a starting template into it (keep them side by side so `theme.css`
   resolves):
   ```
   mkdir -p out && cd out
   cp "$SKILL_DIR/assets/theme.css" .
   cp "$SKILL_DIR/assets/flyer.html"   doc.html   # one-page flyer
   #   …or…
   cp "$SKILL_DIR/assets/program.html" doc.html   # multi-page document
   ```
   (`$SKILL_DIR` = this skill's folder, i.e. where this SKILL.md lives.)

2. **Write the content.** Edit `doc.html` — replace the placeholder text, add or
   remove `.item` rows and `.page` sections. Reuse the components below; don't
   invent new CSS unless asked. For a multi-page doc, put the right page number
   in each page's `.pagefoot .pg`. Put genuine URLs in `href`s — they become
   clickable links in the PDF. Never fabricate facts (dates, names, links);
   ask if unknown.

3. **Render** with the bundled script (finds Chrome/Chromium/Edge automatically):
   ```
   bash "$SKILL_DIR/assets/render.sh" pdf  doc.html  document.pdf
   bash "$SKILL_DIR/assets/render.sh" jpeg doc.html  flyer.jpeg          # 2x, 1080x1500
   bash "$SKILL_DIR/assets/render.sh" jpeg doc.html  flyer.jpeg 1080 1330 # custom sheet size
   ```
   For a JPEG, pass a height at least as tall as the sheet's content (extra
   becomes bottom whitespace; too little clips). If a one-page PDF of a `.sheet`
   should have no trailing blank, add to the page's own `<style>`:
   `@page { size: 1080px <content-height>px; margin: 0; }`.

4. **Verify** before delivering: open the PDF/JPEG (or read it back) and confirm
   the layout, that nothing is clipped, and that links resolve.

## Components (in theme.css)

- `.eyebrow` — small letter-spaced label in navy.
- `.display` — serif headline (navy). Use `<br>` to control line breaks.
- `.rule` — the signature gold-tipped divider bar.
- `.meta-inline` (+ `.dot`) — centered "A · B · C" detail row; `.subline` for a
  line under it (e.g. "led by **Name**").
- `.meta-grid` (`.k` / `.v`) — a label→value grid; labels render gold.
- `.section-head` (`.label` / `.dates`) — a group header with a right-aligned range.
- `.item` = `.chip` (navy date/tag badge) + `.item-title` + `.item-desc` — the
  schedule/list row.
- `.callout` (`h2`, `.row`, `.k`) — a soft panel for "how to join" / logistics.
- Sheet chrome: `.sheet`, `.sheet-foot` (`.url` / `.note`).
- Page chrome: `.page`, `.cover` (`.top`, `.lead`, `.brand`, `.cta`), `.pagefoot`
  (`.pg` = page number).

## Recoloring / rebranding

Edit the `:root` block at the top of `theme.css` — `--navy` (primary) and
`--gold` (accent) drive everything; `--serif` / `--sans` swap fonts (keep to
locally-installed families for reproducibility). To add a logo, place an `<img>`
at the top of the `.sheet` or inside `.cover .top` and size it with an inline
`height`. Everything else — spacing, chips, rules — follows automatically.

## Requirements

Headless Chrome, Chromium, or Edge on the machine (for rendering), and `sips`
(macOS, built in) or ImageMagick `magick` for the JPEG step. No network needed.
