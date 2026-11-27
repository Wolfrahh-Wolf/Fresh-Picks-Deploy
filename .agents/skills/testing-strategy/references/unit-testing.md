# Unit Testing

Scope, structure, naming, determinism, boundaries and error paths for unit tests, with examples for Vitest 5.1, Jest 30.5 and pytest 9.2 (checked 2026-11-26). The project's existing runner, layout and naming conventions override these defaults.

## Contents

- What a unit is
- Structure of a test
- Naming
- Determinism
- Boundaries and equivalence classes
- Error paths
- Assertions that can fail
- Parametrised tables
- Async code
- Running unit tests
- Routing to other skills

## Guidance

### What a unit is

A unit is a behaviour reachable through a public interface, not necessarily one class or one function. Test through the interface a caller would use; a test that needs to reach into private state is testing the wrong thing.

- Scope one test to one behaviour: one reason to fail.
- Keep the unit's real collaborators when they are pure and cheap (value objects, helpers). Replace only collaborators that do I/O, are slow, or are non-deterministic. For how to build doubles, load `test-driven-development`.
- If the behaviour is only observable through a database, a network call or a browser, it is not a unit test; go up a level (see `test-pyramid.md`).
- A refactor that preserves behaviour must not break the test. If it does, the test asserts implementation detail.

### Structure of a test

Use arrange, act, assert, in that order, with a blank line between the phases.

1. **Arrange:** build only the input and state this test needs. Prefer inline values over shared setup so the test reads on its own.
2. **Act:** one call to the behaviour under test.
3. **Assert:** check the observable result: a return value, a thrown error, a changed output state, or a message sent to a boundary when that message is the specified behaviour.

Rules:

- One act per test. Two acts usually mean two behaviours.
- Put the expected value in the test as a literal derived from the requirement. Do not compute it with the production code or an equivalent re-implementation.
- Keep setup shared by `beforeEach` or a fixture to what is truly common; hide nothing the reader needs to understand the assertion.
- Each test creates its own state. A test must pass alone, in a different order and in the full suite.

### Naming

A failure message should explain which behaviour broke without opening the file. Name the behaviour, the condition and the outcome.

| Weak | Strong |
|---|---|
| `test1`, `works`, `testDiscount` | `applies 10 percent when code is SAVE10` |
| `error case` | `rejects a negative total with RangeError` |
| `test_user` | `test_inactive_user_cannot_log_in` |

Conventions by runner: Vitest and Jest use `describe('subject', () => { it('does X when Y', ...) })`; pytest uses `test_<behaviour>_<condition>` in files named `test_*.py` or `*_test.py`, which pytest discovers automatically. Follow whatever the project already does.

### Determinism

A unit test gives the same result on every machine at every time. Remove these sources of variance:

| Source | Control |
|---|---|
| Current time, time zones, daylight saving | Pass the time in as an argument or inject a clock; set the zone explicitly if the code reads it |
| Random values and generated IDs | Inject the generator or seed it; assert properties, not exact random output |
| Locale, currency and number formatting | Set the locale explicitly in the test, never rely on the machine default |
| File system | Use the runner's temporary directory (for pytest, the `tmp_path` fixture) |
| Environment variables and globals | Set and restore them inside the test; never leave them changed |
| Test order | No test relies on another; run the file in a different order to confirm |
| Floating point | Compare money in integer minor units, or use a tolerance matcher for genuine floats |
| Iteration order of maps and sets | Sort before comparing, or compare as sets |
| Network and real services | Not allowed in a unit test; replace the boundary (load `test-driven-development`) |

Never use an arbitrary sleep. If a unit test needs to wait, the code under test needs an injectable clock or a promise to await.

### Boundaries and equivalence classes

For each input, partition into classes that the code should treat alike, then test one value inside each class and the values on every edge.

For a numeric rule "quantity must be 1 to 100":

| Class | Values to test |
|---|---|
| Below range | 0, -1 |
| Lower edge | 1 |
| Inside | 50 |
| Upper edge | 100 |
| Above range | 101 |
| Wrong type or missing | `undefined`, `null`, `"5"`, `NaN` where the language allows it |

