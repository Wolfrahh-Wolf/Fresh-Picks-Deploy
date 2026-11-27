# Architecture Patterns

How to choose, apply and evolve a system's structural style: layered, modular monolith, hexagonal (ports and adapters), event-driven and microservices. Language-neutral; checked on 2026-11-26 against the Azure Architecture Center "Architecture styles" guide (page updated 2026-11-04), Martin Fowler's "Monolith First" (2015), Alistair Cockburn's "Hexagonal architecture" (2005) and the Azure Strangler Fig pattern. The project's own `docs/ARCHITECTURE.md` and manifest win over anything here.

## Contents

- Choosing a style from the forces
- Layered
- Modular monolith
- Hexagonal (ports and adapters)
- Event-driven
- Microservices
- Combining styles
- Evolving: extraction and strangling
- Detecting boundary erosion

## Guidance

### Choosing a style from the forces

A style is a set of constraints on which elements may exist and how they may depend on each other. Pick it for the properties its constraints produce, not for fashion. Focus on why the style is chosen before how it is built; relax a constraint rather than chase purity when the constraint buys nothing here.

Start from the forces, then read down the table. Each row is a driver you can measure or ask about.

| Force | Pushes toward | Pushes away from |
|---|---|---|
| One team, product still being discovered, boundaries unclear | Modular monolith or layered | Microservices |
| Several teams blocked by a shared release train | Separate deployables along stable boundaries | Single deployable without module rules |
| One part needs far more capacity, or a different scaling profile, than the rest | Extract that part; queue in front of it | Scaling the whole system uniformly |
| One part must stay up when another fails | Bulkheads, async decoupling, separate deployables | Shared in-process fate |
| Several subsystems must react to the same fact | Event-driven (publish and subscribe) | Point-to-point calls from the producer |
| Business logic must run from several entry points (web, CLI, queue, tests) or survive swapped infrastructure | Hexagonal inside the deployable | Logic in controllers or handlers |
| Simple CRUD with little logic | Layered | Ports, events, services |
| Operations maturity is low (no automated deploy, no central logs or traces) | Fewer deployables | Microservices, event-driven |

Defaults, in order: layered for small CRUD; modular monolith for most new products; hexagonal as an internal structure when logic is rich or entry points are many. Fowler's observation is that almost all successful microservice systems began as a monolith that grew too big, and that systems built as microservices from scratch often ended in serious trouble. Boundaries are hard to place before the domain is understood, and moving functionality between services is far harder than between modules. Treat microservices as an evolution with a named trigger, not a starting point.

Every style choice that is costly to reverse gets an ADR. Load [adr.md](adr.md).

### Layered

Layers divide responsibilities (presentation, business logic, data access) and each layer may call only the layer beneath it.

Fits when: the application is small to medium, mostly CRUD, owned by one team, or already layered and being migrated. The Azure guide notes it needs few changes when moving existing layered applications.

Fails when: the domain grows. Horizontal layering makes a feature touch every layer, which slows frequent change. Cockburn's critique is that the lines in a layer diagram are not taken seriously, so business logic leaks into the presentation layer and the organisation adds a new layer "that really will have no business logic", which leaks again because nothing detects the violation.

Rules:
- Dependencies point down only. State whether layer skipping is allowed; the default is that it is not.
- Business rules live in the business layer. Controllers translate requests and responses and nothing else.
- Persistence types do not appear in interface shapes or in the presentation layer.
- A rule nobody checks will erode. Add an automated check or an acceptance criterion that searches for the forbidden import (see Detecting boundary erosion).

Evolve to: modular monolith (cut the layers vertically by business capability inside each) or hexagonal (invert the data-access dependency).

### Modular monolith

One deployable unit, divided into modules by business capability. Each module has a public interface, owns its data, and is reachable by other modules only through that interface.

Fits when: most new products; one to a few teams; boundaries still settling; you want fast cycle time and one deployment, with an option to extract later. Fowler is explicit that a monolith-first route only works if the monolith is designed carefully for modularity, at the interface boundaries and in how data is stored; an arbitrary tangled system cannot be sensibly broken apart.

