# REST API Design

Covers HTTP resource modelling, method semantics, status codes, pagination, filtering, idempotency and error format per RFC 9110 (June 2022) and RFC 9457 (September 2023), checked 2026-11-26.

## Contents

- Resource modelling and URI design
- HTTP methods and their semantics
- Status codes
- Idempotency and safe retries
- Pagination and filtering
- Error response format (RFC 9457)

## Guidance

### Resource modelling and URI design

A REST resource is a named concept: `Order`, `Product`, `User`. URIs identify resources, not actions.

- Use lowercase plural nouns: `/orders`, `/order-items`, `/users/{userId}/addresses`.
- Separate words with hyphens, not underscores.
- Nest only one level for owned sub-resources: `/orders/{orderId}/lines`. Avoid deeper nesting; prefer `/order-lines?orderId={id}` if the sub-resource has independent lifecycle.
- Never encode verbs in the path (`/createOrder`, `/getUser`). Use the HTTP method to express the action.
- Use query parameters for filtering, sorting and pagination; never put mutable state in the path.
- Keep URIs stable. Changing them is a breaking change; use versioning or redirect if unavoidable.

### HTTP methods and their semantics

RFC 9110 defines method properties. Use them precisely.

| Method | Safe | Idempotent | Typical use |
|---|---|---|---|
| GET | Yes | Yes | Retrieve a resource or collection |
| HEAD | Yes | Yes | Same as GET but no body; use for existence checks |
| POST | No | No | Create a sub-resource or trigger an action |
| PUT | No | Yes | Replace a resource in full |
| PATCH | No | No* | Apply partial modifications |
| DELETE | No | Yes | Remove a resource |
| OPTIONS | Yes | Yes | Capability discovery (CORS pre-flight) |

*PATCH is idempotent only if the patch document is defined to be (e.g. replace-field, not append).

**Safe** means the request does not alter observable server state; browsers and caches may retry safe requests freely.
**Idempotent** means repeating the identical request leaves server state unchanged after the first application. The response code may differ (a second DELETE may return 404); only the state guarantee matters.

For POST actions that must be idempotent (payments, order placement), accept an `Idempotency-Key` header. Store the first result and return it verbatim on replay within the key's TTL (typically 24–48 hours). Return 422 if the same key is re-used with different parameters.

### Status codes

Use these codes consistently. Never invent meanings.

| Code | Meaning | Notes |
|---|---|---|
| 200 | OK | GET, PATCH, PUT when body is returned |
| 201 | Created | POST that created a resource; always include `Location: /resources/{id}` |
| 202 | Accepted | Async work started; include a poll or webhook URL in the body |
| 204 | No Content | Successful PUT/PATCH/DELETE with no body to return |
| 400 | Bad Request | Malformed syntax, unparseable JSON, missing required header |
| 401 | Unauthorised | Missing or invalid authentication credential |
| 403 | Forbidden | Authenticated but lacks permission; never expose hidden resource names |
| 404 | Not Found | Resource does not exist for this caller |
| 409 | Conflict | State conflict (duplicate key, optimistic lock mismatch) |
| 422 | Unprocessable Content | Syntactically valid but semantically invalid payload (validation failure) |
| 429 | Too Many Requests | Rate limit exceeded; always include `Retry-After` |
| 500 | Internal Server Error | Unexpected server fault; never expose stack traces |
| 503 | Service Unavailable | Maintenance or overload; include `Retry-After` |

### Idempotency and safe retries

- GET, HEAD, OPTIONS, PUT and DELETE are safe to retry on network failure without extra precautions.
- POST and non-idempotent PATCH require an application-level idempotency mechanism before automatic retry is safe.
- Idempotency-Key pattern: client generates a UUID per logical operation; server stores `(key → result)` for the TTL; re-use within TTL returns the stored result, re-use after TTL is treated as a new operation.
- Never auto-retry on 4xx (client error); always retry with `Retry-After` on 429 and 503.

### Pagination and filtering

**Cursor-based pagination** (preferred for large or live datasets):

- Client sends `cursor` (opaque base-64 encoded position) and `limit`.
- Server returns `nextCursor` (null when exhausted) and optionally `prevCursor`.
- Use a `Link` header with `rel="next"` and `rel="prev"` for RFC 8288 compliance.
- Never return unbounded collections; apply a default page size (e.g. 20) and a maximum (e.g. 100).

**Offset pagination** (acceptable for small, stable datasets):

- Client sends `offset` and `limit`; server returns total count.
- Offset pagination is inconsistent under concurrent inserts and expensive at high offsets on large tables.

**Filtering and sorting:**

