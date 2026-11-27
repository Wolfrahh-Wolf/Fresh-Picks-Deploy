# Scalability and Resilience

How to estimate capacity and design for growth and failure at the architecture level: estimates, statelessness, partitioning, replication, queues, load balancing and resilience patterns (timeouts, retries, circuit breakers, bulkheads, load shedding). Language-neutral; checked on 2026-11-26 against the Google SRE book chapter "Addressing Cascading Failures" (2017 edition), the Amazon Builders' Library article "Timeouts, retries, and backoff with jitter" (2019), and the Azure Architecture Center pages for Circuit Breaker, Bulkhead and Queue-Based Load Leveling (pages dated 2025 and 2026). Library defaults change: confirm the project's pinned versions with context7.

## Contents

- Capacity estimates
- Finding the real limit: load tests
- Statelessness
- Scaling out, scaling up and autoscaling
- Partitioning
- Replication
- Queues and asynchronous work
- Load balancing and health checks
- Resilience: timeouts and deadlines
- Resilience: retries, backoff and jitter
- Resilience: circuit breakers, bulkheads, load shedding
- Choosing the mechanism

## Guidance

### Capacity estimates

An estimate is arithmetic with written inputs. Its purpose is to decide whether a design is in the right order of magnitude, not to predict the future to three digits. Always show inputs, formula and result, and label inputs you did not measure as assumptions.

Method:
1. **Demand:** users or clients, actions per user per day, so requests per day. Average rate is requests per day divided by 86,400 seconds.
2. **Peak:** multiply the average by a peak factor taken from real traffic shape (daily curve, campaigns, batch jobs). If unknown, state an assumed factor and mark it.
3. **Work per request:** CPU time, downstream calls, bytes in and out, rows touched. Measure one instance of one request type if you can.
4. **Concurrency:** by Little's law, requests in flight equals arrival rate times time in system. This sizes thread pools, connection pools and queues.
5. **Storage and growth:** events per day times size per event, times retention; add indexes and replicas as a multiplier; state growth per year.
6. **Capacity and headroom:** divide peak by the measured per-instance capacity at the latency target; round up; add redundancy. The SRE chapter's example: if each cluster breaks at 5,000 queries per second and peak is 19,000, 4 clusters carry the load and about 6 are needed to run at N+2.
7. **Cost:** multiply instances and storage by price only if cost is a stated attribute.

Do not estimate what you can measure cheaply. Do not claim a target is met from an estimate alone when the target is tight; schedule a load test.

### Finding the real limit: load tests

The SRE chapter ranks load testing the server's capacity limits, and its failure mode under overload, as the most important step in preventing overload. Predicting which resource runs out first is hard. In a design, require these checks and put them in the acceptance criteria:
- ramp load until the component breaks, and also apply an impulse load, because caches and pools behave differently;
- check that beyond the limit the component serves errors or degraded results while keeping its useful throughput, instead of collapsing;
- check recovery: does it leave degraded mode unaided, and how far must load fall for it to stabilise;
- test each component on its own, since you do not know which breaks first;
- test noncritical dependencies by making them unavailable and also by making them never answer.

Testing tools and plans belong to `testing-strategy`; the architect specifies what must be shown.

### Statelessness

A stateless request handler keeps no data between requests that another instance would need. Instances become interchangeable, so you can add, remove, restart and load balance them freely.

Rules:
- Keep session and user state in a shared store or in a signed client-held token. Which one is a security and consistency choice; for token and session implementation load `backend-engineering`.
- Do not write files that another instance must read to local disk; use shared object or file storage.
- Do not rely on in-process locks, counters or schedulers for correctness across instances. Use the datastore or a lock service, and make background jobs safe to run on two instances at once, or elect one.
- In-process caches are fine as an optimisation, not as the only copy of anything.
- Distinguish a latency cache from a capacity cache. With an empty cache, a latency cache means the service still meets its load, only slower; a capacity cache means it cannot. A service that quietly depends on a capacity cache fails after a restart or a new deployment. Treat each cache as either strictly optional or as a dependency with its own failure row. Cache design itself belongs to `backend-engineering`.
- Slow startup is part of state: first requests after a start may be slow because connections are not yet open or code is not warm. Establish connections before taking traffic, and add load to new instances gradually.

