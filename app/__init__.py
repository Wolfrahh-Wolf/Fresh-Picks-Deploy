"""
__init__.py - Fresh Picks: Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from .config import Config
from .extensions import db, mail, rzp_client
from .logging_setup import setup_logging


def create_app(config_class=None):
    """Application factory for Fresh Picks."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    rzp_client.init(app.config.get("RAZORPAY_KEY_ID"), app.config.get("RAZORPAY_KEY_SECRET"))

    # Rate limiting (memory backend, no Redis required)
    Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    # CSRF protection for all POST/PATCH/PUT/DELETE requests
    CSRFProtect(app)

    # Mail config
    app.config["MAIL_DEFAULT_SENDER"] = (
        app.config.get("SENDER_NAME", "FreshPicks"),
        app.config.get("SMTP_EMAIL")
    )

    # Validate config
    from .config import validate_config
    validate_config(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints/routes
    from . import main_routes
    app.register_blueprint(main_routes.bp)

    # ── Database Table Initialization ───────────────────────────────
    with app.app_context():
        from .models import OTPVerification
        db.create_all()

    # ── Error Handlers ──────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return {"status": "ERROR", "message": "Bad request"}, 400

    @app.errorhandler(404)
    def not_found(e):
        return {"status": "ERROR", "message": "Resource not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"status": "ERROR", "message": "Method not allowed"}, 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return {"status": "ERROR", "message": "Rate limit exceeded. Please try again later."}, 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Unhandled server error: %s", e)
        return {"status": "ERROR", "message": "Internal server error"}, 500

    return app


app = create_app()
