# Task Tracking

How the coordinator keeps `docs/TASKS.md` accurate: columns, IDs, status transitions, links to task files, resuming earlier work and closing tasks; written against the RelayCrew `AGENTS.md`, orchestrator definition and `TASKS.md` / `TASK-TEMPLATE.md` templates supplied with this repository, with no external tool versions involved (checked 2026-11-27).

## Contents

- Purpose and ownership
- Structure of `docs/TASKS.md`
- Columns
- Task IDs and file names
- Statuses and transitions
- Keeping the index and the task file in step
- Backlog and Follow-ups
- Resuming earlier work
- Closing a task
- Routing to other skills

## Guidance

### Purpose and ownership

`docs/TASKS.md` is the index of all work. One row answers, at a glance: what is the task, how big is it, where does it stand, where is the detail and when did this row last change. The detail (goal, plan, criteria, evidence, findings, approvals) lives in the linked task file, whose template and handoff rules are in `AGENTS.md`; this reference does not repeat them.

- Owner: the coordinator (the orchestrator, or the main session when there is none). Nobody else edits `docs/TASKS.md`.
- The coordinator updates it after every successful operation, including trivial ones, before reporting done. A skipped update is a documentation-sync failure.
- Other agents report events (done, blocked, failed, follow-ups) in their standard report. The coordinator turns them into records.
- One writer per file: do not edit a task file while the architect is writing its plan sections; serialise those writes.

### Structure of `docs/TASKS.md`

The template defines this layout; keep it.

```
# Tasks

Owner: coordinator. Index of all work; detail lives in the linked task file.

| ID | Task | Class | Status | Task file | Updated |
|---|---|---|---|---|---|

## Backlog

## Follow-ups
```

Rows sit in ID order (oldest first) so the file can be appended to without reshuffling and diffs stay small. Open rows are found by filtering on `Status`, not by position.

### Columns

| Column | Content | Rules |
|---|---|---|
| ID | Three-digit sequence number such as `024` | Unique, never reused, never renumbered |
| Task | Short imperative title, under about 70 characters | Names the outcome ("Add Google login"), not the activity ("Work on auth") |
| Class | `standard`, `complex` or `unclear-failure`; `trivial` for a one-line record without a task file | Set from triage; if the class is raised later, update it and say why in the task file |
| Status | `planned`, `in-progress`, `in-review`, `blocked`, `done` or `cancelled` | Exactly one value; changes only through the transitions below |
| Task file | Repository-relative path such as `.agents/tasks/024-google-oauth.md`, or `none` for a trivial task | Must exist when not `none`; the path never changes after creation |
| Updated | Date of the last change to this row, `YYYY-MM-DD` | Taken from the system clock when you edit the row, never guessed |

Notes:

- **High-risk marker.** The template carries `Risk: normal | high` in the task file. If the task is high risk, add `(risk: high)` at the end of the Task text so the index shows it; the task file remains the authority.
- **Blocked reason.** A `blocked` row appends one clause to the Task text: `blocked: needs user decision on session store`. Full detail goes in the task file.
- **Trivial work.** A trivial edit has no task file, but the documentation sync still applies. Record it as a single row with Class `trivial`, Task file `none` and Status `done`, with the result in the Task text. A pure question that changed nothing needs no row.

### Task IDs and file names

- The next ID is one more than the highest ID found in **both** `docs/TASKS.md` and the file names under `.agents/tasks/` (a task may exist in one place only after an interrupted session). Cancelled and abandoned IDs are never recycled.
- Zero-pad to three digits (`007`, `024`, `130`). If the project passes 999, use four digits for new IDs and leave existing ones alone.
- Task file path: `.agents/tasks/<ID>-<kebab-slug>.md`, for example `.agents/tasks/024-google-oauth.md`. The slug is lower-case words joined by hyphens, three to six words, describing the outcome. This matches the example in the orchestrator definition and the `<kebab-slug>` rule in `AGENTS.md`. If `.agents/tasks/` already uses another convention, follow the existing one and do not rename existing files.
- Never rename a task file or change its ID. If the task is renamed in conversation, change only the Task title text and keep the path.
- Reference a task by its ID everywhere (reports, memory sources, follow-ups): "task 024". IDs stay stable; titles do not.
- Two agents or sessions must not pick the same ID. Because only the coordinator creates rows, take the ID, write the row and create the file in one uninterrupted step.

### Statuses and transitions

The six statuses come from the task template.

