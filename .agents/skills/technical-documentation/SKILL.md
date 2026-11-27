---
name: technical-documentation
description: "Use when writing or syncing README, API docs, architecture docs or the changelog, and after every successful task to keep docs current."
---

# Technical Documentation

Keep every project document accurate, concise and owned by one role. This skill covers writing the README, API documentation, architecture, database and design docs, and the changelog, and running the documentation sync that `AGENTS.md` requires after every successful task.

## When to use

- A change alters behaviour, setup, configuration, commands, an interface, the data model, a component or a user flow, and a document may now be wrong.
- The brief asks you to write or refresh `README.md`, `CHANGELOG.md`, `docs/API-CONTRACTS.md`, `docs/ARCHITECTURE.md`, `docs/DB.md` or `docs/DESIGN.md`.
- A task finished and the `Documentation sync` step of `AGENTS.md` is due. It is due after every successful operation, including trivial ones.
- You must add a diagram, a quick start, an API example or a release section to a document.
- You must check that documented commands, links, examples or diagrams still work.

## Do not use for

- ADR rules (when to write one, its format, status handling): load `system-architecture`.
- PRD content, user stories, task breakdown and estimates: load `product-technical-planning`.
- `docs/TASKS.md`, `docs/MEMORY.md` and task files: load `project-memory`. The coordinator owns them.
- Designing the API itself, OpenAPI authoring, versioning policy: load `api-engineering`.
- Schema design, index choice, migration technique: load `database-engineering`.
- Commit message conventions, branches, pull requests: load `git-version-control`.
- Tagging, publishing and deploying a release: load `devops-deployment`.

## Research: context7 and gh_grep

- You MUST consult **context7** before documenting any command, flag, option, config key or API of a library, framework, CLI or cloud service, and before using a diagram syntax you have not already used in this project's docs. Check the project's manifest or lockfile first and query that version. Useful queries: `mermaid erDiagram attribute keys`, `mermaid sequenceDiagram alt else block`, `<framework> list registered routes`, `<framework> generate OpenAPI document`, `<package manager> list project scripts`.
- You MUST search **gh_grep** when you are unsure how a documentation convention or diagram is written in maintained projects, or when a rendering error is not explained by the docs. Search literal text. Useful searches: `## [Unreleased]`, `**Breaking:**`, `[Unreleased]: https://github.com/`, `erDiagram`, `sequenceDiagram`.
- Describing what this repository's own code does needs neither. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/readme.md](references/readme.md) | Writing or updating the README: structure, quick start, setup, and proving every documented command works. |
| [references/api-documentation.md](references/api-documentation.md) | Documenting endpoints or events: reference entries, guides, examples, and keeping docs in step with the contract. Also holds the Diátaxis page-type rules used by every document. |
| [references/architecture-documentation.md](references/architecture-documentation.md) | Writing or syncing `ARCHITECTURE.md`, `DB.md` or `DESIGN.md`, or adding a diagram as code. |
| [references/changelog.md](references/changelog.md) | Adding a changelog entry, writing a release section, or marking a breaking change or deprecation. |
| [references/docs-sync.md](references/docs-sync.md) | Running the post-task documentation sync: who owns which file, mapping a change to the docs it affects, and filling the per-file result table. |

## Workflow

### 1. Scope the change

1. Read the brief, the task file, the diff and the `Source of truth` table in `AGENTS.md`. List what changed in user-visible, operator-visible, interface, data, component and flow terms.
2. Decide the mode. **Explicit documentation task:** you were asked to write or refresh named files. **Post-task sync:** a task finished and you must check every file in the source-of-truth table. Load `references/docs-sync.md` for the second mode, every time.

### 2. Decide what to touch

3. Map the change to documents with the impact table in `references/docs-sync.md`. Mark each of the eleven files `update` or `no change`, with a one-line reason.
4. Split the list by owner. Edit only the files your role owns. Name the rest in `Docs impact` for their owner.
5. Choose the page type before writing: tutorial, how-to guide, reference or explanation. One page serves one type. The rules are in `references/api-documentation.md`.

### 3. Write from the source

6. Take every fact from the code, manifest, schema, contract or a command you ran. Do not copy it from another document. Where the code and a specification disagree, stop and report which differ and ask which is right. Do not edit either to match.
7. Make the smallest edit that makes the document true. Keep the project's existing structure, headings and tone. Link to the single source of a fact instead of copying it.
8. Load the matching reference for the file you are editing and follow its structure.

### 4. Verify and record

9. Run the verification checks below. Label anything you could not run, with the reason.
10. Fill the per-file result table: `updated` or `no change` for each file, as `AGENTS.md` requires.
11. Report using the format under Output.

### Differences by role

