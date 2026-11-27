# API Security

Audit checks for object and function level authorization, mass assignment and data exposure, resource limits, sensitive business flows, inventory and unsafe consumption of third-party APIs, organised around the OWASP API Security Top 10:2023 (the current edition when checked on 2026-11-26) and ASVS 5.0.0 chapter V4.

## Contents

- How to audit an API
- API1 Broken Object Level Authorization
- API5 Broken Function Level Authorization
- API3 Broken Object Property Level Authorization (mass assignment and excess exposure)
- API4 Unrestricted Resource Consumption
- API6 Unrestricted Access to Sensitive Business Flows
- API2 Broken Authentication, API7 SSRF and API8 Security Misconfiguration
- API9 Improper Inventory Management
- API10 Unsafe Consumption of APIs
- GraphQL specifics

## Guidance

### How to audit an API

1. Build the endpoint inventory from the code (route registrations, resolvers, generated clients), then compare it with `docs/API-CONTRACTS.md` and any OpenAPI document. Differences are findings or questions.
2. For each endpoint record: method and path, authentication required, roles allowed, object the identifier refers to, fields accepted, fields returned, limits applied.
3. Check each row against the ten risks below. Use the same row to write negative test cases.
4. Rate by likelihood and impact; BOLA and BFLA on data of other users or tenants are usually `high` or `critical`.

Contract design, versioning and rate-limit design belong to `api-engineering`. This file covers auditing for the absence of the control.

### API1 Broken Object Level Authorization

Any endpoint that takes an object identifier (path, query, body, header, nested in a batch) must verify that the caller may access that specific object.

Audit questions:
- For every handler that loads by id, where is the ownership or permission check, and does it run before the data is returned or changed?
- Is the check in a shared function or policy layer, or repeated by hand (and therefore easy to miss)?
- Do list, search, export, bulk and nested-resource endpoints filter by the caller's scope, not only single-object reads?
- Are identifiers inside request bodies and batch arrays checked, not only the one in the URL?
- Does the check use an identifier from the verified session or token, never one supplied by the client for "who am I"?

Unpredictable identifiers (UUIDs) reduce guessing but are not an authorization control; report their use as the only control.

### API5 Broken Function Level Authorization

Administrative or privileged functions reachable by lower roles.

Audit questions:
- Does every route state the required role or permission, and does the code enforce it server-side?
- Are administrative routes separated by path or router so the group is protected as a unit, with deny by default for new routes?
- Does the same operation exposed through a different method, version, route alias or GraphQL mutation have the same check?
- Are internal or support endpoints reachable from the public interface?

### API3 Broken Object Property Level Authorization (mass assignment and excess exposure)

This category merges two older risks: exposing properties the caller should not see, and accepting properties the caller should not set.

Mass assignment audit:
- Is the request body bound directly to a model or passed whole into a create or update call?
- Could a caller set role, owner, tenant, price, status, verification flag, or internal fields?
- Is there an explicit allowlist of writable fields per operation?

