# Data Protection

Audit checks for data classification, encryption in transit and at rest, minimisation, retention, logging and database access control, using OWASP Top 10:2025 A04 and A09, ASVS 5.0.0 chapters V11, V12, V14 and V16, and the OWASP Session Management Cheat Sheet logging guidance; checked 2026-11-26. Cipher and protocol minimums that were not re-read in this session are marked (unverified) and should be confirmed against the project's compliance baseline.

## Contents

- Classify before you audit
- Encryption in transit
- Encryption at rest and key handling
- Minimisation and exposure
- Retention and deletion
- Logging without leaking, and alerting
- Database access control
- Regulatory triggers

## Guidance

### Classify before you audit

You cannot judge controls without knowing what the data is. Use the project's classification if one exists in `docs/DB.md` or `docs/ARCHITECTURE.md`; otherwise propose this scheme and flag it for the architect to record.

| Class | Examples | Minimum handling |
|---|---|---|
| Public | Marketing content, published docs | Integrity protection |
| Internal | Operational metrics, internal docs | Authenticated access, no public listing |
| Confidential | Personal data (names, emails, addresses), business records, tokens | TLS everywhere, encrypted at rest, access logged, minimised in responses and logs |
| Restricted | Credentials, payment data, government identifiers, health data, cryptographic keys | All of the above, field-level protection where feasible, strict role access, short retention, never in logs or non-production copies |

For each flow in the threat model ([threat-modelling.md](threat-modelling.md)) write the class next to it. Then list where each class is stored, copied (caches, backups, analytics, logs, search indexes, exports, emails) and sent (third parties). Every copy is a place the protection can fail.

### Encryption in transit

