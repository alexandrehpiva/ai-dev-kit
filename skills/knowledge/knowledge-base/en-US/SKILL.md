---
name: knowledge-base
description: >-
  Template and bootstrap for creating a custom shared Knowledge Base skill
  (short, cross-referenced Markdown notes, Obsidian-style) about an organization
  or product — not the KB itself. On first run: detect missing custom, create it
  via write-a-skill, uninstall this template from the project via ai-dev-kit CLI,
  install the custom, and use it thereafter. Also guides continuous KB growth
  with explicit user authorization and a security gate. Use when the user asks
  to "create a knowledge base", "build a KB skill", "knowledge base template",
  "document team business rules", "bootstrap knowledge base", "update the KB",
  or when no custom KB skill exists yet.
---

# knowledge-base — Template for a custom KB skill

This skill is **not** any company's knowledge base. It is the **mold**: the
pattern, scope gate, and flow to **generate a custom skill** (via `write-a-skill`)
pointing at the team's real notes repository.

When the custom skill already exists and is installed, **use the custom** to
read/write notes — do not keep operating from this template alone.

## Separation of concerns (CRITICAL)

| Destination | What it stores | Skill |
|-------------|----------------|--------|
| **Shared Knowledge Base** | Facts about the **team/product/organization** | **Custom** skill generated from this template |
| **Agent memory** | What the agent learns **about the developer** | `agent-memory` and/or `memory` (if installed) |
| **Developer's personal notes** | Journal, agenda, personal PKM | Outside these skills |

❌ Never mix: secrets/tokens, a single developer's machine paths, individual sprint tasks, or agent personal preferences into the shared KB.

---

## First-run detection (mandatory when this skill loads)

Before any note read/write, decide whether this project has completed bootstrap.

**It is a first run** if **any** of these is true:

