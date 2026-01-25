"""
Base worker class for background operations
Provides common functionality for all worker threads
"""

import logging
import threading
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """
    Abstract base class for worker threads.
    Provides common error handling and cancellation support.

    Subclasses implement do_work() and optionally override
    _handle_error() and _handle_cancelled() for custom signals.
    """

    progress_update = pyqtSignal(str, int, int)  # stage, current, total
    error_occurred = pyqtSignal(str, Exception)  # message, exception

    def __init__(self):
        super().__init__()
        self._cancelled = threading.Event()
        logger.debug(f"Worker initialised: {self.__class__.__name__}")

    def cancel(self):
        self._cancelled.set()
        logger.info(f"Worker cancellation requested: {self.__class__.__name__}")

    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def do_work(self):
        raise NotImplementedError("Subclasses must implement do_work()")

    def run(self):
        logger.info(f"Worker started: {self.__class__.__name__}")

        try:
            self.do_work()

            if self.is_cancelled():
                logger.info(f"Worker cancelled: {self.__class__.__name__}")
                self._handle_cancelled()
            else:
                logger.info(f"Worker completed: {self.__class__.__name__}")

        except InterruptedError:
            logger.info(f"Worker interrupted: {self.__class__.__name__}")
            self._handle_cancelled()

        except Exception as e:
            logger.error(f"Worker error in {self.__class__.__name__}: {e}", exc_info=True)
            if self.is_cancelled():
                self._handle_cancelled()
            else:
                self._handle_error(e)

    def _handle_error(self, error: Exception):
        self.error_occurred.emit(str(error), error)

    def _handle_cancelled(self):
        pass

    def emit_progress(self, stage: str, current: int, total: int):
        if self.is_cancelled():
            raise InterruptedError("Worker cancelled")

        self.progress_update.emit(stage, current, total)
