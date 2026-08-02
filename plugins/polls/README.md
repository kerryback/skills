# polls

Live in-class polls, with the results on the projector.

You describe the questions — or point Claude at the lecture you're about to give
— and Claude writes the poll. The app runs it: multiple choice, word clouds,
confidence scales, numeric estimates and rankings, each drawn live as answers
come in. Students answer from their own phones or laptops.

Answers are anonymous. No name field, no sign-in, no roster, and nothing stored
per student — which is what makes a concept check tell you something true.

## Install

From the `kerryback-skills` marketplace:

```
/plugin marketplace add kerryback/skills
/plugin install polls@kerryback-skills
```

Then ask Claude for a poll, or invoke the skill with `/polls:polls`.

## Requirements

Python 3.10+ and `cloudflared`, which is what gives students an https link:

| | |
| --- | --- |
| Windows | `winget install --id Cloudflare.cloudflared` |
| macOS | `brew install cloudflared` |
| no admin rights | ask Claude to launch with `--install-cloudflared` |

Ask Claude to check the setup first — it reports Python, the app environment,
cloudflared, and any problems in a poll file, each with what to run next.

## The idea

The part of Menti and its relatives that works is the display. The part that
doesn't is building the questions through a web form. So this keeps the first
and throws away the second: the questions are a small JSON file that Claude
writes, keeps in your course folder, and can rework in a sentence.

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

## Running a class

Claude launches it and the display opens on the classroom computer. Put it on
the projector — it shows the join link, the room code and a QR until you start.

Space or → moves to the next question, ← goes back, `o` opens and closes voting,
`h` shows or hides results, `r` reveals the answer. The control bar hides itself
so the projector stays clean.

Voting opens with each question. A question that has a right answer shows only
a count while voting is open, and the distribution once you close it. That is on
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
flagged, no student data. Or ask Claude how the class did on question 3 and it
reads the results directly.

Nothing is stored between launches. Stop the app and the answers are gone unless
you saved them.

## What it isn't

One answer per browser, tracked by a random local id, so a student can change
their mind while voting is open. It is not a login. Someone with two browsers
can vote twice — the right trade for anonymity in a classroom, but don't use
these numbers for attendance or grades.
