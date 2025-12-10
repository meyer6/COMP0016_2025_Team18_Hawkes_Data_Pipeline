import cv2
import torch
import pandas as pd
import re
from collections import Counter
from itertools import chain
from threading import Thread
from queue import Queue
from pathlib import Path
import easyocr


SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = str(SCRIPT_DIR / "../../../datasets/videos/example5.avi")

FRAME_SKIP = 10
CARD_TIMEOUT_FRAMES = 10
SCENE_CHANGE_THRESHOLD = 5.0
OCR_ALLOWLIST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "

reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available())


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)

    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr

    return prev[-1]


def parse_card(text):
    words = re.findall(r"[A-Za-z]+|[0-9]+", text)

    for i, word in enumerate(words):
        if len(word) < 5:
            continue
        d_p = levenshtein_distance(word.lower(), "participant")
        d_e = levenshtein_distance(word.lower(), "expert")

        if d_p <= 3 or d_e <= 3:
            for j in range(i + 1, len(words)):
                if words[j].isdigit():
                    role = "participant" if d_p <= d_e else "expert"
                    return (role, int(words[j]))

    return None


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def prefetch(iterator, buffer=8):
    # Background thread reads frames while main thread runs GPU OCR (both release GIL)
    q = Queue(maxsize=buffer)

    def fill():
        for item in iterator:
            q.put(item)
        q.put(None)

    Thread(target=fill, daemon=True).start()
    while (item := q.get()) is not None:
        yield item


def read_frames(video_path, frame_skip):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0 or total == 0:
        cap.release()
        raise ValueError(f"Invalid video: fps={fps}, frames={total}")

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

    return fps, total, frames()


def ocr_frames(frames_iter, total_frames):
    prev_frame = None
    prev_result = None
    in_session = False

    for frame_num, img in prefetch(frames_iter):
        if not in_session and prev_frame is not None:
            if cv2.absdiff(prev_frame, img).mean() < SCENE_CHANGE_THRESHOLD:
                prev_frame = img
                yield frame_num, prev_result
                continue

        text = reader.readtext(img, detail=0, paragraph=True, allowlist=OCR_ALLOWLIST)
        prev_result = parse_card(" ".join(text) if isinstance(text, list) else text)
        prev_frame = img
        in_session = prev_result is not None

        yield frame_num, prev_result


def collect_sessions(ocr_iter, fps, total_frames):
    detections = []
    session_start = None
    session_detections = []
    misses = 0

    sentinel = ((total_frames, None) for _ in range(CARD_TIMEOUT_FRAMES))

    for frame_num, result in chain(ocr_iter, sentinel):
        if result:
            if session_start is None:
                session_start = frame_num
                session_detections = []
            session_detections.append(result)
            misses = 0

        elif session_start is not None:
            misses += 1
            if misses >= CARD_TIMEOUT_FRAMES:
                card_type, number = Counter(session_detections).most_common(1)[0][0]
                start_sec = session_start / fps
                end_sec = frame_num / fps

                detections.append({
                    "type": card_type,
                    "number": number,
                    "start_time": format_timestamp(start_sec),
                    "end_time": format_timestamp(end_sec),
                    "duration_sec": round(end_sec - start_sec, 2),
                })

                session_start = None
                misses = 0

    return pd.DataFrame(detections)


def detect_cards(video_path):
    fps, total_frames, frames = read_frames(video_path, FRAME_SKIP)
    return collect_sessions(ocr_frames(frames, total_frames), fps, total_frames)


if __name__ == "__main__":
    results_df = detect_cards(VIDEO_PATH)

    if len(results_df) > 0:
        print(results_df)
    else:
        print("No cards detected")
