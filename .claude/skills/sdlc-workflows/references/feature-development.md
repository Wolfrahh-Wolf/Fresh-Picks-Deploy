# Feature Development

The playbook for taking a feature request from first message to verified, documented result, with the inputs, outputs and exit check of each stage; language-neutral, written against the RelayCrew `AGENTS.md` roles and templates; checked 2026-11-27.

## Contents

- How to read this playbook
- The stage table
- Stage details and briefs
- Slicing a feature into increments
- Hiding unfinished work with release toggles
- Changing an interface or schema during a feature
- Scope changes in flight
- Right-sizing: which stages may be skipped
- Closing the task

## Guidance

### How to read this playbook

This playbook sequences stages and names who acts and which skills they load. It does not repeat the rules that `AGENTS.md` owns. Where a stage touches one of them, it points there:

| Topic | Where the rule lives |
|---|---|
| Classes, high-risk list, routing | `AGENTS.md` (Triage) |
| Delegation brief and standard report | `AGENTS.md` (Handoff) |
| Done criteria, severity scale, loop limit | `AGENTS.md` (Quality gates) |
| Documentation sync procedure | `AGENTS.md` (Documentation sync) |
| What needs the user's approval | `AGENTS.md` (Approval gates) |

If a stage here and `AGENTS.md` ever differ, follow `AGENTS.md` and report the difference. Each stage below has an exit check. Do not begin the next stage until the exit check has evidence, which means a command and its result, or a file and line, not a statement that it was done.

### The stage table

| # | Stage | Who | Input | Output | Exit check |
|---|---|---|---|---|---|
| 0 | Intake and triage | orchestrator | User request | Restated goal, assumptions, class and risk in one line, blocking questions asked once | User answered or assumptions are stated in the task |
| 1 | Resume and open | orchestrator | `docs/TASKS.md`, `docs/MEMORY.md`, `.agents/tasks/` | Task file, row in `docs/TASKS.md` | No duplicate open task for the same work |
| 2 | Discover (Complex) | `explore` (read-only) | Goal, entry points | Map of the code involved, conventions, tests, owners of data | Paths and entry points named with file evidence |
| 3 | Specify and plan | architect | Goal, discovery map, specs | Acceptance criteria, plan, files in scope; specs and ADRs when design changes | Each criterion is observable and testable (orchestrator checks); Complex plans approved by the user |
| 4 | Slice | orchestrator with architect plan | Plan | Ordered increments, each with its own criteria | Each increment can be built and verified alone |
| 5 | Test-first (optional) | tester | Criteria for one increment | Failing tests that express the criteria | Tests fail for the intended reason; failure output recorded |
| 6 | Implement | implementer | One increment brief | Code, tests, verification results, self-review | Report shows baseline, test, lint, type-check and build results |
| 7 | Verify independently | tester | Requirements and changed files | Evidence per acceptance criterion | Every criterion has evidence or a named gap |
| 8 | Review | reviewer, plus security-auditor for high risk | Requirements and changed files | Findings by severity | No `critical` or `high` open |
| 9 | Fix loop | implementer, then repeat 7 and 8 for the affected area | Findings | Fixes with evidence | Re-verified; loop limit from `AGENTS.md` respected |
| 10 | Documentation sync | architect, implementer, orchestrator | Final diff | Per-file `updated` or `no change` | Table complete, no blank rows |
| 11 | Close | orchestrator | All reports | Final report, task `done`, `docs/TASKS.md` updated | Quality gates all met |

Stages 5 to 9 repeat once per increment. Stage 10 runs once at the end of the task and also after every increment that changes behaviour documented elsewhere.

### Stage details and briefs

**0 Intake and triage.** Restate the goal in your own words and list assumptions. Ask blocking questions together in one message. A feature request often hides a decision (who may use it, what happens on failure, what data it keeps); if two readings would change the outcome materially, ask. Apply `AGENTS.md` (Triage) and note whether the request touches the high-risk list. If it does, add the security audit to the plan now so it is not forgotten at the end.

