---
name: testing-strategy
description: "Use when planning, writing or running tests: unit, integration, end-to-end, Playwright, regression and coverage."
---

# Testing Strategy

Produce the cheapest reliable evidence that behaviour meets the acceptance criteria. Pick the lowest test level that can fail for the right reason, and report what was actually run.

## When to use

- Mapping acceptance criteria to test cases and choosing unit, integration or end-to-end level.
- Writing or extending tests in the project's existing runner (Vitest, Jest, pytest, Playwright or equivalent).
- Running a suite, targeted tests or a browser check, and reporting results as evidence.
- Adding a regression test for a fixed bug, or deciding which tests to re-run after a change.
- Investigating a flaky test, or deciding whether a flaky test may be quarantined.
- Reading coverage reports, setting or judging thresholds, or finding untested behaviour.
- Reviewing whether a change's tests would fail if the behaviour broke (reviewer role).

## Do not use for

- Test-first cycle, test doubles, mocks, fakes, fixtures and factories: load `test-driven-development`.
- Security testing, penetration testing and threat modelling: load `security-engineering`.
- Finding the root cause of a failing test or unexplained behaviour: load `debugging`.
- Writing or sharpening acceptance criteria: load `requirements-engineering`.
- Wiring tests into CI/CD pipelines, environments and deployment: load `devops-deployment`.
- Reviewing code quality beyond test adequacy: load `code-review`.

## Research: context7 and gh_grep

- You MUST consult **context7** before you write, change or advise on any use of a test framework, runner, assertion library, coverage tool or browser-automation library. Check the project's manifest or lockfile first and query that version. Useful queries: "Playwright `expect.poll` and web-first assertions", "Vitest `coverage.thresholds` and `coverage.include`", "pytest `parametrize` and `tmp_path`", "Jest `coverageThreshold`", "Playwright `storageState` setup project".
- You MUST search **gh_grep** when a runner or plugin integration is unfamiliar, when the documentation is ambiguous, or when an error message is not explained by the docs. Search literal code. Useful searches: `storageState: 'playwright/.auth`, `coverage: { thresholds`, `@pytest.mark.parametrize(`, `PostgreSqlContainer(`, `testInfo.retry`.
- Pure project-internal assertions (a plain equality check on your own function) need neither. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/test-pyramid.md](references/test-pyramid.md) | Choosing the test level for a criterion, weighting effort by risk, or spotting a lopsided suite. |
| [references/unit-testing.md](references/unit-testing.md) | Writing or reviewing unit tests: scope, structure, naming, determinism, boundaries and error paths. |
| [references/integration-testing.md](references/integration-testing.md) | Testing across a boundary with real dependencies: databases, containers, HTTP contracts, isolation and cleanup. |
| [references/e2e-testing.md](references/e2e-testing.md) | Selecting critical user journeys, preparing environments and test data, or controlling flakiness. |
| [references/playwright.md](references/playwright.md) | Writing, running or debugging Playwright tests, auth state, traces, CI, or using the Playwright MCP against local or test environments. |
| [references/regression-testing.md](references/regression-testing.md) | Reproducing a bug before the fix, choosing which tests to re-run, maintaining the suite, or quarantining a flaky test. |
| [references/test-coverage.md](references/test-coverage.md) | Reading coverage, enabling branch coverage, setting thresholds or analysing gaps. |

## Workflow

1. **Map criteria.** List every acceptance criterion. For each, record test level, file and the observable result. If a criterion is untestable, ambiguous or contradicts an existing test, stop and escalate; do not guess intent.
2. **Learn the project.** Find the test commands in `AGENTS.md`, the manifest and the existing config. Reuse the existing runner, layout and naming. Adding a second runner or a new test dependency needs user approval (see Approval gates in `AGENTS.md`).
3. **Pick the level.** Choose the lowest level that gives reliable evidence (open `test-pyramid.md`). Pure logic goes to unit, cross-boundary behaviour to integration, and a full user flow to end-to-end only when the criterion is about that flow.
4. **Design cases.** For each criterion cover the success path, a boundary, invalid input, permission denied and a failure path. Weight the number of cases by risk. Derive expected values from the requirements, never from the implementation's output.
5. **Write deterministic, isolated tests.** Each test sets up and tears down its own data, names the behaviour it protects and asserts observable results. Follow the level's reference.
6. **Run narrow, then wide.** Run the new tests alone, then the affected area, then the relevant suite. Run new tests three consecutive times and in a different order from the file order. Capture the exact command and output of every failure.
7. **Classify failures.** Decide: product defect, test defect, environment problem or flaky. Report product defects with reproduction steps; do not fix production code. For an unexplained failure, load `debugging`.
8. **Check coverage as a gap finder.** Run coverage on the changed code, read uncovered branches, and add a test or justify the gap (open `test-coverage.md`). A number never replaces judgement.
9. **Report.** Fill the criterion-by-criterion table with `pass`, `fail` or `not tested` plus the reason.

