# Branch strategy — projects with staging and production

Applies to any project whose CI/CD has separate environments
(staging + production). Not every project has this — confirm before assuming
(check whether `develop` exists on the remote and whether there is a `deploy.yml`/pipeline with a
per-branch trigger).

## Flow

```
checkout develop → pull → checkout -b feature/<name>_<task-id-if-any>
  → code → PR to develop → merge → test on staging (automatic deploy)
  → [only when the PO decides to go to production] PR from develop to main → merge
```

- `develop` is where the development team works. Every feature branch
  is born from it, not from `main`. The PRs of phase 3 (Code Review) and phase 4 (QA) of this
  skill always target `develop`.
- `main` is reserved for production. The Senior Dev and the Tech Lead never open
  a PR directly to `main`, never commit to it, and never treat it as the destination
  of an ordinary feature.
- The `develop → main` promotion **is not a phase of this skill's development
  cycle** — it is a business decision by the PO, made outside the
  Dev→TL→QA flow, normally when a set of features already tested on
  staging is ready to go live. Treat it as an escalation to the PO (see
  "Escalation rules" in `flow.md`), never as an automatic technical decision.
- If the project does not yet have production infrastructure provisioned, that is
  an infra blocker (route to the environment's infrastructure skill/flow) — do not invent a
  workaround and do not skip the step.

## When the project does not have this split

Projects without a separate production environment (only staging, or only one environment)
follow the generic branch flow of the language/framework skill in use
(e.g. `dev-python`, if any — checkout the base branch → pull → checkout -b feature).
Do not create a `develop`/`main` split for a project that did not ask for it.
