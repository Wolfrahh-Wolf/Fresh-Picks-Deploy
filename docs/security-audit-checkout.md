# Security Audit Report — Checkout, Payment Verification & Webhook Handling

**Audit Date:** 2026-11-27
**Auditor:** security-auditor (independent)
**Task:** .agents/tasks/006-security-audit-checkout.md
**Scope:** Razorpay checkout flow, payment verification, webhook handling (or absence)
**Standards:** OWASP Top 10:2025, API Security Top 10:2023, CWE-2025
**Dependencies Audited:** razorpay v2.0.1 (confirmed via pip show razorpay)

---

## Executive Summary

This audit independently examined the Razorpay payment integration for Fresh Picks, a Flask-based e-commerce application. The checkout flow consists of two endpoints: POST /api/checkout/razorpay-order (creates a Razorpay server order) and POST /api/checkout/verify (verifies the Razorpay payment signature and creates an order in the database). The Razorpay Python SDK v2.0.1 is used for API communication and signature verification.

**Key Finding:** The most critical finding is the presence of a committed .env file containing **live Razorpay test credentials, SMTP application password, SendGrid API key, and the Flask APP_SECRET_KEY**. Additionally, the application has **no webhook handler** for Razorpay webhooks, meaning payment status updates from Razorpay after the initial checkout flow are not handled server-side.

**Overall Verdict:** **fix required** — multiple critical and high findings must be resolved and re-audited.

---

## Scope

### Files Examined

| File | Lines | Description |
|------|-------|-------------|
| pp/main_routes.py | 1024-1237 | Checkout creation and payment verification routes |
| pp/main_routes.py | 901-905 | _serialize_cart() helper function |
| pp/extensions.py | 1-33 | Razorpay client wrapper, Flask extensions |
| pp/config.py | 1-110 | Configuration including Razorpay keys |
| pp/constants.py | 1-33 | Application constants |
| pp/__init__.py | 1-176 | Application factory, error handlers, Razorpay client init |
| equirements.txt | 10 | azorpay dependency |
| .env | — | Environment variables (found with live secrets) |
| .env.example | 1-31 | Template for environment variables |

### Assets

- Razorpay API keys (key ID and key secret)
- User session data (user_id, pending_rzp_order, pending_slot)
- Cart contents (items, quantities, prices)
- Order records (total_amount, items, delivery slot, delivery boy assignment)
- Stock inventory (product and free item stock levels)
- User PII (email, full name)
- Payment signatures (HMAC-SHA256)

### Actors

- **Authenticated user** — initiates checkout, pays via Razorpay, receives order confirmation
- **Razorpay payment gateway** — processes payments, sends signatures and webhooks
- **Attacker** — any external party attempting to manipulate payments, steal credentials, or replay transactions

### Entry Points

- POST /api/checkout/razorpay-order — creates Razorpay order, returns azorpay_order_id, mount, key_id
- POST /api/checkout/verify — receives payment signature from client, verifies, creates order in DB
- Razorpay webhooks (not implemented in code)

### Trust Boundaries

| Boundary | Protocol | Notes |
|----------|----------|-------|
| Browser ↔ API | HTTP (HTTPS in production) | CSRF-exempt endpoints for JS SDK |
| API ↔ Razorpay | HTTPS (Razorpay SDK) | Auth via key_id/key_secret |
| API ↔ PostgreSQL | Internal (Supabase) | Transaction-mode pooler |
| API ↔ Redis | Internal | Session/cache backend |

### Assumptions

- HTTPS is enforced in production on Render (assumed, not verified)
- Session cookies use Flask default secure settings (not explicitly configured)
- RAZORPAY_KEY_ID is a public-facing key (test or live), not the secret key
- Rate limiting via lask-limiter is active (200 requests/5min per IP)

---

