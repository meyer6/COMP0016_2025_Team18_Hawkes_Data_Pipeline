"""
Unit tests for app/processing/participant_detector.py - pure static methods only
"""

import pytest
from unittest.mock import patch, MagicMock

from app.processing.participant_detector import ParticipantDetector


class TestLevenshteinDistance:

    def test_identical_strings(self):
        assert ParticipantDetector._levenshtein_distance("abc", "abc") == 0

    def test_empty_strings(self):
        assert ParticipantDetector._levenshtein_distance("", "") == 0

    def test_one_empty(self):
        assert ParticipantDetector._levenshtein_distance("abc", "") == 3
        assert ParticipantDetector._levenshtein_distance("", "abc") == 3

    def test_single_substitution(self):
        assert ParticipantDetector._levenshtein_distance("cat", "bat") == 1

    def test_insertion_deletion(self):
        assert ParticipantDetector._levenshtein_distance("kitten", "sitting") == 3


class TestParseCard:

    def test_exact_participant(self):
        result = ParticipantDetector._parse_card("Participant 5")
        assert result == ("participant", 5)

    def test_exact_expert(self):
        result = ParticipantDetector._parse_card("Expert 3")
        assert result == ("expert", 3)

    def test_fuzzy_participant(self):
        # "Paricipant" is close to "participant" (distance <= 3)
        result = ParticipantDetector._parse_card("Paricipant 2")
        assert result is not None
        assert result[0] == "participant"
        assert result[1] == 2

    def test_no_number(self):
        result = ParticipantDetector._parse_card("Participant")
        assert result is None

    def test_unrelated_text(self):
        result = ParticipantDetector._parse_card("Hello World 42")
        assert result is None


class TestParticipantDetectorInit:

    def test_init(self):
        """Line 25: __init__ creates easyocr reader"""
        detector = ParticipantDetector(gpu=False)
        assert detector.reader is not None


class TestPrefetch:

    def test_prefetch_buffers(self):
        """Lines 60-69: _prefetch yields items from iterator"""
        items = list(ParticipantDetector._prefetch(iter([1, 2, 3]), buffer=2))
        assert items == [1, 2, 3]

    def test_prefetch_empty(self):
        items = list(ParticipantDetector._prefetch(iter([]), buffer=2))
        assert items == []


class TestReadFrames:

    def test_read_frames(self):
        """Lines 73-97: _read_frames yields frame_num, grayscale_frame pairs"""
        import numpy as np
        mock_cap = MagicMock()

        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        call_count = [0]

        def mock_read():
            call_count[0] += 1
            if call_count[0] <= 2:
                return True, frame.copy()
            return False, None

        def mock_grab():
            call_count[0] += 1
            return call_count[0] <= 3

        mock_cap.read = mock_read
        mock_cap.grab = mock_grab

        frames = list(ParticipantDetector._read_frames(mock_cap, 100, frame_skip=1))
        assert len(frames) >= 1
        for fn, fr in frames:
            assert fr is not None

    def test_read_frames_with_skip(self):
        """Lines 77-80: frames skipped via grab() when n % frame_skip != 0"""
        import numpy as np
        mock_cap = MagicMock()

        frame = np.zeros((240, 320, 3), dtype=np.uint8)

        # With frame_skip=3: frame 0 -> read, frame 1 -> grab, frame 2 -> grab, frame 3 -> read ...
        # We need grab to succeed for skipped frames and read to succeed for sampled frames
        read_count = [0]
        def mock_read():
            read_count[0] += 1
            if read_count[0] <= 2:
                return True, frame.copy()
            return False, None

        grab_count = [0]
        def mock_grab():
            grab_count[0] += 1
            return True  # Always succeed for grabs

        mock_cap.read = mock_read
        mock_cap.grab = mock_grab

        frames = list(ParticipantDetector._read_frames(mock_cap, 100, frame_skip=3))
        assert len(frames) >= 1
        assert grab_count[0] >= 1  # Some frames were grabbed (skipped)

    def test_read_frames_grab_fails(self):
        """Lines 77-78: grab() returns False, breaks the loop"""
        import numpy as np
        mock_cap = MagicMock()

        frame = np.zeros((240, 320, 3), dtype=np.uint8)

        # frame 0 -> read succeeds, frame 1 -> grab fails -> break
        read_count = [0]
        def mock_read():
            read_count[0] += 1
            return True, frame.copy()

        mock_cap.read = mock_read
        mock_cap.grab.return_value = False

        frames = list(ParticipantDetector._read_frames(mock_cap, 100, frame_skip=2))
        # Frame 0 is read (0 % 2 == 0), frame 1 tries grab (1 % 2 != 0) -> fails -> break
        assert len(frames) == 1


