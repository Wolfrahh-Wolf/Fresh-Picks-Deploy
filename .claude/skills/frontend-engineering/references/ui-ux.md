# UI/UX Behaviour

Covers interaction states, responsive layout, user feedback, design tokens and consistency with `docs/DESIGN.md`; checked against WCAG 2.2 (October 2023), W3C Design Tokens Format Module 2025.10 and MDN CSS specifications on 2026-11-26.

## Contents

- Consistency with docs/DESIGN.md
- Interaction and screen states
- User feedback and motion
- Responsive layout
- Design tokens

## Guidance

### Consistency with docs/DESIGN.md

`docs/DESIGN.md` (owned by the architect per `AGENTS.md`) defines design principles, information architecture, user flows, screens and states, design tokens and components, responsive behaviour and accessibility requirements.

- Read `docs/DESIGN.md` before building or modifying any screen or shared component.
- Reuse existing components and tokens defined there rather than adding one-off styles.
- If a screen state, breakpoint or token is missing from `docs/DESIGN.md`, ask or file a follow-up for the architect rather than inventing design rules silently.
- If existing code disagrees with `docs/DESIGN.md`, report the mismatch per `AGENTS.md` Source of truth instead of altering either silently.

### Interaction and screen states

Every interactive control and every view must account for all relevant states, not only the happy path.

**Control states:**

| State | Requirement | Implementation note |
|---|---|---|
| Default | Clear affordance and ≥ 24 × 24 CSS px pointer target (WCAG 2.2 SC 2.5.8; prefer ≥ 44 × 44 px for touch) | Expand hit area with `padding` rather than shrinking adjacent spacing |
| Hover | Visual change on hover-capable pointers only | Wrap hover styles in `@media (hover: hover)` so touch taps do not stick |
| Focus | High-contrast visible indicator not hidden by sticky bars (WCAG 2.2 SC 2.4.11) | Style `:focus-visible`; never remove outlines globally |
| Active / pressed | Immediate feedback within 100 ms (`:active` or `aria-pressed`) | Subtle scale or colour shift using compositor-safe properties |
| Disabled | Non-interactive appearance (`opacity`, cursor) | Prefer `disabled` on submit buttons during requests, or `aria-disabled="true"` when focus and tooltip explanation must remain reachable |
| Pending / loading | Prevent duplicate submission and announce progress | Set `aria-busy="true"` and update button label (`Saving…`) |

**Screen and async view states (matching `docs/DESIGN.md` `## Screens and states`):**

| View state | When to show | Required behaviour |
|---|---|---|
| Loading | Async work exceeding ~300 ms | Delay spinner/skeleton by ~250–300 ms to avoid flash on fast loads; match final layout dimensions to avoid CLS. Prefer **skeletons** when layout dimensions are known (avoids CLS); use a **spinner** for indeterminate actions where content dimensions are unknown. |
| Empty (first run) | Zero records exist yet | Explain what belongs here and give one primary creation action |
| Empty (filtered) | Query/filters match zero records | State which filters are active and offer a one-click reset |
| Error | Network, validation or server failure | Preserve user input, explain what failed safely, provide a retry or recovery path |
| Success | Mutation completed | Show explicit state update or inline confirmation; redirect only when the flow expects it |
| Permission denied | Caller lacks access (`403`) | State access is denied without exposing hidden record details; link to a safe route. Unauthenticated callers (`401`) must be redirected to the login flow, not shown a generic "access denied" message. |

### User feedback and motion

- **Acknowledge actions immediately.** Optimistic UI (`useOptimistic`) suits low-risk toggles (likes, bookmarks); destructive or billing actions must wait for server confirmation before showing success.
- **Keep error feedback adjacent.** Display field validation inline next to the input (`aria-describedby`) and reserve top-level banners for form-wide or server failures.
- **Avoid transient-only actions.** Never put an essential "Undo" or error detail solely inside an auto-dismissing toast; screen-reader and keyboard users may miss it before timeout. Use `aria-live="polite"` for status updates and `role="alert"` only for critical errors.
- **Honour reduced motion.** Wrap transitions and animations in `@media (prefers-reduced-motion: reduce)` so vestibular-sensitive users are not harmed (WCAG 2.2 SC 2.3.3). Animate only `transform` and `opacity` to avoid layout recalculations.

### Responsive layout

Design mobile-first (`min-width` queries) and use fluid primitives before adding fixed breakpoints.

