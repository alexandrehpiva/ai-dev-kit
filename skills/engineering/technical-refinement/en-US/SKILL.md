---
name: technical-refinement
description: >-
  Guide for conducting technical refinement: investigate a task, analyze the
  related repositories, make every technical decision, and draft subtasks
  with full completeness before any line of code. Covers the investigation
  flow (task context, code, service chain), task structure decisions (when
  to split, which board, how to link) and the vertical delivery-slicing
  principle. Use when the user asks to "refine this task technically",
  "create technical subtasks", "figure out what needs to be done" to
  implement something, or investigate repositories before writing tasks.
disable-model-invocation: true
---

# technical-refinement — Agent Guide

Refining means eliminating every implementation uncertainty before any code exists. A subtask is only ready when it leaves no architecture, contract, or naming decision for the implementer to make.

For **task-tracker access commands** (fetch, create, comment), use whatever integration is available in the current environment. For **writing standard, acceptance criteria, and wave numbering**, see `task-writing`. To **close open decisions**, run `grill-me` — this coupling is intentional (see Step 4). For **dense code investigation** where current behavior isn't obvious, activate `study`.

When a user instruction contradicts anything here, the user instruction wins.

---

## 1. When to apply

Apply when the user asks to "refine this task technically", "create technical subtasks for X", "figure out what needs to change in the code to implement this", or any variation of investigating repositories before writing tasks.

**What this skill produces:** tasks with every technical decision already made — files, paths, field names, API contracts, error behavior, environment variables — with no loose end left for the dev to decide during development.

---

## 2. Cross-cutting principle — slice by delivery (vertical cut)

**Hard rule:** every task/delivery must be a **vertical slice** — it reaches the UI, is **validatable by product**, **deploys on its own**, and closes against that task's acceptance criteria (BDD). Refining is, above all, deciding the **delivery map**; subtasks come only after that.

Avoid the horizontal cut (slicing by service/layer: "backend subtask", "frontend subtask") — it produces long chains of invisible work that product can't validate until the very end.

When refining an epic with several parent tasks:

1. **Draw the delivery map first.** Each delivery is a slice product can see and approve (a screen, a click, an observable effect), aligned to that task's BDD.
2. **A piece belongs to the delivery where it first becomes demonstrable.** If a component has no "home" (no screen/context where product can validate it in that delivery), it doesn't belong there.
3. **Pulling work forward is allowed** when a thin slice of later work needs to exist for the current delivery to make sense — record this explicitly in the subtask.
4. **Bundle** when two pieces are only demonstrable together (e.g., a screen + AI-driven processing). Alternative: ship the piece **stubbed behind a feature flag** and "light it up" later.
5. **Enabling mechanism:** feature flag on the consumer + producer service always additive/backward-compatible — the backend can ship at any time without exposing anything; the frontend lights the feature up once the slice is ready.

When the slicing isn't obvious, close it via `grill-me` before drafting the subtasks.

---

## 3. Investigation flow

1. **Read the task in full** — body, comments (refinement decisions often live there, not in the body), and attachments. If there's a video/screen recording, transcribe it before continuing — demos frequently show the exact points of change that the text doesn't describe.
2. **Identify the repositories involved.** Resolve each repository by its GitHub location, never by a local machine path — use the team's project map (monorepo README, framework repo map, or whatever the team maintains). For deep architectural knowledge of a specific repository (folder structure, endpoint patterns, auth conventions), consult the `knowledge-base` skill if installed, or the repository's own code/docs, before deciding where each piece lives.
3. **Study the repository's state before reading code.** Don't assume a fixed branch. Identify the repo's branch pipeline (GitFlow with `develop`+`main`? trunk-based?), which branch maps to which environment, and whether the development branch carries partial features relevant here. Close the doubt via `grill-me` if needed; then `checkout` the correct branch + `pull` **before** reading any code.
4. **Locate the code** with a broad search for the term/identifier from the task, then narrow down to files. Never decide based only on the matched line — read at least 15–20 surrounding lines to understand the component, how the value is used, and any nearby conditional logic.
5. **Follow the service chain** for changes involving new endpoints or API consumption — map who calls whom and through which proxy before deciding where each piece lives. **Ownership criterion:** concentrate complexity in the component that **owns the context** and keep the **consumer's contract minimal and stable**; this is a heuristic, not a law — when the trade-off isn't obvious, bring the options to `grill-me`.
6. **Make every technical decision** before drafting any task (see checklist §7).

