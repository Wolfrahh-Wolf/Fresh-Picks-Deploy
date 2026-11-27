# Query Optimization

Covers measuring query workloads, reading `EXPLAIN (ANALYZE, BUFFERS)` plans, fixing planner statistics, rewriting non-sargable and slow queries, and validating improvements; checked against PostgreSQL 17/18 and MongoDB 8.0 documentation on 2026-11-26. The project's deployed server version determines exact `EXPLAIN` defaults.

## Contents

- Measuring before optimising
- Reading EXPLAIN (ANALYZE, BUFFERS) output
- Statistics and cardinality estimation
- Rewriting slow queries
- Validating improvements

## Guidance

### Measuring before optimising

Optimise the queries that actually consume database time or block connections, not guesses:

1. **Identify top offenders with `pg_stat_statements`:** Rank queries by total time (`total_exec_time` — highest overall load), mean/p95 time (`mean_exec_time`, `max_exec_time` — worst user latency), and I/O (`shared_blks_read`, `temp_blks_written`).
2. **Reproduce on realistic data volume:** A 100-row fixture almost always chooses `Seq Scan`; test plans against production-scale row counts and realistic value skew.
3. **Run `EXPLAIN (ANALYZE, BUFFERS)`:** PostgreSQL 18 includes `BUFFERS` automatically when `ANALYZE` is specified; PostgreSQL 17 and earlier require `BUFFERS` explicitly. Writing `EXPLAIN (ANALYZE, BUFFERS)` works across all supported versions.

> [!CAUTION]
> `EXPLAIN ANALYZE` executes the statement. For `INSERT`, `UPDATE`, or `DELETE`, always wrap it in `BEGIN; EXPLAIN (ANALYZE, BUFFERS) ...; ROLLBACK;` so the analysis does not mutate data.

In MongoDB, run `.explain("executionStats")` and compare `totalDocsExamined` and `totalKeysExamined` against `nReturned`; an index-backed query aims for a ratio near `1:1` rather than a `COLLSCAN`.

### Reading EXPLAIN (ANALYZE, BUFFERS) output

Read execution plans from the **innermost indented child nodes outward**.

| Plan signal | What it means | Action |
|---|---|---|
| `rows=10` vs `actual ... rows=50000` | Planner underestimated by 5,000x; likely chose a bad join or scan | Refresh `ANALYZE`, add extended statistics, or fix non-sargable filter |
| `loops=1000` with `actual rows=50` | Node executed 1,000 times (`50,000` total rows); common inside a `Nested Loop` | Check if a `Hash Join` (better statistics) or composite index cuts inner work |
| `Seq Scan` on large table with `Rows Removed by Filter: 999000` | Scanning millions of rows to return a few | Add or fix a selective index; ensure predicate is sargable |
| `Index Only Scan` with high `Heap Fetches` | Visibility Map is stale; still hitting heap pages | Tune per-table `autovacuum` or run `VACUUM` |
| `Bitmap Heap Scan` with `lossy=...` blocks | Bitmap exceeded `work_mem`, degrading to page-level tracking | Increase session `work_mem` for analytical queries or narrow the filter |
| `Sort Method: external merge Disk: ...kB` or `Hash Batches: >1` | Sort or hash spilled to temp files because `work_mem` was exceeded | Add an index matching `ORDER BY` or raise `work_mem` for that query |
| High `shared read` vs `shared hit` | Cold cache or working set larger than `shared_buffers` | Measure buffers touched (`hit + read`), not wall-clock time alone |

**Join algorithms at a glance:**
- **Nested Loop:** Fast when the outer set is small (tens to hundreds of rows) and the inner table has an index on the join key. Slow if outer row estimates are wrong and it runs millions of times.
- **Hash Join:** Builds an in-memory hash table on the smaller input; fast for large equi-joins unless `work_mem` spills (`Batches > 1`).
- **Merge Join:** Efficient for large sorted inputs (for example, pre-sorted by B-tree indexes) without building a hash table.

### Statistics and cardinality estimation

PostgreSQL builds plans using histograms and Most Common Values (MCVs) stored in `pg_statistic`:

- **Stale statistics:** After bulk loads or deletes (`> 10%` of rows), run `ANALYZE table_name;` so the planner sees accurate row counts and distributions.
- **Skewed columns:** Increase per-column sample granularity (`ALTER TABLE orders ALTER COLUMN status SET STATISTICS 500; ANALYZE orders;`) when default 100-bucket histograms misestimate rare vs dominant values.
- **Correlated columns:** The planner assumes independent columns by default (`P(A and B) = P(A) * P(B)`). When columns correlate strongly (for example, `country` and `currency`, or `make` and `model`), create extended statistics:

```sql
CREATE STATISTICS orders_region_currency_stats (dependencies, ndistinct, mcv)
    ON region, currency FROM orders;
ANALYZE orders;
```

### Rewriting slow queries

