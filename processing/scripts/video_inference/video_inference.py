import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import cv2

import torch
from fastai.vision.all import *

logger = logging.getLogger(__name__)


# ── Config ──

_SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(_SCRIPT_DIR / "../../models/task_classifier.pkl")
VIDEO_PATH = str(_SCRIPT_DIR / "../../../datasets/videos/example5.avi")
OUTPUT_CSV_FRAMES = "task_detection_results.csv"
OUTPUT_CSV_RANGES = "task_detection_time_ranges.csv"

IMAGE_SIZE = (224, 224)
SAMPLE_EVERY_N_FRAMES = 30
TEMPORAL_SMOOTHING_WINDOW = 15
MIN_TASK_DURATION_SEC = 5


# ── Setup ──

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Device: {DEVICE}")

if torch.cuda.is_available():
    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    available_mb = gpu_memory_gb * 1024 * 0.6  # use 60% of VRAM
    BATCH_SIZE = max(8, min(int((available_mb - 100) / 2.5), 128))
    logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({gpu_memory_gb:.1f}GB), Batch Size: {BATCH_SIZE}")
else:
    BATCH_SIZE = 16
    logger.info("Using CPU, Batch Size: 16")

inference_learn = load_learner(MODEL_PATH)
model = inference_learn.model
model.to(DEVICE)
model.eval()

CLASS_NAMES = list(inference_learn.dls.vocab)
N_CLASSES = len(CLASS_NAMES)

# Pre-compute on device once (avoids per-batch allocation)
NORM_MEAN = torch.tensor([0.485, 0.456, 0.406], device=DEVICE).view(1, 3, 1, 1)
NORM_STD = torch.tensor([0.229, 0.224, 0.225], device=DEVICE).view(1, 3, 1, 1)

logger.info(f"Model loaded: {MODEL_PATH}")
logger.info(f"Classes: {CLASS_NAMES}")


# ── Helpers ──

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ── Inference ──

def predict_batch(model, frames, device):
    if not frames:
        return []

    batch_np = np.empty((len(frames), IMAGE_SIZE[1], IMAGE_SIZE[0], 3), dtype=np.uint8)
    for i, frame in enumerate(frames):
        batch_np[i] = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), IMAGE_SIZE)

    batch = torch.from_numpy(np.ascontiguousarray(batch_np.transpose(0, 3, 1, 2)))
    batch = batch.to(device, dtype=torch.float32, non_blocking=True) / 255.0
    batch = (batch - NORM_MEAN) / NORM_STD

    with torch.no_grad(), torch.amp.autocast('cuda', enabled=device.type == 'cuda'):
        probs = torch.nn.functional.softmax(model(batch), dim=1)
        confs, preds = torch.max(probs, dim=1)

    return [(CLASS_NAMES[p.item()], c.item()) for p, c in zip(preds, confs)]


def process_video(video_path, model, device, sample_every=1, batch_size=32):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logger.info(f"Processing: {video_path}")
    logger.info(f"FPS: {fps:.2f}, Frames: {total_frames}, Duration: {format_timestamp(total_frames/fps)}")
    logger.info(f"Batch size: {batch_size}")

    results = []
    frame_batch = []
    frame_nums = []
    frame_num = 0

    def flush_batch():
        if not frame_batch:
            return
        for fn, (task, conf) in zip(frame_nums, predict_batch(model, frame_batch, device)):
            results.append({
                'frame': fn,
                'time_sec': fn / fps,
                'time_str': format_timestamp(fn / fps),
                'task': task,
                'confidence': conf,
            })
        frame_batch.clear()
        frame_nums.clear()

    while cap.isOpened():
        # grab() advances without decoding - only retrieve() on sampled frames
        if not cap.grab():
            break

        if frame_num % sample_every == 0:
            ret, frame = cap.retrieve()
            if ret:
                frame_batch.append(frame)
                frame_nums.append(frame_num)

                if len(frame_batch) >= batch_size:
                    flush_batch()
                    if len(results) % 500 == 0:
                        logger.debug(f"Frame {frame_num}/{total_frames} ({100*frame_num/total_frames:.1f}%)")

        frame_num += 1

    flush_batch()
    cap.release()
    logger.info(f"Done: {len(results)} frames processed")
    return pd.DataFrame(results)


# ── Smoothing ──

def smooth_predictions(df, smoothing_window=15):
    if len(df) == 0:
        return df

    tasks = df['task'].tolist()
    confidences = df['confidence'].values
    n = len(tasks)
    half = smoothing_window // 2
    task_to_idx = {t: i for i, t in enumerate(CLASS_NAMES)}

    # Sparse confidence matrix - only one class has a non-zero value per frame
    scores = np.zeros((n, N_CLASSES), dtype=np.float32)
    for i, (task, conf) in enumerate(zip(tasks, confidences)):
        scores[i, task_to_idx[task]] = conf

    # Prefix sums for O(n) symmetric sliding window
    prefix = np.zeros((n + 1, N_CLASSES), dtype=np.float32)
    np.cumsum(scores, axis=0, out=prefix[1:])

    starts = np.maximum(0, np.arange(n) - half)
    ends = np.minimum(n, np.arange(n) + half + 1)
    window_sums = prefix[ends] - prefix[starts]

    best_indices = np.argmax(window_sums, axis=1)
    smoothed = [CLASS_NAMES[idx] for idx in best_indices]

    df = df.copy()
    df['task_smoothed'] = smoothed
    return df


