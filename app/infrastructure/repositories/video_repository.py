"""
Video repository - persistent storage of video items with in-memory cache
"""

import json
import logging
import threading
from pathlib import Path
from typing import List, Optional, Protocol

from ...models.video_item import VideoItem
from ...core.config import PathConfig

logger = logging.getLogger(__name__)


class IVideoRepository(Protocol):
    def get_all(self) -> List[VideoItem]: ...
    def add(self, video_item: VideoItem) -> bool: ...
    def remove(self, video_path: str) -> bool: ...
    def find_by_path(self, video_path: str) -> Optional[VideoItem]: ...
    def update_status(self, video_path: str, processed: bool, annotation_version: Optional[int] = None) -> bool: ...


class VideoRepository:
    """
    Persistent video item storage backed by JSON with in-memory cache.
    All reads hit the cache; writes persist to disk atomically.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or PathConfig.get_registry_path()
        self._lock = threading.Lock()
        self._cache: Optional[List[VideoItem]] = None

    def _load_from_disk(self) -> List[VideoItem]:
        if not self.registry_path.exists():
            return []

        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)

            video_items = []

            for item_data in data.get('videos', []):
                video_path = item_data.get('video_path')
                if not video_path or not Path(video_path).exists():
                    continue

                video_items.append(VideoItem(
                    video_path=video_path,
                    thumbnail_path=item_data.get('thumbnail_path'),
                    processed=item_data.get('processed', False),
                    duration=item_data.get('duration', 0.0),
                    fps=item_data.get('fps', 0.0),
                    annotation_version=item_data.get('annotation_version')
                ))

            logger.info(f"Loaded {len(video_items)} videos from registry")
            return video_items

        except json.JSONDecodeError as e:
            logger.error(f"Registry file corrupted: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading registry: {e}", exc_info=True)
            return []

    def _ensure_cache(self) -> List[VideoItem]:
        if self._cache is None:
            self._cache = self._load_from_disk()
        return self._cache

    def _persist(self, video_items: List[VideoItem]) -> bool:
        try:
            videos_data = [{
                'video_path': item.video_path,
                'thumbnail_path': item.thumbnail_path,
                'processed': item.processed,
                'duration': item.duration,
                'fps': item.fps,
                'annotation_version': item.annotation_version
            } for item in video_items]

            data = {'version': 1, 'videos': videos_data}

            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.registry_path.with_suffix('.tmp')

            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            temp_path.replace(self.registry_path)
            return True

        except Exception as e:
            logger.error(f"Error saving registry: {e}", exc_info=True)
            return False

    def get_all(self) -> List[VideoItem]:
        with self._lock:
            return list(self._ensure_cache())

    def add(self, video_item: VideoItem) -> bool:
        with self._lock:
            items = self._ensure_cache()
            for i, item in enumerate(items):
                if item.video_path == video_item.video_path:
                    items[i] = video_item
                    logger.info(f"Updated video in registry: {video_item.filename}")
                    return self._persist(items)

            items.append(video_item)
            logger.info(f"Added video to registry: {video_item.filename}")
            return self._persist(items)

    def remove(self, video_path: str) -> bool:
        with self._lock:
            items = self._ensure_cache()
            original_count = len(items)
            self._cache = [item for item in items if item.video_path != video_path]

            if len(self._cache) < original_count:
                logger.info(f"Removed from registry: {Path(video_path).name}")
                return self._persist(self._cache)

            logger.warning(f"Video not found in registry: {video_path}")
            return False

    def find_by_path(self, video_path: str) -> Optional[VideoItem]:
        with self._lock:
            for item in self._ensure_cache():
                if item.video_path == video_path:
                    return item
            return None

    def update_status(self, video_path: str, processed: bool, annotation_version: Optional[int] = None) -> bool:
        with self._lock:
            for item in self._ensure_cache():
                if item.video_path == video_path:
                    item.processed = processed
                    if annotation_version is not None:
                        item.annotation_version = annotation_version
                    logger.info(f"Updated status: {Path(video_path).name} processed={processed}")
                    return self._persist(self._cache)

            logger.warning(f"Video not found in registry: {video_path}")
            return False

    def clear_all(self) -> bool:
        with self._lock:
            self._cache = []
            return self._persist([])
