# Writing `protocols.html`

This is the spec for the human-facing guide you write to the repo root during
setup. `CLAUDE.md` is the operating manual for you; this is the one document a
coauthor actually reads. Write it once at setup, and update it whenever a rule
in `CLAUDE.md` changes — the two are a pair, and a stale `protocols.html` is
worse than none, because people believe it.

Write it LAST, after the repo is built and verified. It describes what is
actually there, not what was planned: if the interview said no to the debate
panel, the guide has no debate section.

## Who it is for

One person, on their first day, who did not run setup and was not in the
conversation. They know the field and their own research; they may not know git
beyond `commit` and `push`, and they have never seen this layout. They want to
do one afternoon's work without breaking anything or asking a question they feel
they should already know the answer to.

Write for that person, in ordinary sentences. This is the one place in the repo
where the audience is not Claude.

## What it must cover

**1. What this project is.** The one-line description, then two or three
sentences of context. Who is on it, and what stage it is at.

**2. Your first twenty minutes.** The literal steps, in order, with the commands
spelled out: clone, set the data environment variable, create the venv, install
requirements, open Claude Code in the repo and say "get me set up." Say that
Claude runs `tools/onboard.py` itself and will walk them through what is
missing — they do not have to memorize any of this.

Include the one thing that fails silently: their `git config user.name` decides
the slug that names every folder they own. Show them how to check it and what it
will produce.

**3. Where things live, and the one rule.** A short tree, then the rule stated
plainly: `project/global/` is shared and is the project; `project/<you>/` is
yours and nobody else writes in it; data lives outside the repo and is never
committed. Say where the data actually is, by name — the Dropbox or Box folder,
not just an environment variable.

**4. Rounds.** This is the section that most needs to exist, because "round" is
the one piece of vocabulary a newcomer cannot guess and it governs when they may
touch shared state. Cover, in this order:

- What a round is: one bounded stretch of work that ends with `state.md`
  rewritten.
- Why it is claimed: `state.md` is long prose and git cannot merge it, so two
  people rewriting it at once produce a conflict on the file that defines what
  the paper is. A push is atomic, so exactly one claim wins and the loser finds
  out immediately instead of at merge time.
- How: bare `/round` finishes one and is the command they will actually use;
  `/round start "what this is"` claims it first and is only worth doing when
  someone else might be working; `/round status` says who holds it. Say plainly
  that not claiming a round is normal when working alone.
- **A round is not a session.** A round is a unit of work and can span several
  context windows; a session is one conversation with Claude. `/refresh`
  checkpoints a session and deliberately leaves the round open. Say this
  explicitly — it is the single most common misreading, and getting it wrong
  means either a lock released mid-work or one held for days.
- What to do when the claim fails: someone else holds it. Work on something that
  does not touch shared state, and do not edit `state.md` anyway. The lock is a
  protocol between people who agreed to use it, not a permission system, so it
  only works if it is honoured when it is inconvenient.

**5. What the project remembers.** The two committed records — the changelog in
`state.md`, and the run records — and the fact that there is no session log, on
purpose. Then the part that asks something of them: every round ends with an
entry saying what it took up and what came of it, written *even when the round
settled nothing*. That is what answers "did we ever try X" a year later, and it
is the entry people skip, because a round that changed nothing feels like
nothing worth recording. It leaves no diff and no artifact, so if the entry is
not written the exploration is gone. Killed ideas also go in the killed-ideas
section with the reason.

**6. Why Claude runs your scripts oddly.** They will notice Claude typing
`python3 tools/runlog.py my_script.py` instead of `python3 my_script.py`, and
should know why rather than assuming it is a quirk: the wrapper runs the script
normally and appends one line recording the script, the commit, and the files it
actually read and wrote. That line is what answers "where did this number come
from" when a referee asks. Tell them to do the same when they run something
themselves, and that a script run directly still works — it just leaves no
record, and nothing warns them.

**7. Writing.** `writing-guide.md` in the repo root governs everything in
`draft/`. Say that it is binding rather than advisory, that it does not apply to
notes between coauthors, and that Claude reads it before drafting.

**8. The commands.** A short table: `/round`, `/round start`, `/refresh`,
`/report`, and anything else the project got. One line each, in plain language.

**9. Who to ask.** Names, and what each person owns.

Include only the sections that apply. If the project got Overleaf, add how the
mirror works and the rule that you always pull before you push. If it got the
debate panel, add what it costs — their own OpenRouter key, their own calls —
and that the briefs stay on their machine while the decision goes in the
changelog.

## What to leave out

- The internals of `tools/`. If they need provenance, they will ask Claude.
- Anything addressed to Claude. Do not paste `CLAUDE.md` sections in; rewrite
  them for a person or leave them out.
- Rationale for choices they cannot change. Say what the rule is and the one
  sentence of why that makes it stick; skip the design argument.
- Aspirations. Document the repo that exists.

## How to write it

Self-contained HTML — no external stylesheets, scripts, fonts, or images.
Everything inline. Theme-aware: define the light palette on `:root`, redefine
under `@media (prefers-color-scheme: dark)` guarded as
`:root:not([data-theme="light"])`, and give `body` an explicit background.

Readable on a laptop without zooming: a max-width around 70 characters of text,
generous line height, and commands in a monospace block that can be copied in
one selection. Any wide block scrolls inside its own container rather than
making the page scroll sideways.

`/report` writes its report to the same repo root and matches whatever style it
finds here, so this file sets the visual language for the project's documents.
Keep it plain and typographic — it is a reference someone opens on their second
day, not a landing page.

Every command in it must be one you actually ran or verified during setup. A
guide with a command that does not work teaches the reader that the guide is not
to be trusted, and they will stop reading it at that point.
