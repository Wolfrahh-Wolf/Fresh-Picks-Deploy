"""
__init__.py - Fresh Picks: Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

from .config import Config
from .extensions import db, mail, rzp_client
from .logging_setup import setup_logging


def create_app(config_class=None):
    """Application factory for Fresh Picks."""
    app = Flask(__name__)

    # Configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Razorpay client
    rzp_client.init(
        app.config.get("RAZORPAY_KEY_ID"),
        app.config.get("RAZORPAY_KEY_SECRET")
    )

    # Mail config (Flask-Mail handles this, but explicit for clarity)
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

    return app
