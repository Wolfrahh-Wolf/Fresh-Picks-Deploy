# C++

Modern C++: ownership and RAII, memory safety, concurrency, CMake, warnings and sanitizers. Assumes C++20 as the production baseline and C++23 where the project's compilers support it; CMake 4.x; checked 2026-11-26. C++26 is technically complete but not yet published by ISO, so treat it as unavailable unless the project pins a compiler and flags that implement the feature. The project's compilers, `CMakeLists.txt` and style rules win over every default here.

## Contents

- Standard and toolchain
- Ownership and RAII
- Memory safety
- Error handling
- Concurrency
- Interface and type design
- CMake
- Warnings and sanitizers

## Guidance

### Standard and toolchain

- Read the project's standard from `CMakeLists.txt` (`cxx_std_20`, `CMAKE_CXX_STANDARD`), compiler flags and CI matrix. Do not raise it as a side effect of a feature.
- The C++ Core Guidelines are a collaborative, continually evolving rule set for "modern C++" (C++11 and newer), led by Bjarne Stroustrup. Treat them as the default rulebook when the project has none, and cite rule IDs in review comments. Where the project's rules disagree, the project wins unless the rule is unsafe.
- C++26 (reflection, contracts, `std::execution`, library hardening, erroneous behaviour for uninitialised reads) finished technical work in March 2026. The first ISO approval ballot did not pass, and the committee finished a second round of changes on 2026-11-21 before a re-ballot. Compiler support is partial. Do not use C++26-only features unless the build pins a compiler version that implements them; flag any use for approval.
- Prefer standard library facilities over hand-written ones: `std::string`, `std::vector`, `std::array`, `std::span`, `std::optional`, `std::variant`, `std::unique_ptr`, `std::format` (C++20) and algorithms or ranges. `std::expected` and `std::print` need C++23.
- Avoid macros, `using namespace` in headers, and global mutable state. Use `constexpr` and `enum class` instead of `#define`.

### Ownership and RAII

- Every resource (memory, file, socket, lock, handle) is owned by exactly one object whose destructor releases it. Acquire in the constructor, release in the destructor (RAII). This is what makes early returns and exceptions safe.
- Do not call `new` and `delete` explicitly (Core Guidelines R.11). Use `std::make_unique`. Use `std::make_shared` only when ownership is genuinely shared (R.20, R.21: prefer `unique_ptr` unless sharing is needed). Never use `malloc` and `free` in C++ code.
- A raw pointer or reference is non-owning (R.3). Express ownership in signatures:
  - `void f(const Widget&)`: observes, caller keeps ownership.
  - `void f(std::unique_ptr<Widget>)`: takes ownership.
  - `std::unique_ptr<Widget> make()`: gives ownership to the caller.
  - `std::shared_ptr<Widget>` parameters only when the callee really extends the lifetime.
- Pass non-owning array views as `std::span<T>` and read-only strings as `std::string_view`. A view never extends the life of what it points to.
- Follow the rule of zero: give classes members that manage themselves (`std::string`, `std::vector`, smart pointers) and declare no copy, move or destructor. If you declare any special member, consider all five (rule of five, C.21): destructor, copy constructor, copy assignment, move constructor, move assignment, each defaulted or deleted deliberately.
- Mark move operations `noexcept`; containers such as `std::vector` fall back to copying on reallocation when a move can throw.
- Wrap C handles in a small RAII type or a `std::unique_ptr` with a custom deleter. Never leave `open`/`close` or `lock`/`unlock` pairs in application code.
- A base class used polymorphically needs a public virtual destructor (or a protected non-virtual one) (C.35). Mark overrides `override`, and mark leaf classes `final` when they are not designed for extension.
- Prefer composition and values to inheritance and heap allocation. Allocate on the heap only for polymorphism, lifetime beyond scope, or size.

### Memory safety

