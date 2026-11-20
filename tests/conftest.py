"""
conftest.py - pytest fixtures for Fresh Picks tests.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
