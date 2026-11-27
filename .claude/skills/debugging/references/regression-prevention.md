# Regression Prevention

How to specify the failing test, guard rails, same-pattern search, follow-ups and a short post-fix record once a root cause is proven; the debugger describes these and the implementer and tester build them; technique-level guidance with Jest 30 and pytest 8 examples, checked 2026-11-26.

## Contents

- What the debugger specifies and what others build
- The regression test specification
- Making the test fail for the right reason
- Guard rails beyond the test
- Searching for the same pattern elsewhere
- Fixes that must not be proposed
- Follow-ups
- The short post-fix record
- Handoff to the implementer

## Guidance

### What the debugger specifies and what others build

The debugger edits no source, tests or configuration. So the regression work is a **specification** inside the report:

| Item | Debugger provides | Built by |
|---|---|---|
| Fix | File, function, line, before and after, and why it addresses the root cause | implementer |
| Regression test | Level, inputs, steps, assertions, result before and after the fix | implementer writes the fix; tester writes or reviews the test (per `AGENTS.md` roles) |
| Guard rail | What invariant to enforce and where | implementer |
| Same-pattern search | Query, locations found | implementer fixes any extra locations if the coordinator approves the scope |
| Follow-ups | Description and why | coordinator records in `docs/TASKS.md` |
| Post-fix record | Pitfall text | coordinator records in `docs/MEMORY.md` |

A source change invalidates earlier test, review and audit results for the affected area; say so in the handoff so the coordinator re-verifies. For test design in depth (fixtures, mocks, layering), load `testing-strategy` or `test-driven-development`. This file only says what a debugger's test specification must contain.

### The regression test specification

A good regression test pins the **cause**, not only the symptom, fails before the fix, passes after, and cannot pass for another reason.

Specify these fields:

```text
Name:       <behaviour in plain words, with the bug id if there is one>
Level:      unit | integration | end-to-end -- the lowest level that can observe the defect
Setup:      <fixtures, data, clock, configuration; deterministic>
Action:     <the call or request, with exact inputs>
Assert:     <the observable result, exact values>
Before fix: FAILS with <exact message>
After fix:  PASSES
Guards:     <which wrong fixes this test would also catch>
```

Choosing the level:

| Where the defect lives | Test level | Reason |
|---|---|---|
| One function's logic or arithmetic | Unit | Fast, precise, easy to keep |
| Wiring between components (a key mismatch, a missing dependency, a wrong order) | Integration | A unit test with mocks would pass |
| Behaviour visible only through the UI or full stack | End-to-end, with the minimal flow | Only the full path shows it; keep it small |
| Data shape at a boundary | Contract or schema check at the boundary | Catches every producer and consumer |

Rules:

- **Lowest level that fails for the right reason.** A unit test beats an end-to-end test when both fail before the fix.
- **Turn the minimal reproduction into the test.** The minimal reproduction from [bug-reproduction.md](bug-reproduction.md) already has the input, the steps and the failure; keep it small.
- **Assert behaviour, not implementation.** Assert the returned value or visible effect; avoid asserting that a private function was called.
- **Be deterministic.** Fix the clock, seed, ordering and data. A regression test that is itself intermittent is worthless. For a race, make the interleaving deterministic (inject the delay or the ordering at the seam), or run enough iterations and state the count.
- **Include the boundary.** Cover the case that failed and the nearest neighbouring cases (off by one, empty, maximum, the other side of a date boundary).
- **One cause, one test.** If several symptoms share a cause, one test pinned to the cause plus a smaller assertion per extra symptom is enough.
- **Never weaken, skip or delete an existing test to make it pass**, and never mark the new test as expected-to-fail to get a green build. `AGENTS.md` forbids it.

### Making the test fail for the right reason

A test that fails before the fix for the wrong reason (a typo, a missing fixture) proves nothing. Specify how the implementer or tester verifies it:

1. Run the new test **without** the fix. It must fail with the **same message and location** as the original failure, or a clearly equivalent assertion.
2. Apply the fix. The test passes.
3. Revert the fix only (keep the test). It fails again with the same message.
4. For an intermittent defect, run the test the stated number of times each way and record both counts.

