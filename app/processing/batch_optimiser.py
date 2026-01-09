"""Batch size optimiser - selects batch sizes for processing"""

import torch
import logging

logger = logging.getLogger(__name__)


class BatchOptimiser:
    """Simple batch size selection based on device type"""

    @staticmethod
    def get_available_memory():
        gpu_mem = 0.0
        if torch.cuda.is_available():
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        import psutil
        sys_mem = psutil.virtual_memory().available / (1024**3)
        return gpu_mem, sys_mem

    @staticmethod
    def calculate_task_classifier_batch_size(use_gpu=True):
        if use_gpu and torch.cuda.is_available():
            return 32
        return 8

    @staticmethod
    def calculate_ocr_batch_size(use_gpu=True):
        if use_gpu and torch.cuda.is_available():
            return 8
        return 2

    @staticmethod
    def log_hardware_info():
        logger.info("=== Hardware Information ===")
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.info("GPU: Not available (CPU mode)")
        logger.info(f"PyTorch: {torch.__version__}")
        logger.info("===========================")
