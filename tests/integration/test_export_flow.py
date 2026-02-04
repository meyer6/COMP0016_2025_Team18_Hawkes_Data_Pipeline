"""
Integration test for export service with real annotation file
"""

import pytest

from app.core.services.export_service import ExportService
from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.core.config.app_config import AppConfig
from app.models.annotation import VideoAnnotation, TaskSegment


@pytest.mark.integration
class TestExportFlow:

    def test_export_summary_with_real_annotation_file(self, temp_dir):
        annotation_repo = AnnotationRepository()
        config = AppConfig(model_path=str(temp_dir / 'model.pkl'))
        service = ExportService(annotation_repo, config)

        video_path = str(temp_dir / 'test.mp4')

        # Create and save a real annotation
        annotation = VideoAnnotation(video_path=video_path, version=1, duration=100.0)
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=30),
            TaskSegment(task_name='Idle', start_time=30, end_time=50),
            TaskSegment(task_name='ChickenThigh', start_time=50, end_time=80),
            TaskSegment(task_name='GloveCut', start_time=80, end_time=100),
        ]
        annotation_repo.save(annotation)

        # Get export summary from the real saved file
        result = service.get_export_summary(video_path)
        assert result.is_ok()

        summary = result.unwrap()
        assert summary.total_segments == 3  # Idle excluded
        assert summary.task_counts['Suture'] == 1
        assert summary.task_counts['ChickenThigh'] == 1
        assert summary.task_counts['GloveCut'] == 1
        assert summary.total_duration == 80.0
