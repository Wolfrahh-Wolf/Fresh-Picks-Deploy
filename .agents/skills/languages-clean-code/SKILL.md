---
name: languages-clean-code
description: "Use when writing or reviewing code in JavaScript, TypeScript, Python, Java or C++, applying SOLID, refactoring or managing dependencies."
---

# Languages and Clean Code

Produce idiomatic, readable, maintainable JavaScript, TypeScript, Python, Java and C++ that follows the project's own conventions. This is the language-craft core for the implementer and the language lens for the reviewer.

## When to use

- Writing or changing source code in JavaScript, TypeScript, Python, Java or C++.
- Reviewing a diff for idiom, type safety, ownership, error handling, async or concurrency correctness, naming and cohesion.
- Deciding whether SOLID applies to a design question, or whether applying it would be over-engineering.
- Making small, behaviour-preserving refactors that sit inside the task's scope.
- Adding, upgrading, removing or auditing a dependency: manifests, lockfiles, version ranges, licences.
- Choosing or changing language and compiler settings: `tsconfig.json`, `pyproject.toml`, build `release` level, CMake targets, warning and sanitizer flags.

## Do not use for

- Framework usage (React, Next.js, Express, Flask, FastAPI): load `frontend-engineering` or `backend-engineering`.
- Large multi-module refactoring procedure: load `sdlc-workflows`.
- Test code design, fixtures and doubles: load `test-driven-development`. For test levels and tooling, load `testing-strategy`.
- API contract and schema-validation design: load `api-engineering`. Database models and queries: load `database-engineering`.
- Vulnerability assessment of dependencies, threat modelling, secrets handling audits: load `security-engineering`.
- Branches, commits, pull requests: load `git-version-control`. CI pipelines and releases: load `devops-deployment`.
- Choosing between competing technologies beyond the dependency checklist in this skill: load `technical-research`.

## Research: context7 and gh_grep

- You MUST consult **context7** before you write, change or review any use of a library, framework, SDK or CLI tool, and before relying on a language feature that arrived in the last two major language versions. Check the project's manifest or lockfile first and query that version. Useful queries: "typescript tsconfig `moduleResolution` nodenext relative import extensions", "python `asyncio.TaskGroup` cancellation behaviour", "java `Executors.newVirtualThreadPerTaskExecutor` shutdown", "cmake `target_compile_features` `cxx_std_20`", "node.js ESM `package.json` `exports` and `type`".
- You MUST search **gh_grep** when an idiom, compiler flag, configuration or integration is unfamiliar, when documentation is ambiguous, or when a compiler or linter message is not explained by the docs. Search literal code. Useful searches: `Promise.allSettled(`, `AbortSignal.timeout(`, `asyncio.TaskGroup()`, `try (var executor = Executors.newVirtualThreadPerTaskExecutor())`, `target_link_libraries(` together with `PRIVATE`.
- Pure project-internal logic (renaming, extracting a function, reordering code you can read in full) needs neither. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs. Each reference is self-contained.

| Read | When |
|---|---|
| [references/javascript.md](references/javascript.md) | JavaScript or Node.js code: modules, async, equality and coercion traps, error handling. |
| [references/typescript.md](references/typescript.md) | TypeScript code or `tsconfig.json`: strictness, narrowing, generics, `unknown` over `any`, runtime validation at boundaries. |
| [references/python.md](references/python.md) | Python code: idioms, type hints, packaging, virtual environments, `asyncio`, common traps. |
| [references/java.md](references/java.md) | Java code: modern language features, collections, concurrency, exceptions, Maven or Gradle builds. |
| [references/cpp.md](references/cpp.md) | C++ code or CMake: ownership and RAII, memory safety, concurrency, warnings and sanitizers. |
| [references/solid.md](references/solid.md) | A design decision about responsibilities, abstraction or dependencies; naming and cohesion questions; judging whether SOLID is worth applying. |
| [references/refactoring.md](references/refactoring.md) | Cleaning up a smell inside the task's scope, or reviewing a refactor for behaviour preservation. |
| [references/dependency-management.md](references/dependency-management.md) | Adding, pinning, upgrading, removing or licence-checking a dependency; touching a manifest or lockfile. |

## Workflow

1. **Establish conventions and versions.** Read the `Project` and `Commands` lines in `AGENTS.md`, then the manifest and lockfile, the formatter and linter configuration, and two or three neighbouring files. Record the language version, the module system and the type-check, lint, test and build commands. Existing project conventions and `docs/` beat this skill, except where they are unsafe; then report the conflict instead of silently following or overriding it.
2. **Pick the references.** Open the reference for each language you touch, plus `solid.md`, `refactoring.md` or `dependency-management.md` only when the task calls for them. Stay within the three-skill limit in `AGENTS.md`.
3. **Research.** Run the context7 and gh_grep steps above for every library or unfamiliar language feature. Stop and escalate if the documented API contradicts the brief.
4. **Implementer: write the smallest complete change.**
   - Match the existing structure, naming and style. Do not reformat unrelated lines.
   - Type or annotate public signatures. Validate untrusted input at the boundary with runtime checks.
   - Make ownership, error paths and cancellation explicit before adding features.
   - Introduce an abstraction only when the code already has two real uses or a second reason to change.
   - Exit check: type-check, lint, test and build from `AGENTS.md` pass with no new warnings.
