---
name: jd-gitflow
description: Manage branches with git-flow for JuanDevops (feature, develop, release, main, hotfix), with conventional names and commits. Use when starting or finishing a feature, committing, creating a release, merging, or making a hotfix.
---

# JD Gitflow

## Branches

| Branch | From | Merges into | Name |
|---|---|---|---|
| main | - | - | production, tagged `vX.Y.Z` |
| develop | main | - | integration |
| feature | develop | develop | `feature/<feature>` (from sprint backlog) |
| release | develop | main + develop | `release/X.Y.Z` |
| hotfix | main | main + develop | `hotfix/X.Y.Z` |

## Init

Ensure `main` and `develop` exist. Ask before creating or pushing remote branches.

## Start feature

```
git switch develop && git pull
git switch -c feature/<feature>
```

Fill the Branch column in `docs/sprints/###/backlog.md`.

## Commit

Conventional Commits, scope = feature, reference stories and ACs:
`feat(register-user): reject duplicate email (US-1, AC-3)`
Types: feat, fix, test, refactor, docs, chore, ci, build, perf.

## Finish feature

1. Tests, lint and typecheck pass. Suggest `jd-static-analysis` if not run.
2. Rebase on or merge latest `develop`; resolve conflicts with the developer.
3. Open a PR to `develop` (`gh pr create`) with the stories and ACs covered. Local `git merge --no-ff` only if the developer prefers.
4. After merge: delete the branch, set the feature to `done` in the sprint backlog.

## Release (sprint done)

1. `git switch -c release/X.Y.Z develop` (SemVer: breaking → major, features → minor, fixes → patch).
2. Bump version, update `CHANGELOG.md` from commits. Only fixes on this branch.
3. PR to `main`. Merging triggers deploy (`jd-cicd`).
4. Tag `vX.Y.Z` on main, merge `main` back into `develop`, delete the release branch.

## Hotfix

`hotfix/X.Y.Z` from `main`, test-first fix, PR to `main`, tag, merge back into `develop`.

## Rules

- Never commit directly to `main` or `develop`.
- Never force-push shared branches.
- Confirm with the developer before push, merge, tag, or deleting remote branches.
