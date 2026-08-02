# Structural overview pages

A standalone HTML page that lists a deck's sections and slides with a
one-sentence description each, plus the problems worth acting on. It is a
working aid for the author, not a deliverable for an audience — it answers
"what is actually in this deck, and where is it going wrong?"

## When to offer one

Offer, don't assume. Good moments:

- The deck passes roughly 30 slides and the author starts asking where things
  are, or moving material between decks.
- After a restructuring round — sections merged, a deck folded into another,
  a block of slides moved.
- The author says something like "I'm trying to get a handle on the
  organization", or asks what is in a deck they haven't opened in a while.
- Across a multi-deck course or series, when material may be duplicated between
  decks.

Don't offer after a small edit, and don't regenerate unprompted. The page goes
stale the moment the deck changes, so it is worth making only when someone is
about to make decisions from it.

## Before writing the page: measure

Two passes over the deck. Both matter — the second is what makes the page more
useful than reading the `.qmd`.

**1. Structure.** Walk the `.qmd` and collect, for each `##` heading: its line
number, its title, and the first line or two of real content (skip `:::`
fences, `<style>`/`<script>`, code fences, table pipes, and image directives).
That is enough to write each description without reading the whole file.

**2. Overflow.** Render the deck, serve it over HTTP (reveal decks do not run
from `file://`), and measure every slide against the canvas height in the
browser:

```js
document.querySelectorAll('.reveal .slides > section').forEach((s, i) => {
  const prev = s.style.display;
  s.style.display = 'block';          // sections are hidden until shown
  const h = s.scrollHeight;
  s.style.display = prev;
  // compare h against the deck's height (1080 for this theme)
});
```

Slides that fit still report a small constant above the canvas height —
establish that baseline from the majority value and treat anything near it as
clean. Report only the real outliers, with how far over each one is. This
catches overflow that reading the source never would, and it distinguishes a
slide needing a trim from one needing a split.

Note that `.shrink` only fixes *vertical* overflow. A slide whose problem is
horizontal — code blocks or long URLs inside a multi-card grid, which do not
wrap — needs a different layout, usually full-width. If a slide already carries
`.shrink` and still overflows, say so; that tells the author trimming or
splitting is the only option left.

## Page structure

Plain HTML with an inline `<style>` block, self-contained, no external assets.
Theme it for light and dark with `prefers-color-scheme`.

1. **Title and subtitle** — deck name, source path, slide count.
2. **Stat strip** — slides, sections, and whatever else is live for this deck:
   live demos, slides added this round, slides overflowing.
3. **Arc line** — the deck's spine in a few words
   (`modes → connectors → code execution → …`). One line; it exposes ordering
   problems faster than the slide list does.
4. **One block per section** — a header carrying the section name, slide count,
   and any tag that applies (`no divider`, `folded in`). Then the slides as a
   list: line number in a monospace left column, title, and a one-sentence
   description underneath.
5. **Flags** — the part with the most value. See below.

Mark slides inline where it helps scanning: a badge for new or moved slides, a
badge for overflow with the pixel count, a marker on live demos or exercises.
The author should be able to see the problems in context, not only in a summary.

## Writing the descriptions

One sentence, describing what the slide *does*, not restating its title.
"Provider share by spend versus breadth of usage" beats "a table about adoption".
Use the deck's own vocabulary. If a slide is a diagram or screenshot with no
prose, say what it shows.

## The flags section

This is the reason to build the page. Each flag is a heading, a short
paragraph, and — where it helps — a table. Rank them: the decision worth making
goes first, the nits last. Things worth flagging:

- **Duplication across decks.** Same titles, same content, in two files. Give
  the side-by-side list; it is usually the most consequential thing on the page.
- **Slides that overflow**, with pixel counts and which are already `.shrink`.
- **Agenda drift.** An agenda or "today's session" slide promising sections that
  no longer exist, or omitting ones that do.
- **Orphans.** Untitled slides (a bare `##`), slides outside any section,
  references to files or sections that were deleted.
- **Section balance.** One section carrying a third of the deck usually wants
  splitting; a two-slide section may want folding.
- **Consequences of recent cuts.** Material that quietly disappeared from the
  whole course, or that is now referenced but never introduced.

Be specific and verifiable — file, line, count. A flag the author cannot check
is noise.

## Practical notes

- Write it next to the deck, named for it (`<deck>-outline.html`), and open it.
- Say in the footer that line numbers reflect the file at generation time and
  drift with editing.
- Leave it untracked by default and say so. It is a generated view, stale after
  the next edit; offer to add it to `.gitignore` rather than committing it.
- Regenerating is cheap. Offer again after the next round of structural changes.
