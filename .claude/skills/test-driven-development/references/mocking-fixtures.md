# Test Doubles, Fixtures, Clocks and Randomness

How to decide what to replace in a test, which kind of double to use, how to keep doubles honest, how to build fixtures and factories, and how to control time and randomness. Framework specifics cover Jest 29.x, Vitest 3.x and current docs, pytest 8.x and Python 3 `unittest.mock`, checked 2026-11-26. The project's manifest and conventions win; reset and restore semantics differ between major versions, so confirm with context7.

## Contents

- Taxonomy of doubles
- Decide: real or double
- What not to mock
- Prefer fakes and stubs; use mocks for interactions that are the behaviour
- Keep doubles honest
- Framework mechanics
- Fixtures and factories
- Isolation and cleanup
- Clocks, timers and dates
- Randomness and generated identifiers
- Network, filesystem and environment

## Guidance

### Taxonomy of doubles

A test double replaces a real collaborator during a test. Naming the kind helps you choose the least intrusive one.

| Kind | What it does | Verifies calls? | Typical use |
|---|---|---|---|
| Dummy | Fills a required argument, never used | No | Satisfy a signature |
| Stub | Returns canned answers | No | Control input from a dependency (a rate, a user record) |
| Spy | Real or stub behaviour, and records calls | Yes, after the fact | Check that an outgoing message happened |
| Mock | Pre-programmed with expected calls, fails if they differ | Yes, as the assertion | The interaction itself is the behaviour |
| Fake | A working, simplified implementation | Usually no | In-memory repository, fake mailer outbox, fake clock |

Frameworks blur these names: a Jest `jest.fn()`, a Vitest `vi.fn()` and a Python `Mock` can act as a stub, a spy or a mock depending on how you use them. Decide the role first, then use the tool.

### Decide: real or double

Use the **real** collaborator by default. Replace it only when at least one of these is true:

- It is **slow** (network, large computation, process start).
- It is **non-deterministic** (clock, randomness, concurrency, ordering).
- It has **side effects you must not cause** (sending email, charging a card, writing outside a temp area).
- It is **unavailable** in the test environment (third-party service).
- Its **failure mode is hard to trigger** (timeout, partial response) and you must test your error handling.

Decision order:

1. Can the real thing run in the test quickly and safely? Use it.
2. If not, can a **fake** (working in-memory version) do the job? Use it.
3. If you only need controlled input, use a **stub**.
4. If the outgoing call is the specified behaviour, use a **spy** or **mock** and assert it.

Where the real thing needs a container or a database, the choice of level and setup belongs to `testing-strategy`; this file covers the doubles that you build in-process.

### What not to mock

- **The unit under test.** If you replace part of it, you are testing the mock.
- **Pure functions and value objects.** They are fast and deterministic; call them.
- **Private methods and internal helpers.** Test through the public behaviour; mocking internals couples the test to the structure and breaks on harmless refactors.
- **Types you do not own, at their full surface.** Mocking a large third-party client means guessing its behaviour. Wrap the library in a small adapter you own, then double your adapter and test the adapter separately against the real library at a higher level.
- **The thing whose behaviour is the criterion.** A test that mocks the database cannot prove the query is correct; for query correctness use a real database in an integration test (`database-engineering` for the design, `testing-strategy` for the level).
- **Everything, to make a test fast.** A suite of heavily mocked tests passes while the real wiring is broken.

Test of a double: if the production code changed shape but behaviour stayed identical, would this test still pass? If not, it is coupled to structure.

### Prefer fakes and stubs; use mocks for interactions that are the behaviour

- Assert on **outcomes** when you can: the order is saved, the response has status 201, the outbox contains one email. A fake repository or fake mailer lets you assert state, which survives refactoring.
- Assert on **calls** only when the call is the requirement ("a notification is sent to the owner"). Even then, assert the arguments that matter, not the call count of every internal method.
- Avoid asserting the order of calls or "called exactly N times" unless the specification says so.
- A stub that returns canned data should look like real data: correct types, realistic edge values, and the error shapes the real dependency produces.

### Keep doubles honest

A double that drifts from the real thing makes tests pass against a fiction.

