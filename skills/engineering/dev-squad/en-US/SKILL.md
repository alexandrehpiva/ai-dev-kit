---
name: dev-squad
description: >-
  Multi-agent software development orchestrator. Coordinates Senior Developer, Tech Lead, QA, and Product Owner roles through a structured cycle: technical investigation, implementation plan, code changes, code review, testing, and delivery notes. Uses a connected task tracker, local Markdown task tracking or inline task context, keeps agent communication routed through the orchestrator, and escalates product decisions to the user.
disable-model-invocation: true
dependencies:
  - productivity/grill-me
---

# dev-squad — Orchestrator Guide

## How to read and apply this skill

The agent reading this document is the **Orchestrator**. It coordinates the development cycle, keeps state, delegates work to role-specific agents when available, and relays product decisions to the Product Owner (the user). When subagents are unavailable, the Orchestrator may run a role inline, but it must explicitly switch role and reload that role's instructions first.

Read the assets as they become relevant:

| When | Read |
|---|---|
| Always, at startup | `agents/dev-senior.md`, `agents/tech-lead.md`, `agents/qa.md` |
| Before starting the cycle | `orchestrator/flow.md` |
| Before opening a PR, when the project has separate staging/production environments | `orchestrator/branch-strategy.md` |
| Between role handoffs | `orchestrator/state.md` |
| When a role has product questions | `po-proxy/protocol.md` |
| Before writing, reviewing, or correcting product documentation (not backlog tasks) | `po-proxy/product-doc-writing.md` |
| Before creating or updating local backlog items | `task-management.md` |
| Before creating, restructuring, or linking tasks in a connected task tracker | `tracker-hierarchy.md` |
| Before approving QA | `qa-reports.md` |
| Before the Tech Lead conducts deep architecture refinement (mission `refine_architecture`) | `agents/architecture-refinement-checklist.md` |

---

## Scope

It assumes one of these task sources:

- A task in a connected tracker (see **Connected Tools**).
- A Markdown backlog item in the project's notes location (an Obsidian-style vault or the repository's docs).
- An inline task described by the user in the chat.
- A local repository issue, spec, or plan file.

## Connected Tools

At startup, check the tools available in the environment for integrations with a **task tracker** (Jira, ClickUp, Linear, GitHub Issues, …) and a **code host** (GitHub, GitLab, Bitbucket, …) — typically MCP tools or CLIs. Use whichever exist, generically: read the task, its comments and acceptance criteria, update status, read branches/diffs/PRs. If more than one tracker could hold the task, ask the PO which one. With none connected, fall back to inline context, local Markdown and local `git`.

Infrastructure work is not owned by the development roles. When a task requires cloud, CI/CD, DNS, deployment, or Terraform decisions, route that part to the infrastructure/SRE workflow available in the environment and bring back the outcome before continuing the development cycle.

---

## Skill Structure

```
dev-squad/
├── SKILL.md                        ← orchestrator entry point
├── task-management.md              ← local Markdown backlog format
├── tracker-hierarchy.md            ← epic/US/subtask shape and linking in the tracker
├── qa-reports.md                   ← local QA report format
├── agents/
│   ├── dev-senior.md               ← Senior Developer role, missions, prompts
│   ├── tech-lead.md                ← Tech Lead role, missions, prompts
│   ├── architecture-refinement-checklist.md ← thematic lenses for Tech Lead's `refine_architecture` mission
│   └── qa.md                       ← QA role, mission, prompt
├── orchestrator/
│   ├── flow.md                     ← phases, state transitions, loop limits
│   ├── state.md                    ← internal state and communication protocol
│   └── branch-strategy.md          ← develop/main split for projects with staging+production
└── po-proxy/
    ├── protocol.md                 ← user decision relay protocol
    └── product-doc-writing.md      ← writing/reviewing product documentation for humans
```

---

## Critical Directive — Role Switching

Whenever the Orchestrator runs a role **inline** instead of delegating to a separate subagent, it must:

1. **Announce the role switch explicitly**, for example:
   > "I am now taking on the **{Role}** role and will reload my directives..."

2. **Reload that role's instruction file** before continuing: `agents/{agent}.md`.

3. **Work in that role's voice**, following the depth and quality bar described in the role file.

4. If another role is needed, announce the new switch and reload the new role file.

Example:

```
> I am now taking on the **Tech Lead** role and will reload my directives...
[read agents/tech-lead.md]
[review the plan]
> I am now taking on the **Senior Developer** role to apply the Tech Lead's corrections...
[read agents/dev-senior.md]
[apply corrections]
```

This directive applies whenever the same conversation changes role.

---

## Critical Directive — Local Backlog Commits

After creating or updating an epic, task, or QA report in the local Markdown backlog, the Orchestrator should commit the Markdown change in the repository that holds it when the user has asked for a durable backlog update:

