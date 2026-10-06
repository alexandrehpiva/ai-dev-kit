# Orchestrator — State Management and Communication Protocol

## Orchestrator internal state

The Orchestrator maintains and updates this state between each spawn. Keep it in context memory between calls to the Agent tool:

```
task_id: <id in the tracker or "inline">
task_context: <full task description>
current_phase: investigation | implementation | code_review | testing | completed
approved_plan: <Dev's plan approved by the TL>
branch: <branch name>
modified_files: <list of files>
po_decisions: <list of decisions made by the PO during the cycle>
ciclos:
  investigation: 0      # increment on each plan_returned from the TL
  code_review: 0       # increment on each APPROVAL: no from the TL
  qa: 0               # increment on each send back to dev from QA
issue_history: <accumulated list of problems reported by TL and QA>
```

**Update the state on every subagent return** before deciding the next spawn.

---

## Inter-agent communication protocol

All communication between agents goes through the Orchestrator. Agents do not communicate directly.

### Senior Dev → Tech Lead (technical questions)

When Senior Dev returns a filled `QUESTIONS_FOR_TECH_LEAD`:
1. Spawn Tech Lead with mission `answer_questions`, passing the questions
2. Tech Lead answers in `ANSWERS` and `DECISIONS_MADE`
3. Orchestrator includes the answers in Senior Dev's next spawn as `resolved_questions`
4. Record the `DECISIONS_MADE` in `po_decisions` of the internal state

### Any agent → PO (business questions)

When any agent returns a filled `QUESTIONS_FOR_PO`:
→ **Read `po-proxy/protocol.md` — it is mandatory before relaying to the user.**

### Tech Lead → Senior Dev (code review corrections)

When Tech Lead returns `APPROVAL: no`:
1. Increment `ciclos.code_review` in the state
2. Accumulate `CRITICAL_ISSUES` and `MINOR_ISSUES` in `issue_history`
3. Spawn Senior Dev with mission `fix`, passing the problems as `{problems}` and `source: Tech Lead`

### QA → Senior Dev (bugs)

When QA returns `FINAL_VERDICT: send back to dev`:
1. Increment `ciclos.qa` in the state
2. Accumulate `BUGS` in `issue_history`
3. Spawn Senior Dev with mission `fix`, passing the bugs as `{problems}` and `source: QA`
4. After the Dev returns: **return to Phase 3 (Tech Lead reviews)** — do not skip straight to QA

---

## General spawn rule

Every subagent receives in its prompt:
1. **Role and persona** — who it is and how it thinks (read the agent's file in `agents/`)
2. **Task context** — full description + task_id + history of relevant decisions
3. **This round's mission** — what needs to be done now
4. **Available skills and tools** — explicitly list the ones relevant to the mission
5. **Output contract** — the exact format of what it must return

The subagent **returns structured text**, it does not talk directly to the user. The Orchestrator processes it and decides the next step.

### Agent tool call

```javascript
Agent({
  description: "<Role> — <mission> for task #<task_id or title>",
  prompt: "<full prompt as per agents/<agent>.md>",
  subagent_type: "general-purpose"
})
```

The result returned by the Agent tool is the subagent's structured text. Parse the fields delimited by `---` to extract the values.
