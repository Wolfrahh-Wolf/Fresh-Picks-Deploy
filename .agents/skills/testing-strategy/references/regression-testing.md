# Regression Testing

Reproducing a bug before fixing it, selecting which tests to re-run, keeping the suite healthy, and quarantine rules; runner-neutral with Vitest 5.1, Jest 30.5, pytest 9.2 and Playwright 1.65 examples (checked 2026-11-26). Quarantine and skipping are governed by the Quality gates and Approval gates in `AGENTS.md`.

## Contents

- Reproduce before fix
- Writing the regression test
- Selecting what to re-run
- Suite upkeep
- Quarantine rules
- Routing to other skills

## Guidance

### Reproduce before fix

A regression test is evidence only if it failed before the fix, for the reason the bug describes. Without that, you do not know the test can detect the bug.

Procedure:

1. **Capture the report.** Record the symptom, the exact input, the expected behaviour (from the requirement, not from the code) and the actual result, with the verbatim error.
2. **Write the smallest failing test** at the lowest level that shows the defect (see `test-pyramid.md`). A bug found in a browser is often reproducible with a unit or API-level test; use the browser only if the defect is in the browser layer.
3. **Run it against the unfixed code** and confirm it fails with the expected assertion message, not a syntax error, import error, timeout or missing fixture. Record the command and the failing output.
4. **Hand the failing test to the implementer** (through the coordinator) or, if the fix already exists, go to step 5.
5. **Run it again after the fix** and confirm it passes. Record the passing output beside the failing output.
6. **If the fix already landed before you wrote the test,** prove the test detects the bug by running it against the pre-fix source. Do not edit production code to do this (the tester must not). Use a temporary, local checkout of the pre-fix revision, for example a scratch git worktree outside the repository: `git worktree add <scratch-dir> <pre-fix-commit>`, copy the new test file into it, run the test, and then remove the scratch checkout with `git worktree remove <scratch-dir>`. Both commands are local and change nothing in the repository's history; confirm the directory is the one you created before removing it. Never push, and never discard changes you did not create.
7. **If the cause is unknown,** stop and load `debugging` for root-cause analysis before writing the regression test.

If you cannot make the test fail, report that: either the bug is not reproducible with the information given, or the test does not exercise the defect. Do not report a regression test that has never failed.

### Writing the regression test

- Name the behaviour, and reference the report in the name or a comment: `rejects an expired coupon on the last second of the day (BUG-123)`. The reference helps future readers decide whether deleting the test is safe.
- Fix the input in the test as a literal, including the exact value that exposed the defect (the edge, the odd Unicode string, the empty list).
- Assert the specified behaviour, not the previous wrong output.
- Add neighbouring cases that a similar defect could break (the other side of the boundary, the sibling code path), but keep the test small.
- Keep the test in the same file as related tests, not in a separate "regressions" dump. A tag or marker (`@regression`) is fine if the project uses one.

### Selecting what to re-run

Select tests by the blast radius of the change, then widen when uncertain. Every source change invalidates earlier results for the affected area (`AGENTS.md`, Quality gates), so re-run after the last change, not before.

| Change | Minimum re-run |
|---|---|
| One function with local callers | Tests for that module and its direct callers |
| Shared helper, utility or model | All tests that import it; widen to the full unit suite |
| Configuration, build tooling, dependency version, test setup | Full suite (unit and integration) |
| Database schema or migration | Integration suite against a fresh database plus tests touching those tables |
| UI component used in many screens | Component tests plus the end-to-end journeys that include it |
| Public API or contract | Contract tests for every consumer of that endpoint |
| Bug fix | The new regression test, the module's tests, then the relevant suite |

Tool support for change-based selection (confirmed from `--help` on the stated versions):

| Runner | Command | Notes |
|---|---|---|
| Vitest 5.1 | `npx vitest run --changed` | Tests affected by changed files; `--changed <ref>` compares with a ref; needs a git repository |
| Jest 30.5 | `npx jest --onlyChanged`, `npx jest --changedSince=<ref>`, `npx jest --findRelatedTests <files>` | Uses the dependency graph; `--changedSince` needs a version-control ref |
| pytest 9.2 | `python -m pytest --lf`, `python -m pytest --ff`, `-k <expr>`, `-m <marker>` | Re-run last failures, run them first, select by name or marker; there is no built-in dependency-based selection |
| Playwright 1.65 | `npx playwright test --only-changed`, `--last-failed`, `-g <title>` | `--only-changed` selects changed test files, not tests affected by source changes |

Rules:

- Change-based selection is an optimisation. It can miss tests the dependency graph cannot see (dynamic imports, configuration, data files, end-to-end paths). Before reporting done, run the full relevant suite at least once, or state the gap.
- Tag or mark a small smoke set (the core journeys and the most critical unit tests) that runs on every change. Run the full suite on a slower cadence only if the project already does that; do not invent a cadence.
- For a high-risk change (the `AGENTS.md` list), run the full suite and the relevant integration and end-to-end tests, not only the changed area.
- Keep pre-existing failures separate: run the suite on the base revision if needed to show they existed before, and report them as unrelated.

