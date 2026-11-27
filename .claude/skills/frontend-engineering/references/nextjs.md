# Next.js App Router

Covers Next.js 15 App Router: server and client components, data fetching, caching, Server Actions, routing, layouts and deployment concerns; checked 2026-11-26. The project's `package.json` determines the installed version; this file assumes Next.js 15.

## Contents

- Server vs. client components
- Data fetching
- Caching strategy (Next.js 15)
- Server Actions and mutations
- Routing and layouts
- Deployment concerns

## Guidance

### Server vs. client components

All components in the App Router are **Server Components** by default. Add `'use client'` only when the component requires:

- React hooks (`useState`, `useEffect`, `useRef`, `useActionState`, etc.)
- Browser-only APIs (`window`, `localStorage`, `navigator`)
- Event listeners (`onClick`, `onChange`)

Do not add `'use client'` to a component just because it sits below a client component in the tree. The boundary propagates downward: every import of a client component and its imports also become client code.

**Decision table:**

| Need | Server Component | Client Component |
|---|---|---|
| Fetch from DB or API on the server | ✓ |  |
| Use `useState` or `useEffect` |  | ✓ |
| Access `window` or `localStorage` |  | ✓ |
| Render sensitive env vars securely | ✓ |  |
| Handle form submission | Either (Server Action or client handler) | |
| Read `cookies()` or `headers()` | ✓ (async in Next.js 15) | |

Pass server-fetched data to client components as props. Do not re-fetch in a client component what a parent server component already has.

### Data fetching

Fetch data directly in async Server Components using `async/await`. There is no need for `useEffect` or a data-fetching library on the server:

```tsx
// app/products/page.tsx  — Server Component
export default async function ProductsPage() {
  const products = await db.product.findMany();  // or fetch()
  return <ProductList products={products} />;
}
```

For external APIs, use `fetch()`. In Next.js 15, **`fetch` requests are not cached by default**; they behave like `{ cache: 'no-store' }` unless you opt in:

```ts
// No cache (default in Next.js 15)
const data = await fetch('https://api.example.com/data');

// Time-based revalidation (ISR)
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600 },   // seconds
});

// Tag-based invalidation
const data = await fetch('https://api.example.com/data', {
  next: { tags: ['products'] },
});

// Always cache
const data = await fetch('https://api.example.com/data', {
  cache: 'force-cache',
});
```

Do not use `getServerSideProps` or `getStaticProps`; those are Pages Router patterns.

### Caching strategy (Next.js 15)

Next.js 15 changed all caching defaults to **opt-in**:

| Behaviour | Next.js 14 default | Next.js 15 default |
|---|---|---|
| `fetch` with no option | `force-cache` | `no-store` |
| `GET` Route Handlers | Cached | Not cached |
| Client router cache staleTime | Longer (varies) | 0 seconds for dynamic pages |

Choose the right caching tier:

| Requirement | Approach |
|---|---|
| Always fresh (live data) | Omit cache option (defaults to `no-store`) |
| Revalidate on a schedule | `next: { revalidate: N }` |
| Revalidate after a mutation | `next: { tags: ['tag'] }` + `revalidateTag('tag')` in action |
| Static at build time | `cache: 'force-cache'` or `generateStaticParams` |

Avoid mixing ISR and on-demand revalidation on the same page without understanding which wins.

### Server Actions and mutations

Server Actions are async functions marked `'use server'`. They run on the server when invoked from a form action or event handler.

```tsx
// app/actions.ts
'use server';
import { revalidateTag } from 'next/cache';

export async function createProduct(formData: FormData) {
  const name = formData.get('name') as string;
  await db.product.create({ data: { name } });
  revalidateTag('products');   // purge the cached product list
}

// app/products/new/page.tsx  — Server Component using the action
import { createProduct } from '../actions';

export default function NewProductPage() {
  return (
    <form action={createProduct}>
      <input name="name" required />
      <button type="submit">Create</button>
    </form>
  );
}
```

For loading and error states in the client, pair the server action with `useActionState` in a Client Component:

```tsx
'use client';
import { useActionState } from 'react';
import { createProduct } from '../actions';

export function CreateProductForm() {
  const [state, action, isPending] = useActionState(createProduct, null);
  return (
    <form action={action}>
      <input name="name" required />
      <button disabled={isPending}>{isPending ? 'Creating…' : 'Create'}</button>
      {state?.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

Call `revalidatePath` when you need to refresh a specific route segment after a mutation. Prefer `revalidateTag` for data-centric invalidation; prefer `revalidatePath` for page-level invalidation.

### Routing and layouts

The App Router uses the file system:

```
app/
  layout.tsx          # root layout (wraps all pages; includes <html> and <body>)
  page.tsx            # /
  products/
    layout.tsx        # nested layout for /products/*
    page.tsx          # /products
    [id]/
      page.tsx        # /products/:id
      loading.tsx     # streaming loading UI for this segment
      error.tsx       # error boundary for this segment (must be 'use client')
      not-found.tsx   # 404 for this segment