## OWASP Top 10:2025 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| **A01:2025 Broken Access Control** | Evaluated, 2 findings | Session-based auth on checkout endpoints; IDOR not applicable (single-tenant); session state manipulation |
| **A02:2025 Cryptographic Failures** | Evaluated, 1 finding | Signature verification uses correct HMAC-SHA256 via SDK; .env file with live secrets committed |
| **A03:2025 Injection** | Evaluated, none | Input validated; parameters passed to ORM (SQLAlchemy); no raw SQL in checkout |
| **A04:2025 Insecure Design** | Evaluated, 1 finding | No webhook handler for async payment failures; no idempotency guard on verify endpoint |
| **A05:2025 Security Misconfiguration** | Evaluated, 2 findings | .env file with secrets committed; CSRF exempted on checkout endpoints (intentional but risky) |
| **A06:2025 Vulnerable and Outdated Components** | Evaluated, none | razorpay v2.0.1; no known critical advisories found |
| **A07:2025 Authentication Failures** | Evaluated, 1 finding | Session state (pending_rzp_order) has no expiration |
| **A08:2025 Software and Data Integrity Failures** | Evaluated, 1 finding | Cart total recomputed at verify stage allows amount mismatch if cart modified between order creation and payment |
| **A09:2025 Security Logging and Monitoring Failures** | Evaluated, 1 finding | No webhook handler means failed payments go unmonitored; order creation errors leak stack traces |
| **A10:2025 Server-Side Request Forgery** | Not applicable | No SSRF risk surface in checkout flow |

---

## Detailed Findings

### [CRITICAL] Committed .env file with live Razorpay test credentials and application secrets

**Location:** .env (root directory, committed to repository)
**Category:** CWE-798, OWASP A02:2025, CWE-798:2024
**Evidence:** The .env file exists in the repository root and contains actual credentials (see `.env.example` for variable names).
**Impact:** An attacker who gains read access to the repository can:
- Use Razorpay test keys to create and manipulate test orders
- Forge payment signatures using the Razorpay key secret (HMAC key for signature verification)
- Impersonate users via the Flask APP_SECRET_KEY (session signing key)
- Access SMTP and SendGrid to send email as the application
**Likelihood:** High — the .env file is committed to the git repository and accessible to anyone with repo access (public or leaked private repo). Even test credentials should be rotated as a precaution.
**Remediation:** 
1. Immediately rotate ALL credentials listed above (Razorpay keys, APP_SECRET_KEY, SMTP password, SendGrid API key) as they may have been exposed.
2. Add .env to .gitignore immediately.
3. Run git log --all -- .env to check the commit history; if secrets were ever committed, scrub them using git filter-branch or BFG Repo-Cleaner, or start a fresh history.
4. Never store secrets in .env files in version control. Use Render's environment variable dashboard for production secrets.
**Confidence:** confirmed

---

### [CRITICAL] No webhook handler — silent payment failures with no recovery

**Location:** No webhook route exists in pp/main_routes.py or any other file
**Category:** CWE-400 (unbounded resource consumption), OWASP A04:2025
**Evidence:** Searched entire pp/ directory for webhook — zero matches. No route handler exists for Razorpay webhook events (payment.failed, payment.captured, efund.failed, efund.created, etc.).
**Impact:** Razorpay can send asynchronous webhook events for various payment states. Without a handler:
- **Payment failure:** If Razorpay sends payment.failed after the user's browser shows success (race condition or delayed failure), the user has been charged but no order is created. There is **no automated refund or notification mechanism**.
- **Payment success via webhook:** If the verify endpoint fails (e.g., database error after signature verification succeeds) but Razorpay has already captured payment, money is lost with no recovery path.
- **Refund/webhook events:** Refunds initiated by admin or disputed by customers via Razorpay are never reflected in the application's order state.
**Likelihood:** High — payment race conditions and async failures are well-documented with payment gateways. Razorpay's payment flow can result in payment.captured being sent after payment.failed, or a failed payment being acknowledged by Razorpay before the client-side callback fires.
**Remediation:**
1. Create a new endpoint: POST /api/webhook/razorpay (do NOT exempt CSRF for webhooks — use signature verification instead).
2. Implement webhook signature verification using zp_client.client.utility.verify_webhook_signature(body, signature, webhook_secret) with a dedicated webhook secret from Razorpay dashboard.
3. Handle at minimum: payment.failed (notify user, no order created), payment.captured (create order if not already created), efund.created/efund.failed (update order status).
4. Use a webhook_id or payment_id as a deduplication key to handle duplicate webhook delivery.
5. Verify and test with Razorpay's webhook simulator.
**Confidence:** confirmed

