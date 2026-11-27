# Java

Modern Java: language features, collections, concurrency, exceptions and build tools. Assumes Java 25 (LTS, released September 2025) as the newest LTS, with Java 21 and 17 still common in projects; checked 2026-11-26. The project's configured `release` level or toolchain wins over every default here.

## Contents

- Version policy and preview features
- Modern language features
- Collections
- Concurrency
- Exceptions
- Build tools

## Guidance

### Version policy and preview features

- Read the configured Java level before writing: `maven.compiler.release` or `<release>` in the Maven compiler plugin, the Gradle `java.toolchain.languageVersion`, and the CI JDK. Use only language and library features available at that level.
- Oracle's published roadmap lists Java 8, 11, 17, 21 and 25 as LTS releases, with the next LTS planned as Java 29 in September 2027. Releases between LTS versions (26, 27) are superseded when the next feature release ships; do not move a project onto one without approval.
- Moving the project's Java level, the JDK distribution or the build tool's major version is a dependency-style upgrade. Follow [dependency-management.md](dependency-management.md) and obtain approval.
- Preview features need `--enable-preview`, and classes compiled with it run only on the same feature release. Do not use them in production code without approval. In Java 25, structured concurrency (JEP 505) is still in preview, as are stable values (JEP 502) and primitive types in patterns (JEP 507).
- Finalized and safe from the levels shown: records (16), sealed classes (17), pattern matching for `switch` and record patterns (21), virtual threads and sequenced collections (21). In 25, flexible constructor bodies and compact source files with instance `main` methods are final, and scoped values (JEP 506) are delivered as a feature.

### Modern language features

- **Records** for immutable data carriers. Put validation in the compact constructor. Do not use records for entities with identity or mutable state, and copy mutable components (`List.copyOf`) in the constructor.
- **Sealed interfaces plus records plus pattern `switch`** model closed variants. A `switch` expression over a sealed type needs no `default`, so adding a permitted subtype breaks compilation where it is unhandled. Avoid `default` on sealed switches for that reason.
- **Pattern matching for `instanceof`** replaces cast-after-check: `if (obj instanceof String s && !s.isBlank())`.
- **`var`** for local variables when the right-hand side makes the type obvious. Never for fields, parameters or return types, and not when it hides an important type.
- **Text blocks** for multi-line strings such as SQL or JSON fixtures. Parameterise queries; never concatenate user input into text-block SQL (see `database-engineering`).
- **`Optional`** as a return type for "might be absent". Do not use it for fields, parameters or collections, and never call `get()` without checking; prefer `orElseThrow`, `map`, `orElse`.
- **Streams** for straightforward transformation pipelines; use a loop when the body has side effects, early exits or exceptions. Do not mutate external state in a stream lambda. `Stream.toList()` returns an unmodifiable list.
- **Immutability by default**: make fields `final`, classes `final` unless designed for extension, and prefer constructor injection.
- Use `Objects.requireNonNull(arg, "arg")` at public entry points that cannot accept null. Document nullability with the project's annotation library if it has one.
- Override `equals`, `hashCode` and `toString` together or not at all. Records generate all three. Never use mutable fields in `hashCode` for objects stored in hash-based collections.
- Use `enum` for closed sets and `EnumMap`/`EnumSet` for enum-keyed collections. Compare enums with `==`.
- Use `java.time` (`Instant`, `LocalDate`, `ZonedDateTime`, `Duration`). Do not use `Date`, `Calendar` or `SimpleDateFormat`. Pass `Clock` into code that needs "now" so it stays deterministic.
- Use `BigDecimal` (from `String` or `valueOf`, never from a `double`) for money, or integer minor units.
- Follow the project's formatter (google-java-format, Spotless or IDE settings) instead of hand formatting.

### Collections

