"""
Worker test configuration.
Mock heavy ML dependencies (pandas, easyocr, fastai) to allow testing
pure logic without requiring these packages to be fully functional.
"""
import sys
from unittest.mock import MagicMock

# Force-mock heavy dependencies that worker modules import transitively
# (workers -> processing -> task_classifier -> pandas)
for mod_name in ['pandas', 'easyocr', 'fastai', 'fastai.vision', 'fastai.vision.all']:
    sys.modules[mod_name] = MagicMock()
