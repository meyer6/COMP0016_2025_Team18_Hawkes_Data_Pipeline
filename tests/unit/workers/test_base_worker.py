"""
Unit tests for app/workers/base_worker.py - BaseWorker
"""

import pytest

from app.workers.base_worker import BaseWorker


@pytest.mark.pyqt
class TestBaseWorker:

    def test_cancel_sets_flag(self, qapp):
        worker = BaseWorker()
        assert worker.is_cancelled() is False
        worker.cancel()
        assert worker.is_cancelled() is True

    def test_emit_progress_raises_when_cancelled(self, qapp):
        worker = BaseWorker()
        worker.cancel()
        with pytest.raises(InterruptedError):
            worker.emit_progress("test", 1, 10)

    def test_do_work_not_implemented(self, qapp):
        worker = BaseWorker()
        with pytest.raises(NotImplementedError):
            worker.do_work()

    def test_emit_progress_emits_signal(self, qapp):
        worker = BaseWorker()
        received = []
        worker.progress_update.connect(lambda s, c, t: received.append((s, c, t)))
        worker.emit_progress("stage", 5, 10)
        assert len(received) == 1
        assert received[0] == ("stage", 5, 10)

    def test_run_success(self, qapp):
        """Lines 41-50: run() completes successfully"""
        class SuccessWorker(BaseWorker):
            def do_work(self):
                pass
        worker = SuccessWorker()
        worker.run()
        assert not worker.is_cancelled()

    def test_run_cancelled_during_work(self, qapp):
        """Lines 46-48: run() detects cancellation after do_work"""
        class CancelWorker(BaseWorker):
            def do_work(self_inner):
                self_inner.cancel()
            def _handle_cancelled(self_inner):
                self_inner.cancelled_called = True
        worker = CancelWorker()
        worker.cancelled_called = False
        worker.run()
        assert worker.cancelled_called

    def test_run_interrupted_error(self, qapp):
        """Lines 52-54: run() handles InterruptedError"""
        class InterruptWorker(BaseWorker):
            def do_work(self_inner):
                raise InterruptedError("interrupted")
            def _handle_cancelled(self_inner):
                self_inner.cancelled_called = True
        worker = InterruptWorker()
        worker.cancelled_called = False
        worker.run()
        assert worker.cancelled_called

    def test_run_exception_not_cancelled(self, qapp):
        """Lines 56-61: run() handles exception when not cancelled"""
        class ErrorWorker(BaseWorker):
            def do_work(self_inner):
                raise RuntimeError("boom")
        worker = ErrorWorker()
        errors = []
        worker.error_occurred.connect(lambda msg, exc: errors.append(msg))
        worker.run()
        assert len(errors) == 1

    def test_run_exception_when_cancelled(self, qapp):
        """Lines 58-59: exception but cancelled flag is set"""
        class ErrorCancelWorker(BaseWorker):
            def do_work(self_inner):
                self_inner.cancel()
                raise RuntimeError("boom")
            def _handle_cancelled(self_inner):
                self_inner.cancelled_called = True
        worker = ErrorCancelWorker()
        worker.cancelled_called = False
        worker.run()
        assert worker.cancelled_called

    def test_handle_error_default(self, qapp):
        """Line 64: default _handle_error emits error_occurred"""
        worker = BaseWorker()
        errors = []
        worker.error_occurred.connect(lambda msg, exc: errors.append((msg, exc)))
        err = RuntimeError("test")
        worker._handle_error(err)
        assert len(errors) == 1
        assert errors[0][1] is err

    def test_handle_cancelled_default(self, qapp):
        """Line 67: default _handle_cancelled is no-op"""
        worker = BaseWorker()
        worker._handle_cancelled()  # Should not raise