- Initialise every object at declaration (ES.20). Prefer brace initialisation, and be aware that it rejects narrowing conversions. Uninitialised reads are undefined behaviour before C++26.
- Do not index with unchecked bounds when a check is cheap. Use range-`for`, algorithms, `std::span`, `.at()` where exceptions are acceptable, and `std::array` or `std::vector` instead of C arrays. Enable standard-library hardening or assertion modes in debug and test builds, for example `_GLIBCXX_ASSERTIONS` for libstdc++ and libc++'s hardening modes (confirm names for the installed library version, unverified).
- Never return a reference, pointer or view to a local or temporary. A `std::string_view` built from a temporary `std::string` dangles at the end of the statement. Lambdas that capture by reference must not outlive the captured variables.
- Iterator and reference invalidation: `push_back`, `insert` and `erase` can invalidate iterators, pointers and references into a `std::vector`. Do not hold them across mutations.
- Avoid C-style casts and `reinterpret_cast` (ES.48). Use `static_cast` for conversions, `std::bit_cast` for reinterpreting object representations and `std::memcpy` for byte copies. Never read a union member other than the one last written.
- Signed integer overflow is undefined behaviour. Use unsigned types or checked arithmetic for wraparound and size calculations, and enable `-Wconversion` and `-Wsign-conversion`. Do not mix signed and unsigned in comparisons.
- Do not use variable-length arrays, `alloca`, `gets`, `sprintf`, `strcpy` or `strcat`. Use `std::string`, `std::format` and `std::span`.
- `static` and global objects have order-of-initialisation hazards across translation units. Use function-local statics or explicit initialisation.
- Treat memory from `std::vector<char>` or `std::string` as bytes, not as typed objects; construct objects with `new`-free types or `std::start_lifetime_as` only if the project's standard supports it.
- Do not use exceptions or `new` in code paths the project forbids (embedded, real-time). Follow the project's rules there.

### Error handling

- Use exceptions for exceptional, non-local failures, and return values (`std::optional`, `std::expected` in C++23, error codes) for expected, local failures. Follow the project's policy and do not mix styles for one kind of failure.
- Destructors, move operations and `swap` must not throw (they are implicitly or explicitly `noexcept`). An exception escaping a `std::thread` function or a `noexcept` function terminates the program.
- Throw by value, catch by `const&`. Never throw pointers or built-in types. Do not use `catch (...)` except at a boundary that logs and rethrows or translates.
- Keep exceptions out of C ABI boundaries (callbacks passed to C libraries, `extern "C"` functions): catch and translate at the boundary.
- Mark functions `[[nodiscard]]` when ignoring the result is a bug (error codes, `expected`, resource handles).
- Use `assert` for internal invariants in debug builds; use explicit checks for input from outside.

### Concurrency