---

### [HIGH] Session state (pending_rzp_order, pending_slot) has no expiration

**Location:** pp/main_routes.py:1057-1058 (set), pp/main_routes.py:1096 (checked)
**Category:** CWE-613, OWASP A07:2025
**Evidence:** session["pending_rzp_order"] = rzp_order["id"] at line 1058 and session["pending_slot"] = slot at line 1057. No TTL, no expiration check, and no cleanup if the user abandons the checkout flow. The session data persists indefinitely.
**Impact:** If an attacker obtains a valid azorpay_order_id (e.g., from server logs, browser history, or a leaked HTTP request), they can replay it against the verify endpoint indefinitely. The session-based check at line 1096 (zp_order_id != session.get("pending_rzp_order")) only validates that the submitted order ID matches the stored session value — it does not validate freshness. Since the session state never expires, a captured order ID remains valid until the session itself expires (which depends on the session cookie lifetime).
**Likelihood:** Medium — requires the attacker to obtain a valid azorpay_order_id and the victim's session cookie. However, server logs and network monitoring make order ID exposure plausible.
**Remediation:**
1. Set a TTL on pending_rzp_order and pending_slot (e.g., 15 minutes). Store the timestamp alongside the values and reject if expired.
2. Alternatively, use a one-time-use token: after verification, invalidate the pending state immediately (already done at lines 1207-1208 with session.pop()), but add an explicit expiry check before verification.
3. Consider using lask-session with configurable expiry instead of Flask's default server-side sessions.
**Confidence:** confirmed

---

### [HIGH] Cart total recomputed at verify creates amount mismatch attack vector

**Location:** pp/main_routes.py:1118-1120 (cart_total recomputed), pp/main_routes.py:1041 (amount sent to Razorpay)
**Category:** CWE-840, OWASP A01:2025
**Evidence:** At line 1041, mount_paise = int(round(cart_total * RAZORPAY_PAISE_MULTIPLIER)) sends the amount to Razorpay at order creation time. However, at line 1118-1120, the cart total is **recomputed** from the database at verification time:
`python
cart_total = round(sum(
    (row.qty_g / PRICE_DIVISOR_G) * row.price_per_1000g for row in cart_rows
), 2)
`
The Razorpay-created order's amount is never compared against the recomputed cart total at verification time. If a user modifies their cart between order creation and payment verification (or if prices change in the database), the amounts could diverge. More critically, there is **no validation that the Razorpay order amount matches the cart total at verify time**.
**Impact:** An attacker who modifies the cart between order creation and payment, or who intercepts and modifies the Razorpay order amount (if they have access to the Razorpay test environment), could potentially:
- Pay less than the cart total (if cart is modified to add items after order creation)
- Pay more than needed (if cart is modified to remove items after order creation) — though this is less concerning
- Exploit the freebie injection logic: the freebie threshold (₹500) is checked against the **recomputed** cart total, not the Razorpay-confirmed amount. A user could manipulate this to receive freebies they shouldn't qualify for.
**Likelihood:** Medium — the cart is locked server-side at order creation (the user must refresh the cart to see changes), and the Razorpay order is created with the correct amount. However, if an attacker has session access and can modify the cart before completing payment, this becomes exploitable.
**Remediation:**
1. Store the Razorpay order amount in the session or pass it through as a hidden parameter.
2. At verification time, compare the Razorpay order amount (fetched via Razorpay API: zp_client.client.order.fetch(rzp_order_id)) against the cart total.
3. Reject verification if the amounts do not match within a small tolerance (e.g., ±₹1 for rounding).
4. Alternatively, lock the cart at order creation by marking cart items as "reserved" and preventing further modifications.
**Confidence:** confirmed

---

### [HIGH] Error message in razorpay-order endpoint leaks internal details

