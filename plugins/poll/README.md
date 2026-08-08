# poll

Put a question to the class and show the answers on the projector.

```
/poll What's the capital of France? Paris, Topeka or Frankfurt
```

That is the whole thing. Claude reads the sentence, works out that it is
multiple choice with three options and that Paris is the right one, and puts it
on the projector with voting open. Students answer from their own phones.

Answers are anonymous. No name field, no sign-in, no roster, and nothing stored
per student — which is what makes a concept check tell you something true.

## Install

From the `kerryback-skills` marketplace:

```
/plugin marketplace add kerryback/skills
/plugin install poll@kerryback-skills
```

## Requirements

Python 3.10+ and `cloudflared`, which is what gives students an https link:

| | |
| --- | --- |
| Windows | `winget install --id Cloudflare.cloudflared` |
| macOS | `brew install cloudflared` |
| no admin rights | ask Claude to install a private copy |

Ask Claude to check the setup first — it reports Python, the app environment,
cloudflared and any problems in a poll file, each with what to run next.

## Three ways in

| | |
| --- | --- |
| `/poll <a question>` | that question, on the projector, now |
| `/poll <a file>` | a poll you had Claude write earlier |
| `/poll` | bring the room up; join link on the projector, nothing loaded |

And before class, in ordinary conversation: "write me a poll on duration for
Thursday" gets you a small JSON file in your course folder, which is what the
second row runs.

```json
{
  "title": "MGMT 638 — Duration and convexity",
  "questions": [
    {"type": "choice", "text": "Two bonds, same maturity. Which has the higher duration?",
     "options": ["The 8% coupon bond", "The 3% coupon bond", "They are equal"],
     "answer": 1},
    {"type": "wordcloud", "text": "One word: what does convexity buy you?"},
    {"type": "scale", "text": "How solid do you feel about duration?",
     "min_label": "Lost", "max_label": "Solid"}
  ]
}
```

"Add one on why the zero has the longest duration, and drop the third option on
question one" is a faster edit than any interface.

## One session per class

Everything appends. A prepared file and a question you type on the spot go into
the same running session, so the question a student provokes in week 6 lands in
the same results file as the deck you planned. Nothing you type discards
answers.

The first `/poll` of a class is the slow one — a few seconds for the server and
the Cloudflare hostname, longer the very first time on a machine. Every one
after it is immediate, because the session stays up and the student link doesn't
change. If you'd rather pay that while students are still settling, type a bare
`/poll` at the top of class.

## Running it

The display opens on the classroom computer. Put it on the projector — it shows
the join link, the room code and a QR until you start.

Space or → moves to the next question, ← goes back, `o` opens and closes voting,
`h` shows or hides results, `r` reveals the answer. The control bar hides itself
so the projector stays clean.

Voting opens with each question. A question that has a right answer shows only a
count while voting is open, and the distribution once you close it. That is on
purpose: a bar chart growing live tells the room what the popular answer is, and
the students who most need to commit to an answer are the ones who follow it.

## Question types

| type | students see | projector shows |
| --- | --- | --- |
| `choice` | tappable options | bar per option, correct one green when revealed |
| `wordcloud` | a text box | words sized by how many said them |
| `scale` | a row of numbers | distribution and the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | options by average position |

Multiple choice can accept several answers with `"multi": true`.

## Afterwards

Save CSV writes a file next to the poll — one row per option, correct answers
flagged, no student data. A session of questions you typed during class lands in
the folder you started from. Or ask Claude how the class did on question 3 and
it reads the results directly.

Nothing is stored between sessions. Stop the app and the answers are gone unless
you saved them.

## What it isn't

One answer per browser, tracked by a random local id, so a student can change
their mind while voting is open. It is not a login. Someone with two browsers
can vote twice — the right trade for anonymity in a classroom, but don't use
these numbers for attendance or grades.
