# Tracker hierarchy — epics, US, and technical subtasks

Read this asset before creating or restructuring any task in a connected task tracker
(Jira, ClickUp, Linear, GitHub Issues, …). It defines the shape of the board — see
`task-management.md` for the local Markdown backlog equivalent, and the `task-writing`
skill (`US-FORMAT.md` → "Hierarquia") for the general principle this asset makes concrete
for a tracker. Tracker-specific mechanics (ClickUp today) are at the end.

---

## The rule

**Epic and US live at the same hierarchical level — both are product stories, at different
granularity — connected by a *link* (or the tracker's native epic relation), never by
`parent`.** The `parent` slot (subtask) is reserved for one purpose only: the technical
breakdown the Tech Lead creates **inside** a US that the PO already wrote and approved.

| Item | Tracker shape | Who authors it |
|---|---|---|
| Epic | Top-level item in the backlog | PO (product) |
| US | Top-level item in the same backlog, **linked** to its epic | PO (product) |
| Technical subtask | Subtask of the US it details | Tech Lead |

**Why not `parent` for epic↔US:** in most trackers a subtask is buried inside its parent — it
doesn't surface as its own card in board/list views the way a top-level item does, and some
APIs cannot clear `parent` on an existing item. If a US is created as a subtask by mistake,
the fix is usually to **delete and recreate** it as a top-level item, not to try to unparent
it in place (verify against the tracker in use; do not assume).

If the tracker has a native epic concept (e.g. Jira epics, Linear projects/parent issues),
use it for the epic↔US relation instead of a generic link, keeping the same intent: the US
stays a top-level item and the technical subtasks hang under the US.

---

## Order of operations for a new epic + its US's

1. Create the epic as a top-level item in the backlog.
2. Create each US as a **top-level item in the same backlog** — not as a subtask of the epic.
3. Link each US to its epic (native epic relation or generic link — see the tracker notes below).
4. Technical subtasks (Tech Lead phase) are created afterward, as subtasks of the **US**
   they detail — never of the epic directly.

## Technical subtasks (Tech Lead phase)

Once architecture is settled, the Tech Lead creates subtasks under each US following
`US-FORMAT.md` (subtask row of the "Application rules by type" table): one subtask per
layer/dependency (backend, frontend, infra), each independently pickable. Apply
`lean-writing.md` and `readability.md` before publishing. Use blocking dependencies between
subtasks only for genuine hard blockers — see the "when to register a blocker" criteria
pattern in `lean-writing.md`'s Dependencies guidance; two subtasks that can be built in
parallel against a shared contract should not block each other.

## Authorship boundary

The epic/US **title and description** are product content. When acting as Tech Lead, do not
silently rewrite them — surface the suggested change and ask before editing. The Tech Lead
freely creates, renames, and maintains the **subtasks** underneath a US without asking again
for each one, once the US itself is approved.

---

## Tracker notes

### ClickUp

- Epic and US are top-level tasks in the same list; the link is ClickUp's task-link, never `parent`.
- The ClickUp API does not support clearing `parent` on an existing task (`PUT` with
  `"parent": null` is silently ignored — verified against the live API).
- Create the link with the v2 task-link endpoint — it creates a bidirectional relation distinct
  from both `parent` and `depends_on`. If a connected ClickUp tool (MCP/CLI) can create task
  links, prefer it; otherwise use `curl` directly (never echo the key to chat/logs):

```bash
# The key comes from the environment (e.g. CLICKUP_API_KEY); never echo it
curl -s -X POST "https://api.clickup.com/api/v2/task/{US_ID}/link/{EPIC_ID}" \
  -H "Authorization: $CLICKUP_API_KEY" -H "Content-Type: application/json"
```

No body needed. Either task ID can be first — the link is symmetric. The response echoes both
tasks with their `linked_tasks` populated. Blocking dependencies between subtasks use `depends_on`.

### Other trackers (Jira, Linear, GitHub Issues, …)

Use the connected tool's native epic/parent/link primitives to express the same shape. If the
tracker cannot express a top-level US linked to an epic, ask the PO which equivalent to use and
record the choice in `state.md`.