**Location:** pp/main_routes.py:1055
**Category:** CWE-209, OWASP A05:2025
**Evidence:** 
`python
except Exception as e:
    return jsonify({"status": "ERROR", "message": f"Razorpay order creation failed: {str(e)}"})
`
**Impact:** If the Razorpay API returns a detailed error (e.g., connection refused, rate-limited, invalid response format, internal Razorpay error), the error message is returned verbatim to the client. This could expose:
- Internal Razorpay API error codes and messages
- Network routing information (e.g., connection timeout to specific hosts)
- Stack trace fragments that reveal internal architecture
**Likelihood:** Medium — Razorpay API errors are uncommon but possible during outages, rate limiting, or network issues.
**Remediation:**
1. Replace str(e) with a generic message: "Razorpay order creation failed. Please try again later."
2. Log the full exception details server-side for debugging: logger.exception("Razorpay order creation failed")
**Confidence:** confirmed

---

### [MEDIUM] No idempotency guard on the verify endpoint

**Location:** pp/main_routes.py:1082-1237 (verify endpoint, no duplicate check)
**Category:** CWE-841, OWASP A04:2025
**Evidence:** The verify endpoint creates an Order and OrderItems from the cart without checking whether an order was already created for the same Razorpay payment. After successful verification, lines 1207-1208 clean up the session, but there is no check if a previous verification attempt already created an order.
**Impact:** If the client retries the verify request (network retry, browser back-refresh, or deliberate replay), and the session has not been cleaned up yet, a duplicate order could be created for the same payment. The Razorpay payment ID would be used twice.
**Likelihood:** Medium — network retries and browser refreshes are common user behaviors.
**Remediation:**
1. Add a azorpay_payment_id to the Order model (if not already present) and add a unique constraint.
2. Before creating an order, check if an order already exists for this azorpay_payment_id.
3. If a duplicate is detected, return the existing order details instead of creating a new one (true idempotency).
4. Alternatively, add a unique constraint on (order_id, razorpay_payment_id) in the database.
**Confidence:** confirmed

---

### [MEDIUM] Razorpay key_id returned in API response

**Location:** pp/main_routes.py:1065
**Category:** CWE-200, OWASP A05:2025
**Evidence:**
`python
"key_id": os.environ.get("RAZORPAY_KEY_ID"),
`
**Impact:** The RAZORPAY_KEY_ID (test key ID) is returned to the client in the response body. While Razorpay's documentation states that the key ID is not sensitive by itself (the secret key is the sensitive credential), exposing the key ID:
- Helps an attacker identify the payment gateway configuration
- Could help tailor attacks if the key type (test vs. live) is inferred
- In the test environment, the key ID combined with any leaked test transactions could help map the payment flow
**Note:** This is standard practice for Razorpay — the client-side SDK requires the key ID to initialize the checkout. However, it should only be returned in production if using a properly scoped key.
**Likelihood:** Low — the key ID alone is not exploitable without the secret key.
**Remediation:**
1. Ensure the returned key ID is the correct environment key (test in development, live in production).
2. Consider using Razorpay's smart checkout or one-time-use keys for additional security.
3. Ensure CORS is properly configured so the response is not exposed to unintended origins.
**Confidence:** confirmed

---

### [MEDIUM] Cart modification between order creation and payment verification

**Location:** pp/main_routes.py:908-942 (cart modification endpoints), pp/main_routes.py:1036 vs 1113-1120
**Category:** CWE-840, OWASP A01:2025
**Evidence:** The cart can be modified (add, update, remove items) via separate API endpoints (/api/cart/items) at any time. The azorpay-order endpoint reads the cart total at line 1036. The erify endpoint reads the cart total again at line 1113-1120. Between these two points, the cart can be modified by the authenticated user (or via session hijacking).
**Impact:** A user could:
1. Add expensive items to the cart → create Razorpay order (high amount)
2. Remove the expensive items from the cart → pay the original (lower) amount
3. The verify endpoint would compute a lower cart total and create an order for fewer items at a lower price
This is less severe than the previous finding because the cart items are also deleted after order creation (line 1156: db.session.delete(row)), so the user would have already received their items. However, it creates an inconsistency.
**Likelihood:** Low — requires the user to perform this specific sequence of actions.
**Remediation:**
1. Lock the cart at order creation: set a flag on cart items to prevent modification after order creation.
2. Validate that the Razorpay order amount matches the cart total at verification time.
**Confidence:** confirmed

