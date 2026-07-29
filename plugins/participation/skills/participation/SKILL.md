---
name: participation
description: >-
  Score class participation quickly against a class roster. Use when an
  instructor wants to "grade participation", "record who spoke today", "open the
  participation app", "set up a course for participation", or asks to turn a
  class list into a scoring screen. Launches a local app
  (http://127.0.0.1:8020) showing each student with 1-3 scores for amount and
  quality, an optional note, and a class date; Save writes a row per student to
  participation.csv in that class's folder. Needs only a list of names, read
  from whatever the instructor has; photos are optional and shown when
  available. Opens inside Academic Studio when it is running, otherwise in a
  browser.
---

# participation

The instructor runs this app on their own machine, right after class, and taps
scores against faces. You set it up, read their roster out of the class folder,
and answer questions about the saved data. The app makes no model calls; nothing
leaves the machine.

Each class has its own folder. The roster file with the photos lives there, and
that is where its `participation.csv` is written, alongside the rest of the
course material. Courses, extracted photos and the app's own database live in
`~/.participation/data` so they survive a plugin update.

## 1. Preferences — do this first, every time

Read `~/.participation/.preferences`. It is JSON:

```json
{
  "courses_root": "/Users/you/Courses",
  "roster_formats": ["registrar photo-roster PDF, one per class folder"]
}
```

- `courses_root` — the folder holding one subfolder per class. Each class folder
  holds that class's roster and its `participation.csv`.
- `roster_formats` — how this instructor's class lists and photos arrive, in
  their own words: a spreadsheet exported from the registrar, a photo-roster
  PDF, a folder of headshots, a list pasted into chat. Whatever it is, record it
  so you don't ask again next term.

If the file is missing, or either key is absent, ask for what's missing and
write it before doing anything else. Ask for both in one turn when both are
missing; don't interrogate them twice.

- For `courses_root`: ask where they keep their class folders. Confirm it
  exists, or offer to create it.
- For `roster_formats`: ask what they have for their classes — a list of names
  is all that's required, and photos are a bonus if they have them. Don't lead
  with a format; ask what they've got and record the answer.

Create `~/.participation` if it isn't there, then write the file. Preserve any
keys you don't recognise. If the instructor later tells you something that
contradicts the file — a new class-folder location, a different roster format —
update it rather than carrying a stale preference.

Read the file, don't guess: it is the record of what this instructor uses.

## 2. Launch

Run the launcher in the background — it starts a long-lived local server.
`<skill-dir>` is the "Base directory for this skill" reported when the skill is
invoked; use that absolute path.

```
python3 "<skill-dir>/scripts/skill_launch.py"
```

The first launch builds a small Python environment in `~/.participation`, so it
takes a little longer. It prints `Open: http://127.0.0.1:8020` and opens the app
in Academic Studio if Studio is running, in the system browser otherwise — you
do not need to open anything yourself. If the port is taken, rerun with
`--port 8021` and use that port throughout.

## 3. Set the class up (once per class)

Creating a class is yours alone — the app has no form for it. The Courses tab
edits what already exists: name, term, folder, roster, delete. So when an
instructor wants a new class, don't send them to the app; do it here.

Work out the class folder: `<courses_root>/<class>`. List `courses_root` to see
what classes exist rather than guessing at a name.

Check whether the course is already in the app — `GET /courses` lists them, or
just ask. If it is new, create it and point it at its own folder:

```
POST http://127.0.0.1:8020/api/courses
     {"name": "MGMT 638", "term": "Fall 2026", "folder": "<class folder>"}
  -> {"id": 1, "name": "MGMT 638"}
```

Then get the roster in. All the app needs is names; photos are optional and can
be added later or not at all. Look in the class folder, and work with whatever
is actually there rather than asking for a particular format.

**Names — the general case.** You read the class list, whatever it is: a
spreadsheet, a CSV, a Word document, a text file, an email they paste in. Parse
it yourself and post the names:

```
POST http://127.0.0.1:8020/api/courses/<id>/roster/names
     {"names": ["Ada Lovelace", "Alan Turing", …]}
  -> {"imported": 35, "total": 35}
```

Names are stored as given, so normalise "Last, First" to how you'd say it before
posting. Duplicates and blanks are dropped. `mode` defaults to `"replace"`; pass
`"append"` to add to an existing roster.

**A photo-roster PDF, if they have one.** This reads names and headshots
together, in one call. A class folder usually holds many PDFs (slides, papers,
handouts), so pick the one whose name says roster rather than the first PDF you
see, and ask if more than one is plausible:

```
POST http://127.0.0.1:8020/api/courses/<id>/roster/from-path
     {"path": "<class folder>/Course Roster.pdf"}
  -> {"imported": 35, "expected": 35, "path": "…"}
```

`imported` is how many students were found; `expected` is how many the PDF's
student-ID column lists. If they differ, say so plainly rather than presenting a
short roster as complete. On failure it returns 400 with `{"error": "…"}` and
leaves any existing roster alone — say what it said, and fall back to names.

**Photos from a folder of images, if they have one.** Match by name; anything
unmatched comes back so you can ask rather than guess:

```
GET  http://127.0.0.1:8020/api/courses/<id>/roster
  -> {"students": [{"id": 1, "name": "Ada Lovelace", "has_photo": false}, …]}

POST http://127.0.0.1:8020/api/courses/<id>/photos
     {"photos": [{"name": "Ada Lovelace", "path": "…/ada.jpg"}, …]}
  -> {"attached": 34, "unmatched": ["Al Turing"], "unreadable": []}
```

Then have them check the roster at `/courses/<id>`: names are editable,
wrong entries removable, photos swappable by clicking a thumbnail, and missing
students addable by hand.

Never block on photos. A names-only roster is a perfectly good roster — the app
shows initials where there's no photo. Offer photos as an improvement if they
mention having them, and move on if they don't.

## 4. Hand off

The instructor picks the class, confirms the date (today by default), taps
scores, and clicks Save. Leave the launcher running while they work; Ctrl-C
stops it.

## What the photo-roster PDF reader handles

Only relevant when the instructor has a photo roster and wants the headshots;
names alone never go through it.

It reads the table layout registrars typically produce: one student per row, a
square thumbnail in the leftmost column, and the name beside it as
"Last, First", wrapping to a second line when long. Names come out the way you
would say them, so "Mohammed, Ryan" becomes "Ryan Mohammed". Layout is measured
relative to each thumbnail rather than against fixed page coordinates, so a
shifted or scaled roster still reads.

A grid-of-headshots roster, or a PDF that is one big scanned image, will not
read. Neither will an unrelated PDF: a file with images but no student-ID column
is refused outright, so pointing at a paper in the same folder can't overwrite a
good roster. When it fails, don't retry variations — take the names from
wherever else they are and offer to attach photos separately.

## What gets saved

One cumulative `participation.csv` in each class folder, a row per student per
class meeting:

```
date,course,student,amount,quality,notes,recorded_at
2026-09-03,MGMT 638,Ada Lovelace,3,2,Pushed back on the beta estimate,…
2026-09-03,MGMT 638,Alan Turing,0,0,,…
```

Amount and quality are 1 (low) to 3 (high); a student left unscored records as
0, so every saved class is a complete grid with no blanks to reinterpret when
totalling the term. Saving a date replaces that course's rows for that date, so
re-saving a class corrects it rather than duplicating it.

For term totals, a breakdown, or a gradebook column, read that CSV and compute
it yourself — the app has no reporting of its own.

## Notes

- Deleting a course on the Courses tab removes it from the app and leaves the
  CSV alone.
- The app warns before leaving a class with unsaved scores, so an unsaved-work
  prompt in the browser is expected, not a bug.
- Photo rosters are protected student records. Keep names out of anything that
  leaves the instructor's machine.
