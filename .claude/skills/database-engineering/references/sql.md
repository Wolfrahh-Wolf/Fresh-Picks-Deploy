# SQL

Covers standard SQL as used in PostgreSQL 17: joins, aggregation, CTEs, window functions, NULL semantics and parameterised queries; checked against the PostgreSQL 17 documentation on 2026-11-26.

## Contents

- Joins
- Aggregation and GROUP BY
- Common Table Expressions (CTEs)
- Window functions
- NULL semantics
- Parameterised queries

## Guidance

### Joins

| Join type | Returns | Use when |
|---|---|---|
| `INNER JOIN` | Rows matching in both tables | The relationship is mandatory |
| `LEFT JOIN` | All left rows; NULLs for unmatched right | The right side is optional |
| `RIGHT JOIN` | All right rows; NULLs for unmatched left | Rarely needed; rewrite as LEFT JOIN with tables swapped |
| `FULL OUTER JOIN` | All rows from both; NULLs where unmatched | Reconciliation queries |
| `CROSS JOIN` | Cartesian product | Generating combinations; never accidental |

Always qualify column names with the table alias when joining two or more tables. Ambiguous column references are a maintenance hazard.

```sql
-- Bad: unqualified columns
SELECT id, name, order_date FROM users JOIN orders ON users.id = orders.user_id;

-- Good: qualified, explicit columns
SELECT u.id, u.name, o.order_date
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.status = 'pending';
```

### Aggregation and GROUP BY

Aggregation collapses groups of rows into summary rows. Every column in `SELECT` that is not an aggregate function must appear in `GROUP BY`.

```sql
-- Count orders per status with a total value threshold
SELECT
    o.status,
    COUNT(*)           AS order_count,
    SUM(o.total)       AS total_value
FROM orders o
GROUP BY o.status
HAVING SUM(o.total) > 1000
ORDER BY total_value DESC;
```

`HAVING` filters after aggregation; `WHERE` filters before. Never use `HAVING` for conditions that can be expressed in `WHERE`—push filters down to reduce the rows aggregated.

**Filter aggregates** avoid a subquery when counting a subset:

```sql
SELECT
    COUNT(*)                                     AS total_orders,
    COUNT(*) FILTER (WHERE status = 'shipped')   AS shipped_count
FROM orders;
```

### Common Table Expressions (CTEs)

CTEs (`WITH`) name an intermediate result for reuse within the same query. They improve readability; in PostgreSQL 12+ they are inlined by default (the optimiser treats them as subqueries), so the performance is usually identical to a subquery.

Force materialisation when you need the CTE evaluated exactly once (e.g., volatile functions):

```sql
WITH expensive AS MATERIALIZED (
    SELECT user_id, SUM(amount) AS total
    FROM payments
    WHERE paid_at > now() - interval '30 days'
    GROUP BY user_id
)
SELECT u.name, e.total
FROM users u
JOIN expensive e ON e.user_id = u.id;
```

**Recursive CTEs** traverse self-referential structures (trees, graphs):

```sql
WITH RECURSIVE category_tree AS (
    -- Anchor: start at the root
    SELECT id, name, parent_id, 0 AS depth
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive: join children
    SELECT c.id, c.name, c.parent_id, ct.depth + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth, name;
```

Always add a depth counter or cycle-detection guard to prevent infinite loops on cyclic data.

### Window functions

Window functions compute a value over a set of rows related to the current row without collapsing them. They run after `WHERE`, `GROUP BY` and `HAVING`.

```
FUNCTION() OVER (
    PARTITION BY <grouping column(s)>
    ORDER BY <ordering column(s)>
    ROWS/RANGE BETWEEN ...
)
```

| Function | Purpose |
|---|---|
| `ROW_NUMBER()` | Unique sequential rank per partition |
| `RANK()` | Rank with gaps on ties |
| `DENSE_RANK()` | Rank without gaps on ties |
| `LAG(col, n)` / `LEAD(col, n)` | Value n rows before/after current |
| `SUM() OVER (...)` | Running total |
| `FIRST_VALUE()` / `LAST_VALUE()` | First/last in the frame |

```sql
-- Running total of order amounts per user, ordered by date
SELECT
    user_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY user_id
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

### NULL semantics

NULL means "unknown", not zero or empty string. Comparisons with NULL always return NULL (not TRUE or FALSE).

```sql
-- Bad: this returns no rows even when status IS NULL
SELECT * FROM orders WHERE status = NULL;

