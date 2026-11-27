# Documentation Sync

How to carry out the `Documentation sync` section of `AGENTS.md`: who owns each file, how to map a change to the documents it affects, and how to fill the per-file result table; assumes the RelayCrew `AGENTS.md` as shipped with this skill pack, checked 2026-11-26. `AGENTS.md` is the authority. This file shows how to do it and never replaces a rule in it.

## Contents

- When the sync runs and what done means
- File ownership
- Impact mapping
- Running the sync by role
- The per-file result table
- Deciding between updated and no change
- When code and a document disagree
- Edge cases

## Guidance

### When the sync runs and what done means

The `Documentation sync` section of `AGENTS.md` requires the sync after every successful operation, including trivial ones, before reporting done. The `Quality gates` section makes synced documentation a condition of done. So:

- A task with a code change, a configuration change or a documentation change runs the sync.
- A question that changed nothing in the repository has nothing to sync. Report `Docs impact: none (no change made)`.
- A failed or blocked task is not synced as if it succeeded. Report what documents would need updating once it is resolved.
- Any later source change invalidates earlier results for the affected area. If a fix loop changes behaviour after the sync, run the sync again for the affected files.

The sync is a check of every file, not an edit of every file. Most syncs record `no change` for most rows.

### File ownership

The `Source of truth` table in `AGENTS.md` defines ownership. Use it as given.

| File | Owner | Who may edit | Content rules |
|---|---|---|---|
| `docs/PRD.md` | architect | architect | `product-technical-planning` |
| `docs/DESIGN.md` | architect | architect | `architecture-documentation.md` |
| `docs/ARCHITECTURE.md` | architect | architect | `architecture-documentation.md` |
| `docs/DB.md` | architect | architect | `architecture-documentation.md` |
| `docs/API-CONTRACTS.md` | architect | architect | `api-documentation.md` |
| `docs/adr/` | architect | architect | `system-architecture` |
| `README.md` | implementer | implementer | `readme.md` |
| `CHANGELOG.md` | implementer | implementer | `changelog.md` |
| `docs/TASKS.md` | coordinator | coordinator | `project-memory` |
| `docs/MEMORY.md` | coordinator | coordinator | `project-memory` |
| `AGENTS.md`, `CLAUDE.md` | user approval | changed only with user approval | not covered here |

Rules that follow from the table and the role boundaries:

1. You edit only the files your role owns. For any other affected file, state the exact section and the difference in `Docs impact` so the owner can act.
2. The implementer also keeps `.env.example` in step with the variables it adds. The names there are the single source for the README configuration table.
3. One writer per file at a time. If two agents need the same file, the coordinator sequences them.
4. Task files are updated by the coordinator. Agents put their results in their report.

### Impact mapping

Walk this table for every change. A change often matches several rows.

| Change signal | Files to check, with owner |
|---|---|
| User-visible or operator-visible behaviour added, changed, deprecated or removed | `CHANGELOG.md` (implementer). `README.md` if usage or setup shows it |
| Install, run, test, lint or build command, or a required tool version, changed | `README.md` Requirements, Setup, Testing (implementer). If it makes the `Commands` line in `AGENTS.md` wrong, propose the edit to the user |
| Environment variable or configuration key added, renamed or removed | `.env.example` and `README.md` Configuration (implementer). `ARCHITECTURE.md` if topology changed |
| Endpoint or event added, changed or removed; validation, error, auth or rate limit changed | `API-CONTRACTS.md` (architect). README endpoint list, guides and examples (implementer). `CHANGELOG.md` |
| Table, column, constraint, index, migration or retention rule changed | `DB.md` (architect). `CHANGELOG.md` if operators must act. `README.md` if setup commands changed |
| Component, service, dependency, external integration, trust boundary or deployment topology changed | `ARCHITECTURE.md` (architect). `README.md` Requirements if something must be installed. `CHANGELOG.md` if operators notice |
| Decision that is costly to reverse: new dependency, schema migration, auth model, public API shape, infrastructure | `docs/adr/` (architect, per `system-architecture`) |
| Screen, flow, state, token, shared component, breakpoint or accessibility rule changed | `DESIGN.md` (architect). `CHANGELOG.md` if users notice |
| Requirement or scope changed | `PRD.md` (architect, per `product-technical-planning`) |
| Bug fixed | `CHANGELOG.md` Fixed. Other docs only if they described the wrong behaviour as correct |
| Vulnerability fixed | `CHANGELOG.md` Security, with the disclosure timing left to the user. `ARCHITECTURE.md` security model if a boundary changed |
| Internal refactor, rename or test-only change with no behaviour change | Usually none. Still check that names in the `ARCHITECTURE.md` component table, paths in `README.md` and file names in `DB.md` are still right |
| Documentation-only change | The file itself. `CHANGELOG.md` only if users depended on the corrected statement |
| Task finished | `docs/TASKS.md`, always (coordinator) |
| Durable decision, constraint or pitfall learned | `docs/MEMORY.md` (coordinator). State it in your report so the coordinator can record it |
| Change to agent rules, permissions, CI/CD or deployment process | Propose changes to `AGENTS.md` or `CLAUDE.md` to the user first. These are gated actions |

