# SOLID, Naming and Cohesion

SOLID applied with concrete examples, including when not to apply it, plus naming and cohesion rules, for object-oriented and mixed-paradigm code in JavaScript, TypeScript, Python, Java and C++. Language-independent design guidance; no version dependency; checked 2026-11-26. Project conventions and `docs/ARCHITECTURE.md` win over every default here.

## Contents

- How to use SOLID
- Single responsibility
- Open and closed
- Liskov substitution
- Interface segregation
- Dependency inversion
- When not to apply SOLID
- Naming
- Cohesion and coupling

## Guidance

### How to use SOLID

- SOLID is a set of questions to ask when code is hard to change, not a checklist to satisfy. Apply a principle only when you can name the concrete change that is currently painful.
- Implementer: apply it to the code you are already changing. Reviewer: raise a finding only with a failure scenario (a specific change request that now requires edits in several places, or a substitution that breaks callers). "Violates SRP" alone is not a finding.
- System-level structure (layers, hexagonal, modules) is owned by `system-architecture`. Named design patterns are covered there too. This file stays at class, function and module level.

### Single responsibility

- A unit (function, class, module) should have one reason to change, meaning one actor or concern whose requirements drive edits. It is not "does one thing" in the smallest sense.
- Test: list the reasons the unit might change (pricing rules, persistence format, email wording). More than one independent reason means a split candidate.
- Split along the seams of change, not by line count. A 200-line function that always changes together may be fine; a 30-line function mixing parsing, business rules and I/O is not.
- Typical split: parse or validate input, apply the rule, perform the side effect. Keep the rule pure so it is easy to read and test.

### Open and closed

- Open for extension, closed for modification: when a new variant arrives, you add code rather than edit tested code in many places.
- Use it when a switch over a type tag is duplicated in several places and variants keep growing. Replace with polymorphism, a lookup table of handlers or a strategy.
- Do not use it for a stable two-case decision. A single `if` or one `switch` in one place is clearer than an interface plus two classes.
- In languages with closed unions (TypeScript discriminated unions, Java sealed types), a single exhaustive `switch` per operation is often better than classes: the compiler flags every place a new variant must be handled. Choose by what grows: new variants favour polymorphism; new operations favour unions plus `switch`.

### Liskov substitution

- Any subtype must work wherever its base type is expected, without callers knowing. Preconditions may not be strengthened, postconditions may not be weakened, invariants must hold, and thrown error types must stay compatible.
- Red flags: a subclass that throws `UnsupportedOperationException` or `NotImplementedError` for an inherited method; overrides that ignore arguments; callers that check `instanceof` before calling; a mutable `Square` extending `Rectangle`.
- Fix by changing the hierarchy: prefer composition, split the base into smaller interfaces, or model the difference as data. Do not fix by adding type checks in callers.
- Read-only versus mutable is a common trap: a read-only collection must not extend a mutable one.
- In C++, never slice polymorphic objects by copying a derived object into a base value; pass references or pointers.

### Interface segregation

- Callers should not depend on methods they do not use. Prefer several small, role-specific interfaces to one wide one.
- Signal: implementers that stub out half the methods, or a test double that needs twenty methods to satisfy one caller.
- In TypeScript and Python, define the interface where it is consumed, with only the members the consumer needs (a `Protocol` or a structural type). In Java and C++, keep interfaces small and compose them.
- Do not split purely by count. Two methods that always change and are always used together belong in one interface.

### Dependency inversion

- High-level policy should not import low-level detail; both depend on an abstraction owned by the high-level side. In practice: pass the collaborator in (constructor injection) instead of constructing it inside.
- Use it at boundaries that vary or cost something: clocks, random numbers, file systems, networks, databases, third-party SDKs, and the places you need a fake in tests. For test design with doubles, load `test-driven-development`.
- Inject through constructors or function parameters. Avoid global singletons and service locators; they hide dependencies.
- Do not invert everything. An interface with one implementation and no boundary reason is noise. Depend directly on stable standard library types and on your own small pure helpers.
- Framework wiring (dependency-injection containers, decorators) belongs to `frontend-engineering` or `backend-engineering`.

### When not to apply SOLID