- **Viewport vs. container queries:** Use `@media (min-width: …)` for page-level chrome (navigation bar, sidebar drawer, column grid). Use CSS `@container` (`container-type: inline-size`) for reusable components (cards, widgets) so they adapt to the slot they inhabit regardless of viewport width.
- **Reflow (WCAG 1.4.10):** Content must reflow cleanly down to 320 CSS px wide (or 1280 px at 400% zoom) without two-dimensional horizontal scrolling, except for inherently wide elements such as data tables (wrap tables in an overflow container with `tabindex="0"` and an accessible label).
- **Never block zoom:** Never set `user-scalable=no` or `maximum-scale=1` in `<meta name="viewport">`.
- **Safe areas and dynamic viewport:** Use `min-height: 100dvh` instead of `100vh` on full-screen mobile layouts so browser address bars do not clip bottom actions.

### Design tokens

Store design decisions as tokens rather than raw literals in component styles. Align token structure with the W3C Design Tokens Format Module (`$value` and `$type`) and expose them at runtime as CSS custom properties.

**Three-tier hierarchy:**

| Tier | Example name | Purpose |
|---|---|---|
| Primitive | `--color-blue-600`, `--space-4` | Raw palette and scale values; never referenced directly in components |
| Semantic | `--color-action-primary`, `--surface-card`, `--text-muted` | Role-based meaning; swapped per theme (light/dark/high-contrast) |
| Component | `--button-bg`, `--card-padding` | Optional component-level overrides pointing at semantic tokens |

Keep z-index values in a small named token scale (`--z-dropdown`, `--z-sticky`, `--z-modal`, `--z-toast`) instead of arbitrary numbers like `9999`. Implement dark mode and high-contrast themes by overriding semantic tokens on a root selector (`[data-theme="dark"]` or `@media (prefers-color-scheme: dark)`), never by duplicating component rules.

> **Choosing between the two dark-mode strategies:** `@media (prefers-color-scheme: dark)` automatically follows the OS setting but cannot be overridden from within the app. `[data-theme="dark"]` requires a JS toggle but lets users choose independently of the OS. Use `@media` as the base and layer `[data-theme]` on top so both work: the OS default is honoured automatically and the in-app toggle overrides it.

## Examples

### Responsive container-queried card with design tokens and reduced motion

```css
/* tokens.css — semantic tokens mapped from design system primitives */
:root {
  --surface-card: #ffffff;
  --border-subtle: #d0d7de;
  --text-primary: #1f2328;
  --focus-ring: #0969da;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --radius-md: 0.5rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --surface-card: #161b22;
    --border-subtle: #30363d;
    --text-primary: #f0f6fc;
    --focus-ring: #58a6ff;
  }
}

/* Card component using container queries + tokens */
.card-slot {
  container-type: inline-size;
  container-name: card;
}

.card {
  display: grid;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--surface-card);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: transform 150ms ease;
}

@container card (min-width: 28rem) {
  .card {
    grid-template-columns: auto 1fr;
    gap: var(--space-lg);
  }
}

@media (hover: hover) {
  .card-action:hover {
    transform: translateY(-1px);
  }
}

.card-action {
  min-width: 44px;
  min-height: 44px;
}

.card-action:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .card,
  .card-action {
    transition: none;
  }
}
```

### Complete screen-state wrapper