- Design to avoid shared mutable state. If data is shared, protect every access with the same mutex, or use `std::atomic` for single variables with simple operations.
- Take locks with RAII (`std::scoped_lock`, `std::unique_lock`), never plain `lock()` and `unlock()` (CP.20). Lock multiple mutexes in one `std::scoped_lock` call to avoid lock-order deadlocks. Do not call unknown code while holding a lock.
- Use `std::jthread` (C++20) instead of `std::thread`: it joins on destruction and carries a `std::stop_token` for cooperative cancellation. Do not detach threads (CP.26).
- Wait on a condition variable with a predicate (CP.42) to survive spurious wakeups and lost notifications.
- Leave memory order at the default sequentially consistent setting unless a measured need and a written justification exist.
- `std::async` and `std::future` have launch-policy and blocking-destructor surprises. Prefer a thread or task system the project already has.
- Never share a `std::vector`, `std::map` or `std::string` between threads without synchronisation, even for reads while another thread writes.
- `volatile` is not a synchronisation tool in C++.
- Treat coroutines and `std::execution` as advanced: use them only where the project already does, and review lifetime of captured state (a coroutine frame can outlive its caller's locals).
- Document the thread-safety of each class: immutable, internally synchronised, or externally synchronised.

### Interface and type design

- Make interfaces precisely typed (I.4): strong types and `enum class` instead of `int` and `bool` flags, `std::chrono` durations instead of raw numbers, and `explicit` on single-argument constructors.
- Pass cheap-to-copy types (up to roughly two or three words) by value, larger read-only types by `const&` (F.16), and sink parameters by value then `std::move`. Return values rather than using output parameters.
- Mark member functions `const` when they do not modify state, and use `constexpr` for compile-time computation. Use concepts (C++20) to constrain templates instead of unreadable error messages.
- Keep headers minimal: include what you use, forward-declare where possible, and use include guards or `#pragma once` consistently with the project.
- Prefer `std::vector` as the default container, `std::array` for fixed size, and `std::unordered_map` or `std::map` by need. Prefer algorithms and ranges to hand-written loops when they read more clearly.
- Modules (`import std;`) need compiler, build system and generator support. Do not introduce them unless the project already uses them.

### CMake

- Write target-based CMake: declare libraries and executables with `add_library` and `add_executable`, set properties per target, and link with `target_link_libraries` using `PUBLIC`, `PRIVATE` or `INTERFACE` to state whether consumers need the dependency. Avoid global `include_directories`, `link_libraries` and `add_definitions`.
- Require the standard through the target: `target_compile_features(<target> PUBLIC cxx_std_20)`. Set `CMAKE_CXX_EXTENSIONS OFF` for portable code.
- Build out of source. Keep one build directory per configuration; use `CMakePresets.json` so the same commands work locally and in CI (preset schema version 6 requires CMake 3.25 or later).
- Set `cmake_minimum_required` to the oldest CMake you actually test. Very old minimum versions hit removed compatibility behaviour in newer CMake releases (confirm against the release notes of the version you use, unverified for 4.x specifics).
- Export `compile_commands.json` (`CMAKE_EXPORT_COMPILE_COMMANDS`) for clang-tidy and editors.
- Put warning flags on an `INTERFACE` library or per-target options, not in `CMAKE_CXX_FLAGS`, and do not apply them to third-party code you fetch.
- Find dependencies with `find_package`. If the project fetches sources with `FetchContent`, pin to an exact tag or commit hash and treat adding one as a dependency decision that needs approval (see [dependency-management.md](dependency-management.md)).
- Run tests through `enable_testing()` and `ctest`. For test design, load `test-driven-development`.
- Do not glob source files for production targets without a re-run mechanism; list sources explicitly.

### Warnings and sanitizers

- Build with warnings on and keep them clean: for GCC and Clang `-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wnon-virtual-dtor -Woverloaded-virtual`; for MSVC `/W4 /permissive-`. Use `-Werror` in CI for the project's own code once the baseline is clean, not on first introduction.
- Run an address and undefined-behaviour sanitizer build for any change that touches ownership, buffers, casts, lifetimes or arithmetic: `-fsanitize=address,undefined -fno-omit-frame-pointer -g`. Add `-fno-sanitize-recover=undefined` so a finding fails the test.
- Thread sanitizer (`-fsanitize=thread`) is a separate build; it cannot be combined with address sanitizer. Run it for any change that adds or alters threading.
- Memory sanitizer (`-fsanitize=memory`) is Clang-only and needs an instrumented standard library. On MSVC use `/fsanitize=address`.
- Sanitizer builds are slower and use more memory; run them on the tests, not on production artefacts. Do not suppress a sanitizer finding without a recorded reason.
- Run clang-tidy with the `cppcoreguidelines-*` and `bugprone-*` checks the project enables, and the project's clang-format file. Do not reformat unrelated files.
- CI wiring for these builds belongs to `devops-deployment`.

## Examples

RAII for a C handle, bad to good:

```cpp
// Bad: leaks buf and file on the early return and on any exception.
void process(const char* path) {
    FILE* file = std::fopen(path, "rb");
    if (!file) return;
    char* buf = new char[4096];
    if (std::fread(buf, 1, 4096, file) == 0) return; // leak
    consume(buf);
    delete[] buf;
    std::fclose(file);
}

// Good
#include <array>
#include <cstdio>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>

struct FileCloser {
    void operator()(std::FILE* file) const noexcept { if (file) std::fclose(file); }
};
using FilePtr = std::unique_ptr<std::FILE, FileCloser>;

void process(const std::string& path) {
    FilePtr file{std::fopen(path.c_str(), "rb")};
    if (!file) throw std::runtime_error("cannot open " + path);
    std::array<char, 4096> buf{};
    const std::size_t n = std::fread(buf.data(), 1, buf.size(), file.get());
    consume(std::span<const char>{buf.data(), n}); // file closes on every path
}
```

Ownership stated in signatures:

```cpp
void render(const Widget& widget);                  // observes
void adopt(std::unique_ptr<Widget> widget);         // takes ownership
std::unique_ptr<Widget> make_widget(int size);      // transfers ownership to the caller
std::span<const int> window(const std::vector<int>& values, std::size_t first, std::size_t count);
```

Dangling view, bad to good:

```cpp
// Bad: the std::string temporary dies at the end of the statement.
std::string_view name = std::string("temporary");   // dangling
std::string_view label() { return std::string("x") + "y"; } // dangling

// Good: own the text; view it only while the owner lives.
std::string name = "temporary";
std::string_view view = name;                        // fine while name is alive
std::string label() { return std::string("x") + "y"; }
```

Condition variable with a predicate and a cooperative worker:

```cpp
#include <condition_variable>
#include <deque>
#include <mutex>
#include <stop_token>
#include <thread>

class Queue {
public:
    void push(int value) {
        { std::scoped_lock lock{mutex_}; items_.push_back(value); }
        ready_.notify_one();
    }
    int pop() {
        std::unique_lock lock{mutex_};
        ready_.wait(lock, [this] { return !items_.empty(); });
        const int value = items_.front();
        items_.pop_front();
        return value;
    }
private:
    std::mutex mutex_;
    std::condition_variable ready_;
    std::deque<int> items_;
};

void run_worker(Queue& queue) {
    std::jthread worker{[&queue](std::stop_token stop) {
        while (!stop.stop_requested()) {
            handle(queue.pop()); // a real worker would use a stop-aware wait
        }
    }};
} // destructor requests stop and joins
```

Target-based CMake with warnings and an optional sanitizer build:

```cmake
cmake_minimum_required(VERSION 3.25)
project(inventory VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(ENABLE_SANITIZERS "Build with address and undefined behaviour sanitizers" OFF)

add_library(project_warnings INTERFACE)
target_compile_options(project_warnings INTERFACE
  $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra -Wpedantic -Wconversion -Wshadow>
  $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive->)

add_library(inventory src/inventory.cpp)
target_include_directories(inventory PUBLIC include)
target_compile_features(inventory PUBLIC cxx_std_20)
target_link_libraries(inventory PRIVATE project_warnings)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE inventory)

if(ENABLE_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(inventory PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(inventory PUBLIC -fsanitize=address,undefined)
endif()

enable_testing()
```

Presets that give the same commands locally and in CI (`cmake --preset asan`, `cmake --build --preset asan`, `ctest --preset asan`):

```json
{
  "version": 6,
  "configurePresets": [
    { "name": "dev", "generator": "Ninja", "binaryDir": "${sourceDir}/build/dev",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug" } },
    { "name": "asan", "inherits": "dev", "binaryDir": "${sourceDir}/build/asan",
      "cacheVariables": { "ENABLE_SANITIZERS": "ON" } }
  ],
  "buildPresets": [
    { "name": "dev", "configurePreset": "dev" },
    { "name": "asan", "configurePreset": "asan" }
  ],
  "testPresets": [
    { "name": "dev", "configurePreset": "dev", "output": { "outputOnFailure": true } },
    { "name": "asan", "configurePreset": "asan", "output": { "outputOnFailure": true } }
  ]
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Naked `new` and `delete`, or `malloc` and `free` | Leaks on early return and exception | `std::make_unique`, containers, RAII wrappers |
| `shared_ptr` everywhere | Hidden lifetimes, cycles, atomic refcount cost | `unique_ptr` by default; references for observation |
| Returning `string_view` or `span` of a temporary or local | Use-after-free that often works in tests | Return an owning type |
| Holding iterators across `push_back` or `erase` | Undefined behaviour after reallocation | Use indices, re-acquire iterators, or reserve first |
| `std::thread` plus `detach` | Lifetime and shutdown races | `std::jthread` with stop tokens |
| `cv.wait(lock)` without a predicate | Spurious wakeups and missed notifications | `cv.wait(lock, predicate)` |
| Plain `mutex.lock()` and `unlock()` | A throw or early return leaves the mutex locked | `std::scoped_lock` or `std::unique_lock` |
| C-style casts and `reinterpret_cast` | Silent type and aliasing violations | `static_cast`, `std::bit_cast`, `std::memcpy` |
| Global `CMAKE_CXX_FLAGS` and `include_directories` | Settings leak into every target, including dependencies | Per-target properties with `PUBLIC`/`PRIVATE` |
| Skipping sanitizers for pointer or thread changes | Heap and race bugs ship | Run address, undefined behaviour and thread sanitizer builds |
| Adopting C++26 features early | Not portable, not yet published, partial compiler support | Stay on the project's pinned standard |
| Throwing from destructors or moves | Termination during unwinding, slow `vector` growth | `noexcept` and non-throwing cleanup |

## Checklist

- [ ] Does the code compile cleanly at the project's pinned standard with warnings enabled and no new warnings?
- [ ] Is there no naked `new`, `delete`, `malloc` or `free`?
- [ ] Does every function signature show who owns what (value, reference, `unique_ptr`, `span`)?
- [ ] Is every resource released by a destructor, including on exception paths?
- [ ] Are special member functions either all absent (rule of zero) or all deliberate?
- [ ] Is every variable initialised at declaration?
- [ ] Is there no returned reference, pointer or view to a local or temporary?
- [ ] Are casts limited to named C++ casts, each with a reason?
- [ ] Are locks taken with RAII types, with condition waits using predicates?
- [ ] Are threads `std::jthread` or joined, and are shared structures synchronised?
- [ ] Did an address and undefined-behaviour sanitizer build run clean for ownership, buffer or cast changes, and a thread sanitizer build for threading changes?
- [ ] Are CMake settings per target, with `PUBLIC` and `PRIVATE` chosen deliberately and no new dependency added without approval?

## Verify with context7 and gh_grep

- **context7:** query the compiler and library docs for the toolchain in use: "CMake `target_compile_features` and `cxx_std_20`", "CMake presets schema version and minimum CMake", "GCC and Clang `-fsanitize=address,undefined` options", "libstdc++ `_GLIBCXX_ASSERTIONS` and libc++ hardening mode names", "`std::jthread` and `std::stop_token`", and the API of every third-party library in the diff at its pinned version.
- **gh_grep:** search literal code: `std::make_unique<`, `std::scoped_lock`, `std::jthread`, `cv.wait(lock,`, `target_link_libraries(` with `PRIVATE`, `-fsanitize=address,undefined`, `CMAKE_EXPORT_COMPILE_COMMANDS`, `"version": 6` in `CMakePresets.json`. Prefer maintained repositories with permissive licences; do not copy code without a compatible licence.

## Sources

- C++ Core Guidelines repository (scope, "modern C++ means C++11 and newer", evolving without a release cadence): https://github.com/isocpp/CppCoreGuidelines
- Herb Sutter, "C++26 is done (again)", November 2026 WG21 meeting report (ballot status, contracts, `std::execution`; a committee-chair report, not an ISO publication): https://herbsutter.com/2026/11/21/c26-is-done-again-trip-report-november-2026-iso-c-standards-meeting-buzios-brazil/
- WG21 P5000R1, Directions for ISO C++29: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p5000r1.pdf
- CMake 4.2 release notes: https://cmake.org/cmake/help/v4.2/release/4.2.html
