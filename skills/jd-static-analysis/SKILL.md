---
name: jd-static-analysis
description: Run linters, type checks and SonarQube (via MCP) analysis, triage issues and fix them with the developer's approval. Use only when the developer says it is time for static code analysis or asks about code quality, Sonar issues or the quality gate.
---

# JD Static Analysis

Run only when the developer asks. Fixes go on the branch being analyzed; for fixes outside it, decide the branch with `jd-gitflow`.

## 1. Local checks

- Run lint and typecheck commands from AGENTS.md.
- Run tests with coverage (Sonar needs the coverage report).
- Safe autofixes (formatting, import order) are fine; anything else waits for triage.

## 2. SonarQube

- AGENTS.md Tools says SonarQube is not used: skip this section.
- Load the SonarQube MCP tools (ToolSearch `sonarqube`). Missing: ask the developer to add the SonarQube MCP server (server-side issues, quality gate, hotspots) or go without it (local results only); both are valid. Record the answer under Tools in AGENTS.md.
- If server results may be stale, run the Sonar scan command from AGENTS.md first.
- Fetch for the project and current branch: quality gate status, issues (bugs, vulnerabilities, code smells), security hotspots, coverage, duplications.

## 3. Triage

Show one table, most severe first:

| Severity | Source | Rule | File:line | Problem | Proposed fix |
|---|---|---|---|---|---|

- Blocker / critical / vulnerabilities: propose fixing now.
- Major: propose fixing in this sprint.
- Minor / info: list only.
- Likely false positive: say why; the developer decides whether to mark it in Sonar.
- Repeated issue pattern: propose a lint rule or convention instead of one-off fixes.

## 4. Fix

- Fix only what the developer approves.
- Keep TDD: if a fix changes behavior, write or update the test first.
- Re-run local checks, tests, and the scan. Repeat until the quality gate (or local checks without Sonar) passes or the developer stops.
- Commit each fix (`fix(<scope>): ...` or `refactor(...)`, `jd-gitflow`).

## 5. Report

Quality gate status, issues fixed, issues left (with reason), coverage before → after. If a rule was disabled or a hotspot accepted, record it with `jd-decision-log`.