### Scaling out, scaling up and autoscaling

Scale up (bigger instance) is the cheapest first move and has a ceiling. Scale out (more instances) needs statelessness and a way to share load. Prefer scaling up until a measured limit or a redundancy need forces scaling out.

Autoscaling reacts to a metric (CPU, queue depth, requests per instance). Rules:
- Bound the maximum. The Azure load-leveling guidance warns that autoscaling without bounding the aggregate downstream rate only moves overload to downstream dependencies, such as a shared database.
- Account for lag: new instances take time to start and warm up. Autoscaling does not replace headroom for sudden bursts.
- Scale on the metric that reflects the bottleneck (queue depth for workers, in-flight requests for handlers), not a proxy.
- Test scale-in as well as scale-out; instances stopped mid-request must finish or hand off work.

### Partitioning

Partitioning (sharding) splits data or work so no single node must hold or process it all. It is expensive and permanent in practice; do it only when a measured limit of one node (storage, write throughput, memory) will be reached and cannot be pushed back by scaling up, indexing or caching.

Decisions to make and record:
- **Partition key:** choose from the dominant access pattern so that most requests touch one partition. Good keys are high in cardinality and evenly used; tenant or user identifier is common. Avoid keys that create a hot partition (a timestamp that always writes to the newest partition, a single very large tenant).
- **Strategy:** hash of the key spreads evenly but destroys range scans; range keeps order and risks hot ranges; a directory (lookup table) is flexible and becomes a dependency of its own.
- **Cross-partition operations:** queries and transactions that span partitions are slow or unavailable. List them; if one is on a critical path, the key is wrong or the feature needs another approach.
- **Resharding:** state how partitions are split or merged and what that costs; this is where schemes fail later.
- **Isolation use:** partitioning by tenant also isolates failure and load (the bulkhead idea). One partition per tenant versus several tenants per partition is a granularity decision with a cost in efficiency.

Mechanics, schema and platform features: load `database-engineering`.

### Replication

Replication copies data for availability and read scale.

- **Read replicas** scale reads but lag behind the writer. Anything that reads its own write needs a rule: read from the writer, pin a session to it for a short time, or accept stale reads. Decide per feature.
- **Failover** requires detection, promotion and client reconnection; state the expected time and what in-flight work is lost.
- **Synchronous versus asynchronous:** synchronous replication protects data at the cost of latency and availability; asynchronous is faster and can lose recent writes at failover. State the loss tolerance (how many seconds of data may be lost) as an attribute, or mark it **open**.
- **Multiple regions:** adds latency, conflict handling and cost. Require a named driver (regulation, regional users, regional failure tolerance).
- Replication does not replace backups: a replica copies an accidental deletion as faithfully as any other write.

Settings, consistency options and operational checks: load `database-engineering`.

### Queues and asynchronous work

A queue between a producer and a consumer smooths bursts, decouples availability and lets the consumer run at its own pace. The Azure Queue-Based Load Leveling guidance gives these cautions, all of which belong in a design:

- If the average producer rate exceeds the consumer rate, the queue grows without bound and latency grows with it. Monitor depth, scale consumers within safe limits, or shed work at the producer.
- Most queue services deliver at least once, so consumers receive duplicates. Make every consumer idempotent.
- Messages that can never succeed (malformed, referencing missing data) go to a dead-letter queue instead of cycling. Monitor the dead-letter depth and decide who investigates and how messages are resubmitted.
- A queue does not preserve global order when several consumers run in parallel. If order matters, say over which key and use the broker's feature for it; if it does not, design consumers to accept any order, which makes scaling easier.
- The queue must be durable if loss is not acceptable; know its size and retention limits.
- A queue is one-way. If the caller needs a result, the design needs a reply mechanism or a status the caller can poll.
- Competing consumers: several instances read the same queue, each message goes to one of them. They act as replicas, so one failing does not stop processing. Bound their combined rate against the downstream resource.

Do not use a queue when the caller needs a synchronous answer with low latency, or when volume is low and steady; the queue then only adds an operational component.

### Load balancing and health checks

