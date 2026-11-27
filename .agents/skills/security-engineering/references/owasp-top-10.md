# OWASP Top 10

Each category of the OWASP Top 10:2025 with detection questions and defences, plus how to cite ASVS 5.0.0 and the API Security Top 10:2023; editions confirmed on the official OWASP sites on 2026-11-26. If the project mandates a different edition, its documents win.

## Contents

- Using the list in an audit
- What changed from 2021 to 2025
- A01 Broken Access Control
- A02 Security Misconfiguration
- A03 Software Supply Chain Failures
- A04 Cryptographic Failures
- A05 Injection
- A06 Insecure Design
- A07 Authentication Failures
- A08 Software or Data Integrity Failures
- A09 Security Logging and Alerting Failures
- A10 Mishandling of Exceptional Conditions
- Companion standards: ASVS 5.0.0 and API Security Top 10:2023

## Guidance

### Using the list in an audit

The Top 10 is an awareness list, not a test plan. Use it as the minimum set of questions for every audit scope. For each category record one of: **evaluated** (with the result), **not applicable** (with a reason tied to the code, for example "no file upload in the changed files"), or **not assessable** (with what is missing). A bare category list copied into a report without mapping to the actual code is not an audit.

Cite findings as `OWASP A01:2025` and add a CWE only when you have confirmed it. Each category below lists the questions to ask of the code and the defences to expect. For depth, follow the pointer to the owning reference.

### What changed from 2021 to 2025

- Server-Side Request Forgery is no longer its own category; it is rolled into A01 Broken Access Control.
- A02 Security Misconfiguration rose from fifth to second place.
- A03 Software Supply Chain Failures widens the old Vulnerable and Outdated Components to cover dependencies, build systems and distribution infrastructure.
- A10 Mishandling of Exceptional Conditions is new. It covers improper error handling, logic errors and failing open.
- A07 is now named Authentication Failures, and A09 is now Security Logging and Alerting Failures, stressing that logging without alerting has little value.

### A01 Broken Access Control

Users act outside their intended permissions: reading or changing someone else's data, reaching admin functions, forced browsing, missing checks on state-changing methods, tampering with tokens or cookies, permissive CORS, and, in this edition, SSRF.

Detection questions:
- Does every route and data access path check who the caller is and whether they may act on this specific object?
- Is the default deny, with explicit allows only for public resources?
- Are checks done in trusted server-side code rather than the browser?
- Do POST, PUT, PATCH and DELETE have the same checks as GET?
- Can a caller change an identifier, role, tenant or owner field in the request and succeed?
- Does CORS allow only named origins?
- Does the server fetch any URL a user supplied?

Defences: central, reusable enforcement; ownership enforced in the data layer; deny by default; short-lived tokens and server-side invalidation; log and alert on access-control failures. Deep dive: [authorization-security.md](authorization-security.md), [api-security.md](api-security.md), SSRF in [application-security.md](application-security.md).

### A02 Security Misconfiguration

Insecure defaults, unnecessary features, verbose errors, missing hardening, permissive cloud or container settings.

Detection questions:
- Are debug modes, sample apps, default accounts and directory listing off in production configuration?
- Are security headers and cookie attributes set deliberately rather than left to defaults?
- Do error responses reveal stack traces or internal paths?
- Are cloud storage, databases and admin panels reachable from the internet only when required?
- Is configuration the same across environments except for secrets and endpoints, and is it reviewed as code?

Defences: a repeatable hardened baseline, minimal installed features, configuration in version control, automated checks. Deep dive: [infrastructure-security.md](infrastructure-security.md), secure defaults in [application-security.md](application-security.md).

### A03 Software Supply Chain Failures

Compromise in or across dependencies, build systems and distribution infrastructure, not only known-vulnerable libraries.

Detection questions:
- Is there a committed lockfile, and does the build install from it?
- Are new dependencies checked for maintainer reputation, install scripts and name similarity to popular packages?
- Are CI actions and base images pinned to immutable references?
- Does the pipeline have write access it does not need, and are artifacts traceable to a source revision?
- Are advisories checked, with reachability assessed?

Defences: pinning, provenance, least-privilege pipelines, reviewed upgrades, an inventory of what is shipped. Deep dive: [dependency-security.md](dependency-security.md), [infrastructure-security.md](infrastructure-security.md).

### A04 Cryptographic Failures

Missing or weak protection of data in transit and at rest, weak algorithms, poor key handling, poor randomness.

Detection questions:
- Is sensitive data sent only over TLS, with certificate validation left on?
- Is sensitive data at rest encrypted with authenticated encryption, and are keys stored apart from the data?
- Are passwords stored with a slow, salted password hash rather than a fast hash or encryption?
- Are tokens and identifiers generated by a cryptographically secure random source?
- Is any custom cryptography or deprecated algorithm used?

