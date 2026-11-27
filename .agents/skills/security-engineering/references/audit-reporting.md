# Audit Reporting

How to state scope, rate severity, gather evidence and write findings and the final audit report so they fit the RelayCrew standard report and the `AGENTS.md` quality gates; checked 2026-11-26 against OWASP Top 10:2025 and API Security Top 10:2023 identifiers.

## Contents

- Scope statement
- Severity scale and rating method
- Evidence standard
- Confidence
- Finding template
- Report template and verdicts
- Findings lifecycle and re-audit
- Escalation triggers

## Guidance

### Scope statement

Write the scope first. A reader must know what the verdict covers.

State: the change or system audited (task, files, revision range), assets (data and capabilities that matter), actors, entry points, trust boundaries, data classes, standards and editions used (for example OWASP Top 10:2025, API Security Top 10:2023, ASVS 5.0.0 at level L2), inputs received, inputs missing, and assumptions. If the brief defines scope, adopt it; otherwise derive it from changed files and `docs/ARCHITECTURE.md`, and say so. If critical inputs are missing, document the gap and list which checks could not be performed.

Audit only the user's project, using static review and safe local checks. Tools that install packages, use the network or modify files need user approval before they run.

### Severity scale and rating method

Use the scale from `AGENTS.md` exactly, and justify likelihood and impact separately.

| Severity | Meaning (`AGENTS.md`) | Typical examples |
|---|---|---|
| `critical` | Exploitable or data-losing now | Cross-tenant read by any user; committed live cloud key; unauthenticated administrative function |
| `high` | Likely serious defect | Missing object-level check on sensitive data; session not rotated at login; reachable vulnerable dependency with attacker input |
| `medium` | Real defect with limited impact | Missing rate limit on an expensive operation; sensitive header values in logs requiring log access |
| `low` | Improvement | Hardening, unreachable advisory, missing defence in depth |

Method: state **likelihood** (preconditions and attacker capability: anonymous, authenticated user, privileged, requires another flaw) and **impact** (who and what: one user, many users, other tenants, money, full takeover, data loss), then map using the matrix in [threat-modelling.md](threat-modelling.md). Rules:

- A catastrophic impact that needs existing root access is not `critical`; the precondition lowers likelihood.
- Do not inflate theoretical issues, and do not hide uncertainty: use the confidence field.
- Rate each finding on its own evidence. Mention chains in the impact text.
- `critical` and `high` block completion until fixed and re-audited, or until the user explicitly accepts the risk.

### Evidence standard

A finding is a claim backed by evidence a colleague can check.

- Cite a file and line, or a configuration item, for every finding. A finding with no location and no traced path is speculation; drop it or turn it into a question.
- Show the traced path: source, the controls found (or absent), the sink. One or two sentences are enough.
- Safe local checks are acceptable: running the project's tests, rendering configuration, reading a dependency tree, running a scanner after approval. Record the command and the result.
- Never include secret values, personal data or internal hostnames. Use location and type, or placeholders such as `<API_TOKEN>`.
- No exploit code and no attack payload collections. Describe the weakness, the preconditions and the defence. A failing test that demonstrates a missing authorization check is acceptable as a verification step when written in the project's test suite by the implementer; the auditor describes it and does not write it.
- Separate introduced issues (caused by this change) from pre-existing ones (present before). Pre-existing issues are reported but do not by themselves block this change unless the change makes them reachable or worse.

### Confidence

| Value | Use when |
|---|---|
| `confirmed` | You traced the path in code or configuration and saw no control, or ran a safe check that showed it |
| `probable` | The code strongly indicates the issue, but part of the path (a framework default, a deployed setting) was not verified |
| `needs verification` | The hypothesis cannot be settled by static review; state the test needed (dynamic testing, runtime inspection, provider-side setting) |

### Finding template

This is the format required of the security-auditor.

```
[severity] <title>
Location: <file:line or configuration>
Category: <OWASP or CWE reference where confirmed>
Evidence: <code path or check>
Impact: <what could happen, to whom>
Likelihood: <preconditions and attacker capability required>
Remediation: <specific fix and how to verify it>
Confidence: confirmed | probable | needs verification
```

Writing rules: the title names the defect, not the standard. Remediation is specific (the change to make, not "improve security") and includes how to verify it (a named test, a re-run scan, a configuration check). Cite the edition in the category, for example `OWASP A01:2025` or `API1:2023`. Add a CWE only when you confirmed it.

