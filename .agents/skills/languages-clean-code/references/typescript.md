# TypeScript

TypeScript strictness, narrowing, generics, `unknown` over `any`, runtime validation at boundaries, and `tsconfig.json`. Assumes TypeScript 6.0 (released 2026-03-23) and 7.0 (native compiler, released 2026-07-08); checked 2026-11-26. The project's installed `typescript` version and existing `tsconfig.json` win over every default here.

## Contents

- Which compiler the project runs
- tsconfig baseline
- Strictness and escape hatches
- Narrowing
- Generics
- `unknown` over `any` and runtime validation boundaries
- Type design
- Modules and resolution

## Guidance

### Which compiler the project runs

- Read the `typescript` entry in `package.json` and the lockfile. Do not assume the major version.
- TypeScript 6.0 is the last release on the JavaScript codebase and the bridge to 7.0. TypeScript 7.0 is a native port, typically 8x to 12x faster on full builds, and ships its own `tsc`. Its first release has no programmatic compiler API; the team expects a new API in 7.1.
- Tools that import `typescript` directly (typescript-eslint, Volar-based tooling, framework plugins) still need the 6.0 API. The official side-by-side route is an npm alias: keep `"typescript": "npm:@typescript/typescript6@^6.0.2"` for tooling, which provides a `tsc6` binary, and add `"@typescript/native": "npm:typescript@^7.0.2"` so `tsc` runs 7.0.
- Projects using Vue, MDX, Astro or Svelte language tooling should stay on 6.0 until their tools support 7.0. Upgrading the compiler major is a dependency upgrade: follow [dependency-management.md](dependency-management.md) and get approval.
- Options deprecated in 6.0 are hard errors in 7.0. In 6.0 you can silence them with `"ignoreDeprecations": "6.0"`, but that is a stopgap with an end date, not a fix.

### tsconfig baseline

Defaults changed in 6.0 and carry into 7.0: `strict` is `true`, `module` is `esnext`, `target` floats to the newest stable ES version (currently `es2025`), `noUncheckedSideEffectImports` is `true`, `libReplacement` is `false`, `rootDir` is the directory of `tsconfig.json`, and `types` is `[]`.

- **Set options explicitly** even where the default now matches. Explicit values survive version changes and make review easy.
- Set `types` to the globals you need (`["node"]`, or `["node", "vitest/globals"]`). An empty default means missing globals appear as "Cannot find name" errors.
- Set `rootDir` to the source folder (`./src`) if output should not contain a `src/` prefix.
- Removed or deprecated in 6.0 and errors in 7.0: `target: es5`, `downlevelIteration`, `moduleResolution: node` (node10) and `classic`, `module: amd | umd | systemjs | none`, `baseUrl`, `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, `alwaysStrict: false`, `outFile`, and the `module` keyword for namespaces. Replace `baseUrl` by putting the prefix in `paths` values.
- Choose resolution by runtime: `nodenext` for Node.js run directly, `bundler` (with `module: preserve` or `esnext`) when a bundler or Bun runs the code.
- Add strictness that `strict` does not include: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noFallthroughCasesInSwitch`. Add `verbatimModuleSyntax` and `isolatedModules` when files are compiled one at a time by a bundler or transpiler.
- Use `tsc --noEmit` as the type gate in the project's `type-check` command. A bundler that strips types does not check them.
- Command-line `tsc file.ts` with a `tsconfig.json` present is an error in 6.0 and later unless `--ignoreConfig` is passed. Run `tsc -p .` or plain `tsc` instead.

### Strictness and escape hatches

- Never write `any` in new code. If a type is truly unknown, use `unknown` and narrow. Use `never` for impossible states.
- Use `// @ts-expect-error <reason>` instead of `// @ts-ignore`. `@ts-expect-error` fails when the error disappears, so stale suppressions are caught.
- Treat `as` casts and the non-null assertion `!` as claims you must prove. Allowed locations: directly after a runtime check the compiler cannot see, or in test setup. Each needs a comment saying what guarantees it.
- Use `satisfies` to check a value against a type without widening it: `const routes = { home: "/" } satisfies Record<string, string>`.
- Annotate exported function parameters and return types. Let inference handle locals.
- Keep `skipLibCheck` as the project has it, but do not use it to hide errors in your own `.d.ts` files.
- JavaScript files checked through JSDoc behave differently in 7.0 (no `@enum`, no Closure-style function types, no postfix `!`). If the project checks `.js` with `checkJs`, read the 7.0 differences before upgrading.

### Narrowing

