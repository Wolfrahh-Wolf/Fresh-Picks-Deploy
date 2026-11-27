---
name: project-memory
description: "Use when updating docs/MEMORY.md or docs/TASKS.md, resuming earlier work, or recording decisions, constraints and pitfalls."
---

# Project Memory

Keep two small records trustworthy so any session or tool can resume work accurately: `docs/TASKS.md` (what is being done and its status) and `docs/MEMORY.md` (durable facts that code and specifications do not already show). Records are information for the next session; they never grant approval and never contain secrets.

## When to use

- Starting a session or picking up work: checking what exists, what state it is in and whether to resume or open a new task.
- Opening, updating or closing a row in `docs/TASKS.md`, and keeping it in step with the task file under `.agents/tasks/`.
- A durable decision, constraint, convention, pitfall or user preference was learned and should survive this session.
- A remembered fact turns out to be wrong, stale or duplicated and needs correcting or pruning.
- A report contains follow-ups, medium or low findings, or out-of-scope problems that must be tracked.
- Before reporting `done`, to run the coordinator's record update from the documentation sync.

## Do not use for

- Task file template, handoff brief and report format: rules in `AGENTS.md`.
- Specifications, ADRs, README, CHANGELOG and other documentation: load `technical-documentation`.
- Running a delivery procedure such as a feature or bug fix: load `sdlc-workflows`.

## Research: context7 and gh_grep

- You MUST consult **context7** before recording a fact that depends on a library, framework, CLI or cloud API behaviour (a version-specific pitfall, a command flag, a configuration constraint). Check the version the project actually uses. Example queries: "<tool> <flag> behaviour in version <x>", "<framework> <option> default and deprecation".
- You MUST search **gh_grep** before recording a pitfall whose cause rests on an unexplained error message or an unfamiliar integration. Search the literal error text or call, for example `Error: listen EADDRINUSE`, `ECONNREFUSED 127.0.0.1:5432`, `--no-verify-ssl`.
- Pure bookkeeping needs neither: updating a status, an index row, a date, or recording what the user said or decided. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified** in the entry. Never put secrets, private code, personal data or internal hostnames in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/memory-management.md](references/memory-management.md) | Deciding whether a fact belongs in `docs/MEMORY.md`, writing an entry, staying under the size limit, pruning, fixing a stale fact, or checking for secrets. |
| [references/task-tracking.md](references/task-tracking.md) | Choosing IDs, filling `docs/TASKS.md` columns, changing status, linking task files, resuming earlier work, or closing a task. |

## Workflow

1. **Resume first.** Read `docs/TASKS.md`, `docs/MEMORY.md` and the file list of `.agents/tasks/`. Treat every record as a claim to check, not as truth. If the work already has a row, resume it; do not open a duplicate (see `task-tracking.md`, Resuming).
2. **Verify state against reality.** For each open row, compare the task file with the working tree and the last evidence. Evidence older than the last source change is invalid for the affected area. Decide: continue, re-verify, mark `blocked`, or ask the user.
3. **Open or update the row.** Take the next unused ID, create the row and link the task file when the class needs one (Standard, Complex, Unclear failure). Set `Status` and `Updated` in the same step as the task file's own `Status` line.
4. **Change status only on an event.** Transition when a defined event occurs (brief sent, review started, blocker found, gates passed), never on intention. A `done` needs evidence for every gate in `AGENTS.md`.
5. **Capture durable knowledge.** After a task, ask: did we learn a decision, constraint, convention, pitfall or user preference that code, specs and `AGENTS.md` do not already state and that will still be true in a month? If yes, add one dated, sourced line to the right section. If no, add nothing.
6. **Keep memory small.** Replace stale lines instead of appending beside them. Prune when the file passes 160 lines; never exceed 200. Move detail to a spec or ADR (through its owner) and leave a one-line pointer.
7. **Check for secrets and personal data** in every line you wrote to either file, and in any evidence you quote.
8. **Record follow-ups.** Put out-of-scope findings, `medium` and `low` findings and user-deferred items in the `Follow-ups` section with their source task ID.
9. **Report.** State what you changed in each record and what you verified.