- **Bind to the real signature.** In Python use `create_autospec(...)`, `patch(..., autospec=True)` or `spec_set`; calls with the wrong arguments or missing attributes then fail like the real code would. In TypeScript, type the double against the real interface so the compiler catches drift. In Jest or Vitest, prefer `spyOn` on a real object (calls pass through unless you override) over a free-standing `fn()` with no tie to the original.
- **Share a contract.** Run the same small set of behavioural checks against both the fake and the real implementation (at a level where the real one can run). When the real one changes, the contract test fails and the fake is updated.
- **Return realistic failures.** If the real client throws a timeout error type, the double throws that type, not a generic error.
- **Keep fakes small.** A fake that grows complex enough to need its own tests is a signal to use the real dependency at a higher level.

### Framework mechanics

Use the project's framework. Confirm every API below with context7 for the installed version before relying on it.

#### Jest (29.x)

| Need | API | Note |
|---|---|---|
| Stub or spy function | `jest.fn()`, `.mockReturnValue(x)`, `.mockResolvedValue(x)`, `.mockRejectedValue(err)` | `jest.fn(impl)` is shorthand for `mockImplementation` |
| Spy on an existing method | `jest.spyOn(object, "method")` | Calls through by default; override with `mockImplementation` |
| Replace a module | `jest.mock("./path", factory)` | Calls are hoisted above imports by babel-jest; the factory may only use out-of-scope variables whose names start with `mock` |
| Partial module mock | `jest.requireActual("./path")` inside the factory, spread, override one export | Keeps the other exports real |
| Auto-mock a module | `jest.createMockFromModule("./path")` | Then set the behaviours you need |
| Clear or restore | `jest.clearAllMocks()`, `jest.resetAllMocks()`, `jest.restoreAllMocks()` | Restoring only affects mocks made with `spyOn` |
| Automatic cleanup | config options `clearMocks`, `resetMocks`, `restoreMocks` | Prefer one automatic option over remembering hooks |
| Fake time | `jest.useFakeTimers()`, `jest.setSystemTime(date)`, `jest.advanceTimersByTime(ms)`, `jest.useRealTimers()` | Async variants such as `advanceTimersByTimeAsync` exist for promise-based code |

Manually assigning `jest.fn()` over a property is not undone by `restoreAllMocks`; restore it yourself or use `spyOn`.

#### Vitest (3.x)

| Need | API | Note |
|---|---|---|
| Stub or spy function | `vi.fn()`, `vi.spyOn(object, "method")` | Share the same chaining methods as Jest mocks |
| Replace a module | `vi.mock("./path", factory)` | Hoisted to the top of the file |
| Variables in the factory | `const mocks = vi.hoisted(() => ({ fn: vi.fn() }))` | Needed because the factory runs before normal top-level code |
| Partial module mock | `vi.mock("./path", async (importOriginal) => ({ ...(await importOriginal()), one: vi.fn() }))` | Keeps real exports |
| Spy on a module export | `vi.spyOn(moduleNamespace, "name")` | Affects callers outside the original module; calls inside it are not redirected |
| Globals | `vi.stubGlobal(name, value)` | Not reset automatically unless the `unstubGlobals` option is on or you call `vi.unstubAllGlobals()` |
| Fake time | `vi.useFakeTimers()`, `vi.setSystemTime(date)`, `vi.useRealTimers()` | `setSystemTime` is not reset between tests; reset in `afterEach` |
| Cleanup | `vi.clearAllMocks()`, `vi.resetAllMocks()`, `vi.restoreAllMocks()`, config options for each | Behaviour of reset and restore changed across major versions: (unverified for your version) check context7 |

Vitest warns to clear or restore mocks around each test. Mocking classes changed shape in recent releases (the mock implementation for a class is given as a class or constructor function); check the current docs before writing one.

#### pytest (8.x)

| Need | API | Note |
|---|---|---|
| Patch attribute, dict item or environment | `monkeypatch.setattr(target, name, value)`, `setitem`, `setenv(name, value)`, `delenv(name, raising=False)` | All changes are undone after the test or fixture finishes |
| Patch by dotted path | `monkeypatch.setattr("package.module.name", value)` | Raises if the attribute is missing unless `raising=False` |
| Scoped patch | `with monkeypatch.context() as m:` | Patch only inside a block |
| Session-wide patch | `pytest.MonkeyPatch.context()` in a session-scoped fixture | `monkeypatch` itself is function-scoped |
| Fixture with teardown | `@pytest.fixture` with `yield` | Code after `yield` runs at teardown |
| Fixture scope | `@pytest.fixture(scope="module")` and others | Narrowest scope that works; wider scopes share state |
| Applied everywhere | `@pytest.fixture(autouse=True)` in `conftest.py` | Use for a safety net, such as blocking network access |
| Temporary files | `tmp_path` fixture | Per-test directory; never write into the repository |

