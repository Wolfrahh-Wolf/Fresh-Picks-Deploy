---
name: system-architecture
description: "Use when designing or changing system structure, component boundaries, data flow, scalability or design patterns, or when recording an architecture decision."
---

# System Architecture

Produce the simplest design that meets the stated quality attributes, and record the trade-offs so a later reader can see why it was chosen. This is the architect's procedure and router; the depth lives in the references.

## When to use

- A change adds, removes, splits or merges a component, module, service, queue or data store.
- A change alters how components talk to each other: call direction, synchronous versus asynchronous, ownership of data, behaviour when a dependency fails.
- Someone asks which structural style fits (layered, modular monolith, hexagonal, event-driven, microservices) or whether a design pattern is warranted.
- A requirement carries a load, availability or latency target and the design must show how it is met.
- A decision is costly to reverse (new dependency, data store, hosting model, auth model, public interface shape, architectural style) and needs an ADR.
- Specification docs must be synced with a structural change (`docs/ARCHITECTURE.md`, `docs/adr/`).

## Do not use for

- API shapes (resources, payloads, status codes, versioning, pagination): load `api-engineering`.
- Schema design, indexes, transactions and migrations: load `database-engineering`.
- Writing `docs/ARCHITECTURE.md` prose, diagrams and style conventions: load `technical-documentation`. The rules for ADRs stay in this skill.
- Threat modelling and security audit: load `security-engineering`.
- Eliciting, rewording or testing requirements and acceptance criteria: load `requirements-engineering`.
- PRD, task breakdown and estimates: load `product-technical-planning`.
- Comparing technologies or proving feasibility: load `technical-research`.
- Implementing caching, error handling or auth in server code: load `backend-engineering`.
- Pipelines, deployment, rollback and monitoring setup: load `devops-deployment`.

An architect loads this skill first and at most two more. If the task needs a topic above, pick the one skill that matters most and note the gap in the report.

## Research: context7 and gh_grep

- You MUST consult **context7** before naming a library, framework, message broker, database driver, resilience library or hosting feature in a design, and before stating any default, limit, delivery guarantee or configuration option. Check the project's manifest or lockfile first and query that version. Useful queries: "delivery guarantees and ordering for `<broker>` at version `<x>`", "timeout and connection pool options in `<http client or driver>`", "retry and circuit breaker configuration in `<resilience library>`", "module or package boundary features in `<framework>`".
- You MUST search **gh_grep** when a pattern or integration is unfamiliar, when documentation is ambiguous about how a component behaves under failure, or before recommending a structure the project has not used yet. Search literal code. Useful searches: `CircuitBreaker`, `idempotency_key`, `dead_letter`, `Retry-After`, `class .*Adapter`.
- Pure project-internal structure (naming a module, moving a boundary inside the repository, writing an ADR about an existing choice) needs neither tool. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/architecture-patterns.md](references/architecture-patterns.md) | Choosing or changing the structural style: layered, modular monolith, hexagonal, event-driven or microservices; judging a proposed split or extraction. |
| [references/system-design.md](references/system-design.md) | Starting any design: pinning constraints and quality attributes, drawing boundaries and interfaces, tracing data flow, analysing failure modes, comparing options. |
| [references/scalability.md](references/scalability.md) | The task has a load, data-growth or availability target; or touches timeouts, retries, queues, replication, partitioning, load balancing or overload behaviour. |
| [references/design-patterns.md](references/design-patterns.md) | Inside one component: a creational, structural or behavioural pattern is proposed, or a design looks over-engineered. |
| [references/adr.md](references/adr.md) | A decision is costly to reverse, an ADR must be written, numbered, superseded or reviewed. |

## Workflow

Only the architect loads this skill. The implementer, tester and reviewers receive its results through `docs/ARCHITECTURE.md`, `docs/adr/` and the task file; they do not load it. The coordinator, not the architect, decides class and routing.

1. **Orient.** Read the brief, the task file, `docs/ARCHITECTURE.md`, `docs/adr/`, `docs/MEMORY.md` and the code the change touches. Do not design from documents alone. Check whether an accepted ADR already decides the question; if so, follow it or propose superseding it. Exit check: you can state the current structure in three sentences.
2. **Pin the drivers.** List constraints, assumptions and quality attributes. Give every quality attribute a measurable target or mark it **open**. Load `references/system-design.md`. If requirements conflict or a target cannot be met, escalate as the architect definition says instead of choosing silently.
3. **Generate options.** Write at least two viable options. The first is always "extend what exists". Compare on implementation cost, operational complexity, risk, reversibility and fit with existing patterns. Load `references/architecture-patterns.md` for style-level options and `references/design-patterns.md` for options inside a component.
4. **Test against load and failure.** If a target involves volume, latency, availability or data growth, do the arithmetic and write the inputs down. For every network call, queue and shared resource, state the timeout, retry rule, idempotency need and degraded behaviour. Load `references/scalability.md`. Exit check: no dependency has an unstated failure behaviour.
5. **Choose the simplest option that meets the targets.** Prefer the more reversible option when two are close. Name the measurable trigger that would reopen the decision. Reject options with concrete reasons, never "too complex".
6. **Record the design in its owning docs.** Update `docs/ARCHITECTURE.md` and, where the change reaches them, `docs/DB.md`, `docs/API-CONTRACTS.md`, `docs/DESIGN.md` or `docs/PRD.md`. Route the content of those shapes to their skills. Write an ADR for every decision costly to reverse, using `references/adr.md`. Status stays `proposed` until the user approves.
7. **Hand off to the plan.** Fill the task file's Plan, Files in scope and Acceptance criteria so each task can be verified alone. Put boundary rules into acceptance criteria as observable checks. Flag: security audit needed, migrations needing rollback, dependencies needing approval, criteria you could not make testable (mark **open**).
8. **Sync and report.** Compare every file in the source-of-truth table with the change, record `updated` or `no change` per file, and return the standard report with the additions under Output.