| Situation | Why to hold back | Do instead |
|---|---|---|
| One-off script, spike, or prototype | Structure costs more than it returns | Keep it flat and readable; note it is disposable |
| Only one implementation exists and no boundary needs a fake | A speculative interface adds a layer to read and maintain | Use the concrete type; extract the interface when a second use appears (rule of three) |
| Data-only objects (DTOs, records, config) | Behaviour-free carriers have no responsibilities to split | Keep them plain, immutable and validated at construction |
| A framework dictates structure (controllers, components, ORM entities) | Fighting the framework adds friction | Follow the framework's pattern and keep your own logic in plain functions |
| Performance-critical inner loops | Virtual dispatch and allocations may cost measurable time | Measure first; keep hot paths concrete and isolate them |
| Small modules that change together | Splitting them spreads one change across files | Leave them together |
| Existing project style differs | Consistency beats local purity | Match the project; report the conflict only if it is unsafe |

- Prefer duplication over the wrong abstraction. Wait until three similar cases exist and the shared shape is clear before extracting.
- Each added abstraction must pay for itself with a named, present benefit: removing a duplicated switch, enabling a fake at a real boundary, or isolating a rule that changes independently.

### Naming

- Names state intent in the domain's vocabulary: `unpaidInvoices`, not `list2`; `retryDelay`, not `d`. Use one word per concept across the codebase (do not mix `fetch`, `get` and `load` for the same operation).
- Functions are verbs or verb phrases (`calculateTax`, `parse_header`); classes and types are nouns. Predicates and booleans read as questions (`isExpired`, `has_permission`, `canRetry`), never negated (`isNotValid`).
- Put units and scale in names when the type does not carry them: `timeoutMs`, `price_cents`, `sizeBytes`. Better still, use a type (`Duration`, `std::chrono::seconds`).
- Avoid vague catch-alls: `Manager`, `Helper`, `Util`, `Handler`, `Data`, `Info`, `Processor` without a qualifier. If you cannot name a class without one, its responsibility is unclear.
- A name that needs a comment to explain it should be renamed. A comment should explain why, not what.
- Scope sets length: short names for tiny scopes (`i`, `x` in a three-line lambda), descriptive names for wider scopes and public APIs. Avoid abbreviations that the team does not use.
- Follow language conventions: `camelCase` in JavaScript, TypeScript and Java methods; `PascalCase` for types; `snake_case` in Python; the project's style in C++ (read existing code). Do not rename public symbols without checking callers and versioned interfaces; a public rename is a compatibility change for the architect.
- Do not encode types in names (`strName`, `IUser`) unless the project's convention requires it.

### Cohesion and coupling

- Cohesion: everything in a unit should serve the same purpose. Signal of low cohesion: groups of methods that use disjoint sets of fields, or a module whose imports split into unrelated clusters. Split along those clusters.
- Coupling: depend on as little of another unit as possible, through its smallest public surface. Signals of tight coupling: reaching through objects (`a.b().c().d()`), shared mutable globals, one module importing the internals of another, change in one place forcing edits in many.
- Keep dependency direction one way and acyclic. Break import cycles by extracting the shared concept into a lower-level module.
- Keep data and the functions that maintain its invariants together. Prefer telling an object to do something over pulling its state apart and deciding elsewhere (feature envy is the smell; see [refactoring.md](refactoring.md)).
- Group by feature or change reason rather than by technical type when the project already does so; follow existing layout.
- Limit public surface: expose the minimum from a module or class, and make everything else private or file-local. Anything public is a promise.

## Examples

Single responsibility, bad to good (TypeScript):

```ts
// Bad: parsing, pricing rules and persistence change for different reasons.
async function checkout(raw: string, db: Database): Promise<void> {
  const order = JSON.parse(raw);
  let total = 0;
  for (const line of order.lines) total += line.qty * line.unitCents;
  if (order.coupon === "SAVE10") total = Math.round(total * 0.9);
  await db.insert("orders", { id: order.id, total });
}

// Good: parse at the edge, keep the rule pure, isolate the side effect.
type Order = { id: string; lines: { qty: number; unitCents: number }[]; coupon?: string };

function totalCents(order: Order): number {
  const subtotal = order.lines.reduce((sum, l) => sum + l.qty * l.unitCents, 0);
  return order.coupon === "SAVE10" ? Math.round(subtotal * 0.9) : subtotal;
}

async function checkout(order: Order, orders: OrderStore): Promise<void> {
  await orders.save({ id: order.id, totalCents: totalCents(order) });
}
```

Open and closed through a handler table (Python), used only because variants keep growing:

