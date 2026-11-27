"""
conftest.py - pytest fixtures for Fresh Picks tests.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required env vars at module level so they're available
# when test files import `app` at module scope (before fixtures run).
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("RAZORPAY_KEY_ID", "test_key")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "test_secret")
os.environ.setdefault("SMTP_EMAIL", "test@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "test_password")
os.environ.setdefault("SENDGRID_API_KEY", "test_key")
os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")
os.environ.setdefault("RAZORPAY_KEY_ID", "test_key")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "test_secret")


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Ensure test env vars are set for every test."""
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret")
    monkeypatch.setenv("SMTP_EMAIL", "test@example.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "test_password")
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")


@pytest.fixture
def app():
    """Create application for testing."""
    from app import create_app
    from app.config import TestingConfig
    from app.extensions import db as _db

    _db.engine_options = {"pool_pre_ping": False}

    app = create_app(TestingConfig)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()
