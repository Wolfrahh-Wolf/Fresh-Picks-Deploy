# System Design Method

A repeatable method for turning a request into a design that can be recorded in `docs/ARCHITECTURE.md`: constraints, quality attributes, boundaries, interfaces, data flow, failure modes and trade-off analysis. Language-neutral; checked on 2026-11-26 against the Azure Architecture Center architecture-styles guide, the Google SRE book chapter "Addressing Cascading Failures" (2017 edition), the Amazon Builders' Library article on timeouts, retries and backoff (2019) and Michael Nygard's ADR article (2011).

## Contents

- Frame: constraints, assumptions, quality attributes
- Quality attribute scenarios
- Boundaries and responsibilities
- Interfaces between components
- Data and control flow
- Failure-mode analysis
- Trade-off analysis
- The simplicity pass
- Mapping the design into the docs
- Design review

## Guidance

### Frame: constraints, assumptions, quality attributes

Do this before drawing anything. Write three short lists.

- **Constraints:** facts you cannot change in this task. Existing stack, hosting, budget, compliance, deadlines, existing ADRs, interfaces owned by others. Take them from the repository and `docs/`, not from memory.
- **Assumptions:** things you believe but have not confirmed. Mark each one. An assumption that changes the design if false is a risk: say how you will confirm it, or ask.
- **Quality attributes:** the non-functional properties that decide between options. Typical: latency, throughput, availability, durability, consistency, security, operability, cost, changeability. Give each a number and a way to measure it, or mark it **open**.

Pick the few that matter. A design that optimises ten attributes optimises none. State the top three and what is deliberately sacrificed.

If the requirements are unclear, conflicting or untestable, stop and load `requirements-engineering`; do not design around guesses. If two requirements contradict after two clarification attempts, escalate with the exact statements quoted.

### Quality attribute scenarios

Turn each important attribute into a scenario that can be tested. Use the form: source of the stimulus, the stimulus, the part of the system affected, the environment, the response, and a measurable response measure.

| Attribute | Scenario | Measure |
|---|---|---|
| Latency | A customer submits an order during normal load | p95 under 400 ms, measured at the edge |
| Availability | The payment provider times out for 10 minutes | Orders are accepted and queued; none lost; users see "payment pending" |
| Changeability | A new tax rule is introduced | Change confined to one module; no change in more than one deployable |
| Operability | A deploy goes wrong | Rollback completes in under 15 minutes without data loss |

If you cannot name a measure, mark the attribute **open** and list it in the report. Never invent a target to fill the table.

### Boundaries and responsibilities

A boundary is a line across which dependencies are controlled. Draw them in this order:

1. **System boundary:** what is inside, what is outside, and who or what talks across it (users, other systems, schedulers). Record it under "Context and boundaries".
2. **Components:** split by reasons to change, not by technology. A good component has one responsibility you can say in a sentence, owns its data, and has a public interface.
3. **Data ownership:** every datum has one owning component that is the only writer. Others read through the owner's interface or from events it publishes. When two components both need to write, you have found a missing component or a wrong boundary.
4. **Trust boundaries:** mark where data crosses from less trusted to more trusted. Record where they are; threat analysis belongs to `security-engineering`, and a design that adds or moves a trust boundary needs a security audit flag.
5. **Dependency direction:** draw arrows from caller to callee. Look for cycles. Remove them by extracting the shared concept, merging the two components, or inverting one dependency with an interface or an event.

Test each boundary with two questions: what would we have to change if this component were replaced, and what happens to the others when it is slow or down? If the answers are "many things" and "they fail too", the boundary is in the wrong place or missing a protective mechanism.

For choice of structural style, load [architecture-patterns.md](architecture-patterns.md).

### Interfaces between components

Decide the character of each interface here; leave its exact shape to the owning skill.

- **Direction and initiator:** who calls whom, and who owns the contract.
- **Synchronous or asynchronous:** use synchronous when the caller needs the answer to continue and can tolerate the callee's latency and failure; use asynchronous when work can finish later, when load is bursty, or when the callee's failure must not fail the caller.
- **Delivery and ordering needs:** at-least-once with idempotent handling is the normal assumption for asynchronous interfaces; say whether order matters and over which key.
- **Failure contract:** what the caller sees on timeout, rejection or an unavailable dependency.
- **Compatibility:** who consumes it and whether they can be upgraded together.

Output: a table of interfaces (caller, callee, sync or async, purpose, failure contract). For HTTP or event payload shapes, load `api-engineering`. For stored data shapes, load `database-engineering`.

### Data and control flow

Trace at least three flows end to end, each as a numbered sequence naming the component at each step and the data that moves:

1. The most common happy path.
2. The most important failure path (a dependency is down or slow).
3. The path that stresses the scale target (burst, large payload or large tenant).

