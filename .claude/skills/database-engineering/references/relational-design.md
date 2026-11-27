# Relational Design

Covers entity modelling, keys, normalisation through 3NF/BCNF, constraints, relationships and when deliberate denormalisation is justified; checked against standard relational theory and PostgreSQL 17 practice on 2026-11-26.

## Contents

- Entities and attributes
- Primary and surrogate keys
- Normalisation (1NF through BCNF)
- Constraints
- Relationships and join tables
- Deliberate denormalisation

## Guidance

### Entities and attributes

An entity maps to a table; each row is one instance. Name tables as plural nouns (`orders`, `products`). Name columns as lowercase snake_case. Each column stores one atomic value—splitting repeated groups is the first step of normalisation.

Identify the **owner** of each piece of data. If the same fact appears in two tables, one must be the source and the other must reference it; duplicated facts diverge.

### Primary and surrogate keys

| Key type | When to use | Trade-off |
|---|---|---|
| Natural key (email, ISBN) | Stable, unique by domain rule, short | Changes break every foreign key; validate carefully |
| Surrogate integer (`BIGINT GENERATED ALWAYS AS IDENTITY`) | No natural key; key may change | Extra join sometimes needed; no meaning leaks |
| UUID (`gen_random_uuid()`) | Distributed generation, public-facing IDs | Larger (16 B), random UUIDs fragment B-tree indexes; use UUIDv7 or `ulid` for insert-ordered workloads |

Default to `BIGINT GENERATED ALWAYS AS IDENTITY` unless a natural key is stable and short, or distributed generation is required.

Composite primary keys are valid for pure join tables (`order_items(order_id, product_id)`) and avoid a redundant surrogate.

### Normalisation (1NF through BCNF)

**1NF:** Each cell holds one atomic value; no repeating groups; each row is uniquely identified.

**2NF:** Every non-key attribute is fully dependent on the whole primary key (matters only with composite keys). Move partial dependencies to their own table.

**3NF:** No non-key attribute depends on another non-key attribute (no transitive dependencies). Extract the transitive chain into a new table.

**BCNF:** Every determinant is a candidate key. Addresses rare anomalies in tables with overlapping composite candidate keys.

Practical stopping point: aim for 3NF by default. BCNF rarely changes the design for typical application schemas.

| Normal form | Violation signal | Fix |
|---|---|---|
| 1NF | Comma-separated list in a column | Extract to a child table or use an array/JSONB with a constraint |
| 2NF | Column changes only when part of the composite PK changes | Move it to the table whose PK it depends on |
| 3NF | Column `city` determined by `zip_code`, not by the row's PK | Extract `zip_codes(zip_code, city, state)` |

### Constraints

Declare constraints in the schema; do not rely on application code alone.

| Constraint | Purpose | Example |
|---|---|---|
| `NOT NULL` | No missing value | `email TEXT NOT NULL` |
| `UNIQUE` | Business uniqueness rule | `UNIQUE (email)` |
| `CHECK` | Domain rule | `CHECK (price > 0)` |
| `FOREIGN KEY` | Referential integrity | `REFERENCES users(id) ON DELETE CASCADE` |
| `DEFAULT` | Avoids NULL where a sensible default exists | `created_at TIMESTAMPTZ DEFAULT now()` |

Prefer `ON DELETE RESTRICT` (the default) over `CASCADE` unless cascading deletion is an explicit business rule and all stakeholders understand the effect. Document every `CASCADE`.

### Relationships and join tables

**One-to-many:** Add the foreign key to the "many" side. Index that column.

**Many-to-many:** Use a join table with a composite primary key `(a_id, b_id)`. Add a unique constraint if the pair must be unique. Index both columns individually for lookups from either side.

**One-to-one:** Foreign key on the dependent table (not the base table). Use `UNIQUE` on the foreign key column to enforce the one-to-one cardinality.

**Self-referential:** Parent–child hierarchies (`parent_id REFERENCES categories(id)`). For deep trees, consider the closure-table or nested-set pattern and document the choice.

### Deliberate denormalisation

