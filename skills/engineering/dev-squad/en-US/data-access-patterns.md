# Data access patterns — lists, search, sorting, pagination and counters

Read before: specifying a list screen or endpoint; the Tech Lead choosing or closing the data model (mandatory when the database is non-relational, or when cost/capacity rule out open-ended queries); the Senior Developer planning a list query; QA testing a list.

## Failure mode diagnosis

- The spec says "screen with the list of orders" and stops there. Nobody asks whether people will search by text, sort by column, paginate or see totals per status. The Tech Lead models the database only for "write" and "read by id".
- Late in development the requirement "text search, column sorting and backend pagination" shows up. The model cannot answer it: the list is loaded whole, the order is a fixed default, counters are computed in the browser over the whole list (and become wrong the moment the list is paginated), and free-text search has no native solution. Changing it now costs a new key, a new index, a data migration or one more service — and the cost constraint (no scans, minimum capacity, no dedicated search service) may close the door.
- "It's little data, load everything" is said without a number and without a review trigger; volume grows and nobody revisits it.

Why this weighs more on non-relational databases: in a relational database a new filter, sort order or count is usually one more clause and one more index. In a key-value, document or wide-column database, every question the screen asks must be **designed into the keys and indexes** up front; whatever is not becomes a scan (expensive or forbidden), a read of everything, or another system. That is why the survey comes **before** the model, not after.

## Rule

No data model in a non-relational database (nor a relational model under a constraint that forbids open-ended queries) is closed without the **access-pattern sheet** of every list screen and every relevant read: answered by the PO for the product part, validated by the Tech Lead against the database's constraints, with a recorded decision for everything the database does not support natively. An unanswered field is an explicit open item with an owner, never a silent assumption.

## Access-pattern sheet (one per list or query)

| Field | What to declare | Neutral example (order list) |
|---|---|---|
| Who sees it and scope | Role, tenant, user; what never appears | A clerk sees the orders of their store |
| Filters | Field, operator (equals, range, set), whether they combine | Status (set), period (range), store (equals) |
| Text search | Fields; type (prefix, contains, whole word); accents, case, typos; now or later | Order number by prefix; customer name by word, accent-insensitive |
| Sort orders | Columns, direction, default order, tie-breaker | Date desc (default), amount asc/desc; tie-break by id |
| Pagination | Page size; next/previous only or jump to page N; total pages on screen; infinite scroll | 20 per page, "load more", no jump |
| Counters and aggregates | Total, per status, sums; exact or approximate; do they follow the filters? | Tabs with per-status count, exact, respecting the period |
| Volume | Items today, in 12 and 24 months, per scope; average size; writes per day | 3k per store today; 30k in 24 months |
| Freshness and consistency | Must a just-written item show up immediately? Are seconds tolerable? | Up to 5 s of lag is acceptable |
| Export and reporting | Whole list to a file? (that is another access pattern) | Export the filtered month as CSV |
| Performance | Expected response time (p95) | Up to 800 ms |

## Who does what

- **PO** — answers the sheet in product language. The Orchestrator asks through `po-proxy/protocol.md`, one question at a time, with a recommendation and the cost of each answer (e.g., "I recommend 'load more' instead of jumping to page N: in the chosen database, jumping requires reading the previous pages").
- **UX** (when there is a prototype or a UX review) — the prototype shows the list states: empty with no data vs. filter with no results, loading, error with retry, end of list, active sort, search with no results, counters. A search box, sortable header, pagination or tabs with counts drawn in the prototype **are requirements**: the sheet must cover them. Whatever the sheet asks for and the prototype does not show goes to the PO.
- **Tech Lead** — validates each line against the database and records the decision (format below). At minimum, check: scans forbidden or expensive; capacity and read limits; maximum size per response; cost of each extra index (in key-value stores, each new sort or filter is usually an index); index quota; consistency of secondary indexes; free tier and monthly budget; whether a dedicated search service is allowed. For each line: which operation serves it (key read, query on index X, search index, aggregate maintained on write), the cost per call, and what is **not** served natively.
- **Senior Developer** — in `investigate`, the plan links each line of the sheet to the concrete query. A line served by "loading everything and filtering in memory or in the browser" only with the Tech Lead decision that accepted it cited in the plan.
- **QA** — tests the list scenarios below, with volume above one page and counters with pagination active.

## Options for what the database does not support natively

