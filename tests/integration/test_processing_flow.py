"""
Integration tests for processing service flow
"""

import pytest

from app.core.services.processing_service import ProcessingService
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.core.config.app_config import AppConfig
from app.models.video_item import VideoItem


@pytest.mark.integration
class TestProcessingFlow:

    def test_mark_complete_updates_repo(self, temp_dir):
        registry_path = temp_dir / 'registry.json'
        video_repo = VideoRepository(registry_path=registry_path)
        annotation_repo = AnnotationRepository()
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))

        service = ProcessingService(video_repo, annotation_repo, config)

        video_path = str(temp_dir / 'test.mp4')
        video_repo.add(VideoItem(video_path=video_path, duration=30.0))

        assert service.mark_processing_complete(video_path, annotation_version=1)

        item = video_repo.find_by_path(video_path)
        assert item.processed is True
        assert item.annotation_version == 1

    def test_mark_failed_resets(self, temp_dir):
        registry_path = temp_dir / 'registry.json'
        video_repo = VideoRepository(registry_path=registry_path)
        annotation_repo = AnnotationRepository()
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))

        service = ProcessingService(video_repo, annotation_repo, config)

        video_path = str(temp_dir / 'test.mp4')
        video_repo.add(VideoItem(video_path=video_path, processed=True, annotation_version=1))

        assert service.mark_processing_failed(video_path)

        item = video_repo.find_by_path(video_path)
        assert item.processed is False
