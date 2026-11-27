# Bug Fixing

The playbook for fixing a defect: reproduce, diagnose, fix, add a regression test, verify, review and document; language-neutral with JavaScript-style test illustrations, written against the RelayCrew `AGENTS.md` roles and templates; checked 2026-11-27.

## Contents

- Principles of the playbook
- The stage table
- Stage details and briefs
- Choosing the route: known cause or unknown cause
- Bug classes and what changes for each
- Mitigation versus fix
- Failure handling and the loop limit
- The post-fix record

## Guidance

### Principles of the playbook

1. **Reproduce first.** A fix without a reproduction cannot be shown to work. If the bug cannot be reproduced, the next step is more information, not a guess.
2. **Cause before cure.** The fix targets the proven cause, not the visible symptom. Root-cause technique belongs to `debugging`; this playbook only decides when it runs and what the orchestrator accepts as proof.
3. **A test that fails first.** The regression test must fail before the fix and pass after it. A test that has never failed has not shown it can detect the bug.
4. **Smallest correct change.** The fix is scoped to the cause. Cleanups, renames and other defects found on the way become follow-ups (`AGENTS.md`, Safety).
5. **Specifications describe intent.** If the "bug" is that code disagrees with a specification, ask which is right before changing either (`AGENTS.md`, Source of truth).

Rules owned by `AGENTS.md` are not repeated here: triage classes, the brief and report formats, the quality gates and loop limit, approval gates and documentation sync.

### The stage table

| # | Stage | Who | Input | Output | Exit check |
|---|---|---|---|---|---|
| 0 | Intake | orchestrator | Report from user, log, ticket | Symptom, expected versus actual, verbatim error, environment, version, frequency; class and risk in one line | Enough information to attempt a reproduction, or questions asked once |
| 1 | Reproduce | debugger (unknown cause) or tester (known cause) | Intake facts | A command or steps that show the failure, with its verbatim output | The failure reproduces on demand, or the intermittent rate is measured and recorded |
| 2 | Diagnose | debugger | Reproduction | Root cause with evidence: file and line, causal chain, trigger versus cause versus contributing factor | The report proves the cause (a check that would have disproved it was run), not only correlates |
| 3 | Decide scope | orchestrator | Diagnosis | Fix scope, same-pattern occurrences listed, spec question if intent is unclear | Scope agrees with the acceptance criteria; user answered any spec question |
| 4 | Regression test | tester (test-first) or implementer | Reproduction, scope | A test that fails now for the diagnosed reason | Failing run recorded; failure message names the bug, not a setup error |
| 5 | Fix | implementer | Diagnosis, failing test | Smallest change, baseline and after results, self-review | Regression test passes; all four checks from `AGENTS.md` pass; no unrelated diff |
| 6 | Verify | tester | Requirements and changed files | Original reproduction passes, regression test passes, neighbouring behaviour intact | Evidence per criterion |
| 7 | Review | reviewer, plus security-auditor for high risk | Requirements and changed files | Findings by severity | No `critical` or `high` open |
| 8 | Document | implementer, architect, orchestrator | Final diff, diagnosis | CHANGELOG entry, README or spec updates, memory entry | Documentation sync table complete |
| 9 | Close | orchestrator | All reports | Final report with the post-fix record | Quality gates met |

### Stage details and briefs

**0 Intake.** Capture, without interpretation: what the user did, what happened, what they expected, the exact error text, environment and version, how often. Ask all missing questions together. Apply `AGENTS.md` (Triage): a failure of unknown cause is routed through the debugger; a bug whose cause the user or a failing test already identifies is a Standard task. If the bug touches the high-risk list (for example an authorisation bypass or leaked personal data), raise the risk, and treat the details as sensitive: do not paste exploit details into public places, and let the security-auditor see it before the fix is described broadly.

