---
name: jd-static-analysis
description: Run linters, type checks and SonarQube (via MCP) analysis, triage issues and fix them with the developer's approval. Use only when the developer says it is time for static code analysis or asks about code quality, Sonar issues or the quality gate.
---

# JD Static Analysis

Run only when the developer asks.

## 1. Local checks

- Run lint and typecheck commands from AGENTS.md.
- Run tests with coverage (Sonar needs the coverage report).
- Safe autofixes (formatting, import order) are fine; anything else waits for triage.

## 2. SonarQube

- Load the SonarQube MCP tools (ToolSearch `sonarqube`). If they are missing, tell the developer and stop at local results.
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
- Re-run local checks, tests, and the scan. Repeat until the quality gate passes or the developer stops.

## 5. Report

Quality gate status, issues fixed, issues left (with reason), coverage before → after. If a rule was disabled or a hotspot accepted, record it with `jd-decision-log`.
