# Surgical Video Analysis Pipeline

A desktop application for analysing surgical training videos. It uses a deep learning classifier to automatically segment videos into task types (suturing, glove cutting, etc.), detects participant/expert identification cards via OCR, and lets you manually refine the annotations before exporting individual clips.

Built with PyQt6 and Python 3.12.

## What it does

1. **Import** videos into a library with auto-generated thumbnails
2. **Process** them through a task classifier (ResNet50 via fast.ai) and a participant detector (EasyOCR)
3. **Review and edit** annotations on an interactive colour-coded timeline
4. **Export** labelled video clips split by task segment

The classifier recognises the following surgical training tasks:
- CameraTarget, ChickenThigh, CystModel, GloveCut, Idle, MovingIndividualAxes, RingRollercoaster, SeaSpikes, Suture

## Setup

### Prerequisites

- Python 3.12+
- FFmpeg (must be on PATH)
- A CUDA-capable GPU is recommended but not required — the app falls back to CPU

### Install

```bash
# Clone the repo
git clone https://github.com/<your-org>/Data-Pipeline.git
cd Data-Pipeline

# Create and activate a virtual environment
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Exact command may change depending on os
mkdir logs 
```

### Run

```bash
python main.py
```

The app opens a grid-based library view. From there you can import videos, queue them for processing, open the editor to tweak annotations, and export clips.

## Configuration

You can drop a `config.json` in the project root to override defaults. All fields are optional — anything you leave out uses the default.

```json
{
  "model_path": "processing/models/task_classifier.pkl",
  "sample_every": 30,
  "smoothing_window": 15,
  "min_duration_sec": 5,
  "confidence_threshold": 0.5,
  "enable_gpu_acceleration": true,
  "log_level": "INFO"
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `sample_every` | 30 | Process every Nth frame (30 = ~1fps at 30fps video) |
| `smoothing_window` | 15 | Temporal smoothing window for predictions |
| `min_duration_sec` | 5 | Minimum segment length in seconds |
| `confidence_threshold` | 0.5 | Prediction confidence cutoff |
| `enable_gpu_acceleration` | true | Use CUDA if available |
| `log_level` | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

## Testing

```bash
# Run the full suite
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage report
pytest --cov=app --cov-report=html
```

Coverage targets 100% on core logic (services, models, repositories, config). UI components (views, widgets) are excluded from the coverage requirement.

Tests run automatically on every push and PR via GitHub Actions. The CI uses headless PyQt with xvfb and CPU-only PyTorch to keep things fast.

## Architecture notes

The codebase follows a layered architecture:

- **Domain** — pure data models and result types, no framework dependencies
- **Infrastructure** — repositories (JSON-backed with in-memory caching and atomic writes), video utilities, model loading
- **Services** — business logic for import, processing status, and export
- **Processing** — the ML pipeline: frame sampling, classification, temporal smoothing, OCR detection, memory-aware batching
- **UI** — PyQt6 views and widgets, with QThread workers to keep the interface responsive during processing

Dependency injection is handled by a `ServiceContainer` that wires everything together at startup. Annotations are versioned (`_v1.json`, `_v2.json`, ...) so edits don't destroy previous results.

## Tech stack

- **GUI:** PyQt6
- **Video:** OpenCV, FFmpeg
- **ML:** PyTorch, fast.ai (ResNet50), EasyOCR
- **Data:** pandas, NumPy
- **Testing:** pytest + pytest-cov
- **CI:** GitHub Actions
