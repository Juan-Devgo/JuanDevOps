---
name: jd-agents
description: Set up or update AGENTS.md (single source of truth for agent instructions) for the JuanDevops methodology and make CLAUDE.md point to it. Use when starting a JuanDevops project or when the user wants to change the always-on agent instructions.
---

# JD Agents

Create or update `AGENTS.md` with the instructions agents must follow on every call. Keep it small.

## 1. Gather

Inspect the repo first (package.json, pyproject.toml, Makefile, lockfiles, CI config, sonar-project.properties, existing AGENTS.md / CLAUDE.md, git branches). Do not ask what you can detect.

Ask with AskUserQuestion, prefilled with what you detected:
- Project name (used for the Obsidian folder `Projects/<name>/docs`).
- Docs mode. Offer `mirror` and `vault-only` only if the `jd-obsidian-sync` agent is installed (it needs a vault from `install.py`):
  - `mirror`: `docs/` committed and copied to Obsidian.
  - `vault-only`: `docs/` is a gitignored working copy; Obsidian is the source of truth.
  - `repo-only`: `docs/` committed; no Obsidian.
  - `none`: no docs files; results stay in chat, tests, commits and PRs.
- Stack: language, framework, key libraries, package manager.
- Commands: install, dev, build, test (with coverage), lint, typecheck, Sonar scan.

Conventions: detect what the code already does. For each convention not defined or not detectable, ask and recommend an option based on the stack and community standard:
- Slice layout: where features live (e.g. `src/features/<feature>/`), where tests live, where shared code goes.
- Naming: files, directories, symbols, test files (test names reference the AC id, e.g. `test_ac3_rejects_duplicate_email`).
- Formatting and imports, error handling, logging format, language of code and comments.

AskUserQuestion: max 4 questions per round, 2-4 options each, recommended option first with a concrete example. Do not ask what a config file already enforces.

## 2. Write AGENTS.md

Use this structure. Omit empty sections.

```
# AGENTS.md

## Project
- Name: <name>. Docs mode: <mirror | vault-only | repo-only | none>.

## Workflow (JuanDevops)
- Docs hierarchy: `docs/backlog.md` > `docs/user-stories/US-#.md` > `docs/sprints/###/backlog.md` > code. Each level complies with the one above.
- Docs mode: `mirror`/`repo-only` commit `docs/`; `mirror`/`vault-only` launch `jd-obsidian-sync` in the background with the changed paths after any `docs/` change; `none` writes nothing in `docs/`: show the doc in chat, and when a step needs an earlier doc, use the conversation, tests and PRs, or ask.
- Steps: `jd-backlog` → `jd-acceptance-criteria` → `jd-sprint` → `jd-pair-tdd` + `jd-static-analysis` → `jd-infra` → `jd-cicd` → release → `jd-observability` → `jd-retro` (loop).
- Pair programming: developer = navigator, agent = driver. Warn about architecture risks with a reason; the developer has the final word.
- Essential technical decisions are recorded with `jd-decision-log`.

## Git (every step)
- git-flow (`jd-gitflow`) in every step: before changing files, judge whether the work needs a new branch (feature big enough, production bug → `hotfix/X.Y.Z`, release asked → `release/X.Y.Z`) or fits the current one. Never commit to `main` or `develop`; every merge is a PR. Conventional Commits with US/AC ids.

## Architecture
- Vertical slices: one feature/use case per slice in `src/features/<feature>/`. No horizontal layers. Slices do not import each other.
- Observable by design: structured logs, request/correlation id, explicit error codes and messages, health endpoint.

## Stack / Commands / Conventions
- <one line per item> · Test: `<cmd>` · Lint: `<cmd>` · Typecheck: `<cmd>` · Sonar: `<cmd>`

## Testing
- TDD: failing test from an AC, make it pass, refactor. No production code without a failing test.

## Tools
- SonarQube MCP: <used | not used> · DORA action: <name | not used> · gh: <used | not used> · Terraform: <used | not used>
- A step needs a tool not listed here: ask the developer to add it (say what it gives and how) or go without; both are valid. Record the answer here and adapt the step.

## Maintaining this file
- If something matters on every call, ask the user before adding it here.
- Keep this file small: one-line pointers to skills or docs, no duplicates, no stale lines.
```

Rules: facts only, no prose; point to configs instead of repeating them. `vault-only`: add `docs/` to `.gitignore`. Tools: fill only what you detected; the steps ask the rest.

## 3. CLAUDE.md and git

- `CLAUDE.md` contains only `@AGENTS.md`. If it has content, show it, merge what is still valid into AGENTS.md, then replace it.
- Set up git-flow with `jd-gitflow` (Init); commit the setup on a branch and open a PR to `develop`.

## 4. Updating

When AGENTS.md already exists, edit it in place, then re-optimize: remove redundancy, keep every line necessary on every call.
