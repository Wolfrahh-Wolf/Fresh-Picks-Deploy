# Test Design Techniques

How to derive test cases from a requirement: equivalence classes, boundaries, decision tables, state transitions, error guessing, and property-based tests, plus how to structure and name individual tests. Examples use TypeScript (Jest or Vitest), Python (pytest) and the property libraries Hypothesis 6 and fast-check 3/4; checked 2026-11-26. The project's own framework and conventions win.

## Contents

- From criterion to cases
- Equivalence classes
- Boundary values
- Decision tables
- State transitions
- Error guessing and risk weighting
- Reducing combinations
- Property-based tests
- Parametrised tests
- Structuring and naming a single test

## Guidance

### From criterion to cases

A criterion states one expectation; a test design turns it into the smallest set of cases that would catch a wrong implementation. Work in this order:

1. Identify the **inputs** (arguments, request fields, stored state, time, configuration) and the **outputs** (return value, response, message, state change a user can see).
2. For each input, list the **classes** of values the system should treat alike, including invalid ones.
3. Mark the **boundaries** between classes.
4. If several inputs interact, build a **decision table**. If the behaviour depends on history, draw the **states**.
5. Pick cases: one per class, plus values on and around each boundary, plus the error paths.
6. Add **risk-based** cases where a defect would be costly. Weight coverage toward risk: payment logic deserves more cases than a label change.
7. Write the cases as a test list and start the cycle in [red-green-refactor.md](red-green-refactor.md).

Every case traces to a criterion or a named risk. A case you cannot justify is noise. For the level at which each case should run (unit, integration, end-to-end), load `testing-strategy`.

### Equivalence classes

An equivalence class is a set of inputs the system should handle the same way. Testing one value from each class is enough to detect a class-level mistake; testing many values from one class adds cost and no information.

Procedure:

1. List the valid range or set and each distinct valid behaviour.
2. List the invalid classes: below range, above range, wrong type, missing, empty, malformed, not permitted.
3. Choose one representative per class. Prefer ordinary values, not boundaries; boundaries come next.
4. Give each class a test with a name that states the class.

Example: an age field accepts whole numbers 18 to 120.

| Class | Representative | Expected |
|---|---|---|
| Valid adult | 35 | accepted |
| Below range | 10 | rejected, error TOO_YOUNG |
| Above range | 150 | rejected, error TOO_OLD |
| Not a whole number | 35.5 | rejected, error NOT_INTEGER |
| Not a number | "abc" | rejected, error NOT_A_NUMBER |
| Missing | undefined | rejected, error REQUIRED |

Do not invent classes the requirement does not define. If the criterion does not say what happens for 35.5, ask; do not assert a guess.

### Boundary values

Defects cluster at edges, such as off-by-one comparisons and inclusive versus exclusive limits. For each ordered boundary test the value **on** the boundary and the values **just inside** and **just outside**.

For the age range 18 to 120 inclusive:

| Value | Position | Expected |
|---|---|---|
| 17 | just below minimum | rejected |
| 18 | minimum | accepted |
| 19 | just above minimum | accepted |
| 119 | just below maximum | accepted |
| 120 | maximum | accepted |
| 121 | just above maximum | rejected |

For two-sided ranges that is up to six cases; for one-sided limits, three. Also check the boundaries of:

- Sizes and lengths: 0, 1, limit, limit plus 1 (empty string, one character, maximum length, one over).
- Collections: empty, one element, many, limit.
- Dates and times: the instant of expiry, one unit before and after, day and month ends, leap days, daylight saving transitions. Use a fake clock (see [mocking-fixtures.md](mocking-fixtures.md)).
- Numbers: zero, negative, very large, floating-point rounding where money or measurements are involved (prefer integers of the smallest unit).

Inclusive versus exclusive is a requirement question. If the criterion says "up to 10 MB", ask whether exactly 10 MB passes; record the answer in the criteria.

### Decision tables

Use a decision table when several conditions combine to determine the outcome. It makes missing combinations visible.

Procedure:

1. List the conditions (inputs that change the outcome) and the possible actions.
2. List every combination of condition values. With n true or false conditions there are 2 to the n rows; reduce only where a condition provably does not matter and mark it with a dash.
3. Fill the expected action for each row from the criteria. A row nobody can fill is an open question.
4. Write one test per row (or per merged row). A table-driven test keeps this compact.

