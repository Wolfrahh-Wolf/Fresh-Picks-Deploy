---
name: test-driven-development
description: "Use when working test-first, designing test cases, or creating mocks, stubs, fakes and fixtures."
---

# Test Driven Development

Drive behaviour through small failing tests, make them pass with the least code, then clean up while the tests stay green. Keep the test code itself small, deterministic and cheap to maintain.

## When to use

- The brief asks for test-first work, or you are about to write a test before the code it covers.
- A bug needs a regression test that fails before the fix and passes after it.
- You must turn acceptance criteria into concrete test cases (inputs, boundaries, states, error paths).
- You are creating or reviewing a mock, stub, spy, fake, fixture, factory, fake clock or seeded random source.
- Tests are brittle, slow, order-dependent or break on harmless refactors, and the cause looks like over-mocking or shared fixtures.
- A rule has many input combinations and you need a systematic way to choose cases, including property-based tests.

## Do not use for

- Test levels, the test pyramid, coverage targets, integration and end-to-end tests, Playwright: load `testing-strategy`.
- Security testing and abuse cases: load `security-engineering`.
- Writing or fixing the acceptance criteria themselves: load `requirements-engineering`.
- Breaking work into tasks or sequencing it: load `product-technical-planning`.
- Finding the root cause of a failure you cannot explain: load `debugging`.
- Procedures for a whole feature, bug-fix or refactor: load `sdlc-workflows`.

## Research: context7 and gh_grep

- You MUST consult **context7** before using any mocking, timer, fixture or property-testing API of the project's test framework. Read the manifest or lockfile first and query that exact major version, because reset and restore behaviour changes between majors. Useful queries: `jest 29 useFakeTimers setSystemTime`, `vitest vi.mock factory importOriginal hoisting`, `pytest monkeypatch setattr raising`, `unittest.mock create_autospec patch where to patch`, `hypothesis given strategies settings`.
- You MUST search **gh_grep** when a pattern is unfamiliar, the framework docs are ambiguous, or a mock behaves unexpectedly. Search literal code. Useful searches: `vi.useFakeTimers()`, `jest.spyOn(`, `monkeypatch.setattr(`, `@pytest.fixture(autouse=True)`, `create_autospec(`, `fc.assert(fc.property(`.
- Neither is needed for pure test-design reasoning (choosing cases from criteria) or for the cycle itself. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/red-green-refactor.md](references/red-green-refactor.md) | You are running or checking the cycle: step size, what counts as a valid red, minimal green, safe refactoring, violations. |
| [references/tdd-workflow.md](references/tdd-workflow.md) | You are applying TDD to a feature or a bug, or handing work between tester and implementer. |
| [references/test-design.md](references/test-design.md) | You must choose test cases: equivalence classes, boundaries, state transitions, decision tables or property-based tests. |
| [references/mocking-fixtures.md](references/mocking-fixtures.md) | You are deciding what to double, writing a mock, stub or fake, building fixtures or factories, or controlling clocks and randomness. |

## Workflow

Use the project's existing test runner, assertion style and folder layout. Never add a second runner or assertion library without approval.

1. **Orient.** Read the brief, the acceptance criteria and the project's test commands in `AGENTS.md`. Look at one existing test next to the code you will touch and copy its conventions.
2. **Baseline.** Run the relevant tests before changing anything. Record pre-existing failures so you never chase one you did not cause.
3. **Make a test list.** Map each acceptance criterion to one or more small behaviours. Order them simplest first, and include error, boundary and permission cases from the start. Open the test-design reference when the rule has many cases.
4. **Red.** Write one test for one behaviour. Run it. Confirm it fails with an assertion about the missing behaviour, not a syntax error, import error or wrong setup. Record the failing output.
5. **Green.** Write the least production code that passes this test and every earlier test. Run the suite for the area. Do not add behaviour that no test demands.
6. **Refactor.** With everything green, remove duplication and improve names in production and test code. Run the tests after each small step. Never change behaviour and tests in the same step.
7. **Repeat** from step 4 for the next item on the list. Add newly discovered cases to the list instead of detouring.
8. **Bugs.** Write a test that reproduces the bug and fails for the reported reason, then fix. Prove the test fails without the fix. If the cause is unknown, load `debugging` first.
9. **Doubles.** Use the real collaborator when it is fast and deterministic. Replace only slow, non-deterministic or external boundaries, and prefer a fake or stub over a mock that asserts calls.
10. **Close.** Run the full relevant suite, lint and type-check using the commands in `AGENTS.md`. Run each new test in isolation and three consecutive times to expose flakiness.

