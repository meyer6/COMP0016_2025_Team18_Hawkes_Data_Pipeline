"""
Path configuration and project root detection
Fixes the Path.cwd() issue by detecting project root reliably
"""

from pathlib import Path
from typing import Optional


class PathConfig:
    """Centralized path management for the application"""

    _project_root: Optional[Path] = None

    @classmethod
    def get_project_root(cls) -> Path:
        """Uses marker files to reliably find the root regardless of working directory."""
        if cls._project_root is not None:
            return cls._project_root

        # Start from this file's location
        current = Path(__file__).resolve()

        # Traverse up looking for marker files that indicate project root
        markers = [
            'main.py',  # Main entry point
            '.git',     # Git repository
            'app',      # App directory
            'processing'  # Processing directory
        ]

        for parent in [current] + list(current.parents):
            # Check if this directory contains our marker files
            if (parent / 'main.py').exists() and (parent / 'app').is_dir():
                cls._project_root = parent
                return cls._project_root

        # Fallback: assume we're 3 levels deep from root (app/core/config)
        cls._project_root = current.parent.parent.parent
        return cls._project_root

    @classmethod
    def get_registry_path(cls) -> Path:
        return cls.get_project_root() / '.cache' / 'video_registry.json'

    @classmethod
    def get_thumbnails_dir(cls) -> Path:
        thumbnails_dir = cls.get_project_root() / '.cache' / 'thumbnails'
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        return thumbnails_dir

    @classmethod
    def get_models_dir(cls) -> Path:
        return cls.get_project_root() / 'processing' / 'models'

    @classmethod
    def get_task_classifier_model_path(cls) -> Path:
        return cls.get_models_dir() / 'task_classifier.pkl'

    @classmethod
    def get_video_inference_dir(cls) -> Path:
        return cls.get_project_root() / 'processing' / 'scripts' / 'video_inference'

    @classmethod
    def reset(cls):
        cls._project_root = None
