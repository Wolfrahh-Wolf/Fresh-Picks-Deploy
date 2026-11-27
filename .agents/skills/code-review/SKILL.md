---
name: code-review
description: "Use when reviewing a change for correctness, maintainability, performance, architecture fit and baseline security, and reporting findings by severity."
---

# Code Review

Find real defects in a change and report them with evidence, a concrete failure scenario and a severity, without editing anything. The output is a verdict the coordinator can act on: `approve`, `changes required` or `unable to review`.

## When to use

- A Standard, Complex or Unclear failure task has passed testing and needs an independent review.
- The coordinator asks for a review of a diff, branch, patch, pull request or list of changed files.
- The implementer has fixed earlier findings and the affected area needs a re-review (any source change invalidates the earlier review of that area).
- A high-risk change is under review. Run this skill and expect `security-auditor` to review independently.

## Do not use for

- In-depth security audit, threat modelling, OWASP-level analysis: load `security-engineering`.
- Performance tuning technique (index choice, caching design, render optimisation): load the relevant engineering skill (`database-engineering`, `backend-engineering`, `frontend-engineering`).
- Finding the root cause of a failing test or crash: load `debugging`.
- Designing or changing the architecture: load `system-architecture`.
- Judging test strategy in depth or writing tests: load `testing-strategy`.
- Language idioms and refactoring technique: load `languages-clean-code`.
- Writing or syncing documentation: load `technical-documentation`.
- Fixing the code. The reviewer reports; the implementer changes.

## Research: context7 and gh_grep

- You MUST consult **context7** before you judge any call to a library, framework, SDK, CLI tool or cloud API that the diff adds or changes. Check the project's manifest or lockfile first (`package.json` and its lockfile, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.lock`) and query that version. Useful queries: "`<library>` `<version>` `<function>` return value and thrown errors", "`<library>` `<function>` default timeout and retry behaviour", "`<library>` `<function>` deprecated or removed since `<version>`", "`<ORM>` transaction commit and rollback behaviour", "`<framework>` middleware execution order".
- You MUST search **gh_grep** when a pattern in the diff is unfamiliar, when documentation is ambiguous about the behaviour you suspect is wrong, or before you report a library misuse that the documentation does not state outright. Search literal code. Useful searches: `AbortSignal.timeout(`, `ON CONFLICT (`, `FOR UPDATE SKIP LOCKED`, `withTransaction(`, `.findOneAndUpdate(`.
- Project-internal logic (business rules, in-repo calls, naming, structure) needs neither. Say so in the report under Research.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/correctness.md](references/correctness.md) | Checking logic, edge cases, concurrency, error paths, data integrity or whether the change meets the requirement. Always open for the first review pass. |
| [references/maintainability.md](references/maintainability.md) | Judging readability, complexity, duplication, naming, dead code or whether the tests would fail if the behaviour broke. |
| [references/performance-review.md](references/performance-review.md) | The diff touches a hot path, a query, a loop over data, memory-heavy structures, caches, outbound calls or payload size. |
| [references/architecture-review.md](references/architecture-review.md) | The diff crosses a module or service boundary, adds a dependency or component, changes a contract, or may conflict with `docs/ARCHITECTURE.md` or an ADR. |
| [references/review-checklist.md](references/review-checklist.md) | Always, before writing the report: ordered checklist, baseline security, severity rules, finding format, verdict logic. |

## Workflow

The reviewer is the only agent that loads this skill. Related roles, for orientation: the **implementer** changes code, the **tester** verifies behaviour, the **security-auditor** audits high-risk changes independently, and the **coordinator** records findings in the task file. The reviewer never edits and never treats another agent's summary as evidence.

1. **Confirm inputs.** You need the full diff or changed-file list, the acceptance criteria, access to the surrounding source (callers, callees, shared types, config) and the test evidence. If any is missing, request it. If it cannot be supplied, stop with `unable to review` and name what is missing.
2. **Size and classify.** Count files and lines changed. Check the change against the high-risk list in `AGENTS.md` (Triage). If it is high risk and no security audit was requested, say so in the report.
3. **Read project context.** Read the task file, then the specs the change touches: `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md`, `docs/PRD.md` and the ADRs in `docs/adr/`. Specifications describe intent; if code and specification disagree, report it and ask which is right. Do not choose silently.
4. **Read every changed line.** Then trace one hop beyond the diff: callers, callees, shared types, configuration and tests. A diff snippet alone is not enough to judge a change.
5. **Map the acceptance criteria.** For each criterion, find the code and the evidence that satisfies it. Mark it `met`, `not met` or `unable to verify`. An ambiguous criterion becomes an open question.
6. **Review in the fixed order:** correctness, data integrity, security, error handling, compatibility, performance, maintainability, tests, docs. Open the matching reference for each dimension that the diff touches. Do not skip a dimension; if there are no findings, state that it was cleared and how.
7. **Verify library and API behaviour** against documentation for the version in use (see Research). Do this before reporting any misuse.
8. **Confirm every candidate finding.** Trace the execution path from a concrete input or state to the wrong result, or run a safe read-only check. If you cannot, downgrade it to an open question or drop it.
9. **Classify and rate.** Mark each finding `introduced` or `pre-existing` (use history to tell them apart). Assign severity with the rules in the review checklist; do not inflate. Pre-existing issues are follow-ups, not blockers.
10. **Check test adequacy.** Ask of each new behaviour: would a test fail if this broke? List criteria with no covering test.
11. **Check documentation.** Compare the change against the source-of-truth table in `AGENTS.md`. Report missing or inaccurate documentation as a finding and name the owner.
12. **Escalate when required** (design-level defect, ADR contradiction, a `critical` finding, criteria that contradict intent, scope beyond your evidence). State what triggered it, what you reviewed and what is needed to unblock.
13. **Render the verdict and report** in the format in the review checklist, with `Changes: none`.

