# PostgreSQL

Covers PostgreSQL 17 and 18 types, constraints, roles, extensions, locking behaviour, VACUUM and operational checks; checked against PostgreSQL 17 and 18 official documentation on 2026-11-26. The project's deployed server version determines which features are available.

## Contents

- Data types
- Constraints specific to PostgreSQL
- Roles and privileges
- Extensions
- Locking behaviour
- VACUUM and autovacuum
- Operational checks

## Guidance

### Data types

Choose the narrowest type that correctly represents the domain.

| Category | Preferred type | Notes |
|---|---|---|
| Integer IDs | `BIGINT GENERATED ALWAYS AS IDENTITY` | Never reuse a dropped sequence; prefer over `SERIAL` (deprecated pattern) |
| Public-facing IDs | `UUID` default `uuidv7()` (PG 18+) or `gen_random_uuid()` (PG 13+) | Prefer time-ordered `uuidv7()` for high-insert tables to avoid B-tree page splits; `gen_random_uuid()` generates random UUIDv4 |
| Money | `NUMERIC(precision, 2)` | Never `FLOAT` or `DOUBLE PRECISION`—floating-point rounding loses cents |
| Timestamps | `TIMESTAMPTZ` | Always store with time zone; display in the application layer |
| Short text | `TEXT` with a `CHECK` or `VARCHAR(n)` | In PostgreSQL, `TEXT` and `VARCHAR` have identical storage; `VARCHAR(n)` enforces length |
| Structured data | `JSONB` | Prefer `JSONB` over `JSON`; `JSONB` is stored binary and supports indexes |
| Booleans | `BOOLEAN` | Not `SMALLINT`; use `TRUE`/`FALSE` literals |
| Enumerations | `TEXT` with `CHECK (col IN (...))` or `CREATE TYPE ... AS ENUM` | ENUMs are fast but require `ALTER TYPE` to add values; CHECK constraints are easier to migrate |
| IP addresses | `INET` or `CIDR` | Built-in validation; supports `>>` containment operators |
| Full-text search | `TSVECTOR` with a GIN index | Generate with `to_tsvector('english', col)` |

### Constraints specific to PostgreSQL

**Exclusion constraints** (`EXCLUDE`) enforce that no two rows satisfy a predicate simultaneously—useful for non-overlapping time ranges:

```sql
CREATE TABLE reservations (
    room_id  INT NOT NULL,
    during   TSTZRANGE NOT NULL,
    EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);
```

Requires the `btree_gist` extension for mixed B-tree and GiST exclusion.

**Deferrable constraints** can be deferred to the end of a transaction:

```sql
FOREIGN KEY (user_id) REFERENCES users(id) DEFERRABLE INITIALLY DEFERRED
```

Use when inserting related rows whose IDs are not yet committed.

**Generated columns** compute a value from other columns. PostgreSQL 12–17 support `STORED` only; PostgreSQL 18 adds `VIRTUAL` (the default if omitted) and still requires `STORED` for columns you want to index:

```sql
ALTER TABLE products ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('english', name || ' ' || description)) STORED;
```

### Roles and privileges

PostgreSQL uses role-based access control. Roles can be granted to other roles.

```sql
-- Application role: connect and DML only on the app schema
CREATE ROLE app_user LOGIN PASSWORD '<APP_PASSWORD>';
GRANT CONNECT ON DATABASE mydb TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

-- Migration role: DDL rights, used only by the migration runner
CREATE ROLE migrator LOGIN PASSWORD '<MIGRATOR_PASSWORD>';
GRANT ALL ON DATABASE mydb TO migrator;
```

Never connect from the application with a superuser role. Separate the migration role from the application role.

### Extensions

Install extensions in a dedicated schema or the `extensions` schema, not `public`.

| Extension | Purpose |
|---|---|
| `pgcrypto` | `gen_random_uuid()`, hashing |
| `pg_trgm` | Trigram similarity; supports `ILIKE` and fuzzy-search indexes |
| `btree_gist` | Composite GiST indexes mixing B-tree columns |
| `uuid-ossp` | `uuid_generate_v4()` (prefer `pgcrypto` `gen_random_uuid()` in PG 13+) |
| `pg_stat_statements` | Tracks query execution statistics; always enable in production |
| `PostGIS` | Geographic data types and spatial indexes |

Enable with `CREATE EXTENSION IF NOT EXISTS <name>;`. Document every extension in `docs/DB.md`.

### Locking behaviour

PostgreSQL uses MVCC; readers do not block writers. Explicit locks are only needed for writes that must exclude concurrent updates.

**Lock hierarchy (weakest to strongest):**

`ACCESS SHARE` → `ROW SHARE` → `ROW EXCLUSIVE` → `SHARE UPDATE EXCLUSIVE` → `SHARE` → `SHARE ROW EXCLUSIVE` → `EXCLUSIVE` → `ACCESS EXCLUSIVE`

