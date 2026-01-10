"""
Batch size optimiser - automatically selects optimal batch sizes based on hardware
"""

import torch
import psutil
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class BatchOptimiser:
    """Determines optimal batch sizes for GPU/CPU processing"""

    @staticmethod
    def get_available_memory() -> Tuple[float, float]:
        """
        Get available GPU and system memory in GB

        Returns:
            Tuple of (gpu_memory_gb, system_memory_gb)
        """
        # GPU memory
        gpu_memory_gb = 0.0
        if torch.cuda.is_available():
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            gpu_memory_gb -= allocated

        # System RAM
        system_memory_gb = psutil.virtual_memory().available / (1024**3)

        return gpu_memory_gb, system_memory_gb

    @staticmethod
    def calculate_task_classifier_batch_size(use_gpu: bool = True) -> int:
        """
        Calculate optimal batch size for task classifier

        Task classifier uses ResNet50 with 224x224 images:
        - Base model memory: ~100MB
        - Per-image memory: ~2-3MB (input + activations)
        - Safe memory usage: 60% of available (leave headroom)

        Args:
            use_gpu: Whether GPU is being used

        Returns:
            Optimal batch size
        """
        gpu_memory_gb, system_memory_gb = BatchOptimiser.get_available_memory()

        if use_gpu and gpu_memory_gb > 0:
            # GPU batch sizing
            # Use 60% of available GPU memory for safety
            available_memory_mb = gpu_memory_gb * 1024 * 0.6

            # Estimate: 100MB base + 2.5MB per image
            base_memory_mb = 100
            per_image_mb = 2.5

            batch_size = int((available_memory_mb - base_memory_mb) / per_image_mb)

            # Clamp to reasonable range
            batch_size = max(8, min(batch_size, 128))

            logger.info(f"Task classifier: GPU memory available: {gpu_memory_gb:.2f}GB, batch size: {batch_size}")
            return batch_size
        else:
            # CPU batch sizing - limited by RAM and CPU cores
            # Use smaller batches for CPU to avoid thrashing
            available_memory_mb = system_memory_gb * 1024 * 0.3  # Use 30% of RAM

            # CPU is less memory efficient
            base_memory_mb = 50
            per_image_mb = 5

            batch_size = int((available_memory_mb - base_memory_mb) / per_image_mb)

            # CPU benefits less from large batches
            batch_size = max(4, min(batch_size, 32))

            logger.info(f"Task classifier: CPU mode, RAM available: {system_memory_gb:.2f}GB, batch size: {batch_size}")
            return batch_size

    @staticmethod
    def calculate_ocr_batch_size(use_gpu: bool = True) -> int:
        """
        Calculate optimal batch size for OCR (participant detector)

        EasyOCR is more memory-intensive than classification:
        - Base model memory: ~200MB
        - Per-image memory (720p): ~50-100MB depending on text density
        - Safe memory usage: 50% of available (OCR has unpredictable peaks)

        Args:
            use_gpu: Whether GPU is being used

        Returns:
            Optimal batch size
        """
        gpu_memory_gb, system_memory_gb = BatchOptimiser.get_available_memory()

        if use_gpu and gpu_memory_gb > 0:
            # GPU batch sizing
            # Use 50% of available GPU memory (OCR is less predictable)
            available_memory_mb = gpu_memory_gb * 1024 * 0.5

            # Estimate: 200MB base + 75MB per image (conservative)
            base_memory_mb = 200
            per_image_mb = 75

            batch_size = int((available_memory_mb - base_memory_mb) / per_image_mb)

            # OCR doesn't scale as well with large batches
            batch_size = max(4, min(batch_size, 32))

            logger.info(f"OCR: GPU memory available: {gpu_memory_gb:.2f}GB, batch size: {batch_size}")
            return batch_size
        else:
            # CPU batch sizing
            available_memory_mb = system_memory_gb * 1024 * 0.2  # Use 20% of RAM

            base_memory_mb = 100
            per_image_mb = 100

            batch_size = int((available_memory_mb - base_memory_mb) / per_image_mb)

            # Very small batches for CPU OCR
            batch_size = max(2, min(batch_size, 8))

            logger.info(f"OCR: CPU mode, RAM available: {system_memory_gb:.2f}GB, batch size: {batch_size}")
            return batch_size

    @staticmethod
    def log_hardware_info():
        """Log hardware information for debugging"""
        gpu_memory_gb, system_memory_gb = BatchOptimiser.get_available_memory()

        logger.info("=== Hardware Information ===")
        logger.info(f"System RAM: {system_memory_gb:.2f}GB available")

        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {gpu_memory_gb:.2f}GB available")
            logger.info(f"CUDA Version: {torch.version.cuda}")
        else:
            logger.info("GPU: Not available (CPU mode)")

        logger.info(f"PyTorch Version: {torch.__version__}")
        logger.info("===========================")
