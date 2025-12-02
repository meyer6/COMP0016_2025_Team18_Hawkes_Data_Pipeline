"""Participant detector - basic OCR-based detection (no threading)"""

import cv2
import logging
import re
import easyocr
from collections import Counter
from itertools import chain
from typing import Optional, Tuple, List, Dict

from ..infrastructure.video_utils import get_video_metadata, open_video_capture
from ..utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)

FRAME_SKIP = 10
CARD_TIMEOUT_FRAMES = 5
SCENE_CHANGE_THRESHOLD = 8.0
OCR_ALLOWLIST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


class ParticipantDetector:

    def __init__(self, gpu=True):
        self.reader = easyocr.Reader(["en"], gpu=gpu)

    @staticmethod
    def _levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return ParticipantDetector._levenshtein_distance(s2, s1)
        if not s2:
            return len(s1)
        prev = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
            prev = curr
        return prev[-1]

    @staticmethod
    def _parse_card(text):
        words = re.findall(r"[A-Za-z]+|[0-9]+", text)
        for i, word in enumerate(words):
            if len(word) < 5:
                continue
            d_p = ParticipantDetector._levenshtein_distance(word.lower(), "participant")
            d_e = ParticipantDetector._levenshtein_distance(word.lower(), "expert")
            if d_p <= 3 or d_e <= 3:
                for j in range(i + 1, len(words)):
                    if words[j].isdigit():
                        role = "participant" if d_p <= d_e else "expert"
                        return (role, int(words[j]))
        return None

    def process_video(self, video_path, frame_skip=FRAME_SKIP,
                      card_timeout_frames=CARD_TIMEOUT_FRAMES,
                      progress_callback=None, **kwargs):
        metadata_result = get_video_metadata(video_path)
        if metadata_result.is_err():
            error = metadata_result.unwrap_err()
            raise ProcessingError(f"Failed to read video metadata: {error.message}", details=error.details)
        metadata = metadata_result.unwrap()
        fps = metadata.fps
        total_frames = metadata.frame_count

        cap_result = open_video_capture(video_path)
        if cap_result.is_err():
            raise ProcessingError(f"Cannot open video: {video_path}")
        cap = cap_result.unwrap()

        detections = []
        session_start = None
        session_detections = []
        misses = 0
        n = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if n % frame_skip != 0:
                n += 1
                continue

            h, w = frame.shape[:2]
            if h > 480:
                scale = 480 / h
                frame = cv2.resize(frame, (int(w * scale), 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            text = self.reader.readtext(gray, detail=0, paragraph=True, allowlist=OCR_ALLOWLIST)
            result = self._parse_card(" ".join(text) if isinstance(text, list) else text)

            if result:
                if session_start is None:
                    session_start = n
                    session_detections = []
                session_detections.append(result)
                misses = 0
            elif session_start is not None:
                misses += 1
                if misses >= card_timeout_frames:
                    card_type, number = Counter(session_detections).most_common(1)[0][0]
                    detections.append({
                        "participant_type": "P" if card_type == "participant" else "E",
                        "participant_number": number,
                        "timestamp": session_start / fps,
                        "duration": round((n - session_start) / fps, 2),
                        "confidence": 1.0,
                    })
                    session_start = None
                    misses = 0

            if progress_callback:
                progress_callback(n, total_frames)
            n += 1

        cap.release()
        if progress_callback:
            progress_callback(total_frames, total_frames)
        logger.info(f"Found {len(detections)} participant cards")
        return detections
