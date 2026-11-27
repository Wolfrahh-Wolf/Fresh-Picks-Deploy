# TDD Workflow Across Tester and Implementer

How to apply test-first work to features and bug fixes in RelayCrew, including who writes what, what the handoff contains, and how the evidence is recorded. Consistent with `AGENTS.md` (roles, handoff, quality gates, approval gates); framework examples checked against Jest 29.7, Vitest 3 and pytest 8 on 2026-11-26. The project's own conventions win.

## Contents

- Decide whether and how to go test-first
- Entry checks
- Mode A: tester writes the red tests, implementer makes them green
- Mode B: implementer writes tests and code, tester verifies independently
- Feature workflow
- Bug-fix workflow
- The handoff contents
- Recording evidence
- Failure loops and escalation
- Keeping the criteria honest

## Guidance

### Decide whether and how to go test-first

The coordinator decides, and the brief says so. If the brief is silent, use this table.

| Work | Default | Mode |
|---|---|---|
| New behaviour with clear acceptance criteria | Test-first | A if a tester is in the plan, otherwise B |
| Bug with a known reproduction | Test-first (regression test red before the fix) | A or B |
| Bug with unknown cause | Reproduce and find the cause first (`debugging`), then test-first for the fix | A or B |
| Refactoring | Existing tests are the net; add characterization tests first if there are none | B |
| High-risk area (authentication, payments, personal data, migrations) | Test-first, tester involved, security-auditor reviews separately | A |
| One-line trivial edit | Not required | none |
| UI styling, pure configuration | Not test-first; test behaviour after | none |

Say in one line which mode applies. If test-first is requested but impossible (the criterion cannot be tested, the environment is missing), do not guess: escalate with the specific reason.

### Entry checks

Do these before the first test, whichever role you play.

1. Read the brief, the acceptance criteria and the task file. If a criterion is ambiguous, contradictory or untestable, stop and escalate. The ambiguity belongs to the architect; for how criteria should be written, load `requirements-engineering`.
2. Find the project's test commands and runner in `AGENTS.md` and the manifest. Confirm the runner version and the mocking APIs with context7.
3. Read one nearby test file for naming, layout and helper conventions. Match them.
4. Run the relevant suite and record the baseline, including pre-existing failures.
5. Build the test list: every criterion mapped to one or more behaviours, with error, boundary and permission cases included. Record the test type and the file each will live in.

### Mode A: tester writes the red tests, implementer makes them green

Use when a tester is in the plan and independence matters.

**Tester:**

1. Derive expectations from the criteria and requirements only. Do not read the implementation to decide what a correct answer is; there may not be one yet.
2. Write the failing tests for the agreed list, in the project's test directories. Edit only test files, fixtures and test data.
3. Run them. Each must fail for the intended reason. A test failing on an import or setup error is not ready.
4. Provide the handoff (below): the test files, the command, the red output and the criterion map.
5. After the implementer reports green, rerun the tests, add missing cases (extra boundaries, error paths, anything the criteria imply), and run everything in isolation and three times in a row.
6. Report the criterion-by-criterion table.

**Implementer:**

1. Start from the tester's red tests. Run them and confirm they fail as described.
2. Make them pass one at a time, using the cycle in [red-green-refactor.md](red-green-refactor.md): smallest change, run, continue.
3. Do not edit the tester's tests. If one looks wrong, stop and report which test, what it asserts and why it seems to contradict the criterion. The coordinator routes it back to the tester or architect.
4. If an extra test is needed for code you add (a private branch, a new edge), add it as a clearly separate test and say so in the report.
5. Run tests, lint, type-check and build with the exact commands in `AGENTS.md`.

### Mode B: implementer writes tests and code, tester verifies independently

Use when there is no separate tester stage first, or the brief says the implementer works test-first.

**Implementer:**

1. Run the cycle yourself for each list item. Record the red and green output for each.
2. Keep tests behaviour-focused and in the project's conventions.
3. Report the test list with done and remaining items.

**Tester (afterwards):**

1. Do not trust the implementer's tests as proof. Map each criterion to a test independently.
2. Check that each test fails when the behaviour is broken: temporarily break the code or revert the change and confirm.
3. Add missing cases. Report defects in production code; do not fix them.
4. Report the criterion table with `pass`, `fail` or `not tested` and reasons.

In both modes the reviewer (and the security-auditor on high-risk changes) judge the change independently. The implementer never states that its own work is reviewed.

### Feature workflow

1. Entry checks and the test list.
2. Take the simplest item. Red, green, refactor.
3. After each green, run the area suite, not only the new test.
4. Continue down the list. Add discoveries to the list; do not detour.
5. When the list is empty, check the criteria one by one against evidence: each criterion has a passing test you saw fail first.
6. Run the broader suite, lint, type-check and build.
7. Sync documentation: report test command changes and spec impact in `Docs impact`.

