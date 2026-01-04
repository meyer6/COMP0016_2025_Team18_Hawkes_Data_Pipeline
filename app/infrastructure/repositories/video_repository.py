"""Video repository - persistent storage of video items"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from ...models.video_item import VideoItem
from ...core.config import PathConfig

logger = logging.getLogger(__name__)


class VideoRepository:
    """Persistent video item storage backed by JSON."""

    def __init__(self, registry_path=None):
        self.registry_path = registry_path or PathConfig.get_registry_path()
        self._cache = None

    def _load_from_disk(self) -> List[VideoItem]:
        if not self.registry_path.exists():
            return []
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            items = []
            for d in data.get('videos', []):
                video_path = d.get('video_path')
                if not video_path:
                    continue
                items.append(VideoItem(
                    video_path=video_path,
                    thumbnail_path=d.get('thumbnail_path'),
                    processed=d.get('processed', False),
                    duration=d.get('duration', 0.0),
                    fps=d.get('fps', 0.0),
                    annotation_version=d.get('annotation_version')
                ))
            logger.info(f"Loaded {len(items)} videos from registry")
            return items
        except json.JSONDecodeError as e:
            logger.error(f"Registry file corrupted: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            return []

    def _ensure_cache(self):
        if self._cache is None:
            self._cache = self._load_from_disk()
        return self._cache

    def _persist(self, items) -> bool:
        try:
            data = {'version': 1, 'videos': [{
                'video_path': i.video_path,
                'thumbnail_path': i.thumbnail_path,
                'processed': i.processed,
                'duration': i.duration,
                'fps': i.fps,
                'annotation_version': i.annotation_version
            } for i in items]}
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
            return False

    def get_all(self) -> List[VideoItem]:
        return list(self._ensure_cache())

    def add(self, video_item: VideoItem) -> bool:
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
        items = self._ensure_cache()
        original = len(items)
        self._cache = [i for i in items if i.video_path != video_path]
        if len(self._cache) < original:
            logger.info(f"Removed from registry: {Path(video_path).name}")
            return self._persist(self._cache)
        logger.warning(f"Video not found in registry: {video_path}")
        return False

    def find_by_path(self, video_path: str) -> Optional[VideoItem]:
        for item in self._ensure_cache():
            if item.video_path == video_path:
                return item
        return None

    def update_status(self, video_path: str, processed: bool, annotation_version=None) -> bool:
        for item in self._ensure_cache():
            if item.video_path == video_path:
                item.processed = processed
                if annotation_version is not None:
                    item.annotation_version = annotation_version
                logger.info(f"Updated status: {Path(video_path).name} processed={processed}")
                return self._persist(self._cache)
        logger.warning(f"Video not found: {video_path}")
        return False

    def clear_all(self) -> bool:
        self._cache = []
        return self._persist([])
