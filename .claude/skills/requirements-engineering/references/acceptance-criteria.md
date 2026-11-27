# Acceptance Criteria

How to write observable acceptance criteria, including Given/When/Then scenarios, edge and negative cases, and a definition of done for a requirement. Assumes Gherkin as documented by the Cucumber project (Feature, Scenario or Example, Scenario Outline, Background, Given/When/Then/And/But) and ISO/IEC/IEEE 29148:2018 verifiability concepts; checked 2026-11-26. The project's own conventions win over this file.

## Contents

- What an acceptance criterion is
- Choose a format
- Observable means observable at a boundary
- Writing Given/When/Then well
- Scenario Outline and data variation
- Covering edge and negative cases
- Criteria for non-functional requirements
- Writing criteria into the task file
- Definition of done for a requirement
- Keeping criteria small and independent

## Guidance

### What an acceptance criterion is

An acceptance criterion is a statement that someone other than the author can check, with a clear pass or fail, to decide whether a requirement is met. It is derived from a requirement and refers to its ID. It describes behaviour or a measurable property, never an implementation step.

Properties:

- **Observable:** the result can be seen at a system boundary (response, screen, message, file, log line the user is entitled to see, a state a user can read).
- **Unambiguous:** two reviewers reach the same verdict.
- **Specific:** concrete values, not "valid data".
- **Independent:** can be checked on its own, in any order.
- **Traceable:** names the requirement ID it verifies.

The architect fills acceptance criteria in the task file. Only the user approves them.

### Choose a format

| Format | Use when | Example |
|---|---|---|
| Checklist line | One simple, single-step check | `- [ ] (FR-040) GET /invoices/123 for an owned invoice returns 200 and a PDF` |
| Rule-based list | Several constraints on one rule | Bulleted list of values and limits |
| Given/When/Then | Behaviour depends on context, with a trigger and an outcome | Scenario with state, action and result |
| Decision table | Many combinations of conditions | Table of inputs and expected outputs |
| Measured threshold | Quality attribute | "p95 under 300 ms at 200 requests per second, load test" |

Prefer the simplest form that removes ambiguity. Use Given/When/Then when the context matters; do not wrap a one-line check in a scenario.

### Observable means observable at a boundary

Check results where a user or external system would see them. Internal state is observable only when it is itself a requirement (for example, an audit record the product must produce).

| Not observable | Observable |
|---|---|
| "The password is hashed correctly." | "Login with the correct password succeeds; the stored value for the account does not equal the password (inspection of the schema and a sample record)." |
| "The function returns early." | "Calling the endpoint twice with the same key produces one charge." |
| "The page is user-friendly." | "A new user completes checkout in under 3 minutes without help (usability test)." |
| "The cache is used." | "A repeated request within 60 seconds is served in under 50 ms at p95." |
| "A row is inserted in `orders`." | "The order appears in the user's order history with status Paid." |

The Gherkin guidance says the same thing: write outcomes against what a user or external system can see, not deep internals such as a database row, unless that record is itself the deliverable.

### Writing Given/When/Then well

The three parts:

- **Given:** the starting context, a state that already holds. It describes a world, not a user interaction.
- **When:** the single event or action under test.
- **Then:** the expected, observable outcome.

Rules:

1. **One behaviour per scenario.** One When. Several Whens means several scenarios.
2. **Declarative, not procedural.** State what is true and what happens, not clicks. "When the user submits a valid reset request", not "When the user clicks the third field and types".
3. **Concrete values.** "Given my account has a balance of 430" beats "Given I have money".
4. **Domain language.** Use glossary terms and avoid technology and UI wording unless the requirement is about the UI.
5. **Name scenarios by the rule they show**, so a failure tells you which requirement broke.
6. **Then asserts, Given sets up.** Do not put assertions in Given or setup in Then.
7. **Use And and But** to continue a keyword, rather than repeating Given or Then.
8. **Keep Background short.** Use it only for context common to every scenario in the feature. If a reader must scroll back to understand a scenario, move the setup into the scenarios.
9. **Do not put the same step text under two different keywords.** Step matching ignores the keyword, so the same text under Given and Then collides.
10. **Descriptions are free text, but a line may not begin with a keyword.** Lines starting `Given`, `When`, `Then`, `Feature`, `Scenario`, and similar are parsed as steps or structure.
11. **Keyword punctuation matters.** `Feature:`, `Scenario:`, `Scenario Outline:`, `Examples:` and `Background:` take a colon; step keywords do not.

