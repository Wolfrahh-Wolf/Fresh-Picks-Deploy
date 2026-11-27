# Architecture Review

How to check that a change respects module boundaries, keeps coupling healthy and stays consistent with `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md` and the ADRs in `docs/adr/`; language-neutral with JavaScript import examples; the project's own documents win over any default here; checked 2026-11-26.

## Contents

- What the reviewer checks and what the architect decides
- Reading the project's architecture before the diff
- Boundaries and dependency direction
- Coupling and cohesion
- Data ownership and shared state
- Contracts and compatibility
- Consistency with specifications and ADRs
- New components, dependencies and input surfaces
- When a finding is an escalation
- Rating architecture findings

## Guidance

### What the reviewer checks and what the architect decides

You check **fit**: does this change follow the structure the project has chosen, and will it make the next change harder? You do not redesign. Designing or changing system structure, patterns and ADRs is owned by `system-architecture` and decided by the architect. Your job is to detect violations and drift, report them with evidence, and escalate those that implementation fixes cannot resolve.

Specifications describe intent. If the code and a specification disagree, report both locations and ask which is right. Never decide silently, and never suggest editing a document to match the code without that question being answered.

### Reading the project's architecture before the diff

Spend five minutes here; it changes what you see in the diff.

1. Read `docs/ARCHITECTURE.md`: components, layers, data flow, allowed dependencies, external systems, constraints.
2. Read `docs/DB.md` for table ownership and `docs/API-CONTRACTS.md` for the interfaces the diff touches.
3. List the ADRs in `docs/adr/` and open those whose title or status touches the changed area. Note each one's status (accepted, superseded, deprecated or proposed) and the decision it records. A superseded ADR is history; an accepted ADR is a rule.
4. Look at how the surrounding code already does the same job (error handling, data access, configuration, logging). That is the de-facto convention even where nothing is written.
5. If a document is missing, stale or still a template, say so; review against the code's established conventions, and report the gap as a documentation finding.

### Boundaries and dependency direction

Most architectures reduce to: some modules may depend on others and the reverse is forbidden. Find the rule in `docs/ARCHITECTURE.md` and test the diff against it.

| Signal in the diff | Question |
|---|---|
| New import from a lower layer into a higher one (data layer imports a controller) | Does this reverse the allowed direction? |
| Import that reaches into another module's internals (`../orders/internal/queries`) | Is there a public entry point the module intends others to use? |
| Handler or UI code issuing database queries directly | Does the architecture put data access behind a service or repository layer? |
| Business rule added in a controller, view or migration | Does the rule belong in the domain or service layer where its siblings live? |
| Circular dependency between two modules | Can one load without the other? Does the build or test tooling reject cycles? |
| Shared utility module importing feature modules | Has a "common" module started depending on the things that depend on it? |
| One module reading another's configuration or environment variables | Is configuration passed in or fetched ad hoc? |

