"""
Unit tests for app/core/container.py - ServiceContainer
"""

import pytest

from app.core.container import ServiceContainer
from app.core.config.app_config import AppConfig
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.core.services.video_service import VideoService
from app.core.services.processing_service import ProcessingService
from app.core.services.export_service import ExportService


class TestServiceContainer:

    def test_config_returns_provided_config(self, test_config):
        container = ServiceContainer(test_config)
        assert container.config() is test_config

    def test_video_repository_singleton(self, test_config):
        container = ServiceContainer(test_config)
        repo1 = container.video_repository()
        repo2 = container.video_repository()
        assert repo1 is repo2
        assert isinstance(repo1, VideoRepository)

    def test_annotation_repository_singleton(self, test_config):
        container = ServiceContainer(test_config)
        repo1 = container.annotation_repository()
        repo2 = container.annotation_repository()
        assert repo1 is repo2
        assert isinstance(repo1, AnnotationRepository)

    def test_video_service_singleton(self, test_config):
        container = ServiceContainer(test_config)
        svc1 = container.video_service()
        svc2 = container.video_service()
        assert svc1 is svc2
        assert isinstance(svc1, VideoService)

    def test_processing_service_singleton(self, test_config):
        container = ServiceContainer(test_config)
        svc = container.processing_service()
        assert isinstance(svc, ProcessingService)

    def test_export_service_singleton(self, test_config):
        container = ServiceContainer(test_config)
        svc = container.export_service()
        assert isinstance(svc, ExportService)

    def test_reset_clears_singletons(self, test_config):
        container = ServiceContainer(test_config)
        repo1 = container.video_repository()
        container.reset()
        repo2 = container.video_repository()
        assert repo1 is not repo2

    def test_shared_repos_across_services(self, test_config):
        container = ServiceContainer(test_config)
        video_svc = container.video_service()
        proc_svc = container.processing_service()
        # Both services share the same video repository
        assert video_svc.video_repo is proc_svc.video_repo
