# Authorization Security

Audit checks for access control, privilege escalation and tenancy isolation, based on OWASP Top 10:2025 A01 and ASVS 5.0.0 chapter V8; checked 2026-11-26. This file audits; implementing RBAC, ABAC and object checks is owned by `backend-engineering`.

## Contents

- Audit method: the authorization matrix
- Deny by default and central enforcement
- Object level and function level checks
- Privilege escalation paths
- Tenancy isolation
- Data-layer enforcement
- Authorization in background work, caches and files
- Testing authorization

## Guidance

### Audit method: the authorization matrix

Build a matrix before reading handlers. It turns "check access control" into a finite list.

1. Rows: every route, resolver, message consumer, scheduled job and admin tool in scope.
2. Columns: caller types (anonymous, user, user of another tenant, support, admin, service account).
3. Cells: expected result (allow, deny) from `docs/API-CONTRACTS.md`, the task requirements or the product rules. If the expected result is not written anywhere, record it as an open question; do not infer it from the code.
4. For each cell, find where the code decides. A cell with no decision point is a finding candidate. A decision point in the client only does not count.
5. Pay most attention to cells where deny is expected for an authenticated caller: those are the horizontal and vertical escalation cases.

### Deny by default and central enforcement

Access control works only in trusted server-side code. Check:

- **Default:** a new route with no policy declared is denied or flagged, not allowed. Look for router-level middleware or a policy registry rather than per-handler optional checks.
- **Single implementation:** checks live in one reusable layer (middleware, policy classes, decorators, a policy engine) and are reused, not hand-rolled per route. Repeated copies drift.
- **Ordering:** authorization runs before the handler's side effects, and before any expensive work or data load that could leak through timing or errors.
- **Failure behaviour:** if the policy check throws, times out or the policy store is unreachable, the request is denied (fails closed). This is A10:2025 territory; see [owasp-top-10.md](owasp-top-10.md).
- **No client trust:** hidden form fields, client-supplied role or tenant values, and UI-only gating are never the control.
- **CORS:** allowed origins are explicit; credentials are not combined with wildcards.

### Object level and function level checks

Both are needed. A role check alone lets any member read any object; an object check alone lets any member call an administrative function on their own objects.

- **Function level:** each operation states the roles or permissions it requires. Verify that every verb on a resource has its own decision (a route with a protected GET and an unprotected DELETE is common).
- **Object level:** each access to a specific record compares the caller to the record's owner, tenant, team or sharing rule. The decision uses data from the server (session or token verified server-side, and the record loaded from the store), never an owner id that came in the request.
- **Collections:** list, search, count, export and aggregate endpoints scope their results to what the caller may see. Aggregates and counts can leak existence of other tenants' data.
- **Relationships:** when a request references several objects (a comment on a post in a project), authorize the relationship, not only the child.

### Privilege escalation paths

Search for these specific routes to a higher privilege.

| Path | What to check |
|---|---|
| Self-assignment of role or permission fields | Role, admin, owner, plan and verified fields cannot be set through profile or generic update endpoints (see mass assignment in [api-security.md](api-security.md)) |
| Invitation and sharing flows | The inviter cannot grant more than they hold; invitation tokens are single-use and scoped |
| Impersonation and support tools | Reachable only by named roles, logged with the acting user and the target, time-limited, and not usable on higher-privileged accounts |
| Token and claim trust | Roles in a token are accepted only if the token is verified and the role cannot be stale after a change; privileged operations re-check server state |
| Parameter tampering | Identifiers for user, account, tenant, price or status in the request are not trusted as the actor or authority |
| Forced browsing | Admin or internal URLs are not merely unlinked; they enforce authorization |
| Alternate entry points | The same operation through another version, method, content type, batch call, GraphQL path or file import enforces the same rules |
| Default and seed accounts | Test or default administrators do not exist in production configuration |
| Insecure defaults on new resources | New objects are private by default; sharing is an explicit action |
| Race conditions on checks | Check and use happen in one transaction or with a lock where the permission can change mid-request |

Report the route, the missing decision and the impact (who can do what to whom). Do not write or publish step-by-step abuse instructions.

### Tenancy isolation

In a multi-tenant system a cross-tenant read or write is usually `high` or `critical`.

- **Tenant identity source:** the tenant comes from the verified session or token, never from a request field, header or path the caller controls. Where a request carries a tenant identifier (for example in a path), compare it to the verified one.
- **Query scoping:** every query on tenant data includes the tenant condition, preferably through one mechanism (a repository layer, an ORM scope or default filter, or database row-level security) so a developer cannot forget it. Count raw queries and report each that lacks the condition.
- **Shared resources:** caches, queues, search indexes, object-storage paths, file names, background jobs and websocket rooms include the tenant in their keys or namespaces.
- **Uniqueness and references:** unique constraints and foreign keys that span tenants can leak existence; check error messages and response differences.
- **Admin and reporting paths:** internal dashboards, analytics exports and data migrations often bypass the application's scoping; audit them as separate entry points.
- **Isolation model:** record which model is used (shared tables with a tenant column, schema per tenant, database per tenant). The choice sets which controls are available; it does not remove the need for the checks above. Isolation model design belongs to `system-architecture` and `database-engineering`.

### Data-layer enforcement

- If the project uses PostgreSQL row-level security, check that policies exist for every tenant table, that the application connects with a role that is not subject to bypass (superusers and roles with the bypass attribute ignore the policies, and table owners are exempt unless the table is set to force them; confirm the behaviour for the installed version with context7), and that policy conditions use a trusted session setting rather than a caller-controlled value.
- Database accounts follow least privilege: the application role has no schema-changing rights, migrations use a separate role, and each service has its own credentials. Detail on roles and access control audit is in [data-protection.md](data-protection.md).