- Express filters as query parameters: `GET /orders?status=pending&customerId=42`.
- Express sort as `sort=createdAt:desc,id:asc`.
- Reject unknown filter keys with 400 rather than silently ignoring them.
- Never allow arbitrary server-side expression evaluation in filter parameters.

### Error response format (RFC 9457)

All error responses must use `Content-Type: application/problem+json`.

Required members:

| Member | Type | Purpose |
|---|---|---|
| `type` | URI string | Identifies the problem type; dereference to docs. Use `about:blank` only when no type URI is available. |
| `title` | String | Short, stable summary of the problem type (do not vary per occurrence). |
| `status` | Integer | HTTP status code (mirrors the actual response code). |
| `detail` | String | Human-readable explanation specific to this occurrence. |
| `instance` | URI string | Optional. Identifies this specific occurrence (log reference, trace ID). |

Extend with custom members for validation errors, trace IDs or correlation IDs. Never include stack traces, SQL, internal hostnames or personal data.

## Examples

### Cursor-based paginated collection response

```http
GET /orders?limit=20&cursor=eyJpZCI6MTAwfQ HTTP/1.1
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json
Link: <https://api.example.com/orders?cursor=eyJpZCI6MTIwfQ&limit=20>; rel="next"

{
  "data": [ { "id": "101", "status": "pending" }, "..." ],
  "pagination": {
    "nextCursor": "eyJpZCI6MTIwfQ",
    "limit": 20
  }
}
```

### RFC 9457 validation error response

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "One or more fields did not pass validation.",
  "instance": "/requests/abc-123",
  "errors": [
    { "field": "email", "message": "Must be a valid email address." },
    { "field": "quantity", "message": "Must be a positive integer." }
  ]
}
```

### Idempotency-Key on POST

```http
POST /payments HTTP/1.1
Content-Type: application/json
Idempotency-Key: 7f9e1234-aaaa-bbbb-cccc-deadbeef0001

{ "amount": 5000, "currency": "USD", "orderId": "ord-99" }

HTTP/1.1 201 Created
Location: /payments/pay-456
Idempotency-Key: 7f9e1234-aaaa-bbbb-cccc-deadbeef0001
```

A replay of the same key returns the same 201 and body without creating a duplicate payment.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using 200 for all responses including errors | Clients cannot distinguish success from failure without parsing the body | Use the semantically correct 4xx/5xx status code |
| Nesting URIs three or more levels deep (`/users/{id}/orders/{id}/lines/{id}`) | URIs become brittle; sub-resources become impossible to reference independently | Flatten to one level of nesting; use query parameters for joins |
| Returning arbitrary JSON for errors (not RFC 9457) | Clients must parse different error shapes per API | Always use `application/problem+json` with the five standard members |
| Offset pagination on large tables | `OFFSET 50000` forces the database to skip rows, causing slow scans | Use cursor-based pagination keyed on the sort column |
| Not sending `Location` header on 201 | Client must parse the body or re-fetch to find the new resource | Always include `Location: /resources/{id}` on 201 |
| Silently ignoring unknown query parameters | Hides typos; filters silently apply no filtering | Return 400 with a clear message listing unknown parameters |

## Checklist

- [ ] URIs are lowercase plural nouns with hyphens; no verbs in the path.
- [ ] HTTP method matches semantics from RFC 9110 (safe/idempotent table above).
- [ ] Every 201 response includes a `Location` header.
- [ ] Every error response is `application/problem+json` with `type`, `title`, `status`, `detail`.
- [ ] No stack traces, SQL or internal hostnames appear in error responses.
- [ ] Collections are paginated with an explicit limit; cursor-based for large datasets.
- [ ] POST actions that must not duplicate use an `Idempotency-Key` pattern.
- [ ] Unknown filter parameters return 400, not silent no-op.

## Verify with context7 and gh_grep

- **context7:** Not applicable for RFC-defined semantics. For pagination helpers or Idempotency-Key middleware, resolve the library in `package.json` and query context7 for its current API.
- **gh_grep:** Search `Idempotency-Key` to see real header usage; `application/problem+json` to find error response implementations; `rel="next"` to verify Link header pagination patterns; `cursor` with `nextCursor` for cursor field naming conventions.

## Sources

- RFC 9110 HTTP Semantics (June 2022): https://www.rfc-editor.org/rfc/rfc9110
- RFC 9457 Problem Details for HTTP APIs (September 2023): https://www.rfc-editor.org/rfc/rfc9457
- RFC 8288 Web Linking (`Link` header): https://www.rfc-editor.org/rfc/rfc8288
