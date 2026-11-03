---
name: jd-backlog
description: Build or update the initial product backlog (user stories) from a specification, clarifying the spec with the developer first. Use when the developer shares a spec, asks for a backlog, or wants to add, change or drop user stories.
---

# JD Backlog

Turn a specification into `docs/backlog.md`. Clarify before writing; never invent requirements.

## 1. Read

- Get the spec (file, pasted text, link). If there is none, ask for it.
- Read existing `docs/backlog.md` and `AGENTS.md` if present.

## 2. Clarify

List what blocks writing good stories:
- Actors and roles not named or ambiguous.
- Capabilities that are vague ("manage", "handle", "support").
- Business rules, limits and exceptions not stated.
- Scope: what is explicitly out.
- Non-functional hints: estimated users, budget, availability, compliance, deadlines (used later by `jd-infra`).

Ask with AskUserQuestion: max 4 questions per round, 2-4 options, recommended option first. Repeat until nothing blocking remains. Record non-blocking unknowns under `## Open questions`.

## 3. Write docs/backlog.md

```
# Product backlog: <project>

<one paragraph: product goal>

## User stories
| ID | Priority | Actor | Story |
|---|---|---|---|
| US-1 | P1 | <actor> | As a <actor>, I need <capability> for <benefit> |

## Notes
- Users: <estimate> · Budget: <estimate> · Constraints: <...>

## Open questions
- <question>
```

Rules:
- One capability per story; small enough to finish in one sprint (INVEST).
- Priority: P1 must-have (MVP), P2 should-have, P3 could-have. Suggest it; the developer confirms. Leave `-` if the developer wants to prioritize later in `jd-sprint`.
- IDs are stable: new stories take the next number; never renumber or reuse.
- Dropped story: keep the row, strike it (`~~US-4~~`) and put `Dropped: <reason>` in Story.
- Benefit must be real value for the actor, not a restatement of the capability.

## 4. Finish

- Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths. Committed docs modes: decide where to commit with `jd-gitflow`.
- Show the table and suggest next step: `jd-acceptance-criteria` for P1 stories.