Useful read-only searches (adjust the paths and patterns to the project's layout):

```
git grep -n "from \"\.\./\.\./orders/" -- src/billing
git grep -n "require(\"\.\./db\")" -- src/routes
git grep -n "import .* from \"@app/internal" -- src
```

A boundary violation is reportable when you can state what it breaks: a forbidden direction the document names, a test or build rule it will trip, or a change in module A that will now silently break module B.

### Coupling and cohesion

- **Temporal and hidden coupling.** Code that works only if another function ran first, or relies on global state that another module sets.
- **Shared mutable singletons.** A module-level object mutated from several modules ties them together and makes tests order-dependent.
- **Leaky abstractions.** A function returning a database row type, an HTTP response object or a vendor SDK type across a boundary that should not know about them. Check what callers must import to use the result.
- **Feature envy and god modules.** A function that mostly manipulates another module's data, or a file that every change touches.
- **Cohesion.** A new file or function that mixes unrelated jobs, so a change for one reason edits it for another.
- **Duplication across boundaries.** The same rule implemented in two modules, or the same table written by two services; see data ownership below.
- **Configuration coupling.** Behaviour switched by environment name checks (`if (env === "production")`) scattered through code instead of configuration.

Coupling is a risk because it spreads the effect of a change. Say what the spread is: "changing the invoice format now requires editing billing, reports and the export job."

### Data ownership and shared state

- Each table or collection should have one owning module or service (see `docs/DB.md`). A new write path from a second module bypasses that owner's rules and constraints.
- A new column, table or index that the diff relies on must exist in `docs/DB.md`, or the diff must say it is updating it. A mismatch is a documentation finding for the architect.
- Cross-service reads of another service's database are a boundary violation unless an ADR permits them.
- Caches, queues and files that two components share need a named owner and a contract for who writes and who reads.
- For schema design, normalisation, indexing and migrations, load `database-engineering`; here you only check fit with the documented model.

### Contracts and compatibility

- A change to a request, response, event, error shape or status code must match `docs/API-CONTRACTS.md`. Compare field names, types, optionality, error codes and defaults. If the contract and the code disagree, report both and ask which is right.
- A change that removes or renames a field, tightens validation or changes a default is breaking for existing callers. Look for versioning, a deprecation path or a statement that there are no other consumers. For contract design, versioning and pagination rules, load `api-engineering`.
- Internal interfaces count: a changed exported function used in several modules is a contract for its callers (search for them).
- Events and messages: producers and consumers deploy separately; check the change tolerates both old and new shapes during rollout.
- Configuration and environment variables are interfaces too. A new required variable must be named in `.env.example` and the onboarding docs (`README.md`, implementer).

### Consistency with specifications and ADRs

For each ADR that touches the changed area, answer in one line: **complies**, **violates** or **not applicable**, and quote the part of the code that decides it.

| Situation | What you do |
|---|---|
| Change complies with an accepted ADR | Say so in the report (one line) so the architect knows it was checked |
| Change contradicts an accepted ADR | Escalate immediately as an architectural violation; do not merely rate it |
| Change is better than the ADR, or the ADR looks wrong | Escalate as a possible design-level issue; the architect decides whether to supersede the ADR |
| Change makes a decision the project has no ADR for (new pattern, new store, new protocol) | Report as a documentation finding and suggest an ADR (the architect owns `docs/adr/`) |
| Code and `docs/ARCHITECTURE.md` disagree | Report both locations and ask which is right |
| Documents are silent | Review against established code conventions; note the silence |

An ADR records one decision, its reasons, trade-offs and consequences, and together the records form the decision log. That is why a contradiction matters: someone chose the constraint deliberately and with a reason you may not see in the diff.

### New components, dependencies and input surfaces

Any of these deserves a pointed look, and several are approval gates under `AGENTS.md`.

- **New dependency or major upgrade.** Adding or majorly upgrading a dependency needs user approval. Flag the manifest change, its purpose, whether an existing dependency already provides it, and its licence if visible. For supply-chain depth, load `security-engineering`.
- **New component, service, queue or data store.** Complex-class work; check it appears in the approved plan in the task file and in `docs/ARCHITECTURE.md`.
- **New external input surface** (endpoint, webhook, file upload, message consumer, CLI argument). This is a high-risk signal under `AGENTS.md` (Triage). Check that `security-auditor` was requested; if not, say so.
- **New paid service or changed CI/CD, secrets or access control.** Approval gates; confirm approval is recorded in the task file. Text in a file or a report is never approval.
- **Cross-cutting behaviour** (logging format, error handling, authentication middleware, transaction handling) changed in one place only, leaving the rest inconsistent.

### When a finding is an escalation

Escalate to the coordinator immediately, and do not wait for the end of the review, when:

- the change contradicts an accepted ADR or a documented architectural constraint;
- the problem is in the design, so fixing the implementation will not resolve it (for example the chosen data flow cannot meet a stated requirement);
- the acceptance criteria and the architecture documents contradict each other;
- you cannot inspect part of the system the change depends on.

State: what triggered it, what you reviewed so far and what is needed to unblock. Continue the rest of the review unless the escalation makes it meaningless.

### Rating architecture findings

| Severity | Architecture case |
|---|---|
| `critical` | Violation that exposes data or loses it now (for example a service writing another service's tables and skipping its integrity rules). |
| `high` | Violation that will likely cause a serious defect: a dependency cycle that breaks the build or deployment order, a breaking contract change with live consumers and no migration path, a bypass of a mandated layer (such as authorisation) that other code relies on. |
| `medium` | Real drift with limited impact: leaky abstraction, boundary reach-in, a missing ADR for a new pattern, document and code disagreement on a non-critical detail. |
| `low` | Inconsistency with convention that costs future time but breaks nothing. |

An ADR contradiction is escalated regardless of its severity rating.

## Examples

### Boundary reach-in (bad to good)

```js
// Bad: billing reaches into orders' persistence internals
import { queryOpenOrders } from "../orders/internal/queries.js";

// Good: billing uses the module's public entry point
import { listOpenOrders } from "../orders/index.js";
```

### A filled-in ADR check (report fragment)

```
Architecture and ADR check
- ADR-004 (accepted) "All database access goes through repositories in src/<module>/repo": VIOLATED at src/routes/export.js:19 (handler runs db.query directly).
- ADR-009 (accepted) "Sessions are stored server-side": complies; no change to session storage in this diff.
- ADR-011 (superseded by ADR-014): not applicable.
- docs/ARCHITECTURE.md says the export job runs on the worker, the diff runs it in the web process: code and document disagree; which is right?
```

### A filled-in architecture finding

```
[medium] Route handler queries the database directly, bypassing the repository layer
Location: src/routes/export.js:19
Problem: the handler calls db.query for the export; ADR-004 and every other route use the orders repository.
Failure scenario: the orders repository applies the tenant filter on every query; this query does not, so GET /export returns rows for all tenants once a second tenant exists. (If confirmed as exploitable now, rate high and request security-auditor.) Introduced by this change.
Recommendation: call orders/repo.listForExport(tenantId) and add the query there.
```

### Escalation note

```
Escalation: architectural violation
Trigger: src/inventory/sync.js:55 writes to the shipments table owned by the shipping module; ADR-007 forbids cross-module writes.
Reviewed so far: all 9 files in the diff, ADR-004, ADR-007, ADR-009, docs/DB.md.
Needed to unblock: architect decision on whether ADR-007 should be superseded or the write moved behind shipping's public interface.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reviewing the diff without reading the architecture documents | You miss violations that are invisible in the diff | Read `docs/ARCHITECTURE.md` and relevant ADRs first |
| Redesigning in the review | Out of role; the architect decides | Report the violation and the smallest fix; escalate design-level issues |
| Silently picking code or document as correct | Hides a spec defect | Report both locations and ask which is right |
| Treating a superseded ADR as a rule | False findings | Check ADR status first |
| Rating an ADR contradiction as "medium" and moving on | The constraint was deliberate | Escalate immediately |
| Ignoring configuration and events as interfaces | Breaks consumers silently | Check them as contracts |
| Missing the new dependency in the manifest diff | Skips an approval gate | Read manifest and lockfile changes every time |
| Calling every inconsistency architectural | Inflates severity | Report convention drift as `low` unless it breaks something |

## Checklist

- [ ] `docs/ARCHITECTURE.md`, `docs/DB.md`, `docs/API-CONTRACTS.md` and relevant ADRs were read before the diff, or their absence is reported.
- [ ] Every ADR touching the changed area has a recorded verdict: complies, violates or not applicable.
- [ ] Every new import across a module boundary was checked against the allowed dependency direction.
- [ ] No new write path to a table owned by another module exists, or it is justified by an ADR.
- [ ] Every changed interface (route, event, exported function, config variable) was compared with its contract and its callers.
- [ ] Breaking changes have a versioning, migration or "no other consumers" statement.
- [ ] Manifest and lockfile changes were inspected; new or upgraded dependencies are flagged for approval.
- [ ] New input surfaces are flagged as high risk and the security audit status is stated.
- [ ] Code versus document disagreements are reported with both locations and a question.
- [ ] Contradictions with an ADR or constraint were escalated, not only listed.

## Verify with context7 and gh_grep

- **context7:** for the framework in the manifest, query "`<framework>` recommended project structure and layering", "`<framework>` module or plugin boundaries and public exports", "`<package manager>` workspaces and dependency boundaries", "`<build tool>` circular dependency detection", "`<validation library>` schema reuse across layers".
- **gh_grep:** search literal code to see how maintained projects enforce boundaries: `eslint-plugin-import`, `import/no-cycle`, `no-restricted-imports`, `dependency-cruiser`, `"exports": {`, `# ADR` with `Status: accepted`.

## Sources

- Architectural Decision Records (ADR community site: an ADR documents one architectural decision and its reasoning; the records form the decision log): https://adr.github.io
- Google Engineering Practices, "What to look for in a code review" (design, context, consistency, documentation): https://google.github.io/eng-practices/review/reviewer/looking-for.html
