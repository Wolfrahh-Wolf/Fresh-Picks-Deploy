# Threat Modelling

How to model data flows and trust boundaries, enumerate threats with STRIDE, rank them and choose mitigations, following the four-question method in the OWASP Threat Modeling Cheat Sheet; checked against OWASP Top 10:2025 on 2026-11-26. STRIDE and data flow diagrams are stable methods, not versioned standards.

## Contents

- Sizing the model
- The four questions as a procedure
- Assets, actors, entry points and data flows
- Trust boundaries
- STRIDE per element
- Ranking threats
- Choosing mitigations and accepting risk
- Recording the model and when to redo it

## Guidance

### Sizing the model

Match depth to the change. A model nobody finishes protects nothing.

| Change | Depth | Output |
|---|---|---|
| New field or endpoint inside an existing, already-modelled flow | Boundary checklist only (see Trust boundaries) | Notes in the task file |
| New feature that crosses a boundary: login, upload, payment, webhook, export, import | One data flow diagram plus STRIDE per element | Threat table in `docs/ARCHITECTURE.md` |
| New component, third-party integration, tenancy change, auth-model change, new infrastructure | Full model, alternatives compared | Threat table plus an ADR in `docs/adr/` |

Time-box the work. If the model is not finished inside the box, record the unmodelled area as a coverage gap rather than guessing.

### The four questions as a procedure

Use the four questions from the Threat Modeling Manifesto as the phases, each with an exit check.

1. **What are we working on?** Exit check: a diagram exists, every element is numbered, and every flow crossing a boundary is marked.
2. **What can go wrong?** Exit check: STRIDE was applied to every element the diagram shows, and each threat names the element and the boundary it affects.
3. **What are we going to do about it?** Exit check: each threat has a mitigation, a detection, or a named owner who accepted it.
4. **Did we do a good enough job?** Exit check: every mitigation maps to a test or a verification step, and every diagram element was visited at least once.

### Assets, actors, entry points and data flows

List these before drawing anything.

- **Assets:** data (credentials, personal data, payment data, tokens, business records) and capabilities (admin functions, ability to send email, ability to spend money).
- **Actors:** anonymous visitor, authenticated user, user of another tenant, support or admin user, service account, CI job, third-party service, a malicious insider. Include the actor most likely to misuse the feature, not only the intended one.
- **Entry points:** HTTP routes, webhooks, message queue consumers, file imports, scheduled jobs, command-line arguments, environment variables, admin tools, and any place the application reads data another process can write (a shared database table counts).
- **Data stores and outbound calls:** every database, cache, bucket, log sink, and every call to another service.

Draw a data flow diagram with five element types: external entity, process, data store, data flow and trust boundary. A text diagram is enough. Number the elements (`E1`, `P1`, `D1`, `F1`) so threats can refer to them. Label each flow with the data class it carries; for classes see [data-protection.md](data-protection.md).

### Trust boundaries

A trust boundary sits wherever data changes its level of trust or the authority that enforces rules changes. Treat these as boundaries without exception:

- Any place the application accepts input from a user, in any form (body, query, header, cookie, file, URL, token claim).
- Reads from a store that another process can write.
- Calls to and from third-party services, including webhooks and OAuth providers.
- Tenant to tenant, and user to administrator.
- CI to production, and developer machine to CI.
- Internal service to internal service when the network is shared or flat. Network location is not trust.

At every boundary crossing, ask four things: who is the caller (authentication), may they do this to this object (authorization), is the data well-formed and in range (validation), and will the event be recorded (logging). A crossing with a missing answer is a candidate finding.

### STRIDE per element

STRIDE is a mnemonic of six threat classes, each the violation of a security property. Apply the classes that fit each element type, not all six everywhere.

