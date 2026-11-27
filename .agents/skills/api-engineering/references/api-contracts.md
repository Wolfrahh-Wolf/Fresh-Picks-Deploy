# API Contracts

Covers the contract-first API design process, the ownership and structure of `docs/API-CONTRACTS.md`, consumer expectations, backwards compatibility rules and consumer-driven contract testing; aligned with `AGENTS.md` source-of-truth rules, checked 2026-11-26.

## Contents

- Contract-first process
- docs/API-CONTRACTS.md structure and ownership
- Consumer expectations and backwards compatibility
- Contract testing with Pact

## Guidance

### Contract-first process

Define the API interface before writing implementation code. This prevents the API from being shaped by implementation accidents and gives consumers something to code against in parallel.

**Sequence:**

1. **Architect** drafts the resource model, endpoint list, request/response schemas and error codes in `docs/API-CONTRACTS.md`. This is the single source of truth per `AGENTS.md`.
2. Write the matching OpenAPI 3.1.x document alongside (see `openapi.md`). The document and `docs/API-CONTRACTS.md` must agree; the OpenAPI document is the machine-readable form.
3. Share a snapshot with consumer teams. Collect blocking questions before any implementation is merged.
4. Consumer teams write Pact (or equivalent) contract tests against the agreed snapshot.
5. Implementer codes against the contract; not the other way around.
6. Reviewer and security-auditor check implementation against the contract, not against intuition.
7. If implementation reveals a design flaw, the architect updates the contract first (with user awareness if the change is breaking), then the implementation follows.

**Rule:** Code that disagrees with `docs/API-CONTRACTS.md` is a bug. Report it; never silently adjust the contract.

### docs/API-CONTRACTS.md structure and ownership

Owner: architect (per `AGENTS.md` source-of-truth table).

Recommended sections:

```markdown
# API Contracts

## Overview
One paragraph: purpose, versioning policy, base URL pattern.

## Conventions
Error format, authentication scheme, pagination pattern, rate-limiting headers.

## Resources

### <ResourceName>
- Base path: `/resource-names`
- Description: one sentence.

#### Endpoints
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | /resource-names | List (paginated) | Bearer |
| POST | /resource-names | Create | Bearer |
| GET | /resource-names/{id} | Retrieve | Bearer |
| PUT | /resource-names/{id} | Replace | Bearer |
| PATCH | /resource-names/{id} | Update fields | Bearer |
| DELETE | /resource-names/{id} | Remove | Bearer |

#### Request schema
...fields, types, required/optional, constraints...

#### Response schema
...fields, types, nullable rules, example...

#### Error responses
| Status | Type URI | When |
|---|---|---|
...

## Deprecation and sunset log
| Endpoint or field | Deprecated | Sunset date | Replacement |
|---|---|---|---|
```

Whenever a field or endpoint is added, changed or removed, update this file and `CHANGELOG.md` in the same commit.

### Consumer expectations and backwards compatibility

Additive changes are non-breaking. Everything else requires either a new version or a planned migration.

**Non-breaking (safe to ship without a version bump):**

- Adding a new optional field to a response.
- Adding a new optional query parameter.
- Adding a new endpoint.
- Making a previously required request field optional.
- Adding a new enum value to a request field (consumers must tolerate unknown values).

**Breaking (requires a version increment or migration plan):**

- Removing or renaming a field, endpoint or parameter.
- Changing a field's type (e.g. `string` → `integer`).
- Changing a field from optional to required.
- Removing an enum value from a response field consumers may have stored.
- Changing authentication scheme or required headers.
- Changing pagination shape (e.g. `nextCursor` → `next_cursor`).

**Tolerant-reader principle:** consumer implementations must ignore unknown fields in responses. This allows the producer to add fields without breaking consumers. Enforce this in contract tests.

### Contract testing with Pact

Consumer-driven contract tests invert the usual testing direction: the consumer defines what it expects; the provider proves it delivers that.

**How it works:**

1. Consumer team writes a Pact test that specifies:
   - The request it will send (method, path, headers, body shape).
   - The minimum response it needs (status, required fields, types — not exact values).
2. The Pact framework generates a contract file (`.json`).
3. Provider team runs the contract file against the real API (or a test instance) using the Pact provider verifier.
4. Both sides publish results to Pact Broker (or Pactflow) for `can-i-deploy` checks.

**Key rules:**

- Consumers must not over-specify (exact string values fail on irrelevant changes); match types, not values.
- Providers must not change contracts without first passing all existing consumer contracts.
- Run Pact verification in CI on every provider PR before merge.