| Need | Option | Cost | When it breaks |
|---|---|---|---|
| Prefix search (code, name starting with) | Normalized value (lowercase, accent-stripped) in an index's sort key | Low; one index per field | Prefix only; does not find a word in the middle |
| Word search on a few fields, moderate volume | Inverted index maintained by the application (one record per term pointing to the id), written with the item | Writes multiplied by the number of terms | No relevance or typo tolerance; consistency to maintain on edit and delete |
| Free search and sort over small, bounded volume | Compact directory: only the search, filter and sort fields of all items in one document, object-storage object or cache entry; the backend loads it and filters in memory | Very low | Exceeds the declared ceiling; concurrent writes to the directory; needs a version or a lock |
| Free search with relevance, typos, facets | Dedicated search service or index (managed engine, or the database's built-in search feature), fed by the change stream | Fixed monthly cost; one more system to operate | Eventual consistency; reindexing after a long stream outage |
| Exact counters with pagination | Counter maintained on write (atomic increment or in the same transaction) or an aggregates table | Extra write per state change | Counter that drifts without a reconciliation job |
| Several sort orders | One index per order; or the PO reduces the offered orders; or sort on the server a set already bounded by the filter | Writes and index quota | Filtered set too large to sort in memory |

## Small volume also needs a conscious decision

"Load everything" is acceptable when: (1) there is a declared **numeric ceiling** (items per scope and bytes per response); (2) the decision is recorded with the measured number, the date and the **review trigger** (e.g., an alert at 80% of the ceiling); (3) the API contract is already paginated (opaque cursor), so the server can change the implementation without changing the client. Counters computed on the client over the whole list are only valid under that same decision, and never together with pagination: with pagination, counters come from the server.

## Decision record

```markdown
### Decision — <list>: <need> (<YYYY-MM-DD>, <who decided>)
- **Question:** <what the database does not support and why>
- **Options:** <each option with estimated monthly cost, effort and what it delivers>
- **Decision:** <the chosen one>
- **Reason:** <why it beats the others>
- **Residual risk and review trigger:** <what can go wrong; the number or event that reopens the decision>
- **Impact:** <sheet, acceptance criteria, tests, documents changed>
```

## List acceptance criteria (Given/When/Then templates)

Adapt to the sheet; include only what the list has. Each one is a scenario of the story.

- **Empty:** Given no orders in the store, When the clerk opens the list, Then they see the "no orders yet" state (different from "no results for this filter").
- **Filter with no results:** Given orders exist, When filtering by a status with no orders, Then they see "no results" and the option to clear the filter.
- **First page:** Given 45 orders, When opening the list, Then they see 20, in the default order, and the option to load more.
- **Next page:** Given the first page shown and 3 new orders written afterwards, When loading the next page, Then no item is duplicated or skipped relative to the first query's order.
- **End:** Given the last page loaded, When the list ends, Then the load-more option disappears.
- **Sorting:** Given orders with equal amounts, When sorting by amount desc, Then the order is stable across reloads (tie-break by id).
- **Search:** Given a customer "José", When searching "jose", Then the order appears (per the sheet's accent rule).
- **Counters:** Given 45 orders in 3 statuses and pagination active, When filtering by period, Then the tab counts are the server's for the filter, not the loaded page's.
- **Error:** Given the backend fails, When the list loads, Then the error state with retry is shown, without losing the filters.
- **Invalid parameter:** Given a sort or filter outside the allowed list, When the API receives it, Then it responds 400 without querying the database.

## Tests

- Integration against the real database or the official emulator with volume **above one page** and above the database's response limit, asserting no duplicates and no gaps.
- A test or CI check that fails if the list path uses a scan (grep for the operation, or capacity consumed measured in the test).
- Paginated response contract: opaque cursor, page size capped on the server, counters and total coming from the server.

## Checklist (Tech Lead before approving the model; QA before approving the delivery)

- [ ] Every list screen has a filled sheet, or an open item recorded with owner and deadline.
- [ ] Each line of the sheet points to a concrete operation and its cost; what is not served has a recorded decision.
- [ ] No scan on a user request path without a recorded decision.
- [ ] Cursor pagination, stable order with tie-breaker, page size capped on the server.
- [ ] Counters come from the server, or there is a small-volume decision with ceiling and trigger.
- [ ] Text search with a strategy chosen among the options and its limit explained to the PO.
- [ ] List acceptance criteria in the stories and tests that cover them.