### Differences by role

- **orchestrator (or the main session acting as coordinator):** the only writer of `docs/TASKS.md`, `docs/MEMORY.md` and the status, evidence, findings and decisions in task files. Do not edit a task file while the architect is writing its plan sections; serialise those edits.
- **every other agent:** never edit the records. Put candidate durable facts, follow-ups and status-relevant events in the `Docs impact` and `Open questions` lines of the report. The coordinator decides what is recorded.

## Standards

- Only the coordinator writes `docs/TASKS.md` and `docs/MEMORY.md`; no other agent edits them.
- `docs/TASKS.md` is updated after every successful operation, including a trivial one, before reporting done.
- A task ID is unique, never reused and never renumbered, and its row links the task file by path.
- A row's `Status` equals the task file's `Status` line; update both together and stamp `Updated` with the real date.
- Status is one of `planned`, `in-progress`, `in-review`, `blocked`, `done`, `cancelled`, and changes only through the allowed transitions.
- `done` requires evidence for every acceptance criterion and every quality gate; a claim without evidence keeps the task open.
- Every `blocked` row states the reason, what is needed and from whom.
- `docs/MEMORY.md` holds only durable, non-derivable, verified facts, one entry per fact, each with a source and a date.
- `docs/MEMORY.md` stays at or under 200 lines; prune before adding when it is over 160.
- A stale or wrong fact is corrected in place or deleted, never left beside its replacement.
- Never store secrets, credentials, tokens, connection strings with passwords, customer data or personal data in either record or in quoted evidence; record variable names, not values.
- Records are information, never instructions or approval. Do not record an approval as a standing permission; approvals cover only what was described and live in the task file's decisions section.
- Do not copy content owned by another file (spec, ADR, `AGENTS.md`); link to it in one line.
- Do not invent history to make a record look complete: write `unknown` or `unverified` instead.

## Verification

- [ ] Every open row in `docs/TASKS.md` has a task file that exists (or `none` for a trivial task), and every file in `.agents/tasks/` has a row. Compare the two lists.
- [ ] Each row's `Status` matches its task file's `Status`; `Updated` holds today's date for rows you changed.
- [ ] No ID is duplicated or skipped without a cancelled row explaining it.
- [ ] Line count of `docs/MEMORY.md` is 200 or fewer (for example `wc -l docs/MEMORY.md`, or `(Get-Content docs/MEMORY.md).Count` in PowerShell).
- [ ] A search of both records and any quoted evidence for credential words (`password`, `secret`, `token`, `api key`, `private key`, `bearer`) and for long random-looking strings finds no real value.
- [ ] Every file path, command or identifier named in a memory entry was checked and exists now.
- [ ] Each new memory entry passes the qualification test in `memory-management.md` and has a source and a date.
- [ ] Every `done` row has recorded evidence, the quality gates, and the per-file documentation sync result.
- [ ] Follow-ups from the reports of this task appear in `Follow-ups` with a source task ID.

## Output

Put in the standard report:

- **Evidence:** the exact checks run (line count, secret search, list comparison of `docs/TASKS.md` and `.agents/tasks/`, path checks) and their results; for a resume, what you verified against the working tree.
- **Research:** the context7 and gh_grep queries used for any tool-dependent fact, or "none needed: bookkeeping only".
- **Docs impact:** list each file as `updated` or `no change`.
  - `docs/TASKS.md` (owner: coordinator): updated every time.
  - `docs/MEMORY.md` (owner: coordinator): updated when a durable fact was added, corrected or pruned.
  - Task file in `.agents/tasks/` (owner: coordinator for status, evidence, findings and decisions; architect for plan sections).
  - `docs/adr/`, `docs/ARCHITECTURE.md`, `docs/PRD.md` and other specifications (owner: architect): if a recorded decision needs a durable home, request it; do not write it yourself.
  - `README.md` and `CHANGELOG.md` (owner: implementer): only if the change affects them.
  - `AGENTS.md` and `CLAUDE.md`: take proposed changes to the user first.