Jest and pytest commands that run one test (check the project's own commands first; the manifest and `AGENTS.md` win): `jest -t "<name>"`, `pytest <path>::<test_name>`. Jest's `-t` matches the regular expression against the full name, including the `describe` blocks. To catch order dependence, Jest can shuffle test order with `--randomize --seed <n>` and prints the seed so a failing order can be replayed (default `jest-circus` runner).

### Guard rails beyond the test

A test catches this instance. A guard rail makes the **class** of defect hard to write or quick to notice. Propose one only when it is cheap and proportionate; do not gold-plate a one-line fix.

| Defect class | Guard rail | Trade-off |
|---|---|---|
| Wrong or missing configuration key | Validate required configuration at startup and fail fast with the key name (never its value) | Slightly longer startup; clear failure at deploy time |
| Mismatched identifier between registrar and consumer (string keys) | A typed constant or enumeration shared by both; a test that resolves every registered key | A bit more ceremony |
| Invalid data crossing a boundary | Validation at the boundary (schema), with a clear error | Cost on every request; belongs at trust boundaries only |
| Impossible state | An assertion or invariant check at the point of production, so the bad value is caught where it is made | Do not use assertions as input validation |
| Duplicate records | A uniqueness constraint in the data store (coordinate with `database-engineering`) | Needs a migration, which needs user approval |
| Timezone, locale or clock dependence | Inject the clock; run a test job with a non-default timezone | Slightly more setup |
| Concurrency | A lock or atomic operation at the shared resource, a single-writer rule, or an idempotency key | Can reduce throughput; state it |
| Silent failure | Make the failure loud: raise, log with the context needed, count it | More noise; justify each |
| Wrong build or stale artefact | Clean build in CI; print the revision at start | Slower builds |

Guard rails never include suppression: no catch-and-ignore, no retry loop, no sleep, no longer timeout, no loosened assertion, no lowered log level. See below.

A guard rail that changes a public API, a database schema or deployment configuration is not a debugging output; it is a follow-up for the architect or implementer with user approval. For monitoring and alerting setup, load `devops-deployment`.

### Searching for the same pattern elsewhere

The proven cause is a pattern; the defect probably exists elsewhere. Search before you report, and report the result either way.

Procedure:

1. Write the pattern in one sentence: "values read from X without checking Y" or "registers a dependency under a key that no consumer uses".
2. Turn it into searches: the literal call, the function name, the constant, the data shape. Run several; one query misses variants.
3. For each hit, decide: **same defect**, **safe** (and why), or **uncertain**.
4. Cross-check from the other side: list the consumers of the broken contract and confirm each.
5. Report locations with file and line, each with its decision. If there are none, report the queries and that none matched. "I searched" without the query is not evidence.

Example search set for "key registered under one name and read under another":

```text
search: register(          -> list every registration key
search: resolve(           -> list every consumer key
compare: keys registered but never resolved, and keys resolved but never registered
```

Do not fix extra locations yourself and do not widen the scope: report them for the coordinator to scope. Unrelated problems found while searching are follow-ups.

### Fixes that must not be proposed

These hide a symptom and make the next investigation harder. If any seems necessary, the cause is not yet proven; return to the hypotheses.

| Proposed fix | Why it is rejected | What to propose instead |
|---|---|---|
| Add a retry | Masks a deterministic or racing defect | Fix the race or the contract; retry only for a proven transient network error, as a separate, justified change |
| Add a sleep or longer timeout | Depends on timing luck | Fix the ordering, or wait on the actual condition |
| Wrap in try and ignore or log a warning | Destroys the evidence and the signal | Handle the specific error with a defined behaviour |
| Skip, disable or delete the test | Removes the detector | Fix the cause; if the test is wrong, say why with evidence |
| Loosen an assertion or widen a tolerance | Accepts the wrong result | Assert the right value |
| Lower the log level | Hides the failure | Leave logging as is |
| Special-case the failing input | The next input fails | Fix the rule the input exposed |
| Restart or clear a cache as a fix | Hides a state bug | Find why the state went wrong |

### Follow-ups

Follow-ups are real work that the fix does not do. Report each in one line to the coordinator, who records it in `docs/TASKS.md` under Follow-ups. Do not start them and do not bundle them into the fix.

A good follow-up has: what, why it matters (the failure it prevents), suggested owner role, risk class (high-risk areas need security-auditor under `AGENTS.md`), and whether it needs user approval (a migration, a dependency change, a configuration or CI change always does).

Typical follow-ups: other locations of the pattern, a guard rail that needs a schema change, missing coverage in an area the bug exposed, a misleading log message, a specification that disagrees with the code (this goes to the architect, and the user decides which is right).

### The short post-fix record

The coordinator keeps durable facts in `docs/MEMORY.md`, which must stay short. Offer a record the coordinator can paste under **Pitfalls**: one to three lines that someone would need to avoid repeating the bug. Do not add to it yourself.

Rules for the record:

- Durable only: a rule, a constraint or a trap, not a story of the investigation.
- Include the **detection hint**: how this bug shows up, so the next person recognises it.
- No secrets, personal data, hostnames or ticket gossip.
- Blameless: describe the system, not a person.
- If it is already in the file, say "no change".

Longer incident write-ups, when the project wants them, are the coordinator's decision; the blameless postmortem structure used by the Google SRE book (what happened and its impact, mitigation, root causes, follow-up actions) is a good outline. Keep each follow-up action concrete, owned and prioritised.

### Handoff to the implementer

Close the report so the implementer needs no further questions:

```text
Fix:           <file:function:line, before -> after>
Why:           <how it removes the root cause>
Test:          <the specification above>
Guard rail:    <proposed or "none, because ...">
Same pattern:  <queries and locations>
Scope warning: <what must not change>
Re-verify:     run <test command>, lint and build; then review; a source change invalidates earlier results
Cleanup done:  <scratch files, copies, processes removed>
```

## Examples

### Regression test specification, filled in

```text
Name:       Invoice job generates exactly one invoice per customer and period near midnight (bug INV-214)
Level:      Integration (job + store); the defect is in the interaction between scheduler timestamp and period logic
Setup:      Clock fixed at 2026-10-01T00:20:00+01:00 (= 2026-09-30T23:20:00Z); process timezone Europe/Berlin;
            one customer with an active plan; empty invoices table
Action:     Run generate_invoices() once with the scheduler timestamp above
Assert:     invoices table contains exactly 1 row for the customer, period "2026-09"
Before fix: FAILS: expected 1 row, found 2 (periods 2026-09 and 2026-10)
After fix:  PASSES
Guards:     also catches any later change that recomputes the period from local time
Repeat:     deterministic; no repetition needed
```

### Same-pattern report

```text
Pattern:  billing period derived from host-local date.
Queries:  today(  |  datetime.now(  |  date.today(  in src/billing and src/jobs
Found:    invoice_job.py:41 (this bug); report_job.py:27 (same call, same risk - UNCERTAIN, output only
          shown to staff, no money); usage_job.py:63 (uses UTC explicitly - SAFE).
Action:   report_job.py:27 as a follow-up; not part of this fix.
```

### Post-fix record for `docs/MEMORY.md`

```text
- Billing periods must be computed from UTC, never from the host's local date; a scheduler on a
  non-UTC host produced duplicate invoices at month boundaries. Tests must run with a non-UTC TZ too.
  Detection: two invoice rows per customer for adjacent periods created minutes apart.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Proposing a fix with no regression test | The defect returns unnoticed | Always specify a test with inputs, expected result and before and after outcomes |
| A test that never failed before the fix | It may not exercise the defect | Require evidence of the failure without the fix, with the same message |
| Testing at too high a level | Slow, flaky and unclear on failure | Use the lowest level that fails for the right reason |
| Asserting implementation details | Breaks on harmless refactors | Assert observable behaviour |
| A non-deterministic regression test | Becomes the next flaky test | Fix clock, seed and ordering; state run count for races |
| Reporting "searched, none found" with no query | Cannot be checked or repeated | List the exact searches and results |
| Fixing the other locations yourself | Scope creep and unreviewed edits | Report them; the coordinator scopes them |
| Suggesting a retry or sleep as a guard rail | Masks the next failure | Propose a real invariant or boundary check |
| Burying follow-ups in prose | They are never done | One line each, for `docs/TASKS.md`, with owner and risk |
| Writing a long narrative into `docs/MEMORY.md` | The file is capped and stops being read | One to three durable lines with a detection hint |

## Checklist

- [ ] The report contains a regression test specification with name, level, setup, action, assertion and before and after results.
- [ ] The test is at the lowest level that fails for the right reason and is deterministic.
- [ ] The test would fail with the same message as the original failure when the fix is absent.
- [ ] No proposal uses a retry, sleep, longer timeout, swallowed exception, disabled test or loosened assertion.
- [ ] Any proposed guard rail addresses the defect class and states its trade-off.
- [ ] The same-pattern search lists queries, locations and a decision for each hit, or states the queries and that none matched.
- [ ] Extra locations are reported, not edited.
- [ ] Follow-ups are one line each, with reason, suggested owner and whether user approval is needed.
- [ ] A post-fix record of one to three durable, blameless lines with a detection hint is offered for the coordinator.
- [ ] The handoff says earlier test, review and audit results need to be repeated after the source change.
- [ ] Temporary files, copies and processes were removed and listed.

## Verify with context7 and gh_grep

- **context7:** Check the locked test framework's current API for the test you specify: Jest test selection (`-t`), test ordering (`--randomize`, `--seed`) and fake timers for the installed Jest; pytest node-id selection, fixtures and marks (including how expected failures are marked, so you can warn against them) for the installed pytest; the validation or schema library's API for the guard rail you propose; and the database's constraint syntax for the installed version.
- **gh_grep:** Search literal regression-test shapes in maintained repositories, for example `it("does not` plus the bug-class word, or test names containing `regression`; search the guard-rail form such as `process.env.` with a required-variable check at startup, or `assert` at a boundary; search the pattern you are hunting (the literal call) across the project to build the same-pattern list.

## Sources

- Jest CLI options (Jest 30.5): https://jestjs.io/docs/cli
- pytest, How to handle test failures (8.4): https://docs.pytest.org/en/8.4.x/how-to/failures.html
- Google SRE book, chapter 15, Postmortem Culture: Learning from Failure: https://sre.google/sre-book/postmortem-culture/
- git-bisect manual (Git 2.56.0): https://git-scm.com/docs/git-bisect.html