### Differences by role

| Step | tester | implementer |
|---|---|---|
| Test-first request | Writes the failing tests from the criteria, derived from requirements and not from the implementation, and records the red output. | Writes its own failing tests only when the brief says test-first; otherwise receives the tester's red tests. |
| Green | Does not change production code. Reports a defect instead. | Makes the tests pass with the smallest change. |
| Tests that look wrong | Fixes them, or escalates if the criteria are unclear. | Never edits, skips, weakens or deletes a test to pass. Reports the concern to the coordinator. |
| Failure loop | Reports a flaky test as a defect and does not retry until green. | Gets 2 fix attempts on the same failure, then escalates. |
| Evidence | Criterion-by-criterion table: pass, fail or not tested. | Red output, green output, and the commands run. |

## Standards

- Every new behaviour starts with a failing test that was run and seen to fail for the expected reason.
- A test that passes the first time it is run is treated as suspect until shown to fail against broken code.
- Each test checks one behaviour and is named so its failure message explains what broke.
- Assert observable behaviour, never private methods, internal variable names or call counts, unless the interaction is the specified behaviour.
- Tests are independent, order-free and share no mutable state; each builds and cleans up its own data.
- No arbitrary sleeps, live network calls, real clocks or unseeded randomness in tests; inject or fake them.
- Expected values come from criteria or hand calculation, never copied from the output of the code under test.
- Mock only boundaries you own the contract for; do not mock the unit under test, pure functions or value objects.
- A double that stands in for real code is bound to the real signature (autospec, typed interface or shared contract check).
- Restore every patch, spy, fake timer and environment change automatically, using the framework's mechanism, not by remembering.
- A bug fix includes a regression test that fails without the fix.
- Never weaken, skip, delete or loosen an assertion to make a task pass.
- Property-based tests record their seed or failing example so a failure can be replayed.
- Refactoring changes structure only; the tests are not edited while refactoring production code.
- Existing project test conventions win over these defaults, except where they are unsafe; then report it.
- Tests run only against local or dedicated test environments with test data, never production.

## Verification

- [ ] Each new test was run red first and the failure message names the missing behaviour; the output is recorded.
- [ ] Run the targeted tests, then the area suite, using the project's test command from `AGENTS.md`; all pass.
- [ ] Run each new test file alone and again three times in a row; results are identical.
- [ ] Temporarily break the code under test (or revert the fix) and confirm the new test fails; restore it.
- [ ] Search the new tests for sleeps and real clocks: `grep -nE "sleep\(|setTimeout\(|Date\.now\(|new Date\(\)|time\.sleep|datetime\.now\(" <test paths>` (PowerShell: `Select-String -Path <test paths> -Pattern 'sleep\(|Date\.now|time\.sleep'`) and justify each hit.
- [ ] Confirm every mock, spy and patch is restored automatically (config option, hook or fixture teardown).
- [ ] Confirm each assertion traces to a criterion or named risk.
- [ ] Confirm no existing test was skipped, weakened or deleted.

## Output

Return the standard report. Add skill-specific content as follows.

- **Evidence:** for test-first work, the red run (command and failing message) and the green run (command and result) for each behaviour; the isolation and three-run results; for the tester, the criterion-by-criterion table with test name, command and output snippet.
- **Research:** the context7 queries (framework and version confirmed) and gh_grep searches used, or "none needed: test design reasoning only".
- **Docs impact:** changes to test commands, setup, fixtures location or documented behaviour go to `README.md` (owner: implementer). Behaviour that departs from a specification is reported for `docs/PRD.md`, `docs/API-CONTRACTS.md` or `docs/DB.md` (owner: architect). Test-related pitfalls worth remembering are proposed to the coordinator for `docs/MEMORY.md`; the coordinator updates `docs/TASKS.md`.
- **Summary additions:** the test list (done and remaining), which doubles were used and why, any criterion that could not be made testable, and any flaky test found.
- **Open questions:** criteria that are ambiguous or untestable, each with a proposed default.