**1 Reproduce.** For an unknown cause, brief the debugger with the symptom, verbatim errors and paths; the debugger edits nothing and returns a minimal reproduction (skill `debugging`, reference on bug reproduction). For a known cause, the tester writes the failing test directly. Exit check: a command the orchestrator can rerun, and its failing output saved in the task's Evidence. If the bug cannot be reproduced after a reasonable attempt, mark the task `blocked` and ask the user for the missing input; do not ship a speculative fix.

**2 Diagnose.** The debugger returns the root cause with evidence. The orchestrator checks four things: the cause is tied to code (file and line); the causal chain explains every observed symptom; a hypothesis that would contradict it was tested; and trigger, cause and contributing factors are distinguished. A report that says "likely" with no test is incomplete: ask once for the missing evidence, then escalate per `AGENTS.md`.

**3 Decide scope.** Choose what this fix changes. Search for other places that use the same faulty pattern. They are listed as follow-ups unless the user wants them in scope, because unrelated fixes bypass review. If the diagnosis shows the specification itself is wrong or silent, ask the user which behaviour is correct, and record the answer.

**4 Regression test.** Test-first is the default for bugs: ask the tester for the failing test before the implementer starts (skill `test-driven-development`). The test asserts the correct observable behaviour (not the old implementation), uses the smallest input that triggers the bug, and fails for the diagnosed reason. Record the failing output. A test that fails because of a typo or missing fixture proves nothing.

**5 Fix.** The implementer works from the diagnosis, records the baseline first, changes the smallest amount of code that addresses the cause, and runs test, lint, type-check and build with the commands in `AGENTS.md`. Skills: `languages-clean-code` plus up to two matching the area. Do not load this skill unless the brief needs the procedure. Never weaken, skip or delete a test to get green.

**6 Verify.** The tester, given requirements and changed files, runs the original reproduction, the regression test and the neighbouring tests. For an intermittent bug, repeat the original trigger enough times to cover the measured failure rate and record the count (a single green run proves little).

**7 Review.** Reviewer (and security-auditor for high risk) check that the fix addresses the cause, handles the same pattern correctly where it appears in the changed area, and does not change unrelated behaviour. Findings loop per `AGENTS.md`.

**8 Document.**

| File | Owner | Update when |
|---|---|---|
| `CHANGELOG.md` | implementer | Always for a user-visible or operator-visible fix: entry under Unreleased, in Fixed (or Security for a vulnerability) |
| `README.md` | implementer | A documented command, setting or behaviour changed |
| `docs/PRD.md`, `docs/API-CONTRACTS.md`, `docs/DB.md` | architect | The bug showed the spec was wrong or silent (named in `Docs impact`) |
| `docs/MEMORY.md` | orchestrator | A durable pitfall or constraint was learned (skill `project-memory`) |
| `docs/TASKS.md` | orchestrator | Always |

Keep a Changelog guidance applies: entries describe notable differences between versions, not commit logs, and a vulnerability fix goes under Security. For entry wording, load `technical-documentation`.

**9 Close.** Report with the post-fix record (below), the evidence ledger, same-pattern follow-ups and any accepted gaps.

### Choosing the route: known cause or unknown cause

| Situation | Route (per `AGENTS.md` Triage) | Reproduction by | Notes |
|---|---|---|---|
| Cause stated and credible (a failing test, a clear stack trace to one line) | Standard | tester or implementer | Still write the regression test first |
| Cause unknown | Unclear failure: debugger, implementer, tester, reviewer | debugger | The debugger never edits source; instrumentation is proposed to the implementer |
| First fix did not work | Send the failing output, what was tried and the file paths to the debugger | debugger | Counts as a loop iteration |
| Regression from a recent change | Unclear failure | debugger | Bisection technique is in `debugging`; history operations are in `git-version-control` |
| Flaky test failing in CI | Unclear failure | debugger | Do not "fix" by retries or longer timeouts without a cause |

### Bug classes and what changes for each

