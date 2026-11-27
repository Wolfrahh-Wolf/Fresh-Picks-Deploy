# React

Covers React 19 components, hooks, effects, the rendering model, forms with Actions, error boundaries and common mistakes; checked against React 19 (stable release) on 2026-11-26. The project's `package.json` and lockfile determine the installed version.

## Contents

- Rendering model
- Components and composition
- Hooks
- Effects
- Forms and Actions (React 19)
- Error boundaries
- Common mistakes

## Guidance

### Rendering model

React re-renders a component when its state or props change. During a render, React calls the component function and compares the returned element tree with the previous one (reconciliation). DOM updates are batched automatically in React 18+.

**Key invariants:**
- Render functions must be pure: no side effects, no mutation of external state.
- State updates are asynchronous; reading state immediately after `setState` returns the old value.
- React 18 Concurrent Mode may interrupt and restart renders; write components that tolerate this.

Memoisation is an optimisation, not a correctness requirement:

| Tool | When to use |
|---|---|
| `React.memo(Component)` | Expensive child that re-renders with the same props |
| `useMemo(fn, deps)` | Expensive inline computation; referential stability for deps |
| `useCallback(fn, deps)` | Stable function reference passed to a memoised child |

Profile first with React DevTools Profiler before adding any of these.

### Components and composition

Prefer function components. Keep components small and single-responsibility: a component that fetches data, transforms it and renders it is three responsibilities.

**Composition over configuration:** pass children and render-props rather than a growing list of boolean props.

```tsx
// Bad: boolean proliferation
<Card hasHeader hasBorder loading={false} />

// Good: composition
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Body>…</Card.Body>
</Card>
```

Co-locate state with the component that owns it. Lift state only when two siblings genuinely need it. If lifting reaches three or more levels, reconsider the component boundary or use a state manager.

### Hooks

The rules: call hooks only at the top level; call hooks only from React functions. Lint with `eslint-plugin-react-hooks` to enforce this automatically.

| Hook | Purpose |
|---|---|
| `useState` | Local, synchronous UI state |
| `useReducer` | Local state with complex transitions |
| `useEffect` | Synchronise with an external system (DOM, subscriptions, timers) |
| `useRef` | Mutable container that does not trigger re-render; stable DOM reference |
| `useContext` | Read a context value; use sparingly for high-frequency updates |
| `useMemo` / `useCallback` | Memoisation after profiling confirms the need |
| `useId` | Stable, unique IDs for accessibility attributes |
| `useTransition` | Mark a state update as non-urgent; keep the UI responsive |
| `useDeferredValue` | Defer re-rendering a part of the tree for a less-urgent update |

**React 19 additions:**

| Hook | Purpose |
|---|---|
| `useActionState` | Manage async action state (pending, result, error) for forms |
| `useOptimistic` | Optimistically update UI before a mutation settles |
| `use(promise)` | Read a promise or context in render (suspends until resolved) |

Import `useActionState` from `'react'`; import `useFormStatus` from `'react-dom'`.

### Effects

`useEffect` is for synchronising with external systems, not for reacting to state changes inside React.

```tsx
// Bad: effect used as a reaction to derived state
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// Good: derive inline; no effect needed
const fullName = `${firstName} ${lastName}`;
```

Always return a cleanup function when the effect sets up a subscription, timer or event listener:

```tsx
useEffect(() => {
  const sub = store.subscribe(handler);
  return () => sub.unsubscribe();
}, [store]);
```

Strict Mode in development mounts every effect twice to surface missing cleanups. If an effect breaks on remount, the cleanup is missing.

Avoid `useEffect` for: initial data fetching in Next.js (use Server Components); transforming data (compute inline or in `useMemo`); responding to events (use event handlers).

### Forms and Actions (React 19)

React 19 introduces **Actions**: async functions that handle data mutations. Pass an action to `<form action={fn}>`, `useActionState` or `startTransition`.

