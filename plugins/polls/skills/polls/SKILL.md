---
name: polls
description: >-
  Run live in-class polls with the results on the projector. Use when an
  instructor wants to "poll the class", "run a quick concept check", "put a
  question up for students", "make a word cloud of what they think", "do a
  Menti-style poll", or asks to check whether a class understood something.
  Claude writes the questions; the app runs them. Supports multiple choice,
  word clouds, confidence scales, numeric estimates and rankings, each drawn
  live as answers arrive. Launches a local app (http://127.0.0.1:8050) and
  publishes it over a Cloudflare Quick Tunnel so students answer from their own
  devices. Anonymous: no names, no roster, nothing stored per student.
---

# polls

The instructor asks for a poll; you write it; the app runs it. That division is
the point of this skill. Building questions through a web form is the part
instructors dislike, and you can write six good ones from a lecture outline
faster than anyone can click through a builder.

Answers are anonymous by design. There is no name field and no sign-in, which is
what makes a concept check worth running — students answer what they actually
think rather than what won't embarrass them.

## 0. First run on a new machine

```
python3 "<skill-dir>/scripts/skill_launch.py" --check
```

Reports on Python, the app environment, and cloudflared, and validates a poll
file if you pass `--poll`. Walk the instructor through anything it flags. On
Windows use `py -3`, not `python3`, which there is usually a Microsoft Store
stub.

`cloudflared` is required — it is what gives students an https link. Install it
with `winget install --id Cloudflare.cloudflared` on Windows or
`brew install cloudflared` on a Mac, or, with no admin rights, rerun the
launcher with `--install-cloudflared` to fetch a private copy.

## 1. Write the poll

A poll is a JSON file. Put it in the course folder, named for the class it
belongs to — `class-4-duration-polls.json` — so it can be reused next term.

```json
{
  "title": "MGMT 638 — Duration and convexity",
  "questions": [
    {"type": "choice", "text": "Two bonds, same maturity. Which has the higher duration?",
     "options": ["The 8% coupon bond", "The 3% coupon bond", "They are equal"],
     "answer": 1},

    {"type": "wordcloud", "text": "One word: what does convexity buy you?"},

    {"type": "scale", "text": "How solid do you feel about duration right now?",
     "min": 1, "max": 5, "min_label": "Lost", "max_label": "Solid"},

    {"type": "number", "text": "Guess the current 10-year Treasury yield, in percent",
     "answer": 4.3, "unit": "%"},

    {"type": "rank", "text": "Order these from least to most interest-rate risk",
     "options": ["3-month T-bills", "5-year notes", "30-year Treasuries"]},

    {"type": "choice", "text": "Which of these reduce duration? Pick all that apply.",
     "options": ["Higher coupon", "Longer maturity", "Higher yield"],
     "multi": true, "answer": [0, 2]}
  ]
}
```

`answer` is a 0-based index into `options`, a list of them for `multi`, or a
plain number for `number`. It is optional, and including it changes what the
question does: a question with an answer gets a Reveal control, and its results
stay hidden while voting is open.

Validate before class rather than in front of it:

```
python3 "<skill-dir>/scripts/skill_launch.py" --check --poll <file>
```

Every problem is reported at once, with question numbers.

### Writing questions that are worth asking

- One idea per question. If a student can get it right for the wrong reason,
  split it.
- Wrong options should be real misconceptions, not filler. "They are equal"
  earns its place because students genuinely believe it; a joke option teaches
  nothing and wastes the distribution.
- Keep options short. They are read from the back of a room, off a projector.
- Two to four options for a concept check. Ten is unreadable and the app
  refuses more than ten anyway.
- A word cloud wants one word. Say so in the question — "One word:" — or you
  get sentences, and the cloud turns to mush.
- Ask a scale question before deciding whether to move on. It is the cheapest
  way to find out you have lost the room.

## 2. Launch

```
python3 "<skill-dir>/scripts/skill_launch.py" --poll <file>
```

The display page opens on the classroom computer; put it on the projector. It
prints the student link, the room code, and the display URL. Leave it running
for the class; Ctrl-C stops the server and the tunnel together.

To load a different poll without restarting:

```
POST http://127.0.0.1:8050/api/deck?key=<display key>
     {"path": "<poll file>"}
  -> {"title": "…", "questions": 6, "types": ["choice", …]}
```

A file with problems comes back as 400 with every problem listed, and the poll
already loaded is left alone — a typo mid-class cannot wipe out the questions
that were working.

## 3. Running it

This is the instructor's, not yours. Everything is on the display page, and the
keyboard is faster than the buttons:

| key | |
| --- | --- |
| space or → | next question |
| ← | back |
| o | open or close voting |
| h | show or hide results |
| r | reveal the answer |

The control bar hides itself and comes back when the mouse moves, so the
projector stays clean.

Voting opens automatically with each question. A question with a right answer
shows only a count while voting is open — closing voting or pressing `h` shows
the distribution. That withholding is deliberate: a bar chart growing in real
time tells the room what the popular answer is, and quiet students follow it.
Opinion questions have nothing to bias, so they draw live.

Students see their own question and their own answer, never the tally. The
projector is where the room looks together.

## 4. Afterwards

Save CSV on the display, or:

```
POST http://127.0.0.1:8050/api/save?key=<display key>
  -> {"path": "…/class-4-duration-polls-results-2026-08-02.csv"}
```

It lands next to the poll file, one row per option, with correct answers
flagged. Nothing is written until asked, and nothing identifies a student.

`GET /api/state?key=…` returns the live state plus every question's tally, which
is how you answer "how did they do on question 3" without reading the CSV.

## Question types

| type | students see | projector shows |
| --- | --- | --- |
| `choice` | tappable options, A/B/C | bar per option, correct one green when revealed |
| `wordcloud` | a text box | words sized by how many said them |
| `scale` | a row of numbers | distribution plus the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | options by average position |

## Notes

- One answer per browser, kept by a random local id. A student can change their
  mind while voting is open. It is not a login and it is not proof of identity —
  a determined student with two browsers can vote twice. That is the right
  trade for anonymity in a classroom; don't present the numbers as an audit.
- The room code keeps a forwarded link from letting outsiders in. It is on the
  screen, not in the URL.
- Nothing is stored between launches. Stop the app and the answers are gone
  unless the CSV was saved.
- Word clouds drop common English filler and count a word once per student, so
  one enthusiastic student typing "risk risk risk" doesn't distort the picture.
