---
name: sdlc-workflows
description: "Use for end-to-end procedures: feature development, bug fixing, onboarding an existing project and large codebase refactoring."
---

# SDLC Workflows

Run a change from request to verified, documented result by following one playbook: feature, bug fix, onboarding or refactoring. Each playbook sequences the other skills and roles; the rules for triage, handoff, verification, approvals and documentation sync stay in `AGENTS.md`.

## When to use

- A request adds or changes behaviour and needs the stages from request to done (feature development).
- Something behaves wrongly and must be reproduced, diagnosed, fixed, covered by a regression test and documented (bug fixing).
- The repository is new to the agents: `AGENTS.md` still holds placeholders, `docs/` is missing or stale, or commands are unknown (project onboarding).
- A large structural change must keep behaviour identical and ship in small, reversible steps: replacing a subsystem, library or interface (codebase refactoring).
- The orchestrator needs the stage order, exit checks and per-stage skills to write delegation briefs, or the implementer is told to follow one of these procedures.

## Do not use for

- Triage classes, the delegation brief, the standard report, quality gates, approval gates, documentation sync and the loop limit: these are rules in `AGENTS.md`. Follow them there; this skill never restates them differently.
- Root-cause technique, bisection and instrumentation: load `debugging`.
- Requirements and acceptance-criteria writing: load `requirements-engineering`; task slicing and estimates: load `product-technical-planning`.
- Design, patterns and ADR rules: load `system-architecture`.
- Test-first technique and test design: load `test-driven-development`; test levels and coverage: load `testing-strategy`.
- Branches, commits, pull requests and `gh` commands: load `git-version-control`.
- Pipelines, deployment, release and rollback mechanics: load `devops-deployment`.
- README, changelog and docs prose conventions: load `technical-documentation`.
- Updating `docs/TASKS.md` and `docs/MEMORY.md`: load `project-memory`.
- Code review and security audit technique: load `code-review` and `security-engineering`.

## Research: context7 and gh_grep

- You MUST consult **context7** before you rely on a library, framework, SDK, CLI tool or cloud API in any stage: when onboarding reveals the versions in the manifest or lockfile (query their current commands and conventions), when a bug involves a library behaviour (query "`<library>` `<version>` `<function>` behaviour and known issues"), and when a refactoring replaces or upgrades a dependency (query "`<library>` migration guide from `<old>` to `<new>`", "`<tool>` run tests command and flags").
- You MUST search **gh_grep** when a pattern is unfamiliar or documentation is ambiguous. Search literal code: `"scripts": {` to see how projects expose commands, `featureFlags.isEnabled(` or `if (flags.` for toggle usage, `class .*Adapter` for abstraction layers, and the verbatim error message for a bug.
- Process steps that only touch project-internal files, task records and `AGENTS.md` need neither; state that in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/feature-development.md](references/feature-development.md) | Delivering new or changed behaviour: stage order, inputs, outputs and exit checks from request to done, slicing, and flags for unfinished work. |
| [references/bug-fixing.md](references/bug-fixing.md) | Something is broken: reproduce, diagnose, fix, add a regression test, verify, document; includes bug classes and security bugs. |
| [references/project-onboarding.md](references/project-onboarding.md) | `AGENTS.md` has placeholders, commands are unknown, or `docs/` must be bootstrapped from an existing codebase without inventing facts. |
| [references/codebase-refactoring.md](references/codebase-refactoring.md) | A large change with no behaviour change: safety net, incremental plan (strangler, branch by abstraction, parallel change), checkpoints and rollback. |

## Workflow

1. **Pick the playbook.** Match the request to one reference. If it mixes kinds of work (for example a feature plus a refactor, or a bug fix plus cleanup), split it into separate tasks and run one playbook per task, in the order that keeps each verifiable. If `AGENTS.md` still holds placeholders, onboarding comes first.
2. **Classify and resume.** Apply `AGENTS.md` (Triage) and state the class and risk in one line. Check `docs/TASKS.md`, `docs/MEMORY.md` and `.agents/tasks/` and resume matching work instead of opening a duplicate.
3. **Open the task** from the task template with the goal, constraints, assumptions and an observable acceptance criterion for every outcome.
4. **Run the playbook stage by stage.** Each stage in the reference lists who acts, the input, the output and an exit check. Do not start the next stage until the exit check has evidence. Skipping a stage is allowed only when it reduces no real risk; record the reason in the task file.
5. **Delegate one outcome per brief** using the `AGENTS.md` (Handoff) brief. Name the skills each agent loads, at most 3 per agent per task, using the stage tables in the references.
6. **Verify each report** against its acceptance criteria before the next stage, then loop findings and failures as `AGENTS.md` (Quality gates) requires.
7. **Sync documentation and memory** per `AGENTS.md` (Documentation sync) before reporting done. Record the per-file result.
8. **Close with evidence**: the stage ledger (stage, command or check, result), what was not done, and follow-ups.

