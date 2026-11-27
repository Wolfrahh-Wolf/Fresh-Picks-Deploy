# Onboarding: Fresh Picks

- **Created**: 2026-11-27
- **Class**: Complex (Risk: high — auth, payments, personal data, infrastructure)
- **Playbook**: Project Onboarding (sdlc-workflows)
- **Status**: done

## Evidence Ledger

| # | Fact | Evidence | Status |
|---|---|---|---|
| 1 | Runtime: Python 3.x | `.py` files, `python app.py` in README | confirmed |
| 2 | Framework: Flask (application factory pattern) | `requirements.txt`, `app/__init__.py` (create_app factory) | confirmed |
| 3 | ORM: SQLAlchemy (via Flask-SQLAlchemy) | `flask-sqlalchemy` in requirements, `app/extensions.py`, `app/models.py` | confirmed |
| 4 | Database: PostgreSQL via Supabase | `psycopg2-binary`, `psycopg>=3.0` in requirements; README badges; transaction-mode pooler (6543) + session-mode pooler (5432) | confirmed |
| 5 | Migrations: Alembic | `alembic.ini`, `migrations/` directory | confirmed |
| 6 | Payments: Razorpay (HMAC-SHA256) | `razorpay` in requirements, README notes HMAC-SHA256 validation | confirmed |
| 7 | Email: SendGrid API + SMTP fallback | `sendgrid`, `flask-mail` in requirements; README + `.env.example` | confirmed |
| 8 | PDF receipts: FPDF2 | `fpdf2` in requirements, `app/generate_receipt.py` | confirmed |
| 9 | Cache: Redis | `redis` in requirements, `app/cache.py` | confirmed |
| 10 | Frontend: Vanilla JS + Bootstrap 5 + Jinja2 SSR | `templates/`, `static/`; README badges + architecture section | confirmed |
| 11 | Hosting: Render (PaaS) | `render.yaml` (web service + Redis service, free plan) | confirmed |
| 12 | WSGI server: Gunicorn | `gunicorn.conf.py` (2 gthread workers, 4 threads) | confirmed |
| 13 | Rate limiting: Flask-Limiter | `flask-limiter` in requirements | confirmed |
| 14 | CSRF protection: Flask-WTF | `flask-wtf` in requirements | confirmed |
| 15 | Test command: `python test_api.py` | Standalone scripts: `test_api.py`, `test_db.py`, `test_mail.py` | confirmed |
| 16 | Dev command: `python app.py` | `if __name__ == "__main__"` in `app.py`, README | confirmed |
| 17 | Lint: N/A (no linter configured) | No linter in requirements.txt; no `.flake8`, `pyproject.toml`, `pylintrc` | confirmed |
| 18 | Build: `pip install -r requirements.txt` | Render `buildCommand` in `render.yaml` | confirmed |
| 19 | Purpose: Grocery e-commerce web app | README: "Your neighbourhood grocery store, now online. Fresh produce, fast delivery." | confirmed |
| 20 | No automated test framework (pytest) | Only standalone scripts; no `conftest.py`, no pytest config | confirmed |
| 21 | OTP-based auth with time-limited tokens | `.env.example` OTP_TTL_MINUTES; README describes OTP flows | confirmed |
| 22 | Admin portal with SSE notifications | README: "Real-time new order toast notification via Server-Sent Events" | confirmed |
| 23 | Environment: `.env` file present (secrets) | `.env` exists alongside `.env.example`; secrets not read | confirmed |

## Stage Ledger

| # | Stage | Who | Result | Evidence |
|---|---|---|---|---|
| 0 | Scope and class | orchestrator | Complex (Risk: high) | Auth, payments, personal data, infrastructure |
| 1 | Inventory | orchestrator (read-only) | Complete — 23 facts confirmed | Files read: `requirements.txt`, `config.py`, `app.py`, `render.yaml`, `gunicorn.conf.py`, `README.md`, `app/__init__.py`, `app/config.py`, `alembic.ini`, `.env.example`, `CHANGELOG.md`, `opencode.jsonc`, `CLAUDE.md`, `test_api.py`, `test_db.py`, `test_mail.py`, directory listings |
| 2 | Discover commands | orchestrator | Traced to sources (see ledger) | See ledger items 15-18 |
| 3 | Baseline | Not run — no automated test framework | Standalone scripts exist but are not a test suite | `test_api.py` prints results; `test_db.py` checks connection; `test_mail.py` sends real emails (not automated) |
| 4 | Approve and fill AGENTS.md | user | Approved | User approved the exact text; system blocks direct writes to AGENTS.md — manual apply needed |
| 5 | Bootstrap docs | coordinator | All docs already exist; no new files created | `docs/` contains: PRD.md, ARCHITECTURE.md, DB.md, DESIGN.md, API-CONTRACTS.md, MEMORY.md, TASKS.md, adr/ |
| 6 | Risk map | coordinator | See MEMORY.md section below | — |
| 7 | Close | coordinator | — | — |

## Risk Map

| Area | Risk | Evidence |
|---|---|---|
| Authentication (OTP-based) | High | Registration/login via OTP; password change via OTP; SQLite-backed OTP store with TTL |
| Payments (Razorpay) | High | HMAC-SHA256 payment validation; order commits only after verification |
| Personal data | High | User profiles, addresses, order history; stored in PostgreSQL |
| Email delivery | Medium | SendGrid API key + SMTP credentials in environment variables |
| Infrastructure | High | Render PaaS; Supabase PostgreSQL; Redis cache; environment variables for all secrets |
| No linter/type-checker | Medium | No static analysis tool configured |
| No pytest test suite | Medium | Only standalone verification scripts; no regression test framework |

## Documentation Sync

| File | Owner | Result |
|---|---|---|
| `AGENTS.md` | implementer (task 002) | updated — lines 7-10 replaced |
| `README.md` | implementer | no change |
| `CHANGELOG.md` | implementer | no change |
| `docs/PRD.md` | architect | no change (already exists) |
| `docs/ARCHITECTURE.md` | architect | no change (already exists) |
| `docs/DB.md` | architect | no change (already exists) |
| `docs/DESIGN.md` | architect | no change (already exists) |
| `docs/API-CONTRACTS.md` | architect | no change (already exists) |
| `docs/adr/` | architect | no change (directory exists) |
| `docs/TASKS.md` | coordinator | updated — tasks 001-003 registered |
| `docs/MEMORY.md` | coordinator | updated — conventions, pitfalls, orchestrator lesson |

## Follow-ups

1. Add a proper test framework (pytest) — currently only standalone scripts exist
2. Add a linter (ruff or flake8) for Python code quality
3. Add a type-checker (mypy) for type safety
4. Create a seed/fixture system for local testing without production database
