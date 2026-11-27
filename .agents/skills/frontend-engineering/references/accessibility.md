# Accessibility

Covers web accessibility implementation: semantic HTML, keyboard navigation, focus management, ARIA usage limits, colour contrast, form labelling and WCAG 2.2 compliance checks; standards checked against WCAG 2.2 (W3C Recommendation, October 2023) on 2026-11-26.

## Contents

- Semantic HTML first
- Keyboard navigation
- Focus management
- ARIA: when and how
- Colour contrast
- Form labelling
- WCAG 2.2 key criteria
- Testing accessibility

## Guidance

### Semantic HTML first

The first rule of ARIA is: use native HTML elements before ARIA. Native elements carry built-in semantics, keyboard behaviour and screen reader announcements at zero cost.

| Want | Use this | Not this |
|---|---|---|
| A clickable action | `<button type="button">` | `<div onClick>` |
| A page-to-page link | `<a href="…">` | `<span onClick>` |
| A landmark | `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>` | `<div class="nav">` |
| A heading hierarchy | `<h1>` through `<h6>` | `<p class="title">` |
| Grouped options | `<fieldset>` + `<legend>` | Visually grouped labels |
| Data table | `<table>` with `<th scope>` | CSS grid with no headers |

### Keyboard navigation

Every interactive element must be reachable and operable by keyboard alone.

**Tab order:** follows DOM order. Keep the visual reading order and DOM order in sync. Using CSS to visually reorder elements (e.g., `flex-direction: row-reverse`, `order`) without reordering the DOM creates a confusing tab sequence (WCAG 2.4.3).

**Keys to support in custom widgets:**

| Widget | Required keys |
|---|---|
| Button | Enter, Space (activate) |
| Link | Enter (follow) |
| Modal / dialog | Escape (close); Tab/Shift-Tab (cycle within) |
| Accordion | Enter/Space (expand/collapse) |
| Select / listbox | Arrow keys (navigate options); Enter (select); Escape (close) |
| Tab panel | Arrow keys (switch tabs); Tab (move into panel) |
| Menu | Arrow keys (navigate items); Escape (close); Enter (activate) |

Do not rely on `click` events alone for custom interactive elements. A `<div role="button">` needs explicit `keydown` handlers for Enter and Space.

**No keyboard trap (WCAG 2.1.2):** users must be able to Tab out of every component. Modal dialogs are the one exception: they intentionally trap focus while open and must release it on close.

### Focus management

Focus must be visible at all times (WCAG 2.4.7). Never suppress focus rings globally:

```css
/* Bad: hides focus for all users */
* { outline: none; }

/* Good: show a custom indicator only for keyboard users */
:focus-visible { outline: 2px solid #005fcc; outline-offset: 2px; }
:focus:not(:focus-visible) { outline: none; }  /* hide for mouse clicks if desired */
```

**WCAG 2.2 SC 2.4.11 (Focus Not Obscured – Minimum, Level AA):** when an element receives focus, it must not be entirely hidden by sticky headers, cookie banners or chat widgets. Test by tabbing through the page with a sticky header present.

**Programmatic focus management** is required when:
- A modal opens: move focus to the first focusable element inside (or the dialog container itself with `tabIndex={-1}`).
- A modal closes: return focus to the trigger element that opened it.
- A route changes in an SPA: move focus to the page heading or a skip-to-content landmark to announce the new page to screen reader users.
- Dynamic content appears: announce via `aria-live` or move focus only when the user expects it.

```tsx
// Modal focus management
const dialogRef = useRef<HTMLDivElement>(null);
const triggerRef = useRef<HTMLButtonElement>(null);

function openModal() {
  setOpen(true);
  // Focus moves inside useEffect after the dialog renders
}

useEffect(() => {
  if (open) dialogRef.current?.focus();
  else triggerRef.current?.focus();
}, [open]);
```

Use `tabIndex={-1}` on the dialog container to make it focusable programmatically without adding it to the tab sequence.

### ARIA: when and how

Use ARIA only when native HTML cannot provide the required semantics. ARIA does not add keyboard behaviour; it only communicates state and role to assistive technology.