Role differences:

- **Orchestrator.** Owns steps 1 to 8: chooses the playbook, writes the task file, sequences stages, writes complete briefs, checks evidence, runs the loop and escalation rules, updates records. Does not write code, tests, designs or reviews. Loads `project-memory` and this skill.
- **Implementer.** Executes the code stages of a playbook for one brief at a time: baseline, research, smallest complete change, tests it needs, verification with the `AGENTS.md` commands, diff self-review, README and CHANGELOG. Because the implementer's core skill is `languages-clean-code`, loading this skill uses one of the remaining two slots; the orchestrator should put stage-specific instructions in the brief and name this skill only when the whole procedure matters (for example a multi-step refactoring). The implementer never judges its own work as reviewed, never edits task files or specs, and reports a wrong plan instead of redesigning.
- **Other roles** (architect, tester, reviewer, security-auditor, debugger) do not load this skill. They receive stage briefs and return the standard report.

## Standards

- One task, one playbook. A refactoring contains no behaviour change, and a bug fix contains no unrelated cleanup; mix them only as separate tasks.
- `AGENTS.md` wins over any playbook step. If they differ, follow `AGENTS.md` and report the difference.
- Every stage ends with an exit check backed by evidence (a command and its result, or a file and line). A claim is not an exit check.
- Record a baseline (tests, lint, type-check, build) before changing code, and list pre-existing failures so none is attributed to the change.
- Reproduce before you fix. A bug fix needs a regression test that fails before the fix and passes after it, with both results recorded.
- Every step leaves the system buildable, tested and revertible on its own. Steps that cannot ship alone are split further.
- Temporary structure (facades, adapters, compatibility shims, flags) is listed in the plan with a named removal step; the task is not done until it is removed or the user accepts it.
- State the rollback before the first risky step. A step with no rollback is a reason to stop and ask.
- Onboarding writes only what evidence supports. Each fact in a doc carries a source path or is marked unknown for the user to confirm. Never guess commands, purposes or decisions.
- Fill `AGENTS.md` placeholders only from evidence and only after the user approves the exact text.
- Never read or print secrets or `.env` files; take variable names from `.env.example`.
- Gated actions (migrations, deployments, pushes, merges, dependency changes, deleting data, CI/CD changes) are never implied by a playbook step. Ask first with action, target, risk and rollback.
- Never weaken, skip or delete a test to make a stage pass.
- Report unrelated problems as follow-ups; do not fix them inside the task.
- Load at most 3 skills per agent per task and route technique questions to the owning skill instead of teaching them here.
- A later source change invalidates earlier test, review and audit results for the affected area; repeat those stages.

## Verification

- [ ] The task file names the playbook, class, risk and an observable acceptance criterion per outcome.
- [ ] Each stage has a ledger line with its evidence: `git status --short` and `git diff --stat` for what changed, and the exact test, lint, type-check and build commands from `AGENTS.md` with their results.
- [ ] Baseline results exist before the first code change, and any pre-existing failure is listed.
- [ ] For a bug fix, the regression test's failing run (before) and passing run (after) are both recorded.
- [ ] For a refactoring, the rollback is written down per step and `git grep -n "<removed symbol or flag>"` returns nothing after the contract step.
- [ ] For onboarding, every command written into `AGENTS.md` was run and its result recorded, and `grep -n "<" AGENTS.md` shows no remaining placeholder in the Project block.
- [ ] No gated action happened without a recorded user approval for that exact action.
- [ ] The documentation sync table in the task file has a result for every file.
- [ ] Skipped stages and unresolved findings are listed with their reasons.

## Output

Return the standard report from `AGENTS.md` (Handoff) and close to the user in the orchestrator report format.

- **Evidence:** the stage ledger, with commands and results (baseline, failing-then-passing test, verification commands, loop counts).
- **Research:** the context7 and gh_grep queries used and the version checked, or "none needed: project-internal process work".
- **Docs impact:** the affected files and their owners. Onboarding and features can touch `docs/PRD.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md` and `docs/adr/` (architect); `README.md` and `CHANGELOG.md` (implementer); `docs/TASKS.md` and `docs/MEMORY.md` (coordinator). Changes to `AGENTS.md` or `CLAUDE.md` go to the user for approval first.
- **Open questions and follow-ups:** unrelated problems found, skipped stages, accepted gaps.
