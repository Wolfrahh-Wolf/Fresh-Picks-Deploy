---
name: product-technical-planning
description: "Use when writing a PRD or user stories, slicing work into tasks, sequencing dependencies or estimating effort and risk."
---

# Product Technical Planning

Turn agreed requirements into a PRD, vertically sliced stories, a sequenced task plan and an honest estimate. Every plan you produce must be small enough to verify task by task and explicit about what is still uncertain.

## When to use

- Writing or updating `docs/PRD.md`: problem, goals, success measures, non-goals, requirement tables.
- Writing user stories or backlog items, or splitting one that is too large to plan.
- Breaking a Standard or Complex request into the `Plan`, `Files in scope` and `Acceptance criteria` sections of a task file.
- Ordering tasks by dependency, risk and learning value.
- Sizing work, giving a range, listing risks, or deciding that a spike must come first.
- Checking a draft plan against the 12-task limit before it goes to the user.

## Do not use for

- Eliciting requirements, resolving ambiguity, writing or checking acceptance criteria, setting measurable quality targets: load `requirements-engineering`.
- Choosing, comparing or proving a technology, and the rules for running a spike or proof of concept: load `technical-research`.
- Component boundaries, design trade-offs and ADRs: load `system-architecture`.
- Schema, query and migration design: load `database-engineering`. Endpoint and contract design: load `api-engineering`.
- Threat modelling and audit: load `security-engineering`.
- Prose conventions for `ARCHITECTURE.md`, `DB.md`, `DESIGN.md` and the changelog: load `technical-documentation`.
- Editing `docs/TASKS.md` and `docs/MEMORY.md`: load `project-memory` (coordinator only).

## Research: context7 and gh_grep

- You MUST consult **context7** before a plan or PRD names a library, framework, SDK, CLI or cloud API as a dependency or constraint, and before you size work that relies on what such a tool can do. Check the project's manifest or lockfile first and query that version. Useful queries: "does `<library>` `<version>` support `<capability>`", "`<library>` migration guide from `<old>` to `<new>`", "`<service>` rate limits and quotas", "`<framework>` breaking changes in `<version>`".
- You MUST search **gh_grep** when an integration or pattern in the plan is unfamiliar to you and its effort cannot be sized from the repository alone. Search literal code, not a description. Useful searches: the exact constructor or call the integration needs, the configuration key you expect, the literal error text a similar integration reports.
- Slicing stories, ordering tasks, writing a PRD section and relative sizing against tasks already in the repository need neither. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/prd.md](references/prd.md) | Creating or changing `docs/PRD.md`; writing goals, success measures, non-goals or requirement rows; syncing the PRD after a change. |
| [references/user-stories.md](references/user-stories.md) | Writing a story, testing it against INVEST, or splitting a story that is too big or not a vertical slice. |
| [references/task-breakdown.md](references/task-breakdown.md) | Filling a task file's `Plan`, `Files in scope` and `Acceptance criteria`; ordering tasks; mapping dependencies; deciding when to stop at 12 tasks. |
| [references/estimation.md](references/estimation.md) | Giving a size or range, building a risk list, deciding on a spike, or re-estimating after new information. |

## Workflow

Only the architect loads this skill. You may edit spec docs and the plan sections of a task file. You never edit source, tests, `docs/TASKS.md`, `docs/MEMORY.md`, `AGENTS.md` or the task file's status, evidence, findings or decisions; the coordinator owns those.

1. **Orient.** Read the brief, the task file, `AGENTS.md`, `docs/PRD.md`, `docs/MEMORY.md` and the code the change touches. Check `docs/TASKS.md` for existing work to resume. Do not plan from file names alone.
2. **Confirm the input is plannable.** If requirements are unclear, untestable or contradictory, stop and load `requirements-engineering` first. After 2 failed clarification attempts on a conflict, escalate with the quoted statements.
3. **Pick the artefact.** PRD change: `references/prd.md`. Story work: `references/user-stories.md`. Plan or sequencing: `references/task-breakdown.md`. Any size, range or risk statement: `references/estimation.md`. Most requests need two of them.
4. **Write product intent first.** Update `docs/PRD.md` so goals, non-goals and requirement rows exist before tasks do. Leave Status as draft; only the user approves.
5. **Slice vertically.** Split every large item into thin end-to-end slices that each deliver something observable. Record what you defer as non-goals or open questions, not as silent omissions.
6. **Decompose into tasks.** One outcome, one verification, one agent per task. Name dependencies by task ID and the observable output each one provides.
7. **Sequence.** Put the biggest unknowns and the thin end-to-end slice first, then enhancements. Keep the plan linear unless tasks touch disjoint files; the coordinator decides on any parallel work.
8. **Estimate and flag risk.** Give ranges with a basis, list assumptions and top risks, and put a time-boxed spike ahead of any item you cannot size. For spike execution rules load `technical-research`.
9. **Gate the size.** More than 12 tasks, or scope more than 50% above the brief: stop and re-evaluate with the coordinator before finishing the plan.
10. **Flag approval and audit needs.** High-risk areas per `AGENTS.md` need security-auditor; migrations need a rollback step; new or majorly upgraded dependencies, deployments and data deletion are user-approval gates. Say so in the Summary.
11. **Self-check and report** using the Verification list and the standard report.

