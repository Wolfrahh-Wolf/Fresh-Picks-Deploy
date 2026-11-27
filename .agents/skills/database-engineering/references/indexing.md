# Indexing

Covers index access methods, composite column order, partial and covering indexes, expression indexes and write amplification; checked against PostgreSQL 17/18 and MongoDB 8.0 official documentation on 2026-11-26. Check the project's database version before using PostgreSQL 18 B-tree skip scan or driver-specific options.

## Contents

- Index types (access methods)
- Composite index column order
- Partial indexes
- Covering indexes (`INCLUDE`) and index-only scans
- Expression and operator-class indexes
- Write cost, HOT updates and index hygiene

## Guidance

### Index types (access methods)

Choose the access method to match both the data type and the query operator.

| Index type | Supported operators / use case | Trade-offs |
|---|---|---|
| **B-tree** (default) | `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `IN`, prefix `LIKE 'abc%'`, `IS NULL`, `ORDER BY` | Balanced general-purpose tree; largest per-row footprint among specialised types |
| **GIN** (Generalized Inverted) | Multi-valued data: `JSONB` (`@>`, `?`, `?&`, `?|`), arrays (`@>`, `&&`), `TSVECTOR` (`@@`) | Slow synchronous updates unless `fastupdate` pending list is enabled (which adds periodic cleanup spikes) |
| **GiST** (Generalized Search Tree) | Ranges (`TSTZRANGE` overlap `&&`), geometry/PostGIS, `EXCLUDE` constraints, nearest-neighbour (`<->`), `pg_trgm` `ILIKE '%sub%'` | Lossy on some types (requires heap recheck); smaller than GIN for trigrams, slower for exact `TSVECTOR` lookups |
| **SP-GiST** | Non-balanced partitioned spaces: `INET`/`CIDR` containment, quadtrees, prefix tries | Fast on skewed hierarchical spaces; narrower operator support than B-tree/GiST |
| **BRIN** (Block Range Index) | Massive append-only tables whose physical row order correlates with column values (`created_at`, sequential `id`) | Stores only min/max per block range (`pages_per_range`), 100x–1000x smaller than B-tree; ineffective if rows are updated or randomly ordered |
| **Hash** | Exact equality (`=`) only on long scalar values | WAL-logged and crash-safe in PostgreSQL 10+; cannot sort, enforce uniqueness, or serve range queries — default to B-tree unless measured |

For MongoDB compound index key ordering, apply the Equality, Sort, Range (ESR) rule documented in [mongodb.md](mongodb.md).

### Composite index column order

Order columns in a multi-column B-tree index from **equality** to **sort / range**:

1. **Equality columns (`=`, small `IN`) first.** If one column is also queried alone frequently, put it first; otherwise put the most selective equality column first.
2. **Sort (`ORDER BY`) or range (`>`, `<`, `BETWEEN`) column last.** Once a range condition occurs on column K, columns after K cannot be narrowed by tree traversal in the same scan.

**Leftmost prefix rule:** An index on `(tenant_id, status, created_at)` accelerates queries filtering on `(tenant_id)`, `(tenant_id, status)`, or `(tenant_id, status, created_at)`. Prior to PostgreSQL 18, queries filtering only on `(status, created_at)` could not use this index efficiently. PostgreSQL 18 adds B-tree **skip scan**, allowing the planner to step across distinct leading values when the leading column has low cardinality (for example, a small set of statuses), though explicit leading-column alignment remains faster and predictable across versions.

For `ORDER BY a ASC, b DESC`, match the sort directions in the index definition `(a ASC, b DESC)` so the planner avoids an extra `Sort` node.

### Partial indexes

A partial index includes a `WHERE` predicate so only matching rows enter the index:

```sql
CREATE INDEX CONCURRENTLY idx_jobs_pending
    ON jobs (scheduled_at)
    WHERE status IN ('queued', 'retrying');