Example, discount eligibility: a customer gets 10% off when they are a member and the order is at least 5000 cents, and the discount is never stacked with a coupon.

| Member | Order at least 5000 | Coupon applied | Expected |
|---|---|---|---|
| yes | yes | no | 10% off |
| yes | yes | yes | coupon only, no member discount |
| yes | no | no | no discount |
| yes | no | yes | coupon only |
| no | yes | no | no discount |
| no | yes | yes | coupon only |
| no | no | no | no discount |
| no | no | yes | coupon only |

Eight rows, eight cases, and the "coupon only" rows reveal a rule the prose left implicit. Ask the requirement owner to confirm those rows before writing tests for them.

### State transitions

Use a state model when behaviour depends on what happened before: orders, sessions, retries, subscriptions, workflows.

Procedure:

1. List the states and the events (user actions, timeouts, messages).
2. Draw or tabulate each state and event with the next state and visible output.
3. Test every **valid transition** at least once.
4. Test **invalid events** in each state: the system must refuse or ignore them as specified.
5. Test paths that matter for risk: cancel after shipping, pay twice, expire during processing.

Example, order status:

| State | Event | Next state | Observable result |
|---|---|---|---|
| Draft | submit | Submitted | confirmation shown |
| Submitted | pay | Paid | receipt sent |
| Submitted | cancel | Cancelled | refund not needed |
| Paid | ship | Shipped | tracking number shown |
| Paid | cancel | Cancelled | refund issued |
| Shipped | cancel | Shipped | refused with ERROR_ALREADY_SHIPPED |
| Cancelled | pay | Cancelled | refused with ERROR_CANCELLED |

Seven rows give seven transition tests. Add "event in every other state" tests only for events that carry risk, since the full matrix grows fast; the model tells you which cells you chose not to test.

### Error guessing and risk weighting

Experience supplies cases no technique finds. Ask, for each input and dependency, what usually breaks:

- Empty, null, whitespace-only, extremely long or unusual-character input (accents, emoji, right-to-left text).
- Duplicates and repeats: submit twice, retry after timeout, double-click.
- Order and timing: out-of-order events, concurrent updates, stale data.
- Dependencies: slow, down, returning malformed data, returning an unexpected status.
- Permissions: not signed in, wrong role, someone else's data.
- Previous data: records created before this change, partially migrated data.

Weight the effort by risk: how likely is a defect, and how costly would it be? High-risk areas (authentication, payments, personal data, migrations) get more cases, and the security-auditor reviews them separately. Security-specific cases are owned by `security-engineering`.

### Reducing combinations

When inputs multiply (browsers times roles times locales), exhaustive testing is not an option.

- Test each input class once with ordinary values for the others (one-factor-at-a-time).
- For interacting inputs, use pairwise selection: choose cases so every pair of values appears together at least once. It is a heuristic that trades completeness for size, not a guarantee.
- Keep full combinations for the few that the criteria call out, or where the risk is high.

State what you chose not to cover and why; an unexplained gap looks like an oversight.

### Property-based tests

A property-based test states a rule that must hold for many generated inputs, instead of checking a hand-picked example. The library generates inputs, runs the check, and on failure shrinks the input to a small counterexample.

Use them when:

- A rule holds for a whole domain (sorting, parsing, encoding, normalising, arithmetic on money).
- The input space is large and edge cases are hard to enumerate.
- You can state the rule without re-implementing the function.

Do not use them for behaviour that is a list of specific business examples, for slow tests (each property runs many times), or when the only available property is a copy of the implementation.

Useful property shapes:

| Shape | Statement | Example |
|---|---|---|
| Round trip | decode(encode(x)) equals x | JSON, URL, custom serialisers |
| Invariant | A quality is preserved | Sorting keeps the same elements and length |
| Idempotence | f(f(x)) equals f(x) | Normalising whitespace, deduplicating |
| Oracle | The result matches a trivially correct slow version | Compare a fast algorithm with a simple one |
| Metamorphic | Changing input predictably changes output | Adding an item raises the total by its price |
| No crash | Any valid input does not raise | Parsing arbitrary text returns a result or a documented error |

Reproducibility rules:

- Record the seed or the shrunk counterexample from a failure and add it as a plain example test so the case stays covered forever.
- Do not make unseeded randomness a hidden source of flakiness in CI: failures must be replayable. Both libraries print what you need to replay a run.
- Keep the number of runs modest in routine suites and raise it in a scheduled job if the project has one.
- Constrain generators to the valid domain (ranges, sizes) instead of filtering most inputs away, which wastes runs.