| Status | Meaning | Enter when | Evidence to record |
|---|---|---|---|
| `planned` | Defined and accepted for work, not started | The row and task file exist; classification stated | Class and goal in the task file |
| `in-progress` | An agent is working on the outcome | The first brief for the task is sent, or work on a delegated stage starts | Which stage and which agent, in the task file |
| `in-review` | Implementation and tests are done and awaiting verification or review | Tester has reported, or reviewer or security-auditor review has started | Test report and the findings table |
| `blocked` | Cannot proceed without something outside the coordinator's control | A user decision or approval is needed, access or information is missing, the loop limit (2 failed fix-and-verify cycles) is reached, or a report is still incomplete after one request | Reason, what is needed, from whom, what was tried |
| `done` | Finished and verified | Every quality gate in `AGENTS.md` is met | Evidence per criterion, gate results, documentation sync per file |
| `cancelled` | Dropped on purpose | The user cancelled it, or it was superseded by another task | The reason and who decided |

Allowed transitions:

```
planned -> in-progress -> in-review -> done
in-progress -> blocked,  in-review -> blocked,  planned -> blocked
blocked -> in-progress   (blocker cleared; state what changed)
in-review -> in-progress (a source change, finding or failed check sends the work back)
planned | in-progress | in-review | blocked -> cancelled
```

Rules:

- **Event, not intention.** Change status when the event occurs, not when you expect it. `in-review` is not "almost done"; it is "verification is running or complete and not yet passed".
- **A source change reopens verification.** Any source change after tests, review or audit invalidates those results for the affected area (`AGENTS.md`). Move `in-review` back to `in-progress` and re-verify.
- **`done` is gated.** Every acceptance criterion has evidence; tests, lint and build pass or the user accepted a named gap; no `critical` or `high` finding is open; the security audit is complete for high-risk tasks; documentation is synced. If any gate is open, the task is not `done`.
- **No `done` to `in-progress`.** A completed task is not reopened. If a defect appears later, open a new task and reference the old one by ID in its Goal. This keeps the evidence trail truthful.
- **Partial delivery.** The task statuses have no `partial`; that word belongs to the final report. If part of the work is delivered and part is not, either mark the task `blocked` with what is missing, or close what is done as `done` and open a new task for the rest, with the user informed.
- **Failure is not cancellation.** A task that failed its loop limit is `blocked`, not `cancelled`. `cancelled` is a decision, normally the user's.
- **Blocked tasks keep their place.** When unblocked, return to the status held before blocking and note it.
- **Approvals.** If the next step needs an approval-gated action, the task is `blocked` until the user answers. Record the answer and its scope in the task file's decisions and approvals section.

### Keeping the index and the task file in step

The row is the summary; the task file is the detail. They must agree.

- Change the row's Status and the task file's `Status:` line in the same step, then set `Updated`.
- If they disagree on resume, do not assume either is right. Check the evidence in the task file and the state of the work, correct the wrong one, and note the discrepancy in the report.
- Every row with a task file path points to an existing file; every task file has a row. Compare the two lists whenever you open the records: list the file names under `.agents/tasks/`, list the Task file column of `docs/TASKS.md`, and diff them.
- Link outward, do not copy: the task file links specs and ADRs it produced or changed; memory entries cite `task NNN` as a source; follow-ups cite the task they came from.
- Do not put secrets, credentials or personal data in the Task text, the task file's evidence or quoted output. Record variable names and redacted snippets only.
- Keep the Task text short. Anything that needs a sentence or more belongs in the task file.

### Backlog and Follow-ups

**Backlog** holds work that is wanted but not started and not yet triaged into a row. One line each:

```
- Rate-limit the public search endpoint (asked by user, 2026-11-20)
```

Promote an item to a row (take an ID, create the task file for Standard, Complex or Unclear failure) when work begins, and delete the backlog line in the same edit so the item exists in one place.

**Follow-ups** hold things found along the way that are outside the task's scope: out-of-scope problems reported by agents, `medium` and `low` findings listed for the user, and items the user deferred. One line each with a source and a status:

```
- [medium] No rate limit on /auth/callback (source: task 024, reviewer, 2026-11-25) - open
- [low] Index users.google_id if users exceed 100k (source: task 024, reviewer, 2026-11-25) - deferred by user
```

Close a follow-up when it is done (cite the task ID that did it), when the user declines it (say so), or when it became irrelevant (say why). Do not silently delete open follow-ups. Do not fix follow-ups unasked: they need the user's decision to become work.

### Resuming earlier work

Start every session, and every resumption after a gap, with this procedure. Subagents never remember earlier sessions, and memory records may be stale, so treat each record as a claim to verify.

