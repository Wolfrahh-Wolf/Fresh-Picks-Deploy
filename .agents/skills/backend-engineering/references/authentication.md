# Authentication

Covers implementing sessions, tokens (JWT), password storage, and OAuth 2.0/OIDC flows using vetted libraries; versions and standards checked 2026-11-26. Auditing these implementations for vulnerabilities belongs to `security-engineering`.

## Contents

- Choosing an authentication mechanism
- Password storage
- Session-based authentication
- Token-based authentication (JWT)
- OAuth 2.0 and OIDC flows
- Library selection

## Guidance

### Choosing an authentication mechanism

| Scenario | Preferred mechanism |
|---|---|
| Traditional server-rendered web app | Server-side sessions with HttpOnly cookies |
| Decoupled SPA or mobile client consuming your own API | Short-lived JWT access token + refresh token rotation |
| Third-party identity delegation (Google, GitHub, enterprise SSO) | OAuth 2.0 Authorization Code + PKCE; verify identity with OIDC `id_token` |
| Machine-to-machine API calls | OAuth 2.0 Client Credentials |

Avoid mixing mechanisms in the same surface without clear reason; it multiplies attack surface.

### Password storage

**Use Argon2id** for all new projects. It is the winner of the Password Hashing Competition and is recommended by OWASP.

Minimum Argon2id parameters (adjust up for your hardware; target ~250–500 ms per hash on the production server):

| Parameter | Minimum | Purpose |
|---|---|---|
| `m` (memory) | 65536 KiB (64 MiB) | Memory-hardness; resists GPU |
| `t` (iterations) | 3 | Time cost |
| `p` (parallelism) | 4 | Concurrency factor |

If Argon2 is unavailable in the runtime environment, use **bcrypt with cost factor ≥ 12**. Never use SHA-256/SHA-512, MD5 or any unsalted or fast hash for passwords.

Transparent migration: on successful login, check if the stored hash used an older algorithm or weaker parameters; if so, re-hash with the current algorithm and update the stored value in the same transaction.

**Password policy (follow NIST SP 800-63B):**

- Minimum length: 12 characters. No arbitrary complexity rules (special characters, mandatory rotations).
- Check new passwords against a list of known-common passwords (top 10 000 at minimum).
- Return generic messages on login failure (`"Invalid credentials"`); never confirm whether the email exists.

**Node.js example (argon2 library):**

```js
import argon2 from 'argon2';

async function hashPassword(plaintext) {
  return argon2.hash(plaintext, {
    type: argon2.argon2id,
    memoryCost: 65536,
    timeCost: 3,
    parallelism: 4,
  });
}

async function verifyPassword(hash, plaintext) {
  return argon2.verify(hash, plaintext); // returns boolean
}
```

**Python example (passlib with argon2-cffi):**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plaintext: str) -> str:
    return pwd_context.hash(plaintext)

def verify_password(plaintext: str, hashed: str) -> bool:
    return pwd_context.verify(plaintext, hashed)
```

### Session-based authentication

Store session state server-side (Redis or database), keyed by a cryptographically random session ID (≥ 128 bits of entropy). Never store user data or permissions directly in the cookie value.

Cookie attributes required:

| Attribute | Value | Reason |
|---|---|---|
| `HttpOnly` | true | Prevents JavaScript access; blocks XSS theft |
| `Secure` | true | HTTPS only |
| `SameSite` | `Strict` or `Lax` | Mitigates CSRF |
| `Path` | `/` | Scope to the application |
| `Max-Age` / `Expires` | Explicit | Avoids indefinite sessions |

Regenerate the session ID on privilege change (login, role elevation) to prevent session fixation.

**Express + express-session (Redis store):**

```js
import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });
await redisClient.connect();

app.use(session({
  store:             new RedisStore({ client: redisClient }),
  secret:            process.env.SESSION_SECRET,
  resave:            false,
  saveUninitialized: false,
  cookie: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 15 * 60 * 1000 },
}));
```

### Token-based authentication (JWT)

JWTs are suitable for stateless, decoupled APIs. Key rules:

- **Sign with RS256 or EdDSA** (asymmetric). If you must use HS256, use a secret of ≥ 256 bits. Explicitly reject the `none` algorithm and prevent algorithm confusion attacks.
- **Short-lived access tokens:** 5–15 minutes. Never store them in `localStorage`.
- **Refresh token rotation:** Each use of a refresh token issues a new one and invalidates the old. If a used refresh token is replayed, invalidate the entire session family (reuse detection).
- Store refresh tokens in an **HttpOnly, Secure, SameSite cookie** scoped to the refresh endpoint (e.g., `/auth/refresh`).
- Include only non-sensitive claims in the payload. Never put a password hash, PII or secrets in a JWT.

**Node.js example (jose library for RS256):**

```js
import { SignJWT, jwtVerify, importPKCS8, importSPKI } from 'jose';

const privateKey = await importPKCS8(process.env.JWT_PRIVATE_KEY, 'RS256');
const publicKey  = await importSPKI(process.env.JWT_PUBLIC_KEY,  'RS256');

async function signAccessToken(userId) {
  return new SignJWT({ sub: userId })
    .setProtectedHeader({ alg: 'RS256' })
    .setIssuedAt()
    .setExpirationTime('15m')
    .sign(privateKey);
}

