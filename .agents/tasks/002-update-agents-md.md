# AGENTS.md Update Task

- **Created**: 2026-11-27
- **Task from**: `.agents/tasks/onboard-fresh-picks.md` (Stage 4: Approve and fill AGENTS.md)
- **Status**: done
- **Approved by**: user (2026-11-27)

## Goal

Fill the 4 placeholder lines in `AGENTS.md` Project block with confirmed facts from the onboarding evidence.

## Approved Content

Replace lines 7-10:

```
Before:
- Name: <project name>
- Purpose: <one sentence>
- Stack: <languages, frameworks, database, hosting>
- Commands: install `<cmd>` | dev `<cmd>` | test `<cmd>` | lint `<cmd>` | build `<cmd>`

After (user-approved):
- Name: Fresh Picks
- Purpose: Full-stack grocery e-commerce web application with customer and admin portals for ordering fresh produce online.
- Stack: Python 3.x, Flask (application factory), SQLAlchemy ORM, PostgreSQL (Supabase via Alembic), Bootstrap 5, Razorpay (payments), SendGrid/SMTP (email), FPDF2 (receipts), Redis (cache), Gunicorn, Render (PaaS hosting)
- Commands: install `pip install -r requirements.txt` | dev `python app.py` | test `python test_api.py` (or `python test_db.py` / `python test_mail.py`) | lint N/A (no linter configured) | build `pip install -r requirements.txt`
```

## Evidence for each field

| Field | Source |
|---|---|
| Name: Fresh Picks | README.md title, `render.yaml` service name |
| Purpose | README.md: "Your neighbourhood grocery store, now online. Fresh produce, fast delivery." |
| Stack | `requirements.txt` (Flask, flask-sqlalchemy, psycopg2-binary, razorpay, fpdf2, gunicorn, sendgrid, redis, bootstrap via templates), `render.yaml` (Render hosting), `app/__init__.py` (application factory) |
| Commands | README.md (install/dev), `render.yaml` buildCommand (build), root `app.py` entry point (dev), standalone test scripts (test) |

## Scope

Only replace lines 7–10 in `D:\CodeBase\Fresh-Picks-Deploy\AGENTS.md`. Nothing else in the file may change.

## Out of scope

- No other files
- No new docs
- No code changes

## Note

The orchestrator attempted direct edits and was blocked by system permissions. Only the implementer should attempt this write.
