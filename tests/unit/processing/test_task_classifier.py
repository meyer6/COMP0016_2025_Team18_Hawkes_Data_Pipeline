"""
Unit tests for app/processing/task_classifier.py
"""

import pytest
from unittest.mock import patch, MagicMock

from app.processing.task_classifier import TaskClassifier, _get_inference_module


class TestGetInferenceModule:

    @patch('app.processing.task_classifier.InferenceLoader')
    def test_loads_module(self, mock_loader):
        import app.processing.task_classifier as tc
        tc._video_inference = None  # Reset global
        mock_module = MagicMock()
        mock_loader.load_video_inference_module.return_value = mock_module

        result = _get_inference_module()
        assert result is mock_module
        tc._video_inference = None  # Cleanup

    @patch('app.processing.task_classifier.InferenceLoader')
    def test_caches_module(self, mock_loader):
        import app.processing.task_classifier as tc
        tc._video_inference = None
        mock_module = MagicMock()
        mock_loader.load_video_inference_module.return_value = mock_module

        _get_inference_module()
        _get_inference_module()  # Second call
        mock_loader.load_video_inference_module.assert_called_once()
        tc._video_inference = None


