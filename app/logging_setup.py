"""
logging_setup.py - Fresh Picks: Centralized Logging Configuration
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app, name="freshpicks"):
    """Configure structured logging for the application."""
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler (rotating, 5MB x 3 files)
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "freshpicks.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    file_handler.setFormatter(formatter)

    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(
        logging.DEBUG if app.config.get("FLASK_DEBUG") else logging.INFO
    )
