# Requirement Elicitation

How to turn a vague request into confirmed needs: stakeholders, questions, assumptions, ambiguity detection and conflict resolution. Aligned with the requirements-engineering concepts in ISO/IEC/IEEE 29148:2018 (second edition, status active); checked 2026-11-26. The project's own docs and conventions win over this file.

## Contents

- Start from the repository, not from questions
- Identify stakeholders and their sources of truth
- Question techniques
- Asking blocking questions
- Surface assumptions
- Detect ambiguity
- Resolve conflicts
- Know when elicitation is finished

## Guidance

### Start from the repository, not from questions

Every question you ask costs the user attention. Exhaust cheaper sources first, in this order:

1. The brief and the task file: goal, constraints, earlier findings, verbatim errors.
2. `docs/PRD.md`, `docs/DESIGN.md`, `docs/API-CONTRACTS.md`, `docs/DB.md`, `docs/adr/`.
3. `docs/MEMORY.md` for recorded constraints and pitfalls.
4. The code, tests and configuration the change touches. Existing behaviour is evidence of intent, and tests are often the most precise statement of it.
5. Issue and change history (read-only), for why something works as it does.

Write down what each source says. If two sources disagree, you have found a conflict; handle it with the conflict procedure below, not by choosing.

A specification describes intent. If the code and a specification differ, report the difference and ask which is right. Never edit either to match.

### Identify stakeholders and their sources of truth

A stakeholder is anyone, or anything, whose needs or constraints shape what is acceptable. In a software project, people are not the only ones. List each with the thing they can decide.

| Stakeholder type | Examples | What they decide | Where to find them |
|---|---|---|---|
| Requester | The user giving the brief | Goal, priority, scope, approval | The conversation, task file |
| End user | Customer, admin, support agent | Tasks, usability needs, vocabulary | Personas in `docs/PRD.md`, support docs |
| Operator | Person who deploys and monitors | Availability, logging, rollback needs | `README.md`, deployment config |
| Maintainer | Future developers | Code and docs conventions | `AGENTS.md`, existing code |
| External system | Payment provider, identity provider, partner API | Interface format, limits, availability | Their official documentation |
| Regulator or policy | Privacy law, accessibility law, company policy | Mandatory constraints | The user; never guess a legal position |
| Adjacent features | Existing flows the change touches | Behaviour that must not break | Tests and code |

Only the user can resolve a product, cost or data decision. When a stakeholder cannot be consulted, record the need as an assumption with the stakeholder named.

For regulated topics (personal data, payments, accessibility mandates), record the obligation as a constraint with its source and ask the user to confirm it. Do not interpret law yourself. For the security side of such constraints, load `security-engineering`.

### Question techniques

Use the technique that matches the gap.

| Gap | Technique | Example question |
|---|---|---|
| Goal unclear | Ask for the outcome, then ask "so that" once or twice | "What should a user be able to do after this ships that they cannot do now? So that what improves?" |
| Vague quality word | Ask for a number or an example of too slow, too weak | "What response time would make you call this too slow, and on which screen?" |
| Scope boundary | Ask for the nearest thing that is out | "Should this also apply to existing accounts, or only new ones?" |
| Normal behaviour known, edge unknown | Walk the lifecycle and ask "what happens when" | "What happens if the user submits twice, or the email is already registered?" |
| Competing wishes | Ask for a ranking or a trade-off | "If we cannot have both, is exact search results or sub-second response more important?" |
| User cannot articulate need | Ask for a concrete recent example | "Describe the last time this was a problem. What did you do instead?" |
| Hidden rule suspected | Ask for the exception | "Is there any case where this rule does not apply?" |
| Existing behaviour unclear | Offer an observed fact, ask if intended | "Today the export drops rows with empty dates. Is that intended?" |

Rules for good questions:

- Ask open questions to discover, closed questions to confirm. Open: "What happens next?" Closed: "Is 30 days the limit?"
- Ask one thing per question. A question with "and" gets half an answer.
- Offer a proposed default with every question so the user can reply "yes".
- Use the user's vocabulary, then pin it in a glossary. Do not introduce implementation terms.
- Never ask what a document or the code already answers.
- Never ask leading questions that contain your preferred design.

Walk the lifecycle of each noun in the request: created, read, changed, deleted, expired, restored, shared, exported. Each verb not mentioned is a candidate gap. Then walk the failure side: invalid input, missing permission, dependency unavailable, partial completion, repeat submission, concurrent change.

### Asking blocking questions

A question is **blocking** if two reasonable answers produce different observable behaviour, cost or risk. Ask all blocking questions together in one message, numbered, each with a proposed default and the effect of being wrong. Do not drip-feed questions across several turns.

A question that is not blocking becomes a stated assumption. Keep the assumption visible and continue.

