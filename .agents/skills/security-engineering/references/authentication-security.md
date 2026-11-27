# Authentication Security

Audit checks for password storage, multi-factor authentication, sessions, tokens (JWT, OAuth 2.0, OIDC) and recovery flows, using OWASP Top 10:2025 A07, ASVS 5.0.0 chapters V6, V7, V9 and V10, and the OWASP Password Storage and Session Management cheat sheets as read on 2026-11-26. This file audits; implementing authentication is owned by `backend-engineering`.

## Contents

- Audit approach and what to prefer
- Password storage
- Password policy and credential attacks
- Multi-factor authentication
- Sessions and cookies
- Tokens: JWT, OAuth 2.0 and OIDC
- Recovery, registration and enumeration
- Reauthentication and risk events

## Guidance

### Audit approach and what to prefer

1. Identify the mechanisms in use: local passwords, social or enterprise login, API keys, bearer tokens, service-to-service credentials.
2. Prefer established frameworks and vetted libraries over custom code. A hand-built session manager, token verifier or password hasher is a finding to examine closely, not an automatic defect; check it against the sections below.
3. For each mechanism check storage, transmission, lifetime, revocation, and the recovery path. The weakest path defines the strength of the whole login system.
4. Report locations and types only for any credential found; never print values.

### Password storage

Verified against the OWASP Password Storage Cheat Sheet on 2026-11-26.

| Algorithm | Minimum acceptable configuration |
|---|---|
| Argon2id (preferred) | One of: m=19456 KiB (19 MiB), t=2, p=1; m=47104 KiB, t=1, p=1; m=12288 KiB, t=3, p=1. Equivalent trade-offs between memory and iterations |
| scrypt (when Argon2id is unavailable) | N=2^17, r=8, p=1 (or an equivalent listed trade-off) |
| bcrypt (legacy only) | Work factor 10 or more, and a maximum input of 72 bytes enforced |
| PBKDF2 (when FIPS-140 compliance is required) | HMAC-SHA-256 with 600,000 iterations or more |

Audit questions:
- Are passwords hashed with one of the above rather than a fast hash (a general-purpose digest) or reversible encryption?
- Is the algorithm and its cost stored with each hash so it can be upgraded, and does login re-hash after verification when the cost is outdated?
- Is a per-password salt used? Modern libraries do this by default; confirm the library does and that the code does not substitute a fixed value.
- Is a pepper in use? If so, it must live apart from the password database, in a secrets store, and its loss handling must be documented. A pepper adds defence in depth; it never replaces a slow hash.
- Does the hashing call reject or bound very long passwords before the expensive step, to avoid a cheap denial of service?
- Are old, weaker hashes (unsalted digests, legacy algorithms) still present, and is there a migration plan?
- Is the comparison of secrets (tokens, verifiers) done in constant time?

Tune cost on the real server: hashing should complete in about a second or less, and benchmark on target hardware.

### Password policy and credential attacks

- Allow long passphrases and all Unicode characters; do not reduce entropy before hashing. Flag a low maximum length (other than the bcrypt input bound) and flag mandatory composition rules.
- Check new passwords against a list of known-breached or commonly used passwords. Current length minimums depend on the adopted guidance (NIST SP 800-63B-4 is the reference the cheat sheet cites); confirm the current numbers from the source before citing them (unverified here).
- Throttle login, reset and MFA attempts per account and per source. Avoid permanent lockout, which turns the control into a denial of service against users; prefer progressive delay or step-up verification.
- Log failures and alert on spikes across accounts (credential stuffing looks like many accounts from few sources).
- Check that login does not accept credentials in the URL, and that credentials never appear in logs or analytics.

### Multi-factor authentication

- Is MFA available for all accounts that need it, and enforced for privileged roles? Phishing-resistant methods (passkeys or hardware security keys using WebAuthn) are stronger than one-time codes; codes sent by SMS are the weakest accepted option.
- Can any path reach the account without the second factor? Check: password reset, "remember this device", alternate login endpoints, API tokens, legacy routes, account-linking flows, support overrides.
- Are one-time-code attempts rate-limited, and are codes single-use and short-lived?
- Are recovery codes stored hashed, shown once, and invalidated after use?
- Is changing or removing a factor protected by reauthentication?

### Sessions and cookies

Verified against the OWASP Session Management Cheat Sheet on 2026-11-26.

