---
name: poll
description: >-
  Put a question to a class and show the answers on the projector. Use when an
  instructor types "/poll", asks to "poll the class", "run a quick concept
  check", "put a question up for students", "make a word cloud of what they
  think", "do a Menti-style poll", or asks to check whether a class understood
  something -- and when they ask you to write a poll for a coming class.
  `/poll <a question>` puts that one question up immediately; `/poll <a file>`
  runs a poll you prepared earlier; "write me a poll for Thursday" produces the
  file. Multiple choice, word clouds, confidence scales, numeric estimates and
  rankings, each drawn live as answers arrive. Runs a local app (127.0.0.1:8050)
  published over a Cloudflare Quick Tunnel so students answer from their own
  devices. Anonymous: no names, no roster, nothing stored per student.
---

# poll

Three ways in, and they are the same session underneath:

| | |
| --- | --- |
| `/poll What's the capital of France? Paris, Topeka or Frankfurt` | that question, on the projector, now |
| `/poll class-4-duration.json` | a poll written before class |
| "write me a poll for Thursday" | you write the file; Thursday they run it |

The third is ordinary conversation, not a command. What this skill gives it is
the schema in section 4, so the file you write actually loads.

## What to do with the argument

1. Empty → `start`. Bring the room up with nothing loaded, so the join link is
   on the projector before it is needed.
2. Names a file → `file`. It names a file if it ends in `.json`, contains a path
   separator, or matches something on disk. If it looks like a file but isn't
   there, say so and list the `.json` files in the folder — don't quietly turn
   `clsss-4.json` into a question about a filename.
3. Anything else → `ask`. It is a question; write it out and put it up.

You are in front of a class. Don't ask a clarifying question, don't confirm
first, don't think out loud. Make the call and push. Reading it wrong costs one
retyped `/poll`, which is cheaper than any confirmation would have been.

## 0. First run on a new machine

```
python3 "<skill-dir>/scripts/poll.py" check [<poll file>]
```

Reports on Python, the app environment and cloudflared, and validates a poll
file if you name one. Walk the instructor through anything it flags. On Windows
use `py -3`, not `python3`, which there is usually a Microsoft Store stub.

`cloudflared` is required — it is what gives students an https link. Install it
with `winget install --id Cloudflare.cloudflared` on Windows or
`brew install cloudflared` on a Mac, or, with no admin rights,
`python3 "<skill-dir>/scripts/skill_launch.py" --install-cloudflared` for a
private copy under `~/.poll/bin`.

## 1. `/poll <a question>`

Read the sentence into one question and pipe it in as JSON:

```
python3 "<skill-dir>/scripts/poll.py" ask <<'JSON'
{"type": "choice", "text": "What's the capital of France?",
 "options": ["Paris", "Topeka", "Frankfurt"], "answer": 0}
JSON
```

The heredoc rather than an argument, because questions have apostrophes in them.

Reading the sentence:

- Options after the question, comma-separated with a trailing "or", are the
  options. Capitalise them; they are going on a projector.
- Type follows the phrasing. Options listed or an either/or → `choice`. "One
  word", "in a word", "what comes to mind" → `wordcloud`. "How confident", "1
  to 5", "how solid do you feel" → `scale`. "Guess", "estimate", "what percent",
  "how many" → `number`. "Order these", "rank" → `rank`. "Pick all that apply" →
  `choice` with `"multi": true`.
- Mark `answer` when the question has a right answer. Paris is Paris. This is
  not cosmetic: a marked answer hides the distribution while voting is open and
  adds a Reveal, so getting it wrong changes how the question behaves in the
  room. Say in your reply which one you marked, and drop it if told to.

Then report in one line: the question, its type, which answer you marked if any,
and — only when the session just started — the student link and room code. Don't
reprint the link for every question; it hasn't changed.

## 2. `/poll <a file>`

```
python3 "<skill-dir>/scripts/poll.py" file <path>
```

The questions append and the pointer does not move, so loading a file at the top
of class leaves the join screen up, and loading one mid-class doesn't yank the
projector off the question the room is answering. Tell the instructor how many
questions arrived and to press space when ready.

Everything appends, which is the rule worth knowing: a prepared file and a
question typed on the spot go into the same growing session, so an impromptu
question in week 6 lands in the same CSV as the deck you planned. Nothing the
instructor types discards answers — only `stop`, or asking outright.

## 3. Running it

The instructor's job, not yours. It is all on the display page, and the keyboard
beats the buttons:

| key | |
| --- | --- |
| space or → | next question |
| ← | back |
| o | open or close voting |
| h | show or hide results |
| r | reveal the answer |
| j | put the join screen back up, and take it down again |

The control bar hides itself and comes back when the mouse moves, so the
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
plain number for `number`. It is optional, and including it is what makes a
question a concept check rather than an opinion poll.

Validate it before class rather than in front of it — every problem is reported
at once, with question numbers:

```
python3 "<skill-dir>/scripts/poll.py" check <file>
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
- A word cloud wants one word. Say so in the question — "One word:" — or you get
  sentences and the cloud turns to mush.
- Ask a scale question before deciding whether to move on. It is the cheapest
  way to find out you have lost the room.

## 5. Afterwards

```
python3 "<skill-dir>/scripts/poll.py" results   # write the CSV
python3 "<skill-dir>/scripts/poll.py" status    # live state + every tally
python3 "<skill-dir>/scripts/poll.py" stop      # end the session
```

The CSV lands next to the poll file, or in the folder the session started from
if every question was typed during class. One row per option, correct answers
flagged, nothing identifying a student. `status` is how you answer "how did they
do on question 3" without opening it.

## Question types

| type | students see | projector shows |
| --- | --- | --- |
| `choice` | tappable options, A/B/C | bar per option, correct one green when revealed |
| `wordcloud` | a text box | words sized by how many said them |
| `scale` | a row of numbers | distribution plus the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | options by average position |

## Notes

- The first `/poll` of a class pays for the cold start — a few seconds for the
  server and the Cloudflare hostname, and a minute or two the very first time on
  a machine while the app environment builds. Every one after it is immediate,
  because the session outlives the question. That is the whole reason `~/.poll/
  session.json` exists.
- If port 8050 is taken, pass `--port 8051` before the subcommand.
- One answer per browser, kept by a random local id. A student can change their
  mind while voting is open. It is not a login and not proof of identity — a
  determined student with two browsers can vote twice. That is the right trade
  for anonymity in a classroom; don't present the numbers as an audit.
- The room code keeps a forwarded link from letting outsiders in. It is on the
  screen, not in the URL.
- Nothing is stored between sessions. Stop the app and the answers are gone
  unless the CSV was saved.
- Word clouds drop common English filler and count a word once per student, so
  one enthusiastic student typing "risk risk risk" doesn't distort the picture.
- A fixed room code, for a room you poll every week, goes in
  `~/.poll/config.json` as `{"code": "4271"}`.