Python with Hypothesis (6.x):

```python
from hypothesis import given, strategies as st

from codec import encode, decode

@given(st.text())
def test_decode_reverses_encode(text):
    assert decode(encode(text)) == text
```

Pinning a failing example you found as a permanent case:

```python
from hypothesis import example, given, strategies as st

@example("")            # found earlier: empty input
@given(st.text())
def test_decode_reverses_encode(text):
    assert decode(encode(text)) == text
```

JavaScript or TypeScript with fast-check:

```ts
import fc from "fast-check";
import { encode, decode } from "./codec";

test("decode reverses encode", () => {
  fc.assert(
    fc.property(fc.string(), (text) => decode(encode(text)) === text),
    { numRuns: 200 }
  );
});
```

fast-check failure reports include the seed and the path to the minimal counterexample, which you can pass back in the parameters of `fc.assert` to replay it. In recent versions integer ranges are given as a constraints object, for example `fc.integer({ min: 0, max: 100 })`; confirm the signature for the installed major version.

A property for money, avoiding a copy of the implementation:

```ts
test("splitting an amount never loses a cent", () => {
  fc.assert(
    fc.property(
      fc.integer({ min: 0, max: 1_000_000 }),
      fc.integer({ min: 1, max: 20 }),
      (cents, parts) => {
        const shares = splitCents(cents, parts);
        return shares.length === parts && shares.reduce((a, b) => a + b, 0) === cents;
      }
    )
  );
});
```

### Parametrised tests

Use parametrisation when the same behaviour is checked with different data, such as the boundary table above. The cases stay visible, each failure names its row, and the structure is written once.

Jest or Vitest (the `test.each` table form and its `%i` and `%s` title placeholders were not checked against the docs for this file: unverified, confirm with context7):

```ts
test.each([
  [17, false],
  [18, true],
  [120, true],
  [121, false],
])("age %i is accepted: %s", (age, accepted) => {
  expect(isValidAge(age)).toBe(accepted);
});
```

pytest:

```python
import pytest

@pytest.mark.parametrize("age, accepted", [(17, False), (18, True), (120, True), (121, False)])
def test_age_boundaries(age, accepted):
    assert is_valid_age(age) is accepted
```

Do not parametrise different behaviours into one table because they happen to share a setup; each behaviour gets its own test so the name explains the failure. When a row needs its own comment to be understood, split it out.

### Structuring and naming a single test

- **Arrange, act, assert.** Set up the state, perform one action, check the outcome. Separate the three parts with blank lines. One act per test.
- **One reason to fail.** Several asserts are fine when they describe one outcome; several outcomes belong to several tests.
- **Name by behaviour.** "rejects an address without an at sign" beats "test email 3". The failure message alone should tell a reader what broke.
- **Put the data where it is read.** The value that matters to the test (the amount, the role) appears in the test body; irrelevant values come from a default builder.
- **Check observable outcomes.** Assert on results, responses and visible state, not on private fields or the number of internal calls, unless the interaction is the specified behaviour.
- **Keep tests independent.** No test relies on another having run; none leaves state behind.
- **Error paths.** Assert the specific error (type, code, message the user sees), not just that something failed.

## Examples

### Criterion to cases, worked

Criterion FR-050: "The system shall accept image uploads up to 10 MB in JPEG, PNG or WebP and reject all other types with error UNSUPPORTED_TYPE and files above the limit with FILE_TOO_BIG."

Inputs: type, size. Classes and boundaries:

| Case | Type | Size (bytes) | Expected | Technique |
|---|---|---|---|---|
| 1 | PNG | 1 | accepted | boundary: smallest |
| 2 | PNG | 10485760 | accepted | boundary: at limit |
| 3 | PNG | 10485761 | FILE_TOO_BIG | boundary: just over |
| 4 | JPEG | 500000 | accepted | class: valid type |
| 5 | WebP | 500000 | accepted | class: valid type |
| 6 | GIF | 500000 | UNSUPPORTED_TYPE | class: invalid type |
| 7 | PNG | 0 | rejected, error from FR-052 | boundary: empty |
| 8 | GIF | 10485761 | UNSUPPORTED_TYPE or FILE_TOO_BIG? | decision: ask the requirement owner |

