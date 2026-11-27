# Authorization

Covers implementing RBAC, ABAC, object-level checks, deny-by-default and multi-tenant isolation in Node.js and Python backends; patterns current as of 2026-11-26. Auditing these implementations for security vulnerabilities belongs to `security-engineering`.

## Contents

- Deny-by-default and separation of concerns
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- Object-level (row-level) checks
- Multi-tenant isolation
- Externalising policy

## Guidance

### Deny-by-default and separation of concerns

**Start with `allowed = false`.** Every authorization function must explicitly grant access; absence of a matching rule means deny.

Authorization logic belongs in a dedicated **policy layer** (a module, class or middleware), not inside route handlers or database queries. Route handlers call the policy layer; they do not contain conditions themselves.

```
Request → authenticate (verify identity)
         → authorize (call policy layer)
         → access data (service / DB call)
```

If authentication or authorization fails, return 401 or 403 respectively. Do not return 404 to hide resource existence unless the information that the resource exists at all is sensitive.

### Role-Based Access Control (RBAC)

Assign each user one or more roles. Map roles to permitted actions on resource types.

Design decisions:
- Keep roles coarse-grained (admin, editor, viewer, service-account). Proliferating roles is a maintenance burden.
- Roles control what resource *types* a user can act on. For which *specific instances*, use object-level checks.
- Store roles in the authentication token (JWT claims) or look them up fresh from the DB on each request; choose based on how quickly revocation must take effect.

```js
// Node.js: role check at the type level
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

app.delete('/articles/:id', requireRole('admin', 'editor'), deleteArticleHandler);
```

### Attribute-Based Access Control (ABAC)

ABAC evaluates attributes of the user, the resource and the environment together. Use it when RBAC alone cannot express the rules (e.g., "editors can only update their own articles").

Combine RBAC and ABAC: RBAC sets the outer gate (can this role act at all?), ABAC refines it (can this user act on this specific resource?).

```python
# Python: combined RBAC + ABAC check
def can_update(user, resource) -> bool:
    # Deny-by-default
    if user.tenant_id != resource.tenant_id:   # tenant isolation first
        return False
    if user.role == "admin":
        return True
    if user.role == "editor" and resource.owner_id == user.id:
        return True
    if resource.is_locked:                     # environment attribute
        return False
    return False                               # explicit deny fallback
```

### Object-level (row-level) checks

After confirming the user has the right role and attributes, verify they have permission on the *specific* record.

**Fetch then check** pattern: load the resource first (using only the primary key, not filtered by user), then run the policy check on the loaded object. Filtering by user in the query is not sufficient alone because query bugs can expose other users' data.

```js
// Express middleware: fetch-then-authorize
function authorizeResourceAccess(action, fetchResource) {
  return async (req, res, next) => {
    const resource = await fetchResource(req.params.id);
    if (!resource) return res.status(404).json({ error: 'Not found' });
    if (!canPerform(req.user, action, resource)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    req.resource = resource;   // available to the handler without a second DB call
    next();
  };
}

app.patch('/articles/:id',
  verifyToken,
  authorizeResourceAccess('update', (id) => articleService.findById(id)),
  updateArticleHandler,
);
```

For listing endpoints, inject the user's scope into the query as a query-layer filter *in addition to* row-level checks (not instead of). This prevents full-table scans but is not a substitute for per-record authorization.

### Multi-tenant isolation

Apply tenant isolation as the first check in every authorization decision; it must be impossible to bypass.

Rules:
- Never query across tenants unless the user has an explicit cross-tenant role.
- Always scope database queries with `tenant_id = :current_tenant_id`.
- Include `tenant_id` in cache keys so one tenant cannot read another's cached data.
- Validate `tenant_id` from the authenticated identity, not from query parameters or request body.

```python
# FastAPI dependency: tenant-scoped DB session
async def get_tenant_db(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Attach tenant filter that all queries must respect
    db.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": current_user.tenant_id})
    yield db
```

### Externalising policy

