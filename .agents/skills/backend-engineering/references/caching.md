# Caching

Covers cache layers, key design, TTL strategy, invalidation, stampede prevention and what must not be cached; patterns current as of 2026-11-26.

## Contents

- Cache layer overview
- Cache patterns
- Key design
- TTL strategy and jitter
- Invalidation
- Cache stampede prevention
- What must not be cached

## Guidance

### Cache layer overview

| Layer | Scope | Latency | Typical use |
|---|---|---|---|
| In-process (Map, LRU) | Single instance | < 1 ms | Small, stable config; computed constants; short-lived request deduplication |
| Shared (Redis, Memcached) | All instances | 1–5 ms | Session data; computed query results; rate-limit counters; feature flags |
| HTTP cache (CDN, reverse proxy, `Cache-Control`) | Edge | Varies | Public, cacheable API responses; static assets |
| Database query cache | DB server | Transparent | Usually implicit; do not rely on it as the sole caching strategy |

Choose the simplest layer that solves the problem. In-process caches add no network hop but do not share state across instances; use them only for truly instance-local data.

### Cache patterns

**Cache-aside (lazy loading)** – most common:

1. Check cache. On hit, return cached value.
2. On miss, query the source of truth.
3. Write result to cache with TTL.
4. Return result.

Pros: only requested data is cached; tolerant of cache failures (fall back to DB). Cons: first request after a miss or expiry is slow; stampede risk on popular keys.

**Write-through:**

Write to cache and DB atomically (or in sequence) on every mutation. Cache is always warm. Cons: higher write latency; wastes space for data that is never read.

**Read-through:**

Cache sits in front of the DB and loads on miss automatically (the application never reads the DB directly). Requires a cache client that supports this mode (e.g., some Redis clients with a loader function).

**Write-behind (write-back):**

Write to cache; flush to DB asynchronously. Highest write throughput; risk of data loss if cache crashes before the flush. Use only when eventual persistence is acceptable.

For most backends, **cache-aside with stampede protection** is the right default.

### Key design

A cache key must:
- Uniquely identify the data item (all query parameters that affect the result).
- Be stable (same input → same key, every time).
- Be safe to log (no secrets, tokens or PII).

Namespace keys to prevent cross-service or cross-tenant collisions:

```
{service}:{version}:{tenant}:{entity}:{id}[:{variant}]
```

Example: `api:v2:t_42:user:9971:profile`

Include the tenant ID in every key for multi-tenant data. Failing to do so lets one tenant read another's cached data.

Avoid storing sensitive data (tokens, password hashes, PII) in cache keys or values. If a cached value must contain user data, consider encrypting it at rest.

### TTL strategy and jitter

Every cached key must have a TTL. Keys without TTL grow until memory is exhausted.

Choosing TTL:

| Data volatility | TTL guideline |
|---|---|
| Static config, feature flags | 5–30 minutes |
| User profile, session | 15 minutes (or session lifetime) |
| Computed aggregates | 1–5 minutes |
| Rate limit counters | Sliding window size |
| Real-time data | 5–30 seconds |

**Add jitter** to avoid synchronized expiration. When many keys are set at the same time (e.g., on a cache warm-up after a deploy), identical TTLs cause them all to expire simultaneously, sending a surge to the database.

```python
import random

BASE_TTL = 300  # 5 minutes
def ttl_with_jitter(base: int = BASE_TTL, spread: float = 0.1) -> int:
    """Add ±10% jitter to avoid synchronized expiry."""
    return int(base + random.uniform(-base * spread, base * spread))
```

```js
const BASE_TTL = 300;
const jitter = () => BASE_TTL + Math.floor((Math.random() * 2 - 1) * BASE_TTL * 0.1);
await redis.setex(key, jitter(), JSON.stringify(value));
```

### Invalidation

Prefer **TTL-based expiry** over active invalidation. Invalidation is hard to get right; a missed invalidation serves stale data, and over-invalidation eliminates the cache benefit.

When TTL is too long and freshness matters, use **event-driven invalidation**: on mutation, immediately delete or update the affected key. Use atomic operations (Redis `DEL`, `SET … EX`) to avoid race conditions.

Avoid invalidating by prefix (scanning keys is slow and blocks Redis). Structure keys so each invalidation operation targets exactly the affected entries.

**Version-based invalidation:** embed a version or ETag in the cache key. Incrementing the version logically invalidates all old keys without scanning. Old keys expire by TTL.

```
user:v3:9971:profile  ← after updating the user schema version to v3
user:v2:9971:profile  ← still in cache, ignored; expires by TTL
```

### Cache stampede prevention

A cache stampede (thundering herd) occurs when a popular key expires and many concurrent requests simultaneously miss and all hit the database to recompute the value.

**Option A: Distributed lock (mutex)**

