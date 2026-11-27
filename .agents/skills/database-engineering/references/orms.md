# ORMs

Covers Prisma (ORM 6–8) and SQLAlchemy 2.0 patterns, eager loading strategies, session management, raw SQL escape hatches and common ORM pitfalls; checked against official Prisma and SQLAlchemy 2.0 documentation on 2026-11-26. The project's `package.json`, `pyproject.toml`, and lockfile determine the exact API version.

## Contents

- When to use an ORM vs raw SQL
- Prisma patterns and configuration
- SQLAlchemy 2.0 patterns and session lifecycle
- Loading strategies and preventing N+1
- Raw SQL escape hatches
- Common ORM pitfalls

## Guidance

### When to use an ORM vs raw SQL

| Workload | Preferred approach | Rationale |
|---|---|---|
| Standard CRUD, transactional entity updates | ORM (`prisma`, SQLAlchemy ORM) | Type safety, unit-of-work tracking, concise parameterised writes |
| Complex reporting, window functions, recursive CTEs | Raw SQL (`TypedSQL` / `$queryRaw`, SQLAlchemy `text()` or Core) | Avoids fighting query builders and unreadable generated SQL |
| High-volume bulk updates or backfills | Batched Core/SQL statements | Avoids loading thousands of tracked ORM objects into memory |

Always inspect the SQL an ORM emits during development and load testing. Enable query logging in dev (`log: ['query']` in Prisma, `echo=True` or SQL logging in SQLAlchemy) and verify hot paths with `EXPLAIN (ANALYZE, BUFFERS)`.

### Prisma patterns and configuration

Check `package.json` and `prisma/schema.prisma` (or `prisma.config.ts` in Prisma 7+) before writing Prisma code:

- **Configuration shift (Prisma 7+):** CLI paths, seed scripts, `typedSql` paths, and `datasource.url` live in `prisma.config.ts` via `defineConfig({ ... })` rather than `env("DATABASE_URL")` inside `schema.prisma`; the generator provider is `prisma-client`. Prisma 5/6 use `prisma-client-js` and `url = env("DATABASE_URL")` in `schema.prisma`.
- **Client singleton:** Instantiate `PrismaClient` once per process and reuse it across requests; creating a new client per handler leaks connection pools. In hot-reloading dev servers, cache the instance on `globalThis`.
- **Select only needed fields:** Default `findMany` fetches every column. Use `select: { id: true, email: true }` on wide tables to cut network I/O and enable index-only scans.
- **Migrations:** Run `prisma migrate dev` locally and `prisma migrate deploy` in CI/CD; never run `migrate dev` or `db push` against production. Use `prisma migrate dev --create-only` when you need to add `CREATE INDEX CONCURRENTLY` or batched data backfills manually to `migration.sql`.

### SQLAlchemy 2.0 patterns and session lifecycle

Use SQLAlchemy 2.0 declarative typing (`DeclarativeBase`, `Mapped`, `mapped_column`) and explicit `select()` statements; avoid legacy 1.x `declarative_base()`, `Column()`, and `session.query()`.

- **Session factories:** Create one `Engine` (or `AsyncEngine`) per process and bind a `sessionmaker(..., expire_on_commit=False)` or `async_sessionmaker(..., expire_on_commit=False)`.
- **One session per unit of work:** Open a session per request or background job via context manager (`with SessionLocal() as session:` / `async with AsyncSessionLocal() as session:`). Never share one `Session` across concurrent threads or asyncio tasks.
- **Explicit transaction boundaries:** Wrap writes in `with session.begin():` (or `async with session.begin():`) so commit and rollback happen deterministically on exit. Keep outbound network calls outside the transaction block so connections are not held idle.
- **Async requirement:** In `asyncio` applications (`asyncpg`, `psycopg` async), implicit lazy loading triggers synchronous I/O and fails with `MissingGreenlet`. Always forbid implicit lazy loading and specify eager loading explicitly.

### Loading strategies and preventing N+1

**SQLAlchemy 2.0:** Set `lazy="raise"` (or `lazy="raise_on_sql"`) on `relationship()` definitions so accidental lazy loads fail immediately with `InvalidRequestError` in tests instead of silently emitting N+1 queries.

