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


class TestTaskClassifier:

    @patch('app.processing.task_classifier._get_inference_module')
    def test_init(self, mock_get_module):
        mock_vi = MagicMock()
        mock_vi.model = "test_model"
        mock_vi.DEVICE = "cpu"
        mock_get_module.return_value = mock_vi

        tc = TaskClassifier()
        assert tc.model == "test_model"
        assert tc.device == "cpu"

    @patch('app.processing.task_classifier._get_inference_module')
    def test_process_video(self, mock_get_module):
        mock_vi = MagicMock()
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{'task': 'Suture', 'frame': 1}]
        mock_vi.process_video.return_value = mock_df
        mock_vi.smooth_predictions.return_value = mock_df
        mock_vi.enforce_min_duration.return_value = mock_df
        mock_vi.model = "model"
        mock_vi.DEVICE = "cpu"
        mock_get_module.return_value = mock_vi

        tc = TaskClassifier()
        result = tc.process_video('/test.mp4', sample_every=30, smoothing_window=15, min_duration_sec=5, batch_size=32)
        assert result == [{'task': 'Suture', 'frame': 1}]

    @patch('app.processing.task_classifier.pd')
    @patch('app.processing.task_classifier._get_inference_module')
    def test_aggregate_time_ranges(self, mock_get_module, mock_pd):
        mock_vi = MagicMock()
        mock_vi.model = "model"
        mock_vi.DEVICE = "cpu"
        mock_agg_df = MagicMock()
        mock_agg_df.to_dict.return_value = [{'task': 'Suture', 'start': '00:00:00', 'end': '00:00:30'}]
        mock_vi.aggregate_time_ranges.return_value = mock_agg_df
        mock_get_module.return_value = mock_vi

        tc = TaskClassifier()
        result = tc.aggregate_time_ranges([{'frame': 1, 'pred': 'Suture'}])
        assert len(result) == 1
