"""
Video service - handles video import, metadata extraction, and thumbnail generation
Extracted from MainWindow to separate business logic from UI
"""

import cv2
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ...models.video_item import VideoItem
from ...infrastructure.repositories.video_repository import VideoRepository
from ...infrastructure.repositories.annotation_repository import AnnotationRepository
from ...infrastructure.video_utils import get_video_metadata, get_middle_frame
from ...core.config import AppConfig, PathConfig
from ...domain import Result, Ok, Err
from ...utils.error_handling import VideoError, VideoNotFoundError, VideoReadError

logger = logging.getLogger(__name__)


class VideoService:
    """Service for managing video operations"""

    def __init__(self, video_repo: VideoRepository, annotation_repo: AnnotationRepository, config: AppConfig):
        self.video_repo = video_repo
        self.annotation_repo = annotation_repo
        self.config = config

    def import_video(self, video_path: str) -> Result[VideoItem, VideoError]:
        path = Path(video_path)

        if not path.exists():
            error = VideoNotFoundError(f"Video file not found: {path.name}", video_path=video_path)
            logger.error(f"Video not found: {video_path}")
            return Err(error)

        existing = self.video_repo.find_by_path(video_path)
        if existing is not None:
            error = VideoError(f"Video already imported: {path.name}", video_path=video_path)
            logger.warning(f"Video already imported: {video_path}")
            return Err(error)

        metadata_result = get_video_metadata(video_path)
        if metadata_result.is_err():
            return Err(metadata_result.unwrap_err())

        metadata = metadata_result.unwrap()

        thumbnail_result = self.generate_thumbnail(video_path)
        thumbnail_path = thumbnail_result.unwrap() if thumbnail_result.is_ok() else None

        annotation = self.annotation_repo.load(video_path)
        processed = annotation is not None and annotation.processed
        version = annotation.version if annotation else None

        video_item = VideoItem(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            processed=processed,
            duration=metadata.duration,
            fps=metadata.fps,
            annotation_version=version
        )

        if not self.video_repo.add(video_item):
            error = VideoError(f"Failed to save video to registry", video_path=video_path)
            logger.error(f"Failed to save video to registry: {video_path}")
            return Err(error)

        logger.info(f"Imported video: {path.name} ({metadata.duration:.2f}s, {metadata.fps:.2f}fps)")
        return Ok(video_item)

    def generate_thumbnail(self, video_path: str) -> Result[str, VideoError]:
        frame_result = get_middle_frame(video_path)
        if frame_result.is_err():
            return Err(frame_result.unwrap_err())

        success, frame = frame_result.unwrap()

        if not success or frame is None:
            error = VideoReadError(
                f"Failed to extract frame for thumbnail",
                video_path=video_path
            )
            logger.warning(f"Failed to extract thumbnail frame from {video_path}")
            return Err(error)

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            thumbnail_filename = f"thumb_{timestamp}.jpg"
            thumbnails_dir = PathConfig.get_thumbnails_dir()
            thumbnail_path = thumbnails_dir / thumbnail_filename

            height, width = frame.shape[:2]
            target_width = self.config.thumbnail_width
            target_height = self.config.thumbnail_height

            if width > 0 and height > 0:
                scale = min(target_width / width, target_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                resized = cv2.resize(frame, (new_width, new_height))

                success = cv2.imwrite(
                    str(thumbnail_path),
                    resized,
                    [cv2.IMWRITE_JPEG_QUALITY, self.config.thumbnail_quality]
                )

                if not success:
                    error = VideoError(
                        f"Failed to write thumbnail",
                        video_path=video_path,
                        details=f"cv2.imwrite failed for {thumbnail_path}"
                    )
                    logger.warning(f"Failed to write thumbnail to {thumbnail_path}")
                    return Err(error)

                logger.debug(f"Generated thumbnail: {thumbnail_filename}")
                return Ok(str(thumbnail_path))
            else:
                error = VideoError(
                    f"Invalid frame dimensions",
                    video_path=video_path,
                    details=f"width={width}, height={height}"
                )
                logger.warning(f"Invalid frame dimensions for {video_path}")
                return Err(error)

        except Exception as e:
            error = VideoError(
                f"Error generating thumbnail",
                video_path=video_path,
                details=str(e)
            )
            logger.error(f"Error generating thumbnail for {video_path}: {e}", exc_info=True)
            return Err(error)

    def delete_videos(self, video_paths: List[str]) -> Result[int, VideoError]:
        deleted_count = 0

        for video_path in video_paths:
            try:
                video_item = self.video_repo.find_by_path(video_path)

                if video_item and video_item.thumbnail_path:
                    thumbnail_path = Path(video_item.thumbnail_path)
                    if thumbnail_path.exists():
                        try:
                            thumbnail_path.unlink()
                            logger.debug(f"Deleted thumbnail: {thumbnail_path}")
                        except Exception as e:
                            logger.error(f"Error deleting thumbnail: {e}")

                self.annotation_repo.delete_all_versions(video_path)

                if self.video_repo.remove(video_path):
                    deleted_count += 1
                    logger.info(f"Deleted video: {Path(video_path).name}")

            except Exception as e:
                logger.error(f"Error deleting video {video_path}: {e}")

        return Ok(deleted_count)

    def get_all_videos(self) -> List[VideoItem]:
        return self.video_repo.get_all()

    def get_video_metadata(self, video_path: str) -> Result[tuple, VideoError]:
        result = get_video_metadata(video_path)

        if result.is_err():
            return result

        metadata = result.unwrap()
        return Ok((metadata.fps, metadata.duration, metadata.frame_count))

    def is_video_already_imported(self, video_path: str) -> bool:
        return self.video_repo.find_by_path(video_path) is not None
