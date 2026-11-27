# Performance Review

A review lens for spotting performance and resource-cost defects in a diff (hot paths, queries, memory, network) and rating them by evidence, not tuning them; examples use JavaScript (Node.js, ES2022+) and PostgreSQL, and the project's own measurements and versions win; checked 2026-11-26.

## Contents

- The review lens: cost at scale on the paths that matter
- Is this a hot path?
- Algorithmic cost
- Queries and data access
- Loops, concurrency and fan-out
- Memory and resource lifetime
- Network cost and payload size
- Caching claims
- Frontend and client cost
- Evidence and severity
- What to ask others to measure

## Guidance

### The review lens: cost at scale on the paths that matter

A performance finding is a prediction: "at this size, on this path, the cost becomes this." It needs a path, a size and a consequence. Without all three it is a preference.

You review for **defects that grow with data or traffic** and for **waste on paths that run often**. You do not review for micro-optimisation. Fast enough is fast enough: if the diff is not on a hot path and does not scale with data, leave it alone.

This reference is the lens. Tuning technique is owned elsewhere: for index choice and query rewriting, load `database-engineering`; for caching design, connection pooling and server tuning, load `backend-engineering`; for rendering and bundle work, load `frontend-engineering`.

### Is this a hot path?

Classify each changed function before you spend effort on it.

| Class | Examples | Cost that matters |
|---|---|---|
| Per-request or per-event | request handler, message consumer, render function | Latency per call, calls per second |
| Per-item inside a loop | work inside `map`, per row, per element | Multiplied by N |
| Startup or per-deploy | boot sequence, migrations | One-off, but blocks readiness |
| Scheduled or batch | cron job, report, import | Total duration, memory ceiling, lock time |
| Rare and manual | admin script, one-off tool | Usually ignore unless it can lock or exhaust shared resources |

Ask the author's documentation or the code: how often does this run, and with what N (rows, users, items, bytes)? If neither says, state your assumption in the finding and ask.

### Algorithmic cost

- **Nested iteration over two collections.** A lookup inside a loop over another list is O(n times m). Replace with a map or set built once, if both can be large.
- **Repeated work in a loop.** Parsing, compiling a regular expression, building a formatter, reading config or hashing inside the loop body when the value is loop-invariant.
- **Copying in a loop.** Spreading an accumulator (`acc = [...acc, x]`, `{ ...acc, [k]: v }`) inside a reducer copies the whole accumulator on every step and is quadratic.
- **Sorting and searching.** Sorting to find a minimum, sorting inside a loop, linear search in a collection that is already keyed.
- **Unbounded recursion or retry.** Recursion on user-controlled depth; retry loops without a limit or backoff.
- **String building.** Quadratic concatenation in languages where strings are immutable and the platform has no optimisation; large joins in a loop.

Only report the ones where N can realistically be large. A nested loop over 5 configured items is fine.

### Queries and data access

For each query or data-access call the diff adds or changes:

| Check | Defect signal | Failure scenario to write |
|---|---|---|
| N plus 1 | A query (or lazy-loaded relation access) inside a loop over results of another query | List of 500 orders causes 501 queries |
| Unbounded result | No `LIMIT`, no pagination, `findAll()` on a growing table | Table grows to 5 million rows; the handler loads them all into memory |
| Over-fetching | `SELECT *` or loading whole objects when two columns are used, large text or blob columns | Payload and memory grow with column width |
| Filter in application | Fetching rows then filtering in code, when the database can filter | Transfers the table to discard most of it |
| Missing index for a new filter or sort | New `WHERE`/`ORDER BY` column with no supporting index on a large table | Sequential scan per request |
| Function on indexed column | `WHERE lower(email) = $1` or arithmetic on the column, with a plain index | Index unusable |
| Offset pagination at depth | Large `OFFSET` | Cost grows with page number |
| Count on every request | `COUNT(*)` of a large table on a hot endpoint | Scan on each call |
| Writes in a loop | One insert or update per item in a request | Round trips multiplied by N; use a batch where the contract allows |
| Long transaction | Network call or user wait inside a transaction | Locks and connections held; blocks other writers |

Whether an index is the right fix, and which one, is a `database-engineering` question: state the access pattern and the size, and route.