Fails when: boundaries exist on paper but not in code. Modules import each other's internals, share tables freely, and the first extraction becomes a rewrite.

Rules:
- One module per business capability (ordering, billing, catalogue), not per technical layer.
- A module exposes one public surface (a facade, a package export list or an interface file). Everything else is private to it.
- No module reads or writes another module's tables or internal types. For data that other modules need, expose a query on the public surface or publish an in-process event. Schema decisions: load `database-engineering`.
- Cross-module calls form a directed graph with no cycles. A cycle means two modules are really one, or a third concept is missing.
- Enforce with a check in the build, not in a wiki page.
- A module may itself be structured as a hexagon (next section).

Extraction readiness (all must be true before a module becomes a service): it has its own data and no foreign reads; its public surface is stable; a measured trigger exists (deploy conflicts, scaling cost, isolation incident, team ownership); a team will own it; the platform can deploy, observe and roll back a service independently.

### Hexagonal (ports and adapters)

The application core sits inside; it talks to the outside only through ports. A port is a purposeful conversation, expressed as an interface in the core's vocabulary. An adapter translates between a port and one concrete technology. Driving (primary) adapters, such as a web handler, a command-line entry or a test harness, call the core. Driven (secondary) adapters, such as a database gateway or a payment client, are called by it.

Fits when: the logic is rich; several entry points need the same behaviour; infrastructure is likely to change; you want to run the core in tests without a database, a network or a user interface. Cockburn's intent is that the application can be driven equally by users, programs, automated tests or batch scripts and developed in isolation from run-time devices and databases.

Fails when: the application is a thin pass-through. Ports add indirection with no logic to protect. Also when ports are named by technology (a port called after one database product) instead of by purpose, which keeps the coupling and adds code.

Rules:
- The core imports nothing from adapters or frameworks. Dependencies point inward.
- Name a port for the purpose of the conversation, in domain terms ("rate source", "payment gateway"), not for the technology.
- Prefer few ports. Cockburn finds two to four typical, and says the exact number is a matter of judgement; one port per use case or one port for everything are the poor extremes.
- Provide an in-memory adapter for each driven port; it is the cheapest test double and proves the port is clean.
- Write use cases against the core's interface, not against a technology behind a port.
- Hexagonal is an internal structure and combines with every other style here. It is not a deployment decision.

### Event-driven

Producers publish events; consumers react. Producers and consumers are decoupled through a channel or broker. The Azure guide lists real-time processing, high-volume ingest and several subsystems reacting to the same fact as natural fits, and lists guaranteed delivery, ordering and eventual consistency as the challenges.

Fits when: several subsystems each need an independent reaction to the same fact; work can be done after the request returns; load is bursty and a buffer protects a downstream dependency; failures in a consumer must not fail the producer.

Fails when: the caller needs an answer now (this is request and response in disguise); the business flow becomes impossible to follow because control is hidden in subscriptions; consumers cannot tolerate duplicates or reordering; nobody owns the event contracts.

Rules:
- State which kind of event you mean. A notification says something happened and consumers fetch details. State transfer carries the data consumers need. Event sourcing stores events as the system of record; it is a separate, heavy decision and needs its own ADR.
- Name events as past-tense facts about the business ("order placed"), not commands.
- Assume at-least-once delivery. Every consumer is idempotent, and has a dead-letter path for messages it cannot process. Check the broker's real guarantees and ordering scope with context7 for the version in use.
- Order matters only within a key you choose; do not rely on global order. Where order is required, say how it is preserved.
- Carry a correlation identifier on every event and log it, so a flow can be traced end to end.
- Version event schemas and keep consumers tolerant of unknown fields. For the shape of the event contract, load `api-engineering`.
- Keep a bounded queue and an overload behaviour (see [scalability.md](scalability.md)).
- The simple form of this style is web, queue, worker: a front end, a queue and a back-end worker for long or heavy tasks. Use it before a full event mesh when the domain is simple and only some work is heavy.

### Microservices

