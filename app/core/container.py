"""
Dependency injection container
Manages service instances and their dependencies
"""

import logging
from typing import Dict, Any

from .config import AppConfig
from .services.video_service import VideoService
from .services.processing_service import ProcessingService
from .services.export_service import ExportService
from ..infrastructure.repositories.video_repository import VideoRepository
from ..infrastructure.repositories.annotation_repository import AnnotationRepository

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency injection container.
    Manages singleton service instances and their dependencies.
    """

    def __init__(self, config: AppConfig):
        self._config = config
        self._singletons: Dict[str, Any] = {}
        logger.info("Service container initialised")

    def config(self) -> AppConfig:
        return self._config

    def video_repository(self) -> VideoRepository:
        if 'video_repository' not in self._singletons:
            self._singletons['video_repository'] = VideoRepository()
            logger.debug("Created VideoRepository singleton")
        return self._singletons['video_repository']

    def annotation_repository(self) -> AnnotationRepository:
        if 'annotation_repository' not in self._singletons:
            self._singletons['annotation_repository'] = AnnotationRepository()
            logger.debug("Created AnnotationRepository singleton")
        return self._singletons['annotation_repository']

    def video_service(self) -> VideoService:
        if 'video_service' not in self._singletons:
            self._singletons['video_service'] = VideoService(
                self.video_repository(),
                self.annotation_repository(),
                self._config
            )
            logger.debug("Created VideoService singleton")
        return self._singletons['video_service']

    def processing_service(self) -> ProcessingService:
        if 'processing_service' not in self._singletons:
            self._singletons['processing_service'] = ProcessingService(
                self.video_repository(),
                self.annotation_repository(),
                self._config
            )
            logger.debug("Created ProcessingService singleton")
        return self._singletons['processing_service']

    def export_service(self) -> ExportService:
        if 'export_service' not in self._singletons:
            self._singletons['export_service'] = ExportService(
                self.annotation_repository(),
                self._config
            )
            logger.debug("Created ExportService singleton")
        return self._singletons['export_service']

    def reset(self):
        self._singletons.clear()
        logger.info("Service container reset")