- Declare variables and parameters with interface types (`List`, `Map`, `Set`), not `ArrayList` or `HashMap`.
- `List.of`, `Set.of`, `Map.of` and `copyOf` create unmodifiable collections that reject `null`. `Collections.unmodifiableList` is only a read-only view of a list someone else can still change. Defensive-copy with `List.copyOf` at API boundaries.
- `Arrays.asList` returns a fixed-size list backed by the array; adding throws `UnsupportedOperationException`.
- `HashMap` and `HashSet` have no defined iteration order; use `LinkedHashMap` or `TreeMap` when order matters. Since Java 21 `List`, `Deque`, `LinkedHashSet` and `LinkedHashMap` share sequenced methods (`getFirst`, `getLast`, `reversed`).
- Do not modify a collection while iterating it; use `removeIf`, an iterator's `remove`, or build a new collection. Otherwise expect `ConcurrentModificationException` or silent skips.
- `Map.computeIfAbsent` and `compute` mapping functions must not modify the same map. Use `merge` for counters.
- `Collectors.toMap` throws on duplicate keys; supply a merge function. Use `groupingBy` for one-to-many.
- Choose thread-safe collections deliberately: `ConcurrentHashMap` for shared maps (use its atomic `merge`, `compute`), `CopyOnWriteArrayList` for rarely modified listener lists. `Collections.synchronizedList` does not make compound check-then-act operations atomic.
- Keys must be effectively immutable with consistent `equals` and `hashCode`.
- Compare with `Comparator.comparing(...).thenComparing(...)`. Never subtract integers in a comparator; it overflows.

### Concurrency

- Prefer higher-level tools from `java.util.concurrent` over `wait`/`notify`, raw `Thread` and manual locking.
- For blocking I/O workloads (HTTP calls, JDBC, file access), use virtual threads: `Executors.newVirtualThreadPerTaskExecutor()` in a `try`-with-resources block, one task per unit of work. Do not pool virtual threads, and do not use them for CPU-bound work; use a bounded platform-thread pool sized to the cores.
- Bound resource use separately from thread count. Virtual threads make it cheap to start a million tasks, so protect the downstream database or service with a `Semaphore` or pool limit.
- Avoid holding `synchronized` monitors across blocking calls inside virtual threads; older JDKs pin the carrier thread (whether a given JDK still pins is JDK-specific, so verify on the target JDK). Prefer `ReentrantLock` with `try`/`finally` for long critical sections.
- Always shut down executors you create. `ExecutorService` is `AutoCloseable` since Java 19, so use `try`-with-resources, or call `shutdown` and `awaitTermination`.
- Put timeouts on `Future.get(timeout, unit)`, `CompletableFuture.orTimeout`, HTTP clients and lock attempts (`tryLock`). Never wait forever.
- Treat `InterruptedException` as a cancellation request: either propagate it, or restore the flag with `Thread.currentThread().interrupt()` before returning or wrapping. Never swallow it.
- Share data by immutability, confinement or `java.util.concurrent` types. Mark cross-thread flags `volatile` or use `AtomicBoolean`. `volatile` does not make `count++` atomic; use `AtomicInteger` or `LongAdder`.
- `CompletableFuture`: always handle failure (`exceptionally`, `handle`, or let the caller `join` and see `CompletionException`). Pass an explicit executor to `*Async` methods instead of using the common pool for blocking work.
- Use `ThreadLocal` sparingly, and clean it up in pooled platform threads. For passing context to child tasks, scoped values (final in Java 25) are the designed replacement; structured concurrency remains preview.
- Document thread-safety on every class that is shared: immutable, thread-safe, or not thread-safe.

### Exceptions

