"""
Background worker thread for video processing
"""

import logging
from PyQt6.QtCore import pyqtSignal
from .base_worker import BaseWorker
from ..processing.video_processor import VideoProcessor
from ..models.annotation import VideoAnnotation

logger = logging.getLogger(__name__)


class ProcessingWorker(BaseWorker):
    """Worker thread for processing videos in background"""

    processing_complete = pyqtSignal(VideoAnnotation)
    processing_error = pyqtSignal(str)
    processing_cancelled = pyqtSignal()

    def __init__(self, video_path: str, use_gpu: bool = True,
                 sample_every: int = 30, smoothing_window: int = 15,
                 min_duration_sec: int = 5):
        super().__init__()
        self.video_path = video_path
        self.use_gpu = use_gpu
        self.sample_every = sample_every
        self.smoothing_window = smoothing_window
        self.min_duration_sec = min_duration_sec

    def do_work(self):
        processor = VideoProcessor(
            use_gpu=self.use_gpu,
            sample_every=self.sample_every,
            smoothing_window=self.smoothing_window,
            min_duration_sec=self.min_duration_sec
        )

        annotation = processor.process_video(
            self.video_path,
            progress_callback=self._on_progress
        )

        if self.is_cancelled():
            return

        self.processing_complete.emit(annotation)

    def _handle_error(self, error: Exception):
        self.processing_error.emit(str(error))

    def _handle_cancelled(self):
        self.processing_cancelled.emit()

    def _on_progress(self, stage: str, current: int, total: int):
        self.emit_progress(stage, current, total)
