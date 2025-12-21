# Surgical Video Analysis Pipeline

Desktop app for analysing surgical training videos using deep learning.
Built with PyQt6 and Python 3.12.

## What it does
1. Import videos with auto-generated thumbnails
2. Process through task classifier (ResNet50) and participant detector (EasyOCR)
3. Review/edit annotations on interactive timeline
4. Export labelled clips by task

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
