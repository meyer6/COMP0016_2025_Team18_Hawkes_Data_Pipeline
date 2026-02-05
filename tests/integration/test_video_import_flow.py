"""
Integration test for video import flow
"""

import pytest
from pathlib import Path

from app.core.config import AppConfig, PathConfig
from app.core.container import ServiceContainer


class TestVideoImportFlow:

    def test_service_container_creation(self, test_config):
        container = ServiceContainer(test_config)

        assert container.video_service() is not None
        assert container.processing_service() is not None
        assert container.export_service() is not None

        # Singletons should return same instance
        assert container.video_service() is container.video_service()

    def test_config_loading_and_validation(self, temp_dir):
        config_path = temp_dir / 'config.json'
        config = AppConfig()
        config.save(config_path)

        loaded_config = AppConfig.load(config_path)
        assert loaded_config.sample_every == config.sample_every
        assert loaded_config.smoothing_window == config.smoothing_window

    def test_path_config_project_root_detection(self):
        root = PathConfig.get_project_root()
        assert root is not None
        assert root.exists()
