# Red, Green, Refactor

The test-first cycle in detail: rules, step size, what a valid red and a minimal green look like, safe refactoring, and the violations that quietly defeat it. Examples use TypeScript with Jest-style assertions (also valid in Vitest) and Python with pytest; checked against Jest 29.7, Vitest 3 and current docs, and pytest 8 on 2026-11-26. The project's own runner and conventions win.

## Contents

- The cycle in one paragraph
- Working rules
- The test list
- Red: write one failing test
- Green: the least code that passes
- Refactor: improve with the tests green
- Step size and when to shrink it
- Choosing the next test
- When test-first does not fit
- Violations and how to spot them

## Guidance

### The cycle in one paragraph

Pick one small behaviour. Write a test that states it. Run the test and watch it fail for the right reason (red). Write the least production code that makes it pass without breaking anything else (green). Clean up production and test code while everything stays green (refactor). Pick the next behaviour. The failing test is a measurement: it proves the test can detect the absence of the behaviour. The refactor step is where design improves; skipping it leaves only a pile of passing tests.

### Working rules

1. **No production code without a failing test that demands it.** If you cannot name the test that requires a line, do not write the line.
2. **Write only enough test to fail.** A test that fails because it cannot compile or import counts as a start, but you continue until it fails on an assertion.
3. **Write only enough code to pass.** Resist speculative generality, extra parameters and branches no test exercises.
4. **Run the tests at every colour change.** Run after writing the test (expect red), after the code (expect green) and after each refactoring step (expect green). A run you skipped is a colour you assumed.
5. **Refactor only on green.** If a test is red, you are not refactoring; you are debugging or implementing.
6. **Change one thing at a time.** Either behaviour (a new test and its code) or structure (a refactoring), never both in the same step.
7. **Keep the whole suite for the area fast.** A slow cycle gets skipped. If a test needs seconds, it is probably at the wrong level; level choice belongs to `testing-strategy`.
8. **Tests are code.** They get names, small functions and removal of duplication, but stay more explicit than production code: a reader must see inputs and expectation together.

### The test list

Before the first test, write a short list of behaviours, one line each, derived from the acceptance criteria. It is a to-do list, not a design.

- Start from the criteria. Each criterion yields one or more list items: normal case, each error case, each boundary.
- Order from simplest and most degenerate to more complex: empty input, single item, typical, limit, invalid.
- Add items as you discover them during green or refactor; do not stop the cycle to implement them.
- Cross off items as they go green. The list is your progress record and goes in the report.
- For how to find the cases systematically (equivalence classes, boundaries, tables, states, properties), open [test-design.md](test-design.md).

### Red: write one failing test

A valid red has all of these properties:

- The test is **new** and covers one behaviour.
- It **fails**, and the failure message states the missing behaviour (expected value versus received value, expected error versus none).
- It fails **for the intended reason**. A typo, missing import, wrong fixture or wrong path is a broken test, not a red. Fix the test and rerun until the reason is right.
- You have **recorded** the output: command and failing message.

Getting from "does not exist" to a real failure:

1. Write the test calling the function or endpoint as a user of it would.
2. Run it. Expect "not defined", "cannot find module" or "no such route".
3. Add the smallest empty shell so the test can run: an exported function, a route returning a placeholder. In typed languages, add the signature.
4. Run again. Now the failure should be an assertion. If it is not, fix the test, not the shell.

A shell that returns a deliberately wrong value is fine at this point. It is discarded the moment the real behaviour exists.

If a new test passes immediately, one of three things is true: the behaviour already exists, the test does not assert what you think, or the test cannot fail. Check by breaking the code under test on purpose; if the test still passes, delete or rewrite it. A test you have never seen fail has not been shown to work.

### Green: the least code that passes

Three strategies, in order of preference:

| Strategy | How | Use when |
|---|---|---|
| Obvious implementation | Write the real, simple solution directly | You are sure and it is a few lines |
| Fake it | Return the constant the test expects | You are unsure, or want to get to green fast |
| Triangulate | Add a second test with different data, forcing the general form | The constant would pass one test but you need a rule |

Rules for green:

- Make the current test and all earlier tests pass. If an earlier test breaks, undo the change and take a smaller step.
- Duplication and ugliness are allowed in green. Cleanliness is the refactor step's job.
- Do not handle cases that have no test. Add them to the list.
- If green takes more than two distinct attempts, stop and shrink the step (see below). Repeating variations of one idea is the signal.
- Do not edit the test to make it pass. The only reason to edit a test is that it was wrong (wrong expectation from the criteria, wrong setup); in that case go back to red.

### Refactor: improve with the tests green