Never block silently. If you cannot proceed, report `Status: blocked` with the numbered questions, not a vague summary.

### Surface assumptions

An assumption is something you rely on that nobody has confirmed. Every design built on an unrecorded assumption is a latent defect.

Record each assumption with: an ID, the statement, why you assumed it, how it will be confirmed, who can confirm it and what changes if it is false.

Sources of hidden assumptions:

- Defaults you inherited from the existing code ("emails are unique").
- Scale ("a few hundred users") with no number given.
- Environment ("runs behind a reverse proxy", "single region").
- User behaviour ("users will have JavaScript enabled").
- Third-party behaviour ("the provider always returns a verified email").
- Time ("business hours", "UTC").

Version-sensitive assumptions about libraries, platform support or standards must be checked with context7 or official documentation. If you cannot, mark them **unverified**.

### Detect ambiguity

Read each statement as an adversarial implementer and as an adversarial tester. If two people could build different behaviour from it and both be right, it is ambiguous.

| Pattern | Example | Fix |
|---|---|---|
| Vague quality or degree | "fast", "easy", "secure", "scalable", "robust" | Metric, target, conditions; or mark **open** |
| Unbounded quantity | "many users", "large files", "a few retries" | Number with unit and a maximum |
| Undefined time | "soon", "regularly", "real-time" | Interval, clock source, percentile |
| Weak or escape wording | "as appropriate", "if possible", "where feasible", "as needed" | State the condition, or remove |
| Open-ended list | "such as", "including", "and so on" | Enumerate, or state that the list is exhaustive or illustrative |
| Dangling pronoun | "The service calls the queue and it fails" | Name the subject |
| Passive without actor | "The record is deleted" | Name who or what deletes it, and when |
| Compound statement | "The system validates and stores and notifies" | Split into three requirements |
| Logical ambiguity | "A and B or C", "not A or B" | Rewrite with explicit grouping or a decision table |
| Implicit unit or scope | "limit of 100" | Per what (user, minute, request), what unit |
| Negative ambiguity | "shall not be slow" | Rewrite positively with a threshold |
| Undefined term | "active user", "premium account" | Add to the glossary with a testable definition |
| Comparative without baseline | "faster", "better", "improved" | State the baseline and the target |

Test for terms such as "active user": define them with a rule a program could evaluate ("signed in at least once in the last 30 days").

A quick test for any sentence: write the one test that would fail it. If you cannot, the sentence is not yet a requirement.

### Resolve conflicts

Types of conflict:

| Type | Example | Typical resolution path |
|---|---|---|
| Direct contradiction | One doc says sessions last 30 minutes, another says 24 hours | Find the authoritative source; ask the user |
| Priority clash | Wants maximum security and zero login friction | Ask for ranking; record the trade-off |
| Quality attribute trade-off | Strong encryption at rest vs search over content | Record both, flag cost, ask the user |
| Spec vs code | Spec says soft delete, code hard-deletes | Report both; ask which is correct |
| Stakeholder disagreement | Support wants an export, security forbids it | Escalate; do not mediate by guessing |
| Requirement vs constraint | Needs offline mode; platform forbids local storage | Report the gap and what would have to change |

Procedure:

1. Quote both statements verbatim with their sources.
2. Check whether the conflict is real: different scope, different mode or different time can make both true.
3. Try to resolve from authority: later decision records, `docs/adr/`, explicit user statement. Newer is not automatically right.
4. Make at most 2 clarification attempts from documents and code history.
5. If still open, escalate with both quotes, the effect of each choice and a recommended default. Mark the affected requirements **open**.
6. Once resolved, record the decision where it will be found (requirement text, and an ADR if costly to reverse).

Never resolve a conflict by writing a requirement that satisfies neither.

### Know when elicitation is finished

Stop asking when all of these hold:

- Every requirement can be written as a single testable statement, or is marked **open** with an owner.
- Each noun in the request has a defined lifecycle, and its failure cases are addressed or marked **open**.
- No unresolved contradictions remain unreported.
- Blocking questions are answered or sent to the user.
- Remaining assumptions are recorded and none would change the observable behaviour if wrong, or the ones that would are in the open questions.

Do not gold-plate. If a possible requirement was not requested, raise it as an open question. The user decides what to build.

## Examples

### Vague request to clarified statements

Request: "Make password reset better, it's too slow and people complain."

Questions sent together (blocking):

```text
1. Which step is slow: the email arriving, the reset page loading, or setting the new password?
   Proposed default: the email arriving. If wrong: we would optimise the wrong step.
2. What delay counts as acceptable for the email? Proposed default: 95% delivered within 60 seconds.
   If wrong: the target and monitoring change.
3. Should reset links expire? Proposed default: keep the current expiry. If wrong: a security requirement changes.
```

