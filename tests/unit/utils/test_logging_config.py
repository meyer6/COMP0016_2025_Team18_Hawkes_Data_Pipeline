"""
Unit tests for app/utils/logging_config.py
"""

import logging
import pytest
from pathlib import Path

from app.utils.logging_config import setup_logging


class TestSetupLogging:

    def test_console_only(self):
        logger = setup_logging(log_level='DEBUG', log_to_file=False, log_to_console=True)
        assert logger.level == logging.DEBUG
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_only(self, temp_dir):
        log_path = temp_dir / 'test.log'
        logger = setup_logging(log_level='WARNING', log_to_file=True, log_file_path=log_path, log_to_console=False)
        assert logger.level == logging.WARNING
        # Clean up handlers to avoid file locking
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)

    def test_both_handlers(self, temp_dir):
        log_path = temp_dir / 'test.log'
        logger = setup_logging(log_level='INFO', log_to_file=True, log_file_path=log_path, log_to_console=True)
        assert len(logger.handlers) == 2
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)

    def test_no_handlers(self):
        logger = setup_logging(log_to_file=False, log_to_console=False)
        # Only the info message handler addition - no console or file
        # handlers list is cleared then nothing added except maybe 0
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)

    def test_default_log_path(self):
        """When log_file_path is None and log_to_file=True, uses default path"""
        logger = setup_logging(log_to_file=True, log_file_path=None, log_to_console=False)
        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) == 1
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)
