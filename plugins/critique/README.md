# critique

A simple skill to evaluate AI text output.

It instructs Claude to spawn three subagents that critique the work from
different perspectives; the main agent then integrates their findings and
prioritizes them.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install critique@kerryback
```

Then `/critique`, optionally with a file path or a description of what to look
at. With no argument it critiques the most recent substantial thing Claude
produced in the conversation.

## The three perspectives

| reviewer | asks |
| --- | --- |
| Correctness & completeness | Are the facts, logic, and maths right? What's missing? Are assumptions stated? |
| Clarity & persuasiveness | Is the structure sound? What's buried, redundant, or confusing? |
| Devil's advocate | What would a hostile referee say? Where is the reasoning weakest? |

They run in parallel and read only — none of them edits anything. Each reports
findings as Critical, Warning, or Suggestion.

The main agent then merges overlapping findings, ranks them, and shows you a
numbered list. You choose whether to apply everything, pick individual items, or
keep the critique as notes and change nothing yourself.

## Cost

This is heavyweight by design. Three subagents each read the work in full, so a
critique costs several times what a single-pass review would. That is the point
— three independent readings catch things one pass rationalizes away — but it is
not the thing to run on a paragraph.

After revising, it offers a second pass on the new version.
