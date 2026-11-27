---
name: security-engineering
description: "Use when threat modelling or auditing security: OWASP, authentication, authorization, APIs, data protection, secrets, dependencies and infrastructure."
---

# Security Engineering

Find and evidence exploitable risk, then give specific, defensive remediation. Defensive only: describe weaknesses and fixes, never exploit code, attack payload collections or steps against systems the user does not own.

## When to use

- A change touches authentication, authorization, sessions, payments, personal or sensitive data, cryptography, secrets, file upload, a new external input surface, dependencies, database migrations, infrastructure, or CI/CD (the high-risk list in `AGENTS.md`).
- A design introduces or moves a trust boundary, a new integration, a new tenant model or a new data class.
- Someone asks for a threat model, a security audit, an OWASP review or a severity rating.
- Dependency advisories, a leaked credential or an exposed service must be assessed.

## Do not use for

- Implementing authentication or authorization features: load `backend-engineering`.
- General code review of correctness, maintainability or performance: load `code-review`.
- Designing API contracts, validation schemas, versioning or rate limits: load `api-engineering`.
- Writing Dockerfiles, pipelines or hosting configuration: load `devops-deployment`.
- Dependency upkeep and lockfile hygiene: load `languages-clean-code`.

## Research: context7 and gh_grep

- You MUST consult **context7** before you advise on, audit or rate any use of a library, framework, SDK, CLI or cloud API that carries a security control. Check the project's manifest or lockfile first and query that version. Useful queries: the framework's session and cookie options, the JWT or OIDC library's verify options, the ORM's raw-query escape hatch, the security-header middleware options, the dependency scanner's current command syntax.
- You MUST search **gh_grep** when a security pattern or integration is unfamiliar, when documentation is ambiguous, or when you need to confirm how a mitigation is written in maintained projects. Search literal code. Useful searches: `SameSite=`, `timingSafeEqual(`, `algorithms: [`, `permissions:` followed by `contents: read`, `automountServiceAccountToken`.
- Standards and advisories: also confirm the current edition from the official source (OWASP Top 10, ASVS, API Security Top 10, advisory databases). Cite editions in findings, for example `OWASP A01:2025` or `v5.0.0-1.2.5`.
- Pure project-internal logic (for example, tracing a variable through the project's own functions) needs neither. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets, private code, personal data or internal hostnames in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/threat-modelling.md](references/threat-modelling.md) | Scoping a design or audit: data flows, trust boundaries, STRIDE, ranking, choosing mitigations. |
| [references/owasp-top-10.md](references/owasp-top-10.md) | Evaluating every OWASP Top 10:2025 category with detection questions, plus ASVS and API Top 10 mapping. |
| [references/application-security.md](references/application-security.md) | Reviewing input handling, output encoding, injection, CSRF, SSRF, file upload and secure defaults. |
| [references/api-security.md](references/api-security.md) | Auditing endpoints for object and function level authorization, mass assignment, resource limits and inventory. |
| [references/authentication-security.md](references/authentication-security.md) | Auditing passwords, MFA, sessions, tokens, OAuth or OIDC and recovery flows. |
| [references/authorization-security.md](references/authorization-security.md) | Auditing access control, privilege escalation paths and tenancy isolation. |
| [references/data-protection.md](references/data-protection.md) | Classifying data, checking encryption, minimisation, retention, logging and database access control. |
| [references/secrets-management.md](references/secrets-management.md) | Finding stored secrets, judging rotation, or responding to an exposure. |
| [references/dependency-security.md](references/dependency-security.md) | Auditing dependencies: advisories, reachability, supply chain, pinning and provenance. |
| [references/infrastructure-security.md](references/infrastructure-security.md) | Auditing containers, CI/CD permissions, network exposure, cloud configuration and least privilege. |
| [references/audit-reporting.md](references/audit-reporting.md) | Writing scope, severity, evidence, findings and the final audit report. |

## Workflow

1. **Classify.** Read the brief, the task file and the high-risk list in `AGENTS.md`. State whether the change is high risk. If it is and you are not the security-auditor, say that an independent audit is required; never certify your own work as audited.
2. **Define scope.** List assets, actors, entry points, data classes and trust boundaries from the changed files and `docs/ARCHITECTURE.md`. Use `references/threat-modelling.md` for anything beyond a single endpoint. Write assumptions down.
3. **Evaluate the standard categories.** Walk all ten OWASP Top 10:2025 categories using `references/owasp-top-10.md`. Mark each as evaluated with a result, not applicable with a reason, or not assessable with a reason.
4. **Trace untrusted input to sensitive sinks.** Follow every entry point through validation, storage and output. Then go deep only where the scope needs it: application, API, authentication, authorization, data, secrets, dependencies, infrastructure (see the table above).
5. **Verify every finding.** Cite the file and line or the configuration. Use static review or a safe local check only. Never probe live, production or third-party systems. Set confidence to `confirmed`, `probable` or `needs verification`.
6. **Rate.** State likelihood and impact separately, then map to `critical`, `high`, `medium` or `low` using the scale in `AGENTS.md`. Separate introduced issues from pre-existing ones.
7. **Report gaps.** List what you could not check and why. A clean result states coverage and never claims the system is secure.
8. **Hand back.** Return the standard report. `critical` and `high` findings go back to the implementer through the coordinator and must be re-audited after any source change in the affected area.

### What differs by role

- **security-auditor:** run the full workflow independently of the reviewer. Never edit files, change configuration, rotate secrets or contact external services about findings. Verdict: `pass`, `fix required` or `unable to audit`. Use the finding and report formats in `references/audit-reporting.md`.
- **architect:** apply steps 1 to 3 at design time. Record trust boundaries and security assumptions in `docs/ARCHITECTURE.md`, permissions per endpoint in `docs/API-CONTRACTS.md`, data classes and database roles in `docs/DB.md`, and costly decisions in `docs/adr/`. Write security acceptance criteria that can be tested, including negative cases. Say in the report whether a security audit is required.
- **reviewer:** do a baseline pass only: input validation, injection, access control, secret handling, sensitive data in logs and errors, new dependencies. Every finding needs a failure scenario. If the change is high risk and no audit was requested, say so. Do not issue a security pass.

## Standards

- Every finding cites a file and line or a configuration item and a traced path. No theoretical-only findings.
- Every OWASP Top 10:2025 category is explicitly evaluated for the scope: a result, a reason it does not apply, or a stated gap.
- Severity states likelihood and impact separately. `critical` and `high` block completion until fixed and re-audited, or until the user explicitly accepts the risk.
- Access control is enforced server-side, deny by default, at function level and object level. Client-side checks are never counted as controls.
- Never print, log, copy or store a discovered secret. Report its location and type and advise rotation.
- Audit only the user's project with static review and safe local checks. Never probe live, production or third-party systems.
- Never write exploit code or attack payload collections. Describe the weakness, the evidence and the defence.
- A clean result lists what was and was not covered. It never states that the system is secure.
- A dependency advisory is not raised above `low` until reachability from the project's code is assessed; unknown reachability is `needs verification`.
- Tools that install packages, use the network or modify files need user approval before they run.
- Cite the edition of every standard used, and the project's manifest wins over this skill's version assumptions.
- Project conventions and `docs/` beat generic defaults, except where they are unsafe; then report it.
- If code and a specification disagree, report it and ask which is right. Do not silently change either.
- Each remediation names the specific change and how to verify it.
- Any source change invalidates earlier audit results for the affected area.

## Verification

- [ ] The list of changed files was produced with `git diff --name-only <base>...HEAD`, and every file is classified as in scope or out of scope.
- [ ] A search of the code for hardcoded credentials, key-shaped literals and `.env` files was done, and results record location and type only.
- [ ] The project's test command from `AGENTS.md` ran, and authorization tests include a negative case (another user's object, a lower role).
- [ ] A dependency audit ran with the project's scanner after approval (for example `osv-scanner scan source -r .`, or the ecosystem's audit command), or the gap is stated.
- [ ] Each finding has file and line, a traced path, likelihood, impact, remediation and confidence.
- [ ] Each of the ten OWASP Top 10:2025 categories has a result or a reason.
- [ ] Introduced and pre-existing issues are separated.
- [ ] Coverage gaps and the verdict are in the report.

## Output

Return the standard report from `AGENTS.md` (Status, Summary, Changes, Evidence, Research, Docs impact, Open questions).

- **Summary:** scope, assets, entry points, trust boundaries, findings by severity, coverage gaps and the verdict. Use `references/audit-reporting.md` for the exact templates.
- **Evidence:** the commands and checks that ran with their results, and the code paths traced. Never include secret values.
- **Research:** the context7 and gh_grep queries used and the editions confirmed, or why none were needed.
- **Docs impact:** state which of these need an update and who owns them: `docs/ARCHITECTURE.md`, `docs/API-CONTRACTS.md`, `docs/DB.md` and `docs/adr/` (architect); `README.md` for security setup and environment variable names, and `CHANGELOG.md` for security fixes (implementer); `docs/TASKS.md` and, for a durable security constraint or pitfall, `docs/MEMORY.md` (coordinator). Proposed changes to `AGENTS.md` or `CLAUDE.md` go to the user first.
