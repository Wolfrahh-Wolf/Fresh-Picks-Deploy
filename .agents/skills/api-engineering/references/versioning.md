# API Versioning

Covers breaking-change rules, versioning strategies (URL, header, content-type), deprecation headers and sunset policy; aligned with RFC 8594 (Sunset header) and RFC 9110, checked 2026-11-26.

## Contents

- Breaking vs. non-breaking change rules
- Versioning strategies
- Deprecation and Sunset headers
- Sunset policy and migration guidance

## Guidance

### Breaking vs. non-breaking change rules

Apply these rules to every proposed API change before deciding whether to increment the version.

**Non-breaking — ship without a version bump:**

| Change | Notes |
|---|---|
| Add a new optional field to a response | Consumers using tolerant-reader must ignore unknown fields |
| Add a new optional query parameter with a default | Existing calls continue to work unchanged |
| Add a new endpoint | No existing consumers affected |
| Make a required request field optional | Existing clients already send it |
| Add a new enum value to a **request** field | Server handles new value; existing callers unaffected |
| Increase a numeric field's maximum allowed value | Clients that send smaller values are unaffected |
| Improve error messages or add extension members to problem details | Clients read `type` / `code`, not `message` text |

**Breaking — requires a new API version or a phased migration:**

| Change | Why it breaks |
|---|---|
| Remove or rename a field, endpoint or parameter | Existing consumers reference the old name |
| Change a field's type | Clients that parsed the original type will error |
| Change a field from optional to required in a request | Existing clients that omit the field are rejected |
| Remove an enum value from a **response** field | Consumers that stored or matched on the value break |
| Change the pagination shape (cursor field names) | Pagination clients can no longer advance pages |
| Change authentication scheme or add mandatory headers | All existing integrations break immediately |
| Change a 2xx response code to another 2xx code | Clients that branch on the specific code fail |

**Default rule:** prefer additive-only changes. If a breaking change is unavoidable, plan the versioning migration before writing code.

### Versioning strategies

Choose one strategy per API and apply it consistently across the entire surface.

#### URL versioning (`/v1/`, `/v2/`)

```
GET /v1/orders HTTP/1.1
GET /v2/orders HTTP/1.1
```

- Easiest to route, log and document.
- Both versions run simultaneously until the old one sunsets.
- Recommended for public and partner APIs where visibility and ease of adoption matter.
- Downside: proliferates route registrations; old versions must be actively maintained.

#### Header versioning (`API-Version: 2026-01-01`)

```
GET /orders HTTP/1.1
API-Version: 2026-01-01
```

- Keeps URI space clean; a single URL covers all versions.
- Requires consumers to manage headers explicitly; harder to test with a browser.
- Suitable for internal or platform APIs where all callers control their HTTP client.

#### Content-type versioning (`application/vnd.example.orders.v2+json`)

```
Accept: application/vnd.example.orders.v2+json
```

- Technically closest to REST (content negotiation); resource-granular.
- High client and server implementation complexity.
- Rarely worth the overhead in practice; prefer URL or header versioning.

**Do not mix strategies** within the same API surface. Pick one and document it in `docs/API-CONTRACTS.md`.

### Deprecation and Sunset headers

When an endpoint, field or version is being retired, signal it in every response before removal.

#### `Deprecation` header (RFC 9657 draft / de facto standard)

```http
Deprecation: true
```

Or with a date (preferred):

```http
Deprecation: Sun, 01 Jun 2026 00:00:00 GMT
```

The date is when the deprecation decision was made — not when removal happens. Set this header on the first release after the deprecation decision.

#### `Sunset` header (RFC 8594)

```http
Sunset: Sat, 31 Dec 2026 23:59:59 GMT
```

The `Sunset` date is when the endpoint or version stops responding. After this date, return 410 Gone (or 404 if 410 is not supported).

#### `Link` header with `rel="deprecation"` and `rel="successor-version"`

Provide a human-readable deprecation notice URL and a link to the replacement:

```http
Link: <https://api.example.com/docs/migration/v1-v2>; rel="deprecation",
      <https://api.example.com/v2/orders>; rel="successor-version"
```

