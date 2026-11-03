---
name: jd-cicd
description: Define CI/CD with GitHub Actions for JuanDevops - CI on every branch and PR, deploy of the release to the Terraform-defined infrastructure on merge to main. Use when setting up or changing workflows, pipelines or deployments.
---

# JD CI/CD

## 1. Read

Git: decide the branch with `jd-gitflow` (usually a new `feature/cicd-<topic>`; a small change can join a branch in progress). Workflows follow the git-flow branches.

AGENTS.md (commands, Tools), `docs/infrastructure.md` and `infra/` outputs (deploy target, registry), existing `.github/workflows/`.

DORA metrics: ask which DORA metrics GitHub Action the developer uses (unless Tools says). Do not implement it; make deploys visible to it (GitHub `environment: production` deployments, stable workflow and job names). None: ask them to add one or go without (`jd-retro` then skips DORA); both are valid. Record the answer under Tools.

## 2. Workflows in .github/workflows/

`ci.yml`, on pull_request and push to `develop`, `feature/**`, `release/**`, `hotfix/**`:
- Install with dependency cache.
- Lint, typecheck, tests with coverage.
- SonarQube scan + quality gate (`SONAR_TOKEN`, `SONAR_HOST_URL` secrets), fail on gate failure. Only if SonarQube is used (Tools); otherwise ask to add it or skip the step.

`infra.yml`, on pull_request touching `infra/**`:
- `terraform fmt -check`, `validate`, `plan`; post the plan as a PR comment.

`deploy.yml`:
- On push to `release/**`: build, deploy to staging.
- On push to `main`: build once, `terraform apply` for production if `infra/` changed, deploy the artifact, smoke test the health endpoint.
- `environment: production` (optional required reviewers), `concurrency` group per environment, no cancel in progress.
- Version and image tag from the release (`vX.Y.Z`) or commit SHA.
- Rollback step or documented manual rollback.

## 3. Rules

- Cloud auth via OIDC; no long-lived cloud keys in secrets when the provider supports OIDC.
- Pin actions to a major version or SHA; least-privilege `permissions:` per workflow.
- Same commands as local (from AGENTS.md); no logic that only exists in CI.
- No secrets in logs or in the repo.
- Validate with `actionlint` if installed.

## 4. Document

Add a `## CI/CD` section to `docs/infrastructure.md`: workflows, triggers, required secrets and variables, environments. Save per the docs mode in AGENTS.md: `none` → show it in chat; `mirror`/`vault-only` → launch the `jd-obsidian-sync` agent in the background with the changed paths. Record non-obvious choices with `jd-decision-log`.

## 5. Finish

List the secrets the developer must create in GitHub. Commit and open the PR to `develop` (`jd-gitflow`). Do not push or trigger workflows without approval.
