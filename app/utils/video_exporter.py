"""
Video exporter for chopping videos by task segments
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from ..models.annotation import VideoAnnotation, TaskSegment

logger = logging.getLogger(__name__)


class VideoExporter:
    """Exports video clips based on task segments"""

    def __init__(self, video_path: str, annotation: VideoAnnotation, output_dir: str):
        self.video_path = video_path
        self.annotation = annotation
        self.output_dir = Path(output_dir)

    def export_all_segments(self, progress_callback=None) -> List[str]:
        segments_to_export = [
            seg for seg in self.annotation.task_segments
            if seg.task_name.lower() != 'idle'
        ]

        if not segments_to_export:
            return []

        exported_files = []
        total = len(segments_to_export)

        # Track used filenames to ensure uniqueness across task/participant combinations
        used_filenames = {}  # Key: (task_name, participant_label), Value: next available index

        for i, segment in enumerate(segments_to_export):
            participant_label = self.annotation.get_participant_for_task(segment)
            if not participant_label:
                participant_label = "None"

            task_dir = self.output_dir / segment.task_name
            task_dir.mkdir(parents=True, exist_ok=True)

            filename_key = (segment.task_name, participant_label)

            if filename_key not in used_filenames:
                index = 1
            else:
                index = used_filenames[filename_key]

            MAX_RETRIES = 10000  # Prevent infinite loop
            retry_count = 0
            while retry_count < MAX_RETRIES:
                filename = f"{segment.task_name}_{participant_label}_{index}.mp4"
                output_path = task_dir / filename

                if not output_path.exists():
                    used_filenames[filename_key] = index + 1
                    break

                index += 1
                retry_count += 1

            if retry_count >= MAX_RETRIES:
                logger.error(f"Could not find available filename after {MAX_RETRIES} attempts")
                continue  # Skip this segment

            current_clip = i + 1
            if progress_callback:
                progress_callback(current_clip, total, f"Exporting {filename}")

            success = self._export_segment(segment, output_path)

            if success:
                exported_files.append(str(output_path))
            else:
                logger.error(f"Failed to export: {filename}")

        if progress_callback:
            progress_callback(total, total, "Export complete")

        return exported_files

    def _export_segment(self, segment: TaskSegment, output_path: Path) -> bool:
        try:
            duration = segment.end_time - segment.start_time

            if duration <= 0:
                logger.warning(f"Invalid segment duration: {duration}s (start: {segment.start_time}, end: {segment.end_time})")
                return False

            # Using list format for subprocess.run automatically handles path escaping
            command = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-ss', f'{segment.start_time:.3f}',  # Seek to start (with precision)
                '-i', str(self.video_path),  # Input file
                '-t', f'{duration:.3f}',  # Duration (with precision)
                '-c', 'copy',  # Copy codec (fast, no re-encoding)
                '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
                str(output_path)
            ]

            logger.debug(f"Running ffmpeg command: {' '.join(command)}")

            # Run ffmpeg with shorter timeout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout per clip (reduced from 5 minutes)
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error (return code {result.returncode})")
                logger.debug(f"STDOUT: {result.stdout}")
                logger.debug(f"STDERR: {result.stderr}")
                return False

            if not output_path.exists():
                logger.error(f"Output file was not created: {output_path}")
                return False

            logger.info(f"Successfully exported: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout after 60 seconds for segment {segment.task_name}")
            return False
        except Exception as e:
            logger.error(f"Error exporting segment: {e}", exc_info=True)
            return False


