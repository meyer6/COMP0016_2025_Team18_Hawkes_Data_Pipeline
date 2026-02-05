"""
Unit tests for app/utils/video_exporter.py - VideoExporter
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.utils.video_exporter import VideoExporter
from app.models.annotation import VideoAnnotation, TaskSegment, ParticipantMarker


class TestVideoExporter:

    @pytest.fixture
    def exporter(self, temp_dir, sample_annotation):
        return VideoExporter(
            video_path=sample_annotation.video_path,
            annotation=sample_annotation,
            output_dir=str(temp_dir / 'exports')
        )

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_all_segments_skips_idle(self, mock_run, exporter):
        mock_run.return_value = MagicMock(returncode=0)
        # Make output files appear to exist after "ffmpeg" runs
        original_export = exporter._export_segment

        def fake_export(segment, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return True

        exporter._export_segment = fake_export
        files = exporter.export_all_segments()
        # sample_annotation has 4 segments: Suture, Idle, ChickenThigh, GloveCut
        # Idle is skipped -> 3 segments exported
        assert len(files) == 3

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_segment_success(self, mock_run, exporter, temp_dir):
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'exports' / 'Suture' / 'test.mp4'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Simulate ffmpeg creating the file
        output_path.touch()

        segment = TaskSegment(task_name='Suture', start_time=0, end_time=10)
        result = exporter._export_segment(segment, output_path)
        assert result is True

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_segment_ffmpeg_failure(self, mock_run, exporter, temp_dir):
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='error')
        output_path = temp_dir / 'out.mp4'

        segment = TaskSegment(task_name='Suture', start_time=0, end_time=10)
        result = exporter._export_segment(segment, output_path)
        assert result is False

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_segment_timeout(self, mock_run, exporter, temp_dir):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='ffmpeg', timeout=60)
        output_path = temp_dir / 'out.mp4'

        segment = TaskSegment(task_name='Suture', start_time=0, end_time=10)
        result = exporter._export_segment(segment, output_path)
        assert result is False

    def test_export_segment_invalid_duration(self, exporter, temp_dir):
        output_path = temp_dir / 'out.mp4'
        segment = TaskSegment(task_name='Suture', start_time=10, end_time=5)  # negative duration
        result = exporter._export_segment(segment, output_path)
        assert result is False

    def test_export_empty_annotation(self, temp_dir):
        annotation = VideoAnnotation(video_path='/test.mp4')
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir))
        files = exporter.export_all_segments()
        assert files == []

    def test_export_all_idle(self, temp_dir):
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Idle', start_time=0, end_time=30),
        ]
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir))
        files = exporter.export_all_segments()
        assert files == []

    @patch('app.utils.video_exporter.subprocess.run')
    def test_progress_callback(self, mock_run, exporter):
        mock_run.return_value = MagicMock(returncode=0)
        exporter._export_segment = MagicMock(return_value=True)

        callback = MagicMock()
        exporter.export_all_segments(progress_callback=callback)
        assert callback.call_count >= 1

    def test_export_with_participant_labels(self, temp_dir):
        """Line 40: participant_label is resolved from annotation"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=10, end_time=20),
            TaskSegment(task_name='Suture', start_time=25, end_time=35),
        ]
        annotation.participant_markers = [
            ParticipantMarker(participant_type='P', participant_number=1, timestamp=5.0),
        ]
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir / 'exports'))

        def fake_export(segment, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return True

        exporter._export_segment = fake_export
        files = exporter.export_all_segments()
        assert len(files) == 2
        # Both should use P1 label; second should get index 2
        assert 'P1_1' in files[0]
        assert 'P1_2' in files[1]

    def test_export_segment_failure_logged(self, temp_dir, sample_annotation):
        """Line 78: failed export logged"""
        exporter = VideoExporter(sample_annotation.video_path, sample_annotation, str(temp_dir / 'exports'))

        def failing_export(segment, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            return False

        exporter._export_segment = failing_export
        files = exporter.export_all_segments()
        assert len(files) == 0

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_segment_output_not_created(self, mock_run, exporter, temp_dir):
        """Lines 122-123: ffmpeg returns 0 but output file doesn't exist"""
        mock_run.return_value = MagicMock(returncode=0)
        output_path = temp_dir / 'exports' / 'Suture' / 'missing.mp4'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Don't create the file

        segment = TaskSegment(task_name='Suture', start_time=0, end_time=10)
        result = exporter._export_segment(segment, output_path)
        assert result is False

    @patch('app.utils.video_exporter.subprocess.run')
    def test_export_segment_generic_exception(self, mock_run, exporter, temp_dir):
        """Lines 131-133: generic exception in _export_segment"""
        mock_run.side_effect = RuntimeError("unexpected")
        output_path = temp_dir / 'out.mp4'

        segment = TaskSegment(task_name='Suture', start_time=0, end_time=10)
        result = exporter._export_segment(segment, output_path)
        assert result is False

    def test_export_no_participant_marker(self, temp_dir):
        """Line 40: participant_label fallback to 'None'"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=10, end_time=20),
        ]
        # No participant_markers -> get_participant_for_task returns None -> "None" label
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir / 'exports'))

        def fake_export(segment, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return True

        exporter._export_segment = fake_export
        files = exporter.export_all_segments()
        assert len(files) == 1
        assert 'None' in files[0]

    def test_export_filename_collision(self, temp_dir):
        """Lines 62-63: existing file on disk increments index"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=10, end_time=20),
        ]
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir / 'exports'))

        # Pre-create the file that would be generated first
        task_dir = temp_dir / 'exports' / 'Suture'
        task_dir.mkdir(parents=True)
        (task_dir / 'Suture_None_1.mp4').touch()

        def fake_export(segment, output_path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return True

        exporter._export_segment = fake_export
        files = exporter.export_all_segments()
        assert len(files) == 1
        # Should have used index 2 since 1 already existed
        assert 'None_2' in files[0]

    def test_export_max_retries_exceeded(self, temp_dir):
        """Lines 65-67: MAX_RETRIES exceeded skips segment"""
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=10, end_time=20),
        ]
        exporter = VideoExporter('/test.mp4', annotation, str(temp_dir / 'exports'))

        # Make every possible filename appear to exist
        with patch.object(Path, 'exists', return_value=True):
            def fake_export(segment, output_path):
                return True
            exporter._export_segment = fake_export
            files = exporter.export_all_segments()
            assert len(files) == 0  # Segment skipped
