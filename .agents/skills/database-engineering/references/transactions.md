# Transactions

Covers ACID properties, isolation levels, concurrency anomalies, row-level locking, deadlock prevention, transient error retries and idempotency; checked against PostgreSQL 17/18 and MongoDB 8.0 documentation on 2026-11-26. Check your driver's exact transaction API and error codes before coding.

## Contents

- ACID boundaries and transaction lifetime
- Isolation levels and concurrency anomalies
- Row-level locking and deadlock prevention
- Retrying serialization and deadlock failures
- Idempotency and the transactional outbox

## Guidance

### ACID boundaries and transaction lifetime

Keep database transactions as short as possible:

- **Atomicity:** Group only the local database reads and writes that must commit or roll back together.
- **No external I/O inside transactions:** Never wait on third-party HTTP APIs, file uploads, or email servers while holding a DB transaction open. External delays hold row locks, block `VACUUM` from reclaiming dead tuples, and exhaust connection pools.
- **Set session safety timeouts:** Configure `idle_in_transaction_session_timeout` (for example, `30s`) and `statement_timeout` on application roles so crashed clients do not leave transactions open forever.

### Isolation levels and concurrency anomalies

PostgreSQL implements three distinct isolation behaviour levels (`READ UNCOMMITTED` maps internally to `READ COMMITTED`, so dirty reads cannot happen in PostgreSQL).

| Isolation level | Snapshot scope | Dirty read | Non-repeatable read | Phantom read | Lost update (read-modify-write) | Write skew |
|---|---|---|---|---|---|---|
| `READ COMMITTED` (PG default) | Per statement | Prevented | Possible | Possible | Possible unless `FOR UPDATE` or atomic `UPDATE` used | Possible |
| `REPEATABLE READ` (Snapshot) | Start of transaction | Prevented | Prevented | Prevented (in PG MVCC) | Prevented (`40001` error on conflict) | Possible across distinct rows |
| `SERIALIZABLE` (SSI) | Start of transaction + dependency tracking | Prevented | Prevented | Prevented | Prevented (`40001` error on conflict) | Prevented (`40001` error on conflict) |

**Choosing the right level:**
- **`READ COMMITTED`:** Default for simple CRUD, append-only inserts, and single-row atomic updates (`UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1`).
- **`REPEATABLE READ`:** Reporting queries that run multiple `SELECT`s requiring a single consistent point-in-time snapshot, or single-row read-modify-write invariants where an optimistic conflict should abort.
- **`SERIALIZABLE`:** Multi-row invariants (for example, preventing double-booking or preserving minimum aggregate balances across rows — **write skew**) where `FOR UPDATE` locking is impractical. Requires an application retry loop for `40001` failures.

In MongoDB 8.0 replica sets and sharded clusters, multi-document transactions default to `readConcern: "snapshot"` (or `"majority"` / `"local"`) with `writeConcern: { w: "majority", j: true }` on critical writes and must retry on `TransientTransactionError`.

### Row-level locking and deadlock prevention

| Mechanism | Behaviour | Use when |
|---|---|---|
| Optimistic locking (`version` check) | `UPDATE ... SET version = version + 1 WHERE id = $1 AND version = $2`; 0 rows affected = conflict | Contention is low; user edits across separate requests |
| `SELECT ... FOR UPDATE` | Acquires exclusive row lock; concurrent writers and `FOR UPDATE` readers block | Short pessimistic critical sections on hot single rows |
| `SELECT ... FOR SHARE` | Prevents other transactions from updating/deleting the row while allowing shared reads | Ensuring a referenced parent row stays unchanged during computation |
| `NOWAIT` | Fails immediately (`55P03`) if the row is already locked | Interactive calls that must fail fast rather than queue |
| `SKIP LOCKED` | Skips rows locked by other transactions instead of waiting | Worker/job queues under `READ COMMITTED` |

**Queue caveat:** Use `FOR UPDATE SKIP LOCKED` under `READ COMMITTED`, never `REPEATABLE READ` — under `REPEATABLE READ`, a frozen transaction snapshot misses newly committed jobs and increases serialization failures.

**Preventing deadlocks (`40P01`):** Deadlocks occur when Transaction A locks row 1 then requests row 2 while Transaction B locks row 2 then requests row 1. Always acquire locks across multiple rows or tables in a **deterministic global order** (for example, sort target IDs ascending before running `SELECT ... FOR UPDATE`).

### Retrying serialization and deadlock failures

Every `REPEATABLE READ`, `SERIALIZABLE`, or multi-row locking transaction can fail transiently under contention.