```

`loading.tsx` exports a React component used as a Suspense fallback while the page streams. `error.tsx` must be a Client Component (it uses React error boundary behaviour).

In Next.js 15, `params` and `searchParams` in page components are **Promises**; await them:

```tsx
// app/products/[id]/page.tsx
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await db.product.findUnique({ where: { id } });
  if (!product) notFound();
  return <ProductDetail product={product} />;
}
```

Parallel routes (`@slot`) and intercepting routes (`(.)folder`) are advanced patterns; use them only when the routing requirement clearly maps to them.

### Deployment concerns

- **Environment variables:** Prefix with `NEXT_PUBLIC_` to expose to the browser; never expose secrets to the client.
- **Static vs. dynamic rendering:** A page becomes dynamic if it calls `cookies()`, `headers()`, accesses `searchParams` or uses `cache: 'no-store'`. Check the Next.js build output for `○` (static) vs. `ƒ` (dynamic) indicators.
- **Image optimisation:** Use `next/image` for all images. Provide `width`, `height` and meaningful `alt`. Set `priority` on the LCP image.
- **Font optimisation:** Use `next/font` to load fonts; it eliminates layout shift from web fonts.
- **Middleware:** Keep it fast (< 5 ms). It runs on every request including static assets unless constrained with `matcher`.

## Examples

### Parallel data fetching in a server component

```tsx
// Fetch both in parallel; do not await sequentially
export default async function DashboardPage() {
  const [user, stats] = await Promise.all([
    fetchUser(),
    fetchStats(),
  ]);
  return <Dashboard user={user} stats={stats} />;
}
```

### Tag-based cache invalidation after a mutation

```ts
// action
'use server';
import { revalidateTag } from 'next/cache';
import { redirect } from 'next/navigation';

export async function deletePost(id: string) {
  await db.post.delete({ where: { id } });
  revalidateTag('posts');
  redirect('/posts');
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Adding `'use client'` to every component | Sends all logic to the browser; loses server rendering | Server Component is the default; add `'use client'` only when needed |
| Assuming `fetch` is cached (pre-v15 mental model) | Stale data surprises after migrating to Next.js 15 | Explicitly add `cache` or `next.revalidate` options when you need caching |
| Awaiting `params` synchronously in Next.js 15 | `params` is a Promise in v15; synchronous access returns undefined | `const { id } = await params;` |
| Using `useEffect` to fetch in a Client Component | Extra round-trip; no server rendering; loading jank | Fetch in a Server Component and pass data as props |
| `revalidatePath` with the wrong path string | Does not invalidate the intended route | Use exact route path; use `revalidateTag` for data-scoped invalidation |
| Putting secrets in `NEXT_PUBLIC_` vars | Exposed to the browser bundle | Use non-prefixed env vars for secrets; access only in Server Components |

## Checklist

- [ ] Next.js version confirmed from `package.json`.
- [ ] `'use client'` added only where interactivity or browser APIs are required.
- [ ] Data fetched in Server Components, not in `useEffect` in Client Components.
- [ ] Caching intent is explicit: no-store, ISR, tag or force-cache—not relying on a default.
- [ ] `params` and `searchParams` awaited (Next.js 15).
- [ ] `revalidateTag` or `revalidatePath` called after every mutation.
- [ ] LCP image has `priority` on `next/image`.
- [ ] No secrets in `NEXT_PUBLIC_` environment variables.
- [ ] `loading.tsx` and `error.tsx` added for data-dependent routes.

## Verify with context7 and gh_grep

- **context7:** Resolve `next` at the locked version. Check: `fetch` caching defaults in v15 (no-store); `params` as a Promise (v15 breaking change); `revalidateTag` and `revalidatePath` signatures; `next/image` `priority` prop; `next/font` configuration.
- **gh_grep:** Search `revalidateTag(` for tag invalidation patterns; `'use server'` with `revalidatePath` for mutation flows; `const { id } = await params` for the Next.js 15 async params pattern; `next: { tags:` in `fetch()` options.

## Sources

- Next.js 15 upgrade guide: https://nextjs.org/docs/app/building-your-application/upgrading/version-15
- Next.js App Router: data fetching: https://nextjs.org/docs/app/building-your-application/data-fetching/fetching
- Next.js App Router: caching: https://nextjs.org/docs/app/building-your-application/caching
- Next.js App Router: server actions: https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations
- Next.js Image component: https://nextjs.org/docs/app/api-reference/components/image
