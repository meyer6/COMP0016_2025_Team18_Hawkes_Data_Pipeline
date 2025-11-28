"""
Application configuration management
"""

import json
import logging
from dataclasses import dataclass, asdict, field, fields
from pathlib import Path
from typing import Optional

from .paths import PathConfig
from .constants import ProcessingDefaults, UIConstants

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """
    Main application configuration.
    Can be loaded from a JSON file or use defaults.
    """

    # Processing configuration
    model_path: str = ""
    sample_every: int = ProcessingDefaults.SAMPLE_EVERY
    smoothing_window: int = ProcessingDefaults.SMOOTHING_WINDOW
    min_duration_sec: int = ProcessingDefaults.MIN_DURATION_SEC
    confidence_threshold: float = ProcessingDefaults.CONFIDENCE_THRESHOLD

    # Thumbnail configuration
    thumbnail_width: int = ProcessingDefaults.THUMBNAIL_WIDTH
    thumbnail_height: int = ProcessingDefaults.THUMBNAIL_HEIGHT
    thumbnail_quality: int = ProcessingDefaults.THUMBNAIL_QUALITY

    # UI configuration
    window_width: int = UIConstants.DEFAULT_WINDOW_WIDTH
    window_height: int = UIConstants.DEFAULT_WINDOW_HEIGHT
    grid_columns: int = UIConstants.GRID_COLUMNS

    # Logging configuration
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = ""

    # Device configuration (for PyTorch)
    device: Optional[str] = None  # None = auto-detect, 'cuda', 'cpu'

    # Feature flags
    enable_gpu_acceleration: bool = True
    enable_auto_processing: bool = False

    def __post_init__(self):
        if not self.model_path:
            self.model_path = str(PathConfig.get_task_classifier_model_path())

        if not self.log_file_path:
            self.log_file_path = str(PathConfig.get_project_root() / 'logs' / 'app.log')

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'AppConfig':
        if config_path is None:
            config_path = PathConfig.get_project_root() / 'config.json'

        if not config_path.exists():
            return cls()

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            known_fields = {f.name for f in fields(cls)}
            filtered = {k: v for k, v in data.items() if k in known_fields}

            return cls(**filtered)

        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> bool:
        if config_path is None:
            config_path = PathConfig.get_project_root() / 'config.json'

        try:
            with open(config_path, 'w') as f:
                json.dump(asdict(self), f, indent=2)
            return True

        except IOError as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False

    def get_model_path(self) -> Path:
        return Path(self.model_path)

    def get_log_path(self) -> Path:
        return Path(self.log_file_path)

    def validate(self) -> list[str]:
        errors = []

        if not Path(self.model_path).exists():
            errors.append(f"Model file not found: {self.model_path}")

        if self.sample_every < 1:
            errors.append(f"sample_every must be >= 1, got {self.sample_every}")

        if self.smoothing_window < 1:
            errors.append(f"smoothing_window must be >= 1, got {self.smoothing_window}")

        if self.min_duration_sec < 0:
            errors.append(f"min_duration_sec must be >= 0, got {self.min_duration_sec}")

        if not 0 <= self.confidence_threshold <= 1:
            errors.append(f"confidence_threshold must be between 0 and 1, got {self.confidence_threshold}")

        if self.thumbnail_width < 1 or self.thumbnail_height < 1:
            errors.append("Thumbnail dimensions must be positive")

        if self.window_width < 800 or self.window_height < 600:
            errors.append("Window dimensions too small (minimum 800x600)")

        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log_level: {self.log_level}. Must be one of {valid_log_levels}")

        return errors