```javascript
// Consumer test (Pact JS v12+)
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
const { like, eachLike } = MatchersV3;

const provider = new PactV3({
  consumer: 'OrderUI',
  provider: 'OrderAPI',
  dir: './pacts',
  spec: 3,
});

describe('GET /orders', () => {
  it('returns a list of orders', async () => {
    await provider
      .uponReceiving('a request for orders')
      .withRequest({ method: 'GET', path: '/orders', query: { limit: '20' } })
      .willRespondWith({
        status: 200,
        body: {
          data: eachLike({ id: like('ord-1'), status: like('pending') }),
          pagination: { nextCursor: like('eyJ...') },
        },
      })
      .executeTest(async (mockServer) => {
        const result = await fetchOrders(mockServer.url, { limit: 20 });
        expect(result.data).toHaveLength(1);
      });
  });
});
```

## Examples

### Minimal docs/API-CONTRACTS.md entry

```markdown
### Order

- Base path: `/orders`
- Authentication: Bearer token (JWT, OAuth 2.0 `orders:read` and `orders:write` scopes).

#### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /orders | List orders (cursor-paginated, max 100) |
| POST | /orders | Create an order; requires `Idempotency-Key` header |
| GET | /orders/{orderId} | Retrieve an order by ID |
| PATCH | /orders/{orderId} | Update status or shipping address |
| DELETE | /orders/{orderId} | Cancel an order (soft delete) |

#### Response schema (Order object)

| Field | Type | Required | Notes |
|---|---|---|---|
| id | string | Yes | Global opaque ID |
| status | enum | Yes | `pending`, `processing`, `shipped`, `cancelled` |
| createdAt | string (ISO 8601) | Yes | |
| updatedAt | string (ISO 8601) | Yes | |
| lineItems | array | Yes | See LineItem schema |

#### Error responses

| Status | Type URI | When |
|---|---|---|
| 400 | /problems/validation-error | Invalid request body |
| 401 | /problems/unauthorised | Missing or expired token |
| 403 | /problems/forbidden | Insufficient scope |
| 404 | /problems/not-found | Order does not exist |
| 409 | /problems/conflict | Duplicate Idempotency-Key with different payload |
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Writing the API contract after the implementation | Implementation details leak into the design; consumers cannot develop in parallel | Define the contract (and OpenAPI doc) before writing any implementation code |
| Letting the implementer update `docs/API-CONTRACTS.md` unilaterally | Contract changes are not reviewed; consumers are broken silently | Only the architect updates `docs/API-CONTRACTS.md`; breaking changes require user awareness |
| Over-specifying Pact consumer expectations (exact values) | Tests fail on irrelevant response changes (e.g. updated copy in `title`) | Match types and structure, not literal values |
| Skipping Pact verification on provider PRs | Breaking contract changes merge undetected; consumer CI fails later | Run `pact:verify` in provider CI on every PR; block merge on failure |
| Adding new required fields to a response without warning | Consumers crash on null values they didn't anticipate | Additive changes only; discuss with consumers before making previously optional fields required |

## Checklist

- [ ] `docs/API-CONTRACTS.md` exists, is owned by the architect and covers all endpoints being changed.
- [ ] The OpenAPI document agrees with `docs/API-CONTRACTS.md` (no silent divergence).
- [ ] All consumer teams were consulted before any breaking change was finalised.
- [ ] Pact consumer tests exist for each consumer of the changed endpoint.
- [ ] Pact provider verification runs in CI and blocks merge on failure.
- [ ] `CHANGELOG.md` updated for every public API change.
- [ ] Deprecation and sunset log updated for any field or endpoint being retired.

## Verify with context7 and gh_grep

- **context7:** Resolve `@pact-foundation/pact` at the version in `package.json`. Check: `PactV3` constructor options, `MatchersV3` exports (`like`, `eachLike`, `regex`, `integer`), provider verifier CLI flags (`--provider-base-url`, `--pact-broker-url`).
- **gh_grep:** Search `PactV3` with `uponReceiving` for consumer test patterns; `pact:verify` in `package.json` scripts for provider test wiring; `docs/API-CONTRACTS.md` for real project contract file examples.

## Sources

- Pact Foundation documentation: https://docs.pact.io/
- Pact JS (v12+) on GitHub: https://github.com/pact-foundation/pact-js
- AGENTS.md source-of-truth table (see project `AGENTS.md`)