```python
from collections.abc import Callable

Handler = Callable[[dict], None]
HANDLERS: dict[str, Handler] = {}


def handles(kind: str) -> Callable[[Handler], Handler]:
    def register(func: Handler) -> Handler:
        HANDLERS[kind] = func
        return func
    return register


@handles("invoice.paid")
def on_paid(event: dict) -> None: ...


@handles("invoice.voided")
def on_voided(event: dict) -> None: ...


def dispatch(event: dict) -> None:
    HANDLERS[event["kind"]](event)  # a new event kind adds a function, not an edit here
```

Liskov violation and fix (Java):

```java
// Bad: callers of Bird.fly() break for Penguin.
class Bird { void fly() { /* ... */ } }
class Penguin extends Bird {
    @Override void fly() { throw new UnsupportedOperationException(); }
}

// Good: model the capability, not the taxonomy.
interface Walker { void walk(); }
interface Flyer extends Walker { void fly(); }
class Sparrow implements Flyer {
    public void walk() { /* ... */ }
    public void fly() { /* ... */ }
}
class Penguin implements Walker {
    public void walk() { /* ... */ }
}
```

Interface segregation and dependency inversion together (TypeScript):

```ts
// The consumer defines the narrow interface it needs.
interface Clock { now(): Date }
interface Mailer { send(to: string, subject: string, body: string): Promise<void> }

class ReminderJob {
  constructor(private readonly clock: Clock, private readonly mailer: Mailer) {}

  async run(dueDates: Map<string, Date>): Promise<void> {
    for (const [email, due] of dueDates) {
      if (due <= this.clock.now()) {
        await this.mailer.send(email, "Payment due", "Your invoice is due.");
      }
    }
  }
}
```

Naming, bad to good:

```python
# Bad
def proc(d, f):                 # what is d, what is f?
    return [x for x in d if f(x)]
t = 30                          # seconds? minutes?

# Good
def select_overdue(invoices, is_overdue):
    return [invoice for invoice in invoices if is_overdue(invoice)]
retry_timeout_seconds = 30
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Interface for every class | Extra indirection, nothing to substitute | Create the interface when a second implementation or a test boundary exists |
| Splitting by line count | Related logic scattered across files | Split by reason to change |
| Class hierarchies to share code | Subtypes that violate substitution; fragile base class | Composition and small functions |
| Switch replaced by classes when variants are fixed | More code, lost exhaustiveness checking | Keep an exhaustive `switch` over a closed union |
| `Manager`, `Helper`, `Util` classes | Grab-bags with no cohesion | Name by responsibility; move functions to the data they serve |
| Hidden dependencies via singletons | Hard to test, order-dependent behaviour | Pass dependencies in explicitly |
| Boolean flag parameters (`save(user, true)`) | Call sites unreadable; function does two things | Two functions, or a named options object or enum |
| Renaming public symbols casually | Breaks consumers | Treat as an interface change; check callers and docs |
| Reviewer finding "violates SRP" with no scenario | Not actionable; opinion rather than defect | State the change that is now costly, or drop it |

## Checklist

- [ ] Can you name the concrete change that makes each new abstraction worthwhile?
- [ ] Does each new unit have one stated reason to change?
- [ ] Is there at most one implementation per new interface, or a documented boundary reason (fake, plugin, external system)?
- [ ] Do subclasses honour every contract of their base type, with no `UnsupportedOperationException` or `NotImplementedError` stubs?
- [ ] Are interfaces defined by what the consumer uses?
- [ ] Are collaborators passed in rather than created or looked up globally?
- [ ] Do names use domain vocabulary, with units where the type does not carry them?
- [ ] Are there no `Manager`, `Helper` or `Util` classes introduced?
- [ ] Are booleans named as positive predicates and free of flag-parameter overloads?
- [ ] Do imports form an acyclic graph in one direction?
- [ ] Is the public surface of each new module or class as small as the task allows?
- [ ] Did a reviewer finding include a failure scenario?

## Verify with context7 and gh_grep

- **context7:** SOLID itself has no library to check. Query the documentation of the language features you rely on at the project's version: "TypeScript structural typing and interfaces", "Python `typing.Protocol`", "Java sealed interfaces and records", "C++ concepts and virtual destructor rules", and the injection or testing library the project already uses.
- **gh_grep:** search literal code to see how maintained projects apply these ideas: `constructor(private readonly clock: Clock`, `class .*\(Protocol\):`, `sealed interface`, `final class`, `std::unique_ptr<.*Interface>`. Do not copy code without a compatible licence.

## Sources

- None. This file is original practitioner guidance; no external specification or version-dependent documentation applies to it.