At every step mark: where state is stored, where a transaction or consistency boundary begins and ends, and what is lost or duplicated if the process dies right there. Anything between two stores that cannot be updated atomically needs an explicit strategy (idempotent retry, compensating action or a durable outbox written in the same transaction as the state change). Choose the strategy here; its mechanics belong to `database-engineering`.

### Failure-mode analysis

For every network call, queue, shared resource and external dependency, fill one row. Do not skip the "boring" ones: the Google SRE material identifies overload, resource exhaustion and retries as the usual start of cascading failures, and the Amazon material makes a timeout on every remote call the baseline.

| Dependency | Failure modes | Timeout | Retry rule | Fallback or degraded behaviour | Blast radius | Detection |
|---|---|---|---|---|---|---|

Rules for the columns:
- **Failure modes:** include slow (not just down), partial, wrong answers, duplicate delivery and a full queue.
- **Timeout:** a number, chosen from the dependency's latency distribution; see [scalability.md](scalability.md).
- **Retry rule:** only for idempotent operations; backoff with jitter; bounded; at one layer of the stack.
- **Fallback:** what the user sees. "Error page" is a valid answer if stated; silence is not.
- **Blast radius:** which other components or tenants are affected, and whether an isolation mechanism (bulkhead, separate queue, separate pool) contains it.
- **Detection:** the metric or log line that shows it, so `devops-deployment` can wire the alert.

A design with an empty row is not finished. If you cannot fill a cell, write **open** and add an open question.

### Trade-off analysis

Every significant decision compares at least two real options. Include "extend what exists" as one option unless it is impossible.

Procedure:
1. List the decision drivers from the quality attributes and constraints.
2. Apply knockout criteria first: any option that violates a hard constraint or misses a must-have target is out, with the reason written.
3. For the survivors, compare on the same axes: implementation cost, operational complexity, risk, reversibility, fit with existing patterns, and the attributes that decide. Use evidence (measurements, documentation, a spike), not adjectives.
4. If you weight criteria, write the weights down and run a sensitivity check: would a different reasonable weighting change the winner? If yes, the decision is close, so prefer the more reversible option and say so.
5. Ask the reversibility question: if this is wrong, what does undoing it cost, and when would we know? A decision that is cheap to undo needs less analysis; a decision that is costly to undo needs an ADR.
6. Record the rejected options with concrete reasons. "Too complex" is not a reason; "needs a broker we cannot operate yet" is.
7. Write the revisit trigger: the measurable event that reopens the decision.

If two options score about the same, choose the simpler and the more reversible. If the choice depends on a product, cost or data-policy decision only the user can make, put it to the user as a numbered question with your recommendation.

### The simplicity pass

Before finalising, try to delete.

- Remove each component in turn: what breaks? If nothing, remove it.
- For each abstraction, name the variation or problem that exists today. If you cannot, remove it and note the foreseen extension in prose.
- For each technology, name the requirement it serves. If none, remove it. Adding or majorly upgrading a dependency needs user approval under the approval gates in `AGENTS.md`.
- For each asynchronous hop, name why a direct call is not enough.
- For each service boundary, name why a module boundary is not enough.

The design that remains is the one to record.

### Mapping the design into the docs

Write the design into its owning docs, not only the task file. For `docs/ARCHITECTURE.md`, map the method outputs to the template's headings. How to write the prose and diagrams: load `technical-documentation`.

| Method output | Heading in `docs/ARCHITECTURE.md` |
|---|---|
| System boundary, constraints | Context and boundaries |
| Quality attribute scenarios | Quality attributes |
| Components, responsibilities, data ownership | Components and responsibilities |
| Flows | Data and control flow |
| External dependencies and their failure contracts | External dependencies |
| Trust boundaries (flag only) | Security model and trust boundaries |
| Deployables, queues, topology | Deployment topology |
| Detection signals | Observability |
| Rejected options, open items, risks | Risks and trade-offs |
| ADR links | Related decisions |

Data model changes go to `docs/DB.md`, interface changes to `docs/API-CONTRACTS.md`, UX consequences to `docs/DESIGN.md`. Each doc describes what is decided now.

### Design review

Walk the design with the scenarios, not the diagram. For each quality attribute scenario, trace it through the components and confirm the measure can be met. Then try three attacks on the design: a dependency stops answering, load doubles in a minute, and the largest tenant or payload arrives. If the design cannot answer one of them, add a mechanism or mark the risk.

Finish by listing: open questions (numbered, with a recommended default), assumptions still unconfirmed, areas needing a security audit, and anything that needs user approval before work starts.

## Examples

### Filled-in quality attribute table (report export feature)