Small autonomous services, each implementing one business capability within a bounded context, owning its own data, independently deployable and scalable. The Azure guide places them in complicated domains with frequent updates and says success needs mature development and DevOps practices; the costs include service discovery, data consistency, inter-service latency and distributed operations. Fowler calls this the microservice premium: extra cost and risk that only pays back in systems complex enough to need it.

Fits when, all of these:
- at least two teams need to release independently and are blocked by a shared deployable;
- components have sharply different scaling or fault-isolation needs that a bulkhead inside one process cannot give;
- boundaries are stable, because they were learned from a running system;
- the organisation can deploy, observe, trace and roll back each service on its own.

Fails when: it becomes a distributed monolith (services deploy together, share a database, call each other in long synchronous chains) or when boundaries are wrong, so one feature changes four services.

Prerequisites checklist (a no on any is a reason to stay with a modular monolith):
- automated build, test and deploy per service;
- central logs, metrics and distributed traces with a correlation identifier;
- health checks that distinguish "process is up" from "can serve this class of request";
- a named owner per service and per data store;
- a stated timeout, retry and degradation rule for every inter-service call.

Rules:
- A service owns its data; no other service reads its tables. Share data through the service's interface or events.
- Keep synchronous call chains short; each added hop multiplies latency and failure probability. Treat depth greater than two on a user request path as something to justify.
- Calls go downward in the dependency graph. Cycles and sibling-to-sibling proxying in the request path create deadlocks and load feedback loops.
- Every call carries a timeout and follows the retry rule in [scalability.md](scalability.md).
- Start with a few coarse services if you must split early; break them down as boundaries stabilise.

### Combining styles

Real systems mix styles at different scales. A common, healthy shape: a modular monolith whose modules are hexagons, with a queue and a worker for slow tasks, and one or two extracted services where a measured driver exists. Declare the style at each level so readers know which rules apply: system level (deployables and queues), module level (public surfaces and ownership), component level (ports and adapters).

### Evolving: extraction and strangling

To replace or extract a part of a running system, put a façade in front of it that routes each request either to the old part or to the new one, then move functionality across in steps. The Azure Strangler Fig guidance adds three cautions: build new parts so they can themselves be intercepted later; keep the façade in step with the migration; make sure the façade does not become a single point of failure or a bottleneck. When migration ends, remove the façade or keep it as an adapter for legacy clients.

For a data store, the same idea applies: move one domain's data at a time, and validate the new store before retiring the old. The data steps belong to `database-engineering`; the routing and sequencing belong here.

Each step must be independently releasable and reversible. State the rollback for every step in the plan.

### Detecting boundary erosion