| Letter | Threat | Property violated | Applies to | Question to ask |
|---|---|---|---|---|
| S | Spoofing | Authentication | External entity, process | Can the caller claim to be someone else, or can a service be impersonated? |
| T | Tampering | Integrity | Process, data store, data flow | Can data be changed in transit, at rest or by a caller who should only read? |
| R | Repudiation | Non-repudiation | External entity, process, logs | Can a user or admin deny an action because nothing recorded it? |
| I | Information disclosure | Confidentiality | Process, data store, data flow | Can data reach someone not authorised: errors, logs, responses, caches, backups? |
| D | Denial of service | Availability | Process, data store, data flow | Can one caller exhaust CPU, memory, storage, connections or paid third-party calls? |
| E | Elevation of privilege | Authorization | Process | Can a caller gain capabilities beyond their role or tenant? |

Applicability by element: external entity gets S and R; process gets all six; data store gets T, I, D and R when it holds logs; data flow gets T, I and D.

Other techniques (attack trees, abuse cases, LINDDUN for privacy) can run alongside STRIDE. Cloud and managed-service systems need an extra pass for shared-responsibility gaps: for each managed service, write down which controls the provider owns and which the project must configure.

### Ranking threats

A threat is a risk, not a finding. It becomes a finding only when code or configuration evidence shows the weakness exists.

Rank with likelihood and impact stated separately.

- **Likelihood:** `low` needs unusual preconditions such as prior privileged access; `medium` needs a normal authenticated user or a plausible misconfiguration; `high` needs only an anonymous caller or a common mistake.
- **Impact:** `low` limited to one user's low-sensitivity data; `medium` many users or sensitive data of one user; `high` cross-tenant exposure, money movement, full account takeover or loss of integrity of critical data.

| Likelihood \ Impact | low | medium | high |
|---|---|---|---|
| high | medium | high | critical if exploitable now, otherwise high |
| medium | low | medium | high |
| low | low | low | medium |

This maps onto the severity scale in `AGENTS.md`: `critical` exploitable or data-losing now; `high` likely serious defect; `medium` real defect with limited impact; `low` improvement. Consider chains (a low-severity information leak that enables a high-severity takeover) but rate each link on its own evidence and mention the chain in the impact.

### Choosing mitigations and accepting risk

Prefer controls in this order, and note the trade-off of each.

1. **Eliminate:** remove the feature, the data or the permission. Cheapest and strongest.
2. **Prevent:** a control that blocks the threat (parameterised queries, server-side authorization, allowlists).
3. **Detect:** logging and alerting when prevention can fail; see A09 in [owasp-top-10.md](owasp-top-10.md).
4. **Recover:** rotation, revocation, backups, rollback.

Every mitigation must be testable: write it as an acceptance criterion with a negative case ("a user of tenant B requesting tenant A's invoice receives 404"). Only the user can accept a residual risk; record the acceptance under "Decisions and approvals" in the task file and name what was accepted.

### Recording the model and when to redo it

The architect records the model where the project's source of truth lives: trust boundaries and assumptions in `docs/ARCHITECTURE.md`, permissions per endpoint in `docs/API-CONTRACTS.md`, data classes and roles in `docs/DB.md`, decisions in `docs/adr/`. The security-auditor puts scope, assumptions and gaps in the audit report and never edits these files.

Redo or update the model when any of these happen: a new entry point, a new trust boundary, a new data class, a new third-party service, a dependency that executes code or makes network calls, a change of auth or tenancy model, a security incident, or a finding that shows the model missed a flow.

## Examples

### Filled-in text diagram: password reset by email

```
E1 User (browser)        E2 Email provider
P1 Web app (reset form)  P2 Reset service   P3 Mailer
D1 Users table           D2 Reset tokens table   D3 Application log

F1 E1 -> P1   email address submitted        [boundary: internet | app]
F2 P1 -> P2   reset request                  [same trust zone]
F3 P2 -> D2   store token hash + expiry      [class: credential-equivalent]
F4 P2 -> P3 -> E2  email containing link     [boundary: app | third party]
F5 E1 -> P1   token + new password           [boundary: internet | app]
F6 P2 -> D1   update password hash           [class: restricted]
F7 P2 -> D3   audit event                    [must exclude token and password]
```

