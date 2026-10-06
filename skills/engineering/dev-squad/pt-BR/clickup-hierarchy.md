# ClickUp hierarchy — epics, US, and technical subtasks

Read this asset before creating or restructuring any task in a ClickUp Space. It
defines the shape of the board — see `task-management.md` for the local Markdown
backlog equivalent, and the `task-writing` skill (`US-FORMAT.md` → "Hierarquia") for the
general principle this asset makes concrete for ClickUp specifically.

---

## The rule

**Epic and US live at the same hierarchical level — both are product stories, at different
granularity — connected by a ClickUp *link*, never by `parent`.** The `parent` slot
(subtask) is reserved for one purpose only: the technical breakdown the Tech Lead creates
**inside** a US that the PO already wrote and approved.

| Item | ClickUp shape | Who authors it |
|---|---|---|
| Epic | Top-level task in the backlog list | PO (product) |
| US | Top-level task in the same list, **linked** to its epic | PO (product) |
| Technical subtask | Subtask of the US it details | Tech Lead |

**Why not `parent` for epic↔US:** a subtask is buried inside its parent in most ClickUp views
— it doesn't surface as its own card in board/list views the way a top-level task does, and
the ClickUp API does not support clearing `parent` on an existing task (`PUT` with
`"parent": null` is silently ignored — verified against the live API, not assumed). If a US
is created as a subtask by mistake, the fix is to **delete and recreate** it as a top-level
task, not to try to unparent it in place.

---

## Creating the link (epic ↔ US)

Use the ClickUp v2 task-link endpoint — it creates a bidirectional relation distinct from
both `parent` and `depends_on`:

```bash
# The key comes from the environment (e.g. CLICKUP_API_KEY); never echo it
curl -s -X POST "https://api.clickup.com/api/v2/task/{US_ID}/link/{EPIC_ID}" \
  -H "Authorization: $CLICKUP_API_KEY" -H "Content-Type: application/json"
```

No body needed. Either task ID can be first — the link is symmetric. The response echoes both
tasks with their `linked_tasks` populated. If a connected ClickUp tool (MCP/CLI) can create task links, prefer it; otherwise use `curl` directly (never echo the key to chat/logs).

## Order of operations for a new epic + its US's

1. Create the epic as a top-level task in the backlog list.
2. Create each US as a **top-level task in the same list** — not with `parent` set to the
   epic.
3. Link each US to its epic via the endpoint above.
4. Technical subtasks (Tech Lead phase) are created afterward, with `parent` set to the **US**
   they detail — never to the epic directly.

## Technical subtasks (Tech Lead phase)

Once architecture is settled, the Tech Lead creates subtasks under each US following
`US-FORMAT.md` (subtask row of the "Regras de aplicação por tipo" table): one subtask per
layer/dependency (backend, frontend, infra), each independently pickable. Apply
`lean-writing.md` and `readability.md` before publishing. Use blocking dependencies
(`depends_on`) between subtasks only for genuine hard blockers — see the "quando cadastrar
bloqueio" criteria pattern in `lean-writing.md`'s Dependências guidance; two subtasks that can
be built in parallel against a shared contract should not block each other.

## Authorship boundary

The epic/US **title and description** are product content. When acting as Tech Lead, do not
silently rewrite them — surface the suggested change and ask before editing. The Tech Lead
freely creates, renames, and maintains the **subtasks** underneath a US without asking again
for each one, once the US itself is approved.
