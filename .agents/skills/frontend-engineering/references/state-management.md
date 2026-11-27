# State Management

Covers choosing and implementing local, shared client, server cache and URL state in React applications; patterns current as of 2026-11-26. The project's `package.json` determines which libraries are installed.

## Contents

- State categories
- Local UI state
- Shared client state
- Server cache state
- URL state
- Avoiding duplicated state
- Context API limits

## Guidance

### State categories

Identify the category of state before choosing a tool. The wrong category leads to either over-engineering or stale data.

| Category | Definition | Correct tool |
|---|---|---|
| Local UI | Owned by one component; not needed elsewhere (open/closed, hover, input focus) | `useState`, `useReducer` |
| Shared client | UI state that multiple loosely-related components read and write (sidebar open, active theme, multi-step draft) | Zustand, Jotai |
| Server cache | Data that originates from an API or database; needs background refresh, caching and synchronisation | TanStack Query, Next.js server caching |
| URL | Filters, pagination, active tab, search query — anything that must survive a page refresh or be shareable | Query parameters via the router or `nuqs` |

**The golden rule:** identify the category first; do not store server data in Zustand, do not use React Context for high-frequency updates, do not duplicate URL state in `useState`.

### Local UI state

`useState` is correct for the vast majority of component-level state.

```tsx
const [isOpen, setIsOpen] = useState(false);
```

Reach for `useReducer` when state has multiple sub-values that transition together, or when the next state depends on the previous state in non-trivial ways:

```tsx
type Action = { type: 'submit' } | { type: 'error'; message: string } | { type: 'reset' };
function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'submit': return { ...state, submitting: true, error: null };
    case 'error':  return { ...state, submitting: false, error: action.message };
    case 'reset':  return initialState;
  }
}
const [state, dispatch] = useReducer(reducer, initialState);
```

Do not lift state higher than necessary. If only one component needs it, keep it local.

### Shared client state

Use **Zustand** for most shared client state. It requires no provider, works with Server Components (the store is created client-side only), and uses selectors to prevent unnecessary re-renders.

```tsx
// store/ui.ts
import { create } from 'zustand';

interface UIStore {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));

// Component: subscribe to only the slice you need
const sidebarOpen = useUIStore((s) => s.sidebarOpen);
const toggleSidebar = useUIStore((s) => s.toggleSidebar);
```

Use **Jotai** when state is highly granular and components need to subscribe to individual atoms independently. Jotai is well-suited for fine-grained reactive state trees.

**When to prefer Zustand over Jotai:**
- Global state with actions (a "store" mental model)
- When you want one place to read all state for debugging

**When to prefer Jotai:**
- Many small, independent pieces of state; each component subscribes to exactly one atom
- Derived state that depends on other atoms

### Server cache state

Use **TanStack Query** (React Query) for any data that comes from an API or database when you are on the client side. It handles loading/error states, background refetching, deduplication, pagination and optimistic updates.

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function ProductList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetch('/api/products').then(r => r.json()),
    staleTime: 60_000,  // consider fresh for 60 s
  });
  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <ul>{data.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}