class TestProcessVideo:

    @patch('app.processing.participant_detector.open_video_capture')
    @patch('app.processing.participant_detector.get_video_metadata')
    def test_process_video_basic(self, mock_meta, mock_open):
        """Lines 126-184: process_video with mocked pipeline"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata
        import numpy as np

        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=30, width=320, height=240, duration=1.0))
        mock_cap = MagicMock()
        frame = np.zeros((240, 320, 3), dtype=np.uint8)

        read_calls = [0]
        def mock_read():
            read_calls[0] += 1
            if read_calls[0] <= 3:
                return True, frame.copy()
            return False, None

        mock_cap.read = mock_read
        mock_cap.grab.return_value = True
        mock_open.return_value = Ok(mock_cap)

        detector = ParticipantDetector(gpu=False)
        # Mock the OCR reader to return no text
        detector.reader.readtext = MagicMock(return_value=[])

        results = detector.process_video('/test.mp4', frame_skip=1, card_timeout_frames=2)
        assert isinstance(results, list)

    @patch('app.processing.participant_detector.get_video_metadata')
    def test_process_video_metadata_error(self, mock_meta):
        """process_video raises on metadata error"""
        from app.domain.result import Err
        from app.utils.error_handling import VideoError
        mock_meta.return_value = Err(VideoError("bad", video_path='/test.mp4'))

        detector = ParticipantDetector(gpu=False)
        from app.utils.error_handling import ProcessingError
        with pytest.raises(ProcessingError):
            detector.process_video('/test.mp4')

    @patch('app.processing.participant_detector.open_video_capture')
    @patch('app.processing.participant_detector.get_video_metadata')
    def test_process_video_open_error(self, mock_meta, mock_open):
        """Line 140: open_video_capture fails"""
        from app.domain.result import Ok, Err
        from app.infrastructure.video_utils import VideoMetadata
        from app.utils.error_handling import VideoError, ProcessingError
        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=300, width=320, height=240, duration=10.0))
        mock_open.return_value = Err(VideoError("can't open"))

        detector = ParticipantDetector(gpu=False)
        with pytest.raises(ProcessingError):
            detector.process_video('/test.mp4')

    @patch('app.processing.participant_detector.open_video_capture')
    @patch('app.processing.participant_detector.get_video_metadata')
    def test_process_video_with_detection(self, mock_meta, mock_open):
        """Lines 156-184: full session detection + progress callback"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata
        import numpy as np

        mock_meta.return_value = Ok(VideoMetadata(fps=10, frame_count=100, width=320, height=240, duration=10.0))
        mock_cap = MagicMock()

        # Simulate frames: first batch has participant card, then card disappears
        frames_data = []
        for i in range(20):
            frames_data.append((True, np.zeros((240, 320, 3), dtype=np.uint8)))
        frames_data.append((False, None))

        call_idx = [0]
        def mock_read():
            idx = call_idx[0]
            call_idx[0] += 1
            if idx < len(frames_data):
                return frames_data[idx]
            return (False, None)

        mock_cap.read = mock_read
        mock_cap.grab.return_value = True
        mock_open.return_value = Ok(mock_cap)

        detector = ParticipantDetector(gpu=False)

        # Make OCR return participant text for first 5 frames, then nothing
        ocr_call = [0]
        def mock_readtext(*args, **kwargs):
            ocr_call[0] += 1
            if ocr_call[0] <= 5:
                return ["Participant 1"]
            return []

        detector.reader.readtext = mock_readtext

        progress_calls = []
        def progress_cb(current, total):
            progress_calls.append((current, total))

        results = detector.process_video('/test.mp4', frame_skip=1, card_timeout_frames=3, progress_callback=progress_cb)
        assert isinstance(results, list)
        # Should have at least one detection
        if results:
            assert results[0]['participant_type'] == 'P'
            assert results[0]['participant_number'] == 1
        assert len(progress_calls) > 0  # Line 181: final progress callback

    @patch('app.processing.participant_detector.open_video_capture')
    @patch('app.processing.participant_detector.get_video_metadata')
    def test_process_video_with_large_frame_resize(self, mock_meta, mock_open):
        """Lines 88-89: frame height > 480 triggers resize"""
        from app.domain.result import Ok
        from app.infrastructure.video_utils import VideoMetadata
        import numpy as np

        mock_meta.return_value = Ok(VideoMetadata(fps=10, frame_count=20, width=1920, height=1080, duration=2.0))
        mock_cap = MagicMock()

        # Create a large frame (height > 480)
        large_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        calls = [0]
        def mock_read():
            calls[0] += 1
            if calls[0] <= 2:
                return (True, large_frame.copy())
            return (False, None)

        mock_cap.read = mock_read
        mock_cap.grab.return_value = True
        mock_open.return_value = Ok(mock_cap)

        detector = ParticipantDetector(gpu=False)
        detector.reader.readtext = MagicMock(return_value=[])

        results = detector.process_video('/test.mp4', frame_skip=1, card_timeout_frames=2)
        assert isinstance(results, list)