Excess exposure audit:
- Does the response serialise the whole stored object (including hashes, internal ids, flags, other users' data)?
- Are responses shaped by an explicit output schema per role?
- Do error, log and debug responses reveal object internals?

Defence: separate input and output schemas per operation, allowlisted fields, reject unknown fields, deny by default for sensitive properties, and field-level checks where roles differ.

### API4 Unrestricted Resource Consumption

Every request costs CPU, memory, bandwidth, storage, database time and sometimes money (email, SMS, third-party calls).

Audit questions:
- Maximum body size, upload size, array length, nesting depth and string length per endpoint?
- Pagination with an enforced maximum page size, and a cap on total offset or cursor depth?
- Timeouts on every inbound handler and every outbound call?
- Limits on expensive operations (export, report, search, image processing) and on concurrency per caller?
- Limits on calls that trigger paid third-party actions or notifications?
- Rate limits per caller and per source, with a defined response?
- Batch endpoints and GraphQL: cap on operations per request?

A missing limit is a finding when you can name the resource that is exhausted and the caller who can exhaust it. State the unbounded quantity.

### API6 Unrestricted Access to Sensitive Business Flows

Flows such as sign-up, purchase, ticket booking, commenting, referral credit or password reset are harmed when used in excess by automation, even with no implementation bug.

Audit questions: which flows have business value that excess use destroys? What stops bulk use (per-account and per-device limits, step-up verification, cooldowns, inventory caps, monitoring of unusual volume)? This is a design question; if there is no threat model entry, add one (see [threat-modelling.md](threat-modelling.md)).

### API2 Broken Authentication, API7 SSRF and API8 Security Misconfiguration

- **API2:** check token handling, session rules and recovery flows in [authentication-security.md](authentication-security.md). Add API-specific checks: every endpoint requires authentication unless listed as public in the contract; authentication endpoints have throttles; keys passed in query strings are reported because URLs are logged.
- **API7:** any endpoint that fetches a user-supplied URI; see SSRF in [application-security.md](application-security.md).
- **API8:** check CORS (explicit origins), allowed methods, error detail, default credentials, TLS on all hops, security headers, missing hardening of the supporting systems, and debug endpoints; see [infrastructure-security.md](infrastructure-security.md).

### API9 Improper Inventory Management

APIs expose more endpoints than classic web apps, so stale or undocumented ones accumulate.

Audit questions:
- Does the deployed route set equal the documented set? Look for shadow endpoints (undocumented) and zombie endpoints (old versions still served).
- Are older API versions retired, or kept with the same security fixes?
- Are non-production hosts, test data and debug endpoints reachable from the internet?
- Is there an owner and a data classification recorded per API and per integration?
- Which third-party APIs does the service call, and what data does each receive?

Record the inventory as a table in the audit report (see Examples).

### API10 Unsafe Consumption of APIs

Developers often trust data from a third-party API more than user input. An attacker can aim at the integration instead of at the target.

Audit questions:
- Are third-party responses validated against a schema and size limit before use, the same standard as user input?
- Is TLS validated on every call, with timeouts and a cap on redirects followed?
- Are redirects from the third party followed blindly?
- Is the third party's data ever placed into queries, commands, templates or file paths without the sink controls from [application-security.md](application-security.md)?
- If the third party is compromised or returns errors, does the service fail closed?
- Are credentials for the integration scoped to the minimum and stored per [secrets-management.md](secrets-management.md)?

### GraphQL specifics

- Authorization must run in resolvers or a policy layer for each field that returns protected data, not only at the top-level query. A single schema often exposes the same object through many paths.
- Limit query depth, complexity or cost, and the number of aliased or batched operations per request.
- Disable introspection and verbose errors in production unless the API is intentionally public.
- Check mutation access separately from query access.
- Apply pagination limits to every list field.

## Examples

### Endpoint audit row (filled in)

| Endpoint | Auth | Role | Object | Accepts | Returns | Limits | Result |
|---|---|---|---|---|---|---|---|
| `GET /invoices/{id}` | session | user | invoice by id | none | invoice | none needed | API1 finding: no ownership check |
| `PATCH /users/{id}` | session | user | user by id | whole body | whole user | none | API1 and API3 findings |
| `POST /exports` | session | user | none | filter | job id | no concurrency cap | API4 finding (medium) |
| `GET /admin/stats` | session | admin only in contract | none | none | counts | none | API5 finding: route lacks role check |

### Object level authorization (Prisma)

```js
// Bad: any logged-in user can read any invoice by changing the id
const invoice = await prisma.invoice.findUnique({ where: { id } });

// Good: ownership is part of the query; a foreign id behaves like a missing one
const invoice = await prisma.invoice.findFirst({ where: { id, ownerId: user.id } });
if (!invoice) return res.sendStatus(404);
```

### Mass assignment (Prisma)

```js
// Bad: the body decides which columns change, including role or ownerId
await prisma.user.update({ where: { id: user.id }, data: req.body });

// Good: an explicit allowlist of writable fields
const { displayName, locale } = req.body;
await prisma.user.update({ where: { id: user.id }, data: { displayName, locale } });
```

### Finding: mass assignment

```
[high] Profile update accepts role field
Location: src/routes/users.ts:58
Category: OWASP API3:2023, A01:2025
Evidence: PATCH /users/:id passes req.body to the update call; the User model has a role column; no field allowlist exists.
Impact: a normal user can set their own role and gain administrator functions.
Likelihood: any authenticated user; one request.
Remediation: allowlist writable fields as in the example; reject unknown fields; add a test that sending role is ignored or rejected.
Confidence: confirmed
```

### Negative tests to require

```
- user A requests user B's invoice id            -> 404 (or 403), no data
- user with role "member" calls an admin route   -> 403
- PATCH with an extra "role" field               -> field ignored or request rejected, role unchanged
- list endpoint with page size far above maximum -> clamped or rejected
- request body one byte over the size limit      -> 413
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Checking the role but not the object | Any user of that role reads every object | Require both function-level and object-level checks |
| Authorizing only the URL identifier in a batch or nested request | Other identifiers in the body bypass the check | Check every identifier the request touches |
| Relying on UUIDs as access control | Identifiers leak in logs, links and responses | Authorize every access; treat unguessability as a bonus |
| Serialising the stored model straight to the response | Leaks internal and sensitive fields | Use explicit per-role output schemas |
| Binding bodies to models | Callers set fields they should not | Allowlist writable fields per operation |
| Fixing only the documented API | Shadow and old versions stay exposed | Compare deployed routes with the contract and retire versions |
| Trusting third-party responses | A compromised partner becomes an attack path | Validate and size-limit them like user input |
| Rating missing limits as "best practice" | Real outages and bills are missed | Name the resource, the caller and the effect |

## Checklist

- [ ] The endpoint inventory from code was compared with the contract and OpenAPI document.
- [ ] Every id-taking handler has an object-level check before data is returned or changed.
- [ ] Every privileged route enforces its role server-side, and new routes deny by default.
- [ ] No request body is bound whole to a model, and writable fields are allowlisted.
- [ ] Responses use explicit output shapes without internal or sensitive fields.
- [ ] Size, page, depth, timeout and concurrency limits exist or the gap is reported.
- [ ] Sensitive business flows have abuse limits or a recorded design decision.
- [ ] Non-production hosts, debug routes and retired versions are not reachable.
- [ ] Third-party responses are validated and bounded before use.
- [ ] GraphQL depth or cost limits and field-level authorization were checked where GraphQL is used.

## Verify with context7 and gh_grep

- **context7:** for the project's web framework, query: "request body validation and unknown fields", "route-level middleware ordering", "request size limit", "CORS options". For the ORM: "select specific fields", "where with composite conditions", "raw query parameters". For GraphQL servers: "query depth limit", "disable introspection", "field-level authorization".
- **gh_grep:** search literal code: `data: req.body`, `Object.assign(`, `...req.body`, `findUnique({ where: { id`, `introspection:`, `depthLimit(`, `limits: {`. Review how maintained projects scope queries by owner or tenant and apply response shaping.

## Sources

- OWASP Top 10 API Security Risks 2023 (all ten risks, descriptions read): https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP Top 10:2025, A01 Broken Access Control (BOLA-type failures, parameter tampering, CORS, rate limits): https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- OWASP ASVS repository (chapter structure; V4 API and Web Service in 5.0.0): https://github.com/OWASP/ASVS
