# Migrations

Covers expand-and-contract patterns, zero-downtime PostgreSQL DDL changes, batched backfills, rollback planning and realistic-data testing; checked against PostgreSQL 17/18, Prisma and Alembic documentation on 2026-11-26. Per `AGENTS.md`, database migrations are **High risk** (requiring both `reviewer` and `security-auditor`) and running migrations requires explicit user approval under **Approval gates**.

## Contents

- Expand-and-contract workflow
- Zero-downtime DDL rules (PostgreSQL)
- Batched data backfills
- Rollback strategies and approval gates
- Testing on realistic data

## Guidance

### Expand-and-contract workflow

During rolling deployments, old and new application versions run concurrently against the **same** database schema. Breaking changes (renaming a column, dropping a column, changing a column's type in place) immediately break old instances. Use four separate deployments instead:

| Phase | Database change | Application state |
|---|---|---|
| 1. **Expand** | Add nullable column, new table, `NOT VALID` constraint, or `CREATE INDEX CONCURRENTLY` | Old code ignores new structures |
| 2. **Dual-write & backfill** | Backfill historical rows in batches from old structure to new | New code writes to both old and new columns; reads from old (or falls back to old) |
| 3. **Switch & validate** | Run `VALIDATE CONSTRAINT` (and `SET NOT NULL` once clean) | Application reads and writes new column; old column kept populated if fast code rollback is needed |
| 4. **Contract** | Drop old column, old table, or transitional trigger in a subsequent release | Old application instances are 100% drained and rollback window has closed |

Never combine Expand and Contract in a single migration or PR when zero-downtime deployment is required.

### Zero-downtime DDL rules (PostgreSQL)

Always prefix live DDL migrations with lock and statement timeouts so a queued `ACCESS EXCLUSIVE` lock never stalls all incoming application traffic behind a long-running `SELECT`:

```sql
SET lock_timeout = '2s';
SET statement_timeout = '10s';
```

If lock acquisition times out, fail fast and retry in a short deployment loop rather than blocking the connection pool.

| Change | Unsafe (blocks traffic) | Safe zero-downtime alternative |
|---|---|---|
| Add column with constant default | Safe in PG 11+ (`DEFAULT 0` is metadata-only) **unless** default is volatile (`random()`, `clock_timestamp()`) | Use constant default, or add nullable column then backfill in batches |
| Add `NOT NULL` to existing column | `ALTER TABLE t ALTER COLUMN c SET NOT NULL` scans whole table under `ACCESS EXCLUSIVE` | **PG 18+:** `ADD CONSTRAINT ... NOT NULL col NOT VALID` then `VALIDATE CONSTRAINT`. **PG 12–17:** `ADD CONSTRAINT chk CHECK (col IS NOT NULL) NOT VALID`, `VALIDATE CONSTRAINT chk`, then `SET NOT NULL` |
| Add foreign key | `ADD CONSTRAINT fk FOREIGN KEY ...` acquires `SHARE ROW EXCLUSIVE` across both tables | `ADD CONSTRAINT fk ... NOT VALID`, then `VALIDATE CONSTRAINT fk` (`SHARE UPDATE EXCLUSIVE` allows reads and writes) |
| Create or drop index | `CREATE INDEX` blocks writes; `DROP INDEX` blocks reads and writes | `CREATE INDEX CONCURRENTLY` / `DROP INDEX CONCURRENTLY` outside a transaction block |
| Rename column or shrink/change type (`INT` -> `BIGINT`) | Breaks running old app code or rewrites entire table under `ACCESS EXCLUSIVE` | Expand-and-contract with a new column (`new_col`) |
| Add enum value | Safe in PG 12+ (`ALTER TYPE ... ADD VALUE` runs inside a transaction if not used immediately in the same txn) | Prefer `TEXT` + `CHECK` constraints for values that change often; `CHECK` swaps via `NOT VALID` + `VALIDATE` without `ACCESS EXCLUSIVE` scans |

Note: `CREATE INDEX CONCURRENTLY` cannot run inside a `BEGIN ... COMMIT` block. In Prisma, put it in its own edited `migration.sql` outside transactions (or disable transaction wrapping where supported); in Alembic, run `with op.get_context().autocommit_block():`.

### Batched data backfills

Never run an unbounded `UPDATE big_table SET new_col = old_col;` in one transaction. Single-transaction backfills hold locks across millions of rows, spike WAL generation, cause replication lag, and trigger massive table bloat.

**Safe backfill rules:**
1. **Chunk by primary key range** (for example, `1,000–10,000` rows per batch) using keyset iteration (`WHERE id > $last_id AND id <= $end_id AND new_col IS NULL`).
2. **Commit each batch independently** and pause briefly (for example, 50–200 ms) between batches, checking replica lag (`pg_stat_replication`) and autovacuum load.
3. **Make the script idempotent and resumable** (`AND new_col IS NULL`) so a cancelled run restarts safely from the last committed ID.
4. **Pause or throttle** automatically if replica `replay_lag` exceeds your threshold (for example, `5s`).

### Rollback strategies and approval gates

Before asking the user for approval to run a migration (`AGENTS.md` ## Approval gates), document:
- **Forward compatibility:** Can the previous application release still run safely if code rolls back after Expand? (Yes, if Expand only adds optional objects.)
- **Rollback command or forward-fix:**
  - For additive Expand migrations, rolling back application code alone is usually safer than dropping newly populated columns immediately.
  - For destructive Contract migrations (dropping columns/tables, narrowing types), **data loss is irreversible** once executed. Require a verified backup/snapshot and explicit user approval before running.
  - In Prisma, `prisma migrate resolve --rolled-back <migration>` clears a failed migration record after manual cleanup; in Alembic, verify `downgrade()` works on non-empty tables or document why rollback uses a forward-fix migration.

### Testing on realistic data

Empty fixture databases validate syntax only — they hide lock contention, table rewrites, failing `NOT NULL` backfills on legacy rows, and multi-minute index builds.

Before shipping a migration on a large or hot table:
1. Run the migration against an anonymised production-sized clone or synthetic multi-million-row dataset.
2. Measure execution time, `pg_locks` lock modes acquired, and whether concurrent read/write load continues unimpeded.
3. Verify both **N-1** (old) and **N** (new) application builds pass integration tests against the intermediate Expand schema.
4. Verify no orphaned `INVALID` indexes remain (`SELECT relname FROM pg_class c JOIN pg_index i ON c.oid = i.indexrelid WHERE NOT i.indisvalid;`).

## Examples

### Zero-downtime `NOT NULL` and FK migration (PostgreSQL 17 and 18)

```sql
-- Bad: acquires ACCESS EXCLUSIVE and scans entire table while blocking all reads and writes
ALTER TABLE orders ALTER COLUMN account_id SET NOT NULL;
ALTER TABLE orders ADD CONSTRAINT fk_orders_account
    FOREIGN KEY (account_id) REFERENCES accounts(id);

-- Good (PostgreSQL 12-17 compatible, zero long-blocking table scan):
SET lock_timeout = '2s';
-- Step 1: fast metadata-only check constraint (enforced for new/updated rows immediately)
ALTER TABLE orders ADD CONSTRAINT chk_orders_account_not_null
    CHECK (account_id IS NOT NULL) NOT VALID;
-- Step 2: scan existing rows with SHARE UPDATE EXCLUSIVE (reads + writes continue)
ALTER TABLE orders VALIDATE CONSTRAINT chk_orders_account_not_null;
-- Step 3: promote to NOT NULL (instant because chk_orders_account_not_null is valid), then drop check
ALTER TABLE orders ALTER COLUMN account_id SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT chk_orders_account_not_null;

-- Good (PostgreSQL 18+ native NOT NULL NOT VALID):
ALTER TABLE orders ADD CONSTRAINT nn_orders_account_id NOT NULL account_id NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT nn_orders_account_id;

-- Good FK (all modern PG versions):
ALTER TABLE orders ADD CONSTRAINT fk_orders_account
    FOREIGN KEY (account_id) REFERENCES accounts(id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_account;
```

### Resumable keyset-batched backfill (SQL / script pattern)

```sql
-- Run repeatedly in separate short transactions until 0 rows are updated;
-- advance :last_id to the max id returned each batch.
WITH batch AS (
    SELECT id
    FROM orders
    WHERE id > :last_id
      AND total_cents_v2 IS NULL
    ORDER BY id ASC
    LIMIT 2000
    FOR UPDATE SKIP LOCKED
)
UPDATE orders o
SET total_cents_v2 = o.total_amount * 100
FROM batch b
WHERE o.id = b.id
RETURNING o.id;
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Running `ALTER TABLE` without `lock_timeout` | Queues behind a slow `SELECT` and blocks all subsequent app queries | Set `SET lock_timeout = '2s'` and retry safely if blocked |
| Renaming or dropping a column while old code is still running | Old app instances crash immediately during rolling deploy | Use Expand, Dual-write, Switch, then Contract in a later release |
| Adding `NOT NULL` or `FOREIGN KEY` directly on a large table | Scans the whole table under `ACCESS EXCLUSIVE` / `SHARE ROW EXCLUSIVE` | Use `NOT VALID` followed by `VALIDATE CONSTRAINT` |
| Backfilling millions of rows in one `UPDATE` | Massive WAL spike, replication lag, long locks, table bloat | Backfill in idempotent PK-chunked batches with pauses and lag checks |
| Running `prisma migrate dev` or `db push` against production | Attempts shadow-DB resets or destructive drift sync | Use `prisma migrate deploy` (or `alembic upgrade head`) with reviewed SQL files |
| Testing migrations only against empty test databases | Misses table rewrites, dirty historical NULLs, and multi-minute locks | Test against realistic volume and verify N-1 + N app compatibility |

## Checklist

- [ ] Breaking changes split across Expand, Backfill/Dual-write, Switch, and Contract deployments.
- [ ] `SET lock_timeout` and `SET statement_timeout` present on DDL scripts targeting live tables.
- [ ] New indexes created with `CONCURRENTLY` outside a transaction block; `indisvalid` checked afterwards.
- [ ] New `CHECK`, `FOREIGN KEY`, and (PG 18+) `NOT NULL` constraints use `NOT VALID` + `VALIDATE CONSTRAINT` on large tables.
- [ ] Backfills run in idempotent PK-ordered batches with throttling and replication-lag checks.
- [ ] Rollback plan (code rollback compatibility vs forward-fix vs verified snapshot) documented before running.
- [ ] Migration tested against realistic data volume and both N-1 and N application builds.
- [ ] Explicit user approval obtained before running migrations (`AGENTS.md` ## Approval gates), and both `reviewer` and `security-auditor` consulted (`AGENTS.md` ## Triage).
- [ ] `docs/DB.md` (architect) and `CHANGELOG.md` (implementer) updated after migration ships.

## Verify with context7 and gh_grep

- **context7:** Check your PostgreSQL version for `NOT NULL ... NOT VALID` (PG 18+) vs `CHECK (... IS NOT NULL) NOT VALID` (PG 12–17), and your migration runner's transaction-bypass syntax (`alembic` `autocommit_block()`, `prisma` `--create-only`). Queries: `postgresql 18 alter table not null not valid`, `alembic autocommit_block create index concurrently`, `prisma migrate deploy create-only`.
- **gh_grep:** Search `ALTER TABLE` and `CREATE INDEX` in existing migration files to audit `lock_timeout`, `CONCURRENTLY`, and `NOT VALID` conventions in the repo.

## Sources

- PostgreSQL Documentation (`ALTER TABLE`, Locking, `CREATE INDEX CONCURRENTLY`): https://www.postgresql.org/docs/current/
- PostgreSQL 18 Release Notes (`NOT NULL ... NOT VALID`): https://www.postgresql.org/docs/18/release-18.html
- Prisma Documentation (`prisma migrate deploy` & custom migrations): https://www.prisma.io/docs
- Alembic Documentation: https://alembic.sqlalchemy.org/
