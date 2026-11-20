"""
test_security.py - Tests for password hashing and security features.
"""
from werkzeug.security import check_password_hash, generate_password_hash


class TestPasswordHashing:
    def test_hash_password(self):
        hashed = generate_password_hash("testpassword")
        assert hashed is not None
        assert len(hashed) > 10

    def test_check_password_hash_correct(self):
        hashed = generate_password_hash("testpassword")
        assert check_password_hash(hashed, "testpassword") is True

    def test_check_password_hash_incorrect(self):
        hashed = generate_password_hash("testpassword")
        assert check_password_hash(hashed, "wrongpassword") is False

    def test_different_passwords_different_hashes(self):
        hash1 = generate_password_hash("testpassword")
        hash2 = generate_password_hash("testpassword")
        assert hash1 != hash2

    def test_password_hash_format(self):
        hashed = generate_password_hash("testpassword")
        assert hashed.startswith("scrypt:") or hashed.startswith("pbkdf2:")


class TestSecurityHeaders:
    def test_content_type_json(self, client):
        resp = client.get("/api/products")
        assert resp.status_code == 200
        assert resp.content_type.startswith("application/json")


class TestCSRFProtection:
    def test_csrf_disabled_for_testing(self, app):
        assert app.config["WTF_CSRF_ENABLED"] is False

    def test_csrf_disabled_by_config(self):
        from app.config import TestingConfig
        config = TestingConfig()
        assert config.WTF_CSRF_ENABLED is False


class TestRateLimiting:
    def test_rate_limiter_configured(self, app):
        assert hasattr(app, "extensions")
        limiter_found = any("limiter" in str(k).lower() for k in app.extensions.keys())
        assert limiter_found
