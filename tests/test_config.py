"""
test_config.py - Tests for configuration hierarchy and validation.
"""
import os
import pytest
from app.config import Config, DevelopmentConfig, TestingConfig, ProductionConfig


class TestConfig:
    def test_base_config_has_required_attrs(self):
        assert hasattr(Config, "SECRET_KEY")
        assert hasattr(Config, "SQLALCHEMY_DATABASE_URI")
        assert hasattr(Config, "RAZORPAY_KEY_ID")
        assert hasattr(Config, "RAZORPAY_KEY_SECRET")
        assert hasattr(Config, "SMTP_EMAIL")
        assert hasattr(Config, "SMTP_APP_PASSWORD")

    def test_base_config_sqlalchemy_tracked_modifications_false(self):
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False

    def test_base_config_otp_ttl(self):
        assert Config.OTP_TTL_MINUTES == 10

    def test_base_config_smtp_port_465(self):
        assert Config.SMTP_PORT == 465


class TestDevelopmentConfig:
    def test_debug_true(self):
        config = DevelopmentConfig()
        assert config.DEBUG is True

    def test_has_sendgrid_key(self):
        config = DevelopmentConfig()
        assert config.SENDGRID_API_KEY is not None


class TestTestingConfig:
    def test_testing_true(self):
        config = TestingConfig()
        assert config.TESTING is True

    def test_csrf_disabled(self):
        config = TestingConfig()
        assert config.WTF_CSRF_ENABLED is False

    def test_memory_database(self):
        config = TestingConfig()
        assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

    def test_otp_ttl_10(self):
        config = TestingConfig()
        assert config.OTP_TTL_MINUTES == 10


class TestProductionConfig:
    def test_has_secret_key(self):
        config = ProductionConfig()
        assert hasattr(config, "SECRET_KEY")


class TestConfigValidation:
    def test_validate_config_missing_secret_key(self, app):
        from app.config import validate_config
        app.config["SECRET_KEY"] = ""
        with pytest.raises(RuntimeError, match="Missing required config"):
            validate_config(app)

    def test_validate_config_missing_database_uri(self, app):
        from app.config import validate_config
        app.config["SQLALCHEMY_DATABASE_URI"] = None
        with pytest.raises(RuntimeError, match="Missing required config"):
            validate_config(app)

    def test_validate_config_missing_razorpay_key(self, app):
        from app.config import validate_config
        app.config["RAZORPAY_KEY_ID"] = ""
        with pytest.raises(RuntimeError, match="Missing required config"):
            validate_config(app)

    def test_validate_config_missing_smtp_email(self, app):
        from app.config import validate_config
        app.config["SMTP_EMAIL"] = ""
        with pytest.raises(RuntimeError, match="Missing required config"):
            validate_config(app)

    def test_validate_config_passes_all_required(self, app):
        from app.config import validate_config
        validate_config(app)  # Should not raise


class TestConfigByName:
    def test_config_by_name_returns_dict(self):
        from app.config import config_by_name
        assert isinstance(config_by_name, dict)

    def test_config_by_name_has_environments(self):
        from app.config import config_by_name
        assert "development" in config_by_name
        assert "testing" in config_by_name
        assert "production" in config_by_name

    def test_config_by_name_get_valid_env(self):
        from app.config import config_by_name
        config = config_by_name["development"]
        assert config is not None

    def test_config_by_name_returns_default_for_invalid_env(self):
        from app.config import config_by_name
        config = config_by_name.get("invalid_env", config_by_name["development"])
        assert config == config_by_name["development"]