1. **Collect.** Open `docs/TASKS.md`, `docs/MEMORY.md`, and list `.agents/tasks/`.
2. **Reconcile the records.** Find rows whose task file is missing, task files with no row (orphans from an interrupted session), duplicate or skipped IDs, and Status mismatches. Fix them or note them.
3. **Find open work.** Rows with Status `planned`, `in-progress`, `in-review` or `blocked`.
4. **Match the request.** If the user's request matches an open row, resume that task. Do not open a duplicate. If it matches a `done` task, open a new task and reference the old ID. If it matches a `blocked` task, find out whether the blocker is cleared (ask the user if it depends on them).
5. **Open the task file** and read the goal, plan, acceptance criteria, evidence, findings and decisions and approvals.
6. **Verify the state against reality** with read-only checks: the working tree (for example `git status --porcelain` and `git log --oneline -n 10`), whether the files named in scope exist and contain what the evidence implies, and whether the test commands recorded still give the recorded results. A claim you cannot confirm is not evidence.
7. **Decide the status honestly.** An `in-progress` row with no agent running (agents do not survive a session) means the work stopped somewhere: find where, then continue or re-delegate. Evidence recorded before a later source change is invalid for that area: re-verify it. Results that cannot be reproduced mean the task goes back to `in-progress`.
8. **Read relevant memory** (constraints, conventions, pitfalls, user preferences) and put what matters into the next brief; subagents cannot read your context.
9. **State what you found** to the user in two or three lines when the situation is not routine: what was open, what you verified, what you are resuming or what needs their decision.
10. **Record the resume** by updating `Updated` and, where something changed, the task file.

Resuming is not re-doing: do not repeat work whose evidence is still valid, and do not trust an evidence line whose command you cannot identify.

### Closing a task

Closing is the last step of the coordination cycle. Work through it in order.

1. Every acceptance criterion in the task file is checked with evidence (a command, a check and its result), not with a claim.
2. Tests, lint and build pass, or the user accepted a named gap, and the acceptance is recorded.
3. No `critical` or `high` finding is open; `medium` and `low` findings are listed in Follow-ups and told to the user.
4. For a high-risk task, the independent security audit is complete.
5. Documentation sync is recorded per file as `updated` or `no change` in the task file (all files in the `AGENTS.md` source-of-truth table).
6. Durable knowledge was assessed: add to `docs/MEMORY.md` only what passes the qualification test in `memory-management.md`.
7. Set the task file's `Status:` to `done` and the row's Status to `done`; set `Updated`.
8. Move leftover items into Follow-ups, with the source task ID.
9. Send the final report in the standard format (Result, Changes, Verified, Docs, Open, Next).

To close as `cancelled`: record who decided and why, note any partial work left in the tree and what happens to it (a decision for the user if files need removing), set both statuses, set `Updated`.

If a gate cannot be met, the task is not `done`. Mark it `blocked` with the missing item, or get an explicit, recorded user acceptance of a named gap. Never weaken, skip or delete a test to reach `done`.

### Routing to other skills

For the task file template and handoff rules, use `AGENTS.md`. For specifications, ADRs and other documentation, load `technical-documentation`. For git operations such as commits and branches, load `git-version-control`. For TASKS.md-adjacent durable facts, see `memory-management.md`.

## Examples

### A filled-in `docs/TASKS.md`

```
| ID | Task | Class | Status | Task file | Updated |
|---|---|---|---|---|---|
| 022 | Fix 500 on empty cart checkout | unclear-failure | done | .agents/tasks/022-empty-cart-500.md | 2026-11-18 |
| 023 | Rename README heading | trivial | done | none | 2026-11-19 |
| 024 | Add Google login (risk: high) | complex | in-review | .agents/tasks/024-google-oauth.md | 2026-11-26 |
| 025 | Export orders as CSV, blocked: needs user decision on column set | standard | blocked | .agents/tasks/025-orders-csv-export.md | 2026-11-26 |
| 026 | Add dark mode toggle | standard | planned | .agents/tasks/026-dark-mode-toggle.md | 2026-11-27 |

## Backlog

- Rate-limit the public search endpoint (asked by user, 2026-11-20)

## Follow-ups

- [medium] No rate limit on /auth/callback (source: task 024, reviewer, 2026-11-25) - open
```

### Status history of one task (as the coordinator would apply it)

```
2026-11-24  planned      row 024 created; Complex, risk high; plan approved by user
2026-11-24  in-progress  brief sent to implementer (stage: implementation)
2026-11-25  in-review    tester report received (12 new, 47 existing pass); reviewer and security-auditor started
2026-11-25  in-progress  security-auditor: high finding (state parameter not validated); sent to implementer
2026-11-26  in-review    fix verified by tester; reviewer and security-auditor re-run
2026-11-26  done         both approved, gates met, docs synced (see task file)
```

### Resuming: a worked example

