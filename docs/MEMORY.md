# Project Memory

Owner: coordinator, using the `project-memory` skill. Durable facts only. No secrets or personal data. Keep under 200 lines.

## Decisions
## Constraints
- Render free tier: cold start takes ~30 seconds after inactivity (README, render.yaml).
- Payment flow: checkout session state (`pending_rzp_order`, `pending_slot`) must expire within 15 minutes (security audit, 2026-11-27).
- Payment flow: verify endpoint must cross-check Razorpay order amount against cart total before creating order (security audit, 2026-11-27).
## Conventions
- No linter configured (no flake8, ruff, or pylint in requirements.txt or config files).
- No pytest test framework; verification relies on standalone Python scripts (test_api.py, test_db.py, test_mail.py).
- OTP_TTL_MINUTES defaults to 10 minutes for all time-limited token flows.
## Pitfalls
- `app/__init__.py` line 176 creates a top-level `app = create_app()` that runs before the module-level entry point; both this and the `if __name__ == "__main__"` block in root `app.py` create the app (separate file).
- Two pooler URIs exist: `DATABASE_URL` (transaction-mode, port 6543) for the running app, and `DIRECT_URL` (session-mode, port 5432) for migrations only (app/config.py).
## User preferences
## Orchestrator lessons
- 2026-11-27: Orchestrator must never attempt to write `AGENTS.md` — even after user approval, the orchestrator's scope is task files, `docs/TASKS.md`, `docs/MEMORY.md` only. Delegates to implementer for any config/source edit. (Task 001 → 002)