Where to patch: patch an object in the namespace where it is **looked up** (where the code under test imports it), not where it is defined.

#### Python `unittest.mock`

| Need | API | Note |
|---|---|---|
| Stub or spy | `Mock(return_value=..., side_effect=...)`, `MagicMock` | `side_effect` can raise or return a sequence |
| Patch | `patch("package.module.Name")` as decorator or `with` | Patch where it is looked up |
| Keep the real signature | `create_autospec(obj)`, `patch(..., autospec=True)`, `Mock(spec=Cls)`, `spec_set` | Wrong arguments fail like the real call |
| Async | `AsyncMock` | Awaitable mock for coroutine functions |
| Patch a dict temporarily | `patch.dict(target, values, clear=False)` | Restored after the block |
| Assertions | `assert_called_once_with(...)`, `assert_not_called()` | Use sparingly (see above) |

### Fixtures and factories

A fixture is the known state a test starts from. Keep it small, explicit and local.

- **Inline first.** Put the values the test depends on in the test body. A reader should see why the expectation holds without opening another file.
- **Builders and factories for the rest.** Provide a function that returns a valid object with sensible defaults and lets the test override only what matters. Tests then name the one field they care about.
- **No shared mutable state.** Every test builds its own data. A fixture shared at module or session scope must be immutable, or recreated per test.
- **Minimal data.** One user, one order, not a copy of production. Fewer rows mean faster tests and clearer failures.
- **Deterministic data.** No `now`, random values or auto-increment values assumed by the assertion.
- **No real personal data or secrets.** Use obviously fake values such as `sam@example.test`. Never paste production records into fixtures.
- **Put reusable helpers in one place** following the project's layout (for example a `tests/helpers` or `fixtures` folder) and reuse them instead of duplicating.
- **Large fixtures are a smell.** If setup is longer than the test, the unit has too many collaborators or the fixture is covering too much.

Database-backed tests need their own isolation (transaction rollback, per-test schema, cleanup of created rows only). Those setups belong to `testing-strategy`; never point them at a shared or production database.

### Isolation and cleanup

- Everything a test changes must be undone automatically: patches, spies, fake timers, environment variables, globals, temp files, registered handlers.
- Prefer the framework mechanism (config option, fixture teardown, `monkeypatch`, `afterEach`) over a hand-written reset at the end of a test body, which is skipped when the test fails.
- A test must pass alone, in any order, and in parallel with others if the runner parallelises. Order dependence and leaked state are the commonest source of flakiness.
- Cleanup deletes only what the test created, in a temporary location. Do not run deletion helpers against anything but a disposable test environment.
- Await asynchronous work; never use arbitrary sleeps. Wait for a condition with an explicit timeout or advance a fake clock.

### Clocks, timers and dates

Real time makes tests slow and flaky. Control it in one of two ways, in this order:

1. **Inject a clock.** Production code takes a `now()` function or a clock object (default: the system clock). Tests pass a fixed or controllable one. This works in every language and needs no framework magic.
2. **Fake the runtime clock.** Use the framework's fake timers when the code reads `Date.now()` or uses `setTimeout` directly and cannot be changed.

Rules:

- Pin the **time zone** for tests that format or compare dates, or build instants in UTC.
- Test expiry and scheduling at the **boundary**: one unit before, at and after.
- Restore real timers after each test. In Vitest, `setSystemTime` persists across tests until reset.
- Fake timers do not resolve real promises by themselves; use the async advance variants where the code awaits.
- Never assert against `now` computed in the test with the same call the code makes; fix the instant instead.

### Randomness and generated identifiers

- **Inject** the random source or identifier generator (a `random()` function, an id factory) so a test can supply a known sequence.
- Where injection is impossible, stub the runtime function for the duration of one test and restore it.
- Do not assert on specific random output; assert on properties (length, range, uniqueness).
- For property-based tests, record the seed or the shrunk counterexample so failures replay (see [test-design.md](test-design.md)).
- Generated ids and timestamps in output are normalised or injected before comparing whole objects.

### Network, filesystem and environment