---

## 4. Decisions that cannot stay open

- **Shared contract.** When changing an endpoint/contract already consumed by other services, assess whether the change is **additive (backward-compatible)** or **breaking**. Additive proceeds normally. Breaking requires `grill-me` with the user (impact on consumers, migration strategy) before drafting — never assume changing a shared contract is safe.
- **Naming.** Hard, project-agnostic rule: code identifiers (variables, classes, functions, **enums**) are always in **English**. The language of strings/comments **depends on the repository** — study the existing convention before writing, don't impose one. Storage paths and keys: English, no language mixing, organized by **stable domain** (an initiative/moment name is not an organizing criterion), each file with its **own id**.
- **End-of-life component.** When you run into a legacy component slated for deprecation, design the new solution **decoupled/agnostic** from it from the start — use it at most as a reference for mechanics. Temporary coupling only as explicit, dated technical debt (why it's temporary, where it should live, what's needed to migrate). Close the decision via `grill-me`.
- **No architecture, contract, or naming decision can stay "to be defined"** in a subtask. If it can't be decided with the information available, close it via `grill-me` before writing.

---

## 5. Task structure

**Authorship rule:** a top-level task (US/epic) is written **only by product**. Tech only creates: (1) technical-debt tasks, (2) urgent-channel tasks, (3) subtasks inside a product US. Never create a "normal" top-level task — when in doubt, ask.

| Situation | Action |
|---|---|
| Technical detail implementing an existing US | **Subtask** of that US |
| Technical debt / architectural improvement independent of the epic | **Technical-debt task** |
| Multiple repos with different lifecycles (fix now vs. restructure later) | Short-term subtask on the US + technical-debt task(s) |

Merge tasks when the changes are conceptually the same delivery and land in the same PR/sprint. Split when they involve different lifecycles, dependencies on each other, or independent delivery.

**Protecting the parent task:** never change the parent task's content without explicit confirmation in the current prompt. The parent task's wording expresses **product intent**, not a literal spec — it may be technically loose (e.g., "return 404 on error" when the correct taxonomy uses 400/404/422). Decide the technically correct behavior in the subtask and **flag the divergence** to the user/product, without ever rewriting the parent task.

**Sequencing:** when tasks have a technical dependency, document the prerequisite explicitly on the dependent task — never leave it implicit.

---

## 6. Anti-patterns

| Anti-pattern | The correct approach |
|---|---|
| Reading code without studying branch state / without pulling | Study the branch pipeline, close doubts via `grill-me`, pull before reading |
| Literally following a technically loose/wrong parent task | Decide the correct behavior in the subtask and flag the divergence — without changing the parent task |
| Coupling the solution to an end-of-life component | Design decoupled from refinement onward; legacy only as reference; explicit, dated debt |
| Assuming a shared contract change is safe | Assess consumers and additive-vs-breaking; breaking → `grill-me` |
| Naming a variable/class/function/enum in the local language | Code identifiers are always in English |
| Leaving an architecture/contract/naming decision "to be defined" | Close everything via `grill-me` before drafting — full completeness |
| Referencing repositories by a local machine path | Resolve via GitHub (team project map) — this framework is shared |

---

## 7. Checklist before creating technical tasks

- [ ] Parent task fully read, including interpreted videos/attachments
- [ ] Relevant repositories identified via GitHub; branch state studied and doubts closed via `grill-me`; correct branch pulled before reading code
- [ ] Code located with context read (±15 lines)
- [ ] Service chain mapped; ownership of each piece assessed
- [ ] All files to change listed with exact paths
- [ ] API contracts defined (URL, method, auth, fields, errors)
- [ ] Shared contract assessed (additive vs. breaking); breaking closed via `grill-me`
- [ ] End-of-life component treated as reference, not dependency
- [ ] Naming applied (identifiers in English; string language per repo convention)
- [ ] Environment variables identified and named
- [ ] Failure behavior explicit for each consumer
- [ ] Migrations/fixtures documented if needed
- [ ] Task structure decided (subtask vs. task, sequencing)
- [ ] Dry-run presented to the user before creating any task
- [ ] After creation: traceability recorded on the origin task (links to derived tasks)