Other boundaries worth a case: empty string, empty collection, single element, very long input, Unicode (accents, emoji, right-to-left text), leading and trailing whitespace, the first and last day of a month, leap day, midnight, and arithmetic overflow where the language has fixed-size numbers.

For choosing partitions, decision tables and property-based tests in depth, load `test-driven-development`.

### Error paths

Every behaviour that can fail has a test for the failure, asserted as precisely as the specification allows.

- Assert the error type or code and, where it is part of the contract, the message. Do not assert on the full stack trace.
- Assert that the failure leaves no partial state: nothing written, nothing sent.
- Test the permission-denied path wherever the specification restricts who may act.
- Test invalid input at the point the unit accepts it.
- For code that wraps an external failure, assert what the caller sees (the mapped error), using a stand-in that fails.

### Assertions that can fail

A test is worth keeping only if breaking the behaviour makes it fail.

- Assert specific values: `toBe(90)`, not `toBeDefined()`, not "no error thrown".
- Avoid tautologies: `expect(result).toEqual(result)`, or asserting a mock returned what you told it to return.
- Avoid one-sided matchers on collections: check content and order when order is specified.
- After writing a test, confirm it can fail: change the code (or the expected value) temporarily in your working copy and watch it go red, then restore. A reviewer checks this by reading: "if the condition were inverted, would this test fail?"
- Do not use snapshots as a substitute for thinking; if you use one, keep it small and read the diff.

### Parametrised tables

Use a table when the same behaviour is checked over many inputs, so each row names its case.

- Vitest and Jest: `it.each` / `test.each`. Vitest interpolates `$field` from object rows into the title.
- pytest: `@pytest.mark.parametrize(("total", "code", "expected"), [...])`. Use `pytest.param(..., id="...")` for readable IDs when the values alone do not explain the case.
- Do not put branching logic inside a table test; if the rows need different assertions, they are different tests.

### Async code

