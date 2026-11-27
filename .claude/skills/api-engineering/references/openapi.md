# OpenAPI Documents

Covers writing, structuring and validating OpenAPI 3.1.x documents: JSON Schema 2020-12 alignment, component reuse via `$ref`, discriminator, webhooks, examples, security schemes and code generation; based on OpenAPI Specification 3.1.1 (released October 2024), checked 2026-11-26.

## Contents

- Document structure and version
- Schema Objects and JSON Schema 2020-12
- Component reuse with $ref
- Discriminator and polymorphism
- Webhooks
- Examples
- Security schemes
- Validation with Spectral
- Code generation

## Guidance

### Document structure and version

Always declare `openapi: 3.1.1`. The `info`, `paths` (or `webhooks`) and `components` sections are the backbone.

Minimum viable structure:

```yaml
openapi: 3.1.1
info:
  title: Order API
  version: "1.0.0"
  description: Manages customer orders.
paths:
  /orders:
    get:
      summary: List orders
      operationId: listOrders
      tags: [Orders]
      parameters:
        - $ref: '#/components/parameters/LimitParam'
        - $ref: '#/components/parameters/CursorParam'
      responses:
        '200':
          description: Paginated order list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderCollection'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorised'
components:
  schemas: {}
  responses: {}
  parameters: {}
  securitySchemes: {}
```

Always set `operationId` on every operation; code generators use it as the function name.

### Schema Objects and JSON Schema 2020-12

OpenAPI 3.1.x Schema Objects are a strict superset of JSON Schema Draft 2020-12.

Key differences from OpenAPI 3.0.x:

- **`type` as array:** `type: [string, "null"]` replaces the old `nullable: true` extension. Use this for optional fields that may be absent.
- **`$schema`:** Optional; set at the top-level Schema Object if you need to override the dialect.
- **`$ref` with siblings:** In 3.1.x, `$ref` can appear alongside `summary` and `description` in a Schema Object (not so in 3.0.x).
- **`exclusiveMinimum` / `exclusiveMaximum`:** Now take a numeric value directly (not a boolean as in 3.0.x).
- **`unevaluatedProperties`:** Supported natively from JSON Schema 2020-12; use to close schemas strictly.

```yaml
components:
  schemas:
    Order:
      type: object
      required: [id, status, createdAt]
      properties:
        id:
          type: string
          description: Opaque global order ID.
        status:
          type: string
          enum: [pending, processing, shipped, cancelled]
        note:
          type: [string, "null"]   # nullable via type array, not nullable:true
          maxLength: 500
        createdAt:
          type: string
          format: date-time
      unevaluatedProperties: false   # close the schema
```

### Component reuse with $ref

Move every schema, response, parameter, header and security scheme used in more than one place into `components/`. Reference with `$ref: '#/components/schemas/Order'`.

Conventions:
- `components/schemas/`: domain object schemas.
- `components/responses/`: standard error responses (`BadRequest`, `Unauthorised`, `Forbidden`, `NotFound`, `ProblemDetails`).
- `components/parameters/`: shared parameters (`LimitParam`, `CursorParam`, `CorrelationIdHeader`).
- `components/headers/`: shared response headers (`RateLimitRemaining`, `RetryAfter`).
- `components/securitySchemes/`: auth definitions.

A `ProblemDetails` schema component for RFC 9457:

```yaml
ProblemDetails:
  type: object
  required: [type, title, status]
  properties:
    type:
      type: string
      format: uri
    title:
      type: string
    status:
      type: integer
    detail:
      type: string
    instance:
      type: string
      format: uri-reference
  additionalProperties: true  # extension members are allowed
```

### Discriminator and polymorphism

Use `discriminator` with `oneOf` to model type-safe polymorphic payloads.

```yaml
components:
  schemas:
    PaymentMethod:
      oneOf:
        - $ref: '#/components/schemas/CardPayment'
        - $ref: '#/components/schemas/BankTransfer'
      discriminator:
        propertyName: type
        mapping:
          card: '#/components/schemas/CardPayment'
          bank_transfer: '#/components/schemas/BankTransfer'
    CardPayment:
      type: object
      required: [type, cardToken]
      properties:
        type:
          type: string
          const: card
        cardToken:
          type: string
    BankTransfer:
      type: object
      required: [type, iban]
      properties:
        type:
          type: string
          const: bank_transfer
        iban:
          type: string
```

The discriminator `propertyName` must exist in every sub-schema's `required` list.

### Webhooks

OpenAPI 3.1.x has first-class `webhooks` support (alongside `paths`). Use it for outbound event notifications.

```yaml
webhooks:
  orderShipped:
    post:
      summary: Sent when an order status changes to shipped.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrderShippedEvent'
      responses:
        '200':
          description: Webhook acknowledged.
```

### Examples

Prefer the `examples` object (keyed, multiple examples) over the singular `example` property.

