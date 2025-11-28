"""
Application constants including task names, colours, and file extensions
"""

from enum import Enum
from PyQt6.QtGui import QColor
from typing import Dict


class TaskName(str, Enum):
    CAMERA_TARGET = 'CameraTarget'
    CHICKEN_THIGH = 'ChickenThigh'
    CYST_MODEL = 'CystModel'
    GLOVE_CUT = 'GloveCut'
    IDLE = 'Idle'
    MOVING_INDIVIDUAL_AXES = 'MovingIndividualAxes'
    RING_ROLLERCOASTER = 'RingRollercoaster'
    SEA_SPIKES = 'SeaSpikes'
    SUTURE = 'Suture'

    @classmethod
    def get_all_names(cls) -> list[str]:
        return [task.value for task in cls]

    @classmethod
    def is_valid(cls, task_name: str) -> bool:
        return task_name in cls.get_all_names()


class TaskColors:
    """Task colour scheme - vibrant and modern colours"""

    COLORS: Dict[str, QColor] = {
        TaskName.CAMERA_TARGET.value: QColor('#2f81f7'),           # Bright blue
        TaskName.CHICKEN_THIGH.value: QColor('#d29922'),           # Orange/amber
        TaskName.CYST_MODEL.value: QColor('#e85aad'),              # Pink
        TaskName.GLOVE_CUT.value: QColor('#f85149'),               # Bright red
        TaskName.IDLE.value: QColor('#6e7681'),                    # Grey
        TaskName.MOVING_INDIVIDUAL_AXES.value: QColor('#a371f7'),  # Purple
        TaskName.RING_ROLLERCOASTER.value: QColor('#1f6feb'),      # Deep blue
        TaskName.SEA_SPIKES.value: QColor('#26a641'),              # Teal green
        TaskName.SUTURE.value: QColor('#3fb950')                   # Bright green
    }

    DEFAULT_COLOR = QColor('#999999')  # Default grey for unknown tasks

    @classmethod
    def get_color(cls, task_name: str) -> QColor:
        return cls.COLORS.get(task_name, cls.DEFAULT_COLOR)

    @classmethod
    def get_all_colors(cls) -> Dict[str, QColor]:
        return cls.COLORS.copy()


class FileExtensions:
    """Supported file extensions"""

    # Video formats
    VIDEO_EXTENSIONS = [
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'
    ]

    # Image formats (for thumbnails)
    IMAGE_EXTENSIONS = [
        '.jpg', '.jpeg', '.png', '.bmp', '.gif'
    ]

    # Annotation files
    ANNOTATION_EXTENSION = '.json'

    @classmethod
    def is_video_file(cls, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in cls.VIDEO_EXTENSIONS)

    @classmethod
    def is_image_file(cls, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in cls.IMAGE_EXTENSIONS)

    @classmethod
    def get_video_filter(cls) -> str:
        exts = ' '.join(f'*{ext}' for ext in cls.VIDEO_EXTENSIONS)
        return f"Video Files ({exts})"


class ProcessingDefaults:
    """Default values for video processing"""

    # Frame sampling rate (process every Nth frame, 30 = 1fps at 30fps video)
    SAMPLE_EVERY = 30

    # Smoothing window for task predictions
    SMOOTHING_WINDOW = 15

    # Minimum task segment duration in seconds
    MIN_DURATION_SEC = 5

    # Confidence threshold for predictions
    CONFIDENCE_THRESHOLD = 0.5

    # Thumbnail generation
    THUMBNAIL_WIDTH = 400
    THUMBNAIL_HEIGHT = 300
    THUMBNAIL_QUALITY = 85

    # Video processing
    MAX_FRAMES_IN_MEMORY = 1000
    DEFAULT_FPS = 30.0


class UIConstants:
    """UI-related constants"""

    # Grid view
    GRID_COLUMNS = 3
    THUMBNAIL_SIZE = (400, 300)

    # Timeline
    TIMELINE_MIN_HEIGHT = 200
    TIMELINE_HANDLE_WIDTH = 4

    # Progress dialog
    PROGRESS_UPDATE_INTERVAL_MS = 100

    # Window geometry
    DEFAULT_WINDOW_WIDTH = 1400
    DEFAULT_WINDOW_HEIGHT = 900