- **Layer:** layer 4 balances connections cheaply; layer 7 can route on request content, terminate TLS and apply per-route policy. Pick the lower layer that satisfies the routing need.
- **Algorithm:** round robin is fine for uniform requests; least connections or least load helps when request cost varies. Sticky routing only when state forces it, and treat it as a cost, since it unbalances load and breaks on instance loss.
- **Two kinds of health check.** The SRE chapter distinguishes process health ("is the process responding at all") for the scheduler or orchestrator from service health ("can it serve this class of request now") for the load balancer. Conflating them can make a service that is merely busy get killed, which pushes more load on the rest. Keep them separate.
- **Graceful drain:** an instance leaving rotation stops taking new requests and finishes the ones in flight.
- **Avoid load balancing policies that eject instances for serving a few errors** without a floor on healthy capacity; a few erroring backends then shrink capacity and snowball.
- **Cold instances:** ramp traffic to a new instance slowly.

### Resilience: timeouts and deadlines

Every call across a process or network boundary has a timeout, including a connection timeout and a request timeout. Amazon's practice is to set a timeout on any remote call and generally on any call across processes, even on one machine.

Choosing the value:
- Start from the downstream service's measured latency. Pick an acceptable rate of false timeouts (for example 0.1 percent) and read the matching latency percentile (p99.9 in that example). That is a starting point.
- Adjust when clients are far away on the network, when p99.9 is close to the median (add padding), and when the timer includes work such as connection setup or a TLS handshake, which a new instance pays once.
- Too high a timeout holds resources (threads, memory, connections) while the caller waits and invites resource exhaustion. Too low increases retries and can turn a small latency increase into an outage.
- A deadline several orders of magnitude above the mean latency is usually wrong. The SRE chapter's bimodal example: if 5 percent of requests never complete and the deadline is 100 seconds against a 100 millisecond mean, those requests alone occupy more threads than exist, and most requests fail.
- Prefer the timeouts built into well-tested clients; if you write your own, know exactly what the timeout covers (name resolution, handshake, read).

Deadline propagation: set the deadline high in the stack and pass the remaining time down, so each hop uses what is left rather than a fixed value. A server should check remaining time before each stage and drop work whose caller has already given up. Propagate cancellation too, so doomed work stops. Fail fast when a dependency is known to be unavailable instead of waiting for the full deadline.

### Resilience: retries, backoff and jitter

Retries are "selfish": the client spends more of the server's capacity to raise its own odds. They help when failures are rare and transient and hurt when failures come from overload.

Rules:
- Retry only operations that are safe to repeat. Reads are usually idempotent; operations with side effects are safe only with an idempotency mechanism such as a client-supplied key. A timeout does not prove the side effect did not happen. Idempotency design for interfaces: load `api-engineering`.
- Retry only transient failures. Server-side errors may succeed later; client errors will not. Eventual consistency blurs this line, so decide per operation. Do not retry permanent or malformed requests. Return a clear overload signal so clients back off and do not retry.
- Use capped exponential backoff with jitter (randomisation). Without jitter, clients that failed together retry together and overload the dependency again. Jitter also helps timers, periodic jobs and scheduled work: spread them.
- Limit the number of attempts, and keep a local retry budget, for instance a token bucket that allows retries while tokens remain and then only a low fixed rate. The SRE chapter suggests a process-wide cap such as a number of retries per minute, after which requests fail without retrying.
- Retry at one layer. Attempts multiply across layers: with 3 retries (4 attempts) at each of three layers, one user action produces 4 x 4 x 4 = 64 attempts against the database. Decide which layer owns retries and have the others fail fast.
- Retries must stay within the caller's deadline; stop when the remaining time is too short.

### Resilience: circuit breakers, bulkheads, load shedding

**Circuit breaker.** A proxy in front of a remote call with three states. Closed: calls pass and recent failures are counted over a time window. Open: calls fail immediately for a timeout period. Half-open: a limited number of trial calls pass; success closes the circuit, failure reopens it. Use it to stop calling a dependency that is likely to fail and to give it room to recover. It is not a substitute for handling errors in business logic. Decide what the open state returns: an error, a cached value or a default.

