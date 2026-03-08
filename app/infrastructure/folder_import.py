"""
Folder import utilities for multi-part video logs.

Validates folder structure (partXXXX subfolders with EndoscopeImageMemory_0.avi)
and concatenates parts into a single video using FFmpeg concat demuxer.
"""

import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

from ..domain import Result, Ok, Err
from ..utils.error_handling import VideoError

logger = logging.getLogger(__name__)

PART_PATTERN = re.compile(r'^part(\d+)$', re.IGNORECASE)
VIDEO_FILENAME = 'EndoscopeImageMemory_0.avi'


def validate_folder(folder_path: str) -> Result[List[str], VideoError]:
    """
    Validate that a folder contains the expected multi-part video structure.
    Returns a sorted list of video file paths (one per part).
    """
    folder = Path(folder_path)

    if not folder.is_dir():
        return Err(VideoError(
            f"Not a directory: {folder.name}",
            video_path=folder_path
        ))

    part_dirs = []
    for child in folder.iterdir():
        if child.is_dir() and PART_PATTERN.match(child.name):
            part_dirs.append(child)

    if not part_dirs:
        return Err(VideoError(
            f"No partXXXX subfolders found in:\n{folder.name}\n\n"
            "Expected folder structure:\n"
            "  folder/\n"
            "    part0001/\n"
            "      EndoscopeImageMemory_0.avi\n"
            "    part0002/\n"
            "      EndoscopeImageMemory_0.avi\n"
            "    ...",
            video_path=folder_path
        ))

    # Sort by part number
    part_dirs.sort(key=lambda d: int(PART_PATTERN.match(d.name).group(1)))

    video_paths = []
    missing_parts = []

    for part_dir in part_dirs:
        video_file = part_dir / VIDEO_FILENAME
        if video_file.exists():
            video_paths.append(str(video_file))
        else:
            missing_parts.append(part_dir.name)

    if missing_parts:
        return Err(VideoError(
            f"Missing {VIDEO_FILENAME} in: {', '.join(missing_parts)}",
            video_path=folder_path
        ))

    logger.info(f"Validated folder with {len(video_paths)} parts: {folder.name}")
    return Ok(video_paths)


def concatenate_parts(
    part_paths: List[str],
    output_path: str,
) -> Result[str, VideoError]:
    """
    Concatenate multiple video parts into a single file using FFmpeg concat demuxer.
    Uses -c copy (no re-encoding) for speed.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    concat_list_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, prefix='concat_'
        ) as f:
            concat_list_path = f.name
            for part_path in part_paths:
                safe_path = Path(part_path).as_posix().replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        logger.info(f"Concatenating {len(part_paths)} parts -> {output.name}")

        command = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_path,
            '-c', 'copy',
            str(output_path)
        ]

        logger.debug(f"FFmpeg command: {' '.join(command)}")

        # CREATE_NO_WINDOW prevents a console flash on Windows
        kwargs = {}
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=600,
            **kwargs
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg concat failed with return code {result.returncode}")
            return Err(VideoError(
                f"FFmpeg concatenation failed (exit code {result.returncode})"
            ))

        if not output.exists():
            return Err(VideoError(
                f"Concatenated file was not created",
                details=str(output_path)
            ))

        logger.info(f"Concatenation complete: {output.name}")
        return Ok(str(output_path))

    except FileNotFoundError:
        return Err(VideoError(
            "FFmpeg not found. Please install FFmpeg and ensure it's on your PATH."
        ))
    except Exception as e:
        logger.error(f"Concatenation error: {e}", exc_info=True)
        return Err(VideoError(
            f"Error during concatenation: {str(e)}"
        ))
    finally:
        if concat_list_path:
            try:
                Path(concat_list_path).unlink(missing_ok=True)
            except Exception:
                pass
