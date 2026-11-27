# Node.js Runtime

Covers the Node.js runtime model, event loop, async error handling, streams, process management, graceful shutdown and configuration; assumes Node.js 22 LTS (the current LTS as of 2026-11-26). The project's lockfile and `.nvmrc` or `.node-version` win over any version here.

## Contents

- Runtime model and event loop
- Async patterns and error handling
- Streams and backpressure
- Process management
- Graceful shutdown
- Configuration

## Guidance

### Runtime model and event loop

Node.js runs JavaScript on a single main thread with a non-blocking event loop backed by libuv's thread pool (default size 4; set `UV_THREADPOOL_SIZE` for I/O-heavy workloads). Understand the phases: timers → I/O callbacks → idle → poll → check (`setImmediate`) → close callbacks.

**Never block the event loop.** A synchronous computation that takes more than a few milliseconds delays every concurrent request.

| Operation type | Correct tool |
|---|---|
| I/O (file, network, DB) | `async/await` over async APIs |
| CPU-bound (crypto, parsing, compression) | `worker_threads` or `child_process` |
| Scheduled polling | `setInterval` with `timer.unref()` |
| Deferred microtask | `queueMicrotask()` or `Promise.resolve().then()` |

Check event loop lag in production with `perf_hooks.monitorEventLoopDelay()` (Node.js 11.10+). A lag above 100 ms consistently signals a blocking operation.

### Async patterns and error handling

Prefer `async/await` over raw callbacks and `.then()` chains. All promises must be awaited or have a `.catch()`.

```js
// Bad: unhandled rejection if getUser rejects
router.get('/users/:id', (req, res) => {
  getUser(req.params.id).then(u => res.json(u));
});

// Good: awaited inside async handler; Express 5 forwards thrown errors automatically
router.get('/users/:id', async (req, res) => {
  const user = await getUser(req.params.id); // throws -> error middleware
  res.json(user);
});
```

**Global safety nets** – log and initiate graceful shutdown; never try to continue after an uncaught exception because process state is undefined:

```js
process.on('unhandledRejection', (reason) => {
  logger.fatal({ reason }, 'unhandledRejection');
  shutdown('unhandledRejection');
});
process.on('uncaughtException', (err) => {
  logger.fatal({ err }, 'uncaughtException');
  shutdown('uncaughtException');
});
```

Run with `--unhandled-rejections=strict` in CI to surface latent rejections as hard errors.

**Operational vs. programmer errors:**

| Class | Examples | Response |
|---|---|---|
| Operational | DB timeout, 404, validation failure | Log at `warn`, map to a typed response, continue |
| Programmer | TypeError, assertion failure, logic bug | Log at `fatal`, shut down and let the process manager restart |

### Streams and backpressure

Use `stream.pipeline()` (not `.pipe()`) so errors propagate and cleanup happens automatically:

```js
import { pipeline } from 'node:stream/promises';
await pipeline(readable, transform, writable);
```

Always check the return value of `writable.write()`. When it returns `false`, pause the readable until the `drain` event fires. `stream.pipeline()` handles this automatically.

For web streams (Node.js 18+), `ReadableStream`, `WritableStream` and `TransformStream` are available globally and interoperate with `fetch`.

### Process management

- Run the application under a process manager (systemd, PM2 in cluster mode, or a container orchestrator) so it restarts on crash.
- One process per container is the default for Docker/Kubernetes. For multi-core bare-metal deployments use the `cluster` module or Fastify's `--workers` flag.
- Never rely on the process staying up: design for stateless restarts.
- Read configuration from environment variables only; never from command-line flags that could appear in `ps` output.

### Graceful shutdown

Respond to `SIGTERM` (orchestrator termination) and `SIGINT` (Ctrl-C) with the same handler:

```js
const shutdown = (signal) => {
  if (isShuttingDown) return;
  isShuttingDown = true;
  server.close(async (err) => {
    if (err) { logger.error(err); process.exit(1); }
    await db.end();           // close connection pool
    await redis.quit();       // close cache client
    process.exit(0);
  });
  server.closeIdleConnections();   // Node.js 18.2+
  // Force exit if cleanup hangs
  setTimeout(() => {
    server.closeAllConnections();
    process.exit(1);
  }, 10_000).unref();
};
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));
```

Order: stop accepting → drain in-flight → close DB pool → close other clients → exit.

### Configuration

