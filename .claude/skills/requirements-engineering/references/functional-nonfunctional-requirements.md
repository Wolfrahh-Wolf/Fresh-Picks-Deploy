# Functional and Non-Functional Requirements

How to classify a requirement, write it as a single testable sentence, and give every quality attribute a measurable target and verification method. Assumes ISO/IEC/IEEE 29148:2018 (second edition) concepts and the ISO/IEC 25010:2023 product quality model (second edition, nine characteristics); checked 2026-11-26. The project's own docs and conventions win over this file.

## Contents

- Classify before you write
- Construct a requirement sentence
- Characteristics of good requirements
- EARS sentence patterns
- Requirement attributes and IDs
- Quality (non-functional) requirements with measurable targets
- Choosing targets
- Verification methods
- Constraints versus design
- Requirement sets: consistency and trade-offs

## Guidance

### Classify before you write

Classification decides what you must add: a functional requirement needs behaviour and cases; a quality requirement needs a metric; a constraint needs a source.

| Type | ID prefix | Question it answers | Typical form |
|---|---|---|---|
| Functional | FR | What shall the system do? | Trigger, response, data |
| Quality (non-functional) | NFR | How well, under what conditions? | Metric, target, conditions |
| Constraint | CON | What limits the solution, and why? | Fixed technology, law, budget, platform, with source |
| Interface | IF | What does it exchange with others? | Inputs, outputs, errors, permissions per interaction |
| Data | DR | What must be stored, retained, validated? | Entities, rules, retention period |
| Business rule | BR | What policy must always hold? | Condition and consequence, independent of UI |

Decision aid for a statement you are unsure about:

1. Can you describe it as "when X happens, the system does Y"? Functional.
2. Does it describe how well Y happens (speed, uptime, accuracy, accessibility)? Quality.
3. Does it fix something about the solution that is not negotiable? Constraint. It needs a named source; if you cannot name one, it is probably a design preference to route to `system-architecture`.
4. Does it define what crosses a boundary? Interface. Format and contract detail belongs to `api-engineering`.
5. Does it hold regardless of screen or flow? Business rule.

Split mixed statements. "Users shall log in quickly and securely" is one functional need plus two quality needs.

Keep the classification as an attribute. The same user wish often yields several requirements of different types.

### Construct a requirement sentence

A well-formed requirement has these parts, in this order:

`[condition] [actor] shall [action] [object] [constraint on the action]`

- **Condition:** when or while it applies. Omit only for always-true statements.
- **Actor:** the system, a named component or a named role. Never "it" or "the team".
- **Action:** one observable verb. Avoid "support", "handle", "manage", "process" unless defined.
- **Object:** the thing acted upon, using glossary terms.
- **Constraint:** the quantity, bound, format or time that makes it checkable.

Modal verbs:

| Word | Meaning | Rule |
|---|---|---|
| shall | Binding, must be satisfied | Use only for requirements |
| should | Desirable, not binding | Use sparingly; give a priority and a reason it is not "shall" |
| may | Permitted option | Use for allowed behaviour, not for requirements |
| will | Statement of fact or future | Avoid for requirements; ambiguous |
| must | Often used interchangeably with shall | Pick one convention per project; follow the existing docs |

Use positive statements where you can. "The system shall reject uploads above 10 MB" is better than "The system shall not accept large uploads".

### Characteristics of good requirements

ISO/IEC/IEEE 29148 distinguishes characteristics of a single requirement from characteristics of a set. In your own review, use these questions (summarised in our words, not quoted from the standard):

Individual requirement:

| Characteristic | Review question |
|---|---|
| Necessary | If it were removed, would a stakeholder need be unmet? |
| Appropriate | Is it at the right level, neither solution detail nor too abstract? |
| Unambiguous | Can it be read only one way? |
| Complete | Does it hold everything needed to build and test it, with no missing condition or value? |
| Singular | Does it state exactly one thing? |
| Feasible | Can it be built within known constraints? |
| Verifiable | Is there a finite, objective way to prove it is met? |
| Correct | Does it accurately reflect the stakeholder need and its source? |
| Conforming | Does it follow the project's chosen format and conventions? |

Set of requirements:

