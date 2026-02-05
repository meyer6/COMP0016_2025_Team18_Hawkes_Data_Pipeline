"""
Unit tests for app/infrastructure/repositories/annotation_repository.py
"""

import json
import pytest
from pathlib import Path

from app.infrastructure.repositories.annotation_repository import AnnotationRepository
from app.models.annotation import VideoAnnotation, TaskSegment, ParticipantMarker


class TestAnnotationRepository:

    def test_get_annotation_path_with_version(self, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        path = AnnotationRepository.get_annotation_path(video_path, version=1)
        assert path.endswith('video_annotations_v1.json')

    def test_get_annotation_path_wildcard(self, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        path = AnnotationRepository.get_annotation_path(video_path)
        assert '*' in path

    def test_find_latest_version_empty(self, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        assert AnnotationRepository.find_latest_version(video_path) is None

    def test_find_latest_version(self, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        # Create version files
        for v in [1, 2, 3]:
            path = temp_dir / f'video_annotations_v{v}.json'
            path.write_text('{}')

        assert AnnotationRepository.find_latest_version(video_path) == 3

    def test_save_and_load(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=1)
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=10)
        ]

        saved_path = annotation_repository.save(annotation)
        assert Path(saved_path).exists()

        loaded = annotation_repository.load(video_path, version=1)
        assert loaded is not None
        assert loaded.video_path == video_path
        assert len(loaded.task_segments) == 1

    def test_save_creates_new_version(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')

        annotation = VideoAnnotation(video_path=video_path, version=1)
        annotation_repository.save(annotation)

        annotation2 = VideoAnnotation(video_path=video_path)
        annotation_repository.save(annotation2, create_new_version=True)
        assert annotation2.version == 2

    def test_save_atomic_write(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=1)
        saved_path = annotation_repository.save(annotation)

        # No temp files should remain
        tmp_files = list(temp_dir.glob('*.tmp'))
        assert len(tmp_files) == 0

    def test_load_nonexistent_returns_none(self, annotation_repository, temp_dir):
        result = annotation_repository.load(str(temp_dir / 'nofile.mp4'))
        assert result is None

    def test_load_corrupt_json(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        annotation_file = temp_dir / 'video_annotations_v1.json'
        annotation_file.write_text('not valid json {{{')

        result = annotation_repository.load(video_path, version=1)
        assert result is None

    def test_list_versions_empty(self, annotation_repository, temp_dir):
        versions = annotation_repository.list_versions(str(temp_dir / 'video.mp4'))
        assert versions == []

    def test_list_versions(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        for v in [3, 1, 2]:
            ann = VideoAnnotation(video_path=video_path, version=v)
            annotation_repository.save(ann)

        versions = annotation_repository.list_versions(video_path)
        assert versions == [1, 2, 3]

    def test_delete_all_versions(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        for v in [1, 2]:
            ann = VideoAnnotation(video_path=video_path, version=v)
            annotation_repository.save(ann)

        result = annotation_repository.delete_all_versions(video_path)
        assert result.is_ok()
        assert result.unwrap() == 2

        versions = annotation_repository.list_versions(video_path)
        assert versions == []

    def test_delete_all_versions_none_exist(self, annotation_repository, temp_dir):
        result = annotation_repository.delete_all_versions(str(temp_dir / 'nofile.mp4'))
        assert result.is_ok()
        assert result.unwrap() == 0

    def test_find_latest_version_invalid_filename(self, temp_dir):
        """Lines 57-59: invalid annotation filename skipped"""
        video_path = str(temp_dir / 'video.mp4')
        # Create a file with invalid version format
        bad_file = temp_dir / 'video_annotations_vXYZ.json'
        bad_file.write_text('{}')
        assert AnnotationRepository.find_latest_version(video_path) is None

    def test_load_specific_version_not_found(self, annotation_repository, temp_dir):
        """Lines 73-74: specific version doesn't exist on disk"""
        video_path = str(temp_dir / 'video.mp4')
        result = annotation_repository.load(video_path, version=99)
        assert result is None

    def test_load_key_error(self, annotation_repository, temp_dir):
        """Lines 87-89: KeyError in from_dict"""
        video_path = str(temp_dir / 'video.mp4')
        annotation_file = temp_dir / 'video_annotations_v1.json'
        # Missing required 'video_path' key
        annotation_file.write_text('{"task_segments": "bad"}')
        result = annotation_repository.load(video_path, version=1)
        assert result is None

    def test_load_io_error(self, annotation_repository, temp_dir):
        """Lines 90-92: IOError reading annotation file"""
        from unittest.mock import patch
        video_path = str(temp_dir / 'video.mp4')
        annotation_file = temp_dir / 'video_annotations_v1.json'
        annotation_file.write_text('{}')

        with patch('builtins.open', side_effect=IOError("disk error")):
            result = annotation_repository.load(video_path, version=1)
            assert result is None

    def test_load_generic_exception(self, annotation_repository, temp_dir):
        """Lines 93-95: generic Exception in load"""
        from unittest.mock import patch
        video_path = str(temp_dir / 'video.mp4')
        annotation_file = temp_dir / 'video_annotations_v1.json'
        annotation_file.write_text('{"video_path": "/test.mp4"}')

        with patch('app.models.annotation.VideoAnnotation.from_dict', side_effect=TypeError("bad")):
            result = annotation_repository.load(video_path, version=1)
            assert result is None

    def test_save_version_none_defaults_to_1(self, annotation_repository, temp_dir):
        """Line 107: annotation.version is None defaults to 1"""
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=None)
        annotation_repository.save(annotation)
        assert annotation.version == 1

    def test_save_io_error(self, annotation_repository, temp_dir):
        """Lines 126-128: IOError in save"""
        from unittest.mock import patch
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=1)

        with patch('builtins.open', side_effect=IOError("disk full")):
            with pytest.raises(IOError):
                annotation_repository.save(annotation)

    def test_save_generic_exception(self, annotation_repository, temp_dir):
        """Lines 129-131: generic Exception in save"""
        from unittest.mock import patch
        from app.utils.error_handling import AnnotationError
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=1)

        with patch.object(VideoAnnotation, 'to_dict', side_effect=RuntimeError("bad")):
            with pytest.raises(AnnotationError):
                annotation_repository.save(annotation)

    def test_list_versions_invalid_filename(self, annotation_repository, temp_dir):
        """Lines 145-147: invalid filename in list_versions"""
        video_path = str(temp_dir / 'video.mp4')
        bad_file = temp_dir / 'video_annotations_vXYZ.json'
        bad_file.write_text('{}')
        versions = annotation_repository.list_versions(video_path)
        assert versions == []

    def test_delete_all_versions_unlink_error(self, annotation_repository, temp_dir):
        """Lines 162-163: exception during unlink in delete_all_versions"""
        from unittest.mock import patch
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(video_path=video_path, version=1)
        annotation_repository.save(annotation)

        with patch.object(Path, 'unlink', side_effect=PermissionError("locked")):
            result = annotation_repository.delete_all_versions(video_path)
            assert result.is_ok()
            assert result.unwrap() == 0

    def test_version_roundtrip(self, annotation_repository, temp_dir):
        video_path = str(temp_dir / 'video.mp4')
        annotation = VideoAnnotation(
            video_path=video_path,
            version=1,
            duration=60.0,
            fps=30.0,
            frame_count=1800,
            processed=True
        )
        annotation.task_segments = [
            TaskSegment(task_name='Suture', start_time=0, end_time=30, confidence=0.9),
        ]
        annotation.participant_markers = [
            ParticipantMarker(participant_type='P', participant_number=1, timestamp=5.0),
        ]

        annotation_repository.save(annotation)
        loaded = annotation_repository.load(video_path, version=1)

        assert loaded.duration == 60.0
        assert loaded.fps == 30.0
        assert loaded.processed is True
        assert len(loaded.task_segments) == 1
        assert loaded.task_segments[0].confidence == 0.9
        assert len(loaded.participant_markers) == 1
        assert loaded.participant_markers[0].label == 'P1'