- Read all configuration from `process.env`. Validate at startup using a schema library (zod, envalid, or joi); crash with a clear message if a required variable is missing.
- Never hard-code connection strings, secrets or feature-flag values.
- Keep `.env.example` up to date with every variable name but no real values.
- For multi-environment setups, use a `.env` file for local dev only; inject real secrets via the platform's secret manager in staging and production.

```js
import { z } from 'zod';
const env = z.object({
  PORT:         z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  SECRET_KEY:   z.string().min(32),
  NODE_ENV:     z.enum(['development', 'production', 'test']),
}).parse(process.env);
```

## Examples

### Worker thread for CPU-bound work

```js
// main.js
import { Worker } from 'node:worker_threads';
function hashInWorker(data) {
  return new Promise((resolve, reject) => {
    const w = new Worker('./workers/hasher.js', { workerData: data });
    w.on('message', resolve);
    w.on('error', reject);
  });
}

// workers/hasher.js
import { workerData, parentPort } from 'node:worker_threads';
import { hash } from 'argon2';
const result = await hash(workerData.password);
parentPort.postMessage(result);
```

### Event loop lag monitor

```js
import { monitorEventLoopDelay } from 'node:perf_hooks';
const histogram = monitorEventLoopDelay({ resolution: 10 });
histogram.enable();
setInterval(() => {
  const lag = histogram.mean / 1e6; // nanoseconds to milliseconds
  if (lag > 100) logger.warn({ lagMs: lag }, 'event loop lag');
  histogram.reset();
}, 30_000).unref();
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Blocking the event loop with `fs.readFileSync` or `JSON.parse` on a large payload | Stalls all concurrent requests | Use async file API; parse in a worker thread for large payloads |
| Swallowing a rejection with an empty `.catch(() => {})` | Hides bugs; leaves the system in an unknown state | Log the error or re-throw with context |
| Setting `UV_THREADPOOL_SIZE` and not increasing it for heavy I/O | Thread pool exhaustion causes artificial serialisation | Set `UV_THREADPOOL_SIZE=16` or higher for DB-heavy services |
| Storing secrets in process arguments (`--secret=xyz`) | Visible in `ps aux` | Use environment variables |
| Not calling `.unref()` on timers used in graceful shutdown | Timer keeps the event loop alive and delays exit | Always `.unref()` safety-timeout timers |
| Using `process.exit(0)` without closing DB connections | In-flight transactions are truncated | Drain connections first; `process.exit` only inside the `server.close` callback |

## Checklist

- [ ] No synchronous I/O or CPU loop on the main thread for more than ~5 ms.
- [ ] Every promise is awaited or has a `.catch()`.
- [ ] `unhandledRejection` and `uncaughtException` handlers log then shut down.
- [ ] `SIGTERM` and `SIGINT` trigger graceful shutdown with a force-exit timeout.
- [ ] Configuration is validated at startup; the process crashes with a clear message on a missing required variable.
- [ ] No secret or connection string appears in source; `.env.example` has all variable names.
- [ ] Streams use `pipeline()` or manually handle backpressure.
- [ ] CPU-bound work runs in a `worker_threads` Worker, not on the event loop.

## Verify with context7 and gh_grep

- **context7:** Resolve `node` at the version in the project's `.nvmrc` or `engines.node`. Check: `closeIdleConnections` availability (Node.js 18.2+), `monitorEventLoopDelay` options, `stream.pipeline` promise API (Node.js 15+), `worker_threads` message passing, `--unhandled-rejections` modes.
- **gh_grep:** Search `process.on('SIGTERM'` to see real graceful-shutdown patterns; `server.closeIdleConnections` for adoption; `UV_THREADPOOL_SIZE` in Dockerfile or env configuration; `monitorEventLoopDelay` in production observability setups.

## Sources

- Node.js 22 documentation, Event Loop, Timers and process: https://nodejs.org/en/docs/guides/event-loop-timers-and-nexttick
- Node.js 22 API reference, http.Server.closeIdleConnections: https://nodejs.org/api/http.html#servercloseidleconnections
- Node.js 22 API reference, perf_hooks.monitorEventLoopDelay: https://nodejs.org/api/perf_hooks.html#perf_hooksmonitoreventloopdelayoptions
- Node.js 22 API reference, stream.pipeline: https://nodejs.org/api/stream.html#streampipelinestreams-callback
- Node.js 22 API reference, worker_threads: https://nodejs.org/api/worker_threads.html
