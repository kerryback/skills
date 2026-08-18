# survey

Put a question to the class and show the answers on the projector.

```
/survey What's the capital of France? Paris, Topeka or Frankfurt
```

That is the whole thing. Claude reads the sentence, works out that it is
multiple choice with three options and that Paris is the right one, and puts it
on the projector with voting open. Students answer from their own phones at
<https://poll.kerryback.com>.

Answers are anonymous. No name field, no sign-in, no roster, and nothing stored
per student — which is what makes a concept check tell you something true.

## Install

From the `kerryback` marketplace:

```
/plugin marketplace add kerryback/skills
/plugin install survey@kerryback
```

## Requirements

Python 3.9+ and the API token in `~/.survey/.env`:

```
SURVEY_TOKEN=...
```

Nothing else. The app is already running at a fixed address, and the script that
talks to it imports only the standard library — no install, no virtualenv, no
tunnel, and no waiting at the start of class. Ask Claude to check the setup and
it reports whether the app is reachable, whether the token works, and whether a
poll file loads.

## Three ways in

| | |
| --- | --- |
| `/survey <a question>` | that question, on the projector, now |
| `/survey <a file>` | a poll you had Claude write earlier |
| `/survey` | bring the room up; QR and join code on the projector, nothing loaded |

"Write me a poll for Thursday" is the fourth, and it is ordinary conversation
rather than a command — Claude writes the JSON file, and Thursday you load it.

## In the room

The projector page is driven from the keyboard:

| key | |
| --- | --- |
| m | the question menu — every prepared question, jump to any of them |
| 1–9 | with the menu up, the question with that number |
| space or → | next question |
| ← | back |
| o | open or close voting |
| h | show or hide results |
| r | reveal the answer |
| j | put the welcome screen back up, for whoever walked in late |

A prepared class is a set of questions to reach for in whatever order the
discussion takes, not a queue to walk front to back — that is what the menu is
for. A question typed on the spot joins the same set and can be returned to.

## Question types

| type | students see | projector shows |
| --- | --- | --- |
| `choice` | tappable options, A/B/C | a bar per option, as % of the people who answered |
| `multi` | the same, tick any number, then Submit | a bar per option, as % of the people who answered — so they add to more than 100% |
| `wordcloud` | a text box | answers sized by how many said them |
| `scale` | a row of numbers | distribution plus the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | options by average position |

If you would rather say the type than have it guessed, there is a command for
each: `/survey:choice`, `/survey:select-all`, `/survey:word-cloud`,
`/survey:scale`, `/survey:number`, `/survey:rank`.

## Perception questions draw live

Most of these ask what students think and how solid they feel, so there is no
right answer and the distribution builds on screen as they answer. Press `h` if
you would rather withhold it and show the room at the end.

A question that does have a right answer behaves differently: mark it and the
projector shows only a count while voting is open, then the distribution when
you close voting or press `r`. A bar growing in real time tells the room what
the popular answer is, and quiet students follow it.

## The app

Source and HTTP API: <https://github.com/kerryback/survey>. It holds one session
in memory and stores nothing, so a redeploy loses the class in progress and
there is no history to mine afterwards. `results` downloads a CSV if you want
one.
