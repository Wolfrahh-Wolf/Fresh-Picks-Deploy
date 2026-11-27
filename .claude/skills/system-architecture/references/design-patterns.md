# Practical Design Patterns

When a creational, structural or behavioural design pattern earns its place inside a component, the simplest form of each, and how to recognise over-engineering. Language-neutral guidance with examples in Python 3.11; checked on 2026-11-26 against the Refactoring.Guru catalogue of 22 classic patterns (5 creational, 7 structural, 10 behavioural) and Alistair Cockburn's description of ports and adapters. Translate examples to the project's language; the project's own conventions win.

## Contents

- When a pattern is justified
- Creational patterns
- Structural patterns
- Behavioural patterns
- Language features that replace patterns
- Over-engineering warnings
- Pattern selection table

## Guidance

### When a pattern is justified

A pattern is a named, proven answer to a recurring problem. It is worth its cost only when the problem exists now. Use this test before introducing one:

1. Name the force: the variation, coupling or duplication that hurts today, with an example from the code.
2. Write the simplest code that solves it without the pattern. Compare.
3. Use the pattern only if the simple version fails on a stated criterion (a second implementation exists, a test cannot isolate a dependency, a change touches many places).
4. If the need is foreseen rather than present, record it in prose in the design and do not build it.

Every indirection costs reading time, debugging time and onboarding time. Patterns are a shared vocabulary, so use the name in documentation when the structure really is that pattern, and do not put pattern names in class names unless that helps readers.

Patterns here work at the scale of classes and functions inside one component. Structural styles (layered, hexagonal, event-driven and the rest) are in [architecture-patterns.md](architecture-patterns.md); resilience patterns (retry, circuit breaker, bulkhead) are in [scalability.md](scalability.md). For SOLID and refactoring techniques, load `languages-clean-code`.

### Creational patterns

Creational patterns control how objects are created, so that code does not depend on concrete classes more than it needs to.

**Factory Method and Abstract Factory.** Use when the concrete type depends on configuration or runtime data and callers should not know the choice, or when whole families of related objects must be created consistently (for example matching a storage client and its serializer).
- Simplest form: a plain function that returns an object that satisfies an interface.
- Add a class hierarchy only when subclasses must override the creation step.
- Do not use for one concrete class with no variation. A factory that always builds the same thing is indirection.

**Builder.** Use when constructing an object takes many steps or many optional parts, and an invalid half-built object must not escape.
- Simplest form: keyword arguments with defaults, or an immutable data class. Many languages make a builder unnecessary.
- Use a builder when construction is genuinely staged (query builders, request builders) or validation spans several fields.

**Singleton.** Ensures one instance with global access. Avoid it as global mutable state: it hides dependencies, hurts tests and breaks when you need two instances (per tenant, per test).
- Do instead: create the single instance once at the application's entry point (the composition root) and pass it to whoever needs it. You get one instance without a global.
- Acceptable: a stateless, immutable, process-wide resource such as configuration read once, when exposed through the same passing mechanism.

**Prototype.** Creates objects by copying an existing one. Rare. Use for expensive-to-build objects that are copied with small changes. Check that the language's copy semantics (shallow versus deep) match your intent.

### Structural patterns

Structural patterns assemble classes and objects into larger structures while keeping them flexible.

**Adapter.** Converts one interface into another so that code can use a component with an incompatible interface. This is the most useful pattern in practice: wrap each third-party library, SDK or legacy system behind an interface shaped by your needs. Cockburn describes ports and adapters as a particular use of Adapter.
- Name the interface by purpose in your domain's terms, not after the vendor.
- Keep vendor types inside the adapter; translate errors and data at the boundary.
- One adapter per external dependency; an in-memory version for tests.
- Do not adapt what you own and can simply change.

