# Rate Limiting

Covers token-bucket and sliding-window algorithms, partition key selection, rate-limit response headers (IETF draft-ietf-httpapi-ratelimit-headers), distributed counters with Redis and client backoff strategies; checked 2026-11-26.

## Contents

- When and where to apply rate limits
- Algorithms: token bucket and sliding window
- Partition keys
- Rate-limit response headers
- Distributed rate limiting with Redis
- Client backoff on 429

## Guidance

### When and where to apply rate limits

Apply a rate limit to every public or partner-facing endpoint, and to every internal endpoint exposed across a service boundary. Enforce limits **before** any business logic, database access or external call — a limit that runs after a database query does not protect the database.

Layer your limits:

| Layer | Mechanism | Protects |
|---|---|---|
| Edge / API gateway | Global per-IP burst limit | The entire backend from DDoS and scrapers |
| Application | Per-API-key or per-user limit | Individual resource quotas |
| Downstream | Per-service limit on outbound calls | Third-party API quotas and your own microservices |

Do not rely on a single layer. Combine edge and application limits.

### Algorithms: token bucket and sliding window

**Token bucket** (best for bursty traffic):

- Each key has a bucket of capacity `C` tokens.
- One token is consumed per request.
- Tokens refill at rate `R` tokens/second up to capacity.
- A request that arrives when the bucket is empty is rejected (429) or queued.
- Allows short bursts up to `C` requests, then sustains at `R` requests/second.

**Sliding window** (best for smooth enforcement):

- Track request timestamps in a moving time window (e.g. 1 minute).
- Count requests in the window; reject if the count exceeds the limit.
- More precise than a fixed window (no edge-of-window burst exploit), but requires more storage.
- A fixed-window variant is cheaper but allows up to `2 × limit` requests at the window boundary.

**Choosing between them:**

| Goal | Algorithm |
|---|---|
| Allow short bursts then throttle | Token bucket |
| Smooth, predictable rate enforcement | Sliding window |
| Lowest storage overhead | Fixed window (with awareness of boundary spike) |

For most APIs: use **token bucket at the edge** (for burst protection) and **sliding window per key** at the application layer (for fair quota enforcement).

### Partition keys

The partition key determines who shares a limit bucket.

| Key | Granularity | Use case |
|---|---|---|
| API key | Per integration | Partner and developer portals |
| User ID (authenticated) | Per user | Per-user resource quotas |
| IP address | Per network client | Unauthenticated or pre-auth endpoints (login, password reset) |
| Tenant ID | Per organisation | Multi-tenant SaaS; tenant-level quotas |

Priority order when multiple keys are available: **API key > authenticated user ID > IP address**. Never use IP as the sole key on authenticated endpoints — shared NAT or VPNs cause false positives.

Avoid using user-supplied values (e.g. query parameters) as partition keys. Attackers can spoof them to exhaust other users' buckets.

### Rate-limit response headers

Include rate-limit headers on **every** response (not only on 429), so clients can track consumption proactively.

The IETF `draft-ietf-httpapi-ratelimit-headers` draft (evolving) defines two consolidated structured headers. Many APIs still use the earlier per-field form; use whichever the project has established — but be consistent.

**Common per-field form (widely implemented):**

```http
RateLimit-Limit: 100
RateLimit-Remaining: 73
RateLimit-Reset: 42
```

- `RateLimit-Limit`: the quota ceiling for the current window.
- `RateLimit-Remaining`: requests left before the client is throttled.
- `RateLimit-Reset`: seconds until the quota resets (delta-seconds, not an epoch timestamp — avoids clock-skew bugs).

**On a 429 response, always include `Retry-After`:**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
Retry-After: 42
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 42

{
  "type": "https://api.example.com/problems/rate-limited",
  "title": "Too many requests",
  "status": 429,
  "detail": "Rate limit of 100 requests per minute exceeded. Retry after 42 seconds."
}
```

`Retry-After` values: an integer (delta-seconds) or an HTTP-date. Delta-seconds is simpler and avoids timezone issues. Align it with `RateLimit-Reset`.

### Distributed rate limiting with Redis

A single in-memory counter only works on a single instance. For multi-instance services use a shared counter in Redis.

**Token bucket in Redis (Lua script for atomicity):**

```lua
-- KEYS[1] = bucket key (e.g. "rl:user:42")
-- ARGV[1] = capacity, ARGV[2] = refill_rate (tokens/sec), ARGV[3] = now (unix ms), ARGV[4] = cost
local key = KEYS[1]
local capacity   = tonumber(ARGV[1])
local rate       = tonumber(ARGV[2])
local now        = tonumber(ARGV[3])
local cost       = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens      = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

local elapsed = math.max(0, now - last_refill)
tokens = math.min(capacity, tokens + elapsed * rate / 1000)

if tokens < cost then
  return {0, math.ceil((cost - tokens) / rate * 1000)}
end