function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fetch(`/api/products/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['products'] }),
  });
}
```

In **Next.js App Router**, prefer fetching data in Server Components using `async/await` and Next.js caching. Use TanStack Query only for client-side data that must be fetched after page load (infinite scroll, real-time feeds, user-specific data not known at render time).

Do not store server data in Zustand or Jotai. If you find yourself manually syncing API responses into a global store, switch to TanStack Query.

### URL state

Filters, sort order, pagination, search query and active tab belong in the URL so they:
- Survive a page refresh
- Are shareable as a link
- Work with the browser back/forward buttons

In Next.js App Router, read URL state from `searchParams` in Server Components:

```tsx
// app/products/page.tsx
export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  const { q = '', page = '1' } = await searchParams;
  const products = await fetchProducts({ query: q, page: Number(page) });
  return <ProductList products={products} query={q} page={Number(page)} />;
}
```

For client-driven URL updates, use **nuqs** for type-safe, hydration-safe query parameter management:

```tsx
'use client';
import { useQueryState, parseAsString } from 'nuqs';

function SearchBar() {
  const [query, setQuery] = useQueryState('q', parseAsString.withDefault(''));
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

Do not mirror URL state in `useState`. Reading from the URL and keeping a parallel `useState` creates a source-of-truth conflict.

### Avoiding duplicated state

Duplicated state is state derived from other state stored separately. It goes stale.

| Pattern | Problem | Fix |
|---|---|---|
| `const [fullName, setFullName] = useState(…)` updated in an effect from `firstName` + `lastName` | Two renders per change; can go out of sync | Compute: `const fullName = \`${firstName} ${lastName}\`` |
| Product list in Zustand + filtered list in another store slice | Filter must be re-applied on every change | Store the raw list; derive filtered in a selector |
| `searchParams` read from the URL and also mirrored in `useState` | Two sources of truth; they diverge on navigation | Read from the URL only; derive display state from that |
| `isLoading`, `error`, `data` as separate `useState` values for a fetch | Three states to keep consistent | Use TanStack Query or `useActionState` |

### Context API limits

React Context is appropriate for:
- Stable, infrequently-changing values: current user identity, theme name, locale
- Dependency injection for testability (swapping implementations)

React Context is not appropriate for:
- High-frequency state updates (every keystroke, scroll position) — every consumer re-renders on every change
- Large, structured state with many fields — use Zustand or Jotai instead

```tsx
// Good use of Context: stable user identity
const UserContext = createContext<User | null>(null);
export const useUser = () => useContext(UserContext);
```

## Examples

### Complete state decision for a products filter page

```
State: search query    → URL (?q=shoes)        via nuqs
State: products list   → Server Component fetch → TanStack Query if client-driven
State: loading/error   → TanStack Query
State: selected items  → Local useState (not shared, not URL)
State: modal open      → Zustand (accessible from toolbar + content area)
```

### Zustand selector to prevent over-rendering

```tsx
// Bad: subscribes to the whole store; re-renders on any change
const store = useUIStore();
const { sidebarOpen } = store;

// Good: subscribes only to the slice it needs
const sidebarOpen = useUIStore((s) => s.sidebarOpen);
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Storing API responses in Zustand | Manual cache invalidation; stale data after mutations | Use TanStack Query or Next.js server caching |
| `useState` for a filter that must be shareable | Filter lost on refresh; not linkable | Put it in the URL as a query parameter |
| Syncing URL state to `useState` in an effect | Two sources of truth; diverge on navigation | Read from the URL directly; derive display state from that |
| Using React Context for every piece of shared state | Every consumer re-renders on every context value change | Use Zustand/Jotai for high-frequency or large state |
| Computing derived state in a `useEffect` | Extra render; can go out of sync | Derive inline or in a Zustand selector |

## Checklist

- [ ] State category identified (local/shared/server/URL) before choosing a tool.
- [ ] No server-fetched data stored manually in Zustand or Jotai.
- [ ] Filters, pagination and search terms live in the URL.
- [ ] Zustand selectors subscribe to the minimum slice of state.
- [ ] No state derived via `useEffect`; derived state computed inline or in a selector.
- [ ] React Context used only for stable, infrequent values.
- [ ] No `useState` that mirrors URL query parameters.

## Verify with context7 and gh_grep

- **context7:** Resolve `zustand`, `jotai`, `@tanstack/react-query`, `nuqs` at their locked versions. Check: Zustand `create` API and selector pattern; Jotai `atom` and `useAtom`; TanStack Query `useQuery` `staleTime` and `useQueryClient().invalidateQueries`; nuqs `useQueryState` with `parseAsString`.
- **gh_grep:** Search `useUIStore((s) =>` for Zustand selector patterns; `invalidateQueries({` for TanStack Query cache invalidation; `useQueryState(` for nuqs URL state; `parseAsString.withDefault(` for type-safe query params.

## Sources

- Zustand documentation: https://zustand.docs.pmnd.rs/getting-started/introduction
- Jotai documentation: https://jotai.org/docs/introduction
- TanStack Query documentation: https://tanstack.com/query/latest/docs/framework/react/overview
- nuqs documentation: https://nuqs.dev
- React documentation, useState vs. useReducer: https://react.dev/learn/extracting-state-logic-into-a-reducer