Refactoring changes structure without changing observable behaviour. The tests are the safety net, so they must pass before you start and after every step.

Candidates:

- Remove duplication, including duplication between production code and the constants you faked.
- Rename for intent. A name that needs a comment is a candidate.
- Extract a function or variable; inline one that adds nothing.
- Move code to where it belongs.
- Simplify conditionals; replace a flag with two functions.
- In tests: extract a builder for repeated setup, rename a test so its failure reads like a sentence, delete a test made redundant by a stronger one (never one that guards a criterion).

Rules:

- Make one small change, run the tests, continue. If a test goes red, revert that step; do not debug forward.
- Do not edit tests while refactoring production code. If a refactoring forces a test change, the test was coupled to implementation: that is a finding to fix as its own step, after confirming it still asserts the same behaviour.
- Stop when the code expresses intent and no obvious duplication remains. Do not generalise for imagined future needs.
- Public behaviour changes (an API shape, a message) are not refactoring. They need a failing test first.
- A large restructuring belongs in its own planned task, not inside the cycle. For the procedure, load `sdlc-workflows`.

### Step size and when to shrink it

The right step is the smallest that is meaningful: a few lines of test and a few lines of code, a cycle measured in minutes.

| Signal | Meaning | Action |
|---|---|---|
| Red to green takes several attempts | Step too large | Delete the attempt, write a smaller test (simpler input, one rule) |
| One test forces changes across many files | Test is too high level or design is tangled | Test a smaller unit first, or add a seam |
| You cannot predict the failure message | You do not understand the behaviour | Write a smaller test; read the criterion again |
| Green feels trivial every time | Step may be too small | Combine two obvious steps; do not drop the red |
| Refactor step breaks tests repeatedly | Steps too large or tests coupled to structure | Smaller moves; fix coupling |

Practical limit: if the same failure survives two distinct fix attempts, stop. Revert to the last green state and take a smaller step. The implementer's loop limit (2 attempts, then escalate) applies on top of this.

### Choosing the next test

- Prefer a test that forces a new line of code or a new decision.
- Take degenerate and error cases early (empty, zero, missing). They shape the structure cheaply.
- Move from constants to variables to conditionals to loops, as the tests demand.
- Take boundaries after the general rule exists, so you learn whether the rule or the boundary was wrong.
- When two tests are equally good, pick the one whose failure you can predict best.

### When test-first does not fit

Test-first is a tool, not a ritual. Do not force it where the failing test cannot be written first, but say so in the report and still add tests afterwards.

| Situation | What to do instead |
|---|---|
| Exploratory spike to learn an unfamiliar API | Spike, throw the code away, then restart test-first with what you learned |
| Visual layout and styling | Add a behavioural test for logic and states; check visuals with the UI procedure in `testing-strategy` |
| Generated code, pure configuration | Test the behaviour that depends on it, not the generated text |
| Legacy code with no tests that must change | Add characterization tests that pin current behaviour first, then change with new red tests |
| Third-party behaviour you only call | Test your adapter; do not test the library |

Characterization tests record what the code does today, which may be wrong. Mark them as such so nobody mistakes them for requirements.

## Examples

### A worked cycle (TypeScript, Jest or Vitest)

Rule from the requirement: members never pay shipping; non-members pay 500 cents under 5000 cents and nothing at 5000 or more.

Test list:

```text
[ ] member pays nothing
[ ] non-member below the threshold pays 500
[ ] non-member at exactly the threshold pays nothing
[ ] non-member above the threshold pays nothing
[ ] negative total is rejected
```

Cycle 1, red. Write the test, then the smallest shell so it can run:

```ts
// shipping.test.ts
import { shippingFee } from "./shipping";

test("members never pay shipping", () => {
  expect(shippingFee({ totalCents: 1000, isMember: true })).toBe(0);
});
```

```ts
// shipping.ts (shell)
export function shippingFee(order: { totalCents: number; isMember: boolean }): number {
  return -1;
}
```

Run result (recorded): `Expected: 0  Received: -1`. This is a valid red: an assertion about the missing behaviour.

Cycle 1, green (fake it):

```ts
export function shippingFee(order: { totalCents: number; isMember: boolean }): number {
  return 0;
}
```

Cycle 2, red: add the non-member test.

```ts
test("non-members below the threshold pay 500 cents", () => {
  expect(shippingFee({ totalCents: 4999, isMember: false })).toBe(500);
});
```

Run: `Expected: 500  Received: 0`. Green by triangulating:

```ts
export function shippingFee(order: { totalCents: number; isMember: boolean }): number {
  if (order.isMember) return 0;
  return 500;
}
```

Cycle 3, red: the boundary.