- Use unchecked exceptions for programming errors and unrecoverable conditions. Use checked exceptions when the caller can reasonably recover and the API should force a decision. Follow the project's existing policy and do not mix both styles for the same kind of failure.
- Never catch `Throwable` or `Error`. Catch `Exception` only at a boundary that logs and converts, such as a request handler or job runner.
- Never leave an empty `catch`. Either handle, rethrow or log with context, and do all three at most once per failure path to avoid duplicate logs.
- Preserve the cause when wrapping: pass the original exception as the second constructor argument.
- Use `try`-with-resources for everything `AutoCloseable`. Exceptions from `close` are attached as suppressed exceptions instead of masking the primary one.
- Do not use exceptions for ordinary control flow, and do not return `null` where an empty collection, `Optional` or an exception is clearer.
- Validate arguments early with `IllegalArgumentException` (bad value) or `IllegalStateException` (wrong object state). Name the offending value in the message, without including secrets.
- Keep exception hierarchies small: one base exception per module if callers need to catch it, with specific subclasses only when callers react differently.
- A `finally` block must not `return` or throw, which would hide the original failure.

### Build tools

- Commit and use the wrapper (`mvnw` or `gradlew`) so everyone builds with the same tool version. Run `./mvnw -B verify` or `./gradlew check` as the project's CI-equivalent command (use `mvnw.cmd` and `gradlew.bat` on Windows).
- Set the language level with `release` (Maven: `maven.compiler.release`) rather than separate `source` and `target`, because `release` also restricts the API to that level. In Gradle use a Java toolchain.
- Set `project.build.sourceEncoding` to UTF-8.
- Manage versions in one place: Maven `dependencyManagement` or an imported BOM, Gradle `gradle/libs.versions.toml` version catalogs. Never use version ranges or `LATEST` or `RELEASE`, and be careful with dynamic Gradle versions (`1.+`).
- Keep dependency scopes tight (`test`, `provided`, `runtime`, Gradle `api` versus `implementation`) so test and tooling libraries do not ship.
- Reproducibility: pin plugin versions too. Gradle supports dependency locking; Maven projects pin exact versions and may add the enforcer plugin to ban duplicates and ranges. Lockfile mechanics are in [dependency-management.md](dependency-management.md).
- Add static analysis the project already uses (Checkstyle, SpotBugs, Error Prone, Spotless); do not introduce a new tool as a side effect of a feature task.
- Multi-module builds: keep module dependencies acyclic and directional; shared test utilities go in a test-only module.

## Examples

Sealed variants with records and an exhaustive `switch` (Java 21 or later):

```java
sealed interface Shape permits Circle, Rectangle {}

record Circle(double radius) implements Shape {}

record Rectangle(double width, double height) implements Shape {}

final class Geometry {
    private Geometry() {}

    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Rectangle(double w, double h) -> w * h;
        };
    }
}
```

Validation in a record's compact constructor and a defensive copy:

```java
import java.util.List;

record Port(int value) {
    Port {
        if (value < 1 || value > 65_535) {
            throw new IllegalArgumentException("port out of range: " + value);
        }
    }
}

record Route(String name, List<String> hosts) {
    Route {
        hosts = List.copyOf(hosts); // rejects null elements, detaches from caller's list
    }
}
```

Virtual threads for blocking I/O with bounded downstream load (Java 21 or later):

```java
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;

final class Fetcher {
    private final Semaphore limit = new Semaphore(20); // protects the downstream service

    List<String> fetchAll(List<URI> uris) throws InterruptedException, ExecutionException {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<String>> futures = uris.stream()
                .map(uri -> executor.submit(() -> fetchLimited(uri)))
                .toList();
            List<String> bodies = new ArrayList<>();
            for (Future<String> future : futures) {
                bodies.add(future.get());
            }
            return bodies;
        } // close() waits for submitted tasks to finish
    }

    private String fetchLimited(URI uri) throws InterruptedException {
        limit.acquire();
        try {
            return blockingGet(uri);
        } finally {
            limit.release();
        }
    }

    private String blockingGet(URI uri) {
        return uri.toString(); // stands in for a blocking HTTP call
    }
}
```

Resources, cause preservation and interruption, bad to good:

