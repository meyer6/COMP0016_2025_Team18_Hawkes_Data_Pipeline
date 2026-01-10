"""Main video processor - task classification only (participant detection TODO)"""

import logging
from typing import Callable, Optional

from ..models.annotation import VideoAnnotation, TaskSegment
from .task_classifier import TaskClassifier
from .batch_optimiser import BatchOptimiser
from .base.processor_base import ProcessorBase
from ..infrastructure.video_utils import get_video_metadata
from ..utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)


class VideoProcessor(ProcessorBase):
    """Orchestrates video processing - currently task classification only"""

    def __init__(self, use_gpu=True, sample_every=30, smoothing_window=15, min_duration_sec=5):
        self.use_gpu = use_gpu
        self.sample_every = sample_every
        self.smoothing_window = smoothing_window
        self.min_duration_sec = min_duration_sec
        self._task_classifier = None

    @property
    def task_classifier(self):
        if self._task_classifier is None:
            self._task_classifier = TaskClassifier()
        return self._task_classifier

    def process_video(self, video_path, progress_callback=None):
        BatchOptimiser.log_hardware_info()
        metadata_result = get_video_metadata(video_path)
        if metadata_result.is_err():
            error = metadata_result.unwrap_err()
            raise ProcessingError(f"Failed to read video metadata: {error.message}", details=error.details)

        metadata = metadata_result.unwrap()
        annotation = VideoAnnotation(
            video_path=video_path, duration=metadata.duration,
            fps=metadata.fps, frame_count=metadata.frame_count, processed=False
        )

        batch_size = BatchOptimiser.calculate_task_classifier_batch_size(use_gpu=self.use_gpu)

        if progress_callback:
            progress_callback("Analysing tasks", 0, 100)

        frame_results = self.task_classifier.process_video(
            video_path, sample_every=self.sample_every,
            smoothing_window=self.smoothing_window,
            min_duration_sec=self.min_duration_sec, batch_size=batch_size,
        )
        time_ranges = self.task_classifier.aggregate_time_ranges(frame_results)
        annotation.task_segments = [
            TaskSegment(task_name=seg['task'], start_time=self._parse_timestamp(seg['start']),
                        end_time=self._parse_timestamp(seg['end']), confidence=seg['avg_conf'])
            for seg in time_ranges
        ]

        # TODO: add participant detection here

        annotation.processed = True
        if progress_callback:
            progress_callback("Complete", 100, 100)
        return annotation

    @staticmethod
    def _parse_timestamp(ts):
        try:
            parts = ts.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid timestamp: {ts}")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse timestamp '{ts}': {e}")