### Running the sync by role

**Implementer**

1. Collect the facts of the change from the diff: behaviours, commands, variables, interfaces, files and tables touched.
2. Walk the impact table and the eleven files. For each, decide `update` or `no change` and write the reason.
3. Edit `README.md`, `CHANGELOG.md` and `.env.example` as needed, using [readme.md](readme.md) and [changelog.md](changelog.md).
4. For each specification file that is affected, write `needs update (architect)` with the section and the exact difference. Do not edit it. Say whether the document is stale (the change followed the plan) or the code departs from the design.
5. Verify your edits: run documented commands, check links and examples.
6. Report the per-file table in `Docs impact`.

**Architect**

1. Compare each specification file with what was built, following the sync steps in [architecture-documentation.md](architecture-documentation.md) and [api-documentation.md](api-documentation.md).
2. Update stale details, remove `Planned` marks on built work, and request a decision record where a costly decision was made.
3. Report any departure of code from an approved design with the file, section and difference, instead of rewriting the design.
4. For README or changelog needs, write `needs update (implementer)` with the section and the difference.
5. Leave `Status` lines unchanged. Only the user approves.
6. Report the per-file table in `Docs impact`.

**Coordinator** (the orchestrator, or the main session where no orchestrator exists)

1. Collect the tables from every agent and route each `needs update` to its owner.
2. Always update `docs/TASKS.md`. Update `docs/MEMORY.md` when a durable decision, constraint or pitfall was learned. For how, load `project-memory`.
3. Take proposed changes to `AGENTS.md` or `CLAUDE.md` to the user before anything is edited.
4. Record the final result per file in the task file, or in the final report when there is no task file.
5. Do not close the task while any file is neither `updated` nor `no change`.

### The per-file result table

The final record has one row for each of the eleven rows of the `Source of truth` table and uses exactly two result values, as `AGENTS.md` requires: `updated` or `no change`. Add a reason or evidence to every row.

An agent's own report may use a third value for files it cannot edit: `needs update (owner)`. The coordinator resolves each of these into `updated` or `no change` before the final record.

| Column | Content |
|---|---|
| File | Path as in the source-of-truth table |
| Owner | architect, implementer, coordinator, or user approval |
| Result | `updated`, `no change`, or in an agent report `needs update (owner)` |
| Reason or evidence | What changed and where, or why nothing needed to. Name the checked source |

Rules:

1. Every row has a reason. "No change" alone is not enough.
2. An `updated` row names the section edited.
3. A `no change` row names what you compared. For example: "compared the component table with `src/` entry points".
4. For `AGENTS.md` and `CLAUDE.md`, record `no change`, and when a proposal was sent to the user, add "(proposal sent to user)". The result becomes `updated` only after approval and the edit.

### Deciding between updated and no change

- Update a file only when a statement in it became false, incomplete or misleading because of this change.
- Do not invent changes to make a file look current. A document that was already accurate is `no change`.
- Do not use the sync to rewrite or tidy unrelated passages. If you spot an unrelated stale statement, list it as a follow-up and leave it, as `AGENTS.md` asks for unrelated problems.
- Prefer the smallest correct edit and keep the file's existing structure.
- If you cannot tell whether a statement is still true, check the source. If you still cannot tell, mark it **unverified** and ask.

### When code and a document disagree

`AGENTS.md` states: if code and a specification disagree, report it and ask which is right. Never silently change either to match. In practice:

1. Quote the document statement and the code behaviour with file and line.
2. Say which one the plan or acceptance criteria support.
3. State the two options: change the code to match the specification, or change the specification to match the code. Ask the user. Include the cost of each.
4. Until the answer, leave both unchanged. The task cannot be reported done while the disagreement concerns an acceptance criterion.

### Edge cases

- **Missing documentation file.** If a file in the table does not exist in this project, record `no change` with "file not present" unless the change makes it necessary. Ask the coordinator before creating a new document.
- **Trivial change.** The sync still runs. The table is quick: usually all `no change` except `docs/TASKS.md`.
- **Bulk or generated edits.** Sync against the generator's source and regenerate. Do not hand-edit generated files.
- **Documentation in another language or location.** Follow the project's existing locations. A translated or hosted copy is listed in `Docs impact` as a follow-up if you cannot update it.
- **Conflicting agents.** If an agent report contradicts a document, say so in `Open questions`. Do not decide between them.
- **Approval gates.** Editing documents needs no approval. Pushing, publishing, releasing and changing `AGENTS.md`, `CLAUDE.md`, CI/CD or permissions do.

## Examples

### Final per-file table for a standard feature (new login endpoint)