```yaml
content:
  application/json:
    schema:
      $ref: '#/components/schemas/Order'
    examples:
      pending:
        summary: A newly created pending order
        value:
          id: "ord-001"
          status: pending
          createdAt: "2026-01-15T10:00:00Z"
      shipped:
        summary: An order that has shipped
        value:
          id: "ord-002"
          status: shipped
          createdAt: "2026-01-10T08:00:00Z"
```

Use realistic but non-sensitive placeholder values. Never include real email addresses, real payment tokens, real internal hostnames or real API keys.

### Security schemes

Define once in `components/securitySchemes/`; apply globally or per-operation.

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKey:
      type: apiKey
      in: header
      name: X-API-Key

security:
  - BearerAuth: []   # global default

paths:
  /webhooks/register:
    post:
      security:
        - ApiKey: []   # override for this operation
```

Scope requirements go in the `scopes` list for OAuth2/OIDC flows.

### Validation with Spectral

Run `spectral lint <openapi-file> --ruleset <ruleset>` in CI on every change to the OpenAPI document.

A minimal `.spectral.yaml`:

```yaml
extends:
  - spectral:oas
rules:
  operation-operationId: error
  operation-tags: warn
  no-$ref-siblings: off   # 3.1.x allows $ref + description siblings; disable this 3.0 rule
```

Treat errors as build failures. Treat warnings as review-required items; graduate them to errors over time.

### Code generation

Prefer **TypeSpec** for large APIs: author the schema in TypeSpec, emit OpenAPI as an artifact. For consuming generated clients, use **openapi-typescript** (TypeScript types from OpenAPI) or **openapi-generator** (multi-language full clients).

Pitfalls:
- Swagger Codegen 2.x targets OpenAPI 2.0 (Swagger); do not use it with OpenAPI 3.1.x documents.
- `openapi-generator` supports 3.1.x only from v7+; check the version in use.
- Code-generated clients must not be manually edited; regenerate from the spec on every API change.
- Validate the generated code compiles and passes type-checks in CI.

## Examples

### Reusable error response component

```yaml
components:
  responses:
    BadRequest:
      description: Malformed request.
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            missingField:
              summary: Required field absent
              value:
                type: "https://api.example.com/problems/validation-error"
                title: "Validation failed"
                status: 400
                detail: "The 'email' field is required."
```

### Operation with inline parameter and $ref response

```yaml
paths:
  /orders/{orderId}:
    get:
      operationId: getOrder
      summary: Retrieve a single order
      tags: [Orders]
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Order found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '404':
          $ref: '#/components/responses/NotFound'
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Declaring `openapi: 3.0.3` and using 3.1.x features (e.g. `type: [string, "null"]`) | Validators flag schema errors; generated clients produce wrong types | Match the version declaration to the features used |
| Using `nullable: true` in a 3.1.x document | `nullable` is not a JSON Schema 2020-12 keyword; validators ignore or flag it | Use `type: [string, "null"]` |
| Duplicating schema definitions inline across multiple operations | Changes require updating multiple places; schemas drift | Move all reused schemas to `components/schemas/` and use `$ref` |
| Skipping `operationId` on operations | Code generators produce unreadable auto-generated function names | Set a stable, unique `operationId` on every operation |
| Committing a document that fails `spectral lint` | Consumers cannot rely on the spec being valid; code generation fails | Make spectral lint a required CI check; fix errors before merging |
| Including real credentials or hostnames in examples | Security risk and policy violation | Use placeholder values (`<API_TOKEN>`, `api.example.com`) |

## Checklist

- [ ] `openapi: 3.1.1` (or the project's locked minor version) declared at the top.
- [ ] Every operation has a unique `operationId` and at least one `tag`.
- [ ] All reused schemas, responses, parameters and security schemes are in `components/`.
- [ ] No `nullable: true`; nullable fields use `type: [<type>, "null"]`.
- [ ] All error responses reference the `ProblemDetails` schema component.
- [ ] `spectral lint` exits 0 (no errors) in CI.
- [ ] Examples contain no real credentials, tokens, emails or internal hostnames.
- [ ] Code-generation output is regenerated from the spec (not manually edited).

## Verify with context7 and gh_grep

- **context7:** Resolve `@stoplight/spectral-cli`, `openapi-typescript` and (if used) `typespec` at the versions in `package.json`. Check: Spectral ruleset format (`extends`, `rules`), `openapi-typescript generate` CLI flags, TypeSpec `@route` and `@operationId` decorators.
- **gh_grep:** Search `openapi: 3.1` to find real OpenAPI 3.1.x documents; `$ref: '#/components/schemas'` for component reuse patterns; `spectral lint` in CI workflow YAML for integration examples; `discriminator:` with `propertyName:` for polymorphism wiring.

## Sources

- OpenAPI Specification 3.1.1 (October 2024): https://spec.openapis.org/oas/v3.1.1
- Spectral (OpenAPI linter): https://docs.stoplight.io/docs/spectral
- openapi-typescript: https://openapi-ts.dev/
- TypeSpec: https://typespec.io/