Row 8 is a decision table gap: both rules apply. The test list records it as an open question; the implementer is not left to choose.

### Table-driven test from the case list

```ts
test.each([
  ["png", 1, { ok: true }],
  ["png", 10_485_760, { ok: true }],
  ["png", 10_485_761, { ok: false, error: "FILE_TOO_BIG" }],
  ["gif", 500_000, { ok: false, error: "UNSUPPORTED_TYPE" }],
])("upload of %s with %i bytes", (type, size, expected) => {
  expect(validateUpload({ type, size })).toEqual(expected);
});
```

### Bad to good: asserting implementation

Bad: it copies the code's own formula and checks a private call.

```ts
test("total", () => {
  const spy = jest.spyOn(cart as any, "applyDiscount");
  const total = cart.total([1000, 2000], "SAVE10");
  expect(spy).toHaveBeenCalledTimes(1);
  expect(total).toBe((1000 + 2000) * 0.9);
});
```

Good: it states the criterion with hand-computed values and checks only what a user sees.

```ts
test("a 10% coupon reduces a 3000 cent cart to 2700 cents", () => {
  expect(cart.total([1000, 2000], "SAVE10")).toBe(2700);
});
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Testing many values from the same class | Cost with no new information | One representative per class, plus boundaries |
| Skipping boundaries | Off-by-one defects ship | Test on, just inside and just outside each boundary |
| Guessing the expected result for an unspecified case | The test invents a requirement | Mark it open and ask |
| One test per input field instead of per behaviour | Interactions are missed | Use a decision table for interacting inputs |
| Only valid transitions in a state model | Illegal events in the wrong state go untested | Test invalid events where risk is high |
| A property that reimplements the function | The test cannot disagree with the code | State a round-trip, invariant or oracle rule |
| Property tests with unrecorded seeds | Failures cannot be replayed | Record the seed or pin the counterexample as an example |
| Generators filtered down to almost nothing | Wasted runs and health warnings | Constrain the generator to the valid domain |
| Parametrising unrelated behaviours | Failure names do not explain the break | One behaviour per test or table |
| Expected values computed with the code's own logic | Proves the code agrees with itself | Hand-compute from the criterion |

## Checklist

- [ ] Inputs, outputs and classes are listed for each criterion.
- [ ] Each equivalence class, valid and invalid, has a case.
- [ ] Each ordered boundary has on, just-inside and just-outside cases.
- [ ] Inclusive versus exclusive limits were confirmed in the criteria, or marked open.
- [ ] Interacting conditions are covered by a decision table with no unexplained gaps.
- [ ] Stateful behaviour has a transition per valid event and invalid events for risky states.
- [ ] Error paths assert the specific error, not only failure.
- [ ] Risk-weighted extra cases exist for high-risk areas, and routine areas are not over-tested.
- [ ] Property-based tests state a rule independent of the implementation, with replayable seeds.
- [ ] Each test has one act, a behaviour-based name and independent data.
- [ ] Expected values come from the criteria, not from the code under test.

## Verify with context7 and gh_grep

- **context7:** before using a property or parametrisation API, query the installed version, for example "hypothesis given strategies text integers lists", "hypothesis example decorator and settings max_examples", "fast-check fc.assert fc.property numRuns seed replay", "fast-check fc.integer min max constraints", "jest 29 test.each table syntax", "pytest parametrize ids and indirect".
- **gh_grep:** search literal code for how real projects state properties and tables, for example `fc.assert(fc.property(`, `@given(st.`, `@pytest.mark.parametrize(`, `test.each([`, `@example(`. Use results to learn idiom, and confirm any API against the documentation for your version.

## Sources

- Hypothesis documentation, API reference (`@given`, `@example`, `@seed`, settings) (read): https://hypothesis.readthedocs.io/en/latest/reference/api.html
- fast-check repository documentation, Tips guide (seed, path, counterexample replay) (read): https://github.com/dubzzz/fast-check/blob/68a4c78741d23f068febe8b2816474726133882c/documentation/1-Guides/Tips.md
- Jest, The Jest Object (version 29.7 page read): https://jestjs.io/docs/29.7/jest-object
- pytest, How to monkeypatch/mock modules and environments (read; the `parametrize` marker usage shown is standard pytest but its reference page was not read): https://docs.pytest.org/monkeypatch.html