~~~~text
Docs impact:
| File | Owner | Result | Reason |
|---|---|---|---|
| docs/PRD.md | architect | no change | Requirements unchanged; endpoint was already in scope |
| docs/DESIGN.md | architect | no change | No UI change |
| docs/ARCHITECTURE.md | architect | no change | No new component; compared component table with src/ entry points |
| docs/DB.md | architect | no change | Uses the existing users table; no schema change |
| docs/API-CONTRACTS.md | architect | updated | Added POST /api/auth/login: request, 200, 401, 422, 429 |
| docs/adr/ | architect | no change | No decision costly to reverse |
| README.md | implementer | updated | Usage: login example, run against local server; Configuration: JWT_SECRET already listed |
| CHANGELOG.md | implementer | updated | Unreleased > Added: login endpoint |
| docs/TASKS.md | coordinator | updated | Task marked done with evidence |
| docs/MEMORY.md | coordinator | no change | No durable decision or pitfall |
| AGENTS.md, CLAUDE.md | user approval | no change | No rule changed |
~~~~

### Implementer's report, with files it cannot edit

~~~~text
Docs impact:
  PRD.md: no change (requirements unchanged)
  DESIGN.md: no change (no UI)
  ARCHITECTURE.md: no change (no new component)
  DB.md: needs update (architect): section "Indexes and the queries they serve":
    new index idx_orders_user_created serves GET /api/orders; not listed.
    Doc is stale; change followed the plan.
  API-CONTRACTS.md: needs update (architect): GET /api/orders returns 429 when
    the limiter trips; contract lists only 200 and 401.
  adr/: no change
  README.md: updated (Usage: orders example run against local instance)
  CHANGELOG.md: updated (Unreleased > Added: GET /api/orders)
  TASKS.md, MEMORY.md: coordinator
  AGENTS.md, CLAUDE.md: no change
~~~~

### Trivial change (typo in an error message)

~~~~text
Docs impact:
  README.md: no change (error text not quoted)
  CHANGELOG.md: no change (not noticeable to users)
  All specification docs: no change (no behaviour, contract or schema change)
  TASKS.md: coordinator
~~~~

### Code departs from the approved design (architect)

~~~~text
Open questions:
  1. DESIGN.md "Screens and states" says the order list shows an empty state with a
     link to the catalogue. src/pages/orders.tsx:48 shows a blank table. Plan and
     acceptance criterion 3 support the document. Options: (a) change the code to
     match the document (small change, one component); (b) change the document to
     match the code (loses the empty state). Which is right? Both left unchanged.
~~~~

### Proposal for AGENTS.md (sent to the user, not applied)

~~~~text
Proposed change to AGENTS.md, section "Project", Commands:
  Current: test `npm test`
  Proposed: test `npm run test:ci`
  Reason: package.json no longer defines "test"; README already uses test:ci.
  Status: not applied; needs user approval.
~~~~

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Skipping the sync for a trivial change | The rule has no exception, and small changes cause stale docs | Run the sync and record `no change` with reasons |
| Marking `no change` without comparing | A stale document stays | Name the source you compared with each file |
| Editing a specification as the implementer | Breaks ownership and review | Write `needs update (architect)` with the exact difference |
| Updating every file to look thorough | Invents changes and adds noise | Update only statements made false by the change |
| Aligning code and document silently | Hides a departure the user should decide | Report the disagreement and ask |
| Leaving `needs update` in the final record | The sync is incomplete | The coordinator routes it and records `updated` or `no change` |
| Editing `AGENTS.md` or `CLAUDE.md` directly | These change only with user approval | Send a proposal to the user |
| Fixing unrelated stale docs | Widens the diff and bypasses scope | List them as follow-ups |
| Recording results only in chat | The task file has no record | Put the table in the report so the coordinator can record it |
| Reporting done before verifying edited commands and links | Docs can be wrong the day they ship | Run the checks, then report |

## Checklist

- [ ] All eleven files in the `Source of truth` table have a row in the result table.
- [ ] Every row has `updated` or `no change` in the final record, with a reason.
- [ ] Every `needs update (owner)` in an agent report was routed and resolved by the coordinator.
- [ ] Every file you edited is one your role owns.
- [ ] Each `updated` row names the section edited, and each `no change` row names what was compared.
- [ ] Any code-versus-document disagreement was reported with both options, not resolved silently.
- [ ] `docs/TASKS.md` was updated by the coordinator, and `docs/MEMORY.md` where a durable lesson was learned.
- [ ] Any change to `AGENTS.md` or `CLAUDE.md` is only a proposal until the user approves.
- [ ] Commands, links and examples in edited files were verified or labelled `not run`.
- [ ] Unrelated stale documentation was listed as follow-ups and not edited.
- [ ] The sync was rerun after any fix that changed behaviour.

## Verify with context7 and gh_grep

- **context7:** if the project generates documentation (an OpenAPI renderer, a static site generator, an API reference generator), query its documentation at the version in the lockfile for the command that regenerates output and the configuration keys you mention, for example `<generator> build command` and `<generator> configuration reference`. Pure sync of this repository's own documents needs neither tool. Say so in the report.
- **gh_grep:** search literal text for how maintained projects keep documentation in step with code, for example `## Documentation` in `AGENTS.md` files, `docs impact` and `Update documentation` in contribution guides, and `[Unreleased]` in `CHANGELOG.md` files. Treat results as examples. `AGENTS.md` in this project always wins.

## Sources

- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- Keep a Changelog 2.0.0: https://keepachangelog.com/en/2.0.0/
- Diátaxis, start here: https://www.diataxis.fr/start-here/
