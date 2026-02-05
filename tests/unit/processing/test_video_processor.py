"""
Unit tests for app/processing/video_processor.py - VideoProcessor
"""

import pytest
from unittest.mock import patch, MagicMock

from app.processing.video_processor import VideoProcessor


class TestParseTimestamp:

    def test_simple_timestamp(self):
        assert VideoProcessor._parse_timestamp('00:01:30') == 90.0

    def test_zero_timestamp(self):
        assert VideoProcessor._parse_timestamp('00:00:00') == 0.0

    def test_hours(self):
        assert VideoProcessor._parse_timestamp('01:00:00') == 3600.0

    def test_fractional_seconds(self):
        result = VideoProcessor._parse_timestamp('00:00:30.5')
        assert abs(result - 30.5) < 0.001

    def test_combined(self):
        result = VideoProcessor._parse_timestamp('02:30:45')
        assert result == 2 * 3600 + 30 * 60 + 45

    def test_invalid_format_too_few_parts(self):
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            VideoProcessor._parse_timestamp('01:30')

    def test_invalid_format_too_many_parts(self):
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            VideoProcessor._parse_timestamp('01:02:03:04')

    def test_negative_values(self):
        with pytest.raises(ValueError, match="Negative values"):
            VideoProcessor._parse_timestamp('-01:00:00')

    def test_non_numeric(self):
        with pytest.raises(ValueError, match="Failed to parse"):
            VideoProcessor._parse_timestamp('ab:cd:ef')


class TestVideoProcessorInit:

    def test_default_params(self):
        proc = VideoProcessor()
        assert proc.use_gpu is True
        assert proc.sample_every == 30
        assert proc.smoothing_window == 15
        assert proc.min_duration_sec == 5

    def test_custom_params(self):
        proc = VideoProcessor(use_gpu=False, sample_every=10, smoothing_window=5, min_duration_sec=3)
        assert proc.use_gpu is False
        assert proc.sample_every == 10
        assert proc.smoothing_window == 5
        assert proc.min_duration_sec == 3

    def test_lazy_classifier(self):
        proc = VideoProcessor()
        assert proc._task_classifier is None

    def test_lazy_detector(self):
        proc = VideoProcessor()
        assert proc._participant_detector is None

    @patch('app.processing.video_processor.TaskClassifier')
    def test_task_classifier_property(self, mock_cls):
        """Lines 37-39: lazy-loads TaskClassifier"""
        mock_cls.return_value = MagicMock()
        proc = VideoProcessor()
        tc = proc.task_classifier
        assert tc is not None
        # Second access should return same instance
        assert proc.task_classifier is tc

    @patch('app.processing.video_processor.ParticipantDetector')
    def test_participant_detector_property(self, mock_cls):
        """Lines 43-45: lazy-loads ParticipantDetector"""
        mock_cls.return_value = MagicMock()
        proc = VideoProcessor()
        pd = proc.participant_detector
        assert pd is not None
        assert proc.participant_detector is pd


class TestProcessVideo:

    @patch('app.processing.video_processor.BatchOptimiser')
    @patch('app.processing.video_processor.get_video_metadata')
    def test_process_video_metadata_error(self, mock_meta, mock_batch):
        """process_video raises on metadata error"""
        from app.domain.result import Err
        from app.utils.error_handling import VideoError, ProcessingError
        mock_meta.return_value = Err(VideoError("bad"))

        proc = VideoProcessor()
        with pytest.raises(ProcessingError):
            proc.process_video('/test.mp4')

    @patch('app.processing.video_processor.BatchOptimiser')
    @patch('app.processing.video_processor.get_video_metadata')
    def test_process_video_full(self, mock_meta, mock_batch):
        """Lines 51-128: full orchestration of process_video"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata

        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=900, width=1920, height=1080, duration=30.0))
        mock_batch.log_hardware_info = MagicMock()
        mock_batch.calculate_task_classifier_batch_size.return_value = 32

        proc = VideoProcessor(use_gpu=False)

        # Mock task_classifier
        mock_tc = MagicMock()
        mock_tc.process_video.return_value = [{'frame': 1, 'pred': 'Suture'}]
        mock_tc.aggregate_time_ranges.return_value = [
            {'task': 'Suture', 'start': '00:00:00', 'end': '00:00:30', 'avg_conf': 0.9}
        ]
        proc._task_classifier = mock_tc

        # Mock participant_detector
        mock_pd = MagicMock()
        mock_pd.process_video.return_value = [
            {'participant_type': 'P', 'participant_number': 1, 'timestamp': 5.0, 'duration': 2.0, 'confidence': 0.9}
        ]
        proc._participant_detector = mock_pd

        callback = MagicMock()
        annotation = proc.process_video('/test.mp4', progress_callback=callback)

        assert annotation.processed is True
        assert len(annotation.task_segments) == 1
        assert annotation.task_segments[0].task_name == 'Suture'
        assert len(annotation.participant_markers) == 1
        assert callback.call_count >= 3  # At least: Analysing tasks, Detecting, Complete

    @patch('app.processing.video_processor.BatchOptimiser')
    @patch('app.processing.video_processor.get_video_metadata')
    def test_process_video_no_callback(self, mock_meta, mock_batch):
        """process_video works without progress callback"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata

        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=900, width=1920, height=1080, duration=30.0))
        mock_batch.calculate_task_classifier_batch_size.return_value = 32

        proc = VideoProcessor()
        proc._task_classifier = MagicMock()
        proc._task_classifier.process_video.return_value = []
        proc._task_classifier.aggregate_time_ranges.return_value = []
        proc._participant_detector = MagicMock()
        proc._participant_detector.process_video.return_value = []

        annotation = proc.process_video('/test.mp4')
        assert annotation.processed is True

    @patch('app.processing.video_processor.BatchOptimiser')
    @patch('app.processing.video_processor.get_video_metadata')
    def test_participant_progress_callback(self, mock_meta, mock_batch):
        """Lines 103-105: participant_progress closure calls outer callback"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata

        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=900, width=1920, height=1080, duration=30.0))
        mock_batch.calculate_task_classifier_batch_size.return_value = 32

        proc = VideoProcessor(use_gpu=False)
        proc._task_classifier = MagicMock()
        proc._task_classifier.process_video.return_value = []
        proc._task_classifier.aggregate_time_ranges.return_value = []

        # Capture what participant_detector.process_video receives as progress_callback
        captured_cb = [None]
        def capture_process_video(video_path, progress_callback=None, **kwargs):
            captured_cb[0] = progress_callback
            # Invoke the callback to trigger the participant_progress closure
            if progress_callback:
                progress_callback(25, 50)
            return []

        proc._participant_detector = MagicMock()
        proc._participant_detector.process_video.side_effect = capture_process_video

        outer_calls = []
        def outer_callback(stage, current, total):
            outer_calls.append((stage, current, total))

        proc.process_video('/test.mp4', progress_callback=outer_callback)
        # The participant_progress(25,50) should produce 50 + int(25/50*50) = 75
        assert any(c[1] == 75 for c in outer_calls)
