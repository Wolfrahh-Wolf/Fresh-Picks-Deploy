# Project Onboarding

The playbook for taking over an existing repository: discover the stack and commands, record a baseline, fill the `AGENTS.md` placeholders with the user's approval and bootstrap `docs/` without inventing facts; language-neutral, written against the RelayCrew `AGENTS.md` and templates; checked 2026-11-27.

## Contents

- Purpose and the one rule: evidence or unknown
- The stage table
- Stage details
- The evidence ledger
- Discovering commands safely
- Filling the `AGENTS.md` Project block
- Bootstrapping `docs/`
- Special cases
- Closing the onboarding

## Guidance

### Purpose and the one rule: evidence or unknown

Onboarding makes an unfamiliar repository workable for the team: the agents know the stack, the exact commands, the current test state, where documentation lives and which areas are risky. `AGENTS.md` requires this before other work when any value in its Project block is still a placeholder.

The rule that governs everything here: **every statement written into `AGENTS.md` or `docs/` is backed by evidence you saw, or is marked unknown for the user to confirm.** Specifications describe intent and docs describe what is true now, so a guessed sentence is worse than a gap. A sparse, true document beats a complete, partly invented one.

Rules owned by `AGENTS.md` are not repeated here: triage, the brief and report formats, approval gates, quality gates and documentation sync. Onboarding of an unfamiliar codebase is normally Complex (ambiguous and cross-cutting); state the class you choose.

### The stage table

| # | Stage | Who | Input | Output | Exit check |
|---|---|---|---|---|---|
| 0 | Scope and class | orchestrator | User goal, repository | Class and risk line, what the user wants from onboarding, questions asked once | User confirmed scope or assumptions are stated |
| 1 | Inventory | `explore` (read-only) | Repository | Facts for the ledger: layout, manifests, versions, entry points, tests, CI, existing docs | Each fact has a path or command as evidence |
| 2 | Discover commands | implementer, with orchestrator | Manifests, scripts, CI, README | Candidate install, dev, test, lint, type-check and build commands | Each candidate traced to its source |
| 3 | Baseline | implementer | Candidate commands | Command results: exit status, counts, warnings; pre-existing failures list | Each command was run (or its blocker recorded) and results are verbatim |
| 4 | Approve and fill `AGENTS.md` | user, then implementer | Proposed exact text | Project block filled | User approved the exact text; no placeholder remains in the Project block |
| 5 | Bootstrap `docs/` | architect (specs, ADRs), implementer (README, CHANGELOG), orchestrator (TASKS, MEMORY) | Ledger | Documents containing only evidenced facts, with unknowns marked | Every claim traces to the ledger; every path mentioned exists |
| 6 | Risk map and conventions | orchestrator, from reports | Ledger, inventory | High-risk areas, conventions, pitfalls recorded in `docs/MEMORY.md` | Each entry has evidence |
| 7 | Close | orchestrator | All reports | Final report with unknowns and proposed follow-ups | Quality gates and documentation sync met |

### Stage details

**0 Scope and class.** Ask what the user wants out of onboarding (get running, prepare for a feature, audit before takeover). Note any constraints such as "do not touch CI". Onboarding is mostly read-only until stage 4, and every edit afterwards is limited to the files named in the plan.

**1 Inventory (read-only).** Brief `explore` to look, not to change. Collect:

| Fact | Where to look |
|---|---|
| Languages and runtime versions | Version files and manifest fields (for example a runtime version file, `engines`, a required-version field, a `go` directive in the module file), container files, CI configuration |
| Frameworks and libraries | Manifest and lockfile (read the versions actually locked) |
| Package manager | Lockfile type, `packageManager` field, tool configuration |
| Entry points | Manifest `main` or `bin`, framework config, server start file, container `CMD` |
| Layout | Top-level directories, source and test locations, monorepo workspace configuration |
| Tests | Test directories, test configuration, how tests are named |
| CI | Workflow files under `.github/workflows/` or the CI system's configuration |
| Containers and infrastructure | Dockerfiles, compose files, infrastructure definitions (read only) |
| Configuration | `.env.example` names (never `.env` values) |
| Data model | Migrations, model definitions, schema files (never a live database) |
| API surface | Route definitions, an OpenAPI file, controllers |
| Existing documentation | README, `docs/`, ADRs, contributing guide, changelog |
| History | Recent commit subjects (`git log --oneline -n 30`), tags, branch names |

