---
name: database-engineering
description: "Use when designing, querying, indexing or migrating data: relational design, SQL, PostgreSQL, MongoDB, ORMs, transactions and query optimisation."
---

# Database Engineering

Covers the full data lifecycle: schema design, querying, indexing, transactions, migrations and ORM usage for relational and document databases.

## When to use

- Designing or reviewing a data model, schema or collection structure.
- Writing or reviewing SQL queries, CTEs, window functions or parameterised statements.
- Choosing or tuning indexes for a table or collection.
- Configuring transactions, isolation levels or retry logic.
- Writing or reviewing a database migration, including zero-downtime changes.
- Debugging slow queries, lock contention or replication lag.
- Choosing between embedding and referencing in MongoDB.
- Using Prisma or SQLAlchemy and hitting an ORM limitation.

## Do not use for

- Application-level caching (Redis, in-process): load `backend-engineering`.
- Database access control audit and privilege escalation risk: load `security-engineering`.
- Schema design as part of system architecture decisions: load `system-architecture`.

## Research: context7 and gh_grep

- You MUST consult **context7** before writing or reviewing any use of PostgreSQL, MongoDB, Prisma or SQLAlchemy. Check the project's manifest or lockfile (`package.json`, `pyproject.toml`, `requirements.txt`) first and query that version. Useful queries:
  - `postgresql EXPLAIN ANALYZE plan types`
  - `prisma migrate deploy zero-downtime`
  - `sqlalchemy 2.0 selectinload joinedload`
  - `mongodb aggregation pipeline $lookup $group`
  - `postgresql isolation level serializable repeatable read`
- You MUST search **gh_grep** when a migration pattern, ORM loading strategy or query rewrite is unfamiliar or when documentation is ambiguous. Search literal code. Useful searches:
  - `CREATE INDEX CONCURRENTLY`
  - `prisma.$queryRaw`
  - `session.execute(select(`
  - `readConcern majority`
  - `EXPLAIN (ANALYZE, BUFFERS)`
- Pure project-internal business logic with no library calls needs neither tool.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/relational-design.md](references/relational-design.md) | Designing or reviewing entities, keys, normalisation or constraints. |
| [references/sql.md](references/sql.md) | Writing or reviewing joins, aggregation, CTEs, window functions or NULL handling. |
| [references/postgresql.md](references/postgresql.md) | Using PostgreSQL-specific types, extensions, locking, vacuum or operational checks. |
| [references/mongodb.md](references/mongodb.md) | Designing documents, aggregation pipelines or configuring consistency in MongoDB. |
| [references/orms.md](references/orms.md) | Using Prisma or SQLAlchemy: loading strategies, migrations, raw SQL escape hatches. |
| [references/indexing.md](references/indexing.md) | Choosing index types, composite order, partial or covering indexes. |
| [references/query-optimization.md](references/query-optimization.md) | Reading EXPLAIN output, rewriting slow queries or measuring improvement. |
| [references/transactions.md](references/transactions.md) | Isolation levels, anomalies, locking, retries or idempotency. |
| [references/migrations.md](references/migrations.md) | Zero-downtime schema changes, backfills, rollback or expand-and-contract. |

## Workflow

