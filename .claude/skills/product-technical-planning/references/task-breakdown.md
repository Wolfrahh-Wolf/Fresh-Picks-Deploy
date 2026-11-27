# Task Breakdown, Dependencies and Sequencing

How to decompose a slice of work into independently verifiable tasks, map dependencies, sequence them and fill the task file's plan sections; assumes the RelayCrew task template and `AGENTS.md`, the Scrum Guide (November 2020 edition), Wake's SMART task criteria (2003) and the Kanban Guide (May 2025 edition); checked 2026-11-26.

## Contents

- What a plan task is
- The task test
- Decomposition procedure
- Size limits and the 12-task gate
- Dependencies
- Sequencing rules
- Parallel work and file ownership
- Gates, risk and audit flags
- Task file plan sections
- Re-planning

## Guidance

### What a plan task is

A plan task is one outcome that one agent can complete and prove in one delegation. It is smaller than a story and is for the people doing the work, not for the customer.

- Stories (see [user-stories.md](user-stories.md)) say what a user can do. Tasks say what to change, in what order, and how to prove each step.
- The Scrum Guide describes developers planning the work for a selected item, often by decomposing it into work items of one day or less. Treat that as the right granularity: small enough that a stuck task shows up quickly.
- The architect fills `Plan`, `Files in scope` and `Acceptance criteria`. The coordinator owns status, evidence and findings. Do not touch those.

### The task test

Adapt Wake's SMART list. A task passes only if every answer is yes.

| Check | Question | Failing example |
|---|---|---|
| Specific | Does it name one outcome and the place it happens? | "Improve reminders" |
| Measurable | Is there a command or observable result that says done? | "Make it work" |
| Achievable | Can one agent do it with the listed inputs and files? | A task needing a decision the user has not made |
| Relevant | Does it trace to an acceptance criterion or a requirement ID? | "Tidy imports" in a feature plan |
| Time-boxed | Is its size small or medium, and does a failed attempt show quickly? | A task sized "large" |

Independently verifiable means: if every later task were cancelled, you could still run the check for this one, with only its prerequisites done, and get a clear pass or fail. If the check needs a later task to exist, the task is mis-cut.

### Decomposition procedure

1. Start from one story or one vertical slice and its acceptance criteria. Do not decompose a whole PRD in one pass.
2. Walk the slice through the system and list every place it touches: interface, logic, storage, integration, configuration. Name the files if you can find them in the code.
3. Cut vertically first. The earliest tasks should produce a thin end-to-end path, even if crude.
4. Add enabling tasks only when a later task cannot be verified without them (a schema change, a contract, a configuration key). Each enabling task still needs its own check.
5. Put the verification inside the task that creates the behaviour. Do not plan a final "write all tests" task. For test-first ordering load `test-driven-development`.
6. Give each task one verification: a command from `AGENTS.md` (test, lint, build) scoped narrowly, or an observable result.
7. Count tasks. If you pass 12, stop and re-scope (see below).
8. Read the list as the implementer would. Anything that would make them ask a question becomes a note, an assumption or an open question.

Do not add tasks for documentation sync. Syncing documentation runs after each successful operation as a workflow stage under `AGENTS.md`; planning only names which docs a task will affect.

### Size limits and the 12-task gate

- A task is `S` (a few files, clear change), `M` (several files or one unfamiliar integration) or `L` (should be split unless it is a single indivisible step). Anything bigger than `L` must be split or preceded by a spike. Sizing rules are in [estimation.md](estimation.md).
- `AGENTS.md` and the architect role set a limit: if the plan exceeds 12 tasks, re-evaluate scope with the coordinator before presenting it. Typical resolutions: take the first vertical slice as this task file and defer the rest as new task files; or merge tasks that share a check.
- If you discover the work is more than 50% larger than the brief described, escalate before finishing the plan.
- A task file is not a place to hold a backlog. Longer work becomes several task files, each with its own goal.

### Dependencies

Write every dependency as a task ID plus the observable output you need from it.

| Type | Example | How to express |
|---|---|---|
| Output dependency | T3 needs the endpoint T2 exposes | `Needs: T2 (endpoint answers 200 for a valid request)` |
| Data dependency | T4 needs the schema change applied | `Needs: T1 (migration applied on a test copy)` |
| Decision dependency | T5 needs the user to choose a rule | `Needs: Q1 answered`; the task stays blocked until then |
| Approval gate | T6 runs a migration | `Gate: user approval` (see below) |
| Soft dependency | T7 is easier after T2 but not blocked | Note it; do not list it as `Needs` |

Rules:

- Dependencies point backwards only. The graph must be acyclic; if two tasks need each other, they are one task or a missing third task sits between them.
- Hard dependencies on external parties or unmade decisions go to the front of the plan or become open questions. They are the usual cause of idle time.
- Define interfaces before the work on either side. A contract task (documented in `docs/API-CONTRACTS.md` through `api-engineering`) lets two later tasks be cut independently.
- Do not create a dependency just to force a preferred order. Use sequencing for preference and `Needs` for necessity.
- Identify the critical path: the longest chain of hard dependencies. Name it in the Summary.