Include all three headers together on every response from a deprecated endpoint.

### Sunset policy and migration guidance

Define the minimum runway in `docs/API-CONTRACTS.md`:

| Caller type | Minimum deprecation runway |
|---|---|
| Public (external developers) | 12 months |
| Partner (contracted integrators) | 6 months |
| Internal (services this org controls) | 4 weeks (with team agreement) |

Steps for a compliant retirement:

1. Architect documents the removal in `docs/API-CONTRACTS.md` with the sunset date and replacement.
2. Implementer adds `Deprecation`, `Sunset` and `Link` headers to the endpoint in the same release.
3. Notify all known consumers in writing (email, changelog, developer portal).
4. After the sunset date, return 410 Gone.
5. Remove the route in the next major release.

**Never remove an endpoint or field without at least one intermediate release carrying the deprecation headers.** Consumers must have a chance to observe the headers before the endpoint disappears.

## Examples

### Full deprecation header set

```http
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: Tue, 01 Oct 2026 00:00:00 GMT
Sunset: Wed, 31 Dec 2026 23:59:59 GMT
Link: <https://api.example.com/docs/deprecations/orders-v1>; rel="deprecation",
      <https://api.example.com/v2/orders>; rel="successor-version"
```

### Version routing in Express (URL versioning)

```javascript
// routes/index.js
const v1Router = require('./v1/orders');
const v2Router = require('./v2/orders');

app.use('/v1/orders', v1Router);  // keep alive until sunset
app.use('/v2/orders', v2Router);  // current version
```

### Post-sunset response (410 Gone)

```http
HTTP/1.1 410 Gone
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/gone",
  "title": "This endpoint has been removed.",
  "status": 410,
  "detail": "The /v1/orders endpoint was sunset on 2026-12-31. Use /v2/orders instead.",
  "instance": "/docs/deprecations/orders-v1"
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Treating field renames as non-breaking | Every consumer that reads the old name breaks | Rename = breaking; add the new name as an alias first, then sunset the old one |
| Removing endpoints without prior deprecation headers | Consumers get unexpected 404s with no warning | Always ship at least one release with `Deprecation` and `Sunset` headers first |
| Setting a Sunset date in the past | Consumers never had a chance to migrate | Minimum runway is 12 months for public APIs; compute the date before merging the deprecation |
| Running two URL versions indefinitely | Old code accumulates; both versions diverge silently | Enforce the sunset date; track sunset status in the deprecation log in `docs/API-CONTRACTS.md` |
| Mixing URL and header versioning in the same API | Consumers must guess which mechanism applies where | Pick one strategy; document it in `docs/API-CONTRACTS.md` |

## Checklist

- [ ] Every proposed change is classified as breaking or non-breaking before implementation.
- [ ] Breaking changes are accompanied by a new version or phased migration plan approved by the architect.
- [ ] Deprecated endpoints respond with `Deprecation`, `Sunset` and `Link` headers.
- [ ] Sunset date is at least the minimum runway from the deprecation date.
- [ ] All known consumers have been notified in writing.
- [ ] `docs/API-CONTRACTS.md` deprecation log is updated.
- [ ] Post-sunset responses return 410 Gone with a `application/problem+json` body pointing to the replacement.

## Verify with context7 and gh_grep

- **context7:** Not applicable for HTTP header semantics (RFC-defined). For Express or Fastify version-routing middleware, resolve the library at its locked version and check router APIs.
- **gh_grep:** Search `Sunset:` for real header usage; `Deprecation: true` or `Deprecation: Sun` for date-form usage; `rel="successor-version"` for Link header patterns; `app.use('/v2/'` for URL-versioning router registrations.

## Sources

- RFC 8594 The Sunset HTTP Header Field: https://www.rfc-editor.org/rfc/rfc8594
- RFC 9110 HTTP Semantics (410 Gone, status code semantics): https://www.rfc-editor.org/rfc/rfc9110
- IETF draft-ietf-httpapi-deprecation-header (Deprecation header): https://datatracker.ietf.org/doc/draft-ietf-httpapi-deprecation-header/
