---
name: critique
description: Critique and revise work produced by Claude. Spawns parallel reviewer agents that examine the work from different angles, then synthesizes findings and applies revisions.
argument-hint: [file-or-description]
---

# /critique

Critique and revise work that Claude has produced in this session or in a specified file.

## Arguments

- `$ARGUMENTS` — optional path to a file to critique, or a short description of what to critique (e.g., "the paper draft," "the slide deck," "the code I just wrote").
- If no argument is given, critique the most recent substantive work produced in this conversation.

## Workflow

### 1. Identify the work to critique

Read the file(s) or review the recent conversation output to understand what was produced and its purpose.

### 2. Spawn three parallel reviewer agents

Launch these three agents **in parallel** using the Agent tool. Each reviewer is read-only — it analyzes and reports but does not edit.

**Agent 1 — Correctness & Completeness**
> Review the following work for factual correctness, logical consistency, and completeness. Are there errors in reasoning, math, or claims? Are there important gaps or omissions? Are assumptions stated and justified? Report specific issues with line references or quotes. Organize findings as Critical / Warning / Suggestion.

**Agent 2 — Clarity & Persuasiveness**
> Review the following work for clarity, readability, and persuasive force. Is the structure logical? Is anything confusing, redundant, or buried? Could the main message be stated more directly? Would a reader understand the key points quickly? Report specific issues with quotes and proposed rewrites where helpful. Organize findings as Critical / Warning / Suggestion.

**Agent 3 — Devil's Advocate**
> You are a skeptical, tough-minded reviewer. Challenge the assumptions, question the methodology, and look for weaknesses a hostile referee or audience member would find. What are the strongest counterarguments? What would someone who disagrees say? Where is the reasoning weakest? Be specific and constructive. Organize findings as Critical / Warning / Suggestion.

### 3. Synthesize findings

After all three agents report back:

1. **Deduplicate** — merge overlapping findings.
2. **Prioritize** — rank by importance (Critical first, then Warnings, then Suggestions).
3. **Present to the user** — show a concise numbered list of findings with the reviewer source noted.

### 4. Ask the user

Ask whether to:
- **Apply all** revisions automatically
- **Apply selectively** — let the user choose which findings to address
- **Skip** — just keep the critique as feedback

### 5. Revise (if approved)

Apply the approved changes to the file(s) using the Edit tool. For each change, briefly note which critique finding it addresses.

After revising, offer to run `/critique` again on the revised version for a second pass.
