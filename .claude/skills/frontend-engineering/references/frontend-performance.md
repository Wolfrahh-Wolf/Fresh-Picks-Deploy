# Frontend Performance

Covers Core Web Vitals, bundle size optimisation, loading strategy, rendering cost and measurement; thresholds from Google Web Vitals documentation, checked 2026-11-26.

## Contents

- Measure first
- Core Web Vitals thresholds
- LCP: largest contentful paint
- INP: interaction to next paint
- CLS: cumulative layout shift
- Bundle size
- Loading strategy
- Rendering cost

## Guidance

### Measure first

Never optimise without data. Run measurements in this order:

1. **Field data:** Google Search Console → Core Web Vitals report shows real-user 75th percentile over 28 days. This is the authoritative source that affects search ranking.
2. **PageSpeed Insights:** combines field data (CrUX) and lab data (Lighthouse) for a specific URL.
3. **Chrome DevTools:** Performance panel records a trace with flame charts for diagnosing the specific bottleneck.
4. **Lighthouse CI:** integrates into CI to prevent regressions; use it to gate pull requests when field data is not yet available.

Do not optimise a metric that is already in the "Good" range at the 75th percentile. Fix the worst metric first.

### Core Web Vitals thresholds

Google evaluates at the **75th percentile** of field data:

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5 s | 2.5–4.0 s | > 4.0 s |
| INP (Interaction to Next Paint) | ≤ 200 ms | 200–500 ms | > 500 ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | 0.1–0.25 | > 0.25 |

INP replaced First Input Delay (FID) in March 2024. FID is no longer a Core Web Vital.

### LCP: largest contentful paint

LCP measures when the largest visible element (image, video poster, or text block) is painted. The goal is ≤ 2.5 s.

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Slow server response (TTFB > 600 ms) | CDN, server-side caching, reduce server work |
| Render-blocking CSS | Inline critical CSS; defer non-critical |
| Render-blocking JavaScript | `defer` or `async` on non-critical scripts; remove unused scripts |
| Unoptimised hero image | Use `next/image` with `priority`; serve WebP/AVIF; use a CDN |
| Late-discovered LCP resource | `<link rel="preload">` for the LCP image if not in initial HTML |

**In Next.js:** add `priority` to the `<Image>` component for the LCP element. This adds `fetchpriority="high"` and disables lazy loading.

```tsx
// Good: LCP image has priority
<Image src="/hero.webp" alt="Hero" width={1200} height={600} priority />
```

**Preload when the LCP is a background image (CSS) or dynamically chosen:**

```html
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high" />
```

### INP: interaction to next paint

INP measures the total latency of a user interaction (click, tap, keyboard) until the browser paints the next frame. The goal is ≤ 200 ms.

INP = input delay + processing time + presentation delay.

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Long task on the main thread (> 50 ms) | Break into smaller tasks with `scheduler.yield()` or `setTimeout(0, fn)` |
| Heavy event handler | Move synchronous computation out of the handler; defer with `startTransition` |
| Large DOM (> 1 500 nodes typical) | Virtualise long lists (`@tanstack/react-virtual`) |
| Third-party scripts | Load with `strategy="lazyOnload"` in Next.js `<Script>`; use a facade for embeds |
| Expensive state update triggering full re-render | Use `useTransition` to mark the update as non-urgent |

```tsx
import { useTransition, useState } from 'react';

function SearchResults({ query }: { query: string }) {
  const [isPending, startTransition] = useTransition();
  const [deferredQuery, setDeferredQuery] = useState(query);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    // Input update is urgent; results update is non-urgent
    startTransition(() => setDeferredQuery(e.target.value));
  }
  return (
    <>
      <input onChange={handleChange} />
      {isPending && <Spinner />}
      <ResultList query={deferredQuery} />
    </>
  );
}
```

Measure interaction latency in DevTools: Performance panel → Interactions track shows each interaction and its phases.

### CLS: cumulative layout shift

CLS measures unexpected visual movement. Each shift is scored as `impact fraction × distance fraction`. Goal: ≤ 0.1.

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Images without dimensions | Always set `width` and `height` on `<img>` or `next/image` |
| Ads and embeds without reserved space | Wrap in a container with explicit height |
| Late-loading web fonts | Use `next/font` to eliminate FOUT/FOIT; set `font-display: optional` |
| Dynamic content injected above existing content | Insert new content below the fold or use CSS `min-height` to reserve space |
| Animations that move elements | Animate only `transform` and `opacity`; never `top`, `left`, `width`, `height` |

```tsx
{/* Good: dimensions reserved; no shift */}
<Image src="/product.webp" alt="…" width={400} height={300} />

{/* Bad: no dimensions; causes shift when image loads */}
<img src="/product.webp" alt="…" />
```

### Bundle size

Smaller JavaScript means faster parse, compile and execution.

**Analyse the bundle** before and after every significant dependency addition:
- Next.js: `ANALYZE=true next build` with `@next/bundle-analyzer`
- Generic: `source-map-explorer` or `webpack-bundle-analyzer`

**Techniques:**