-- Good
SELECT * FROM orders WHERE status IS NULL;
SELECT * FROM orders WHERE status IS NOT DISTINCT FROM NULL;  -- also works in expressions
```

Three-valued logic: `TRUE AND NULL = NULL`, `FALSE AND NULL = FALSE`, `TRUE OR NULL = TRUE`, `FALSE OR NULL = NULL`.

`COALESCE(a, b)` returns the first non-NULL value. Use it to supply defaults in expressions. `NULLIF(a, b)` returns NULL when `a = b`, useful to avoid division-by-zero: `NULLIF(denominator, 0)`.

Aggregate functions ignore NULLs by default (`SUM`, `AVG`, `COUNT(col)`). `COUNT(*)` counts all rows including those with NULLs.

### Parameterised queries

Never interpolate user-supplied values into query strings. Always use the driver's parameter syntax.

| Driver / ORM | Parameter syntax | Example |
|---|---|---|
| PostgreSQL (`psycopg` 3) | `%s` positional / `%(name)s` named | `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))` |
| `node-postgres` (`pg`) | `$1`, `$2` ... | `client.query("SELECT * FROM users WHERE id = $1", [userId])` |
| Prisma `$queryRaw` | Tagged template literal | `` prisma.$queryRaw`SELECT * FROM "User" WHERE id = ${userId}` `` |
| SQLAlchemy `text()` | `:name` | `session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})` |

Using string concatenation or f-strings bypasses parameterisation and opens SQL-injection vulnerabilities. The reviewer must reject any such pattern at `critical` severity.

## Examples

### De-duplicate with ROW_NUMBER

```sql
-- Keep only the latest order per user
WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
    FROM orders
)
SELECT user_id, id AS latest_order_id, created_at
FROM ranked
WHERE rn = 1;
```

### Safe parameterised query (psycopg 3)

```python
# Bad: string interpolation — SQL injection risk
query = f"SELECT * FROM users WHERE email = '{email}'"
cur.execute(query)

# Good: parameterised
cur.execute("SELECT * FROM users WHERE email = %s", (email,))
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `SELECT *` in application code | Schema changes silently break callers; over-fetches data | Name every column you need |
| Filtering in `HAVING` what could go in `WHERE` | Aggregates more rows than necessary | Move constant filters to `WHERE` |
| Forgetting `IS NULL` vs `= NULL` | Query silently returns wrong results | Always use `IS NULL` / `IS NOT NULL` |
| Recursive CTE without depth limit | Infinite loop on cyclic data | Add `depth < 50` guard or `CYCLE` clause (PostgreSQL 14+) |
| String-formatted queries | SQL injection | Always use parameterised queries |
| `COUNT(col)` expecting to count NULLs | NULLs are silently skipped | Use `COUNT(*)` to count all rows |

## Checklist

- [ ] Every column in `SELECT` is explicitly named (no `SELECT *` in application code).
- [ ] All user-supplied values are passed as parameters, never interpolated.
- [ ] `WHERE` filters applied before `HAVING`; `HAVING` only used for aggregate conditions.
- [ ] `NULL` comparisons use `IS NULL` / `IS NOT NULL` / `IS NOT DISTINCT FROM`.
- [ ] Recursive CTEs have a depth or cycle guard.
- [ ] Window function frame (`ROWS`/`RANGE`) is explicit when the default would be wrong.
- [ ] `EXPLAIN` reviewed for any new query in a hot path.

## Verify with context7 and gh_grep

- **context7:** Verify CTE materialisation behaviour (`WITH ... AS MATERIALIZED`) against the PostgreSQL version in use—default changed in PostgreSQL 12. Query: `postgresql cte materialized`, `postgresql window function frame`.
- **gh_grep:** Search `$queryRaw` and `text("SELECT` to audit raw SQL usage in the project for parameterisation compliance.

## Sources

- PostgreSQL 17 Documentation — Queries: https://www.postgresql.org/docs/17/queries.html
- PostgreSQL 17 Documentation — Window Functions: https://www.postgresql.org/docs/17/tutorial-window.html
- PostgreSQL 17 Documentation — WITH Queries: https://www.postgresql.org/docs/17/queries-with.html
