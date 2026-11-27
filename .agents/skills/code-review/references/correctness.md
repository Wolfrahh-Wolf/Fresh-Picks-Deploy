# Correctness

How to find logic, edge-case, concurrency, error-path, data-integrity and requirement-match defects in a diff; examples use JavaScript (Node.js, ES2022+), SQL (PostgreSQL) and a little Python, and the project's own manifest and database version always win; checked 2026-11-26.

## Contents

- Requirement match
- Logic and control flow
- Edge cases to try on every input
- Error paths
- Concurrency and check-then-act
- Data integrity
- Compatibility and callers
- Proving a finding before you write it

## Guidance

### Requirement match

Correct means "does what the acceptance criteria and specifications say", not "does what the author meant".

1. List the criteria. For each, find the line of code that makes it true and the test that would fail if it stopped being true.
2. Check the negative space: what the change does that no criterion asks for (extra writes, extra endpoints, changed defaults). Unrequested behaviour is a finding when it can fail or surprise a caller.
3. If a criterion is ambiguous, do not pick a reading. Record it as an open question and say which readings the code could satisfy.
4. If the code intentionally does something different from the criteria, that is an escalation (criteria contradict intent), not a finding.
5. Do not review against requirements nobody wrote. "It should also support X" is a question for the coordinator.

### Logic and control flow

Read each changed conditional and loop as if you were the machine. Typical defects:

| Pattern | What to check |
|---|---|
| Off-by-one | `<` versus `<=`, slice end is exclusive, first and last element, empty range. |
| Inverted or incomplete condition | Negations, `&&` versus `||` precedence, De Morgan rewrites, a branch missing for one enum value. |
| Falsy confusion | `if (count)` when `0` is valid; `||` default that overrides `0`, `""` or `false` (use `??` when only null or undefined should default). |
| Wrong comparison | `==` coercion, comparing objects or dates by reference, string compare of numbers, locale-sensitive sorting. |
| Floating point money or rates | Binary floats for currency; summing then rounding versus rounding then summing; use integer minor units or a decimal type. |
| Time | Date-only strings parsed as UTC while date-times without offset parse as local time; daylight-saving gaps; "end of day" as 23:59; comparing a timestamp with a calendar date. |
| Text | Length in characters versus bytes versus code points; case folding; trimming; normalisation; truncation that splits a multi-unit character. |
| Integer limits | Overflow or wrap in fixed-width languages; large IDs losing precision in JavaScript numbers (above 2^53 - 1). |
| Mutation of shared values | Sorting or splicing an array the caller still holds; default argument objects shared across calls (Python mutable defaults). |
| Fall-through and early return | A missing `break`, a `return` that skips cleanup, a guard that returns the wrong type. |
| Copy-paste drift | A duplicated block where one variable name was not updated. |

When a function is new, trace one normal input and one boundary input through it line by line. When a function is changed, compare old and new behaviour for the inputs the old tests covered.

### Edge cases to try on every input

Run each changed input through this list and pick the ones that apply. Name the one that breaks in the finding.

| Class | Examples |
|---|---|
| Empty or missing | `null`, `undefined`, `""`, `[]`, `{}`, absent optional field, absent header |
| Single and many | exactly one item, two items, the maximum page size, one more than the maximum |
| Boundary | `0`, `-1`, minimum, maximum, exactly at a threshold, one past it |
| Duplicate | same key twice, same item in two lists, replayed request, double click |
| Unexpected type or shape | number as string, array where an object is expected, extra fields, nested nulls |
| Text | very long, leading or trailing space, mixed case, non-ASCII, emoji, newline inside a value |
| Order | unsorted input where sorted is assumed, events arriving out of order |
| Time | midnight, daylight-saving change, leap day, timezone of server versus user |
| Resource state | file or row already exists, already deleted, locked, partially written |
| Concurrency | two callers at once, caller cancelled mid-way, retry after a timeout |

### Error paths

The unhappy path is where most real defects live. For every call that can fail, ask four questions: what fails, who finds out, what state is left behind, and can it be retried safely.

- **Swallowed errors.** An empty `catch`, a `catch` that logs and returns a success-shaped value, a promise with no rejection handler. A failure that looks like success is usually `high`.
- **Wrong error mapping.** Internal errors returned as client errors (or the reverse), or a not-found condition reported as a server error. Check against the project's error conventions and `docs/API-CONTRACTS.md`.
- **Cleanup.** Connections, file handles, locks and timers released on every path, including the error path. Look for a release that is skipped when an earlier line throws.
- **Partial failure.** Multi-step operations where step two fails after step one succeeded: is the first step undone, or is the state valid anyway? Batch operations: does one bad item abort the rest, and is that intended?
- **Retries.** A retry around a non-idempotent write duplicates the effect. Retries need a limit, backoff and an idempotency key or a safe operation.
- **Timeouts.** Every outbound call needs a bound. An unbounded call can hold a request, a worker and a connection indefinitely. In JavaScript, `AbortSignal.timeout(ms)` gives a signal that aborts with a `TimeoutError`; it cannot be cancelled, so use an `AbortController` with `setTimeout` and `clearTimeout` when the timer must be stopped early.
- **HTTP clients that do not throw.** The `fetch` API rejects on network failure but resolves for HTTP error statuses; code that skips the `res.ok` check treats a 500 response body as data.
- **Error messages and logs.** Errors that leak internals or secrets to callers are baseline security findings; see the checklist reference.
- **Async code.** Missing `await`, `forEach` with an `async` callback (the loop does not wait), `Promise.all` where one rejection leaves the other operations running, and un-awaited promises that fail after the function returned.

