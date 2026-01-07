"""
Export service - handles video export operations
Coordinates export workflow and calculates export summaries
"""

import logging
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

from ...models.video_item import VideoItem
from ...infrastructure.repositories.annotation_repository import AnnotationRepository
from ...core.config import AppConfig
from ...domain import Result, Ok, Err
from ...utils.error_handling import ExportError

logger = logging.getLogger(__name__)


@dataclass
class ExportSummary:
    """Summary of segments to be exported"""
    total_segments: int
    task_counts: Dict[str, int]  # task_name -> count
    total_duration: float  # Total duration in seconds

    def get_breakdown_text(self) -> str:
        lines = []
        for task, count in sorted(self.task_counts.items()):
            lines.append(f"  • {task}: {count} clip(s)")
        return "\n".join(lines)


class ExportService:
    """Service for managing video export operations"""

    def __init__(self, annotation_repo: AnnotationRepository, config: AppConfig):
        self.annotation_repo = annotation_repo
        self.config = config

    def get_export_summary(self, video_path: str) -> Result[ExportSummary, ExportError]:
        annotation = self.annotation_repo.load(video_path)

        if annotation is None:
            error = ExportError(
                f"No annotation found for video",
                details=f"Cannot export without annotation for {Path(video_path).name}"
            )
            logger.warning(f"No annotation for export: {video_path}")
            return Err(error)

        task_counts = {}
        total_duration = 0.0

        for segment in annotation.task_segments:
            if segment.task_name.lower() != 'idle':
                task_counts[segment.task_name] = task_counts.get(segment.task_name, 0) + 1
                duration = segment.end_time - segment.start_time
                total_duration += duration

        summary = ExportSummary(
            total_segments=sum(task_counts.values()),
            task_counts=task_counts,
            total_duration=total_duration
        )

        logger.debug(f"Export summary for {Path(video_path).name}: {summary.total_segments} segments")
        return Ok(summary)

    def get_batch_export_summary(self, video_items: List[VideoItem]) -> Result[ExportSummary, ExportError]:
        total_segments = 0
        combined_task_counts = {}
        total_duration = 0.0

        for video_item in video_items:
            result = self.get_export_summary(video_item.video_path)

            if result.is_ok():
                summary = result.unwrap()
                total_segments += summary.total_segments
                total_duration += summary.total_duration

                for task, count in summary.task_counts.items():
                    combined_task_counts[task] = combined_task_counts.get(task, 0) + count

        combined_summary = ExportSummary(
            total_segments=total_segments,
            task_counts=combined_task_counts,
            total_duration=total_duration
        )

        logger.info(f"Batch export summary: {total_segments} segments from {len(video_items)} videos")
        return Ok(combined_summary)