Defences: vetted libraries and protocols, managed key storage, rotation, no custom primitives. Deep dive: [data-protection.md](data-protection.md), password storage in [authentication-security.md](authentication-security.md).

### A05 Injection

Untrusted data interpreted as code or commands: SQL, NoSQL, operating system commands, template engines, LDAP, and script injection into pages (cross-site scripting).

Detection questions:
- Is every query built with bound parameters, including inside raw-query escape hatches of an ORM?
- Is output encoded for its context, and where is raw HTML rendering enabled?
- Are operating system calls made with argument arrays rather than shell strings built from input?
- Are templates ever compiled from user-supplied text?

Defences: parameterisation, context-aware output encoding, allowlist validation as a second layer, avoiding interpreters. Deep dive: [application-security.md](application-security.md).

### A06 Insecure Design

Flaws that no amount of correct implementation fixes: missing controls, abuse cases never considered, trust placed in the wrong place.

Detection questions:
- Is there a threat model or design note for this feature, and does it match the code?
- Can a legitimate feature be abused at scale (enumeration, scraping, bulk purchase, reset flooding)?
- Do business limits live in the domain model rather than only in the UI?
- Are failure paths safe (does the system fail closed)?

Defences: threat modelling during design, abuse cases as requirements, secure design patterns, tests for misuse. Deep dive: [threat-modelling.md](threat-modelling.md).

### A07 Authentication Failures

Weak or bypassable identity checks: credential stuffing, weak passwords, poor session handling, missing or bypassable MFA, flawed recovery flows.

Detection questions:
- How are passwords stored and what are the parameters?
- Is there a throttle on login, reset and MFA attempts, and does it avoid easy account lockout abuse?
- Are session identifiers random, rotated after login, invalidated on logout and expired on the server?
- Do recovery and registration flows reveal whether an account exists?
- Are token signatures, issuers, audiences and expiry validated?

Defences: use established frameworks and vetted libraries, MFA, safe recovery, secure session cookies. Deep dive: [authentication-security.md](authentication-security.md).

### A08 Software or Data Integrity Failures

Code, data or artifacts accepted without verifying integrity or origin, at a lower level than supply-chain compromise.

Detection questions:
- Is anything downloaded, deserialised or auto-updated without signature or integrity verification?
- Is untrusted data deserialised into objects with a format that can instantiate arbitrary types?
- Can a caller modify data that the server later trusts as authoritative (prices, roles, state)?
- Do CI artifacts get promoted without checking they came from the expected build?

Defences: signatures and checksums, safe data formats, server-side recomputation of authoritative values. Deep dive: [application-security.md](application-security.md), [dependency-security.md](dependency-security.md).

### A09 Security Logging and Alerting Failures

Security-relevant events are not recorded, or are recorded but nobody is told.

Detection questions:
- Are logins, failures, access-control failures, input-validation failures and admin actions logged with enough context to investigate?
- Does an alert exist for repeated failures, and does anyone receive it?
- Do logs exclude secrets, tokens, session identifiers and unnecessary personal data?
- Is log injection prevented (newlines and control characters neutralised)?
- Are logs protected from tampering and deletion?

Defences: structured security events, alert thresholds, protected log storage, redaction. Deep dive: [data-protection.md](data-protection.md).

### A10 Mishandling of Exceptional Conditions

The system fails to prevent, detect or respond to unusual states: uncaught exceptions, ignored return values, failing open, partial transactions, resource leaks on error, errors that reveal internals.

Detection questions:
- When an authorization or validation step throws or times out, does the request fail closed?
- Are multi-step operations rolled back completely on failure?
- Are resources (files, connections, locks) released on every error path?
- Is there a central error handler, and does it return generic messages while logging detail?
- Are missing or extra parameters handled explicitly?

Defences: handle errors where they occur, a global handler as backstop, roll back fully, quotas and rate limits, alerts on repeated errors.

### Companion standards: ASVS 5.0.0 and API Security Top 10:2023

**ASVS.** The latest stable version is 5.0.0 (May 2025), with three cumulative levels (L1 baseline, L2 standard, L3 advanced) and 17 chapters, V1 Encoding and Sanitization through V17 WebRTC. Cite requirements as `v<version>-<chapter>.<section>.<requirement>`, for example `v5.0.0-1.2.5`, because identifiers change between versions. Use ASVS to turn a category into a pass or fail check; pick the level from the project's risk (L1 for any application, L2 for most business applications holding sensitive data, L3 for the highest assurance).

