"""Video repository - in-memory storage of video items"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from ...models.video_item import VideoItem
from ...core.config import PathConfig

logger = logging.getLogger(__name__)


class VideoRepository:
    """Simple in-memory video item storage."""

    def __init__(self, registry_path=None):
        self.registry_path = registry_path or PathConfig.get_registry_path()
        self._items: List[VideoItem] = []

    def get_all(self) -> List[VideoItem]:
        return list(self._items)

    def add(self, video_item: VideoItem) -> bool:
        for i, item in enumerate(self._items):
            if item.video_path == video_item.video_path:
                self._items[i] = video_item
                return True
        self._items.append(video_item)
        return True

    def remove(self, video_path: str) -> bool:
        original = len(self._items)
        self._items = [i for i in self._items if i.video_path != video_path]
        return len(self._items) < original

    def find_by_path(self, video_path: str) -> Optional[VideoItem]:
        for item in self._items:
            if item.video_path == video_path:
                return item
        return None

    def update_status(self, video_path: str, processed: bool, annotation_version=None) -> bool:
        for item in self._items:
            if item.video_path == video_path:
                item.processed = processed
                if annotation_version is not None:
                    item.annotation_version = annotation_version
                return True
        return False

    def clear_all(self) -> bool:
        self._items = []
        return True