### STRIDE applied to the flows that cross a boundary

| ID | Element | Threat | Evidence needed in code or config | Mitigation | Test |
|---|---|---|---|---|---|
| T1 | F1 | S: account enumeration through different responses | Does the response or timing differ for unknown emails? | Same response and similar timing for all emails | Two requests, one unknown email, identical response |
| T2 | D2 | I: tokens readable from a database backup | Is the raw token stored? | Store only a hash of a random token | Inspect schema: no raw token column |
| T3 | F5 | S: guessed or reused token | Token length, randomness source, single use, expiry | 128-bit or longer CSPRNG token, single use, short expiry | Second use of a token is rejected |
| T4 | F5 | E: sessions survive the password change | Are existing sessions revoked after reset? | Invalidate all sessions on reset | Old session cookie gets 401 after reset |
| T5 | F1 | D: mailbox flooding and paid email cost | Any per-address and per-source limit? | Limits per address and per source; see `api-engineering` for limit design | Burst of requests is throttled |
| T6 | F7 | R/I: no audit trail, or secrets in the log | Is the event logged without the token? | Log event, user id and outcome only | Log line contains no token |

### Ranked entry

```
T4  Sessions survive password reset
    Likelihood: medium (attacker needs a stolen session first)
    Impact:     high (reset does not evict the attacker)
    Rating:     high
    Status:     finding only if code shows sessions are not revoked
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Modelling only the happy path and the intended user | Misses the actor most likely to abuse the feature | List an abusive actor for every entry point |
| Drawing a diagram with no trust boundaries | Threats cannot be located; STRIDE becomes a generic list | Mark every boundary and review each crossing with the four questions |
| Treating the internal network as trusted | One compromised service reaches everything | Authenticate and authorize service-to-service calls |
| Reporting threats as findings without evidence | Noise, inflated severity, lost trust | Promote a threat to a finding only with file, line or configuration evidence |
| Rating by impact alone | Everything looks critical | State likelihood and impact separately and use the matrix |
| Mitigations with no test | No way to know the control works or keeps working | Write each mitigation as an acceptance criterion with a negative case |
| Never revisiting the model | The model describes a system that no longer exists | Redo it on the triggers listed above |

## Checklist

- [ ] Assets, actors, entry points, data stores and outbound calls are listed.
- [ ] The diagram has numbered elements and marked trust boundaries.
- [ ] Every boundary crossing was checked for authentication, authorization, validation and logging.
- [ ] STRIDE was applied to every element using the applicability rules.
- [ ] Each threat names its element and boundary.
- [ ] Each threat has likelihood and impact stated separately.
- [ ] Each threat has a mitigation, a detection, or a user-accepted residual risk.
- [ ] Each mitigation maps to a test or a verification step.
- [ ] Unmodelled areas are listed as coverage gaps.
- [ ] The model is recorded in the owning docs, or flagged for the architect to record.

## Verify with context7 and gh_grep

- **context7:** if the project uses a modelling tool or library (for example OWASP Threat Dragon or pytm), query its current documentation for how threats and data flows are declared before recommending syntax. Also query the project's framework docs for the boundary controls you reference (authentication middleware, request validation).
- **gh_grep:** search for the literal heading `## Threat model` and the literal word `STRIDE` in documentation of maintained projects to see how teams record threat tables; search `trust boundary` in architecture docs for naming conventions. Treat results as examples, not requirements.

## Sources

- OWASP Threat Modeling Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
- OWASP Top 10:2025, A10 Mishandling of Exceptional Conditions (threat modelling and secure design review in prevention guidance): https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Top 10:2025 Introduction: https://top10.owasp.org/2025/0x00_2025-Introduction/
