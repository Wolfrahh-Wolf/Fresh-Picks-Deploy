# Refactoring

Code smells and small, behaviour-preserving refactoring techniques for JavaScript, TypeScript, Python, Java and C++, scoped to changes inside a task. Language-independent; examples use TypeScript and Python; checked 2026-11-26. Large multi-module refactoring belongs to `sdlc-workflows`; test design belongs to `test-driven-development`.

## Contents

- Rules of engagement
- Safety net
- Smell catalogue
- Techniques
- Review lens
- Stop conditions

## Guidance

### Rules of engagement

- A refactoring changes structure, not behaviour. If observable behaviour changes (outputs, errors, timing contracts, public signatures, logs that others parse), it is a feature or a fix and needs its own criteria.
- Stay in scope. Refactor only code the task touches. Report unrelated smells as follow-ups; do not fix them unasked, and do not reformat unrelated lines.
- One change per step. After each step the code compiles and the checks pass. Never carry a half-finished refactor between steps.
- Do not mix refactoring with behaviour changes in the same step. If you must do both, do the refactor first, verify, then change behaviour, so a failure points to one cause.
- Keep public API signatures, serialized shapes and error types unchanged unless the brief says otherwise. Changing them is a compatibility decision for the architect and may need approval.
- Prefer the editor's or tool's automated rename and extract operations; they update every reference. After a mechanical change, still search the code for string-based references (reflection, dynamic imports, configuration, templates).
- If the same refactor attempt fails verification twice, stop and report. Do not keep trying variations.

### Safety net

- Before the first edit, run the project's tests, type-check and lint, and record the baseline, including pre-existing failures.
- Confirm the tests cover the code you will change: search for tests that call it and read what they assert. A passing suite that never executes the code proves nothing.
- If coverage is missing, stop and report to the coordinator. Characterization tests that pin current behaviour come first; load `test-driven-development` for how to write them. Do not refactor untested code on faith.
- Never weaken, skip or delete a test to make a refactor pass. A test that fails after a refactor has found a behaviour change; fix the code.
- Type systems help: tighten types after structure is stable, not during.

### Smell catalogue

| Smell | Signal | Technique |
|---|---|---|
| Long function | Does several things; needs scrolling or comments to separate phases | Extract function; decompose conditional |
| Duplicated code | Same logic in two or more places, edited together | Extract function; parameterise differences; wait for three uses before abstracting |
| Deep nesting | Many levels of `if` and loops | Guard clauses; extract function |
| Long parameter list | More than three or four parameters; callers pass the same group | Introduce parameter object; replace flags with separate functions |
| Boolean flag parameter | `render(page, true)` | Split into two named functions or use an enum |
| Magic numbers and strings | Unexplained literals in logic | Named constant or enum |
| Primitive obsession | Strings or numbers standing in for domain concepts (`email`, `money`) | Small value type with validation |
| Feature envy | A function mostly reads another object's fields | Move function to the data's owner |
| Data clump | The same fields travel together | Introduce a type for them |
| Large class or module | Several unrelated groups of members | Extract class or module along reasons to change (see [solid.md](solid.md)) |
| Divergent change | One class edited for many unrelated reasons | Split by reason to change |
| Shotgun surgery | One change needs edits in many files | Move related code together |
| Switch on type tag repeated | Same `switch` or `if` chain in several places | Polymorphism or handler table, only if variants keep growing |
| Temporary field or output parameter | State used only in some paths | Return values; extract the path |
| Speculative generality | Hooks, abstract classes or parameters with no current use | Remove them (YAGNI) |
| Dead code | Unused functions, branches, flags, parameters, commented-out code | Delete it; version control keeps history |
| Comments explaining what | A comment restates opaque code | Rename or extract so the code says it |
| Mutable shared state | Globals or fields changed from many places | Pass values in, return new values, narrow scope |
| Message chains | `a.getB().getC().getD()` | Hide the chain behind a method on the first object |
| Inconsistent naming | Several words for one concept | Rename to one term across the code |