1. **Make predicates sargable (Index-able):** Keep indexed columns bare on one side of the comparison. Never apply functions (`DATE(ts)`, `LOWER(col)`, `col + 1`) unless an identical expression index exists.
2. **Replace `OFFSET` with keyset (cursor) pagination:** `OFFSET 100000` reads and discards 100,000 rows on every page turn. Compare against the last seen `(sort_col, id)` tuple instead.
3. **Replace `NOT IN (subquery)` with `NOT EXISTS`:** `NOT IN` returns zero rows if the subquery yields any `NULL`, and often prevents efficient anti-join plans. `NOT EXISTS` handles `NULL` safely and compiles to a `Hash Anti Join`.
4. **Eliminate correlated subqueries in `SELECT`:** Rewrite per-row subselects as `LEFT JOIN`, `LATERAL` join with `LIMIT 1`, or a window function (`ROW_NUMBER()`).
5. **Avoid `SELECT DISTINCT` over over-joined tables:** Removing duplicates caused by a missing join predicate wastes CPU sorting/hashing huge intermediate sets; aggregate or deduplicate the child side first.

### Validating improvements

Measure **buffers touched** (`shared hit + shared read`) alongside execution time before and after every change. Wall-clock time alone misleads when the first run warms the OS page cache and the second run appears 10x faster with no real plan improvement.

Confirm the new plan under:
- Cold and warm runs (compare total buffer accesses and temp disk spills).
- Representative parameter values (both rare tenants and high-volume tenants).
- Concurrent load tests if the optimisation adds an index (verify acceptable write overhead).

## Examples

### Making a date filter sargable and eliminating OFFSET

```sql
-- Bad: function on indexed column prevents B-tree use; OFFSET scans discarded rows
SELECT id, total_cents
FROM orders
WHERE DATE(created_at AT TIME ZONE 'UTC') = '2026-11-26'
ORDER BY created_at DESC, id DESC
LIMIT 50 OFFSET 50000;

-- Good: half-open range uses index on (created_at DESC, id DESC); keyset cursor skips in O(log N)
SELECT id, total_cents, created_at
FROM orders
WHERE created_at >= TIMESTAMPTZ '2026-11-26 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-11-27 00:00:00+00'
  AND (created_at, id) < ($1, $2)  -- cursor from previous page
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

### Top queries from `pg_stat_statements`

```sql
SELECT
    queryid,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2)  AS mean_ms,
    rows,
    shared_blks_read,
    temp_blks_written,
    left(query, 120) AS query_snippet
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 15;
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Wrapping indexed columns in `DATE()`, `COALESCE()`, or `LOWER()` in `WHERE` | Forces `Seq Scan` instead of B-tree range/index scan | Rewrite as a half-open range or create a matching expression index |
| Running `EXPLAIN ANALYZE` on `UPDATE`/`DELETE` without `ROLLBACK` | Permanently modifies or deletes rows during analysis | Wrap write `EXPLAIN ANALYZE` in `BEGIN; ... ROLLBACK;` |
| Judging optimisation solely by second-run elapsed milliseconds | Cache warming hides bad buffer reads; query stays slow on cold data | Compare total `shared hit + shared read` buffers and `temp` spills |
| Using `NOT IN (SELECT ...)` on nullable columns | Returns zero rows if any `NULL` is present and blocks anti-join plans | Use `NOT EXISTS (SELECT 1 FROM ... WHERE ...)` |
| Using `OFFSET` for deep pagination | Performance degrades linearly (`O(N)`) as page number grows | Use keyset pagination `(sort_col, id) < ($1, $2)` |
| Testing query plans on 50-row dev fixtures | Planner picks `Seq Scan` and hides missing indexes until production | Seed production-scale volume and skewed data before tuning |

## Checklist

- [ ] Slow queries identified from `pg_stat_statements` or slow query logs before tuning.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` run on realistic data volume and representative parameters.
- [ ] Write queries analysed inside `BEGIN ... ROLLBACK`.
- [ ] Estimated vs actual rows (`actual rows * loops`) checked for >10x skew; `ANALYZE` or `CREATE STATISTICS` applied where correlated.
- [ ] No non-sargable functions wrapping indexed columns without matching expression indexes.
- [ ] Deep pagination uses keyset/cursor predicates instead of `OFFSET`.
- [ ] Zero `temp written` / external disk spills on hot-path sorts or hashes.
- [ ] Buffer reduction (`shared hit + shared read`) and latency verified after the change.

## Verify with context7 and gh_grep

- **context7:** Check `EXPLAIN` options and `pg_stat_statements` column names for the exact PostgreSQL version (`total_exec_time` in PG 13+ vs legacy `total_time`; PG 18 default `BUFFERS`). Queries: `postgresql explain analyze buffers`, `postgresql pg_stat_statements columns`, `postgresql create statistics dependencies`.
- **gh_grep:** Search `OFFSET` or `DATE(` inside SQL/ORM queries to locate non-sargable filters and deep-pagination bottlenecks.

## Sources

- PostgreSQL Documentation (`EXPLAIN`, Planner Statistics, `pg_stat_statements`): https://www.postgresql.org/docs/current/
- PostgreSQL 18 Release Notes (`EXPLAIN ANALYZE` `BUFFERS` default): https://www.postgresql.org/docs/18/release-18.html
- MongoDB Manual (`explain` results and query performance): https://www.mongodb.com/docs/manual/