- **Retry ONLY transient conflict codes:**
  - PostgreSQL: SQLSTATE `40001` (`serialization_failure`) and `40P01` (`deadlock_detected`).
  - MongoDB: error labels `TransientTransactionError` and `UnknownTransactionCommitResult` (handled automatically by the driver's `session.withTransaction(...)` callback).
  - Never retry constraint violations (`23505` unique violation, `23503` FK violation), check failures, or query syntax errors.
- **Retry from the very start of the transaction** (`BEGIN`), never from the middle of a rolled-back transaction block.
- **Bound attempts and add jitter:** Cap retries (for example, 3–5 attempts) with exponential back-off plus random jitter so contending callers do not collide repeatedly in lockstep.

### Idempotency and the transactional outbox

Retrying transactions or HTTP requests safely requires idempotent writes:

1. **Idempotency keys:** Accept a client-supplied `idempotency_key` (UUID) on state-changing commands, enforce `UNIQUE (idempotency_key)` in a ledger or request table, and store the response payload alongside a request-parameter hash. On duplicate key, return the stored result if the payload hash matches, or reject with a conflict error if parameters differ.
2. **Atomic conditional `UPSERT`:** Prefer `INSERT INTO ... ON CONFLICT (key) DO NOTHING` (or `DO UPDATE`) over check-then-insert (`SELECT` followed by `INSERT`), which races under `READ COMMITTED`.
3. **Transactional outbox:** When a DB commit must trigger an external event (payment webhook, message broker publish), write an `outbox` row inside the **same database transaction** and publish asynchronously via a separate relay worker. This guarantees at-least-once event delivery without holding the DB transaction open across the network.

## Examples

### Deterministic lock ordering and atomic conditional update (PostgreSQL)

```sql
-- Bad: read balance then update in READ COMMITTED without lock (lost update / negative balance race)
-- SELECT balance FROM accounts WHERE id = $1;
-- UPDATE accounts SET balance = balance - 100 WHERE id = $1;

-- Bad: locking two accounts in arbitrary caller order causes deadlocks (40P01)
-- SELECT id FROM accounts WHERE id IN ($from_id, $to_id) FOR UPDATE; -- order depends on heap scan!

-- Good: deterministic ascending lock order avoids deadlocks
BEGIN;
SELECT id, balance
FROM accounts
WHERE id IN ($1, $2)
ORDER BY id ASC
FOR UPDATE;

UPDATE accounts SET balance = balance - $3
WHERE id = $1 AND balance >= $3;  -- enforces non-negative invariant atomically

UPDATE accounts SET balance = balance + $3
WHERE id = $2;
COMMIT;
```

### Bounded retry loop with exponential back-off and jitter (Python / psycopg 3)

```python
import random
import time
import psycopg

RETRYABLE_SQLSTATES = {"40001", "40P01"}

def run_serializable_transfer(conn: psycopg.Connection, fn, max_attempts: int = 4):
    for attempt in range(max_attempts):
        try:
            with conn.transaction():
                conn.execute("SET LOCAL TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                return fn(conn)
        except psycopg.Error as exc:
            if exc.sqlstate not in RETRYABLE_SQLSTATES or attempt == max_attempts - 1:
                raise
            delay = (0.05 * (2 ** attempt)) + random.uniform(0, 0.05)
            time.sleep(delay)
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Read-then-write in `READ COMMITTED` without `FOR UPDATE` | Concurrent transactions overwrite each other (lost update) | Use single atomic `UPDATE ... WHERE`, `FOR UPDATE`, or `REPEATABLE READ`/`SERIALIZABLE` |
| Holding transactions open during external HTTP calls | Starves connection pool, blocks `VACUUM`, magnifies lock contention | Commit local DB + outbox row first; execute HTTP calls outside the transaction |
| Using `SERIALIZABLE` without a retry loop | Transient `40001` errors surface as 500 errors to callers | Wrap `SERIALIZABLE` and `REPEATABLE READ` writes in a bounded retry loop with jitter |
| Retrying `23505` unique violations as transient errors | Repeats an invalid write instead of reporting conflict or handling idempotently | Retry only `40001`/`40P01` (or MongoDB transient labels); handle `23505` with `ON CONFLICT` |
| Locking rows in arbitrary order (`WHERE id IN (...) FOR UPDATE` without `ORDER BY`) | Two concurrent transfers lock rows in opposite order and deadlock | Add `ORDER BY id ASC` before `FOR UPDATE` |
| Using `SELECT ... FOR UPDATE SKIP LOCKED` inside `REPEATABLE READ` | Stale transaction snapshot ignores newly inserted jobs | Run job-queue `SKIP LOCKED` polls under `READ COMMITTED` |

## Checklist

- [ ] No external network or slow disk I/O executes inside an open database transaction.
- [ ] `idle_in_transaction_session_timeout` and `statement_timeout` are configured for app connections.
- [ ] Isolation level matches the concurrency risk (`READ COMMITTED` for simple CRUD; `REPEATABLE READ` or `SERIALIZABLE` documented when multi-row invariants require it).
- [ ] Multi-row `FOR UPDATE` locks acquire rows in a deterministic `ORDER BY` sequence.
- [ ] Every `REPEATABLE READ` / `SERIALIZABLE` / pessimistic-lock transaction has a bounded retry loop with exponential back-off and jitter for `40001` / `40P01`.
- [ ] Retried write operations and external commands are idempotent (`ON CONFLICT` / `idempotency_key` / transactional outbox).
- [ ] Job queues using `SKIP LOCKED` execute under `READ COMMITTED`.

## Verify with context7 and gh_grep

- **context7:** Check your driver's exact transaction context-manager and SQLSTATE/error-label APIs (`psycopg` 3 `conn.transaction()`, `asyncpg` `SerializationError`, `prisma.$transaction({ isolationLevel: ... })`, MongoDB `session.withTransaction`). Queries: `postgresql transaction isolation serializable`, `psycopg 3 transaction retry sqlstate`, `prisma interactive transaction isolationLevel`.
- **gh_grep:** Search `SERIALIZABLE` or `40001` to confirm conflict retry handling exists wherever elevated isolation is used; search `FOR UPDATE` to verify deterministic `ORDER BY` lock acquisition.

## Sources

- PostgreSQL Documentation — Concurrency Control & Transaction Isolation: https://www.postgresql.org/docs/current/
- PostgreSQL Documentation — Explicit Locking: https://www.postgresql.org/docs/current/explicit-locking.html
- MongoDB Manual — Read Concern & Multi-Document Transactions: https://www.mongodb.com/docs/manual/reference/read-concern/
