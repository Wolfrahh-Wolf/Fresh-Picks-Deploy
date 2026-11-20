"""
logging_setup.py - Fresh Picks: Centralized Logging Configuration
"""
import logging
import sys
import json
import os
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """JSON formatter for production log output."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class RequestFormatter(logging.Formatter):
    """Formatter that includes request info."""

    def format(self, record):
        if hasattr(record, "request_id"):
            record.msg = f"[{record.request_id}] {record.msg}"
        return super().format(record)


def setup_logging(app, name="freshpicks"):
    """Configure structured logging for the application."""
    is_debug = app.config.get("FLASK_DEBUG", False)
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if is_debug:
        console_handler.setFormatter(ColoredFormatter(log_format, datefmt=datefmt))
    else:
        console_handler.setFormatter(RequestFormatter(log_format, datefmt=datefmt))

    # File handler (rotating, 5MB x 3 files)
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "freshpicks.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    file_handler.setFormatter(JSONFormatter())

    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG if is_debug else logging.INFO)

    # Silence noisy third-party loggers in production
    if not is_debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    app.logger.info("Logging initialized | Environment=%s | Level=%s",
                    "debug" if is_debug else "production",
                    app.logger.level)