```

**When to use:**
- Queries consistently filter on a constant predicate (active rows, soft deletes `WHERE deleted_at IS NULL`, non-null external IDs).
- Conditional uniqueness: `CREATE UNIQUE INDEX CONCURRENTLY uq_users_active_email ON users (email) WHERE deleted_at IS NULL;`.

**Trade-off:** Smaller index stays hot in `shared_buffers`, and rows outside the predicate incur zero index write overhead. The query's `WHERE` clause must logically imply the index predicate (for example, querying `WHERE status = 'queued'` uses the partial index above; querying `WHERE status = $1` with a bound parameter cannot use it because the planner does not know `$1` at plan time).

### Covering indexes (`INCLUDE`) and index-only scans

Adding `INCLUDE (col1, col2)` appends non-key payload columns to B-tree (or GiST) leaf pages without including them in the search key or uniqueness check:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_covering
    ON orders (customer_id, created_at DESC)
    INCLUDE (status, total_cents);
```

This enables an **Index-Only Scan** when every column in `SELECT`, `WHERE`, and `ORDER BY` is present in the index key or `INCLUDE` list.

**Caveat:** Index-Only Scans still touch the table heap whenever PostgreSQL's Visibility Map (VM) shows the page is not all-visible (`Heap Fetches > 0` in `EXPLAIN`). Keep autovacuum tuned on frequently updated tables so VM bits stay set.

### Expression and operator-class indexes

Index the exact expression used in `WHERE` — querying `LOWER(email) = 'a@b.com'` cannot use a plain index on `(email)`:

```sql
CREATE INDEX CONCURRENTLY idx_users_lower_email ON users (LOWER(email));
```

For prefix `LIKE 'prefix%'` queries under non-`C` locales (`en_US.UTF-8`), a standard B-tree index is ignored unless created with `text_pattern_ops` (or `varchar_pattern_ops`):

```sql
CREATE INDEX CONCURRENTLY idx_users_username_prefix ON users (username text_pattern_ops);
```

### Write cost, HOT updates and index hygiene

Every index adds CPU, WAL, and I/O overhead to `INSERT`, `DELETE`, and non-HOT `UPDATE` statements.

- **HOT (Heap-Only Tuple) updates:** PostgreSQL skips updating indexes on an `UPDATE` only if **no indexed column changes** and the new row fits on the same 8 KiB heap page. Indexing volatile columns (`updated_at`, `last_seen_at`, `retry_count`) on hot tables breaks HOT updates and doubles write amplification and index bloat.
- **Avoid redundant prefixes:** If `(a, b)` exists, a separate index on `(a)` is usually redundant — verify whether `(a)` is serving a unique constraint or needs smaller size before keeping both.
- **Create and drop live indexes `CONCURRENTLY`:** Standard `CREATE INDEX` acquires a `SHARE` lock that blocks all writes; `DROP INDEX` acquires `ACCESS EXCLUSIVE`. Always use `CONCURRENTLY` outside a transaction block. If `CREATE INDEX CONCURRENTLY` fails mid-build, it leaves an `INVALID` index (`pg_index.indisvalid = false`) that still slows writes and must be dropped with `DROP INDEX CONCURRENTLY` and recreated.
- **Audit unused indexes safely:** Check `pg_stat_user_indexes` over a full business cycle (week/month) on **both primary and read replicas** before dropping an index, and never drop indexes backing `UNIQUE` or `FOREIGN KEY` constraints without checking schema dependencies.

## Examples

### Composite order and partial index (bad to good)

```sql
-- Query pattern:
-- SELECT id, total_cents FROM invoices
-- WHERE account_id = $1 AND status = 'open' AND due_date < now()
-- ORDER BY due_date ASC;

-- Bad: range column first, includes closed rows never queried by this path, blocks writes on creation
CREATE INDEX idx_invoices_bad ON invoices (due_date, account_id, status);

-- Good: equality column first, range/sort column second, partial predicate shrinks index,
-- INCLUDE satisfies SELECT without heap reads, CONCURRENTLY avoids write lock
CREATE INDEX CONCURRENTLY idx_invoices_open_acct_due
    ON invoices (account_id, due_date)
    INCLUDE (total_cents)
    WHERE status = 'open';
```

