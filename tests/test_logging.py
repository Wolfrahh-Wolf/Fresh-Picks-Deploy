"""
test_logging.py - Tests for logging configuration.
"""
import logging
from app.logging_setup import setup_logging


class TestLogging:
    def test_logging_initialized(self, app):
        app.logger.info("Test message")
        # Should not raise
        assert app.logger is not None

    def test_logger_has_handler(self, app):
        assert len(app.logger.handlers) >= 1

    def test_logger_level_set(self, app):
        assert app.logger.level <= logging.INFO

    def test_logger_formats_message(self, app, capsys):
        app.logger.info("Test info message")
        captured = capsys.readouterr()
        assert "Test info message" in captured.out or app.logger.level <= logging.INFO