- Every connection carrying Confidential or Restricted data uses TLS: browser to server, server to database, server to cache and queue, server to third party, and service to service when the network is shared. Plaintext inside a "trusted network" is a finding when it crosses a trust boundary.
- Certificate and hostname validation stays on. Search the code and configuration for disabled validation (`rejectUnauthorized: false`, `verify=False`, `InsecureSkipVerify`, `NODE_TLS_REJECT_UNAUTHORIZED=0`). Each is a finding unless confined to a documented local test fixture.
- Protocol and cipher policy: modern TLS only (1.2 as a minimum and 1.3 preferred) (unverified here; confirm against the project's baseline and the OWASP Transport Layer Security cheat sheet). Prefer managed platform defaults over hand-picked cipher strings.
- `Strict-Transport-Security` is sent on HTTPS responses; session cookies are marked `Secure`.
- No sensitive data in URLs, because URLs are stored in logs, history and referrer headers.
- Mutual authentication (client certificates or signed requests) for service-to-service calls where the network is not isolated.

### Encryption at rest and key handling

- Storage-level encryption (disk, database, bucket, backups, snapshots) is the baseline for Confidential and Restricted data. It protects against lost media, not against a compromised application.
- Field-level or application-level encryption is for Restricted data and for cases where database administrators should not read values. It needs key management or it adds nothing.
- Use authenticated encryption from a vetted library, and a cryptographically secure random source for keys, nonces and tokens. Any custom or hand-composed cryptography is a finding for specialist review.
- Keys are stored apart from the data they protect (a key manager or secrets store, not the same database or repository), access to them is separately limited, and a rotation procedure exists. See [secrets-management.md](secrets-management.md).
- Passwords are hashed, not encrypted; see [authentication-security.md](authentication-security.md).
- Hashing is not encryption: a hashed low-entropy value (a phone number, a national identifier) can be reversed by guessing. Use keyed hashing or encryption for such values.
- Backups, exports, replicas and snapshots carry the same class as the source; check that they are encrypted, access controlled and covered by retention.

### Minimisation and exposure

- Collect only what a stated feature needs. For each Confidential or Restricted field ask which requirement uses it; if none, report it as unnecessary exposure.
- Return only the fields the caller needs, shaped per role. Excess exposure in responses is API3:2023 in [api-security.md](api-security.md).
- Mask or truncate on display (last four digits only), and tokenise values that only need to be matched.
- Non-production environments hold synthetic or masked data, never copies of production Restricted data.
- Client-side storage, analytics and error trackers receive no Confidential or Restricted data unless approved and listed in the data inventory.
- Third-party processors: record which fields each receives and under which agreement; the project, not this skill, decides whether the agreement is adequate.

### Retention and deletion

- A retention period exists for each class and data store, recorded in `docs/DB.md`; if none exists, ask the user for one rather than inventing it.
- Deletion actually deletes: soft-deleted rows, search indexes, caches, object storage, derived datasets and backups are all covered, or the lag is documented.
- User-requested deletion and account closure have a tested path.
- Logs and analytics have their own, shorter retention.
- Temporary files and exports are removed after use, including on error paths (A10:2025).

### Logging without leaking, and alerting

Security logging has two halves: record the right events, and keep the wrong data out.

Record (A09:2025): authentication successes and failures, access-control failures, input-validation failures on sensitive operations, administrative and privilege changes, session creation, renewal and destruction, high-value business actions, and security-relevant configuration changes. Each entry carries time, event type, outcome, acting user id, source address and the target object. An event nobody is alerted on has little value: confirm an alert exists for repeated failures and for unusual volumes, and that someone owns it.

Never log: passwords, tokens, session identifiers, API keys, private keys, full payment numbers, government identifiers, or entire request and response bodies by default. Where correlation across a session is needed, log a salted hash of the session identifier instead of the identifier itself.

Further checks:
- Log injection: user-controlled text is neutralised (newlines and control characters) or logged as structured fields.
- Redaction is configured centrally in the logging layer, not left to each call site.
- Logs are stored with restricted access, protected from alteration and deletion, and retained for the period the project requires.
- Error responses to users are generic; detail goes to the server log (see A10:2025). A stack trace or database error in a response is a finding.
- Administrative interfaces that show or manage sessions or logs are themselves protected.

### Database access control

This audit belongs here, not in the database skill.

- The application connects with a dedicated, least-privilege role: data read and write on the tables it needs, no schema-changing rights, not a superuser or owner account.
- Migrations run under a separate role with schema rights, used only in the deployment step.
- Each service and each environment has its own credentials. Shared credentials across services hide the source of a compromise and widen the blast radius.
- Reporting and analytics users get read-only access to the minimum views, preferably masked.
- Database ports are not exposed to the internet; connections are restricted by network rules and use TLS (see [infrastructure-security.md](infrastructure-security.md)).
- Default accounts are removed or locked, and the connection string is not in the repository.
- Query design, indexing and migration safety are owned by `database-engineering`.

### Regulatory triggers

When data in scope may fall under a privacy or industry regulation (for example personal data of residents of regions with privacy law, payment card data, health data), flag it in the report as an escalation. Name the regulation if you know it, and state that the obligation analysis is outside this skill and needs the user or a specialist. Do not give legal conclusions.

## Examples

### Data inventory row (filled in)

| Data | Class | Stored in | Copies | Sent to | Retention | Controls found |
|---|---|---|---|---|---|---|
| Email address | Confidential | `users.email` | backups, search index, mail provider | email provider | life of account plus 30 days | TLS, disk encryption, masked in logs: yes |
| Password hash | Restricted | `users.password_hash` | backups | none | life of account | Argon2id, never returned |
| Reset token | Restricted | `reset_tokens.token_hash` | backups | email (link only) | 1 hour | hashed, single use |
| Card payment token | Restricted | provider vault | none | payment provider | per provider | no card data stored |

### Log redaction: bad to good (Node, `pino`)

```js
// Bad: request headers and body logged wholesale
logger.info({ req }, "incoming request");

// Good: redact at the logger, and log selected fields only
import pino from "pino";
const logger = pino({
  redact: { paths: ["req.headers.authorization", "req.headers.cookie", "req.body.password"], censor: "[REDACTED]" },
});
logger.info({ method: req.method, path: req.path, userId: req.auth?.userId }, "request");
```

Confirm the `redact` option shape for the installed version with context7 before recommending it.

### Finding: sensitive data in logs

```
[medium] Authorization header written to application logs
Location: src/middleware/logging.ts:19
Category: OWASP A09:2025, A04:2025
Evidence: the middleware logs req.headers in full at info level; bearer tokens are in that object; logs are shipped to a third-party aggregator.
Impact: anyone with log access, or the aggregator, can reuse live tokens until they expire.
Likelihood: requires log access; medium. Tokens are long-lived (24 hours).
Remediation: redact authorization and cookie headers in the logger configuration and log selected fields; rotate tokens issued during the exposure window; add a test that a logged request contains no authorization value.
Confidence: confirmed
```

### Database role check (read-only review of configuration)

```
App role: app_rw   -> SELECT, INSERT, UPDATE on app tables; no CREATE, no ownership of tables
Migration role: app_migrate -> schema rights, used by the deploy step only
Reporting role: app_ro -> SELECT on reporting views only
Finding: the API's connection string uses the table-owner role (ownership implies schema-changing rights).
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Encrypting at rest and calling it done | Does not protect against a compromised application or its credentials | Combine with access control, minimisation and key separation |
| Keys stored next to the encrypted data | One leak exposes both | Key manager or secrets store, separate access, rotation |
| Disabling certificate checks "to make it work" | Removes the protection of TLS | Fix the trust chain; limit any exception to a local fixture |
| Logging whole requests and responses | Credentials and personal data spread into logs | Redact centrally and log selected fields |
| Logging events but never alerting | Incidents stay unnoticed (A09) | Define alert thresholds and an owner |
| Production data in staging | Staging is less protected | Synthetic or masked data |
| No retention rule | Data accumulates and breach impact grows | Set and test retention and deletion |
| Application connects as owner or superuser | Any injection flaw becomes full database control | Dedicated least-privilege role and a separate migration role |
| Hashing low-entropy identifiers and treating them as safe | Values can be recovered by guessing | Keyed hashing or encryption |

## Checklist

- [ ] Each data flow and store in scope has a class.
- [ ] Every copy of Confidential and Restricted data (backups, logs, caches, exports, third parties) was listed.
- [ ] All connections carrying Confidential or Restricted data use TLS with validation on.
- [ ] No disabled-validation settings exist outside a documented local fixture.
- [ ] At-rest encryption is in place for Confidential and Restricted stores, and keys are stored and rotated separately.
- [ ] No custom cryptography is used.
- [ ] Responses, logs and error trackers contain only necessary fields.
- [ ] Retention and deletion exist, are recorded and cover backups, indexes and caches.
- [ ] Security events are logged and an owned alert exists.
- [ ] Logs exclude secrets, tokens, session ids and unnecessary personal data.
- [ ] The application database role is least-privilege and separate from the migration role.
- [ ] Possible regulatory implications are flagged for the user.

## Verify with context7 and gh_grep

- **context7:** for the logger in use, query "redact sensitive fields option". For the TLS client or HTTP library, query "certificate verification options". For the database driver and PostgreSQL, query "ssl mode connection options" and "roles and privileges GRANT". For the crypto library, query "authenticated encryption API and key generation".
- **gh_grep:** search literal code: `rejectUnauthorized: false`, `verify=False`, `InsecureSkipVerify`, `NODE_TLS_REJECT_UNAUTHORIZED`, `redact:`, `console.log(req.headers`, `GRANT ALL`, `createCipher(`. Review how maintained projects configure redaction and database roles.

## Sources

- OWASP Top 10:2025 Introduction (A04 Cryptographic Failures, A09 Security Logging and Alerting Failures): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OWASP Top 10:2025, A10 Mishandling of Exceptional Conditions (generic errors, central handling, resource release): https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Top 10:2025, A01 Broken Access Control (CWE list for exposure of sensitive information): https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- OWASP Session Management Cheat Sheet (session logging, Cache-Control, Clear-Site-Data, secure transport): https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Password Storage Cheat Sheet (hashing versus encryption, pepper storage): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP ASVS repository (5.0.0 chapter list: V11, V12, V14, V16): https://github.com/OWASP/ASVS