### Auditing unused and invalid indexes

```sql
-- 1. Find invalid indexes left behind by failed CONCURRENTLY builds
SELECT c.relname AS index_name, i.indisvalid
FROM pg_index i
JOIN pg_class c ON c.oid = i.indexrelid
WHERE NOT i.indisvalid;

-- 2. Find large non-unique indexes with zero or near-zero scans (check replicas too!)
SELECT s.schemaname, s.relname AS table_name, s.indexrelname AS index_name,
       s.idx_scan, pg_size_pretty(pg_relation_size(s.indexrelid)) AS index_size
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan < 10
  AND NOT i.indisunique
  AND NOT i.indisprimary
ORDER BY pg_relation_size(s.indexrelid) DESC;
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Putting a range column before an equality column in a composite index | Planner scans a wide range instead of seeking the exact equality prefix | Place equality columns first, then sort/range columns |
| Creating an index on a live table without `CONCURRENTLY` | Acquires `SHARE` lock, stalling all `INSERT`/`UPDATE`/`DELETE` traffic | Use `CREATE INDEX CONCURRENTLY` outside a transaction block |
| Leaving an `INVALID` index after a cancelled concurrent build | Continues slowing writes while the planner never uses it for reads | Check `pg_index.indisvalid`, run `DROP INDEX CONCURRENTLY`, then rebuild |
| Indexing volatile columns like `updated_at` on heavily updated tables | Disables PostgreSQL HOT updates, multiplying WAL and index bloat | Index volatile columns only if proven necessary by slow-query telemetry |
| Dropping a "zero-scan" index without checking read replicas | Breaks analytical or reporting queries routed to replicas | Inspect `pg_stat_user_indexes` across primary and every replica |
| Expecting a partial index (`WHERE status = 'open'`) to match `WHERE status = $1` | Parameterised `$1` hides the constant from the planner | Hard-code the matching constant in the query predicate or drop the `WHERE` filter from the index |

## Checklist

- [ ] Every foreign key column has a supporting index (as leading column of an index or standalone).
- [ ] Composite indexes place equality columns before sort/range columns and match `ORDER BY` direction.
- [ ] `INCLUDE` columns are added where covering Index-Only Scans eliminate hot heap lookups.
- [ ] Partial indexes (`WHERE ...`) are used for skewed status flags or soft-deleted tables, and query predicates match literally.
- [ ] Live index builds and drops use `CONCURRENTLY` outside a transaction block.
- [ ] `pg_index.indisvalid` verified `true` after concurrent index creation.
- [ ] Redundant prefix indexes and unused non-unique indexes reviewed across primary and replicas.
- [ ] Write amplification and HOT-update impact assessed before indexing frequently updated columns.

## Verify with context7 and gh_grep

- **context7:** Verify PostgreSQL version support for `INCLUDE` (PG 11+), `BRIN` multi-minmax / bloom (`PG 14+`), and B-tree skip scan (`PG 18+`). Queries: `postgresql create index concurrently include`, `postgresql 18 btree skip scan`, `postgresql gin jsonb_path_ops`.
- **gh_grep:** Search `CREATE INDEX` across migrations to ensure `CONCURRENTLY` is used on existing tables; search `pg_trgm` or `USING GIN` to see established index operator conventions in the repo.

## Sources

- PostgreSQL Documentation (Indexes, Access Methods, Partial & Covering Indexes): https://www.postgresql.org/docs/current/
- PostgreSQL 18 Release Notes (B-tree Skip Scan): https://www.postgresql.org/docs/18/release-18.html
- MongoDB Manual — Data Modeling & Indexing: https://www.mongodb.com/docs/manual/data-modeling/
