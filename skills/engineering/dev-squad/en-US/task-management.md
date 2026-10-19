# Task Management — Markdown Backlog

This asset defines how the Orchestrator creates, reads, and updates epics and tasks in the project's local Markdown backlog.

---

## Location

`{NotesRoot}` is the root where the project keeps notes and the Markdown backlog (an Obsidian vault, the repository's `docs/` folder, etc.). Resolve it once: use the convention the project already has; if there is none, ask the PO where to store it and record it in `state.md`.

```
{NotesRoot}/{ProjectName}/backlog/
├── epics/
│   ├── EPIC-01 - {Epic Name}.md
│   └── …
└── tasks/
    ├── TASK-01.1 - {Task Name}.md
    └── …
```

---

## Epic Template

```markdown
---
tags: [backlog, {project-name-in-kebab-case}, epic]
status: backlog
project: {ProjectName}
created_at: {YYYY-MM-DD}
---

# EPIC-{n}: {Epic Name}

## Objective

{What this epic delivers and what value justifies its existence.}

## Acceptance criteria

- [ ] {measurable criterion 1}
- [ ] {measurable criterion 2}

## Tasks

- [[TASK-{n}.1 - {Name}]]
- [[TASK-{n}.2 - {Name}]]

## Technical context

{Architectural decisions, risks, dependencies.}
```

---

## Task Template

```markdown
---
tags: [backlog, {project-name-in-kebab-case}, task]
status: backlog
epic: [[EPIC-{n} - {Epic Name}]]
complexity: small | medium | large
created_at: {YYYY-MM-DD}
---

# TASK-{epic}.{n}: {Task Name}

## Context

{What needs to be done and why.}

## Acceptance criteria

- [ ] {criterion 1 — measurable and verifiable}
- [ ] {criterion 2}

## Technical details

{Files, endpoints, schemas, env vars, decisions already made.}

## Development notes

{Blockers, decisions, links to commits.}
```

## US standard for epics and tasks (mandatory)

Follow the User Stories standard from the official `task-writing` skill (`US-FORMAT.md`), including the
section "Hierarchy: story vs subtask" — epic and US sit at the same level (wikilink between
`[[EPIC-{n}...]]` and the task, as in the template above, not file nesting); subtask is
reserved for the Tech Lead's technical breakdown. When publishing to a connected tracker, also apply
`tracker-hierarchy.md` from this skill (link mechanism, not `parent`, between epic and US).
Acceptance criteria: Given/When/Then only when there is behavior QA can exercise; deliverables with no system behavior (documentation, process, research, decision) use a verifiable deliverables checklist. Full rule in `task-writing`'s `US-FORMAT.md`.

### Banner on technical tasks

```
> ⚠️ **Technical-scope task.** Contains technical terms and implementation references. Product/QA: focus on **Context** and **Acceptance Criteria**.
```

### Acceptance criteria: BDD (only for behavior QA can exercise)

```markdown
### Scenario N: {title}

**Given** {context}
**When** {action}
**Then** {result}
```

### Acceptance criteria: checklist (no system behavior)

```markdown
- [ ] {deliverable or condition} — {how it is verified / who confirms}
```

## Updating status

Edit the Markdown file's `status` frontmatter:

| Cycle status | Frontmatter value |
|---|---|
| backlog | `backlog` |
| in development | `in-progress` |
| in technical validation | `in-review` |
| in testing | `in-qa` |
| ready / delivered | `done` |
