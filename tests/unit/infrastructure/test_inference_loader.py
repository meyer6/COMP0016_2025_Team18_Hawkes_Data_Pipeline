"""
Unit tests for app/infrastructure/inference_loader.py
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.infrastructure.inference_loader import InferenceLoader


class TestInferenceLoader:

    def setup_method(self):
        InferenceLoader.reset_cache()

    def teardown_method(self):
        InferenceLoader.reset_cache()

    def test_reset_cache(self):
        InferenceLoader._cached_module = "something"
        InferenceLoader.reset_cache()
        assert InferenceLoader._cached_module is None

    def test_returns_cached_module(self):
        mock_module = MagicMock()
        InferenceLoader._cached_module = mock_module
        result = InferenceLoader.load_video_inference_module()
        assert result is mock_module

    @patch('app.infrastructure.inference_loader.PathConfig')
    def test_module_not_found(self, mock_path_config, temp_dir):
        mock_path_config.get_video_inference_dir.return_value = temp_dir / 'nonexistent'
        with pytest.raises(ImportError, match="video_inference.py not found"):
            InferenceLoader.load_video_inference_module()

    @patch('app.infrastructure.inference_loader.importlib.util.spec_from_file_location')
    @patch('app.infrastructure.inference_loader.PathConfig')
    def test_spec_is_none(self, mock_path_config, mock_spec_from, temp_dir):
        inference_dir = temp_dir / 'scripts'
        inference_dir.mkdir()
        module_file = inference_dir / 'video_inference.py'
        module_file.write_text('# empty module')
        mock_path_config.get_video_inference_dir.return_value = inference_dir
        mock_spec_from.return_value = None

        with pytest.raises(ImportError, match="Failed to load"):
            InferenceLoader.load_video_inference_module()

    @patch('app.infrastructure.inference_loader.importlib.util')
    @patch('app.infrastructure.inference_loader.PathConfig')
    def test_successful_load(self, mock_path_config, mock_util, temp_dir):
        inference_dir = temp_dir / 'scripts'
        inference_dir.mkdir()
        module_file = inference_dir / 'video_inference.py'
        module_file.write_text('# test module')
        mock_path_config.get_video_inference_dir.return_value = inference_dir

        mock_spec = MagicMock()
        mock_module = MagicMock()
        mock_util.spec_from_file_location.return_value = mock_spec
        mock_util.module_from_spec.return_value = mock_module

        result = InferenceLoader.load_video_inference_module()
        assert result is mock_module
        assert InferenceLoader._cached_module is mock_module
