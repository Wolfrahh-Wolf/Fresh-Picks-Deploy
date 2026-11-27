# Backend Performance

Covers profiling, concurrency, connection pooling, N+1 query detection, backpressure and load testing for backend services; patterns current as of 2026-11-26.

## Contents

- Profiling workflow
- Concurrency and the event loop
- Connection pooling
- N+1 query detection and prevention
- Backpressure
- Load testing

## Guidance

### Profiling workflow

Profile before optimising. Never guess at bottlenecks.

1. **Measure the symptom.** Record the specific metric that is slow or high: p99 latency, error rate, CPU%, memory, DB query duration, event loop lag. Use the monitoring stack that is already in place (Prometheus, Datadog, CloudWatch, etc.).
2. **Reproduce in a controlled environment.** Isolate the service and replay realistic traffic or the failing request to the staging environment. Never profile against production user data.
3. **Profile with the right tool for the runtime:**

| Runtime | Profiler | Output |
|---|---|---|
| Node.js | `--prof` + `--prof-process`, or `clinic.js doctor` / `clinic.js flame` | Tick-based CPU profile; flame graph |
| Node.js (async) | `clinic.js bubbleprof` | Async bubble chart; event loop idle vs. busy |
| Python (synchronous) | `cProfile`, `py-spy`, `scalene` | Call tree; line-level CPU/memory |
| Python (async) | `aiomonitor`, `pyinstrument` | Coroutine-level timing |
| General | Log `start = Date.now()` / `time.perf_counter()` before and after specific operations | Manual span timing |

4. **Find the dominant cost.** The largest self-time or the most-called function is the first candidate. Cross-check with database slow query logs and external call durations.
5. **Fix one thing.** Change one variable, re-run the benchmark, compare. Discard if no improvement.
6. **Verify the fix did not regress other metrics.** A change that halves query time but doubles CPU is not necessarily better overall.

### Concurrency and the event loop

Node.js is single-threaded for JavaScript. CPU-bound work on the main thread blocks all concurrent requests.

| Task type | Node.js | Python (FastAPI async) |
|---|---|---|
| Async I/O (DB, HTTP, file) | `await`; non-blocking by default | `await` with async libraries |
| CPU-bound (crypto, compression, parsing) | `worker_threads.Worker` | `asyncio.run_in_executor` with `ProcessPoolExecutor` |
| Synchronous, short (< 2 ms) | Acceptable on main thread | Acceptable in `async def` |
| Synchronous, long (> 2 ms) | Move to worker thread | Use plain `def`; FastAPI dispatches it to a threadpool |

**Node.js event loop lag** is the key concurrency metric. Measure it continuously:

```js
import { monitorEventLoopDelay } from 'node:perf_hooks';
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();
setInterval(() => {
  const ms = h.mean / 1e6;
  if (ms > 50) logger.warn({ lagMs: ms }, 'event loop lag');
  h.reset();
}, 10_000).unref();
```

For Python async services, avoid `time.sleep`, `requests.get` or any blocking call inside `async def`. Use `asyncio.sleep`, `httpx.AsyncClient` or similar.

### Connection pooling

**Always use a connection pool** for database, Redis and HTTP client connections. Opening a new connection per request is expensive (TCP handshake, TLS negotiation, DB authentication).

| Resource | Node.js | Python |
|---|---|---|
| PostgreSQL | `pg` pool, `knex`, or `Prisma` (built-in pool) | `asyncpg` pool, SQLAlchemy `AsyncEngine` with `pool_size` |
| MySQL | `mysql2` pool | `aiomysql` pool, SQLAlchemy pool |
| Redis | `ioredis` (single client multiplexes) | `aioredis` or `redis-py` with connection pool |
| Outbound HTTP | Node.js built-in `fetch` reuses keep-alive connections by default; use `undici` `Pool` for explicit pooling | `httpx.AsyncClient` (keep-alive); reuse a single client instance per service startup |

Pool sizing formula (starting point; tune with load tests):

```
pool_size = target_RPS × average_query_time_s × 1.5
```

Do not set pool size higher than the database's `max_connections` minus slots reserved for migrations, monitoring and admin.

Symptoms of pool exhaustion:
- Requests queue at the application tier (high latency spike)
- DB shows many `idle` connections but new connections are refused
- Pool timeout errors in logs

```js
// pg pool with explicit pool size and timeout
import { Pool } from 'pg';
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,              // max connections
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 2_000,
});
```

### N+1 query detection and prevention

An N+1 query occurs when code issues one query to fetch a list of N items, then issues N additional queries to fetch related data for each item.

**Detect:**
- Enable slow query logging in the DB (threshold: > 100 ms).
- Use `EXPLAIN ANALYZE` for queries suspected of N+1.
- In Python with SQLAlchemy, enable `echo=True` during development to log all queries.
- In Node.js with Prisma, enable the `query` log level in development.

**Fix with eager loading:**

```python
# SQLAlchemy: N+1 without fix
users = session.execute(select(User)).scalars().all()
for u in users:
    _ = u.posts  # N additional queries

# SQLAlchemy: fix with joinedload or selectinload
from sqlalchemy.orm import selectinload
users = session.execute(
    select(User).options(selectinload(User.posts))
).scalars().all()
# 2 queries total regardless of N
```

```js
// Prisma: N+1 without fix
const users = await prisma.user.findMany();
for (const u of users) {
  const posts = await prisma.post.findMany({ where: { authorId: u.id } }); // N queries
}

// Prisma: fix with include
const users = await prisma.user.findMany({ include: { posts: true } }); // 1 query
```

For deeply nested relations, prefer `selectinload` (SQL IN clause) over `joinedload` (SQL JOIN) in SQLAlchemy when the related collection is large; a JOIN multiplies rows.