| Aspect | implementer | architect |
|---|---|---|
| Files you edit | `README.md`, `CHANGELOG.md`, `.env.example` names it adds | `docs/PRD.md`, `DESIGN.md`, `ARCHITECTURE.md`, `DB.md`, `API-CONTRACTS.md`, `docs/adr/` |
| Mostly uses | `readme.md`, `changelog.md`, `api-documentation.md` (guides and examples) | `architecture-documentation.md`, `api-documentation.md` (contract entries) |
| When a spec is affected | Name the file in `Docs impact` for the architect. Never edit it. | Edit it, then compare it with what was built. |
| When code departs from a design | Report the departure. Do not redesign. | Report the difference. Do not rewrite the design to hide it. |
| README or changelog needs a change | Make it. | Name it in `Docs impact` for the implementer. |
| Status of a spec | Not yours to change. | Leave `Status` as it is. Only the user approves. |

The coordinator updates `docs/TASKS.md` and `docs/MEMORY.md` and collects every per-file result.

## Standards

- Edit only the files your role owns under `AGENTS.md`. Name any other affected file in `Docs impact`.
- Run the documentation sync after every successful operation, including trivial ones. A sync with no edits is valid when every file is recorded `no change` with a reason.
- Documents describe what is true now. Mark intended-but-unbuilt design as `Planned` and remove the mark once it is built and verified.
- Never edit code or a specification to match the other. Report the disagreement and ask.
- Every command, flag, path, environment variable and code example in a document is checked against the code or run. Anything not run is labelled `not run` with the reason.
- State each fact once. Link to its source: variable names in `.env.example`, contracts in `docs/API-CONTRACTS.md`, token values in the token file.
- One page serves one Diátaxis type. Reference states facts without instructions. How-to guides assume a competent reader.
- Every user-visible or operator-visible change gets one changelog entry under `[Unreleased]`, using only the six Keep a Changelog types. Internal-only changes get none.
- Mark every breaking change with `**Breaking:**`, say what breaks, and give the migration.
- Changelog dates are `YYYY-MM-DD` from the system clock. Do not rewrite a released section except to correct a factual error, and report the correction.
- Diagrams are text (`mermaid` fenced blocks), labelled, small, and followed by a one-to-three sentence text description. No image-only diagrams.
- Use relative links inside the repository. A broken link is a defect.
- Put no secrets, tokens, real hostnames or personal data in any document. Use placeholders such as `<API_TOKEN>`.
- Commands that delete data, run migrations, deploy, publish or push carry a warning that they need user approval. Never run them to verify a document.
- Do not change a specification's `Status` and do not mark requirements approved. Propose changes to `AGENTS.md` or `CLAUDE.md` to the user first.
- Write plain, short, factual prose. No marketing, history, speculation or unfinished-work markers.

## Verification

- [ ] Every documented command was run in a clean checkout or labelled `not run` with the reason. Record the exit status of each.
- [ ] Every relative link resolves. Run the project's link checker, or list each link target and confirm the path exists.
- [ ] Every path, endpoint, flag, environment variable and table name mentioned was found in the code, manifest or schema by searching for it.
- [ ] Every API example was run against a local or test instance, or labelled `not run`.
- [ ] Every diagram renders on the docs host. Preview it there, or run a Mermaid render of the source and confirm exit status 0.
- [ ] `CHANGELOG.md` starts with `## [Unreleased]`, uses only the six type headings, and release dates are `YYYY-MM-DD`.
- [ ] A search of the changed docs for `TODO`, `lorem`, the project's own placeholder markers, `AKIA`, `ghp_` and `BEGIN .*PRIVATE KEY` returns nothing.
- [ ] The per-file table has one row for each of the eleven files in the `Source of truth` table, each `updated` or `no change`.
- [ ] The documentation diff contains only changes justified by the task. Review it with `git diff` before reporting.
- [ ] Nothing outside your role's files was edited.

## Output

Fill the standard report fields as follows.

- **Evidence:** each command you ran with its exit status and key output line, each link, example and diagram check, and every item you could not run with the reason.
- **Research:** the context7 and gh_grep queries used, or "none needed: described this repository's own behaviour".
- **Docs impact:** the per-file table from `references/docs-sync.md`, one line per file, plus any file that needs an update from another owner.

Affected files and owners:

| File | Owner |
|---|---|
| `README.md`, `CHANGELOG.md` | implementer |
| `docs/PRD.md`, `DESIGN.md`, `ARCHITECTURE.md`, `DB.md`, `API-CONTRACTS.md`, `docs/adr/` | architect |
| `docs/TASKS.md`, `docs/MEMORY.md` | coordinator |
| `AGENTS.md`, `CLAUDE.md` | changed only with user approval |

Filled example for `Docs impact`:

```
Docs impact:
  PRD.md: no change (requirements unchanged)
  DESIGN.md: no change (no UI)
  ARCHITECTURE.md: no change (no new component)
  DB.md: no change (no schema change)
  API-CONTRACTS.md: needs update for architect (POST /api/auth/login: add 429 response)
  adr/: no change (no costly decision)
  README.md: updated (Usage: login example; verified against local server)
  CHANGELOG.md: updated (Unreleased > Added: login endpoint)
  TASKS.md: coordinator
  MEMORY.md: coordinator
  AGENTS.md, CLAUDE.md: no change
```
