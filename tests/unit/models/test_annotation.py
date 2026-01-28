"""
Unit tests for app/models/annotation.py - TaskSegment, ParticipantMarker, VideoAnnotation
"""

import pytest

from app.models.annotation import TaskSegment, ParticipantMarker, VideoAnnotation


class TestTaskSegment:

    def test_duration_property(self, sample_task_segment):
        assert sample_task_segment.duration == 15.0

    def test_to_dict(self, sample_task_segment):
        d = sample_task_segment.to_dict()
        assert d['task_name'] == 'Suture'
        assert d['start_time'] == 10.0
        assert d['end_time'] == 25.0
        assert d['confidence'] == 0.95

    def test_from_dict(self):
        data = {'task_name': 'Idle', 'start_time': 0.0, 'end_time': 5.0, 'confidence': 0.8}
        seg = TaskSegment.from_dict(data)
        assert seg.task_name == 'Idle'
        assert seg.start_time == 0.0
        assert seg.end_time == 5.0
        assert seg.confidence == 0.8

    def test_from_dict_default_confidence(self):
        data = {'task_name': 'Suture', 'start_time': 1.0, 'end_time': 2.0}
        seg = TaskSegment.from_dict(data)
        assert seg.confidence == 1.0

    def test_roundtrip(self, sample_task_segment):
        d = sample_task_segment.to_dict()
        restored = TaskSegment.from_dict(d)
        assert restored.task_name == sample_task_segment.task_name
        assert restored.start_time == sample_task_segment.start_time
        assert restored.end_time == sample_task_segment.end_time
        assert restored.confidence == sample_task_segment.confidence


class TestParticipantMarker:

    def test_label_participant(self, sample_participant_marker):
        assert sample_participant_marker.label == 'P1'

    def test_label_expert(self):
        marker = ParticipantMarker(participant_type='E', participant_number=3, timestamp=10.0)
        assert marker.label == 'E3'

    def test_to_dict(self, sample_participant_marker):
        d = sample_participant_marker.to_dict()
        assert d['participant_type'] == 'P'
        assert d['participant_number'] == 1
        assert d['timestamp'] == 5.0
        assert d['duration'] == 3.0
        assert d['confidence'] == 0.9

    def test_from_dict(self):
        data = {
            'participant_type': 'E', 'participant_number': 2,
            'timestamp': 10.0, 'duration': 1.5, 'confidence': 0.7
        }
        marker = ParticipantMarker.from_dict(data)
        assert marker.label == 'E2'
        assert marker.duration == 1.5

    def test_from_dict_defaults(self):
        data = {'participant_type': 'P', 'participant_number': 1, 'timestamp': 0.0}
        marker = ParticipantMarker.from_dict(data)
        assert marker.duration == 0.0
        assert marker.confidence == 1.0

    def test_roundtrip(self, sample_participant_marker):
        d = sample_participant_marker.to_dict()
        restored = ParticipantMarker.from_dict(d)
        assert restored.label == sample_participant_marker.label
        assert restored.timestamp == sample_participant_marker.timestamp


class TestVideoAnnotation:

    def test_to_dict_structure(self, sample_annotation):
        d = sample_annotation.to_dict()
        assert 'version' in d
        assert 'video_path' in d
        assert 'metadata' in d
        assert 'task_segments' in d
        assert 'participant_markers' in d
        assert 'processing' in d
        assert d['metadata']['fps'] == 30.0
        assert d['processing']['processed'] is True

    def test_from_dict(self, sample_annotation):
        d = sample_annotation.to_dict()
        restored = VideoAnnotation.from_dict(d)
        assert restored.video_path == sample_annotation.video_path
        assert restored.version == sample_annotation.version
        assert restored.fps == 30.0
        assert restored.frame_count == 3600
        assert restored.processed is True
        assert len(restored.task_segments) == 4
        assert len(restored.participant_markers) == 2

    def test_from_dict_minimal(self):
        data = {'video_path': '/some/video.mp4'}
        annotation = VideoAnnotation.from_dict(data)
        assert annotation.video_path == '/some/video.mp4'
        assert annotation.version == 1
        assert annotation.task_segments == []
        assert annotation.participant_markers == []

    def test_get_participant_for_task_before_marker(self, sample_annotation):
        # Task starts at 0.0, marker P1 at 2.0 (after), marker E2 at 50.0
        # No marker before 0.0 -> falls back to closest after -> P1
        task = sample_annotation.task_segments[0]  # Suture 0-30
        result = sample_annotation.get_participant_for_task(task)
        assert result == 'P1'

    def test_get_participant_for_task_closest_before(self, sample_annotation):
        # Task starts at 80.0, P1 at 2.0 and E2 at 50.0 are both before
        task = sample_annotation.task_segments[3]  # GloveCut 80-120
        result = sample_annotation.get_participant_for_task(task)
        assert result == 'E2'

    def test_get_participant_for_task_no_markers(self):
        annotation = VideoAnnotation(video_path='/test.mp4')
        task = TaskSegment(task_name='Suture', start_time=10.0, end_time=20.0)
        assert annotation.get_participant_for_task(task) is None
