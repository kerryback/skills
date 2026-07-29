# participation

Record class participation against your class roster.

Ask Claude to open it and your class comes up as a grid: a 1–3 score for how
much each student spoke, another for quality, and a note where you want one.
Saving writes a row per student to `participation.csv` in that class's folder.

All it needs is a list of names. Photos are optional — where you have them
students show as faces, and where you don't, as initials.

Everything runs on your own machine. Nothing is uploaded, and the app makes no
model calls.

## Install

From the `kerryback-skills` marketplace:

```
/plugin marketplace add kerryback/skills
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
class lists look like. Setting up a class is then one ask — Claude reads your
list, whatever form it's in, and builds the roster.

The roster is shown for review: names are editable, wrong entries removable,
photos swappable, missing students addable by hand.

## Getting the roster in

Claude does the reading, so the format is whatever you already have:

| you have | what happens |
| --- | --- |
| a spreadsheet, CSV, text file, or a list you paste in | Claude parses it and posts the names |
| a photo roster PDF | names and headshots are read together in one pass |
| a folder of headshots | matched to students by name; anything unmatched is reported, not guessed |
| names only | perfectly fine — students show as initials |

The photo-roster reader handles the table layout registrars typically produce:
one student per row, thumbnail in the left column, name beside it. It reads that
relative to each thumbnail rather than against fixed page coordinates, so a
shifted or scaled roster still works. A grid-of-headshots roster or a scanned
image won't read — and since a class folder holds plenty of other PDFs, a file
with images but no student-ID column is refused outright rather than importing
stray figures over a good roster. A failed import always leaves the roster you
already had in place.

## Where things are kept

| what | where | why |
| --- | --- | --- |
| preferences | `~/.participation/.preferences` | where your class folders are, what your class lists look like |
| courses, rosters, photos | `~/.participation/data` | survives plugin updates, shared across projects |
| evaluations | `participation.csv` in each class folder | yours, alongside the course material |
| Python environment | `~/.participation/venv` | built once on first launch |

The CSV holds a row per student per class meeting. Amount and quality are 1 to
3; a student left unscored records as 0, so a saved class is a complete grid
rather than a set of blanks to interpret later. Re-saving a date replaces that
date's rows instead of duplicating them.

## Requirements

Python 3.11+, and a list of your students' names. Nothing else — the first
launch installs what it needs.
