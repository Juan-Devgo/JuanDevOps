---
name: jd-acceptance-criteria
description: Analyze a user story for edge cases and write its Given/When/Then acceptance criteria in its own doc. Use when the developer asks to detail, analyze or define acceptance criteria for one or more US-#, or before a story enters a sprint.
---

# JD Acceptance Criteria

One document per story: `docs/user-stories/US-#.md`.

## 1. Select

- Input: US ids, or "all stories without AC". Read `docs/backlog.md` and any existing story doc.
- Next AC id = highest `AC-#` across `docs/user-stories/` + 1. AC ids are global and never reused, so tests can reference them unambiguously.

## 2. Analyze

For each story, walk the happy path, then search edge cases:
- Input: empty, invalid, too long, wrong format, duplicates.
- Boundaries: zero, one, max, limits, pagination.
- Permissions: unauthenticated, wrong role, other user's data.
- State: invalid transitions, already done, deleted, expired.
- Failures: external service down, timeout, partial failure, retries.
- Concurrency: two actors at once, double submit.
- Time and locale: time zones, dates, currency, language.

Business rules you cannot infer: ask with AskUserQuestion (max 4 per round, recommended option first). Do not guess.

## 3. Write docs/user-stories/US-#.md

```
# US-1: <short title>

> As a <actor>, I need <capability> for <benefit>

Priority: P1 · Sprint: -

## Analysis
- Happy path: <steps>
- Edge cases: <case → expected behavior>
- Out of scope: <...>
- Open questions: <...>

## Acceptance criteria
- AC-1 (US-1): Given <state>, when <action>, then <observable result>
```

Rules:
- One behavior per AC; observable from outside (response, UI, stored data, event, log).
- Testable as a unit or slice test; no vague words ("fast", "user-friendly") without a number.
- Cover the happy path plus every edge case that changes behavior.
- Existing AC: never renumber. Changed behavior → edit text; removed → strike it with a reason.

## 4. Finish

- Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths. Committed docs modes: decide where to commit with `jd-gitflow`.
- Report per story: number of ACs, open questions. Suggest `jd-sprint` when P1 stories are covered.