| Class | What is different | Evidence to demand |
|---|---|---|
| Crash or exception | Stack trace is the lead; check input that triggers it | Reproduction input; trace tied to the cause |
| Wrong output | Pin down expected output from the requirement, not from the code | Expected and actual values |
| Intermittent | Frequency and conditions matter; races, ordering, time, shared state | Measured failure rate before and many passes after |
| Performance regression | Needs a number and a scenario | Before and after measurement under the same load; request measurement from tester or implementer |
| Data corruption | Fixing code does not repair existing data | Separate data-repair plan with backup and rollback; running it is a gated action |
| Security bug | Risk is high; confidentiality matters | security-auditor involved; report location and kind only, never secret values |
| Regression | A known-good version exists | The commit range and the change that introduced it |
| Environment-only | Works on one machine or deployment | Environment capture; differences listed |

### Mitigation versus fix

A mitigation reduces harm now (turn a feature off with an operations toggle, roll back a release, block an input). It does not close the bug. The playbook tracks them separately:

- Record the mitigation, who approved it and how to undo it. Rollbacks, deployments and configuration changes in production are gated actions: ask the user with action, target, risk and rollback (`AGENTS.md`, Approval gates). Mechanics belong to `devops-deployment`.
- Keep the bug task open until the cause is fixed and the mitigation is removed, or the user accepts the mitigation as the resolution.
- Ops toggles used as kill switches are a recognised pattern, but they add a code path that must be tested in both states.

### Failure handling and the loop limit

When a fix does not make the checks pass, or a review finds the fix wrong, follow the failure and loop rules in `AGENTS.md` (Quality gates) and the orchestrator's failure steps: first failed fix or unknown cause goes to the debugger with the failing output and what was tried, a second attempt uses the debugger's root cause, and after the loop limit the task is marked `blocked` and the user gets the options. A regression caused by a fix counts toward the limit; rephrasing the issue or splitting it does not reset it. When escalating, state four things: what failed (verbatim), what was tried, the likely cause, the options.

Anti-patterns that look like fixes: catching and ignoring the error; adding a retry or a longer timeout with no cause; special-casing the failing input; deleting or loosening the failing assertion; changing the specification to match the bug without asking.

### The post-fix record

A short record in the task file, so the knowledge outlives the session. The format of the record is owned by `debugging` (regression prevention); this is the minimum:

| Field | Content |
|---|---|
| Symptom | What users saw, verbatim error |
| Root cause | One or two sentences with file and line |
| Fix | What changed and why that addresses the cause |
| Regression test | Test name and location; failing-before and passing-after evidence |
| Detection gap | Why existing tests missed it, and what guard was added |
| Follow-ups | Same-pattern occurrences and unrelated findings, not fixed |

## Examples

### Intake summary

```
Symptom: POST /api/orders returns 500 when the item list contains a repeated product id.
Expected: 422 with a message naming the duplicate id (docs/API-CONTRACTS.md, Orders).
Verbatim error: "duplicate key value violates unique constraint "order_items_order_id_product_id_key""
Environment: staging, v1.8.2, PostgreSQL 16. Frequency: every time with duplicates.
Class: unclear failure resolved to known cause after intake (constraint named in the error); standard, risk normal.
```

### Regression test that fails first (illustrative syntax)

```js
// Fails before the fix with: expected status 422, received 500
test("rejects an order with a repeated product id", async () => {
  const res = await post("/api/orders", { items: [{ productId: 7, qty: 1 }, { productId: 7, qty: 2 }] });
  assert.equal(res.status, 422);
  assert.match(res.body.error, /duplicate product id 7/);
});
```

The recorded failing run is the evidence that the test can detect the bug. The test framework syntax is illustrative; use the project's own framework and confirm its API with context7.

### Fix brief to the implementer

