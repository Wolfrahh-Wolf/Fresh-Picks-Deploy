# Express

Covers Express 5 (the current stable major version as of 2026-11-26): routing, middleware order, native async error handling, project layout and hardening hooks. Requires Node.js 18 or later. The project's `package.json` and lockfile determine the installed version; this file assumes Express 5.

## Contents

- Routing in Express 5
- Middleware order and request lifecycle
- Async error handling
- Project layout
- Hardening hooks

## Guidance

### Routing in Express 5

Express 5 ships a new version of `path-to-regexp` with breaking changes compared to Express 4:

| Feature | Express 4 | Express 5 |
|---|---|---|
| Optional parameter | `/user/:id?` | `/user{/:id}` |
| Inline regex | `/user/:id(\d+)` | Not supported; validate in handler |
| Wildcard | `/files*` | `/files/(.*)` with named capture |
| Invalid HTTP status | Silent | Throws at runtime |

Do not put regex in route path strings. Validate `req.params`, `req.body` and `req.query` explicitly in the handler or in a validation middleware before the route reaches business logic.

```js
// Bad (Express 4 style, broken in Express 5)
app.get('/items/:id(\\d+)', handler);

// Good
app.get('/items/:id', (req, res, next) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) return next(createError(400, 'id must be a positive integer'));
  // ...
});
```

Removed in Express 5: `app.del()` (use `app.delete()`), `req.param(name)` (use `req.params`, `req.body`, `req.query` explicitly), `res.send(status, body)` (use `res.status(status).send(body)`).

### Middleware order and request lifecycle

Order matters. The canonical order is:

1. Security headers (helmet)
2. Request logging (pino-http, morgan)
3. Body parsers (`express.json()`, `express.urlencoded()`)
4. Session or token verification
5. Route handlers
6. 404 handler (`app.use((req, res) => res.status(404).json({ error: 'Not found' }))`)
7. Error handler (four-argument signature, last)

Never put the error handler before routes; Express skips it. Never put body parsers after route handlers that read the body.

### Async error handling

Express 5 catches rejected promises and thrown errors from async route handlers and middleware automatically and routes them to the error handler. You do not need `express-async-handler` or manual `try/catch` wrappers in Express 5.

```js
// Express 5: throw or reject -> error middleware receives err
app.get('/users/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  if (!user) throw createError(404, 'User not found');
  res.json(user);
});

// Error handler: 4 arguments, always last
app.use((err, req, res, next) => {
  const status = err.status ?? err.statusCode ?? 500;
  const safe   = status < 500 ? err.message : 'Internal server error';
  res.status(status).json({ error: safe });
  if (status >= 500) logger.error({ err, reqId: req.id }, 'server error');
});
```

In Express 4 (if the project uses it), async handlers must call `next(err)` explicitly. Confirm the version in `package.json` before relying on automatic async catching.

### Project layout

A maintainable Express project separates responsibilities:

```
src/
  app.js          # create and configure app, register middleware and routers; no listen()
  server.js       # import app, call listen(), set up graceful shutdown
  routes/
    users.js      # express.Router(); import controller
  controllers/
    users.js      # validate input, call service, format response
  services/
    users.js      # business logic; no HTTP objects (req/res)
  middleware/
    auth.js       # token/session verification
    errors.js     # error handler
  config/
    index.js      # validated env schema
```

Keep `app.js` and `server.js` separate so tests can import the app without starting the HTTP server.

### Hardening hooks

Install and configure these before any route:

```js
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

// Security headers
app.use(helmet());

// Rate limiting on auth and sensitive routes
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  standardHeaders: 'draft-7',
  legacyHeaders: false,
});
app.use('/auth', authLimiter);

// Body size limit
app.use(express.json({ limit: '100kb' }));
app.use(express.urlencoded({ extended: false, limit: '100kb' }));
```

Disable `x-powered-by` (helmet does this automatically). Do not send the Express version or any internal framework name in response headers.

Trust a reverse proxy's `X-Forwarded-For` only when explicitly configured: `app.set('trust proxy', 1)`. Without this setting, `req.ip` returns the proxy's IP, which breaks rate limiting by IP.

## Examples

### Router module with validation and service call

```js
// routes/items.js
import { Router } from 'express';
import createError from 'http-errors';
import * as itemService from '../services/items.js';

const router = Router();

router.get('/:id', async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id < 1) throw createError(400, 'id must be a positive integer');
  const item = await itemService.getById(id);
  if (!item) throw createError(404, 'Item not found');
  res.json(item);
});

router.post('/', async (req, res) => {
  const { name, price } = req.body;
  if (!name || typeof name !== 'string') throw createError(400, 'name is required');
  if (typeof price !== 'number' || price <= 0) throw createError(400, 'price must be a positive number');
  const item = await itemService.create({ name, price });
  res.status(201).json(item);
});

export default router;
```

### Centralised error handler

```js
// middleware/errors.js
export function errorHandler(err, req, res, next) {
  const status = err.status ?? err.statusCode ?? 500;
  const safe   = status < 500 ? err.message : 'An unexpected error occurred';
  if (status >= 500) {
    logger.error({ err, reqId: req.id, path: req.path }, 'unhandled server error');
  }
  res.status(status).json({ error: safe });
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Putting the error handler before routes | Express never calls it for route errors | Always register `(err, req, res, next)` after all routes |
| Using `req.param(name)` from Express 4 | Removed in Express 5; throws at runtime | Use `req.params.name`, `req.body.name` or `req.query.name` |
| Sending `res.json(err)` directly | Leaks stack trace, internal paths and DB state to callers | Extract only a safe message; log the full error server-side |
| Not setting a body size limit | Allows memory exhaustion via large request bodies | Set `limit` in `express.json()` and `express.urlencoded()` |
| Setting `trust proxy` unconditionally | Allows clients to spoof IP via `X-Forwarded-For` | Set it only when behind a trusted proxy; configure the specific hop count |
| Registering `helmet()` after routes | Routes served before helmet don't get security headers | Register helmet as the first middleware |

## Checklist

- [ ] Express version confirmed from `package.json` and lockfile.
- [ ] Middleware order is: security → logging → body parser → auth → routes → 404 → error handler.
- [ ] Error handler has four arguments and is registered after all routes.
- [ ] No `req.param()` or `app.del()` (removed in Express 5).
- [ ] Body parsers have an explicit size limit.
- [ ] `helmet()` is registered before any route.
- [ ] Rate limiting is applied to auth and sensitive endpoints.
- [ ] `app.set('trust proxy', …)` is set only when behind a trusted reverse proxy.
- [ ] All async route handlers can rely on Express 5 automatic error forwarding (confirmed version ≥ 5).

## Verify with context7 and gh_grep

- **context7:** Resolve `express` at the version in `package.json`. Check: automatic async error handling behaviour, `path-to-regexp` changes, removed APIs (`req.param`, `app.del`), `trust proxy` options.
- **gh_grep:** Search `app.use((err, req, res, next)` for real error handler patterns; `helmet()` placement relative to routes; `express-rate-limit` with `standardHeaders: 'draft-7'`; `express.json({ limit:` for body size limits in production apps.

## Sources

- Express 5 migration guide: https://expressjs.com/en/guide/migrating-5.html
- Express 5 routing guide: https://expressjs.com/en/guide/routing.html
- Express 5 error handling: https://expressjs.com/en/guide/error-handling.html
- helmet documentation: https://helmetjs.github.io
- express-rate-limit documentation: https://express-rate-limit.mintlify.app
