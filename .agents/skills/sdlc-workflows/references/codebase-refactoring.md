# Codebase Refactoring

The playbook for large structural changes that keep behaviour identical: build a safety net, plan small reversible steps, set checkpoints and define rollback, using strangler fig, branch by abstraction and parallel change; language-neutral with JavaScript illustrations, written against the RelayCrew `AGENTS.md` roles and templates; checked 2026-11-27.

## Contents

- What counts as refactoring here
- The stage table
- Stage 1: the safety net
- Stage 2: choosing the strategy and writing the plan
- Stage 3: executing one step at a time
- Stage 4: checkpoints
- Stage 5: migrate and contract
- Stage 6: rollback
- Stop conditions and partial completion
- Closing the task

## Guidance

### What counts as refactoring here

Refactoring is changing the internal structure of code without changing its external behaviour, done as a series of small behaviour-preserving steps, with the software working after every step. A "large refactoring" is that same discipline applied to a change too big for one step: replacing a subsystem, a library, an interface or a data structure used in many places.

The invariant is **no behaviour change**. This playbook therefore never mixes in a feature or a bug fix. If you discover a defect in the old code, pin the current behaviour with a test, record the defect as a follow-up and carry on; fixing it is a separate task with its own regression test (see the bug-fixing playbook). Likewise, a new feature that needs restructuring first becomes two tasks: the refactoring, then the feature.

Rules owned by `AGENTS.md` are not repeated here: triage, briefs and reports, quality gates and the loop limit, approval gates, documentation sync. A cross-cutting restructuring is normally Complex under `AGENTS.md` (Triage): the architect writes the plan and the user approves it before code changes. If the refactoring touches a high-risk area (authentication, authorization, payments, personal data, cryptography, secrets, migrations, CI/CD), the security-auditor reviews as well as the reviewer.

### The stage table

| # | Stage | Who | Input | Output | Exit check |
|---|---|---|---|---|---|
| 0 | Scope and class | orchestrator | Request | Goal, non-goals, "no behaviour change" invariant, class and risk line | User confirmed scope and non-goals |
| 1 | Safety net | tester and implementer | Code in scope | Baseline results; behaviour-pinning tests; seams where needed | Tests pass on the unchanged code and are shown able to fail |
| 2 | Plan | architect (skills `system-architecture`, `product-technical-planning`) | Discovery, safety net | Strategy, ordered steps with verification and rollback, transitional-code inventory | Every step buildable alone; user approved the plan |
| 3 | Execute a step | implementer | One step brief | Change, results, self-review | Same behaviour: baseline-equivalent results |
| 4 | Checkpoint | orchestrator, tester | Step report | Verified state recorded | Evidence recorded; scope unchanged |
| 5 | Migrate and contract | implementer | Remaining callers | Old path removed | No references to the old path; transitional code removed |
| 6 | Review | reviewer (and security-auditor if high risk), at milestones and at the end | Requirements and changed files | Findings by severity | No `critical` or `high` open |
| 7 | Documentation sync | architect, implementer, orchestrator | Final diff | Updated `docs/ARCHITECTURE.md`, ADR, others per file | Table complete |
| 8 | Close | orchestrator | All reports | Final report | Quality gates met |

Stages 3 and 4 repeat for every step. Stage 6 also runs at milestones for large plans, because a source change invalidates earlier review results for the affected area.

### Stage 1: the safety net

Do not change structure until you can tell whether behaviour changed.

