"""
config.py - Fresh Picks: Application Configuration

All secrets are loaded from environment variables (.env locally,
Render dashboard in production). Nothing sensitive is hardcoded here.
"""

import os
from dotenv import load_dotenv

# Load .env file for local development.
# In production (Render), env vars are injected directly — load_dotenv()
# silently does nothing if no .env file is found, so this is safe either way.
load_dotenv()


class Config:
    # ── Flask Core ──────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("APP_SECRET_KEY")

    # ── Database (SQLAlchemy) ───────────────────────────────────────────
    # Transaction-mode pooler (port 6543) — used for normal app queries.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session-mode pooler (port 5432) — used only for one-off migrations
    # (e.g. flask db upgrade), not used by the running app itself.
    DIRECT_URL = os.environ.get("DIRECT_URL")

    # ── Razorpay ─────────────────────────────────────────────────────────
    RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

    # ── SMTP (Flask-Mail) ────────────────────────────────────────────────
    SMTP_EMAIL         = os.environ.get("SMTP_EMAIL")
    SMTP_APP_PASSWORD  = os.environ.get("SMTP_APP_PASSWORD")
    SMTP_HOST          = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT          = int(os.environ.get("SMTP_PORT", 465))
    SENDER_NAME        = os.environ.get("SENDER_NAME", "FreshPicks")

    # ── OTP ──────────────────────────────────────────────────────────────
    OTP_TTL_MINUTES = int(os.environ.get("OTP_TTL_MINUTES", 10))


def validate_config(app):
    """
    Called once at app startup. Fails loudly if any required secret
    is missing, instead of failing silently mid-request later.
    """
    required = [
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "RAZORPAY_KEY_ID",
        "RAZORPAY_KEY_SECRET",
        "SMTP_EMAIL",
        "SMTP_APP_PASSWORD",
    ]
    missing = [key for key in required if not app.config.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required config values: {', '.join(missing)}. "
            f"Check your .env file or Render environment variables."
        )