### Techniques

- **Rename**: the cheapest, highest-value change. Rename for intent using the domain's words. Use the tool's rename so all references change.
- **Extract function**: take a coherent block, give it a verb name and pass in what it reads; return what it produces. Extract when you would otherwise write a comment above the block.
- **Inline function**: reverse of extract when the body is as clear as the name, or when a layer adds nothing.
- **Extract variable**: name a complex sub-expression (`isEligible = age >= 18 && !suspended`).
- **Guard clauses**: handle invalid and trivial cases first with early return or throw; the main path then stays unindented.
- **Decompose conditional**: move long condition and branch bodies into named functions.
- **Introduce parameter object**: replace a recurring group of parameters with one type.
- **Replace magic value with constant** or enum.
- **Replace flag argument with separate functions**.
- **Move function or field** to where the data lives.
- **Replace loop with pipeline**, but only when the pipeline reads more clearly than the loop; keep loops for early exits, side effects or complex state.
- **Separate query from modifier**: a function that returns a value should not also change state.
- **Replace primitive with value object**: a small immutable type that validates in its constructor.
- **Remove dead code**: delete, do not comment out. Verify it is dead by searching for references, including dynamic ones and public API consumers.
- **Replace inheritance with composition** when a subclass overrides most of its base or breaks substitution.
- **Pull up or push down only with a clear shared contract**; do not create hierarchies for code reuse.
- Order of work: rename first, then extract, then move, then simplify conditionals, then remove duplication. Each is independently verifiable.
- When a technique needs a new dependency, new framework or a new layer of abstraction, it is no longer a small refactor; stop and report.

### Review lens

- The reviewer checks that the refactor is behaviour-preserving: compare old and new logic branch by branch, check that tests still cover the moved code, and confirm that no public signature, serialized shape or error type changed.
- Common behaviour changes hiding in refactors: reordered side effects, changed evaluation order or short-circuiting, different rounding or integer types, a default that moved, error messages or types that changed, a `finally` or cleanup that no longer runs, an async call that is no longer awaited, and a mutated argument that is now copied (or the reverse).
- Report a maintainability finding only with a concrete scenario: a specific upcoming change that now requires edits in N places, a duplicated rule that has already diverged, or a readability problem that caused a bug. Rate smells as `low` or `medium`; they do not block unless they cause a defect.
- Separate introduced smells from pre-existing ones, and say which are out of scope.
- Flag an unrelated reformatting or opportunistic cleanup in the diff as scope creep.

### Stop conditions

- No test covers the area and none can be added within scope: report and ask.
- The refactor needs a public API change, a data migration or a dependency change: report and ask for approval.
- The change spans several modules or needs a staged plan: stop and ask for the `sdlc-workflows` refactoring procedure.
- Two verification failures in a row: stop, mark blocked and give the options.

## Examples

Guard clauses and extract function, bad to good (TypeScript):

```ts
// Bad: nested, mixed concerns.
function shippingLabel(order: Order): string {
  if (order) {
    if (order.address) {
      if (order.items.length > 0) {
        const lines = [];
        for (const item of order.items) lines.push(`${item.qty} x ${item.name}`);
        return `${order.address.city}\n${lines.join("\n")}`;
      } else {
        throw new Error("empty order");
      }
    } else {
      throw new Error("missing address");
    }
  }
  throw new Error("missing order");
}

// Good: same behaviour, same error messages, same order of checks.
function shippingLabel(order: Order | undefined): string {
  if (!order) throw new Error("missing order");
  if (!order.address) throw new Error("missing address");
  if (order.items.length === 0) throw new Error("empty order");
  return `${order.address.city}\n${itemLines(order.items).join("\n")}`;
}

function itemLines(items: readonly OrderItem[]): string[] {
  return items.map((item) => `${item.qty} x ${item.name}`);
}
```

Behaviour changed while "refactoring" (what a reviewer should catch):

