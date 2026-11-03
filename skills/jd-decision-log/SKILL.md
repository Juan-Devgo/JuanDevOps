---
name: jd-decision-log
description: Record an essential technical decision with its reason as an ADR in docs/decisions/. Use when the developer chooses a library, framework, pattern, data model, API contract, infrastructure option, deviates from a convention, or overrules an agent warning.
---

# JD Decision Log

## When

Record a decision when it is hard to reverse or affects more than one slice:
- Framework, library, database, external service.
- Architecture pattern, API contract, data model.
- Infrastructure, CI/CD, observability tooling.
- Deviation from AGENTS.md conventions.
- The developer overrules an agent warning (record the warning as a consequence).

Skip trivial, local, easily reversible choices.

## Write docs/decisions/ADR-###-<kebab-title>.md

Number = highest existing + 1, three digits. Commit it on the branch of the change it records (`jd-gitflow`).
Docs mode `none`: put the same content in the commit body and the PR description instead of a file.

```
# ADR-001: <decision title>

Status: accepted · Date: <YYYY-MM-DD>
Related: US-1, Sprint 001

## Context
<problem and forces, 2-4 lines>

## Decision
<what was decided, 1-2 lines>

## Reason
<why this option>

## Alternatives
- <option>: <why rejected>

## Consequences
- <trade-offs, risks, follow-ups>
```

## Index

Keep `docs/decisions/index.md` as a table: `| ADR | Title | Status | Date |`. Add a row per new ADR.

## Rules

- Short: the whole ADR fits on one screen.
- Write the developer's reason, not yours. Ask if the reason was not stated.
- Never rewrite an accepted decision. Create a new ADR and set the old one to `superseded by ADR-###`.
- Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths.