tokens = tokens - cost
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('PEXPIRE', key, math.ceil(capacity / rate * 1000) + 5000)
return {1, tokens}
```

Call with `EVALSHA` (pre-loaded) for minimal latency. The Lua script runs atomically on the Redis server — no race conditions.

**Sliding window counter in Redis (simpler):**

```javascript
async function isAllowed(redisClient, key, limit, windowSeconds) {
  const now = Date.now();
  const windowStart = now - windowSeconds * 1000;
  const multi = redisClient.multi();
  multi.zremrangebyscore(key, '-inf', windowStart);  // expire old entries
  multi.zadd(key, now, `${now}-${Math.random()}`);   // record request
  multi.zcard(key);                                   // count in window
  multi.expire(key, windowSeconds + 1);
  const results = await multi.exec();
  const count = results[2];
  return count <= limit;
}
```

Use `MULTI`/`EXEC` for optimistic locking. For strict consistency under high concurrency, prefer the Lua token-bucket approach.

### Client backoff on 429

Document the expected client behaviour in the API contract and developer portal.

**Algorithm:**

1. Receive 429 response.
2. Read `Retry-After` header value (seconds).
3. Wait `Retry-After` seconds (minimum).
4. Add a random jitter of 0–`Retry-After` × 10% to avoid the thundering herd (all clients retrying simultaneously).
5. Retry the request at most `MAX_RETRIES` times (typically 3).
6. If still receiving 429 after retries, back off exponentially: `wait = min(base × 2^attempt, maxWait)`.
7. Surface the error to the caller after all retries are exhausted.

**Server responsibilities:**

- Always set `Retry-After`; clients that do not receive it will retry immediately (thundering herd).
- Keep `Retry-After` ≤ 60 seconds for interactive APIs; longer values are acceptable for batch endpoints.
- On a second 429 within the same client session, increase `Retry-After` to discourage tight retry loops.

## Examples

### Express middleware applying a sliding window per API key

```javascript
import { createClient } from 'redis';

const redis = createClient();
await redis.connect();

export async function rateLimitMiddleware(req, res, next) {
  const key = `rl:${req.headers['x-api-key'] ?? req.ip}`;
  const LIMIT = 100;
  const WINDOW = 60; // seconds

  const now = Date.now();
  const windowStart = now - WINDOW * 1000;

  await redis.zRemRangeByScore(key, '-inf', windowStart);
  const count = await redis.zCard(key);

  const remaining = Math.max(0, LIMIT - count - 1);
  const reset = Math.ceil(WINDOW - (now % (WINDOW * 1000)) / 1000);

  res.setHeader('RateLimit-Limit', LIMIT);
  res.setHeader('RateLimit-Remaining', remaining);
  res.setHeader('RateLimit-Reset', reset);

  if (count >= LIMIT) {
    res.setHeader('Retry-After', reset);
    return res.status(429).json({
      type: 'https://api.example.com/problems/rate-limited',
      title: 'Too many requests',
      status: 429,
      detail: `Limit of ${LIMIT} requests per ${WINDOW}s exceeded.`,
    });
  }

  await redis.zAdd(key, { score: now, value: `${now}-${Math.random()}` });
  await redis.expire(key, WINDOW + 1);
  next();
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Applying the rate limit after the database call | The database is hit before the check; limit protects nothing | Check the counter at the start of the handler, before any I/O |
| Using an in-process counter on a multi-instance service | Each instance has its own counter; total throughput = limit × instance count | Use Redis or a shared counter store |
| Using IP address as the sole key on authenticated endpoints | Shared NAT or corporate proxies cause false positives for many users | Partition by API key or user ID; fall back to IP only for unauthenticated endpoints |
| Omitting `Retry-After` on 429 | Clients retry immediately in a tight loop, amplifying load | Always include `Retry-After` with the seconds to wait |
| Using an epoch timestamp for `RateLimit-Reset` | Clients in different timezones calculate incorrect wait times | Use delta-seconds (integer seconds until reset) |
| Setting headers only on 429 responses | Clients cannot proactively shape traffic; they only discover limits on failure | Include `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset` on every response |

## Checklist

- [ ] Rate limit applied before any business logic or database access on every public endpoint.
- [ ] Partition key is API key (authenticated) or IP (unauthenticated), not a client-supplied value.
- [ ] Counter is stored in Redis (or equivalent shared store) for multi-instance deployments.
- [ ] `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset` headers present on all responses.
- [ ] 429 responses include `Retry-After` aligned with `RateLimit-Reset`.
- [ ] 429 response body is `application/problem+json`.
- [ ] Client backoff policy (wait, jitter, max retries) is documented in `docs/API-CONTRACTS.md`.

## Verify with context7 and gh_grep

- **context7:** Resolve `ioredis` or `redis` (Node.js) at the locked version. Check: `zAdd`, `zRemRangeByScore`, `zCard`, `expire` command signatures; Lua `EVALSHA` loading pattern; connection pool configuration.
- **gh_grep:** Search `RateLimit-Remaining` for header-setting patterns; `Retry-After` with `429` for throttle response implementations; `zremrangebyscore` for sliding-window Redis patterns; `EVALSHA` with token-bucket Lua scripts.

## Sources

- IETF draft-ietf-httpapi-ratelimit-headers: https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- RFC 9110 HTTP Semantics (429 Too Many Requests, Retry-After): https://www.rfc-editor.org/rfc/rfc9110
- RFC 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457
