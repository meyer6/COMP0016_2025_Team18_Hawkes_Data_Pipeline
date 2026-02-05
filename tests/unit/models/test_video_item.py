"""
Unit tests for app/models/video_item.py - VideoItem properties
"""

import pytest
from pathlib import Path

from app.models.video_item import VideoItem


class TestVideoItem:

    def test_filename(self, sample_video_item):
        assert sample_video_item.filename == 'test_video.mp4'

    def test_file_size_mb_nonexistent_file(self, sample_video_item):
        # File doesn't exist -> returns 0.0
        assert sample_video_item.file_size_mb == 0.0

    def test_file_size_mb_existing_file(self, temp_dir):
        test_file = temp_dir / 'size_test.mp4'
        test_file.write_bytes(b'\x00' * (1024 * 1024))  # 1MB
        item = VideoItem(video_path=str(test_file))
        assert abs(item.file_size_mb - 1.0) < 0.01

    def test_duration_str_zero(self):
        item = VideoItem(video_path='/test.mp4', duration=0.0)
        assert item.duration_str == '00:00:00'

    def test_duration_str_minutes(self):
        item = VideoItem(video_path='/test.mp4', duration=90.0)
        assert item.duration_str == '00:01:30'

    def test_duration_str_hours(self):
        item = VideoItem(video_path='/test.mp4', duration=3661.0)
        assert item.duration_str == '01:01:01'

    def test_status_text_unprocessed(self, sample_video_item):
        assert sample_video_item.status_text == 'Unprocessed'

    def test_status_text_processed_with_version(self):
        item = VideoItem(video_path='/test.mp4', processed=True, annotation_version=3)
        assert item.status_text == 'Processed (v3)'

    def test_status_text_processed_no_version(self):
        item = VideoItem(video_path='/test.mp4', processed=True, annotation_version=None)
        assert item.status_text == 'Processed'
