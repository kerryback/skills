---
name: survey
description: >-
  Put a question to a class and show the answers on the projector. Use when an
  instructor types "/survey", asks to "poll the class", "run a quick concept
  check", "put a question up for students", "make a word cloud of what they
  think", "do a Menti-style poll", or asks to check whether a class understood
  something -- and when they ask you to write a poll for a coming class.
  `/survey <a question>` puts that one question up immediately; `/survey <a
  file>` loads a poll you prepared earlier; "write me a poll for Thursday"
  produces the file. Multiple choice, select-all-that-apply, word clouds,
  confidence scales, numeric estimates and rankings, each drawn live as answers
  arrive. Runs at
  https://poll.kerryback.com, always on, so students join from any device with
  no tunnel and no waiting. Anonymous: no names, no roster, nothing stored per
  student.
---

# survey

Three ways in, and they are the same session underneath:

| | |
| --- | --- |
| `/survey What's the capital of France? Paris, Topeka or Frankfurt` | that question, on the projector, now |
| `/survey class-4-duration.json` | a poll written before class |
| "write me a poll for Thursday" | you write the file; Thursday they load it |

The third is ordinary conversation, not a command. What this skill gives it is
the schema in section 4, so the file you write actually loads.

`/survey` works out the question type from how the sentence is phrased. When the
instructor would rather say than be guessed at, there is a command per type —
`/survey:word-cloud`, `/survey:scale`, `/survey:number`, `/survey:rank`,
`/survey:choice`, `/survey:select-all` — and each carries the same instruction:
the type is settled, don't re-infer it from the wording.

## What to do with the argument

1. Empty → `start`. Bring the room up with nothing loaded, so the welcome screen
   with the QR is on the projector before it is needed.
2. Names a file → `file`. It names a file if it ends in `.json`, contains a path
   separator, or matches something on disk. If it looks like a file but isn't
   there, say so and list the `.json` files in the folder — don't quietly turn
   `clsss-4.json` into a question about a filename.
3. Anything else → `ask`. It is a question; write it out and put it up.

You are in front of a class. Don't ask a clarifying question, don't confirm
first, don't think out loud. Make the call and push. Reading it wrong costs one
retyped `/survey`, which is cheaper than any confirmation would have been.

## 0. One-time setup

The app is already running at <https://poll.kerryback.com>. The only thing a
machine needs is the API token, in `~/.survey/.env`:

```
SURVEY_TOKEN=...
```

Check it with:

```
python3 "<skill-dir>/scripts/survey.py" check [<poll file>]
```

That reports whether the app is reachable, whether the token works, and — if you
name one — whether a poll file loads. On Windows use `py -3`, not `python3`,
which there is usually a Microsoft Store stub. There is nothing to install: the
script imports only the standard library.

## 1. `/survey <a question>`

Read the sentence into one question and pipe it in as JSON:

```
python3 "<skill-dir>/scripts/survey.py" ask <<'JSON'
{"type": "choice", "text": "What's the capital of France?",
 "options": ["Paris", "Topeka", "Frankfurt"], "answer": 0}
JSON
```

The heredoc rather than an argument, because questions have apostrophes in them.

Reading the sentence:

- Options after the question, comma-separated with a trailing "or", are the
  options. Capitalise them; they are going on a projector.
- Type follows the phrasing. Options listed or an either/or → `choice`. "Short
  answer", "in a word", "what comes to mind" → `wordcloud`. "How confident", "1
  to 5", "how solid do you feel" → `scale`. "Guess", "estimate", "what percent",
  "how many" → `number`. "Order these", "rank" → `rank`. "Select all that apply",
  "which of these", "tick everything that" → `multi`. Unless a `/survey:<type>` command already
  settled it, in which case use that type and don't second-guess the wording.
- Leave `answer` out unless the instructor says the question has a right one.
  Most questions here are perception checks -- what students think, and how
  solid they feel -- and those have no right answer to mark. A marked answer is
  not cosmetic: it hides the distribution while voting is open and adds a
  Reveal, so marking one on an opinion question changes how it behaves in the
  room for the worse. Where there genuinely is a right answer, mark it and say
  in your reply which one.

A question asked this way goes up immediately and joins the same session as
everything else, so it appears in the menu alongside the prepared questions and
can be returned to later.

Then report in one line: the question, its type, which answer you marked if any,
and — only when the session just started — the student link and room code. Don't
reprint the link for every question; it hasn't changed.

## 2. `/survey <a file>`

```
python3 "<skill-dir>/scripts/survey.py" file <path>
```

The questions append and the pointer does not move, so loading a file at the top
of class leaves the welcome screen up, and loading one mid-class doesn't yank the
projector off the question the room is answering. Tell the instructor how many
questions arrived and that the menu is on `m`.

Everything appends, which is the rule worth knowing: a prepared file and a
question typed on the spot go into the same growing session. Nothing the
instructor types discards answers — only `stop` or `reset`, or asking outright.

## 3. Running it

The instructor's job, not yours. It is all on the display page, and the keyboard
beats the buttons:

| key | |
| --- | --- |
| m | the question menu — every prepared question, jump to any of them |
| 1–9 | with the menu up, the question with that number |
| space or → | next question |
| ← | back |
| o | open or close voting |
| h | show or hide results |
| r | reveal the answer |
| j | put the welcome screen back up, and take it down again |
| Esc | close the menu |

The menu is the main way to run a prepared class: the questions are a set to
reach for in whatever order the discussion takes, not a queue to walk front to
back. It shows each question's type, how many have answered it, and which one is
up. The control bar hides itself and comes back when the mouse moves, so the
projector stays clean.