```python
import uuid

async def get_with_lock(redis, key, fetch_fn, ttl):
    cached = await redis.get(key)
    if cached:
        return cached
    lock_key = f"{key}:lock"
    lock_value = str(uuid.uuid4())
    # Acquire lock with 5-second timeout
    acquired = await redis.set(lock_key, lock_value, ex=5, nx=True)
    if acquired:
        try:
            value = await fetch_fn()
            await redis.setex(key, ttl, value)
            return value
        finally:
            # Release only if we still own the lock
            if await redis.get(lock_key) == lock_value:
                await redis.delete(lock_key)
    else:
        # Wait briefly, then read (value should be populated by lock holder)
        await asyncio.sleep(0.05)
        return await redis.get(key)
```

**Option B: Probabilistic early expiration (XFetch)**

Proactively regenerate the cache before the key expires. As TTL approaches zero, the probability of an early refresh increases. Only one request will trigger the refresh; others continue to serve the still-valid key.

```js
// XFetch: beta controls eagerness (1.0 is standard)
function shouldRefreshEarly(ttlMs, computeTimeMs, beta = 1.0) {
  const delta = computeTimeMs * beta * Math.log(Math.random());
  return ttlMs + delta <= 0;
}
```

**Option C: Stale-while-revalidate**

Serve the stale cached value immediately while triggering an async background refresh. Requires storing the original TTL alongside the value so you can determine when it became stale.

### What must not be cached

- **Authentication credentials**: passwords, tokens, session secrets. These must never be in cache.
- **Authorization decisions that need to be instantly revocable**: if you must cache a permission check, use a very short TTL (< 60 s) and make the cache-miss path the authoritative one.
- **Non-idempotent operation results**: the result of a POST that created a record is not a cache entry.
- **Per-user sensitive data in a shared cache without tenant isolation**: always include `tenant_id` and `user_id` in the key.
- **Large binary blobs** unless you have measured that caching is worth the memory cost and eviction pressure.

## Examples

### Node.js cache-aside with stampede protection

```js
async function getCachedUser(redis, db, userId) {
  const key = `api:v1:user:${userId}`;
  const hit  = await redis.get(key);
  if (hit) return JSON.parse(hit);

  // Simple lock
  const lockKey = `${key}:lock`;
  const locked   = await redis.set(lockKey, '1', { NX: true, EX: 5 });
  if (locked) {
    const user = await db.users.findById(userId);
    if (user) await redis.setex(key, jitter(), JSON.stringify(user));
    await redis.del(lockKey);
    return user;
  } else {
    await sleep(50);
    const afterWait = await redis.get(key);
    return afterWait ? JSON.parse(afterWait) : db.users.findById(userId);
  }
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Caching without a TTL | Memory grows until OOM; stale data served forever | Every key must have a TTL |
| Identical TTLs on bulk-loaded keys | Synchronized expiry stampede | Add jitter (±10%) to every TTL |
| Including `tenant_id` in the value but not the key | One tenant reads another tenant's cached data | Include `tenant_id` in the cache key |
| Caching authentication tokens or session secrets | Cache breach exposes credentials | Never cache secrets; query the session store directly |
| Invalidating by key prefix with `SCAN` | SCAN blocks Redis single-threaded server under load | Use versioned keys; let TTL expire old versions |
| Treating a cache failure as a fatal error | Cache is a performance optimisation, not a source of truth | Fail open to the DB; log the cache error; alert if failure rate is high |

## Checklist

- [ ] Every cached key has a TTL.
- [ ] TTLs have jitter to prevent synchronized expiration.
- [ ] Tenant ID and user ID are part of every multi-tenant cache key.
- [ ] No authentication credentials or session secrets are stored in cache.
- [ ] A cache failure falls back to the source of truth, not to an error response.
- [ ] Popular or high-traffic keys are protected against stampedes (lock, XFetch or stale-while-revalidate).
- [ ] Invalidation targets specific keys, not prefix scans.
- [ ] Cache keys contain no PII or sensitive data.

## Verify with context7 and gh_grep

- **context7:** Resolve `ioredis` or `redis` (Node.js) and `redis-py` or `aioredis` (Python) at their locked versions. Check: `SET NX EX` atomicity; `SETEX` behaviour; `GET` return type for missing keys; pipeline and Lua scripting APIs.
- **gh_grep:** Search `redis.set(` with `NX` and `EX` options for distributed lock implementations; `ttl_with_jitter` or `random.uniform` near `setex` for jitter patterns; `stale-while-revalidate` in backend cache headers; `cache.get(key)` with a fallback `fetchFn` for cache-aside patterns.

## Sources

- Redis documentation, SET command NX/EX options: https://redis.io/commands/set/
- Redis documentation, Distributed Locks (Redlock): https://redis.io/docs/manual/patterns/distributed-locks/
- Antirez: Cache Stampede (XFetch algorithm): http://antirez.com/news/136
- AWS: Caching Strategies: https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Strategies.html