| Technique | How |
|---|---|
| Dynamic import | `const Chart = dynamic(() => import('./Chart'), { ssr: false })` |
| Tree shaking | Named imports from ES modules; check the library ships ESM |
| Remove unused dependencies | `depcheck` or `knip` to find unused packages |
| Replace heavy libraries | `date-fns` instead of `moment`; `zod` instead of `joi` |
| Code split at the route | Next.js does this automatically per page |

Track bundle size with `bundlesize` or `size-limit` in CI. Set a budget and fail the build when it is exceeded.

### Loading strategy

Prioritise the critical path: load only what is needed for the first meaningful paint.

| Resource | Strategy |
|---|---|
| LCP image | `fetchpriority="high"` / `priority` on `next/image` |
| Below-fold images | Lazy load (`loading="lazy"` or `next/image` default) |
| Non-critical CSS | Load asynchronously or inline critical styles |
| Non-critical JavaScript | `<Script strategy="lazyOnload">` in Next.js |
| Fonts | `next/font` (zero layout shift; self-hosted) |
| Third-party embeds | Facade pattern: load a placeholder image; load the real embed on click |

**Streaming in Next.js:** wrap slow Server Components in `<Suspense>` to stream the shell and stream in the slow parts asynchronously:

```tsx
import { Suspense } from 'react';

export default function Page() {
  return (
    <>
      <StaticHeader />
      <Suspense fallback={<Spinner />}>
        <SlowDataComponent />
      </Suspense>
    </>
  );
}
```

### Rendering cost

Expensive renders degrade both LCP and INP.

**Identify expensive renders with React DevTools Profiler:** record a session, sort by "Render duration", find the slowest components.

| Problem | Fix |
|---|---|
| Component re-renders when props have not changed | `React.memo(Component)` after profiling confirms the need |
| Expensive calculation in render | `useMemo(fn, deps)` |
| Long list (> 100 items) | Virtualise with `@tanstack/react-virtual` |
| Heavy computation blocking the main thread | Web Worker via `comlink` or `workerize-loader` |

Avoid premature memoisation. `React.memo` has a comparison cost that exceeds the render cost for simple components.

## Examples

### Next.js dynamic import for a heavy chart

```tsx
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

const RevenueChart = dynamic(() => import('./RevenueChart'), {
  ssr: false,
  loading: () => <div style={{ height: 300 }}>Loading chart…</div>,
});

export function Dashboard() {
  return (
    <Suspense>
      <RevenueChart />
    </Suspense>
  );
}
```

### Virtual list for performance

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function ProductList({ items }: { items: Product[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualiser = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,
  });
  return (
    <div ref={parentRef} style={{ height: 600, overflow: 'auto' }}>
      <div style={{ height: virtualiser.getTotalSize() }}>
        {virtualiser.getVirtualItems().map(row => (
          <div key={row.index} style={{ position: 'absolute', top: row.start }}>
            <ProductRow item={items[row.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Optimising before measuring | Effort spent on fast things; slow things remain slow | Check field data in Search Console first |
| `<img>` with no width/height | CLS on image load | Always provide dimensions or use `next/image` |
| Heavy library in the main bundle | Slow parse + execute on mobile | Dynamic import + code split |
| `React.memo` on every component | Comparison overhead on cheap renders | Profile first; apply selectively |
| `useTransition` or `useDeferredValue` without measuring INP | May add complexity with no measurable gain | Confirm the interaction is slow first |
| No `priority` on the LCP image | LCP image deprioritised behind other resources | Add `priority` to the above-the-fold hero image |

## Checklist

- [ ] Field data checked in Search Console before any optimisation.
- [ ] LCP ≤ 2.5 s at 75th percentile; LCP image has `priority` or `fetchpriority="high"`.
- [ ] INP ≤ 200 ms; no interaction takes > 50 ms on the main thread.
- [ ] CLS ≤ 0.1; all images have explicit dimensions; no content injected above the fold.
- [ ] Bundle size analysed; dynamic import applied to routes and heavy third-party components.
- [ ] Long lists (> 100 items) virtualised.
- [ ] `React.memo`/`useMemo` applied only after profiling confirms a render bottleneck.
- [ ] Third-party scripts loaded with `lazyOnload` strategy; facades used for heavy embeds.

## Verify with context7 and gh_grep

- **context7:** Resolve `next` for `next/image` `priority` prop and `dynamic` import options; `@tanstack/react-virtual` for `useVirtualizer` API; `scheduler` for `scheduler.yield()` availability; `@next/bundle-analyzer` configuration.
- **gh_grep:** Search `priority` on `next/image` for LCP optimisation patterns; `useVirtualizer(` for virtual list implementations; `strategy="lazyOnload"` for third-party script loading; `startTransition(` with result-list updates for INP reduction.

## Sources

- Google Web Vitals, Core Web Vitals thresholds: https://web.dev/articles/vitals
- Google Web Vitals, LCP: https://web.dev/articles/lcp
- Google Web Vitals, INP: https://web.dev/articles/inp
- Google Web Vitals, CLS: https://web.dev/articles/cls
- Next.js, Image optimisation: https://nextjs.org/docs/app/building-your-application/optimizing/images
- TanStack Virtual: https://tanstack.com/virtual/latest/docs/introduction