Keep each cycle small enough that the diff for one item can be understood alone. If the plan has more than about a dozen tasks, or one task needs many criteria, tell the coordinator; splitting is the architect's job (`product-technical-planning`).

### Bug-fix workflow

1. **Reproduce.** Get the exact steps, inputs and error from the report. If you cannot reproduce it, you do not have a bug to fix yet; load `debugging`.
2. **Write the regression test** at the lowest level that shows the bug, using the reported input. It describes the correct behaviour, not the bug.
3. **Red.** Run it against the current code. The failure must match the reported symptom. Record the output.
4. **Fix** with the smallest change that addresses the cause, not only the symptom. Re-run: green.
5. **Prove the test guards the fix.** Revert only the production change, run the test, confirm it fails, then restore. Record both results.
6. **Look for siblings.** If the same defect pattern likely exists in similar code, report it as a follow-up; do not widen scope without approval.
7. **Run the area suite**, lint and type-check.

A regression test never replaces an existing test. If the fix changes behaviour that an existing test asserts, that test either encoded the bug or contradicts the new requirement: report it with the test name and file. Do not edit or delete it without the user's approval.

### The handoff contents

Every delegation follows the standard brief in `AGENTS.md`. For test-first work, the tester's handoff to the coordinator (for the implementer) includes at least:

- **Goal:** the single outcome the tests express.
- **Test files and names:** exact paths and the test names.
- **Command:** the exact command to run just these tests, and the area suite command.
- **Red evidence:** the failing output for each test, trimmed to the relevant lines.
- **Criterion map:** which test covers which criterion.
- **Doubles and fixtures:** what is faked and where the helpers live, so the implementer does not duplicate them.
- **Out of scope:** what the tests deliberately do not cover.

The implementer's report back includes the green output, the commands, any test it believes is wrong (with reasoning) and any behaviour it added beyond the tests (with a test).

### Recording evidence

Keep evidence short and checkable: command and result, not prose.

```text
Behaviour: non-members at exactly the threshold pay nothing  (criterion 3)
Red:   npm test -- shipping -t "exactly the threshold"
       FAIL  Expected: 0  Received: 500
Green: npm test -- shipping
       PASS  3 tests
Guard: reverted shipping.ts change -> FAIL (Expected: 0 Received: 500); restored -> PASS
Runs:  3 consecutive passes, test file run alone: pass
```

The tester's criterion table follows the report format:

| # | Criterion | Verdict | Test | Evidence |
|---|---|---|---|---|
| 1 | Members never pay shipping | pass | shipping.test.ts "members never pay shipping" | PASS, red seen first |
| 3 | Exactly 5000 cents ships free | pass | shipping.test.ts "exactly the threshold" | PASS, guard checked |
| 5 | Negative total rejected | not tested | none | Criterion ambiguous: error type unspecified; escalated |

Report only what you ran. If a command could not run, say so and why.

### Failure loops and escalation

| Situation | Who | Action |
|---|---|---|
| Same failure after 2 distinct fix attempts | implementer | Revert to last green, stop, escalate with the error output and what you tried |
| Test is flaky (passes and fails without a code change) | tester or implementer | Treat as a defect: report it, find the shared state, timing or randomness cause; never retry until green |
| Existing test contradicts a new requirement | any | Report test name, file and the contradiction; do not edit it without user approval |
| Criterion untestable or ambiguous | tester or implementer | Escalate to the coordinator and architect with the quoted criterion and a proposed measurable version |
| Required service or database unavailable | tester | Check config, retry once, then escalate with the exact error |
| Test needs production access or real data | any | Stop; escalate. Never use production or real accounts |
| Test execution is far too slow | tester | Move the check down a level or fake the slow boundary; for level choice load `testing-strategy`; justify any unit test above 60 seconds |
| The tests pass but you doubt them | any | Break the code on purpose; if nothing fails, the tests are weak |

After 2 failed fix-and-verify loops on the same task the coordinator stops, marks the task blocked and gives the user the options. Any source change invalidates earlier test, review and audit results for the affected area; rerun them.

Do not run destructive commands (dropping databases, deleting data) as part of test setup against anything but a disposable test environment. Cleanup helpers delete only what the test created, in temporary locations.

### Keeping the criteria honest

- Tests express criteria; they do not replace them. If a test needs behaviour the criteria do not state, ask for it rather than inventing it.
- Every assertion traces to a criterion or a named risk. Remove "while I'm here" assertions.
- Never copy the output of the code under test into the expected value. Compute it by hand or from the rule.
- Do not mark a criterion `pass` because the implementer's own tests pass. Pass means you saw the criterion verified by a test that can fail.

## Examples

### Delegation from the coordinator to the tester (Mode A)