**Key rules:**
- `role` overrides the accessibility name of an element completely; set it deliberately.
- `aria-hidden="true"` removes an element and its descendants from the accessibility tree entirely. Apply it to decorative icons and background content behind a modal.
- `aria-label` overrides the visible label; use it only when there is no visible label to associate.
- `aria-describedby` points to a description element (error message, hint text); `aria-labelledby` points to a visible label.
- `aria-live="polite"` announces changes without interrupting the current speech. Use for status messages, success banners, cart updates.
- `aria-live="assertive"` interrupts immediately. Use only for time-sensitive errors or alerts.

**Common ARIA patterns:**

```tsx
{/* Dialog */}
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title" ref={dialogRef} tabIndex={-1}>
  <h2 id="dialog-title">Confirm Delete</h2>
  …
</div>

{/* Status update */}
<div aria-live="polite" aria-atomic="true">
  {saved && <span>Changes saved.</span>}
</div>

{/* Expandable section */}
<button aria-expanded={isOpen} aria-controls="panel-id" onClick={() => setIsOpen(o => !o)}>
  Section title
</button>
<div id="panel-id" hidden={!isOpen}>…</div>
```

Do not use `aria-label` to fix a missing visible label. Add the visible label and associate it with `htmlFor` / `id`.

### Colour contrast

**WCAG 2.1 SC 1.4.3 (Level AA):** minimum contrast ratio of **4.5:1** for normal text; **3:1** for large text (≥ 18 pt / 14 pt bold) and UI components (borders, icons).

**WCAG 2.1 SC 1.4.6 (Level AAA):** enhanced ratio of **7:1** for normal text.

Measure with browser DevTools (colour picker shows contrast ratio) or axe DevTools. Automated tools catch many violations but miss contrast in images and gradients; check those manually.

Colour must not be the **only** means of conveying information (WCAG 1.4.1). Pair colour with an icon, pattern or text label (e.g., a red border alone is insufficient for an error; add an error icon and text).

### Form labelling

Every form control must have a programmatically associated label:

```tsx
{/* Good: explicit association */}
<label htmlFor="email">Email address</label>
<input type="email" id="email" name="email" required aria-describedby="email-hint" />
<p id="email-hint">We will never share your email.</p>

{/* Good: wrapping label */}
<label>
  <input type="checkbox" name="agree" />
  I agree to the terms
</label>

{/* Bad: placeholder as the only label */}
<input type="text" placeholder="Email" />
```

Required fields: add `required` to the input and communicate requirement visually (asterisk with a legend). Do not rely on colour alone.

Error messages: associate with `aria-describedby`; set `aria-invalid="true"` on the control when it has an error. Display error text adjacent to the field, not only as an alert at the top of the page.

```tsx
<input
  id="username"
  name="username"
  aria-invalid={!!error}
  aria-describedby={error ? 'username-error' : undefined}
/>
{error && <p id="username-error" role="alert">{error}</p>}
```

### WCAG 2.2 key criteria

WCAG 2.2 (October 2023) added 9 new success criteria and removed SC 4.1.1 (Parsing); existing criteria such as SC 2.4.4 (Link Purpose – In Context) remain active. The new criteria most relevant to web applications:

| SC | Level | Summary | Most common failure |
|---|---|---|---|
| 2.4.11 Focus Not Obscured (Minimum) | AA | Focused component not entirely hidden by sticky UI | Sticky header or chat bubble fully covers the focused button |
| 2.4.12 Focus Not Obscured (Enhanced) | AAA | No part of focused component hidden | Same, stricter |
| 2.4.13 Focus Appearance | AAA | Focus indicator area ≥ perimeter of component × 2 px; contrast ≥ 3:1 | Thin or low-contrast outline |
| 2.5.3 Label in Name | A | Visible label is part of the accessible name | Icon-only button where `aria-label` does not contain the icon's visible text |
| 2.5.7 Dragging Movements | AA | All drag operations have a pointer alternative | Drag-to-reorder with no up/down button alternative |
| 2.5.8 Target Size (Minimum) | AA | Touch targets ≥ 24 × 24 CSS px (with exceptions) | Small icon buttons on mobile |
| 3.2.6 Consistent Help | A | Help mechanisms appear in same relative order across pages | Contact link moved to footer on some pages |
| 3.3.7 Redundant Entry | A | Do not ask for the same information twice in a process | Multi-step form re-asking for name already provided |
| 3.3.8 Accessible Authentication (Minimum) | AA | Cognitive function test not required unless alternative provided | CAPTCHA with no alternative |

