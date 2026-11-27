# Test Coverage

What coverage does and does not tell you, branch coverage, thresholds and gap analysis for Vitest 5.1 (v8 provider), Jest 30.5, and pytest 9.2 with pytest-cov 7.1 and coverage.py 7.17 (checked 2026-11-26). The project's own configuration and agreed thresholds win.

## Contents

- Meaning and limits
- Kinds of coverage
- Enabling branch coverage
- Thresholds
- Gap analysis
- Reading and reporting coverage
- Routing to other skills

## Guidance

### Meaning and limits

Coverage records which code ran while the tests ran. It does not record whether anything was checked.

- High coverage with weak assertions proves nothing. A test that calls a function and asserts nothing yields full coverage of that function.
- Low coverage is a reliable signal: the uncovered code has no test exercising it, so changes there are unverified.
- Coverage cannot see missing code: an unhandled input, a forgotten error path or a requirement that was never implemented has no lines to cover.
- Coverage is silent about the quality of expected values, about concurrency, about integration wiring and about unreachable-in-test states.
- Coverage of a unit says nothing about whether acceptance criteria are met. Criteria mapping (see `test-pyramid.md`) is the primary measure; coverage is the check that you did not forget a branch.

So: use coverage to find gaps, never to declare correctness. The tester definition states the same rule: coverage numbers support judgement, they do not prove correctness.

### Kinds of coverage

| Kind | Question it answers | Notes |
|---|---|---|
| Line or statement | Did this line or statement run? | Weakest useful measure. Statements and lines differ when several statements share a line |
| Branch | Did each outcome of each decision (true and false, each case) run? | The most informative common measure; catches untested `else` and early returns |
| Function | Was this function called at least once? | Finds dead or untested functions; says nothing about paths inside |
| Condition or path | Did each sub-condition or each path run? | Not provided by these tools; reason about it in test design (see `test-driven-development`) |

A line can be covered while one of its branches is not: `if (a && b) return x;` is a covered line when only `a && b` true is tested, and the false outcome is a branch miss.

### Enabling branch coverage

Turn on and read branch coverage everywhere; do not rely on line coverage alone.

| Tool | How | Notes |
|---|---|---|
| Vitest 5.1 | Install `@vitest/coverage-v8` (or `@vitest/coverage-istanbul`), run `npx vitest run --coverage` | Branches are reported by default in the text table (`% Branch`). V8 is the default and recommended provider; it does not work on runtimes without V8, where Istanbul does |
| Jest 30.5 | `npx jest --coverage` | Default `coverageProvider` is `babel`; `v8` is available. Branches are reported in the text table |
| pytest with pytest-cov | `python -m pytest --cov=<package> --cov-branch --cov-report=term-missing` | `--cov-branch` enables branch coverage; the equivalent is `branch = true` under `[tool.coverage.run]` |

Vitest, from 3.2 on, uses AST-based remapping for V8 coverage so its reports match Istanbul's, according to the Vitest guide.

### Thresholds

A threshold is a guard against regression of coverage, not a quality target.

Rules:

- **Use the project's existing threshold.** Do not lower it to pass a task. Lowering a threshold or widening an exclusion is a quality-gate change; report it and ask the user.
- **Prefer branch thresholds** over line thresholds, and prefer per-file or per-directory thresholds on critical code over one global number that hides a gap behind averages.
- **Do not choose a magic number.** No universal percentage is right: the point is to prevent decline and to hold risky modules to a higher bar. If the project has none, propose one based on the current measured baseline (record the baseline, set the threshold at or just below it, raise it as tests are added) and ask before adding it to the configuration or CI.
- **Do not game it.** Never exclude files, add ignore comments or write assertion-free tests to move a number. An ignore comment needs a reason in the same line or the line above (unreachable defensive code, generated code, a platform-specific branch).
- **Make include rules explicit.** Vitest reports only files imported during the run unless `coverage.include` is set; set it (for example `src/**/*.ts`) so untested files appear as 0% instead of vanishing. Jest needs `collectCoverageFrom` for the same reason: files matching it get coverage data even when no test imports them.