| Characteristic | Review question |
|---|---|
| Complete | Are all needs, modes, error cases and interfaces covered? |
| Consistent | Do any two statements contradict, use different terms for the same thing, or use one term for two things? |
| Feasible | Can all be satisfied together under the budget and constraints? |
| Comprehensible | Can a new colleague understand the set without the author? |
| Able to be validated | Can stakeholders confirm that the set meets their real needs? |

The standard's wording is its own; consult the standard if exact text matters. The project may choose a lighter subset; the minimum for RelayCrew is singular, unambiguous, verifiable and traceable.

### EARS sentence patterns

EARS (Easy Approach to Requirements Syntax, introduced by Mavin and colleagues at Rolls-Royce in 2009) gives common requirement shapes. It is optional; use it if the project already does or the statements are hard to write plainly. It works poorly for logic-heavy rules, where a decision table is clearer.

| Pattern | Template | Example |
|---|---|---|
| Ubiquitous | The `<system>` shall `<response>`. | The API shall return all timestamps in UTC. |
| Event-driven | When `<trigger>`, the `<system>` shall `<response>`. | When a user submits the reset form, the system shall send one email. |
| State-driven | While `<state>`, the `<system>` shall `<response>`. | While an export is running, the system shall show progress. |
| Unwanted behaviour | If `<condition>`, then the `<system>` shall `<response>`. | If the email address is not registered, then the system shall show the same confirmation message. |
| Optional feature | Where `<feature is present>`, the `<system>` shall `<response>`. | Where two-factor authentication is enabled, the system shall require a code. |
| Complex | Combine the keywords, for example While then When. | While an account is locked, when a login is attempted, the system shall refuse it. |

Use the unwanted-behaviour pattern as a prompt: for each event-driven requirement, ask what happens if it goes wrong. (The pattern descriptions come from secondary sources: unverified against the originating paper.)

### Requirement attributes and IDs

Give every requirement at least these attributes. Keep them in a table or consistent block in `docs/PRD.md` unless the project has a different convention.

| Attribute | Rule |
|---|---|
| ID | Unique, stable, never reused. `FR-001`, `NFR-001`. Do not renumber when inserting or deleting. |
| Statement | One sentence, "shall". |
| Type | Functional, quality, constraint, interface, data, business rule. |
| Priority | Must, should, could, or won't for now. State the scale used. |
| Source | The user statement, doc, law or code that justifies it. |
| Rationale | Why it exists, in a sentence, when not obvious. |
| Verification | Test, inspection, analysis or demonstration. |
| Status | draft, proposed, approved, deprecated. Only the user moves it to approved. |
| Open flag | **open** and the owner, when a value or case is missing. |

Traceability runs both ways: each requirement links to its source and to its criteria, and each criterion links back to a requirement ID. A requirement without a source is gold-plating; a criterion without a requirement is dead weight.

### Quality (non-functional) requirements with measurable targets

A quality requirement is incomplete unless it states four things:

1. **Metric:** what is measured (p95 latency, error rate, availability percentage).
2. **Target:** the number and unit, plus the minimum acceptable value when one exists.
3. **Conditions:** load, data size, environment, time window and where it is measured.
4. **Verification:** how and when the number is checked.

ISO/IEC 25010:2023 lists nine product quality characteristics. Use them as a checklist so you do not forget one. For each, decide: relevant, not relevant (say why), or **open**.

| Characteristic | Prompt | Example metric and target form | Verification |
|---|---|---|---|
| Functional suitability | Is the right thing done, completely and correctly? | Rule correctness: 100% of the 25 documented pricing cases give the stated result | Test |
| Performance efficiency | How fast, how much resource, at what capacity? | p95 response under 300 ms at 200 requests per second on the reference environment | Load test, production metric |
| Compatibility | Does it coexist and interoperate? | Runs on Node.js versions in the project's engine range; imports files produced by version N of a format | Test, analysis |
| Interaction capability | Can specified users achieve goals, including with assistive technology? | Meets the WCAG success criteria the project names at the stated conformance level; 9 of 10 test users finish checkout unaided | Inspection, automated check, user test |
| Reliability | How available, fault tolerant, recoverable? | 99.9% monthly availability; recovery point at most 15 minutes after a crash | Monitoring, recovery drill |
| Security | Who may do what; how is data protected? | All endpoints other than health and login return 401 without a valid session | Test, inspection |
| Maintainability | How easily changed and tested? | New module needs no change to existing modules; critical-path automated test pass rate at least 98% | Inspection, analysis |
| Flexibility | Can it adapt to new environments or scale? | Deployable to the two named hosting targets using the same artifact | Demonstration, test |
| Safety | Does it avoid harm in its context of use? | Dangerous operation requires confirmation, and fails closed on sensor loss | Analysis, test |

