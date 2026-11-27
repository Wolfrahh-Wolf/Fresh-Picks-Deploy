# JavaScript

Modern JavaScript for Node.js and browser code: modules, async, equality and coercion traps, and error handling. Assumes ECMAScript 2025 as the language baseline and Node.js 24 or 26 as the server runtime (Node.js 26 enters LTS in October 2026); checked 2026-11-26. The project's `package.json` (`engines`, `type`, `browserslist`) wins over every default here.

## Contents

- Baseline and project-first rules
- Modules
- Declarations, immutability and data
- Equality and coercion traps
- Numbers and dates
- Async code
- Error handling
- Structure and style

## Guidance

### Baseline and project-first rules

- Read `package.json` before writing: `"type"` (`module` or `commonjs`), `"engines"`, `"exports"`, and the lint, test and build scripts. Match what is there.
- Use only features the oldest supported runtime has. For browsers read `browserslist`; for Node.js read `engines`. If neither exists, ask which runtimes matter before using a feature from the last two ECMAScript editions.
- ES2025 adds, among others, `Promise.try`, iterator helper methods, and `Set` methods such as `union`; `RegExp.escape` arrived with it as well. Temporal and `Map.prototype.getOrInsert` reached stage 4 in 2026 but runtime support varies, so check target runtimes before use.
- For TypeScript projects, load the typescript reference as well: [typescript.md](typescript.md).

### Modules

- Prefer ES modules (`import` and `export`). In a Node.js package that sets `"type": "module"`, relative imports need the file extension: `import { parse } from "./parse.js"`.
- Use named exports. A default export makes renaming and searching harder and invites inconsistent import names.
- Keep modules free of side effects at import time. Do not open connections, read environment variables into mutable globals or start timers at the top level; export a function that does it.
- Break import cycles instead of working around them. A cycle usually means two modules share a third concept that deserves its own module.
- Resolve files relative to the module with `new URL("./data.json", import.meta.url)`, not with `__dirname`, which does not exist in ES modules.
- Mixing CommonJS and ESM: `require()` of an ES module and dynamic `import()` of CommonJS have version-specific behaviour. Check the Node.js version and context7 before depending on either.
- Restrict a package's public surface with the `"exports"` field. Do not deep-import another package's internal paths.

### Declarations, immutability and data

- Use `const` by default, `let` only when reassigned, never `var`. Do not create implicit globals; module code is strict by default.
- Treat input objects as read-only. Return new values. For arrays, `toSorted`, `toReversed`, `toSpliced` and `with` return copies; `sort`, `reverse` and `splice` mutate.
- Use `Map` and `Set` for dynamic keys and membership. Plain objects as dictionaries break on keys such as `__proto__` and `constructor`. For a plain-object lookup use `Object.hasOwn(obj, key)`, not `obj.hasOwnProperty(key)` or `key in obj`.
- Use `structuredClone` for deep copies of plain data. It throws on functions and drops prototypes; do not use `JSON.parse(JSON.stringify(x))`, which loses `undefined`, `Date`, `Map` and `BigInt`.
- Prefer `for...of` and array methods to index loops. Use `Array.prototype.at(-1)` for the last element, `Object.groupBy` for grouping, and `Array.prototype.includes` instead of `indexOf(...) !== -1`.
- Use optional chaining (`?.`) and nullish coalescing (`??`) deliberately; see the coercion section for why `||` is wrong for defaults.
- Use `#private` fields for true privacy in classes. Do not use underscore prefixes as a privacy mechanism.

### Equality and coercion traps

| Expression | Result | Rule |
|---|---|---|
| `0 == ""`, `null == undefined`, `"1" == 1` | `true` | Use `===` and `!==`. The one tolerated exception is `x == null` to test for both `null` and `undefined`, and only if the project's lint config allows it. |
| `NaN === NaN` | `false` | Use `Number.isNaN(x)` or `Object.is(x, NaN)`. The global `isNaN` coerces its argument. |
| `typeof null` | `"object"` | Test `x === null` first. |
| `value \|\| "default"` | replaces `0`, `""`, `false` | Use `value ?? "default"` when only `null` and `undefined` should fall back. |
| `[10, 9, 1].sort()` | `[1, 10, 9]` | Default sort compares strings. Always pass a comparator: `(a, b) => a - b`. |
| `parseInt("08")`, `parseInt("12px")` | `8`, `12` | `parseInt` stops silently at junk. Use `Number(s)` and check `Number.isFinite`, or validate the format first. |
| `"5" + 1`, `"5" - 1` | `"51"`, `4` | `+` concatenates when either side is a string. Convert explicitly before arithmetic. |
| `[] + {}`, `[] == false` | `"[object Object]"`, `true` | Never compare or add values of different types. |
| `if (arr)` | always true for `[]` | Test `arr.length > 0`. |