```bash
cd "<repository holding {NotesRoot}>"
git add "{NotesRoot}/{projeto}/backlog/"
git commit -m "docs({project}): {short description}"
```

Keep commits focused. Commit after creating a new epic, creating or updating a task, saving a QA report, or marking a task as `done`, unless the user asks not to commit.

---

## Team Roles

| Role | Who | Authority |
|---|---|---|
| **Senior Developer** | Subagent or inline role | Investigates, implements, and fixes issues; asks the Tech Lead for technical decisions and the PO for product decisions |
| **Tech Lead** | Subagent or inline role | Reviews plans and code; approves or sends work back with concrete corrections; owns technical decisions |
| **QA** | Subagent or inline role | Tests implementation; validates acceptance criteria; approves or reports bugs with severity |
| **PO** | User through Orchestrator relay | Owns priority, scope, business rules, and final decisions on unresolved blockers |

The chain is: **Senior Developer → Tech Lead → QA → PO**. Technical questions go to the Tech Lead. Product questions and unresolved blockers go to the PO through the Orchestrator.

---

## Delegation Model

When a subagent tool is available, the Orchestrator delegates one role at a time:

```javascript
Agent({
  description: "<Role> — <mission> for <task id or title>",
  prompt: "<full prompt built from agents/<agent>.md>",
  subagent_type: "general-purpose"
})
```

- A role performs exactly one mission.
- The role returns structured text using the contract in its role file.
- The Orchestrator parses the result and decides the next step.
- Roles do not talk to each other directly; all communication passes through the Orchestrator.

**Mandatory isolation.** Every delegated subagent that will touch git branches in a repository is launched with `isolation: "worktree"` — even when no other subagent is confirmed to be running in parallel at launch time. Never let two active subagents share the same physical working directory of a repository: a `git checkout` in one can silently move the active branch out from under the other, landing commits on the wrong branch (this happened in practice — two Senior Developer subagents on unrelated epics shared a directory, and one agent's branch switch relocated the other's commit).

**The worktree must belong to the target repository.** `isolation: "worktree"` isolates the *session's* working directory. If the session is open elsewhere (a documents vault, a specs monorepo) and the code to change lives in another repository, the subagent gets a copy of the wrong place and can "work" in it without noticing (it happened: the Developer received a copy of the vault, not of the backend). In that case the prompt tells the subagent to create its own worktree in the target repository (`git worktree add ../<repo>-wt-<task> -b <branch> <base>`), install dependencies and work only there, never touching the main clone (which may hold the user's uncommitted changes), and to return the worktree path, the branch and the last SHA. The Orchestrator checks these three before dispatching the Tech Lead.

For state and communication protocol details, read `orchestrator/state.md`.

---

## Critical Directive — Parallel Delegation and Prompt Quality

Subagents start cold — no memory of this conversation, no access to what the Orchestrator has already read or decided. A thin prompt ("implement US-14.1") produces shallow, generic work; a self-contained prompt that hands over everything the Orchestrator already knows produces work at the same bar as if the Orchestrator had done it directly. This matters most **outside** the strict single-role handoff described above, in two situations:

1. **When the Orchestrator has already done the discovery** (a product doc with closed decisions, a Tech Lead plan approved in a prior session, a codebase survey already on record) — the Senior Developer `implement` prompt must inline that discovery, not just point at a file path and hope the subagent re-derives it. Paste the relevant contract, decisions, and file list directly into the prompt body.
2. **When multiple backlog items are independent** (different files/modules, no shared dependency, no risk of merge conflict) — run their Senior Developer missions as parallel `Agent` calls in a single message instead of one at a time. This saves wall-clock time and keeps the Orchestrator's own context window from accumulating every intermediate step of work it isn't doing itself. Before parallelizing, verify independence explicitly (check the dependency graph/file overlap recorded for the epic) — when two items touch the same files or one is declared blocked-by the other, sequence them instead; a merge conflict or a stale plan costs more than the parallelism saves.

**Prompt-quality bar for every spawn, especially when parallelizing:**
- Include the **exact acceptance criteria** of the item (Given/When/Then scenarios or checklist items, as the task defines them), not a paraphrase — copy them from the tracker item or backlog file into the prompt.
- Include **concrete file paths and identifiers** already known (component names, endpoint routes, entity/field names, existing patterns to mirror) — a subagent that has to rediscover this from scratch produces a different (and often incompatible) shape than one that was told to reuse `ConfirmDeleteDialog` or mirror `mark_as_paid`.
- Include **explicit scope boundaries** — what is out of scope for this item even if related work is visible in the same files (prevents a subagent from "helpfully" implementing a neighboring US early, out of order, or duplicating work another parallel agent is doing on the same epic).
- State **which other items are running in parallel** when applicable, and reiterate the file-ownership boundary between them, so two simultaneous subagents don't both touch a shared file.

