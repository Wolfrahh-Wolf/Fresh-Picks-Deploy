---
name: backend-engineering
description: "Use when building, reviewing or debugging server code: Node.js, Express, Python backends, authentication, authorization, errors, caching and performance."
---

# Backend Engineering

Covers the full lifecycle of server-side code: runtime configuration, request handling, authentication, authorization, error propagation, caching and observable performance. The output is correct, secure, deployable server behaviour.

## When to use

- Implementing or modifying a Node.js, Express, Flask or FastAPI service.
- Reviewing server-side code for correctness, security or performance.
- Debugging a backend failure: unhandled rejection, timeout, auth error or cache miss.
- Adding or reviewing authentication flows (sessions, tokens, OAuth/OIDC).
- Implementing authorization checks (RBAC, ABAC, object-level).
- Designing or tuning a cache layer (in-process, Redis, CDN).
- Profiling or fixing a throughput or latency regression.

## Do not use for

- API contract design (HTTP shape, schema, versioning, OpenAPI spec): load `api-engineering`.
- Schema definition, SQL queries, migrations, indexes and ORM usage: load `database-engineering`.
- Security audit of authentication or authorization for vulnerabilities: load `security-engineering`.

## Research: context7 and gh_grep

- You MUST consult **context7** before writing, changing or reviewing any code that relies on Express, Flask, FastAPI, Node.js built-ins, or any third-party library used for auth, caching or HTTP. Read the version from the project's `package.json`, `pyproject.toml` or lockfile first and query that exact version. Useful queries: `"express" "5" async error handling middleware`, `"fastapi" "0.115" lifespan dependency injection`, `"node.js" "22" graceful shutdown closeIdleConnections`, `"flask" "3" application factory blueprint`, `"passport" OR "jose" JWT signing RS256`.
- You MUST search **gh_grep** when a pattern or integration is unfamiliar, an error is not explained by the docs, or you are unsure whether a middleware order is correct in real projects. Useful searches: `app.use((err, req, res, next)`, `process.on('SIGTERM'`, `@asynccontextmanager`, `password_hash argon2`, `cache.get cache.set lock`.
- Pure project-internal business logic (a wrong condition in this project's own code) needs neither. State that in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets, private code or internal hostnames in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/nodejs.md](references/nodejs.md) | Working on the runtime: event loop, streams, process management, configuration or graceful shutdown. |
| [references/express.md](references/express.md) | Routing, middleware, project layout or hardening an Express 5 app. |
| [references/python-backend.md](references/python-backend.md) | Flask or FastAPI structure, WSGI/ASGI, validation or async pitfalls. |
| [references/authentication.md](references/authentication.md) | Sessions, tokens, password storage or OAuth/OIDC flow. |
| [references/authorization.md](references/authorization.md) | RBAC, ABAC, object-level checks or multi-tenant isolation. |
| [references/error-handling.md](references/error-handling.md) | Error taxonomy, boundaries, response mapping, retries or timeouts. |
| [references/caching.md](references/caching.md) | Cache layers, keys, TTL, invalidation or stampede prevention. |
| [references/backend-performance.md](references/backend-performance.md) | Profiling, concurrency, pooling, N+1 queries, backpressure or load testing. |

## Workflow

1. **Understand the task.** Read the brief. Identify framework, runtime version and the files in scope. Check `docs/ARCHITECTURE.md` and `docs/API-CONTRACTS.md` for existing decisions. If the task touches authentication, authorization, sessions or payments, classify it **high risk** (requires security-auditor).
2. **Consult context7 and check the manifest.** Read the locked version of every library you will touch before writing any code. Query the reference files only as the task demands.
3. **Open the matching references.** Route by signal using the table above. Load at most two reference files in addition to this skill.
4. **Implement.** Follow the Standards below. Implementer writes source and tests; reviewer reads only.
5. **Reviewer steps.** Check each Standard item. For auth changes also confirm: no plaintext credential in source, error message is generic, every endpoint has an authorization check. File findings at the correct severity per `AGENTS.md`.
6. **Debugger steps.** State the failure, collect evidence, search `gh_grep` with the verbatim error, check library versions with context7, then propose the minimal fix without editing source. See `AGENTS.md` workflow.
7. **Verify.** Run every check in the Verification section below.
8. **Sync docs.** Update `docs/ARCHITECTURE.md` on new service boundaries, `docs/API-CONTRACTS.md` via the architect on interface changes, and `README.md` if setup commands changed.

## Standards

- Read the locked dependency version from the manifest or lockfile before every context7 query. The project's versions win over any default stated here.
- Set a timeout on every outbound network call and database query; never leave a call without a deadline.
- Never log or return internal error details (stack traces, SQL, file paths) to callers; map every error to a safe, typed response.
- Validate all inbound data at the boundary (request body, path params, query string, headers) before it reaches business logic.
- Authenticate before authorizing; authorize before accessing data; default to deny when no rule matches.
- Hash passwords with Argon2id (minimum `m=65536`, `t=3`, `p=4`) or bcrypt (cost ≥ 12); never use a reversible encoding or a fast hash.
- Use vetted libraries for cryptographic operations (tokens, signing, hashing); do not implement primitives from scratch.
- Store secrets in environment variables; use `.env.example` for names; never commit a secret or a string shaped like a key.
- Keep each function or handler to one responsibility; push business logic into a service layer, not into routes or controllers.
- Instrument every service with structured logs (timestamp, level, request ID, duration) and expose a health check endpoint.
- Apply backpressure: reject or queue requests when the service is at capacity rather than accepting unbounded load.
- For high-risk changes (auth, payments, sensitive data), require security-auditor review in parallel with the standard reviewer.
- Gracefully shut down: stop accepting connections, drain in-flight requests, close database pools, then exit.
- Never swallow an error silently; every caught error must be logged or re-thrown with added context.
- Write or update an integration test for every new endpoint or auth flow; a unit test for every new service function.

## Verification

- [ ] `context7` was queried for every library used, at the locked version; unverified claims are labelled.
- [ ] `gh_grep` was searched for any unfamiliar middleware or integration pattern.
- [ ] All inbound inputs are validated before reaching any service or database call.
- [ ] Every outbound call has a configured timeout.
- [ ] No stack trace, SQL or internal path appears in any HTTP response or log line visible to callers.
- [ ] Auth is in the correct order: authenticate → authorize → access.
- [ ] Passwords use Argon2id or bcrypt at the required strength.
- [ ] No secret appears in source, logs or task files; `.env.example` lists the variable names.
- [ ] The linter, type checker and test suite pass with no new failures.
- [ ] Graceful shutdown handles `SIGTERM` and `SIGINT`; a force-exit timeout is set.
- [ ] Structured logging is in place with request ID and duration on every request.
- [ ] Health check endpoint responds correctly.
- [ ] `docs/ARCHITECTURE.md` and `docs/API-CONTRACTS.md` are up to date, or the architect has a follow-up task.

## Output

Return the standard report from `AGENTS.md`. Key additions for this skill:

- **Evidence:** linter command and exit code, test command and pass/fail count, the health check URL and response, and any `context7`/`gh_grep` queries with their relevant results.
- **Research:** every context7 library and version queried; every gh_grep pattern searched and what it returned or confirmed.
- **Docs impact:** `docs/ARCHITECTURE.md` (architect) on new services or boundaries; `docs/API-CONTRACTS.md` (architect) on interface changes; `README.md` and `CHANGELOG.md` (implementer) on setup or behaviour changes; `docs/MEMORY.md` (coordinator) on durable decisions or pitfalls learned.