**Facade.** A simple interface in front of a complex subsystem. Use to give callers one small, stable entry point (a module's public surface is a facade). Do not let it grow into a catch-all with every method of the subsystem; that is a pass-through that hides nothing.

**Decorator.** Adds behaviour to an object by wrapping it with an object of the same interface. Fits cross-cutting additions around one operation: logging, metrics, caching, authorisation checks, retries. Wrapping order matters (a retry wrapper around a timeout wrapper behaves differently from the reverse), so test the order.

**Proxy.** Stands in for another object to control access: lazy loading, remote access, caching, access control. Same shape as Decorator with a different intent: Decorator adds behaviour, Proxy controls access to the same behaviour.

**Composite.** Treats individual objects and trees of them uniformly (file systems, UI trees, rule sets). Use when the data is truly a tree and clients should not care about leaf or branch.

**Bridge.** Separates an abstraction from its implementation when both vary independently (two axes of variation). If only one axis varies, use a plain interface.

**Flyweight.** Shares common state between many objects to save memory. Rare; justify with a measurement of memory pressure.

### Behavioural patterns

Behavioural patterns distribute responsibility and define how objects collaborate.

**Strategy.** Makes an algorithm interchangeable behind one interface. Use when the same step has several implementations chosen at runtime (pricing rules, retry policies, serialisation formats).
- Simplest form: pass a function, or keep a table of functions keyed by name. A class hierarchy is needed only when each strategy carries its own state.

**Observer.** One object notifies subscribers of changes. Use for in-process event handling and decoupling a producer from several reactions. Watch for: listeners that are never removed (leaks), order dependence between listeners, one failing listener breaking the others, and hidden control flow. When the reaction must survive a process restart or cross a process boundary, you need a durable queue or broker instead (see [architecture-patterns.md](architecture-patterns.md), event-driven).

**Command.** Turns a request into an object with all the data to run it. Use for job queues, undo, audit trails, retries and macro operations. A job message with a name and parameters is a command.

**State.** Lets an object change behaviour as its internal state changes. For a lifecycle with a few states and clear transitions, a transition table is simpler and easier to verify; use polymorphic State objects only when each state carries substantial different behaviour.

**Chain of Responsibility.** Passes a request along handlers until one handles it. Matches middleware pipelines (validation, authentication, parsing). Keep the order explicit and documented; make it clear who ends the chain.

**Template Method.** A base class fixes the skeleton of an algorithm; subclasses fill steps. Prefer composition (pass the varying step in) because inheritance couples the subclass to the base class's internals.

**Iterator.** Traverses a collection without exposing its structure. Almost every language has it built in; implement your own only for a custom data structure.

**Mediator.** A central object coordinates interactions among several objects so they do not refer to each other. Use when many-to-many references are tangled. Beware of a mediator that absorbs all logic and becomes a god object.

**Memento.** Saves and restores an object's earlier state without exposing internals. Use for undo and snapshots; often a copy of an immutable value does the job.

**Visitor.** Adds operations to a structure of different node types without changing them. Rare; useful for syntax trees and compilers. Prefer pattern matching or a plain function over the structure if the language supports it.

### Language features that replace patterns

Many patterns exist to work around language limits. Check the language first.

| Pattern | Often replaced by |
|---|---|
| Strategy, Command, Template Method | First-class functions and closures; passing a callable |
| Singleton | Module-level object or one instance created at the entry point and passed in |
| Builder | Named or keyword arguments, defaults, immutable data classes |
| Iterator | Built-in iteration protocol, generators |
| Observer | Language or library events and callbacks; a message broker across processes |
| Decorator | Language decorators or middleware composition, where available |
| Visitor | Pattern matching on a closed set of variants |
| Factory | A function; a dictionary from a key to a constructor |

### Over-engineering warnings

The Refactoring.Guru catalogue of code smells names the family: Speculative Generality (hooks and abstractions for a future that has not arrived), Lazy Class (a class that does too little to justify existing), and Middle Man (a class that only delegates). Watch for these signs in a design or a review:

- An interface with exactly one implementation and no test double that needs it.
- A factory that creates one class; an abstract base class with one subclass.
- Names such as Manager, Handler, Processor, Helper or Service that say nothing about responsibility.
- Layers whose methods only forward to the next layer.
- Configuration that selects behaviour no one has ever changed.
- A pattern applied because the vocabulary was available, with no named force.
- A generic framework or extension point "in case" a second use appears.
- Pattern names in class names that make the code harder to read than the problem is.

The deletion test: inline the abstraction. If no caller or test becomes harder to understand or change, remove it. The architect's rule is to design for stated requirements, note foreseen extensions, and not build them.

When a pattern is warranted but not yet: write the foreseen variation as a sentence in the design ("a second payment provider is expected in Q3; the adapter boundary is where it plugs in"), keep the code direct, and refactor when the second case arrives.

### Pattern selection table

| Problem | Pattern | Simplest form | Do not use when |
|---|---|---|---|
| Need to wrap a vendor SDK or legacy API | Adapter | Interface in domain terms plus one class per vendor | You own the code and can change it |
| Many entry points to a complex subsystem | Facade | One small public module | It would forward every call 1:1 |
| Add logging, metrics or caching around an operation | Decorator | Wrapper with the same interface | Behaviour changes the contract |
| Choose an algorithm at runtime | Strategy | Function or table of functions | There is only one algorithm |
| Lifecycle with several states | State | Transition table | States have rich differing behaviour: then State objects |
| Queue jobs, undo, audit | Command | Named job with parameters | A direct call is enough |
| Pipeline of checks | Chain of Responsibility | Ordered list of functions | One check |
| Object has many optional parts | Builder | Keyword arguments, defaults | Few parameters |
| Create type chosen by configuration | Factory Method | Function returning an interface | One concrete type |
| Single shared resource | None; pass it in | Create once at the entry point | You are tempted to use global access |

## Examples

### Bad to good: Strategy as a class hierarchy

Bad: three small classes, an abstract base, a factory and a registry to apply a discount.

```python
from abc import ABC, abstractmethod
from decimal import Decimal


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, amount: Decimal) -> Decimal: ...


class StandardDiscount(DiscountStrategy):
    def apply(self, amount: Decimal) -> Decimal:
        return amount


class MemberDiscount(DiscountStrategy):
    def apply(self, amount: Decimal) -> Decimal:
        return amount * Decimal("0.90")


class DiscountFactory:
    @staticmethod
    def create(tier: str) -> DiscountStrategy:
        return {"standard": StandardDiscount, "member": MemberDiscount}[tier]()
```

Good: the strategy is a function and the table is the registry.

```python
from decimal import Decimal

DISCOUNTS = {
    "standard": lambda amount: amount,
    "member": lambda amount: amount * Decimal("0.90"),
}


def price(amount: Decimal, tier: str) -> Decimal:
    return DISCOUNTS[tier](amount)
```

Introduce classes only when a strategy needs its own state or several methods.

### Adapter with a purpose-named port (the useful case)

```python
from decimal import Decimal
from typing import Protocol


class PaymentGateway(Protocol):
    """Port, named by purpose, in the application's vocabulary."""

    def charge(self, order_id: str, amount: Decimal) -> str:
        """Charge once for this order; return a payment identifier."""
        ...


class ExampleProviderGateway:
    """Adapter for a hypothetical provider client; vendor types stay in here."""

    def __init__(self, client) -> None:
        self._client = client

    def charge(self, order_id: str, amount: Decimal) -> str:
        response = self._client.create_charge(  # hypothetical client method
            reference=order_id,
            minor_units=int(amount * 100),
        )
        return response["id"]


class InMemoryGateway:
    """Test adapter: proves the port is clean and keeps tests fast."""

    def __init__(self) -> None:
        self.charges: dict[str, Decimal] = {}

    def charge(self, order_id: str, amount: Decimal) -> str:
        self.charges[order_id] = amount
        return f"test-{order_id}"
```

The core depends only on `PaymentGateway`. Keying the in-memory charge by `order_id` also demonstrates the idempotency a real adapter must provide.

### State as a transition table

```python
ALLOWED = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"approved", "rejected", "cancelled"},
    "approved": {"fulfilled", "cancelled"},
    "rejected": set(),
    "fulfilled": set(),
    "cancelled": set(),
}


def transition(current: str, target: str) -> str:
    if target not in ALLOWED.get(current, set()):
        raise ValueError(f"illegal transition {current} -> {target}")
    return target
```

The table is the specification, easy to test exhaustively and to review against requirements. Move to State objects only if states need different behaviour, not just different permitted moves.

### Decorator around a stable interface

```python
import logging
import time

log = logging.getLogger(__name__)


class TimedGateway:
    """Decorator: same interface as the wrapped gateway, adds timing."""

    def __init__(self, inner) -> None:
        self._inner = inner

    def charge(self, order_id, amount):
        started = time.monotonic()
        try:
            return self._inner.charge(order_id, amount)
        finally:
            log.info("charge took %.3f s", time.monotonic() - started)
```

Compose at the entry point: `TimedGateway(ExampleProviderGateway(client))`. The core still sees only the port.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Adding a pattern for a future need | Code to maintain and read for no present benefit | Note the foreseen extension in the design; build it when it arrives |
| Interface plus factory for one implementation | Two extra files, no flexibility | Direct construction; extract when a second implementation or a test double needs it |
| Singleton as global access to mutable state | Hidden dependency, hard to test, cannot have two instances | Create once at the entry point and pass it in |
| Class hierarchies for simple strategies | Boilerplate hides the algorithm | Functions or a lookup table |
| Vendor types leaking past the adapter | Vendor change touches the whole codebase | Translate data and errors inside the adapter |
| Observer used for cross-process or must-not-lose reactions | Lost reactions on restart; invisible flow | Durable queue or broker with idempotent consumers |
| Wrong decorator order | Retries outside timeouts behave differently from the reverse | Document and test the composition order |
| Naming code after the pattern | Names describe form not purpose | Name for the responsibility; mention the pattern in docs only if helpful |
| Mediator or facade that absorbs all logic | A god object | Keep it to coordination or to a thin entry point |

## Checklist

- [ ] Each pattern in the design names the present force that justifies it, with an example from the code.
- [ ] The simpler version without the pattern was considered and the reason it fails is written down.
- [ ] No interface exists with one implementation and no test-double need.
- [ ] Every third-party dependency that may change is behind an adapter with a purpose-named interface.
- [ ] Vendor types and errors do not cross the adapter boundary.
- [ ] Shared instances are created once at the entry point and passed in; no global access.
- [ ] Strategies that need no state are functions or table entries.
- [ ] Observers are used only in process; cross-process reactions use a durable channel.
- [ ] Decorator or middleware order is stated and tested.
- [ ] Foreseen extensions are recorded in prose, not built.

## Verify with context7 and gh_grep

- **context7:** before relying on a language or framework feature to replace a pattern, check it for the version in the manifest, for example "dependency injection and scopes in `<framework>` `<version>`", "typing `Protocol` and `dataclass` features in Python `<version>`", or the equivalents for the project's language. Check how the framework's own container or middleware chain expresses factories, decorators and pipelines before writing your own.
- **gh_grep:** search literal code to see how maintained repositories in the project's language really use patterns: `class .*Factory`, `class .*Adapter`, `getInstance(`, `implements .*Strategy`, `register(` for registries. Count how often a pattern appears with only one implementation; that is the over-engineering signal.

## Sources

- Refactoring.Guru, "The Catalog of Design Patterns". https://refactoring.guru/design-patterns/catalog
- Alistair Cockburn, "Hexagonal architecture" (2005), the Related Patterns section on Adapter and mock objects; text read through a third-party mirror because the original site could not be fetched: https://gist.github.com/timabell/4f6b6d222b7742f4784b3b306a0cfd43 (canonical home: alistair.cockburn.us, not fetched)
- Refactoring.Guru, code smell index (Speculative Generality, Lazy Class, Middle Man), listed on the catalogue page above.