Write in the project's language convention. If the project does not use a BDD tool, the scenarios are still valuable as plain text criteria. Choosing and wiring a test tool belongs to `testing-strategy`.

### Scenario Outline and data variation

Use a Scenario Outline when only the data changes, not the shape of the behaviour. Parameters appear in angle brackets and an Examples table supplies the rows. Each row runs the scenario once.

Do not use an outline to hide different behaviours behind one template. If the expected outcome has different shape for different rows, write separate scenarios.

For rules with many combinations, a decision table in the requirement plus an outline in the criteria keeps the data in one place.

### Covering edge and negative cases

A criteria set that covers only the happy path is incomplete. For each functional requirement, walk this list and keep what applies. If a case applies but you cannot define it, write it and mark it **open**.

| Category | Ask | Example |
|---|---|---|
| Normal | Does the main flow work with typical valid data? | Valid reset request sends one email |
| Alternate | Are there other valid routes to the same goal? | Reset by email or by SMS |
| Invalid input | What for wrong type, format, length, missing field? | Malformed email returns a validation error |
| Boundary | Minimum, maximum, just inside, just outside | 10 MB accepted; 10 MB plus 1 byte rejected |
| Empty and null | Nothing, blank, whitespace, zero | Empty search term returns the documented response |
| Duplicate and repeat | Same request twice, retry, double-click | Second submission does not create a second order |
| Permission | Not signed in, wrong role, someone else's data | Another user's invoice returns 404 |
| State | Wrong state for this action (expired, cancelled, locked) | Cancelling a shipped order is refused |
| Concurrency | Two actors at once, stale update | Second save of an edited record reports a conflict |
| Dependency failure | Downstream service slow or unavailable, partial completion | Email provider down: request succeeds and email is queued, or fails with a documented error |
| Time | Expiry, time zones, daylight saving, clock skew | Reset link rejected after its expiry |
| Volume | Large lists, large files, many requests | Page size limit applies; limit exceeded is rejected |
| Data change | Existing records, migration, rollback | Records created before the change still display |

Techniques for choosing cases systematically:

- **Equivalence partitioning:** group inputs the system treats alike, and test one from each group.
- **Boundary value analysis:** test at and around each limit, since defects cluster at edges.
- **Decision tables:** list every combination of conditions and the expected outcome.
- **State transitions:** for each state, list allowed and disallowed events.

Do not write criteria for behaviour nobody requested. If a case suggests a new requirement, raise it as an open question.

### Criteria for non-functional requirements

A quality criterion repeats the requirement's metric as a pass or fail check:

```text
(NFR-007) With 1 million documents indexed and 200 requests per second for 10 minutes on the
reference environment, the 95th percentile response time of GET /search is at most 300 ms.
Method: load test. Evidence: test report with percentile table.
```

State: metric, threshold, conditions, duration and the method. If the threshold is unknown, the criterion is **open**; do not copy a made-up number.

For accessibility, name the standard, version and conformance level the project chose, and how it is checked (automated check plus manual inspection). Confirm the current standard version with context7 or official documentation.

### Writing criteria into the task file

The architect fills only the plan, files in scope and acceptance criteria in the task file. The coordinator owns status and evidence.

Rules for the `Acceptance criteria` section:

- One checkbox per verifiable result, each starting with the requirement ID in parentheses.
- Include normal, error and boundary cases for each functional requirement.
- Include open items explicitly: `- [ ] (FR-014) **open**: behaviour when the provider is unavailable; owner: user`.
- Keep each line checkable by a different agent who has not read your reasoning.
- Keep the list small enough to verify: if one task needs more than about 12 criteria, the task is probably too large, so tell the coordinator and consider splitting it. For splitting work, load `product-technical-planning`.

