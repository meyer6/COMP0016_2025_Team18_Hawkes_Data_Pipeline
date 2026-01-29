"""
Unit tests for app/core/services/processing_service.py
"""

import pytest

from app.core.services.processing_service import ProcessingService


class TestProcessingService:

    def test_mark_complete(self, processing_service, video_repository, sample_video_item):
        video_repository.add(sample_video_item)
        result = processing_service.mark_processing_complete(sample_video_item.video_path, 1)
        assert result is True

        found = video_repository.find_by_path(sample_video_item.video_path)
        assert found.processed is True
        assert found.annotation_version == 1

    def test_mark_complete_nonexistent(self, processing_service):
        result = processing_service.mark_processing_complete('/nonexistent.mp4', 1)
        assert result is False

    def test_mark_failed(self, processing_service, video_repository, sample_video_item):
        video_repository.add(sample_video_item)
        # First mark complete
        processing_service.mark_processing_complete(sample_video_item.video_path, 1)
        # Then mark failed - resets processed flag but annotation_version
        # is only updated when not None (by repo design), so it keeps old value
        result = processing_service.mark_processing_failed(sample_video_item.video_path)
        assert result is True

        found = video_repository.find_by_path(sample_video_item.video_path)
        assert found.processed is False

    def test_mark_failed_nonexistent(self, processing_service):
        result = processing_service.mark_processing_failed('/nonexistent.mp4')
        assert result is False

    def test_get_processing_params(self, processing_service, test_config):
        params = processing_service.get_processing_params()
        assert params['sample_every'] == test_config.sample_every
        assert params['smoothing_window'] == test_config.smoothing_window
        assert params['min_duration_sec'] == test_config.min_duration_sec
        assert 'use_gpu' in params