**1 Resume and open.** Search `docs/TASKS.md` and `.agents/tasks/` for the same work before creating anything. Open the task from the template (`.agents/tasks/TEMPLATE.md`) with Goal, Constraints, Assumptions and the class and risk lines.

**2 Discover.** Brief `explore` as read-only with a concrete question: "which modules handle X, how do they persist it, which tests cover it". Output is a map, not opinions. Skip for a change confined to one known file.

**3 Specify and plan.** The architect fills the plan, files in scope and acceptance criteria. Loads: `requirements-engineering`, `product-technical-planning`, and `system-architecture` when structure changes (at most 3). The orchestrator rejects criteria it cannot verify with a command or an observable result ("works well" is not a criterion; "POST /orders with a missing field returns 422 and an error naming the field" is). For a Complex task, present the plan to the user and wait for approval.

**4 Slice.** See the next section. The output is an ordered list of increments written into the task plan.

**5 Test-first.** Only when the brief asks for test-first work. The tester writes failing tests (skill `test-driven-development`) before the implementer starts. Record the failing output; it is the evidence that the tests can fail.

**6 Implement.** One brief per increment, using the `AGENTS.md` brief shape. Skills for the implementer: `languages-clean-code` plus up to two of the domain skills (`backend-engineering`, `frontend-engineering`, `database-engineering`, `api-engineering`) that match the increment. Put the stage instructions in the brief rather than loading this skill, unless the whole procedure matters. A filled-in brief is in Examples.

**7 Verify independently.** Give the tester the requirements and changed files, not the implementer's account of its own work. The tester maps each criterion to a result.

**8 Review.** Give the reviewer and security-auditor the requirements and changed files. Do not show either the other's findings before both report. The high-risk list decides whether the audit is required.

**9 Fix loop.** Send `critical` and `high` findings to the implementer, then repeat stages 7 and 8 for the affected area, because a source change invalidates earlier results there. Count loops as `AGENTS.md` (Quality gates) defines; a regression introduced by a fix counts toward the limit.

**10 Documentation sync.** Follow `AGENTS.md` (Documentation sync). Delegate specification and ADR updates to the architect and README and CHANGELOG updates to the implementer. For writing technique, load `technical-documentation`.

**11 Close.** All quality gates met, `docs/TASKS.md` updated, `docs/MEMORY.md` updated if something durable was learned (skill `project-memory`), final report with evidence, medium and low findings listed for the user.

### Slicing a feature into increments

An increment is the smallest piece that is useful to verify and safe to leave behind. Slice vertically, through the layers, not horizontally by layer.

| Slice by layer (avoid) | Vertical slice (prefer) |
|---|---|
| 1. Add the table. 2. Add the repository. 3. Add the endpoint. 4. Add the UI. Nothing can be demonstrated until step 4. | 1. Create an order with one item end to end (table, repository, endpoint, minimal UI). 2. Add multiple items. 3. Add validation and error states. Each step can be tried and tested. |

Rules for slicing:

1. Each increment has its own acceptance criteria that can be checked without the later increments.
2. Each increment leaves the codebase building and every existing test passing.
3. Order the riskiest unknown first, so surprises appear while the plan is cheap to change.
4. Put interface and schema additions before the code that uses them (see the parallel change section).
5. Keep increments small enough that one review can hold them in mind. As a heuristic, a diff over a few hundred changed lines or more than a handful of files is a signal to split further (heuristic, not a rule).
6. Task-breakdown technique, dependencies and estimates belong to `product-technical-planning`; use it for the slicing itself.

"Deliverable" means complete and verified in the working tree. Pushing, merging, releasing or deploying an increment are separate actions that need the user's approval for that exact action (`AGENTS.md`, Approval gates).

### Hiding unfinished work with release toggles

When an increment must be integrated before the whole feature is ready, a release toggle can hide the incomplete behaviour so the code can still be built and tested. Martin Fowler's article on feature toggles describes release toggles as the way to let incomplete or untested code be merged and deployed while keeping it unseen. Rules when the plan uses one:

- The toggle is part of the plan: name, default (off), where it is read, and the increment that removes it.
- "Off" means legacy behaviour and "on" means new behaviour, so the convention is the same everywhere.
- Test both states: the expected production configuration and the fallback with the new toggle off.
- Release toggles are short-lived. Add the removal as a task when the toggle is created, and set an expiry. The task is not done while a release toggle remains, unless the user accepts it.
- Adding a toggle library is a dependency change and needs approval; a plain configuration value read in one place usually does not.
- Do not use a toggle to hide security-relevant behaviour (authorisation checks) behind a default-off switch without the security-auditor reviewing both states.

### Changing an interface or schema during a feature

Use the three-phase expand, migrate, contract sequence (Parallel Change) so every intermediate state works:

1. **Expand:** add the new interface or column beside the old one. Nothing breaks.
2. **Migrate:** move callers or data to the new form, one at a time, testing as you go.
3. **Contract:** remove the old form when nothing uses it.

Each phase is a separate increment. The contract phase must be in the plan, or the codebase keeps two versions. Writing a migration is an implementer task; running it is a gated action. Design questions about schema belong to `database-engineering`, and interface versioning to `api-engineering`.

### Scope changes in flight

A feature grows when discovery shows more work than the request described. When any of these appear, stop and escalate to the user as `AGENTS.md` requires, with what happened, what was tried, what you need and the options:

- Satisfying a criterion needs changes outside the files in scope.
- The work touches a high-risk area that the task did not list (re-classify and add the audit).
- Two valid interpretations now lead to different outcomes.
- A dependency, paid service or infrastructure change is required.

Do not absorb scope silently. Record the new scope as a decision with approval in the task file.

### Right-sizing: which stages may be skipped

Every stage exists to reduce a real risk. Skip a stage only when it reduces none, and write the reason in the task file.

| Stage | Reasonable to skip when | Never skip when |
|---|---|---|
| Discover | The change is confined to one known file | The code involved is unfamiliar or cross-cutting |
| Specify and plan | `AGENTS.md` routes the class without design and the criteria are already observable | Design is open or the class is Complex |
| Test-first | The brief did not ask and the project has no harness for it | The brief asks for it |
| Independent verify and review | Never for Standard or above (the class routing requires them) | Always required by the routing |
| Security audit | Not high risk | High risk, whatever the size |

### Closing the task

Before reporting done, check each of the following has evidence in the task file: each acceptance criterion; the latest test, lint, type-check and build results; no open `critical` or `high` finding; the security audit for a high-risk task; the documentation sync table; and the removal of every temporary toggle or shim, or the user's acceptance of it. Report using the orchestrator report format, with one recommended next step.

## Examples

### Filled-in task file (abbreviated)

```
# Add CSV export to the orders page

Status: in-progress
Class: standard
Risk: normal

## Goal
Signed-in users can download their own orders as a CSV file from the orders page.

## Constraints
No new dependencies. Reuse the existing orders repository.

## Assumptions
Export covers the user's own orders only; up to 10,000 rows (confirmed by the user).

## Plan
1. Increment A: GET /orders/export returns CSV for the caller's orders (no UI).
2. Increment B: "Export" button on the orders page calls it.
3. Increment C: empty-result and large-result behaviour.

## Files in scope
src/orders/export.ts, src/routes/orders.ts, src/ui/OrdersPage.tsx, tests/orders/export.test.ts

## Acceptance criteria
- [ ] A: the response has Content-Type text/csv and one header row plus one row per order of the caller
- [ ] A: another user's orders never appear in the response
- [ ] B: clicking Export downloads orders.csv
- [ ] C: zero orders returns the header row only; more than 10,000 rows returns 413 with an error message
```

### Increment brief to the implementer

