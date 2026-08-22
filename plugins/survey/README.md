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

## Ways in, and the way out

| | |
| --- | --- |
| `/survey <a question>` | that question, on the projector, now |
| `/survey <a file>` | a poll you had Claude write earlier |
| `/survey` | a new room; QR and join code on the projector, nothing loaded |
| `/survey stop` | end the session; the display says "No session running" |

"Write me a poll for Thursday" is another, and it is ordinary conversation
rather than a command — Claude writes the JSON file, and Thursday you load it.

A question typed on the spot and a prepared file join the same session, so they
share one menu. Bare `/survey` starts a new one: it ends whatever was left
running, so Tuesday's class never opens with last Thursday's questions still in
the menu. Ask for a new poll or a fresh session when loading a file and you get
the same clean start.

## The projector

Claude opens the display on the machine it is running on. When that isn't the
machine plugged into the projector, the other one goes to
<https://poll.kerryback.com/display> and types the six-digit display code Claude
prints at the start of the session. Both can be open at once and stay in sync,
so you can advance questions from your own laptop while the room watches the
podium screen.

The display code is not the room code students type, and it never appears on the
projector — it drives the deck. A new session mints a new one; the podium page
waits on "No session running" in between and asks for the new code by itself.

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
| `choice` | tappable options, A/B/C | a pie, each slice labelled with its % of the people who answered |
| `multi` | the same, tick any number, then Submit | a bar per option, measured against everyone who answered — so they add to more than 100% |
| `wordcloud` | a text box | answers sized by how many said them |
| `scale` | a row of numbers | distribution plus the mean |
| `number` | a number box | histogram, mean, median, true answer marked |
| `rank` | a reorderable list | a heatmap: categories across, ranks down, colour by % of the room |

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
in memory and stores nothing — no database, no export, no file on disk — so a
redeploy loses the class in progress and there is no history to mine afterwards.
Ask Claude how a question went while the session is still up and it reads the
tallies off the live state; once the session ends they are gone.
