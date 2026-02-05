"""
Unit tests for app/workers/export_worker.py - ExportWorker
"""

import pytest
from unittest.mock import patch, MagicMock

from app.workers.export_worker import ExportWorker
from app.models.annotation import VideoAnnotation


@pytest.mark.pyqt
class TestExportWorker:

    def test_init_stores_params(self, qapp):
        annotation = VideoAnnotation(video_path='/test.mp4')
        worker = ExportWorker(
            video_path='/test.mp4',
            annotation=annotation,
            output_dir='/output'
        )
        assert worker.video_path == '/test.mp4'
        assert worker.annotation is annotation
        assert worker.output_dir == '/output'

    def test_error_signal_emission(self, qapp):
        annotation = VideoAnnotation(video_path='/test.mp4')
        worker = ExportWorker('/test.mp4', annotation, '/output')
        errors = []
        worker.export_error.connect(lambda msg: errors.append(msg))
        worker._handle_error(RuntimeError("export failed"))
        assert len(errors) == 1
        assert "export failed" in errors[0]

    def test_complete_signal(self, qapp):
        annotation = VideoAnnotation(video_path='/test.mp4')
        worker = ExportWorker('/test.mp4', annotation, '/output')
        results = []
        worker.export_complete.connect(lambda files: results.append(files))
        worker.export_complete.emit(['file1.mp4', 'file2.mp4'])
        assert len(results) == 1
        assert results[0] == ['file1.mp4', 'file2.mp4']

    @patch('app.workers.export_worker.VideoExporter')
    def test_do_work(self, mock_exporter_cls, qapp):
        """Lines 27-33: do_work creates exporter and runs"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        mock_exporter = MagicMock()
        mock_exporter.export_all_segments.return_value = ['file1.mp4']
        mock_exporter_cls.return_value = mock_exporter

        worker = ExportWorker('/test.mp4', annotation, '/output')
        results = []
        worker.export_complete.connect(lambda files: results.append(files))
        worker.do_work()
        assert len(results) == 1
        assert results[0] == ['file1.mp4']

    def test_on_progress(self, qapp):
        """Lines 39-41: _on_progress checks cancellation and emits"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        worker = ExportWorker('/test.mp4', annotation, '/output')
        received = []
        worker.progress_update.connect(lambda s, c, t: received.append((s, c, t)))
        worker._on_progress(1, 10, "exporting")
        assert received == [("exporting", 1, 10)]

    def test_on_progress_cancelled(self, qapp):
        """Lines 39-40: _on_progress raises when cancelled"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        worker = ExportWorker('/test.mp4', annotation, '/output')
        worker.cancel()
        with pytest.raises(InterruptedError):
            worker._on_progress(1, 10, "exporting")
