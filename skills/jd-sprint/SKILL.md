---
name: jd-sprint
description: Prioritize the backlog if needed, group user stories into vertical-slice features and create the next sprint backlog in docs/sprints/###/backlog.md. Use when the developer wants to plan a sprint, prioritize, or update sprint status.
---

# JD Sprint

## 1. Read

- `docs/backlog.md`, `docs/user-stories/`, existing `docs/sprints/*/backlog.md`.
- Latest `docs/sprints/###/retro.md` if present: apply its actions to this plan.

## 2. Prioritize (only if any story has Priority `-`)

Propose P1/P2/P3 per story based on value, risk, and dependencies. Show a table with a one-line reason each. The developer confirms or corrects; update `docs/backlog.md`.

## 3. Group into features

- A feature is a use case delivering end-to-end value: one vertical slice (`src/features/<feature>/`).
- Judge each group: big enough to be its own use case → new feature with its own branch (`jd-gitflow`); a small story that extends a feature still in progress → add it to that feature and its branch.
- Group stories that share the same use case and data; never group by technical layer (no "database feature", "API feature").
- Name features in kebab-case, verb-noun when possible (`register-user`).
- Order by dependencies; flag stories that do not fit any slice.

## 4. Scope the sprint

Ask with AskUserQuestion: sprint goal, duration, capacity. Pick the highest priority features that fit. Stories without AC: run `jd-acceptance-criteria` first.

Sprint number = highest existing + 1, three digits (`001`).

## 5. Write docs/sprints/###/backlog.md

```
# Sprint 001

Goal: <one sentence>
Dates: <start> → <end>

## Features
| Feature | User stories | Branch | Status |
|---|---|---|---|
| register-user | US-1, US-2 | feature/register-user | todo |

## Dependencies and risks
- <risk → mitigation>

## Applied from last retro
- <action>
```

Status: `todo` | `in-progress` | `done`. Update it as work progresses (`jd-pair-tdd`, `jd-gitflow`).

## 6. Finish

- Set `Sprint: ###` in each selected `docs/user-stories/US-#.md`.
- Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths. Decide the branches for the plan and the features with `jd-gitflow`.
- When every feature is `done` and merged, suggest `jd-infra` (first sprint) or asking for a release (`jd-gitflow`).
