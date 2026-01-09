import cv2
import logging
import re
import easyocr
from threading import Thread
from queue import Queue
from collections import Counter
from itertools import chain
from typing import Optional, Tuple, List, Dict

from ..infrastructure.video_utils import get_video_metadata, open_video_capture
from ..utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)

FRAME_SKIP = 10
CARD_TIMEOUT_FRAMES = 10
SCENE_CHANGE_THRESHOLD = 5.0
OCR_ALLOWLIST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


class ParticipantDetector:

    def __init__(self, gpu: bool = True):
        self.reader = easyocr.Reader(["en"], gpu=gpu)

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
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
    def _parse_card(text: str) -> Optional[Tuple[str, int]]:
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

    @staticmethod
    def _prefetch(iterator, buffer=8):
        # Background thread reads frames while main thread runs GPU OCR (both release GIL)
        q = Queue(maxsize=buffer)

        def fill():
            for item in iterator:
                q.put(item)
            q.put(None)

        Thread(target=fill, daemon=True).start()
        while (item := q.get()) is not None:
            yield item

    @staticmethod
    def _read_frames(cap: cv2.VideoCapture, total_frames: int, frame_skip: int):
        def frames():
            n = 0
            while True:
                if n % frame_skip != 0:
                    if not cap.grab():
                        break
                    n += 1
                    continue

                ret, frame = cap.read()
                if not ret:
                    break

                h, w = frame.shape[:2]
                if h > 480:
                    scale = 480 / h
                    frame = cv2.resize(frame, (int(w * scale), 480), interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                yield n, frame
                n += 1

            cap.release()

        return frames()

    def _ocr_frames(self, frames_iter, total_frames, progress_callback=None):
        prev_frame = None
        prev_result = None
        in_session = False

        for frame_num, img in self._prefetch(frames_iter):
            if not in_session and prev_frame is not None:
                if cv2.absdiff(prev_frame, img).mean() < SCENE_CHANGE_THRESHOLD:
                    prev_frame = img
                    yield frame_num, prev_result
                    continue

            text = self.reader.readtext(img, detail=0, paragraph=True, allowlist=OCR_ALLOWLIST)
            prev_result = self._parse_card(" ".join(text) if isinstance(text, list) else text)
            prev_frame = img
            in_session = prev_result is not None

            yield frame_num, prev_result

            if progress_callback:
                progress_callback(frame_num, total_frames)

    def process_video(self, video_path: str,
                      frame_skip: int = FRAME_SKIP,
                      card_timeout_frames: int = CARD_TIMEOUT_FRAMES,
                      progress_callback=None,
                      **kwargs) -> List[Dict]:
        metadata_result = get_video_metadata(video_path)
        if metadata_result.is_err():
            error = metadata_result.unwrap_err()
            raise ProcessingError(
                f"Failed to read video metadata: {error.message}",
                details=error.details
            )

        metadata = metadata_result.unwrap()
        fps = metadata.fps
        total_frames = metadata.frame_count

        cap_result = open_video_capture(video_path)
        if cap_result.is_err():
            raise ProcessingError(f"Cannot open video: {video_path}")
        cap = cap_result.unwrap()

        frames_iter = self._read_frames(cap, total_frames, frame_skip)
        ocr_iter = self._ocr_frames(frames_iter, total_frames, progress_callback)

        # Collect sessions
        detections = []
        session_start = None
        session_detections = []
        misses = 0

        sentinel = ((total_frames, None) for _ in range(card_timeout_frames))

        for frame_num, result in chain(ocr_iter, sentinel):
            if result:
                if session_start is None:
                    session_start = frame_num
                    session_detections = []
                session_detections.append(result)
                misses = 0

            elif session_start is not None:
                misses += 1
                if misses >= card_timeout_frames:
                    card_type, number = Counter(session_detections).most_common(1)[0][0]
                    start_time = session_start / fps
                    end_time = frame_num / fps

                    detections.append({
                        "participant_type": "P" if card_type == "participant" else "E",
                        "participant_number": number,
                        "timestamp": start_time,
                        "duration": round(end_time - start_time, 2),
                        "confidence": 1.0,
                    })

                    session_start = None
                    misses = 0

        if progress_callback:
            progress_callback(total_frames, total_frames)

        logger.info(f"Found {len(detections)} participant cards")
        return detections
