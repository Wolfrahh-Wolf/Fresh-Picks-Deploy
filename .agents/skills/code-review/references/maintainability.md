# Maintainability

How to judge readability, complexity, duplication, naming, dead code and test quality in a change, and when each one is a reportable finding rather than a preference; language-neutral, with JavaScript and Python examples; checked 2026-11-26.

## Contents

- What makes a maintainability finding reportable
- Complexity
- Readability and naming
- Comments and documentation in code
- Duplication
- Scope and over-engineering
- Dead code and leftovers
- Test quality
- Rating maintainability findings

## Guidance

### What makes a maintainability finding reportable

The reviewer reports defects and real risks, not personal style. A maintainability finding needs a concrete way it goes wrong:

| Reportable | Not reportable |
|---|---|
| A misleading name that will make a caller pass the wrong argument | A name you would have spelled differently |
| A function so tangled that the bug in it is hard to see (and you found one) | A function longer than you like, with no defect and no mandate |
| Two copies of a rule that already disagree | Two similar lines that serve different purposes |
| A test that cannot fail | A test that is merely different from how you would write it |
| A comment that states the opposite of the code | A comment you consider unnecessary |
| A style rule the project's linter or style guide mandates and the change breaks | A formatting preference the project has not adopted |

Project conventions and the project's linter configuration beat your defaults. If the linter passes and the code follows the surrounding code, leave it alone. For language idiom questions and refactoring technique, load `languages-clean-code`.

### Complexity

Complexity is a risk because every extra path is a place for a defect and a cost to the next editor. Look at the line, function and module levels.

Heuristics, not laws. A project's own thresholds win.

| Signal | Rough trigger for a closer look |
|---|---|
| Function length | Longer than about 50 lines or does not fit on one screen |
| Nesting depth | More than 3 levels of `if`, loop or callback |
| Branches in one function | More than about 10 independent paths |
| Parameter count | More than about 5, or several booleans in a row |
| Boolean flag parameters | A flag that switches the function between two jobs |
| Shared mutable state | Module-level variables, long-lived objects mutated from many places |
| Hidden coupling | Behaviour depends on call order, global configuration or implicit environment |

When a signal fires, ask the useful question: **can I explain what this does, and convince myself it is right, in under a minute?** If not, describe where you got lost. A finding that says "line 120 mixes validation, persistence and notification, so the error on line 134 skips the audit write" is actionable. "This function is too long" is not.

Prefer the smallest suggested change: extract the one branch that hides the defect, return early to flatten nesting, replace a flag with two named functions. Do not propose a redesign for a `low` finding.

### Readability and naming

- **Names carry meaning.** A name should say what a thing is or does without being unwieldy. Check: does the name match what the code actually does after this change (a function called `getUser` that now also creates one)? Are units in the name when they matter (`timeoutMs`)? Are two different things given the same name, or one thing two names?
- **Boolean and negation.** `if (!isNotDisabled)` is a defect factory. Prefer positive names for conditions.
- **Magic values.** A bare `86400` or `"pending"` repeated in several places should be one named constant, or the project's enum, so the next change cannot update one copy only.
- **Consistency.** Follow the surrounding code unless it is unsafe. A new pattern for an existing job (a second way to read configuration, a second error type) needs a reason; otherwise report it as `low` with the existing pattern named.
- **Control flow clarity.** Early returns for guards, no else-after-return noise, no deeply chained ternaries, no clever one-liners that hide a side effect.
- **Types and contracts.** In typed code, check for `any` or unchecked casts at the new boundary; in untyped code, check the function states what it accepts and returns where the project does that by convention.

### Comments and documentation in code

- Comments should explain **why** (a constraint, a trade-off, a non-obvious requirement), not restate **what** the next line does.
- A comment that contradicts the code is a finding: someone will trust the comment.
- Commented-out code and notes promising later work with no tracked issue are leftovers; report them as `low` unless they hide a known defect.
- Public functions, routes and configuration the change introduces should be documented where the project documents them. Missing or inaccurate documentation is reported with the owner from the `AGENTS.md` source-of-truth table.
- API documentation is separate from comments: for API docs, load `technical-documentation`.