The 2023 edition replaced "usability" with "interaction capability" and "portability" with "flexibility", and added safety. If the project's docs use the older names, keep the project's names and map them in one line.

For security and privacy targets, load `security-engineering` for the control design. Here you only state the observable requirement.

### Choosing targets

Never invent a target to make a requirement look complete. Use this order:

1. A figure from the user, a contract or a regulation (record the source).
2. A measured baseline of the current system, plus a stated improvement.
3. A figure from a comparable, documented system (record it as an assumption).
4. If none exists, write the metric and conditions, set the target to **open**, and name who can decide.

State a statistic, not a worst case, unless it is a hard limit. Use percentiles for latency ("95% of requests"), not averages, which hide slow tails. State the measurement window and the measurement point (client, edge, server).

Give a minimum acceptable value when it differs from the aim: "target 300 ms, never above 1 s at p99". Two values avoid argument at acceptance time.

Note the cost: each extra nine in availability, and each halving of latency, costs more. If the user gives a very strict target, record the consequence as an open question rather than silently accepting it.

### Verification methods

Every requirement names one of four methods, and the requirement's wording must allow it.

| Method | Use when | Evidence |
|---|---|---|
| Test | Behaviour can be exercised with inputs and checked outputs | Automated test results, run command and output |
| Inspection | Property of an artefact (document, configuration, code structure) | Checked item list with findings |
| Analysis | Property inferred by reasoning or calculation (capacity estimate, proof) | Calculation or model with its assumptions |
| Demonstration | Operation shown, not measured | Recorded steps and observed result |

If a requirement can only be checked by "looks good", rewrite it or mark the acceptance method **open**. Test design belongs to `testing-strategy`; here you only guarantee the requirement is testable.

### Constraints versus design

A constraint restricts the solution for a reason outside the design process. It is legitimate when it has a source: "Data shall be stored in the existing PostgreSQL cluster (source: operations policy)". It is design leakage when it has none: "The system shall use a message queue" with no reason.

When you see design in a requirement:

1. Ask what need it serves. Restate the need as the requirement.
2. If the user insists on the technology, record it as a constraint with the user as the source.
3. Route the actual design to `system-architecture`.

### Requirement sets: consistency and trade-offs

Check the set against itself before handing it on:

- Duplicate statements with different wording. Merge and keep one ID.
- One term for two things, or two terms for one. Fix in the glossary.
- Quality targets that cannot hold together (highest throughput with synchronous audit of every write). Flag the trade-off and ask.
- Functional requirements with no error behaviour.
- Requirements for modes the system has (first run, maintenance, degraded) that nobody wrote.
- Interfaces mentioned in text but absent from the interface list.

Record a trade-off decision once, where it will be found, and in an ADR when it is costly to reverse.

## Examples

### Classifying a single wish

Wish: "Customers should be able to download invoices quickly and only their own."

```text
FR-040  When an authenticated customer requests an invoice they own, the system shall return it as a PDF.
FR-041  If an authenticated customer requests an invoice they do not own, then the system shall respond
        with 404 and shall not reveal that the invoice exists.
NFR-011 The system shall return an invoice PDF within 2 seconds for 95% of requests, measured at the API
        edge under 50 concurrent users with invoices up to 5 pages. Verification: load test.
CON-003 Invoices shall be generated from data in the existing billing tables. Source: finance policy
        FIN-12 (from the user). Verification: inspection.
```

### Bad to good

| Bad | Problem | Good |
|---|---|---|
| "The system shall be highly available." | No metric | "NFR-020: The system shall be available 99.9% of each calendar month, excluding announced maintenance of up to 2 hours per month, measured by external probe every minute." |
| "The UI shall be intuitive." | Unverifiable | "NFR-021: At least 8 of 10 first-time test users shall complete account creation without help in under 3 minutes." |
| "The system shall support many file types." | Open-ended | "FR-050: The system shall accept JPEG, PNG and WebP files and reject all other types with error code UNSUPPORTED_TYPE." |
| "The system shall use React and cache results." | Design, no source | "FR-051: Search results for repeated queries shall appear within 200 ms for 95% of requests. (Design is decided separately.)" |

