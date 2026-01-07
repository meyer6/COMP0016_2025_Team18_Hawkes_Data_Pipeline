"""
Logging configuration for the application
Provides structured logging with file and console handlers
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_file_path: Optional[Path] = None,
    log_to_console: bool = True
) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        if log_file_path is None:
            from ..core.config import PathConfig
            log_file_path = PathConfig.get_project_root() / 'logs' / 'app.log'
            log_file_path.parent.mkdir(exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={log_level}, file={log_to_file}, console={log_to_console}")

    return logger

