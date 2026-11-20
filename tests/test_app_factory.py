"""
test_app_factory.py - Tests for application factory and configuration.
"""
from app import create_app


class TestAppFactory:
    def test_create_app_returns_app(self):
        app = create_app()
        assert app is not None

    def test_app_has_secret_key(self):
        app = create_app()
        assert app.config.get("SECRET_KEY") or app.config.get("APP_SECRET_KEY")

    def test_app_testing_mode(self):
        app = create_app()
        assert app.testing is False

    def test_app_testing_config(self):
        from app.config import TestingConfig
        app = create_app(TestingConfig)
        assert app.testing is True

    def test_app_registers_blueprints(self):
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/" in rules
        assert "/login/<role>" in rules
        assert "/register" in rules
        assert "/dashboard" in rules
        assert "/admin/dashboard" in rules
        assert "/api/products" in rules

    def test_app_has_error_handlers(self):
        app = create_app()
        errors = app.error_handler_spec
        assert 400 in errors.get(None, {})
        assert 404 in errors.get(None, {})
        assert 405 in errors.get(None, {})
        assert 429 in errors.get(None, {})
        assert 500 in errors.get(None, {})

    def test_app_has_rate_limiter(self):
        app = create_app()
        assert any("limiter" in str(k).lower() for k in app.extensions.keys())

    def test_app_has_csrf_protection(self):
        app = create_app()
        assert "csrf" in app.extensions

    def test_app_has_mail(self):
        app = create_app()
        assert "mail" in app.extensions


class TestCreateAppWithConfig:
    def test_create_app_with_custom_config_class(self):
        from app.config import TestingConfig
        app = create_app(TestingConfig)
        assert app.config["TESTING"] is True
        assert app.config["WTF_CSRF_ENABLED"] is False

    def test_create_app_with_testing_config(self):
        app = create_app()
        app.config.update({"TESTING": True})
        assert app.testing is True


class TestAppContext:
    def test_app_context_works(self):
        from flask import current_app
        app = create_app()
        with app.app_context():
            assert current_app is not None
            assert current_app.name == "app"
