# Test Pyramid

Level selection, risk-based allocation and anti-patterns for choosing unit, integration and end-to-end tests; runner-neutral, with examples for Vitest 5.1, Jest 30.5, pytest 9.2 and Playwright 1.65 (checked 2026-11-26). The project's own manifest and existing conventions win over anything here.

## Contents

- Level selection
- Cost of evidence
- Risk-based allocation
- Mapping criteria to levels
- Suite shape and budgets
- Anti-patterns
- Routing to other skills

## Guidance

### Level selection

Choose the lowest level where the failure you care about can actually appear. Walk down this table and stop at the first row that fits.

| The behaviour is... | Level | Why |
|---|---|---|
| Pure logic: calculation, parsing, validation, state transition, formatting | Unit | No I/O is needed; failures point at one function. |
| A module that talks to a database, queue, file system or another process, where the interaction is the risk (queries, transactions, serialisation, migrations) | Integration | A fake would hide exactly the defect you want to catch. |
| An HTTP or RPC boundary: status codes, error shape, auth scope, schema | Integration (API level) | Faster and more stable than driving a browser to reach the same code. |
| A user journey across several screens or services whose value is the whole chain | End-to-end | Only the full chain can show wiring, routing, session and rendering faults. |
| Layout, visual appearance, cross-browser rendering | End-to-end or visual test | Only a real browser renders it. |

Decision rules:

1. If a unit test can fail for the same reason, do not write the higher-level test for that reason.
2. If the defect lives in the wiring (configuration, serialisation, SQL, headers, routes), a unit test with a fake cannot catch it; go up one level.
3. Add an end-to-end test only for a journey whose breakage would stop users or lose money or data. One happy path per journey is the default; push error and edge cases down to unit and integration.
4. When one criterion needs two levels (for example a rule plus its wiring), write the fast one first and the slow one second, and keep the slow one minimal.

### Cost of evidence

Think of each test as buying evidence. Price it by feedback time, stability and diagnosis effort.

| Level | Typical feedback | Stability | Diagnosis | Use for |
|---|---|---|---|---|
| Unit | milliseconds per test | very high | the failing line is nearby | most rules and branches |
| Integration | tens of milliseconds to seconds | high if isolated | one boundary to inspect | boundaries and data handling |
| End-to-end | seconds per test | lowest; most exposed to timing and environment | many layers to inspect | a few critical journeys |

A slow, flaky test costs more than it proves. If an end-to-end test fails once in twenty runs, the team learns to ignore red; treat that as a defect (see `e2e-testing.md`).

### Risk-based allocation

Spend test effort where a failure hurts most. Score each changed behaviour on two axes and allocate paths accordingly.

| Impact if wrong | Likelihood of defect | Effort |
|---|---|---|
| High (money, data loss, access control, legal, irreversible) | High (new, complex, many branches, recently buggy) | Success, boundary, invalid, permission, failure and concurrency paths at unit and integration, plus one end-to-end journey |
| High | Low (small, well-understood, already covered) | Existing coverage plus one regression check at the boundary |
| Low (label, copy, ordering, cosmetic) | High | One or two unit or component checks |
| Low | Low | No new test; note the decision in the report |

Signals that raise likelihood: code written under pressure, many conditionals, date and time arithmetic, money arithmetic, parsing user input, concurrency, a dependency upgrade, areas with prior regressions.

Signals that raise impact: payments, authentication, authorisation, personal data, migrations, anything in the `AGENTS.md` high-risk list. For high-risk changes the security-auditor reviews separately; for security test design, load `security-engineering`.

### Mapping criteria to levels

Write the mapping before any test. One row per acceptance criterion; the test name is filled in once the test exists.

| # | Criterion | Level | File | Paths to cover |
|---|---|---|---|---|
| 1 | Coupon `SAVE10` takes 10% off the cart total | Unit | `tests/pricing.test.ts` | valid code, no code, zero total, rounding |
| 2 | Expired coupon is rejected with `COUPON_EXPIRED` | Unit | `tests/pricing.test.ts` | expiry boundary (day before, day of, day after) |
| 3 | Applied coupon is persisted with the order | Integration | `tests/orders.integration.test.ts` | row written, rolled back on payment failure |
| 4 | Shopper sees the reduced total at checkout | End-to-end | `e2e/checkout.spec.ts` | one journey: add item, apply code, see total |

If a criterion cannot be placed in any row, it is untestable or ambiguous: escalate.

### Suite shape and budgets

The classic pyramid (many unit, fewer integration, very few end-to-end) is a default, not a law. Match the shape to the architecture:

- Logic-heavy library or service core: pyramid, with the weight on unit tests.
- Thin service over a database (CRUD with little logic): more integration tests, fewer unit tests, because the logic is mostly queries and mapping.
- UI-heavy front end: component tests plus a small end-to-end set; do not test every component state through the browser.
- Many small services: contract-level integration tests per boundary plus a very small cross-service end-to-end set.