5. **Implementer: dependencies.** Adding or majorly upgrading a dependency is an approval gate and a high-risk change in `AGENTS.md`. Stop, state the action, target, risk and rollback, and wait for the user. Work through `dependency-management.md` first. Never run forced or destructive fix commands without approval.
6. **Implementer: refactoring inside scope.** Confirm a passing safety net, change one thing per step and re-run checks after each step. If the area has no tests, report it to the coordinator and load `test-driven-development` for characterization tests. If the refactor spans modules, stop and ask for `sdlc-workflows`.
7. **Implementer: self-review the diff.** Look for leftover debug output, commented-out code, suppressed warnings without a reason, swallowed errors, scope creep and key-like strings. This is not a review; never call the change reviewed.
8. **Reviewer: review the language dimension.**
   - Read the full diff and the surrounding code. Run only read-only commands.
   - Check, in order: correctness of types and nullability, error handling, resource ownership, async or concurrency safety, boundary validation, dependency changes, naming and cohesion.
   - Report a finding only with a concrete failure scenario. Style preferences and naming taste are not findings. Reserve `critical` and `high` for data loss, security exposure or wrong behaviour.
   - A new or upgraded dependency in a high-risk change: state that `security-auditor` must audit it if none was requested.
   - Never edit, format or comment on remote pull requests. Return the standard report with `Changes: none`.
9. **Stop rules.** After two failed fix-and-verify loops, mark the task blocked and give the user the options. Never weaken, skip or delete a test or a lint rule to get a pass.

## Standards

- Project conventions, formatter and linter configuration win over personal preference. Never reformat unrelated code.
- Use only language and library features available in the version the manifest pins. Preview and experimental features need user approval.
- Write no unchecked escape hatches: no `any`, `@ts-ignore`, bare `# type: ignore`, blanket `catch`, or unchecked casts. A necessary suppression is narrow, names the rule and carries a one-line reason.
- Validate untrusted input at every trust boundary with a runtime check. Type annotations alone do not validate data.
- Handle errors explicitly: no swallowed exceptions, no silent fallbacks, and preserve the original cause when wrapping.
- Tie every resource to automatic cleanup: RAII, `try`-with-resources, context managers or `finally`.
- Give every asynchronous or concurrent operation a handled failure path and a timeout or cancellation route. Do not leave a promise, task or future unobserved.
- Do not share mutable state across threads or tasks without synchronisation, or avoid the sharing.
- Name things for intent and domain. No `Util`, `Helper` or `Manager` catch-alls. Booleans read as predicates. Units appear in names.
- A function or class has one reason to change. Extract after real duplication or a real second reason, not in anticipation.
- Refactor in small behaviour-preserving steps with passing checks before and after. Do not mix a refactor with a behaviour change in one step.
- Do not add or majorly upgrade a dependency without recorded user approval. Use the package manager, commit the lockfile and never hand-edit it.
- Check a dependency's licence, maintenance and size before proposing it. Report licence conflicts; do not decide them.
- Leave no dead code, debug output, commented-out code or task comments without an owner.
- Do not use deprecated or removed APIs. Confirm deprecations with context7 for the pinned version.
- Put no secrets, tokens or real hostnames in code, examples, tests or queries.
- Reviewer findings carry location, problem, failure scenario and smallest fix. Opinions without a failure scenario are dropped.

## Verification

- [ ] The language and tool versions used in the change match the manifest or lockfile.
- [ ] The type-check command from `AGENTS.md` passes (for example `tsc --noEmit`, `mypy` or `pyright`, `./mvnw -B verify`, `cmake --build` with warnings enabled) with no new diagnostics.
- [ ] The lint and format commands pass with no new warnings and no new suppressions without a reason (search the diff for `eslint-disable`, `@ts-`, `type: ignore`, `noqa`, `@SuppressWarnings`, `NOLINT`).
- [ ] The test command passes; no test was skipped, weakened or deleted.
- [ ] For C++ changes touching ownership, threads or buffers: a sanitizer build (address and undefined behaviour, plus thread where relevant) ran clean.
- [ ] For dependency changes: the manifest and lockfile diffs list exactly the intended packages; a frozen or clean install succeeds; the licence and approval record is in the report.
- [ ] The diff contains no debug output, commented-out code, secrets or unrelated reformatting (read it with `git diff`).
- [ ] Reviewer only: each finding has a failure scenario, a severity and a location, and the report states what was not inspected.

## Output

Return the standard report from `AGENTS.md` (Status, Summary, Changes, Evidence, Research, Docs impact, Open questions) with these skill-specific contents:

- **Evidence:** the exact type-check, lint, test, build and sanitizer commands run and their results; for dependency work, the manifest and lockfile diff summary, the install command that proved the lockfile, and the licence per new package.
- **Research:** the context7 and gh_grep queries used, and which claims stayed **unverified**. If the change was pure project-internal logic, say so.
- **Docs impact:** list each file as `updated`, `needs update` or `no change`.
  - `README.md` (implementer): install, run or version requirements changed.
  - `CHANGELOG.md` (implementer): user-visible or operator-visible behaviour, or a dependency or runtime upgrade.
  - `docs/ARCHITECTURE.md` (architect): module boundaries or dependency direction changed.
  - `docs/API-CONTRACTS.md` (architect): a public signature or serialized shape changed.
  - `docs/adr/` (architect): a notable dependency, language-version or build-system decision.
  - `docs/MEMORY.md` (coordinator): a durable constraint or pitfall learned, such as a compiler flag that must stay.
- **Reviewer only:** findings in the `AGENTS.md` format, a verdict (`approve`, `changes required` or `unable to review`), and an explicit list of dimensions or files not checked.