Never open files that hold secrets: `.env`, key files, credential stores, token files. If one is found, report its path and kind and stop reading it. Never print a secret that appears in output; recommend rotation for anything committed.

**2 Discover commands.** See "Discovering commands safely".

**3 Baseline.** Run the candidate install (if the project is not set up), test, lint, type-check and build commands, record each one's exit status, test counts and warnings, and list failures that exist before any change. Failures found here are pre-existing: record them, do not fix them. This list is what later tasks compare against.

**4 Approve and fill `AGENTS.md`.** See the dedicated section. The change to `AGENTS.md` needs the user's approval of the exact text, which is recorded in the brief to the implementer.

**5 Bootstrap `docs/`.** See the dedicated section.

**6 Risk map and conventions.** From the ledger, write down: which high-risk areas exist (authentication, authorization, payments, personal data, cryptography, secrets handling, file upload, external input surfaces, migrations, infrastructure, CI/CD) and where; conventions actually observed (formatting and lint rules, naming, test layout, commit message style from history); known pitfalls (a flaky test, a slow step, a required environment variable). Conventions and pitfalls go to `docs/MEMORY.md` (skill `project-memory`), each with its evidence. This map decides later routing: a task in a listed area is high risk by default.

**7 Close.** Report what was learned, what is unknown, the baseline failures and recommended follow-up tasks. Follow-ups are proposed, not started.

### The evidence ledger

Keep a ledger in the task file. Nothing is written into a document unless it is `confirmed`; `inferred` items are put to the user; `unknown` items are written as unknown.

| Fact | Evidence | Status |
|---|---|---|
| Runtime is Node 20 | `.nvmrc` line 1: `20`; CI `setup-node` uses `20` | confirmed |
| Package manager is pnpm | `pnpm-lock.yaml` present; no other lockfile | confirmed |
| Test command is `pnpm test` | `package.json` scripts.test = `vitest run`; CI step runs `pnpm test` | confirmed |
| App serves a REST API | `src/routes/*.ts` register `GET`/`POST` handlers | confirmed |
| Hosted on a container platform | `Dockerfile` present; no deployment config found | inferred, confirm with user |
| Purpose of the product | README is the default template text | unknown, ask the user |
| Why PostgreSQL was chosen | no ADR, no note | unknown, do not write a reason |

Statuses are defined this way: **confirmed** means you saw it in a file or command output; **inferred** means a reasonable reading of the evidence that something else could contradict; **unknown** means you did not find it.

### Discovering commands safely

Find commands in this order of reliability, and note conflicts instead of resolving them silently:

1. The task runner or package manifest scripts (the `scripts` section, a Makefile, a justfile, a task runner file).
2. The CI workflow steps that run build and test (they are exercised automatically, so they are more likely current than a README).
3. The README and contributing guide (often stale; treat as a lead to verify).
4. The framework's convention if nothing else exists (confirm the version first with context7).

For each of install, dev, test, lint, type-check and build, record: the command, where it came from and what it does.

Before running anything, read the body of the script. Run only commands you understand. These are never run during onboarding without the user's explicit approval for that exact command: anything named or doing deploy, release, publish, push, migrate, seed, reset, drop, clean-all or destroy; anything that talks to a remote service, production data or a paid service; anything that writes outside the repository. A test command that needs a database or network is run only after confirming its configuration points at a local or test target. Installing existing dependencies from the lockfile is expected, but adding or upgrading a dependency is not part of onboarding and needs approval.

When commands fail, capture the exact error. A failing baseline is information, not a task; report it and move on. If the environment is broken (missing runtime, missing service), report what is needed and stop rather than improvising.

### Filling the `AGENTS.md` Project block

The Project block has four lines: name, purpose, stack and commands. Fill each only from the ledger.

1. Draft the exact replacement text and show the user a before and after.
2. Mark anything inferred, and leave the purpose as a question for the user if the repository does not state it. The purpose is a statement of intent, so it is the user's to give.
3. After approval, the implementer edits only those placeholder lines, under the recorded approval, and nothing else in the file. `AGENTS.md` changes only with the user's approval.
4. Commands use the format already in the file, one command per label.

