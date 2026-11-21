# Orchestrator — Squad common briefing and evaluating what roles deliver

Domain asset. Read it **before the first spawn** of a cycle, and again when the user gives a new directive mid-work. The general material on subagents (self-contained briefing, safe parallelism, evidence, usage limits, questions to the owner) lives in the `subagent-orchestration` skill; this file holds only what is specific to the squad.

## Failure mode diagnosis

- A role launched with only persona + task ignores a directive given twenty messages earlier, repeats another role's work, and "completes" what it does not know with assumptions.
- The orchestrator relays a role's report as fact; the result is only disproved when the user tests.
- Diagnosis and fix in the same spawn: the role fixes the first plausible cause and the report calls it the "root cause".
- One fix at a time, each rebuilding the environment: slow, and defects that only show up in the sum stay hidden.
- A role that launches its own subagents without applying to them what the orchestrator applies to it: the error comes back unfiltered.

## 1. Common briefing in a file

Create a single file, read by **every** role before anything else (each role's prompt carries the path in the `COMMON_BRIEFING` slot plus the role template; see `orchestrator/state.md`). Sections:

1. Project goal and what "done" means for the user.
2. Where the code is and which is the integration base (branch or worktree).
3. How to create the isolated area, install dependencies and run tests (exact commands).
4. The user's permanent directives, with literal text and date (the same as `permanent_directives`).
5. Prohibitions (what the user vetoed and what must never happen without an order: push, merge, deploy).
6. Output format the orchestrator expects.
7. Map of what each role does in parallel and who owns which files.
8. Environment gotchas (e.g., the current directory does not persist between shell calls; path variables the tests expect). When a role fails because of one, the next briefing already carries the fix.
9. Recursion clause (item 7 below), copied verbatim.

Test: can a role that reads only the briefing and the task tell where to work, what it must not do, and how to prove it is done?

## 2. Literal excerpts of the user's request

Besides the orchestrator's instructions, each role's prompt carries, in quotes and marked as the user's words, the excerpts of the request that motivate **that** task (a `USER_REQUEST` section of the briefing or the prompt). A paraphrase loses nuance; the literal text disambiguates intent and helps the role fill in what the instruction did not foresee.

- Choose the excerpts that explain the why or the constraint, not the whole request.
- Do not alter or cut in a way that changes meaning; mark what was omitted.
- Remove secrets and personal data before pasting; the literal text is not a license to leak.

## 3. A new directive mid-work

1. Record the literal text and date in the common briefing (dated section) and in `permanent_directives` (and in the agent's memory, if the environment has one).
2. **Resend it to the roles already running**, through a continuation message, not only to later spawns: whoever works from the old briefing violates the new rule without knowing.
3. Before launching a batch in a long or compacted session, recover the directives from the history (`recall-directives`, when available) and check that the briefing is current.

## 4. Diagnosis separate from the fix

For a bug with a non-obvious cause (reported by QA, the Tech Lead or the user):

1. **Diagnosis spawn**, read-only: reproduces with evidence (see `llm-systems.md` for reproducing without calling the model), changes no code, returns the cause with FACT vs INFERENCE.
2. **The orchestrator evaluates the cause**: does it match the source (original text, real data, test output)? If not, send it back to the diagnosis with the objection, or explicitly disagree.
3. **Fix spawn** (`fix`) with the **adopted** cause in the prompt; if the orchestrator disagreed with the diagnosis, its revision is written into the prompt.

## 5. Batch integration

When several fixes are ready: merge them into the integration base, run the suite, rebuild the environment **once**, and test together. Only the orchestrator rebuilds the shared environment, and never during a test round. A shared resource with a limit (same test login, same quota, same local environment) caps concurrency: serialize what conflicts.

## 6. Diff audit before the merge

The orchestrator reads the diff (not only the report) looking for what the user vetoed and what the convention skills (`code-naming-conventions`) forbid: deterministic logic over natural language, magic strings, examples copied from test cases, error handling that reads message text. To make the reading feasible, the briefing tells the Dev to list the **sensitive lines** itself (e.g., every new regular expression over text, every new cap or default) with a justification, in the `SENSITIVE_LINES` field. A finding goes back to the Dev before the merge, not after.

## 7. Evaluate, request changes, recursion

- **Do not relay a role's report as fact.** Open the diff, run the key tests, check the critical claims (e.g., "no calculated value changed" -> check the regression test that proves it).
- **Reclassify severity** when the role underestimates, especially what the end user sees (see the table in `llm-systems.md`).
- **Disagree** when the diagnosis or proposal does not match the source, including when the role wants to ask the user something the original text already answers.
- **Distrust test specifications written by the team** ("invented" ambiguity, stale expected results): validate against the source text and, when in doubt, against the user.
- **Review cycle:** if it is not good, ask the same role for the change (continuation message) or launch another with a corrected briefing, until it is good enough. The 3-cycle limits in `orchestrator/flow.md` still apply for escalating to the PO.
- **Recursion.** Clause to copy into the briefing: "If you launch subagents, apply to them what I apply to you: common briefing, literal excerpts of the request, evaluation of what they deliver, change requests until it is good. You answer for what they deliver; do not relay their report without checking it."

## 8. File ownership and workspace

Split parallel work by file ownership, each role in its own worktree. Never `git stash` (the stack is shared across worktrees). One temp folder per agent (one role overwrote another's script in a shared folder). In long autonomous work, write state to disk and use `session-limit-guard` (when available) to resume after the usage limit.

## Orchestrator checklist before launching a role

- [ ] Does the common briefing exist and carry the latest literal directives?
- [ ] Does the prompt carry the literal excerpts of the request that motivate this task?
- [ ] Is it clear who owns which files among the parallel roles?
- [ ] For a fix with a non-obvious cause: was there a separate diagnosis and an adopted cause?
- [ ] Is the recursion clause in the briefing?
