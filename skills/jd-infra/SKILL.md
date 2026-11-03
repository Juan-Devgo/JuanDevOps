---
name: jd-infra
description: Analyze estimated users, budget and architecture, suggest the infrastructure, iterate with the developer, and define it as Terraform IaC. Use when a sprint is completed and infrastructure must be defined or changed before release.
---

# JD Infra

## 1. Gather

Read `docs/backlog.md` (Notes), `docs/decisions/`, AGENTS.md (stack), the slices in `src/features/`, data stores and external services. Ask with AskUserQuestion only what is missing:
- Estimated users now and in 12 months; peak requests per second.
- Monthly budget; cloud provider preference or credits.
- Region, compliance, data residency.
- Availability target; who operates it (ops experience).

## 2. Propose

Show 2-3 options in one table: cheapest viable, recommended, scale-ready.

| Option | Compute | Data | Network / CDN | Est. monthly cost | Pros | Cons |
|---|---|---|---|---|---|---|

- State assumptions behind each cost estimate; mark them as rough.
- Fit the architecture: vertical slices usually deploy as one service until load says otherwise; do not propose microservices without evidence.
- Include environments (staging, production), secrets management, backups, and a place for observability.
- Recommend one with the reason.

## 3. Agree

The developer corrects; iterate. Record the final choice with `jd-decision-log`.

## 4. Document docs/infrastructure.md

Inputs, chosen option, Mermaid diagram, environments, cost estimate, outputs CI/CD needs. Launch the `jd-obsidian-sync` agent in the background.

## 5. Terraform in infra/

```
infra/
  modules/<component>/        # reusable pieces
  environments/staging/       # main.tf, variables.tf, outputs.tf, backend.tf
  environments/production/
```

- Remote state with locking (backend per environment).
- Pin provider and Terraform versions.
- No secrets in code: variables marked `sensitive`, values from a secret manager or CI secrets.
- Outputs for CI/CD: deploy target, registry URL, URLs, ids.
- Tag resources with project and environment.
- Run `terraform fmt`, `terraform validate`, `tflint` if installed, and `terraform plan`.
- Never run `terraform apply` or `destroy` without explicit developer approval; they cost money and change real resources.

## 6. Finish

Summarize the plan output and suggest `jd-cicd`.
