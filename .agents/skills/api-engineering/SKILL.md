---
name: api-engineering
description: "Use when designing, documenting or changing APIs: REST, GraphQL, OpenAPI contracts, versioning, validation, pagination and rate limiting."
---

# API Engineering

Guides the full lifecycle of API interfaces: resource modelling, contract authorship, schema validation, versioning strategy and traffic controls. Depth lives in the references below; this file routes each agent to the right one.

## When to use

- Designing a new REST endpoint or GraphQL type for the first time.
- Reviewing a proposed API change for breaking-change impact.
- Writing or updating `docs/API-CONTRACTS.md` or an OpenAPI document.
- Deciding a pagination, versioning, rate-limiting or validation strategy.
- Auditing an API surface for security-auditor review.

## Do not use for

- Server implementation details (middleware, database queries, caching): load `backend-engineering`.
- Writing human-facing API guides, README or CHANGELOG: load `technical-documentation`.
- API attack testing (fuzzing, injection, auth bypass probing): load `security-engineering`.

## Research: context7 and gh_grep

- You MUST consult **context7** before writing or reviewing any OpenAPI document, Zod schema, Pact test or Spectral ruleset. Check the version locked in `package.json` or `pyproject.toml`. Useful queries: `openapi-typescript codegen options`, `zod parse safeParse error format`, `@pact-foundation/pact consumer test setup`, `@stoplight/spectral-cli run rules`, `graphql-js schema definition`.
- You MUST search **gh_grep** when a pattern or header format is unfamiliar or documentation is ambiguous. Useful searches: `RateLimit-Remaining` (header usage in real APIs), `application/problem+json` (error response format), `paths:` with `$ref:` (OpenAPI component reuse), `DataLoader` with `batch` function (N+1 mitigation), `Idempotency-Key` (POST safety patterns).
- RFC semantics (safe/idempotent methods, status codes, problem details format) need neither tool — use the official RFC text and mark any claim from memory as **unverified**.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/rest.md](references/rest.md) | Designing or reviewing REST resources, methods, status codes, pagination or error responses |
| [references/graphql.md](references/graphql.md) | Working on a GraphQL schema, resolver, N+1 fix, pagination or query cost limits |
| [references/api-contracts.md](references/api-contracts.md) | Writing or updating `docs/API-CONTRACTS.md`, running consumer-driven contract tests, or assessing compatibility |
| [references/openapi.md](references/openapi.md) | Authoring or validating an OpenAPI 3.1.x document, using `$ref` reuse, or setting up code generation |
| [references/versioning.md](references/versioning.md) | Deciding how to evolve an existing API, assessing breaking changes, or setting deprecation headers |
| [references/validation.md](references/validation.md) | Adding input validation at a trust boundary, choosing a schema library or coercion strategy |
| [references/rate-limiting.md](references/rate-limiting.md) | Implementing or reviewing rate-limit algorithms, headers or distributed counters |

## Workflow

1. **Classify the work by role** before opening any reference:
   - *Architect*: open `api-contracts.md` first; design resource model and document in `docs/API-CONTRACTS.md`. Check `openapi.md` to write the OpenAPI document and validate with Spectral. Load `versioning.md` if the change touches an existing endpoint.
   - *Implementer*: open the reference for the specific concern (REST, GraphQL, validation, rate-limiting). Implement against the contract already in `docs/API-CONTRACTS.md`. Do not silently change the contract.
   - *Reviewer*: open `versioning.md` to check breaking-change impact, `rest.md` or `graphql.md` for correctness, `openapi.md` to verify the document is valid. Flag any contract drift to the architect.
   - *Security-auditor*: check `validation.md` (inbound allow-list enforcement), `rate-limiting.md` (limits applied, headers present), `rest.md` (auth status codes 401/403, no stack traces in errors). For attack testing, load `security-engineering`.

2. **Contract first**: the architect defines the interface in `docs/API-CONTRACTS.md` before implementation begins (see `api-contracts.md`).

3. **Research the locked versions**: query context7 for the exact version of any library in use; run gh_grep for real usage patterns.

4. **Write or validate the OpenAPI document**: use OpenAPI 3.1.1; run `spectral lint` with the project ruleset before committing (see `openapi.md`).

5. **Implement**: validate every inbound payload at the boundary using the project's schema library (Zod, Pydantic, or JSON Schema); never trust client-supplied types (see `validation.md`).

6. **Apply rate limits**: every public or partner-facing endpoint must have a limit; expose `RateLimit-Remaining` and `Retry-After` on 429 (see `rate-limiting.md`).

7. **Versioning check**: before merging, run the breaking-change checklist in `versioning.md`. Add `Deprecation` and `Sunset` headers if retiring a field or endpoint.

8. **Contract tests**: run Pact (or equivalent) consumer-driven tests in CI before shipping (see `api-contracts.md`).

## Standards

- Every REST endpoint maps to a named resource; URIs are lowercase nouns with hyphens (`/order-items`), not verbs.
- Use HTTP methods per RFC 9110: GET is safe and idempotent; DELETE and PUT are idempotent; POST is neither.
- Status codes must be semantically correct: 201 for created resources (with `Location` header), 204 for no-body success, 400 for malformed requests, 422 for valid-syntax but invalid-semantic payloads, 401 for missing/invalid auth, 403 for insufficient permissions, 429 for rate-limit exceeded.
- All error responses use `application/problem+json` (RFC 9457) with at minimum `type`, `title`, `status` and `detail`; never return a stack trace.
- Paginate any collection that can grow: cursor-based for large or frequently updated datasets; include `Link` header or inline cursor fields.
- Filter and sort via query parameters; never encode mutable state in the path.
- API changes default to additive-only; any removal or rename of a field, endpoint or enum value is a breaking change requiring a version increment.
- GraphQL schemas use Relay cursor-based connections for lists; solve N+1 with DataLoader, never with per-resolver fetches.
- OpenAPI documents must pass `spectral lint` with zero errors; reuse types via `$ref` to `components/`.
- Validate every inbound payload against an allow-listed schema at the trust boundary; never use a deny-list.
- Rate limits must be applied before any database or external call; return 429 with `Retry-After`.
- No real credentials, hostnames, internal IPs or personal data in any OpenAPI example, schema or contract test fixture.

## Verification

- [ ] `spectral lint <openapi-file>` exits 0 with the project ruleset.
- [ ] All inbound endpoints have schema validation; test with a deliberately malformed payload and confirm 400/422 with `application/problem+json`.
- [ ] All collections are paginated; test cursor continuity across pages.
- [ ] Rate limit headers (`RateLimit-Remaining`, `Retry-After`) appear on 429 responses.
- [ ] No field or endpoint removed without a matching `Deprecation` and `Sunset` header in the previous release.
- [ ] `docs/API-CONTRACTS.md` reflects the final interface and is owned by the architect.
- [ ] Consumer-driven contract tests pass in CI.
- [ ] `gh_grep` and context7 queries are recorded in the Research section of the task report.

## Output

Report under **Evidence**: spectral lint output, test results for validation and pagination, rate-limit header samples from a curl or test run. Report under **Research**: context7 versions queried, gh_grep patterns searched. Report under **Docs impact**: `docs/API-CONTRACTS.md` (architect), `docs/ARCHITECTURE.md` if the API surface changed structurally, `CHANGELOG.md` (implementer) for any public API change.
