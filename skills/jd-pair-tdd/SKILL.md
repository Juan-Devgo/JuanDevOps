---
name: jd-pair-tdd
description: Pair programming with TDD on a vertical slice, developer as navigator and agent as driver. Use when the developer asks to implement a piece of code for a sprint feature, or asks a technical question while implementing.
---

# JD Pair TDD

Developer = navigator (decides what and why). Agent = driver (writes tests and code). The developer has the final word.

## 1. Context

- Identify the sprint, feature and user story being worked on. If unclear, ask.
- Read `docs/user-stories/US-#.md` (its ACs), `docs/sprints/###/backlog.md`, and the slice in `src/features/<feature>/`.
- Set the feature status to `in-progress` if it was `todo`.

## 2. Scope

The developer asks for a small section. If it is too big for one red-green cycle, propose a split and let the developer pick.

## 3. Red

- For each AC touched by the request that has no test yet, write a unit test named after it (e.g. `test_ac3_rejects_duplicate_email`).
- Also test the edge cases listed in the story analysis that apply.
- Run the tests. Confirm they fail for the right reason (not import or syntax errors).

## 4. Green

- Write the minimum code that makes all tests pass.
- Run the slice tests, then the whole suite.

## 5. Refactor

Remove duplication and improve names while staying green. Run tests again.

## 6. Report

Short: tests added (AC ids), files changed, what is left of the story. Suggest the next small section.

## Rules

- Vertical slice: code and tests stay inside `src/features/<feature>/`. Shared code only when two or more slices need it. Slices never import each other.
- Observable by design: structured logs at slice boundaries, explicit error codes and messages, request/correlation id propagated, no swallowed exceptions.
- Navigator authority: if a request risks architecture (cross-slice coupling, horizontal layering), security, performance, or future maintenance, say it once with the reason and an alternative. Then do what the developer decides.
- Essential decision (library, pattern, contract, data model, overruled warning): record it with `jd-decision-log`.
- Technical questions: answer directly and briefly, with the trade-off.
- Do not run static analysis unless the developer asks (`jd-static-analysis`).
- Set the feature to `done` only when the developer confirms and all its ACs have passing tests.
