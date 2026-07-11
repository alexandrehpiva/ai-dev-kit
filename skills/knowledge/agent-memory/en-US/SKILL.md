---
name: agent-memory
description: >-
  Maintain the agent's long-term memory about a developer and their work in a
  knowledge repository — durable instructions, corrections, preferences, project
  facts, decisions, technical references, and chat-session records organized as
  a tree of small Markdown files with per-folder indexes. Use at the start of
  every iteration to load conduct rules and relevant entries, and whenever
  learning something durable; when the user says "remember this", "save this to
  your memory", "check your memory", "set up agent memory", "what do you know
  about X".
---

# agent-memory — Agent Memory in a Knowledge Repository

An agent without persistent memory repeats mistakes, re-asks settled questions, and loses the developer's standards between sessions. This skill governs a **memory tree**: what the agent learns from the developer's instructions, corrections, complaints, and decisions, stored as small Markdown files in a repository the developer designates.

> **Do not confuse** the agent's memory with the developer's own notes or the team's shared knowledge base. This memory is the agent's learning about how to serve this developer well. Team-wide facts belong in the shared Knowledge Base (a **custom** skill generated from the `knowledge-base` template); personal notes belong to the developer.

## Locating the memory root

Never assume a fixed path. Before reading or writing:

1. Check whether a memory root is already known in the current environment (a `memory/` folder in the repository or vault the agent is instructed to use, or a path given in persistent instructions such as `CLAUDE.md`/`AGENTS.md`).
2. If not, **ask the developer where the memory should live** (an existing knowledge repository, a dedicated repo, or a folder in the current project).
3. If the root exists but is empty, bootstrap the tree below and record the location in the project's persistent instructions so future sessions find it without asking.

## Critical directives (non-negotiable)

1. **Consult memory every iteration.** At the start of EVERY turn, read `memory/MEMORY.md` and open `memory/agent-conduct/` plus the indexes/entries relevant to the task. **Re-read even if already read in this session** — multiple chat sessions may run in parallel and new direction may have landed. Never assume last turn's reading is still current.
2. **Conduct first.** `agent-conduct/` (quality bar, working process, language) is mandatory and always relevant. Read it before planning or acting.
3. **Update over time.** Whenever the developer gives a durable instruction, corrects something, complains, or a stable project fact/decision emerges, **record it** (see "How to WRITE"). Stale memory is a failure.
4. **Efficiency under growth.** Memory grows. Keep files **small and atomic**, split into folders (a tree). Read the router plus only the needed indexes/entries — never the whole tree.
5. **No loss, no fabrication.** Never delete knowledge when reorganizing. Don't invent detail; mark `status: summary` for summaries only, `status: detailed` for verified content, `status: critical` for conduct rules.

## Structure (tree)

```
memory/
├── MEMORY.md              # root router: critical rules + category links
├── agent-conduct/         # CRITICAL: how to work for this developer (always read)
│   ├── INDEX.md
│   ├── quality-bar.md
│   ├── working-process.md
│   └── communication-language.md
├── sessions/              # records of significant chat sessions (what was done/decided)
├── feedback/              # point corrections and preferences
├── projects/              # state and facts of projects
├── reference/             # technical references and procedures
└── decisions/             # ADRs and durable choices
```

Each folder has an `INDEX.md` with one line per entry (link + short descriptor + `(detailed)`/`(summary)`). Each entry is a small file with frontmatter `name`, `type`, `status`, `source`. Prefer `.md`; `.txt` and images are allowed when a diagram says more than text.

## How to READ (every turn)

1. Read `memory/MEMORY.md` (small).
2. Read the files in `agent-conduct/`.
3. Identify the categories relevant to the task and open their `INDEX.md`.
4. Open only the entries that matter.
5. If planned work contradicts memory, **memory wins until the developer says otherwise** — and if they do, update the memory.

## How to SEARCH

- Start with the `INDEX.md` files (cheap scan).
- Broad textual search: `grep -ri "<term>" memory/`.
- Filter by category via the `type:` frontmatter field.

## How to WRITE (update memory)

Triggers: a durable instruction or preference; a correction or complaint (goes to `feedback/`, or `agent-conduct/` if about the agent's conduct); a stable project fact (`projects/`); a reusable reference (`reference/`); an architecture decision (`decisions/`); a significant session worth recording (`sessions/`).

Before creating an entry, ask: *does this serve only the current task, or could it help something entirely different later?* Task-bound facts go to `projects/`; transferable knowledge goes to `reference/` written **generically and reusably**.

<entry-frontmatter>
---
name: <slug>
type: agent-conduct | session | feedback | project | reference | decision
status: critical | detailed | summary
source: <session/date or origin>
---
</entry-frontmatter>

Procedure: pick the right category; create/update one **small, atomic** file; update the folder's `INDEX.md`; **never duplicate** (edit the existing entry if the topic exists); promote `summary` → `detailed` when verified content lands. **Never store secrets, tokens, or credentials.**

## Session records (`sessions/`)

For sessions with durable outcomes (decisions made, things built, direction changed), write one small entry: date, what was asked, what was done, decisions, and open threads. Skip trivial sessions. Extract anything durable into the proper category (`feedback/`, `projects/`, ...) — the session record points to it, not the other way around.

## Consolidation

Periodically (or when a folder bloats): merge duplicates, fix obsolete facts, trim indexes — **without losing any fact**.

## Checklist

- [ ] Located (or bootstrapped) the memory root without assuming a path.
- [ ] Read `MEMORY.md` + `agent-conduct/` this turn (even if read earlier this session).
- [ ] Opened only the relevant indexes/entries (efficiency).
- [ ] Recorded durable learnings in the right category and updated the INDEX.
- [ ] No duplication, no fabrication, no secrets stored.