Cautions: Azure lists unsuitable cases, including a message-driven design where dead-letter queues and retries already isolate failure, and cases where the platform (a service mesh or global load balancer) already handles failure recovery, so do not configure it twice. Amazon notes that breakers introduce modal behaviour that is difficult to test and can add time to recovery, and prefers a local retry budget where that suffices. Use one breaker per independent resource (for example per shard or per downstream), not one for a pool of different providers. Emit an event on each state change and alert on open. Provide a manual override when recovery time varies a lot. Long external timeouts defeat a breaker, since threads block before it notices.

**Bulkhead.** Isolate resources into pools so that one failing element cannot starve the rest. A consumer can give each downstream its own connection pool or concurrency limit; a service can give different consumers or tenants separate instances or queues; containers give isolation at low overhead. Choose the granularity (one tenant per partition or several), monitor each partition and combine bulkheads with retry, circuit breaker and throttling. Prefer platform controls (rate limits, resource limits) over re-creating them in code. The trade-off is less efficient resource use.

**Load shedding and graceful degradation.** When load exceeds capacity, something must give; it is better to serve some errors or lower-quality results than to try to serve everything and collapse. Shed early and cheaply: for example return a service-unavailable response when too many requests are in flight, drop low-priority work first, and discard requests that have waited so long the caller has likely given up. Degrade by doing less work (serve cached or approximate results, skip optional features). Keep queues short relative to worker pools for steady traffic so rejection is early. Graceful degradation is a rarely used code path: exercise it regularly, alert when it activates, keep it simple, and give operators a quick way to turn it off.

### Choosing the mechanism

| Symptom or risk | First mechanism | Add when |
|---|---|---|
| Caller threads blocked on a slow dependency | Timeout and deadline propagation | Dependency fails for long periods: circuit breaker |
| Transient errors on safe calls | Bounded retry with backoff and jitter at one layer | Failures correlate: retry budget |
| One dependency exhausts shared pool | Bulkhead (separate pool or concurrency limit) | Tenants differ in load: per-tenant partitions |
| Bursts overload a downstream store | Queue with bounded consumers | Peak exceeds average for long: shed at producer |
| Overload despite the above | Load shedding, reject early | Optional features: degraded mode |
| Consumers see duplicates | Idempotent consumer | Poison messages: dead-letter queue |

## Examples

### Filled-in capacity estimate (all inputs are assumptions until measured)

| Step | Input or formula | Result |
|---|---|---|
| Daily active users | 200,000 | |
| Requests per user per day | 20 | 4,000,000 requests per day |
| Average rate | 4,000,000 / 86,400 | about 46 per second |
| Peak factor | 5 (assumed; check real traffic shape) | about 230 per second |
| Per-instance capacity | 80 per second at p95 under 300 ms (measured in a test) | |
| Instances for peak | 230 / 80 = 2.9, round up | 3 |
| Redundancy | N+1 | 4 |
| Concurrency | 230 per second x 0.2 s average time in system | about 46 requests in flight |
| Storage growth | 4,000,000 events per day x 1 KB | about 4 GB per day, about 1.46 TB per year before indexes and replicas |

State what would change the answer most: the peak factor and per-instance capacity.

### Bad to good: retries at every layer

Bad: browser, API, service and database client each retry 3 times. A database brown-out multiplies each user action into 64 attempts and keeps the database down.

Good: only the service layer retries, bounded to 2 retries with jittered backoff and a retry budget; the browser and API fail fast and show a retry-later message; the database client does not retry; the overload response tells callers not to retry.

### Retry with a deadline (Python 3.11)

```python
import random
import time


def call_with_retry(operation, *, attempts=3, base=0.1, cap=2.0, deadline=5.0):
    """Retry a safe-to-repeat operation within an overall deadline.

    `operation(timeout=...)` must raise TimeoutError for a transient failure.
    Use only for reads or for writes protected by an idempotency key.
    """
    start = time.monotonic()
    for attempt in range(attempts):
        remaining = deadline - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError("deadline exhausted")
        try:
            return operation(timeout=remaining)
        except TimeoutError:
            if attempt == attempts - 1:
                raise
            pause = random.uniform(0, min(cap, base * 2 ** attempt))
            if time.monotonic() - start + pause >= deadline:
                raise
            time.sleep(pause)
```

The pause is random between zero and a capped exponential bound (jitter), attempts are bounded, and the whole call respects one deadline. A production version also needs a retry budget shared across calls.