Before and after:

```
Before:
- Name: <project name>
- Purpose: <one sentence>
- Stack: <languages, frameworks, database, hosting>
- Commands: install `<cmd>` | dev `<cmd>` | test `<cmd>` | lint `<cmd>` | build `<cmd>`

After (approved by the user):
- Name: Acme Orders
- Purpose: Order management API for Acme's storefront.
- Stack: TypeScript 5, Node 20, Express 4, PostgreSQL 16; container hosting (to be confirmed)
- Commands: install `pnpm install --frozen-lockfile` | dev `pnpm dev` | test `pnpm test` | lint `pnpm lint` | build `pnpm build`
```

(The values above are an example; use only what the repository shows.) Type-check is part of the verification set; if it is a separate command, list it where the project's file format allows, or note it with the test command.

### Bootstrapping `docs/`

Create only what the evidence supports. A missing document is created with its template headings and the unknowns marked; an existing document is corrected only where it is provably wrong, and disagreements between a document and the code are reported to the user, not resolved silently.

| File | Owner | Build it from | Leave as unknown |
|---|---|---|---|
| `README.md` | implementer | Verified commands, the manifest, `.env.example` names | Purpose if not stated; anything not run |
| `docs/PRD.md` | architect | What the user states and what the code demonstrably does, labelled as observed | Goals, success measures, target users |
| `docs/ARCHITECTURE.md` | architect | Directory structure, entry points, module imports, container and CI files | Rationale for decisions; deployment topology without evidence |
| `docs/DB.md` | architect | Migrations, model or schema files | Production data volumes, live-only objects |
| `docs/API-CONTRACTS.md` | architect | Route definitions, an OpenAPI or schema file, request validators | Undocumented behaviours; consumers |
| `docs/DESIGN.md` | architect | Only for projects with a UI: component structure, design tokens in code | Visual intent |
| `docs/adr/` | architect | Decisions explicitly recorded somewhere (README, commit messages with reasons) | Past decisions with no written reason: do not backfill a reason |
| `CHANGELOG.md` | implementer | The template with an empty Unreleased section; do not reconstruct history | Past releases unless the user supplies them |
| `docs/TASKS.md` | orchestrator | The template | Backlog items unless the user provides them |
| `docs/MEMORY.md` | orchestrator | Confirmed conventions, constraints and pitfalls with evidence | Preferences the user did not state |

Rules for bootstrapped content:

- Phrase observations as observations: "The code registers these routes" is evidence; "the system is designed for X" is a guess.
- Do not record a decision's reason unless a source states it. "Unknown: no record of why" is a valid entry.
- Each document is written by its owner (`AGENTS.md`, Source of truth). Do not let two agents edit one file at the same time.
- Verify every path and command written down: every referenced file exists and every documented command was run.
- Record `updated` for each created file in the documentation sync table.
- For writing conventions and structure, load `technical-documentation`; for ADR rules, `system-architecture`.

### Special cases

| Situation | What to do |
|---|---|
| Monorepo with several packages | Record the workspace tool and the root commands; then per-package commands in a table; do not assume the same commands everywhere |
| Several languages | One stack line listing each with its version; commands per language |
| No tests | Record "no automated tests found" as the baseline; propose adding tests as a follow-up, do not add them during onboarding |
| README says one thing, CI does another | Record both; prefer verified behaviour; tell the user |
| Failing baseline | Record, do not fix; later tasks must not be blamed for it |
| Greenfield (empty or template repository) | Nothing to discover: ask the user for stack and purpose, then use the feature-development playbook for the first task |
| Secrets found in the repository | Report path and kind, never the value; recommend rotation; escalate to the user, and consider the security-auditor (skill `security-engineering`) |
| Existing agent or contributor instructions | Read them, report differences with `AGENTS.md`, do not edit either without the user's decision |

### Closing the onboarding

The final report lists: the stack and commands confirmed, the baseline (including pre-existing failures), the documents created or updated (and by whom), the unknowns for the user, the risk map, and proposed follow-up tasks. The orchestrator updates `docs/TASKS.md` and `docs/MEMORY.md`.

