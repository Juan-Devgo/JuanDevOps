---
name: jd-retro
description: Close the JuanDevops loop - analyze observability, DORA and quality data after a release, suggest improvements and post-sprint fixes, and write feedback for the next sprint. Use after a release is deployed, or when the developer asks about production data or what to improve.
---

# JD Retro

The developer decides; the agent analyzes and suggests.

## 1. Gather

- Observability: query the tools in `docs/observability.md` through available MCP tools or CLIs; otherwise ask the developer for exports or screenshots.
- DORA metrics from the developer's DORA action (deployment frequency, lead time, change failure rate, time to restore).
- Quality: latest SonarQube quality gate and coverage.
- Plan vs result: `docs/sprints/###/backlog.md`, ADRs from this sprint.

## 2. Analyze (when asked, or at sprint end)

- Errors: top errors by volume and affected users; link each to its slice and user story.
- Performance: latency and SLO breaches, regressions after the release.
- Usage: which features are used, which are not.
- Cost: actual vs estimated in `docs/infrastructure.md`.
- DORA: trend vs previous release.

Separate facts (with the data source) from hypotheses. Do not overstate small samples.

## 3. Suggest

One table, ordered by impact:

| Finding | Evidence | Suggestion | Type |
|---|---|---|---|

Types: hotfix (`jd-gitflow`), new story (`jd-backlog`), tech debt, infra change (`jd-infra`), observability gap (`jd-observability`).
Add stories to the backlog only after the developer approves.

## 4. Feedback for the next sprint

If the backlog has stories not assigned to any sprint, write `docs/sprints/###/retro.md` for the completed sprint:

```
# Retro: Sprint 001 (vX.Y.Z)

## Metrics
- DORA: <values> · Quality gate: <status> · Coverage: <%> · Errors/SLO: <summary>

## Went well
- <...>

## Problems
- <problem → cause>

## Actions for next sprint
- <concrete, checkable action> (max 5)
```

`jd-sprint` reads this file when planning the next sprint.

## 5. Finish

Launch the `jd-obsidian-sync` agent in the background with the changed paths. Suggest the next step: `jd-sprint` (loop) or the approved fixes.
