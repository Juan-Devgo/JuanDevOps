---
name: jd-observability
description: Suggest observability tools for the defined architecture and infrastructure, check the app is observable by design, and connect it to logs, metrics, traces, errors and alerts. Use after infrastructure and CI/CD exist, or when the developer asks about monitoring or observability.
---

# JD Observability

## 1. Read

Git: decide the branch with `jd-gitflow` (usually a new `feature/observability-<topic>`; a small change can join a branch in progress).

`docs/infrastructure.md`, `docs/decisions/`, AGENTS.md (stack), budget in `docs/backlog.md` Notes, the main user journeys in `docs/user-stories/`.

## 2. Suggest tools

One table, one row per need, 2-3 options each (managed vs self-hosted), with rough cost:

| Need | Option | Cost | Fits because |
|---|---|---|---|
| Logs / Metrics / Traces / Errors / Uptime and alerts | | | |

- Prefer OpenTelemetry for instrumentation, so the backend can change later.
- Prefer what the cloud provider already includes when the budget is small.
- Recommend one coherent set. The developer decides; record it with `jd-decision-log`.

## 3. Check observability by design

Verify, per slice:
- Structured (JSON) logs with level, slice, request/correlation id; no secrets or personal data.
- Errors return explicit codes and messages and are logged once, with context.
- Health and readiness endpoints; metrics endpoint if pull-based.
- Key operations of each user story emit a log or metric.

Gaps that need code: fix them with `jd-pair-tdd` (tests first).

## 4. Connect

- Add SDK or agent configuration; endpoints and keys from environment variables and secrets, never hardcoded.
- Define dashboards, alerts and uptime checks in Terraform under `infra/` when the provider supports it.
- Add needed secrets to the deploy workflow (`jd-cicd`).

## 5. SLOs and alerts

- SLIs per critical user journey: availability, latency (p95), error rate.
- Dashboard: golden signals (latency, traffic, errors, saturation) plus key business events.
- Few, actionable alerts, each with a runbook line.

## 6. Document docs/observability.md

Tools, what goes where, dashboard links, SLOs, alerts and runbooks. Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths. Commit and open the PR to `develop` (`jd-gitflow`); it ships with the next release. Suggest `jd-retro` once production data exists.
