"""
Proper module loading for video_inference without sys.path manipulation
Replaces the fragile sys.path.insert() hack
"""

import importlib.util
import logging
from pathlib import Path
from typing import Optional, Any

from ..core.config import PathConfig

logger = logging.getLogger(__name__)


class InferenceLoader:
    """Loads the video_inference module without modifying sys.path"""

    _cached_module: Optional[Any] = None

    @classmethod
    def load_video_inference_module(cls) -> Any:
        if cls._cached_module is not None:
            return cls._cached_module

        inference_dir = PathConfig.get_video_inference_dir()
        module_path = inference_dir / 'video_inference.py'

        if not module_path.exists():
            raise ImportError(
                f"video_inference.py not found at {module_path}. "
                f"Ensure the processing/scripts/video_inference directory exists."
            )

        try:
            spec = importlib.util.spec_from_file_location(
                "video_inference",
                module_path
            )

            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create module spec for {module_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            cls._cached_module = module

            logger.info(f"Loaded video_inference module from {module_path}")
            return module

        except Exception as e:
            logger.error(f"Failed to load video_inference module: {e}", exc_info=True)
            raise ImportError(f"Failed to load video_inference module: {e}") from e

    @classmethod
    def reset_cache(cls):
        cls._cached_module = None