1. **Record the baseline.** Run test, lint, type-check and build with the commands in `AGENTS.md`. Save the results, including pre-existing failures, so later runs are compared against them.
2. **Find what pins the behaviour.** For the code in scope, list which tests exercise it and through which public entry points. Prefer tests at the boundary of the code you will restructure (its public functions or endpoints) because they survive internal changes. Skill `testing-strategy` helps choose levels.
3. **Add characterisation tests where behaviour is unpinned.** A characterisation test records what the code does today for representative inputs, including odd outputs, so a change in behaviour is visible. Do not "correct" an odd result in the test; if it looks like a bug, record a follow-up. Technique for building these belongs to `test-driven-development`.
4. **Create seams where code cannot be tested.** A seam is a place where behaviour can be changed without editing at that spot, and every seam has an enabling point where the choice is made (Michael Feathers' definition, as described by Martin Fowler). Seams let you substitute a slow or external dependency in tests, observe calls, and later redirect behaviour to new code. Making code testable needs edits of its own: keep them minimal, mechanical and covered by whatever tests exist (for example passing a dependency as a parameter).
5. **Prove the net can fail.** For each pinned behaviour, deliberately make a small local change that alters it (invert a condition), confirm a test fails, then revert the change. Record the failing output. This is done by the implementer in the working tree and reverted before any commit; it is not a test edit.
6. **Compare old and new at runtime when possible.** With a branch-by-abstraction approach, a feature flag can run the new implementation in test environments and compare its behaviour with the old one (Fowler). Record what was compared and the result.

The safety net passes on the unchanged code before step 1 of the plan. If you cannot build one for a region, say so: the plan either shrinks that region or the user accepts the named risk.

### Stage 2: choosing the strategy and writing the plan

Pick the lightest strategy that works, and write the choice into the plan, with an ADR when it is an architectural decision (skill `system-architecture`, ADR reference).

| Strategy | Use when | How it works | Watch for |
|---|---|---|---|
| Small in-place steps | Rename, extract, move, simplify within a module | A sequence of tiny behaviour-preserving edits, tested after each | Scope creep into "while I am here" |
| Parallel change (expand, migrate, contract) | Changing an interface, signature, schema or data format with many callers | Add the new form beside the old, migrate callers one by one, remove the old | Forgetting the contract phase leaves two versions |
| Branch by abstraction | Replacing an internal supplier (library, module, framework) used in many places | Put an abstraction in front of the old supplier, migrate all callers to it, build the new supplier behind it, switch, delete the old and, if no longer useful, the abstraction | Abstraction leaking old-supplier concepts; long coexistence |
| Strangler fig | Replacing a large subsystem or service gradually while it keeps running | A facade or proxy intercepts requests; migrate functionality piece by piece; retire the old when nothing depends on it; remove the facade | Needs an interception point and the ability to modify the legacy side; poor fit for small systems or when the old system must be retired quickly; the facade must not become a single point of failure |
| Full rewrite | Almost never | Build a replacement and cut over | Martin Fowler notes that simple full replacements fail most of the time: long, hard to specify, and users do not wait; prefer a gradual route |

Each of these keeps old and new coexisting, so the system builds and runs correctly at every point and stays releasable while the change is in progress. That is the core of incremental delivery: value and learning arrive gradually, and any step can be the last for now.

**The plan** (architect writes it into the task's Plan section; the orchestrator checks it) has these parts:

| Part | Content |
|---|---|
| Goal and non-goals | What structure changes, what explicitly does not (including behaviour) |
| Invariant | "No behaviour change", plus the list of tests and runtime comparisons that show it |
| Strategy | One of the strategies above, with the reason |
| Steps | Ordered, each with: change, files, verification command, rollback |
| Transitional inventory | Every facade, adapter, shim, flag or duplicate that exists only for the migration, with the step that removes it |
| Ordering rationale | Seams first, then smallest or least risky callers, then the rest, then contract |
| Safe stopping points | Which steps leave the system in a coherent state suitable to pause |
| Approvals needed | Gated actions the plan contains (migrations, dependency changes, deploys, merges) with the point where approval is requested |

Step size: each step is reviewable in one sitting, leaves the build green and every test passing, and can be reverted on its own. As a heuristic (not a rule), a step touching more than a handful of files or a few hundred lines should be split.

### Stage 3: executing one step at a time

- **One step per brief.** The `AGENTS.md` brief with Goal set to the single step. Include verbatim baseline results, the files in scope, the verification commands and the rollback. Skills: `languages-clean-code`, and one or two matching the area. Name `sdlc-workflows` only if the implementer needs the whole procedure.
- **One writer per file.** Steps that touch the same files run one after another. Only steps on clearly separate modules may run in parallel.
- **Behaviour-preserving edits only.** If a test needs to change, treat it as a warning: either the step changed behaviour or the test pinned an implementation detail. A test is never weakened, skipped or deleted to pass. When a test legitimately pins an internal detail that is being replaced, move its assertion to the public behaviour first, in its own step, with the orchestrator's agreement.
- **Mechanical changes stay mechanical.** Renames, moves and signature changes are done as pure moves, without logic edits in the same step, so the diff is easy to review.
- **Report differences.** If the implementer finds the old code has a defect, it pins the behaviour, lists a follow-up and does not fix it.
- **Dependencies.** Adding or majorly upgrading one (for example the new supplier's library) needs the user's approval before the step that needs it.

### Stage 4: checkpoints

After every step the orchestrator verifies, using evidence, that the checkpoint holds:

| Check | Evidence |
|---|---|
| Behaviour unchanged | Test, lint, type-check and build results equivalent to the baseline plus new tests; no test edited to pass |
| Scope held | `git diff --stat` lists only the files the step names |
| Public contracts unchanged | Compared with `docs/API-CONTRACTS.md` and exported signatures, unless the step is the planned expand phase |
| Performance sane on hot paths | A measurement or a statement that the path is not hot; measurements are requested from tester or implementer |
| Transitional inventory current | New shims or flags added to the inventory with their removal step |
| Rollback still valid | The recorded rollback for this step still applies |

A checkpoint is a verified state recorded in the task file. When the user has asked for commits, make a commit at each checkpoint (skill `git-version-control`); pushing, merging and force or history-rewriting operations always need approval. Any later source change invalidates earlier results for the affected area.

Drift control: if a step's diff grows beyond the plan, stop and re-plan instead of finishing it. If the work exceeds what the user approved, escalate as scope change (`AGENTS.md`).

### Stage 5: migrate and contract

Migration moves callers and data from old to new in small batches, with tests after each. Contract removes what was only needed for the migration.

- **Feature flags during migration.** If a toggle selects old or new behaviour, "off" means legacy behaviour and "on" means new, both states are tested, and the toggle has an expiry and a removal step. Release toggles are short-lived; treat them as inventory to keep low.
- **Data and schema.** Use expand, migrate, contract: add new structures beside the old, move data and code over, remove the old structures last. Migrations are reversible or have a stated recovery plan, an applied migration is never edited, and running a migration is a gated action. The contract migration, which removes the old structure, is the point where rollback becomes harder, so request approval for it separately and confirm a backup or recovery path first (skill `database-engineering` for the design).
- **Shared resources.** While old and new coexist, both must be able to reach shared data stores and services; plan for it.
- **Anti-corruption.** When the new code must talk to old semantics, put a translation layer between so the new design does not absorb old conventions.
- **Contract step evidence.** After removing the old path: `git grep -n "<old symbol>"` returns nothing; the old module, adapter and flag are deleted; the full checks pass. Deleting files inside the task's scope is part of the task; deleting anything else needs approval.

### Stage 6: rollback

Write the rollback before the first risky step; if no rollback exists for a step, stop and ask.

| Situation | Rollback |
|---|---|
| Step in the working tree, not yet committed | Discard that step's changes (a destructive command: confirm the working tree contains only that step first) |
| Step committed locally | Revert that commit with a new commit (skill `git-version-control`); never rewrite shared history without approval |
| Behind a toggle | Switch the toggle to the legacy state; the old path still exists until the contract step |
| Strangler fig | Route traffic back to the legacy system at the facade; the old system stays until retired |
| Schema in the expand or migrate phase | The old structure still exists, so return to it; rollback is possible until the legacy objects are removed |
| After the contract step | Restore from the recovery path approved earlier; this is why contract is approved separately |
| Deployed change | Follow the deployment rollback; mechanics belong to `devops-deployment`, and deploying and rolling back in production are gated actions |

Rollback triggers (decide them in advance): a regression the loop limit cannot resolve; a behaviour difference found in the runtime comparison; a measured performance regression beyond the agreed threshold; a scope change the user has not approved. After the loop limit in `AGENTS.md`, stop, mark the task `blocked`, and give the user the options (continue with a revised plan, roll back to the last checkpoint, stop at a safe stopping point).

### Stop conditions and partial completion

Because every step leaves the system working, the work can stop at any checkpoint. Record the last checkpoint, which transitional code remains and why, and the remaining steps in the task file and `docs/TASKS.md`. With a strangler fig, pausing is expected: the facade routes the remaining functionality to the legacy system. The task is `done` only when the contract step is finished, or when the user accepts the stopping point and the transitional code that remains.

### Closing the task

All quality gates in `AGENTS.md` are met; the transitional inventory is empty or accepted; `docs/ARCHITECTURE.md` describes the new structure (architect); an ADR records the strategy (architect); README and CHANGELOG are updated where setup or user-visible behaviour changed (implementer; usually only when something visible changed); `docs/TASKS.md` and `docs/MEMORY.md` are updated (orchestrator). Report with the checkpoint ledger.

## Examples

### Plan: replace a homegrown HTTP client with a library (branch by abstraction)

```
Goal: All outbound HTTP goes through the new `http-lib` client; the old client is deleted.
Non-goals: changing retry or timeout behaviour; changing any endpoint contract.
Invariant: no behaviour change; the 31 tests in tests/http/ pass unchanged; a dev-only flag
  HTTP_CLIENT=new|old selects the supplier for comparison runs.
Strategy: branch by abstraction. Reason: 14 call sites, one supplier, no external interface.

Step 1: add src/http/client.ts (interface: get, post) wrapping the OLD client. Verify: build, all tests. Rollback: revert commit.
Step 2: migrate callers in src/billing (3 sites) to the interface. Verify: tests/billing. Rollback: revert commit.
Step 3: migrate callers in src/orders (5 sites). Same verification and rollback.
Step 4: migrate remaining callers (6 sites). Same.
Step 5: [approval: add dependency http-lib] implement src/http/newClient.ts behind the interface; flag selects it. Verify: both flag states pass the suite. Rollback: flag off, revert commit.
Step 6: switch the default to new; run comparison. Rollback: set flag to old.
Step 7 (contract): delete old client, flag and, if unused, the interface wrapper. Verify: git grep -n "oldHttpClient" empty; all checks pass. Rollback: revert commit.

Transitional inventory: wrapper in client.ts (removed step 7), HTTP_CLIENT flag (removed step 7).
Safe stopping points: after steps 1-4 (abstraction only), after step 6.
```

### Parallel change on a function signature

```js
// Before: callers pass x and y
function move(x, y) { /* ... */ }

// Expand: new form beside the old; old delegates to new, so behaviour is identical
function moveTo(point) { /* implementation moved here */ }
function move(x, y) { return moveTo({ x, y }); }

// Migrate: update callers to moveTo(...), a few per step, tests after each.
// Contract: when `git grep -n "move("` shows no callers, delete move().
```

### Characterisation test (illustrative)

```js
// Pins today's behaviour, including the odd rounding, before restructuring pricing code
test("price rounds half up per line before summing (current behaviour)", () => {
  assert.equal(total([{ cents: 1005, qty: 1 }, { cents: 1005, qty: 1 }]), 2020);
});
```

If the rounding looks wrong, a follow-up is recorded; the characterisation test stays as is during the refactoring.

### Checkpoint ledger entry

```
Step 3 checkpoint: tests 149 pass / 0 fail / 0 skipped (baseline 142 + 7 characterisation); lint 0 errors;
types 0 errors; build ok. git diff --stat: 5 files, all in src/orders and tests/orders. Contracts: no change.
Transitional inventory: unchanged. Rollback: revert commit for step 3. Decision: proceed to step 4.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Starting without a safety net | Behaviour changes go unnoticed | Baseline, characterisation tests, seams, and proof the net can fail |
| Mixing a feature or bug fix into the refactoring | The invariant is lost; review and rollback become unclear | Separate tasks; pin the defect and list a follow-up |
| One big-bang change | One failure blocks everything and cannot be reverted cleanly | Small steps, each buildable and revertible |
| Editing tests to make steps pass | Hides behaviour change | Never weaken, skip or delete a test; move assertions to public behaviour in a separate step |
| No contract step in the plan | Two versions live forever | Put the removal in the plan and check it at close |
| Rollback written after trouble starts | Too late to choose well | Write rollback per step first |
| Running the destructive schema step with the rest | Rollback gets harder at once | Approve the contract migration separately with a recovery path |
| Facade or adapter treated as permanent | Transitional code becomes unowned complexity | Inventory it with a removal step |
| Parallel edits to the same files | Lost changes | One writer per file; serialise overlapping steps |
| Counting a regression as a fresh start | Hides repeated failure | Keep the loop counter across fixes; stop at the limit |

## Checklist

- [ ] Scope, non-goals and the "no behaviour change" invariant are recorded and the user confirmed them.
- [ ] Baseline results are recorded, including pre-existing failures.
- [ ] Behaviour in scope is pinned by tests, and a deliberate local change was shown to make a test fail and then reverted.
- [ ] The strategy is named with its reason, and an ADR exists if it is an architectural decision.
- [ ] Every step has a verification command and a rollback, and leaves the build green.
- [ ] The transitional inventory lists each shim, adapter, flag and duplicate with its removal step.
- [ ] Gated actions in the plan (dependencies, migrations, merges, deployments) have approval points.
- [ ] After each step, results equal the baseline plus new tests, `git diff --stat` matches the step's scope, and no test was edited to pass.
- [ ] After the contract step, `git grep -n "<old symbol>"` returns nothing and all checks pass.
- [ ] Review ran at the end (and at milestones for large plans) and documentation sync is complete.

## Verify with context7 and gh_grep

- **context7:** for the dependency being replaced or introduced, query "`<new library>` `<version>` migration guide from `<old library>`", "`<new library>` `<version>` default timeouts, retries and error types" (to confirm behaviour parity), and for the test runner "`<test framework>` `<version>` snapshot or approval testing" if characterisation uses it.
- **gh_grep:** search literal code for how maintained projects structure the transition: `class .*Adapter`, `implements .*Gateway`, `process.env.USE_NEW_`, `featureFlags.isEnabled(`, `@deprecated Use`, and `strangler` in directory names or comments.

## Sources

- Strangler Fig, martinfowler.com (gradual replacement beside the legacy system, seams, transitional architecture, risks of full replacement): https://www.martinfowler.com/bliki/StranglerFigApplication.html
- Strangler Fig pattern, Microsoft Azure Architecture Center (facade phases, considerations, when not to use): https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
- Branch By Abstraction, martinfowler.com (steps and purpose, flags for comparison): https://www.martinfowler.com/bliki/BranchByAbstraction.html
- Parallel Change, martinfowler.com (expand, migrate, contract; interfaces and schemas): https://www.martinfowler.com/bliki/ParallelChange.html
- Legacy Seam, martinfowler.com (definition of a seam and enabling point): https://martinfowler.com/bliki/LegacySeam.html
- Refactoring, refactoring.com (behaviour-preserving restructuring in small steps): https://refactoring.com/
- Feature Toggles (aka Feature Flags), martinfowler.com (release toggles, removal, testing both states): https://www.martinfowler.com/articles/feature-toggles.html