| Attribute | Scenario | Target | Status |
|---|---|---|---|
| Latency | A user requests a 10,000-row export | Download starts within 5 s | Assumption: row count; confirm with product |
| Availability | The file store is unavailable | Export request queued; user told to retry; no data lost | Fixed |
| Isolation | One tenant requests many exports | Others' interactive latency unchanged | **open**: target not agreed |
| Cost | Peak of 20 concurrent exports | Fits in current worker pool | Assumption |

### Filled-in failure-mode row

| Dependency | Failure modes | Timeout | Retry rule | Fallback | Blast radius | Detection |
|---|---|---|---|---|---|---|
| Payment provider | Slow, 5xx, duplicate webhook | 3 s connect plus request, from p99.9 of measured latency (assumption until measured) | Charge calls retried only with an idempotency key, 2 retries, backoff with jitter, at the payments module only | Order accepted as "payment pending", worker retries from a queue | Orders module unaffected; payments module bulkheaded in its own pool | Error rate and queue depth alerts |

### Bad to good: a boundary

Bad: "The Orders service calls the Inventory service, which calls Orders to confirm the customer's status."

Good: "Orders owns customer-order status and publishes `order placed` with the facts Inventory needs. Inventory never calls Orders. If Inventory needs Orders' data synchronously, merge the two or move the shared concept into its own component that both call downward."

### Bad to good: a rejection reason

Bad: "Rejected message broker: too complex."

Good: "Rejected message broker: it would add the first stateful infrastructure component to a team with no on-call process for it; a database-backed job table meets the 50 jobs per minute target (assumption: peak measured at 12 per minute last quarter). Revisit if sustained load passes 500 jobs per minute or a second consumer needs the same events."

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Drawing boxes before listing constraints and targets | The design fits nothing in particular | Frame first: constraints, assumptions, quality attributes with numbers |
| Quality attributes stated as adjectives | Cannot choose between options or test the result | Scenario plus measure, or mark **open** |
| Only the happy path traced | Failure behaviour is discovered in production | Trace the failure and the stress path; fill the failure-mode table |
| Two components writing the same data | Conflicting updates, no owner for correctness | One owner per datum; others read through the owner |
| Comparing one real option against two strawmen | The decision looks justified but is not | Include "extend what exists"; use evidence for every option |
| Weighted scores without a sensitivity check | A hidden weighting decides the outcome | Show that the winner survives a different reasonable weighting |
| Putting detail that belongs to another skill in the design | Duplicate, drifting contracts | Decide the character of the interface here; shape lives in the owning doc |
| Designing from documents without reading the code | Existing behaviour is misread; the top source of design defects | Read the code the change touches before choosing |
| Leaving the design only in the task file | The next task cannot find it | Record in the owning docs; ADR where costly to reverse |

## Checklist

- [ ] Constraints, assumptions and quality attributes are listed and each assumption is marked.
- [ ] Each important quality attribute has a scenario with a measure, or is marked **open**.
- [ ] The system boundary and component responsibilities are stated, and each datum has one owner.
- [ ] The dependency graph has no cycles.
- [ ] Every interface states direction, sync or async, and its failure contract.
- [ ] At least three flows (happy, failure, stress) are traced with state and consistency points marked.
- [ ] Every call, queue and external dependency has a failure-mode row with a timeout and retry rule.
- [ ] Every significant decision lists at least two options with evidence and concrete rejection reasons.
- [ ] A revisit trigger is written for each decision costly to reverse.
- [ ] The simplicity pass was done and removed anything without a stated need.
- [ ] The design is written into the owning docs under the right headings.
- [ ] Open questions are numbered, with a recommended default for each.

## Verify with context7 and gh_grep

- **context7:** before putting a number in a failure-mode table, check the default and configurable timeouts, pool sizes and retry behaviour of the HTTP client, database driver or SDK at the version in the project's lockfile (for example "request and connection timeout options in `<client>` `<version>`"). Check the broker's delivery and ordering guarantees at the pinned version. Do not copy a default into the design without confirming it.
- **gh_grep:** search literal code to see how real services express the policies you are designing: `timeout=`, `Retry-After`, `idempotency_key`, `dead_letter`, `CircuitBreaker`. Prefer repositories in the project's language that are actively maintained and read how they wire timeouts and retries at one layer.

## Sources

- Google, "Addressing Cascading Failures", Site Reliability Engineering (2017). https://sre.google/sre-book/addressing-cascading-failures/
- Amazon Builders' Library, "Timeouts, retries, and backoff with jitter" (2019). https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter
- Azure Architecture Center, "Architecture styles". https://learn.microsoft.com/azure/architecture/guide/architecture-styles
- Azure Architecture Center, "Circuit Breaker pattern". https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker
- Michael Nygard, "Documenting Architecture Decisions" (2011). https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