| Operation | Lock acquired | Blocks |
|---|---|---|
| `SELECT` | ACCESS SHARE | ACCESS EXCLUSIVE only |
| `INSERT`, `UPDATE`, `DELETE` | ROW EXCLUSIVE | SHARE, EXCLUSIVE, ACCESS EXCLUSIVE |
| `CREATE INDEX` (non-concurrent) | SHARE | ROW EXCLUSIVE and above |
| `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | ACCESS EXCLUSIVE only |
| `ALTER TABLE` | ACCESS EXCLUSIVE | Everything |
| `VACUUM` (auto) | SHARE UPDATE EXCLUSIVE | ACCESS EXCLUSIVE only |
| `LOCK TABLE` | Specified level | Corresponding |

`ACCESS EXCLUSIVE` from `ALTER TABLE` blocks all reads and writes. On a large live table, this causes visible downtime. Use the expand-and-contract migration pattern to avoid it.

**Advisory locks** (`pg_advisory_lock`) coordinate application-level operations (e.g., cron jobs) without table locks. Always release them in a `FINALLY` block; they are session-scoped and survive transaction rollback.

**Detecting lock waits:**

```sql
SELECT pid, wait_event_type, wait_event, query, age(clock_timestamp(), query_start) AS duration
FROM pg_stat_activity
WHERE wait_event_type = 'Lock'
ORDER BY duration DESC;
```

### VACUUM and autovacuum

PostgreSQL's MVCC leaves dead tuples (old row versions) in place after `UPDATE` and `DELETE`. VACUUM reclaims them.

**Autovacuum** runs automatically; configure per-table when the defaults are too aggressive (high-write tables) or too slow (large tables that bloat):

```sql
ALTER TABLE high_write_table SET (
    autovacuum_vacuum_scale_factor = 0.01,  -- trigger at 1% dead tuples (default 20%)
    autovacuum_vacuum_cost_delay = 2        -- ms between I/O bursts
);
```

PostgreSQL 17 introduced `TidStore` for vacuum dead-tuple tracking, sharply cutting `maintenance_work_mem` usage and multi-pass index scans; PostgreSQL 18 adds an asynchronous I/O (AIO) subsystem accelerating vacuum and sequential scans.

**Signs of vacuum lag:**
- Table bloat: `pg_relation_size` grows while row count stays flat.
- Transaction ID wraparound warning in the logs (`WARNING: database "X" must be vacuumed within Y transactions`). Resolve immediately with `VACUUM FREEZE`.
- `pg_stat_user_tables.n_dead_tup` persistently above 10 % of `n_live_tup`.

**Manual vacuum when needed:**

```sql
-- Aggressive vacuum + freeze on a specific table (requires user approval; locks SHARE UPDATE EXCLUSIVE)
VACUUM (ANALYZE, VERBOSE) orders;
```

### Operational checks

Run these checks regularly in production:

```sql
-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) AS total_size
FROM pg_class WHERE relkind = 'r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;

-- Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '30 seconds'
ORDER BY duration DESC;

-- Unused indexes (high write, low scan)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan < 50 ORDER BY idx_scan;

-- Replication lag (streaming replica)
SELECT application_name,
       state,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS replay_lag_bytes,
       write_lag,
       replay_lag
FROM pg_stat_replication;
```

> [!WARNING]
> Queries against `pg_stat_activity` and `pg_stat_replication` may expose session details. Restrict access to the monitoring role.

## Examples

### JSONB column with index

```sql
-- Storing arbitrary metadata on orders
ALTER TABLE orders ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}';

-- Index a frequently filtered key
CREATE INDEX ON orders USING GIN (metadata);

-- Or a partial index on a specific path value
CREATE INDEX ON orders ((metadata->>'source')) WHERE metadata ? 'source';

-- Query
SELECT * FROM orders WHERE metadata->>'source' = 'mobile_app';
```

### Full-text search with generated column

```sql
ALTER TABLE articles ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,''))
    ) STORED;

CREATE INDEX ON articles USING GIN (search_vector);

SELECT title FROM articles
WHERE search_vector @@ plainto_tsquery('english', 'database performance');
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using `FLOAT` for money | Rounding errors accumulate | `NUMERIC(12,2)` |
| Storing timestamps without time zone | Ambiguous in multi-region or DST transitions | `TIMESTAMPTZ` |
| Running as superuser from the app | One injection = full database compromise | Use a least-privilege app role |
| Ignoring autovacuum lag | Table bloat, XID wraparound, query slowdown | Monitor `n_dead_tup`; tune per-table autovacuum |
| `ALTER TABLE` on a large live table | ACCESS EXCLUSIVE lock causes downtime | Use expand-and-contract pattern |
| Not enabling `pg_stat_statements` | Cannot identify slow queries | Add to `shared_preload_libraries` before restart |

## Checklist

- [ ] All monetary values use `NUMERIC`, not `FLOAT`.
- [ ] All timestamps use `TIMESTAMPTZ`.
- [ ] Application connects with a least-privilege role (not superuser).
- [ ] `pg_stat_statements` is enabled.
- [ ] Autovacuum thresholds reviewed for high-write tables.
- [ ] No `ALTER TABLE` on a large table without an expand-and-contract plan.
- [ ] Extensions documented in `docs/DB.md`.
- [ ] Replication lag monitored for read replicas.

## Verify with context7 and gh_grep

- **context7:** Confirm `GENERATED ALWAYS AS` (`VIRTUAL` vs `STORED`), `uuidv7()`, and `TidStore` vacuum behaviour for the exact server version (PG 17 vs PG 18). Query: `postgresql 18 generated columns virtual stored`, `postgresql 17 vacuum tidstore`.
- **gh_grep:** Search `CREATE EXTENSION` to audit which extensions are already installed; search `TIMESTAMPTZ` vs `TIMESTAMP` to find type inconsistencies.

## Sources

- PostgreSQL Documentation — Data Types: https://www.postgresql.org/docs/current/datatype.html
- PostgreSQL Documentation — VACUUM: https://www.postgresql.org/docs/current/sql-vacuum.html
- PostgreSQL Documentation — Explicit Locking: https://www.postgresql.org/docs/current/explicit-locking.html
- PostgreSQL 17 Release Notes: https://www.postgresql.org/docs/17/release-17.html
- PostgreSQL 18 Release Notes: https://www.postgresql.org/docs/18/release-18.html