### Sequencing rules

Apply in this order; later rules break ties for earlier ones.

1. **Unblock and learn first.** Spikes, decisions and external dependencies go to the front. Uncertainty narrows only when someone decides or tries something (Construx), and a late surprise costs more than an early one.
2. **Thin end-to-end slice next.** The first demonstrable behaviour proves the integration path and gives the user something to react to.
3. **Risky work early, behind its prerequisites.** Migrations, authentication changes, new external input and new dependencies are high risk in `AGENTS.md`. Place them as soon as their `Needs` allow, so rework is cheap.
4. **Value order for the rest.** Enhancements follow the PRD's `must`, `should`, `could` order.
5. **Cheap and low-risk last.** Convenience and polish at the end can be dropped if scope has to shrink.

Test the order: if the plan were cut after any task, the system should still work and the delivered part should be demonstrable.

### Parallel work and file ownership

- `AGENTS.md` delegates one outcome at a time and allows one writer per file. So write the plan as a linear order by default.
- Mark `Parallel-safe with: T5` only when the two tasks have no shared files, no data dependency and no shared decision. The coordinator decides whether to run them in parallel.
- Reviewer and security-auditor reviews can run in parallel with each other after implementation. That is the coordinator's workflow, not something to encode as tasks.
- Controlling how much is in progress at once helps flow (Kanban Guide). A plan with many half-finished tasks is worse than a short plan finished in order.

### Gates, risk and audit flags

- Any task that deploys, publishes, pushes, merges, runs migrations, deletes data or files outside the task, adds a paid service, adds or majorly upgrades a dependency, or changes secrets, access control or CI/CD needs user approval before it starts. Mark it `Gate: user approval` and state the action, target, risk and rollback in the task. **Warning:** never write a plan step that performs these actions automatically.
- Migration tasks must state both the forward step and the rollback step, and who verifies the rollback. Design of both belongs to `database-engineering`.
- For high-risk areas (authentication, authorization, sessions, payments, personal or sensitive data, cryptography, secrets, file upload, new external input surfaces, dependencies, database migrations, infrastructure, CI/CD), the plan is at least Standard and needs security-auditor. State that in the Summary; the coordinator records it in the task file.
- Mark criteria you could not make testable as **open**, and list the people who must answer.

### Task file plan sections

You write three sections of `.agents/tasks/<kebab-slug>.md`. Keep the rest as the template defines.

- **Plan:** a table of tasks (below), plus the order, critical path and any parallel-safe pairs, in a few lines.
- **Files in scope:** every path a task may change, grouped by task ID; paths that must not change under "Out of scope".
- **Acceptance criteria:** observable checks for the whole task file, one per line, each with an error or edge case where relevant. Rules for writing them belong to `requirements-engineering`.

Plan table columns: `ID | Outcome | Needs | Verify | Size`. Add `Gate` or `Risk` columns only when they apply.

### Re-planning

- Update the plan when you learn something that changes order, size or scope, and report what changed and why. Keep it a description of what is true now.
- After two failed fix-and-verify loops on a task, `AGENTS.md` says to stop and mark the task blocked; propose replanning options to the coordinator rather than retrying.
- A source change invalidates earlier test, review and audit results for the affected area. If a re-plan reorders tasks, state which earlier verification no longer holds.
- Do not change approved acceptance criteria to make a task pass. Report it and ask.

## Examples

### Bad plan to good plan

Bad:

```
1. Create reminder database
2. Build reminder API
3. Build reminder screen
4. Write tests
5. Update docs
```

Why it fails: it is cut layer by layer so nothing is demonstrable until task 3, "write tests" comes last with no check, "update docs" duplicates documentation sync, and nothing names dependencies, files or sizes.

Good (excerpt of the Plan section):

```
Plan (order T1 to T6; critical path T2, T3, T4, T5; T1 runs beside T2)

| ID | Outcome | Needs | Verify | Size |
|---|---|---|---|---|
| T1 | Spike: confirm the email provider can send scheduled messages and report its limits (time-box: one task) | none | Written answers to the two spike questions in the Summary | S |
| T2 | Migration: add reminder rule and reminders-sent tables. Gate: user approval before running on any shared database | none | Applies to a test copy; rollback verified on a test copy | M |
| T3 | Store and read one reminder rule (days after due date) | T2 | `<test command> reminders/rules` passes; rule survives a restart | S |
| T4 | Send one reminder email for an overdue invoice on the due day plus N | T1, T3 | Integration test sends to a test inbox; log shows one message per invoice | M |
| T5 | Make the job idempotent: a second run sends nothing | T4 | Test runs the job twice and asserts one message | S |
| T6 | Billing admin can enable and disable the rule in the admin screen | T3 | Browser check against a local build shows the toggle persists | M |

Parallel-safe: T1 with T2 (no shared files); T5 with T6 (disjoint files).
```