Read-only inspection: reading the query plan with `EXPLAIN` is safe because it does not run the statement. `EXPLAIN ANALYZE` executes the statement, so on an insert, update or delete it changes data and on any query it adds load; treat it as a command that needs approval and never point it at production. (Behaviour of `EXPLAIN ANALYZE` stated from general PostgreSQL knowledge; confirm with context7 for the project's version.)

### Loops, concurrency and fan-out

- **Sequential awaits that are independent.** `for (const id of ids) await fetchOne(id)` over many items multiplies latency. Run independent calls concurrently, but with a limit.
- **Unbounded parallelism.** `Promise.all(ids.map(fetchOne))` over an unbounded list opens that many connections at once, exhausts a pool or trips an upstream rate limit. Check for a concurrency cap or batching.
- **Fan-out per request.** One user request that triggers N outbound calls, each of which may trigger more.
- **Blocking the event loop.** Synchronous file, crypto or compression calls, large `JSON.parse`, catastrophic-backtracking regular expressions or CPU-heavy loops in a single-threaded request path.
- **Thundering herd.** Many callers refreshing the same expired cache entry at once, or retrying in lockstep without jitter.
- **Lock hold time.** Work inside a lock or transaction that could happen outside it.

### Memory and resource lifetime

- **Whole-object loading.** Reading a full file, response body or result set into memory when the code processes it item by item. Prefer streaming or pagination when size is unbounded.
- **Unbounded in-memory structures.** A module-level map, array or cache that only grows (keyed by user, request or URL), with no eviction, size limit or expiry.
- **Listeners and timers that are never removed.** Event listeners added per request, intervals never cleared, subscriptions never closed. MDN notes that a pending `AbortSignal.timeout()` timer keeps its signal alive while it has abort listeners, so remove listeners you no longer need.
- **Handles not released.** Connections, file descriptors and cursors left open on the error path.
- **Large closures and captured objects.** A long-lived callback holding a reference to a large request or buffer.
- **Per-request allocation of heavy objects.** Creating a client, pool, parser or schema validator on every call instead of once.

### Network cost and payload size

- **No timeout** on an outbound call is both a correctness and a resource defect (see the correctness reference).
- **Chatty interfaces.** Many small calls where one batched call exists; a loop of HTTP calls to the same host.
- **Repeated identical calls.** The same lookup made several times in one request; no reuse of the result.
- **Payload size.** Responses that include whole records when the client needs a few fields; no compression for large text; unbounded request bodies (a baseline security issue too).
- **Retries.** Retries with no backoff, no cap and no jitter multiply load during an outage.
- **Pagination contract.** A list endpoint with no page size limit lets one caller request everything.
- **Connection reuse.** A new connection or client per call where keep-alive or a pool is the project's norm.

### Caching claims

A cache is a trade of freshness for speed, and a source of bugs. When the diff adds one, check: the key includes everything the value depends on (user, tenant, locale, version); there is an expiry or invalidation on every write path; there is a size bound; a failure to read it falls back to the source; and cached values do not contain data the next requester must not see. A cache keyed too coarsely is a data-exposure defect (report it as a security or correctness finding, not a performance one). Cache design itself is owned by `backend-engineering`.

### Frontend and client cost

Check only what the diff changes, and only where it can be large:

- A list rendered with no bound, no virtualisation and no pagination.
- Work done in the render path on every render (sorting, filtering, parsing) with no memoisation where the input rarely changes.
- State placed so high that unrelated parts re-render on every keystroke.
- A heavy library imported for one function, or imported in the entry bundle instead of lazily.
- Images without dimensions or sizes, causing layout shift.
- Effects or subscriptions without cleanup.

Tuning technique belongs to `frontend-engineering`.

### Evidence and severity

Write the scale you assumed and the arithmetic. Reviewers who say "slow" are ignored; reviewers who write "501 queries at about 2 ms each is about 1 second" are fixed.

| Severity | Performance case |
|---|---|
| `critical` | The change will take the system down or lose data at present load (for example, an unbounded query on a hot endpoint against a table already large, or a loop that exhausts the connection pool). |
| `high` | Likely serious defect at realistic scale: N plus 1 on a list endpoint with a known large N, unbounded memory growth in a long-running process, blocking the event loop on the request path. |
| `medium` | Real but limited: waste on a moderately used path, missing limit where growth is slow, sequential calls that could be concurrent. |
| `low` | Improvement with measurable but small gain; no scale risk. |

Do not rate by how inelegant the code is. Rate by cost at the scale you can justify.

### What to ask others to measure

The reviewer runs only read-only commands. When the claim needs a measurement (a benchmark, a profile, a plan with execution, a load test), do not run it. Put it in the report as a request: name the scenario, the data size and the metric, and say who can run it (the tester or the implementer, with approval where the command writes or loads a shared environment). Mark your claim as a prediction until it is measured.

## Examples

### N plus 1 (bad to good)

```js
// Bad: one query for the orders, then one query per order
const orders = await db.query("SELECT id, customer_id FROM orders WHERE status = $1", ["open"]);
for (const order of orders.rows) {
  order.customer = (await db.query("SELECT name FROM customers WHERE id = $1", [order.customer_id])).rows[0];
}
```

```js
// Good: one joined query (or one batched lookup by id list)
const { rows } = await db.query(
  `SELECT o.id, c.name AS customer_name
     FROM orders o JOIN customers c ON c.id = o.customer_id
    WHERE o.status = $1
    LIMIT $2`,
  ["open", 200]
);
```

### Quadratic accumulator (bad to good)

```js
// Bad: copies the accumulator on every iteration
const byId = rows.reduce((acc, r) => ({ ...acc, [r.id]: r }), {});
```

```js
// Good
const byId = new Map(rows.map((r) => [r.id, r]));
```

### Unbounded fan-out (bad to good)

```js
// Bad: opens one request per id, all at once
await Promise.all(ids.map((id) => fetchProfile(id)));
```

```js
// Good: bounded batches (or the project's concurrency helper)
for (let i = 0; i < ids.length; i += 10) {
  await Promise.all(ids.slice(i, i + 10).map((id) => fetchProfile(id)));
}
```

### A filled-in performance finding

```
[high] Order list endpoint issues one customer query per order
Location: src/orders/list.js:27
Problem: customer name is loaded inside the loop over open orders (N plus 1); there is no limit on the outer query.
Failure scenario: docs/DB.md and the seed data show about 40,000 open orders in production; GET /orders runs 40,001 queries, about 80 seconds at 2 ms each, and holds a pool connection throughout. Assumption: N is the open-order count; please confirm. Introduced by this change.
Recommendation: join customers in the outer query and add a LIMIT with the pagination parameters from docs/API-CONTRACTS.md. For any index question, load database-engineering.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reporting micro-optimisations | Noise; blocks nothing real | Report only scale-dependent cost or hot-path waste |
| "This looks slow" | Not actionable or checkable | Write path, N, arithmetic, consequence |
| Rating by elegance | Severity loses meaning | Rate by cost at justified scale |
| Running `EXPLAIN ANALYZE` or a benchmark yourself | It executes statements or loads shared systems | Request the measurement; read plans with `EXPLAIN` only |
| Teaching index design in the review | Out of scope; findings get long | State access pattern and size, route to `database-engineering` |
| Ignoring the second-order path | Cost often sits in the callee or the retry | Trace one hop out, including retries and fan-out |
| Missing memory growth | Leaks surface days later | Check every new map, cache, listener and timer for bounds and cleanup |
| Treating a cache as free | Stale or cross-user data | Check key, expiry, invalidation, size and isolation |

## Checklist

- [ ] Each changed function is classified as hot, per-item, startup, batch or rare.
- [ ] Every new or changed query has been checked for N plus 1, unbounded results, over-fetching and a supporting index question.
- [ ] Every loop was checked for repeated invariant work, copying and independent sequential awaits.
- [ ] Every fan-out has a concurrency limit or a stated bound on N.
- [ ] Every new in-memory structure, listener, timer and handle has a bound or a cleanup.
- [ ] Every outbound call has a timeout, and retries have a cap and backoff.
- [ ] Every new cache has a key, expiry or invalidation, size bound and tenant-safe scope.
- [ ] Each performance finding states the path, the assumed N and the consequence with arithmetic.
- [ ] Measurements needed to confirm a claim are requested, not run.
- [ ] Tuning advice beyond the smallest fix is routed to the owning skill.

## Verify with context7 and gh_grep

- **context7:** for the ORM, database driver and HTTP client in the lockfile, query "`<ORM>` eager loading versus lazy loading relations", "`<ORM>` batch insert", "`<driver>` connection pool default size and timeout", "PostgreSQL `EXPLAIN` versus `EXPLAIN ANALYZE`", "`<HTTP client>` keep-alive and connection reuse", "`<framework>` streaming responses".
- **gh_grep:** search literal code for how maintained projects bound work: `p-limit(`, `Promise.all(` with a chunk helper, `LIMIT $`, `.limit(`, `AbortSignal.timeout(`, `new Map(`, `removeEventListener(`, `clearInterval(`.

## Sources

- Google Engineering Practices, "What to look for in a code review" (complexity, context, over-engineering): https://google.github.io/eng-practices/review/reviewer/looking-for.html
- MDN, `AbortSignal.timeout()` static method (timer lifetime and listeners): https://developer.mozilla.org/docs/Web/API/AbortSignal/timeout_static