```
Goal: Make POST /api/orders reject repeated product ids with 422 instead of failing with 500.
Task file: .agents/tasks/orders-duplicate-product-500.md
Context: Debugger root cause: src/orders/create.ts:58 inserts rows without checking duplicates; the
  database constraint raises an unhandled error. Failing test: tests/orders/create.test.ts:44
  (expected 422, received 500). Baseline: 142 pass, 1 pre-existing failure in tests/legacy/report.test.ts.
Scope: src/orders/create.ts, src/orders/validate.ts
Out of scope: schema changes, other endpoints with the same pattern (listed as follow-ups), refactoring
Acceptance criteria:
  1. The failing test passes without being edited.
  2. All previously passing tests still pass; the pre-existing failure is reported unchanged.
  3. The error body names the duplicated product id.
Skills: languages-clean-code, api-engineering
Research: use context7 and gh_grep as required by AGENTS.md
Return: the standard report
```

### CHANGELOG entry

```
## [Unreleased]

### Fixed
- Creating an order with a repeated product id now returns 422 with the duplicate id instead of a 500 error.
```

### Post-fix record

```
Symptom: POST /api/orders returned 500 for a repeated product id.
Root cause: create.ts:58 relied on the database constraint; validation never checked duplicates.
Fix: validate.ts rejects duplicates before insert and returns 422 naming the id.
Regression test: tests/orders/create.test.ts:44 failed (500) before the fix, passes after.
Detection gap: no test sent repeated ids; added this one.
Follow-ups: the same pattern exists in POST /api/carts (not fixed; added to docs/TASKS.md follow-ups).
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Fixing before reproducing | Cannot show the fix works; may fix the wrong thing | Reproduce, record the failing output |
| Accepting "likely cause" | The fix may treat a symptom | Require evidence and a disconfirming check |
| Writing the test after the fix | The test may never have failed | Record the failing run first |
| A regression test that fails for the wrong reason | Proves nothing about the bug | Check the failure message names the bug |
| Fixing the same pattern elsewhere unasked | Unreviewed, out-of-scope changes | List as follow-ups; ask the user |
| Calling a mitigation a fix | The bug returns when the mitigation is lifted | Track both; close only when the cause is fixed |
| Single green run for an intermittent bug | Luck, not proof | Measure the failure rate and repeat enough times |
| Repairing data with code changes only | Existing bad data stays | Plan a gated data repair with backup and rollback |
| Resetting the loop counter by rewording | Hides repeated failure | Count every cycle on the same cause; escalate at the limit |
| Posting security bug details widely | Exposes users before the fix ships | Keep details to those who need them; involve security-auditor |

## Checklist

- [ ] Symptom, expected result, verbatim error, environment and frequency are recorded.
- [ ] A reproduction exists and its failing output is saved.
- [ ] The root cause is tied to code and was tested against at least one alternative explanation.
- [ ] Scope is set; same-pattern occurrences are listed as follow-ups; any spec question is answered.
- [ ] The regression test failed before the fix for the diagnosed reason, and the failing run is recorded.
- [ ] The fix is the smallest change that addresses the cause, with no unrelated diff.
- [ ] Baseline and after results for test, lint, type-check and build are recorded.
- [ ] Independent verification repeated the original reproduction; an intermittent bug was repeated enough times.
- [ ] Review and, for high risk, the security audit have no open `critical` or `high` finding.
- [ ] CHANGELOG, README, specs and memory were checked, and the post-fix record is in the task file.

## Verify with context7 and gh_grep

- **context7:** when the failing code calls a library, query "`<library>` `<version>` `<function>` behaviour and error conditions" and "`<library>` `<version>` known issues `<symptom>`", and for the test runner "`<test framework>` `<version>` run one test and show failure output".
- **gh_grep:** search the exact error text in quotes, for example the constraint or exception message, and literal code for the suspect call, such as `ON CONFLICT (` or the specific method name, to see how maintained projects handle the same failure.

## Sources

- Keep a Changelog 1.1.0 (change types including Fixed and Security, Unreleased section, what not to do): https://keepachangelog.com/en/1.1.0/
- Feature Toggles (aka Feature Flags), martinfowler.com (ops toggles and kill switches, testing toggle states): https://www.martinfowler.com/articles/feature-toggles.html