```text
Goal: Write failing tests for password-reset throttling
Task file: .agents/tasks/password-reset-throttle.md
Context: FR-012, FR-015. Existing tests in tests/auth/*.test.ts use Jest 29 and a fake clock helper
  in tests/helpers/clock.ts. Email provider is faked in tests/helpers/mailer.ts.
Scope: test files and fixtures only
Out of scope: production code, load testing
Acceptance criteria:
  - [ ] (FR-012) First request for a registered address sends exactly one email
  - [ ] (FR-015) A second request within 60 seconds for the same address sends no second email
  - [ ] (FR-015) A request 61 seconds after the first sends a second email
Skills: test-driven-development
Research: use context7 and gh_grep as required by AGENTS.md
Return: the standard report with red output for each test
```

### Tester report with red evidence

```text
Status: done
Summary: 3 tests written, all red for the intended reason. Mode A: handing to implementer.
Changes: tests/auth/reset-throttle.test.ts (new)
Evidence:
  npm test -- reset-throttle
  FAIL "second request within 60 seconds sends no second email"
    Expected: 1  Received: 2   (mailer.sent.length)
  FAIL "request after 61 seconds sends a second email"  Expected: 2  Received: 1
  FAIL "first request sends one email"  Expected: 1  Received: 0  (route not implemented)
Research: context7 jest 29 fake timers (useFakeTimers, advanceTimersByTime); gh_grep not needed.
Docs impact: none
Open questions: Is 60 seconds measured from the first request or from the last allowed send? Default: last send.
```

### Implementer report back

```text
Status: done
Summary: all 3 tests green; implemented throttle in src/auth/reset.ts. No test edited.
Changes: src/auth/reset.ts
Evidence: npm test -- reset-throttle -> PASS 3 tests; npm test -> PASS (142 + 3); lint, tsc, build: pass
Research: context7 jest 29 (fake timers confirmed in tester report); none further.
Docs impact: README unchanged; FR-015 interval to be confirmed for docs/PRD.md (architect)
Open questions: none
```

### Regression test in a bug fix

```python
# tests/test_invoice.py
from invoice import format_total

def test_total_uses_two_decimals_for_whole_amounts():
    # Reported bug: 12 shown as "12" instead of "12.00"
    assert format_total(12) == "12.00"
```

Red: `AssertionError: assert '12' == '12.00'`. Fix, green. Guard: revert only `invoice.py`, the test fails with the same message; restore.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Implementer edits the tester's test to get green | Hides a defect and breaks independence | Report the suspected wrong test to the coordinator |
| Tester reads the implementation to decide expected values | Tests then prove the code does what it does | Derive expectations from the criteria |
| Handing over red tests without the red output | The implementer cannot tell if they fail for the right reason | Include command and failing message per test |
| Treating the implementer's tests as independent verification | The author tests what they built | Tester maps criteria independently and checks tests can fail |
| Fixing the bug before the regression test exists | The test is never seen to fail | Reproduce as a failing test first |
| Retrying a flaky test until it passes | The defect stays and recurs | Find the shared state, timing or randomness cause |
| Adding behaviour with no test | Untested code reaches review | Add a test first or remove the behaviour |
| Wide cycles covering a whole feature at once | Slow feedback and vague failures | One behaviour per cycle |
| Declaring a criterion passed without running it | A claim without evidence | Record the command and result |
| Using production data or accounts in tests | Safety and privacy breach | Use test data in local or dedicated test environments |

## Checklist

- [ ] The mode (A, B or none) is stated and matches the brief.
- [ ] Every criterion is mapped to at least one test, with its type and file recorded.
- [ ] A baseline run was recorded before any change.
- [ ] Every behaviour has recorded red output that fails for the intended reason.
- [ ] The handoff includes files, commands, red evidence, criterion map and the doubles in use.
- [ ] The implementer did not edit, skip, weaken or delete any test.
- [ ] Each bug fix has a regression test shown to fail without the fix and pass with it.
- [ ] New tests pass in isolation and in three consecutive runs.
- [ ] Failures after 2 attempts, flaky tests and contradictions were escalated, not worked around.
- [ ] Test commands or setup changes are named in `Docs impact`.
- [ ] No test touched production systems or real accounts.

## Verify with context7 and gh_grep

- **context7:** before writing the handoff, confirm the project's runner and its filtering syntax for single tests, for example "jest 29 run a single test -t testNamePattern", "vitest run filter by test name", "pytest -k expression selecting tests" and the timer or mock APIs used (see [mocking-fixtures.md](mocking-fixtures.md)). Use the version from the lockfile.
- **gh_grep:** search literal code for how maintained projects structure regression tests and helpers, for example `regression`, `describe("bug`, `test_regression`, `# Reported bug`, `fixtures/` helper layouts. Treat results as examples of practice, not as a convention to adopt without checking the project's own.

## Sources

- Jest, The Jest Object (version 29.7 page read): https://jestjs.io/docs/29.7/jest-object
- Vitest, Mocking guide (read): https://vitest.dev/guide/mocking.md
- pytest, How to monkeypatch/mock modules and environments (read): https://docs.pytest.org/monkeypatch.html
- Python documentation, unittest.mock (read): https://docs.python.org/3/library/unittest.mock.html