### Suite upkeep

A regression suite is useful only while it is fast, trusted and current.

- **Fix or remove broken tests honestly.** A failing test means the code is wrong or the test is. Decide which. Updating an expectation is fine when the requirement changed (cite the requirement); changing it because the code now behaves differently is how regressions are accepted.
- **Never weaken, skip or delete an existing test to make a task pass.** That needs the user's approval (`AGENTS.md`). Report the conflict instead: test name, file, and what contradicts what.
- **Delete only with approval and a reason.** Obsolete when the feature is removed (check the requirement and the PRD), or fully duplicated at a lower level. Record the reason in the task file.
- **Keep it fast.** Track the slowest tests (`--durations=10` in pytest; the runner's duration output elsewhere) and the total time. Investigate when the unit suite approaches 60 seconds.
- **Keep it deterministic.** A new flaky test is a defect to fix the day it is found. A test that passes only on retry is flaky.
- **Keep names meaningful.** A failure in CI should identify the behaviour without opening the file.
- **Remove dead tests of removed code.** Tests that no longer import anything real hide coverage gaps.
- **Update tests when specifications change.** If a requirement changes, update the criterion and the test together, and note the change in `Docs impact`. Do not edit a test to match code that disagrees with the specification; report it.
- **Snapshots:** review every changed snapshot as code. Updating snapshots (`--update-snapshots`, `-u`) rewrites baselines and needs user approval when it changes the contents of many files.

### Quarantine rules

Quarantine means keeping a flaky or blocked test out of the gating result for a limited time while its cause is fixed. It is a last resort, not a way to get green.

When it is allowed:

- The test is flaky (it fails intermittently on unchanged code) and the cause is not fixable within the task.
- It is blocked by an unavailable environment or an upstream defect that someone else owns.

When it is not allowed:

- The test fails deterministically. That is a real failure: report it as `fail`.
- The test fails because the change broke it. That is a defect in the change.
- Skipping would hide an acceptance criterion; the criterion becomes `not tested`, with the reason.

Procedure:

1. **Prove flakiness.** Show repeated runs with both outcomes (`--repeat-each` in Playwright, repeated runs elsewhere) and keep the trace or log.
2. **Ask the user before skipping.** Skipping an existing test is an action `AGENTS.md` reserves for user approval ("Never weaken, skip or delete an existing test without the user's approval"). State the test, the evidence, the risk (what is now unverified) and the plan to restore it.
3. **Quarantine visibly,** with a reason, a report reference, an owner and an expiry date. Use the runner's own mechanism so the test still shows in reports as skipped or expected-to-fail:
   - pytest: for a flaky test use `@pytest.mark.xfail(strict=False, reason="BUG-123 ...")`, which accepts either outcome and still reports it. For a test that fails every time because of a known open defect, `strict=True` is better: an unexpected pass fails the run and tells you the defect is fixed. Do not use `strict=True` on a flaky test, because its next lucky pass would fail the run. (Both forms executed with pytest 9.2.0.) Register custom markers and use `--strict-markers`.
   - Playwright: `test.fixme(...)` marks a test as to be fixed and skips it, or `test.skip(...)` with a condition; Playwright's flaky classification (`failed` then `passed` on retry) is the detection signal.
   - Vitest and Jest: `it.skip` / `test.skip` with a comment carrying the same reference, owner and expiry.
4. **Record it.** Put the entry in the task file, the coordinator records it in `docs/TASKS.md`, and a durable pitfall goes to `docs/MEMORY.md` (owner: coordinator).
5. **Keep it visible.** Report the number of quarantined tests in every test report until they are restored.
6. **Limit and expire.** Treat the quarantine list as debt: a short list with owners and dates. When the expiry passes, either fix the test, escalate to the user, or remove it with approval. Never extend an expiry silently.
7. **Restore.** After the fix, remove the marker, run the test with repeats (at least three, ten for known flakes) and confirm it passes consistently.

Never quarantine a test that guards a high-risk area (`AGENTS.md`) without telling the user that the area is now unverified.

### Routing to other skills

For finding why a test fails, load `debugging`. For test-first workflow, doubles and fixtures, load `test-driven-development`. For git branch and worktree policy beyond the scratch checkout above, load `git-version-control`.

## Examples

### Regression test with report reference (Vitest)

```ts
// tests/coupon.test.ts
import { it, expect } from 'vitest';
import { isCouponValid } from '../src/coupon';

// BUG-123: coupons expired one day early because the end date was compared at 00:00.
it('accepts a coupon until the last second of its end date (BUG-123)', () => {
  const coupon = { code: 'SAVE10', endsOn: '2026-11-30' };
  expect(isCouponValid(coupon, new Date('2026-11-30T23:59:59Z'))).toBe(true);
  expect(isCouponValid(coupon, new Date('2026-12-01T00:00:00Z'))).toBe(false);
});
```

Evidence recorded before and after the fix:

```text
Before fix: npx vitest run tests/coupon.test.ts
  FAIL accepts a coupon until the last second of its end date (BUG-123)
  AssertionError: expected false to be true
After fix:  npx vitest run tests/coupon.test.ts
  PASS 1 test
```

### Quarantine in pytest (executed with pytest 9.2.0)

```python
import pytest


# Known open defect, fails every time: strict, so a pass means the fix landed.
@pytest.mark.xfail(strict=True, reason="BUG-123: cents are dropped; owner: implementer")
def test_total_keeps_cents():
    assert round(2.675, 2) == 2.68


# Intermittent: non-strict, so either outcome is accepted but still reported.
@pytest.mark.xfail(strict=False, reason="BUG-456 flaky; owner: tester; expires 2026-12-15")
def test_refund_is_recorded_once():
    assert True  # stands in for the intermittent check
```

```text
$ python -m pytest -q -rxX
XFAIL tests/test_refunds.py::test_total_keeps_cents - BUG-123: cents are dropped; ...
XPASS tests/test_refunds.py::test_refund_is_recorded_once - BUG-456 flaky; ...
```

### Filled-in quarantine record (task file entry)

```text
Quarantined: e2e/checkout.spec.ts "declined card shows an error"
Evidence: failed 3 of 30 runs with --repeat-each 30; trace attached; passes alone
Cause (suspected): stub payment service answers before the page registers its handler
Approved by: user, 2026-11-26 (message reference in the task file)
Unverified while quarantined: declined-card error display (criterion 6)
Owner: tester. Expires: 2026-12-10. Restore: fix wait in fixture, run --repeat-each 10
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Writing a regression test after the fix and never seeing it fail | It may not detect the bug at all | Run it against the pre-fix code and record the failing output |
| Failing for the wrong reason (import error, typo) | The "failure" proves nothing | Confirm the assertion message matches the bug |
| Reproducing a bug at browser level when a unit test would do | Slow and flaky guard | Use the lowest level that shows the defect |
| Re-running only the changed file | Misses dependants and configuration effects | Select by blast radius and run the relevant suite at the end |
| Skipping a flaky test without asking | Violates the approval gate and hides risk | Get user approval; record owner and expiry |
| Quarantining a deterministic failure | A real defect is hidden | Report `fail` and send it back |
| Updating a snapshot or expectation to match new output | Regressions become accepted | Check the requirement; update only when the requirement changed |
| Keeping quarantined tests forever | The suite rots and areas stay unverified | Owners, expiry dates and a visible count |
| Deleting an old test to simplify the task | Loses a guard that may still matter | Ask the user; record the reason |

## Checklist

- [ ] The bug is described with input, expected result (from the requirement) and verbatim actual result.
- [ ] The regression test failed before the fix with the expected assertion message, and the output is recorded.
- [ ] The same test passes after the fix, and the output is recorded.
- [ ] The test sits at the lowest level that shows the defect and names the behaviour and report reference.
- [ ] Selected re-runs cover the change's blast radius, and the relevant full suite ran after the last source change.
- [ ] No existing test was weakened, skipped or deleted without user approval.
- [ ] Any quarantined test has proven flakiness, user approval, a reason, an owner and an expiry.
- [ ] The report lists quarantined tests and the criteria that are unverified because of them.
- [ ] Pre-existing failures are listed separately from failures caused by the change.

## Verify with context7 and gh_grep

- **context7:** confirm for the project's versions: "pytest `xfail` `strict` parameter and `--strict-markers`", "Playwright `test.fixme` and `test.skip`", "Vitest `--changed` and `it.skip`", "Jest `--onlyChanged`, `--changedSince` and `--findRelatedTests`", "pytest `--lf` and `--ff` cache behaviour".
- **gh_grep:** search literal code: `@pytest.mark.xfail(strict=True`, `test.fixme(`, `it.skip(`, `--changedSince`, `--only-changed`, `@regression`.

## Sources

- [Playwright: Test retries](https://playwright.dev/docs/test-retries), read 2026-11-26.
- [Playwright: Best Practices](https://playwright.dev/docs/best-practices), read 2026-11-26.
- [pytest: Good Integration Practices](https://docs.pytest.org/goodpractices.html), read 2026-11-26.
- [Jest: Configuration](https://jestjs.io/docs/configuration), read 2026-11-26.
- Runner flags were confirmed from `--help` of Vitest 5.1.2, Jest 30.5.2, pytest 9.2.0 and @playwright/test 1.65.1, and the `xfail(strict=True)` example was executed, on 2026-11-26. `test.fixme` behaviour was not executed here (unverified).
