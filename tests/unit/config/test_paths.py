"""
Unit tests for app/core/config/paths.py - PathConfig
"""

import pytest
from pathlib import Path

from app.core.config.paths import PathConfig


class TestPathConfig:

    def test_get_project_root_returns_path(self):
        root = PathConfig.get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_project_root_contains_main_py(self):
        root = PathConfig.get_project_root()
        assert (root / 'main.py').exists()

    def test_get_project_root_caching(self):
        root1 = PathConfig.get_project_root()
        root2 = PathConfig.get_project_root()
        assert root1 == root2

    def test_reset_clears_cache(self):
        PathConfig.get_project_root()
        PathConfig.reset()
        assert PathConfig._project_root is None

    def test_get_registry_path(self):
        path = PathConfig.get_registry_path()
        assert path.name == 'video_registry.json'
        assert '.cache' in str(path)

    def test_get_thumbnails_dir(self):
        thumbnails = PathConfig.get_thumbnails_dir()
        assert thumbnails.name == 'thumbnails'
        assert thumbnails.exists()

    def test_get_task_classifier_model_path(self):
        path = PathConfig.get_task_classifier_model_path()
        assert path.name == 'task_classifier.pkl'
        assert 'models' in str(path)

    def test_get_video_inference_dir(self):
        path = PathConfig.get_video_inference_dir()
        assert path.name == 'video_inference'

    def test_fallback_when_no_markers(self):
        from unittest.mock import patch
        PathConfig.reset()
        # Mock exists/is_dir to always return False so marker check fails
        with patch.object(Path, 'exists', return_value=False), \
             patch.object(Path, 'is_dir', return_value=False):
            PathConfig.reset()
            root = PathConfig.get_project_root()
            assert isinstance(root, Path)