### Testing accessibility

Automated tools catch approximately 30–40% of accessibility issues. Manual and assistive-technology testing is required.

**Automated:**
- Run axe DevTools (browser extension) or the `axe-core` integration in Vitest/Jest on every component.
- Run Lighthouse accessibility audit in CI.

**Manual keyboard test:**
1. Tab through the entire page; every interactive element receives focus.
2. Activate each element with Enter and Space.
3. Navigate a modal: Escape closes it; focus returns to the trigger.
4. Submit a form with keyboard only; check error announcements.

**Screen reader test (minimum):**
- macOS: VoiceOver + Safari
- Windows: NVDA + Firefox or Chrome
- Mobile: TalkBack (Android) or VoiceOver (iOS)

Check: headings make sense out of context; links and buttons have descriptive names; dynamic content changes are announced.

## Examples

### Modal with correct focus management and ARIA

```tsx
'use client';
import { useEffect, useRef } from 'react';

interface ModalProps { isOpen: boolean; onClose: () => void; title: string; children: React.ReactNode; }

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (isOpen) ref.current?.focus(); }, [isOpen]);
  if (!isOpen) return null;
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title"
         ref={ref} tabIndex={-1}
         onKeyDown={e => { if (e.key === 'Escape') onClose(); }}>
      <h2 id="modal-title">{title}</h2>
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `outline: none` globally | Keyboard users cannot see where focus is | Use `:focus-visible` for custom indicator |
| `<div onClick>` for a button | No keyboard activation; no accessible role | Use `<button type="button">` |
| Placeholder as label | Disappears on typing; fails contrast in many browsers | Use `<label>` with `htmlFor` |
| Not returning focus after modal closes | Keyboard user loses their place in the page | Return focus to the trigger element |
| `aria-label` that does not match visible text | Breaks voice control ("click Save" activates nothing) | Include the visible text in `aria-label` or use `aria-labelledby` |
| Missing `aria-describedby` on error inputs | Screen reader does not announce which field errored | Link error message ID via `aria-describedby` and set `aria-invalid` |

## Checklist

- [ ] All interactive elements are native HTML or have correct `role` + keyboard handlers.
- [ ] Focus ring is visible for keyboard users (`:focus-visible` with ≥ 3:1 contrast).
- [ ] No element is entirely obscured by sticky UI when focused (WCAG 2.4.11).
- [ ] Modal dialogs trap focus, respond to Escape, and return focus to the trigger on close.
- [ ] All form controls have programmatically associated labels.
- [ ] Error states use `aria-invalid` and `aria-describedby`.
- [ ] Colour contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI components.
- [ ] Colour is not the sole means of conveying information.
- [ ] `aria-live` used for dynamic content; `role="alert"` only for critical, immediate messages.
- [ ] Automated axe scan passes with zero violations.

## Verify with context7 and gh_grep

- **context7:** Check `axe-core` for the installed version's rule set and query API; `@testing-library/jest-dom` for accessibility matchers like `toHaveAccessibleName`; any component library in use (Radix UI, Headless UI) for built-in ARIA management.
- **gh_grep:** Search `role="dialog"` with `aria-modal` for modal patterns; `aria-live="polite"` for status announcements; `:focus-visible` for custom focus indicator CSS; `aria-describedby` with error state management; `tabIndex={-1}` on dialog containers.

## Sources

- WCAG 2.2 (W3C Recommendation, October 2023): https://www.w3.org/TR/WCAG22/
- MDN: ARIA authoring practices: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA
- ARIA Authoring Practices Guide, Dialog pattern: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
- axe-core rules: https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md
- WebAIM: Colour Contrast Checker: https://webaim.org/resources/contrastchecker/
