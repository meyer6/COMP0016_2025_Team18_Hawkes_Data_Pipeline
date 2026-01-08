"""
Processing service - manages video processing status updates
"""

import logging
from pathlib import Path

from ...infrastructure.repositories.video_repository import VideoRepository
from ...infrastructure.repositories.annotation_repository import AnnotationRepository
from ...core.config import AppConfig

logger = logging.getLogger(__name__)


class ProcessingService:
    """Manages video processing status in the repository layer"""

    def __init__(self,
                 video_repo: VideoRepository,
                 annotation_repo: AnnotationRepository,
                 config: AppConfig):
        self.video_repo = video_repo
        self.annotation_repo = annotation_repo
        self.config = config

    def mark_processing_complete(self, video_path: str, annotation_version: int) -> bool:
        success = self.video_repo.update_status(video_path, processed=True, annotation_version=annotation_version)
        if success:
            logger.info(f"Marked as processed: {Path(video_path).name} (v{annotation_version})")
        else:
            logger.error(f"Failed to update status for {video_path}")
        return success

    def mark_processing_failed(self, video_path: str) -> bool:
        success = self.video_repo.update_status(video_path, processed=False, annotation_version=None)
        if success:
            logger.warning(f"Marked as failed: {Path(video_path).name}")
        else:
            logger.error(f"Failed to update status for {video_path}")
        return success

    def get_processing_params(self) -> dict:
        return {
            'sample_every': self.config.sample_every,
            'smoothing_window': self.config.smoothing_window,
            'min_duration_sec': self.config.min_duration_sec,
            'use_gpu': self.config.enable_gpu_acceleration
        }