### Numbers and dates

- Numbers are IEEE 754 doubles. `0.1 + 0.2 !== 0.3`. Store money as integer minor units (cents) or use a decimal library; never accumulate floats.
- Integers beyond `Number.MAX_SAFE_INTEGER` lose precision. Use `BigInt` for IDs and counters that may exceed it, and note that `JSON.stringify` throws on `BigInt` without a custom replacer.
- `toFixed` returns a string and rounds by binary representation. Format for display only, at the edge.
- `Date` is mutable, months are zero-based and parsing non-ISO strings is implementation-defined. Store UTC instants (`toISOString`), pass ISO 8601 strings between systems, and keep time-zone logic in one module. Use Temporal only where target runtimes support it.

### Async code

- Use `async` and `await`. Every promise must be awaited, returned or explicitly handled. A floating promise hides failures; in Node.js an unhandled rejection terminates the process by default.
- Run independent work concurrently with `Promise.all`. Use `Promise.allSettled` when partial failure is acceptable and each result needs inspection. Do not `await` inside a loop for independent items unless order or rate limiting requires it.
- Bound concurrency. `Promise.all(items.map(fetchOne))` over ten thousand items opens ten thousand sockets. Process in batches or use a small queue helper the project already depends on.
- Put a timeout on every outbound call, and make work cancellable: pass `AbortSignal.timeout(ms)` or an `AbortController` signal to APIs that accept `signal`, and check `signal.aborted` in long loops.
- `async` functions always return a promise; a thrown error becomes a rejection. Do not mix callbacks and promises in one function. Wrap callback APIs once with `util.promisify` or a small hand-written wrapper.
- Event handlers and `setTimeout` callbacks that are `async` must contain their own `try`/`catch`, because nobody awaits them.
- Use `try`/`finally` for cleanup that must run after both success and failure. Return values from `try` blocks interact with `finally`; do not `return` inside `finally`.
- `Promise.try(fn)` (ES2025) runs a function that may throw synchronously or return a promise and always yields a promise. Check runtime support first.

### Error handling

- Throw `Error` objects, never strings or plain objects. Subclass `Error` for conditions callers must distinguish and set `name`.
- Wrap with context, keeping the cause: `throw new Error("load config failed", { cause: err })`.
- Catch only what you can handle. In `catch (err)`, `err` can be anything; check `err instanceof Error` before reading `.message`.
- Never leave an empty `catch`. Log once at the boundary that decides the outcome, not at every layer.
- Distinguish expected failures (validation, not found) from bugs. Expected failures return typed results or throw a specific class; bugs propagate to a top-level handler that logs and fails the request or process.
- `JSON.parse` throws on bad input and returns untyped data. Wrap it and validate the result before using it.
- Use `AggregateError` and `Promise.any` when "first success wins" and all-failed is a real state.

### Structure and style

- Keep functions short enough to read without scrolling and focused on one level of abstraction. Prefer early returns over deep nesting.
- Pass an options object when a function takes more than three parameters or any boolean flags, so call sites read clearly.
- Avoid `this` pitfalls: do not pass unbound methods as callbacks; prefer arrow functions or closures where binding is needed.
- Do not use `eval`, `new Function` or `with`. For HTML and URL handling in the browser, load `frontend-engineering`.
- Run the project's formatter and linter; do not hand-argue style. For design questions, see [solid.md](solid.md) and [refactoring.md](refactoring.md).

## Examples

Equality and defaults, bad to good:

```js
// Bad: 0 and "" are replaced; sort is lexicographic; NaN check always false.
function pageSize(opts) {
  return opts.size || 20; // size: 0 becomes 20
}
const ids = [10, 9, 1].sort(); // [1, 10, 9]
if (value === NaN) { /* never runs */ }

// Good
function pageSize(opts) {
  return opts.size ?? 20;
}
const ids = [10, 9, 1].toSorted((a, b) => a - b); // [1, 9, 10]
if (Number.isNaN(value)) { /* runs */ }
```

Concurrency with a timeout, an error cause and bounded fan-out (Node.js 18 or later):

