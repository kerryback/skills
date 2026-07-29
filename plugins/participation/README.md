# participation

Score class participation from a photo roster, right after class, while you can
still put names to what was said.

Keep each class in its own folder with the Course Roster PDF you printed from
Esther, and Claude reads every student's name and headshot straight out of it —
nothing to upload. Pick the class, confirm the date, and tap 1–3 for how much
each student spoke and how good it was, with a note where you want one. Save
writes a row per student to `participation.csv` in that class's folder.

Everything runs on your own machine. Nothing is uploaded anywhere, and the app
makes no model calls.

## Install

From the `kerryback-skills` marketplace:

```
/plugin install participation@kerryback-skills
```

Then ask Claude Code to open the participation app, or invoke the skill
directly with `/participation:participation`.

## Using it

Claude launches the app on <http://127.0.0.1:8020> — in Academic Studio when
Studio is running, in your browser otherwise. First launch builds a small Python
environment in `~/.participation`; after that it starts immediately.

On first use Claude asks two things and remembers them in
`~/.participation/.preferences`: where your class folders live, and what your
roster files are. After that, setting up a class is one ask — Claude creates it,
points it at its folder, and reads the roster from that folder.

Extraction is shown for review: names are editable, wrong entries removable,
photos swappable, missing students addable by hand.

After that it's the class picker, the date (today by default), and the grid of
faces.

## Where things are kept

| what | where | why |
| --- | --- | --- |
| preferences | `~/.participation/.preferences` | where your class folders are, what your roster files are |
| courses, rosters, photos | `~/.participation/data` | survives plugin updates, shared across projects |
| evaluations | `participation.csv` in each class folder | yours, alongside the course material |
| Python environment | `~/.participation/venv` | built once on first launch |

The CSV holds a row per student per class meeting. Amount and quality are 1 to
3; a student left unscored records as 0, so a saved class is a complete grid
rather than a set of blanks to interpret later. Re-saving a date replaces that
date's rows instead of duplicating them.

## The roster PDF

Built for the Course Roster report printed from Esther: one student per row,
square thumbnail in the left column, name beside it as "Last, First". Names are
stored the way you'd say them — "Mohammed, Ryan" becomes "Ryan Mohammed".

The layout is read relative to each thumbnail rather than against fixed page
coordinates, so a shifted or scaled roster still works. A different report won't
— and since a class folder holds plenty of other PDFs, anything without a
student-ID column is refused outright rather than importing a few stray figures
over a good roster. Whatever the reason, a failed import leaves the roster you
already had in place.

The student-ID column doubles as a cross-check: if the photo count doesn't match
the number of students the PDF lists, you're told, rather than handed a short
roster that looks complete.

## Requirements

Python 3.11+. Nothing else — the first launch installs what it needs.
