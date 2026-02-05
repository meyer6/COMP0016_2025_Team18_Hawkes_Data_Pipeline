"""
Integration tests for annotation save-load-version cycle
"""

import pytest
from pathlib import Path

from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.models.annotation import VideoAnnotation, TaskSegment, ParticipantMarker


@pytest.mark.integration
class TestAnnotationFlow:

    def test_save_load_version_cycle(self, temp_dir):
        repo = AnnotationRepository()
        video_path = str(temp_dir / 'video.mp4')

        # Save v1
        ann_v1 = VideoAnnotation(video_path=video_path, version=1, duration=60.0)
        ann_v1.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=30, confidence=0.9),
        ]
        ann_v1.participant_markers = [
            ParticipantMarker(participant_type='P', participant_number=1, timestamp=5.0),
        ]
        repo.save(ann_v1)

        # Save v2 with new version
        ann_v2 = VideoAnnotation(video_path=video_path, duration=60.0)
        ann_v2.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=25),
            TaskSegment(task_name='ChickenThigh', start_time=25, end_time=60),
        ]
        repo.save(ann_v2, create_new_version=True)

        # Verify versions exist
        versions = repo.list_versions(video_path)
        assert versions == [1, 2]

        # Load latest (should be v2)
        loaded = repo.load(video_path)
        assert loaded.version == 2
        assert len(loaded.task_segments) == 2

        # Load specific version
        loaded_v1 = repo.load(video_path, version=1)
        assert loaded_v1.version == 1
        assert len(loaded_v1.task_segments) == 1

    def test_delete_then_load(self, temp_dir):
        repo = AnnotationRepository()
        video_path = str(temp_dir / 'video.mp4')

        # Save two versions
        ann = VideoAnnotation(video_path=video_path, version=1)
        repo.save(ann)
        ann2 = VideoAnnotation(video_path=video_path)
        repo.save(ann2, create_new_version=True)

        # Delete all
        result = repo.delete_all_versions(video_path)
        assert result.is_ok()
        assert result.unwrap() == 2

        # Load should return None
        assert repo.load(video_path) is None
        assert repo.list_versions(video_path) == []
