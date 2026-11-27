---
name: frontend-engineering
description: "Use when building, reviewing or debugging web UI: React, Next.js, state management, accessibility, frontend performance and UI/UX behaviour."
---

# Frontend Engineering

Covers the full lifecycle of web UI work: React component design, Next.js App Router patterns, state management, accessibility compliance, performance measurement and UI/UX behaviour. The output is accessible, fast, maintainable UI that matches `docs/DESIGN.md`.

## When to use

- Building or modifying a React component, hook, form or error boundary.
- Working on a Next.js route, layout, server component, server action or data fetch.
- Choosing or refactoring a state management approach (local, shared, server or URL state).
- Reviewing frontend code for correctness, accessibility or performance.
- Debugging a render issue, interaction failure or Core Web Vitals regression.
- Implementing an interaction pattern, focus management, or responsive layout.

## Do not use for

- JavaScript and TypeScript language rules (typing, naming, linting, clean code): load `languages-clean-code`.
- UI tests and Playwright end-to-end testing: load `testing-strategy`.

## Research: context7 and gh_grep

- You MUST consult **context7** before writing, changing or reviewing any code that relies on React, Next.js, Zustand, Jotai, TanStack Query or any third-party UI library. Read the version from `package.json` or the lockfile first and query that exact version. Useful queries: `"react" "19" useActionState forms`, `"next.js" "15" server components data fetching`, `"next.js" "15" revalidatePath revalidateTag`, `"zustand" selector subscriptions`, `"@tanstack/react-query" useQuery staleTime`.
- You MUST search **gh_grep** when a hook or component pattern is unfamiliar, an error is not explained by the docs, or you are deciding between rendering strategies. Useful searches: `'use client'` with `useState`, `useActionState(`, `revalidateTag(`, `aria-live="polite"`, `role="dialog"` with `aria-modal`.
- Project-internal logic (a wrong condition in a component's own state or business rule) needs neither. State that in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/react.md](references/react.md) | Writing or reviewing React components, hooks, effects, forms or error boundaries. |
| [references/nextjs.md](references/nextjs.md) | Working with Next.js routing, server/client components, data fetching, mutations or caching. |
| [references/state-management.md](references/state-management.md) | Choosing or refactoring state: local, shared client, server cache or URL. |
| [references/accessibility.md](references/accessibility.md) | Keyboard navigation, focus management, ARIA, contrast, form labelling or WCAG compliance. |
| [references/frontend-performance.md](references/frontend-performance.md) | Core Web Vitals, bundle size, loading strategy, rendering cost or profiling. |
| [references/ui-ux.md](references/ui-ux.md) | Interaction states, responsive layout, design tokens or matching `docs/DESIGN.md`. |

## Workflow

1. **Read the design spec.** Check `docs/DESIGN.md` for interaction states, tokens and responsive breakpoints. If the file is missing or incomplete, raise it as a follow-up; do not invent design decisions.
2. **Consult context7 and check the manifest.** Read the locked version of every library you will touch. Query the reference files only as the task demands.
3. **Open the matching references.** Route by signal using the table above. Load at most two reference files in addition to this skill.
4. **Implement.** Follow the Standards below. Implementer writes source and tests; reviewer reads only.
5. **Reviewer steps.** Check each Standard item. For accessibility changes also confirm: every interactive element is keyboard-reachable, focus is managed, ARIA is used only where native semantics cannot serve, contrast passes. File findings at the correct severity per `AGENTS.md`.
6. **Debugger steps.** State the failure (render output, console error, visual regression, interaction failure), collect evidence from the browser console and React DevTools, then search `gh_grep` with the verbatim error and check library versions with context7. Propose the minimal fix without editing source.
7. **Verify.** Run every check in the Verification section below.
8. **Sync docs.** Update `docs/DESIGN.md` (architect) if a new interaction pattern or token was added; `README.md` if a new dev command was introduced.

## Standards

- Read the locked dependency version from `package.json` before every context7 query. The project's versions win over any default stated here.
- Never remove `outline: none` or `outline: 0` from focusable elements without providing a custom focus indicator that meets WCAG 2.2 SC 2.4.11 (not entirely obscured).
- Every `<img>` must have an `alt` attribute; decorative images use `alt=""`.
- Every form control must have a programmatically associated label (`<label for>` or `aria-label`).
- Use semantic HTML first; reach for `role` and `aria-*` only when native elements cannot serve.
- In Next.js App Router, components are Server Components by default; add `'use client'` only when the component requires interactivity, browser APIs or React hooks.
- Never fetch data in a Client Component when the same data can be fetched in a parent Server Component and passed as props.
- Match state to its category: local UI → `useState`/`useReducer`; server cache → TanStack Query or Next.js caching; shared client → Zustand/Jotai; URL → query parameters.
- Measure before optimising: run Lighthouse or PageSpeed Insights and check field data in Search Console before changing loading strategy.
- Never block the main thread for more than 50 ms; move heavy computation to a Web Worker.
- Set explicit `width` and `height` on images and reserve space for ads and embeds to prevent CLS.
- Implement all interaction states: default, hover, focus, active, disabled, loading, error, empty. Never leave a state unstyled.
- Use design tokens from `docs/DESIGN.md` or the project's token file; do not hard-code colour values or spacing.
- Every new interactive pattern must be keyboard-navigable and tested without a mouse.

## Verification

- [ ] `context7` queried for every library used, at the locked version; unverified claims are labelled.
- [ ] `gh_grep` searched for any unfamiliar hook or component pattern.
- [ ] No `outline: none` without a visible custom focus indicator.
- [ ] All images have `alt`; all form controls have associated labels.
- [ ] Keyboard navigation tested: Tab, Shift-Tab, Enter, Space, Escape reach and activate all interactive elements.
- [ ] No `'use client'` added where a Server Component would suffice.
- [ ] State is in the correct layer (local/shared/server/URL); no duplicate state.
- [ ] All interaction states (hover, focus, disabled, loading, error, empty) are implemented.
- [ ] Lighthouse score checked; LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile.
- [ ] Design tokens used; no hard-coded colour or spacing values.
- [ ] Linter, type checker and test suite pass with no new failures.
- [ ] `docs/DESIGN.md` updated or the architect has a follow-up.

## Output

Return the standard report from `AGENTS.md`. Key additions for this skill:

- **Evidence:** linter command and exit code, test command and pass/fail count, Lighthouse scores (LCP, INP, CLS) or the tool used to get them, keyboard navigation test result (which elements tested, any failures).
- **Research:** every context7 library and version queried; every gh_grep pattern searched and what it returned or confirmed.
- **Docs impact:** `docs/DESIGN.md` (architect) on new interaction patterns or tokens; `README.md` and `CHANGELOG.md` (implementer) on new setup commands or behaviour changes; `docs/MEMORY.md` (coordinator) on durable decisions or pitfalls.