```java
// Bad: leaks the reader on failure, drops the cause, swallows interruption.
String load(Path path) {
    try {
        BufferedReader in = Files.newBufferedReader(path);
        return in.readLine();
    } catch (Exception e) {
        return null;
    }
}

// Good
String load(Path path) {
    try (BufferedReader in = Files.newBufferedReader(path)) {
        return in.readLine();
    } catch (IOException e) {
        throw new UncheckedIOException("cannot read " + path, e);
    }
}

void await(CountDownLatch latch) {
    try {
        latch.await();
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw new IllegalStateException("interrupted while waiting", e);
    }
}
```

Maven compiler level (use the project's own number):

```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using `source` and `target` instead of `release` | Compiles against newer JDK APIs missing at runtime | `maven.compiler.release` or a Gradle toolchain |
| Catching `Exception` or `Throwable` and returning `null` | Hides bugs, produces null pointer failures far away | Catch specific exceptions; rethrow with cause |
| Swallowing `InterruptedException` | Threads cannot be cancelled; shutdown hangs | Re-set the interrupt flag or propagate |
| `Collections.unmodifiableList(list)` treated as immutable | The backing list can still change | `List.copyOf(list)` |
| Mutable keys in `HashMap` | Entries become unreachable after mutation | Immutable keys with stable `hashCode` |
| Pooling virtual threads or running CPU work on them | Loses their benefit or starves carriers | One virtual thread per task for blocking I/O; sized pool for CPU |
| `count++` on a `volatile` field | Not atomic; lost updates | `AtomicInteger` or `LongAdder` |
| `new BigDecimal(0.1)` | Carries binary floating-point error | `new BigDecimal("0.1")` or `BigDecimal.valueOf` |
| Using `Optional.get()` unchecked | Throws `NoSuchElementException` | `orElseThrow`, `map`, `orElse` |
| Version ranges or `LATEST` in builds | Non-reproducible builds | Exact versions via BOM or catalog |
| Enabling preview features casually | Classes tied to one JDK feature release | Avoid, or get approval and document it |
| `default` branch in a sealed `switch` | New variants compile silently and go unhandled | List every permitted type; no `default` |

## Checklist

- [ ] Does the code compile and run at the project's configured `release` level without preview flags?
- [ ] Are data carriers records, with validation in the compact constructor and defensive copies of collections?
- [ ] Do `switch` expressions over sealed types omit `default`?
- [ ] Are variables and parameters declared with interface types?
- [ ] Are returned or stored collections immutable copies where callers could otherwise mutate them?
- [ ] Is every `AutoCloseable` opened in `try`-with-resources?
- [ ] Is every executor closed or shut down, and every blocking wait bounded by a timeout?
- [ ] Is `InterruptedException` either propagated or followed by restoring the interrupt flag?
- [ ] Does every wrapping exception carry its cause, and is there no empty `catch`?
- [ ] Is shared mutable state protected, atomic or confined, and is thread-safety documented?
- [ ] Is time obtained through an injected `Clock` and money kept out of `double`?
- [ ] Do build files use `release`, exact versions and the committed wrapper?

## Verify with context7 and gh_grep

- **context7:** query the JDK and build tool documentation for the project's versions: "`Executors.newVirtualThreadPerTaskExecutor` shutdown and close behaviour", "pattern matching for switch exhaustiveness with sealed types", "record compact constructor rules", "maven-compiler-plugin `release` parameter", "Gradle Java toolchains `languageVersion`", and the exact API of any library in the diff.
- **gh_grep:** search literal code: `newVirtualThreadPerTaskExecutor()`, `sealed interface`, `Thread.currentThread().interrupt()`, `<maven.compiler.release>`, `JavaLanguageVersion.of(`, `List.copyOf(`. Check how recent, maintained repositories apply them, and do not copy code without a compatible licence.

## Sources

- Oracle Java SE Support Roadmap (LTS releases and next LTS): https://www.oracle.com/technetwork/java/java-se-support-roadmap.html
- OpenJDK JDK 25 project page (JEP list, scoped values, stable values, primitive patterns): https://openjdk.org/projects/jdk/25
