# Orchestrator — Lifecycle and Decision Rules

## Status management

The Orchestrator updates the task status in the local Markdown backlog (or in the connected tracker):

| Cycle status | Frontmatter |
|---|---|
| `in development` | `status: in-progress` |
| `in technical validation` | `status: in-review` |
| `in testing` | `status: in-qa` |
| `ready for deploy` | `status: done` + "Delivery notes" section |

Edit the YAML frontmatter of the task's Markdown file. Read `task-management.md` for the path and format.

If the task is in a connected tracker (Jira, ClickUp, Linear etc.), update the status there. If the task exists only inline in the chat, omit status updates and inform the PO of each transition.

---

## Phase 1 — Investigation

**Owner:** Senior Dev (mission `investigate`)

### Steps

1. Spawn Senior Dev with mission `investigate` and the full task context
2. If the return contains `QUESTIONS_FOR_TECH_LEAD`:
   - Spawn Tech Lead with mission `answer_questions`
   - Include the TL's `ANSWERS` in the Dev's next spawn
   - Re-spawn Senior Dev to complete the investigation with the answers
3. If the return contains `QUESTIONS_FOR_PO`:
   - **Read `po-proxy/protocol.md` and relay to the user** (grill-me format: one question + recommendation)
   - Include the PO's answers in the Dev's next spawn
4. When Senior Dev returns `STATUS: investigation_complete`:
   - Spawn Tech Lead with mission `review_plan`

### Loop rule — plan review

- If Tech Lead returns `STATUS: plan_returned`: re-spawn Senior Dev to adjust the plan with `REQUIRED_CORRECTIONS`
- **Limit: 3 plan review cycles** — after the 3rd without approval, escalate to the PO before continuing

---

## Phase 2 — Implementation

**Owner:** Senior Dev (mission `implement`)

### Steps

1. Update the task status to `in development` (frontmatter or connected tracker)
2. Spawn Senior Dev with mission `implement`, passing:
   - `approved_plan` = `IMPLEMENTATION_PLAN` approved by the TL
   - `resolved_questions` = all decisions made so far
3. If the return contains `QUESTIONS_FOR_TECH_LEAD` during implementation:
   - Spawn Tech Lead with mission `answer_questions`
   - Re-spawn Senior Dev to continue with the answers
4. If the return contains `QUESTIONS_FOR_PO`:
   - **Read `po-proxy/protocol.md` and relay to the user** (grill-me format: one question + recommendation)
5. When Senior Dev returns `STATUS: implemented`:
   - Proceed to Phase 3

---

## Phase 3 — Code Review (Tech Lead)

**Owner:** Tech Lead (mission `review_code`)

If the project has separate staging/production environments, read
`orchestrator/branch-strategy.md` before opening the PR — the target is always
`develop`, never `main`.

### Steps

1. Update the task status to `in technical validation`
2. Spawn Tech Lead with mission `review_code`, passing:
   - `branch` = the Dev's branch
   - `files` = the Dev's `MODIFIED_FILES`
   - `dev_summary` = the Dev's `SUMMARY`
3. If `APPROVAL: yes`:
   - Proceed to Phase 4
4. If `APPROVAL: no`:
   - Spawn Senior Dev with mission `fix`, passing the TL's problems
   - After the Dev returns, **re-spawn Tech Lead to review again** — do not skip to QA

### Loop rule — code review

- **Limit: 3 cycles without approval** — after the 3rd, escalate to the PO:
  - Present the history of problems and ask whether they want to relax the criteria, change the approach or step in

---

## Phase 4 — Testing (QA)

**Owner:** QA (mission `testar`)

### Steps

1. Update the status in the tracker to `in testing`
2. Spawn QA with mission `testar`, passing:
   - `branch` = current branch
   - `files` = list of modified files
   - `implementation_summary` = summary of what was implemented
3. If `FINAL_VERDICT: approved for deploy`:
   - **Verify** the QA report in `qa-reports/` (local Markdown backlog — `qa-reports.md`)
   - Update the status to `ready for deploy` / Markdown `done`
   - Notify the PO: summary + **link to the QA report** for manual re-testing
4. If `FINAL_VERDICT: send back to dev`:
   - Update the status in the tracker to `in development`
   - Spawn Senior Dev with mission `fix`, passing the QA's `BUGS` with `source: QA`
   - After the fix: **return to Phase 3 (Tech Lead reviews)** — do not skip straight to QA

### Loop rule — QA

- **Limit: 3 cycles without approval** — after the 3rd, escalate to the PO:
  - Present the persistent bugs and ask how to proceed (accept with caveats? change scope? subset?)

---

## PO escalation rules

Escalate to the PO (via `po-proxy/protocol.md`) when:
- Any agent returns a filled `QUESTIONS_FOR_PO`
- Review cycles exceed the limit (3x)
- There is a business decision with no clear technical resolution
- There is an external blocker: infra, environment access, dependency on another team
- QA finds a bug in functionality outside the scope of the current task

**Never make business or scope decisions without the PO.**
