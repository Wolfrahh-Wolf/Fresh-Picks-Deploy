# Input Validation

Covers schema validation at inbound trust boundaries, allow-list field enforcement, type coercion rules, error response format and common validation libraries; checked against Zod 3.x, Pydantic 2.x and JSON Schema Draft 2020-12 documentation on 2026-11-26.

## Contents

- Trust boundaries and where to validate
- Allow-list validation vs. deny-list filtering
- Type coercion rules
- Error response format
- Validation libraries

## Guidance

### Trust boundaries and where to validate

Validate every inbound payload at the point it enters your system from an untrusted source. "Inbound" means any data whose origin you do not control.

**Always validate:**

- HTTP request bodies (JSON, multipart).
- HTTP query parameters and path segments.
- HTTP headers used as application inputs (`Idempotency-Key`, `X-Tenant-Id`).
- Webhook payloads arriving from external services.
- Messages consumed from a queue or event stream.
- Configuration values loaded from environment variables at startup (fail fast on bad config).

**Do not validate inbound at the outbound boundary.** Response schemas are enforced by contract tests (see `api-contracts.md`), not by runtime output validation — which adds latency and masks bugs.

**Never trust client-supplied types.** If the declared JSON type is `number`, coerce and range-check it; do not pass raw user input as a number to a SQL query or business logic.

### Allow-list validation vs. deny-list filtering

**Allow-list:** explicitly enumerate every field, type, format and range the system accepts. Reject anything that does not appear on the list.

**Deny-list:** enumerate known-bad values and reject them. Everything else passes.

**Always prefer allow-list validation.** A deny-list misses unknown-bad inputs; an allow-list rejects them by default. Apply allow-lists at:

- Object schemas (use `additionalProperties: false` or Zod's `.strict()` to reject unknown fields).
- String formats (`enum`, `pattern`, `format: email`).
- Numeric ranges (`minimum`, `maximum`, `multipleOf`).
- Array lengths (`minItems`, `maxItems`).
- String lengths (`minLength`, `maxLength`).

Unknown fields in the request body must be **rejected with 400**, not silently stripped. Silently stripping hides integration bugs; rejecting reveals them immediately.

### Type coercion rules

Apply coercion only at the system boundary (the HTTP layer), never in business logic.

**Allowed coercions:**

- Incoming query parameter string `"42"` → integer `42` (parse explicitly, do not cast blindly).
- Incoming string `"true"` / `"false"` → boolean.
- Incoming ISO 8601 string → `Date` object.

**Forbidden coercions:**

- Never coerce an empty string to `null` or `0` silently; return a validation error.
- Never truncate strings that exceed `maxLength`; return a validation error.
- Never accept `NaN`, `Infinity` or `-Infinity` as numeric values from external input.

After coercion at the boundary, treat the validated value as a trusted type for all downstream code. Business logic must never receive raw, unvalidated input.

### Error response format

Validation errors must use `application/problem+json` (RFC 9457) with status 400 or 422. Include field-level details so the client can display inline errors.

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "2 fields failed validation.",
  "instance": "/requests/abc-xyz",
  "errors": [
    {
      "field": "quantity",
      "path": "$.quantity",
      "message": "Must be a positive integer no greater than 10 000."
    },
    {
      "field": "email",
      "path": "$.customer.email",
      "message": "Must be a valid email address."
    }
  ]
}
```

Requirements:
- Include the JSON Pointer path (`$.field.subfield`) or dot notation path so clients locate the error.
- Messages must be human-readable and safe; no stack traces, SQL fragments or internal paths.
- If multiple fields fail, report all errors in a single response — do not stop at the first failure (clients can then fix all issues at once).

### Validation libraries

Use the project's established library. If none is set, prefer:

**TypeScript / Node.js — Zod 3.x:**

```typescript
import { z } from 'zod';

const CreateOrderSchema = z.object({
  customerId: z.string().uuid(),
  lineItems: z.array(
    z.object({
      productId: z.string().uuid(),
      quantity: z.int().positive().max(10_000),
    })
  ).min(1).max(100),
  note: z.string().max(500).nullable().optional(),
}).strict();  // reject unknown fields

type CreateOrderInput = z.infer<typeof CreateOrderSchema>;