### Concurrency and check-then-act

Races rarely show up by running the code, so reason about them. Ask: what shared state exists, who else can change it between my read and my write, and what happens if two copies of this code run at once (two requests, two workers, two tabs).

- **Check-then-act.** A check followed by an action on the same resource, where the resource can change in between. The Node.js file-system documentation warns against calling `fs.access()` before opening a file because another process may change the file in the gap; the recommended pattern is to attempt the operation and handle the error (for example open with the exclusive-create flag and handle an `EEXIST` error).
- **Read-modify-write.** Read a value, compute in application code, write it back. Two callers lose one update. Prefer an atomic operation in the data store (`SET x = x + $1`), a conditional write, optimistic versioning or an explicit lock.
- **Shared mutable state.** Module-level variables, caches and singletons mutated per request. In a multi-process deployment, in-memory state is also not shared across processes.
- **Lock ordering and holding.** Two locks taken in different orders can deadlock; a lock held across a network call blocks everyone behind it.
- **Idempotency.** Handlers that can be called twice (retries, redelivered messages, double submit) must give the same end state. Look for a uniqueness constraint or a processed-marker.
- **Async interleaving.** In single-threaded runtimes the danger is interleaving at `await`: state read before an `await` may be stale after it.
- **Cancellation and shutdown.** Work in flight when a signal arrives: is it finished, retried or lost?

Concurrency design is something the reviewer and author reason through together; if you cannot convince yourself the code is safe, say so as a question with the interleaving you could not rule out.

### Data integrity

- **Atomicity.** Steps that must succeed together belong in one transaction. Look for two writes to different tables without a transaction, or a write plus a message publish with no outbox or retry story.
- **Isolation level awareness.** PostgreSQL's default, Read Committed, gives each statement a fresh snapshot, so two reads in one transaction can see different data. When a concurrent update changes a row a statement is about to modify, the statement waits and then re-evaluates its `WHERE` clause against the new row version; the PostgreSQL documentation calls Read Committed unsuitable for commands with complex search conditions. Repeatable Read and Serializable raise serialisation failures (SQLSTATE `40001` for Serializable) that the application must retry; check that the code retries the whole transaction when the project uses them.
- **Constraints.** A rule enforced only in application code is bypassed by the second writer. Check that uniqueness, foreign keys and not-null rules exist where the data model says they do (`docs/DB.md`). For index choice and schema design, load `database-engineering`.
- **Migrations.** Is the migration reversible or safe to run twice? Does old code still work against the new schema during rollout? Does it lock a large table? Running a migration needs user approval; the reviewer only reads it.
- **Deletes and cascades.** What else disappears when this row goes? Soft versus hard delete consistent with the rest of the model.
- **Derived data.** Counters, caches and denormalised copies updated on every write path, including the paths the diff did not touch.
- **Units and formats at boundaries.** Currency, time zone, encoding and ID format agree on both sides of every interface.

### Compatibility and callers

- Find every caller of a changed public function, type, route, event or column with a code search. Check each still works with the new signature, default, return shape and thrown errors.
- A changed default, a removed field or a stricter validation is a breaking change for someone. Compare with `docs/API-CONTRACTS.md`. For contract design questions, load `api-engineering`.
- Feature flags and configuration: both the on and off paths must be correct.

### Proving a finding before you write it

1. Pick the smallest concrete input or state that triggers the defect.
2. Walk it through the code line by line, quoting `file:line` at each decision.
3. State the wrong observable result (wrong value, lost update, error, data loss).
4. If a safe read-only check can confirm it (search for callers, read the migration, read the library source or docs), run it.
5. If you cannot complete steps 1 to 3, it is a question, not a finding.

## Examples

### Check-then-act on a file (bad to good)

```js
// Bad: another process can create the file between the check and the write
import { access, writeFile } from "node:fs/promises";
async function saveOnce(path, data) {
  try { await access(path); return false; } catch { /* missing */ }
  await writeFile(path, data);
  return true;
}
```

```js
// Good: one atomic attempt; the exclusive-create flag fails if the file exists
import { writeFile } from "node:fs/promises";
async function saveOnce(path, data) {
  try {
    await writeFile(path, data, { flag: "wx" });
    return true;
  } catch (err) {
    if (err.code === "EEXIST") return false;
    throw err;
  }
}
```

