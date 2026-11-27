# End-to-End Testing

Choosing critical journeys, preparing environments and test data, and controlling flakiness in end-to-end tests; runner-neutral with Playwright 1.65 examples (checked 2026-11-26). Playwright specifics are in `playwright.md`.

## Contents

- When end-to-end is the right level
- Choosing critical journeys
- Environments
- Test data
- Flakiness control
- Failure evidence
- Scope limits
- Routing to other skills

## Guidance

### When end-to-end is the right level

An end-to-end test drives the system the way a user does, through the real UI or the real public entry point, with all layers wired. It is the most expensive and least stable evidence, so use it only when the chain is the risk.

Write one when:

- A criterion is phrased as a user journey ("a shopper can pay and receive a confirmation").
- A past regression came from wiring: routing, session handling, serialisation between front end and back end, configuration, a browser-only behaviour.
- The behaviour is observable only in a real browser (focus handling, navigation, file download, rendering).

Do not write one for validation rules, calculations or error messages that a unit or API-level test can check; push those down (see `test-pyramid.md`).

### Choosing critical journeys

A critical journey is one whose failure stops users or loses money or data. Select by these tests, in order:

1. Does failure block revenue, sign-up, sign-in, or the core action of the product?
2. Does failure lose, corrupt or expose user data?
3. Does it cross several services or screens, so no lower-level test sees the whole path?
4. Has it broken before?

Keep the set small and explicit. A useful working limit is the journeys a team can name from memory (often 5 to 20 for a product); beyond that, the suite becomes slow and unreliable. Record each in the task file or test plan:

| Journey | Why critical | Level of detail | Test data |
|---|---|---|---|
| Sign up, verify, first sign-in | Entry to the product | Happy path only | New unique account per run |
| Add to cart, pay, see confirmation | Revenue | Happy path plus declined payment | Seeded product, payment sandbox or stand-in |
| Export my data | Legal and data handling | Happy path, one permission-denied | Seeded account with known records |

One journey, one test, one reason to fail. Test the happy path end to end; cover error and edge cases at lower levels. Add a second end-to-end test for a journey only for a different outcome that matters (a declined payment, for example).

### Environments

- **Allowed:** a local development environment, an ephemeral per-branch environment, or a dedicated test or staging environment with test data only. This matches the Other tools rule in `AGENTS.md`: browser verification runs against local or test environments only.
- **Forbidden:** production, shared environments holding real customer data, and real user or payment accounts. If a criterion cannot be verified without them, stop and escalate.
- Start the application the same way a user environment would: build, configuration and migrations applied. Playwright's `webServer` option can start and wait for a local server; see `playwright.md`.
- Pin what influences results: browser version (the one the test runner installs), operating system for visual comparisons, time zone, locale, viewport and feature flags. Set them in the test configuration, not on a developer's machine.
- Keep third parties out of the loop: stub or sandbox payment, email, SMS, maps and analytics. Letting a live third party sit inside a journey makes the test depend on someone else's uptime and rate limits.
- Isolation: environments the test mutates must be disposable or reset between runs through the project's documented reset step. Resetting a shared environment is destructive; ask the user first.

### Test data

Data causes more end-to-end failures than code. Rules:

- Create the data a test needs at the start of that test, through the fastest reliable route: an API call, a seed script or a database insert in a fixture. Do not click through the UI to create preconditions that are not the subject of the test.
- Make data unique per test run (a random or counter suffix in names and emails) so parallel tests and repeated runs do not collide.
- Do not share a mutable account between parallel tests. Give each worker or test its own account; Playwright documents authenticating once per worker with a worker-scoped fixture for exactly this case.
- Clean up what the test created, by identifier, in teardown that runs on failure too. Prefer an expiring or disposable environment over complex cleanup.
- Never use real personal data. Use obviously fake values and reserved example domains (`example.com`, `example.org`) for email addresses.
- Credentials for test accounts come from environment variables, never from the repository, and are not printed. Saved login state is also a secret (see `playwright.md`).
- Fixed reference data (product catalogue, plan names) should be seeded and versioned with the tests, so a data change shows up in review.

