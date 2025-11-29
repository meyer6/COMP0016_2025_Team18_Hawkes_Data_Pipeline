"""
Video item model for grid view
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Optional

from ..infrastructure.video_utils import format_duration

logger = logging.getLogger(__name__)


@dataclass
class VideoItem:
    video_path: str
    thumbnail_path: Optional[str] = None
    processed: bool = False
    duration: float = 0.0
    fps: float = 30.0
    annotation_version: Optional[int] = None

    @property
    def filename(self) -> str:
        return Path(self.video_path).name

    @property
    def file_size_mb(self) -> float:
        try:
            return Path(self.video_path).stat().st_size / (1024 * 1024)
        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Unable to get file size for {self.video_path}: {e}")
            return 0.0

    @property
    def duration_str(self) -> str:
        return format_duration(self.duration)

    @property
    def status_text(self) -> str:
        if not self.processed:
            return "Unprocessed"
        elif self.annotation_version:
            return f"Processed (v{self.annotation_version})"
        return "Processed"