```ts
test("non-members at exactly the threshold pay nothing", () => {
  expect(shippingFee({ totalCents: 5000, isMember: false })).toBe(0);
});
```

Run: `Expected: 0  Received: 500`. Green:

```ts
const FREE_SHIPPING_THRESHOLD_CENTS = 5000;
const STANDARD_FEE_CENTS = 500;

export function shippingFee(order: { totalCents: number; isMember: boolean }): number {
  if (order.isMember) return 0;
  return order.totalCents >= FREE_SHIPPING_THRESHOLD_CENTS ? 0 : STANDARD_FEE_CENTS;
}
```

Refactor on green: the constants are already named; the three tests share no setup worth extracting. Run all three tests, still green. Next list item: negative totals, which starts a new red.

### The same cycle in pytest, bug-fix flavour

Report: "A cart with a 100% coupon charges a negative total." First the failing regression test:

```python
# test_cart.py
from cart import total_cents

def test_full_discount_never_goes_below_zero():
    assert total_cents(items=[1000], discount_percent=100) == 0
```

Run the test against the buggy code and record the output. It must show the reported symptom, a negative total in the assertion message, for example `assert -100 == 0` if the buggy code subtracted more than the item total. A failure about a missing import or a wrong argument name is not the reported bug. After the fix the test passes. Revert the fix temporarily to confirm the test fails again, then restore it.

### A false green, bad to good

Bad: the test passes immediately because it asserts the wrong thing.

```ts
test("rejects invalid email", () => {
  const result = validateEmail("not-an-email");
  expect(result).toBeDefined(); // passes for any return value
});
```

Good: it asserts the outcome, and was seen to fail against a validator that accepts everything.

```ts
test("rejects an address without an at sign", () => {
  expect(validateEmail("not-an-email")).toEqual({ ok: false, error: "MISSING_AT" });
});
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Writing the code first and the test after | The test is shaped by the code and never seen to fail | Write the test first, or say test-first was not possible and why |
| Accepting a failure caused by a typo or import error as red | The test was never shown to detect the behaviour | Rerun until the failure is an assertion about the behaviour |
| Writing several tests, then the code | Large step, vague failures, big green jump | One test, one behaviour, one cycle |
| Writing more code than the test needs | Untested behaviour appears | Add the extra case to the list and write a test for it |
| Refactoring while red | You cannot tell what broke | Return to green first, or revert |
| Editing a test to make it pass | Hides a defect or a wrong implementation | Fix the code; edit the test only if it misstated the criterion |
| Skipping the refactor step | Duplication and unclear names pile up | Spend a minute each cycle on names and duplication |
| Never running the full area suite | Breaks elsewhere go unseen | Run the area suite at each green |
| Mocking everything to keep tests small | Tests pass while the real wiring is broken | Use real collaborators where cheap; see [mocking-fixtures.md](mocking-fixtures.md) |
| Treating TDD as a coverage exercise | Weak assertions satisfy a number, not a behaviour | Assert outcomes from criteria |

## Checklist

- [ ] A test list derived from the acceptance criteria exists, including error and boundary cases.
- [ ] Each cycle started with a test that was run and failed.
- [ ] Each recorded red failed on an assertion about the missing behaviour, not on setup, syntax or imports.
- [ ] Each green change is the smallest that passes, and every earlier test still passes.
- [ ] Tests were run after every colour change, including each refactoring step.
- [ ] No test was edited during a refactoring of production code.
- [ ] No test was weakened, skipped or deleted to reach green.
- [ ] Any test that passed on its first run was proved able to fail.
- [ ] A step that resisted two fix attempts was reverted and shrunk.
- [ ] Where test-first was not possible, the report states why and when tests were added.

## Verify with context7 and gh_grep

- **context7:** confirm the project's runner and version from the manifest, then query the assertion and failure-output behaviour you rely on, for example "jest 29 expect toBe toEqual failure message", "vitest test.each syntax", "pytest assert rewriting failure output" or "pytest parametrize ids". Check anything you record as the expected red message against the installed version.
- **gh_grep:** search literal code for how maintained projects name and structure first tests, for example `test("rejects`, `it("returns`, `def test_.*_raises`, `pytest.raises(`, `expect(.*).toThrow(`. Use results to match naming style, not to copy tests.

## Sources

- Jest, The Jest Object (version 29.7 page read; timers, mock modules): https://jestjs.io/docs/29.7/jest-object
- Vitest, Mocking guide (read): https://vitest.dev/guide/mocking.md
- pytest, How to monkeypatch/mock modules and environments (read): https://docs.pytest.org/monkeypatch.html
- Python documentation, unittest.mock (read): https://docs.python.org/3/library/unittest.mock.html