`j` is for the student who walked in late. It puts the QR, link and room code
back over whatever question is live, says which question that is so they know
there is something to answer, and leaves voting open underneath — they can join
and answer the question the room is already on. Moving to another question takes
it down on its own.

Voting opens automatically with each question. A question with a right answer
shows only a count while voting is open — closing voting or pressing `h` shows
the distribution. That withholding is deliberate: a bar chart growing in real
time tells the room what the popular answer is, and quiet students follow it.
Opinion questions have nothing to bias, so they draw live.

Students see their own question and their own answer, never the tally. The
projector is where the room looks together.

## 4. Writing a poll before class

A poll file is JSON. Put it in the course folder, named for the class it belongs
to — `class-4-duration.json` — so it can be run again next term.

```json
{
  "title": "MGMT 638 — Duration and convexity",
  "questions": [
    {"type": "scale", "text": "How solid do you feel about duration right now?",
     "min": 1, "max": 5, "min_label": "Lost", "max_label": "Solid"},

    {"type": "multi", "text": "Which of these still feel shaky? Select all that apply.",
     "options": ["Duration", "Convexity", "Immunization", "None of these"]},

    {"type": "wordcloud", "text": "Short answer: what does convexity buy you?"},

    {"type": "rank", "text": "Order these from least to most interest-rate risk",
     "options": ["3-month T-bills", "5-year notes", "30-year Treasuries"]},

    {"type": "number", "text": "Guess the current 10-year Treasury yield, in percent",
     "unit": "%"},

    {"type": "choice", "text": "Two bonds, same maturity. Which has the higher duration?",
     "options": ["The 8% coupon bond", "The 3% coupon bond", "They are equal"]}
  ]
}
```

No `answer` anywhere, which is the normal case: these ask what students think
and how solid they feel, and there is nothing to be right about. Add one only
where the question genuinely has a right answer -- a 0-based index into
`options`, a list of them for `multi`, or a plain number for `number`. Doing so
withholds the distribution while voting is open and adds a Reveal, which is what
you want for a concept check and wrong for everything else here.

`multi` is select all that apply. Its bars are percentages of the people who
answered rather than of the ticks, so they add to more than 100% -- which is the
reading that means something: "two-thirds of the room is shaky on convexity".

Because any question can be reached from the menu at any time, a prepared file
can hold more than one class will use — questions for wherever the discussion
goes, not a fixed running order.

Validate it before class rather than in front of it — every problem is reported
at once, with question numbers:

```
python3 "<skill-dir>/scripts/survey.py" check <file>
```

### Questions worth asking

- One idea per question. If a student can get it right for the wrong reason,
  split it.
- Wrong options should be real misconceptions, not filler. "They are equal"
  earns its place because students genuinely believe it; a joke option teaches
  nothing and wastes the distribution.
- Keep options short. They are read from the back of a room, off a projector.
- Two to four options for a concept check. Ten is unreadable and the app refuses
  more than ten anyway.
- A word cloud wants a short answer, and the question should say so — "Short
  answer:" — or you get sentences and the cloud turns to mush. Don't demand a
  single word: two or three stay together as one entry, so "interest rate risk"
  lands whole rather than as a bare "risk", and nobody has to squeeze an idea
  into a word that doesn't fit it.
- Ask a scale question before deciding whether to move on. It is the cheapest
  way to find out you have lost the room.

## 5. Afterwards

```
python3 "<skill-dir>/scripts/survey.py" status     # live state + every tally
python3 "<skill-dir>/scripts/survey.py" results    # download the CSV
python3 "<skill-dir>/scripts/survey.py" stop       # end the session
python3 "<skill-dir>/scripts/survey.py" reset      # empty it, keep the room open
```

`status` is how you answer "how did they do on question 3" without opening
anything. `results` writes a CSV into the current folder — one row per option,
correct answers flagged, nothing identifying a student. It is optional; skip it
if the answers were only for the room.

`stop` ends the class: the room code stops working and the projector page says
so. Leaving a session running between classes is fine too — the next `file` or
`ask` appends to it, so `stop` first if you want a clean start and a new code.

## Question types

| type | students see | projector shows |
| --- | --- | --- |
| `choice` | tappable options, A/B/C | bar per option, as % of the people who answered |
| `multi` | the same, tick any number, then Submit | bar per option, as % of the people who answered, so they add to more than 100% |
| `wordcloud` | a text box | answers sized by how many said them |
| `scale` | a row of numbers | distribution plus the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | options by average position |

## Notes

- Nothing is stored. The session lives in the server's memory, so a redeploy of
  the app loses the class in progress. Don't push to `kerryback/survey` on a
  class day, and pull the CSV before `stop` if you want it.
- The room code is fresh for each session and shown on the welcome screen. It
  keeps a forwarded link from letting outsiders in; it is not in the URL.
- The QR carries the code, so a student who scans it only has to tap Join. One
  who types the address in enters the four digits.
- One answer per browser, kept by a random local id. A student can change their
  mind while voting is open. It is not a login and not proof of identity — a
  determined student with two browsers can vote twice. That is the right trade
  for anonymity in a classroom; don't present the numbers as an audit.
- Word clouds keep an answer of up to three words whole and only break longer
  ones into their content words, drop common English filler from the ends, and
  collapse a repeated word, so one enthusiastic student typing "risk risk risk"
  lands on the same entry as everyone who wrote "risk".
- The app's source and HTTP API are at <https://github.com/kerryback/survey>.