When reviewing existing structure rather than designing: start at step 1, then compare the code with the recorded design. If they differ, report the difference and ask which is right; never edit the design to hide it.

## Standards

- Every quality attribute in a design has a number and a way to measure it, or is marked **open**. Words such as "fast" or "scalable" alone are not accepted.
- Every significant decision lists at least two options and a concrete reason for each rejection.
- Existing architecture and project conventions are the default. Introducing a new style, pattern or dependency needs a stated reason in the design.
- The default structure is one deployable with enforced module boundaries. Split into separately deployed services only for a named driver: independent release cadence, divergent scaling profile, fault isolation or team ownership.
- Every component states one responsibility, the data it owns and its public interface. Each datum has exactly one owning component that writes it.
- Dependencies point one way. A cycle between modules or layers is a defect to remove before the design is accepted.
- Every call across a process or network boundary has a timeout. Retries apply only to idempotent operations, use backoff with jitter, are bounded, and happen at one layer.
- Every asynchronous consumer tolerates duplicate delivery and has a dead-letter or equivalent path for messages it cannot process.
- Every queue or buffer is bounded and has a stated overload behaviour: reject, shed or degrade.
- Every capacity claim shows inputs, formula and result. Inputs that were not measured are labelled as assumptions.
- No speculative abstraction. A pattern or extension point must name the variation or problem that exists now; foreseen extensions are noted, not built.
- Every external dependency has a stated user-visible behaviour for when it is unavailable.
- Every decision costly to reverse has an ADR. An accepted ADR is changed only in its status line; a reversed decision is superseded by a new ADR, never deleted or rewritten.
- The design is recorded in the owning docs, not only in the task file. Docs describe the decision, not what was built; departures are reported.
- Designs and ADRs are never marked approved by the architect. Approval comes from the user, and an ADR does not authorise a gated action.
- Every change to data or state names its reversal path; the steps belong to `database-engineering` or `devops-deployment`.
- Each assumption is marked as an assumption and each unconfirmed claim as **unverified**.

## Verification

- [ ] Each quality attribute has a target and a measurement, or the word **open**. Evidence: the quality attribute table in the design.
- [ ] List `docs/adr/`: new numbers are the highest existing number plus one, none repeats, `0000-template.md` is untouched.
- [ ] Search the new and changed docs for `TODO`, `NNNN`, `YYYY` and leftover angle-bracket placeholders: none remain.
- [ ] Each new ADR has at least two options considered, a Consequences section naming negative effects, and a Verification section.
- [ ] Search the source for imports that cross a boundary the design forbids. Use the project's own dependency-rule check if one exists; otherwise a text search for the forbidden path. If the architect cannot run it, name the command the implementer must run.
- [ ] Every network call, queue and external dependency in the design appears in a failure-mode table with timeout, retry rule and degraded behaviour.
- [ ] Capacity arithmetic can be recomputed from the written inputs and gives the stated result.
- [ ] `docs/ARCHITECTURE.md` Related decisions section lists each new or superseded ADR.
- [ ] The documentation sync table in the task file shows `updated` or `no change` for every source-of-truth file.
- [ ] Every claim about a library, broker or platform has a context7 query or the label **unverified**.

## Output

Return the standard report from `AGENTS.md`. Add these specifics:

- **Summary:** the chosen design in a few sentences, the rejected options with concrete reasons, the risks, and whether a security audit is required (yes or no, with the boundary that triggers it).
- **Evidence:** documents and code read, the arithmetic performed with its inputs, the boundary check run or named for the implementer, and the ADR numbers checked for conflicts.
- **Research:** the context7 and gh_grep queries used and what they confirmed, or "pure project-internal structure; neither needed".
- **Docs impact:** per file, `updated`, `no change` or `needs update` with a reason.

Files this work can affect, with owners:

| File | Owner | Typical change |
|---|---|---|
| `docs/ARCHITECTURE.md` | architect | Components, flows, quality attributes, topology, risks, Related decisions |
| `docs/adr/NNNN-<slug>.md` | architect | New ADR, or the status line of a superseded one |
| `docs/DB.md` | architect | Data ownership changes (schema content via `database-engineering`) |
| `docs/API-CONTRACTS.md` | architect | New or changed interface between components (shape via `api-engineering`) |
| `docs/DESIGN.md`, `docs/PRD.md` | architect | Only when the structural change alters UX or requirements |
| Task file Plan, Files in scope, Acceptance criteria | architect | Tasks and observable boundary checks |
| `docs/TASKS.md`, `docs/MEMORY.md` | coordinator | Status; a pointer to a durable decision, constraint or pitfall |
| `README.md`, `CHANGELOG.md` | implementer | Only if setup or visible behaviour changes |
