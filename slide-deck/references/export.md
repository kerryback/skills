# Exporting a deck to PDF, PNG, or PowerPoint

You export the **rendered** deck, so render first:

```
quarto render <name>.qmd     # produces <name>.html
```

Export is done with **decktape**, which loads the HTML deck in a headless
browser and steps through every slide. It needs Node.js. In Academic Studio,
install decktape from Help → Run Setup… (the opt-in "decktape" program), or
globally with `npm install -g decktape`. If it isn't installed you can also run
it one-off with `npx decktape`.

## PDF (most reliable)

```
decktape reveal "<absolute-file-url>/<name>.html" <name>.pdf
```

The input must be a URL. Build a `file://` URL from the absolute path of the
rendered HTML, for example:

- macOS/Linux: `file:///Users/you/talks/deck/mytalk.html`
- Windows: `file:///C:/Users/you/talks/deck/mytalk.html`

If decktape can't find a browser, point it at an installed Chrome/Chromium with
`--chrome-path`:

```
decktape reveal --chrome-path "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "file:///…/mytalk.html" mytalk.pdf
```

Common `--chrome-path` values:

- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Windows: `C:/Program Files/Google/Chrome/Application/chrome.exe`
- Linux: `/usr/bin/google-chrome` or `/usr/bin/chromium`

Tip: the theme hides non-active slides for on-screen presenting; decktape drives
reveal's own slide navigation, so all slides are captured correctly.

## PNG images (one per slide)

Useful for importing into PowerPoint/Google Slides, or as input to
`tutorbot-builder`:

```
decktape reveal --screenshots --screenshots-directory slides_png \
  "file:///…/mytalk.html" mytalk.pdf
```

decktape still writes the PDF; the per-slide PNGs land in `slides_png/`.

## PowerPoint (.pptx)

There is no clean "editable text" path from a reveal deck to PowerPoint. Choose
by what the user actually needs:

- **They want the deck as slides in PowerPoint (fidelity over editability):**
  export PNGs (above) and place one image per slide, or convert the PDF to PPTX
  in Acrobat/another converter. The result is image-based slides — pixel-perfect
  but not text-editable.
- **They need to edit text and shapes natively in PowerPoint:** don't force this
  route — build the deck with the separate `pptx` skill instead, which produces
  real editable PowerPoint objects.

State the tradeoff plainly and let the user pick.

## Troubleshooting

- Blank or clipped slides in the PDF: confirm the deck renders correctly in a
  browser first; export only ever reflects the rendered `.html`.
- decktape hangs or errors on launch: it can't find a browser — pass
  `--chrome-path` (above).
- Slide overflow in the PDF that isn't visible on screen: the slide is too dense
  — add `{.shrink}` or split it, then re-render and re-export.
