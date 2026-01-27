"""
Unit tests for app/core/config/constants.py - TaskName, FileExtensions, ProcessingDefaults
"""

import pytest

from app.core.config.constants import (
    TaskName, FileExtensions, ProcessingDefaults, UIConstants
)


class TestTaskName:

    def test_all_task_names(self):
        names = TaskName.get_all_names()
        assert len(names) == 9
        assert 'Idle' in names
        assert 'Suture' in names

    def test_is_valid_true(self):
        assert TaskName.is_valid('Suture') is True
        assert TaskName.is_valid('Idle') is True
        assert TaskName.is_valid('CameraTarget') is True

    def test_is_valid_false(self):
        assert TaskName.is_valid('NonExistent') is False
        assert TaskName.is_valid('') is False

    def test_enum_values(self):
        assert TaskName.IDLE.value == 'Idle'
        assert TaskName.SUTURE.value == 'Suture'
        assert TaskName.CAMERA_TARGET.value == 'CameraTarget'

    def test_string_enum(self):
        # TaskName inherits from str
        assert isinstance(TaskName.IDLE, str)
        assert TaskName.IDLE == 'Idle'


class TestFileExtensions:

    def test_video_extensions_list(self):
        assert '.mp4' in FileExtensions.VIDEO_EXTENSIONS
        assert '.avi' in FileExtensions.VIDEO_EXTENSIONS
        assert len(FileExtensions.VIDEO_EXTENSIONS) == 8

    def test_is_video_file_true(self):
        assert FileExtensions.is_video_file('test.mp4') is True
        assert FileExtensions.is_video_file('TEST.AVI') is True

    def test_is_video_file_false(self):
        assert FileExtensions.is_video_file('test.txt') is False
        assert FileExtensions.is_video_file('test.jpg') is False

    def test_is_image_file(self):
        assert FileExtensions.is_image_file('thumb.jpg') is True
        assert FileExtensions.is_image_file('photo.PNG') is True
        assert FileExtensions.is_image_file('video.mp4') is False

    def test_get_video_filter(self):
        filt = FileExtensions.get_video_filter()
        assert 'Video Files' in filt
        assert '*.mp4' in filt

    def test_annotation_extension(self):
        assert FileExtensions.ANNOTATION_EXTENSION == '.json'


class TestProcessingDefaults:

    def test_sample_every(self):
        assert ProcessingDefaults.SAMPLE_EVERY == 30

    def test_smoothing_window(self):
        assert ProcessingDefaults.SMOOTHING_WINDOW == 15

    def test_min_duration_sec(self):
        assert ProcessingDefaults.MIN_DURATION_SEC == 5

    def test_confidence_threshold(self):
        assert ProcessingDefaults.CONFIDENCE_THRESHOLD == 0.5

    def test_thumbnail_dimensions(self):
        assert ProcessingDefaults.THUMBNAIL_WIDTH == 400
        assert ProcessingDefaults.THUMBNAIL_HEIGHT == 300
        assert ProcessingDefaults.THUMBNAIL_QUALITY == 85


class TestTaskColors:

    def test_get_color_known(self):
        from app.core.config.constants import TaskColors
        color = TaskColors.get_color('Idle')
        assert color is not None

    def test_get_color_unknown(self):
        from app.core.config.constants import TaskColors
        color = TaskColors.get_color('NonExistentTask')
        assert color == TaskColors.DEFAULT_COLOR

    def test_get_all_colors(self):
        from app.core.config.constants import TaskColors
        colors = TaskColors.get_all_colors()
        assert len(colors) == 9


class TestUIConstants:

    def test_grid_columns(self):
        assert UIConstants.GRID_COLUMNS == 3

    def test_window_dimensions(self):
        assert UIConstants.DEFAULT_WINDOW_WIDTH == 1400
        assert UIConstants.DEFAULT_WINDOW_HEIGHT == 900