### Quality attribute row, filled in

```text
NFR-007  Metric: p95 latency of GET /search. Target: 300 ms. Minimum acceptable: 800 ms.
         Conditions: 1 million documents, 200 requests per second, reference environment.
         Measured at: API response, server side. Verification: load test before release and a
         production metric alert. Source: user answer 3. Priority: must. Status: draft.
NFR-008  Metric: monthly availability. Target: open (owner: user). Candidate: 99.9%.
         Verification: external probe. Note: cost consequence to be explained to the user.
```

### Decision table instead of a long sentence

Business rule BR-002, shipping fee:

| Order total | Member | Fee |
|---|---|---|
| under 50 | no | 5.00 |
| under 50 | yes | 0.00 |
| 50 or more | no | 0.00 |
| 50 or more | yes | 0.00 |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Mixing functional and quality needs in one sentence | Cannot be tested or traced as one | Split and classify each |
| Quality requirement with no number | Passes or fails by opinion | Metric, target, conditions, method |
| Inventing a target to fill the gap | A fake figure drives cost and acceptance | Mark **open** with the owner |
| Using averages for latency | Hides slow requests users feel | Use percentiles with a window |
| Writing "shall" and "should" at random | Binding level is unclear | Follow one convention, mark priority |
| Naming a technology without a source | Design is decided in the requirement | State the need; record a constraint only with a source |
| Reusing or renumbering IDs | Breaks traceability and review history | IDs are stable; deprecate, never reuse |
| Only quality requirements for performance | Reliability, accessibility, safety are missed | Walk all nine characteristics |
| Leaving error behaviour out | Failure is decided ad hoc in code | One unwanted-behaviour requirement per event |
| Calling a requirement approved | Only the user can approve | Leave status draft or proposed |

## Checklist

- [ ] Every statement is classified as functional, quality, constraint, interface, data or business rule.
- [ ] Every requirement is a single sentence with one actor, one response and "shall".
- [ ] Every requirement has an ID, source, priority, verification method and status.
- [ ] Each non-functional requirement has metric, target, conditions and verification.
- [ ] Every missing target is marked **open** with an owner and a candidate value if one exists.
- [ ] Each of the nine ISO/IEC 25010:2023 characteristics was considered and marked relevant, not relevant with a reason, or **open**.
- [ ] Latency and similar metrics use percentiles, a window and a measurement point.
- [ ] Each constraint names its source; each design-sounding requirement was restated as a need.
- [ ] No two requirements contradict, and no term has two meanings.
- [ ] Each event-driven requirement has an unwanted-behaviour counterpart or an **open** marker.
- [ ] No requirement is marked approved by the architect.

## Verify with context7 and gh_grep

- **context7:** before setting a target that depends on a platform or standard, query it for the version the project uses, for example "WCAG 2.2 conformance level AA success criteria", "`<framework>` `<version>` supported runtimes", "`<cloud service>` SLA availability" or "`<database>` `<version>` maximum connection limits". Quote the version in the requirement or assumption.
- **gh_grep:** search literal patterns to see how real projects phrase and test quality targets, for example `p95`, `p99 <`, `shall not exceed`, `Retry-After`, `max_file_size`, `aria-label`. Use results as evidence of practice, not as targets for this project.

## Sources

- IEEE Xplore, ISO/IEC/IEEE 29148:2018 abstract and status (read): https://ieeexplore.ieee.org/document/8559686
- ISO/IEC/IEEE 29148:2018 table of contents (concepts, characteristics of individual requirements and of a set, language criteria, attributes), via the DIN listing (read): https://www.din.de/de/mitwirken/normenausschuesse/nia/veroeffentlichungen/wdc-beuth:din21:299567544/toc-3025650/download
- ISO, ISO/IEC 25010:2023 product quality model, edition 2 (catalogue page read): https://www.iso.org/standard/78176.html
- ISO/IEC 25010:2023 preview describing changes from 2011 (read): https://cdn.standards.iteh.ai/samples/78176/13ff8ea97048443f99318920757df124/ISO-IEC-25010-2023.pdf