### Filled-in queue design note

Producer: web handler writes an export job to a durable queue and returns "accepted". Consumers: 4 worker instances, concurrency 2 each, so at most 8 jobs run at once (bounds the file store and database load). Queue: bounded at 5,000 jobs; when full the handler returns a retry-later response (shed at the producer). Duplicates: job identifier is the idempotency key; a finished job is skipped. Poison jobs: after 3 attempts move to the dead-letter queue; an alert fires at depth 1. Ordering: none required. Scale rule: add workers when oldest-message age exceeds 60 seconds, maximum 8 workers (bounded by database connection limit).

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| No timeout, or a very large one | Threads and connections pile up behind one slow dependency | A timeout on every remote call, chosen from measured latency |
| Retrying everything, at every layer, without jitter | Multiplies load during overload; synchronised retry waves | One layer, bounded, jittered, budgeted, idempotent operations only |
| Unbounded queue | Latency grows without limit; memory exhaustion | Bound it; shed at the producer; alert on depth and age |
| Autoscaling with no maximum | Moves the overload to the database or a third party | Bound the aggregate downstream rate |
| Treating a cache as an optimisation when it carries the load | A restart or new cluster with an empty cache fails | Overprovision, warm gradually, or give it a failure row |
| Using one health check for process and service health | Busy instances are killed and load snowballs | Separate checks for the scheduler and the load balancer |
| Sharding early | Permanent complexity for a limit not yet reached | Scale up, index and cache first; shard on a measured limit |
| Reading from a replica right after a write | Users see their own change missing | Decide read-your-write behaviour per feature |
| A circuit breaker shared across unrelated providers | One bad provider blocks good ones | One breaker per independent resource |
| Capacity claims with no inputs shown | Cannot be checked or updated | Show inputs, formula and result; label assumptions |

## Checklist

- [ ] Every capacity claim shows its inputs, formula and result, and labels unmeasured inputs as assumptions.
- [ ] A load test that finds the breaking point and the overload behaviour is in the acceptance criteria.
- [ ] Request handlers keep no state another instance needs.
- [ ] Every cache is classed as latency or capacity, and a capacity cache has a failure row.
- [ ] Autoscaling has a maximum that protects downstream dependencies.
- [ ] Any partition key is justified by the dominant access pattern, and cross-partition operations are listed.
- [ ] Read-after-write behaviour is stated for every read path that may use a replica.
- [ ] Every queue is bounded, durable where loss matters, has idempotent consumers and a dead-letter path.
- [ ] Every remote call has a connection timeout and a request timeout with a stated source for the value.
- [ ] Retries are bounded, jittered, limited to safe operations and performed at one layer.
- [ ] Each dependency has a stated behaviour when it is open-circuited, slow or down.
- [ ] Overload behaviour is stated: what is rejected, what is degraded, how operators see it.

## Verify with context7 and gh_grep

- **context7:** confirm the defaults and options of the project's own libraries at the pinned version before writing a number: HTTP client connect and read timeouts, database driver pool size and acquire timeout, message broker acknowledgement, redelivery and dead-letter settings, and the resilience library in use (for example "circuit breaker and bulkhead configuration in `<library>` `<version>`"). Ask the hosting platform's documentation whether it already retries or breaks circuits (service mesh, gateway, serverless trigger), so they are not applied twice.
- **gh_grep:** search literal code to see real usage: `CircuitBreaker`, `maxRetries`, `jitter`, `Retry-After`, `x-dead-letter-exchange`, `idempotency_key`, `semaphore` or `Bulkhead`. Read how two or three maintained repositories bound retries and where they place timeouts.

## Sources

- Google, "Addressing Cascading Failures", Site Reliability Engineering (2017). https://sre.google/sre-book/addressing-cascading-failures/
- Amazon Builders' Library, "Timeouts, retries, and backoff with jitter" (2019). https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter
- Azure Architecture Center, "Circuit Breaker pattern". https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker
- Azure Architecture Center, "Bulkhead pattern". https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
- Azure Architecture Center, "Queue-Based Load Leveling pattern". https://learn.microsoft.com/azure/architecture/patterns/queue-based-load-leveling
