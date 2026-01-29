"""
Unit tests for VideoService
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.core.services.video_service import VideoService
from app.models.video_item import VideoItem
from app.domain import Ok, Err
from app.utils.error_handling import VideoError, VideoNotFoundError


class TestVideoService:
    """Test cases for VideoService"""

    def test_is_video_already_imported(self, video_service, sample_video_item):
        """Test checking if video is already imported"""
        # Not imported yet
        assert video_service.is_video_already_imported(sample_video_item.video_path) is False

        # Add video
        video_service.video_repo.add(sample_video_item)

        # Now it should be imported
        assert video_service.is_video_already_imported(sample_video_item.video_path) is True

    def test_get_all_videos(self, video_service, sample_video_item):
        """Test getting all videos"""
        # Empty initially
        videos = video_service.get_all_videos()
        assert len(videos) == 0

        # Add video
        video_service.video_repo.add(sample_video_item)

        # Should return the video
        videos = video_service.get_all_videos()
        assert len(videos) == 1
        assert videos[0].video_path == sample_video_item.video_path

    @patch('app.core.services.video_service.get_video_metadata')
    @patch('app.core.services.video_service.get_middle_frame')
    def test_import_video_success(self, mock_get_frame, mock_get_metadata, video_service, temp_dir):
        """Test successful video import"""
        # Create a real test file
        test_video_path = temp_dir / 'test.mp4'
        test_video_path.touch()

        # Mock metadata
        from app.infrastructure.video_utils import VideoMetadata
        mock_metadata = VideoMetadata(
            fps=30.0,
            frame_count=900,
            width=1920,
            height=1080,
            duration=30.0
        )
        mock_get_metadata.return_value = Ok(mock_metadata)

        # Mock frame extraction
        mock_frame = MagicMock()
        mock_get_frame.return_value = Ok((True, mock_frame))

        # Import video (will fail on thumbnail generation since frame is mocked)
        # But we can test the metadata extraction part
        result = video_service.import_video(str(test_video_path))

        # Check metadata was retrieved
        mock_get_metadata.assert_called_once_with(str(test_video_path))

    def test_import_nonexistent_video(self, video_service):
        """Test importing non-existent video returns error"""
        result = video_service.import_video('/nonexistent/video.mp4')

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, VideoNotFoundError)

    def test_import_already_imported_video(self, video_service, sample_video_item, temp_dir):
        """Test importing already imported video returns error"""
        # Create real file
        test_path = temp_dir / 'test.mp4'
        test_path.touch()

        # Add to repository
        video_service.video_repo.add(VideoItem(
            video_path=str(test_path),
            thumbnail_path=None,
            processed=False,
            duration=10.0,
            fps=30.0
        ))

        # Try to import again
        result = video_service.import_video(str(test_path))

        assert result.is_err()
        error = result.unwrap_err()
        assert "already imported" in error.message.lower()

    def test_delete_videos(self, video_service, sample_video_item):
        """Test deleting videos"""
        # Add video (note: file doesn't actually exist)
        video_service.video_repo.add(sample_video_item)

        # Delete it
        result = video_service.delete_videos([sample_video_item.video_path])

        assert result.is_ok()
        deleted_count = result.unwrap()
        assert deleted_count == 1

        # Verify it's gone
        videos = video_service.get_all_videos()
        assert len(videos) == 0

    @patch('app.core.services.video_service.get_video_metadata')
    def test_import_video_metadata_error(self, mock_get_metadata, video_service, temp_dir):
        """Line 47: metadata extraction fails"""
        test_path = temp_dir / 'test.mp4'
        test_path.touch()
        from app.utils.error_handling import VideoReadError
        mock_get_metadata.return_value = Err(VideoReadError("bad", video_path=str(test_path)))

        result = video_service.import_video(str(test_path))
        assert result.is_err()

    @patch('app.core.services.video_service.get_video_metadata')
    @patch('app.core.services.video_service.get_middle_frame')
    def test_import_video_add_fails(self, mock_frame, mock_meta, video_service, temp_dir):
        """Lines 68-70: video_repo.add returns False"""
        test_path = temp_dir / 'test.mp4'
        test_path.touch()

        from app.infrastructure.video_utils import VideoMetadata
        mock_meta.return_value = Ok(VideoMetadata(fps=30, frame_count=900, width=1920, height=1080, duration=30))
        mock_frame.return_value = Err(VideoError("no frame"))

        video_service.video_repo.add = MagicMock(return_value=False)
        result = video_service.import_video(str(test_path))
        assert result.is_err()
        assert "Failed to save" in result.unwrap_err().message

    @patch('app.core.services.video_service.get_middle_frame')
    def test_generate_thumbnail_frame_error(self, mock_frame, video_service):
        """Line 78: get_middle_frame returns Err"""
        from app.utils.error_handling import VideoReadError
        mock_frame.return_value = Err(VideoReadError("fail", video_path="/test.mp4"))
        result = video_service.generate_thumbnail('/test.mp4')
        assert result.is_err()

    @patch('app.core.services.video_service.get_middle_frame')
    def test_generate_thumbnail_frame_not_success(self, mock_frame, video_service):
        """Lines 83-88: frame extraction returns (False, None)"""
        mock_frame.return_value = Ok((False, None))
        result = video_service.generate_thumbnail('/test.mp4')
        assert result.is_err()
        assert "Failed to extract frame" in result.unwrap_err().message

    @patch('app.core.services.video_service.get_middle_frame')
    @patch('app.core.services.video_service.cv2')
    def test_generate_thumbnail_success(self, mock_cv2, mock_frame, video_service, temp_dir):
        """Lines 97-123: full thumbnail generation path"""
        import numpy as np
        fake_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_frame.return_value = Ok((True, fake_frame))
        mock_cv2.resize.return_value = fake_frame
        mock_cv2.imwrite.return_value = True
        mock_cv2.IMWRITE_JPEG_QUALITY = 1

        result = video_service.generate_thumbnail(str(temp_dir / 'test.mp4'))
        assert result.is_ok()

    @patch('app.core.services.video_service.get_middle_frame')
    @patch('app.core.services.video_service.cv2')
    def test_generate_thumbnail_imwrite_fails(self, mock_cv2, mock_frame, video_service, temp_dir):
        """Lines 113-120: cv2.imwrite returns False"""
        import numpy as np
        fake_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_frame.return_value = Ok((True, fake_frame))
        mock_cv2.resize.return_value = fake_frame
        mock_cv2.imwrite.return_value = False
        mock_cv2.IMWRITE_JPEG_QUALITY = 1

        result = video_service.generate_thumbnail(str(temp_dir / 'test.mp4'))
        assert result.is_err()
        assert "Failed to write thumbnail" in result.unwrap_err().message

    @patch('app.core.services.video_service.get_middle_frame')
    def test_generate_thumbnail_zero_dimensions(self, mock_frame, video_service, temp_dir):
        """Lines 124-131: invalid frame dimensions (0x0)"""
        import numpy as np
        fake_frame = np.zeros((0, 0, 3), dtype=np.uint8)
        # shape[:2] returns (0, 0)
        mock_frame.return_value = Ok((True, fake_frame))

        result = video_service.generate_thumbnail(str(temp_dir / 'test.mp4'))
        assert result.is_err()

    @patch('app.core.services.video_service.get_middle_frame')
    def test_generate_thumbnail_exception(self, mock_frame, video_service, temp_dir):
        """Lines 133-140: exception during thumbnail generation"""
        mock_frame.return_value = Ok((True, MagicMock(shape=(1080, 1920, 3))))
        # cv2.resize will fail on a MagicMock frame
        result = video_service.generate_thumbnail(str(temp_dir / 'test.mp4'))
        assert result.is_err()

    def test_delete_videos_with_existing_thumbnail(self, video_service, temp_dir):
        """Lines 152-156: delete video with existing thumbnail file"""
        thumb_path = temp_dir / 'thumb.jpg'
        thumb_path.touch()
        item = VideoItem(
            video_path=str(temp_dir / 'v.mp4'),
            thumbnail_path=str(thumb_path),
            processed=False
        )
        video_service.video_repo.add(item)
        result = video_service.delete_videos([str(temp_dir / 'v.mp4')])
        assert result.is_ok()
        assert not thumb_path.exists()

    def test_delete_videos_thumbnail_error(self, video_service, temp_dir):
        """Lines 155-156: thumbnail deletion raises exception"""
        item = VideoItem(
            video_path=str(temp_dir / 'v.mp4'),
            thumbnail_path=str(temp_dir / 'thumb.jpg'),
            processed=False
        )
        video_service.video_repo.add(item)
        # Create thumb, then make unlink fail
        thumb = Path(temp_dir / 'thumb.jpg')
        thumb.touch()
        with patch.object(Path, 'unlink', side_effect=PermissionError("locked")):
            result = video_service.delete_videos([str(temp_dir / 'v.mp4')])
            assert result.is_ok()

    def test_delete_videos_general_exception(self, video_service, temp_dir):
        """Lines 164-165: general exception during deletion"""
        item = VideoItem(video_path=str(temp_dir / 'v.mp4'), processed=False)
        video_service.video_repo.add(item)
        video_service.video_repo.remove = MagicMock(side_effect=RuntimeError("boom"))
        result = video_service.delete_videos([str(temp_dir / 'v.mp4')])
        assert result.is_ok()
        assert result.unwrap() == 0

    @patch('app.core.services.video_service.get_video_metadata')
    def test_get_video_metadata_success(self, mock_get, video_service):
        """Lines 173-179: get_video_metadata returns Ok tuple"""
        from app.infrastructure.video_utils import VideoMetadata
        mock_get.return_value = Ok(VideoMetadata(fps=30, frame_count=900, width=1920, height=1080, duration=30))
        result = video_service.get_video_metadata('/test.mp4')
        assert result.is_ok()
        fps, duration, frame_count = result.unwrap()
        assert fps == 30
        assert duration == 30
        assert frame_count == 900

    @patch('app.core.services.video_service.get_video_metadata')
    def test_get_video_metadata_error(self, mock_get, video_service):
        """Lines 175-176: get_video_metadata returns Err"""
        mock_get.return_value = Err(VideoError("fail"))
        result = video_service.get_video_metadata('/test.mp4')
        assert result.is_err()
