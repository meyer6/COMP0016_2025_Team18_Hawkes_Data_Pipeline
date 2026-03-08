"""
Unit tests for app/workers/concat_worker.py - ConcatWorker
"""

import pytest
from unittest.mock import patch, MagicMock

from app.workers.concat_worker import ConcatWorker
from app.domain import Ok, Err
from app.utils.error_handling import VideoError


@pytest.mark.pyqt
class TestConcatWorker:

    def test_init_stores_params(self, qapp):
        worker = ConcatWorker(['/a.avi', '/b.avi'], '/out.avi')
        assert worker.part_paths == ['/a.avi', '/b.avi']
        assert worker.output_path == '/out.avi'

    @patch('app.workers.concat_worker.concatenate_parts')
    def test_do_work_success(self, mock_concat, qapp):
        mock_concat.return_value = Ok('/out.avi')
        worker = ConcatWorker(['/a.avi'], '/out.avi')
        results = []
        worker.concat_complete.connect(lambda path: results.append(path))

        worker.do_work()

        assert len(results) == 1
        assert results[0] == '/out.avi'

    @patch('app.workers.concat_worker.concatenate_parts')
    def test_do_work_error(self, mock_concat, qapp):
        mock_concat.return_value = Err(VideoError("concat failed"))
        worker = ConcatWorker(['/a.avi'], '/out.avi')
        errors = []
        worker.concat_error.connect(lambda msg: errors.append(msg))

        worker.do_work()

        assert len(errors) == 1
        assert "concat failed" in errors[0]

    @patch('app.workers.concat_worker.concatenate_parts')
    def test_do_work_cancelled(self, mock_concat, qapp):
        mock_concat.return_value = Ok('/out.avi')
        worker = ConcatWorker(['/a.avi'], '/out.avi')
        worker.cancel()

        results = []
        errors = []
        worker.concat_complete.connect(lambda path: results.append(path))
        worker.concat_error.connect(lambda msg: errors.append(msg))

        worker.do_work()

        # Neither signal should fire when cancelled
        assert len(results) == 0
        assert len(errors) == 0

    def test_handle_error(self, qapp):
        worker = ConcatWorker(['/a.avi'], '/out.avi')
        errors = []
        worker.concat_error.connect(lambda msg: errors.append(msg))

        worker._handle_error(RuntimeError("unexpected"))

        assert len(errors) == 1
        assert "unexpected" in errors[0]

    def test_handle_cancelled(self, qapp):
        worker = ConcatWorker(['/a.avi'], '/out.avi')
        # Should not raise
        worker._handle_cancelled()