### Duplication

Duplication is a problem when copies must change together and one gets missed.

- Search the code for a distinctive line or constant from the new code (`git grep -n "<distinctive string>"`). If the same rule exists elsewhere, find out whether the copies already differ.
- Report duplication as `medium` when the copies disagree today, or when the rule is a business rule, a validation or a permission check. Report as `low` when it is incidental similarity.
- Do not demand abstraction for two small look-alike blocks. Three real uses and a stable shape justify an abstraction; fewer usually do not.
- A new helper that re-implements something the project or its dependencies already provide is a finding: name the existing one.

### Scope and over-engineering

- **Scope creep.** Unrelated refactors, formatting sweeps or renamed files mixed into a functional change make the diff hard to review and hard to revert. Report as `low`, and say which hunks are unrelated. Do not demand the author revert them unless they hide the real change.
- **Over-engineering.** Generality the system does not need today (plug-in points with one implementation, configuration for values that never change, abstract layers with one caller) is a cost without a benefit. Report with the simplest alternative.
- **Under-engineering at a boundary.** A quick hack at a trust or module boundary (unvalidated input, a global used as a message bus) costs more than elsewhere; rate it by what it can break.
- **New dependency.** Adding or majorly upgrading a dependency needs user approval under `AGENTS.md`. Flag any new entry in the manifest, say what it is used for, and ask whether the standard library or an existing dependency covers it. For supply-chain depth, load `security-engineering`.

### Dead code and leftovers

Look for: unused exports or parameters introduced by this change, unreachable branches after a refactor, debug output, disabled tests, a feature flag with no off path, temporary files and local paths in the diff. Skipped or disabled tests are never acceptable as a way to make a task pass; report them at least `high` if the skipped test covered an acceptance criterion.

### Test quality

Tests are code and carry the same risks, plus one more: they can give false confidence. For each new or changed behaviour ask: **would a test fail if this behaviour broke?** Check it with a thought experiment: delete the line, invert the condition or return a constant, and see whether any test notices.

| Smell | Why the test cannot fail | What to ask for |
|---|---|---|
| Asserts only that a value is defined or that nothing threw | Almost any output passes | Assert the specific expected value or effect |
| Asserts on a mock that the test itself configured | The test only checks its own setup | Assert on observable behaviour, mock only the boundary |
| Assertion inside a callback or promise the test does not wait for | The test finishes before the assertion runs | Await the operation; assert after it |
| Snapshot of a large object | Any change is "accepted" without reading | Targeted assertions on the fields that matter |
| Expected value computed by the same logic as the code | Wrong logic is confirmed by itself | Hard-code expected values from the requirement |
| Test depends on order, clock, randomness or network | Passes or fails by luck | Control time and randomness; isolate state |
| `sleep` to wait for async work | Flaky and slow | Wait on the condition, not on time |
| One test with many unrelated assertions | A failure does not say what broke | Split by behaviour |
| Skipped, focused (`only`) or commented-out tests | Silent loss of coverage | Remove the skip or the `only`; explain any skip |

Also check:

- Every acceptance criterion has at least one test that exercises it; list those that do not.
- Failure paths and boundaries are tested, not just the happy path.
- Test names describe the behaviour, so a failure reads as a sentence.
- Changed behaviour changed the tests; a green suite after a behaviour change with no test edits is suspicious.
- No test was weakened, deleted or loosened to pass. This is never acceptable; report it as `high`.

You judge adequacy; you do not write the tests. For strategy depth (what to test at which level), load `testing-strategy`. For writing test-first or designing doubles, load `test-driven-development`.

### Rating maintainability findings

| Severity | Typical case |
|---|---|
| `high` | A weakened, skipped or non-failing test covering an acceptance criterion; duplicated rule already diverged and causing wrong behaviour |
| `medium` | Misleading name or comment likely to cause misuse; untested failure path; duplicated business rule not yet diverged |
| `low` | Readability, naming, dead code, minor duplication, scope creep, missing nit-level documentation |

A pure maintainability finding is rarely `high` or `critical`. If you want to rate one that high, check whether the real issue is a correctness defect and report it under correctness.

## Examples