```
Goal: Implement increment A: GET /orders/export returns the caller's orders as CSV.
Task file: .agents/tasks/orders-csv-export.md
Context: Express 4 app. Routes in src/routes/orders.ts; repository in src/orders/repo.ts
  (listByUser(userId)). Auth middleware sets req.user. Baseline: 142 tests pass, 0 skipped.
Scope: src/orders/export.ts, src/routes/orders.ts, tests/orders/export.test.ts
Out of scope: UI, new dependencies, schema changes, README structure changes
Acceptance criteria:
  1. 200 with Content-Type text/csv; header row plus one row per order of the caller.
  2. Another user's orders never appear (test with two users).
  3. Unauthenticated request returns 401.
Skills: languages-clean-code, backend-engineering
Research: use context7 and gh_grep as required by AGENTS.md
Return: the standard report
```

### Slicing: bad to good

```
Bad:  "Build the export feature" as one task touching route, repository, UI, tests and docs.
Good: A (endpoint, verified alone) -> B (button, verified alone) -> C (edge cases, verified alone).
      After each: build green, all tests pass, criteria for that increment checked.
```

### Stage ledger in the closing report

```
Stage ledger
0 triage: standard, risk normal (no high-risk signals)
3 plan: criteria observable; architect report accepted
6 implement A: baseline 142 pass; after 149 pass, 0 skipped; lint 0; types 0; build ok
7 verify A: tester mapped criteria 1-3 to tests export.test.ts:12,31,48
8 review A: reviewer approve; 1 low (naming) listed for the user
10 docs sync: README updated (export usage); CHANGELOG updated (Added); others no change
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Slicing by layer | Nothing can be verified until the last slice | Slice vertically; each increment verifiable alone |
| Starting stage N+1 on a claim | Defects compound and the evidence trail breaks | Require the exit-check evidence first |
| Merging a feature and a refactor in one task | The diff cannot be reviewed or reverted cleanly | Split into separate tasks with one playbook each |
| Leaving the toggle or shim in place | Two code paths live forever | Put the removal increment in the plan and check it at close |
| Forgetting the audit on a high-risk feature | A required gate is missed late | Check the high-risk list at intake and again at planning |
| Giving the reviewer the implementer's summary | Review inherits the author's blind spots | Give requirements and changed files |
| Absorbing scope silently | Cost, risk and approvals drift | Stop and escalate with options |
| Treating "deliverable" as "pushed" | Remote writes happen without approval | Push, merge and deploy only on approval for that exact action |

## Checklist

- [ ] The request was restated, assumptions stated and the class and risk named in one line.
- [ ] `docs/TASKS.md` and `.agents/tasks/` were checked for existing work.
- [ ] The task file has Goal, Constraints, Plan, Files in scope and an observable criterion per outcome.
- [ ] Every acceptance criterion can be checked with a command or an observable result.
- [ ] Each increment can be built and verified alone and has its own criteria.
- [ ] Each brief has one goal, at most 3 skills and the context a fresh agent needs.
- [ ] Baseline and post-change test, lint, type-check and build results are recorded per increment.
- [ ] Independent verification and review ran on the final state of each affected area.
- [ ] Any toggle, shim or compatibility layer is removed or explicitly accepted by the user.
- [ ] The documentation sync table has a result for every file.

## Verify with context7 and gh_grep

- **context7:** for the frameworks and libraries named in the task, query "`<framework>` `<version>` route handler and middleware conventions", "`<test framework>` `<version>` run a single test file", "`<package manager>` `<version>` run scripts". For any flag or toggle library already in the manifest, query its evaluation API and default behaviour.
- **gh_grep:** search literal code for conventions before inventing one: `featureFlags.isEnabled(`, `process.env.FEATURE_`, `router.get("/` for route registration style, and the verbatim text of any error you meet.

## Sources

- Feature Toggles (aka Feature Flags), Pete Hodgson on martinfowler.com (toggle categories, lifetimes, removal, testing both states): https://www.martinfowler.com/articles/feature-toggles.html
- Parallel Change, martinfowler.com (expand, migrate, contract): https://www.martinfowler.com/bliki/ParallelChange.html
- Branch By Abstraction, martinfowler.com (gradual change while staying releasable): https://www.martinfowler.com/bliki/BranchByAbstraction.html
