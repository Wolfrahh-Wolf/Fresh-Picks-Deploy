# Python

Idiomatic Python: language idioms, type hints, packaging, virtual environments, `asyncio` and common traps. Assumes CPython 3.12 to 3.15 (3.14 released 2025-10-07, 3.15 released 2026-10-09); checked 2026-11-26. The project's `requires-python` and CI matrix decide which features are allowed.

## Contents

- Version and feature availability
- Idioms
- Type hints
- Packaging and project layout
- Virtual environments
- Async code
- Common traps

## Guidance

### Version and feature availability

- Read `requires-python` in `pyproject.toml` (or `python_requires`, `.python-version`, CI matrix) before writing. Use only syntax and library features available at the lowest supported version.
- Available from 3.12: PEP 695 generics and the `type` statement (`def first[T](xs: list[T])`, `type UserId = int`), `typing.override`. From 3.11: `asyncio.TaskGroup`, `asyncio.timeout`, `ExceptionGroup` with `except*`, `datetime.UTC`. From 3.10: `match`, `X | Y` unions, `zip(strict=True)`, `dataclass(slots=True, kw_only=True)`.
- 3.14 evaluates annotations lazily (PEP 649 and 749): forward references no longer need quotes, and the `annotationlib` module inspects them. `from __future__ import annotations` still works. Code that must run on 3.12 or 3.13 keeps quotes or the future import.
- 3.15 adds explicit lazy imports (`lazy import json`), a `frozendict` builtin, a `sentinel` builtin, unpacking in comprehensions (`[*row for row in rows]`), `TaskGroup.cancel`, and makes UTF-8 the default text encoding. It also adds `TypedDict` `closed` and `extra_items` and `typing.TypeForm`. Use none of these unless every supported interpreter has them.
- Never rely on the 3.15 UTF-8 default for portability: always pass `encoding="utf-8"` to `open` and `Path.read_text`.
- Free-threaded (no-GIL) builds exist and macOS binaries in 3.15 install them by default. Do not assume the GIL makes compound operations such as `counter += 1` atomic; protect shared mutable state with a lock regardless.

### Idioms

- Follow PEP 8 naming (`snake_case`, `PascalCase`, `UPPER_CASE`). Run the project's formatter and linter (Ruff, Black, flake8 or similar) rather than hand-formatting.
- Use comprehensions and generator expressions for simple transformations; use a loop when the body needs more than one clear step. Do not nest comprehensions beyond two levels.
- Use `pathlib.Path` for paths, `with` for resources, `enumerate` instead of `range(len(x))`, `zip(a, b, strict=True)` when lengths must match, and f-strings for formatting.
- Prefer EAFP for expected races and absent keys (`try`/`except KeyError`) and LBYL when the check is cheap and failure would be destructive. Use `dict.get(key)` with an explicit `is None` test when `None` is not a valid stored value.
- Test identity with `is None` and `is not None`. Test emptiness with truthiness only when `0`, `""` and `[]` are all "empty" for your purpose.
- Use `dataclasses` (or `NamedTuple`) for data carriers. Use `frozen=True, slots=True, kw_only=True` by default for value objects. Use `enum.Enum` or `StrEnum` for closed sets.
- Use `match` for structural dispatch over tagged data; use `if` chains for simple conditions.
- Use `logging` with module-level `logger = logging.getLogger(__name__)`, never `print`, for diagnostics. Pass values as arguments (`logger.info("loaded %s", name)`), not pre-formatted strings.
- Use `functools.cache` for pure functions with hashable arguments; use `contextlib.contextmanager` for setup and teardown pairs.
- Keep module import-time work minimal. Put runnable code under `if __name__ == "__main__":` or a console-script entry point.
- Use `assert` for internal invariants only. It disappears under `python -O`; never use it to validate input.

### Type hints