function parseCreateOrder(raw: unknown): CreateOrderInput {
  const result = CreateOrderSchema.safeParse(raw);
  if (!result.success) {
    // Map Zod errors to the problem+json format
    throw new ValidationError(result.error.issues);
  }
  return result.data;
}
```

Use `safeParse` (not `parse`) so you can format the error before it propagates. Never let Zod `ZodError` escape to the global error handler unformatted.

**Python — Pydantic 2.x:**

```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional

class LineItem(BaseModel):
    model_config = {"extra": "forbid"}  # reject unknown fields

    product_id: UUID4
    quantity: int = Field(gt=0, le=10_000)

class CreateOrderInput(BaseModel):
    model_config = {"extra": "forbid"}

    customer_id: UUID4
    line_items: list[LineItem] = Field(min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)
```

Call `.model_validate(data)` and catch `ValidationError` to format errors for the response.

**JSON Schema (language-agnostic):**

Use `ajv` (Node.js) or `jsonschema` (Python) with Draft 2020-12. Set `additionalProperties: false` and `unevaluatedProperties: false` on all object schemas. Pre-compile schemas at startup; do not compile on each request.

## Examples

### Zod schema with custom error mapping

```typescript
import { z, ZodIssue } from 'zod';

function zodIssuesToErrors(issues: ZodIssue[]) {
  return issues.map(issue => ({
    field: issue.path[issue.path.length - 1],
    path: '$.' + issue.path.join('.'),
    message: issue.message,
  }));
}

function parseBody<T>(schema: z.ZodSchema<T>, raw: unknown): T {
  const result = schema.safeParse(raw);
  if (!result.success) {
    throw {
      type: 'https://api.example.com/problems/validation-error',
      title: 'Validation failed',
      status: 422,
      detail: `${result.error.issues.length} field(s) failed validation.`,
      errors: zodIssuesToErrors(result.error.issues),
    };
  }
  return result.data;
}
```

### Query parameter validation

```typescript
const ListOrdersQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(20),
  cursor: z.string().base64().optional(),
  status: z.enum(['pending', 'processing', 'shipped', 'cancelled']).optional(),
});

// In route handler:
const query = parseBody(ListOrdersQuerySchema, req.query);
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Validating only in the UI; trusting backend receives clean data | Any direct API call bypasses frontend validation; backend processes arbitrary input | Validate every inbound payload at the server trust boundary regardless of client |
| Using a deny-list to block malicious values | Unknown-bad values slip through; the list is never complete | Use allow-list schemas; reject everything not explicitly permitted |
| Silently stripping unknown fields instead of rejecting them | Hides client integration bugs and can mask injection attempts | Return 400 with a list of unexpected fields |
| Stopping at the first validation error | Client must submit the form multiple times to find all errors | Collect and return all validation errors in a single response |
| Letting raw `ZodError` or `ValidationError` reach the global error handler | Stack traces or internal field names leak to the client | Catch validation errors in the route layer and map to `application/problem+json` before responding |
| Coercing `""` (empty string) to `null` silently | Required-field checks pass; null propagates into business logic | Treat empty string as a validation error; never coerce to null silently |

## Checklist

- [ ] Every endpoint's body, query parameters and relevant headers are validated against a schema.
- [ ] Schemas use allow-lists: `strict()` / `additionalProperties: false` / `extra: "forbid"`.
- [ ] No unknown fields are silently stripped; they produce a 400 error.
- [ ] All validation errors are mapped to `application/problem+json` with field paths and messages.
- [ ] Validation errors are collected and returned in full (not stop-at-first).
- [ ] No stack traces, SQL or internal paths appear in validation error responses.
- [ ] Schemas are pre-compiled at startup (AJV); not compiled per request.
- [ ] Business logic receives only post-validated, typed values.

## Verify with context7 and gh_grep

- **context7:** Resolve `zod` or `pydantic` at the project's locked version. Check: Zod `z.object().strict()`, `safeParse`, `z.coerce.*` coercion helpers; Pydantic `model_config = {"extra": "forbid"}`, `model_validate`, `ValidationError.errors()` structure.
- **gh_grep:** Search `safeParse` with `issues` for Zod error-mapping patterns; `model_validate` with `ValidationError` for Pydantic patterns; `additionalProperties: false` in OpenAPI schemas; `application/problem+json` with `errors:` array for validation error response format.

## Sources

- Zod documentation (v3): https://zod.dev/
- Pydantic documentation (v2): https://docs.pydantic.dev/latest/
- JSON Schema Draft 2020-12: https://json-schema.org/specification
- RFC 9457 Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457
