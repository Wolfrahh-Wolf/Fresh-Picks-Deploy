# Error Handling

Covers error taxonomy, boundaries, mapping errors to HTTP responses, retries, timeouts and safe error messages for backend services; patterns current as of 2026-11-26.

## Contents

- Error taxonomy
- Error boundaries
- Mapping errors to HTTP responses
- Safe error messages
- Retries and timeouts
- Structured error logging

## Guidance

### Error taxonomy

Classify every error before deciding how to handle it:

| Class | Description | Examples | Action |
|---|---|---|---|
| Validation | Input fails business or format constraints | Missing field, invalid enum value, out-of-range number | 400; return detail to caller |
| Authentication | Identity cannot be established | No token, expired token, bad signature | 401; generic message |
| Authorization | Identity lacks permission | Wrong role, wrong tenant, object ownership | 403; generic message |
| Not found | Resource does not exist (and existence is not sensitive) | Unknown ID in a public API | 404 |
| Conflict | State conflict | Duplicate key, optimistic lock failure | 409 |
| Operational | External dependency failed; retryable | DB timeout, downstream 503, queue full | 502/503/504; retry with backoff |
| Rate limit | Caller exceeded quota | Too many requests | 429; include `Retry-After` |
| Programmer | Bug in this codebase | TypeError, null dereference, assertion failure | Log at fatal, 500; no detail to caller; shut down if state is unknown |

Operational errors are expected and recoverable. Programmer errors are bugs; the process should not continue in an unknown state.

### Error boundaries

Place explicit boundaries at every entry and exit point of the service:

1. **Inbound boundary** (before handlers): validate all inputs; reject invalid requests immediately with a 400 and a safe, structured message.
2. **Service boundary**: wrap every external call (database, HTTP, queue) in a try/catch that classifies the error and re-throws a typed application error.
3. **Outbound boundary** (error middleware): a single, final error handler maps application errors to HTTP responses. No other layer sends a response on error.

```
Inbound       Service layer           Error middleware
─────────     ───────────────         ─────────────────
Validate  →   Call DB / HTTP  →  ✗   Catch all; map to response
Input         Catch; wrap error  →   Log; send safe body
```

**Express 5 centralised error handler:**

```js
// middleware/errors.js  — always the last app.use()
export function errorHandler(err, req, res, next) {
  const status  = err.status ?? err.statusCode ?? 500;
  const isClient = status < 500;

  if (!isClient) {
    logger.error({
      err,
      reqId:  req.id,
      method: req.method,
      path:   req.path,
    }, 'server error');
  }

  res.status(status).json({
    error: isClient ? err.message : 'An unexpected error occurred',
    // Include a request ID so callers can correlate with logs
    reqId: req.id,
  });
}
```

**FastAPI exception handler:**

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("server error", exc_info=exc, req_id=request.state.req_id)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.safe_message if exc.status_code < 500 else "An unexpected error occurred",
            "req_id": request.state.req_id,
        },
    )
```

### Mapping errors to HTTP responses

| Situation | Status | Body |
|---|---|---|
| Validation failure | 400 | `{ "error": "<field>: <reason>" }` |
| Auth failed | 401 | `{ "error": "Unauthorized" }` |
| Permission denied | 403 | `{ "error": "Forbidden" }` |
| Resource not found | 404 | `{ "error": "Not found" }` |
| Duplicate / conflict | 409 | `{ "error": "<context-safe description>" }` |
| Downstream service failed | 502 | `{ "error": "Service unavailable" }` |
| Timeout waiting for downstream | 504 | `{ "error": "Gateway timeout" }` |
| Unhandled server error | 500 | `{ "error": "An unexpected error occurred" }` |

Always include `req_id` or `trace_id` in every error response so callers can correlate with server-side logs.

### Safe error messages

**Never** send to callers:
- Stack traces
- SQL error text (reveals schema, DB engine, table names)
- Internal file paths
- Downstream service names or hostnames
- Sensitive data contained in the failing request

**Always** send to callers:
- A human-readable, safe, specific message for 4xx errors
- A generic message for 5xx errors
- The request ID for correlation

Log the full error (including stack trace and all context) server-side only.

### Retries and timeouts

**Always set a timeout on every outbound call.** An unbounded call holds a connection and blocks the caller indefinitely.

```js
// Node.js with native fetch (Node.js 18+)
const signal = AbortSignal.timeout(5000); // 5 seconds
const response = await fetch(url, { signal });
```

```python
# httpx (Python async)
async with httpx.AsyncClient(timeout=5.0) as client:
    response = await client.get(url)