### Authorization in background work, caches and files

- Jobs and consumers run with the identity and tenant of the request that created them, or a narrowly scoped service identity. A job that runs as an all-powerful account and takes the target from the message is a confused-deputy risk.
- Cached responses are keyed by the caller's authorization context; a response cached for one user must not be served to another.
- File and object downloads check the same permission as the record they belong to, and signed URLs are short-lived and scoped to one object.
- Webhooks and callbacks verify the sender before acting.

### Testing authorization

Require tests, not only code reading.

- A negative test for every deny cell in the matrix that is reachable by an authenticated caller.
- A test per tenant-scoped resource where tenant B asks for tenant A's object and gets no data.
- A test that a user cannot change their own role or ownership.
- A test that a new, unannotated route is denied or fails a startup check.
- Include authorization tests in unit and integration test suites so regressions are caught (OWASP A01 prevention guidance).

## Examples

### Authorization matrix (excerpt, filled in)

| Operation | anonymous | user (owner) | user (other, same tenant) | user (other tenant) | admin (own tenant) | Decision point found |
|---|---|---|---|---|---|---|
| `GET /projects/{id}` | deny | allow | allow if member | deny | allow | `projects.policy.canRead` |
| `DELETE /projects/{id}` | deny | allow | deny | deny | allow | none found: finding |
| `GET /admin/users` | deny | deny | deny | deny | allow | middleware `requireRole("admin")` |
| `POST /projects/{id}/share` | deny | allow (up to own role) | deny | deny | allow | role ceiling not enforced: finding |

### Function and object checks together (Express-style, illustrative)

```js
// Bad: role is checked, object is not
router.delete("/projects/:id", requireRole("member"), async (req, res) => {
  await db.project.delete({ where: { id: req.params.id } });
  res.sendStatus(204);
});

// Good: object scope and tenant are part of the operation
router.delete("/projects/:id", requireRole("member"), async (req, res) => {
  const result = await db.project.deleteMany({
    where: { id: req.params.id, tenantId: req.auth.tenantId, ownerId: req.auth.userId },
  });
  if (result.count === 0) return res.sendStatus(404);
  res.sendStatus(204);
});
```

### Finding: cross-tenant read

```
[critical] Invoice export returns other tenants' invoices
Location: src/reports/export.ts:73
Category: OWASP A01:2025, API1:2023
Evidence: the query filters by status and date; tenantId is read from the request query string, not from the session.
Impact: any authenticated user can read invoices of every tenant: customer names, amounts, addresses.
Likelihood: any authenticated user; one request. Exploitable now.
Remediation: take the tenant from the verified session; add the tenant condition in the shared repository function; add a cross-tenant negative test and review the other report routes for the same pattern.
Confidence: confirmed
```

### Tenant-scoped negative test (pseudocode)

```
as user of tenant B:
  GET /invoices/<id of tenant A invoice>   -> 404, body contains no invoice data
  GET /exports?tenantId=<tenant A>          -> uses tenant B or rejects; never returns tenant A data
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Checking role only | Any member reads or changes any object | Add an object check using server-side data |
| Taking tenant or owner from the request | Caller chooses whose data they get | Derive it from the verified session |
| Hiding admin links in the UI | The route is still reachable | Enforce authorization on the server route |
| Per-handler hand-written checks | One forgotten handler is a breach | Central policy layer with deny by default |
| Protecting GET but not other methods | State-changing verbs stay open | Decide per method and per route |
| Assuming the ORM scopes by tenant | Raw queries and new code skip it | Enforce scope in one layer; audit raw queries |
| Caching by URL only | One user's response served to another | Include authorization context in cache keys |
| Admin or analytics paths outside the matrix | They bypass application scoping | Add them as entry points and audit them |
| No negative tests | Regressions go unnoticed | Test every deny cell that matters |

## Checklist

- [ ] An authorization matrix exists for the scope, with expected results sourced from docs or requirements.
- [ ] Every cell has a server-side decision point, or a finding.
- [ ] New routes are denied or flagged by default.
- [ ] Authorization runs in one reusable layer before side effects, and fails closed.
- [ ] Both function-level and object-level checks exist for each operation.
- [ ] No role, owner or tenant value from the request is trusted as the actor.
- [ ] Collections, exports and aggregates are scoped to the caller.
- [ ] Tenant identity comes from the verified session, and every tenant query is scoped.
- [ ] Caches, queues, jobs and file paths include the tenant or authorization context.
- [ ] Database roles follow least privilege, and row-level security policies (if used) are enforced for the application role.
- [ ] Negative authorization and cross-tenant tests exist and run in the project's test command.

## Verify with context7 and gh_grep

- **context7:** for the framework and ORM versions in the lockfile, query: "route-level middleware and ordering", "global default filter or scope", "row level security policy (PostgreSQL) FORCE and bypass behaviour", "policy or permission library usage". For PostgreSQL, confirm how table owners and bypass roles interact with row-level security in the installed version.
- **gh_grep:** search literal code: `tenantId`, `requireRole(`, `deny by default`, `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, `where: { id, ownerId`. Compare how maintained multi-tenant projects enforce scoping in one place.

## Sources

- OWASP Top 10:2025, A01 Broken Access Control (description, prevention, test guidance, ASVS V8 reference): https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- OWASP Top 10:2025, A10 Mishandling of Exceptional Conditions (fail closed): https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Top 10 API Security Risks 2023 (API1 and API5): https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP ASVS repository (5.0.0, chapter V8 Authorization): https://github.com/OWASP/ASVS