- Always `await` (or return) the promise or coroutine. A missing `await` makes the test pass without checking anything; the Playwright documentation recommends the `@typescript-eslint/no-floating-promises` rule for this reason, and the same rule helps in unit tests.
- Assert rejections explicitly: `await expect(fn()).rejects.toThrow(...)` in Vitest and Jest, `with pytest.raises(...)` around `await` in async pytest tests (needs the project's async plugin; check its documentation with context7).
- Never poll with a fixed sleep; use the runner's fake timers (see `test-driven-development`) or await the event.

### Running unit tests

Prefer the project's own script (`npm test`, `pnpm test`, `python -m pytest`). When no script exists, these are the common forms (all confirmed against Vitest 5.1.2, Jest 30.5.2 and pytest 9.2.0):

| Goal | Vitest | Jest | pytest |
|---|---|---|---|
| Whole suite once | `npx vitest run` | `npx jest` | `python -m pytest` |
| One file | `npx vitest run tests/price.test.ts` | `npx jest tests/price.test.ts` | `python -m pytest tests/test_price.py` |
| By name | `npx vitest run -t "SAVE10"` | `npx jest -t "SAVE10"` | `python -m pytest -k save10` |
| Tests affected by changes | `npx vitest run --changed` | `npx jest --onlyChanged` | none built in; select by path or marker |
| Last failures only | none built in | none built in | `python -m pytest --lf` |
| Slowest tests | `--reporter verbose` | `--verbose` | `--durations=10` |

For pytest configuration the documentation suggests `--import-mode=importlib` for new projects and a `src` layout with `pythonpath = ["src"]`; both are project decisions, so follow the existing config.

### Routing to other skills

For red-green-refactor, doubles, mocks, fakes, factories, clocks and randomness, load `test-driven-development`. For integration tests, see `integration-testing.md`.

## Examples

### Vitest (TypeScript), boundaries and error path

```ts
// src/price.ts
export function discount(total: number, code?: string): number {
  if (total < 0) throw new RangeError('total must be >= 0');
  if (code === 'SAVE10') return Math.round(total * 90) / 100;
  return total;
}
```

```ts
// tests/price.test.ts
import { describe, it, expect } from 'vitest';
import { discount } from '../src/price';

describe('discount', () => {
  it.each([
    { total: 100, code: 'SAVE10', expected: 90 },
    { total: 50, code: undefined, expected: 50 },
    { total: 0, code: 'SAVE10', expected: 0 },
  ])('total $total with code $code gives $expected', ({ total, code, expected }) => {
    expect(discount(total, code)).toBe(expected);
  });

  it('rejects a negative total with RangeError', () => {
    expect(() => discount(-1)).toThrow(RangeError);
  });
});
```

### pytest (Python), boundaries and error path

```python
# tests/test_price.py
import pytest
from shop.price import discount


@pytest.mark.parametrize(
    ("total", "code", "expected"),
    [(100, "SAVE10", 90.0), (50, None, 50), (0, "SAVE10", 0.0)],
)
def test_discount_applies_code_only_when_valid(total, code, expected):
    assert discount(total, code) == expected


def test_discount_rejects_negative_total():
    with pytest.raises(ValueError, match="must be >= 0"):
        discount(-1)


def test_report_is_written_to_isolated_directory(tmp_path):
    target = tmp_path / "report.txt"
    target.write_text("ok")
    assert target.read_text() == "ok"
```

### Bad to good: asserting implementation instead of behaviour

Bad: passes when the call happens, even if the result is wrong; breaks when the internals are renamed.

```ts
it('calls the rounding helper', () => {
  const spy = vi.spyOn(helpers, 'roundCents');
  discount(100, 'SAVE10');
  expect(spy).toHaveBeenCalledTimes(1);
});
```

Good: asserts the result the requirement specifies.

```ts
it('gives 10 percent off, rounded to whole cents', () => {
  expect(discount(19.99, 'SAVE10')).toBe(17.99);
});
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Computing the expected value with the production code | The test passes by construction | Write the expected value as a literal from the requirement |
| Several acts and many assertions in one test | A failure does not say which behaviour broke | One behaviour per test; use a table for many inputs |
| Only the happy path | Failure paths ship untested | Add boundary, invalid, permission and failure cases |
| Asserting call counts and private state | Refactors break the test | Assert observable output |
| Missing `await` on a promise | The test passes without checking | Await or return it; enable the floating-promise lint rule |
| Real clock, random or locale in the code under test | Intermittent failures | Inject or control them; load `test-driven-development` |
| Shared mutable state across tests | Order dependence, vanishing failures | Build state inside each test and clean it up |
| Matching only on `toBeDefined()` or "did not throw" | The test cannot fail | Assert specific values |
| Using a sleep to wait | Slow and flaky | Await the event or use controlled timers |

## Checklist

- [ ] Each test names one behaviour, its condition and its outcome.
- [ ] Each test has exactly one act and passes in isolation.
- [ ] Expected values are literals traced to a requirement, not computed from the code under test.
- [ ] Boundary values on both sides of every limit are covered.
- [ ] Invalid input, permission denied and failure paths each have a test with a specific assertion.
- [ ] No sleeps, wall-clock reads, unseeded randomness, network or shared state.
- [ ] Every promise or coroutine is awaited, and rejections are asserted explicitly.
- [ ] Temporarily breaking the behaviour makes the test fail.
- [ ] The unit suite finishes in under 60 seconds.

## Verify with context7 and gh_grep

- **context7:** check the project's runner and version for: "Vitest `it.each` and `expect(...).rejects`", "Jest 30 `test.each` and `toThrow`", "pytest `parametrize`, `raises(match=...)` and `tmp_path`", "pytest `--import-mode` and `pythonpath` settings", and the async plugin the project uses.
- **gh_grep:** search literal code for real usage: `it.each([`, `toThrow(RangeError)`, `with pytest.raises(`, `@pytest.mark.parametrize(`, `tmp_path /`.

## Sources

- [pytest: Good Integration Practices](https://docs.pytest.org/goodpractices.html), read 2026-11-26.
- [Playwright: Best Practices](https://playwright.dev/docs/best-practices) (floating-promise lint rule), read 2026-11-26.
- [Jest: Configuration](https://jestjs.io/docs/configuration), read 2026-11-26.
- [Vitest: Coverage guide](https://vitest.dev/guide/coverage), read 2026-11-26.
- Runner flags were confirmed from `--help` output of Vitest 5.1.2, Jest 30.5.2 and pytest 9.2.0, and the examples were executed, on 2026-11-26.