### Differences by role

- **tester:** writes and runs tests, edits only test files, fixtures and test data, and never weakens, skips or deletes an existing test without user approval. Reports defects instead of fixing them.
- **reviewer:** does not edit anything. Judge adequacy: would each test fail if the behaviour broke, is every criterion covered, is anything flaky, order-dependent or asserting implementation detail? Run the existing tests when needed to confirm evidence, and report missing coverage as a finding with severity per `AGENTS.md`.

## Standards

- Every acceptance criterion maps to at least one test, and the mapping is recorded.
- Use the lowest test level that can fail for the right reason; add a higher level only for risk the lower level cannot see.
- Expected values come from requirements, not from running the code and pasting its output.
- Assert observable behaviour, not private methods, internal state or call counts, unless the call is the specified behaviour.
- No arbitrary sleeps, wall-clock dependence, order dependence, shared mutable state or live third-party calls.
- Retries never turn a red test green in the report: a test that passes only on retry is flaky and is reported as a defect.
- A bug fix includes a regression test that failed before the fix, with the failing output recorded.
- Never weaken, skip, quarantine or delete a test to make a task pass; quarantining needs user approval and a recorded owner and expiry.
- Browser tests run only against local or dedicated test environments with test data, never production or real accounts.
- Saved authentication state and test credentials are secrets: never commit, print or log them.
- Unit suites finish in under 60 seconds; justify and report any longer test.
- Coverage is a gap-finding tool; use branch coverage where the tool supports it and never exclude files merely to reach a threshold.
- Destructive or remote-writing steps (dropping or resetting databases, updating snapshots, deleting artefacts, pushing, publishing) need user approval first.
- Any source change invalidates earlier test results for the affected area; re-run before reporting.
- Report what was actually run. Never claim `pass` without command output.

## Verification

- [ ] Each acceptance criterion has a row in the evidence table with verdict, test name, command and output snippet.
- [ ] New tests pass alone and in the full suite: run the project test command with the new files, then the whole suite.
- [ ] New tests passed 3 consecutive runs (for example `npx playwright test --repeat-each 3`, or repeat the unit command three times).
- [ ] For a bug fix, the regression test was shown failing without the fix and passing with it.
- [ ] No test was skipped, weakened or deleted; `git diff` of test files shows no removed assertions.
- [ ] Coverage was run on changed code and every uncovered branch is tested or justified.
- [ ] Lint and build commands from `AGENTS.md` still pass, or the user accepted a named gap.
- [ ] No test contacts production, real accounts or live third parties.
- [ ] Pre-existing failures are listed separately from failures caused by the change.

## Output

Put in the standard report:

- **Evidence:** the criterion table (`pass`, `fail`, `not tested`, with reason), the exact commands run, results, and the flake check (three runs). Add coverage figures only as support, with the gaps you examined.
- **Research:** the context7 and gh_grep queries used (framework, version, question), or "none needed: project-internal logic".
- **Docs impact:** list each affected file and mark `updated` or `no change`.
  - `README.md` and `CHANGELOG.md` (owner: implementer): changed test commands, setup steps or documented behaviour.
  - `docs/PRD.md` (owner: architect): an acceptance criterion found untestable or ambiguous.
  - `docs/API-CONTRACTS.md` (owner: architect): a contract test exposed a mismatch with the code; report it, do not change either silently.
  - `docs/TASKS.md` and `docs/MEMORY.md` (owner: coordinator): task status, and durable pitfalls such as a quarantined flaky test or a required test environment.
  - `AGENTS.md` Commands line: changes go to the user first.