```tsx
interface AsyncViewProps<T> {
  /**
   * loading      – async work in progress
   * error        – request failed
   * empty-create – zero records; show a creation CTA
   * empty-filter – filters match nothing; offer a reset
   * success      – mutation just completed; show brief confirmation
   * forbidden    – 403: caller lacks permission
   * ready        – data is available; render children
   */
  status: 'loading' | 'error' | 'empty-create' | 'empty-filter' | 'success' | 'forbidden' | 'ready';
  data?: T;
  errorMessage?: string;
  successMessage?: string;
  onRetry?: () => void;
  onResetFilters?: () => void;
  onCreateFirst?: () => void;
  children: (data: T) => React.ReactNode;
}

export function AsyncView<T>({
  status,
  data,
  errorMessage,
  successMessage,
  onRetry,
  onResetFilters,
  onCreateFirst,
  children,
}: AsyncViewProps<T>) {
  if (status === 'loading') {
    return <div role="status" aria-busy="true" aria-label="Loading">Loading…</div>;
  }

  // 403: static page — no live region; screen reader reads it as normal content
  if (status === 'forbidden') {
    return (
      <p>You do not have access to this resource. Contact your administrator if you believe this is an error.</p>
    );
  }

  if (status === 'error') {
    return (
      <div role="alert">
        <p>{errorMessage ?? 'Could not load items.'}</p>
        {onRetry && <button type="button" onClick={onRetry}>Retry</button>}
      </div>
    );
  }

  if (status === 'empty-create') {
    return (
      <div>
        <p>Nothing here yet.</p>
        {onCreateFirst && <button type="button" onClick={onCreateFirst}>Create your first item</button>}
      </div>
    );
  }

  if (status === 'empty-filter') {
    return (
      <div>
        <p>No items match your current filters.</p>
        {onResetFilters && <button type="button" onClick={onResetFilters}>Clear filters</button>}
      </div>
    );
  }

  // Inline confirmation after a mutation; dismiss automatically or on user action.
  if (status === 'success') {
    return (
      <div role="status" aria-live="polite">
        {successMessage ?? 'Changes saved.'}
      </div>
    );
  }

  if (!data) return null;
  return <>{children(data)}</>;
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Hard-coding hex colours, pixel gaps or `z-index: 9999` | Breaks theming, drifts from `docs/DESIGN.md` and creates stacking bugs | Reference semantic design tokens (`var(--...)`) defined for the project |
| Designing only the populated "happy path" screen | Users hit unstyled spinners, blank screens or silent failures on empty/error states | Implement loading, empty, error, success and permission-denied states per `docs/DESIGN.md` |
| Styling `:hover` without `@media (hover: hover)` | Sticky hover highlights remain active after tapping on touchscreens | Gate hover-only effects behind `@media (hover: hover)` |
| Using `user-scalable=no` in the viewport meta tag | Prevents low-vision users from zooming; fails WCAG 1.4.4 | Allow pinch zoom (`width=device-width, initial-scale=1`) |
| Putting critical "Undo" actions only in auto-dismissing toasts | Users reading slowly or using screen readers miss the action | Keep recovery actions inline or persistent until acknowledged |
| Animating `width`, `height`, `top` or `left` | Triggers layout recalculation on every frame and causes jank/CLS | Animate only `transform` and `opacity`, and respect `prefers-reduced-motion` |

## Checklist

- [ ] Implementation matches tokens, states and breakpoints in `docs/DESIGN.md`.
- [ ] All control states (default, hover, focus-visible, active, disabled, loading) are styled.
- [ ] All view states (loading, empty-create, empty-filter, error, success, permission-denied) are handled explicitly.
- [ ] Interactive hit targets are at least 24 × 24 CSS px (prefer 44 × 44 px on touch controls).
- [ ] Transitions and animations honour `@media (prefers-reduced-motion: reduce)`.
- [ ] Layout reflows cleanly down to 320 CSS px without unintended horizontal scroll or disabled zoom.
- [ ] Reusable layout components use `@container` queries where parent slot width varies.
- [ ] Zero hard-coded colour, spacing or arbitrary `z-index` values outside token definitions.
- [ ] Any discrepancy or missing specification in `docs/DESIGN.md` is reported to the architect.

## Verify with context7 and gh_grep

- **context7:** Resolve the project's styling or component library (for example `tailwindcss`, `@radix-ui/react-dialog`, `lucide-react`) at its locked version in `package.json`. Check: theme token configuration (`@theme` in Tailwind v4 vs `theme.extend` in v3), container-query utilities (`@container`), and accessible disabled/loading patterns.
- **gh_grep:** Search `prefers-reduced-motion: reduce` for motion-safe CSS patterns; `@container` with `container-type: inline-size` for component-level responsive CSS; `@media (hover: hover)` for touch-safe hover rules; `aria-busy=` paired with loading indicators.

## Sources

- W3C WCAG 2.2 Recommendation (Target Size 2.5.8, Focus Not Obscured 2.4.11, Animation from Interactions 2.3.3): https://www.w3.org/TR/WCAG22/
- W3C Design Tokens Format Module 2025.10: https://www.designtokens.org/TR/2025.10/
- MDN: `@media (prefers-reduced-motion)`: https://developer.mozilla.org/docs/Web/CSS/@media/prefers-reduced-motion
- MDN: Using container size and style queries: https://developer.mozilla.org/docs/Web/CSS/CSS_containment/Using_container_size_and_style_queries
- MDN: `@container`: https://developer.mozilla.org/docs/Web/CSS/@container