Configuration forms (all verified against the stated versions or the version's documentation):

```ts
// vitest.config.ts (executed against Vitest 5.1.2)
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],      // show untested files as 0%
      reporter: ['text', 'lcov'],
      thresholds: { branches: 80, lines: 80, perFile: true },
    },
  },
});
```

```js
// jest.config.js (Jest 30.x; keys per the Jest configuration documentation)
module.exports = {
  collectCoverageFrom: ['src/**/*.{js,ts}', '!**/node_modules/**'],
  coverageProvider: 'v8',            // default is 'babel'
  coverageReporters: ['text', 'lcov'],
  coverageThreshold: {
    global: { branches: 80, lines: 80 },
    './src/payments/': { branches: 95 },   // a stricter bar for a critical directory
  },
};
```

```toml
# pyproject.toml (executed with pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.5)
[tool.coverage.run]
branch = true
source = ["shop"]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
```

In Jest a negative threshold number means "at most this many uncovered items" rather than a percentage. The command `python -m pytest --cov --cov-fail-under=90` fails the run when total coverage is below the number. Keep one source of truth for the number (the config file) and use the flag only if the project already does.

When a threshold fails, the runner exits non-zero even though every test passed. Report it as a coverage gate failure, with the file and metric named in the message (for Vitest: `Coverage for lines (75%) does not meet global threshold (80%) for src/price.ts`).

### Gap analysis

Run this on the code the change touched, not on the whole repository.

1. **Generate** a report with uncovered lines and branches: `--coverage` with the `text` and `lcov` or `html` reporters; `--cov-report=term-missing` in pytest.
2. **Narrow** to files in the diff. Coverage for unrelated files is noise; list them separately as follow-ups.
3. **Read each uncovered line or branch** and classify it:

| Class | Meaning | Action |
|---|---|---|
| Untested behaviour | A real path with no test | Write a test, derived from the requirement |
| Error or failure path | Catch block, invalid input, timeout mapping | Write a test that triggers it with a stand-in failure |
| Defensive code that cannot occur | Guard against an impossible state | Remove it with the implementer's agreement or mark it ignored with a reason |
| Dead code | Nothing can reach it | Report to the implementer for removal |
| Generated or boilerplate | Not authored logic | Exclude by configuration, with a note, only if the project agrees |
| Platform-specific | Runs only elsewhere | Cover on that platform or mark it ignored with a reason |

4. **Close or justify.** Each uncovered branch in changed code ends as a test, a reported follow-up or a justified ignore. Do not leave it unexplained.
5. **Check that the new tests can fail.** For a new test covering a branch, change the condition in a scratch copy or reason through it: if the test still passes with the branch inverted, it covers the line without checking the behaviour (see `unit-testing.md`).
6. **Report** the files examined, the uncovered items and the decision for each.

Diff-focused coverage, meaning coverage computed only for changed lines, is the most useful view on a pull request. Use the project's tool for it if one exists; otherwise read the full report filtered to the changed files, as above.

### Reading and reporting coverage

- State the command, the tool and version, the provider (v8 or Istanbul/Babel) and the figures (statements, branches, functions, lines) in `Evidence`.
- Report the uncovered items you examined, not only the headline percentage.
- Never write "coverage is 92%, so it works". Write which criteria are covered by which tests, and use coverage as the supporting statement.
- Coverage varies by provider and by what is included. Do not compare numbers across tools or after changing `include` or `exclude`.
- Coverage runs slower than plain tests. Run it on the targeted files while developing and on the relevant suite before reporting; do not make the fast unit loop depend on it unless the project does.
- Coverage output directories (`coverage/`, `htmlcov/`, `.coverage`) are generated artefacts: they belong in `.gitignore`, not in the repository.
- Ignore hints are provider-specific: `v8 ignore` comments for V8 coverage, `istanbul ignore` for Istanbul, and for TypeScript the Vitest guide notes that esbuild needs the `@preserve` marker for the comment to survive. For coverage.py the usual hint is a `# pragma: no cover` comment (unverified in this session; confirm with context7).
- Mutation testing (for example Stryker for JavaScript or mutmut for Python) measures whether tests fail when code is changed and addresses the weakness of coverage; it is slow and optional, and adding it is a dependency change needing user approval (unverified current versions).

### Routing to other skills

For test design that reaches branch and condition completeness, load `test-driven-development`. For wiring coverage gates into CI, load `devops-deployment`. For reviewing code beyond test adequacy, load `code-review`.

## Examples

### Bad to good: coverage without a check

Bad: 100% line coverage, no assertion. This passes even if `discount` returns the wrong value.

```ts
it('runs discount', () => {
  discount(100, 'SAVE10');
});
```

Good: the same coverage with an assertion from the requirement.

```ts
it('gives 10 percent off with SAVE10', () => {
  expect(discount(100, 'SAVE10')).toBe(90);
});
```

### Reading a Vitest report (output produced by the run above)

```text
File      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
price.ts  |   83.33 |      100 |      50 |      75 | 6
ERROR: Coverage for lines (75%) does not meet global threshold (80%) for src/price.ts
```

Analysis: line 6 is `unused()`, a function nothing calls. Branch coverage is 100%, so every decision in `discount` ran. Decision: report `unused()` to the implementer as dead code (class "dead code"); do not write a test for it and do not lower the threshold.

### Filled-in gap analysis entry (for the report)

```text
Changed file: src/refunds.ts
Command: python -m pytest tests/test_refunds.py --cov=shop --cov-branch --cov-report=term-missing
Result: statements 94%, branches 88%
Uncovered: lines 41-43 (except TimeoutError branch), line 57 (partial refund when amount > balance)
Decisions:
  - 41-43: untested error path -> added test_refund_maps_gateway_timeout_to_502 (criterion 5)
  - 57: untested behaviour -> added test_partial_refund_rejects_amount_over_balance (criterion 3)
After: branches 100% for src/refunds.ts; both new tests fail when the condition is inverted
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Treating a percentage as proof of correctness | Assertion-free tests also reach 100% | Map criteria to tests; use coverage to find gaps |
| Line coverage only | Misses untested `else` and early returns | Enable and read branch coverage |
| One global threshold | An average hides an untested critical module | Per-file or per-directory thresholds on critical code |
| Lowering the threshold or excluding files to pass | Hides risk and breaks the quality gate | Write the missing test or justify and report the gap |
| Adding tests only to raise the number | Low-value tests, false confidence | Gap analysis; tests derived from requirements |
| Vitest or Jest without include rules | Untested files do not appear | Set `coverage.include` or `collectCoverageFrom` |
| Comparing numbers across providers or configs | Misleading trends | Compare like with like; record the provider and include rules |
| Ignore comments without a reason | Unreviewable blind spots | Reason in the comment; review ignores in the diff |
| Committing coverage output | Noise and merge conflicts | Git-ignore generated reports |

## Checklist

- [ ] Branch coverage was enabled and read, not only line coverage.
- [ ] The report states tool, version, provider, command and all four metrics.
- [ ] Coverage was examined for the changed files, and every uncovered branch there is tested, reported or justified.
- [ ] Each new test that covers a branch fails when that branch's condition is inverted.
- [ ] No threshold was lowered, no file excluded and no ignore comment added merely to pass.
- [ ] Include rules list the source directories so untested files are visible.
- [ ] Critical modules have a threshold that is at least as strict as the global one, if the project uses thresholds.
- [ ] Coverage figures are presented as support for the criteria table, not as proof.
- [ ] Generated coverage output is git-ignored.

## Verify with context7 and gh_grep

- **context7:** check for the project's versions: "Vitest `coverage.thresholds`, `coverage.include` and `perFile`", "Vitest coverage providers v8 and istanbul", "Jest `coverageThreshold`, `collectCoverageFrom` and `coverageProvider`", "pytest-cov `--cov-branch`, `--cov-report` and `--cov-fail-under`", "coverage.py `fail_under`, `branch` and exclude lines".
- **gh_grep:** search literal code: `thresholds: {` with `perFile`, `coverageThreshold: {`, `collectCoverageFrom:`, `--cov-branch`, `fail_under =`, `branch = true`, `v8 ignore next`.

## Sources

- [Vitest: Coverage guide](https://vitest.dev/guide/coverage), read 2026-11-26.
- [Jest: Configuration](https://jestjs.io/docs/configuration), read 2026-11-26.
- [pytest-cov: Configuration](https://pytest-cov.readthedocs.io/en/stable/config.html), read 2026-11-26.
- Vitest thresholds and the pytest-cov and coverage.py configuration were executed on Vitest 5.1.2, pytest 9.2.0, pytest-cov 7.1.0 and coverage 7.17.5 on 2026-11-26; the Jest configuration was read from the documentation and not executed.