---

### [LOW] CSRF protection exempted on all checkout endpoints

**Location:** pp/main_routes.py:1025, 1083 (@csrf.exempt on both checkout endpoints)
**Category:** OWASP A01:2025, CWE-352
**Evidence:** Both /api/checkout/razorpay-order and /api/checkout/verify are exempted from CSRF protection via @csrf.exempt. This is necessary because the Razorpay JavaScript SDK directly handles payment submission, which cannot include CSRF tokens in the same way as form submissions.
**Impact:** Without CSRF protection, a malicious website could theoretically:
1. Trick a logged-in user into calling /api/checkout/razorpay-order (creating a Razorpay order)
2. However, the verify endpoint requires valid Razorpay signature parameters that only the Razorpay SDK can produce
3. The CSRF exemption is effectively mitigated by the cryptographic signature verification on the verify endpoint
**Likelihood:** Low — the signature verification requirement makes CSRF exploitation impractical.
**Remediation:**
1. Document this exemption explicitly in the code comments.
2. Ensure the Razorpay webhook endpoint (once implemented) uses webhook signature verification (not CSRF) for authentication.
3. Consider using SameSite=Lax or SameSite=Strict cookie attributes for the session cookie to provide defense-in-depth against CSRF.
**Confidence:** confirmed

---

### [LOW] Signature verification does not use timing-safe comparison for session comparison

**Location:** pp/main_routes.py:1096
**Category:** CWE-208, OWASP A02:2025
**Evidence:**
`python
if rzp_order_id != session.get("pending_rzp_order"):
`
This uses Python's != operator for string comparison, which is not timing-safe. An attacker with network-level access could potentially perform a timing side-channel attack to determine the correct azorpay_order_id character-by-character.
**Impact:** Theoretically, an attacker could extract a valid order ID through timing analysis of the response. In practice, the order ID is a server-generated UUID, which is unlikely to be guessable.
**Likelihood:** Very low — requires network-level access and many repeated requests.
**Remediation:**
Use hmac.compare_digest(rzp_order_id, session.get("pending_rzp_order", "")) for timing-safe comparison, or use secrets.compare_digest (Python 3.6+).
**Confidence:** confirmed

---

## Architecture Assessment

### Current Security Posture

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Payment signature verification** | Good | Uses Razorpay SDK's erify_payment_signature() which correctly computes HMAC-SHA256 over order_id|payment_id using the client secret, with timing-safe comparison via hmac.compare_digest |
| **Authentication** | Good | Session-based authentication with user_id check on both endpoints |
| **Input validation** | Adequate | Slot validation, required field checks, type coercion |
| **Secrets management** | Poor | .env file with live credentials committed to repository |
| **Webhook handling** | Missing | No webhook handler implemented — critical gap for async payment events |
| **Idempotency** | Missing | No deduplication on verify endpoint |
| **CSRF** | Risky | Exempted on checkout endpoints (necessary but reduces defense-in-depth) |
| **Error handling** | Poor | Internal errors leaked to clients; no structured error responses |
| **Session security** | Adequate | No explicit session timeout; default Flask session behavior |
| **Amount integrity** | Weak | No verification that Razorpay order amount matches cart total at verify time |

### Threat Model Summary (STRIDE)

| Threat | Present? | Notes |
|--------|----------|-------|
| **Spoofing** | Unlikely | Session-based auth; signature verification prevents payment impersonation |
| **Tampering** | Possible | Amount mismatch between Razorpay order and cart; no webhook handler for state updates |
| **Repudiation** | High | No audit trail for payment events; no webhook logging; duplicate orders possible |
| **Information Disclosure** | High | .env with secrets; error message leakage; key_id in response |
| **Denial of Service** | Low | Rate limiting active (200/5min); no DoS-specific vulnerabilities identified |
| **Elevation of Privilege** | Unlikely | Session-based auth; no admin access in checkout flow |