### Filled task file sections

```
## Plan
See the table above. Critical path: T2, T3, T4, T5.
Risks: provider limits unknown until T1 (could force a different send model); T2 touches shared tables (needs approval and a verified rollback).

## Files in scope
- T2: migrations/<new migration pair>
- T3: src/reminders/rules.*, tests/reminders/rules.*
- T4: src/reminders/send.*, src/jobs/reminders.*, tests/integration/reminders.*
- T5: src/jobs/reminders.* (same file as T4, so run after T4)
- T6: src/admin/reminders/*
Out of scope: customer-facing email templates, any change to payment code.

## Acceptance criteria
- [ ] With the rule enabled, an overdue invoice receives exactly one reminder on the due day plus N.
- [ ] Running the job twice in one day sends no second message for the same invoice.
- [ ] Disabling the rule stops new reminders at the next run; messages already sent are unaffected.
- [ ] A provider error does not lose the reminder: it is retried on the next run and the failure is logged.
- [ ] The migration rolls back cleanly on a test copy. (open: rollback owner not yet named)
```

### Dependency map and critical path

```
T1 (spike) -------------------+
                              v
T2 (migration) --> T3 ------> T4 --> T5
                    \
                     +--> T6
```

Critical path: T2, T3, T4, T5. T1 must finish before T4 starts but runs beside T2 and T3. T6 is off the path and parallel-safe with T4 and T5 only while their files stay disjoint.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Layer-by-layer tasks | Nothing demonstrable until the end; integration risk last | Cut a thin end-to-end path first |
| A final "write tests" task | Verification arrives after the fact and is easy to skip | Put the check inside each task |
| Tasks that cannot be verified alone | Review and testing wait on later work | Re-cut so each has a check using only prerequisites |
| More than 12 tasks | Plan is too large to verify and hold in mind | Take one vertical slice per task file |
| Hidden dependencies | Agents block each other or edit the same file | Write `Needs` with the required observable output |
| Cycles resolved by "do both together" without saying so | One task is secretly huge | Merge them explicitly into one task and size it |
| Same file in two tasks run at once | Overwrites and conflicting edits | Order them, or merge them |
| Planning approval-gated actions as automatic steps | Violates the approval rules | Mark `Gate: user approval` with action, target, risk, rollback |
| Documentation or status tasks in the plan | Duplicates sync and breaks ownership | Name affected docs; leave sync and status to the workflow |
| Editing the task file outside your three sections | Overwrites the coordinator's records | Limit edits to Plan, Files in scope and Acceptance criteria |

## Checklist

- [ ] The plan has at most 12 tasks, or the coordinator has agreed to more.
- [ ] Each task has one outcome, one verification, one size and a `Needs` entry.
- [ ] Each task passes the five-question task test.
- [ ] Each task can be verified with only its prerequisites done.
- [ ] No dependency points forward and there is no cycle.
- [ ] Every `Needs` names the observable output required.
- [ ] Unknowns, decisions and external dependencies are at the front.
- [ ] The first demonstrable behaviour appears early in the order.
- [ ] No file is in two tasks marked parallel-safe.
- [ ] Every migration task states forward and rollback steps.
- [ ] Every approval-gated action is marked with action, target, risk and rollback.
- [ ] The Summary states the critical path and whether a security audit is required.
- [ ] You changed only Plan, Files in scope and Acceptance criteria in the task file.

## Verify with context7 and gh_grep

- **context7:** before sizing or ordering a task around a library or service you did not write, query the version in the manifest: "`<library>` `<version>` supported way to run scheduled jobs", "`<service>` limits that affect batch sending", "migration guide `<old>` to `<new>`". A plan made only of project-internal changes needs no query; state that.
- **gh_grep:** when a task needs an integration you have not seen in this repository, search the literal call or configuration key in maintained projects (for example the exact constructor name and an adjacent test file name) to judge how many files the change usually touches. Use the count to size, not the code to copy.

## Sources

- The 2020 Scrum Guide (planning work for a selected item, decomposition into small work items, Definition of Done): https://scrumguides.org/scrum-guide.html
- INVEST in Good Stories, and SMART Tasks (SMART criteria for tasks), Bill Wake, 2003: https://xp123.com/invest-in-good-stories-and-smart-tasks/
- The Kanban Guide, May 2025 (controlling work in progress, flow metrics): https://kanbanguides.org/the-kanban-guide/2025.5
- Software Development's Cone of Uncertainty, Steve McConnell, Construx, version 1, 2010: https://www.construx.com/wp-content/uploads/2019/02/CxWhitePaper_ConeOfUncertainty.pdf