Criteria become the contract for the implementer, tester and reviewer. A weakened or deleted criterion to make a task pass is a failure of the process; changing one needs the architect, and approval needs the user.

### Definition of done for a requirement

A requirement is ready to hand over (specified) when all are true:

1. It has an ID, a single "shall" sentence, a type, a source and a priority.
2. Vague terms are replaced by numbers or marked **open**.
3. It has a named verification method.
4. It has at least one normal, one error or negative and one boundary criterion, or the missing ones are marked **open**.
5. Each criterion is observable and refers to the requirement ID.
6. Assumptions behind it are recorded and marked.
7. It does not contradict another requirement.
8. It is recorded in the owning doc, not only in the task file.
9. The user has seen it. Only the user marks it approved.

A requirement is later considered met (done) when each of its criteria has recorded evidence: the command or check run and its result. That judgement belongs to the coordinator at the quality gate; do not claim it in a specification.

### Keeping criteria small and independent

- One criterion tests one thing. If a failed check leaves two possible reasons, split it.
- No criterion may depend on another having run first, unless the dependency is stated in Given.
- Do not duplicate a criterion at several levels; assign each to the cheapest level that can prove it (test design is `testing-strategy`).
- Avoid brittle literal wording. Quote an exact message only when the message is the requirement.

## Examples

### Bad to good

| Bad | Problem | Good |
|---|---|---|
| "Login works." | Untestable, only happy path | Three scenarios: valid, wrong password, locked account |
| "Errors are handled gracefully." | Opinion | "Submitting an empty form returns 422 with a message naming each missing field." |
| "Upload is fast." | No number | "A 10 MB file uploads and shows Done within 5 seconds on the reference network, 95% of attempts." |
| "Given the user clicks the Save button" | Action in Given | "Given a draft with a title" then "When the user saves the draft" |
| "Then the database has 1 row" | Internal | "Then the draft appears in the user's drafts list" |

### Feature file

```gherkin
Feature: Password reset
  A registered user can set a new password through a one-time link sent by email.
  Covers FR-012, FR-013, FR-014.

  Scenario: Registered user requests a reset (FR-012)
    Given a registered user with the email address "sam@example.test"
    When the user requests a password reset for "sam@example.test"
    Then one reset email is sent to "sam@example.test"
    And the page shows the confirmation "If the address is registered, a link was sent."

  Scenario: Unregistered address gets the same confirmation (FR-013)
    Given no account exists for "nobody@example.test"
    When a visitor requests a password reset for "nobody@example.test"
    Then no email is sent
    And the page shows the confirmation "If the address is registered, a link was sent."

  Scenario: Expired link is refused (FR-014)
    Given a reset link that was issued 61 minutes ago and the link lifetime is 60 minutes
    When the user opens the link
    Then the page shows "This link has expired."
    And the password is not changed
```

### Scenario Outline with boundary data

```gherkin
Scenario Outline: Upload size limit (FR-050)
  Given a signed-in user
  When the user uploads a PNG file of <size> bytes
  Then the upload is <result>

  Examples:
    | size     | result                          |
    | 1        | accepted                        |
    | 10485760 | accepted                        |
    | 10485761 | rejected with error FILE_TOO_BIG |
    | 0        | rejected with error EMPTY_FILE  |
```

### Filled task file section

```text
Acceptance criteria
- [ ] (FR-012) A registered email requests a reset: exactly one email is sent and the confirmation text is shown.
- [ ] (FR-013) An unregistered email shows the same confirmation and sends no email.
- [ ] (FR-014) A link older than 60 minutes is refused with "This link has expired." and the password is unchanged.
- [ ] (FR-014) A link used once cannot be used again.
- [ ] (FR-012) Two requests within one minute for the same address send at most one email. **open**: confirm the interval; owner: user.
- [ ] (NFR-004) 95% of reset emails are handed to the provider within 5 seconds under 50 requests per second (load test).
- [ ] (FR-012) Provider unavailable: the request returns the confirmation and the email is retried. **open**: retry count; owner: user.
```