- **Network:** tests make no live third-party calls. Stub at your own adapter. Add a safety net that fails any real outbound request in unit tests (a pytest autouse fixture, a Jest or Vitest setup file).
- **Filesystem:** write only to a temporary directory created for the test. Do not depend on the current working directory or on files outside the repository.
- **Environment variables:** set and restore through the framework (`monkeypatch.setenv`, scoped helpers); never rely on a developer's machine settings. Use placeholders such as `<API_TOKEN>` in documentation and fake values in tests; never real credentials.
- **Process and platform:** do not depend on locale, OS path separators or installed tools unless that is the behaviour under test.

## Examples

### Over-mocked to behaviour-focused (TypeScript)

Bad: asserts internal calls and structure.

```ts
test("registers a user", async () => {
  const repo = { save: jest.fn(), findByEmail: jest.fn().mockResolvedValue(null) };
  const hasher = { hash: jest.fn().mockResolvedValue("h") };
  await new UserService(repo as any, hasher as any).register("sam@example.test", "pw");
  expect(hasher.hash).toHaveBeenCalledTimes(1);
  expect(repo.save).toHaveBeenCalledWith({ email: "sam@example.test", password: "h" });
});
```

Good: uses an in-memory fake and asserts the outcome.

```ts
class InMemoryUsers implements UserRepository {
  rows = new Map<string, User>();
  async findByEmail(email: string) { return this.rows.get(email) ?? null; }
  async save(user: User) { this.rows.set(user.email, user); }
}

test("a registered user can be found and the password is not stored in clear text", async () => {
  const users = new InMemoryUsers();
  const service = new UserService(users, new FakeHasher());

  await service.register("sam@example.test", "correct horse");

  const stored = await users.findByEmail("sam@example.test");
  expect(stored).not.toBeNull();
  expect(stored!.passwordHash).not.toBe("correct horse");
});
```

### Factory with overrides

```ts
function makeOrder(overrides: Partial<Order> = {}): Order {
  return { id: "o-1", totalCents: 1000, isMember: false, items: [], ...overrides };
}

test("members never pay shipping", () => {
  const order = makeOrder({ isMember: true });
  expect(shippingFee(order)).toBe(0);
});
```

### Injected clock (TypeScript)

```ts
export type Clock = { now(): Date };

export function isExpired(issuedAt: Date, lifetimeMs: number, clock: Clock): boolean {
  return clock.now().getTime() - issuedAt.getTime() >= lifetimeMs;
}
```

```ts
test("a link is expired exactly at its lifetime", () => {
  const issued = new Date("2026-01-01T12:00:00Z");
  const at = (ms: number): Clock => ({ now: () => new Date(issued.getTime() + ms) });

  expect(isExpired(issued, 3_600_000, at(3_599_999))).toBe(false);
  expect(isExpired(issued, 3_600_000, at(3_600_000))).toBe(true);
});
```

### Fake timers with Jest

```ts
beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

test("shows the toast for 3 seconds", () => {
  jest.setSystemTime(new Date("2026-01-01T00:00:00Z"));
  const toast = showToast("Saved");
  expect(toast.isVisible()).toBe(true);

  jest.advanceTimersByTime(2999);
  expect(toast.isVisible()).toBe(true);

  jest.advanceTimersByTime(1);
  expect(toast.isVisible()).toBe(false);
});
```

Vitest is the same with `vi.useFakeTimers()`, `vi.setSystemTime(...)`, `vi.advanceTimersByTime(...)` and `vi.useRealTimers()`.

### Partial module mock with Vitest

```ts
import { vi, test, expect } from "vitest";
import { sendEmail } from "./mailer";
import { notifyOwner } from "./notify";

vi.mock("./mailer", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./mailer")>()),
  sendEmail: vi.fn().mockResolvedValue({ queued: true }),
}));

test("notifies the owner once", async () => {
  await notifyOwner({ ownerEmail: "owner@example.test", docTitle: "Plan" });
  expect(sendEmail).toHaveBeenCalledWith(expect.objectContaining({ to: "owner@example.test" }));
});
```

### pytest: patch where it is looked up, and an autouse safety net

```python
# conftest.py
import pytest

@pytest.fixture(autouse=True)
def no_real_http(monkeypatch):
    # Any attempt to send a real request through requests fails the test.
    monkeypatch.delattr("requests.sessions.Session.request")
```

```python
# test_notify.py
from unittest.mock import create_autospec

import notify          # notify.py does: from mailer import send_email
import mailer

def test_notify_owner_sends_one_email(monkeypatch):
    fake_send = create_autospec(mailer.send_email, return_value=True)
    monkeypatch.setattr(notify, "send_email", fake_send)   # patch where it is looked up

    notify.notify_owner("owner@example.test", "Plan")

    fake_send.assert_called_once_with("owner@example.test", subject="Plan updated")
```

