---
name: jd-gitflow
description: Git-flow for the whole JuanDevops project (feature, develop, release, main, hotfix) - decide in any step whether the work needs a new branch, conventional commits, and PRs for every merge. Use before changing files in any step, and when committing, finishing a feature, merging, releasing or making a hotfix.
---

# JD Gitflow

Git-flow applies to the whole project, not only to merging. In any step, before changing files, analyze whether the work needs a new branch, fits the current one, or needs no branch yet. Propose with the reason; the developer decides. Every merge goes through a PR.

## Branches

| Branch | From | Merges into (PR) | Name |
|---|---|---|---|
| main | - | - | production, tagged `vX.Y.Z` |
| develop | main | - | integration |
| feature | develop | develop | `feature/<feature>` |
| release | develop | main, then main → develop | `release/X.Y.Z` |
| hotfix | main | main, then main → develop | `hotfix/X.Y.Z` |

## Decide the branch

| Situation | Decision |
|---|---|
| New sprint: a group of stories is big enough to be its own use case (own slice, several ACs, end-to-end value) | new `feature/<feature>` from `develop` when work starts |
| Small story or change that extends a feature still in progress | that feature's branch |
| Infra, CI/CD or observability work that deserves its own review | new `feature/<topic>` from `develop` |
| Only patching a bug in production | `hotfix/X.Y.Z` from `main` |
| Features ready in `develop` and the developer asks for a release | `release/X.Y.Z` from `develop` |
| Planning docs (committed docs modes) with no branch yet | commit them on the first feature branch they belong to; a short `feature/<topic>` only if they must reach `develop` alone |
| Reading, analysis, questions, or more work on the current branch | no new branch |

Never commit directly to `main` or `develop`: if the work lands there, it needs a branch and a PR.

## Init

Ensure `main` and `develop` exist. Empty repo: initial commit on `main` (README, .gitignore), then create `develop`. Ask before creating or pushing remote branches.

## Start a branch

`git switch develop && git pull && git switch -c feature/<feature>` (hotfix: from `main`). Uncommitted changes: ask before stashing or moving them. For a feature, fill the Branch column in the sprint backlog.

## Commit

At meaningful points (a green TDD cycle, a finished doc or config). Conventional Commits, scope = feature or topic, reference stories and ACs:
`feat(register-user): reject duplicate email (US-1, AC-3)`
Types: feat, fix, test, refactor, docs, chore, ci, build, perf.

## Pull requests

1. Before: tests, lint and typecheck pass; suggest `jd-static-analysis` if not run. Rebase on or merge the latest base; resolve conflicts with the developer.
2. Open it with `gh pr create`: title as a Conventional Commit, body with the stories and ACs covered, how it was tested, and ADRs.
3. No `gh`: ask the developer to install it or go without; without it, give them the title and body to open the PR on the web. Record the choice under Tools in AGENTS.md. Never replace a PR with a local merge.
4. After merge: delete the branch; for a feature, set it to `done` in the sprint backlog.

## Release (developer asks)

1. `git switch -c release/X.Y.Z develop` (SemVer: breaking → major, features → minor, fixes → patch).
2. Bump version, update `CHANGELOG.md` from commits. Only fixes on this branch.
3. PR to `main`. Merging triggers deploy (`jd-cicd`).
4. Tag `vX.Y.Z` on main, PR `main` → `develop`, delete the release branch.

## Hotfix

`hotfix/X.Y.Z` from `main`, test-first fix, PR to `main`, tag, PR `main` → `develop`.

## Rules

- Never force-push shared branches.
- Confirm with the developer before creating a branch, push, opening or merging a PR, tag, or deleting remote branches.