Boundaries that are not checked decay. Use the cheapest check that works for the stack:
- a search for forbidden imports (for example, any import of a module's internal path from outside the module);
- the project's dependency-rule checker or architecture test if one exists (Java projects sometimes use ArchUnit-style tests, as the MADR template itself suggests for confirming a decision);
- a review question on every change: does it add an edge to the dependency graph?

Put the check in the build and in the task's acceptance criteria, so it fails loudly.

## Examples

### Filled-in style decision (summary form)

Context: six engineers, one team, new order-intake product, requirements still changing weekly, no automated per-service deploy yet. Targets: p95 intake latency under 400 ms at 50 requests per second (open: peak not yet measured).

| Option | Cost | Operational complexity | Risk | Reversibility | Fit |
|---|---|---|---|---|---|
| A. Extend existing layered app | Low | Low | Logic keeps leaking into controllers | High | Matches current code |
| B. Modular monolith, 4 modules, hexagonal core in ordering | Medium (module rules, one check) | Low | Boundaries could erode if unchecked | High; extraction possible later | Matches team size and uncertainty |
| C. Four microservices from day one | High | High (deploy, tracing, contracts) | Wrong boundaries are costly | Low | Prerequisites missing |

Decision: B. Revisit when one of these is true: two teams are blocked on the same release more than twice a month, or one module needs a different scaling profile that a queue cannot absorb. Rejected C: the prerequisites checklist fails on automated deploy and tracing.

### Module layout with an enforced surface

```text
src/
  ordering/
    public        # the only thing other modules may import
    internal/     # private to ordering
      domain/     # core: no framework or database imports
      ports/      # purpose-named interfaces
      adapters/   # database, payment client, message publisher
  billing/
    public
    internal/
  catalogue/
    public
    internal/
```

Acceptance criterion (observable): searching `src/` for imports of `*/internal/*` from outside the owning module returns no results; the build fails if it does.

### Bad to good: hidden coupling through events

Bad: an "order placed" event contains a database row id and the billing module reads the ordering tables to find the rest.

Good: the event carries the facts billing needs (order identifier, amount, currency, customer reference) and a correlation identifier; billing never reads ordering's data store; the consumer ignores unknown fields and is idempotent on the order identifier.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Starting with microservices for a small team and unsettled domain | Pays the full distributed-systems premium before boundaries are known; wrong splits are expensive to move | Modular monolith with an ADR naming the extraction trigger |
| Modules that share tables or import each other's internals | The first extraction becomes a rewrite; hidden coupling | Public surface per module, owned data, an automated boundary check |
| Distributed monolith: services deployed together, sharing a database | All the cost of distribution, none of the independence | Merge them, or give each real data ownership and a separate release |
| Ports named after technologies, or one port per method | Coupling kept, code added | Name ports by purpose; two to four ports is typical |
| Events used as disguised synchronous calls | Hidden control flow, timeouts without owners, no way to answer the caller | Use a direct call, or accept an asynchronous result |
| Assuming exactly-once delivery or global order | Duplicate charges, out-of-order updates | Idempotent consumers; order within a chosen key only |
| New layer added to "stop leaks" with no check | The same leak returns in a few years | Automate the dependency rule |
| Façade left as a single point of failure during migration | The migration creates the outage | Scale and monitor the façade; plan its removal |
| Declaring a style without saying at which level it applies | Readers apply the wrong rules | State system, module and component level separately |

## Checklist

- [ ] The chosen style is justified by named forces, not by preference.
- [ ] At least two styles or structures were compared, including "extend what exists".
- [ ] If microservices are proposed, every prerequisite is answered yes with evidence, and the trigger that forces the split is written down.
- [ ] Every module or service has one responsibility, one owner of its data and a public interface.
- [ ] The dependency graph has no cycles and flows one way.
- [ ] Ports (if any) are named by purpose and the core imports nothing from adapters.
- [ ] Event consumers are idempotent and have a dead-letter path.
- [ ] An automated check or acceptance criterion detects boundary violations.
- [ ] Each migration step is independently releasable and has a rollback.
- [ ] An ADR exists for the style decision and states its revisit trigger.

## Verify with context7 and gh_grep

- **context7:** for the framework in the project manifest, ask how it expresses module or package boundaries and dependency injection at that version (for example "module boundaries and providers in `<framework>` `<version>`"). For the message broker or queue service in use, ask for its delivery guarantee, ordering scope and dead-letter support at the pinned version. For any service mesh or gateway named in a design, ask whether it provides retries or circuit breaking so they are not configured twice.
- **gh_grep:** search literal code to see how maintained projects enforce boundaries and structure adapters: `class .*Adapter implements`, `x-dead-letter-exchange`, `dead_letter`, `idempotency_key`, `internal/` import restrictions in lint configuration. Compare two or three active repositories in the project's language before recommending a layout.

## Sources

- Azure Architecture Center, "Architecture styles". https://learn.microsoft.com/azure/architecture/guide/architecture-styles
- Martin Fowler, "Monolith First" (3 June 2015). https://www.martinfowler.com/bliki/MonolithFirst.html
- Alistair Cockburn, "Hexagonal architecture" (2005); text read through a third-party mirror because the original site could not be fetched: https://gist.github.com/timabell/4f6b6d222b7742f4784b3b306a0cfd43 (canonical home: alistair.cockburn.us, not fetched)
- Azure Architecture Center, "Strangler Fig pattern". https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
- Azure Architecture Center, "Queue-Based Load Leveling pattern" (for the web, queue, worker style). https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling
- MADR template and examples (for architecture tests as a decision confirmation). https://adr.github.io/madr
