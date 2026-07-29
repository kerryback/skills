---
name: participation
description: >-
  Score class participation quickly from a photo roster. Use when an instructor
  wants to "grade participation", "record who spoke today", "open the
  participation app", "set up a course for participation", or asks to turn a
  class roster with photos into a scoring screen. Launches a local app
  (http://127.0.0.1:8020) showing every student's name and headshot with 1-3
  scores for amount and quality, an optional note, and a class date; Save writes
  a row per student to participation.csv in that class's folder. Reads the
  roster straight out of the class folder — nothing is uploaded. Opens inside
  Academic Studio when it is running, otherwise in a browser.
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
  "roster_formats": ["PDF printed from a Rice Esther page"]
}
```

- `courses_root` — the folder holding one subfolder per class. Each class folder
  holds that class's roster file and its `participation.csv`.
- `roster_formats` — what the instructor's roster-with-photos files actually
  are, in their own words.

If the file is missing, or either key is absent, ask for what's missing and
write it before doing anything else. Ask for both in one turn when both are
missing; don't interrogate them twice.

- For `courses_root`: ask where they keep their class folders. Confirm it
  exists, or offer to create it.
- For `roster_formats`: tell them the expected file is a PDF printed from a
  Rice Esther page, and that other formats can be used too — then ask what they
  will actually be using and record their answer. Don't assume Esther just
  because it's the default.

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

Work out the class folder: `<courses_root>/<class>`. List `courses_root` to see
what classes exist rather than guessing at a name.

Check whether the course is already in the app — `GET /admin` lists them, or
just ask. If it is new, create it and point it at its own folder:

```
POST http://127.0.0.1:8020/api/courses
     {"name": "MGMT 638", "term": "Fall 2026", "folder": "<class folder>"}
  -> {"id": 1, "name": "MGMT 638"}
```

Then find the roster file in that folder and read it in — no upload, no drag and
drop. A class folder usually holds many PDFs (slides, papers, handouts), so pick
the one whose name says roster rather than the first PDF you see, and ask if
more than one is plausible:

```
POST http://127.0.0.1:8020/api/courses/<id>/roster/from-path
     {"path": "<class folder>/Course Roster.pdf"}
  -> {"imported": 35, "expected": 35, "path": "…"}
```

`mode` defaults to `"replace"`; pass `"append"` to add to an existing roster.

Report the result honestly:

- `imported` is how many students were found; `expected` is how many the PDF's
  student-ID column lists. If they differ, say so plainly and send them to the
  roster list to fix it — do not present a short roster as complete.
- On an error the call returns 400 with `{"error": "…"}` and leaves any existing
  roster untouched. Say what it said.

Then have them check the roster at `/admin/courses/<id>`: names are editable,
wrong entries removable, photos swappable by clicking a thumbnail, and missing
students addable by hand.

## 4. Hand off

The instructor picks the class, confirms the date (today by default), taps
scores, and clicks Save. Leave the launcher running while they work; Ctrl-C
stops it.

## The roster file

The reader targets the Course Roster report printed from Esther: one student per
table row, square thumbnail in the leftmost column, name beside it as
"Last, First", wrapping to a second line when long. Names are stored the way you
would say them, so "Mohammed, Ryan" becomes "Ryan Mohammed".

Layout is measured relative to each thumbnail rather than against fixed page
coordinates, so a shifted or scaled roster still reads. A different report, or a
PDF that is one big scanned image, will not — the import stops, says so, and
leaves any existing roster alone.

If `roster_formats` says the instructor uses something else, be straight with
them: the built-in reader only handles the Esther PDF today. Offer to add the
students by hand, or to look at a sample of their format and extend the reader.
Don't quietly try it and let it fail.

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

- Deleting a course in the admin panel removes it from the app and leaves the
  CSV alone.
- The app warns before leaving a class with unsaved scores, so an unsaved-work
  prompt in the browser is expected, not a bug.
- Photo rosters are protected student records. Keep names out of anything that
  leaves the instructor's machine.
