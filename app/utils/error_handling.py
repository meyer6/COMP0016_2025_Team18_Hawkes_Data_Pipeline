"""
Custom exception hierarchy for the application
Provides specific exception types for different error scenarios
"""

from typing import Optional


class AppError(Exception):

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class VideoError(AppError):

    def __init__(self, message: str, video_path: Optional[str] = None, details: Optional[str] = None):
        self.video_path = video_path
        super().__init__(message, details)


class VideoNotFoundError(VideoError):
    pass


class VideoReadError(VideoError):
    pass


class VideoCorruptedError(VideoError):
    pass


class ProcessingError(AppError):

    def __init__(self, message: str, stage: Optional[str] = None, details: Optional[str] = None):
        self.stage = stage
        super().__init__(message, details)


class ModelError(ProcessingError):
    pass


class TaskClassificationError(ProcessingError):
    pass


class ParticipantDetectionError(ProcessingError):
    pass


class ExportError(AppError):

    def __init__(self, message: str, output_path: Optional[str] = None, details: Optional[str] = None):
        self.output_path = output_path
        super().__init__(message, details)


class AnnotationError(AppError):

    def __init__(self, message: str, annotation_path: Optional[str] = None, details: Optional[str] = None):
        self.annotation_path = annotation_path
        super().__init__(message, details)


class AnnotationNotFoundError(AnnotationError):
    pass


class AnnotationParseError(AnnotationError):
    pass


class ConfigurationError(AppError):
    pass


class ValidationError(AppError):
    pass


class ErrorContext:
    """Context manager for consistent error handling and logging."""

    def __init__(self, logger, operation: str, raise_on_error: bool = True):
        self.logger = logger
        self.operation = operation
        self.raise_on_error = raise_on_error
        self.error = None

    def __enter__(self):
        self.logger.debug(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.debug(f"Completed: {self.operation}")
            return True

        # Log the error
        if isinstance(exc_val, AppError):
            self.logger.error(f"Error in {self.operation}: {exc_val.message}")
            if exc_val.details:
                self.logger.debug(f"Error details: {exc_val.details}")
        else:
            self.logger.error(f"Unexpected error in {self.operation}: {exc_val}", exc_info=True)

        self.error = exc_val

        # Suppress exception if raise_on_error is False
        if not self.raise_on_error:
            return True

        return False