| Scenario | SQLAlchemy 2.0 | Prisma |
|---|---|---|
| Load child collections (`1:N`, `M:N`) | `.options(selectinload(User.orders))` — secondary `SELECT ... IN (...)`; no duplicate parent rows | `include: { orders: true }` with `relationLoadStrategy: "query"` (or `"join"` via PostgreSQL `LATERAL JOIN`) |
| Load single parent (`N:1`, `1:1`) | `.options(joinedload(Order.user))` — single `LEFT OUTER JOIN` | `include: { user: true }` with `relationLoadStrategy: "join"` (`relationJoins` preview feature) |
| Forbid any unrequested lazy load per query | `.options(raiseload("*"))` | Omit `include`; Prisma does not lazy-load properties implicitly |
| Fetch subset of scalar columns | `.options(load_only(User.id, User.email))` or `select(User.id, User.email)` | `select: { id: true, email: true }` |

**Critical SQLAlchemy rule:** When using `joinedload()` on a one-to-many collection, PostgreSQL returns duplicated parent rows; you MUST call `result.unique().scalars().all()` or SQLAlchemy raises an error. Prefer `selectinload()` for collections.

**Prisma `relationLoadStrategy`:** When `relationJoins` is enabled in `schema.prisma`, `"join"` (default when enabled) fetches nested relations in a single query using database `LATERAL` joins; switch a specific query to `relationLoadStrategy: "query"` if a large lateral join inflates row width or degrades the query plan.

### Raw SQL escape hatches

Never pass interpolated strings into raw SQL functions (`$queryRawUnsafe`, `text(f"...")`).

| ORM | Safe raw query mechanism | Notes |
|---|---|---|
| Prisma | `` prisma.$queryRaw`... ${val}` `` / `` prisma.$executeRaw`... ${val}` `` | Tagged template literals bind parameters automatically |
| Prisma (`typedSql`) | `.sql` files in `prisma/sql/` compiled with `prisma generate --sql` and called via `$queryRawTyped` | Checked against database schema at generate time; full TypeScript return types |
| SQLAlchemy | `text("... WHERE id = :id")` with parameter dict in `session.execute(stmt, {"id": val})` | Use `bindparam("ids", expanding=True)` for `IN :ids` lists |
| SQLAlchemy -> ORM objects | `select(User).from_statement(text("SELECT id, name FROM users WHERE ..."))` | Maps raw SQL output back into tracked ORM model instances |

### Common ORM pitfalls

- **Hidden loops (`N+1`):** Fetching a list, then awaiting `prisma.<model>.findUnique(...)` or accessing an unloaded SQLAlchemy attribute inside a loop. Note: Prisma's dataloader batches `findUnique` calls made in the same event-loop tick on the same filter shape, whereas `findFirst` and `findMany` do not batch.
- **Offset pagination at depth:** `skip: 10000` or `.offset(10000)` forces PostgreSQL to scan and discard 10,000 rows. Use cursor/keyset pagination (`cursor: { id: lastId }, take: 50` in Prisma; `WHERE (created_at, id) < (:ts, :id)` in SQLAlchemy).
- **Bulk updates row-by-row:** Iterating over ORM objects to mutate and flush one by one issues N `UPDATE` statements. Use `prisma.order.updateMany(...)` or SQLAlchemy `update(Order).where(...).values(...)`.
- **Autogenerate blind spots:** Alembic (`alembic revision --autogenerate`) misses custom partial indexes, check constraints with raw expressions, or triggers unless declared explicitly; always read and edit generated migration files before applying.

## Examples

### SQLAlchemy 2.0: `lazy="raise"` with `selectinload` and `text()`