### Lost update (bad to good)

```sql
-- Bad: both callers read stock = 5, both write 4
SELECT stock FROM items WHERE id = $1;
-- application computes stock - 1
UPDATE items SET stock = $2 WHERE id = $1;
```

```sql
-- Good: atomic, with the rule inside the statement; check that 1 row was affected
UPDATE items SET stock = stock - $2 WHERE id = $1 AND stock >= $2;
```

### Unbounded outbound call and ignored status

```js
// Bad: no timeout, HTTP errors treated as data
const res = await fetch(url);
const body = await res.json();
```

```js
// Good: bounded, status checked, timeout distinguished
try {
  const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`upstream status ${res.status}`);
  return await res.json();
} catch (err) {
  if (err.name === "TimeoutError") throw new Error("upstream timed out");
  throw err;
}
```

### `async` callback in `forEach`

```js
// Bad: returns before any save finishes; failures become unhandled rejections
items.forEach(async (item) => { await save(item); });
```

```js
// Good: wait for all; decide deliberately between all-or-nothing and per-item results
await Promise.all(items.map((item) => save(item)));
// or, when partial success is acceptable:
const results = await Promise.allSettled(items.map((item) => save(item)));
```

### Mutable default argument (Python)

```python
# Bad: the same list is reused by every call that omits `tags`
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags
```

```python
# Good
def add_tag(tag, tags=None):
    tags = [] if tags is None else tags
    return [*tags, tag]
```

### A filled-in finding

```
[high] Stock can go negative under concurrent orders
Location: src/orders/reserve.js:41
Problem: stock is read in one statement and written back in another (read-modify-write), with no lock or conditional update.
Failure scenario: stock = 1; two requests reserve 1 at the same moment; both read 1, both write 0; two orders are accepted for one unit. Introduced by this change (new function).
Recommendation: replace the pair with UPDATE items SET stock = stock - $2 WHERE id = $1 AND stock >= $2 and treat 0 affected rows as "out of stock".
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reviewing only the happy path | Most defects sit in empty, boundary and failure cases | Run the edge-case table on each changed input |
| Reporting a race with no interleaving | The author cannot confirm or fix it | Write the two-step interleaving that loses data |
| Trusting passing tests as proof | Tests may not cover the changed branch | Check that a test would fail if the behaviour broke |
| Accepting a swallowed error because it is logged | The caller sees success and data is wrong | Require the failure to reach the caller or be handled with a stated policy |
| Judging an API call from memory | Behaviour differs between versions | Check documentation for the version in the lockfile |
| Reading only the diff | Callers and callees contain the contract | Trace at least one hop out |
| Choosing one reading of an ambiguous criterion | You may fail correct code or pass wrong code | Record an open question |
| Calling an unlikely race `critical` | Inflated severity erodes trust in the scale | Rate by likelihood and impact; say how likely the interleaving is |

## Checklist

- [ ] Every acceptance criterion is mapped to code and marked met, not met or unable to verify.
- [ ] Each changed conditional and loop was traced with a normal and a boundary input.
- [ ] The edge-case table was applied to every new or changed input.
- [ ] Every call that can fail has an identified failure behaviour and the state it leaves behind.
- [ ] Every outbound call has a bound (timeout) and its status or error is handled.
- [ ] No check-then-act or read-modify-write remains on shared state without an atomic or locked form.
- [ ] Multi-step writes are atomic or have a stated recovery path.
- [ ] Constraints named in `docs/DB.md` exist where the change relies on them.
- [ ] Every caller of a changed public symbol was found and checked.
- [ ] Each reported finding has a concrete input, a traced path and a wrong result.

## Verify with context7 and gh_grep

- **context7:** for the library versions in the lockfile, query "`<library>` `<function>` errors thrown and return value", "`<HTTP client>` timeout default and status handling", "`<ORM>` transaction isolation default and retry on serialisation failure", "Node.js `fs` `writeFile` flag option `wx`", "PostgreSQL Read Committed concurrent UPDATE behaviour".
- **gh_grep:** search literal patterns to see how maintained projects bound and handle calls: `AbortSignal.timeout(`, `flag: "wx"`, `Promise.allSettled(`, `FOR UPDATE`, `SET stock = stock -`, `could not serialize access`.

## Sources

- Google Engineering Practices, "What to look for in a code review" (functionality, concurrency, tests, every line, context): https://google.github.io/eng-practices/review/reviewer/looking-for.html
- MDN, `AbortSignal.timeout()` static method: https://developer.mozilla.org/docs/Web/API/AbortSignal/timeout_static
- PostgreSQL documentation, Transaction Isolation (Read Committed, Repeatable Read, Serializable): https://www.postgresql.org/docs/current/transaction-iso.html
- Node.js documentation, File system, `fs.access()` race-condition note: https://beta.docs.nodejs.org/fs/callback-api
