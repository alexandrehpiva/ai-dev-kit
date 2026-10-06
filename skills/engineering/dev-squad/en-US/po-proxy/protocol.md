# PO Proxy — Question Relay Protocol to the User

## When to use

Use this protocol when:
- Any subagent returns a filled (non-empty) `QUESTIONS_FOR_PO`
- The Orchestrator needs a business decision to continue
- Review cycles exceeded the limit and the PO needs to step in
- There is an external blocker with no possible technical resolution

---

## Step 1 — Collect all questions of the cycle

Before asking the user, check whether other subagents also have pending questions in the same cycle. If so, group everything into a single interaction with the PO — never run multiple separate interactions for questions from the same cycle.

For each question collected, record:
- **Origin:** which agent asked (Senior Dev / Tech Lead / QA / Orchestrator)
- **Question:** the question itself
- **Impact:** what changes depending on the answer
- **Urgency:** blocks now | can be resolved later

---

## Step 2 — Prepare the presentation for the PO

The PO in this flow is the **real user** (the human user). Questions must follow the **grill-me** protocol: **one question at a time**, with a **team recommendation** and brief reasoning — never a list of loose questions without context.

Use `AskUserQuestion` when there are discrete options; otherwise, text in grill-me format:

> **Context:** {1 sentence}
> **Question:** {just one}
> **Team recommendation:** {preferred option + why}

Additional rules:

- **Do not expose internal vocabulary** — the PO does not need to know about "spawn", "Orchestrator", "subagent", "mission"
- **Speak like a PM or the team's secretary** — "the team has a few questions before continuing"
- **Be concise** — minimum necessary context + direct question
- **Maximum of 4 questions per interaction** — if there are more, prioritize the ones that block now

### Text template before AskUserQuestion

> The team has reached some questions that need your decision before continuing:

### Options template in AskUserQuestion

Each option must contain a real decision alternative, not just a confirmation. Example:

```
Question: "How should the system behave when the user does not have permission for this action?"
Options:
- Return 403 with a generic message (without exposing details)
- Return 403 with a description of what is missing
- Redirect to the plan upgrade screen
- Other (free field)
```

If the question does not have well-defined options, use an open format with "Other" as an escape.

---

## Step 3 — Process the PO's answer

1. Map each answer to the originating question and to the agent that asked
2. Format the answers as `resolved_questions` for the next spawn:

```
PO DECISIONS:
- [summarized question]: [PO's answer]
- [summarized question]: [PO's answer]
```

3. Record the decision in the conversation log and, if there is a task_id, add it as a comment on the task through the connected tracker (for traceability)

---

## Step 4 — Continue the cycle

After receiving the PO's answers:
1. Return to `orchestrator/flow.md` and identify which phase the cycle was in
2. Re-spawn the correct agent, now with the answers included
3. If the PO answered with a scope change or cancellation, tell the user what will change

---

## Escalation by cycle limit

When the Orchestrator escalates to the PO for having reached the cycle limit (3x without resolution):

Present to the user:
- The recurring problem (what the Tech Lead or QA keeps pointing out)
- What the Senior Dev is doing in each attempt
- The options to unblock:
  1. Change the technical approach (Orchestrator instructs the Dev with new direction)
  2. Accept the current state with documented caveats (tech debt)
  3. Reduce the scope (deliver a functional subset now)
  4. Pause and escalate to a human on the real team

Never make this decision alone — always bring it to the PO.