### Flakiness control

A flaky test passes and fails on the same code. It is a defect in the test, the product or the environment. Never retry until green and never report a retry-passed test as `pass`.

#### Common causes and fixes

| Cause | Symptom | Fix |
|---|---|---|
| Fixed sleeps or manual waits | Passes on fast machines, fails on slow ones | Wait on an observable condition with an auto-retrying assertion; never `sleep` |
| Asserting before the UI is ready | "Element not found" intermittently | Use web-first assertions that retry until the condition holds |
| Shared data between tests | Fails when run in parallel or in a different order | Unique data per test; no dependence on another test's rows |
| Order dependence | Passes alone, fails in the suite | Each test creates its own preconditions |
| Brittle locators | Breaks on a styling change | Use role, label and test-ID locators (see `playwright.md`) |
| Animation and transitions | Clicks land on a moving target | Wait for the stable state; reduce motion in the test environment if the project supports it |
| Third-party latency | Random timeouts | Stub or use a sandbox |
| Environment load | Failures only on CI | Fewer workers on CI, resource limits, fixed browser versions |
| Time-dependent logic | Fails near midnight or month end | Control the clock in the application's test mode; set the time zone |
| Real network in the journey | Timeouts, rate limits | Stub external calls at the network layer |

#### Detecting flakiness