def enforce_min_duration(df, min_duration_sec=5):
    if len(df) < 2:
        return df

    tasks = df['task_smoothed'].tolist()
    times = df['time_sec'].tolist()

    # Iteratively merge the shortest sub-minimum segment into its longer neighbour
    changed = True
    while changed:
        changed = False

        segments = []
        start = 0
        for i in range(1, len(tasks)):
            if tasks[i] != tasks[start]:
                segments.append((start, i - 1))
                start = i
        segments.append((start, len(tasks) - 1))

        for seg_idx, (s, e) in enumerate(segments):
            if times[e] - times[s] >= min_duration_sec:
                continue

            left_dur = -1
            right_dur = -1

            if seg_idx > 0:
                ls, le = segments[seg_idx - 1]
                left_dur = times[le] - times[ls]

            if seg_idx < len(segments) - 1:
                rs, re = segments[seg_idx + 1]
                right_dur = times[re] - times[rs]

            if left_dur >= right_dur and left_dur >= 0:
                merge_task = tasks[segments[seg_idx - 1][0]]
            elif right_dur >= 0:
                merge_task = tasks[segments[seg_idx + 1][0]]
            else:
                continue

            for i in range(s, e + 1):
                tasks[i] = merge_task
            changed = True
            break  # restart after each merge

    df = df.copy()
    df['task_smoothed'] = tasks
    return df


# ── Aggregation ──

def aggregate_time_ranges(df):
    if len(df) == 0:
        return pd.DataFrame()

    ranges = []
    current_task = df.iloc[0]['task_smoothed']
    start_time = df.iloc[0]['time_sec']
    confidences = [df.iloc[0]['confidence']]

    for i in range(1, len(df)):
        row = df.iloc[i]
        if row['task_smoothed'] != current_task:
            # End at the next segment's start so segments are contiguous
            end_time = row['time_sec']
            ranges.append({
                'task': current_task,
                'start': format_timestamp(start_time),
                'end': format_timestamp(end_time),
                'duration_sec': end_time - start_time,
                'avg_conf': np.mean(confidences)
            })
            current_task = row['task_smoothed']
            start_time = end_time
            confidences = [row['confidence']]
        else:
            confidences.append(row['confidence'])

    ranges.append({
        'task': current_task,
        'start': format_timestamp(start_time),
        'end': format_timestamp(df.iloc[-1]['time_sec']),
        'duration_sec': df.iloc[-1]['time_sec'] - start_time,
        'avg_conf': np.mean(confidences)
    })

    return pd.DataFrame(ranges)


# ── Pipeline ──

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    if os.path.exists(VIDEO_PATH):
        results_df = process_video(VIDEO_PATH, model, DEVICE,
                                   sample_every=SAMPLE_EVERY_N_FRAMES,
                                   batch_size=BATCH_SIZE)
        results_df = smooth_predictions(results_df, smoothing_window=TEMPORAL_SMOOTHING_WINDOW)
        results_df = enforce_min_duration(results_df, min_duration_sec=MIN_TASK_DURATION_SEC)

        time_ranges = aggregate_time_ranges(results_df)

        print(results_df.head())
        print("\nTask Time Ranges:")
        print(time_ranges.to_string(index=False))

        results_df.to_csv(OUTPUT_CSV_FRAMES, index=False)
        time_ranges.to_csv(OUTPUT_CSV_RANGES, index=False)
        print(f"\nSaved: {OUTPUT_CSV_FRAMES}")
        print(f"Saved: {OUTPUT_CSV_RANGES}")

        fig, ax = plt.subplots(figsize=(15, 5))
        task_to_idx = {task: i for i, task in enumerate(CLASS_NAMES)}
        task_indices = [task_to_idx[t] for t in results_df['task_smoothed']]
        ax.plot(results_df['time_sec'], task_indices, linewidth=2)
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Task')
        ax.set_yticks(range(len(CLASS_NAMES)))
        ax.set_yticklabels(CLASS_NAMES)
        ax.set_title('Task Timeline')
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

        summary = time_ranges.groupby('task')['duration_sec'].sum().sort_values(ascending=False)
        total_time = summary.sum()
        print("\nTask Duration Summary:")
        for task, duration in summary.items():
            pct = 100 * duration / total_time
            print(f"  {task:20s}: {duration:7.1f}s ({pct:5.1f}%)")
    else:
        print(f"Video not found: {VIDEO_PATH}")

# Temporal smoothing with prefix-sum optimisation