- Use `typeof`, `instanceof`, `in`, `Array.isArray`, equality and truthiness checks, and let control flow narrow. Narrowing works on `const` and on parameters you do not reassign.
- Model variants as discriminated unions with a literal tag (`kind`, `type`, `status`). Switch on the tag and finish with an exhaustiveness check that assigns the value to `never`, so adding a variant breaks compilation where it is unhandled.
- Write user-defined type guards (`x is T`) for reusable checks. A guard that lies is worse than a cast, so test it. Since TypeScript 5.5 the compiler infers predicates for simple arrow functions, so `.filter((n) => n !== undefined)` yields a narrowed array type.
- Use assertion functions (`asserts x is T`) for "throw unless" helpers at boundaries.
- After narrowing inside a callback, remember that mutable variables lose narrowing. Copy to a `const` first.
- `noUncheckedIndexedAccess` makes `arr[i]` and `record[key]` include `undefined`. Handle it with a check or a default; do not silence it with `!`.

### Generics

- Add a type parameter only when it relates two or more positions (input to output, key to value). A parameter used once should be the concrete type or `unknown`.
- Constrain with `extends`: `<T extends object, K extends keyof T>`. An unconstrained `T` cannot be indexed or called.
- Let inference choose type arguments from call arguments. If callers must write `f<Foo>(...)` every time, the signature is probably wrong.
- Use `const` type parameters (`<const T extends readonly unknown[]>`) to preserve literal tuples without callers writing `as const`.
- Keep conditional and mapped types shallow. If a type needs more than a screen of logic, simplify the API instead; error messages become unreadable.
- In 6.0, a function that never uses `this` is no longer treated as context-sensitive for generic inference, so object-literal methods like `consume(y) { ... }` now infer from sibling properties in either order. Do not add casts to work around old inference failures; re-check after upgrading.
- Prefer overloads rarely. A union parameter or a generic usually says the same thing more simply.

### `unknown` over `any` and runtime validation boundaries

Types are erased at runtime. A declared type does not prove anything about data from outside the process.

- Treat these as untrusted and type them `unknown` on arrival: `JSON.parse` results, request bodies and query strings, `process.env` values, database rows from untyped drivers, message-queue payloads, `localStorage`, `postMessage` data, third-party API responses, and file contents.
- Parse, don't cast: write one function per boundary, `parseX(input: unknown): X`, that checks every field and returns a correctly typed value or throws a specific error. Inside the boundary the code works with real types and needs no further checks.
- Use a schema library already in the project to generate both the validator and the static type from one definition, so they cannot drift. If none exists, hand-written guards are fine for small shapes; adding a library is a dependency decision that needs approval.
- Validate strictly: reject unknown fields where extra data is dangerous, check ranges and formats, and return field-level errors for user input.
- For request and response schema design and error formats, load `api-engineering`. This file covers only the language-level boundary pattern.
- `catch (err)` binds `unknown` under `strict` (`useUnknownInCatchVariables`). Narrow with `instanceof Error` before reading properties.
- Type environment configuration once, in one module that fails fast at startup, instead of reading `process.env.X` throughout the code.

### Type design

- Prefer unions of string literals (or `as const` objects) over `enum`. Enums emit runtime code, numeric enums accept arbitrary numbers, and `const enum` breaks under single-file transpilation.
- Use `readonly` and `ReadonlyArray` for data you do not mutate. Prefer `type` aliases for unions and `interface` for object shapes you expect to extend; be consistent with the project.
- Use optional properties (`?`) only when a value can be absent. With `exactOptionalPropertyTypes`, `{ a?: string }` does not accept an explicit `undefined`.
- Brand primitives that must not be mixed (`UserId` versus `OrderId`) with an intersection tag and create them through one validating function.
- Prefer small, composable types over deep inheritance. Use `Pick`, `Omit` and `Partial` sparingly; a named type usually reads better than a chain.
- Use `import type` (or `verbatimModuleSyntax` with `type` modifiers) for type-only imports so they are erased predictably.
- Never export a type that exposes an `any`. It infects every consumer.

### Modules and resolution

- In Node.js ESM packages, relative imports are written with the output extension (`./util.js`) even when the source file is `util.ts`. Do not write `.ts` extensions unless the project enables the rewriting option and its toolchain supports it.
- Subpath imports from `package.json` `imports` can now start with `#/` under `nodenext` and `bundler` resolution (6.0). Use them instead of long relative paths, and keep `paths` mappings for bundler-only aliases.
- `esModuleInterop` is always on from 6.0; write `import express from "express"`, not `import * as express`.
- Keep type-only packages (`@types/*`) in development dependencies and list them in `types` when they declare globals.

## Examples

A tsconfig for an ES module Node.js service (TypeScript 6.0 or 7.0):

```json
{
  "compilerOptions": {
    "target": "es2025",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "types": ["node"],
    "rootDir": "./src",
    "outDir": "./dist"
  },
  "include": ["./src"]
}
```

Discriminated union with an exhaustiveness check:

```ts
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rect":
      return shape.width * shape.height;
    default: {
      const unreachable: never = shape; // compile error if a variant is added and not handled
      return unreachable;
    }
  }
}
```

Boundary parsing, bad to good:

```ts
// Bad: a cast asserts what nobody checked.
interface User { id: number; name: string }
const user = JSON.parse(text) as User; // runtime data may be anything

// Good: unknown in, proven type out.
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseUser(input: unknown): User {
  if (!isRecord(input)) throw new TypeError("user must be an object");
  const { id, name } = input;
  if (typeof id !== "number" || !Number.isInteger(id)) {
    throw new TypeError("user.id must be an integer");
  }
  if (typeof name !== "string" || name.length === 0) {
    throw new TypeError("user.name must be a non-empty string");
  }
  return { id, name };
}

const parsed = parseUser(JSON.parse(text));
```

Generics, bad to good:

```ts
// Bad: any in, any out; typos in key compile.
function getProp(obj: any, key: string): any {
  return obj[key];
}

// Good: the return type follows the key.
function getProp<T extends object, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const port = getProp({ port: 8080, host: "localhost" }, "port"); // number
```

Fail-fast environment access:

```ts
export function requireEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}
```

Package.json aliasing so tooling keeps the 6.0 API while `tsc` is 7.0:

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `JSON.parse(x) as T` | The cast removes checking exactly where data is least trustworthy | `parseT(input: unknown): T` with real checks or a schema |
| `any` in signatures and generics | Disables checking for every caller | `unknown` and narrowing, or a constrained generic |
| `// @ts-ignore` with no reason | Hides errors and survives after the bug is fixed | `// @ts-expect-error <reason>`, scoped to one line |
| Non-null `!` to quiet `noUncheckedIndexedAccess` | Replaces a check with a crash at runtime | Test for `undefined` or supply a default |
| Relying on `tsconfig` defaults | Defaults changed in 6.0; behaviour differs across versions | Set `strict`, `module`, `moduleResolution`, `target`, `types`, `rootDir` explicitly |
| Leaving `types` empty after upgrading | "Cannot find name" errors for `process`, `describe` and other globals | List the global-declaring packages in `types` |
| Using `baseUrl` or `moduleResolution: node` | Errors in 7.0 and a deprecation in 6.0 | Prefix `paths` values; use `nodenext` or `bundler` |
| `enum` for simple option sets | Runtime code, loose numeric enums, single-file transpile hazards | Union of string literals or `as const` object |
| Unconstrained generics used once | Extra complexity with no safety | Use the concrete type or `unknown` |
| Treating bundler success as type safety | Bundlers strip types without checking | Run `tsc --noEmit` in the type-check command |
| Importing tooling that needs the compiler API against 7.0 alone | Tools break because 7.0 has no programmatic API yet | Alias the 6.0 package for tooling as shown above |

## Checklist

- [ ] Is the compiler version (6.x or 7.x) read from the lockfile rather than assumed?
- [ ] Are `strict`, `module`, `moduleResolution`, `target`, `types` and `rootDir` set explicitly?
- [ ] Is `moduleResolution` `nodenext` or `bundler`, with no `baseUrl` and no `node10`?
- [ ] Does the type-check command run `tsc --noEmit` (or the project build with type checking) and pass?
- [ ] Is there no `any` in new code and no `@ts-ignore`?
- [ ] Does every `as` cast and every `!` have a comment naming what guarantees it?
- [ ] Is every external input typed `unknown` and passed through a parse or validation function?
- [ ] Do switches over discriminated unions end with a `never` exhaustiveness check?
- [ ] Are exported functions annotated with parameter and return types?
- [ ] Are generic parameters constrained and each used in at least two positions?
- [ ] Do relative ESM imports use output extensions where Node.js requires them?
- [ ] Is a compiler major-version change recorded as an approved dependency upgrade?

## Verify with context7 and gh_grep

- **context7:** query the `typescript` documentation for the installed version: "tsconfig `strict` flags and defaults", "`moduleResolution` nodenext versus bundler", "`noUncheckedIndexedAccess`", "`exactOptionalPropertyTypes`", "`verbatimModuleSyntax`", "`ignoreDeprecations`", "`types` default". Also query typescript-eslint for rules that enforce `no-explicit-any` and `no-floating-promises` at the installed version, and the schema library the project uses for its parse and infer functions.
- **gh_grep:** search literal strings: `"moduleResolution": "nodenext"`, `"noUncheckedIndexedAccess": true`, `// @ts-expect-error`, `satisfies Record<`, `const unreachable: never`, and `: unknown` in function signatures near `JSON.parse(`. Check recent repositories to see how current projects set `types` and `rootDir` after 6.0.

## Sources

- Announcing TypeScript 6.0 (defaults, deprecations, `ignoreDeprecations`, `types`, `rootDir`, `#/` subpath imports, `this`-less inference): https://devblogs.microsoft.com/typescript/announcing-typescript-6.0/
- Announcing TypeScript 7.0 (native port, no API in 7.0, `@typescript/typescript6` alias, hard errors for deprecated options, embedded-language caveats): https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