- Annotate every public function, method and module-level constant. Annotate locals only when inference fails.
- Write `str | None`, `list[int]`, `dict[str, int]` with built-in generics. Do not import `List`, `Dict` or `Optional` in new code.
- Accept the widest useful abstraction and return the concrete type: parameters as `Iterable`, `Sequence` or `Mapping` from `collections.abc`; returns as `list`, `dict` or a dataclass.
- Use `Protocol` for structural interfaces (duck typing with checking), `TypedDict` for dictionary shapes you do not control, `Literal` for fixed strings, `Final` for constants, `Self` for fluent methods and `@override` to catch renamed base methods.
- Use `Any` only at genuinely dynamic edges and `object` when "anything, but I will check". Avoid `cast`; when needed, put it directly after the runtime check that justifies it.
- Suppress narrowly: `# type: ignore[specific-code]` with a reason. A bare `# type: ignore` hides unrelated errors.
- Run a static checker the project already configures (mypy, pyright or another) in CI with a strict profile for new code. Introduce strictness per module if the codebase is large; do not weaken existing settings.
- Annotations are not enforced at runtime. Validate untrusted input at boundaries with explicit checks or a validation library the project already uses. For web request models and serialization, load `backend-engineering` and `api-engineering`.
- Use `TYPE_CHECKING` imports to break import cycles that exist only for annotations.

### Packaging and project layout

- Declare the project in `pyproject.toml` with a `[project]` table: `name`, `version` (or dynamic), `requires-python`, `dependencies`, and `[project.scripts]` for console commands. Use `[dependency-groups]` (PEP 735) for development-only tools such as test runners and linters when the project's tooling supports it.
- Use a `src/` layout for libraries so tests run against the installed package, not the working directory.
- Pick the build backend the project already uses (setuptools, hatchling, flit-core, pdm-backend or another) and do not switch it as a side effect.
- Libraries declare compatible ranges in `pyproject.toml`; applications additionally commit a lock file. For lockfile formats (`uv.lock`, `pylock.toml` from PEP 751, hashed `requirements.txt`) and upgrade procedure, see [dependency-management.md](dependency-management.md).
- Keep one source of truth for dependencies. Do not maintain both `requirements.txt` and `pyproject.toml` by hand with different contents.
- Include `py.typed` in packages that ship type hints.

### Virtual environments

- Use one environment per project, kept out of version control (`.venv/` in `.gitignore`). Never install project dependencies into the system interpreter and never run `sudo pip`.
- Create and use it with the interpreter explicitly: `python -m venv .venv`, activate (`source .venv/bin/activate` on POSIX shells, `.venv\Scripts\Activate.ps1` in PowerShell), then `python -m pip install -e .`. If the project uses uv, Poetry, PDM or Hatch, use that tool's commands instead and do not mix tools.
- Distribution-managed interpreters may mark themselves externally managed (PEP 668) and refuse global `pip install`. That is a signal to use a virtual environment, not to force the install.
- Installing packages runs third-party build and install code and changes the environment. Treat adding a dependency as an approval-gated action; see [dependency-management.md](dependency-management.md).
- Record the interpreter version in `.python-version` or the CI configuration so everyone runs the same one.

### Async code

- Use `asyncio.run(main())` as the single entry point. Do not create or manage event loops by hand in application code.
- Never block the event loop. Replace `time.sleep` with `await asyncio.sleep`, blocking HTTP or file calls with async clients, or offload with `await asyncio.to_thread(func, *args)`.
- Run concurrent children with `asyncio.TaskGroup`: all tasks are awaited, a failure cancels siblings, and errors arrive as an `ExceptionGroup` (handle with `except*`). Use `asyncio.gather(..., return_exceptions=True)` only when you intend to inspect each outcome.
- Bound waits with `async with asyncio.timeout(seconds):` and propagate cancellation. Do not catch `asyncio.CancelledError` without re-raising it after cleanup.
- Keep a reference to every task created with `asyncio.create_task`; unreferenced tasks can be garbage-collected mid-flight and their exceptions are lost. Prefer `TaskGroup` over bare `create_task`.
- Use `async with` and `async for` for resources and streams. Do not call `asyncio.run` inside a running loop.
- Limit concurrency with `asyncio.Semaphore` when fanning out to an external service.
- Do not mix threads and the loop casually. Cross into the loop from a thread with `asyncio.run_coroutine_threadsafe` or `loop.call_soon_threadsafe`.

