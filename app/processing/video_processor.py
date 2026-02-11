"""
Main video processor that combines task classification and participant detection
"""

import cv2
import logging
from pathlib import Path
from typing import Callable, Optional

from ..models.annotation import VideoAnnotation, TaskSegment, ParticipantMarker
from .task_classifier import TaskClassifier
from .participant_detector import ParticipantDetector
from .batch_optimiser import BatchOptimiser
from .base.processor_base import ProcessorBase
from ..core.config import AppConfig
from ..infrastructure.video_utils import get_video_metadata, open_video_capture
from ..utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)


class VideoProcessor(ProcessorBase):
    """Orchestrates video processing with task classification and participant detection"""

    def __init__(self, use_gpu: bool = True,
                 sample_every: int = 30, smoothing_window: int = 15,
                 min_duration_sec: int = 5):
        self.use_gpu = use_gpu
        self.sample_every = sample_every
        self.smoothing_window = smoothing_window
        self.min_duration_sec = min_duration_sec
        self._task_classifier = None
        self._participant_detector = None

    @property
    def task_classifier(self) -> TaskClassifier:
        if self._task_classifier is None:
            self._task_classifier = TaskClassifier()
        return self._task_classifier

    @property
    def participant_detector(self) -> ParticipantDetector:
        if self._participant_detector is None:
            self._participant_detector = ParticipantDetector(gpu=self.use_gpu)
        return self._participant_detector

    def process_video(self,
                     video_path: str,
                     progress_callback: Optional[Callable[[str, int, int], None]] = None
                     ) -> VideoAnnotation:
        BatchOptimiser.log_hardware_info()

        metadata_result = get_video_metadata(video_path)
        if metadata_result.is_err():
            error = metadata_result.unwrap_err()
            raise ProcessingError(
                f"Failed to read video metadata: {error.message}",
                details=error.details
            )

        metadata = metadata_result.unwrap()
        fps = metadata.fps
        frame_count = metadata.frame_count
        duration = metadata.duration

        annotation = VideoAnnotation(
            video_path=video_path,
            duration=duration,
            fps=fps,
            frame_count=frame_count,
            processed=False
        )

        task_batch_size = BatchOptimiser.calculate_task_classifier_batch_size(use_gpu=self.use_gpu)

        if progress_callback:
            progress_callback("Analysing tasks", 0, 100)

        frame_results = self.task_classifier.process_video(
            video_path,
            sample_every=self.sample_every,
            smoothing_window=self.smoothing_window,
            min_duration_sec=self.min_duration_sec,
            batch_size=task_batch_size,
        )

        time_ranges = self.task_classifier.aggregate_time_ranges(frame_results)

        annotation.task_segments = [
            TaskSegment(
                task_name=seg['task'],
                start_time=self._parse_timestamp(seg['start']),
                end_time=self._parse_timestamp(seg['end']),
                confidence=seg['avg_conf']
            )
            for seg in time_ranges
        ]

        if progress_callback:
            progress_callback("Detecting participants", 50, 100)

        def participant_progress(current, total):
            if progress_callback:
                progress = 50 + int((current / total) * 50)  # 50-100% for participant detection
                progress_callback("Detecting participants", progress, 100)

        detections = self.participant_detector.process_video(
            video_path,
            progress_callback=participant_progress
        )

        annotation.participant_markers = [
            ParticipantMarker(
                participant_type=det['participant_type'],
                participant_number=det['participant_number'],
                timestamp=det['timestamp'],
                duration=det['duration'],
                confidence=det['confidence']
            )
            for det in detections
        ]

        annotation.processed = True

        if progress_callback:
            progress_callback("Complete", 100, 100)

        return annotation

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> float:
        try:
            parts = timestamp_str.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid timestamp format: {timestamp_str}")

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])

            if hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError(f"Negative values in timestamp: {timestamp_str}")

            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse timestamp '{timestamp_str}': {e}")