### Backpressure

Backpressure prevents unbounded load from overwhelming the service. Apply it at every boundary:

**HTTP tier:**
- Set a maximum request body size on the parser.
- Return 429 when a rate limit is exceeded. Include `Retry-After`.
- Return 503 when the service is at capacity (health check fails; orchestrator stops routing traffic).

**Queue / stream consumer tier:**
- Process messages at a fixed concurrency; do not spin up unlimited parallel handlers.
- Acknowledge only after successful processing; allow dead-letter after N failures.

**Node.js streams:**
- Check the return value of `writable.write()`; pause the readable on `false`; resume on `drain`. Use `stream.pipeline()` for automatic backpressure.

**Outbound HTTP:**
- Cap concurrent outbound requests with a semaphore or connection pool size.

```js
// Semaphore for concurrent outbound requests
class Semaphore {
  constructor(max) { this.max = max; this.count = 0; this.queue = []; }
  acquire() {
    return new Promise(resolve => {
      if (this.count < this.max) { this.count++; resolve(); }
      else this.queue.push(resolve);
    });
  }
  release() {
    this.count--;
    if (this.queue.length) { this.count++; this.queue.shift()(); }
  }
}
const sem = new Semaphore(10); // max 10 concurrent outbound calls
```

### Load testing

Load test before every significant release that touches throughput-sensitive paths.

**Recommended tools:**

| Tool | Good for |
|---|---|
| `k6` | Scripted scenarios in JavaScript; HTTP and gRPC; CI integration |
| `autocannon` | Quick Node.js HTTP benchmarks from the terminal |
| `locust` | Python-defined user scenarios; real browser simulation |

**Minimum test cases:**

1. **Baseline:** single user, sustained. Establishes latency at zero contention.
2. **Ramp:** gradually increase virtual users to target RPS; find the knee in the latency curve.
3. **Sustained peak:** hold target RPS for 10–30 minutes; find memory leaks and gradual degradation.
4. **Spike:** instantaneous jump to 2× target; test autoscaling and queue behaviour.

Acceptance criteria to define before the test (example):

```
p50 latency ≤ 50 ms, p99 ≤ 300 ms, error rate ≤ 0.1%, at 1000 RPS sustained for 10 minutes.
```

Never load-test against a production environment with real user traffic. Use a staging environment with production-shaped data (anonymised).

## Examples

### k6 baseline test

```js
// k6 script: baseline.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 50, duration: '3m',
  thresholds: { http_req_duration: ['p(99)<300'], http_req_failed: ['rate<0.01'] },
};

export default function () {
  const res = http.get('http://staging-api.internal/api/v1/health');
  check(res, { 'status 200': r => r.status === 200 });
}
```

### autocannon quick benchmark

```bash
# 10 seconds, 100 connections, 10 pipelining
npx autocannon -c 100 -p 10 -d 10 http://localhost:3000/api/v1/users
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Opening a new DB connection per request | TCP/TLS handshake adds 50–200 ms per request | Use a connection pool sized for target concurrency |
| Running CPU-bound work on the Node.js main thread | Event loop lag; all concurrent requests stall | Offload to `worker_threads` |
| Load testing against production | Affects real users; contaminates metrics | Use a dedicated staging environment |
| Fixing N+1 with a cache instead of eager loading | Cache adds complexity and eventual-consistency; the query still runs on cache miss | Fix the query first; cache only if profiling shows it still matters |
| Setting pool size without measuring DB `max_connections` | Pool exhausts DB connections; causes cascading failures | Check DB settings; size pool to `max_connections × 0.8 / num_app_instances` |
| Profiling without a reproducible baseline | Cannot tell if a change improved or regressed | Establish a reproducible benchmark before any optimisation |

## Checklist

- [ ] A profiler was used to identify the dominant cost before any optimisation.
- [ ] No CPU-bound work runs on the Node.js main thread or inside a Python `async def`.
- [ ] All DB, Redis and outbound HTTP clients use a connection pool with an explicit size.
- [ ] N+1 queries detected via query logging and fixed with eager loading.
- [ ] Backpressure is applied: request body size limits, rate limits and capacity-based 503s.
- [ ] Load test run against staging with acceptance criteria defined before the test.
- [ ] Event loop lag (Node.js) or async queue depth (Python) monitored in production.

## Verify with context7 and gh_grep

- **context7:** Resolve `pg`, `prisma`, `sqlalchemy`, `ioredis`, `httpx`, `k6` at their locked versions. Check: `pg.Pool` options (`max`, `idleTimeoutMillis`, `connectionTimeoutMillis`); SQLAlchemy `selectinload` vs. `joinedload` semantics; Prisma `include` and `select` for eager loading; `monitorEventLoopDelay` resolution option; `k6` threshold syntax.
- **gh_grep:** Search `monitorEventLoopDelay(` for event-loop lag patterns; `pool_size` or `max:` near a `Pool` constructor for sizing examples; `selectinload(` or `joinedload(` for ORM eager-loading; `options.thresholds` in k6 test files; `Semaphore` class near concurrent fetch calls.

## Sources

- Node.js perf_hooks.monitorEventLoopDelay: https://nodejs.org/api/perf_hooks.html#perf_hooksmonitoreventloopdelayoptions
- clinic.js: https://clinicjs.org/documentation/
- SQLAlchemy 2.0 relationship loading: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
- Prisma eager loading (include): https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries#nested-reads
- k6 documentation: https://grafana.com/docs/k6/latest/
- autocannon: https://github.com/mcollina/autocannon
- py-spy profiler: https://github.com/benfred/py-spy