### Requirement to criteria mapping

```text
FR-041  If an authenticated customer requests an invoice they do not own, then the system shall respond
        with 404 and shall not reveal that the invoice exists.

Criteria
  (FR-041) Another customer's invoice ID returns status 404.
  (FR-041) The 404 body for another customer's invoice is identical to the 404 body for a nonexistent ID.
  (FR-041) A signed-out request returns 401, not 404. **open**: confirm with the user.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Happy path only | Error behaviour is decided by accident | Add error, boundary and permission cases, or mark them **open** |
| Criteria describe implementation | Cannot be checked from outside; locks design | State the observable outcome |
| Several Whens in one scenario | A failure is hard to localise | One behaviour per scenario |
| Procedural UI steps | Break on every UI change | Declarative steps in domain words |
| Vague data ("valid input") | Reviewers pick different cases | Give concrete values and boundaries |
| Assertions in Given or setup in Then | Scenario meaning is unclear | Given sets state, Then asserts outcome |
| Same step text under Given and Then | Step matching ignores keywords, so they collide | Reword so each text has one meaning |
| Giant Background | Readers lose the context | Keep to shared essentials, or inline it |
| Invented thresholds | False precision causes false failures | Mark **open** with an owner |
| Weakening a criterion to pass a task | Hides a defect | Escalate; only the architect changes and the user approves |
| Criteria with no requirement ID | Cannot trace or prune | Prefix every line with the ID |

## Checklist

- [ ] Each criterion names the requirement ID it verifies.
- [ ] Each criterion is observable at a system boundary by someone other than the author.
- [ ] Each functional requirement has a normal, an error or negative and a boundary criterion, or the missing case is marked **open**.
- [ ] Permission, duplicate and dependency-failure cases were considered for each relevant requirement.
- [ ] Each Given/When/Then scenario has exactly one When and concrete values.
- [ ] No Then asserts on internal state unless that state is itself a requirement.
- [ ] Each Scenario Outline varies only data, and each Examples row has a defined expected result.
- [ ] Each non-functional criterion states metric, threshold, conditions and method.
- [ ] Unknown values are marked **open** with an owner, not guessed.
- [ ] Task file criteria are checkboxes, small enough to verify, and match the requirements in the owning doc.
- [ ] No criterion depends on another having run first, unless stated in Given.
- [ ] The architect has not marked anything approved.

## Verify with context7 and gh_grep

- **context7:** before writing criteria that depend on a framework, tool or standard, query the version the project uses, for example "Cucumber Gherkin reference keywords", "`<test tool>` `<version>` Scenario Outline Examples syntax", "WCAG 2.2 success criteria contrast minimum" or "`<HTTP framework>` `<version>` default status code for validation errors". Use the result to confirm syntax and defaults.
- **gh_grep:** search literal code for how real projects phrase and structure scenarios, for example `Scenario Outline:`, `Examples:`, `Then the response status is`, `Background:`, `@wip`. Search for the shape of an error case, such as `returns 429` or `FILE_TOO_BIG`. Treat results as evidence of practice, not as requirements for this project.

## Sources

- Gherkin Reference, Cucumber project (read through a modified copy of the official text at a CRAN-hosted vignette; the upstream page is https://cucumber.io/docs/gherkin/reference/): https://stat.ethz.ch/CRAN/web/packages/cucumber/vignettes/reference-gherkin.html
- IEEE Xplore, ISO/IEC/IEEE 29148:2018 abstract and status (read): https://ieeexplore.ieee.org/document/8559686
- ISO/IEC/IEEE 29148:2018 table of contents, via the DIN listing (read): https://www.din.de/de/mitwirken/normenausschuesse/nia/veroeffentlichungen/wdc-beuth:din21:299567544/toc-3025650/download
