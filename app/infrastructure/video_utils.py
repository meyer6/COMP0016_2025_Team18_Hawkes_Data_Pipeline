"""
Shared video utilities for handling OpenCV video operations
Eliminates duplicated video capture initialisation code
"""

import cv2
import logging
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from ..domain import Result, Ok, Err
from ..utils.error_handling import VideoError, VideoNotFoundError, VideoReadError, VideoCorruptedError

logger = logging.getLogger(__name__)


def format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass
class VideoMetadata:
    fps: float
    frame_count: int
    width: int
    height: int
    duration: float

    @property
    def duration_str(self) -> str:
        return format_duration(self.duration)


def open_video_capture(video_path: str) -> Result[cv2.VideoCapture, VideoError]:
    path = Path(video_path)

    if not path.exists():
        error = VideoNotFoundError(
            f"Video file not found: {path.name}",
            video_path=video_path
        )
        logger.error(f"Video not found: {video_path}")
        return Err(error)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        error = VideoReadError(
            f"Cannot open video file: {path.name}",
            video_path=video_path,
            details="OpenCV VideoCapture failed to open file"
        )
        logger.error(f"Failed to open video: {video_path}")
        return Err(error)

    logger.debug(f"Opened video capture: {path.name}")
    return Ok(cap)


def get_video_metadata(video_path: str) -> Result[VideoMetadata, VideoError]:
    result = open_video_capture(video_path)

    if result.is_err():
        return result

    cap = result.unwrap()

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps <= 0 or frame_count <= 0:
            error = VideoCorruptedError(
                f"Invalid video metadata",
                video_path=video_path,
                details=f"fps={fps}, frame_count={frame_count}"
            )
            logger.error(f"Invalid metadata for {video_path}: fps={fps}, frames={frame_count}")
            return Err(error)

        duration = frame_count / fps if fps > 0 else 0.0

        metadata = VideoMetadata(
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration=duration
        )

        logger.debug(f"Extracted metadata from {Path(video_path).name}: {duration:.2f}s, {fps:.2f}fps")
        return Ok(metadata)

    except Exception as e:
        error = VideoError(
            f"Failed to read video metadata",
            video_path=video_path,
            details=str(e)
        )
        logger.error(f"Error reading metadata from {video_path}: {e}", exc_info=True)
        return Err(error)

    finally:
        cap.release()


def extract_frame(video_path: str, frame_number: int) -> Result[Tuple[bool, Optional[any]], VideoError]:
    result = open_video_capture(video_path)

    if result.is_err():
        return result

    cap = result.unwrap()

    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()

        if not success:
            logger.warning(f"Failed to read frame {frame_number} from {video_path}")

        return Ok((success, frame))

    except Exception as e:
        error = VideoError(
            f"Failed to extract frame {frame_number}",
            video_path=video_path,
            details=str(e)
        )
        logger.error(f"Error extracting frame from {video_path}: {e}", exc_info=True)
        return Err(error)

    finally:
        cap.release()


def get_middle_frame(video_path: str) -> Result[Tuple[bool, Optional[any]], VideoError]:
    cap_result = open_video_capture(video_path)
    if cap_result.is_err():
        return cap_result

    cap = cap_result.unwrap()
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            return Err(VideoReadError("Video has no frames", video_path=video_path))

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        success, frame = cap.read()
        if not success:
            logger.warning(f"Failed to read middle frame from {video_path}")
        return Ok((success, frame))
    except Exception as e:
        return Err(VideoError(f"Failed to extract middle frame", video_path=video_path, details=str(e)))
    finally:
        cap.release()
