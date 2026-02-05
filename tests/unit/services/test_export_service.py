"""
Unit tests for app/core/services/export_service.py - ExportService, ExportSummary
"""

import pytest
from unittest.mock import MagicMock

from app.core.services.export_service import ExportService, ExportSummary
from app.models.video_item import VideoItem
from app.models.annotation import VideoAnnotation, TaskSegment


class TestExportSummary:

    def test_get_breakdown_text(self):
        summary = ExportSummary(
            total_segments=5,
            task_counts={'Suture': 3, 'ChickenThigh': 2},
            total_duration=150.0
        )
        text = summary.get_breakdown_text()
        assert 'Suture: 3 clip(s)' in text
        assert 'ChickenThigh: 2 clip(s)' in text

    def test_empty_breakdown(self):
        summary = ExportSummary(total_segments=0, task_counts={}, total_duration=0.0)
        assert summary.get_breakdown_text() == ''


class TestExportService:

    def test_get_export_summary_no_annotation(self, export_service):
        result = export_service.get_export_summary('/nonexistent.mp4')
        assert result.is_err()

    def test_get_export_summary_success(self, export_service):
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=30),
            TaskSegment(task_name='Idle', start_time=30, end_time=40),
            TaskSegment(task_name='ChickenThigh', start_time=40, end_time=70),
        ]
        export_service.annotation_repo.load = MagicMock(return_value=annotation)

        result = export_service.get_export_summary('/test.mp4')
        assert result.is_ok()
        summary = result.unwrap()
        assert summary.total_segments == 2  # Idle excluded
        assert summary.task_counts['Suture'] == 1
        assert summary.task_counts['ChickenThigh'] == 1
        assert summary.total_duration == 60.0

    def test_get_export_summary_all_idle(self, export_service):
        annotation = VideoAnnotation(video_path='/test.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Idle', start_time=0, end_time=30),
        ]
        export_service.annotation_repo.load = MagicMock(return_value=annotation)

        result = export_service.get_export_summary('/test.mp4')
        assert result.is_ok()
        assert result.unwrap().total_segments == 0

    def test_get_batch_export_summary(self, export_service):
        annotation1 = VideoAnnotation(video_path='/v1.mp4')
        annotation1.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=20),
        ]
        annotation2 = VideoAnnotation(video_path='/v2.mp4')
        annotation2.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=15),
            TaskSegment(task_name='GloveCut', start_time=15, end_time=30),
        ]

        def mock_load(video_path, version=None):
            return {'/v1.mp4': annotation1, '/v2.mp4': annotation2}.get(video_path)

        export_service.annotation_repo.load = mock_load

        items = [
            VideoItem(video_path='/v1.mp4'),
            VideoItem(video_path='/v2.mp4'),
        ]
        result = export_service.get_batch_export_summary(items)
        assert result.is_ok()
        summary = result.unwrap()
        assert summary.total_segments == 3
        assert summary.task_counts['Suture'] == 2
        assert summary.task_counts['GloveCut'] == 1

    def test_batch_summary_with_missing_annotations(self, export_service):
        annotation = VideoAnnotation(video_path='/v1.mp4')
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=10),
        ]

        def mock_load(video_path, version=None):
            if video_path == '/v1.mp4':
                return annotation
            return None

        export_service.annotation_repo.load = mock_load

        items = [
            VideoItem(video_path='/v1.mp4'),
            VideoItem(video_path='/v2.mp4'),  # No annotation
        ]
        result = export_service.get_batch_export_summary(items)
        assert result.is_ok()
        assert result.unwrap().total_segments == 1
