"""
Unit tests for app/infrastructure/video_utils.py
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from app.infrastructure.video_utils import (
    format_duration, VideoMetadata, open_video_capture,
    get_video_metadata, extract_frame, get_middle_frame
)
from app.domain.result import Ok, Err
from app.utils.error_handling import VideoNotFoundError, VideoReadError, VideoCorruptedError


class TestFormatDuration:

    def test_zero_seconds(self):
        assert format_duration(0) == '00:00:00'

    def test_seconds_only(self):
        assert format_duration(45) == '00:00:45'

    def test_minutes_and_seconds(self):
        assert format_duration(125) == '00:02:05'

    def test_hours(self):
        assert format_duration(3661) == '01:01:01'

    def test_large_value(self):
        assert format_duration(86400) == '24:00:00'


class TestVideoMetadata:

    def test_duration_str(self):
        meta = VideoMetadata(fps=30.0, frame_count=900, width=1920, height=1080, duration=30.0)
        assert meta.duration_str == '00:00:30'

    def test_properties(self):
        meta = VideoMetadata(fps=24.0, frame_count=2400, width=1280, height=720, duration=100.0)
        assert meta.fps == 24.0
        assert meta.width == 1280


class TestOpenVideoCapture:

    def test_file_not_found(self, temp_dir):
        result = open_video_capture(str(temp_dir / 'missing.mp4'))
        assert result.is_err()
        assert isinstance(result.unwrap_err(), VideoNotFoundError)

    @patch('app.infrastructure.video_utils.cv2.VideoCapture')
    def test_cannot_open(self, mock_cap_class, temp_dir):
        video_file = temp_dir / 'bad.mp4'
        video_file.touch()

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_class.return_value = mock_cap

        result = open_video_capture(str(video_file))
        assert result.is_err()
        assert isinstance(result.unwrap_err(), VideoReadError)

    @patch('app.infrastructure.video_utils.cv2.VideoCapture')
    def test_success(self, mock_cap_class, temp_dir):
        video_file = temp_dir / 'good.mp4'
        video_file.touch()

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap_class.return_value = mock_cap

        result = open_video_capture(str(video_file))
        assert result.is_ok()


class TestGetVideoMetadata:

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_success(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.side_effect = lambda prop: {
            0: 30.0,    # CAP_PROP_POS_MSEC (not used directly)
            3: 1920.0,  # CAP_PROP_FRAME_WIDTH
            4: 1080.0,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,    # CAP_PROP_FPS
            7: 900.0,   # CAP_PROP_FRAME_COUNT
        }.get(prop, 0.0)
        mock_open.return_value = Ok(mock_cap)

        result = get_video_metadata('/test.mp4')
        assert result.is_ok()
        meta = result.unwrap()
        assert meta.fps == 30.0
        assert meta.frame_count == 900

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_invalid_metadata(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.return_value = 0.0  # fps=0, frame_count=0
        mock_open.return_value = Ok(mock_cap)

        result = get_video_metadata('/test.mp4')
        assert result.is_err()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_open_fails(self, mock_open):
        mock_open.return_value = Err(VideoNotFoundError("not found", video_path='/test.mp4'))
        result = get_video_metadata('/test.mp4')
        assert result.is_err()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_exception_in_metadata(self, mock_open):
        """Lines 100-107: general exception reading metadata"""
        mock_cap = MagicMock()
        mock_cap.get.side_effect = RuntimeError("segfault")
        mock_open.return_value = Ok(mock_cap)

        result = get_video_metadata('/test.mp4')
        assert result.is_err()
        mock_cap.release.assert_called_once()


class TestExtractFrame:

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_open_fails(self, mock_open):
        mock_open.return_value = Err(VideoNotFoundError("missing", video_path='/test.mp4'))
        result = extract_frame('/test.mp4', 0)
        assert result.is_err()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_success(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.read.return_value = (True, MagicMock())
        mock_open.return_value = Ok(mock_cap)

        result = extract_frame('/test.mp4', 50)
        assert result.is_ok()
        success, frame = result.unwrap()
        assert success is True
        mock_cap.release.assert_called_once()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_read_fails(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.read.return_value = (False, None)
        mock_open.return_value = Ok(mock_cap)

        result = extract_frame('/test.mp4', 50)
        assert result.is_ok()
        success, frame = result.unwrap()
        assert success is False

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_exception(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.set.side_effect = RuntimeError("boom")
        mock_open.return_value = Ok(mock_cap)

        result = extract_frame('/test.mp4', 50)
        assert result.is_err()
        mock_cap.release.assert_called_once()


class TestGetMiddleFrame:

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_open_fails(self, mock_open):
        mock_open.return_value = Err(VideoNotFoundError("missing", video_path='/test.mp4'))
        result = get_middle_frame('/test.mp4')
        assert result.is_err()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_no_frames(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.return_value = 0
        mock_open.return_value = Ok(mock_cap)

        result = get_middle_frame('/test.mp4')
        assert result.is_err()
        mock_cap.release.assert_called_once()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_success(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.return_value = 100
        mock_cap.read.return_value = (True, MagicMock())
        mock_open.return_value = Ok(mock_cap)

        result = get_middle_frame('/test.mp4')
        assert result.is_ok()
        success, frame = result.unwrap()
        assert success is True
        mock_cap.release.assert_called_once()

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_read_fails(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.return_value = 100
        mock_cap.read.return_value = (False, None)
        mock_open.return_value = Ok(mock_cap)

        result = get_middle_frame('/test.mp4')
        assert result.is_ok()
        success, _ = result.unwrap()
        assert success is False

    @patch('app.infrastructure.video_utils.open_video_capture')
    def test_exception(self, mock_open):
        mock_cap = MagicMock()
        mock_cap.get.side_effect = RuntimeError("boom")
        mock_open.return_value = Ok(mock_cap)

        result = get_middle_frame('/test.mp4')
        assert result.is_err()
        mock_cap.release.assert_called_once()