The reviewer uses a different finding shape (location, problem, failure scenario, recommendation); when you hand findings to the coordinator's task file, the table row is `Severity | Source | Finding | Status`.

### Report template and verdicts

Return the standard report. Put the audit content in `Summary`.

```
Status: done | blocked | failed
Verdict: pass | fix required | unable to audit
Summary:
  Scope: <change, files, revision range, standards and editions>
  Assets / Actors / Entry points / Trust boundaries: <lists>
  Assumptions: <list>
  OWASP Top 10:2025 coverage: <ten lines: evaluated with result / not applicable with reason / not assessable with reason>
  Findings (by severity): <finding blocks, critical first>
  Pre-existing issues: <separate list>
  Coverage gaps: <what was not checked and why>
Changes: none
Evidence: <commands and checks with results>
Research: <context7 and gh_grep queries and editions confirmed, or why none were needed>
Docs impact: <docs needing update with owners, or none with reason>
Open questions: <or none>
```

Verdict rules:
- **fix required:** one or more open `critical` or `high` findings.
- **pass:** no open `critical` or `high` finding in the audited scope. A `pass` still lists coverage and gaps and never says the system is secure.
- **unable to audit:** missing context, inaccessible files or scope too large to give meaningful assurance. State exactly what is missing. A cursory "looks fine" is not an audit.

`Status` follows the report format: `done` when the audit was completed (even if the verdict is `fix required`), `blocked` when you need input or an approval, `failed` when the work could not be done.

### Findings lifecycle and re-audit

1. **Open:** reported by the auditor. The coordinator records it in the task file's Review findings table and sends `critical` and `high` findings to the implementer.
2. **Fixed:** the implementer changes the code. Any source change invalidates earlier audit results for the affected area, so the auditor re-audits that area.
3. **Verified:** the auditor confirms the fix by evidence (code reading, passing negative test, clean re-scan) and checks the fix did not open a new issue.
4. **Accepted:** only the user can accept a residual risk. Record the acceptance and the named gap under "Decisions and approvals".

After 2 failed fix-and-verify loops, stop: the task is marked `blocked` and the user is given the options (a different fix approach, a design change through the architect, or an explicit risk acceptance). Never weaken, skip or delete a test to pass a gate.

Documentation sync after an audit: say in `Docs impact` which of `docs/ARCHITECTURE.md`, `docs/API-CONTRACTS.md`, `docs/DB.md` and `docs/adr/` (architect), and `README.md`, `CHANGELOG.md` (implementer) need updates, and propose durable lessons for `docs/MEMORY.md` (coordinator). Task file field "Security audit: Required: yes | no" is set by the coordinator.

### Escalation triggers

Escalate to the coordinator immediately, with what triggered it, what you reviewed, and what is needed:

- Exposed credentials or evidence of active exploitation (rotation and incident response needed).
- Findings that need dynamic testing, penetration testing or production runtime inspection; state which test.
- Possible regulatory or compliance implications; name the regulation if known.
- Trust boundaries that are misdrawn so no code-level fix works (design change needed).
- Supply chain risk with no mitigation path.
- Audit scope exceeds the available information.
- Custom cryptography or non-standard protocol use that needs specialist review.

## Examples

### Filled-in report (illustrative)

