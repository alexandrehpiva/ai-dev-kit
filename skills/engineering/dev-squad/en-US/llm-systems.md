# Products with an LLM or natural language — fixing, system knowledge and QA

Read before specifying, implementing, reviewing or testing a task in which the product contains an LLM or interprets natural language (assistant, extraction from free text into a structured rule, classification, generation of options for the user). It applies to any such system.

## Failure mode diagnosis

- Text interpretation becomes a regex, word list or word count in code. Each new case demands a new exception until the detector passes the tests: it is judging language and will be wrong outside them.
- The product's model offers an option the system cannot honor; the user picks it and lands in a dead end ("contact support").
- QA runs a scenario once, it passes, and it is declared fixed; on the next run the result changes.
- The fix is validated with "reached the end of the flow", without checking the calculated value or the text the user read.

## 1. Right layer

- **Natural-language interpretation goes to the LLM's prompt and context.** Code keeps calculation, structure and flow.
- Deterministic checks only for what is determinable: JSON shape, numbers, literal equality, punctuation. Do not validate language with regex, word lists or counts.
- **Alarm signal:** a deterministic detector that needs a per-scenario exception to pass the tests. Remove it; do not patch it. An exception is a recorded PO decision, never the Dev's initiative.
- **The same applies inside the prompt:** a trigger-word list or a specific condition in the instruction to the model is disguised determinism and can lead it to err where the rule did not foresee. When the model gets the obvious wrong, find and remove the prompt instruction that induced the error and give it facts about the system (§2), not a word rule. A quote from the user or client does not go into a product prompt.
- Tech Lead: send back a plan or code that decides language in code, even if it passes the tests.

## 2. System knowledge for the product's LLM

The model that generates options and answers for the user needs an organized asset of what the system does and does not do: available data, features that do not exist, what blocks a process. Rules:

1. Before offering an option, the model checks that the system honors it; if not, it does not offer it and explains why to the user.
2. Never offer something that will later have to be undone.
3. The asset is versioned with the code, lives in the context the model receives, and is updated when a feature changes. A missing or stale asset is a review finding.

Test question for the Dev, the Tech Lead and QA when facing a strange option: does a feature in the system carry it out? If not, the defect is the model's missing context, not a "user decision".

## 3. No dead end in the user's flow

A system defect does not end in "contact support". Recovery first: try again, explain what happened, offer what is possible. Handing off to a person comes only after the user insists on something infeasible, showing what would remain and why it is not possible.

## 4. Diagnosis by reproduction

Reproduce the cause **without calling the model** when possible: run the engine or functions with the case's real data. What was not reproduced goes in the report as INFERENCE, never as a confirmed cause. The orchestrator adopts the cause only after that (`orchestrator/squad-briefing.md`, separate diagnosis section).

## 5. Fixtures, generators and examples

- Realistic test data: no combination that is impossible in the domain, and the literals the rule uses are exercised.
- Examples in prompts and tests are neutral and **never copied from the acceptance cases** (overfitting: the product passes the cases and fails the neighboring one).

## 6. QA for systems with an LLM

1. **Repeat:** the result varies between runs. An unstable scenario runs at least 2 to 3 times before being declared fixed; record how many passed.
2. **Record the literal the end user sees**, round by round, and the time of each round. The QA report (`qa-reports.md`) carries these fields.
3. **Check calculated values against the expected ones**, not only "the flow finished".
4. **Separate a product defect from a test-tool artifact** (script, driver, environment) before opening a bug.
5. **Do not spend extra runs on a known blocker:** a scenario blocked by an already recorded defect stays pending; it is not repeated.

## 7. FAILED criteria for what the end user perceives

Each item below fails the scenario. Severity is a floor: the orchestrator reclassifies upward when QA underestimates.

| What the end user perceives | Minimum severity |
|---|---|
| Infeasible option or one that leads to a dead end; effect described wrongly; silent default value; a condition that vanished without notice | `SEVERE` (leads the person to decide or believe something wrong) |
| Repeated question; obvious or context-free question; technical leak (error code, internal name, raw JSON); time above the agreed limit | `MEDIUM` |

None of them is `MINOR`. An effect described wrongly to the user is not an "imprecise message".