`create_autospec` makes a call with the wrong arguments fail, as the real function would.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Mocking the unit under test or its private helpers | The test checks the mock and breaks on refactors | Call the real unit; double only its boundaries |
| Mocking a large third-party client directly | Tests encode guesses about its behaviour | Wrap in an adapter you own; double the adapter |
| Asserting call counts of internal methods | Couples tests to structure | Assert outcomes; assert calls only when specified |
| Free-standing `fn()` with no tie to the real signature | Doubles drift and tests pass against fiction | Use autospec, typed interfaces or `spyOn` on the real object |
| Patching where the object is defined | The code under test still uses the original | Patch where it is looked up (the importing module) |
| Relying on `restoreAllMocks` for `jest.fn()` assignments | It restores only `spyOn` mocks; the patch leaks | Use `spyOn`, or restore manually, or use a config option |
| Leaving fake timers or a faked system time on | Later tests see frozen time | Restore in `afterEach` or a fixture teardown |
| Reading `Date.now()` or `random()` in code under test with no seam | Flaky or untestable | Inject a clock or random source |
| Large shared fixtures at module or session scope | Order dependence and leaks | Per-test builders; immutable shared data |
| Real network, real accounts or production data in tests | Safety, privacy and flakiness risk | Stubs at the adapter and a network safety net |
| Arbitrary sleeps to wait for async work | Slow and still flaky | Await the operation, wait on a condition or advance a fake clock |

## Checklist

- [ ] Every double has a stated reason: slow, non-deterministic, side-effecting, unavailable or hard-to-fail.
- [ ] The unit under test, pure functions and value objects are real.
- [ ] Doubles for owned boundaries are bound to the real signature (autospec, typed interface or contract test).
- [ ] Third-party libraries are reached through an adapter that the tests double, not mocked at full surface.
- [ ] Assertions are on outcomes; call assertions exist only where the call is the specified behaviour.
- [ ] Every patch, spy, fake timer, global stub and environment change is restored automatically.
- [ ] Each test builds its own data; no test depends on another or on shared mutable state.
- [ ] Time and randomness come from an injected source or a restored fake, and the time zone is pinned where relevant.
- [ ] Tests make no live network calls and write only to temporary locations.
- [ ] Test data is fake: no real personal data, secrets or production records.
- [ ] There are no arbitrary sleeps; async work is awaited or controlled by a fake clock.
- [ ] The mocking API used was confirmed for the installed framework version.

## Verify with context7 and gh_grep

- **context7:** resolve the project's framework and version from the manifest, then query: "jest 29 jest.mock factory hoisting mock prefix", "jest restoreAllMocks only spyOn", "jest config clearMocks resetMocks restoreMocks", "vitest vi.mock vi.hoisted importOriginal", "vitest restoreMocks mockReset behaviour change", "vitest vi.stubGlobal unstubGlobals", "pytest monkeypatch setattr delenv context", "pytest fixture scope yield teardown autouse", "unittest.mock create_autospec patch where to patch AsyncMock". Record the version each answer applies to.
- **gh_grep:** search literal code for real usage before inventing a pattern, for example `vi.hoisted(`, `vi.mock(`, `jest.spyOn(`, `jest.useFakeTimers(`, `vi.useFakeTimers(`, `monkeypatch.setattr(`, `monkeypatch.setenv(`, `@pytest.fixture(autouse=True)`, `create_autospec(`, `patch.dict(`. Prefer official documentation when it disagrees with a repository example.

## Sources

- Jest, The Jest Object (version 29.7 page read; module mocks, timers, `setSystemTime`): https://jestjs.io/docs/29.7/jest-object
- Vitest, Mocking guide (read; `vi.mock`, `vi.hoisted`, `importOriginal`, `vi.stubGlobal`, `vi.setSystemTime`): https://vitest.dev/guide/mocking.md
- Vitest 3, Mocking guide (read): https://v3.vitest.dev/guide/mocking
- pytest, How to monkeypatch/mock modules and environments (read): https://docs.pytest.org/monkeypatch.html
- pytest 7.1 monkeypatch page (read; fixtures built on `monkeypatch`): https://docs.pytest.org/en/7.1.x/monkeypatch.html
- Python documentation, unittest.mock (read; `patch`, `create_autospec`, `spec_set`, where to patch): https://docs.python.org/3/library/unittest.mock.html
