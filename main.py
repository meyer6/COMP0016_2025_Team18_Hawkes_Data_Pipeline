#!/usr/bin/env python3
"""
PyQt6 Application Entry Point
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.core.config import AppConfig
from app.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    config = AppConfig.load()

    errors = config.validate()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nUsing default configuration where possible...")

    setup_logging(
        log_level=config.log_level,
        log_to_file=config.log_to_file,
        log_file_path=config.get_log_path()
    )

    logger.info("=== Video Analysis Application Starting ===")

    app = QApplication(sys.argv)
    app.setApplicationName("Video Analysis Application")

    window = MainWindow(config)
    window.show()

    logger.info("Application window shown")

    exit_code = app.exec()

    logger.info(f"=== Application Exiting (code: {exit_code}) ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