```
Status: done
Verdict: fix required
Summary:
  Scope: new document-sharing feature, task .agents/tasks/share-documents.md, 6 changed files, revision range <BASE>..<HEAD>.
    Standards: OWASP Top 10:2025, API Security Top 10:2023, ASVS 5.0.0 L2.
  Assets: document contents, share links, user emails. Actors: owner, collaborator, anonymous link holder, other-tenant user.
  Entry points: POST /documents/{id}/share, GET /s/{token}, DELETE /documents/{id}/share/{shareId}.
  Trust boundaries: browser to API; API to object storage; API to email provider.
  Assumptions: tenant id comes from the verified session (confirmed in src/auth/session.ts).
  OWASP Top 10:2025 coverage:
    A01 evaluated, 2 findings | A02 evaluated, none | A03 evaluated, 1 low | A04 evaluated, none
    A05 evaluated, none | A06 evaluated, 1 medium | A07 not applicable, authentication code unchanged
    A08 evaluated, none | A09 evaluated, 1 low | A10 evaluated, none
  Findings:
    [critical] Share endpoint does not check document ownership
      Location: src/routes/share.ts:37
      Category: OWASP A01:2025, API1:2023
      Evidence: the handler loads the document by id and creates a share link; no comparison with req.auth.userId or tenantId occurs; any authenticated user can share any document id.
      Impact: any user can generate a link to any document of any tenant and read it.
      Likelihood: any authenticated user, one request; exploitable now.
      Remediation: load the document with the tenant and owner in the query and return 404 when absent; add a cross-user and cross-tenant negative test; re-audit the route.
      Confidence: confirmed
    [medium] Share links never expire
      Location: src/services/shareLinks.ts:22
      Category: OWASP A06:2025
      Evidence: the expiry column exists but is never set; the lookup does not check it.
      Impact: a link forwarded once grants access indefinitely.
      Likelihood: requires a link to leak; medium.
      Remediation: set a default expiry, enforce it in the lookup, add a test for an expired link returning 404.
      Confidence: confirmed
    [low] Share link creation is not logged
      Location: src/routes/share.ts:52
      Category: OWASP A09:2025
      Evidence: no security event is emitted on create or revoke.
      Impact: no audit trail for sharing decisions.
      Likelihood: n/a; investigation gap.
      Remediation: log actor, document id and outcome without the token; add an alert threshold for bulk sharing.
      Confidence: confirmed
  Pre-existing issues: none found in scope.
  Coverage gaps: object storage bucket policy (not in repository); email provider settings; rate limits (pre-existing, not reviewed).
Changes: none
Evidence: static review of 6 changed files; project test command ran (all passing, no negative authorization tests for sharing); dependency manifest unchanged.
Research: context7 for the framework's route middleware ordering; gh_grep for share-link expiry patterns.
Docs impact: docs/API-CONTRACTS.md needs permissions and expiry for the share endpoints (architect); docs/DB.md needs the expiry rule (architect); CHANGELOG.md entry after fix (implementer).
Open questions: what default expiry does the product want?
```

### Task file row

```
| critical | security-auditor | Share endpoint does not check document ownership (src/routes/share.ts:37) | open |
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Findings without a file and line | Cannot be verified or fixed | Cite location and trace the path |
| Severity from impact alone | Everything becomes critical | State likelihood and impact, then map |
| A report that lists only findings | Creates false confidence in unexamined areas | State coverage and gaps every time |
| Saying "the system is secure" | Overclaims what static review can show | Say what was and was not covered |
| Including the secret or exploit steps | The report becomes a hazard | Location and type only; describe the defence |
| Mixing pre-existing and introduced issues | Blocks work for old problems or hides new ones | Separate lists |
| A generic OWASP checklist unrelated to the code | Looks thorough, proves nothing | Map each category to files, with a result or a reason |
| Closing a finding after a fix without re-audit | Fix may be incomplete or introduce new issues | Re-audit the affected area with evidence |

## Checklist

- [ ] The scope statement lists assets, actors, entry points, trust boundaries, standards with editions, inputs and assumptions.
- [ ] Each of the ten OWASP Top 10:2025 categories has a result or a reason.
- [ ] Every finding has location, category, evidence, impact, likelihood, remediation and confidence.
- [ ] Likelihood and impact are justified separately, and severity uses the `AGENTS.md` scale.
- [ ] No finding lacks a traced path.
- [ ] No secret value, exploit code or attack payload collection appears in the report.
- [ ] Introduced and pre-existing issues are separated.
- [ ] Coverage gaps and unavailable inputs are listed.
- [ ] The verdict follows the verdict rules, and `Changes` is `none`.
- [ ] `Docs impact` names affected files and owners.
- [ ] Escalation triggers were checked and raised where they apply.

## Verify with context7 and gh_grep

- **context7:** before citing a standard or tool in a report, confirm the current edition and identifiers from the project's own references: query the OWASP Top 10 and ASVS repositories for "latest stable version" and the scanner's documentation for the exact command used. Confirm library behaviour for any library your evidence relies on (for example how a framework's session middleware regenerates ids).
- **gh_grep:** search literal text for how mature projects structure security reports and advisories: `SECURITY.md`, `## Impact`, `## Remediation`, `CWE-` in advisory files. Use them as format references only; never copy text.

## Sources

- OWASP Top 10:2025 Introduction (category identifiers and names): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OWASP Top 10 API Security Risks 2023 (identifiers API1 to API10): https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP ASVS repository (latest stable 5.0.0, referencing format `v<version>-<chapter>.<section>.<requirement>`): https://github.com/OWASP/ASVS
- OWASP Threat Modeling Cheat Sheet (four questions; ranking inputs): https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
