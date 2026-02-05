"""
Unit tests for app/processing/batch_optimiser.py - BatchOptimiser
"""

import pytest
from unittest.mock import patch, MagicMock

from app.processing.batch_optimiser import BatchOptimiser


class TestBatchOptimiser:

    @patch('app.processing.batch_optimiser.psutil')
    @patch('app.processing.batch_optimiser.torch')
    def test_get_available_memory_with_gpu(self, mock_torch, mock_psutil):
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value = MagicMock(
            total_memory=8 * 1024**3  # 8GB
        )
        mock_torch.cuda.memory_allocated.return_value = 1 * 1024**3  # 1GB allocated

        mem_info = MagicMock()
        mem_info.available = 16 * 1024**3  # 16GB RAM
        mock_psutil.virtual_memory.return_value = mem_info

        gpu_mem, sys_mem = BatchOptimiser.get_available_memory()
        assert abs(gpu_mem - 7.0) < 0.1  # 8 - 1 = 7GB
        assert abs(sys_mem - 16.0) < 0.1

    @patch('app.processing.batch_optimiser.psutil')
    @patch('app.processing.batch_optimiser.torch')
    def test_get_available_memory_no_gpu(self, mock_torch, mock_psutil):
        mock_torch.cuda.is_available.return_value = False

        mem_info = MagicMock()
        mem_info.available = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mem_info

        gpu_mem, sys_mem = BatchOptimiser.get_available_memory()
        assert gpu_mem == 0.0
        assert abs(sys_mem - 8.0) < 0.1

    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(4.0, 16.0))
    def test_task_classifier_batch_gpu(self, mock_mem):
        batch = BatchOptimiser.calculate_task_classifier_batch_size(use_gpu=True)
        assert 8 <= batch <= 128

    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(0.0, 8.0))
    def test_task_classifier_batch_cpu(self, mock_mem):
        batch = BatchOptimiser.calculate_task_classifier_batch_size(use_gpu=False)
        assert 4 <= batch <= 32

    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(4.0, 16.0))
    def test_ocr_batch_gpu(self, mock_mem):
        batch = BatchOptimiser.calculate_ocr_batch_size(use_gpu=True)
        assert 4 <= batch <= 32

    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(0.0, 8.0))
    def test_ocr_batch_cpu(self, mock_mem):
        batch = BatchOptimiser.calculate_ocr_batch_size(use_gpu=False)
        assert 2 <= batch <= 8

    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(0.0, 0.5))
    def test_low_memory_clamped(self, mock_mem):
        batch = BatchOptimiser.calculate_task_classifier_batch_size(use_gpu=False)
        assert batch >= 4  # Minimum clamp

    @patch('app.processing.batch_optimiser.torch')
    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(0.0, 8.0))
    def test_log_hardware_info_no_gpu(self, mock_mem, mock_torch):
        mock_torch.cuda.is_available.return_value = False
        mock_torch.__version__ = '2.1.0'
        BatchOptimiser.log_hardware_info()

    @patch('app.processing.batch_optimiser.psutil')
    @patch('app.processing.batch_optimiser.torch')
    def test_get_available_memory_gpu_exception(self, mock_torch, mock_psutil):
        """Lines 32-33: exception getting GPU memory"""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.side_effect = RuntimeError("GPU error")

        mem_info = MagicMock()
        mem_info.available = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mem_info

        gpu_mem, sys_mem = BatchOptimiser.get_available_memory()
        assert gpu_mem == 0.0
        assert abs(sys_mem - 8.0) < 0.1

    @patch('app.processing.batch_optimiser.torch')
    @patch.object(BatchOptimiser, 'get_available_memory', return_value=(4.0, 16.0))
    def test_log_hardware_info_with_gpu(self, mock_mem, mock_torch):
        """Lines 149-151: GPU available path in log_hardware_info"""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "Test GPU"
        mock_torch.version.cuda = "11.8"
        mock_torch.__version__ = '2.1.0'
        BatchOptimiser.log_hardware_info()
