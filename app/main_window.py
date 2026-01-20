"""
Main Window for Video Analysis Application
"""

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from .views.grid_view import GridView
from .views.video_editor import VideoEditorView
from .models.video_item import VideoItem
from .core.config.constants import FileExtensions
from .models.annotation import VideoAnnotation
from .utils.styles import (
    GLOBAL_STYLESHEET, show_info_dialog, show_error_dialog,
    show_warning_dialog, show_confirmation_dialog, show_yes_no_dialog
)
from .widgets.progress_dialog import ProcessingProgressDialog
from .widgets.export_progress_dialog import ExportProgressDialog
from .widgets.video_selection_dialog import VideoSelectionDialog
from .widgets.video_deletion_dialog import VideoDeletionDialog
from .workers.processing_worker import ProcessingWorker
from .workers.export_worker import ExportWorker
from .core.config import AppConfig, PathConfig
from .core.container import ServiceContainer


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.setWindowTitle("Video Analysis Application")

        self.config = config or AppConfig.load()
        self.setGeometry(100, 100, self.config.window_width, self.config.window_height)
        self.setStyleSheet(GLOBAL_STYLESHEET)

        container = ServiceContainer(self.config)
        self.video_repository = container.video_repository()
        self.annotation_repository = container.annotation_repository()
        self.video_service = container.video_service()
        self.processing_service = container.processing_service()
        self.export_service = container.export_service()

        self.video_items = []
        self.processing_worker = None
        self.export_worker = None
        self.processing_queue = []
        self.currently_processing = None
        self.progress_dialog = None

        self.batch_export_videos = None
        self.batch_export_output_dir = None
        self.batch_export_current_index = 0
        self.batch_export_total = 0
        self.batch_export_all_files = []

        self.init_ui()
        self.load_saved_videos()

    def init_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.grid_view = GridView()
        self.grid_view.import_clicked.connect(self.on_import_video)
        self.grid_view.export_all_clicked.connect(self.on_export_all)
        self.grid_view.delete_clicked.connect(self.on_delete_videos)
        self.grid_view.video_clicked.connect(self.on_video_clicked)
        self.stacked_widget.addWidget(self.grid_view)

        self.video_editor = VideoEditorView()
        self.video_editor.back_clicked.connect(self.on_back_to_grid)
        self.video_editor.save_clicked.connect(self.on_save_editor)
        self.video_editor.export_clicked.connect(self.on_export_video)
        self.stacked_widget.addWidget(self.video_editor)

        self.statusBar().showMessage("Ready")

    def _cleanup_worker(self, worker, timeout_ms=5000):
        if worker and worker.isRunning():
            worker.quit()
            worker.wait(timeout_ms)
        if worker:
            worker.deleteLater()

    def _close_progress_dialog(self):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

    def _finish_processing(self):
        self._cleanup_worker(self.processing_worker)
        self.processing_worker = None
        self.currently_processing = None
        self.process_next_in_queue()

    def load_saved_videos(self):
        saved_videos = self.video_repository.get_all()

        if not saved_videos:
            return

        unprocessed_count = 0
        for video_item in saved_videos:
            self.video_items.append(video_item)
            self.grid_view.add_video(video_item)

            if video_item.processed:
                # Verify annotation file still exists
                annotation = self.annotation_repository.load(video_item.video_path)
                if not annotation or not annotation.processed:
                    logger.warning(f"Annotation missing for {Path(video_item.video_path).name}, resetting status")
                    video_item.processed = False
                    video_item.annotation_version = None
                    self.processing_service.mark_processing_failed(video_item.video_path)
                    self.processing_queue.append(video_item.video_path)
                    unprocessed_count += 1
                    queue_position = len(self.processing_queue)
                    self.update_video_card_status(video_item.video_path, f"Queued ({queue_position} in queue)")
            else:
                # Check if processing completed in a previous session
                annotation = self.annotation_repository.load(video_item.video_path)
                if annotation and annotation.processed:
                    video_item.processed = True
                    video_item.annotation_version = annotation.version
                    self.processing_service.mark_processing_complete(video_item.video_path, annotation.version)
                    self.refresh_grid()
                else:
                    self.processing_queue.append(video_item.video_path)
                    unprocessed_count += 1
                    queue_position = len(self.processing_queue)
                    self.update_video_card_status(video_item.video_path, f"Queued ({queue_position} in queue)")

        if unprocessed_count > 0:
            self.process_next_in_queue()
            self.statusBar().showMessage(f"Loaded {len(saved_videos)} video(s), {unprocessed_count} queued for processing")
        else:
            self.statusBar().showMessage(f"Loaded {len(saved_videos)} video(s) from previous session")

    def on_import_video(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video File(s)",
            "",
            "All Files (*)"
        )

        if file_paths:
            for file_path in file_paths:
                self.import_video(file_path)

    def import_video(self, video_path: str):
        result = self.video_service.import_video(video_path)

        if result.is_err():
            error = result.unwrap_err()
            show_error_dialog(self,
                "Import Failed",
                error.message
            )
            return

        video_item = result.unwrap()

        self.video_items.append(video_item)
        self.grid_view.add_video(video_item)

        if not video_item.processed:
            self.processing_queue.append(video_path)
            queue_position = len(self.processing_queue)
            self.update_video_card_status(video_path, f"Queued ({queue_position} in queue)")
            self.statusBar().showMessage(f"Added to queue: {Path(video_path).name}")
            self.process_next_in_queue()
        else:
            self.statusBar().showMessage(f"Imported with existing annotations: {Path(video_path).name}")

    def on_export_all(self):
        if not self.video_items:
            show_info_dialog(self,
                "No Videos",
                "No videos to export."
            )
            return

        processed_videos = [v for v in self.video_items if v.processed]
        if not processed_videos:
            show_info_dialog(self,
                "No Processed Videos",
                "No processed videos available to export. Please import and process videos first."
            )
            return

        selection_dialog = VideoSelectionDialog(self.video_items, self)
        if selection_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_videos = selection_dialog.get_selected_videos()
        if not selected_videos:
            return

        summary_result = self.export_service.get_batch_export_summary(selected_videos)

        if summary_result.is_err():
            show_warning_dialog(self,
                "Export Error",
                summary_result.unwrap_err().message
            )
            return

        summary = summary_result.unwrap()

        if summary.total_segments == 0:
            show_info_dialog(self,
                "No Segments",
                "No non-idle task segments to export from selected videos."
            )
            return

        task_breakdown = summary.get_breakdown_text()

        reply = show_yes_no_dialog(
            self,
            "Export Video Clips",
            f"Ready to export {summary.total_segments} clip(s) from {len(selected_videos)} video(s):\n\n"
            f"{task_breakdown}\n\n"
            "Select output folder?"
        )

        if not reply:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home())
        )

        if not output_dir:
            return

        self.start_batch_export(selected_videos, output_dir)

    def on_video_clicked(self, video_path: str):
        if not Path(video_path).exists():
            show_error_dialog(self,
                "File Not Found",
                f"Video file not found:\n{video_path}\n\n"
                "The file may have been moved or deleted."
            )
            return

        if video_path == self.currently_processing:
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                if not self.progress_dialog.isVisible():
                    self.progress_dialog.show()
                self.progress_dialog.raise_()
                self.progress_dialog.activateWindow()
            else:
                show_info_dialog(self,
                    "Processing In Progress",
                    f"This video is currently being processed.\n\n"
                    f"Video: {Path(video_path).name}"
                )
            return

        if video_path in self.processing_queue:
            show_info_dialog(self,
                "Video Queued",
                f"This video is queued for processing.\n\n"
                f"Position in queue: {self.processing_queue.index(video_path) + 1}"
            )
            return

        annotation = self.annotation_repository.load(video_path)

        if not annotation:
            video_item = next((item for item in self.video_items if item.video_path == video_path), None)

            if video_item and video_item.processed:
                reply = show_yes_no_dialog(
                    self,
                    "Annotations Missing",
                    f"This video was marked as processed, but the annotation file is missing.\n\n"
                    f"The file may have been deleted or moved outside the application.\n\n"
                    f"Would you like to reset the status and re-process this video?"
                )

                if reply:
                    video_item.processed = False
                    video_item.annotation_version = None
                    self.processing_service.mark_processing_failed(video_path)
                    self.update_video_card_status(video_path, "Not Processed")

                    process_reply = show_yes_no_dialog(
                        self,
                        "Start Processing?",
                        "Would you like to start processing this video now?"
                    )

                    if process_reply:
                        self.on_process_video(video_path)

                return
            else:
                reply = show_yes_no_dialog(
                    self,
                    "Video Not Processed",
                    f"This video hasn't been processed yet.\n\n"
                    f"Video: {Path(video_path).name}\n\n"
                    f"Would you like to start processing it now?"
                )

                if reply:
                    self.on_process_video(video_path)

                return

        self.video_editor.load_video(video_path, annotation)
        self.stacked_widget.setCurrentWidget(self.video_editor)
        self.statusBar().showMessage(f"Editing: {Path(video_path).name}")

    def on_delete_videos(self):
        if not self.video_items:
            show_info_dialog(self,
                "No Videos",
                "No videos to delete."
            )
            return

        deletion_dialog = VideoDeletionDialog(self.video_items, self)
        if deletion_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_videos = deletion_dialog.get_selected_videos()
        if not selected_videos:
            return

        reply = show_yes_no_dialog(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_videos)} video(s)?\n\n"
            "This will permanently remove them from the library and delete their thumbnails and annotations."
        )

        if not reply:
            return

        processing_video = None
        for video_item in selected_videos:
            if video_item.video_path == self.currently_processing:
                processing_video = video_item
                break

        if processing_video:
            if self.processing_worker and self.processing_worker.isRunning():
                # Request cancellation - worker will stop naturally
                self.processing_worker.cancel()

                if not self.processing_worker.wait(5000):
                    # If still running after 5 seconds, force quit
                    logger.warning("Processing worker did not finish gracefully, forcing quit")
                    self.processing_worker.quit()
                    self.processing_worker.wait(2000)  # Wait another 2 seconds

                self.processing_worker.deleteLater()
                self.processing_worker = None

            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog.deleteLater()
                self.progress_dialog = None

            self.currently_processing = None

        video_paths = [item.video_path for item in selected_videos]
        result = self.video_service.delete_videos(video_paths)

        if result.is_err():
            show_error_dialog(self,
                "Deletion Failed",
                result.unwrap_err().message
            )
            return

        deleted_count = result.unwrap()

        for video_path in video_paths:
            if video_path in self.processing_queue:
                self.processing_queue.remove(video_path)
                self.update_queue_positions()

            self.video_items = [item for item in self.video_items if item.video_path != video_path]
            self.grid_view.remove_video(video_path)

        show_info_dialog(self,
            "Deletion Complete",
            f"Successfully deleted {deleted_count} video(s)."
        )

        self.statusBar().showMessage(f"Deleted {deleted_count} video(s)")

        if processing_video:
            self.process_next_in_queue()

    def on_process_video(self, video_path: str):
        if video_path in self.processing_queue:
            show_info_dialog(self,
                "Already Queued",
                f"This video is already in the processing queue.\n\n"
                f"Position: {self.processing_queue.index(video_path) + 1}"
            )
            return

        if video_path == self.currently_processing:
            show_info_dialog(self,
                "Already Processing",
                "This video is currently being processed."
            )
            return

        self.processing_queue.append(video_path)
        queue_position = len(self.processing_queue)

        if queue_position == 1 and not self.currently_processing:
            self.update_video_card_status(video_path, "Starting...")
        else:
            self.update_video_card_status(video_path, f"Queued ({queue_position} in queue)")

        self.statusBar().showMessage(f"Added {Path(video_path).name} to processing queue")

        if not self.currently_processing:
            self.process_next_in_queue()

    def process_next_in_queue(self):
        if self.currently_processing or not self.processing_queue:
            return

        video_path = self.processing_queue.pop(0)
        self.currently_processing = video_path

        queue_size = len(self.processing_queue)
        if queue_size > 0:
            self.statusBar().showMessage(
                f"Processing: {Path(video_path).name} ({queue_size} remaining in queue)"
            )
        else:
            self.statusBar().showMessage(f"Processing: {Path(video_path).name}")

        self.update_video_card_status(video_path, "Processing...")
        self.update_queue_positions()
        self.start_video_processing(video_path)

    def update_queue_positions(self):
        for i, video_path in enumerate(self.processing_queue):
            position = i + 1
            self.update_video_card_status(video_path, f"Queued ({position} in queue)")

    def start_video_processing(self, video_path: str):
        if not self.config.get_model_path().exists():
            show_error_dialog(self,
                "Model Not Found",
                f"Task classifier model not found at:\n{self.config.model_path}\n\n"
                "Please ensure the model file exists before processing videos."
            )
            self.currently_processing = None
            return

        import torch
        use_gpu = torch.cuda.is_available() if self.config.enable_gpu_acceleration else False

        self.progress_dialog = ProcessingProgressDialog(self)
        self.progress_dialog.setModal(False)
        self.progress_dialog.setWindowTitle(f"Processing: {Path(video_path).name}")
        self.progress_dialog.reset()

        self.processing_worker = ProcessingWorker(
            video_path=video_path,
            use_gpu=use_gpu,
            sample_every=self.config.sample_every,
            smoothing_window=self.config.smoothing_window,
            min_duration_sec=self.config.min_duration_sec
        )

        self.processing_worker.progress_update.connect(self.on_processing_progress)
        self.processing_worker.processing_complete.connect(self.on_processing_complete)
        self.processing_worker.processing_error.connect(self.on_processing_error)
        self.processing_worker.processing_cancelled.connect(self.on_processing_cancelled)
        self.progress_dialog.cancel_requested.connect(self.on_cancel_processing)

        self.processing_worker.start()

    def on_processing_progress(self, stage: str, current: int, total: int):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.update_progress(stage, current, total)

    def on_processing_complete(self, annotation: VideoAnnotation):
        self._close_progress_dialog()

        try:
            self.annotation_repository.save(annotation, create_new_version=True)

            for item in self.video_items:
                if item.video_path == annotation.video_path:
                    item.processed = True
                    item.annotation_version = annotation.version
                    break

            if not self.processing_service.mark_processing_complete(annotation.video_path, annotation.version):
                logger.warning("Failed to update video status in registry")

            self.update_video_card_status(annotation.video_path, "Processed")
            self.statusBar().showMessage(f"Processing complete: {Path(annotation.video_path).name}")

        except Exception as e:
            show_error_dialog(self, "Save Error", f"Failed to save annotations: {str(e)}")

        self._finish_processing()

    def on_processing_error(self, error_message: str):
        self._close_progress_dialog()

        if self.currently_processing:
            self.update_video_card_status(self.currently_processing, "Processing Failed")

        show_error_dialog(self, "Processing Error", f"Failed to process video:\n\n{error_message}")
        self.statusBar().showMessage("Processing failed")
        self._finish_processing()

    def on_cancel_processing(self):
        if self.processing_worker and self.processing_worker.isRunning():
            self.processing_worker.cancel()

    def on_processing_cancelled(self):
        self._close_progress_dialog()

        if self.currently_processing:
            self.update_video_card_status(self.currently_processing, "Not Processed")

        self.statusBar().showMessage("Processing cancelled by user")
        self._finish_processing()

    def refresh_grid(self):
        self.grid_view.clear_videos()
        for item in self.video_items:
            self.grid_view.add_video(item)

    def update_video_card_status(self, video_path: str, status_text: str):
        for card in self.grid_view.video_cards:
            if card.video_path == video_path:
                card.update_status(status_text)
                break

    def on_back_to_grid(self):
        if self.video_editor.has_unsaved_changes:
            reply = show_confirmation_dialog(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before leaving?",
                buttons=['Save', 'Discard', 'Cancel']
            )

            if reply == 'Save':
                self.on_save_editor()
                if self.video_editor.has_unsaved_changes:
                    return
            elif reply == 'Cancel':
                return

        if hasattr(self.video_editor, 'media_player') and self.video_editor.media_player:
            self.video_editor.media_player.pause()

        self.stacked_widget.setCurrentWidget(self.grid_view)
        self.statusBar().showMessage("Ready")

    def on_save_editor(self):
        if self.video_editor.annotation:
            try:
                self.annotation_repository.save(self.video_editor.annotation)

                self.video_editor.has_unsaved_changes = False
                filename = Path(self.video_editor.video_path).name
                self.video_editor.title_label.setText(filename)

                self.statusBar().showMessage("Annotations saved")
                show_info_dialog(
                    self,
                    "Saved",
                    "Annotations saved successfully!"
                )
            except Exception as e:
                show_error_dialog(
                    self,
                    "Save Error",
                    f"Failed to save annotations:\n\n{str(e)}"
                )

    def on_export_video(self):
        if not self.video_editor.annotation:
            show_warning_dialog(self,
                "No Annotations",
                "Cannot export: No annotations loaded."
            )
            return

        summary_result = self.export_service.get_export_summary(self.video_editor.video_path)

        if summary_result.is_err():
            show_warning_dialog(self,
                "Export Error",
                summary_result.unwrap_err().message
            )
            return

        summary = summary_result.unwrap()

        if summary.total_segments == 0:
            show_info_dialog(self,
                "No Segments",
                "No non-idle task segments to export."
            )
            return

        task_breakdown = summary.get_breakdown_text()

        reply = show_yes_no_dialog(
            self,
            "Export Video Clips",
            f"Ready to export {summary.total_segments} clip(s):\n\n{task_breakdown}\n\n"
            "Select output folder?"
        )

        if not reply:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home())
        )

        if not output_dir:
            return

        self.start_video_export(output_dir)

    def start_video_export(self, output_dir: str):
        self.export_worker = ExportWorker(
            video_path=self.video_editor.video_path,
            annotation=self.video_editor.annotation,
            output_dir=output_dir
        )

        self.export_worker.export_complete.connect(self.on_export_complete)
        self.export_worker.export_error.connect(self.on_export_error)

        self.export_worker.start()
        self.statusBar().showMessage("Exporting video clips...")

    def start_batch_export(self, selected_videos, output_dir: str):
        self.batch_export_videos = selected_videos
        self.batch_export_output_dir = output_dir
        self.batch_export_current_index = 0
        self.batch_export_total = len(selected_videos)
        self.batch_export_all_files = []

        self.statusBar().showMessage(f"Exporting {len(selected_videos)} video(s)...")
        self._export_next_video_in_batch()

    def _export_next_video_in_batch(self):
        if self.batch_export_current_index >= self.batch_export_total:
            self._on_batch_export_complete()
            return

        video_item = self.batch_export_videos[self.batch_export_current_index]
        annotation = self.annotation_repository.load(video_item.video_path)

        if not annotation:
            self.batch_export_current_index += 1
            self._export_next_video_in_batch()
            return

        video_name = Path(video_item.video_path).name
        self.statusBar().showMessage(
            f"Exporting video {self.batch_export_current_index + 1}/{self.batch_export_total}: {video_name}"
        )

        self.export_worker = ExportWorker(
            video_path=video_item.video_path,
            annotation=annotation,
            output_dir=self.batch_export_output_dir
        )

        self.export_worker.export_complete.connect(self.on_batch_export_video_complete)
        self.export_worker.export_error.connect(self.on_batch_export_error)

        self.export_worker.start()

    def on_batch_export_video_complete(self, exported_files: list):
        self.batch_export_all_files.extend(exported_files)
        self._cleanup_worker(self.export_worker)
        self.export_worker = None
        self.batch_export_current_index += 1
        self._export_next_video_in_batch()

    def on_batch_export_error(self, error_message: str):
        video_item = self.batch_export_videos[self.batch_export_current_index]
        video_name = Path(video_item.video_path).name

        reply = show_yes_no_dialog(self,
            "Export Error",
            f"Failed to export video '{video_name}':\n\n{error_message}\n\n"
            "Do you want to continue with remaining videos?"
        )

        self._cleanup_worker(self.export_worker)
        self.export_worker = None

        if reply:
            self.batch_export_current_index += 1
            self._export_next_video_in_batch()
        else:
            self._on_batch_export_complete()

    def _on_batch_export_complete(self):
        total_files = len(self.batch_export_all_files)
        videos_processed = self.batch_export_current_index

        if total_files > 0:
            show_info_dialog(self,
                "Batch Export Complete",
                f"Successfully exported {total_files} clip(s) from {videos_processed} video(s)!\n\n"
                f"Files saved to:\n{self.batch_export_output_dir}"
            )
            self.statusBar().showMessage(f"Batch export complete: {total_files} clips from {videos_processed} videos")
        else:
            show_warning_dialog(self,
                "Batch Export Complete",
                "No clips were exported."
            )
            self.statusBar().showMessage("Batch export completed with no clips")

        self.batch_export_videos = None
        self.batch_export_output_dir = None
        self.batch_export_current_index = 0
        self.batch_export_total = 0
        self.batch_export_all_files = []

    def on_export_complete(self, exported_files: list):
        self._cleanup_worker(self.export_worker)
        self.export_worker = None

        if exported_files:
            output_folder = Path(exported_files[0]).parent.parent
            show_info_dialog(self,
                "Export Complete",
                f"Successfully exported {len(exported_files)} clip(s)!\n\n"
                f"Files saved to:\n{output_folder}"
            )
        else:
            show_warning_dialog(self,
                "Export Complete",
                "No clips were exported."
            )

        self.statusBar().showMessage(f"Exported {len(exported_files)} clip(s)")

    def on_export_error(self, error_message: str):
        show_error_dialog(self, "Export Error", f"Failed to export video clips:\n\n{error_message}")
        self.statusBar().showMessage("Export failed")
        self._cleanup_worker(self.export_worker)
        self.export_worker = None

    def closeEvent(self, event):
        if self.currently_processing or (self.processing_worker and self.processing_worker.isRunning()):
            reply = show_yes_no_dialog(
                self,
                "Processing In Progress",
                "Video processing is currently in progress. Closing now will stop the processing.\n\n"
                "Do you want to close anyway?"
            )

            if not reply:
                event.ignore()
                return

            if self.processing_worker and self.processing_worker.isRunning():
                self.processing_worker.cancel()
                self.processing_worker.quit()
                self.processing_worker.wait(3000)  # Wait up to 3 seconds

        if self.export_worker and self.export_worker.isRunning():
            reply = show_yes_no_dialog(
                self,
                "Export In Progress",
                "Video export is currently in progress. Closing now will stop the export.\n\n"
                "Do you want to close anyway?"
            )

            if not reply:
                event.ignore()
                return

            if self.export_worker and self.export_worker.isRunning():
                self.export_worker.quit()
                self.export_worker.wait(2000)  # Wait up to 2 seconds

        if (self.stacked_widget.currentWidget() == self.video_editor and
                self.video_editor.has_unsaved_changes):
            reply = show_confirmation_dialog(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                buttons=['Save', 'Discard', 'Cancel']
            )

            if reply == 'Save':
                self.on_save_editor()
                if self.video_editor.has_unsaved_changes:
                    event.ignore()
                    return
            elif reply == 'Cancel':
                event.ignore()
                return


        if hasattr(self, 'video_editor'):
            self.video_editor.cleanup()

        event.accept()