```
Request: "Continue the CSV export."
Records: row 025 is blocked ("needs user decision on column set"); task file exists.
Reconcile: .agents/tasks/ has 025-orders-csv-export.md and 027-search-ratelimit.md; 027 has no row.
  -> orphan from an interrupted session; check its status line, add the row, tell the user.
Verify: git status shows uncommitted edits in src/export/; task file evidence says "tests pass".
  -> run the recorded test command: 2 failures. Evidence is not valid.
Decision: 025 stays blocked until the user answers the column question; record the 2 failures
  in the task file; ask the user the column question and report the orphan.
```

### Bad to good: rows

| Bad | Why | Good |
|---|---|---|
| `\| 24 \| auth stuff \| standard \| WIP \| \| \|` | Unpadded ID, vague title, invalid status, no file, no date | `\| 024 \| Add Google login (risk: high) \| complex \| in-progress \| .agents/tasks/024-google-oauth.md \| 2026-11-24 \|` |
| Status `done` while a `high` finding is open | Violates the quality gate | `in-progress` until the finding is fixed and re-verified |
| Two rows for the same work after a session restart | Duplicate effort and conflicting records | Resume the existing row; remove the duplicate row you added and note it |
| Task renamed by editing the file name | Links in reports and memory break | Keep the path; change only the title text |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Updating status from memory or intention | The index drifts from reality | Change status on the event, with evidence in the task file |
| Row and task file disagree | Resumers trust the wrong one | Update both in the same step; reconcile on resume |
| Opening a duplicate task on resume | Split evidence and repeated work | Search rows and `.agents/tasks/` first, then resume |
| Trusting old evidence after later source changes | A green result no longer applies | Re-verify the affected area; set status back to `in-progress` |
| Reusing or renumbering IDs | Old references point at the wrong work | Next ID from the highest in both places; never recycle |
| Marking `done` with open gates | Unverified work shipped as complete | Hold `done` until every gate is met, or record a user-accepted gap |
| Reopening a `done` task | The evidence trail becomes false | Open a new task that references the old ID |
| Letting follow-ups disappear | Findings are lost | Keep them in Follow-ups with source and status until closed |
| Skipping the row for a trivial change | Documentation sync fails; the change is invisible | Record a one-line `trivial` row with `none` as the task file |
| Putting credentials or personal data in evidence | Secrets spread through committed files | Redact; record variable names only |
| Editing the task file while the architect writes it | Lost or conflicting edits | One writer per file; serialise |

## Checklist

- [ ] Every row has a three-digit ID that is unique and in order, a short outcome title, a valid Class and Status, a path or `none`, and an `Updated` date.
- [ ] Every non-`none` Task file path exists, and every file in `.agents/tasks/` has a row.
- [ ] Each row's Status equals its task file's `Status:` line.
- [ ] Every `blocked` row names the reason, what is needed and from whom.
- [ ] Every status change followed an allowed transition and a real event, with evidence in the task file.
- [ ] Status moved back to `in-progress` where a later source change invalidated earlier verification.
- [ ] No `done` row has an open `critical` or `high` finding, an incomplete security audit or unsynced documentation.
- [ ] Follow-ups from this task are recorded with a source task ID and a status.
- [ ] On resume: orphans, duplicates and mismatches were found and handled, and state was verified against the working tree.
- [ ] No secrets or personal data appear in rows, task files or quoted evidence.

## Verify with context7 and gh_grep

- **context7:** not needed for index and status bookkeeping. Use it only when a resume check depends on a tool's behaviour and you need the project's version, for example: "git status --porcelain output format", "git log --oneline and -n options", or the project's test runner flag that was recorded as evidence.
- **gh_grep:** not needed for bookkeeping. If a task is blocked on an unexplained error, search the literal error text (for example `Error: Cannot find module`) to describe the likely cause in the blocked reason, labelled `unverified` until confirmed. Never put internal hostnames, secrets or private code in a query.
- Pure project-internal record-keeping needs neither; say so in the report.

## Sources

- `AGENTS.md` (this repository): Workflow, Handoff, Quality gates, Documentation sync, Approval gates, Safety. Read 2026-11-27.
- `sources/agents/orchestrator.md` (this repository): Workflow, Records, Quality gates, Failures, Definition of Done and its example task file path. Read 2026-11-27.
- `sources/templates/TASKS.md` and `sources/templates/TASK-TEMPLATE.md` (this repository): table columns, section names and the six statuses. Read 2026-11-27.
- `sources/shared/report-format.md` (this repository): the standard report structure. Read 2026-11-27.
- No external web source was needed: this reference describes repository conventions and involves no third-party library or standard.