| Topic | ASVS 5.0.0 chapter | Reference here |
|---|---|---|
| Encoding, injection | V1, V2 | [application-security.md](application-security.md) |
| API and web service | V4 | [api-security.md](api-security.md) |
| File handling | V5 | [application-security.md](application-security.md) |
| Authentication, sessions, tokens, OAuth | V6, V7, V9, V10 | [authentication-security.md](authentication-security.md) |
| Authorization | V8 | [authorization-security.md](authorization-security.md) |
| Cryptography, communication, data protection | V11, V12, V14 | [data-protection.md](data-protection.md) |
| Configuration | V13 | [infrastructure-security.md](infrastructure-security.md) |
| Logging and error handling | V16 | [data-protection.md](data-protection.md) |

Chapter titles V1, V7, V8 and V16 were read in official OWASP sources; the other chapter numbers above come from a secondary summary (unverified), so confirm them against the ASVS 5.0.0 CSV before citing a requirement id.

**API Security Top 10:2023** is the current edition of the separate API list (API1 Broken Object Level Authorization through API10 Unsafe Consumption of APIs). Use it alongside the web Top 10 for any HTTP or GraphQL API; all ten risks are covered in [api-security.md](api-security.md).

## Examples

### Category coverage table for an audit of a new file-upload feature

| Category | Result | Note |
|---|---|---|
| A01 Broken Access Control | Evaluated, 1 finding | Download route checks login but not file owner |
| A02 Security Misconfiguration | Evaluated, no finding | Upload directory outside web root, no listing |
| A03 Software Supply Chain Failures | Evaluated, 1 low finding | New image library, unpinned range; reachability confirmed |
| A04 Cryptographic Failures | Not applicable | No new sensitive data at rest in changed files |
| A05 Injection | Evaluated, no finding | File names never reach a shell or query |
| A06 Insecure Design | Evaluated, 1 medium finding | No per-user quota; storage can be exhausted |
| A07 Authentication Failures | Not applicable | Authentication code unchanged |
| A08 Software or Data Integrity Failures | Evaluated, no finding | Files are never executed or deserialised |
| A09 Security Logging and Alerting Failures | Evaluated, 1 low finding | Rejected uploads are not logged |
| A10 Mishandling of Exceptional Conditions | Evaluated, 1 medium finding | Temporary file not removed when the size check throws |

### Bad to good: a finding cited with edition

```
Bad:  "Looks like an OWASP issue."
Good: "[high] Download route does not check file ownership
       Category: OWASP A01:2025 (CWE-639 confirmed), ASVS 5.0.0 chapter V8 Authorization
       (look up the exact requirement id in the 5.0.0 CSV before citing it as v5.0.0-8.x.y)"
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Citing the 2021 list or 2021 names | Reports disagree with the current edition | Cite A01 to A10 of 2025 and name the edition |
| Looking for SSRF as its own category | It is now inside A01 | Report SSRF under A01:2025 and API7:2023 |
| Treating the list as the whole scope | Business-logic and project-specific risks are missed | Use it as the minimum, add threat-model findings |
| Marking a category "not applicable" without a reason | Reader cannot tell if it was checked | Tie each N/A to the files reviewed |
| Equating "no dependency CVE" with A03 satisfied | A03 covers build and distribution compromise | Also check pinning, provenance and pipeline permissions |
| Copying ASVS ids without a version | Ids change between versions | Use `v5.0.0-x.y.z` |

## Checklist

- [ ] All ten categories have a result, a reason or a gap in the report.
- [ ] Findings cite the category with the 2025 identifier.
- [ ] SSRF findings are filed under A01:2025 and, for APIs, API7:2023.
- [ ] ASVS references include the version.
- [ ] The ASVS level used is stated and justified by the project's risk.
- [ ] API findings reference the API Security Top 10:2023 identifier.
- [ ] The project's mandated edition, if any, was checked first.

## Verify with context7 and gh_grep

- **context7:** query the framework's security documentation for the project's version to confirm which defences are built in (for example how the framework escapes output, protects against cross-site request forgery, and configures cookies) before marking a category satisfied. Query: "output escaping", "csrf protection", "session cookie options" for the framework in the lockfile.
- **gh_grep:** search literal code for escape hatches that bypass defaults: `dangerouslySetInnerHTML`, `v-html`, `|safe`, `rejectUnauthorized: false`, `verify=False`, `eval(`. Search `SECURITY.md` files in maintained projects to see how categories are tracked.

## Sources

- OWASP Top 10:2025 Introduction: https://top10.owasp.org/2025/0x00_2025-Introduction/
- A01:2025 Broken Access Control: https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- A10:2025 Mishandling of Exceptional Conditions: https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Top 10 API Security Risks 2023: https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP Application Security Verification Standard repository (5.0.0, release and referencing format): https://github.com/OWASP/ASVS