When rule complexity grows beyond simple role/attribute checks (time-based access, hierarchical resources, compliance mandates), move policy decisions to an external Policy Decision Point (PDP):

| Tool | Language | Model |
|---|---|---|
| Open Policy Agent (OPA) | Rego | ABAC, RBAC, any |
| Casbin | Go, Node.js, Python bindings | RBAC, ABAC, ACL |

The backend becomes a Policy Enforcement Point (PEP): it sends context to the PDP and enforces the decision. Deny if the PDP is unreachable (fail closed).

External policy is a separate service with a deployment cost. For most applications, well-structured in-code policy is simpler and sufficient. Migrate when rule complexity or compliance audit trails demand it.

## Examples

### Complete RBAC + ABAC middleware (TypeScript)

```ts
type Action = 'read' | 'update' | 'delete';

function authorize(user: AuthUser, action: Action, resource: Resource): boolean {
  if (user.tenantId !== resource.tenantId) return false;  // tenant boundary
  if (user.role === 'admin') return true;
  if (user.role === 'editor') {
    if (action === 'read') return true;
    if (action === 'update' && resource.ownerId === user.id) return true;
  }
  if (user.role === 'viewer' && action === 'read' && resource.isPublic) return true;
  return false;  // deny-by-default
}
```

### FastAPI dependency for object-level authorization

```python
class CanUpdate:
    async def __call__(self, doc_id: int, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)) -> Document:
        doc = await document_service.get(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        if not can_update(user, doc):
            raise HTTPException(status_code=403, detail="Forbidden")
        return doc

@router.put("/{doc_id}")
async def update_doc(payload: UpdateDocRequest,
                     doc: Document = Depends(CanUpdate())):
    # doc is already authorized; proceed safely
    ...
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Filtering the DB query by `user_id` and treating that as authorization | A query bug exposes every user's data | Fetch by primary key; run the policy check on the loaded object |
| Trusting `tenant_id` from request params | Callers can forge it | Derive `tenant_id` exclusively from the authenticated identity |
| Using 404 for every authorization failure | Hides the distinction between "missing" and "forbidden" | Return 403 for forbidden; 404 only when the resource genuinely does not exist and you must not reveal its existence |
| Embedding authorization logic in SQL (`WHERE user_id = ?` as the only check) | Business rules leak into the data layer; reuse becomes impossible | Separate policy layer; use query-level scoping as an optimisation, not as the sole guard |
| Storing roles in a cookie or query parameter | Client-side modification bypasses access control | Derive roles from the signed token or from the DB on each request |
| Failing open when the PDP is unavailable | Outage of the policy service grants full access | Fail closed: deny all if the PDP returns an error or is unreachable |

## Checklist

- [ ] Every authorization function starts with `allowed = false` (deny-by-default).
- [ ] Tenant isolation check runs before any role or attribute check.
- [ ] `tenant_id` is derived from the authenticated identity, not from the request.
- [ ] Object-level checks fetch the resource first, then run the policy; query-level filters are an optimisation only.
- [ ] No authorization logic inside route handlers; it lives in a policy layer.
- [ ] Listing endpoints scope queries to the current tenant AND apply row-level checks.
- [ ] 403 is returned for forbidden; 404 only for genuinely missing resources.
- [ ] Cache keys include `tenant_id` for any user-scoped data.

## Verify with context7 and gh_grep

- **context7:** Check `casbin` or `opa` client libraries at their locked versions for query syntax and middleware integration. Check `express-session` or FastAPI `Depends` patterns for attaching the user object to the request context.
- **gh_grep:** Search `tenant_id !== resource.tenant_id` or `user.tenant_id != resource.tenant_id` for multi-tenant boundary enforcement; `allowed = false` or `allowed = False` as a deny-by-default pattern; `req.resource =` or `request.state.resource` for the fetch-then-authorize pattern.

## Sources

- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Insecure Direct Object Reference Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html
- Open Policy Agent documentation: https://www.openpolicyagent.org/docs/latest/
- Casbin documentation: https://casbin.org/docs/overview
