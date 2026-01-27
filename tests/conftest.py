"""
Pytest configuration and fixtures
"""

import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from app.core.config import AppConfig, PathConfig
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.core.services.video_service import VideoService
from app.core.services.processing_service import ProcessingService
from app.core.services.export_service import ExportService
from app.models.video_item import VideoItem
from app.models.annotation import VideoAnnotation, TaskSegment, ParticipantMarker


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration"""
    config = AppConfig(
        model_path=str(temp_dir / 'test_model.pkl'),
        sample_every=5,
        smoothing_window=15,
        log_level='DEBUG',
        log_to_file=False
    )
    return config


@pytest.fixture
def test_registry_path(temp_dir):
    """Create a test registry path"""
    return temp_dir / 'test_registry.json'


@pytest.fixture
def video_repository(test_registry_path):
    """Create a video repository for testing"""
    return VideoRepository(registry_path=test_registry_path)


@pytest.fixture
def annotation_repository():
    """Create an annotation repository for testing"""
    return AnnotationRepository()


@pytest.fixture
def video_service(video_repository, annotation_repository, test_config):
    """Create a video service for testing"""
    return VideoService(video_repository, annotation_repository, test_config)


@pytest.fixture
def processing_service(video_repository, annotation_repository, test_config):
    """Create a processing service for testing"""
    return ProcessingService(video_repository, annotation_repository, test_config)


@pytest.fixture
def export_service(annotation_repository, test_config):
    """Create an export service for testing"""
    return ExportService(annotation_repository, test_config)


@pytest.fixture
def sample_video_item(temp_dir):
    """Create a sample VideoItem for testing"""
    return VideoItem(
        video_path=str(temp_dir / 'test_video.mp4'),
        thumbnail_path=str(temp_dir / 'test_thumb.jpg'),
        processed=False,
        duration=60.0,
        fps=30.0,
        annotation_version=None
    )


@pytest.fixture
def sample_task_segment():
    """Create a single TaskSegment for testing"""
    return TaskSegment(
        task_name='Suture',
        start_time=10.0,
        end_time=25.0,
        confidence=0.95
    )


@pytest.fixture
def sample_participant_marker():
    """Create a single ParticipantMarker for testing"""
    return ParticipantMarker(
        participant_type='P',
        participant_number=1,
        timestamp=5.0,
        duration=3.0,
        confidence=0.9
    )


@pytest.fixture
def sample_annotation(temp_dir):
    """Create a VideoAnnotation with task segments and participant markers"""
    annotation = VideoAnnotation(
        video_path=str(temp_dir / 'test_video.mp4'),
        version=1,
        duration=120.0,
        fps=30.0,
        frame_count=3600,
        processed=True,
        model_version='1.0'
    )
    annotation.task_segments = [
        TaskSegment(task_name='Suture', start_time=0.0, end_time=30.0, confidence=0.95),
        TaskSegment(task_name='Idle', start_time=30.0, end_time=45.0, confidence=0.8),
        TaskSegment(task_name='ChickenThigh', start_time=45.0, end_time=80.0, confidence=0.9),
        TaskSegment(task_name='GloveCut', start_time=80.0, end_time=120.0, confidence=0.85),
    ]
    annotation.participant_markers = [
        ParticipantMarker(participant_type='P', participant_number=1, timestamp=2.0, duration=3.0, confidence=0.9),
        ParticipantMarker(participant_type='E', participant_number=2, timestamp=50.0, duration=2.5, confidence=0.85),
    ]
    return annotation


@pytest.fixture
def mock_logger():
    """Create a mock logger for ErrorContext tests"""
    return MagicMock(spec=logging.Logger)


@pytest.fixture(scope='session')
def qapp():
    """Session-scoped QApplication instance for PyQt tests"""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def reset_path_config():
    """Reset PathConfig before each test"""
    PathConfig.reset()
    yield
    PathConfig.reset()
