# Integration Testing

Testing across a boundary with real dependencies: containers, databases, HTTP contracts, isolation and cleanup, for Vitest 5.1, Jest 30.5, pytest 9.2 and Testcontainers for Node (checked 2026-11-26). Test doubles and fixture design belong to `test-driven-development`.

## Contents

- What integration tests are for
- Real dependencies
- Containers
- Databases
- Contracts
- Isolation and cleanup
- Environment safety
- Speed and organisation
- Routing to other skills

## Guidance

### What integration tests are for

An integration test exercises your code together with a real collaborator across a boundary, where a fake would hide the defect: SQL and transactions, migrations, serialisation, HTTP framing, message queues, file formats, configuration wiring.

Use one when:

- The risk is in the interaction itself (a query returns the wrong rows, a constraint is missing, a transaction does not roll back).
- A unit test would need a fake so detailed that it re-implements the dependency.
- A criterion names an observable effect at a boundary (a row is stored, a response has status 403 and an error code, a message is published).

Do not use one for pure logic; that belongs at unit level (see `test-pyramid.md`).

### Real dependencies

Prefer the real thing, in this order of preference:

1. **The real engine, in a disposable instance** (a container or an embedded instance of the same engine the project runs in production). Same SQL dialect, same constraints, same transaction behaviour.
2. **A different engine** (for example an in-memory SQLite standing in for PostgreSQL): acceptable only for logic that is dialect-neutral. It will not catch dialect-specific SQL, locking or type behaviour; say so in the report when you rely on it.
3. **A provider's sandbox** for a third-party service, with test credentials from the environment. Use only when the criterion requires the real provider; never use live accounts.
4. **A stand-in server you control** (a small local HTTP server returning recorded or specified responses) for third parties that have no sandbox. Never call a live third party from a test suite. For building such stand-ins, load `test-driven-development`.

When the dependency is not available, do not fake it silently and report `pass`. Mark the criterion `not tested` with the reason, or escalate (see "Escalate when" in the tester definition).

### Containers

Use containers to get a real, disposable, version-pinned dependency per test run.

- Pin the image to an exact tag that matches the production version (for example `postgres:16-alpine`); never `latest`. The project's deployment config names the production version.
- Wait for readiness through the library's wait strategy, not a sleep. The Testcontainers modules provide this for common databases.
- Let the library choose a random host port and read it back; never hard-code `5432`. This lets parallel runs and local services coexist.
- Start the container once per test file or once per run (global setup), not once per test; start-up is the cost. Isolate tests inside it (below).
- Stop the container when finished. Testcontainers for Node supports `await using` for scope-bound lifetime on runtimes that support it, otherwise call `stop()` in teardown.
- Containers need a running container runtime. If none is present, escalate; do not fall back to a shared database.
- Adding a container library or a new image is a dependency change that needs user approval.
- Container, image and volume commands that delete (`docker rm`, `docker volume rm`, `docker system prune`) are destructive: ask the user first, and never run them against resources you did not create.

### Databases

#### Schema and data

- Create the schema by running the project's real migrations against the disposable database. A hand-written test schema drifts from production. For migration design, load `database-engineering`.
- Insert the data each test needs inside that test (or its fixture). Use unique values (a counter or random suffix) when a unique constraint exists.
- Assert on the database state directly (query the table) as well as on the return value when persistence is the criterion.

#### Isolation strategies

| Strategy | How | Strength | Weakness |
|---|---|---|---|
| Transaction rollback | Open a transaction per test, roll back at the end | Fastest; no cleanup code | Cannot test code that commits or opens its own connection; hides commit-time constraint failures |
| Truncate or delete between tests | Clear the touched tables in teardown | Works with code that commits | Slower; must know every table touched; ordering of foreign keys |
| Database per test file or per worker | Create a fresh database or schema from a template | Strong isolation, parallel-safe | Slower start-up; more resources |
| Fresh container per file | New container each time | Strongest isolation | Slowest; use sparingly |

Choose the cheapest strategy that is correct for the code under test. If the code commits, rollback isolation does not apply. With parallel workers, give each worker its own database or schema; never let two workers share mutable tables.

#### Constraints and transactions

Test what only a real database can show: unique and check constraints reject bad rows, foreign keys protect integrity, a failed step rolls back the whole transaction, concurrent updates do not corrupt state (where the criterion covers it).

### Contracts

A contract test asserts that a boundary behaves as its documented contract says, so that producer and consumer can change independently.