async function verifyAccessToken(token) {
  const { payload } = await jwtVerify(token, publicKey, { algorithms: ['RS256'] });
  return payload;
}
```

### OAuth 2.0 and OIDC flows

**Authorization Code + PKCE** is the required flow for any user-facing client (web apps, mobile, SPAs):

1. Generate a `code_verifier` (random 43–128 character string) and derive `code_challenge = BASE64URL(SHA256(code_verifier))`.
2. Redirect user to the IdP with `response_type=code`, `code_challenge` and `code_challenge_method=S256`.
3. IdP redirects back with `code`. Exchange code + `code_verifier` for tokens on the **backend**, not in client-side JavaScript.
4. Validate `id_token` signature, `iss`, `aud`, `exp` and `nonce` before trusting claims.
5. Never allow wildcard redirect URIs; require exact string match.

OAuth 2.0 is for authorization (access delegation); OIDC (the `id_token`) is for authentication (identity). Do not use an access token to establish identity.

**Client Credentials** (machine-to-machine): validate the access token on the resource server by checking signature, `iss`, `aud` and `exp`. Use short token lifetimes.

### Library selection

Prefer purpose-built, actively maintained libraries over hand-rolled implementations:

| Need | Node.js | Python |
|---|---|---|
| JWT | `jose` (RFC-compliant; preferred) or `jsonwebtoken` | `python-jose` or `PyJWT` |
| Password hashing | `argon2-cffi` (via bindings) or `argon2` | `passlib[argon2]` |
| Sessions | `express-session` + `connect-redis` | Flask-Login + Flask-Session, or FastAPI with `starlette-session` |
| OAuth client | `openid-client` | `authlib` |
| OIDC server | Use a managed IdP (Auth0, Keycloak, Cognito) | Same recommendation |

Do not implement JWT signature verification, OAuth flows or password hashing from scratch.

## Examples

### Login handler (Express 5, JWT)

```js
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) throw createError(400, 'email and password are required');
  const user = await userService.findByEmail(email);
  // Constant-time compare even on user-not-found to prevent timing attacks
  const valid = user && await verifyPassword(user.passwordHash, password);
  if (!valid) throw createError(401, 'Invalid credentials');
  const accessToken  = await signAccessToken(user.id);
  const refreshToken = await issueRefreshToken(user.id);
  res.cookie('refresh_token', refreshToken, {
    httpOnly: true, secure: true, sameSite: 'lax', path: '/auth/refresh', maxAge: 7 * 24 * 3600 * 1000,
  });
  res.json({ accessToken });
});
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Storing JWT in `localStorage` | XSS can exfiltrate it and impersonate the user | Store access token in memory; refresh token in HttpOnly cookie |
| Using `alg: "none"` or not restricting algorithms | Algorithm confusion or no-signature bypass | Explicitly allowlist algorithms in `jwtVerify` |
| Long-lived JWTs without rotation | Stolen token is valid until expiry | Short access token TTL + refresh rotation with reuse detection |
| Storing session data in the cookie value | HMAC is not encryption; data is visible client-side | Store only the session ID in the cookie |
| Confirming whether an email exists on login failure | Enables user enumeration | Always return `"Invalid credentials"` regardless |
| Rolling your own PBKDF or crypto primitive | Almost certainly weaker than a vetted library | Use Argon2id via a library |
| Not re-generating the session ID after login | Session fixation: attacker pre-sets ID before login | Call `req.session.regenerate()` on login |

## Checklist

- [ ] Passwords hashed with Argon2id (`m≥65536`, `t≥3`, `p≥4`) or bcrypt (cost ≥ 12).
- [ ] No reversible encoding or fast hash (SHA-256, MD5) used for passwords.
- [ ] Session cookies have HttpOnly, Secure and SameSite attributes.
- [ ] Session ID regenerated on login (session fixation prevention).
- [ ] JWT algorithm explicitly allowlisted; `none` algorithm rejected.
- [ ] Access token TTL ≤ 15 minutes.
- [ ] Refresh tokens stored in HttpOnly cookie; rotate on each use.
- [ ] OAuth flows use PKCE; redirect URIs matched exactly.
- [ ] Login and password-reset endpoints return generic error messages.
- [ ] No sensitive data (passwords, PII) in JWT payload.
- [ ] All auth libraries are purpose-built and actively maintained.

## Verify with context7 and gh_grep

- **context7:** Resolve `jose`, `jsonwebtoken`, `argon2`, `express-session`, `passlib`, `python-jose`, `authlib` at the locked versions. Check: `jose` `jwtVerify` algorithm parameter; `argon2` hash options API; `express-session` `regenerate()` method; `openid-client` PKCE helpers.
- **gh_grep:** Search `jwtVerify(` with `algorithms:` parameter for RS256 enforcement; `argon2.hash(` with `type: argon2id`; `session.regenerate(` for session fixation prevention; `sameSite: 'lax'` or `sameSite: 'strict'` on session cookies.

## Sources

- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- NIST SP 800-63B Digital Identity Guidelines: https://pages.nist.gov/800-63-3/sp800-63b.html
- jose library (npm): https://github.com/panva/jose
- RFC 7636 – Proof Key for Code Exchange: https://datatracker.ietf.org/doc/html/rfc7636