```python
# Before
def total(prices):
    result = 0
    for p in prices:
        if p < 0:
            raise ValueError("negative price")
        result += p
    return result

# After: shorter, but a generator argument is consumed by any(), so sum() sees
# nothing and returns 0 instead of the real total.
def total(prices):
    if any(p < 0 for p in prices):   # consumes a generator input
        raise ValueError("negative price")
    return sum(prices)               # sees an exhausted generator
```

Replace flag argument and magic value (TypeScript):

```ts
// Before
function sendEmail(user: User, urgent: boolean) {
  const retries = urgent ? 5 : 1;
  // ...
}
sendEmail(user, true);

// After
const URGENT_RETRIES = 5;
const NORMAL_RETRIES = 1;

function sendUrgentEmail(user: User) { return deliver(user, URGENT_RETRIES); }
function sendNormalEmail(user: User) { return deliver(user, NORMAL_RETRIES); }
function deliver(user: User, retries: number) { /* ... */ }
```

A worked sequence for a long function (each step verified by the test suite before the next):

```text
1. Run the tests and record the baseline: 142 passed, 0 failed.
2. Rename variables d -> invoiceDate, f -> isOverdue. Run tests.
3. Extract calculateLateFee(invoice) from lines 40-62. Run tests.
4. Replace the nested conditionals at the top with guard clauses. Run tests.
5. Replace the literal 0.015 with LATE_FEE_RATE. Run tests.
6. Self-review the diff: no signature, message or ordering change. Report.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Refactoring with no tests around the code | No evidence behaviour survived | Stop and get characterization tests first |
| Mixing a fix or feature into the refactor | A failure has two possible causes; review is harder | Separate steps, verified individually |
| Reformatting unrelated files | Noisy diff hides real changes; scope creep | Touch only the code in scope |
| Extracting an abstraction after one use | Wrong abstraction costs more than duplication | Wait for three similar uses |
| Changing a public signature "while there" | Breaks callers and consumers silently | Treat as a compatibility change; ask |
| Replacing loops with long pipelines everywhere | Harder to read, harder to debug | Use a pipeline only when it is clearer |
| Deleting "dead" code without searching dynamic uses | Reflection, config or plugins still call it | Search code, config and docs first; check public API |
| Changing evaluation order or error timing | Subtle behaviour change | Keep order of checks and side effects |
| Deleting or loosening a failing test | Hides the behaviour change | Fix the code or report the discrepancy |
| Reviewer flagging style as a defect | Noise; no failure scenario | Drop it or file it as `low` with a scenario |

## Checklist

- [ ] Were tests, type-check and lint run and recorded before the first edit?
- [ ] Do existing tests execute and assert on the code being changed?
- [ ] Is each step independently verified before the next?
- [ ] Is the refactor free of behaviour changes (outputs, errors, ordering, side effects)?
- [ ] Are public signatures, serialized shapes and error types unchanged?
- [ ] Did you search for string-based and dynamic references after renames and deletions?
- [ ] Is the diff limited to code in the task's scope, with no unrelated reformatting?
- [ ] Are dead code and commented-out code deleted rather than disabled?
- [ ] Were all tests, lint, type-check and build re-run after the final step?
- [ ] Did you stop and report where a public API change, new dependency or multi-module change was needed?
- [ ] For reviews: does each maintainability finding carry a concrete scenario and a severity?

## Verify with context7 and gh_grep

- **context7:** refactoring technique itself needs no library lookup. Query the documentation of language features you introduce while refactoring, at the project's version (for example "TypeScript `readonly` arrays and `satisfies`", "Python `dataclass` `frozen` and `slots`", "Java records compact constructor", "C++ `std::span`"), and the rename or code-action support of the project's tooling.
- **gh_grep:** search literal code to confirm idioms: `if (!order) throw`, `@dataclass(frozen=True`, `const [A-Z_]+ = ` constants next to the code that uses them, `Object.freeze(`. Use results as evidence only; do not copy code without a compatible licence.

## Sources

- None. This file is original practitioner guidance; no external specification or version-dependent documentation applies to it.
