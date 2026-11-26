"""
config.py - Fresh Picks: Application Configuration

All secrets are loaded from environment variables (.env locally,
Render dashboard in production). Nothing sensitive is hardcoded here.
"""

import os
from dotenv import load_dotenv

# Load .env file for local development.
# In production (Render), env vars are injected directly - load_dotenv()
# silently does nothing if no .env file is found, so this is safe either way.
load_dotenv()


class Config:
    """Base configuration - shared across all environments."""

    # ── Flask Core ──────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("APP_SECRET_KEY")

    # ── Database (SQLAlchemy) ───────────────────────────────────────────
    # Transaction-mode pooler (port 6543) - used for normal app queries.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session-mode pooler (port 5432) - used only for one-off migrations
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
    FAVICON_VERSION = os.environ.get("FAVICON_VERSION", "2")

    # ── Cache (Redis) ──────────────────────────────────────────────────
    REDIS_URL          = os.environ.get("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 60       # seconds – default cache TTL
    CACHE_KEY_PREFIX   = "fp"        # prefix for all cache keys

    # ── Mailer Provider ────────────────────────────────────────────────
    # "smtp"    = Flask-Mail (Gmail SMTP)  – development
    # "resend"  = Resend API               – production
    MAILER_PROVIDER = os.environ.get("MAILER_PROVIDER", "smtp")
    RESEND_API_KEY  = os.environ.get("RESEND_API_KEY", "")
    RESEND_FROM     = os.environ.get("RESEND_FROM", "")


class DevelopmentConfig(Config):
    """Development-specific overrides."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "dev-key")


class TestingConfig(Config):
    """Testing-specific overrides."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    SENDGRID_API_KEY = "test-key"
    OTP_TTL_MINUTES = 10


class ProductionConfig(Config):
    """Production-specific overrides."""
    DEBUG = False
    # Ensure production secrets are present
    SECRET_KEY = os.environ.get("APP_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


# Config lookup by environment name
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


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
        "REDIS_URL",
    ]
    missing = [key for key in required if not app.config.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required config values: {', '.join(missing)}. "
            f"Check your .env file or Render environment variables."
        )