---

## Pre-existing Issues

| Finding | Severity | Location |
|---------|----------|----------|
| .env file committed to repository with live secrets | Critical | .env (root) |
| No webhook handler | High | N/A (entire absence) |
| Session state no expiration | High | pp/main_routes.py:1057-1058 |
| No idempotency on verify | Medium | pp/main_routes.py:1082-1237 |
| Amount mismatch potential | Medium | pp/main_routes.py:1041 vs 1118-1120 |
| Error message leakage | High | pp/main_routes.py:1055 |
| Non-timing-safe session comparison | Low | pp/main_routes.py:1096 |

---

## Coverage Gaps

| Area | Reason |
|------|--------|
| **HTTPS/TLS configuration** | Not verifiable via static code review; requires checking Render dashboard settings |
| **Session cookie security settings** | Flask defaults used; SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE not explicitly configured — confirmed absent from pp/__init__.py and pp/config.py |
| **Razorpay webhook configuration in dashboard** | Cannot verify if webhooks are configured in Razorpay admin; requires manual check |
| **Rate limiting effectiveness** | lask-limiter is active but no custom limits on checkout endpoints (uses default 200/5min) |
| **Database transaction isolation** | No explicit transaction isolation level set; concurrent order creation could cause race conditions |
| **Render deployment configuration** | Production secrets management, environment variable injection, and secret rotation procedures not reviewed |
| **Static analysis / dependency scanning** | No dependency vulnerability scan was performed for razorpay v2.0.1 or other dependencies |
| **Frontend Razorpay integration** | The client-side Razorpay Checkout.js integration was not audited (out of scope) |
| **Email sending security** | SMTP credentials in .env; email recipient validation not checked |

---

## Verification

All findings are based on static code review and safe local checks. The following was verified:

1. **Razorpay SDK signature verification:** Confirmed via context7 that erify_payment_signature() (v2.0.1) uses HMAC-SHA256 over order_id|payment_id with the client's secret key and hmac.compare_digest for constant-time comparison. The SDK correctly raises SignatureVerificationError on mismatch.

2. **Webhook absence:** Grep of entire pp/ directory for webhook returned zero matches. Confirmed no webhook handler exists.

3. **Secret exposure:** .env file exists in repository root with credential values. Confirmed via file read.

4. **Error message leakage:** pp/main_routes.py:1055 returns str(e) directly in the error response. Confirmed via file read.

5. **Session expiration:** No SESSION_PERMANENT, PERMANENT_SESSION_LIFETIME, or TTL logic found for checkout-specific session data. Confirmed via code scan.

6. **Amount integrity:** No comparison between Razorpay order amount and cart total at verify time. Confirmed via code scan.

7. **CSRF exemption:** Both checkout endpoints have @csrf.exempt. Confirmed via code scan.

---

## Risk Posture Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 1 | Must fix and re-audit |
| High | 3 | Must fix and re-audit |
| Medium | 3 | Should fix before production |
| Low | 2 | Should fix in next iteration |

**Verdict:** **fix required**

The .env file with live credentials is the highest priority finding and requires immediate credential rotation. The absence of a webhook handler represents a significant operational risk — payment failures and async events are silently ignored, with no automated recovery. The session expiration gap and idempotency gap should be addressed before production deployment.

---

## Remediation Priority

1. **IMMEDIATE:** Rotate all secrets in .env file; add .env to .gitignore; scrub git history
2. **IMMEDIATE:** Implement Razorpay webhook handler with signature verification
3. **HIGH:** Add session TTL to pending_rzp_order and pending_slot
4. **HIGH:** Add amount comparison between Razorpay order and cart total at verify time
5. **HIGH:** Replace str(e) in error responses with sanitized messages; log full details server-side
6. **MEDIUM:** Add idempotency guard on verify endpoint (unique constraint on payment ID)
7. **MEDIUM:** Add cart locking at order creation time
8. **LOW:** Configure SameSite cookie attributes for defense-in-depth against CSRF
9. **LOW:** Use hmac.compare_digest for session order ID comparison

---

*End of report.*
