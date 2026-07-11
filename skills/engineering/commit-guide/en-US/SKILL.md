---
name: commit-guide
description: Guide a developer through staging one atomic, quality-gated conventional commit — never commits or pushes without explicit per-commit confirmation. Detects the project's stack and harnesses the matching dev-* specialist skill (dev-ts-angular, dev-ts-nest, dev-python-fastapi, ...) when one exists, then runs code-review against the diff. Use when the user asks to prepare, organize, or split a commit; says "commit guide", "stage this", "help me commit", "organize these changes into commits"; or when there are pending changes ready to become one or more commits.
disable-model-invocation: true
---

# commit-guide

Stage changes for one atomic conventional commit at a time. Never commit or push without the developer explicitly confirming that specific commit.

## 1 — Load project context

Read `AGENTS.md` or `CLAUDE.md`. Check the project's manifest (`package.json`, `pyproject.toml`, etc.) for its stack. Note established conventions before touching anything.

## 2 — Understand what changed

Run `git status` and `git diff HEAD`. Read carefully.

## 3 — Quality gate

### 3a — Detect the stack, harness the matching specialist

Identify the project's primary language, framework, and design patterns from its manifest and existing code (`package.json` dependencies, `pyproject.toml`, `nest-cli.json`, `angular.json`, and so on). Map what you find to the `dev-<lang>-<framework>` naming convention (Angular → `dev-ts-angular`, NestJS → `dev-ts-nest`, FastAPI → `dev-python-fastapi`, and any newer ones registered since). If a matching skill is installed in this project, invoke it now — its stack-specific rules (framework version compliance, forbidden patterns, testing conventions) take priority over generic advice for the rest of this gate. If it exists in `ai-dev-kit` but isn't installed here, tell the developer and suggest `ai-dev-kit skills install --skills <bucket>/<name>` — then continue the gate regardless; don't block on it.

### 3b — Verify

Detect and run the project's build, lint, and test commands. **Zero errors, zero warnings, zero test failures** — fix before continuing. If a failure is pre-existing and unrelated to the current diff, flag it explicitly and get the developer's acknowledgement before proceeding; never silently ignore it.

### 3c — Review the diff

Invoke the `code-review` skill against the current diff for correctness bugs and reuse/simplification opportunities, informed by whatever the specialist skill in 3a surfaced. Apply the fixes it finds in place — don't just list them. Report a short summary before proceeding to commit planning.

## 4 — Plan atomic commits upfront

Per-file: does this file have mixed concerns? If yes, note it must use `git add -p`.

List every commit in dependency order:
```
1. fix(scope): lowercase verb only
2. feat(scope): one verb, one concern
3. test(scope): related tests only
```

If a file's diff has genuinely ambiguous atomic boundaries — you cannot confidently tell which lines belong to which concern — invoke `grill-me` to resolve the split with the developer one question at a time. Don't guess.

## ⚠️ ATOMICITY CHECKPOINT — MANDATORY

Before staging ANYTHING, verify EACH commit:

**Verify each commit message:**
- [ ] Contains EXACTLY ONE verb (add, fix, remove, refactor — not "fix AND add")
- [ ] NO "and", "also", ",", ";", "/" in description
- [ ] NO multiple concerns (e.g., not "component logic + CI config")
- [ ] Changes single layer (logic OR test OR config, not mixed)

**If ANY checkbox fails: SPLIT into more commits. DO NOT PROCEED.**

Example violation: `fix(lead): remove payload and add isSaving` → SPLIT
- Commit 1: `fix(lead): remove redundant payload from POST /send`
- Commit 2: `fix(lead-detail): add isSaving guard to prevent duplicate saves`

## 5 — Stage

Specific files only. Use `git add -p <file>` for mixed-concern files.
Never `git add -A` or `git add .`.

Before staging: verify diff hunks match the commit's single concern.

## 6 — Confirm staged diff

`git diff --staged`. Verify output matches intention exactly.

## 7 — Suggest message and hand off

Format: `type(scope): lowercase-verb-only ≤80 chars`

Output the suggested commit message as plain text:

<!-- message begin -->
Commit N staged. Suggested message:
```
type(scope): description
```
<!-- message end -->

Then call AskUserQuestion with:
- question: "Tell me if you want to proceed or if you need adjustments for the current commit"
- header: "Next step"
- options: [{ label: "Proceed with commit using suggested message", description: "Commit now with the message above, then stage the next commit" }, { label: "Next commit", description: "I have committed manually, skip to next commit" }]
- The auto-added "Other" option serves as the adjustment input field.

If the user selects "Proceed with commit using suggested message": run `git commit -m "<suggested message>"`, then continue to the next staged commit.
If the user selects "Next commit": skip committing and proceed to stage the next commit.
If the user provides text via "Other": treat it as adjustment instructions and apply them before re-presenting step 7.

If last commit: output "All N commits staged." then call AskUserQuestion with the same question, replacing "Proceed with commit using suggested message" with "Commit and finish" and "Next commit" with "Done (committed manually)".

Commit message rules:
- Format: `type(scope): description`
- Types — pick the FIRST that fits, top to bottom:
  - `feat`: introduces new user-facing functionality; triggers a minor release
  - `fix`: corrects any broken or wrong behaviour — bugs, wrong UI appearance, incorrect output; triggers a patch release
  - `refactor`: changes code structure or logic with ZERO observable behaviour change — no new features, no bug fixes, no UI differences; does NOT trigger a release
  - `perf`: improves measurable performance with no observable behaviour change
  - `test`: adds or corrects tests only — no production code changes
  - `docs`: documentation files only
  - `style`: **whitespace and formatting only** — indentation, trailing commas, semicolons; zero logic or UI change; does NOT trigger a release
  - `ci`: CI/CD pipeline changes only
  - `build`: changes to the build system or bundler config
  - `chore`: any other maintenance that doesn't fit the above — dependency bumps, config tweaks, generated files
- Scope: single noun, no commas, no "and"
- Description: lowercase imperative verb only. No periods. ≤80 chars total.
- Body: only if WHY is non-obvious. Wrap at 100 chars. No WHAT.
- No Co-Authored-By. No trailing period.
