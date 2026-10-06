# QA Reports — Markdown Reports

**Mandatory:** every dev-squad QA cycle that uses the local Markdown backlog **must** generate a report in this format and location. The PO uses these files to **see** what was tested and to **re-test** manually.

---

## Location

```
{NotesRoot}/{ProjectName}/qa-reports/
├── README.md
└── {YYYY-MM-DD}/
    └── {TASK-ID} - {short-name} - {status}.md
```

**Example:**
`{NotesRoot}/ExampleApp/qa-reports/2026-06-14/TASK-03.1 - Login and session - approved.md`

---

## File naming

```
{TASK-ID} - {short task name} - {approved|bugs|partial}.md
```

- `approved` — all of the task's BDD scenarios passed
- `bugs` — there are open bugs; send back to dev
- `partial` — external blocker (DNS, access); pending scenarios listed explicitly

---

## Mandatory report template

QA **copies the task's BDD scenarios** and fills in each one. The PO must be able to re-run them without reading the chat.

```markdown
---
tags: [backlog, {project-kebab}, qa-report]
task: "[[TASK-xx.x - Name]]"
epic: "[[EPIC-xx - Name]]"
status: approved | bugs | partial
tested_at: {YYYY-MM-DD HH:MM}
tested_by: QA (dev-squad)
branch: {branch or N/A for infra}
commits: [{hash}, ...]
environment: dev | staging | production
---

# QA Report — {TASK-ID}: {Name}

## Executive summary

{2–4 sentences: what was tested, overall result, blockers}

## Prerequisites for re-test (PO)

{Numbered list — what the PO needs to have/configure before re-testing}

## Commands and tools used

\`\`\`bash
# exact copyable commands
\`\`\`

## BDD scenarios (copied from the task)

### Scenario 1: {title from the task}

**Given** ...
**When** ...
**Then** ...

| Re-test step (PO) | Command / action | QA result | PO result |
|--------------------|----------------|--------------|--------------|
| 1 | `curl ...` | ✅ 200 | ☐ |
| 2 | ... | ... | ☐ |

**QA evidence:** {summarized output or observation link}

---

### Scenario 2: ...

(repeat for **all** of the task's scenarios + edge cases tested)

## Automated tests

| Suite | Command | Result |
|-------|---------|-----------|
| ... | ... | pass / fail / N/A |

## Bugs found

(empty if approved)

### [SEVERITY] Title

- **Reproduction:** numbered steps
- **Expected:** ...
- **Actual:** ...
- **Severity:** CRITICAL | SEVERE | MEDIUM | MINOR

## Pending / blocked scenarios

| Scenario | Blocker reason | Owner |
|---------|-------------------|-------------|
| ... | DNS not propagated | PO (Cloudflare) |

## Final verdict

- [ ] **Approved for deploy** — task can move to `done`
- [ ] **Send back to dev** — bugs above
- [ ] **Partial** — wait for PO/external unblock

## PO checklist (manual re-test)

- [ ] Scenario 1 re-tested by me
- [ ] Scenario 2 re-tested by me
- [ ] Accepted as done
```

---

## QA rules

1. **Never** approve without a report saved in `{NotesRoot}`
2. **Every BDD scenario** of the task appears in the report — even if blocked (mark as pending)
3. Commands must be **copyable** — full paths, URLs, headers
4. The **PO result** column leaves empty checkboxes for the PO to fill in
5. After saving the report: the Orchestrator commits in the repository that holds `{NotesRoot}`:

```bash
cd "<repository that holds {NotesRoot}>"
git add "{NotesRoot}/{project}/qa-reports/"
git commit -m "qa({project}): report TASK-xx.x — {approved|bugs|partial}"
```

6. Link the report in the task's **Development notes** section (`[[qa-reports/...]]`)

---

## Integration with the cycle (flow.md Phase 4)

After the QA spawn returns `STATUS: approved`, the Orchestrator **verifies** that the report file exists before marking the task `done`.

If `partial`: the task stays `in-qa` or goes back to `in-progress` depending on the blocker; the PO is notified with a link to the report.