Re-review after fixes: re-read only the changed area plus its callers, confirm each earlier blocking finding is resolved with evidence, and look for regressions the fix introduced.

## Standards

- Never edit, format, commit or comment on a remote pull request without user approval; every report has `Changes: none`.
- Every finding states severity, `file:line`, problem, a concrete failure scenario and the smallest fix. No scenario means it is a question or it is dropped.
- Use the `AGENTS.md` severity scale exactly: `critical`, `high`, `medium`, `low`. Only `critical` and `high` block completion.
- Evaluate all nine dimensions in the fixed order and say explicitly when one is clear.
- Check every acceptance criterion individually and record `met`, `not met` or `unable to verify`.
- Read the full diff and one hop of surrounding code. Never approve from the author's summary or from passing tests alone.
- Separate defects the change introduced from pre-existing ones.
- Confirm library and API behaviour against documentation for the version in use before reporting misuse. Unconfirmed claims are labelled **unverified**.
- Order findings by severity, then by file. State plainly when nothing blocks, and list what you did not check.
- Run only read-only commands. Ask before anything that writes files, installs, uses the network, changes git state or runs a command with side effects.
- Do not issue `approve` for work you could not inspect; use `unable to review` and list the coverage gaps.
- Do not invent requirements. A missing requirement is an escalation or a question, not a finding.
- Style preferences are not findings. Report style only when a project rule mandates it or it will mislead a future reader into a defect.
- If code and a specification disagree, report both locations and ask which is right. A contradiction with an ADR is escalated.
- Never print, quote or log a secret found in the diff. Report its location and kind and recommend rotation.
- State the baseline-security result in every review. A high-risk change without a requested audit is flagged; the baseline does not replace `security-auditor`.
- Any later source change invalidates the review of the affected area; re-review it.

## Verification

- [ ] The full change was listed with read-only commands, for example `git diff --stat <base>...<head>` and `git diff <base>...<head> -- <path>`, and the file count in the report matches.
- [ ] Each changed file was opened and read, and the callers of each changed public symbol were found with a code search, for example `git grep -n "<symbol>"`.
- [ ] Pre-existing versus introduced was decided with history, for example `git blame -L <start>,<end> -- <file>`.
- [ ] Each acceptance criterion has a verdict and a pointer to code or test evidence.
- [ ] Each finding was traced from input to wrong result, or marked as a question.
- [ ] Each library or API claim was checked in documentation for the project's version, or labelled unverified.
- [ ] The nine dimensions are each either listed with findings or explicitly cleared.
- [ ] Findings are in severity order and every one carries all five fields.
- [ ] Coverage gaps (files, dimensions, tests not run) are listed.
- [ ] The verdict matches the decision rules: any open `critical` or `high` finding, or any `not met` criterion, means `changes required`.

## Output

Return the standard report from `AGENTS.md` (Handoff). Put the verdict and findings under `Summary` and set `Changes: none`.

- **Summary:** verdict, scope reviewed (files and lines), findings in the finding format, acceptance-criteria results, per-dimension result, coverage gaps.
- **Evidence:** the read-only commands you ran and what they showed; test results you relied on and their source; the files you read.
- **Research:** the context7 and gh_grep queries used and the version checked, or "not needed: project-internal logic".
- **Docs impact:** documentation that is missing or inaccurate, per file, or "none" with the reason. The reviewer updates nothing; owners update.
- **Open questions:** ambiguities, unverifiable claims, spec-versus-code disagreements, or "none".

Docs this review can affect, and who updates them: `docs/PRD.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md` and `docs/adr/` (architect); `README.md` and `CHANGELOG.md` (implementer); `docs/TASKS.md` and `docs/MEMORY.md` (coordinator, who also records the findings in the task file's review findings table). `AGENTS.md` and `CLAUDE.md` change only with user approval.