```

**Retry rules:**

| Condition | Retry? |
|---|---|
| Network timeout or connection reset | Yes, with exponential backoff |
| Downstream 500 or 503 | Yes, if the operation is idempotent; check `Retry-After` for 429/503 |
| Downstream 400, 401, 403, 404 | No; retrying will not help |
| Any write operation | Only if idempotency is guaranteed (idempotency key, database upsert) |

Exponential backoff formula: `delay = base * 2^attempt + jitter`. Jitter (random 0–base seconds) prevents synchronized retry storms when multiple callers fail at the same time.

Cap the maximum number of retries (3 is a reasonable default for external services) and the maximum total wait time. Implement a circuit breaker for chronically failing dependencies.

```js
// Simple retry with exponential backoff
async function withRetry(fn, { maxAttempts = 3, baseMs = 200 } = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try { return await fn(); }
    catch (err) {
      if (!isRetryable(err) || attempt === maxAttempts - 1) throw err;
      const delay = baseMs * 2 ** attempt + Math.random() * baseMs;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

### Structured error logging

Log every error with enough context for the on-call engineer to understand what happened and correlate with the caller's report:

Required fields per error log entry:

| Field | Example |
|---|---|
| `level` | `error`, `fatal` |
| `req_id` | `"c7f4a1b2"` |
| `method` | `"POST"` |
| `path` | `"/api/v1/orders"` |
| `status` | `500` |
| `err.message` | `"connection refused"` |
| `err.stack` | Full stack trace (server-side only) |
| `duration_ms` | `1340` |

Do not log request bodies, tokens, passwords or PII. Redact them before logging.

## Examples

### Typed application error class (Node.js)

```js
export class AppError extends Error {
  constructor(message, { status = 500, code } = {}) {
    super(message);
    this.status = status;
    this.code   = code;
    this.name   = 'AppError';
  }
  get isOperational() { return this.status < 500; }
}

// Usage in service
if (!user) throw new AppError('User not found', { status: 404 });
```

### Python typed error hierarchy

```python
class AppError(Exception):
    def __init__(self, safe_message: str, status_code: int = 500):
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.status_code  = status_code

class NotFoundError(AppError):
    def __init__(self, what: str):
        super().__init__(f"{what} not found", status_code=404)

class ForbiddenError(AppError):
    def __init__(self):
        super().__init__("Forbidden", status_code=403)
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `res.json({ error: err.stack })` | Leaks implementation details to callers | Log the stack server-side; send only a safe message |
| Catching all errors and swallowing them with `catch (e) {}` | Hides bugs; leaves the system in an unknown state | At minimum log every caught error |
| Retrying non-idempotent writes on failure | Creates duplicates | Only retry idempotent operations or operations protected by an idempotency key |
| No timeout on outbound calls | One slow dependency can saturate all connections | Set explicit timeouts on every outbound call |
| Sending `200 OK` with an error body | Client libraries and monitoring tools miss the error | Always use the correct HTTP status code |
| Including DB error text in 500 response | Reveals schema, table names, SQL dialect | Catch DB errors in the service layer; replace with `AppError` |

## Checklist

- [ ] Every outbound call has an explicit timeout.
- [ ] No stack trace, SQL, file path or internal hostname in any HTTP response body.
- [ ] A single, final error middleware handles all errors; route handlers do not send error responses themselves.
- [ ] Every 5xx error is logged with `req_id`, method, path, status and stack trace.
- [ ] Every 4xx validation error includes a safe, specific message.
- [ ] Retries apply only to retryable, idempotent operations with exponential backoff and a cap.
- [ ] `req_id` or `trace_id` is included in every error response.
- [ ] Logs contain no request bodies, tokens, passwords or PII.

## Verify with context7 and gh_grep

- **context7:** Check `http-errors` or `createError` for Node.js error creation conventions; `AbortSignal.timeout` availability (Node.js 17.3+); `httpx` timeout configuration for the locked Python version; FastAPI `exception_handler` decorator signature.
- **gh_grep:** Search `app.use((err, req, res, next)` for centralised Express error handler patterns; `AbortSignal.timeout(` for timeout idioms; `exception_handler(AppError)` or `@app.exception_handler` for FastAPI; `baseMs \* 2 \*\* attempt` or `exponential backoff` for retry implementations.

## Sources

- Node.js http-errors package: https://github.com/jshttp/http-errors
- MDN: AbortSignal.timeout(): https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static
- FastAPI exception handlers: https://fastapi.tiangolo.com/tutorial/handling-errors/
- httpx timeout documentation: https://www.python-httpx.org/advanced/timeouts/
- AWS: Exponential Backoff and Jitter: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