1. No custom KB skill is installed under `.cursor/skills/` / `.claude/skills/` (no `SKILL.md` that declares itself the team's Knowledge Base — typically `*-knowledge-base`, `*-kb`, or the agreed name).
2. No local bootstrap marker (e.g. agent-memory entry / `AGENTS.md` / `CLAUDE.md` pointing at the custom KB skill).
3. Only the official `knowledge-base` template (bucket `knowledge`) is symlinked, with no matching custom.

**It is not a first run** if the custom is installed and identifiable → **stop using this template for operations**; load and follow the custom.

If first run → execute **Bootstrap flow (first run)** below, with **explicit user confirmation** on every destructive step (uninstall template, create files, install custom, write to the KB repo).

---

## Bootstrap flow (first run)

Fixed order. Do not skip. Do not write KB notes before step 5.

### 0. Bootstrap authorization

Ask whether the user wants to create the custom KB skill **now**. If not, stop and explain that this template alone does not operate an enterprise KB.

### 1. Inventory (ask what is missing)

Close via questions (one at a time if using `grill-me`):

- Organization/product name the KB covers
- Path or URL of the notes repository (create empty only if authorized)
- Folder layout (or accept `kb/services/`, `kb/repositories/`, `kb/business-rules/`, `kb/overview.md`, `kb/glossary.md`)
- Content language
- Custom skill kebab name (e.g. `acme-knowledge-base`)
- Install targets: `cursor`, `claude`, or both

### 2. Generate the custom skill with `write-a-skill`

Invoke **`write-a-skill`** and create a **custom** flat skill:

```
<storePath>/skills/custom/<kebab-name>/SKILL.md
```

The custom must include at least:

- `description` with triggers + org/product name
- Locate repo, reading, scope gate, writing, commit
- **Concrete** gate and folders
- Explicit split: agent-personal facts → `agent-memory` / `memory`
- **Continuous growth** section (below) + **Security gate**
- Instruction: once installed, the custom is the operational source of truth for the KB

### 3. Uninstall the `knowledge-base` template from the project (CLI)

In the **project/vault cwd** where the template is installed, remove the official template symlinks so day-to-day work does not keep loading the mold:

```bash
# Non-interactive — remove the official template (all targets, or filter with --target)
ai-dev-kit skills uninstall --skills knowledge/knowledge-base
# or, if installed by short name only:
ai-dev-kit skills uninstall --skills knowledge-base

# Optional: one target only
ai-dev-kit skills uninstall --skills knowledge-base --target cursor
ai-dev-kit skills uninstall --skills knowledge-base --target claude
```

If the CLI is unavailable, manually remove `.cursor/skills/knowledge-base` and/or
`.claude/skills/knowledge-base` **only** if they point at
`skills/knowledge/knowledge-base/...` in the store — and get user confirmation first.

⚠️ Do **not** delete the skill from the **store** (`ai-dev-kit`); only uninstall it from the
**project**. The template remains in the kit for other projects to bootstrap.

### 4. Install the custom into the project (CLI)

```bash
[ -d ".claude" ] && TARGET="claude" || TARGET="cursor"

ai-dev-kit skills install --skills custom/<kebab-name> --target "$TARGET"
```

If the user wants both cursor and claude, run install twice.

Confirm symlinks point at `<storePath>/skills/custom/<kebab-name>`.

### 5. Validate and switch to the custom

- Dry-run: locate KB repo, `pull`, read overview (or create overview **only with authorization**).
- From here on: **operate via the custom skill**, not this template.
- Record in agent memory: “team KB = custom skill `<kebab-name>`” so future sessions detect this is **not** a first run.

### Bootstrap checklist

- [ ] User authorized bootstrap
- [ ] Inventory closed
- [ ] Custom created via `write-a-skill` under `skills/custom/<kebab-name>/`
- [ ] Template `knowledge-base` uninstalled from the project
- [ ] Custom installed via CLI
- [ ] Symlinks verified
- [ ] Agent-memory marker written
- [ ] Further operations use **only** the custom

---

## Canonical KB pattern (what the custom must implement)

### Locating the repository

1. Check whether the KB repo/folder is already available.
2. If not, **ask** — never assume path/URL.
3. `pull` before reading.

### Scope gate — add a note only when **all** are true

1. About the **organization/product** the custom covers.
2. Serves the **whole team**.
3. Not already covered (link/extend).

### Writing

- One concept per file; short and direct.
- Cross-reference with `[[wikilinks]]` and `#tags`.
- Repos by team **URL**, never a single developer's absolute path.
- Lazy file creation; update glossary when terms appear.
- Commits: Conventional Commits in English (`docs:`, `feat:`, `chore:`).

### Note template (suggested)

```markdown
---
tags: [#<area>, #<concept>]
---

# <Short title>

<1–3 direct paragraphs. Link related concepts with [[other-note]] and #tags.>

## References
- Repo: https://github.com/<org>/<repo>
- Related: [[other-note]]
```

---

## Continuous KB growth (required in the custom)

The custom must instruct the agent to **grow the KB over time**, not only at bootstrap.

### When to propose an increment

When something learned during work passes the scope gate (new business rule, service contract, glossary term, repo map, integration constraint):

1. **Classify:** shared KB vs agent memory vs personal note.
2. If KB candidate → prepare a **proposed diff** (create/update note, tags, links).
3. **Ask for explicit user authorization** before any write to the KB repo
   (create/edit file, commit, push). No clear yes → do not write.
4. After approval: write the minimum; offer commit; **push only if the user asks**.

### Authorization ask (example)

> “This looks like a team-wide fact. I propose updating `kb/…` with [summary].
> May I write it? (no push)”

### What NOT to auto-increment

- Personal user/agent preferences → `agent-memory` / `memory`
- Secrets, tokens, sensitive internal URLs without user classification
- Unverified hypotheses — caveat or skip
- Anything the user asked to keep private

---

## Security gate (CRITICAL — template and custom)

Before proposing or writing any note:

| Check | If it fails |
|-------|-------------|
| Contains secret/token/password/API key/PII? | **Block.** Redact or move guidance to memory without the value |
| Contains a developer's absolute machine path? | **Block.** Use repo URL or documented team-relative path |
| Individual/task-only? | **Not KB** → agent memory or task tracker |
| Possible NDA / partner IP leak? | **Ask** for classification; when unsure, do not write |
| External repo write / push? | Only with explicit authorization in the current turn |

Never ask the user to paste secrets into chat “to document in the KB”.

---

## Anti-patterns

- Operating an enterprise KB from this template after first run
- Skipping template uninstall / custom install
- Writing to the KB without explicit authorization
- Copying another team's org/repo names into the public kit
- Mixing agent memory with KB (or the reverse)
- Assuming `github.com/<org>/…` without confirmation
- Silent commit/push to the KB repo