- Run each new test several times: Playwright offers `npx playwright test --repeat-each 3` (three consecutive runs is the project's bar for new tests; use a larger number, such as 10, for a test you suspect).
- Run the whole suite with workers enabled and with `--workers=1`; a test that passes only one way has hidden shared state.
- Use the runner's own classification: Playwright reports a test that failed and then passed on retry as flaky, and `--fail-on-flaky-tests` makes the run fail when any test is flagged flaky.
- Keep retries low on CI (commonly 1 or 2) as a signal, not a cure. Capture a trace on the first retry so a flake leaves evidence (see `playwright.md`).

#### Handling a flaky test

1. Reproduce it: repeat the test until it fails, keep the trace, note the exact command.
2. Classify the cause: test defect, product defect (a real race), or environment.
3. Fix the cause. A test defect is fixed in the test. A real race is a product defect: report it with the reproduction.
4. If it cannot be fixed now, quarantine it under the rules in `regression-testing.md`: that needs user approval, an owner and an expiry. Do not silently skip it.

### Failure evidence

A failing end-to-end test must leave enough to diagnose without a rerun: the exact command, the full error, a trace or screenshot, and the data identifiers used. Configure the runner to keep this on failure (for Playwright, a trace on the first retry and the HTML report as a CI artefact). Report the evidence under `Evidence`, with reproduction steps for every `fail`.

### Scope limits

- Visual and cross-browser coverage is a decision: the default is one browser unless a criterion names others. Do not multiply the suite across browsers without a stated reason.
- Performance, load and accessibility audits are separate concerns. For accessibility rules, load `frontend-engineering`; for load and performance measurement, use the project's own tooling (this skill does not cover it).
- If end-to-end runs exceed 5 minutes for the task's tests, tell the coordinator and propose narrowing or sharding.

### Routing to other skills

For doubles and stand-ins, load `test-driven-development`. For security testing of a journey (sessions, access control), load `security-engineering`. For CI setup and environments, load `devops-deployment`. For UI behaviour and accessibility, load `frontend-engineering`.

## Examples

### Filled-in journey spec

```text
Journey: Add to cart, pay, see confirmation
Environment: local app on http://127.0.0.1:3000, payment stand-in on port 4010
Preconditions (created by fixture, via API): product "Test Mug" (stock 5), account
  "shopper-<run-id>@example.com" with a saved test card
Steps: open product, add to cart, check out, submit payment
Expected: order confirmation page shows order number; stock is 4; confirmation email
  captured by the mail stand-in
Teardown: delete order and account by id
Out of scope here (lower levels): coupon rules, tax rounding, card-number validation
```

### Bad to good: fixed wait to observable condition (Playwright)

Bad:

```ts
await page.getByRole('button', { name: 'Pay' }).click();
await page.waitForTimeout(3000);
expect(await page.getByText('Order confirmed').isVisible()).toBe(true);
```

Good: the web-first assertion retries until the condition holds or the timeout expires.

```ts
await page.getByRole('button', { name: 'Pay' }).click();
await expect(page.getByRole('heading', { name: 'Order confirmed' })).toBeVisible();
```

### Bad to good: shared account to per-test data

Bad: every test logs in as `testuser@example.com` and edits the same profile; parallel runs overwrite each other.

Good: a fixture creates `user-<unique>@example.com` through the API before the test and deletes it after; the test never touches a shared record.

### Flake triage record (task file or report)

```text
Test: checkout.spec.ts "shopper sees confirmation"
Observed: failed 2 of 20 runs (--repeat-each 20), passed on retry in CI
Trace: playwright-report/data/<run>.zip, failure at click on "Pay": element detached
Cause: product bug, the pay button re-renders after the totals request returns
Action: reported to implementer as a defect with the trace; test left as is (not retried to green)
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| End-to-end test for every rule | Slow, flaky suite for evidence lower levels give cheaper | Keep a short list of critical journeys; push the rest down |
| Running against a shared or production-like environment with real data | Data loss, privacy exposure, nondeterminism | Local or dedicated test environment with fake data only |
| Sleeping instead of asserting a condition | Slow and still flaky | Auto-retrying assertions on an observable state |
| Shared mutable account | Parallel and repeated runs collide | Unique data per test or per worker |
| Retrying until green | Hides flaky tests and real races | Treat flakiness as a defect; use retries only as a signal |
| Clicking through the UI to build preconditions | Longer, more fragile tests | Create preconditions through an API or seed |
| Live third parties inside the journey | External outages fail your suite | Stub or sandbox them |
| No evidence on failure | Failures cannot be diagnosed | Keep a trace, report and exact command |
| Testing in all browsers by default | Multiplies cost without a criterion | Decide browsers from the criteria |

## Checklist

- [ ] Each end-to-end test maps to a critical journey recorded with its reason.
- [ ] The test runs only against a local or dedicated test environment with test data.
- [ ] Preconditions are created per test, by API or seed, with unique data.
- [ ] No test depends on another test's data or on execution order.
- [ ] Third-party services are stubbed or sandboxed; no live call is made.
- [ ] No fixed sleeps; every wait is on an observable condition.
- [ ] The test passed 3 consecutive runs, and also with a single worker.
- [ ] A failure leaves a trace or screenshot, the command and the data identifiers.
- [ ] Test-account credentials come from the environment and are not printed or committed.
- [ ] Any quarantined test follows `regression-testing.md` and has user approval.

## Verify with context7 and gh_grep

- **context7:** check for the project's Playwright version: "Playwright `webServer` config", "Playwright `--repeat-each` and `--fail-on-flaky-tests`", "Playwright retries and the flaky test category", "Playwright `page.route` to stub requests", and the project's own end-to-end runner if it is not Playwright.
- **gh_grep:** search literal code: `reuseExistingServer`, `fullyParallel: true`, `retries: process.env.CI`, `page.route('**/`, `test.describe.configure({ mode: 'parallel' })`.

## Sources

- [Playwright: Best Practices](https://playwright.dev/docs/best-practices), read 2026-11-26.
- [Playwright: Test retries](https://playwright.dev/docs/test-retries), read 2026-11-26.
- [Playwright: Authentication](https://playwright.dev/docs/auth) (one account per worker), read 2026-11-26.
- [Playwright: Continuous Integration](https://playwright.dev/docs/ci), read 2026-11-26.
- `--repeat-each`, `--fail-on-flaky-tests` and `--workers` were confirmed from `npx playwright test --help` on @playwright/test 1.65.1, 2026-11-26.