```python
from sqlalchemy import ForeignKey, String, bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Fail loudly if code forgets to eager-load orders
    orders: Mapped[list["Order"]] = relationship(back_populates="user", lazy="raise")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship(back_populates="orders", lazy="raise")

# Bad: lazy="select" default causes MissingGreenlet in async or N+1 in sync
# Good: explicit eager load
async def get_users_with_orders(session: AsyncSession, ids: list[int]) -> list[User]:
    stmt = (
        select(User)
        .options(selectinload(User.orders))
        .where(User.id.in_(ids))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

# Good: safe parameterised raw SQL with expanding IN list
async def count_orders_by_status(session: AsyncSession, statuses: list[str]):
    stmt = text(
        "SELECT status, COUNT(*) AS total FROM orders WHERE status IN :statuses GROUP BY status"
    ).bindparams(bindparam("statuses", expanding=True))
    return (await session.execute(stmt, {"statuses": statuses})).mappings().all()
```

### Prisma: selective loading and safe raw SQL

```typescript
// Bad: string interpolation in $queryRawUnsafe — SQL injection risk
const bad = await prisma.$queryRawUnsafe(
  `SELECT * FROM "Order" WHERE status = '${userStatus}'`
);

// Good: narrow select + explicit relationLoadStrategy
const recentOrders = await prisma.order.findMany({
  where: { customerId, status: "paid" },
  select: {
    id: true,
    totalCents: true,
    createdAt: true,
    items: {
      select: { productId: true, quantity: true },
    },
  },
  orderBy: { createdAt: "desc" },
  take: 50,
});

// Good: tagged template literal (automatically parameterised)
const totals = await prisma.$queryRaw<Array<{ status: string; count: bigint }>>`
  SELECT status, COUNT(*)::bigint AS count
  FROM "Order"
  WHERE "customerId" = ${customerId}
  GROUP BY status
`;
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Leaving SQLAlchemy `relationship()` at default `lazy="select"` | Silent N+1 queries in sync code; `MissingGreenlet` crash in async | Set `lazy="raise"` and pass `selectinload()` / `joinedload()` per query |
| Creating `new PrismaClient()` inside request handlers | Exhausts PostgreSQL `max_connections` under load | Export a single shared `PrismaClient` instance per process |
| Using `joinedload()` on a collection without `.unique()` | Raises `InvalidRequestError` or duplicates parent rows | Use `selectinload()` for collections, or call `.unique()` |
| Using `$queryRawUnsafe` or Python f-strings in `text()` | Critical SQL injection vulnerability | Use `` prisma.$queryRaw`...` ``, `TypedSQL`, or `text()` with `:param` bindings |
| Loading full ORM models when returning summary lists | Wastes bandwidth and prevents covering index-only scans | Use Prisma `select` or SQLAlchemy `load_only()` / column `select()` |
| Using `OFFSET` / `skip` on deep pages | Scans and discards all skipped rows linearly | Use keyset/cursor pagination |

## Checklist

- [ ] `package.json` / `pyproject.toml` checked for exact Prisma or SQLAlchemy version before coding.
- [ ] Single shared `PrismaClient` / `Engine` + `sessionmaker` per process (no per-request client creation).
- [ ] SQLAlchemy relationships use `lazy="raise"` (or explicit loader options on every query).
- [ ] Collections loaded via `selectinload()` (SQLAlchemy) or explicit `include`/`select` (Prisma); no N+1 loops.
- [ ] Hot-path queries project only needed columns (`select`, `load_only()`).
- [ ] All raw SQL uses tagged templates (`$queryRaw`), `TypedSQL`, or `text()` with bound parameters; zero `$queryRawUnsafe` string interpolation.
- [ ] Pagination on large tables uses cursor/keyset predicates rather than large `OFFSET`.
- [ ] Autogenerated migrations (Alembic / Prisma) reviewed line by line for lock safety and custom constraints.

## Verify with context7 and gh_grep

- **context7:** Query the exact locked major version in the repo (`prisma` 6/7/8, `sqlalchemy` 2.0.x): `prisma config defineConfig typedSql`, `prisma relationLoadStrategy join query`, `sqlalchemy 2.0 async_sessionmaker selectinload`, `sqlalchemy text bindparam expanding`.
- **gh_grep:** Search `$queryRawUnsafe` and `text(f"` to catch SQL injection risks; search `relationship(` to verify `lazy="raise"` conventions; search `new PrismaClient` to verify singleton instantiation.

## Sources

- Prisma Documentation: https://www.prisma.io/docs
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/en/20/
- Alembic Documentation: https://alembic.sqlalchemy.org/