## Examples

### Discovery brief to `explore`

```
Goal: Inventory the repository for onboarding; change nothing.
Task file: .agents/tasks/onboard-acme-orders.md
Context: New to this repository. AGENTS.md Project block still holds placeholders.
Scope: Read-only. List manifests and versions, entry points, test and CI setup, existing docs, data model files.
Out of scope: Opening .env or key files, running any command that writes, editing anything.
Acceptance criteria:
  1. Each fact reported with the file path or command that shows it.
  2. Files that appear to hold secrets are listed by path only.
Skills: none
Research: use context7 and gh_grep as required by AGENTS.md
Return: the standard report
```

### Baseline table

```
Command                Source                   Result
pnpm install --frozen-lockfile   package.json, CI   ok, 0 warnings
pnpm test                         package.json scripts.test   138 pass, 4 fail, 0 skipped (pre-existing: tests/legacy/*.test.ts)
pnpm lint                         package.json scripts.lint   0 errors, 12 warnings (pre-existing)
pnpm build                        package.json scripts.build  ok
Not run: pnpm deploy (deploy script; needs user approval)
```

### A bootstrapped `docs/ARCHITECTURE.md` fragment with unknowns

```
## Components (observed)
- src/routes: HTTP handlers registered in src/server.ts:21-34.
- src/orders: order logic and repository (src/orders/repo.ts uses the pg client).
- Background jobs: none found.

## Deployment
Unknown: a Dockerfile exists but no deployment configuration was found. Confirm hosting with the user.

## Decisions
Unknown: no ADRs and no recorded reasons for the framework or database choice.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Copying commands from the README without running them | Stale commands break every later task | Trace to scripts or CI, run, record results |
| Inventing a purpose or a rationale | Future agents rely on fiction | Write "Unknown" and ask the user |
| Opening `.env` to learn variable names | Exposes secrets in logs and context | Use `.env.example` names only |
| Running a deploy, seed or migrate script to "see what happens" | Real side effects | Read scripts first; ask before anything with side effects |
| Fixing baseline failures during onboarding | Mixes unrelated changes into the first task | Record them as pre-existing; propose follow-ups |
| Editing `AGENTS.md` beyond the placeholders | Changes core agent rules without approval | Fill only the approved placeholder lines |
| Backfilling ADRs with guessed reasons | Creates false records | Record only decisions with a written source |
| Writing docs from the framework's typical layout | Describes a project that does not exist | Describe the code you actually read |
| Letting two agents edit one file | Overwrites and lost work | One writer per file, owners as in `AGENTS.md` |
| Resolving a doc-versus-code conflict silently | Hides which is right | Report both and ask the user |

## Checklist

- [ ] The class and risk were stated and the user's onboarding goal is recorded.
- [ ] Inventory was read-only and no secret file was opened or printed.
- [ ] Every command in the Project block traces to a script, CI step or verified source.
- [ ] Each command was run, with exit status and counts recorded, or its blocker noted.
- [ ] Pre-existing failures are listed and were not fixed.
- [ ] The user approved the exact `AGENTS.md` text before it changed, and only placeholder lines changed.
- [ ] No placeholder remains in the Project block; unknowns are marked, not guessed.
- [ ] Each bootstrapped doc claim traces to the ledger; every path and command in it was verified.
- [ ] Conventions, pitfalls and the risk map are in `docs/MEMORY.md` with evidence.
- [ ] The documentation sync table has a result for every file, and follow-ups are proposed but not started.

## Verify with context7 and gh_grep

- **context7:** for the runtime, framework and package manager versions in the lockfile, query "`<package manager>` `<version>` install from lockfile frozen flag", "`<test framework>` `<version>` run tests and exit codes", "`<framework>` `<version>` default project layout and start command".
- **gh_grep:** search literal code for how comparable projects expose commands and documents them: `"scripts": {`, `run: pnpm test`, `.PHONY: test`, `"engines": {`, and the exact text of any install or build error.

## Sources

- Keep a Changelog 1.1.0 (Unreleased section, change types, do not reconstruct from commit logs): https://keepachangelog.com/en/1.1.0/
- Architectural Decision Records (an ADR documents one decision and its reasoning; the records form the decision log): https://adr.github.io