### Common traps

- **Mutable default arguments** are created once at definition time and shared across calls. Use `None` and create the object inside the function.
- **Late-binding closures**: a lambda in a loop sees the final loop value. Bind with a default argument (`lambda i=i: i`) or `functools.partial`.
- **`is` versus `==`**: `is` compares identity. Small-integer and string interning make wrong code appear to work. Use `==` for values and `is` only for `None`, `True`, `False` and sentinels.
- **Bare `except:` and `except Exception: pass`** swallow `KeyboardInterrupt`, bugs and cancellation. Catch the narrowest exception, and log or re-raise.
- **Mutating while iterating** a list or dict raises or skips items. Iterate over a copy or build a new collection.
- **Naive datetimes**: `datetime.utcnow()` is deprecated since 3.12 and returns a naive value. Use `datetime.now(UTC)`, store aware datetimes and convert at the edges.
- **Float money**: use `decimal.Decimal` built from strings, or integer minor units.
- **Class attributes shared by instances**: a list assigned in the class body is shared. Create it in `__init__` or use `field(default_factory=list)`.
- **Text encoding**: `open()` without `encoding` depends on the platform before 3.15. Always pass `encoding="utf-8"`.
- **`subprocess` with `shell=True`** and string interpolation allows command injection. Pass a list of arguments with `shell=False`.
- **`pickle`, `yaml.load` and `eval` on untrusted data** execute code. Use JSON or `yaml.safe_load`.
- **`re.match` only anchors at the start**; use `re.fullmatch` for whole-string checks. 3.15 adds `re.prefixmatch` as a clearer alias for the old `re.match` behaviour.
- **Circular imports** signal tangled modules. Move the shared piece into its own module before reaching for local imports.
- **Shadowing builtins** (`list`, `id`, `type`, `input`, `file`) causes confusing errors; rename the variable.

## Examples

Typed value objects with a structural interface:

```python
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLine:
    sku: str
    quantity: int


class PriceSource(Protocol):
    def price_cents(self, sku: str) -> int: ...


def total_cents(lines: Iterable[OrderLine], prices: PriceSource) -> int:
    return sum(line.quantity * prices.price_cents(line.sku) for line in lines)
```

PEP 695 generics and a `type` alias (3.12 or later):

```python
from collections.abc import Sequence

type UserId = int


def first[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None
```

Mutable default and naive datetime, bad to good:

```python
# Bad
from datetime import datetime

def add_tag(tag, tags=[]):          # the same list is reused across calls
    tags.append(tag)
    return tags

created = datetime.utcnow()          # naive and deprecated since 3.12

# Good
from datetime import UTC, datetime

def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    result = [] if tags is None else list(tags)
    result.append(tag)
    return result

created = datetime.now(UTC)
```

Structured concurrency with a timeout and an offloaded blocking call (3.11 or later):

```python
import asyncio
from pathlib import Path


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")  # blocking


async def load_all(paths: list[Path]) -> list[str]:
    async with asyncio.timeout(10):
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(asyncio.to_thread(read_file, p)) for p in paths]
    return [task.result() for task in tasks]


async def main() -> None:
    try:
        texts = await load_all([Path("a.txt"), Path("b.txt")])
    except* FileNotFoundError as group:
        print(f"{len(group.exceptions)} file(s) missing")
    else:
        print(len(texts))


if __name__ == "__main__":
    asyncio.run(main())
```

A minimal `pyproject.toml` (package names are illustrative):

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "inventory"
version = "1.2.0"
requires-python = ">=3.12"
dependencies = ["example-client>=2.1,<3"]

