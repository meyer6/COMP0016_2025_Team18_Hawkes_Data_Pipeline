"""
Unit tests for app/utils/error_handling.py - Exception hierarchy and ErrorContext
"""

import pytest

from app.utils.error_handling import (
    AppError, VideoError, VideoNotFoundError, VideoReadError, VideoCorruptedError,
    ProcessingError, ModelError, TaskClassificationError, ParticipantDetectionError,
    ExportError, AnnotationError, AnnotationNotFoundError, AnnotationParseError,
    ConfigurationError, ValidationError, ErrorContext
)


class TestAppError:

    def test_message_only(self):
        err = AppError("something failed")
        assert err.message == "something failed"
        assert err.details is None
        assert str(err) == "something failed"

    def test_message_with_details(self):
        err = AppError("failed", details="more info")
        assert "Details: more info" in str(err)

    def test_is_exception(self):
        assert issubclass(AppError, Exception)


class TestVideoError:

    def test_video_path_attribute(self):
        err = VideoError("bad video", video_path='/test.mp4')
        assert err.video_path == '/test.mp4'
        assert err.message == "bad video"

    def test_subclass_not_found(self):
        err = VideoNotFoundError("not found", video_path='/x.mp4')
        assert isinstance(err, VideoError)
        assert isinstance(err, AppError)

    def test_subclass_read_error(self):
        err = VideoReadError("cant read", video_path='/x.mp4', details="corrupted codec")
        assert err.details == "corrupted codec"

    def test_subclass_corrupted(self):
        err = VideoCorruptedError("corrupt", video_path='/x.mp4')
        assert isinstance(err, VideoError)


class TestProcessingError:

    def test_stage_attribute(self):
        err = ProcessingError("failed", stage="classification")
        assert err.stage == "classification"

    def test_model_error(self):
        err = ModelError("model load failed", stage="init")
        assert isinstance(err, ProcessingError)
        assert isinstance(err, AppError)

    def test_task_classification_error(self):
        err = TaskClassificationError("bad prediction")
        assert isinstance(err, ProcessingError)

    def test_participant_detection_error(self):
        err = ParticipantDetectionError("OCR failed")
        assert isinstance(err, ProcessingError)


class TestExportError:

    def test_output_path(self):
        err = ExportError("export failed", output_path='/output')
        assert err.output_path == '/output'
        assert isinstance(err, AppError)


class TestAnnotationError:

    def test_annotation_path(self):
        err = AnnotationError("parse failed", annotation_path='/ann.json')
        assert err.annotation_path == '/ann.json'

    def test_not_found_subclass(self):
        err = AnnotationNotFoundError("missing")
        assert isinstance(err, AnnotationError)

    def test_parse_error_subclass(self):
        err = AnnotationParseError("bad json")
        assert isinstance(err, AnnotationError)


class TestConfigAndValidationError:

    def test_configuration_error(self):
        err = ConfigurationError("bad config")
        assert isinstance(err, AppError)

    def test_validation_error(self):
        err = ValidationError("invalid input")
        assert isinstance(err, AppError)


class TestErrorContext:

    def test_success_path(self, mock_logger):
        with ErrorContext(mock_logger, "test operation"):
            pass
        mock_logger.debug.assert_any_call("Starting: test operation")
        mock_logger.debug.assert_any_call("Completed: test operation")

    def test_app_error_reraise(self, mock_logger):
        with pytest.raises(AppError):
            with ErrorContext(mock_logger, "test"):
                raise AppError("boom")

    def test_app_error_suppressed(self, mock_logger):
        ctx = ErrorContext(mock_logger, "test", raise_on_error=False)
        with ctx:
            raise AppError("boom", details="detail")
        assert ctx.error is not None
        assert isinstance(ctx.error, AppError)

    def test_unexpected_error_reraise(self, mock_logger):
        with pytest.raises(RuntimeError):
            with ErrorContext(mock_logger, "test"):
                raise RuntimeError("unexpected")

    def test_unexpected_error_suppressed(self, mock_logger):
        ctx = ErrorContext(mock_logger, "test", raise_on_error=False)
        with ctx:
            raise RuntimeError("unexpected")
        assert isinstance(ctx.error, RuntimeError)