- Take the expected status codes, response shape, error codes and auth behaviour from `docs/API-CONTRACTS.md` (or the OpenAPI document the project keeps), not from what the code currently returns.
- Assert the parts a consumer depends on: status, required fields and types, error envelope, headers named in the contract. Do not assert on fields the contract leaves open.
- Cover the contract's error paths: invalid body, missing credentials, insufficient scope, not found, upstream failure mapping.
- Run the request through the real HTTP layer of the application (start the app on a random port, or use the framework's in-process request test helper) so routing, middleware and serialisation are included.
- If code and contract disagree, report it and ask which is right; never change either silently (see Source of truth in `AGENTS.md`).
- For consumer-driven contract tooling and API design rules, load `api-engineering`.

### Isolation and cleanup

- Each test builds the data it needs and does not depend on rows left by another test.
- Clean up in teardown that runs even when the test fails (`afterEach` or `afterAll` in Vitest and Jest, fixtures with `yield` in pytest, `finally`).
- Clean up what you created, by identifier. Never run a blanket "delete everything" against a database you did not create.
- Reset external state you changed: environment variables, temporary files (use the runner's temporary directory), queues, caches, background servers, ports.
- Order independence: run the file with its tests in a different order (`--sequence.shuffle` in Vitest, `--randomize` in Jest 30; for pytest use the project's ordering plugin if it has one) and confirm it still passes.
- Leaked handles show up as a runner that hangs after the tests finish. Jest offers `--detectOpenHandles` to find them; use it rather than `--forceExit`, which hides the leak.

### Environment safety

An integration test can destroy data. Guard against pointing it at a real database.

- Read connection settings from environment variables (names listed in `.env.example`), never hard-code credentials, never print them.
- Refuse to run unless the target is clearly local or disposable: check the host is localhost or a container address, or that the database name carries a test marker. Fail loudly with a message that names the guard.
- Never run migrations, truncation or drops against shared, staging or production databases from a test. Running migrations is an approval-gated action in `AGENTS.md`; a disposable test database you created is not a shared database, but say which one you used.
- Use test credentials with the least privilege the test needs.

### Speed and organisation

- Keep integration tests in a separate directory, file suffix (`*.integration.test.ts`) or marker (`@pytest.mark.integration`) so they can be run on their own and excluded from the fast loop. Register markers in the pytest config and use `--strict-markers` so a typo fails.
- Run them in the default command only if they stay quick; otherwise document a dedicated command in the README and `AGENTS.md` Commands line (changes to `AGENTS.md` go to the user first).
- Share expensive set-up (container start, migrations) across a file or the run; keep per-test set-up small.
- Report the time of the slowest tests (`--durations=10` in pytest) when a suite is slow.

### Routing to other skills

For doubles, factories and fixtures, load `test-driven-development`. For schema and migration design, load `database-engineering`. For API design and contract tooling, load `api-engineering`. For CI service containers, load `devops-deployment`.

## Examples

### pytest: real SQL engine, constraint behaviour, per-test isolation (executed)

```python
# tests/test_orders_db.py  (pytest 9.2; stdlib sqlite3 stands in for the real engine)
import sqlite3
import pytest


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")  # fresh database per test: nothing to clean up
    c.execute(
        "CREATE TABLE orders ("
        "id INTEGER PRIMARY KEY, sku TEXT NOT NULL UNIQUE, "
        "qty INTEGER NOT NULL CHECK (qty > 0))"
    )
    c.commit()
    yield c
    c.close()


@pytest.mark.integration
def test_duplicate_sku_is_rejected_by_the_database(conn):
    conn.execute("INSERT INTO orders (sku, qty) VALUES ('A-1', 2)")
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        conn.execute("INSERT INTO orders (sku, qty) VALUES ('A-1', 1)")


@pytest.mark.integration
def test_zero_quantity_is_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        conn.execute("INSERT INTO orders (sku, qty) VALUES ('B-2', 0)")
```

Select with `python -m pytest -m integration`, and exclude with `-m "not integration"`. Register the marker:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = ["integration: needs a real dependency"]
addopts = ["--strict-markers"]
```

### Vitest with a PostgreSQL container (unverified: not executed here, no container runtime was available)

```ts
// tests/orders.integration.test.ts  (Vitest 5.x, @testcontainers/postgresql, pg)
import { afterAll, beforeAll, beforeEach, expect, it } from 'vitest';
import { PostgreSqlContainer, type StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { Client } from 'pg';

let container: StartedPostgreSqlContainer;
let db: Client;

beforeAll(async () => {
  container = await new PostgreSqlContainer('postgres:16-alpine').start(); // pin the production major version
  db = new Client({ connectionString: container.getConnectionUri() });
  await db.connect();
  // Apply the project's real migrations here, using the project's migration command.
}, 120_000);

afterAll(async () => {
  await db?.end();
  await container?.stop();
});

beforeEach(async () => {
  await db.query('TRUNCATE orders RESTART IDENTITY'); // disposable database created above
});

it('rejects a duplicate SKU with a unique violation', async () => {
  await db.query("INSERT INTO orders (sku, qty) VALUES ('A-1', 2)");
  await expect(db.query("INSERT INTO orders (sku, qty) VALUES ('A-1', 1)"))
    .rejects.toMatchObject({ code: '23505' });
});
```

The `TRUNCATE` here is safe only because the database was created by this test file; it is destructive on any other database, which is why the environment guard above matters.

### Filled-in contract assertion (framework-neutral)

```text
Contract: POST /api/payments  (docs/API-CONTRACTS.md, section "Payments")
Case                         Request                         Expected
valid                        amount 1000, valid card         201, body.id present
invalid amount               amount 0                        400, body.error == "INVALID_AMOUNT"
missing scope                token without payments:write    403, no payment row created
gateway timeout              stand-in gateway times out      502, body.error == "GATEWAY_ERROR"
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Replacing the database with a hand-rolled fake | Misses constraint, SQL and transaction defects | Use the real engine in a disposable instance |
| Hard-coded port, host or shared database | Collides with parallel runs; risks real data | Random port from the library, per-run disposable database, environment guard |
| Hand-written test schema | Drifts from production | Run the project's real migrations |
| Cleanup only on success | Failures leave state that breaks later tests | Teardown in `afterEach`/fixture `yield`/`finally` |
| Rollback isolation for code that commits | The test does not see commit behaviour | Use truncate or per-worker databases |
| `latest` image tag | The test environment changes under you | Pin the production version |
| Contract taken from current code output | Proves the code does what it does | Take expectations from `docs/API-CONTRACTS.md` |
| Calling a live third party | Flaky, costly, unsafe | Provider sandbox or a local stand-in; mark `not tested` if neither exists |
| `--forceExit` to stop a hanging run | Hides leaked handles | Find the leak (`--detectOpenHandles`) and close it |

## Checklist

- [ ] The dependency under test is real or the substitution is stated in the report.
- [ ] Container images are pinned to the production version and use random ports.
- [ ] Readiness is awaited through a wait strategy, not a sleep.
- [ ] The schema comes from the project's real migrations.
- [ ] Each test builds its own data, and cleanup runs even when the test fails.
- [ ] The tests refuse to run against a non-local or non-disposable target.
- [ ] Contract expectations trace to `docs/API-CONTRACTS.md` or the OpenAPI document, including error paths.
- [ ] No test contacts a live third party, production or real accounts.
- [ ] Tests pass in shuffled order and in parallel with the rest of the suite.
- [ ] Any new container library or image had user approval.

## Verify with context7 and gh_grep

- **context7:** confirm for the project's versions: "Testcontainers for Node `PostgreSqlContainer` start, `getConnectionUri` and stop", "Vitest `globalSetup` and `beforeAll` timeouts", "Vitest `sequence.shuffle`", "Jest 30 `--detectOpenHandles` and `--randomize`", "pytest markers, `--strict-markers` and fixtures with `yield`".
- **gh_grep:** search literal code: `new PostgreSqlContainer(`, `getConnectionUri()`, `@pytest.mark.integration`, `markers = [`, `TRUNCATE`  with `RESTART IDENTITY` in test files, `--detectOpenHandles`.

## Sources

- [Testcontainers for Node.js: PostgreSQL module](https://node.testcontainers.org/modules/postgresql/), read 2026-11-26.
- [pytest: Good Integration Practices](https://docs.pytest.org/goodpractices.html), read 2026-11-26.
- [Jest: Configuration](https://jestjs.io/docs/configuration), read 2026-11-26.
- [Playwright: Best Practices](https://playwright.dev/docs/best-practices) (stub third-party calls, control test data), read 2026-11-26.
- The pytest example was executed with pytest 9.2.0 on 2026-11-26; the Testcontainers example was not executed.
