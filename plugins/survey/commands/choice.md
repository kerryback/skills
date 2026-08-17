---
description: Put a multiple-choice question to the class, with a bar per option on the projector.
argument-hint: "[the question, then the options]"
---

Invoke the `survey` skill and follow it, with "$ARGUMENTS" as the question and
`choice` as the type. Do not infer the type from the phrasing — the instructor
has already chosen it.

Options come from the list in "$ARGUMENTS", split on commas and a trailing "or".
Capitalise them; they are going on a projector. If "$ARGUMENTS" gives none, write
two to four short ones yourself, and make the wrong ones real misconceptions
rather than filler — a joke option teaches nothing and wastes the distribution.

Set `answer` when there is a right one, and say in your reply which you marked.
It changes how the question behaves: a marked answer hides the distribution
while voting is open and adds a Reveal. Set `"multi": true` if the question
allows more than one.

You are in front of a class. Don't confirm first and don't think out loud — push
it and report in one line what went up.