1. **Identify the database engine and ORM.** Check `docs/DB.md` for the agreed data model and stack. If `docs/DB.md` is missing or stale, raise it as a follow-up; do not invent schema decisions.
2. **Consult context7.** Check the project lockfile for the exact version of PostgreSQL driver, MongoDB driver, Prisma or SQLAlchemy. Query context7 for that version before writing any query, migration or ORM call.
3. **Open the matching references.** Use the routing table above. Load at most two reference files in addition to this skill.
4. **Architect role:** Design the schema following `references/relational-design.md` or `references/mongodb.md`. Record decisions in `docs/DB.md` and, for significant trade-offs, in `docs/adr/`. Get user approval before any destructive change.
5. **Implementer role:** Write queries, migrations and ORM code. Use parameterised queries always; never interpolate user input. For migrations, follow the expand-and-contract pattern from `references/migrations.md`. Run the test suite against a realistic dataset before marking done.
6. **Reviewer role:** Check every Standard item below. Confirm no raw string interpolation in queries, no missing indexes on foreign keys, no migration that locks under load. File findings at the correct severity per `AGENTS.md`.
7. **Debugger role:** Collect the slow query log entry or error verbatim. Run `EXPLAIN (ANALYZE, BUFFERS)` or the equivalent and read the output per `references/query-optimization.md`. Search gh_grep with the error message before proposing a fix.
8. **Verify.** Run every check in the Verification section below.
9. **Sync docs.** Update `docs/DB.md` (architect) for any schema change. Update `CHANGELOG.md` (implementer) for any migration shipped.

## Standards

- Never interpolate user-supplied values into SQL or MongoDB queries; always use parameterised statements or tagged template literals.
- Every foreign key column must have an index unless the table is tiny and the query plan confirms it is not needed.
- Every migration must be reversible or the rollback plan must be documented and approved before applying.
- Use `CREATE INDEX CONCURRENTLY` (PostgreSQL) for indexes on live tables to avoid table locks; note it cannot run inside a transaction block.
- Never run a migration that acquires an `ACCESS EXCLUSIVE` lock on a large table in a single step during business hours without an explicit maintenance window approval.
- Isolation level must match the anomaly risk: use `READ COMMITTED` for simple CRUD; use `REPEATABLE READ` or `SERIALIZABLE` only when the invariant requires it, and document why.
- Every transaction that can conflict must have a retry loop with exponential back-off; retried operations must be idempotent.
- ORM lazy loading is off by default or explicitly controlled; never accept the N+1 default in a hot path.
- Raw SQL escape hatches (`$queryRaw`, `text()`) must use bound parameters; never string-format a query.
- Schema changes to `docs/DB.md` must be proposed by the architect and approved before implementation.
- Backfills on large tables must run in batches; never `UPDATE` millions of rows in one transaction.
- Test migrations against a realistic data volume before shipping; a migration that passes on empty fixtures and fails on 10 M rows is a defect.
- Document deliberate denormalisation with the reason and the invariant that keeps it consistent.
- MongoDB write operations on data that must survive a primary failover must use `writeConcern: { w: "majority", j: true }`.

## Verification

- [ ] `context7` queried for every library at the locked version; unverified claims are labelled.
- [ ] `gh_grep` searched for any unfamiliar migration pattern or ORM call.
- [ ] No user input interpolated into any query string.
- [ ] Every foreign key column has an index (or the absence is justified by EXPLAIN evidence).
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` run on every new or changed query in the hot path; plan is documented.
- [ ] All new indexes created with `CONCURRENTLY` on live PostgreSQL tables.
- [ ] Migration is reversible, or rollback plan is documented and approved.
- [ ] Backfills run in batches; no single-transaction full-table UPDATE.
- [ ] ORM loading strategy chosen explicitly; no implicit lazy load in a hot path.
- [ ] `docs/DB.md` updated to reflect any schema change.
- [ ] `CHANGELOG.md` updated for any shipped migration.
- [ ] Test suite (including migration tests on realistic volume) passes.

## Output

Return the standard report from `AGENTS.md`. Key additions for this skill:

- **Evidence:** `EXPLAIN (ANALYZE, BUFFERS)` output or the query plan label, migration dry-run result, test command and pass/fail count.
- **Research:** every context7 library and version queried; every gh_grep pattern searched and what it confirmed.
- **Docs impact:** `docs/DB.md` (architect) on any schema or model change; `docs/adr/` (architect) on significant design trade-offs; `CHANGELOG.md` and `README.md` (implementer) on shipped migrations or new setup commands; `docs/MEMORY.md` (coordinator) on durable constraints or pitfalls discovered.