| Check | Expectation |
|---|---|
| Session id source | Framework-generated, or a cryptographically secure generator producing at least 128 bits when self-built; at least 64 bits of entropy is the floor for any scheme |
| Session id content | Meaningless; no user data or PII inside; all state on the server |
| Transport | Cookie carries it, never a URL parameter; HTTPS for the whole session, with HSTS |
| Cookie flags | `Secure`, `HttpOnly`, explicit `SameSite=Strict` (preferred) or `Lax`; `__Host-` prefix recommended for session cookies; no `Domain` attribute and narrow `Path` |
| Fixation | Session id regenerated on login and on any privilege change; the server rejects session ids it never issued |
| Expiry | Idle and absolute timeouts enforced on the server. Typical idle ranges: 2 to 5 minutes for high-value applications, 15 to 30 minutes for low-risk ones; absolute 4 to 8 hours for a working day |
| Logout | Server invalidates the session; all ids tied to the same logical session are revoked, including ones still in a rotation grace period |
| Caching | `Cache-Control: no-store` on responses with session data; `Clear-Site-Data` on logout where appropriate |
| Storage in the browser | No session ids, tokens or credentials in `localStorage` or `sessionStorage` |
| Server-side store | Access restricted; consider storing only a hash of the verifier so a read-only leak of the store does not give usable sessions |
| Logging | Never log raw session ids; log a salted hash for correlation |

Treat the session id as input: validate its format before using it in a lookup.

### Tokens: JWT, OAuth 2.0 and OIDC

A bearer token is equivalent to the credential that produced it. Check:

- **Signature and algorithm:** the verifier fixes an expected algorithm list and key; it never takes the algorithm from the token header, never accepts "none", and never uses a public key as a shared secret. Keys come from a trusted source with managed rotation.
- **Claims:** issuer, audience, expiry and not-before are validated; the audience is this service. Authorization decisions are not made solely from client-modifiable claims without checking server-side state where the role can change.
- **Lifetime and revocation:** access tokens are short-lived; refresh tokens are rotated and revocable; logout and password change invalidate them. Long-lived JWTs without a revocation path are a finding (see A01:2025 prevention guidance).
- **Storage:** browser applications keep tokens out of script-readable storage; prefer an `HttpOnly` cookie or a backend that holds tokens for the browser.
- **OAuth 2.0 and OIDC flows:** authorization code flow with PKCE for public clients; `state` verified on the callback (or PKCE used to bind it) and `nonce` verified for ID tokens; redirect URIs matched exactly against a registered list; no implicit flow for new work; client secrets only in confidential clients; scopes minimal.
- **Account linking:** automatic linking by email must require a verified email from the provider; an unverified email enables account takeover.
- **API keys:** scoped, revocable, stored hashed, never in URLs or client code, with owner and rotation recorded.

### Recovery, registration and enumeration

- Reset and registration responses are identical whether or not the account exists, including timing as far as practical.
- Reset tokens are random, at least 128 bits, single-use, short-lived and stored only as a hash. Links expire; using one invalidates all outstanding tokens.
- Completing a reset revokes existing sessions and refresh tokens, and notifies the account owner by another channel.
- No passwords are ever sent or displayed. Security questions are not used as a recovery factor.
- Email or phone changes need reauthentication and verification of the new address before taking effect.
- Recovery cannot bypass MFA without an equal-strength check.
- Rate limit all of the above; see `api-engineering` for limit design.

### Reauthentication and risk events

Require reauthentication (password or MFA) before: changing the password, email or MFA factor, completing an account recovery, performing high-value actions (payments, key creation, role changes), and when a login arrives from a new or suspicious device or address.

## Examples

### Cookie header: bad to good

```
Bad:   Set-Cookie: JSESSIONID=<ID>; Path=/app
Good:  Set-Cookie: __Host-sid=<ID>; Secure; HttpOnly; SameSite=Strict; Path=/
```

### Argon2id parameters recorded with the hash (PHC string format)

```
$argon2id$v=19$m=19456,t=2,p=1$<SALT>$<HASH>
```

The cost parameters travel with the hash, so verification works after the defaults are raised and rehash-on-login can upgrade old entries.

### JWT verification: fixed algorithm, issuer and audience (Node, `jose`)

