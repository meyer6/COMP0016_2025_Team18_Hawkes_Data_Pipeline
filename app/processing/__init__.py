"""
Video processing module
"""

from .task_classifier import TaskClassifier
from .participant_detector import ParticipantDetector
from .video_processor import VideoProcessor

__all__ = ['TaskClassifier', 'ParticipantDetector', 'VideoProcessor']