Budgets that keep the suite useful (the tester definition sets the unit limit; the others are practical starting points, so the project's own numbers win):

- Unit suite: under 60 seconds in total. Justify any single test that needs longer.
- Integration suite: minutes at most; run it in the default test command only if it stays fast, otherwise give it its own command and name it in `AGENTS.md` and the README.
- End-to-end suite: small enough to run on every pull request; if it exceeds roughly 10 minutes, shard it or cut tests, do not skip them.
- Escalate to the coordinator when a required test run would exceed 5 minutes.

### Anti-patterns

| Name | Symptom | Effect |
|---|---|---|
| Ice-cream cone | Many end-to-end tests, few unit tests | Slow, flaky feedback; failures are hard to localise |
| Hourglass | Unit and end-to-end tests, nothing in between | Wiring defects reach production; end-to-end carries the load |
| Mirror test | Test repeats the implementation's logic or pastes its output as the expectation | Passes by construction; proves nothing |
| Over-mocked unit test | Every collaborator is replaced, assertions check calls | Refactors break it; real defects pass; load `test-driven-development` for doubles |
| Same check at three levels | Unit, integration and end-to-end all assert the same rule | Triple maintenance for one signal |
| Coverage chasing | Tests added to move a number | Low-value tests, false confidence; see `test-coverage.md` |
| Snapshot sprawl | Large snapshots approved without reading | Regressions are accepted as "updated snapshots" |
| Shared fixtures with state | Tests depend on data left by earlier tests | Order dependence; failures that vanish when run alone |
| Retry until green | Retries mask failures | Flaky tests ship; red stops meaning anything |
| Testing the framework | Asserting that the library works | Cost without evidence about your code |

### Routing to other skills

For the test-first cycle, test doubles and fixtures, load `test-driven-development`. For security tests, load `security-engineering`. For pipeline setup, load `devops-deployment`.

## Examples

### Bad to good: moving a rule down a level

Bad: five end-to-end tests, each drives the browser to the checkout page to check a different coupon rule.

```ts
// e2e/checkout.spec.ts: slow, five browser sessions for one rule table
test('SAVE10 gives 10% off', async ({ page }) => { /* 40 lines of navigation */ });
test('expired code is rejected', async ({ page }) => { /* 40 lines of navigation */ });
test('negative total is rejected', async ({ page }) => { /* 40 lines of navigation */ });
```

Good: the rules are a table at unit level; one end-to-end test proves the page shows the result.

```ts
// tests/pricing.test.ts (Vitest 5.x)
import { describe, it, expect } from 'vitest';
import { discount } from '../src/pricing';

describe('discount', () => {
  it.each([
    { total: 100, code: 'SAVE10', expected: 90 },
    { total: 100, code: undefined, expected: 100 },
    { total: 0, code: 'SAVE10', expected: 0 },
  ])('total $total with code $code gives $expected', ({ total, code, expected }) => {
    expect(discount(total, code)).toBe(expected);
  });

  it('rejects a negative total', () => {
    expect(() => discount(-1, 'SAVE10')).toThrow(RangeError);
  });
});
```

```ts
// e2e/checkout.spec.ts (Playwright 1.65): one journey, minimal
import { test, expect } from '@playwright/test';

test('shopper sees the discounted total after applying a code', async ({ page }) => {
  await page.goto('/cart');
  await page.getByLabel('Coupon code').fill('SAVE10');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByTestId('cart-total')).toHaveText('$90.00');
});
```

### Filled-in allocation note (for the report)

```text
Change: coupon engine and checkout total display.
Risk: money arithmetic (high impact, medium likelihood: new rounding code).
Allocation: 9 unit cases (rules, rounding, boundaries), 2 integration cases
(persisted discount, rollback on payment failure), 1 end-to-end journey.
Not tested: coupon admin UI (unchanged, no criterion); reported as "not tested".
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Picking the level by habit ("we always do end-to-end") | Slow, flaky evidence for logic a unit test proves in milliseconds | Walk the level table and justify any level above unit |
| Writing only happy-path tests at the top level | Error and edge paths ship untested | Cover edge, invalid, permission and failure paths at unit or integration level |
| Equal effort everywhere | Low-risk code is over-tested, high-risk code under-tested | Score impact and likelihood; allocate paths by the table |
| Treating the pyramid as a quota | Suite shape ignores the architecture | Shape follows where the logic and the risk are |
| Skipping the criteria mapping | Criteria silently go unverified | Write the mapping table first and review it for gaps |
| Duplicating a check at several levels | Maintenance cost for no extra evidence | Keep the check at the lowest level that can fail for that reason |
| Letting suite time grow unchecked | Developers stop running tests | Hold the budgets; shard or delete low-value tests with approval |

## Checklist

- [ ] Every acceptance criterion has a row naming its level, file and paths.
- [ ] No higher-level test repeats a rule already proven at a lower level.
- [ ] Each end-to-end test covers a critical journey and has a stated reason.
- [ ] Effort is weighted by impact and likelihood, and the allocation is written down.
- [ ] High-risk behaviour has success, boundary, invalid, permission and failure paths.
- [ ] The unit suite runs in under 60 seconds, or the exception is justified in the report.
- [ ] Any criterion that is untestable or ambiguous was escalated, not guessed.

## Verify with context7 and gh_grep

- **context7:** confirm the project's runner and version before quoting any command: "Vitest `it.each` with object rows and `$name` interpolation", "Playwright `getByTestId` and `toHaveText`", "pytest `parametrize` argument names", "Jest `test.each` table syntax".
- **gh_grep:** search literal code to see how maintained projects split levels: `it.each([`, `@pytest.mark.parametrize(`, `test.describe(` together with `e2e/` paths, `*.integration.test.ts`, `testMatch:`.

## Sources

- [Playwright: Best Practices](https://playwright.dev/docs/best-practices), read 2026-11-26.
- [Vitest: Coverage guide](https://vitest.dev/guide/coverage), read 2026-11-26.
- [pytest: Good Integration Practices](https://docs.pytest.org/goodpractices.html), read 2026-11-26.
- The Vitest table example was executed against Vitest 5.1.2 on 2026-11-26; the Playwright checkout journey is illustrative and was not run against a real checkout page.
