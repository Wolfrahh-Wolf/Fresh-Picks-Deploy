# Monitoring and Observability

Covers health check endpoints, structured logging, metrics, distributed tracing, alerting rules and post-deploy verification; aligned with OpenTelemetry conventions and the Three Pillars of observability, checked 2026-11-26.

## Contents

- Health check endpoints
- Structured logging
- Metrics
- Distributed tracing
- Alerting
- Post-deploy verification

## Guidance

### Health check endpoints

Every service must expose two distinct HTTP endpoints:

| Endpoint | Purpose | What to check |
|---|---|---|
| `GET /healthz` | Liveness: is the process alive and not deadlocked? | Process is running; not in an irrecoverable state |
| `GET /readyz` | Readiness: can the service accept traffic? | Database connection pool is healthy; required caches are warm; config is loaded |

Both must return `200 OK` with an empty body or a minimal JSON object. Never include sensitive information in the response.

```typescript
// Express example
app.get('/healthz', (_req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.get('/readyz', async (_req, res) => {
  try {
    await db.query('SELECT 1');       // confirm DB connectivity
    res.status(200).json({ status: 'ready' });
  } catch {
    res.status(503).json({ status: 'not ready', reason: 'database unreachable' });
  }
});
```

**Probe design rules:**
- `/healthz` must be fast (< 10 ms, no I/O). Kubernetes liveness probes fire frequently; a slow liveness check causes unnecessary restarts.
- `/readyz` may do lightweight I/O but must time out in < 2 seconds and not fail under normal load. Keep the check shallow — `SELECT 1` not a full table scan.
- Never call downstream microservices from a readiness probe; a dependency outage must not mark your service as not ready (cascade failure).
- Expose health endpoints on a separate port or path that is not behind authentication middleware.

### Structured logging

Log in JSON with a consistent schema on every service. This enables log aggregation, querying and trace correlation.

Minimum required fields:

| Field | Type | Example |
|---|---|---|
| `level` | string | `info`, `warn`, `error` |
| `timestamp` | ISO 8601 string | `2026-11-26T18:00:00.123Z` |
| `message` | string | `Order created successfully` |
| `service` | string | `order-api` |
| `traceId` | string | (injected by OpenTelemetry SDK) |
| `spanId` | string | (injected by OpenTelemetry SDK) |

```json
{
  "level": "info",
  "timestamp": "2026-11-26T18:00:00.123Z",
  "message": "Order created",
  "service": "order-api",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "orderId": "ord-42",
  "durationMs": 23
}
```

**Rules:**
- Use log levels correctly: `debug` (dev-only, never in production by default), `info` (normal operations), `warn` (recoverable anomaly), `error` (operation failed, requires attention).
- Never log secrets, passwords, tokens, PII (email, name, phone) or full request/response bodies.
- Log the correlation between an HTTP request and all downstream calls by propagating the `traceId`.
- Emit exactly one log line per HTTP request at `info` level (access log) with method, path, status, duration and traceId.
- Use a structured logger library (e.g. `pino` for Node.js, `structlog` for Python); never format log strings manually.

### Metrics

Metrics are numeric measurements over time. Expose them in a format the platform's monitoring system can scrape (Prometheus exposition format is the standard; most platforms ingest it).

**Four golden signals** (what every service must measure):

| Signal | Metric | Alert threshold |
|---|---|---|
| Latency | p50, p95, p99 request duration | p99 > SLO target |
| Traffic | Requests per second | Sudden spike or drop |
| Errors | HTTP 5xx rate | > 1% of requests for > 5 min |
| Saturation | CPU %, memory %, queue depth | CPU > 80% sustained, memory > 85% |

Instrument using the OpenTelemetry SDK or a compatible library. Export to Prometheus (or push to a managed metrics platform).

```typescript
// Node.js with @opentelemetry/sdk-metrics
import { MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { PrometheusExporter } from '@opentelemetry/exporter-prometheus';

const exporter = new PrometheusExporter({ port: 9464 });
const meterProvider = new MeterProvider({
  readers: [new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 10_000 })],
});

const meter = meterProvider.getMeter('order-api');
const requestDuration = meter.createHistogram('http_request_duration_seconds', {
  description: 'HTTP request duration',
  unit: 's',
  boundaries: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5],
});
```

**Cardinality rule:** never use unbounded high-cardinality values (user IDs, raw URLs, trace IDs) as metric labels. High-cardinality labels cause memory explosions in time-series databases.

### Distributed tracing

Use OpenTelemetry for trace instrumentation. Configure the SDK once at application startup and use auto-instrumentation for HTTP, database and queue clients.