After answers, requirements:

```text
FR-012  When a user requests a password reset for a registered email address, the system shall send one
        reset email to that address.
NFR-004 The system shall hand the reset email to the mail provider within 5 seconds for 95% of requests,
        measured over any 24-hour period under normal load. Verification: test and production metric.
        Source: Q2 answer. Status: draft.
```

### Ambiguity rewrite

| Before | Problem | After |
|---|---|---|
| "Search should be fast." | No metric | "NFR-009: Search results shall appear within 800 ms for 95% of queries against a 1 million record index, measured at the API response." |
| "Users can upload large images." | Unbounded | "FR-021: The system shall accept image uploads up to 10 MB in JPEG, PNG or WebP." |
| "The system should notify the owner when needed." | Escape wording, unclear trigger | "FR-022: When a comment is added to a document, the system shall send the owner one notification." |
| "Admins and editors can delete or archive posts." | Compound, unclear who does what | Split into four requirements, or a role table with actions. |

### Assumption register

```text
A-1  Emails are unique per account.
     Basis: unique index seen in the schema file. Confirm: user or a DB check.
     If false: account linking in FR-030 would attach to the wrong person.
A-2  The identity provider returns a verified-email flag.
     Basis: unconfirmed. Mark unverified; confirm with the provider's official documentation.
     If false: auto-linking must be refused.
```

### Conflict report

```text
Conflict C-1 (unresolved after 2 attempts)
  Source A (docs/PRD.md, FR-007): "Sessions shall expire after 30 minutes of inactivity."
  Source B (src/config/session.js): idle timeout is 24 hours.
  Effect of A: users re-authenticate often. Effect of B: security exposure for shared devices.
  Recommended default: 30 minutes per the PRD, pending your decision.
  Affected: FR-007, AC for session expiry marked open.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Asking the user before reading the repo | Wastes their time and signals no preparation | Exhaust brief, docs, code and history first |
| Drip-feeding questions over many turns | Slows work and fragments context | Ask all blocking questions together with defaults |
| Recording an assumption as a fact | The design silently depends on it | Mark it, give the confirmation path and owner |
| Treating "fast" or "secure" as a requirement | Cannot be tested, so cannot be accepted or rejected | Metric, target, conditions, or mark **open** |
| Choosing a side in a conflict | Hides a product decision from the person who owns it | Quote both, give a default, escalate |
| Inventing helpful extra requirements | Scope grows without consent | Raise as a numbered open question |
| Writing the solution as the need ("use Redis") | Locks design before the need is known | State the need ("repeat lookups within 50 ms") and route design to `system-architecture` |
| Never defining terms | Each reader invents a meaning | Maintain a glossary with testable definitions |
| Only eliciting the happy path | Failure behaviour is decided by accident in code | Walk lifecycle and failure cases for every noun |
| Rewriting existing requirements silently | The author cannot see what changed | Report defects with ID, quote and rule broken |

## Checklist

- [ ] Brief, task file, relevant `docs/` files, `docs/MEMORY.md` and affected code were read before any question was asked.
- [ ] Every stakeholder who can decide a requirement is listed with what they decide.
- [ ] Each question is single-topic, has a proposed default and states the effect of a wrong default.
- [ ] All blocking questions were sent together, numbered.
- [ ] Every assumption has an ID, a basis, a confirmation path and an impact if false.
- [ ] Every vague term was replaced by a measurable statement or marked **open**.
- [ ] Every undefined term was added to a glossary with a testable definition.
- [ ] Every conflict is quoted verbatim with sources and a recommended default.
- [ ] No requirement was invented; every addition came from a source or is an open question.
- [ ] Version-sensitive claims were checked or marked **unverified**.

## Verify with context7 and gh_grep

- **context7:** before relying on any third-party fact that became an assumption (a rate limit, token lifetime, supported platform version, accessibility level), resolve the library or service and query it for the version in the manifest, for example "`<service>` API rate limits", "`<library>` `<version>` default request timeout" or "WCAG 2.2 success criteria list". Confirm the fact and the version it applies to.
- **gh_grep:** search literal code to see how a behaviour is handled in maintained projects before deciding it is an open question, for example `Retry-After`, `expires_in`, `password reset token expired`, `Scenario: .* already registered`. Treat results as evidence, not as requirements.

## Sources

- IEEE Xplore, ISO/IEC/IEEE 29148:2018 abstract and status (read): https://ieeexplore.ieee.org/document/8559686
- ISO/IEC/IEEE 29148:2018 table of contents and scope, via the DIN listing (read; the standard text is not reproduced here): https://www.din.de/de/mitwirken/normenausschuesse/nia/veroeffentlichungen/wdc-beuth:din21:299567544/toc-3025650/download
