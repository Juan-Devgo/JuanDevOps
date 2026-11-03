---
name: jd-agents
description: Set up or update AGENTS.md (single source of truth for agent instructions) for the JuanDevops methodology and make CLAUDE.md point to it. Use when starting a JuanDevops project or when the user wants to change the always-on agent instructions.
---

# JD Agents

Create or update `AGENTS.md` with the instructions agents must follow on every call. Keep it small.

## 1. Gather

Inspect the repo first (package.json, pyproject.toml, Makefile, lockfiles, CI config, sonar-project.properties, existing AGENTS.md / CLAUDE.md). Do not ask what you can detect.

Ask with AskUserQuestion, prefilled with what you detected:
- Project name (used for the Obsidian folder `Projects/<name>/docs`).
- Docs mode: `mirror` (docs committed in `docs/` and copied to Obsidian) or `vault-only` (`docs/` is a gitignored working copy; Obsidian is the source of truth).
- Stack: language, framework, key libraries, package manager.
- Commands: install, dev, build, test (with coverage), lint, typecheck, Sonar scan.

Conventions: detect what the code already does. For each convention not defined or not detectable, ask and recommend an option based on the stack and community standard:
- Slice layout: where features live (e.g. `src/features/<feature>/`), where tests live (inside the slice or `tests/<feature>/`), where shared code goes.
- Naming: files, directories, symbols, test files (test names reference the AC id, e.g. `test_ac3_rejects_duplicate_email`).
- Formatting and imports, error handling, logging format, language of code and comments.

AskUserQuestion: max 4 questions per round, 2-4 options each, recommended option first with a concrete example. Do not ask what a config file already enforces.

## 2. Write AGENTS.md

Use this structure. Omit empty sections.

```
# AGENTS.md

## Project
- Name: <name>. Docs mode: <mirror | vault-only>.

## Workflow (JuanDevops)
- Docs hierarchy: `docs/backlog.md` > `docs/user-stories/US-#.md` > `docs/sprints/###/backlog.md` > code. Each level complies with the one above.
- After writing or editing anything in `docs/`, launch the `jd-obsidian-sync` agent in the background with the changed paths. Keep working meanwhile.
- Steps: `jd-backlog` → `jd-acceptance-criteria` → `jd-sprint` → `jd-pair-tdd` + `jd-static-analysis` → `jd-infra` → `jd-gitflow` + `jd-cicd` → `jd-observability` → `jd-retro` (loop).
- Pair programming: developer = navigator, agent = driver. Warn about architecture risks with a reason; the developer has the final word.
- Essential technical decisions are recorded with `jd-decision-log`.

## Architecture
- Vertical slices: one feature/use case per slice in `src/features/<feature>/`. No horizontal layers. Slices do not import each other.
- Observable by design: structured logs, request/correlation id, explicit error codes and messages, health endpoint.

## Stack
- <one line per item>

## Commands
- Test: `<cmd>` · Lint: `<cmd>` · Typecheck: `<cmd>` · Sonar: `<cmd>`

## Conventions
- <only what the user decided>

## Testing
- TDD: failing test from an AC, make it pass, refactor. No production code without a failing test.

## Git
- git-flow: `feature/<feature>` → `develop` → `release/x.y.z` → `main`. Conventional Commits. See `jd-gitflow`.

## Maintaining this file
- If something matters on every call, ask the user before adding it here.
- Prefer a one-line pointer to a skill or doc over explaining.
- Keep this file small: merge duplicates, delete stale lines, move details to docs or skills.
```

Rules:
- Commands, stack and conventions: facts only, no prose. Point to configs instead of repeating them.
- `vault-only`: add `docs/` to `.gitignore`.

## 3. CLAUDE.md

`CLAUDE.md` must contain only `@AGENTS.md`. If it already has content, show it to the user, merge what is still valid into AGENTS.md, then replace it.

## 4. Updating

When AGENTS.md already exists, edit it in place, then re-optimize: remove redundancy, keep every line necessary on every call.
