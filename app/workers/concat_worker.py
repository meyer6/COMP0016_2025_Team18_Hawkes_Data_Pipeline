"""
Background worker thread for concatenating multi-part video folders
"""

import logging
from typing import List
from PyQt6.QtCore import pyqtSignal
from .base_worker import BaseWorker
from ..infrastructure.folder_import import concatenate_parts

logger = logging.getLogger(__name__)


class ConcatWorker(BaseWorker):
    """Worker thread for concatenating video parts in background"""

    concat_complete = pyqtSignal(str)  # output_path
    concat_error = pyqtSignal(str)

    def __init__(self, part_paths: List[str], output_path: str):
        super().__init__()
        self.part_paths = part_paths
        self.output_path = output_path

    def do_work(self):
        result = concatenate_parts(self.part_paths, self.output_path)

        if self.is_cancelled():
            return

        if result.is_err():
            self.concat_error.emit(result.unwrap_err().message)
        else:
            self.concat_complete.emit(result.unwrap())

    def _handle_error(self, error: Exception):
        self.concat_error.emit(str(error))

    def _handle_cancelled(self):
        pass