Denormalise only after measuring that the normalised query is the bottleneck, the join is too costly, and no index change fixes it.

| Pattern | When justified | Invariant to maintain |
|---|---|---|
| Materialised summary column (`order_total` on `orders`) | Aggregate is queried far more than it changes | Update atomically in the same transaction as the detail change; add a `CHECK` or trigger to catch drift |
| Duplicated lookup value (`user_email` on `audit_log`) | Historical snapshot required even if user changes email | Make the column write-once; document that it is a snapshot, not a live reference |
| Flattened join (`product_name` on `order_items`) | Join to `products` is prohibitively expensive at scale | Same snapshot rationale; fill on insert only |

Document every deliberate denormalisation in `docs/DB.md` with: the reason, the invariant and how it is enforced.

## Examples

### Normalised order schema (3NF)

```sql
-- Bad: order_items stores the product name inline with no reference
CREATE TABLE order_items_bad (
    id          BIGINT PRIMARY KEY,
    order_id    BIGINT NOT NULL,
    product_name TEXT NOT NULL,  -- denormalised without justification
    quantity    INT NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

-- Good: reference products table; denormalise only if justified
CREATE TABLE products (
    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  TEXT NOT NULL,
    sku   TEXT NOT NULL UNIQUE
);

CREATE TABLE order_items (
    order_id    BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  BIGINT NOT NULL REFERENCES products(id),
    quantity    INT NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX ON order_items (product_id);  -- lookup from product side
```

### Documented deliberate denormalisation

```sql
-- order_items.product_name_snapshot: historical snapshot at order time.
-- Reason: product name may change after purchase; invoice must reflect original name.
-- Invariant: set once on INSERT, never updated. No live reference to products.name.
ALTER TABLE order_items ADD COLUMN product_name_snapshot TEXT NOT NULL;
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Storing comma-separated IDs in a column | Breaks joins, cannot enforce FK, violates 1NF | Use a join table |
| Using `VARCHAR(255)` everywhere | Arbitrary limit; `TEXT` is equivalent in PostgreSQL and unconstrained | Use `TEXT` with a `CHECK` or `VARCHAR(n)` only where the limit is a business rule |
| `ON DELETE CASCADE` without thinking | Silent mass deletion on a parent row delete | Default to `RESTRICT`; use `CASCADE` only with explicit approval |
| No index on the FK column | Every join scans the child table | Add an index on every FK column |
| Surrogate key on a pure join table | Adds an unused column, loses composite-PK uniqueness guarantee | Use composite PK `(a_id, b_id)` |
| Storing calculated values without maintaining them | Column drifts from reality | Either compute at query time or update atomically in the same transaction |

## Checklist

- [ ] Every table has a primary key.
- [ ] Every column stores one atomic value (1NF).
- [ ] No partial dependency on a composite PK (2NF).
- [ ] No transitive dependency between non-key columns (3NF).
- [ ] Every foreign key column has an index.
- [ ] `NOT NULL` applied to every column that must never be absent.
- [ ] `CHECK` constraints declared for domain rules (positive price, valid status enum).
- [ ] `ON DELETE` behaviour documented for every FK.
- [ ] Deliberate denormalisation documented in `docs/DB.md` with reason and invariant.
- [ ] `docs/DB.md` updated to reflect the final schema.

## Verify with context7 and gh_grep

- **context7:** Check the PostgreSQL version in use before relying on `GENERATED ALWAYS AS IDENTITY`, `gen_random_uuid()` or `INCLUDE` on indexes. Query: `postgresql identity columns`, `postgresql uuid generation`.
- **gh_grep:** Search `ON DELETE CASCADE` to find how cascade rules are applied in the project; search `CHECK (` to audit existing constraint patterns.

## Sources

- PostgreSQL 17 Documentation — DDL: https://www.postgresql.org/docs/17/ddl.html
- PostgreSQL 17 Documentation — Constraints: https://www.postgresql.org/docs/17/ddl-constraints.html
- C.J. Date, *An Introduction to Database Systems* (8th ed.) — normalisation theory (summarised, not reproduced)
