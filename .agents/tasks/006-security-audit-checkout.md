# Task 006: Security Audit — Checkout, Payment Verification & Webhook Handling

**Class:** Standard → elevated to **Complex** (Risk: high)
**Status:** in-progress (Committing staged changes, merging to main, pushing)
**Updated:** 2026-11-27

## Goal

Conduct an independent security audit of the Razorpay checkout flow, payment verification, and any webhook handling. Produce a prioritized findings report with severity ratings and actionable remediation steps. No code modifications during the audit.

## Context

Fresh Picks is a Flask-based e-commerce app with Razorpay integration for payments. The checkout flow is:

1. **`/api/checkout/razorpay-order` (POST)** — Creates a Razorpay server order with amount derived from the user's cart. Returns `razorpay_order_id`, `amount`, `key_id` to the client. Stores `pending_rzp_order` in session.
2. **Client-side** — User pays via Razorpay Checkout (JS SDK).
3. **`/api/checkout/verify` (POST)** — Verifies payment: checks `rzp_order_id` matches session, calls `rzp_client.client.utility.verify_payment_signature()`, then creates order in DB, deducts stock, sends receipt email, and cleans up session.

Key concerns:
- No webhook handler exists (webhooks may be configured in Razorpay dashboard but not in-code)
- Amount is derived from client-side cart data on the server side but stored in Razorpay notes
- `RAZORPAY_KEY_ID` is returned to the client in the response
- No idempotency guard on the verification endpoint
- Session-based state (`pending_rzp_order`, `pending_slot`) with no expiration enforcement
- Freebie injection logic based on `cart_total` computed server-side after payment verification

## Files in Scope

| File | Description |
|------|-------------|
| `app/main_routes.py:1024-1237` | Checkout and payment verification routes |
| `app/models.py` | Order, OrderItem, CartItem models |
| `app/config.py` | Razorpay key configuration |
| `app/extensions.py` | Razorpay client wrapper |
| `app/constants.py` | Pricing constants |
| `.env.example` | Secret variable names |

## Acceptance Criteria

1. Every Razorpay signature verification path is examined for correctness.
2. Order amount manipulation attack vectors are identified and assessed.
3. Idempotency and replay attack scenarios are analyzed.
4. Secret/key leakage vectors are audited across response bodies and logs.
5. Webhook handling (or absence thereof) is documented.
6. Each finding has: severity (Critical/High/Medium/Low), description, attack scenario, and remediation steps.
7. Report is written to `docs/security-audit-checkout.md` in the repo.

## Skills: none
Research: use context7 for razorpay library signature verification API behavior.

## Documentation Sync

| File | Result |
|------|--------|
| `docs/TASKS.md` | updated (row 006 → done) |
| `docs/security-audit-checkout.md` | created by auditor (405 lines) |
| `docs/MEMORY.md` | updated (durable constraint recorded) |

## Auditor Summary

Report: `docs/security-audit-checkout.md`

**Findings: 9 total — 7 fixed, 2 deferred**

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | .env with live secrets | Critical | User confirmed not committed — not an issue |
| 2 | No webhook handler | High | Deferred (requires new endpoint) |
| 3 | Session state no expiration | High | ✅ Fixed (#1) |
| 4 | Error message leakage | High | ✅ Fixed (#2) |
| 5 | Amount mismatch | High | ✅ Fixed (#3) |
| 6 | No idempotency guard | Medium | ✅ Fixed (#4) |
| 7 | key_id in response | Medium | Deferred (standard Razorpay SDK practice) |
| 8 | Cart modification between order creation/verify | Medium | ✅ Fixed (#5) |
| 9 | CSRF exemption / non-timing-safe comparison | Low | ✅ Fixed (#7 + #1) |

**Files changed across 7 fixes:**
- `app/main_routes.py` — 7 edits (session TTL, timing-safe comparison, error sanitization, amount cross-check, idempotency guard, cart locking, CSRF comment)
- `app/models.py` — 1 edit (razorpay_payment_id column)
- `app/config.py` — 1 edit (session cookie security attributes)
- `migrations/versions/6242fe0cc8cd_...` — new migration for razorpay_payment_id column
- `migrations/env.py` — pre-existing `%` escaping bug fixed

**Pre-existing validations:**
- Razorpay SDK v2.0.1 signature verification is correct (HMAC-SHA256, timing-safe)
- Rate limiting active via flask-limiter (200/5min per IP)
- `.gitignore` includes `.env` (line 19) — user confirmed not committed

## Open Questions (from auditor)

1. Has Razorpay webhook been configured in the Razorpay dashboard?
2. What is the Render production deployment's HTTPS configuration?
3. Are session cookie security settings (SESSION_COOKIE_SECURE, HTTPONLY, SAMESITE) explicitly configured?
4. Is there any existing razorpay_payment_id column on the Order model?