### Misleading name (reportable) versus preference (not reportable)

```js
// Reportable: the name says "get" but the call writes, so a read-only caller changes data
async function getOrCreateCart(userId) { /* inserts when missing */ }
// Used in a GET handler: GET /cart now writes a row for every visitor.
```

```js
// Not reportable: a working, consistent name you would spell differently
const userList = await loadUsers();   // project uses "List" suffix everywhere
```

### Test that cannot fail (bad to good)

```js
// Bad: passes for any non-throwing implementation
test("applies discount", async () => {
  const total = await priceOrder(order, "SAVE10");
  expect(total).toBeDefined();
});
```

```js
// Good: expected value comes from the requirement, not from the code
test("SAVE10 takes 10 percent off the item subtotal, not the shipping", async () => {
  const order = { items: [{ priceCents: 10000 }], shippingCents: 500 };
  expect(await priceOrder(order, "SAVE10")).toBe(9500);
});
```

### Complexity finding with a concrete consequence

```
[medium] Error branch skips the audit write
Location: src/billing/refund.js:88
Problem: refund() mixes validation, the provider call, persistence and audit logging in one 140-line function with five nested levels; the early return on line 104 exits before the audit write on line 131.
Failure scenario: a refund rejected by the provider returns at line 104; no audit row is written, so the rejected attempt is missing from the audit trail required by docs/ARCHITECTURE.md. Introduced by this change.
Recommendation: move the audit write into a finally block or into a small recordAttempt() called from every exit.
```

### Scope creep (low)

```
[low] Unrelated formatting changes hide the functional change
Location: src/orders/ (14 files)
Problem: 11 of the 14 changed files contain only whitespace and import reordering.
Failure scenario: a future revert of this feature also reverts the formatting, and blame on those lines points to this change.
Recommendation: keep formatting in a separate change, or list the three functional files in the description.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Filing style preferences as findings | Noise hides real defects and wastes the author's time | Report only mandated rules and misleading code |
| "Too complex" with no location or consequence | The author cannot act on it | Name the line where you got lost and what it hides |
| Demanding abstraction for two similar blocks | Premature abstraction costs more than a copy | Report duplication only when copies diverge or carry rules |
| Trusting a green suite | Tests may not be able to fail | Run the delete-the-line thought experiment |
| Ignoring tests that were edited | Weakened assertions pass the gate quietly | Diff test files as carefully as source |
| Inflating a readability issue to `high` | Blocks completion for no defect | Reserve `high` for defects and lost coverage |
| Writing the tests or the fix yourself | Reviewers never edit; independence is lost | Describe the missing test and the smallest fix |
| Ignoring project conventions | Findings contradict the codebase | Read surrounding code and linter configuration first |

## Checklist

- [ ] Each maintainability finding names a concrete way it will go wrong, or was dropped.
- [ ] The project's linter configuration and surrounding code were checked before any style comment.
- [ ] Functions that grew past the project's complexity thresholds were looked at for a hidden defect.
- [ ] Names, comments and types in the diff match what the code now does.
- [ ] Copies of any business rule, validation or permission check were searched for and compared.
- [ ] Unrelated hunks in the diff are identified as such.
- [ ] Any new manifest dependency is flagged for approval with its purpose.
- [ ] Each new or changed behaviour has a test that would fail if it broke.
- [ ] No test was skipped, focused, loosened or deleted to pass.
- [ ] Acceptance criteria with no test are listed.

## Verify with context7 and gh_grep

- **context7:** for the test framework and linter in the manifest, query "`<framework>` async assertion awaiting and `rejects` matcher", "`<framework>` skip and only behaviour in CI", "`<linter>` rule `<rule-name>` default and options", "`<language>` style guide naming rules for `<construct>`".
- **gh_grep:** search literal code for smells and conventions in maintained repositories: `test.only(`, `it.skip(`, `expect(`, `toBeDefined()`, `await expect(`, `.rejects.toThrow(`, `no-floating-promises`.

## Sources

- Google Engineering Practices, "What to look for in a code review" (complexity, over-engineering, tests, naming, comments, style, consistency, documentation): https://google.github.io/eng-practices/review/reviewer/looking-for.html