```js
import { jwtVerify, createRemoteJWKSet } from "jose";

const jwks = createRemoteJWKSet(new URL(process.env.JWKS_URL));

export async function verify(token) {
  const { payload } = await jwtVerify(token, jwks, {
    algorithms: ["RS256"],               // fixed list, not taken from the token
    issuer: process.env.TOKEN_ISSUER,
    audience: process.env.TOKEN_AUDIENCE,
  });
  return payload;
}
```

Check the options for the installed `jose` version with context7 before recommending this exact shape.

### Finding: session id not rotated at login

```
[high] Session identifier not regenerated after authentication
Location: src/auth/login.ts:44
Category: OWASP A07:2025, ASVS 5.0.0 chapter V7 (Session Management)
Evidence: the handler sets req.session.userId on the existing session; no regenerate call occurs; the pre-login cookie remains valid after login.
Impact: an attacker who plants a known session id before login takes over the account after the victim signs in.
Likelihood: needs a way to set the cookie (an XSS or a sibling-subdomain flaw); medium.
Remediation: regenerate the session on login and on privilege change, then copy only needed data; add a test that the pre-login session id is rejected after login.
Confidence: confirmed
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Hashing passwords with a fast digest, even salted | Billions of guesses per second offline | Argon2id with the minimum parameters above |
| Treating the pepper as a replacement for a slow hash | A leaked pepper plus a fast hash is cracked quickly | Slow hash first; pepper only in addition, stored separately |
| Taking the JWT algorithm from the token header | Allows downgrade or key confusion | Fix the algorithm list in the verifier |
| Not checking audience and issuer | A token for another service is accepted | Validate `iss` and `aud` on every verification |
| Storing tokens in `localStorage` | One script injection discloses every token | `HttpOnly` cookie or a backend-held token |
| Permanent lockout after N failures | Anyone can lock out any user | Progressive delay, step-up checks, alerts |
| Different responses for unknown and known accounts | Lets callers enumerate users | Same response and similar timing |
| Logout that only deletes the cookie | A stolen session id stays valid | Invalidate on the server and revoke related ids |
| MFA enforced at login but not at recovery | The recovery path becomes the weakest link | Equal-strength verification in recovery and factor changes |

## Checklist

- [ ] Password hashing uses an accepted algorithm at or above the minimum parameters, with cost stored per hash.
- [ ] Legacy weak hashes were searched for and a migration path exists.
- [ ] Login, reset and MFA endpoints are throttled without enabling easy lockout abuse.
- [ ] No path reaches an MFA-protected account without the second factor.
- [ ] Session ids come from a vetted source with sufficient entropy and no embedded data.
- [ ] Session cookies set `Secure`, `HttpOnly` and an explicit `SameSite`.
- [ ] The session id is regenerated on login and on privilege change.
- [ ] Idle and absolute timeouts and logout are enforced on the server.
- [ ] Token verification fixes algorithms and validates issuer, audience and expiry.
- [ ] OAuth or OIDC flows use PKCE, validated `state` and `nonce`, and exact redirect URI matching.
- [ ] Recovery flows avoid enumeration, use single-use hashed tokens, and revoke sessions on completion.
- [ ] No credential or token appears in logs, URLs or script-readable storage.

## Verify with context7 and gh_grep

- **context7:** for the authentication library and framework in the lockfile, query: "session cookie options secure httpOnly sameSite", "regenerate session id", "password hashing parameters argon2", "verify JWT algorithms issuer audience", "OAuth PKCE and state". Confirm option names and defaults for the exact version.
- **gh_grep:** search literal code: `SameSite=`, `__Host-`, `algorithms: [`, `timingSafeEqual(`, `session.regenerate(`, `argon2id`, `localStorage.setItem("token"`. Compare with how maintained projects set cookie flags and verify tokens.

## Sources

- OWASP Password Storage Cheat Sheet (Argon2id, scrypt, bcrypt, PBKDF2 minimums; pepper; upgrading hashes): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet (entropy, cookie attributes, rotation, timeouts, storage, logging): https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Top 10:2025 Introduction (A07 Authentication Failures): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OWASP Top 10:2025, A01 Broken Access Control (token lifetime, JWT guidance): https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- OWASP Top 10 API Security Risks 2023 (API2 Broken Authentication): https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP ASVS repository (5.0.0 latest stable): https://github.com/OWASP/ASVS