```tsx
import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';

async function updateProfile(prevState: State, formData: FormData): Promise<State> {
  const name = formData.get('name') as string;
  const result = await api.updateName(name);
  if (!result.ok) return { error: result.message };
  return { error: null };
}

function SubmitButton() {
  const { pending } = useFormStatus();  // must be a child of <form>
  return (
    <button type="submit" disabled={pending} aria-busy={pending}>
      {pending ? 'Saving…' : 'Save'}
    </button>
  );
}

export function ProfileForm() {
  const [state, formAction, isPending] = useActionState(updateProfile, { error: null });
  return (
    <form action={formAction}>
      <label htmlFor="name">Name</label>
      <input id="name" name="name" required />
      <SubmitButton />
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

Use uncontrolled inputs with `FormData` when you do not need real-time validation. Use controlled inputs (`value` + `onChange`) only when you need live feedback (e.g., password strength).

### Error boundaries

Error boundaries catch render errors in their child tree and display a fallback. They are class components or wrappers from the `react-error-boundary` library.

Place boundaries at meaningful component subtrees: wrapping the whole app masks errors; wrapping every leaf is noise. A product page, a sidebar and a widget panel are good granularities.

```tsx
import { ErrorBoundary } from 'react-error-boundary';

function FallbackComponent({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert">
      <p>Something went wrong: {error.message}</p>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

<ErrorBoundary FallbackComponent={FallbackComponent}>
  <ProductCard id={id} />
</ErrorBoundary>
```

Error boundaries do not catch errors in event handlers (use try/catch), async code (use `useActionState`) or server-side rendering.

## Examples

### Bad to good: unnecessary effect

```tsx
// Bad: synchronises derived state through an effect
const [items, setItems] = useState([]);
const [filtered, setFiltered] = useState([]);
useEffect(() => {
  setFiltered(items.filter(i => i.active));
}, [items]);

// Good: compute during render
const filtered = items.filter(i => i.active);
```

### Optimistic UI with useOptimistic

```tsx
import { startTransition, useOptimistic, useState } from 'react';

function LikeButton({ postId, initialLiked }: { postId: string; initialLiked: boolean }) {
  const [liked, setLiked] = useState(initialLiked);
  const [optimisticLiked, setOptimisticLiked] = useOptimistic(liked);

  function handleLike() {
    startTransition(async () => {
      const next = !optimisticLiked;
      setOptimisticLiked(next);          // must run inside a Transition or Form Action
      const saved = await api.toggleLike(postId);
      setLiked(saved);                   // commit source of truth; on throw React reverts
    });
  }

  return <button type="button" onClick={handleLike}>{optimisticLiked ? '♥' : '♡'}</button>;
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using `useEffect` to sync derived state | Creates an extra render cycle; produces stale state | Compute derived values inline during render |
| Adding `useCallback`/`useMemo` everywhere | Adds memory and diff cost with no benefit unless profiling shows a problem | Profile first; add memoisation only where needed |
| Calling hooks inside conditions or loops | Breaks the hook call order between renders | Move the condition inside the hook body |
| Missing cleanup in `useEffect` | Memory leaks and stale callbacks on unmount or re-mount | Always return a cleanup function |
| `useFormState` from `react-dom` in React 19 | Deprecated in favour of `useActionState` from `'react'` and lacks `isPending` | Import `useActionState` from `'react'` |
| `role="alert"` on every error message | Screen readers announce every update; noisy | Use `role="alert"` for critical, immediate feedback; use `aria-live="polite"` for less urgent updates |

## Checklist

- [ ] Component renders pure (no side effects in the function body).
- [ ] `useEffect` has a cleanup function wherever it sets up an observable.
- [ ] `useActionState` used for async form submission (React 19); `useFormStatus` called only from a child of the form.
- [ ] `useMemo`/`useCallback` added only after profiling confirms the need.
- [ ] Error boundaries placed at meaningful subtree granularities with an accessible fallback.
- [ ] No hook called conditionally or inside a loop.
- [ ] `useId()` used for accessibility ID attributes that must be unique.

## Verify with context7 and gh_grep

- **context7:** Resolve `react` and `react-dom` at the version in `package.json`. Check: `useActionState` signature and import path (React 19); `useFormStatus` availability in `react-dom`; `useOptimistic` behaviour on mutation error; `useDeferredValue` and `useTransition` semantics for the installed version.
- **gh_grep:** Search `useActionState(` for form action patterns; `useOptimistic(` for optimistic update usage; `ErrorBoundary` with `FallbackComponent` for error boundary implementations; `useEffect(() => {` with `return () =>` for cleanup patterns.

## Sources

- React 19 release blog: https://react.dev/blog/2024/12/05/react-19
- React documentation, useActionState: https://react.dev/reference/react/useActionState
- React documentation, useOptimistic: https://react.dev/reference/react/useOptimistic
- React documentation, useFormStatus: https://react.dev/reference/react-dom/hooks/useFormStatus
- React documentation, Error boundaries: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
