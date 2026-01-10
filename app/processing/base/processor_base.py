"""
Base processor interface
Defines the contract for all video processors
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from ...models.annotation import VideoAnnotation


class ProcessorBase(ABC):
    """Abstract base class for video processors"""

    @abstractmethod
    def process_video(self,
                     video_path: str,
                     progress_callback: Optional[Callable[[str, int, int], None]] = None
                     ) -> VideoAnnotation:
        """
        Process a video file.

        Args:
            video_path: Path to video file
            progress_callback: Optional callback(stage, current, total) for progress

        Returns:
            VideoAnnotation with processing results

        Raises:
            ProcessingError: If processing fails
        """
        pass