[project.scripts]
inventory = "inventory.cli:main"

[dependency-groups]
dev = ["pytest>=8", "mypy>=1.10"]

[tool.mypy]
strict = true
python_version = "3.12"
```

Setting up and using an environment in PowerShell, then installing the project in editable mode:

```text
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pytest
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `def f(x, items=[])` | State leaks between calls | `items: list[str] \| None = None`, create inside |
| `except Exception: pass` | Hides bugs and cancellation | Catch specific errors; log or re-raise |
| Blocking calls inside `async def` | Freezes every task on the loop | Async client or `asyncio.to_thread` |
| `create_task` without keeping the result | Task can be collected; exception lost | `TaskGroup` or store the task and await it |
| Swallowing `CancelledError` | Breaks timeouts and shutdown | Clean up and re-raise |
| `datetime.utcnow()` | Naive, deprecated, wrong when compared with aware values | `datetime.now(UTC)` |
| `open(path)` without `encoding` | Different text on different platforms (before 3.15) | `encoding="utf-8"` always |
| Global `pip install` or `sudo pip` | Pollutes the system, conflicts across projects | Project virtual environment |
| `assert` for input validation | Stripped under `-O` | Raise `ValueError` or a specific error |
| Bare `# type: ignore` | Masks unrelated errors | `# type: ignore[code]` plus a reason |
| `requirements.txt` and `pyproject.toml` drifting apart | Different installs in CI and locally | One source of truth, generated exports only |
| Using 3.15-only features on a 3.12 project | Syntax errors on supported interpreters | Check `requires-python` first |

## Checklist

- [ ] Does every language and library feature used exist in the lowest `requires-python` version?
- [ ] Are all public functions and methods annotated, with no bare `# type: ignore`?
- [ ] Does the configured type checker pass with no new errors?
- [ ] Are there no mutable default arguments and no class-level mutable state shared by accident?
- [ ] Does every `open`, `read_text` and `write_text` call pass `encoding="utf-8"`?
- [ ] Are datetimes timezone-aware and money values `Decimal` or integer minor units?
- [ ] Is untrusted input validated at the boundary rather than assumed from annotations?
- [ ] Is every async task awaited through a `TaskGroup` or a retained reference?
- [ ] Does every async I/O path have a timeout, and is `CancelledError` re-raised?
- [ ] Is no blocking call made on the event loop?
- [ ] Is the virtual environment untracked and the interpreter version recorded?
- [ ] Is there a single source of truth for dependencies in `pyproject.toml`?
- [ ] Are subprocess calls list-form without `shell=True`?

## Verify with context7 and gh_grep

- **context7:** query the Python documentation for the project's interpreter version: "`asyncio.TaskGroup` and `ExceptionGroup` handling", "`asyncio.timeout` behaviour on cancellation", "PEP 695 `type` statement and generic syntax", "annotation evaluation with `annotationlib`", "dataclass `slots` and `kw_only`". Query the project's type checker and packaging tool docs for strictness flags and the `[dependency-groups]` and `[project.scripts]` tables.
- **gh_grep:** search literal code: `asyncio.TaskGroup()`, `async with asyncio.timeout(`, `datetime.now(UTC)`, `field(default_factory=list)`, `class .*\(Protocol\):`, `requires-python = ">=3.12"`, `[dependency-groups]`. Prefer maintained projects with a permissive licence and recent commits.

## Sources

- What's new in Python 3.14 (deferred annotations, `annotationlib`): https://docs.python.org/3/whatsnew/3.14.html
- What's new in Python 3.15 (lazy imports, `frozendict`, `sentinel`, UTF-8 default, typing additions, `TaskGroup.cancel`, `re.prefixmatch`): https://docs.python.org/3.15/whatsnew/3.15.html
- PEP 751, a file format to record Python dependencies (status Final): https://peps.python.org/pep-0751/