When the request is only an estimate or a story review, change no files and answer in the report.

## Standards

- Every plan task has one outcome, one verification a person can run or observe, and can be completed and verified without any later task.
- A plan never exceeds 12 tasks without the coordinator's agreement.
- Stories are vertical slices of user-visible value; a layer-only item is a task, not a story, and carries its own check.
- Testing is part of every story and task. Never plan "write tests" as a final separate item.
- Every dependency names task IDs, is acyclic, and states the observable output it needs.
- Order puts unknowns and the first thin end-to-end slice before enhancements and polish.
- No file is in scope for two tasks that could run at the same time (one writer per file).
- `docs/PRD.md` keeps goals, non-goals and success measures; each success measure has a target and a way to measure it, or is marked **open**.
- PRD requirement IDs are unique and are never renumbered or reused.
- The PRD states what and why; how belongs in `DESIGN.md`, `ARCHITECTURE.md`, `DB.md`, `API-CONTRACTS.md` and `docs/adr/`.
- Estimates are ranges with a stated basis and assumptions. They are forecasts, never commitments, and are never converted to dates without measured history.
- Anything that cannot be sized becomes a time-boxed spike or an **open** question with an owner.
- Status in the PRD stays `draft` until the user approves; you never mark requirements approved.
- Task file edits are limited to `Plan`, `Files in scope` and `Acceptance criteria`.
- Every assumption is marked, and every unconfirmed claim is marked **unverified**.
- Tasks that deploy, publish, push, run migrations, delete data, add paid services or add dependencies are marked as needing user approval.

## Verification

Commands are POSIX; use the shell's equivalent on Windows. Do not report `done` while any box is unchecked.

- [ ] Plan has at most 12 tasks: count the numbered rows under `Plan` in the task file.
- [ ] Every task row has an outcome, a `Needs` entry (a task ID or `none`), a verification and a size: read the table and find any blank cell.
- [ ] No dependency cycle: every ID in a `Needs` cell appears earlier in the plan.
- [ ] Every path under `Files in scope` exists or is marked new: run `ls <path>` or search the repository for it.
- [ ] No file path appears under two tasks that are marked parallel-safe.
- [ ] PRD IDs are unique: search `docs/PRD.md` for repeated IDs (`grep -oE '^\| (FR|NFR)-[0-9]+' docs/PRD.md | sort | uniq -d` prints nothing).
- [ ] No unfilled fields remain in `docs/PRD.md` or the plan: search both for angle-bracket fields and the phrase "to be decided".
- [ ] Every estimate has a low, a likely and a high value, a basis and at least one assumption.
- [ ] Every item you could not size has a named spike or an **open** question.
- [ ] Every acceptance criterion in the plan is observable and covers an error or edge case, or is marked **open**.
- [ ] The Summary states task count, critical path, estimate range, top risks and whether a security audit is required.

## Output

Use the standard report from `AGENTS.md`. Skill-specific content:

- **Summary:** slice strategy, task count, critical path, estimate range with basis, top three risks, spikes planned, deferred items, and whether security-auditor is required.
- **Evidence:** the checks from Verification and their results; which files you counted or searched.
- **Research:** the context7 and gh_grep queries used, or the statement that the plan was project-internal and needed neither.
- **Docs impact:** list each file below as updated or no change, with a reason.

| File | Owner | When this work affects it |
|---|---|---|
| `docs/PRD.md` | architect | Goals, non-goals, requirements, constraints or open questions changed. |
| Task file `Plan`, `Files in scope`, `Acceptance criteria` | architect | Always, for Standard and Complex work. |
| `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md`, `docs/adr/` | architect | Planning exposed a design change; make it with the owning skill. |
| `docs/TASKS.md` | coordinator | Report new tasks, a re-scope or a blocked plan; do not edit it. |
| `docs/MEMORY.md` | coordinator | Report a durable constraint or decision learned; do not edit it. |
| `README.md`, `CHANGELOG.md` | implementer | Not edited by planning; report if a planned change will affect them. |
