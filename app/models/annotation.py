"""
Video annotation data models
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class TaskSegment:
    task_name: str
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float = 1.0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            'task_name': self.task_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'confidence': self.confidence
        }

    @staticmethod
    def from_dict(data: dict) -> 'TaskSegment':
        return TaskSegment(
            task_name=data['task_name'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            confidence=data.get('confidence', 1.0)
        )


@dataclass
class ParticipantMarker:
    participant_type: str  # 'P' for participant or 'E' for expert
    participant_number: int
    timestamp: float  # seconds
    duration: float = 0.0  # how long the card was visible
    confidence: float = 1.0

    @property
    def label(self) -> str:
        return f"{self.participant_type}{self.participant_number}"

    def to_dict(self) -> dict:
        return {
            'participant_type': self.participant_type,
            'participant_number': self.participant_number,
            'timestamp': self.timestamp,
            'duration': self.duration,
            'confidence': self.confidence
        }

    @staticmethod
    def from_dict(data: dict) -> 'ParticipantMarker':
        return ParticipantMarker(
            participant_type=data['participant_type'],
            participant_number=data['participant_number'],
            timestamp=data['timestamp'],
            duration=data.get('duration', 0.0),
            confidence=data.get('confidence', 1.0)
        )


@dataclass
class VideoAnnotation:
    video_path: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Video metadata
    duration: float = 0.0  # seconds
    fps: float = 30.0
    frame_count: int = 0

    # Annotations
    task_segments: List[TaskSegment] = field(default_factory=list)
    participant_markers: List[ParticipantMarker] = field(default_factory=list)

    # Processing status
    processed: bool = False
    model_version: str = "1.0"

    def get_participant_for_task(self, task_segment: TaskSegment) -> Optional[str]:
        """
        Smart fallback: closest marker before task start, then closest after, then None.
        """
        before_markers = [
            m for m in self.participant_markers
            if m.timestamp <= task_segment.start_time
        ]
        if before_markers:
            closest = max(before_markers, key=lambda m: m.timestamp)
            return closest.label

        after_markers = [
            m for m in self.participant_markers
            if m.timestamp > task_segment.start_time
        ]
        if after_markers:
            closest = min(after_markers, key=lambda m: m.timestamp)
            return closest.label

        return None

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'video_path': self.video_path,
            'created_at': self.created_at,
            'modified_at': datetime.now().isoformat(),
            'metadata': {
                'duration': self.duration,
                'fps': self.fps,
                'frame_count': self.frame_count
            },
            'task_segments': [seg.to_dict() for seg in self.task_segments],
            'participant_markers': [marker.to_dict() for marker in self.participant_markers],
            'processing': {
                'processed': self.processed,
                'model_version': self.model_version
            }
        }

    @staticmethod
    def from_dict(data: dict) -> 'VideoAnnotation':
        metadata = data.get('metadata', {})
        processing = data.get('processing', {})

        annotation = VideoAnnotation(
            video_path=data['video_path'],
            version=data.get('version', 1),
            created_at=data.get('created_at', datetime.now().isoformat()),
            modified_at=data.get('modified_at', datetime.now().isoformat()),
            duration=metadata.get('duration', 0.0),
            fps=metadata.get('fps', 30.0),
            frame_count=metadata.get('frame_count', 0),
            processed=processing.get('processed', False),
            model_version=processing.get('model_version', '1.0')
        )

        annotation.task_segments = [
            TaskSegment.from_dict(seg)
            for seg in data.get('task_segments', [])
        ]

        annotation.participant_markers = [
            ParticipantMarker.from_dict(marker)
            for marker in data.get('participant_markers', [])
        ]

        return annotation
