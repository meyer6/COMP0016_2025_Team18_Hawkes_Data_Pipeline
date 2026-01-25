"""
Background worker thread for video export
"""

import logging
from PyQt6.QtCore import pyqtSignal
from .base_worker import BaseWorker
from ..utils.video_exporter import VideoExporter
from ..models.annotation import VideoAnnotation

logger = logging.getLogger(__name__)


class ExportWorker(BaseWorker):
    """Worker thread for exporting video clips in background"""

    export_complete = pyqtSignal(list)
    export_error = pyqtSignal(str)

    def __init__(self, video_path: str, annotation: VideoAnnotation, output_dir: str):
        super().__init__()
        self.video_path = video_path
        self.annotation = annotation
        self.output_dir = output_dir

    def do_work(self):
        exporter = VideoExporter(self.video_path, self.annotation, self.output_dir)

        exported_files = exporter.export_all_segments(
            progress_callback=self._on_progress
        )

        self.export_complete.emit(exported_files)

    def _handle_error(self, error: Exception):
        self.export_error.emit(str(error))

    def _on_progress(self, current: int, total: int, message: str):
        if self.is_cancelled():
            raise InterruptedError("Export cancelled")
        self.progress_update.emit(message, current, total)