```typescript
// tracing.ts — initialise before importing anything else
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  serviceName: 'order-api',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

The auto-instrumentation automatically propagates `traceId` and `spanId` across HTTP calls, database queries and message queue operations, enabling end-to-end trace correlation.

Propagate the W3C `traceparent` header on all outbound HTTP calls so downstream services can join the same trace.

### Alerting

Alert on **symptoms**, not on causes. A symptom alert fires when users are affected; a cause alert fires when infrastructure changes, which is often irrelevant.

| ✅ Symptom (alert on) | ❌ Cause (monitor, don't alert by default) |
|---|---|
| HTTP 5xx error rate > 1% for 5 min | CPU usage > 70% |
| p99 latency > SLO for 10 min | Memory usage > 60% |
| `/readyz` returning 503 | Disk I/O throughput spike |
| Queue depth growing unboundedly | Number of active connections |

**Alert rules:**
- Every alert must have a runbook URL in its annotation.
- Alerts must be routed to the on-call channel, not to everyone.
- Keep alert noise low: false positives cause alert fatigue and get ignored.
- Use `for: 5m` (Prometheus syntax) to avoid alerting on transient spikes.
- Review and prune alerts quarterly; delete any that have never fired a true positive.

```yaml
# Prometheus alerting rule example
groups:
  - name: order-api
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{job="order-api",status=~"5.."}[5m]))
          / sum(rate(http_requests_total{job="order-api"}[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP 5xx rate on order-api"
          runbook: "https://docs.internal/runbooks/order-api-5xx"
```

### Post-deploy verification

Run these checks immediately after every deploy:

1. **Health probes:** confirm `/healthz` and `/readyz` return 200 on the new version.
2. **Smoke test:** exercise the critical path (create an order, list orders, retrieve an order) against the target environment.
3. **Error rate baseline:** observe the error rate in monitoring for 5 minutes post-deploy; confirm it has not risen above the pre-deploy baseline.
4. **Latency baseline:** confirm p99 latency has not increased beyond the SLO.
5. **Log check:** tail the logs for the first 2 minutes; look for new error patterns.

Automate smoke tests in the CI deploy job. If any check fails, trigger the rollback runbook (see `rollback.md`).

## Examples

### Pino structured logger configuration (Node.js)

```typescript
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: { service: 'order-api' },
  redact: ['req.headers.authorization', 'req.body.password'],
});
```

### Minimal Grafana dashboard panels

| Panel | Query |
|---|---|
| Request rate | `rate(http_requests_total{job="order-api"}[5m])` |
| Error rate % | `100 * sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| p99 latency | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| Memory usage | `container_memory_usage_bytes{name="order-api"}` |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Combining liveness and readiness into one `/health` endpoint | A database outage causes liveness failures, triggering unnecessary pod restarts | Separate `/healthz` (no I/O) and `/readyz` (checks dependencies) |
| Calling downstream services from a readiness probe | A dependency outage cascades to your service being marked not-ready | Only check your own dependencies (DB, cache); never fan out to other microservices |
| Logging PII or secrets | GDPR and security violations; credentials in log archives indefinitely | Redact sensitive fields using the logger's `redact` option |
| Alerting on CPU spikes | High CPU is often benign (GC, compilation warm-up); alerts desensitise the team | Alert on error rate and latency SLO breaches instead |
| Using high-cardinality labels in metrics (e.g. user ID as a label) | Time-series database uses unbounded memory; query performance degrades | Use only low-cardinality labels (endpoint, method, status code) |
| No post-deploy verification step | Bugs introduced by the deploy are discovered by users, not the team | Run smoke tests and monitor error rate for 5 minutes in every deploy job |

## Checklist

- [ ] `/healthz` and `/readyz` endpoints are distinct and return 200 after every deploy.
- [ ] All logs are JSON-structured with `level`, `timestamp`, `message`, `service` and `traceId`.
- [ ] No secrets, passwords or PII appear in logs.
- [ ] The four golden signals (latency, traffic, errors, saturation) are instrumented.
- [ ] At least one alert fires on HTTP 5xx error rate > 1% for > 5 min.
- [ ] Every alert has a runbook URL annotation.
- [ ] OpenTelemetry tracing is configured and exporting to the project's trace backend.
- [ ] Post-deploy smoke test runs in CI deploy job and fails the job if it fails.

## Verify with context7 and gh_grep

- **context7:** Resolve `pino` (Node.js) or `structlog` (Python) at the locked version. Check: `pino` `redact` option, `formatters.level` customisation. Resolve `@opentelemetry/sdk-node`, `@opentelemetry/auto-instrumentations-node` at current stable. Check: `NodeSDK` constructor options, `OTLPTraceExporter` URL env var convention.
- **gh_grep:** Search `GET /healthz` with `GET /readyz` for dual-endpoint patterns; `pino({` with `redact:` for structured logger setups; `histogram_quantile(0.99` for latency alert queries; `for: 5m` with `rate(http_requests_total` for error-rate alerting rules.

## Sources

- OpenTelemetry documentation: https://opentelemetry.io/docs/
- Prometheus alerting rules: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- Google SRE Book — The Four Golden Signals: https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals
- pino logger: https://getpino.io/