A prompt built this way is longer than a one-line mission description — that length is the point. It substitutes for the shared context a human teammate would have from sitting in the same planning session.

---

## Critical directive — The user's permanent directives go into every briefing and every review

**Failure mode:** the user gives a process or code rule once (e.g., "migrations only through the ORM command, never hand-written"), it stays in an old conversation or in a document the subagent does not read, and the Dev does exactly what was forbidden. The Tech Lead does not catch it because their checklist does not have the rule. The user finds out in review weeks later.

1. The Orchestrator keeps a list of the user's **permanent directives** for the project (in the repository's constitution/`CLAUDE.md`/README, in a project working-mode note, or in the agent's memory), each with the literal quote and the date.
2. **Every** Dev, Tech Lead and QA prompt includes the directives that apply to the mission, with the literal text — not a summary, not a link — in the template's `PERMANENT_DIRECTIVES` slot (the list lives in `permanent_directives` in the state; see `orchestrator/state.md`).
3. The Tech Lead checks each applicable directive in `review_code` (its own step in the template, with output in `DIRECTIVES_CHECKED`) and QA in the report (same field); a violation blocks approval.
4. A directive that can be checked by a machine becomes tooling (lint rule, hook, test, CI check) as soon as a violation appears — a second violation of the same rule is a process failure, not an agent failure.

---

## Critical Directive — New Requests Mid-Cycle

A `/dev-squad` cycle can run long (parallel subagents, multi-item batches, background execution). While it's in progress, the user may send a new message with a fresh feature request or change — often explicitly flagged as "don't let this interrupt what you're doing." Treat that as the default expectation even when not stated:

1. **Acknowledge in one line**, without stopping current work.
2. **Record the request** (local task list or backlog note) so it isn't lost.
3. **Finish the current batch to a real completion point** — merged, tested, backlog/tracker updated — not just "stop at the next convenient pause."
4. **Only then start the new request**, through the normal cycle: PO (the user) defines/confirms scope → UX review when the request has a user-facing surface → Tech Lead turns it into technical tasks → Senior Developer implements. Do not skip straight to implementation because the request arrived mid-session and feels urgent — the same phase discipline in `orchestrator/flow.md` still applies.

This keeps concurrent requests from fragmenting an in-flight batch into a half-finished state, and keeps the PO→UX→Tech Lead→Dev chain intact even under interruption pressure.

---

## Critical directive — No journey or rule outside the navigable prototype without authorization

**Failure mode:** the Dev meets a case the spec does not cover (network failure, conflict, partner error) and decides a behavior alone: a block, a message, a screen destination. The PO only finds out while testing, and the rework costs more than the question would have.

When the project has an **approved navigable prototype**, it is the source of truth for what gets built:

1. **No journey, business rule, message or block that is absent from the prototype (and from a PO-approved story) is developed** until the PO gets a plain product-language explanation (what the person sees and does, before and after, why the rule exists, alternatives, recommendation) and answers with explicit authorization. Silence is not authorization.
2. **Dev and Tech Lead do not decide product.** Whatever the spec does not cover goes to the PO through the Orchestrator (`po-proxy/protocol.md`); the affected part waits, the rest continues. Technical protections invisible to the user (rate limit, logging, idempotency) follow the project pattern, but any effect the person can notice (block, text, screen) is a product decision.
3. **A demonstrable change that is not yet in the prototype** (prototype limits may prevent some, e.g. real infrastructure failures) follows this order: adjust the prototype → PO approves → beta version → official version → only then the Dev implements code and tests. The Orchestrator does not dispatch the implementation before the PO's OK on the prototype.
4. **Backend changes with no visible effect** (new column, internal operation) may proceed in parallel; whatever depends on a screen waits for the prototype.
5. In QA and Tech Lead audits, **implemented behavior that is in neither the prototype nor an approved story is a finding** (high severity), even if it looks sensible.

---

## Critical directive — A decision that diverges from the prototype becomes documentation, and the prototype's documentation follows

**Failure mode:** the team decides (with the PO) that the product behaves differently from the prototype, but the decision stays in chat or in code. The prototype, journeys and test scenarios keep saying the opposite; the prototyping skill (or another session) "fixes" the product back to what the prototype says, or QA tests the old rule.

Whenever the team decides the product must behave differently from the prototype (or from what the documentation says), **in the same cycle it is mandatory to**:

1. **Record in the product documentation** the context, explanation and decision (who decided, when, why, what it replaces), in product language, in a versioned place (decision log and the topic's rules document).
2. **Reflect it in the acceptance criteria/BDD** of the affected stories: the new rule becomes a testable scenario; the old scenario is removed or marked as superseded.
3. **If the prototype has documents that carry the rule** (user journeys, BDD, README, business rules, changelog), **change them too**, with a short dated PO or Tech Lead comment at the changed passage (suggested format: "PO decision on YYYY-MM-DD: what changed and why. Replaces: previous behavior."). Changing the prototype itself follows the prototyping skill, if there is one; changing only its documentation does not require creating a new document.
4. The Orchestrator **does not close the cycle** (nor declare delivery) until the divergence is recorded in all three places; QA checks it as an acceptance item.

---

## Critical directive — A security block requires a threat model, not a reflex

**Failure mode:** the team declares "needs Information Security approval" or "privacy risk" about anything involving personal data, without saying who could obtain what, with what proof. The PO loses time and scope stalls over a risk that does not exist, while the real risk (a credential that never expires, enumeration, data returned to someone who proved nothing) goes unnoticed.

Before classifying something as a security or privacy block, write the **threat model** in three lines: (a) who receives the data; (b) what proof they presented (a possession-bound, expiring credential such as a session cookie; a code sent to the owner; nothing); (c) what they already knew (the person receiving back what they typed themselves, on the device that proved possession, is not new disclosure). Rules:

1. **Returning to a person what they themselves provided, under a device-bound credential with an expiry, is not by itself a block**; the remaining risk is the credential (lifetime, absolute cap, scope), and that is the control to require.
2. **Another device** only receives data after a new proof (for example a code sent to the holder's contact), with an attempt limit and an expiry.
3. What is only **information** for the security team (the design, limits, residual risks) is communicated without becoming a delivery prerequisite; what is a **control** (limits, expiry, minimal scope, encryption) is implemented.
4. If the PO has already explained their threat model, **assess it technically and say what you agree with and what remains** (residual risk), instead of repeating the alarm or agreeing by reflex.

---

## Lifecycle

```
[1] Investigation      Senior Developer investigates → Tech Lead reviews plan
        ↓ approved plan
[2] Implementation     Senior Developer implements → local status: in-progress
        ↓ implemented
[3] Code Review        Tech Lead reviews → local status: in-review
        ↓ approved         ↑ fixes, up to 3 loops before PO escalation
[4] QA                 QA tests → local status: in-qa
        ↓ approved         ↑ bugs → developer fixes → back to Tech Lead
[5] Delivery Ready     local status: done → notify PO with QA report and delivery notes
[6] Merge + cleanup    merge, then remove the task's worktree and local branch if nothing is pending (no PO approval needed; see orchestrator/flow.md, Phase 5)
```

For phase details and decision rules, read `orchestrator/flow.md`.

---

## Skills and Tools Roles May Use

List only the skills and tools relevant to the mission:

**Commonly useful:**
- `spec-kit-setup` — constitution.md, spec.md, plan.md, data-model.md
- `task-management.md` — local backlog structure
- `qa-reports.md` — QA report structure
- Infrastructure/SRE skill of the environment, if any — infrastructure, CI/CD, cloud, deployment
- Stack skill (e.g. `dev-python`, `dev-ts-nest`, `dev-ts-react`, `dev-ts-angular`, `dev-go`) — **recommendation**, if the environment has one. Without it, follow current best practice from the most respected professionals and community for that stack (most used, secure, well-maintained libraries) and research it on the internet (WebSearch/WebFetch) before deciding
- `task-writing`, `security-verification`, `recall-directives`, `agent-memory` — when available: story format, secret/PII checks, recovering earlier directives, durable agent memory
- WebSearch and WebFetch — external technical references
- Read, Edit, Write, Bash — local code reading, editing, and execution

---

## Entry Checklist

- [ ] Identify the task source: local Markdown, inline user request, or repo spec.
- [ ] Read `task-management.md` before creating or updating backlog items.
- [ ] Read `agents/dev-senior.md`, `agents/tech-lead.md`, `agents/qa.md`
- [ ] Read `orchestrator/flow.md`
- [ ] Read `orchestrator/state.md`
- [ ] Load into the state (`permanent_directives`) the user's permanent directives for the project — constitution/`CLAUDE.md`/README, working-mode note, agent memory — each with the literal text and the date.
- [ ] Initialize internal state with `task_ref`, `task_context`, and `current_phase = investigation`
- [ ] Start the Senior Developer investigation mission.

## PO Defines Epics, Technical Team Refines Tasks

Planning starts with the PO defining high-level epics. The Orchestrator, in Tech Lead posture, refines each epic into technical tasks before development starts. Each task should include:

- Measurable acceptance criteria.
- Impacted files and modules when known.
- Technical decisions already made.
- Complexity estimate: small, medium, or large.

The Orchestrator creates or updates Markdown backlog files following `task-management.md` and asks the PO to approve the refinement before implementation begins.
