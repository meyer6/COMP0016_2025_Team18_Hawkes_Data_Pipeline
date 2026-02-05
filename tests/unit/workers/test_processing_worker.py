"""
Unit tests for app/workers/processing_worker.py - ProcessingWorker
"""

import pytest
from unittest.mock import patch, MagicMock

from app.workers.processing_worker import ProcessingWorker


@pytest.mark.pyqt
class TestProcessingWorker:

    def test_init_stores_params(self, qapp):
        worker = ProcessingWorker(
            video_path='/test.mp4',
            use_gpu=False,
            sample_every=10,
            smoothing_window=5,
            min_duration_sec=3
        )
        assert worker.video_path == '/test.mp4'
        assert worker.use_gpu is False
        assert worker.sample_every == 10
        assert worker.smoothing_window == 5
        assert worker.min_duration_sec == 3

    def test_error_signal_emission(self, qapp):
        worker = ProcessingWorker(video_path='/test.mp4')
        errors = []
        worker.processing_error.connect(lambda msg: errors.append(msg))
        worker._handle_error(RuntimeError("test error"))
        assert len(errors) == 1
        assert "test error" in errors[0]

    def test_cancelled_signal_emission(self, qapp):
        worker = ProcessingWorker(video_path='/test.mp4')
        cancelled = []
        worker.processing_cancelled.connect(lambda: cancelled.append(True))
        worker._handle_cancelled()
        assert len(cancelled) == 1

    @patch('app.workers.processing_worker.VideoProcessor')
    def test_do_work(self, mock_vp_cls, qapp):
        """Lines 32-47: do_work creates processor and processes video"""
        from app.models.annotation import VideoAnnotation
        mock_processor = MagicMock()
        mock_annotation = VideoAnnotation(video_path='/test.mp4')
        mock_processor.process_video.return_value = mock_annotation
        mock_vp_cls.return_value = mock_processor

        worker = ProcessingWorker(video_path='/test.mp4', use_gpu=False)
        results = []
        worker.processing_complete.connect(lambda ann: results.append(ann))
        worker.do_work()
        assert len(results) == 1

    @patch('app.workers.processing_worker.VideoProcessor')
    def test_do_work_cancelled(self, mock_vp_cls, qapp):
        """Line 45: do_work when cancelled during processing"""
        mock_processor = MagicMock()
        from app.models.annotation import VideoAnnotation
        mock_processor.process_video.return_value = VideoAnnotation(video_path='/test.mp4')
        mock_vp_cls.return_value = mock_processor

        worker = ProcessingWorker(video_path='/test.mp4', use_gpu=False)
        worker.cancel()  # Set cancelled before emit
        results = []
        worker.processing_complete.connect(lambda ann: results.append(ann))
        worker.do_work()
        # Should NOT emit processing_complete because cancelled
        assert len(results) == 0

    def test_on_progress(self, qapp):
        """Line 56: _on_progress delegates to emit_progress"""
        worker = ProcessingWorker(video_path='/test.mp4')
        received = []
        worker.progress_update.connect(lambda s, c, t: received.append((s, c, t)))
        worker._on_progress("stage", 5, 10)
        assert received == [("stage", 5, 10)]
