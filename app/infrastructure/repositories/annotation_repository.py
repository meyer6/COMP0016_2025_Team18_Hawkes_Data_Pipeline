"""
Annotation repository - replaces AnnotationIO with proper repository pattern
Separates path resolution from I/O operations
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Protocol

from ...models.annotation import VideoAnnotation
from ...domain import Result, Ok, Err
from ...utils.error_handling import AnnotationError, AnnotationNotFoundError, AnnotationParseError

logger = logging.getLogger(__name__)


class IAnnotationRepository(Protocol):

    def load(self, video_path: str, version: Optional[int] = None) -> Optional[VideoAnnotation]: ...

    def save(self, annotation: VideoAnnotation, create_new_version: bool = False) -> str: ...

    def list_versions(self, video_path: str) -> List[int]: ...


class AnnotationRepository:
    """
    Repository for managing video annotations.
    Replaces the old AnnotationIO with better separation of concerns.
    """

    @staticmethod
    def get_annotation_path(video_path: str, version: Optional[int] = None) -> str:
        video_file = Path(video_path)
        base_name = video_file.stem
        video_dir = video_file.parent

        if version is None:
            return str(video_dir / f"{base_name}_annotations_v*.json")
        else:
            return str(video_dir / f"{base_name}_annotations_v{version}.json")

    @staticmethod
    def find_latest_version(video_path: str) -> Optional[int]:
        video_file = Path(video_path)
        base_name = video_file.stem
        video_dir = video_file.parent

        pattern = f"{base_name}_annotations_v*.json"
        versions = []

        for file in video_dir.glob(pattern):
            try:
                version_str = file.stem.split('_v')[-1]
                versions.append(int(version_str))
            except (ValueError, IndexError):
                logger.warning(f"Invalid annotation filename format: {file.name}")
                continue

        return max(versions) if versions else None

    def load(self, video_path: str, version: Optional[int] = None) -> Optional[VideoAnnotation]:
        if version is None:
            version = self.find_latest_version(video_path)
            if version is None:
                logger.debug(f"No annotations found for {Path(video_path).name}")
                return None

        annotation_path = self.get_annotation_path(video_path, version)

        if not Path(annotation_path).exists():
            logger.debug(f"Annotation file not found: {annotation_path}")
            return None

        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            annotation = VideoAnnotation.from_dict(data)
            logger.info(f"Loaded annotation v{version} for {Path(video_path).name}")
            return annotation

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in annotation file {annotation_path}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Missing required field in annotation file {annotation_path}: {e}")
            return None
        except IOError as e:
            logger.error(f"Unable to read annotation file {annotation_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading annotation from {annotation_path}: {e}", exc_info=True)
            return None

    def save(self, annotation: VideoAnnotation, create_new_version: bool = False) -> str:
        try:
            if create_new_version:
                # Find latest version and increment
                latest_version = self.find_latest_version(annotation.video_path)
                new_version = (latest_version or 1) + 1
                annotation.version = new_version
            else:
                # Use existing version or default to 1
                if annotation.version is None:
                    annotation.version = 1

            annotation_path = self.get_annotation_path(
                annotation.video_path,
                annotation.version
            )

            Path(annotation_path).parent.mkdir(parents=True, exist_ok=True)

            temp_path = Path(annotation_path).with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(annotation.to_dict(), f, indent=2)

            # Atomic rename
            temp_path.replace(annotation_path)

            logger.info(f"Saved annotation v{annotation.version} for {Path(annotation.video_path).name}")
            return annotation_path

        except IOError as e:
            logger.error(f"Failed to save annotation to {annotation_path}: {e}")
            raise IOError(f"Failed to save annotation to {annotation_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving annotation: {e}", exc_info=True)
            raise AnnotationError(f"Unexpected error saving annotation: {e}")

    def list_versions(self, video_path: str) -> List[int]:
        video_file = Path(video_path)
        base_name = video_file.stem
        video_dir = video_file.parent

        pattern = f"{base_name}_annotations_v*.json"
        versions = []

        for file in video_dir.glob(pattern):
            try:
                version_str = file.stem.split('_v')[-1]
                versions.append(int(version_str))
            except (ValueError, IndexError):
                logger.warning(f"Invalid annotation filename format: {file.name}")
                continue

        return sorted(versions)

    def delete_all_versions(self, video_path: str) -> Result[int, AnnotationError]:
        versions = self.list_versions(video_path)
        deleted_count = 0

        for version in versions:
            annotation_path = Path(self.get_annotation_path(video_path, version))
            try:
                if annotation_path.exists():
                    annotation_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted annotation v{version} for {Path(video_path).name}")
            except Exception as e:
                logger.error(f"Error deleting annotation v{version}: {e}")

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} annotation files for {Path(video_path).name}")

        return Ok(deleted_count)