```js
export async function fetchJson(url, { timeoutMs = 5000 } = {}) {
  const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  if (!response.ok) {
    throw new Error(`GET ${url} failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchAll(urls, batchSize = 5) {
  const results = [];
  for (let i = 0; i < urls.length; i += batchSize) {
    const batch = urls.slice(i, i + batchSize);
    const settled = await Promise.allSettled(batch.map((u) => fetchJson(u)));
    results.push(...settled);
  }
  return results; // each item is { status: "fulfilled", value } or { status: "rejected", reason }
}

try {
  await fetchJson("https://example.invalid/data");
} catch (err) {
  throw new Error("refresh failed", { cause: err });
}
```

Dictionary safety:

```js
// Bad: user-controlled key can collide with Object.prototype members.
const counts = {};
counts[word] = (counts[word] ?? 0) + 1; // word === "__proto__" misbehaves

// Good
const counts = new Map();
counts.set(word, (counts.get(word) ?? 0) + 1);
```

ES module with explicit extension and no import-time side effects:

```js
// package.json contains: { "type": "module" }
import { loadConfig } from "./config.js";

export function createApp(env = process.env) {
  const config = loadConfig(env); // work happens when called, not when imported
  return { port: config.port };
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using `\|\|` for defaults | Valid values `0`, `""` and `false` get replaced | Use `??` |
| Calling `.sort()` without a comparator | Numbers sort as strings, silently wrong order | Pass a comparator; use `toSorted` to avoid mutation |
| Floating promises and `async` callbacks without `try`/`catch` | Failures vanish or crash the process on a later tick | `await`, return or `.catch` every promise |
| `await` in a loop over independent items | Latency adds up linearly | `Promise.all` or `allSettled` with bounded batches |
| `Promise.all` over unbounded input | Socket, memory or rate-limit exhaustion | Batch or use a queue |
| No timeout on `fetch` or sockets | One slow dependency stalls the whole service | `AbortSignal.timeout` on every call |
| Throwing strings or swallowing in empty `catch` | No stack, no cause, no diagnosis | Throw `Error` with `cause`; handle or rethrow |
| Plain objects keyed by user input | Prototype keys corrupt behaviour | `Map`, or `Object.create(null)` plus `Object.hasOwn` |
| Float arithmetic on money | Rounding drift | Integer minor units or a decimal library |
| Mixing `require` and `import` casually | Runtime errors that depend on Node.js version and file type | Pick one module system per package and follow `"type"` |
| Top-level side effects in modules | Import order bugs, untestable code | Export functions; run work from an explicit entry point |

## Checklist

- [ ] Does `package.json` (`type`, `engines`, `exports`) agree with the module syntax used?
- [ ] Do relative ESM imports include file extensions where Node.js requires them?
- [ ] Is every promise awaited, returned or handled?
- [ ] Does every outbound call have a timeout or abort signal?
- [ ] Is concurrency bounded for any input of unknown size?
- [ ] Are all comparisons `===` (or a documented `== null`)?
- [ ] Are defaults written with `??` where `0`, `""` or `false` are valid?
- [ ] Does every `sort` have a comparator?
- [ ] Do thrown values extend `Error`, and do wrapped errors carry `cause`?
- [ ] Is there no empty `catch` and no `return` inside `finally`?
- [ ] Is parsed JSON validated before use?
- [ ] Are money and IDs safe from float and 53-bit precision loss?
- [ ] Are user-keyed lookups on `Map`, `Set` or `Object.hasOwn`-guarded objects?
- [ ] Does the code avoid features missing from the oldest supported runtime?

## Verify with context7 and gh_grep

- **context7:** query the Node.js documentation for the project's major version: "ECMAScript modules `package.json` `type` and `exports`", "`AbortSignal.timeout` and `fetch` signal", "unhandled rejections default behaviour", "`require()` of ES modules support in this version". For browser code, query the MDN-backed library for the feature and its compatibility notes (`Array.prototype.toSorted`, `Object.groupBy`, `structuredClone`, `Promise.try`).
- **gh_grep:** search literal patterns in maintained repositories to see real usage: `AbortSignal.timeout(`, `Promise.allSettled(`, `new Error(` followed by `{ cause`, `Object.hasOwn(`, `"type": "module"` in `package.json`, `structuredClone(`. Prefer repositories with recent commits and a permissive licence; do not copy code without a compatible licence.

## Sources

- Node.js release schedule announcement ("Evolving the Node.js Release Schedule"): https://nodejs.org/en/blog/announcements/evolving-the-nodejs-release-schedule
- Announcing TypeScript 6.0 (ES2025 library contents, Temporal and upsert stage 4 status, `RegExp.escape`): https://devblogs.microsoft.com/typescript/announcing-typescript-6.0/
